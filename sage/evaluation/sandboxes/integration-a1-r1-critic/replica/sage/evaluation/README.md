# Sage verification

This directory contains the frozen verification boundary and the offline product gate for the rebuilt Codex package.

Run the offline harness from the repository root:

```bash
python3 sage/evaluation/run_verification.py --mode harness
python3 sage/evaluation/run_verification.py --mode red
```

`harness` validates the frozen cases, rubric, score/status rules, and paired-comparison protocol without requiring the product. The historically named `red` mode runs the harness, every product contract test, and the focused `sage/tests/test_state.py` and `test_knowledge.py` regressions. It was expected to fail before implementation and is now the complete offline green gate; missing product is a failure, never a skip. Archived Phase tests are intentionally outside discovery.

The runner is network-free. It sets all temporary, cache, and captured-output paths beneath `sage/evaluation/sandboxes`. `--evidence-dir` may choose another child of that directory but cannot escape it. Generated evidence is not a product result.

During implementation, run one product slice without requiring later slices to be green:

```bash
mkdir -p sage/evaluation/sandboxes/state-wave/tmp
PYTHONDONTWRITEBYTECODE=1 SAGE_EVALUATION_SANDBOX="$PWD/sage/evaluation/sandboxes/state-wave" TMPDIR="$PWD/sage/evaluation/sandboxes/state-wave/tmp" python3 -m unittest discover -s sage/evaluation/tests -p 'test_product_state.py' -v

mkdir -p sage/evaluation/sandboxes/knowledge-wave/tmp
PYTHONDONTWRITEBYTECODE=1 SAGE_EVALUATION_SANDBOX="$PWD/sage/evaluation/sandboxes/knowledge-wave" TMPDIR="$PWD/sage/evaluation/sandboxes/knowledge-wave/tmp" python3 -m unittest discover -s sage/evaluation/tests -p 'test_product_knowledge.py' -v
```

The integration builder uses the same form with `test_product_install.py`. Capture retained stdout/stderr evidence beneath that wave’s sandbox; the broad `--mode red` command remains the integration gate and also proves the 16 focused state and 15 focused knowledge regressions still pass.

The product interface is frozen in [../docs/CONTRACTS.md](../docs/CONTRACTS.md). Development cases are public and may guide implementation. `holdout-boundary.json` freezes what later independent prompts may contain without revealing those prompts or expected answers. Live trials are a later gate and must not be marked passed by this harness.

`pairing.py` prepares a hash-bound manifest from an explicit evaluator case selection and validates evidence-bearing paired records:

```bash
python3 sage/evaluation/pairing.py prepare sage/evaluation/cases/development-selection.json --output sage/evaluation/sandboxes/development-pairs.json
python3 sage/evaluation/pairing.py validate RESULTS.json --manifest sage/evaluation/sandboxes/development-pairs.json
```

Each pair uses the same prompt, raw inputs, checks, acceptance criteria, installed Sage procedure, Astra root model, and sandbox conditions. Treatment uses Sage worker routing; baseline requests Astra for every eligible worker. That worker routing is the only intended difference. Order alternates by case. Outcome scores, calls, wall time, reported usage, and money are separate fields. Unavailable usage or money is JSON null and never blocks execution. A small observed set supports only case-level conclusions. The actor/scorer procedure is frozen in [live-protocol.md](live-protocol.md).
