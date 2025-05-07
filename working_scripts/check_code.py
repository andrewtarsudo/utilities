# -*- coding: utf-8 -*-

def check_code_command():
    from pathlib import Path
    from subprocess import CompletedProcess, run
    from sys import exit

    path: Path = Path.cwd()
    print("Поиск неиспользуемого кода")

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

        vulture_output: Path = path.joinpath("vulture.txt")
        vulture_output.touch(exist_ok=True)

        with open(vulture_output, "w", encoding="utf-8", errors="ignore") as f:
            f.write(str(result.stdout))

        if result.stderr:
            print(f"Ошибки:\n{str(result.stderr)}")

    except Exception as e:
        print(f"Ошибка запуска vulture: {str(e)}")
        exit(1)


if __name__ == '__main__':
    check_code_command()
