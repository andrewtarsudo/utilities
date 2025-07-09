# -*- coding: utf-8 -*-
from glob import iglob
from pathlib import Path

from click.core import Context
from click.decorators import argument, help_option, option, pass_context
from click.termui import pause
from click.types import BOOL, Path as ClickPath
from click.utils import echo
from loguru import logger

from utilities.common.config_file import config_file
from utilities.common.errors import RepairLinksInvalidFileDictAttributeError, RepairLinksInvalidStorageAttributeError
from utilities.common.functions import file_reader, file_writer
from utilities.common.shared import ADOC_EXTENSION, HELP, MD_EXTENSION, PRESS_ENTER_KEY, StrPath
from utilities.repair_links.const import FileLanguage, prepare_logging
from utilities.repair_links.file_dict import FileDict, FileLinkItem, TextFile
from utilities.repair_links.general_storage import Storage
from utilities.repair_links.internal_link_inspector import internal_inspector
from utilities.repair_links.link import Link
from utilities.repair_links.link_fixer import link_fixer
from utilities.repair_links.link_inspector import link_inspector
from utilities.scripts.api_group import SwitchArgsAPIGroup
from utilities.scripts.cli import cli
from utilities.common.completion import dir_completion


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

    else:
        return True


def has_no_required_files(path: StrPath) -> bool:
    bool_md: bool = next(iglob(f"**/*{MD_EXTENSION}", root_dir=path, recursive=True), None) is None
    bool_adoc: bool = next(iglob(f"**/*{ADOC_EXTENSION}", root_dir=path, recursive=True), None) is None

    return bool_md and bool_adoc


@cli.command(
    "repair-links",
    cls=SwitchArgsAPIGroup,
    help="Команда для проверки и исправления ссылок в файлах документации")
@argument(
    "root",
    type=ClickPath(
        file_okay=False,
        resolve_path=True,
        allow_dash=False,
        dir_okay=True),
    required=True,
    shell_complete=dir_completion,
    metavar="ROOT")
@option(
    "-a/-A", "--anchor/--no-anchor", "anchor_validation",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг поиска повторяющихся якорей."
         "\nПо умолчанию: True, дублирующиеся якори обрабатываются",
    show_default=True,
    required=False,
    default=config_file.get_commands("repair-links", "anchor_validation"))
@option(
    "-d/-D", "--dry-run/--no-dry-run",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг вывода некорректных ссылок на экран без"
         "\nнепосредственного изменения файлов."
         "\nПо умолчанию: False, файлы перезаписываются",
    show_default=True,
    required=False,
    default=config_file.get_commands("repair-links", "dry_run"))
@option(
    "-n/-N", "--no-result/--with-result",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг удаления файла с результатами работы скрипта по"
         "\nзавершении работы в штатном режиме."
         "\nПо умолчанию: False, файл сохраняется",
    show_default=True,
    required=False,
    default=config_file.get_commands("repair-links", "no_result"))
@option(
    "-s/-S", "--separate/--together", "separate_languages",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг раздельной обработки файлов на различных языках."
         "\nПо умолчанию: True, файлы обрабатываются отдельно",
    show_default=True,
    required=False,
    default=config_file.get_commands("repair-links", "separate_languages"))
@option(
    "-e/-E", "--skip-en/--with-en",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг обработки файлов только на русском языке."
         "\nПо умолчанию: False, обрабатываются файлы на обоих"
         "\nязыках",
    show_default=True,
    required=False,
    default=config_file.get_commands("repair-links", "skip_en"))
@option(
    "-k/-K", "--keep-logs/--remove-logs",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг сохранения директории с лог-файлом"
         "\nпо завершении работы в штатном режиме."
         "\nПо умолчанию: False, лог-файл и директория удаляются",
    show_default=True,
    required=False,
    default=config_file.get_commands("repair-links", "keep_logs"))
@help_option(
    "-h", "--help",
    help=HELP,
    is_eager=True)
@pass_context
def repair_links_command(
        ctx: Context,
        root: Path,
        dry_run: bool = False,
        no_result: bool = False,
        anchor_validation: bool = True,
        separate_languages: bool = True,
        skip_en: bool = False,
        keep_logs: bool = False):
    result_file_path: Path = Path.cwd().joinpath("results.txt")

    if not validate_dir_path(root):
        logger.error(f"Путь {root} не существует или указывает не на директорию")
        pause(PRESS_ENTER_KEY)
        ctx.exit(0)

    if has_no_required_files(root):
        logger.warning(
            f"В директории {root} не найдены файлы с расширением {MD_EXTENSION}, {ADOC_EXTENSION}")
        pause(PRESS_ENTER_KEY)
        ctx.exit(0)

    _base_dir: Path = Path(root).parent.parent.resolve()

    # operate with Storage
    storage: Storage = Storage(root)
    storage.prepare()

    if storage is None:
        logger.error("Объект типа Storage не определен")
        raise RepairLinksInvalidStorageAttributeError

    logger.debug(prepare_logging(storage.dir_indexes.items()))
    logger.debug(prepare_logging(storage.dirindexes.items()))
    logger.debug(prepare_logging(storage.text_files.items()))
    logger.debug(prepare_logging(storage.non_text_files.items()))

    # operate with FileDict
    file_dict: FileDict = FileDict(root)
    file_dict + iter(storage)

    if file_dict is None:
        logger.error("Объект типа FileDict не определен")
        raise RepairLinksInvalidFileDictAttributeError

    logger.debug(prepare_logging(file_dict.dict_files.items()))

    if anchor_validation:
        from utilities.repair_links.anchor_inspector import anchor_inspector

        # operate with AnchorInspector
        anchor_inspector + iter(file_dict.dict_files.values())

        if separate_languages:
            languages: list[FileLanguage] = [FileLanguage.RU, FileLanguage.EN]

        elif skip_en:
            languages: list[FileLanguage] = [FileLanguage.RU]

        else:
            languages: list[FileLanguage] = [FileLanguage.RU_EN_FR]

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

        dir_file._content = file_reader(dir_file.full_path, "lines", encoding="utf-8")

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
                _file_path: str = _base_dir.relative_to(link_inspector.link.from_file).as_posix()
                logger.error(
                    f"Не удалось обработать ссылку в файле.\n"
                    f"Ссылка: {link_inspector.link.link_to}\n"
                    f"Файл: {_file_path}", result=True)
                continue

            # if file is out of root directory
            if link_inspector.destination_file() is None:
                continue

            # specify link
            logger.debug(f"Ссылка = {link_inspector.link}")
            link_inspector.inspect_anchor()
            link_inspector.find_proper_anchor()
            link_inspector.set_proper_link()

            # inspect if proper link and origin one are equal
            if not link_inspector.compare_links():
                dir_file.update_line(index, link.link_to, link_inspector.proper_link)

        # update file content
        if not dry_run:
            file_writer(dir_file.full_path, dir_file.content, encoding="utf-8")

    echo("Работа завершена.\n")

    if dry_run:
        logger.info("==================== Файлы не изменены ====================", result=True)

    else:
        logger.info("==================== Файлы изменены ====================", result=True)

    if not no_result:
        logger.info(f"Файл results.txt находится здесь:\n{result_file_path}")

    ctx.obj["keep_logs"] = keep_logs
    ctx.obj["no_result"] = no_result
    ctx.obj["result_file"] = result_file_path
