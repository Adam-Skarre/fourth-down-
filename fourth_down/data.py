"""Strict CSV/JSON ingestion, provenance checks and SQL-backed historical features."""
from __future__ import annotations
import csv
import hashlib
import json
import math
import re
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('player_id', 'name', 'position', 'team', 'season', 'week', 'opponent', 'standard_points', 'receptions')
SCORING = {'standard': 0.0, 'half': 0.5, 'ppr': 1.0}
POSITIONS = frozenset(('QB', 'RB', 'WR', 'TE'))

class DataError(ValueError):
    """An input violated the dataset contract; never silently fabricate a value."""

@dataclass(frozen=True)
class Game:
    player_id: str
    name: str
    position: str
    team: str
    season: int
    week: int
    opponent: str
    standard_points: float
    receptions: int

    def points(self, scoring: str) -> float:
        if scoring not in SCORING:
            raise DataError('Scoring must be standard, half or ppr.')
        return self.standard_points + SCORING[scoring] * self.receptions


def number(value: object, field: str) -> float:
    if isinstance(value, bool) or value is None or str(value).strip() == '':
        raise DataError(f'{field} must contain a number, not a missing value.')
    try:
        result = float(value)
    except (ValueError, TypeError) as exc:
        raise DataError(f'{field} must be numeric.') from exc
    if not math.isfinite(result):
        raise DataError(f'{field} must be finite.')
    return result


def integer(value: object, field: str) -> int:
    result = number(value, field)
    if not result.is_integer():
        raise DataError(f'{field} must be an integer.')
    return int(result)


def validate_row(row: dict) -> Game:
    missing = set(FIELDS) - row.keys()
    if missing:
        raise DataError('Missing columns: ' + ', '.join(sorted(missing)))
    if any(row[k] is None or not isinstance(row[k], str) for k in ('player_id', 'name', 'position', 'team', 'opponent')):
        raise DataError('Identity and team fields must contain text, not null values.')
    pid = str(row['player_id']).strip()
    name = str(row['name']).strip()
    pos = str(row['position']).strip().upper()
    team = str(row['team']).strip().upper()
    opponent = str(row['opponent']).strip().upper()
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,50}', pid):
        raise DataError('player_id contains invalid characters.')
    if not name or len(name) > 100 or any(ord(c) < 32 for c in name):
        raise DataError('name must be 1–100 printable characters.')
    if pos not in POSITIONS:
        raise DataError(f'Unsupported position {pos!r}; only QB/RB/WR/TE are supported.')
    if not re.fullmatch(r'[A-Z]{2,4}', team) or not re.fullmatch(r'[A-Z]{2,4}', opponent):
        raise DataError('team and opponent must be 2–4 letter team codes.')
    season = integer(row['season'], 'season')
    week = integer(row['week'], 'week')
    points = number(row['standard_points'], 'standard_points')
    receptions = integer(row['receptions'], 'receptions')
    if not 1999 <= season <= 2100 or not 1 <= week <= 18:
        raise DataError('Expected a regular-season year (1999–2100) and week (1–18).')
    if not -100 <= points <= 150 or not 0 <= receptions <= 50:
        raise DataError('Fantasy points or receptions exceed the accepted sanity range.')
    return Game(pid, name, pos, team, season, week, opponent, points, receptions)


def validate_rows(rows: Iterable[dict]) -> list[Game]:
    result: list[Game] = []
    seen: set[tuple] = set()
    identities: dict[str, str] = {}
    for index, row in enumerate(rows, 2):
        if not isinstance(row, dict):
            raise DataError(f'Row {index}: expected an object.')
        try:
            game = validate_row(row)
        except DataError as exc:
            raise DataError(f'Row {index}: {exc}') from exc
        key = (game.player_id, game.season, game.week)
        if key in seen:
            raise DataError(f'Row {index}: duplicate player/season/week key {key}.')
        if game.player_id in identities and identities[game.player_id] != game.position:
            raise DataError(f'Row {index}: position changed for {game.player_id}; resolve explicitly.')
        identities[game.player_id] = game.position
        seen.add(key)
        result.append(game)
    if not result:
        raise DataError('Dataset has no supported player-game records.')
    return sorted(result, key=lambda g: (g.season, g.week, g.player_id))


def load_games(path: Path) -> list[Game]:
    if not path.is_file():
        raise DataError(f'Data file does not exist: {path}')
    if path.stat().st_size > 100_000_000:
        raise DataError('Input exceeds the 100 MB local file limit.')
    try:
        with path.open(encoding='utf-8-sig', newline='') as handle:
            if path.suffix.lower() == '.json':
                rows = json.load(handle)
                if not isinstance(rows, list):
                    raise DataError('JSON input must be an array of row objects.')
            elif path.suffix.lower() == '.csv':
                rows = list(csv.DictReader(handle))
            else:
                raise DataError('Choose a .csv or .json normalized dataset.')
        return validate_rows(rows)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DataError(f'Cannot read data: {exc}') from exc


def write_games(games: Iterable[Game], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(asdict(game) for game in games)


class Repository:
    """Immutable, validated dataset. Each query gets an isolated in-memory SQL connection.

    The tiny offline sample does not need a database daemon. For a full season the
    same SQL is still cheap; use Databricks for the optional external batch path.
    """
    def __init__(self, path: Path | None = None):
        self.path = path or ROOT / 'data/reference_2024.csv'
        self.games = load_games(self.path)
        self.sha256 = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.is_reference = self.path.resolve() == (ROOT / 'data/reference_2024.csv').resolve()
        if self.is_reference:
            self.manifest = json.loads((ROOT / 'data/manifest.json').read_text())
            if self.sha256 != self.manifest['sha256']:
                raise DataError('Reference checksum mismatch. Restore the bundled CSV or import a separate file with --data.')
        else:
            self.manifest = {'name': 'Imported historical dataset', 'mode': 'imported_historical',
                             'source': 'User-imported normalized data; verify its provenance.',
                             'limitations': ['No live injury or league ownership feed.',
                                             'Historical team assignment is carried forward from the last observed game.',
                                             'Automatic bye checks are supplied for 2024 only; other seasons require manual exclusions.']}
        self.byes = json.loads((ROOT / 'data/byes_2024.json').read_text())
        self.seasons = sorted({g.season for g in self.games})
        self.by_key = {(g.player_id, g.season, g.week): g for g in self.games}
        self._sql = (ROOT / 'sql/historical_features.sql').read_text()
        self._schema = (ROOT / 'sql/schema.sql').read_text()

    def connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(':memory:')
        conn.row_factory = sqlite3.Row
        conn.executescript(self._schema)
        conn.executemany('INSERT INTO player_games VALUES (?,?,?,?,?,?,?,?,?)',
                         [tuple(asdict(g).values()) for g in self.games])
        return conn

    def history(self, season: int, week: int, scoring: str) -> list[dict]:
        if scoring not in SCORING:
            raise DataError('Invalid scoring preset.')
        conn = self.connection()
        try:
            return [dict(row) for row in conn.execute(self._sql,
                    {'season': season, 'week': week, 'ppr': SCORING[scoring]})]
        finally:
            conn.close()

    def bounds(self, season: int) -> tuple[int, int]:
        weeks = [g.week for g in self.games if g.season == season]
        if not weeks:
            raise DataError('That season is not present in the loaded dataset.')
        return min(weeks), max(weeks)

    def metadata(self) -> dict:
        default_season = self.seasons[-1]
        lo, hi = self.bounds(default_season)
        return {'name': 'Fourth Down', 'version': '1.0.0', 'dataset': self.manifest,
                'sha256': self.sha256, 'records': len(self.games),
                'players': len({g.player_id for g in self.games}), 'seasons': self.seasons,
                'bounds': {s: self.bounds(s) for s in self.seasons},
                'default_season': default_season, 'default_week': min(max(13, lo + 1), hi),
                'first_week': lo, 'last_week': hi,
                'default_roster': json.loads((ROOT / 'data/example_roster.json').read_text())['player_ids']}
