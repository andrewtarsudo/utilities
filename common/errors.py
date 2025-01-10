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
