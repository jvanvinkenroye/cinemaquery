"""Tests for the interactive module."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from cinemaquery.cli import main
from cinemaquery.interactive import (
    format_cinema_entry,
    format_movie_entry,
    format_showtime_entry,
    load_cinemas_with_progress,
    load_movies_with_progress,
    load_showtimes_with_progress,
)

# Sample test data
SAMPLE_CINEMA: dict[str, Any] = {
    "id": 123,
    "name": "Cineplex Titania",
    "city": "Berlin",
    "countryCode": "DE",
}

SAMPLE_CINEMA_NO_CITY: dict[str, Any] = {
    "id": 124,
    "name": "Unknown Cinema",
    "countryCode": "US",
}

SAMPLE_CINEMA_MINIMAL: dict[str, Any] = {
    "id": 125,
    "name": "Minimal Cinema",
}

SAMPLE_MOVIE: dict[str, Any] = {
    "id": 456,
    "title": "Avatar 3",
    "releaseDate": "2026-01-15T00:00:00Z",
    "runtime": 162,
}

SAMPLE_MOVIE_NO_RUNTIME: dict[str, Any] = {
    "id": 457,
    "title": "Test Movie",
    "releaseDate": "2026-02-01T00:00:00Z",
}

SAMPLE_MOVIE_MINIMAL: dict[str, Any] = {
    "id": 458,
    "title": "Minimal Movie",
}

SAMPLE_SHOWTIME: dict[str, Any] = {
    "id": 789,
    "name": "Avatar 3",
    "startDatetime": "2026-01-25T14:30:00Z",
    "language": "deu",
    "isOriginalLanguage": False,
}

SAMPLE_SHOWTIME_OV: dict[str, Any] = {
    "id": 790,
    "name": "Avatar 3 OV",
    "startDatetime": "2026-01-25T17:00:00Z",
    "language": "eng",
    "isOriginalLanguage": True,
}


class TestFormatCinemaEntry:
    """Tests for format_cinema_entry function."""

    def test_full_cinema_info(self) -> None:
        """Test formatting with all fields present."""
        result = format_cinema_entry(SAMPLE_CINEMA)
        assert "Cineplex Titania" in result
        assert "Berlin" in result
        assert "DE" in result

    def test_cinema_without_city(self) -> None:
        """Test formatting when city is missing."""
        result = format_cinema_entry(SAMPLE_CINEMA_NO_CITY)
        assert "Unknown Cinema" in result
        assert "US" in result

    def test_minimal_cinema(self) -> None:
        """Test formatting with minimal data."""
        result = format_cinema_entry(SAMPLE_CINEMA_MINIMAL)
        assert "Minimal Cinema" in result

    def test_empty_cinema(self) -> None:
        """Test formatting with empty dict."""
        result = format_cinema_entry({})
        assert "Unknown" in result


class TestFormatMovieEntry:
    """Tests for format_movie_entry function."""

    def test_full_movie_info(self) -> None:
        """Test formatting with all fields present."""
        result = format_movie_entry(SAMPLE_MOVIE)
        assert "Avatar 3" in result
        assert "162 min" in result
        assert "2026-01-15" in result

    def test_movie_without_runtime(self) -> None:
        """Test formatting when runtime is missing."""
        result = format_movie_entry(SAMPLE_MOVIE_NO_RUNTIME)
        assert "Test Movie" in result
        assert "2026-02-01" in result

    def test_minimal_movie(self) -> None:
        """Test formatting with minimal data."""
        result = format_movie_entry(SAMPLE_MOVIE_MINIMAL)
        assert "Minimal Movie" in result

    def test_empty_movie(self) -> None:
        """Test formatting with empty dict."""
        result = format_movie_entry({})
        assert "Unknown" in result


class TestFormatShowtimeEntry:
    """Tests for format_showtime_entry function."""

    def test_regular_showtime(self) -> None:
        """Test formatting a regular showing."""
        result = format_showtime_entry(SAMPLE_SHOWTIME)
        assert "14:30" in result
        assert "Avatar 3" in result
        assert "deu" in result

    def test_original_version_showtime(self) -> None:
        """Test formatting an OV showing."""
        result = format_showtime_entry(SAMPLE_SHOWTIME_OV)
        assert "17:00" in result
        assert "Avatar 3 OV" in result
        assert "OV" in result


class TestLoadCinemasWithProgress:
    """Tests for load_cinemas_with_progress function."""

    def test_loads_cinemas(self) -> None:
        """Test that cinemas are loaded from the client."""
        mock_client = MagicMock()
        mock_client.stream_all.return_value = iter(
            [SAMPLE_CINEMA, SAMPLE_CINEMA_NO_CITY]
        )

        with patch("cinemaquery.interactive.Progress"):
            result = load_cinemas_with_progress(mock_client)

        assert len(result) == 2
        assert result[0]["id"] == 123
        mock_client.stream_all.assert_called_once()

    def test_loads_cinemas_with_city_filter(self) -> None:
        """Test that city filter is passed to the client."""
        mock_client = MagicMock()
        mock_client.stream_all.return_value = iter([SAMPLE_CINEMA])

        with patch("cinemaquery.interactive.Progress"):
            result = load_cinemas_with_progress(mock_client, city="Berlin")

        assert len(result) == 1
        call_kwargs = mock_client.stream_all.call_args[1]
        assert call_kwargs.get("city") == "Berlin"

    def test_respects_limit(self) -> None:
        """Test that limit parameter is respected."""
        mock_client = MagicMock()
        # Return more cinemas than the limit
        cinemas = [{"id": i, "name": f"Cinema {i}"} for i in range(10)]
        mock_client.stream_all.return_value = iter(cinemas)

        with patch("cinemaquery.interactive.Progress"):
            result = load_cinemas_with_progress(mock_client, limit=3)

        assert len(result) == 3


class TestLoadMoviesWithProgress:
    """Tests for load_movies_with_progress function."""

    def test_loads_movies(self) -> None:
        """Test that movies are loaded from the client."""
        mock_client = MagicMock()
        mock_client.stream_all.return_value = iter([SAMPLE_MOVIE, SAMPLE_MOVIE_MINIMAL])

        with patch("cinemaquery.interactive.Progress"):
            result = load_movies_with_progress(mock_client)

        assert len(result) == 2
        assert result[0]["id"] == 456
        mock_client.stream_all.assert_called_once_with("/movies", per_page=50)

    def test_loads_movies_with_query(self) -> None:
        """Test that query filter is passed to the client."""
        mock_client = MagicMock()
        mock_client.stream_all.return_value = iter([SAMPLE_MOVIE])

        with patch("cinemaquery.interactive.Progress"):
            result = load_movies_with_progress(mock_client, query="Avatar")

        assert len(result) == 1
        call_kwargs = mock_client.stream_all.call_args[1]
        assert call_kwargs.get("query") == "Avatar"

    def test_loads_cinema_movies(self) -> None:
        """Test loading movies for a specific cinema."""
        mock_client = MagicMock()
        mock_client.stream_all.return_value = iter([SAMPLE_MOVIE])

        with patch("cinemaquery.interactive.Progress"):
            result = load_movies_with_progress(mock_client, cinema_id=123)

        assert len(result) == 1
        call_args = mock_client.stream_all.call_args[0]
        assert "/cinemas/123/movies" in call_args[0]


class TestLoadShowtimesWithProgress:
    """Tests for load_showtimes_with_progress function."""

    def test_loads_showtimes(self) -> None:
        """Test that showtimes are loaded from the client."""
        mock_client = MagicMock()
        mock_client.stream_all.return_value = iter(
            [SAMPLE_SHOWTIME, SAMPLE_SHOWTIME_OV]
        )

        test_date = datetime(2026, 1, 25, tzinfo=timezone.utc)
        with patch("cinemaquery.interactive.Progress"):
            result = load_showtimes_with_progress(
                mock_client, cinema_id=123, date=test_date
            )

        assert len(result) == 2
        mock_client.stream_all.assert_called_once()
        call_args = mock_client.stream_all.call_args
        assert call_args[0][0] == "/showings"
        assert call_args[1]["cinemaIds[]"] == 123

    def test_showtimes_are_sorted(self) -> None:
        """Test that showtimes are sorted by start time."""
        mock_client = MagicMock()
        # Return showtimes in reverse order
        mock_client.stream_all.return_value = iter(
            [SAMPLE_SHOWTIME_OV, SAMPLE_SHOWTIME]
        )

        test_date = datetime(2026, 1, 25, tzinfo=timezone.utc)
        with patch("cinemaquery.interactive.Progress"):
            result = load_showtimes_with_progress(
                mock_client, cinema_id=123, date=test_date
            )

        # Should be sorted by startDatetime (14:30 before 17:00)
        assert result[0]["id"] == 789  # 14:30 showing
        assert result[1]["id"] == 790  # 17:00 showing


class TestCLIInteractiveCommand:
    """Tests for the CLI interactive command."""

    def test_interactive_command_exists(self) -> None:
        """Test that the interactive command is registered."""
        runner = CliRunner()
        result = runner.invoke(main, ["interactive", "--help"])
        assert result.exit_code == 0
        assert "--type" in result.output

    def test_interactive_alias_exists(self) -> None:
        """Test that the 'i' alias command is registered."""
        runner = CliRunner()
        result = runner.invoke(main, ["i", "--help"])
        assert result.exit_code == 0

    def test_interactive_type_option(self) -> None:
        """Test the --type option for direct workflow start."""
        runner = CliRunner()
        result = runner.invoke(main, ["interactive", "--help"])
        assert "--type" in result.output
        assert "cinema" in result.output
        assert "movie" in result.output
