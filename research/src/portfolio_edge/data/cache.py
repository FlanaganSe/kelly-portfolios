"""Content-addressed cache for raw downloaded bytes.

The cache lives outside Git (default ``research/cache/``) and holds the *exact*
bytes a source returned, together with the HTTP response headers that arrived
with them. Nothing in this package parses a byte it did not first read back out
of this cache, so every derived table is traceable to a stored artifact.

What a hash proves, and what it does not
----------------------------------------
``sha256`` identifies *which file was used*. It says nothing about whether that
file represents what was publicly available at any earlier date. Ken French and
FRED both rebuild their full history from the current source vintage and publish
no archive of prior vintages, so a hash recorded today cannot be used to assert
that a 1963 observation was the same number in 1990, or in 2019. Point-in-time
claims require a vintage archive; identity claims require a hash. They are
different claims and this package keeps them apart: see
:mod:`portfolio_edge.data.manifest`, whose ``revision_policy`` field carries the
vintage caveat while ``sha256_raw`` carries the identity claim.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

import requests

__all__ = [
    "CACHE_ENV_VAR",
    "CacheEntry",
    "CacheIntegrityError",
    "RawArtifactMissing",
    "RawCache",
    "default_cache_root",
    "range_key",
    "sha256_hex",
]

CACHE_ENV_VAR: Final = "PORTFOLIO_EDGE_CACHE_DIR"

#: Seconds to wait between retry attempts. Short, and bounded by ``attempts``.
_RETRY_BACKOFF_SECONDS: Final = 2.0

#: Statuses that mean "not now" rather than "not ever", and are retried within
#: the attempt budget. Yahoo's edge in particular answers 429 to a client it
#: serves normally seconds later.
_RETRYABLE_STATUSES: Final = frozenset({429, 500, 502, 503, 504})

#: Grace added to ``curl``'s own ``--max-time`` before the subprocess is killed,
#: so that a timeout is reported by curl rather than by an opaque process kill.
_CURL_TIMEOUT_SLACK_SECONDS: Final = 15.0


def range_key(url: str, byte_range: tuple[int, int] | None) -> str:
    """The cache key for a possibly-ranged fetch of ``url``.

    A ranged response is a *prefix*, not the file, so it is stored under its own
    key. Without this a 64 KB prefix and the whole document would collide in the
    URL index and the parser could silently be handed the wrong one.
    """
    if byte_range is None:
        return url
    return f"{url}#bytes={byte_range[0]}-{byte_range[1]}"


def _parse_header_block(text: str) -> tuple[int, dict[str, str]]:
    """Return the status code and headers of the *last* response in ``text``.

    ``curl --location`` writes one header block per hop. Only the final hop
    describes the bytes that were actually saved.
    """
    blocks = [block for block in text.replace("\r\n", "\n").split("\n\n") if block.strip()]
    if not blocks:
        raise RuntimeError("curl returned no response headers")
    lines = [line for line in blocks[-1].split("\n") if line.strip()]
    status_parts = lines[0].split()
    if len(status_parts) < 2 or not status_parts[1].isdigit():
        raise RuntimeError(f"unparseable curl status line: {lines[0]!r}")
    headers: dict[str, str] = {}
    for line in lines[1:]:
        name, separator, value = line.partition(":")
        if separator:
            headers[name.strip()] = value.strip()
    return int(status_parts[1]), headers


def _run_curl(
    url: str,
    *,
    timeout: float,
    user_agent: str | None,
    byte_range: tuple[int, int] | None,
) -> tuple[int, dict[str, str], bytes]:
    """Run ``curl`` once, returning the final status, headers and body bytes."""
    with tempfile.TemporaryDirectory(prefix="portfolio-edge-curl-") as workspace:
        body_path = Path(workspace) / "body"
        header_path = Path(workspace) / "headers"
        command = [
            "curl",
            "--silent",
            "--show-error",
            "--location",
            "--max-time",
            str(int(timeout)),
            "--dump-header",
            str(header_path),
            "--output",
            str(body_path),
        ]
        if user_agent is not None:
            command += ["--user-agent", user_agent]
        if byte_range is not None:
            command += ["--range", f"{byte_range[0]}-{byte_range[1]}"]
        command.append(url)
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                check=False,
                timeout=timeout + _CURL_TIMEOUT_SLACK_SECONDS,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise RuntimeError(f"curl could not run for {url}: {exc}") from exc
        if completed.returncode != 0:
            detail = completed.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"curl exited {completed.returncode} for {url}: {detail}")
        if not header_path.is_file():
            raise RuntimeError(f"curl wrote no headers for {url}")
        status, headers = _parse_header_block(
            header_path.read_text(encoding="utf-8", errors="replace")
        )
        body = body_path.read_bytes() if body_path.is_file() else b""
    return status, headers, body


class RawArtifactMissing(KeyError):
    """Raised when a parse is attempted without a cached raw artifact."""


class CacheIntegrityError(RuntimeError):
    """Raised when a stored blob no longer hashes to its recorded digest."""


def sha256_hex(data: bytes) -> str:
    """Return the hex SHA-256 digest of ``data``."""
    return hashlib.sha256(data).hexdigest()


def default_cache_root() -> Path:
    """Resolve the default cache root.

    Order of preference: the ``PORTFOLIO_EDGE_CACHE_DIR`` environment variable,
    then ``<research workspace>/cache`` when this module is being imported from a
    source checkout, then ``./cache``. The workspace directory is identified by
    the presence of ``pyproject.toml``, so an installed wheel does not write into
    ``site-packages``.
    """
    override = os.environ.get(CACHE_ENV_VAR)
    if override:
        return Path(override).expanduser()
    workspace = Path(__file__).resolve().parents[3]
    if (workspace / "pyproject.toml").is_file():
        return workspace / "cache"
    return Path.cwd() / "cache"


@dataclass(frozen=True)
class CacheEntry:
    """A stored raw artifact and the HTTP exchange that produced it.

    ``headers`` holds every response header the server actually returned, in
    arrival order, with lower-cased names. It is kept whole because a header the
    parser ignores today (``content-encoding``, ``content-disposition``) is often
    the one that explains a later discrepancy.
    """

    url: str
    sha256: str
    size_bytes: int
    retrieved_utc: str
    http_status: int
    headers: tuple[tuple[str, str], ...]

    def header(self, name: str) -> str | None:
        """Return the first response header called ``name``, or ``None``."""
        wanted = name.lower()
        for key, value in self.headers:
            if key == wanted:
                return value
        return None

    @property
    def content_type(self) -> str:
        return self.header("content-type") or "application/octet-stream"

    @property
    def last_modified(self) -> str | None:
        return self.header("last-modified")

    @property
    def etag(self) -> str | None:
        return self.header("etag")

    def to_json_dict(self) -> dict[str, object]:
        return {
            "url": self.url,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "retrieved_utc": self.retrieved_utc,
            "http_status": self.http_status,
            "headers": [list(pair) for pair in self.headers],
        }

    @classmethod
    def from_json_dict(cls, payload: Mapping[str, object]) -> CacheEntry:
        raw_headers = payload.get("headers", [])
        headers: list[tuple[str, str]] = []
        if isinstance(raw_headers, list):
            for item in raw_headers:
                if isinstance(item, list) and len(item) == 2:
                    headers.append((str(item[0]), str(item[1])))
        return cls(
            url=str(payload["url"]),
            sha256=str(payload["sha256"]),
            size_bytes=int(str(payload["size_bytes"])),
            retrieved_utc=str(payload["retrieved_utc"]),
            http_status=int(str(payload["http_status"])),
            headers=tuple(headers),
        )


def _utc_now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalise_headers(headers: Mapping[str, str]) -> tuple[tuple[str, str], ...]:
    return tuple((str(key).lower(), str(value)) for key, value in headers.items())


class RawCache:
    """A content-addressed store of raw downloaded bytes.

    Blobs are addressed by digest under ``blobs/``. A small index under
    ``index/`` maps a URL to the entry last retrieved from it, which is what
    makes "do not download again" possible: the digest of a remote file cannot be
    known before fetching it, so the URL is the only usable pre-fetch key.
    """

    def __init__(self, root: Path | None = None) -> None:
        self._root = Path(root) if root is not None else default_cache_root()

    @property
    def root(self) -> Path:
        return self._root

    def blob_path(self, sha256: str) -> Path:
        return self._root / "blobs" / sha256[:2] / f"{sha256}.bin"

    def _index_path(self, url: str) -> Path:
        return self._root / "index" / f"{sha256_hex(url.encode('utf-8'))}.json"

    def entry_for(self, url: str) -> CacheEntry | None:
        """Return the cached entry for ``url``, or ``None`` if there is none.

        An index record whose blob has gone missing is treated as absent rather
        than as an error, so a partially deleted cache heals on the next fetch.
        """
        path = self._index_path(url)
        if not path.is_file():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return None
        entry = CacheEntry.from_json_dict(payload)
        if not self.blob_path(entry.sha256).is_file():
            return None
        return entry

    def has(self, sha256: str) -> bool:
        return self.blob_path(sha256).is_file()

    def read(self, entry: CacheEntry) -> bytes:
        """Read the raw bytes for ``entry``, verifying the digest on every read.

        Raises:
            RawArtifactMissing: the blob is not in this cache. Parsers surface
                this rather than silently re-downloading, which keeps parsing a
                pure function of stored bytes.
            CacheIntegrityError: the blob no longer hashes to its recorded
                digest, so the manifest that cites it would be a false claim.
        """
        path = self.blob_path(entry.sha256)
        if not path.is_file():
            raise RawArtifactMissing(
                f"no cached raw artifact {entry.sha256} for {entry.url}; "
                "download it before parsing"
            )
        data = path.read_bytes()
        actual = sha256_hex(data)
        if actual != entry.sha256:
            raise CacheIntegrityError(
                f"cached blob {path} hashes to {actual}, expected {entry.sha256}"
            )
        return data

    def store(
        self,
        url: str,
        data: bytes,
        *,
        headers: Mapping[str, str] | None = None,
        http_status: int = 200,
        retrieved_utc: str | None = None,
    ) -> CacheEntry:
        """Store ``data`` verbatim under its digest and index it against ``url``.

        Used by :meth:`fetch` and by offline tests that seed the cache from a
        frozen fixture. The bytes are never transformed: no newline translation,
        no decoding, no re-compression.
        """
        digest = sha256_hex(data)
        blob = self.blob_path(digest)
        blob.parent.mkdir(parents=True, exist_ok=True)
        if not blob.is_file():
            tmp = blob.with_suffix(".bin.partial")
            tmp.write_bytes(data)
            tmp.replace(blob)
        entry = CacheEntry(
            url=url,
            sha256=digest,
            size_bytes=len(data),
            retrieved_utc=retrieved_utc or _utc_now_iso(),
            http_status=http_status,
            headers=_normalise_headers(headers or {}),
        )
        index = self._index_path(url)
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text(
            json.dumps(entry.to_json_dict(), indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
        return entry

    def fetch(
        self,
        url: str,
        *,
        force: bool = False,
        timeout: float = 60.0,
        session: requests.Session | None = None,
        user_agent: str | None = None,
        attempts: int = 3,
    ) -> CacheEntry:
        """Return the cached entry for ``url``, downloading only when needed.

        A cached entry whose blob is present is returned untouched. Passing
        ``force=True`` re-downloads and re-indexes; if the bytes are unchanged
        the digest and therefore the blob are unchanged, and only the retrieval
        timestamp and headers move.

        Args:
            user_agent: Sent as the ``User-Agent`` header. ``None`` sends
                whatever ``requests`` sends by default, which is the right choice
                more often than it looks: the FRED edge silently black-holes
                requests carrying a browser-shaped or unfamiliar agent string,
                while Yahoo's chart endpoint refuses requests without one. The
                header is a per-source property, so each reader sets it and the
                cache does not impose a default.
            attempts: Bounded retries on transport errors. Edge protection on
                these hosts fails as a hung connection rather than a status code,
                and a single timeout is not evidence that a source is down.

        Raises:
            requests.HTTPError: the server did not return 2xx.
            requests.RequestException: every attempt failed at the transport
                level.
        """
        if not force:
            cached = self.entry_for(url)
            if cached is not None:
                return cached
        getter = session.get if session is not None else requests.get
        headers = {"User-Agent": user_agent} if user_agent is not None else {}
        last_error: Exception | None = None
        for attempt in range(max(1, attempts)):
            try:
                response = getter(url, timeout=timeout, headers=headers)
            except requests.RequestException as exc:
                last_error = exc
                if attempt + 1 < attempts:
                    time.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1))
                continue
            response.raise_for_status()
            return self.store(
                url,
                response.content,
                headers=dict(response.headers),
                http_status=response.status_code,
            )
        if last_error is None:  # pragma: no cover - unreachable with attempts >= 1
            raise RuntimeError(f"fetch({url!r}) made no attempt")
        raise last_error

    def fetch_via_curl(
        self,
        url: str,
        *,
        force: bool = False,
        timeout: float = 60.0,
        user_agent: str | None = None,
        byte_range: tuple[int, int] | None = None,
        attempts: int = 3,
    ) -> CacheEntry:
        """Fetch ``url`` by shelling out to ``curl``, and cache the bytes verbatim.

        Why this exists, and why it is not the default
        ----------------------------------------------
        Some hosts distinguish clients by their TLS and HTTP/2 fingerprint rather
        than by their headers. Yahoo's chart endpoint is the measured example:
        ``requests`` receives HTTP 429 for a URL that ``curl`` carrying the same
        headers is served normally, and no header this package could send closes
        that gap. Shelling out to the system ``curl`` is the smallest way to reach
        such a host, and it is deliberately preferred to adding a dependency whose
        purpose is to imitate a browser's TLS stack.

        This does **not** make such a source research-grade. It only means the
        bytes can be snapshotted, hashed and manifested, so that an exploratory
        result stays reconstructible. See
        ``docs/decisions/0002-no-research-grade-free-price-source.md``.

        Args:
            byte_range: Inclusive ``(first, last)`` byte offsets, sent as an HTTP
                ``Range`` header. A ranged response is cached under a key that
                carries the range, so a prefix can never be mistaken for, or
                overwrite, the whole file. Servers that ignore ``Range`` return
                the whole body and HTTP 200; the caller sees the real status and
                length and can decide, which is why this method does not enforce
                206.

        Raises:
            RuntimeError: ``curl`` is unavailable, or every attempt failed.
            requests.HTTPError: the server answered with a non-2xx status. The
                exception type matches :meth:`fetch` so callers handle one kind.
        """
        key = range_key(url, byte_range)
        if not force:
            cached = self.entry_for(key)
            if cached is not None:
                return cached

        last_error: Exception | None = None
        for attempt in range(max(1, attempts)):
            try:
                status, headers, body = _run_curl(
                    url,
                    timeout=timeout,
                    user_agent=user_agent,
                    byte_range=byte_range,
                )
            except RuntimeError as exc:
                last_error = exc
                if attempt + 1 < attempts:
                    time.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1))
                continue
            if status in _RETRYABLE_STATUSES and attempt + 1 < attempts:
                # Yahoo's edge answers 429 intermittently to a client it serves
                # normally seconds later, so one refusal is not evidence that a
                # source is unavailable. Back off and try again.
                last_error = requests.HTTPError(f"HTTP {status} for {url}")
                time.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1) ** 2)
                continue
            if not 200 <= status < 300:
                raise requests.HTTPError(f"HTTP {status} for {url}")
            return self.store(key, body, headers=headers, http_status=status)

        raise last_error or RuntimeError(f"fetch_via_curl({url!r}) made no attempt")

    def require(self, url: str) -> CacheEntry:
        """Return the cached entry for ``url`` or raise.

        The entry point for code paths that must not reach the network.
        """
        entry = self.entry_for(url)
        if entry is None:
            raise RawArtifactMissing(f"no cached raw artifact for {url}")
        return entry
