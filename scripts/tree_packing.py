#!/usr/bin/env python3
"""Deterministic graphic-matroid union for edge-disjoint spanning trees.

The input is the compact JSON certificate from certify_compress.py.  Copies
are expanded only after Section 6 has proved there are fewer than n^4 of them.
The augmenting-path method follows Knuth's matroid-union exchange graph.
"""

from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path


class PackingError(ValueError):
    pass


def expand_compressed(certificate: dict) -> tuple[int, list[tuple[int, int, int]]]:
    n = certificate["n"]
    if not isinstance(n, int) or n < 2:
        raise PackingError("invalid vertex count")
    edges = []
    seen_pairs = set()
    for pair in certificate["pairs"]:
        u, v, count = (pair["u"], pair["v"], pair["compressed_multiplicity"])
        if not all(isinstance(x, int) for x in (u, v, count)) or not (0 <= u < v < n):
            raise PackingError("invalid compressed pair")
        if (u, v) in seen_pairs:
            raise PackingError("duplicate compressed pair")
        seen_pairs.add((u, v))
        if not (0 <= count <= 2 * n * n):
            raise PackingError("compressed multiplicity exceeds Section 6 bound")
        edges.extend((u, v, copy) for copy in range(count))
    if len(edges) != certificate["explicit_copy_count"] or len(edges) >= n**4:
        raise PackingError("copy-count certificate mismatch")
    return n, edges


def forest_oracle(n: int, edges: list[tuple[int, int, int]], ids: set[int]) -> bool:
    parent = list(range(n))

    def root(u: int) -> int:
        while parent[u] != u:
            parent[u] = parent[parent[u]]
            u = parent[u]
        return u

    for edge_id in ids:
        u, v, _ = edges[edge_id]
        ru, rv = root(u), root(v)
        if ru == rv:
            return False
        parent[ru] = rv
    return True


def exchange_graph(n: int, edges: list[tuple[int, int, int]],
                   forests: list[set[int]], owner: list[int]) -> tuple[list[list[int]], list[int]]:
    """Return arcs e -> f and one forest accepting each free-addable f."""
    m = len(edges)
    adjacency = [[] for _ in range(m)]
    free = [-1] * m
    for color, forest in enumerate(forests):
        tree_adj = [[] for _ in range(n)]
        for edge_id in forest:
            u, v, _ = edges[edge_id]
            tree_adj[u].append((v, edge_id))
            tree_adj[v].append((u, edge_id))
        for f, (u, v, _) in enumerate(edges):
            if owner[f] == color:
                continue
            previous = [-1] * n
            previous_edge = [-1] * n
            previous[u] = u
            queue = deque([u])
            while queue and previous[v] < 0:
                w = queue.popleft()
                for x, edge_id in tree_adj[w]:
                    if previous[x] < 0:
                        previous[x], previous_edge[x] = w, edge_id
                        queue.append(x)
            if previous[v] < 0:
                if free[f] < 0:
                    free[f] = color
                # In a forest, removing any edge still permits this addition.
                for e in forest:
                    adjacency[e].append(f)
            else:
                x = v
                while x != u:
                    adjacency[previous_edge[x]].append(f)
                    x = previous[x]
    return adjacency, free


def augmenting_path(adjacency: list[list[int]], free: list[int],
                    owner: list[int]) -> tuple[list[int], list[bool]]:
    previous = [-2] * len(owner)
    queue = deque()
    for e, color in enumerate(free):
        if color >= 0:
            previous[e] = -1
            queue.append(e)
    while queue:
        e = queue.popleft()
        if owner[e] < 0:
            path = [e]
            while previous[e] >= 0:
                e = previous[e]
                path.append(e)
            path.reverse()
            return path, [p != -2 for p in previous]
        for f in adjacency[e]:
            if previous[f] == -2:
                previous[f] = e
                queue.append(f)
    return [], [p != -2 for p in previous]


def obstruction_partition(n: int, edges: list[tuple[int, int, int]],
                          reachable: list[bool], colors: int) -> list[int]:
    """Components of E minus the reachable exchange-graph edges."""
    parent = list(range(n))

    def root(u: int) -> int:
        while parent[u] != u:
            parent[u] = parent[parent[u]]
            u = parent[u]
        return u

    for edge_id, (u, v, _) in enumerate(edges):
        if not reachable[edge_id]:
            parent[root(u)] = root(v)
    label_by_root = {}
    labels = []
    for u in range(n):
        r = root(u)
        if r not in label_by_root:
            label_by_root[r] = len(label_by_root)
        labels.append(label_by_root[r])
    crossing = sum(labels[u] != labels[v] for u, v, _ in edges)
    if len(label_by_root) < 2 or crossing >= colors * (len(label_by_root) - 1):
        raise AssertionError("exchange-graph obstruction is not a violated partition")
    return labels


def pack_forests(n: int, edges: list[tuple[int, int, int]],
                 colors: int) -> tuple[list[set[int]], bool, list[int] | None]:
    """Maximum union of `colors` forests or a violated partition certificate."""
    if n < 2 or colors < 0:
        raise PackingError("invalid packing dimensions")
    if colors == 0:
        return [], True, None
    if colors * (n - 1) > len(edges):
        return [], False, list(range(n))
    forests = [set() for _ in range(colors)]
    owner = [-1] * len(edges)
    while True:
        adjacency, free = exchange_graph(n, edges, forests, owner)
        path, reachable = augmenting_path(adjacency, free, owner)
        if not path:
            return forests, False, obstruction_partition(n, edges, reachable, colors)
        start_color = free[path[0]]
        old_owners = [owner[e] for e in path]
        for e, color in zip(path[:-1], old_owners[:-1]):
            forests[color].remove(e)
            owner[e] = -1
        for e, f, color in zip(path[:-1], path[1:], old_owners[:-1]):
            forests[color].add(f)
            owner[f] = color
        forests[start_color].add(path[0])
        owner[path[0]] = start_color
        if any(not forest_oracle(n, edges, forest) for forest in forests):
            raise AssertionError("matroid exchange produced a cycle")
        if sum(map(len, forests)) == colors * (n - 1):
            break
    return forests, True, None


def verify_trees(n: int, edges: list[tuple[int, int, int]],
                 trees: list[list[int]]) -> None:
    used = set()
    for tree in trees:
        if len(tree) != n - 1 or len(set(tree)) != n - 1:
            raise PackingError("tree size or duplicate edge invalid")
        if any(not isinstance(e, int) or e < 0 or e >= len(edges) for e in tree):
            raise PackingError("tree edge ID invalid")
        if used.intersection(tree) or not forest_oracle(n, edges, set(tree)):
            raise PackingError("trees overlap or contain a cycle")
        used.update(tree)


def verify_obstruction(n: int, edges: list[tuple[int, int, int]],
                       colors: int, labels: list[int]) -> int:
    if len(labels) != n or any(not isinstance(x, int) or x < 0 for x in labels):
        raise PackingError("invalid partition labels")
    parts = len(set(labels))
    crossing = sum(labels[u] != labels[v] for u, v, _ in edges)
    if parts < 2 or crossing >= colors * (parts - 1):
        raise PackingError("partition does not obstruct requested packing")
    return crossing


def verify_result(n: int, edges: list[tuple[int, int, int]], result: dict) -> None:
    if result.get("n") != n or not isinstance(result.get("requested_trees"), int):
        raise PackingError("packing dimensions mismatch")
    requested = result["requested_trees"]
    if requested < 1:
        raise PackingError("invalid requested tree count")
    if result.get("complete") is True:
        trees = result.get("trees")
        if not isinstance(trees, list) or len(trees) != requested:
            raise PackingError("wrong number of trees")
        verify_trees(n, edges, trees)
    elif result.get("complete") is False:
        verify_obstruction(n, edges, requested, result.get("obstruction_partition"))
    else:
        raise PackingError("missing completion status")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("certificate", type=Path)
    parser.add_argument("--trees", type=int, help="requested number of edge-disjoint trees")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify", type=Path, help="verify a previous packing JSON instead of constructing")
    args = parser.parse_args()
    try:
        certificate = json.loads(args.certificate.read_text(encoding="utf-8"))
        n, edges = expand_compressed(certificate)
        if args.verify:
            result = json.loads(args.verify.read_text(encoding="utf-8"))
            verify_result(n, edges, result)
            print("packing certificate verified")
            return 0
        requested = (args.trees if args.trees is not None
                     else max(1, certificate["compressed_connectivity_lower_bound"] // 2))
        if requested < 1:
            raise PackingError("requested number of trees must be positive")
        forests, complete, partition = pack_forests(n, edges, requested)
        if complete:
            trees = [sorted(forest) for forest in forests]
            verify_trees(n, edges, trees)
        else:
            trees = []
        result = {"n": n, "requested_trees": requested, "complete": complete,
                  "union_size": sum(map(len, forests)) if requested * (n - 1) <= len(edges) else None,
                  "trees": trees, "obstruction_partition": partition}
        if partition is not None:
            crossing = verify_obstruction(n, edges, requested, partition)
            result["obstruction_crossing_edges"] = crossing
            result["obstruction_required_edges"] = requested * (len(set(partition)) - 1)
        verify_result(n, edges, result)
        payload = json.dumps(result, indent=2) + "\n"
        if args.output:
            args.output.write_text(payload, encoding="utf-8")
        else:
            print(payload, end="")
    except (OSError, ValueError, KeyError, TypeError, PackingError) as exc:
        parser.exit(2, f"packing rejected: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
