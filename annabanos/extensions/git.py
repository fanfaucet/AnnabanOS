"""Read-only GitHub repository extension for AnnabanAI's Knowledge Curator.

The adapter reads repository metadata only. It does not clone repositories,
execute repository code, open issues, create branches, commit, or change files.
Tests use an injected transport and do not call live APIs.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Callable
from urllib.parse import quote

JsonTransport = Callable[[str, dict[str, str]], dict[str, Any]]


def _http_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


@dataclass(frozen=True)
class RepositorySnapshot:
    repository: str
    ref: str
    commit_sha: str
    tree_sha: str
    paths: tuple[str, ...]
    jurisdiction_id: str
    visibility: str
    source: str = "github_rest_api"
    read_only: bool = True
    external_effects: int = 0
    snapshot_sha256: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class KnowledgeGap:
    gap_type: str
    description: str
    severity: float
    rationale: str
    confidence: float
    evidence_paths: tuple[str, ...]
    jurisdiction_id: str
    visibility: str
    projected_tradeoffs: tuple[str, ...] = (
        "Improving the gap may increase maintenance effort.",
    )
    advisory_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GitRepositoryExtension:
    """Read-only repository observer that emits deterministic KCA findings."""

    def __init__(
        self,
        repository: str,
        *,
        token: str | None = None,
        api_base: str = "https://api.github.com",
        transport: JsonTransport | None = None,
        max_files: int = 5000,
    ) -> None:
        parts = repository.split("/", 1)
        if len(parts) != 2 or not all(parts):
            raise ValueError("repository must be in 'owner/name' form")
        if max_files < 1:
            raise ValueError("max_files must be positive")
        self.repository = repository
        self.api_base = api_base.rstrip("/")
        self.max_files = max_files
        self.transport = transport or _http_json
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "AnnabanAI-Git-KCA/0.1",
        }
        credential = token or os.getenv("GITHUB_TOKEN")
        if credential:
            self.headers["Authorization"] = f"Bearer {credential}"

    def snapshot(
        self,
        *,
        ref: str = "main",
        jurisdiction_id: str,
        visibility: str,
    ) -> RepositorySnapshot:
        """Read branch/tree metadata and return a hashed inventory of paths."""
        if not jurisdiction_id.strip() or not visibility.strip():
            raise ValueError("jurisdiction_id and visibility are required")
        owner, name = self.repository.split("/", 1)
        branch_url = (
            f"{self.api_base}/repos/{quote(owner)}/{quote(name)}"
            f"/branches/{quote(ref, safe='')}"
        )
        branch_data = self.transport(branch_url, dict(self.headers))
        commit_sha = str(branch_data.get("commit", {}).get("sha", ""))
        tree_sha = str(branch_data.get("commit", {}).get("commit", {}).get("tree", {}).get("sha", ""))
        if not commit_sha or not tree_sha:
            raise ValueError("GitHub response lacks commit or tree SHA")

        tree_url = f"{self.api_base}/repos/{quote(owner)}/{quote(name)}/git/trees/{quote(tree_sha)}?recursive=1"
        tree_data = self.transport(tree_url, dict(self.headers))
        if tree_data.get("truncated"):
            raise ValueError("repository tree is truncated; refusing incomplete inventory")
        entries = tree_data.get("tree", [])
        paths = tuple(sorted(
            str(entry["path"])
            for entry in entries
            if entry.get("type") in {"blob", "tree"} and isinstance(entry.get("path"), str)
        ))
        if len(paths) > self.max_files:
            raise ValueError(f"repository inventory exceeds max_files={self.max_files}")
        canonical = json.dumps(
            {
                "repository": self.repository,
                "ref": ref,
                "commit_sha": commit_sha,
                "tree_sha": tree_sha,
                "paths": paths,
                "jurisdiction_id": jurisdiction_id,
                "visibility": visibility,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return RepositorySnapshot(
            repository=self.repository,
            ref=ref,
            commit_sha=commit_sha,
            tree_sha=tree_sha,
            paths=paths,
            jurisdiction_id=jurisdiction_id,
            visibility=visibility,
            snapshot_sha256=hashlib.sha256(canonical).hexdigest(),
        )

    @staticmethod
    def identify_gaps(snapshot: RepositorySnapshot) -> list[KnowledgeGap]:
        """Report only observable repository-structure gaps; never mutate state."""
        paths = set(snapshot.paths)
        findings: list[KnowledgeGap] = []
        readme_paths = {p for p in paths if p.rsplit("/", 1)[-1].lower() in {"readme.md", "readme.rst", "readme.txt"}}
        if not readme_paths:
            findings.append(KnowledgeGap(
                gap_type="DOCUMENTATION_MISSING",
                description="No README file is present in the repository inventory.",
                severity=0.55,
                rationale="A repository landing document was not found in the observed tree.",
                confidence=0.99,
                evidence_paths=(),
                jurisdiction_id=snapshot.jurisdiction_id,
                visibility=snapshot.visibility,
            ))
        test_paths = {p for p in paths if p.startswith(("tests/", "test/")) or p.rsplit("/", 1)[-1].startswith("test_")}
        if not test_paths:
            findings.append(KnowledgeGap(
                gap_type="TEST_COVERAGE_UNKNOWN",
                description="No conventional test files or test directories were found.",
                severity=0.65,
                rationale="Repository path inventory contains no recognized test paths; this does not prove tests are absent elsewhere.",
                confidence=0.92,
                evidence_paths=(),
                jurisdiction_id=snapshot.jurisdiction_id,
                visibility=snapshot.visibility,
            ))
        for finding in findings:
            # Keep output grounded in the observed snapshot and scoped for audit.
            _ = snapshot.snapshot_sha256
        return findings

    def observe(self, **scope: str) -> dict[str, Any]:
        """Return one KCA-compatible observation record with no write operations."""
        snapshot = self.snapshot(**scope)
        gaps = self.identify_gaps(snapshot)
        return {
            "status": "complete",
            "source": "git_repository_extension",
            "repository_snapshot": snapshot.to_dict(),
            "knowledge_gaps": [gap.to_dict() for gap in gaps],
            "recommendations": [
                {
                    "action": "human_review",
                    "rationale": "Review repository-structure findings before changing the knowledge base.",
                    "confidence": 1.0,
                    "affected_constraints": ["read_only", "human_authorization_required"],
                    "projected_tradeoffs": ["No repository changes are made by this extension."],
                }
            ] if gaps else [],
            "audit_metadata": {
                "snapshot_sha256": snapshot.snapshot_sha256,
                "commit_sha": snapshot.commit_sha,
                "jurisdiction_id": snapshot.jurisdiction_id,
                "visibility": snapshot.visibility,
                "advisory_only": True,
                "external_effects": 0,
            },
        }
