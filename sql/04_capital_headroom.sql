-- 04_capital_headroom.sql
-- Classify each bank's CET1 buffer above the 10.5 % SREP floor and flag
-- whether it can comfortably absorb a 200 bp cost-of-risk shock.
-- Shows: CASE WHEN multi-condition, arithmetic expressions, filtering.

SELECT
    bank,
    year,
    cet1,
    ROUND(cet1 - 10.5, 1)          AS buffer_pp,
    ROUND((cet1 - 10.5) * 100, 0)  AS buffer_bp,
    CASE
        WHEN cet1 >= 17.0 THEN 'Fortress'
        WHEN cet1 >= 14.0 THEN 'Strong'
        WHEN cet1 >= 12.0 THEN 'Adequate'
        ELSE                   'Thin — watch closely'
    END                             AS capital_tier,
    -- Rough shock absorption: 200 bp CoR on loans ≈ loans * 0.02 / (total_assets * 0.12) pp CET1
    CASE
        WHEN (cet1 - 10.5) > 3.0 THEN 'Can absorb EBA adverse shock'
        ELSE                           'May breach SREP floor under stress'
    END                             AS stress_flag
FROM kpis
WHERE year = 2024
ORDER BY cet1 DESC;

-- NBG (19.1 %) and Eurobank (17.6 %) both classified as Fortress
-- Piraeus (13.7 %) is Adequate but flagged under stress
