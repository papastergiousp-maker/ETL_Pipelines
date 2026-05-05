-- 03_peer_ranking.sql
-- Rank all four banks on six KPIs for 2024; compute a composite Z-score ranking.
-- Shows: RANK(), DENSE_RANK(), multiple window partitions, CTE chaining, CASE WHEN.

WITH raw AS (
    SELECT bank, roe, nim, cost_to_income, cet1, npe_ratio, roa
    FROM kpis
    WHERE year = 2024
),
ranked AS (
    SELECT
        bank,
        -- Lower cost_to_income and npe_ratio is better → invert rank direction
        RANK() OVER (ORDER BY roe            DESC) AS rk_roe,
        RANK() OVER (ORDER BY nim            DESC) AS rk_nim,
        RANK() OVER (ORDER BY cost_to_income ASC)  AS rk_ci,   -- lower = better
        RANK() OVER (ORDER BY cet1           DESC) AS rk_cet1,
        RANK() OVER (ORDER BY npe_ratio      ASC)  AS rk_npe,  -- lower = better
        RANK() OVER (ORDER BY roa            DESC) AS rk_roa,
        roe, nim, cost_to_income, cet1, npe_ratio, roa
    FROM raw
)
SELECT
    bank,
    roe, rk_roe,
    nim, rk_nim,
    cost_to_income, rk_ci,
    cet1, rk_cet1,
    npe_ratio, rk_npe,
    roa, rk_roa,
    ROUND((rk_roe + rk_nim + rk_ci + rk_cet1 + rk_npe + rk_roa) / 6.0, 2) AS composite_avg_rank,
    DENSE_RANK() OVER (
        ORDER BY (rk_roe + rk_nim + rk_ci + rk_cet1 + rk_npe + rk_roa) ASC
    )                                                                        AS overall_rank
FROM ranked
ORDER BY overall_rank;

-- Eurobank expected to lead; Piraeus scores well on efficiency but lags on CET1
