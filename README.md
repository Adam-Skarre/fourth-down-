# Fourth Down

**Forecast. Decide. Verify.** An interactive fantasy-football decision lab and a reproducible, three-season forecasting study by Adam Skarre.

## [Open the live dashboard →](https://adam-skarre.github.io/fourth-down-/#lineup)

**[Homepage](https://adam-skarre.github.io/fourth-down-/) · [Interactive lineup lab](https://adam-skarre.github.io/fourth-down-/#lineup) · [Research dashboard](https://adam-skarre.github.io/fourth-down-/#research)**

Open the link in any browser. No installation, login, or download is required. Change players, scoring, and availability in the lineup lab, or explore model results in the research dashboard.

Hosted on **GitHub Pages**, with a custom JavaScript interface. This is an interactive historical-data dashboard, not a live NFL data feed. Streamlit is not required to view or use it.

[Research implementation](fourth_down/research.py) · [Model results](reports/research.json) · [Data provenance](data/research/manifest.json)

## The question

A player ranking does not tell you whether a pickup improves your starting lineup. A sophisticated model does not automatically outperform a simple average. Fourth Down tests both ideas:

- **Decision lab:** select a roster, change scoring, exclude unavailable players, optimize seven legal slots, and measure a one-add/one-drop scenario.
- **Forecast research:** train ridge regression on earlier seasons, select its regularization chronologically, and compare it with three baselines on identical evaluation rows.
- **Visible evidence:** inspect the time split, errors by position and week, uncertainty, data provenance, and cloud execution status.

The interface is a portable static application. It runs without accounts, API keys, or a backend. Python generates its forecast snapshots; the browser optimizer is checked against the Python implementation.

## Research result

**15,773 historical records. 3,503 evaluation forecasts. 420 evaluation players.**

| Phase | Season | Eligible observed examples | Purpose |
|---|---:|---:|---|
| Train | 2022 | 3,442 | Fit feature scaling and candidate ridge models |
| Select | 2023 | 3,583 | Select λ by MAE from 0.1, 1, 10, 100, 1,000 |
| Evaluate | 2024 | 3,503 | Score after refitting the selected λ = 10 on 2022–2023 |

The target is **half-PPR points for an observed player-week**, conditional on at least three prior games in the same season and a prior observation within two weeks. All features precede the predicted week.

| Method | 2024 MAE ↓ | 2024 RMSE ↓ | Bias |
|---|---:|---:|---:|
| Ridge regression | 4.6284 | 6.1774 | −0.3281 |
| Fixed recency blend | 4.6509 | 6.2988 | −0.2396 |
| History average | 4.6293 | 6.2845 | −0.4127 |
| Last observed game | 5.8374 | 7.9517 | +0.0704 |

**Interpretation:** ridge reduces RMSE relative to history average, but MAE is effectively tied. The paired player-cluster bootstrap 95% interval for MAE(ridge) − MAE(history) is **[−0.0464, +0.0472]**, crossing zero. Added complexity does not establish an MAE advantage in this evaluation.

The bootstrap uses 1,000 resamples and seed 42. It is conditional on sampled players; it does not account for shared weekly shocks or model-selection uncertainty. This is retrospective, chronologically separated research, not a preregistered prospective test. Missing outcomes are excluded, never treated as zero. See [research methodology](docs/RESEARCH.md) and [row-level predictions](reports/research_predictions.csv).

## Try it locally

Open **`index.html`** in a browser, or serve the folder:

```bash
python3 -m http.server 8877 --bind 127.0.0.1
```

Visit `http://127.0.0.1:8877`. The portfolio includes Overview, Lineup lab, The research, and Data & build.

For the Python API and original workspaces:

```bash
python3 -m fourth_down
```

The portfolio opens at `/`; the original API-backed lab remains available at `/lab.html` and the 2025 case study at `/championship.html`.

### A 60-second walkthrough

1. Open **Lineup lab**. The default Week 13 half-PPR example projects about **96.6** starting points.
2. Flag Joe Mixon unavailable; the optimizer rebuilds a legal lineup. Reset the demo and try the suggested pickup.
3. Open **The research**. Switch MAE/RMSE and filter by position; the all-position finding remains explicitly labeled.
4. Open **Data & build** to inspect source downloads and the actual cloud execution record.

The interactive lab uses the **original fixed 65/35 recency blend** on 164 selected 2024 records, not the fitted research regression. Its purpose is a transparent decision replay. It has no live injury or ownership feed, and does not claim real league gains.

## AWS and Databricks

| Component | Verified scope |
|---|---|
| AWS S3 | Four reference artifacts uploaded through the AWS console; private, versioned, SSE-S3-encrypted storage |
| Databricks Free Edition | User reported final PASS: 164 input records, 14 forecasts, Delta table readback and agreement with local results |
| Direct S3 → Databricks access | Not configured; the notebook uses an explicit embedded copy of the uploaded dataset |
| Expanded three-season benchmark | Executed locally; not yet run in Databricks |
| CloudFormation / boto3 uploader | Included implementation; not used for the console upload |

The Databricks runtime export has not yet been collected. See [execution status](reports/cloud_setup_status.json), [Free Edition notebook](cloud/databricks/free_edition_run.py), and the separate [S3-connected notebook](cloud/databricks/fourth_down_notebook.py).

## Reproduce and validate

Python 3.10+; no Python dependencies required for the local study and application.

```bash
python3 -m fourth_down.research
python3 -m scripts.build_site
python3 -m unittest discover -s tests -v
python3 -m scripts.check_browser_engine  # requires Node.js
```

**109 unit/API/research tests** and **78 browser/Python optimizer parity cases** passed locally. Tests cover input contracts, future-data mutation, chronological feature construction, ridge fitting, baseline cohort alignment, exact optimization, and HTTP boundaries. GitHub Actions runs the suite on Python 3.10, 3.12, and 3.13.

Normalized 2022–2024 research datasets are included with source and output hashes. The 2024 importer has been corrected to the current official nflverse release URL:

```bash
python3 -m scripts.import_nflverse --season 2024 --output data/full_2024.csv
```

## Repository map

| Path | Purpose |
|---|---|
| `index.html`, `site/` | Responsive portfolio and interactive browser decision lab |
| `fourth_down/research.py` | Standardized ridge regression, chronological selection, bootstrap evaluation |
| `fourth_down/` | Validated ingestion, SQLite features, forecasting, optimization, local API |
| `data/research/` | Normalized three-season data and provenance |
| `reports/research*` | Reproducible study and player-week predictions |
| `cloud/` | AWS storage/upload components and Databricks notebooks |
| `tests/`, `scripts/` | Validation, import, export, and portable-site generation |
| `app/` | Original API-backed lab and supplementary 2025 retrospective |

## Attribution

Built with AI assistance; technical contributions and limitations should be described accurately. Application code is MIT licensed. NFL statistics are attributed to nflverse contributors under CC BY 4.0; see [third-party notices](THIRD_PARTY_NOTICES.md). The visual direction draws inspiration from Firecrawl’s fantasy page; no Firecrawl code, logos, or assets are used. No NFL, JPMorganChase, AWS, or Databricks endorsement is implied.
