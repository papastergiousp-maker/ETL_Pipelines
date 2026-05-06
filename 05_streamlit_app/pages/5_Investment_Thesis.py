"""
5_Investment_Thesis.py — Per-bank investment rating, justified P/B, and thesis/risk summary.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from utils.data import load_kpis, BANKS, COLORS, LAYOUT

st.set_page_config(page_title="Investment Thesis", page_icon="💡", layout="wide")

with st.sidebar:
    st.markdown("### 💡 Investment Thesis")
    st.markdown("**Model assumptions**")
    coe = st.slider("Cost of Equity — CoE (%)", 8.5, 13.0, 10.3, 0.1,
                    help="Rf 3.5% + β×ERP 5.5% + CRP 1.3% (post-Greek IG upgrade)")
    g   = st.slider("Long-run growth — g (%)", 1.0, 3.5, 2.0, 0.5,
                    help="Nominal GDP growth proxy for terminal value")
    st.divider()
    st.caption(
        "Justified P/B = (ROE − g) / (CoE − g).  \n"
        "**Note:** ROE uses year-end equity. RoTE (tangible equity) would be higher "
        "for Eurobank post-Hellenic Bank consolidation due to goodwill."
    )


@st.cache_data
def get_kpis():
    return load_kpis()


kpis = get_kpis()
k24  = kpis[kpis.year == 2024].set_index("bank")

# ── Market P/B inputs (approximate end-2024 closing prices) ───────────────────
# User-editable defaults; sourced from approximate market data at end-2024.
MARKET_PB_DEFAULTS = {
    "Eurobank":     1.10,
    "Alpha Bank":   0.88,
    "Piraeus Bank": 0.87,
    "NBG":          0.98,
}

# ── Thesis and risk bullets per bank ──────────────────────────────────────────
THESIS = {
    "Eurobank": {
        "thesis": [
            "Highest ROE in peer group (FY2024) with sector-leading NIM; Hellenic Bank consolidation adds Cypriot franchise and deposit base",
            "NPE ratio below 3% — among the cleanest balance sheets since the crisis; continued NPE securitisation expected",
            "Strong capital generation (CET1 well above SREP floor) supports dividend restoration and potential buybacks",
        ],
        "risks": [
            "Goodwill from Hellenic Bank acquisition (~€1bn) depresses RoTE vs ROE — key metric for institutional investors",
            "ECB rate cuts compress NIM faster than peers given larger corporate/floating-rate book",
            "Cypriot exposure adds macro correlation risk to a second sovereign",
        ],
    },
    "Alpha Bank": {
        "thesis": [
            "Aggressive cost reduction driving C/I improvement; management guidance of sub-40% C/I is credible on the current trajectory",
            "Strongest deposit beta protection in the peer group — lower liability re-pricing slows NIM compression in a rate-cut cycle",
            "Galaxy NPE securitisation programme largely complete; asset quality overhang is materially reduced",
        ],
        "risks": [
            "ROE is the lowest in the peer group; gap to CoE remains the widest — must sustain cost reduction to close",
            "Legacy IT infrastructure remediation adds operational risk and ongoing investment spend",
            "Smaller loan book growth vs peers limits NII upside in a volume-recovery scenario",
        ],
    },
    "Piraeus Bank": {
        "thesis": [
            "Fastest NPE reduction trajectory in the sector; Sunrise programme delivered rapid balance sheet clean-up",
            "Recovery in retail lending (mortgages, SME) supports volume-driven NII growth independent of rate path",
            "Lowest market valuation in the peer group offers the most asymmetric upside if ROE converges toward CoE",
        ],
        "risks": [
            "CET1 the closest to SREP floor in the peer group (FY2024); limited capital buffer for stress scenarios",
            "Higher retail funding cost relative to Eurobank/NBG — deposit beta less favourable",
            "Remaining legacy NPE stock still above EU average; any macro deterioration slows clean-up pace",
        ],
    },
    "NBG": {
        "thesis": [
            "Most balanced liability structure — strongest deposit franchise dampens ECB rate sensitivity and protects NIM in downturns",
            "Largest CET1 buffer above SREP floor; can sustain higher dividend payout and has most stress resilience",
            "Government HFSF stake fully exited by 2024 — improved governance, free float, and ESG eligibility for index funds",
        ],
        "risks": [
            "NII sensitivity to ECB cuts is the highest on an absolute € basis among the four banks",
            "TLTRO repayment impact on funding cost has not been fully absorbed; NIM pressure into 2025",
            "Slower loan growth vs peers reduces volume-driven NII upside; risk of market share loss in corporate lending",
        ],
    },
}

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("Investment Thesis")
st.caption(
    "FY2024 actuals — Gordon Growth justified P/B model. "
    "Adjust CoE and g in the sidebar. "
    "**Not investment advice.** For research and portfolio context only."
)
st.divider()

# ── Justified P/B summary table ────────────────────────────────────────────────
st.subheader("Justified P/B vs Market — FY2024")

col_mkt, col_note = st.columns([2, 1])
with col_note:
    st.info(
        "Enter approximate market P/B for each bank below.  \n"
        "Defaults ≈ end-2024 closing prices.  \n"
        "**Upside** = (Justified P/B − Market P/B) / Market P/B."
    )

with col_mkt:
    market_pb = {}
    pb_cols = st.columns(4)
    for i, bank in enumerate(BANKS):
        market_pb[bank] = pb_cols[i].number_input(
            f"{bank} Market P/B",
            min_value=0.1, max_value=5.0,
            value=MARKET_PB_DEFAULTS[bank], step=0.05,
            key=f"mpb_{bank}",
        )

st.divider()

# ── Compute justified P/B and rating ──────────────────────────────────────────
summary_rows = []
for bank in BANKS:
    roe_val      = k24.loc[bank, "roe"]
    roe_avg_val  = k24.loc[bank, "roe_avg_eq"] if "roe_avg_eq" in k24.columns else np.nan
    justified_pb = (roe_val - g) / (coe - g) if (coe - g) > 0 else np.nan
    mpb          = market_pb[bank]
    upside_pct   = (justified_pb - mpb) / mpb * 100 if not np.isnan(justified_pb) else np.nan

    if np.isnan(upside_pct):
        rating = "N/A"
    elif upside_pct >= 15:
        rating = "BUY"
    elif upside_pct >= -15:
        rating = "HOLD"
    else:
        rating = "SELL"

    summary_rows.append({
        "Bank":           bank,
        "ROE 2024A (YE)": f"{roe_val:.1f}%",
        "ROE (avg eq.)":  f"{roe_avg_val:.1f}%" if not np.isnan(roe_avg_val) else "N/A (no 2021 data)",
        "Justified P/B":  f"{justified_pb:.2f}×" if not np.isnan(justified_pb) else "—",
        "Market P/B":     f"{mpb:.2f}×",
        "Upside/Downside":f"{upside_pct:+.1f}%" if not np.isnan(upside_pct) else "—",
        "Rating":         rating,
        "_justified_pb":  justified_pb,
        "_market_pb":     mpb,
        "_upside":        upside_pct,
        "_rating":        rating,
        "_roe":           roe_val,
    })

summary_df = pd.DataFrame(summary_rows)

def style_rating(row):
    rating = row["Rating"]
    if rating == "BUY":
        return [""] * (len(row) - 1) + ["background-color: #14532d; color: #86efac; font-weight: bold"]
    if rating == "HOLD":
        return [""] * (len(row) - 1) + ["background-color: #1e3a1e; color: #4ade80; font-weight: bold"]
    if rating == "SELL":
        return [""] * (len(row) - 1) + ["background-color: #450a0a; color: #fca5a5; font-weight: bold"]
    return [""] * len(row)

display_df = summary_df[["Bank", "ROE 2024A (YE)", "ROE (avg eq.)", "Justified P/B", "Market P/B", "Upside/Downside", "Rating"]].set_index("Bank")
st.dataframe(
    display_df.style.apply(style_rating, axis=1),
    use_container_width=True, height=215,
)
st.caption(
    f"Justified P/B = (ROE − g) / (CoE − g) | CoE = {coe:.1f}% | g = {g:.1f}%. "
    "Rating thresholds: BUY > +15% upside, SELL < −15%, HOLD otherwise. "
    "ROE (avg eq.) uses average of year-end equity t and t−1; N/A for 2022 (no 2021 data)."
)

st.divider()

# ── Waterfall: Justified P/B vs Market P/B chart ───────────────────────────────
st.subheader("Justified P/B vs Market P/B")

fig_pb = go.Figure()
justified_vals = [r["_justified_pb"] for r in summary_rows]
market_vals    = [r["_market_pb"]    for r in summary_rows]

fig_pb.add_trace(go.Bar(
    name="Justified P/B",
    x=BANKS,
    y=justified_vals,
    marker_color=[COLORS[b] for b in BANKS],
    text=[f"{v:.2f}×" for v in justified_vals],
    textposition="outside",
    hovertemplate="%{x}<br>Justified P/B: %{y:.2f}×<extra></extra>",
))
fig_pb.add_trace(go.Scatter(
    name="Market P/B",
    x=BANKS,
    y=market_vals,
    mode="markers",
    marker=dict(symbol="diamond", size=14, color="#f59e0b",
                line=dict(color="#fbbf24", width=2)),
    hovertemplate="%{x}<br>Market P/B: %{y:.2f}×<extra></extra>",
))
fig_pb.add_hline(y=1.0, line_dash="dot", line_color="#475569",
                 annotation_text="1.0× book", annotation_font_color="#64748b")
fig_pb.update_layout(
    **LAYOUT,
    title=f"Justified P/B (bars) vs Market P/B (diamonds) | CoE {coe:.1f}%, g {g:.1f}%",
    height=380,
    barmode="group",
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8")),
)
fig_pb.update_yaxes(ticksuffix="×")
st.plotly_chart(fig_pb, use_container_width=True)

st.divider()

# ── Per-bank thesis cards ──────────────────────────────────────────────────────
st.subheader("Thesis & Risk Summary — Per Bank")

for bank in BANKS:
    row   = next(r for r in summary_rows if r["Bank"] == bank)
    color = COLORS[bank]
    rating_label = row["_rating"]
    rating_color = {"BUY": "#86efac", "HOLD": "#4ade80", "SELL": "#fca5a5"}.get(rating_label, "#94a3b8")

    with st.expander(
        f"**{bank}** — {rating_label}  |  Justified P/B {row['Justified P/B']}  "
        f"vs Market {row['Market P/B']}  |  Upside {row['Upside/Downside']}",
        expanded=True,
    ):
        tc, rc = st.columns(2)
        with tc:
            st.markdown(f"**Bull Case** (ROE {row['ROE 2024A (YE)']})")
            for bullet in THESIS[bank]["thesis"]:
                st.markdown(f"✅ {bullet}")
        with rc:
            st.markdown("**Key Risks**")
            for bullet in THESIS[bank]["risks"]:
                st.markdown(f"⚠️ {bullet}")

st.divider()
st.caption(
    "Greek Banking Sector Analysis 2022–2024 | "
    "Analyst: Spyros Papastergiou | spyrossyo96@gmail.com  \n"
    "Justified P/B is a Gordon Growth model output — directional only. "
    "Real investment decisions require quarterly data, management guidance, and sell-side models."
)
