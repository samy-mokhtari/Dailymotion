"""
Smoke test (sanity check)

Purpose
- Provide a minimal test to confirm the test runner (pytest) is correctly installed and wired.
- Act as a "canary" so CI/pre-push hooks fail fast if the testing setup is broken.

Why it exists
- When bootstrapping a new project, it's easy to misconfigure pytest discovery or environments.
- This test ensures at least one test is always collected and executed.

How it should evolve
- Keep this file lightweight.
- Replace or complement it with real unit/integration tests as features are added.
"""


def test_smoke():
    assert 1 + 1 == 2
