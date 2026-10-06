"""Run with `python -m fourth_down`; Python 3.10+ and no pip install required."""
from __future__ import annotations
import argparse
import json
import logging
import sys
import threading
import webbrowser
from pathlib import Path
from .data import DataError, Repository
from .model import backtest
from .server import create_server


def main() -> int:
    parser = argparse.ArgumentParser(description='Fourth Down — fantasy lineup decision lab')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--data', type=Path, help='Normalized CSV/JSON input; default is the offline reference snapshot.')
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--case-2025', action='store_true', help='Open the AJ 2025 retrospective research workspace.')
    parser.add_argument('--check', action='store_true', help='Validate the data and print the historical evaluation without starting the app.')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format='%(levelname)s: %(message)s')
    try:
        repo = Repository(args.data)
        if args.check:
            season = repo.seasons[-1]
            audit = backtest(repo, season, 'half')
            print(json.dumps({'records': len(repo.games), 'checksum': repo.sha256,
                              'half_ppr_audit': audit['overall'],
                              'missing_outcomes': audit['missing_outcomes']}, indent=2))
            return 0
        if not 1024 <= args.port <= 65535:
            raise DataError('Choose a port from 1024 through 65535.')
        server = create_server(repo, args.port)
    except (OSError, DataError) as exc:
        print(f'Cannot start Fourth Down: {exc}', file=sys.stderr)
        print('If the port is in use, try: python -m fourth_down --port 8766', file=sys.stderr)
        return 1
    url = f'http://127.0.0.1:{args.port}'
    print(f'\nFourth Down is running at {url}\n{len(repo.games)} validated historical records. Not a live NFL feed.\nPress Ctrl+C to stop.\n', flush=True)
    if args.case_2025:
        url += '/championship.html'
        print(f'2025 research workspace: {url}\n64 separately validated backfield records; scenario assumptions are shown in the app.\n')
    if not args.no_browser:
        timer = threading.Timer(0.6, webbrowser.open, args=(url,))
        timer.daemon = True
        timer.start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopped.')
    finally:
        server.server_close()
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
