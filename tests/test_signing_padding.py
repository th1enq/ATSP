import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from signing_certificate import check_signing
from signing_padding import pad_to_identity, prepare_stacked_columns
from continuation_state import initial_state
from rational_frame import find_frame_weights


class SigningPaddingTest(unittest.TestCase):
    def test_exact_identity_completion(self):
        columns, data_count = pad_to_identity([[F(1, 2), F(0)],
                                               [F(0), F(1, 2)]], 2)
        self.assertEqual(data_count, 2)
        self.assertGreater(len(columns), data_count)
        self.assertTrue(check_signing(columns, [1]*len(columns), F(1)))
        with self.assertRaisesRegex(ValueError, "exceeds identity"):
            pad_to_identity([[F(2)]], 2)

    def test_shortcut_to_padded_identity(self):
        state = initial_state(2, [(0, 1)], 1, F(1))
        edges = [0]
        weights, scores, _ = find_frame_weights(2, state.edges, 1, 1)
        data = prepare_stacked_columns(state, edges, weights, 8)
        self.assertEqual(len(data), 1)
        self.assertEqual(len(data[0]), 2)
        padded, count = pad_to_identity(data, 1)
        self.assertEqual(count, 1)
        self.assertTrue(check_signing(padded, [1]*len(padded), F(1)))


if __name__ == "__main__":
    unittest.main()
