import unittest
from dataclasses import replace
from fourth_down.data import load_games, ROOT
from fourth_down.research import examples, fit, predict, build_report

class ResearchTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.games = load_games(ROOT / 'data/research/2024.csv')
        cls.report, cls.rows = build_report()

    def test_chronological_features_ignore_target_and_future(self):
        before = [r for r in examples(self.games) if r['week'] <= 10]
        poisoned = [replace(g, standard_points=g.standard_points + 20) if g.week >= 10 else g for g in self.games]
        after = [r for r in examples(poisoned) if r['week'] <= 10]
        self.assertEqual([(r['id'], r['week'], r['x']) for r in before], [(r['id'], r['week'], r['x']) for r in after])
        self.assertTrue(all((r['history_end'] < r['week'] for r in self.rows)))

    def test_scaled_ridge_learns_synthetic_linear_signal(self):
        rows = [{'x': [float(i), float(i % 7), float(i % 3), float(i % 5), float(i % 11), float(i % 13), float(i % 2), float(i % 4), float(i % 6)], 'actual': 3 + 2 * i} for i in range(100)]
        m = fit(rows, 1e-05)
        self.assertLess(abs(predict(m, rows[60]['x']) - 123), 0.01)

    def test_selection_and_evaluation_are_separate(self):
        train = examples(load_games(ROOT / 'data/research/2022.csv'))
        validation = examples(load_games(ROOT / 'data/research/2023.csv'))
        self.assertEqual({r['season'] for r in train}, {2022})
        self.assertEqual({r['season'] for r in validation}, {2023})
        self.assertEqual({r['season'] for r in self.rows}, {2024})
        self.assertEqual(self.report['selected_lambda'], min(self.report['validation'], key=lambda r: (r['mae'], r['lambda']))['lambda'])
        self.assertEqual(self.report['model'], fit(train + validation, self.report['selected_lambda']))

    def test_all_methods_score_identical_observations(self):
        self.assertEqual({v['n'] for v in self.report['overall'].values()}, {len(self.rows)})
        self.assertEqual(len({(r['id'], r['season'], r['week']) for r in self.rows}), len(self.rows))

    def test_manifest_and_report_reproduce(self):
        import json
        saved = json.loads((ROOT / 'reports/research.json').read_text())
        self.assertEqual(saved['overall'], self.report['overall'])
        self.assertEqual(saved['cohorts'], self.report['cohorts'])
        self.assertEqual(saved['selected_lambda'], self.report['selected_lambda'])
        for a, b in zip(saved['model']['coefficients'], self.report['model']['coefficients']):
            self.assertAlmostEqual(a, b, places=8)

    def test_uncertainty_contains_zero_no_superiority_claim(self):
        ci = self.report['uncertainty']
        self.assertLess(ci['lower'], 0)
        self.assertGreater(ci['upper'], 0)

    def test_extension_uses_identical_frozen_model(self):
        for year in (2025, 2026):
            actual = [r for r in self.report['additional_predictions'] if r['season'] == year]
            self.assertTrue(actual)
            for r in actual:
                self.assertAlmostEqual(r['ridge'], predict(self.report['model'], r['x']), places=10)
                self.assertLess(r['history_end'], r['week'])
            counts = {m['n'] for m in self.report['season_results'][str(year)]['overall'].values()}
            self.assertEqual(counts, {len(actual)})

    def test_partial_season_and_saved_extension_reproduce(self):
        import json
        saved = json.loads((ROOT / 'reports/research.json').read_text())
        self.assertEqual(saved['season_results'], self.report['season_results'])
        latest = self.report['season_results']['2026']
        self.assertTrue(latest['partial'])
        self.assertEqual(latest['last_week'], 4)
        self.assertEqual([w['week'] for w in latest['by_week']], [4])
