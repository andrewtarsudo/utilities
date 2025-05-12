# -*- coding: utf-8 -*-

if __name__ == '__main__':
    from check_code import check_code_command
    from delete_pycache import delete_pycache_command
    from generate_executable import generate_executable_command
    from run_flake8 import run_flake8_command

    delete_pycache_command()
    check_code_command()
    run_flake8_command()
    generate_executable_command()
