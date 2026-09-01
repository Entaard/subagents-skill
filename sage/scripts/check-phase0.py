#!/usr/bin/env python3
"""Validate Sage Phase 0 contracts with Python's standard library only."""

from __future__ import annotations

import argparse
import copy
import dataclasses
import datetime as dt
import glob
import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


# Phase 0 implementation paths are rooted in ``sage/``. Baseline corpus paths
# and repository history remain rooted in the enclosing Git repository.
ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_ROOT = ROOT.parent


@dataclasses.dataclass(frozen=True)
class Issue:
    code: str
    location: str
    message: str

    def render(self) -> str:
        return f"{self.code} {self.location}: {self.message}"


class DuplicateKeyError(ValueError):
    pass


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_nonfinite_constant(value: str) -> None:
    raise ValueError(f"non-JSON numeric constant {value!r}")


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(
            handle,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonfinite_constant,
        )


def canonical_normalize(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))
    if isinstance(value, list):
        return [canonical_normalize(item) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, child in value.items():
            normalized_key = unicodedata.normalize("NFC", key.replace("\r\n", "\n").replace("\r", "\n"))
            if normalized_key in normalized:
                raise ValueError(f"canonical JSON object keys collide after normalization: {normalized_key!r}")
            normalized[normalized_key] = canonical_normalize(child)
        return normalized
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("canonical JSON forbids non-finite numbers")
    return value


def canonical_json_bytes(value: Any) -> bytes:
    normalized = canonical_normalize(value)
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def json_pointer(document: Any, pointer: str) -> Any:
    if pointer in ("", "/"):
        return document
    current = document
    for raw_part in pointer.lstrip("/").split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(part)]
        else:
            current = current[part]
    return current


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and not (isinstance(value, float) and not math.isfinite(value))
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    return False


def validate_schema(instance: Any, schema: dict[str, Any], root_schema: dict[str, Any] | None = None, location: str = "$") -> list[Issue]:
    root_schema = root_schema or schema
    if "$ref" in schema:
        reference = schema["$ref"]
        if not reference.startswith("#/"):
            return [Issue("SCHEMA-REF", location, f"unsupported non-local reference {reference}")]
        try:
            target = json_pointer(root_schema, reference[1:])
        except (KeyError, IndexError, ValueError) as error:
            return [Issue("SCHEMA-REF", location, f"unresolved reference {reference}: {error}")]
        return validate_schema(instance, target, root_schema, location)

    issues: list[Issue] = []

    if "oneOf" in schema:
        branch_results = [validate_schema(instance, branch, root_schema, location) for branch in schema["oneOf"]]
        passing = [result for result in branch_results if not result]
        if len(passing) == 1:
            return []
        if not passing:
            nonempty = [result for result in branch_results if result]
            return min(nonempty, key=len) if nonempty else [Issue("SCHEMA-ONEOF", location, "no oneOf branch matched")]
        return [Issue("SCHEMA-ONEOF", location, f"{len(passing)} oneOf branches matched")]

    expected_type = schema.get("type")
    if expected_type is not None:
        candidates = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(_type_matches(instance, candidate) for candidate in candidates):
            return [Issue("SCHEMA-TYPE", location, f"expected {candidates}, got {type(instance).__name__}")]

    if "const" in schema and instance != schema["const"]:
        issues.append(Issue("SCHEMA-CONST", location, f"expected constant {schema['const']!r}"))
    if "enum" in schema and instance not in schema["enum"]:
        issues.append(Issue("SCHEMA-ENUM", location, f"value {instance!r} is outside the enum"))

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                issues.append(Issue("SCHEMA-REQUIRED", f"{location}/{key}", "required property is missing"))
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in properties:
                    issues.append(Issue("SCHEMA-ADDITIONAL", f"{location}/{key}", "additional property is forbidden"))
        for key, subschema in properties.items():
            if key in instance:
                issues.extend(validate_schema(instance[key], subschema, root_schema, f"{location}/{key}"))

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            issues.append(Issue("SCHEMA-MIN-ITEMS", location, f"requires at least {schema['minItems']} items"))
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, sort_keys=True, separators=(",", ":")) for item in instance]
            if len(encoded) != len(set(encoded)):
                issues.append(Issue("SCHEMA-UNIQUE", location, "array items are not unique"))
        if "items" in schema:
            for index, item in enumerate(instance):
                issues.extend(validate_schema(item, schema["items"], root_schema, f"{location}/{index}"))

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            issues.append(Issue("SCHEMA-MIN-LENGTH", location, f"requires at least {schema['minLength']} characters"))
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            issues.append(Issue("SCHEMA-PATTERN", location, f"does not match {schema['pattern']!r}"))
        if schema.get("format") == "date-time":
            try:
                parse_timestamp(instance)
            except ValueError:
                issues.append(Issue("SCHEMA-FORMAT", location, "is not an ISO 8601 date-time"))

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if isinstance(instance, float) and not math.isfinite(instance):
            issues.append(Issue("SCHEMA-NONFINITE", location, "number must be finite JSON"))
            return issues
        if "minimum" in schema and instance < schema["minimum"]:
            issues.append(Issue("SCHEMA-MINIMUM", location, f"must be >= {schema['minimum']}"))
        if "exclusiveMinimum" in schema and instance <= schema["exclusiveMinimum"]:
            issues.append(Issue("SCHEMA-MINIMUM", location, f"must be > {schema['exclusiveMinimum']}"))

    return issues


def parse_timestamp(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp lacks timezone")
    return parsed


def _ids(items: Iterable[dict[str, Any]], field: str) -> tuple[set[str], list[Issue]]:
    values: set[str] = set()
    issues: list[Issue] = []
    for index, item in enumerate(items):
        value = item.get(field)
        if value in values:
            issues.append(Issue("ART-DUPLICATE-ID", f"{field}[{index}]", f"duplicate id {value}"))
        values.add(value)
    return values, issues


def artifact_semantic_issues(run: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    plan = run.get("plan", {})
    revisions = plan.get("revisions", [])
    revision_numbers = [revision.get("revision") for revision in revisions]
    revisions_by_number: dict[Any, dict[str, Any]] = {}
    for index, revision in enumerate(revisions):
        number = revision.get("revision")
        if number in revisions_by_number:
            issues.append(Issue("ART-DUPLICATE-REVISION", f"$/plan/revisions/{index}/revision", f"duplicate revision {number}"))
        else:
            revisions_by_number[number] = revision
    numbers = sorted(number for number in revisions_by_number if isinstance(number, int))
    expected_numbers = list(range(0 if numbers and numbers[0] == 0 else 1, (numbers[-1] + 1) if numbers else 1))
    if numbers != expected_numbers or revision_numbers != expected_numbers:
        issues.append(Issue("ART-PLAN-SEQUENCE", "$/plan/revisions", f"revision sequence is {revision_numbers}, expected {expected_numbers}"))
    if not numbers or plan.get("current_revision") != numbers[-1]:
        issues.append(Issue("ART-PLAN-CURRENT", "$/plan/current_revision", f"must identify latest revision {numbers[-1] if numbers else None}"))

    all_prior_units: set[tuple[str, int]] = set()
    unit_specs: dict[tuple[int, str, int], dict[str, Any]] = {}
    logical_unit_specs: dict[tuple[str, int], bytes] = {}
    criteria: set[str] = set()
    criterion_definitions: dict[str, bytes] = {}
    prior_dispositions: list[tuple[int, dict[str, Any]]] = []
    prior_admitted_at: dt.datetime | None = None
    for index, revision in enumerate(revisions):
        number = revision.get("revision")
        prior = revision.get("expected_prior_revision")
        if index == 0 and prior is not None:
            issues.append(Issue("ART-PLAN-PRIOR", f"$/plan/revisions/{index}/expected_prior_revision", "first revision must have null prior"))
        if index > 0 and prior != revisions[index - 1].get("revision"):
            issues.append(Issue("ART-PLAN-PRIOR", f"$/plan/revisions/{index}/expected_prior_revision", "must equal the immediately preceding revision"))
        try:
            created_at = parse_timestamp(revision.get("created_at", ""))
            admitted_value = revision.get("admitted_at")
            admitted_at = parse_timestamp(admitted_value) if admitted_value is not None else None
            if admitted_at is not None and created_at > admitted_at:
                issues.append(Issue("ART-PLAN-CHRONOLOGY", f"$/plan/revisions/{index}", "plan revision was admitted before it was created"))
            if index > 0 and (prior_admitted_at is None or prior_admitted_at > created_at):
                issues.append(Issue("ART-PLAN-CHRONOLOGY", f"$/plan/revisions/{index}", "plan revision predates admission of its immediate predecessor"))
            prior_admitted_at = admitted_at
        except (TypeError, ValueError):
            prior_admitted_at = None
        dispositions = {
            (entry.get("unit_id"), entry.get("unit_spec_revision"))
            for entry in revision.get("prior_units", [])
        }
        current_units_by_key = {
            (unit.get("unit_id"), unit.get("unit_spec_revision")): unit
            for unit in revision.get("units", [])
        }
        if index > 0 and dispositions != all_prior_units:
            missing = sorted(all_prior_units - dispositions)
            extra = sorted(dispositions - all_prior_units)
            issues.append(Issue("ART-PLAN-COVERAGE", f"$/plan/revisions/{index}/prior_units", f"missing prior units {missing}; unexpected {extra}"))
        for disposition_index, disposition in enumerate(revision.get("prior_units", [])):
            prior_dispositions.append((index, disposition))
            key = (disposition.get("unit_id"), disposition.get("unit_spec_revision"))
            decision = disposition.get("disposition")
            replacement = disposition.get("replacement_unit_spec_revision")
            if decision == "carried" and key not in current_units_by_key:
                issues.append(Issue("ART-PLAN-DISPOSITION", f"$/plan/revisions/{index}/prior_units/{disposition_index}", "carried unit is absent from the new revision"))
            if decision == "removed" and key in current_units_by_key:
                issues.append(Issue("ART-PLAN-DISPOSITION", f"$/plan/revisions/{index}/prior_units/{disposition_index}", "removed unit remains active"))
            if decision == "superseded":
                replacement_key = (disposition.get("unit_id"), replacement)
                if replacement is None or replacement_key not in current_units_by_key or replacement == disposition.get("unit_spec_revision"):
                    issues.append(Issue("ART-PLAN-DISPOSITION", f"$/plan/revisions/{index}/prior_units/{disposition_index}", "superseded unit lacks a distinct active replacement revision"))
            elif replacement is not None:
                issues.append(Issue("ART-PLAN-DISPOSITION", f"$/plan/revisions/{index}/prior_units/{disposition_index}/replacement_unit_spec_revision", "only superseded units may name a replacement"))
        admission = revision.get("admission_policy", {})
        bounds = revision.get("bounds", {})
        spend_limit = bounds.get("spend_limit")
        spend_unit = bounds.get("spend_unit")
        if (spend_limit is None) != (spend_unit is None):
            issues.append(Issue("ART-ADMISSION-POLICY", f"$/plan/revisions/{index}/bounds", "spend limit and unit must both be known or both null"))
        if isinstance(bounds.get("planned_agent_count"), int) and isinstance(bounds.get("max_admitted_agents"), int) and bounds.get("max_admitted_agents") < bounds.get("planned_agent_count"):
            issues.append(Issue("ART-ADMISSION-POLICY", f"$/plan/revisions/{index}/bounds/max_admitted_agents", "agent ceiling is below the planned agent count"))
        if spend_limit is None and admission.get("usage_provenance") != "unknown":
            issues.append(Issue("ART-ADMISSION-POLICY", f"$/plan/revisions/{index}/admission_policy/usage_provenance", "missing spend sensor must be recorded as unknown"))
        estimate_multiple = admission.get("estimate_multiple")
        if admission.get("profile") == "estimate-multiple":
            units = revision.get("units", [])
            unit_ceilings = estimate_multiple.get("unit_ceilings", []) if isinstance(estimate_multiple, dict) else []
            ceilings_by_key = {
                (ceiling.get("unit_id"), ceiling.get("unit_spec_revision")): ceiling
                for ceiling in unit_ceilings
            }
            expected_unit_keys = {(unit.get("unit_id"), unit.get("unit_spec_revision")) for unit in units}
            constants_match = isinstance(estimate_multiple, dict) and {
                "profile_id": estimate_multiple.get("profile_id"),
                "task_multiplier": estimate_multiple.get("task_multiplier"),
                "task_floor": estimate_multiple.get("task_floor"),
                "unit_multiplier": estimate_multiple.get("unit_multiplier"),
                "unit_floor": estimate_multiple.get("unit_floor"),
                "agent_multiplier": estimate_multiple.get("agent_multiplier"),
                "agent_floor": estimate_multiple.get("agent_floor"),
            } == {
                "profile_id": "estimate-multiple/baseline-v1",
                "task_multiplier": 4,
                "task_floor": 500000,
                "unit_multiplier": 4,
                "unit_floor": 150000,
                "agent_multiplier": 2,
                "agent_floor": 10,
            }
            task_estimate = estimate_multiple.get("task_estimate") if isinstance(estimate_multiple, dict) else None
            expected_task_ceiling = max(4 * task_estimate, 500000) if isinstance(task_estimate, (int, float)) else None
            formula_matches = (
                constants_match
                and admission.get("compatibility_profile") == "estimate-multiple/baseline-v1"
                and admission.get("control_strength") == "advisory"
                and isinstance(task_estimate, (int, float))
                and task_estimate >= sum(unit.get("estimated_spend", 0) for unit in units)
                and estimate_multiple.get("task_ceiling") == expected_task_ceiling
                and bounds.get("spend_limit") == expected_task_ceiling
                and bounds.get("spend_unit") == "normalized_tokens"
                and bounds.get("max_admitted_agents") == max(2 * bounds.get("planned_agent_count", 0), 10)
                and len(unit_ceilings) == len(ceilings_by_key)
                and set(ceilings_by_key) == expected_unit_keys
            )
            for unit in units:
                ceiling = ceilings_by_key.get((unit.get("unit_id"), unit.get("unit_spec_revision")), {})
                estimate = unit.get("estimated_spend")
                if ceiling.get("estimate") != estimate or ceiling.get("ceiling") != max(4 * estimate, 150000):
                    formula_matches = False
            if not formula_matches:
                issues.append(Issue("ART-ADMISSION-POLICY", f"$/plan/revisions/{index}/admission_policy/estimate_multiple", "baseline profile does not encode the exact 4x task/unit and 2x agent ceilings and floors"))
        elif estimate_multiple is not None:
            issues.append(Issue("ART-ADMISSION-POLICY", f"$/plan/revisions/{index}/admission_policy/estimate_multiple", "only estimate-multiple may carry estimate-derived formula inputs"))
        if admission.get("profile") == "uncapped-observed" and not bounds.get("uncapped_attended"):
            issues.append(Issue("ART-ADMISSION-POLICY", f"$/plan/revisions/{index}/bounds/uncapped_attended", "uncapped-observed must be attended"))
        if admission.get("profile") != "uncapped-observed" and bounds.get("uncapped_attended"):
            issues.append(Issue("ART-ADMISSION-POLICY", f"$/plan/revisions/{index}/bounds/uncapped_attended", "attended uncapped flag requires uncapped-observed profile"))
        if isinstance(bounds.get("max_units"), int) and len(revision.get("units", [])) > bounds.get("max_units"):
            issues.append(Issue("ART-ADMISSION-POLICY", f"$/plan/revisions/{index}/bounds/max_units", "unit count exceeds admitted bound"))
        if isinstance(bounds.get("max_plan_revisions"), int) and len(revisions) > bounds.get("max_plan_revisions"):
            issues.append(Issue("ART-ADMISSION-POLICY", f"$/plan/revisions/{index}/bounds/max_plan_revisions", "recorded revisions exceed admitted bound"))
        active_unit_ids: set[str] = set()
        for unit_index, unit in enumerate(revision.get("units", [])):
            unit_id = unit.get("unit_id")
            if unit_id in active_unit_ids:
                issues.append(Issue("ART-DUPLICATE-UNIT", f"$/plan/revisions/{index}/units/{unit_index}", f"duplicate active unit {unit_id}"))
            active_unit_ids.add(unit_id)
            key = (number, unit.get("unit_id"), unit.get("unit_spec_revision"))
            if key in unit_specs:
                issues.append(Issue("ART-DUPLICATE-UNIT", f"$/plan/revisions/{index}/units/{unit_index}", f"duplicate unit spec {key}"))
            else:
                unit_specs[key] = unit
            logical_key = (unit.get("unit_id"), unit.get("unit_spec_revision"))
            encoded = canonical_json_bytes(unit)
            if logical_key in logical_unit_specs and logical_unit_specs[logical_key] != encoded:
                issues.append(Issue("ART-UNIT-IMMUTABLE", f"$/plan/revisions/{index}/units/{unit_index}", f"unit spec {logical_key} changed without a new revision"))
            else:
                logical_unit_specs.setdefault(logical_key, encoded)
            for criterion in unit.get("acceptance_criteria", []):
                criterion_id = criterion.get("criterion_id")
                criterion_bytes = canonical_json_bytes(criterion)
                if criterion_id in criterion_definitions and criterion_definitions[criterion_id] != criterion_bytes:
                    issues.append(Issue("ART-CRITERION-IMMUTABLE", f"$/plan/revisions/{index}/units/{unit_index}", f"criterion {criterion_id} changed without a new ID"))
                criteria.add(criterion_id)
                criterion_definitions.setdefault(criterion_id, criterion_bytes)
            if revision.get("kind") == "bootstrap" and unit.get("effect_class") != "read_only":
                issues.append(Issue("ART-BOOTSTRAP-READONLY", f"$/plan/revisions/{index}/units", "bootstrap unit is not read-only"))
        all_prior_units.update((unit.get("unit_id"), unit.get("unit_spec_revision")) for unit in revision.get("units", []))

    briefs: dict[tuple[Any, Any], dict[str, Any]] = {}
    for index, brief in enumerate(run.get("briefs", [])):
        brief_key = (brief.get("brief_id"), brief.get("brief_revision"))
        if brief_key in briefs:
            issues.append(Issue("ART-DUPLICATE-BRIEF", f"$/briefs/{index}", f"duplicate brief revision {brief_key}"))
        else:
            briefs[brief_key] = brief
        key = (brief.get("plan_revision"), brief.get("unit_id"), brief.get("unit_spec_revision"))
        if key not in unit_specs:
            issues.append(Issue("ART-BINDING", f"$/briefs/{index}", "brief does not bind an existing unit spec"))
        revision = revisions_by_number.get(brief.get("plan_revision"))
        if revision and brief.get("caps") != revision.get("bounds"):
            issues.append(Issue("ART-BOUNDS-BINDING", f"$/briefs/{index}/caps", "brief caps differ from the exact admitted plan bounds"))
        if revision and revision.get("kind") == "bootstrap":
            forbidden = set(brief.get("allowed_effects", [])) - {"read"}
            if forbidden:
                issues.append(Issue("ART-BOOTSTRAP-READONLY", f"$/briefs/{index}/allowed_effects", f"bootstrap permits {sorted(forbidden)}"))

    attempt_ids, duplicate_issues = _ids(run.get("attempts", []), "attempt_id")
    issues.extend(duplicate_issues)
    attempts = {attempt.get("attempt_id"): attempt for attempt in run.get("attempts", [])}
    for index, attempt in enumerate(run.get("attempts", [])):
        key = (attempt.get("plan_revision"), attempt.get("unit_id"), attempt.get("unit_spec_revision"))
        brief = briefs.get((attempt.get("brief_id"), attempt.get("brief_revision")))
        if key not in unit_specs or brief is None:
            issues.append(Issue("ART-BINDING", f"$/attempts/{index}", "attempt does not bind existing unit and brief"))
        elif (
            brief.get("plan_revision"),
            brief.get("unit_id"),
            brief.get("unit_spec_revision"),
            brief.get("brief_hash"),
        ) != (
            attempt.get("plan_revision"),
            attempt.get("unit_id"),
            attempt.get("unit_spec_revision"),
            attempt.get("brief_hash"),
        ):
            issues.append(Issue("ART-BINDING", f"$/attempts/{index}", "attempt tuple or hash differs from its exact brief revision"))
        revision = revisions_by_number.get(attempt.get("plan_revision"))
        if revision and revision.get("kind") == "bootstrap" and attempt.get("side_effect_class") != "read_only":
            issues.append(Issue("ART-BOOTSTRAP-READONLY", f"$/attempts/{index}/side_effect_class", "bootstrap attempt is not read-only"))
        try:
            started_value = attempt.get("started_at")
            ended_value = attempt.get("ended_at")
            started_at = parse_timestamp(started_value) if started_value is not None else None
            ended_at = parse_timestamp(ended_value) if ended_value is not None else None
            admitted_value = revision.get("admitted_at") if revision else None
            admitted_at = parse_timestamp(admitted_value) if admitted_value is not None else None
            if started_at is not None and (admitted_at is None or started_at < admitted_at):
                issues.append(Issue("ART-ATTEMPT-CHRONOLOGY", f"$/attempts/{index}/started_at", "attempt started before its bound plan revision was admitted"))
            if ended_at is not None and (started_at is None or ended_at < started_at):
                issues.append(Issue("ART-ATTEMPT-CHRONOLOGY", f"$/attempts/{index}/ended_at", "attempt ended before it started"))
        except (TypeError, ValueError):
            pass

    result_ids, duplicate_issues = _ids(run.get("results", []), "result_id")
    issues.extend(duplicate_issues)
    results = {result.get("result_id"): result for result in run.get("results", [])}
    for index, result in enumerate(run.get("results", [])):
        attempt = attempts.get(result.get("attempt_id"))
        if attempt is None:
            issues.append(Issue("ART-BINDING", f"$/results/{index}/attempt_id", "result does not bind an attempt"))
        elif result.get("acceptance") == "accepted" and attempt.get("state") != "completed":
            issues.append(Issue("ART-RESULT-TERMINAL", f"$/results/{index}", f"accepted result binds attempt in {attempt.get('state')}"))
        if result.get("acceptance") == "accepted" and result.get("accepted_at") is None:
            issues.append(Issue("ART-RESULT-ACCEPTANCE", f"$/results/{index}/accepted_at", "accepted result lacks acceptance time"))
        if result.get("acceptance") != "accepted" and result.get("accepted_at") is not None:
            issues.append(Issue("ART-RESULT-ACCEPTANCE", f"$/results/{index}/accepted_at", "non-accepted result has acceptance time"))
        if attempt and attempt.get("result_id") != result.get("result_id"):
            issues.append(Issue("ART-BINDING", f"$/results/{index}", "attempt/result links disagree"))
        try:
            received_at = parse_timestamp(result.get("received_at", ""))
            accepted_value = result.get("accepted_at")
            accepted_at = parse_timestamp(accepted_value) if accepted_value is not None else None
            started_value = attempt.get("started_at") if attempt else None
            started_at = parse_timestamp(started_value) if started_value is not None else None
            if started_at is None or received_at < started_at:
                issues.append(Issue("ART-RESULT-CHRONOLOGY", f"$/results/{index}/received_at", "result was received before its attempt started"))
            if accepted_at is not None and accepted_at < received_at:
                issues.append(Issue("ART-RESULT-CHRONOLOGY", f"$/results/{index}/accepted_at", "result was accepted before it was received"))
        except (TypeError, ValueError):
            pass
    decision_ids, duplicate_issues = _ids(run.get("decisions", []), "decision_id")
    issues.extend(duplicate_issues)
    decisions = {decision.get("decision_id"): decision for decision in run.get("decisions", [])}
    used_adoption_decisions: set[Any] = set()
    for revision_index, disposition in prior_dispositions:
        prior_key = (disposition.get("unit_id"), disposition.get("unit_spec_revision"))
        target_revision = revisions[revision_index] if revision_index < len(revisions) else {}
        target_revision_number = target_revision.get("revision")
        target_criteria = {
            criterion.get("criterion_id")
            for unit in target_revision.get("units", [])
            for criterion in unit.get("acceptance_criteria", [])
        }
        for adoption_index, adoption in enumerate(disposition.get("result_adoptions", [])):
            result_id = adoption.get("result_id")
            result = results.get(result_id)
            attempt = attempts.get(result.get("attempt_id")) if result else None
            decision = decisions.get(adoption.get("decision_id"))
            criterion_ids = adoption.get("target_criterion_ids", [])
            expected_decision = {
                "prior_unit_id": disposition.get("unit_id"),
                "prior_unit_spec_revision": disposition.get("unit_spec_revision"),
                "result_id": result_id,
                "target_plan_revision": target_revision_number,
                "target_criterion_ids": criterion_ids,
            }
            chronology_valid = False
            try:
                accepted_at = parse_timestamp(result.get("accepted_at", "")) if result else None
                created_at = parse_timestamp(target_revision.get("created_at", ""))
                admitted_at = parse_timestamp(target_revision.get("admitted_at", ""))
                decided_at = parse_timestamp(decision.get("recorded_at", "")) if decision else None
                chronology_valid = bool(accepted_at and decided_at and accepted_at <= created_at <= decided_at <= admitted_at)
            except (TypeError, ValueError):
                chronology_valid = False
            if (
                result is None
                or attempt is None
                or (attempt.get("unit_id"), attempt.get("unit_spec_revision")) != prior_key
                or result.get("acceptance") != "accepted"
                or adoption.get("target_plan_revision") != target_revision_number
                or not criterion_ids
                or not set(criterion_ids).issubset(target_criteria)
                or decision is None
                or decision.get("kind") != "adoption"
                or decision.get("adoption") != expected_decision
                or not chronology_valid
            ):
                issues.append(Issue("ART-PLAN-ADOPTION", f"$/plan/revisions/{revision_index}/prior_units/{adoption_index}", f"adoption of {result_id} lacks an earlier accepted result, current criteria, matching decision, or valid chronology"))
            used_adoption_decisions.add(adoption.get("decision_id"))
    for index, decision in enumerate(run.get("decisions", [])):
        if decision.get("kind") == "adoption":
            if decision.get("adoption") is None or decision.get("decision_id") not in used_adoption_decisions:
                issues.append(Issue("ART-PLAN-ADOPTION", f"$/decisions/{index}", "adoption decision is not exactly linked from a prior-unit disposition"))
        elif decision.get("adoption") is not None:
            issues.append(Issue("ART-PLAN-ADOPTION", f"$/decisions/{index}/adoption", "non-adoption decision carries an adoption binding"))

    artifact_ids, duplicate_issues = _ids(run.get("artifacts", []), "artifact_id")
    issues.extend(duplicate_issues)
    for index, artifact in enumerate(run.get("artifacts", [])):
        producer = artifact.get("produced_by_attempt")
        if producer is not None and producer not in attempt_ids:
            issues.append(Issue("ART-BINDING", f"$/artifacts/{index}/produced_by_attempt", "artifact producer does not exist"))
    rendered = run.get("rendered_run_record")
    if rendered is not None and rendered.get("artifact_id") not in artifact_ids:
        issues.append(Issue("ART-BINDING", "$/rendered_run_record/artifact_id", "rendered record artifact does not exist"))

    finding_ids, duplicate_issues = _ids(run.get("findings", []), "finding_id")
    issues.extend(duplicate_issues)
    disposition_ids, duplicate_issues = _ids(run.get("dispositions", []), "disposition_id")
    issues.extend(duplicate_issues)
    disposition_by_finding: dict[str, list[dict[str, Any]]] = {}
    for disposition in run.get("dispositions", []):
        disposition_by_finding.setdefault(disposition.get("finding_id"), []).append(disposition)
    for finding_id in finding_ids:
        if len(disposition_by_finding.get(finding_id, [])) != 1:
            issues.append(Issue("ART-FINDING-DISPOSITION", "$/dispositions", f"finding {finding_id} has {len(disposition_by_finding.get(finding_id, []))} dispositions"))
    for finding_id in disposition_by_finding:
        if finding_id not in finding_ids:
            issues.append(Issue("ART-BINDING", "$/dispositions", f"disposition references unknown finding {finding_id}"))

    verification_ids, duplicate_issues = _ids(run.get("verifications", []), "verification_id")
    issues.extend(duplicate_issues)
    verifications = {verification.get("verification_id"): verification for verification in run.get("verifications", [])}
    for index, verification in enumerate(run.get("verifications", [])):
        if verification.get("criterion_id") not in criteria:
            issues.append(Issue("ART-BINDING", f"$/verifications/{index}/criterion_id", "verification references unknown criterion"))
    for index, disposition in enumerate(run.get("dispositions", [])):
        missing = set(disposition.get("verification_ids", [])) - verification_ids
        if missing:
            issues.append(Issue("ART-BINDING", f"$/dispositions/{index}/verification_ids", f"unknown verifications {sorted(missing)}"))
        if disposition.get("decision") == "rejected" and not disposition.get("evidence"):
            issues.append(Issue("ART-FINDING-EVIDENCE", f"$/dispositions/{index}/evidence", "rejected finding requires evidence"))
        if disposition.get("decision") == "accepted" and disposition.get("status") == "resolved":
            linked = [verifications.get(verification_id) for verification_id in disposition.get("verification_ids", [])]
            valid = any(
                verification
                and verification.get("subject_kind") == "finding"
                and verification.get("subject_id") == disposition.get("finding_id")
                and verification.get("verdict") == "pass"
                for verification in linked
            )
            if not valid:
                issues.append(Issue("ART-FINDING-VERIFICATION", f"$/dispositions/{index}/verification_ids", "resolved accepted finding lacks a passing finding verification"))

    if run.get("status") == "completed":
        completion = run.get("completion", {})
        if completion.get("state") != "closed":
            issues.append(Issue("ART-COMPLETED-STATE", "$/completion/state", "completed run is not closed"))
        awaiting_locations: list[str] = []

        def find_awaiting(value: Any, path: str) -> None:
            if value == "AwaitingHuman":
                awaiting_locations.append(path)
            elif isinstance(value, dict):
                for key, child in value.items():
                    find_awaiting(child, f"{path}/{key}")
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    find_awaiting(child, f"{path}/{index}")

        find_awaiting(run, "$")
        if awaiting_locations or completion.get("human_items"):
            issues.append(Issue("ART-COMPLETED-AWAITING", "$/completion", f"completed run retains human items at {awaiting_locations}"))

        current = revisions_by_number.get(plan.get("current_revision"), {})
        if current.get("kind") != "complete":
            issues.append(Issue("ART-COMPLETED-PLAN", "$/plan/current_revision", "completed run does not have a complete current plan"))
        pass_pairs = {
            (verification.get("subject_id"), verification.get("criterion_id"))
            for verification in run.get("verifications", [])
            if verification.get("verdict") == "pass" and verification.get("subject_kind") == "unit"
        }
        for unit in current.get("units", []):
            for criterion in unit.get("acceptance_criteria", []):
                if criterion.get("required") and (unit.get("unit_id"), criterion.get("criterion_id")) not in pass_pairs:
                    issues.append(Issue("ART-COMPLETED-VERIFICATION", "$/verifications", f"unit {unit.get('unit_id')} lacks passing verification for {criterion.get('criterion_id')}"))
            unit_attempts = [attempt for attempt in run.get("attempts", []) if attempt.get("unit_id") == unit.get("unit_id") and attempt.get("plan_revision") == current.get("revision")]
            accepted = any(
                attempt.get("state") == "completed"
                and attempt.get("result_id") in results
                and results[attempt.get("result_id")].get("acceptance") == "accepted"
                for attempt in unit_attempts
            )
            if not accepted:
                issues.append(Issue("ART-COMPLETED-RESULT", "$/attempts", f"unit {unit.get('unit_id')} lacks a terminal accepted result"))
        unresolved = [disposition.get("finding_id") for disposition in run.get("dispositions", []) if disposition.get("status") != "resolved"]
        if unresolved:
            issues.append(Issue("ART-COMPLETED-FINDINGS", "$/dispositions", f"unresolved findings {unresolved}"))
        if any(assumption.get("status") == "open" for assumption in run.get("assumptions", [])):
            issues.append(Issue("ART-COMPLETED-OPEN", "$/assumptions", "completed run has open assumption"))
        if any(gap.get("status") == "open" for gap in run.get("gaps", [])):
            issues.append(Issue("ART-COMPLETED-OPEN", "$/gaps", "completed run has open gap"))
        if run.get("coordination_outcome", {}).get("state") == "open":
            issues.append(Issue("ART-COMPLETED-OPEN", "$/coordination_outcome", "completed run has open coordination outcome"))
        required_completion = {
            "criteria_status": "pass",
            "checks_status": "pass",
            "findings_status": "resolved",
            "scope_status": "inside_scope",
        }
        for field, expected in required_completion.items():
            if completion.get(field) != expected:
                issues.append(Issue("ART-COMPLETED-STATE", f"$/completion/{field}", f"expected {expected}"))
        if not completion.get("claim") or not completion.get("claimed_at") or not completion.get("deliverable"):
            issues.append(Issue("ART-COMPLETED-STATE", "$/completion", "claim, timestamp, and deliverable are required"))
        if rendered is None:
            issues.append(Issue("ART-COMPLETED-STATE", "$/rendered_run_record", "completed run lacks rendered projection"))

    if run.get("status") == "AwaitingHuman":
        completion = run.get("completion", {})
        if completion.get("state") != "AwaitingHuman" or not completion.get("human_items"):
            issues.append(Issue("ART-AWAITING-HUMAN", "$/completion", "AwaitingHuman run must name pending human items"))

    return issues


def _is_canonical_absolute_path(value: Any) -> bool:
    if not isinstance(value, str) or not value.startswith("/") or value == "/" or "\x00" in value:
        return False
    if canonical_normalize(value) != value:
        return False
    parts = value[1:].split("/")
    return bool(parts) and all(part not in ("", ".", "..") for part in parts) and str(PurePosixPath(value)) == value


def _is_canonical_relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or value.startswith("/") or "\x00" in value:
        return False
    if canonical_normalize(value) != value:
        return False
    parts = value.split("/")
    return all(part not in ("", ".", "..") for part in parts) and str(PurePosixPath(value)) == value


def _paths_overlap(left: str, right: str) -> bool:
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


def _identity_issues(identity: Any, expected_type: str, location: str) -> list[Issue]:
    if not isinstance(identity, dict):
        return []
    issues: list[Issue] = []
    if expected_type != "directory" and identity.get("link_count") != 1:
        issues.append(Issue("RECEIPT-LINK-AMBIGUITY", location + "/link_count", "hard-linked or unknown identity is not safe to mutate"))
    target_hash = identity.get("symlink_target_sha256")
    if expected_type == "symlink" and target_hash is None:
        issues.append(Issue("RECEIPT-LINK-AMBIGUITY", location + "/symlink_target_sha256", "symlink identity lacks exact target hash"))
    if expected_type != "symlink" and target_hash is not None:
        issues.append(Issue("RECEIPT-LINK-AMBIGUITY", location + "/symlink_target_sha256", "non-symlink identity claims a symlink target"))
    return issues


def _resource_key(identity: Any) -> tuple[Any, Any, Any] | None:
    if not isinstance(identity, dict):
        return None
    return (identity.get("provider"), identity.get("volume_id"), identity.get("object_id"))


def _resource_overlap(left: Any, right: Any) -> bool:
    left_key = _resource_key(left)
    right_key = _resource_key(right)
    if left_key is None or right_key is None or left_key[:2] != right_key[:2]:
        return False
    left_object = left_key[2]
    right_object = right_key[2]
    return (
        left_object == right_object
        or left_object in right.get("ancestor_object_ids", [])
        or right_object in left.get("ancestor_object_ids", [])
    )


def _resource_descends(target: Any, root: Any) -> bool:
    target_key = _resource_key(target)
    root_key = _resource_key(root)
    if target_key is None or root_key is None or target_key[:2] != root_key[:2]:
        return False
    return target_key[2] != root_key[2] and root_key[2] in target.get("ancestor_object_ids", [])


def _resource_identity_issues(identity: Any, path_hash: Any, location: str) -> list[Issue]:
    if not isinstance(identity, dict):
        return []
    issues: list[Issue] = []
    if identity.get("resolved_path_sha256") != path_hash:
        issues.append(Issue("RECEIPT-RESOURCE-IDENTITY", location + "/resolved_path_sha256", "resolved path hash differs from the canonical path"))
    object_id = identity.get("object_id")
    if object_id in identity.get("ancestor_object_ids", []):
        issues.append(Issue("RECEIPT-RESOURCE-IDENTITY", location, "resource identity contains itself as an ancestor"))
    return issues


def _parent_binding_issues(target: Any, parent: Any, parent_path: str, location: str) -> list[Issue]:
    issues = _resource_identity_issues(parent, hashlib.sha256(parent_path.encode("utf-8")).hexdigest(), location)
    if not _resource_descends(target, parent):
        issues.append(Issue("RECEIPT-PARENT-IDENTITY", location, "declared parent is not a physical ancestor of the target"))
    return issues


def receipt_intent_projection(receipt: dict[str, Any]) -> dict[str, Any]:
    operation = receipt.get("operation", {})
    fields = (
        "receipt_version",
        "installation_id",
        "mode",
        "installer_version",
        "source",
        "protected_paths",
        "roots",
        "entries",
        "config_entries",
        "backups",
        "retention_policies",
        "preservation",
    )
    projection = {field: receipt.get(field) for field in fields}
    projection["operation"] = {
        "operation_id": operation.get("operation_id"),
        "kind": operation.get("kind"),
        "prior_receipt_sha256": operation.get("prior_receipt_sha256"),
    }
    return projection


def journal_entry_projection(entry: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in entry.items() if key != "journal_entry_sha256"}


def refresh_receipt_fixture_integrity(receipt: dict[str, Any]) -> dict[str, Any]:
    """Rebind fixture hashes without repairing deliberately tampered state proofs."""
    operation = receipt["operation"]
    operation["intended_receipt_sha256"] = canonical_sha256(receipt_intent_projection(receipt))
    prior_journal_hash: str | None = None
    for row in operation.get("journal", []):
        row["operation_id"] = operation["operation_id"]
        row["intended_receipt_sha256"] = operation["intended_receipt_sha256"]
        row["prior_receipt_sha256"] = operation.get("prior_receipt_sha256")
        row["precondition_sha256"] = canonical_sha256(row.get("precondition", {}))
        row["postcondition_sha256"] = canonical_sha256(row.get("postcondition", {}))
        row["prior_journal_sha256"] = prior_journal_hash
        row.pop("journal_entry_sha256", None)
        row["journal_entry_sha256"] = canonical_sha256(row)
        prior_journal_hash = row["journal_entry_sha256"]
    return receipt


def _present_state_subject(
    *,
    entry_id: Any,
    subject_kind: str,
    resource_identity: Any,
    identity: Any,
    expected_type: Any,
    ownership_marker_sha256: Any,
    content_sha256: Any,
    selector_state: Any,
    basis: str,
    basis_sha256: str | None = None,
) -> dict[str, Any]:
    identity = identity if isinstance(identity, dict) else {}
    return {
        "entry_id": entry_id,
        "subject_kind": subject_kind,
        "state": "present",
        "basis": basis,
        "basis_sha256": basis_sha256,
        "target_path_sha256": resource_identity.get("resolved_path_sha256") if isinstance(resource_identity, dict) else None,
        "resolved_resource_identity": resource_identity,
        "ancestor_chain_sha256": identity.get("ancestor_chain_sha256"),
        "device": identity.get("device"),
        "inode": identity.get("inode"),
        "link_count": identity.get("link_count"),
        "expected_type": expected_type,
        "observed_type": expected_type,
        "ownership_marker_sha256": ownership_marker_sha256,
        "content_sha256": content_sha256,
        "symlink_target_sha256": identity.get("symlink_target_sha256"),
        "selector_state": selector_state,
        "parent_resource_identity": None,
        "parent_identity": None,
    }


def _absent_state_subject(*, entry_id: Any, subject_kind: str, target_path_sha256: Any, expected_type: Any, parent_resource_identity: Any, parent_identity: Any) -> dict[str, Any]:
    return {
        "entry_id": entry_id,
        "subject_kind": subject_kind,
        "state": "absent",
        "basis": "live_parent",
        "basis_sha256": None,
        "target_path_sha256": target_path_sha256,
        "resolved_resource_identity": None,
        "ancestor_chain_sha256": None,
        "device": None,
        "inode": None,
        "link_count": None,
        "expected_type": expected_type,
        "observed_type": None,
        "ownership_marker_sha256": None,
        "content_sha256": None,
        "symlink_target_sha256": None,
        "selector_state": "absent" if subject_kind == "config" else None,
        "parent_resource_identity": parent_resource_identity,
        "parent_identity": parent_identity,
    }


def entry_present_subject(entry: dict[str, Any], basis: str, basis_sha256: str | None = None) -> dict[str, Any]:
    marker = hashlib.sha256(entry.get("ownership_marker", "").encode("utf-8")).hexdigest()
    return _present_state_subject(
        entry_id=entry.get("entry_id"), subject_kind="entry", resource_identity=entry.get("resource_identity"), identity=entry.get("identity"),
        expected_type=entry.get("expected_type"), ownership_marker_sha256=marker, content_sha256=entry.get("content_sha256"),
        selector_state=None, basis=basis, basis_sha256=basis_sha256,
    )


def entry_absent_subject(entry: dict[str, Any]) -> dict[str, Any]:
    return _absent_state_subject(
        entry_id=entry.get("entry_id"), subject_kind="entry", target_path_sha256=entry.get("resource_identity", {}).get("resolved_path_sha256"),
        expected_type=entry.get("expected_type"), parent_resource_identity=entry.get("parent_resource_identity"), parent_identity=entry.get("parent_identity"),
    )


def config_present_subject(config: dict[str, Any], basis: str, basis_sha256: str | None = None) -> dict[str, Any]:
    marker = hashlib.sha256((config.get("selector", "") + "\n" + config.get("installed_digest", "")).encode("utf-8")).hexdigest()
    return _present_state_subject(
        entry_id=config.get("entry_id"), subject_kind="config", resource_identity=config.get("current_resource_identity"), identity=config.get("current_identity"),
        expected_type="file", ownership_marker_sha256=marker, content_sha256=config.get("installed_digest"), selector_state="present",
        basis=basis, basis_sha256=basis_sha256,
    )


def config_absent_subject(config: dict[str, Any]) -> dict[str, Any]:
    return _absent_state_subject(
        entry_id=config.get("entry_id"), subject_kind="config", target_path_sha256=config.get("current_resource_identity", {}).get("resolved_path_sha256"),
        expected_type="file", parent_resource_identity=config.get("parent_resource_identity"), parent_identity=config.get("parent_identity"),
    )


def backup_original_subject(backup: dict[str, Any], owner: dict[str, Any]) -> dict[str, Any]:
    subject_kind = backup.get("owner_kind")
    if subject_kind == "entry":
        marker = None
        selector_state = None
    else:
        selector_state = owner.get("prior_state")
        marker = None if selector_state == "absent" else hashlib.sha256((owner.get("selector", "") + "\n" + (owner.get("prior_content_sha256") or "")).encode("utf-8")).hexdigest()
    return _present_state_subject(
        entry_id=backup.get("owner_entry_id"), subject_kind=subject_kind, resource_identity=backup.get("original_resource_identity"), identity=backup.get("original_identity"),
        expected_type=backup.get("original_type"), ownership_marker_sha256=marker, content_sha256=backup.get("sha256"), selector_state=selector_state,
        basis="backup_original", basis_sha256=None,
    )


def backup_present_subject(backup: dict[str, Any]) -> dict[str, Any]:
    identity = backup.get("backup_identity", {})
    return {
        "backup_id": backup.get("backup_id"), "state": "present", "basis": "intended_receipt",
        "target_path_sha256": backup.get("backup_resource_identity", {}).get("resolved_path_sha256"),
        "resolved_resource_identity": backup.get("backup_resource_identity"), "ancestor_chain_sha256": identity.get("ancestor_chain_sha256"),
        "device": identity.get("device"), "inode": identity.get("inode"), "link_count": identity.get("link_count"),
        "observed_type": backup.get("original_type"), "content_sha256": backup.get("sha256"),
        "symlink_target_sha256": identity.get("symlink_target_sha256"), "parent_resource_identity": None, "parent_identity": None,
    }


def backup_absent_subject(backup: dict[str, Any]) -> dict[str, Any]:
    return {
        "backup_id": backup.get("backup_id"), "state": "absent", "basis": "live_parent",
        "target_path_sha256": backup.get("backup_resource_identity", {}).get("resolved_path_sha256"),
        "resolved_resource_identity": None, "ancestor_chain_sha256": None, "device": None, "inode": None, "link_count": None,
        "observed_type": None, "content_sha256": None, "symlink_target_sha256": None,
        "parent_resource_identity": backup.get("parent_resource_identity"), "parent_identity": backup.get("parent_identity"),
    }


def backup_precondition_subject(backup: dict[str, Any]) -> dict[str, Any]:
    """Compatibility name used by the standalone restoration fixture."""
    return backup_present_subject(backup)


def lifecycle_phase_issues(
    kind: Any,
    state: Any,
    phases: list[Any],
    *,
    has_backups: bool,
    has_entries: bool,
    has_config: bool,
    keep_data: bool,
    location: str,
) -> list[Issue]:
    issues: list[Issue] = []
    if kind == "uninstall":
        phase_order = ["preflight_complete", "admissions_stopped", "processes_stopped", "user_content_restored", "structured_config_restored", "owned_entry_removed", "retention_receipt_committed", "removal_verified", "ownership_receipt_removed", "cleanup_complete"]
        repeatable_phases = {"user_content_restored", "structured_config_restored", "owned_entry_removed"}
    else:
        phase_order = ["preflight_complete", "backups_durable", "stage_verified", "replacement_applied", "structured_edit_applied", "health_verified", "receipt_committed", "cleanup_complete"]
        repeatable_phases = {"replacement_applied", "structured_edit_applied"}
    phase_rank = {phase: index for index, phase in enumerate(phase_order)}
    if any(phase not in phase_rank for phase in phases) or [phase_rank.get(phase, -1) for phase in phases] != sorted(phase_rank.get(phase, -1) for phase in phases):
        issues.append(Issue("RECEIPT-JOURNAL-ORDER", location, f"non-monotonic or operation-incompatible phases {phases}"))
    for phase in set(phases) - repeatable_phases:
        if phases.count(phase) > 1:
            issues.append(Issue("RECEIPT-JOURNAL-ORDER", location, f"phase {phase} may not repeat"))
    if state == "committed":
        if kind == "uninstall":
            required_phases = {"preflight_complete", "admissions_stopped", "processes_stopped", "removal_verified", "ownership_receipt_removed", "cleanup_complete"}
            if has_backups:
                required_phases.add("user_content_restored")
            if has_config:
                required_phases.add("structured_config_restored")
            if has_entries:
                required_phases.add("owned_entry_removed")
            if keep_data:
                required_phases.add("retention_receipt_committed")
        else:
            required_phases = {"preflight_complete", "stage_verified", "health_verified", "receipt_committed", "cleanup_complete"}
            if has_backups:
                required_phases.add("backups_durable")
            if has_entries:
                required_phases.add("replacement_applied")
            if has_config:
                required_phases.add("structured_edit_applied")
        missing_phases = required_phases - set(phases)
        if missing_phases:
            issues.append(Issue("RECEIPT-JOURNAL", location, f"committed operation lacks phases {sorted(missing_phases)}"))
    return issues


def receipt_semantic_issues(receipt: dict[str, Any], prior_receipt: dict[str, Any] | None = None) -> list[Issue]:
    issues: list[Issue] = []
    root_ids, duplicate = _ids(receipt.get("roots", []), "root_id")
    issues.extend(duplicate)
    entry_ids, duplicate = _ids(receipt.get("entries", []), "entry_id")
    issues.extend(duplicate)
    config_ids, duplicate = _ids(receipt.get("config_entries", []), "entry_id")
    issues.extend(duplicate)
    backup_ids, duplicate = _ids(receipt.get("backups", []), "backup_id")
    issues.extend(duplicate)
    if entry_ids & config_ids:
        issues.append(Issue("RECEIPT-DUPLICATE-ID", "$/config_entries", f"entry IDs overlap {sorted(entry_ids & config_ids)}"))
    all_entry_ids = entry_ids | config_ids

    protected_paths: list[str] = []
    protected_resources: list[dict[str, Any]] = []
    protected_classes: set[str] = set()
    for index, protected in enumerate(receipt.get("protected_paths", [])):
        value = protected.get("canonical_path")
        if not _is_canonical_absolute_path(value):
            issues.append(Issue("RECEIPT-PATH-TRAVERSAL", f"$/protected_paths/{index}/canonical_path", f"non-canonical absolute path {value!r}"))
        elif hashlib.sha256(value.encode("utf-8")).hexdigest() != protected.get("canonical_path_sha256"):
            issues.append(Issue("RECEIPT-PATH-HASH", f"$/protected_paths/{index}/canonical_path_sha256", "path hash does not match canonical path"))
        if value in protected_paths:
            issues.append(Issue("RECEIPT-PATH-ALIAS", f"$/protected_paths/{index}/canonical_path", f"duplicate path {value!r}"))
        protected_paths.append(value)
        resource_identity = protected.get("resource_identity", {})
        issues.extend(_resource_identity_issues(resource_identity, protected.get("canonical_path_sha256"), f"$/protected_paths/{index}/resource_identity"))
        if any(_resource_key(resource_identity) == _resource_key(existing) for existing in protected_resources):
            issues.append(Issue("RECEIPT-RESOURCE-ALIAS", f"$/protected_paths/{index}/resource_identity", "duplicate protected physical identity"))
        protected_resources.append(resource_identity)
        protected_classes.add(protected.get("path_class"))
    if "source_checkout" not in protected_classes:
        issues.append(Issue("RECEIPT-PROTECTED-SOURCE", "$/protected_paths", "source checkout is not protected"))
    source_repository = receipt.get("source", {}).get("repository")
    protected_source_paths = {
        protected.get("canonical_path")
        for protected in receipt.get("protected_paths", [])
        if protected.get("path_class") == "source_checkout"
    }
    if not _is_canonical_absolute_path(source_repository):
        issues.append(Issue("RECEIPT-PATH-TRAVERSAL", "$/source/repository", f"non-canonical absolute path {source_repository!r}"))
    elif source_repository not in protected_source_paths:
        issues.append(Issue("RECEIPT-PROTECTED-SOURCE", "$/protected_paths", "source repository path is not exactly protected"))

    root_paths: list[str] = []
    root_resources: list[dict[str, Any]] = []
    roots_by_id: dict[Any, dict[str, Any]] = {}
    for index, root in enumerate(receipt.get("roots", [])):
        value = root.get("canonical_path")
        if not _is_canonical_absolute_path(value):
            issues.append(Issue("RECEIPT-PATH-TRAVERSAL", f"$/roots/{index}/canonical_path", f"non-canonical absolute path {value!r}"))
        elif hashlib.sha256(value.encode("utf-8")).hexdigest() != root.get("canonical_path_sha256"):
            issues.append(Issue("RECEIPT-PATH-HASH", f"$/roots/{index}/canonical_path_sha256", "path hash does not match canonical path"))
        if any(isinstance(existing, str) and isinstance(value, str) and _paths_overlap(value, existing) for existing in root_paths):
            issues.append(Issue("RECEIPT-ROOT-OVERLAP", f"$/roots/{index}/canonical_path", f"root overlaps another owned root {value!r}"))
        if isinstance(value, str) and any(isinstance(protected, str) and _paths_overlap(value, protected) for protected in protected_paths):
            issues.append(Issue("RECEIPT-PROTECTED-OVERLAP", f"$/roots/{index}/canonical_path", "owned root overlaps a protected path"))
        resource_identity = root.get("resource_identity", {})
        issues.extend(_resource_identity_issues(resource_identity, root.get("canonical_path_sha256"), f"$/roots/{index}/resource_identity"))
        if any(_resource_overlap(resource_identity, protected) for protected in protected_resources):
            issues.append(Issue("RECEIPT-PROTECTED-OVERLAP", f"$/roots/{index}/resource_identity", "owned root physically overlaps a protected resource"))
        if any(_resource_overlap(resource_identity, existing) for existing in root_resources):
            issues.append(Issue("RECEIPT-ROOT-OVERLAP", f"$/roots/{index}/resource_identity", "owned roots physically overlap"))
        issues.extend(_identity_issues(root.get("identity"), "directory", f"$/roots/{index}/identity"))
        root_paths.append(value)
        root_resources.append(resource_identity)
        roots_by_id[root.get("root_id")] = root

    entry_paths: set[tuple[Any, Any]] = set()
    resolved_entry_paths: set[str] = set()
    entry_resources: list[dict[str, Any]] = []
    resolved_entry_path_by_id: dict[Any, str] = {}
    entries_by_id = {entry.get("entry_id"): entry for entry in receipt.get("entries", [])}
    configs_by_id = {entry.get("entry_id"): entry for entry in receipt.get("config_entries", [])}
    backup_references: dict[Any, list[tuple[str, Any]]] = {}
    for index, entry in enumerate(receipt.get("entries", [])):
        relative = entry.get("relative_path", "")
        if not _is_canonical_relative_path(relative):
            issues.append(Issue("RECEIPT-PATH-TRAVERSAL", f"$/entries/{index}/relative_path", f"unsafe or aliased relative path {relative!r}"))
        entry_path = (entry.get("root_id"), relative)
        if entry_path in entry_paths:
            issues.append(Issue("RECEIPT-PATH-ALIAS", f"$/entries/{index}/relative_path", f"duplicate owned path {entry_path}"))
        entry_paths.add(entry_path)
        if entry.get("root_id") not in root_ids:
            issues.append(Issue("RECEIPT-ROOT", f"$/entries/{index}/root_id", "unknown receipt root"))
        root_path = roots_by_id.get(entry.get("root_id"), {}).get("canonical_path")
        if isinstance(root_path, str) and _is_canonical_relative_path(relative):
            resolved_path = root_path + "/" + relative
            if resolved_path in resolved_entry_paths:
                issues.append(Issue("RECEIPT-PATH-ALIAS", f"$/entries/{index}/relative_path", f"duplicate resolved target {resolved_path}"))
            resolved_entry_paths.add(resolved_path)
            resolved_entry_path_by_id[entry.get("entry_id")] = resolved_path
            resolved_hash = hashlib.sha256(resolved_path.encode("utf-8")).hexdigest()
            resource_identity = entry.get("resource_identity", {})
            issues.extend(_resource_identity_issues(resource_identity, resolved_hash, f"$/entries/{index}/resource_identity"))
            root_resource = roots_by_id.get(entry.get("root_id"), {}).get("resource_identity", {})
            if not _resource_descends(resource_identity, root_resource):
                issues.append(Issue("RECEIPT-RESOURCE-ROOT", f"$/entries/{index}/resource_identity", "entry target is not physically descended from its declared root"))
            issues.extend(_parent_binding_issues(
                resource_identity,
                entry.get("parent_resource_identity", {}),
                str(PurePosixPath(resolved_path).parent),
                f"$/entries/{index}/parent_resource_identity",
            ))
            if any(_resource_overlap(resource_identity, protected) for protected in protected_resources):
                issues.append(Issue("RECEIPT-PROTECTED-OVERLAP", f"$/entries/{index}/resource_identity", "owned entry physically overlaps a protected resource"))
            if any(_resource_key(resource_identity) == _resource_key(existing) for existing in entry_resources):
                issues.append(Issue("RECEIPT-RESOURCE-ALIAS", f"$/entries/{index}/resource_identity", "multiple owned entries resolve to the same physical object"))
            entry_resources.append(resource_identity)
        referenced_backups = entry.get("backup_ids", [])
        unknown_backups = set(referenced_backups) - backup_ids
        if unknown_backups:
            issues.append(Issue("RECEIPT-BACKUP", f"$/entries/{index}/backup_ids", f"unknown backups {sorted(unknown_backups)}"))
        for backup in referenced_backups:
            backup_references.setdefault(backup, []).append(("entry", entry.get("entry_id")))
        issues.extend(_identity_issues(entry.get("identity"), entry.get("expected_type"), f"$/entries/{index}/identity"))
        issues.extend(_identity_issues(entry.get("parent_identity"), "directory", f"$/entries/{index}/parent_identity"))

    config_resources: list[dict[str, Any]] = []
    for index, config in enumerate(receipt.get("config_entries", [])):
        value = config.get("config_path")
        if not _is_canonical_absolute_path(value):
            issues.append(Issue("RECEIPT-PATH-TRAVERSAL", f"$/config_entries/{index}/config_path", f"non-canonical absolute path {value!r}"))
        value_hash = hashlib.sha256(value.encode("utf-8")).hexdigest() if isinstance(value, str) else None
        current_resource = config.get("current_resource_identity", {})
        issues.extend(_resource_identity_issues(current_resource, value_hash, f"$/config_entries/{index}/current_resource_identity"))
        if isinstance(value, str) and _is_canonical_absolute_path(value):
            issues.extend(_parent_binding_issues(
                current_resource,
                config.get("parent_resource_identity", {}),
                str(PurePosixPath(value).parent),
                f"$/config_entries/{index}/parent_resource_identity",
            ))
        if any(_resource_overlap(current_resource, protected) for protected in protected_resources):
            issues.append(Issue("RECEIPT-PROTECTED-OVERLAP", f"$/config_entries/{index}/current_resource_identity", "configuration target physically overlaps a protected resource"))
        if any(_resource_key(current_resource) == _resource_key(existing) for existing in entry_resources):
            issues.append(Issue("RECEIPT-RESOURCE-ALIAS", f"$/config_entries/{index}/current_resource_identity", "configuration and owned entry resolve to the same physical object"))
        config_resources.append(current_resource)
        issues.extend(_identity_issues(config.get("current_identity"), "file", f"$/config_entries/{index}/current_identity"))
        prior_state = config.get("prior_state")
        prior_file_state = config.get("prior_file_state")
        referenced_backups = config.get("prior_backup_ids", [])
        prior_hash = config.get("prior_content_sha256")
        prior_identity = config.get("prior_identity")
        prior_resource = config.get("prior_resource_identity")
        unknown_backups = set(referenced_backups) - backup_ids
        if unknown_backups:
            issues.append(Issue("RECEIPT-CONFIG-PRIOR", f"$/config_entries/{index}/prior_backup_ids", f"unknown backups {sorted(unknown_backups)}"))
        if prior_file_state == "present" and (prior_hash is None or prior_identity is None or prior_resource is None or not referenced_backups):
            issues.append(Issue("RECEIPT-CONFIG-PRIOR", f"$/config_entries/{index}", "present prior file requires digest, physical identity, and backup"))
        if prior_file_state == "absent" and any(value is not None for value in (prior_hash, prior_identity, prior_resource)):
            issues.append(Issue("RECEIPT-CONFIG-PRIOR", f"$/config_entries/{index}", "absent prior file cannot claim digest or target identity"))
        if prior_state == "present" and prior_file_state != "present":
            issues.append(Issue("RECEIPT-CONFIG-PRIOR", f"$/config_entries/{index}", "present prior selector requires a present prior file"))
        if prior_file_state == "present":
            issues.extend(_identity_issues(prior_identity, "file", f"$/config_entries/{index}/prior_identity"))
            expected_prior_hash = hashlib.sha256(value.encode("utf-8")).hexdigest() if isinstance(value, str) else None
            issues.extend(_resource_identity_issues(prior_resource, expected_prior_hash, f"$/config_entries/{index}/prior_resource_identity"))
            if isinstance(value, str) and _is_canonical_absolute_path(value) and not _resource_descends(prior_resource, config.get("parent_resource_identity", {})):
                issues.append(Issue("RECEIPT-PARENT-IDENTITY", f"$/config_entries/{index}/prior_resource_identity", "prior configuration target is not descended from the declared parent"))
        issues.extend(_identity_issues(config.get("parent_identity"), "directory", f"$/config_entries/{index}/parent_identity"))
        for backup in referenced_backups:
            backup_references.setdefault(backup, []).append(("config", config.get("entry_id")))

    backup_resources: list[dict[str, Any]] = []
    for index, backup in enumerate(receipt.get("backups", [])):
        for field in ("original_path", "backup_path"):
            value = backup.get(field)
            if not _is_canonical_absolute_path(value):
                issues.append(Issue("RECEIPT-PATH-TRAVERSAL", f"$/backups/{index}/{field}", f"non-canonical absolute path {value!r}"))
        backup_root = roots_by_id.get(backup.get("backup_root_id"))
        backup_relative = backup.get("backup_relative_path")
        if backup_root is None:
            issues.append(Issue("RECEIPT-ROOT", f"$/backups/{index}/backup_root_id", "unknown backup root"))
        elif not _is_canonical_relative_path(backup_relative) or backup.get("backup_path") != backup_root.get("canonical_path") + "/" + backup_relative:
            issues.append(Issue("RECEIPT-BACKUP", f"$/backups/{index}/backup_path", "backup path is not anchored to its approved root"))
        backup_path = backup.get("backup_path")
        backup_path_hash = hashlib.sha256(backup_path.encode("utf-8")).hexdigest() if isinstance(backup_path, str) else None
        backup_resource = backup.get("backup_resource_identity", {})
        issues.extend(_resource_identity_issues(backup_resource, backup_path_hash, f"$/backups/{index}/backup_resource_identity"))
        if isinstance(backup_path, str) and _is_canonical_absolute_path(backup_path):
            issues.extend(_parent_binding_issues(
                backup_resource,
                backup.get("parent_resource_identity", {}),
                str(PurePosixPath(backup_path).parent),
                f"$/backups/{index}/parent_resource_identity",
            ))
        if backup_root is not None and not _resource_descends(backup_resource, backup_root.get("resource_identity", {})):
            issues.append(Issue("RECEIPT-RESOURCE-ROOT", f"$/backups/{index}/backup_resource_identity", "backup target is not physically descended from its approved root"))
        if any(_resource_overlap(backup_resource, protected) for protected in protected_resources):
            issues.append(Issue("RECEIPT-PROTECTED-OVERLAP", f"$/backups/{index}/backup_resource_identity", "backup physically overlaps a protected resource"))
        if any(_resource_overlap(backup_resource, target) for target in entry_resources + config_resources + backup_resources):
            issues.append(Issue("RECEIPT-RESOURCE-ALIAS", f"$/backups/{index}/backup_resource_identity", "backup storage overlaps another receipt target"))
        backup_resources.append(backup_resource)
        issues.extend(_identity_issues(backup.get("parent_identity"), "directory", f"$/backups/{index}/parent_identity"))
        original_path = backup.get("original_path")
        original_path_hash = hashlib.sha256(original_path.encode("utf-8")).hexdigest() if isinstance(original_path, str) else None
        original_resource = backup.get("original_resource_identity", {})
        issues.extend(_resource_identity_issues(original_resource, original_path_hash, f"$/backups/{index}/original_resource_identity"))
        if any(isinstance(protected, str) and isinstance(original_path, str) and _paths_overlap(original_path, protected) for protected in protected_paths) or any(_resource_overlap(original_resource, protected) for protected in protected_resources):
            issues.append(Issue("RECEIPT-PROTECTED-OVERLAP", f"$/backups/{index}/original_path", "backup restoration destination overlaps a protected resource"))
        owner_kind = backup.get("owner_kind")
        owner_id = backup.get("owner_entry_id")
        if owner_kind == "entry":
            owner = entries_by_id.get(owner_id)
            expected_original_path = resolved_entry_path_by_id.get(owner_id)
            expected_original_type = owner.get("expected_type") if owner else None
        elif owner_kind == "config":
            owner = configs_by_id.get(owner_id)
            expected_original_path = owner.get("config_path") if owner else None
            expected_original_type = "file" if owner else None
        else:
            owner = None
            expected_original_path = None
            expected_original_type = None
        references = backup_references.get(backup.get("backup_id"), [])
        if owner is None or references != [(owner_kind, owner_id)] or original_path != expected_original_path or backup.get("original_type") != expected_original_type:
            issues.append(Issue("RECEIPT-BACKUP-BINDING", f"$/backups/{index}", "backup is not uniquely bound to its exact owner and restoration path"))
        if owner is not None and not _resource_descends(original_resource, owner.get("parent_resource_identity", {})):
            issues.append(Issue("RECEIPT-PARENT-IDENTITY", f"$/backups/{index}/original_resource_identity", "backup restoration target is not descended from its owner's declared parent"))
        purpose = backup.get("purpose")
        if (purpose == "displaced_user" and owner_kind != "entry") or (purpose == "config_prior" and owner_kind != "config"):
            issues.append(Issue("RECEIPT-BACKUP-BINDING", f"$/backups/{index}/purpose", "backup purpose is incompatible with its owner kind"))
        issues.extend(_identity_issues(backup.get("original_identity"), backup.get("original_type"), f"$/backups/{index}/original_identity"))
        issues.extend(_identity_issues(backup.get("backup_identity"), backup.get("original_type"), f"$/backups/{index}/backup_identity"))

    unbound_backups = set(backup_references) - backup_ids
    if unbound_backups:
        issues.append(Issue("RECEIPT-BACKUP-BINDING", "$/backups", f"references name missing backups {sorted(unbound_backups)}"))
    backups_by_id = {backup.get("backup_id"): backup for backup in receipt.get("backups", [])}
    for index, entry in enumerate(receipt.get("entries", [])):
        displaced = [
            backup_id for backup_id in entry.get("backup_ids", [])
            if backups_by_id.get(backup_id, {}).get("purpose") == "displaced_user"
        ]
        expected_displaced = 1 if entry.get("entry_class") == "replaced" else 0
        if len(displaced) != expected_displaced:
            code = "RECEIPT-BACKUP" if expected_displaced == 1 and not displaced else "RECEIPT-BACKUP-CARDINALITY"
            issues.append(Issue(code, f"$/entries/{index}/backup_ids", f"expected {expected_displaced} displaced-user backup, got {len(displaced)}"))
    for index, config in enumerate(receipt.get("config_entries", [])):
        prior_backups = [
            backup_id for backup_id in config.get("prior_backup_ids", [])
            if backups_by_id.get(backup_id, {}).get("purpose") == "config_prior"
        ]
        expected_prior_backups = 1 if config.get("prior_file_state") == "present" else 0
        if len(prior_backups) != expected_prior_backups:
            code = "RECEIPT-CONFIG-PRIOR" if expected_prior_backups == 1 and not prior_backups else "RECEIPT-BACKUP-CARDINALITY"
            issues.append(Issue(code, f"$/config_entries/{index}/prior_backup_ids", f"expected {expected_prior_backups} config-prior backup, got {len(prior_backups)}"))

    required_preservation = {"run_history", "current_run_recovery", "promoted_overlay", "retention_settings", "backups"}
    actual_preservation = set(receipt.get("preservation", {}).get("preserve_on_update", []))
    if actual_preservation != required_preservation:
        issues.append(Issue("RECEIPT-PRESERVATION", "$/preservation/preserve_on_update", f"expected {sorted(required_preservation)}, got {sorted(actual_preservation)}"))

    policies = receipt.get("retention_policies", [])
    policy_ids, duplicate = _ids(policies, "policy_id")
    issues.extend(duplicate)
    policies_by_class: dict[Any, dict[str, Any]] = {}
    for index, policy in enumerate(policies):
        retention_class = policy.get("retention_class")
        if retention_class in policies_by_class:
            issues.append(Issue("RECEIPT-RETENTION", f"$/retention_policies/{index}", f"duplicate policy for {retention_class}"))
        policies_by_class[retention_class] = policy
        if policy.get("disposition") == "expire_at" and policy.get("expires_at") is None:
            issues.append(Issue("RECEIPT-RETENTION", f"$/retention_policies/{index}/expires_at", "expire_at policy requires a timestamp"))
    entry_classes = {entry.get("retention_class") for entry in receipt.get("entries", [])}
    if not entry_classes.issubset(policies_by_class):
        issues.append(Issue("RECEIPT-RETENTION", "$/retention_policies", f"missing classes {sorted(entry_classes - set(policies_by_class))}"))
    preservation = receipt.get("preservation", {})
    retained_ids = set(preservation.get("keep_data_entry_ids", []))
    unknown_retained = retained_ids - entry_ids
    if unknown_retained:
        issues.append(Issue("RECEIPT-RETENTION", "$/preservation/keep_data_entry_ids", f"unknown retained entries {sorted(unknown_retained)}"))
    eligible_retained = {
        entry.get("entry_id")
        for entry in receipt.get("entries", [])
        if policies_by_class.get(entry.get("retention_class"), {}).get("disposition") == "retain_on_keep_data"
    }
    if preservation.get("keep_data"):
        if retained_ids != eligible_retained or not preservation.get("retention_receipt_id"):
            issues.append(Issue("RECEIPT-RETENTION", "$/preservation", "keep-data requires the exact eligible entry set and a retention receipt"))
    elif retained_ids or preservation.get("retention_receipt_id") is not None:
        issues.append(Issue("RECEIPT-RETENTION", "$/preservation", "non-keep-data receipt cannot retain entries or name a retention receipt"))

    operation = receipt.get("operation", {})
    operation_kind = operation.get("kind")
    intended = canonical_sha256(receipt_intent_projection(receipt))
    if operation.get("intended_receipt_sha256") != intended:
        issues.append(Issue("RECEIPT-INTENT-HASH", "$/operation/intended_receipt_sha256", f"expected {intended}"))

    prior_entries_by_id: dict[Any, dict[str, Any]] = {}
    prior_configs_by_id: dict[Any, dict[str, Any]] = {}
    prior_backups_by_id: dict[Any, dict[str, Any]] = {}
    prior_digest: str | None = None
    if operation_kind == "install":
        if operation.get("prior_receipt_sha256") is not None or prior_receipt is not None:
            issues.append(Issue("RECEIPT-PRIOR", "$/operation/prior_receipt_sha256", "fresh install must not bind a prior receipt"))
    elif prior_receipt is None:
        issues.append(Issue("RECEIPT-PRIOR", "$/operation/prior_receipt_sha256", "update and uninstall require the externally resolved prior receipt"))
    else:
        prior_digest = canonical_sha256(prior_receipt)
        if operation.get("prior_receipt_sha256") != prior_digest or prior_receipt.get("installation_id") != receipt.get("installation_id"):
            issues.append(Issue("RECEIPT-PRIOR", "$/operation/prior_receipt_sha256", "prior receipt digest or installation identity does not match"))
        prior_entries_by_id = {entry.get("entry_id"): entry for entry in prior_receipt.get("entries", [])}
        prior_configs_by_id = {entry.get("entry_id"): entry for entry in prior_receipt.get("config_entries", [])}
        prior_backups_by_id = {backup.get("backup_id"): backup for backup in prior_receipt.get("backups", [])}

        current_backup_ids = set(backups_by_id)
        inherited_ids = set(prior_backups_by_id)
        missing_inherited = inherited_ids - current_backup_ids
        unexpected_uninstall = current_backup_ids - inherited_ids if operation_kind == "uninstall" else set()
        if missing_inherited or unexpected_uninstall:
            issues.append(Issue("RECEIPT-PRIOR-BACKUP", "$/backups", f"missing inherited backups {sorted(missing_inherited, key=repr)}; unexpected uninstall backups {sorted(unexpected_uninstall, key=repr)}"))
        for backup_id in inherited_ids & current_backup_ids:
            prior_backup = prior_backups_by_id[backup_id]
            current_backup = backups_by_id[backup_id]
            prior_projection = {key: value for key, value in prior_backup.items() if key != "restored"}
            current_projection = {key: value for key, value in current_backup.items() if key != "restored"}
            restored_transition_ok = (
                operation_kind == "uninstall"
                and prior_backup.get("purpose") in {"displaced_user", "config_prior"}
                and prior_backup.get("restored") is False
                and current_backup.get("restored") is True
            )
            if prior_projection != current_projection or (
                current_backup.get("restored") != prior_backup.get("restored") and not restored_transition_ok
            ):
                issues.append(Issue("RECEIPT-PRIOR-BACKUP", f"$/backups/{backup_id}", "inherited backup differs from the externally bound prior receipt"))

    def target_state(entry: dict[str, Any], kind: str) -> bytes:
        if kind == "entry":
            identity = entry.get("identity", {})
            projection = {
                "resource_identity": entry.get("resource_identity"), "device": identity.get("device"), "inode": identity.get("inode"),
                "link_count": identity.get("link_count"), "ancestor_chain_sha256": identity.get("ancestor_chain_sha256"),
                "symlink_target_sha256": identity.get("symlink_target_sha256"), "expected_type": entry.get("expected_type"),
                "ownership_marker": entry.get("ownership_marker"), "content_sha256": entry.get("content_sha256"),
            }
        else:
            identity = entry.get("current_identity", {})
            projection = {
                "resource_identity": entry.get("current_resource_identity"), "device": identity.get("device"), "inode": identity.get("inode"),
                "link_count": identity.get("link_count"), "ancestor_chain_sha256": identity.get("ancestor_chain_sha256"),
                "symlink_target_sha256": identity.get("symlink_target_sha256"), "selector": entry.get("selector"),
                "installed_digest": entry.get("installed_digest"),
            }
        return canonical_json_bytes(projection)

    prior_entry_ids = set(prior_entries_by_id)
    prior_config_ids = set(prior_configs_by_id)
    prior_backup_ids = set(prior_backups_by_id)
    if operation_kind == "update":
        if prior_entry_ids - entry_ids or prior_config_ids - config_ids:
            issues.append(Issue("RECEIPT-UPDATE-REMOVAL", "$", "receipt v1 update cannot silently drop a prior entry or config target"))
        changed_entries = {
            entry_id for entry_id in entry_ids
            if entry_id not in prior_entries_by_id or target_state(entries_by_id[entry_id], "entry") != target_state(prior_entries_by_id[entry_id], "entry")
        }
        changed_configs = {
            entry_id for entry_id in config_ids
            if entry_id not in prior_configs_by_id or target_state(configs_by_id[entry_id], "config") != target_state(prior_configs_by_id[entry_id], "config")
        }
        durable_backup_ids = backup_ids - prior_backup_ids
        expected_rollback_owners = ({("entry", key) for key in changed_entries & prior_entry_ids}
                                    | {("config", key) for key in changed_configs & prior_config_ids})
        actual_rollback_owner_list = [
            (backups_by_id[key].get("owner_kind"), backups_by_id[key].get("owner_entry_id"))
            for key in durable_backup_ids
            if backups_by_id.get(key, {}).get("purpose") == "operation_rollback"
        ]
        actual_rollback_owners = set(actual_rollback_owner_list)
        if actual_rollback_owners != expected_rollback_owners or len(actual_rollback_owner_list) != len(expected_rollback_owners):
            expected_labels = sorted(f"{kind}:{owner}" for kind, owner in expected_rollback_owners)
            actual_labels = sorted(f"{kind}:{owner}" for kind, owner in actual_rollback_owners)
            issues.append(Issue("RECEIPT-ROLLBACK-BACKUP", "$/backups", f"expected rollback owners {expected_labels}, got {actual_labels}"))
        for backup_id in durable_backup_ids:
            backup = backups_by_id.get(backup_id, {})
            if backup.get("purpose") != "operation_rollback":
                continue
            owner_kind = backup.get("owner_kind")
            owner_id = backup.get("owner_entry_id")
            if owner_kind == "entry":
                prior_owner = prior_entries_by_id.get(owner_id)
                expected_digest = prior_owner.get("content_sha256") if prior_owner else None
                expected_resource = prior_owner.get("resource_identity") if prior_owner else None
                expected_identity = prior_owner.get("identity") if prior_owner else None
            else:
                prior_owner = prior_configs_by_id.get(owner_id)
                expected_digest = prior_owner.get("installed_digest") if prior_owner else None
                expected_resource = prior_owner.get("current_resource_identity") if prior_owner else None
                expected_identity = prior_owner.get("current_identity") if prior_owner else None
            if (
                prior_owner is None
                or expected_digest is None
                or backup.get("sha256") != expected_digest
                or backup.get("original_resource_identity") != expected_resource
                or backup.get("original_identity") != expected_identity
            ):
                issues.append(Issue("RECEIPT-ROLLBACK-BACKUP", f"$/backups/{backup_id}", "rollback backup does not exactly bind the prior committed target state"))
    elif operation_kind == "install":
        changed_entries = set(entry_ids)
        changed_configs = set(config_ids)
        durable_backup_ids = set(backup_ids)
    else:
        changed_entries = set()
        changed_configs = set()
        durable_backup_ids = set()
        if prior_receipt is not None and (
            entry_ids != prior_entry_ids or config_ids != prior_config_ids
            or any(target_state(entries_by_id[key], "entry") != target_state(prior_entries_by_id[key], "entry") for key in entry_ids & prior_entry_ids)
            or any(target_state(configs_by_id[key], "config") != target_state(prior_configs_by_id[key], "config") for key in config_ids & prior_config_ids)
        ):
            issues.append(Issue("RECEIPT-PRIOR", "$", "uninstall target state differs from its bound prior receipt"))

    displaced_entry_ids = {
        backup.get("owner_entry_id") for backup in receipt.get("backups", [])
        if backup.get("purpose") == "displaced_user"
    }
    removable_entry_ids = entry_ids - retained_ids - displaced_entry_ids
    restoration_backup_ids = {
        backup.get("backup_id") for backup in receipt.get("backups", [])
        if backup.get("purpose") in {"displaced_user", "config_prior"}
    }

    def owners_for(backup_set: set[Any]) -> tuple[set[Any], set[Any]]:
        return (
            {backups_by_id[key].get("owner_entry_id") for key in backup_set if backups_by_id.get(key, {}).get("owner_kind") == "entry"},
            {backups_by_id[key].get("owner_entry_id") for key in backup_set if backups_by_id.get(key, {}).get("owner_kind") == "config"},
        )

    durable_entry_ids, durable_config_ids = owners_for(durable_backup_ids)
    if operation_kind == "uninstall":
        coverage = {
            "user_content_restored": (displaced_entry_ids, set(), {key for key in restoration_backup_ids if backups_by_id.get(key, {}).get("purpose") == "displaced_user"}),
            "structured_config_restored": (set(), config_ids, {key for key in restoration_backup_ids if backups_by_id.get(key, {}).get("purpose") == "config_prior"}),
            "owned_entry_removed": (removable_entry_ids, set(), set()),
            "cleanup_complete": (set(), set(), backup_ids),
        }
    else:
        coverage = {
            "backups_durable": (durable_entry_ids, durable_config_ids, durable_backup_ids),
            "replacement_applied": (changed_entries, set(), set()),
            "structured_edit_applied": (set(), changed_configs, set()),
        }

    journal_rows = operation.get("journal", [])
    sequences = [entry.get("sequence") for entry in journal_rows]
    if sequences != list(range(1, len(sequences) + 1)):
        issues.append(Issue("RECEIPT-JOURNAL", "$/operation/journal", f"non-contiguous sequence {sequences}"))
    phases = [entry.get("phase") for entry in journal_rows]
    issues.extend(lifecycle_phase_issues(
        operation_kind, operation.get("state"), phases,
        has_backups=bool(displaced_entry_ids) if operation_kind == "uninstall" else bool(durable_backup_ids),
        has_entries=bool(removable_entry_ids) if operation_kind == "uninstall" else bool(changed_entries),
        has_config=bool(config_ids) if operation_kind == "uninstall" else bool(changed_configs),
        keep_data=receipt.get("preservation", {}).get("keep_data") is True,
        location="$/operation/journal",
    ))

    if operation.get("state") == "committed":
        for phase, (expected_entries, expected_configs, expected_backups) in coverage.items():
            phase_rows = [row for row in journal_rows if row.get("phase") == phase]
            actual_entries = {value for row in phase_rows for value in row.get("entry_ids", [])}
            actual_configs = {value for row in phase_rows for value in row.get("config_entry_ids", [])}
            actual_backups = {value for row in phase_rows for value in row.get("backup_ids", [])}
            expected_any = bool(expected_entries or expected_configs or expected_backups)
            empty_proxy = any(not (row.get("entry_ids") or row.get("config_entry_ids") or row.get("backup_ids")) for row in phase_rows)
            if (actual_entries, actual_configs, actual_backups) != (expected_entries, expected_configs, expected_backups) or empty_proxy or (not expected_any and phase_rows):
                issues.append(Issue("RECEIPT-OPERATION-COVERAGE", "$/operation/journal", f"{phase} coverage differs from the exact expected entry/config/backup sets"))
        if operation_kind == "uninstall":
            unrestored = {key for key in restoration_backup_ids if backups_by_id.get(key, {}).get("restored") is not True}
            wrongly_removed = displaced_entry_ids & removable_entry_ids
            if unrestored or wrongly_removed:
                issues.append(Issue("RECEIPT-OPERATION-COVERAGE", "$/backups", f"unrestored backups {sorted(unrestored)} or restored owners also removed {sorted(wrongly_removed)}"))

    def unique_owner_backup(collection: Iterable[dict[str, Any]], owner_kind: str, owner_id: Any, purposes: set[str]) -> dict[str, Any] | None:
        matches = [backup for backup in collection if backup.get("owner_kind") == owner_kind and backup.get("owner_entry_id") == owner_id and backup.get("purpose") in purposes]
        return matches[0] if len(matches) == 1 else None

    def owner_backup(owner_kind: str, owner_id: Any, purposes: set[str]) -> dict[str, Any] | None:
        return unique_owner_backup(receipt.get("backups", []), owner_kind, owner_id, purposes)

    def prior_owner_backup(owner_kind: str, owner_id: Any, purposes: set[str]) -> dict[str, Any] | None:
        return unique_owner_backup(prior_backups_by_id.values(), owner_kind, owner_id, purposes)

    def proof_backup(backup_id: Any) -> dict[str, Any] | None:
        if operation_kind == "uninstall":
            return prior_backups_by_id.get(backup_id)
        return backups_by_id.get(backup_id)

    def prior_entry_subject(entry_id: Any) -> dict[str, Any] | None:
        entry = prior_entries_by_id.get(entry_id)
        return entry_present_subject(entry, "prior_receipt", prior_digest) if entry else None

    def prior_config_subject(entry_id: Any) -> dict[str, Any] | None:
        config = prior_configs_by_id.get(entry_id)
        return config_present_subject(config, "prior_receipt", prior_digest) if config else None

    def expected_proofs(journal: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        phase = journal.get("phase")
        row_entries = journal.get("entry_ids", [])
        row_configs = journal.get("config_entry_ids", [])
        row_backups = journal.get("backup_ids", [])
        pre_subjects: list[dict[str, Any]] = []
        post_subjects: list[dict[str, Any]] = []
        pre_backups: list[dict[str, Any]] = []
        post_backups: list[dict[str, Any]] = []
        if operation_kind in {"install", "update"} and phase == "backups_durable":
            for entry_id in row_entries:
                backup = next((backups_by_id[key] for key in row_backups if backups_by_id.get(key, {}).get("owner_kind") == "entry" and backups_by_id[key].get("owner_entry_id") == entry_id), None)
                subject = prior_entry_subject(entry_id) if operation_kind == "update" else backup_original_subject(backup, entries_by_id.get(entry_id, {})) if backup else None
                if subject:
                    pre_subjects.append(subject); post_subjects.append(subject)
            for entry_id in row_configs:
                backup = next((backups_by_id[key] for key in row_backups if backups_by_id.get(key, {}).get("owner_kind") == "config" and backups_by_id[key].get("owner_entry_id") == entry_id), None)
                subject = prior_config_subject(entry_id) if operation_kind == "update" else backup_original_subject(backup, configs_by_id.get(entry_id, {})) if backup else None
                if subject:
                    pre_subjects.append(subject); post_subjects.append(subject)
            pre_backups = [backup_absent_subject(backups_by_id[key]) for key in row_backups if key in backups_by_id]
            post_backups = [backup_present_subject(backups_by_id[key]) for key in row_backups if key in backups_by_id]
        elif operation_kind in {"install", "update"} and phase == "replacement_applied":
            for entry_id in row_entries:
                current = entries_by_id.get(entry_id)
                if current is None:
                    continue
                displaced = owner_backup("entry", entry_id, {"displaced_user"})
                before = prior_entry_subject(entry_id) if operation_kind == "update" and entry_id in prior_entries_by_id else backup_original_subject(displaced, current) if displaced else entry_absent_subject(current)
                pre_subjects.append(before); post_subjects.append(entry_present_subject(current, "intended_receipt"))
        elif operation_kind in {"install", "update"} and phase == "structured_edit_applied":
            for entry_id in row_configs:
                current = configs_by_id.get(entry_id)
                if current is None:
                    continue
                prior_backup = owner_backup("config", entry_id, {"config_prior"})
                before = prior_config_subject(entry_id) if operation_kind == "update" and entry_id in prior_configs_by_id else backup_original_subject(prior_backup, current) if prior_backup else config_absent_subject(current)
                pre_subjects.append(before); post_subjects.append(config_present_subject(current, "intended_receipt"))
        elif operation_kind == "uninstall" and phase == "user_content_restored":
            for entry_id in row_entries:
                backup = prior_owner_backup("entry", entry_id, {"displaced_user"})
                before = prior_entry_subject(entry_id)
                if before: pre_subjects.append(before)
                if backup: post_subjects.append(backup_original_subject(backup, entries_by_id.get(entry_id, {})))
            pre_backups = post_backups = [backup_present_subject(backup) for key in row_backups if (backup := proof_backup(key)) is not None]
        elif operation_kind == "uninstall" and phase == "structured_config_restored":
            for entry_id in row_configs:
                backup = prior_owner_backup("config", entry_id, {"config_prior"})
                before = prior_config_subject(entry_id)
                if before: pre_subjects.append(before)
                if backup: post_subjects.append(backup_original_subject(backup, configs_by_id.get(entry_id, {})))
                elif entry_id in configs_by_id: post_subjects.append(config_absent_subject(configs_by_id[entry_id]))
            pre_backups = post_backups = [backup_present_subject(backup) for key in row_backups if (backup := proof_backup(key)) is not None]
        elif operation_kind == "uninstall" and phase == "owned_entry_removed":
            for entry_id in row_entries:
                before = prior_entry_subject(entry_id)
                if before: pre_subjects.append(before)
                if entry_id in entries_by_id: post_subjects.append(entry_absent_subject(entries_by_id[entry_id]))
        elif operation_kind == "uninstall" and phase == "cleanup_complete":
            pre_backups = [backup_present_subject(backup) for key in row_backups if (backup := proof_backup(key)) is not None]
            post_backups = [backup_absent_subject(backup) for key in row_backups if (backup := proof_backup(key)) is not None]
        return pre_subjects, pre_backups, post_subjects, post_backups

    def proof_issues(proof: Any, expected_subjects: list[dict[str, Any]], expected_backups: list[dict[str, Any]], journal: dict[str, Any], code: str, location: str) -> list[Issue]:
        found: list[Issue] = []
        if not isinstance(proof, dict):
            return [Issue(code, location, "state proof is not an object")]
        subject_rows = proof.get("subjects", [])
        backup_rows = proof.get("backup_subjects", [])
        if not isinstance(subject_rows, list) or not all(isinstance(subject, dict) for subject in subject_rows) or not isinstance(backup_rows, list) or not all(isinstance(subject, dict) for subject in backup_rows):
            return [Issue(code, location, "state proof subjects are not typed object arrays")]
        actual_subjects = {(subject.get("subject_kind"), subject.get("entry_id")): subject for subject in subject_rows}
        wanted_subjects = {(subject.get("subject_kind"), subject.get("entry_id")): subject for subject in expected_subjects}
        actual_backups = {subject.get("backup_id"): subject for subject in backup_rows}
        wanted_backups = {subject.get("backup_id"): subject for subject in expected_backups}
        if proof.get("operation_id") != operation.get("operation_id") or actual_subjects != wanted_subjects or actual_backups != wanted_backups or len(actual_subjects) != len(subject_rows) or len(actual_backups) != len(backup_rows):
            found.append(Issue(code, location, "state proof does not match the exact phase-specific prior/post state"))
        try:
            if parse_timestamp(proof.get("observed_at", "")) > parse_timestamp(journal.get("recorded_at", "")):
                found.append(Issue(code, location + "/observed_at", "state proof was observed after the journal row"))
        except (TypeError, ValueError):
            pass
        return found

    prior_time: dt.datetime | None = None
    prior_postcondition_time: dt.datetime | None = None
    prior_journal_hash: str | None = None
    valid_entry_refs = entry_ids | prior_entry_ids
    valid_config_refs = config_ids | prior_config_ids
    valid_backup_refs = backup_ids | prior_backup_ids
    for index, journal in enumerate(journal_rows):
        missing_entries = set(journal.get("entry_ids", [])) - valid_entry_refs
        missing_configs = set(journal.get("config_entry_ids", [])) - valid_config_refs
        missing_backups = set(journal.get("backup_ids", [])) - valid_backup_refs
        if missing_entries or missing_configs or missing_backups:
            issues.append(Issue("RECEIPT-JOURNAL", f"$/operation/journal/{index}", f"unknown entry/config/backup ids {sorted(missing_entries)}, {sorted(missing_configs)}, {sorted(missing_backups)}"))
        expected_binding = (operation.get("operation_id"), operation.get("intended_receipt_sha256"), operation.get("prior_receipt_sha256"))
        actual_binding = (journal.get("operation_id"), journal.get("intended_receipt_sha256"), journal.get("prior_receipt_sha256"))
        if actual_binding != expected_binding:
            issues.append(Issue("RECEIPT-JOURNAL-BINDING", f"$/operation/journal/{index}", "journal operation or receipt hashes do not match"))
        expected_pre, expected_pre_backups, expected_post, expected_post_backups = expected_proofs(journal)
        precondition = journal.get("precondition", {})
        postcondition = journal.get("postcondition", {})
        issues.extend(proof_issues(precondition, expected_pre, expected_pre_backups, journal, "RECEIPT-PRECONDITION", f"$/operation/journal/{index}/precondition"))
        issues.extend(proof_issues(postcondition, expected_post, expected_post_backups, journal, "RECEIPT-POSTCONDITION", f"$/operation/journal/{index}/postcondition"))
        try:
            if not isinstance(precondition, dict) or not isinstance(postcondition, dict):
                raise TypeError("malformed proof")
            precondition_time = parse_timestamp(precondition.get("observed_at", ""))
            postcondition_time = parse_timestamp(postcondition.get("observed_at", ""))
            if postcondition_time < precondition_time:
                issues.append(Issue("RECEIPT-POSTCONDITION", f"$/operation/journal/{index}/postcondition/observed_at", "postcondition was observed before its precondition"))
            if prior_postcondition_time is not None and precondition_time < prior_postcondition_time:
                issues.append(Issue("RECEIPT-PRECONDITION", f"$/operation/journal/{index}/precondition/observed_at", "precondition predates the preceding row's postcondition"))
            prior_postcondition_time = postcondition_time
        except (TypeError, ValueError):
            pass
        if journal.get("precondition_sha256") != canonical_sha256(precondition):
            issues.append(Issue("RECEIPT-PRECONDITION", f"$/operation/journal/{index}/precondition_sha256", "precondition digest differs from the exact proof"))
        if journal.get("postcondition_sha256") != canonical_sha256(postcondition):
            issues.append(Issue("RECEIPT-POSTCONDITION", f"$/operation/journal/{index}/postcondition_sha256", "postcondition digest differs from the exact proof"))
        computed_journal_hash = canonical_sha256(journal_entry_projection(journal))
        if journal.get("prior_journal_sha256") != prior_journal_hash or journal.get("journal_entry_sha256") != computed_journal_hash:
            issues.append(Issue("RECEIPT-JOURNAL-HASH", f"$/operation/journal/{index}", "journal hash or prior-row link does not match"))
        prior_journal_hash = journal.get("journal_entry_sha256")
        try:
            recorded = parse_timestamp(journal.get("recorded_at", ""))
            if prior_time is not None and recorded < prior_time:
                issues.append(Issue("RECEIPT-JOURNAL-ORDER", f"$/operation/journal/{index}/recorded_at", "journal timestamps moved backward"))
            prior_time = recorded
        except (TypeError, ValueError):
            pass
    return issues


def runtime_semantic_issues(message: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    kind = message.get("message_kind")
    if kind == "request":
        reserved_authority_fields = {
            "principal",
            "authenticated_principal",
            "role",
            "capability_token",
            "approval_secret",
            "scheduler_token",
        }

        def find_reserved(value: Any, path: str) -> list[str]:
            found: list[str] = []
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in reserved_authority_fields:
                        found.append(f"{path}/{key}")
                    found.extend(find_reserved(child, f"{path}/{key}"))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    found.extend(find_reserved(child, f"{path}/{index}"))
            return found

        reserved = find_reserved(message.get("payload", {}), "$/payload")
        if reserved:
            issues.append(Issue("RUNTIME-CALLER-AUTHORITY", "$/payload", f"reserved authority fields at {reserved}"))
        try:
            expected_payload_hash = canonical_sha256(message.get("payload", {}))
            if message.get("payload_sha256") != expected_payload_hash:
                issues.append(Issue("RUNTIME-PAYLOAD-HASH", "$/payload_sha256", f"expected {expected_payload_hash}"))
        except ValueError as error:
            issues.append(Issue("RUNTIME-PAYLOAD-HASH", "$/payload", str(error)))
        if message.get("operation") == "CreateRun":
            if message.get("run_id") is not None or message.get("expected_run_version") is not None:
                issues.append(Issue("RUNTIME-CREATE-VERSION", "$", "CreateRun must have null run_id and expected_run_version"))
        elif message.get("run_id") is None or message.get("expected_run_version") is None:
            issues.append(Issue("RUNTIME-EXPECTED-VERSION", "$", "mutating non-create request requires run_id and expected version"))
    if kind == "observation" and message.get("delivery") == "replayable":
        string_fields = ("source_event_id", "source_epoch", "source_cursor")
        if any(not isinstance(message.get(field), str) or not message.get(field) for field in string_fields) or not isinstance(message.get("source_seq"), int) or message.get("source_seq") <= 0:
            issues.append(Issue("RUNTIME-REPLAY-EVIDENCE", "$", "replayable observation lacks native identity, epoch, sequence, or cursor"))
    if kind == "transition":
        authority = load_json(ROOT / "runtime/protocol-v0/authority-matrix.json")
        allowed = authority.get("operations", {}).get(message.get("operation"), [])
        if message.get("authenticated_principal") not in allowed:
            issues.append(Issue("RUNTIME-TRANSITION-AUTHORITY", "$", f"{message.get('authenticated_principal')!r} cannot commit {message.get('operation')!r}"))
    if kind == "approval_record":
        descriptor = message.get("descriptor", {})
        try:
            def forbidden_action_values(value: Any, path: str) -> list[str]:
                found: list[str] = []
                if isinstance(value, float):
                    found.append(path)
                elif isinstance(value, dict):
                    for key, child in value.items():
                        found.extend(forbidden_action_values(child, f"{path}/{key}"))
                elif isinstance(value, list):
                    for value_index, child in enumerate(value):
                        found.extend(forbidden_action_values(child, f"{path}/{value_index}"))
                return found

            forbidden_values = forbidden_action_values(descriptor, "$/descriptor")
            if forbidden_values:
                issues.append(Issue("RUNTIME-ACTION-VALUE", "$/descriptor", f"only integers, not floating-point values, are permitted at {forbidden_values}"))
            expected_digest = canonical_sha256(descriptor)
            if message.get("action_digest") != expected_digest:
                issues.append(Issue("RUNTIME-ACTION-DIGEST", "$/action_digest", f"expected {expected_digest}"))
            if canonical_normalize(descriptor) != descriptor:
                issues.append(Issue("RUNTIME-ACTION-NORMALIZATION", "$/descriptor", "descriptor strings are not in canonical normalized form"))
        except ValueError as error:
            issues.append(Issue("RUNTIME-ACTION-DIGEST", "$/descriptor", str(error)))
        consumptions = message.get("consumptions", [])
        consumption_ids, duplicate = _ids(consumptions, "consumption_id")
        issues.extend(Issue("RUNTIME-APPROVAL-CONSUMPTION", issue.location, issue.message) for issue in duplicate)
        native_refs = [consumption.get("native_request_ref") for consumption in consumptions]
        if len(native_refs) != len(set(native_refs)):
            issues.append(Issue("RUNTIME-APPROVAL-CONSUMPTION", "$/consumptions", "native approval request was consumed more than once"))
        reuse = descriptor.get("reuse", {})
        max_uses = reuse.get("max_uses")
        if reuse.get("mode") == "one_shot" and max_uses != 1:
            issues.append(Issue("RUNTIME-APPROVAL-REUSE", "$/descriptor/reuse", "one-shot approval must have max_uses 1"))
        if isinstance(max_uses, int) and len(consumptions) > max_uses:
            issues.append(Issue("RUNTIME-APPROVAL-REUSE", "$/consumptions", "consumptions exceed approved maximum"))
        if message.get("decision") == "deny" and consumptions:
            issues.append(Issue("RUNTIME-APPROVAL-DENIED", "$/consumptions", "denied approval cannot be consumed"))
        try:
            issued = parse_timestamp(message["issued_at"])
            expires = parse_timestamp(message["expires_at"])
            revoked = parse_timestamp(message["revoked_at"]) if message.get("revoked_at") else None
            if expires <= issued or (revoked and revoked < issued):
                issues.append(Issue("RUNTIME-APPROVAL-TIME", "$", "approval issue, expiry, revocation, or consumption order is invalid"))
            prior_version = 0
            for index, consumption in enumerate(consumptions):
                consumed = parse_timestamp(consumption["consumed_at"])
                if not (issued <= consumed <= expires) or (revoked and consumed >= revoked):
                    issues.append(Issue("RUNTIME-APPROVAL-TIME", f"$/consumptions/{index}/consumed_at", "consumption is outside validity or at/after revocation"))
                if consumption.get("prior_approval_version") != prior_version or consumption.get("committed_approval_version") != prior_version + 1:
                    issues.append(Issue("RUNTIME-APPROVAL-CONSUMPTION", f"$/consumptions/{index}", "approval versions are not a contiguous compare-and-consume chain"))
                prior_version += 1
            if consumptions and message.get("record_version") != prior_version:
                issues.append(Issue("RUNTIME-APPROVAL-CONSUMPTION", "$/record_version", f"expected committed version {prior_version}"))
        except (KeyError, TypeError, ValueError):
            pass
    if kind in ("environment_offer", "capability_snapshot"):
        for index, capability in enumerate(message.get("capabilities", [])):
            if not capability.get("available") and capability.get("control_strength") == "enforced":
                issues.append(Issue("RUNTIME-CAPABILITY-CLAIM", f"$/capabilities/{index}", "unavailable capability cannot be enforced"))
    return issues


def apply_mutations(base: Any, mutations: list[dict[str, Any]]) -> Any:
    result = copy.deepcopy(base)
    for mutation in mutations:
        parts = [part.replace("~1", "/").replace("~0", "~") for part in mutation["path"].lstrip("/").split("/")]
        parent = result
        for part in parts[:-1]:
            parent = parent[int(part)] if isinstance(parent, list) else parent[part]
        final = parts[-1]
        operation = mutation["op"]
        if operation == "copy":
            value = copy.deepcopy(json_pointer(result, mutation["from"]))
            if isinstance(parent, list):
                if final == "-":
                    parent.append(value)
                else:
                    parent.insert(int(final), value)
            else:
                parent[final] = value
        elif operation == "remove":
            if isinstance(parent, list):
                del parent[int(final)]
            else:
                del parent[final]
        elif operation in ("add", "replace"):
            value = mutation.get("value")
            if isinstance(parent, list):
                if final == "-":
                    parent.append(value)
                elif operation == "add":
                    parent.insert(int(final), value)
                else:
                    parent[int(final)] = value
            else:
                parent[final] = value
        else:
            raise ValueError(f"unsupported fixture patch operation {operation}")
    return result


def runtime_sequence_issues(path: Path, schema: dict[str, Any]) -> list[Issue]:
    sequence = load_json(path)
    base = load_json(path.parent / sequence["base"])
    ledger: dict[tuple[str, str], tuple[Any, ...]] = {}
    issues: list[Issue] = []
    for index, step in enumerate(sequence.get("steps", [])):
        request = apply_mutations(base, step.get("patch", []))
        validation = validate_schema(request, schema) + runtime_semantic_issues(request)
        if validation:
            issues.append(Issue("RUNTIME-SEQUENCE-REQUEST", f"{path.relative_to(ROOT)}:steps[{index}]", f"request invalid: {[issue.code for issue in validation]}"))
            continue
        principal = step.get("authenticated_connection_principal")
        scoped_key = (principal, request.get("idempotency_key"))
        identity = (
            request.get("operation"),
            request.get("run_id"),
            request.get("expected_run_version"),
            request.get("payload_sha256"),
        )
        if scoped_key in ledger:
            actual = "replayed" if ledger[scoped_key] == identity else "idempotency_conflict"
        elif request.get("expected_run_version") != step.get("current_run_version"):
            actual = "version_conflict"
        else:
            ledger[scoped_key] = identity
            actual = "accepted"
        if actual != step.get("expected"):
            issues.append(Issue("RUNTIME-SEQUENCE", f"{path.relative_to(ROOT)}:steps[{index}]", f"expected {step.get('expected')}, got {actual}"))
    return issues


def retention_fixture_issues(path: Path) -> list[Issue]:
    fixture = load_json(path)
    required = {"retention-expiry", "active-legal-hold", "complete-deletion", "partial-replica-failure", "installation-backup-excluded"}
    cases = fixture.get("cases", [])
    ids = {case.get("case_id") for case in cases}
    issues: list[Issue] = []
    if ids != required:
        issues.append(Issue("RUNTIME-RETENTION-FIXTURE", str(path.relative_to(ROOT)), f"expected {sorted(required)}, got {sorted(ids)}"))
    for index, case in enumerate(cases):
        if not case.get("condition") or len(case.get("required_outcome", [])) < 2:
            issues.append(Issue("RUNTIME-RETENTION-FIXTURE", f"{path.relative_to(ROOT)}:cases[{index}]", "case lacks condition or concrete outcomes"))
    return issues


def authority_fixture_issues(path: Path, schema: dict[str, Any]) -> list[Issue]:
    fixture = load_json(path)
    matrix_path = (path.parent / fixture.get("matrix", "")).resolve()
    matrix = load_json(matrix_path)
    issues: list[Issue] = []
    schema_operations = set(schema["$defs"]["Operation"]["enum"])
    matrix_operations = matrix.get("operations", {})
    if set(matrix_operations) != schema_operations:
        issues.append(Issue("RUNTIME-AUTHORITY-MATRIX", str(matrix_path.relative_to(ROOT)), "operation coverage differs from the request schema"))
    if (
        matrix.get("default") != "deny"
        or matrix.get("authority_source") != "authenticated_connection_principal"
        or matrix.get("authenticated_scope_required") is not True
        or matrix.get("payload_authority_fields") != "forbidden"
    ):
        issues.append(Issue("RUNTIME-AUTHORITY-MATRIX", str(matrix_path.relative_to(ROOT)), "deny-by-default authenticated authority controls are incomplete"))
    expected_matrix = {
        "CreateRun": ["operator"],
        "ProposePlanRevision": ["policy_actor"],
        "CommitPlanRevision": ["scheduler"],
        "AdmitAttempt": ["scheduler"],
        "BindWorker": ["scheduler"],
        "SteerAttempt": ["policy_actor"],
        "InterruptAttempt": ["operator", "policy_actor"],
        "RecordFinding": ["policy_actor"],
        "DispositionFinding": ["policy_actor"],
        "AcceptResult": ["policy_actor"],
        "RecordVerification": ["policy_actor"],
        "AdoptArtifact": ["policy_actor"],
        "GrantLease": ["scheduler"],
        "ReleaseLease": ["scheduler"],
        "RecordApproval": ["approval_channel"],
        "BeginDrain": ["operator", "scheduler"],
        "CloseRun": ["operator"],
    }
    if matrix_operations != expected_matrix:
        issues.append(Issue("RUNTIME-AUTHORITY-MATRIX", str(matrix_path.relative_to(ROOT)), "principal-operation assignments differ from the reviewed deny-by-default oracle"))
    known_principals = {"operator", "policy_actor", "scheduler", "approval_channel", "adapter", "worker"}
    for operation, principals in matrix_operations.items():
        unknown = set(principals) - known_principals
        if unknown or len(principals) != len(set(principals)):
            issues.append(Issue("RUNTIME-AUTHORITY-MATRIX", f"{matrix_path.relative_to(ROOT)}:{operation}", f"invalid principals {sorted(unknown)} or duplicates"))
    case_ids: set[Any] = set()
    required_cases = {"scheduler-commit", "policy-cannot-commit", "operator-cannot-self-record-approval", "adapter-cannot-request", "unknown-principal-denied"}
    for index, case in enumerate(fixture.get("cases", [])):
        case_id = case.get("case_id")
        if case_id in case_ids:
            issues.append(Issue("RUNTIME-AUTHORITY-CASE", f"{path.relative_to(ROOT)}:cases[{index}]", f"duplicate case {case_id}"))
        case_ids.add(case_id)
        operation = case.get("operation")
        actual = "allow" if case.get("principal") in matrix_operations.get(operation, []) else "deny"
        if operation not in schema_operations or case.get("expected") != actual:
            issues.append(Issue("RUNTIME-AUTHORITY-CASE", f"{path.relative_to(ROOT)}:cases[{index}]", f"expected {case.get('expected')}, matrix gives {actual}"))
    if not required_cases.issubset(case_ids):
        issues.append(Issue("RUNTIME-AUTHORITY-CASE", str(path.relative_to(ROOT)), f"missing required cases {sorted(required_cases - case_ids)}"))
    return issues


def approval_argument_fixture_issues(path: Path) -> list[Issue]:
    fixture = load_json(path)
    issues: list[Issue] = []
    if fixture.get("descriptor_version") != "ActionArguments/v1" or fixture.get("canonicalization") != "sage-json-v1+sha256":
        issues.append(Issue("RUNTIME-ARGUMENT-FIXTURE", str(path.relative_to(ROOT)), "argument descriptor or canonicalization version is wrong"))
    cases = fixture.get("cases", [])
    required = {"exact-match", "key-order-equivalent", "newline-normalized", "nfc-key-normalized", "different-destination", "floating-point-rejected", "normalized-key-collision-rejected"}
    case_ids = {case.get("case_id") for case in cases}
    if case_ids != required or len(case_ids) != len(cases):
        issues.append(Issue("RUNTIME-ARGUMENT-FIXTURE", str(path.relative_to(ROOT)), f"expected cases {sorted(required)}, got {sorted(case_ids)}"))

    def contains_float(value: Any) -> bool:
        if isinstance(value, float):
            return True
        if isinstance(value, dict):
            return any(contains_float(child) for child in value.values())
        if isinstance(value, list):
            return any(contains_float(child) for child in value)
        return False

    for index, case in enumerate(cases):
        arguments = case.get("arguments")
        invalid = not isinstance(arguments, dict) or contains_float(arguments)
        try:
            actual = "invalid" if invalid else "match" if canonical_sha256(arguments) == case.get("recorded_arguments_sha256") else "mismatch"
        except ValueError:
            actual = "invalid"
        if actual != case.get("expected"):
            issues.append(Issue("RUNTIME-ARGUMENT-FIXTURE", f"{path.relative_to(ROOT)}:cases[{index}]", f"expected {case.get('expected')}, got {actual}"))
    return issues


def lifecycle_operation_fixture_issues(path: Path) -> list[Issue]:
    fixture = load_json(path)
    issues: list[Issue] = []
    cases = fixture.get("cases", [])
    case_ids = {case.get("case_id") for case in cases}
    required = {
        "committed-install",
        "committed-update-with-backup",
        "committed-uninstall",
        "committed-uninstall-keep-data",
        "uninstall-cannot-use-install-phase",
        "committed-uninstall-missing-removal-proof",
        "install-cannot-use-uninstall-phase",
    }
    if case_ids != required or len(case_ids) != len(cases):
        issues.append(Issue("RECEIPT-OPERATION-FIXTURE", str(path.relative_to(ROOT)), f"expected cases {sorted(required)}, got {sorted(case_ids)}"))
    for index, case in enumerate(cases):
        found = lifecycle_phase_issues(
            case.get("kind"),
            case.get("state"),
            case.get("phases", []),
            has_backups=case.get("has_backups") is True,
            has_entries=case.get("has_entries") is True,
            has_config=case.get("has_config") is True,
            keep_data=case.get("keep_data") is True,
            location=f"{path.relative_to(ROOT)}:cases[{index}]",
        )
        found_codes = {issue.code for issue in found}
        expected_codes = set(case.get("expected_errors", []))
        if found_codes != expected_codes:
            issues.append(Issue("RECEIPT-OPERATION-FIXTURE", f"{path.relative_to(ROOT)}:cases[{index}]", f"expected {sorted(expected_codes)}, got {sorted(found_codes)}"))
    return issues


def backup_binding_fixture_issues(path: Path, receipt_schema: dict[str, Any]) -> list[Issue]:
    fixture = load_json(path)
    base = load_json(path.parent / fixture["base"])
    common = apply_mutations(base, fixture.get("common_patch", []))
    issues: list[Issue] = []
    binding_cases = fixture.get("binding_cases", [])
    required_binding = {
        "exact-owner-and-roots", "mismatched-owner", "protected-original", "backup-outside-root",
        "backup-equals-root", "multiply-referenced", "duplicate-displaced-purpose", "duplicate-config-prior-purpose",
    }
    if {case.get("case_id") for case in binding_cases} != required_binding:
        issues.append(Issue("RECEIPT-BACKUP-FIXTURE", str(path.relative_to(ROOT)), "backup binding cases are incomplete"))
    watched_prefixes = ("RECEIPT-BACKUP", "RECEIPT-RESOURCE-ROOT", "RECEIPT-PROTECTED-OVERLAP", "RECEIPT-RESOURCE-IDENTITY", "RECEIPT-LINK-AMBIGUITY", "SCHEMA-")
    for index, case in enumerate(binding_cases):
        instance = apply_mutations(common, case.get("patch", []))
        found = validate_schema(instance, receipt_schema) + receipt_semantic_issues(instance)
        found_codes = {issue.code for issue in found if issue.code.startswith(watched_prefixes)}
        expected_codes = set(case.get("expected_errors", []))
        if found_codes != expected_codes:
            issues.append(Issue("RECEIPT-BACKUP-FIXTURE", f"{path.relative_to(ROOT)}:binding_cases[{index}]", f"expected {sorted(expected_codes)}, got {sorted(found_codes)}"))

    canonical_backup = common["backups"][0]
    expected_subject = backup_precondition_subject(canonical_backup)
    restoration_cases = fixture.get("restoration_cases", [])
    required_restoration = {"exact-live-backup", "changed-backup-content", "aliased-backup-source", "missing-backup-subject"}
    by_id = {case.get("case_id"): case for case in restoration_cases}
    if set(by_id) != required_restoration:
        issues.append(Issue("RECEIPT-BACKUP-FIXTURE", str(path.relative_to(ROOT)), "backup restoration cases are incomplete"))
    exact = by_id.get("exact-live-backup", {}).get("subject")
    for index, case in enumerate(restoration_cases):
        subject = case.get("subject")
        if case.get("subject_ref") == "exact-live-backup":
            subject = apply_mutations(exact, case.get("patch", []))
        schema_valid = not validate_schema(subject, receipt_schema["$defs"]["BackupStateSubject"], receipt_schema)
        actual = "allow" if schema_valid and subject == expected_subject else "block"
        if actual != case.get("expected"):
            issues.append(Issue("RECEIPT-BACKUP-FIXTURE", f"{path.relative_to(ROOT)}:restoration_cases[{index}]", f"expected {case.get('expected')}, got {actual}"))
    return issues


def fixture_issues() -> list[Issue]:
    issues: list[Issue] = []
    artifact_root = ROOT / "artifacts/fixtures"
    manifest = load_json(artifact_root / "manifest.json")
    artifact_schema = load_json(ROOT / "artifacts/schemas/sage-artifact-v1.schema.json")
    for fixture in manifest["valid"]:
        path = artifact_root / fixture["path"]
        instance = load_json(path)
        found = validate_schema(instance, artifact_schema) + artifact_semantic_issues(instance)
        issues.extend(Issue(issue.code, str(path.relative_to(ROOT)) + issue.location, issue.message) for issue in found)
    for fixture in manifest["invalid"]:
        path = artifact_root / fixture["path"]
        mutation = load_json(path)
        base = load_json(path.parent / mutation["base"])
        instance = apply_mutations(base, mutation["patch"])
        found = validate_schema(instance, artifact_schema) + artifact_semantic_issues(instance)
        codes = {issue.code for issue in found}
        expected_codes = set(fixture["expected_errors"])
        if codes != expected_codes:
            issues.append(Issue("FIXTURE-EXPECTED", str(path.relative_to(ROOT)), f"expected exactly {sorted(expected_codes)}, got {sorted(codes)}"))
        if mutation.get("expected_errors") != fixture.get("expected_errors"):
            issues.append(Issue("FIXTURE-MANIFEST", str(path.relative_to(ROOT)), "fixture and manifest expected_errors differ"))

    lifecycle = manifest["lifecycle"]
    receipt_schema = load_json(artifact_root / lifecycle["schema"])
    issues.extend(lifecycle_operation_fixture_issues(artifact_root / lifecycle["operation_cases"]))
    issues.extend(backup_binding_fixture_issues(artifact_root / lifecycle["backup_cases"], receipt_schema))
    for fixture in lifecycle["valid"]:
        relative = fixture["path"] if isinstance(fixture, dict) else fixture
        path = artifact_root / relative
        prior_path = fixture.get("prior") if isinstance(fixture, dict) else None
        prior_receipt = load_json(artifact_root / prior_path) if prior_path else None
        instance = load_json(path)
        found = validate_schema(instance, receipt_schema) + receipt_semantic_issues(instance, prior_receipt)
        issues.extend(Issue(issue.code, str(path.relative_to(ROOT)) + issue.location, issue.message) for issue in found)
    for fixture in lifecycle["invalid"]:
        path = artifact_root / fixture["path"]
        mutation = load_json(path)
        base = load_json(path.parent / mutation["base"])
        instance = apply_mutations(base, mutation["patch"])
        if mutation.get("refresh_integrity") is True:
            instance = refresh_receipt_fixture_integrity(instance)
        prior_path = fixture.get("prior")
        prior_receipt = load_json(artifact_root / prior_path) if prior_path else None
        found = validate_schema(instance, receipt_schema) + receipt_semantic_issues(instance, prior_receipt)
        codes = {issue.code for issue in found}
        expected_codes = set(fixture["expected_errors"])
        if codes != expected_codes:
            issues.append(Issue("FIXTURE-EXPECTED", str(path.relative_to(ROOT)), f"expected exactly {sorted(expected_codes)}, got {sorted(codes)}"))
        if mutation.get("expected_errors") != fixture.get("expected_errors"):
            issues.append(Issue("FIXTURE-MANIFEST", str(path.relative_to(ROOT)), "fixture and manifest expected_errors differ"))

    runtime_root = ROOT / "runtime/protocol-v0/fixtures"
    runtime_manifest = load_json(runtime_root / "manifest.json")
    runtime_schema = load_json(runtime_root / runtime_manifest["schema"])
    for relative in runtime_manifest["valid"]:
        path = runtime_root / relative
        instance = load_json(path)
        found = validate_schema(instance, runtime_schema) + runtime_semantic_issues(instance)
        issues.extend(Issue(issue.code, str(path.relative_to(ROOT)) + issue.location, issue.message) for issue in found)
    for fixture in runtime_manifest["invalid"]:
        path = runtime_root / fixture["path"]
        mutation = load_json(path)
        base = load_json(path.parent / mutation["base"])
        instance = apply_mutations(base, mutation["patch"])
        found = validate_schema(instance, runtime_schema) + runtime_semantic_issues(instance)
        codes = {issue.code for issue in found}
        expected_codes = set(fixture["expected_errors"])
        if codes != expected_codes:
            issues.append(Issue("FIXTURE-EXPECTED", str(path.relative_to(ROOT)), f"expected exactly {sorted(expected_codes)}, got {sorted(codes)}"))
        if mutation.get("expected_errors") != fixture.get("expected_errors"):
            issues.append(Issue("FIXTURE-MANIFEST", str(path.relative_to(ROOT)), "fixture and manifest expected_errors differ"))
    for relative in runtime_manifest.get("sequences", []):
        issues.extend(runtime_sequence_issues(runtime_root / relative, runtime_schema))
    issues.extend(approval_argument_fixture_issues(runtime_root / runtime_manifest["approval_argument_cases"]))
    issues.extend(authority_fixture_issues(runtime_root / runtime_manifest["authorization_cases"], runtime_schema))
    issues.extend(retention_fixture_issues(runtime_root / runtime_manifest["retention_cases"]))
    return issues


def markdown_without_fences(text: str) -> str:
    output: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        stripped = line.lstrip()
        marker = "```" if stripped.startswith("```") else "~~~" if stripped.startswith("~~~") else None
        if marker:
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            output.append("")
        elif fence is None:
            output.append(line)
        else:
            output.append("")
    return "\n".join(output)


def heading_slug(heading: str) -> str:
    heading = re.sub(r"[`*_]", "", heading.strip().lower())
    heading = re.sub(r"[^\w\- ]", "", heading, flags=re.UNICODE)
    heading = re.sub(r"[\s\-]+", "-", heading).strip("-")
    return heading


def markdown_headings(path: Path) -> set[str]:
    headings: set[str] = set()
    for line in markdown_without_fences(path.read_text(encoding="utf-8")).splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            headings.add(heading_slug(match.group(1)))
    return headings


LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


def pointer_issues(paths: Iterable[Path], root: Path = ROOT) -> list[Issue]:
    issues: list[Issue] = []
    for path in paths:
        text = markdown_without_fences(path.read_text(encoding="utf-8"))
        for line_number, line in enumerate(text.splitlines(), 1):
            for match in LINK_RE.finditer(line):
                raw_target = match.group(1).strip()
                if raw_target.startswith("<") and raw_target.endswith(">"):
                    raw_target = raw_target[1:-1]
                if re.match(r"^(https?://|mailto:)", raw_target):
                    continue
                file_part, separator, fragment = raw_target.partition("#")
                target = path if not file_part else (path.parent / file_part).resolve()
                try:
                    target.relative_to(root.resolve())
                except ValueError:
                    issues.append(Issue("POINTER-ESCAPE", f"{path.relative_to(root)}:{line_number}", raw_target))
                    continue
                if not target.exists():
                    issues.append(Issue("POINTER-MISSING", f"{path.relative_to(root)}:{line_number}", raw_target))
                    continue
                if separator and fragment:
                    if target.suffix.lower() == ".md":
                        if fragment not in markdown_headings(target):
                            issues.append(Issue("POINTER-FRAGMENT", f"{path.relative_to(root)}:{line_number}", raw_target))
                    elif target.suffix.lower() == ".json" and fragment.startswith("/"):
                        try:
                            json_pointer(load_json(target), fragment)
                        except (KeyError, IndexError, ValueError):
                            issues.append(Issue("POINTER-FRAGMENT", f"{path.relative_to(root)}:{line_number}", raw_target))
    return issues


HOST_PATTERNS = {
    "host-name": re.compile(r"\b(?:claude|codex|openai|anthropic)\b", re.IGNORECASE),
    "host-path": re.compile(r"(?:\.claude/|\.codex/|~/\.claude|~/\.codex)", re.IGNORECASE),
    "host-tool": re.compile(r"\b(?:spawn_agent|send_message|followup_task|interrupt_agent|list_agents|wait_agent|TaskStop|ToolSearch)\b", re.IGNORECASE),
    "concrete-model": re.compile(r"\b(?:gpt-[\w.-]+|sonnet|opus|haiku)\b", re.IGNORECASE),
    "app-server": re.compile(r"\bapp server\b", re.IGNORECASE),
}


def host_leak_issues(paths: Iterable[Path], root: Path = ROOT) -> list[Issue]:
    issues: list[Issue] = []
    for path in paths:
        text = markdown_without_fences(path.read_text(encoding="utf-8"))
        for line_number, line in enumerate(text.splitlines(), 1):
            for name, pattern in HOST_PATTERNS.items():
                match = pattern.search(line)
                if match:
                    issues.append(Issue("POLICY-HOST-LEAK", f"{path.relative_to(root)}:{line_number}", f"{name}: {match.group(0)}"))
    return issues


SPECIAL_SECTIONS = {"script", "header manual", "README"}


def resolve_inventory_pointer(pointer: str) -> bool:
    file_part, separator, fragment = pointer.partition("#")
    path = REPOSITORY_ROOT / file_part
    if not path.exists():
        return False
    if not separator or not fragment:
        return True
    if path.suffix == ".md":
        return fragment in markdown_headings(path)
    if path.suffix == ".json" and fragment.startswith("/"):
        try:
            json_pointer(load_json(path), fragment)
            return True
        except (KeyError, IndexError, ValueError, DuplicateKeyError):
            return False
    return False


def inventory_issues() -> list[Issue]:
    path = ROOT / "docs/phase0/invariant-ownership.json"
    inventory = load_json(path)
    issues: list[Issue] = []
    allowed_owners = set(inventory.get("owner_categories", []))
    ids: set[str] = set()
    covered_classes: set[str] = set()
    covered_sources: set[tuple[str, str]] = set()
    for index, invariant in enumerate(inventory.get("invariants", [])):
        invariant_id = invariant.get("id")
        if invariant_id in ids:
            issues.append(Issue("OWNER-DUPLICATE-ID", f"{path.relative_to(ROOT)}:invariants[{index}]", str(invariant_id)))
        ids.add(invariant_id)
        owner = invariant.get("owner")
        if not isinstance(owner, str) or owner not in allowed_owners:
            issues.append(Issue("OWNER-INVALID", f"{path.relative_to(ROOT)}:{invariant_id}", f"owner {owner!r}"))
        if not resolve_inventory_pointer(invariant.get("canonical", "")):
            issues.append(Issue("OWNER-CANONICAL-POINTER", f"{path.relative_to(ROOT)}:{invariant_id}", invariant.get("canonical", "")))
        covered_classes.update(invariant.get("classes", []))
        for baseline in invariant.get("baseline", []):
            key_name = "path" if "path" in baseline else "glob"
            key = (key_name, baseline.get(key_name, ""))
            covered_sources.add(key)
            if key_name == "path":
                source = REPOSITORY_ROOT / baseline["path"]
                if not source.exists():
                    issues.append(Issue("OWNER-BASELINE-MISSING", f"{path.relative_to(ROOT)}:{invariant_id}", baseline["path"]))
                section = baseline.get("section")
                if source.suffix == ".md" and section and section not in SPECIAL_SECTIONS:
                    if heading_slug(section) not in markdown_headings(source):
                        issues.append(Issue("OWNER-BASELINE-SECTION", f"{path.relative_to(ROOT)}:{invariant_id}", f"{baseline['path']}#{section}"))
            else:
                matches = glob.glob(str(REPOSITORY_ROOT / baseline["glob"]), recursive=True)
                if not matches:
                    issues.append(Issue("OWNER-BASELINE-MISSING", f"{path.relative_to(ROOT)}:{invariant_id}", baseline["glob"]))

    missing_classes = set(inventory.get("required_obligation_classes", [])) - covered_classes
    if missing_classes:
        issues.append(Issue("OWNER-CLASS-COVERAGE", str(path.relative_to(ROOT)), f"missing {sorted(missing_classes)}"))
    for source in inventory.get("baseline_sources", []):
        key_name = "path" if "path" in source else "glob"
        key = (key_name, source[key_name])
        if key not in covered_sources:
            issues.append(Issue("OWNER-SOURCE-COVERAGE", str(path.relative_to(ROOT)), f"unowned baseline source {source[key_name]}"))
        if key_name == "path" and not (REPOSITORY_ROOT / source["path"]).exists():
            issues.append(Issue("OWNER-BASELINE-MISSING", str(path.relative_to(ROOT)), source["path"]))
        if key_name == "glob" and not glob.glob(str(REPOSITORY_ROOT / source["glob"]), recursive=True):
            issues.append(Issue("OWNER-BASELINE-MISSING", str(path.relative_to(ROOT)), source["glob"]))

    policy_markers: dict[str, str] = {}
    for policy_path in sorted((ROOT / "policy").glob("*.md")):
        match = re.search(r"^Policy owner: `([^`]+)`$", policy_path.read_text(encoding="utf-8"), re.MULTILINE)
        if policy_path.name == "README.md":
            continue
        if not match:
            issues.append(Issue("OWNER-POLICY-MARKER", str(policy_path.relative_to(ROOT)), "missing Policy owner marker"))
            continue
        marker = match.group(1)
        if marker in policy_markers:
            issues.append(Issue("OWNER-DUPLICATE-POLICY", str(policy_path.relative_to(ROOT)), f"also declared in {policy_markers[marker]}"))
        policy_markers[marker] = str(policy_path.relative_to(ROOT))
    expected_markers = {f"policy.{name}" for name in ("delegation", "contracts", "topologies", "review", "recovery", "memory")}
    if set(policy_markers) != expected_markers:
        issues.append(Issue("OWNER-POLICY-MARKER", "policy/", f"found {sorted(policy_markers)}, expected {sorted(expected_markers)}"))
    return issues


KNOWLEDGE_PORTABLE_FIELDS = (
    "stable_id",
    "class",
    "status",
    "rule",
    "qualifier",
    "recognizer",
    "falsifier",
    "provenance",
)


def knowledge_projection(record: dict[str, Any]) -> dict[str, Any]:
    projection = {field: record.get(field) for field in KNOWLEDGE_PORTABLE_FIELDS}
    normalized = canonical_normalize(projection)
    normalized["provenance"] = sorted(normalized.get("provenance", []), key=canonical_json_bytes)
    return normalized


def promotion_fixture_issues() -> list[Issue]:
    path = ROOT / "docs/phase0/promotion-reconciliation-cases.json"
    fixture = load_json(path)
    issues: list[Issue] = []
    cases = {case.get("case_id"): case for case in fixture.get("cases", [])}
    required = {"equivalent-format-and-local-metadata", "divergent-portable-content", "same-hash-unequal-bytes", "stale-stored-integrity", "idempotent-rerun"}
    if set(cases) != required:
        issues.append(Issue("PROMOTION-FIXTURE", str(path.relative_to(ROOT)), f"expected {sorted(required)}, got {sorted(cases)}"))
        return issues

    base = cases["equivalent-format-and-local-metadata"]
    left_bytes = canonical_json_bytes(knowledge_projection(base["left"]))
    right_bytes = canonical_json_bytes(knowledge_projection(base["right"]))
    left_hash = hashlib.sha256(left_bytes).hexdigest()
    right_hash = hashlib.sha256(right_bytes).hexdigest()
    if (
        left_bytes != right_bytes
        or base["left"].get("stored_integrity_sha256") != left_hash
        or base["right"].get("stored_integrity_sha256") != right_hash
        or base.get("expected") != "equivalent"
    ):
        issues.append(Issue("PROMOTION-EQUIVALENCE", str(path.relative_to(ROOT)), "format/local-metadata case is not equivalent"))

    divergent = cases["divergent-portable-content"]
    divergent_record = copy.deepcopy(base["left"])
    divergent_record.update(divergent.get("right_patch", {}))
    divergent_bytes = canonical_json_bytes(knowledge_projection(divergent_record))
    divergent_hash = hashlib.sha256(divergent_bytes).hexdigest()
    if divergent_bytes == left_bytes or divergent.get("right_stored_integrity_sha256") != divergent_hash or divergent.get("expected") != "conflict":
        issues.append(Issue("PROMOTION-CONFLICT", str(path.relative_to(ROOT)), "divergent portable content was not a conflict"))

    collision = cases["same-hash-unequal-bytes"]
    collision_record = copy.deepcopy(base["left"])
    collision_record.update(collision.get("right_patch", {}))
    collision_bytes = canonical_json_bytes(knowledge_projection(collision_record))
    if (
        collision_bytes == left_bytes
        or not collision.get("forced_hash_equal")
        or collision.get("forced_stored_integrity_sha256") != left_hash
        or collision.get("expected") != "collision_error"
    ):
        issues.append(Issue("PROMOTION-COLLISION", str(path.relative_to(ROOT)), "collision oracle does not preserve unequal bytes"))

    stale = cases["stale-stored-integrity"]
    if stale.get("stored_integrity_override") == left_hash or stale.get("expected") != "integrity_error":
        issues.append(Issue("PROMOTION-INTEGRITY", str(path.relative_to(ROOT)), "stale integrity case does not force a stored/projection mismatch"))

    rerun = cases["idempotent-rerun"]
    state = {
        "repository_active": [{"stable_id": base["left"]["stable_id"], "projection_sha256": left_hash}],
        "overlay_active": [],
        "overlay_archive": [{"stable_id": base["right"]["stable_id"], "projection_sha256": right_hash, "reconciled_to": f"repository:{base['left']['stable_id']}"}],
    }
    observed_states = [copy.deepcopy(state) for _ in range(rerun.get("applications", 0))]
    if (
        rerun.get("repository_ref") != "equivalent-format-and-local-metadata:left"
        or rerun.get("overlay_ref") != "equivalent-format-and-local-metadata:right"
        or rerun.get("applications") != 2
        or rerun.get("expected_after_each_application") != observed_states
        or rerun.get("expected_state_sha256") != canonical_sha256(state)
        or rerun.get("expected") != "idempotent"
    ):
        issues.append(Issue("PROMOTION-IDEMPOTENCY", str(path.relative_to(ROOT)), "repeated reconciliation duplicated a record"))
    return issues


def evaluation_issues() -> list[Issue]:
    issues: list[Issue] = []
    task_path = ROOT / "evaluation/phase-1/tasks.json"
    rubric_path = ROOT / "evaluation/phase-1/rubric.json"
    tasks = load_json(task_path)
    rubric = load_json(rubric_path)
    task_rows = tasks.get("tasks", [])
    if len(task_rows) != 20:
        issues.append(Issue("EVAL-TASK-COUNT", str(task_path.relative_to(ROOT)), f"expected 20, found {len(task_rows)}"))
    task_ids = [task.get("task_id") for task in task_rows]
    if len(task_ids) != len(set(task_ids)):
        issues.append(Issue("EVAL-TASK-DUPLICATE", str(task_path.relative_to(ROOT)), "task IDs are not unique"))
    strata: dict[str, int] = {}
    eligible = set(tasks.get("wall_time_eligible_task_ids", []))
    assessments = tasks.get("independence_assessments", {})
    declared_independent = {task.get("task_id") for task in task_rows if task.get("three_plus_independent_units") is True}
    if not tasks.get("independence_rule") or set(assessments) != set(task_ids) or any(not assessments.get(task_id) for task_id in task_ids):
        issues.append(Issue("EVAL-INDEPENDENCE", str(task_path.relative_to(ROOT)), "independence rule or per-task assessments are incomplete"))
    if eligible != declared_independent:
        issues.append(Issue("EVAL-INDEPENDENCE", str(task_path.relative_to(ROOT)), f"eligible IDs {sorted(eligible)} differ from independently classified IDs {sorted(declared_independent)}"))
    for task in task_rows:
        strata[task.get("stratum")] = strata.get(task.get("stratum"), 0) + 1
        if task.get("three_plus_independent_units") is True and len(task.get("preclassified_independent_units", [])) < 3:
            issues.append(Issue("EVAL-PRECLASSIFICATION", f"{task_path.relative_to(ROOT)}:{task.get('task_id')}", "three-unit classification is incomplete"))
        for corpus_id in task.get("corpus_set_ids", []):
            if corpus_id not in tasks.get("corpus_sets", {}):
                issues.append(Issue("EVAL-CORPUS", f"{task_path.relative_to(ROOT)}:{task.get('task_id')}", f"unknown corpus set {corpus_id}"))
    if sorted(strata.values()) != [4, 4, 4, 4, 4]:
        issues.append(Issue("EVAL-STRATA", str(task_path.relative_to(ROOT)), f"expected five strata of four, found {strata}"))
    if sum(dimension.get("points", 0) for dimension in rubric.get("dimensions", [])) != rubric.get("total_points"):
        issues.append(Issue("EVAL-RUBRIC", str(rubric_path.relative_to(ROOT)), "dimension points do not total total_points"))
    task_20 = next((task for task in task_rows if task.get("task_id") == "P1-T20"), {})
    if task_20.get("three_plus_independent_units") is not False or task_20.get("deterministic_root_loss_fixture") is not False:
        issues.append(Issue("EVAL-ROOT-LOSS", f"{task_path.relative_to(ROOT)}:P1-T20", "sequential prose task must not be wall-time eligible or count as executable root loss"))

    root_loss_path = ROOT / "evaluation/phase-1/root-loss-fixture.json"
    root_loss = load_json(root_loss_path)
    root_cases = {case.get("case_id"): case for case in root_loss.get("cases", [])}
    expected_root_cases = {"accepted-response-lost", "not-started-response-lost", "handle-persisted-before-root-loss"}
    deterministic_oracles = {
        "accepted-response-lost": (1, 1, 0),
        "not-started-response-lost": (1, 0, 0),
        "handle-persisted-before-root-loss": (1, 1, 0),
    }
    deterministic_cases = set(root_cases) == expected_root_cases
    for case_id, counts in deterministic_oracles.items():
        case = root_cases.get(case_id, {})
        oracle = case.get("oracle_before_recovery", {})
        actual_counts = (
            oracle.get("native_start_invocations"),
            oracle.get("native_workers_created"),
            oracle.get("duplicate_workers_created"),
        )
        if (
            actual_counts != counts
            or not case.get("forced_native_outcome")
            or not case.get("kill_schedule")
            or not case.get("permitted_safe_terminals")
            or not case.get("autonomous_success_terminal")
        ):
            deterministic_cases = False
    driver = root_loss.get("driver_contract", {})
    if (
        root_loss.get("execution_required") is not True
        or driver.get("repetitions_per_case") != 3
        or driver.get("fresh_run_per_repetition") is not True
        or "hidden" not in driver.get("oracle_isolation", "")
        or len(driver.get("counter_definitions", {})) != 3
        or not deterministic_cases
        or len(root_loss.get("required_observations", [])) < 7
        or len(root_loss.get("oracle_assertions", {}).get("all_cases", [])) < 4
        or not root_loss.get("required_success")
        or not root_loss.get("light_mode_inability")
    ):
        issues.append(Issue("EVAL-ROOT-LOSS", str(root_loss_path.relative_to(ROOT)), "executable fault-injection oracle is incomplete"))

    preregistration_path = ROOT / "evaluation/phase-1/preregistration.md"
    preregistration = preregistration_path.read_text(encoding="utf-8")
    for required_text in (
        "pre-execution manifest",
        "every included pair",
        "cheap tasks cannot cross-subsidize",
        "If a control denominator above is zero",
        "A prose simulation is not a pass or failure",
        "Quality and safety require all 20 frozen task pairs",
        "at least 16 of 20 pairs",
        "at least 16 of the 19 frozen eligible pairs",
        "no post-outcome substitution",
    ):
        if required_text not in preregistration:
            issues.append(Issue("EVAL-PREREGISTRATION", str(preregistration_path.relative_to(ROOT)), f"missing frozen rule {required_text!r}"))
    baseline = tasks.get("baseline_revision")
    for corpus_paths in tasks.get("corpus_sets", {}).values():
        for corpus_path in corpus_paths:
            command = ["git", "cat-file", "-e", f"{baseline}:{corpus_path}"]
            result = subprocess.run(command, cwd=REPOSITORY_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            if result.returncode != 0:
                issues.append(Issue("EVAL-CORPUS", str(task_path.relative_to(ROOT)), f"{corpus_path} is absent at {baseline}"))

    freeze_path = ROOT / "evaluation/phase-1/PREREGISTRATION.sha256"
    expected_files = ["preregistration.md", "root-loss-fixture.json", "rubric.json", "tasks.json"]
    if not freeze_path.exists():
        issues.append(Issue("EVAL-FREEZE", str(freeze_path.relative_to(ROOT)), "hash manifest is missing"))
    else:
        lines = [line.split(None, 1) for line in freeze_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        recorded = {name.strip(): digest for digest, name in lines if name.strip()}
        if set(recorded) != set(expected_files):
            issues.append(Issue("EVAL-FREEZE", str(freeze_path.relative_to(ROOT)), f"expected {expected_files}, found {sorted(recorded)}"))
        for name in expected_files:
            target = freeze_path.parent / name
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            if recorded.get(name) != digest:
                issues.append(Issue("EVAL-FREEZE", str(freeze_path.relative_to(ROOT)), f"hash mismatch for {name}"))
    return issues


def review_issues() -> list[Issue]:
    path = ROOT / "docs/phase0/reviews/authority-privacy-review.json"
    if not path.exists():
        return [Issue("REVIEW-MISSING", str(path.relative_to(ROOT)), "authority/privacy review is missing")]
    review = load_json(path)
    issues: list[Issue] = []
    for evidence_path in review.get("evidence", []):
        if not (REPOSITORY_ROOT / evidence_path).exists():
            issues.append(Issue("REVIEW-EVIDENCE-MISSING", str(path.relative_to(ROOT)), evidence_path))
    if review.get("status") != "pass":
        issues.append(Issue("REVIEW-STATUS", str(path.relative_to(ROOT)), f"status is {review.get('status')!r}"))
    open_blockers = [finding.get("id") for finding in review.get("findings", []) if finding.get("severity") == "blocker" and finding.get("status") != "resolved"]
    if open_blockers:
        issues.append(Issue("REVIEW-BLOCKER", str(path.relative_to(ROOT)), f"open blockers {open_blockers}"))
    return issues


def protocol_posture_issues() -> list[Issue]:
    path = ROOT / "runtime/protocol-v0/README.md"
    text = path.read_text(encoding="utf-8").lower()
    issues: list[Issue] = []
    for required in ("provisional", "does not freeze the worker port", "not a cross-harness contract"):
        if required not in text:
            issues.append(Issue("RUNTIME-POSTURE", str(path.relative_to(ROOT)), f"missing {required!r}"))
    return issues


def generated_type_issues() -> list[Issue]:
    command = [sys.executable, str(ROOT / "scripts/generate-schema-types.py"), "--check"]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode == 0:
        return []
    detail = (result.stderr or result.stdout).strip() or f"generator exited {result.returncode}"
    return [Issue("GENERATED-TYPE-DRIFT", "generated schema types", detail)]


def run_self_test() -> list[Issue]:
    issues: list[Issue] = []
    with tempfile.TemporaryDirectory(prefix="sage-phase0-check-") as directory:
        root = Path(directory)
        (root / "target.md").write_text("# Target heading\n", encoding="utf-8")
        source = root / "source.md"
        source.write_text("[ok](target.md#target-heading)\n```\n[ignored](missing.md)\n```\n", encoding="utf-8")
        if pointer_issues([source], root):
            issues.append(Issue("SELFTEST-POINTER", "self-test", "valid relative pointer or fenced example failed"))
        source.write_text("[broken](missing.md)\n", encoding="utf-8")
        if not any(issue.code == "POINTER-MISSING" for issue in pointer_issues([source], root)):
            issues.append(Issue("SELFTEST-POINTER", "self-test", "missing pointer was not detected"))
        duplicate = root / "duplicate.json"
        duplicate.write_text('{"id":"one","id":"two"}\n', encoding="utf-8")
        try:
            load_json(duplicate)
            issues.append(Issue("SELFTEST-JSON", "self-test", "duplicate JSON key was accepted"))
        except DuplicateKeyError:
            pass
        nonfinite = root / "nonfinite.json"
        nonfinite.write_text('{"value":NaN}\n', encoding="utf-8")
        try:
            load_json(nonfinite)
            issues.append(Issue("SELFTEST-JSON", "self-test", "non-finite JSON number was accepted"))
        except ValueError:
            pass
        policy = root / "policy.md"
        policy.write_text("# Policy\nUse spawn_agent here.\n", encoding="utf-8")
        if not any(issue.code == "POLICY-HOST-LEAK" for issue in host_leak_issues([policy], root)):
            issues.append(Issue("SELFTEST-LEAK", "self-test", "host tool leakage was not detected"))
        _, duplicate_ids = _ids([{"id": "DUP"}, {"id": "DUP"}], "id")
        if not duplicate_ids:
            issues.append(Issue("SELFTEST-OWNER", "self-test", "duplicate IDs were not detected"))
        if _is_canonical_absolute_path("/safe/../victim") or _is_canonical_relative_path("safe/./alias"):
            issues.append(Issue("SELFTEST-PATH", "self-test", "path aliases were accepted"))
    return issues


def collect_markdown() -> list[Path]:
    roots = [ROOT / "policy", ROOT / "docs/phase0", ROOT / "runtime/protocol-v0", ROOT / "evaluation/phase-1"]
    return sorted(path for directory in roots for path in directory.rglob("*.md"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run checker unit fixtures before the repository checks")
    args = parser.parse_args()
    issues: list[Issue] = []
    if args.self_test:
        issues.extend(run_self_test())
    try:
        markdown = collect_markdown()
        issues.extend(pointer_issues(markdown, REPOSITORY_ROOT))
        issues.extend(host_leak_issues(sorted((ROOT / "policy").glob("*.md"))))
        issues.extend(inventory_issues())
        issues.extend(promotion_fixture_issues())
        issues.extend(fixture_issues())
        issues.extend(evaluation_issues())
        issues.extend(review_issues())
        issues.extend(protocol_posture_issues())
        issues.extend(generated_type_issues())
    except (OSError, ValueError, KeyError, DuplicateKeyError, json.JSONDecodeError) as error:
        issues.append(Issue("CHECK-EXCEPTION", "phase0", str(error)))
    if issues:
        for issue in sorted(set(issues), key=lambda item: (item.code, item.location, item.message)):
            print(issue.render())
        return 1
    print("phase0-check: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
