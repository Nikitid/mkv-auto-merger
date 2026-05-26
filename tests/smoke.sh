#!/usr/bin/env bash
# Minimal smoke test for generated non-Python projects.

set -Eeuo pipefail

main() {
  [[ -d src ]] || {
    printf 'src directory is missing\n' >&2
    exit 1
  }

  [[ -d scripts ]] || {
    printf 'scripts directory is missing\n' >&2
    exit 1
  }
}

main "$@"
