# -*- coding: utf-8 -*-
from pathlib import Path


class GitManager:
    TEMPORARY: Path
    TEMPORARY_TERMS: Path
    TEMP_VERSION: Path
    TEMP_TERMS_VERSION: Path
    TEMP_TERMS: Path
    TEMP_TERMS_BASIC: Path

    def __init__(self) -> None: ...

    def __eq__(self, other): ...

    def __ne__(self, other): ...

    def __bool__(self) -> bool: ...

    @property
    def version_validator(self): ...

    def set_content_git_pages(self) -> None: ...

    def set_versions(self) -> None: ...

    def output_if_different(self, message: str): ...

    def compare(self) -> None: ...

    def set_terms(self) -> None: ...

    def __iter__(self): ...


git_manager: GitManager
