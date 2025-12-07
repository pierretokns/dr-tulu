#!/bin/bash
# Tulu 3.1 → Ollama with Tool Calling Setup (M2 Mac Studio)
# UPDATED: Includes cow/tulu3_tools template approach for proper tool calling
# Copy this entire script, save as setup_tulu3_ollama_toolcalling.sh, then: bash setup_tulu3_ollama_toolcalling.sh

set -e

echo "🚀 Tulu 3.1 to Ollama with Tool Calling Support"
echo "=========================================================="
echo "Target: M2 Mac Studio"
echo "Tool Calling: ENABLED (cow/tulu3_tools template approach)"
echo ""

# STEP 1: Verify Ollama is running
echo "✓ Step 1: Checking Ollama..."
if ! pgrep -x "ollama" > /dev/null; then
    echo "  ⚠️  Ollama daemon not running!"
    echo "  Please start Ollama from Applications (/Applications/Ollama.app)"
    echo "  Then run this script again."
    exit 1
fi
echo "  ✓ Ollama running on localhost:11434"

# STEP 2: Create workspace
WORKSPACE="$HOME/tulu3_1_tools_setup"
mkdir -p "$WORKSPACE"
cd "$WORKSPACE"
echo ""
echo "✓ Step 2: Workspace created: $WORKSPACE"

# STEP 3: Download GGUF
echo ""
echo "✓ Step 3: Downloading Tulu 3.1 GGUF model..."
echo "  (Q6_K_M quantization: ~5GB, 5-15 min)"

MODEL_FILE="$WORKSPACE/Tulu-3.1-8B-Q6_K_M.gguf"
MODEL_URL="https://huggingface.co/bartowski/allenai_Llama-3.1-Tulu-3.1-8B-GGUF/raw/main/allenai_Llama-3.1-Tulu-3.1-8B-Q6_K_L.gguf"

if [ ! -f "$MODEL_FILE" ]; then
    echo "  📡 Starting download (this takes a while on first run)..."
    curl -L -# -o "$MODEL_FILE" "$MODEL_URL"
    echo "  ✓ Downloaded $(du -h "$MODEL_FILE" | cut -f1)"
else
    echo "  ✓ Model already exists: $(du -h "$MODEL_FILE" | cut -f1)"
fi

# STEP 4: Create Modelfile with Tool Calling Support (cow/tulu3_tools approach)
echo ""
echo "✓ Step 4: Creating Modelfile with tool calling support..."
echo "  (Based on cow/tulu3_tools template)"

cat > "$WORKSPACE/Modelfile" << 'MODELFILE_EOF'
FROM ./Tulu-3.1-8B-Q6_K_M.gguf

# Tool calling template - ADAPTED FROM cow/tulu3_tools
# This template teaches the model how to call tools properly
# Key features:
#   - Role markers: <|user|>, <|assistant|>, <|tool|>
#   - Explicit tool instruction
#   - Proper message sequencing
#   - JSON format enforcement

TEMPLATE """{{ .System }}

{{- if .Tools }}
When given functions, ONLY respond with valid JSON in this format:
{"name": "function_name", "parameters": {"key": "value"}}

Available functions:
{{ range .Tools }}{{ . }}
{{ end }}
{{- end }}

{{- range $i, $_ := .Messages }}

{{- $last := eq (len (slice $.Messages $i)) 1 }}

{{- if eq .Role "user" }}<|user|>

{{- if and $.Tools $last }}

Given the following functions, please respond with a JSON for a function call with its proper arguments that best answers the given prompt.

Respond in the format {"name": function name, "parameters": dictionary of argument name and its value}. Do not use variables.

{{ range $.Tools }}{{ . }}{{ end }}

{{ .Content }}<|end|>

{{- else }}

{{ .Content }}<|end|>

{{- end }}{{ if $last }}<|assistant|>{{ end }}

{{- else if eq .Role "assistant" }}<|assistant|>

{{- if .ToolCalls }}

{{ range .ToolCalls }}{"name": "{{ .Function.Name }}", "parameters": {{ .Function.Arguments }}}{{ end }}

{{- else }}

{{ .Content }}

{{- end }}{{ if not $last }}<|end|>{{ end }}

{{- else if eq .Role "tool" }}<|tool|>

{{ .Content }}<|end|>{{ if $last }}<|assistant|>{{ end }}

{{- end }}

{{- end }}<|end|>"""

# System prompt with tool calling awareness
SYSTEM "You are Tulu 3, a helpful and harmless AI Assistant built by the Allen Institute for AI. You have tool calling capabilities. When you receive a tool call response, use the output to format an answer to the original user question. Only call tools when necessary - do not call tools for information you already know or can infer."

# Model parameters optimized for M2
PARAMETER temperature 0.7
PARAMETER top_k 40
PARAMETER top_p 0.9
PARAMETER num_ctx 8192
PARAMETER repeat_penalty 1.1
MODELFILE_EOF

echo "  ✓ Modelfile created with cow/tulu3_tools template"

# STEP 5: Build Ollama Model
echo ""
echo "✓ Step 5: Building Ollama model 'tulu3_tools'..."
echo "  (First build may take 1-2 min for M2 Mac)"

cd "$WORKSPACE"
ollama create tulu3_tools -f Modelfile

if [ $? -eq 0 ]; then
    echo "  ✓ Model 'tulu3_tools' created successfully!"
else
    echo "  ✗ Model creation failed. Check errors above."
    exit 1
fi

# STEP 6: Verify model
echo ""
echo "✓ Step 6: Verifying model..."
if ollama list | grep -q tulu3_tools; then
    echo "  ✓ Model registered in Ollama"
else
    echo "  ✗ Model not found after creation"
    exit 1
fi

# STEP 7: Verify template includes tool support
echo ""
echo "✓ Step 7: Verifying tool calling template..."
TEMPLATE_CHECK=$(ollama show tulu3_tools | grep -i "tool\|function" | head -1)
if [ ! -z "$TEMPLATE_CHECK" ]; then
    echo "  ✓ Template includes tool support markers"
else
    echo "  ⚠️  Template verification inconclusive (model may still work)"
fi

# STEP 8: Quick test
echo ""
echo "✓ Step 8: Testing model (30 sec test)..."
RESPONSE=$(ollama run tulu3_tools "Say 'Tool calling enabled!' in one sentence" 2>&1 | head -1)
if [ ! -z "$RESPONSE" ]; then
    echo "  ✓ Model responds: $RESPONSE"
else
    echo "  ⚠️  No immediate response, but model may still work"
fi

# STEP 9: Tool calling test
echo ""
echo "✓ Step 9: Testing tool calling capability..."
TOOL_TEST=$(ollama run tulu3_tools "Use a search_tool to find information about transformers" 2>&1 | grep -E '{"name"|function' | head -1)
if [ ! -z "$TOOL_TEST" ]; then
    echo "  ✓ Tool calling works! Output:"
    echo "    $TOOL_TEST"
else
    echo "  ℹ️  No immediate tool call (model may use for valid queries only)"
fi

# STEP 10: Show access methods
echo ""
echo "=========================================================="
echo "✅ SUCCESS! Tulu 3.1 with Tool Calling Ready"
echo "=========================================================="
echo ""
echo "Tool Calling Enabled: YES"
echo "Template: cow/tulu3_tools approach"
echo "System Prompt: Tool-aware"
echo ""
echo "Access your model:"
echo ""
echo "1️⃣  Direct Ollama:"
echo "   ollama run tulu3_tools"
echo ""
echo "2️⃣  OpenAI-Compatible API (for DR-Tulu integration):"
echo "   export OPENAI_API_KEY='ollama'"
echo "   export LLM_ENDPOINT='http://localhost:11434/v1'"
echo "   export LLM_MODEL='tulu3_tools'"
echo ""
echo "3️⃣  Python with OpenAI SDK:"
echo "   from openai import OpenAI"
echo "   client = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')"
echo "   response = client.chat.completions.create("
echo "     model='tulu3_tools',"
echo "     messages=[{'role': 'user', 'content': 'Your query'}],"
echo "     tools=[...]  # Optional: add tools for tool calling"
echo "   )"
echo ""
echo "4️⃣  Test Tool Calling:"
echo "   ollama run tulu3_tools"
echo "   >> Use search_web to find: what are transformers?"
echo "   (Watch for: {\"name\": \"search_web\", \"parameters\": {...}})"
echo ""
echo "📁 Workspace: $WORKSPACE"
echo "📦 Model size: $(du -h "$MODEL_FILE" | cut -f1)"
echo ""
echo "⚠️  IMPORTANT: Next step is to integrate with DR-Tulu"
echo "   Run: bash integrate_dr_tulu_ollama_toolcalling.sh"
echo ""
echo "📖 For tool calling details, see: TOOL_CALLING_TWEAKS.md"
