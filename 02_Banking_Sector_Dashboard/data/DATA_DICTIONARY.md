# Greek Banking Sector Analysis - Data Dictionary

## Overview
This document describes the metrics and data fields used in the Greek Banking Sector Analysis project.

---

## Balance Sheet Metrics (`balance_sheet_final.csv`)

| Metric | Unit | Description |
|--------|------|-------------|
| `metric` | string | Name of the balance sheet item |
| `unit` | string | Measurement unit (€ million) |
| `year` | integer | Fiscal year (2022, 2023, 2024) |
| `value` | float | Monetary value in millions of euros |
| `bank` | string | Bank name (Alpha Bank, Eurobank, NBG, Piraeus Bank) |

### Key Balance Sheet Items

| Metric | Description |
|--------|-------------|
| Cash and balances with central banks | Cash held at Bank of Greece + foreign currency reserves |
| Loans and advances to customers | Gross loan portfolio (before provisions) |
| Total assets | Sum of all assets (balance sheet total) |
| Deposits from customers | Customer deposits (demand + term) |
| Total liabilities | All liabilities including deposits |
| Total equity | Shareholders' equity + reserves |

---

## Income Statement Metrics (`income_statement_final.csv`)

| Metric | Unit | Description |
|--------|------|-------------|
| `metric` | string | Name of the income statement item |
| `unit` | string | Measurement unit (€ million) |
| `year` | integer | Fiscal year (2022, 2023, 2024) |
| `value` | float | Monetary value in millions of euros |
| `bank` | string | Bank name |

### Key Income Statement Items

| Metric | Description |
|--------|-------------|
| Net interest income (NII) | Interest income - interest expense |
| Net banking fee and commission income | Fee income from banking services |
| Operating income | Total operating revenue |
| Operating expenses | Staff costs + administrative expenses + depreciation |
| Impairment losses on loans | Loan loss provisions (negative = expense) |
| Profit before tax | Pre-tax profit |
| Net profit attributable to shareholders | Net income after tax |

---

## KPIs Dataset (`kpis_final.csv`)

| Column | Unit | Description | Formula |
|--------|------|-------------|---------|
| `bank` | string | Bank name | - |
| `year` | integer | Fiscal year | - |
| `nii` | € million | Net Interest Income | - |
| `operating_income` | € million | Total operating income | - |
| `operating_expenses` | € million | Total operating expenses (negative) | - |
| `net_profit` | € million | Net profit after tax | - |
| `impairment` | € million | Loan loss provisions (negative) | - |
| `loans` | € million | Gross loans to customers | - |
| `deposits` | € million | Customer deposits | - |
| `equity` | € million | Shareholders' equity | - |
| `total_assets` | € million | Total assets | - |
| `roe` | % | Return on Equity | Net Profit / Year-end Equity × 100 ¹ |
| `cost_to_income` | % | Cost-to-Income Ratio | Operating Expenses / Operating Income × 100 |
| `loan_to_deposit` | % | Loan-to-Deposit Ratio | Loans / Deposits × 100 |
| `nim` | % | Net Interest Margin | NII / Year-end Total Assets × 100 ² |
| `nii_yoy` | % | NII Year-over-Year growth | (NII_current - NII_prior) / NII_prior × 100 |
| `profit_yoy` | % | Net Profit YoY growth | (Profit_current - Profit_prior) / Profit_prior × 100 |
| `assets_yoy` | % | Total Assets YoY growth | (Assets_current - Assets_prior) / Assets_prior × 100 |
| `opincome_yoy` | % | Operating Income YoY growth | (OpIncome_current - OpIncome_prior) / OpIncome_prior × 100 |

**Methodology notes:**
- ¹ **ROE** uses year-end equity (not average equity). Using average equity would yield slightly higher ROE values (~0.5–1pp difference). Year-end is used for simplicity and consistency across all banks.
- ² **NIM** is calculated as NII / Year-end Total Assets — a simplified proxy. True NIM uses average interest-earning assets (loans + securities + interbank) in the denominator. The true NIM would be ~1–1.5pp higher. This approximation understates NIM but allows consistent cross-bank comparison without requiring full earning-asset decomposition for all banks.

---

## Derived Metrics (Not Calculated Yet)

### Profitability
- **ROA (Return on Assets)**: Net Profit / Total Assets × 100
- **Net Profit Margin**: Net Profit / Operating Income × 100
- **Efficiency Ratio**: (Operating Expenses - Depreciation) / (NII + Non-NII Income)

### Asset Quality
- **NPL Ratio**: Non-Performing Loans / Gross Loans × 100
- **Coverage Ratio**: Loan Loss Provisions / NPLs × 100
- **Cost of Risk**: Impairment / Average Gross Loans × 100

### Capital & Liquidity
- **CET1 Ratio**: Common Equity Tier 1 / Risk-Weighted Assets × 100
- **Tier 1 Ratio**: Tier 1 Capital / Risk-Weighted Assets × 100
- **LCR (Liquidity Coverage Ratio)**: High-Quality Liquid Assets / Total Net Cash Outflows × 100
- **NSFR (Net Stable Funding Ratio)**: Available Stable Funding / Required Stable Funding × 100

### Market Ratios
- **P/E (Price-to-Earnings)**: Market Cap / Net Profit
- **P/B (Price-to-Book)**: Market Cap / Book Value
- **Dividend Yield**: Dividends per Share / Price per Share × 100

---

## Data Sources

| Bank | Source | URL |
|------|--------|-----|
| Alpha Bank | Annual Reports 2022-2024 | https://www.alpha.gr/en/group/investor-relations |
| Eurobank | Annual Reports 2022-2024 | https://www.eurobank.gr/en/group/investor-relations |
| NBG | Annual Reports 2022-2024 | https://www.nbg.gr/en/group/investor-relations |
| Piraeus Bank | Annual Reports 2022-2024 | https://www.piraeusbank.gr/en/group/investor-relations |

---

## Notes

- All monetary values are in **millions of euros (€ million)**
- Fiscal year: Calendar year (January 1 - December 31)
- YoY calculations use prior year as baseline
- Negative values in impairment/expenses indicate expense items
- Data extracted from official PDF annual reports via pdfplumber + manual verification

### Data corrections log

| Date | File | Bank | Year | Field | Old value | New value | Source |
|------|------|------|------|-------|-----------|-----------|--------|
| May 2026 | balance_sheet_final.csv | Alpha Bank | 2022 | Due to credit institutions | 7,093.0 | 14,345.1 | alpha_2023.pdf p.131 comparative |
| May 2026 | balance_sheet_final.csv | Alpha Bank | 2022–2024 | Investment securities | — (missing) | 12,710.1 / 15,993.8 / 17,574.0 | alpha_2023.pdf p.131, alpha_2024.pdf p.282 |
| May 2026 | balance_sheet_final.csv | Alpha Bank | 2022–2024 | Due from credit institutions | — (missing) | 1,368.1 / 1,722.5 / 2,296.0 | alpha_2023.pdf p.131, alpha_2024.pdf p.282 |
| May 2026 | balance_sheet_final.csv | Eurobank | 2022–2024 | Various rows | unit empty | € million | all Eurobank PDFs |

> **Note on Alpha 2022 correction:** The original extraction used the 2022 standalone PDF for Alpha Bank. The 2022 value for "Due to banks" (14,345m) was verified from the prior-year comparative column in the 2023 Annual Report (alpha_2023.pdf, Consolidated Balance Sheet, p.131). The original CSV showed 7,093m for both 2022 and 2023, which was the 2023 value incorrectly applied to 2022.

> **Note on 2024 restatement:** The alpha_2024.pdf shows restated 2023 comparative figures (Total Assets 71,453m vs original 72,694m) due to discontinued operations reclassification. This project uses the **originally reported** figures from each year's annual report for consistency.

---

*Last updated: May 2026*
*Project: Greek Banking Sector Analysis 2022-2024*