import datetime

import pytest

from uk_energy_mix import dates

SNAPSHOT_DATE = datetime.date.fromisoformat("2026-11-12")
LONDON = "Europe/London"
UTC = "UTC"

@pytest.mark.parametrize(
    ("date_from", "date_to", "timezone", "expected"),
    [
        (datetime.date(2026, 10, 25), datetime.date(2026, 10, 25), LONDON, 50),
        (datetime.date(2026, 10, 25), datetime.date(2026, 10, 25), UTC, 48),
        (datetime.date(2026, 3, 23), datetime.date(2026, 3, 30), LONDON, 382),
        (datetime.date(2026, 3, 23), datetime.date(2026, 3, 30), UTC, 384),
    ],
    ids=[
        "london_oct_change",
        "utc_oct_change",
        "london_march_change_range",
        "utc_march_change_range",
    ],
)
def test_expected_records(date_from, date_to, timezone, expected):
    assert dates.expected_records(date_from, date_to, timezone) == expected


@pytest.mark.parametrize(
    ("window", "start_date", "end_date", "expected"),
    [
        (
            10,
            None,
            datetime.date(2026, 11, 10),
            (datetime.date(2026, 11, 1), datetime.date(2026, 11, 10)),
        ),
        (
            10,
            datetime.date(2026, 11, 10),
            None,
            (datetime.date(2026, 11, 10), datetime.date(2026, 11, 11)),
        ),
        (10, None, None, (datetime.date(2026, 11, 2), datetime.date(2026, 11, 11))),
        (
            10,
            datetime.date(2026, 10, 25),
            datetime.date(2026, 10, 30),
            (datetime.date(2026, 10, 25), datetime.date(2026, 10, 30)),
        ),
        (1, None, None, (datetime.date(2026, 11, 11), datetime.date(2026, 11, 11))),
    ],
    ids=["no-start", "no-end", "no-given-dates", "given-both-dates", "window-length-1"],
)
def test_date_window(window, start_date, end_date, expected):
    assert dates.date_window(SNAPSHOT_DATE, window, start_date, end_date) == expected


@pytest.mark.parametrize(
    ("start_date", "end_date", "chunk_length", "expected_output"),
    [
        (datetime.date(2026, 11, 1), 
         datetime.date(2026, 11, 1), 
         14, 
         [(datetime.date(2026, 11, 1), datetime.date(2026, 11, 1))]),
        (datetime.date(2026, 11, 1), 
         datetime.date(2026, 11, 7), 
         3, 
         [(datetime.date(2026, 11, 1), datetime.date(2026, 11, 3)),
          (datetime.date(2026, 11, 4), datetime.date(2026, 11, 6)),
          (datetime.date(2026, 11, 7), datetime.date(2026, 11, 7))]),
        (datetime.date(2026, 11, 1), 
         datetime.date(2026, 11, 28), 
         14, 
         [(datetime.date(2026, 11, 1), datetime.date(2026, 11, 14)),
         (datetime.date(2026, 11, 15), datetime.date(2026, 11, 28))]),
        (datetime.date(2026, 11, 1), 
         datetime.date(2026, 11, 29), 
         14, 
         [(datetime.date(2026, 11, 1), datetime.date(2026, 11, 14)),
         (datetime.date(2026, 11, 15), datetime.date(2026, 11, 28)),
         (datetime.date(2026, 11, 29), datetime.date(2026, 11, 29))])
    ]
)
def test_chunk_dates(start_date, end_date, chunk_length, expected_output):
    assert dates.chunk_dates(start_date, end_date, chunk_length) == expected_output


@pytest.mark.parametrize(
        ("chunk_length"),
        [0, -1],
)
def test_chunk_dates_raises(chunk_length):
    with pytest.raises(ValueError, match="must be greater than"):
        dates.chunk_dates(datetime.date(2026, 11, 1), datetime.date(2026, 11, 12), chunk_length)






