"""Shared pytest fixtures for cineamoquery tests."""

from __future__ import annotations

from unittest.mock import Mock

import httpx
import pytest

from cineamoquery.client import CineamoClient, Page


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx.Client for testing."""
    return Mock(spec=httpx.Client)


@pytest.fixture
def cineamo_client(mock_httpx_client):
    """Create a CineamoClient with mocked httpx client."""
    client = CineamoClient(base_url="https://api.test.com", timeout=10.0)
    client._client = mock_httpx_client
    return client


@pytest.fixture
def sample_cinema_data():
    """Sample cinema data for testing."""
    return {
        "id": 1,
        "name": "Test Cinema",
        "city": "Berlin",
        "countryCode": "DE",
        "slug": "test-cinema",
        "ticketSystem": "test",
        "email": "test@cinema.com",
    }


@pytest.fixture
def sample_movie_data():
    """Sample movie data for testing."""
    return {
        "id": 100,
        "title": "Test Movie",
        "region": "DE",
        "releaseDate": "2024-01-01",
        "runtime": 120,
        "imdbId": "tt1234567",
    }


@pytest.fixture
def sample_hal_response():
    """Sample HAL-JSON response for testing pagination."""
    return {
        "_embedded": {
            "cinemas": [
                {"id": 1, "name": "Cinema 1", "city": "Berlin"},
                {"id": 2, "name": "Cinema 2", "city": "Munich"},
            ]
        },
        "_page": 1,
        "_page_count": 5,
        "_total_items": 50,
        "_links": {
            "next": {"href": "/cinemas?page=2&per_page=10"},
            "self": {"href": "/cinemas?page=1&per_page=10"},
        },
    }


@pytest.fixture
def sample_page():
    """Sample Page object for testing."""
    return Page(
        items=[
            {"id": 1, "name": "Cinema 1"},
            {"id": 2, "name": "Cinema 2"},
        ],
        total_items=50,
        page=1,
        page_count=5,
        next_url="/cinemas?page=2",
    )
