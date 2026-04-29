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
| `roe` | % | Return on Equity | Net Profit / Average Equity × 100 |
| `cost_to_income` | % | Cost-to-Income Ratio | Operating Expenses / Operating Income × 100 |
| `loan_to_deposit` | % | Loan-to-Deposit Ratio | Loans / Deposits × 100 |
| `nim` | % | Net Interest Margin | NII / Average Earning Assets × 100 |
| `nii_yoy` | % | NII Year-over-Year growth | (NII_current - NII_prior) / NII_prior × 100 |
| `profit_yoy` | % | Net Profit YoY growth | (Profit_current - Profit_prior) / Profit_prior × 100 |
| `assets_yoy` | % | Total Assets YoY growth | (Assets_current - Assets_prior) / Assets_prior × 100 |
| `opincome_yoy` | % | Operating Income YoY growth | (OpIncome_current - OpIncome_prior) / OpIncome_prior × 100 |

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
- Data extracted manually from PDF annual reports

---

*Last updated: April 2026*
*Project: Greek Banking Sector Analysis 2022-2024*