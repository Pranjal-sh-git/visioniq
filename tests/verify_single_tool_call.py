"""Verification script for single message / single tool invocation and clarification behavior."""

import sys
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from agent.agent import VisionIQAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def verify_single_message_tool_count():
    # Fresh session - brand new agent instance with zero prior context or history
    agent = VisionIQAgent()

    # Tool invocation counter map
    call_counts = {name: 0 for name in agent.tool_map.keys()}

    def wrap_tool(name, original_fn):
        def wrapper(*args, **kwargs):
            call_counts[name] += 1
            return original_fn(*args, **kwargs)
        return wrapper

    for name in list(agent.tool_map.keys()):
        agent.tool_map[name] = wrap_tool(name, agent.tool_map[name])

    query = "What is its battery life?"
    result = agent.run(user_prompt=query)

    total_tool_calls = sum(call_counts.values())

    print("\n" + "=" * 65)
    print("TEST 1: FRESH SESSION (NO CONTEXT / NO PRODUCT SPECIFIED)")
    print("=" * 65)
    print(f"User Message: \"{query}\"")
    print(f"Selected Tool: {result['selected_tool']}")
    print(f"Routing Reasoning: {result['routing_reasoning']}")
    print(f"Tool Parameters: {result['tool_parameters']}")
    print("-" * 65)
    print("TOOL INVOCATION AUDIT:")
    for tool_name, count in call_counts.items():
        print(f"  * {tool_name:25s}: {count} invocation(s)")
    print("-" * 65)
    print(f"TOTAL TOOL CALL COUNT: {total_tool_calls}")
    print("-" * 65)
    print(f"ANSWER & CLARIFICATION CHECK:")
    print(f"  * Requires Clarification: {result['tool_output'].get('requires_clarification')}")
    print(f"  * Answer: {result['tool_output'].get('answer')}")
    print("=" * 65)

    assert total_tool_calls == 1, f"Expected exactly 1 tool call, but got {total_tool_calls}"
    assert call_counts["search_product_knowledge"] == 1, "Expected search_product_knowledge to be invoked exactly once"
    assert result["selected_tool"] == "search_product_knowledge", "Expected selected_tool to be search_product_knowledge"
    assert result["tool_output"].get("requires_clarification") is True, "Expected clarification request when no product_id given"
    assert "Which product are you asking about?" in result["tool_output"].get("answer")

    # TEST 2: With specific product_id provided (Check duplicate brand name fix)
    print("\n" + "=" * 65)
    print("TEST 2: SPECIFIED PRODUCT P001 (CHECK BRAND NAME FORMATTING)")
    print("=" * 65)
    result_p001 = agent.run(user_prompt="What is its battery life?", product_id="P001")
    answer_p001 = result_p001["tool_output"].get("answer", "")
    print(f"User Message with product_id='P001': \"{query}\"")
    print(f"Answer: {answer_p001}")
    print("=" * 65)

    assert "Sony Sony" not in answer_p001, "Brand name must not be duplicated!"
    assert "Sony WH-1000XM5" in answer_p001, "Must contain clean product name"
    assert "30 hours" in answer_p001, "Must contain battery life"

    print("\n[VERIFICATION PASS] All checks passed: Honest clarification on missing context + clean brand formatting.")


if __name__ == "__main__":
    verify_single_message_tool_count()
