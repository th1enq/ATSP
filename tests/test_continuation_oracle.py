import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from continuation_oracle import separate_step


class ContinuationOracleTest(unittest.TestCase):
    def setUp(self):
        self.edges = [(0, 1), (0, 2), (1, 2)]
        self.args = (3, self.edges, [True]*3, [F(1)]*3,
                     F(1), F(1, 64), F(1, 4), F(1))
        # Reduced Laplacian of the triangle is [[2,-1],[-1,2]].
        self.good = {"Y:0:0": F(4), "Y:0:1": F(-2), "Y:1:1": F(4),
                     "z:0": F(1), "z:1": F(1), "z:2": F(1)}

    def check_cut(self, point, expected_reason):
        cut = separate_step(*self.args, point)
        self.assertIsNotNone(cut)
        self.assertIn(expected_reason, cut.reason)
        self.assertLess(cut.value(point), 0)
        self.assertGreaterEqual(cut.value(self.good), 0)

    def test_feasible_and_scalar_cuts(self):
        self.assertIsNone(separate_step(*self.args, self.good))
        point = self.good | {"z:0": F(3)}
        self.check_cut(point, "z upper")
        point = self.good | {"lambda:0:1:2": F(-1)}
        self.check_cut(point, "lower bound")

    def test_psd_cuts(self):
        point = self.good | {"Y:0:0": F(0), "Y:0:1": F(0), "Y:1:1": F(0)}
        self.check_cut(point, "Y >=")
        point = self.good | {"Y:0:0": F(10), "Y:1:1": F(10)}
        self.check_cut(point, "3L_H")
        point = self.good | {"y:0": F(1)}
        self.check_cut(point, "response LMI")

    def test_partition_cut(self):
        point = self.good | {"z:0": F(0), "z:1": F(0), "z:2": F(0)}
        self.check_cut(point, "partition")


if __name__ == "__main__":
    unittest.main()
