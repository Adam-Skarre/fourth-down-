"use strict";
const D = window.FOURTH_DOWN_DATA,
  R = D.research,
  $ = (s) => document.querySelector(s),
  esc = (v) =>
    String(v ?? "").replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
const f = (v, n = 1) => (Number.isFinite(v) ? v.toFixed(n) : "—"),
  num = (v) => Number(v).toLocaleString("en-US"),
  methodNames = {
    ridge: "Ridge regression",
    blend: "Recency blend",
    history: "History average",
    last_game: "Last observed game",
  };
const S = {
  view: "overview",
  week: 13,
  scoring: "half",
  roster: new Set(D.meta.default_roster),
  out: new Set(),
  search: "",
  position: "ALL",
  metric: "mae",
  steady: false,
  compare: [],
  reveal: false,
};
try {
  const saved = JSON.parse(localStorage.getItem("fourth-down-portfolio-v2"));
  if (saved && Array.isArray(saved.roster)) {
    S.roster = new Set(saved.roster);
    S.out = new Set(saved.out || []);
  }
} catch {}
const pool = () => D.snapshots[`${S.week}-${S.scoring}`];
const selected = () =>
  pool().filter((p) => S.roster.has(p.id) && !S.out.has(p.id) && p.eligible);
const solve = () => FourthDownEngine.optimize(selected(), S.steady);
function save() {
  try {
    localStorage.setItem(
      "fourth-down-portfolio-v2",
      JSON.stringify({ roster: [...S.roster], out: [...S.out] }),
    );
  } catch {}
}
function download(data, name, type = "application/json") {
  const blob = new Blob(
      [typeof data === "string" ? data : JSON.stringify(data, null, 2)],
      { type },
    ),
    url = URL.createObjectURL(blob),
    a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function pill(text) {
  return `<span class="pill">${text}</span>`;
}
function sectionLabel(n, text) {
  return `<div class="section-label"><span>${n}</span>${text}</div>`;
}
function metric(value, label, note) {
  return `<div class="metric"><strong>${value}</strong><span>${label}</span><small>${note}</small></div>`;
}
function go(view) {
  location.hash = view;
}
function field() {
  return `<div class="field-art" aria-hidden="true"><div class="field-top"><span>THE NEXT PLAY</span><span>4TH & DECISION</span></div><svg viewBox="0 0 500 330"><defs><pattern id="field-grid" width="50" height="50" patternUnits="userSpaceOnUse"><path d="M50 0H0V50" fill="none" stroke="#ffffff" stroke-opacity=".075"/></pattern></defs><rect width="500" height="330" fill="url(#field-grid)"/><g stroke="#fff" stroke-opacity=".13"><path d="M50 40V290M150 40V290M250 40V290M350 40V290M450 40V290"/></g><g fill="#d2d9c5" opacity=".5" font-family="monospace" font-size="15"><text x="37" y="25">10</text><text x="137" y="25">20</text><text x="237" y="25">30</text><text x="337" y="25">40</text><text x="437" y="25">50</text></g><path d="M115 252V135Q115 105 145 105H352" stroke="#fa693d" stroke-width="4" fill="none"/><path d="M335 91L354 105L335 119" stroke="#fa693d" stroke-width="4" fill="none"/><path d="M188 252V181L291 78M260 252V193H395" stroke="#e8eedc" stroke-opacity=".65" stroke-width="2" stroke-dasharray="6 7" fill="none"/><g fill="#172f2d" stroke="#e8eedc" stroke-width="2"><circle cx="115" cy="252" r="12"/><circle cx="188" cy="252" r="12"/><circle cx="260" cy="252" r="12"/><circle cx="333" cy="252" r="12"/></g><circle cx="115" cy="252" r="5" fill="#ff7045"/><g stroke="#e8eedc" stroke-opacity=".5" stroke-width="2"><path d="M99 59l12 12m0-12l-12 12M203 134l12 12m0-12l-12 12M321 158l12 12m0-12l-12 12"/></g></svg><div class="field-bottom"><span><i></i>Forecast</span><span>Constraints</span><span>Decision ↗</span></div><div class="field-caption"><span>THE EDGE IS IN THE PROCESS.</span><strong>Every choice.<br>A reason behind it.</strong></div></div>`;
}
function overview() {
  const total = Object.values(R.cohorts).reduce((a, c) => a + c.records, 0);
  return `<section class="hero"><div class="hero-text"><div class="eyebrow"><span class="orange-dot"></span> FANTASY FOOTBALL / DECISION SCIENCE</div><h1>Better decisions.<br><em>Every down.</em></h1><p class="hero-description">A forecast is only the beginning. Turn historical player data into a legal lineup—and put every prediction to the test.</p><div class="hero-actions"><a class="button primary" href="#lineup">Explore the lineup lab <span>↗</span></a><a class="text-link" href="#research">See the evidence <span>→</span></a></div><div class="hero-footnote">Interactive 2024 replay <span>·</span> No signup <span>·</span> No live advice</div></div>${field()}</section>
<section class="metrics-strip" aria-label="Research scope">${metric(num(total), "Historical records", "Regular seasons 2022–2024")}${metric(num(R.overall.ridge.n), "Evaluation forecasts", "2024 · 420 eligible players")}${metric("3 seasons", "Chronological study", "Train → select → evaluate")}${metric("2 cloud tools", "AWS + Databricks", "Reference workflow executed")}</section>
<section class="section"><div class="section-heading"><div>${sectionLabel("01", "FROM FORECAST TO DECISION")}<h2>Good projections.<br>Better questions.</h2></div><p>Does a pickup improve your starting lineup?<br>Does a fitted model beat a simpler baseline?<br>Explore both sides of the decision.</p></div><div class="feature-grid"><a class="feature-card" href="#lineup"><div class="card-index">01 / INTERACTIVE LAB <span>↗</span></div><div class="mini-lineup"><span>QB</span><div></div><b>17.4</b><span>RB</span><div></div><b>19.5</b><span>FLEX</span><div></div><b>10.5</b></div><h3>The best seven. Within your rules.</h3><p>Select players, flag absences, and see an exact optimizer find your legal starting lineup. Then measure what one pickup changes.</p><span class="card-link">Make a decision →</span></a><a class="feature-card research-card" href="#research"><div class="card-index">02 / MODEL EVIDENCE <span>↗</span></div><div class="mini-benchmark"><span>Ridge regression <b>${f(R.overall.ridge.mae, 3)}</b></span><div style="--bar:78%"></div><span>History average <b>${f(R.overall.history.mae, 3)}</b></span><div style="--bar:78%"></div><small>2024 MAE · lower is better</small></div><h3>A fair test. Including the close calls.</h3><p>The fitted model reduces squared error, but barely changes average absolute error. The uncertainty interval tells the fuller story.</p><span class="card-link">Inspect the research →</span></a></div></section>
<section class="principles"><div>${sectionLabel("02", "BUILT TO BE INSPECTED")}<h2>Evidence over<br><em>assumptions.</em></h2></div><div class="principle"><span>01</span><h3>Respect the clock.</h3><p>Every feature uses earlier weeks. Model settings are selected in 2023 before the 2024 evaluation.</p></div><div class="principle"><span>02</span><h3>Keep the baseline.</h3><p>Compare every model on the same player-weeks. Added complexity has to earn its place.</p></div><div class="principle"><span>03</span><h3>Show the boundaries.</h3><p>Observed games, historical data, explicit assumptions. No invented outcomes or promises of wins.</p></div></section>
<section class="closing"><div><span class="eyebrow">A SMALL PRODUCT. A COMPLETE ANALYTICAL PROCESS.</span><h2>From raw records<br>to a reasoned call.</h2></div><a class="button dark" href="#data">Explore the build ↗</a></section>`;
}
function pageHeading(kicker, title, description) {
  return `<section class="page-heading"><div class="eyebrow">${kicker}</div><h1>${title}</h1><p>${description}</p></section>`;
}
function settings() {
  return `<div class="settings"><div><span class="eyebrow">HISTORICAL REPLAY</span><b>2024 season</b></div><label>Decision week<select id="week">${Array.from(
    { length: 13 },
    (_, i) => i + 4,
  )
    .map(
      (w) =>
        `<option value="${w}" ${w === S.week ? "selected" : ""}>Week ${w}</option>`,
    )
    .join(
      "",
    )}</select></label><div><span class="control-label">Scoring</span><div class="segmented" role="group" aria-label="Scoring format">${["standard", "half", "ppr"].map((k) => `<button data-scoring="${k}" aria-pressed="${S.scoring === k}" class="${S.scoring === k ? "active" : ""}">${{ standard: "Standard", half: "Half PPR", ppr: "PPR" }[k]}</button>`).join("")}</div></div><label class="check-option"><input id="steady" type="checkbox" ${S.steady ? "checked" : ""}> Prefer steadier players</label></div>`;
}
function rosterRows() {
  return (
    pool()
      .filter((p) =>
        (p.name + " " + p.position + " " + p.team)
          .toLowerCase()
          .includes(S.search.toLowerCase()),
      )
      .map(
        (p) =>
          `<tr class="${!p.eligible || S.out.has(p.id) ? "muted-row" : ""}"><td><input type="checkbox" aria-label="Roster ${esc(p.name)}" data-roster="${p.id}" ${S.roster.has(p.id) ? "checked" : ""}></td><td><b>${esc(p.name)}</b><small><span class="position ${p.position}">${p.position}</span> ${p.team} · ${p.n} prior games${!p.eligible ? " · " + esc(p.availability_note) : ""}</small></td><td class="numeric"><strong>${f(p.projection)}</strong></td><td class="numeric history-col">${f(p.recent_three)}</td><td><button class="flag ${S.out.has(p.id) ? "flagged" : ""}" aria-label="Flag ${esc(p.name)} unavailable" aria-pressed="${S.out.has(p.id)}" data-out="${p.id}">${S.out.has(p.id) ? "Out" : "Flag out"}</button></td></tr>`,
      )
      .join("") ||
    '<tr><td colspan="5" class="empty">No matching players. Try a name, team, or position.</td></tr>'
  );
}
function bestMove(current) {
  if (!current.feasible) return null;
  let best = null;
  for (const add of pool().filter(
    (p) => p.eligible && !S.roster.has(p.id) && !S.out.has(p.id),
  )) {
    for (const drop of pool()
      .filter((p) => S.roster.has(p.id))
      .sort(
        (a, b) => a.projection - b.projection || a.id.localeCompare(b.id),
      )) {
      const result = FourthDownEngine.optimize(
        [...selected().filter((p) => p.id !== drop.id), add],
        S.steady,
      );
      if (
        result.feasible &&
        (!best || result.objective - current.objective > best.gain + 1e-10)
      )
        best = {
          add,
          drop,
          gain: result.objective - current.objective,
          points: result.projection - current.projection,
        };
    }
  }
  return best;
}
function lineup() {
  const result = solve(),
    move = bestMove(result);
  return `${pageHeading("01 / THE LINEUP LAB", "Make your next <em>move.</em>", "Build a starting seven from the information available before kickoff. Change a constraint and watch the decision change.")}${settings()}<div class="context-note"><span class="orange-dot"></span> Demo pool: 14 players · 164 records · Using observations before Week ${S.week}. The lineup uses the fixed recency blend, not the research regression.</div><div class="lab-layout"><section class="panel roster-panel"><div class="panel-heading"><div><span class="eyebrow">YOUR PLAYER POOL</span><h2>Build the roster <span class="count">${S.roster.size}</span></h2></div><button class="text-button" data-action="reset">Reset demo ↺</button></div><div class="search-wrap"><span>⌕</span><input id="search" type="search" placeholder="Search player, team or position" aria-label="Search players" value="${esc(S.search)}"></div><div class="table-scroll"><table><thead><tr><th aria-label="Select player"></th><th>PLAYER</th><th class="numeric">PROJ.</th><th class="numeric history-col">LAST 3</th><th>STATUS</th></tr></thead><tbody id="roster-rows">${rosterRows()}</tbody></table></div><p class="panel-foot">Uncheck players to compare pickups. Flag out to exclude a player. Availability is not verified by an injury feed.</p></section><aside class="lineup-aside"><section class="lineup-card"><div class="lineup-card-head"><span class="eyebrow">YOUR STARTING SEVEN</span>${pill("EXACT OPTIMIZATION")}</div><div class="total-score">${f(result.projection)}<span>projected points</span></div><div class="lineup-list">${result.feasible ? result.lineup.map((p) => `<div><span class="slot">${p.slot}</span><span><b>${esc(p.name)}</b><small>${p.team} · ${p.position}</small></span><strong>${f(p.projection)}</strong></div>`).join("") : '<p class="empty">Select at least 1 QB, 2 RB, 2 WR, 1 TE and one additional RB/WR/TE with eligible history.</p>'}</div><button class="button primary full" data-action="export-lineup" ${result.feasible ? "" : "disabled"}>Export lineup ↗</button><p>One player, one slot. FLEX accepts RB, WR or TE.${S.steady ? " Objective subtracts 0.25 × recent standard deviation; the total above is unpenalized." : ""}</p></section><section class="move-card"><span class="eyebrow">THE MARGINAL GAIN</span><h3>What would a pickup change?</h3>${move ? `<div class="move-gain">${move.gain >= 0 ? "+" : ""}${f(move.gain)}<span>${S.steady ? "objective" : "projected"} points</span></div><p>Add <b>${esc(move.add.name)}</b><br>Drop <b>${esc(move.drop.name)}</b></p><button class="button outline full" data-add="${move.add.id}" data-drop="${move.drop.id}">Try this move →</button>` : "<p>Build a legal lineup and leave an eligible player outside your roster to compare a move.</p>"}<small>One-week scenario. No actual league transaction or rest-of-season valuation.</small></section></aside></div><section class="panel compare-panel"><div class="panel-heading"><div><span class="eyebrow">BEHIND THE PROJECTION</span><h2>Two players. One clearer call.</h2></div></div><div class="compare-controls">${[
    0, 1,
  ]
    .map(
      (n) =>
        `<label>Player ${n + 1}<select data-compare="${n}">${pool()
          .map(
            (p) =>
              `<option value="${p.id}" ${p.id === S.compare[n] ? "selected" : ""}>${esc(p.name)}</option>`,
          )
          .join("")}</select></label>`,
    )
    .join("")}</div><div id="comparison">${comparison()}</div></section>`;
}
function comparison() {
  let players = S.compare
    .map((id) => pool().find((p) => p.id === id))
    .filter(Boolean);
  if (players.length !== 2) players = pool().slice(0, 2);
  return `<div class="comparison-stats">${players.map((p) => `<div><span class="eyebrow">${esc(p.name)}</span><strong>${f(p.projection)}</strong><p>65% × ${f(p.recent_weighted, 2)} recent weighted mean<br>+ 35% × ${f(p.baseline, 2)} history average</p><small>Recent variability: ${f(p.volatility, 2)} points (historical SD)</small></div>`).join("")}</div>${lineChart(
    players.map((p) => ({
      name: p.name,
      points: p.history.map((g) => ({ x: g.week, y: g.points })),
    })),
    "Historical fantasy points",
  )}<p class="panel-foot">Prior observed games only. Lines connect recorded games; missing weeks are not zero. Variability is descriptive, not a prediction interval.</p>`;
}
function lineChart(series, description) {
  const points = series
    .flatMap((s) => s.points)
    .filter((p) => Number.isFinite(p.y));
  if (!points.length) return "";
  const W = 900,
    H = 250,
    L = 45,
    T = 20,
    B = 32,
    minX = Math.min(...points.map((p) => p.x)),
    maxX = Math.max(minX + 1, ...points.map((p) => p.x)),
    minY = Math.min(0, ...points.map((p) => p.y)),
    maxY = Math.max(1, ...points.map((p) => p.y)) * 1.12,
    x = (v) => L + ((v - minX) / (maxX - minX)) * (W - L - 20),
    y = (v) => H - B - ((v - minY) / (maxY - minY)) * (H - T - B);
  return `<div class="chart-wrap"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(description)}">${[
    0, 1, 2, 3, 4,
  ]
    .map((i) => {
      const v = minY + ((maxY - minY) * i) / 4;
      return `<path d="M${L} ${y(v)}H${W - 20}" stroke="#e5e5df"/><text x="${L - 10}" y="${y(v) + 4}" text-anchor="end">${f(v, 1)}</text>`;
    })
    .join("")}${[...new Set(points.map((p) => p.x))]
    .sort((a, b) => a - b)
    .filter((_, i) => i % 2 === 0)
    .map(
      (v) => `<text x="${x(v)}" y="${H - 7}" text-anchor="middle">W${v}</text>`,
    )
    .join("")}${series
    .map(
      (s, i) =>
        `<polyline fill="none" stroke="${i ? "#1d514c" : "#e66334"}" stroke-width="2.5" points="${s.points
          .filter((p) => Number.isFinite(p.y))
          .map((p) => `${x(p.x)},${y(p.y)}`)
          .join(" ")}"/>` +
        s.points
          .filter((p) => Number.isFinite(p.y))
          .map(
            (p) =>
              `<circle cx="${x(p.x)}" cy="${y(p.y)}" r="3.5" fill="${i ? "#1d514c" : "#e66334"}"><title>${esc(s.name)} · Week ${p.x}: ${f(p.y, 2)}</title></circle>`,
          )
          .join(""),
    )
    .join(
      "",
    )}</svg><div class="legend">${series.map((s, i) => `<span><i style="background:${i ? "#1d514c" : "#e66334"}"></i>${esc(s.name)}</span>`).join("")}</div></div>`;
}
function benchmark() {
  const scores = S.position === "ALL" ? R.overall : R.by_position[S.position],
    max = Math.max(...Object.values(scores).map((s) => s[S.metric]));
  return `<div class="benchmark-bars">${Object.entries(scores)
    .map(
      ([k, m]) =>
        `<div class="benchmark-row"><div><b>${methodNames[k]}</b>${k === "ridge" ? pill("FITTED") : ""}<strong>${f(m[S.metric], 3)}</strong></div><div class="bar-track"><div class="bar ${k === "ridge" ? "model" : ""}" style="width:${(m[S.metric] / max) * 100}%"></div></div></div>`,
    )
    .join(
      "",
    )}</div><p class="panel-foot">${num(scores.ridge.n)} identical player-weeks · ${S.metric === "mae" ? "Mean absolute error" : "Root mean squared error"} in fantasy points · Lower is better.</p>`;
}
function research() {
  return `${pageHeading("02 / THE RESEARCH", "Test the forecast.<br><em>Keep the evidence.</em>", "A reproducible comparison of fitted ridge regression and three simple forecasting rules, evaluated in chronological order.")}<div class="research-split">${[
    [
      "2022",
      "TRAIN",
      "3,442 examples",
      "Learn feature scaling and model weights.",
    ],
    [
      "2023",
      "SELECT",
      "3,583 examples",
      "Select regularization from five candidates by MAE.",
    ],
    [
      "2024",
      "EVALUATE",
      "3,503 examples",
      "Refit on 2022–23; score the selected configuration.",
    ],
  ]
    .map(
      ([y, l, n, d], i) =>
        `<div><span class="eyebrow">${l}</span><strong>${y}<span>${i < 2 ? "→" : "↗"}</span></strong><b>${n}</b><p>${d}</p></div>`,
    )
    .join(
      "",
    )}</div><div class="research-grid"><section class="panel"><div class="panel-heading"><div><span class="eyebrow">2024 / MODEL COMPARISON</span><h2>Does complexity help?</h2></div><button class="text-button" data-action="research-export">Export study ↗</button></div><div class="benchmark-controls"><div class="segmented" aria-label="Error metric">${["mae", "rmse"].map((k) => `<button data-metric="${k}" aria-pressed="${S.metric === k}" class="${S.metric === k ? "active" : ""}">${k.toUpperCase()}</button>`).join("")}</div><label>Position<select id="position">${["ALL", "QB", "RB", "WR", "TE"].map((p) => `<option ${p === S.position ? "selected" : ""} value="${p}">${p === "ALL" ? "All positions" : p}</option>`).join("")}</select></label></div><div id="benchmark">${benchmark()}</div></section><aside class="finding"><span class="eyebrow">THE FINDING / ALL POSITIONS</span><h2>Nearly tied.<br><em>That matters.</em></h2><p>Ridge MAE is <b>${f(R.overall.ridge.mae, 4)}</b> versus <b>${f(R.overall.history.mae, 4)}</b> for history average. Its RMSE is lower, but the MAE difference is not distinguishable from zero under this bootstrap.</p><div class="interval"><span>95% PLAYER-CLUSTER BOOTSTRAP</span><strong>−0.046 <i>to</i> +0.047</strong><small>MAE difference: ridge − history average</small><div class="interval-line"><i></i></div><div class="interval-labels"><span>Favors ridge</span><span>0</span><span>Favors baseline</span></div></div><p class="fine">1,000 resamples · 420 players · fixed seed. Conditional on these players; shared weekly shocks and model-selection uncertainty are not captured.</p></aside></div><section class="panel weekly-panel"><div class="panel-heading"><div><span class="eyebrow">STABILITY OVER TIME</span><h2>The average hides the weeks.</h2></div>${pill("2024 · HALF PPR")}</div>${lineChart(
    ["ridge", "history"].map((k) => ({
      name: methodNames[k] + " MAE",
      points: R.by_week.map((w) => ({ x: w.week, y: w[k].mae })),
    })),
    "2024 weekly mean absolute forecast error",
  )}<p class="panel-foot">Identical observed player-weeks within each week. Player availability and cohort size vary.</p></section><section class="methods-grid"><div>${sectionLabel("METHOD", "A REPRODUCIBLE EXPERIMENT")}<h2>Simple enough<br>to inspect.</h2><p>Nine features. An explicit training objective. Every baseline stays visible.</p><a class="text-link" href="https://github.com/Adam-Skarre/fourth-down-/blob/main/fourth_down/research.py">Read the implementation ↗</a></div><div class="method-details"><details open><summary>What does the model learn?</summary><p>Ridge regression predicts half-PPR fantasy points using the prior history mean, recency-weighted mean, last-three mean, last game, recent standard deviation, history count, and three position indicators. Features are standardized on training data only; the intercept is unpenalized.</p></details><details><summary>How is the model selected?</summary><p>Train on 2022 and choose λ from 0.1, 1, 10, 100, 1,000 using 2023 MAE. λ = ${R.selected_lambda} is selected. Refit that configuration on 2022–2023 before evaluating 2024. No 2024 outcomes enter scaling, coefficient fitting, or parameter selection.</p></details><details><summary>Which observations are evaluated?</summary><p>QB, RB, WR and TE player-weeks with a recorded outcome, at least three earlier games in the same season, and a prior observation within two weeks. Missing outcomes are excluded, never assigned zero. The task is conditional scoring, not injury or participation prediction.</p></details><details><summary>What can’t this study establish?</summary><p>This is retrospective research, not a preregistered prospective test. Statistics may contain later corrections. It does not measure live lineup gains, compare with professional projections, or establish that the fitted model is better on unseen future seasons. The interactive replay retains the original heuristic.</p></details></div></section>`;
}
function dataView() {
  return `${pageHeading("03 / DATA & BUILD", "Trace every step.<br><em>Trust what ran.</em>", "Public historical data, explicit contracts, reproducible calculations, and an honest record of the cloud workflow.")}<div class="pipeline">${[
    ["01", "Ingest", "nflverse CSV"],
    ["02", "Validate", "Types · keys · checksums"],
    ["03", "Learn", "Past-only features"],
    ["04", "Decide", "Constrained optimization"],
    ["05", "Evaluate", "Baselines · uncertainty"],
  ]
    .map(([n, t, d]) => `<div><span>${n}</span><h3>${t}</h3><p>${d}</p></div>`)
    .join(
      "",
    )}</div><div class="data-grid"><section class="panel"><div class="panel-heading"><div><span class="eyebrow">SOURCE / NFLVERSE</span><h2>Three seasons. Explicit provenance.</h2></div></div><table><thead><tr><th>SEASON</th><th>RECORDS</th><th>PLAYERS</th><th>SOURCE</th></tr></thead><tbody>${R.sources.sources.map((s) => `<tr><td><b>${s.season}</b></td><td>${num(s.records)}</td><td>${s.players}</td><td><a href="${esc(s.url)}">CSV ↗</a></td></tr>`).join("")}</tbody></table><div class="pad"><p>Regular-season QB/RB/WR/TE observations. Normalized fields retain player identity, team, week, opponent, fantasy points and receptions.</p><p class="fine">Retrieved October 6, 2026. Attribution: nflverse contributors, CC BY 4.0. SHA-256 hashes preserve the exact source and normalized files. Original publication vintages are not reconstructed.</p><button class="button outline" data-action="provenance">Download provenance ↗</button></div></section><section class="panel"><div class="panel-heading"><div><span class="eyebrow">CLOUD EXECUTION</span><h2>Working tools. Clear boundaries.</h2></div></div><div class="cloud-item"><span class="cloud-logo">S3</span><div><b>AWS S3</b><span class="status">UPLOAD VERIFIED</span><p>Four reference artifacts uploaded. Private bucket, versioning enabled, S3-managed encryption.</p></div></div><div class="cloud-item"><span class="cloud-logo db">DB</span><div><b>Databricks / PySpark / Delta</b><span class="status">USER-CONFIRMED PASS</span><p>164 source records and 14 forecasts verified against local calculations. Exported runtime evidence is pending.</p></div></div><p class="panel-foot">An explicit file-copy boundary connects the reference workflow. Direct S3 integration is not configured. The expanded three-season benchmark runs locally and has not been rerun in the cloud.</p></section></div><section class="quality"><div>${sectionLabel("ENGINEERING", "THE CHECKS BEHIND THE INTERFACE")}<h2>Designed to be<br>reproduced.</h2></div><div><h3>Data quality</h3><p>Duplicate keys, malformed values, invalid positions and non-finite numbers fail validation. Missing observations stay missing.</p><h3>Temporal integrity</h3><p>Forecasts use earlier games only. Mutation tests check that changing a future outcome cannot alter earlier features.</p></div><div><h3>Exact optimization</h3><p>Bitmask dynamic programming enforces seven legal slots and player uniqueness, checked against exhaustive search.</p><h3>Portable by design</h3><p>The browser uses Python-generated forecasts and a parity-tested optimizer. No credentials or cloud account are needed to explore this demo.</p></div></section><section class="source-cta"><div><span class="eyebrow">OPEN SOURCE / MIT APPLICATION CODE</span><h2>Inspect it. Run it. Question it.</h2><p>Source code, normalized data, row-level predictions, tests, and model documentation are included.</p></div><a class="button primary" href="https://github.com/Adam-Skarre/fourth-down-">Open GitHub ↗</a></section>`;
}
function render() {
  S.view = ["overview", "lineup", "research", "data"].includes(
    location.hash.slice(1),
  )
    ? location.hash.slice(1)
    : "overview";
  if (!S.compare.length)
    S.compare = pool()
      .slice(0, 2)
      .map((p) => p.id);
  $("#main").innerHTML = { overview, lineup, research, data: dataView }[
    S.view
  ]();
  document.querySelectorAll("[data-nav]").forEach((a) => {
    a.classList.toggle("active", a.dataset.nav === S.view);
    if (a.dataset.nav === S.view) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  document.title = `Fourth Down — ${{ overview: "Forecast. Decide. Verify.", lineup: "Lineup Lab", research: "The Research", data: "Data & Build" }[S.view]}`;
}
document.addEventListener("click", (e) => {
  const b = e.target.closest("button");
  if (!b) return;
  if (b.dataset.scoring) {
    S.scoring = b.dataset.scoring;
    render();
  }
  if (b.dataset.out) {
    S.out.has(b.dataset.out)
      ? S.out.delete(b.dataset.out)
      : S.out.add(b.dataset.out);
    save();
    render();
  }
  if (b.dataset.metric) {
    S.metric = b.dataset.metric;
    render();
  }
  if (b.dataset.add) {
    S.roster.delete(b.dataset.drop);
    S.roster.add(b.dataset.add);
    save();
    render();
  }
  if (b.dataset.action === "reset") {
    S.roster = new Set(D.meta.default_roster);
    S.out.clear();
    S.search = "";
    save();
    render();
  }
  if (b.dataset.action === "export-lineup") {
    download(
      {
        season: 2024,
        week: S.week,
        scoring: S.scoring,
        method: "Fixed 65/35 recency blend with exact lineup optimization",
        objective: S.steady
          ? "projection minus 0.25 x historical SD"
          : "projected points",
        ...solve(),
      },
      "fourth-down-lineup.json",
    );
  }
  if (b.dataset.action === "research-export")
    download(R, "fourth-down-research.json");
  if (b.dataset.action === "provenance")
    download(R.sources, "fourth-down-provenance.json");
});
document.addEventListener("input", (e) => {
  if (e.target.id === "search") {
    S.search = e.target.value;
    $("#roster-rows").innerHTML = rosterRows();
  }
});
document.addEventListener("change", (e) => {
  const t = e.target;
  if (t.dataset.roster) {
    t.checked
      ? S.roster.add(t.dataset.roster)
      : S.roster.delete(t.dataset.roster);
    save();
    render();
  }
  if (t.id === "week") {
    S.week = Number(t.value);
    render();
  }
  if (t.id === "steady") {
    S.steady = t.checked;
    render();
  }
  if (t.id === "position") {
    S.position = t.value;
    $("#benchmark").innerHTML = benchmark();
  }
  if (t.dataset.compare !== undefined) {
    S.compare[Number(t.dataset.compare)] = t.value;
    $("#comparison").innerHTML = comparison();
  }
});
window.addEventListener("hashchange", () => {
  render();
  window.scrollTo({ top: 0, behavior: "instant" });
  $("#main").focus({ preventScroll: true });
});
render();
