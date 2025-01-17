# -*- coding: utf-8 -*-
from glob import iglob
from os.path import relpath
from pathlib import Path

from click.core import Context
from click.decorators import argument, help_option, option, pass_context
from click.termui import echo, pause
from click.types import BOOL, Path as ClickPath
from loguru import logger

from utilities.common.constants import ADOC_EXTENSION, HELP, MD_EXTENSION, PRESS_ENTER_KEY, StrPath
from utilities.common.errors import InvalidFileDictAttributeError, InvalidStorageAttributeError
from utilities.repair_link.const import FileLanguage, prepare_logging
from utilities.repair_link.file_dict import FileDict, FileLinkItem, TextFile
from utilities.repair_link.general_storage import Storage
from utilities.repair_link.internal_link_inspector import internal_inspector
from utilities.repair_link.link import Link
from utilities.repair_link.link_fixer import link_fixer
from utilities.repair_link.link_inspector import link_inspector
from utilities.scripts.cli import clear_logs, command_line_interface


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


@command_line_interface.command(
    "link-repair",
    help="Команда для проверки и исправления ссылок в файлах документации")
@argument(
    "pathdir",
    type=ClickPath(
        file_okay=False,
        resolve_path=True,
        allow_dash=False,
        dir_okay=True),
    required=True,
    nargs=1,
    is_eager=True)
@option(
    "-d", "--dry-run",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг вывода некорректных ссылок на экран без изменения файлов.\n"
         "По умолчанию: False, файлы перезаписываются",
    show_default=True,
    required=False,
    default=False)
@option(
    "-n", "--no-result",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг удаления файла с результатами работы скрипта по завершении \n"
         "работы в штатном режиме.\n"
         "По умолчанию: False, файл сохраняется",
    show_default=True,
    required=False,
    default=True)
@option(
    "-a", "--anchor-disable", "anchor_validation",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг поиска повторяющихся якорей.\n"
         "По умолчанию: True, поиск дублирующихся якорей осуществляется",
    show_default=True,
    required=False,
    default=True)
@option(
    "-s", "--separate", "separate_languages",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг раздельной обработки файлов на различных языках.\n"
         "По умолчанию: True, файлы на русском и английском обрабатываются \n"
         "отдельно",
    show_default=True,
    required=False,
    default=True)
@option(
    "--skip-en",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг обработки файлов только на русском языке.\n"
         "По умолчанию: False, обрабатываются файлы на обоих языках",
    show_default=True,
    required=False,
    default=False)
@option(
    "--keep-logs",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг сохранения директории с лог-файлом по завершении работы \nв штатном режиме.\n"
         "По умолчанию: False, лог-файл и директория удаляются",
    show_default=True,
    required=False,
    default=False)
@help_option(
    "-h", "--help",
    help=HELP,
    is_eager=True)
@pass_context
def link_repair_command(
        ctx: Context,
        pathdir: Path,
        dry_run: bool = False,
        no_result: bool = True,
        anchor_validation: bool = True,
        separate_languages: bool = True,
        skip_en: bool = False,
        keep_logs: bool = False):
    result_file_path: Path = Path.cwd().joinpath("results.txt")

    if not validate_dir_path(pathdir):
        logger.critical(f"Путь {pathdir} не существует или указывает не на директорию")
        pause(PRESS_ENTER_KEY)
        ctx.exit(0)

    if has_no_required_files(pathdir):
        logger.warning(
            f"В директории {pathdir} не найдены файлы с расширением {MD_EXTENSION}, {ADOC_EXTENSION}")
        pause(PRESS_ENTER_KEY)
        ctx.exit(0)

    _base_dir: Path = Path(pathdir).parent.parent.resolve()

    # operate with Storage
    storage: Storage = Storage(pathdir)
    storage.prepare()

    if storage is None:
        logger.error("Объект типа Storage не определен")
        raise InvalidStorageAttributeError

    logger.debug(prepare_logging(storage.dir_indexes.items()))
    logger.debug(prepare_logging(storage.dirindexes.items()))
    logger.debug(prepare_logging(storage.text_files.items()))
    logger.debug(prepare_logging(storage.non_text_files.items()))

    # operate with FileDict
    file_dict: FileDict = FileDict(pathdir)
    file_dict + iter(storage)

    if file_dict is None:
        logger.error("Объект типа FileDict не определен")
        raise InvalidFileDictAttributeError

    logger.debug(prepare_logging(file_dict.dict_files.items()))

    if anchor_validation:
        from utilities.repair_link.anchor_inspector import anchor_inspector

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
            dir_file.write()

        dir_file.read()

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
            dir_file.write()

    echo("Работа завершена.\n")

    if dry_run:
        logger.info("==================== Файлы не изменены ====================", result=True)

    else:
        logger.info("==================== Файлы изменены ====================", result=True)

    # delete result file
    if not no_result:
        result_file_path.unlink(True)
        logger.debug("Файл results.txt был удален")

    else:
        logger.info(f"Файл results.txt находится здесь:\n{result_file_path}")

    ctx.obj["keep_logs"] = keep_logs
    ctx.invoke(clear_logs)
