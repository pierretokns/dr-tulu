# DR Tulu Agents

This document provides simple instructions for running the DR Tulu agents and workflows.

## Quick Start

### 1. Setup Environment

```bash
# Navigate to agent directory
cd agent

# CRITICAL: Always use the project's .venv
# The virtual environment contains all required dependencies
source .venv/bin/activate

# Verify you're using the correct Python environment
which python  # Should show: /path/to/agent/.venv/bin/python
python --version  # Should match project requirements

# Ensure Ollama is running and Tulu 3 Tools model is available
ollama list  # Should show: cow/tulu3_tools:8b
# If not available: ollama pull cow/tulu3_tools:8b

# Ensure .env file exists with API keys
cp .env.example .env
# Edit .env with your API keys:
# SERPER_API_KEY=your_serper_key
# JINA_API_KEY=your_jina_key

# Verify environment is properly set up
pip list | grep -E "(litellm|fastmcp|playwright)"  # Key dependencies should be visible
```

#### Virtual Environment (.venv) Details

The project uses a dedicated Python virtual environment for isolation and reproducibility:

**Why .venv is essential:**
- **Dependency isolation**: Prevents conflicts with system Python packages
- **Reproducible builds**: Ensures all team members use the same package versions
- **Security**: Contains dependencies to the project directory
- **Version control**: Python and package versions are locked and tested

**Critical .venv usage rules:**
1. **ALWAYS activate** before running any Python commands: `source .venv/bin/activate`
2. **NEVER use system Python** or virtual environments from other projects
3. **Verify activation** by checking `which python` points to `.venv/bin/python`
4. **Install packages** only through pip in the activated environment
5. **Keep .venv local** - never commit it to version control

**Common .venv issues:**
- **ModuleNotFoundError**: You forgot to activate .venv
- **Wrong Python version**: System Python is being used instead of .venv
- **Import errors**: Dependencies installed in wrong environment
- **Permission denied**: .venv permissions were modified accidentally

**Recovery commands:**
```bash
# If .venv is corrupted or missing
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # If requirements.txt exists

# Verify .venv is working
python -c "import litellm; print('Dependencies OK')"
```

### 2. Available Workflows

#### Cloud Cost Researcher
Specializes in comparing deployment costs across cloud providers (AWS, GCP, Azure, Digital Ocean, Cloudflare) using Tulu 3 Tools with Ollama.

```bash
# Start on port 8080
python workflows/auto_search_sft.py serve --port 8080 \
  --config workflows/cloud_cost_researcher.yaml \
  --config-overrides prompt_version=cloud_cost

# Test with curl
curl -X POST http://localhost:8080/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"content": "What is the cost to run PostgreSQL on AWS vs GCP?", "dataset_name": "cloud_cost"}'
```

#### General Research (Auto Search)
General purpose search and research workflow using Tulu 3 Tools with Ollama.

```bash
# Start on port 8080
python workflows/auto_search_sft.py serve --port 8080

# Test with curl
curl -X POST http://localhost:8080/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"content": "What are the latest developments in quantum computing?", "dataset_name": "long_form"}'
```

### 3. Configuration Overrides

Use `--config-overrides` to customize behavior:

```bash
# Override temperature (0.0 = more deterministic, 1.0 = more creative)
--config-overrides search_agent_temperature=0.3

# Override max tokens for responses
--config-overrides search_agent_max_tokens=8000

# Increase tool call limit
--config-overrides search_agent_max_tool_calls=20

# Enable browse agent for more comprehensive research
--config-overrides use_browse_agent=true

# Override prompt version
--config-overrides prompt_version=cloud_cost
```

### 4. Common Override Examples

#### For Cloud Cost Research
```bash
python workflows/auto_search_sft.py serve --port 8080 \
  --config workflows/cloud_cost_researcher.yaml \
  --config-overrides prompt_version=cloud_cost search_agent_temperature=0.7 search_agent_max_tool_calls=20
```

#### For Creative Research
```bash
python workflows/auto_search_sft.py serve --port 8080 \
  --config-overrides search_agent_temperature=1.0 search_agent_max_tokens=16000 use_browse_agent=true
```

#### For Factual Research
```bash
python workflows/auto_search_sft.py serve --port 8080 \
  --config-overrides search_agent_temperature=0.3 search_agent_max_tool_calls=15
```

### 5. Features We Can Make Better

1. **Caching**: Implement tool call caching to avoid repeated API calls for the same queries
2. **Key Facts Storage**: Store persistent information about cloud services, pricing, and technical specs
3. **Parallel Tool Calls**: Execute multiple search queries simultaneously for faster research
4. **Response Streaming**: Improve streaming experience for long responses
5. **Tool Usage Optimization**: Better tool selection and more efficient tool calling
6. **Error Handling**: More robust error recovery and retry mechanisms
7. **Context Management**: Better handling of long conversations and research sessions

### 6. Troubleshooting

#### API Keys Not Found
- Ensure `.env` file exists in the agent directory
- Check that API keys are properly formatted
- Verify the .env file path in the workflow script

#### Server Not Starting
- Check if port is already in use
- Verify virtual environment is activated
- Ensure all dependencies are installed

#### No Tool Calls Made
- Check if prompt version is correctly set
- Verify API keys are loaded
- Check search tool configuration (serper, jina, etc.)

### 7. Development Tips

- Use `2>&1 | tee logfile.log` to capture both stdout and stderr for debugging
- Monitor tool usage by checking logs for "Tool calls made:" messages
- Test with different dataset names to trigger different prompt versions
- Use lower ports (below 1024) may require sudo privileges