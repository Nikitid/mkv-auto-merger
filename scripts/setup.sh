#!/usr/bin/env bash
# Verify the local development environment and print actionable install hints.

set -Eeuo pipefail

readonly PROJECT_NAME="MKV auto merger"
readonly MAIN_LANGUAGE="python"

log() {
  printf '[setup] %s\n' "$*"
}

fail() {
  printf '[setup] error: %s\n' "$*" >&2
  exit 1
}

need_command() {
  local name="$1"
  local hint="$2"

  if ! command -v "$name" >/dev/null 2>&1; then
    fail "missing required command '$name'. ${hint}"
  fi
}

main() {
  log "checking development tools for ${PROJECT_NAME}"

  need_command bash "Install Bash 4+ with your OS package manager."
  need_command git "Install Git from https://git-scm.com/ or your package manager."
  need_command shellcheck "macOS: brew install shellcheck. Debian/Ubuntu: sudo apt-get install shellcheck."
  need_command shfmt "macOS: brew install shfmt. Debian/Ubuntu: install shfmt from your package manager or mvdan.cc/sh."

  if [[ "${MAIN_LANGUAGE}" == "python" ]]; then
    need_command python3 "Install Python 3.12+."
    log "optional Python tools can be installed with: python3 -m pip install -e '.[dev]'"
  fi

  log "environment looks ready"
}

main "$@"
