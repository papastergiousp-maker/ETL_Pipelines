"""
data.py — shared data loading, constants, and financial calculations.
All callers apply @st.cache_data around these functions.
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
DB   = ROOT / "02_Banking_Sector_Dashboard" / "data" / "greek_banking_final.db"

# ── Constants ─────────────────────────────────────────────────────────────────
BANKS = ["Eurobank", "Alpha Bank", "Piraeus Bank", "NBG"]
YEARS = [2022, 2023, 2024]

COLORS = {
    "Eurobank":     "#0067B1",
    "Alpha Bank":   "#E2231A",
    "Piraeus Bank": "#F7A600",
    "NBG":          "#003087",
}

# Historical ECB Deposit Facility Rate — period-end monthly average (%)
# Source: ECB key interest rates page; average of 12 month-end values.
# 2022: avg of [-0.5×6, 0×2, 0.75×2, 1.5, 2.0] = 0.17%
# 2023: avg of [2.0, 2.5, 3.0, 3.0, 3.25, 3.5, 3.75×2, 4.0×4] = 3.39%
# 2024: avg of [4.0×5, 3.75×3, 3.5, 3.25×2, 3.0] = 3.69%
ECB_HIST = {2022: 0.17, 2023: 3.39, 2024: 3.69}

# Forward ECB rate scenarios (end-year levels, %)
ECB_SCENARIOS = {
    "Dovish (rapid cuts)":  {2025: 1.75, 2026: 1.50},
    "Base (gradual cuts)":  {2025: 2.25, 2026: 2.00},
    "Hawkish (cuts pause)": {2025: 3.15, 2026: 3.15},
}

SREP_FLOOR = 10.5  # minimum CET1 requirement (%)

# ── Goodwill & Intangible Assets (€m) ────────────────────────────────────────
# Source: investing.com consolidated IFRS balance sheets, verified 2022–2024.
# Used to compute Return on Tangible Equity (RoTE = Net Profit / Tangible Equity).
# Note: Piraeus goodwill jump 2024 (€26m → €262m) reflects consolidation of
# Attica Holdings subsidiary in 2024; NBG goodwill zero (no major acquisitions).
GOODWILL_DATA = {
    "Eurobank":     {2022: 44,  2023: 42,  2024: 42},
    "Alpha Bank":   {2022: 0,   2023: 0,   2024: 83},
    "Piraeus Bank": {2022: 26,  2023: 26,  2024: 262},
    "NBG":          {2022: 0,   2023: 0,   2024: 0},
}
INTANGIBLES_DATA = {
    "Eurobank":     {2022: 290, 2023: 373, 2024: 469},
    "Alpha Bank":   {2022: 467, 2023: 438, 2024: 433},
    "Piraeus Bank": {2022: 321, 2023: 391, 2024: 556},
    "NBG":          {2022: 431, 2023: 524, 2024: 626},
}

# ── Deferred Tax Credits (DTC, €m) ───────────────────────────────────────────
# DTC = PSI-era DTAs eligible for conversion to Greek state tax credits under
# Law 4172/2013. Qualitatively inferior to organic CET1 (state-guaranteed).
# Eurobank 2024 & 2023: confirmed from Eurobank annual report (DTC = 50% / 36%
# of bank / group CET1). All other figures: estimated from Bloomberg sector
# total (€12.5bn mid-2024) and proportional DTA allocation (investing.com).
# Accuracy: ±€200–300m; use for directional analysis only.
DTC_DATA = {
    "Eurobank":     {2022: 3400, 2023: 3212, 2024: 3022},
    "Alpha Bank":   {2022: 3600, 2023: 3500, 2024: 3500},
    "Piraeus Bank": {2022: 3500, 2023: 3200, 2024: 2800},
    "NBG":          {2022: 3600, 2023: 3400, 2024: 3200},
}


# ── Loaders ───────────────────────────────────────────────────────────────────
def _connect():
    return sqlite3.connect(DB)


def load_kpis() -> pd.DataFrame:
    con = _connect()
    df  = pd.read_sql("SELECT * FROM kpis ORDER BY bank, year", con)
    con.close()

    # Average-equity ROE: (NP_t) / [(Equity_t + Equity_{t-1}) / 2]
    # Industry standard; year-end equity overstates ROE in capital-growth years.
    # 2022 is NaN because we lack 2021 equity — flagged "N/A" in the UI.
    df = df.sort_values(["bank", "year"]).copy()
    df["equity_lag"] = df.groupby("bank")["equity"].shift(1)
    df["avg_equity"] = (df["equity"] + df["equity_lag"]) / 2
    df["roe_avg_eq"] = (df["net_profit"] / df["avg_equity"] * 100).round(2)

    # RoTE = Net Profit / Tangible Equity (Equity − Goodwill − Other Intangibles)
    # Source for goodwill/intangibles: investing.com consolidated balance sheets.
    df["goodwill"]        = df.apply(lambda r: GOODWILL_DATA.get(r.bank, {}).get(r.year, 0) or 0, axis=1)
    df["intangibles"]     = df.apply(lambda r: INTANGIBLES_DATA.get(r.bank, {}).get(r.year, 0) or 0, axis=1)
    df["tangible_equity"] = (df["equity"] - df["goodwill"] - df["intangibles"]).clip(lower=1)
    df["rote"]            = (df["net_profit"] / df["tangible_equity"] * 100).round(2)

    # DTC = PSI-era deferred tax credits (€m). Eurobank 2023/2024 confirmed;
    # others estimated from Bloomberg sector total. See DTC_DATA comment above.
    df["dtc"] = df.apply(lambda r: DTC_DATA.get(r.bank, {}).get(r.year, None), axis=1)
    df["dtc_pct_equity"] = (df["dtc"] / df["equity"] * 100).round(1)

    return df


def load_income() -> pd.DataFrame:
    con  = _connect()
    raw  = pd.read_sql("SELECT * FROM income_statement", con)
    con.close()
    pivot = raw.pivot_table(index=["bank", "year"], columns="metric",
                            values="value").reset_index()
    pivot.columns.name = None
    return pivot


def load_balance() -> pd.DataFrame:
    con  = _connect()
    raw  = pd.read_sql("SELECT * FROM balance_sheet", con)
    con.close()
    pivot = raw.pivot_table(index=["bank", "year"], columns="metric",
                            values="value").reset_index()
    pivot.columns.name = None
    return pivot


# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_eur(val, decimals=0):
    """Format a value in €m with suffix."""
    if pd.isna(val):
        return "—"
    if abs(val) >= 1_000:
        return f"€{val/1_000:.1f}bn"
    return f"€{val:,.{decimals}f}m"


def pct(val, decimals=1):
    if pd.isna(val):
        return "—"
    return f"{val:.{decimals}f}%"


# ── Plotly dark layout (pass as **LAYOUT_DARK to go.Figure(layout=...)) ───────
LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", size=12),
    title_font=dict(color="#f1f5f9", size=14),
    xaxis=dict(gridcolor="#1e293b", zerolinecolor="#334155",
               tickfont=dict(color="#94a3b8")),
    yaxis=dict(gridcolor="#1e293b", zerolinecolor="#334155",
               tickfont=dict(color="#94a3b8")),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8")),
    margin=dict(l=50, r=20, t=40, b=50),
    hovermode="x unified",
)


# ── Stress-test engine ────────────────────────────────────────────────────────
def stress_bank(row: pd.Series,
                delta_cor_bps: int,
                loan_growth_pct: float,
                nim_comp_bps: int) -> dict:
    """
    Apply EBA-style stress to one bank (2024 actuals).

    Returns dict with stressed / delta values for net profit and CET1.
    """
    nii        = row["nii"]
    assets     = row["total_assets"]
    loans      = row["loans"]
    impairment = row["impairment"]          # negative in CSV
    opincome   = row["operating_income"]
    opex       = row["operating_expenses"]  # negative in CSV
    net_profit = row["net_profit"]
    cet1       = row["cet1"]
    nim        = row["nim"] / 100           # convert % → decimal

    # Matches 04_forecasting/02_stress_test.ipynb methodology exactly.
    # ── NII stress: NIM compression applied to shrinking asset base ──────
    nim_adv      = nim - nim_comp_bps / 10_000
    loans_adv    = loans * (1 + loan_growth_pct / 100)
    nii_adv      = nim_adv * assets * (1 + loan_growth_pct / 100)
    other_income = opincome - nii    # fees/trading fixed in stress
    opincome_adv = nii_adv + other_income

    # ── Additional impairment ───────────────────────────────────────────
    cor_base     = abs(impairment) / loans
    cor_adv      = cor_base + delta_cor_bps / 10_000
    impairment_adv = -(cor_adv * loans_adv)

    # ── Stressed PBT → net profit ───────────────────────────────────────
    ppop_base    = opincome + opex
    pbt_base     = ppop_base + impairment
    ppop_adv     = opincome_adv + opex
    pbt_adv      = ppop_adv + impairment_adv

    # Implied tax rate from actuals (clamped 15%–35%)
    tax_rate = max(0.15, min(0.35, 1 - net_profit / pbt_base)) if pbt_base != 0 else 0.24

    stressed_profit = pbt_adv * (1 - tax_rate)
    d_profit        = stressed_profit - net_profit

    # ── CET1 impact (RWA = loans × 0.50, consistent with stress notebook) ─
    rwa           = loans * 0.50
    stressed_cet1 = cet1 + d_profit / rwa * 100

    return {
        "baseline_profit":  net_profit,
        "stressed_profit":  round(stressed_profit, 0),
        "d_profit":         round(d_profit, 0),
        "baseline_cet1":    cet1,
        "stressed_cet1":    round(stressed_cet1, 1),
        "d_cet1":           round(stressed_cet1 - cet1, 1),
        "breaches_srep":    stressed_cet1 < SREP_FLOOR,
    }


# ── NII forecast engine ───────────────────────────────────────────────────────
# Sector-level fallback (used only if a bank-specific sensitivity is missing)
NII_SENSITIVITY_PER_25BP = -195  # €m per 25bp cut across sector

# Bank-specific NII sensitivity to a 25bp parallel shock (negative = NII falls when rates fall).
# Source: each bank's most recent Pillar 3 IRRBB / NII sensitivity disclosure (FY2024).
# These approximate the per-bank share of asset sensitivity vs. liability beta.
# Calibrated so that the sum is consistent with the sector midpoint (-€195m / 25bp).
NII_SENSITIVITY_BY_BANK = {
    "Eurobank":      -58,   # asset-sensitive; large corporate book
    "Alpha Bank":    -42,   # asset-sensitive; lower deposit beta
    "Piraeus Bank":  -52,   # asset-sensitive; high retail funding base
    "NBG":           -43,   # most balanced — strongest deposit franchise dampens transmission
}

# Annual loan growth differs by ECB scenario (rates → credit demand transmission).
VOL_GROWTH_BY_SCENARIO = {
    "Dovish (rapid cuts)":  0.035,  # +3.5% pa — cheaper credit unlocks demand
    "Base (gradual cuts)":  0.020,  # +2.0% pa — baseline
    "Hawkish (cuts pause)": 0.005,  # +0.5% pa — credit demand stays subdued
}


def forecast_nii(kpis_df: pd.DataFrame, scenario_name: str) -> pd.DataFrame:
    """
    Project NII for 2025–2026 per bank under a named ECB rate scenario.

    Methodology:
      • Rate effect uses bank-specific Pillar 3 sensitivities (€m / 25bp).
      • Volume effect compounds on the previous year's stressed NII
        (not 2024 base) and varies by scenario (3.5% / 2.0% / 0.5%).
    """
    k24            = kpis_df[kpis_df.year == 2024].set_index("bank")
    scenario_rates = ECB_SCENARIOS[scenario_name]
    vol_growth     = VOL_GROWTH_BY_SCENARIO[scenario_name]

    result = []
    for bank in BANKS:
        bank_sensitivity = NII_SENSITIVITY_BY_BANK.get(bank,
            NII_SENSITIVITY_PER_25BP * (k24.loc[bank, "nii"] / k24["nii"].sum()))
        nii_prev = k24.loc[bank, "nii"]

        for year in [2025, 2026]:
            prev_rate   = ECB_HIST[2024] if year == 2025 else scenario_rates[2025]
            curr_rate   = scenario_rates[year]
            delta_bp    = (curr_rate - prev_rate) * 100  # bps change
            rate_effect = (delta_bp / 25) * bank_sensitivity

            # Volume effect compounds on previous (stressed) NII.
            vol_effect  = nii_prev * vol_growth

            nii_curr = nii_prev + rate_effect + vol_effect
            result.append({
                "bank":        bank,
                "year":        year,
                "nii":         round(nii_curr, 0),
                "rate_effect": round(rate_effect, 0),
                "vol_effect":  round(vol_effect, 0),
            })
            nii_prev = nii_curr

    return pd.DataFrame(result)
