# -*- coding: utf-8 -*-
from pathlib import Path

from _pytest.fixtures import fixture


@fixture(scope="module")
def folder():
    return Path.cwd().parent.joinpath("docs").as_posix()


@fixture(scope="module")
def folder_result():
    return (
        "README_terms.adoc\n"
        "README_list_files.adoc\n"
        "README_check_russian.adoc\n"
        "README_validate_yaml.adoc\n"
        "README_format_code.adoc\n"
        "README_convert_tables.adoc\n"
        "README_link_repair.adoc\n"
        "README_repair_svg.adoc\n"
        "Временные журналы скрипта удалены\n")


@fixture(scope="module")
def check():
    pass
