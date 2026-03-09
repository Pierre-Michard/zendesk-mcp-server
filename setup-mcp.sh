#!/bin/bash
# Starts the Zendesk MCP server and writes a self-contained auth token into .mcp.json.
# Run once (or when credentials change). The token survives server restarts — no need to re-run.

set -e

DOCKER_NAME="zendesk-mcp-server"
SERVER_URL="http://localhost:8000"
ENV_FILE="$(cd "$(dirname "$0")" && pwd)/.env"
MCP_CONFIG="/Users/pierre.michard/workspace/sorare/backend/.mcp.json"

# Load credentials
if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: .env file not found at $ENV_FILE" >&2
  exit 1
fi
export $(grep -v '^#' "$ENV_FILE" | xargs)

# Remove stopped container if it exists
if docker ps -a --format '{{.Names}}' | grep -q "^${DOCKER_NAME}$"; then
  if ! docker ps --format '{{.Names}}' | grep -q "^${DOCKER_NAME}$"; then
    echo "Removing stopped container..." >&2
    docker rm "$DOCKER_NAME" >/dev/null
  fi
fi

# Start container if not already running
if ! docker ps --format '{{.Names}}' | grep -q "^${DOCKER_NAME}$"; then
  echo "Starting Docker container..." >&2
  docker run -d --name "$DOCKER_NAME" --restart unless-stopped -p 8000:8000 zendesk-mcp-server >/dev/null
fi

# Wait for server to accept requests (any HTTP response means it's up)
echo "Waiting for server to be ready..." >&2
for i in $(seq 1 30); do
  if curl -s --max-time 1 "$SERVER_URL/.well-known/oauth-authorization-server" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

# Authenticate
echo "Authenticating as $ZENDESK_EMAIL..." >&2
RESPONSE=$(curl -sf -X POST "$SERVER_URL/auth" \
  -H "Content-Type: application/json" \
  -d "{\"subdomain\":\"$ZENDESK_SUBDOMAIN\",\"email\":\"$ZENDESK_EMAIL\",\"api_key\":\"$ZENDESK_API_KEY\"}")

TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])" 2>/dev/null || true)

if [ -z "$TOKEN" ]; then
  echo "ERROR: Authentication failed. Response: $RESPONSE" >&2
  exit 1
fi

echo "Got session token." >&2

# Update .mcp.json
python3 - "$MCP_CONFIG" "$TOKEN" <<'EOF'
import sys, json

config_path = sys.argv[1]
token = sys.argv[2]

with open(config_path) as f:
    config = json.load(f)

config['mcpServers']['zendesk'] = {
    'type': 'sse',
    'url': f'http://localhost:8000/sse?token={token}'
}

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)
    f.write('\n')

print(f"Updated {config_path}")
print(f"Token: {token}")
EOF
