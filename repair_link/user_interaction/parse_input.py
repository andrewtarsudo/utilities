# -*- coding: utf-8 -*-
from argparse import ArgumentParser, RawDescriptionHelpFormatter, SUPPRESS, Namespace, ArgumentError, OPTIONAL
from locale import getlocale
from sys import platform

from loguru import logger

from repair_link.general.const import prog, version
from repair_link.general.custom_logger import configure_custom_logging
from repair_link.user_interaction.const import InputUser, PRESS_ENTER_KEY

_python: str = "python3" if not platform.startswith("win") else "py"
usage: str = (
    f"{prog} \n"
    f"[ -h/--help | -v/--version ] [-a/--anchor-disable ] [ -d/--dry-run ] [ -l/--keep-log ] [ -n/--no-result] "
    f"[-s/--separate ] PATHDIR ")

if getlocale()[0] == "en_US":
    _note_pwd: str = "Using 'pwd' for current directory and marks '.' and '..' is allowed"
    description: str = "Script to fix the links in the markdown files from the specified directory"
    _help_pathdir: str = (
        "str | Path. Specify the folder to process all *.md files inside.\n"
        f"{_note_pwd}")
    _help_dry_run: str = (
        "Flag. Specify only to show invalid links in files without replacing them.\n"
        "Default is False, updating files is enabled. If missing, the default value is implemented")
    _help_keep_log: str = (
        "Flag. Specify to keep the directory with the log file after the program finishes its work.\n"
        "Default is False, log file and folder are deleted. If missing, the default value is implemented")
    _help_no_result: str = (
        "Flag. Specify to keep the file with all information after the program finishes its work.\n"
        "Default is True, result file is stored. If missing, the default value is implemented")
    _help_separate: str = (
        "Flag. Specify to process the files according to their languages without mixing up.\n"
        "Default is True, the files in Russian and English are handled separately. "
        "If missing, the default value is implemented")
    _help_skip_en: str = (
        "Flag. Specify to process only files in Russian.\n"
        "Default is False, all files are handled. "
        "If missing, the default value is implemented"
    )
    _help_anchor_inspection: str = (
        "Flag. Specify to activate anchor inspection.\n"
        "Default is True, the anchors are validated. If missing, the default value is implemented")
    _help_version: str = (
        "Show the script version with the full information message and close the window")
    _help_help: str = "Show the help message and close the window"

else:
    _note_pwd: str = "Допускается использование 'pwd' для текущей директории и пути '.' и '..'"
    description: str = "Скрипт для исправления ссылок в Markdown-файлах в заданной директории"
    _help_pathdir: str = (
        "Строка. Директория, в которой будут обрабатываться все *.md файлы.\n"
        f"{_note_pwd}")
    _help_dry_run: str = (
        "Флаг. Индикатор вывода некорректных ссылок на экран без изменения файлов.\n"
        "По умолчанию: False, файлы перезаписываются. При отсутствии используется значение по умолчанию")
    _help_keep_log: str = (
        "Флаг. Индикатор сохранения директории с лог-файлом по завершении работы скрипта в штатном режиме.\n"
        "По умолчанию: False, лог-файл и директория удаляются. При отсутствии используется значение по умолчанию")
    _help_no_result: str = (
        "Флаг. Индикатор удаления файла с результатами работы скрипта по завершении работы скрипта в штатном режиме.\n"
        "По умолчанию: False, файл сохраняется. При отсутствии используется значение по умолчанию")
    _help_separate: str = (
        "Флаг. Индикатор раздельной обработки файлов на различных языках.\n"
        "По умолчанию: True, файлы на русском и английском обрабатываются отдельно. "
        "При отсутствии используется значение по умолчанию")
    _help_skip_en: str = (
        "Флаг. Индикатор обработки файлов только на русском языке.\n"
        "По умолчанию: False, обрабатываются файлы и на русском, и на английском. "
        "При отсутствии используется значение по умолчанию"
    )
    _help_anchor_inspection: str = (
        "Флаг. Индикатор поиска повторяющихся якорей.\n"
        "По умолчанию: True, поиск дублирующихся якорей осуществляется. "
        "При отсутствии используется значение по умолчанию")
    _help_version: str = "Вывести версию скрипта на экран и завершить работу"
    _help_help: str = "Вывести справочную информацию на экран и завершить работу"


@logger.catch
@configure_custom_logging("link_repair")
def parse_command_line() -> InputUser | None:
    """
    The generation of the user input parser.

    Returns
    -------
    InputUser
        The user input transformed to the comfortable instance.

    """
    parser: ArgumentParser = ArgumentParser(
        prog=prog,
        usage=usage,
        description=description,
        formatter_class=RawDescriptionHelpFormatter,
        add_help=False,
        allow_abbrev=False,
        exit_on_error=False)

    parser.add_argument(
        "pathdir",
        action='store',
        help=_help_pathdir,
        nargs=OPTIONAL,
        default=None
    )

    parser.add_argument(
        "-d", "--dry-run",
        action="store_true",
        default=SUPPRESS,
        required=False,
        help=_help_dry_run,
        dest="dry_run"
    )

    parser.add_argument(
        "-l", "--keep-log",
        action="store_true",
        default=SUPPRESS,
        required=False,
        help=_help_keep_log,
        dest="keep_log"
    )

    parser.add_argument(
        "-n", "--no-result",
        action="store_false",
        default=SUPPRESS,
        required=False,
        help=_help_no_result,
        dest="no_result"
    )

    parser.add_argument(
        "-a", "--anchor-disable",
        action="store_false",
        default=SUPPRESS,
        required=False,
        help=_help_anchor_inspection,
        dest="anchor_validation"
    )

    parser.add_argument(
        "-s", "--separate",
        action="store_false",
        default=SUPPRESS,
        required=False,
        help=_help_separate,
        dest="separate"
    )

    parser.add_argument(
        "--skip-en",
        action="store_true",
        default=SUPPRESS,
        required=False,
        help=_help_skip_en,
        dest="skip_en"
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=version,
        help=_help_version
    )

    parser.add_argument(
        "-h", "--help",
        action="help",
        default=SUPPRESS,
        help=_help_help
    )

    try:
        args: Namespace = parser.parse_args()

        if hasattr(args, "help") or hasattr(args, "version"):
            input(PRESS_ENTER_KEY)
            return

        else:
            _root_dir: str = getattr(args, "pathdir", None)
            _dry_run: bool = getattr(args, "dry_run", False)
            _keep_log: bool = getattr(args, "keep_log", False)
            _no_result: bool = getattr(args, "no_result", True)
            _anchor_validation: bool = getattr(args, "anchor_validation", True)
            _separate: bool = getattr(args, "separate", True)
            _skip_en: bool = getattr(args, "skip_en", True)

            input_user: InputUser = InputUser(
                _root_dir,
                _dry_run,
                _keep_log,
                _no_result,
                _anchor_validation,
                _separate,
                _skip_en)
            logger.error(f"input_user = {input_user}")

            return input_user

    except ArgumentError as exc:
        logger.critical(f"{exc.__class__.__name__}, {exc.argument_name}\n{exc.message}")
        input(PRESS_ENTER_KEY)
        exit(-1)

    except KeyboardInterrupt:
        logger.critical("Работа программы прекращена")
        exit(-2)
