from pathlib import Path
import tempfile
import unittest
from glance_guard.settings import Settings

class SettingsTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"settings.json"
            original=Settings(camera=2,calibration=[1,2,.5,.6])
            original.save(path)
            self.assertEqual(Settings.load(path),original)
            self.assertFalse(path.with_suffix(".tmp").exists())
    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(Settings.load(Path(folder)/"missing.json"),Settings())
    def test_validation(self):
        for settings in [Settings(fps=0),Settings(away_delay=-1),Settings(camera=-1),
                         Settings(calibration=[1]),Settings(calibration=[0,0,float("nan"),0]),
                         Settings(appearance="transparent"),Settings(startup="yes")]:
            with self.assertRaises(ValueError):
                settings.validate()
    def test_corrupt_settings(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"settings.json"; path.write_text("bad json")
            with self.assertRaises(ValueError):
                Settings.load(path)
