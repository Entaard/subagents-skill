#!/usr/bin/env python3
"""Run the maintained matrix against old/new copied validators without live history."""
import ast
import json
import re
import shutil
import sys
from checks import HERE, SAGE, R2, ROOT, BUILDER, call, save, sha

old=R2 / "candidate-source/sage/evaluation/pairing.py"
new=SAGE / "evaluation/pairing.py"
def functions(path):
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}
old_functions=functions(old); new_functions=functions(new)
changed=[name for name,value in old_functions.items() if new_functions.get(name)!=value]
assert changed==["validate_native_result"]
assert set(new_functions)-set(old_functions)=={"validate_native_shape"}
results=[]
for label,validator,expected in (("old",old,1),("current",new,0)):
    root=HERE / "portable-matrix" / label / "sage" / "evaluation"
    tests=root / "tests"; tests.mkdir(parents=True)
    for name in ("test_native_shape.py","test_live_repairs.py","support.py"):
        shutil.copy2(SAGE / "evaluation/tests" / name,tests / name)
    shutil.copytree(SAGE / "evaluation/cases",root / "cases")
    for name in ("rubric.json","live-protocol.md"):
        shutil.copy2(SAGE / "evaluation" / name,root / name)
    shutil.copy2(validator,root / "pairing.py")
    result=call([sys.executable,"-m","unittest","discover","-s",tests,"-p","test_native_shape.py","-v"])
    result.update(label=label,validator_sha256=sha(validator),no_historical_sandboxes=True,expected_exit=expected)
    assert result["exit_code"]==expected
    if label=="old": assert "FAILED (failures=51)" in result["stderr"]
    else: assert "Ran 3 tests" in result["stderr"] and result["stderr"].rstrip().endswith("OK")
    save(HERE / f"sensitivity-{label}.json",result); results.append(result)
builder_red=(BUILDER / "red/stderr.txt").read_text(); builder_green=(BUILDER / "green/stderr.txt").read_text()
assert "FAILED (failures=51)" in builder_red and builder_green.rstrip().endswith("OK")
save(HERE / "sensitivity-summary.json",dict(old_exit=results[0]["exit_code"],old_failing_subcases=51,current_exit=results[1]["exit_code"],
    current_methods_passed=3,existing_functions_changed=changed,added_function="validate_native_shape",
    v2_shared_functions_ast_unchanged=True,no_historical_sandboxes=True,builder_red_green_classification_verified=True,
    diff_whitespace=call(["git","diff","--check","--","sage"])))
print((HERE / "sensitivity-summary.json").read_text())
