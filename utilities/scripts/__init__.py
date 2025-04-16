# -*- coding: utf-8 -*-
from utilities.scripts.args_help_dict import ArgsHelpDict
from utilities.scripts.api_group import APIGroup, NoArgsAPIGroup, SwitchArgsAPIGroup, TermsAPIGroup, install_completion
from utilities.scripts.completion import dir_completion, doc_completion, file_completion, file_dir_completion, PowershellComplete

from utilities.scripts.cli import clear_logs, cli, install_command
from utilities.scripts.check_russian import check_russian_command
from utilities.scripts.convert_tables import convert_tables_command
from utilities.scripts.filter_images import filter_images_command
from utilities.scripts.format_code import format_code_command
from utilities.scripts.help import help_command
from utilities.scripts.link_repair import link_repair_command
from utilities.scripts.list_files import list_files_command
from utilities.scripts.reduce_image import reduce_image_command
from utilities.scripts.repair_svg import repair_svg_command
from utilities.scripts.table_cols import table_cols_command
from utilities.scripts.terms import terms_command
from utilities.scripts.validate_yaml_file import validate_yaml_command
