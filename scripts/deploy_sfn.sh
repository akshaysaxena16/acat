#!/usr/bin/env bash
set -euo pipefail

# Full deploy script for Step Functions (Option B: CLI create/update).
#
# Requirements:
# - AWS credentials already configured (e.g. via GitHub OIDC).
# - Env vars:
#     AWS_REGION
#     SFN_EXECUTION_ROLE_ARN   (role for the state machine to assume)
# - Optional:
#     SFN_LOG_GROUP_ARN        (CloudWatch Logs log group ARN)
#     SFN_LOG_LEVEL            (ALL|ERROR|FATAL|OFF; default ALL)
#     SFN_INCLUDE_EXEC_DATA    (true|false; default true)
#
# Usage:
#   scripts/deploy_sfn.sh <cert|prod> <path-to-definition.asl.json>

ENV_NAME="${1:-}"
DEF_PATH="${2:-}"

if [[ -z "$ENV_NAME" || -z "$DEF_PATH" ]]; then
  echo "Usage: $0 <cert|prod> <path-to-definition.asl.json>" >&2
  exit 2
fi

if [[ -z "${AWS_REGION:-}" ]]; then
  echo "Missing AWS_REGION env var" >&2
  exit 2
fi

if [[ -z "${SFN_EXECUTION_ROLE_ARN:-}" ]]; then
  echo "Missing SFN_EXECUTION_ROLE_ARN env var" >&2
  exit 2
fi

ENV_FILE="stepfunctions/env/${ENV_NAME}.json"
MANIFEST="stepfunctions/manifest.json"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 2
fi
if [[ ! -f "$MANIFEST" ]]; then
  echo "Missing manifest file: $MANIFEST" >&2
  exit 2
fi
if [[ ! -f "$DEF_PATH" ]]; then
  echo "Missing definition file: $DEF_PATH" >&2
  exit 2
fi

WF_ID="$(basename "$DEF_PATH" .asl.json)"
NAME_TEMPLATE="$(jq -r '.stateMachineNameTemplate' "$MANIFEST")"
STATE_MACHINE_NAME="${NAME_TEMPLATE//'${ENV}'/$ENV_NAME}"
STATE_MACHINE_NAME="${STATE_MACHINE_NAME//'${ID}'/$WF_ID}"

TYPE="$(jq -r --arg id "$WF_ID" '.workflows[] | select(.id==$id) | .type // "STANDARD"' "$MANIFEST")"
if [[ -z "$TYPE" || "$TYPE" == "null" ]]; then
  TYPE="STANDARD"
fi

TAGS_JSON="$(jq -c --arg env "$ENV_NAME" --arg id "$WF_ID" '
  (
    (.workflows[] | select(.id==$id) | .tags) // {}
  ) as $t
  | ($t + {env: $env, workflow: $id})
' "$MANIFEST")"

RENDERED_DEF="$(mktemp)"
trap 'rm -f "$RENDERED_DEF"' EXIT

python3 scripts/render_asl.py "$ENV_FILE" "$DEF_PATH" "$RENDERED_DEF"

echo "==> Env: $ENV_NAME"
echo "==> Workflow: $WF_ID"
echo "==> State machine: $STATE_MACHINE_NAME"

EXISTING_ARN="$(aws stepfunctions list-state-machines \
  --region "$AWS_REGION" \
  --query "stateMachines[?name=='${STATE_MACHINE_NAME}'].stateMachineArn | [0]" \
  --output text)"

LOG_LEVEL="${SFN_LOG_LEVEL:-ALL}"
INCLUDE_EXEC_DATA="${SFN_INCLUDE_EXEC_DATA:-true}"

LOGGING_ARGS=()
if [[ -n "${SFN_LOG_GROUP_ARN:-}" ]]; then
  LOGGING_ARGS=(--logging-configuration "level=${LOG_LEVEL},includeExecutionData=${INCLUDE_EXEC_DATA},destinations=[{cloudWatchLogsLogGroup={logGroupArn=${SFN_LOG_GROUP_ARN}}}]")
fi

TRACING_ARGS=(--tracing-configuration "enabled=true")

TAGS_ARG="$(echo "$TAGS_JSON" | jq -c 'to_entries | map({key: .key, value: (.value|tostring)})')"

if [[ "$EXISTING_ARN" == "None" || -z "$EXISTING_ARN" ]]; then
  echo "==> Creating state machine..."
  CREATE_OUT="$(aws stepfunctions create-state-machine \
    --region "$AWS_REGION" \
    --name "$STATE_MACHINE_NAME" \
    --type "$TYPE" \
    --role-arn "$SFN_EXECUTION_ROLE_ARN" \
    --definition "file://${RENDERED_DEF}" \
    "${LOGGING_ARGS[@]}" \
    "${TRACING_ARGS[@]}" \
    --tags "$TAGS_ARG" \
    --output json)"

  STATE_MACHINE_ARN="$(echo "$CREATE_OUT" | jq -r '.stateMachineArn')"
else
  STATE_MACHINE_ARN="$EXISTING_ARN"
  echo "==> Updating state machine: $STATE_MACHINE_ARN"
  aws stepfunctions update-state-machine \
    --region "$AWS_REGION" \
    --state-machine-arn "$STATE_MACHINE_ARN" \
    --role-arn "$SFN_EXECUTION_ROLE_ARN" \
    --definition "file://${RENDERED_DEF}" \
    "${LOGGING_ARGS[@]}" \
    "${TRACING_ARGS[@]}" \
    --output json >/dev/null

  # Tags are not updated by update-state-machine; enforce them.
  aws stepfunctions tag-resource \
    --region "$AWS_REGION" \
    --resource-arn "$STATE_MACHINE_ARN" \
    --tags "$TAGS_ARG" \
    --output json >/dev/null
fi

echo "==> Done: $STATE_MACHINE_ARN"
