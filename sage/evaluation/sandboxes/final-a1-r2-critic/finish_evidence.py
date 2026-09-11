#!/usr/bin/env python3
"""Carry forward the independently read requirement trace, with exact repair findings."""
import json
from pathlib import Path
import re
import runpy

HERE = Path(__file__).resolve().parent
audit = runpy.run_path(str(HERE / "audit.py"))
ROOT, sha, save = (audit[k] for k in ("ROOT", "sha", "save"))
prior = json.loads((ROOT / "sage/evaluation/sandboxes/final-a1-r1-critic/requirements-assessment.json").read_text())
repairs = {
    "R-012": "Promotion now reads run/state before planning and commits its own bounded task graph, authority/baselines, actual role handles and dependencies through landing.",
    "R-013": "Its separate events.jsonl is explicitly append-only own authority; shared state governs immutable task/plan/result corrections while source logs and generations remain separate.",
    "R-015": "Required shared delegation/recovery links supply temporal writer release; own unknown actor/effects retain the writer barrier before any further mutation.",
    "R-016": "Own graph records dependencies through landing and shared state/delegation govern dependency-ready admission, including after stale-state revision.",
    "R-021": "Promotion explicitly evaluates total delegation overhead including briefing, root context, review, integration, verification and retry cost.",
    "R-023": "Every own assignment records requested and effective model/effort separately, linked to the existing state contract's null/unknown observations.",
    "R-024": "Before dispatch or rerouting promotion reads installed delegation, whose fresh/bounded versus inherited-fork rules match the supplied callable schema; context fork is recorded per assignment.",
    "R-025": "Shared recovery requires actual handle inventory, active steering versus idle followup, latest effect/lifecycle reconciliation and no completion inferred from idle/missing/interruption.",
    "R-026": "Promotion requires the existing live-tool operating seam, actual role handles/results and evidence of independence; cached role priors do not override supplied callable schema or returned observations.",
    "R-030": "Each invocation selects a separate own coordinator run and explicitly establishes events.jsonl as authority. Shared state handles derived snapshot/report binding.",
    "R-031": "The own run records bounded plan, actual assignments/results, authority, source/proposal/pointer/generation baselines, checkpoints, unresolved items and next action, using the existing complete state vocabulary.",
    "R-033": "Mandatory run/state references supply compact classified protected-locator/hash evidence and exclusion of credentials, rather than copying private raw material into promotion history.",
    "R-034": "Promotion's own completion requires criterion observations, checks, finding disposition, reconciled effects/scope; shared state additionally rejects accepted major/blocker findings. Honest open/failed/stopped and human items remain explicit.",
    "R-035": "Promotion checkpoints plan commitment, delegation waves, proposal/refutation/review and before/after stage/activation. Shared run guidance includes host context warnings.",
    "R-036": "Own log validates before projection repair; corrupt authority pauses. Resume reconciles handles/effects and source/proposal/pointer/generation/authority baselines; unknown mutations are observed before any retry, stale next action revised and continuing authority checked.",
    "R-037": "Mandatory run/delegation/state procedures provide finite task and revision allowances plus recorded failure cause/material strategy changes; promotion additionally bounds corpus/candidates and attempts.",
    "R-038": "Shared cause-responsive replanning is reachable, and promotion requires stale-action revision with existing-authority confirmation. It asks for new authority only when scope/action requires it; no_change stays zero-team."
}
prior["scope"] = "Final-a1 round 2 assembled both-skills assessment. Unchanged areas reuse round-1 independent semantic review and original scoped evidence, with fresh 95-test/package/hash verification. Changed instruction coverage is independently rejudged below. No new live trial or universal empirical guarantee."
prior["prior_trace"] = "sage/evaluation/sandboxes/final-a1-r1-critic/requirements-assessment.json"
prior["basis"].update({
    "current-audit":"sage/evaluation/sandboxes/final-a1-r2-critic/summary.json",
    "current-graphs":"sage/evaluation/sandboxes/final-a1-r2-critic/instruction-graphs.json",
    "current-install":"sage/evaluation/sandboxes/final-a1-r2-critic/installed-audit.json",
    "current-boundary":"sage/evaluation/sandboxes/final-a1-r2-critic/independent-boundary-summary.json",
    "current-historical":"sage/evaluation/sandboxes/final-a1-r2-critic/historical-binding-check.json",
    "current-history":"sage/evaluation/sandboxes/final-a1-r2-critic/status-before.json"
})
for row in prior["rows"]:
    rid = row[0]
    if rid in repairs:
        row[1:] = ["verified_fixed_final_e1", repairs[rid], ["promotion", "current-graphs", "current-audit", "current-boundary"]]
    else:
        row[3].append("current-audit")
    if rid == "R-051":
        row[1:] = ["supported_with_limits", "The separate Sol/xhigh builder released a frozen candidate; the same independent whole_skill_critic actor rechecks it, without product authorship. Retained critic reuse is explicit and this is informed review, not a fresh blinded trial.", ["current-history", "current-audit", "history"]]
    if rid == "R-052":
        row[1:] = ["gate_enforced", "Eight genuine round-2 scores are independently assigned with evidence; every score is at least 8.5 and FINAL-A1-R1-E1 is verified fixed, leaving zero open errors. No aggregation hides a failed dimension.", ["rubric", "current-audit", "current-boundary"]]
    if rid == "R-056":
        row[1:] = ["supported_with_limits", "Fresh normal 95 tests pass; identical focused six-check copies reproduce only the old instruction-graph failure and pass current. One independent 13-command installed lost-acknowledgement/control scenario also passes; model judgment remains outside synthetic tests.", ["current-audit", "current-boundary", "offline-detail"]]
    if rid in {"R-058", "R-059", "R-060", "R-061"}:
        row[3].append("current-historical")
    if rid in {"R-002", "R-070", "R-073"}:
        row[3].append("current-install")
expected = set(re.findall(r"\*\*(R-\d{3})", (ROOT/"sage/docs/REQUIREMENTS.md").read_text()))
actual = {row[0] for row in prior["rows"]}
assert len(actual) == len(prior["rows"]) == 57 and expected == actual
assert all((ROOT/p).exists() for p in prior["basis"].values())
save("requirements-assessment.json", prior)
save("trace-validation.json", dict(requirements=57, assessed=57, missing=[], extra=[], updated_e1_requirements=len(repairs), prior_trace_preserved=True))
protected = json.loads((HERE/"protected-before.json").read_text())
changed = [p for p,h in protected.items() if sha(ROOT/p) != h]
save("final-preservation.json", dict(protected_files=len(protected), changed=changed, actual_status_unchanged=sha(ROOT/"sage/docs/STATUS.json")==protected["sage/docs/STATUS.json"]))
assert not changed
print(json.dumps(dict(requirements=57, updated_e1=len(repairs), protected_files=len(protected), changed=changed)))
