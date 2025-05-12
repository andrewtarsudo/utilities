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
    """Base class for errors associated with the get_terms."""


class TermsAsciiDocFileTableRowIndexError(TermsError):
    """Invalid AsciiDocTable row index."""


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


class LinkRepairTextFileInvalidPathError(LinkRepairError):
    """Text file has an invalid extension."""


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


class FormatCodeError(BaseError):
    """Base class for errors associated with the format-code."""


class FormatCodeNonPositiveLineLengthError(FormatCodeError):
    """Maximum line length cannot be less than zero."""


class FormatCodeNonIntegerLineLengthError(FormatCodeError):
    """Maximum line length cannot be non-integer."""


class TableColsError(BaseError):
    """Base class for errors associated with the table-cols."""


class TableColsTableBorderNotClosedError(TableColsError):
    """Specified file has closing set_table_cols border mark '|===' missing."""


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


class NoArgumentsOptionsError(BaseError):
    """No argument or option is specified."""


class FileReaderError(BaseError):
    """Specified file reader mode has an invalid type."""


class FileReaderTypeError(BaseError):
    """Specified file has an improper extension."""


class UpdateProjectIdError(BaseError):
    """Specified project_id is invalid."""


class ConfigFileError(BaseError):
    """Base class for errors associated with the config file sources/config.toml."""


class ConfigFileGeneralKeyError(ConfigFileError):
    """Specified key has not been found in the section 'general'."""


class ConfigFileUpdateKeyError(ConfigFileError):
    """Specified key has not been found in the section 'update'."""
