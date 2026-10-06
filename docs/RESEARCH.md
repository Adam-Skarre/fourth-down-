# Forecast study: protocol and interpretation

## Objective

Predict half-PPR points for regular-season QB/RB/WR/TE observations. Forecasts support analysis of scoring conditional on observed participation. This study does not predict whether a player will play, a fantasy win probability, or the realized value of an actual lineup transaction.

## Data

Official nflverse player-statistics releases for 2022–2024 were downloaded on October 6, 2026. The normalized files contain 5,252, 5,294 and 5,227 rows respectively. Source and normalized SHA-256 hashes are in `data/research/manifest.json`. Records preserve standard fantasy points and receptions; half-PPR adds 0.5 points per reception.

Rows are checked for duplicate player-season-week keys, supported positions, finite numeric values, and consistent position identity. Source PPR values are checked against standard points plus receptions when available. No player outcomes are synthesized.

## Information set

For a target player-week, features use only previous observed games in the same season. Require at least three prior observations and a most-recent observation no more than two weeks earlier. Evaluate only rows with observed outcomes. This defines a conditional evaluation cohort and can favor players with persistent participation. It does not charge the model for unavailable players, missing data, or unobserved zero-score games.

Features: history mean, exponentially weighted mean of up to six recent games (decay 0.75), last-three mean, previous observed score, population SD of recent games, prior observation count, and RB/WR/TE indicators (QB reference).

## Estimation and selection

Standardize features using the fitting cohort only. Solve ridge regression with an unpenalized intercept by pivoted Gaussian elimination of the normal equations. The objective is sum of squared errors plus λ times the squared coefficient norm. The implementation is intentionally dependency-free; a larger or ill-conditioned problem should use a numerically stable linear-algebra library.

Fit candidate λ values (0.1, 1, 10, 100, 1,000) on 2022. Select by 2023 MAE, with lower λ breaking exact ties. Refit the selected λ=10 on combined 2022–2023, recomputing scaling from that fitting cohort, then evaluate 2024. Predictions are not clipped.

The feature specification and split were designed retrospectively after these seasons occurred. Although model selection excludes 2024 outcomes, the evaluation is not a prospective, preregistered experiment. Do not repeatedly tune against 2024 while continuing to call it untouched validation.

## Comparators and uncertainty

Compare ridge, the fixed 65/35 recency-history blend, history average, and previous observed game on identical rows. Report MAE, RMSE, signed bias, position breakdowns and weekly errors.

For MAE(ridge) minus MAE(history), resample players with replacement, retaining all each sampled player's errors, and compute a row-weighted paired difference. Use 1,000 replicates, seed 42, and percentile bounds. Player clustering captures within-player dependence, but not shared weekly shocks or uncertainty from model selection and refitting. The interval is descriptive conditional uncertainty, not a guarantee about future seasons.

## Finding

Across 3,503 observed 2024 forecasts, ridge MAE is 4.6284 and history-average MAE is 4.6293. The 95% player-cluster interval is [−0.0464, +0.0472], so there is no demonstrated MAE advantage. Ridge RMSE is 6.1774 versus 6.2845 for history average, consistent with smaller squared errors on this cohort; uncertainty for the RMSE difference was not estimated.

The decision lab remains on its original documented heuristic. The fitted research model is not silently substituted into the optimizer. Cloud verification covers the original 164-row reference, not the expanded research corpus.

## Reproduction

Run `python3 -m fourth_down.research`, then `python3 -m scripts.build_site`. The study JSON stores the scaling parameters, fitted coefficients, validation scores, cohort sizes, and aggregate results. The prediction CSV stores each evaluated player-week's forecast, target, baseline values, and history cutoff.
