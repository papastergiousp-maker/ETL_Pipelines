@echo off
cd /d "C:\Users\Spyro\Desktop\FinTech -Analyst\Projects\Greek_Banking_Sector_Analysis"

echo === Stage methodology text updates ===
git add 05_streamlit_app/pages/3_Forecast_Stress.py

echo.
echo === Commit ===
git commit -m "docs(forecast): align Forecast page narrative with new bank-specific NII methodology" -m "- Update top-of-page methodology blurb to mention per-bank Pillar 3 sensitivities (Eurobank -58, Alpha -42, Piraeus -52, NBG -43) and scenario-dependent volume growth (3.5%% / 2.0%% / 0.5%%)" -m "- Update results-table caption to match new approach"

echo.
echo === Push ===
git push origin main

echo.
echo === DONE ===
pause
