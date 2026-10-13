import random
import itertools
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from certify_compress import certify_and_compress
from tree_packing import (PackingError, expand_compressed, pack_forests,
                          verify_obstruction, verify_result, verify_trees)


ROOT = Path(__file__).resolve().parents[1]


def partitions(n):
    labels = [0] * n

    def rec(i, maximum):
        if i == n:
            if maximum:
                yield labels.copy()
            return
        for label in range(maximum + 2):
            labels[i] = label
            yield from rec(i + 1, max(maximum, label))

    yield from rec(1, 0)


def packing_number_by_partitions(n, edges):
    return min(sum(labels[u] != labels[v] for u, v, _ in edges) // max(labels)
               for labels in partitions(n))


class TreePackingTest(unittest.TestCase):
    def test_witness_compression(self):
        from certify_compress import read_hk
        n, denominator, arcs = read_hk(ROOT / "instances/regression/witness6_hk.txt")
        compressed = certify_and_compress(n, denominator, arcs)
        n, edges = expand_compressed(compressed)
        forests, complete, partition = pack_forests(n, edges, 18)
        self.assertTrue(complete)
        self.assertIsNone(partition)
        verify_trees(n, edges, [sorted(forest) for forest in forests])

    def test_random_graphs_against_partition_theorem(self):
        rng = random.Random(20261008)
        for n in range(2, 6):
            for _ in range(15):
                edges = [(u, v, copy) for u in range(n) for v in range(u + 1, n)
                         for copy in range(rng.randrange(4))]
                optimum = packing_number_by_partitions(n, edges)
                for requested in (1, max(1, optimum), optimum + 1):
                    forests, complete, partition = pack_forests(n, edges, requested)
                    self.assertEqual(complete, requested <= optimum)
                    if complete:
                        self.assertIsNone(partition)
                        verify_trees(n, edges, [sorted(forest) for forest in forests])
                    else:
                        self.assertIsNotNone(partition)
                        crossing = verify_obstruction(n, edges, requested, partition)
                        self.assertLess(crossing, requested * (len(set(partition)) - 1))

    def test_reject_bad_tree_certificate(self):
        edges = [(0, 1, 0), (1, 2, 0), (0, 2, 0)]
        with self.assertRaises(PackingError):
            verify_trees(3, edges, [[0, 0]])
        with self.assertRaises(PackingError):
            verify_result(3, edges, {"n": 3, "requested_trees": 1,
                                     "complete": True, "trees": [[0, 0]]})

    def test_nontrivial_partition_obstruction(self):
        edges = [(u, v, copy) for u, v in ((0, 1), (0, 2), (1, 2))
                 for copy in range(2)]
        edges.append((2, 3, 0))
        forests, complete, partition = pack_forests(4, edges, 2)
        self.assertFalse(complete)
        self.assertEqual(sum(map(len, forests)), 5)
        self.assertEqual(verify_obstruction(4, edges, 2, partition), 1)

    def test_exhaustive_n4_multiplicities_up_to_two(self):
        pairs = list(itertools.combinations(range(4), 2))
        for multiplicities in itertools.product(range(3), repeat=len(pairs)):
            edges = [(u, v, copy) for (u, v), count in zip(pairs, multiplicities)
                     for copy in range(count)]
            optimum = packing_number_by_partitions(4, edges)
            for requested in range(1, optimum + 2):
                forests, complete, partition = pack_forests(4, edges, requested)
                self.assertEqual(complete, requested <= optimum)
                if complete:
                    verify_trees(4, edges, [sorted(forest) for forest in forests])
                else:
                    verify_obstruction(4, edges, requested, partition)


if __name__ == "__main__":
    unittest.main()
