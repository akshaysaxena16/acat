#!/usr/bin/env bash
set -euo pipefail

# Delete a Step Functions state machine using the same naming template as deploy.
#
# Requirements:
# - AWS credentials already configured (e.g. via GitHub OIDC).
# - Env vars:
#     AWS_REGION
# - Usage:
#     scripts/delete_sfn.sh <cert|prod> <workflow-id>

ENV_NAME="${1:-}"
WF_ID="${2:-}"

if [[ -z "$ENV_NAME" || -z "$WF_ID" ]]; then
  echo "Usage: $0 <cert|prod> <workflow-id>" >&2
  exit 2
fi

if [[ -z "${AWS_REGION:-}" ]]; then
  echo "Missing AWS_REGION env var" >&2
  exit 2
fi

MANIFEST="stepfunctions/manifest.json"
if [[ ! -f "$MANIFEST" ]]; then
  echo "Missing manifest file: $MANIFEST" >&2
  exit 2
fi

NAME_TEMPLATE="$(jq -r '.stateMachineNameTemplate' "$MANIFEST")"
STATE_MACHINE_NAME="${NAME_TEMPLATE//'${ENV}'/$ENV_NAME}"
STATE_MACHINE_NAME="${STATE_MACHINE_NAME//'${ID}'/$WF_ID}"

echo "==> Env: $ENV_NAME"
echo "==> Deleting workflow: $WF_ID"
echo "==> State machine name: $STATE_MACHINE_NAME"

ARN="$(aws stepfunctions list-state-machines \
  --region "$AWS_REGION" \
  --query "stateMachines[?name=='${STATE_MACHINE_NAME}'].stateMachineArn | [0]" \
  --output text)"

if [[ "$ARN" == "None" || -z "$ARN" ]]; then
  echo "==> Not found; nothing to delete."
  exit 0
fi

aws stepfunctions delete-state-machine \
  --region "$AWS_REGION" \
  --state-machine-arn "$ARN" \
  --output json >/dev/null

echo "==> Deleted: $ARN"
