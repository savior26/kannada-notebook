from datetime import datetime, timedelta, timezone


INDIA_TIMEZONE = timezone(timedelta(hours=5, minutes=30), name="IST")


def to_india_time(value: datetime) -> datetime:
    """Convert a database datetime to Asia/Kolkata, treating naive values as UTC."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(INDIA_TIMEZONE)


def format_india_time(value: datetime) -> str:
    return to_india_time(value).strftime("%d %b %Y, %I:%M %p IST")
