#!/usr/bin/env python3
"""False positive filtering for review findings."""
from __future__ import annotations

import fnmatch
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LEARNINGS_PATH = ROOT / "learnings.json"
DEFAULT_LEARNINGS = {"dismissed_patterns": []}


def load_learnings() -> dict[str, Any]:
    if not LEARNINGS_PATH.exists():
        return DEFAULT_LEARNINGS
    try:
        data = json.loads(LEARNINGS_PATH.read_text(encoding="utf-8"))
        if "dismissed_patterns" not in data:
            data["dismissed_patterns"] = []
        return data
    except json.JSONDecodeError:
        return DEFAULT_LEARNINGS


def _is_noise(item: dict[str, Any], ignore_paths: list[str]) -> bool:
    path = item.get("file", "")
    category = item.get("category", "")
    message = item.get("message", "")

    for pattern in ignore_paths:
        if fnmatch.fnmatch(path, pattern):
            return True

    noise_categories = {
        "whitespace_only_change",
        "rename_without_logic_change",
        "comment_update",
        "snapshot_file",
    }
    if category in noise_categories:
        return True

    if any(token in path.lower() for token in ("snapshot", "fixtures", "data/")):
        return True

    if "docstring" in message.lower() and "only" in message.lower():
        return True

    return False


def filter_findings(findings: list[dict[str, Any]], ignore_paths: list[str] | None = None) -> list[dict[str, Any]]:
    ignore_paths = ignore_paths or []
    learnings = load_learnings()
    dismissed = learnings.get("dismissed_patterns", [])

    filtered = []
    for finding in findings:
        text = f"{finding.get('message', '')} {finding.get('rule_id', '')}".lower()
        if any(pattern.lower() in text for pattern in dismissed):
            continue
        if _is_noise(finding, ignore_paths):
            continue
        filtered.append(finding)
    return filtered


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: false-positive-filter.py <findings.json>")
        return 1

    findings_path = Path(sys.argv[1])
    findings = json.loads(findings_path.read_text(encoding="utf-8"))
    filtered = filter_findings(findings)
    print(json.dumps(filtered, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
