# -*- coding: utf-8 -*-
from functools import cached_property
from pathlib import Path
from string import Template
from textwrap import dedent
from typing import Any, Iterable, Literal, Mapping, NamedTuple, Type

from click.core import Argument, Command, Context, Group, Option, Parameter
from click.termui import unstyle

from utilities.common.functions import file_reader, file_reader_type, file_writer
from utilities.common.shared import StrPath
from utilities.scripts.args_help_dict import args_help_dict
from utilities.scripts.cli import cli

Attrs: Type[str] = Literal["description", "purpose", "admonitions", "others"]


def separate_flag_options(command_name: str, options: Iterable[str] = None) -> tuple[str | None, str | None]:
    short: str | None = None
    full: str | None = None

    if options is None:
        options: list[str] = []

    for option in options:
        if option.startswith("--"):
            full: str = option.removeprefix("--")

        elif option.startswith("-"):
            short: str = option.removeprefix("-")

        else:
            print(f"Неожидаемый флаг {option} для опции {options} в команде {command_name}")
            exit(1)

    return short, full


def bound_string(line: str, prefix: str = "", postfix: str = ""):
    return "\n".join((prefix, "\n", line, "\n", postfix))


def convert_type(param: Parameter):
    type_map: dict[str, str] = {
        "Path": "str",
        "StringParamType": "str",
        "BoolParamType": "bool",
        "IntParamType": "int",
        "FloatParamType": "float",
        "Choice": "str"}

    type_name: str = type(param.type).__name__
    param_type: str = type_map.get(type_name, type_name)

    if param.multiple:
        param_type: str = f"[{param_type}]"

    return param_type


class ReadmeArgument(NamedTuple):
    arg_name: str
    arg_description: str
    arg_type: str

    @classmethod
    def from_argument(cls, argument: Argument, command_name: str):
        arg_name: str = argument.name
        arg_type: str = convert_type(argument)
        arg_description: str = args_help_dict.get_multiple_keys(keys=(command_name,)).get(arg_name)

        return cls(arg_name, arg_description, arg_type)

    def __str__(self):
        return (
            f"\n|{self.arg_name}"
            f"\n|{self.arg_description}"
            f"\n|{self.arg_type}")


class ReadmeOption(NamedTuple):
    short_flag: str
    full_flag: str
    short_counter_flag: str | None
    full_counter_flag: str | None
    option_description: str
    option_type: str

    @property
    def flags(self):
        return f"-{self.short_flag}/--{self.full_flag}"

    @property
    def counter_flags(self):
        if self.short_counter_flag is None and self.full_counter_flag is None:
            return "MISSING"

        if self.short_counter_flag is None:
            short: str = ""

        else:
            short: str = f"-{self.short_counter_flag}"

        if self.full_counter_flag is None:
            full: str = ""

        else:
            full: str = f"--{self.full_counter_flag}"

        return f"{short}/{full}"

    @classmethod
    def from_option(cls, option: Option, command_name: str):
        short_flag, full_flag = separate_flag_options(
            command_name,
            option.opts)

        if option.is_bool_flag and option.secondary_opts:
            short_counter_flag, full_counter_flag = separate_flag_options(
                command_name,
                option.secondary_opts)

        else:
            short_counter_flag, full_counter_flag = None, None

        option_type: str = convert_type(option)
        option_description: str = (
            unstyle(option.help)
            .removesuffix("\n")
            .replace("\b\n", "")
            .replace("\n", " +\n"))

        return cls(
            short_flag,
            full_flag,
            short_counter_flag,
            full_counter_flag,
            option_description,
            option_type)

    def __str__(self):
        return (
            f"\n|{self.flags}"
            f"\n|{self.counter_flags}"
            f"\n|{self.option_description}"
            f"\n|{self.option_type}")


class ReadmeCommand:
    def __init__(self, command: Command):
        self._command: Command = command
        self._readme_arguments: list[ReadmeArgument] = []
        self._readme_options: list[ReadmeOption] = []

    @property
    def command_name(self):
        return self._command.name

    def __add__(self, other):
        if isinstance(other, ReadmeArgument):
            self._readme_arguments.append(other)

        elif isinstance(other, ReadmeOption):
            self._readme_options.append(other)

        else:
            print(
                f"Некорректный тип: должен быть ReadmeArgument или ReadmeOption, "
                f"но получен {type(other).__name__}")
            exit(1)

    def prepare(self):
        for param in self._command.params:
            if isinstance(param, Argument):
                doc_argument: ReadmeArgument = ReadmeArgument.from_argument(param, self.command_name)
                self + doc_argument

            elif isinstance(param, Option):
                doc_option: ReadmeOption = ReadmeOption.from_option(param, self.command_name)
                self + doc_option

            else:
                continue

    @property
    def arguments(self):
        if not self._readme_arguments:
            return ""

        else:
            prefix: str = dedent(
                """\
                \n
                .Описание аргументов
                [options="header",width="100%"]
                |===
                |Название |Описание |Тип\n
                """)
            postfix: str = "\n|===\n\n"
            line: str = "\n\n".join(*self._readme_arguments, )

            return bound_string(line, prefix, postfix)

    @property
    def options(self):
        if not self._readme_options:
            return ""

        prefix: str = dedent(
            """\
            .Описание опций
            [options="header",width="100%"]
            |===
            |Флаги |Обратные |Описание |Тип\n\n
            """)
        postfix: str = "\n|===\n"
        line: str = "\n".join(map(str, self._readme_options))

        return bound_string(line, prefix, postfix)

    def get_subs(self, ctx: Context):
        command_name: str = self.command_name
        help_text: str = unstyle(self._command.get_help(ctx))
        arguments: str = self.arguments
        options: str = self.options

        kwargs: dict[str, str] = {
            "command_name": command_name,
            "help_text": help_text,
            "arguments": arguments,
            "options": options}

        return kwargs


class ReadmeFileGenerator:
    def __init__(
            self,
            group: Group,
            *,
            base_readme: StrPath = None,
            readme_dir: StrPath = None,
            readme_config_file: StrPath = None):
        if base_readme is None:
            base_readme: Path = Path.cwd().joinpath("working_scripts/src/README_base_file.txt")

        else:
            base_readme: Path = Path(base_readme)

        if readme_dir is None:
            readme_dir: Path = Path.cwd().joinpath("docs")

        else:
            readme_dir: Path = Path(readme_dir)

        if readme_config_file is None:
            readme_config_file: Path = Path.cwd().joinpath("working_scripts/src/config_readme.yaml")

        else:
            readme_config_file: Path = Path(readme_config_file)

        self._group: Group = group
        self._base_readme: Path = base_readme
        self._readme_dir: Path = readme_dir
        self._readme_config_file: Path = readme_config_file

    @cached_property
    def template(self) -> Template:
        return Template(file_reader(self._base_readme, "string"))

    @cached_property
    def doc_config(self) -> dict[str, Any]:
        return file_reader_type(self._readme_config_file, "yaml")

    @cached_property
    def attributes(self) -> str:
        return self.doc_config.get("attributes")

    def get_command_attr_config(self, command: Command, attr: Attrs):
        value: str | list[str] | None = self.doc_config.get(command.name).get(attr)

        if value is None:
            return ""

        elif isinstance(value, list):
            return "\n\n".join(value).removesuffix("\n")

        else:
            return value.removesuffix("\n")

    def get_readme_file_subs(self, command: Command):
        attributes: str = self.attributes
        description: str = self.get_command_attr_config(command, "description")
        purpose: str = self.get_command_attr_config(command, "purpose")
        admonitions: str = self.get_command_attr_config(command, "admonitions")
        others: str = self.get_command_attr_config(command, "others")

        kwargs: dict[str, str] = {
            "attributes": attributes,
            "description": description,
            "purpose": purpose,
            "admonitions": admonitions,
            "others": others}

        return kwargs

    def generate_readme_file(self, command_name: str) -> Path:
        _: str = command_name.replace("-", "_")
        doc_file: Path = self._readme_dir.joinpath(f"README_{_}.adoc")
        doc_file.touch(exist_ok=True)

        return doc_file

    def write_readme_file(self, path: StrPath, kwargs: Mapping[str, Any]):
        content: str = self.template.safe_substitute(kwargs)
        file_writer(path, content)

    def generate_readme_files(self):
        parent: Context = Context(self._group, info_name="cli", color=False)

        for command_name, command in self._group.commands.items():
            ctx: Context = Context(command, parent=parent, info_name=command_name, color=False)

            path: Path = self.generate_readme_file(command_name)

            readme_command: ReadmeCommand = ReadmeCommand(command)
            readme_command.prepare()

            kwargs: dict[str, Any] = {
                **self.get_readme_file_subs(command),
                **readme_command.get_subs(ctx)}

            self.write_readme_file(path, kwargs)

            print(f"Записан файл {path.parent}/{path.name} для команды {command_name}")

        print("Генерация документации завершена")


def make_readme_command(
        base_readme: StrPath = None,
        readme_dir: StrPath = None,
        readme_config_file: StrPath = None):
    readme_file_generator: ReadmeFileGenerator = ReadmeFileGenerator(
        cli,
        base_readme=base_readme,
        readme_dir=readme_dir,
        readme_config_file=readme_config_file)
    readme_file_generator.generate_readme_files()


if __name__ == '__main__':
    make_readme_command(
        "src/README_base_file.txt",
        "../docs",
        "src/config_readme.yaml")
