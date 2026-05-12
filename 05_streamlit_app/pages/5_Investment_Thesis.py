"""
5_Investment_Thesis.py — Per-bank investment rating, justified P/B, and thesis/risk summary.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

from utils.data import load_kpis, BANKS, COLORS, LAYOUT, GOODWILL_DATA, INTANGIBLES_DATA

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
        "**P/Book** uses ROE (year-end equity). "
        "**P/TBV** uses RoTE (tangible equity = equity minus goodwill and intangibles). "
        "P/TBV is the industry standard for European banks — strips out acquisition intangibles."
    )


@st.cache_data
def get_kpis():
    return load_kpis()


kpis = get_kpis()
k24  = kpis[kpis.year == 2024].set_index("bank")

# Approximate end-2024 market multiples. P/TBV > P/B where intangibles are small.
MARKET_PB_DEFAULTS = {
    "Eurobank":     1.10,
    "Alpha Bank":   0.88,
    "Piraeus Bank": 0.87,
    "NBG":          0.98,
}
MARKET_PTBV_DEFAULTS = {
    "Eurobank":     1.17,   # slightly above P/B given intangibles deduction
    "Alpha Bank":   0.96,
    "Piraeus Bank": 1.02,   # goodwill jump (Attica Holdings) inflates divergence
    "NBG":          1.07,
}

# ── Thesis and risk bullets per bank ──────────────────────────────────────────
THESIS = {
    "Eurobank": {
        "thesis": [
            "Highest RoTE in peer group (FY2024) with sector-leading NIM; Hellenic Bank consolidation adds Cypriot franchise and €27bn asset base",
            "NPE ratio below 3% — among the cleanest balance sheets in the sector; continued NPE securitisation expected",
            "Strong capital generation (CET1 well above SREP floor) supports dividend restoration and potential buybacks",
        ],
        "risks": [
            "Total intangibles €511m (goodwill €42m + other €469m from Hellenic Bank PPA) creates ~6pp gap between ROE and RoTE — institutional investors use P/TBV as primary valuation metric",
            "ECB rate cuts compress NIM faster than peers given larger corporate/floating-rate book (Pillar 3 IRRBB: −€58m per 25bp)",
            "Cypriot and Bulgarian exposure adds macro correlation risk to two additional sovereigns beyond Greece",
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

# ── Justified P/B + P/TBV summary table ───────────────────────────────────────
st.subheader("Justified P/B & P/TBV vs Market — FY2024")

col_mkt, col_note = st.columns([2, 1])
with col_note:
    st.info(
        "**P/Book** based on ROE (total equity).  \n"
        "**P/TBV** based on RoTE (tangible equity = equity − goodwill − intangibles).  \n"
        "P/TBV is the primary institutional benchmark for European banks.  \n"
        "Defaults ≈ end-2024 indicative market prices."
    )

with col_mkt:
    market_pb   = {}
    market_ptbv = {}
    pb_cols = st.columns(4)
    for i, bank in enumerate(BANKS):
        market_pb[bank]   = pb_cols[i].number_input(
            f"{bank} Market P/B",
            min_value=0.1, max_value=5.0,
            value=MARKET_PB_DEFAULTS[bank], step=0.05, key=f"mpb_{bank}",
        )
        market_ptbv[bank] = pb_cols[i].number_input(
            f"{bank} Market P/TBV",
            min_value=0.1, max_value=5.0,
            value=MARKET_PTBV_DEFAULTS[bank], step=0.05, key=f"mptbv_{bank}",
        )

st.divider()

# ── Compute ratings ────────────────────────────────────────────────────────────
summary_rows = []
for bank in BANKS:
    roe_val   = k24.loc[bank, "roe"]
    rote_val  = k24.loc[bank, "rote"]   if "rote"       in k24.columns else np.nan
    roe_avg   = k24.loc[bank, "roe_avg_eq"] if "roe_avg_eq" in k24.columns else np.nan
    tang_eq   = k24.loc[bank, "tangible_equity"] if "tangible_equity" in k24.columns else np.nan

    justified_pb   = (roe_val  - g) / (coe - g) if (coe > g and not np.isnan(roe_val))  else np.nan
    justified_ptbv = (rote_val - g) / (coe - g) if (coe > g and not np.isnan(rote_val)) else np.nan

    mpb   = market_pb[bank]
    mptbv = market_ptbv[bank]

    upside_pb   = (justified_pb   - mpb)   / mpb   * 100 if not np.isnan(justified_pb)   else np.nan
    upside_ptbv = (justified_ptbv - mptbv) / mptbv * 100 if not np.isnan(justified_ptbv) else np.nan

    # Rating driven by P/TBV upside (industry-standard metric)
    ref_upside = upside_ptbv if not np.isnan(upside_ptbv) else upside_pb
    if np.isnan(ref_upside):
        rating = "N/A"
    elif ref_upside >= 15:
        rating = "BUY"
    elif ref_upside >= -15:
        rating = "HOLD"
    else:
        rating = "SELL"

    gw   = GOODWILL_DATA.get(bank, {}).get(2024, 0)
    intg = INTANGIBLES_DATA.get(bank, {}).get(2024, 0)

    summary_rows.append({
        "Bank":              bank,
        "ROE (YE)":          f"{roe_val:.1f}%",
        "RoTE":              f"{rote_val:.1f}%" if not np.isnan(rote_val) else "—",
        "Goodwill+Intang.":  f"€{gw+intg:,}m",
        "Just. P/B":         f"{justified_pb:.2f}×"   if not np.isnan(justified_pb)   else "—",
        "Mkt P/B":           f"{mpb:.2f}×",
        "Just. P/TBV":       f"{justified_ptbv:.2f}×" if not np.isnan(justified_ptbv) else "—",
        "Mkt P/TBV":         f"{mptbv:.2f}×",
        "P/TBV Upside":      f"{upside_ptbv:+.1f}%"  if not np.isnan(upside_ptbv)    else "—",
        "Rating":            rating,
        "_justified_pb":     justified_pb,
        "_justified_ptbv":   justified_ptbv,
        "_market_pb":        mpb,
        "_market_ptbv":      mptbv,
        "_upside_pb":        upside_pb,
        "_upside_ptbv":      upside_ptbv,
        "_rating":           rating,
        "_roe":              roe_val,
        "_rote":             rote_val,
    })

summary_df = pd.DataFrame(summary_rows)

def style_rating(row):
    rating = row["Rating"]
    base   = [""] * (len(row) - 1)
    if rating == "BUY":
        return base + ["background-color: #14532d; color: #86efac; font-weight: bold"]
    if rating == "HOLD":
        return base + ["background-color: #1e3a1e; color: #4ade80; font-weight: bold"]
    if rating == "SELL":
        return base + ["background-color: #450a0a; color: #fca5a5; font-weight: bold"]
    return base + [""]

display_cols = ["Bank", "ROE (YE)", "RoTE", "Goodwill+Intang.",
                "Just. P/B", "Mkt P/B", "Just. P/TBV", "Mkt P/TBV", "P/TBV Upside", "Rating"]
display_df = summary_df[display_cols].set_index("Bank")
st.dataframe(
    display_df.style.apply(style_rating, axis=1),
    use_container_width=True, height=215,
)
st.caption(
    f"Justified P/B = (ROE − g) / (CoE − g) | Justified P/TBV = (RoTE − g) / (CoE − g) | "
    f"CoE = {coe:.1f}% | g = {g:.1f}%. "
    "Rating driven by P/TBV upside (BUY > +15%, SELL < −15%). "
    "Goodwill + Intangibles from investing.com consolidated balance sheets (FY2024)."
)

st.divider()

# ── Chart: P/B and P/TBV — justified vs market ────────────────────────────────
st.subheader("Justified vs Market Multiples — P/Book and P/TBV")

fig_pb = make_subplots(rows=1, cols=2,
                       subplot_titles=("P/Book (based on ROE)", "P/TBV (based on RoTE)"))

for col_idx, (just_key, mkt_key, label) in enumerate(
    [("_justified_pb", "_market_pb", "P/B"), ("_justified_ptbv", "_market_ptbv", "P/TBV")],
    start=1,
):
    just_vals = [r[just_key] for r in summary_rows]
    mkt_vals  = [r[mkt_key]  for r in summary_rows]

    fig_pb.add_trace(go.Bar(
        name=f"Justified {label}",
        x=BANKS,
        y=just_vals,
        marker_color=[COLORS[b] for b in BANKS],
        text=[f"{v:.2f}×" if not np.isnan(v) else "—" for v in just_vals],
        textposition="outside",
        showlegend=(col_idx == 1),
        hovertemplate=f"%{{x}}<br>Justified {label}: %{{y:.2f}}×<extra></extra>",
    ), row=1, col=col_idx)

    fig_pb.add_trace(go.Scatter(
        name=f"Market {label}",
        x=BANKS, y=mkt_vals, mode="markers",
        marker=dict(symbol="diamond", size=14, color="#f59e0b",
                    line=dict(color="#fbbf24", width=2)),
        showlegend=(col_idx == 1),
        hovertemplate=f"%{{x}}<br>Market {label}: %{{y:.2f}}×<extra></extra>",
    ), row=1, col=col_idx)

    fig_pb.add_hline(y=1.0, line_dash="dot", line_color="#475569", row=1, col=col_idx)

fig_pb.update_layout(
    **{k: v for k, v in LAYOUT.items() if k not in ("xaxis", "yaxis")},
    title=f"Justified (bars) vs Market (diamonds) | CoE {coe:.1f}%, g {g:.1f}%",
    height=420,
    barmode="group",
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8")),
)
for col_idx in [1, 2]:
    fig_pb.update_yaxes(ticksuffix="×", row=1, col=col_idx,
                        gridcolor="#1e293b", tickfont=dict(color="#94a3b8"))
    fig_pb.update_xaxes(gridcolor="#1e293b", tickfont=dict(color="#94a3b8"),
                        row=1, col=col_idx)
st.plotly_chart(fig_pb, use_container_width=True)
st.caption(
    "P/Book: justified = (ROE − g)/(CoE − g); P/TBV: justified = (RoTE − g)/(CoE − g). "
    "P/TBV is higher than P/Book for all banks because intangibles are deducted from the denominator. "
    "Dotted line = 1.0× (book-value parity)."
)

st.divider()

# ── Per-bank thesis cards ──────────────────────────────────────────────────────
st.subheader("Thesis & Risk Summary — Per Bank")

for bank in BANKS:
    row   = next(r for r in summary_rows if r["Bank"] == bank)
    color = COLORS[bank]
    rating_label = row["_rating"]
    rating_color = {"BUY": "#86efac", "HOLD": "#4ade80", "SELL": "#fca5a5"}.get(rating_label, "#94a3b8")

    with st.expander(
        f"**{bank}** — {rating_label}  |  Justified P/TBV {row['Just. P/TBV']}  "
        f"vs Market {row['Mkt P/TBV']}  |  Upside {row['P/TBV Upside']}",
        expanded=True,
    ):
        tc, rc = st.columns(2)
        with tc:
            st.markdown(f"**Bull Case** (ROE {row['ROE (YE)']}  |  RoTE {row['RoTE']})")
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
