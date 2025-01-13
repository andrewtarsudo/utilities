# -*- coding: utf-8 -*-
class BaseError(Exception):
    """Base class to inherit."""


class TimerError(BaseError):
    """Base class for errors associated with the timer."""


class TimerRunningError(TimerError):
    """Timer is already running."""


class TimerStoppedError(TimerError):
    """Timer has been already stopped."""


class TermsError(BaseError):
    """Base class for errors associated with the terms."""


class RequiredAttributeMissingError(TermsError):
    """Required attribute has no specified value."""


class AsciiDocFileTableRowIndexError(TermsError):
    """Invalid AsciiDocTable row index."""


class ImportLibraryDependencyFailedError(TermsError):
    """Dependency lib failed to import."""


class InvalidProjectIdError(TermsError):
    """Gitlab project identifier is not a positive integer."""


class InvalidVersionError(TermsError):
    """File version has an invalid structure."""


class InvalidTermIndexError(TermsError):
    """Specified index is not found in the dictionary."""


class EmptyFileError(TermsError):
    """Read file is empty."""


# -*- coding: utf-8 -*-
class LinkRepairError(BaseError):
    """Base class to inherit."""


class LineInvalidTypeError(LinkRepairError):
    """Line index type must be int and its value must be str."""


class InvalidStorageAttributeError(LinkRepairError):
    """Storage attribute is not proper."""


class InvalidFileDictAttributeError(LinkRepairError):
    """FileDict attribute is not proper."""


class InvalidPythonVersion(LinkRepairError):
    """Installed Python version is outdated."""


class FileInvalidTypeError(LinkRepairError):
    """File has an invalid type."""


class InternalLinkAnchorError(LinkRepairError):
    """Neither anchor nor internal link is found in file."""


class InvalidMatchError(LinkRepairError):
    """Match item does not have enough match groups."""


class FixerNoLinkError(LinkRepairError):
    """LinkFixer instance has no specified link."""


class InvalidHashCharIndexError(LinkRepairError):
    """Impossible hash symbol position in the string."""


class MissingFileError(LinkRepairError):
    """File is not found."""
