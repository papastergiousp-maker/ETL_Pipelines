@echo off
cd /d "C:\Users\Spyro\Desktop\FinTech -Analyst\Projects\Greek_Banking_Sector_Analysis"

echo === Git status ===
git status

echo.
echo === Staging changes ===
git add 05_streamlit_app/app.py 05_streamlit_app/pages/3_Forecast_Stress.py 05_streamlit_app/utils/data.py README.md

echo.
echo === Committing ===
git commit -m "fix(app): TypeError on duplicate xaxis kwarg + improve NII forecast methodology" -m "- Fix Plotly update_layout TypeError in app.py (4 charts) and 3_Forecast_Stress.py by replacing **LAYOUT + xaxis= pattern with update_xaxes/update_yaxes calls" -m "- NII forecast: bank-specific Pillar 3 sensitivities replace flat sector allocation" -m "- Volume growth now scenario-dependent (3.5%% dovish / 2.0%% base / 0.5%% hawkish) and compounds on previous stressed NII instead of static 2024 base" -m "- Remove dead code in vol_effect dict computation" -m "- README: justified P/B uses proper Gordon Growth (ROE-g)/(CoE-g); CoE updated to 10.3%% reflecting Greek IG upgrade (CRP 200bp -> 130bp)"

echo.
echo === Pushing to origin/main ===
git push origin main

echo.
echo === DONE ===
pause
