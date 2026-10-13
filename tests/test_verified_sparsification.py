import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from continuation_state import initial_state
from verified_sparsification import (automatic_sparsification_step,
                                     verify_shortcut_cone, verify_sparsification)


class VerifiedSparsificationTest(unittest.TestCase):
    def test_parallel_edge_certificate(self):
        state = initial_state(2, [(0, 1)]*8, 8, F(1))
        state.s = F(2)
        union = [[e] for e in range(8)]
        self.assertTrue(verify_shortcut_cone(state))
        certificate = verify_sparsification(state, union, [0, 1, 2, 3], F(0))
        self.assertEqual(certificate.r_next, 4)
        self.assertEqual(certificate.cut_load_factor, F(1, 2))
        with self.assertRaisesRegex(ValueError, "spectral"):
            verify_sparsification(state, union, list(range(8)), F(0))
        automatic = automatic_sparsification_step(state, union)
        self.assertEqual(automatic.certificate.r_next, 4)
        self.assertEqual(len(automatic.certificate.selected_edges), 4)
        self.assertTrue(automatic.signing.frobenius_guaranteed)


if __name__ == "__main__":
    unittest.main()
