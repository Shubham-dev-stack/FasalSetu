from datetime import date, datetime
from zoneinfo import ZoneInfo

IST_TZ = ZoneInfo("Asia/Kolkata")


def today_ist() -> date:
    """Return the current calendar date in Asia/Kolkata timezone."""
    return datetime.now(IST_TZ).date()


def now_ist() -> datetime:
    """Return the current datetime in Asia/Kolkata timezone."""
    return datetime.now(IST_TZ)
