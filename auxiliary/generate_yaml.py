# -*- coding: utf-8 -*-
from itertools import product
from pathlib import Path
from sys import stdout
from typing import Any, ClassVar, ForwardRef, Iterable, Mapping, NamedTuple, Self

# noinspection PyProtectedMember
from frontmatter import load, Post
from loguru import logger
from yaml import safe_dump

from utilities.common.functions import file_reader
from utilities.common.shared import EXTENSIONS, INDEX_STEMS, StrPath

RecursiveDict = ForwardRef("RecursiveDict")
RecursiveDict.__forward_arg__ = "dict[Path, list[Path | RecursiveDict]]"


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

    def is_index(self):
        return self._path.name.startswith(("index", "_index"))

    def is_text(self):
        return self._path.suffix in EXTENSIONS

    def set_frontmatter(self):
        try:
            post: Post = load(str(self._path))
            fm: FrontMatter = FrontMatter.from_dict(**post.metadata)

            self._frontmatter = fm

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


class BranchDict(dict):
    pass


class Branch:
    root: ClassVar[Path]

    branch_dict: BranchDict = BranchDict()

    def __init__(self, path: StrPath):
        self._path = Path(path)
        self._index_file: File | None = None
        self._files: list[File] = []
        self._subs: list[Self] = []
        self._parent: Self = None

        self.__class__.branch_dict[self._path] = self

    def set_files(self):
        for file_path in filter(lambda x: x.suffix in EXTENSIONS, self._path.iterdir()):
            file: File = File(file_path)
            file.set_frontmatter()

            if file.is_index():
                self._index_file = file

            else:
                self._files.append(file)

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




class WithFrontMatter:
    root: Path

    def __init__(self, path: StrPath):
        self._path: Path = Path(path).expanduser()
        self._front_matter: dict[str, str | int | bool | object] = {}

    def __repr__(self):
        return f"<{self.__class__.__name__}>({str(self)})"

    @property
    def weight(self):
        return int(self._front_matter.get("weight"))

    @property
    def draft(self):
        return self._front_matter.get("draft", False)

    @property
    def front_matter(self):
        return self._front_matter

    @front_matter.setter
    def front_matter(self, value):
        self._front_matter = value

    @property
    def title(self):
        return self._front_matter.get("title")

    @property
    def parent(self):
        return self._path.parent

    def __hash__(self):
        return hash(self._path)

    @property
    def relpath(self):
        return self._path.resolve().relative_to(self.root.resolve()).as_posix()

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


class TextFile(WithFrontMatter):
    def __init__(self, path: StrPath = None):
        if path is None:
            path: Path = self.root.parent.parent.joinpath("README.md")
            front_matter: dict[str, str | int | bool | object] = {"title": None, "weight": 10_000, "draft": True}
            content: str | None = None

        else:
            post: Post = load(path.as_posix(), encoding="utf-8")
            front_matter: dict[str, str | int | bool | object] = post.metadata
            content: str | None = post.content.strip()

        super().__init__(path)

        self._front_matter: dict[str, str | int | bool | object] = front_matter
        self._content: str = content

    def __str__(self):
        return f"title={self.title}, weight={self.weight}, draft={self.draft}"

    def __bool__(self):
        return bool(self._content)

    def _compare(self, other):
        return not isinstance(other, self.__class__) or self.parent.resolve() != other.parent.resolve()

    def __lt__(self, other):
        if self._compare(other):
            return NotImplemented

        elif self.draft is not other.draft:
            return int(self.draft) < int(other.draft)

        elif self.weight != other.weight:
            return self.weight < other.weight

        else:
            return self.title < other.title

    def __le__(self, other):
        if self._compare(other):
            return NotImplemented

        elif self.draft is not other.draft:
            return int(self.draft) < int(other.draft)

        elif self.weight != other.weight:
            return self.weight < other.weight

        else:
            return self.title <= other.title

    def __gt__(self, other):
        if self._compare(other):
            return NotImplemented

        elif self.draft is not other.draft:
            return int(self.draft) > int(other.draft)

        elif self.weight != other.weight:
            return self.weight > other.weight

        else:
            return self.title > other.title

    def __ge__(self, other):
        if self._compare(other):
            return NotImplemented

        elif self.draft is not other.draft:
            return int(self.draft) > int(other.draft)

        elif self.weight != other.weight:
            return self.weight > other.weight

        else:
            return self.title >= other.title

    @property
    def is_index(self):
        return self._path.stem in INDEX_STEMS


class TextFolder(WithFrontMatter):
    def __init__(
            self,
            path: StrPath, *,
            file_paths: Iterable[StrPath] = None,
            folder_paths: Iterable[StrPath] = None):
        super().__init__(path)

        if file_paths is None:
            file_paths: list[Path] = []

        else:
            file_paths: list[Path] = [
                Path(file_path).expanduser() for file_path in file_paths]

        if folder_paths is None:
            folder_paths: list[Path] = []

        else:
            folder_paths: list[Path] = [
                Path(folder_path).expanduser() for folder_path in folder_paths]

        self._text_files: list[TextFile] = []
        self._file_paths: list[Path] = file_paths
        self._text_folders: dict[int, TextFolder] = {}
        self._folder_paths: list[Path] = folder_paths
        self._index_file: Path | None = None
        self.find_index_file()
        self.set_front_matter()
        self.add_file_paths()
        self.handle_text_files()

    def find_index_file(self):
        for name, suffix in product(INDEX_STEMS, EXTENSIONS):
            index_file: Path = self._path.joinpath(f"{name}{suffix}")

            if index_file.exists(follow_symlinks=True):
                self._index_file = index_file
                return

    def __bool__(self):
        return self._index_file is not None

    def __str__(self):
        return str(self.index_text_file)

    def __key(self):
        return self.level, self.weight, self.title

    def _compare(self, other):
        return not isinstance(other, self.__class__) or self.draft or other.draft

    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        elif self.draft is not other.draft:
            return int(self.draft) < int(other.draft)

        elif self.level != other.level:
            return self.level < other.level

        elif self.weight != other.weight:
            return self.weight < other.weight

        else:
            return self.title < other.title

    def __le__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        elif self.draft is not other.draft:
            return int(self.draft) < int(other.draft)

        elif self.level != other.level:
            return self.level < other.level

        elif self.weight != other.weight:
            return self.weight < other.weight

        else:
            return self.title <= other.title

    def __gt__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        elif self.draft is not other.draft:
            return int(self.draft) > int(other.draft)

        elif self.level != other.level:
            return self.level > other.level

        elif self.weight != other.weight:
            return self.weight > other.weight

        else:
            return self.title > other.title

    def __ge__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented

        elif self.draft is not other.draft:
            return int(self.draft) > int(other.draft)

        elif self.level != other.level:
            return self.level > other.level

        elif self.weight != other.weight:
            return self.weight > other.weight

        else:
            return self.title >= other.title

    @property
    def index_text_file(self):
        return TextFile(self._index_file)

    @property
    def level(self):
        return len(self._path.relative_to(self.root).parts) - 2

    def set_front_matter(self):
        if bool(self):
            self._front_matter = self.index_text_file.front_matter

        else:
            self._front_matter = {
                "draft": True,
                "weight": 10_000,
                "title": "_"}

    def add_file_paths(self):
        self._file_paths = list(
            set(self._file_paths)
            .union(
                item for item in self._path.resolve().iterdir()
                if item.is_file and item.suffix in EXTENSIONS))

    def handle_text_files(self):
        text_files: list[TextFile] = [
            TextFile(file_path)
            for file_path in self._file_paths
            if file_path.suffix in EXTENSIONS]

        for index, text_file in enumerate(text_files):
            if not text_file.draft and not text_file.is_index:
                self._text_files.append(text_file)

        self._text_files = list(set(self._text_files))

    def to_dict(self):
        if self.draft:
            return None

        key: str = self._path.relative_to(self.root).as_posix()
        title: dict[str, str | int | bool] = {}

        if not bool(self.index_text_file):
            title["value"] = self.index_text_file.title
            index: list[str] | None = None

        else:
            index: list[str] | None = [self.index_text_file.relpath]

        title["level"] = self.level

        if self._text_files:
            files: list[str] | None = list(map(lambda x: x.relpath, sorted(self._text_files)))

        else:
            files: list[str] | None = None

        kwargs: dict[str, dict[str, int | str | bool] | list[str]] = {}

        if title is not None:
            kwargs["title"] = title

        if index is not None:
            kwargs["index"] = index

        if files is not None:
            kwargs["files"] = files

        return {key: kwargs}

    @property
    def text_files(self):
        return self._text_files

    @property
    def file_paths(self):
        return self._file_paths


class FolderStorage:
    def __init__(self, path: StrPath):
        self._path: Path = Path(path).expanduser()
        self._text_folders: list[TextFolder] = []
        self._directories: list[StrPath] = []
        self._tree: RecursiveDict = {}
        self.walk_dirs()

    @property
    def directories(self):
        return self._directories

    @property
    def text_folders(self):
        return self._text_folders

    def sort(self):
        self._text_folders.sort()

    def to_yaml(self):
        safe_dump([_tf.to_dict() for _tf in self._text_folders], allow_unicode=True)

    def walk_dirs(self, base_path: str | Path = None):
        if base_path is None:
            base_path: str | Path = self._path

        tree: RecursiveDict = {}

        for dirpath, dirnames, filenames in self._path.walk():
            dirpath: Path = Path(dirpath).expanduser()
            file_paths: list[str | Path] = [dirpath.joinpath(filename) for filename in filenames]
            folder_paths: list[str | Path] = [dirpath.joinpath(dirname) for dirname in dirnames]
            text_folder: TextFolder = TextFolder(
                dirpath,
                file_paths=file_paths,
                folder_paths=folder_paths)
            self._text_folders.append(text_folder)
            path: Path = Path(dirpath).relative_to(base_path)
            tree[path] = [Path(filename) for filename in filenames]

        self._tree = tree


if __name__ == '__main__':
    root: Path = Path("../../DRA")
    WithFrontMatter.root = root

    folder_storage: FolderStorage = FolderStorage(root.joinpath("content/common"))
    folder_storage.walk_dirs(root)

    folder_storage.sort()
    data: list[dict] = [v.to_dict() for v in folder_storage.text_folders]
    print(safe_dump(data, stdout, indent=2, allow_unicode=True))
