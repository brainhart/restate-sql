"""DB-API 2.0 compatible exceptions for Restate SQL."""


class Error(Exception):
    """Base exception for database-related errors."""


class Warning(Exception):
    """Exception for important warnings."""


class InterfaceError(Error):
    """Exception for errors related to the database interface."""


class DatabaseError(Error):
    """Exception for errors related to the database."""


class DataError(DatabaseError):
    """Exception for errors due to problems with the processed data."""


class OperationalError(DatabaseError):
    """Exception for errors related to database operation."""


class IntegrityError(DatabaseError):
    """Exception for database constraint violations."""


class InternalError(DatabaseError):
    """Exception for internal database errors."""


class ProgrammingError(DatabaseError):
    """Exception for programming errors."""


class NotSupportedError(DatabaseError):
    """Exception for operations not supported by the database."""
