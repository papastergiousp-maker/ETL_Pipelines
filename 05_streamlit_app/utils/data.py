"""
data.py — shared data loading, constants, and financial calculations.
All callers apply @st.cache_data around these functions.
"""

import sqlite3
import pandas as pd
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

# Historical ECB Deposit Facility Rate (approximate annual average, %)
ECB_HIST = {2022: 0.56, 2023: 3.39, 2024: 3.28}

# Forward ECB rate scenarios (end-year levels, %)
ECB_SCENARIOS = {
    "Dovish (rapid cuts)":  {2025: 1.75, 2026: 1.50},
    "Base (gradual cuts)":  {2025: 2.25, 2026: 2.00},
    "Hawkish (cuts pause)": {2025: 3.15, 2026: 3.15},
}

SREP_FLOOR = 10.5  # minimum CET1 requirement (%)


# ── Loaders ───────────────────────────────────────────────────────────────────
def _connect():
    return sqlite3.connect(DB)


def load_kpis() -> pd.DataFrame:
    con = _connect()
    df  = pd.read_sql("SELECT * FROM kpis ORDER BY bank, year", con)
    con.close()
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
# Sensitivity: 25bp ECB cut → sector NII impact €-195m (midpoint of €170–220m range)
NII_SENSITIVITY_PER_25BP = -195  # €m per 25bp cut across sector

def forecast_nii(kpis_df: pd.DataFrame, scenario_name: str) -> pd.DataFrame:
    """
    Project NII for 2025–2026 per bank under a named ECB rate scenario.
    Rate sensitivity is allocated proportionally to each bank's share of sector NII.
    Volume growth assumed: +2% pa for all banks in all scenarios.
    """
    k24          = kpis_df[kpis_df.year == 2024].set_index("bank")
    sector_nii   = k24["nii"].sum()
    scenario_rates = ECB_SCENARIOS[scenario_name]

    rows = []
    for year in [2025, 2026]:
        prev_rate = ECB_HIST[2024] if year == 2025 else scenario_rates[2025]
        curr_rate = scenario_rates[year]
        delta_bp  = (curr_rate - prev_rate) * 100  # bps change

        # Sector NII change due to rate: scaled by sensitivity
        sector_delta = (delta_bp / 25) * NII_SENSITIVITY_PER_25BP

        for bank in BANKS:
            prev_nii  = k24.loc[bank, "nii"] if year == 2025 else None
            bank_share = k24.loc[bank, "nii"] / sector_nii
            rate_effect = sector_delta * bank_share
            # Volume effect: +2% loan growth × bank's NIM
            vol_effect = (k24.loc[bank, "nii"] * 0.02) if year == 2025 else 0

            base_nii = k24.loc[bank, "nii"] if year == 2025 else None
            rows.append({
                "bank": bank, "year": year,
                "rate_effect": rate_effect,
                "vol_effect": vol_effect if year == 2025 else rate_effect * 0,
                "base_nii": base_nii,
            })

    # Build cumulative NII from 2024 actuals
    result = []
    for bank in BANKS:
        nii_prev = k24.loc[bank, "nii"]
        for year in [2025, 2026]:
            r = next(x for x in rows if x["bank"] == bank and x["year"] == year)
            nii_curr = nii_prev + r["rate_effect"] + (k24.loc[bank, "nii"] * 0.02)
            result.append({"bank": bank, "year": year,
                           "nii": round(nii_curr, 0),
                           "rate_effect": round(r["rate_effect"], 0)})
            nii_prev = nii_curr

    return pd.DataFrame(result)
