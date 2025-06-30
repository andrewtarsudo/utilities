# -*- coding: utf-8 -*-
from pathlib import Path


def run_pyment_command(root: str | Path = None):
    from os import environ, chdir
    from subprocess import CalledProcessError, CompletedProcess, run
    from sys import platform

    if root is None:
        root: Path = Path.cwd().resolve()

    else:
        root: Path = Path(root).expanduser().resolve()

    environ["VIRTUAL_ENV"] = root.joinpath(".venv/").as_posix()

    pyment_dir: Path = root.joinpath("pyment/")
    pyment_dir.mkdir(parents=True, exist_ok=True)
    chdir(pyment_dir)

    shell: bool = platform.startswith("win")

    command: list[str] = [
        "uv",
        "run",
        "pyment",
        "--config-file",
        "../pyment.conf",
        "--ignore-private",
        "true",
        "../utilities/"]

    try:
        _: CompletedProcess = run(
            command,
            shell=shell,
            encoding="utf-8",
            check=True)

        _.check_returncode()

    except CalledProcessError as e:
        print(f"{e.__class__.__name__}, код {e.returncode}:\n{e.stderr}\n{e.output}\n{e.stdout}")
        raise

    except RuntimeError as e:
        print(f"{e.__class__.__name__}, ошибка во время выполнения скрипта")
        raise

    except OSError as e:
        print(f"{e.__class__.__name__}, код {e.errno}\nОшибка {e.strerror}")
        raise

    else:
        print(f"Для всех файлов в директории {root.as_posix()} успешно создана документация")


if __name__ == '__main__':
    run_pyment_command("../")
