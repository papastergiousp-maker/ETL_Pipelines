"""
app.py — Overview page (entry point for the Streamlit multi-page app).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.data import (
    load_kpis, BANKS, YEARS, COLORS, LAYOUT, fmt_eur, pct
)

st.set_page_config(
    page_title="Greek Banking Sector Analysis",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏦 Greek Banking 2022–2024")
    st.caption("Eurobank · Alpha Bank · Piraeus Bank · NBG")
    st.divider()
    st.caption("Data sourced from audited annual reports.\n"
               "All figures in € millions unless stated.")
    st.divider()
    st.caption("**Analyst:** Spyros Papastergiou\n\n"
               "📧 spyrossyo96@gmail.com")


@st.cache_data
def get_kpis():
    return load_kpis()


kpis = get_kpis()
k24  = kpis[kpis.year == 2024].set_index("bank")

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("Greek Banking Sector Analysis 2022–2024")
st.markdown(
    "Four systemic Greek banks — Eurobank, Alpha Bank, Piraeus, NBG — "
    "analysed from official annual report PDFs. "
    "Sector NII grew **+55%** over 2022–2024 driven by ECB rate hikes."
)
st.divider()

# ── Sector headline cards ───────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
sector_assets  = k24["total_assets"].sum()
sector_nii     = k24["nii"].sum()
best_roe_bank  = k24["roe"].idxmax()
best_cet1_bank = k24["cet1"].idxmax()

c1.metric("Sector Total Assets", fmt_eur(sector_assets))
c2.metric("Sector NII (2024)", fmt_eur(sector_nii),
          delta="+55% vs 2022", delta_color="normal")
c3.metric(f"Highest ROE — {best_roe_bank}",
          pct(k24.loc[best_roe_bank, "roe"]))
c4.metric(f"Strongest Capital — {best_cet1_bank}",
          pct(k24.loc[best_cet1_bank, "cet1"]) + " CET1")

st.divider()

# ── FY2024 Peer Scorecard ───────────────────────────────────────────────────────
st.subheader("FY2024 Peer Scorecard")

scorecard_cols = ["roe", "roa", "nim", "cost_to_income", "cet1",
                  "loan_to_deposit", "npe_ratio", "net_profit"]
labels         = ["ROE (%)", "ROA (%)", "NIM (%)", "C/I (%)",
                  "CET1 (%)", "L/D (%)", "NPE (%)", "Net Profit (€m)"]
lower_better   = {"cost_to_income", "loan_to_deposit", "npe_ratio"}

rows = []
for bank in BANKS:
    row = {"Bank": bank}
    for col, lbl in zip(scorecard_cols, labels):
        val = k24.loc[bank, col] if col in k24.columns else None
        if val is None or (hasattr(val, "isna") and val.isna()):
            row[lbl] = "—"
        elif col == "net_profit":
            row[lbl] = f"€{val:,.0f}m"
        else:
            row[lbl] = f"{val:.1f}%"
    rows.append(row)

import pandas as pd
scorecard_df = pd.DataFrame(rows).set_index("Bank")

# Highlight best-in-class per column
def highlight_best(df):
    styled = pd.DataFrame("", index=df.index, columns=df.columns)
    for col_lbl, col_key in zip(labels, scorecard_cols):
        if col_lbl not in df.columns:
            continue
        raw = k24[col_key] if col_key in k24.columns else None
        if raw is None:
            continue
        best_bank = raw.idxmin() if col_key in lower_better else raw.idxmax()
        styled.loc[best_bank, col_lbl] = "background-color: #14532d; color: #86efac; font-weight: bold"
    return styled

st.dataframe(
    scorecard_df.style.apply(highlight_best, axis=None),
    use_container_width=True,
    height=215,
)
st.caption("★ Green = best in class for that metric.")

st.divider()

# ── Trend charts ───────────────────────────────────────────────────────────────
st.subheader("Key Sector Trends")

col_l, col_r = st.columns(2)

# ── NII trend ──────────────────────────────────────────────────────────────────
with col_l:
    fig_nii = go.Figure()
    for bank in BANKS:
        bdf = kpis[kpis.bank == bank].sort_values("year")
        fig_nii.add_trace(go.Scatter(
            x=bdf["year"], y=bdf["nii"], name=bank,
            mode="lines+markers",
            line=dict(color=COLORS[bank], width=2.5),
            marker=dict(size=7),
            hovertemplate=f"<b>{bank}</b><br>NII: €%{{y:,.0f}}m<extra></extra>",
        ))
    fig_nii.update_layout(**LAYOUT, title="Net Interest Income (€m)",
                          xaxis=dict(**LAYOUT["xaxis"], tickvals=YEARS))
    st.plotly_chart(fig_nii, use_container_width=True)

# ── ROE trend ──────────────────────────────────────────────────────────────────
with col_r:
    fig_roe = go.Figure()
    for bank in BANKS:
        bdf = kpis[kpis.bank == bank].sort_values("year")
        fig_roe.add_trace(go.Scatter(
            x=bdf["year"], y=bdf["roe"], name=bank,
            mode="lines+markers",
            line=dict(color=COLORS[bank], width=2.5),
            marker=dict(size=7),
            hovertemplate=f"<b>{bank}</b><br>ROE: %{{y:.1f}}%<extra></extra>",
        ))
    fig_roe.add_hline(y=11, line_dash="dot", line_color="#475569",
                      annotation_text="CoE ~11%",
                      annotation_font_color="#94a3b8")
    fig_roe.update_layout(**LAYOUT, title="Return on Equity (%)",
                          yaxis=dict(**LAYOUT["yaxis"], ticksuffix="%"),
                          xaxis=dict(**LAYOUT["xaxis"], tickvals=YEARS))
    st.plotly_chart(fig_roe, use_container_width=True)

col_l2, col_r2 = st.columns(2)

# ── C/I trend ──────────────────────────────────────────────────────────────────
with col_l2:
    fig_ci = go.Figure()
    for bank in BANKS:
        bdf = kpis[kpis.bank == bank].sort_values("year")
        fig_ci.add_trace(go.Scatter(
            x=bdf["year"], y=bdf["cost_to_income"], name=bank,
            mode="lines+markers",
            line=dict(color=COLORS[bank], width=2.5),
            marker=dict(size=7),
            hovertemplate=f"<b>{bank}</b><br>C/I: %{{y:.1f}}%<extra></extra>",
        ))
    fig_ci.update_layout(**LAYOUT, title="Cost-to-Income Ratio (%)",
                         yaxis=dict(**LAYOUT["yaxis"], ticksuffix="%",
                                    autorange="reversed"),
                         xaxis=dict(**LAYOUT["xaxis"], tickvals=YEARS))
    st.plotly_chart(fig_ci, use_container_width=True)

# ── NPE trend ──────────────────────────────────────────────────────────────────
with col_r2:
    fig_npe = go.Figure()
    for bank in BANKS:
        bdf = kpis[kpis.bank == bank].sort_values("year")
        if "npe_ratio" not in bdf.columns:
            continue
        fig_npe.add_trace(go.Scatter(
            x=bdf["year"], y=bdf["npe_ratio"], name=bank,
            mode="lines+markers",
            line=dict(color=COLORS[bank], width=2.5, dash="dot"),
            marker=dict(size=7),
            hovertemplate=f"<b>{bank}</b><br>NPE: %{{y:.1f}}%<extra></extra>",
        ))
    fig_npe.update_layout(**LAYOUT, title="NPE Ratio (%) — lower is better",
                          yaxis=dict(**LAYOUT["yaxis"], ticksuffix="%",
                                     autorange="reversed"),
                          xaxis=dict(**LAYOUT["xaxis"], tickvals=YEARS))
    st.plotly_chart(fig_npe, use_container_width=True)

st.divider()

# ── Key insight callout ────────────────────────────────────────────────────────
st.subheader("Key Takeaways")
cols = st.columns(3)
cols[0].info(
    "**Rate cycle winner: NBG**\n\n"
    "NIM of 3.14% (highest in peer group) and 860bp of CET1 headroom above "
    "SREP floor position NBG as the most defensively positioned bank into the "
    "ECB rate-cutting cycle."
)
cols[1].success(
    "**Quality compounder: Eurobank**\n\n"
    "ROE of 16.9% — the only bank trading below its justified P/B (~1.5x) "
    "at an estimated market ~1.3x. Hellenic Bank consolidation adds Cypriot "
    "diversification. Best earnings quality in the sector."
)
cols[2].warning(
    "**Watch: Piraeus CoR risk**\n\n"
    "2024 profit (+35% YoY) included ~€165m after-tax impairment benefit "
    "from sales of NPE portfolios. Underlying earnings growth was ~+14%. "
    "CET1 of 13.7% leaves only 320bp above the SREP floor — tightest in sector."
)
