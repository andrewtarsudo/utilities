# -*- coding: utf-8 -*-
from base64 import b64decode
from pathlib import Path
from string import Template
from subprocess import run
from sys import platform
from typing import Any

from httpx import HTTPStatusError, request, RequestError, Response, URL
from loguru import logger

from utilities.common.functions import file_reader_type, get_version
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

    def download(self):
        file_name: Path = BASE_PATH.joinpath(f"{self._temp_dir}/{self._file_name}").expanduser()
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

    def delete(self):
        Path(self._file_name).unlink(missing_ok=True)


def compare_versions():
    current_version: str = get_version()

    git_file: GitFile = GitFile("pyproject.toml")
    pyproject_file: str = git_file.download()
    content: dict[str, Any] = file_reader_type(pyproject_file, "toml")
    latest_version: str = content.get("project").get("version")
    git_file.delete()

    return current_version == latest_version


# @cli.command(
#     "inspect-updates",
#     cls=APIGroup,
#     help="""Команда для загрузки файла с Git""",
#     hidden=True)
# @argument(
#     "filename",
#     type=STRING,
#     required=True,
#     metavar="FILE")
# @option(
#     "-p", "--project-id",
#     type=INT,
#     help="\b\nИдентификатор проекта на Git."
#          "\nПо умолчанию: 65722828",
#     multiple=False,
#     required=False,
#     metavar="PROJECT_ID",
#     default=65722828)
# @option(
#     "-t", "--temp-dir",
#     type=ClickPath(
#         file_okay=False,
#         resolve_path=True,
#         allow_dash=False,
#         dir_okay=True,
#         exists=False),
#     help="\b\nДиректория для временного хранения файлов."
#          "\nПо умолчанию: ./_temp/",
#     multiple=False,
#     required=False,
#     metavar="DIR",
#     default="_temp/")
# @pass_context


def update_exe(exe_file_name: str, project_id: int = 65722828, temp_dir: StrPath = "_temp/", ):
    executable_file: GitFile = GitFile(exe_file_name, project_id=project_id, temp_dir=temp_dir)
    return executable_file.download()


def activate_runner(executable_file: str, shell: bool, exe_file_name: str, temp_dir: StrPath = "_temp/"):
    runner: Path = BASE_PATH.joinpath("sources/runner.txt").expanduser()
    runner_exe: Path = BASE_PATH.joinpath(temp_dir).joinpath("runner.py")
    runner_exe.parent.mkdir(parents=True, exist_ok=True)
    runner_exe.touch(exist_ok=True)

    with open(runner_exe, "wb") as fw, open(runner, "r", encoding="utf-8", errors="ignore") as fr:
        template: Template = Template(fr.read())
        kwargs: dict[str, str] = {
            "old_file": f"\"{Path.cwd().joinpath("")}\"",
            "new_file": f"\"{BASE_PATH.joinpath(temp_dir).joinpath(exe_file_name)}\"",
            "shell": shell
        }
        data: str = template.safe_substitute(kwargs)
        print(data)
        fw.write(data.encode())

        logger.success(f"Файл {runner_exe} записан и готов к запуску")

    run([executable_file, runner_exe])


def update():
    if not compare_versions():
        if platform.startswith("win"):
            exe_file_name: str = "bin/tw_utilities.exe"
            python_exe: str = "python"
            shell: bool = True

        else:
            exe_file_name: str = "bin/tw_utilities"
            python_exe: str = "python3"
            shell: bool = False

        update_exe(exe_file_name)
        activate_runner(python_exe, shell)

    else:
        logger.info("OK")


if __name__ == '__main__':
    update()
