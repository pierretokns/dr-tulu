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

_cloud_cost_path = Path(__file__).parent / "cloud_cost_researcher.yaml"
if _cloud_cost_path.exists():
    CLOUD_COST_RESEARCHER_PROMPT = _load_yaml(_cloud_cost_path)
    UNIFIED_TOOL_CALLING_STRUCTURED_PROMPTS["cloud_cost"] = CLOUD_COST_RESEARCHER_PROMPT
