# -*- coding: utf-8 -*-
from base64 import b64decode
from typing import Any, NamedTuple

from httpx import get, HTTPStatusError, RequestError, Response, stream, URL
from loguru import logger


class GitFile(NamedTuple):
    project_id: int = 65722828
    file_name: str = "bin/{file_name}"
    scheme: str = "https"
    host: str = "gitlab.com"
    port: int = 443
    query: bytes = b"raw=main"
    method: str = "GET"

    @property
    def path(self):
        return f"api/v4/projects/{self.project_id}/repository/files/{self.file_name}"

    @property
    def url(self):
        return URL(
            scheme=self.scheme,
            host=self.host,
            path=self.path,
            query=self.query)

    def send_get_request(self):
        return get(self.url, verify=True, timeout=60.0)

    def get_string_content(self):
        return self.get_bytes_content().decode("utf-8")

    def get_bytes_content(self):
        response: Response = self.send_get_request()
        json: dict[str, Any] = response.json()
        content: bytes = json.get("content")

        return b64decode(content)

    def download_file(self, name: str):
        try:
            with stream(self.method, self.url, timeout=60.0) as response, open(name, "wb") as f:
                logger.info(f"Запрос: {response.request.method} {response.request.url}")
                response.raise_for_status()
                for chunk in response.iter_bytes():
                    f.write(chunk)

        except HTTPStatusError as e:
            print(f"Ошибка HTTP: {e.response}")

        except RequestError as e:
            print(f"Request error occurred: {e}")

        logger.info(f"Файл {self.file_name} скачан")
