.PHONY: review review-incremental review-config

review:
	python .codex-review/scripts/review-diff.py

review-incremental:
	python .codex-review/scripts/incremental-tracker.py

review-config:
	cat .codex-review/config/review-rules.yaml
