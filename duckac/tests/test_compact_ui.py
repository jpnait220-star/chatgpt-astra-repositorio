"""Static UI regression for compact, centered DuckAC controls."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from duckac import W,H
class CompactUITests(unittest.TestCase):
    def test_compact_geometry(self):
        self.assertEqual((W,H),(560,592))
    def test_images_only_for_icon_and_mouse(self):
        assets=Path(__file__).resolve().parents[1]/'assets'
        for p in ('duckac.png','duckac.ico','duckac-alternativo.png','mouse-glow-small.png'):
            self.assertTrue((assets/p).is_file(),p)
