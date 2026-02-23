#!/bin/bash
# Web design auto-generator — called by OpenClaw cron every 5 hours
set -e

cd /root/webdesign

# Extract Anthropic API key from OpenClaw auth profiles
ANTHROPIC_API_KEY=$(python3 -c "
import json
d = json.load(open('/root/.openclaw/agents/main/agent/auth-profiles.json'))
profiles = d.get('profiles', {})
p = profiles.get('anthropic:default', {})
print(p.get('apiKey', p.get('key', '')))
")
export ANTHROPIC_API_KEY

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "ERROR: Could not read Anthropic API key"
  exit 1
fi

echo "[$(date -u '+%Y-%m-%d %H:%M UTC')] Starting web design generation run..."

/root/webdesign/.venv/bin/python /root/webdesign/generate.py 2>&1

echo "[$(date -u '+%Y-%m-%d %H:%M UTC')] Generation complete."
