# -*- coding: utf-8 -*-
from base64 import b64decode
from pathlib import Path
from typing import Any

from httpx import HTTPStatusError, request, RequestError, Response, URL
from loguru import logger

from utilities.common.functions import file_reader_type, get_version


class GitFile:
    def __init__(
            self,
            file_name: str, *,
            project_id: int = 65722828,
            scheme: str = "https",
            host: str = "gitlab.com",
            port: int = 443,
            query: bytes = b"ref_type=heads",
            method: str = "GET",
            temp_dir: str = "_temp/"):
        self._file_name: str = file_name
        self._project_id: int = project_id
        self._scheme: str = scheme
        self._host: str = host
        self._port: int = port
        self._query: bytes = query
        self._method: str = method
        self._temp_dir: str = temp_dir

    @property
    def path(self) -> str:
        url_file_name: str = self._file_name.replace(".", "%2E").replace("/", "%2F")
        return f"/api/v4/projects/{self._project_id}/repository/files/{url_file_name}/raw"

    @property
    def url(self) -> URL:
        return URL(
            scheme=self._scheme,
            host=self._host,
            path=self.path,
            query=self._query)

    def get_response(self) -> Response:
        logger.info(f"{self.url}")
        return request(method=self._method, url=self.url, timeout=120.0)

    @property
    def json(self) -> dict[str, Any]:
        return self.get_response().json()

    def __bytes__(self):
        return b64decode(self.json.get("content"))

    def __str__(self):
        return self.__bytes__().decode("utf-8")

    def __repr__(self):
        return f"<{self.__class__.__name__}>({str(self)})"

    def download_file(self):
        file_name: Path = Path(f"{self._temp_dir}/{self._file_name}").expanduser()
        file_name.parent.mkdir(parents=True, exist_ok=True)
        file_name.touch(exist_ok=True)

        try:
            with open(file_name, "wb") as f:
                response: Response = self.get_response().raise_for_status()
                logger.debug(f"Запрос: {response.request.method} {response.request.url}")

                for chunk in response.iter_bytes():
                    f.write(chunk)

        except HTTPStatusError as e:
            logger.error(f"Ошибка HTTP: {e.response}\n{e.response.reason_phrase}\n{e.response.status_code}")

        except RequestError as e:
            logger.error(f"Ошибка запроса: {str(e)}")

        else:
            logger.debug(f"Файл {file_name} скачан")
            return file_name.as_posix()


def get_latest_version() -> str:
    git_file: GitFile = GitFile("pyproject.toml")
    pyproject_file: str = git_file.download_file()

    content: dict[str, Any] = file_reader_type(pyproject_file, "toml")

    return content.get("project").get("version")


def compare_versions():
    current_version: str = get_version()
    latest_version: str = get_latest_version()

    return current_version == latest_version


def 


if __name__ == '__main__':
    print(compare_versions())
