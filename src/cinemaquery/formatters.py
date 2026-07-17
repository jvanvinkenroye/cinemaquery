"""Rendering helpers for CLI list commands."""

from __future__ import annotations

import json
from typing import Any

import click
from rich.console import Console
from rich.table import Table

console = Console()


def _is_quiet() -> bool:
    ctx = click.get_current_context(silent=True)
    return bool(ctx and ctx.obj and ctx.obj.get("quiet", False))


def _format_runtime(minutes: int | None) -> str:
    if not minutes:
        return ""
    hours, mins = divmod(minutes, 60)
    if hours:
        return f"{hours}h {mins}min ({minutes} min)"
    return f"{mins} min"


def _format_genres(genres: list[dict[str, Any]] | None) -> str:
    if not genres:
        return ""
    return ", ".join(g.get("name", "") for g in genres if g.get("name"))


def render_movie_details(data: dict[str, Any]) -> None:
    """Render rich movie detail view from an already-fetched API response."""
    if _is_quiet():
        return
    title = data.get("title", "Unknown")
    original_title = data.get("originalTitle", "")

    console.print()
    console.print(f"[bold cyan]{title}[/bold cyan]")
    if original_title and original_title != title:
        console.print(f"[dim]({original_title})[/dim]")
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="magenta", no_wrap=True)
    table.add_column("Value")
    table.add_row("Runtime", _format_runtime(data.get("runtime")))
    table.add_row("Release", str(data.get("releaseDate", ""))[:10])
    table.add_row("Genres", _format_genres(data.get("genres")))
    table.add_row("Language", str(data.get("originalLanguage", "")))
    table.add_row("IMDb", str(data.get("imdbId", "")))
    table.add_row("TMDB", str(data.get("tmdbId", "")))
    console.print(table)

    overview = data.get("overview")
    if overview:
        console.print()
        console.print("[bold]Overview:[/bold]")
        console.print(f"[dim]{overview}[/dim]", width=80)


def _cinema_table(title: str) -> Table:
    table = Table(title=title, header_style="bold cyan", show_lines=False)
    table.add_column("ID", justify="right", style="magenta", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("City", style="green")
    table.add_column("Country", style="yellow")
    return table


def _movie_table(title: str) -> Table:
    table = Table(title=title, header_style="bold cyan", show_lines=False)
    table.add_column("ID", justify="right", style="magenta", no_wrap=True)
    table.add_column("Title", style="bold")
    table.add_column("Release", style="green")
    table.add_column("Region", style="yellow")
    return table


def output_cinemas(
    items: list[dict[str, Any]],
    title: str,
    fmt: str,
    *,
    page: int | None = None,
    total: int | None = None,
) -> None:
    if fmt.lower() == "json":
        payload: dict[str, Any] = {"items": items}
        if page is not None:
            payload["page"] = page
        if total is not None:
            payload["total"] = total
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    if _is_quiet():
        return
    table = _cinema_table(title)
    for c in items:
        table.add_row(
            str(c.get("id", "")),
            str(c.get("name", "")),
            str(c.get("city", "")),
            str(c.get("countryCode", "")),
        )
    console.print(table)


def output_movies(
    items: list[dict[str, Any]],
    title: str,
    fmt: str,
    *,
    page: int | None = None,
    total: int | None = None,
) -> None:
    if fmt.lower() == "json":
        payload: dict[str, Any] = {"items": items}
        if page is not None:
            payload["page"] = page
        if total is not None:
            payload["total"] = total
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    if _is_quiet():
        return
    table = _movie_table(title)
    for m in items:
        table.add_row(
            str(m.get("id", "")),
            str(m.get("title", "")),
            str(m.get("releaseDate", "")),
            str(m.get("region", "")),
        )
    console.print(table)
