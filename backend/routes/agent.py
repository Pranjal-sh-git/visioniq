"""Agent query and multimodal reasoning API route definitions."""

import logging
from typing import Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agent.agent import VisionIQAgent

try:
    from backend.timing import profile_timer
except ImportError:
    from timing import profile_timer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["Agent Orchestration"])

# Singleton instance of VisionIQAgent
_agent_instance: Optional[VisionIQAgent] = None


def get_agent() -> VisionIQAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = VisionIQAgent()
    return _agent_instance


class AgentQueryRequest(BaseModel):
    prompt: str = Field(..., description="User's natural language question or follow-up prompt.")
    product_id: Optional[str] = Field(None, description="Optional active product ID context (e.g. 'P001').")
    video_id: Optional[str] = Field(None, description="Optional active video ID context.")
    media_url: Optional[str] = Field(None, description="Optional image/media URL context.")
    product_info: Optional[dict[str, Any]] = Field(None, description="Optional open-world product identification metadata.")


@router.post("/query")
async def query_agent_endpoint(request: AgentQueryRequest):
    """Executes the Microsoft Foundry Agent with genuine tool calling."""
    with profile_timer("qa:request_parse"):
        prompt_text = request.prompt.strip()
        if not prompt_text:
            raise HTTPException(status_code=400, detail="prompt cannot be empty.")
        p_id = request.product_id
        v_id = request.video_id
        m_url = request.media_url
        p_info = request.product_info

    try:
        agent = get_agent()
        result = agent.run(
            user_prompt=prompt_text,
            product_id=p_id,
            video_id=v_id,
            media_url=m_url,
            product_info=p_info,
        )
        with profile_timer("qa:response_serialization"):
            final_res = result
        return final_res
    except Exception as e:
        logger.exception("Error executing VisionIQ agent run")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")
