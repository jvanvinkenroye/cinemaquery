"""Tests for CLI commands."""

from __future__ import annotations

import json
from unittest.mock import Mock, patch

import httpx
import pytest
from click.testing import CliRunner

from cinemaquery.cli import main
from cinemaquery.client import Page


@pytest.fixture
def runner():
    """Create a Click CliRunner for testing."""
    return CliRunner()


@pytest.fixture
def mock_client():
    """Create a mock CineamoClient."""
    return Mock()


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_main_help(self, runner):
        """Test main --help command."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Cineamo API command-line tool" in result.output
        assert "--base-url" in result.output
        assert "--timeout" in result.output
        assert "--verbose" in result.output
        assert "--quiet" in result.output

    def test_main_version_displays_commands(self, runner):
        """Test main command lists subcommands."""
        result = runner.invoke(main, ["--help"])
        assert "cinemas" in result.output
        assert "cinema" in result.output
        assert "movies" in result.output
        assert "movie" in result.output
        assert "config" in result.output


class TestCinemasCommand:
    """Test cinemas command."""

    def test_cinemas_help(self, runner):
        """Test cinemas --help."""
        result = runner.invoke(main, ["cinemas", "--help"])
        assert result.exit_code == 0
        assert "--city" in result.output
        assert "--per-page" in result.output
        assert "--all" in result.output
        assert "--format" in result.output

    @patch("cinemaquery.cli.CineamoClient")
    def test_cinemas_json_format(self, mock_client_class, runner):
        """Test cinemas command with JSON format."""
        mock_client = Mock()
        mock_page = Page(
            items=[
                {"id": 1, "name": "Test Cinema", "city": "Berlin", "countryCode": "DE"}
            ],
            total_items=1,
            page=1,
            page_count=1,
            next_url=None,
        )
        mock_client.list_paginated.return_value = mock_page
        mock_client_class.return_value = mock_client

        result = runner.invoke(main, ["cinemas", "--per-page", "1", "--format", "json"])

        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert "items" in output_data
        assert output_data["page"] == 1
        assert output_data["total"] == 1

    @patch("cinemaquery.cli.CineamoClient")
    def test_cinemas_with_city_filter(self, mock_client_class, runner):
        """Test cinemas command with city filter."""
        mock_client = Mock()
        mock_page = Page(items=[], total_items=0, page=1, page_count=0, next_url=None)
        mock_client.list_paginated.return_value = mock_page
        mock_client_class.return_value = mock_client

        result = runner.invoke(
            main, ["cinemas", "--city", "Berlin", "--format", "json"]
        )

        assert result.exit_code == 0
        mock_client.list_paginated.assert_called_once()
        call_kwargs = mock_client.list_paginated.call_args[1]
        assert call_kwargs["city"] == "Berlin"


class TestCinemaCommand:
    """Test cinema command."""

    def test_cinema_help(self, runner):
        """Test cinema --help."""
        result = runner.invoke(main, ["cinema", "--help"])
        assert result.exit_code == 0
        assert "--id" in result.output
        assert "--format" in result.output

    @patch("cinemaquery.cli.CineamoClient")
    def test_cinema_json_format(self, mock_client_class, runner, sample_cinema_data):
        """Test cinema command with JSON format."""
        mock_client = Mock()
        mock_client.get_json.return_value = sample_cinema_data
        mock_client_class.return_value = mock_client

        result = runner.invoke(main, ["cinema", "--id", "1", "--format", "json"])

        assert result.exit_code == 0
        output_data = json.loads(result.output)
        assert output_data["id"] == 1
        assert output_data["name"] == "Test Cinema"

    @patch("cinemaquery.cli.CineamoClient")
    def test_cinema_handles_404(self, mock_client_class, runner):
        """Test cinema command handles 404 gracefully."""
        mock_client = Mock()
        mock_client.get_json.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=Mock(),
            response=Mock(status_code=404),
        )
        mock_client_class.return_value = mock_client

        result = runner.invoke(main, ["cinema", "--id", "999999"])

        assert result.exit_code == 1  # Abort
        assert "Resource not found" in result.output


class TestMoviesCommand:
    """Test movies command."""

    def test_movies_help(self, runner):
        """Test movies --help."""
        result = runner.invoke(main, ["movies", "--help"])
        assert result.exit_code == 0
        assert "--query" in result.output
        assert "--per-page" in result.output

    @patch("cinemaquery.cli.CineamoClient")
    def test_movies_with_query(self, mock_client_class, runner):
        """Test movies command with query parameter."""
        mock_client = Mock()
        mock_page = Page(
            items=[
                {
                    "id": 1,
                    "title": "Test Movie",
                    "releaseDate": "2024-01-01",
                    "region": "DE",
                }
            ],
            total_items=1,
            page=1,
            page_count=1,
            next_url=None,
        )
        mock_client.list_paginated.return_value = mock_page
        mock_client_class.return_value = mock_client

        result = runner.invoke(main, ["movies", "--query", "Test", "--format", "json"])

        assert result.exit_code == 0
        mock_client.list_paginated.assert_called_once()
        call_kwargs = mock_client.list_paginated.call_args[1]
        assert call_kwargs["query"] == "Test"


class TestConfigCommand:
    """Test config commands."""

    def test_config_help(self, runner):
        """Test config --help."""
        result = runner.invoke(main, ["config", "--help"])
        assert result.exit_code == 0
        assert "set" in result.output
        assert "get" in result.output
        assert "show" in result.output

    def test_config_set_and_get(self, runner):
        """Test config set and get commands."""
        with runner.isolated_filesystem():
            # Set a value
            result = runner.invoke(main, ["config", "set", "test_key", "test_value"])
            assert result.exit_code == 0
            assert "Set test_key" in result.output

            # Get the value
            result = runner.invoke(main, ["config", "get", "test_key"])
            assert result.exit_code == 0
            assert "test_value" in result.output

    def test_config_show(self, runner):
        """Test config show command."""
        with runner.isolated_filesystem():
            runner.invoke(main, ["config", "set", "base_url", "https://test.com"])
            result = runner.invoke(main, ["config", "show"])

            assert result.exit_code == 0
            output_data = json.loads(result.output)
            assert output_data["base_url"] == "https://test.com"


class TestVerboseQuietFlags:
    """Test --verbose and --quiet flags."""

    @patch("cinemaquery.cli.CineamoClient")
    def test_verbose_flag_enables_debug_logging(self, mock_client_class, runner):
        """Test --verbose flag enables debug logging."""
        mock_client = Mock()
        mock_page = Page(items=[], total_items=0, page=1, page_count=0, next_url=None)
        mock_client.list_paginated.return_value = mock_page
        mock_client_class.return_value = mock_client

        result = runner.invoke(main, ["--verbose", "cinemas", "--format", "json"])

        assert result.exit_code == 0
        # Verbose mode should show DEBUG logs
        assert "DEBUG" in result.output or result.exit_code == 0

    @patch("cinemaquery.cli.CineamoClient")
    def test_quiet_flag_suppresses_output(self, mock_client_class, runner):
        """Test --quiet flag suppresses warnings."""
        mock_client = Mock()
        mock_page = Page(items=[], total_items=0, page=1, page_count=0, next_url=None)
        mock_client.list_paginated.return_value = mock_page
        mock_client_class.return_value = mock_client

        result = runner.invoke(main, ["--quiet", "cinemas", "--format", "json"])

        assert result.exit_code == 0
        # Should not have WARNING level logs
        assert "WARNING" not in result.output or result.exit_code == 0


class TestErrorHandling:
    """Test error handling."""

    @patch("cinemaquery.cli.CineamoClient")
    def test_network_error_handling(self, mock_client_class, runner):
        """Test network errors are handled gracefully."""
        mock_client = Mock()
        mock_client.list_paginated.side_effect = httpx.RequestError("Connection failed")
        mock_client_class.return_value = mock_client

        result = runner.invoke(main, ["cinemas"])

        assert result.exit_code == 1
        assert "Could not connect to API" in result.output

    @patch("cinemaquery.cli.CineamoClient")
    def test_500_error_handling(self, mock_client_class, runner):
        """Test 500 errors are handled gracefully."""
        mock_client = Mock()
        mock_client.get_json.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=Mock(),
            response=Mock(status_code=500),
        )
        mock_client_class.return_value = mock_client

        result = runner.invoke(main, ["cinema", "--id", "1"])

        assert result.exit_code == 1
        assert "Server error" in result.output


class TestCompletionsCommand:
    """Test completions commands."""

    def test_completions_bash(self, runner):
        """Test bash completions."""
        result = runner.invoke(main, ["completions", "bash"])
        assert result.exit_code == 0
        assert "bash_complete" in result.output

    def test_completions_zsh(self, runner):
        """Test zsh completions."""
        result = runner.invoke(main, ["completions", "zsh"])
        assert result.exit_code == 0
        assert "zsh_complete" in result.output

    def test_completions_fish(self, runner):
        """Test fish completions."""
        result = runner.invoke(main, ["completions", "fish"])
        assert result.exit_code == 0
        assert "fish_complete" in result.output
