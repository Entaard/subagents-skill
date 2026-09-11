# Live repairs builder checkpoint

- Writer: `/root/live_repairs_builder`
- Lease: active; root remains read-only.
- Architecture-first decision record: `sage/ARCHITECTURE.md`.
- Public seams: `sage_state.py` CLI and `pairing.py` CLI; installed Markdown is validated through an isolated install.
- TDD: LIVE-01 red (3/3 expected failures) and green (3/3 pass) are retained; LIVE-02 red (7 original-report subcases) and green (5/5 cumulative tests pass) are retained. The clean-checkout LIVE-03 public-CLI red is retained with the expected missing `validate-native` command; the first draft that depended on historical sandboxes is retained but superseded by the self-contained red.
- Historical replay policy: normal offline tests use maintained synthetic fixtures. Exact creative/seven-report replay will run separately on fresh copies under this evidence root and be labeled informed diagnostic.
- LIVE-03 is implemented as the explicit `sage-live-native-scored-results-v3` / `validate-native` path; v2 remains unchanged. LIVE-04 installed-only documentation/example is green. Focused current result is 10/10 passed.
- Informed diagnostics passed on exact copies: 22 original creative events preserved as prefix and stopped honestly; seven report copies regenerated; original v2 exit 2 retained; adapted v3 exit 0 with six separately captured subprocess exits; 2,239 protected files compared unchanged.
- Fresh complete offline gate (`final-offline2/`): 89 tests passed, zero failures/errors/skips; no live trial or network.
- Final exact-copy informed diagnostics (`informed-diagnostics-final/`) passed every repair assertion; its before/after inventory covers 2,239 protected files and is unchanged.
- Final static checks: four Python sources compile, 7 changed-document local links resolve, `git diff --check -- sage` exits 0, and the two entrypoint spines remain 25 and 19 lines.
- Current phase: RELEASED for the separate critic. Writer lease is released; no process or effect is pending. Repair claims remain pending critic disposition.
- Frozen guards: original live protocol, rubric, manifests, results, scorer artifacts, and historical reports remain read-only.
