# Loom Walkthrough Script — Greek Banking Sector Analysis
# Target length: 3 minutes | Audience: FinTech/banking recruiters

---

## Setup before recording

- Browser: open Streamlit app at https://greek-banking-sector-analysis.streamlit.app/
- VS Code: project root open, README visible
- Terminal: ready to run `pytest tests/ -v`
- Close all unrelated tabs and notifications

---

## [0:00–0:20] Hook — what this project answers

> "Greek banks went from near-insolvency in 2015 to some of the highest ROEs in Europe
> by 2024. I built this analysis to answer one question from first principles:
> which bank is best positioned heading into the ECB rate-cutting cycle —
> and which one carries the most earnings-quality risk?"

**Show:** README headline section with the +55% NII stat and architecture diagram.
Scroll past it quickly — don't read it out loud.

---

## [0:20–0:50] Data foundation — credibility first

> "All data comes from 12 official annual report PDFs — no Bloomberg, no paid vendors.
> I extracted every figure with pdfplumber, cross-validated against source page numbers,
> and logged every correction in a data corrections file."

**Show:**
1. `02_Banking_Sector_Dashboard/data/processed/kpis_final.csv` — just flash it, 12 rows
2. Switch to terminal → run `pytest tests/ -v` live
3. 26 tests pass in ~1s → "26 assertions verify the data hasn't drifted"

---

## [1:00–1:40] The analysis — show the actual work

**Switch to Streamlit app.**

> "The Streamlit app is the recruiter-facing layer — 8 pages built on the same SQLite
> database."

**Bank Deep Dive (30 sec):**
- Click through to Eurobank
- Point to the 7 KPI cards at the top: "RoTE, ROE, ROA — I show both year-end and
  average-equity ROE because that's what equity analysts actually use"
- Hover over the ROE trend chart: "three series — year-end ROE, average-equity ROE,
  and RoTE. The gap between ROE and RoTE is Hellenic Bank acquisition intangibles"

**Investment Thesis (20 sec):**
- Navigate to Investment Thesis
- Drag the CoE slider from 10.3% down to 9.5%: "this is a live Gordon Growth model —
  P/TBV upside updates in real time"
- Point to the BUY/HOLD/SELL ratings: "driven by P/TBV, not P/B, because that's the
  institutional standard for European banks"

---

## [1:40–2:10] The hard analysis — what makes it investment-grade

**Switch to DTC Analysis:**
> "DTCs are the single biggest capital quality issue for Greek banks — PSI-era
> deferred tax assets guaranteed by the Greek state. A bank at 15% CET1 where
> 40% is DTC has materially weaker capital than a German bank at 15%.
> This chart shows the derecognition path to 2034."

**Switch to Macro & Funding:**
> "And here's the rate-cycle context. Greek banks had near-zero deposit betas in
> 2022–2023 — they captured almost the full ECB hike as NIM. NBG had the highest
> NIM sensitivity, which is why it's the most defensively positioned in a rate-cut cycle."

---

## [2:10–2:40] Stress test — the thing analysts actually care about

**Switch to Forecast & Stress → Sensitivity tab:**
> "The stress test applies EBA-style parameters — plus 200 basis points on cost of risk,
> minus 15% loan volume. Under that scenario, Piraeus CET1 falls to 9.9%,
> below the ECB SREP floor of 10.5%."
- Drag the CoR slider to 400bps, watch CET1 heatmap change colour
- Point to the amber box: "the box marks the EBA 2023 adverse scenario baseline"

---

## [2:40–3:00] Close — stack and signal

> "The full stack: pdfplumber extraction, pandas cleaning, SQLite, pytest CI,
> 5 analysis notebooks, 2 forecasting notebooks, Streamlit, Power BI, Excel model,
> and a 12-slide deck. Everything reproducible from a single git clone.
> The repo is linked in the description — feedback welcome."

**Show:** README skills table for 3 seconds, then cut.

---

## Recording tips

- Don't read slides — talk over visuals
- Keep cursor movement slow and deliberate
- If you stumble: pause, breathe, continue — don't re-record the whole thing
- Target 3:00 exactly; 3:30 max
- Add captions in Loom after recording (auto-generated, just review)
- Thumbnail: use the radar/spider chart screenshot from Peer Comparison page
