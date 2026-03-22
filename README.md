# cinemaquery

CLI tool to query the public Cineamo API with rich table output, JSON formatting, and an interactive TUI mode.

[![CI](https://github.com/jvanvinkenroye/cinemaquery/actions/workflows/ci.yml/badge.svg)](https://github.com/jvanvinkenroye/cinemaquery/actions/workflows/ci.yml)

## Quick Start (No Installation Required)

Run the tool directly with `uvx` without installing:

```bash
# Run from GitHub (always uses latest version)
uvx --from git+https://github.com/jvanvinkenroye/cinemaquery cinemaquery --help

# Interactive mode (TUI with fuzzy search)
uvx --from git+https://github.com/jvanvinkenroye/cinemaquery cinemaquery interactive

# Get showtimes for a cinema
uvx --from git+https://github.com/jvanvinkenroye/cinemaquery cinemaquery showtimes --cinema-id 781

# Run from local directory (for development)
uvx --from . cinemaquery --help
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
uv tool install git+https://github.com/jvanvinkenroye/cinemaquery
```

After installation, the `cinemaquery` command is available globally.

### Using pip

```bash
pip install git+https://github.com/jvanvinkenroye/cinemaquery
```

## Usage Examples

```bash
# Interactive TUI mode (recommended for exploration)
cinemaquery interactive
cinemaquery interactive --type cinema  # start directly with cinema search
cinemaquery interactive --type movie   # start directly with movie search
cinemaquery i                          # short alias

# List cinemas in Berlin
cinemaquery cinemas --city Berlin --per-page 5

# Search for movies
cinemaquery movies --query Dune --per-page 5

# Get detailed cinema info
cinemaquery cinema --id 123

# Get showtimes for a cinema (single day)
cinemaquery showtimes --cinema-id 781 --date 2026-01-04

# Get all showtimes from a date onwards
cinemaquery showtimes --cinema-id 781 --date 2026-01-04 --all

# Enable verbose logging
cinemaquery --verbose cinemas --city Paris
```

## Commands

### Interactive Mode
- `cinemaquery interactive [--type cinema|movie]` - Interactive TUI with fuzzy search menus
- `cinemaquery i` - Short alias for interactive mode

**Keyboard shortcuts in interactive mode:**
- `[c]` - Search cinemas
- `[m]` - Search movies
- `[b]` - Back to previous menu
- `[d]` - Show details
- `[q]` / `Ctrl+C` - Quit

**Workflows:**
- **Cinema workflow:** Search by city → select cinema → view showtimes, movies, or details
- **Movie workflow:** Search by title → select movie → find cinemas showing it → view showtimes

### Cinema Commands
- `cinemaquery cinemas [--city <CITY>] [--per-page N] [--page N] [--all] [--limit N] [--format rich|table|json]` - List cinemas with optional filters
- `cinemaquery cinema --id <ID> [--format rich|json]` - Get single cinema detail
- `cinemaquery cinemas-near --lat <LAT> --lon <LON> --distance <M> [...]` - Find cinemas near coordinates
- `cinemaquery cinema-movies --cinema-id <ID> [--query Q] [--region R] [...]` - List movies at a cinema
- `cinemaquery showtimes --cinema-id <ID> [--date YYYY-MM-DD] [--per-page N] [--page N] [--all] [--limit N] [--format rich|table|json]` - List showtimes for a cinema (single day by default, use `--all` for multiple days)

### Movie Commands
- `cinemaquery movies [--query Q] [--per-page N] [--page N] [--all] [--limit N] [--format ...]` - List movies with optional query
- `cinemaquery movies-search [--query Q] [--region R] [--release-date-start YYYY-MM-DD] [...]` - Advanced movie search
- `cinemaquery movie --id <ID> [--format rich|json]` - Get single movie detail

### Utility Commands
- `cinemaquery get /path -p key=value [-p key=value ...] [--format json|rich]` - Raw GET request to any API path
- `cinemaquery config set <key> <value>` - Set configuration value
- `cinemaquery config get <key>` - Get configuration value
- `cinemaquery config show` - Show all configuration

### Global Flags
- `--verbose` - Enable debug logging
- `--quiet` - Suppress warnings (errors only)
- `--base-url <URL>` - Override API base URL
- `--timeout <SECONDS>` - Set request timeout

## Configuration

Configuration is stored in `~/.config/cinemaquery/config.toml`.

**Precedence (highest to lowest):**
1. Command-line flags (e.g., `--base-url`)
2. Environment variables (e.g., `CINEAMO_BASE_URL`)
3. Config file values
4. Built-in defaults

**Example:**
```bash
# Set custom API URL
cinemaquery config set base_url https://api.example.com

# Override with environment variable
CINEAMO_BASE_URL=https://test.api.com cinemaquery cinemas

# Override with CLI flag (highest priority)
cinemaquery --base-url https://dev.api.com cinemas
```

## Shell Completions

```bash
# Bash
echo 'eval "$(_CINEMAQUERY_COMPLETE=bash_complete cinemaquery)"' >> ~/.bashrc

# Zsh
echo 'eval "$(_CINEMAQUERY_COMPLETE=zsh_complete cinemaquery)"' >> ~/.zshrc

# Fish
echo 'eval (env _CINEMAQUERY_COMPLETE=fish_complete cinemaquery)' >> ~/.config/fish/config.fish
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
- Pytest (67 tests)
- CLI smoke test

## Troubleshooting

### uvx fails with "Git operation failed"

If `uvx --from git+https://...` fails on your system, try these alternatives:

**Option 1: Install permanently with uv tool**
```bash
uv tool install git+https://github.com/jvanvinkenroye/cinemaquery
cinemaquery --help
```

**Option 2: Use pip**
```bash
pip install git+https://github.com/jvanvinkenroye/cinemaquery
cinemaquery --help
```

**Option 3: Clone and install locally**
```bash
git clone https://github.com/jvanvinkenroye/cinemaquery.git
cd cinemaquery
uv tool install .
# or: pip install .
```

**Common causes:**
- Git not installed on the system
- Network/firewall blocking GitHub access
- Corporate proxy settings

## Features

- ✅ Interactive TUI mode with fuzzy search menus
- ✅ Rich table output with colored columns
- ✅ JSON output for scripting
- ✅ Automatic pagination with `--all` flag
- ✅ Single-day showtimes by default, multi-day with `--all`
- ✅ Configurable API base URL and timeout
- ✅ User-friendly error messages
- ✅ Verbose/quiet logging modes
- ✅ Shell completions for Bash/Zsh/Fish
- ✅ Date range queries with `--end-date`
- ✅ Comprehensive test suite (72 tests)
- ✅ Full type checking with mypy
- ✅ Python 3.10+ compatibility

## Claude Code Skill

cinemaquery can be used as a [Claude Code](https://claude.ai/code) skill, allowing Claude to answer natural-language cinema queries automatically.

### Installation

```bash
mkdir -p ~/.claude/skills/cinemaquery
curl -o ~/.claude/skills/cinemaquery/SKILL.md \
  https://raw.githubusercontent.com/jvanvinkenroye/cinemaquery/main/skill/SKILL.md
```

Or create `~/.claude/skills/cinemaquery/SKILL.md` manually — see [`skill/SKILL.md`](skill/SKILL.md) for the content.

### Usage

Once installed, Claude detects cinema-related questions automatically:

> "Was läuft diese Woche im Kino in Stuttgart?"
> "Was kommt nächste Woche im Corso?"
> "Um was geht es bei Gelbe Briefe?"

Claude will run the appropriate `cinemaquery` commands and present the results in a readable format.
