"""Public CLI regressions for prior-selection diagnostics and abrupt staging exits."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SAGE / 'evaluation/tests'))
from support import complete_read_run, cues, dump, record, write_log

KNOWLEDGE = SAGE / 'scripts/sage_knowledge.py'
CRASH = '''
import os, sys
sys.path.insert(0, sys.argv[1])
import sage_knowledge as k
cut = sys.argv[2]
if cut == 'created':
    k.write_generation = lambda *a, **kw: os._exit(91)
elif cut == 'writing':
    original = k.atomic_write
    def write(path, data):
        if path.parent.name == 'records':
            path.write_bytes(data[:17])
            os._exit(91)
        original(path, data)
    k.atomic_write = write
else:
    original = k.os.rename
    def rename(source, target):
        if cut == 'renamed': original(source, target)
        os._exit(91)
    k.os.rename = rename
args = k.parser().parse_args(sys.argv[3:])
args.func(args)
'''


class MajorKnowledgeTests(unittest.TestCase):
    def setUp(self):
        base = Path(os.environ['SAGE_EVALUATION_SANDBOX']); base.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=base)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.store = self.root / 'store'
        self.cue_file = dump(self.root / 'cues.json', cues(operation=['resume']))
        self.source = self.root / 'source'; write_log(self.source, complete_read_run('source-1'))

    def cli(self, command, *args, error=None):
        p = subprocess.run([sys.executable, '-B', str(KNOWLEDGE), command, '--store-dir', str(self.store), *map(str, args)], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2 if error else 0, p.stderr)
        value = json.loads(p.stderr if error else p.stdout)
        if error: self.assertEqual(value['code'], error)
        return value

    def proposal(self, item, action='create'):
        return dump(self.root / 'proposal.json', dict(action=action, proposer='proposer', reviewer='reviewer', source_runs=[str(self.source)], record=item))

    def stage(self, item, generation, parent, action='create'):
        return self.cli('stage', '--proposal', self.proposal(item, action), '--generation-id', generation, '--expected-current', parent)

    def activate(self, generation, parent):
        self.cli('activate', '--generation-id', generation, '--expected-current', parent)

    def revalidate(self, previous=None):
        previous = previous if previous is not None else [dict(id='k-1', revision=1, generation_id='g-1')]
        result = self.cli('revalidate', '--previous', dump(self.root / 'previous.json', previous), '--cues', self.cue_file)
        self.assertNotIn('matches', result)
        return result['diagnostics']

    def test_exact_diagnostics_status_scope_and_rollback(self):
        self.stage(record(), 'g-1', 'none'); self.activate('g-1', 'none')
        self.assertEqual(self.revalidate()[0]['diagnostic'], 'unchanged_applicable')
        for revision, status, action in [(2, 'contested', 'contest'), (3, 'refuted', 'refute'), (4, 'retired', 'retire')]:
            item = record(revision=revision, prior_revision=revision-1, status=status)
            item['counterevidence'] = ['source-1:source-1-e-4']
            if status == 'retired': item['review'].update(retirement_basis='explicit_decision', retirement_reason='Fixture retirement')
            self.stage(item, f'g-{revision}', f'g-{revision-1}', action); self.activate(f'g-{revision}', f'g-{revision-1}')
            diagnostic = self.revalidate()[0]
            self.assertEqual(diagnostic['diagnostic'], status)
            self.assertEqual(diagnostic['current_revision'], revision)
            self.assertFalse(diagnostic['eligible'])
            self.assertEqual(self.cli('retrieve', '--cues', self.cue_file, '--limit', 3)['matches'], [])
        self.cli('rollback', '--generation-id', 'g-1', '--expected-current', 'g-4')
        old = self.revalidate([dict(id='k-1', revision=4, generation_id='g-4')])[0]
        self.assertEqual(old['diagnostic'], 'revised'); self.assertEqual(old['current_revision'], 1)
        dump(self.cue_file, cues(operation=['resume'], environment=['remote-managed']))
        self.assertEqual(self.revalidate()[0]['diagnostic'], 'out_of_scope')
        self.assertEqual(self.revalidate([dict(id='absent', revision=1, generation_id='g-4')])[0]['diagnostic'], 'not_present_in_active_generation')

    def test_ranking_displacement_and_narrowed_qualifier(self):
        self.stage(record('z-rule'), 'g-1', 'none'); self.activate('g-1', 'none')
        self.stage(record('a-rule'), 'g-2', 'g-1'); self.activate('g-2', 'g-1')
        self.assertEqual(self.cli('retrieve', '--cues', self.cue_file, '--limit', 1)['matches'][0]['id'], 'a-rule')
        prior = [dict(id='z-rule', revision=1, generation_id='g-1')]
        self.assertEqual(self.revalidate(prior)[0]['diagnostic'], 'unchanged_applicable')
        changed = record('z-rule', revision=2, prior_revision=1)
        changed['qualifier']['all']['environment'] = ['special-host']
        changed['counterevidence'] = ['source-1:source-1-e-4']
        self.stage(changed, 'g-3', 'g-2', 'correct'); self.activate('g-3', 'g-2')
        diagnostic = self.revalidate(prior)[0]
        self.assertEqual(diagnostic['diagnostic'], 'out_of_scope')
        self.assertEqual(diagnostic['qualifier']['all']['environment'], ['special-host'])

    def test_revalidation_empty_and_invalid_inventory(self):
        self.assertEqual(self.revalidate([]), [])
        self.assertEqual(self.revalidate()[0]['diagnostic'], 'not_present_in_active_generation')
        for previous in ([dict(id='k-1', revision=True, generation_id='g-1')], [dict(id='../bad', revision=1, generation_id='g-1')], [{}], {}):
            self.cli('revalidate', '--previous', dump(self.root / 'bad.json', previous), '--cues', self.cue_file, error='invalid_previous')

    def test_abrupt_stage_cuts_preserve_validation_and_all_mutations(self):
        for cut in ('created', 'writing', 'before_rename', 'renamed'):
            with self.subTest(cut=cut):
                self.store = self.root / cut
                self.stage(record('k-0'), 'g-0', 'none'); self.activate('g-0', 'none')
                self.stage(record(), 'g-1', 'g-0'); self.activate('g-1', 'g-0')
                self.stage(record('ready'), 'g-ready', 'g-1')
                published = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.store.rglob('*') if p.is_file()}
                proposal = self.proposal(record('new-rule'))
                child = subprocess.run([sys.executable, '-B', '-c', CRASH, str(KNOWLEDGE.parent), cut, 'stage', '--store-dir', str(self.store), '--proposal', str(proposal), '--generation-id', 'g-2', '--expected-current', 'g-1'], capture_output=True, text=True)
                self.assertEqual(child.returncode, 91, child.stderr)
                self.assertTrue(all(hashlib.sha256(p.read_bytes()).hexdigest() == digest for p, digest in published.items()))
                self.assertEqual(self.cli('validate')['current'], 'g-1')
                self.assertEqual(self.cli('retrieve', '--cues', self.cue_file, '--limit', 3)['generation_id'], 'g-1')
                if cut != 'renamed':
                    self.assertEqual(len(list((self.store / '.staging').iterdir())), 1)
                    self.stage(record('new-rule'), 'g-2', 'g-1')
                else:
                    self.assertEqual(list((self.store / '.staging').iterdir()), [])
                    self.cli('stage', '--proposal', proposal, '--generation-id', 'g-2', '--expected-current', 'g-1', error='revision_exists')
                self.activate('g-ready', 'g-1')
                self.cli('rollback', '--generation-id', 'g-1', '--expected-current', 'g-ready')
                self.activate('g-2', 'g-1')
                self.cli('rollback', '--generation-id', 'g-1', '--expected-current', 'g-2')
                self.cli('activate', '--generation-id', 'g-2', '--expected-current', 'g-0', error='stale_current')

    def test_unknown_and_symlink_staging_and_corrupt_committed_history_reject(self):
        self.stage(record(), 'g-1', 'none'); self.activate('g-1', 'none')
        staging = self.store / '.staging'; staging.mkdir(exist_ok=True)
        unknown = staging / 'unrecognized'; unknown.mkdir()
        self.cli('validate', error='invalid_staging')
        self.cli('stage', '--proposal', self.proposal(record('new')), '--generation-id', 'g-2', '--expected-current', 'g-1', error='invalid_staging')
        unknown.rmdir(); staging.rmdir(); staging.symlink_to(self.root / 'missing', target_is_directory=True)
        self.cli('validate', error='invalid_staging')
        staging.unlink(); staging.mkdir()
        owned = staging / 'stage-abcdefgh'; owned.mkdir(); (owned / 'records').symlink_to(self.source, target_is_directory=True)
        self.cli('validate', error='invalid_staging')
        (owned / 'records').unlink(); owned.rmdir()
        retained = self.store / 'generations/g-1/records/k-1.json'; retained.write_text(retained.read_text()+' ')
        self.cli('validate', error='generation_hash_mismatch')
        self.cli('activate', '--generation-id', 'g-1', '--expected-current', 'g-1', error='generation_hash_mismatch')


if __name__ == '__main__': unittest.main()
