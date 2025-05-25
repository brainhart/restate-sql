"""DB-API 2.0 compatible Connection class for Restate SQL."""

import json
from typing import Any
from urllib.parse import urljoin

import httpx

from .cursor import Cursor
from .exceptions import DatabaseError, InterfaceError, OperationalError


def connect(base_url: str, **kwargs) -> "Connection":
    """Create a connection to Restate SQL introspection API.

    Args:
        base_url: Base URL for the Restate admin API (e.g., 'http://localhost:9070')
        **kwargs: Additional connection parameters

    Returns:
        Connection: A DB-API 2.0 compatible connection object

    """
    return Connection(base_url, **kwargs)


class Connection:
    """DB-API 2.0 compatible connection to Restate SQL introspection API."""

    def __init__(self, base_url: str, timeout: int = 30, **kwargs):
        """Initialize connection to Restate.

        Args:
            base_url: Base URL for the Restate admin API
            timeout: Request timeout in seconds
            **kwargs: Additional connection parameters

        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._closed = False
        self._client = httpx.Client(
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "accept": "application/json",
            },
        )

    def _make_request(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a SQL query request to Restate.

        Args:
            query: SQL query string
            parameters: Query parameters (not currently supported by Restate)

        Returns:
            Dict containing query results

        Raises:
            OperationalError: If the request fails

        """
        if self._closed:
            raise InterfaceError("Connection is closed")

        url = urljoin(self.base_url + "/", "query")
        payload = {"query": query}

        if parameters:
            # Note: Restate SQL may not support parameterized queries yet
            raise DatabaseError("Parameterized queries not supported")

        try:
            response = self._client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise OperationalError(f"Query failed: {e}")
        except httpx.RequestError as e:
            raise OperationalError(f"Request failed: {e}")
        except json.JSONDecodeError as e:
            raise DatabaseError(f"Invalid response format: {e}")

    def cursor(self) -> Cursor:
        """Create a new cursor object using the connection.

        Returns:
            Cursor: A new cursor object

        """
        if self._closed:
            raise InterfaceError("Connection is closed")
        return Cursor(self)

    def sql(self, query: str) -> ...:
        if self._closed:
            raise InterfaceError("Connection is closed")
        cur = Cursor(self)
        cur.execute(query)
        return cur

    def close(self) -> None:
        """Close the connection."""
        if not self._closed:
            self._client.close()
        self._closed = True

    def commit(self) -> None:
        """Commit any pending transaction.

        Note: Restate SQL introspection is read-only, so this is a no-op.
        """
        if self._closed:
            raise InterfaceError("Connection is closed")
        # No-op for read-only connection

    def rollback(self) -> None:
        """Rollback any pending transaction.

        Note: Restate SQL introspection is read-only, so this is a no-op.
        """
        if self._closed:
            raise InterfaceError("Connection is closed")
        # No-op for read-only connection

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
