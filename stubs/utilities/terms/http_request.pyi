# -*- coding: utf-8 -*-
from http.client import HTTPResponse
from typing import NamedTuple
from urllib.request import Request
from utilities.common.shared import StrPath as StrPath
from utilities.common.errors import TermsRequiredAttributeMissingError as TermsRequiredAttributeMissingError
from utilities.terms.const import CustomPort as CustomPort, CustomScheme as CustomScheme

PROTOCOL: str
CHUNK_SIZE: int


class CustomHTTPRequest:
    identifier: int
    index: int

    def __init__(
            self, *,
            scheme: str | None = None,
            web_hook: str | None = None,
            host: str | None = None,
            port: int | None = None,
            params: tuple[tuple[str, str], ...] | None = None) -> None: ...

    def __hash__(self): ...

    def __eq__(self, other): ...

    def __ne__(self, other): ...

    def url(self) -> str: ...

    @property
    def host(self) -> str: ...


class CustomPreparedRequest(NamedTuple):
    url: str
    data: bytes
    headers: dict[str, str]
    host: str
    unverifiable: bool
    method: str
    index: int

    def __hash__(self): ...

    def __eq__(self, other): ...

    def __ne__(self, other): ...

    @classmethod
    def from_custom_request(
            cls,
            custom_http_request: CustomHTTPRequest, *,
            method: str = None,
            data: bytes = None,
            headers: dict[str, str] = None): ...

    def request(self) -> Request: ...

    def http_response(self) -> HTTPResponse: ...


class CustomHTTPResponseChunked:
    def __init__(self, path: StrPath, http_response: HTTPResponse, *, chunk: int = ...) -> None: ...

    def decode_base64(self) -> str: ...

    def __bytes__(self) -> bytes: ...

    def get_response(self) -> None: ...

    def __hash__(self): ...

    def __eq__(self, other): ...

    def __ne__(self, other): ...

    def __getitem__(self, item): ...

    def status(self): ...
