#!/usr/bin/env python3
"""Reproducible small-instance HK -> sparsification -> tree -> AKS campaign."""

import argparse
import csv
import json
import random
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from certify_compress import read_hk
from experimental_tree import construct, run_aks, verify_report


def cases(seed):
    n, denominator, arcs = read_hk(ROOT / "instances/regression/witness6_hk.txt")
    yield "witness6", n, denominator, arcs
    # Forced vertex split preserves HK feasibility and non-Hamiltonicity.
    split = [(6 if u == 0 else u, v, q) for u, v, q in arcs]
    split.append((0, 6, denominator))
    yield "split7", 7, denominator, split
    for n in range(3, 7):
        yield f"cycle{n}", n, 1, [(u, (u+1) % n, 1) for u in range(n)]
        yield f"complete{n}", n, n-1, [(u, v, 1) for u in range(n) for v in range(n) if u != v]
    rng = random.Random(seed)
    for n in range(4, 7):
        for rep in range(2):
            masses = {}
            denominator = 0
            for _ in range(4):
                order = list(range(n))
                rng.shuffle(order)
                weight = rng.randrange(1, 6)
                denominator += weight
                for i, u in enumerate(order):
                    edge = (u, order[(i+1) % n])
                    masses[edge] = masses.get(edge, 0)+weight
            yield f"mixture{n}_{rep}", n, denominator, [(u, v, q) for (u, v), q in sorted(masses.items())]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batsp", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results/experimental_tree")
    parser.add_argument("--seed", type=int, default=20261011)
    parser.add_argument("--reuse", action="store_true", help="verify and reuse matching saved tree certificates")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, n, denominator, arcs in cases(args.seed):
        start = time.perf_counter()
        saved = args.output_dir / f"{name}.json"
        if args.reuse and saved.exists():
            report = json.loads(saved.read_text())
            if (report["n"] != n or report["denominator"] != denominator or
                    [tuple(arc) for arc in report["arcs"]] != arcs):
                raise ValueError(f"saved experiment input mismatch: {name}")
        else:
            report = construct(n, denominator, arcs, exact_measurements=True)
        verify_report(report)
        report["aks_output"] = run_aks(report, args.batsp)
        report["baseline_output"] = run_aks(report, args.batsp, "construct-polynomial-baseline")
        report["reference_output"] = run_aks(report, args.batsp, "construct-certified")
        report["experiment"] = {"name": name, "seed": args.seed}
        (args.output_dir / f"{name}.json").write_text(json.dumps(report, indent=2)+"\n")
        metrics = dict(re.findall(r"(\w+)=([^\s]+)", report["aks_output"].splitlines()[0]))
        baseline_beta = re.search(r"beta_exact=([^\s]+)", report["baseline_output"]).group(1)
        reference_beta = re.search(r"beta_exact=([^\s]+)", report["reference_output"]).group(1)
        trace = report["trace"]
        row = {"name": name, "n": n, "denominator": denominator,
               "compressed_edges": report["compression"]["explicit_copy_count"],
               "rounds": len(trace["rounds"]), "final_edges": len(trace["final_edges"]),
               "final_r": trace["final_r"], "stop_reason": trace["stop_reason"],
               "beta_exact": report["beta_exact"],
               "beta_baseline_bound": baseline_beta, "beta_reference_optimal": reference_beta,
               "beta_from_spectral_chain": report["beta_from_spectral_chain"],
               "beta_from_exact_cut_chain": report["beta_from_exact_cut_chain"],
               "aks_feasible": metrics["aks_feasible"],
               "aks_power_bound": metrics["aks_power_bound"],
               "metric_bottleneck": metrics["metric_bottleneck"],
               "metric_optimum": metrics["metric_optimum"],
               "construction_seconds": trace["seconds"],
               "seconds": time.perf_counter()-start}
        rows.append(row)
        # Flush completed cases to disk so an interrupted campaign is usable.
        with (args.output_dir / "summary.csv").open("w", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=list(row))
            writer.writeheader()
            writer.writerows(rows)
        print(f"{name}: rounds={row['rounds']} edges={row['compressed_edges']}->{row['final_edges']} "
              f"beta={row['beta_exact']} bottleneck={row['metric_bottleneck']} "
              f"opt={row['metric_optimum']} seconds={row['seconds']:.3f}", flush=True)


if __name__ == "__main__":
    main()
