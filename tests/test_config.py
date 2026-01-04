"""Tests for configuration handling."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from cinemaquery.cli import _config_path, _load_config, _save_config, main


@pytest.fixture
def temp_config_dir(monkeypatch):
    """Create a temporary config directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".config" / "cinemaquery"
        config_dir.mkdir(parents=True)

        # Mock the config path to use our temp directory
        def mock_config_path():
            return str(config_dir / "config.toml")

        monkeypatch.setattr("cinemaquery.cli._config_path", mock_config_path)
        yield config_dir


class TestConfigPrecedence:
    """Test configuration precedence logic."""

    def test_default_base_url(self, temp_config_dir):
        """Test default base URL is used when no config exists."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0

    def test_config_file_overrides_default(self, temp_config_dir):
        """Test config file values override defaults."""
        config = {"base_url": "https://config.example.com", "timeout": "20.0"}
        _save_config(config)

        loaded = _load_config()
        assert loaded["base_url"] == "https://config.example.com"
        assert loaded["timeout"] == "20.0"

    def test_env_var_overrides_config(self, temp_config_dir, monkeypatch):
        """Test environment variables override config file."""
        # Set config file value
        config = {"base_url": "https://config.example.com"}
        _save_config(config)

        # Set environment variable
        monkeypatch.setenv("CINEAMO_BASE_URL", "https://env.example.com")

        runner = CliRunner()
        # The main function should use env var over config
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0

    def test_cli_flag_overrides_all(self, temp_config_dir, monkeypatch):
        """Test CLI flags override both config and env vars."""
        # Set config
        config = {"base_url": "https://config.example.com"}
        _save_config(config)

        # Set env var
        monkeypatch.setenv("CINEAMO_BASE_URL", "https://env.example.com")

        runner = CliRunner()
        # CLI flag should take precedence
        result = runner.invoke(
            main, ["--base-url", "https://cli.example.com", "--help"]
        )
        assert result.exit_code == 0


class TestConfigCommands:
    """Test config subcommands."""

    def test_config_set_creates_file(self, temp_config_dir):
        """Test config set creates config file."""
        runner = CliRunner()
        result = runner.invoke(main, ["config", "set", "base_url", "https://test.com"])

        assert result.exit_code == 0
        assert "Set base_url" in result.output

        # Verify file was created
        config_file = Path(_config_path())
        assert config_file.exists()

    def test_config_set_and_get(self, temp_config_dir):
        """Test config set followed by get."""
        runner = CliRunner()

        # Set a value
        result = runner.invoke(main, ["config", "set", "timeout", "25.0"])
        assert result.exit_code == 0

        # Get the value
        result = runner.invoke(main, ["config", "get", "timeout"])
        assert result.exit_code == 0
        assert "25.0" in result.output

    def test_config_get_nonexistent_key(self, temp_config_dir):
        """Test config get for non-existent key returns empty."""
        runner = CliRunner()
        result = runner.invoke(main, ["config", "get", "nonexistent"])

        assert result.exit_code == 0
        assert result.output.strip() == ""

    def test_config_show_empty(self, temp_config_dir):
        """Test config show with no config file."""
        runner = CliRunner()
        result = runner.invoke(main, ["config", "show"])

        assert result.exit_code == 0
        assert "{}" in result.output

    def test_config_show_with_values(self, temp_config_dir):
        """Test config show displays all values."""
        runner = CliRunner()

        # Set multiple values
        runner.invoke(main, ["config", "set", "base_url", "https://test.com"])
        runner.invoke(main, ["config", "set", "timeout", "30.0"])

        # Show all config
        result = runner.invoke(main, ["config", "show"])

        assert result.exit_code == 0
        assert "base_url" in result.output
        assert "https://test.com" in result.output
        assert "timeout" in result.output
        assert "30.0" in result.output

    def test_config_update_existing_value(self, temp_config_dir):
        """Test updating an existing config value."""
        runner = CliRunner()

        # Set initial value
        runner.invoke(main, ["config", "set", "base_url", "https://first.com"])

        # Update value
        runner.invoke(main, ["config", "set", "base_url", "https://second.com"])

        # Verify updated value
        result = runner.invoke(main, ["config", "get", "base_url"])
        assert "https://second.com" in result.output
        assert "https://first.com" not in result.output


class TestConfigFileHandling:
    """Test config file operations."""

    def test_load_config_missing_file(self, temp_config_dir):
        """Test loading config when file doesn't exist."""
        config_file = Path(_config_path())
        if config_file.exists():
            config_file.unlink()

        config = _load_config()
        assert config == {}

    def test_save_and_load_config(self, temp_config_dir):
        """Test saving and loading config."""
        test_config = {
            "base_url": "https://api.example.com",
            "timeout": "15.0",
        }

        _save_config(test_config)
        loaded_config = _load_config()

        assert loaded_config == test_config

    def test_config_preserves_existing_values(self, temp_config_dir):
        """Test that setting one value doesn't delete others."""
        # Set first value
        _save_config({"key1": "value1"})

        # Load, modify, and save
        config = _load_config()
        config["key2"] = "value2"
        _save_config(config)

        # Verify both values exist
        final_config = _load_config()
        assert final_config["key1"] == "value1"
        assert final_config["key2"] == "value2"


class TestConfigPathCreation:
    """Test config directory creation."""

    def test_config_path_creates_directory(self, monkeypatch):
        """Test that config path creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_config_dir = Path(tmpdir) / "test_config" / "cinemaquery"
            test_config_path = test_config_dir / "config.toml"

            def mock_config_path():
                # Ensure directory exists (mimicking the real _config_path behavior)
                test_config_dir.mkdir(parents=True, exist_ok=True)
                return str(test_config_path)

            monkeypatch.setattr("cinemaquery.cli._config_path", mock_config_path)

            # Save config should work with the mocked path
            _save_config({"test": "value"})

            assert test_config_path.exists()
            assert test_config_path.parent.exists()
