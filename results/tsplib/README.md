# Real TSPLIB benchmark artifacts (2026-10-11)

- `summary.csv`: one row per input, including failures and the full pipeline's elapsed time.
- `<name>.json`: original-cost tour evaluation, exact Held–Karp threshold,
  exact infeasibility proof at the preceding distinct cost, and individual timings.
- `<name>.hk.txt`: rational Held–Karp solution supplied to the existing constructor.
- `<name>.tree.json`: the existing constructor's certificate, for completed tree constructions.
- `environment.json`: software versions, limits, executable and constructor hashes.

The reported `bottleneck` is **the maximum original matrix cost**, including
the closing tour edge. The C++ `aks_output` field also contains
`metric_bottleneck`, which is an unweighted hop count in the HK support graph;
that field is not the TSPLIB objective value.

An `ok` row means the current constructor and AKS completed and the tour is
Hamiltonian. A `timeout` row claims no tour. A completed tree can have zero
sparsification rounds because its packing parameter is already at the
existing cutoff. These outcomes do not imply a full implementation of the
general constant-thin-tree theorem.

Input provenance is in `../../instances/tsplib/manifest.json`. Published
bottleneck optima are external references; no exact Hamiltonian DP, exhaustive
tree search, or enumeration of all cuts was used in this campaign.

Verify saved weighted tours and exact HK lower bounds using standard Python
without SciPy or an LP solve:

```bash
python3 benchmarks/bench_tsplib.py --verify-results
```

Full tree-certificate replay remains available through the existing tool:

```bash
python3 scripts/experimental_tree.py --verify results/tsplib/br17.tree.json
```
