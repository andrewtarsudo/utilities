# -*- coding: utf-8 -*-
class BaseError(Exception):
    """Base error class to inherit."""


class RequiredAttributeMissingError(BaseError):
    """Required attribute has no specified value."""


class AsciiDocFileTableRowIndexError(BaseError):
    """Invalid AsciiDocTable row index."""


class ImportLibraryDependencyFailedError(BaseError):
    """Dependency lib failed to import."""


class InvalidProjectIdError(BaseError):
    """Gitlab project identifier is not a positive integer."""


class InvalidVersionError(BaseError):
    """File version has an invalid structure."""


class InvalidTermIndexError(BaseError):
    """Specified index is not found in the dictionary."""


class EmptyFileError(BaseError):
    """Read file is empty."""
