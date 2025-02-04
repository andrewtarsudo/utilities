# -*- coding: utf-8 -*-
from click.core import Context
from click.decorators import argument, help_option, option, pass_context
from click.types import BOOL, Path as ClickPath

from utilities.common.constants import HELP, StrPath
from utilities.convert_tables.line_formatter import LineFormatter
from utilities.convert_tables.xml_file import CoreDocument, XmlDocument
from utilities.scripts.cli import clear_logs, command_line_interface, MutuallyExclusiveOption


@command_line_interface.command(
    "convert-tables",
    help="Команда для корректного извлечения таблиц из файлов docx в формат Markdown")
@argument(
    "docx_file",
    type=ClickPath(
        exists=True,
        file_okay=True,
        resolve_path=True,
        allow_dash=False,
        dir_okay=False),
    required=True,
    metavar="DOCX_FILE")
@option(
    "-p", "--parse", "tables_dir",
    type=ClickPath(
        exists=False,
        file_okay=False,
        resolve_path=True,
        allow_dash=False,
        dir_okay=True),
    help="\b\nДиректория для хранения таблиц. По умолчанию: ./tables/.\nЕсли не существует, то будет создана",
    multiple=False,
    required=False,
    metavar="DIR_TABLES",
    default="./tables/")
@option(
    "-t", "--temp", "temp_dir",
    type=ClickPath(
        exists=False,
        file_okay=False,
        resolve_path=True,
        allow_dash=False,
        dir_okay=True),
    help="\b\nВременная директория для скрипта. По умолчанию: ./_temp/.\nЕсли не существует, то будет создана",
    multiple=False,
    required=False,
    metavar="TEMP_DIR",
    default="./_temp/")
@option(
    "-e", "--escape/--no-escape", "escape",
    type=BOOL,
    help="\b\nФлаг экранирования символов '<', '>'.\n"
         "По умолчанию: True, добавление '\\' перед символами",
    show_default=True,
    required=False,
    default=True)
@option(
    "-r", "--remove/--no-remove", "remove",
    type=BOOL,
    help="\b\nФлаг удаления всех множественных пробелов и пробелов \nперед знаками препинания.\n"
         "По умолчанию: True, удаление всех дополнительных пробелов",
    show_default=True,
    required=False,
    default=False)
@option(
    "-f", "--fix/--no-fix", "fix",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["keep"],
    type=BOOL,
    help="\b\nФлаг удаления лишних пробелов и экранирования символов.\n"
         "По умолчанию: не задано, обработка определяется параметрами \n"
         "--preserve и --escape.\n"
         "Имеет приоритет выше, чем у опций --preserve и --escape",
    show_default=True,
    required=False,
    default=None)
@option(
    "-k", "--keep/--no-keep", "keep",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["fix"],
    type=BOOL,
    help="\b\nФлаг извлечения текста без дополнительной обработки.\n"
         "По умолчанию: не задано, обработка определяется параметрами \n--preserve и --escape.\n"
         "Имеет приоритет выше, чем у опций --preserve и --escape",
    show_default=True,
    required=False,
    default=None)
@option(
    "--keep-logs",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг сохранения директории с лог-файлом по завершении \nработы в штатном режиме.\n"
         "По умолчанию: False, лог-файл и директория удаляются",
    show_default=True,
    required=False,
    default=False)
@help_option(
    "-h", "--help",
    help=HELP,
    is_eager=True)
@pass_context
def convert_tables_command(
        ctx: Context,
        docx_file: StrPath,
        tables_dir: StrPath = "./tables/",
        temp_dir: StrPath = "./_temp/",
        remove: bool = False,
        escape: bool = True,
        fix: bool = None,
        keep: bool = None,
        keep_logs: bool = False):
    if fix:
        remove_spaces: bool = True
        escape_chars: bool = True

    elif keep:
        remove_spaces: bool = False
        escape_chars: bool = False

    else:
        remove_spaces: bool = remove
        escape_chars: bool = escape

    line_formatter: LineFormatter = LineFormatter(remove_spaces, escape_chars)

    core_document: CoreDocument = CoreDocument(docx_file, temp_dir)
    core_document.unarchive()

    xml_document: XmlDocument = XmlDocument(core_document, tables_dir)
    xml_document.read()
    xml_document.parse_document(line_formatter)

    core_document.delete_temp_archive()

    ctx.obj["keep_logs"] = keep_logs
    ctx.invoke(clear_logs)
