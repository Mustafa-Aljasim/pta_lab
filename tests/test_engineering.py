import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from superposition import (Reservoir, unit_response, rate_increments, pressure_history,
                           horner, buildup_superposition_function)
from diagnostics import signature, bourdet_derivative
from educational_content import MODELS
from well_tests import SCHEDULES, test_history, status_at, well_svg, history_figure


class EngineeringTests(unittest.TestCase):
    def test_rate_increments_and_constant_rate_limit(self):
        np.testing.assert_array_equal(rate_increments([500, 300, 0]), [500, -200, -300])
        t = np.geomspace(.001, 200, 100)
        p, parts = pressure_history(t, [0, 24, 72], [500, 500, 500])
        np.testing.assert_allclose(p, 4000 - 500 * unit_response(t))
        np.testing.assert_array_equal(parts[1:], 0)

    def test_kernel_causality_and_known_field_units(self):
        self.assertEqual(float(unit_response(0)), 0)
        self.assertEqual(float(unit_response(-1)), 0)
        self.assertTrue(np.isfinite(unit_response([1e-300, 1e-12, 1e9])).all())
        # Independently tabulated petroleum field-unit E1 expression (rounded constants).
        from scipy.special import exp1
        r = Reservoir()
        u = 948 * r.porosity * r.viscosity_cp * r.compressibility_psi * r.radius_ft**2 / (r.permeability_md * 24)
        expected = 70.6 * r.volume_factor * r.viscosity_cp / (r.permeability_md * r.thickness_ft) * exp1(u)
        self.assertAlmostEqual(float(unit_response(24)) / expected, 1, delta=.001)

    def test_superposition_linearity_and_activation(self):
        times = np.array([0, 12, 24, 25, 72, 100])
        p, parts = pressure_history(times, [0, 24, 72], [500, 300, 0])
        p2, _ = pressure_history(times, [0, 24, 72], [1000, 600, 0])
        np.testing.assert_allclose(4000 - p2, 2 * (4000 - p))
        np.testing.assert_array_equal(parts[1, :3], 0)
        np.testing.assert_allclose(p, 4000 - parts.sum(axis=0))

    def test_buildup_and_falloff_recovery(self):
        t = 24 + np.geomspace(.001, 1e5, 200)
        p, _ = pressure_history(t, [0, 24], [500, 0])
        inj, _ = pressure_history(t, [0, 24], [-500, 0])
        self.assertTrue(np.all(np.diff(p) > 0))
        self.assertTrue(np.all(np.diff(inj) < 0))
        self.assertTrue(np.all(p < 4000))
        self.assertTrue(np.all(inj > 4000))
        self.assertLess(abs(p[-1] - 4000), .01)

    def test_horner_and_normalized_time_constant_rate(self):
        H, logH, te = horner(24, 6)
        np.testing.assert_allclose([H, logH, te], [5, np.log10(5), 4.8])
        t = 24 + np.geomspace(.01, 100, 50)
        F, terms = buildup_superposition_function(t, [0, 24], [500, 0])
        np.testing.assert_allclose(F, np.log(t / (t - 24)), atol=1e-12)
        np.testing.assert_allclose(F, terms.sum(axis=0))

    def test_multirate_log_time_is_consistent_with_radial_limit(self):
        t = 72 + np.geomspace(1, 1000, 100)
        F, _ = buildup_superposition_function(t, [0, 24, 72], [500, 300, 0])
        p, _ = pressure_history(t, [0, 24, 72], [500, 300, 0])
        coefficient = float(unit_response(1e6) - unit_response(1e6 / np.e))
        np.testing.assert_allclose(4000 - p, 300 * coefficient * F, rtol=1e-4)

    def test_bourdet_unequal_intervals(self):
        t = np.exp(np.array([-3, -2.1, -.3, .4, 3, 4.3]))
        x = np.log(t)
        np.testing.assert_allclose(bourdet_derivative(t, 2*x + 7), 2)
        np.testing.assert_allclose(bourdet_derivative(t, x*x)[1:-1], 2*x[1:-1], atol=1e-12)

    def test_catalog_is_positive_and_characteristic_slopes_match(self):
        self.assertEqual(len(MODELS), 17)
        for model_id, model in MODELS.items():
            with self.subTest(model=model_id):
                secondary = .1 if model_id.startswith("dual") else 90 if model_id == "intersecting" else 1
                t, p, d, mask = signature(model_id, 1, secondary)
                self.assertTrue(np.all(np.isfinite(p)) and np.all(p > 0))
                self.assertTrue(np.all(np.isfinite(d)) and np.all(d > 0))
                self.assertGreater(mask.sum(), 5)
                self.assertTrue(np.all(np.diff(p) > 0))
                if model["expected_derivative_slope"] is not None:
                    local = np.gradient(np.log(d), np.log(t))
                    self.assertAlmostEqual(np.median(local[mask]), model["expected_derivative_slope"], delta=.035)

    def test_sensitivity_changes_signature_and_storage_timing(self):
        for model_id in MODELS:
            second = .1 if model_id.startswith("dual") else 90 if model_id == "intersecting" else 1
            _, _, d1, _ = signature(model_id, .3, second)
            _, _, d2, _ = signature(model_id, 4, second)
            # A composite with equal mobilities intentionally has no interface signature.
            if model_id == "composite":
                _, _, d1, _ = signature(model_id, .3, .5)
                _, _, d2, _ = signature(model_id, 4, .5)
            self.assertFalse(np.allclose(d1, d2), model_id)
        t, _, low, _ = signature("storage", .3)
        _, _, high, _ = signature("storage", 4)
        self.assertGreater(t[np.argmax(high >= .25)], t[np.argmax(low >= .25)])

    def test_operational_histories_and_time_markers(self):
        for name, (starts, rates, end) in SCHEDULES.items():
            with self.subTest(test=name):
                t, q, p = test_history(name)
                self.assertTrue(np.all(np.isfinite(p)))
                for start, rate in zip(starts, rates):
                    state, observed_rate = status_at(name, start)
                    self.assertEqual(observed_rate, rate)
                    self.assertIn(state, well_svg(state))
                before, _ = history_figure(name, end * .2)
                after, _ = history_figure(name, end * .8)
                self.assertNotEqual(before.data[2].x[0], after.data[2].x[0])
        t, _, p = test_history("Interference / Pulse Testing")
        self.assertTrue(np.all(p[t <= 8] == 4000))
        self.assertLess(p[-1], 4000)

    def test_invalid_inputs_are_rejected(self):
        for call in [lambda: horner(24, 0), lambda: Reservoir(porosity=1.5),
                     lambda: pressure_history([1], [0, 0], [500, 0]),
                     lambda: buildup_superposition_function([72], [0, 72], [500, 0]),
                     lambda: bourdet_derivative([0, 1, 2], [1, 2, 3])]:
            with self.assertRaises(ValueError):
                call()


if __name__ == "__main__":
    unittest.main()
