from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from audiorepodigest.logging import get_logger
from audiorepodigest.models import RepositoryCandidate

logger = get_logger(__name__)


class GitHubApiError(RuntimeError):
    """Generic GitHub API failure."""


class GitHubRateLimitError(GitHubApiError):
    """Raised when GitHub rate limiting is encountered."""


class GitHubClient:
    """Minimal GitHub REST client with retries and pagination."""

    def __init__(self, token: str, *, timeout: float = 30.0) -> None:
        self._client = httpx.Client(
            base_url="https://api.github.com",
            timeout=timeout,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "User-Agent": "AudioRepoDigest/0.1.0",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> GitHubClient:
        return self

    def __exit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        self.close()

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, GitHubApiError)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        response = self._client.request(method, url, **kwargs)
        if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
            raise GitHubRateLimitError("GitHub API rate limit exhausted.")
        if response.status_code in {429, 500, 502, 503, 504}:
            raise GitHubApiError(f"Retryable GitHub API error: {response.status_code}")
        response.raise_for_status()
        return response

    def search_repositories(
        self,
        query: str,
        *,
        sort: str = "updated",
        order: str = "desc",
        limit: int = 50,
    ) -> list[RepositoryCandidate]:
        repositories: list[RepositoryCandidate] = []
        for page in self._page_numbers(limit):
            if len(repositories) >= limit:
                break
            per_page = min(100, limit - len(repositories))
            response = self._request(
                "GET",
                "/search/repositories",
                params={
                    "q": query,
                    "sort": sort,
                    "order": order,
                    "per_page": per_page,
                    "page": page,
                },
            )
            data = response.json()
            items = data.get("items", [])
            repositories.extend(self._to_candidate(item, source_query=query) for item in items)
            if len(items) < per_page:
                break
        logger.debug("Search query returned %s repositories: %s", len(repositories), query)
        return repositories

    def get_repository(self, full_name: str) -> RepositoryCandidate:
        response = self._request("GET", f"/repos/{full_name}")
        return self._to_candidate(response.json(), source_query=f"repo:{full_name}")

    def get_readme_text(self, full_name: str) -> str | None:
        response = self._request(
            "GET",
            f"/repos/{full_name}/readme",
            headers={"Accept": "application/vnd.github.raw"},
        )
        return response.text or None

    def _page_numbers(self, limit: int) -> Iterator[int]:
        max_pages = max(1, (limit + 99) // 100)
        return iter(range(1, max_pages + 1))

    def _to_candidate(self, payload: dict[str, Any], *, source_query: str) -> RepositoryCandidate:
        owner = payload.get("owner", {})
        return RepositoryCandidate(
            id=payload["id"],
            full_name=payload["full_name"],
            name=payload["name"],
            owner=owner.get("login", "unknown"),
            html_url=payload["html_url"],
            description=payload.get("description") or "",
            topics=payload.get("topics") or [],
            language=payload.get("language"),
            created_at=self._parse_datetime(payload["created_at"]),
            updated_at=self._parse_datetime(payload["updated_at"]),
            pushed_at=self._parse_datetime(payload["pushed_at"]),
            stargazers_count=payload.get("stargazers_count", 0),
            forks_count=payload.get("forks_count", 0),
            watchers_count=payload.get("watchers_count", 0),
            open_issues_count=payload.get("open_issues_count", 0),
            archived=payload.get("archived", False),
            fork=payload.get("fork", False),
            source_queries=[source_query],
            raw_payload=payload,
        )

    def _parse_datetime(self, value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
