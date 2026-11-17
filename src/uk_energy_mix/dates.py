import datetime
from zoneinfo import ZoneInfo


def date_window(
    run_date: datetime.date,
    window: int,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
) -> tuple[datetime.date, datetime.date]:
    """Take the run date, window length and parsed dates.
       If dates are empty return default date range.
       Default end date is yesterday and default start date is
       the window length before the end date"""
    if end_date is None:
        end_date = run_date - datetime.timedelta(days=1)
    if start_date is None:
        start_date = end_date - datetime.timedelta(days=(window - 1))
    return (start_date, end_date)


def expected_records(
    start_date: datetime.date, end_date: datetime.date, date_tz: str
) -> int:
    """Calculate the number of 30 minute intervals in the given date range"""
    end_date_exclusive = end_date + datetime.timedelta(days=1)
    start_date_local = datetime.datetime.combine(
        start_date, time=datetime.time.min, tzinfo=ZoneInfo(date_tz)
    )
    end_date_exclusive_local = datetime.datetime.combine(
        end_date_exclusive, time=datetime.time.min, tzinfo=ZoneInfo(date_tz)
    )
    dt_from_utc = start_date_local.astimezone(datetime.UTC)
    dt_to_exclusive_utc = end_date_exclusive_local.astimezone(datetime.UTC)
    interval = dt_to_exclusive_utc - dt_from_utc
    periods = interval / datetime.timedelta(minutes=30)
    return int(periods)