"""Centralized Azure OpenAI LLM Service for VisionIQ.

Provides client instantiation and grounded answer generation using the deployed
Foundry Azure OpenAI model (gpt-5-mini). All API calls log deployment status without secrets.
"""

import logging
from typing import Any, Optional
from openai import AzureOpenAI

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
for directory in (str(ROOT_DIR), str(ROOT_DIR / "backend")):
    if directory not in sys.path:
        sys.path.insert(0, directory)

try:
    from backend.config import settings
except ImportError:
    from config import settings

logger = logging.getLogger("visioniq.llm")

_OPENAI_CLIENT: Optional[AzureOpenAI] = None


def get_azure_openai_client() -> AzureOpenAI:
    """Instantiates or returns cached AzureOpenAI client from environment configuration."""
    global _OPENAI_CLIENT
    raw_endpoint = settings.AZURE_OPENAI_ENDPOINT
    key = settings.AZURE_OPENAI_API_KEY
    if not raw_endpoint or not key:
        raise ValueError(
            "AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be configured in .env "
            "for real Azure OpenAI model inference."
        )
    print(f"[AZURE_OPENAI_ENDPOINT raw from env]: '{raw_endpoint}'")
    
    # Strip any trailing path components if the user pasted a full route or Foundry URL
    clean_endpoint = raw_endpoint.split("/openai")[0].split("/models")[0].rstrip("/")
    print(f"[AZURE_OPENAI_CLIENT init]: azure_endpoint='{clean_endpoint}', api_version='2024-06-01'")
    
    if _OPENAI_CLIENT is None:
        _OPENAI_CLIENT = AzureOpenAI(
            azure_endpoint=clean_endpoint,
            api_key=key,
            api_version="2024-06-01",
        )
    return _OPENAI_CLIENT


def generate_grounded_answer(
    user_question: str,
    retrieved_context: str,
    system_instruction: Optional[str] = None,
) -> str:
    """Generates a natural-language answer strictly grounded in retrieved catalog/video data.

    Instructs the LLM to answer ONLY using the provided retrieved context,
    and to explicitly state that the information is unavailable if absent.

    Args:
        user_question (str): User's natural language question.
        retrieved_context (str): Grounded context retrieved from Azure AI Search / video analysis.
        system_instruction (Optional[str]): Custom prompt instructions.

    Returns:
        str: LLM-generated grounded answer.
    """
    client = get_azure_openai_client()
    deployment = settings.AZURE_OPENAI_DEPLOYMENT_NAME

    sys_prompt = system_instruction or (
        "You are VisionIQ's Strict Grounded Answering Assistant. "
        "Answer the user's question using ONLY the exact facts and specification values present in the provided retrieved context. "
        "CRITICAL GROUNDING RULES:\n"
        "1. Do NOT extrapolate, enrich, or add external real-world knowledge (e.g. do NOT add qualifiers, caveats, or conditions unless they are explicitly written under that exact specification field in the context).\n"
        "2. State the exact specification value verbatim and concisely.\n"
        "3. If the requested information is absent or not explicitly stated in the retrieved context, explicitly state:\n"
        "'This information is not specified in the retrieved catalog/video data.'"
    )

    user_content = (
        f"--- RETRIEVED CONTEXT ---\n{retrieved_context}\n\n"
        f"--- USER QUESTION ---\n{user_question}"
    )

    try:
        print(f"[AZURE OPENAI CALLING] Base URL: {client.base_url} | Deployment: {deployment}")
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_content},
            ],
            max_completion_tokens=2500,
        )
        usage = response.usage
        usage_info = f"Total={usage.total_tokens}, Prompt={usage.prompt_tokens}, Completion={usage.completion_tokens}" if usage else "N/A"
        print(f"[AZURE OPENAI RESPONSE] ID: {response.id} | Model: {response.model} | Usage: {usage_info}")
        logger.info(f"[AZURE OPENAI CALL] Deployment: {deployment} | Response ID: {response.id} | Status: SUCCESS")
        content = response.choices[0].message.content
        return (content or "").strip()
    except Exception as e:
        logger.error(f"[AZURE OPENAI ERROR] Call to deployment '{deployment}' failed: {e}")
        raise RuntimeError(f"Azure OpenAI generation failed on deployment '{deployment}': {str(e)}") from e

