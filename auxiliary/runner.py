# -*- coding: utf-8 -*-
from pathlib import Path
from subprocess import CompletedProcess, run


if __name__ == '__main__':
    Path(old_file).unlink(missing_ok=True)
    old_file: Path = Path(new_file).rename(old_file)
    output: CompletedProcess = run([f"{old_file}", "--version"], shell=shell, capture_output=True, check=True)
    print(output.stdout.decode())
    print("Файл обновлен")
    exit(0)