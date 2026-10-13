#!/usr/bin/env python3
"""Run the existing checked tree + AKS pipeline on TSPLIB cost matrices.

SciPy/HiGHS is used only for the Held--Karp input adapter. Separation and
acceptance use integral min-cuts, never subset or Hamiltonian enumeration.
Neither the tree constructor nor the AKS implementation is modified.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import re
import signal
import sys
import time
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from certify_compress import min_cut
from experimental_tree import construct, run_aks

PAPER = "https://cedric.cnam.fr/~bentzc/INITREC/Files/CB1.pdf"
# LaRusic & Punnen, Computers & Operations Research 43 (2014), Table 5.
# These are bottleneck optima, not the minimum-sum optima on the TSPLIB site.
PUBLISHED_OPT = {"br17": 8, "ft53": 977, "ft70": 1398, "ftv33": 113,
                 "ftv35": 113, "ftv38": 113, "ftv44": 113, "ftv47": 104,
                 "ftv55": 64, "ftv64": 104, "ftv70": 104, "p43": 5008,
                 "ry48p": 577}


def read_tsplib(path: Path) -> tuple[dict, list[list[int]]]:
    text = path.read_text()
    header, body = text.split("EDGE_WEIGHT_SECTION", 1)
    meta = {}
    for line in header.splitlines():
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    if (meta.get("TYPE"), meta.get("EDGE_WEIGHT_TYPE"), meta.get("EDGE_WEIGHT_FORMAT")) != (
            "ATSP", "EXPLICIT", "FULL_MATRIX"):
        raise ValueError("expected ATSP / EXPLICIT / FULL_MATRIX")
    n = int(meta["DIMENSION"])
    values = list(map(int, body.split("EOF", 1)[0].split()))
    if n < 2 or len(values) != n*n or any(v < 0 for v in values):
        raise ValueError("invalid cost matrix")
    matrix = [values[i*n:(i+1)*n] for i in range(n)]
    # Diagonal sentinel values in TSPLIB do not represent travel edges.
    for i in range(n):
        matrix[i][i] = 0
    return meta, matrix


def matrix_sha256(matrix: list[list[int]]) -> str:
    return hashlib.sha256(json.dumps(matrix, separators=(",", ":")).encode()).hexdigest()


def triangle_violations(matrix: list[list[int]]) -> int:
    n = len(matrix)
    return sum(matrix[i][j] > matrix[i][k]+matrix[k][j]
               for i in range(n) for j in range(n) if i != j for k in range(n))


def validate_tour(matrix: list[list[int]], tour: list[int]) -> tuple[int, int]:
    n = len(matrix)
    if len(tour) != n+1 or tour[0] != tour[-1] or set(tour[:-1]) != set(range(n)):
        raise ValueError("invalid Hamiltonian tour")
    costs = [matrix[u][v] for u, v in zip(tour, tour[1:])]
    return max(costs), sum(costs)


def rational_solution(n: int, edges: list[tuple[int, int]], values) -> tuple[int, list[tuple[int, int, int]]]:
    fractions = [F(float(x)).limit_denominator(1_000_000) for x in values]
    if any(q < 0 for q in fractions):
        raise ValueError("negative rational LP coordinate")
    denominator = math.lcm(*(q.denominator for q in fractions))
    arcs = [(u, v, int(q*denominator)) for (u, v), q in zip(edges, fractions) if q]
    incoming, outgoing = [0]*n, [0]*n
    for u, v, num in arcs:
        outgoing[u] += num
        incoming[v] += num
    if incoming != [denominator]*n or outgoing != [denominator]*n:
        raise ValueError("LP rational reconstruction failed exact degree equalities")
    return denominator, arcs


def violated_cuts(n: int, denominator: int, arcs: list[tuple[int, int, int]]) -> list[tuple[int, ...]]:
    cuts = set()
    for v in range(1, n):
        for source, sink in ((0, v), (v, 0)):
            value, side = min_cut(n, arcs, source, sink)
            if value < denominator:
                cuts.add(tuple(sorted(side)))
    return sorted(cuts)


def verify_infeasibility(n: int, edges: list[tuple[int, int]], proof: dict) -> None:
    """Exact Farkas check: lambda*A >= 0, lambda*b < 0, lambda >= 0."""
    coefficients = [F() for _ in edges]
    rhs = F()
    for entry in proof["multipliers"]:
        weight = F(entry["weight"])
        if weight <= 0:
            raise ValueError("invalid Farkas multiplier")
        kind, sign = entry["kind"], entry["sign"]
        if kind in ("out", "in"):
            vertex = entry["vertex"]
            if sign not in (-1, 1) or not 0 <= vertex < n:
                raise ValueError("invalid degree multiplier")
            rhs += weight*sign
            for i, (u, v) in enumerate(edges):
                if (u if kind == "out" else v) == vertex:
                    coefficients[i] += weight*sign
        elif kind == "cut":
            side = set(entry["side"])
            if sign != -1 or not side or len(side) == n or not side <= set(range(n)):
                raise ValueError("invalid cut multiplier")
            rhs -= weight
            for i, (u, v) in enumerate(edges):
                if u in side and v not in side:
                    coefficients[i] -= weight
        else:
            raise ValueError("invalid Farkas row")
    if any(q < 0 for q in coefficients) or rhs >= 0 or F(proof["weighted_rhs"]) != rhs:
        raise ValueError("unverified LP infeasibility")


def farkas_certificate(n, edges, equalities, cut_matrix, cuts):
    import numpy as np
    from scipy.optimize import linprog
    from scipy.sparse import hstack, vstack
    # Phase I makes the relaxation feasible; dual weights certify that the
    # original degree/cut system with nonnegative x is infeasible.
    matrix = vstack([equalities, -equalities, cut_matrix], format="csr")
    rhs = np.array([1.]*(2*n)+[-1.]*(2*n+len(cuts)))
    relaxed = hstack([matrix, -np.ones((len(rhs), 1))], format="csr")
    objective = np.zeros(len(edges)+1)
    objective[-1] = 1
    result = linprog(objective, A_ub=relaxed, b_ub=rhs,
                     bounds=(0, None), method="highs-ds")
    if not result.success or result.fun <= 1e-8:
        raise ValueError("no positive Phase I optimum")
    labels = ([{"kind": kind, "vertex": v, "sign": sign}
               for sign in (1, -1) for kind in ("out", "in") for v in range(n)] +
              [{"kind": "cut", "side": list(side), "sign": -1} for side in cuts])
    multipliers = []
    weighted_rhs = F()
    for row, value, bound in zip(labels, result.ineqlin.marginals, rhs):
        weight = F(float(-value)).limit_denominator(1_000_000)
        if weight:
            multipliers.append({**row, "weight": str(weight)})
            weighted_rhs += weight*int(bound)
    proof = {"multipliers": multipliers, "weighted_rhs": str(weighted_rhs),
             "verification": "exact rational Farkas certificate"}
    verify_infeasibility(n, edges, proof)
    return proof


def held_karp_at_threshold(matrix, threshold, cap=500):
    import numpy as np
    from scipy.optimize import linprog
    from scipy.sparse import coo_matrix
    n = len(matrix)
    edges = [(u, v) for u in range(n) for v in range(n) if u != v and matrix[u][v] <= threshold]
    m = len(edges)
    if not m:
        return {"feasible": False, "reason": "no_edges", "threshold": threshold}
    equalities = coo_matrix(([1.]*(2*m),
                            ([u for u, v in edges]+[n+v for u, v in edges], list(range(m))*2)),
                           shape=(2*n, m)).tocsr()
    cuts, seen = [], set()
    for iteration in range(cap):
        rows, columns = [], []
        for i, side in enumerate(cuts):
            members = set(side)
            for j, (u, v) in enumerate(edges):
                if u in members and v not in members:
                    rows.append(i)
                    columns.append(j)
        cut_matrix = coo_matrix(([-1.]*len(rows), (rows, columns)), shape=(len(cuts), m)).tocsr()
        result = linprog(np.zeros(m), A_ub=cut_matrix if cuts else None,
                         b_ub=-np.ones(len(cuts)) if cuts else None,
                         A_eq=equalities, b_eq=np.ones(2*n), bounds=(0, None), method="highs-ds")
        if result.status == 2:
            proof = farkas_certificate(n, edges, equalities, cut_matrix, cuts)
            return {"feasible": False, "threshold": threshold, "iterations": iteration+1,
                    "cut_count": len(cuts), "proof": proof}
        if not result.success:
            raise RuntimeError(f"LP failed: {result.message}")
        denominator, arcs = rational_solution(n, edges, result.x)
        violations = violated_cuts(n, denominator, arcs)
        if not violations:
            return {"feasible": True, "threshold": threshold, "denominator": denominator,
                    "arcs": arcs, "iterations": iteration+1, "cut_count": len(cuts),
                    "verification": "exact degrees and integral root-v min-cuts"}
        new = [side for side in violations if side not in seen]
        if not new:
            raise ValueError("LP repeats an exactly violated constraint")
        cuts.extend(new)
        seen.update(new)
    raise RuntimeError("Held--Karp separation iteration limit")


def held_karp_threshold(matrix):
    n = len(matrix)
    costs = sorted({matrix[u][v] for u in range(n) for v in range(n) if u != v})
    cache, log = {}, []
    def solve(index):
        if index not in cache:
            started = time.perf_counter()
            answer = held_karp_at_threshold(matrix, costs[index])
            cache[index] = answer
            log.append({"threshold": costs[index], "feasible": answer["feasible"],
                        "iterations": answer.get("iterations", 0), "cuts": answer.get("cut_count", 0),
                        "seconds": time.perf_counter()-started})
        return cache[index]
    low, high = 0, len(costs)-1
    while low < high:
        mid = (low+high)//2
        if solve(mid)["feasible"]:
            high = mid
        else:
            low = mid+1
    answer = solve(low)
    if not answer["feasible"]:
        raise ValueError("complete graph Held--Karp feasibility failed")
    predecessor = solve(low-1) if low else None
    if predecessor and predecessor["feasible"]:
        raise AssertionError("threshold search mismatch")
    return {**answer, "predecessor": predecessor, "queries": log,
            "lower_bound_certified": True, "subset_enumeration": False}


def timeout_handler(signum, frame):
    raise TimeoutError("per-instance wall clock limit exceeded")


def verify_saved_result(path: Path, input_dir: Path) -> None:
    """Verify stored lower bound and weighted tour without solving an LP."""
    report = json.loads(path.read_text())
    _, matrix = read_tsplib(input_dir/(report["name"]+".atsp"))
    if matrix_sha256(matrix) != report["matrix_sha256"]:
        raise ValueError("benchmark input matrix changed")
    if "hk" not in report:
        if report["status"] == "ok":
            raise ValueError("completed run is missing its Held--Karp certificate")
        return
    hk = report["hk"]
    n, denominator = len(matrix), hk["denominator"]
    arcs = [tuple(arc) for arc in hk["arcs"]]
    outgoing, incoming, seen = [0]*n, [0]*n, set()
    for u, v, mass in arcs:
        if not (0 <= u < n and 0 <= v < n and u != v and 0 < mass <= denominator) or (u, v) in seen:
            raise ValueError("invalid stored HK arc")
        seen.add((u, v))
        if matrix[u][v] > hk["threshold"]:
            raise ValueError("HK support exceeds original-cost threshold")
        outgoing[u] += mass
        incoming[v] += mass
    if outgoing != [denominator]*n or incoming != [denominator]*n or violated_cuts(n, denominator, arcs):
        raise ValueError("invalid stored HK solution")
    costs = sorted({matrix[u][v] for u in range(n) for v in range(n) if u != v})
    index = costs.index(hk["threshold"])
    previous = hk["predecessor"]
    if index:
        if previous is None or previous["threshold"] != costs[index-1] or previous["feasible"]:
            raise ValueError("missing immediate predecessor certificate")
        edges = [(u, v) for u in range(n) for v in range(n)
                 if u != v and matrix[u][v] <= previous["threshold"]]
        if edges:
            verify_infeasibility(n, edges, previous["proof"])
    elif previous is not None:
        raise ValueError("unexpected predecessor")
    if report["status"] != "ok":
        return
    bottleneck, total = validate_tour(matrix, report["tour"])
    if (bottleneck, total) != (report["bottleneck"], report["total_cost"]):
        raise ValueError("stored weighted tour cost mismatch")
    if bottleneck < hk["threshold"]:
        raise ValueError("tour contradicts HK lower bound")
    if triangle_violations(matrix) != report["triangle_violations"]:
        raise ValueError("metric assumption annotation mismatch")


def run_case(path, executable, output, timeout):
    started = time.perf_counter()
    meta, matrix = read_tsplib(path)
    name, n = meta["NAME"], len(matrix)
    stage = "metric_check"
    report = {"name": name, "n": n, "objective": "maximum original directed edge cost",
              "matrix_transformation": "none; diagonal excluded",
              "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "matrix_sha256": matrix_sha256(matrix), "published_bottleneck_optimum": PUBLISHED_OPT.get(name),
              "published_optimum_source": PAPER, "exact_references_run": False}
    signal.alarm(timeout)
    try:
        report["triangle_violations"] = triangle_violations(matrix)
        report["metric"] = report["triangle_violations"] == 0
        stage = "held_karp_input"
        lp_started = time.perf_counter()
        hk = held_karp_threshold(matrix)
        report["hk"] = hk
        report["hk_seconds"] = time.perf_counter()-lp_started
        output.joinpath(name+".hk.txt").write_text(
            f"{n} {hk['denominator']} {len(hk['arcs'])}\n" +
            "".join(f"{u} {v} {num}\n" for u, v, num in hk["arcs"]))
        print(f"{name}: exact HK threshold={hk['threshold']}, denominator={hk['denominator']}, "
              f"support={len(hk['arcs'])}, metric={report['metric']}; running main constructor", flush=True)
        stage = "tree_construction"
        tree_started = time.perf_counter()
        tree = construct(n, hk["denominator"], hk["arcs"])
        report["tree_seconds"] = time.perf_counter()-tree_started
        output.joinpath(name+".tree.json").write_text(json.dumps(tree, indent=2)+"\n")
        report["tree"] = {"rounds": len(tree["trace"]["rounds"]),
                          "stop_reason": tree["trace"]["stop_reason"],
                          "initial_copies": tree["input_graph_copy_count"],
                          "final_edges": len(tree["trace"]["final_edges"]),
                          "beta_bound": tree["beta_bound_for_aks"]}
        stage = "aks_rounding"
        aks_started = time.perf_counter()
        stdout = run_aks(tree, executable)
        report["aks_seconds"] = time.perf_counter()-aks_started
        report["aks_output"] = stdout
        tour = list(map(int, re.search(r"^tour=([^\n]+)", stdout, re.M)[1].split()))
        stage = "original_cost_validation"
        bottleneck, total = validate_tour(matrix, tour)
        report.update(status="ok", tour=tour, bottleneck=bottleneck, total_cost=total,
                      ratio_to_hk_lower_bound=bottleneck/hk["threshold"] if hk["threshold"] else None,
                      ratio_to_published_optimum=bottleneck/PUBLISHED_OPT[name] if name in PUBLISHED_OPT else None,
                      theorem_assumptions_satisfied=report["metric"])
    except Exception as exc:
        report.update(status="timeout" if isinstance(exc, TimeoutError) else "error", stage=stage,
                      error=f"{type(exc).__name__}: {exc}")
    finally:
        signal.alarm(0)
    report["seconds"] = time.perf_counter()-started
    output.joinpath(name+".json").write_text(json.dumps(report, indent=2)+"\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batsp", type=Path)
    parser.add_argument("--input-dir", type=Path, default=ROOT/"instances/tsplib")
    parser.add_argument("--output-dir", type=Path, default=ROOT/"results/tsplib")
    parser.add_argument("--names", nargs="+")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--verify-results", action="store_true")
    args = parser.parse_args()
    if args.timeout < 1:
        parser.error("timeout must be positive")
    if args.verify_results:
        paths = sorted(p for p in args.output_dir.glob("*.json")
                       if p.name != "environment.json" and not p.name.endswith(".tree.json"))
        if not paths:
            parser.error("no saved benchmark results")
        for path in paths:
            verify_saved_result(path, args.input_dir)
            if json.loads(path.read_text())["status"] == "ok":
                print(f"verified {path.stem}: weighted tour and exact HK lower bound", flush=True)
            else:
                has_hk = "hk" in json.loads(path.read_text())
                print(f"recorded {path.stem}: incomplete run, no tour claimed" +
                      ("; exact HK lower bound verified" if has_hk else ""), flush=True)
        return
    if args.batsp is None:
        parser.error("--batsp is required for benchmark execution")
    import scipy
    import numpy
    args.output_dir.mkdir(parents=True, exist_ok=True)
    source_paths = [ROOT/"scripts"/name for name in (
        "experimental_tree.py", "verified_sparsification.py", "rational_frame.py", "tree_packing.py")]
    environment = {"python": platform.python_version(), "scipy": scipy.__version__,
                   "numpy": numpy.__version__, "lp_method": "highs-ds", "per_case_timeout": args.timeout,
                   "platform": platform.platform(),
                   "binary_sha256": hashlib.sha256(args.batsp.read_bytes()).hexdigest(),
                   "constructor_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                          for p in source_paths}}
    args.output_dir.joinpath("environment.json").write_text(json.dumps(environment, indent=2)+"\n")
    signal.signal(signal.SIGALRM, timeout_handler)
    paths = sorted(args.input_dir.glob("*.atsp"), key=lambda p: (int(read_tsplib(p)[0]["DIMENSION"]), p.name))
    if args.names:
        paths = [p for p in paths if p.stem in args.names]
        if {p.stem for p in paths} != set(args.names):
            parser.error("unknown requested instance name")
    rows = []
    for path in paths:
        print(f"starting {path.stem}", flush=True)
        report = run_case(path, args.batsp, args.output_dir, args.timeout)
        tree = report.get("tree", {})
        row = {key: report.get(key) for key in ("name", "n", "status", "metric", "triangle_violations",
                "bottleneck", "published_bottleneck_optimum", "ratio_to_published_optimum", "seconds")}
        row.update(hk_threshold=report.get("hk", {}).get("threshold"),
                   denominator=report.get("hk", {}).get("denominator"), rounds=tree.get("rounds"),
                   stop_reason=tree.get("stop_reason"), beta_bound=tree.get("beta_bound"),
                   hk_seconds=report.get("hk_seconds"), tree_seconds=report.get("tree_seconds"),
                   aks_seconds=report.get("aks_seconds"), error=report.get("error"))
        rows.append(row)
        with args.output_dir.joinpath("summary.csv").open("w", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=list(row))
            writer.writeheader()
            writer.writerows(rows)
        print(f"{path.stem}: {report['status']}, bottleneck={report.get('bottleneck')}, "
              f"ratio={report.get('ratio_to_published_optimum')}, seconds={report['seconds']:.3f}, "
              f"error={report.get('error')}", flush=True)


if __name__ == "__main__":
    main()
