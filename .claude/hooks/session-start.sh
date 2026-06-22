#!/bin/bash
# SessionStart hook: install Python dependencies so tests and linters work
# in Claude Code on the web sessions. Idempotent and non-interactive.
set -euo pipefail

# Only run inside Claude Code on the web (remote) sessions.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$PROJECT_DIR"

echo "[session-start] Setting up Python environment in $PROJECT_DIR"

# Best-effort pip upgrade (never fail the hook if the environment forbids it).
python3 -m pip install --upgrade pip >/dev/null 2>&1 || true

# Install, falling back to --break-system-packages for Debian
# externally-managed environments only when a plain install fails.
pip_install() {
  python3 -m pip install "$@" \
    || python3 -m pip install --break-system-packages "$@"
}

installed_something=0

if [ -f "requirements.txt" ]; then
  echo "[session-start] Installing requirements.txt"
  pip_install -r requirements.txt
  installed_something=1
fi

if [ -f "requirements-dev.txt" ]; then
  echo "[session-start] Installing requirements-dev.txt"
  pip_install -r requirements-dev.txt
  installed_something=1
fi

if [ -f "pyproject.toml" ]; then
  echo "[session-start] Installing project from pyproject.toml"
  pip_install -e ".[dev]" 2>/dev/null \
    || pip_install -e . 2>/dev/null \
    || echo "[session-start] pyproject.toml present but editable install skipped"
  installed_something=1
fi

if [ "$installed_something" -eq 0 ]; then
  echo "[session-start] No Python dependency manifest found yet; nothing to install."
fi

# Make repo-root imports resolve for test runs.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo "export PYTHONPATH=\"$PROJECT_DIR:\${PYTHONPATH:-}\"" >> "$CLAUDE_ENV_FILE"
fi

echo "[session-start] Done."
