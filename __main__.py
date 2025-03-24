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

    from sys import stdout

    try:
        from shellingham import detect_shell, ShellDetectionFailure

        shell, _ = detect_shell()

    except RuntimeError or ShellDetectionFailure:
        shell = None

    if shell in ("powershell", "pwsh") or shell is None:
        stdout.reconfigure(encoding="cp1251")

    else:
        stdout.reconfigure(encoding="utf-8")

    from utilities.scripts.cli import cli

    cli()

    if faulthandler.is_enabled():
        faulthandler.disable()
