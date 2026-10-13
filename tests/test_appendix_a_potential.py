import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from appendix_a_potential import AppendixAPotential, cube_root_interval
from appendix_a_signing import AppendixASigner


class AppendixAPotentialTest(unittest.TestCase):
    def test_cube_root_enclosure(self):
        low, high = cube_root_interval(F(1, 2), F(1, 1000))
        self.assertLessEqual(low**3, F(1, 2))
        self.assertGreaterEqual(high**3, F(1, 2))
        self.assertLessEqual(high-low, F(1, 1000))

    def test_normalization_and_sign_folding(self):
        potential = AppendixAPotential([[[F(-2)]], [[F(1)]], [[F(0)]]])
        self.assertEqual(sum((a[0][0] for a in potential.a), F()), 1)
        self.assertLessEqual(potential.nu, F(1001, 1000)*F(5, 9))
        self.assertEqual(potential.fold_signs([1, -1]), [-1, -1, 1])

    def test_scalar_end_to_end(self):
        result = AppendixASigner([[[F(1)]]]).sign(max_steps=2)
        self.assertEqual(len(result.signs), 1)
        self.assertLessEqual(result.steps, 2)
        self.assertEqual(result.spectral_bound_squared, 1600)

    def test_finite_difference_and_curvature_direction(self):
        signer = AppendixASigner([[[F(1, 2)]], [[F(1, 2)]]])
        signer._value = lambda x, accuracy: x[0]**2 + 3*x[0]*x[1] - x[1]**2
        gradient, hessian = signer._stencil([F(0), F(0)], [0, 1])
        self.assertEqual(gradient, [0, 0])
        self.assertEqual(hessian, [[2, 3], [3, -2]])
        q = signer._curvature_step([[F(-8)*signer.a]])
        self.assertIsNotNone(q)
        self.assertNotEqual(q[0], 0)
        self.assertLessEqual(q[0]*q[0], signer.s*signer.s)


if __name__ == "__main__":
    unittest.main()
