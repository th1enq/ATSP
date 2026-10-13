import copy
import json
import sys
import unittest
from fractions import Fraction as F
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from experimental_tree import build_tree, construct, run_aks, verify_report, verify_trace


class ExperimentalTreeTest(unittest.TestCase):
    def test_spectral_path_never_calls_exhaustive_oracle(self):
        arcs = [(u, v, 1) for u in range(5) for v in range(5) if u != v]
        with patch("experimental_tree.exact_cut_ratio", side_effect=AssertionError("brute-force call")):
            report = construct(5, 4, arcs)
            self.assertTrue(report["trace"]["rounds"])
            verify_report(report)
        self.assertIsNone(report["beta_exact"])
        self.assertEqual(report["input_graph_kind"], "reduced_original")
        self.assertEqual(report["input_graph_copy_count"], 20)
        with self.assertRaisesRegex(ValueError, "exhaustive"):
            run_aks(report, Path("/unused"), "construct-certified")
        bad = copy.deepcopy(report)
        bad["beta_bound_for_aks"] = "1/2"
        with self.assertRaisesRegex(ValueError, "bound"):
            verify_report(bad)

    def test_spectral_dimensions_above_old_limit(self):
        n = 20
        arcs = [(u, (u+1) % n, 1) for u in range(n)]
        with patch("experimental_tree.exact_cut_ratio", side_effect=AssertionError("brute-force call")):
            report = construct(n, 1, arcs)
            verify_report(report)
        self.assertEqual(report["input_graph_copy_count"], n)
        self.assertEqual(report["beta_bound_for_aks"], "1")
        self.assertEqual(len(report["tree_pairs"]), n-1)

    def test_multiple_rounds_and_independent_replay(self):
        edges = [(0, 1)]*32
        trace = build_tree(2, edges, 16, stop_r=1, exact_measurements=True)
        self.assertGreaterEqual(len(trace["rounds"]), 3)
        self.assertEqual(trace["final_r"], 1)
        self.assertEqual(len(trace["final_tree"]), 1)
        verify_trace(2, edges, json.loads(json.dumps(trace)))
        for row in trace["rounds"]:
            self.assertLessEqual(2*row["r_next"], row["r"])
            self.assertGreaterEqual(4*row["r_next"], row["r"])
            self.assertLess(row["edges_after"], row["edges_before"])
        bad = copy.deepcopy(trace)
        bad["rounds"][0]["r_next"] += 1
        with self.assertRaises(ValueError):
            verify_trace(2, edges, bad)
        bad = copy.deepcopy(trace)
        bad["rounds"][0]["packed_trees"][0] = [31]
        with self.assertRaises(ValueError):
            verify_trace(2, edges, bad)

    def test_rational_projection_and_tampered_certificate(self):
        report = construct(3, 2, [(u, v, 1) for u in range(3) for v in range(3) if u != v], exact_measurements=True)
        verify_report(json.loads(json.dumps(report)))
        self.assertEqual(F(report["beta_exact"]), 1)
        self.assertTrue(report["trace"]["rounds"])
        bad = copy.deepcopy(report)
        bad["beta_exact"] = "1/2"
        with self.assertRaisesRegex(ValueError, "thinness"):
            verify_report(bad)
        bad = copy.deepcopy(report)
        bad["trace"]["rounds"][0]["x"][0][0] = "0"
        with self.assertRaises(ValueError):
            verify_report(bad)

    def test_large_denominator_and_bounded_stop(self):
        scale = 1 << 4096
        arcs = [(u, v, scale) for u in range(3) for v in range(3) if u != v]
        report = construct(3, 2*scale, arcs, max_rounds=0, exact_measurements=True)
        self.assertEqual(report["trace"]["stop_reason"], "round_limit")
        self.assertEqual(F(report["beta_exact"]), 1)
        verify_report(report)
        with self.assertRaises(ValueError):
            build_tree(2, [(0, 1)], 2)


if __name__ == "__main__":
    unittest.main()
