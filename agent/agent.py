"""Agent orchestration module for VisionIQ using Microsoft Foundry Azure OpenAI Agent Service.

Directly invokes the deployed Azure OpenAI model (gpt-5-mini) for tool selection
via JSON function-calling schemas over the full conversation context.
"""

import json
import logging
from pathlib import Path
import sys
from typing import Any, Optional, Union
from PIL import Image

# Ensure workspace root and backend are on sys.path
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
for directory in (str(ROOT_DIR), str(ROOT_DIR / "backend")):
    if directory not in sys.path:
        sys.path.insert(0, directory)

try:
    from backend.config import settings
except ImportError:
    from config import settings

from agent.prompts import SYSTEM_PROMPT
from agent.tools import (
    find_similar_products,
    identify_product,
    search_product_knowledge,
    search_video,
)
from services.llm import get_azure_openai_client

logger = logging.getLogger("visioniq.agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# ============================================================================
# Microsoft Foundry Agent Tool Definitions (OpenAI Function Schemas)
# ============================================================================

FOUNDRY_TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "identify_product",
            "description": (
                "Identifies ANY commercial product, brand, model, and category from an uploaded image "
                "using open-world multimodal vision AI (gpt-5-mini), and suggests similar catalog items. "
                "Use when the user asks 'What is this product?', 'Identify this item', or provides a product image."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "image_url": {
                        "type": "string",
                        "description": "The URL, local file path, or storage URI of the product image to identify.",
                    },
                    "query": {
                        "type": "string",
                        "description": "Optional text description describing the visual appearance of the product.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of top matching candidate products to retrieve.",
                        "default": 3,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_product_knowledge",
            "description": (
                "Searches product catalog specifications and technical documentation (RAG) "
                "to answer questions about battery life, weight, connectivity, driver size, ANC, price, and specs. "
                "Use when the user asks 'What is its [spec]?', 'How long does the battery last?', or technical details."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user's technical specification or capability question (e.g. 'What is its battery life?').",
                    },
                    "product_id": {
                        "type": "string",
                        "description": "Target product ID (e.g., 'P001') if known from context.",
                    },
                    "product_name": {
                        "type": "string",
                        "description": "Target product brand or model name if known from context.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_video",
            "description": (
                "Searches timestamped segments in a processed video for spoken dialogues, reviewer statements, "
                "scene events, or audience capacity, returning grounded start_time and end_time. "
                "Use when the user asks 'What did the reviewer/speaker say about X?' or inquires about video content."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "video_id": {
                        "type": "string",
                        "description": "The unique video identifier (e.g. 'vid_df16da8f30f96fb6').",
                    },
                    "query": {
                        "type": "string",
                        "description": "The question or description of what the speaker/reviewer said or what occurs in the video.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of candidate video segments to evaluate.",
                        "default": 3,
                    },
                },
                "required": ["video_id", "query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_similar_products",
            "description": (
                "Finds visually or categorically similar product alternatives, recommendations, or comparable items. "
                "Use when the user asks 'Show me similar products', 'What are other alternatives?', or requests related items."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "The source product ID to find alternatives for (e.g. 'P001').",
                    },
                    "image_url": {
                        "type": "string",
                        "description": "Source image URL to perform visual similarity search.",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category filter (e.g. 'Headphones', 'Chairs', 'Shoes').",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of similar products to retrieve.",
                        "default": 4,
                    },
                },
                "required": [],
            },
        },
    },
]


class VisionIQAgent:
    """VisionIQ Multimodal Content Intelligence Agent powered by Microsoft Foundry Agent Service."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        deployment_name: Optional[str] = None,
    ) -> None:
        """Initializes the VisionIQ Agent with Microsoft Foundry tools and Azure OpenAI client."""
        self.endpoint = endpoint or settings.AZURE_OPENAI_ENDPOINT
        self.api_key = api_key or settings.AZURE_OPENAI_API_KEY
        self.deployment_name = deployment_name or settings.AZURE_OPENAI_DEPLOYMENT_NAME
        self.system_prompt = SYSTEM_PROMPT
        self.tool_definitions = FOUNDRY_TOOL_DEFINITIONS

        # Map function names to actual tool implementations
        self.tool_map = {
            "identify_product": identify_product,
            "search_product_knowledge": search_product_knowledge,
            "search_video": search_video,
            "find_similar_products": find_similar_products,
        }

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Returns the registered Microsoft Foundry Agent tool definitions."""
        return self.tool_definitions

    def _select_tool_via_model(
        self,
        messages: list[dict[str, str]],
    ) -> tuple[str, dict[str, Any], str]:
        """Invokes the Azure OpenAI model for genuine tool calling / function calling.

        Raises a visible RuntimeError if the API call fails; no silent keyword fallbacks.

        Returns:
            tuple[str, dict[str, Any], str]: (selected_tool_name, tool_arguments, reasoning)
        """
        client = get_azure_openai_client()
        deployment = self.deployment_name

        try:
            response = client.chat.completions.create(
                model=deployment,
                messages=messages,
                tools=self.tool_definitions,
                tool_choice="auto",
                max_completion_tokens=2000,
            )
            logger.info(f"[AZURE OPENAI CALL] Deployment: {deployment} | Status: SUCCESS")
        except Exception as e:
            logger.error(f"[AZURE OPENAI ERROR] Deployment '{deployment}' tool selection failed: {e}")
            raise RuntimeError(
                f"Azure OpenAI tool selection failed for deployment '{deployment}'. "
                f"Verify AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, and AZURE_OPENAI_DEPLOYMENT_NAME: {str(e)}"
            ) from e

        choice = response.choices[0].message
        if choice.tool_calls:
            call = choice.tool_calls[0]
            tool_name = call.function.name
            tool_args = json.loads(call.function.arguments or "{}")
            reasoning = f"Azure OpenAI ({deployment}) function call: selected '{tool_name}' with parameters {tool_args}"
            return tool_name, tool_args, reasoning

        # If model answered directly without tool invocation
        return (
            "search_product_knowledge",
            {"query": messages[-1]["content"]},
            f"Azure OpenAI ({deployment}) default selection for conversational text: {choice.content}",
        )

    def run(
        self,
        user_prompt: str,
        media_url: Optional[str] = None,
        image: Optional[Union[str, bytes, Path, Image.Image]] = None,
        video_id: Optional[str] = None,
        product_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Executes the Microsoft Foundry Agent with real model-driven tool selection.

        Logs the selected tool and reasoning (no secrets).
        Guarantees that only a single tool is invoked for a single-intent question.

        Args:
            user_prompt (str): User's natural language question or request.
            media_url (Optional[str]): Image or video URL context.
            image (Optional[Any]): Image input.
            video_id (Optional[str]): Target video identifier.
            product_id (Optional[str]): Target product identifier.

        Returns:
            dict[str, Any]: Execution result containing selected tool, reasoning, and tool output.
        """
        context_prompt = user_prompt
        if product_id:
            context_prompt = f"[Context: Product ID is {product_id}] {user_prompt}"
        if video_id:
            context_prompt = f"[Context: Video ID is {video_id}] {user_prompt}"
        if media_url:
            context_prompt = f"[Context: Image URL is {media_url}] {user_prompt}"

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": context_prompt},
        ]

        # Model selects the tool and structured parameters
        tool_name, tool_args, reasoning = self._select_tool_via_model(messages=messages)

        # Merge any explicitly supplied runtime inputs if missing from LLM arguments
        if media_url and "image_url" not in tool_args:
            tool_args["image_url"] = media_url
        if video_id and "video_id" not in tool_args:
            tool_args["video_id"] = video_id
        if product_id and "product_id" not in tool_args:
            tool_args["product_id"] = product_id

        # Log tool selection and reasoning (CRITICAL: no secrets)
        logger.info(f"[ROUTING] Selected tool: '{tool_name}' via Foundry Agent Tool-Calling | Parameters: {tool_args} | Reasoning: {reasoning}")

        # Execute ONLY the single selected tool
        if tool_name not in self.tool_map:
            raise ValueError(f"Unknown tool '{tool_name}' selected by model.")

        tool_func = self.tool_map[tool_name]
        tool_result: Any = None

        if tool_name == "identify_product":
            tool_result = tool_func(
                image=image,
                image_url=tool_args.get("image_url") or media_url,
                query=tool_args.get("query") or user_prompt,
                top_k=tool_args.get("top_k", 3),
            )
        elif tool_name == "search_product_knowledge":
            tool_result = tool_func(
                query=user_prompt or tool_args.get("query", ""),
                product_id=tool_args.get("product_id") or product_id,
                product_name=tool_args.get("product_name"),
            )
        elif tool_name == "search_video":
            tool_result = tool_func(
                video_id=tool_args.get("video_id") or video_id or "vid_df16da8f30f96fb6",
                query=user_prompt or tool_args.get("query", ""),
                top_k=tool_args.get("top_k", 3),
            )
        elif tool_name == "find_similar_products":
            tool_result = tool_func(
                product_id=tool_args.get("product_id") or product_id,
                image=image,
                image_url=tool_args.get("image_url") or media_url,
                category=tool_args.get("category"),
                top_k=tool_args.get("top_k", 4),
            )

        return {
            "query": user_prompt,
            "selected_tool": tool_name,
            "tool_parameters": tool_args,
            "routing_reasoning": reasoning,
            "tool_output": tool_result,
        }
