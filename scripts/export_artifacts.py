"""Build traceable local batch outputs for inspection or optional cloud upload."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
from fourth_down.data import Repository, write_games
from fourth_down.model import project, backtest


def export(repo: Repository, output: Path, season: int=2024, week: int=13, scoring: str='half') -> dict:
    output.mkdir(parents=True, exist_ok=True)
    write_games(repo.games, output/'player_games.csv')
    forecasts = project(repo, season, week, scoring)
    fields = ['id','name','position','team','projection','baseline','recent_weighted','volatility','n','last_week','eligible']
    with (output/'projections.csv').open('w',newline='',encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key:p[key] for key in fields} for p in forecasts)
    audit = backtest(repo, season, scoring)
    (output/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    files = {name: hashlib.sha256((output/name).read_bytes()).hexdigest()
             for name in ['player_games.csv','projections.csv','audit.json']}
    report = {'season':season,'decision_week':week,'scoring':scoring,'history_cutoff_week':week-1,
              'source_sha256':repo.sha256,'files':files,'cloud_executed':False}
    (output/'run_manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path)
    parser.add_argument('--output',type=Path,default=Path('data/processed'))
    parser.add_argument('--season',type=int,default=2024)
    parser.add_argument('--week',type=int,default=13)
    parser.add_argument('--scoring',choices=['half','standard','ppr'],default='half')
    args=parser.parse_args()
    print(json.dumps(export(Repository(args.data),args.output,args.season,args.week,args.scoring),indent=2))

if __name__=='__main__':
    main()
