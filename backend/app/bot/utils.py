"""Bot utility functions"""
import re
from datetime import datetime, timezone as dt_timezone
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


# Day name mapping (Python weekday 0=Monday)
WEEKDAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def is_within_business_hours(business_hours: Optional[dict], timezone: str = "UTC") -> bool:
    """
    Check if the current time falls within configured business hours.

    Args:
        business_hours: Dict with day names as keys. Each value is either:
            - {"open": "HH:MM", "close": "HH:MM"} for open days
            - null / missing key for closed days
          Example:
            {
              "monday": {"open": "07:00", "close": "17:00"},
              "saturday": {"open": "07:00", "close": "12:00"},
              "sunday": null
            }
        timezone: IANA timezone string (e.g. "Africa/Douala")

    Returns:
        True if currently within business hours (or if no business_hours configured).
        False if outside business hours.
    """
    # If no business hours configured, always open
    if not business_hours:
        return True

    try:
        tz = ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, KeyError):
        tz = ZoneInfo("UTC")

    now = datetime.now(tz)
    day_name = WEEKDAY_NAMES[now.weekday()]

    day_config = business_hours.get(day_name)

    # Day not configured or explicitly null = closed
    if not day_config:
        return False

    open_time_str = day_config.get("open")
    close_time_str = day_config.get("close")

    if not open_time_str or not close_time_str:
        return False

    try:
        open_hour, open_min = map(int, open_time_str.split(":"))
        close_hour, close_min = map(int, close_time_str.split(":"))
    except (ValueError, AttributeError):
        return True  # Malformed config → treat as open

    current_minutes = now.hour * 60 + now.minute
    open_minutes = open_hour * 60 + open_min
    close_minutes = close_hour * 60 + close_min

    return open_minutes <= current_minutes < close_minutes


def interpolate_message(text: Optional[str], timezone: str = "UTC") -> Optional[str]:
    """
    Replace built-in placeholders in a bot message.

    Supported placeholders:
      {now}   — current datetime  e.g. 07/07/2026 14:30
      {date}  — current date      e.g. 07/07/2026
      {time}  — current time      e.g. 14:30
    """
    if not text or '{' not in text:
        return text

    try:
        tz = ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, KeyError):
        tz = ZoneInfo("UTC")

    now = datetime.now(tz)
    built_in = {
        'now':  now.strftime('%d/%m/%Y %H:%M'),
        'date': now.strftime('%d/%m/%Y'),
        'time': now.strftime('%H:%M'),
    }

    def replacer(match: re.Match) -> str:
        key = match.group(1)
        return built_in.get(key, match.group(0))

    return re.sub(r'\{(\w+)\}', replacer, text)
