from .unified_tool_calling import ALL_PROMPTS as UNIFIED_TOOL_CALLING_PROMPTS
from .unified_tool_calling import (
    STRUCTURED_PROMPTS as UNIFIED_TOOL_CALLING_STRUCTURED_PROMPTS,
)

# Load cloud cost researcher prompt
from pathlib import Path
import yaml

def _load_yaml(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

# Always try to load cloud_cost_researcher prompt
_cloud_cost_path = Path(__file__).parent / "cloud_cost_researcher.yaml"
if _cloud_cost_path.exists():
    import sys
    from datetime import datetime

    print(f"[{datetime.now().isoformat()}] [DEBUG] Loading cloud_cost_researcher prompt from {_cloud_cost_path}", file=sys.stderr)
    CLOUD_COST_RESEARCHER_PROMPT = _load_yaml(_cloud_cost_path)
    UNIFIED_TOOL_CALLING_STRUCTURED_PROMPTS["cloud_cost"] = CLOUD_COST_RESEARCHER_PROMPT
    print(f"[{datetime.now().isoformat()}] [DEBUG] cloud_cost prompt loaded successfully", file=sys.stderr)
    print(f"[{datetime.now().isoformat()}] [DEBUG] Available additional instructions: {list(CLOUD_COST_RESEARCHER_PROMPT.get('additional_instructions', {}).keys())}", file=sys.stderr)
else:
    import sys
    from datetime import datetime
    print(f"[{datetime.now().isoformat()}] [ERROR] cloud_cost_researcher.yaml not found at {_cloud_cost_path}", file=sys.stderr)
