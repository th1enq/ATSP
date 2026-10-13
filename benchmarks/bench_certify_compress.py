#!/usr/bin/env python3
"""Reproducible exact-compression timing on directed Hamiltonian cycles."""

import csv
import platform
import sys
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from certify_compress import certify_and_compress


def main() -> None:
    writer = csv.writer(sys.stdout)
    writer.writerow(("n", "denominator_bits", "arc_count", "seconds", "peak_python_bytes",
                     "compressed_copies", "compressed_min_cut", "python_version"))
    for n in (6, 12, 24, 48):
        for bits in (1, 4096):
            denominator = 1 << (bits - 1)
            arcs = [(u, (u + 1) % n, denominator) for u in range(n)]
            tracemalloc.start()
            start = time.perf_counter()
            result = certify_and_compress(n, denominator, arcs)
            elapsed = time.perf_counter() - start
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            writer.writerow((n, bits, len(arcs), f"{elapsed:.6f}", peak,
                             result["explicit_copy_count"],
                             result["compressed_min_cut"], platform.python_version()))


if __name__ == "__main__":
    main()
