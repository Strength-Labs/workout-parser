# Codebase Cleanup Checklist

## Immediate Hygiene
- [x] Audit repository for committed environment/cache artifacts (`.venv/`, `__pycache__/`, `tmp*.txt`, etc.)
- [x] Update `.gitignore` to exclude virtual environments, caches, and compiled artifacts
- [x] Remove existing tracked environment/cache files (e.g., run `git rm -r --cached .venv/` if present)

## Quick Fixes
- [x] Fix escape sequence warning in `actual_prs_tool.py` navigation prompt
- [x] Add prominent reminders in `markup.md` about exact nutrition item names and metric naming (ensure already added notes are reviewed)

## Documentation Updates
- [x] Expand `DevGuides/05-Workout-Management.md` with full nutrition calendar workflow and dual-calendar explanation
- [x] Update `DevGuides/01-Architecture-Overview.md` and `DevGuides/TOC.md` to reference nutrition + metrics features
- [x] Link `METRICS_GUIDE.md` and `METRICS_IN_MARKUP.md` from the primary guides

## Code Quality Improvements
- [x] Introduce helper functions for exercise map access (`get_exercise_id`, `get_exercise_type`) and refactor call sites
- [x] Document and/or consolidate metric upload flow to avoid duplicate submissions
- [x] Cache metric catalog lookup (or otherwise memoize) to reduce rebuild cost per upload

## Testing & Tooling
- [x] Establish baseline pytest suite covering metric parsing and nutrition/workout parsing
- [x] Add a validation/dry-run CLI option to surface parsing issues before upload

## Repository Organization
- [x] Move sample/fixture files into a structured directory (e.g., `tests/fixtures/` and `docs/examples/`) and remove stray temp files
- [x] Create `CONTRIBUTING.md` outlining environment setup, coding standards, testing, and documentation expectations
