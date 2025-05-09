# -*- coding: utf-8 -*-
from os import environ, execv
from pathlib import Path
from shutil import which
from string import Template
from subprocess import CalledProcessError, run, TimeoutExpired
import sys
from typing import Any, Iterable

from click.core import Context
from click.decorators import group, help_option, option
from click.globals import get_current_context
from click.termui import pause
from click.types import BOOL
from click.utils import echo
from loguru import logger

from utilities.common.config import config_file
from utilities.common.custom_logger import custom_logging
from utilities.common.errors import BaseError
from utilities.common.functions import file_reader, file_reader_type, file_writer, get_shell, get_version, GitFile, \
    is_macos, is_windows
from utilities.common.shared import BASE_PATH, EXE_FILE, HELP, PRESS_ENTER_KEY, StrPath
from utilities.scripts.api_group import APIGroup, get_full_help, print_version

ENV_VAR: str = config_file.get_update("env_var")
TEMP_DIR: Path = Path(config_file.get_update("temp_dir")).expanduser()
TEMP_COMMAND_FILE: Path = Path(config_file.get_update("temp_command_file")).expanduser()


def set_env(*, timeout: float | None = 15.0):
    root_dir: Path = BASE_PATH

    shell_exe: str = get_shell()

    if is_windows():
        exe: str = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
        file: str = str(root_dir.joinpath("sources/set_env.ps1").resolve().absolute())
        command: list[str] = [exe, "-File", file]
        shell: bool = True

    elif is_macos():
        file: str = str(root_dir.joinpath("sources/set_env.zsh").resolve().absolute())
        command: list[str] = [shell_exe, file]
        shell: bool = False

    else:
        file: str = str(root_dir.joinpath("sources/set_env.sh").resolve().absolute())
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


def update_exe(exe_file_name: str, project_id: int, **kwargs):
    executable_file: GitFile = GitFile(exe_file_name, project_id, **kwargs)
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

    new_file: Path = update_exe(exe_file_name, **kwargs)
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


@group(
    cls=APIGroup,
    help="Набор скриптов для технических писателей")
@option(
    "--debug",
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
    ctx: Context = get_current_context()

    try:
        ctx.ensure_object(dict)
        ctx.obj = {"debug": debug}

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
        config_var: bool = config_file.get_update("auto_update")

        if env_var is None:
            env_update: bool = True
            set_env()

        else:
            env_update: bool | None = convert_value(env_var)

        if not config_var:
            logger.debug("Автообновление отключено на уровне конфигурационного файла")

        elif env_update is None:
            logger.debug("Автообновление отключено на уровне системы")

        elif update:
            logger.debug("Автообновление отключено на уровне общей команды")

        elif not env_update:
            logger.info(
                "Автообновление отключено."
                f"\nЧтобы включить, необходимо задать переменной {ENV_VAR} значение:"
                "\n1 / \"1\" / \"True\" / true / \"yes\" / \"on\" в любом регистре.\n")

        elif compare_versions(config_file.get_update("project_id")):
            logger.info("Версия актуальна")

        else:
            args: list[str] = sys.argv[:]
            args[0]: str = str(EXE_FILE.resolve().absolute())
            args.insert(1, "--no-update")
            record_command(args)
            check_updates()
            logger.success("Исполняемый файл обновлен")

    except BaseError as e:
        logger.error(f"Ошибка {e.__class__.__name__}: {str(e)}")
        pause(PRESS_ENTER_KEY)
        ctx.exit(1)
