"""EXPLORATORY price adapters. Nothing here is research-grade, by construction.

Read this before using anything in this module
----------------------------------------------
No free ETF or equity price source available to this project provides what a
confirmatory experiment needs: a point-in-time contract, a documented revision
history, delisted and merged share classes, executable rather than indicative
quotes, and a stated total-return and corporate-action methodology. A price
series without those is fine for looking around and useless for deciding
anything, because survivorship and silent adjustment changes bias results in the
direction that makes a strategy look better.

``yfinance`` is not used and is not installed. It is the clearest example of the
problem: adjusted closes are recomputed on every request, delisted tickers vanish,
and there is no published methodology to cite in a manifest.

So this module defines the adapter interface and the guard rail, not a data
supply. Every series carries:

* ``series_kind`` — what the numbers actually are (an exchange close is not a
  fund NAV, and neither is an investable index);
* ``research_grade`` — ``False`` unless an adapter can document the contract
  above. No adapter in this repository sets it ``True``.

:func:`require_research_grade` raises on anything else, so a confirmatory
experiment cannot consume an exploratory series even by accident. Exploratory
work calls :func:`allow_exploratory` instead, which is deliberately a different
name so the choice is visible in the code that made it.

The two implementations, and what was actually observed
------------------------------------------------------
:class:`StooqDailyAdapter` wraps ``https://stooq.com/q/d/l/?s=SPY.US&i=d``.
Checked on 2026-08-12: it never returns CSV to this client. ``curl`` gets HTTP
200 carrying an HTML JavaScript proof-of-work interstitial ("This site requires
JavaScript to verify your browser"), for both upper- and lower-case symbols;
``requests`` gets HTTP 404 for the same URL. The adapter detects the interstitial
and raises :class:`ExploratorySourceUnavailable` rather than parsing HTML into
prices, and lets the 404 surface as an ``HTTPError``. It is kept because the
refusal is the finding, and because a source that starts working again should not
have to be rewritten.

:class:`YahooChartAdapter` wraps ``https://query1.finance.yahoo.com/v8/finance/
chart/<symbol>``. It is the same underlying source as ``yfinance`` and inherits
every one of its problems: ``adjclose`` is recomputed from current dividend and
split data on every request, no adjustment methodology is published, delisted
symbols disappear rather than terminating, and there is no revision history to
diff against. It is exploratory and cannot become otherwise by being called more
carefully.

Yahoo also cannot currently be fetched from this process. Measured on
2026-08-12: ``curl`` with a browser ``User-Agent`` gets HTTP 200 and JSON, while
``requests`` gets HTTP 429 from the same URL with the same headers, with or
without ``Accept``, ``Accept-Language`` or a cleared default header set, and with
a curl agent string too. That pattern is TLS or HTTP/2 client fingerprinting, not
a header problem, and no header this adapter could send would fix it. The parser
is therefore exercised offline against
``tests/fixtures/yahoo_chart_vti_1mo.json``, a verbatim capture of a real
response, and :meth:`YahooChartAdapter.fetch` will surface the 429 as an
``HTTPError`` rather than pretending the source is available.

Header handling differs by host and is not incidental. Yahoo requires a browser
``User-Agent`` to get as far as the 429; FRED, in
:mod:`portfolio_edge.data.fred`, black-holes requests that carry one. Each
adapter sets its own, and neither default is safe to copy to the other.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final, Literal, Protocol, runtime_checkable

from portfolio_edge.data.cache import CacheEntry, RawCache
from portfolio_edge.data.manifest import DatasetManifest, manifest_from_table
from portfolio_edge.data.table import ParsedTable

__all__ = [
    "PARSER_VERSION",
    "STOOQ_ENDPOINT",
    "YAHOO_CHART_ENDPOINT",
    "ExploratorySourceUnavailable",
    "NonResearchGradeSeriesError",
    "PriceAdapter",
    "PriceSeries",
    "SeriesKind",
    "StooqDailyAdapter",
    "YahooChartAdapter",
    "allow_exploratory",
    "build_manifest",
    "require_research_grade",
]

PARSER_VERSION: Final = "prices/1.0.0"
STOOQ_ENDPOINT: Final = "https://stooq.com/q/d/l/"
YAHOO_CHART_ENDPOINT: Final = "https://query1.finance.yahoo.com/v8/finance/chart"

#: Yahoo's edge returns 429 to clients without a browser agent string. Sending
#: one is a condition of the endpoint answering at all, and is recorded here
#: rather than buried at a call site.
_YAHOO_USER_AGENT: Final = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

#: What the numbers in a series are. The research framework requires this on
#: every fund and index series; a "price" with no kind is not usable evidence.
SeriesKind = Literal[
    "exchange_close_price",
    "fund_nav",
    "investable_index",
    "non_investable_peer_index",
    "rules_backtest",
    "live_product",
]


class NonResearchGradeSeriesError(RuntimeError):
    """Raised when a confirmatory experiment is handed an exploratory series."""


class ExploratorySourceUnavailable(RuntimeError):
    """Raised when an exploratory source did not return the data it advertises."""


@dataclass(frozen=True)
class PriceSeries:
    """A price series, stamped with what it is and how far it can be trusted.

    Attributes:
        research_grade: ``False`` unless the provider documents point-in-time
            availability, revision history, delisting coverage, and total-return
            and corporate-action treatment. Defaulting to ``False`` means an
            adapter has to make an affirmative, reviewable claim to become usable
            in confirmatory work.
        adjustment: The provider's stated price-adjustment methodology, or an
            explicit statement that it publishes none.
    """

    symbol: str
    provider_id: str
    series_kind: SeriesKind
    table: ParsedTable
    adjustment: str
    currency: str
    entry: CacheEntry
    research_grade: bool = False
    notes: tuple[str, ...] = ()


def require_research_grade(series: PriceSeries) -> PriceSeries:
    """Return ``series`` if it is research-grade, otherwise raise.

    The gate a confirmatory experiment calls. It refuses rather than warns: a
    warning next to a number that looks like a result is not a control.
    """
    if not series.research_grade:
        raise NonResearchGradeSeriesError(
            f"{series.provider_id}:{series.symbol} is an exploratory series "
            f"(series_kind={series.series_kind}, adjustment={series.adjustment!r}) "
            "and must not be used in a confirmatory experiment. It has no "
            "documented point-in-time contract, revision history, delisting "
            "coverage or total-return methodology. Either label the experiment "
            "exploratory and call allow_exploratory, or obtain a source that "
            "documents those properties."
        )
    return series


def allow_exploratory(series: PriceSeries) -> PriceSeries:
    """Accept a series for exploratory use, recording the choice in its notes."""
    return PriceSeries(
        symbol=series.symbol,
        provider_id=series.provider_id,
        series_kind=series.series_kind,
        table=series.table,
        adjustment=series.adjustment,
        currency=series.currency,
        entry=series.entry,
        research_grade=series.research_grade,
        notes=(
            *series.notes,
            "consumed under allow_exploratory: any result derived from this "
            "series is exploratory and may not be promoted without re-running "
            "on a research-grade source.",
        ),
    )


@runtime_checkable
class PriceAdapter(Protocol):
    """The interface an ETF or price source must implement.

    ``research_grade`` is part of the interface rather than a per-call argument so
    that a provider cannot be upgraded at a call site.
    """

    provider_id: str
    series_kind: SeriesKind
    research_grade: bool

    def url_for(self, symbol: str) -> str:
        """Return the URL this adapter would fetch for ``symbol``."""

    def fetch(
        self, cache: RawCache, symbol: str, *, force: bool = False
    ) -> PriceSeries:
        """Download if needed, then parse from the cache."""


@dataclass(frozen=True)
class StooqDailyAdapter:
    """Daily OHLCV from Stooq's CSV endpoint. Exploratory only.

    Stooq publishes no adjustment methodology, no delisting policy and no
    revision history, so ``research_grade`` is fixed at ``False``. As of
    2026-08-12 it does not serve this client at all: an HTML proof-of-work
    interstitial to ``curl``, HTTP 404 to ``requests``. The parser detects the
    interstitial and raises rather than inventing a price series out of HTML.
    """

    provider_id: str = "stooq"
    series_kind: SeriesKind = "exchange_close_price"
    research_grade: bool = False
    interval: str = "d"

    def url_for(self, symbol: str) -> str:
        return f"{STOOQ_ENDPOINT}?s={symbol}&i={self.interval}"

    def fetch(
        self, cache: RawCache, symbol: str, *, force: bool = False
    ) -> PriceSeries:
        entry = cache.fetch(self.url_for(symbol), force=force)
        return self.parse(cache, entry, symbol)

    def parse(self, cache: RawCache, entry: CacheEntry, symbol: str) -> PriceSeries:
        """Parse a cached Stooq response, or explain why it is not data."""
        raw = cache.read(entry)
        text = raw.decode("utf-8", errors="replace")
        stripped = text.lstrip()
        if stripped.startswith("<") or "<script" in stripped[:2048].lower():
            raise ExploratorySourceUnavailable(
                f"{self.url_for(symbol)} returned HTML, not CSV "
                f"(content-type {entry.content_type!r}, {len(raw)} bytes). Stooq "
                "serves a JavaScript proof-of-work interstitial to non-browser "
                "clients. The response is cached under its own sha256 so this "
                "refusal is reproducible; nothing was parsed."
            )
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            raise ExploratorySourceUnavailable(f"{self.url_for(symbol)} returned no rows")
        header = [cell.strip() for cell in lines[0].split(",")]
        expected = ["Date", "Open", "High", "Low", "Close", "Volume"]
        warnings: list[str] = [
            "EXPLORATORY SOURCE. Stooq publishes no price-adjustment "
            "methodology, no corporate-action treatment, no delisting coverage "
            "and no revision history. These are close prices of whatever the "
            "symbol maps to today; they are not total returns and they are not "
            "point-in-time.",
        ]
        if header[: len(expected)] != expected:
            warnings.append(
                f"column names {header!r} differ from the expected {expected!r}; "
                "the endpoint's schema has changed."
            )
        columns = tuple(header[1:])
        periods: list[str] = []
        values: list[tuple[float | None, ...]] = []
        for line in lines[1:]:
            cells = [cell.strip() for cell in line.split(",")]
            if len(cells) != len(header):
                warnings.append(f"row with {len(cells)} fields was skipped: {line!r}")
                continue
            row: list[float | None] = []
            for cell in cells[1:]:
                try:
                    row.append(float(cell))
                except ValueError:
                    row.append(None)
            periods.append(cells[0])
            values.append(tuple(row))

        table = ParsedTable(
            table_id=f"stooq_{symbol.lower().replace('.', '_')}_daily",
            banner=f"Stooq daily OHLCV for {symbol}",
            columns=columns,
            periods=tuple(periods),
            values=tuple(values),
            frequency="daily",
            source_units="price_and_share_count",
            units="price_and_share_count",
            unit_transform="identity",
            warnings=tuple(warnings),
        )
        return PriceSeries(
            symbol=symbol,
            provider_id=self.provider_id,
            series_kind=self.series_kind,
            table=table,
            adjustment="undocumented; Stooq publishes no adjustment methodology",
            currency="unknown; not stated by the endpoint",
            entry=entry,
            research_grade=False,
        )


@dataclass(frozen=True)
class YahooChartAdapter:
    """Daily bars from Yahoo's chart API. Exploratory only, permanently.

    This is the endpoint ``yfinance`` wraps. It returns an adjusted close, but
    that column is recomputed from today's dividend and split records on every
    request: it is a current opinion about history, not a record of it. Yahoo
    publishes no total-return methodology, no corporate-action policy, no
    delisting coverage and no revision history, so ``research_grade`` is fixed at
    ``False`` and no amount of care at a call site changes that.

    Dates are the exchange-local trading date, derived from each bar's timestamp
    and the ``gmtoffset`` the response reports, rather than a UTC date that would
    silently shift bars across a day boundary.

    :meth:`fetch` currently fails with HTTP 429 from a ``requests`` client; see
    the module docstring. :meth:`parse` works on any cached response, however it
    was obtained, which is the point of separating them.
    """

    provider_id: str = "yahoo_chart"
    series_kind: SeriesKind = "exchange_close_price"
    research_grade: bool = False
    range_: str = "max"
    interval: str = "1d"

    def url_for(self, symbol: str) -> str:
        return (
            f"{YAHOO_CHART_ENDPOINT}/{symbol}"
            f"?range={self.range_}&interval={self.interval}&events=div%7Csplit"
        )

    def fetch(
        self, cache: RawCache, symbol: str, *, force: bool = False
    ) -> PriceSeries:
        entry = cache.fetch(
            self.url_for(symbol), force=force, user_agent=_YAHOO_USER_AGENT
        )
        return self.parse(cache, entry, symbol)

    def parse(self, cache: RawCache, entry: CacheEntry, symbol: str) -> PriceSeries:
        """Parse a cached chart response into an exploratory price series."""
        raw = cache.read(entry)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ExploratorySourceUnavailable(
                f"{self.url_for(symbol)} did not return JSON "
                f"(content-type {entry.content_type!r}, {len(raw)} bytes): {exc}"
            ) from exc
        chart = payload.get("chart") if isinstance(payload, dict) else None
        if not isinstance(chart, dict):
            raise ExploratorySourceUnavailable(f"{symbol}: no chart object in response")
        if chart.get("error"):
            raise ExploratorySourceUnavailable(f"{symbol}: {chart['error']}")
        results = chart.get("result")
        if not isinstance(results, list) or not results:
            raise ExploratorySourceUnavailable(f"{symbol}: empty chart result")
        result = results[0]
        meta = result.get("meta", {})
        timestamps = result.get("timestamp", [])
        quote = result.get("indicators", {}).get("quote", [{}])[0]
        adjclose_block = result.get("indicators", {}).get("adjclose", [{}])
        adjclose = adjclose_block[0].get("adjclose", []) if adjclose_block else []

        warnings: list[str] = [
            "EXPLORATORY SOURCE. This is the endpoint yfinance wraps. The "
            "adjusted close is recomputed from current dividend and split "
            "records on every request, no adjustment or corporate-action "
            "methodology is published, delisted symbols disappear rather than "
            "terminating, and there is no revision history. Do not use for any "
            "result intended to inform a decision.",
            f"instrumentType={meta.get('instrumentType')!r}, "
            f"exchange={meta.get('fullExchangeName')!r}, "
            f"firstTradeDate={meta.get('firstTradeDate')!r} (epoch seconds)",
        ]
        if not timestamps:
            raise ExploratorySourceUnavailable(f"{symbol}: response carried no bars")

        offset = int(meta.get("gmtoffset", 0) or 0)
        columns = ("open", "high", "low", "close", "adjclose", "volume")
        periods: list[str] = []
        values: list[tuple[float | None, ...]] = []
        for index, stamp in enumerate(timestamps):
            local = datetime.fromtimestamp(int(stamp) + offset, tz=UTC)
            periods.append(local.date().isoformat())
            row = tuple(
                _optional_float(_at(quote.get(name, []), index))
                for name in ("open", "high", "low", "close")
            )
            values.append(
                (
                    *row,
                    _optional_float(_at(adjclose, index)),
                    _optional_float(_at(quote.get("volume", []), index)),
                )
            )

        events = result.get("events") or {}
        if events:
            warnings.append(
                "the response carried dividend or split events "
                f"({sorted(events)}); they are preserved in the cached raw bytes "
                "but this parser does not build total returns from them."
            )
        missing = sum(1 for row in values for v in row if v is None)
        if missing:
            warnings.append(
                f"{missing} cells were null in the response and became missing "
                "values, not zeros."
            )

        table = ParsedTable(
            table_id=f"yahoo_{symbol.lower().replace('.', '_')}_{self.interval}",
            banner=f"Yahoo chart {self.interval} bars for {symbol}",
            columns=columns,
            periods=tuple(periods),
            values=tuple(values),
            frequency="daily" if self.interval == "1d" else "unknown",
            source_units="price_and_share_count",
            units="price_and_share_count",
            unit_transform="identity",
            warnings=tuple(warnings),
        )
        return PriceSeries(
            symbol=symbol,
            provider_id=self.provider_id,
            series_kind=self.series_kind,
            table=table,
            adjustment=(
                "undocumented; adjclose is recomputed from current dividend and "
                "split data on every request"
            ),
            currency=str(meta.get("currency", "unknown")),
            entry=entry,
            research_grade=False,
        )


def _at(sequence: object, index: int) -> object:
    if isinstance(sequence, list) and index < len(sequence):
        return sequence[index]
    return None


def _optional_float(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


_TERMS_URL: Final = {
    "stooq": "https://stooq.com/",
    "yahoo_chart": "https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html",
}


def build_manifest(series: PriceSeries) -> DatasetManifest:
    """Build a manifest for an exploratory price series.

    The manifest exists so that an exploratory result can still be reproduced and
    so that its exploratory status is recorded next to its digest, not only in
    whatever prose accompanied it.
    """
    return manifest_from_table(
        dataset_id=f"{series.provider_id}_{series.symbol.lower().replace('.', '_')}",
        entry=series.entry,
        table=series.table,
        parser_version=PARSER_VERSION,
        availability_policy=(
            "Unknown. This provider publishes no availability or point-in-time "
            "contract, so no observation here may be assumed to have been "
            "available on its own date."
        ),
        revision_policy=(
            "Unknown and unbounded. The provider publishes no revision history "
            "and may restate prices or change adjustment on any request. The "
            "sha256 pins the snapshot that was downloaded and nothing else."
        ),
        license_or_terms_url=_TERMS_URL.get(series.provider_id, "unknown"),
        extra_warnings=(
            f"series_kind={series.series_kind}",
            f"research_grade={series.research_grade}",
            f"price adjustment: {series.adjustment}",
            f"currency: {series.currency}",
            "EXPLORATORY: not admissible in a confirmatory experiment. "
            "prices.require_research_grade will refuse it.",
            *series.notes,
        ),
    )
