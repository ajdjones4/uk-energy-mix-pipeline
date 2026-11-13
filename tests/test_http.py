import requests

import pytest

from uk_energy_mix.ingest import http

def make_http_error(status_code: int) -> requests.HTTPError:
    response = requests.Response()
    response.status_code = status_code
    return requests.HTTPError(response=response)

@pytest.mark.parametrize(
    ("error", "is_retryable"),
    [
        (make_http_error(404), False),
        (make_http_error(409), False),
        (make_http_error(429), True),
        (make_http_error(499), False),
        (make_http_error(500), True),
        (make_http_error(503), True),
        (make_http_error(599), True),
        (make_http_error(600), False),
        (requests.HTTPError(), False),
        (requests.Timeout(), True),
        (requests.ConnectionError(), True),
        (ValueError(), False)
    ],
)
def test_is_retryable_error(error, is_retryable):
    assert http.is_retryable_error(error) == is_retryable
