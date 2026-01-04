"""Tests for CineamoClient."""

from __future__ import annotations

from unittest.mock import Mock

import httpx
import pytest

from cineamoquery.client import CineamoClient, Page


class TestCineamoClient:
    """Test suite for CineamoClient."""

    def test_client_initialization(self):
        """Test client initializes with correct defaults."""
        client = CineamoClient()
        assert client.base_url == "https://api.cineamo.com"
        # httpx.Client.timeout is a Timeout object, check its connect value
        assert client._client.timeout.connect == 15.0
        assert client._client.timeout.read == 15.0
        client.close()

    def test_client_custom_base_url(self):
        """Test client accepts custom base URL."""
        client = CineamoClient(base_url="https://custom.api.com", timeout=30.0)
        assert client.base_url == "https://custom.api.com"
        # httpx.Client.timeout is a Timeout object, check its connect value
        assert client._client.timeout.connect == 30.0
        assert client._client.timeout.read == 30.0
        client.close()

    def test_client_strips_trailing_slash(self):
        """Test client strips trailing slash from base URL."""
        client = CineamoClient(base_url="https://api.test.com/")
        assert client.base_url == "https://api.test.com"
        client.close()

    def test_get_json_success(
        self, cineamo_client, mock_httpx_client, sample_cinema_data
    ):
        """Test get_json returns JSON data on success."""
        mock_response = Mock()
        mock_response.json.return_value = sample_cinema_data
        mock_response.raise_for_status.return_value = None
        mock_httpx_client.get.return_value = mock_response

        result = cineamo_client.get_json("/cinemas/1")

        assert result == sample_cinema_data
        mock_httpx_client.get.assert_called_once_with("/cinemas/1", params=None)
        mock_response.raise_for_status.assert_called_once()

    def test_get_json_with_params(self, cineamo_client, mock_httpx_client):
        """Test get_json passes query parameters correctly."""
        mock_response = Mock()
        mock_response.json.return_value = {"items": []}
        mock_response.raise_for_status.return_value = None
        mock_httpx_client.get.return_value = mock_response

        cineamo_client.get_json("/cinemas", city="Berlin", per_page=10)

        mock_httpx_client.get.assert_called_once_with(
            "/cinemas", params={"city": "Berlin", "per_page": 10}
        )

    def test_get_raises_on_http_error(self, cineamo_client, mock_httpx_client):
        """Test get raises HTTPStatusError on HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found",
            request=Mock(),
            response=Mock(status_code=404),
        )
        mock_httpx_client.get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            cineamo_client.get_json("/cinemas/999999")

    def test_list_paginated_parses_hal_json(
        self, cineamo_client, mock_httpx_client, sample_hal_response
    ):
        """Test list_paginated correctly parses HAL-JSON response."""
        mock_response = Mock()
        mock_response.json.return_value = sample_hal_response
        mock_response.raise_for_status.return_value = None
        mock_httpx_client.get.return_value = mock_response

        result = cineamo_client.list_paginated("/cinemas", per_page=10, page=1)

        assert isinstance(result, Page)
        assert len(result.items) == 2
        assert result.items[0]["id"] == 1
        assert result.items[1]["id"] == 2
        assert result.total_items == 50
        assert result.page == 1
        assert result.page_count == 5
        assert result.next_url == "/cinemas?page=2&per_page=10"

    def test_list_paginated_handles_missing_metadata(
        self, cineamo_client, mock_httpx_client
    ):
        """Test list_paginated handles missing pagination metadata."""
        minimal_response = {
            "_embedded": {"items": [{"id": 1}]},
            "_links": {},
        }
        mock_response = Mock()
        mock_response.json.return_value = minimal_response
        mock_response.raise_for_status.return_value = None
        mock_httpx_client.get.return_value = mock_response

        result = cineamo_client.list_paginated("/test")

        assert len(result.items) == 1
        assert result.total_items is None
        assert result.page is None
        assert result.page_count is None
        assert result.next_url is None

    def test_list_paginated_finds_first_array_in_embedded(
        self, cineamo_client, mock_httpx_client
    ):
        """Test list_paginated finds first array value in _embedded."""
        response = {
            "_embedded": {
                "movies": [{"id": 1}, {"id": 2}],
                "total": 100,  # Non-array value should be ignored
            },
            "_links": {},
        }
        mock_response = Mock()
        mock_response.json.return_value = response
        mock_response.raise_for_status.return_value = None
        mock_httpx_client.get.return_value = mock_response

        result = cineamo_client.list_paginated("/movies")

        assert len(result.items) == 2
        assert result.items[0]["id"] == 1

    def test_stream_all_yields_items_from_multiple_pages(
        self, cineamo_client, mock_httpx_client
    ):
        """Test stream_all fetches and yields items from multiple pages."""
        page1_response = {
            "_embedded": {"cinemas": [{"id": 1}, {"id": 2}]},
            "_page": 1,
            "_total_items": 4,
            "_links": {"next": {"href": "/cinemas?page=2"}},
        }
        page2_response = {
            "_embedded": {"cinemas": [{"id": 3}, {"id": 4}]},
            "_page": 2,
            "_total_items": 4,
            "_links": {},  # No next link
        }

        mock_response1 = Mock()
        mock_response1.json.return_value = page1_response
        mock_response1.raise_for_status.return_value = None

        mock_response2 = Mock()
        mock_response2.json.return_value = page2_response
        mock_response2.raise_for_status.return_value = None

        mock_httpx_client.get.side_effect = [mock_response1, mock_response2]

        items = list(cineamo_client.stream_all("/cinemas", per_page=2))

        assert len(items) == 4
        assert items[0]["id"] == 1
        assert items[1]["id"] == 2
        assert items[2]["id"] == 3
        assert items[3]["id"] == 4
        assert mock_httpx_client.get.call_count == 2

    def test_stream_all_stops_when_no_next_link(
        self, cineamo_client, mock_httpx_client
    ):
        """Test stream_all stops iteration when no next link is present."""
        single_page_response = {
            "_embedded": {"cinemas": [{"id": 1}]},
            "_links": {},  # No next link
        }
        mock_response = Mock()
        mock_response.json.return_value = single_page_response
        mock_response.raise_for_status.return_value = None
        mock_httpx_client.get.return_value = mock_response

        items = list(cineamo_client.stream_all("/cinemas"))

        assert len(items) == 1
        assert mock_httpx_client.get.call_count == 1

    def test_close(self, cineamo_client, mock_httpx_client):
        """Test close calls httpx client close."""
        cineamo_client.close()
        mock_httpx_client.close.assert_called_once()
