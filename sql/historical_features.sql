-- The cutoff happens BEFORE any window function. Current/future outcomes cannot
-- enter feature computation. :week is the decision week, not the last played week.
WITH scored AS (
    SELECT *, standard_points + :ppr * receptions AS points
    FROM player_games
    WHERE season = :season AND week < :week
), features AS (
    SELECT *,
        COUNT(*) OVER (PARTITION BY player_id) AS history_count,
        AVG(points) OVER (PARTITION BY player_id) AS history_mean,
        AVG(points) OVER (
            PARTITION BY player_id ORDER BY week
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS recent_three_mean,
        LAG(points) OVER (PARTITION BY player_id ORDER BY week) AS previous_points,
        ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY week DESC) AS recency_rank
    FROM scored
)
SELECT * FROM features ORDER BY player_id, week;
