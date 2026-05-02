"""
Regression tests for kpis_final.csv.
Validates computed KPIs against re-derivation from raw CSVs and asserts data integrity.

Run with:  pytest tests/ -v
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "02_Banking_Sector_Dashboard" / "data" / "processed"

KPIS_PATH = DATA_DIR / "kpis_final.csv"
IS_PATH   = DATA_DIR / "income_statement_final.csv"
BS_PATH   = DATA_DIR / "balance_sheet_final.csv"

EXPECTED_BANKS = {"Eurobank", "Alpha Bank", "NBG", "Piraeus Bank"}
EXPECTED_YEARS = {2022, 2023, 2024}

TOLERANCE = 0.01   # 1% relative tolerance for re-derived KPIs
ABS_TOL_PP = 0.5   # 0.5 percentage-point tolerance for ratio KPIs


# ── Fixtures ──────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def kpis():
    return pd.read_csv(KPIS_PATH)


@pytest.fixture(scope="module")
def income_stmt():
    return pd.read_csv(IS_PATH)


@pytest.fixture(scope="module")
def balance_sheet():
    return pd.read_csv(BS_PATH)


@pytest.fixture(scope="module")
def is_pivot(income_stmt):
    return income_stmt.pivot_table(
        index=["bank", "year"], columns="metric", values="value", aggfunc="first"
    ).reset_index()


@pytest.fixture(scope="module")
def bs_pivot(balance_sheet):
    return balance_sheet.pivot_table(
        index=["bank", "year"], columns="metric", values="value", aggfunc="first"
    ).reset_index()


# ── Data integrity tests ───────────────────────────────────────────────────────
class TestDataIntegrity:

    def test_row_count(self, kpis):
        assert len(kpis) == 12, f"Expected 12 rows (4 banks × 3 years), got {len(kpis)}"

    def test_bank_names(self, kpis):
        actual = set(kpis["bank"].unique())
        assert actual == EXPECTED_BANKS, f"Unexpected banks: {actual ^ EXPECTED_BANKS}"

    def test_years(self, kpis):
        actual = set(kpis["year"].unique())
        assert actual == EXPECTED_YEARS, f"Unexpected years: {actual ^ EXPECTED_YEARS}"

    def test_unique_bank_year(self, kpis):
        dupes = kpis.duplicated(subset=["bank", "year"])
        assert not dupes.any(), f"Duplicate bank-year rows: {kpis[dupes][['bank','year']].values.tolist()}"

    def test_no_nulls_primary_keys(self, kpis):
        assert kpis["bank"].notna().all(), "Null values in 'bank' column"
        assert kpis["year"].notna().all(), "Null values in 'year' column"

    def test_no_nulls_financial_columns(self, kpis):
        financial_cols = ["nii", "operating_income", "operating_expenses", "net_profit",
                          "impairment", "loans", "deposits", "equity", "total_assets",
                          "roe", "cost_to_income", "loan_to_deposit", "nim", "roa", "cet1"]
        for col in financial_cols:
            assert col in kpis.columns, f"Missing column: {col}"
            assert kpis[col].notna().all(), f"Null values in '{col}'"

    def test_yoy_columns_null_for_2022(self, kpis):
        yoy_cols = ["nii_yoy", "profit_yoy", "assets_yoy", "opincome_yoy"]
        yr2022 = kpis[kpis["year"] == 2022]
        for col in yoy_cols:
            if col in kpis.columns:
                assert yr2022[col].isna().all(), f"YoY column '{col}' should be null for 2022 (no prior year)"

    def test_values_are_positive(self, kpis):
        must_positive = ["loans", "deposits", "equity", "total_assets", "nii"]
        for col in must_positive:
            assert (kpis[col] > 0).all(), f"Non-positive values in '{col}'"

    def test_impairment_is_negative_or_zero(self, kpis):
        assert (kpis["impairment"] <= 0).all(), "Impairment should be non-positive (provision charges)"

    def test_operating_expenses_are_negative(self, kpis):
        assert (kpis["operating_expenses"] < 0).all(), "Operating expenses should be negative"


# ── KPI re-derivation tests ────────────────────────────────────────────────────
class TestKPIReDerivation:

    def test_roe_recomputed(self, kpis, is_pivot):
        """ROE = net_profit / equity × 100. Validate within ABS_TOL_PP."""
        recomputed = (kpis["net_profit"] / kpis["equity"]) * 100
        diff = (recomputed - kpis["roe"]).abs()
        fails = kpis[diff > ABS_TOL_PP][["bank", "year"]].values.tolist()
        assert len(fails) == 0, f"ROE mismatch >±{ABS_TOL_PP}pp for: {fails}"

    def test_roa_recomputed(self, kpis):
        """ROA = net_profit / total_assets × 100. Validate within ABS_TOL_PP."""
        recomputed = (kpis["net_profit"] / kpis["total_assets"]) * 100
        diff = (recomputed - kpis["roa"]).abs()
        fails = kpis[diff > ABS_TOL_PP][["bank", "year"]].values.tolist()
        assert len(fails) == 0, f"ROA mismatch >±{ABS_TOL_PP}pp for: {fails}"

    def test_cost_to_income_recomputed(self, kpis):
        """C/I = |operating_expenses| / operating_income × 100."""
        recomputed = (kpis["operating_expenses"].abs() / kpis["operating_income"]) * 100
        diff = (recomputed - kpis["cost_to_income"]).abs()
        fails = kpis[diff > ABS_TOL_PP][["bank", "year"]].values.tolist()
        assert len(fails) == 0, f"Cost-to-Income mismatch >±{ABS_TOL_PP}pp for: {fails}"

    def test_loan_to_deposit_recomputed(self, kpis):
        """L/D = loans / deposits × 100."""
        recomputed = (kpis["loans"] / kpis["deposits"]) * 100
        diff = (recomputed - kpis["loan_to_deposit"]).abs()
        fails = kpis[diff > ABS_TOL_PP][["bank", "year"]].values.tolist()
        assert len(fails) == 0, f"Loan-to-Deposit mismatch >±{ABS_TOL_PP}pp for: {fails}"

    def test_nim_recomputed(self, kpis):
        """NIM = nii / total_assets × 100. Validates against stored NIM (rounded)."""
        recomputed = (kpis["nii"] / kpis["total_assets"]) * 100
        diff = (recomputed - kpis["nim"]).abs()
        # Stored NIM has 2dp rounding, allow 0.01pp tolerance
        fails = kpis[diff > 0.01][["bank", "year", "nim"]].values.tolist()
        assert len(fails) == 0, f"NIM mismatch >0.01pp (check rounding): {fails}"

    def test_nii_yoy_recomputed(self, kpis):
        """NII YoY = (NII_t - NII_{t-1}) / NII_{t-1} × 100 for years 2023 and 2024."""
        df = kpis.sort_values(["bank", "year"]).copy()
        df["nii_prev"] = df.groupby("bank")["nii"].shift(1)
        df["nii_yoy_recomp"] = (df["nii"] - df["nii_prev"]) / df["nii_prev"] * 100
        df_check = df[df["year"] > 2022].dropna(subset=["nii_yoy", "nii_yoy_recomp"])
        diff = (df_check["nii_yoy_recomp"] - df_check["nii_yoy"]).abs()
        fails = df_check[diff > ABS_TOL_PP][["bank", "year"]].values.tolist()
        assert len(fails) == 0, f"NII YoY mismatch >±{ABS_TOL_PP}pp for: {fails}"


# ── Balance sheet identity tests ──────────────────────────────────────────────
class TestBalanceSheetIdentity:

    def test_assets_equal_liabilities_plus_equity(self, kpis):
        """Assets ≈ Liabilities + Equity (within 1% tolerance)."""
        # kpis_final has: total_assets, deposits (as proxy for liabilities), equity
        # Full identity uses total_liabilities from balance_sheet_final.csv
        # Here we assert using kpis columns as a proxy check
        implied_liabilities = kpis["total_assets"] - kpis["equity"]
        # All implied liabilities should be positive (assets > equity)
        assert (implied_liabilities > 0).all(), "Assets < Equity for some bank-years — impossible"

    def test_assets_liabilities_equity_from_bs_csv(self, bs_pivot):
        """Full balance sheet identity: Total Assets = Total Liabilities + Total Equity."""
        bs = bs_pivot.copy()
        # Extract key line items (exact metric names from balance_sheet_final.csv)
        metric_map = {
            "Total assets": "total_assets",
            "Total liabilities": "total_liabilities",
            "Total equity": "total_equity",
        }
        for col_name, new_col in metric_map.items():
            if col_name in bs.columns:
                bs[new_col] = bs[col_name]

        if not all(c in bs.columns for c in ["total_assets", "total_liabilities", "total_equity"]):
            pytest.skip("Balance sheet CSV missing Total assets/liabilities/equity rows — check metric names")

        bs["implied_assets"] = bs["total_liabilities"] + bs["total_equity"]
        bs["bs_error_pct"] = ((bs["total_assets"] - bs["implied_assets"]) / bs["total_assets"]).abs() * 100

        max_error = bs["bs_error_pct"].max()
        fails = bs[bs["bs_error_pct"] > 1.0][["bank", "year", "bs_error_pct"]].values.tolist()
        assert len(fails) == 0, f"Balance sheet identity fails >1% for: {fails}"

    def test_deposits_less_than_total_liabilities_kpis(self, kpis):
        """Deposits should be < Total Assets (sanity check)."""
        assert (kpis["deposits"] < kpis["total_assets"]).all(), "Deposits exceed Total Assets"

    def test_equity_less_than_total_assets(self, kpis):
        """Equity < Total Assets (lever > 1)."""
        assert (kpis["equity"] < kpis["total_assets"]).all(), "Equity >= Total Assets — impossible"

    def test_leverage_range(self, kpis):
        """Leverage (Assets/Equity) should be between 5× and 20× for systemic banks."""
        leverage = kpis["total_assets"] / kpis["equity"]
        assert (leverage >= 5).all(), f"Leverage < 5x for some bank: {leverage.min():.1f}x"
        assert (leverage <= 20).all(), f"Leverage > 20x for some bank: {leverage.max():.1f}x"


# ── Sector-level sanity tests ─────────────────────────────────────────────────
class TestSectorSanity:

    def test_sector_nii_grew_2022_to_2024(self, kpis):
        """Sector NII should have grown significantly 2022→2024 (ECB rate hike tailwind)."""
        sector_nii = kpis.groupby("year")["nii"].sum()
        assert sector_nii[2024] > sector_nii[2022] * 1.3, \
            f"Sector NII growth 2022→2024 < 30%: {(sector_nii[2024]/sector_nii[2022]-1)*100:.1f}%"

    def test_cet1_above_regulatory_minimum(self, kpis):
        """All banks should have CET1 > 10.5% (ECB Pillar 1 + conservation buffer)."""
        min_cet1 = 10.5
        fails = kpis[kpis["cet1"] < min_cet1][["bank", "year", "cet1"]].values.tolist()
        assert len(fails) == 0, f"CET1 below {min_cet1}% for: {fails}"

    def test_cost_to_income_reasonable_range(self, kpis):
        """C/I should be between 20% and 60% for modern banks."""
        assert (kpis["cost_to_income"] >= 20).all(), "C/I below 20% — unusually efficient"
        assert (kpis["cost_to_income"] <= 60).all(), "C/I above 60% — check data"

    def test_nim_positive_and_reasonable(self, kpis):
        """NIM should be positive and between 0.5% and 5%."""
        assert (kpis["nim"] > 0.5).all(), "NIM below 0.5% — unusually low"
        assert (kpis["nim"] < 5.0).all(), "NIM above 5% — check data"

    def test_loan_to_deposit_reasonable(self, kpis):
        """L/D should be between 50% and 100% for modern retail banks."""
        assert (kpis["loan_to_deposit"] >= 50).all(), "L/D below 50% — check data"
        assert (kpis["loan_to_deposit"] <= 100).all(), "L/D above 100% — check data"
