# -*- coding: utf-8 -*-
class BaseError(Exception):
    """Base class to inherit."""


class LineInvalidTypeError(BaseError):
    """Line index type must be int and its value must be str."""


class InvalidStorageAttributeError(BaseError):
    """Storage attribute is not proper."""


class InvalidFileDictAttributeError(BaseError):
    """FileDict attribute is not proper."""


class InvalidPythonVersion(BaseError):
    """Installed Python version is outdated."""


class FileInvalidTypeError(BaseError):
    """File has an invalid type."""


class InternalLinkAnchorError(BaseError):
    """Neither anchor nor internal link is found in file."""


class InvalidMatchError(BaseError):
    """Match item does not have enough match groups."""


class FixerNoLinkError(BaseError):
    """LinkFixer instance has no specified link."""


class InvalidHashCharIndexError(BaseError):
    """Impossible hash symbol position in the string."""


class MissingFileError(BaseError):
    """File is not found."""
