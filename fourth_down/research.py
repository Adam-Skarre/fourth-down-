"""Chronological ridge-regression benchmark, independent of the lineup heuristic.

2022 trains; 2023 selects regularization by MAE; the selected configuration is
refit on 2022–2023 and evaluated once on 2024. Standard library only.
"""
from collections import defaultdict
from statistics import mean, pstdev
from pathlib import Path
import csv, hashlib, json, math, random
from .data import ROOT, load_games
from .model import metrics
FEATURES = ['history_mean', 'recent_weighted', 'last_three', 'last_game', 'recent_sd', 'history_count', 'RB', 'WR', 'TE']
LAMBDAS = (0.1, 1.0, 10.0, 100.0, 1000.0)

def examples(games):
    groups = defaultdict(list)
    for g in games:
        groups[g.player_id, g.season].append(g)
    rows = []
    for (pid, year), history in sorted(groups.items()):
        history.sort(key=lambda g: g.week)
        for i, g in enumerate(history):
            prior = history[:i]
            if len(prior) < 3 or g.week - prior[-1].week > 2:
                continue
            values = [p.points('half') for p in prior]
            recent = values[-6:]
            weights = [0.75 ** k for k in reversed(range(len(recent)))]
            weighted = sum((v * w for v, w in zip(recent, weights))) / sum(weights)
            avg = mean(values)
            x = [avg, weighted, mean(values[-3:]), values[-1], pstdev(recent), len(prior), *[float(prior[-1].position == p) for p in ('RB', 'WR', 'TE')]]
            rows.append({'id': pid, 'name': prior[-1].name, 'position': prior[-1].position, 'season': year, 'week': g.week, 'history_end': prior[-1].week, 'x': x, 'actual': g.points('half'), 'history': avg, 'blend': 0.65 * weighted + 0.35 * avg, 'last_game': values[-1]})
    return rows

def solve(a, b):
    a = [list(row) + [val] for row, val in zip(a, b)]
    n = len(b)
    for c in range(n):
        pivot = max(range(c, n), key=lambda r: abs(a[r][c]))
        a[c], a[pivot] = (a[pivot], a[c])
        if abs(a[c][c]) < 1e-12:
            raise ValueError('Singular system')
        d = a[c][c]
        a[c] = [v / d for v in a[c]]
        for r in range(n):
            if r != c:
                d = a[r][c]
                a[r] = [v - d * w for v, w in zip(a[r], a[c])]
    return [r[-1] for r in a]

def fit(rows, penalty):
    means = [mean((r['x'][j] for r in rows)) for j in range(len(FEATURES))]
    scales = [pstdev((r['x'][j] for r in rows)) or 1 for j in range(len(FEATURES))]
    xs = [[1] + [(v - m) / s for v, m, s in zip(r['x'], means, scales)] for r in rows]
    n = len(xs[0])
    a = [[sum((x[i] * x[j] for x in xs)) + (penalty if i == j and i else 0) for j in range(n)] for i in range(n)]
    b = [sum((x[i] * r['actual'] for x, r in zip(xs, rows))) for i in range(n)]
    return {'means': means, 'scales': scales, 'coefficients': solve(a, b), 'lambda': penalty}

def predict(model, x):
    z = [1] + [(v - m) / s for v, m, s in zip(x, model['means'], model['scales'])]
    return sum((a * b for a, b in zip(z, model['coefficients'])))

def bootstrap(rows, repeats=1000):
    """Paired player-cluster bootstrap of MAE(model) - MAE(history)."""
    groups = defaultdict(list)
    for r in rows:
        groups[r['id']].append(abs(r['ridge'] - r['actual']) - abs(r['history'] - r['actual']))
    aggregates = [(sum(v), len(v)) for v in groups.values()]
    rng = random.Random(42)
    deltas = []
    for _ in range(repeats):
        sample = [rng.choice(aggregates) for _ in aggregates]
        deltas.append(sum((v for v, n in sample)) / sum((n for v, n in sample)))
    deltas.sort()
    return {'method': 'Paired player-cluster bootstrap, percentile interval', 'repeats': repeats, 'seed': 42, 'clusters': len(groups), 'lower': round(deltas[int(0.025 * repeats)], 4), 'upper': round(deltas[int(0.975 * repeats)], 4), 'quantity': 'MAE ridge minus MAE history; negative favors ridge', 'limitation': 'Conditional on sampled players; does not capture common weekly shocks or model-selection uncertainty.'}

def build_report(directory=None):
    directory = Path(directory or ROOT / 'data/research')
    manifest = json.loads((directory / 'manifest.json').read_text())
    seasons = {}
    for source in manifest['sources']:
        path = directory / f"{source['season']}.csv"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source['normalized_sha256'], 'Research data checksum mismatch'
        seasons[source['season']] = load_games(path)
    rows = {y: examples(g) for y, g in seasons.items()}
    validation = []
    for penalty in LAMBDAS:
        model = fit(rows[2022], penalty)
        validation.append({'lambda': penalty, **metrics([(predict(model, r['x']), r['actual']) for r in rows[2023]])})
    choice = min(validation, key=lambda v: (v['mae'], v['lambda']))['lambda']
    model = fit(rows[2022] + rows[2023], choice)
    evaluated = [dict(r, ridge=predict(model, r['x'])) for r in rows[2024]]

    def score(rs):
        return {method: metrics([(r[method], r['actual']) for r in rs]) for method in ('ridge', 'blend', 'history', 'last_game')}
    report = {'title': 'Chronological NFL forecast benchmark', 'scoring': 'half PPR', 'target': 'Next observed player-week fantasy points, conditional on recorded outcome and prior-history eligibility', 'features': FEATURES, 'sources': manifest, 'split': {'train': 2022, 'validation': 2023, 'evaluation': 2024, 'refit': [2022, 2023]}, 'cohorts': {str(y): {'records': len(seasons[y]), 'predictions': len(rows[y]), 'players': len({r['id'] for r in rows[y]})} for y in seasons}, 'validation': validation, 'selected_lambda': choice, 'model': model, 'overall': score(evaluated), 'by_position': {p: score([r for r in evaluated if r['position'] == p]) for p in ('QB', 'RB', 'WR', 'TE')}, 'by_week': [{'week': w, **score([r for r in evaluated if r['week'] == w])} for w in sorted({r['week'] for r in evaluated})], 'uncertainty': bootstrap(evaluated), 'limitations': ['Retrospective study; design and split were chosen after the seasons occurred. This is not a prospective or preregistered validation.', 'Missing target outcomes are not zero-filled. Evaluation is conditional on recorded player appearances, at least three prior games, and a prior observation within two weeks.', 'No live injury feed, snap counts, opponent adjustments or league ownership. No claim of professional-projection superiority or realized lineup gains.', 'The fitted model is a research benchmark. The interactive lineup replay continues using its documented 65/35 heuristic.', 'AWS and Databricks verification covers the original 164-row reference, not this expanded local benchmark.']}
    return (report, evaluated)
if __name__ == '__main__':
    report, rows = build_report()
    (ROOT / 'reports/research.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    fields = ['id', 'name', 'position', 'season', 'week', 'history_end', 'actual', 'ridge', 'blend', 'history', 'last_game']
    with (ROOT / 'reports/research_predictions.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({'cohorts': report['cohorts'], 'lambda': report['selected_lambda'], 'metrics': report['overall'], 'uncertainty': report['uncertainty']}, indent=2))
