# Bottleneck ATSP via Strong Thin Trees — C++ research artifact

This repository is a correctness-first experimental artifact for the bridge

\[
\text{Held–Karp feasibility} \Rightarrow \text{constant supported thin tree}
\Rightarrow \text{constant Hamiltonian power / Bottleneck-ATSP approximation}.
\]

The theoretical bridge uses OpenAI Math Result 174 together with An–Kleinberg–Shmoys (TALG 2021). See `docs/PROOF.md` and `docs/MASTER_HANDOFF.md`.

## Implemented in C++20

- internal two-phase simplex LP solver;
- Held–Karp feasibility with explicit subtour cuts (small/medium `n`);
- exact directed Hamiltonian-cycle bitmask DP;
- exact graph-power threshold `p*`;
- exact supported-tree thinness by cut enumeration;
- exact spanning-tree enumeration for small supports;
- inverse-z MST, randomized weighted-tree sampling, and edge-swap local search;
- shortest-path asymmetric metric closure;
- exact Bottleneck-ATSP optimum and exact HK threshold for small instances;
- An–Kleinberg–Shmoys downstream rounding from any supplied supported thin tree: bounded integral circulation, Euler tour, Hall-transversal shortcutting;
- exhaustive `n=4` and `n=5` benchmark campaigns;
- 6-vertex HK-feasible/non-Hamiltonian regression witness;
- random directed graph search.

## Important limitation

The full September-2026 OpenAI deterministic strong-thin-tree construction is **not reimplemented here**. Its mathematical theorem is used in `docs/PROOF.md`; the executable provides exact and heuristic thin-tree oracles for experiments. The AKS circulation/shortcut pipeline **is implemented**. What is not reimplemented is the new OpenAI strong-thin-tree construction itself; experiments supply exact or heuristic supported thin trees to the AKS pipeline. Do not claim the repository is an implementation of Result 174 itself.

This distinction is deliberate: the public catalog states the constructive theorem, but faithfully reproducing that new manuscript is a separate large engineering task and must not be replaced by a heuristic while retaining the same label.

## Build

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
ctest --test-dir build --output-on-failure
```

## Regression experiments

```bash
./build/batsp witness6
./build/batsp exhaustive-n4 results/exhaustive_n4.csv
./build/batsp random-search 9 100 0.18 0.55 20261007 results/random.csv
```

Expected `n=4` totals:

- total digraphs: 4096
- Held–Karp feasible: 1194
- HK-feasible non-Hamiltonian: 0

Expected witness:

- HK feasible: true
- Hamiltonian: false
- `p*=2`
- support spanning trees: 128
- exact optimal supported thinness: `4/3`
- shortest-path metric HK threshold: 1
- exact bottleneck optimum: 2

## Scope

This artifact targets exact verification and small-instance benchmarking. The explicit-cut LP has exponentially many constraints and is not intended as a production large-n Held–Karp solver.

## Reproduced headline results

The packaged CSVs/logs reproduce:

- all `4096` labeled `n=4` digraphs: `1194` Held–Karp feasible, zero HK-feasible non-Hamiltonian;
- all `1,048,576` labeled `n=5` digraphs: `240` HK-feasible non-Hamiltonian, all with `p*=2`;
- on those 240 hard `n=5` instances, the LP solution returned by the internal simplex has exact optimal supported thinness `beta*=1`;
- a 16,000-random-digraph campaign produced `6906` HK-feasible graphs and `8` non-Hamiltonian hard instances, all with `p*=2`;
- a structured hard family for `n=6..12` remains HK feasible, non-Hamiltonian, and has `p*=2`;
- 200 random asymmetric metrics: downstream AKS pipeline succeeded on all, median final ratio `1.0`, maximum observed `1.74194`.

See `docs/BENCHMARK_RESULTS.md`.
