import sys
import unittest
from fractions import Fraction as F
from pathlib import Path
import random

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from appendix_a_value_oracle import AppendixASDP
from exact_psd import psd_or_negative_vector, quadratic_form
from rational_ellipsoid import IterationLimitReached


class AppendixAValueOracleTest(unittest.TestCase):
    def test_schur_separator(self):
        sdp = AppendixASDP([[[F(1)]]], [F(0)], [F(1)], F(1))
        feasible = [F(50), F(1, 20), F(1, 20)]
        self.assertIsNone(sdp.separate(feasible))
        point = [F(1), F(1), F(1)]
        cut = sdp.separate(point)
        self.assertIsNotNone(cut)
        constant, coefficients = cut
        self.assertLess(constant + sum((a*b for a, b in zip(coefficients, point)), F()), 0)
        self.assertGreaterEqual(constant + sum((a*b for a, b in zip(coefficients, feasible)), F()), 0)

    def test_scalar_optimum_interval(self):
        # psi=0 gives min_{t,X,Y} t+X+Y with X,Y >= 1/t: 2 sqrt(2).
        sdp = AppendixASDP([[[F(1)]]], [F(0)], [F(0)], F(1))
        result = sdp.value_interval(F(1, 64))
        self.assertLessEqual(result.upper - result.lower, F(1, 64))
        self.assertLessEqual(result.lower*result.lower, 8)
        self.assertGreaterEqual(result.upper*result.upper, 8)
        self.assertIsNone(sdp.separate(result.optimizer))
        self.assertEqual(result.upper, sdp.objective_value(result.optimizer))

    def test_normalization_required(self):
        with self.assertRaisesRegex(ValueError, "total trace one"):
            AppendixASDP([[[F(1, 2)]]], [F(0)], [F(0)], F(1))

    def test_iteration_budget_is_not_an_sdp_lower_bound(self):
        sdp = AppendixASDP([[[F(1,2),F(0)],[F(0),F(0)]],
                           [[F(1,4),F(1,4)],[F(1,4),F(1,4)]]],
                          [F(0),F(0)], [F(1),F(1)], F(1,3))
        with self.assertRaises(IterationLimitReached):
            sdp.value_interval(F(1,64), max_feasibility_iterations=0)

    def test_sparse_separator_matches_dense_exact_cuts(self):
        sdp = AppendixASDP([[[F(1,2),F(0)],[F(0),F(0)]],
                           [[F(1,4),F(1,4)],[F(1,4),F(1,4)]]],
                          [F(1,3),F(-1,2)], [F(2,3),F(1,4)], F(1,3))
        rng = random.Random(71)
        points = [sdp.strict_reference_point()]
        points += [[F(rng.randrange(-2,10),7) for _ in sdp.keys] for _ in range(30)]
        for point in points:
            if point[0] < 0:
                expected = F(), [F(int(i==0)) for i in range(sdp.dimension)]
            else:
                expected = None
                for constant,coefficients in sdp.lmis:
                    size = len(constant)
                    matrix = [[constant[i][j]+sum((point[k]*c[i][j]
                               for k,c in enumerate(coefficients)),F())
                               for j in range(size)] for i in range(size)]
                    good,witness = psd_or_negative_vector(matrix)
                    if not good:
                        expected = quadratic_form(constant,witness), [quadratic_form(c,witness) for c in coefficients]
                        break
            self.assertEqual(sdp.separate(point),expected)


if __name__ == "__main__":
    unittest.main()
