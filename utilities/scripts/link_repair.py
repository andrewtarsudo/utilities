# -*- coding: utf-8 -*-
from glob import iglob
from os.path import relpath
from pathlib import Path

from click.core import Context
from click.exceptions import Exit
from loguru import logger
from rich import print
from rich.prompt import Prompt
from typer.main import Typer
from typer.params import Argument, Option
from typing_extensions import Annotated

from utilities.common.constants import ADOC_EXTENSION, MD_EXTENSION, PRESS_ENTER_KEY, StrPath
from utilities.common.errors import LinkRepairInvalidFileDictAttributeError, LinkRepairInvalidStorageAttributeError
from utilities.common.functions import clear_logs, file_reader, file_writer, ReaderMode
from utilities.link_repair.const import FileLanguage, prepare_logging
from utilities.link_repair.file_dict import FileDict, FileLinkItem, TextFile
from utilities.link_repair.general_storage import Storage
from utilities.link_repair.internal_link_inspector import internal_inspector
from utilities.link_repair.link import Link
from utilities.link_repair.link_fixer import link_fixer
from utilities.link_repair.link_inspector import link_inspector
from utilities.scripts.main_group import MainGroup

link_repair: Typer = Typer(
    cls=MainGroup,
    add_help_option=True,
    rich_markup_mode="rich",
    help="Команда для проверки и исправления ссылок в файлах документации")


def validate_dir_path(path: StrPath | None) -> bool:
    if path is None:
        return False

    _: Path = Path(path).resolve()

    if not _.exists():
        logger.debug(f"Директория {path} не найдена")
        return False

    elif not _.is_dir():
        logger.debug(f"Путь {path} указывает не на директорию")
        return False

    return True


def has_no_required_files(path: StrPath) -> bool:
    bool_md: bool = next(iglob(f"**/*{MD_EXTENSION}", root_dir=path, recursive=True), None) is None
    bool_adoc: bool = next(iglob(f"**/*{ADOC_EXTENSION}", root_dir=path, recursive=True), None) is None
    return bool_md and bool_adoc


@link_repair.command(
    add_help_option=False,
    name="link-repair",
    help="Команда для проверки и исправления ссылок в файлах документации")
def link_repair_command(
        ctx: Context,
        pathdir: Annotated[
            Path, Argument(
                metavar="PATHDIR",
                file_okay=False,
                dir_okay=True,
                exists=True,
                allow_dash=False,
                resolve_path=True,
                help="Путь до директории для обработки *.md- и *.adoc-файлов")],
        dry_run: Annotated[
            bool,
            Option(
                "-d/-D", "--dry-run/--no-dry-run",
                show_default=True,
                help="Флаг вывода некорректных ссылок на экран без изменения"
                     "\nфайлов."
                     "\nПо умолчанию: False, файлы перезаписываются")] = False,
        no_result: Annotated[
            bool,
            Option(
                "-n", "--no-result",
                show_default=True,
                help="\b\nФлаг удаления файла с результатами работы скрипта по"
                     "\nзавершении работы в штатном режиме.\n"
                     "По умолчанию: False, файл сохраняется")] = False,
        anchor_validation: Annotated[
            bool,
            Option(
                "-a", "--anchor-disable",
                show_default=True,
                help="Флаг поиска повторяющихся якорей.\n"
                     "По умолчанию: True, дублирующийся якори обрабатываются")] = True,
        separate_languages: Annotated[
            bool,
            Option(
                "-s", "--separate",
                show_default=True,
                help="\b\nФлаг раздельной обработки файлов на различных языках.\n"
                     "По умолчанию: True, файлы обрабатываются отдельно")] = True,
        skip_en: Annotated[
            bool,
            Option(
                "--skip-en",
                show_default=True,
                help="\b\nФлаг обработки файлов только на русском языке."
                     "\nПо умолчанию: False, обрабатываются файлы на обоих"
                     "\nязыках")] = False,
        keep_logs: Annotated[
            bool,
            Option(
                "--keep-logs",
                show_default=True,
                help="Флаг сохранения директории с лог-файлом по завершении\nработы в штатном режиме."
                     "\nПо умолчанию: False, лог-файл и директория удаляются")] = False,
        help_option: Annotated[
            bool,
            Option(
                "-h", "--help",
                show_default=False,
                help="Показать справку и закрыть окно",
                is_eager=True)] = False):
    result_file_path: Path = Path.cwd().joinpath("results.txt")

    if not validate_dir_path(pathdir):
        logger.error(f"Путь {pathdir} не существует или указывает не на директорию")
        Prompt.ask(PRESS_ENTER_KEY)
        raise Exit(0)

    if has_no_required_files(pathdir):
        logger.warning(
            f"В директории {pathdir} не найдены файлы с расширением {MD_EXTENSION}, {ADOC_EXTENSION}")
        Prompt.ask(PRESS_ENTER_KEY)
        raise Exit(0)

    _base_dir: Path = Path(pathdir).parent.parent.resolve()

    # operate with Storage
    storage: Storage = Storage(pathdir)
    storage.prepare()

    if storage is None:
        logger.error("Объект типа Storage не определен")
        raise LinkRepairInvalidStorageAttributeError

    logger.debug(prepare_logging(storage.dir_indexes.items()))
    logger.debug(prepare_logging(storage.dirindexes.items()))
    logger.debug(prepare_logging(storage.text_files.items()))
    logger.debug(prepare_logging(storage.non_text_files.items()))

    # operate with FileDict
    file_dict: FileDict = FileDict(pathdir)
    file_dict + iter(storage)

    if file_dict is None:
        logger.error("Объект типа FileDict не определен")
        raise LinkRepairInvalidFileDictAttributeError

    logger.debug(prepare_logging(file_dict.dict_files.items()))

    if anchor_validation:
        from utilities.link_repair.anchor_inspector import anchor_inspector

        # operate with AnchorInspector
        anchor_inspector + iter(file_dict.dict_files.values())

        if separate_languages:
            languages: list[FileLanguage] = [FileLanguage.RU, FileLanguage.EN]

        elif skip_en:
            languages: list[FileLanguage] = [FileLanguage.RU]

        else:
            languages: list[FileLanguage] = [FileLanguage.RU_EN]

        for language in languages:
            anchor_inspector.inspect_inside_file(language)
            anchor_inspector.inspect_all_files(language)

        for file, anchors in anchor_inspector.dict_changes.items():
            for anchor in anchors:
                line_number: list[int] = file.find_anchor(anchor)
                addition: str = (
                    file.full_path.stem
                    .lower()
                    .removeprefix('_')
                    .replace('_', '-')
                    .replace('.', '-'))
                file.update_line(line_number, anchor, f"{anchor}-{addition}", is_boundary=True)

    else:
        logger.info("Проверка дублирования якорей отключена пользователем", result=True)

    # operate with LinkInspector
    link_inspector.storage = storage
    link_inspector.file_dict = file_dict

    dir_file: TextFile
    for dir_file in iter(file_dict):
        # validate links
        link_fixer.text_file = dir_file
        link_fixer.fix_links()

        if not dry_run:
            file_writer(dir_file.full_path, dir_file.content, encoding="utf-8")

        dir_file._content = file_reader(dir_file.full_path, ReaderMode.LINES, encoding="utf-8")

        # validate internal links
        internal_inspector.text_file = dir_file
        internal_inspector.inspect_links()

        link_item: FileLinkItem
        for link_item in dir_file.iter_links():
            index: int
            link: Link
            index, link = link_item.index, link_item.link

            # nullify values
            link_inspector.clear()

            # specify values
            link_inspector.link = link
            link_inspector.preprocess_link()

            # validate link or search for file
            link_inspector.inspect_original_link()
            link_inspector.inspect_trivial_options()
            link_inspector.find_file()

            # if not found
            if not bool(link_inspector):
                _file_path: str = relpath(link_inspector.link.from_file, _base_dir).replace('\\', '/')
                logger.error(
                    f"Не удалось обработать ссылку в файле.\n"
                    f"Ссылка: {link_inspector.link.link_to}\n"
                    f"Файл: {_file_path}", result=True)
                continue

            # if file is out of root directory
            if link_inspector.destination_file() is None:
                continue

            # specify link
            logger.debug(f"link = {link_inspector.link}")
            link_inspector.inspect_anchor()
            link_inspector.find_proper_anchor()
            link_inspector.set_proper_link()

            # inspect if proper link and origin one are equal
            if not link_inspector.compare_links():
                dir_file.update_line(index, link.link_to, link_inspector.proper_link)

        # update file content
        if not dry_run:
            file_writer(dir_file.full_path, dir_file.content, encoding="utf-8")

    print("Работа завершена.\n")

    if dry_run:
        logger.info("==================== Файлы не изменены ====================", result=True)

    else:
        logger.info("==================== Файлы изменены ====================", result=True)

    if not no_result:
        logger.info(f"Файл results.txt находится здесь:\n{result_file_path}")

    ctx.obj["keep_logs"] = keep_logs
    ctx.obj["no_result"] = no_result
    ctx.obj["result_file"] = result_file_path
    ctx.invoke(clear_logs)
