# -*- coding: utf-8 -*-
from http.client import HTTPResponse
from typing import NamedTuple

from loguru import logger

from utilities.common.shared import StrPath
from utilities.common.errors import TermsInvalidProjectIdError
from utilities.common.functions import file_writer
from utilities.terms.const import CustomPort, CustomScheme
from utilities.terms.http_request import (
    CustomHTTPRequest,
    CustomHTTPResponseChunked,
    CustomPreparedRequest,
)


class ContentGitPage(NamedTuple):
    project_id: int | str = 57022544
    file_name: str = None
    path: StrPath = None
    content: list[str] = []

    def __iter__(self):
        return iter(self.content)

    def __str__(self):
        return "".join(iter(self))

    __repr__ = __str__

    def validate(self):
        if isinstance(self.project_id, str) and self.project_id.isnumeric():
            return int(self.project_id)

        elif isinstance(self.project_id, int):
            return self.project_id

        else:
            logger.error(
                f"Идентификатор проекта {self.project_id} должен быть int или str, "
                f"но получено {type(self.project_id)}"
            )
            raise TermsInvalidProjectIdError

    @property
    def _custom_http_request(self):
        scheme: str = CustomScheme.HTTPS.value
        web_hook: str = (
            f"api/v4/projects/{self.project_id}/repository/files/{self.file_name}"
        )
        host: str = "gitlab.com"
        port: int = CustomPort.HTTPS.value
        params: tuple[tuple[str, str], ...] = (("ref", "main"),)

        return CustomHTTPRequest(
            scheme=scheme, web_hook=web_hook, host=host, port=port, params=params
        )

    def set_content(self):
        logger.debug(f"URL = {self._custom_http_request.url()}")

        _prepared_request: CustomPreparedRequest
        _prepared_request = CustomPreparedRequest.from_custom_request(
            self._custom_http_request
        )

        _http_response: HTTPResponse = _prepared_request.http_response()
        _chunked: CustomHTTPResponseChunked
        _chunked = CustomHTTPResponseChunked(self.path, _http_response)

        _content: str = _chunked.decode_base64()

        if isinstance(_content, str):
            self.content.append(_content)

        else:
            self.content.extend(_content)

        logger.debug(f"Response: {self.content is not None}")

    def __len__(self):
        return len(self.content)

    def __bool__(self):
        return len(self.content) != 0

    def download(self):
        self.validate()
        self.set_content()
        file_writer(self.path, str(self))
