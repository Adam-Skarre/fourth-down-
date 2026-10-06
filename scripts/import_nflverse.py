"""Import full real historical NFL data; never silently substitute fabricated data.

python -m scripts.import_nflverse --season 2024 --output data/full_2024.csv
python -m scripts.import_nflverse --input downloaded.csv --season 2024
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen
from fourth_down.data import DataError, number, integer, validate_rows, write_games

SOURCE = 'https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{season}.csv'
MAX_BYTES = 100_000_000


def fetch_bytes(url: str) -> bytes:
    """Bounded HTTPS download; no credentials, telemetry, scraping or silent fallback."""
    if not url.startswith('https://'):
        raise DataError('Source must use HTTPS.')
    request = Request(url, headers={'User-Agent': 'FourthDown-ReferenceImporter/1.0'})
    with urlopen(request, timeout=45) as response:
        content = response.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise DataError('Source exceeded the 100 MB download limit.')
    return content


def normalize(content: bytes, season: int) -> list:
    """Normalize known old/new nflverse aliases; all scoring inputs remain mandatory."""
    reader = csv.DictReader(io.StringIO(content.decode('utf-8-sig')))
    headers = set(reader.fieldnames or [])
    aliases = {'player_id': ['player_id'], 'name': ['player_display_name', 'player_name'],
               'position': ['position'], 'team': ['recent_team', 'team'],
               'season': ['season'], 'week': ['week'], 'opponent': ['opponent_team', 'opponent'],
               'standard_points': ['fantasy_points'], 'receptions': ['receptions']}
    chosen = {target: next((candidate for candidate in options if candidate in headers), None)
              for target, options in aliases.items()}
    missing = [target for target, source in chosen.items() if source is None]
    if missing or 'season_type' not in headers:
        raise DataError('Unsupported upstream schema; missing: ' + ', '.join(missing + ([] if 'season_type' in headers else ['season_type'])))
    rows = []
    for line, row in enumerate(reader, 2):
        if row['season_type'] != 'REG' or integer(row['season'], 'season') != season:
            continue
        if row[chosen['position']] not in {'QB', 'RB', 'WR', 'TE'}:
            continue  # K, DST, FB and defense are outside this application's explicit scope.
        normalized = {target: row[source] for target, source in chosen.items()}
        if 'fantasy_points_ppr' in headers and row['fantasy_points_ppr'] not in (None, ''):
            expected = number(normalized['standard_points'], 'fantasy_points') + number(normalized['receptions'], 'receptions')
            if abs(expected - number(row['fantasy_points_ppr'], 'fantasy_points_ppr')) > 0.015:
                raise DataError(f'Line {line}: source PPR does not match base points + receptions.')
        rows.append(normalized)
    return validate_rows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--season', type=int, default=2024)
    parser.add_argument('--input', type=Path, help='Already-downloaded nflverse CSV; skips network.')
    parser.add_argument('--output', type=Path, default=None)
    args = parser.parse_args(argv)
    args.output = args.output or Path(f'data/full_{args.season}.csv')
    if not 1999 <= args.season <= datetime.now(timezone.utc).year:
        parser.error('Season must be between 1999 and the current year.')
    source = SOURCE.format(season=args.season)
    if args.output.resolve() == (Path(__file__).resolve().parents[1] / 'data/reference_2024.csv').resolve():
        parser.error('Do not overwrite the checksum-protected reference file. Choose a different output.')
    temp = args.output.with_suffix('.tmp.csv')
    try:
        if args.input and args.input.stat().st_size > MAX_BYTES:
            raise DataError('Input exceeds 100 MB.')
        raw = args.input.read_bytes() if args.input else fetch_bytes(source)
        games = normalize(raw, args.season)
        write_games(games, temp)
        os.replace(temp, args.output)
        metadata = {'source': str(args.input) if args.input else source,
                    'retrieved_at': datetime.now(timezone.utc).isoformat(), 'season': args.season,
                    'source_sha256': hashlib.sha256(raw).hexdigest(),
                    'normalized_sha256': hashlib.sha256(args.output.read_bytes()).hexdigest(),
                    'rows': len(games), 'players': len({g.player_id for g in games}),
                    'license': 'CC BY 4.0; retain nflverse attribution',
                    'changes': 'REG QB/RB/WR/TE only; selected normalized columns; no imputed outcomes.'}
        args.output.with_suffix('.manifest.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        print(json.dumps(metadata, indent=2))
        print(f'Historical dataset saved; the lineup replay bye schedule remains 2024-specific. Data:  "{args.output}"')
        return 0
    except (DataError, URLError, OSError, UnicodeError, TimeoutError) as exc:
        temp.unlink(missing_ok=True)
        print(f'Import failed: {exc}\nNo replacement dataset was fabricated. Download the upstream CSV and use --input on a connected computer.')
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
