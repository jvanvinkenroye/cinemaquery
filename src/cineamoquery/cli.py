from __future__ import annotations

import json

import click
from rich.console import Console
from rich.table import Table

from .client import CineamoClient

console = Console()


@click.group()
@click.option("--base-url", envvar="CINEAMO_BASE_URL", default="https://api.cineamo.com", help="API base URL")
@click.option("--timeout", type=float, default=15.0, show_default=True, help="Request timeout seconds")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("-q", "--quiet", is_flag=True, help="Quiet output")
@click.pass_context
def main(ctx: click.Context, base_url: str, timeout: float, verbose: bool, quiet: bool) -> None:
    """Cineamo API command-line tool."""
    ctx.ensure_object(dict)
    ctx.obj["client"] = CineamoClient(base_url=base_url, timeout=timeout)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet


@main.command("cinemas")
@click.option("--city", type=str, help="Filter by city")
@click.option("--per-page", type=int, default=10, show_default=True)
@click.option("--page", type=int, default=1, show_default=True)
@click.option("--all", "list_all", is_flag=True, help="Stream all pages")
@click.option(
    "--limit",
    type=int,
    default=0,
    show_default=False,
    help="Maximum items when using --all (0 = no limit)",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "rich", "json"], case_sensitive=False),
    default="rich",
    show_default=True,
    help="Output format",
)
@click.pass_context
def list_cinemas(
    ctx: click.Context,
    city: str | None,
    per_page: int,
    page: int,
    list_all: bool,
    limit: int,
    fmt: str,
) -> None:
    """List cinemas with optional filters."""
    client: CineamoClient = ctx.obj["client"]
    params = {"per_page": per_page, "page": page}
    if city:
        params["city"] = city
    if list_all:
        count = 0
        rows = []
        for c in client.stream_all("/cinemas", per_page=per_page, **params):
            rows.append((str(c.get("id", "")), str(c.get("name", "")), str(c.get("city", "")), str(c.get("countryCode", ""))))
            count += 1
            if limit and count >= limit:
                break
        if fmt.lower() == "json":
            click.echo(json.dumps({"items": rows, "total": count}, ensure_ascii=False, indent=2))
            return
        table = Table(
            title=f"Cinemas (total {count})",
            header_style="bold cyan",
            show_lines=False,
        )
        table.add_column("ID", justify="right", style="magenta", no_wrap=True)
        table.add_column("Name", style="bold")
        table.add_column("City", style="green")
        table.add_column("Country", style="yellow")
        for r in rows:
            table.add_row(*r)
        console.print(table)
        return

    result = client.list_paginated("/cinemas", **params)
    if fmt.lower() == "json":
        click.echo(json.dumps({"items": result.items, "page": result.page, "total": result.total_items}, ensure_ascii=False, indent=2))
        return
    table = Table(
        title=f"Cinemas page {result.page}", header_style="bold cyan", show_lines=False
    )
    table.add_column("ID", justify="right", style="magenta", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("City", style="green")
    table.add_column("Country", style="yellow")
    for c in result.items:
        table.add_row(str(c.get("id", "")), str(c.get("name", "")), str(c.get("city", "")), str(c.get("countryCode", "")))
    console.print(table)


@main.command("cinema")
@click.option("--id", "cinema_id", type=int, required=True, help="Cinema ID")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["rich", "json"], case_sensitive=False),
    default="rich",
    show_default=True,
    help="Output format",
)
@click.pass_context
def get_cinema(ctx: click.Context, cinema_id: int, fmt: str) -> None:
    """Get a single cinema by ID."""
    client: CineamoClient = ctx.obj["client"]
    data = client.get_json(f"/cinemas/{cinema_id}")
    if fmt == "json":
        click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return
    table = Table(title=f"Cinema {cinema_id}", header_style="bold cyan")
    table.add_column("Field", style="magenta", no_wrap=True)
    table.add_column("Value")
    for key in ("id", "name", "city", "countryCode", "slug", "ticketSystem", "email"):
        table.add_row(key, str(data.get(key, "")))
    console.print(table)


@main.command("cinemas-near")
@click.option("--lat", type=float, required=True, help="Latitude")
@click.option("--lon", type=float, required=True, help="Longitude")
@click.option("--distance", type=int, required=True, help="Distance in meters")
@click.option("--per-page", type=int, default=10, show_default=True)
@click.option("--page", type=int, default=1, show_default=True)
@click.option("--all", "list_all", is_flag=True, help="Stream all pages")
@click.option("--limit", type=int, default=0, show_default=False, help="Maximum items when using --all (0 = no limit)")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "rich", "json"], case_sensitive=False),
    default="rich",
    show_default=True,
    help="Output format",
)
@click.pass_context
def cinemas_near(
    ctx: click.Context,
    lat: float,
    lon: float,
    distance: int,
    per_page: int,
    page: int,
    list_all: bool,
    limit: int,
    fmt: str,
) -> None:
    """Search cinemas nearby coordinates."""
    client: CineamoClient = ctx.obj["client"]
    params = {
        "latitude": lat,
        "longitude": lon,
        "distance": distance,
        "per_page": per_page,
        "page": page,
    }
    if list_all:
        count = 0
        rows: list[tuple[str, str, str, str]] = []
        for c in client.stream_all("/cinemas", **params):
            rows.append((str(c.get("id", "")), str(c.get("name", "")), str(c.get("city", "")), str(c.get("countryCode", ""))))
            count += 1
            if limit and count >= limit:
                break
        if fmt.lower() == "json":
            click.echo(json.dumps({"items": rows, "total": count}, ensure_ascii=False, indent=2))
            return
        table = Table(title=f"Cinemas near ({lat},{lon}) total {count}", header_style="bold cyan", show_lines=False)
        table.add_column("ID", justify="right", style="magenta", no_wrap=True)
        table.add_column("Name", style="bold")
        table.add_column("City", style="green")
        table.add_column("Country", style="yellow")
        for r in rows:
            table.add_row(*r)
        console.print(table)
        return

    result = client.list_paginated("/cinemas", **params)
    if fmt.lower() == "json":
        click.echo(json.dumps({"items": result.items, "page": result.page, "total": result.total_items}, ensure_ascii=False, indent=2))
        return
    table = Table(title=f"Cinemas near ({lat},{lon}) page {result.page}", header_style="bold cyan", show_lines=False)
    table.add_column("ID", justify="right", style="magenta", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("City", style="green")
    table.add_column("Country", style="yellow")
    for c in result.items:
        table.add_row(str(c.get("id", "")), str(c.get("name", "")), str(c.get("city", "")), str(c.get("countryCode", "")))
    console.print(table)


@main.command("movies")
@click.option("--query", type=str, help="Search string")
@click.option("--per-page", type=int, default=10, show_default=True)
@click.option("--page", type=int, default=1, show_default=True)
@click.option("--all", "list_all", is_flag=True, help="Stream all pages")
@click.option(
    "--limit",
    type=int,
    default=0,
    show_default=False,
    help="Maximum items when using --all (0 = no limit)",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "rich", "json"], case_sensitive=False),
    default="rich",
    show_default=True,
    help="Output format",
)
@click.pass_context
def list_movies(
    ctx: click.Context,
    query: str | None,
    per_page: int,
    page: int,
    list_all: bool,
    limit: int,
    fmt: str,
) -> None:
    """List movies with optional query."""
    client: CineamoClient = ctx.obj["client"]
    params = {"per_page": per_page, "page": page}
    if query:
        params["query"] = query
    if list_all:
        count = 0
        rows = []
        for m in client.stream_all("/movies", per_page=per_page, **params):
            rows.append((str(m.get("id", "")), str(m.get("title", "")), str(m.get("releaseDate", "")), str(m.get("region", ""))))
            count += 1
            if limit and count >= limit:
                break
        if fmt.lower() == "json":
            click.echo(json.dumps({"items": rows, "total": count}, ensure_ascii=False, indent=2))
            return
        table = Table(
            title=f"Movies (total {count})",
            header_style="bold cyan",
            show_lines=False,
        )
        table.add_column("ID", justify="right", style="magenta", no_wrap=True)
        table.add_column("Title", style="bold")
        table.add_column("Release", style="green")
        table.add_column("Region", style="yellow")
        for r in rows:
            table.add_row(*r)
        console.print(table)
        return

    result = client.list_paginated("/movies", **params)
    if fmt.lower() == "json":
        click.echo(json.dumps({"items": result.items, "page": result.page, "total": result.total_items}, ensure_ascii=False, indent=2))
        return
    table = Table(
        title=f"Movies page {result.page}", header_style="bold cyan", show_lines=False
    )
    table.add_column("ID", justify="right", style="magenta", no_wrap=True)
    table.add_column("Title", style="bold")
    table.add_column("Release", style="green")
    table.add_column("Region", style="yellow")
    for m in result.items:
        table.add_row(str(m.get("id", "")), str(m.get("title", "")), str(m.get("releaseDate", "")), str(m.get("region", "")))
    console.print(table)


@main.command("movies-search")
@click.option("--query", type=str, help="Search string")
@click.option("--region", type=str, help="Region code")
@click.option("--release-date-start", type=str, help="YYYY-MM-DD")
@click.option("--release-date-end", type=str, help="YYYY-MM-DD")
@click.option("--type", "movie_type", type=str, help="Movie type filter")
@click.option("--per-page", type=int, default=10, show_default=True)
@click.option("--page", type=int, default=1, show_default=True)
@click.option("--all", "list_all", is_flag=True, help="Stream all pages")
@click.option(
    "--limit",
    type=int,
    default=0,
    show_default=False,
    help="Maximum items when using --all (0 = no limit)",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["table", "rich", "json"], case_sensitive=False),
    default="rich",
    show_default=True,
    help="Output format",
)
@click.pass_context
def movies_search(
    ctx: click.Context,
    query: str | None,
    region: str | None,
    release_date_start: str | None,
    release_date_end: str | None,
    movie_type: str | None,
    per_page: int,
    page: int,
    list_all: bool,
    limit: int,
    fmt: str,
) -> None:
    """Search movies with advanced filters."""
    client: CineamoClient = ctx.obj["client"]
    params: dict[str, str | int] = {"per_page": per_page, "page": page}
    if query:
        params["query"] = query
    if region:
        params["region"] = region
    if release_date_start:
        params["releaseDateStart"] = release_date_start
    if release_date_end:
        params["releaseDateEnd"] = release_date_end
    if movie_type:
        params["type"] = movie_type

    if list_all:
        count = 0
        rows: list[tuple[str, str, str, str]] = []
        for m in client.stream_all("/movies", **params):
            rows.append((str(m.get("id", "")), str(m.get("title", "")), str(m.get("releaseDate", "")), str(m.get("region", ""))))
            count += 1
            if limit and count >= limit:
                break
        if fmt.lower() == "json":
            click.echo(json.dumps({"items": rows, "total": count}, ensure_ascii=False, indent=2))
            return
        table = Table(title=f"Movies search (total {count})", header_style="bold cyan", show_lines=False)
        table.add_column("ID", justify="right", style="magenta", no_wrap=True)
        table.add_column("Title", style="bold")
        table.add_column("Release", style="green")
        table.add_column("Region", style="yellow")
        for r in rows:
            table.add_row(*r)
        console.print(table)
        return

    result = client.list_paginated("/movies", **params)
    if fmt.lower() == "json":
        click.echo(json.dumps({"items": result.items, "page": result.page, "total": result.total_items}, ensure_ascii=False, indent=2))
        return
    table = Table(title=f"Movies search page {result.page}", header_style="bold cyan", show_lines=False)
    table.add_column("ID", justify="right", style="magenta", no_wrap=True)
    table.add_column("Title", style="bold")
    table.add_column("Release", style="green")
    table.add_column("Region", style="yellow")
    for m in result.items:
        table.add_row(str(m.get("id", "")), str(m.get("title", "")), str(m.get("releaseDate", "")), str(m.get("region", "")))
    console.print(table)


@main.command("movie")
@click.option("--id", "movie_id", type=int, required=True, help="Movie ID")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["rich", "json"], case_sensitive=False),
    default="rich",
    show_default=True,
    help="Output format",
)
@click.pass_context
def get_movie(ctx: click.Context, movie_id: int, fmt: str) -> None:
    """Get a single movie by ID."""
    client: CineamoClient = ctx.obj["client"]
    data = client.get_json(f"/movies/{movie_id}")
    if fmt == "json":
        click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return
    table = Table(title=f"Movie {movie_id}", header_style="bold cyan")
    table.add_column("Field", style="magenta", no_wrap=True)
    table.add_column("Value")
    for key in ("id", "title", "region", "releaseDate", "runtime", "imdbId"):
        table.add_row(key, str(data.get(key, "")))
    console.print(table)


@main.result_callback()
@click.pass_context
def finalize(ctx: click.Context, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
    client: CineamoClient = ctx.obj.get("client")
    if client:
        client.close()


@main.command("get")
@click.argument("path", type=str)
@click.option("-p", "params", multiple=True, help="Query param key=value (repeat)")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["rich", "json"], case_sensitive=False),
    default="json",
    show_default=True,
    help="Output format",
)
@click.pass_context
def raw_get(ctx: click.Context, path: str, params: tuple[str, ...], fmt: str) -> None:
    """Generic GET for any API path (starting with '/')."""
    if not path.startswith("/"):
        raise click.UsageError("path must start with '/'")
    client: CineamoClient = ctx.obj["client"]
    qp: dict[str, str] = {}
    for p in params:
        if "=" not in p:
            raise click.UsageError("-p expects key=value")
        k, v = p.split("=", 1)
        qp[k] = v
    data = client.get_json(path, **qp)
    if fmt == "json":
        click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return
    # simple rich key-value table where possible
    if isinstance(data, dict):
        table = Table(title=f"GET {path}", header_style="bold cyan")
        table.add_column("Key", style="magenta", no_wrap=True)
        table.add_column("Value")
        for k, v in data.items():
            table.add_row(str(k), str(v))
        console.print(table)
    else:
        click.echo(json.dumps(data, ensure_ascii=False, indent=2))


@main.group()
def config() -> None:
    """Manage cineamoquery configuration."""


def _config_path() -> str:
    import os

    base = os.path.join(os.path.expanduser("~"), ".config", "cineamoquery")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "config.toml")


def _load_config() -> dict[str, str]:
    import tomllib
    import os

    path = _config_path()
    if not os.path.exists(path):
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def _save_config(cfg: dict[str, str]) -> None:
    import tomli_w

    with open(_config_path(), "wb") as f:
        f.write(tomli_w.dumps(cfg).encode())


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    cfg = _load_config()
    cfg[key] = value
    _save_config(cfg)
    click.echo(f"Set {key}")


@config.command("get")
@click.argument("key")
def config_get(key: str) -> None:
    cfg = _load_config()
    click.echo(cfg.get(key, ""))


@config.command("show")
def config_show() -> None:
    cfg = _load_config()
    click.echo(json.dumps(cfg, ensure_ascii=False, indent=2))
