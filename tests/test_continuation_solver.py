import sys
import unittest
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from continuation_solver import dyadic_g, finalize_shortcut, solve_response
from continuation_state import initial_state


class ContinuationSolverTest(unittest.TestCase):
    def test_exact_response_and_transition(self):
        state = initial_state(2, [(0, 1)]*3, 1, dyadic_g(1))
        response, cuts = solve_response(state, max_iterations=2000)
        self.assertEqual(cuts, 0)  # The analytic proposal passed the full oracle.
        self.assertTrue(state.advance(response).verify_invariant())

    def test_terminal_packing(self):
        state = initial_state(2, [(0, 1)]*3, 1, F(1))
        state.s = F(1)
        state.q = F(2)
        active, trees = finalize_shortcut(state)
        self.assertEqual(len(active), 3)
        self.assertEqual(len(trees), 1)
        self.assertEqual(len(trees[0]), 1)

    def test_dyadic_parameter(self):
        self.assertEqual(dyadic_g(2**4097), F(1, 2**512))


if __name__ == "__main__":
    unittest.main()
