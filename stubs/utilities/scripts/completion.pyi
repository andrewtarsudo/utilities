# -*- coding: utf-8 -*-
from click.core import Context, Parameter


def file_completion(ctx: Context, parameter: Parameter, incomplete: str): ...


def dir_completion(ctx: Context, parameter: Parameter, incomplete: str): ...


def doc_completion(ctx: Context, parameter: Parameter, incomplete: str): ...
