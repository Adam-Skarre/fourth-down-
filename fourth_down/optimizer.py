"""Exact bitmask dynamic programming, including FLEX and player uniqueness."""
from __future__ import annotations
import math
from .data import DataError

SLOTS = ('QB', 'RB1', 'RB2', 'WR1', 'WR2', 'TE', 'FLEX')
ELIGIBILITY = (frozenset(['QB']), frozenset(['RB']), frozenset(['RB']),
               frozenset(['WR']), frozenset(['WR']), frozenset(['TE']),
               frozenset(['RB', 'WR', 'TE']))
RISK = {'points': 0.0, 'steady': 0.25}


def optimize(players: list[dict], risk: str = 'points') -> dict:
    """O(N * S * 2^S). Every player can be used at most once.

    A copied DP frontier for each player prevents assigning that same player to
    two slots. Score maximizes projection - lambda * historical SD. The second
    objective is a preference penalty, not a probability or lineup variance model.
    """
    if not isinstance(risk, str) or risk not in RISK:
        raise DataError('Risk preference must be points or steady.')
    if len(players) > 64:
        raise DataError('Optimizer input is limited to 64 players.')
    ids = [p['id'] for p in players]
    if len(ids) != len(set(ids)):
        raise DataError('A player appears more than once.')
    for p in players:
        if not math.isfinite(p['projection']) or not math.isfinite(p['volatility']):
            raise DataError('Optimizer scores must be finite.')
        if p['volatility'] < 0 or p['position'] not in {'QB', 'RB', 'WR', 'TE'}:
            raise DataError('Invalid volatility or unsupported position.')
    # State -> (objective, tuple of (slot index, player index)).
    ordered = sorted(players, key=lambda p: p['id'])
    dp = {0: (0.0, ())}
    for index, player in enumerate(ordered):
        previous = dict(dp)
        value = player['projection'] - RISK[risk] * player['volatility']
        for mask, (score, picks) in previous.items():
            for slot, positions in enumerate(ELIGIBILITY):
                if player['position'] not in positions or mask & (1 << slot):
                    continue
                new_mask = mask | (1 << slot)
                candidate = (score + value, picks + ((slot, index),))
                current = dp.get(new_mask)
                if current is None or candidate[0] > current[0] + 1e-10:
                    dp[new_mask] = candidate
    full = (1 << len(SLOTS)) - 1
    if full not in dp:
        counts = {pos: sum(p['position'] == pos for p in players) for pos in ['QB', 'RB', 'WR', 'TE']}
        return {'feasible': False, 'lineup': [], 'projection': None, 'objective': None,
                'reason': 'A legal lineup needs 1 QB, 2 RB, 2 WR, 1 TE and one additional RB/WR/TE. Add eligible players or remove an unavailable flag.',
                'available_counts': counts}
    objective, assignments = dp[full]
    lineup = [dict(ordered[index], slot=SLOTS[slot]) for slot, index in sorted(assignments)]
    selected = {p['id'] for p in lineup}
    return {'feasible': True, 'lineup': lineup,
            'bench': [p for p in ordered if p['id'] not in selected],
            'projection': round(sum(p['projection'] for p in lineup), 4),
            'objective': round(objective, 4), 'risk': risk,
            'method': 'Exact bitmask dynamic programming; 7 slots, unique players, legal FLEX.'}


def waiver_moves(pool: list[dict], roster_ids: set[str], excluded: set[str], risk: str) -> dict:
    eligible = [p for p in pool if p['eligible'] and p['id'] not in excluded]
    roster = [p for p in eligible if p['id'] in roster_ids]
    current = optimize(roster, risk)
    if not current['feasible']:
        return {'baseline': current, 'moves': [], 'reason': 'Build a legal lineup before evaluating a one-for-one pickup.'}
    by_id = {p['id']: p for p in pool}
    moves = []
    for add in eligible:
        if add['id'] in roster_ids:
            continue
        best = None
        # A noneligible roster player can also be dropped. We do not invent ownership.
        drops = sorted((by_id[x] for x in roster_ids if x in by_id),
                       key=lambda p: (p['projection'], p['id']))
        for drop in drops:
            scenario = [p for p in roster if p['id'] != drop['id']] + [add]
            solved = optimize(scenario, risk)
            if not solved['feasible']:
                continue
            if best is None or solved['objective'] > best['objective'] + 1e-10:
                best = {'add': add, 'drop': drop, 'objective': solved['objective'],
                        'projection': solved['projection'],
                        'projected_gain': round(solved['projection'] - current['projection'], 4),
                        'objective_gain': round(solved['objective'] - current['objective'], 4),
                        'enters_lineup': any(p['id'] == add['id'] for p in solved['lineup']),
                        'lineup': solved['lineup']}
        if best:
            moves.append(best)
    moves.sort(key=lambda m: (-m['objective_gain'], m['add']['name']))
    return {'baseline': current, 'moves': moves,
            'scope': 'One-week, one-add/one-drop scenarios within your selected demo pool; no actual league ownership, rest-of-season value or transaction is implied.'}
