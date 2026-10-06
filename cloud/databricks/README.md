# Optional Databricks / Delta batch path

**Status:** the original S3-connected notebook below remains syntax-checked only. The separate `free_edition_run.py` notebook was run by the user in Databricks Free Edition, with a reported final PASS verifying 164 records and 14 forecasts. Its input is an embedded copy of the S3 dataset, not a direct S3 read. Exported runtime evidence has not yet been collected. See `reports/cloud_setup_status.json`.

## Purpose

The notebook reads the same normalized `player_games.csv` used locally, validates its contract, writes a Delta source table, computes strictly pre-week features, and writes a projection table. It is a separate batch integration—not a hidden dependency of the app.

## Run in a configured workspace

Import `fourth_down_notebook.py` as a Python notebook. Supply a UC volume path to the normalized CSV, or an S3 path already authorized through a Unity Catalog external location and storage credential. The notebook contains no keys. A CloudFormation bucket alone does not configure Unity Catalog permissions.

Set the widgets for `source_path`, `catalog`, `schema`, `decision_week` and `scoring`. Use a **dedicated project schema**: execution overwrites the project's `player_games` and `projections` tables in that schema. The source is restricted to 2024 for compatibility with the local demonstration.

The notebook requires a suitable Databricks runtime and permissions to read the source, create/use the dedicated schema, and write Delta tables. Runtime/version compatibility and account permissions must be checked in the target workspace. Cloud compute may incur charges.

## Model parity and boundaries

The notebook uses the same 0.75 recency weights over up to six prior observed games, 0.65 recent / 0.35 history blend, population standard deviation and target-week cutoff. A cutoff assertion rejects features using the target week.

Projection rows are **not automatically eligible lineups**. The app separately handles its bye map, three-game minimum, stale observations, manual exclusions, and exact slot optimization. Do not present the batch projection table as proof that a player is active.

Compare the notebook output with `data/processed/projections.csv` using player ID, season, scoring and decision week after the first real execution. Round only at display/export boundaries; the local projection export uses four decimal places.

For a round-trip to the app, export the notebook's normalized source data into your own writable UC volume, download its CSV part file, then run:

```bash
python -m fourth_down --data path/to/part-file.csv
```

The app does not directly query a Databricks SQL warehouse; that integration is not implemented.

## Official references

- UC S3 access: https://docs.databricks.com/aws/en/connect/unity-catalog/cloud-storage/s3/
- Reading files: https://docs.databricks.com/aws/en/files/readproc
- SQL `read_files`: https://docs.databricks.com/aws/en/sql/language-manual/functions/read_files
