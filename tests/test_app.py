"""Exercise every lesson selector and form through Streamlit's native test harness."""
import sys
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from educational_content import MODULES, WELL_TESTS, MODELS


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()

    def assert_clean(self):
        self.assertEqual(len(self.app.exception), 0, str(self.app.exception))

    def select_module(self, index):
        self.app.sidebar.radio[0].set_value(MODULES[index]).run()
        self.assert_clean()

    def test_default_and_all_well_tests(self):
        self.assertEqual(self.app.selectbox[0].value, "Pressure Buildup")
        self.assertEqual(self.app.sidebar.radio[0].value, MODULES[0])
        for name in WELL_TESTS:
            self.app.selectbox[0].set_value(name).run()
            self.assert_clean()
            if self.app.slider:
                slider = self.app.slider[0]
                slider.set_value(float(slider.max)).run()
                self.assert_clean()
            elif self.app.select_slider:
                self.app.select_slider[0].set_value(self.app.select_slider[0].options[-1]).run()
                self.assert_clean()

    def test_all_diagnostic_selectors_and_controls(self):
        self.select_module(1)
        for category in ["Early Time", "Middle Time", "Late Time"]:
            self.app.radio[0].set_value(category).run()
            for key, model in MODELS.items():
                if model["category"] != category:
                    continue
                self.app.selectbox[0].set_value(key).run()
                self.assert_clean()
                self.app.slider[0].set_value(self.app.slider[0].max).run()
                self.assert_clean()
        self.app.toggle[0].set_value(False).run()
        self.assert_clean()

    def test_all_superposition_experiments(self):
        self.select_module(2)
        for option in self.app.selectbox[0].options:
            self.app.selectbox[0].set_value(option).run()
            self.assert_clean()
            if self.app.slider:
                self.app.slider[0].set_value(self.app.slider[0].max).run()
                self.assert_clean()
            if option.startswith("B"):
                self.app.radio[0].set_value(2).run()
                self.assert_clean()
            if option.startswith("D"):
                self.app.number_input[1].set_value(.01).run()
                self.assert_clean()

    def test_exercises_submit_and_reveal_feedback(self):
        self.select_module(3)
        self.app.selectbox[1].set_value("A")
        self.app.selectbox[2].set_value("C")
        self.app.button[0].click().run()
        self.assert_clean()
        self.assertTrue(self.app.success)
        self.app.selectbox[0].set_value("2 · Boundary interpretation").run()
        self.app.multiselect[0].set_value(["A sealing boundary", "Lower outer-region mobility"]).run()
        self.app.button[0].click().run()
        self.assert_clean()
        self.assertTrue(self.app.info)
        self.app.selectbox[0].set_value("3 · Superposition rate changes").run()
        for control, value in zip(self.app.number_input, [500, -200, -300]):
            control.set_value(value)
        self.app.button[0].click().run()
        self.assert_clean()
        self.assertTrue(self.app.success)


if __name__ == "__main__":
    unittest.main()
