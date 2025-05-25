"""Restate SQL DB-API 2.0 compatible interface.

This package provides a Python DB-API 2.0 compatible interface for querying
Restate's SQL introspection API.
"""

from .connection import connect
from .exceptions import (
    DatabaseError,
    DataError,
    Error,
    IntegrityError,
    InterfaceError,
    InternalError,
    NotSupportedError,
    OperationalError,
    ProgrammingError,
    Warning,
)

__version__ = "0.1.0"

# DB-API 2.0 module interface
apilevel = "2.0"
threadsafety = 1  # Threads may share the module
paramstyle = "named"  # Named parameters (:param)

__all__ = [
    "DataError",
    "DatabaseError",
    "Error",
    "IntegrityError",
    "InterfaceError",
    "InternalError",
    "NotSupportedError",
    "OperationalError",
    "ProgrammingError",
    "Warning",
    "apilevel",
    "connect",
    "paramstyle",
    "threadsafety",
]
