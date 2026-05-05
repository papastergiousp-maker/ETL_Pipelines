@echo off
cd /d "C:\Users\Spyro\Desktop\FinTech -Analyst\Projects\Greek_Banking_Sector_Analysis"

echo === Last 5 commits ===
git log --oneline -5

echo.
echo === git diff app.py (first 30 lines) ===
git diff 05_streamlit_app/app.py | findstr /N "^" | findstr "^[1-3][0-9]:"
echo .........

echo.
echo === git ls-files vs disk: app.py size ===
dir 05_streamlit_app\app.py
git cat-file -s HEAD:05_streamlit_app/app.py 2>nul && echo (size of file in git HEAD)

echo.
echo === git status -s ===
git status -s

echo.
echo === Direct check: does line 134 of app.py contain update_xaxes? ===
findstr /N "update_xaxes" 05_streamlit_app\app.py

echo.
echo === git remote / branch ===
git remote -v
git branch -vv

echo.
pause
