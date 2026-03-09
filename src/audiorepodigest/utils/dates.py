from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from audiorepodigest.models import DateRange, ReportFrequency


def parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    return date.fromisoformat(value)


def _start_of_day(value: date, timezone: str) -> datetime:
    return datetime.combine(value, time.min, tzinfo=ZoneInfo(timezone))


def _first_day_of_current_month(now: datetime) -> datetime:
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def resolve_period(
    *,
    frequency: ReportFrequency,
    timezone: str,
    start_date: date | None = None,
    end_date: date | None = None,
    lookback_days: int = 7,
    now: datetime | None = None,
) -> DateRange:
    tz = ZoneInfo(timezone)
    current = now.astimezone(tz) if now is not None else datetime.now(tz)

    if start_date and end_date:
        start = _start_of_day(start_date, timezone)
        end = _start_of_day(end_date + timedelta(days=1), timezone)
    elif start_date or end_date:
        raise ValueError("start_date and end_date must either both be supplied or both be omitted.")
    elif frequency is ReportFrequency.DAILY:
        end = current.replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=1)
    elif frequency is ReportFrequency.WEEKLY:
        end = current.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
            days=current.weekday()
        )
        start = end - timedelta(days=7)
    elif frequency is ReportFrequency.MONTHLY:
        end = _first_day_of_current_month(current)
        previous_month_end = end - timedelta(days=1)
        start = previous_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        end = current
        start = end - timedelta(days=lookback_days)

    display_end = (end - timedelta(seconds=1)).date()
    label = f"{start.date().isoformat()} to {display_end.isoformat()}"
    return DateRange(start=start, end=end, label=label)


def format_timestamp(value: datetime, timezone: str) -> str:
    localized = value.astimezone(ZoneInfo(timezone))
    return localized.strftime("%Y-%m-%d %H:%M %Z")
