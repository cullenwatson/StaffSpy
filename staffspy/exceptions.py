from requests.exceptions import RequestException


class TooManyRequests(RequestException):
    """Too many requests."""


class BadCookies(RequestException):
    """Login expiration."""


class GeoUrnNotFound(RequestException):
    """Could not find geo urn for given location."""
