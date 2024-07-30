class TooManyRequests(Exception):
    """Too many requests."""


class BadCookies(Exception):
    """Login expiration."""


class GeoUrnNotFound(Exception):
    """Could not find geo urn for given location."""


class BlobException(Exception):
    """Could not find the blob needed to solve the captcha."""
