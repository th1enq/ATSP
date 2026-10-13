import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from deterministic_signing import (sign_by_frobenius, sign_stacked_data,
                                   sign_stacked_data_appendix_a)
from signing_certificate import check_signing
from signing_padding import pad_to_identity


class DeterministicSigningTest(unittest.TestCase):
    def test_balanced_axis_frame(self):
        half = F(1, 2)
        # Two copies of each coordinate, each with squared norm 1/2.
        # Rational four-copy version: each axis has four columns of length 1/2.
        columns = [[half, F(0)]]*4 + [[F(0), half]]*4
        result = sign_by_frobenius(columns)
        self.assertTrue(result.frobenius_guaranteed)
        self.assertTrue(check_signing(columns, result.signs, result.spectral_bound))
        self.assertEqual(result.signs[:4], [1, -1, 1, -1])

    def test_padded_identity(self):
        data = [[F(1, 2), F(0)], [F(0), F(1, 2)]]
        columns, count = pad_to_identity(data, 1)
        result = sign_by_frobenius(columns)
        self.assertTrue(result.frobenius_guaranteed)
        self.assertEqual(len(result.signs), len(columns))
        compact, residual_count = sign_stacked_data(data, 1)
        self.assertEqual(len(columns), len(data) + 4*residual_count)
        padding_signs = [1, -1, 1, -1]*residual_count
        self.assertTrue(check_signing(columns, compact.signs + padding_signs,
                                      compact.spectral_bound))

    def test_appendix_a_stacked_scalar(self):
        data = [[F(1, 2)]]
        result, residual_count = sign_stacked_data_appendix_a(data, 1, max_steps=2)
        self.assertEqual(len(result.signs), 1)
        self.assertGreaterEqual(residual_count, 1)
        self.assertTrue(check_signing(data, result.signs, result.spectral_bound,
                                      require_identity=False))


if __name__ == "__main__":
    unittest.main()
