# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Any, Mapping

# noinspection PyProtectedMember
from frontmatter import load, Post
from yaml import dump


def is_valid_file(filepath: str | Path):
    """Check if file is .md or .adoc"""
    return Path(filepath).suffix in (".md", ".adoc")


def has_content(filepath: str | Path):
    """Check if file has any non-empty content"""
    try:
        post: Post = load(filepath)
        return bool(post.content.strip())

    except OSError:
        return False


def parse_frontmatter(filepath: str | Path, root: str | Path) -> dict[str, int | str] | None:
    """Extract frontmatter from a file. Returns None if invalid."""
    filepath: Path = Path(filepath)

    try:
        post: Post = load(filepath.as_posix())
        # Ignore if no frontmatter (post.metadata is empty)
        if not post.metadata:
            return None

        elif post.get("draft", False):
            return None

        return {
            "weight": post.get("weight"),
            "title": post.get("title", ""),  # Default to empty string
            "filename": filepath.relative_to(root).as_posix(),
            'path': filepath.as_posix()}

    except OSError:
        return None


def get_dir_info(dirpath: str | Path, root: str | Path) -> dict[str, int | str] | None:
    """Check for _index.* or index.* in a directory to determine its weight."""
    dirpath: Path = Path(dirpath)

    for filename in ["_index.md", "index.md", "_index.adoc", "index.adoc"]:
        filepath: Path = dirpath.joinpath(filename)

        if filepath.exists():
            front_matter: dict[str, int | str] | None = parse_frontmatter(filepath, root)

            if front_matter is not None:
                return {
                    "weight": front_matter.get("weight"),
                    "index": front_matter.get("filename") if has_content(filepath) else None}

    else:
        return None


def check_language(file_path: str | Path, language: str | None = None):
    if language is None:
        language: str = ""

    suffixes: list[str] = Path(file_path).suffixes

    if len(suffixes) == 1:
        file_language: str = ""

    else:
        file_language: str = suffixes[0]

    return file_language == language


def process_directory(
        dirpath: str | Path,
        base_path: str | Path,
        root: str | Path,
        language: str | None = None):
    dirpath: Path = Path(dirpath)

    dir_info: dict[str, int | str] | None = get_dir_info(dirpath, root)

    if dir_info is None:
        return {}, 0

    dir_entry: dict[str, list[str] | dict[str, int | str] | str | int] = {
        "files": [],
        "index": [dir_info.get("index")] if dir_info.get("index") else None}

    valid_files: list[dict[str, int | str]] | None = []

    for filepath in dirpath.iterdir():
        if not filepath.is_file() or not is_valid_file(filepath):
            continue

        elif not check_language(filepath, language):
            continue

        # Skip index files (already handled for directory weight)
        elif filepath.stem in ("_index", "index"):
            continue

        front_matter: dict[str, int | str] | None = parse_frontmatter(filepath, root)

        if front_matter is not None:
            valid_files.append(front_matter)

    valid_files.sort(key=lambda x: (x.get("weight"), x.get("title").lower().strip()))
    dir_entry["files"] = [file.get("filename") for file in valid_files]

    subdirs: dict[str, Any] = {}

    for subdir in sorted(dirpath.iterdir()):
        if subdir.is_dir():
            subdir_tree, _ = process_directory(subdir, base_path, root, language)

            if subdir_tree:
                subdir_name: str = subdir.name
                subdirs[subdir_name] = subdir_tree

    # Only add if we have content
    if subdirs:
        dir_entry["subdirs"] = subdirs

    return dir_entry, dir_info.get("weight")


def build_tree(base_path: str | Path, root: str | Path, language: str | None = None) -> dict[str, dict[str, list[str] | dict[str, int | str] | str | int]]:
    """Generate the YAML tree structure with sorted directories and files."""
    base_path: Path = Path(base_path).resolve()
    tree, _ = process_directory(base_path, base_path, root, language)

    return tree


def process_tree(tree: Mapping[str, str | int | list[str] | dict[str, str | int | list[str]]]):
    processed_tree: dict[str, str | int | list[str] | dict[str, str | int | list[str]]] = {}

    for k, v in tree.items():
        if isinstance(v, Mapping):
            processed: dict[str, str | int | list[str] | dict[str, str | int | list[str]]] = process_tree(v)

            if processed:
                processed_tree[k] = processed

        elif v is not None and v:
            processed_tree[k] = v

    return processed_tree


def save_tree(tree: dict[str, str | int | list[str] | dict[str, str | int | list[str]]], path: str | Path):
    def flatten_tree(current_tree: dict[str, Any], flat: dict[str, Any], current_path: str = ""):
        for key, entry in current_tree.items():
            if key == "subdirs":
                for subdir_name, subdir_entry in entry.items():
                    new_path: str = Path(current_path).joinpath(subdir_name).as_posix() if current_path else subdir_name

                    flat_entry = {}

                    if "index" in subdir_entry:
                        flat_entry["index"] = subdir_entry.get("index")

                    if "files" in subdir_entry:
                        flat_entry["files"] = subdir_entry.get("files")

                    flat[new_path] = flat_entry

                    if "subdirs" in subdir_entry:
                        flatten_tree(subdir_entry, flat, new_path)

            else:
                if current_path in flat:
                    flat[current_path][key] = entry

                elif current_path:
                    flat[current_path] = {key: entry}

    flat_tree: dict[str, dict[str, Any | None]] = {}

    if "index" in tree:
        flat_tree["."] = {"index": tree.get("index")}

    if "files" in tree:
        if "." in flat_tree:
            flat_tree["."]["files"] = tree.get("files")

        else:
            flat_tree["."] = {"files": tree.get("files")}

    # Handle subdirectories
    if "subdirs" in tree:
        flatten_tree(tree, flat_tree)

    with open(path, "w") as f:
        dump(flat_tree, f, indent=2, allow_unicode=True, sort_keys=False)


if __name__ == '__main__':
    root_dir: Path = Path("../../hlr_hss/content/common").resolve()
    _file_tree: dict[str, dict[str, list[str]]] = build_tree(root_dir, root_dir.parent.parent)
    file_tree = process_tree(_file_tree)
    save_tree(file_tree, "file.yaml")
