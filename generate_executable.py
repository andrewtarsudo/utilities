# -*- coding: utf-8 -*-
from subprocess import CalledProcessError, run
from sys import platform

if __name__ == "__main__":
    log_file: str = "pyinstaller.log"

    if platform.startswith("msys"):
        spec_file: str = "utilities.exe.spec"
        exe_file: str = r".\bin\tw_utilities.exe"

    else:
        spec_file: str = "utilities.spec"
        exe_file: str = r"./bin/tw_utilities"

    args: list[str] = [
        "poetry",
        "run",
        "pyinstaller",
        "--noconfirm",
        "--distpath",
        "./bin",
        f"{spec_file}"]

    try:
        with open(log_file, "w", encoding="utf-8") as f:
            run(
                args,
                capture_output=True,
                encoding="utf-8",
                check=True).check_returncode()

    except CalledProcessError as e:
        print(f"{e.__class__.__name__}, код {e.returncode}:\n{e.stderr}")

    else:
        print(f"Исполняемый файл {exe_file} успешно создан")
