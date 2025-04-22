# -*- coding: utf-8 -*-
from io import TextIOWrapper

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

    from sys import stdout

    try:
        from shellingham import detect_shell, ShellDetectionFailure

        shell, _ = detect_shell()

    except (RuntimeError, ShellDetectionFailure):
        shell = None

    encoding: str = "cp1251" if shell in ("powershell", "pwsh") or shell is None else "utf-8"

    if isinstance(stdout, TextIOWrapper):
        stdout.reconfigure(encoding=encoding)

    from utilities.scripts.cli import cli

    cli()

    if faulthandler.is_enabled():
        faulthandler.disable()
