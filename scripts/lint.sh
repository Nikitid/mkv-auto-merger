#!/usr/bin/env bash
# Run deterministic local lint checks. CI uses the same entrypoint.

set -Eeuo pipefail

log() {
  printf '[lint] %s\n' "$*"
}

fail() {
  printf '[lint] error: %s\n' "$*" >&2
  exit 1
}

need_command() {
  local name="$1"

  command -v "$name" >/dev/null 2>&1 || fail "missing required command '$name'"
}

collect_shell_files() {
  find scripts -type f -name '*.sh' -print | sort
}

main() {
  need_command shellcheck
  need_command shfmt

  local shell_files=()
  while IFS= read -r file; do
    shell_files+=("$file")
  done < <(collect_shell_files)

  if [[ ${shell_files[0]+set} != set ]]; then
    fail "no shell scripts found under scripts/"
  fi

  log "running shellcheck"
  shellcheck "${shell_files[@]}"

  log "checking shfmt formatting"
  local unformatted
  unformatted="$(shfmt -l -i 2 "${shell_files[@]}" || true)"
  if [[ -n "${unformatted}" ]]; then
    shfmt -d -i 2 "${shell_files[@]}"
    fail "shell scripts are not formatted; run: make format"
  fi

  if command -v python3 >/dev/null 2>&1; then
    log "checking Python syntax"
    python3 -m compileall -q scripts src tests
    if python3 -m ruff --version >/dev/null 2>&1; then
      log "running ruff"
      python3 -m ruff check scripts src tests
    else
      log "ruff is not installed; skipping Python style lint"
    fi
  else
    fail "python3 is required for Python projects"
  fi

  log "lint checks passed"
}

main "$@"
