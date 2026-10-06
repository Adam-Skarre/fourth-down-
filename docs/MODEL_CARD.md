# Model card — recency blend v1

This document describes the original 164-record decision lab and its API-backed interface. The portfolio now also includes a separate trained, three-season ridge-regression study; see [research methodology](RESEARCH.md) and the [current README](../README.md). Current cloud execution evidence is recorded in [cloud status](../reports/cloud_setup_status.json).

## Intended use

A local educational/portfolio replay of one-week fantasy lineup and one-for-one pickup decisions. It demonstrates data contracts, temporal feature construction, constraint optimization and transparent evaluation. It is not live fantasy advice, a wagering system, a medical assessment of athletes, or a trained ML product.

## Data

The reference consists of 164 observed 2024 regular-season player-game records for 14 selected players, Weeks 3–16. This is a curated sample, not a random sample or a complete player universe. Rookies, many positions/roles and most teams are absent. Weeks 1–2 are not loaded. The manifest preserves source attribution and transformations. A file checksum guards against package drift, not source inaccuracies. An internet-dependent reconciliation script exists but was not executed during the isolated build.

Missing observations remain missing. They may reflect byes, injury, nonparticipation, or missing/selected data; a missing record alone does not establish which explanation applies.

## Input contract and scoring

Key: `(player_id, season, week)`. Supported positions: QB, RB, WR and TE. Source standard fantasy points may be negative. Scoring presets add zero, half a point or one point per reception. This does not cover all platform-specific bonuses. Source points already incorporate the source's standard scoring; the app does not infer every event from a partial box score.

Rows are rejected for missing mandatory values, non-finite numbers, duplicate keys, invalid position codes, fractional reception counts and sanity-bound violations. Position changes for the same player ID must be resolved explicitly.

## Temporal information set

The SQL query filters to `week < decision_week` before any window calculation. Player identity, team and available candidate history come from these earlier rows as well. The target-week actual is retrieved separately only during audit/reveal. No target-week participation filter is used to generate projections.

The latest observed team may lag a trade. A preseason-known 2024 bye map is used. Eligibility requires three prior observations, no mapped bye and an observation within the previous two weeks; users can additionally exclude a player manually. These filters are heuristics, not injury verification.

## Projection specification

For up to six most recent observed prior games, use weights `0.75^k`, newest first. Normalize weights to sum to one. Blend 65% of that recent weighted average with 35% of the mean of all loaded prior observations for the player and season. Round displayed/exported projections to four decimal places internally and usually one in the interface.

Coefficients were selected as transparent implementation choices. They were not estimated with regression or optimized by searching these evaluation results. There is no trained parameter artifact, inferred injury probability, matchup adjustment, calibrated confidence interval, or claim of optimal forecasting.

Recent population standard deviation and empirical quartiles describe up to six observed games. They are not predictive distributions. Negative outcomes are possible. The model does not silently clip every result to zero.

## Decision objective

Default: maximize the sum of projected points subject to seven legal starting slots and player uniqueness. “Steadier” mode subtracts 0.25 × each player's recent population standard deviation. That penalty trades off projected output and historical variability, but it ignores correlations and cannot be called lineup win probability, forecast risk, or portfolio variance.

An exact bitmask dynamic program searches the selected eligible roster. The waiver module inserts one candidate and removes one roster player, recomputes the optimum, and compares the new objective and unpenalized projected total with the original. It does not value future weeks, bids, depth, keeper rights, or real league availability. Drops can therefore look unreasonable from a rest-of-season perspective; the one-week scope is deliberate.

## Evaluation protocol and observed results

For each evaluable week, compute predictions from prior records only. Evaluate eligible player-weeks that have an observed target outcome. The model and both baselines use exactly the same rows. Missing targets are counted, then excluded—not fabricated as zero.

Reference half-PPR audit: 121 observed predictions, 3 unknown target outcomes.

| Method | MAE | RMSE | Bias (predicted minus actual) |
|---|---:|---:|---:|
| Recency blend | 6.1191 | 7.6802 | -0.3181 |
| Loaded-history mean | 6.2254 | 7.8946 | -0.4206 |
| Previous observed game | 7.8579 | 9.8531 | 0.0423 |

This is a retrospective selected-player demonstration. It is not an independent multi-season validation, an experiment on actual league decisions, or a proof of statistical significance. Missing-outcome exclusion makes the errors conditional on observed participation/data. No injury-adjusted full-roster performance can be inferred.

## Validated vs unvalidated

Validated locally: explicit scoring, strict input contracts, SQL-to-Python aggregate agreement, target/future-outcome mutation invariance, future-only candidate exclusion, baseline cohort alignment, optimizer/brute-force agreement, manual/bye exclusions, API boundaries and UI interactions.

Unvalidated: full-NFL generalization, predictive calibration, real-time freshness, unseen-season performance, actual league outcomes, direct production hosting, external source download success in this build, AWS deployment and Databricks execution.

No zero-error, elite predictive accuracy or production-readiness claim is justified by this reference.
