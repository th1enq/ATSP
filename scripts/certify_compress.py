#!/usr/bin/env python3
"""Exact Held--Karp validation and Section 6 binary-multiplicity reduction.

Input: n D m, followed by m lines 'u v numerator'.  Numerators encode x_uv
as numerator/D.  Output is a compact JSON certificate; no parallel copies are
materialized.  This module does not construct a strong thin tree.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from pathlib import Path

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)  # exact binary multiplicities may exceed 4300 decimal digits


class CertificateError(ValueError):
    pass


def read_hk(path: Path) -> tuple[int, int, list[tuple[int, int, int]]]:
    rows = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        row = raw.split("#", 1)[0].strip()
        if row:
            rows.append(row.split())
    if not rows or len(rows[0]) != 3:
        raise CertificateError("expected header: n denominator arc_count")
    try:
        n, denominator, count = map(int, rows[0])
    except ValueError as exc:
        raise CertificateError("non-integer header") from exc
    if n < 2 or denominator <= 0 or count < n or len(rows) != count + 1:
        raise CertificateError("invalid header or arc count")
    arcs = []
    seen = set()
    for row in rows[1:]:
        if len(row) != 3:
            raise CertificateError("expected arc: u v numerator")
        try:
            u, v, numerator = map(int, row)
        except ValueError as exc:
            raise CertificateError("non-integer arc") from exc
        if not (0 <= u < n and 0 <= v < n) or u == v or (u, v) in seen:
            raise CertificateError("invalid or duplicate arc")
        if not (0 <= numerator <= denominator):
            raise CertificateError("arc numerator outside [0, denominator]")
        seen.add((u, v))
        arcs.append((u, v, numerator))
    return n, denominator, arcs


def read_binary_multigraph(path: Path) -> tuple[int, int, list[tuple[int, int, int]]]:
    """Input: n k pair_count, then one 'u v multiplicity' per pair."""
    rows = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        row = raw.split("#", 1)[0].strip()
        if row:
            rows.append(row.split())
    if not rows or len(rows[0]) != 3:
        raise CertificateError("expected header: n k pair_count")
    try:
        n, k, count = map(int, rows[0])
    except ValueError as exc:
        raise CertificateError("non-integer header") from exc
    if n < 2 or k <= 0 or count < n - 1 or len(rows) != count + 1:
        raise CertificateError("invalid header or pair count")
    pairs = []
    seen = set()
    for row in rows[1:]:
        if len(row) != 3:
            raise CertificateError("expected pair: u v multiplicity")
        try:
            u, v, c = map(int, row)
        except ValueError as exc:
            raise CertificateError("non-integer pair") from exc
        if not (0 <= u < v < n) or (u, v) in seen or c < 0:
            raise CertificateError("invalid or duplicate pair")
        seen.add((u, v))
        pairs.append((u, v, c))
    return n, k, pairs


def min_cut(n: int, edges: list[tuple[int, int, int]], source: int,
            sink: int) -> tuple[int, list[int]]:
    """Exact directed s-t min cut by integral Dinic max flow."""
    graph: list[list[list[int]]] = [[] for _ in range(n)]

    def add_edge(u: int, v: int, capacity: int) -> None:
        forward = [v, len(graph[v]), capacity]
        backward = [u, len(graph[u]), 0]
        graph[u].append(forward)
        graph[v].append(backward)

    for u, v, capacity in edges:
        if capacity > 0:
            add_edge(u, v, capacity)
    total = 0
    # Dinic's depth is at most n; this is unrelated to numeric capacities.
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 2 * n + 100))
    while True:
        level = [-1] * n
        level[source] = 0
        queue = deque([source])
        while queue:
            u = queue.popleft()
            for v, _, capacity in graph[u]:
                if capacity and level[v] < 0:
                    level[v] = level[u] + 1
                    queue.append(v)
        if level[sink] < 0:
            break
        next_edge = [0] * n

        def push(u: int, available: int) -> int:
            if u == sink:
                return available
            while next_edge[u] < len(graph[u]):
                edge = graph[u][next_edge[u]]
                v, reverse, capacity = edge
                if capacity and level[v] == level[u] + 1:
                    sent = push(v, min(available, capacity))
                    if sent:
                        edge[2] -= sent
                        graph[v][reverse][2] += sent
                        return sent
                next_edge[u] += 1
            return 0

        limit = sum(edge[2] for edge in graph[source])
        while (sent := push(source, limit)):
            total += sent
    reachable = [u for u, distance in enumerate(level) if distance >= 0]
    return total, reachable


def global_directed_min_cut(n: int, edges: list[tuple[int, int, int]]) -> tuple[int, list[int]]:
    # Every nontrivial S either contains root 0 or has a vertex on the far side.
    # The two orientations of root-v cuts therefore cover every directed cut.
    best = None
    side = []
    for v in range(1, n):
        for source, sink in ((0, v), (v, 0)):
            value, reachable = min_cut(n, edges, source, sink)
            if best is None or value < best:
                best, side = value, reachable
    assert best is not None
    return best, side


def global_undirected_min_cut(n: int, pairs: list[tuple[int, int, int]]) -> tuple[int, list[int]]:
    directed = [(u, v, c) for u, v, c in pairs] + [(v, u, c) for u, v, c in pairs]
    best = None
    side = []
    for v in range(1, n):
        value, reachable = min_cut(n, directed, 0, v)
        if best is None or value < best:
            best, side = value, reachable
    assert best is not None
    return best, side


def certify_and_compress(n: int, denominator: int,
                         arcs: list[tuple[int, int, int]]) -> dict:
    incoming = [0] * n
    outgoing = [0] * n
    pairs: dict[tuple[int, int], int] = {}
    for u, v, numerator in arcs:
        outgoing[u] += numerator
        incoming[v] += numerator
        key = (min(u, v), max(u, v))
        pairs[key] = pairs.get(key, 0) + numerator
    for v in range(n):
        if incoming[v] != denominator or outgoing[v] != denominator:
            raise CertificateError(f"degree equality fails at vertex {v}")
    directed_cut, side = global_directed_min_cut(n, arcs)
    if directed_cut < denominator:
        raise CertificateError(f"subtour inequality fails on cut {side}: {directed_cut} < {denominator}")

    result = compress_multigraph(n, 2 * denominator,
                                 [(u, v, c) for (u, v), c in pairs.items() if c])
    result["denominator"] = str(denominator)
    result["directed_hk_min_cut"] = str(directed_cut)
    return result


def compress_multigraph(n: int, k: int,
                        pairs: list[tuple[int, int, int]]) -> dict:
    original_cut, original_side = global_undirected_min_cut(n, pairs)
    if original_cut < k:
        raise CertificateError(f"original connectivity fails on cut {original_side}: {original_cut} < {k}")
    scale = 2 * n * n
    compressed = []
    for u, v, c in sorted(pairs):
        if c == 0:
            continue
        a = scale * min(c, k) // k
        if a < 0 or a > scale or a * k > scale * c:
            raise AssertionError("pair compression invariant failed")
        compressed.append((u, v, c, a))
    copy_count = sum(a for _, _, _, a in compressed)
    if copy_count >= n**4:
        raise AssertionError("explicit copy bound failed")
    compressed_cut, compressed_side = global_undirected_min_cut(
        n, [(u, v, a) for u, v, _, a in compressed])
    if compressed_cut < n * n:
        raise AssertionError("compressed min-cut bound failed")
    return {
        "n": n,
        "original_connectivity_lower_bound": str(k),
        "original_min_cut": str(original_cut),
        "compressed_connectivity_lower_bound": n * n,
        "compressed_min_cut": compressed_cut,
        "compressed_min_cut_side": compressed_side,
        "explicit_copy_count": copy_count,
        "explicit_copy_bound_strict": n**4,
        "pairs": [
            {"u": u, "v": v, "original_multiplicity": str(c),
             "compressed_multiplicity": a}
            for u, v, c, a in compressed
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hk_file", type=Path)
    parser.add_argument("--kind", choices=("hk", "binary"), default="hk",
                        help="binary reads n k p and undirected pair multiplicities")
    parser.add_argument("--output", type=Path, help="write compact JSON certificate here")
    args = parser.parse_args()
    try:
        result = (certify_and_compress(*read_hk(args.hk_file)) if args.kind == "hk"
                  else compress_multigraph(*read_binary_multigraph(args.hk_file)))
    except (OSError, CertificateError) as exc:
        parser.exit(2, f"certificate rejected: {exc}\n")
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
