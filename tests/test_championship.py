from __future__ import annotations
import json
import math
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from fourth_down.championship import (CASE, METHODS, add_fitted, build_report, evaluate,
                                     fit_blend, forecast_rows, pair_case)
from fourth_down.data import DataError, Repository, write_games
from fourth_down.model import project

class ChampionshipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = Repository(CASE / 'backfield.csv')
        cls.report = build_report()
    def test_real_dataset_size(self):
        self.assertEqual(len(self.repo.games),64)
        self.assertEqual({g.player_id for g in self.repo.games},{'achane','montgomery','harvey','stevenson'})
    def test_published_totals_reconcile(self):
        for pid,expected in [('achane',322.8),('harvey',206.6),('montgomery',166.9),('stevenson',178.8)]:
            self.assertAlmostEqual(sum(g.points('ppr') for g in self.repo.games if g.player_id==pid),expected)
    def test_stevenson_two_point_conversions(self):
        self.assertAlmostEqual(self.repo.by_key['stevenson',2025,2].points('ppr'),21.2)
        self.assertAlmostEqual(self.repo.by_key['stevenson',2025,16].points('ppr'),17.8)
    def test_full_inventory_not_false_data_coverage(self):
        roster=self.report['roster']
        self.assertEqual(len(roster['draft_roster']),17)
        self.assertEqual(sum(p['statistical_data_bundled'] for p in roster['draft_roster']),3)
        self.assertIsNone(roster['reported_additions'][0]['acquisition_week'])
        self.assertFalse(roster['observed_team_result']['algorithm_attribution'])
    def test_checksum(self):self.assertEqual(self.repo.sha256,self.report['data']['manifest']['sha256'])
    def test_train_test_sizes(self):
        self.assertEqual(self.report['training']['n'],25)
        self.assertEqual(self.report['later_evaluation']['n'],23)
    def test_cutoffs(self):
        self.assertEqual(self.report['fit']['max_training_outcome_week'],10)
        self.assertTrue(all(r['history_end']<r['week'] for r in self.report['player_forecasts']))
        self.assertTrue(all(r['week']<18 for r in self.report['player_forecasts']))
    def test_missing_outcomes_not_zero(self):
        rows={(r['id'],r['week']) for r in self.report['player_forecasts']}
        self.assertNotIn(('stevenson',9),rows)
        self.assertTrue(any(x['id']=='stevenson' and x['week']==9 for x in self.report['omitted']))
    def test_bye_exclusions(self):
        self.assertTrue(any(x['id']=='stevenson' and x['week']==14 and 'bye' in x['reason'] for x in self.report['omitted']))
    def test_all_methods_share_cohort(self):
        self.assertEqual({m['n'] for m in self.report['later_evaluation']['methods'].values()},{23})
    def test_model_unchanged(self):
        r=self.report
        self.assertEqual(r['parameters']['original_recent_blend'],.65)
        by_key={(p['id'],p['week']):p for p in r['player_forecasts']}
        for p in project(self.repo,2025,17,'ppr'):
            self.assertEqual(p['projection'],by_key[p['id'],17]['original'])
    def test_closed_form_fit(self):
        rows=[{'week':4,'history':0.,'recent_weighted':2.,'actual':1.},
              {'week':5,'history':10.,'recent_weighted':14.,'actual':12.}]
        self.assertAlmostEqual(fit_blend(rows)['alpha'],.5)
    def test_fit_ignores_late_outcome(self):
        rows=self.report['player_forecasts']
        changed=[dict(r,actual=1000 if r['week']>10 else r['actual']) for r in rows]
        self.assertEqual(fit_blend(rows),fit_blend(changed))
    def test_fit_zero_denominator(self):
        self.assertTrue(fit_blend([{'week':4,'history':5,'recent_weighted':5,'actual':9}])['fallback'])
    def test_empty_training_rejected(self):
        with self.assertRaises(DataError):fit_blend([])
    def test_alpha_bounds(self):
        rows=[{'week':4,'history':5,'recent_weighted':7,'actual':100}]
        self.assertEqual(fit_blend(rows)['alpha'],1)
        with self.assertRaises(DataError):add_fitted([],1.1)
    def test_original_pair_choices_include_losses(self):
        r=self.report['pair_case']
        self.assertEqual([w['decisions']['original']['id'] for w in r['weeks']],['montgomery','montgomery','stevenson'])
        self.assertEqual(r['correct_weekly_choices']['original'],1)
        self.assertAlmostEqual(r['totals']['original'],37.8)
        self.assertAlmostEqual(r['totals']['always_stevenson'],55.7)
        self.assertAlmostEqual(r['totals']['last_game'],54.2)
    def test_actual_difference_not_projected_difference(self):
        w=self.report['pair_case']['weeks'][-1]
        m,s=w['players']
        self.assertAlmostEqual(s['actual']-m['actual'],21.2)
        self.assertAlmostEqual(s['original']-m['original'],2.5038)
    def test_unknown_addition_date_is_scenario_input(self):
        r=build_report(acquisition_week=17)['pair_case']
        self.assertEqual(r['n'],1)
        self.assertEqual(len(r['skipped']),2)
    def test_invalid_acquisition(self):
        for v in (14,18,True,'15',None):
            with self.assertRaises(DataError):build_report(acquisition_week=v)
    def test_invalid_scoring(self):
        with self.assertRaises(DataError):build_report(scoring='bonus')
    def test_half_scoring_is_recomputed(self):
        h=build_report(scoring='half')
        s=next(p for p in h['player_forecasts'] if p['id']=='stevenson' and p['week']==17)
        self.assertAlmostEqual(s['actual'],24.7)
        self.assertNotEqual(h['later_evaluation']['methods']['original']['rmse'],self.report['later_evaluation']['methods']['original']['rmse'])
    def test_target_week_points_do_not_enter_target_forecast(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'changed.csv'
            games=[replace(g,standard_points=99) if g.week>=17 else g for g in self.repo.games]
            write_games(games,path)
            a=project(self.repo,2025,17,'ppr');b=project(Repository(path),2025,17,'ppr')
            self.assertEqual(a,b)
    def test_future_poison_does_not_change_fit_or_earlier_forecasts(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'changed.csv'
            games=[replace(g,standard_points=99) if g.week>10 else g for g in self.repo.games]
            write_games(games,path)
            other=build_report(data_path=path)
            self.assertEqual(other['fit'],self.report['fit'])
            self.assertEqual([r for r in other['player_forecasts'] if r['week']<=10],
                             [r for r in self.report['player_forecasts'] if r['week']<=10])
    def test_reproducible_report(self):self.assertEqual(build_report(),self.report)
    def test_json_finite(self):json.dumps(self.report,allow_nan=False)
    def test_pair_missing_row_not_silently_zero(self):
        rows=[r for r in self.report['player_forecasts'] if not(r['id']=='stevenson' and r['week']==16)]
        r=pair_case(rows,15)
        self.assertEqual(r['n'],2)
        self.assertEqual(r['skipped'][0]['week'],16)
    def test_subset_unique_players(self):
        for w in self.report['three_rb_case']:
            for r in w['methods'].values():self.assertEqual(len(set(r['selected'])),3)

if __name__=='__main__':unittest.main()
