import pytest
from unittest.mock import AsyncMock
from config.settings import Settings
from database.astra_db import AstraMemory
from services.llm_orchestrator import LLMOrchestrator
from services.tools.booking_tool import BookingTool
from services.tools.diagram_tool import VisualDiagramTool

@pytest.mark.asyncio
async def test_lazy_onboarding_flow(settings, memory):
    service = LLMOrchestrator(
        settings,
        memory,
        None,
        AsyncMock(),
        BookingTool(settings, memory),
        AsyncMock(),
        AsyncMock(),
        client=AsyncMock(),
    )
    user_id = "test_lazy_user_99"

    # Step 0: Initial greeting prompts language
    res0 = await service.handle_interactive_turn(user_id, "Hi")
    assert len(res0["buttons"]) == 3
    assert (await memory.get_session(user_id)).profile.get("onboarding_step") in (None, "awaiting_language")

    # Step 1: Select Language -> Completes onboarding immediately with NO Pincode prompt!
    res1 = await service.handle_interactive_turn(user_id, "lang_english")
    assert "Welcome" in res1["reply"] or "Thirdhand" in res1["reply"]
    # Verify that Pincode was NOT requested!
    assert "Pincode" not in res1["reply"]
    session = await memory.get_session(user_id)
    assert session.profile["language"] == "english"
    assert session.profile["onboarding_step"] == "completed"
    assert session.profile.get("pincode") is None

    # Step 2: User can chat, ask questions, or generate images freely without pincode gate!
    res2 = await service.handle_interactive_turn(user_id, "What is the speed of light?")
    assert "pincode" not in res2["reply"].lower()

    # Step 3: Lazy Pincode Trigger — When user asks for food/grocery, pincode is requested in-context
    res3 = await service.handle_interactive_turn(user_id, "Order a chicken biryani")
    assert "Pincode" in res3["reply"] or "pincode" in res3["reply"]

    # Step 4: Providing pincode resolves geography and updates profile
    res4 = await service.handle_interactive_turn(user_id, "621209")
    assert "621209" in res4["reply"]
    assert "Perambalur" in res4["reply"] or "Valikandapuram" in res4["reply"]
    session = await memory.get_session(user_id)
    assert session.profile["pincode"] == "621209"
    assert session.profile["onboarding_step"] == "completed"

@pytest.mark.asyncio
async def test_mirage_card_and_flux_engine():
    tool = VisualDiagramTool()
    # Test mirage progress card generation
    card = tool.generate_mirage_card("A futuristic flying car", percentage=75)
    assert card["percentage"] == 75
    assert card["image_url"].endswith(".jpg")

    # Test FLUX.1 neural generation (tier 4 or local fallback)
    res = await tool.generate_ai_art_image("A futuristic flying car")
    assert res["success"] is True
    assert res["image_url"].startswith("http")
    assert res["file_size_bytes"] > 0
