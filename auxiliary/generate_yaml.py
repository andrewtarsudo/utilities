# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Any, ClassVar, Mapping, NamedTuple, Self

from click import argument, BOOL, Choice, Context, help_option, option, pass_context, STRING
# noinspection PyProtectedMember
from frontmatter import load, Post
from loguru import logger

from common.completion import dir_completion, language_completion
from common.config_file import config_file
from common.errors import GenerateYamlMissingAttributeError
from common.shared import HELP, MyYAML
from scripts import cli, SwitchArgsAPIGroup
from utilities.common.shared import EXTENSIONS, StrPath
from click import Path as ClickPath

EPILOG_GENERATE_YAML: str = (
    "\b\nЗначения атрибутов AsciiDoc по умолчанию, добавляемые в файл:"
    "\n:doctype: book"
    "\n:outlinelevels: 4"
    "\n:sectnumlevels: 4"
    "\n:toclevels: 3"
    "\n:toc: true"
    "\n:chapter-signifier!:"
    "\n"
    "\n:figure-caption: Рисунок/Figure"
    "\n:table-caption: Таблица/Table"
    "\n:toc-title: Содержание/Contents"
    "\n:title-logo-image: images/logo<_en>.svg[top=4%,align=right,pdfwidth=3cm]"
    "\n"
    "\b\nДопускается добавлять любые атрибуты, в том числе и пользовательские.")


# noinspection PyTypeChecker
class FrontMatter(NamedTuple):
    title: str
    weight: int
    draft: bool = False

    def __key(self) -> tuple[int, str]:
        return self.weight, self.title

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__key() == other.__key()

        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self.__key() != other.__key()

        else:
            return NotImplemented

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.__key() < other.__key()

        else:
            return NotImplemented

    def __le__(self, other):
        if isinstance(other, self.__class__):
            return self.__key() <= other.__key()

        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, self.__class__):
            return self.__key() > other.__key()

        else:
            return NotImplemented

    def __ge__(self, other):
        if isinstance(other, self.__class__):
            return self.__key() >= other.__key()

        else:
            return NotImplemented

    @classmethod
    def from_dict(cls, __dict: Mapping[str, Any]):
        try:
            title: str = __dict.get("title")
            weight: int = int(__dict.get("weight"))
            draft: bool = __dict.get("draft", False)

            return cls(title, weight, draft)

        except KeyError:
            logger.error(f"Отсутствуют обязательные атрибуты")
            raise

        except ValueError:
            logger.error(f"Значение weight нельзя привести к типу int")


class File:
    def __init__(self, path: StrPath):
        self._path: Path = Path(path)
        self._frontmatter: FrontMatter | None = None
        self._content: str | None = None

    def is_index(self):
        return self._path.name.startswith(("index", "_index"))

    def is_text(self):
        return self._path.suffix in EXTENSIONS

    def set_params(self):
        try:
            post: Post = load(str(self._path))
            fm: FrontMatter = FrontMatter.from_dict(**post.metadata)
            content: str = post.content

            self._frontmatter = fm
            self._content = content

        except (AttributeError, ValueError):
            logger.error("Файл некорректен, поэтому проигнорирован")

    def __bool__(self):
        return self._frontmatter is not None

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._path == other._path

        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self._path != other._path

        else:
            return NotImplemented

    def __lt__(self, other):
        if isinstance(other, self.__class__) and bool(self) and bool(other):
            return self._frontmatter < other._frontmatter

        else:
            return NotImplemented

    def __le__(self, other):
        if isinstance(other, self.__class__) and bool(self) and bool(other):
            return self._frontmatter <= other._frontmatter

        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, self.__class__) and bool(self) and bool(other):
            return self._frontmatter > other._frontmatter

        else:
            return NotImplemented

    def __ge__(self, other):
        if isinstance(other, self.__class__) and bool(self) and bool(other):
            return self._frontmatter >= other._frontmatter

        else:
            return NotImplemented

    def is_empty(self):
        return not self._content

    def relpath(self, root: Path):
        return self._path.relative_to(root)

    @property
    def language(self):
        suffixes: list[str] = self._path.suffixes

        if len(suffixes) > 1:
            return suffixes[0]

        else:
            return "ru"


class BranchDict(dict):
    pass


class BranchParameters(NamedTuple):
    name: str
    title: str | None
    level: int | None
    index: list[str] = []
    files: list[str] = []

    def to_dict(self):
        dict_parameters: dict[str, Any] = {}

        if self.title is not None:
            dict_parameters["title"] = self.title

        if self.level is not None:
            dict_parameters["level"] = self.level

        if self.index:
            dict_parameters["index"] = self.index

        if self.files:
            dict_parameters["files"] = self.files

        return {self.name: dict_parameters}

    def __str__(self):
        my_yaml: MyYAML = MyYAML()
        my_yaml.dump(self.to_dict())


class Branch:
    root: ClassVar[Path]

    branch_dict: BranchDict = BranchDict()

    def __init__(self, path: StrPath):
        self._path = Path(path)
        self._index_file: File | None = None
        self._files: list[File] = []
        self._subs: list[Self] = []
        self._parent: Self = None

        self.__files_inside: list[Path] = []
        self.__dirs_inside: list[Path] = []

        self.__class__.branch_dict[self._path] = self

    def set_inside(self):
        for item in self._path.iterdir():
            if item.is_file() and item.suffix in EXTENSIONS:
                self.__files_inside.append(item)

            elif item.is_dir():
                self.__dirs_inside.append(item)

            else:
                pass

    def set_files(self):
        for file_path in self.__files_inside:
            file: File = File(file_path)
            file.set_params()

            if not bool(file):
                continue

            elif file.is_index():
                self._index_file = file

            else:
                self._files.append(file)

    def set_parent(self):
        if self._path.resolve() != self.__class__.root.resolve():
            self._parent = self._path.parent

    def __len__(self):
        return len(self._files) + int(self._index_file is not None)

    def __bool__(self):
        return self._index_file is not None and not len(self._files)

    @property
    def relpath(self):
        return self._path.relative_to(self.root)

    @property
    def level(self):
        return len(self.relpath.parts)

    def __add__(self, other):
        if isinstance(other, File):
            self._files.append(other)

        elif isinstance(other, self.__class__):
            self._subs.append(other)

        else:
            return NotImplemented

    @property
    def no_index_file(self):
        return self._index_file is None

    def set_subs(self):
        for item in self.__dirs_inside:
            branch: Branch = Branch(item.resolve())
            branch.set_inside()
            branch.set_parent()
            branch.set_files()
            branch.set_subs()

            if branch.no_index_file:
                del self.__class__.branch_dict[branch._path]
                continue

            self + branch

    def to_parameters(self):
        if self._index_file.is_empty():
            title: str | None = ""

        else:
            title: str | None = None

        if self.level > 2:
            level: int | None = self.level

        else:
            level: int | None = None

        if self._index_file is not None:
            index: list[str] = [self._index_file.relpath(self.__class__.root).as_posix()]

        else:
            index: list[str] = []

        if self._files is not None:
            files: list[str] = list(map(lambda x: x.relpath(self.__class__.root), self._files))

        else:
            files: list[str] = []

        name: str = self.relpath.as_posix()

        return BranchParameters(name, title, level, index, files)

    @classmethod
    def get_root(cls) -> Self:
        for path, branch in cls.branch_dict.items():
            if path == cls.root:
                return branch

    @property
    def index_file(self):
        return self._index_file


def generate_branches(path: StrPath | None = None):
    branch: Branch = Branch(path)
    branch.set_inside()
    branch.set_parent()
    branch.set_files()
    branch.set_subs()

    branches: list[Branch] = sorted(Branch.branch_dict.values())
    branch_params: list[BranchParameters] = list(map(lambda x: x.to_params(), branches))

    return list(map(str, branch_params))


def to_str(path: StrPath | None = None):
    generate_branches(path)

    branches: list[Branch] = sorted(Branch.branch_dict.values())

    branch_params: list[BranchParameters] = list(map(lambda x: x.to_params(), branches))
    return "\n".join(map(str, branch_params))


def to_yaml(kwargs: dict[str, Any]) -> str:
    yaml: MyYAML = MyYAML(typ="safe")
    return yaml.dump(kwargs)


class YAMLConfig(NamedTuple):
    language: str
    root: StrPath
    settings: dict[str, str | int | bool] = {}
    rights: dict[str, list[str] | dict[str, str | bool]] = {}
    subdirs: dict[str, dict[str, Any]] = {}

    def set_settings(self, **kwargs) -> None:
        if "title-page" not in kwargs:
            logger.error("Не задан обязательный параметр title-page")
            raise GenerateYamlMissingAttributeError

        if "version" not in kwargs:
            logger.error("Не задан обязательный параметр version")
            raise GenerateYamlMissingAttributeError

        if self.language == "ru":
            lang_attributes: dict[str, str | int | bool] = {
                "figure-caption": "Рисунок",
                "table-caption": "Таблица",
                "toc-title": "Содержание",
                "title-logo-image": "images/logo.svg[top=4%,align=right,pdfwidth=3cm]"}

        else:
            lang_attributes: dict[str, str | int | bool] = {
                "figure-caption": "Figure",
                "table-caption": "Table",
                "toc-title": "Contents",
                "title-logo-image": "images/logo_en.svg[top=4%,align=right,pdfwidth=3cm]"}

        outlinelevels: int = kwargs.get(
            "outlinelevels",
            config_file.get_commands("generate-yaml", "outlinelevels"))

        sectnumlevels: int = kwargs.get(
            "sectnumlevels",
            config_file.get_commands("generate-yaml", "sectnumlevels"))

        toclevels: int = kwargs.get(
            "toclevels",
            config_file.get_commands("generate-yaml", "toclevels"))

        main_attributes: dict[str, str | int | bool] = {
            "doctype": "book",
            "outlinelevels": outlinelevels,
            "sectnumlevels": sectnumlevels,
            "toclevels": toclevels,
            "toc": True,
            "chapter-signifier": False,
            "title-page": kwargs.get("title-page"),
            "version": kwargs.get("version")}

        settings: dict[str, str | int | bool] = {}
        settings.update(lang_attributes)
        settings.update(main_attributes)
        user_kwargs: dict[str, str | int | bool] = {k.replace("_", "-"): v for k, v in kwargs.items()}
        settings.update(user_kwargs)

        self.settings.update(settings)

        logger.debug(f"Раздел settings:\n{to_yaml(self.settings)}")

    def set_legal_info(self) -> None:
        if self.language == "ru":
            value: str = "Юридическая информация"

        else:
            value: str = "Legal Information"

        legal_info_file: Path = self.root.joinpath("content/common")
        branch = Branch(legal_info_file)
        branch.set_files()
        index_file: str = branch.index_file.relpath(self.root).as_posix()
        logger.debug(f"Директория: {legal_info_file}\nФайл index: {index_file}")
        title_files: bool = False

        rights: dict[str, list[str] | dict[str, str | bool]] = {
            "index": [index_file],
            "title": {
                "value": value,
                "title-files": title_files
            }
        }

        self.rights.update(rights)

        logger.debug(f"Раздел rights:\n{to_yaml(self.rights)}")

    # def write(self, output: StrPath, is_execute: bool = True) -> None:
    #     logger.success(f"Конфигурационный файл:\n{str(self)}")
    #
    #     if is_execute:
    #         file_writer(output, str(self))
    #         logger.success(f"Записан файл {Path(output).resolve()}")
    #
    #     else:
    #         logger.warning("Файл не был записан согласно используемым опциям в команде")
    #         echo(str(self))

    def to_dict(self) -> dict[str, Any]:
        return {
            "settings": self.settings,
            "rights": self.rights,
            **self.subdirs}

    def __str__(self) -> str:
        return to_yaml(self.to_dict())


@cli.command(
    "generate-yaml",
    cls=SwitchArgsAPIGroup,
    help="Команда для генерации YAML-файла, используемого при сборке PDF",
    epilog=EPILOG_GENERATE_YAML)
@argument(
    "root",
    type=ClickPath(
        exists=True,
        file_okay=False,
        allow_dash=False,
        dir_okay=True),
    required=True,
    metavar="ROOT",
    shell_complete=dir_completion)
@option(
    "-t", "--title-page",
    type=STRING,
    help="\b\nНазвание продукта, отображаемое на титульном листе",
    required=True,
    nargs=1,
    metavar="<TITLE>")
@option(
    "-v", "--version",
    type=STRING,
    help="\b\nНомер версии продукта",
    nargs=1,
    metavar="<VERSION>",
    required=True)
@option(
    "-d/-D", "--dry-run/--no-dry-run",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг вывода текста на экран без записи в файл "
         "\nв директории проекта."
         "\nПо умолчанию: False, файл создается",
    show_default=True,
    required=False,
    default=config_file.get_commands("generate-yaml", "dry_run"))
@option(
    "-l", "--language", "language",
    type=Choice(
        ["ru", "en", "fr"]
    ),
    help="\b\nЯзык файлов, используемый как постфикс."
         "\nВозможные значения: ru, en, fr."
         "\nПо умолчанию: ru",
    multiple=False,
    required=False,
    metavar="<LANG>",
    shell_complete=language_completion,
    show_choices=True,
    default=config_file.get_commands("generate-yaml", "language"))
@option(
    "-a", "--args", "args",
    type=STRING,
    help="\b\nДополнительные параметры AsciiDoc, добавляемые к файлу, "
         "\nили изменяющие значения по умолчанию."
         "\nПо умолчанию: пусто",
    multiple=True,
    required=False,
    metavar="<KEY>=<VALUE>",
    default=config_file.get_commands("generate-yaml", "args"))
@option(
    "-k/-K", "--keep-logs/--remove-logs",
    type=BOOL,
    is_flag=True,
    help="\b\nФлаг сохранения директории с лог-файлом по завершении"
         "\nработы в штатном режиме."
         "\nПо умолчанию: False, лог-файл и директория удаляются",
    show_default=True,
    required=False,
    default=config_file.get_commands("generate-yaml", "keep_logs"))
@help_option(
    "-h", "--help",
    help=HELP,
    is_eager=True)
@pass_context
def generate_yaml_command(
        ctx: Context,
        root: str,
        title_page: str,
        version: str,
        dry_run: bool = False,
        language: str = "ru",
        args: tuple[str, ...] = None,
        keep_logs: bool = False):
    kwargs: dict[str, str] = {
        "title-page": title_page,
        "version": version}

    if args is not None:
        args: list[str] = [*args]

        kw: dict[str, Any] = {
            attribute.split("=", 1)[0]: attribute.split("=", 1)[1]
            for attribute in args}

        attrs: dict[str, Any] = prepare_attributes(kw)

        kwargs.update(attrs)

    root: Path = Path(root)
    Branch.root = root
    Tree.language = language

    tree: Tree = Tree(root.joinpath("content/common/"))
    tree.build()

    yaml_config: YAMLConfig = YAMLConfig(language, root)
    yaml_config.set_settings(**kwargs)
    yaml_config.set_legal_info()
    yaml_config.subdirs.update(**tree.to_yaml())

    yaml_name: str = title_page.replace(" ", "_")
    output: Path = root.joinpath(f"PDF_{yaml_name}.yml")

    yaml_config.write(output, not dry_run)

    ctx.obj["keep_logs"] = keep_logs
