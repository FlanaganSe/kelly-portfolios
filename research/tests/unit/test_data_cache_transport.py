"""The ``curl`` transport and ranged fetches added for the fund audit.

Shelling out to ``curl`` exists for one measured reason: some hosts discriminate
on TLS and HTTP/2 fingerprint rather than on headers, so ``requests`` is refused
where ``curl`` carrying identical headers is served. These tests exercise the
parts of that path that do not need a network, and pin the one invariant that
would otherwise corrupt the cache: a ranged response is a prefix, not the file.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import requests

from portfolio_edge.data.cache import RawCache, _parse_header_block, range_key


def test_a_ranged_fetch_is_stored_under_its_own_key() -> None:
    """A 64 KB prefix must never be served later as if it were the whole document."""
    url = "https://example.invalid/primary_doc.xml"
    assert range_key(url, None) == url
    assert range_key(url, (0, 65535)) == f"{url}#bytes=0-65535"
    assert range_key(url, (0, 65535)) != range_key(url, (0, 1023))


def test_the_last_header_block_wins_after_a_redirect() -> None:
    """``curl --location`` writes one block per hop; only the final one describes the bytes."""
    dump = (
        "HTTP/1.1 301 Moved Permanently\r\n"
        "Location: https://example.invalid/final\r\n"
        "\r\n"
        "HTTP/2 200 \r\n"
        "content-type: text/xml\r\n"
        "last-modified: Thu, 25 Jun 2026 17:30:32 GMT\r\n"
        "\r\n"
    )
    status, headers = _parse_header_block(dump)
    assert status == 200
    assert headers["content-type"] == "text/xml"
    assert headers["last-modified"].endswith("GMT")


def test_a_429_is_reported_as_the_status_it_is() -> None:
    dump = "HTTP/2 429 \r\nretry-after: 60\r\n\r\n"
    status, headers = _parse_header_block(dump)
    assert status == 429
    assert headers["retry-after"] == "60"


def test_an_unparseable_status_line_is_refused_rather_than_guessed() -> None:
    with pytest.raises(RuntimeError, match="unparseable curl status line"):
        _parse_header_block("not a status line\r\nfoo: bar\r\n\r\n")


def test_an_empty_dump_is_refused() -> None:
    with pytest.raises(RuntimeError, match="no response headers"):
        _parse_header_block("   \n\n  ")


def test_a_cached_ranged_entry_is_returned_without_touching_the_network(
    tmp_path: Path,
) -> None:
    """``fetch_via_curl`` must be a no-op when the exact ranged key is already stored."""
    cache = RawCache(tmp_path)
    url = "https://example.invalid/doc.xml"
    stored = cache.store(range_key(url, (0, 15)), b"sixteen bytes!!!")
    entry = cache.fetch_via_curl(url, byte_range=(0, 15))
    assert entry.sha256 == stored.sha256
    assert cache.read(entry) == b"sixteen bytes!!!"


def test_curl_failures_surface_as_errors_rather_than_empty_data(tmp_path: Path) -> None:
    """A source that will not answer must raise, never return zero bytes."""
    cache = RawCache(tmp_path)
    with pytest.raises((RuntimeError, requests.HTTPError)):
        cache.fetch_via_curl(
            "https://127.0.0.1:1/definitely-not-listening", timeout=2.0, attempts=1
        )
