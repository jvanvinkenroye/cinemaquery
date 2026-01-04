from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, cast

import httpx

DEFAULT_BASE_URL = "https://api.cineamo.com"


@dataclass
class Page:
    items: list[dict[str, Any]]
    total_items: int | None
    page: int | None
    page_count: int | None
    next_url: str | None


class CineamoClient:
    """Minimal client for the public Cineamo API."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 15.0) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def get(self, path: str, **params: Any) -> httpx.Response:
        resp = self._client.get(path, params=params or None)
        resp.raise_for_status()
        return resp

    def get_json(self, path: str, **params: Any) -> dict[str, Any]:
        return cast(dict[str, Any], self.get(path, **params).json())

    def list_paginated(self, path: str, **params: Any) -> Page:
        resp = self.get(path, **params)
        data = resp.json()
        embedded = data.get("_embedded", {})
        # Try to pick the first embedded array
        items: list[dict[str, Any]] = []
        for v in embedded.values():
            if isinstance(v, list):
                items = v
                break
        links = data.get("_links", {})
        return Page(
            items=items,
            total_items=data.get("_total_items"),
            page=data.get("_page"),
            page_count=data.get("_page_count"),
            next_url=(links.get("next") or {}).get("href"),
        )

    def stream_all(
        self, path: str, per_page: int = 50, **params: Any
    ) -> Iterable[dict[str, Any]]:
        page = 1
        while True:
            p = self.list_paginated(path, per_page=per_page, page=page, **params)
            yield from p.items
            if not p.next_url:
                break
            page += 1
