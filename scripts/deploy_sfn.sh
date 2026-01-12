#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-}"
DEF_PATH="${2:-}"

if [[ -z "$ENV_NAME" || -z "$DEF_PATH" ]]; then
  echo "Usage: $0 <cert|prod> <path-to-definition.asl.json>" >&2
  exit 2
fi

ENV_FILE="stepfunctions/env/${ENV_NAME}.json"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 2
fi

if [[ ! -f "$DEF_PATH" ]]; then
  echo "Missing definition file: $DEF_PATH" >&2
  exit 2
fi

WF_ID="$(basename "$DEF_PATH" .asl.json)"
STATE_MACHINE_NAME="dummy-${ENV_NAME}-${WF_ID}"

echo "==> Target env: $ENV_NAME"
echo "==> Workflow id: $WF_ID"
echo "==> State machine name: $STATE_MACHINE_NAME"
echo

# Load env values
CLUSTER_ARN="$(jq -r '.CLUSTER_ARN' "$ENV_FILE")"
TASK_DEFINITION_ARN="$(jq -r '.TASK_DEFINITION_ARN' "$ENV_FILE")"
SUBNETS_JSON="$(jq -c '.SUBNETS_JSON' "$ENV_FILE")"
SECURITY_GROUPS_JSON="$(jq -c '.SECURITY_GROUPS_JSON' "$ENV_FILE")"
ASSIGN_PUBLIC_IP="$(jq -r '.ASSIGN_PUBLIC_IP' "$ENV_FILE")"
ENV_VALUE="$(jq -r '.ENV' "$ENV_FILE")"

# Render the ASL template via simple placeholder replacement.
# Notes:
# - SUBNETS_JSON / SECURITY_GROUPS_JSON are JSON arrays, so we inject them without quotes.
# - Other values are string substituted.
RENDERED_DEF="$(mktemp)"
trap 'rm -f "$RENDERED_DEF"' EXIT

python - "$DEF_PATH" "$RENDERED_DEF" <<'PY'
import json
import os
import sys

src, dst = sys.argv[1], sys.argv[2]
with open(src, "r", encoding="utf-8") as f:
    content = f.read()

repl = {
    "${CLUSTER_ARN}": os.environ["CLUSTER_ARN"],
    "${TASK_DEFINITION_ARN}": os.environ["TASK_DEFINITION_ARN"],
    "${ASSIGN_PUBLIC_IP}": os.environ["ASSIGN_PUBLIC_IP"],
    "${ENV}": os.environ["ENV_VALUE"],
    "${SUBNETS_JSON}": os.environ["SUBNETS_JSON"],
    "${SECURITY_GROUPS_JSON}": os.environ["SECURITY_GROUPS_JSON"],
}
for k, v in repl.items():
    content = content.replace(k, v)

# Validate JSON output (this catches malformed substitutions)
json.loads(content)

with open(dst, "w", encoding="utf-8") as f:
    f.write(content)
PY

echo "==> Rendered definition is valid JSON."
echo "==> Stub deploy (no AWS calls). Would create/update State Machine:"
echo "    - name: $STATE_MACHINE_NAME"
echo "    - definition: $RENDERED_DEF"
echo

# Real deployment (uncomment once AWS auth + roles are wired):
# ARN="$(aws stepfunctions list-state-machines --query \"stateMachines[?name=='${STATE_MACHINE_NAME}'].stateMachineArn | [0]\" --output text)"
# if [[ "$ARN" == "None" || -z "$ARN" ]]; then
#   echo "Creating state machine..."
#   aws stepfunctions create-state-machine \
#     --name "$STATE_MACHINE_NAME" \
#     --role-arn "REPLACE_ME_STATE_MACHINE_ROLE_ARN" \
#     --definition "file://${RENDERED_DEF}"
# else
#   echo "Updating state machine: $ARN"
#   aws stepfunctions update-state-machine \
#     --state-machine-arn "$ARN" \
#     --definition "file://${RENDERED_DEF}"
# fi
