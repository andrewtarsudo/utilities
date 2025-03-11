# -*- coding: utf-8 -*-
import shellingham

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

    print(shellingham.detect_shell())

    stdout.reconfigure(encoding="utf-8")

    from utilities.scripts.cli import command_line_interface

    command_line_interface()

    if faulthandler.is_enabled():
        faulthandler.disable()
