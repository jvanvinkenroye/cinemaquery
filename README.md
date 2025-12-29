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

Dev
- ruff check . && ruff format .
- mypy src

