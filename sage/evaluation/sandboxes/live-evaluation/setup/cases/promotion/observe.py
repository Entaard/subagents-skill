"""Repeatable controlled observation, not a task solution or promotion decision."""
import csv
import json
from pathlib import Path
samples = json.loads(Path(__file__).with_name('samples.json').read_text())
print(json.dumps({kind: [{"line": line, "plain_split_fields": len(line.split(',')), "csv_reader_fields": len(next(csv.reader([line])))} for line in samples[kind]] for kind in ('old', 'new')}, indent=2))
