# -*- coding: utf-8 -*-

if __name__ == '__main__':
    from pathlib import Path
    from subprocess import CompletedProcess, run, CalledProcessError

    old_file: str = r"/Users/andrewtarasov/PycharmProjects/utilities/bin/tw_utilities"
    new_file: str = r"/Users/andrewtarasov/PycharmProjects/utilities/_temp/bin/tw_utilities"
    shell: bool = False

#    Path(old_file).unlink(missing_ok=True)
#    old_file: Path = Path(new_file).rename(old_file)

    try:
        run(["chmod", "+x", f"{old_file}"], shell=False, capture_output=True, check=True)
        output: CompletedProcess = run([f"{old_file}", "--version"], shell=False, capture_output=True, check=True)

    except CalledProcessError as e:
        print(f"{e.__class__.__name__}, {e.returncode}: {e.stderr}")
        raise

    print(f"Файл {new_file} --> {old_file} обновлен")
    exit(0)
