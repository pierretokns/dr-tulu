import requests, json

tools = [
  {
    "type": "function",
    "function": {
      "name": "get_time",
      "description": "Get the current time in UTC"
    }
  }
]

resp = requests.post(
  "http://localhost:11434/v1/chat/completions",
  headers={"Content-Type": "application/json"},
  data=json.dumps({
    "model": "hf.co/bartowski/allenai_Llama-3.1-Tulu-3.1-8B-GGUF:Q6_K_L",
    "messages": [
      {"role": "user", "content": "Call get_time and then tell me the result."}
    ],
    "tools": tools,
    "tool_choice": "auto"
  })
)

print(resp.json())
tool_result = "2025-12-06T13:30:00Z"  # your real result

resp2 = requests.post(
  "http://localhost:11434/v1/chat/completions",
  headers={"Content-Type": "application/json"},
  data=json.dumps({
    "model": "hf.co/bartowski/allenai_Llama-3.1-Tulu-3.1-8B-GGUF:Q6_K_L",
    "messages": [
      {"role": "user", "content": "Call get_time and then tell me the result."},
      {
        "role": "assistant",
        "tool_calls": [{
          "type": "function",
          "function": {"name": "get_time", "arguments": "{}"},
          "id": "call_1"
        }]
      },
      {
        "role": "tool",
        "tool_call_id": "call_1",
        "name": "get_time",
        "content": tool_result
      }
    ],
  })
)

print(resp2.json())
