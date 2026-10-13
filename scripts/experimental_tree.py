#!/usr/bin/env python3
"""Bounded, certificate-driven sparsification experiments on rational HK input.

Uses admissible terminal shortcuts X=c L_H (c=1,2,3), checked exactly.
This is an experimental strategy, not Proposition 3.1's
general continuation algorithm or a universal constant-factor guarantee.
Every accepted round and the final tree can be verified without rerunning
the frame search, signing, or matroid-union construction.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import time
from fractions import Fraction as F
from math import gcd
from pathlib import Path

from certify_compress import certify_and_compress, read_hk
from continuation_oracle import _laplacian
from continuation_solver import dyadic_g, finalize_shortcut
from continuation_state import ContinuationState
from tree_packing import expand_compressed, pack_forests, verify_trees
from verified_sparsification import (automatic_sparsification_step,
                                     certified_spectral_error,
                                     verify_shortcut_cone, verify_sparsification)


def exact_cut_ratio(n: int, numerator: list[tuple[int, int, int]],
                    denominator: list[tuple[int, int, int]]) -> tuple[F, list[int]]:
    """Enumerate one side of each undirected cut; explicit small-n oracle."""
    if not 2 <= n <= 16:
        raise ValueError("experimental all-cut verifier supports 2<=n<=16")
    worst, side = F(), []
    for mask in range(1, (1 << n)-1, 2):
        top = sum(w for u, v, w in numerator if ((mask >> u) ^ (mask >> v)) & 1)
        bottom = sum(w for u, v, w in denominator if ((mask >> u) ^ (mask >> v)) & 1)
        if bottom <= 0:
            raise ValueError("disconnected denominator graph")
        ratio = F(top, bottom)
        if ratio > worst:
            worst = ratio
            side = [v for v in range(n) if mask >> v & 1]
    return worst, side


def weighted_edges(edges: list[tuple[int, int]]) -> list[tuple[int, int, int]]:
    counts: dict[tuple[int, int], int] = {}
    for pair in edges:
        counts[pair] = counts.get(pair, 0) + 1
    return [(u, v, w) for (u, v), w in sorted(counts.items())]


def direct_shortcut(n: int, edges: list[tuple[int, int]], r: int) -> ContinuationState:
    """Try terminal scalar Laplacians; reject when their packing test fails."""
    s = 1
    while s**4 < r:
        s *= 2
    lap = _laplacian(n, edges)
    for scale in (1, 2, 3):
        state = ContinuationState(n, edges, r, dyadic_g(r),
                                  [[scale*x for x in row] for row in lap],
                                  F(s), F(r))
        if state.verify_invariant() and verify_shortcut_cone(state):
            return state
    raise ValueError("no checked scalar-Laplacian terminal shortcut")


def build_tree(n: int, original: list[tuple[int, int]], r: int,
               max_rounds: int = 32, frame_cap: int = 200,
               signing_method: str = "frobenius", signing_cap: int = 100,
               stop_r: int = 2,
               exact_measurements: bool = False,
               ) -> dict:
    if n < 2 or (exact_measurements and n > 16) or r < 1 or max_rounds < 0 or frame_cap < 1 or signing_cap < 1 or stop_r < 1:
        raise ValueError("invalid experimental dimensions or limits")
    original = [tuple(pair) for pair in original]
    if any(not 0 <= u < v < n for u, v in original):
        raise ValueError("invalid experimental edge")
    start = time.perf_counter()
    full = [(u, v, e) for e, (u, v) in enumerate(original)]
    forests, complete, obstruction = pack_forests(n, full, r)
    if not complete:
        raise ValueError(f"initial tree packing failed: {obstruction}")
    packing = [sorted(tree) for tree in forests]
    initial_packing = packing
    ids = list(range(len(original)))
    rounds = []
    product = F(1)
    exact_product = F(1) if exact_measurements else None
    stop_reason = "packing_cutoff"
    while r > stop_r:
        if len(rounds) >= max_rounds:
            stop_reason = "round_limit"
            break
        edges = [original[e] for e in ids]
        round_start = time.perf_counter()
        try:
            state = direct_shortcut(n, edges, r)
            lookup = {e: local for local, e in enumerate(ids)}
            union = [[lookup[e] for e in tree] for tree in packing]
            ramp = state.ramp()
            union_source = "current_packing"
            if any(ramp[e] <= 0 for tree in union for e in tree):
                _, union = finalize_shortcut(state)
                union_source = "low_resistance_repacking"
            step = None
            failures = []
            for edge_order in ("pairs", "trees"):
                try:
                    step = automatic_sparsification_step(
                        state, union, frame_iteration_cap=frame_cap,
                        signing_method=signing_method, signing_step_cap=signing_cap,
                        tighten_error=True, try_complement=True,
                        frame_method="balancing", edge_order=edge_order,
                        materialize_padding=exact_measurements)
                    break
                except (ValueError, RuntimeError) as exc:
                    failures.append(str(exc))
            if step is None:
                raise ValueError("; ".join(failures))
        except (ValueError, RuntimeError) as exc:
            stop_reason = f"experimental_step_unavailable: {exc}"
            break
        cert = step.certificate
        selected = [ids[e] for e in cert.selected_edges]
        if len(selected) >= len(ids):
            stop_reason = "no_edge_reduction"
            break
        epsilon = certified_spectral_error(state, [e for tree in union for e in tree],
                                           cert.selected_edges)
        load, cut = None, None
        if exact_measurements:
            load, cut = exact_cut_ratio(n, weighted_edges([original[e] for e in selected]),
                                       weighted_edges(edges))
            if load > cert.cut_load_factor:
                raise AssertionError("spectral cut certificate contradicts exact cuts")
        product *= cert.cut_load_factor
        if exact_measurements:
            exact_product *= load
        packing = [[ids[e] for e in tree] for tree in cert.packed_trees]
        rounds.append({
            "r": r, "r_next": cert.r_next, "edges_before": len(ids),
            "edges_after": len(selected), "s": str(state.s), "q": str(state.q),
            "x": [[str(x) for x in row] for row in state.x],
            "cone_lambda": {key: str(x) for key, x in state.cone_lambda.items()},
            "union_trees": [[ids[e] for e in tree] for tree in union],
            "selected_edges": selected, "packed_trees": packing,
            "epsilon": str(epsilon), "cut_load_factor": str(cert.cut_load_factor),
            "exact_cut_load_factor": str(load) if load is not None else None, "worst_cut": cut,
            "signing_method": signing_method,
            "frame_method": "balancing", "edge_order": edge_order,
            "union_source": union_source,
            "frame_iterations": step.frame_iterations,
            "residual_columns": step.residual_columns,
            "padding_materialized": exact_measurements,
            "seconds": time.perf_counter()-round_start,
        })
        ids, r = selected, cert.r_next
    if r == 1 and stop_reason == "packing_cutoff":
        stop_reason = "packing_reached_one"
    # Compare the already constructed final packing trees, without enumerating
    # all spanning trees or adding a different constructor as a fallback.
    if exact_measurements:
        denominator = weighted_edges(original)
        scored = [(exact_cut_ratio(n, [(original[e][0], original[e][1], 1) for e in tree],
                                   denominator)[0], tree) for tree in packing]
        thinness, tree = min(scored, key=lambda item: (item[0], item[1]))
    else:
        thinness, tree = None, min(packing)
    return {
        "initial_r": len(initial_packing), "initial_packing": initial_packing,
        "rounds": rounds, "stop_reason": stop_reason, "final_r": r,
        "final_edges": ids, "final_tree": tree,
        "spectral_product": str(product), "exact_cut_product": str(exact_product) if exact_measurements else None,
        "compressed_tree_thinness": str(thinness) if thinness is not None else None,
        "exact_measurements": exact_measurements,
        "seconds": time.perf_counter()-start,
        "limits": {"max_rounds": max_rounds, "frame_cap": frame_cap,
                   "signing_cap": signing_cap, "stop_r": stop_r},
    }


def verify_trace(n: int, original: list[tuple[int, int]], trace: dict) -> None:
    """Replay certificates; do not run a frame/signing/packing search."""
    full = [(u, v, e) for e, (u, v) in enumerate(original)]
    verify_trees(n, full, trace["initial_packing"])
    r = trace["initial_r"]
    if r < 1 or len(trace["initial_packing"]) != r:
        raise ValueError("initial packing count mismatch")
    ids = list(range(len(original)))
    exact_measurements = trace.get("exact_measurements", True)
    if n < 2 or (exact_measurements and n > 16):
        raise ValueError("invalid verification dimensions")
    product = F(1)
    exact_product = F(1) if exact_measurements else None
    packing = trace["initial_packing"]
    for row in trace["rounds"]:
        if row["r"] != r or row["edges_before"] != len(ids):
            raise ValueError("round input mismatch")
        edges = [original[e] for e in ids]
        lookup = {e: local for local, e in enumerate(ids)}
        try:
            union = [[lookup[e] for e in tree] for tree in row["union_trees"]]
            selected = [lookup[e] for e in row["selected_edges"]]
            trees = [[lookup[e] for e in tree] for tree in row["packed_trees"]]
        except KeyError as exc:
            raise ValueError("round references an edge outside the current graph") from exc
        state = ContinuationState(n, edges, r, dyadic_g(r),
                                  [[F(x) for x in line] for line in row["x"]],
                                  F(row["s"]), F(row["q"]),
                                  {key: F(x) for key, x in row["cone_lambda"].items()})
        cert = verify_sparsification(state, union, selected, F(row["epsilon"]), trees)
        if (cert.r_next != row["r_next"] or len(selected) != row["edges_after"]
                or len(selected) >= len(ids)
                or cert.cut_load_factor != F(row["cut_load_factor"])):
            raise ValueError("round output mismatch")
        if exact_measurements:
            load, cut = exact_cut_ratio(n, weighted_edges([edges[e] for e in selected]),
                                      weighted_edges(edges))
            if (load != F(row["exact_cut_load_factor"]) or load > cert.cut_load_factor
                    or cut != row["worst_cut"]):
                raise ValueError("cut load mismatch")
            exact_product *= load
        elif row["exact_cut_load_factor"] is not None or row["worst_cut"] is not None:
            raise ValueError("unverified exact cut measurements in spectral trace")
        product *= cert.cut_load_factor
        ids, r, packing = row["selected_edges"], cert.r_next, row["packed_trees"]
    if ids != trace["final_edges"] or r != trace["final_r"]:
        raise ValueError("final graph mismatch")
    if product != F(trace["spectral_product"]) or (
            exact_measurements and exact_product != F(trace["exact_cut_product"])):
        raise ValueError("accumulated cut bound mismatch")
    tree = trace["final_tree"]
    if tree not in packing or any(e not in ids for e in tree):
        raise ValueError("final tree is not in the certified packing")
    verify_trees(n, full, [tree])
    if exact_measurements:
        beta, _ = exact_cut_ratio(n, [(original[e][0], original[e][1], 1) for e in tree],
                                 weighted_edges(original))
        if beta != F(trace["compressed_tree_thinness"]) or beta > exact_product:
            raise ValueError("final tree thinness mismatch")
    elif trace["compressed_tree_thinness"] is not None or trace["exact_cut_product"] is not None:
        raise ValueError("unverified exact thinness in spectral trace")


def prepare_graph(n: int, denominator: int, arcs: list[tuple[int, int, int]],
                  compression: dict, exact_measurements: bool
                  ) -> tuple[list[tuple[int, int]], int, F, str]:
    """Prefer reduced original copies when fewer than certified compressed copies.

    Reducing a common integer factor preserves z. Original multiplicities
    then have connectivity 2D and supply D trees. The copy-count comparison
    prevents expanding numerical multiplicities larger than the O(n^4) bound.
    """
    divisor = denominator
    for _, _, numerator in arcs:
        divisor = gcd(divisor, numerator)
    reduced_d = denominator//divisor
    if not exact_measurements and sum(num//divisor for _, _, num in arcs) < compression["explicit_copy_count"]:
        masses = {}
        for u, v, num in arcs:
            pair = tuple(sorted((u, v)))
            masses[pair] = masses.get(pair, 0) + num//divisor
        edges = [pair for pair, count in sorted(masses.items()) for _ in range(count)]
        return edges, reduced_d, F(reduced_d), "reduced_original"
    _, copies = expand_compressed(compression)
    return [(u, v) for u, v, _ in copies], n*n//2, F(n*n), "section6_compressed"


def construct(n: int, denominator: int, arcs: list[tuple[int, int, int]], **limits) -> dict:
    compression = certify_and_compress(n, denominator, arcs)
    exact_measurements = limits.get("exact_measurements", False)
    original, r, projection, graph_kind = prepare_graph(n, denominator, arcs, compression, exact_measurements)
    trace = build_tree(n, original, r, **limits)
    pairs = [original[e] for e in trace["final_tree"]]
    masses: dict[tuple[int, int], int] = {}
    for u, v, numerator in arcs:
        key = tuple(sorted((u, v)))
        masses[key] = masses.get(key, 0) + numerator
    weights = [(u, v, mass) for (u, v), mass in masses.items() if mass]
    ratio, cut = None, None
    if exact_measurements:
        ratio, cut = exact_cut_ratio(n, [(u, v, denominator) for u, v in pairs], weights)
    divisor = denominator
    for _, _, num in arcs:
        divisor = gcd(divisor, num)
    support_bound = min(F(denominator//divisor), F(n-1, 2))
    return {"schema": "experimental-thin-tree-v2", "backend": "checked_laplacian_sparsification",
            "scope": "instance certificate; no universal constant guarantee",
            "n": n, "denominator": denominator, "arcs": arcs,
            "compression": compression, "trace": trace, "tree_pairs": pairs,
            "input_graph_kind": graph_kind, "input_graph_copy_count": len(original),
            "projection_multiplier": str(projection),
            "beta_exact": str(ratio) if ratio is not None else None, "beta_worst_cut": cut,
            "beta_support_bound": str(support_bound),
            "beta_bound_for_aks": str(ratio if exact_measurements else support_bound),
            "beta_from_spectral_chain": str(projection*F(trace["spectral_product"])),
            "beta_from_exact_cut_chain": str(projection*F(trace["exact_cut_product"])) if exact_measurements else None}


def verify_report(report: dict) -> None:
    if report["schema"] not in ("experimental-thin-tree-v1", "experimental-thin-tree-v2"):
        raise ValueError("unknown certificate schema")
    n, denominator = report["n"], report["denominator"]
    compression = certify_and_compress(n, denominator, [tuple(a) for a in report["arcs"]])
    if compression != report["compression"]:
        raise ValueError("compression mismatch")
    exact_measurements = report["trace"].get("exact_measurements", True)
    edges, initial_r, projection, kind = prepare_graph(n, denominator, [tuple(a) for a in report["arcs"]],
                                                      compression, exact_measurements)
    if report["schema"] == "experimental-thin-tree-v2" and (
            kind != report["input_graph_kind"] or len(edges) != report["input_graph_copy_count"]
            or projection != F(report["projection_multiplier"])):
        raise ValueError("prepared input graph mismatch")
    if report["trace"]["initial_r"] != initial_r:
        raise ValueError("initial graph packing parameter mismatch")
    verify_trace(n, edges, report["trace"])
    pairs = [edges[e] for e in report["trace"]["final_tree"]]
    if pairs != [tuple(pair) for pair in report["tree_pairs"]]:
        raise ValueError("tree projection mismatch")
    masses = {}
    for u, v, numerator in report["arcs"]:
        key = tuple(sorted((u, v)))
        masses[key] = masses.get(key, 0) + numerator
    beta = None
    if exact_measurements:
        beta, cut = exact_cut_ratio(n, [(u, v, denominator) for u, v in pairs],
                                  [(u, v, mass) for (u, v), mass in masses.items() if mass])
        if beta != F(report["beta_exact"]) or cut != report["beta_worst_cut"]:
            raise ValueError("projected thinness mismatch")
    elif report["beta_exact"] is not None or report["beta_worst_cut"] is not None:
        raise ValueError("unverified exact thinness in spectral report")
    for field, factor in (("beta_from_spectral_chain", "spectral_product"),
                          ("beta_from_exact_cut_chain", "exact_cut_product")):
        if not exact_measurements and factor == "exact_cut_product":
            if report[field] is not None:
                raise ValueError("unverified exact chain bound")
            continue
        bound = projection*F(report["trace"][factor])
        if F(report[field]) != bound or (beta is not None and beta > bound):
            raise ValueError("projected chain bound mismatch")
    if report["schema"] == "experimental-thin-tree-v2":
        divisor = denominator
        for _, _, num in report["arcs"]:
            divisor = gcd(divisor, num)
        support_bound = min(F(denominator//divisor), F(n-1, 2))
        if F(report["beta_support_bound"]) != support_bound or F(report["beta_bound_for_aks"]) != (
                beta if exact_measurements else support_bound):
            raise ValueError("AKS support bound mismatch")


def run_aks(report: dict, executable: Path, backend: str | None = None) -> str:
    """Send a reduced HK certificate to C++ for rounding or comparisons."""
    exact_measurements = report["trace"].get("exact_measurements", True)
    if backend is None:
        backend = "round-supplied-tree" if exact_measurements else "round-supported-tree"
    if backend in ("construct-certified", "round-supplied-tree") and not exact_measurements:
        raise ValueError("exhaustive reference requires explicit exact-small measurements")
    if backend not in ("round-supplied-tree", "round-supported-tree", "construct-polynomial-baseline", "construct-certified"):
        raise ValueError("unknown C++ comparison backend")
    verify_report(report)
    divisor = report["denominator"]
    for _, _, numerator in report["arcs"]:
        divisor = gcd(divisor, numerator)
    denominator = report["denominator"]//divisor
    beta = F(report.get("beta_bound_for_aks", report["beta_exact"]))
    if max(denominator, beta.denominator) >= 1 << 64 or beta.numerator >= 1 << 63:
        raise ValueError("AKS C++ bridge requires reduced integers below 2^64")
    with tempfile.TemporaryDirectory(prefix="kltn-aks-") as tmp:
        hk = Path(tmp)/"hk.txt"
        hk.write_text(f"{report['n']} {denominator} {len(report['arcs'])}\n" +
                      "".join(f"{u} {v} {num//divisor}\n" for u, v, num in report["arcs"]))
        tree = Path(tmp)/"tree.txt"
        tree.write_text(f"{report['n']} {beta.numerator} {beta.denominator} {len(report['tree_pairs'])}\n" +
                        "".join(f"{u} {v}\n" for u, v in report["tree_pairs"]))
        command = [str(executable.resolve()), backend, str(hk)]
        if backend in ("round-supplied-tree", "round-supported-tree"):
            command.append(str(tree))
        result = subprocess.run(command,
                                check=True, text=True, capture_output=True, timeout=60)
        return result.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, nargs="?")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--batsp", type=Path)
    parser.add_argument("--max-rounds", type=int, default=32)
    parser.add_argument("--frame-cap", type=int, default=200)
    parser.add_argument("--signing-method", choices=("frobenius", "appendix_a"), default="frobenius")
    parser.add_argument("--signing-cap", type=int, default=100)
    parser.add_argument("--stop-r", type=int, default=2)
    parser.add_argument("--exact-small", action="store_true", help="opt in to exhaustive cut measurements for n<=16")
    args = parser.parse_args()
    if args.verify:
        verify_report(json.loads(args.verify.read_text()))
        print("experimental tree certificate verified")
        return
    if not args.input:
        parser.error("an HK input or --verify certificate is required")
    n, denominator, arcs = read_hk(args.input)
    report = construct(n, denominator, arcs, max_rounds=args.max_rounds,
                       frame_cap=args.frame_cap, signing_method=args.signing_method,
                       signing_cap=args.signing_cap, stop_r=args.stop_r,
                       exact_measurements=args.exact_small)
    verify_report(report)
    if args.batsp:
        report["aks_output"] = run_aks(report, args.batsp)
    if args.output:
        args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"n": n, "rounds": len(report["trace"]["rounds"]),
                      "edges": [report["input_graph_copy_count"], len(report["trace"]["final_edges"])],
                      "beta_bound_for_aks": report["beta_bound_for_aks"],
                      "beta_exact": report["beta_exact"], "stop_reason": report["trace"]["stop_reason"],
                      "seconds": report["trace"]["seconds"]}, ensure_ascii=False))
    if "aks_output" in report:
        print(report["aks_output"], end="")


if __name__ == "__main__":
    main()
