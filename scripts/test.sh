#!/usr/bin/env bash
# Run the project test suite. Keep this script as the stable local and CI entrypoint.

set -Eeuo pipefail

log() {
  printf '[test] %s\n' "$*"
}

fail() {
  printf '[test] error: %s\n' "$*" >&2
  exit 1
}

main() {
  if ! command -v python3 >/dev/null 2>&1; then
    fail "python3 is required to run tests"
  fi

  if python3 -m pytest --version >/dev/null 2>&1; then
    log "running pytest"
    python3 -m pytest tests
  else
    log "pytest is not installed; running unittest and Python syntax smoke test"
    PYTHONPATH="src${PYTHONPATH:+:${PYTHONPATH}}" python3 -m unittest discover -s tests
    python3 -m compileall -q src tests
  fi

}

main "$@"
