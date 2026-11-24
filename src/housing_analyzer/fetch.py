"""Download raw datasets and cache them locally so repeat runs are fast and offline-friendly."""

from __future__ import annotations

import logging
import time
from pathlib import Path

import requests

from housing_analyzer.config import RAW_DIR, SOURCES

log = logging.getLogger(__name__)

USER_AGENT = "housing-analyzer/0.1 (educational data project)"
MAX_AGE_SECONDS = 7 * 24 * 3600  # Zillow updates monthly; a week-old cache is fine.


def _get_with_retries(url: str, attempts: int = 4, timeout: tuple[int, int] = (10, 30)):
    """GET ``url``, retrying timeouts and server errors with exponential backoff.

    Public data servers (FRED in particular) sometimes hang on a request that succeeds
    instantly on the next try, so a short timeout plus retries beats one long wait.
    """
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
            if response.status_code < 500:
                response.raise_for_status()
                return response
            error: Exception = requests.HTTPError(f"HTTP {response.status_code}")
        except (requests.Timeout, requests.ConnectionError) as exc:
            error = exc
        if attempt == attempts:
            raise RuntimeError(f"Failed to download {url} after {attempts} attempts") from error
        wait = 2 ** attempt
        log.warning("Attempt %d/%d failed (%s); retrying in %ds", attempt, attempts, error, wait)
        time.sleep(wait)
    raise AssertionError("unreachable")


def download(name: str, url: str, dest_dir: Path = RAW_DIR, force: bool = False) -> Path:
    """Download ``url`` to ``dest_dir/<name>.csv`` unless a fresh cached copy exists."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{name}.csv"

    if not force and dest.exists() and time.time() - dest.stat().st_mtime < MAX_AGE_SECONDS:
        log.info("Using cached %s (%s)", name, dest)
        return dest

    log.info("Downloading %s from %s", name, url)
    response = _get_with_retries(url)

    # Write to a temp file first so a failed download never leaves a half-written CSV.
    tmp = dest.with_suffix(".tmp")
    tmp.write_bytes(response.content)
    tmp.replace(dest)
    log.info("Saved %s (%.1f MB)", dest, dest.stat().st_size / 1e6)
    return dest


def fetch_all(force: bool = False) -> dict[str, Path]:
    """Download every configured source and return a mapping of name -> local path."""
    return {name: download(name, url, force=force) for name, url in SOURCES.items()}
