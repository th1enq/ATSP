import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from rational_ellipsoid import FeasibilityError, IterationLimitReached, find_feasible


class RationalEllipsoidTest(unittest.TestCase):
    def test_translated_box(self):
        cuts = [(F(-1), [F(1), F(0)]), (F(2), [F(-1), F(0)]),
                (F(-1), [F(0), F(1)]), (F(2), [F(0), F(-1)])]

        def separate(point):
            return next(((c, a) for c, a in cuts
                         if c + sum((x*y for x, y in zip(a, point)), F()) < 0), None)

        point, iterations = find_feasible(2, separate, F(10), F(1, 4))
        self.assertGreater(iterations, 0)
        self.assertTrue(all(F(1) <= x <= F(2) for x in point))

    def test_bad_oracle_detected(self):
        with self.assertRaisesRegex(FeasibilityError, "did not return"):
            find_feasible(2, lambda point: (F(1), [F(0), F(0)]), F(10), F(1, 4))

    def test_operational_budget_has_no_volume_conclusion(self):
        with self.assertRaises(IterationLimitReached):
            find_feasible(2, lambda point: (F(-1), [F(1), F(0)]),
                          F(10), F(1, 4), max_iterations=0)


if __name__ == "__main__":
    unittest.main()
