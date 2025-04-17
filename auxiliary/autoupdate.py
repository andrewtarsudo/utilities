# -*- coding: utf-8 -*-
import base64
from enum import Enum
import faulthandler
from http.client import HTTPResponse
from json import loads
from os import walk
from pathlib import Path
from sys import platform
from typing import Any, Optional
from urllib.parse import quote_plus

from httpx import get

from utilities.common.functions import get_version
from utilities.terms.const import CustomPort, CustomScheme
from utilities.terms.http_request import CustomHTTPRequest, CustomHTTPResponseChunked


def walk_files(root: str | Path, base_path: str | Path = None):
    if base_path is None:
        base_path: str | Path = root

    tree: dict = {}

    for dirpath, _, filenames in walk(root):
        folder: Path = Path(dirpath).relative_to(base_path)
        tree[folder] = [Path(filename) for filename in filenames]

    return tree

_PROTOCOL: str = "HTTPS"
_CHUNK_SIZE: int = 4096
_gitlab: dict[str, str] = {
    "win32": "docx_modify.exe",
    "darwin": "docx_modify",
    "linux": "docx_modify"}


class CustomMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

    def __str__(self):
        return f"{self.__class__.__name__}.{self.value}"

    def __repr__(self):
        return f"<{self.__class__.__name__}.{self.name}>"


class GitlabRequest(CustomHTTPRequest):
    def __init__(self, file_name: Optional[str] = None):
        if file_name is None:
            file_name: str = _gitlab[platform]

        scheme: CustomScheme = CustomScheme.HTTPS
        web_hook: str = f"/api/v4/projects/65722828/repository/files/bin%2F{file_name}"
        host: str = "gitlab.com"
        port: CustomPort = CustomPort.HTTPS
        params: tuple[tuple[str, str], ...] = (("ref", "main"),)
        super().__init__(scheme=scheme.value, web_hook=web_hook, host=host, port=port.value, params=params)
        self._file_name: str = file_name

    @property
    def url(self) -> str:
        _url: str = f"{self._get_scheme()}://{self._get_host()}{self._web_hook}{self._get_params()}"
        return quote_plus(_url, "%/:&?=")


class GitlabResponse(CustomHTTPResponseChunked):
    def __init__(
            self,
            http_response: HTTPResponse,
            path_file: Path = Path(__file__).with_name("_temp_file"),
            chunk: int = _CHUNK_SIZE):
        super().__init__(path_file, http_response, chunk=chunk)

    def _base64_content(self) -> bytes:
        return base64.b64decode(self.dict_response.get("content"))

    @property
    def file_name(self) -> Path:
        return self._path.with_name(_gitlab[platform])

    def generate_executable(self):
        with open(self.file_name, "wb") as fb:
            fb.write(self._base64_content())

    @property
    def dict_response(self) -> dict[str, Any]:
        with open(self._path, "rb") as fb:
            text: dict[str, Any] = loads(fb.read())

        return text


def main():
    gitlab_request: GitlabRequest = GitlabRequest()
    http_response: HTTPResponse = gitlab_request.http_response()
    desktop: Path = Path.home().joinpath("Desktop").joinpath("_temp_file")
    gitlab_response: GitlabResponse = GitlabResponse(http_response, desktop)
    gitlab_response.get_response()
    gitlab_response.generate_executable()
    print(f"Загружен файл {gitlab_response.file_name}")
    input("Нажмите <Enter>, чтобы закрыть окно ...")




def get_current_version():
    return get_version()



def download_file(project_id: int, file_name: str):





if __name__ == '__main__':
    faulthandler.enable()
    main()
