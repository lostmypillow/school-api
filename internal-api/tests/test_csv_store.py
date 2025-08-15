# tests/test_csv_store.py
from pathlib import Path

import pandas as pd
import pytest
import typer

from lib.csv_store import CSVStore, UserData


@pytest.fixture
def users_csv(tmp_path: Path) -> Path:
    # Copy a realistic test CSV from fixtures to tmp_path
    src = Path(__file__).parent / "fixtures" / "from_db.csv"
    dest = tmp_path / "from_db.csv"
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


@pytest.fixture
def deps_csv(tmp_path: Path) -> Path:
    src = Path(__file__).parent / "fixtures" / "deps.csv"
    dest = tmp_path / "deps.csv"
    dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


@pytest.fixture
def store(users_csv: Path, deps_csv: Path) -> CSVStore:
    return CSVStore(users_csv=users_csv, deps_csv=deps_csv)


def test_clean_df_strips_and_converts_nan_like_values_to_none() -> None:
    df = pd.DataFrame(
        {
            "a": [" x ", None, " y ", float("nan"), " NULL ", " null ", "NaN", "  "],
            "b": [1, float("nan"), None, " z ", " keep ", "NONE", "nAn", ""],
        },
    )
    cleaned = CSVStore._clean_df(df.copy())  # noqa: SLF001
    assert cleaned.loc[0, "a"] == "x"
    assert cleaned.loc[3, "b"] == "z"
    assert cleaned.loc[1, "a"] is None
    assert cleaned.loc[1, "b"] is None
    assert cleaned.loc[2, "b"] is None
    assert cleaned.loc[4, "a"] is None
    assert cleaned.loc[5, "a"] is None
    assert cleaned.loc[6, "a"] is None
    assert cleaned.loc[7, "a"] is None
    assert cleaned.loc[5, "b"] is None
    assert cleaned.loc[6, "b"] is None
    assert cleaned.loc[7, "b"] is None


def test_load_row_returns_userdata_and_trims_fields(store: CSVStore) -> None:
    row0 = store.load_row(0)
    assert isinstance(row0, UserData)
    assert row0.uid.strip() != ""  # sanity
    assert row0.pwd is None or len(row0.pwd) == 8 or row0.pwd.isalpha()  # noqa: PLR2004

    row1 = store.load_row(1)
    assert isinstance(row1, UserData)
    assert row1.uid.strip() != ""
    assert row1.cn.strip() != ""


def test_load_row_out_of_range_low_raises_exit(store: CSVStore) -> None:
    with pytest.raises(typer.Exit):
        store.load_row(-1)


def test_load_row_out_of_range_high_raises_exit(store: CSVStore) -> None:
    with pytest.raises(typer.Exit):
        store.load_row(9999)  # deliberately large


def test_load_all_returns_list_of_userdata(store: CSVStore) -> None:
    users = store.load_all()
    assert isinstance(users, list)
    assert all(isinstance(u, UserData) for u in users)
    assert len(users) > 0


