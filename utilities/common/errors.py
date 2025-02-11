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


class TermsRequiredAttributeMissingError(TermsError):
    """Required attribute has no specified value."""


class TermsAsciiDocFileTableRowIndexError(TermsError):
    """Invalid AsciiDocTable row index."""


class TermsInvalidProjectIdError(TermsError):
    """Gitlab project identifier is not a positive integer."""


class TermsInvalidVersionError(TermsError):
    """File version has an invalid structure."""


class TermsInvalidTermIndexError(TermsError):
    """Specified index is not found in the dictionary."""


class TermsEmptyFileError(TermsError):
    """Read file is empty."""


class TermsInvalidTypeVersionError(TermsError):
    """File version has an invalid type."""


class LinkRepairError(BaseError):
    """Base class for errors associated with the link-repair."""


class LinkRepairLineInvalidTypeError(LinkRepairError):
    """Line index type must be int and its value must be str."""


class LinkRepairInvalidStorageAttributeError(LinkRepairError):
    """Storage attribute is not proper."""


class LinkRepairInvalidFileDictAttributeError(LinkRepairError):
    """FileDict attribute is not proper."""


class LinkRepairFileInvalidTypeError(LinkRepairError):
    """File has an invalid type."""


class LinkRepairInternalLinkAnchorError(LinkRepairError):
    """Neither anchor nor internal link is found in file."""


class LinkRepairInvalidMatchError(LinkRepairError):
    """Match item does not have enough match groups."""


class LinkRepairFixerNoLinkError(LinkRepairError):
    """LinkFixer instance has no specified link."""


class LinkRepairInvalidHashCharIndexError(LinkRepairError):
    """Impossible hash symbol position in the string."""


class LinkRepairMissingFileError(LinkRepairError):
    """File is not found."""


class ConvertTablesError(BaseError):
    """Base class for errors associated with the convert-tables."""


class ConvertTablesEmptyLinesError(ConvertTablesError):
    """Lines to format is not specified."""


class ConvertTablesFormatCodeError(BaseError):
    """Base class for errors associated with the format-code."""


class ConvertTablesNonPositiveLineLengthError(ConvertTablesFormatCodeError):
    """Maximum line length cannot be less than zero."""


class ConvertTablesNonIntegerLineLengthError(ConvertTablesFormatCodeError):
    """Maximum line length cannot be non-integer."""


class TableColsError(BaseError):
    """Base class for errors associated with the table_cols-cols."""


class TableColsTableBorderNotClosedError(TableColsError):
    """Specified file has closing table_cols border mark '|===' missing."""


class TableColsTableCoordinateInitError(TableColsError):
    """Specified value cannot represent the cell coordinates in the table."""


class TableColsTableColumnTypeError(TableColsError):
    """Specified value has an invalid type."""


class TableColsTableColumnIndexError(TableColsError):
    """Specified column index has not been found."""


class TableColsTableColumnInvalidNameError(TableColsError):
    """Specified column name has not been found."""


class TableColsTableColumnInvalidIdentifierError(TableColsError):
    """Specified column identifier has an invalid type."""
