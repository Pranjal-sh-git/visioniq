"""Diagnose and test Azure OpenAI / Foundry endpoint connections."""

import os
from pathlib import Path
import sys
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

load_dotenv(override=True)
raw_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
key = os.getenv("AZURE_OPENAI_API_KEY", "")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5-mini")

print(f"Raw AZURE_OPENAI_ENDPOINT: {repr(raw_endpoint)}")
print(f"Deployment Name: {repr(deployment)}")
print(f"Key configured: {bool(key)}")

# Clean root endpoint (strip path suffixes)
clean_endpoint = raw_endpoint.split("/openai")[0].split("/models")[0].rstrip("/")
print(f"Normalized Root Endpoint: {repr(clean_endpoint)}")

from openai import AzureOpenAI, OpenAI

# 1. AzureOpenAI with standard root and api_version 2024-06-01
print("\n[TEST 1] AzureOpenAI(azure_endpoint=clean_endpoint, api_version='2024-06-01')")
try:
    client1 = AzureOpenAI(azure_endpoint=clean_endpoint, api_key=key, api_version="2024-06-01")
    print(f"  Constructed Base URL: {client1.base_url}")
    resp1 = client1.chat.completions.create(model=deployment, messages=[{"role": "user", "content": "Hi"}], max_tokens=10)
    print(f"  SUCCESS! ID: {resp1.id} | Response: {resp1.choices[0].message.content}")
except Exception as e:
    print(f"  FAILED: {e}")

# 2. AzureOpenAI with api_version 2024-05-01-preview
print("\n[TEST 2] AzureOpenAI(azure_endpoint=clean_endpoint, api_version='2024-05-01-preview')")
try:
    client2 = AzureOpenAI(azure_endpoint=clean_endpoint, api_key=key, api_version="2024-05-01-preview")
    resp2 = client2.chat.completions.create(model=deployment, messages=[{"role": "user", "content": "Hi"}], max_tokens=10)
    print(f"  SUCCESS! ID: {resp2.id} | Response: {resp2.choices[0].message.content}")
except Exception as e:
    print(f"  FAILED: {e}")

# 3. OpenAI Client with Foundry /models endpoint
print("\n[TEST 3] OpenAI(base_url=f'{clean_endpoint}/models')")
try:
    client3 = OpenAI(base_url=f"{clean_endpoint}/models", api_key=key)
    print(f"  Constructed Base URL: {client3.base_url}")
    resp3 = client3.chat.completions.create(model=deployment, messages=[{"role": "user", "content": "Hi"}], max_tokens=10)
    print(f"  SUCCESS! ID: {resp3.id} | Response: {resp3.choices[0].message.content}")
except Exception as e:
    print(f"  FAILED: {e}")
