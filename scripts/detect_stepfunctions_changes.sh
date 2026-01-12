#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   scripts/detect_stepfunctions_changes.sh <base_sha> <head_sha>
#
# Outputs to stdout in a simple, parseable format:
#   DEPLOY:<path>   (definition file path to create/update)
#   DELETE:<id>     (workflow id to delete; derived from removed file name)
#
# Rules:
# - If shared inputs changed (manifest or env files), we deploy ALL current definitions.
# - Deletes are still detected from git diff and emitted.

BASE_SHA="${1:-}"
HEAD_SHA="${2:-}"

if [[ -z "$BASE_SHA" || -z "$HEAD_SHA" ]]; then
  echo "Usage: $0 <base_sha> <head_sha>" >&2
  exit 2
fi

DEF_GLOB='stepfunctions/definitions/*.asl.json'

shared_changed="$(git diff --name-only "$BASE_SHA" "$HEAD_SHA" -- \
  stepfunctions/manifest.json \
  stepfunctions/env \
  || true)"

declare -A deploy=()
declare -A delete=()

if [[ -n "${shared_changed//[[:space:]]/}" ]]; then
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    deploy["$f"]=1
  done < <(git ls-files "$DEF_GLOB")
else
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    deploy["$f"]=1
  done < <(git diff --name-only "$BASE_SHA" "$HEAD_SHA" -- "$DEF_GLOB" || true)
fi

# Detect deletes/renames.
# name-status outputs:
#  D <path>
#  R100 <old> <new>
while IFS=$'\t' read -r status p1 p2; do
  [[ -z "$status" ]] && continue

  case "$status" in
    D)
      if [[ "$p1" == stepfunctions/definitions/*.asl.json ]]; then
        id="$(basename "$p1" .asl.json)"
        delete["$id"]=1
      fi
      ;;
    R*)
      if [[ "$p1" == stepfunctions/definitions/*.asl.json ]]; then
        old_id="$(basename "$p1" .asl.json)"
        delete["$old_id"]=1
      fi
      if [[ "$p2" == stepfunctions/definitions/*.asl.json ]]; then
        deploy["$p2"]=1
      fi
      ;;
  esac
done < <(git diff --name-status "$BASE_SHA" "$HEAD_SHA" -- "$DEF_GLOB" || true)

for f in "${!deploy[@]}"; do
  echo "DEPLOY:$f"
done
for id in "${!delete[@]}"; do
  echo "DELETE:$id"
done
