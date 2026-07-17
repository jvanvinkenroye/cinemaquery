"""Rendering helpers for CLI list commands."""

from __future__ import annotations

import json
from typing import Any

import click
from rich.console import Console
from rich.table import Table

console = Console()


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
    table = _movie_table(title)
    for m in items:
        table.add_row(
            str(m.get("id", "")),
            str(m.get("title", "")),
            str(m.get("releaseDate", "")),
            str(m.get("region", "")),
        )
    console.print(table)
