"""Application clock: all business datetimes use Africa/Johannesburg (SAST, UTC+2).

Stored values are naive datetimes representing wall-clock time in this zone.
Override with env APP_TIMEZONE (IANA name, e.g. Africa/Johannesburg).
"""
from __future__ import annotations

import os
import time
from datetime import date, datetime
from zoneinfo import ZoneInfo

_APP_TZ_NAME = os.environ.get("APP_TIMEZONE", "Africa/Johannesburg")
try:
    APP_TZ = ZoneInfo(_APP_TZ_NAME)
except Exception:
    APP_TZ = ZoneInfo("Africa/Johannesburg")
    _APP_TZ_NAME = "Africa/Johannesburg"

# Short label for UI copy
APP_TIMEZONE_LABEL = "Johannesburg (SAST, UTC+2)"


def app_now() -> datetime:
    """Current wall-clock time in the app timezone, as naive datetime."""
    return datetime.now(APP_TZ).replace(tzinfo=None)


def app_today() -> date:
    """Current calendar date in the app timezone."""
    return datetime.now(APP_TZ).date()


def app_timestamp() -> float:
    """Unix timestamp for the current instant (not tied to naive storage)."""
    return time.time()
