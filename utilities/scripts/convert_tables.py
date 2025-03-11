# -*- coding: utf-8 -*-
from pathlib import Path

from click.core import Context
from typer.main import Typer
from typer.params import Argument, Option
from typing_extensions import Annotated

from utilities.convert_tables.line_formatter import LineFormatter
from utilities.convert_tables.xml_file import CoreDocument, XmlDocument
from utilities.common.functions import clear_logs

convert_tables: Typer = Typer(
    add_help_option=True,
    rich_markup_mode="rich",
    help="Команда для корректного извлечения таблиц из файлов docx в формат Markdown")


@convert_tables.command(
    "convert-tables",
    help="Команда для корректного извлечения таблиц из файлов docx в формат Markdown")
def convert_tables_command(
        ctx: Context,
        docx_file: Annotated[
            Path,
            Argument(
                metavar="DOCX_FILE",
                help="Путь до файла Word в формате *.docx или *.docm",
                exists=True,
                file_okay=True,
                dir_okay=False,
                resolve_path=True,
                allow_dash=False)],
        tables_dir: Annotated[
            Path,
            Option(
                "--parse", "-p",
                help="Директория для таблиц. По умолчанию: ./tables/."
                     "\nЕсли не существует, то будет создана",
                file_okay=False,
                dir_okay=True,
                resolve_path=True,
                allow_dash=False)] = "./tables/",
        temp_dir: Annotated[
            Path,
            Option(
                "--temp-dir", "-t",
                help="Временная директория. По умолчанию: ./_temp/."
                     "\nЕсли не существует, то будет создана",
                exists=True,
                file_okay=False,
                dir_okay=True,
                resolve_path=True,
                allow_dash=False)] = "./_temp/",
        remove: Annotated[
            bool,
            Option(
                "--remove/--no-remove", "-r/-R",
                show_default=True,
                help="Флаг удаления всех множественных пробелов и пробелов"
                     "\nперед знаками препинания."
                     "\nПо умолчанию: True, удаление всех лишних пробелов")] = False,
        escape: Annotated[
            bool,
            Option(
                "--escape/--no-escape", "-e/-E",
                show_default=True,
                help="Флаг экранирования символов '<', '>'."
                     "\nПо умолчанию: True, добавление '\\' перед символами")] = True,
        fix: Annotated[
            bool,
            Option(
                "--fix/--no-fix", "-f/-F",
                show_default=True,
                help="Флаг удаления лишних пробелов и экранирования символов."
                     "\nПо умолчанию: не задано, определяется параметрами"
                     "\n--escape и --remove."
                     "\nПриоритет выше, чем у опций --escape и --remove")] = None,
        keep: Annotated[
            bool,
            Option(
                "--keep/--no-keep", "-k/-K",
                show_default=True,
                help="Флаг извлечения текста без дополнительной обработки."
                     "\nПо умолчанию: не задано, определяется параметрами"
                     "\n--escape и --remove."
                     "\nПриоритет выше, чем у опций --escape и --remove")] = None,
        keep_logs: Annotated[
            bool,
            Option(
                "--keep-logs",
                show_default=True,
                help="Флаг сохранения директории с лог-файлом по завершении\nработы в штатном режиме."
                     "\nПо умолчанию: False, лог-файл и директория удаляются")] = False):
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
