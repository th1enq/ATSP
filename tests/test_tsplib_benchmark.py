"""Meaningful checks for the real-matrix adapter and its lower-bound proof."""
import sys
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"benchmarks"))
from bench_tsplib import (held_karp_threshold, read_tsplib, triangle_violations,
                          validate_tour, verify_infeasibility)


class TSPLIBAdapterTests(unittest.TestCase):
    def test_official_matrices_have_expected_dimensions(self):
        manifest = __import__("json").loads((ROOT/"instances/tsplib/manifest.json").read_text())
        from bench_tsplib import matrix_sha256
        for row in manifest["instances"]:
            meta, matrix = read_tsplib(ROOT/"instances/tsplib"/row["path"])
            self.assertEqual(meta["NAME"], row["name"])
            self.assertEqual(len(matrix), row["n"])
            self.assertEqual(matrix_sha256(matrix), row["matrix_sha256"])

    def test_weighted_objective_and_closed_tour_validation(self):
        matrix = [[0, 7, 2], [2, 0, 9], [4, 1, 0]]
        self.assertEqual(validate_tour(matrix, [0, 1, 2, 0]), (9, 20))
        with self.assertRaises(ValueError):
            validate_tour(matrix, [0, 1, 1, 0])

    def test_metric_and_nonmetric_inputs_are_distinguished(self):
        _, matrix = read_tsplib(ROOT/"instances/tsplib/ftv33.atsp")
        self.assertEqual(triangle_violations(matrix), 0)
        _, matrix = read_tsplib(ROOT/"instances/tsplib/br17.atsp")
        self.assertEqual(triangle_violations(matrix), 488)

    @unittest.skipUnless(importlib.util.find_spec("scipy"), "optional TSPLIB adapter needs SciPy")
    def test_lp_rejects_disconnected_cycle_cover_with_exact_cut_proof(self):
        # The assignment equations are feasible at cost 1, but two disjoint
        # cycles violate HK. This catches accidentally benchmarking a cycle
        # cover in place of a Held--Karp solution.
        matrix = [[0 if u == v else (1 if u//2 == v//2 else 9)
                   for v in range(4)] for u in range(4)]
        report = held_karp_threshold(matrix)
        self.assertEqual(report["threshold"], 9)
        previous = report["predecessor"]
        self.assertEqual(previous["threshold"], 1)
        self.assertFalse(previous["feasible"])
        edges = [(u, v) for u in range(4) for v in range(4) if u != v and matrix[u][v] <= 1]
        verify_infeasibility(4, edges, previous["proof"])
        previous["proof"]["weighted_rhs"] = "0"
        with self.assertRaises(ValueError):
            verify_infeasibility(4, edges, previous["proof"])

    def test_parser_rejects_truncated_matrix(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"bad.atsp"
            path.write_text("NAME: bad\nTYPE: ATSP\nDIMENSION: 2\nEDGE_WEIGHT_TYPE: EXPLICIT\n"
                            "EDGE_WEIGHT_FORMAT: FULL_MATRIX\nEDGE_WEIGHT_SECTION\n9999 1 1\nEOF\n")
            with self.assertRaises(ValueError):
                read_tsplib(path)


if __name__ == "__main__":
    unittest.main()
