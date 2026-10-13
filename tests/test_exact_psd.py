import random
import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from exact_psd import psd_or_negative_vector, quadratic_form, rational_psd_columns


class ExactPSDTest(unittest.TestCase):
    def test_zero_pivot_and_negative_witness(self):
        for matrix in ([[0, 1], [1, 0]], [[1, 2], [2, 1]],
                       [[1, 0, 0], [0, 0, 2], [0, 2, 1]]):
            okay, witness = psd_or_negative_vector(matrix)
            self.assertFalse(okay)
            self.assertLess(quadratic_form(matrix, witness), 0)

    def test_random_rational_gram_matrices(self):
        rng = random.Random(20261008)
        for n in range(1, 7):
            for _ in range(20):
                rows = [[Fraction(rng.randrange(-5, 6), rng.randrange(1, 8))
                         for _ in range(n)] for _ in range(n - 1)]
                gram = [[sum((row[i] * row[j] for row in rows), Fraction())
                         for j in range(n)] for i in range(n)]
                self.assertEqual(psd_or_negative_vector(gram), (True, None))
                gram[0][0] -= 100
                okay, witness = psd_or_negative_vector(gram)
                self.assertFalse(okay)
                self.assertLess(quadratic_form(gram, witness), 0)

    def test_reject_nonsymmetric(self):
        with self.assertRaises(ValueError):
            psd_or_negative_vector([[1, 2], [1, 1]])

    def test_rational_psd_decomposition(self):
        rng = random.Random(20261009)
        for n in range(1, 6):
            for _ in range(12):
                vectors = [[Fraction(rng.randrange(-4, 5), rng.randrange(1, 6))
                            for _ in range(n)] for _ in range(n - 1)]
                matrix = [[sum((v[i]*v[j] for v in vectors), Fraction())
                           for j in range(n)] for i in range(n)]
                columns = rational_psd_columns(matrix)
                rebuilt = [[sum((v[i]*v[j] for v in columns), Fraction())
                            for j in range(n)] for i in range(n)]
                self.assertEqual(rebuilt, matrix)
        self.assertEqual(rational_psd_columns([[0, 0], [0, 0]]), [])
        with self.assertRaisesRegex(ValueError, "not positive semidefinite"):
            rational_psd_columns([[1, 2], [2, 1]])


if __name__ == "__main__":
    unittest.main()
