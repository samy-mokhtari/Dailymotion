"""
scripts/run_pytest.py

Purpose
- Make the backend test suite runnable in a consistent way from anywhere (Git hooks, CI, CLI),
  without requiring the developer to manually activate a virtual environment.
- Provide a "self-validating" bootstrap for a fresh project/template installation:
  - Creates backend/.venv if missing
  - Installs minimal test dependencies (or backend/requirements-dev.txt if present)
  - Runs pytest from the backend directory

Why this exists
- pre-commit hooks run commands in different contexts (terminal, VS Code UI, GUI clients).
  Relying on an activated venv is fragile.
- This wrapper centralizes the logic for locating/creating the backend venv and executing tests.

Behavior
1) Detect repository root and backend directory.
2) Ensure backend/.venv exists (create it using the current Python interpreter if needed).
3) Upgrade pip inside the venv.
4) Install dev/test dependencies:
   - Prefer backend/requirements-dev.txt if present
   - Otherwise fall back to installing pytest only (template-friendly)
5) Run `pytest -q` from backend/ and return pytest's exit code.

Notes
- The virtual environment directory (backend/.venv) should be gitignored.
- If your backend becomes an installable package, you may optionally install it in editable mode.
- This script is designed to be invoked by pre-commit (pre-push stage), but can also be run manually.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print(f"+ {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=str(cwd) if cwd else None)


def find_venv_python(venv_dir: Path) -> Path | None:
    candidates = [
        venv_dir / "Scripts" / "python.exe",  # Windows
        venv_dir / "bin" / "python",          # Linux/Mac
    ]
    return next((p for p in candidates if p.exists()), None)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    backend_dir = root / "backend"
    venv_dir = backend_dir / ".venv"

    if not backend_dir.exists():
        print("ERROR: backend/ directory not found.", file=sys.stderr)
        return 1

    # 1) Ensure venv exists
    venv_python = find_venv_python(venv_dir)
    if venv_python is None:
        print("backend/.venv not found -> creating venv...")
        run([sys.executable, "-m", "venv", str(venv_dir)])
        venv_python = find_venv_python(venv_dir)
        if venv_python is None:
            print("ERROR: venv creation failed.", file=sys.stderr)
            return 1

    # 2) Ensure test deps are installed
    run([str(venv_python), "-m", "pip", "install", "-U", "pip"])

    req_dev = backend_dir / "requirements-dev.txt"
    if req_dev.exists():
        run([str(venv_python), "-m", "pip", "install", "-r", str(req_dev)])
    else:
        # Minimum viable for a fresh template
        run([str(venv_python), "-m", "pip", "install", "pytest"])

    # (Optionnel) installer le backend en editable si tu as un package installé
    # Si ton backend est une app non-packagée, tu peux enlever ce bloc sans souci.
    pyproject = backend_dir / "pyproject.toml"
    if pyproject.exists():
        # Ne pas planter si ce n’est pas un package installable : on tente, sinon on continue.
        try:
            run([str(venv_python), "-m", "pip", "install", "-e", str(backend_dir)])
        except subprocess.CalledProcessError:
            print("NOTE: backend not installed as a package (pip -e failed). Continuing...")

    # 3) Run pytest from backend/
    os.chdir(backend_dir)
    return subprocess.call([str(venv_python), "-m", "pytest", "-q"])


if __name__ == "__main__":
    raise SystemExit(main())
