# -*- coding: utf-8 -*-
class BaseError(Exception):
    """Base class to inherit."""


class InvalidPythonVersion(BaseError):
    """Installed Python version is outdated."""


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


class InvalidProjectIdError(TermsError):
    """Gitlab project identifier is not a positive integer."""


class InvalidVersionError(TermsError):
    """File version has an invalid structure."""


class InvalidTermIndexError(TermsError):
    """Specified index is not found in the dictionary."""


class EmptyFileError(TermsError):
    """Read file is empty."""


class LinkRepairError(BaseError):
    """Base class for errors associated with the link-repair."""


class LineInvalidTypeError(LinkRepairError):
    """Line index type must be int and its value must be str."""


class InvalidStorageAttributeError(LinkRepairError):
    """Storage attribute is not proper."""


class InvalidFileDictAttributeError(LinkRepairError):
    """FileDict attribute is not proper."""


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


class ConvertTablesError(BaseError):
    """Base class for errors associated with the convert-tables."""


class EmptyLinesError(ConvertTablesError):
    """Lines to format is not specified."""


class FormatCodeError(BaseError):
    """Base class for errors associated with the format-code."""


class NonPositiveLineLengthError(FormatCodeError):
    """Maximum line length cannot be less than zero."""


class NonIntegerLineLengthError(FormatCodeError):
    """Maximum line length cannot be non-integer."""
