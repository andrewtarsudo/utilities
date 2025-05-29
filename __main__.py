# -*- coding: utf-8 -*-
from utilities.common.shared import PRESS_ENTER_KEY

if __name__ == '__main__':
    from sys import hexversion

    if hexversion < 0x30900f0:
        from sys import version
        from utilities.common.errors import InvalidPythonVersion

        print(
            f"Текущая версия Python {version} слишком стара. "
            "Необходимо обновить или использовать более новую версию")
        raise InvalidPythonVersion

    import faulthandler

    if not faulthandler.is_enabled():
        faulthandler.enable()

    from io import TextIOWrapper
    from sys import stdout
    from utilities.common.functions import get_shell

    shell: str = get_shell()

    encoding: str = "cp1251" if shell in ("powershell", "pwsh") else "utf-8"

    if isinstance(stdout, TextIOWrapper):
        stdout.reconfigure(encoding=encoding)

    from utilities.scripts.cli import cli

    try:
        cli()

    except Exception as e:
        from click.termui import echo, pause
        from sys import exit

        echo(f"Ошибка {e.__class__.__name__}, {e!s}")
        pause(PRESS_ENTER_KEY)
        exit(1)

    if faulthandler.is_enabled():
        faulthandler.disable()
