#!/usr/bin/env python3
"""Audit North Pier's fictional aggregate counts. Python standard library only.

Run from any directory: python3 /path/to/work/analysis.py
Use --output - for JSON on stdout without writing. Inputs are never modified.
Missing completion rows are excluded only from explicitly labelled observed-row
fractions. Full-cohort results enumerate every feasible integer completion count.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ARM = Path(__file__).resolve().parents[1]


def wilson(completed, visitors):
    z = 1.96
    p = completed / visitors
    denominator = 1 + z * z / visitors
    center = (p + z * z / (2 * visitors)) / denominator
    half = z * math.sqrt(p * (1 - p) / visitors + z * z / (4 * visitors**2)) / denominator
    return {"lower": center - half, "upper": center + half, "z": z}


def load_rows(path):
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        assert reader.fieldnames == ["row_id", "week", "crowd_block", "sign", "visitors", "completed"]
        rows = []
        for raw in reader:
            row = dict(raw, week=int(raw["week"]), visitors=int(raw["visitors"]),
                       completed=None if raw["completed"] == "" else int(raw["completed"]))
            assert row["sign"] in ("old", "new") and row["crowd_block"] in ("quiet", "busy")
            assert row["visitors"] > 0
            assert row["completed"] is None or 0 <= row["completed"] <= row["visitors"]
            rows.append(row)
    assert len({r["row_id"] for r in rows}) == len(rows)
    missing = [r for r in rows if r["completed"] is None]
    assert len(missing) == 1 and missing[0]["row_id"] == "M09", "This bounded audit expects M09 as the sole missing row"
    return rows


def cohort(rows, scenario=None):
    result = {}
    for sign in ("old", "new"):
        selected = [r for r in rows if r["sign"] == sign]
        observed = [r for r in selected if r["completed"] is not None]
        included = selected if scenario is not None else observed
        n = sum(r["visitors"] for r in included)
        k = sum((scenario if r["completed"] is None else r["completed"]) for r in included)
        result[sign] = {"row_ids": [r["row_id"] for r in selected],
                        "included_row_ids": [r["row_id"] for r in included],
                        "missing_row_ids": [r["row_id"] for r in selected if r["completed"] is None],
                        "all_visitors": sum(r["visitors"] for r in selected),
                        "completed": k, "denominator": n, "fraction": k / n}
    result["difference_new_minus_old_pp"] = 100 * (result["new"]["fraction"] - result["old"]["fraction"])
    return result


def build_summary(input_dir):
    rows = load_rows(input_dir / "sessions.csv")
    groups = {"overall": rows}
    groups.update({f"crowd_{block}": [r for r in rows if r["crowd_block"] == block] for block in ("quiet", "busy")})
    groups.update({f"week_{week}": [r for r in rows if r["week"] == week] for week in (1, 2)})
    groups.update({f"week_{week}_{block}": [r for r in rows if r["week"] == week and r["crowd_block"] == block]
                   for week in (1, 2) for block in ("quiet", "busy")})
    observed = {name: cohort(group) for name, group in groups.items()}
    for sign in ("old", "new"):
        item = observed["overall"][sign]
        item["wilson_95"] = wilson(item["completed"], item["denominator"])
    missing = next(r for r in rows if r["completed"] is None)
    scenarios = []
    for k in range(missing["visitors"] + 1):
        comparisons = {name: cohort(group, k) for name, group in groups.items()}
        item = comparisons["overall"]["new"]
        item["wilson_95"] = wilson(item["completed"], item["denominator"])
        scenarios.append({"M09_completed": k, "comparisons": comparisons})
    bounds = {}
    for name in groups:
        values = [s["comparisons"][name] for s in scenarios]
        bounds[name] = {"new_fraction_min": min(v["new"]["fraction"] for v in values),
                        "new_fraction_max": max(v["new"]["fraction"] for v in values),
                        "new_denominator": values[0]["new"]["denominator"],
                        "old_fraction": values[0]["old"]["fraction"],
                        "old_denominator": values[0]["old"]["denominator"],
                        "difference_new_minus_old_pp_min": min(v["difference_new_minus_old_pp"] for v in values),
                        "difference_new_minus_old_pp_max": max(v["difference_new_minus_old_pp"] for v in values)}
    return {"schema_version": 1,
            "source_sha256": {name: hashlib.sha256((input_dir / name).read_bytes()).hexdigest() for name in ("sessions.csv", "notes.txt")},
            "method": {"difference": "100 * (new fraction - old fraction); signed percentage points, not relative percent",
                       "observed_rows": "Exclude the entire M09 row from numerator and denominator; no imputation. Old includes all 410 visitors; new includes 380 of 400.",
                       "sensitivity": "Evaluate every integer M09 completion count 0..20 at the known full-cohort denominators.",
                       "wilson": "95% descriptive binomial Wilson intervals, z=1.96, for observed-row overall sign fractions. Full-cohort new-sign intervals are conditional on each hypothetical M09 count. Neither accounts for confounding or session clustering and neither identifies a causal effect."},
            "audit": {"row_count": len(rows), "all_visitors": sum(r["visitors"] for r in rows),
                      "missing_rows": [missing], "observed_completed": sum(r["completed"] for r in rows if r["completed"] is not None),
                      "note_ids": ["N1", "N2", "N3", "N4", "N5"]},
            "observed_rows": observed,
            "missing_count_sensitivity": {"row_id": "M09", "feasible_counts": list(range(21)), "bounds": bounds,
                                          "overall_new_wilson_envelope": {
                                              "lower": min(s["comparisons"]["overall"]["new"]["wilson_95"]["lower"] for s in scenarios),
                                              "upper": max(s["comparisons"]["overall"]["new"]["wilson_95"]["upper"] for s in scenarios),
                                              "interpretation": "Envelope across 21 hypothetical intervals; not itself a 95% interval or causal confidence bound."},
                                          "scenarios": scenarios}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=ARM / "inputs")
    parser.add_argument("--output", default=str(Path(__file__).with_name("summary.json")))
    args = parser.parse_args()
    output = json.dumps(build_summary(args.input_dir), indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output == "-":
        print(output, end="")
    else:
        path = Path(args.output)
        assert path.resolve() not in [(args.input_dir / name).resolve() for name in ("sessions.csv", "notes.txt")], "Refusing to overwrite a raw input"
        path.write_text(output, encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
