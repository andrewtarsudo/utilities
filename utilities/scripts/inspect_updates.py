# -*- coding: utf-8 -*-
from base64 import b64decode
from pathlib import Path
from string import Template
from subprocess import run
from typing import Any

from httpx import HTTPStatusError, request, RequestError, Response, URL
from loguru import logger

from utilities.common.functions import file_reader_type, get_version, is_windows, path_to_exe
from utilities.common.shared import BASE_PATH, StrPath


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

    @property
    def download_parent(self):
        return self.download_destination.parent

    @property
    def download_destination(self):
        return BASE_PATH.joinpath(f"{self._temp_dir}/{self._file_name}").expanduser()

    def download(self):
        logger.error(self.download_parent.as_posix())
        logger.error(self.download_destination.as_posix())
        self.download_parent.mkdir(parents=True, exist_ok=True)
        self.download_destination.touch(exist_ok=True)

        try:
            with open(self.download_destination, "wb") as f:
                response: Response = self.get_response().raise_for_status()
                logger.debug(f"Запрос: {response.request.method} {response.request.url}")

                for chunk in response.iter_bytes():
                    f.write(chunk)

        except HTTPStatusError as e:
            logger.error(f"Ошибка HTTP: {e.response}\n{e.response.reason_phrase}\n{e.response.status_code}")

        except RequestError as e:
            logger.error(f"Ошибка запроса: {str(e)}")

        else:
            logger.debug(f"Файл {self.download_destination.name} загружен")


def compare_versions():
    current_version: str = get_version()

    git_file: GitFile = GitFile("pyproject.toml")
    git_file.download()
    content: dict[str, Any] = file_reader_type(git_file.download_destination, "toml")
    latest_version: str = content.get("project").get("version")
    # rmtree(git_file.download_parent)

    return current_version == latest_version


def update_exe(exe_file_name: str, project_id: int = 65722828, temp_dir: StrPath = "_temp/", **kwargs):
    executable_file: GitFile = GitFile(exe_file_name, project_id=project_id, temp_dir=temp_dir, **kwargs)
    executable_file.download()


def activate_runner(executable_file: str, shell: bool, exe_file_name: str, temp_dir: StrPath = "_temp/"):
    runner: Path = BASE_PATH.joinpath("sources/runner.txt").expanduser()
    runner_exe: Path = BASE_PATH.joinpath(temp_dir).joinpath("runner.py")
    runner_exe.parent.mkdir(parents=True, exist_ok=True)
    runner_exe.touch(exist_ok=True)

    with open(runner_exe, "wb") as fw, open(runner, "r", encoding="utf-8", errors="ignore") as fr:
        template: Template = Template(fr.read())
        kwargs: dict[str, str] = {
            "old_file": f"\"{path_to_exe()}\"",
            "new_file": f"\"{BASE_PATH.joinpath(temp_dir).joinpath(exe_file_name)}\"",
            "shell": shell}

        data: str = template.safe_substitute(kwargs)
        fw.write(data.encode())

        logger.success(f"Файл {runner_exe} записан и готов к запуску")

    run([executable_file, runner_exe])


def check_updates(**kwargs):
    if not compare_versions():
        if is_windows():
            exe_file_name: str = "bin/tw_utilities.exe"
            python_exe: str = "python"
            shell: bool = True

        else:
            exe_file_name: str = "bin/tw_utilities"
            python_exe: str = "python3"
            shell: bool = False

        update_exe(exe_file_name, **kwargs)
        activate_runner(python_exe, shell, exe_file_name)

    else:
        logger.info("OK")


if __name__ == '__main__':
    check_updates()
