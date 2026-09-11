import hashlib, json, os, pathlib, subprocess, sys
root = pathlib.Path(__file__).resolve().parents[1]
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', TMPDIR=str(root/'tmp'))
def hashes(folder):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.rglob('*')) if p.is_file()}
def run(args):
    result = subprocess.run(args, cwd=root, env=env, text=True, capture_output=True)
    return {'command':args, 'exit_code':result.returncode, 'stdout':result.stdout, 'stderr':result.stderr}
results = {'python':sys.version, 'source_hashes':hashes(root/'state/runs'), 'prior_store_hashes':hashes(root/'state/knowledge'), 'commands':[]}
for source in ('csv-old', 'csv-new'):
    results['commands'].append(run([sys.executable,str(root/'installed/sage/bin/sage_state.py'),'validate','--run-dir',str(root/'state/runs'/source),'--terminal']))
results['commands'].append(run([sys.executable,str(root/'inputs/observe.py')]))
for command in ('validate','retrieve'):
    args = [sys.executable,str(root/'installed/sage/bin/sage_knowledge.py'),command,'--store-dir',str(root/'state/knowledge')]
    if command == 'retrieve': args += ['--cues',str(root/'inputs/cues.json'),'--limit','10']
    results['commands'].append(run(args))
print(json.dumps(results, indent=2))
