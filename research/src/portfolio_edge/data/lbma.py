"""LBMA Gold Price reader — a cross-check, not the source a published figure rests on.

READ THIS FIRST: the licence, which is the binding constraint
-------------------------------------------------------------
The endpoint below is the undocumented JSON backend behind lbma.org.uk's own price
charts. It answers HTTP 200 with ``access-control-allow-origin: *`` and no bot
protection, and **open CORS is not a licence grant**. Verified 2026-08-17:

* LBMA, https://www.lbma.org.uk/prices-and-data/precious-metal-prices — "A licence from
  IBA is required in order to obtain, use or redistribute real-time or historical
  benchmark data."
* IBA's own methodology disclaimer — "None of IBA's benchmark and other information may
  be used without a written licence from IBA."
* LBMA states the tabulated historical data "has been moved to our MyLBMA Portal", which
  is behind a login. There is no documented public CSV or XLSX download.
* The restriction is enforced in practice: the World Gold Council's Goldhub states that
  "as of 18 March 2025, only limited LBMA Gold Price data is available on our website.
  Historical LBMA Gold Price data has been removed at the request of the ICE Benchmark
  Administration."
* No research or non-commercial exemption was found in any of those documents. Given
  "may not be used without a written licence", absence reads as prohibition rather than
  as silence.

**Consequence, and it is a design decision rather than a caveat.** The raw bytes live in
the uncommitted cache and only hashes are manifested — the same treatment
:mod:`portfolio_edge.data.fred` gives the ICE BofA total-return indices, for the same
administrator and the same reason. And the primary gold instrument in this repository is
**not** this file but :mod:`portfolio_edge.data.worldbank`, whose Pink Sheet gold series
*is* the London afternoon fixing, monthly-averaged, under CC BY 4.0. This module exists
because a monthly average is a biased instrument for a volatility (see that module) and a
month-end series is the check that prices the bias. It is a cross-check whose numbers may
be reported and whose bytes may not be redistributed.

Why the decision-0002 argument still matters
---------------------------------------------
``docs/decisions/0002-no-research-grade-free-price-source.md`` bans free price feeds
from confirmatory work. Read its *reasoning* rather than its headline: the two failure
modes it names are **a silently dropped distribution** and **a mishandled corporate
action**. A price series without a documented total-return contract cannot be turned
into a total return, so a fund's price history is evidence of nothing.

**Physical gold has neither failure mode, and that is a fact about the asset rather
than about the vendor.** Bullion pays no dividend, no coupon and no distribution of any
kind; it splits nothing and merges with nothing; it is not issued by an entity that can
restate, delist or reorganise. For an unlevered holder of allocated metal,

    total return  =  price return  -  storage and insurance cost,

exactly, with no unobserved cash flow anywhere in the identity. The only free parameter
is the carry cost, which is an **assumption a caller must state**, not a number this
module can silently drop. That is a categorically different situation from an ETF price
whose adjusted close is recomputed on every request.

So the ban does not bind here on its own terms — and that conclusion transfers to the
World Bank series, which is the same benchmark under a licence that permits use. Three
weaker objections remain, and they are why :data:`RESEARCH_GRADE` is ``False`` on both:

1. **No vintage archive.** LBMA republishes one current history. If a past fix is
   corrected, the correction overwrites in place and nothing this code can read records
   it. That is the same limitation FRED carries and it is recorded the same way, in
   ``revision_policy``.
2. **A benchmark auction price is not an execution.** The fix is the clearing price of a
   wholesale auction in Good Delivery bars. A retail holder pays a spread, a vehicle fee,
   or both, and none of that is in these numbers.
3. **The carry cost is assumed.** The identity above is exact only once storage is
   named. This repository has no measured storage series, so any figure derived here
   inherits an assumption rather than a measurement.

None of the three is decision 0002's objection, and the distinction matters: 0002 says
a free price feed *cannot become* a total return, while these three say a gold series
*can*, subject to a stated assumption and without point-in-time resolution. **The
ceiling is therefore `exploratory`, and the reason is different from the reason
elsewhere in this package.**

What the source is, as published
---------------------------------
The LBMA Gold Price is an administered benchmark, not a scraped quote, and the following
is from the administrator's own methodology (version stamped January 2026, read
2026-08-17 at :data:`METHODOLOGY_URL`):

* It is administered by **ICE Benchmark Administration Limited (IBA)**, which is
  "authorised and regulated by the U.K. Financial Conduct Authority (FCA) for the
  regulated activity of administering a benchmark under the U.K. Benchmarks Regulation".
  LBMA owns the benchmark; IBA runs it. LBMA's price page gives 20 March 2015 as the date
  the London Gold Fix ceased, and states that "from 1 April 2015 the LBMA Gold Price
  became a regulated benchmark".
* Gold is auctioned **twice daily, at 10:30 and 15:00 London**, in 30-second rounds: IBA
  publishes a price, participants enter orders, and the round settles if the imbalance is
  inside a threshold — normally 10,000 oz — or repeats at an adjusted price if not.
* **Price formation is in USD only.** GBP and EUR are converted from FX rates at the
  close of the final round and are **not tradeable**. That is the reason only USD is used
  here, and it is a stronger reason than convenience.
* **There is no chair.** The algorithmic auction replaced that role in 2015, so do not
  describe one.

Two things were *not* verifiable and are recorded as such rather than asserted: the exact
1919 start date often quoted for the morning fixing, and any LBMA statement about the
1968 start of the afternoon fixing. Neither matters, because **the published series does
not reach either date**: what this endpoint serves begins in 1968.

The payload is a JSON array of ``{"is_cms_locked": int, "d": "YYYY-MM-DD",
"v": [USD, GBP, EUR]}``. Measured 2026-08-17: ``gold_pm`` carries 14,662 rows from
1968-04-01 to 2026-08-14, strictly increasing in date, no duplicates, no missing months
across 701 consecutive months; the USD column has no missing values at all, GBP has 11
and EUR has 7,737 — the euro did not exist before 1999-01-04, which is where its first
observation sits. ``gold_am`` carries 14,814 rows from 1968-01-02 on the same shape.

**Only the USD column is landed for analysis.** All three are parsed and hashed, because
dropping a column silently is the failure this package exists to prevent. The GBP column
carries at least one visible error — 1968-04-02 reads 37.3 in both USD and GBP, against
15.68 the previous day — which is a second reason no study here should reach for it.

The 1971 break, which is not a data problem but decides the window
------------------------------------------------------------------
Before 15 August 1971 the US dollar price of gold was an administered peg, not a market
price, and a "return" computed across a devaluation records a policy decision. The dates,
from the statutes rather than from a summary of them:

* **1971-08-15** — convertibility suspended, announced by the President that evening.
* **1972-03-31** — Public Law 92-268, the Par Value Modification Act, 86 Stat. 116, sets
  "a new par value of the dollar of $1 equals one thirty-eighth of a fine troy ounce of
  gold". Announced at the Smithsonian in December 1971 and enacted here.
* **1973-09-21** — Public Law 93-110, 87 Stat. 352, replaces that with "forty-two and
  two-ninths dollars per fine troy ounce". Announced February 1973, enacted here.
* **1974-12-31** — Public Law 93-373, 88 Stat. 445, is the date from which the
  regulations on private US gold ownership were eliminated.

Announcement and enactment are months apart in both devaluations; a page citing either
must say which it means. :func:`month_end_usd` returns the whole series and the *caller*
declares its window, with :data:`BRETTON_WOODS_END` here so a study cannot pick the date
by eye. Note the complication in the other direction: the London Gold Pool collapsed in
March 1968 and a two-tier market followed, so the *London* price from 1968-04 is already
a market price even while the *official* US price was pegged. The two devaluations still
pass through it, which is why 1971-09 rather than 1968-04 is the recommended start.

What this module deliberately does not do
------------------------------------------
It does not compute a return. Converting a price level to a total return requires the
storage assumption, and that belongs in a study that states it, not in a parser that
would bury it. :func:`month_end_usd` gives month-end levels and stops.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from portfolio_edge.data.cache import CacheEntry, RawCache
from portfolio_edge.data.manifest import DatasetManifest, manifest_from_table
from portfolio_edge.data.table import ParsedTable

__all__ = [
    "BRETTON_WOODS_END",
    "DATASETS",
    "LICENCE_RESTRICTION",
    "LICENSE_OR_TERMS_URL",
    "METHODOLOGY_URL",
    "PARSER_VERSION",
    "RESEARCH_GRADE",
    "LbmaDataset",
    "LbmaParseError",
    "UnknownDatasetError",
    "build_manifest",
    "download",
    "get_dataset",
    "month_end_usd",
    "parse",
    "parse_bytes",
]

#: Bump on any change to parsing behaviour.
PARSER_VERSION: Final = "lbma/1.0.0"

#: ``False``, and the reason is **not** decision 0002's. See the module docstring: gold
#: has no distribution and no corporate action, so the total-return objection does not
#: apply. What does apply is the absence of a vintage archive, the gap between a
#: wholesale auction price and a retail execution, and the assumed carry cost. Any
#: result derived from this source is ``exploratory``.
RESEARCH_GRADE: Final = False

#: The auction methodology, published by the administrator. Version stamped January 2026,
#: read 2026-08-17. Note ``theice.com/iba/*`` now redirects to ``ice.com/iba/*``.
METHODOLOGY_URL: Final = (
    "https://www.ice.com/publicdocs/"
    "LBMA_Gold_Price_and_LBMA_Silver_Price_Calculation_Methodology.pdf"
)

#: The page stating the licence requirement. It is the honest field to record and it does
#: **not** grant what this download assumes: it says a licence from IBA is required to
#: obtain, use or redistribute the data. See the module docstring.
LICENSE_OR_TERMS_URL: Final = (
    "https://www.lbma.org.uk/prices-and-data/precious-metal-prices"
)

#: What that page and IBA's disclaimer actually say, carried into every manifest so the
#: restriction cannot be lost between here and a result.
LICENCE_RESTRICTION: Final = (
    "LICENCE-RESTRICTED. LBMA: 'A licence from IBA is required in order to obtain, use "
    "or redistribute real-time or historical benchmark data.' IBA: 'None of IBA's "
    "benchmark and other information may be used without a written licence from IBA.' "
    "No research or non-commercial exemption was found (checked 2026-08-17). IBA had "
    "the World Gold Council remove its historical LBMA series in March 2025, so the "
    "restriction is enforced. Raw bytes stay in the uncommitted cache and only hashes "
    "are manifested. The primary gold instrument in this repository is the CC BY 4.0 "
    "World Bank Pink Sheet (portfolio_edge.data.worldbank); this series is a "
    "month-end cross-check on that monthly average."
)

#: The last month in which the US dollar gold price was an administered peg rather than
#: a market price. Convertibility was suspended on 1971-08-15; the Smithsonian
#: devaluation followed in December 1971 and a second in February 1973. A study that
#: wants a market price starts after this month, and says so.
BRETTON_WOODS_END: Final = "1971-08"

#: The currencies in the payload's ``v`` array, in the order the source writes them.
_CURRENCIES: Final = ("USD", "GBP", "EUR")


class UnknownDatasetError(KeyError):
    """Raised when a dataset id is not registered."""


class LbmaParseError(ValueError):
    """Raised when the payload does not have the shape this parser was written for."""


@dataclass(frozen=True)
class LbmaDataset:
    """One published LBMA price series and everything needed to use it correctly.

    Attributes:
        auction: Which daily auction the series records. The two are different
            observations of different moments and must never be spliced.
        first_published: The first date the source itself carries, as measured.
        availability_policy: When a row could first have been known.
        revision_policy: Whether earlier rows can still change.
    """

    dataset_id: str
    url: str
    metal: str
    auction: str
    banner: str
    first_published: str
    availability_policy: str
    revision_policy: str


_AVAILABILITY: Final = (
    "The auction clears at a fixed London time each business day and the price is "
    "published immediately afterwards, so an observation dated D is available at the "
    "end of D in London. The retrieval timestamp in this manifest bounds availability "
    "for the last observation only and says nothing about earlier ones. Note that the "
    "PM auction settles after the US equity market opens and before it closes, so a "
    "same-day pairing of this price with a US equity close is not a synchronous "
    "observation; monthly pairing, which is what every study here uses, is unaffected "
    "to any degree that matters."
)

_REVISION: Final = (
    "Not point-in-time. LBMA republishes one current history and exposes no vintage "
    "archive this code can read, so a corrected fix overwrites in place exactly as a "
    "revised FRED series does. The sha256 in this manifest identifies the file that "
    "was downloaded; it cannot establish that any earlier row read the same on any "
    "earlier date."
)

DATASETS: Final[dict[str, LbmaDataset]] = {
    dataset.dataset_id: dataset
    for dataset in (
        LbmaDataset(
            dataset_id="lbma_gold_pm",
            url="https://prices.lbma.org.uk/json/gold_pm.json",
            metal="gold",
            auction="pm",
            banner=(
                "LBMA Gold Price PM, the afternoon (15:00 London) auction, in USD, GBP "
                "and EUR per troy ounce. Administered by ICE Benchmark Administration; "
                "LBMA gives 2015-03-20 as the date the London Gold Fix ceased."
            ),
            first_published="1968-04-01",
            availability_policy=_AVAILABILITY,
            revision_policy=_REVISION,
        ),
        LbmaDataset(
            dataset_id="lbma_gold_am",
            url="https://prices.lbma.org.uk/json/gold_am.json",
            metal="gold",
            auction="am",
            banner=(
                "LBMA Gold Price AM, the morning (10:30 London) auction, in USD, GBP "
                "and EUR per troy ounce. Administered by ICE Benchmark Administration. "
                "LBMA dates the first gold fix to 1919, but THIS SERIES BEGINS IN 1968 "
                "and no earlier history is published at this endpoint."
            ),
            first_published="1968-01-02",
            availability_policy=_AVAILABILITY,
            revision_policy=_REVISION,
        ),
    )
}


def get_dataset(dataset_id: str) -> LbmaDataset:
    """Look up a registered dataset, or raise :class:`UnknownDatasetError`."""
    try:
        return DATASETS[dataset_id]
    except KeyError:
        raise UnknownDatasetError(
            f"{dataset_id!r} is not registered. Registered: {sorted(DATASETS)}"
        ) from None


def download(
    cache: RawCache,
    dataset: LbmaDataset,
    *,
    force: bool = False,
    timeout: float = 60.0,
) -> CacheEntry:
    """Fetch the JSON into ``cache``, reusing cached bytes unless forced.

    No ``User-Agent`` override. Verified 2026-08-17: prices.lbma.org.uk serves the
    default ``requests`` agent HTTP 200 with ``access-control-allow-origin: *``. There
    is no interstitial, no challenge and nothing to work around; if that ever changes,
    record the refusal rather than defeating it.
    """
    return cache.fetch(dataset.url, force=force, timeout=timeout)


def parse(cache: RawCache, entry: CacheEntry, *, dataset: LbmaDataset) -> ParsedTable:
    """Parse a cached payload. Reads only from the cache."""
    return parse_bytes(cache.read(entry), dataset=dataset)


def parse_bytes(raw: bytes, *, dataset: LbmaDataset) -> ParsedTable:
    """Parse payload bytes into one daily table of currency-per-troy-ounce levels.

    Split from :func:`parse` so the whole path can be exercised offline against a small
    frozen slice of the real payload rather than against a megabyte committed to Git.
    """
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LbmaParseError(f"{dataset.dataset_id}: payload is not JSON: {exc}") from exc
    if not isinstance(payload, list) or not payload:
        raise LbmaParseError(
            f"{dataset.dataset_id}: expected a non-empty JSON array, got "
            f"{type(payload).__name__}"
        )

    warnings: list[str] = []
    periods: list[str] = []
    values: list[tuple[float | None, ...]] = []
    locked: list[str] = []
    missing = {name: 0 for name in _CURRENCIES}

    for index, row in enumerate(payload):
        if not isinstance(row, dict) or "d" not in row or "v" not in row:
            raise LbmaParseError(
                f"{dataset.dataset_id}: row {index} is not a "
                f"{{'d': ..., 'v': [...]}} object: {row!r}. The endpoint's shape has "
                "changed; do not work around it."
            )
        day = str(row["d"])
        cells = row["v"]
        if not isinstance(cells, list) or len(cells) != len(_CURRENCIES):
            raise LbmaParseError(
                f"{dataset.dataset_id}: row {index} dated {day} carries "
                f"{cells!r}, not {len(_CURRENCIES)} currency values."
            )
        parsed: list[float | None] = []
        for name, cell in zip(_CURRENCIES, cells, strict=True):
            if cell is None:
                missing[name] += 1
                parsed.append(None)
                continue
            try:
                parsed.append(float(cell))
            except (TypeError, ValueError):
                missing[name] += 1
                parsed.append(None)
                warnings.append(f"{day}: {name} value {cell!r} is not a number")
        if row.get("is_cms_locked"):
            locked.append(day)
        periods.append(day)
        values.append(tuple(parsed))

    if sorted(periods) != periods:
        raise LbmaParseError(
            f"{dataset.dataset_id}: observation dates are not in increasing order. "
            "The parser relies on source order and will not sort silently."
        )
    if len(set(periods)) != len(periods):
        raise LbmaParseError(f"{dataset.dataset_id}: duplicate observation dates")

    for name, count in missing.items():
        if count:
            warnings.append(
                f"{name} is missing on {count} of {len(periods)} days and those became "
                "missing values, never zeros or carried-forward prices."
            )
    warnings.append(
        "EUR necessarily has no observation before the euro existed on 1999-01-01; a "
        "long EUR gap is the currency's history, not a data fault."
    )
    if locked:
        warnings.append(
            f"{len(locked)} rows carry is_cms_locked=1 ({locked[:6]}). The source "
            "publishes no definition of this flag; it is recorded and ignored, and no "
            "value was altered because of it."
        )
    warnings.append(
        "values are the auction clearing price per troy ounce of gold, in the stated "
        "currency, as published. They are a wholesale benchmark in Good Delivery "
        "bars, not a price any retail holder transacts at, and they are a "
        "PRICE LEVEL, not a return: gold pays no distribution, so a total return is "
        "the price return less an explicitly stated storage and vehicle cost."
    )
    warnings.append(
        "the US dollar price was an administered peg until convertibility was "
        f"suspended on 1971-08-15 (see BRETTON_WOODS_END={BRETTON_WOODS_END!r}); the "
        "par value was reset by PL 92-268 (1972-03-31, 86 Stat. 116) and PL 93-110 "
        "(1973-09-21, 87 Stat. 352), and regulations on private US gold ownership were "
        "eliminated from 1974-12-31 by PL 93-373 (88 Stat. 445). Returns computed "
        "across those dates describe policy, not a market a US investor could hold."
    )

    return ParsedTable(
        table_id=f"{dataset.metal}_{dataset.auction}",
        banner=dataset.banner,
        columns=_CURRENCIES,
        periods=tuple(periods),
        values=tuple(values),
        frequency="daily",
        source_units="currency_per_troy_ounce",
        units="currency_per_troy_ounce",
        unit_transform="identity",
        warnings=tuple(warnings),
    )


def month_end_usd(table: ParsedTable) -> tuple[tuple[str, float], ...]:
    """Month-end USD levels: the last published USD fix in each calendar month.

    Returns ``(("YYYY-MM", level), ...)`` in increasing order, skipping any month whose
    every USD observation is missing. **The last published fix, not the fix on the last
    calendar day** — the auction does not run at weekends or on London holidays, so
    demanding a specific date would drop months rather than describe them. No value is
    interpolated and none is carried across a month boundary.
    """
    if "USD" not in table.columns:
        raise LbmaParseError(f"{table.table_id}: no USD column in {table.columns}")
    usd = table.column("USD")
    latest: dict[str, float] = {}
    for period, value in zip(table.periods, usd, strict=True):
        if value is None:
            continue
        latest[period[:7]] = value
    return tuple((month, latest[month]) for month in sorted(latest))


def build_manifest(
    dataset: LbmaDataset,
    entry: CacheEntry,
    table: ParsedTable,
    *,
    extra_warnings: Sequence[str] = (),
) -> DatasetManifest:
    """Build the manifest for one LBMA series."""
    return manifest_from_table(
        dataset_id=dataset.dataset_id,
        entry=entry,
        table=table,
        parser_version=PARSER_VERSION,
        availability_policy=dataset.availability_policy,
        revision_policy=dataset.revision_policy,
        license_or_terms_url=LICENSE_OR_TERMS_URL,
        extra_warnings=(
            LICENCE_RESTRICTION,
            f"AUCTION PINNED: {dataset.auction.upper()}. The AM and PM auctions are "
            "different observations of different moments and must never be spliced.",
            "administrator: ICE Benchmark Administration, authorised and regulated by "
            "the UK FCA for administering a benchmark under the UK Benchmarks "
            "Regulation. LBMA gives 2015-03-20 as the date the London Gold Fix ceased. "
            "Price formation is in USD only; GBP and EUR are converted at the close of "
            f"the final round and are not tradeable. Methodology: {METHODOLOGY_URL}",
            f"research_grade={RESEARCH_GRADE}. The reason is NOT decision 0002's "
            "total-return objection, which does not apply to an asset with no "
            "distribution and no corporate action. It is the absence of a vintage "
            "archive, the gap between a wholesale auction price and a retail "
            "execution, and the fact that the carry cost is assumed rather than "
            "measured. Results are exploratory.",
            *extra_warnings,
        ),
    )
