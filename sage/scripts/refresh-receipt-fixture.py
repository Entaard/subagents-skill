#!/usr/bin/env python3
"""Deterministically refresh the install/update/uninstall receipt chain."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import unicodedata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
INSTALL_PATH = ROOT / "artifacts/fixtures/ownership-receipt.example.json"
UPDATE_PATH = ROOT / "artifacts/fixtures/ownership-receipt.update.example.json"
UNINSTALL_PATH = ROOT / "artifacts/fixtures/ownership-receipt.uninstall.example.json"


def normalize(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            normalized_key = unicodedata.normalize("NFC", key)
            if normalized_key in result:
                raise ValueError(f"normalized key collision: {normalized_key!r}")
            result[normalized_key] = normalize(child)
        return result
    return value


def digest(value: Any) -> str:
    encoded = json.dumps(normalize(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def intent_projection(receipt: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "receipt_version", "installation_id", "mode", "installer_version", "source",
        "protected_paths", "roots", "entries", "config_entries", "backups",
        "retention_policies", "preservation",
    )
    operation = receipt["operation"]
    projection = {field: receipt[field] for field in fields}
    projection["operation"] = {
        "operation_id": operation["operation_id"],
        "kind": operation["kind"],
        "prior_receipt_sha256": operation["prior_receipt_sha256"],
    }
    return projection


def resource(path: str, object_id: str, ancestors: list[str]) -> dict[str, Any]:
    return {
        "provider": "posix-fixture", "volume_id": "volume-1", "object_id": object_id,
        "ancestor_object_ids": ancestors, "case_sensitivity": "sensitive", "unicode_normalization": "NFC",
        "resolved_path_sha256": hashlib.sha256(path.encode("utf-8")).hexdigest(),
    }


def identity(inode: int, chain: str, verified_at: str) -> dict[str, Any]:
    return {"device": 1, "inode": inode, "link_count": 1, "ancestor_chain_sha256": chain * 64, "symlink_target_sha256": None, "verified_at": verified_at}


def present_subject(entry_id: str, subject_kind: str, target_resource: dict[str, Any], target_identity: dict[str, Any], expected_type: str, marker: str | None, content: str | None, selector_state: str | None, basis: str, basis_sha256: str | None = None) -> dict[str, Any]:
    return {
        "entry_id": entry_id, "subject_kind": subject_kind, "state": "present", "basis": basis, "basis_sha256": basis_sha256,
        "target_path_sha256": target_resource["resolved_path_sha256"], "resolved_resource_identity": target_resource,
        "ancestor_chain_sha256": target_identity["ancestor_chain_sha256"], "device": target_identity["device"], "inode": target_identity["inode"],
        "link_count": target_identity["link_count"], "expected_type": expected_type, "observed_type": expected_type,
        "ownership_marker_sha256": marker, "content_sha256": content, "symlink_target_sha256": target_identity["symlink_target_sha256"],
        "selector_state": selector_state, "parent_resource_identity": None, "parent_identity": None,
    }


def absent_subject(entry: dict[str, Any], subject_kind: str) -> dict[str, Any]:
    target_resource = entry["resource_identity"] if subject_kind == "entry" else entry["current_resource_identity"]
    return {
        "entry_id": entry["entry_id"], "subject_kind": subject_kind, "state": "absent", "basis": "live_parent", "basis_sha256": None,
        "target_path_sha256": target_resource["resolved_path_sha256"], "resolved_resource_identity": None, "ancestor_chain_sha256": None,
        "device": None, "inode": None, "link_count": None, "expected_type": entry["expected_type"] if subject_kind == "entry" else "file",
        "observed_type": None, "ownership_marker_sha256": None, "content_sha256": None, "symlink_target_sha256": None,
        "selector_state": "absent" if subject_kind == "config" else None,
        "parent_resource_identity": entry["parent_resource_identity"], "parent_identity": entry["parent_identity"],
    }


def entry_subject(entry: dict[str, Any], basis: str, basis_sha256: str | None = None) -> dict[str, Any]:
    marker = hashlib.sha256(entry["ownership_marker"].encode("utf-8")).hexdigest()
    return present_subject(entry["entry_id"], "entry", entry["resource_identity"], entry["identity"], entry["expected_type"], marker, entry.get("content_sha256"), None, basis, basis_sha256)


def config_subject(entry: dict[str, Any], basis: str, basis_sha256: str | None = None) -> dict[str, Any]:
    marker = hashlib.sha256((entry["selector"] + "\n" + entry["installed_digest"]).encode("utf-8")).hexdigest()
    return present_subject(entry["entry_id"], "config", entry["current_resource_identity"], entry["current_identity"], "file", marker, entry["installed_digest"], "present", basis, basis_sha256)


def backup_original_subject(backup: dict[str, Any], owner: dict[str, Any]) -> dict[str, Any]:
    if backup["owner_kind"] == "entry":
        marker = None
        selector_state = None
    else:
        selector_state = owner["prior_state"]
        marker = None if selector_state == "absent" else hashlib.sha256((owner["selector"] + "\n" + (owner["prior_content_sha256"] or "")).encode("utf-8")).hexdigest()
    return present_subject(backup["owner_entry_id"], backup["owner_kind"], backup["original_resource_identity"], backup["original_identity"], backup["original_type"], marker, backup["sha256"], selector_state, "backup_original")


def backup_subject(backup: dict[str, Any], state: str) -> dict[str, Any]:
    if state == "present":
        target_identity = backup["backup_identity"]
        return {
            "backup_id": backup["backup_id"], "state": "present", "basis": "intended_receipt",
            "target_path_sha256": backup["backup_resource_identity"]["resolved_path_sha256"], "resolved_resource_identity": backup["backup_resource_identity"],
            "ancestor_chain_sha256": target_identity["ancestor_chain_sha256"], "device": target_identity["device"], "inode": target_identity["inode"],
            "link_count": target_identity["link_count"], "observed_type": backup["original_type"], "content_sha256": backup["sha256"],
            "symlink_target_sha256": target_identity["symlink_target_sha256"], "parent_resource_identity": None, "parent_identity": None,
        }
    return {
        "backup_id": backup["backup_id"], "state": "absent", "basis": "live_parent",
        "target_path_sha256": backup["backup_resource_identity"]["resolved_path_sha256"], "resolved_resource_identity": None,
        "ancestor_chain_sha256": None, "device": None, "inode": None, "link_count": None, "observed_type": None,
        "content_sha256": None, "symlink_target_sha256": None,
        "parent_resource_identity": backup["parent_resource_identity"], "parent_identity": backup["parent_identity"],
    }


def proof(operation_id: str, observed_at: str, subjects: list[dict[str, Any]], backups: list[dict[str, Any]]) -> dict[str, Any]:
    return {"proof_version": "StateProof/v2", "operation_id": operation_id, "observed_at": observed_at, "subjects": subjects, "backup_subjects": backups}


def owner_backup(receipt: dict[str, Any], owner_kind: str, owner_id: str, purposes: set[str]) -> dict[str, Any] | None:
    matches = [item for item in receipt["backups"] if item["owner_kind"] == owner_kind and item["owner_entry_id"] == owner_id and item["purpose"] in purposes]
    return matches[0] if len(matches) == 1 else None


def expected_proofs(receipt: dict[str, Any], prior: dict[str, Any] | None, row: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    operation = receipt["operation"]
    kind = operation["kind"]
    phase = row["phase"]
    entries = {item["entry_id"]: item for item in receipt["entries"]}
    configs = {item["entry_id"]: item for item in receipt["config_entries"]}
    backups = {item["backup_id"]: item for item in receipt["backups"]}
    prior_entries = {item["entry_id"]: item for item in prior["entries"]} if prior else {}
    prior_configs = {item["entry_id"]: item for item in prior["config_entries"]} if prior else {}
    prior_backups = {item["backup_id"]: item for item in prior["backups"]} if prior else {}
    prior_digest = digest(prior) if prior else None
    pre: list[dict[str, Any]] = []
    post: list[dict[str, Any]] = []
    pre_backups: list[dict[str, Any]] = []
    post_backups: list[dict[str, Any]] = []
    if kind in {"install", "update"} and phase == "backups_durable":
        for entry_id in row["entry_ids"]:
            candidate = next(backups[key] for key in row["backup_ids"] if backups[key]["owner_kind"] == "entry" and backups[key]["owner_entry_id"] == entry_id)
            subject = entry_subject(prior_entries[entry_id], "prior_receipt", prior_digest) if kind == "update" else backup_original_subject(candidate, entries[entry_id])
            pre.append(subject); post.append(subject)
        for entry_id in row["config_entry_ids"]:
            candidate = next(backups[key] for key in row["backup_ids"] if backups[key]["owner_kind"] == "config" and backups[key]["owner_entry_id"] == entry_id)
            subject = config_subject(prior_configs[entry_id], "prior_receipt", prior_digest) if kind == "update" else backup_original_subject(candidate, configs[entry_id])
            pre.append(subject); post.append(subject)
        pre_backups = [backup_subject(backups[key], "absent") for key in row["backup_ids"]]
        post_backups = [backup_subject(backups[key], "present") for key in row["backup_ids"]]
    elif kind in {"install", "update"} and phase == "replacement_applied":
        for entry_id in row["entry_ids"]:
            current = entries[entry_id]
            displaced = owner_backup(receipt, "entry", entry_id, {"displaced_user"})
            before = entry_subject(prior_entries[entry_id], "prior_receipt", prior_digest) if kind == "update" and entry_id in prior_entries else backup_original_subject(displaced, current) if displaced else absent_subject(current, "entry")
            pre.append(before); post.append(entry_subject(current, "intended_receipt"))
    elif kind in {"install", "update"} and phase == "structured_edit_applied":
        for entry_id in row["config_entry_ids"]:
            current = configs[entry_id]
            prior_backup = owner_backup(receipt, "config", entry_id, {"config_prior"})
            before = config_subject(prior_configs[entry_id], "prior_receipt", prior_digest) if kind == "update" and entry_id in prior_configs else backup_original_subject(prior_backup, current) if prior_backup else absent_subject(current, "config")
            pre.append(before); post.append(config_subject(current, "intended_receipt"))
    elif kind == "uninstall" and phase == "user_content_restored":
        for entry_id in row["entry_ids"]:
            candidate = owner_backup(prior, "entry", entry_id, {"displaced_user"}) if prior else None
            pre.append(entry_subject(prior_entries[entry_id], "prior_receipt", prior_digest)); post.append(backup_original_subject(candidate, entries[entry_id]))
        pre_backups = post_backups = [backup_subject(prior_backups[key], "present") for key in row["backup_ids"]]
    elif kind == "uninstall" and phase == "structured_config_restored":
        for entry_id in row["config_entry_ids"]:
            candidate = owner_backup(prior, "config", entry_id, {"config_prior"}) if prior else None
            pre.append(config_subject(prior_configs[entry_id], "prior_receipt", prior_digest))
            post.append(backup_original_subject(candidate, configs[entry_id]) if candidate else absent_subject(configs[entry_id], "config"))
        pre_backups = post_backups = [backup_subject(prior_backups[key], "present") for key in row["backup_ids"]]
    elif kind == "uninstall" and phase == "owned_entry_removed":
        for entry_id in row["entry_ids"]:
            pre.append(entry_subject(prior_entries[entry_id], "prior_receipt", prior_digest)); post.append(absent_subject(entries[entry_id], "entry"))
    elif kind == "uninstall" and phase == "cleanup_complete":
        pre_backups = [backup_subject(prior_backups[key], "present") for key in row["backup_ids"]]
        post_backups = [backup_subject(prior_backups[key], "absent") for key in row["backup_ids"]]
    return pre, pre_backups, post, post_backups


def row(sequence: int, phase: str, recorded_at: str, *, entries: list[str] | None = None, configs: list[str] | None = None, backups: list[str] | None = None) -> dict[str, Any]:
    return {"sequence": sequence, "phase": phase, "recorded_at": recorded_at, "entry_ids": entries or [], "config_entry_ids": configs or [], "backup_ids": backups or []}


def refreshed(receipt: dict[str, Any], prior: dict[str, Any] | None = None) -> dict[str, Any]:
    operation = receipt["operation"]
    operation["intended_receipt_sha256"] = digest(intent_projection(receipt))
    prior_hash: str | None = None
    for item in operation["journal"]:
        pre, pre_backups, post, post_backups = expected_proofs(receipt, prior, item)
        item["operation_id"] = operation["operation_id"]
        item["intended_receipt_sha256"] = operation["intended_receipt_sha256"]
        item["prior_receipt_sha256"] = operation["prior_receipt_sha256"]
        item["precondition"] = proof(operation["operation_id"], item["recorded_at"], pre, pre_backups)
        item["precondition_sha256"] = digest(item["precondition"])
        item["postcondition"] = proof(operation["operation_id"], item["recorded_at"], post, post_backups)
        item["postcondition_sha256"] = digest(item["postcondition"])
        item["prior_journal_sha256"] = prior_hash
        item.pop("journal_entry_sha256", None)
        item["journal_entry_sha256"] = digest(item)
        prior_hash = item["journal_entry_sha256"]
    return receipt


def install_receipt(seed: dict[str, Any]) -> dict[str, Any]:
    receipt = copy.deepcopy(seed)
    entries = {item["entry_id"]: item for item in receipt["entries"]}
    configs = {item["entry_id"]: item for item in receipt["config_entries"]}
    skill = entries["entry-skill"]
    overlay = entries["entry-overlay"]
    skill["entry_class"] = "replaced"
    skill["content_sha256"] = "e" * 64
    skill["backup_ids"] = ["backup-entry-skill"]
    skill.pop("backup_id", None)
    skill["parent_resource_identity"] = resource("/opt/sage-example/skills", "object-opt-sage-skills", ["object-root", "object-opt", "object-opt-sage"])
    skill["parent_identity"] = identity(1051, "7", "2026-08-31T05:59:00Z")
    overlay["backup_ids"] = []
    overlay.pop("backup_id", None)
    overlay["parent_resource_identity"] = copy.deepcopy(receipt["roots"][1]["resource_identity"])
    overlay["parent_identity"] = copy.deepcopy(receipt["roots"][1]["identity"])
    config = configs["config-explicit-skill"]
    config["current_resource_identity"] = resource(config["config_path"], "object-etc-sage-example-config", ["object-root", "object-etc", "object-etc-sage-example"])
    config["parent_resource_identity"] = resource("/etc/sage-example", "object-etc-sage-example", ["object-root", "object-etc"])
    config["parent_identity"] = identity(1003, "8", "2026-08-31T05:59:00Z")
    config["prior_state"] = "absent"
    config["prior_file_state"] = "present"
    config["prior_content_sha256"] = "d" * 64
    config["prior_identity"] = identity(1200, "9", "2026-08-31T05:59:30Z")
    config["prior_resource_identity"] = resource(config["config_path"], "object-etc-sage-config-prior", ["object-root", "object-etc", "object-etc-sage-example"])
    config["prior_backup_ids"] = ["backup-config-explicit-skill"]
    config.pop("prior_backup_id", None)
    backup_parent_resource = resource("/var/lib/sage-example/backups", "object-var-lib-sage-backups", ["object-root", "object-var", "object-var-lib", "object-var-lib-sage"])
    backup_parent_identity = identity(1800, "1", "2026-08-31T05:59:30Z")
    receipt["backups"] = [
        {
            "backup_id": "backup-entry-skill", "purpose": "displaced_user", "owner_kind": "entry", "owner_entry_id": "entry-skill",
            "original_path": "/opt/sage-example/skills/sage", "original_identity": identity(901, "2", "2026-08-31T05:59:30Z"),
            "original_resource_identity": resource("/opt/sage-example/skills/sage", "object-opt-sage-skills-sage-prior", ["object-root", "object-opt", "object-opt-sage", "object-opt-sage-skills"]),
            "backup_root_id": "state", "backup_relative_path": "backups/entry-skill", "backup_path": "/var/lib/sage-example/backups/entry-skill",
            "original_type": "directory", "mode": "0755", "sha256": "c" * 64, "backup_identity": identity(1901, "3", "2026-08-31T06:00:05Z"),
            "backup_resource_identity": resource("/var/lib/sage-example/backups/entry-skill", "object-var-lib-sage-backup-entry-skill", ["object-root", "object-var", "object-var-lib", "object-var-lib-sage", "object-var-lib-sage-backups"]),
            "parent_identity": copy.deepcopy(backup_parent_identity), "parent_resource_identity": copy.deepcopy(backup_parent_resource), "restored": False,
        },
        {
            "backup_id": "backup-config-explicit-skill", "purpose": "config_prior", "owner_kind": "config", "owner_entry_id": "config-explicit-skill",
            "original_path": config["config_path"], "original_identity": copy.deepcopy(config["prior_identity"]), "original_resource_identity": copy.deepcopy(config["prior_resource_identity"]),
            "backup_root_id": "state", "backup_relative_path": "backups/config-explicit-skill", "backup_path": "/var/lib/sage-example/backups/config-explicit-skill",
            "original_type": "file", "mode": "0644", "sha256": "d" * 64, "backup_identity": identity(1902, "4", "2026-08-31T06:00:05Z"),
            "backup_resource_identity": resource("/var/lib/sage-example/backups/config-explicit-skill", "object-var-lib-sage-backup-config", ["object-root", "object-var", "object-var-lib", "object-var-lib-sage", "object-var-lib-sage-backups"]),
            "parent_identity": copy.deepcopy(backup_parent_identity), "parent_resource_identity": copy.deepcopy(backup_parent_resource), "restored": False,
        },
    ]
    receipt["operation"] = {
        "operation_id": "operation-install-1", "kind": "install", "state": "committed", "prior_receipt_sha256": None, "intended_receipt_sha256": "0" * 64,
        "journal": [
            row(1, "preflight_complete", "2026-08-31T06:00:00Z"),
            row(2, "backups_durable", "2026-08-31T06:00:10Z", entries=["entry-skill"], configs=["config-explicit-skill"], backups=["backup-entry-skill", "backup-config-explicit-skill"]),
            row(3, "stage_verified", "2026-08-31T06:00:20Z"),
            row(4, "replacement_applied", "2026-08-31T06:00:30Z", entries=["entry-skill", "entry-overlay"]),
            row(5, "structured_edit_applied", "2026-08-31T06:00:40Z", configs=["config-explicit-skill"]),
            row(6, "health_verified", "2026-08-31T06:00:50Z"), row(7, "receipt_committed", "2026-08-31T06:01:00Z"),
            row(8, "cleanup_complete", "2026-08-31T06:01:10Z"),
        ],
    }
    return refreshed(receipt)


def update_receipt(prior: dict[str, Any]) -> dict[str, Any]:
    receipt = copy.deepcopy(prior)
    entries = {item["entry_id"]: item for item in receipt["entries"]}
    skill = entries["entry-skill"]
    prior_skill = {item["entry_id"]: item for item in prior["entries"]}["entry-skill"]
    skill["resource_identity"] = resource("/opt/sage-example/skills/sage", "object-opt-sage-skills-sage-v2", ["object-root", "object-opt", "object-opt-sage", "object-opt-sage-skills"])
    skill["identity"] = identity(2101, "5", "2026-08-31T07:00:30Z")
    skill["ownership_marker"] = "sage-owned:install-example:entry-skill:v2"
    skill["content_sha256"] = "f" * 64
    rollback = {
        "backup_id": "backup-entry-skill-v1-rollback", "purpose": "operation_rollback", "owner_kind": "entry", "owner_entry_id": "entry-skill",
        "original_path": "/opt/sage-example/skills/sage", "original_identity": copy.deepcopy(prior_skill["identity"]), "original_resource_identity": copy.deepcopy(prior_skill["resource_identity"]),
        "backup_root_id": "state", "backup_relative_path": "backups/entry-skill-v1-rollback", "backup_path": "/var/lib/sage-example/backups/entry-skill-v1-rollback",
        "original_type": "directory", "mode": "0755", "sha256": prior_skill["content_sha256"], "backup_identity": identity(1903, "6", "2026-08-31T07:00:10Z"),
        "backup_resource_identity": resource("/var/lib/sage-example/backups/entry-skill-v1-rollback", "object-var-lib-sage-backup-entry-skill-v1", ["object-root", "object-var", "object-var-lib", "object-var-lib-sage", "object-var-lib-sage-backups"]),
        "parent_identity": copy.deepcopy(receipt["backups"][0]["parent_identity"]), "parent_resource_identity": copy.deepcopy(receipt["backups"][0]["parent_resource_identity"]), "restored": False,
    }
    receipt["backups"].append(rollback)
    skill["backup_ids"].append(rollback["backup_id"])
    receipt["operation"] = {
        "operation_id": "operation-update-1", "kind": "update", "state": "committed", "prior_receipt_sha256": digest(prior), "intended_receipt_sha256": "0" * 64,
        "journal": [
            row(1, "preflight_complete", "2026-08-31T07:00:00Z"),
            row(2, "backups_durable", "2026-08-31T07:00:10Z", entries=["entry-skill"], backups=[rollback["backup_id"]]),
            row(3, "stage_verified", "2026-08-31T07:00:20Z"), row(4, "replacement_applied", "2026-08-31T07:00:30Z", entries=["entry-skill"]),
            row(5, "health_verified", "2026-08-31T07:00:40Z"), row(6, "receipt_committed", "2026-08-31T07:00:50Z"),
            row(7, "cleanup_complete", "2026-08-31T07:01:00Z"),
        ],
    }
    return refreshed(receipt, prior)


def uninstall_receipt(prior: dict[str, Any]) -> dict[str, Any]:
    receipt = copy.deepcopy(prior)
    for item in receipt["backups"]:
        item["restored"] = item["purpose"] in {"displaced_user", "config_prior"}
    all_backups = [item["backup_id"] for item in receipt["backups"]]
    receipt["operation"] = {
        "operation_id": "operation-uninstall-1", "kind": "uninstall", "state": "committed", "prior_receipt_sha256": digest(prior), "intended_receipt_sha256": "0" * 64,
        "journal": [
            row(1, "preflight_complete", "2026-08-31T08:00:00Z"), row(2, "admissions_stopped", "2026-08-31T08:00:10Z"),
            row(3, "processes_stopped", "2026-08-31T08:00:20Z"),
            row(4, "user_content_restored", "2026-08-31T08:00:30Z", entries=["entry-skill"], backups=["backup-entry-skill"]),
            row(5, "structured_config_restored", "2026-08-31T08:00:40Z", configs=["config-explicit-skill"], backups=["backup-config-explicit-skill"]),
            row(6, "owned_entry_removed", "2026-08-31T08:00:50Z", entries=["entry-overlay"]),
            row(7, "removal_verified", "2026-08-31T08:01:00Z"), row(8, "ownership_receipt_removed", "2026-08-31T08:01:10Z"),
            row(9, "cleanup_complete", "2026-08-31T08:01:20Z", backups=all_backups),
        ],
    }
    return refreshed(receipt, prior)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    seed = json.loads(INSTALL_PATH.read_text(encoding="utf-8"))
    install = install_receipt(seed)
    update = update_receipt(install)
    uninstall = uninstall_receipt(update)
    rendered = {
        INSTALL_PATH: json.dumps(install, ensure_ascii=False, indent=2) + "\n",
        UPDATE_PATH: json.dumps(update, ensure_ascii=False, indent=2) + "\n",
        UNINSTALL_PATH: json.dumps(uninstall, ensure_ascii=False, indent=2) + "\n",
    }
    if args.check:
        return 0 if all(path.exists() and path.read_text(encoding="utf-8") == content for path, content in rendered.items()) else 1
    for path, content in rendered.items():
        path.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
