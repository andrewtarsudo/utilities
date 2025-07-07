# -*- coding: utf-8 -*-
from os import environ, execv
from pathlib import Path
from shutil import which
from string import Template
from subprocess import run
import sys
from typing import Any, Iterable

from click.core import Context
from click.decorators import group, help_option, option
from click.globals import get_current_context
from click.termui import pause
from click.types import BOOL
from click.utils import echo
from loguru import logger

from utilities.common.config_file import config_file
from utilities.common.custom_logger import add_handler, custom_logging
from utilities.common.errors import BaseError
from utilities.common.functions import file_reader, file_reader_type, file_writer, get_version, GitFile, \
    is_windows
from utilities.common.shared import BASE_PATH, EXE_FILE, HELP, PRESS_ENTER_KEY, ScriptVersion, StrPath
from utilities.scripts.api_group import APIGroup, get_full_help, print_version
from utilities.scripts.args_help_dict import args_help_dict

ENV_VAR: str = config_file.get_update("env_var")
TEMP_DIR: Path = Path(config_file.get_update("temp_dir")).expanduser()
TEMP_COMMAND_FILE: Path = Path(config_file.get_update("temp_command_file")).expanduser()


def check_env() -> bool:
    """Checks the environment variable _TW_UTILITIES_UPDATE."""
    FALSE: tuple[str, ...] = ("0", "false", "no", "off")
    env_var: str | None = environ.get("_TW_UTILITIES_UPDATE", None)

    if env_var is None:
        return True

    env_var: str = env_var.lower()

    if env_var in FALSE:
        return False

    else:
        return True


def check_file() -> bool:
    """Checks if the specified file exists. """
    if is_windows():
        local_file: Path = Path(environ.get("LOCALAPPDATA")).joinpath("_tw_utilities_update")

    else:
        local_file: Path = Path(environ.get("HOME")).joinpath("local/_tw_utilities_update")

    statuses: dict[bool, str] = {
        True: "найден",
        False: "не найден"}

    update: bool = local_file.exists()

    logger.debug(f"Файл {local_file} {statuses.get(update)}")
    return not update


def check_config_file() -> bool:
    """Checks the value in the configuration file."""
    return config_file.get_update("auto_update")


def compare_versions(project_id: int):
    git_file: GitFile = GitFile("pyproject.toml", project_id)
    git_file.download()

    if not bool(git_file):
        logger.error("Не удалось подключиться к репозиторию Git, проверка обновлений завершена")
        return True

    else:
        content: dict[str, Any] = file_reader_type(git_file.download_destination, "toml")
        latest: str = content.get("project").get("version")
        latest_version: ScriptVersion = ScriptVersion.from_string(latest)
        logger.debug(f"Последняя версия: {latest_version!s}")

        current: str = get_version()
        current_version: ScriptVersion = ScriptVersion.from_string(current)
        logger.debug(f"Текущая версия: {current_version}")

        return current_version >= latest_version


def update_exe(exe_file_name: str, project_id: int, **kwargs):
    executable_file: GitFile = GitFile(exe_file_name, project_id, **kwargs)
    echo("Обновление исполняемого файла...")
    executable_file.download()

    return executable_file.download_destination


# noinspection SpawnShellInjection
def activate_runner(
        *,
        old_file: StrPath,
        new_file: StrPath):
    """Generates a script from the text file to run it.

    :param old_file: The path to the current file.
    :type old_file: str or Path
    :param new_file: The path to the file downloaded from the git.
    :type new_file: str or Path
    """
    runner: Path = BASE_PATH.joinpath("sources/runner.txt").expanduser()
    runner_exe: Path = TEMP_DIR.joinpath("runner.py")
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    runner_exe.touch(exist_ok=True)

    with open(runner_exe, "wb") as fw, open(runner, "r", encoding="utf-8", errors="ignore") as fr:
        template: Template = Template(fr.read())

        kwargs: dict[str, str | list[str]] = {
            "old_file": f"\"{str(old_file)}\"",
            "new_file": f"\"{str(new_file)}\"",
            "args": f"{get_command()}"}

        data: str = template.safe_substitute(kwargs)
        fw.write(data.encode())

    runner_exe.chmod(0o775, follow_symlinks=True)
    return runner_exe


# noinspection SpawnShellInjection
def check_updates(**kwargs):
    if is_windows():
        exe_file_name: str = "bin/tw_utilities.exe"
        executable: str = "python"

    else:
        exe_file_name: str = "bin/tw_utilities"
        executable: str = "python3"

    new_file: Path = update_exe(exe_file_name, config_file.get_update("project_id"), **kwargs)
    runner_exe: Path = activate_runner(old_file=EXE_FILE, new_file=new_file)

    python: str = which(executable)

    execv(python, [python, runner_exe])


def record_command(args: Iterable[str]):
    TEMP_COMMAND_FILE.touch(exist_ok=True)
    line: str = " ".join(args)
    file_writer(TEMP_COMMAND_FILE, line)


def get_command() -> list[str]:
    command: str = file_reader(TEMP_COMMAND_FILE, "string")
    args: list[str] = command.split()
    args[0] = str(Path(args[0]).resolve().absolute())
    return args


def run_command(args):
    run(args, capture_output=True, shell=is_windows())


# noinspection PyTypeChecker
@group(
    cls=APIGroup,
    help="Набор скриптов для технических писателей")
@option(
    "--debug", "debug",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг активации режима отладки."
         "\nПо умолчанию: False, режим отключен",
    show_default=True,
    required=False,
    default=False,
    hidden=False)
@option(
    "-u/-U", "--update/--no-update", "update",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг автообновления перед выполнением команды."
         "\nПо умолчанию: True, автообновление активно",
    show_default=True,
    required=False,
    default=True,
    hidden=False)
@option(
    "--version",
    is_flag=True,
    expose_value=False,
    is_eager=True,
    help="Вывести версию скрипта на экран и завершить работу",
    callback=print_version)
@help_option(
    "-h", "--help",
    help=HELP,
    is_eager=True)
def cli(debug: bool = False, update: bool = True):
    custom_logging(is_debug=debug)

    try:
        ctx: Context = get_current_context()
        ctx.ensure_object(dict)
        ctx.obj = {"debug": debug}

        if ctx.invoked_subcommand is None:
            echo("Не указана ни одна из доступных команд. Для вызова справки используется опция -h / --help")
            pause(PRESS_ENTER_KEY)
            ctx.exit(0)

        elif ctx.invoked_subcommand == "help":
            ctx.obj["full_help"] = True
            text: str = ctx.invoke(get_full_help, cmd=ctx.command, ctx=ctx)
            echo(text)
            ctx.exit(0)

        elif ctx.invoked_subcommand == "repair-links":
            add_handler("result_file")

        logger.debug(str(config_file))
        logger.debug(f"Файл описания аргументов:\n{str(args_help_dict)}")

        checked_file: bool = check_file()
        checked_env: bool = check_env()
        checked_config_file: bool = check_config_file()
        checked_command: bool = update

        if any(value is False for value in (checked_file, checked_env, checked_config_file, checked_command)):
            logger.info("Автообновление отключено")

        elif compare_versions(config_file.get_update("project_id")):
            logger.info("Версия актуальна")

        else:
            args: list[str] = sys.argv[:]
            args[0]: str = str(EXE_FILE.resolve().absolute())
            args.insert(1, "--no-update")
            record_command(args)
            check_updates()

            run_command(args)
            logger.success("Исполняемый файл обновлен")

    except BaseError as e:
        logger.error(f"Ошибка {e.__class__.__name__}")
        pause(PRESS_ENTER_KEY)
        sys.exit(1)
