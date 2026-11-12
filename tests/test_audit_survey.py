import pytest
from unittest.mock import AsyncMock, MagicMock
from services.audit_logger import (
    log_interaction,
    record_survey,
    is_awaiting_feedback,
    record_feedback_explanation,
    generate_diagnostic_report,
    _load_data,
    AUDIT_FILE,
)
from services.llm_orchestrator import LLMOrchestrator


@pytest.mark.asyncio
async def test_audit_log_interaction(tmp_path, monkeypatch):
    test_file = tmp_path / "audit_log.json"
    monkeypatch.setattr("services.audit_logger.AUDIT_FILE", test_file)
    monkeypatch.setattr("services.audit_logger.AUDIT_DIR", tmp_path)

    log_interaction(
        user_id="919384146157",
        input_type="text",
        user_query="Tell me about Stranger Things",
        bot_reply="Here is Stranger Things overview...",
    )
    log_interaction(
        user_id="919384146157",
        input_type="audio",
        user_query="Trichy-la nalla veg food enga bro kedaikum",
        bot_reply="Trichy-la Shri Sangeethas super spot bro!",
        is_voice=True,
        raw_transcript="Trichy-la nalla veg food enga bro kedaikum",
    )

    data = _load_data()
    assert len(data["interactions"]) == 2
    assert data["interactions"][1]["is_voice"] is True
    assert data["interactions"][1]["raw_transcript"] == "Trichy-la nalla veg food enga bro kedaikum"


@pytest.mark.asyncio
async def test_survey_positive(tmp_path, monkeypatch, settings, memory):
    test_file = tmp_path / "audit_log.json"
    monkeypatch.setattr("services.audit_logger.AUDIT_FILE", test_file)
    monkeypatch.setattr("services.audit_logger.AUDIT_DIR", tmp_path)

    orchestrator = LLMOrchestrator(
        settings=settings,
        memory=memory,
        whatsapp=MagicMock(),
        transit=MagicMock(),
        booking=MagicMock(),
        shopping=MagicMock(),
        local=MagicMock(),
    )
    user_id = "919999999991"

    # 1. User asks question
    log_interaction(user_id, "text", "Weather today", "Sunny and 30C")

    # 2. User clicks 👍 Yes
    res = await orchestrator.handle_interactive_turn(user_id, "survey_pos")
    assert "nandri" in res["reply"].lower() or "நன்றி" in res["reply"]
    data = _load_data()
    assert len(data["surveys"]) == 1
    assert data["surveys"][0]["satisfied"] is True


@pytest.mark.asyncio
async def test_survey_negative_and_feedback_capture(tmp_path, monkeypatch, settings, memory):
    test_file = tmp_path / "audit_log.json"
    monkeypatch.setattr("services.audit_logger.AUDIT_FILE", test_file)
    monkeypatch.setattr("services.audit_logger.AUDIT_DIR", tmp_path)

    orchestrator = LLMOrchestrator(
        settings=settings,
        memory=memory,
        whatsapp=MagicMock(),
        transit=MagicMock(),
        booking=MagicMock(),
        shopping=MagicMock(),
        local=MagicMock(),
    )
    user_id = "919999999992"

    # 1. User asked something in voice
    log_interaction(
        user_id,
        "audio",
        "Train time to Madurai",
        "Here are trains to Madurai",
        is_voice=True,
        raw_transcript="Train time to Madurai",
    )

    # 2. User clicks 👎 No
    res1 = await orchestrator.handle_interactive_turn(user_id, "survey_neg")
    assert "sorry" in res1["reply"].lower()
    assert is_awaiting_feedback(user_id) is True

    # 3. User explains the issue
    complaint = "I asked for evening trains but you showed morning trains"
    res2 = await orchestrator.handle_interactive_turn(user_id, complaint)
    assert "feedback" in res2["reply"].lower() or "noted" in res2["reply"].lower()
    assert is_awaiting_feedback(user_id) is False

    data = _load_data()
    assert len(data["unresolved_issues"]) == 1
    assert data["unresolved_issues"][0]["user_complaint"] == complaint
    assert data["unresolved_issues"][0]["is_voice"] is True


@pytest.mark.asyncio
async def test_diagnostic_report_command(tmp_path, monkeypatch, settings, memory):
    test_file = tmp_path / "audit_log.json"
    test_report = tmp_path / "audit_report.md"
    monkeypatch.setattr("services.audit_logger.AUDIT_FILE", test_file)
    monkeypatch.setattr("services.audit_logger.AUDIT_DIR", tmp_path)
    monkeypatch.setattr("services.audit_logger.REPORT_FILE", test_report)

    orchestrator = LLMOrchestrator(
        settings=settings,
        memory=memory,
        whatsapp=MagicMock(),
        transit=MagicMock(),
        booking=MagicMock(),
        shopping=MagicMock(),
        local=MagicMock(),
    )
    user_id = "919384146157"

    # Populate some interactions
    log_interaction(user_id, "text", "Best cafe?", "Cafe Coffee Day")
    record_survey(user_id, satisfied=True)

    res = await orchestrator.handle_interactive_turn(user_id, "/report")
    assert "Diagnostic Report" in res["reply"]
    assert "Active Users" in res["reply"]
    assert "100.0%" in res["reply"]


@pytest.mark.asyncio
async def test_human_support_handoff(settings, memory):
    orchestrator = LLMOrchestrator(
        settings=settings,
        memory=memory,
        whatsapp=MagicMock(),
        transit=MagicMock(),
        booking=MagicMock(),
        shopping=MagicMock(),
        local=MagicMock(),
    )
    user_id = "test_user_support"
    res = await orchestrator.handle_interactive_turn(user_id, "human support")
    assert "Human Support" in res["reply"]
    assert "+91 93841 46157" in res["reply"]


@pytest.mark.asyncio
async def test_ecommerce_shopping_compare(settings, memory):
    mock_shopping = AsyncMock()
    mock_shopping.compare_ecommerce_products.return_value = {
        "products": [
            {
                "store": "flipkart",
                "title": "boAt Airdopes 141 ANC",
                "price_inr": 1099.0,
                "rating": 4.3,
                "review_sentiment": {"pros": "Bass", "cons": "Case"},
                "url": "https://flipkart.com",
            },
            {
                "store": "amazon",
                "title": "OnePlus Nord Buds 2r",
                "price_inr": 1799.0,
                "rating": 4.6,
                "review_sentiment": {"pros": "Vocals", "cons": "No multipoint"},
                "url": "https://amazon.in",
            },
        ]
    }
    orchestrator = LLMOrchestrator(
        settings=settings,
        memory=memory,
        whatsapp=MagicMock(),
        transit=MagicMock(),
        booking=MagicMock(),
        shopping=mock_shopping,
        local=MagicMock(),
    )
    user_id = "test_user_ecom"
    await memory.update_profile(user_id, {"language": "tanglish", "pincode": "620018", "onboarding_step": "completed"})
    res = await orchestrator.handle_interactive_turn(user_id, "compare earbuds in amazon flipkart")
    assert "Amazon & Flipkart" in res["reply"]
    assert "boAt Airdopes" in res["reply"]
    assert "OnePlus Nord Buds" in res["reply"]
    assert "Safety & Purchase Warning" in res["reply"]


@pytest.mark.asyncio
async def test_reverse_scout_hidden_gems(settings, memory):
    user_id = "test_user_scout"
    await memory.update_profile(user_id, {"place": "trichy", "pincode": "620018", "locality": "Thillai Nagar", "language": "tanglish", "onboarding_step": "completed"})
    orchestrator = LLMOrchestrator(
        settings=settings,
        memory=memory,
        whatsapp=MagicMock(),
        transit=MagicMock(),
        booking=MagicMock(),
        shopping=MagicMock(),
        local=MagicMock(),
    )
    res = await orchestrator.handle_interactive_turn(user_id, "hidden spot near me")
    assert "Mani Mess" in res["reply"] or "Green Courtyard" in res["reply"] or "food spots" in res["reply"]


@pytest.mark.asyncio
async def test_clear_chat_and_reset(settings, memory):
    user_id = "test_user_clear"
    await memory.update_profile(user_id, {"place": "trichy", "language": "tamil", "onboarding_step": "completed"})
    await memory.append_message(user_id, "user", "Hello earlier message")
    orchestrator = LLMOrchestrator(
        settings=settings,
        memory=memory,
        whatsapp=MagicMock(),
        transit=MagicMock(),
        booking=MagicMock(),
        shopping=MagicMock(),
        local=MagicMock(),
    )
    # Trigger Clear Chat command in English and Tamil
    res_en = await orchestrator.handle_interactive_turn(user_id, "clear chat")
    assert "அழிக்கப்பட்டது" in res_en["reply"] or "Cleared" in res_en["reply"]
    assert any(b["id"] == "lang_tamil" for b in res_en["buttons"])

    # Verify session profile was cleared
    session = await memory.get_session(user_id)
    assert session.profile == {}

    # Trigger Clear Chat in Tamil
    await memory.update_profile(user_id, {"pincode": "600028"})
    res_ta = await orchestrator.handle_interactive_turn(user_id, "கிளியர்")
    assert "அழிக்கப்பட்டது" in res_ta["reply"]
    session_after = await memory.get_session(user_id)
    assert session_after.profile == {}


@pytest.mark.asyncio
async def test_safe_send_buttons_clamping(settings, memory):
    mock_whatsapp = AsyncMock()
    orchestrator = LLMOrchestrator(
        settings=settings,
        memory=memory,
        whatsapp=mock_whatsapp,
        transit=MagicMock(),
        booking=MagicMock(),
        shopping=MagicMock(),
        local=MagicMock(),
    )
    # Pass a button with title > 20 characters
    long_buttons = [
        {"id": "b1", "title": "This title is way longer than twenty characters for sure"}
    ]
    await orchestrator._safe_send_buttons("test_user_btn", "Choose option", long_buttons)
    mock_whatsapp.send_buttons.assert_called_once()
    called_btns = mock_whatsapp.send_buttons.call_args[0][2]
    assert len(called_btns) == 1
    assert len(called_btns[0]["title"]) <= 20
