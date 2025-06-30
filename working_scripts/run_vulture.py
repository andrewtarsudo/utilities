# -*- coding: utf-8 -*-
from pathlib import Path


def run_vulture_command(root: str | Path = None):
    from os import chdir
    from subprocess import CompletedProcess, run
    from sys import exit

    if root is None:
        root: Path = Path.cwd().resolve()

    else:
        root: Path = Path(root).expanduser().resolve()

    print("Поиск неиспользуемого кода")
    chdir(root)
    print(f"root = {root}")

    try:
        vulture: list[str] = [
            "vulture",
            "--config=pyproject.toml",
            "./utilities/",
            "./__main__.py"]

        result: CompletedProcess = run(
            vulture,
            capture_output=True,
            text=True)

        vulture_output: Path = root.joinpath("vulture.txt").resolve()
        vulture_output.touch(exist_ok=True)

        with open(vulture_output, "w", encoding="utf-8", errors="ignore") as f:
            f.write(str(result.stdout))

        print(f"Отчет записан в файл {vulture_output.as_posix()}")

        if result.stderr:
            print(f"Ошибки:\n{str(result.stderr)}")

    except Exception as e:
        print(f"Ошибка запуска vulture: {str(e)}")
        exit(1)


if __name__ == '__main__':
    run_vulture_command("../")
