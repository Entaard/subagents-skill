# Sage

This directory contains Sage for Codex. Phase 0 establishes the host-neutral contracts and frozen evaluation. Phase 1 provides the full explicit-only Codex Light experience: bounded native orchestration for research, review, implementation, and verification; portable run tools; a manual promoted-knowledge workflow; and a receipt-bound lifecycle.

## Layout

- [`policy/`](policy/) contains the canonical host-neutral orchestration policy.
- [`artifacts/`](artifacts/) contains schemas, generated types, and validation fixtures.
- [`runtime/protocol-v0/`](runtime/protocol-v0/) contains the provisional runtime protocol and security model.
- [`docs/phase0/`](docs/phase0/) contains the Phase 0 ownership, lifecycle, and promotion contracts.
- [`docs/phase1/equivalence.md`](docs/phase1/equivalence.md) maps the full Claude Sage behavior and the intentional Codex-plan deltas.
- [`evaluation/phase-1/`](evaluation/phase-1/) contains the frozen Phase 1 pilot definition.
- [`skills/`](skills/) contains the explicit-only `$sage` and `$sage-promote` Codex skills.
- [`lib/`](lib/) and [`scripts/`](scripts/) contain artifact, memory, promotion, lifecycle, and validation tools.
- [`knowledge/`](knowledge/) is the source-only global-promotion destination; installed promotion uses the state overlay.
- [`install.sh`](install.sh) and [`uninstall.sh`](uninstall.sh) own only the Codex distribution. The repository-root scripts remain the unchanged `sage-claude` lifecycle.

Run the complete Phase 0 validation from the repository root:

```sh
python3 sage/scripts/check-phase0.py --self-test
```

Run the complete Phase 1 implementation and behavior matrix:

```sh
python3 sage/scripts/check-phase1.py
```

Install, update, or remove Sage for Codex from this directory:

```sh
./sage/install.sh
./sage/uninstall.sh --dry-run --yes
./sage/uninstall.sh --yes
```

The default command wrappers are installed under `~/.local/bin`; add that directory to `PATH` if your shell does not already include it. The receipt records custom destinations supplied to the lifecycle scripts.

Light handover writes mandatory hash-bound `handoff.json`. Human-readable `handoff.md` is optional and is never resume authority. Regenerate it with `sage-light handoff-projection <run-id>` and verify the existing projection with `sage-light handoff-projection <run-id> --check`.

## Phase 1 pilot gate

The 20-pair pilot has **not started**. The frozen preregistration requires a hard 250,000 normalized input-plus-output token cap for each complete arm. Codex CLI 0.151.0 exposes usage telemetry and an unqualified thread-goal budget, but its schema does not prove the required accounting unit, hard enforcement, or aggregate root-and-subagent scope. The executable RL-01 driver boundary is also unavailable. Under the frozen rule, zero outcomes may be generated until those controls exist.

[`evaluation/phase-1/STATUS.md`](evaluation/phase-1/STATUS.md) records the evidence. Reproduce the gate with:

```sh
python3 sage/evaluation/phase-1/pilot.py preflight
```

Exit status 2 means the preregistered start gate is blocked; it is not a failed task outcome or a managed-mode decision.
