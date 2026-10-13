import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from signing_certificate import check_signing


class SigningCertificateTest(unittest.TestCase):
    def test_exact_discrepancy(self):
        columns = [[F(1), F(0)], [F(0), F(1)]]
        self.assertTrue(check_signing(columns, [1, -1], F(1)))
        self.assertFalse(check_signing(columns, [1, -1], F(1, 2)))
        with self.assertRaisesRegex(ValueError, "sum to identity"):
            check_signing([[F(1, 2), F(0)]], [1], F(1))


if __name__ == "__main__":
    unittest.main()
