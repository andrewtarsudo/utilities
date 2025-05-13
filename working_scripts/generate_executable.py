# -*- coding: utf-8 -*-

def generate_executable_command():
    from os import environ
    from pathlib import Path
    from subprocess import CalledProcessError, CompletedProcess, run
    from sys import platform

    log_file: Path = Path.cwd().joinpath("pyinstaller.log")
    print(f"Лог: {log_file.resolve().as_posix()}")

    if platform.startswith("win"):
        spec_file: Path = Path.cwd().joinpath("utilities.exe.spec")
        exe_file: Path = Path.cwd().joinpath("bin/tw_utilities.exe")
        environ["VIRTUAL_ENV"] = "venv"
        shell: bool = True

    else:
        spec_file: Path = Path.cwd().joinpath("utilities.spec")
        exe_file: Path = Path.cwd().joinpath("bin/tw_utilities")
        environ["VIRTUAL_ENV"] = ".venv"
        shell: bool = False

    install: list[str] = [
        "uv",
        "run",
        "--active",
        "pyinstaller",
        "--noconfirm",
        "--distpath",
        "./bin",
        f"{spec_file.as_posix()}"]

    try:
        with open(log_file, "w", encoding="utf-8", errors="ignore") as lf:
            _: CompletedProcess = run(
                install,
                shell=shell,
                stderr=lf,
                encoding="utf-8",
                check=True)

            _.check_returncode()

    except CalledProcessError as e:
        print(f"{e.__class__.__name__}, код {e.returncode}:\n{e.stderr}")
        raise

    except PermissionError as e:
        access: int = int(f"{log_file.stat().st_mode}", 8)

        print(f"{e.__class__.__name__}, недостаточно прав доступа к файлу {log_file}.\nМаска: {access}")
        raise

    except RuntimeError as e:
        print(f"{e.__class__.__name__}, ошибка во время выполнения скрипта")
        raise

    except OSError as e:
        print(f"{e.__class__.__name__}, код {e.errno}\nОшибка {e.strerror}")
        raise

    else:
        print(f"Исполняемый файл {exe_file} успешно создан")


if __name__ == '__main__':
    generate_executable_command()
