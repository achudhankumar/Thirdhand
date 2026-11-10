"""Test Zepto Quick-Commerce Family Cart & Guardian Approval."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from database.astra_db import AstraMemory
from services.llm_orchestrator import LLMOrchestrator
from services.tools.zepto_tool import parse_zepto_cart_items, format_zepto_approval_card, format_zepto_confirmed_card


def test_zepto_cart_parsing():
    items = parse_zepto_cart_items("Zepto-la 2 milk and 1 bread order podu")
    assert len(items) == 2
    names = [i["name"] for i in items]
    assert any("Milk" in n for n in names)
    assert any("Bread" in n for n in names)


def test_zepto_approval_card():
    items = parse_zepto_cart_items("milk and eggs")
    card = format_zepto_approval_card(items, {"pincode": "620018", "locality": "Trichy"})
    assert "Zepto" in card["reply"]
    assert "Approval" in card["reply"]
    button_ids = [b["id"] for b in card["buttons"]]
    assert "approve_zepto_order" in button_ids
    assert "reject_zepto_order" in button_ids


@pytest.mark.asyncio
async def test_zepto_interactive_flow(settings, memory):
    user_id = "test_user_zepto_flow"
    await memory.update_profile(user_id, {"language": "tanglish", "pincode": "620018", "onboarding_step": "completed"})

    orchestrator = LLMOrchestrator(
        settings=settings,
        memory=memory,
        whatsapp=MagicMock(),
        transit=MagicMock(),
        booking=MagicMock(),
        shopping=MagicMock(),
        local=MagicMock()
    )

    # 1. Ask for Zepto order
    res1 = await orchestrator.handle_interactive_turn(user_id, "Zepto-la Amma-ku 2 milk and bread order podu")
    assert "Zepto" in res1["reply"]
    assert "Approval" in res1["reply"]
    assert any(b["id"] == "approve_zepto_order" for b in res1["buttons"])

    # 2. Family Admin Approves
    res2 = await orchestrator.handle_interactive_turn(user_id, "approve_zepto_order")
    assert "Confirmed" in res2["reply"]
    assert "ZEP-" in res2["reply"]
    assert "zeptonow.com" in res2["reply"]
