# AnnabanOS RPM Governor — Product Blueprint v0.1

**Status:** Design proposal / simulation-first  
**Scope:** Six-phase IPMSM supervisory governor and compute-cluster fan telemetry separation  
**Hardware status:** This document does not indicate that a physical motor, inverter, rotor, or fan is connected. Values below are candidate test points or illustrative assumptions, not certified limits.

## 1. Product objective

Provide an auditable supervisory layer that distinguishes motor-shaft state from compute-cluster cooling state, checks model and telemetry integrity, and recommends a safe response when electrical, thermal, mechanical, or sensor constraints are approached.

Do not use an average RPM as a governor input. Verification is based on time-aligned samples, model validity, limit margins, and repeatable state transitions. The five RPM values below are test points only; they are not measured operating statistics or certified limits.

## 2. Operating-point register

| ID | RPM | Current interpretation | Evidence needed before treating as a limit |
|---|---:|---|---|
| T01 | 4,000 | Candidate base-speed test point | Torque/current map and voltage margin |
| T02 | 8,590 | Estimated voltage-ceiling point | Reproduced dq model, inverter voltage convention, current vector, DC-bus limits |
| T03 | 12,000 | Candidate high-speed / constant-power test point | Power, loss, cooling, rotor, magnet, bearing, and inverter envelopes |
| T04 | 13,850 | Earlier rotor-stress estimate | Geometry-specific stress analysis, material allowables, fatigue and retention review |
| T05 | 15,000 | Simulated overspeed fault-injection point | Simulation only until a qualified test facility and manufacturer-approved limits exist |

Record dwell time and the full speed/load/current history at each point. Calculate duty-cycle statistics only from timestamped samples with known sampling gaps; calculate thermal soak from the validated loss model and thermal time constants, not from a mean of test-point labels.

## 3. Separate telemetry domains

### Motor-shaft telemetry
- shaft_rpm — mechanical rotor speed, with timestamp and source.
- electrical_frequency_hz — derived from pole-pair count and shaft speed.
- phase_current_a / dq_current_a — measured or estimated currents, clearly labelled.
- dc_bus_voltage_v, phase_voltage_v, modulation_index.
- torque_estimate_nm, torque_residual_nm.
- stator_temp_c, magnet_temp_c where available, bearing_temp_c, coolant_temp_c.
- rotor_stress_estimate_mpa — model output, not a direct measurement unless supported by an actual instrument.
- sensor_quality, sample_age_ms, model_version, fault_flags.

### Compute-cluster / cooling telemetry
- fan_rpm, fan_pwm_pct, inlet_temp_c, outlet_temp_c, gpu_temp_c, cpu_temp_c, fan_fault.
- Device identity and sensor provenance must be explicit.

These domains require different metric names, units, device IDs, alert rules, and control authorities. A cooling-fan RPM must never enter the motor-shaft overspeed comparator. A shared dashboard may display both domains but must not merge their physical state or safety rails.

## 4. Proposed governor states

1. NORMAL — inputs valid and monitored margins inside approved envelopes.
2. DERATE — a validated operating margin is narrowing; recommend bounded torque/power reduction.
3. PRESERVE — model, telemetry, or mechanical margin is uncertain or outside the normal envelope; inhibit escalation and request conservative handling.
4. SAFE_HOLD — a defined hard-limit or integrity event requests a safe stop/hold through an independently engineered protection path.

State definitions, thresholds, and transitions require review against the selected motor, inverter, and safety architecture. The software governor is not a substitute for certified inverter protections, hardware interlocks, or a manufacturer's rotor-speed rating.

Suggested priority: invalid/stale critical sensor or hard-limit event → protection request; otherwise integrity or envelope uncertainty → PRESERVE; approaching validated soft limit → DERATE; all checks healthy → NORMAL. SAFE_HOLD must not depend on a single unvalidated model estimate.

## 5. Physics and units

For a conventional dq representation, the torque equation is:

$$
T_e = \frac{3}{2}p\left[\lambda_m i_q+(L_d-L_q)i_d i_q\right]
$$

Confirm the coefficient and current definition for the selected six-phase winding and transform convention before using this equation as an acceptance oracle. Record whether voltage values are phase peak, phase RMS, line-to-line RMS, or DC-bus voltage; never compare unlike conventions.

At the proposed 12,000 RPM / 100 kW point, the ideal shaft torque requirement is about 79.6 N·m. Treat this as a consistency check only. Acceptance requires the model to report electrical input, shaft output, and losses with an energy-balance discrepancy within a documented tolerance; motor-specific continuous operation cannot be inferred from this calculation.

Field weakening must be demonstrated by a functioning controller/model, not inferred from RPM alone. Validate negative d-axis current, voltage saturation, current-vector limits, and recovery behavior. Do not label 8,590 RPM an exact transition until the coupled model reproduces it.

## 6. Stress-test campaign

All initial tests are simulation-only. Each run records model/version, initial conditions, parameter set, injected fault, timestamps, peak values, state transitions, uncertainty, and pass/fail rationale.

- **T01 — Current-vector / torque map:** sweep current vectors within the defined current limit; compare predicted torque with an independent calculation. Do not assume 250–280 N·m without the relevant current vector and validated machine constants.
- **T02 — Voltage saturation / field weakening:** sweep speed and load; verify voltage convention, current constraints, negative d-axis current, and transition/recovery hysteresis.
- **T03 — High-speed power envelope:** evaluate 12,000 RPM and the 100 kW scenario against every active limit; include speed-dependent load and loss maps.
- **T04 — Torque reversal / regeneration:** test +200 to −200 N·m command transitions in simulation; track DC-bus energy, inverter limits, braking capability, and rate limits.
- **T05 — Phase-set / inverter fault:** inject a loss at 8,000 RPM; recompute achievable torque from remaining topology, currents, voltages, thermal margins, and control strategy. Never assume capability simply halves.
- **T06 — Thermal escalation:** couple temperature-dependent resistance and loss to a thermal network; verify derating and trip priority.
- **T07 — Overspeed:** simulate 15,000 RPM and compare with explicitly defined model limits. Compare rotor stress against a geometry- and material-specific approved limit at each simulated speed. Do not substitute a generic speed-squared ratio for stress analysis or fatigue/retention assessment. Do not conduct a destructive physical overspeed test based on this blueprint.
- **T08 — Sensor/model integrity:** inject stale or reordered packets, speed disagreement, failed temperature sensors, invalid units, and torque residual excursions. Confirm the governor rejects or quarantines bad inputs.
- **T09 — Competing fault priority:** combine overspeed indication, thermal trip, and telemetry loss; verify deterministic priority and independent protection requests.
- **T10 — Cooling-domain isolation:** inject a fan-RPM spike or missing fan packet and verify it cannot directly alter motor-shaft RPM state or bypass motor safety logic. Thermal observations may inform a separate, explicitly designed derating path.

## 7. Verification targets and evidence

The following are **provisional software/telemetry verification targets**, not motor safety limits. Confirm or revise them against the actual sensor, controller, simulator, and system requirements before using them as release gates.

| Check | Initial verification target | How to verify |
|---|---|---|
| RPM signal identity | 100% of samples include device ID, metric name, unit, timestamp, source, and measured/estimated flag | Schema validation; reject ambiguous or unitless samples |
| Timestamp ordering | No silent acceptance of out-of-order samples; every rejected/reordered sample is counted | Inject reordered and duplicate packets |
| Telemetry freshness | Mark data stale when age exceeds the configured source-specific deadline; use 100 ms only as an initial simulator default, not a physical safety setting | Replay delayed, frozen, and dropped packets |
| Packet delivery | Report received, missing, duplicate, rejected, and late counts; do not hide losses behind an average | Run a 10-minute synthetic stream and compare sender/receiver sequence numbers |
| RPM channel isolation | Zero cross-routing of fan RPM into shaft-speed comparisons in the test suite | Feed extreme fan-RPM values while holding shaft telemetry constant; assert motor governor inputs do not change |
| Deterministic state logic | Identical version, inputs, and configuration produce identical state-transition records | Replay the same captured scenario at least 100 times |
| Fault detection | Each injected fault in T05–T10 is detected or explicitly classified as not detectable; no silent pass | Automated fault-injection coverage report |
| Model residuals | Define residuals per quantity and set limits from calibration/validation data; no universal mixed-unit threshold | Report torque in N·m, current in A, voltage in V, temperature in °C, each with separate tolerances |
| Energy balance | Report input power, shaft power, and modeled losses; set allowable discrepancy from numerical solver convergence and model validation | Run convergence study across solver tolerances and time steps |
| Thermal behavior | Validate against documented thermal parameters and reference data before assigning temperature trip values | Parameter sensitivity and transient-response tests |
| Speed envelope | Every soft/hard speed limit is linked to a named requirement and source; missing limits block physical release | Requirement traceability check |
| Test report completeness | 100% of runs contain configuration hash, model version, initial conditions, fault schedule, extrema, transitions, and verdict | Validate report schema on every run |

A provisional 1 kHz simulation/telemetry rate may be used to test software timing, but it is not a requirement for every sensor and does not establish that a physical system can safely operate at that rate. Use source-specific sample rates and deadlines. Report p50, p95, p99, and maximum end-to-end latency rather than only a mean.

## 8. Acceptance criteria

A run is acceptable only when:
- Units, timestamps, sensor source, quality, and model version are present.
- Motor RPM and cooling-fan RPM are stored and evaluated independently.
- Numerical integration and current/voltage constraints are tested, including non-zero electrical dynamics where expected.
- Residuals are separately normalized or dimensionally separated; unlike units are not combined into an unexplained scalar threshold.
- State transitions are reproducible from recorded inputs.
- Soft-limit recommendations and hard-protection requests are distinct and auditable.
- Failed, uncertain, and untested cases remain visible; no dashboard label implies physical validation that has not occurred.
- No physical operating limit is promoted from an illustrative simulation value without traceable engineering evidence.

A run is acceptable only when:
- Units, timestamps, sensor source, quality, and model version are present.
- Motor RPM and cooling-fan RPM are stored and evaluated independently.
- Numerical integration and current/voltage constraints are tested, including non-zero electrical dynamics where expected.
- Residuals are normalized or dimensionally separated; unlike units are not combined into an unexplained scalar threshold.
- State transitions are reproducible from recorded inputs.
- Soft-limit recommendations and hard-protection requests are distinct and auditable.
- Failed, uncertain, and untested cases remain visible; no dashboard label implies physical validation that has not occurred.

## 9. Proposed architecture

Drive-cycle / fault scenario → Load model → IPMSM physics model → Controller model → Fault manager → AnnabanOS supervisory governor → Immutable test report.

A separate path handles compute-cluster sensors → Cooling telemetry service → Cluster dashboard. A read-only aggregation layer may display both. Any cross-domain policy must be explicit, reviewed, and incapable of confusing the identity or units of the two RPM signals.

## 10. Evidence and release ladder

- **L0 — Concept:** equations, assumptions, and test definitions.
- **L1 — Reproducible simulation:** deterministic scenarios, tests, and saved run artifacts.
- **L2 — Independent model review:** numerical and physical review by qualified reviewers.
- **L3 — Hardware-in-the-loop:** authorized lab setup, interlocks, risk assessment, and approved limits.
- **L4 — Manufacturer-qualified physical validation:** instrumented tests under approved procedures.
- **L5 — Operational release:** documented safety case, monitoring, change control, and maintenance process.

Do not promote a claim to a higher level without evidence from that level.

## 11. Product principle

**Verified telemetry and validated limits govern decisions.** AnnabanOS preserves traceability and human authority by separating measured data, model estimates, operating assumptions, and safety decisions. This blueprint is a design proposal, not a claim of hardware connection, motor certification, or validated operating limits.
