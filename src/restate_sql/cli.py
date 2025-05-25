#!/usr/bin/env python3
"""Command-line interface for Restate SQL.

Provides a CLI tool to execute SQL queries against Restate's SQL introspection API
and display results in a formatted table.
"""

import os
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

import restate_sql

app = typer.Typer(help="Execute SQL queries against Restate's SQL introspection API")
console = Console()


def create_table_from_cursor(cursor) -> Table | None:
    """Create a Rich table from cursor results."""
    if not cursor.description:
        return None

    table = Table(show_header=True, header_style="bold magenta")

    # Add columns from cursor description
    for desc in cursor.description:
        table.add_column(desc[0])

    # Add rows
    for row in cursor.fetchall():
        table.add_row(*[str(col) if col is not None else "" for col in row])

    return table


def execute_query(url: str, query: str) -> None:
    """Execute a SQL query and display results."""
    try:
        with restate_sql.connect(url) as conn, conn.cursor() as cursor:
            cursor.execute(query)

            table = create_table_from_cursor(cursor)
            if table:
                console.print(table)
            else:
                # No results to display (e.g., INSERT/UPDATE/DELETE)
                console.print("[green]Query executed successfully.[/green]")

    except restate_sql.Error as e:
        console.print(f"[red]Database error: {e}[/red]", file=sys.stderr)
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]", file=sys.stderr)
        raise typer.Exit(1)


def get_query_text(stdin: bool, file: Path | None) -> str | None:
    if stdin:
        return sys.stdin.read().strip()
    if file:
        try:
            return file.read_text().strip()
        except FileNotFoundError:
            console.print(f"[red]Error: File '{file}' not found[/red]", file=sys.stderr)
            raise typer.Exit(1)
        except Exception as e:
            console.print(
                f"[red]Error reading file '{file}': {e}[/red]",
                file=sys.stderr,
            )
            raise typer.Exit(1)

    console.print(
        "[red]Error: Either provide a query as an argument, use --stdin, or use --file[/red]",
        file=sys.stderr,
    )
    raise typer.Exit(1)


@app.command()
def main(
    query: Annotated[str | None, typer.Argument(help="SQL query to execute")] = None,
    url: Annotated[str | None, typer.Option(help="Restate server URL")] = None,
    stdin: Annotated[
        bool,
        typer.Option("--stdin", help="Read query from stdin"),
    ] = False,
    file: Annotated[
        Path | None,
        typer.Option("--file", "-f", help="Read query from SQL file"),
    ] = None,
) -> None:
    """Execute SQL queries against Restate's SQL introspection API.

    Examples:
        restate-sql "SELECT * FROM sys_service" --url http://localhost:9070
        restate-sql "SELECT COUNT(*) FROM sys_invocation"
        restate-sql --file query.sql
        echo "SELECT name FROM sys_service" | restate-sql --stdin

    """
    # Get URL from environment variable or parameter
    if url:
        server_url = url
    else:
        host = os.getenv("RESTATE_HOST", "localhost")
        # Add protocol if not present
        if not host.startswith(("http://", "https://")):
            host = f"http://{host}"
        # Add port if not present
        if ":" not in host.split("//")[1]:
            host = f"{host}:9070"
        server_url = host

    # Determine query source
    query_sources = [stdin, file is not None, query is not None]
    if sum(query_sources) > 1:
        console.print(
            "[red]Error: Only one of query argument, --stdin, or --file can be used[/red]",
            file=sys.stderr,
        )
        raise typer.Exit(1)

    query_text = query if query else get_query_text(stdin, file)
    if not query_text:
        console.print("[red]Error: Query cannot be empty[/red]", file=sys.stderr)
        raise typer.Exit(1)
    execute_query(server_url, query_text)


if __name__ == "__main__":
    app()
