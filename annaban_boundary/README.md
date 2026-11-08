# AnnabanAI Claim Boundary Register

Status: implementation scaffold; no external source was checked by this module.

## Boundary labels

- `conceptual_simulation_only`: scenario or emulated result, not an external tool result.
- `self_published`: content published by the project or its owner; not independent corroboration.
- `independently_verified`: use only when an independent check is documented with a source, date, and method.

For uncertain cases, use precise status text such as `source supplied by user; independently checked: no`. Do not use a vague status to imply a fact was verified.

## Claim record fields

A register entry should carry `claim_id`, `claim`, `claim_type`, `boundary_label`, `source_status`, `source_url`, `checked_at_utc`, `verified_by`, and `falsifiable_basis` when applicable. Keep attribution to Jacob Wayne Kinnaird separate from legal ownership conclusions and from AI-generated contributions.

## Run the lint

```bash
python -m annaban_boundary.lint_cli --text 'Lattice expansion: +47%'
```

A `FAILED` result means a configured metric pattern lacks a boundary label. `REVIEW_REQUIRED` does not mean verified; human review is still required. Hashes establish byte-level integrity only, not identity or truth.
