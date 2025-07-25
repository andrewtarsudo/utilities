# -*- coding: utf-8 -*-
class BaseError(Exception):
    """Base class to inherit."""


class CommandNotFoundError(BaseError):
    """Input command has not been found."""


class InvalidPythonVersion(BaseError):
    """Installed Python version is outdated."""


class TimerError(BaseError):
    """Base class for errors associated with the timer."""


class TimerRunningError(TimerError):
    """Timer is already running."""


class TimerStoppedError(TimerError):
    """Timer has been already stopped."""


class GetTermsError(BaseError):
    """Base class for errors associated with the get-terms."""


class GetTermsAsciiDocFileTableRowIndexError(GetTermsError):
    """Invalid AsciiDocTable row index."""


class GetTermsInvalidTermIndexError(GetTermsError):
    """Specified index is not found in the dictionary."""


class GetTermsEmptyFileError(GetTermsError):
    """Read file is empty."""


class MutuallyExclusiveOptionError(BaseError):
    """Command contains mutually exclusive options."""


class ConditionalOptionError(BaseError):
    """Command contains none of the conditional options."""


class RepairLinksError(BaseError):
    """Base class for errors associated with the repair-links."""


class RepairLinksTextFileInvalidPathError(RepairLinksError):
    """Text file has an invalid extension."""


class RepairLinksLineInvalidTypeError(RepairLinksError):
    """Line index type must be int and its value must be str."""


class RepairLinksInvalidStorageAttributeError(RepairLinksError):
    """Storage attribute is not proper."""


class RepairLinksInvalidFileDictAttributeError(RepairLinksError):
    """FileDict attribute is not proper."""


class RepairLinksFileInvalidTypeError(RepairLinksError):
    """File has an invalid type."""


class RepairLinksInternalLinkAnchorError(RepairLinksError):
    """Neither anchor nor internal link is found in file."""


class RepairLinksInvalidMatchError(RepairLinksError):
    """Match item does not have enough match groups."""


class RepairLinksFixerNoLinkError(RepairLinksError):
    """LinkFixer instance has no specified link."""


class RepairLinksInvalidHashCharIndexError(RepairLinksError):
    """Impossible hash symbol position in the string."""


class RepairLinksMissingFileError(RepairLinksError):
    """File is not found."""


class ConvertTablesError(BaseError):
    """Base class for errors associated with the convert-tables."""


class ConvertTablesEmptyLinesError(ConvertTablesError):
    """Lines to format is not specified."""


class ConvertTablesInvalidFileError(ConvertTablesError):
    """Failed to parse the specified file."""


class FormatCodeError(BaseError):
    """Base class for errors associated with the format-code."""


class FormatCodeNonPositiveLineLengthError(FormatCodeError):
    """Maximum line length cannot be less than zero."""


class FormatCodeNonIntegerLineLengthError(FormatCodeError):
    """Maximum line length cannot be non-integer."""


class TableColsError(BaseError):
    """Base class for errors associated with the set-table-cols."""


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


class GenerateYamlError(BaseError):
    """Base class for errors associated with the generate-yaml."""


class GenerateYamlMissingAttributeError(GenerateYamlError):
    """At least one of 'title-page', 'version' required parameters is missing."""


class GenerateYamlMissingIndexFileError(GenerateYamlError):
    """Files index/_index have not been found."""


class GenerateYamlMissingBranchError(GenerateYamlError):
    """Branch instance cannot be None."""


class GenerateYamlInvalidLevelError(GenerateYamlError):
    """Chapter level cannot be less than 1."""


class TableError(BaseError):
    """Base class for errors associated with the tables."""


class TableKeyError(TableError):
    """Line with the specified index has not been found."""


class TableRowIndexError(TableColsError):
    """Specified row index has not been found."""


class TableRowInvalidIdentifierError(TableColsError):
    """Specified column identifier has an invalid type."""


class ValidateYamlBaseError(BaseError):
    """Base class for errors associated with the validate-yaml."""


class LoggerInitError(BaseError):
    """Failed to initiate loguru logger."""


class ShellUnknownError(BaseError):
    """Failed to determine the operating system and command line shell."""
