# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Any, NamedTuple

from click.core import Context
from click.decorators import argument, help_option, option, pass_context
from click.types import BOOL, Path as ClickPath, STRING, Choice
# noinspection PyProtectedMember
from frontmatter import load, Post
from loguru import logger
from yaml import dump

from utilities.common.config_file import config_file
from utilities.common.errors import GenerateYamlMissingAttributeError, GenerateYamlMissingBranchError, GenerateYamlMissingIndexFileError
from utilities.common.functions import pretty_print
from utilities.common.shared import HELP, StrPath
from utilities.scripts.api_group import SwitchArgsAPIGroup
from utilities.scripts.cli import cli
from utilities.scripts.completion import dir_completion, language_completion

EPILOG_GENERATE_YAML: str = (
    "\b\nЗначения атрибутов AsciiDoc по умолчанию, добавляемые в файл:"
    "\n:doctype: book"
    "\n:outlinelevels: 4"
    "\n:sectnumlevels: 4"
    "\n:toclevels: 3"
    "\n:toc: true"
    "\n:chapter-signifier!:"
    "\n"
    "\nfigure-caption: Рисунок/Figure"
    "\n:table-caption: Таблица/Table"
    "\n:toc-title: Содержание/Contents"
    "\n:title-logo-image: images/logo<_en>.svg[top=4%,align=right,pdfwidth=3cm]"
    "\n"
    "\b\nДопускается добавлять любые атрибуты, в том числе и пользовательские.")


class Frontmatter(NamedTuple):
    """Structured representation of the file frontmatter metadata."""
    weight: int
    title: str
    filename: str
    path: str
    draft: bool = False

    @classmethod
    def parse_frontmatter(cls, filepath: StrPath, root: StrPath):
        try:
            post: Post = load(str(filepath))

            if not post.metadata or post.get("draft", False):
                return None

            filepath: Path = Path(filepath)
            weight: int = int(str(post.get("weight")))
            title: str = str(post.get("title"))
            filename: str = filepath.relative_to(root).as_posix()
            path: str = filepath.as_posix()
            draft: bool = bool(post.get("draft", False))

            return cls(weight, title, filename, path, draft)

        except OSError:
            logger.info(f"В файле {filepath} отсутствует frontmatter")
            return None

    def __str__(self):
        return pretty_print([f"{k} = {v}" for k, v in self._asdict().items()])


class Branch:
    """Represents a directory branch in the tree."""
    root: Path

    def __init__(self, path: Path) -> None:
        self._path: Path = path
        self._index: list[str] = []
        self._title: dict[str, int | str] = {}
        self._files: list[str] = []
        self._subdirs: dict[str, Branch] = {}
        self._weight: int | None = None

    @property
    def relpath(self):
        return self._path.relative_to(self.__class__.root).as_posix()

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}

        if self._index:
            result["index"] = self._index

        if self._title:
            result["title"] = self._title

        if self._files:
            result["files"] = sorted(self._files)

        if self._subdirs:
            # Sort subdirs by weight (None last), then by name
            sorted_subdirs = sorted(
                self._subdirs.items(),
                key=lambda item: (
                    -1 if item[1].weight is None else item[1].weight,
                    item[0].lower()))
            result["subdirs"] = {k: v.to_dict() for k, v in sorted_subdirs}

        return result

    def __str__(self):
        lines: list[str] = [f"{self.__class__.__name__}: {self._path}"]
        lines.extend([f"{k} = {v}" for k, v in self.to_dict().items()])
        return pretty_print(lines)

    def flatten(self) -> dict[str, dict[str, Any]]:
        """Flatten the branch structure for YAML output"""
        flat: dict[str, dict[str, Any]] = {}

        if self._index or self._files or self._title:
            flat[self.relpath] = {}

            if self._index:
                flat[self.relpath]["index"] = self._index

            if self._files:
                flat[self.relpath]["files"] = self._files

            if self._title:
                flat[self.relpath]["title"] = self._title

        # Sort subdirs by weight before flattening
        for subdir in sorted(
                self._subdirs.values(),
                key=lambda b: (
                        -1 if b.weight is None else b.weight,
                        b.path.name.lower())):
            flat.update(subdir.flatten())

        return flat

    @property
    def path(self):
        return self._path

    @property
    def title(self):
        return self._title

    @property
    def files(self):
        return self._files

    @property
    def index(self):
        return self._index

    @property
    def subdirs(self):
        return self._subdirs

    @property
    def weight(self):
        return self._weight


class Tree:
    language: str
    """Represents the complete directory tree"""

    def __init__(self, root: Path) -> None:
        self.root: Path = root
        self.branches: dict[str, Branch] = {}

    def get_directory_weight(self, dirpath: StrPath, branch: Branch) -> Branch | None:
        try:
            filepath: Path = find_index(dirpath, self.__class__.language)

        except GenerateYamlMissingIndexFileError:
            raise GenerateYamlMissingBranchError

        else:
            front_matter: Frontmatter | None = Frontmatter.parse_frontmatter(filepath, self.root)

            if front_matter:
                branch._weight = front_matter.weight

                if has_content(filepath):
                    branch.index.append(front_matter.filename)

                else:
                    branch.title["value"] = front_matter.title

                level: int = len(Path(branch.relpath).parts) + 1
                branch.title["level"] = level

            return branch

    def process_files(self, dirpath: StrPath, branch: Branch | None) -> Branch | None:
        if branch is None:
            logger.debug(f"В директории {dirpath} отсутствует файл index.*/_index.*")
            raise GenerateYamlMissingBranchError

        for filepath in dirpath.iterdir():
            if not filepath.is_file():
                continue

            if not is_valid_file(filepath, self.__class__.language):
                continue

            if filepath.stem in ("_index", "index"):
                continue

            front_matter: Frontmatter = Frontmatter.parse_frontmatter(filepath, self.root)

            if front_matter:
                branch.files.append(front_matter.filename)

        # Sort files by weight then title
        branch.files.sort(
            key=lambda x: (
                (Frontmatter.parse_frontmatter(self.root.joinpath(x), self.root)).weight,
                (Frontmatter.parse_frontmatter(self.root.joinpath(x), self.root)).title.lower()))

        return branch

    def process_subdirectories(self, dirpath: StrPath, branch: Branch | None) -> Branch | None:
        if branch is None:
            raise GenerateYamlMissingBranchError

        dirpath: Path = Path(dirpath)
        subdirs: list[Path] = sorted(dirpath.iterdir())  # First sort by name for consistent processing

        for subdir in subdirs:
            if subdir.is_dir():
                sub_branch: Branch | None = self.generate_branch(subdir)

                if sub_branch:
                    branch.subdirs[sub_branch.path.name] = sub_branch

        return branch

    def generate_branch(self, dirpath: StrPath, branch: Branch | None = None) -> Branch | None:
        if branch is None:
            branch: Branch = Branch(dirpath)

        try:
            branch = self.get_directory_weight(dirpath, branch)
            branch = self.process_files(dirpath, branch)
            branch = self.process_subdirectories(dirpath, branch)

            if branch.index or branch.files or branch.subdirs:
                return branch

            else:
                return None

        except GenerateYamlMissingBranchError:
            return None

    # def process_directory(self, dirpath: Path) -> Branch | None:
    #     """Process a directory and return its Branch"""
    #     branch: Branch = Branch(dirpath)
    #     language: str = self.__class__.language
    #
    #     # Check for index files to get directory weight
    #     try:
    #         filepath: Path = find_index(dirpath, language)
    #
    #     except GenerateYamlMissingIndexFileError:
    #         return
    #
    #     front_matter: Frontmatter | None = Frontmatter.parse_frontmatter(filepath, self.root)
    #
    #     if front_matter:
    #         branch._weight = front_matter.weight
    #
    #         if has_content(filepath):
    #             branch.index.append(front_matter.filename)
    #
    #         else:
    #             branch.title["value"] = front_matter.title
    #
    #         level: int = len(Path(branch.relpath).parts) + 1
    #         branch.title["level"] = level
    #
    #     # Process files
    #     for filepath in dirpath.iterdir():
    #         if not filepath.is_file():
    #             continue
    #
    #         if not is_valid_file(filepath, language):
    #             continue
    #
    #         if filepath.stem in ("_index", "index"):
    #             continue
    #
    #         front_matter: Frontmatter = Frontmatter.parse_frontmatter(filepath, self.root)
    #
    #         if front_matter:
    #             branch.files.append(front_matter.filename)
    #
    #     # Sort files by weight then title
    #     branch.files.sort(
    #         key=lambda x: (
    #             (Frontmatter.parse_frontmatter(self.root.joinpath(x), self.root)).weight,
    #             (Frontmatter.parse_frontmatter(self.root.joinpath(x), self.root)).title.lower()))
    #
    #     # Process subdirectories
    #     subdirs: list[Path] = sorted(dirpath.iterdir())  # First sort by name for consistent processing
    #
    #     for subdir in subdirs:
    #         if subdir.is_dir():
    #             sub_branch: Branch | None = self.process_directory(subdir)
    #
    #             if sub_branch:
    #                 branch.subdirs[sub_branch.path.name] = sub_branch
    #
    #     # Only keep branches with content
    #     if branch.index or branch.files or branch.subdirs:
    #         return branch
    #
    #     else:
    #         return None

    def build(self) -> None:
        """Build the complete tree structure"""
        root_branch: Branch | None = self.generate_branch(self.root)

        if root_branch:
            self.branches = root_branch.subdirs

    def to_yaml(self) -> dict[str, dict[str, Any]]:
        """Save the flattened tree structure to YAML"""
        root_branch: Branch = Branch(self.root)
        root_branch.subdirs.update(self.branches)

        return root_branch.flatten()


class YAMLConfig(NamedTuple):
    language: str
    root: StrPath
    settings: dict[str, str | int | bool] = {}
    rights: dict[str, list[str] | dict[str, str | bool]] = {}
    subdirs: dict[str, dict[str, Any]] = {}

    def set_settings(self, **kwargs):
        if "title-page" not in kwargs or "version" not in kwargs:
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

        main_attributes: dict[str, str | int | bool] = {
            "doctype": "book",
            "outlinelevels": kwargs.get("outlinelevels", 4),
            "sectnumlevels": kwargs.get("sectnumlevels", 4),
            "toclevels": kwargs.get("toclevels", 3),
            "toc": kwargs.get("toc", True),
            "chapter-signifier": kwargs.get("chapter-signifier", False),
            "title-page": kwargs.get("title-page"),
            "version": kwargs.get("version")
        }

        settings: dict[str, str | int | bool] = {k.replace("_", "-"): v for k, v in kwargs.items()}
        settings.update(lang_attributes)
        settings.update(main_attributes)

        self.settings.update(settings)

    def set_legal_info(self):
        if self.language == "ru":
            value: str = "Юридическая информация"

        else:
            value: str = "Legal Information"

        index_file: str = find_index(self.root.joinpath("content/common"), self.language).as_posix()
        title_files: bool = False

        rights: dict[str, list[str] | dict[str, str | bool]] = {
            "index": [index_file],
            "title": {
                "value": value,
                "title-files": title_files
            }
        }

        self.rights.update(rights)

    def write(self, output: StrPath):
        kwargs: dict[str, Any] = {
            "settings": self.settings,
            "rights": self.rights,
            **self.subdirs}

        with open(output, "w", encoding="utf-8", errors="ignore") as f:
            dump(kwargs, f, indent=2, allow_unicode=True, sort_keys=False)


def has_content(filepath: StrPath) -> bool:
    try:
        post: Post = load(str(filepath))
        return bool(post.content.strip())

    except OSError:
        return False


def is_valid_file(filepath: Path, language: str) -> bool:
    if language == "ru":
        is_language: bool = filepath.suffixes[0] in (".md", ".adoc")

    else:
        is_language: bool = filepath.suffixes[0] == language

    return filepath.suffix in (".md", ".adoc") and is_language


def find_index(directory: StrPath, language: str):
    directory: Path = Path(directory)

    if language == "ru":
        files: list[str] = [
            "_index.md",
            "_index.adoc",
            "index.md",
            "index.adoc"]

    else:
        files: list[str] = [
            f"_index.{language}.md",
            f"_index.{language}.adoc",
            f"index.{language}.md",
            f"index.{language}.adoc"]

    for file in files:
        index_file: Path = directory.joinpath(file)

        if index_file.exists():
            return index_file

    else:
        logger.debug(f"В директории {directory} не найдены файлы index.*/_index.*")
        raise GenerateYamlMissingIndexFileError


def prepare_title(title: str):
    return title.replace(" ", "_")


@cli.command(
    "generate-yaml",
    cls=SwitchArgsAPIGroup,
    help="Команда для генерации YAML-файла, используемого при сборке PDF",
    epilog=EPILOG_GENERATE_YAML)
@argument(
    "project",
    type=ClickPath(
        exists=True,
        file_okay=False,
        allow_dash=False,
        dir_okay=True),
    required=True,
    shell_complete=dir_completion)
@option(
    "-l", "--language", "language",
    type=Choice(["ru", "en", "fr"]),
    help="\b\nИспользуемый язык в файлах",
    nargs=1,
    required=True,
    metavar="LANG",
    shell_complete=language_completion,
    show_choices=True)
@option(
    "-t", "--title-page",
    type=STRING,
    help="\b\nНазвание продукта, отображаемое на титульном листе",
    required=True,
    nargs=1,
    metavar="TITLE")
@option(
    "-v", "--version",
    type=STRING,
    help="\b\nНомер версии продукта",
    nargs=1,
    metavar="VERSION",
    required=True)
@option(
    "-a", "--args", "args",
    type=tuple[str, ...],
    help="\b\nДополнительные параметры AsciiDoc, добавляемые "
         "\nк файлу, или изменяющие значения по умолчанию."
         "\nПо умолчанию: null",
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
        project: str,
        language: str,
        title_page: str,
        version: str,
        args: tuple[str, ...] = None,
        keep_logs: bool = False):
    kwargs: dict[str, str] = {
        "language": language,
        "title-page": title_page,
        "version": version}

    if args is None:
        args: list[str] = []

    else:
        args: list[str] = [*args]

    attrs: dict[str, Any] = {
        attribute.split("=", 1)[0]: attribute.split("=", 1)[1]
        for attribute in args}

    kwargs.update(**attrs)

    project: Path = Path(project)
    Branch.root = project
    Tree.language = language

    tree: Tree = Tree(project.joinpath("content/common/"))
    tree.build()

    yaml_config: YAMLConfig = YAMLConfig(language, project)
    yaml_config.set_settings(**kwargs)
    yaml_config.set_legal_info()
    yaml_config.subdirs.update(**tree.to_yaml())

    output: str = f"PDF_{prepare_title(title_page)}.yml"

    yaml_config.write(output)

    ctx.obj["keep_logs"] = keep_logs
