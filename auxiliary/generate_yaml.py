# -*- coding: utf-8 -*-
from itertools import product
from os import scandir
from pathlib import Path
from sys import stdout
from typing import Any, Iterable

# noinspection PyProtectedMember
from frontmatter import load, Post
import yaml

from utilities.common.shared import ADOC_EXTENSION, MD_EXTENSION, StrPath


def walk_directory(directory: str | Path, tree: dict[Path, Any] = None):
    """Recursively build a Tree with directory contents."""
    # Sort dirs first then by filename
    if tree is None:
        tree: dict[Path, list[Path]] = {directory: []}

    for path in Path(directory).iterdir():
        if path.is_dir():
            tree[directory].append({path: []})
            tree[directory].append(walk_directory(path, tree))

        else:
            tree[directory].append(path)

    return tree


class WithFrontMatter:
    root: Path

    def __init__(self, path: StrPath):
        print(path)
        self._path: Path = Path(path).expanduser()
        self._front_matter: dict[str, str | int | bool | object] = {}

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

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._path, self.weight == other._path, other.weight

        else:
            return NotImplemented

    def __lt__(self, other):
        if not isinstance(other, self.__class__) or self.draft or other.draft or self.parent != other.parent:
            return NotImplemented

        if self.weight != other.weight:
            return self.weight < other.weight

        else:
            return self.title < other.title

    def __le__(self, other):
        if not isinstance(other, self.__class__) or self.draft or other.draft or self.parent != other.parent:
            return NotImplemented

        if self.weight != other.weight:
            return self.weight < other.weight

        else:
            return self.title <= other.title

    def __gt__(self, other):
        if not isinstance(other, self.__class__) or self.draft or other.draft or self.parent != other.parent:
            return NotImplemented

        if self.weight != other.weight:
            return self.weight > other.weight

        else:
            return self.title > other.title

    def __ge__(self, other):
        if not isinstance(other, self.__class__) or self.draft or other.draft or self.parent != other.parent:
            return NotImplemented

        if self.weight != other.weight:
            return self.weight > other.weight

        else:
            return self.title >= other.title

    def __hash__(self):
        return hash(self._path)

    @property
    def relpath(self):
        return self._path.relative_to(self.root).as_posix()

    @property
    def path(self):
        return self._path


class TextFile(WithFrontMatter):
    def __init__(self, path: StrPath):
        super().__init__(path)
        self._post: Post = load(self._path.as_posix(), encoding="utf-8")
        self._front_matter: dict[str, str | int | bool | object] = self._post.metadata
        self._content: str = self._post.content.strip()

    def __bool__(self):
        return bool(self._content)


class TextFolder(WithFrontMatter):
    def __init__(self, path: StrPath, file_paths: Iterable[StrPath] = None, folder_paths: Iterable[StrPath] = None):
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

        self._text_files: dict[int, TextFile] = {}
        self._file_paths: list[Path] = file_paths
        self._text_folders: dict[int, TextFolder] = {}
        self._folder_paths: list[Path] = folder_paths
        self._index_file: Path | None = None
        self.find_index_file()
        self.set_front_matter()

    def find_index_file(self):
        names: tuple[str, ...] = ("_index", "index")
        suffixes: tuple[str, ...] = (MD_EXTENSION, ADOC_EXTENSION)

        for name, suffix in product(names, suffixes):
            index_file: Path = self._path.joinpath(f"{name}{suffix}")
            print(f"{index_file=}")
            print(f"{index_file.exists()=}")

            if index_file.exists(follow_symlinks=True):
                self._index_file = index_file
                return

    def __bool__(self):
        return self._index_file is not None

    @property
    def index_text_file(self):
        return TextFile(self._index_file)

    @property
    def level(self):
        return len(self._path.relative_to(self.root).parts) - 2

    def set_front_matter(self):
        if bool(self):
            self._front_matter = self.index_text_file.front_matter

    def handle_text_files(self):
        text_files: list[TextFile] = [
            TextFile(file_path) for file_path in self._file_paths]

        self._text_files = {
            index: text_file
            for index, text_file in enumerate(sorted(filter(lambda x: not x.draft, text_files)))}

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
            files: list[str] | None = [self._text_files.get(k).relpath for k in sorted(self._text_files.keys())]

        else:
            files: list[str] | None = None

        return {
            key: {
                "title": title,
                "index": index,
                "files": files
            }
        }

    @property
    def text_files(self):
        return self._text_files

    @property
    def file_paths(self):
        return self._file_paths


class FolderStorage:
    def __init__(self, path: StrPath):
        self._path: Path = Path(path).expanduser()
        self._text_folders: dict[int, TextFolder] = {}
        self._directories: list[StrPath] = []

    def find_directories(
            self, *,
            item: Path = None,
            ignored_dirs: Iterable[str] = None,
            ignored_files: Iterable[str] = None,
            extensions: Iterable[str] = None,
            language: str | None = None,
            root: Path = None,
            results: list[Path] = None):
        if root is None:
            root: Path = WithFrontMatter.root

        if item is None:
            item: Path = self._path

        if results is None:
            results: list[Path] = []

        for element in scandir(item):
            item: Path = Path(element.path)

            if element.is_dir(follow_symlinks=True):
                self._directories.append(element.path)
                self.find_directories(
                    item=item,
                    ignored_dirs=ignored_dirs,
                    ignored_files=ignored_files,
                    extensions=extensions,
                    language=language,
                    root=root,
                    results=results)

            else:
                continue

    @property
    def directories(self):
        return self._directories

    @property
    def text_folders(self):
        return self._text_folders

    def sort(self):
        self._text_folders = {k: self._text_folders.get(k) for k in sorted(self._text_folders.keys())}

    def to_yaml(self):
        yaml.dump([_tf.to_dict() for _tf in self._text_folders.values()])


if __name__ == '__main__':
    WithFrontMatter.root = Path("../../MME")

    folder_storage: FolderStorage = FolderStorage(WithFrontMatter.root.joinpath("content/common"))
    folder_storage.find_directories()

    for folder in folder_storage.directories:
        text_folder: TextFolder = TextFolder(folder)

        if bool(text_folder):
            text_folder._file_paths = [
                item for item in text_folder.path.iterdir()
                if item.is_file() and item.suffix in (MD_EXTENSION, ADOC_EXTENSION)]

            for file in text_folder.file_paths:
                text_file: TextFile = TextFile(file)
                text_folder.text_files[text_file.weight] = text_file

            folder_storage.text_folders[text_folder.weight] = text_folder

    folder_storage.sort()
    data: dict = {k: v.to_dict() for k, v in folder_storage.text_folders.items()}
    print(yaml.safe_dump(data, stdout, indent=2))
    # print([_.to_dict() for _ in folder_storage.text_folders.values()])

    print(walk_directory("../"))