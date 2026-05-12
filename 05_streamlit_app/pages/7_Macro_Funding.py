"""
7_Macro_Funding.py — ECB rate pass-through, deposit beta proxy, TLTRO repayment,
and deposit growth for the four Greek systemic banks.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

from utils.data import load_kpis, load_balance, BANKS, YEARS, COLORS, LAYOUT, ECB_HIST

st.set_page_config(page_title="Macro & Funding", page_icon="📡", layout="wide")

with st.sidebar:
    st.markdown("### 📡 Macro & Funding")
    st.caption(
        "How the 2022–2024 ECB rate cycle flowed through to Greek bank earnings. "
        "Key topics: NIM expansion, deposit beta, TLTRO repayment, and deposit growth."
    )

@st.cache_data
def get_data():
    return load_kpis(), load_balance()

kpis, balance = get_data()

# ── TLTRO reference data ───────────────────────────────────────────────────────
# Eurobank: confirmed from balance sheet (Due to central banks column).
# Alpha Bank, Piraeus Bank, NBG: estimated from individual bank earnings
# presentations and ECB TLTRO-III repayment disclosures (2023 annual reports).
# All figures approximate ±€500m for non-Eurobank banks.
TLTRO = {
    "Eurobank":     {2022: 8774, 2023: 3771, 2024: 0},
    "Alpha Bank":   {2022: 4000, 2023: 0,    2024: 0},
    "Piraeus Bank": {2022: 7000, 2023: 0,    2024: 0},
    "NBG":          {2022: 5000, 2023: 0,    2024: 0},
}

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Macro & Funding Context")
st.caption("ECB rate cycle pass-through, deposit beta proxy, TLTRO repayment — FY2022–2024")
st.divider()

# ── Section 1: ECB rate vs NIM ─────────────────────────────────────────────────
st.subheader("1. NIM Expansion vs ECB Rate Cycle")
st.markdown(
    "Greek banks entered the 2022 rate hike cycle with **variable-rate loan books** and "
    "**sticky retail deposits** — the combination that maximises asset-sensitive NIM expansion. "
    "The key question for 2025–2026 is how fast deposits reprice as competition intensifies "
    "and ECB begins cutting rates."
)

fig_nim = go.Figure()

# ECB rate bars (secondary axis workaround: scale to NIM range)
ecb_vals = [ECB_HIST[y] for y in YEARS]
fig_nim.add_trace(go.Bar(
    x=YEARS, y=ecb_vals,
    name="ECB DFR (%)",
    marker_color="rgba(71,85,105,0.5)",
    hovertemplate="ECB DFR: %{y:.2f}%<extra></extra>",
    yaxis="y2",
))

for bank in BANKS:
    bdata = kpis[kpis.bank == bank].sort_values("year")
    fig_nim.add_trace(go.Scatter(
        x=bdata["year"], y=bdata["nim"],
        mode="lines+markers",
        name=bank,
        line=dict(color=COLORS[bank], width=2.5),
        marker=dict(size=9),
        hovertemplate=f"<b>{bank}</b><br>NIM: %{{y:.2f}}%<extra></extra>",
    ))

fig_nim.update_layout(
    **{k: v for k, v in LAYOUT.items() if k not in ("xaxis", "yaxis")},
    title="Net Interest Margin (%) vs ECB Deposit Facility Rate",
    height=400,
    xaxis=dict(tickvals=YEARS, gridcolor="#1e293b", tickfont=dict(color="#94a3b8")),
    yaxis=dict(title="NIM (%)", ticksuffix="%", gridcolor="#1e293b",
               tickfont=dict(color="#94a3b8"), range=[0, 4.5]),
    yaxis2=dict(title="ECB DFR (%)", ticksuffix="%", overlaying="y", side="right",
                tickfont=dict(color="#64748b"), range=[0, 4.5],
                showgrid=False),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8")),
    barmode="overlay",
)
st.plotly_chart(fig_nim, use_container_width=True)

st.divider()

# ── Section 2: Deposit beta proxy ─────────────────────────────────────────────
st.subheader("2. Deposit Beta Proxy — NIM Sensitivity to ECB Rate")
st.markdown(
    "**Deposit beta** measures what fraction of a central bank rate change is passed through "
    "to deposit customers. A **low deposit beta** means the bank captures more of each rate "
    "hike as NIM. Greek banks had unusually low deposit betas vs EU peers throughout 2022–2023, "
    "reflecting weak deposit competition in a recovering economy.\n\n"
    "Proxy: `NIM Δ (bps) / ECB Δ (bps)` — higher = bank captured more of the rate hike "
    "(lower pass-through to depositors)."
)

# Compute NIM sensitivity
ecb_delta_22_23 = (ECB_HIST[2023] - ECB_HIST[2022]) * 100  # bps
ecb_delta_23_24 = (ECB_HIST[2024] - ECB_HIST[2023]) * 100

beta_rows = []
for bank in BANKS:
    bdata = kpis[kpis.bank == bank].sort_values("year").set_index("year")
    nim_delta_22_23 = (bdata.loc[2023, "nim"] - bdata.loc[2022, "nim"]) * 100
    nim_delta_23_24 = (bdata.loc[2024, "nim"] - bdata.loc[2023, "nim"]) * 100
    sensitivity_22_23 = nim_delta_22_23 / ecb_delta_22_23 * 100
    sensitivity_23_24 = nim_delta_23_24 / ecb_delta_23_24 * 100 if ecb_delta_23_24 != 0 else None

    beta_rows.append({
        "Bank":               bank,
        "ECB Δ 22→23 (bps)":  f"+{ecb_delta_22_23:.0f}bp",
        "NIM Δ 22→23 (bps)":  f"{nim_delta_22_23:+.0f}bp",
        "NIM/ECB Sensitivity": f"{sensitivity_22_23:.1f}%",
        "ECB Δ 23→24 (bps)":  f"{ecb_delta_23_24:+.0f}bp",
        "NIM Δ 23→24 (bps)":  f"{nim_delta_23_24:+.0f}bp",
        "Implied (23→24)":     f"{sensitivity_23_24:.1f}%" if sensitivity_23_24 else "N/A",
        "_sens_22_23":         sensitivity_22_23,
    })

beta_df = pd.DataFrame(beta_rows)

# Bar chart: NIM/ECB sensitivity 22→23 per bank
fig_beta = go.Figure(go.Bar(
    x=[r["Bank"] for r in beta_rows],
    y=[r["_sens_22_23"] for r in beta_rows],
    marker_color=[COLORS[b] for b in BANKS],
    text=[f"{r['_sens_22_23']:.1f}%" for r in beta_rows],
    textposition="outside",
    hovertemplate="%{x}<br>NIM/ECB sensitivity: %{y:.1f}%<extra></extra>",
))
fig_beta.add_hline(y=0, line_color="#475569")
fig_beta.update_layout(
    **LAYOUT,
    title=f"NIM Sensitivity to ECB Rate Hike 2022→2023  (NIM Δbp / ECB Δ{ecb_delta_22_23:.0f}bp × 100%)",
    height=320,
    showlegend=False,
)
fig_beta.update_yaxes(ticksuffix="%")
st.plotly_chart(fig_beta, use_container_width=True)

# Table
display_beta = beta_df[["Bank", "ECB Δ 22→23 (bps)", "NIM Δ 22→23 (bps)",
                         "NIM/ECB Sensitivity", "ECB Δ 23→24 (bps)",
                         "NIM Δ 23→24 (bps)", "Implied (23→24)"]].set_index("Bank")
st.dataframe(display_beta, use_container_width=True, height=215)
st.caption(
    "NIM/ECB Sensitivity = NIM change (bps) / ECB rate change (bps) × 100%.  "
    "Higher = bank captured more of the rate hike = lower effective deposit beta.  "
    "NBG's superior deposit franchise gave it the highest sensitivity (strongest NIM expansion).  "
    "Note: NIM here uses year-end total assets — not average earning assets — so figures are proxies."
)

st.divider()

# ── Section 3: TLTRO repayment ─────────────────────────────────────────────────
st.subheader("3. TLTRO-III Repayment — Cheap ECB Funding Exit")
st.markdown(
    "All four Greek banks borrowed heavily under the ECB's **TLTRO-III** programme "
    "(Targeted Longer-Term Refinancing Operations) at rates as low as −1% during 2020–2021. "
    "As TLTRO rates moved above market in 2022–2023, banks rushed to repay, "
    "replacing cheap ECB funding with customer deposits and wholesale instruments. "
    "This repayment is a key driver of **funding cost normalisation** and puts upward pressure "
    "on **deposit rates** as banks compete to replace lost cheap funding."
)

fig_tltro = go.Figure()
for bank in BANKS:
    t_vals = [TLTRO[bank][y] for y in YEARS]
    fig_tltro.add_trace(go.Bar(
        x=[f"{bank}<br>{y}" for y in YEARS],
        y=t_vals,
        name=bank,
        marker_color=COLORS[bank],
        text=[f"€{v/1000:.1f}bn" if v > 0 else "—" for v in t_vals],
        textposition="outside",
        hovertemplate=f"<b>{bank}</b><br>Year: %{{x}}<br>TLTRO: €%{{y:,.0f}}m<extra></extra>",
    ))

fig_tltro.add_hline(y=0, line_color="#475569")
fig_tltro.update_layout(
    **LAYOUT,
    barmode="group",
    title="TLTRO-III Outstanding Balance (€m) — All Banks Fully Repaid by 2024",
    height=380,
    showlegend=True,
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8")),
)
fig_tltro.update_yaxes(tickprefix="€", ticksuffix="m")
st.plotly_chart(fig_tltro, use_container_width=True)

# Sector total table
tltro_rows = []
for bank in BANKS:
    t22, t23, t24 = TLTRO[bank][2022], TLTRO[bank][2023], TLTRO[bank][2024]
    confirmed = "✓ (balance sheet)" if bank == "Eurobank" else "~ est."
    tltro_rows.append({
        "Bank":          bank,
        "2022 (€m)":     f"€{t22:,}m",
        "2023 (€m)":     f"€{t23:,}m" if t23 > 0 else "€0 (repaid)",
        "2024 (€m)":     "€0 (repaid)",
        "Repaid by":     "2023" if bank != "Eurobank" else "2024",
        "Data Source":   confirmed,
    })

tltro_df = pd.DataFrame(tltro_rows).set_index("Bank")
st.dataframe(tltro_df, use_container_width=True, height=215)
st.caption(
    "Eurobank figures confirmed from audited balance sheet (Due to central banks line item). "
    "Alpha Bank, Piraeus Bank, and NBG figures estimated from individual bank 2023 annual "
    "report disclosures and ECB TLTRO repayment schedule. Accuracy ±€500m."
)

st.divider()

# ── Section 4: Deposit growth ─────────────────────────────────────────────────
st.subheader("4. Customer Deposit Growth — Funding Stability")
st.markdown(
    "Greek banks successfully grew their deposit base while repaying TLTRO, "
    "demonstrating strong retail franchise strength. "
    "Eurobank's 2024 deposit jump (+€21bn) reflects consolidation of Hellenic Bank Cyprus."
)

fig_dep = make_subplots(rows=1, cols=2,
                        subplot_titles=("Customer Deposits (€bn)", "YoY Deposit Growth (%)"))

for bank in BANKS:
    bdata = kpis[kpis.bank == bank].sort_values("year")
    deposits_bn = bdata["deposits"] / 1000

    fig_dep.add_trace(go.Bar(
        x=bdata["year"], y=deposits_bn,
        name=bank,
        marker_color=COLORS[bank],
        showlegend=True,
        hovertemplate=f"<b>{bank}</b><br>Deposits: €%{{y:.1f}}bn<extra></extra>",
    ), row=1, col=1)

    yoy_growth = bdata["deposits"].pct_change() * 100
    fig_dep.add_trace(go.Scatter(
        x=bdata["year"].values[1:],
        y=yoy_growth.values[1:],
        mode="lines+markers",
        name=bank,
        showlegend=False,
        line=dict(color=COLORS[bank], width=2),
        marker=dict(size=8),
        hovertemplate=f"<b>{bank}</b><br>Deposit growth: %{{y:+.1f}}%<extra></extra>",
    ), row=1, col=2)

fig_dep.add_hline(y=0, line_color="#475569", row=1, col=2)

# Annotate Eurobank 2024 spike — Hellenic Bank consolidation
euro_dep_2024 = kpis[(kpis.bank == "Eurobank") & (kpis.year == 2024)]["deposits"].values[0] / 1000
fig_dep.add_annotation(
    x=2024, y=euro_dep_2024,
    text="Hellenic Bank<br>consolidated",
    showarrow=True, arrowhead=2, arrowcolor="#94a3b8",
    ax=40, ay=-40,
    font=dict(color="#94a3b8", size=10),
    row=1, col=1,
)

fig_dep.update_layout(
    **{k: v for k, v in LAYOUT.items() if k not in ("xaxis", "yaxis")},
    title="Customer Deposit Base and Growth",
    height=400,
    barmode="group",
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8")),
)
for col_idx in [1, 2]:
    fig_dep.update_xaxes(tickvals=YEARS, gridcolor="#1e293b",
                         tickfont=dict(color="#94a3b8"), row=1, col=col_idx)
    fig_dep.update_yaxes(gridcolor="#1e293b", tickfont=dict(color="#94a3b8"), row=1, col=col_idx)
fig_dep.update_yaxes(tickprefix="€", ticksuffix="bn", row=1, col=1)
fig_dep.update_yaxes(ticksuffix="%", row=1, col=2)
st.plotly_chart(fig_dep, use_container_width=True)
st.caption(
    "Eurobank 2024 deposit surge (+36% YoY) driven by consolidation of Hellenic Bank Cyprus "
    "(~€20bn in Cypriot and Greek deposits). Organic growth across all peers: +5–8% pa, "
    "consistent with Greek household savings recovery."
)

st.divider()

# ── Analyst takeaway ───────────────────────────────────────────────────────────
st.subheader("Key Takeaways for the 2025–2026 Outlook")
st.markdown("""
| Factor | 2022–2024 Driver | 2025–2026 Outlook |
|--------|-----------------|-------------------|
| **NIM** | ECB hikes + low deposit beta = structural expansion | Gradual compression as ECB cuts and deposit competition intensifies |
| **Deposit beta** | Near-zero in Greece vs 0.4–0.6 EU average; exceptional NIM capture | Rising as banks compete post-TLTRO; Greek deposit beta converging toward EU peers |
| **TLTRO** | Cheap ECB funding fully repaid 2023–2024; temporary NIM headwind | No residual TLTRO drag; funding mix now 100% market/deposit-based |
| **Deposit growth** | Steady organic +5–8% pa; franchise strength intact | Moderate growth expected; risk of rate-sensitive outflows in rate-cut cycle |
| **NII outlook** | +50–70% sector-wide 2022→2024 | Base scenario: −3–5% by 2026 (rate cuts offset by volume recovery) |

**The bottom line:** Greek banks entered the rate-cut cycle from a position of strength —
NIM above 2%, deposits fully replacing TLTRO, and capital buffers well above SREP minimums.
The key risk is how fast domestic deposit competition forces liability repricing.
NBG's superior deposit franchise (lowest deposit beta, highest NIM sensitivity) provides
the most natural hedge in the downward rate environment.
""")

st.divider()
st.caption(
    "Greek Banking Sector Analysis 2022–2024 | "
    "Analyst: Spyros Papastergiou | spyrossyo96@gmail.com  \n"
    "NIM from kpis_final.csv; ECB rates hardcoded (approximate annual averages). "
    "TLTRO: Eurobank confirmed from balance sheet; others estimated from annual report disclosures."
)
