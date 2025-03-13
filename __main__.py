# -*- coding: utf-8 -*-
import faulthandler
from sys import hexversion, stdout

from shellingham import detect_shell, ShellDetectionFailure

from utilities.scripts.main import main

if __name__ == '__main__':
    if hexversion < 0x30900f0:
        from sys import version
        from utilities.common.errors import InvalidPythonVersion

        print(
            f"Текущая версия Python {version} слишком стара. "
            f"Необходимо обновить или использовать более новую версию")
        raise InvalidPythonVersion

    if not faulthandler.is_enabled():
        faulthandler.enable()

    try:
        shell, _ = detect_shell()

    except ShellDetectionFailure:
        shell = None

    if shell in ("powershell", "pwsh") or shell is None:
        stdout.reconfigure(encoding="cp1251")

    else:
        stdout.reconfigure(encoding="utf-8")

    main()

    if faulthandler.is_enabled():
        faulthandler.disable()
