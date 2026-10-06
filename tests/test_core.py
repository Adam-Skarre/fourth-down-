from __future__ import annotations
import csv
import io
import json
import math
import random
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from statistics import mean
from fourth_down.data import DataError, Repository, load_games, number, validate_rows, write_games
from fourth_down.model import project, backtest, metrics, quantile
from fourth_down.optimizer import SLOTS, ELIGIBILITY, optimize, waiver_moves
from fourth_down.server import Service
from scripts.import_nflverse import normalize
from scripts.export_artifacts import export
from cloud.aws.upload import build_plan, upload

REPO = Repository()

class DataTests(unittest.TestCase):
    def test_reference_shape_and_checksum(self):
        self.assertEqual(len(REPO.games),164)
        self.assertEqual(REPO.metadata()['players'],14)
        self.assertEqual(REPO.sha256,REPO.manifest['sha256'])
    def test_csv_json_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            csvpath=Path(d)/'copy.csv';jsonpath=Path(d)/'copy.json'
            write_games(REPO.games,csvpath)
            jsonpath.write_text(json.dumps([asdict(g) for g in REPO.games]))
            self.assertEqual(load_games(csvpath),REPO.games)
            self.assertEqual(load_games(jsonpath),REPO.games)
    def test_known_scoring(self):
        g=REPO.by_key[('00-0030061',2024,11)]
        self.assertAlmostEqual(g.points('standard'),12.7)
        self.assertAlmostEqual(g.points('half'),15.7)
        self.assertAlmostEqual(g.points('ppr'),18.7)
    def test_invalid_scoring(self):
        with self.assertRaises(DataError):REPO.games[0].points('mystery')
    def test_empty(self):
        with self.assertRaises(DataError):validate_rows([])
    def test_duplicate_key(self):
        row=asdict(REPO.games[0])
        with self.assertRaisesRegex(DataError,'duplicate'):validate_rows([row,row])
    def test_position_change(self):
        a=asdict(REPO.games[0]);b={**a,'week':17,'position':'TE'}
        with self.assertRaisesRegex(DataError,'position changed'):validate_rows([a,b])
    def test_missing_column(self):
        row=asdict(REPO.games[0]);del row['receptions']
        with self.assertRaisesRegex(DataError,'Missing columns'):validate_rows([row])
    def test_nonfinite_numbers(self):
        for v in [float('nan'),float('inf'),-float('inf'),'NaN','inf',None,True,'',[],{}]:
            with self.subTest(v=v),self.assertRaises(DataError):number(v,'value')
    def test_invalid_receptions(self):
        for v in [-1,2.5,51,None]:
            with self.subTest(v=v),self.assertRaises(DataError):validate_rows([{**asdict(REPO.games[0]),'receptions':v}])
    def test_invalid_identity(self):
        for key,value in [('name',None),('name',''),('team',None),('player_id','../../x'),('position','DST'),('opponent','')]:
            with self.subTest(key=key,value=value),self.assertRaises(DataError):validate_rows([{**asdict(REPO.games[0]),key:value}])
    def test_week_and_season_bounds(self):
        for key,value in [('week',0),('week',19),('week',3.5),('season',1970),('season',True)]:
            with self.subTest(key=key,value=value),self.assertRaises(DataError):validate_rows([{**asdict(REPO.games[0]),key:value}])
    def test_invalid_json_shape(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.json';p.write_text('{"rows":[]}')
            with self.assertRaisesRegex(DataError,'array'):load_games(p)
    def test_missing_file(self):
        with self.assertRaises(DataError):load_games(Path('/no/such/fourth-down.csv'))
    def test_sql_aggregates_match_independent_python(self):
        rows=REPO.history(2024,13,'half')
        self.assertTrue(all(r['week']<13 for r in rows))
        for pid in {r['player_id'] for r in rows}:
            group=[r for r in rows if r['player_id']==pid]
            expected=mean(g.points('half') for g in REPO.games if g.player_id==pid and g.week<13)
            self.assertAlmostEqual(group[-1]['history_mean'],expected)
            self.assertAlmostEqual(group[-1]['recent_three_mean'],mean(r['points'] for r in group[-3:]))
            self.assertEqual(group[-1]['recency_rank'],1)

class ModelTests(unittest.TestCase):
    def test_projection_cutoff(self):
        for week in range(6,17):
            for p in project(REPO,2024,week,'half'):
                self.assertLess(p['last_week'],week)
                self.assertTrue(all(g['week']<week for g in p['history']))
    def test_future_outcomes_do_not_change_predictions(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'mutated.csv'
            modified=[replace(g,standard_points=100.0,receptions=12) if g.week>=13 else g for g in REPO.games]
            write_games(modified,path)
            self.assertEqual(project(REPO,2024,13,'half'),project(Repository(path),2024,13,'half'))
    def test_future_only_player_not_in_candidate_pool(self):
        with tempfile.TemporaryDirectory() as d:
            new=replace(REPO.games[0],player_id='future_only',name='Future Only',week=16)
            path=Path(d)/'mutated.csv';write_games([*REPO.games,new],path)
            self.assertNotIn('future_only',[p['id'] for p in project(Repository(path),2024,13,'half')])
    def test_explicit_model_formula(self):
        for p in project(REPO,2024,13,'half'):
            history=[g['points'] for g in p['history']];r=history[-6:]
            weights=[.75**i for i in reversed(range(len(r)))]
            expected=.65*sum(a*b for a,b in zip(r,weights))/sum(weights)+.35*mean(history)
            self.assertAlmostEqual(p['projection'],expected,places=3)
    def test_bye_exclusion(self):
        henry=next(p for p in project(REPO,2024,14,'half') if p['name']=='Derrick Henry')
        self.assertTrue(henry['bye']);self.assertFalse(henry['eligible'])
    def test_minimum_history(self):
        thielen=next(p for p in project(REPO,2024,13,'half') if p['name']=='Adam Thielen')
        self.assertEqual(thielen['n'],2);self.assertFalse(thielen['eligible'])
    def test_stale_history(self):
        evans=next(p for p in project(REPO,2024,10,'half') if p['name']=='Mike Evans')
        self.assertTrue(evans['stale']);self.assertFalse(evans['eligible'])
    def test_missing_not_zero(self):
        a=backtest(REPO,2024,'half')
        self.assertEqual(a['missing_outcomes'],3)
        for record in a['records']:
            self.assertIn((record['id'],2024,record['week']),REPO.by_key)
    def test_evaluation_same_cohort(self):
        a=backtest(REPO,2024,'half')
        self.assertEqual({m['n'] for m in a['overall'].values()},{121})
        self.assertTrue(all(r['history_end']<r['week'] for r in a['records']))
    def test_metrics_independent_recalculation(self):
        a=backtest(REPO,2024,'half');errors=[r['projection']-r['actual'] for r in a['records']]
        self.assertAlmostEqual(a['overall']['model']['mae'],mean(abs(e) for e in errors),places=3)
        self.assertAlmostEqual(a['overall']['model']['rmse'],math.sqrt(mean(e*e for e in errors)),places=3)
    def test_metrics_empty(self):
        self.assertEqual(metrics([]),{'n':0,'mae':None,'rmse':None,'bias':None})
    def test_quantile(self):
        self.assertEqual(quantile([0,10,20,30],.25),7.5)
        self.assertEqual(quantile([4],.75),4)
    def test_selection_errors(self):
        for season,week,scoring in [(2023,13,'half'),(2024,1,'half'),(2024,19,'half'),(2024,True,'half'),(2024,13,'invalid'),(2024,13,[])]:
            with self.subTest(week=week,scoring=scoring),self.assertRaises(DataError):project(REPO,season,week,scoring)

class OptimizerTests(unittest.TestCase):
    def setUp(self):
        self.pool=project(REPO,2024,13,'half')
        self.roster=set(REPO.metadata()['default_roster'])
        self.players=[p for p in self.pool if p['eligible'] and p['id'] in self.roster]
    def test_complete_legal_unique_lineup(self):
        result=optimize(self.players)
        self.assertTrue(result['feasible']);self.assertEqual(len({p['id'] for p in result['lineup']}),7)
        for i,p in enumerate(result['lineup']):self.assertIn(p['position'],ELIGIBILITY[i])
    def test_optimal_against_independent_bruteforce(self):
        def brute(players,risk):
            best=-math.inf
            def walk(slot,used,total):
                nonlocal best
                if slot==7:best=max(best,total);return
                for p in players:
                    if p['id'] not in used and p['position'] in ELIGIBILITY[slot]:
                        walk(slot+1,used|{p['id']},total+p['projection']-risk*p['volatility'])
            walk(0,set(),0.0);return best
        for seed in range(8):
            rng=random.Random(seed)
            players=[{**p,'projection':rng.uniform(-5,35),'volatility':rng.uniform(0,20)} for p in self.players]
            for risk,penalty in [('points',0),('steady',.25)]:
                with self.subTest(seed=seed,risk=risk):
                    self.assertAlmostEqual(optimize(players,risk)['objective'],brute(players,penalty),places=3)
    def test_infeasible(self):
        self.assertFalse(optimize([p for p in self.players if p['position']!='QB'])['feasible'])
    def test_negative_scores_still_fill_slots(self):
        result=optimize([{**p,'projection':-5.} for p in self.players])
        self.assertTrue(result['feasible']);self.assertEqual(result['projection'],-35.)
    def test_duplicate_rejected(self):
        with self.assertRaises(DataError):optimize(self.players+[self.players[0]])
    def test_nonfinite_rejected(self):
        with self.assertRaises(DataError):optimize([{**self.players[0],'projection':float('nan')}])
    def test_negative_volatility_rejected(self):
        with self.assertRaises(DataError):optimize([{**self.players[0],'volatility':-1}])
    def test_deterministic_input_permutation(self):
        self.assertEqual(optimize(self.players),optimize(list(reversed(self.players))))
    def test_waiver_gain_recalculates(self):
        result=waiver_moves(self.pool,self.roster,set(),'points')
        self.assertTrue(result['moves'])
        for move in result['moves']:
            new=(self.roster-{move['drop']['id']})|{move['add']['id']}
            solved=optimize([p for p in self.pool if p['eligible'] and p['id'] in new])
            self.assertAlmostEqual(move['projected_gain'],solved['projection']-result['baseline']['projection'],places=3)
    def test_excluded_player_never_added(self):
        excluded={p['id'] for p in self.pool if p['name']=='Alvin Kamara'}
        moves=waiver_moves(self.pool,self.roster,excluded,'points')['moves']
        self.assertFalse(any(m['add']['id'] in excluded for m in moves))
    def test_infeasible_waiver_state(self):
        self.assertEqual(waiver_moves(self.pool,set(),set(),'points')['moves'],[])

class ImportExportTests(unittest.TestCase):
    @staticmethod
    def raw_fixture():
        row=asdict(REPO.games[0]);row.update(player_display_name=row.pop('name'),recent_team=row.pop('team'),opponent_team=row.pop('opponent'),fantasy_points=row.pop('standard_points'),season_type='REG')
        buffer=io.StringIO();writer=csv.DictWriter(buffer,fieldnames=list(row));writer.writeheader();writer.writerow(row)
        return buffer.getvalue().encode()
    def test_nflverse_normalization(self):
        self.assertEqual(normalize(self.raw_fixture(),2024),[REPO.games[0]])
    def test_new_aliases(self):
        b=self.raw_fixture().replace(b'recent_team',b'team').replace(b'player_display_name',b'player_name')
        self.assertEqual(normalize(b,2024),[REPO.games[0]])
    def test_unsupported_schema(self):
        with self.assertRaisesRegex(DataError,'Unsupported upstream schema'):normalize(b'player,points\nAdam,30\n',2024)
    def test_ppr_consistency(self):
        b=self.raw_fixture().decode().splitlines();b[0]+=',fantasy_points_ppr';b[1]+=',999'
        with self.assertRaisesRegex(DataError,'PPR'):normalize(('\n'.join(b)).encode(),2024)
    def test_batch_artifacts(self):
        with tempfile.TemporaryDirectory() as d:
            report=export(REPO,Path(d));self.assertEqual(len(report['files']),3)
            self.assertFalse(report['cloud_executed'])
            self.assertEqual(load_games(Path(d)/'player_games.csv'),REPO.games)
    def test_s3_plan_upload_contract(self):
        with tempfile.TemporaryDirectory() as d:
            export(REPO,Path(d));plan=build_plan(Path(d),'fourth-down-test')
            class Fake:
                def __init__(self):self.calls=[]
                def upload_file(self,*args,**kwargs):self.calls.append((args,kwargs))
            client=Fake();upload(plan,client)
            self.assertEqual(len(client.calls),4)
            self.assertTrue(all(c[1]['ExtraArgs']['ServerSideEncryption']=='AES256' for c in client.calls))
            self.assertTrue(all('sha256' in c[1]['ExtraArgs']['Metadata'] for c in client.calls))
    def test_s3_kms_contract(self):
        with tempfile.TemporaryDirectory() as d:
            export(REPO,Path(d));plan=build_plan(Path(d),'fourth-down-test')
            class Fake:
                def upload_file(self,*args,**kwargs):
                    assert kwargs['ExtraArgs']['SSEKMSKeyId']=='alias/fourth-down'
                    assert kwargs['ExtraArgs']['ServerSideEncryption']=='aws:kms'
            upload(plan,Fake(),'alias/fourth-down')
    def test_s3_path_restrictions(self):
        for bucket,prefix in [('UPPERCASE','x'),('valid-bucket','../credentials'),('valid-bucket','/absolute'),('valid-bucket','a//b'),('127.0.0.1','x')]:
            with self.subTest(bucket=bucket,prefix=prefix),self.assertRaises(DataError):build_plan(Path('.'),bucket,prefix)
    def test_s3_requires_artifacts(self):
        with tempfile.TemporaryDirectory() as d,self.assertRaisesRegex(DataError,'Missing'):build_plan(Path(d),'fourth-down-test')

class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.service=Service(REPO)
        self.payload={'season':2024,'week':13,'scoring':'half','risk':'points','roster':REPO.metadata()['default_roster'],'exclude':[]}
    def test_manual_exclusion(self):
        self.payload['exclude']=[self.payload['roster'][0]]
        result=self.service.solve(self.payload)
        self.assertNotIn(self.payload['exclude'][0],[p['id'] for p in result['lineup']])
    def test_reveal_matches_source(self):
        result=self.service.reveal(self.payload)
        self.assertTrue(result['players'])
        self.assertEqual(result['total'],round(sum(p['actual'] for p in result['players']),2))
    def test_unknown_player(self):
        self.payload['roster']=['invented']
        with self.assertRaises(DataError):self.service.solve(self.payload)
    def test_duplicate_roster(self):
        self.payload['roster']*=2
        with self.assertRaises(DataError):self.service.solve(self.payload)
    def test_oversized_roster(self):
        self.payload['roster']=['x']*25
        with self.assertRaises(DataError):self.service.solve(self.payload)
    def test_infeasible_reveal(self):
        self.payload['roster']=[]
        with self.assertRaises(DataError):self.service.reveal(self.payload)
    def test_wrong_payload_type(self):
        with self.assertRaises(DataError):self.service.solve([])

if __name__=='__main__':unittest.main()
