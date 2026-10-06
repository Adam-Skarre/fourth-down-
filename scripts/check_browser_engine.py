"""Cross-language optimizer parity on every bundled week/scoring/objective."""
import json, subprocess, shutil, sys
from pathlib import Path
from fourth_down.data import ROOT, Repository
from fourth_down.model import project
from fourth_down.optimizer import optimize
repo = Repository()
cases = []
for week in range(4, 17):
    for scoring in ('standard', 'half', 'ppr'):
        players = [p for p in project(repo, 2024, week, scoring) if p['eligible']]
        for steady in (False, True):
            cases.append({'players': players, 'steady': steady, 'expected': optimize(players, 'steady' if steady else 'points')})
node = sys.argv[1] if len(sys.argv) > 1 else shutil.which('node')
if not node:
    raise SystemExit('Node.js is required for browser-engine parity checks.')
program = "const fs=require('fs'),e=require('./site/engine.js');const c=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(c.map(x=>e.optimize(x.players,x.steady))));"
result = subprocess.run([node, '-e', program], input=json.dumps(cases), text=True, capture_output=True, cwd=ROOT, check=True)
for case, actual in zip(cases, json.loads(result.stdout)):
    expected = case['expected']
    assert actual['feasible'] == expected['feasible']
    if actual['feasible']:
        assert abs(actual['projection'] - expected['projection']) < 5.1e-05
        assert abs(actual['objective'] - expected['objective']) < 5.1e-05
        assert len({p['id'] for p in actual['lineup']}) == 7
print(f'PASS: {len(cases)} browser/Python optimizer comparisons')
