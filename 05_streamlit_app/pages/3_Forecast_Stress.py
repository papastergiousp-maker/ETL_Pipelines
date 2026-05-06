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

tab1, tab2, tab3 = st.tabs(["📉 NII Forecast 2025–2026", "⚠️ EBA-Style Stress Test", "🔢 Sensitivity Analysis"])

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


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SENSITIVITY ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Sensitivity Analysis")
    st.markdown(
        "Two grids: **(1)** how the Gordon Growth justified P/B changes across CoE and g assumptions, "
        "and **(2)** how stressed CET1 changes across cost-of-risk and loan-growth shocks. "
        "All figures use FY2024 actuals as the base."
    )

    sens_tab_a, sens_tab_b = st.tabs(["Justified P/B vs CoE & g", "CET1 vs CoR & Loan Growth"])

    # ── Grid A: Justified P/B sensitivity ─────────────────────────────────────
    with sens_tab_a:
        st.markdown("**Justified P/B = (ROE − g) / (CoE − g)**  \n"
                    "Grid shows justified P/B for a selected bank across CoE and g ranges. "
                    "Green = above 1.0× (book-accretive), red = below 1.0×.")

        pb_bank = st.selectbox("Bank", BANKS, key="pb_bank")
        roe_for_pb = k24.loc[pb_bank, "roe"]
        st.caption(f"{pb_bank} FY2024 ROE (year-end equity): **{roe_for_pb:.1f}%**  "
                   f"| Use avg-equity ROE for a more conservative estimate.")

        coe_vals = [8.5, 9.0, 9.5, 10.0, 10.3, 11.0, 11.5, 12.0]
        g_vals   = [1.0, 1.5, 2.0, 2.5, 3.0]

        pb_grid = np.array([
            [(roe_for_pb - g) / (coe - g) if (coe - g) > 0 else np.nan
             for coe in coe_vals]
            for g in g_vals
        ])

        fig_pb = go.Figure(go.Heatmap(
            z=pb_grid,
            x=[f"{c:.1f}%" for c in coe_vals],
            y=[f"{g:.1f}%" for g in g_vals],
            colorscale=[[0, "#450a0a"], [0.45, "#7f1d1d"], [0.5, "#1e293b"],
                        [0.55, "#14532d"], [1.0, "#052e16"]],
            zmid=1.0,
            text=[[f"{v:.2f}×" if not np.isnan(v) else "—" for v in row] for row in pb_grid],
            texttemplate="%{text}",
            textfont=dict(size=11, color="#f1f5f9"),
            hovertemplate="CoE: %{x}<br>g: %{y}<br>P/B: %{z:.2f}×<extra></extra>",
            showscale=True,
            colorbar=dict(title="P/B", tickfont=dict(color="#94a3b8"),
                          titlefont=dict(color="#94a3b8")),
        ))
        # Mark the base-case cell (CoE = 10.3%, g = 2.0%)
        base_coe_idx = coe_vals.index(10.3)
        base_g_idx   = g_vals.index(2.0)
        fig_pb.add_shape(type="rect",
                         x0=base_coe_idx - 0.5, x1=base_coe_idx + 0.5,
                         y0=base_g_idx - 0.5,   y1=base_g_idx + 0.5,
                         line=dict(color="#f59e0b", width=2))
        fig_pb.update_layout(
            **{k: v for k, v in LAYOUT.items() if k not in ("xaxis", "yaxis")},
            title=f"{pb_bank} — Justified P/B Sensitivity (amber box = base case: CoE 10.3%, g 2.0%)",
            height=340,
            xaxis=dict(title="Cost of Equity (CoE)", tickfont=dict(color="#94a3b8"),
                       gridcolor="#1e293b"),
            yaxis=dict(title="Long-run Growth (g)", tickfont=dict(color="#94a3b8"),
                       gridcolor="#1e293b"),
        )
        st.plotly_chart(fig_pb, use_container_width=True)
        st.caption(
            "Formula: (ROE − g) / (CoE − g). ROE = FY2024 reported (year-end equity). "
            "CoE = 10.3% base case: Rf 3.5% + β×ERP 5.5% + CRP 1.3% (post-Greek IG upgrade). "
            "g = 2.0% base case (nominal GDP growth proxy). "
            "Values > 1.0× imply the bank earns above its cost of equity and should trade above book."
        )

    # ── Grid B: CET1 sensitivity to CoR × Loan Growth ─────────────────────────
    with sens_tab_b:
        st.markdown("**Stressed CET1 = Baseline CET1 + Δ Net Profit / (Loans × 0.50)**  \n"
                    "Grid shows stressed CET1 ratio for each bank. "
                    "Red cells breach the 10.5% SREP floor.")

        cet1_bank = st.selectbox("Bank", BANKS, key="cet1_bank")
        brow = k24.loc[cet1_bank]

        cor_bps_grid  = [0, 50, 100, 150, 200, 250, 300, 400, 500]
        loan_gr_grid  = [0, -5, -10, -15, -20, -25, -30, -40]

        cet1_grid = np.array([
            [stress_bank(brow, cor_b, lg, 50)["stressed_cet1"]
             for cor_b in cor_bps_grid]
            for lg in loan_gr_grid
        ])

        colorscale_cet1 = [
            [0.0,  "#450a0a"],   # deep red — far below SREP
            [0.3,  "#7f1d1d"],
            [0.45, "#ef4444"],   # red — below SREP
            [0.55, "#14532d"],   # green — above SREP
            [0.7,  "#16a34a"],
            [1.0,  "#052e16"],   # deep green
        ]

        fig_cet1 = go.Figure(go.Heatmap(
            z=cet1_grid,
            x=[f"+{c}bp" for c in cor_bps_grid],
            y=[f"{lg}%" for lg in loan_gr_grid],
            colorscale=colorscale_cet1,
            zmid=SREP_FLOOR,
            text=[[f"{v:.1f}%" for v in row] for row in cet1_grid],
            texttemplate="%{text}",
            textfont=dict(size=11, color="#f1f5f9"),
            hovertemplate="CoR shock: %{x}<br>Loan Δ: %{y}<br>Stressed CET1: %{z:.1f}%<extra></extra>",
            showscale=True,
            colorbar=dict(title="CET1 (%)", ticksuffix="%",
                          tickfont=dict(color="#94a3b8"),
                          titlefont=dict(color="#94a3b8")),
        ))
        # Mark EBA 2023 adverse defaults (+200bp CoR, −15% loans)
        eba_cor_idx  = cor_bps_grid.index(200)
        eba_loan_idx = loan_gr_grid.index(-15)
        fig_cet1.add_shape(type="rect",
                           x0=eba_cor_idx - 0.5, x1=eba_cor_idx + 0.5,
                           y0=eba_loan_idx - 0.5, y1=eba_loan_idx + 0.5,
                           line=dict(color="#f59e0b", width=2))
        fig_cet1.update_layout(
            **{k: v for k, v in LAYOUT.items() if k not in ("xaxis", "yaxis")},
            title=f"{cet1_bank} — Stressed CET1 Sensitivity (amber = EBA 2023 adverse: +200bp CoR, −15% loans)",
            height=380,
            xaxis=dict(title="Additional Cost of Risk", tickfont=dict(color="#94a3b8"),
                       gridcolor="#1e293b"),
            yaxis=dict(title="Loan Volume Change", tickfont=dict(color="#94a3b8"),
                       gridcolor="#1e293b"),
        )
        st.plotly_chart(fig_cet1, use_container_width=True)
        st.caption(
            f"NIM compression fixed at 50bp (EBA 2023 adverse). SREP floor = {SREP_FLOOR}% (red = breach). "
            "RWA proxy = loans × 50% risk weight. "
            "Tax rate implied from FY2024 actuals (clamped 15%–35%)."
        )
