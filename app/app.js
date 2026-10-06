/* Fourth Down. No CDN, framework or build step. All decisions come from the Python API. */
'use strict';
const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = (n, digits = 1) => typeof n === 'number' && Number.isFinite(n) ? n.toFixed(digits) : '—';
const signed = n => `${n > 0 ? '+' : ''}${fmt(n)}`;
const label = key => ({half: 'Half PPR', ppr: 'PPR', standard: 'Standard'}[key]);
const state = {meta:null, season:2024, week:13, scoring:'half', risk:'points', roster:new Set(), exclude:new Set(), pool:[], solved:null, moves:null, audit:null, view:'lineup', search:'', compare:[], revision:0, request:null};
const titles = {
 lineup:['LINEUP LAB','FANTASY FOOTBALL, WITH A REASON.','A better call.<br><span>Before kickoff.</span>','Select your roster. Compare the trade-offs.<br>Build a legal starting seven from the information available then.'],
 waivers:['WAIVER IMPACT','A PICKUP SHOULD CHANGE SOMETHING.','A better player.<br><span>Or a better lineup?</span>','Measure what one add and one drop change in your starting seven.<br>A high rank alone is not a reason to make a move.'],
 compare:['PLAYER COMPARE','THE REASON BEHIND THE NUMBER.','Two players.<br><span>One clearer decision.</span>','Compare the records behind each projection.<br>See recent form, historical variability, and the exact calculation.'],
 audit:['MODEL AUDIT','SHOW THE MISSES, TOO.','Projections need<br><span>a scorecard.</span>','Walk forward one week at a time, without using target-week results.<br>Compare the model with two simpler baselines on the same observations.'],
 pipeline:['DATA & PIPELINE','SMALL DATA. COMPLETE ENGINEERING.','Trace the input.<br><span>Trust the process.</span>','Inspect the data contract, cutoff logic, and execution status.<br>Local code runs now. Cloud extensions are a separate deployment.']
};
async function api(path, body, signal) {
 const response = await fetch(path, {method: body === undefined ? 'GET':'POST', headers: body === undefined ? {} : {'Content-Type':'application/json'}, body:body === undefined ? undefined : JSON.stringify(body), signal});
 const content = await response.json(); if (!response.ok) throw new Error(content.error || `Request failed (${response.status}).`); return content;
}
const payload = () => ({season:state.season,week:state.week,scoring:state.scoring,risk:state.risk,roster:[...state.roster],exclude:[...state.exclude]});
function save() {try {localStorage.setItem('fourth-down-v1',JSON.stringify({...payload(),sha:state.meta.sha256}));} catch (_) { /* Private browsing may disallow storage. */ }}
function toast(message) {$('#toast').textContent=message;$('#toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('#toast').hidden=true,3300);}
function error(message) {$('#error').textContent=message;$('#error').hidden=!message;}
function download(text, filename, type='text/csv;charset=utf-8') {const url=URL.createObjectURL(new Blob([text],{type}));const a=document.createElement('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),3000);}
function csv(rows) {return rows.map(row=>row.map(value=>{let v=String(value??'');if (typeof value==='string' && /^[=+@\-\t\r]/.test(v)) v="'"+v;return '"'+v.replaceAll('"','""')+'"';}).join(',')).join('\r\n');}
function playerTag(p) {return `<span class="pos ${esc(p.position)}">${esc(p.position)}</span>`;}
function stat(labelText,value,detail,featured=false) {return `<div class="stat ${featured?'featured':''}"><div class="stat-label">${labelText}</div><div class="stat-value">${value}</div><div class="stat-detail">${detail}</div></div>`;}
function panelHeading(tag,title,extra='') {return `<div class="panel-head"><div><span class="panel-tag">${tag}</span><h2>${title}</h2></div>${extra}</div>`;}
function selectionControls() {
 const bounds=state.meta.bounds[state.season];
 $('#season').innerHTML=state.meta.seasons.map(s=>`<option value="${s}">${s}</option>`).join('');$('#season').value=state.season;
 const start=bounds[0]+1, end=bounds[1];
 if(state.week<start||state.week>end)state.week=Math.min(Math.max(13,start),end);
 $('#week').innerHTML=Array.from({length:Math.max(0,end-start+1)},(_,i)=>`<option value="${start+i}">Week ${start+i}</option>`).join('');$('#week').value=state.week;
 $('#risk').value=state.risk;$$('[data-scoring]').forEach(b=>{b.classList.toggle('selected',b.dataset.scoring===state.scoring);b.setAttribute('aria-pressed',String(b.dataset.scoring===state.scoring));});
}
function header() {
 const [crumb,eyebrow,title,sub]=titles[state.view];$('#breadcrumb').textContent=crumb;$('#eyebrow').textContent=eyebrow;$('#heading').innerHTML=title;$('#subheading').innerHTML=sub;
 $('#heroWeek').textContent=state.week;$('#yearBadge').textContent=state.season;$('#cutoffLabel').textContent=`Using records before Week ${state.week}`;
 $('#footerData').textContent=`${state.meta.players} players · ${state.meta.records} source rows · historical, not live`;
 $$('#nav button').forEach(b=>{b.classList.toggle('active',b.dataset.view===state.view);b.setAttribute('aria-current',b.dataset.view===state.view?'page':'false');});
}
async function refresh() {
 const revision=++state.revision;state.request?.abort();state.request=new AbortController();const signal=state.request.signal;
 error('');$('#busy').hidden=false;selectionControls();header();
 try {
  const snap=await api(`/api/snapshot?season=${state.season}&week=${state.week}&scoring=${state.scoring}`,undefined,signal);
  if(revision!==state.revision)return;state.pool=snap.players;
  const known=new Set(state.pool.map(p=>p.id));state.roster=new Set([...state.roster].filter(id=>known.has(id)));state.exclude=new Set([...state.exclude].filter(id=>known.has(id)));
  const solved=await api('/api/solve',payload(),signal);if(revision!==state.revision)return;state.solved=solved;
  state.moves=null;state.audit=null;
  if(state.view==='waivers'){const moves=await api('/api/waivers',payload(),signal);if(revision!==state.revision)return;state.moves=moves;}
  if(state.view==='audit'){const audit=await api(`/api/audit?season=${state.season}&scoring=${state.scoring}`,undefined,signal);if(revision!==state.revision)return;state.audit=audit;}
  if(revision!==state.revision)return;save();render();
 } catch(e) {if(e.name!=='AbortError'){error(e.message);$('#view').innerHTML='<div class="empty-state">The calculation did not complete. Review the message above and change a setting to retry.</div>';}}
 finally {if(revision===state.revision)$('#busy').hidden=true;}
}
function render() {header();({lineup:renderLineup,waivers:renderWaivers,compare:renderCompare,audit:renderAudit,pipeline:renderPipeline}[state.view])();}
function rosterRows() {
 const query=state.search.toLowerCase().trim();
 return state.pool.filter(p=>(p.name+' '+p.position+' '+p.team).toLowerCase().includes(query)).map(p=>{
  const out=state.exclude.has(p.id),unusable=out||!p.eligible;
  return `<tr class="${unusable?'excluded':''}"><td><input class="pickbox" type="checkbox" data-roster="${esc(p.id)}" ${state.roster.has(p.id)?'checked':''} aria-label="Roster ${esc(p.name)}"></td><td><div class="player-name">${esc(p.name)}</div><div class="player-meta">${playerTag(p)} <span>${esc(p.team)} · ${p.n} prior games</span></div>${!p.eligible?`<div class="status-note">${esc(p.availability_note)}</div>`:''}</td><td class="number projected">${fmt(p.projection)}</td><td class="number recent-column">${fmt(p.recent_three)}</td><td class="number"><button class="availability-button ${out?'flagged':''}" data-exclude="${esc(p.id)}" aria-pressed="${out}" aria-label="${out?'Clear':'Set'} unavailable flag for ${esc(p.name)}">${out?'OUT':'Flag out'}</button></td></tr>`;
 }).join('') || '<tr><td colspan="5" class="empty-state">No player matches that search.</td></tr>';
}
function renderLineup() {
 const solved=state.solved, rosterEligible=state.pool.filter(p=>state.roster.has(p.id)&&p.eligible&&!state.exclude.has(p.id)).length;
 const lineup=solved.feasible?solved.lineup.map(p=>`<div class="lineup-row"><span class="slot-label">${esc(p.slot)}</span><div class="lineup-player">${esc(p.name)}<small>${esc(p.team)} · ${esc(p.position)}</small></div><strong class="lineup-score">${fmt(p.projection)}</strong></div>`).join(''):`<div class="empty-state"><h3>Not enough eligible players.</h3><p>${esc(solved.reason)}</p></div>`;
 $('#view').innerHTML=`<div class="stats-grid">${stat('PROJECTED STARTING TOTAL',fmt(solved.projection),'Fantasy points · not a guaranteed result',true)}${stat('YOUR ROSTER',`${state.roster.size}<span class="stat-route"> / 24</span>`,`${rosterEligible} eligible · seven starting slots`)}${stat('INFORMATION CUTOFF',`W${state.week-1}`,`No Week ${state.week} outcomes in the calculation`)}</div>
 <div class="grid-two"><section class="panel">${panelHeading('01 / BUILD YOUR POOL','Your roster',`<button class="link-button" data-action="reset">Reset example</button>`)}<div class="tools-row"><input class="search" id="playerSearch" aria-label="Search player, team or position" placeholder="Search player, team, or position" value="${esc(state.search)}"><span class="micro">${state.pool.length} PLAYERS IN HISTORY</span></div><div class="table-wrap"><table class="player-table"><thead><tr><th scope="col" aria-label="On roster">IN</th><th scope="col">PLAYER</th><th scope="col" class="number">PROJ.</th><th scope="col" class="number recent-column">LAST 3</th><th scope="col" class="number">OVERRIDE</th></tr></thead><tbody id="rosterBody">${rosterRows()}</tbody></table></div><div class="roster-note">Example pool, not your real league. Uncheck players you do not own. “Flag out” is your manual availability override; no injury feed is connected.</div></section>
 <section class="panel lineup-panel">${panelHeading('02 / THE STARTING SEVEN','Your lineup',`<span class="formation">1 · 2 · 2 · 1 · FLEX</span>`)}<div class="lineup-rows">${lineup}</div><div class="lineup-actions"><button class="primary" data-action="export" ${!solved.feasible?'disabled':''}>Export lineup <span aria-hidden="true">↗</span></button><button class="secondary" data-action="reveal" ${!solved.feasible?'disabled':''}>Reveal historical results</button></div><div class="content-pad fineprint">${state.risk==='steady'?`Steadiness objective: <b>${fmt(solved.objective)}</b>. Each player’s projection is penalized by 0.25 × recent historical standard deviation. The total above remains projected points, not the penalized score.`:'Exact optimization over your eligible players. FLEX accepts RB, WR or TE. Each player can appear only once.'}</div></section></div>
 <div class="insight-strip"><b>What would a pickup change?</b><span>The waiver lab re-solves your lineup after each one-for-one move. A better bench player may add zero starting points.</span><button class="link-button" data-view="waivers">Measure a move ↗</button></div>
 <p class="fineprint">Reference replay: ${state.meta.players} selected players and ${state.meta.records} real historical records, not the entire NFL. Automatic eligibility also requires three prior observations, no recorded team bye, and a recent observation. Verify availability yourself.</p>`;
}
function renderWaivers() {
 const data=state.moves;const top=data?.moves?.[0];
 const metric=state.risk==='steady'?'OBJECTIVE GAIN':'PROJECTED POINT GAIN';
 $('#view').innerHTML=`<div class="stats-grid">${stat('CURRENT STARTING TOTAL',fmt(state.solved.projection),`${label(state.scoring)} · before any hypothetical move`,true)}${stat('BEST AVAILABLE MOVE',top?signed(top.objective_gain):'—',metric.toLowerCase())}${stat('SCENARIOS COMPARED',String(data?.moves?.length??0),'Eligible nonrostered players in this pool')}</div>
 <div class="section-intro"><div><span class="panel-tag">ONE ADD. ONE DROP. RE-OPTIMIZE.</span><h2>Measure the actual lineup impact.</h2></div><span class="micro">LOCAL SCENARIOS ONLY</span></div>
 <div class="waiver-grid">${data?.moves?.length?data.moves.map((m,i)=>`<article class="waiver-card"><div class="waiver-top"><span class="waiver-rank">MOVE ${String(i+1).padStart(2,'0')}</span><div class="gain">${signed(m.objective_gain)}<small>${metric}</small></div></div><div class="transaction"><div><small>ADD TO YOUR EXAMPLE ROSTER</small><strong>${esc(m.add.name)}</strong><span class="player-meta">${playerTag(m.add)} ${esc(m.add.team)} · ${fmt(m.add.projection)} projected</span></div><span class="transaction-arrow">↘</span><div><small>DROP FROM YOUR EXAMPLE ROSTER</small><strong>${esc(m.drop.name)}</strong><span class="player-meta">${playerTag(m.drop)} ${esc(m.drop.team)} · ${fmt(m.drop.projection)} projected</span></div></div><div class="waiver-bottom"><span>${m.enters_lineup?'Enters starting lineup':'Bench only; no starting slot'}<br><b>${fmt(m.projection)}</b> new projected total${state.risk==='steady'?` · ${signed(m.projected_gain)} points`:''}</span><button class="secondary" data-add="${esc(m.add.id)}" data-drop="${esc(m.drop.id)}">Try this move</button></div></article>`).join(''):`<div class="panel empty-state">${esc(data?.reason||'There are no eligible nonrostered players in this pool. Uncheck a player in the lineup lab to compare pickups.')}</div>`}</div>
 <div class="small-grid"><article class="note-card"><h3>Why not just rank players?</h3><p>A highly projected tight end may still sit behind your current tight end and FLEX. The app values the change to the legal starting seven, not the name in isolation.</p></article><article class="note-card"><h3>A deliberately narrow decision</h3><p>This is one week and one move. It does not price waiver bids, future weeks, bye coverage, or bench depth. Trying a move changes this browser’s example roster only.</p></article></div>`;
}
function seriesChart(series, axis='Week', yTitle='Fantasy points') {
 const all=series.flatMap(s=>s.points).filter(p=>Number.isFinite(p.x)&&Number.isFinite(p.y));if(!all.length)return '<div class="empty-state">Not enough observations to draw a chart.</div>';
 const W=920,H=285,L=50,R=20,T=25,B=38;const xs=all.map(p=>p.x),ys=all.map(p=>p.y);
 const xmin=Math.min(...xs),xmax=Math.max(xmin+1,...xs),ymin=Math.min(0,...ys),ymax=Math.max(1,...ys)*1.12;
 const x=v=>L+(v-xmin)/(xmax-xmin)*(W-L-R),y=v=>H-B-(v-ymin)/(ymax-ymin)*(H-T-B);
 const grid=Array.from({length:5},(_,i)=>{const v=ymin+(ymax-ymin)*i/4;return `<line x1="${L}" y1="${y(v)}" x2="${W-R}" y2="${y(v)}" stroke="currentColor" opacity=".1"/><text x="${L-12}" y="${y(v)+4}" text-anchor="end" fill="currentColor" opacity=".6" font-size="11">${fmt(v,0)}</text>`;}).join('');
 const ticks=[...new Set(xs)].sort((a,b)=>a-b).filter((_,i)=>i%Math.max(1,Math.ceil(new Set(xs).size/12))===0).map(v=>`<text x="${x(v)}" y="${H-12}" text-anchor="middle" fill="currentColor" opacity=".6" font-size="11">${axis==='Week'?'W':''}${v}</text>`).join('');
 const paths=series.map((s,i)=>{const color=i===0?'#9fc6e6':'#d2b99a';const points=s.points.filter(p=>Number.isFinite(p.y));return `<polyline points="${points.map(p=>`${x(p.x)},${y(p.y)}`).join(' ')}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linejoin="round"/>`+points.map(p=>`<circle cx="${x(p.x)}" cy="${y(p.y)}" r="4" fill="${color}" stroke="#10151c" stroke-width="2"><title>${esc(s.name)} · ${axis} ${p.x} · ${fmt(p.y,2)}</title></circle>`).join('');}).join('');
 return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(yTitle)} by ${esc(axis)}; exact observations available in tables or exports">${grid}${ticks}${paths}</svg><div class="chart-legend">${series.map((s,i)=>`<span><i class="legend-dot ${i?'alt':''}"></i>${esc(s.name)}</span>`).join('')}</div>`;
}
function renderCompare() {
 const pool=state.pool;if(!pool.length){$('#view').innerHTML='<div class="empty-state">No historical players.</div>';return;}
 if(!pool.some(p=>p.id===state.compare[0]))state.compare[0]=pool.find(p=>p.name==='Joe Mixon')?.id||pool[0].id;
 if(!pool.some(p=>p.id===state.compare[1]))state.compare[1]=pool.find(p=>p.name==='Derrick Henry')?.id||pool[Math.min(1,pool.length-1)].id;
 const players=state.compare.map(id=>pool.find(p=>p.id===id));
 const signalSummary=p=>{const values=[p.projection,p.baseline,p.recent_three].filter(Number.isFinite);const mean=values.reduce((a,b)=>a+b,0)/values.length;const spread=Math.max(...values)-Math.min(...values);return {mean,spread};};
 $('#view').innerHTML=`<div class="compare-controls">${players.map((p,i)=>`<label>PLAYER ${i===0?'A':'B'}<select data-compare="${i}" aria-label="Player ${i===0?'A':'B'}">${[...pool].sort((a,b)=>a.name.localeCompare(b.name)).map(q=>`<option value="${esc(q.id)}" ${p.id===q.id?'selected':''}>${esc(q.name)} · ${esc(q.position)}</option>`).join('')}</select></label>`).join('')}</div>
 <div class="compare-cards">${players.map(p=>{const sig=signalSummary(p);return `<article class="compare-card"><div class="player-meta">${playerTag(p)} ${esc(p.team)} · last observed Week ${p.last_week}</div><h2>${esc(p.name)}</h2><div class="decision-call"><div><span class="signal-kicker">MODEL CALL</span><strong>${fmt(p.projection)} pts</strong></div><div><span class="signal-kicker">3-SIGNAL MEAN</span><strong>${fmt(sig.mean)} pts</strong></div><div><span class="signal-kicker">SIGNAL SPREAD</span><strong>${fmt(sig.spread)} pts</strong></div></div><div class="signal-board"><div><span>Recency blend</span><b>${fmt(p.projection)}</b></div><div><span>History mean</span><b>${fmt(p.baseline)}</b></div><div><span>Last 3 mean</span><b>${fmt(p.recent_three)}</b></div></div><div class="metric-trio"><div><b>${fmt(p.volatility)}</b><small>Recent SD</small></div><div><b>${fmt(p.historical_q25)}</b><small>Historical Q25</small></div><div><b>${fmt(p.historical_q75)}</b><small>Historical Q75</small></div></div><p class="body-copy">${esc(p.explanation)}</p><p class="fineprint">The three-signal mean is a descriptive cross-check across internal methods, not an external expert consensus. ${p.n} prior observations. ${p.eligible?'Eligibility conditions pass; availability still unverified.':esc(p.availability_note)+'.'} The historical quartiles are descriptive, not a forecast interval.</p></article>`;}).join('')}</div>
 <section class="panel chart-panel">${panelHeading('THE INPUTS / NOT THE TARGET','Historical scoring')}${seriesChart(players.map(p=>({name:p.name,points:p.history.map(g=>({x:g.week,y:g.points}))})))}<p class="chart-caption">Only observations before Week ${state.week}. Gaps are joined visually; an absent record is not a zero-point game.</p></section>
 <details><summary>Inspect the exact historical observations</summary><div class="table-wrap"><table class="audit-table"><thead><tr><th>Player</th><th>Week</th><th>Team</th><th>Opponent</th><th class="number">Points</th></tr></thead><tbody>${players.flatMap(p=>p.history.map(g=>`<tr><td>${esc(p.name)}</td><td>${g.week}</td><td>${esc(g.team)}</td><td>${esc(g.opponent)}</td><td class="number">${fmt(g.points,2)}</td></tr>`)).join('')}</tbody></table></div></details>`;
}
function renderAudit() {
 const a=state.audit;if(!a){$('#view').innerHTML='<div class="loading-state">Loading audit…</div>';return;}
 const m=a.overall.model,b=a.overall.history_mean;const delta=b.mae===null||m.mae===null?null:b.mae-m.mae;
 const comparison=delta===null?'No evaluable observations.':`The heuristic’s MAE is ${fmt(Math.abs(delta),3)} points ${delta>=0?'lower':'higher'} than the loaded-history mean on this sample. This is descriptive, not evidence of a general advantage.`;
 $('#view').innerHTML=`<div class="stats-grid">${stat('MEAN ABSOLUTE ERROR',fmt(m.mae,2),'Fantasy points · lower is better',true)}${stat('OBSERVED PREDICTIONS',String(m.n),'Same evaluation rows for every baseline')}${stat('UNKNOWN OUTCOMES',String(a.missing_outcomes),'Excluded from errors; never filled with zero')}</div>
 <div class="audit-layout"><section class="panel">${panelHeading('SAME COHORT / THREE METHODS','The honest benchmark',`<button class="link-button" data-action="audit-export">Export audit ↗</button>`)}<div class="table-wrap"><table class="audit-table"><thead><tr><th>METHOD</th><th class="number">MAE ↓</th><th class="number">RMSE ↓</th><th class="number">BIAS</th></tr></thead><tbody>${[['Recency blend','model'],['Loaded-history mean','history_mean'],['Previous observed game','last_game']].map(([name,key])=>`<tr class="${key==='model'?'highlight':''}"><td>${name}</td><td class="number">${fmt(a.overall[key].mae,2)}</td><td class="number">${fmt(a.overall[key].rmse,2)}</td><td class="number">${fmt(a.overall[key].bias,2)}</td></tr>`).join('')}</tbody></table></div><p class="content-pad body-copy">${comparison}</p></section>
 <aside class="note-card"><span class="panel-tag">READ THIS RESULT CORRECTLY</span><h3>Small sample. No victory lap.</h3><p>These are historical, selected-player observations. Metrics omit missing outcomes and players that fail the eligibility rules. They are not a full-roster score or a comparison against professional projections.</p><p>Bias = predicted minus actual. A negative bias means underprediction on average.</p></aside></div>
 <section class="panel chart-panel">${panelHeading('WALK-FORWARD ERROR','No future week in the inputs')}${seriesChart([{name:'Recency blend MAE',points:a.weekly.map(w=>({x:w.week,y:w.model.mae}))},{name:'History mean MAE',points:a.weekly.map(w=>({x:w.week,y:w.history_mean.mae}))}],'Week','Mean absolute error')}<p class="chart-caption">Each week uses strictly earlier records. This audit covers all evaluable weeks in the selected season, independently of the lineup’s decision-week control.</p></section>
 <div class="small-grid"><article class="note-card"><h3>What is fixed?</h3><p>A maximum of six recent games, 0.75 recency decay, 65% recent weighted mean and 35% loaded-history mean. These are explicit design choices, not fitted coefficients or optimized hyperparameters.</p></article><article class="note-card"><h3>What is excluded?</h3><p>No current injury feed, opponent-adjusted strength, snaps, weather, depth charts, or availability probabilities. The app does not turn a heuristic into an “AI” claim.</p></article></div>`;
}
function renderPipeline() {
 const meta=state.meta;
 $('#view').innerHTML=`<div class="pipeline-path">${[['01','Historical CSV','Explicit source + schema'],['02','Validation','Types · keys · checksum'],['03','SQL features','Pre-week window functions'],['04','Python decisions','Projection + exact lineup'],['05','Decision interface','Compare · simulate · audit']].map(([step,name,sub])=>`<div class="pipeline-node"><span class="step">${step}</span><h3>${name}</h3><p>${sub}</p></div>`).join('')}</div>
 <div class="provenance"><section class="panel">${panelHeading('DATA CONTRACT','Inspect the reference')}
 <div class="content-pad"><div class="definition-row"><span>Dataset</span><b>${esc(meta.dataset.name)}</b></div><div class="definition-row"><span>Scope</span><b>${meta.players} players / ${meta.records} observed games</b></div><div class="definition-row"><span>Coverage</span><b>Weeks ${meta.first_week}–${meta.last_week}, ${state.season}</b></div><div class="definition-row"><span>Scoring</span><b>Standard points + reception multiplier</b></div><div class="definition-row"><span>Key</span><b>Player ID + season + week</b></div><div class="definition-row"><span>Null outcomes</span><b>Unknown, never assumed zero</b></div><div class="definition-row"><span>Source</span><b>${esc(meta.dataset.source)}</b></div><p class="fineprint">SHA-256 of the loaded dataset</p><div class="hash">${esc(meta.sha256)}</div><div class="lineup-actions"><a class="secondary" href="/api/data.csv" download>Export loaded data</a><button class="secondary" data-action="manifest">Export provenance</button></div></div></section>
 <section class="panel">${panelHeading('EXECUTION / NOT MARKETING','What actually runs?')}<div class="content-pad"><div class="definition-row"><span>Python + SQLite + browser</span><b class="status-pill">LOCAL IMPLEMENTATION</b></div><div class="definition-row"><span>AWS S3 upload adapter</span><b class="status-pill unverified">NOT CLOUD-DEPLOYED</b></div><div class="definition-row"><span>Databricks / Delta notebook</span><b class="status-pill unverified">NOT CLOUD-EXECUTED</b></div><p class="body-copy">The local application needs only Python. Optional AWS storage configuration, an upload adapter, and a Databricks batch notebook are included in the repository. They are not silently simulated by the local app.</p><p class="fineprint">A small reference dataset does not need distributed computing. The cloud path demonstrates how the same data contract could move into a separate batch workflow; it is not required to make this demo work.</p></div></section></div>
 <div class="small-grid"><article class="note-card"><h3>Fail loudly, not creatively.</h3><p>Missing columns, duplicate player-week keys, invalid positions, non-finite numbers and corrupted reference bytes produce an error. The loader does not invent stats to keep the screen populated.</p></article><article class="note-card"><h3>Use a fuller historical dataset.</h3><p>The repository includes a CSV importer and an nflverse download command. Both validate before writing. Run the app with <code>--data data/full_2024.csv</code> after importing. External downloads require internet access.</p></article></div>
 <details><summary>Projection and optimizer specification</summary><pre>points = standard_points + reception_multiplier × receptions
recent_weight[i] = 0.75 ** games_before_latest[i]
projection = 0.65 × recent_weighted_mean + 0.35 × history_mean

maximize Σ (projection[player] − λ × recent_SD[player])
subject to 1 QB + 2 RB + 2 WR + 1 TE + 1 FLEX
           each player appears at most once
           only selected, eligible, nonexcluded players

λ = 0.00 (projected points) or 0.25 (steadiness preference)
Exact dynamic programming: O(players × slots × 2^slots)</pre></details>
 <p class="fineprint">Historical data attribution: nflverse, CC BY 4.0; reference values preserved in a commit-pinned public mirror. Source URLs, transformation notes, and limitations are in data/manifest.json and THIRD_PARTY_NOTICES.md. No NFL or fantasy-platform endorsement is implied.</p>`;
}
// Delegated handlers survive view updates. All mutation remains local to this app.
document.addEventListener('click', async event=>{
 const button=event.target.closest('button');if(!button||button.disabled)return;
 if(button.dataset.view){state.view=button.dataset.view;state.search='';await refresh();window.scrollTo(0,0);$('#workspace').focus({preventScroll:true});return;}
 if(button.dataset.scoring){state.scoring=button.dataset.scoring;await refresh();return;}
 if(button.dataset.exclude){const id=button.dataset.exclude;state.exclude.has(id)?state.exclude.delete(id):state.exclude.add(id);await refresh();return;}
 if(button.dataset.add){state.roster.delete(button.dataset.drop);state.roster.add(button.dataset.add);state.view='lineup';await refresh();toast('Hypothetical move applied to this example roster only.');return;}
 const action=button.dataset.action;
 if(action==='reset'){state.roster=new Set(state.meta.default_roster);state.exclude.clear();await refresh();toast('Example roster restored.');}
 if(action==='export'&&state.solved.feasible){const rows=[['season','week','scoring','objective','history_cutoff_week','slot','player_id','player','projection'],...state.solved.lineup.map(p=>[state.season,state.week,state.scoring,state.risk,state.week-1,p.slot,p.id,p.name,p.projection])];download(csv(rows),`fourth-down-${state.season}-w${state.week}-lineup.csv`);}
 if(action==='audit-export'&&state.audit){const keys=['id','name','position','week','history_end','projection','baseline','last_game','actual'];download(csv([keys,...state.audit.records.map(r=>keys.map(k=>r[k]))]),`fourth-down-${state.season}-${state.scoring}-audit.csv`);}
 if(action==='manifest')download(JSON.stringify(state.meta,null,2),'fourth-down-provenance.json','application/json');
 if(action==='reveal'){
  button.disabled=true;try {const r=await api('/api/reveal',payload());$('#resultsContent').innerHTML=`<span class="panel-tag">HINDSIGHT / KEPT SEPARATE</span><h2>Week ${r.week} results</h2><div class="reveal-total">${fmt(r.total)}<small>observed lineup total</small></div>${r.missing.length?`<p class="warning">Incomplete outcomes: ${esc(r.missing.join(', '))}. The full total is unknown; the observed subtotal is ${fmt(r.observed_subtotal)}.</p>`:''}<div class="results-head results-grid"><span>PLAYER</span><span>PROJ.</span><span>ACTUAL</span></div>${r.players.map(p=>`<div class="results-grid"><span>${esc(p.slot)} · ${esc(p.name)}</span><b>${fmt(p.projection)}</b><b>${fmt(p.actual)}</b></div>`).join('')}<p class="fineprint">${esc(r.note)} Revealing history does not establish that this lineup would have been chosen in a live setting.</p>`;$('#resultsDialog').showModal();} catch(e){error(e.message);}finally{button.disabled=false;}
 }
});
document.addEventListener('change',async event=>{
 const target=event.target;
 if(target.dataset.roster){const id=target.dataset.roster;if(target.checked&&state.roster.size>=24){target.checked=false;toast('Limit: 24 players on your roster.');return;}target.checked?state.roster.add(id):state.roster.delete(id);await refresh();}
 else if(target.dataset.compare!==undefined){state.compare[Number(target.dataset.compare)]=target.value;renderCompare();}
 else if(target.id==='season'){state.season=Number(target.value);state.exclude.clear();await refresh();}
 else if(target.id==='week'){state.week=Number(target.value);state.exclude.clear();await refresh();}
 else if(target.id==='risk'){state.risk=target.value;await refresh();}
});
document.addEventListener('input',event=>{if(event.target.id==='playerSearch'){state.search=event.target.value;$('#rosterBody').innerHTML=rosterRows();}});
$('#closeDialog').addEventListener('click',()=>$('#resultsDialog').close());
async function start() {
 try {state.meta=await api('/api/meta');state.season=state.meta.default_season;state.week=state.meta.default_week;state.roster=new Set(state.meta.default_roster);
  try {const saved=JSON.parse(localStorage.getItem('fourth-down-v1'));if(saved?.sha===state.meta.sha256&&Array.isArray(saved.roster)&&saved.roster.length<=24){if(state.meta.seasons.includes(saved.season))state.season=saved.season;if(Number.isInteger(saved.week))state.week=saved.week;if(['half','ppr','standard'].includes(saved.scoring))state.scoring=saved.scoring;if(['points','steady'].includes(saved.risk))state.risk=saved.risk;state.roster=new Set(saved.roster.filter(x=>typeof x==='string'));state.exclude=new Set(Array.isArray(saved.exclude)?saved.exclude.filter(x=>typeof x==='string'):[]);}}
  catch(_){/* A damaged saved preference never replaces validated source data. */}
  await refresh();
 }catch(e){error(e.message);$('#view').innerHTML='<div class="empty-state">Start the Python server, then reload this page. The HTML file is not a standalone application.</div>';}
}
start();
