# -*- coding: utf-8 -*-
from click.core import Context
from click.decorators import argument, help_option, option, pass_context
from click.types import BOOL, Path as ClickPath

from utilities.common.completion import doc_completion
from utilities.common.config_file import config_file
from utilities.common.shared import HELP, StrPath
from utilities.convert_tables.line_formatter import LineFormatter
from utilities.convert_tables.xml_file import CoreDocument, XmlDocument
from utilities.scripts.api_group import MutuallyExclusiveOption, SwitchArgsAPIGroup
from utilities.scripts.cli import cli


@cli.command(
    "convert-tables",
    cls=SwitchArgsAPIGroup,
    help="Команда для корректного извлечения таблиц из файлов docx в формат Markdown")
@argument(
    "docx",
    type=ClickPath(
        exists=True,
        file_okay=True,
        resolve_path=True,
        allow_dash=False,
        dir_okay=False),
    required=True,
    shell_complete=doc_completion,
    metavar="DOCX")
@option(
    "-p", "--parse", "tables_dir",
    type=ClickPath(
        file_okay=False,
        resolve_path=True,
        allow_dash=False,
        dir_okay=True),
    help="\b\nДиректория для таблиц. По умолчанию: ./tables/."
         "\nЕсли не существует, то будет создана",
    multiple=False,
    required=False,
    metavar="DIR_TABLES",
    default=config_file.get_commands("convert-tables", "tables_dir"))
@option(
    "-t", "--temp", "temp_dir",
    type=ClickPath(
        exists=False,
        file_okay=False,
        resolve_path=True,
        allow_dash=False,
        dir_okay=True),
    help="\b\nВременная директория. По умолчанию: ./_temp/."
         "\nЕсли не существует, то будет создана",
    multiple=False,
    required=False,
    metavar="TEMP_DIR",
    default=config_file.get_commands("convert-tables", "temp_dir"))
@option(
    "-e/-E", "--escape/--no-escape", "escape",
    type=BOOL,
    help="\b\nФлаг экранирования символов '<', '>'."
         "\nПо умолчанию: True, добавление '\\' перед символами",
    show_default=True,
    required=False,
    default=config_file.get_commands("convert-tables", "escape"))
@option(
    "-r/-R", "--remove/--no-remove", "remove",
    type=BOOL,
    help="\b\nФлаг удаления всех множественных пробелов и пробелов"
         "\nперед знаками препинания."
         "\nПо умолчанию: True, удаление всех лишних пробелов",
    show_default=True,
    required=False,
    default=config_file.get_commands("convert-tables", "remove"))
@option(
    "--fix/--no-fix", "fix",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["keep"],
    type=BOOL,
    help="\b\nФлаг удаления лишних пробелов и экранирования символов."
         "\nПо умолчанию: не задано, определяется параметрами"
         "\n'[magenta]--escape[/magenta]' и '[magenta]--remove[/magenta]'."
         "\nПриоритет выше, чем у опций '[magenta]--escape[/magenta]' и '[magenta]--remove[/magenta]'",
    show_default=True,
    required=False,
    default=config_file.get_commands("convert-tables", "fix"))
@option(
    "--keep/--no-keep", "keep",
    cls=MutuallyExclusiveOption,
    mutually_exclusive=["fix"],
    type=BOOL,
    help="\b\nФлаг извлечения текста без дополнительной обработки."
         "\nПо умолчанию: не задано, определяется параметрами"
         "\n'[magenta]--escape[/magenta]' и '[magenta]--remove[/magenta]'."
         "\nПриоритет выше, чем у опций '[magenta]--escape[/magenta]' и '[magenta]--remove[/magenta]'",
    show_default=True,
    required=False,
    default=config_file.get_commands("convert-tables", "keep"))
@option(
    "-k/-K", "--keep-logs/--remove-logs",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг сохранения директории с лог-файлом по завершении"
         "\nработы в штатном режиме."
         "\nПо умолчанию: False, лог-файл и директория удаляются",
    show_default=True,
    required=False,
    default=config_file.get_commands("convert-tables", "keep_logs"))
@help_option(
    "-h", "--help",
    help=HELP,
    is_eager=True)
@pass_context
def convert_tables_command(
        ctx: Context,
        docx: StrPath,
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

    core_document: CoreDocument = CoreDocument(docx, temp_dir)
    core_document.unarchive()

    xml_document: XmlDocument = XmlDocument(core_document, tables_dir)
    xml_document.read()
    xml_document.parse_document(line_formatter)

    core_document.delete_temp_archive()

    ctx.obj["keep_logs"] = keep_logs
