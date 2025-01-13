# -*- coding: utf-8 -*-
# from importlib import import_module
# from subprocess import CalledProcessError, run
# from sys import executable, modules, version_info
#
# from utilities.common.constants import PRESS_ENTER_KEY
# from utilities.repair_link.const import log_folder
# from utilities.repair_link.general.errors import InvalidPythonVersion
#
# # validate the current Python version
# if version_info < (3, 8):
#     print("Версия Python должна быть не меньше, чем 3.8.")
#     input(PRESS_ENTER_KEY)
#     raise InvalidPythonVersion
#
# # required packages
# _packages: tuple[str, ...] = ("loguru",)
# for _package in _packages:
#     if _package not in modules:
#         try:
#             # attempt to import the module
#             import_module(_package)
#         # if the module is not installed
#         except ModuleNotFoundError | ImportError:
#             try:
#                 # attempt to install the module through the pip
#                 run([executable, "-m", "pip", "install", _package]).check_returncode()
#             except CalledProcessError as e:
#                 print(f"{e.__class__.__name__}\nКод ошибки {e.returncode}\nОшибка {e.output}")
#                 print(f"Не удалось импортировать модуль `{_package}`")
#                 raise
#             except OSError as e:
#                 print(f"{e.__class__.__name__}\nФайл {e.filename}\nОшибка {e.strerror}")
#                 print(f"Не удалось импортировать модуль `{_package}`")
#                 raise
#
# # create the folder for logs if not exists
# if not log_folder.exists():
#     log_folder.mkdir(parents=True)
