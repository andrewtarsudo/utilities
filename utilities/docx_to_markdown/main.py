# -*- coding: utf-8 -*-
import os.path as p
from importlib import util
from subprocess import CalledProcessError, run
from sys import argv, executable, exit, modules, version_info
from tkinter.filedialog import askopenfilename
from types import ModuleType


def get_user_input() -> str:
    filetypes: tuple[tuple[str, str], ...] = (
        ("Word files", "*.docx *.docm"),
        ("docx files", "*.docx"),
        ("docm files", "*.docm")
    )
    initialdir: str = p.join(p.expanduser("~"), "Desktop")
    title: str = "Выберите файл:"
    file = askopenfilename(filetypes=filetypes, initialdir=initialdir, title=title)
    return file


if __name__ == '__main__':
    if version_info < (3, 8):
        print("Версия Python должна быть не ниже 3.8.")
        input("Нажмите <Enter>, чтобы закрыть окно ...")
        exit(-1)

    if version_info >= (3, 11):
        _packages: tuple[str, ...] = ("lxml",)
    else:
        _packages: tuple[str, ...] = ("lxml", "tomli")

    for _package in _packages:
        if _package in modules:
            continue
        elif _package not in modules and (spec := util.find_spec(_package)) is not None:
            module: ModuleType = util.module_from_spec(spec)
            modules[_package] = module
            spec.loader.exec_module(module)
        else:
            try:
                run([executable, "-m", "pip", "install", _package]).check_returncode()
            except CalledProcessError as e:
                print(f"{e.__class__.__name__}\nКод ответа {e.returncode}\nОшибка {e.output}")
                print(f"Не удалось импортировать пакет `{_package}`")
                raise
            except OSError as e:
                print(f"{e.__class__.__name__}\nФайл {e.filename}\nОшибка {e.strerror}")
                print(f"Не удалось импортировать пакет `{_package}`")
                raise

    if len(argv) == 2:
        path: str | None = argv[1]
    else:
        path: str | None = get_user_input()

    if not path:
        print("Файл не выбран.")
        input("Нажмите <Enter>, чтобы закрыть окно ...")
        exit(-2)

    abs_path: str = p.realpath(path)

    if not p.exists(abs_path):
        print("Файл не найден.")
        input("Нажмите <Enter>, чтобы закрыть окно ...")
        exit(-3)

    from xml_file import CoreDocument, XmlDocument

    core_document: CoreDocument = CoreDocument(abs_path)
    core_document.unarchive()

    xml_document: XmlDocument = XmlDocument(core_document)
    xml_document.read()
    xml_document.parse_document()

    core_document.delete_temp_archive()

    print(f"Таблицы из файла в формате Markdown находятся в директории:\n{xml_document.table_dir}")
    input("Нажмите <Enter>, чтобы закрыть окно ...")

    exit(0)
