# Sage

This directory contains the Sage implementation. Phase 0 establishes contracts, schemas, fixtures, a provisional runtime protocol, and the frozen Phase 1 evaluation without changing the existing Claude distribution at the repository root.

## Layout

- [`policy/`](policy/) contains the canonical host-neutral orchestration policy.
- [`artifacts/`](artifacts/) contains schemas, generated types, and validation fixtures.
- [`runtime/protocol-v0/`](runtime/protocol-v0/) contains the provisional runtime protocol and security model.
- [`docs/phase0/`](docs/phase0/) contains the Phase 0 ownership, lifecycle, and promotion contracts.
- [`evaluation/phase-1/`](evaluation/phase-1/) contains the frozen Phase 1 pilot definition.
- [`scripts/`](scripts/) contains schema generation, fixture maintenance, and Phase 0 validation tools.

Run the complete Phase 0 validation from the repository root:

```sh
python3 sage/scripts/check-phase0.py --self-test
```
