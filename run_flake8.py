# -*- coding: utf-8 -*-
from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess, run

if __name__ == "__main__":
    output_file: str = "flake8.txt"
    file: Path = Path(output_file)
    file.unlink(missing_ok=True)
    file.touch(exist_ok=True)

    flake8: list[str] = [
        "flake8",
        "--color=auto",
        f"--output-file={output_file}",
        "--verbose",
        "--benchmark",
        "--exit-zero",
        "__main__.py",
        "utilities/**/*.py"
    ]

    try:
        _: CompletedProcess = run(
            flake8,
            encoding="utf-8",
            shell=True,
            capture_output=True,
            check=True)

        _.check_returncode()

    except CalledProcessError as e:
        print(f"{e.__class__.__name__}, код {e.returncode}:\n{str(e)}")
        raise

    except PermissionError as e:
        print(f"{e.__class__.__name__}, недостаточно прав доступа к файлу. {e.strerror}.")
        raise

    except RuntimeError as e:
        print(f"{e.__class__.__name__}, ошибка во время выполнения скрипта")
        raise

    except OSError as e:
        print(f"{e.__class__.__name__}, код {e.errno}\nОшибка {e.strerror}")
        raise

    else:
        print(f"Итоговый файл {output_file} записан")
