# -*- coding: utf-8 -*-
from os import environ
from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess, run
from sys import platform

if __name__ == "__main__":
    log_file: str = "pyinstaller.log"
    print(f"log: {Path(log_file).resolve()}")

    if platform.startswith("win"):
        spec_file: str = "utilities.exe.spec"
        exe_file: str = r".\bin\tw_utilities.exe"

    else:
        spec_file: str = "utilities.spec"
        exe_file: str = r"./bin/tw_utilities"

    environ["VIRTUAL_ENV"] = ".venv"

    install: list[str] = [
        "uv",
        "run",
        "--active",
        "pyinstaller",
        "--noconfirm",
        "--distpath",
        "./bin",
        f"{spec_file}",
        f"2> {log_file}"]

    try:
        _: CompletedProcess = run(
            install,
            encoding="utf-8",
            check=True)

        _.check_returncode()

    except CalledProcessError as e:
        print(f"{e.__class__.__name__}, код {e.returncode}:\n{e.stderr}")
        raise

    except PermissionError as e:
        from os import environ, stat

        print(f"Недостаточно прав доступа к файлу {log_file}.\nМаска: {stat(log_file).st_mode}")
        raise

    except RuntimeError as e:
        print(f"{e.__class__.__name__}, ошибка во время выполнения скрипта")
        raise

    except OSError as e:
        print(f"{e.__class__.__name__}, код {e.errno}\nОшибка {e.strerror}")
        raise

    else:
        print(f"Исполняемый файл {exe_file} успешно создан")
