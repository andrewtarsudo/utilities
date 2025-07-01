# -*- coding: utf-8 -*-
from os import chdir
from pathlib import Path

from working_scripts.delete_pycache import delete_pycache_command
# from working_scripts.make_readme import make_readme_command
from working_scripts.run_flake8 import run_flake8_command
from working_scripts.run_pyinstaller import run_pyinstaller_command
# from working_scripts.run_pyment import run_pyment_command
from working_scripts.run_vulture import run_vulture_command

if __name__ == '__main__':
    root: Path = Path(__file__).parent.parent
    chdir(root)

    delete_pycache_command(".")
    run_vulture_command(".")
    run_flake8_command(".")
    # make_readme_command(".")
    # run_pyment_command(".")
    run_pyinstaller_command(".")
