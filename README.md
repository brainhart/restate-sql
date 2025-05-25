# Restate SQL

A Python DB-API 2.0 compatible interface for querying Restate's SQL introspection API.

## Overview

`restate-sql` provides a standard Python database interface to query Restate's built-in SQL introspection capabilities. Using familiar tools like Pandas, DuckDB, and Jupyter, you can explore services, invocations, state, and other system information through SQL queries.

## Features

- **DB-API 2.0 Compatible**: Standard Python database interface
- **Rich Table Outputs**: Interactive command-line tool with formatted output
- **Jupyter Integration**: Works seamlessly with JupySQL and pandas

## Installation

```bash
pip install git+https://github.com/brainhart/restate-sql.git
```

## Quick Start

### Command Line Interface

Execute SQL queries directly from the command line:

```bash
# Query services
restate-sql --url http://localhost:9070 --query "SELECT * FROM sys_service"

# Interactive mode
restate-sql --url http://localhost:9070
```

### Jupyter Notebooks

Works great with JupySQL for data exploration:

```python
import restate_sql
conn = restate_sql.connect("http://localhost:9070")

%load_ext sql
%sql conn

%%sql
SELECT 
    target_service_name,
    COUNT(*) as invocation_count
FROM sys_invocation 
GROUP BY target_service_name
ORDER BY invocation_count DESC
```

## Available System Tables

Restate exposes several system tables for introspection:

- `state` - Service state entries
- `sys_service` - Registered services and their metadata
- `sys_invocation` - Service invocations and their status
- `sys_keyed_service_status` - Status of keyed services
- `sys_inbox` - Pending invocations in service inboxes

## Configuration

### Environment Variables

- `RESTATE_URL` - Default Restate instance URL
- `RESTATE_TIMEOUT` - Connection timeout in seconds (default: 30)

### Connection Parameters

```python
conn = restate_sql.connect("http://localhost:9070")
```

## Examples

### Service Health Monitoring

```python
conn.sql("""
SELECT 
    s.name as service_name,
    COUNT(i.id) as total_invocations,
    COUNT(CASE WHEN i.status = 'completed' THEN 1 END) as completed,
    COUNT(CASE WHEN i.status = 'failed' THEN 1 END) as failed
FROM sys_service s
LEFT JOIN sys_invocation i ON s.name = i.target_service_name
GROUP BY s.name
ORDER BY total_invocations DESC
""")
```

### State Analysis

```python
conn.sql("""
SELECT 
    service_name,
    COUNT(*) as state_entries,
    AVG(LENGTH(value)) as avg_value_size
FROM state 
GROUP BY service_name
""")
```

## Development

### Setup

```bash
git clone https://github.com/brainhart/restate-sql-python
cd restate-sql-python
uv sync
```

### Running Examples

```bash
uv run python example.py
```

### Linting

```bash
uv run ruff check
uv run ruff format
```

## Requirements

- Python 3.11+
- Restate instance with SQL introspection enabled

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
