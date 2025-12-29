from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import httpx


DEFAULT_BASE_URL = "https://api.cineamo.com"


@dataclass
class Page:
    items: List[Dict[str, Any]]
    total_items: Optional[int]
    page: Optional[int]
    page_count: Optional[int]
    next_url: Optional[str]


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

    def list_paginated(self, path: str, **params: Any) -> Page:
        resp = self.get(path, **params)
        data = resp.json()
        embedded = data.get("_embedded", {})
        # Try to pick the first embedded array
        items: List[Dict[str, Any]] = []
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

    def stream_all(self, path: str, per_page: int = 50, **params: Any) -> Iterable[Dict[str, Any]]:
        page = 1
        while True:
            p = self.list_paginated(path, per_page=per_page, page=page, **params)
            for item in p.items:
                yield item
            if not p.next_url:
                break
            page += 1

