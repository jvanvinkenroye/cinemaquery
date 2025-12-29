# cineamoquery

CLI to query the public Cineamo API.

Setup (uv)
- uv venv --seed
- source .venv/bin/activate
- uv add click httpx rich
- uv add -D ruff mypy pytest pytest-playwright

Run
- cineamo --help
- cineamo cinemas --city Berlin --per-page 5
- cineamo movies --query Dune --per-page 5

Commands
- List cinemas: `cineamo cinemas [--city <CITY>] [--per-page N] [--page N] [--all] [--limit N] [--format rich|table|json]`
- Cinema detail: `cineamo cinema --id <ID> [--format rich|json]`
- Cinemas near: `cineamo cinemas-near --lat <LAT> --lon <LON> --distance <M> [--per-page N] [--all] [--limit N] [--format ...]`
- List movies: `cineamo movies [--query Q] [--per-page N] [--page N] [--all] [--limit N] [--format ...]`
- Movies search: `cineamo movies-search [--query Q] [--region R] [--release-date-start YYYY-MM-DD] [--release-date-end YYYY-MM-DD] [--type T] [--per-page N] [--all] [--limit N] [--format ...]`
- Movie detail: `cineamo movie --id <ID> [--format rich|json]`
- Raw GET: `cineamo get /path -p key=value [-p key=value ...] [--format json|rich]`
- Config: `cineamo config set/get/show`

Completions
- Bash: `echo 'eval "$( _CINEAMO_COMPLETE=bash_complete cineamo )"' >> ~/.bashrc`
- Zsh: `echo 'eval "$( _CINEAMO_COMPLETE=zsh_complete cineamo )"' >> ~/.zshrc`
- Fish: `echo 'eval ( env _CINEAMO_COMPLETE=fish_complete cineamo )' >> ~/.config/fish/config.fish`

CI
- GitHub Actions: ruff + mypy + CLI smoke

Dev
- ruff check . && ruff format .
- mypy src
