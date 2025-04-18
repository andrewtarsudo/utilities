# -*- coding: utf-8 -*-
from base64 import b64decode
from os import getenv
from pathlib import Path
from string import Template
from subprocess import CalledProcessError, run, TimeoutExpired
from typing import Any

from httpx import HTTPStatusError, InvalidURL, request, RequestError, Response, StreamError, URL
from loguru import logger

from utilities.common.errors import UpdateProjectIdError
from utilities.common.functions import file_reader_type, get_version, is_windows, path_to_exe
from utilities.common.shared import BASE_PATH, StrPath

POWERSHELL_EXE: str = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
ENV_VAR: str = "_TW_UTILITIES_UPDATE"
SET_ENV_PS: str = f'[Environment]::SetEnvironmentVariable("{ENV_VAR}", 1, "Machine")'


class GitFile:
    def __init__(
            self,
            file_name: str,
            project_id: int | str, *,
            scheme: str = "https",
            host: str = "gitlab.com",
            port: int = 443,
            query: bytes = b"ref_type=heads",
            method: str = "GET",
            temp_dir: str = "_temp/"):
        if not isinstance(project_id, int):
            try:
                project_id: int = int(project_id)

            except ValueError:
                logger.error(f"Идентификатор проекта должен быть int или содержать только цифры, isdecimal(), но получено {project_id}")
                raise UpdateProjectIdError

        self._file_name: str = file_name
        self._project_id: int = project_id
        self._scheme: str = scheme
        self._host: str = host
        self._port: int = port
        self._query: bytes = query
        self._method: str = method
        self._temp_dir: str = temp_dir
        self._success: bool = False

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
        logger.debug(f"{self.url}")
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
    def download_destination(self):
        return BASE_PATH.joinpath(f"{self._temp_dir}/{self._file_name}").expanduser()

    def download(self):
        self.download_destination.parent.mkdir(parents=True, exist_ok=True)
        self.download_destination.touch(exist_ok=True)

        try:
            with open(self.download_destination, "wb") as f:
                response: Response = self.get_response().raise_for_status()
                logger.debug(f"Запрос: {response.request.method} {response.request.url}")

                for chunk in response.iter_bytes():
                    f.write(chunk)

        except HTTPStatusError as e:
            logger.error(f"Ошибка HTTP, {e.__class__.__name__}: {e.response}\n{e.response.reason_phrase}\n{e.response.status_code}")

        except RequestError as e:
            logger.error(f"Ошибка запроса, {e.__class__.__name__}: {str(e)}")

        except InvalidURL as e:
            logger.error(f"Ошибка URL, {e.__class__.__name__}: {str(e)}")

        except StreamError as e:
            logger.error(f"Ошибка потока, {e.__class__.__name__}: {str(e)}")

        else:
            logger.debug(f"Файл {self.download_destination.name} загружен")
            self._success = True

    def __bool__(self):
        return self._success


def set_env(*, timeout: float | None = 15.0):
    if is_windows():
        set_env_var: list[str] = [f"{POWERSHELL_EXE}", "setx", f"{ENV_VAR}=1", "/M"]
        refresh: list[str] = [f"{POWERSHELL_EXE}", "RefreshEnv.cmd"]
        shell: bool = True

    else:
        set_env_var: list[str] = ["echo", f"{ENV_VAR}=1", ">>", "~/.bashrc"]
        refresh: list[str] = ["source", "~/.bashrc"]
        shell: bool = False

    try:
        run(set_env_var, shell=shell, capture_output=True, timeout=timeout).check_returncode()
        run(refresh, shell=shell, capture_output=True, timeout=timeout).check_returncode()

    except CalledProcessError as e:
        logger.error(
            f"Не удалось задать переменную {ENV_VAR} и обновить оболочку."
            f"\nВывод команды: {e.output}")

    except TimeoutExpired as e:
        logger.debug(
            f"Не удалось задать переменную {ENV_VAR} и обновить оболочку за время {timeout:.0f} секунд."
            f"\nВывод команды: {e.output}")
        set_env(timeout=None)

    else:
        logger.debug(f"Задана переменная {ENV_VAR} = 1")


def convert_value(value: int | str | bool):
    TRUE: tuple[str, ...] = ("1", "true", "yes", "on")
    FALSE: tuple[str, ...] = ("0", "false", "no", "off")

    if value is None:
        return True

    _value: str = str(value).lower()

    if _value in TRUE:
        return True

    elif _value in FALSE:
        return False

    else:
        logger.debug(f"Значение {value} недопустимо")
        logger.error(
            f"Переменной {ENV_VAR} можно задать одно из следующих значений:"
            f"\n{TRUE} для активации автообновления;"
            f"\n{FALSE} для отключения автообновления.")

        return True


def compare_versions(project_id: int):
    git_file: GitFile = GitFile("pyproject.toml", project_id)
    git_file.download()

    if not bool(git_file):
        logger.error(f"Не удалось подключиться к репозиторию Git, проверка обновлений завершена")
        return True

    else:
        content: dict[str, Any] = file_reader_type(git_file.download_destination, "toml")
        latest_version: str = content.get("project").get("version")

        current_version: str = get_version()

        return current_version == latest_version


def update_exe(exe_file_name: str, project_id: int, temp_dir: StrPath = "_temp/", **kwargs):
    executable_file: GitFile = GitFile(exe_file_name, project_id, temp_dir=temp_dir, **kwargs)
    executable_file.download()


def activate_runner(*, executable_file: StrPath, shell: bool, exe_file_name: str, temp_dir: StrPath = "_temp/"):
    """Generates a script from the text file to run it.

    :param executable_file: The path or name of the Python executable.
    :type executable_file: str or Path
    :param shell: The flag to run shell.
    :type shell: bool
    :param exe_file_name: The name of the executable file to replace.
    :type exe_file_name: str or Path
    :param temp_dir: The path to the temporary directory to store files.
    :type temp_dir: str or Path (default: _temp/)
    """
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

    run([str(executable_file), runner_exe])


def check_updates(**kwargs):
    env_var: Any = getenv(ENV_VAR, None)
    project_id: int = 65722828

    if env_var is None:
        is_update: bool = True

    else:
        is_update: bool = convert_value(env_var)

    if not is_update:
        logger.info(
            f"Автообновление отключено."
            f"\nЧтобы включить, необходимо задать переменной {ENV_VAR} значение:"
            f"\n1 / \"1\" / \"True\" / true / \"yes\" / \"on\" в любом регистре.")
        return

    else:
        if compare_versions(project_id):
            logger.success("Используется последняя версия")
            return

        elif is_windows():
            executable_file: str = "python"
            shell: bool = True
            exe_file_name: str = "bin/tw_utilities.exe"

        else:
            executable_file: str = "python3"
            shell: bool = False
            exe_file_name: str = "bin/tw_utilities"

        update_exe(exe_file_name, project_id,  **kwargs)
        activate_runner(executable_file=executable_file, shell=shell, exe_file_name=exe_file_name)
