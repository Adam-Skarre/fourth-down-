# Explore Fourth Down

Open `index.html` in a browser for the complete portfolio. No accounts, API keys or installation are required.

1. **Overview:** the question, scope and research finding.
2. **Lineup lab:** adjust a historical roster and scoring, flag a player unavailable, compare pickups, and export the optimized lineup.
3. **The research:** inspect the 2022/2023/2024 split, compare model errors, filter by position, and export the study.
4. **Data & build:** review provenance and the actual AWS/Databricks execution scope.

To serve locally: `python3 -m http.server 8877 --bind 127.0.0.1`, then open `http://127.0.0.1:8877`.

For the Python API and original workspaces, run `python3 -m fourth_down`. The original lab is at `/lab.html` and supplementary 2025 case at `/championship.html`.

The interactive demo uses 164 historical records and a fixed forecasting heuristic. The separate fitted-model study uses 15,773 records across three seasons. These are distinct analyses; neither establishes live fantasy winnings.
