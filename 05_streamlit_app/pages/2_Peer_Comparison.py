"""
2_Peer_Comparison.py — Radar chart + ranked bar charts across the 4-bank peer group.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

from utils.data import load_kpis, BANKS, YEARS, COLORS, LAYOUT

st.set_page_config(page_title="Peer Comparison", page_icon="📊", layout="wide")

with st.sidebar:
    st.markdown("### 📊 Peer Comparison")
    year = st.radio("Select year", YEARS, index=2)
    st.divider()
    st.caption("Normalised scores (min-max) and percentile ranks computed against the 4-bank peer group.")


@st.cache_data
def get_kpis():
    return load_kpis()


kpis = get_kpis()
ky   = kpis[kpis.year == year].set_index("bank")

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("Peer Comparison")
st.caption(f"FY{year} — normalised percentile ranking (min-max) across Eurobank, Alpha Bank, Piraeus Bank, NBG")
st.divider()

# ── Normalise for radar ────────────────────────────────────────────────────────
RADAR_METRICS = {
    "RoTE": ("rote",            True),    # tangible equity return — industry standard
    "ROE":  ("roe",             True),
    "ROA":  ("roa",             True),
    "NIM":  ("nim",             True),
    "CET1": ("cet1",            True),
    "C/I":  ("cost_to_income",  False),   # lower = better
    "NPE":  ("npe_ratio",       False),   # lower = better
}

def normalise(series: pd.Series, higher_better: bool) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(0.5, index=series.index)
    norm = (series - mn) / (mx - mn)
    return norm if higher_better else 1 - norm


radar_df = pd.DataFrame({
    label: normalise(ky[col], hb)
    for label, (col, hb) in RADAR_METRICS.items()
    if col in ky.columns
})

# ── Radar chart ────────────────────────────────────────────────────────────────
st.subheader(f"Spider Chart — FY{year} (normalised 0–1, 1 = best in peer group)")

theta = list(radar_df.columns) + [radar_df.columns[0]]   # close the polygon

fig_radar = go.Figure()
for bank in BANKS:
    r_vals = list(radar_df.loc[bank]) + [radar_df.loc[bank].iloc[0]]
    fig_radar.add_trace(go.Scatterpolar(
        r=r_vals, theta=theta, name=bank, fill="toself",
        line=dict(color=COLORS[bank], width=2),
        fillcolor=COLORS[bank].replace(")", ", 0.07)").replace("rgb", "rgba") if "rgb" in COLORS[bank] else COLORS[bank] + "12",
        opacity=0.85,
        hovertemplate=f"<b>{bank}</b><br>%{{theta}}: %{{r:.2f}}<extra></extra>",
    ))

fig_radar.update_layout(
    **{k: v for k, v in LAYOUT.items() if k not in ("xaxis", "yaxis")},
    polar=dict(
        bgcolor="rgba(0,0,0,0)",
        radialaxis=dict(visible=True, range=[0, 1],
                        tickfont=dict(color="#64748b"),
                        gridcolor="#1e293b"),
        angularaxis=dict(tickfont=dict(color="#94a3b8"),
                         gridcolor="#1e293b"),
    ),
    height=480,
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8")),
    margin=dict(l=60, r=60, t=40, b=40),
    title=f"FY{year} Multi-Metric Radar",
    title_font=dict(color="#f1f5f9"),
)
st.plotly_chart(fig_radar, use_container_width=True)

st.divider()

# ── Z-score / percentile rank table ───────────────────────────────────────────
st.subheader("Percentile Ranks (FY" + str(year) + ")")

ALL_METRICS = {
    "RoTE (%)":     ("rote",            True),
    "ROE (%)":      ("roe",             True),
    "ROA (%)":      ("roa",             True),
    "NIM (%)":      ("nim",             True),
    "CET1 (%)":     ("cet1",            True),
    "C/I (%)":      ("cost_to_income",  False),
    "L/D (%)":      ("loan_to_deposit", False),
    "NPE (%)":      ("npe_ratio",       False),
    "Net Profit":   ("net_profit",      True),
    "NII (€m)":     ("nii",             True),
    "Assets (€bn)": ("total_assets",    True),
}

rank_rows = []
for bank in BANKS:
    row = {"Bank": bank}
    for label, (col, hb) in ALL_METRICS.items():
        if col not in ky.columns:
            row[label] = "—"
            continue
        series = ky[col].dropna()
        pct_rank = int(normalise(series, hb).loc[bank] * 100)
        row[label] = f"{pct_rank}th"
    rank_rows.append(row)

rank_df = pd.DataFrame(rank_rows).set_index("Bank")

def style_pct(val):
    if val == "—":
        return ""
    n = int(val.replace("th", ""))
    if n >= 75:
        return "background-color: #14532d; color: #86efac"
    if n >= 50:
        return "background-color: #1e3a1e; color: #4ade80"
    if n >= 25:
        return "background-color: #422006; color: #fb923c"
    return "background-color: #450a0a; color: #fca5a5"

st.dataframe(rank_df.style.applymap(style_pct),
             use_container_width=True, height=220)
st.caption("Percentile = rank within 4-bank peer group. 100th = best, 0th = worst (direction-adjusted).")

st.divider()

# ── Ranked bar charts ──────────────────────────────────────────────────────────
st.subheader("Ranked Bar Charts — FY" + str(year))

BAR_METRICS = [
    ("rote",            "RoTE (%)",          True,  "%"),
    ("roe",             "ROE (%)",           True,  "%"),
    ("nim",             "NIM (%)",           True,  "%"),
    ("cost_to_income",  "Cost-to-Income (%)",False, "%"),
    ("cet1",            "CET1 (%)",          True,  "%"),
    ("npe_ratio",       "NPE Ratio (%)",     False, "%"),
    ("net_profit",      "Net Profit (€m)",   True,  ""),
]

# Filter to metrics present in data
BAR_METRICS = [(c, l, hb, sfx) for c, l, hb, sfx in BAR_METRICS if c in ky.columns]

cols_per_row = 3
rows_needed  = (len(BAR_METRICS) + cols_per_row - 1) // cols_per_row

for r in range(rows_needed):
    cols = st.columns(cols_per_row)
    for i in range(cols_per_row):
        idx = r * cols_per_row + i
        if idx >= len(BAR_METRICS):
            break
        col_key, label, higher_better, suffix = BAR_METRICS[idx]
        sorted_df = ky[[col_key]].copy().dropna()
        sorted_df = sorted_df.sort_values(col_key, ascending=not higher_better)

        bar_colors = [COLORS[b] for b in sorted_df.index]
        fig_bar = go.Figure(go.Bar(
            x=sorted_df.index,
            y=sorted_df[col_key],
            marker_color=bar_colors,
            text=[f"{v:.1f}{suffix}" for v in sorted_df[col_key]],
            textposition="outside",
            hovertemplate="%{x}<br>" + label + ": %{y:.2f}" + suffix + "<extra></extra>",
        ))
        arrow = "▼ lower = better" if not higher_better else "▲ higher = better"
        fig_bar.update_layout(
            **LAYOUT,
            title=f"{label}  ({arrow})",
            height=300,
            showlegend=False,
            margin=dict(l=30, r=10, t=50, b=40),
        )
        fig_bar.update_yaxes(
            ticksuffix=suffix,
            autorange="reversed" if not higher_better else True,
        )
        cols[i].plotly_chart(fig_bar, use_container_width=True)
