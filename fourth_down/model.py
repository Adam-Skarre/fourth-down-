"""Explainable, fixed-parameter estimates; no claims of calibrated ML predictions."""
from __future__ import annotations
from collections import defaultdict
from math import sqrt
from statistics import mean, pstdev
from .data import DataError, Repository, SCORING

MIN_HISTORY = 3
RECENT_GAMES = 6
DECAY = 0.75
RECENT_BLEND = 0.65


def quantile(values: list[float], q: float) -> float:
    values = sorted(values)
    index = (len(values) - 1) * q
    left = int(index)
    right = min(left + 1, len(values) - 1)
    return values[left] + (index - left) * (values[right] - values[left])


def validate_selection(repo: Repository, season: int, week: int, scoring: str) -> None:
    if type(season) is not int or type(week) is not int:
        raise DataError('Season and week must be integers.')
    lo, hi = repo.bounds(season)
    if not lo + 1 <= week <= hi:
        raise DataError(f'Choose a decision week from {lo + 1} through {hi}.')
    if not isinstance(scoring, str) or scoring not in SCORING:
        raise DataError('Scoring must be standard, half or ppr.')


def project(repo: Repository, season: int, week: int, scoring: str) -> list[dict]:
    validate_selection(repo, season, week, scoring)
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in repo.history(season, week, scoring):
        groups[row['player_id']].append(row)
    result = []
    for pid, rows in groups.items():
        latest = rows[-1]
        values = [r['points'] for r in rows]
        recent = values[-RECENT_GAMES:]
        weights = [DECAY ** i for i in reversed(range(len(recent)))]
        weighted = sum(x * w for x, w in zip(recent, weights)) / sum(weights)
        baseline = latest['history_mean']
        estimate = RECENT_BLEND * weighted + (1 - RECENT_BLEND) * baseline
        bye = season == 2024 and repo.byes.get(latest['team']) == week
        stale = week - latest['week'] > 2
        eligible = not bye and not stale and len(values) >= MIN_HISTORY
        reason = ('Team bye' if bye else 'History gap: verify availability' if stale
                  else 'Fewer than 3 prior games' if len(values) < MIN_HISTORY
                  else 'Availability not verified')
        result.append({
            'id': pid, 'name': latest['name'], 'position': latest['position'],
            'team': latest['team'], 'projection': round(estimate, 4),
            'baseline': round(baseline, 4), 'recent_weighted': round(weighted, 4),
            'recent_three': round(latest['recent_three_mean'], 4),
            'last_points': values[-1], 'last_week': latest['week'], 'n': len(values),
            'volatility': round(pstdev(recent), 4),
            'historical_q25': round(quantile(recent, 0.25), 4),
            'historical_q75': round(quantile(recent, 0.75), 4),
            'trend': round(latest['recent_three_mean'] - baseline, 4),
            'bye': bye, 'stale': stale, 'eligible': eligible, 'availability_note': reason,
            'history': [{'week': r['week'], 'points': round(r['points'], 2),
                         'opponent': r['opponent'], 'team': r['team']} for r in rows],
            'explanation': f"65% recent weighted average ({weighted:.1f}) + 35% loaded-history average ({baseline:.1f}). Only weeks before {week}."
        })
    return sorted(result, key=lambda p: (-p['projection'], p['name']))


def metrics(pairs: list[tuple[float, float]]) -> dict:
    if not pairs:
        return {'n': 0, 'mae': None, 'rmse': None, 'bias': None}
    errors = [pred - actual for pred, actual in pairs]
    return {'n': len(errors), 'mae': round(mean(abs(e) for e in errors), 4),
            'rmse': round(sqrt(mean(e * e for e in errors)), 4),
            'bias': round(mean(errors), 4)}


def backtest(repo: Repository, season: int, scoring: str) -> dict:
    """Walk forward without target-week features; retain missing-target counts.

    Metrics are conditional on an observed target-week row. Missing rows are not
    labeled zero. This is a selected-player demonstration, NOT a full-roster test.
    """
    lo, hi = repo.bounds(season)
    records, weekly = [], []
    missing = 0
    for week in range(lo + MIN_HISTORY, hi + 1):
        this_week, missing_week = [], 0
        for player in project(repo, season, week, scoring):
            if not player['eligible']:
                continue
            actual_game = repo.by_key.get((player['id'], season, week))
            if actual_game is None:
                missing_week += 1
                continue
            actual = actual_game.points(scoring)
            record = {'id': player['id'], 'name': player['name'], 'week': week,
                      'position': player['position'], 'projection': player['projection'],
                      'baseline': player['baseline'], 'last_game': player['last_points'],
                      'actual': round(actual, 4), 'history_end': player['last_week']}
            this_week.append(record)
            records.append(record)
        missing += missing_week
        weekly.append({'week': week, 'n': len(this_week), 'missing_outcomes': missing_week,
                       'model': metrics([(r['projection'], r['actual']) for r in this_week]),
                       'history_mean': metrics([(r['baseline'], r['actual']) for r in this_week]),
                       'last_game': metrics([(r['last_game'], r['actual']) for r in this_week])})
    overall = {label: metrics([(r[field], r['actual']) for r in records])
               for label, field in [('model', 'projection'), ('history_mean', 'baseline'), ('last_game', 'last_game')]}
    positions = {pos: metrics([(r['projection'], r['actual']) for r in records if r['position'] == pos])
                 for pos in ['QB', 'RB', 'WR', 'TE']}
    return {'season': season, 'scoring': scoring, 'overall': overall, 'weekly': weekly,
            'positions': positions, 'missing_outcomes': missing, 'records': records,
            'cohort': 'Only predicted, eligible player-weeks with an observed target-week row. Missing rows are excluded, never set to zero.',
            'limitation': 'Curated sample and fixed, uncalibrated heuristic. This does not establish an advantage over professional projections or on unseen seasons.',
            'parameters': {'min_history': MIN_HISTORY, 'recent_games': RECENT_GAMES,
                           'decay': DECAY, 'recent_blend': RECENT_BLEND}}
