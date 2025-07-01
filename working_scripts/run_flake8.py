# -*- coding: utf-8 -*-
from os import chdir
from pathlib import Path


def run_flake8_command(root: str | Path = None):
    from subprocess import CalledProcessError, CompletedProcess, run
    from sys import platform

    if root is None:
        root: Path = Path.cwd().resolve()

    else:
        root: Path = Path(root).expanduser().resolve()

    chdir(root)

    print(f"root = {root}")

    file: Path = root.joinpath("flake8.txt")
    file.unlink(missing_ok=True)
    file.touch(exist_ok=True)

    flake8: list[str] = [
        "flake8",
        "--color=auto",
        "--config=.flake8",
        f"--output-file={file.as_posix()}",
        "--verbose",
        "--benchmark",
        "--exit-zero",
        "__main__.py",
        "utilities/common/",
        "utilities/convert_tables/",
        "utilities/get_terms/",
        "utilities/repair_links/",
        "utilities/scripts/",
        "utilities/set_table_cols/"]

    shell: bool = platform.startswith("win")

    try:
        _: CompletedProcess = run(
            flake8,
            encoding="utf-8",
            shell=shell,
            capture_output=True,
            check=True)

        _.check_returncode()

    except CalledProcessError as e:
        print(f"{e.__class__.__name__}, код {e.returncode}:\n{str(e)}")
        raise

    except PermissionError as e:
        access: int = int(f"{file.stat().st_mode}", 8)

        print(f"{e.__class__.__name__}, недостаточно прав доступа к файлу {file}.\nМаска: {access}")
        raise

    except RuntimeError as e:
        print(f"{e.__class__.__name__}, ошибка во время выполнения скрипта")
        raise

    except OSError as e:
        print(f"{e.__class__.__name__}, код {e.errno}\nОшибка {e.strerror}")
        raise

    else:
        print(f"Отчет flake8 записан в файл {file.as_posix()}")


if __name__ == '__main__':
    run_flake8_command("../")
