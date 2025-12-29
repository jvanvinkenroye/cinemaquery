from __future__ import annotations

import json
from typing import Optional

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
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
@click.pass_context
def list_cinemas(ctx: click.Context, city: Optional[str], per_page: int, page: int, json_out: bool) -> None:
    """List cinemas with optional filters."""
    client: CineamoClient = ctx.obj["client"]
    params = {"per_page": per_page, "page": page}
    if city:
        params["city"] = city
    result = client.list_paginated("/cinemas", **params)

    if json_out:
        click.echo(json.dumps({"items": result.items, "page": result.page, "total": result.total_items}, ensure_ascii=False, indent=2))
        return

    table = Table(title=f"Cinemas page {result.page}")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("City")
    table.add_column("Country")
    for c in result.items:
        table.add_row(str(c.get("id", "")), str(c.get("name", "")), str(c.get("city", "")), str(c.get("countryCode", "")))
    console.print(table)


@main.command("movies")
@click.option("--query", type=str, help="Search string")
@click.option("--per-page", type=int, default=10, show_default=True)
@click.option("--page", type=int, default=1, show_default=True)
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
@click.pass_context
def list_movies(ctx: click.Context, query: Optional[str], per_page: int, page: int, json_out: bool) -> None:
    """List movies with optional query."""
    client: CineamoClient = ctx.obj["client"]
    params = {"per_page": per_page, "page": page}
    if query:
        params["query"] = query
    result = client.list_paginated("/movies", **params)

    if json_out:
        click.echo(json.dumps({"items": result.items, "page": result.page, "total": result.total_items}, ensure_ascii=False, indent=2))
        return

    table = Table(title=f"Movies page {result.page}")
    table.add_column("ID", justify="right")
    table.add_column("Title")
    table.add_column("Release")
    table.add_column("Region")
    for m in result.items:
        table.add_row(str(m.get("id", "")), str(m.get("title", "")), str(m.get("releaseDate", "")), str(m.get("region", "")))
    console.print(table)


@main.result_callback()
@click.pass_context
def finalize(ctx: click.Context, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
    client: CineamoClient = ctx.obj.get("client")
    if client:
        client.close()

