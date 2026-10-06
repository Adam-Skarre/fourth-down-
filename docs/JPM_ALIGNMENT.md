# Why this project is relevant to a Data & AI role

Fourth Down is intentionally framed as a **decision system**, not a fantasy-football toy. The domain is sports; the engineering pattern is general.

## End-to-end flow

1. **Ingest** normalized historical player-game data from CSV/JSON sources.
2. **Validate** schema, keys, numeric values, and source checksums before calculation.
3. **Transform** prior-week observations into rolling features with Python and SQL window functions.
4. **Forecast** player outcomes with an explicit, explainable recency/history blend.
5. **Optimize** a position-constrained starting lineup with exact dynamic programming.
6. **Simulate** one-add/one-drop roster changes and quantify marginal lineup impact.
7. **Evaluate** forecasts walk-forward against simpler baselines using MAE, RMSE, and bias.
8. **Serve** the calculations through JSON HTTP endpoints to a custom browser interface.
9. **Test** data contracts, model leakage, optimizer correctness, API behavior, and UI smoke flows.
10. **Extend** the reference workflow with private AWS S3 storage and a replicated Databricks dataset; document the separate execution paths.
11. **Research** ridge regression across 2022–2024 using chronological model selection, baseline comparisons, and player-cluster bootstrap uncertainty. The larger study runs locally.

## JPM-style engineering signals

- **Business objective → measurable outcome:** “Does this transaction improve the legal starting lineup?” becomes a numeric counterfactual.
- **Data quality:** invalid rows fail loudly; missing observations are not silently zero-filled.
- **Model governance:** target-week leakage is explicitly tested, baselines are reported, and limitations are documented.
- **Decision intelligence:** the model is only one component; forecasts feed an optimizer and scenario engine.
- **Reproducibility:** deterministic calculations, checksums, exports, test fixtures, and CI.
- **Separation of concerns:** source data, feature logic, forecast logic, optimization, HTTP API, UI, and cloud examples are separate modules.

## Claims to avoid

Do not claim this model caused a fantasy championship, uses live 2026 data, is production-deployed to AWS/Databricks, or materially outperforms professional fantasy projections. The repository is stronger when the boundaries are explicit.
