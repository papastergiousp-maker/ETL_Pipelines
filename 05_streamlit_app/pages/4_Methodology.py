"""
4_Methodology.py — Data sources, metric definitions, and known limitations.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Methodology", page_icon="📋", layout="wide")

with st.sidebar:
    st.markdown("### 📋 Methodology")
    st.caption("All data sourced exclusively from official annual reports.")


st.title("Methodology & Data Sources")
st.divider()

# ── Data sources ───────────────────────────────────────────────────────────────
st.subheader("Data Sources")
st.markdown("""
All financial data was extracted from **12 official annual reports** (4 banks × 3 years, FY2022–FY2024).
No third-party data vendors, Bloomberg terminals, or paid databases were used.

| Bank | 2022 | 2023 | 2024 |
|------|------|------|------|
| Eurobank | Annual Report 2022 | Annual Report 2023 | Annual Report 2024 |
| Alpha Bank | Annual Report 2022 | Annual Report 2023 | Annual Report 2024 |
| Piraeus Bank | Annual Report 2022 | Annual Report 2023 | Annual Report 2024 |
| NBG | Annual Report 2022 | Annual Report 2023 | Annual Report 2024 |

**Extraction method:** `pdfplumber` (Python) with manual cross-validation of every extracted figure
against source PDF page numbers. All corrections are documented in the project's
`data_corrections.md`.

**ECB rate data:** Historical ECB Deposit Facility Rate averages (approximate) used for macro
context. No live API connection — rates are hardcoded for reproducibility.
""")

st.divider()

# ── Metric definitions ─────────────────────────────────────────────────────────
st.subheader("Metric Definitions")

defs = [
    ("NII", "Net Interest Income", "Interest income minus interest expense. Primary revenue line for Greek banks."),
    ("NIM", "Net Interest Margin", "NII / Total Assets. Proxy — uses year-end assets, not average earning assets."),
    ("ROE", "Return on Equity", "Net Profit / Average Equity. Average approximated as (Equity_t + Equity_{t-1}) / 2 where available."),
    ("ROA", "Return on Assets", "Net Profit / Total Assets."),
    ("C/I", "Cost-to-Income Ratio", "Operating Expenses (absolute) / Operating Income. Lower = more efficient."),
    ("L/D", "Loan-to-Deposit Ratio", "Gross Loans / Customer Deposits. Liquidity proxy; lower = more liquid."),
    ("CET1", "CET1 Ratio", "Common Equity Tier 1 / Risk-Weighted Assets. Regulatory capital adequacy measure."),
    ("SREP Floor", "SREP Minimum CET1", "10.5% minimum CET1 requirement set by ECB Supervisory Review and Evaluation Process for Greek systemic banks."),
    ("NPE Ratio", "Non-Performing Exposure Ratio", "NPEs / Gross Loans. Extracted from annual reports with pdfplumber; all figures verified to source PDF page."),
    ("PPOP", "Pre-Provision Operating Profit", "Operating Income minus Operating Expenses (before impairment)."),
    ("CoR", "Cost of Risk", "Impairment Losses / Gross Loans. Measures credit loss rate on the loan book."),
    ("Justified P/B", "Gordon Growth P/B", "ROE / CoE. Estimated using CoE = 11% (Rf 3.5% + β×ERP 5.5% + CRP 2.0%)."),
    ("RWA Proxy", "Stress-Test RWA", "Loan book × 0.50 risk weight, consistent with `04_forecasting/02_stress_test.ipynb`. Used to translate Δ profit into Δ CET1 ratio."),
]

def_df = pd.DataFrame(defs, columns=["Abbreviation", "Full Name", "Definition"])
st.dataframe(def_df.set_index("Abbreviation"), use_container_width=True, height=500)

st.divider()

# ── ETL pipeline ────────────────────────────────────────────────────────────────
st.subheader("Data Pipeline")
st.markdown("""
```
12 Annual Report PDFs
        │
        ▼  (pdfplumber extraction)
pandas DataFrames
        │
        ▼  (tidy-data transforms + manual validation)
3 processed CSVs
  ├── kpis_final.csv          (12 rows: 4 banks × 3 years)
  ├── income_statement_final.csv  (long format)
  └── balance_sheet_final.csv     (long format)
        │
        ▼  (rebuild_db.py)
greek_banking_final.db (SQLite)
        │
  ┌─────┼──────────────┐
  ▼     ▼              ▼
Streamlit  Plotly/sql.js  Power BI
  App    Dashboard       Dashboard
        │
  ┌─────┘
  ▼
03_analysis/ notebooks     04_forecasting/ notebooks
  DuPont · CAMELS            NII Forecast · Stress Test
  Peer · NII Walk            (basis for this app's
  Earnings Quality            Forecast & Stress page)
```
""")

st.divider()

# ── Limitations ────────────────────────────────────────────────────────────────
st.subheader("Known Limitations")
st.markdown("""
| Limitation | Impact | Workaround Used |
|---|---|---|
| Annual data only (no quarterly) | Cannot isolate intra-year rate pass-through | Rate sensitivity estimated at sector level |
| NIM uses year-end assets (not average earning assets) | NIM slightly overstated in growth years | Consistent methodology applied to all banks |
| Static P/B estimates (~end-2024 prices) | Market prices have moved; justified P/B is directional only | Clearly flagged as approximate in dashboard |
| RWA proxy (60% density) | Stressed CET1 impact is directional, not precise | Methodology note on every stress output |
| No live ECB rate feed | Forecast scenarios are pre-defined, not live | Three scenarios cover realistic range |
| Minority interests and one-off items | Tax rate implied from actuals; one-offs partially stripped in `05_earnings_quality.ipynb` | Noted in earnings quality notebook |

**What this analysis is:** A rigorous, reproducible, first-principles financial analysis of four Greek
systemic banks built entirely from public annual reports. Suitable for equity research context,
credit analysis, and FP&A purposes.

**What this analysis is not:** Investment advice. Real-money investment decisions require access to
management guidance, quarterly data, sell-side models, and regulatory filings not available here.
""")

st.divider()

# ── Data quality ───────────────────────────────────────────────────────────────
st.subheader("Data Quality")
st.markdown("""
**Automated tests:** 26 pytest assertions verify:
- ROE, ROA, C/I, L/D, NIM re-computed from raw CSVs match `kpis_final.csv` within ±1%
- Balance sheet identity: Total Assets ≈ Total Liabilities + Total Equity (within 1%)
- No nulls in primary key fields (`bank`, `year`)
- 4 unique banks × 3 unique years = exactly 12 rows

Run: `pytest tests/ -v` from the project root.

**Manual cross-checks:** Every figure was verified against source PDF page numbers.
Corrections are logged in `memory/data_corrections.md`.
""")

st.divider()
st.caption(
    "Greek Banking Sector Analysis 2022–2024 | "
    "Analyst: Spyros Papastergiou | spyrossyo96@gmail.com"
)
