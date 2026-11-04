from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def add_reminder(state, text, now=None):
    loc = state.get("location")
    if not loc:
        return "Set your city before scheduling a reminder."
    now = now or datetime.now(timezone.utc)
    try:
        date, clock, title = text.split(maxsplit=2)
        local = datetime.fromisoformat(date + "T" + clock)
        if local.tzinfo is not None:
            raise ValueError()
        zone = ZoneInfo(loc["timezone"])
        candidates = set()
        for fold in (0, 1):
            instant = local.replace(tzinfo=zone, fold=fold).astimezone(timezone.utc)
            if instant.astimezone(zone).replace(tzinfo=None) == local:
                candidates.add(instant)
        if len(candidates) != 1:
            return "That time is skipped or repeated by a clock change. Choose another local time."
        due = candidates.pop()
    except ValueError:
        return "Use remind YYYY-MM-DD HH:MM description."
    if not now < due < now + timedelta(hours=23):
        return "Choose a time within the next 23 hours for WhatsApp reminder delivery."
    reminders = state.setdefault("reminders", [])
    if len(reminders) >= 20:
        return "Your reminder list is full."
    reminders.append({"time": due.timestamp(), "title": title[:200]})
    return f"Reminder saved for {local:%Y-%m-%d %H:%M} in {loc['timezone']}."
