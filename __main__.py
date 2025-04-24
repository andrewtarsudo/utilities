# -*- coding: utf-8 -*-


if __name__ == '__main__':
    from sys import hexversion

    if hexversion < 0x30900f0:
        from sys import version
        from utilities.common.errors import InvalidPythonVersion

        print(
            f"Текущая версия Python {version} слишком стара. "
            f"Необходимо обновить или использовать более новую версию")
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

    cli()

    if faulthandler.is_enabled():
        faulthandler.disable()
