"""Test gpt-5-mini with max_completion_tokens."""

import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv(override=True)
raw_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
clean_endpoint = raw_endpoint.split("/openai")[0].split("/models")[0].rstrip("/")
key = os.getenv("AZURE_OPENAI_API_KEY", "")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5-mini")

print(f"Connecting to: {clean_endpoint} with model {deployment}")

client = AzureOpenAI(
    azure_endpoint=clean_endpoint,
    api_key=key,
    api_version="2024-06-01",
)

try:
    resp = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": "What is 2+2? Reply with just the number."}],
        max_completion_tokens=50,
    )
    print(f"\n[LIVE CALL SUCCEEDED!]")
    print(f"Response ID: {resp.id}")
    print(f"Model: {resp.model}")
    print(f"Content: {resp.choices[0].message.content}")
    print(f"Usage: Total={resp.usage.total_tokens}, Prompt={resp.usage.prompt_tokens}, Completion={resp.usage.completion_tokens}")
except Exception as e:
    print(f"Call failed: {e}")
