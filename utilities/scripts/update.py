# # -*- coding: utf-8 -*-
# from os import environ
# from pathlib import Path
# from string import Template
# from subprocess import CalledProcessError, Popen, run, TimeoutExpired
#
# try:
#     from subprocess import CREATE_NO_WINDOW
# except:
#     pass
#
# import sys
# from typing import Any
#
# from click.core import Context
# from click.decorators import pass_context
# from loguru import logger
#
# from utilities.common.functions import file_reader_type, get_shell, get_version, GitFile, is_macos, is_windows
# from utilities.common.shared import BASE_PATH
# from utilities.scripts.cli import APIGroup, cli
#
#
# ENV_VAR: str = "_TW_UTILITIES_UPDATE"
#
#
# def set_env(*, timeout: float | None = 15.0):
#     root_dir: Path = Path(getattr(sys, "_MEIPASS"))
#
#     shell_exe: str = get_shell()
#
#     if is_windows():
#         exe: str = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
#         file: Path = root_dir.joinpath("sources/set_env.ps1").resolve()
#         command: list[str] = [exe, "-File", file]
#         shell: bool = True
#
#     elif is_macos():
#         file: Path = root_dir.joinpath("sources/set_env.zsh")
#         command: list[str] = [shell_exe, file]
#         shell: bool = False
#
#     else:
#         file: Path = root_dir.joinpath("sources/set_env.sh")
#         command: list[str] = [shell_exe, file]
#         shell: bool = False
#
#     try:
#         file.chmod(0o775)
#         run(command, shell=shell, timeout=timeout)
#
#     except CalledProcessError as e:
#         logger.error(
#             f"Не удалось задать переменную {ENV_VAR} и обновить оболочку."
#             f"\nВывод команды: {e.stdout}\nВывод ошибки: {e.stderr}\nКоманда: {e.cmd}")
#         raise
#
#     except TimeoutExpired as e:
#         logger.error(
#             f"Не удалось задать переменную {ENV_VAR} и обновить оболочку за время {timeout:.0f} секунд."
#             f"\nВывод команды: {e.output}")
#         set_env(timeout=None)
#         raise
#
#     else:
#         logger.debug(f"Задана переменная {ENV_VAR}")
#         return
#
#
# def convert_value(value: int | str | bool):
#     TRUE: tuple[str, ...] = ("1", "true", "yes", "on")
#     FALSE: tuple[str, ...] = ("0", "false", "no", "off")
#
#     if value is None:
#         return True
#
#     _value: str = str(value).lower()
#
#     if _value == "-1":
#         return None
#
#     elif _value in TRUE:
#         return True
#
#     elif _value in FALSE:
#         logger.success(f"{ENV_VAR} = {value}")
#         return False
#
#     else:
#         logger.debug(f"Значение {value} недопустимо")
#         logger.error(
#             f"Переменной {ENV_VAR} можно задать одно из следующих значений:"
#             f"\n{TRUE} для активации автообновления;"
#             f"\n{FALSE} для отключения автообновления.")
#
#         return True
#
#
# def compare_versions(project_id: int):
#     git_file: GitFile = GitFile("pyproject.toml", project_id)
#     git_file.download()
#
#     if not bool(git_file):
#         logger.error("Не удалось подключиться к репозиторию Git, проверка обновлений завершена")
#         return True
#
#     else:
#         content: dict[str, Any] = file_reader_type(git_file.download_destination, "toml")
#         latest_version: str = content.get("project").get("version")
#
#         current_version: str = get_version()
#
#         return current_version == latest_version
#
#
# def update_exe(ctx: Context, exe_file_name: str, project_id: int, **kwargs):
#     executable_file: GitFile = GitFile(exe_file_name, project_id, temp_dir=ctx.obj.get("temp_dir"), **kwargs)
#     executable_file.download()
#
#     return executable_file.download_destination
#
#
# @cli.command(
#     "update",
#     cls=APIGroup,
#     help="Команда для замены переменных на их значения",
#     hidden=True)
# @pass_context
# def update_command(ctx: Context):
#     env_var: Any = environ.get(ENV_VAR)
#
#     if env_var is None:
#         is_update: bool = True
#         set_env()
#
#     else:
#         is_update: bool | None = convert_value(env_var)
#
#     if is_update is None or not is_update:
#         logger.info(
#             "Автообновление отключено."
#             f"\nЧтобы включить, необходимо задать переменной {ENV_VAR} значение:"
#             "\n1 / \"1\" / \"True\" / true / \"yes\" / \"on\" в любом регистре.\n")
#         return
#
#     else:
#         project_id: int = 65722828
#
#         if compare_versions(project_id):
#             logger.success("Используется последняя версия")
#             return
#
#         elif is_windows():
#             exe_file_name: str = "bin/tw_utilities.exe"
#
#         else:
#             exe_file_name: str = "bin/tw_utilities"
#
#     new_file: Path = update_exe(ctx, exe_file_name, project_id)
#     temp_dir: Path = Path(ctx.obj.get("temp_dir"))
#
#     runner: Path = BASE_PATH.joinpath("sources/runner.txt").expanduser()
#     runner_exe: Path = Path.home().joinpath(temp_dir).joinpath("runner.py")
#     runner_exe.parent.mkdir(parents=True, exist_ok=True)
#     runner_exe.touch(exist_ok=True)
#
#     old_file: str = sys.executable
#
#     with open(runner_exe, "wb") as fw, open(runner, "r", encoding="utf-8", errors="ignore") as fr:
#         template: Template = Template(fr.read())
#         kwargs: dict[str, str] = {
#             "old_file": f"\"{str(old_file)}\"",
#             "new_file": f"\"{str(new_file)}\"",
#             "shell": f"{is_windows()}"}
#
#         data: str = template.safe_substitute(kwargs)
#         fw.write(data.encode())
#
#     runner_exe.chmod(0o775, follow_symlinks=True)
#     Popen([runner_exe], creationflags=CREATE_NO_WINDOW)
#
#     sys.exit(0)
#
#     # ctx.obj["keep_logs"] = keep_logs
