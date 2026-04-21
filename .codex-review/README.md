# Local CodeRabbit-Inspired Review System

This folder contains an offline, customizable review engine that mirrors core CodeRabbit workflows without SaaS/API dependencies.

## Architecture

- `scripts/review-diff.py`: Main reviewer. Parses git diff hunks, runs heuristic checks, consults codebase intelligence, writes findings, patches, and reports.
- `scripts/incremental-tracker.py`: Tracks the last reviewed commit and returns the next incremental range.
- `scripts/false-positive-filter.py`: Suppresses noisy findings and applies historical dismissals from `learnings.json`.
- `config/review-rules.yaml`: Review profile, severity model, language linter hints, ignore paths, and custom checks.
- `codebase-intelligence/`: Dependency graph and symbol index generated from Python AST scanning.
- `findings/`: Severity buckets (`critical`, `warnings`, `suggestions`) with structured JSON findings.
- `fixes/`: Generated patch stubs split into `auto-fixable` and `needs-review`.
- `reports/`: PR summary, architecture diagram (Mermaid), and incremental history log.

## Feature Mapping to CodeRabbit

- **Line-by-line diff review** → Hunk-level parsing with file/line metadata in findings.
- **Incremental review** → Commit-hash based review range tracking.
- **Codebase intelligence** → Local dependency graph and symbol index.
- **False-positive filtering** → Rule-based suppression + persistent `learnings.json`.
- **One-click fixes** → Patch stubs and `git apply` guidance.
- **PR summaries + architecture diagrams** → Markdown report + Mermaid graph.
- **Custom checks via YAML** → Regex-based custom rules in `review-rules.yaml`.

## Usage

From repo root:

```bash
make review
make review-incremental
make review-config
```

Optional:

```bash
python .codex-review/scripts/review-diff.py --diff-range main...HEAD
```

## Offline Differences vs CodeRabbit

- Runs entirely local.
- No paid API or hosted service dependency.
- Heuristic checks are intentionally simple and transparent.
- Linter/scanner integrations are represented via config and can be extended per repo.

## Future Roadmap

1. IDE plugin hooks for inline comments.
2. CI gate with severity thresholds.
3. Multi-language parser plugins.
4. AI-assisted patch synthesis for `needs-review` findings.
