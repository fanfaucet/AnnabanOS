from annaban_boundary.lint import lint_claim_text, lint_record


def test_unlabeled_metric_fails():
    result = lint_claim_text("Lattice expansion: +47%")
    assert result.validation_status == "FAILED"
    assert result.findings[0].code == "METRIC_BOUNDARY_LABEL_MISSING"


def test_simulated_metric_is_flagged_not_verified():
    result = lint_claim_text("INTERNAL_SIMULATION: Lattice expansion: +47%")
    assert result.validation_status == "REVIEW_REQUIRED"
    assert result.findings[0].code == "SIMULATED_METRIC_NOT_VERIFIED"


def test_plain_text_does_not_get_a_truth_certificate():
    result = lint_claim_text("AnnabanAI is a governance-first architecture.")
    assert result.validation_status == "REVIEW_REQUIRED"
    assert "not a factual verification" in result.findings[0].message


def test_independent_label_requires_independent_check_status():
    record = {
        "claim_id": "CLM-001",
        "claim": "A test source was checked",
        "claim_type": "artifact",
        "boundary_label": "independently_verified",
        "source_status": "self_published",
    }
    assert "independent_verification_requires_source_status_independent_check" in lint_record(record)


def test_metric_requires_falsifiable_basis():
    record = {
        "claim_id": "MET-001",
        "claim": "Efficiency uplift: 5%",
        "claim_type": "metric",
        "boundary_label": "self_published",
        "source_status": "self_published",
    }
    assert "metric_requires_falsifiable_basis_or_explicit_unavailable_note" in lint_record(record)
