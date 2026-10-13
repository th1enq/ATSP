import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from continuation_state import initial_state


class ContinuationStateTest(unittest.TestCase):
    def test_exact_one_step(self):
        edges = [(0, 1), (0, 2), (1, 2)]
        state = initial_state(3, edges, 1, F(1))
        self.assertEqual(state.ramp(), [F(1)]*3)
        response = {"Y:0:0": F(4), "Y:0:1": F(-2), "Y:1:1": F(4),
                    "z:0": F(1), "z:1": F(1), "z:2": F(1)}
        successor = state.advance(response)
        self.assertEqual(successor.s, F(1, 2)*(1 + state.t))
        self.assertEqual(successor.q, F(1)-2*state.t)
        self.assertTrue(successor.verify_invariant())

    def test_invalid_response(self):
        edges = [(0, 1), (0, 2), (1, 2)]
        state = initial_state(3, edges, 1, F(1))
        with self.assertRaisesRegex(ValueError, "invalid response"):
            state.advance({})
        with self.assertRaisesRegex(ValueError, "required tree packing"):
            initial_state(3, edges, 2, F(1))


if __name__ == "__main__":
    unittest.main()
