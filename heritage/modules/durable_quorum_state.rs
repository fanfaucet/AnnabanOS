// Copyright 2026 Jacob Wayne Kinnaird / Annaban Integrated Solutions
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

//! Durable BFT quorum state tracking for the Heritage Stack.
//!
//! This module stores verified votes in one sled tree and finalized event markers in
//! a separate sled tree. On restart, [`DurableQuorumState::recover_from_disk`] scans
//! both trees and rebuilds the in-memory hot caches used by the async API.
//!
//! Security notes:
//! - Votes are domain-separated before Ed25519 verification to reduce cross-protocol
//!   replay risk.
//! - Callers should rotate `epoch` whenever membership or consensus view changes;
//!   the epoch is part of the signed payload.
//! - Ed25519 verification is delegated to `ed25519-dalek`, which performs strict
//!   signature checks for canonical encodings.

use std::collections::{HashMap, HashSet};
use std::path::Path;
use std::sync::Arc;

use ed25519_dalek::{Signature, VerifyingKey};
use serde::{Deserialize, Serialize};
use thiserror::Error;
use tokio::sync::RwLock;
use uuid::Uuid;

const RAW_VOTES_TREE: &str = "durable_quorum_state.raw_votes.v1";
const FINALIZED_EVENTS_TREE: &str = "durable_quorum_state.finalized_events.v1";
const VOTE_DOMAIN_SEPARATOR: &[u8] = b"AnnabanOS.Heritage.DurableQuorumState.vote.v1";

/// Result type used by the durable quorum module.
pub type RelayResult<T> = Result<T, RelayError>;

/// Errors emitted while validating, persisting, recovering, or querying quorum state.
#[derive(Debug, Error)]
pub enum RelayError {
    /// The configured peer count cannot support the requested Byzantine fault tolerance.
    #[error(
        "invalid peer configuration: total_peers={total_peers}, f={f}; BFT requires total_peers >= 3f + 1"
    )]
    InvalidPeerConfiguration {
        /// Total number of peers in the consensus membership.
        total_peers: usize,
        /// Number of Byzantine faults the tracker must tolerate.
        f: usize,
    },

    /// The peer registry size does not match the declared consensus membership size.
    #[error("peer registry contains {actual} peers, but total_peers is {expected}")]
    PeerRegistrySizeMismatch {
        /// Declared consensus membership size.
        expected: usize,
        /// Number of unique public keys supplied to the registry.
        actual: usize,
    },

    /// A vote was submitted by a public key outside the registered membership.
    #[error("vote rejected because the voter public key is not in the peer registry")]
    UnknownPeer,

    /// A vote signature was malformed or failed strict Ed25519 verification.
    #[error("vote signature verification failed")]
    InvalidSignature,

    /// The same voter attempted to cast a second vote for an event.
    #[error("double vote rejected for event_id={event_id} and voter={voter_hex}")]
    DoubleVote {
        /// Event for which the duplicate vote was submitted.
        event_id: Uuid,
        /// Hex-encoded public key for diagnostics.
        voter_hex: String,
    },

    /// Stored data could not be decoded during recovery or readback.
    #[error("serialization failure: {0}")]
    Serialization(#[from] postcard::Error),

    /// sled returned a storage or durability error.
    #[error("sled storage failure: {0}")]
    Storage(#[from] sled::Error),

    /// The embedded database could not be opened.
    #[error("failed to open sled database at {path}: {source}")]
    OpenDatabase {
        /// Filesystem path passed to sled.
        path: String,
        /// Underlying sled error.
        source: sled::Error,
    },
}

/// Consensus decision carried by a quorum vote.
#[derive(Clone, Copy, Debug, Deserialize, Eq, Hash, PartialEq, Serialize)]
pub enum VoteDecision {
    /// The voter attests that the event should be finalized.
    Commit,
    /// The voter attests that the event should not be finalized in the current epoch/view.
    Reject,
}

/// Finality status returned after recording or querying votes for an event.
#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum FinalityStatus {
    /// The event has not yet reached a durable quorum.
    Pending {
        /// Number of valid commit votes currently recorded for the event.
        commit_votes: usize,
        /// Number of commit votes required to finalize the event.
        required_votes: usize,
    },
    /// The event reached quorum and a finalized marker was durably stored.
    Finalized {
        /// Number of valid commit votes observed when finality was reached.
        commit_votes: usize,
        /// Number of commit votes required to finalize the event.
        required_votes: usize,
    },
}

/// A signed vote for a single consensus event.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct QuorumVote {
    /// Unique event identifier. The value is encoded into persistence keys to prevent replay across events.
    #[serde(with = "uuid_as_bytes")]
    pub event_id: Uuid,
    /// Application-level event digest being voted on.
    pub event_digest: [u8; 32],
    /// Voter public key encoded as a 32-byte Ed25519 verifying key.
    pub voter_key: [u8; 32],
    /// Commit/reject decision for this event.
    pub decision: VoteDecision,
    /// Consensus epoch or view. Include membership/view changes in this value to reduce replay risk.
    pub epoch: u64,
    /// Ed25519 signature over the domain-separated vote payload.
    pub signature: [u8; 64],
}

/// Crash-tolerant, durable BFT quorum state backed by sled.
///
/// The tracker supports `f` Byzantine faults with at least `3f + 1` total peers and
/// finalizes on `2f + 1` valid commit votes. All mutable hot caches are protected
/// by Tokio [`RwLock`] values, making the public API safe to share across async
/// tasks through [`Arc`].
pub struct DurableQuorumState {
    db: sled::Db,
    raw_votes: sled::Tree,
    finalized_events: sled::Tree,
    peer_registry: Arc<RwLock<HashSet<[u8; 32]>>>,
    votes_by_event: RwLock<HashMap<Uuid, HashMap<[u8; 32], QuorumVote>>>,
    finalized_cache: RwLock<HashSet<Uuid>>,
    total_peers: usize,
    f: usize,
    quorum_threshold: usize,
}

#[derive(Serialize)]
struct SignedVotePayload {
    domain: &'static [u8],
    event_id: [u8; 16],
    event_digest: [u8; 32],
    voter_key: [u8; 32],
    decision: VoteDecision,
    epoch: u64,
}

mod uuid_as_bytes {
    use serde::{Deserialize, Deserializer, Serialize, Serializer};
    use uuid::Uuid;

    pub fn serialize<S>(value: &Uuid, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        value.as_bytes().serialize(serializer)
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<Uuid, D::Error>
    where
        D: Deserializer<'de>,
    {
        let bytes = <[u8; 16]>::deserialize(deserializer)?;
        Ok(Uuid::from_bytes(bytes))
    }
}

#[derive(Deserialize, Serialize)]
struct FinalizedMarker {
    #[serde(with = "uuid_as_bytes")]
    event_id: Uuid,
    commit_votes: usize,
    required_votes: usize,
}

impl DurableQuorumState {
    /// Open or create a durable quorum database and recover all hot caches from disk.
    ///
    /// `peer_keys` is the authoritative membership registry. A vote from any key not
    /// present in this registry is rejected before it reaches disk.
    pub async fn new<P>(
        path: P,
        total_peers: usize,
        f: usize,
        peer_keys: Vec<[u8; 32]>,
    ) -> RelayResult<Self>
    where
        P: AsRef<Path>,
    {
        Self::validate_bft_configuration(total_peers, f, &peer_keys)?;

        let db_path = path.as_ref().display().to_string();
        let db = sled::open(path).map_err(|source| RelayError::OpenDatabase {
            path: db_path,
            source,
        })?;
        let raw_votes = db.open_tree(RAW_VOTES_TREE)?;
        let finalized_events = db.open_tree(FINALIZED_EVENTS_TREE)?;
        let peer_registry = Arc::new(RwLock::new(peer_keys.into_iter().collect()));

        let state = Self {
            db,
            raw_votes,
            finalized_events,
            peer_registry,
            votes_by_event: RwLock::new(HashMap::new()),
            finalized_cache: RwLock::new(HashSet::new()),
            total_peers,
            f,
            quorum_threshold: (2 * f) + 1,
        };

        state.recover_from_disk().await?;
        Ok(state)
    }

    /// Rebuild all in-memory vote and finality caches from the sled trees.
    ///
    /// Recovery validates persisted votes against the current peer registry and their
    /// signatures. Invalid legacy or corrupted entries are ignored in memory rather
    /// than trusted; operators can audit sled directly if forensic detail is needed.
    /// If a crash happened after enough raw votes were flushed but before the
    /// finalized marker was written, recovery derives and persists the missing
    /// marker before publishing rebuilt hot caches.
    pub async fn recover_from_disk(&self) -> RelayResult<()> {
        let registry = self.peer_registry.read().await;
        let mut recovered_votes: HashMap<Uuid, HashMap<[u8; 32], QuorumVote>> = HashMap::new();

        for entry in self.raw_votes.iter() {
            let (_key, value) = entry?;
            let vote: QuorumVote = postcard::from_bytes(&value)?;
            if registry.contains(&vote.voter_key) && Self::verify_vote_signature(&vote).is_ok() {
                recovered_votes
                    .entry(vote.event_id)
                    .or_default()
                    .entry(vote.voter_key)
                    .or_insert(vote);
            }
        }
        drop(registry);

        let mut recovered_finalized = HashSet::new();
        for entry in self.finalized_events.iter() {
            let (_key, value) = entry?;
            let marker: FinalizedMarker = postcard::from_bytes(&value)?;
            recovered_finalized.insert(marker.event_id);
        }

        let mut missing_markers = Vec::new();
        for (event_id, event_votes) in &recovered_votes {
            let commit_votes = Self::commit_vote_count(event_votes);
            if commit_votes >= self.quorum_threshold && !recovered_finalized.contains(event_id) {
                missing_markers.push((*event_id, commit_votes));
            }
        }

        for (event_id, commit_votes) in missing_markers {
            self.persist_finalized_marker(event_id, commit_votes)
                .await?;
            recovered_finalized.insert(event_id);
        }

        *self.votes_by_event.write().await = recovered_votes;
        *self.finalized_cache.write().await = recovered_finalized;
        Ok(())
    }

    /// Validate, durably persist, and index a vote.
    ///
    /// The method rejects unknown peers, invalid signatures, and duplicate votes for
    /// the same `(event_id, voter_key)` composite key. Persistence is write-ahead
    /// style: sled receives and flushes the vote before the in-memory cache is
    /// updated. If a commit quorum is reached, the finalized marker is written and
    /// flushed before finality is reported.
    pub async fn record_vote(&self, vote: QuorumVote) -> RelayResult<FinalityStatus> {
        {
            let registry = self.peer_registry.read().await;
            if !registry.contains(&vote.voter_key) {
                return Err(RelayError::UnknownPeer);
            }
        }
        Self::verify_vote_signature(&vote)?;

        let key = Self::vote_key(vote.event_id, &vote.voter_key);
        if self.raw_votes.contains_key(&key)? {
            return Err(RelayError::DoubleVote {
                event_id: vote.event_id,
                voter_hex: Self::hex_encode(&vote.voter_key),
            });
        }

        let encoded_vote = postcard::to_allocvec(&vote)?;
        let inserted =
            self.raw_votes
                .compare_and_swap(&key, None as Option<&[u8]>, Some(encoded_vote))?;
        if inserted.is_err() {
            return Err(RelayError::DoubleVote {
                event_id: vote.event_id,
                voter_hex: Self::hex_encode(&vote.voter_key),
            });
        }
        self.raw_votes.flush_async().await?;
        self.db.flush_async().await?;

        let event_id = vote.event_id;
        let mut votes_guard = self.votes_by_event.write().await;
        let event_votes = votes_guard.entry(event_id).or_default();
        event_votes.insert(vote.voter_key, vote);
        let commit_votes = Self::commit_vote_count(event_votes);
        drop(votes_guard);

        if commit_votes >= self.quorum_threshold {
            self.persist_finalized_marker(event_id, commit_votes)
                .await?;
            Ok(FinalityStatus::Finalized {
                commit_votes,
                required_votes: self.quorum_threshold,
            })
        } else {
            Ok(FinalityStatus::Pending {
                commit_votes,
                required_votes: self.quorum_threshold,
            })
        }
    }

    /// Return `true` when an event has a durable finalized marker.
    pub async fn is_finalized(&self, event_id: Uuid) -> RelayResult<bool> {
        if self.finalized_cache.read().await.contains(&event_id) {
            return Ok(true);
        }

        let exists = self
            .finalized_events
            .contains_key(Self::event_key(event_id))?;
        if exists {
            self.finalized_cache.write().await.insert(event_id);
        }
        Ok(exists)
    }

    /// Return the number of peers declared for this BFT membership.
    pub fn total_peers(&self) -> usize {
        self.total_peers
    }

    /// Return the number of Byzantine faults tolerated by this tracker.
    pub fn tolerated_faults(&self) -> usize {
        self.f
    }

    /// Return the commit vote threshold required for finality (`2f + 1`).
    pub fn quorum_threshold(&self) -> usize {
        self.quorum_threshold
    }

    async fn persist_finalized_marker(
        &self,
        event_id: Uuid,
        commit_votes: usize,
    ) -> RelayResult<()> {
        let key = Self::event_key(event_id);
        if !self.finalized_events.contains_key(&key)? {
            let marker = FinalizedMarker {
                event_id,
                commit_votes,
                required_votes: self.quorum_threshold,
            };
            self.finalized_events
                .insert(key, postcard::to_allocvec(&marker)?)?;
            self.finalized_events.flush_async().await?;
            self.db.flush_async().await?;
        }
        self.finalized_cache.write().await.insert(event_id);
        Ok(())
    }

    fn validate_bft_configuration(
        total_peers: usize,
        f: usize,
        peer_keys: &[[u8; 32]],
    ) -> RelayResult<()> {
        if total_peers < (3 * f) + 1 {
            return Err(RelayError::InvalidPeerConfiguration { total_peers, f });
        }

        let unique_peers: HashSet<[u8; 32]> = peer_keys.iter().copied().collect();
        if unique_peers.len() != total_peers {
            return Err(RelayError::PeerRegistrySizeMismatch {
                expected: total_peers,
                actual: unique_peers.len(),
            });
        }

        Ok(())
    }

    fn commit_vote_count(event_votes: &HashMap<[u8; 32], QuorumVote>) -> usize {
        event_votes
            .values()
            .filter(|stored_vote| stored_vote.decision == VoteDecision::Commit)
            .count()
    }

    fn verify_vote_signature(vote: &QuorumVote) -> RelayResult<()> {
        let verifying_key =
            VerifyingKey::from_bytes(&vote.voter_key).map_err(|_| RelayError::InvalidSignature)?;
        let signature = Signature::from_bytes(&vote.signature);
        let payload = Self::signed_payload_bytes(vote)?;
        verifying_key
            .verify_strict(&payload, &signature)
            .map_err(|_| RelayError::InvalidSignature)
    }

    fn signed_payload_bytes(vote: &QuorumVote) -> RelayResult<Vec<u8>> {
        let payload = SignedVotePayload {
            domain: VOTE_DOMAIN_SEPARATOR,
            event_id: *vote.event_id.as_bytes(),
            event_digest: vote.event_digest,
            voter_key: vote.voter_key,
            decision: vote.decision,
            epoch: vote.epoch,
        };
        Ok(postcard::to_allocvec(&payload)?)
    }

    fn vote_key(event_id: Uuid, voter_key: &[u8; 32]) -> Vec<u8> {
        let mut key = Vec::with_capacity(16 + 32);
        key.extend_from_slice(event_id.as_bytes());
        key.extend_from_slice(voter_key);
        key
    }

    fn event_key(event_id: Uuid) -> [u8; 16] {
        *event_id.as_bytes()
    }

    fn hex_encode(bytes: &[u8]) -> String {
        const HEX: &[u8; 16] = b"0123456789abcdef";
        let mut out = String::with_capacity(bytes.len() * 2);
        for byte in bytes {
            out.push(HEX[(byte >> 4) as usize] as char);
            out.push(HEX[(byte & 0x0f) as usize] as char);
        }
        out
    }
}

/// Example harness demonstrating initialization, recovery, and voting.
///
/// This harness is feature-gated so production builds can import the module
/// without pulling in random-number dependencies. To run it as a standalone
/// example, enable a crate feature named `durable-quorum-example` and add
/// `rand_core` with the `getrandom` feature to the dependency graph.
#[cfg(feature = "durable-quorum-example")]
#[tokio::main]
async fn main() -> RelayResult<()> {
    use ed25519_dalek::{Signer, SigningKey};
    use rand_core::OsRng;

    let peer_signers: Vec<SigningKey> = (0..4).map(|_| SigningKey::generate(&mut OsRng)).collect();
    let peer_keys: Vec<[u8; 32]> = peer_signers
        .iter()
        .map(|signer| signer.verifying_key().to_bytes())
        .collect();

    let db_path = std::env::temp_dir().join(format!("annaban-durable-quorum-{}", Uuid::new_v4()));
    let state = DurableQuorumState::new(&db_path, 4, 1, peer_keys.clone()).await?;
    let event_id = Uuid::new_v4();
    let digest = [7_u8; 32];

    for signer in peer_signers.iter().take(3) {
        let mut vote = QuorumVote {
            event_id,
            event_digest: digest,
            voter_key: signer.verifying_key().to_bytes(),
            decision: VoteDecision::Commit,
            epoch: 1,
            signature: [0_u8; 64],
        };
        let payload = DurableQuorumState::signed_payload_bytes(&vote)?;
        vote.signature = signer.sign(&payload).to_bytes();
        let status = state.record_vote(vote).await?;
        println!("status after vote: {status:?}");
    }

    assert!(state.is_finalized(event_id).await?);
    drop(state);

    let recovered = DurableQuorumState::new(&db_path, 4, 1, peer_keys).await?;
    assert!(recovered.is_finalized(event_id).await?);
    recovered.recover_from_disk().await?;
    assert!(recovered.is_finalized(event_id).await?);

    Ok(())
}
