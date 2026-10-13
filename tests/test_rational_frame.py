import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from rational_frame import (approximate_frame_columns, exp_rational_lower,
                            find_balanced_frame_weights, find_frame_weights, leverage_scores)


class RationalFrameTest(unittest.TestCase):
    def test_experimental_balancing_has_exact_leverage_certificate(self):
        edges = 15*[(0, 1), (1, 2)] + [(0, 2), (1, 2)]
        weights, scores, iterations = find_balanced_frame_weights(3, edges, 16, 16)
        self.assertGreater(iterations, 0)
        self.assertTrue(all(w > 0 for w in weights))
        self.assertEqual(leverage_scores(3, edges, weights), scores)
        self.assertEqual(sum(scores), 2)
        self.assertLessEqual(max(scores), F(5, 64))

    def test_rational_exponential_bounds(self):
        for x in (F(-7, 3), F(-1, 100), F(0), F(3, 2), F(11)):
            lower = exp_rational_lower(x, F(1, 1000))
            self.assertGreater(lower, 0)
            # Float is only a test reference; the routine uses exact Taylor
            # remainder bounds to enclose the true exponential.
            from math import exp
            self.assertLessEqual(float(lower), exp(float(x))*(1+1e-12))
            self.assertGreaterEqual(float(lower)*1.001, exp(float(x))*(1-1e-12))

    def test_nonuniform_tree_packing(self):
        edges = 7*[(0, 1), (1, 2)] + [(0, 2), (1, 2)]
        weights, scores, iterations = find_frame_weights(3, edges, 8, 8,
                                                          max_iterations=5000)
        self.assertGreater(iterations, 0)
        self.assertEqual(sum(scores), 2)
        self.assertEqual(leverage_scores(3, edges, weights), scores)
        self.assertLessEqual(max(scores), F(1+F(4, 8), 8))
        columns = approximate_frame_columns(3, edges, weights, 24)
        gram = [[sum((z[i]*z[j] for z in columns), F()) for j in range(2)]
                for i in range(2)]
        self.assertTrue(all(abs(gram[i][j] - int(i == j)) < F(1, 2**18)
                            for i in range(2) for j in range(2)))


if __name__ == "__main__":
    unittest.main()
