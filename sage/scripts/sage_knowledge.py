#!/usr/bin/env python3
"""Validate, retrieve, and reversibly activate Sage knowledge generations.

This helper proves structural and recorded-reference invariants only. It cannot
prove evidence quality, causal adequacy, live actor independence, authority, or
a physical writer lease.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any

from sage_state import (
    ContractError,
    CUE_KEYS,
    ID,
    atomic_write,
    encode,
    native_handle,
    read_events,
    read_json,
    runtime_paths,
    resolve_run,
    utc_timestamp,
    validate as validate_run,
)


EMPTY_GENERATION = "none"
RECORD_FIELDS = {
    "v", "id", "revision", "prior_revision", "status", "evidence_class",
    "gate_rationale", "gate_evidence", "rule", "recognizer", "qualifier",
    "falsifier", "evidence_summary", "provenance", "alternative_explanations",
    "counterevidence", "refutation", "review", "created_at", "reviewed_at",
}
STATUSES = {"provisional", "supported", "contested", "refuted", "retired"}
EVIDENCE_CLASSES = {"scoped_fact", "transferable_heuristic", "causal_guidance"}
ACTIONS = {"create", "correct", "contest", "refute", "retire"}
MAX_TEXT = 8192
MAX_LIST = 128
UNSET = object()


def fail(condition: bool, code: str, message: str) -> None:
    if condition:
        raise ContractError(code, message)


def exact_object(value: Any, fields: set[str], where: str, code: str = "invalid_record") -> dict[str, Any]:
    fail(not isinstance(value, dict), code, f"{where} must be an object")
    fail(set(value) != fields, code, f"{where} fields must be exactly {sorted(fields)}")
    return value


def text(value: Any, where: str, code: str = "invalid_record") -> str:
    fail(not isinstance(value, str) or not value.strip(), code, f"{where} must be nonempty text")
    fail(len(value) > MAX_TEXT or any(ord(char) < 32 and char not in "\n\t" for char in value), code, f"invalid {where}")
    return value


def identifier(value: Any, where: str, code: str = "invalid_record") -> str:
    fail(not isinstance(value, str) or ID.fullmatch(value) is None, code, f"invalid {where}")
    return value


def positive(value: Any, where: str, code: str = "invalid_record") -> int:
    fail(type(value) is not int or value < 1, code, f"{where} must be a positive integer")
    return value


def string_list(value: Any, where: str, *, nonempty: bool = False, code: str = "invalid_record") -> list[str]:
    fail(not isinstance(value, list) or len(value) > MAX_LIST, code, f"{where} must be a bounded string array")
    fail(nonempty and not value, code, f"{where} must not be empty")
    result = [text(item, f"{where}[]", code) for item in value]
    fail(len(result) != len(set(result)), code, f"{where} contains duplicates")
    return result


def generation_id(value: Any) -> str:
    fail(
        not isinstance(value, str) or value == EMPTY_GENERATION or ID.fullmatch(value) is None,
        "invalid_generation_id",
        "generation ID must be a Sage ID other than reserved value 'none'",
    )
    return value


def expected_generation(value: Any, *, allow_none: bool) -> str:
    if allow_none and value == EMPTY_GENERATION:
        return value
    return generation_id(value)


def normalize_text(value: Any, where: str) -> str:
    fail(not isinstance(value, str), "invalid_cues", f"{where} must be text")
    normalized = unicodedata.normalize("NFC", " ".join(value.split())).casefold()
    fail(not normalized, "invalid_cues", f"{where} must be nonempty text")
    fail(len(normalized) > 256, "invalid_cues", f"{where} is too long")
    return normalized


def normalize_cues(value: Any, *, allow_option: bool) -> tuple[dict[str, list[str]], bool]:
    fail(not isinstance(value, dict), "invalid_cues", "cues must be an object")
    allowed = set(CUE_KEYS) | ({"include_non_supported"} if allow_option else set())
    fail(bool(set(value) - allowed), "invalid_cues", "cues contain unknown keys")
    result: dict[str, list[str]] = {}
    for key in CUE_KEYS:
        raw = value.get(key, [])
        fail(not isinstance(raw, list) or len(raw) > 32, "invalid_cues", f"cues.{key} must be a bounded array")
        normalized = [normalize_text(item, f"cues.{key}") for item in raw]
        result[key] = sorted(set(normalized))
    include = value.get("include_non_supported", False)
    fail(not isinstance(include, bool), "invalid_cues", "include_non_supported must be boolean")
    return result, include


def cue_fingerprint(cues: dict[str, list[str]], include_non_supported: bool) -> str:
    selection = {"cues": cues, "include_non_supported": include_non_supported}
    raw = json.dumps(selection, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def utc_instant_key(value: str) -> tuple[str, str]:
    whole_second, _, fraction = value[:-1].partition(".")
    return whole_second, fraction.rstrip("0")


def choice(value: Any, allowed: set[str], where: str, code: str = "invalid_record") -> str:
    fail(not isinstance(value, str) or value not in allowed, code, f"invalid {where}")
    return value


def validate_untrusted_json(value: Any, where: str, depth: int = 0) -> None:
    fail(depth > 8, "invalid_record", f"{where} is too deeply nested")
    if value is None or isinstance(value, (bool, str, int, float)):
        if isinstance(value, str): fail(len(value) > MAX_TEXT, "invalid_record", f"{where} text is too long")
        return
    if isinstance(value, list):
        fail(len(value) > MAX_LIST, "invalid_record", f"{where} is too large")
        for index, item in enumerate(value): validate_untrusted_json(item, f"{where}[{index}]", depth + 1)
        return
    if isinstance(value, dict):
        fail(len(value) > MAX_LIST or any(not isinstance(key, str) for key in value), "invalid_record", f"{where} is invalid")
        for key, item in value.items(): validate_untrusted_json(item, f"{where}.{key}", depth + 1)
        return
    raise ContractError("invalid_record", f"{where} contains an unsupported value")


def validate_supported_gate(record: dict[str, Any]) -> None:
    gate = record["gate_evidence"]
    fail(not isinstance(gate, dict), "invalid_record", "gate_evidence must be an object")
    evidence_class = record["evidence_class"]
    if evidence_class == "scoped_fact":
        exact_object(gate, {"repeatable_check", "environment"}, "scoped_fact gate_evidence")
        text(gate["repeatable_check"], "repeatable_check"); text(gate["environment"], "environment")
    elif evidence_class == "transferable_heuristic":
        allowed = {"contexts", "comparison", "corroboration", "confounder_dispositions", "counterexample_dispositions"}
        fail(bool(set(gate) - allowed), "invalid_record", "transferable gate_evidence has unknown fields")
        required = {"contexts", "confounder_dispositions", "counterexample_dispositions"}
        fail(not required.issubset(gate), "invalid_record", "transferable gate_evidence is incomplete")
        contexts = string_list(gate["contexts"], "contexts", nonempty=True)
        fail(len(contexts) < 2, "invalid_record", "transferable support requires at least two recorded contexts")
        comparison = gate.get("comparison", []); corroboration = gate.get("corroboration", [])
        string_list(comparison, "comparison"); string_list(corroboration, "corroboration")
        fail(not comparison and not corroboration, "invalid_record", "transferable support requires comparison or corroboration")
        string_list(gate["confounder_dispositions"], "confounder_dispositions", nonempty=True)
        string_list(gate["counterexample_dispositions"], "counterexample_dispositions", nonempty=True)
    else:
        exact_object(gate, {"method", "evidence", "alternative_cause_dispositions"}, "causal gate_evidence")
        choice(gate["method"], {"controlled", "counterfactual", "direct_mechanism"}, "causal method")
        string_list(gate["evidence"], "causal evidence", nonempty=True)
        string_list(gate["alternative_cause_dispositions"], "alternative_cause_dispositions", nonempty=True)


def canonical_record(value: Any, *, stored: bool = False) -> dict[str, Any]:
    record = copy.deepcopy(exact_object(value, RECORD_FIELDS, "record"))
    fail(type(record["v"]) is not int or record["v"] != 1, "invalid_record", "record version must be 1")
    identifier(record["id"], "knowledge ID")
    revision = positive(record["revision"], "revision")
    if revision == 1:
        fail(record["prior_revision"] is not None, "invalid_record", "revision 1 must have null prior_revision")
    else:
        positive(record["prior_revision"], "prior_revision")
        fail(record["prior_revision"] != revision - 1, "invalid_record", "prior_revision must be the preceding revision")
    choice(record["status"], STATUSES, "status"); choice(record["evidence_class"], EVIDENCE_CLASSES, "evidence_class")
    for field in ("gate_rationale", "rule", "falsifier", "evidence_summary"): text(record[field], field)
    recognizer, _ = normalize_cues(record["recognizer"], allow_option=False)
    qualifier = exact_object(record["qualifier"], {"all", "none"}, "qualifier")
    qualifier_all, _ = normalize_cues(qualifier["all"], allow_option=False)
    qualifier_none, _ = normalize_cues(qualifier["none"], allow_option=False)
    record["recognizer"] = recognizer; record["qualifier"] = {"all": qualifier_all, "none": qualifier_none}
    provenance = record["provenance"]
    fail(not isinstance(provenance, list) or not provenance or len(provenance) > MAX_LIST, "invalid_record", "provenance must be a bounded nonempty array")
    for index, item in enumerate(provenance):
        exact_object(item, {"run_id", "locator"}, f"provenance[{index}]")
        identifier(item["run_id"], "provenance run_id"); text(item["locator"], "provenance locator")
    fail(len({(item["run_id"], item["locator"]) for item in provenance}) != len(provenance), "invalid_record", "duplicate provenance")
    string_list(record["alternative_explanations"], "alternative_explanations")
    string_list(record["counterevidence"], "counterevidence")
    refutation = exact_object(record["refutation"], {"actor", "outcome", "findings", "evidence"}, "refutation")
    native_handle(refutation["actor"], "refutation actor")
    choice(refutation["outcome"], {"passed", "failed", "unsupported"}, "refutation outcome")
    string_list(refutation["evidence"], "refutation evidence", nonempty=True)
    fail(not isinstance(refutation["findings"], list) or len(refutation["findings"]) > MAX_LIST, "invalid_record", "refutation findings must be an array")
    finding_ids: list[str] = []
    for index, finding in enumerate(refutation["findings"]):
        exact_object(finding, {"id", "summary", "evidence"}, f"refutation.findings[{index}]")
        finding_ids.append(identifier(finding["id"], "refutation finding ID"))
        text(finding["summary"], "refutation finding summary")
        string_list(finding["evidence"], "refutation finding evidence", nonempty=True)
    fail(len(finding_ids) != len(set(finding_ids)), "invalid_record", "duplicate refutation finding ID")
    review = record["review"]
    fail(not isinstance(review, dict), "invalid_record", "review must be an object")
    allowed_review = {"actor", "outcome", "dispositions", "gate_decision", "retirement_basis", "retirement_reason"}
    required_review = {"actor", "outcome", "dispositions", "gate_decision"}
    fail(bool(set(review) - allowed_review) or not required_review.issubset(review), "invalid_record", "review fields are invalid")
    native_handle(review["actor"], "review actor"); choice(review["outcome"], {"passed", "failed", "unsupported"}, "review outcome")
    fail(review["actor"] == refutation["actor"], "invalid_record", "refuter and reviewer must be distinct")
    text(review["gate_decision"], "gate_decision")
    fail(not isinstance(review["dispositions"], list) or len(review["dispositions"]) > MAX_LIST, "invalid_record", "review dispositions must be an array")
    disposition_ids: list[str] = []
    for index, disposition in enumerate(review["dispositions"]):
        exact_object(disposition, {"finding_id", "disposition", "rationale", "evidence"}, f"review.dispositions[{index}]")
        disposition_ids.append(identifier(disposition["finding_id"], "disposition finding_id"))
        choice(disposition["disposition"], {"resolved", "accepted", "rejected"}, "finding disposition")
        text(disposition["rationale"], "disposition rationale")
        string_list(disposition["evidence"], "disposition evidence", nonempty=True)
    fail(len(disposition_ids) != len(set(disposition_ids)) or set(disposition_ids) != set(finding_ids), "invalid_record", "review must disposition every refutation finding exactly once")
    if "retirement_basis" in review:
        choice(review["retirement_basis"], {"explicit_decision", "superseded", "scope_obsolete"}, "retirement_basis")
        text(review.get("retirement_reason"), "retirement_reason")
    fail("retirement_reason" in review and "retirement_basis" not in review, "invalid_record", "retirement_reason requires retirement_basis")
    utc_timestamp(record["created_at"], "created_at"); utc_timestamp(record["reviewed_at"], "reviewed_at")
    fail(utc_instant_key(record["reviewed_at"]) < utc_instant_key(record["created_at"]), "invalid_record", "reviewed_at precedes created_at")
    validate_untrusted_json(record["gate_evidence"], "gate_evidence")
    if record["status"] == "supported":
        validate_supported_gate(record)
        fail(review["gate_decision"] != "supported", "invalid_record", "supported record requires a supported gate decision")
    if stored:
        fail(record != value, "invalid_record", "stored record cues are not canonical")
        fail(refutation["outcome"] != "passed" or review["outcome"] != "passed", "invalid_record", "stored record did not pass refutation and review")
    return record


def source_catalog(paths: Any) -> tuple[dict[str, dict[str, Any]], list[str]]:
    fail(not isinstance(paths, list) or not paths or len(paths) > MAX_LIST, "invalid_proposal", "source_runs must be a bounded nonempty array")
    resolved_paths: list[Path] = []
    for value in paths:
        fail(not isinstance(value, str) or not value, "invalid_proposal", "source run path must be text")
        resolved_paths.append(Path(value).resolve())
    fail(len(resolved_paths) != len(set(resolved_paths)), "invalid_proposal", "duplicate source run path")
    catalog: dict[str, dict[str, Any]] = {}
    for path in resolved_paths:
        rows, raw = read_events(path / "events.jsonl"); state = validate_run(rows, terminal=True); run_id = state["run_id"]
        fail(run_id in catalog, "invalid_proposal", f"duplicate source run ID: {run_id}")
        catalog[run_id] = {
            "path": str(path),
            "events_sha256": hashlib.sha256(raw).hexdigest(),
            "events": {row["event_id"] for row in rows},
            "evidence": {row["payload"]["evidence_id"] for row in rows if row["type"] == "evidence.recorded"},
            "external": {row["payload"]["locator"] for row in rows if row["type"] == "evidence.recorded" and row["payload"]["sha256"] is not None},
        }
    return catalog, sorted(catalog)


def reference_exists(catalog: dict[str, dict[str, Any]], run_id: str, locator: str) -> bool:
    source = catalog.get(run_id)
    if source is None: return False
    if locator in source["external"]: return True
    if locator in source["events"] or locator in source["evidence"]: return True
    if locator.startswith("events.jsonl#"):
        reference = locator.removeprefix("events.jsonl#")
        return reference in source["events"] or reference in source["evidence"]
    return False


def validate_qualified_reference(value: str, catalog: dict[str, dict[str, Any]], where: str) -> None:
    text(value, where)
    fail(":" not in value, "invalid_reference", f"{where} must be qualified by source run ID")
    run_id, locator = value.split(":", 1)
    fail(not reference_exists(catalog, run_id, locator), "invalid_reference", f"unresolved {where}: {value}")


def validate_record_references(record: dict[str, Any], catalog: dict[str, dict[str, Any]], source_ids: list[str]) -> None:
    provenance_runs: set[str] = set()
    for item in record["provenance"]:
        provenance_runs.add(item["run_id"])
        fail(not reference_exists(catalog, item["run_id"], item["locator"]), "invalid_reference", f"unresolved provenance: {item}")
    fail(provenance_runs != set(source_ids), "invalid_reference", "provenance run IDs must exactly cover source_runs")
    for index, value in enumerate(record["counterevidence"]): validate_qualified_reference(value, catalog, f"counterevidence[{index}]")
    for index, value in enumerate(record["refutation"]["evidence"]): validate_qualified_reference(value, catalog, f"refutation.evidence[{index}]")
    for finding in record["refutation"]["findings"]:
        for value in finding["evidence"]: validate_qualified_reference(value, catalog, "refutation finding evidence")
    for disposition in record["review"]["dispositions"]:
        for value in disposition["evidence"]: validate_qualified_reference(value, catalog, "review disposition evidence")
    if record["status"] == "supported":
        for field in ("comparison", "corroboration", "evidence"):
            for value in record["gate_evidence"].get(field, []): validate_qualified_reference(value, catalog, f"gate_evidence.{field}")


def safe_relative(value: Any) -> str:
    fail(not isinstance(value, str), "invalid_generation", "manifest path must be text")
    pure = PurePosixPath(value)
    fail(pure.is_absolute() or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts), "invalid_generation", f"unsafe manifest path: {value}")
    fail(str(pure) != value or value == "manifest.json", "invalid_generation", f"noncanonical manifest path: {value}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_generation(path: Path, expected_id: str | None = None, *, staging: bool = False) -> dict[str, Any]:
    fail(not path.is_dir() or path.is_symlink(), "invalid_generation", f"generation is missing or unsafe: {path}")
    manifest_path = path / "manifest.json"
    fail(not manifest_path.is_file() or manifest_path.is_symlink(), "invalid_generation", "generation manifest is missing or unsafe")
    manifest = exact_object(read_json(manifest_path), {"v", "generation_id", "parent_generation_id", "files", "authors"}, "manifest", "invalid_generation")
    fail(type(manifest["v"]) is not int or manifest["v"] != 1, "invalid_generation", "manifest version must be 1")
    actual_id = generation_id(manifest["generation_id"])
    parent_id = manifest["parent_generation_id"]
    fail(parent_id != EMPTY_GENERATION and (not isinstance(parent_id, str) or ID.fullmatch(parent_id) is None), "invalid_generation", "invalid parent generation ID")
    fail(expected_id is not None and actual_id != expected_id, "invalid_generation", "manifest generation ID mismatch")
    fail(not staging and path.name != actual_id, "invalid_generation", "generation directory name mismatch")
    files = manifest["files"]
    fail(not isinstance(files, list) or not files, "invalid_generation", "manifest files must be a nonempty array")
    listed: list[str] = []
    for index, entry in enumerate(files):
        exact_object(entry, {"path", "sha256"}, f"manifest.files[{index}]", "invalid_generation")
        relative = safe_relative(entry["path"]); listed.append(relative)
        fail(not isinstance(entry["sha256"], str) or len(entry["sha256"]) != 64 or any(char not in "0123456789abcdef" for char in entry["sha256"]), "invalid_generation", "invalid manifest sha256")
    fail(listed != sorted(listed) or len(listed) != len(set(listed)), "invalid_generation", "manifest file paths must be unique and sorted")
    disk_files: set[str] = set(); disk_directories: set[str] = set()
    for child in path.rglob("*"):
        mode = child.lstat().st_mode
        fail(stat.S_ISLNK(mode), "invalid_generation", f"generation contains a symlink: {child}")
        fail(not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)), "invalid_generation", f"generation contains a special file: {child}")
        relative_child = child.relative_to(path).as_posix()
        if stat.S_ISREG(mode): disk_files.add(relative_child)
        else: disk_directories.add(relative_child)
    fail(disk_files != set(listed) | {"manifest.json"}, "invalid_generation", "generation has missing or extra files")
    fail(disk_directories != {"records"}, "invalid_generation", "generation has missing or extra directories")
    for entry in files:
        if sha256(path / entry["path"]) != entry["sha256"]:
            raise ContractError("generation_hash_mismatch", f"hash mismatch for {entry['path']}")
    index = exact_object(read_json(path / "index.json"), {"v", "generation_id", "records"}, "index", "invalid_generation")
    fail(type(index["v"]) is not int or index["v"] != 1 or index["generation_id"] != actual_id, "invalid_generation", "invalid index identity")
    fail(not isinstance(index["records"], list), "invalid_generation", "index records must be an array")
    records: dict[str, dict[str, Any]] = {}; expected_entries: list[dict[str, Any]] = []
    for index_entry in index["records"]:
        fields = {"id", "revision", "status", "evidence_class", "recognizer", "qualifier", "record_path"}
        exact_object(index_entry, fields, "index record", "invalid_generation")
        record_id = identifier(index_entry["id"], "index record ID", "invalid_generation")
        fail(record_id in records, "invalid_generation", f"duplicate record ID: {record_id}")
        record_path = f"records/{record_id}.json"
        fail(index_entry["record_path"] != record_path, "invalid_generation", "index record path mismatch")
        record = canonical_record(read_json(path / record_path), stored=True)
        derived = {key: record[key] for key in ("id", "revision", "status", "evidence_class", "recognizer", "qualifier")}
        derived["record_path"] = record_path
        fail(index_entry != derived, "invalid_generation", f"index metadata mismatch for {record_id}")
        records[record_id] = record; expected_entries.append(derived)
    fail(index["records"] != sorted(expected_entries, key=lambda item: item["id"]), "invalid_generation", "index records must be sorted")
    expected_paths = {"index.json"} | {f"records/{record_id}.json" for record_id in records}
    fail(set(listed) != expected_paths, "invalid_generation", "manifest does not exactly cover index records")
    authors = manifest["authors"]
    fail(not isinstance(authors, list), "invalid_generation", "manifest authors must be an array")
    author_ids: list[str] = []
    for author in authors:
        exact_object(author, {"id", "action", "proposer", "refuter", "reviewer", "source_run_ids"}, "manifest author", "invalid_generation")
        author_ids.append(identifier(author["id"], "author record ID", "invalid_generation"))
        choice(author["action"], ACTIONS, "author action", "invalid_generation")
        for role in ("proposer", "refuter", "reviewer"): native_handle(author[role], f"{role} actor")
        fail(len({author["proposer"], author["refuter"], author["reviewer"]}) != 3, "invalid_generation", "promotion actors must be distinct")
        string_list(author["source_run_ids"], "author source_run_ids", nonempty=True, code="invalid_generation")
        record = records.get(author["id"])
        fail(record is None or author["refuter"] != record["refutation"]["actor"] or author["reviewer"] != record["review"]["actor"], "invalid_generation", "manifest actor binding does not match record")
    fail(author_ids != sorted(records) or len(author_ids) != len(set(author_ids)), "invalid_generation", "manifest authors must exactly cover sorted records")
    return {"generation_id": actual_id, "parent_generation_id": parent_id, "manifest": manifest, "manifest_sha256": sha256(manifest_path), "records": records}


def validate_staging(store: Path) -> None:
    """Recognize scratch paths without treating partial bytes as published history."""
    root = store / '.staging'
    fail(root.is_symlink(), 'invalid_staging', 'staging must not be a symlink')
    if not root.exists(): return
    fail(not root.is_dir(), 'invalid_staging', 'staging must be a directory')
    for operation in root.iterdir():
        fail(operation.is_symlink() or not operation.is_dir() or re.fullmatch(r'stage-[a-z0-9_]{8}', operation.name) is None,
             'invalid_staging', f'unrecognized staging operation: {operation.name}')
        for child in operation.rglob('*'):
            mode = child.lstat().st_mode
            relative = child.relative_to(operation)
            fail(stat.S_ISLNK(mode) or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)),
                 'invalid_staging', f'unsafe staging path: {relative}')
            if stat.S_ISDIR(mode):
                valid = relative.as_posix() == 'records'
            else:
                name = child.name
                # atomic_write may itself be interrupted before replacing a JSON file.
                temporary = re.fullmatch(r'\.(.+\.json)\.[a-z0-9_]{8}', name)
                if temporary: name = temporary.group(1)
                valid = ((len(relative.parts) == 1 and name in {'index.json', 'manifest.json'}) or
                         (len(relative.parts) == 2 and relative.parts[0] == 'records' and
                          name.endswith('.json') and ID.fullmatch(name[:-5]) is not None))
            fail(not valid, 'invalid_staging', f'unrecognized staging path: {relative}')


def validated_generations(store: Path) -> dict[str, dict[str, Any]]:
    validate_staging(store)
    root = store / "generations"
    fail(root.is_symlink(), "invalid_store", "generations must not be a symlink")
    if not root.exists(): return {}
    fail(not root.is_dir() or root.is_symlink(), "invalid_store", "generations must be a directory")
    generations: dict[str, dict[str, Any]] = {}
    for child in sorted(root.iterdir()):
        child_id = generation_id(child.name); generations[child_id] = validate_generation(child, child_id)
    for generation, value in generations.items():
        parent = value["parent_generation_id"]
        fail(parent == generation or (parent != EMPTY_GENERATION and parent not in generations), "invalid_generation", f"invalid parent for generation {generation}")
        seen: set[str] = set(); cursor = generation
        while cursor != EMPTY_GENERATION:
            fail(cursor in seen, "invalid_generation", f"generation parent cycle at {cursor}")
            seen.add(cursor); cursor = generations[cursor]["parent_generation_id"]
    lineages: dict[str, dict[int, bytes]] = {}
    for value in generations.values():
        for record in value["records"].values():
            revisions = lineages.setdefault(record["id"], {}); record_bytes = encode(record); revision = record["revision"]
            if revision in revisions and revisions[revision] != record_bytes:
                raise ContractError("revision_conflict", f"retained {record['id']} revision {revision} has conflicting bytes")
            revisions[revision] = record_bytes
    for record_id, revisions in lineages.items():
        latest = max(revisions)
        fail(set(revisions) != set(range(1, latest + 1)), "invalid_generation", f"retained lineage for {record_id} has a revision gap")
    return generations


def current_pointer(store: Path) -> tuple[str, bytes | None, dict[str, Any] | None]:
    path = store / "current.json"
    fail(path.is_symlink(), "invalid_store", "current.json must be a regular file")
    if not path.exists(): return EMPTY_GENERATION, None, None
    fail(not path.is_file(), "invalid_store", "current.json must be a regular file")
    raw = path.read_bytes()
    pointer = exact_object(read_json(path), {"v", "generation_id", "manifest_sha256"}, "current pointer", "invalid_store")
    fail(type(pointer["v"]) is not int or pointer["v"] != 1, "invalid_store", "current pointer version must be 1")
    active = generation_id(pointer["generation_id"])
    digest = pointer["manifest_sha256"]
    fail(not isinstance(digest, str) or len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest), "invalid_store", "invalid current manifest hash")
    generation = validate_generation(store / "generations" / active, active)
    fail(digest != generation["manifest_sha256"], "generation_hash_mismatch", "current pointer manifest hash mismatch")
    return active, raw, generation


def require_expected(store: Path, expected: str, token: object = UNSET) -> tuple[bytes | None, dict[str, Any] | None]:
    active, raw, generation = current_pointer(store)
    fail(active != expected, "stale_current", f"expected current {expected}, found {active}")
    if token is not UNSET: fail(raw != token, "stale_current", "current pointer changed during operation")
    return raw, generation


def fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
        try: os.fsync(descriptor)
        finally: os.close(descriptor)
    except OSError:
        pass


def write_generation(path: Path, generation: str, parent: str, records: dict[str, dict[str, Any]], authors: dict[str, dict[str, Any]]) -> dict[str, Any]:
    (path / "records").mkdir(parents=True)
    index_records: list[dict[str, Any]] = []
    for record_id in sorted(records):
        record = records[record_id]; relative = f"records/{record_id}.json"
        atomic_write(path / relative, encode(record))
        entry = {key: record[key] for key in ("id", "revision", "status", "evidence_class", "recognizer", "qualifier")}
        entry["record_path"] = relative; index_records.append(entry)
    atomic_write(path / "index.json", encode({"v": 1, "generation_id": generation, "records": index_records}))
    relatives = ["index.json", *[f"records/{record_id}.json" for record_id in sorted(records)]]
    files = [{"path": relative, "sha256": sha256(path / relative)} for relative in sorted(relatives)]
    manifest = {"v": 1, "generation_id": generation, "parent_generation_id": parent, "files": files, "authors": [authors[key] for key in sorted(authors)]}
    atomic_write(path / "manifest.json", encode(manifest))
    fsync_directory(path / "records"); fsync_directory(path)
    return validate_generation(path, generation, staging=True)


def command_validate(args: argparse.Namespace) -> dict[str, Any]:
    store = Path(args.store_dir).resolve()
    if not store.exists(): return {"ok": True, "current": EMPTY_GENERATION, "generation_count": 0}
    fail(not store.is_dir() or store.is_symlink(), "invalid_store", "store must be a directory")
    allowed = {"current.json", "generations", ".staging"}
    fail(any(child.name not in allowed for child in store.iterdir()), "invalid_store", "store contains unexpected paths")
    generations = validated_generations(store); count = len(generations)
    active, _, _ = current_pointer(store)
    return {"ok": True, "current": active, "generation_count": count}


def qualifier_matches(qualifier: dict[str, dict[str, list[str]]], cues: dict[str, list[str]]) -> bool:
    for key in CUE_KEYS:
        required = qualifier["all"][key]
        if required and not set(required).intersection(cues[key]): return False
        excluded = qualifier["none"][key]
        if excluded and set(excluded).intersection(cues[key]): return False
    return True


def command_retrieve(args: argparse.Namespace) -> dict[str, Any]:
    store = Path(args.store_dir).resolve()
    cues, include_non_supported = normalize_cues(read_json(Path(args.cues).resolve()), allow_option=True)
    try: limit = int(args.limit)
    except (TypeError, ValueError) as exc: raise ContractError("invalid_limit", "limit must be an integer between 1 and 100") from exc
    fail(limit < 1 or limit > 100, "invalid_limit", "limit must be between 1 and 100")
    cards = getattr(args, "cards", False)
    budget = getattr(args, "max_bytes", None)
    fail(budget is not None and (not cards or budget < 1024), "invalid_limit", "max-bytes requires --cards and at least 1024 bytes")
    record_id = getattr(args, "record_id", None)
    if record_id is not None:
        identifier(record_id, "record ID"); fail(not cards, "invalid_arguments", "record-id requires --cards")
    active, _, generation = current_pointer(store); fingerprint = cue_fingerprint(cues, include_non_supported)
    if generation is None and not cards:
        return {"generation_id": EMPTY_GENERATION, "cue_fingerprint": fingerprint, "retrieval_status": "no_match", "matches": []}
    candidates: list[tuple[int, int, str, dict[str, Any], str]] = []
    for candidate_id, record in (generation["records"].items() if generation else []):
        if record_id is not None and candidate_id != record_id: continue
        if record["status"] in {"refuted", "retired"}: continue
        if record["status"] != "supported" and not include_non_supported: continue
        intersections = []
        for key in CUE_KEYS:
            values = sorted(set(record["recognizer"][key]).intersection(cues[key]))
            if values: intersections.append(f"{key}={','.join(values)}")
        if not intersections or not qualifier_matches(record["qualifier"], cues): continue
        reason = "recognizer intersection: " + "; ".join(intersections) + "; qualifier satisfied"
        status_priority = {"supported": 0, "provisional": 1, "contested": 2}[record["status"]]
        score = sum(len(set(record["recognizer"][key]).intersection(cues[key])) for key in CUE_KEYS)
        candidates.append((-score, status_priority, candidate_id, record, reason))
    candidates.sort(key=lambda item: (item[0], item[1], item[2], item[3]["revision"]))
    matches = []
    for _, _, _, record, reason in candidates[:limit]:
        match = {key: copy.deepcopy(record[key]) for key in (
            "id", "revision", "status", "evidence_class", "gate_rationale", "rule",
            "qualifier", "falsifier", "evidence_summary", "counterevidence",
        )}
        match["reason"] = reason
        if cards:
            relative = f"records/{record['id']}.json"
            match.update(card_version=1, generation_id=active,
                         record_sha256=next(entry["sha256"] for entry in generation["manifest"]["files"] if entry["path"] == relative),
                         record_locator=str(store / "generations" / active / relative),
                         gate_evidence=copy.deepcopy(record["gate_evidence"]),
                         alternative_explanations=copy.deepcopy(record["alternative_explanations"]))
        matches.append(match)
    result = {"generation_id": active, "cue_fingerprint": fingerprint, "retrieval_status": "matched" if matches else "no_match", "matches": matches}
    if cards:
        result.update(card_version=1, manifest_sha256=generation["manifest_sha256"] if generation else None,
                      candidate_count=len(candidates), withheld_count=len(candidates) - len(matches),
                      max_bytes=budget, drill_down="Use --record-id ID with these cues; complete IDs are in the validated generation index.json.")
        # Include the root-mode envelope in the actual wire budget. Never truncate a card.
        if getattr(args, "runtime_root", None) is not None: result["store_dir"] = args.store_dir
        def wire_size() -> int:
            return len((json.dumps(result, allow_nan=False, sort_keys=True) + "\n").encode("utf-8"))
        while budget is not None and wire_size() > budget and matches:
            matches.pop(); result["withheld_count"] += 1
            result["retrieval_status"] = "matched" if matches else "no_match"
        fail(bool(candidates) and not matches, "budget_too_small", "Eligible cards were withheld; increase max-bytes or use --record-id with a larger budget. No cards were loaded.")
        fail(budget is not None and wire_size() > budget, "invalid_limit", "budget cannot fit the receipt; increase max-bytes")
    return result


def command_revalidate(args: argparse.Namespace) -> dict[str, Any]:
    """Diagnose every supplied prior selection, independently of recommendation rank."""
    cues, inclusive = normalize_cues(read_json(Path(args.cues).resolve()), allow_option=True)
    previous = read_json(Path(args.previous).resolve())
    fail(not isinstance(previous, list) or len(previous) > MAX_LIST, 'invalid_previous', 'previous must be an array of at most 128 selections')
    seen = set()
    for selection in previous:
        exact_object(selection, {'id', 'revision', 'generation_id'}, 'previous selection', 'invalid_previous')
        identifier(selection['id'], 'previous ID', 'invalid_previous')
        positive(selection['revision'], 'previous revision', 'invalid_previous')
        identifier(selection['generation_id'], 'previous generation', 'invalid_previous')
        fail(selection['generation_id'] == EMPTY_GENERATION, 'invalid_previous', 'empty generation cannot contain a selection')
        key = (selection['id'], selection['revision'], selection['generation_id'])
        fail(key in seen, 'invalid_previous', 'duplicate previous selection'); seen.add(key)
    active, _, generation = current_pointer(Path(args.store_dir).resolve())
    diagnostics = []
    for selection in previous:
        record = generation['records'].get(selection['id']) if generation else None
        result = {**selection, 'current_revision': None, 'current_status': None,
                  'qualifier': None, 'eligible': False}
        if record is None:
            diagnostic, reason = 'not_present_in_active_generation', 'Exact ID is absent from the active generation.'
        else:
            result.update(current_revision=record['revision'], current_status=record['status'],
                          qualifier=copy.deepcopy(record['qualifier']))
            intersects = any(set(record['recognizer'][key]).intersection(cues[key]) for key in CUE_KEYS)
            applicable = intersects and qualifier_matches(record['qualifier'], cues)
            status = record['status']
            result['eligible'] = applicable and (status == 'supported' or (inclusive and status in {'provisional', 'contested'}))
            if status in {'refuted', 'retired', 'contested', 'provisional'}:
                diagnostic, reason = status, f'Current status is {status}; diagnostics do not authorize application.'
            elif not applicable:
                diagnostic, reason = 'out_of_scope', 'Current recognizer or qualifier does not match the observed cues.'
            elif record['revision'] != selection['revision']:
                diagnostic, reason = 'revised', 'Active revision differs from the loaded revision; rollback may select an older revision.'
            else:
                diagnostic, reason = 'unchanged_applicable', 'Same revision remains applicable regardless of recommendation ranking.'
            result['recognizer_matches'] = intersects
            result['qualifier_matches'] = qualifier_matches(record['qualifier'], cues)
        result.update(diagnostic=diagnostic, reason=reason)
        diagnostics.append(result)
    return {'generation_id': active, 'manifest_sha256': generation['manifest_sha256'] if generation else None,
            'cue_fingerprint': cue_fingerprint(cues, inclusive), 'diagnostics': diagnostics}


def validate_proposal(value: Any) -> dict[str, Any]:
    fields = {"action", "proposer", "reviewer", "source_runs", "record"}
    if isinstance(value, dict) and "source_hashes" in value: fields.add("source_hashes")
    proposal = exact_object(value, fields, "proposal", "invalid_proposal")
    fail(not isinstance(proposal["action"], str) or proposal["action"] not in ACTIONS, "invalid_proposal", "invalid proposal action")
    for role in ("proposer", "reviewer"): native_handle(proposal[role], f"{role} actor")
    record = canonical_record(proposal["record"])
    fail(proposal["reviewer"] != record["review"]["actor"], "invalid_proposal", "proposal reviewer must own the record review")
    actors = {proposal["proposer"], proposal["reviewer"], record["refutation"]["actor"]}
    fail(len(actors) != 3, "invalid_proposal", "proposer, refuter, and reviewer must be distinct")
    fail(record["refutation"]["outcome"] != "passed", "invalid_proposal", "the proposed action did not pass refutation")
    fail(record["review"]["outcome"] != "passed", "invalid_proposal", "the proposed action did not pass review")
    result = copy.deepcopy(proposal); result["record"] = record
    return result


def validate_source_bindings(proposal: dict[str, Any], catalog: dict[str, Any], root: str | None) -> None:
    hashes = proposal.get("source_hashes")
    if root is not None or "source_hashes" in proposal:
        fail(not isinstance(hashes, dict) or set(hashes) != set(catalog), "invalid_proposal", "source_hashes must bind every selected run ID from discovery")
        for run_id, source in catalog.items():
            fail(hashes[run_id] != source["events_sha256"], "invalid_reference", f"selected source log changed: {run_id}")
            if root is not None:
                resolved = resolve_run(Path(root), run_id)
                fail(str(resolved) != source["path"], "invalid_reference", f"source path does not match central discovery: {run_id}")


def check_transition(action: str, record: dict[str, Any], prior: dict[str, Any] | None) -> None:
    if action == "create":
        fail(prior is not None, "invalid_transition", "create requires a new stable ID")
        fail(record["revision"] != 1 or record["prior_revision"] is not None, "invalid_transition", "create must start at revision 1")
        return
    fail(prior is None, "invalid_transition", f"{action} requires an existing stable ID")
    fail(record["revision"] != prior["revision"] + 1 or record["prior_revision"] != prior["revision"], "invalid_transition", "new revision must link to the greatest retained prior revision")
    fail(record == prior, "invalid_transition", "promotion action must change the record")
    fail(record["status"] == "retired" and action != "retire", "invalid_transition", "an existing record enters retired status only through retire")
    if action == "contest": fail(record["status"] != "contested", "invalid_transition", "contest must set contested status")
    if action == "refute": fail(record["status"] != "refuted", "invalid_transition", "refute must set refuted status")
    if action == "retire":
        fail(record["status"] != "retired", "invalid_transition", "retire must set retired status")
        fail("retirement_basis" not in record["review"], "invalid_transition", "retire requires an intentional retirement basis and reason")
    if action in {"correct", "contest", "refute"}: fail(not record["counterevidence"], "invalid_transition", f"{action} requires preserved counterevidence")


def retained_lineage_prior(store: Path, candidate: dict[str, Any]) -> dict[str, Any] | None:
    generations = validated_generations(store)
    if not generations: return None
    candidate_bytes = encode(candidate)
    revisions: dict[int, tuple[bytes, dict[str, Any]]] = {}
    for retained in generations.values():
        prior = retained["records"].get(candidate["id"])
        if prior is None: continue
        prior_bytes = encode(prior); revision = prior["revision"]
        if revision in revisions and revisions[revision][0] != prior_bytes:
            raise ContractError("revision_conflict", f"retained {candidate['id']} revision {revision} has conflicting bytes")
        revisions[revision] = (prior_bytes, prior)
    if candidate["revision"] in revisions:
        if revisions[candidate["revision"]][0] != candidate_bytes:
            raise ContractError("revision_conflict", f"{candidate['id']} revision {candidate['revision']} already has different bytes")
        raise ContractError("revision_exists", f"{candidate['id']} revision {candidate['revision']} already exists in retained history")
    if not revisions: return None
    latest = max(revisions)
    fail(set(revisions) != set(range(1, latest + 1)), "invalid_generation", f"retained lineage for {candidate['id']} has a revision gap")
    return revisions[latest][1]


def command_stage(args: argparse.Namespace) -> dict[str, Any]:
    new_id = generation_id(args.generation_id); expected = expected_generation(args.expected_current, allow_none=True)
    store = Path(args.store_dir).resolve(); token, current = require_expected(store, expected)
    proposal = validate_proposal(read_json(Path(args.proposal).resolve()))
    catalog, source_ids = source_catalog(proposal["source_runs"]); validate_record_references(proposal["record"], catalog, source_ids)
    runtime_root = getattr(args, "runtime_root", None)
    validate_source_bindings(proposal, catalog, runtime_root)
    records = copy.deepcopy(current["records"] if current else {})
    authors = {item["id"]: copy.deepcopy(item) for item in (current["manifest"]["authors"] if current else [])}
    record = proposal["record"]; record_id = record["id"]
    prior = retained_lineage_prior(store, record)
    check_transition(proposal["action"], record, prior); records[record_id] = record
    authors[record_id] = {
        "id": record_id, "action": proposal["action"], "proposer": proposal["proposer"],
        "refuter": record["refutation"]["actor"], "reviewer": proposal["reviewer"], "source_run_ids": source_ids,
    }
    generations = store / "generations"; target = generations / new_id
    fail(target.exists(), "generation_exists", f"generation already exists: {new_id}")
    generations.mkdir(parents=True, exist_ok=True)
    staging = store / '.staging'; staging.mkdir(exist_ok=True)
    fail(staging.stat().st_dev != generations.stat().st_dev, 'invalid_staging', 'staging and generations must share a filesystem')
    fsync_directory(store)
    temporary = Path(tempfile.mkdtemp(prefix='stage-', dir=staging))
    try:
        built = write_generation(temporary, new_id, expected, records, authors)
        if runtime_root is not None or "source_hashes" in proposal:
            final_catalog, _ = source_catalog(proposal["source_runs"])
            validate_source_bindings(proposal, final_catalog, runtime_root)
        require_expected(store, expected, token); fail(target.exists(), "generation_exists", f"generation appeared during stage: {new_id}")
        os.rename(temporary, target); fsync_directory(generations); fsync_directory(staging)
    finally:
        if temporary.exists(): shutil.rmtree(temporary)
    return {
        "ok": True, "generation_id": new_id, "manifest_sha256": built["manifest_sha256"],
        "prior_generation_id": expected, "action": proposal["action"],
        "record": {"id": record_id, "revision": record["revision"], "status": record["status"]},
    }


def replace_pointer(store: Path, target_id: str, expected: str, *, rollback: bool) -> dict[str, Any]:
    generations = validated_generations(store)
    fail(target_id not in generations, "invalid_generation", f"generation is missing: {target_id}")
    target = generations[target_id]; token, _ = require_expected(store, expected)
    if not rollback: fail(target["parent_generation_id"] != expected, "stale_generation", "target was staged from a different active generation")
    if rollback: fail(expected == EMPTY_GENERATION or target_id == expected, "invalid_transition", "rollback requires a different active generation")
    require_expected(store, expected, token)
    pointer = {"v": 1, "generation_id": target_id, "manifest_sha256": target["manifest_sha256"]}
    atomic_write(store / "current.json", encode(pointer)); fsync_directory(store)
    return {"ok": True, "generation_id": target_id, "previous_generation_id": expected, "manifest_sha256": target["manifest_sha256"]}


def command_activate(args: argparse.Namespace) -> dict[str, Any]:
    return replace_pointer(Path(args.store_dir).resolve(), generation_id(args.generation_id), expected_generation(args.expected_current, allow_none=True), rollback=False)


def command_rollback(args: argparse.Namespace) -> dict[str, Any]:
    return replace_pointer(Path(args.store_dir).resolve(), generation_id(args.generation_id), expected_generation(args.expected_current, allow_none=False), rollback=True)


class CliParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ContractError("invalid_arguments", message)


def parser() -> argparse.ArgumentParser:
    root = CliParser(); commands = root.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate"); validate.set_defaults(func=command_validate)
    retrieve = commands.add_parser("retrieve"); retrieve.add_argument("--cues", required=True); retrieve.add_argument("--limit", required=True); retrieve.add_argument("--cards", action="store_true"); retrieve.add_argument("--max-bytes", type=int); retrieve.add_argument("--record-id"); retrieve.set_defaults(func=command_retrieve)
    revalidate = commands.add_parser('revalidate'); revalidate.add_argument('--cues', required=True); revalidate.add_argument('--previous', required=True); revalidate.set_defaults(func=command_revalidate)
    stage = commands.add_parser("stage"); stage.add_argument("--proposal", required=True); stage.add_argument("--generation-id", required=True); stage.add_argument("--expected-current", required=True); stage.set_defaults(func=command_stage)
    activate = commands.add_parser("activate"); activate.add_argument("--generation-id", required=True); activate.add_argument("--expected-current", required=True); activate.set_defaults(func=command_activate)
    rollback = commands.add_parser("rollback"); rollback.add_argument("--generation-id", required=True); rollback.add_argument("--expected-current", required=True); rollback.set_defaults(func=command_rollback)
    for command in (validate, retrieve, revalidate, stage, activate, rollback):
        target = command.add_mutually_exclusive_group()
        target.add_argument("--store-dir", help="explicit isolated or legacy store")
        target.add_argument("--state-root", help="shared runtime root; defaults match sage_state.py paths")
    return root


def main() -> int:
    try:
        arguments = parser().parse_args()
        shared_root = arguments.store_dir is None
        if shared_root:
            layout = runtime_paths(arguments.state_root)
            arguments.runtime_root = layout["state_root"]
            arguments.store_dir = layout["store_dir"]
        else:
            store = Path(arguments.store_dir).expanduser()
            fail(store.is_symlink(), "invalid_store", f"knowledge store must not be a symlink: {store}")
            arguments.runtime_root = None
            arguments.store_dir = str(store.resolve())
        result = arguments.func(arguments)
        if shared_root: result["store_dir"] = arguments.store_dir
        sys.stdout.write(json.dumps(result, allow_nan=False, sort_keys=True) + "\n"); return 0
    except ContractError as exc:
        exit_code = 3 if exc.code == "io_error" else 2
        sys.stderr.write(json.dumps({"ok": False, "code": exc.code, "message": exc.message}, sort_keys=True) + "\n"); return exit_code
    except OSError as exc:
        sys.stderr.write(json.dumps({"ok": False, "code": "io_error", "message": str(exc)}, sort_keys=True) + "\n"); return 3


if __name__ == "__main__":
    raise SystemExit(main())
