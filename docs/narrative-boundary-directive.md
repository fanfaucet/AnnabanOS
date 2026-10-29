# Narrative Boundary and Terminology Clarity Directive

**Policy ID:** `ANNABANOS-NARRATIVE-BOUNDARY-DIRECTIVE`  
**Version:** 1.0.0  
**Status:** Proposed policy artifact; runtime enforcement is not established by this document alone.

## Purpose

Keep AnnabanOS terminology clear, autonomy-supporting, evidence-grounded, and proportionate. System rules should serve people; people should not be forced to conform to unnecessary complexity.

## Operating rules

1. **Clarity over jargon.** Prefer plain language. Define a specialized term when it adds necessary precision.
2. **Autonomy over unnecessary constraint.** Explain the purpose of mandatory controls and distinguish them from optional workflow preferences.
3. **Boundaries without overreach.** Describe permissions, consent, delivery, execution, and system authority only to the extent supported by evidence.
4. **Independent pacing.** Let people proceed at their own pace unless a documented dependency or safety requirement calls for a limit.
5. **Precision without rigidity.** Keep definitions consistent, but revise wording that creates avoidable ambiguity or friction.
6. **Evidence before attribution.** Do not infer a real person's views, feelings, motives, consent, participation, or endorsement from a simulation or from unrelated public information.
7. **Correction, not erasure.** Preserve traceable corrections. Do not claim that data was permanently purged or that a rule is enforced system-wide unless that scope and persistence have been verified.

## Provenance labels

Use explicit labels where they affect interpretation:

- `USER_PROVIDED`: supplied by a user; not independently verified.
- `SIMULATED`: fictional or hypothetical output.
- `OBSERVED`: directly visible in a specified source or system.
- `INDEPENDENTLY_VERIFIED`: checked against an identified, reliable source or reproducible result.
- `PROPOSED`: a recommendation or intended design, not yet confirmed as implemented.
- `UNVERIFIED`: evidence is insufficient to establish the claim.

Do not use `OBSERVED` or `INDEPENDENTLY_VERIFIED` as synonyms for plausible, asserted, or generated.

## Human authorization and action boundaries

- Default to advisory or simulation mode.
- Treat consequential external actions as blocked until an authorized human approves them.
- A generated message is not a delivered message.
- A delivery attempt is not proof of receipt.
- Receipt is not consent or endorsement.
- A proposed policy is not an implemented control.
- A successful test is not proof of production deployment.

## Review checklist

Before finalizing an output or ledger entry, ask:

- Can the intended reader understand the wording without unnecessary jargon?
- Does every mandatory constraint have a stated purpose?
- Are user choice and independent pacing preserved where safe?
- Are simulated content, observed facts, and verified outcomes clearly separated?
- Are claims about people attributed only when evidence supports them?
- Are implementation, deployment, persistence, and external effects described accurately?
- Can an ambiguous term or mistaken claim be corrected with a traceable record?

If a check fails, revise the wording or mark the claim as pending verification. Do not invent a replacement fact.

## Acceptance criteria

A review passes when:
- mandatory rules state their purpose;
- unexplained jargon is removed or defined;
- provenance labels are present for material claims;
- simulated dialogue is not attributed as verified real-world speech;
- no external action or persistent change is claimed without evidence; and
- corrections retain a clear scope and audit trail.

## Implementation status

This commit adds a human-readable directive and a machine-readable policy definition. It does **not** by itself wire a runtime policy engine, change deployed systems, or establish automatic enforcement. Runtime integration and tests should be a separate, reviewable change.
