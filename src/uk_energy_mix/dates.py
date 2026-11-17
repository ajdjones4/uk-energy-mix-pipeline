import datetime
from zoneinfo import ZoneInfo


def date_window(
    snapshot_date: datetime.date,
    window: int,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
) -> tuple[datetime.date, datetime.date]:
    """Return the date window for which data should be fetched
    
    Missing end_date defaults to the day before snapshot_date, missing 
    start_date gives a window of window days ending on end_date. Given dates
    pass through unchanged. Ordering not checked.

    """
    if end_date is None:
        end_date = snapshot_date - datetime.timedelta(days=1)
    if start_date is None:
        start_date = end_date - datetime.timedelta(days=(window - 1))
    return (start_date, end_date)


def expected_records(
    start_date: datetime.date, end_date: datetime.date, date_tz: str
) -> int:
    """Calculate the number of 30 minute intervals in the given date range.
    
    Args:
        date_tz: The timezone of the date range

    """
    end_date_exclusive = end_date + datetime.timedelta(days=1)
    start_date_local = datetime.datetime.combine(
        start_date, time=datetime.time.min, tzinfo=ZoneInfo(date_tz)
    )
    end_date_exclusive_local = datetime.datetime.combine(
        end_date_exclusive, time=datetime.time.min, tzinfo=ZoneInfo(date_tz)
    )
    start_date_utc = start_date_local.astimezone(datetime.UTC)
    end_date_exclusive_utc = end_date_exclusive_local.astimezone(datetime.UTC)
    interval = end_date_exclusive_utc - start_date_utc
    periods = interval / datetime.timedelta(minutes=30)
    return int(periods)