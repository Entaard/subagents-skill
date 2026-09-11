#!/usr/bin/env python3
"""Validate and project Sage run facts.

This helper proves only syntactic and recorded-state invariants.  It cannot prove
evidence quality, user authority, agent independence, or a physical writer lease.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
UTC = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$")
COMMON = {"v", "event_id", "run_id", "seq", "at", "actor", "type", "payload"}
KINDS = {
    "run.opened", "run.amended", "criteria.revised", "note.recorded", "user.decision", "plan.revised",
    "task.admitted", "agent.requested", "agent.not_created", "agent.observed", "task.result",
    "task.dispositioned",
    "evidence.recorded", "check.recorded", "finding.opened", "finding.dispositioned",
    "knowledge.selected", "knowledge.feedback", "checkpoint.written", "run.closed",
}
TASK_FIELDS = {
    "id", "revision", "objective", "completion", "dependencies", "owner", "effect",
    "scope", "inputs", "returns", "risk", "verification", "requested_model",
    "requested_effort", "fork_turns",
}
OPERATIONAL_TASK_FIELDS = TASK_FIELDS - {"id", "revision"}
TERMINAL_LIFECYCLES = {"completed", "failed"}
CAUSES = {"missing_input_or_authority", "ambiguous_brief", "decomposition", "capability", "environment_or_tool", "candidate_defect"}
CUE_KEYS = ("task", "domain", "artifact", "environment", "risk", "operation", "failure")


class ContractError(Exception):
    def __init__(self, code: str, message: str):
        self.code, self.message = code, message
        super().__init__(message)


def fail(condition: bool, code: str, message: str) -> None:
    if condition:
        raise ContractError(code, message)


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        fail(key in value, "invalid_json", f"duplicate object key: {key}")
        value[key] = item
    return value


def loads(text: str, source: str) -> Any:
    try:
        value = json.loads(text, object_pairs_hook=unique_object,
                           parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    except (json.JSONDecodeError, ValueError, ContractError) as exc:
        raise ContractError("invalid_json", f"invalid JSON in {source}: {exc}") from exc
    def finite(item: Any) -> None:
        if isinstance(item, float): fail(not math.isfinite(item), "invalid_json", f"non-finite number in {source}")
        elif isinstance(item, list):
            for child in item: finite(child)
        elif isinstance(item, dict):
            for child in item.values(): finite(child)
    finite(value)
    return value


def read_json(path: Path) -> Any:
    try: raw = path.read_bytes()
    except OSError as exc: raise ContractError("io_error", f"cannot read {path}: {exc}") from exc
    try: decoded = raw.decode("utf-8")
    except UnicodeDecodeError as exc: raise ContractError("invalid_json", f"JSON input is not UTF-8 in {path}: {exc}") from exc
    return loads(decoded, str(path))


def read_events(path: Path) -> tuple[list[dict[str, Any]], bytes]:
    try: raw = path.read_bytes()
    except OSError as exc: raise ContractError("io_error", f"cannot read {path}: {exc}") from exc
    try: text = raw.decode("utf-8")
    except UnicodeDecodeError as exc: raise ContractError("invalid_json", f"events log is not UTF-8: {exc}") from exc
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip(): continue
        item = loads(line, f"{path}:{number}")
        fail(not isinstance(item, dict), "invalid_json", f"event line {number} is not an object")
        rows.append(item)
    fail(not rows, "invalid_log", "events log is empty")
    return rows, raw


def need(payload: dict[str, Any], fields: set[str], where: str) -> None:
    missing = fields - payload.keys()
    fail(bool(missing), "invalid_event", f"{where} missing: {', '.join(sorted(missing))}")


def text(value: Any, where: str) -> str:
    fail(not isinstance(value, str) or not value.strip(), "invalid_event", f"{where} must be nonempty text")
    return value


def identifier(value: Any, where: str) -> str:
    fail(not isinstance(value, str) or ID.fullmatch(value) is None, "invalid_event", f"invalid {where}")
    return value


def native_handle(value: Any, where: str = "agent handle") -> str:
    fail(not isinstance(value, str) or not value or len(value) > 512 or any(ord(char) < 32 or ord(char) == 127 for char in value), "invalid_event", f"invalid {where}")
    return value


def strings(value: Any, where: str) -> list[str]:
    fail(not isinstance(value, list) or any(not isinstance(x, str) for x in value), "invalid_event", f"{where} must be a string array")
    return value


def positive(value: Any, where: str) -> int:
    fail(not isinstance(value, int) or isinstance(value, bool) or value < 1, "invalid_event", f"{where} must be a positive integer")
    return value


def choice(value: Any, choices: set[str], where: str) -> str:
    fail(not isinstance(value, str) or value not in choices, "invalid_event", f"invalid {where}")
    return value


def utc_timestamp(value: Any, where: str) -> str:
    fail(not isinstance(value, str) or UTC.fullmatch(value) is None, "invalid_event", f"invalid {where}")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ContractError("invalid_event", f"invalid {where}") from exc
    fail(parsed.utcoffset() != timezone.utc.utcoffset(parsed), "invalid_event", f"invalid {where}")
    return value


def check_task(item: Any, where: str) -> dict[str, Any]:
    fail(not isinstance(item, dict), "invalid_task", f"{where} must be an object")
    need(item, TASK_FIELDS, where)
    identifier(item["id"], f"{where}.id"); positive(item["revision"], f"{where}.revision")
    for key in ("objective", "completion", "owner", "risk", "verification", "requested_model", "requested_effort", "fork_turns"):
        text(item[key], f"{where}.{key}")
    choice(item["effect"], {"read", "write", "external", "unknown"}, f"effect in {where}")
    for key in ("dependencies", "scope", "inputs", "returns"): strings(item[key], f"{where}.{key}")
    fail(len(set(item["dependencies"])) != len(item["dependencies"]), "invalid_task", f"duplicate dependency in {where}")
    return item


def task_signature(item: dict[str, Any]) -> str:
    """Compare task work independently of its stable ID and revision."""
    return json.dumps({key: item[key] for key in sorted(OPERATIONAL_TASK_FIELDS)}, sort_keys=True, separators=(",", ":"))


def check_criterion(item: Any, where: str, *, replacement: bool = False) -> dict[str, Any]:
    fail(not isinstance(item, dict), "invalid_event", f"{where} must be an object")
    fields = {"id", "text"}
    if replacement: fields.add("supersedes")
    need(item, fields, where)
    identifier(item["id"], f"{where}.id"); text(item["text"], f"{where}.text")
    if replacement: identifier(item["supersedes"], f"{where}.supersedes")
    return item


def optional_cap(value: Any, where: str) -> int | None:
    if value is None: return None
    return positive(value, where)


def validate_payload(row: dict[str, Any]) -> None:
    p, kind = row["payload"], row["type"]
    fail(not isinstance(p, dict), "invalid_event", f"{row['event_id']} payload must be an object")
    required = {
        "run.opened": {"objective", "criteria", "constraints", "next_action"},
        "run.amended": {"kind", "value", "reason", "corrects_event_id"},
        "criteria.revised": {"revision", "authority_event_id", "reason", "added", "replaced", "retired"},
        "note.recorded": {"category", "text", "evidence_ids", "corrects_event_id"},
        "user.decision": {"request_id", "question", "decision", "received_at"},
        "plan.revised": {"revision", "reason", "attempt_limit", "revision_limit", "no_progress", "trigger_event_ids", "tasks"},
        "task.admitted": {"task_id", "task_revision", "plan_revision"},
        "agent.requested": {"task_id", "handle", "requested_model", "requested_effort", "fork_turns"},
        "agent.not_created": {"task_id", "task_revision", "reason", "evidence_ids"},
        "agent.observed": {"handle", "lifecycle", "effect_status", "effective_model", "effective_effort"},
        "task.result": {"task_id", "task_revision", "outcome", "effect_status", "evidence_ids"},
        "task.dispositioned": {"task_id", "task_revision", "disposition", "authority_event_id", "reason", "dependent_tasks"},
        "evidence.recorded": {"evidence_id", "criterion_ids", "kind", "locator", "sha256"},
        "check.recorded": {"check_id", "criterion_ids", "outcome", "evidence_ids"},
        "finding.opened": {"finding_id", "severity", "summary", "evidence_ids"},
        "finding.dispositioned": {"finding_id", "disposition", "evidence_ids", "verification_check_id"},
        "knowledge.selected": {"generation_id", "cue_fingerprint", "cues", "matches", "retrieval_status"},
        "knowledge.feedback": {"id", "revision", "outcome", "evidence_ids", "missed_recognizers"},
        "checkpoint.written": {"next_action", "baselines", "unresolved_user_items"},
        "run.closed": {"status", "criterion_evidence", "scope_reconciled", "remaining_human_items"},
    }[kind]
    need(p, required, row["event_id"])
    if kind == "run.opened":
        text(p["objective"], "objective"); text(p["next_action"], "next_action"); strings(p["constraints"], "constraints")
        fail(not isinstance(p["criteria"], list) or not p["criteria"], "invalid_event", "criteria must be a nonempty array")
        ids = []
        for criterion in p["criteria"]:
            check_criterion(criterion, "criterion"); ids.append(criterion["id"])
        fail(len(ids) != len(set(ids)), "duplicate_id", "duplicate criterion id")
    elif kind == "criteria.revised":
        positive(p["revision"], "criteria revision"); identifier(p["authority_event_id"], "criteria authority_event_id"); text(p["reason"], "criteria revision reason")
        fail(not isinstance(p["added"], list) or not isinstance(p["replaced"], list), "invalid_event", "criterion additions and replacements must be arrays")
        added = [check_criterion(item, f"added criterion[{index}]") for index, item in enumerate(p["added"])]
        replaced = [check_criterion(item, f"replacement criterion[{index}]", replacement=True) for index, item in enumerate(p["replaced"])]
        strings(p["retired"], "retired criteria")
        for criterion_id in p["retired"]: identifier(criterion_id, "retired criterion id")
        introduced = [item["id"] for item in added + replaced]
        fail(len(introduced) != len(set(introduced)), "duplicate_id", "criterion revision introduces a duplicate id")
        superseded = [item["supersedes"] for item in replaced]
        fail(len(superseded) != len(set(superseded)) or len(p["retired"]) != len(set(p["retired"])), "duplicate_id", "criterion revision repeats a current criterion")
        fail(not introduced and not p["retired"], "no_progress", "criterion revision must add, replace, or retire a criterion")
    elif kind == "plan.revised":
        positive(p["revision"], "plan revision"); positive(p["attempt_limit"], "attempt_limit"); positive(p["revision_limit"], "revision_limit")
        choice(p["reason"], {"initial", "failure", "user_amendment", "evidence_change", "approach_renewal"}, "plan reason")
        text(p["no_progress"], "no_progress"); strings(p["trigger_event_ids"], "trigger_event_ids")
        fail(not isinstance(p["tasks"], list), "invalid_event", "tasks must be an array")
        tasks = [check_task(x, f"task[{i}]") for i, x in enumerate(p["tasks"])]
        tids = [x["id"] for x in tasks]; fail(len(tids) != len(set(tids)), "duplicate_id", "duplicate task id in plan")
        for task in tasks:
            fail(any(x not in tids or x == task["id"] for x in task["dependencies"]), "invalid_dependency", f"invalid dependency for {task['id']}")
        if p["reason"] in {"failure", "approach_renewal"}:
            need(p, {"unmet_criterion", "failure_evidence_ids", "cause", "strategy_change"}, "failure plan")
            identifier(p["unmet_criterion"], "unmet criterion"); strings(p["failure_evidence_ids"], "failure_evidence_ids"); text(p["strategy_change"], "strategy_change")
            choice(p["cause"], CAUSES, "failure cause")
        if p["reason"] == "approach_renewal":
            need(p, {"authority_event_id", "total_attempt_limit"}, "approach renewal")
            identifier(p["authority_event_id"], "approach authority_event_id"); positive(p["total_attempt_limit"], "total_attempt_limit")
    elif kind in {"task.admitted", "task.result"}:
        identifier(p["task_id"], "task_id"); positive(p["task_revision"], "task_revision")
        if kind == "task.admitted": positive(p["plan_revision"], "plan_revision")
        else:
            choice(p["outcome"], {"passed", "failed", "unknown"}, "task outcome")
            choice(p["effect_status"], {"none", "reconciled", "unknown"}, "effect status"); strings(p["evidence_ids"], "evidence_ids")
    elif kind == "task.dispositioned":
        identifier(p["task_id"], "task_id"); positive(p["task_revision"], "task_revision")
        choice(p["disposition"], {"cancelled", "superseded"}, "task disposition")
        identifier(p["authority_event_id"], "task disposition authority_event_id"); text(p["reason"], "task disposition reason")
        fail(not isinstance(p["dependent_tasks"], list), "invalid_event", "dependent_tasks must be an array")
        dependent_ids = []
        for item in p["dependent_tasks"]:
            fail(not isinstance(item, dict), "invalid_event", "dependent task treatment must be an object")
            need(item, {"task_id", "treatment"}, "dependent task treatment")
            dependent_ids.append(identifier(item["task_id"], "dependent task id"))
            choice(item["treatment"], {"cancelled", "replanned"}, "dependent task treatment")
        fail(len(dependent_ids) != len(set(dependent_ids)), "duplicate_id", "dependent task treatment is duplicated")
    elif kind == "agent.requested":
        identifier(p["task_id"], "task_id"); native_handle(p["handle"])
        for key in ("requested_model", "requested_effort", "fork_turns"): text(p[key], key)
    elif kind == "agent.not_created":
        identifier(p["task_id"], "task_id"); positive(p["task_revision"], "task_revision")
        text(p["reason"], "reason"); strings(p["evidence_ids"], "evidence_ids")
    elif kind == "agent.observed":
        native_handle(p["handle"])
        choice(p["lifecycle"], {"active", "idle", "completed", "failed", "interrupted", "missing"}, "lifecycle")
        choice(p["effect_status"], {"none", "reconciled", "unknown"}, "effect status")
        for key in ("effective_model", "effective_effort"):
            fail(p[key] is not None and not isinstance(p[key], str), "invalid_event", f"{key} must be text or null")
    elif kind == "evidence.recorded":
        identifier(p["evidence_id"], "evidence_id"); strings(p["criterion_ids"], "criterion_ids"); text(p["locator"], "locator")
        choice(p["kind"], {"observation", "inference", "unknown", "untested"}, "evidence kind")
        fail(p["sha256"] is not None and (not isinstance(p["sha256"], str) or re.fullmatch(r"[0-9a-f]{64}", p["sha256"]) is None), "invalid_event", "invalid sha256")
    elif kind == "check.recorded":
        identifier(p["check_id"], "check_id"); strings(p["criterion_ids"], "criterion_ids"); strings(p["evidence_ids"], "evidence_ids")
        choice(p["outcome"], {"passed", "failed", "not_tested"}, "check outcome")
    elif kind == "finding.opened":
        identifier(p["finding_id"], "finding_id"); text(p["summary"], "summary"); strings(p["evidence_ids"], "evidence_ids")
        choice(p["severity"], {"blocker", "major", "minor"}, "finding severity")
    elif kind == "finding.dispositioned":
        identifier(p["finding_id"], "finding_id"); strings(p["evidence_ids"], "evidence_ids")
        choice(p["disposition"], {"fixed", "accepted", "rejected"}, "finding disposition")
        fail(p["verification_check_id"] is not None and not isinstance(p["verification_check_id"], str), "invalid_event", "invalid verification_check_id")
    elif kind == "run.amended":
        choice(p["kind"], {"objective", "constraint"}, "amendment kind"); text(p["value"], "value"); text(p["reason"], "reason")
    elif kind == "note.recorded":
        choice(p["category"], {"assumption", "decision"}, "note category"); text(p["text"], "text"); strings(p["evidence_ids"], "evidence_ids")
    elif kind == "user.decision":
        identifier(p["request_id"], "request_id"); text(p["question"], "question"); text(p["decision"], "decision"); utc_timestamp(p["received_at"], "received_at")
        if "hard_caps" in p:
            caps = p["hard_caps"]
            fail(not isinstance(caps, dict) or set(caps) != {"total_attempt_limit", "plan_revision_limit"}, "invalid_event", "hard_caps must contain total_attempt_limit and plan_revision_limit")
            values = [optional_cap(caps[key], f"hard_caps.{key}") for key in ("total_attempt_limit", "plan_revision_limit")]
            fail(all(value is None for value in values), "invalid_event", "hard_caps must set at least one finite limit")
    elif kind == "knowledge.selected":
        identifier(p["generation_id"], "generation_id"); text(p["cue_fingerprint"], "cue_fingerprint")
        fail(not isinstance(p["cues"], dict) or not isinstance(p["matches"], list), "invalid_event", "invalid knowledge selection")
        choice(p["retrieval_status"], {"matched", "no_match", "unchanged"}, "retrieval_status")
        fail(set(p["cues"]) - set(CUE_KEYS) - {"include_non_supported"}, "invalid_event", "unknown knowledge cue key")
        for key, values in p["cues"].items():
            if key == "include_non_supported":
                fail(type(values) is not bool, "invalid_event", "include_non_supported must be boolean")
            else:
                strings(values, f"cues.{key}")
                fail(any(not value.strip() for value in values), "invalid_event", "knowledge cues must be nonblank")
        fail(len(p["matches"]) > 100, "invalid_event", "knowledge selection exceeds retrieval limit")
        fail((p["retrieval_status"] == "matched") != bool(p["matches"]), "invalid_event", "retrieval status and matches disagree")
        fail(p["generation_id"] == "none" and bool(p["matches"]), "invalid_event", "empty generation cannot contain matches")
        fail(bool(p["matches"]) and not any(p["cues"].get(key, []) for key in CUE_KEYS), "invalid_event", "matches require an observed recognizer cue")
        ids = set()
        for match in p["matches"]:
            fail(not isinstance(match, dict), "invalid_event", "knowledge match must be object"); need(match, {"id", "revision", "status", "reason"}, "knowledge match")
            identifier(match["id"], "knowledge id"); positive(match["revision"], "knowledge revision"); text(match["reason"], "match reason")
            choice(match["status"], {"supported", "provisional", "contested"}, "knowledge match status")
            fail(match["status"] != "supported" and not p["cues"].get("include_non_supported", False), "invalid_event", "non-supported match requires explicit retrieval policy")
            fail(match["id"] in ids, "duplicate_id", "duplicate knowledge match ID")
            ids.add(match["id"])
    elif kind == "knowledge.feedback":
        identifier(p["id"], "knowledge id"); positive(p["revision"], "knowledge revision"); strings(p["evidence_ids"], "evidence_ids"); strings(p["missed_recognizers"], "missed_recognizers")
        choice(p["outcome"], {"useful", "neutral", "misleading", "not_exercised"}, "feedback outcome")
    elif kind == "checkpoint.written":
        text(p["next_action"], "next_action"); fail(not isinstance(p["baselines"], list), "invalid_event", "baselines must be array"); strings(p["unresolved_user_items"], "unresolved_user_items")
    elif kind == "run.closed":
        choice(p["status"], {"completed", "failed", "stopped"}, "run status")
        fail(not isinstance(p["criterion_evidence"], dict), "invalid_event", "criterion_evidence must be object"); strings(p["remaining_human_items"], "remaining_human_items")
        for criterion_id, evidence_ids in p["criterion_evidence"].items():
            identifier(criterion_id, "criterion_evidence key"); strings(evidence_ids, f"criterion_evidence.{criterion_id}")
        fail(not isinstance(p["scope_reconciled"], bool), "invalid_event", "scope_reconciled must be boolean")
    for key in ("corrects_event_id",):
        if key in p: fail(p[key] is not None and not isinstance(p[key], str), "invalid_event", f"{key} must be id or null")


def validate(rows: list[dict[str, Any]], terminal: bool = False) -> dict[str, Any]:
    event_ids: set[str] = set(); run_id = None; closed = False
    criteria: set[str] = set(); known_criteria: set[str] = set(); criteria_revision = 0
    evidence: dict[str, dict[str, Any]] = {}; checks: dict[str, dict[str, Any]] = {}
    plans: dict[int, dict[str, Any]] = {}; current_tasks: dict[str, dict[str, Any]] = {}
    task_history: dict[tuple[str, int], dict[str, Any]] = {}; admitted: dict[tuple[str, int], dict[str, Any]] = {}
    results: dict[tuple[str, int], dict[str, Any]] = {}; requests: dict[tuple[str, int], str] = {}; not_created: dict[tuple[str, int], dict[str, Any]] = {}; observations: dict[tuple[str, int], dict[str, Any]] = {}; current_assignment: dict[str, tuple[str, int]] = {}; released_tasks: set[tuple[str, int]] = set(); released_assignments: set[tuple[str, int]] = set()
    task_dispositions: dict[tuple[str, int], dict[str, Any]] = {}; pending_dispositions: set[tuple[str, int]] = set()
    findings: dict[str, dict[str, Any]] = {}; dispositioned: dict[str, dict[str, Any]] = {}
    amendments: set[str] = set(); decisions: set[str] = set(); decision_events: set[str] = set(); authority_events: set[str] = set()
    hard_caps: dict[str, int | None] = {"total_attempt_limit": None, "plan_revision_limit": None}
    approach_total_attempt_limit: int | None = None; approach_revision_limit: int | None = None
    prior_selection = None
    for index, row in enumerate(rows, 1):
        fail(not isinstance(row, dict), "invalid_event", f"event {index} must be an object")
        fail(set(row) != COMMON, "invalid_event", f"event {index} common fields must be exactly {sorted(COMMON)}")
        fail(type(row["v"]) is not int or row["v"] != 1, "invalid_event", f"event {index} has unsupported version")
        identifier(row["event_id"], "event_id"); identifier(row["run_id"], "run_id"); text(row["actor"], "actor")
        fail(type(row["seq"]) is not int or row["seq"] != index, "invalid_sequence", f"event {row['event_id']} sequence must be {index}")
        utc_timestamp(row["at"], f"timestamp in {row['event_id']}")
        choice(row["type"], KINDS, "event type")
        fail(row["event_id"] in event_ids, "duplicate_id", f"duplicate event id: {row['event_id']}")
        fail(run_id is not None and row["run_id"] != run_id, "invalid_log", "mixed run ids")
        fail(closed, "invalid_transition", "events cannot follow run.closed")
        run_id = row["run_id"]; validate_payload(row); p, kind = row["payload"], row["type"]
        fail(index == 1 and kind != "run.opened", "invalid_transition", "first event must be run.opened")
        fail(index > 1 and kind == "run.opened", "invalid_transition", "run.opened may occur only once")
        correction = p.get("corrects_event_id")
        fail(correction is not None and correction not in event_ids, "invalid_reference", "correction must reference an earlier event")
        if kind == "run.opened":
            criteria = {x["id"] for x in p["criteria"]}; known_criteria = set(criteria); criteria_revision = 1
        elif kind == "run.amended":
            amendments.add(row["event_id"]); authority_events.add(row["event_id"])
        elif kind == "criteria.revised":
            fail(p["revision"] != criteria_revision + 1, "invalid_revision", "criteria revisions must be contiguous")
            fail(p["authority_event_id"] not in authority_events, "invalid_reference", "criteria revision needs an earlier decision or amendment authority")
            introduced = {item["id"] for item in p["added"] + p["replaced"]}
            fail(bool(introduced & known_criteria), "immutable_history", "criterion ids cannot be reused")
            superseded = {item["supersedes"] for item in p["replaced"]}
            retired = set(p["retired"])
            fail(not superseded <= criteria or not retired <= criteria, "invalid_reference", "only current criteria may be replaced or retired")
            fail(bool(superseded & retired), "invalid_event", "a criterion cannot be both replaced and retired")
            criteria = (criteria - superseded - retired) | introduced
            fail(not criteria, "invalid_event", "the current acceptance contract cannot be empty")
            known_criteria.update(introduced); criteria_revision = p["revision"]
            authority_events.add(row["event_id"]); amendments.add(row["event_id"])
        elif kind == "user.decision":
            fail(p["request_id"] in decisions, "duplicate_id", "duplicate user decision request_id")
            decisions.add(p["request_id"]); decision_events.add(row["event_id"]); authority_events.add(row["event_id"])
            if "hard_caps" in p:
                for cap_name in hard_caps:
                    proposed = p["hard_caps"][cap_name]
                    if proposed is None: continue
                    used = len(admitted) if cap_name == "total_attempt_limit" else len(plans)
                    fail(proposed < used, "limit_exceeded", f"{cap_name} is already exceeded by recorded history")
                    current_cap = hard_caps[cap_name]
                    fail(current_cap is not None and proposed > current_cap, "limit_exceeded", f"user hard cap {cap_name} cannot be relaxed")
                    hard_caps[cap_name] = proposed
        elif kind == "plan.revised":
            revision = p["revision"]; fail(revision != len(plans) + 1, "invalid_revision", "plan revisions must be contiguous")
            hard_revision_cap = hard_caps["plan_revision_limit"]
            fail(hard_revision_cap is not None and revision > hard_revision_cap, "limit_exceeded", "plan revision exceeds the user hard cap")
            fail(hard_revision_cap is not None and p["revision_limit"] > hard_revision_cap, "limit_exceeded", "plan allowance exceeds the user hard cap")
            triggers = p["trigger_event_ids"]
            fail(any(x not in event_ids for x in triggers), "invalid_reference", "plan trigger must reference an earlier event")
            if revision == 1:
                fail(p["reason"] != "initial", "invalid_revision", "first plan reason must be initial")
                fail(p["revision_limit"] < 1, "limit_exceeded", "initial plan has an exhausted revision limit")
                fail(hard_revision_cap is not None and p["revision_limit"] > hard_revision_cap, "limit_exceeded", "plan allowance exceeds the user hard cap")
            else:
                fail(p["reason"] == "initial", "invalid_revision", "only the first plan may use reason initial")
                prior = plans[revision - 1]["payload"]
                over_prior_limit = revision > prior["revision_limit"]
                fail(over_prior_limit and p["reason"] != "approach_renewal", "limit_exceeded", "plan revision exceeds the previously committed limit")
                fail(not over_prior_limit and p["reason"] == "approach_renewal", "invalid_transition", "approach renewal requires an exhausted plan revision allowance")
                if approach_revision_limit is not None and p["reason"] != "approach_renewal":
                    fail(p["revision_limit"] > approach_revision_limit, "limit_exceeded", "an active approach revision allowance cannot be expanded without renewal")
                old = {x["id"]: x for x in prior["tasks"]}; new = {x["id"]: x for x in p["tasks"]}
                dropped = set(old) - set(new)
                pending_current = {key for key in pending_dispositions if key[0] in old and old[key[0]]["revision"] == key[1]}
                fail(any((task_id, old[task_id]["revision"]) not in pending_dispositions for task_id in dropped), "immutable_history", "a dropped task needs an authorized disposition")
                fail(any(key[0] not in dropped for key in pending_current), "invalid_transition", "a task disposition must be consumed by the next plan")
                for task_id in dropped:
                    disposition = task_dispositions[(task_id, old[task_id]["revision"])]
                    treatments = {item["task_id"]: item["treatment"] for item in disposition["dependent_tasks"]}
                    dependents = {item_id for item_id, item in old.items() if task_id in item["dependencies"]}
                    fail(set(treatments) != dependents, "invalid_dependency", f"task {task_id} must explicitly treat every dependent edge")
                    for dependent_id, treatment in treatments.items():
                        if treatment == "cancelled":
                            dep_key = (dependent_id, old[dependent_id]["revision"])
                            fail(dependent_id not in dropped or dep_key not in pending_dispositions, "invalid_dependency", f"cancelled dependent {dependent_id} needs its own disposition")
                        else:
                            fail(dependent_id not in new or task_id in new[dependent_id]["dependencies"], "invalid_dependency", f"replanned dependent {dependent_id} must remove the obsolete edge")
                changed = bool(dropped) or p["attempt_limit"] != prior["attempt_limit"] or p["revision_limit"] != prior["revision_limit"] or p["no_progress"] != prior["no_progress"]
                old_signatures = {task_signature(item) for item in old.values()}
                new_signatures = {task_signature(item) for item in new.values()}
                operational_changed = any(signature not in new_signatures for signature in old_signatures)
                operational_changed = operational_changed or any(signature not in old_signatures for signature in new_signatures)
                for task_id, task_value in new.items():
                    if task_id in old:
                        before = old[task_id]
                        same_ops = all(task_value[k] == before[k] for k in OPERATIONAL_TASK_FIELDS)
                        if same_ops:
                            fail(task_value["revision"] != before["revision"], "immutable_history", f"unchanged task {task_id} must retain revision")
                        else:
                            was_admitted = (task_id, before["revision"]) in admitted
                            expected = before["revision"] + 1 if was_admitted else before["revision"]
                            fail(task_value["revision"] != expected, "immutable_history", f"changed task {task_id} has invalid revision")
                            changed = True; operational_changed = True
                    else:
                        fail(any(key[0] == task_id for key in task_history), "immutable_history", f"historically dropped task id {task_id} cannot be reintroduced")
                        fail(task_value["revision"] != 1, "immutable_history", f"new task {task_id} must start at revision 1")
                        changed = True
                fail(not changed, "no_progress", "later plan has no operational change")
                if p["reason"] == "failure":
                    fail(p["unmet_criterion"] not in criteria, "invalid_reference", "unknown unmet criterion")
                    fail(not p["failure_evidence_ids"] or any(x not in evidence for x in p["failure_evidence_ids"]), "invalid_reference", "failure evidence must already exist")
                elif p["reason"] == "approach_renewal":
                    fail(p["authority_event_id"] not in decision_events, "invalid_reference", "approach renewal needs an earlier user decision authority")
                    fail(p["authority_event_id"] not in triggers, "invalid_reference", "approach renewal authority must also be a plan trigger")
                    fail(p["unmet_criterion"] not in criteria, "invalid_reference", "unknown unmet criterion")
                    failure_ids = set(p["failure_evidence_ids"])
                    fail(not failure_ids or any(item not in evidence or evidence[item]["kind"] != "observation" for item in failure_ids), "invalid_reference", "approach renewal needs recorded observation evidence")
                    fail(not any(result["outcome"] == "failed" and failure_ids & set(result["evidence_ids"]) for result in results.values()), "invalid_reference", "approach renewal evidence must come from a failed task result")
                    fail(not operational_changed, "no_progress", "approach renewal needs an operational task or graph change")
                    fail(p["revision_limit"] < revision, "limit_exceeded", "renewed revision allowance is already exhausted")
                    fail(p["total_attempt_limit"] <= len(admitted), "limit_exceeded", "renewed total attempt allowance must leave a finite next attempt")
                    hard_attempt_cap = hard_caps["total_attempt_limit"]
                    fail(hard_attempt_cap is not None and p["total_attempt_limit"] > hard_attempt_cap, "limit_exceeded", "renewed total attempt allowance exceeds the user hard cap")
                    fail(hard_revision_cap is not None and p["revision_limit"] > hard_revision_cap, "limit_exceeded", "renewed revision allowance exceeds the user hard cap")
                    approach_total_attempt_limit = p["total_attempt_limit"]; approach_revision_limit = p["revision_limit"]
                elif p["reason"] == "user_amendment": fail(not triggers or not any(x in amendments or next((r["payload"]["request_id"] for r in rows[:index-1] if r["event_id"] == x and r["type"] == "user.decision"), None) in decisions for x in triggers), "invalid_reference", "user amendment needs an amendment/decision trigger")
                elif p["reason"] == "evidence_change": fail(not any(next((r["type"] for r in rows[:index-1] if r["event_id"] == x), "") in {"evidence.recorded", "check.recorded", "finding.opened", "finding.dispositioned", "user.decision"} for x in triggers), "invalid_reference", "evidence change needs new evidence or decision")
                pending_dispositions.difference_update(pending_current)
            plans[revision] = row; current_tasks = {x["id"]: x for x in p["tasks"]}
            for task_value in p["tasks"]:
                task_history[(task_value["id"], task_value["revision"])] = copy.deepcopy(task_value)
        elif kind == "task.admitted":
            key = (p["task_id"], p["task_revision"]); fail(p["plan_revision"] not in plans, "invalid_reference", "unknown plan revision")
            fail(p["plan_revision"] != len(plans), "stale_revision", "task admission must use the current plan revision")
            plan_tasks = {x["id"]: x for x in plans[p["plan_revision"]]["payload"]["tasks"]}
            fail(p["task_id"] not in plan_tasks or plan_tasks[p["task_id"]]["revision"] != p["task_revision"], "invalid_reference", "task not in named plan revision")
            fail(key in admitted, "invalid_transition", "task revision already admitted")
            fail(key in task_dispositions, "invalid_transition", "a dispositioned task revision cannot be admitted")
            attempts = sum(1 for prior in admitted if prior[0] == p["task_id"])
            fail(attempts >= plans[p["plan_revision"]]["payload"]["attempt_limit"], "limit_exceeded", f"task {p['task_id']} exceeds its attempt limit")
            total_cap = approach_total_attempt_limit
            if hard_caps["total_attempt_limit"] is not None:
                total_cap = min(total_cap, hard_caps["total_attempt_limit"]) if total_cap is not None else hard_caps["total_attempt_limit"]
            fail(total_cap is not None and len(admitted) >= total_cap, "limit_exceeded", "run exceeds its cumulative total attempt limit")
            task_value = plan_tasks[p["task_id"]]
            for dep in task_value["dependencies"]:
                dep_task = plan_tasks[dep]; dep_key = (dep, dep_task["revision"]); dep_result = results.get(dep_key)
                fail(not dep_result or dep_result["outcome"] != "passed" or dep_key not in released_tasks, "dependency_blocked", f"dependency {dep} has not passed and released")
            if task_value["effect"] in {"write", "external", "unknown"}:
                for active_key, admission in admitted.items():
                    active_task = task_history[active_key]
                    if active_task["effect"] in {"write", "external", "unknown"} and active_key not in released_tasks:
                        raise ContractError("writer_busy", f"effect barrier held by {active_key[0]}")
            admitted[key] = row
        elif kind == "agent.requested":
            candidates = [key for key in admitted if key[0] == p["task_id"] and key not in results]
            fail(len(candidates) != 1, "invalid_transition", "agent request needs one admitted task")
            key = candidates[0]; task_value = task_history[key]
            fail(task_value["owner"] == "root", "invalid_transition", "root-owned task cannot request an agent")
            fail(key in not_created, "invalid_transition", "known uncreated assignment cannot request an agent")
            fail(key in requests, "invalid_transition", "task revision already has an assigned agent")
            fail(p["handle"] != task_value["owner"], "invalid_event", "agent handle must match the task owner")
            prior_key = current_assignment.get(p["handle"])
            if prior_key is not None:
                prior_observation = observations.get(prior_key, {})
                fail(prior_key not in released_assignments or prior_observation.get("lifecycle") not in TERMINAL_LIFECYCLES or prior_observation.get("effect_status") != "reconciled", "invalid_transition", "agent handle is still bound to an unreleased assignment")
            fail(any(p[k] != task_value[k] for k in ("requested_model", "requested_effort", "fork_turns")), "invalid_event", "request differs from task routing")
            requests[key] = p["handle"]; current_assignment[p["handle"]] = key
        elif kind == "agent.not_created":
            key = (p["task_id"], p["task_revision"])
            fail(key not in admitted, "invalid_transition", "no-creation fact needs an admitted task")
            fail(task_history[key]["owner"] == "root", "invalid_transition", "root-owned task has no delegated creation")
            fail(key in requests, "invalid_transition", "requested assignment cannot be marked uncreated")
            fail(key in not_created or key in results, "invalid_transition", "assignment creation outcome is final")
            fail(not p["evidence_ids"] or any(x not in evidence or evidence[x]["kind"] != "observation" for x in p["evidence_ids"]), "invalid_reference", "no-creation fact needs recorded observation evidence")
            not_created[key] = p
        elif kind == "agent.observed":
            fail(p["handle"] not in current_assignment, "invalid_reference", "observation for unknown handle")
            if p["lifecycle"] in {"idle", "interrupted", "missing"}: fail(p["effect_status"] != "unknown", "unknown_effect", "nonterminal/unknown observation must preserve unknown effect")
            assignment = current_assignment[p["handle"]]
            record_observation(assignment, p, task_history, results, requests, not_created, observations, released_tasks, released_assignments)
        elif kind == "evidence.recorded":
            fail(p["evidence_id"] in evidence, "duplicate_id", "duplicate evidence id"); fail(any(x not in known_criteria for x in p["criterion_ids"]), "invalid_reference", "unknown criterion in evidence")
            evidence[p["evidence_id"]] = p
        elif kind == "check.recorded":
            fail(p["check_id"] in checks, "duplicate_id", "duplicate check id"); fail(any(x not in known_criteria for x in p["criterion_ids"]), "invalid_reference", "unknown criterion in check")
            fail(any(x not in evidence for x in p["evidence_ids"]), "invalid_reference", "check references missing evidence"); checks[p["check_id"]] = p
        elif kind == "task.result":
            key = (p["task_id"], p["task_revision"]); fail(key not in admitted, "invalid_transition", "result needs an admitted task")
            prior_result = results.get(key)
            if prior_result:
                fail(prior_result["outcome"] != "unknown" or p["outcome"] == "unknown" or p["effect_status"] == "unknown", "invalid_transition", "only one unknown result may be reconciled to a known result")
            fail(any(x not in evidence for x in p["evidence_ids"]), "invalid_reference", "result references missing evidence")
            if p["outcome"] == "passed": fail(not p["evidence_ids"], "invalid_transition", "passed result needs evidence")
            if prior_result: fail(not p["evidence_ids"], "invalid_transition", "result reconciliation needs evidence")
            fail(p["effect_status"] == "unknown" and p["outcome"] != "unknown", "unknown_effect", "known outcome cannot have unknown effect status")
            task_value = task_history[key]
            if task_value["owner"] != "root":
                fail(key not in requests and key not in not_created, "invalid_transition", "delegated result needs a recorded agent request or no-creation fact")
                if key in not_created:
                    fail(p["outcome"] != "failed" or p["effect_status"] != "none", "invalid_transition", "uncreated assignment accepts only a failed no-effect result")
                    fail(not set(p["evidence_ids"]) & set(not_created[key]["evidence_ids"]), "invalid_reference", "uncreated assignment result must cite its no-creation evidence")
            if task_value["effect"] == "read" and p["outcome"] != "unknown": fail(p["effect_status"] != "none", "invalid_transition", "known read result effect must be none")
            if p["outcome"] == "unknown": fail(p["effect_status"] != "unknown", "unknown_effect", "unknown result must preserve unknown effect")
            if task_value["effect"] in {"write", "external", "unknown"} and p["outcome"] != "unknown" and key not in not_created: fail(p["effect_status"] != "reconciled", "unknown_effect", "known effectful result must be reconciled")
            results[key] = p
            mark_release(key, task_history, results, requests, not_created, observations, released_tasks, released_assignments)
        elif kind == "task.dispositioned":
            key = (p["task_id"], p["task_revision"])
            fail(p["task_id"] not in current_tasks or current_tasks[p["task_id"]]["revision"] != p["task_revision"], "invalid_reference", "task disposition must name a current task revision")
            fail(key in task_dispositions, "invalid_transition", "task revision already has a disposition")
            fail(p["authority_event_id"] not in authority_events, "invalid_reference", "task disposition needs an earlier criteria, decision, or amendment authority")
            fail(key in admitted and key not in released_tasks, "unknown_effect", "an admitted task must reconcile its result and effects before disposition")
            dependents = {task_id for task_id, task_value in current_tasks.items() if p["task_id"] in task_value["dependencies"]}
            recorded_dependents = {item["task_id"] for item in p["dependent_tasks"]}
            fail(recorded_dependents != dependents, "invalid_dependency", "task disposition must enumerate every current dependent")
            task_dispositions[key] = p; pending_dispositions.add(key)
        elif kind == "finding.opened":
            fail(p["finding_id"] in findings, "duplicate_id", "duplicate finding id"); fail(any(x not in evidence for x in p["evidence_ids"]), "invalid_reference", "finding references missing evidence"); findings[p["finding_id"]] = p
        elif kind == "finding.dispositioned":
            fail(p["finding_id"] not in findings or p["finding_id"] in dispositioned, "invalid_transition", "finding must be open")
            fail(any(x not in evidence for x in p["evidence_ids"]), "invalid_reference", "disposition references missing evidence")
            if p["disposition"] == "fixed": fail(p["verification_check_id"] not in checks or checks[p["verification_check_id"]]["outcome"] != "passed", "invalid_reference", "fixed finding needs a passed verification check")
            if p["disposition"] == "rejected": fail(not p["evidence_ids"], "invalid_transition", "rejected finding needs evidence")
            dispositioned[p["finding_id"]] = p
        elif kind == "note.recorded":
            fail(any(x not in evidence for x in p.get("evidence_ids", [])), "invalid_reference", "note references missing evidence")
            if p["category"] == "decision": authority_events.add(row["event_id"])
        elif kind == "knowledge.selected":
            if p["retrieval_status"] == "unchanged":
                fail(prior_selection is None or any(p[field] != prior_selection[field] for field in ("generation_id", "cue_fingerprint", "cues")), "invalid_reference", "unchanged retrieval requires the same prior generation, fingerprint and cues")
            prior_selection = p
        elif kind == "knowledge.feedback": fail(any(x not in evidence for x in p["evidence_ids"]), "invalid_reference", "feedback references missing evidence")
        elif kind == "run.closed":
            fail(any(x not in criteria for x in p["criterion_evidence"]), "invalid_reference", "closure references an unknown criterion")
            fail(any(x not in evidence for refs in p["criterion_evidence"].values() for x in refs), "invalid_reference", "closure references missing evidence")
            fail(bool(pending_dispositions), "invalid_transition", "task dispositions must be reconciled by a later plan before closure")
            closed = True
        event_ids.add(row["event_id"])
    state = project(rows)
    if terminal:
        fail(not closed, "incomplete_run", "terminal validation requires run.closed")
    if closed:
        close = rows[-1]["payload"]; fail(any(key not in released_tasks for key in admitted), "unknown_effect", "a task or effect is unresolved")
        if close["status"] == "completed":
            fail(any((task_id, task["revision"]) not in results for task_id, task in current_tasks.items()), "incomplete_run", "every task in a completed plan must have a result")
            fail(any(results[(task_id, task["revision"])]["outcome"] != "passed" for task_id, task in current_tasks.items()), "incomplete_run", "every task in a completed plan must pass")
            fail(not close["scope_reconciled"], "incomplete_run", "completed run must reconcile scope")
            for criterion in criteria:
                refs = close["criterion_evidence"].get(criterion, [])
                fail(not refs or any(x not in evidence or evidence[x]["kind"] != "observation" or criterion not in evidence[x]["criterion_ids"] for x in refs), "incomplete_run", f"criterion {criterion} lacks associated observation evidence")
                fail(not any(check["outcome"] == "passed" and criterion in check["criterion_ids"] and check["evidence_ids"] for check in checks.values()), "incomplete_run", f"criterion {criterion} lacks an evidence-bearing passed check")
            for finding_id, finding in findings.items():
                disp = dispositioned.get(finding_id); fail(disp is None, "open_finding", f"finding {finding_id} remains open")
                fail(finding["severity"] in {"blocker", "major"} and disp["disposition"] == "accepted", "open_finding", f"material finding {finding_id} is accepted")
    return state


def released(key: tuple[str, int], task: dict[str, Any], results: dict, requests: dict,
             not_created: dict, observations: dict) -> bool:
    result = results.get(key)
    if not result or result["outcome"] == "unknown" or result["effect_status"] == "unknown": return False
    if key in not_created: return result["outcome"] == "failed" and result["effect_status"] == "none"
    if task["effect"] == "read": return True
    if result["effect_status"] != "reconciled": return False
    if task["owner"] == "root": return True
    handle = requests.get(key); observation = observations.get(key, {})
    return bool(handle) and observation.get("lifecycle") in TERMINAL_LIFECYCLES and observation.get("effect_status") == "reconciled"


def mark_release(key: tuple[str, int], tasks: dict, results: dict, requests: dict, not_created: dict,
                 observations: dict, released_tasks: set[tuple[str, int]],
                 released_assignments: set[tuple[str, int]]) -> None:
    """Persist task-effect and native-assignment release boundaries."""
    task = tasks.get(key)
    if task is not None and key not in released_tasks and released(key, task, results, requests, not_created, observations):
        released_tasks.add(key)
    observation = observations.get(key, {})
    if (key in released_tasks and key in requests and
            observation.get("lifecycle") in TERMINAL_LIFECYCLES and observation.get("effect_status") == "reconciled"):
        released_assignments.add(key)


def record_observation(key: tuple[str, int], observation: dict[str, Any], tasks: dict,
                       results: dict, requests: dict, not_created: dict, observations: dict,
                       released_tasks: set[tuple[str, int]],
                       released_assignments: set[tuple[str, int]]) -> None:
    """Keep the latest provisional observation; freeze it only at release."""
    if key not in released_assignments:
        observations[key] = observation
        mark_release(key, tasks, results, requests, not_created, observations, released_tasks, released_assignments)


def execution_facts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Replay revision-specific execution facts after structural validation."""
    tasks: dict[tuple[str, int], dict[str, Any]] = {}
    current: dict[str, dict[str, Any]] = {}
    admitted: set[tuple[str, int]] = set()
    results: dict[tuple[str, int], dict[str, Any]] = {}
    requests: dict[tuple[str, int], str] = {}
    not_created: dict[tuple[str, int], dict[str, Any]] = {}
    observations: dict[tuple[str, int], dict[str, Any]] = {}
    current_assignment: dict[str, tuple[str, int]] = {}
    released_tasks: set[tuple[str, int]] = set()
    released_assignments: set[tuple[str, int]] = set()
    for row in rows:
        p, kind = row["payload"], row["type"]
        if kind == "plan.revised":
            current = {task["id"]: task for task in p["tasks"]}
            tasks.update({(task["id"], task["revision"]): task for task in p["tasks"]})
        elif kind == "task.admitted": admitted.add((p["task_id"], p["task_revision"]))
        elif kind == "agent.requested":
            candidates = [key for key in admitted if key[0] == p["task_id"] and key not in results]
            if len(candidates) == 1:
                requests[candidates[0]] = p["handle"]
                current_assignment[p["handle"]] = candidates[0]
        elif kind == "agent.not_created":
            not_created[(p["task_id"], p["task_revision"])] = p
        elif kind == "agent.observed":
            assignment = current_assignment.get(p["handle"])
            if assignment is not None:
                record_observation(assignment, p, tasks, results, requests, not_created, observations, released_tasks, released_assignments)
        elif kind == "task.result":
            key = (p["task_id"], p["task_revision"]); results[key] = p
            mark_release(key, tasks, results, requests, not_created, observations, released_tasks, released_assignments)
    return {"tasks": tasks, "current": current, "admitted": admitted, "results": results,
            "requests": requests, "not_created": not_created, "observations": observations, "released": released_tasks,
            "released_assignments": released_assignments, "current_assignment": current_assignment}


def project(rows: list[dict[str, Any]]) -> dict[str, Any]:
    opened = rows[0]["payload"]; objective = opened["objective"]; constraints = list(opened["constraints"]); next_action = opened["next_action"]
    state: dict[str, Any] = {"v": 1, "run_id": rows[0]["run_id"], "last_seq": rows[-1]["seq"], "terminal": None,
        "objective": objective, "constraints": constraints, "criteria": copy.deepcopy(opened["criteria"]),
        "criteria_history": [{"revision": 1, "event_id": rows[0]["event_id"], "authority_event_id": None,
                              "reason": "run opened", "added": copy.deepcopy(opened["criteria"]), "replaced": [],
                              "retired": [], "criteria": copy.deepcopy(opened["criteria"])}],
        "current_plan_revision": None, "current_approach": None, "approach_history": [], "plan_history": [],
        "task_history": [], "task_results": [], "task_dispositions": [], "attempt_history": [],
        "tasks": {}, "agents": {}, "findings": {}, "evidence": {}, "checks": {}, "assumptions": [], "decisions": [],
        "user_decisions": [], "hard_caps": {"total_attempt_limit": None, "plan_revision_limit": None},
        "knowledge_selection": None, "knowledge_selected_revisions": [], "knowledge_feedback": [], "baselines": [],
        "next_action": next_action, "unresolved_user_items": []}
    selected_revisions: set[tuple[str, int, str]] = set()
    for row in rows:
        p, kind = row["payload"], row["type"]
        if kind == "run.amended":
            if p["kind"] == "objective": state["objective"] = p["value"]
            else: state["constraints"].append(p["value"])
        elif kind == "criteria.revised":
            replacements = {item["supersedes"]: {"id": item["id"], "text": item["text"]} for item in p["replaced"]}
            retired = set(p["retired"]); current = []
            for criterion in state["criteria"]:
                if criterion["id"] in replacements: current.append(replacements[criterion["id"]])
                elif criterion["id"] not in retired: current.append(copy.deepcopy(criterion))
            current.extend(copy.deepcopy(p["added"])); state["criteria"] = current
            state["criteria_history"].append({**copy.deepcopy(p), "event_id": row["event_id"], "criteria": copy.deepcopy(current)})
        elif kind == "note.recorded": state[p["category"] + "s"].append({**p, "event_id": row["event_id"]})
        elif kind == "user.decision":
            state["user_decisions"].append({**p, "event_id": row["event_id"]})
            for cap_name, cap in p.get("hard_caps", {}).items():
                if cap is not None: state["hard_caps"][cap_name] = cap
        elif kind == "plan.revised":
            state["current_plan_revision"] = p["revision"]
            state["plan_history"].append({**copy.deepcopy(p), "event_id": row["event_id"]})
            state["task_history"].extend({**copy.deepcopy(task), "plan_revision": p["revision"]} for task in p["tasks"])
            if state["current_approach"] is None:
                state["current_approach"] = 1
                state["approach_history"].append({"approach": 1, "plan_revision": p["revision"],
                    "attempt_limit": p["attempt_limit"], "revision_limit": p["revision_limit"],
                    "total_attempt_limit": None, "reason": "initial", "event_id": row["event_id"]})
            elif p["reason"] == "approach_renewal":
                state["current_approach"] += 1
                state["approach_history"].append({"approach": state["current_approach"],
                    "plan_revision": p["revision"], "attempt_limit": p["attempt_limit"],
                    "revision_limit": p["revision_limit"], "total_attempt_limit": p["total_attempt_limit"],
                    "reason": p["reason"], "authority_event_id": p["authority_event_id"],
                    "failure_evidence_ids": copy.deepcopy(p["failure_evidence_ids"]), "cause": p["cause"],
                    "strategy_change": p["strategy_change"], "event_id": row["event_id"]})
            prior = state["tasks"]
            state["tasks"] = {}
            for task in p["tasks"]:
                old = prior.get(task["id"], {})
                carry = old if old.get("revision") == task["revision"] else {}
                state["tasks"][task["id"]] = {**copy.deepcopy(task), "state": carry.get("state", "planned")}
                if "result" in carry: state["tasks"][task["id"]]["result"] = carry["result"]
        elif kind == "task.admitted":
            state["attempt_history"].append({**copy.deepcopy(p), "event_id": row["event_id"]})
            if p["task_id"] in state["tasks"]: state["tasks"][p["task_id"]]["state"] = "admitted"
        elif kind == "task.result":
            state["task_results"].append({**copy.deepcopy(p), "event_id": row["event_id"]})
            current = state["tasks"].get(p["task_id"])
            if current and current.get("revision") == p["task_revision"]:
                current["state"] = p["outcome"]; current["result"] = p
        elif kind == "task.dispositioned": state["task_dispositions"].append({**copy.deepcopy(p), "event_id": row["event_id"]})
        elif kind == "agent.requested": state["agents"][p["handle"]] = {**p, "lifecycle": "unknown", "effect_status": "unknown", "effective_model": "unknown", "effective_effort": "unknown"}
        elif kind == "agent.observed":
            agent = state["agents"].setdefault(p["handle"], {})
            agent.update({**p, "effective_model": p["effective_model"] or "unknown", "effective_effort": p["effective_effort"] or "unknown"})
        elif kind == "evidence.recorded": state["evidence"][p["evidence_id"]] = {**p, "event_id": row["event_id"]}
        elif kind == "check.recorded": state["checks"][p["check_id"]] = {**p, "event_id": row["event_id"]}
        elif kind == "finding.opened": state["findings"][p["finding_id"]] = {**p, "event_id": row["event_id"], "disposition": None}
        elif kind == "finding.dispositioned": state["findings"][p["finding_id"]]["disposition"] = p
        elif kind == "knowledge.selected":
            state["knowledge_selection"] = copy.deepcopy(p)
            for match in p["matches"]:
                key = (match["id"], match["revision"], p["generation_id"])
                if key not in selected_revisions:
                    selected_revisions.add(key)
                    state["knowledge_selected_revisions"].append({"id": match["id"], "revision": match["revision"],
                        "generation_id": p["generation_id"], "status": match["status"], "reason": match["reason"],
                        "application": "unknown"})
        elif kind == "knowledge.feedback": state["knowledge_feedback"].append({**p, "event_id": row["event_id"]})
        elif kind == "checkpoint.written": state.update({"baselines": p["baselines"], "next_action": p["next_action"], "unresolved_user_items": p["unresolved_user_items"]})
        elif kind == "run.closed": state["terminal"] = p
    facts = execution_facts(rows)
    for handle, key in facts["current_assignment"].items():
        observation = facts["observations"].get(key)
        if observation:
            state["agents"][handle].update({**observation,
                "effective_model": observation["effective_model"] or "unknown",
                "effective_effort": observation["effective_effort"] or "unknown"})
    for task_id, task in facts["current"].items():
        key = (task_id, task["revision"]); current = state["tasks"][task_id]
        current.pop("result", None)
        current["state"] = "admitted" if key in facts["admitted"] else "planned"
        if key in facts["results"]:
            current["result"] = facts["results"][key]
            current["state"] = facts["results"][key]["outcome"]
    return state


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(raw)
    try:
        with os.fdopen(fd, "wb") as stream: stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists(): tmp.unlink()


def encode(value: Any) -> bytes:
    return (json.dumps(value, allow_nan=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def write_snapshot(run_dir: Path) -> dict[str, Any]:
    rows, raw = read_events(run_dir / "events.jsonl"); state = validate(rows)
    state["events_sha256"] = hashlib.sha256(raw).hexdigest(); atomic_write(run_dir / "snapshot.json", encode(state)); return state


def bound_snapshot(run_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]], bytes]:
    rows, raw = read_events(run_dir / "events.jsonl"); expected = validate(rows); digest = hashlib.sha256(raw).hexdigest(); expected["events_sha256"] = digest; path = run_dir / "snapshot.json"
    stale = True
    if path.exists():
        try: stale = read_json(path) != expected
        except (ContractError, OSError, AttributeError): stale = True
    state = write_snapshot(run_dir) if stale else expected
    return state, rows, raw


def runtime_paths(explicit: str | None = None) -> dict[str, Any]:
    """One cwd-independent root contract, shared by both installed helpers."""
    if explicit is not None:
        raw, source = explicit, "argument"
    elif "SAGE_STATE_ROOT" in os.environ:
        raw, source = os.environ["SAGE_STATE_ROOT"], "SAGE_STATE_ROOT"
    elif "CODEX_HOME" in os.environ:
        home = absolute_runtime_path(os.environ["CODEX_HOME"])
        raw, source = str(home / "sage"), "CODEX_HOME"
    else:
        raw, source = str(Path.home() / ".codex/sage"), "default"
    root = absolute_runtime_path(raw)
    fail(root.exists() and not root.is_dir(), "invalid_path", f"state root must be a directory: {root}")
    return {"state_root": str(root), "root_source": source, "root_exists": root.exists(),
            "runs_dir": str(root / "runs"), "references_dir": str(root / "run-references"),
            "store_dir": str(runtime_namespace(root, "knowledge"))}


def absolute_runtime_path(raw: str) -> Path:
    fail(not isinstance(raw, str) or not raw.strip() or "\x00" in raw, "invalid_path", "runtime path must be nonempty text")
    try:
        path = Path(raw).expanduser()
        fail(not path.is_absolute(), "invalid_path", f"runtime path must be absolute, independent of the task directory: {raw}")
        return path.resolve()
    except (RuntimeError, ValueError) as exc:
        raise ContractError("invalid_path", f"cannot resolve runtime path: {raw}") from exc


def runtime_namespace(root: Path, name: str) -> Path:
    path = root / name
    fail(path.is_symlink() or (path.exists() and not path.is_dir()), "invalid_path", f"runtime namespace must be a real directory: {path}")
    return path


def registered_run(reference: Path) -> tuple[Path, dict[str, Any], bytes]:
    fail(reference.is_symlink() or not reference.is_file(), "invalid_reference", f"invalid run reference: {reference}")
    value = read_json(reference)
    fail(not isinstance(value, dict) or set(value) != {"v", "run_id", "run_dir", "events_sha256"}, "invalid_reference", "invalid run reference fields")
    fail(type(value["v"]) is not int or value["v"] != 1, "invalid_reference", "invalid run reference version")
    identifier(value["run_id"], "registered run_id")
    fail(reference.name != value["run_id"] + ".json", "invalid_reference", "reference name does not match run ID")
    path = absolute_runtime_path(value["run_dir"])
    fail(str(path) != value["run_dir"], "invalid_reference", "registered path changed or is not canonical")
    rows, raw = read_events(path / "events.jsonl")
    fail(hashlib.sha256(raw).hexdigest() != value["events_sha256"], "invalid_reference", f"registered log changed: {path}")
    state = validate(rows, terminal=True)
    fail(state["run_id"] != value["run_id"], "invalid_reference", "registered run ID mismatch")
    return path, state, raw


def resolve_run(root: Path, run_id: str, *, new: bool = False) -> Path:
    identifier(run_id, "run_id")
    run = runtime_namespace(root, "runs") / run_id
    reference = runtime_namespace(root, "run-references") / (run_id + ".json")
    fail(run.is_symlink(), "invalid_path", f"canonical run must not be a symlink: {run}")
    fail(new and run.exists(), "state_exists", f"canonical run ID is occupied: {run_id}")
    if reference.exists() or reference.is_symlink():
        fail(new or run.exists(), "state_exists", f"run ID is already registered or duplicated: {run_id}")
        return registered_run(reference)[0]
    if not new:
        fail(not run.exists(), "invalid_reference", f"run ID is not present in the selected root: {run_id}")
        rows, _ = read_events(run / "events.jsonl")
        state = validate(rows)
        fail(state["run_id"] != run_id, "invalid_reference", "directory name does not match run ID")
    return run


def command_register(args: argparse.Namespace) -> dict[str, Any]:
    """Enroll a closed legacy run without moving evidence or rewriting history."""
    layout = runtime_paths(args.state_root)
    root = Path(layout["state_root"])
    source = Path(args.run_dir).expanduser().resolve()
    rows, raw = read_events(source / "events.jsonl")
    state = validate(rows, terminal=True)
    run_id = state["run_id"]
    canonical = runtime_namespace(root, "runs") / run_id
    refs = runtime_namespace(root, "run-references")
    reference = refs / (run_id + ".json")
    fail(canonical.exists() or canonical.is_symlink(), "state_exists", f"run ID already occupies the canonical namespace: {run_id}")
    value = {"v": 1, "run_id": run_id, "run_dir": str(source), "events_sha256": hashlib.sha256(raw).hexdigest()}
    if reference.exists() or reference.is_symlink():
        registered_run(reference)
        fail(read_json(reference) != value, "state_exists", f"run ID already registered: {run_id}")
    else:
        atomic_write(reference, encode(value))
    return {"ok": True, **value, "state_root": str(root), "reference": str(reference)}


def command_list_runs(args: argparse.Namespace) -> dict[str, Any]:
    layout = runtime_paths(args.state_root)
    fail(not 1 <= args.limit <= 128 or args.offset < 0, "invalid_arguments", "limit must be 1..128 and offset nonnegative")
    root = Path(layout["state_root"])
    runs = runtime_namespace(root, "runs")
    refs = runtime_namespace(root, "run-references")
    entries = ([(p.name, "canonical", p) for p in runs.iterdir()] if runs.exists() else [])
    entries += ([(p.stem, "registered", p) for p in refs.iterdir()] if refs.exists() else [])
    entries.sort(key=lambda x: (x[0], x[1], str(x[2])))
    counts: dict[str, int] = {}
    for run_id, _, _ in entries: counts[run_id] = counts.get(run_id, 0) + 1
    results = []
    for run_id, origin, path in entries[args.offset:args.offset + args.limit]:
        item: dict[str, Any] = {"run_id": run_id, "origin": origin, "entry_path": str(path), "eligible": False}
        try:
            identifier(run_id, "run_id")
            fail(counts[run_id] != 1, "duplicate_id", f"multiple entries for run ID: {run_id}")
            if origin == "registered":
                run, state, raw = registered_run(path)
            else:
                fail(path.is_symlink() or not path.is_dir(), "invalid_path", f"invalid run directory: {path}")
                run = path
                rows, raw = read_events(path / "events.jsonl")
                state = validate(rows)
                fail(state["run_id"] != run_id, "invalid_reference", "directory name does not match run ID")
            status = state["terminal"]["status"] if state["terminal"] else "active"
            item.update(run_dir=str(run), status=status, eligible=status in {"completed", "failed", "stopped"},
                        events_sha256=hashlib.sha256(raw).hexdigest(), last_seq=state["last_seq"])
        except (ContractError, OSError) as exc:
            item.update(status="quarantined", code=exc.code if isinstance(exc, ContractError) else "io_error", reason=str(exc))
        results.append(item)
    next_offset = args.offset + len(results)
    return {"ok": True, **layout, "runs": results, "total_entries": len(entries),
            "next_offset": next_offset if next_offset < len(entries) else None}


def command_init(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = Path(args.run_dir).resolve(); identifier(args.run_id, "run_id"); text(args.objective, "objective")
    fail(run_dir.exists() and any(run_dir.iterdir()), "state_exists", "run directory already contains state")
    criteria = read_json(Path(args.criteria).resolve()); fail(not isinstance(criteria, list), "invalid_event", "criteria file must contain an array")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    row = {"v": 1, "event_id": "e-1", "run_id": args.run_id, "seq": 1, "at": now, "actor": "root", "type": "run.opened", "payload": {"objective": args.objective, "criteria": criteria, "constraints": [], "next_action": "plan"}}
    validate([row]); atomic_write(run_dir / "events.jsonl", encode(row))
    result = {"ok": True, "run_id": args.run_id, "event_id": "e-1", "run_dir": str(run_dir), "discoverable": args.canonical}
    if not args.canonical:
        result["warning"] = "Explicit --run-dir bypasses central discovery; register this run after closure, or use --run-id with the shared state root."
    return result


def command_append(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = Path(args.run_dir).resolve(); rows, raw = read_events(run_dir / "events.jsonl")
    if args.event:
        additions = [read_json(Path(args.event).resolve())]
    else:
        additions, _ = read_events(Path(args.events).resolve())
    fail(any(not isinstance(x, dict) for x in additions), "invalid_json", "append input must contain event objects")
    proposed = rows + additions; validate(proposed)
    appended = b"".join(encode(x) for x in additions); prefix = raw if not raw or raw.endswith(b"\n") else raw + b"\n"
    atomic_write(run_dir / "events.jsonl", prefix + appended)
    return {"ok": True, "appended": len(additions), "last_seq": proposed[-1]["seq"]}


def command_validate(args: argparse.Namespace) -> dict[str, Any]:
    rows, _ = read_events(Path(args.run_dir).resolve() / "events.jsonl"); state = validate(rows, args.terminal)
    return {"ok": True, "run_id": state["run_id"], "last_seq": state["last_seq"], "terminal": state["terminal"] is not None}


def command_resume(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = Path(args.run_dir).resolve(); state, rows, _ = bound_snapshot(run_dir); live = read_json(Path(args.agents).resolve())
    fail(not isinstance(live, list), "invalid_json", "agents file must contain an array")
    handles = [x.get("handle") for x in live if isinstance(x, dict)]
    fail(any(not isinstance(x, str) for x in handles) or len(handles) != len(live), "invalid_json", "every live agent must be an object with a handle")
    fail(len(handles) != len(set(handles)), "duplicate_id", "duplicate live agent handle")
    for agent in live:
        native_handle(agent["handle"]); need(agent, {"handle", "lifecycle"}, "live agent")
        choice(agent["lifecycle"], {"active", "idle", "completed", "failed", "interrupted", "missing"}, "live lifecycle")
        if "effect_status" in agent: choice(agent["effect_status"], {"none", "reconciled", "unknown"}, "live effect status")
        for field in ("effective_model", "effective_effort"):
            fail(field in agent and agent[field] is not None and not isinstance(agent[field], str), "invalid_event", f"{field} must be text or null")
    live_by_handle = {x.get("handle"): x for x in live if isinstance(x, dict) and isinstance(x.get("handle"), str)}
    proposals = []; seq = rows[-1]["seq"]
    facts = execution_facts(rows)
    for handle, recorded in state["agents"].items():
        if facts["current_assignment"].get(handle) in facts["released_assignments"]: continue
        observed = live_by_handle.get(handle, {"handle": handle, "lifecycle": "missing"}); lifecycle = observed.get("lifecycle", "missing")
        choice(lifecycle, {"active", "idle", "completed", "failed", "interrupted", "missing"}, f"live lifecycle for {handle}")
        seq += 1; now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        supplied_effect = observed.get("effect_status", "unknown")
        choice(supplied_effect, {"none", "reconciled", "unknown"}, f"live effect status for {handle}")
        effect = supplied_effect
        if lifecycle in {"idle", "interrupted", "missing"}: effect = "unknown"
        proposals.append({"v": 1, "event_id": f"resume-{seq}", "run_id": state["run_id"], "seq": seq, "at": now, "actor": "root", "type": "agent.observed", "payload": {"handle": handle, "lifecycle": lifecycle, "effect_status": effect, "effective_model": observed.get("effective_model"), "effective_effort": observed.get("effective_effort")}})
    unsafe = any(facts["tasks"][key]["effect"] in {"write", "external", "unknown"} and key not in facts["released"]
                 for key in facts["admitted"])
    return {"ok": True, "run_id": state["run_id"], "proposed_events": proposals, "admission_allowed": not unsafe and state["terminal"] is None, "recommended_next_action": "revise_plan" if unsafe else state["next_action"]}


def command_report(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = Path(args.run_dir).resolve(); state, _, _ = bound_snapshot(run_dir)
    observations = [x for x in state["evidence"].values() if x["kind"] == "observation"]
    inferences = [x for x in state["evidence"].values() if x["kind"] == "inference"]
    unknowns = [x["locator"] for x in state["evidence"].values() if x["kind"] == "unknown"]
    for handle, agent in state["agents"].items():
        unknown_fields = [f"{field}=unknown" for field in ("effective_model", "effective_effort", "lifecycle", "effect_status")
                          if agent.get(field) == "unknown"]
        if unknown_fields: unknowns.append(f"{handle}: {', '.join(unknown_fields)}")
    untested_evidence = [x for x in state["evidence"].values() if x["kind"] == "untested"]
    untested_checks = [x for x in state["checks"].values() if x["outcome"] == "not_tested"]
    failed_checks = [x for x in state["checks"].values() if x["outcome"] == "failed"]
    open_findings = [x for x in state["findings"].values() if x["disposition"] is None]
    accepted = [x for x in state["findings"].values() if x["disposition"] and x["disposition"]["disposition"] == "accepted"]
    def bullets(items: list[Any], render=lambda x: str(x)) -> str:
        return "\n".join(f"- {render(x)}" for x in items) or "- No entries recorded."
    delivered = [f"{key}: {value.get('state', 'planned')}" for key, value in state["tasks"].items() if value.get("state") == "passed"]
    failed_tasks = [f"{key}: failed" for key, value in state["tasks"].items() if value.get("state") == "failed"]
    unfinished = [f"{key}: {value.get('state', 'planned')}" for key, value in state["tasks"].items() if value.get("state") not in {"passed", "failed"}]
    current_result_keys = {(task_id, task["revision"]) for task_id, task in state["tasks"].items()}
    historical_results = [f"{item['task_id']} revision {item['task_revision']}: {item['outcome']}"
                          for item in state["task_results"]
                          if (item["task_id"], item["task_revision"]) not in current_result_keys]
    approaches = [f"Approach {item['approach']}: plan revision {item['plan_revision']} ({item['reason']})" +
                  (f"; cause={item['cause']}; strategy={item['strategy_change']}" if "strategy_change" in item else "")
                  for item in state["approach_history"]]
    task_dispositions = [f"{item['task_id']} revision {item['task_revision']}: {item['disposition']} — {item['reason']}"
                         for item in state["task_dispositions"]]
    human = state["terminal"]["remaining_human_items"] if state["terminal"] else state["unresolved_user_items"]
    status = state["terminal"]["status"] if state["terminal"] else "active"
    scope = state["terminal"]["scope_reconciled"] if state["terminal"] else "not closed"
    next_action = f"Run is terminal ({status}); no further admission." if state["terminal"] else state["next_action"]
    report = f"# Sage run {state['run_id']}\n\n## Outcome\n\n- Status: {status}\n- Scope reconciled: {scope}\n\n## Approach history\n\n{bullets(approaches)}\n\n## Recorded passed tasks\n\n{bullets(delivered)}\n\n## Failed tasks\n\n{bullets(failed_tasks)}\n\n## Historical task results\n\n{bullets(historical_results)}\n\n## Task dispositions\n\n{bullets(task_dispositions)}\n\n## Unfinished tasks\n\n{bullets(unfinished)}\n\n## Observed evidence\n\n{bullets(observations, lambda x: x['locator'])}\n\n## Inferences\n\n{bullets(inferences, lambda x: x['locator'])}\n\n## Unknowns\n\n{bullets(unknowns)}\n\n## Untested evidence\n\n{bullets(untested_evidence, lambda x: x['locator'])}\n\n## Failed checks\n\n{bullets(failed_checks, lambda x: x['check_id'])}\n\n## Untested checks\n\n{bullets(untested_checks, lambda x: x['check_id'])}\n\n## Open findings\n\n{bullets(open_findings, lambda x: x['summary'])}\n\n## Accepted limitations\n\n{bullets(accepted, lambda x: x['summary'])}\n\n## Remaining human items\n\n{bullets(human)}\n\n## Next action\n\n{next_action}\n"
    atomic_write(run_dir / "report.md", report.encode()); return {"ok": True, "run_id": state["run_id"], "report": str(run_dir / "report.md")}


class CliParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ContractError("invalid_arguments", message)


def parser() -> argparse.ArgumentParser:
    root = CliParser(); commands = root.add_subparsers(dest="command", required=True)
    paths = commands.add_parser("paths"); paths.set_defaults(func=lambda a: {"ok": True, **runtime_paths(a.state_root)})
    listing = commands.add_parser("list-runs"); listing.add_argument("--limit", type=int, default=20); listing.add_argument("--offset", type=int, default=0); listing.set_defaults(func=command_list_runs)
    register = commands.add_parser("register"); register.add_argument("--run-dir", required=True); register.set_defaults(func=command_register)
    init = commands.add_parser("init"); init.add_argument("--run-dir"); init.add_argument("--run-id", required=True); init.add_argument("--objective", required=True); init.add_argument("--criteria", required=True); init.set_defaults(func=command_init)
    append = commands.add_parser("append"); choice = append.add_mutually_exclusive_group(required=True); choice.add_argument("--event"); choice.add_argument("--events"); append.set_defaults(func=command_append)
    valid = commands.add_parser("validate"); valid.add_argument("--terminal", action="store_true"); valid.set_defaults(func=command_validate)
    snap = commands.add_parser("snapshot"); snap.add_argument("--write", action="store_true", required=True); snap.set_defaults(func=lambda a: {"ok": True, **write_snapshot(Path(a.run_dir).resolve())})
    resume = commands.add_parser("resume"); resume.add_argument("--agents", required=True); resume.set_defaults(func=command_resume)
    report = commands.add_parser("report"); report.add_argument("--write", action="store_true", required=True); report.set_defaults(func=command_report)
    for command in (paths, listing, register, init, append, valid, snap, resume, report):
        command.add_argument("--state-root", help="absolute runtime root; otherwise SAGE_STATE_ROOT, CODEX_HOME/sage, or ~/.codex/sage")
    for command in (append, valid, snap, resume, report):
        target = command.add_mutually_exclusive_group(required=True)
        target.add_argument("--run-dir"); target.add_argument("--run-id")
    return root


def main() -> int:
    try:
        value = parser().parse_args()
        if value.command not in {"paths", "list-runs", "register"}:
            value.canonical = value.run_dir is None
            if value.canonical:
                layout = runtime_paths(value.state_root)
                value.run_dir = str(resolve_run(Path(layout["state_root"]), value.run_id, new=value.command == "init"))
            else:
                fail(value.state_root is not None, "invalid_arguments", "--run-dir and --state-root are alternative targets")
                supplied_run = Path(value.run_dir).expanduser()
                value.run_dir = str(supplied_run.resolve())
                if value.command == "init":
                    # Preserve explicit fixture access even if unrelated root configuration is invalid.
                    try: layout = runtime_paths()
                    except ContractError: layout = None
                    if layout and supplied_run.parent.resolve() / supplied_run.name == Path(layout["runs_dir"]) / value.run_id:
                        value.run_dir = str(resolve_run(Path(layout["state_root"]), value.run_id, new=True))
                        value.canonical = True
        result = value.func(value)
        if getattr(value, "canonical", False):
            result.update(state_root=layout["state_root"], run_dir=value.run_dir)
        sys.stdout.write(json.dumps(result, allow_nan=False, sort_keys=True) + "\n"); return 0
    except ContractError as exc:
        code = 3 if exc.code == "io_error" else 2; sys.stderr.write(json.dumps({"ok": False, "code": exc.code, "message": exc.message}, sort_keys=True) + "\n"); return code
    except OSError as exc:
        sys.stderr.write(json.dumps({"ok": False, "code": "io_error", "message": str(exc)}, sort_keys=True) + "\n"); return 3


if __name__ == "__main__": raise SystemExit(main())
