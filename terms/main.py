# -*- coding: utf-8 -*-
import os.path as p
from os import environ, rmdir, listdir, unlink
from textwrap import dedent

from loguru import logger

from terms.ascii_doc_table_terms import AsciiDocTableTerms
from terms.const import _log_folder, _temp_version, _temp_terms, State
from terms.git_manager import GitManager
from terms.init_logger import configure_custom_logging
from terms.user_input import UserInputParser

_spec: str = dedent(
    """\
    Для вывода информации о списке необходимо ввести любой из ниже предложенных вариантов:
    -a/--all -- отобразить все термины и сокращения на английском;
    -f/--full -- отобразить все термины и сокращения, а также их полные расшифровки и комментарии к ним;
    """)

_disclaimer: str = dedent(
    f"""\
    В случае ошибки необходимо сохранить лог-файл, который будет находиться здесь:
    '{_log_folder}'

    https://gitlab.com/tech_writers_protei/terms/-/tree/main

    Утилита для получения полного наименования сокращения и его описания.
    Используется таблица, хранящаяся в репозитории Gitlab:

    https://gitlab.com/tech_writers_protei/glossary/-/blob/main/terms.adoc

    Искомые термины и аббревиатуры можно вводить как по одному, так и несколько.
    При вводе нескольких необходимо разделить любым не циферным и не буквенным символом, кроме '_' и '-'.
    """)

_help: str = dedent(
    """\
    Для вывода краткой справочной информации необходимо ввести любой из ниже предложенных вариантов:
    -h/--help
    Для вывода полной справочной информации необходимо ввести любой из ниже предложенных вариантов:
    -r/--readme
    Для вывода примеров использования необходимо ввести любой из ниже предложенных вариантов:
    -s/--samples
    """)

_exit: str = dedent(
    """\
    Для выхода необходимо ввести любой из ниже предложенных вариантов:
    __exit__, exit, __quit__, quit, !e, !exit, !q, !quit
    """)


def _delete_log_dir():
    try:
        return rmdir(_log_folder)

    except (FileNotFoundError, NotADirectoryError):
        print(f"Директория {_log_folder} уже удалена")

    except PermissionError:
        print(f"Недостаточно прав для удаления директории {_log_folder}")

    except (OSError, RuntimeError) as e:
        print(
            f"Возникла внутренняя ошибка {e.__class__.__name__} "
            f"при удалении директории {_log_folder}")


def _delete_logs():
    env_variable: str = "KEEP_TERMS_LOGS"

    if env_variable in environ.keys() and bool(environ.get(env_variable)):
        return

    if not listdir(_log_folder):
        return

    try:
        for file in listdir(_log_folder):
            unlink(p.join(_log_folder, file))

    except (FileNotFoundError, NotADirectoryError, IsADirectoryError) as e:
        print(f"Директория {_log_folder} уже пуста. {e.__class__.__name__}")

    except PermissionError:
        print(f"Недостаточно прав для удаления файлов из директории {_log_folder}")

    except (OSError, RuntimeError) as e:
        print(
            f"Возникла внутренняя ошибка {e.__class__.__name__} при удалении файлов из директории {_log_folder}")


def _delete_temp_files():
    try:
        unlink(_temp_terms)
        unlink(_temp_version)

    except (FileNotFoundError, IsADirectoryError) as e:
        print(f"{_temp_terms} и {_temp_version} уже удалены. {e.__class__.__name__}")

    except PermissionError:
        print(f"Недостаточно прав для удаления файлов {_temp_terms} и {_temp_version}")

    except (OSError, RuntimeError) as e:
        print(f"Возникла внутренняя ошибка {e.__class__.__name__} при удалении файлов {_temp_terms} и {_temp_version}")


@logger.catch
@configure_custom_logging("terms", True)
def run_script():
    git_manager: GitManager = GitManager()
    git_manager.compare()
    git_manager.set_terms()

    lines: list[str] = git_manager.lines

    ascii_doc_table: AsciiDocTableTerms = AsciiDocTableTerms(lines)
    ascii_doc_table.complete()
    ascii_doc_table.set_terms()

    user_input_parser: UserInputParser = UserInputParser(ascii_doc_table)
    prompt: str = (
        "Введите сокращение или несколько сокращений, "
        "чтобы получить полное наименование и описание:\n")

    logger.success(_disclaimer)
    logger.success(_spec)
    logger.success(_help)
    logger.success(_exit)

    while user_input_parser.state != State.STOPPED:
        print(prompt)
        user_input: str = input()
        user_input_parser.handle_input(user_input)

    input("Нажмите любую клавишу, чтобы закрыть окно ...")
    logger.stop()
    _delete_logs()
    _delete_log_dir()
    _delete_temp_files()



