# Sage for Codex

Sage is an explicit Codex workflow for demanding tasks: define observable quality, use the smallest useful team, preserve durable run facts, verify independently, and report evidence honestly. `$sage-promote` is a separate workflow that reviews closed runs and lands bounded, reversible knowledge. There is no active Claude adapter, managed scheduler, or automatic lesson extraction in this rebuild.

The active package is deliberately small:

- `skills/sage/` and `skills/sage-promote/` contain the two explicit-only skill packages and their linked references.
- `scripts/sage_state.py` validates and projects append-only run state.
- `scripts/sage_knowledge.py` retrieves and lands immutable knowledge generations.
- `install.sh`, `uninstall.sh`, and the source-only `scripts/sage-lifecycle.py` manage the receipt-bound installation.
- `archive/legacy/` preserves the superseded implementation as inert, hash-inventoried history.

The root `CONTEXT.md` describes the superseded cross-host product. For this Codex-only package, its Light/Managed split, 30-percent handover trigger, and source-global promotion destination are historical terms, not active behavior. The current contract is [ARCHITECTURE.md](ARCHITECTURE.md) plus [docs/CONTRACTS.md](docs/CONTRACTS.md).

## Install, update, and uninstall

Choose an explicit Codex package root. The [official Codex skill guide](https://learn.chatgpt.com/docs/build-skills) documents user skills under `$HOME/.agents/skills`, so `$HOME/.agents` is the recommended target root. Installation never infers or creates runtime state, and this repository does not install into the home directory during its tests:

```sh
bash sage/install.sh --target-root "$HOME/.agents"
```

The source defaults to this `sage/` directory. A sandbox or vendored package can name it explicitly:

```sh
bash sage/install.sh \
  --target-root "$HOME/.agents" \
  --source-root /path/to/sage
```

Run the same install command to update. Update proceeds only when every previously owned destination still matches its receipt hash and every new destination is unowned. Predictable path, parent-type, ownership, and receipt conflicts are reported before mutation. With the recommended target, the receipt and helpers are under `$HOME/.agents/sage/`; the runtime state root remains a separate explicit path.

Uninstall preflights predictable parent/type conflicts, removes only unchanged receipt-owned files, reports edited or replaced paths it retained, and leaves runtime runs and knowledge stores alone. The operation is conservative but is not a crash-atomic multi-file transaction; unexpected I/O can still interrupt it:

```sh
bash sage/uninstall.sh --target-root "$HOME/.agents"
```

## Run and resume

Invoke `$sage` explicitly for a new task. Source-tree state operations use the source helper and an explicit run directory:

```sh
python3 sage/scripts/sage_state.py init \
  --run-dir /path/to/state/runs/example \
  --run-id example \
  --objective "Deliver the requested artifact" \
  --criteria /path/to/criteria.json
python3 sage/scripts/sage_state.py snapshot --run-dir /path/to/state/runs/example --write
python3 sage/scripts/sage_state.py report --run-dir /path/to/state/runs/example --write
```

From an installation, resume with the installed sibling helper and a fresh explicit native-agent observation file:

```sh
python3 "$HOME/.agents/sage/bin/sage_state.py" resume \
  --run-dir /path/to/state/runs/example \
  --agents /path/to/agents.json
```

`resume` is advisory. Persist accepted proposed observations with `append`, then regenerate the snapshot. See the installed `skills/sage/references/state.md` and `recovery.md` for the event and recovery boundaries; they work without this source documentation.

## Promote closed-run evidence

Invoke `$sage-promote` separately. It accepts only integrity-valid terminal run directories with reconciled effects. The workflow uses distinct proposer, refuter, and reviewer actors for a real change, then stages and activates through the knowledge helper. Source and installed retrieval examples are:

```sh
python3 sage/scripts/sage_knowledge.py retrieve \
  --store-dir /path/to/state/knowledge \
  --cues /path/to/cues.json --limit 3

python3 "$HOME/.agents/sage/bin/sage_knowledge.py" validate \
  --store-dir /path/to/state/knowledge
```

Staging requires a reviewed proposal and explicit source-run paths; activation and rollback require the expected current generation. The complete installed procedure and proposal schema are in `skills/sage-promote/references/promotion.md` and `knowledge.md`.

## Offline verification

From the repository root:

```sh
python3 sage/evaluation/run_verification.py --mode harness
python3 sage/evaluation/run_verification.py --mode red
```

`harness` checks the frozen evaluation machinery. The historically named `red` mode is now the complete offline gate: evaluation tests plus the focused state and knowledge regressions. It uses only `sage/evaluation/sandboxes/`, performs no network or live trials, and makes no claim about task quality, model placement, token use, or cost savings.
