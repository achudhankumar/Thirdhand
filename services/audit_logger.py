import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

AUDIT_DIR = Path("data/whatsapp")
AUDIT_FILE = AUDIT_DIR / "audit_log.json"
REPORT_FILE = AUDIT_DIR / "audit_report.md"


def _ensure_dir():
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def _load_data() -> dict[str, Any]:
    _ensure_dir()
    if not AUDIT_FILE.exists():
        return {
            "interactions": [],
            "surveys": [],
            "unresolved_issues": [],
            "awaiting_feedback": {},
        }
    try:
        return json.loads(AUDIT_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Could not read audit log (%s), initializing empty", exc)
        return {
            "interactions": [],
            "surveys": [],
            "unresolved_issues": [],
            "awaiting_feedback": {},
        }


def _save_data(data: dict[str, Any]) -> None:
    _ensure_dir()
    AUDIT_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def log_interaction(
    user_id: str,
    input_type: str,
    user_query: str,
    bot_reply: str,
    is_voice: bool = False,
    raw_transcript: str | None = None,
) -> dict:
    data = _load_data()
    now_iso = datetime.now(timezone.utc).isoformat()
    record = {
        "id": f"int_{len(data['interactions']) + 1}_{int(datetime.now(timezone.utc).timestamp())}",
        "user_id": str(user_id),
        "timestamp": now_iso,
        "input_type": input_type,
        "is_voice": is_voice,
        "retention_policy": "ephemeral_privacy_aware",
        "raw_transcript": raw_transcript or (user_query if is_voice else None),
        "user_query": user_query[:500],
        "bot_reply": bot_reply[:1000],
    }
    data["interactions"].append(record)
    # keep last 2000 interactions
    if len(data["interactions"]) > 2000:
        data["interactions"] = data["interactions"][-2000:]
    _save_data(data)
    return record


def set_awaiting_feedback(user_id: str, awaiting: bool = True) -> None:
    data = _load_data()
    if awaiting:
        # find the last interaction for this user
        user_ints = [i for i in data["interactions"] if i["user_id"] == str(user_id)]
        last_int_id = user_ints[-1]["id"] if user_ints else None
        data["awaiting_feedback"][str(user_id)] = {
            "interaction_id": last_int_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    else:
        data["awaiting_feedback"].pop(str(user_id), None)
    _save_data(data)


def is_awaiting_feedback(user_id: str) -> bool:
    data = _load_data()
    return str(user_id) in data.get("awaiting_feedback", {})


def clear_awaiting_feedback(user_id: str) -> None:
    set_awaiting_feedback(user_id, False)


def record_survey(user_id: str, satisfied: bool) -> dict:
    data = _load_data()
    now_iso = datetime.now(timezone.utc).isoformat()
    user_ints = [i for i in data["interactions"] if i["user_id"] == str(user_id)]
    last_int = user_ints[-1] if user_ints else None

    survey_entry = {
        "user_id": str(user_id),
        "timestamp": now_iso,
        "satisfied": satisfied,
        "interaction_id": last_int["id"] if last_int else None,
        "user_query": last_int["user_query"] if last_int else "",
        "is_voice": last_int.get("is_voice", False) if last_int else False,
        "raw_transcript": last_int.get("raw_transcript") if last_int else None,
    }
    data["surveys"].append(survey_entry)
    _save_data(data)

    if not satisfied:
        set_awaiting_feedback(user_id, awaiting=True)
    else:
        set_awaiting_feedback(user_id, awaiting=False)
    return survey_entry


def record_feedback_explanation(user_id: str, explanation: str) -> dict:
    data = _load_data()
    now_iso = datetime.now(timezone.utc).isoformat()
    awaiting_info = data.get("awaiting_feedback", {}).get(str(user_id), {})
    int_id = awaiting_info.get("interaction_id")

    # Locate interaction
    target_int = None
    for item in reversed(data["interactions"]):
        if item["id"] == int_id:
            target_int = item
            break
    if not target_int:
        user_ints = [i for i in data["interactions"] if i["user_id"] == str(user_id)]
        target_int = user_ints[-1] if user_ints else {}

    issue = {
        "user_id": str(user_id),
        "timestamp": now_iso,
        "user_query": target_int.get("user_query", "Unknown"),
        "is_voice": target_int.get("is_voice", False),
        "raw_transcript": target_int.get("raw_transcript"),
        "bot_reply": target_int.get("bot_reply", "")[:500],
        "user_complaint": explanation,
    }
    data["unresolved_issues"].append(issue)
    if "awaiting_feedback" in data:
        data["awaiting_feedback"].pop(str(user_id), None)
    _save_data(data)
    return issue


def generate_diagnostic_report() -> str:
    data = _load_data()
    interactions = data.get("interactions", [])
    surveys = data.get("surveys", [])
    issues = data.get("unresolved_issues", [])

    total_queries = len(interactions)
    unique_users = len({i["user_id"] for i in interactions})
    voice_notes = len([i for i in interactions if i.get("is_voice")])

    pos_surveys = len([s for s in surveys if s.get("satisfied") is True])
    neg_surveys = len([s for s in surveys if s.get("satisfied") is False])
    total_surveys = pos_surveys + neg_surveys
    satisfaction_rate = (
        f"{(pos_surveys / total_surveys * 100):.1f}%" if total_surveys > 0 else "N/A"
    )

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "# 📊 Thirdhand AI - Multi-User Quality & Diagnostic Report",
        f"*Generated on: {now_str}*",
        "",
        "### 📈 Summary Metrics",
        f"- **Active Users:** {unique_users}",
        f"- **Total Interactions:** {total_queries}",
        f"- **Voice Notes (STT):** {voice_notes}",
        f"- **Survey Responses:** {total_surveys} (👍 {pos_surveys} Yes | 👎 {neg_surveys} No)",
        f"- **User Satisfaction Rate:** {satisfaction_rate}",
        f"- **Recorded Unresolved Issues:** {len(issues)}",
        "",
    ]

    if issues:
        lines.append("### ⚠️ Recorded Gaps & Unresolved Issues")
        lines.append("| Time | User | Voice? | User Asked (Transcript) | User Complaint / Feedback |")
        lines.append("|---|---|---|---|---|")
        for iss in issues[-20:]:
            is_v = "🎙️ Voice" if iss.get("is_voice") else "💬 Text"
            asked = (iss.get("raw_transcript") or iss.get("user_query") or "").replace("|", "-").replace("\n", " ")[:60]
            complaint = (iss.get("user_complaint") or "").replace("|", "-").replace("\n", " ")[:80]
            uid = iss.get("user_id")[-4:] if len(iss.get("user_id", "")) > 4 else iss.get("user_id")
            time_short = iss.get("timestamp", "")[:19].replace("T", " ")
            lines.append(f"| {time_short} | ...{uid} | {is_v} | {asked} | {complaint} |")
        lines.append("")
    else:
        lines.append("### ⚠️ Recorded Gaps & Unresolved Issues")
        lines.append("*No complaints or negative survey responses recorded yet. Everything running smoothly!*")
        lines.append("")

    if voice_notes > 0:
        lines.append("### 🎙️ Recent Voice Note Transcriptions")
        lines.append("| Time | User | Transcribed Speech | Bot Response Preview |")
        lines.append("|---|---|---|---|")
        recent_voices = [i for i in interactions if i.get("is_voice")][-10:]
        for v in recent_voices:
            transcript = (v.get("raw_transcript") or v.get("user_query") or "").replace("|", "-").replace("\n", " ")[:60]
            resp_preview = (v.get("bot_reply") or "").replace("|", "-").replace("\n", " ")[:50]
            uid = v.get("user_id")[-4:] if len(v.get("user_id", "")) > 4 else v.get("user_id")
            time_short = v.get("timestamp", "")[:19].replace("T", " ")
            lines.append(f"| {time_short} | ...{uid} | {transcript} | {resp_preview} |")
        lines.append("")

    report_content = "\n".join(lines)
    _ensure_dir()
    REPORT_FILE.write_text(report_content, encoding="utf-8")
    return report_content
