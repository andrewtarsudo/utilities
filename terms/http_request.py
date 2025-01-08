# -*- coding: utf-8 -*-
from base64 import b64decode
from http.client import HTTPResponse
from json import loads
from os import environ
from pathlib import Path
from typing import Any, NamedTuple
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from loguru import logger

from terms.const import CustomPort, CustomScheme
from terms.custom_exceptions import RequiredAttributeMissingError

try:
    PROTOCOL: str = environ['PROTOCOL']
    CHUNK_SIZE: int = int(environ['CHUNK_SIZE'])

except KeyError:
    PROTOCOL = "HTTPS"
    CHUNK_SIZE = 4096


class CustomHTTPRequest:
    identifier = 0

    def __init__(
            self, *,
            scheme: str | None = None,
            web_hook: str | None = None,
            host: str | None = None,
            port: int | None = None,
            params: tuple[tuple[str, str], ...] | None = None):
        if scheme is None:
            scheme: str = CustomScheme[PROTOCOL].value

        if port is None:
            port: int = CustomPort[PROTOCOL].value

        self._scheme: str = scheme
        self._web_hook: str = web_hook
        self._host: str = host
        self._port: int = port
        self._params: tuple[tuple[str, str], ...] = params
        self.index: int = self.__class__.identifier

        self.__class__.identifier += 1

    def __str__(self):
        return (
            f"{self.__class__.__name__}: "
            f"scheme = {self._scheme}, web hook = {self._web_hook}, "
            f"host = {self._host}, "
            f"post = {self._port}, "
            f"params = {self._params})")

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}"
            f"({self._scheme}, {self._web_hook}, {self._host}, {self._port},"
            f" {self._params})>")

    def __hash__(self):
        return hash(self.url())

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.url() == other.url()
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self.url() != other.url()
        else:
            return NotImplemented

    def _get_params(self) -> str:
        if self._params is None:
            return ""
        else:
            _params = "&".join([f"{name}={value}" for name, value in self._params])
            return f"?{_params}"

    def _get_web_hook(self) -> str:
        if self._web_hook is None:
            logger.error("Не указан web hook")
            raise RequiredAttributeMissingError
        else:
            return self._web_hook.rstrip("/")

    def _get_scheme(self) -> str:
        if self._scheme is None:
            return "https"
        else:
            return self._scheme.lower().strip("/")

    def _get_port(self) -> int:
        if self._port is None:
            return CustomPort[PROTOCOL].value
        else:
            return self._port

    def _get_host(self) -> str:
        if self._host is None:
            logger.error("Не указан адрес host")
            raise RequiredAttributeMissingError
        else:
            return self._host.strip("/")

    def url(self) -> str:
        _url: str = f"{self._get_scheme()}://{self._get_host()}/{self._web_hook}{self._get_params()}"
        return quote_plus(_url, ":/&?=")

    @property
    def host(self) -> str:
        return self._host


class CustomPreparedRequest(NamedTuple):
    url: str
    data: bytes
    headers: dict[str, str]
    host: str
    unverifiable: bool
    method: str
    index: int

    def __str__(self):
        return f"Connection #{self.index}:\n{str(self.request().full_url)}"

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}: "
            f"Connection #{self.index} ({self.url}, {self.data}, "
            f"{[header for header in self.headers]}, "
            f"{self.host}, {self.unverifiable}, {self.method})>")

    def __hash__(self):
        return hash((self.host, self.headers, self.data))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.request() == other.request()
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self.request() != other.request()
        else:
            return NotImplemented

    @classmethod
    def from_custom_request(
            cls,
            custom_http_request: CustomHTTPRequest, *,
            method: str = None,
            data: bytes = None,
            headers: dict[str, str] = None):
        if headers is None:
            headers = dict()

        if data is None:
            data = b''

        if method is None:
            method: str = "GET"

        return cls(
            custom_http_request.url(),
            data,
            headers,
            custom_http_request.host,
            False,
            method,
            custom_http_request.index)

    def request(self) -> Request:
        if self.headers is None:
            self.headers = dict()

        return Request(
            self.url,
            self.data,
            self.headers,
            self.host,
            self.unverifiable,
            self.method)

    def response(self) -> bytes:
        req: HTTPResponse
        with urlopen(self.request()) as req:
            _: bytes = req.read()

        return _

    def http_response(self) -> HTTPResponse:
        return urlopen(self.request())


class CustomHTTPResponse:
    def __init__(self, http_response: HTTPResponse):
        self._http_response: HTTPResponse = http_response

    def __repr__(self):
        return f"<{self.__class__.__name__}({str(self)})>"

    def __str__(self):
        return bytes(self).decode("utf-8")

    def __hash__(self):
        return hash(self._http_response)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._http_response == other._http_response
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self._http_response != other._http_response
        else:
            return NotImplemented

    def __len__(self):
        return len(self.dict_response)

    def __getitem__(self, item):
        return self.dict_response.get(item)

    def __bool__(self):
        return len(self) > 0

    def __bytes__(self):
        return self._http_response.read()

    @property
    def dict_response(self) -> dict[str, Any]:
        return loads(bytes(self))


class CustomHTTPResponseChunked:
    def __init__(
            self,
            path: str | Path,
            http_response: HTTPResponse, *,
            chunk: int = CHUNK_SIZE):
        self._path: Path = Path(path).resolve()
        self._http_response: HTTPResponse = http_response
        self._chunk: int = chunk
        self._response_dict: dict[str, Any] = dict()
        self.get_response()

    def __str__(self):
        return bytes(self).decode("utf-8")

    def decode_base64(self) -> str:
        return b64decode(self["content"]).decode("utf-8")

    def __bytes__(self):
        return self._http_response.read()

    def get_response(self):
        self._path.touch(exist_ok=True)

        with open(self._path, mode="w+b") as fb:
            while chunk := self._http_response.read(self._chunk):
                fb.write(chunk)
            fb.seek(0)
            full_response: dict[str, Any] = loads(fb.read())
            self._response_dict = full_response

        logger.debug(f"status = {self.status()}")

    def __repr__(self):
        return f"<{self.__class__.__name__}({str(self)})>"

    def __hash__(self):
        return hash(bytes(self))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._http_response == other._http_response
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self._http_response != other._http_response
        else:
            return NotImplemented

    def __getitem__(self, item):
        return self._response_dict.get(item, None)

    def status(self):
        return self._http_response.getcode()
