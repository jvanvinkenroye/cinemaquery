from __future__ import annotations

import json
import logging
import os

import click
import httpx
import tomli_w
import tomllib
from rich.console import Console
from rich.table import Table

from .client import CineamoClient

console = Console()
logger = logging.getLogger(__name__)


def handle_api_errors(func):  # type: ignore[no-untyped-def]
    """Decorator to handle API errors with user-friendly messages."""

    def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
        ctx = click.get_current_context()
        verbose = ctx.obj.get("verbose", False) if ctx.obj else False

        try:
            return func(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:  # noqa: PLR2004
                console.print(
                    "[bold red]Error:[/bold red] Resource not found", style="red"
                )
            elif e.response.status_code == 429:  # noqa: PLR2004
                console.print(
                    "[bold red]Error:[/bold red] Rate limit exceeded. "
                    "Please try again later.",
                    style="red",
                )
            elif e.response.status_code >= 500:  # noqa: PLR2004
                console.print(
                    f"[bold red]Error:[/bold red] Server error "
                    f"({e.response.status_code}). Please try again later.",
                    style="red",
                )
            else:
                console.print(
                    f"[bold red]Error:[/bold red] API returned "
                    f"{e.response.status_code}",
                    style="red",
                )

            if verbose:
                logger.exception("Full error details:")
            raise click.Abort() from e
        except httpx.RequestError:
            console.print(
                "[bold red]Error:[/bold red] Could not connect to API. "
                "Check your network connection.",
                style="red",
            )
            if verbose:
                logger.exception("Full error details:")
            raise click.Abort() from None
        except Exception:
            # Re-raise unexpected errors to see full stack trace
            if verbose:
                logger.exception("Unexpected error:")
            raise

    return wrapper


@click.group()
@click.option(
    "--base-url",
    envvar="CINEAMO_BASE_URL",
    default=None,
    help="API base URL",
)
@click.option(
    "--timeout",
    type=float,
    default=None,
    help="Request timeout seconds (default: 15.0)",
)
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("-q", "--quiet", is_flag=True, help="Quiet output")
@click.pass_context
def main(
    ctx: click.Context,
    base_url: str | None,
    timeout: float | None,
    verbose: bool,
    quiet: bool,
) -> None:
    """Cineamo API command-line tool."""
    # Configure logging based on verbosity flags
    if verbose:
        logging.basicConfig(
            level=logging.DEBUG, format="%(levelname)s: %(message)s"
        )
    elif quiet:
        logging.basicConfig(level=logging.ERROR, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    # Load config and apply overrides
    # Precedence: CLI flags > env vars > config file > defaults
    ctx.ensure_object(dict)
    cfg = _load_config()
    logger.debug(f"Loaded config: {cfg}")

    # base_url precedence: --base-url flag/CINEAMO_BASE_URL env > config > default
    if base_url is not None:
        eff_base = base_url
        logger.debug(f"Using base_url from CLI/env: {eff_base}")
    elif "base_url" in cfg:
        eff_base = cfg["base_url"]
        logger.debug(f"Using base_url from config: {eff_base}")
    else:
        eff_base = "https://api.cineamo.com"
        logger.debug(f"Using default base_url: {eff_base}")

    # timeout precedence: --timeout flag > config > default
    if timeout is not None:
        eff_timeout = timeout
        logger.debug(f"Using timeout from CLI: {eff_timeout}")
    elif "timeout" in cfg:
        eff_timeout = float(cfg["timeout"])
        logger.debug(f"Using timeout from config: {eff_timeout}")
    else:
        eff_timeout = 15.0
        logger.debug(f"Using default timeout: {eff_timeout}")

    ctx.obj["client"] = CineamoClient(base_url=eff_base, timeout=eff_timeout)
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
@handle_api_errors
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
        _ps = dict(params)
        _ps.pop("per_page", None)
        _ps.pop("page", None)
        for c in client.stream_all("/cinemas", per_page=per_page, **_ps):
            rows.append(
                (
                    str(c.get("id", "")),
                    str(c.get("name", "")),
                    str(c.get("city", "")),
                    str(c.get("countryCode", "")),
                )
            )
            count += 1
            if limit and count >= limit:
                break
        if fmt.lower() == "json":
            click.echo(
                json.dumps(
                    {"items": rows, "total": count}, ensure_ascii=False, indent=2
                )
            )
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
        click.echo(
            json.dumps(
                {
                    "items": result.items,
                    "page": result.page,
                    "total": result.total_items,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    table = Table(
        title=f"Cinemas page {result.page}", header_style="bold cyan", show_lines=False
    )
    table.add_column("ID", justify="right", style="magenta", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("City", style="green")
    table.add_column("Country", style="yellow")
    for c in result.items:
        table.add_row(
            str(c.get("id", "")),
            str(c.get("name", "")),
            str(c.get("city", "")),
            str(c.get("countryCode", "")),
        )
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
@handle_api_errors
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
@handle_api_errors
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
        _ps = dict(params)
        _ps.pop("per_page", None)
        _ps.pop("page", None)
        for c in client.stream_all("/cinemas", per_page=per_page, **_ps):
            rows.append(
                (
                    str(c.get("id", "")),
                    str(c.get("name", "")),
                    str(c.get("city", "")),
                    str(c.get("countryCode", "")),
                )
            )
            count += 1
            if limit and count >= limit:
                break
        if fmt.lower() == "json":
            click.echo(
                json.dumps(
                    {"items": rows, "total": count}, ensure_ascii=False, indent=2
                )
            )
            return
        table = Table(
            title=f"Cinemas near ({lat},{lon}) total {count}",
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
        click.echo(
            json.dumps(
                {
                    "items": result.items,
                    "page": result.page,
                    "total": result.total_items,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    table = Table(
        title=f"Cinemas near ({lat},{lon}) page {result.page}",
        header_style="bold cyan",
        show_lines=False,
    )
    table.add_column("ID", justify="right", style="magenta", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("City", style="green")
    table.add_column("Country", style="yellow")
    for c in result.items:
        table.add_row(
            str(c.get("id", "")),
            str(c.get("name", "")),
            str(c.get("city", "")),
            str(c.get("countryCode", "")),
        )
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
@handle_api_errors
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
        _ps = dict(params)
        _ps.pop("per_page", None)
        _ps.pop("page", None)
        for m in client.stream_all("/movies", per_page=per_page, **_ps):
            rows.append(
                (
                    str(m.get("id", "")),
                    str(m.get("title", "")),
                    str(m.get("releaseDate", "")),
                    str(m.get("region", "")),
                )
            )
            count += 1
            if limit and count >= limit:
                break
        if fmt.lower() == "json":
            click.echo(
                json.dumps(
                    {"items": rows, "total": count}, ensure_ascii=False, indent=2
                )
            )
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
        click.echo(
            json.dumps(
                {
                    "items": result.items,
                    "page": result.page,
                    "total": result.total_items,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    table = Table(
        title=f"Movies page {result.page}", header_style="bold cyan", show_lines=False
    )
    table.add_column("ID", justify="right", style="magenta", no_wrap=True)
    table.add_column("Title", style="bold")
    table.add_column("Release", style="green")
    table.add_column("Region", style="yellow")
    for m in result.items:
        table.add_row(
            str(m.get("id", "")),
            str(m.get("title", "")),
            str(m.get("releaseDate", "")),
            str(m.get("region", "")),
        )
    console.print(table)


@main.command("cinema-movies")
@click.option("--cinema-id", type=int, required=True, help="Cinema ID")
@click.option("--query", type=str, help="Search string")
@click.option("--region", type=str, help="Region code")
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
@handle_api_errors
def cinema_movies(
    ctx: click.Context,
    cinema_id: int,
    query: str | None,
    region: str | None,
    per_page: int,
    page: int,
    list_all: bool,
    limit: int,
    fmt: str,
) -> None:
    """List movies for a given cinema."""
    client: CineamoClient = ctx.obj["client"]
    path = f"/cinemas/{cinema_id}/movies"
    params: dict[str, str | int] = {"per_page": per_page, "page": page}
    if query:
        params["query"] = query
    if region:
        params["region"] = region

    if list_all:
        count = 0
        rows: list[tuple[str, str, str, str]] = []
        _ps = dict(params)
        _ps.pop("per_page", None)
        _ps.pop("page", None)
        for m in client.stream_all(path, per_page=per_page, **_ps):
            rows.append(
                (
                    str(m.get("id", "")),
                    str(m.get("title", "")),
                    str(m.get("releaseDate", "")),
                    str(m.get("region", "")),
                )
            )
            count += 1
            if limit and count >= limit:
                break
        if fmt.lower() == "json":
            click.echo(
                json.dumps(
                    {"items": rows, "total": count}, ensure_ascii=False, indent=2
                )
            )
            return
        table = Table(
            title=f"Cinema {cinema_id} movies (total {count})",
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

    result = client.list_paginated(path, **params)
    if fmt.lower() == "json":
        click.echo(
            json.dumps(
                {
                    "items": result.items,
                    "page": result.page,
                    "total": result.total_items,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    table = Table(
        title=f"Cinema {cinema_id} movies page {result.page}",
        header_style="bold cyan",
        show_lines=False,
    )
    table.add_column("ID", justify="right", style="magenta", no_wrap=True)
    table.add_column("Title", style="bold")
    table.add_column("Release", style="green")
    table.add_column("Region", style="yellow")
    for m in result.items:
        table.add_row(
            str(m.get("id", "")),
            str(m.get("title", "")),
            str(m.get("releaseDate", "")),
            str(m.get("region", "")),
        )
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
@handle_api_errors
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
        _ps = dict(params)
        _ps.pop("per_page", None)
        _ps.pop("page", None)
        for m in client.stream_all("/movies", per_page=per_page, **_ps):
            rows.append(
                (
                    str(m.get("id", "")),
                    str(m.get("title", "")),
                    str(m.get("releaseDate", "")),
                    str(m.get("region", "")),
                )
            )
            count += 1
            if limit and count >= limit:
                break
        if fmt.lower() == "json":
            click.echo(
                json.dumps(
                    {"items": rows, "total": count}, ensure_ascii=False, indent=2
                )
            )
            return
        table = Table(
            title=f"Movies search (total {count})",
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
        click.echo(
            json.dumps(
                {
                    "items": result.items,
                    "page": result.page,
                    "total": result.total_items,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    table = Table(
        title=f"Movies search page {result.page}",
        header_style="bold cyan",
        show_lines=False,
    )
    table.add_column("ID", justify="right", style="magenta", no_wrap=True)
    table.add_column("Title", style="bold")
    table.add_column("Release", style="green")
    table.add_column("Region", style="yellow")
    for m in result.items:
        table.add_row(
            str(m.get("id", "")),
            str(m.get("title", "")),
            str(m.get("releaseDate", "")),
            str(m.get("region", "")),
        )
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
@handle_api_errors
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
@handle_api_errors
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
    base = os.path.join(os.path.expanduser("~"), ".config", "cineamoquery")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "config.toml")


def _load_config() -> dict[str, str]:
    path = _config_path()
    if not os.path.exists(path):
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def _save_config(cfg: dict[str, str]) -> None:
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


@main.group()
def completions() -> None:
    """Generate shell completion scripts."""


@completions.command("bash")
def completions_bash() -> None:
    """Output bash completion eval line."""
    click.echo('eval "$( _CINEAMO_COMPLETE=bash_complete cineamo )"')


@completions.command("zsh")
def completions_zsh() -> None:
    """Output zsh completion eval line."""
    click.echo('eval "$( _CINEAMO_COMPLETE=zsh_complete cineamo )"')


@completions.command("fish")
def completions_fish() -> None:
    """Output fish completion eval line."""
    click.echo("eval ( env _CINEAMO_COMPLETE=fish_complete cineamo )")
