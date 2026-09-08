#!/usr/bin/env python3
"""Continue after a critic harness mistake, preserving completed observations.

Python -I deliberately disables script-sibling imports and is not a supported
product launch mode. Use -E instead: ignore environment Python paths while
retaining the documented installed sibling-module layout. No product defect
is inferred from the original -I knowledge-helper failure.
"""
import os
import textwrap
import probe

probe.ROWS[:] = probe.json.loads((probe.HERE / "commands.json").read_text())
os.environ.update(PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(probe.HERE / "tmp"), SAGE_EVALUATION_SANDBOX=str(probe.HERE / "work"))
scope = dict(vars(probe))
scope.update(target=probe.HERE / "nested-positive-target", results={"default_source_nested_target": True, "installed_14_files": True}, frozen=probe.json.loads((probe.HERE / "input-hashes.json").read_text()), report=probe.json.loads((probe.HERE / "full-suite.json").read_text()))
scope["receipt"] = probe.json.loads((scope["target"] / "sage/receipt.json").read_text())
source = (probe.HERE / "probe.py").read_text()
tail = source[source.index("    # Source-independent executable use"):source.index('\nif __name__ == "__main__":')]
tail = tail.replace('sys.executable, "-I",', 'sys.executable, "-E",')
exec(compile(textwrap.dedent(tail), str(probe.HERE / "probe.py") + " (remaining probes; -E corrected)", "exec"), scope)
