# AnnabanOS — AI-Native Governance Operating System

<p align="center">
  <img src="https://img.shields.io/badge/AnnabanOS-6C5CE7?style=for-the-badge&labelColor=0F0F1A" alt="AnnabanOS">
  <img src="https://img.shields.io/badge/×-F5F6FA?style=for-the-badge&labelColor=0F0F1A" alt="×">
  <img src="https://img.shields.io/badge/Kimi-00D2D3?style=for-the-badge&labelColor=0F0F1A" alt="Kimi">
</p>

<p align="center"><i>"Where Intelligence Meets Intent"</i></p>

---

## Overview

**AnnabanOS** is a deterministic governance middleware for probabilistic AI systems. Built in collaboration with [Kimi](https://kimi.moonshot.cn), it provides a complete operating layer for routing, constraining, observing, and auditing LLM operations — without claiming that any model output is truth.

## The Four Responsibilities

| # | Responsibility | Description |
|---|---------------|-------------|
| 1 | **Route** | Select models using latency, cost, and task-type heuristics |
| 2 | **Constrain** | Apply deterministic policy sidecars to text and metadata |
| 3 | **Observe** | Emit signal heuristics (ambiguity, authority markers) without epistemic claims |
| 4 | **Record** | Write append-only, hash-chained audit events for verification and replay |

> **Core Principle:** The orchestrator decides *process*, not *truth*. Governance scores are operational metadata only.

---

## Quick Start

```bash
# Install
pip install -e .

# Run the orchestrator
annaban

# Run with options
annaban --prompt "Summarize the operational risks of a delayed shipment" --task-type fast
```

---

## System Pipeline

```
Prompt → Router → Model Adapter → Constraint Layer → Output Normalizer → Audit Logger → Output
```

---

## Project Structure

```
AnnabanOS/
├── annaban_benchmark/      # Core governance middleware
│   ├── orchestrator.py     # Single-turn pipeline
│   ├── router.py           # Model selection & fallback chains
│   ├── constraints.py      # Deterministic policy sidecars
│   ├── signals.py          # Non-epistemic signal heuristics
│   ├── audit.py            # Append-only hash-chained audit log
│   └── harness.py          # Reproducible benchmark harness
├── api/                    # API endpoints and adapters
├── llm_agents/             # LLM agent implementations
├── kubernetes/             # Deployment manifests
├── datasets/               # JSONL prompt suites for evaluation
├── examples/               # Usage examples and tutorials
├── heritage/               # Historical versions and migrations
├── tests/                  # Test suite
├── BRANDING.md             # Brand identity guidelines
├── COLLABORATION.md        # Kimi collaboration framework
└── README.md               # This file
```

---

## Benchmark Metrics

- **Policy Pass Rate** — Percentage of outputs meeting constraint requirements
- **Cost Per Task** — Average operational cost per inference
- **Agreement Signal** — Statistical alignment between model outputs
- **Audit Integrity** — Cryptographic verification of log chains
- **Governance Score** — Operational composite (not a correctness score)

---

## Collaboration

This project is developed in active collaboration with **Kimi**, Moonshot AI's advanced AI assistant. See [COLLABORATION.md](COLLABORATION.md) for our partnership framework, attribution principles, and collaboration history.

### Key Collaboration Areas

- Architecture design and system scaffolding
- Documentation and brand identity
- Code review and security analysis
- Benchmarking and evaluation frameworks

---

## Brand

See [BRANDING.md](BRANDING.md) for the complete AnnabanOS brand identity — including color palette, typography, voice guidelines, and collaboration marks.

---

## License

See [LICENSE](LICENSE) for details.

---

<p align="center">
  <sub>Built with 💜 by the AnnabanOS Team × Kimi</sub>
</p>
