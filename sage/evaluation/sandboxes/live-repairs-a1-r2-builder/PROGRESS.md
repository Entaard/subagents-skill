# Live repairs round-2 builder checkpoint

- Writer: `/root/live_repairs_builder`; lease active and root read-only.
- Round 1 independent verdict: failed. LIVE-01, LIVE-02, LIVE-04, and DOC-01 are verified fixed; only LIVE-03 remains open.
- Architecture cause and boundary are recorded before code changes in `sage/ARCHITECTURE.md`.
- Public seam: `pairing.py validate-native`; tests stay self-contained for clean checkout.
- Intended v3 contract: arm/execution objects before nested access; nonblank string `run_id`, `started_at`, and `finished_at`; no new timestamp parser.
- First red draft correctly exposed three failures but used an empty object that old truthiness already rejected for `finished_at`; it is retained as `red-current/`. `red-exact/` then reproduced all four exact failures before implementation, and `green-four/` passed all 11 focused methods after the execution/type guard.
- Current slice: public-CLI result/pair/arm object guards at the same v3 boundary. The arm guard is already covered by the first slice; result and pair shapes must now go red before their explicit checks.
- The first expanded-negative run is retained in `focused-final/`: product cases were green, but its test fixture removed provenance from the wrong evidence entry and raised `KeyError`. The corrected final run will use a fresh directory.
- `focused-final2/` is green: 13 methods passed. The exact critic fixtures all return structured exit 2 under the active validator in `retained-green/results.json`.
- `final-offline/` passed 92 tests with zero failures/errors/skips and no live trial/network; a fresh final gate will follow the completed documentation/test set.
- Preservation baseline: 665 prior round-1 builder/critic evidence entries hash to `c64d6be9756fce8d05036ffde551c94da1d3d0bb7c5af28b7685dc33a409ebec`; five frozen guards match, and the actual original v2 result still exits 2 with its historical error.
- Current phase: RELEASED for the separate critic. Writer lease is released with no pending process or effect. LIVE-03 remains pending critic disposition.
- Frozen v2 protocol/rubric/original result and all round-1 builder/critic evidence remain read-only.
