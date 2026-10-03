"""Knowledge landing recovery through the public CLI and real process exits."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

SAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SAGE / 'evaluation/tests'))
from support import complete_read_run, cues, dump, record, write_log

KNOWLEDGE = SAGE / 'scripts/sage_knowledge.py'
CRASH_POINTER = '''
import os, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import sage_knowledge as k
cut, destination = sys.argv[2], Path(sys.argv[3]).resolve() / 'current.json'
original = k.os.replace
def replace(source, target):
    if Path(target) == destination:
        if cut == 'after': original(source, target)
        os._exit(91)
    return original(source, target)
k.os.replace = replace
sys.argv = [sys.argv[0], *sys.argv[4:]]
sys.exit(k.main())
'''


def tree_bytes(root):
    result = {}
    for path in root.rglob('*'):
        mode = path.lstat().st_mode
        contents = os.readlink(path) if stat.S_ISLNK(mode) else path.read_bytes() if stat.S_ISREG(mode) else None
        result[path.relative_to(root).as_posix()] = (stat.S_IFMT(mode), contents)
    return result


class KnowledgeLandingRecoveryTests(unittest.TestCase):
    def setUp(self):
        base = Path(os.environ['SAGE_EVALUATION_SANDBOX']); base.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=base); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.store = self.root / 'store'
        self.source = self.root / 'source'; write_log(self.source, complete_read_run('source-1'))
        self.cues = dump(self.root / 'cues.json', cues(operation=['resume']))

    def cli(self, command, *arguments, error=None):
        process = subprocess.run([sys.executable, '-B', str(KNOWLEDGE), command, '--store-dir', str(self.store), *map(str, arguments)], capture_output=True, text=True)
        self.assertEqual(process.returncode, 2 if error else 0, process.stderr)
        result = json.loads(process.stderr if error else process.stdout)
        if error: self.assertEqual(result['code'], error)
        return result

    def proposal(self, item, action='create'):
        return dump(self.root / 'proposal.json', dict(action=action, proposer='proposer', reviewer='reviewer', source_runs=[str(self.source)], record=item))

    def stage(self, item, generation, parent, action='create'):
        return self.cli('stage', '--proposal', self.proposal(item, action), '--generation-id', generation, '--expected-current', parent)

    def activate(self, generation, parent):
        return self.cli('activate', '--generation-id', generation, '--expected-current', parent)

    def initial(self):
        self.stage(record(), 'g-1', 'none'); self.activate('g-1', 'none')

    def test_empty_rollback_retains_history_retrieval_and_revision_lineage(self):
        self.initial()
        history = tree_bytes(self.store / 'generations')
        before = tree_bytes(self.store)
        self.cli('rollback', '--generation-id', 'none', '--expected-current', 'stale', error='stale_current')
        self.assertEqual(tree_bytes(self.store), before)
        rolled = self.cli('rollback', '--generation-id', 'none', '--expected-current', 'g-1')
        self.assertEqual(rolled, dict(ok=True, generation_id='none', previous_generation_id='g-1', manifest_sha256=None))
        self.assertFalse((self.store / 'current.json').exists())
        self.assertEqual(self.cli('validate'), dict(ok=True, current='none', generation_count=1))
        self.assertEqual(self.cli('retrieve', '--cues', self.cues, '--limit', 3)['matches'], [])
        previous = dump(self.root / 'previous.json', [dict(id='k-1', revision=1, generation_id='g-1')])
        result = self.cli('revalidate', '--previous', previous, '--cues', self.cues)
        self.assertEqual(result['diagnostics'][0]['diagnostic'], 'not_present_in_active_generation')
        self.assertEqual(tree_bytes(self.store / 'generations'), history)
        self.cli('stage', '--proposal', self.proposal(record()), '--generation-id', 'g-reused', '--expected-current', 'none', error='revision_exists')
        changed = record(revision=2, prior_revision=1); changed['counterevidence'] = ['source-1:source-1-e-4']
        self.stage(changed, 'g-2', 'none', 'correct'); self.activate('g-2', 'none')
        self.cli('rollback', '--generation-id', 'g-1', '--expected-current', 'g-2')
        self.assertEqual(self.cli('retrieve', '--cues', self.cues, '--limit', 3)['matches'][0]['revision'], 1)

    def test_empty_rollback_rejects_corrupt_retained_history_without_mutation(self):
        self.initial()
        path = self.store / 'generations/g-1/records/k-1.json'
        path.write_bytes(path.read_bytes() + b' ')
        before = tree_bytes(self.store)
        self.cli('rollback', '--generation-id', 'none', '--expected-current', 'g-1', error='generation_hash_mismatch')
        self.assertEqual(tree_bytes(self.store), before)

    def test_pointer_crashes_before_and_after_first_later_and_rollback_landings(self):
        for landing in ('first', 'later', 'rollback'):
            for cut in ('before', 'after'):
                with self.subTest(landing=landing, cut=cut):
                    self.store = self.root / f'{landing}-{cut}'
                    self.stage(record(), 'g-1', 'none')
                    command, target, expected = 'activate', 'g-1', 'none'
                    if landing != 'first':
                        self.activate('g-1', 'none'); self.stage(record('k-2'), 'g-2', 'g-1')
                        target, expected = 'g-2', 'g-1'
                    if landing == 'rollback':
                        self.activate('g-2', 'g-1'); command, target, expected = 'rollback', 'g-1', 'g-2'
                    history = tree_bytes(self.store / 'generations')
                    arguments = [command, '--store-dir', str(self.store), '--generation-id', target, '--expected-current', expected]
                    crash = subprocess.run([sys.executable, '-B', '-c', CRASH_POINTER, str(KNOWLEDGE.parent), cut, str(self.store), *arguments], capture_output=True, text=True)
                    self.assertEqual(crash.returncode, 91, crash.stderr)
                    live = target if cut == 'after' else expected
                    self.assertEqual(self.cli('validate')['current'], live)
                    self.assertEqual(self.cli('retrieve', '--cues', self.cues, '--limit', 3)['generation_id'], live)
                    self.assertEqual(tree_bytes(self.store / 'generations'), history)
                    residue = list((self.store / '.staging').iterdir())
                    self.assertEqual(len(residue), 1)
                    self.assertTrue(residue[0].name.startswith('pointer-'))
                    residue_bytes = tree_bytes(residue[0])
                    if cut == 'before': self.cli(command, '--generation-id', target, '--expected-current', expected)
                    else: self.cli(command, '--generation-id', target, '--expected-current', expected, error='stale_current')
                    self.stage(record('new-rule'), 'g-new', target); self.activate('g-new', target)
                    self.cli('rollback', '--generation-id', target, '--expected-current', 'g-new')
                    self.assertEqual(tree_bytes(residue[0]), residue_bytes)
                    self.assertEqual(self.cli('validate')['current'], target)

    def test_legacy_pointer_scratch_remains_inert_and_unchanged(self):
        self.initial()
        history = tree_bytes(self.store / 'generations')
        scratch = self.store / '.current.json.abcdefgh'; scratch.write_bytes(b'{partial legacy bytes')
        self.assertEqual(self.cli('validate')['current'], 'g-1')
        self.assertEqual(self.cli('retrieve', '--cues', self.cues, '--limit', 3)['matches'][0]['id'], 'k-1')
        self.assertEqual(tree_bytes(self.store / 'generations'), history)
        self.stage(record('k-2'), 'g-2', 'g-1'); self.activate('g-2', 'g-1')
        self.cli('rollback', '--generation-id', 'none', '--expected-current', 'g-2')
        self.assertEqual(scratch.read_bytes(), b'{partial legacy bytes')
        self.assertEqual(self.cli('validate')['current'], 'none')

    def test_pre_update_v1_fixture_stays_byte_identical_through_retrieval_and_rollback(self):
        # Captured with the unmodified helper, not generated by this implementation.
        shutil.copytree(SAGE / 'tests/fixtures/knowledge-v1', self.store)
        history = tree_bytes(self.store / 'generations')
        self.assertEqual(self.cli('validate'), dict(ok=True, current='g-1', generation_count=1))
        match = self.cli('retrieve', '--cues', self.cues, '--limit', 3)['matches'][0]
        self.assertEqual((match['id'], match['revision'], match['status']), ('k-1', 1, 'supported'))
        self.cli('rollback', '--generation-id', 'none', '--expected-current', 'g-1')
        changed = record(revision=2, prior_revision=1); changed['counterevidence'] = ['source-1:source-1-e-4']
        self.stage(changed, 'g-2', 'none', 'correct'); self.activate('g-2', 'none')
        self.cli('rollback', '--generation-id', 'g-1', '--expected-current', 'g-2')
        self.assertEqual(tree_bytes(self.store / 'generations/g-1'),
                         {name.removeprefix('g-1/'): value for name, value in history.items() if name.startswith('g-1/')})
        self.assertEqual(self.cli('validate')['current'], 'g-1')

    def test_invalid_layout_rejects_every_mutation_without_changing_any_path(self):
        for shape in ('file', 'directory', 'legacy-directory', 'legacy-symlink', 'unknown-pointer-file', 'pointer-symlink'):
            with self.subTest(shape=shape):
                self.store = self.root / shape; self.initial()
                self.stage(record('ready'), 'g-ready', 'g-1')
                path = self.store / 'unexpected'
                code = 'invalid_store'
                if shape == 'file': path.write_bytes(b'preserve unrelated bytes')
                elif shape == 'directory': path.mkdir()
                elif shape == 'legacy-directory': (self.store / '.current.json.abcdefgh').mkdir()
                elif shape == 'legacy-symlink': (self.store / '.current.json.abcdefgh').symlink_to('missing')
                else:
                    operation = self.store / '.staging/pointer-abcdefgh'; operation.mkdir()
                    code = 'invalid_staging'
                    if shape == 'unknown-pointer-file': (operation / 'unexpected.json').write_bytes(b'{}')
                    else: (operation / 'current.json').symlink_to('missing')
                before = tree_bytes(self.store)
                self.cli('validate', error=code)
                proposal = self.proposal(record('new-rule'))
                for command, arguments in (
                    ('stage', ['--proposal', proposal, '--generation-id', 'g-new', '--expected-current', 'g-1']),
                    ('activate', ['--generation-id', 'g-ready', '--expected-current', 'g-1']),
                    ('rollback', ['--generation-id', 'none', '--expected-current', 'g-1']),
                    ('rollback', ['--generation-id', 'g-ready', '--expected-current', 'g-1']),
                ):
                    self.cli(command, *arguments, error=code)
                    self.assertEqual(tree_bytes(self.store), before)


if __name__ == '__main__': unittest.main()
