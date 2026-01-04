# cineamoquery

CLI tool to query the public Cineamo API with rich table output and JSON formatting.

[![CI](https://github.com/jvanvinkenroye/cineamoquery/actions/workflows/ci.yml/badge.svg)](https://github.com/jvanvinkenroye/cineamoquery/actions/workflows/ci.yml)

## Quick Start (No Installation Required)

Run the tool directly with `uvx` without installing:

```bash
# Run from GitHub (always uses latest version)
uvx --from git+https://github.com/jvanvinkenroye/cineamoquery cineamo --help

# Get showtimes for a cinema
uvx --from git+https://github.com/jvanvinkenroye/cineamoquery cineamo showtimes --cinema-id 781

# List cinemas in a city
uvx --from git+https://github.com/jvanvinkenroye/cineamoquery cineamo cinemas --city Berlin --per-page 5

# Run from local directory (for development)
uvx --from . cineamo --help
```

**Note:** The `uvx` command downloads and runs the tool in an isolated environment without installing it globally. Perfect for trying it out or running occasionally.

## Setup

```bash
uv venv --seed
source .venv/bin/activate
uv pip install -e .
```

For development:
```bash
uv pip install -e ".[dev]"
```

## Installation Methods

### Using uv tool (recommended for regular use)

```bash
uv tool install git+https://github.com/jvanvinkenroye/cineamoquery
```

After installation, the `cineamo` command is available globally.

### Using pip

```bash
pip install git+https://github.com/jvanvinkenroye/cineamoquery
```

## Usage Examples

```bash
# Get help
cineamo --help

# List cinemas in Berlin
cineamo cinemas --city Berlin --per-page 5

# Search for movies
cineamo movies --query Dune --per-page 5

# Get detailed cinema info
cineamo cinema --id 123

# Get showtimes for a cinema (single day)
cineamo showtimes --cinema-id 781 --date 2026-01-04

# Get all showtimes from a date onwards
cineamo showtimes --cinema-id 781 --date 2026-01-04 --all

# Enable verbose logging
cineamo --verbose cinemas --city Paris
```

## Commands

### Cinema Commands
- `cineamo cinemas [--city <CITY>] [--per-page N] [--page N] [--all] [--limit N] [--format rich|table|json]` - List cinemas with optional filters
- `cineamo cinema --id <ID> [--format rich|json]` - Get single cinema detail
- `cineamo cinemas-near --lat <LAT> --lon <LON> --distance <M> [...]` - Find cinemas near coordinates
- `cineamo cinema-movies --cinema-id <ID> [--query Q] [--region R] [...]` - List movies at a cinema
- `cineamo showtimes --cinema-id <ID> [--date YYYY-MM-DD] [--per-page N] [--page N] [--all] [--limit N] [--format rich|table|json]` - List showtimes for a cinema (single day by default, use `--all` for multiple days)

### Movie Commands
- `cineamo movies [--query Q] [--per-page N] [--page N] [--all] [--limit N] [--format ...]` - List movies with optional query
- `cineamo movies-search [--query Q] [--region R] [--release-date-start YYYY-MM-DD] [...]` - Advanced movie search
- `cineamo movie --id <ID> [--format rich|json]` - Get single movie detail

### Utility Commands
- `cineamo get /path -p key=value [-p key=value ...] [--format json|rich]` - Raw GET request to any API path
- `cineamo config set <key> <value>` - Set configuration value
- `cineamo config get <key>` - Get configuration value
- `cineamo config show` - Show all configuration

### Global Flags
- `--verbose` - Enable debug logging
- `--quiet` - Suppress warnings (errors only)
- `--base-url <URL>` - Override API base URL
- `--timeout <SECONDS>` - Set request timeout

## Configuration

Configuration is stored in `~/.config/cineamoquery/config.toml`.

**Precedence (highest to lowest):**
1. Command-line flags (e.g., `--base-url`)
2. Environment variables (e.g., `CINEAMO_BASE_URL`)
3. Config file values
4. Built-in defaults

**Example:**
```bash
# Set custom API URL
cineamo config set base_url https://api.example.com

# Override with environment variable
CINEAMO_BASE_URL=https://test.api.com cineamo cinemas

# Override with CLI flag (highest priority)
cineamo --base-url https://dev.api.com cinemas
```

## Shell Completions

```bash
# Bash
echo 'eval "$(_CINEAMO_COMPLETE=bash_complete cineamo)"' >> ~/.bashrc

# Zsh
echo 'eval "$(_CINEAMO_COMPLETE=zsh_complete cineamo)"' >> ~/.zshrc

# Fish
echo 'eval (env _CINEAMO_COMPLETE=fish_complete cineamo)' >> ~/.config/fish/config.fish
```

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Code Quality
```bash
# Lint and format
ruff check .
ruff format .

# Type checking
mypy src
```

### CI/CD
GitHub Actions runs:
- Ruff linting
- Mypy type checking
- Pytest (46 tests)
- CLI smoke test

## Features

- ✅ Rich table output with colored columns
- ✅ JSON output for scripting
- ✅ Automatic pagination with `--all` flag
- ✅ Configurable API base URL and timeout
- ✅ User-friendly error messages
- ✅ Verbose/quiet logging modes
- ✅ Shell completions for Bash/Zsh/Fish
- ✅ Comprehensive test suite (46 tests)
- ✅ Full type checking with mypy
- ✅ Python 3.10+ compatibility
