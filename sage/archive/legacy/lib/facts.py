"""Allowlisted factual event names for append-only Sage Light run logs."""

from __future__ import annotations

import json
import re
from typing import Any


INTERNAL_FACT_TYPES = frozenset({
    "run.created",
    "run.state_committed",
    "run.handed_over",
    "run.resume_checked",
    "run.closed",
})

USER_FACT_TYPES = frozenset({
    "approval.requested",
    "approval.resolved",
    "artifact.recorded",
    "assumption.recorded",
    "capability.degraded",
    "capability.recorded",
    "capability.restored",
    "decision.recorded",
    "dispatch.recorded",
    "disposition.recorded",
    "evidence.recorded",
    "failure.recorded",
    "finding.recorded",
    "gap.recorded",
    "knowledge.loaded",
    "knowledge.assessed",
    "observation.recorded",
    "outcome.recorded",
    "rail.fired",
    "usage.recorded",
    "verification.recorded",
    "worker.observed",
})

ALL_FACT_TYPES = INTERNAL_FACT_TYPES | USER_FACT_TYPES

PERSISTABLE_CLASSIFICATIONS = frozenset({"public", "internal", "confidential"})
SENSITIVE_KEYS = frozenset({
    "api_key",
    "authorization",
    "capability_token",
    "cookie",
    "credential",
    "credentials",
    "password",
    "private_key",
    "raw_prompt",
    "raw_tool_payload",
    "refresh_token",
    "secret",
    "session_token",
})
SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}", re.IGNORECASE),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)
CONFIDENTIAL_POINTER_FIELDS = frozenset({"sha256", "locator", "purpose", "redaction"})


def validate_fact_payload(payload: Any, classification: str) -> list[str]:
    """Reject raw or obviously restricted content before a fact reaches disk."""
    issues: list[str] = []
    if not isinstance(payload, dict):
        return ["a current-run fact payload must be one JSON object"]
    if classification not in PERSISTABLE_CLASSIFICATIONS:
        return ["restricted or unknown data classification cannot be persisted in a run fact"]
    if len(json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")) > 65536:
        issues.append("a current-run fact payload must not exceed 65536 UTF-8 JSON bytes")
    if classification == "confidential":
        if not payload or not set(payload).issubset(CONFIDENTIAL_POINTER_FIELDS):
            issues.append("confidential facts may persist only a hash, protected locator, purpose, and redaction note")
        digest = payload.get("sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            issues.append("a confidential fact requires a lowercase SHA-256")
        if not isinstance(payload.get("locator"), str) or not payload["locator"].strip():
            issues.append("a confidential fact requires a protected locator")

    def walk(value: Any, depth: int = 0) -> None:
        if depth > 16:
            issues.append("a current-run fact payload exceeds the maximum nesting depth")
            return
        if isinstance(value, dict):
            for raw_key, child in value.items():
                normalized_key = str(raw_key).strip().lower().replace("-", "_")
                if normalized_key in SENSITIVE_KEYS:
                    issues.append("a current-run fact payload contains a restricted or raw-payload field")
                walk(child, depth + 1)
        elif isinstance(value, list):
            for child in value:
                walk(child, depth + 1)
        elif isinstance(value, str) and any(pattern.search(value) for pattern in SENSITIVE_VALUE_PATTERNS):
            issues.append("a current-run fact payload appears to contain restricted credential material")

    walk(payload)
    return list(dict.fromkeys(issues))
