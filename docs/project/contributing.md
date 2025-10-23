# Contributing Guide

Thanks for helping improve the Turnkey Coach Tools workspace. This project is shared between multiple tooling scripts, so a consistent workflow keeps the CLI stable and predictable.

## 1. Environment Setup

- **Python**: Use Python 3.12 (matching the production environment).
- **Virtualenv**:
  ```bash
  python -m venv .venv
  source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
  pip install -r requirements.txt
  pip install pytest  # currently a dev-only dependency
  ```
- Keep `.venv/` and other build artifacts out of version control – the updated `.gitignore` already handles this.
- Run `python -m compileall <modified_files>` before committing when working without pytest to catch syntax errors quickly.

## 2. Coding Standards

- Follow PEP 8 for Python. When in doubt, prefer readability over cleverness.
- Use the helper utilities exposed in `api_client.py` (`get_exercise_id`, `get_exercise_type`, `get_metric_lookup_structures`, etc.) instead of duplicating lookup logic.
- Keep comments purposeful. Add brief context comments only when the code’s intent is not obvious.
- Treat sample markup files as read-only references. Updated examples belong in `docs/examples/`; test fixtures belong in `tests/fixtures/`.

## 3. Testing & Validation

- The baseline suite lives in `tests/`. Run it with:
  ```bash
  python -m pytest
  ```
- Tests currently focus on markup parsing and metric resolution. When you touch parsing logic or CLI flows, add or update tests alongside the change.
- For manual verification of uploads, use the CLI **Validate Markup (Dry Run)** option before hitting the API. This surfaces parse warnings without changing client data.

## 4. Documentation Expectations

- Update the developer guides in `DevGuides/` when you alter workflows (parsing, nutrition calendars, metrics, etc.).
- Cross-link new material from `DevGuides/TOC.md` and reference shared resources like `METRICS_GUIDE.md` and `METRICS_IN_MARKUP.md`.
- Store reusable examples under `docs/examples/` and refer to them from guides rather than inlining long snippets.

## 5. Pull Request Checklist

Before opening a PR:

- [ ] Run tests (`python -m pytest`) or `python -m compileall` on touched modules.
- [ ] Execute the relevant dry-run validation flow in the CLI when markup parsing is affected.
- [ ] Update documentation and the changelog (`changes.md`) if behaviour or workflows shift.
- [ ] Ensure `CHECKLIST.md` items stay accurate when you complete or add cleanup tasks.

## 6. Workflow Tips

- Use `coach_cli.py` for end-to-end verification; it already routes uploads, nutrition assignments, and metrics through the cached catalog helpers.
- Keep branches focused—large refactors should land after covering tests and docs so other contributors can follow along.
- When in doubt, check `docs/examples/` for canonical sample markup and metric usage before authoring new fixtures.

Welcome aboard! 🎯
