"""
3_Forecast_Stress.py — ECB rate scenario NII forecast + interactive EBA-style stress test.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from utils.data import (
    load_kpis, BANKS, YEARS, COLORS, LAYOUT,
    ECB_HIST, ECB_SCENARIOS, SREP_FLOOR,
    forecast_nii, stress_bank, fmt_eur, pct
)

st.set_page_config(page_title="Forecast & Stress", page_icon="📈", layout="wide")

with st.sidebar:
    st.markdown("### 📈 Forecast & Stress")
    st.caption("NII forecast driven by ECB rate scenarios (P1.2 macro overlay).\n\n"
               "Stress test follows EBA 2023 adverse scenario methodology.")


@st.cache_data
def get_kpis():
    return load_kpis()


kpis = get_kpis()
k24  = kpis[kpis.year == 2024].set_index("bank")

st.title("Forecast & Stress Testing")
st.divider()

tab1, tab2 = st.tabs(["📉 NII Forecast 2025–2026", "⚠️ EBA-Style Stress Test"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — NII FORECAST
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("NII Forecast 2025–2026 — ECB Rate Scenarios")
    st.markdown(
        "Forecast methodology: **bank-specific rate effect** (per-bank Pillar 3 IRRBB sensitivity "
        "to a 25bp parallel shock — Eurobank −€58m, Alpha −€42m, Piraeus −€52m, NBG −€43m) "
        "+ **scenario-dependent volume effect** (Dovish +3.5% / Base +2.0% / Hawkish +0.5% pa loan growth, "
        "compounding on previous-year NII)."
    )

    col_ctrl, col_ecb = st.columns([1, 2])

    with col_ctrl:
        scenario = st.radio(
            "ECB Rate Scenario",
            list(ECB_SCENARIOS.keys()),
            index=1,
        )
        st.markdown("**ECB Rate Assumptions (%)**")
        ecb_table = pd.DataFrame({
            "Year": [2022, 2023, 2024, 2025, 2026],
            "Rate": [
                ECB_HIST[2022],
                ECB_HIST[2023],
                ECB_HIST[2024],
                ECB_SCENARIOS[scenario][2025],
                ECB_SCENARIOS[scenario][2026],
            ]
        })
        st.dataframe(ecb_table.set_index("Year"), use_container_width=True, height=220)

    with col_ecb:
        # ECB rate path chart
        all_years = [2022, 2023, 2024, 2025, 2026]
        fig_ecb = go.Figure()
        for sc_name, sc_rates in ECB_SCENARIOS.items():
            rates = [ECB_HIST[2022], ECB_HIST[2023], ECB_HIST[2024],
                     sc_rates[2025], sc_rates[2026]]
            is_selected = sc_name == scenario
            fig_ecb.add_trace(go.Scatter(
                x=all_years, y=rates,
                mode="lines+markers",
                name=sc_name,
                line=dict(
                    width=3 if is_selected else 1.5,
                    dash="solid" if is_selected else "dash",
                    color={"Dovish (rapid cuts)":  "#60a5fa",
                           "Base (gradual cuts)":  "#10b981",
                           "Hawkish (cuts pause)": "#f59e0b"}[sc_name],
                ),
                marker=dict(size=8 if is_selected else 5),
                opacity=1.0 if is_selected else 0.45,
                hovertemplate=f"<b>{sc_name}</b><br>Year: %{{x}}<br>Rate: %{{y:.2f}}%<extra></extra>",
            ))
        fig_ecb.add_vline(x=2024.5, line_dash="dot", line_color="#475569",
                          annotation_text="forecast →", annotation_font_color="#64748b")
        fig_ecb.update_layout(**LAYOUT, title="ECB Deposit Facility Rate Path (%)",
                              height=280)
        fig_ecb.update_yaxes(ticksuffix="%")
        st.plotly_chart(fig_ecb, use_container_width=True)

    st.divider()

    # ── NII forecast chart ─────────────────────────────────────────────────────
    fc = forecast_nii(kpis, scenario)
    hist = kpis[["bank", "year", "nii"]].copy()
    hist["source"] = "actual"
    fc["source"]   = "forecast"
    combined = pd.concat([hist, fc], ignore_index=True)

    fig_nii = go.Figure()
    for bank in BANKS:
        bdata = combined[combined.bank == bank].sort_values("year")
        actual  = bdata[bdata.source == "actual"]
        fcast   = bdata[bdata.source == "forecast"]

        # Actual line
        fig_nii.add_trace(go.Scatter(
            x=actual["year"], y=actual["nii"], name=bank,
            mode="lines+markers",
            line=dict(color=COLORS[bank], width=2.5),
            marker=dict(size=7),
            hovertemplate=f"<b>{bank}</b> (actual)<br>NII: €%{{y:,.0f}}m<extra></extra>",
        ))
        # Forecast — dashed, connect from last actual
        bridge_x = [actual["year"].iloc[-1]] + list(fcast["year"])
        bridge_y = [actual["nii"].iloc[-1]]  + list(fcast["nii"])
        fig_nii.add_trace(go.Scatter(
            x=bridge_x, y=bridge_y, name=f"{bank} (forecast)",
            mode="lines+markers", showlegend=False,
            line=dict(color=COLORS[bank], width=2, dash="dash"),
            marker=dict(color=COLORS[bank], size=7, symbol="diamond"),
            hovertemplate=f"<b>{bank}</b> (forecast)<br>NII: €%{{y:,.0f}}m<extra></extra>",
        ))

    fig_nii.add_vline(x=2024.5, line_dash="dot", line_color="#475569")
    fig_nii.update_layout(
        **LAYOUT,
        title=f"NII Forecast 2025–2026 — {scenario}",
        height=420,
    )
    fig_nii.update_xaxes(tickvals=[2022, 2023, 2024, 2025, 2026])
    st.plotly_chart(fig_nii, use_container_width=True)

    # ── Forecast summary table ─────────────────────────────────────────────────
    st.subheader("Forecast Summary (€m)")
    fc_pivot = fc.pivot(index="bank", columns="year", values="nii")
    fc_pivot.columns = [f"NII {y}E" for y in fc_pivot.columns]
    act_24 = k24[["nii"]].rename(columns={"nii": "NII 2024A"})
    summary = act_24.join(fc_pivot)
    for col in summary.columns:
        summary[col] = summary[col].apply(lambda x: f"€{x:,.0f}m" if pd.notna(x) else "—")
    st.dataframe(summary, use_container_width=True, height=215)
    st.caption(
        "E = estimate. Rate sensitivities are bank-specific (Pillar 3 IRRBB disclosures, FY2024). "
        "Volume growth varies by scenario: Dovish +3.5% / Base +2.0% / Hawkish +0.5% pa, compounded. "
        "Figures are directional estimates, not investment advice."
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — STRESS TEST
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("EBA-Style Adverse Scenario Stress Test")
    st.markdown(
        "Applies a simultaneous shock to (1) NIM compression, (2) loan volume decline, "
        "and (3) additional cost of risk. Based on EBA 2023 adverse scenario parameters. "
        "CET1 impact estimated using loan book × 50% risk weight (consistent with `04_forecasting/02_stress_test.ipynb`)."
    )

    c_l, c_r = st.columns([1, 2])

    with c_l:
        st.markdown("**Stress Parameters**")
        cor_bps = st.slider(
            "Additional Cost of Risk (bps)",
            min_value=0, max_value=500, value=200, step=25,
            help="Basis points of additional loan loss provisions on stressed loan book.",
        )
        loan_growth = st.slider(
            "Loan Volume Change (%)",
            min_value=-40, max_value=10, value=-15, step=5,
            help="Change in gross loan book vs 2024 actuals.",
        )
        nim_comp = st.slider(
            "NIM Compression (bps)",
            min_value=0, max_value=200, value=50, step=10,
            help="Reduction in net interest margin applied to total assets.",
        )
        st.divider()
        st.markdown(f"""
**EBA 2023 defaults**
CoR: +200bp | Loans: −15% | NIM: −50bp

SREP Floor: **{SREP_FLOOR}% CET1**
""")

    with c_r:
        # Compute stress for all banks
        results = {}
        for bank in BANKS:
            row = k24.loc[bank]
            results[bank] = stress_bank(row, cor_bps, loan_growth, nim_comp)

        # ── Results table ──────────────────────────────────────────────────────
        tbl_rows = []
        for bank in BANKS:
            r = results[bank]
            tbl_rows.append({
                "Bank":               bank,
                "Net Profit 2024A":   f"€{r['baseline_profit']:,.0f}m",
                "Stressed Profit":    f"€{r['stressed_profit']:,.0f}m",
                "Δ Profit":           f"{r['d_profit']:+,.0f}m",
                "CET1 2024A":         f"{r['baseline_cet1']:.1f}%",
                "Stressed CET1":      f"{r['stressed_cet1']:.1f}%",
                "Δ CET1 (pp)":        f"{r['d_cet1']:+.1f}pp",
                "Breaches SREP?":     "⚠️ YES" if r["breaches_srep"] else "✅ No",
            })

        tbl_df = pd.DataFrame(tbl_rows).set_index("Bank")

        def style_stress(df):
            styles = pd.DataFrame("", index=df.index, columns=df.columns)
            for bank in df.index:
                r = results[bank]
                if r["breaches_srep"]:
                    styles.loc[bank, "Breaches SREP?"] = "background-color: #450a0a; color: #fca5a5; font-weight: bold"
                    styles.loc[bank, "Stressed CET1"]  = "color: #fca5a5"
                else:
                    styles.loc[bank, "Breaches SREP?"] = "background-color: #14532d; color: #86efac"
                if r["d_profit"] < 0:
                    styles.loc[bank, "Δ Profit"] = "color: #f87171"
                if r["d_cet1"] < 0:
                    styles.loc[bank, "Δ CET1 (pp)"] = "color: #f87171"
            return styles

        st.dataframe(tbl_df.style.apply(style_stress, axis=None),
                     use_container_width=True, height=220)

        # ── CET1 waterfall ─────────────────────────────────────────────────────
        fig_cet = go.Figure()
        x_banks = BANKS

        fig_cet.add_trace(go.Bar(
            x=x_banks,
            y=[results[b]["baseline_cet1"] for b in x_banks],
            name="CET1 2024A",
            marker_color=[COLORS[b] for b in x_banks],
            opacity=0.85,
            hovertemplate="%{x}<br>CET1 2024A: %{y:.1f}%<extra></extra>",
        ))
        fig_cet.add_trace(go.Bar(
            x=x_banks,
            y=[results[b]["d_cet1"] for b in x_banks],
            name="Δ CET1 (stress)",
            marker_color=["#ef4444" if results[b]["d_cet1"] < 0 else "#10b981"
                          for b in x_banks],
            base=[results[b]["baseline_cet1"] for b in x_banks],
            hovertemplate="%{x}<br>Δ CET1: %{y:+.1f}pp<extra></extra>",
        ))
        fig_cet.add_hline(y=SREP_FLOOR, line_dash="dash", line_color="#f59e0b",
                          annotation_text=f"SREP floor {SREP_FLOOR}%",
                          annotation_font_color="#f59e0b")
        fig_cet.update_layout(
            **LAYOUT,
            barmode="stack",
            title="CET1 — Baseline vs Stressed",
            height=340,
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8")),
        )
        fig_cet.update_yaxes(ticksuffix="%", range=[0, 25])
        st.plotly_chart(fig_cet, use_container_width=True)

    st.caption(
        "Stressed CET1 = 2024 CET1 + (Δ Net Profit) / (Loans × 0.50). "
        "RWA proxy = loan book at 50% risk weight, consistent with `04_forecasting/02_stress_test.ipynb`. "
        "Tax rate implied from each bank's FY2024 actuals (15%–35% cap). "
        "This is a simplified single-period shock, not a multi-year dynamic model."
    )
