# Explain the code, not the buzzwords

This document describes the original 164-record decision lab and its API-backed interface. The portfolio now also includes a separate trained, three-season ridge-regression study; see [research methodology](RESEARCH.md) and the [current README](../README.md). Current cloud execution evidence is recorded in [cloud status](../reports/cloud_setup_status.json).

## A clear project description

“Fourth Down is a fantasy-football lineup lab. It answers a specific question: does a one-player pickup improve my legal starting lineup? I separated validated historical data, pre-week projections, exact roster optimization, and the interface so the recommendation can be inspected and tested.”

This is a useful description only after you have run the app and understand those components. It is an AI-assisted independent project, not UConn coursework or a cloud production deployment.

## Walkthrough in code order

**`fourth_down/data.py`** is the data boundary. Explain why `(player_id, season, week)` is a better key than a name, why NaN and duplicate rows are errors, and why a missing game is not filled with zero. The repository executes parameterized SQL through a fresh SQLite connection.

**`sql/historical_features.sql`** filters the information set first. Explain why applying a rolling or full-history mean before filtering would leak future outcomes. `ROW_NUMBER`, `AVG`, `COUNT` and rolling windows prepare inspection-friendly features. SQLite is appropriate for a small offline dataset; Spark would add deployment overhead without solving a local need.

**`fourth_down/model.py`** produces an explicit weighted average. Be able to calculate one player's forecast from the last six scores. The weights have consistent units—fantasy points. Variability is kept separate, rather than added to a point forecast as an arbitrary unitless “AI score.”

**`fourth_down/optimizer.py`** fills a seven-bit mask. One bit corresponds to each slot. For every player, the algorithm starts from a copied frontier, which prevents using that player twice. Explain why a naive top-seven ranking can violate positional requirements and why FLEX requires care.

**`waiver_moves`** recomputes the legal lineup after each hypothetical swap. The value of a pickup is a difference between two optimized lineups, not just the candidate's projection. A bench upgrade can have zero current starting value. The model is explicitly one-week only; it can recommend dropping someone you would keep for longer-term reasons.

**`fourth_down/server.py`** makes the UI and analysis separate. Inputs are checked again at the API boundary. It binds to loopback, rejects unrelated Host/Origin values, serves only an explicit static-file allowlist and keeps real historical outcomes behind a separate reveal endpoint. This is not production authentication or internet hosting.

**`app/app.js`** makes real requests, retains local roster preferences, protects against outdated asynchronous responses, escapes dynamic text and exports data. There are no placeholder charts or hard-coded recommendations. The SVG chart uses the returned history.

**`tests/`** proves limited properties, not general quality. Point to future-outcome mutation tests, the independent brute-force optimizer comparison, strict data-contract tests, the same-cohort error calculation, and HTTP tests. Know which paths were not executed in a real cloud account.

## Concrete demonstration

Use default Week 13 / half PPR. The example roster projects about 96.6 points. Compare one-for-one moves: the starting-value effect of Alvin Kamara is about +1.6 projected points, Mike Evans about +1.2, and Zach Ertz 0.0. These are deterministic model calculations for a fictional roster, not guarantees or claims about actual league ownership.

Toggle a starter's unavailable flag. Show the changed legal starting seven. Switch scoring and explain why receptions alter the ordering. Open the audit and explain why 121 observed outcomes and three excluded unknowns are not a general accuracy claim.

## Questions you should be able to answer

- Why can an optimizer be exact even when the projections are uncertain? It is exact for the supplied objective and constraints, not for unknowable future outcomes.
- Why not call the model machine learning? It has fixed heuristic coefficients; no parameters are fitted from training examples.
- Why is the time filter before the SQL windows? To prevent target/future records from entering any aggregate or candidate feature.
- Why are absent rows not zero? The observation does not identify participation or missing-data status.
- Why is the cloud path optional? The sample is small; the extension demonstrates a governed batch interface without pretending distributed compute is needed.
- What was actually tested in AWS? No real AWS execution; only local upload planning and fake-client argument contracts.
- What would production require? Real source freshness, governed credentials, tested integrations, availability data, monitoring, fuller evaluation and an appropriate authenticated deployment. These are not implemented by calling the local server production-ready.

## Personal contribution

Before using the project to demonstrate your own ability, run the tests, trace one calculation by hand, and implement a change you can explain. Accurately distinguish AI-generated scaffolding, your own revisions, and any cloud steps you personally executed. Do not invent a class, professor, date or performance result.


## 2025 extension: questions the code can answer

The case-study module fits a single convex-blend coefficient using early-season mean squared error, freezes it, and evaluates later player-weeks. The fit returns zero, an important result: more recent weighting was not supported by this particular training set. The original model nevertheless has lower later RMSE, while historical mean has slightly lower MAE. Explain the difference between those loss functions and why this is not a reason to re-tune on the later period.

The original formula recommends Stevenson over Montgomery in week 17 using earlier stats, but misses weeks 15 and 16. Always-start-Stevenson and last-game controls beat it across that illustrative three-week comparison. The code exports all of these outcomes. The player cohort and case were selected retrospectively, so this is a research diagnostic rather than clean prospective validation.
