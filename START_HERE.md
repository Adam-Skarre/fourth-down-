# New: your 2025 championship-roster research case

Open a terminal in the extracted `fourth-down` folder and run:

```bash
python3 -m fourth_down --case-2025
```

On Windows use `py -3 -m fourth_down --case-2025`. The regular launchers also work: click **AJ 2025 case** in the left navigation.

The new workspace shows your complete draft inventory, but the computed retrospective covers four running backs only. It includes real historical points, scoring controls, acquisition-date scenarios, an early/later time split, baseline comparisons, and a downloadable calculation report. Read `docs/CHAMPIONSHIP_2025.md` for the actual findings and limitations.

---

# Start Fourth Down

1. Extract the ZIP. Open the `fourth-down` folder.
2. **Windows:** double-click `Launch Fourth Down.bat`. **Mac / Linux:** run `python3 -m fourth_down` in a terminal in this folder. Python 3.10+ must be installed.
3. Keep the terminal open. The app opens at `http://127.0.0.1:8765`.

No pip install, Node.js, API keys, AWS account or Databricks account is needed for the local app.

## A useful first walkthrough

Begin with the default **2024 Week 13 / half-PPR** replay. The example roster projects approximately **96.6** starting points. Open **Waiver impact**: the model estimates that adding Alvin Kamara and dropping Davante Adams improves the legal starting lineup by about **1.6 projected points**, while adding Zach Ertz does not improve it. These are model estimates in a fictional roster, not real league advice or realized gains.

Return to **Lineup lab**, flag a starter out, and see the legal lineup change. **Player compare** shows the actual prior observations and projection formula. **Model audit** shows prediction errors—including misses—against two simple baselines. **Data & pipeline** identifies the source, checksum and cloud execution status.

## The boundaries

Bundled data: **14 selected players, 164 historical records, 2024 Weeks 3–16**. This is a reproducible portfolio replay, not live 2026 fantasy advice. No injury or actual league-ownership feed is connected. The repo includes an internet-dependent full-2024 data importer.

AWS and Databricks code are included, **not cloud-deployed**. The local application is complete without them.

For implementation, tests and fuller-data import: `README.md`.
For résumé wording: `docs/RESUME.md`.
For a code walkthrough: `docs/INTERVIEW_GUIDE.md`.
