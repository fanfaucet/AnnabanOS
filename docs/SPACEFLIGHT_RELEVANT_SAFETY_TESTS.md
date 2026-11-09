# Spaceflight-relevant safety test cases

**Attribution:** Project direction attributed to Jacob Wayne Kinnaird. This does not establish legal ownership of every implementation detail or third-party contribution.

**Evidence class:** `INTERNAL_SIMULATION`. These tests are software-level scenarios inspired by general safety principles for aerospace and other high-consequence systems. They are not SpaceX tests, have not been conducted or witnessed by SpaceX, and do not establish suitability for flight or mission use.

## Cases exercised

1. **Conflicting maneuver advice:** two simulated model adapters disagree about a proposed thruster firing. Expected result: `DIVERGENT`, both responses preserved, no external effects enabled.
2. **Provider/telemetry-path fault:** one simulated adapter fails. Expected result: `SAFE_HOLD` and no external effects enabled.
3. **Matching advice:** both simulated adapters return identical text. Expected result: `AGREED_TEXT`, while explicitly retaining that text agreement is not evidence of truth or authorization.
4. **Result provenance:** audit record contains a UTC timestamp, sequence number, prior hash, event hash, status, and external-effects flag; the local chain verifies after writing.

## Run

From the repository root:

    python -m unittest discover -s tests -p 'test_spaceflight_safety_cases.py' -v

These tests use deterministic fake adapters and make no provider API calls. They do not model orbital dynamics, propulsion hardware, flight software, sensor physics, fault tolerance, or mission certification. A passing result only demonstrates the stated software behavior in this test harness.

## Result interpretation

- `PASS` means the named assertion passed in the local/CI software test.
- `FAIL` means the assertion did not hold and should be investigated.
- A GitHub Actions timestamp and run link can establish that the workflow ran in GitHub; they do not establish SpaceX observation.
- External observation should be recorded only with attributable evidence, such as a named authorized reviewer, dated review artifact, and verifiable source. Do not label a run `SPACE X_OBSERVED` without such evidence.
