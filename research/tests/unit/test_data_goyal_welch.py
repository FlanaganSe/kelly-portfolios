"""Offline parser tests for the Goyal-Welch predictor reader.

Two fixtures, both lifted verbatim from real downloads of 2026-08-16:

* ``goyal_welch_predictors_slice.json`` — the header and first and last rows of
  each sheet of ``PredictorData2025.xlsx`` (sha256 ``1e4b6527…``), the Welch and
  Goyal (2008) set.
* ``goyal_welch_zafirov_slice.json`` — the same for ``Data2025.xlsx`` (sha256
  ``bbd61678…``), the 2024 extension, plus the head of its ReadMe sheet.

The slices are stored as rows rather than as ``.xlsx`` bytes; the byte reader is
covered in ``test_data_workbook.py`` and the live downloads by the ``network``
test in ``tests/integration/test_data_network.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from portfolio_edge.data import goyal_welch
from portfolio_edge.data.cache import RawCache
from portfolio_edge.data.workbook import SheetRows

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _sheets(name: str) -> dict[str, SheetRows]:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return {sheet: tuple(tuple(row) for row in rows) for sheet, rows in payload.items()}


@pytest.fixture
def predictors() -> goyal_welch.GoyalWelchFile:
    return goyal_welch.parse_sheets(
        _sheets("goyal_welch_predictors_slice.json"),
        dataset=goyal_welch.get_dataset("goyal_welch_predictors"),
    )


@pytest.fixture
def extended() -> goyal_welch.GoyalWelchFile:
    return goyal_welch.parse_sheets(
        _sheets("goyal_welch_zafirov_slice.json"),
        dataset=goyal_welch.get_dataset("goyal_welch_zafirov_predictors"),
    )


def test_all_three_frequencies_are_landed(predictors: goyal_welch.GoyalWelchFile) -> None:
    assert [t.table_id for t in predictors.tables] == ["monthly", "quarterly", "annual"]
    assert predictors.table("monthly").frequency == "monthly"
    assert predictors.table("annual").frequency == "annual"
    # ParsedTable has no quarterly member, so ignorance is declared rather than
    # a quarter being mislabelled as a month.
    assert predictors.table("quarterly").frequency == "unknown"


def test_each_period_format_decodes_to_an_unambiguous_label(
    predictors: goyal_welch.GoyalWelchFile,
) -> None:
    assert predictors.table("monthly").periods[:3] == ("1871-01", "1871-02", "1871-03")
    assert predictors.table("annual").periods[:3] == ("1871", "1872", "1873")
    # A quarter is labelled by its LAST month, which was verified against the
    # Monthly sheet rather than assumed.
    assert predictors.table("quarterly").periods[:3] == ("1871-03", "1871-06", "1871-09")
    assert any(
        "QUARTERLY SHEET" in w for w in predictors.table("quarterly").warnings
    )


def test_the_quarterly_label_matches_the_monthly_observation_it_claims_to_be(
    predictors: goyal_welch.GoyalWelchFile,
) -> None:
    monthly = predictors.table("monthly")
    quarterly = predictors.table("quarterly")
    march = monthly.values[monthly.periods.index("1871-03")][
        monthly.columns.index("Index")
    ]
    q1 = quarterly.values[quarterly.periods.index("1871-03")][
        quarterly.columns.index("Index")
    ]

    assert march == pytest.approx(q1)


def test_the_nan_string_becomes_missing_and_never_zero(
    predictors: goyal_welch.GoyalWelchFile,
) -> None:
    monthly = predictors.table("monthly")
    row = monthly.values[monthly.periods.index("1871-01")]

    assert row[monthly.columns.index("Index")] == pytest.approx(4.44)
    assert row[monthly.columns.index("tbl")] is None
    assert row[monthly.columns.index("b/m")] is None
    assert any("became missing values, not zeros" in w for w in monthly.warnings)


def test_units_are_declared_per_column_and_nothing_is_converted(
    predictors: goyal_welch.GoyalWelchFile,
) -> None:
    monthly = predictors.table("monthly")

    assert monthly.unit_transform == "identity"
    assert monthly.source_units == monthly.units
    assert "Index=index_level" in monthly.units
    assert "tbl=decimal_per_year" in monthly.units
    assert "b/m=ratio" in monthly.units
    assert "Rfree=decimal_per_period" in monthly.units
    assert "svar=decimal_squared_return" in monthly.units


def test_the_full_sample_predictors_are_named_wherever_they_appear(
    extended: goyal_welch.GoyalWelchFile,
) -> None:
    """The look-ahead the file itself documents, and no hash can detect."""
    warnings = extended.table("monthly").warnings
    flagged = next(w for w in warnings if w.startswith("FULL-SAMPLE PREDICTORS PRESENT"))

    for name in ("cay", "pce", "ogap", "sntm", "fbm", "tchi", "shtint"):
        assert name in flagged
    assert "look-ahead by construction" in flagged


def test_predictors_this_repository_cannot_defend_a_unit_for_are_declared_undeclared(
    extended: goyal_welch.GoyalWelchFile,
) -> None:
    monthly = extended.table("monthly")

    assert "vrp=undeclared" in monthly.units
    assert "impvar=undeclared" in monthly.units
    assert any("no unit is declared for these columns" in w for w in monthly.warnings)
    # The 2008 columns that survive into the extension still carry their units.
    assert "lty=decimal_per_year" in monthly.units


def test_the_readme_sheet_is_captured_when_the_workbook_has_one(
    extended: goyal_welch.GoyalWelchFile, predictors: goyal_welch.GoyalWelchFile
) -> None:
    assert "Description" in extended.readme
    assert predictors.readme == ""


def test_a_missing_declared_sheet_is_fatal() -> None:
    dataset = goyal_welch.get_dataset("goyal_welch_predictors")
    with pytest.raises(goyal_welch.GoyalWelchParseError, match="declared sheet"):
        goyal_welch.parse_sheets({"Renamed": (("yyyymm",),)}, dataset=dataset)


def test_a_renamed_period_column_is_fatal() -> None:
    dataset = goyal_welch.get_dataset("goyal_welch_predictors")
    sheets = _sheets("goyal_welch_predictors_slice.json")
    header = list(sheets["Monthly"][0])
    header[0] = "date"
    sheets["Monthly"] = (tuple(header), *sheets["Monthly"][1:])

    with pytest.raises(goyal_welch.GoyalWelchParseError, match="yyyymm"):
        goyal_welch.parse_sheets(sheets, dataset=dataset)


def test_the_manifest_pins_the_vintage_the_sheet_and_the_document_id(
    predictors: goyal_welch.GoyalWelchFile, tmp_path: Path
) -> None:
    dataset = goyal_welch.get_dataset("goyal_welch_predictors")
    cache = RawCache(tmp_path)
    entry = cache.store(
        dataset.url,
        b"PK\x03\x04 not the real bytes",
        headers={
            "Content-Type": (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            "Content-Disposition": 'attachment; filename="PredictorData2025.xlsx"',
        },
        retrieved_utc="2026-08-16T00:00:00Z",
    )
    manifests = goyal_welch.build_manifests(dataset, entry, predictors)

    assert [m.dataset_id for m in manifests] == [
        "goyal_welch_predictors_monthly",
        "goyal_welch_predictors_quarterly",
        "goyal_welch_predictors_annual",
    ]
    monthly = manifests[0]
    assert "1qwpl2R_DNujpU5YUkk8lacP1tTeMb9iJ" in monthly.source_url
    assert monthly.source_last_modified is None
    assert "NO Last-Modified header" in monthly.availability_policy
    assert "not point-in-time" in monthly.revision_policy.lower()
    assert any(w.startswith("VINTAGE PINNED:") for w in monthly.warnings)
    assert any("document id is part of the data's identity" in w for w in monthly.warnings)
