"""Boundary checks for AnnabanAI claims; deterministic and advisory-only.

This module flags missing simulation labels and unsupported-looking metrics.
It does not verify facts, sources, identity, or legal ownership.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Iterable

SIMULATION_LABELS = (
    "INTERNAL_SIMULATION",
    "CONCEPTUAL / SIMULATION-ONLY",
    "SIMULATED",
    "simulation-only",
    "conceptual simulation",
)
METRIC_PATTERNS = (
    re.compile(r"(?i)\b(?:lattice expansion|joy[- ]density|human sovereignty|thought[- ]output bandwidth)\s*[:=]?\s*[+−-]?\d+(?:\.\d+)?\s*%?"),
    re.compile(r"(?i)\b(?:efficiency uplift|integration overhead reduction)\s*[:=]?\s*(?:up to\s*)?\d+(?:\.\d+)?\s*%"),
    re.compile(r"(?i)\$\s?\d+(?:\.\d+)?\s*(?:B|M|K|billion|million|thousand)\b"),
)
EVIDENCE_LABELS = ("independently_verified", "source supplied by user; independently checked: yes")


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    excerpt: str


@dataclass(frozen=True)
class LintResult:
    validation_status: str
    findings: tuple[Finding, ...]

    def to_dict(self) -> dict:
        return {"validation_status": self.validation_status,
                "findings": [asdict(item) for item in self.findings],
                "note": "Lint flags wording patterns only; it does not establish truth."}


def lint_claim_text(text: str) -> LintResult:
    """Flag unlabeled simulation-style metrics; never certify a claim as true."""
    findings: list[Finding] = []
    lowered = text.casefold()
    has_simulation_label = any(label.casefold() in lowered for label in SIMULATION_LABELS)
    for pattern in METRIC_PATTERNS:
        for match in pattern.finditer(text):
            if not has_simulation_label and not any(label.casefold() in lowered for label in EVIDENCE_LABELS):
                findings.append(Finding(
                    code="METRIC_BOUNDARY_LABEL_MISSING",
                    message="Quantified claim needs an explicit evidence/simulation boundary label.",
                    excerpt=match.group(0)[:180],
                ))
            elif has_simulation_label:
                findings.append(Finding(
                    code="SIMULATED_METRIC_NOT_VERIFIED",
                    message="Simulation label found; metric remains unverified and must not be presented as measured fact.",
                    excerpt=match.group(0)[:180],
                ))
    if not findings:
        findings.append(Finding(
            code="NO_PATTERN_MATCH",
            message="No configured metric pattern matched. This is not a factual verification result.",
            excerpt="",
        ))
    failed = any(f.code == "METRIC_BOUNDARY_LABEL_MISSING" for f in findings)
    return LintResult("FAILED" if failed else "REVIEW_REQUIRED", tuple(findings))


def lint_record(record: dict) -> list[str]:
    """Return structural issues for a claim-register record."""
    issues = []
    required = ("claim_id", "claim", "claim_type", "boundary_label", "source_status")
    for field in required:
        if not record.get(field):
            issues.append(f"missing_required_field:{field}")
    if record.get("boundary_label") == "independently_verified" and record.get("source_status") != "independent_check":
        issues.append("independent_verification_requires_source_status_independent_check")
    if record.get("claim_type") == "metric" and not record.get("falsifiable_basis"):
        issues.append("metric_requires_falsifiable_basis_or_explicit_unavailable_note")
    return issues
