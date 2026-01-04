# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`cinemaquery` is a CLI tool to query the public Cineamo API. It provides commands to search cinemas, movies, and related data with rich table output or JSON formatting.

## Development Commands

### Setup
```bash
uv venv --seed
source .venv/bin/activate
uv pip install -e .
uv pip install -e ".[dev]"  # Install dev dependencies
```

### Code Quality
```bash
# Lint and format
ruff check .
ruff format .

# Type checking
mypy src
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_client.py -v

# CLI smoke test
cineamo --help
cineamo cinemas --per-page 1 --format json
```

**Test Suite:** The project has comprehensive test coverage with 46 tests across three test files:
- `tests/test_client.py` - 12 tests for CineamoClient (HAL-JSON parsing, pagination, streaming)
- `tests/test_cli.py` - 20 tests for CLI commands (all commands, formats, error handling)
- `tests/test_config.py` - 14 tests for configuration (precedence, persistence, operations)

**Test Patterns:**
- Use pytest fixtures for CineamoClient instances (`conftest.py`)
- Mock httpx responses for unit tests (avoiding real API calls)
- Test both single-page and `--all` streaming modes
- Verify Rich table output and JSON formatting
- Test error handling (404, 429, 500+ status codes, network errors)
- Test configuration precedence (CLI flags > env vars > config file > defaults)

### Running the CLI
```bash
# After installation in dev mode
cineamo --help

# Main entry point
python -m cinemaquery.cli

# Environment variables
CINEAMO_BASE_URL=https://custom-api.example.com cineamo cinemas
```

## Available Commands

### Cinema Commands
```bash
# List cinemas with filters
cineamo cinemas [--city <CITY>] [--per-page N] [--page N] [--all] [--limit N] [--format rich|table|json]

# Get single cinema detail
cineamo cinema --id <ID> [--format rich|json]

# Find cinemas near coordinates
cineamo cinemas-near --lat <LAT> --lon <LON> --distance <M> [--per-page N] [--all] [--limit N] [--format ...]

# List movies showing at a specific cinema
cineamo cinema-movies --cinema-id <ID> [--query Q] [--region R] [--per-page N] [--all] [--limit N] [--format ...]

# List showtimes/screenings for a cinema
# Default: shows only the specified date (single day)
cineamo showtimes --cinema-id <ID> [--date YYYY-MM-DD] [--per-page N] [--page N] [--format rich|table|json]

# With --all: shows all showtimes from date onwards (multiple days)
cineamo showtimes --cinema-id <ID> --date YYYY-MM-DD --all [--limit N] [--format rich|table|json]
```

### Movie Commands
```bash
# List movies with optional query
cineamo movies [--query Q] [--per-page N] [--page N] [--all] [--limit N] [--format ...]

# Advanced movie search
cineamo movies-search [--query Q] [--region R] [--release-date-start YYYY-MM-DD] [--release-date-end YYYY-MM-DD] [--type T] [--per-page N] [--all] [--limit N] [--format ...]

# Get single movie detail
cineamo movie --id <ID> [--format rich|json]
```

### Utility Commands
```bash
# Raw GET request to any API path
cineamo get /path -p key=value [-p key=value ...] [--format json|rich]

# Configuration management
cineamo config set <key> <value>
cineamo config get <key>
cineamo config show

# Shell completions
cineamo completions bash|zsh|fish
```

## Architecture

### Two-Layer Design

1. **Client Layer** (`src/cinemaquery/client.py`):
   - `CineamoClient`: Thin wrapper around httpx for API communication
   - Handles pagination via `list_paginated()` returning `Page` dataclass
   - Provides `stream_all()` iterator for fetching all pages automatically
   - HAL-JSON aware (handles `_embedded`, `_links`, `_page`, `_total_items`)
   - Error handling: Uses `raise_for_status()` to throw exceptions on HTTP errors

2. **CLI Layer** (`src/cinemaquery/cli.py`):
   - Click-based command structure with command groups
   - All commands share common options via `@click.pass_context`
   - Client instance created once in main group, passed to subcommands via context
   - Client cleanup handled in `@main.result_callback()` to ensure httpx client is properly closed
   - Configuration stored in `~/.config/cinemaquery/config.toml`

### Page Dataclass Structure

The `Page` dataclass (client.py:12-18) represents paginated API responses:
```python
@dataclass
class Page:
    items: list[dict[str, Any]]      # The actual data items
    total_items: int | None           # Total across all pages
    page: int | None                  # Current page number
    page_count: int | None            # Total number of pages
    next_url: str | None              # URL for next page (from HAL links)
```

### HAL-JSON Parsing Strategy

The API returns HAL-JSON format. `list_paginated()` extracts data by:
1. Looking in `_embedded` object for the first array value (different endpoints use different keys)
2. Extracting pagination metadata from `_page`, `_total_items`, `_page_count`
3. Getting next page link from `_links.next.href`

This automatic detection means adding new endpoints usually requires no client changes.

### Pagination Pattern

Commands support two pagination modes:
- **Single page**: `--page N --per-page M` (default)
- **Stream all**: `--all` flag with optional `--limit N`

When `--all` is used, the CLI calls `client.stream_all()` which automatically fetches pages until no `next` link exists. The `--limit` flag caps total items returned (useful for large datasets).

### Output Formatting

All list commands support `--format rich|table|json`:
- `rich`/`table`: Pretty Rich tables with colored columns
- `json`: Raw JSON for scripting

Config commands use TOML for persistence (tomli_w for writing, tomllib for reading on Python 3.11+).

### Configuration and Environment Variables

**Configuration file:** `~/.config/cinemaquery/config.toml`

**Environment variables:**
- `CINEAMO_BASE_URL` - Override API base URL

**Precedence order (highest to lowest):**
1. Command-line flags (e.g., `--base-url`)
2. Environment variables (e.g., `CINEAMO_BASE_URL`)
3. Config file values
4. Built-in defaults

The precedence logic in cli.py:40 uses Python's `or` operator:
```python
eff_base = base_url or cfg.get("base_url") or "https://api.cineamo.com"
```

**Note:** Empty strings from CLI flags may not work as expected due to this logic.

**Global Flags (currently unused):**
The `--verbose` and `--quiet` flags are defined but not yet implemented. They're stored in context but no code currently checks them.

### Shell Completions

Click's built-in completion system via environment variables:
- `_CINEAMO_COMPLETE=bash_complete cineamo`
- `_CINEAMO_COMPLETE=zsh_complete cineamo`
- `_CINEAMO_COMPLETE=fish_complete cineamo`

Access via `cineamo completions bash|zsh|fish` commands that output the appropriate eval line.

## Key Patterns

### Adding New API Endpoints

1. Add method to `CineamoClient` if the endpoint needs special handling (most don't)
2. Create Click command in `cli.py` following existing patterns
3. Use `client.list_paginated()` for paginated endpoints
4. Use `client.get_json()` for single-resource endpoints
5. Support both `--all` streaming and single-page modes for lists
6. Add Rich table formatting with appropriate columns
7. Support `--format json` output mode

**Example:** See `cinema-movies` command (cli.py:313-417) for a complete pattern showing:
- Optional filters (`--query`, `--region`)
- Both pagination modes (`--all` with `--limit`, or `--page`)
- Rich table and JSON output
- Proper typing and error handling

**Showtimes Command Pattern:**

The `showtimes` command demonstrates a date-range pattern:
- **Without `--all`**: Automatically sets `endDatetime` to limit results to a single day
- **With `--all`**: No `endDatetime` parameter, streams all showtimes from date onwards
- Uses `timedelta` to calculate end date (start + 1 day)
- API endpoint: `/showings?cinemaIds[]=<id>&startDatetime=<ISO8601>&endDatetime=<ISO8601>`
- Discovered via browser automation monitoring network requests on cineamo.com

This pattern can be reused for any time-range queries where users typically want single-day results but may need multi-day streaming.

### Configuration

Config keys can be set/read via:
```bash
cineamo config set base_url https://api.example.com
cineamo config get base_url
cineamo config show
```

Common config keys:
- `base_url` - API base URL (default: https://api.cineamo.com)
- `timeout` - Request timeout in seconds (default: 15.0)

### Error Handling

The client uses `httpx.Response.raise_for_status()` which throws:
- `httpx.HTTPStatusError` for 4xx/5xx responses
- `httpx.RequestError` for network issues

The CLI implements a `@handle_api_errors` decorator that catches these exceptions and provides user-friendly error messages:
- **404 errors**: "Resource not found"
- **429 errors**: "Rate limit exceeded. Please try again later."
- **500+ errors**: "Server error (XXX). Please try again later."
- **Network errors**: "Could not connect to API. Check your network connection."

When `--verbose` flag is used, full stack traces are shown for debugging.

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`):
- **Ruff linting** - Code style and quality checks
- **Mypy type checking** - Full strict type checking (requires tomli for Python 3.10 compatibility)
- **Pytest** - 46 tests across client, CLI, and config
- **CLI smoke test** - Basic functionality verification

The workflow runs on:
- Push to `main` branch
- Pull requests to `main`

**CI Dependencies:**
- `tomli` must be installed in CI for mypy to type-check the conditional import (Python 3.11+ uses stdlib `tomllib`, Python 3.10 uses `tomli`)

## Code Style

- Python 3.10+ with type hints (enforced by mypy strict mode)
- Ruff linting with rules: E, F, I, B, UP, SIM, PL, RUF (except PLR0913)
- Line length: 88 characters
- All functions must have type annotations (`disallow_untyped_defs = true`)
- Use `from __future__ import annotations` for forward references

## Best Practices and Lessons Learned

### Type Checking

**Mypy strict mode challenges and solutions:**

1. **httpx Response.json() returns Any**
   - **Problem**: `response.json()` returns `Any`, causing mypy errors when expecting `dict[str, Any]`
   - **Solution**: Use `cast(dict[str, Any], response.json())` to satisfy type checker
   - **Example**: `client.py:37`

2. **tomllib/tomli conditional import**
   - **Problem**: `tomllib` is Python 3.11+ stdlib, need `tomli` for 3.10
   - **Solution**: Conditional import with version check:
     ```python
     if sys.version_info >= (3, 11):
         import tomllib
     else:
         import tomli as tomllib
     ```
   - **Important**: CI must install `tomli` for mypy to type-check the import, even when running Python 3.12

3. **Dict type inference with mixed values**
   - **Problem**: `params = {"per_page": 10, "page": 1}` inferred as `dict[str, int]`, fails when adding string values
   - **Solution**: Explicitly annotate as `dict[str, Any]`: `params: dict[str, Any] = {...}`
   - **Example**: `cli.py:180, 430`

4. **Config file parsing**
   - **Problem**: `tomllib.load()` returns `Any`
   - **Solution**: Use `cast(dict[str, str], tomllib.load(f))` to specify expected type
   - **Example**: `cli.py:835`

### Testing

**Pytest patterns that worked well:**

1. **Shared fixtures in conftest.py**
   - Mock httpx.Client in one place, reuse across all tests
   - Sample data fixtures reduce duplication
   - Temporary config directories with proper cleanup

2. **Test organization**
   - Separate test files by component (client, cli, config)
   - Group related tests in classes (e.g., `TestCinemasCommand`)
   - Use descriptive test names: `test_cinemas_json_format`, not `test_1`

3. **Mocking strategies**
   - Mock at the httpx.Client level, not individual methods
   - Use `Mock(spec=...)` to catch attribute errors early
   - Return realistic HAL-JSON structures in mocks

4. **Per-file ignore rules**
   - Tests often need long lines and magic values
   - Add to `pyproject.toml`: `"tests/**/*.py" = ["E501", "PLR2004"]`

### Error Handling

**Decorator pattern for consistent error handling:**

1. **Benefits**
   - Single source of truth for error messages
   - Easy to apply to all commands
   - Centralized verbose/quiet handling

2. **Implementation**
   - Catch `httpx.HTTPStatusError` and `httpx.RequestError`
   - Extract context from Click context object
   - Use Rich console for colored error output
   - Show stack traces only with `--verbose`

### Configuration Precedence

**Explicit is better than implicit:**

1. **Problem with `or` chains**
   - `base_url or cfg.get("base_url") or default` fails with empty strings
   - Short-circuit evaluation doesn't work as expected

2. **Solution with explicit checks**
   ```python
   if base_url is not None:  # CLI flag
       eff_base = base_url
   elif "base_url" in cfg:  # Config file
       eff_base = cfg["base_url"]
   else:  # Default
       eff_base = "https://api.cineamo.com"
   ```
   - Use `None` as Click default, not hardcoded values
   - Check for `None` explicitly, not truthiness

### Pagination and Streaming

**HAL-JSON automatic detection:**

1. **Flexible embedded data extraction**
   - Don't hardcode `_embedded.cinemas` or `_embedded.movies`
   - Iterate through values, take first list found
   - Enables adding new endpoints without client changes

2. **Streaming implementation**
   - Use generators (`yield from`) for memory efficiency
   - Respect `--limit` flag by breaking early
   - Stop when `next_url` is None, not when items list is empty

## Troubleshooting

### Common Issues

**API Connection Errors:**
- Check base URL with `cineamo config get base_url`
- Test with raw GET: `cineamo get /cinemas -p per_page=1`
- Verify timeout setting (default 15s may be too short for slow connections)

**Pagination Issues:**
- The `--all` flag streaming stops when `_links.next` is missing from API response
- Use `--limit` with `--all` to cap results during testing
- Recent fix (commit cee9c4d): Avoid duplicate page when streaming with `--all`

**Type Errors:**
- Run `mypy src` to check before committing
- Ensure all function parameters and returns are typed
- Use `Any` from typing for dynamic API response data

**Config Not Loaded:**
- Check file exists at `~/.config/cinemaquery/config.toml`
- Verify TOML syntax with `cineamo config show`
- Remember CLI flags and env vars override config
