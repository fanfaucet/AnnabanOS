# Tokenized Agent Economy: Proficiency-Based Mining & Staking

- **Specification version:** 1.0.0
- **Status:** Conceptual design / pre-implementation review
- **Conceptual origin attribution:** Jacob Wayne Kinnaird
- **Repository:** fanfaucet/AnnabanOS
- **Design date:** 2026-10-17
- **Policy baseline:** Advisory-only; human authority retained; no external actuation implied
- **Evidence boundary:** This document records a design proposal and review findings. It does not establish deployed contracts, live token value, realized revenue, or legal ownership beyond the stated project attribution.

## 1. Purpose

Define a tokenized agent ecosystem in which agents develop measurable skills, are assigned to funded projects, and may receive capped token rewards for validated work. The economic loop is:

1. Create or acquire an agent.
2. Train and evaluate skills.
3. Assign the agent to an eligible project.
4. Validate useful work and calculate rewards.
5. Claim rewards and reinvest in training or additional agents.
6. Audit all changes, issuance, and treasury movements.

**Core rule:** capability, contribution, and compensation are separate concepts. Self-reported IQ, accumulated time, NFT ownership, or staking alone should not be sufficient proof of useful work or entitlement to unlimited rewards.

## 2. System boundaries

### On-chain responsibilities
- Agent ownership and authorized staking.
- Training payment and upgrade state, where practical.
- Project registration and published eligibility parameters.
- Reward budgets, emission caps, claim accounting, and event logs.
- Timelocked governance changes and emergency pause controls.

### Off-chain responsibilities
- Training execution and evaluation.
- Evidence collection for task completion and quality.
- Optional AI model scoring, with versioned evaluator metadata.
- User interface, analytics, and project discovery.

Off-chain assertions that affect token payouts require a clearly specified trust model: independent attestation, dispute process, trusted oracle, or verifiable computation. An LLM-generated score by itself is not cryptographic proof of task quality.

## 3. Proficiency and reward model

The original proposal expresses mining rate as:

`rate = baseRate × (1 + IQ/200) × (1 + skillSum/10) × (1 + experience/1000)`

This formula is straightforward to simulate but has important economic properties:
- Multipliers compound and can make issuance grow quickly.
- Skill sum and experience need explicit maximums.
- Passive time is not equivalent to productive experience.
- IQ is not a standard, objectively verifiable on-chain measurement; replace it with named benchmark scores or omit it from compensation.
- Collaboration and specialization bonuses should be earned, bounded, and independently testable.

**Recommended payout model:** calculate a base contribution reward from accepted work, then apply bounded proficiency and project multipliers. Cap each task reward, each agent's reward per epoch, each project's budget, and total protocol emissions. If the reward pool is exhausted, stop or proportionally scale payouts according to a published rule.

## 4. Illustrative emissions calculation

At 10 tokens/hour base rate and the example multiplier of 6×:
- Per hour: 60 tokens.
- Per 24-hour day: 1,440 tokens.
- Per 365-day year: 525,600 tokens per continuously rewarded agent.
- A 400,000,000-token mining allocation would fund about 761 continuously rewarded agent-years at this rate, before other emissions or unclaimed rewards.

Formula:

`annualEmissions = activeAgents × rewardedHoursPerYear × averageRewardPerHour`

These are model outputs, not forecasts, market prices, or realized earnings. The 400 million mining allocation must be enforced by contract-level accounting rather than documentation alone.

## 5. Solidity fixed-point math reference

The following library corrects the premature integer truncation in the initial draft. It is a math component only, not a complete staking or token contract. Production use requires range analysis, overflow review, tests, and integration review.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

library AgentYieldMath {
    uint256 internal constant SCALE = 1e18;
    uint256 internal constant BASE_RATE = 10e18; // 10 tokens/hour

    struct AgentDNA {
        uint256 iq;
        uint256 skillBonus;
        uint256 experience;
    }

    function miningRatePerHour(
        AgentDNA memory dna
    ) internal pure returns (uint256) {
        require(dna.iq <= 200, "IQ exceeds maximum");

        uint256 iqFactor = SCALE + (dna.iq * SCALE / 200);
        uint256 skillFactor = SCALE + (dna.skillBonus * SCALE / 10);
        uint256 experienceFactor =
            SCALE + (dna.experience * SCALE / 1000);

        uint256 rate = BASE_RATE;
        rate = rate * iqFactor / SCALE;
        rate = rate * skillFactor / SCALE;
        rate = rate * experienceFactor / SCALE;
        return rate;
    }

    function accruedYield(
        AgentDNA memory dna,
        uint256 elapsedSeconds
    ) internal pure returns (uint256) {
        return miningRatePerHour(dna) * elapsedSeconds / 3600;
    }
}
```

The sample values IQ=120, skill sum=15, and experience=500 yield 60 tokens/hour. The library does not validate DNA provenance, enforce emission limits, pay tokens, or authorize project boosts.

## 6. Contract review findings from the initial proposal

1. **ERC interface mismatch:** the initial `IERC1155` interface declares `ownerOf`, which is not part of standard ERC-1155. Use ERC-721 consistently or use ERC-1155 `balanceOf(owner, id)` and the receiver interface.
2. **Fixed-point scaling error:** the initial implementation truncates factors to integers and then divides by `10000 * 10000`, losing the intended multiplier precision.
3. **No token transfer on claim:** rewards are only accumulated in a mapping; there is no ERC-20 transfer or withdrawal path.
4. **Project boost is not enforced on-chain:** the JavaScript mock applies a conceptual boost, but the Solidity calculation does not. The external project callback needs authorization, budget checks, and failure handling.
5. **Token ID zero sentinel:** using `agentId == 0` as the unstaked marker excludes token ID zero. Use an explicit `isStaked` flag.
6. **ERC-1155 receiver support:** safe transfers require the staking contract to implement the appropriate receiver interface.
7. **Unbounded emissions:** the stated 400 million mining allocation is not enforced in the provided contract.
8. **Untrusted project callbacks:** external calls need reentrancy protection, checks-effects-interactions, and clear failure semantics.
9. **Mutable metadata trust:** NFT metadata must not be the sole authority for mutable skills, experience, or reward balances.
10. **Training is a placeholder:** enforce token payment, skill limits, authorization, cooldowns, and upgrade state transitions.

## 7. Project delegation

A project definition should include:
- Project identifier and owner.
- Eligibility rules with versioned parameters.
- Reward token and funded budget.
- Maximum reward per task, agent, and epoch.
- Accepted-work evidence and evaluation procedure.
- Boost limits and whether boosts affect base rewards or a separate project pool.
- Dispute, cancellation, and withdrawal rules.
- Start/end times and upgradeable-parameter governance.

A project must not promise yield unsupported by its funded treasury. A project-specific token is a separate asset and its distribution must not be confused with base $AGENT rewards.

## 8. Token supply and business economics

Proposed fixed supply: 1,000,000,000 $AGENT.
- Mining rewards: 40% (400,000,000).
- Ecosystem fund: 30% (300,000,000).
- Reserve: 20% (200,000,000).
- Team and advisors: 10% (100,000,000), subject to a defined vesting schedule.

These are proposed allocations, not deployed tokenomics. Before implementation, define the emission curve, halving schedule, vesting contracts, treasury permissions, and what happens when a pool is depleted. Optional transaction taxes should be evaluated against user experience, transfer compatibility, and jurisdiction-specific legal review.

Token issuance is not revenue. Model platform revenue separately from token incentives, including paying customer fees, project listing fees, subscriptions, training services, marketplace fees, and actual operating costs. Do not assume token appreciation, liquidity, or guaranteed returns.

## 9. Security and acceptance gates

### MVP gate
- Choose ERC-721 or ERC-1155 and use its standard interface correctly.
- Implement a real ERC-20 reward transfer or explicitly model a funded pull-payment design.
- Enforce the mining reserve cap and per-epoch emission limit.
- Add explicit staking state, receiver support where applicable, pause control, and reentrancy protections.
- Test duplicate staking, repeated claims, token ID zero, zero elapsed time, reward exhaustion, and unstaking.
- Add unit tests for all multiplier boundaries and precision.

### Project gate
- Verify project eligibility and published boost parameters.
- Ensure all promised rewards are funded and capped.
- Test malicious/reverting project contracts and callbacks.
- Provide dispute handling and auditable accepted-work records.

### Production gate
- Independent Solidity security audit.
- Economic stress tests across agent counts, reward rates, uptime, and treasury inflows.
- Threat model, monitoring, incident response, and key-management plan.
- Legal and compliance review appropriate to the target jurisdictions.
- Explicit human authorization for consequential changes; no autonomous external actuation by default.

## 10. Provenance and decision record

- **Conceptual contribution attribution:** Jacob Wayne Kinnaird.
- **AI-assisted review:** This document includes assistant-generated organization, arithmetic review, and a corrected illustrative Solidity math library based on the supplied concept.
- **Human-originated input:** The tokenized agent economy concept, example rates, allocations, upgrade costs, project categories, and original code were supplied in the user-provided specification.
- **Implementation distinction:** This commit is a design document and reference code only; it does not prove deployment or production readiness.
- **Decision:** Retain as a versioned design proposal; do not treat the original staking contract as deployable until the listed acceptance gates pass.
