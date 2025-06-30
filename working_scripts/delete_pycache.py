# -*- coding: utf-8 -*-
from os import chdir
from pathlib import Path


def delete_pycache_command(root: str | Path = None):
    from shutil import rmtree

    if root is None:
        root: Path = Path.cwd().resolve()

    else:
        root: Path = Path(root).expanduser().resolve()

    chdir(root)
    print(f"root = {root}")

    deleted_dirs: list[Path] = []

    for pycache in root.rglob("__pycache__"):
        deleted_dirs.append(pycache.expanduser().resolve())
        rmtree(pycache, ignore_errors=True)

    print("Все __pycache__ удалены")
    print("\n".join(map(str, deleted_dirs)))


if __name__ == '__main__':
    delete_pycache_command("../")
