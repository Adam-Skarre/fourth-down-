# Fourth Down — AJ 2025 championship-roster case

**Executed:** October 6, 2026. **Status:** retrospective, exploratory, selected-roster analysis.

## Scope and evidence

The user supplied a 2025 league-history screenshot showing first place and a listed 9–5–0 record, a photograph of 17 drafted entries, and a report that Rhamondre Stevenson was added during the playoffs. These sources do not provide weekly starting lineups, complete transactions, league scoring, exact playoff dates, or opponents.

The complete roster inventory is in `data/championship_2025/roster.json`. This statistical diagnostic includes De'Von Achane, David Montgomery, RJ Harvey and Rhamondre Stevenson: **64 published 2025 regular-season player-game observations**. The other drafted players are inventoried, not evaluated. It is not a full-team replay.

## Reproducible default assumptions

Full PPR (one point per catch), an illustrative weeks 15–17 comparison, and Stevenson available by week 15. These are scenario assumptions, not confirmed league settings or acquisition dates. The app supports standard, half-PPR and PPR and availability from week 15, 16 or 17. All figures below use the full-PPR/week-15 default.

## Calculation

The original, unchanged projection is:

`0.65 × recent weighted average + 0.35 × all-prior-games average`

The recent component uses the last six observed games, with newest-to-oldest weights 1, 0.75, 0.75², and so on. Both components exclude the decision week and all later weeks. At least three prior appearances are required. Team byes are excluded. A history gap greater than two weeks triggers the existing availability gate. An absent target outcome is omitted from evaluation, never silently set to zero.

A second model fits one coefficient alpha in `history + alpha × (recent − history)`. Alpha is constrained to [0,1] and minimizes squared error on **25 eligible observed player-weeks in weeks 4–10**. The closed-form fit uses no later-week outcomes. It selected **alpha = 0**, equivalent to using the historical mean. That result is retained, not replaced with a coefficient that looks better in the playoffs.

## Later-week benchmark

All methods use the same **23 eligible observed player-weeks in weeks 11–17**. Week 18 exists in the source file but is outside fitting and evaluation. Smaller errors are better.

| Method | Mean absolute error | Root mean squared error |
|---|---:|---:|
| Original 65/35 model | 5.39 | 6.43 |
| Early-season fitted blend (alpha = 0) | 5.36 | 6.84 |
| History-average baseline | 5.36 | 6.84 |
| Last-three-game baseline | 5.69 | 6.85 |
| Last-game baseline | 5.73 | 7.39 |

The original heuristic has lower RMSE than these controls on this sample, but slightly worse MAE than the historical mean. The coefficient fit does not improve the later-week RMSE. These small, selected-sample results do not establish statistical significance or general superiority.

## Stevenson versus Montgomery: one hypothetical slot

| Week | Montgomery forecast | Stevenson forecast | Original-model pick | Montgomery actual | Stevenson actual |
|---|---:|---:|---|---:|---:|
| 15 | 10.88 | 8.40 | Montgomery | 9.2 | 10.7 |
| 16 | 10.51 | 8.73 | Montgomery | 1.4 | 17.8 |
| 17 | 8.54 | 11.04 | Stevenson | 6.0 | 27.2 |

With only earlier-game inputs, the original formula would favor Stevenson for week 17 in this two-player comparison. Stevenson outscored Montgomery by **21.2 PPR points** that week. That is a realized counterfactual difference, not the model's projected margin (about 2.50 points) and not a verified gain over the user's actual lineup.

The same rule misses the higher scorer in weeks 15 and 16. Its complete default-window result is:

| Method or descriptive control | Realized points across the three weeks |
|---|---:|
| Original 65/35 model | 37.8 |
| Early-season fitted blend / historical mean | 16.6 |
| Last-three-game baseline | 37.8 |
| Last-game baseline | 54.2 |
| Always start Montgomery | 16.6 |
| Always start Stevenson | 55.7 |
| Hindsight-best choice, not a forecast | 55.7 |

The original rule selects the higher scorer in **one of three weeks**. It improves over always starting Montgomery but loses to the last-game baseline and to always starting Stevenson. A three-RB exercise is also exported, but WR/TE FLEX options, other running backs and actual roster transactions are outside its scope.

## What this establishes

The project now has executable parameter estimation, chronological feature cutoffs, baseline comparisons, a player-specific decision case, visible misses, and tests designed to detect future-data contamination. The evidence supports a limited retrospective case study. It does not establish that the software was used in 2025, caused the championship, or improves league-winning probability.

The roster and case were selected after the championship was known. Although later outcomes never enter fitting, the later period is not an untouched prospective test. The source records are retrospectively retrieved published statistics, not reconstructed historical publication vintages. Forecast metrics are conditional on observed appearances and do not capture the full cost of starting an unavailable player.

## Source provenance

Published PPR values and receptions were manually transcribed and normalized. NFL game logs supplied the week/box-score references. Source totals reconcile to the included player seasons. Values use one-decimal source precision; Montgomery week 5 is 18.2 rather than the additional 0.02 from fractional passing yardage. Stevenson weeks 2 and 16 include two-point conversions. The source CSV has a SHA-256 fingerprint in the manifest.

- Achane: https://www.statmuse.com/nfl/ask/achane-ppr-points-by-week-2025 and https://www.nfl.com/players/devon-achane/stats/logs/2025/
- Montgomery: https://www.statmuse.com/nfl/ask/david-montgomery-ppr-2025 and https://www.nfl.com/players/david-montgomery/stats/logs/2025/
- Harvey: https://www.statmuse.com/nfl/ask/rj-harvey-ppr-stats and https://www.nfl.com/players/rj-harvey/stats/logs/2025/
- Stevenson: https://www.statmuse.com/nfl/ask/stevenson-ppr-points-by-week-2025 and https://www.nfl.com/players/rhamondre-stevenson/stats/logs/2025/
- Methodological reference: https://scikit-learn.org/stable/common_pitfalls.html#data-leakage

## Run and inspect

```bash
python3 -m fourth_down --case-2025
python3 -m fourth_down.championship
python3 -m fourth_down.championship --scoring half --acquired-week 17
python3 -m unittest discover -s tests -v
```

The analysis command writes a JSON report and row-level CSV. The app performs the same calculations behind its interface. No cloud account or extra Python package is required for the local app.

**Verification:** 103 unit/API tests passed. The 21 new browser checks used a fetch-to-real-HTTP bridge because the build environment blocked direct browser navigation; no model outputs were mocked. Tests cover invalid inputs, published-total reconciliation, conversion scoring, source integrity, future-outcome poisoning, equal evaluation cohorts, comparison losses, all nine scoring/acquisition scenarios, exports and mobile layout. Actual AWS/Databricks execution remains unperformed.
