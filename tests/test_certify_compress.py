import sys
import random
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from certify_compress import (CertificateError, certify_and_compress,
                              compress_multigraph, read_binary_multigraph, read_hk)


ROOT = Path(__file__).resolve().parents[1]


def all_cuts(n, pairs):
    for mask in range(1, 1 << (n - 1)):
        yield sum(c for u, v, c in pairs if bool(mask & (1 << u)) != bool(mask & (1 << v)))


class CompressionTest(unittest.TestCase):
    def test_witness_and_every_cut(self):
        n, denominator, arcs = read_hk(ROOT / "instances/regression/witness6_hk.txt")
        result = certify_and_compress(n, denominator, arcs)
        self.assertEqual(result["directed_hk_min_cut"], str(denominator))
        self.assertGreaterEqual(result["compressed_min_cut"], n * n)
        self.assertLess(result["explicit_copy_count"], n**4)
        original = [(p["u"], p["v"], int(p["original_multiplicity"])) for p in result["pairs"]]
        compact = [(p["u"], p["v"], p["compressed_multiplicity"]) for p in result["pairs"]]
        for old, new in zip(all_cuts(n, original), all_cuts(n, compact)):
            self.assertGreaterEqual(old, 2 * denominator)
            self.assertGreaterEqual(new, n * n)
            self.assertLessEqual(new * (2 * denominator), 2 * n * n * old)

    def test_thousand_bit_denominator(self):
        n, denominator, arcs = read_hk(ROOT / "instances/regression/witness6_hk.txt")
        factor = (1 << 4096) + 12345
        scaled = [(u, v, numerator * factor) for u, v, numerator in arcs]
        original = certify_and_compress(n, denominator, arcs)
        large = certify_and_compress(n, denominator * factor, scaled)
        self.assertEqual(large["pairs"][0]["compressed_multiplicity"],
                         original["pairs"][0]["compressed_multiplicity"])
        self.assertEqual(large["explicit_copy_count"], original["explicit_copy_count"])

    def test_reject_disconnected_cycle_cover(self):
        arcs = [(u, (u + 1) % 3, 1) for u in range(3)]
        arcs += [(u, 3 + (u - 2) % 3, 1) for u in range(3, 6)]
        with self.assertRaisesRegex(CertificateError, "subtour"):
            certify_and_compress(6, 1, arcs)

    def test_reject_degree_error(self):
        with self.assertRaisesRegex(CertificateError, "degree"):
            certify_and_compress(3, 1, [(0, 1, 1), (1, 2, 1)])

    def test_binary_truncation_with_huge_multiplicity(self):
        huge = 1 << 8192
        result = compress_multigraph(3, 7, [(0, 1, huge), (0, 2, 7), (1, 2, 7)])
        pair = next(p for p in result["pairs"] if (p["u"], p["v"]) == (0, 1))
        self.assertEqual(pair["compressed_multiplicity"], 18)
        self.assertEqual(result["compressed_min_cut"], 36)
        self.assertLess(result["explicit_copy_count"], 3**4)

    def test_binary_fixture_parser(self):
        n, k, pairs = read_binary_multigraph(ROOT / "instances/regression/binary_triangle.txt")
        result = compress_multigraph(n, k, pairs)
        self.assertEqual(result["explicit_copy_count"], 54)

    def test_reject_low_connectivity(self):
        with self.assertRaisesRegex(CertificateError, "connectivity"):
            compress_multigraph(3, 3, [(0, 1, 1), (1, 2, 1)])

    def test_floor_can_remove_a_pair(self):
        result = compress_multigraph(3, 100,
                                     [(0, 1, 1), (0, 2, 100), (1, 2, 100)])
        self.assertEqual(sum(p["compressed_multiplicity"] > 0 for p in result["pairs"]), 2)
        self.assertEqual(result["pairs"][0]["compressed_multiplicity"], 0)
        self.assertEqual(result["compressed_min_cut"], 18)

    def test_random_small_graphs_against_all_cuts(self):
        rng = random.Random(20261008)
        for n in range(3, 8):
            for _ in range(6):
                mass = {}
                for _ in range(3):
                    order = rng.sample(range(n), n)
                    for i, u in enumerate(order):
                        v = order[(i + 1) % n]
                        mass[u, v] = mass.get((u, v), 0) + 1
                arcs = [(u, v, c) for (u, v), c in mass.items()]
                result = certify_and_compress(n, 3, arcs)
                directed = []
                for mask in range(1, (1 << n) - 1):
                    directed.append(sum(c for u, v, c in arcs
                                        if (mask >> u) & 1 and not (mask >> v) & 1))
                self.assertEqual(int(result["directed_hk_min_cut"]), min(directed))
                compact = [(p["u"], p["v"], p["compressed_multiplicity"])
                           for p in result["pairs"]]
                self.assertEqual(result["compressed_min_cut"], min(all_cuts(n, compact)))


if __name__ == "__main__":
    unittest.main()
