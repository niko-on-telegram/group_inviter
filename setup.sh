#!/bin/bash
set -e

# Create logs directory with proper permissions
mkdir -p logs
chmod 777 logs

# Setup Grafana alerting configuration
CONFIG_FILE="config/config.yaml"
TEMPLATE="monitoring/grafana/provisioning/alerting/contact-points.yaml.tmpl"
OUTPUT="monitoring/grafana/provisioning/alerting/contact-points.yaml"

# Create alerting directory if it doesn't exist
mkdir -p "$(dirname "$OUTPUT")"

# Extract bot token and chat id from config
TOKEN=$(awk -F'"' '/bot_token:/ {print $2; exit}' "$CONFIG_FILE")
CHAT=$(awk -F': ' '/admin_chat_id:/ {print $2; exit}' "$CONFIG_FILE")

if [ -z "$TOKEN" ] || [ -z "$CHAT" ]; then
    echo "Error: Could not extract bot token or chat ID from config file"
    exit 1
fi

# Generate contact points configuration
sed "s/__BOT_TOKEN__/$TOKEN/g; s/__CHAT_ID__/$CHAT/g" "$TEMPLATE" > "$OUTPUT"

# Ensure the output file is readable by Grafana
chmod 644 "$OUTPUT"
