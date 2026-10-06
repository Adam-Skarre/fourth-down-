# Résumé wording

Use only after reviewing the code and being able to explain your own contribution to this AI-assisted project. Do not invent dates or affiliation.

**Fourth Down — Predictive Analytics & Decision Optimization | Python, SQL, JavaScript, AWS S3, Databricks**

*Independent Project | [Live demo](https://adam-skarre.github.io/fourth-down-/) | [GitHub](https://github.com/Adam-Skarre/fourth-down-)*

- Evaluated ridge regression against three forecasting baselines on 15,773 historical records using chronological training, model selection, and 3,503 evaluation forecasts.
- Built an interactive lineup optimizer and scenario-analysis interface; validated behavior with 109 unit/API/research tests and 78 browser/Python optimizer comparisons.
- Stored reference data and outputs in private, versioned AWS S3 storage and processed a replicated dataset in Databricks with PySpark and Delta tables.

## Explain the evidence

Ridge reduced RMSE relative to history average; MAE was effectively tied and its paired bootstrap interval crossed zero. Do not claim a proven forecasting advantage, actual league gains, or a model-caused championship.

The larger study ran locally. AWS holds four reference artifacts. Databricks processed the 164-record reference dataset and its final PASS was reported by the user; the runtime export has not yet been collected. No direct S3-to-Databricks connection or automated production pipeline is claimed. See [cloud status](../reports/cloud_setup_status.json).
