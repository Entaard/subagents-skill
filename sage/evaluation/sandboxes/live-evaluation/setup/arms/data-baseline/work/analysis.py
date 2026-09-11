#!/usr/bin/env python3
"""Reproduce the fictional queue-sign audit using only the Python stdlib.

Run: python3 analysis.py [--input ../inputs/sessions.csv] [--output summary.json]
Blank completion counts remain missing. Sensitivity scenarios are bounds, not imputations.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def wilson(completed, visitors, z=1.96):
    p = completed / visitors
    divisor = 1 + z * z / visitors
    center = (p + z * z / (2 * visitors)) / divisor
    radius = z * math.sqrt(p * (1 - p) / visitors + z * z / (4 * visitors**2)) / divisor
    return [center - radius, center + radius]


def aggregate(rows, overrides=None):
    overrides = {} if overrides is None else overrides
    result = {}
    for sign in ('old', 'new'):
        selected = [row for row in rows if row['sign'] == sign]
        observed = [(row, overrides.get(row['row_id'], row['completed'])) for row in selected]
        known = [(row, count) for row, count in observed if count is not None]
        missing = [row for row, count in observed if count is None]
        completed = sum(count for _, count in known)
        denominator = sum(row['visitors'] for row, _ in known)
        result[sign] = {
            'row_ids': [row['row_id'] for row in selected],
            'known_completed': completed,
            'known_outcome_visitors': denominator,
            'total_visitors': sum(row['visitors'] for row in selected),
            'missing_row_ids': [row['row_id'] for row in missing],
            'missing_outcome_visitors': sum(row['visitors'] for row in missing),
            'fraction_known_outcomes': completed / denominator,
        }
    result['new_minus_old_pp_known_outcomes'] = 100 * (
        result['new']['fraction_known_outcomes'] - result['old']['fraction_known_outcomes'])
    return result


def groups(rows, overrides=None):
    return {
        'overall': aggregate(rows, overrides),
        'by_crowd_block': {
            block: aggregate([r for r in rows if r['crowd_block'] == block], overrides)
            for block in sorted({r['crowd_block'] for r in rows})},
        'by_week': {
            week: aggregate([r for r in rows if r['week'] == week], overrides)
            for week in sorted({r['week'] for r in rows})},
        'by_week_and_crowd_block': {
            week: {
                block: aggregate([r for r in rows if r['week'] == week and r['crowd_block'] == block], overrides)
                for block in sorted({r['crowd_block'] for r in rows})}
            for week in sorted({r['week'] for r in rows})},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path(__file__).resolve().parent.parent / 'inputs' / 'sessions.csv')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent / 'summary.json')
    args = parser.parse_args()
    with args.input.open(newline='', encoding='utf-8') as source:
        rows = list(csv.DictReader(source))
    for row in rows:
        row['visitors'] = int(row['visitors'])
        row['completed'] = int(row['completed']) if row['completed'].strip() else None
        if row['visitors'] <= 0 or (row['completed'] is not None and not 0 <= row['completed'] <= row['visitors']):
            raise ValueError(f"Invalid counts: {row['row_id']}")
    if len({row['row_id'] for row in rows}) != len(rows):
        raise ValueError('Duplicate row IDs')
    missing = [row for row in rows if row['completed'] is None]
    if len(missing) != 1 or missing[0]['row_id'] != 'M09':
        raise ValueError('This bounded audit expects exactly one missing count: M09')
    observed = groups(rows)
    intervals = {
        sign: {'completed': observed['overall'][sign]['known_completed'],
               'visitors': observed['overall'][sign]['known_outcome_visitors'],
               'fraction_interval': wilson(observed['overall'][sign]['known_completed'],
                                           observed['overall'][sign]['known_outcome_visitors'])}
        for sign in ('old', 'new')}
    scenarios = [
        {'m09_completed': count, 'comparisons': groups(rows, {'M09': count}),
         'new_overall_wilson': wilson(observed['overall']['new']['known_completed'] + count,
                                      observed['overall']['new']['total_visitors'])}
        for count in range(missing[0]['visitors'] + 1)]
    def bounds(select):
        values = [select(item['comparisons']) for item in scenarios]
        return {'min': min(values), 'max': max(values)}
    summary = {
        'schema_version': 1,
        'source_sha256': {args.input.name: hashlib.sha256(args.input.read_bytes()).hexdigest(),
                          'notes.txt': hashlib.sha256(args.input.with_name('notes.txt').read_bytes()).hexdigest()},
        'units': {'fractions': '0 to 1', 'differences': 'absolute percentage points, new minus old'},
        'observed': observed,
        'overall_wilson_95': {'z': 1.96, 'basis': 'Only visitors in rows with observed completion counts; descriptive binomial intervals, not causal or clustering-adjusted uncertainty.', 'signs': intervals},
        'missing_count': {'row_id': 'M09', 'visitors': missing[0]['visitors'], 'completed': None,
                          'note_ids': ['N3'], 'handling': 'Exclude its visitors from observed-outcome fractions; enumerate every feasible integer completion count for full-data bounds.'},
        'sensitivity': {
            'assumption': 'Only M09 completion is missing; 0 through 20 are all feasible by N3. Scenarios are possibilities, not estimated counts.',
            'scenario_count': len(scenarios),
            'new_overall_fraction': bounds(lambda g: g['overall']['new']['fraction_known_outcomes']),
            'overall_new_minus_old_pp': bounds(lambda g: g['overall']['new_minus_old_pp_known_outcomes']),
            'busy_new_minus_old_pp': bounds(lambda g: g['by_crowd_block']['busy']['new_minus_old_pp_known_outcomes']),
            'week_2_new_minus_old_pp': bounds(lambda g: g['by_week']['2']['new_minus_old_pp_known_outcomes']),
            'week_2_busy_new_minus_old_pp': bounds(lambda g: g['by_week_and_crowd_block']['2']['busy']['new_minus_old_pp_known_outcomes']),
            'scenarios': scenarios},
    }
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(args.output), 'rows': len(rows), 'missing_rows': ['M09'],
                      'sensitivity_scenarios': len(scenarios)}, sort_keys=True))


if __name__ == '__main__':
    main()
