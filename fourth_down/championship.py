"""Reproducible, explicitly retrospective 2025 backfield diagnostic.

Fits one recency coefficient on weeks 4-10, freezes it, evaluates weeks 11-17.
This is NOT a reconstruction of the user's actual lineups or a causal result.
The original production heuristic remains unchanged in model.py.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
from .data import DataError, Repository, ROOT, SCORING
from .model import DECAY, RECENT_BLEND, RECENT_GAMES, metrics, project

CASE = ROOT / 'data/championship_2025'
TRAIN_END = 10
TEST_START, TEST_END = 11, 17
METHODS = {'original': 'Original 65/35 model', 'fitted': 'Early-season fitted blend',
           'history': 'History-average baseline', 'recent_three': 'Last-three-game baseline',
           'last_game': 'Last-game baseline'}
BYE_WEEKS = {'MIA': 12, 'DEN': 12, 'DET': 8, 'NE': 14}


def forecast_rows(repo: Repository, scoring: str = 'ppr', end_week: int = TEST_END) -> tuple[list[dict], list[dict]]:
    """Predict before looking up outcomes. Missing/bye rows never become zeros."""
    if scoring not in SCORING:
        raise DataError('Scoring must be standard, half or ppr.')
    records, omitted = [], []
    for week in range(4, end_week + 1):
        for p in project(repo, 2025, week, scoring):
            if BYE_WEEKS.get(p['team']) == week:
                omitted.append({'week': week, 'id': p['id'], 'reason': 'Scheduled team bye'})
                continue
            if not p['eligible']:
                omitted.append({'week': week, 'id': p['id'], 'reason': p['availability_note']})
                continue
            # Forecast features are frozen first; target lookup happens only afterward.
            record = {'week': week, 'id': p['id'], 'name': p['name'],
                      'history_end': p['last_week'], 'prior_games': p['n'],
                      'history': p['baseline'], 'recent_weighted': p['recent_weighted'],
                      'recent_three': p['recent_three'], 'last_game': p['last_points'],
                      'original': p['projection']}
            actual_game = repo.by_key.get((p['id'], 2025, week))
            if actual_game is None:
                omitted.append({'week': week, 'id': p['id'], 'reason': 'No observed target; not scored as zero'})
                continue
            record['actual'] = round(actual_game.points(scoring), 4)
            records.append(record)
    return records, omitted


def fit_blend(records: list[dict], train_end: int = TRAIN_END) -> dict:
    """Least-squares solution for alpha, constrained to [0,1]; no late outcomes.

    p(alpha)=history+alpha*(recent-history).
    alpha=clip(sum((recent-history)*(actual-history))/sum((recent-history)^2)).
    A zero denominator identifies no recency signal; default to history average.
    """
    training = [r for r in records if 4 <= r['week'] <= train_end]
    if not training:
        raise DataError('No observed training rows with enough prior history.')
    numerator = sum((r['recent_weighted'] - r['history']) * (r['actual'] - r['history']) for r in training)
    denominator = sum((r['recent_weighted'] - r['history']) ** 2 for r in training)
    raw_alpha = numerator / denominator if denominator > 1e-12 else 0.0
    return {'alpha': max(0.0, min(1.0, raw_alpha)), 'unconstrained_alpha': raw_alpha,
            'n': len(training), 'training_weeks': [4, train_end],
            'max_training_outcome_week': max(r['week'] for r in training),
            'objective': 'Minimize squared forecast error on early-season observed player-weeks',
            'fallback': denominator <= 1e-12}


def add_fitted(records: list[dict], alpha: float) -> list[dict]:
    if not 0 <= alpha <= 1:
        raise DataError('Alpha must be within [0,1].')
    return [dict(r, fitted=r['history'] + alpha * (r['recent_weighted'] - r['history'])) for r in records]


def evaluate(records: list[dict], start: int, end: int) -> dict:
    selected = [r for r in records if start <= r['week'] <= end]
    return {'weeks': [start, end], 'n': len(selected),
            'methods': {m: dict(label=label, **metrics([(r[m], r['actual']) for r in selected]))
                        for m, label in METHODS.items()},
            'cohort': 'Same observed, non-bye, prior-history-eligible player-weeks for all methods. Missing outcomes excluded.'}


def pair_case(records: list[dict], acquisition_week: int) -> dict:
    if type(acquisition_week) is not int or acquisition_week not in (15, 16, 17):
        raise DataError('Assumed acquisition week must be 15, 16 or 17.')
    index = {(r['id'], r['week']): r for r in records}
    weeks, skipped = [], []
    totals = {m: 0.0 for m in METHODS}
    totals.update(always_montgomery=0.0, always_stevenson=0.0, hindsight_best=0.0)
    correct = {m: 0 for m in METHODS}
    for week in (15, 16, 17):
        if week < acquisition_week:
            skipped.append({'week': week, 'reason': 'Before assumed Stevenson acquisition'})
            continue
        if any((pid, week) not in index for pid in ('montgomery', 'stevenson')):
            skipped.append({'week': week, 'reason': 'Both comparable player-outcomes are required'})
            continue
        a, b = index['montgomery', week], index['stevenson', week]
        outcome = max(a['actual'], b['actual'])
        decisions = {}
        for method in METHODS:
            chosen = sorted((a, b), key=lambda r: (-r[method], r['id']))[0]
            decisions[method] = {'id': chosen['id'], 'name': chosen['name'],
                                 'actual': chosen['actual'], 'projection': round(chosen[method], 4),
                                 'regret_vs_hindsight': round(outcome - chosen['actual'], 4)}
            totals[method] += chosen['actual']
            correct[method] += int(abs(chosen['actual'] - outcome) < 1e-8)
        totals['always_montgomery'] += a['actual']
        totals['always_stevenson'] += b['actual']
        totals['hindsight_best'] += outcome
        weeks.append({'week': week, 'players': [a, b], 'decisions': decisions})
    return {'weeks': weeks, 'skipped': skipped, 'n': len(weeks),
            'totals': {k: round(v, 2) for k, v in totals.items()}, 'correct_weekly_choices': correct,
            'assumed_acquisition_week': acquisition_week,
            'scope': 'One hypothetical interchangeable RB/FLEX slot, not the full starting lineup.',
            'baseline_note': 'Always-start comparisons are descriptive controls, not claims they were the manager decisions. Hindsight best is unattainable advance knowledge.'}


def subset_case(records: list[dict], acquisition_week: int) -> list[dict]:
    """Restricted three-RB exercise; WR/TE FLEX alternatives are NOT evaluated."""
    index = {(r['id'], r['week']): r for r in records}
    result = []
    for week in (15, 16, 17):
        base_ids = ['achane', 'harvey', 'montgomery']
        pool_ids = base_ids + (['stevenson'] if week >= acquisition_week else [])
        if any((pid, week) not in index for pid in pool_ids):
            result.append({'week': week, 'status': 'Incomplete observed outcomes'})
            continue
        pool = [index[pid, week] for pid in pool_ids]
        base_actual = sum(index[pid, week]['actual'] for pid in base_ids)
        methods = {}
        for method in METHODS:
            selected = sorted(pool, key=lambda r: (-r[method], r['id']))[:3]
            actual = sum(r['actual'] for r in selected)
            methods[method] = {'selected': [r['name'] for r in selected],
                               'projected': round(sum(r[method] for r in selected), 4),
                               'actual': round(actual, 2),
                               'delta_vs_drafted_three': round(actual - base_actual, 2)}
        result.append({'week': week, 'status': 'Restricted RB-only counterfactual',
                       'drafted_three_actual': round(base_actual, 2), 'methods': methods})
    return result


def build_report(scoring: str = 'ppr', acquisition_week: int = 15, data_path: Path | None = None) -> dict:
    if scoring not in SCORING:
        raise DataError('Scoring must be standard, half or ppr.')
    if type(acquisition_week) is not int or acquisition_week not in (15, 16, 17):
        raise DataError('Assumed acquisition week must be 15, 16 or 17.')
    path = data_path or CASE / 'backfield.csv'
    source = json.loads((CASE / 'manifest.json').read_text())
    repo = Repository(path)
    if path.resolve() == (CASE / 'backfield.csv').resolve() and repo.sha256 != source['sha256']:
        raise DataError('Bundled 2025 dataset checksum mismatch.')
    records, omitted = forecast_rows(repo, scoring)
    fit = fit_blend(records)
    records = add_fitted(records, fit['alpha'])
    train, later = evaluate(records, 4, TRAIN_END), evaluate(records, TEST_START, TEST_END)
    return {'title': 'AJ 2025 — championship-roster research case', 'version': '1.1.0',
            'analysis_created': '2026-10-06', 'scoring': scoring,
            'status': 'Retrospective, selected-roster diagnostic. Not a causal championship result.',
            'roster': json.loads((CASE / 'roster.json').read_text()),
            'data': {'records': len(repo.games), 'players': len({g.player_id for g in repo.games}),
                     'sha256': repo.sha256, 'manifest': source},
            'parameters': {'original_recent_blend': RECENT_BLEND, 'recent_games': RECENT_GAMES,
                           'decay': DECAY, 'minimum_prior_games': 3},
            'fit': fit, 'training': train, 'later_evaluation': later,
            'player_forecasts': records, 'omitted': omitted,
            'pair_case': pair_case(records, acquisition_week),
            'three_rb_case': subset_case(records, acquisition_week),
            'limits': [
                'Only four RBs have statistical data here; all 17 drafted players plus the reported playoff addition are inventoried, not all evaluated.',
                'Full PPR and weeks 15-17 are defaults, not confirmed league settings or playoff dates.',
                'Stevenson ownership is assumed from the selected week; actual add/drop time and roster history were not supplied.',
                'The coefficient is fitted on weeks 4-10 only. Evaluation uses weeks 11-17. The roster and study were chosen after knowing the championship outcome, so this is not untouched validation.',
                'Latest published historical statistics are used; original injury, waiver, lineup, and publication-time feeds are not reconstructed.',
                'Absent outcomes are excluded, not imputed as zero. Error metrics are conditional on observed player appearances, not the total cost of unavailable starts.',
                'The pair comparison is not an optimization against WR/TE FLEX options and cannot establish an improvement over actual team decisions.',
                'No model win probability, statistical significance, production advantage, or causal championship attribution is established.'
            ]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scoring', choices=tuple(SCORING), default='ppr')
    parser.add_argument('--acquired-week', type=int, choices=(15, 16, 17), default=15)
    parser.add_argument('--output', type=Path, default=ROOT / 'reports/championship_2025.json')
    args = parser.parse_args()
    report = build_report(args.scoring, args.acquired_week)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    csv_path = args.output.with_suffix('.csv')
    with csv_path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=report['player_forecasts'][0].keys())
        writer.writeheader(); writer.writerows(report['player_forecasts'])
    print(json.dumps({'output': str(args.output), 'forecasts_csv': str(csv_path),
                      'fitted_alpha': report['fit']['alpha'],
                      'later_evaluation': report['later_evaluation'],
                      'pair_totals': report['pair_case']['totals']}, indent=2))


if __name__ == '__main__':
    main()
