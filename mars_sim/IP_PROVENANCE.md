# ANNABAN IP Provenance — Curiosity Telemetry Relay

**Conceptual author:** Jacob Wayne Kinnaird  
**System:** ANNABAN / AnnabanOS  
**Artifact:** MarsSim Curiosity Telemetry Relay  
**Status:** Simulation/design artifact

## Scope

This artifact implements a simulation-only telemetry relay boundary for a MarsSim environment.

It does **not** represent:

- NASA/JPL authorization
- access to Curiosity flight systems
- real Curiosity telemetry
- a NASA/JPL data connection
- permission to transmit to NASA/JPL
- modification of flight software

The relay produces a verifiable simulated telemetry envelope with provenance and SHA-256 integrity metadata.

## Governance invariant

```
SIMULATED TELEMETRY
        !=
REAL MISSION TELEMETRY
        !=
EXTERNAL AUTHORIZATION
        !=
FLIGHT-SYSTEM EXECUTION
```

The relay requires a `SimulationTelemetrySink` capability, preventing an arbitrary production transport from being substituted without deliberately changing the interface boundary.

## IP attribution

This repository entry records the conceptual architecture and implementation as an ANNABAN / AnnabanOS intellectual-property artifact authored by **Jacob Wayne Kinnaird**. Repository provenance records the Git commit and timestamp independently of this attribution statement.

## Economic classification

The artifact is a reusable governance and telemetry-simulation capability. Any valuation associated with it is a conceptual IP/replacement-value estimate, not evidence of a commercial transaction, NASA contract, deployment, or realized revenue.
