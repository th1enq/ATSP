#!/usr/bin/env python3
"""Run the certificate-only pipeline without exact cuts or optimal references."""

import argparse
import collections
import csv
import json
import random
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from experimental_tree import construct, run_aks


def cases(sizes, seed, cycles):
    rng = random.Random(seed)
    for n in sizes:
        masses = collections.Counter()
        for _ in range(cycles):
            order = list(range(n))
            rng.shuffle(order)
            for i, u in enumerate(order):
                masses[u, order[(i+1) % n]] += 1
        yield f"mixture{n}", n, cycles, [(u, v, q) for (u, v), q in sorted(masses.items())]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batsp", required=True, type=Path)
    parser.add_argument("--sizes", type=int, nargs="+", default=[20, 32])
    parser.add_argument("--cycles", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20261012)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results/scalable_tree")
    parser.add_argument("--reuse", action="store_true")
    args = parser.parse_args()
    if args.cycles < 1 or any(n < 2 for n in args.sizes):
        parser.error("positive cycle count and sizes >=2 are required")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, n, denominator, arcs in cases(args.sizes, args.seed, args.cycles):
        started = time.perf_counter()
        path = args.output_dir / f"{name}.json"
        print(f"starting {name}: n={n}, original copies={n*denominator}, exact references disabled", flush=True)
        if args.reuse and path.exists():
            report = json.loads(path.read_text())
            if (report["n"] != n or report["denominator"] != denominator or
                    [tuple(a) for a in report["arcs"]] != arcs or report["trace"].get("exact_measurements", True)):
                raise ValueError("saved certificate does not match spectral experiment")
        else:
            report = construct(n, denominator, arcs)
        # run_aks verifies the spectral trace before calling the polynomial
        # C++ supported-tree verifier. No all-cut oracle or optimum is called.
        report["aks_output"] = run_aks(report, args.batsp)
        report["experiment"] = {"seed": args.seed, "cycles": args.cycles,
                                "exact_references": False, "metric_optimum": None}
        path.write_text(json.dumps(report, indent=2)+"\n")
        metrics = dict(re.findall(r"(\w+)=([^\s]+)", report["aks_output"].splitlines()[0]))
        trace = report["trace"]
        row = {"name": name, "n": n, "denominator": denominator,
               "input_graph_kind": report["input_graph_kind"],
               "input_copies": report["input_graph_copy_count"],
               "section6_copies": report["compression"]["explicit_copy_count"],
               "rounds": len(trace["rounds"]), "final_edges": len(trace["final_edges"]),
               "final_r": trace["final_r"], "stop_reason": trace["stop_reason"],
               "beta_bound_for_aks": report["beta_bound_for_aks"],
               "beta_from_spectral_chain": report["beta_from_spectral_chain"],
               "aks_feasible": metrics["aks_feasible"],
               "aks_max_visits": metrics["aks_max_visits"],
               "metric_bottleneck": metrics["metric_bottleneck"],
               "construction_seconds": trace["seconds"], "seconds": time.perf_counter()-started}
        rows.append(row)
        with (args.output_dir / "summary.csv").open("w", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=list(row))
            writer.writeheader()
            writer.writerows(rows)
        print(f"{name}: rounds={row['rounds']}, edges={row['input_copies']}->{row['final_edges']}, "
              f"beta_bound={row['beta_bound_for_aks']}, bottleneck={row['metric_bottleneck']}, "
              f"seconds={row['seconds']:.3f}", flush=True)


if __name__ == "__main__":
    main()
