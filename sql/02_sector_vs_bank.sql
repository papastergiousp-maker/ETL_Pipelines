-- 02_sector_vs_bank.sql
-- Compare each bank's NIM and ROE against the sector average for the same year.
-- Shows: CTE, GROUP BY aggregation, JOIN, deviation from mean.

WITH sector_avg AS (
    SELECT
        year,
        ROUND(AVG(nim), 2)  AS avg_nim,
        ROUND(AVG(roe), 2)  AS avg_roe
    FROM kpis
    GROUP BY year
)
SELECT
    k.bank,
    k.year,
    k.nim                                       AS bank_nim,
    s.avg_nim                                   AS sector_avg_nim,
    ROUND(k.nim - s.avg_nim, 2)                 AS nim_vs_sector,
    k.roe                                       AS bank_roe,
    s.avg_roe                                   AS sector_avg_roe,
    ROUND(k.roe - s.avg_roe, 2)                 AS roe_vs_sector
FROM kpis k
JOIN sector_avg s ON k.year = s.year
ORDER BY k.year, k.bank;

-- Positive nim_vs_sector → above-average spread capture (e.g. NBG in 2024)
