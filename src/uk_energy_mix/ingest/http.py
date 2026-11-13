import requests


def is_retryable_error(exception: BaseException) -> bool:
    """Retry on Timeout, Connection Error, 429 or server-side HTTP Error (5xx)"""
    if isinstance(exception, (requests.Timeout, requests.ConnectionError)):
        return True
    if not isinstance(exception, requests.HTTPError):
        return False
    if exception.response is None:
        return False
    status_code = exception.response.status_code
    return status_code == 429 or status_code in range(500, 600)
