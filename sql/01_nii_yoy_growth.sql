-- 01_nii_yoy_growth.sql
-- Year-over-year NII growth per bank using LAG window function.
-- Shows: LAG(), ROUND(), computed columns, NULLIF guard against divide-by-zero.

SELECT
    bank,
    year,
    ROUND(nii, 1)                                                   AS nii_eur_m,
    ROUND(LAG(nii) OVER (PARTITION BY bank ORDER BY year), 1)       AS nii_prior_yr,
    ROUND(nii - LAG(nii) OVER (PARTITION BY bank ORDER BY year), 1) AS abs_growth_eur_m,
    ROUND(
        (nii - LAG(nii) OVER (PARTITION BY bank ORDER BY year))
        * 100.0
        / NULLIF(LAG(nii) OVER (PARTITION BY bank ORDER BY year), 0),
        1
    )                                                               AS pct_growth
FROM kpis
ORDER BY bank, year;

-- Expected (2024 vs 2022 for Eurobank): nii grows from ~1 390 to ~2 160 → +55 %
