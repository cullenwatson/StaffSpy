from requests.exceptions import RequestException


class TooManyRequests(RequestException):
    """Too many requests."""
