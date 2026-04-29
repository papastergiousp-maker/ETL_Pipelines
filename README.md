# Greek Banking Financial Analysis 2022–2024

**End-to-end financial analysis of the Greek banking sector — data extracted directly from official annual report PDFs, no pre-cleaned datasets used.**

Two interconnected projects: a deep-dive single-bank pipeline (Eurobank) and a multi-bank comparative dashboard covering all four Greek systemic banks.

---

## Project 1 — Eurobank Single-Bank Pipeline

Full extract → clean → load → query → visualise pipeline for Eurobank (2022–2024).

### Pipeline

| Step | Tool | Description |
|:-----|:-----|:------------|
| 1. Extract | Python · pdfplumber | Financial tables extracted directly from official Annual Report PDFs |
| 2. Clean | pandas | Structured and normalised P&L and Balance Sheet data |
| 3. Load | SQLite | Loaded into a relational database with 2 tables |
| 4. Query | SQL | KPI calculations using SELECT, JOIN, GROUP BY, Window Functions |
| 5. Analyse | Python · pandas | YoY trends, ROE, Cost-to-Income, Loan-to-Deposit ratios |
| 6. Visualise | Power BI · DAX | Interactive dashboard with slicers and custom DAX measures |

### Dashboard Preview

![Eurobank Dashboard](eurobank_dashboard.png)

### Key Findings

| KPI | 2022 | 2023 | 2024 |
|:----|-----:|-----:|-----:|
| Net Interest Income | €1,456m | €2,174m | €2,504m |
| Operating Income | €2,089m | €2,821m | €3,242m |
| Net Profit | €1,353m | €1,148m | €1,458m |
| Cost-to-Income | 46.8% | 38.2% | 33.0% |
| Loan-to-Deposit | 75.2% | 72.4% | 68.3% |
| ROE | — | — | 16.9% |

**Insights**
- **NII +72%** over 2 years — driven by higher interest rates and strong loan growth
- **Cost-to-Income 46.8% → 33.0%** — significant efficiency improvement
- **Loan-to-Deposit 68.3%** — healthy liquidity, well below the 80% threshold
- **ROE 16.9%** — above European banking average (~12%)
- **Net Profit +27% YoY** in 2024 despite a challenging macro environment

### SQL Highlights

```sql
-- Cost-to-Income Ratio trend
SELECT
    'Cost-to-Income Ratio' AS kpi,
    ROUND(ABS(value_2022) * 100.0 / 2089, 1) AS ratio_2022,
    ROUND(ABS(value_2023) * 100.0 / 2821, 1) AS ratio_2023,
    ROUND(ABS(value_2024) * 100.0 / 3242, 1) AS ratio_2024
FROM income_statement
WHERE metric = 'Operating expenses';

-- NII YoY Growth with Window Function
WITH yearly AS (
    SELECT metric, value_2022 AS val, '2022' AS year FROM income_statement
    WHERE metric = 'Net interest income'
    UNION ALL
    SELECT metric, value_2023, '2023' FROM income_statement
    WHERE metric = 'Net interest income'
    UNION ALL
    SELECT metric, value_2024, '2024' FROM income_statement
    WHERE metric = 'Net interest income'
)
SELECT year,
       val AS net_interest_income,
       ROUND((val - LAG(val) OVER (ORDER BY year)) * 100.0 /
             LAG(val) OVER (ORDER BY year), 1) AS yoy_growth_pct
FROM yearly;

-- Executive KPI Summary using JOIN
SELECT 'ROE 2024' AS kpi,
    ROUND(
        (SELECT value_2024 FROM income_statement
         WHERE metric = 'Net profit attributable to shareholders') * 100.0 /
        (SELECT value_2024 FROM balance_sheet
         WHERE metric = 'Total equity'), 1
    ) || '%' AS value
UNION ALL
SELECT 'Cost-to-Income 2024',
    ROUND(ABS(
        (SELECT value_2024 FROM income_statement WHERE metric = 'Operating expenses')) * 100.0 /
        (SELECT value_2024 FROM income_statement WHERE metric = 'Operating income'), 1
    ) || '%'
UNION ALL
SELECT 'Loan-to-Deposit 2024',
    ROUND(
        (SELECT value_2024 FROM balance_sheet
         WHERE metric = 'Loans and advances to customers') * 100.0 /
        (SELECT value_2024 FROM balance_sheet
         WHERE metric = 'Deposits from customers'), 1
    ) || '%';
```

---

## Project 2 — Greek Banking Sector Dashboard

Interactive web dashboard comparing all four Greek systemic banks: **Eurobank, Alpha Bank, Piraeus Bank, NBG**.

Data extracted from 12 official annual report PDFs (4 banks × 3 years) using the same Python/pdfplumber pipeline. Results stored in SQLite and rendered as a fully client-side dashboard using Plotly and sql.js.

Open `greek-banking-analysis/index.html` in a browser — no server required.

### Sector Snapshot (2024, € million)

| Bank | NII | Net Profit | Total Assets | ROE |
|:-----|----:|-----------:|-------------:|----:|
| Eurobank | 2,504 | 1,458 | 101,151 | 16.9% |
| NBG | 2,356 | 1,158 | 74,957 | 13.7% |
| Piraeus Bank | 2,088 | 1,066 | 80,044 | 12.9% |
| Alpha Bank | 1,646 | 668 | 70,954 | 8.2% |

**Insights**
- **Sector NII +58%** from 2022 to 2024 (€5.4bn → €8.6bn) — rate cycle tailwind across all four banks
- **Eurobank leads** on both NII and ROE, reflecting its diversified regional presence
- **NBG most cost-efficient** — operating expenses €581m vs sector average ~€846m
- **Combined sector deposits grew +8%** YoY to ~€246bn in 2024, signalling deposit franchise strength

---

## Repository Structure

```
eurobank-financial-analysis/
│
├── Database/
│   ├── balance_sheet.csv          ← Eurobank Balance Sheet 2022–2024
│   ├── income_statement.csv       ← Eurobank Income Statement 2022–2024
│   └── eurobank.db                ← SQLite database (Eurobank)
│
├── greek-banking-analysis/
│   ├── data/
│   │   ├── greek_banking_final.db ← SQLite (4 banks × 3 years)
│   │   ├── processed/             ← Cleaned CSVs (balance sheet, IS, KPIs)
│   │   └── raw/                   ← 12 source PDFs (4 banks × 3 years)
│   ├── notebooks/
│   │   └── 01_extract.ipynb       ← Full pipeline: extract → clean → load → analyse
│   └── index.html                 ← Interactive Plotly dashboard (open in browser)
│
├── eurobank_dashboard.png         ← Power BI dashboard screenshot
├── eurobank_BI_dashboard.pdf      ← Power BI dashboard export
└── eurobank_dashboard.pbix        ← Power BI source file
```

---

## Tools & Technologies

`Python` `pandas` `pdfplumber` `SQLite` `SQL` `Plotly` `sql.js` `Power BI` `DAX` `Jupyter Notebook`

---

## Data Sources

**Eurobank:** Official Annual Reports 2022–2024 — [investor-relations](https://www.eurobank.gr/en/group/investor-relations)

**Alpha Bank:** Official Annual Reports 2022–2024 — [investor-relations](https://www.alpha.gr/en/group/investor-relations)

**Piraeus Bank:** Official Annual Reports 2022–2024 — [investor-relations](https://www.piraeusbankgroup.com/en/investors)

**NBG:** Official Annual Reports 2022–2024 — [investor-relations](https://www.nbg.gr/en/the-group/investor-relations)

All figures in € million.

---

## Methodology

### Data Extraction Pipeline

| Step | Description | Tools |
|:-----|:-------------|:------|
| 1. **PDF Collection** | Downloaded official Annual Reports (2022-2024) for all 4 systemic banks from their investor relations portals | Manual download |
| 2. **Table Extraction** | Identified and extracted financial tables from PDF reports using programmatic parsing | `pdfplumber` |
| 3. **Data Cleaning** | Normalized column names, handled missing values, standardized units (€ millions) | `pandas` |
| 4. **Data Validation** | Cross-checked totals and calculated ratios against published KPIs in reports | Python + manual verification |
| 5. **Database Loading** | Loaded cleaned data into SQLite for efficient querying | `sqlite3` |
| 6. **KPI Calculation** | Computed derived metrics (ROE, Cost-to-Income, NIM, YoY growth) using SQL | SQL + pandas |
| 7. **Visualization** | Built interactive dashboard using Plotly + sql.js | Plotly, sql.js |

### Data Quality Notes

- **Source**: Official annual reports published by each bank
- **Frequency**: Annual (calendar year)
- **Currency**: Euros (€)
- **Units**: Millions unless otherwise stated
- **Coverage**: 4 Greek systemic banks × 3 years (2022-2024)
- **Validation**: All calculated KPIs cross-checked against reported figures where available

### Limitations

1. **Annual only**: No quarterly data available in this version
2. **Static data**: Requires manual refresh when new reports are published
3. **Estimated ratios**: Some derived ratios (e.g., NIM) use simplified formulas based on available data
4. **NPL data**: Non-performing loan ratios not included in current dataset (requires more granular data from reports)

### Reproducibility

To reproduce the analysis:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the extraction notebook
cd greek-banking-analysis/notebooks
jupyter notebook 01_extract.ipynb

# Open the dashboard
cd greek-banking-analysis
open index.html
```

---

## Data Dictionary

See [DATA_DICTIONARY.md](greek-banking-analysis/data/DATA_DICTIONARY.md) for detailed field descriptions.

---

*Project: Greek Banking Sector Analysis 2022-2024*
