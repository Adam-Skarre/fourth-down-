/* Personal-season views. Source data and model outputs remain distinct. */
(function () {
  "use strict";

  const state = { week: 17, reveal: false, roster: "all", current: "all" };
  const bound = new WeakSet();
  const escape = (value) =>
    String(value ?? "").replace(/[&<>"']/g, (character) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[character]);
  const number = (value, digits = 1) => Number.isFinite(value) ? value.toFixed(digits) : "—";
  const signed = (value, digits = 1) => Number.isFinite(value) ? `${value > 0 ? "+" : value < 0 ? "−" : ""}${Math.abs(value).toFixed(digits)}` : "—";
  const data = () => window.FOURTH_DOWN_SEASONS;
  const readableDate = (value) => {
    const parsed = new Date(`${value}T12:00:00Z`);
    return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric", timeZone: "UTC" });
  };
  const teamName = (code) => data().teams[code] || code || "Team not recorded";
  const teamMark = (code) => `<span class="fd-season-teammark" aria-hidden="true">${escape(code)}</span>`;
  const sourceLink = (url, label) => url ? `<a href="${escape(url)}" target="_blank" rel="noopener">${escape(label)} <span aria-hidden="true">↗</span></a>` : "";

  function seasonNavigation(view) {
    const seasons = [
      { view: "season-2024", year: "2024", label: "Fourth place" },
      { view: "seasons", year: "2025", label: "League champion" },
      { view: "season-2026", year: "2026", label: "In testing" },
    ];
    return `<nav class="fd-season-nav" aria-label="Season case studies"><span class="fd-season-kicker">THE SEASON NOTEBOOK</span><div>${seasons.map((season) => `<a href="#${season.view}" class="${view === season.view ? "is-active" : ""}" ${view === season.view ? 'aria-current="page"' : ""}><b class="fd-season-nav-year">${season.year}</b><span class="fd-season-nav-label">${season.label}</span></a>`).join("")}</div></nav>`;
  }

  function keeperNote() {
    return `<div class="fd-season-keeper-note"><span class="fd-season-keeper-count">3</span><div><strong>A keeper league, season by season.</strong><p>Keep three players. The keeper trio cannot stay unchanged.</p></div><span class="fd-season-keeper-source">Keeper choices are not identified in these records.</span></div>`;
  }

  function firstSeasonView() {
    const first = data().firstSeason;
    if (!first) return '<section class="fd-season-hero"><div><h1>The first season.</h1><p>The 2024 roster is being added to the season notebook.</p></div></section>';
    const players = first.players || [];
    return `<section class="fd-season-hero fd-season-first-hero"><div class="fd-season-hero-copy"><span class="fd-season-kicker"><i></i> MY SEASONS / ${first.season}</span><h1>Where the<br><em>story started.</em></h1><p>Fourth place in the first season. The draft-board roster is the starting point for a notebook that continues through a championship and a new year of testing.</p><div class="fd-season-hero-actions"><button type="button" class="button primary" data-season-jump="fd-season-first-roster">See my 2024 team <span aria-hidden="true">↓</span></button><a class="fd-season-text-link" href="#seasons">Continue to 2025 <span aria-hidden="true">↗</span></a></div><div class="fd-season-hero-note">Fourth-place finish reported by Adam. Player entries transcribed from the supplied draft board.</div></div><div class="fd-season-record fd-season-first-record" aria-label="2024 first season: reported fourth-place finish"><div class="fd-season-record-top"><span>${escape(first.team_name || "Adam")} / ${first.season}</span><span>THE FIRST SEASON</span></div><div class="fd-season-record-rank">${escape(first.league_finish)}<sup>th</sup></div><div class="fd-season-record-title">A starting point.</div><div class="fd-season-record-bottom"><div><strong>${players.length} entries</strong><span>visible in Adam’s draft-board column</span></div><span class="fd-season-record-lines" aria-hidden="true"></span></div></div></section><section class="fd-season-first-roster" id="fd-season-first-roster" aria-labelledby="fd-season-first-title"><div class="fd-season-section-head"><div><span class="fd-season-kicker">01 / THE FIRST ROSTER</span><h2 id="fd-season-first-title">My 2024 team.<br>The first season.</h2></div><p>${players.length} visible draft-board entries, with the NFL teams recorded at the time. This is a draft roster, not a reconstruction of every weekly lineup.</p></div><div class="fd-season-roster-grid">${players.map((player, index) => `<article class="fd-season-roster-player">${teamMark(player.team)}<div class="fd-season-roster-player-copy"><h3>${escape(player.name)}</h3><p>${escape(player.team_name || teamName(player.team))}</p><div><span>Board entry ${String(player.row_order || index + 1).padStart(2, "0")}</span></div></div><span class="fd-season-position">${escape(["DST", "D/ST"].includes(player.position) ? "D/ST" : player.position)}</span></article>`).join("")}</div><p class="fd-season-small fd-season-roster-footnote">Only Adam’s column is transcribed. Names and NFL affiliations reflect the supplied 2024 draft board.</p></section><section class="fd-season-methods fd-season-first-methods" aria-labelledby="fd-season-first-method-title"><div><span class="fd-season-kicker">02 / THE LEAGUE FORMAT</span><h2 id="fd-season-first-method-title">Three keepers.<br>A changing roster.</h2><p>The league’s keeper rule makes each new season a fresh set of decisions about who to retain and where to rebuild.</p></div><div class="fd-season-method-content"><div class="fd-season-keeper-feature"><strong>3</strong><div><span>PLAYERS CAN BE KEPT</span><p>The keeper trio cannot stay unchanged.</p></div></div><details><summary>What is recorded about keepers?</summary><p>This rule is supplied by the league participant. The records do not identify the actual keeper selections or additional rotation mechanics. Players are not labeled as keepers based on roster overlap alone.</p></details><details><summary>How the seasons connect</summary><p>Adam reports finishing fourth in his first season in 2024. The 2025 case records a first-place finish, and the 2026 roster provides a current testing context. Those results describe the seasons; they do not establish a model-caused improvement.</p></details><details class="fd-season-first-source"><summary>Inspect the original draft board</summary><a href="${escape(first.source_asset)}" target="_blank" rel="noopener"><span>2024 draft board <span aria-hidden="true">↗</span></span><img src="${escape(first.source_asset)}" alt="Supplied 2024 draft board; the roster shown here is transcribed from Adam’s column" loading="lazy"></a><p>The roster above preserves the visible entries. The fourth-place finish is user-reported and is not inferred from the draft-board image.</p></details></div></section><section class="fd-season-next"><div><span class="fd-season-kicker">THE NEXT CHAPTER / 2025</span><h2>From fourth<br>to <em>first.</em></h2><p>Explore the championship roster and the retrospective backfield comparison.</p></div><a class="button dark" href="#seasons">Explore the 2025 case <span aria-hidden="true">↗</span></a></section>`;
  }

  function championshipPlayers() {
    const roster = data().championship.roster;
    return [
      ...roster.draft_roster.map((player) => ({ ...player, team: player.team_at_draft, origin: "Drafted" })),
      ...roster.reported_additions.map((player) => ({ ...player, origin: "Reported playoff addition" })),
    ];
  }

  function championshipHero() {
    const roster = data().championship.roster;
    const finish = roster.observed_team_result;
    return `<section class="fd-season-hero"><div class="fd-season-hero-copy"><span class="fd-season-kicker"><i></i> MY SEASONS / 2025</span><h1>I won my league<br><em>in 2025.</em></h1><p>This is my 2025 championship team. Explore the players and their NFL teams, then follow a retrospective comparison of one backfield decision.</p><div class="fd-season-hero-actions"><button type="button" class="button primary" data-season-jump="fd-season-championship-roster">See my 2025 team <span aria-hidden="true">↓</span></button><button type="button" class="button outline" data-season-jump="fd-season-decision">Explore the decision <span aria-hidden="true">↓</span></button></div><div class="fd-season-hero-note">An observed championship finish. A separate, retrospective model analysis.</div></div><div class="fd-season-record" aria-label="2025 recorded league finish: first place, record ${escape(finish.listed_record)}"><div class="fd-season-record-top"><span>AJ / 2025</span><span>THE SEASON RESULT</span></div><div class="fd-season-record-rank">${escape(finish.finish)}<sup>st</sup></div><div class="fd-season-record-title">League champion</div><div class="fd-season-record-bottom"><div><strong>${escape(finish.listed_record.replace(/-/g, "–"))}</strong><span>record shown in league history</span></div><span class="fd-season-record-lines" aria-hidden="true"></span></div></div></section>`;
  }

  function decisionPanel() {
    const report = data().championship.report;
    const weeks = report.pair_case.weeks;
    const selected = weeks.find((week) => week.week === state.week) || weeks[weeks.length - 1];
    const choice = selected.decisions.original;
    const winner = selected.players.find((player) => player.id === choice.id);
    const other = selected.players.find((player) => player.id !== choice.id);
    const forecastGap = winner.original - other.original;
    const actualGap = winner.actual - other.actual;
    const rosterById = Object.fromEntries(championshipPlayers().map((player) => [player.id, player]));
    const successCount = weeks.filter((week) => {
      const pick = week.players.find((player) => player.id === week.decisions.original.id);
      return pick.actual === Math.max(...week.players.map((player) => player.actual));
    }).length;
    return `<section class="fd-season-decision" id="fd-season-decision" aria-labelledby="fd-season-decision-title"><div class="fd-season-section-head"><div><span class="fd-season-kicker">02 / THE DECISION</span><h2 id="fd-season-decision-title">One slot.<br>Two possibilities.</h2></div><p>Compare the original forecast for a hypothetical RB/FLEX slot. Then reveal what happened.</p></div><div class="fd-season-decision-controls"><div class="fd-season-week-controls" role="group" aria-label="Comparison week">${weeks.map((week) => `<button type="button" data-season-week="${week.week}" aria-pressed="${week.week === selected.week}" class="${week.week === selected.week ? "is-active" : ""}">Week ${week.week}</button>`).join("")}</div><span class="fd-season-tag">2025 REPLAY <b>FULL PPR</b></span><button type="button" class="fd-season-reveal-button" data-season-reveal aria-expanded="${state.reveal}" aria-controls="fd-season-outcomes">${state.reveal ? "Hide outcomes" : "Reveal outcomes"} <span aria-hidden="true">${state.reveal ? "−" : "+"}</span></button></div><div class="fd-season-decision-body"><div class="fd-season-player-comparison">${selected.players.map((player) => {
      const rosterPlayer = rosterById[player.id];
      const picked = player.id === choice.id;
      return `<article class="fd-season-player ${picked ? "is-picked" : ""}"><div class="fd-season-player-top">${teamMark(rosterPlayer.team)}<span class="fd-season-choice-label">${picked ? "MODEL’S PICK" : "THE ALTERNATIVE"}</span></div><h3>${escape(player.name)}</h3><p class="fd-season-player-team">${escape(teamName(rosterPlayer.team))} <span>RB</span></p><div class="fd-season-player-numbers"><div><span>Forecast</span><strong>${number(player.original, 2)}</strong><small>before Week ${selected.week}</small></div><div class="fd-season-actual ${state.reveal ? "is-revealed" : ""}"><span>Actual points</span><strong>${state.reveal ? number(player.actual) : '<span aria-label="Outcome hidden">—</span>'}</strong><small>${state.reveal ? "full-PPR outcome" : "reveal to compare"}</small></div></div><div class="fd-season-player-history"><span>${player.prior_games} prior appearances</span><span>History through W${player.history_end}</span></div></article>`;
    }).join("")}</div><aside class="fd-season-insight ${state.reveal && actualGap < 0 ? "is-miss" : ""}" id="fd-season-outcomes" aria-live="polite"><span class="fd-season-kicker">${state.reveal ? "THE OBSERVED DIFFERENCE" : "THE FORECAST DIFFERENCE"}</span><div class="fd-season-insight-number">${state.reveal ? signed(actualGap) : signed(forecastGap, 2)}<span>points</span></div><h3>${state.reveal ? (actualGap >= 0 ? "The pick scored higher." : "The other player scored higher.") : "The model leans toward " + escape(winner.name.split(" ").slice(-1)[0]) + "."}</h3><p>${state.reveal ? `${escape(winner.name)} scored ${number(winner.actual)}; ${escape(other.name)} scored ${number(other.actual)}. The forecast difference was ${number(forecastGap, 2)} points.` : `The fixed recency blend projects ${number(winner.original, 2)} for ${escape(winner.name)} and ${number(other.original, 2)} for ${escape(other.name)}.`}</p><div class="fd-season-insight-note">${state.reveal ? "This is a difference between two players, not a verified gain in the actual league lineup." : "The forecast uses earlier games only. The actual outcome does not enter this calculation."}</div></aside></div><div class="fd-season-case-note"><span aria-hidden="true">i</span><p>Case assumptions: full PPR, Stevenson available from Week 15, and one interchangeable RB/FLEX slot. Actual league scoring, acquisition timing and weekly lineups are unconfirmed.</p></div><div class="fd-season-all-weeks"><div class="fd-season-all-weeks-head"><h3>Keep the whole comparison in view.</h3><span>${state.reveal ? `${successCount} of ${weeks.length} higher-scoring selections` : `${weeks.length} weeks · the same rule`}</span></div><div class="fd-season-table-scroll" tabindex="0" role="region" aria-label="All three comparison weeks"><table><thead><tr><th scope="col">Week</th><th scope="col">Montgomery forecast</th><th scope="col">Stevenson forecast</th><th scope="col">Model pick</th><th scope="col">Outcome</th></tr></thead><tbody>${weeks.map((week) => {
      const montgomery = week.players.find((player) => player.id === "montgomery");
      const stevenson = week.players.find((player) => player.id === "stevenson");
      const pick = week.players.find((player) => player.id === week.decisions.original.id);
      const matched = pick.actual === Math.max(montgomery.actual, stevenson.actual);
      return `<tr class="${week.week === selected.week ? "is-selected" : ""}"><th scope="row">${week.week}</th><td>${number(montgomery.original, 2)}${state.reveal ? `<small>${number(montgomery.actual)} actual</small>` : ""}</td><td>${number(stevenson.original, 2)}${state.reveal ? `<small>${number(stevenson.actual)} actual</small>` : ""}</td><td>${escape(pick.name.split(" ").slice(-1)[0])}</td><td>${state.reveal ? `<span class="fd-season-result ${matched ? "is-match" : "is-miss"}">${matched ? "Higher scorer" : "Lower scorer"}</span>` : '<span class="fd-season-muted">Hidden</span>'}</td></tr>`;
    }).join("")}</tbody></table></div><p class="fd-season-small">The original 65/35 rule is shown throughout. Outcomes are a retrospective check, not a record of model-guided decisions or proof of a championship advantage.</p></div></section>`;
  }

  function championshipRoster() {
    const allPlayers = championshipPlayers();
    const analyzed = allPlayers.filter((player) => player.statistical_data_bundled);
    const players = state.roster === "analyzed" ? analyzed : allPlayers;
    return `<section class="fd-season-roster-section" id="fd-season-championship-roster" aria-labelledby="fd-season-roster-title"><div class="fd-season-section-head"><div><span class="fd-season-kicker">01 / MY 2025 TEAM</span><h2 id="fd-season-roster-title">My 2025<br>championship team.</h2></div><p>17 drafted entries and one reported playoff addition. NFL teams are the affiliations recorded for 2025.</p></div><div class="fd-season-roster-toolbar"><div class="fd-season-filters" role="group" aria-label="2025 roster scope"><button type="button" data-season-champ-filter="all" aria-pressed="${state.roster === "all"}" class="${state.roster === "all" ? "is-active" : ""}">Full roster <span>${allPlayers.length}</span></button><button type="button" data-season-champ-filter="analyzed" aria-pressed="${state.roster === "analyzed"}" class="${state.roster === "analyzed" ? "is-active" : ""}">Analyzed backfield <span>${analyzed.length}</span></button></div><span class="fd-season-small">Roster inventory · not a reconstruction of every weekly lineup</span></div><div class="fd-season-roster-grid">${players.map((player) => `<article class="fd-season-roster-player">${teamMark(player.team)}<div class="fd-season-roster-player-copy"><h3>${escape(player.name)}</h3><p>${escape(teamName(player.team))}</p><div><span>${escape(player.origin)}</span>${player.statistical_data_bundled ? '<span class="fd-season-analysis-tag">In the analysis</span>' : ""}</div></div><span class="fd-season-position">${escape(player.position === "DST" ? "D/ST" : player.position)}</span></article>`).join("")}</div><p class="fd-season-small fd-season-roster-footnote">The statistical case covers Achane, Montgomery, Harvey and Stevenson. Stevenson’s exact pickup date and the dropped player are not recorded.</p></section>`;
  }

  function championshipMethods() {
    const sources = data().sources;
    return `<section class="fd-season-methods" aria-labelledby="fd-season-method-title"><div><span class="fd-season-kicker">03 / HOW IT WORKS</span><h2 id="fd-season-method-title">A forecast you<br>can follow.</h2><p>Begin with the earlier games. Make the weighting visible. Check the result afterward.</p></div><div class="fd-season-method-content"><div class="fd-season-formula" aria-label="Forecast equals 65 percent weighted recent average plus 35 percent all-prior-games average"><div><strong>65<span>%</span></strong><p>Weighted recent average</p></div><span aria-hidden="true">+</span><div><strong>35<span>%</span></strong><p>All-prior-games average</p></div></div><details><summary>What goes into the forecast?</summary><p>The recent component uses the last six observed games, with weights 1, 0.75, 0.75² and so on from newest to oldest. Both averages exclude the decision week and later weeks. At least three prior appearances are required; missing appearances are not scored as zero.</p><p>This is the original fixed heuristic. The separately fitted blend and the broader ridge-regression study are different comparisons.</p></details><details><summary>What does the championship establish?</summary><p>The supplied league-history screenshot records a first-place finish and a 9–5–0 record. The later model replay makes selected decisions inspectable. It does not establish that the software was used during the season or caused the championship.</p><p>The replay covers four running backs, with assumed scoring and availability. Actual weekly starters, opponents and complete transactions are not supplied.</p></details><div class="fd-season-source-links">${sourceLink(sources.roster, "Roster record")}${sourceLink(sources.report, "Full comparison data")}${sourceLink(sources.method, "Case methodology")}</div></div></section><section class="fd-season-next"><div><span class="fd-season-kicker">THE NEXT SEASON</span><h2>A new roster.<br><em>More to learn.</em></h2><p>Explore AJ’s 2026 team and the Week 7 snapshot being used for continued testing.</p></div><a class="button dark" href="#season-2026">See the 2026 roster <span aria-hidden="true">↗</span></a></section>`;
  }

  function currentHero() {
    const current = data().current;
    const count = (section) => current.players.filter((player) => player.section === section).length;
    return `<section class="fd-season-hero fd-season-current-hero"><div class="fd-season-hero-copy"><span class="fd-season-kicker"><i></i> MY SEASONS / ${current.season}</span><h1>The next test<br>is <em>this roster.</em></h1><p>A new season of lineup decisions. This is AJ’s Week ${current.week} roster snapshot, the starting point for continued evaluation.</p><div class="fd-season-hero-actions"><button type="button" class="button primary" data-season-jump="fd-season-current-roster">See my 2026 team <span aria-hidden="true">↓</span></button><span class="fd-season-testing-label"><i></i> IN TESTING</span></div><div class="fd-season-hero-note">Manual snapshot · supplied ${escape(readableDate(current.provided_on))} · no automatic refresh</div></div><div class="fd-season-record fd-season-current-record"><div class="fd-season-record-top"><span>AJ / ${current.season}</span><span>WEEK ${current.week} SNAPSHOT</span></div><div class="fd-season-current-week">${String(current.week).padStart(2, "0")}<span>WEEK</span></div><div class="fd-season-record-title">A roster to evaluate.</div><div class="fd-season-current-counts"><div><strong>${count("starter")}</strong><span>starter slots</span></div><div><strong>${count("bench")}</strong><span>bench entries</span></div><div><strong>${count("injured_reserve")}</strong><span>IR slot</span></div></div></div></section>`;
  }

  function currentPlayer(player) {
    const status = { final: "Final", in_progress: "In progress", bye: "Bye" }[player.game_status] || "As shown";
    return `<article class="fd-season-current-player"><div class="fd-season-current-player-head">${teamMark(player.team)}<div><h3>${escape(player.name)}</h3><p>${escape(player.team_name || teamName(player.team))}</p></div><span class="fd-season-position">${escape(player.position)}</span></div><div class="fd-season-current-player-meta"><span><b>${escape(player.slot)}</b> roster slot</span><span class="fd-season-game-status ${player.game_status === "in_progress" ? "is-progress" : player.game_status === "bye" ? "is-bye" : ""}">${player.game_status === "in_progress" ? '<i aria-hidden="true"></i>' : ""}${status}</span>${player.injury_tag ? `<span class="fd-season-injury">${escape(player.injury_tag)} designation</span>` : ""}</div><div class="fd-season-current-player-scores"><div><span>APP SCORE</span><strong>${number(player.displayed_score)}</strong></div><div><span>APP PROJECTION</span><strong>${number(player.displayed_projection, 2)}</strong></div></div>${player.game_status === "bye" ? '<p class="fd-season-current-player-note">No numerical score or projection shown.</p>' : player.game_status === "in_progress" ? '<p class="fd-season-current-player-note">Partial score at screenshot capture.</p>' : ""}</article>`;
  }

  function currentRoster() {
    const current = data().current;
    const categories = [
      { key: "starter", label: "Starters", title: "The starting lineup", description: "8 offensive slots, plus defense/special teams and kicker." },
      { key: "bench", label: "Bench", title: "The bench", description: "The alternatives available in this roster snapshot." },
      { key: "injured_reserve", label: "IR slot", title: "Injured reserve", description: "A separate roster slot, distinct from an injury designation." },
    ];
    const counts = Object.fromEntries(categories.map((category) => [category.key, current.players.filter((player) => player.section === category.key).length]));
    const filters = [{ key: "all", label: "All players", count: current.players.length }, ...categories.map((category) => ({ ...category, count: counts[category.key] }))];
    return `<section class="fd-season-current-roster" id="fd-season-current-roster" aria-labelledby="fd-season-current-title"><div class="fd-season-section-head"><div><span class="fd-season-kicker">01 / THE CURRENT TEAM</span><h2 id="fd-season-current-title">My ${current.season} team.<br>Currently testing.</h2></div><p>NFL teams, fantasy slots and values transcribed from the supplied Week ${current.week} screenshots.</p></div><div class="fd-season-current-context"><span class="fd-season-context-icon" aria-hidden="true">i</span><p><strong>These are fantasy-app values, not Fourth Down forecasts.</strong> CeeDee Lamb’s game is in progress at capture; Cam Little is on a bye. No final weekly result is inferred.</p></div><div class="fd-season-filters fd-season-current-filters" role="group" aria-label="2026 roster section">${filters.map((filter) => `<button type="button" data-season-current-filter="${filter.key}" class="${state.current === filter.key ? "is-active" : ""}" aria-pressed="${state.current === filter.key}">${escape(filter.label)} <span>${filter.count}</span></button>`).join("")}</div><div class="fd-season-current-groups">${categories.filter((category) => state.current === "all" || category.key === state.current).map((category) => `<section class="fd-season-current-group" aria-labelledby="fd-season-group-${category.key}"><div class="fd-season-group-head"><h3 id="fd-season-group-${category.key}">${category.title} <span>${counts[category.key]}</span></h3><p>${category.description}</p></div><div class="fd-season-current-grid">${current.players.filter((player) => player.section === category.key).map(currentPlayer).join("")}</div></section>`).join("")}</div></section>`;
  }

  function currentMethods() {
    const current = data().current;
    return `<section class="fd-season-snapshot-notes"><div><span class="fd-season-kicker">02 / THE TESTING CONTEXT</span><h2>A clear record<br>to build on.</h2><p>The roster is the input. Evaluating a decision requires preserving the forecast, the choice and the eventual outcome separately.</p></div><div><details open><summary>How to read this snapshot</summary><p>“App score” and “App projection” reproduce the visible fantasy-app values. They are not generated by Fourth Down, and this page is not a live feed. The screenshots do not establish the league’s scoring rules.</p><p>The user identifies this as the 2026 season. Week 7 and team AJ are visible in the supplied images; the year is supplied by that context.</p></details><details><summary>Availability and roster slots</summary><p>Jayden Reed is in a bench slot with an IR injury designation. Jalen McMillan is in the IR roster slot and also has an IR designation. Cam Little’s bye is preserved as an unavailable numerical value, not a recorded zero.</p><p>These labels reflect the screenshots, not a current injury-status service. This ten-slot starting roster is separate from the seven-slot 2024 lineup demonstration.</p></details><details><summary>What is being evaluated next</summary><p>This roster provides a personal testing context for start/sit choices, available alternatives and forecast accuracy. Fourth Down model forecasts and verified decision outcomes have not been attached to this snapshot.</p></details><details class="fd-season-screenshot-details"><summary>Inspect the supplied screenshots</summary><div class="fd-season-screenshot-grid">${(current.screenshots || []).map((screenshot) => `<a href="${escape(screenshot.path)}" target="_blank" rel="noopener"><span>${escape(screenshot.label)} <span aria-hidden="true">↗</span></span><img src="${escape(screenshot.path)}" alt="${escape(screenshot.label)} supplied for AJ’s Week 7 roster" loading="lazy" width="945" height="2048"></a>`).join("")}</div><p>Original supplied images. Scores and status remain as shown at capture.</p></details></div></section><section class="fd-season-next fd-season-next-compact"><div><span class="fd-season-kicker">LOOK BACK AT THE METHOD</span><h2>See a decision<br><em>from both sides.</em></h2></div><a class="button dark" href="#seasons">Explore the 2025 case <span aria-hidden="true">↗</span></a></section>`;
  }

  function render(view) {
    if (!data()) return '<section class="fd-season-page"><p>Season data is unavailable. Reload the page to try again.</p></section>';
    const selected = ["season-2024", "seasons", "season-2026"].includes(view) ? view : "seasons";
    const content = selected === "season-2024" ? firstSeasonView() : selected === "season-2026" ? currentHero() + currentRoster() + currentMethods() : championshipHero() + championshipRoster() + decisionPanel() + championshipMethods();
    return `<div class="fd-season-page" data-season-view="${selected}">${seasonNavigation(selected)}${keeperNote()}${content}</div>`;
  }

  function bind(container) {
    if (bound.has(container)) return;
    bound.add(container);
    container.addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (!button || !container.contains(button)) return;
      const page = container.querySelector("[data-season-view]");
      if (!page) return;
      const view = page.dataset.seasonView;
      let focus = null;
      if (button.dataset.seasonJump) {
        const target = container.querySelector(`#${button.dataset.seasonJump}`);
        if (target) target.scrollIntoView({ behavior: window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth", block: "start" });
        return;
      }
      if (button.dataset.seasonWeek !== undefined) {
        const week = Number(button.dataset.seasonWeek);
        if (!data().championship.report.pair_case.weeks.some((entry) => entry.week === week)) return;
        state.week = week;
        focus = `[data-season-week="${week}"]`;
      } else if (button.hasAttribute("data-season-reveal")) {
        state.reveal = !state.reveal;
        focus = "[data-season-reveal]";
      } else if (button.dataset.seasonChampFilter !== undefined && ["all", "analyzed"].includes(button.dataset.seasonChampFilter)) {
        state.roster = button.dataset.seasonChampFilter;
        focus = `[data-season-champ-filter="${state.roster}"]`;
      } else if (button.dataset.seasonCurrentFilter !== undefined && ["all", "starter", "bench", "injured_reserve"].includes(button.dataset.seasonCurrentFilter)) {
        state.current = button.dataset.seasonCurrentFilter;
        focus = `[data-season-current-filter="${state.current}"]`;
      }
      if (focus) {
        container.innerHTML = render(view);
        const nextButton = container.querySelector(focus);
        if (nextButton) nextButton.focus({ preventScroll: true });
      }
    });
  }

  window.FourthDownSeasons = Object.freeze({ render, bind });
})();
