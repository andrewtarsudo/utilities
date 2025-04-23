# -*- coding: utf-8 -*-
from os import chmod, getenv
from pathlib import Path
from stat import S_IXGRP, S_IXOTH, S_IXUSR
from string import Template
from subprocess import CalledProcessError, run, TimeoutExpired
import sys
from typing import Any

from click.core import Context
from loguru import logger

from utilities.common.functions import file_reader_type, get_version, GitFile, is_windows
from utilities.common.shared import BASE_PATH, StrPath

ENV_VAR: str = "_TW_UTILITIES_UPDATE"


def set_env(*, timeout: float | None = 15.0):
    if is_windows():
        POWERSHELL_EXE: str = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"

        file: str = "../../sources/set_env.ps1"
        command: list[str] = [POWERSHELL_EXE, "-File", file]
        shell: bool = True

    else:
        file: str = "../../sources/set_env.sh"
        command: list[str] = ["sh", file]
        shell: bool = False

    try:
        chmod(file, S_IXUSR | S_IXGRP | S_IXOTH)
        run(command, shell=shell, timeout=timeout).check_returncode()

    except CalledProcessError as e:
        logger.error(
            f"Не удалось задать переменную {ENV_VAR} и обновить оболочку."
            f"\nВывод команды: {e.stdout}\nВывод ошибки: {e.stderr}\nКоманда: {e.cmd}")
        raise

    except TimeoutExpired as e:
        logger.error(
            f"Не удалось задать переменную {ENV_VAR} и обновить оболочку за время {timeout:.0f} секунд."
            f"\nВывод команды: {e.output}")
        set_env(timeout=None)
        raise

    else:
        logger.debug(f"Задана переменная {ENV_VAR}")


def convert_value(value: int | str | bool):
    TRUE: tuple[str, ...] = ("1", "true", "yes", "on")
    FALSE: tuple[str, ...] = ("0", "false", "no", "off")

    if value is None:
        return True

    _value: str = str(value).lower()

    if _value == "-1":
        return None

    elif _value in TRUE:
        return True

    elif _value in FALSE:
        logger.success(f"{ENV_VAR} = {value}")
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
        logger.error("Не удалось подключиться к репозиторию Git, проверка обновлений завершена")
        return True

    else:
        content: dict[str, Any] = file_reader_type(git_file.download_destination, "toml")
        latest_version: str = content.get("project").get("version")

        current_version: str = get_version()

        return current_version == latest_version


def update_exe(ctx: Context, exe_file_name: str, project_id: int, **kwargs):
    executable_file: GitFile = GitFile(exe_file_name, project_id, temp_dir=ctx.obj.get("temp_dir"), **kwargs)
    executable_file.download()
    return executable_file.download_destination


def activate_runner(
        ctx: Context, *,
        executable_file: StrPath,
        old_file: StrPath,
        new_file: StrPath):
    """Generates a script from the text file to run it.

    :param ctx: The Click context.
    :type ctx: Context
    :param executable_file: The path or name of the Python executable.
    :type executable_file: str or Path
    :param old_file: The path to the current file.
    :type old_file: str or Path
    :param new_file: The path to the file downloaded from the git.
    :type new_file: str or Path
    """
    temp_dir: Path = Path(ctx.obj.get("temp_dir"))
    runner: Path = BASE_PATH.joinpath("sources/runner.txt").expanduser()
    runner_exe: Path = Path.home().joinpath(temp_dir).joinpath("runner.py")
    runner_exe.parent.mkdir(parents=True, exist_ok=True)
    runner_exe.touch(exist_ok=True)

    with open(runner_exe, "wb") as fw, open(runner, "r", encoding="utf-8", errors="ignore") as fr:
        template: Template = Template(fr.read())
        kwargs: dict[str, str] = {
            "old_file": f"\"{str(old_file)}\"",
            "new_file": f"\"{str(new_file)}\""}

        data: str = template.safe_substitute(kwargs)
        fw.write(data.encode())

    run([str(executable_file), runner_exe])


def check_updates(ctx: Context, **kwargs):
    env_var: Any = getenv(ENV_VAR, None)

    if env_var is None:
        is_update: bool = True
        set_env()

    else:
        is_update: bool | None = convert_value(env_var)

    if is_update is None:
        return

    if not is_update:
        logger.info(
            "Автообновление отключено."
            f"\nЧтобы включить, необходимо задать переменной {ENV_VAR} значение:"
            "\n1 / \"1\" / \"True\" / true / \"yes\" / \"on\" в любом регистре.\n")
        return

    else:
        project_id: int = 65722828

        if compare_versions(project_id):
            logger.success("Используется последняя версия")
            return

        elif is_windows():
            executable_file: str = "python"
            exe_file_name: str = "bin/tw_utilities.exe"

        else:
            executable_file: str = "python3"
            exe_file_name: str = "bin/tw_utilities"

        new_file: Path = update_exe(ctx, exe_file_name, project_id, **kwargs)
        activate_runner(ctx, executable_file=executable_file, old_file=sys.executable, new_file=new_file)
