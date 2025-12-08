#!/usr/bin/env bash
set -euo pipefail

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

# Ensure OPENAI_API_KEY is set for OpenAI-compatible adapter
if [ -z "${OPENAI_API_KEY:-}" ]; then
  export OPENAI_API_KEY="ollama"
  echo "Exported OPENAI_API_KEY=ollama"
fi

echo "Launching Web UI with model: $MODEL"

# Use the Ollama-specific workflow we added under agent/workflows
CONFIG_PATH="workflows/auto_search_sft-ollama.yaml"

# Install UI dependencies if needed
if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "Installing UI dependencies..."
    cd agent && python3 -m pip install -e ".[ui]" && cd ..
fi

# Run the web UI server
cd agent && python3 -m workflows.auto_search_sft serve --config "$CONFIG_PATH" --host 0.0.0.0 --port 7860 --verbose && cd ..
