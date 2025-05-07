# -*- coding: utf-8 -*-
from pathlib import Path
from stat import S_IREAD, S_IWRITE

from pytest import raises

from utilities.common.errors import FileReaderTypeError, UpdateProjectIdError
from utilities.common.functions import check_path, file_reader, file_reader_type, file_writer, GitFile, walk_full


def test_file_reader_reads_string_success(tmp_path: Path) -> None:
    file_path: Path = tmp_path.joinpath("test.txt")
    content: str = "Hello, world!"
    file_path.write_text(content, encoding="utf-8")
    result: str = file_reader(file_path, "string")

    assert result == content


def test_check_path_valid_file(tmp_path: Path) -> None:
    file_path: Path = tmp_path.joinpath("foo.md")
    file_path.write_text("test")
    ignored_dirs: set[str] = {"ignored_dir"}
    ignored_files: set[str] = {"ignored_file"}
    extensions: set[str] = {".md", ".adoc"}

    result: bool = check_path(
        file_path,
        ignored_dirs,
        ignored_files,
        extensions)

    assert result is True


def test_file_reader_file_not_found(tmp_path: Path) -> None:
    missing_file: Path = tmp_path.joinpath("does_not_exist.txt")

    with raises(FileNotFoundError):
        file_reader(missing_file, "string")


def test_file_reader_type_invalid_extension(tmp_path: Path) -> None:
    file_path: Path = tmp_path.joinpath("foo.txt")
    file_path.write_text("{}", encoding="utf-8")

    with raises(FileReaderTypeError):
        file_reader_type(file_path, "json")


def test_git_file_invalid_project_id() -> None:
    with raises(UpdateProjectIdError):
        GitFile(file_name="foo.txt", project_id="not_an_int")


def test_walk_full_collects_files_with_ignores(tmp_path: Path) -> None:
    # Setup directory structure
    tmp_path.joinpath("keep.md").write_text("a")
    tmp_path.joinpath("ignore.txt").write_text("b")
    ignored_dir: Path = tmp_path.joinpath("ignored")
    ignored_dir.mkdir()
    ignored_dir.joinpath("skip.md").write_text("c")
    ignored_dirs: set[str] = {"ignored"}
    ignored_files: set[str] = {"ignore"}
    extensions: set[str] = {".md"}
    files: list[Path] = walk_full(
        tmp_path,
        ignored_dirs=ignored_dirs,
        ignored_files=ignored_files,
        extensions=extensions)
    files_str: list[str] = list(map(str, files))

    assert any("keep.md" in f for f in files_str)
    assert not any("ignore.txt" in f for f in files_str)
    assert not any("skip.md" in f for f in files_str)


def test_file_writer_permission_error(tmp_path: Path) -> None:
    file_path: Path = tmp_path.joinpath("protected.txt")
    file_path.write_text("original")
    # Remove write permissions
    file_path.chmod(S_IREAD)

    try:
        with raises(PermissionError):
            file_writer(file_path, "new content")

    finally:
        # Restore permissions so tmp_path can be cleaned up
        file_path.chmod(S_IWRITE | S_IREAD)
