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

    stdout.reconfigure(encoding="utf-8")

    # from utilities.scripts.cli import command_line_interface
    from utilities.scripts.main import main

    app = main()
    app()

    if faulthandler.is_enabled():
        faulthandler.disable()
