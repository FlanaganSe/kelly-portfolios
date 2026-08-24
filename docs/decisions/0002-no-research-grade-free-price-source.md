# 0002 — No free price source is research-grade; fund experiments are exploratory

**Status:** scoped historical finding. As of the audit recorded here, the examined free
fund-price feeds did not support confirmatory **fund total-return** inference requiring a
documented distribution and corporate-action contract. This is not a finding about every
free source or every use case. Source reproduction, non-distributing assets, reader-supplied
data, cross-checks, and differently contracted sources require their own fitness review.
See [decision 0010](0010-bars-carry-a-reopening-condition.md).

Date: 2026-08-12. Status: accepted.

## Context

Experiments that audit investable products need total-return histories for funds
and ETFs. Factor files from Ken French do not supply them: they are academic
zero-investment long-short portfolios, not products anyone can hold.

Every free source reachable on 2026-08-12 was tested directly.

| Source | Result |
| --- | --- |
| Stooq CSV | Returns a JavaScript proof-of-work interstitial to `curl` and HTTP 404 to `requests` for the identical URL. Never returns CSV. |
| Yahoo chart API | Returns data to `curl` with a browser agent, HTTP 429 to `requests` under every header combination tried. The difference is TLS/HTTP-2 fingerprinting, not headers. |
| Goyal–Welch at the URL previously recorded | HTTP 404. |
| Shiller `ie_data.xls` | HTTP 404. |

Reachability was never the real problem. Neither Stooq nor Yahoo publishes a
documented total-return contract, corporate-action treatment, delisting coverage,
adjusted-price semantics, or a revision history. A survivorship-free point-in-time
fund universe is exactly what a product audit needs and exactly what they do not
provide.

## Decision

No currently available free price source is research-grade. Price adapters carry
`research_grade = False` and a `series_kind`, and the code **raises** rather than
warns when a confirmatory experiment tries to consume one.

Experiment 002 and any other fund-level work is therefore classified
`exploratory` until a source with documented total-return and corporate-action
treatment is licensed. An exploratory result may motivate further testing. It may
not promote a sleeve, and it may not appear in the app as a finding.

Adapters for blocked sources are kept rather than deleted, because the refusal is
the finding: the Stooq adapter detects the interstitial and raises instead of
parsing HTML into prices, which is the failure this decision exists to prevent.

No dependency is added to defeat bot detection. Circumventing a site's access
controls to obtain data we have decided is not research-grade anyway would add
risk without adding evidence.

## Alternatives considered

**Use yfinance.** Rejected. It is the same underlying source as the Yahoo adapter
and inherits every limitation, while hiding the raw bytes behind a parser and
making source changes invisible.

**Loosen the standard and treat Yahoo as authoritative.** Rejected. It would let
an ETF result that cannot survive its own data contract inform a decision, which
is the specific failure mode this repository is built to make expensive.

**Pay for a licensed source now.** Not rejected — deferred. It is the correct fix
and the only one that upgrades Experiment 002 beyond exploratory. It needs a
budget decision that has not been taken.

## Consequences

Experiment 002 cannot reach a promotion gate on current data, and its conclusion
must state that its limit is the data contract rather than the evidence.

The framework's open question about which point-in-time datasets are licensed,
reproducible, and rich enough stays open, and is now the binding constraint on
investable conclusions rather than one item among many.

Every price snapshot that is taken must still be cached, hashed and manifested, so
an exploratory result remains reconstructible even though it cannot be promoted.
