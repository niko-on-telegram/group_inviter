#!/usr/bin/env bash

set -euo pipefail

# Configuration (override via environment variables before invoking the script)
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-admin}"
CONFIG_FILE="${CONFIG_FILE:-config/config.yaml}"
CONTACT_POINT_UID="${CONTACT_POINT_UID:-telegram-alerts}"
CONTACT_POINT_NAME="${CONTACT_POINT_NAME:-telegram-alerts}"
POLICY_MATCH_SEVERITY="${POLICY_MATCH_SEVERITY:-critical}"

curl_with_auth() {
  curl -sS -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" "$@"
}

info() {
  printf '[contact-point] %s\n' "$*" >&2
}

fail() {
  printf '[contact-point] %s\n' "$*" >&2
  exit 1
}

if [[ ! -f "${CONFIG_FILE}" ]]; then
  fail "Config file not found: ${CONFIG_FILE}"
fi

# Extract bot token and chat id from the YAML config without extra dependencies.
BOT_TOKEN=$(awk -F'"' '/bot_token:/ {print $2; exit}' "${CONFIG_FILE}")
CHAT_ID=$(awk -F': ' '/admin_chat_id:/ {print $2; exit}' "${CONFIG_FILE}" | tr -d '"')

if [[ -z "${BOT_TOKEN}" ]]; then
  fail "Failed to extract telegram.bot_token from ${CONFIG_FILE}"
fi

if [[ -z "${CHAT_ID}" ]]; then
  fail "Failed to extract telegram.admin_chat_id from ${CONFIG_FILE}"
fi

info "Waiting for Grafana to become ready at ${GRAFANA_URL}"
for _ in {1..60}; do
  status=$(curl -s -o /dev/null -w "%{http_code}" "${GRAFANA_URL}/api/health" || true)
  if [[ "${status}" == "200" ]]; then
    break
  fi
  sleep 2
done

if [[ "${status}" != "200" ]]; then
  fail "Grafana API did not become ready (last status: ${status})"
fi

CONTACT_POINT_PAYLOAD=$(cat <<EOF
{
  "uid": "${CONTACT_POINT_UID}",
  "name": "${CONTACT_POINT_NAME}",
  "type": "telegram",
  "settings": {
    "bottoken": "${BOT_TOKEN}",
    "chatid": "${CHAT_ID}"
  },
  "disableResolveMessage": false
}
EOF
)

POLICY_PAYLOAD=$(cat <<EOF
{
  "receiver": "${CONTACT_POINT_NAME}",
  "group_by": ["grafana_folder", "alertname"],
  "routes": [
    {
      "receiver": "${CONTACT_POINT_NAME}",
      "objectMatchers": [["severity", "=", "${POLICY_MATCH_SEVERITY}"]]
    }
  ]
}
EOF
)

info "Upserting Telegram contact point '${CONTACT_POINT_NAME}'"
set +e
response_code=$(curl_with_auth \
  -o /dev/null \
  -w "%{http_code}" \
  -H 'Content-Type: application/json' \
  -X PUT \
  --data "${CONTACT_POINT_PAYLOAD}" \
  "${GRAFANA_URL}/api/v1/provisioning/contact-points/${CONTACT_POINT_UID}")
set -e

if [[ "${response_code}" == "404" ]]; then
  info "Contact point not found, creating"
  curl_with_auth \
    -H 'Content-Type: application/json' \
    -X POST \
    --data "${CONTACT_POINT_PAYLOAD}" \
    "${GRAFANA_URL}/api/v1/provisioning/contact-points" \
    >/dev/null
elif [[ "${response_code}" != "202" ]]; then
  fail "Unexpected response when updating contact point (HTTP ${response_code})"
fi

info "Updating default notification policy to route severity='${POLICY_MATCH_SEVERITY}' to '${CONTACT_POINT_NAME}'"
curl_with_auth \
  -H 'Content-Type: application/json' \
  -X PUT \
  --data "${POLICY_PAYLOAD}" \
  "${GRAFANA_URL}/api/v1/provisioning/policies" \
  >/dev/null

info "Contact point provisioning complete"
