# Third-party attribution

## Historical NFL statistics

Source: **nflverse contributors**, weekly player statistics from the nflverse data ecosystem. Source documentation and data licensing:

- https://nflreadr.nflverse.com/articles/dictionary_player_stats.html
- https://nflreadr.nflverse.com/reference/load_player_stats.html
- https://github.com/nflverse/nflverse-data
- https://raw.githubusercontent.com/nflverse/nflverse-data/master/LICENSE
- https://creativecommons.org/licenses/by/4.0/

The included normalized CSV preserves selected factual records from a public mirror:

- Repository: https://github.com/merlin-gogolin/fantasy
- Commit: `03995a26515c43bfe687f0c3723a69806b2e7d4e`
- Files: `data/raw/{QB,RB,WR,TE}_2024_weekly.csv`
- QB blob: `9609c5071600e248c7ca4f3f76615421b2eff94c`
- RB blob: `e1ff51e104c012490cd38c33933f118676c2745c`
- WR blob: `66a88b3b2747060412c512e6a43589f786947e7f`
- TE blob: `7bd04a3dee67bc319fcae159c11c311ccb5d84b7`

Changes: selected 14 players and their available 2024 regular-season Weeks 3–16 records; retained IDs, names, positions, teams, season, week, opponent, standard fantasy points and receptions; renamed columns and sorted records. Fantasy outcomes were not synthesized. No source repository application code was copied into this project.

Source rows were inspected through retrieval tools and transcribed into the compact reference fixture. The online reconciliation script is included, but an automated source-to-file comparison could not be executed in the network-isolated build environment. A SHA-256 match verifies the packaged bytes have not changed; it is not proof of external statistical accuracy.

## Bye schedule

The 2024 team bye-week map was checked against the published schedule breakdown:
https://dknetwork.draftkings.com/2024/05/16/bye-week-breakdown-for-the-2024-nfl-season/

The schedule map is factual data, not article text. No article text, photos, player images or team logos are included.

## Software and services

The local runtime uses Python's standard library. Optional AWS code uses boto3 when installed by the user. The optional notebook uses PySpark and Delta in Databricks. Optional browser tests use Playwright and a separately installed Chromium. Those dependencies retain their own licenses and are not bundled here.

NFL, AWS, Databricks and all other third-party names identify data or integrations, not affiliation or endorsement.


## 2025 case-study statistics

The separately identified 2025 data are transcribed published quantitative player statistics, credited row-cohort by row-cohort in `data/championship_2025/manifest.json`. PPR/reception values are credited to StatMuse; week labels and box-score references to NFL.com. This code license does not license third-party websites or branding. No player photographs or league logos are bundled in this extension. Source facts are not generated or simulated.

## Expanded 2022–2024 forecast study

The research CSVs were normalized directly from the official `nflverse/nflverse-data` player_stats release assets. Exact source URLs and hashes are preserved in `data/research/manifest.json`. Attribution: nflverse contributors, CC BY 4.0. Transformations retain regular-season QB/RB/WR/TE records and selected identity/scoring columns; no outcomes are imputed.

## Visual reference

Firecrawl's fantasy page (https://www.firecrawl.dev/alexandria/fantasy) informed the restrained typography, warm accent color, and task-oriented flow. Fourth Down uses original HTML, CSS, SVG and JavaScript; no Firecrawl brand assets, source code, or data services are incorporated.
