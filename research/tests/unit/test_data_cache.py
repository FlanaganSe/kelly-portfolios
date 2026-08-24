"""The cache must preserve bytes, record headers, and refuse to guess."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest
import requests

from portfolio_edge.data.cache import (
    CacheEntry,
    CacheIntegrityError,
    RawArtifactMissing,
    RawCache,
    sha256_hex,
)

URL = "https://example.invalid/data.zip"
PAYLOAD = b"PK\x03\x04\x00 raw bytes with \r\n mixed \n endings and \xff high byte"


class _StubResponse:
    def __init__(self, content: bytes, headers: dict[str, str], status: int) -> None:
        self.content = content
        self.headers = headers
        self.status_code = status

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"status {self.status_code}")


class _StubSession:
    """Counts calls so "did not re-download" is an assertion, not a hope."""

    def __init__(self, content: bytes = PAYLOAD, status: int = 200) -> None:
        self.content = content
        self.status = status
        self.calls = 0

    def get(self, url: str, **kwargs: object) -> _StubResponse:
        self.calls += 1
        return _StubResponse(
            self.content,
            {
                "Content-Type": "application/x-zip-compressed",
                "Last-Modified": "Mon, 03 Aug 2026 19:17:07 GMT",
                "ETag": '"545631ad7c23dd1:0"',
                "Content-Length": str(len(self.content)),
            },
            self.status,
        )


def _session(stub: _StubSession) -> requests.Session:
    return cast(requests.Session, stub)


def test_download_preserves_bytes_verbatim(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    stub = _StubSession()
    entry = cache.fetch(URL, session=_session(stub))

    assert cache.read(entry) == PAYLOAD
    assert entry.sha256 == sha256_hex(PAYLOAD)
    assert entry.size_bytes == len(PAYLOAD)


def test_response_headers_are_recorded(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    entry = cache.fetch(URL, session=_session(_StubSession()))

    assert entry.content_type == "application/x-zip-compressed"
    assert entry.last_modified == "Mon, 03 Aug 2026 19:17:07 GMT"
    assert entry.etag == '"545631ad7c23dd1:0"'
    assert entry.header("content-length") == str(len(PAYLOAD))


def test_second_fetch_does_not_download_again(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    stub = _StubSession()
    first = cache.fetch(URL, session=_session(stub))
    second = cache.fetch(URL, session=_session(stub))

    assert stub.calls == 1
    assert first == second


def test_force_downloads_again_and_keeps_one_blob(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    stub = _StubSession()
    first = cache.fetch(URL, session=_session(stub))
    second = cache.fetch(URL, force=True, session=_session(stub))

    assert stub.calls == 2
    # Identical bytes hash identically, so forcing does not fork the store.
    assert first.sha256 == second.sha256
    blobs = list((tmp_path / "blobs").rglob("*.bin"))
    assert len(blobs) == 1


def test_changed_source_bytes_get_a_new_digest(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    first = cache.fetch(URL, session=_session(_StubSession(b"old")))
    second = cache.fetch(URL, force=True, session=_session(_StubSession(b"new")))

    assert first.sha256 != second.sha256
    assert cache.read(first) == b"old"
    assert cache.read(second) == b"new"


def test_reading_an_uncached_artifact_raises(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    entry = CacheEntry(
        url=URL,
        sha256="0" * 64,
        size_bytes=0,
        retrieved_utc="2026-08-12T00:00:00Z",
        http_status=200,
        headers=(),
    )
    with pytest.raises(RawArtifactMissing):
        cache.read(entry)


def test_require_raises_for_unknown_url(tmp_path: Path) -> None:
    with pytest.raises(RawArtifactMissing):
        RawCache(tmp_path).require(URL)


def test_corrupted_blob_is_detected_on_read(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    entry = cache.fetch(URL, session=_session(_StubSession()))
    cache.blob_path(entry.sha256).write_bytes(b"tampered")

    with pytest.raises(CacheIntegrityError):
        cache.read(entry)


def test_missing_blob_makes_the_index_entry_absent(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    entry = cache.fetch(URL, session=_session(_StubSession()))
    cache.blob_path(entry.sha256).unlink()

    assert cache.entry_for(URL) is None


def test_http_error_is_not_cached(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    with pytest.raises(requests.HTTPError):
        cache.fetch(URL, session=_session(_StubSession(b"nope", status=404)))
    assert cache.entry_for(URL) is None


def test_entry_round_trips_through_json(tmp_path: Path) -> None:
    cache = RawCache(tmp_path)
    entry = cache.fetch(URL, session=_session(_StubSession()))
    assert CacheEntry.from_json_dict(entry.to_json_dict()) == entry
