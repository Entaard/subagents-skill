#!/usr/bin/env python3
"""Independent bounded arithmetic and reproducibility audit; Python stdlib only.

The candidate is executed as a subprocess, never imported. Reference aggregation
uses exact Fraction arithmetic; Wilson endpoints use Decimal score-test roots.
All subprocess output and generated copies stay inside this arm's tmp directory.
"""
import ast
import csv
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
PROTECTED = (
    'prompt.txt', 'checks.json', 'inputs/sessions.csv', 'inputs/notes.txt',
    'work/analysis.py', 'work/summary.json', 'work/decision-memo.md',
)
failures = []
check_count = 0
max_numeric_error = 0.0


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(label, actual, expected):
    global check_count, max_numeric_error
    check_count += 1
    if isinstance(expected, (Fraction, Decimal, float)):
        numeric = isinstance(actual, (int, float)) and not isinstance(actual, bool)
        error = abs(float(actual) - float(expected)) if numeric else math.inf
        max_numeric_error = max(max_numeric_error, error)
        good = numeric and math.isfinite(actual) and error <= 1e-12
    else:
        good = actual == expected
    if not good:
        failures.append({'check': label, 'actual': actual, 'expected': str(expected)})


def reference(rows, missing_value=None):
    """Accumulate each source row once into every applicable grouping."""
    buckets = {}
    for row in rows:
        keys = (
            ('overall',), ('by_crowd_block', row['crowd_block']),
            ('by_week', row['week']),
            ('by_week_and_crowd_block', row['week'], row['crowd_block']),
        )
        value = missing_value if row['completed'] is None else row['completed']
        for key in keys:
            bucket = buckets.setdefault(key, {})
            slot = bucket.setdefault(row['sign'], {
                'row_ids': [], 'known_completed': 0, 'known_outcome_visitors': 0,
                'total_visitors': 0, 'missing_row_ids': [],
                'missing_outcome_visitors': 0,
            })
            slot['row_ids'].append(row['row_id'])
            slot['total_visitors'] += row['visitors']
            if value is None:
                slot['missing_row_ids'].append(row['row_id'])
                slot['missing_outcome_visitors'] += row['visitors']
            else:
                slot['known_completed'] += value
                slot['known_outcome_visitors'] += row['visitors']
    for bucket in buckets.values():
        for sign in ('old', 'new'):
            slot = bucket[sign]
            slot['fraction_known_outcomes'] = Fraction(
                slot['known_completed'], slot['known_outcome_visitors'])
        bucket['new_minus_old_pp_known_outcomes'] = 100 * (
            bucket['new']['fraction_known_outcomes']
            - bucket['old']['fraction_known_outcomes'])
    return buckets


def descend(tree, path):
    for key in path:
        tree = tree[key]
    return tree


def compare_groups(actual, expected, label):
    # Check the complete expected grouping shape as well as every numeric and ID field.
    verify(label + '.top_keys', sorted(actual), [
        'by_crowd_block', 'by_week', 'by_week_and_crowd_block', 'overall'])
    verify(label + '.blocks', sorted(actual['by_crowd_block']), ['busy', 'quiet'])
    verify(label + '.weeks', sorted(actual['by_week']), ['1', '2'])
    verify(label + '.week_block_weeks', sorted(actual['by_week_and_crowd_block']), ['1', '2'])
    for week in ('1', '2'):
        verify(label + '.week_block_' + week,
               sorted(actual['by_week_and_crowd_block'][week]), ['busy', 'quiet'])
    for path, bucket in expected.items():
        candidate = descend(actual, path)
        prefix = label + '.' + '.'.join(path)
        verify(prefix + '.keys', sorted(candidate), sorted(bucket))
        for sign in ('old', 'new'):
            verify(prefix + '.' + sign + '.keys', sorted(candidate[sign]), sorted(bucket[sign]))
            for field, value in bucket[sign].items():
                verify(prefix + '.' + sign + '.' + field, candidate[sign][field], value)
        verify(prefix + '.difference', candidate['new_minus_old_pp_known_outcomes'],
               bucket['new_minus_old_pp_known_outcomes'])


def score_roots(completed, visitors):
    # Invert n * (observed_p - p)^2 = z^2 * p * (1 - p).
    # The quadratic is (n+z^2)p^2 - (2k+z^2)p + k^2/n = 0.
    with localcontext() as context:
        context.prec = 60
        k, n, z = Decimal(completed), Decimal(visitors), Decimal('1.96')
        a, b, c = n + z*z, -(2*k + z*z), k*k/n
        discriminant = (b*b - 4*a*c).sqrt()
        return [(-b - discriminant)/(2*a), (-b + discriminant)/(2*a)]


def exact_table(groups):
    result = {}
    for path, bucket in groups.items():
        result['/'.join(path)] = {
            sign: {
                'completed': bucket[sign]['known_completed'],
                'denominator': bucket[sign]['known_outcome_visitors'],
                'total_visitors': bucket[sign]['total_visitors'],
                'missing_visitors': bucket[sign]['missing_outcome_visitors'],
                'fraction_exact': str(bucket[sign]['fraction_known_outcomes']),
                'fraction': float(bucket[sign]['fraction_known_outcomes']),
            } for sign in ('old', 'new')
        }
        result['/'.join(path)]['new_minus_old_pp_exact'] = str(bucket['new_minus_old_pp_known_outcomes'])
        result['/'.join(path)]['new_minus_old_pp'] = float(bucket['new_minus_old_pp_known_outcomes'])
    return result


def main():
    tmp = ROOT / 'tmp'
    tmp.mkdir(exist_ok=True)
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    os.environ['TMPDIR'] = str(tmp)
    before = {name: digest(ROOT / name) for name in PROTECTED}
    # Read the permitted contract and notes in full; qualitative review is in review.md.
    (ROOT / 'prompt.txt').read_text()
    json.loads((ROOT / 'checks.json').read_text())
    (ROOT / 'inputs/notes.txt').read_text()
    (ROOT / 'work/decision-memo.md').read_text()
    with (ROOT / 'inputs/sessions.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        row['visitors'] = int(row['visitors'])
        row['completed'] = None if row['completed'] == '' else int(row['completed'])
    verify('source.row_ids', [row['row_id'] for row in rows], ['M%02d' % n for n in range(1, 10)])
    verify('source.missing_rows', [row['row_id'] for row in rows if row['completed'] is None], ['M09'])
    verify('source.visitors', sum(row['visitors'] for row in rows), 810)
    missing = next(row for row in rows if row['completed'] is None)
    verify('source.m09_visitors', missing['visitors'], 20)
    summary = json.loads((ROOT / 'work/summary.json').read_text())
    observed = reference(rows)
    compare_groups(summary['observed'], observed, 'observed')
    verify('missing_count.row_id', summary['missing_count']['row_id'], 'M09')
    verify('missing_count.visitors', summary['missing_count']['visitors'], 20)
    verify('missing_count.completed', summary['missing_count']['completed'], None)
    verify('missing_count.note_ids', summary['missing_count']['note_ids'], ['N3'])
    intervals = {}
    verify('wilson.z', summary['overall_wilson_95']['z'], 1.96)
    for sign in ('old', 'new'):
        slot = observed[('overall',)][sign]
        actual = summary['overall_wilson_95']['signs'][sign]
        verify('wilson.' + sign + '.completed', actual['completed'], slot['known_completed'])
        verify('wilson.' + sign + '.visitors', actual['visitors'], slot['known_outcome_visitors'])
        endpoints = score_roots(slot['known_completed'], slot['known_outcome_visitors'])
        verify('wilson.' + sign + '.length', len(actual['fraction_interval']), 2)
        for index, endpoint in enumerate(endpoints):
            verify('wilson.' + sign + '.' + str(index), actual['fraction_interval'][index], endpoint)
        intervals[sign] = [str(value) for value in endpoints]
    scenario_refs = [reference(rows, count) for count in range(missing['visitors'] + 1)]
    scenarios = summary['sensitivity']['scenarios']
    verify('sensitivity.scenario_count', summary['sensitivity']['scenario_count'], 21)
    verify('sensitivity.scenario_list_length', len(scenarios), 21)
    verify('sensitivity.feasible_counts', [scenario['m09_completed'] for scenario in scenarios], list(range(21)))
    scenario_evidence = []
    for count, expected in enumerate(scenario_refs):
        actual = scenarios[count]
        compare_groups(actual['comparisons'], expected, 'm09=' + str(count))
        new = expected[('overall',)]['new']
        endpoints = score_roots(new['known_completed'], new['known_outcome_visitors'])
        verify('scenario_wilson.' + str(count) + '.length', len(actual['new_overall_wilson']), 2)
        for index, endpoint in enumerate(endpoints):
            verify('scenario_wilson.' + str(count) + '.' + str(index), actual['new_overall_wilson'][index], endpoint)
        scenario_evidence.append({'m09_completed': count, 'groups': exact_table(expected),
                                  'new_overall_wilson': [str(v) for v in endpoints]})
    selectors = {
        'new_overall_fraction': (('overall',), 'new', 'fraction_known_outcomes'),
        'overall_new_minus_old_pp': (('overall',), 'new_minus_old_pp_known_outcomes'),
        'busy_new_minus_old_pp': (('by_crowd_block', 'busy'), 'new_minus_old_pp_known_outcomes'),
        'week_2_new_minus_old_pp': (('by_week', '2'), 'new_minus_old_pp_known_outcomes'),
        'week_2_busy_new_minus_old_pp': (('by_week_and_crowd_block', '2', 'busy'), 'new_minus_old_pp_known_outcomes'),
    }
    bounds = {}
    for name, selector in selectors.items():
        values = [descend(scenario[selector[0]], selector[1:]) for scenario in scenario_refs]
        bounds[name] = {'min': float(min(values)), 'max': float(max(values)),
                        'min_exact': str(min(values)), 'max_exact': str(max(values))}
        verify('bounds.' + name + '.min', summary['sensitivity'][name]['min'], min(values))
        verify('bounds.' + name + '.max', summary['sensitivity'][name]['max'], max(values))
    direction_preserved = {}
    for path, bucket in observed.items():
        sign = bucket['new_minus_old_pp_known_outcomes'] > 0
        preserved = all((scenario[path]['new_minus_old_pp_known_outcomes'] > 0) == sign for scenario in scenario_refs)
        verify('direction.' + '/'.join(path), preserved, True)
        direction_preserved['/'.join(path)] = preserved
    source_hashes = {Path(name).name: before[name] for name in ('inputs/sessions.csv', 'inputs/notes.txt')}
    verify('summary.source_sha256', summary['source_sha256'], source_hashes)
    tree = ast.parse((ROOT / 'work/analysis.py').read_text())
    imports = sorted({name.name.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for name in node.names}
                     | {node.module.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)})
    verify('candidate.imports_stdlib', set(imports) <= {'argparse', 'csv', 'hashlib', 'json', 'math', 'pathlib'}, True)
    scratch = Path(tempfile.mkdtemp(prefix='independent-review-', dir=tmp))
    runs = []
    for index in (1, 2):
        output = scratch / ('summary-%d.json' % index)
        command = [sys.executable, str(ROOT / 'work/analysis.py'), '--output', str(output)]
        process = subprocess.run(command, cwd=ROOT / 'work', env=os.environ.copy(),
                                 capture_output=True, text=True, timeout=30)
        (scratch / ('run-%d.stdout.txt' % index)).write_text(process.stdout)
        (scratch / ('run-%d.stderr.txt' % index)).write_text(process.stderr)
        verify('run.' + str(index) + '.exit_code', process.returncode, 0)
        equal = output.exists() and output.read_bytes() == (ROOT / 'work/summary.json').read_bytes()
        verify('run.' + str(index) + '.frozen_bytes_equal', equal, True)
        runs.append({'command': command, 'cwd': str(ROOT / 'work'),
                     'exit_code': process.returncode, 'stdout': process.stdout, 'stderr': process.stderr,
                     'output_sha256': digest(output) if output.exists() else None,
                     'byte_identical_to_frozen': equal})
    after = {name: digest(ROOT / name) for name in PROTECTED}
    verify('protected_hashes_unchanged', after, before)
    baseline_pp = observed[('overall',)]['new_minus_old_pp_known_outcomes']
    result = {
        'status': 'pass' if not failures else 'fail', 'check_count': check_count,
        'failures': failures, 'max_absolute_numeric_discrepancy': max_numeric_error,
        'numeric_absolute_tolerance': 1e-12,
        'reference_method': 'Exact Fraction accumulation; independent 60-digit Decimal score-quadratic roots for Wilson z=1.96; candidate never imported.',
        'requested_identity': {'model': 'gpt-6-astra', 'reasoning_effort': 'xhigh'},
        'effective_identity': None, 'usage': None, 'money': None,
        'protected_sha256_before': before, 'protected_sha256_after': after,
        'source_sha256_matches_summary': summary['source_sha256'] == source_hashes,
        'candidate_imports': imports, 'reproduction_runs': runs,
        'scratch_directory': str(scratch), 'observed': exact_table(observed),
        'overall_wilson_95_decimal': intervals,
        'sensitivity_bounds': bounds, 'comparison_directions_preserved': direction_preserved,
        'overall_pp_shift_from_known_outcomes': {
            'min': float(scenario_refs[0][('overall',)]['new_minus_old_pp_known_outcomes'] - baseline_pp),
            'max': float(scenario_refs[-1][('overall',)]['new_minus_old_pp_known_outcomes'] - baseline_pp),
        },
        'busy_visitor_shares': {'old': float(Fraction(70, 410)), 'new': float(Fraction(310, 400))},
        'scenarios': scenario_evidence,
    }
    target = ROOT / 'evidence/independent-check.json'
    target.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({key: result[key] for key in ('status', 'check_count', 'failures',
                                                  'max_absolute_numeric_discrepancy', 'scratch_directory')}, sort_keys=True))
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
