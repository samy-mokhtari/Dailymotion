#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# bootstrap.sh
#
# Purpose
# - Bootstrap a fresh clone of this repository/template so it is immediately usable.
# - Install and wire local quality gates (pre-commit hooks) for a "showcase-ready" workflow.
#
# What this script does
# 1) Backend (Python):
#    - Create a virtual environment in backend/.venv (if missing)
#    - Upgrade pip
#    - Install required tooling: pre-commit, ruff, pytest
# 2) Frontend (Node):
#    - Run `npm install` inside frontend/ (if package.json exists)
# 3) Git hooks:
#    - Migrate pre-commit config to the latest schema (safe to run repeatedly)
#    - Install pre-commit hooks for commit + pre-push stages
# 4) Validation:
#    - Optionally run pre-commit across the whole repo to catch issues early
#
# Assumptions / Requirements
# - Python is available on PATH (for venv creation).
# - Node + npm are available on PATH (for frontend install).
# - Run from the repository root (or any folder; the script resolves its own location).
#
# Notes
# - backend/.venv and frontend/node_modules are local artifacts and must be gitignored.
# - This script is safe to re-run; it will reuse existing environments where possible.
# ------------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[1/5] Backend: create venv + install tools"
python -m venv "$ROOT/backend/.venv"

# Cross-platform venv python path
if [ -f "$ROOT/backend/.venv/Scripts/python.exe" ]; then
    PY="$ROOT/backend/.venv/Scripts/python.exe"
else
    PY="$ROOT/backend/.venv/bin/python"
fi

"$PY" -m pip install -U pip
"$PY" -m pip install -U pre-commit ruff pytest

echo "[2/5] Frontend: install node dependencies (if package.json exists)"
if [ -f "$ROOT/frontend/package.json" ]; then
    (cd "$ROOT/frontend" && npm install)
else
    echo "  - Skipped: frontend/package.json not found"
fi

echo "[3/5] pre-commit: migrate config (safe) + install hooks"
"$PY" -m pre_commit migrate-config || true
"$PY" -m pre_commit install
"$PY" -m pre_commit install --hook-type pre-push

echo "[4/5] pre-commit: initial run (optional but useful)"
"$PY" -m pre_commit run --all-files || true
"$PY" -m pre_commit run --hook-stage pre-push --all-files || true

echo "[5/5] Done."
echo "Next: commit your changes; hooks will run automatically on commit/push."
