"""Loopback-only JSON API and static application server; no third-party runtime."""
from __future__ import annotations
import csv
import io
import json
import logging
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from dataclasses import asdict
from urllib.parse import parse_qs, urlsplit
from .data import DataError, Repository, ROOT, FIELDS
from .model import backtest, project, validate_selection
from .optimizer import RISK, optimize, waiver_moves
from .championship import build_report

LOG = logging.getLogger('fourth_down')

class Service:
    def __init__(self, repo: Repository):
        self.repo = repo

    @lru_cache(maxsize=96)
    def snapshot(self, season: int, week: int, scoring: str) -> dict:
        players = project(self.repo, season, week, scoring)
        return {'season': season, 'week': week, 'scoring': scoring,
                'cutoff': week - 1, 'players': players,
                'eligible_count': sum(p['eligible'] for p in players)}

    @lru_cache(maxsize=12)
    def audit(self, season: int, scoring: str) -> dict:
        return backtest(self.repo, season, scoring)

    @lru_cache(maxsize=9)
    def championship(self, scoring: str, acquired: int) -> dict:
        return build_report(scoring, acquired)

    def parse(self, payload: dict) -> tuple[int, int, str, str, set[str], set[str]]:
        if not isinstance(payload, dict):
            raise DataError('Expected a JSON object.')
        season, week = payload.get('season', 2024), payload.get('week', 13)
        scoring, risk = payload.get('scoring', 'half'), payload.get('risk', 'points')
        validate_selection(self.repo, season, week, scoring)
        if not isinstance(risk, str) or risk not in RISK:
            raise DataError('Risk preference must be points or steady.')
        known = {p['id'] for p in self.snapshot(season, week, scoring)['players']}
        values = []
        for name, limit in [('roster', 24), ('exclude', 64)]:
            incoming = payload.get(name, [])
            if not isinstance(incoming, list) or len(incoming) > limit or any(not isinstance(x, str) for x in incoming):
                raise DataError(f'{name} must be an array of at most {limit} player IDs.')
            if len(incoming) != len(set(incoming)):
                raise DataError(f'{name} contains duplicate IDs.')
            if set(incoming) - known:
                raise DataError(f'{name} contains a player without history before the selected week.')
            values.append(set(incoming))
        return season, week, scoring, risk, values[0], values[1]

    def solve(self, payload: dict) -> dict:
        season, week, scoring, risk, roster, excluded = self.parse(payload)
        pool = self.snapshot(season, week, scoring)['players']
        valid = [p for p in pool if p['id'] in roster and p['id'] not in excluded and p['eligible']]
        result = optimize(valid, risk)
        result.update({'season': season, 'week': week, 'scoring': scoring,
                       'cutoff': week - 1, 'roster_size': len(roster), 'available': len(valid),
                       'omitted': [p for p in pool if p['id'] in roster and
                                   (p['id'] in excluded or not p['eligible'])]})
        return result

    def waivers(self, payload: dict) -> dict:
        season, week, scoring, risk, roster, excluded = self.parse(payload)
        return waiver_moves(self.snapshot(season, week, scoring)['players'], roster, excluded, risk)

    def reveal(self, payload: dict) -> dict:
        # Re-solve from the pre-week inputs. The client cannot insert a hindsight lineup.
        solved = self.solve(payload)
        if not solved['feasible']:
            raise DataError('Build a legal lineup before revealing outcomes.')
        rows, missing = [], []
        for player in solved['lineup']:
            game = self.repo.by_key.get((player['id'], solved['season'], solved['week']))
            actual = None if game is None else round(game.points(solved['scoring']), 2)
            rows.append({'name': player['name'], 'slot': player['slot'],
                         'projection': player['projection'], 'actual': actual})
            if actual is None:
                missing.append(player['name'])
        return {'week': solved['week'], 'season': solved['season'], 'scoring': solved['scoring'],
                'players': rows, 'total': None if missing else round(sum(r['actual'] for r in rows), 2),
                'observed_subtotal': round(sum(r['actual'] for r in rows if r['actual'] is not None), 2),
                'missing': missing, 'note': 'Absent outcomes remain unknown, not zero. Outcomes are never used by the optimizer.'}


def make_handler(service: Service):
    class Handler(BaseHTTPRequestHandler):
        server_version = 'FourthDown/1.0'
        sys_version = ''
        protocol_version = 'HTTP/1.1'

        def log_message(self, fmt, *args):
            LOG.debug(fmt, *args)

        def allowed_host(self) -> bool:
            port = self.server.server_port
            return self.headers.get('Host') in {f'127.0.0.1:{port}', f'localhost:{port}'}

        def send(self, status: int, content: bytes, mime: str = 'application/json; charset=utf-8', filename: str | None = None):
            self.send_response(status)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
            if filename:
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.end_headers()
            try:
                self.wfile.write(content)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def json(self, status: int, data: object):
            self.send(status, json.dumps(data, allow_nan=False, ensure_ascii=False).encode())

        def do_GET(self):
            if not self.allowed_host():
                self.json(403, {'error': 'Only loopback hostnames are allowed.'})
                return
            parsed = urlsplit(self.path)
            query = parse_qs(parsed.query)
            try:
                defaults = service.repo.metadata()
                season = int(query.get('season', [defaults['default_season']])[0])
                week = int(query.get('week', [defaults['default_week']])[0])
                scoring = query.get('scoring', ['half'])[0]
                if parsed.path == '/api/health':
                    self.json(200, {'status': 'ok', 'records': len(service.repo.games)})
                elif parsed.path == '/api/meta':
                    self.json(200, defaults)
                elif parsed.path == '/api/snapshot':
                    self.json(200, service.snapshot(season, week, scoring))
                elif parsed.path == '/api/audit':
                    self.json(200, service.audit(season, scoring))
                elif parsed.path == '/api/championship':
                    case_scoring = query.get('scoring', ['ppr'])[0]
                    acquired = int(query.get('acquired', ['15'])[0])
                    self.json(200, service.championship(case_scoring, acquired))
                elif parsed.path == '/api/data.csv':
                    buffer = io.StringIO(newline='')
                    writer = csv.DictWriter(buffer, fieldnames=FIELDS)
                    writer.writeheader()
                    writer.writerows(asdict(g) for g in service.repo.games)
                    self.send(200, buffer.getvalue().encode(), 'text/csv; charset=utf-8', 'fourth-down-source.csv')
                else:
                    allowed = {'/': ('index.html', 'text/html; charset=utf-8'),
                               '/index.html': ('index.html', 'text/html; charset=utf-8'),
                               '/championship.html': ('championship.html', 'text/html; charset=utf-8'),
                               '/championship.js': ('championship.js', 'text/javascript; charset=utf-8'),
                               '/championship.css': ('championship.css', 'text/css; charset=utf-8'),
                               '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                               '/style.css': ('style.css', 'text/css; charset=utf-8'),
                               '/favicon.svg': ('favicon.svg', 'image/svg+xml')}
                    if parsed.path not in allowed:
                        self.json(404, {'error': 'Route not found.'})
                        return
                    filename, mime = allowed[parsed.path]
                    self.send(200, (ROOT / 'app' / filename).read_bytes(), mime)
            except (DataError, ValueError, TypeError) as exc:
                self.json(400, {'error': str(exc)})
            except Exception:
                LOG.exception('Unexpected GET error')
                self.json(500, {'error': 'Unexpected server error. See the terminal log.'})

        def do_POST(self):
            if not self.allowed_host():
                self.close_connection = True
                self.json(403, {'error': 'Only loopback hostnames are allowed.'})
                return
            origin = self.headers.get('Origin')
            if origin and origin != f"http://{self.headers.get('Host')}":
                self.close_connection = True
                self.json(403, {'error': 'Cross-origin requests are not permitted.'})
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 1 <= length <= 65536:
                    self.close_connection = True
                    self.json(413, {'error': 'Request must be 1–65,536 bytes.'})
                    return
                if self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json':
                    self.close_connection = True
                    self.json(415, {'error': 'Use application/json.'})
                    return
                payload = json.loads(self.rfile.read(length))
                routes = {'/api/solve': service.solve, '/api/waivers': service.waivers, '/api/reveal': service.reveal}
                if self.path not in routes:
                    self.json(404, {'error': 'Route not found.'})
                    return
                self.json(200, routes[self.path](payload))
            except (ValueError, TypeError, DataError, UnicodeError) as exc:
                self.json(400, {'error': str(exc)})
            except Exception:
                LOG.exception('Unexpected POST error')
                self.json(500, {'error': 'Unexpected server error. See the terminal log.'})
    return Handler


def create_server(repo: Repository, port: int = 8765) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(('127.0.0.1', port), make_handler(Service(repo)))
    server.daemon_threads = True
    return server
