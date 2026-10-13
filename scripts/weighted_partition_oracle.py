#!/usr/bin/env python3
"""Exact weighted-partition separator, MST oracle, and small reference.

Kruskal separates a proposed spanning-tree inequality v <= length(T) in
equation (3.18).  The partition separator implements Algorithm 1 and the
min-cut reduction of Baiou, Barahona and Mahjoub (2000), Sections 2--3.
The outer rational LP/ellipsoid algorithm is not implemented.
"""

from __future__ import annotations

from fractions import Fraction
from math import lcm

from certify_compress import min_cut


def most_violated_partition(
    n: int, edges: list[tuple[int, int]], capacities: list[Fraction],
    q: Fraction,
) -> tuple[list[int], Fraction]:
    """Minimize z(E(P)) - q(|P|-1) over all partitions P, exactly.

    Runs n integral s-t min-cut computations after one denominator scaling.
    The input may have parallel edges. The returned labels are canonical block
    indices and the slack is nonpositive (the one-block partition has slack 0).
    """
    if n < 2 or len(edges) != len(capacities) or q < 0:
        raise ValueError("invalid partition instance")
    if any(not (0 <= u < v < n) for u, v in edges):
        raise ValueError("invalid partition edge")
    if any(z < 0 for z in capacities):
        raise ValueError("negative capacity")
    if q == 0:
        return [0] * n, Fraction()

    # Normalize q to 1, then put every capacity on a common integer scale.
    normalized = [Fraction(z) / q for z in capacities]
    scale = lcm(*(z.denominator for z in normalized))
    weights = [int(z * scale) for z in normalized]
    y = [2 * scale] * n
    tight_blocks: list[set[int]] = []
    source, sink = n, n + 1
    bidirected = [(u, v, w) for (u, v), w in zip(edges, weights)]
    bidirected += [(v, u, w) for (u, v), w in zip(edges, weights)]

    for vertex in range(n):
        if any(vertex in block for block in tight_blocks):
            continue
        # psi(r)=y(r)+2, psi(i)=y(i) otherwise, with root r=0.
        psi = y.copy()
        psi[0] += 2 * scale
        finite = sum(weights) * 2 + sum(abs(value) for value in psi) + 1
        network = bidirected.copy()
        for i, value in enumerate(psi):
            if i == vertex:
                network.append((source, i, finite))
                if value > 0:
                    network.append((i, sink, value))
            elif value < 0:
                network.append((source, i, -value))
            elif value > 0:
                network.append((i, sink, value))
        _, reachable = min_cut(n + 2, network, source, sink)
        block = set(reachable) - {source}
        assert vertex in block and sink not in block
        crossing = sum(w for (u, v), w in zip(edges, weights)
                       if (u in block) != (v in block))
        f_block = (0 if 0 in block else 2 * scale) - crossing
        y[vertex] += f_block - sum(y[i] for i in block)
        tight_blocks.append(block)
        # Tight intersecting sets have a tight union. Maintain a partition.
        while True:
            overlap = next(((i, j) for i in range(len(tight_blocks))
                            for j in range(i + 1, len(tight_blocks))
                            if tight_blocks[i] & tight_blocks[j]), None)
            if overlap is None:
                break
            i, j = overlap
            tight_blocks[i] |= tight_blocks[j]
            tight_blocks.pop(j)

    assert set().union(*tight_blocks) == set(range(n))
    labels = [0] * n
    for label, block in enumerate(sorted(tight_blocks, key=min)):
        for vertex in block:
            labels[vertex] = label
    slack = sum((z for (u, v), z in zip(edges, capacities)
                 if labels[u] != labels[v]), Fraction()) - q * (len(tight_blocks) - 1)
    assert slack <= 0
    return labels, slack


def violated_partition(
    n: int, edges: list[tuple[int, int]], capacities: list[Fraction],
    q: Fraction,
) -> tuple[list[int], Fraction] | None:
    """Return an exact violated partition, or None if all are satisfied."""
    labels, slack = most_violated_partition(n, edges, capacities, q)
    return (labels, slack) if slack < 0 else None


def exact_mst(n: int, edges: list[tuple[int, int]],
              lengths: list[Fraction]) -> tuple[Fraction, list[int]]:
    if n < 1 or len(edges) != len(lengths):
        raise ValueError("invalid MST dimensions")
    if any(not (0 <= u < v < n) for u, v in edges):
        raise ValueError("invalid MST edge")
    parent = list(range(n))

    def root(u: int) -> int:
        while parent[u] != u:
            parent[u] = parent[parent[u]]
            u = parent[u]
        return u

    chosen = []
    for edge_id in sorted(range(len(edges)), key=lambda i: (lengths[i], i)):
        u, v = edges[edge_id]
        ru, rv = root(u), root(v)
        if ru != rv:
            parent[ru] = rv
            chosen.append(edge_id)
            if len(chosen) == n - 1:
                break
    if len(chosen) != n - 1:
        raise ValueError("graph is disconnected")
    return sum((lengths[i] for i in chosen), Fraction()), chosen


def violated_partition_small(n: int, edges: list[tuple[int, int]],
                             capacities: list[Fraction], q: Fraction,
                             max_n: int = 8) -> tuple[list[int], Fraction] | None:
    """Exhaustive exact reference; exponential Bell(n), never production LP."""
    if n < 2 or n > max_n or len(edges) != len(capacities) or q < 0:
        raise ValueError("invalid small partition instance")
    if any(not (0 <= u < v < n) for u, v in edges):
        raise ValueError("invalid partition edge")
    if any(z < 0 for z in capacities):
        raise ValueError("negative capacity")
    labels = [0] * n

    def search(vertex: int, maximum: int):
        if vertex == n:
            if maximum:
                crossing = sum((z for (u, v), z in zip(edges, capacities)
                                if labels[u] != labels[v]), Fraction())
                slack = crossing - q * maximum
                if slack < 0:
                    return labels.copy(), slack
            return None
        for label in range(maximum + 2):
            labels[vertex] = label
            found = search(vertex + 1, max(maximum, label))
            if found is not None:
                return found
        return None

    return search(1, 0)
