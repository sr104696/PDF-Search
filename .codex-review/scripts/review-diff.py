#!/usr/bin/env python3
"""Offline local code review engine inspired by CodeRabbit workflows."""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from false_positive_filter import filter_findings

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
CONFIG_PATH = ROOT / "config" / "review-rules.yaml"
FINDINGS_DIR = ROOT / "findings"
FIXES_DIR = ROOT / "fixes"
REPORTS_DIR = ROOT / "reports"
INTELLIGENCE_DIR = ROOT / "codebase-intelligence"

DEFAULT_CONFIG = {
    "ignore_paths": ["*.min.js", "vendor/**", "tests/fixtures/**"],
    "custom_checks": [
        {
            "name": "No raw SQL in handlers",
            "pattern": "cursor.execute|raw_query",
            "severity": "critical",
            "message": "Use ORM or parameterized queries",
        }
    ],
}


@dataclass
class Finding:
    severity: str
    confidence: float
    file: str
    line: int
    rule_id: str
    message: str
    category: str
    hunk: str


def git_diff(diff_range: str | None) -> str:
    cmd = ["git", "diff"]
    if diff_range:
        cmd.append(diff_range)
    return subprocess.check_output(cmd, text=True)


def parse_diff(diff_text: str) -> dict[str, list[dict[str, Any]]]:
    files: dict[str, list[dict[str, Any]]] = defaultdict(list)
    current_file = None
    current_hunk = None
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
        elif line.startswith("@@") and current_file:
            m = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
            if m:
                start = int(m.group(2))
                count = int(m.group(3) or "1")
                current_hunk = {"start": start, "count": count, "lines": []}
                files[current_file].append(current_hunk)
        elif current_hunk and (line.startswith("+") or line.startswith("-")):
            current_hunk["lines"].append(line)
    return files


def _parse_yaml_fallback(text: str) -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    ignore_paths: list[str] = []
    custom_checks: list[dict[str, str]] = []
    lines = text.splitlines()
    in_ignore = False
    in_custom = False
    current_check: dict[str, str] | None = None

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("ignore_paths:"):
            in_ignore, in_custom = True, False
            continue
        if line.startswith("custom_checks:"):
            in_custom, in_ignore = True, False
            continue

        if in_ignore and line.startswith("-"):
            ignore_paths.append(line.lstrip("-").strip().strip('"'))
        elif in_custom and line.startswith("- name:"):
            if current_check:
                custom_checks.append(current_check)
            current_check = {"name": line.split(":", 1)[1].strip().strip('"')}
        elif in_custom and current_check and ":" in line:
            k, v = line.split(":", 1)
            current_check[k.strip()] = v.strip().strip('"')

    if current_check:
        custom_checks.append(current_check)

    if ignore_paths:
        config["ignore_paths"] = ignore_paths
    if custom_checks:
        config["custom_checks"] = custom_checks
    return config


def load_config() -> dict[str, Any]:
    text = CONFIG_PATH.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text)
        return {**DEFAULT_CONFIG, **(data or {})}
    return _parse_yaml_fallback(text)


def analyze_hunk(file_path: str, hunk: dict[str, Any], config: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    added_lines = [line[1:] for line in hunk["lines"] if line.startswith("+") and not line.startswith("+++")]
    added_text = "\n".join(added_lines)

    def add(sev: str, conf: float, rule_id: str, msg: str, category: str) -> None:
        findings.append(
            Finding(
                severity=sev,
                confidence=conf,
                file=file_path,
                line=hunk["start"],
                rule_id=rule_id,
                message=msg,
                category=category,
                hunk=added_text[:500],
            )
        )

    if re.search(r"(api[_-]?key|secret|password)\s*=\s*['\"][^'\"]+['\"]", added_text, re.I):
        add("critical", 0.92, "hardcoded_secret", "Potential hardcoded secret detected.", "security_vulnerability")
    if re.search(r"cursor\.execute\s*\(f?['\"]", added_text):
        add("critical", 0.87, "raw_sql", "Potential raw SQL execution pattern.", "security_vulnerability")
    if "eval(" in added_text or "exec(" in added_text:
        add("critical", 0.80, "unsafe_eval", "Unsafe dynamic execution detected.", "security_vulnerability")
    if re.search(r"for .* in .*:\n\s*for .* in", added_text, re.M):
        add("warning", 0.65, "nested_loop", "Nested loop may cause performance regression.", "performance_regression")
    if re.search(r"except\s+Exception\s*:\s*pass", added_text):
        add("warning", 0.72, "swallowed_exception", "Exception is swallowed without handling.", "missing_error_handling")
    if "TODO" in added_text:
        add("suggestion", 0.60, "todo_added", "TODO introduced; track with issue if production bound.", "minor_refactor_opportunity")

    for check in config.get("custom_checks", []):
        pattern = check.get("pattern")
        if pattern and re.search(pattern, added_text):
            add(check.get("severity", "warning"), 0.70, check.get("name", "custom_check"), check.get("message", "Custom check matched."), "custom_check")

    return findings


def build_intelligence() -> tuple[dict[str, Any], dict[str, Any]]:
    symbols: dict[str, list[dict[str, Any]]] = defaultdict(list)
    edges: list[dict[str, str]] = []
    py_files = list(REPO_ROOT.rglob("*.py"))

    for file in py_files:
        if ".venv" in file.parts or ".codex-review" in file.parts:
            continue
        rel = str(file.relative_to(REPO_ROOT))
        text = file.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                symbols[rel].append({"name": node.name, "line": node.lineno, "type": type(node).__name__})
            if isinstance(node, ast.Import):
                for name in node.names:
                    edges.append({"from": rel, "to": name.name, "type": "import"})
            if isinstance(node, ast.ImportFrom) and node.module:
                edges.append({"from": rel, "to": node.module, "type": "import_from"})

    graph = {"generated_at": datetime.now(timezone.utc).isoformat(), "nodes": sorted(symbols.keys()), "edges": edges}
    index = {"generated_at": datetime.now(timezone.utc).isoformat(), "symbols": symbols}
    return graph, index


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def categorize(findings: list[Finding]) -> dict[str, list[Finding]]:
    out = {"critical": [], "warnings": [], "suggestions": []}
    for f in findings:
        if f.severity == "critical":
            out["critical"].append(f)
        elif f.severity == "warning":
            out["warnings"].append(f)
        else:
            out["suggestions"].append(f)
    return out


def assess_ship_status(grouped: dict[str, list[Finding]]) -> str:
    if grouped["critical"]:
        return "Critical"
    if len(grouped["warnings"]) > 2:
        return "Needs Work"
    return "Ship"


def build_architecture_diagram(changed_files: list[str], graph: dict[str, Any]) -> str:
    lines = ["graph TD"]
    for node in changed_files:
        safe = node.replace("/", "_").replace(".", "_")
        lines.append(f'  {safe}["{node}"]:::changed')
    for edge in graph.get("edges", []):
        src = edge.get("from", "")
        if src in changed_files:
            src_id = src.replace("/", "_").replace(".", "_")
            target = edge.get("to", "external").replace(".", "_").replace("-", "_")
            lines.append(f"  {src_id} --> {target}")
    lines.append("  classDef changed fill:#f9d,stroke:#333,stroke-width:2px;")
    return "\n".join(lines)


def generate_patch_stub(finding: Finding, bucket: str) -> None:
    target = FIXES_DIR / bucket / f"{finding.rule_id}-{Path(finding.file).name}-{finding.line}.patch"
    target.write_text(
        "# Auto-generated fix stub\n"
        f"# File: {finding.file}\n"
        f"# Line: {finding.line}\n"
        f"# Finding: {finding.message}\n"
        "# Apply manually after editing: git apply <patch-file>\n",
        encoding="utf-8",
    )


def write_reports(changed_files: list[str], grouped: dict[str, list[Finding]], graph: dict[str, Any]) -> None:
    status = assess_ship_status(grouped)
    (REPORTS_DIR / "pr-summary.md").write_text(
        "\n".join(
            [
                "# PR Summary",
                "",
                f"- Files changed: {len(changed_files)}",
                f"- Critical issues: {len(grouped['critical'])}",
                f"- Warnings: {len(grouped['warnings'])}",
                f"- Suggestions: {len(grouped['suggestions'])}",
                f"- Recommendation: **{status}**",
                "",
                "## Architecture Impact",
                "Modified components were mapped against import dependencies in `codebase-intelligence/dependency-graph.json`.",
                "",
                "## Auto-fix Commands",
                "Run `git apply .codex-review/fixes/auto-fixable/<patch-file>.patch` for generated patch stubs.",
            ]
        ),
        encoding="utf-8",
    )
    (REPORTS_DIR / "architecture-diagram.mmd").write_text(
        build_architecture_diagram(changed_files, graph), encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--diff-range", default=None, help="Git diff range, e.g. main...HEAD")
    args = parser.parse_args()

    config = load_config()
    diff_text = git_diff(args.diff_range)
    parsed = parse_diff(diff_text)

    graph, index = build_intelligence()
    write_json(INTELLIGENCE_DIR / "dependency-graph.json", graph)
    write_json(INTELLIGENCE_DIR / "symbol-index.json", index)

    findings: list[Finding] = []
    for file, hunks in parsed.items():
        for hunk in hunks:
            findings.extend(analyze_hunk(file, hunk, config))

    filtered = filter_findings([asdict(f) for f in findings], config.get("ignore_paths", []))
    filtered_findings = [Finding(**f) for f in filtered]

    grouped = categorize(filtered_findings)
    for bucket, bucket_findings in grouped.items():
        out_dir = FINDINGS_DIR / bucket
        out_dir.mkdir(parents=True, exist_ok=True)
        for idx, finding in enumerate(bucket_findings, start=1):
            write_json(out_dir / f"{idx:03d}-{finding.rule_id}.json", asdict(finding))
            generate_patch_stub(finding, "auto-fixable" if bucket == "suggestions" else "needs-review")

    write_reports(list(parsed.keys()), grouped, graph)
    print(f"Reviewed {len(parsed)} files and produced {sum(len(v) for v in grouped.values())} findings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
