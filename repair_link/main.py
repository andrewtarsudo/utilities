# -*- coding: utf-8 -*-
from glob import iglob
from os.path import relpath
from pathlib import Path
from shutil import rmtree
from warnings import simplefilter

from loguru import logger

from repair_link.dir_file.const import FileLinkItem
from repair_link.dir_file.dir_file import TextFile
from repair_link.dir_file.file_dict import FileDict
from repair_link.general.const import StrPath, ADOC_EXTENSION, MD_EXTENSION, result_file_path, log_folder, FileLanguage, \
    prepare_logging
from repair_link.general.custom_logger import configure_custom_logging
from repair_link.general.errors import InvalidStorageAttributeError, InvalidFileDictAttributeError
from repair_link.general.link import Link
from repair_link.inspector.internal_link_inspector import internal_inspector
from repair_link.inspector.link_fixer import link_fixer
from repair_link.inspector.link_inspector import link_inspector
from repair_link.storage.storage import Storage
from repair_link.user_interaction.const import InputUser, PRESS_ENTER_KEY


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


@logger.catch
@configure_custom_logging("link_repair", is_initial=False)
def link_repair(input_user: InputUser):
    if input_user is None:
        return

    if not validate_dir_path(input_user.pathdir):
        logger.critical(f"Путь {input_user.pathdir} не существует или указывает не на директорию")
        input(PRESS_ENTER_KEY)
        exit()

    if has_no_required_files(input_user.pathdir):
        logger.warning(
            f"В директории {input_user.pathdir} не найдены файлы с расширением {MD_EXTENSION}, {ADOC_EXTENSION}")
        input(PRESS_ENTER_KEY)
        exit()

    _base_dir: Path = Path(input_user.pathdir).parent.parent.resolve()
    # operate with Storage
    storage: Storage = Storage(input_user.pathdir)
    storage.prepare()

    if storage is None:
        logger.error("Объект типа Storage не определен")
        raise InvalidStorageAttributeError

    logger.debug(prepare_logging(storage.dir_indexes.items()))
    logger.debug(prepare_logging(storage.dirindexes.items()))
    logger.debug(prepare_logging(storage.text_files.items()))
    logger.debug(prepare_logging(storage.non_text_files.items()))

    # operate with FileDict
    file_dict: FileDict = FileDict(input_user.pathdir)
    file_dict + iter(storage)

    if file_dict is None:
        logger.error("Объект типа FileDict не определен")
        raise InvalidFileDictAttributeError

    logger.debug(prepare_logging(file_dict.dict_files.items()))

    if input_user.anchor_validation:
        from repair_link.inspector.anchor_inspector import anchor_inspector
        # operate with AnchorInspector
        anchor_inspector + iter(file_dict.dict_files.values())

        if input_user.separate_languages:
            languages: list[FileLanguage] = [FileLanguage.RU, FileLanguage.EN]
        elif input_user.skip_en:
            languages: list[FileLanguage] = [FileLanguage.RU]
        else:
            languages: list[FileLanguage] = [FileLanguage.RU_EN]

        for language in languages:
            anchor_inspector.inspect_inside_file(language)
            anchor_inspector.inspect_all_files(language)

        for file, anchors in anchor_inspector.dict_changes.items():
            for anchor in anchors:
                line_number: list[int] = file.find_anchor(anchor)
                file.update_line(
                    line_number,
                    anchor,
                    f"{anchor}-{file.full_path.stem.lower().removeprefix('_').replace('_', '-').replace('.', '-')}",
                    is_boundary=True)

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

        if not input_user.dry_run:
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
        if not input_user.dry_run:
            dir_file.write()
    logger.info("Работа завершена.\n")

    if input_user.dry_run:
        logger.info("==================== Файлы не изменены ====================", result=True)
    else:
        logger.info("==================== Файлы изменены ====================", result=True)

    # delete result file
    if not input_user.no_result:
        result_file_path.unlink(True)
        logger.debug("results.txt has been deleted")
    else:
        logger.info(f"Файл results.txt находится здесь:\n{result_file_path}")
    # stop logging
    logger.remove()
    # delete logs
    if not input_user.keep_log:
        rmtree(log_folder, True)
    input(PRESS_ENTER_KEY)


if __name__ == '__main__':
    from repair_link.user_interaction.parse_input import parse_command_line

    simplefilter("ignore")

    _input_user: InputUser | None = parse_command_line()

    if not bool(_input_user):
        from repair_link.user_interaction.gui import get_input_user

        _input_user: InputUser | None = get_input_user()

    if _input_user is None:
        logger.remove()
        rmtree(log_folder, True)
    else:
        link_repair(_input_user)
