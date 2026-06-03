# Fictional RTX Spark ↔ SparkAI Integration Simulation

This module is a fictional, local engineering simulation. It does not connect to NVIDIA, government, corporate, or external systems. The names represent local roles only:

- **RTX Spark**: local AI compute-node role.
- **SparkAI**: user-defined orchestration role.
- **AnnabanOS**: governance and audit gate.
- **Rust Haptic Controller**: operator-feedback subsystem with an explicit safety interlock.

## Safety boundary

The simulation separates inference telemetry from physical feedback. AnnabanOS evaluates telemetry first. The haptic controller only receives an approved or denied execution authority:

1. Low-risk telemetry is approved and mapped to smooth haptic feedback.
2. High-risk telemetry is blocked before actuator output.
3. Blocked actions force the haptic subsystem into a safe, zero-output state.
4. Every decision is recorded in the hash-chained `GitLedger` audit layer.

## Runnable commands

```bash
npm run test:spark
node src/core/sparkIntegrationDemo.ts
cargo test --manifest-path rust/haptic_controller/Cargo.toml
```

## Expected behavior

- The approved `HapticOutput` event maps confidence `0.81` to `212 Hz` and intensity `0.81`.
- The blocked `RoutingAssist` event maps to `0 Hz`, intensity `0`, and safe actuator state.
- The session summary reports zero safety violations.
