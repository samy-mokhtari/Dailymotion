# basic_structure

A project template for **Python backend + React/TypeScript frontend + Docs**, including local quality gates (pre-commit) and a bootstrap script for quick setup.

## Repository layout

```text
.
├── backend/
├── frontend/
├── doc/
├── scripts/
├── .pre-commit-config.yaml
├── .gitignore
├── docker-compose.yml
└── README.md
```

## Prerequisites

- **Git**
- **Python** (recommended: 3.11+)
- **Node.js + npm**
- (optional) **Docker Desktop** if you use `docker-compose.yml`

## Quick start

### 1) Clone the repository

```bash
git clone <repo>
cd basic_structure
```

### 2) Bootstrap (recommended)

> On Windows, run `bootstrap.sh` via **Git Bash** or **WSL**.

```bash
chmod +x bootstrap.sh
./bootstrap.sh
```

This script:

- creates `backend/.venv`
- installs `pre-commit`, `ruff`, and `pytest`
- installs Node dependencies in `frontend/`
- installs Git hooks (`pre-commit` + `pre-push`)
- runs an initial validation (best effort)

## Quality gates (pre-commit)

Hooks run automatically:

### On every commit

- File hygiene: EOF, trailing whitespace, YAML validity, merge conflict markers, large files
- **Backend**: `ruff format` + `ruff check`
- **Frontend**: `prettier` + `eslint --fix`

### On every push (pre-push)

- **Backend**: `pytest` (via `scripts/run_pytest.py`, which can auto-setup the venv if needed)

### Run manually

```bash
# Run all commit-stage hooks across the whole repo
pre-commit run --all-files

# Run the hooks configured for pre-push
pre-commit run --hook-stage pre-push --all-files
```

## Backend (Python)

### Virtual environment

The venv lives here:

- `backend/.venv/` (gitignored)

### Dev / test dependencies

- `backend/requirements-dev.txt`

### Run tests

```bash
# From repository root
python scripts/run_pytest.py
```

Or (if your venv is activated):

```bash
cd backend
python -m pytest -q
```

## Frontend (React / TypeScript)

Node dependencies are local to the project:

- `frontend/package.json` + lockfile
- `frontend/node_modules/` (gitignored)

### Install

```bash
cd frontend
npm install
```

### Lint / format

```bash
cd frontend
npm run lint
npm run lint:fix
npm run format
```

## Docker (optional)

The `docker-compose.yml` file is intentionally minimal in this template.

```bash
docker compose up -d
docker compose down
```

## Conventions

- **One formatter per stack**:
  - Backend: Ruff (format + lint)
  - Frontend: Prettier (format) + ESLint (quality)
- Do not commit:
  - `backend/.venv/`
  - `frontend/node_modules/`
  - build outputs / caches

## License

TBD.
