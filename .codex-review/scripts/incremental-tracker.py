#!/usr/bin/env python3
"""Track reviewed commits and return incremental diffs."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "reports" / "review-state.json"
HISTORY_FILE = ROOT / "reports" / "review-history.log"


@dataclass
class ReviewState:
    last_reviewed_commit: str | None = None



def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def load_state() -> ReviewState:
    if not STATE_FILE.exists():
        return ReviewState()
    data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return ReviewState(last_reviewed_commit=data.get("last_reviewed_commit"))


def save_state(state: ReviewState) -> None:
    STATE_FILE.write_text(
        json.dumps({"last_reviewed_commit": state.last_reviewed_commit}, indent=2),
        encoding="utf-8",
    )


def get_incremental_range(state: ReviewState) -> str:
    head = _git("rev-parse", "HEAD")
    if state.last_reviewed_commit:
        return f"{state.last_reviewed_commit}..{head}"
    return "HEAD~1..HEAD"


def mark_reviewed() -> str:
    head = _git("rev-parse", "HEAD")
    state = load_state()
    state.last_reviewed_commit = head
    save_state(state)

    timestamp = datetime.now(timezone.utc).isoformat()
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open("a", encoding="utf-8") as fp:
        fp.write(f"{timestamp} reviewed {head}\n")
    return head


def main() -> int:
    state = load_state()
    print(get_incremental_range(state))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
