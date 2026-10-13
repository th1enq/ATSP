import itertools
import random
import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from weighted_partition_oracle import (exact_mst, most_violated_partition,
                                       violated_partition, violated_partition_small)


class WeightedPartitionOracleTest(unittest.TestCase):
    def test_mst_against_all_trees(self):
        rng = random.Random(20261008)
        for n in range(2, 6):
            edges = list(itertools.combinations(range(n), 2))
            for _ in range(10):
                lengths = [Fraction(rng.randrange(10), rng.randrange(1, 8)) for _ in edges]
                cost, chosen = exact_mst(n, edges, lengths)
                self.assertEqual(len(chosen), n - 1)
                brute = None
                for ids in itertools.combinations(range(len(edges)), n - 1):
                    parent = list(range(n))
                    for i in ids:
                        u, v = edges[i]
                        while parent[u] != u:
                            u = parent[u]
                        while parent[v] != v:
                            v = parent[v]
                        parent[u] = v
                    def root(u):
                        while parent[u] != u:
                            u = parent[u]
                        return u
                    if len({root(u) for u in range(n)}) == 1:
                        value = sum((lengths[i] for i in ids), Fraction())
                        brute = value if brute is None else min(brute, value)
                self.assertEqual(cost, brute)

    def test_rational_partition_violation(self):
        edges = [(0, 1), (0, 2), (1, 2)]
        capacities = [Fraction(1, 2)] * 3
        labels, slack = violated_partition_small(3, edges, capacities, Fraction(1))
        self.assertEqual(slack, Fraction(-1, 2))
        self.assertEqual(len(set(labels)), 3)
        self.assertIsNone(violated_partition_small(3, edges, capacities,
                                                   Fraction(3, 4)))

    def test_polynomial_separator_against_all_partitions(self):
        rng = random.Random(39017)
        for n in range(2, 7):
            possible = list(itertools.combinations(range(n), 2))
            for _ in range(30):
                edges = [e for e in possible if rng.randrange(3)]
                capacities = [Fraction(rng.randrange(8), rng.randrange(1, 8))
                              for _ in edges]
                q = Fraction(rng.randrange(1, 6), rng.randrange(1, 5))
                labels, slack = most_violated_partition(n, edges, capacities, q)
                brute = Fraction(0)
                assignment = [0] * n

                def visit(v, maximum):
                    nonlocal brute
                    if v == n:
                        value = sum((z for (u, w), z in zip(edges, capacities)
                                     if assignment[u] != assignment[w]),
                                    Fraction()) - q * maximum
                        brute = min(brute, value)
                        return
                    for block in range(maximum + 2):
                        assignment[v] = block
                        visit(v + 1, max(maximum, block))

                visit(1, 0)
                self.assertEqual(slack, brute)
                self.assertEqual(violated_partition(n, edges, capacities, q) is None,
                                 brute == 0)

    def test_zero_q_and_large_denominator(self):
        edges = [(0, 1), (1, 2)]
        capacities = [Fraction(1, 2**4096), Fraction(1, 2**2048)]
        self.assertIsNone(violated_partition(3, edges, capacities, Fraction(0)))
        labels, slack = most_violated_partition(3, edges, capacities, Fraction(1))
        self.assertEqual(len(set(labels)), 3)
        self.assertEqual(slack, sum(capacities) - 2)


if __name__ == "__main__":
    unittest.main()
