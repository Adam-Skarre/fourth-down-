"""Reconcile every bundled record with a commit-pinned upstream mirror.

Requires internet access. This external reconciliation was NOT run in the
network-isolated build environment; local schema/checksum tests are separate.
"""
from __future__ import annotations
import json
from fourth_down.data import Repository, ROOT
from scripts.import_nflverse import fetch_bytes, normalize


def main() -> int:
    repo = Repository()
    manifest = repo.manifest
    source = {}
    for filename in manifest['source_files'].values():
        content = fetch_bytes(manifest['mirror_base'] + filename)
        for g in normalize(content, 2024):
            source[(g.player_id, g.season, g.week)] = g
    mismatches = []
    for key, bundled in repo.by_key.items():
        original = source.get(key)
        if original != bundled:
            mismatches.append({'key': key, 'bundled': repr(bundled), 'source': repr(original)})
    report = {'reference_rows': len(repo.games), 'matched': len(repo.games)-len(mismatches),
              'source_commit': manifest['mirror_commit'], 'mismatches': mismatches}
    output = ROOT/'reports/source_reconciliation.json'
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    return 1 if mismatches else 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f'External verification did not complete: {exc}')
        raise SystemExit(1)
