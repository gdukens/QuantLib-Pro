"""
QuantLib Pro SDK — Base Resource
"""


class BaseResource:
    """Base class for all API resources."""

    PREFIX = ""

    def __init__(self, http):
        self._http = http

    def _url(self, path: str) -> str:
        return f"{self.PREFIX}{path}"
