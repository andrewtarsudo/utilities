# -*- coding: utf-8 -*-

def delete_pycache_command():
    from pathlib import Path
    from shutil import rmtree

    for pycache in Path(__file__).parent.rglob("__pycache__"):
        rmtree(pycache, ignore_errors=True)

    print("Все __pycache__ удалены")


if __name__ == '__main__':
    delete_pycache_command()
