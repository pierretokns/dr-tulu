#!/usr/bin/env bash
set -euo pipefail

# Function to cleanup MCP server
cleanup_mcp() {
    if [ -f /tmp/mcp_server.pid ]; then
        MCP_PID=$(cat /tmp/mcp_server.pid)
        if kill -0 $MCP_PID 2>/dev/null; then
            echo "Stopping MCP server (PID: $MCP_PID)..."
            kill $MCP_PID 2>/dev/null || true
        fi
        rm -f /tmp/mcp_server.pid
    fi
}

# Set trap to cleanup on exit
trap cleanup_mcp EXIT

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "== DR-Tulu: Run UI with Ollama (native) =="

# Load Ollama env if present
if [ -f ".env.ollama" ]; then
  echo "Sourcing .env.ollama"
  # shellcheck disable=SC1091
  source .env.ollama
fi

# Check Ollama API
echo "Checking Ollama API at http://localhost:11434/api/tags ..."
if ! curl -sS --max-time 3 http://localhost:11434/api/tags >/tmp/ollama_tags.json 2>/dev/null; then
  echo "⚠ Could not reach Ollama API at http://localhost:11434. Ensure 'ollama serve' is running."
  echo "You can start Ollama via the app or: ollama serve"
  exit 1
fi

# Detect model name from API output (best-effort)
MODEL=$(python3 - <<'PY'
import sys, json
try:
    j = json.load(open('/tmp/ollama_tags.json'))
except Exception:
    sys.exit(0)

def emit(s):
    if s:
        print(s)
        sys.exit(0)

if isinstance(j, dict):
    # common shapes: {'tags': [...]}, {'models': [...]}
    for key in ('tags','models','data'):
        if key in j and isinstance(j[key], list) and j[key]:
            first = j[key][0]
            if isinstance(first, dict) and 'name' in first:
                emit(first['name'])
            if isinstance(first, str):
                emit(first)
    # fallback: scan lists for dicts with 'name'/'id'
    for v in j.values():
        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    for k in ('name','model','id'):
                        if k in item:
                            emit(item[k])

elif isinstance(j, list) and j:
    first = j[0]
    if isinstance(first, dict):
        for k in ('name','model','id'):
            if k in first:
                emit(first[k])
    if isinstance(first, str):
        emit(first)

sys.exit(0)
PY
)

if [ -z "$MODEL" ]; then
  echo "No model detected from Ollama API output, defaulting to 'tulu3_tools'"
  MODEL="tulu3_tools"
else
  echo "Detected Ollama model: $MODEL"
fi

# Override to use the correct tool-capable model
MODEL="cow/tulu3_tools:8b"
echo "Using model: $MODEL"

# Ensure OPENAI_API_KEY is set for OpenAI-compatible adapter
if [ -z "${OPENAI_API_KEY:-}" ]; then
  export OPENAI_API_KEY="ollama"
  echo "Exported OPENAI_API_KEY=ollama"
fi

# Check if MCP server is running, start it if not
MCP_PORT=8000
if ! curl -s http://localhost:${MCP_PORT}/health > /dev/null 2>&1; then
    echo "🚀 Starting MCP server on port ${MCP_PORT}..."
    python -m dr_agent.mcp_backend.main --port ${MCP_PORT} > /tmp/mcp_server_${MCP_PORT}.log 2>&1 &
    MCP_PID=$!
    echo "MCP server started with PID: $MCP_PID"
    echo "Logs: /tmp/mcp_server_${MCP_PORT}.log"
    # Give it a moment to start
    sleep 2
    # Store PID to clean up later
    echo $MCP_PID > /tmp/mcp_server.pid
else
    echo "✅ MCP server already running on port ${MCP_PORT}"
fi

echo "Launching native UI (agent/scripts/launch_chat.py) with model: $MODEL"

# Use the Ollama-specific workflow we added under agent/workflows
CONFIG_PATH="agent/workflows/auto_search_sft-ollama.yaml"

# Run the chat script
python3 agent/scripts/launch_chat.py --config "$CONFIG_PATH" --model "$MODEL" --skip-checks
