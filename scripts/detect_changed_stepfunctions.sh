#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   scripts/detect_changed_stepfunctions.sh <base_sha> <head_sha>
#
# Output:
#   - If env/shared files changed: prints ALL definition files (one per line)
#   - Else: prints ONLY changed definition files (one per line)

BASE_SHA="${1:-}"
HEAD_SHA="${2:-}"

if [[ -z "$BASE_SHA" || -z "$HEAD_SHA" ]]; then
  echo "Usage: $0 <base_sha> <head_sha>" >&2
  exit 2
fi

DEF_GLOB='stepfunctions/definitions/*.asl.json'

# If shared inputs changed, redeploy everything (safe default).
SHARED_CHANGED="$(git diff --name-only "$BASE_SHA" "$HEAD_SHA" -- \
  stepfunctions/manifest.json \
  stepfunctions/env \
  || true)"

if [[ -n "${SHARED_CHANGED//[[:space:]]/}" ]]; then
  git ls-files "$DEF_GLOB"
  exit 0
fi

# Otherwise deploy only changed definitions.
git diff --name-only "$BASE_SHA" "$HEAD_SHA" -- "$DEF_GLOB" || true
