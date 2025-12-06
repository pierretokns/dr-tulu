#!/usr/bin/env python3
"""Test script for cloud cost workflow"""

import requests
import json

# Test request
data = {
    "content": "What is the cost to run PostgreSQL on AWS vs GCP?",
    "dataset_name": "cloud_cost"
}

# Send request
response = requests.post(
    "http://localhost:8080/chat/stream",
    headers={"Content-Type": "application/json"},
    json=data,
    stream=True
)

print("Response from server:")
print("-" * 50)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))