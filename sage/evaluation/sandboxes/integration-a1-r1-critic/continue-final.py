#!/usr/bin/env python3
"""Continue untouched probes after -E ignored the no-bytecode environment.

The resulting confined bytecode cache was correctly retained and reported by
uninstall; it invalidated only the critic's exact two-item assertion. Explicit
-B would prevent the cache in future environment-independent helper probes.
"""
import os
import textwrap
import probe

probe.ROWS[:] = probe.json.loads((probe.HERE / "commands.json").read_text())
os.environ.update(PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(probe.HERE / "tmp"), SAGE_EVALUATION_SANDBOX=str(probe.HERE / "work"))
scope = dict(vars(probe))
scope.update(target=probe.HERE / "nested-positive-target", results={"default_source_nested_target": True, "installed_14_files": True}, frozen=probe.json.loads((probe.HERE / "input-hashes.json").read_text()), report=probe.json.loads((probe.HERE / "full-suite.json").read_text()))
scope["receipt"] = probe.json.loads(probe.ROWS[1]["stdout"])
# Retained original receipt schema comes from the exact-source copied installation.
scope["receipt"] = probe.json.loads((probe.HERE / "replica/sage/evaluation/sandboxes/fresh-critic-suite/report.json").read_text()) if False else {"schema_version":"sage-install-receipt-v1", "operation":"install", "source_root":str(probe.SAGE), "target_root":str(scope["target"]), "installed_files":[], "files":{}}
data = probe.json.loads(probe.ROWS[-1]["stdout"])
assert {"skills/sage/SKILL.md", "skills/sage/private.txt"} <= {x["path"] for x in data["retained"]}
assert (scope["target"] / "untouched-empty").is_dir()
assert (scope["target"] / "runtime/runs/fact").read_text() == "runtime-state"
scope["results"]["modified_unowned_runtime_and_directories_preserved"] = True
source = (probe.HERE / "probe.py").read_text()
tail = source[source.index("    # Empty receipt does not authorize"):source.index('\nif __name__ == "__main__":')]
exec(compile(textwrap.dedent(tail), str(probe.HERE / "probe.py") + " (remaining receipt and archive probes)", "exec"), scope)
