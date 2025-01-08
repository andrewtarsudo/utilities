# -*- coding: utf-8 -*-
from http.client import HTTPResponse
from typing import NamedTuple

from loguru import logger

from terms.const import StrPath, CustomScheme, CustomPort, _temp_terms, _temp_version, write_file
from terms.custom_exceptions import InvalidProjectIdError
from terms.http_request import CustomPreparedRequest, CustomHTTPResponseChunked, CustomHTTPRequest


def validate_positive_int(value: int) -> bool:
    return value > 0


class ContentGitPage(NamedTuple):
    project_id: int | str
    file_name: str
    path: StrPath
    content: list[str] = []

    def __iter__(self):
        return iter(self.content)

    def __str__(self):
        return "".join(iter(self))

    __repr__ = __str__

    def validate(self):
        if isinstance(self.project_id, str) and self.project_id.isnumeric():
            value: int = int(self.project_id)

        elif isinstance(self.project_id, int):
            value: int = self.project_id

        else:
            raise InvalidProjectIdError

        if value > 0:
            return

        else:
            raise InvalidProjectIdError

    @property
    def _custom_http_request(self):
        scheme: str = CustomScheme.HTTPS.value
        web_hook: str = f"api/v4/projects/{self.project_id}/repository/files/{self.file_name}"
        host: str = "gitlab.com"
        port: int = CustomPort.HTTPS.value
        params: tuple[tuple[str, str], ...] = (("ref", "main"),)

        return CustomHTTPRequest(
            scheme=scheme,
            web_hook=web_hook,
            host=host,
            port=port,
            params=params)

    def set_content(self):
        logger.debug(f"URL = {self._custom_http_request.url()}")

        _prepared_request: CustomPreparedRequest
        _prepared_request = CustomPreparedRequest.from_custom_request(self._custom_http_request)

        _http_response: HTTPResponse = _prepared_request.http_response()
        _chunked: CustomHTTPResponseChunked
        _chunked = CustomHTTPResponseChunked(self.path, _http_response)

        _content: str = _chunked.decode_base64()

        if isinstance(_content, str):
            self.content.append(_content)

        else:
            self.content.extend(_content.split("\n"))

        logger.debug(f"Response: {self.content is not None}")

    def __getitem__(self, item):
        return self.content[item]

    def __len__(self):
        return len(self.content)

    def __bool__(self):
        return len(self.content) != 0

    def download(self):
        self.validate()
        self.set_content()
        write_file(self.path, str(self))


content_git_terms: ContentGitPage = ContentGitPage(57022544, "terms.adoc", _temp_terms)
content_git_version: ContentGitPage = ContentGitPage(57022544, "__version__.txt", _temp_version)
