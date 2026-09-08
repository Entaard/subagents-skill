#!/usr/bin/env python3
import json
import sys
from checks import HERE, SAGE, OLD, LIVE, BUILDER, ROOT, call, save, sha

cli=HERE / "candidate-source/sage/evaluation/pairing.py"
retained=[]
for name in ("surface-results.json","primitive-results.json"):
    for prior in json.loads((HERE/name).read_text()):
        if prior["matched"]: continue
        result=call([sys.executable,cli,"validate-native",prior["input"],"--manifest",LIVE / "setup/frozen-pairs.json"])
        result.update(label=prior["label"],input=prior["input"],original_exit=prior["exit_code"])
        assert result["exit_code"]==prior["exit_code"]
        if prior["exit_code"]==1: assert "AttributeError" in result["stderr"]
        retained.append(result)
save(HERE / "retained-failures.json",retained)
classifications={
    "red-current":("failures=3","first draft; wrong empty-object fixture did not reproduce the fourth truthy-object failure"),
    "red-exact":("failures=4","correct exact four product-boundary failures"),
    "red-surrounding":("failures=2","result/pair object-shape product failures; arm-null already rejected"),
    "focused-final":("KeyError: 'provenance'","test-fixture error at wrong evidence index, not product validator failure"),
    "focused-final2":("Ran 13 tests","corrected fresh test run; final OK verified")}
history=[]
for label,(needle,classification) in classifications.items():
    p=BUILDER / label / "stderr.txt"; content=p.read_text(); assert needle in content
    if label=="focused-final2": assert content.rstrip().endswith("OK")
    history.append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p),classification=classification))
save(HERE / "builder-evidence-classification.json",history)
save(HERE / "source-diff.json",call(["diff","-u",OLD / "without-history/sage/evaluation/pairing.py",SAGE / "evaluation/pairing.py"]))
save(HERE / "static.json",dict(diff_whitespace=call(["git","diff","--check","--","sage"]),
    no_historical_test_dependencies=call(["rg","-n","sandboxes/live",SAGE / "evaluation/tests/test_live_repairs.py"]),
    retained_failures=len(retained),retained_validator_sha256=sha(cli)))
print(json.dumps(dict(retained_failures=len(retained),builder_history_classifications=len(history))))
