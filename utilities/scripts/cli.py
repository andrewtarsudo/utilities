# -*- coding: utf-8 -*-
from os import environ, execv
from pathlib import Path
from shutil import which
from string import Template
from subprocess import CalledProcessError, run, TimeoutExpired
import sys
from typing import Any

from click.core import Context
from click.decorators import group, help_option, option
from click.globals import get_current_context
from click.termui import pause
from click.types import BOOL
from click.utils import echo
from loguru import logger

from utilities.common.custom_logger import custom_logging
from utilities.common.errors import BaseError
from utilities.common.functions import file_reader_type, get_shell, get_version, GitFile, is_macos, is_windows
from utilities.common.shared import BASE_PATH, ENV_VAR, HELP, PRESS_ENTER_KEY, StrPath
from utilities.scripts.api_group import APIGroup, get_full_help, print_version


def set_env(*, timeout: float | None = 15.0):
    root_dir: Path = Path(getattr(sys, "_MEIPASS"))

    shell_exe: str = get_shell()

    if is_windows():
        exe: str = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
        file: str = root_dir.joinpath("sources/set_env.ps1").resolve().as_posix()
        command: list[str] = [exe, "-File", file]
        shell: bool = True

    elif is_macos():
        file: str = root_dir.joinpath("sources/set_env.zsh").as_posix()
        command: list[str] = [shell_exe, file]
        shell: bool = False

    else:
        file: str = root_dir.joinpath("sources/set_env.sh").as_posix()
        command: list[str] = [shell_exe, file]
        shell: bool = False

    try:
        Path(file).chmod(0o775)
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


def compare_versions(project_id: int = 65722828):
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


def update_exe(exe_file_name: str, project_id: int = 65722828, **kwargs):
    executable_file: GitFile = GitFile(exe_file_name, project_id, **kwargs)
    executable_file.download()

    return executable_file.download_destination


# noinspection SpawnShellInjection
def activate_runner(
        ctx: Context, *,
        old_file: StrPath,
        new_file: StrPath):
    """Generates a script from the text file to run it.

    :param ctx: The Click context.
    :type ctx: Context
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
            "new_file": f"\"{str(new_file)}\"",
            "args": ctx.obj.get("args")}

        data: str = template.safe_substitute(kwargs)
        fw.write(data.encode())

    runner_exe.chmod(0o775, follow_symlinks=True)
    return runner_exe


def check_updates(ctx: Context, **kwargs):
    if is_windows():
        exe_file_name: str = "bin/tw_utilities.exe"

    else:
        exe_file_name: str = "bin/tw_utilities"

    new_file: Path = update_exe(exe_file_name, **kwargs)
    runner_exe: Path = activate_runner(ctx, old_file=sys.executable, new_file=new_file)

    if is_windows():
        executable: str = "python"

    else:
        executable: str = "python3"

    # noinspection SpawnShellInjection
    execv(which(executable), [which(executable), runner_exe])


@group(
    cls=APIGroup,
    help="Набор скриптов для технических писателей")
@option(
    "--version",
    is_flag=True,
    expose_value=False,
    is_eager=True,
    help="Вывести версию скрипта на экран и завершить работу",
    callback=print_version)
@option(
    "--debug",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг активации режима отладки."
         "\nПо умолчанию: False, режим отключен",
    show_default=True,
    required=False,
    default=False,
    hidden=True)
@help_option(
    "-h", "--help",
    help=HELP,
    is_eager=True)
def cli(debug: bool = False):
    ctx: Context = get_current_context()

    try:
        ctx.ensure_object(dict)
        ctx.obj = {"debug": debug, "temp_dir": "_temp/", "args": sys.argv}

        result_file: bool = False

        if ctx.invoked_subcommand is None:
            echo("Не указана ни одна из доступных команд. Для вызова справки используется опция -h / --help")
            pause(PRESS_ENTER_KEY)
            ctx.exit(0)

        elif ctx.invoked_subcommand == "help":
            ctx.obj["full_help"] = True
            text: str = ctx.invoke(get_full_help, cmd=ctx.command, ctx=ctx)
            echo(text)
            ctx.exit(0)

        elif ctx.invoked_subcommand == "link-repair":
            result_file: bool = True

        custom_logging("cli", is_debug=debug, result_file=result_file)

        env_var: Any = environ.get(ENV_VAR)

        if env_var is None:
            is_update: bool = True
            set_env()

        else:
            is_update: bool | None = convert_value(env_var)

        if is_update is None or not is_update:
            logger.info(
                "Автообновление отключено."
                f"\nЧтобы включить, необходимо задать переменной {ENV_VAR} значение:"
                "\n1 / \"1\" / \"True\" / true / \"yes\" / \"on\" в любом регистре.\n")
            return True

        if not compare_versions():
            check_updates(ctx)
            logger.success("Исполняемый файл обновлен")
            pause("Введите команду повторно")
            ctx.exit(0)

    except BaseError as e:
        logger.error(f"Ошибка {e.__class__.__name__}")
        pause(PRESS_ENTER_KEY)
        ctx.exit(1)
