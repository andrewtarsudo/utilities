from click.core import Context

from utilities.common.shared import StrPath

POWERSHELL_EXE: str
ENV_VAR: str
SET_ENV_PS: str

def set_env(*, timeout: float | None = 15.0): ...


def convert_value(value: int | str | bool): ...


def compare_versions(project_id: int): ...


def update_exe(ctx: Context, exe_file_name: str, project_id: int, **kwargs): ...


def activate_runner(ctx: Context, *, executable_file: StrPath, exe_file_name: str): ...


def check_updates(ctx: Context, **kwargs): ...
