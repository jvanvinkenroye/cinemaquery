"""Tests for formatters module."""

from __future__ import annotations

import json
from io import StringIO
from typing import ClassVar
from unittest.mock import patch

from rich.console import Console

from cinemaquery.formatters import (
    _format_genres,
    _format_runtime,
    output_cinemas,
    output_movies,
    render_movie_details,
)

SAMPLE_CINEMAS = [
    {"id": 1, "name": "Test Cinema", "city": "Berlin", "countryCode": "DE"},
    {"id": 2, "name": "Other Cinema", "city": "Hamburg", "countryCode": "DE"},
]

SAMPLE_MOVIES = [
    {"id": 10, "title": "Test Movie", "releaseDate": "2024-01-15", "region": "DE"},
    {"id": 11, "title": "Other Movie", "releaseDate": "2024-06-01", "region": "DE"},
]


def _capture_json(fn, *args, **kwargs) -> dict:  # type: ignore[no-untyped-def]
    """Call fn and parse the first click.echo argument as JSON."""
    captured: list[str] = []
    with patch("cinemaquery.formatters.click") as mock_click:
        mock_click.echo.side_effect = captured.append
        mock_click.get_current_context.return_value = None
        fn(*args, **kwargs)
    return json.loads(captured[0])


def _capture_rich(fn, *args, **kwargs) -> str:  # type: ignore[no-untyped-def]
    """Call fn and return Rich console output."""
    con = Console(file=StringIO(), no_color=True)
    with patch("cinemaquery.formatters.console", con), patch("cinemaquery.formatters.click") as mock_click:
        mock_click.get_current_context.return_value = None
        fn(*args, **kwargs)
    return con.file.getvalue()  # type: ignore[union-attr]


def _capture_rich_quiet(fn, *args, **kwargs) -> str:  # type: ignore[no-untyped-def]
    """Call fn with quiet=True and return Rich console output (should be empty)."""
    con = Console(file=StringIO(), no_color=True)
    mock_ctx = type("ctx", (), {"obj": {"quiet": True}})()
    with patch("cinemaquery.formatters.console", con), patch("cinemaquery.formatters.click") as mock_click:
        mock_click.get_current_context.return_value = mock_ctx
        fn(*args, **kwargs)
    return con.file.getvalue()  # type: ignore[union-attr]


class TestFormatRuntime:
    def test_none_returns_empty(self) -> None:
        assert _format_runtime(None) == ""

    def test_zero_returns_empty(self) -> None:
        assert _format_runtime(0) == ""

    def test_minutes_only(self) -> None:
        result = _format_runtime(45)
        assert "45 min" in result
        assert "h" not in result

    def test_hours_and_minutes(self) -> None:
        result = _format_runtime(125)
        assert "2h" in result
        assert "5min" in result
        assert "125 min" in result

    def test_exact_hours(self) -> None:
        result = _format_runtime(120)
        assert "2h" in result
        assert "0min" in result


class TestFormatGenres:
    def test_none_returns_empty(self) -> None:
        assert _format_genres(None) == ""

    def test_empty_list_returns_empty(self) -> None:
        assert _format_genres([]) == ""

    def test_single_genre(self) -> None:
        assert _format_genres([{"name": "Action"}]) == "Action"

    def test_multiple_genres(self) -> None:
        result = _format_genres([{"name": "Action"}, {"name": "Comedy"}])
        assert "Action" in result
        assert "Comedy" in result

    def test_skips_genres_without_name(self) -> None:
        result = _format_genres([{"name": "Action"}, {}, {"name": "Drama"}])
        assert "Action" in result
        assert "Drama" in result


class TestOutputCinemas:
    def test_json_format_with_items(self) -> None:
        data = _capture_json(output_cinemas, SAMPLE_CINEMAS, "Test", "json")
        assert "items" in data
        assert len(data["items"]) == 2

    def test_json_format_includes_page_and_total(self) -> None:
        data = _capture_json(output_cinemas, SAMPLE_CINEMAS, "Test", "json", page=2, total=10)
        assert data["page"] == 2
        assert data["total"] == 10

    def test_rich_format_renders_table(self) -> None:
        output = _capture_rich(output_cinemas, SAMPLE_CINEMAS, "Test Cinemas", "rich")
        assert "Test Cinema" in output
        assert "Berlin" in output

    def test_quiet_mode_suppresses_rich_output(self) -> None:
        output = _capture_rich_quiet(output_cinemas, SAMPLE_CINEMAS, "Test", "rich")
        assert output == ""


class TestOutputMovies:
    def test_json_format_with_items(self) -> None:
        data = _capture_json(output_movies, SAMPLE_MOVIES, "Test", "json")
        assert "items" in data
        assert len(data["items"]) == 2

    def test_rich_format_renders_table(self) -> None:
        output = _capture_rich(output_movies, SAMPLE_MOVIES, "Test Movies", "rich")
        assert "Test Movie" in output
        assert "2024-01-15" in output

    def test_quiet_mode_suppresses_rich_output(self) -> None:
        output = _capture_rich_quiet(output_movies, SAMPLE_MOVIES, "Test", "rich")
        assert output == ""


class TestRenderMovieDetails:
    SAMPLE_DATA: ClassVar[dict] = {
        "title": "Inception",
        "originalTitle": "Inception",
        "runtime": 148,
        "releaseDate": "2010-07-16",
        "genres": [{"name": "Sci-Fi"}, {"name": "Action"}],
        "originalLanguage": "en",
        "imdbId": "tt1375666",
        "tmdbId": "27205",
        "overview": "A thief who steals corporate secrets.",
    }

    def test_renders_title(self) -> None:
        output = _capture_rich(render_movie_details, self.SAMPLE_DATA)
        assert "Inception" in output

    def test_renders_runtime_and_genres(self) -> None:
        output = _capture_rich(render_movie_details, self.SAMPLE_DATA)
        assert "148 min" in output
        assert "Sci-Fi" in output

    def test_renders_overview(self) -> None:
        output = _capture_rich(render_movie_details, self.SAMPLE_DATA)
        assert "thief" in output

    def test_quiet_suppresses_output(self) -> None:
        output = _capture_rich_quiet(render_movie_details, self.SAMPLE_DATA)
        assert output == ""
