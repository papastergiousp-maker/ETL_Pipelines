"""
1_Bank_Deep_Dive.py — Per-bank selector with KPI trend charts and IS/BS tables.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from utils.data import (
    load_kpis, load_income, load_balance,
    BANKS, YEARS, COLORS, LAYOUT, fmt_eur, pct
)

st.set_page_config(page_title="Bank Deep-Dive", page_icon="🔍", layout="wide")

with st.sidebar:
    st.markdown("### 🔍 Bank Deep-Dive")
    bank = st.selectbox("Select bank", BANKS)
    st.divider()
    st.caption("Data sourced from audited annual reports.")


@st.cache_data
def get_data():
    return load_kpis(), load_income(), load_balance()


kpis, income, balance = get_data()
bkpis = kpis[kpis.bank == bank].sort_values("year").set_index("year")
k24   = bkpis.loc[2024]
k23   = bkpis.loc[2023]

color = COLORS[bank]

# ── Header ─────────────────────────────────────────────────────────────────────
st.title(f"{bank} — Financial Overview")
st.caption("FY2022–2024  |  Source: Audited Annual Reports")
st.divider()

# ── KPI delta cards ────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5, c6 = st.columns(6)

def delta_fmt(curr, prev, suffix="", invert=False):
    if pd.isna(prev) or prev == 0:
        return None, "off"
    d = curr - prev
    color_logic = "inverse" if invert else "normal"
    return f"{d:+.1f}{suffix}", color_logic

c1.metric("ROE 2024",    pct(k24["roe"]),
          *delta_fmt(k24["roe"], k23["roe"], "%"))
_roe_avg = k24.get("roe_avg_eq") if hasattr(k24, "get") else (k24["roe_avg_eq"] if "roe_avg_eq" in k24.index else None)
if _roe_avg and not pd.isna(_roe_avg):
    c1.caption(f"Avg-eq: {_roe_avg:.1f}%")
c2.metric("NIM 2024",    pct(k24["nim"]),
          *delta_fmt(k24["nim"], k23["nim"], "%"))
c3.metric("C/I 2024",    pct(k24["cost_to_income"]),
          *delta_fmt(k24["cost_to_income"], k23["cost_to_income"], "%", invert=True))
c4.metric("CET1 2024",   pct(k24["cet1"]),
          *delta_fmt(k24["cet1"], k23["cet1"], "%"))
c5.metric("Net Profit",  fmt_eur(k24["net_profit"]),
          *delta_fmt(k24["net_profit"], k23["net_profit"], "m"))
npe_val = k24.get("npe_ratio", None) if hasattr(k24, "get") else k24["npe_ratio"] if "npe_ratio" in k24.index else None
npe_prev = k23.get("npe_ratio", None) if hasattr(k23, "get") else k23["npe_ratio"] if "npe_ratio" in k23.index else None
c6.metric("NPE Ratio",   pct(npe_val) if npe_val else "—",
          *delta_fmt(npe_val, npe_prev, "%", invert=True) if (npe_val and npe_prev) else (None, "off"))

st.divider()

# ── Trend charts ───────────────────────────────────────────────────────────────
st.subheader("3-Year KPI Trends")

fig = make_subplots(rows=2, cols=2,
                    subplot_titles=("Net Interest Income (€m)",
                                    "Return on Equity (%)",
                                    "Cost-to-Income Ratio (%)",
                                    "NIM & CET1 (%)"),
                    vertical_spacing=0.14)

marker_style = dict(color=color, size=8)
line_style   = dict(color=color, width=2.5)

# NII
fig.add_trace(go.Scatter(x=YEARS, y=[bkpis.loc[y, "nii"] for y in YEARS],
                         mode="lines+markers", name="NII",
                         line=line_style, marker=marker_style,
                         hovertemplate="€%{y:,.0f}m<extra></extra>"),
              row=1, col=1)

# ROE (year-end equity — as reported)
fig.add_trace(go.Scatter(x=YEARS, y=[bkpis.loc[y, "roe"] for y in YEARS],
                         mode="lines+markers", name="ROE (YE equity)",
                         line=line_style, marker=marker_style,
                         hovertemplate="ROE (YE): %{y:.1f}%<extra></extra>"),
              row=1, col=2)
# ROE (average equity — industry standard, available 2023–2024 only)
_roe_avg_yrs = [y for y in YEARS if not pd.isna(bkpis.loc[y, "roe_avg_eq"])]
_roe_avg_vals = [bkpis.loc[y, "roe_avg_eq"] for y in _roe_avg_yrs]
if _roe_avg_yrs:
    fig.add_trace(go.Scatter(x=_roe_avg_yrs, y=_roe_avg_vals,
                             mode="lines+markers", name="RoE (avg equity)",
                             line=dict(color=color, width=1.5, dash="dot"),
                             marker=dict(color=color, size=6, symbol="circle-open"),
                             hovertemplate="ROE (avg eq): %{y:.1f}%<extra></extra>"),
                  row=1, col=2)
fig.add_hline(y=10.3, line_dash="dot", line_color="#475569", row=1, col=2,
              annotation_text="CoE 10.3%", annotation_font_color="#94a3b8")

# C/I
fig.add_trace(go.Scatter(x=YEARS, y=[bkpis.loc[y, "cost_to_income"] for y in YEARS],
                         mode="lines+markers", name="C/I",
                         line=line_style, marker=marker_style,
                         hovertemplate="%{y:.1f}%<extra></extra>"),
              row=2, col=1)

# NIM
fig.add_trace(go.Scatter(x=YEARS, y=[bkpis.loc[y, "nim"] for y in YEARS],
                         mode="lines+markers", name="NIM",
                         line=dict(color=color, width=2.5),
                         marker=dict(color=color, size=8),
                         hovertemplate="NIM: %{y:.2f}%<extra></extra>"),
              row=2, col=2)
# CET1
fig.add_trace(go.Scatter(x=YEARS, y=[bkpis.loc[y, "cet1"] for y in YEARS],
                         mode="lines+markers", name="CET1",
                         line=dict(color="#10b981", width=2, dash="dash"),
                         marker=dict(color="#10b981", size=8),
                         hovertemplate="CET1: %{y:.1f}%<extra></extra>"),
              row=2, col=2)

fig.update_layout(
    **LAYOUT,
    height=540,
    showlegend=False,
    title=f"{bank} — Key Performance Indicators",
)
# Suffix axes
for r, c, sfx in [(1,2,"%"), (2,1,"%"), (2,2,"%")]:
    fig.update_yaxes(ticksuffix=sfx, row=r, col=c,
                     gridcolor="#1e293b", tickfont=dict(color="#94a3b8"))
fig.update_xaxes(tickvals=YEARS, gridcolor="#1e293b",
                 tickfont=dict(color="#94a3b8"))
fig.update_yaxes(row=2, col=1, autorange="reversed")

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── Income Statement table ─────────────────────────────────────────────────────
st.subheader("Income Statement (€m)")
b_income = income[income.bank == bank].sort_values("year")

IS_COLS = {
    "Net interest income":                    "NII",
    "Net banking fee and commission income":  "Fee & Commission",
    "Operating income":                       "Operating Income",
    "Operating expenses":                     "Operating Expenses",
    "Profit from operations before impairments": "PPOP",
    "Impairment losses on loans":             "Impairment",
    "Profit before tax":                      "Profit Before Tax",
    "Net profit attributable to shareholders": "Net Profit",
}

is_rows = []
for col, label in IS_COLS.items():
    row = {"Line item": label}
    for y in YEARS:
        year_data = b_income[b_income.year == y]
        val = year_data[col].values[0] if (col in year_data.columns and len(year_data)) else None
        row[str(y)] = f"{val:,.0f}" if val is not None and not pd.isna(val) else "—"
    is_rows.append(row)

st.dataframe(pd.DataFrame(is_rows).set_index("Line item"),
             use_container_width=True, height=320)

# ── Balance Sheet table ────────────────────────────────────────────────────────
with st.expander("Balance Sheet (€m)", expanded=False):
    b_balance = balance[balance.bank == bank].sort_values("year")
    BS_COLS = {
        "Cash and balances with central banks": "Cash & CBs",
        "Due from credit institutions":         "Due from Banks",
        "Investment securities":                "Investment Securities",
        "Loans and advances to customers":      "Loans & Advances",
        "Total assets":                         "Total Assets",
        "Due to central banks":                 "Due to CBs",
        "Due to credit institutions":           "Due to Banks",
        "Deposits from customers":              "Customer Deposits",
        "Total liabilities":                    "Total Liabilities",
        "Total equity":                         "Total Equity",
    }
    bs_rows = []
    for col, label in BS_COLS.items():
        row = {"Line item": label}
        for y in YEARS:
            year_data = b_balance[b_balance.year == y]
            val = year_data[col].values[0] if (col in year_data.columns and len(year_data)) else None
            row[str(y)] = f"{val:,.0f}" if val is not None and not pd.isna(val) else "—"
        bs_rows.append(row)
    st.dataframe(pd.DataFrame(bs_rows).set_index("Line item"),
                 use_container_width=True)

# ── Waterfall: NII bridge 2022 → 2024 ─────────────────────────────────────────
with st.expander("NII Bridge 2022 → 2024", expanded=False):
    nii_22 = bkpis.loc[2022, "nii"]
    nii_23 = bkpis.loc[2023, "nii"]
    nii_24 = bkpis.loc[2024, "nii"]
    d23    = nii_23 - nii_22
    d24    = nii_24 - nii_23

    fig_wf = go.Figure(go.Waterfall(
        name="NII",
        orientation="v",
        measure=["absolute", "relative", "relative", "total"],
        x=["2022", "Δ 2023", "Δ 2024", "2024"],
        y=[nii_22, d23, d24, nii_24],
        text=[f"€{nii_22:,.0f}m", f"{d23:+,.0f}m", f"{d24:+,.0f}m", f"€{nii_24:,.0f}m"],
        textposition="outside",
        connector=dict(line=dict(color="#475569")),
        increasing=dict(marker=dict(color="#10b981")),
        decreasing=dict(marker=dict(color="#ef4444")),
        totals=dict(marker=dict(color=color)),
    ))
    fig_wf.update_layout(**LAYOUT, title=f"{bank} — NII Bridge (€m)",
                         showlegend=False, height=380)
    st.plotly_chart(fig_wf, use_container_width=True)
