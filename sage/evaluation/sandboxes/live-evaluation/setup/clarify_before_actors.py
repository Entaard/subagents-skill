"""One bounded pre-actor freeze correction; original manifests retained."""
import hashlib
import json
from pathlib import Path
import subprocess
import os
base=Path(__file__).resolve().parent
os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['TMPDIR']=str(base/'tmp')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def artifact(path):return dict(path=str(path),sha256=sha(path))
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
subprocess.run(['python3',str(base.parents[3]/'evaluation/pairing.py'),'prepare',str(base/'selection.json'),'--output',str(base/'frozen-pairs.json')],check=True,capture_output=True,env=os.environ)
inventory=json.loads((base/'initial-arm-hashes.json').read_text())
for arm in inventory:
    for row in arm['initial_files']:row['sha256']=sha(Path(row['path']))
write(base/'initial-arm-hashes.json',inventory)
setup=json.loads((base/'setup-freeze.json').read_text());setup.pop('manifest_sha256')
setup['pairs']=artifact(base/'frozen-pairs.json');setup['initial_arm_hashes']=artifact(base/'initial-arm-hashes.json')
setup['setup_sources'].append(artifact(Path(__file__)))
setup['pre_actor_revision']=dict(reason='Clarified feed TypeError versus invalid constructor ValueError before any actor started; no behavior outcome informed change.',superseded_manifests=str(base/'superseded-before-actors-v1'),unstarted_all_arms=True)
setup['manifest_sha256']=canonical(setup);write(base/'setup-freeze.json',setup)
print(json.dumps(dict(pairs=json.loads((base/'frozen-pairs.json').read_text())['manifest_sha256'],smokes=json.loads((base/'frozen-smokes.json').read_text())['manifest_sha256'],setup=setup['manifest_sha256']),indent=2))
