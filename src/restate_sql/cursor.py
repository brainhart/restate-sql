"""DB-API 2.0 compatible Cursor class for Restate SQL."""

from collections.abc import Sequence
from typing import Any

import pandas as pd
from rich.table import Table

from .exceptions import InterfaceError, ProgrammingError


class Cursor:
    """DB-API 2.0 compatible cursor for executing queries against Restate SQL."""

    def __init__(self, connection):
        """Initialize cursor with a connection.

        Args:
            connection: The connection object this cursor belongs to

        """
        self.connection = connection
        self._closed = False
        self._results: list[tuple] | None = None
        self._description: list[tuple] | None = None
        self._rowcount = -1
        self._arraysize = 1
        self._rownumber = 0

    @property
    def description(self) -> list[tuple] | None:
        """Sequence of 7-item sequences describing result columns.

        Each sequence contains:
        (name, type_code, display_size, internal_size, precision, scale, null_ok)
        """
        return self._description

    @property
    def rowcount(self) -> int:
        """Number of rows affected by the last operation."""
        return self._rowcount

    @property
    def arraysize(self) -> int:
        """Number of rows to fetch at a time with fetchmany()."""
        return self._arraysize

    @arraysize.setter
    def arraysize(self, size: int) -> None:
        """Set the number of rows to fetch at a time."""
        self._arraysize = size

    def _check_closed(self) -> None:
        """Check if cursor is closed and raise exception if so."""
        if self._closed:
            raise InterfaceError("Cursor is closed")
        if self.connection._closed:
            raise InterfaceError("Connection is closed")

    def _parse_results(self, response: dict[str, Any]) -> None:
        """Parse query response and set cursor state.

        Args:
            response: Response from Restate SQL API

        """
        # Extract rows from response
        rows = response.get("rows", [])

        if not rows:
            self._description = []
            self._results = []
            self._rowcount = 0
            self._rownumber = 0
            return

        # Collect all unique column names across all rows
        all_columns = set()
        for row in rows:
            all_columns.update(row.keys())

        # Sort columns for consistent ordering
        columns = sorted(all_columns)

        # Build description tuple for each column
        self._description = []
        for col in columns:
            col_name = col
            col_type = "STRING"
            # DB-API description format: (name, type_code, display_size, internal_size, precision, scale, null_ok)
            self._description.append((col_name, col_type, None, None, None, None, True))

        # Convert rows to tuples, filling missing columns with None
        self._results = []
        for row in rows:
            row_tuple = tuple(row.get(col) for col in columns)
            self._results.append(row_tuple)

        self._rowcount = len(self._results)
        self._rownumber = 0

    def execute(
        self,
        operation: str,
        parameters: Sequence | dict[str, Any] | None = None,
    ) -> None:
        """Execute a database operation (query or command).

        Args:
            operation: SQL query string
            parameters: Parameters for the operation (not supported yet)

        """
        self._check_closed()

        if parameters:
            raise ProgrammingError("Parameterized queries not yet supported")

        try:
            response = self.connection._make_request(operation, parameters)
            self._parse_results(response)
        except Exception:
            # Reset cursor state on error
            self._results = None
            self._description = None
            self._rowcount = -1
            self._rownumber = 0
            raise

    def executemany(
        self,
        operation: str,
        seq_of_parameters: Sequence[Sequence | dict[str, Any]],
    ) -> None:
        """Execute a database operation repeatedly.

        Args:
            operation: SQL query string
            seq_of_parameters: Sequence of parameter sequences/dicts

        """
        self._check_closed()
        raise ProgrammingError("executemany not supported for read-only operations")

    def fetchone(self) -> tuple | None:
        """Fetch the next row of a query result set.

        Returns:
            Tuple representing the next row, or None if no more rows

        """
        self._check_closed()

        if self._results is None:
            raise ProgrammingError("No query has been executed")

        if self._rownumber >= len(self._results):
            return None

        row = self._results[self._rownumber]
        self._rownumber += 1
        return row

    def fetchmany(self, size: int | None = None) -> list[tuple]:
        """Fetch the next set of rows of a query result.

        Args:
            size: Number of rows to fetch (defaults to arraysize)

        Returns:
            List of tuples representing the rows

        """
        self._check_closed()

        if self._results is None:
            raise ProgrammingError("No query has been executed")

        if size is None:
            size = self._arraysize

        start = self._rownumber
        end = min(start + size, len(self._results))

        rows = self._results[start:end]
        self._rownumber = end

        return rows

    def fetchall(self) -> list[tuple]:
        """Fetch all remaining rows of a query result.

        Returns:
            List of tuples representing all remaining rows

        """
        self._check_closed()

        if self._results is None:
            raise ProgrammingError("No query has been executed")

        rows = self._results[self._rownumber :]
        self._rownumber = len(self._results)

        return rows

    def close(self) -> None:
        """Close the cursor."""
        self._closed = True
        self._results = None
        self._description = None
        self._rowcount = -1
        self._rownumber = 0

    def setinputsizes(self, sizes: Sequence[int | None]) -> None:
        """Predefine memory areas for parameters.

        This is a no-op for Restate SQL.
        """

    def setoutputsize(self, size: int, column: int | None = None) -> None:
        """Set a column buffer size for fetches.

        This is a no-op for Restate SQL.
        """

    def __iter__(self):
        """Iterator interface."""
        return self

    def __next__(self):
        """Iterator next method."""
        row = self.fetchone()
        if row is None:
            raise StopIteration
        return row

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def _repr_mimebundle_(self, include=None, exclude=None):
        """Return a rich table mimebundle representation of the cursor results."""
        if self._results is None or self._description is None:
            return None

        if not self._results:
            return None

        table = Table(show_header=True, header_style="bold magenta")

        # Add columns from description
        for col_desc in self._description:
            table.add_column(col_desc[0])  # Column name

        # Add rows
        for row in self._results:
            table.add_row(
                *[str(value) if value is not None else "NULL" for value in row],
            )

        return table._repr_mimebundle_(include=include, exclude=exclude)

    def df(self) -> pd.DataFrame:
        """Return query results as a pandas DataFrame.

        Returns:
            pandas.DataFrame: DataFrame containing the query results

        Raises:
            ProgrammingError: If no query has been executed

        """
        self._check_closed()

        if self._results is None or self._description is None:
            raise ProgrammingError("No query has been executed")

        if not self._results:
            # Return empty DataFrame with correct column names
            column_names = [col_desc[0] for col_desc in self._description]
            return pd.DataFrame(columns=column_names)

        # Extract column names from description
        column_names = [col_desc[0] for col_desc in self._description]

        # Create DataFrame from results
        return pd.DataFrame(self._results, columns=column_names)
