# Runtime paths and discovery

Read before opening any Sage or promotion run, retrieving knowledge, or locating a run for report/resume. Resolve the helper belonging to the loaded package: installed skills use `<target-root>/sage/bin/{sage_state.py,sage_knowledge.py}`; source development uses `sage/scripts/`. The installation directory contains code and its ownership receipt, not runtime history.

## Resolve once, then pin

```text
python3 SAGE_STATE paths
```

This read-only command returns absolute `state_root`, `runs_dir`, `references_dir`, `store_dir`, `root_source`, and `root_exists`. Both helpers use the same precedence: explicit `--state-root`, then `SAGE_STATE_ROOT`, then `$CODEX_HOME/sage`, then `~/.codex/sage`. Root overrides must be absolute (a leading `~` is expanded); relative or empty configuration is an error. There is no installer-owned root setting. Use a standing environment setting for a persistent override, or pass the user's explicit root to `paths --state-root PATH`.

State the returned root and run ID to the user. Pin `ROOT` to that absolute root and pass `--state-root ROOT` throughout this invocation, including knowledge operations. Resolve once more in a later invocation so the current user configuration remains authoritative. An absent root is normal on first use: reads create nothing; `init` creates the run. A permission failure preserves the selected root and is reported; obtain the necessary filesystem authority instead of inventing a repository-local fallback.

## Open and retain every invocation

Every `$sage` invocation that performs work, including inline work, opens a run before execution; `$sage-promote` opens its own coordinator run. Report/resume locates the existing run. Tiny work may have one root task and zero workers. If the user explicitly forbids persistence, honor that instruction and report that this invocation produces no durable history for promotion.

Choose a unique ID (for example date, task slug, and a short unique suffix). Create criteria before `init`; keep subsequent coordination inputs and evidence under the returned run directory when practical.

```text
python3 SAGE_STATE init --state-root ROOT --run-id ID --objective TEXT --criteria criteria.json
python3 SAGE_STATE append --state-root ROOT --run-id ID --events wave.jsonl
python3 SAGE_STATE snapshot --state-root ROOT --run-id ID --write --summary
```

`init` returns `run_dir: ROOT/runs/ID` and `discoverable: true`. Reusing an occupied ID fails; resume the intended run or select a new ID. Keep authoritative events append-only and close using the [state contract](state.md). Return the exact run/report path at handoff.

The low-level `--run-dir` interface remains for explicit legacy access and isolated test fixtures. An external `init` returns `discoverable: false` plus a warning; explicitly targeting the selected root's exact `runs/ID` location instead receives canonical collision checks and truthful `discoverable: true`. It is not the normal invocation path and is mutually exclusive with `--state-root`. Tests must supply isolated paths or a temporary absolute root. Occupied canonical IDs reject even when their directory is empty. The `runs`, `run-references`, and `knowledge` namespaces must be real directories, not symlinks.

## Locate history

```text
python3 SAGE_STATE list-runs --state-root ROOT --limit 20 --offset 0
```

The inventory reads only direct canonical runs and explicitly registered legacy references. Each entry reports its origin, absolute locator, status, eligibility, and log hash, or a quarantine reason. It does not load evidence bodies or derive lessons. Main Sage uses this metadata only to locate a user-requested report/resume; task-time knowledge still comes exclusively from the knowledge helper. Promotion bounds its source set from this inventory before examining source evidence.

Entries sort by ID/origin; `next_offset` identifies another page. A page may contain only active or quarantined runs. Inspect further pages within the agreed source budget before claiming there are no eligible sources. Report the inspected extent and exclusions. `root_exists: false`, an empty inventory, active-only history, quarantined sources, and reviewed evidence yielding no reusable rule are different outcomes. An empty page alone does not justify a learning `no_change` claim. Inventory is a point-in-time observation; revalidate selected sources before staging.

For report/resume, use `--run-id ID --state-root ROOT` with every state command. IDs also resolve registered legacy runs. If the user has not identified one run and the inventory contains multiple plausible choices, ask which run; do not choose by directory modification time.

## Recover scattered historical runs

For known paths outside the central root:

```text
python3 SAGE_STATE register --state-root ROOT --run-dir /absolute/legacy/run
python3 SAGE_STATE list-runs --state-root ROOT --limit 20
```

Registration requires a valid terminal run with reconciled effects. It writes only `ROOT/run-references/ID.json`, binding the original absolute directory and exact log hash. Repeating the identical registration is safe. It neither moves nor copies evidence, rewrites source logs, promotes knowledge, or resumes a task. Keep the original directory and referenced artifacts available; a missing or changed source becomes quarantined. ID conflicts fail without overwriting either run. Registration is cooperative bookkeeping under the single-writer rule, not a physical lease or an archival backup.

An active legacy run is resumed by its explicit path and registered after honest closure. Invalid history stays unchanged and is reported. Recovery scans only user-supplied historical locations; a missing central root is not authorization to search unrelated directories. If expected history is absent, name the root searched and request its old location instead of concluding that no tasks were tracked.
