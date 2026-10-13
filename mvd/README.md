# Human Authority Gate MVD v0.1

A minimal, dependency-free Python demonstration of a human decision boundary for allowlisted in-memory state updates.

## Run tests

From the repository root:

    python -m unittest discover -s tests -v

## Minimal example

    from mvd.human_authority_gate import HumanAuthorityGate

    gate = HumanAuthorityGate(allowed_keys={"mode"}, initial_state={"mode": "safe"})
    gate.propose(proposal_id="demo-001", actor="example-agent", key="mode", value="reviewed")
    assert gate.state["mode"] == "safe"  # still pending
    gate.decide(proposal_id="demo-001", human_id="local-operator", approve=True)
    assert gate.state["mode"] == "reviewed"
    assert gate.verify_event_chain()

## Important

This is a local demonstration, not an authenticated approval system or production safety boundary. Human identity is only a label; data is in memory; the hash chain is not a digital signature or immutable external ledger. See docs/human-authority-gate-rfc.md for the threat boundary and limitations.
