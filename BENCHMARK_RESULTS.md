# Benchmark results — C++ artifact

**TSPLIB update 2026-10-11:** the unchanged current constructor + AKS is run
on original weighted matrices from ten official ATSP benchmark instances.
See `docs/TSPLIB_BENCHMARK_2026-10-11.md` and `results/tsplib/summary.csv` for
weighted bottleneck costs, published bottleneck optima, exact HK lower
bounds, metric checks, and timeouts. No exhaustive reference is used.

**Update 2026-10-11:** the iterative certificate-driven construction campaign
is documented in `docs/EXPERIMENTAL_PIPELINE_2026-10-11.md`, with raw JSON
certificates and comparisons in `results/experimental_tree/`. It is a new
16-instance campaign, separate from the historical results below.

**Run date:** 2026-10-07  
**Master seed:** `20261007`

Environment used in this artifact build:

```text
CPU: AMD EPYC 9V74 (container exposes 5 cores)
RAM: 5.8 GiB
OS: Debian GNU/Linux 13 (trixie)
Compiler: g++ 14.2.0
Build: C++20, Release / -O3
```

These are research-environment timings, not hardware-normalized publication benchmarks.

---

## 1. Regression witness (`n=6`)

Command:

```bash
./build/batsp witness6
```

Observed:

```text
n=6
arcs=14
Held–Karp feasible = yes
Hamiltonian G = no
minimum Hamiltonian power p* = 2
support edges of exact z = 10
supported spanning trees enumerated = 128
exact optimal supported thinness beta* = 4/3
inverse-z MST beta = 3/2
random/local-search beta = 4/3
AKS downstream circulation feasible = yes
AKS k bound = 6
actual max circuit visits = 2
AKS graph-power bound = 11
algorithmic bottleneck on shortest-path metric = 2
minimum HK threshold = 1
exact Bottleneck ATSP optimum = 2
actual produced ratio = 1.0
```

The theorem guarantee `G^11` coming from the experimentally supplied `β=4/3` tree is deliberately much looser than the exact instance fact `p*=2`. This is useful for studying the gap between worst-case analysis and actual shortcut lengths.

---

## 2. Exhaustive all labeled digraphs on 4 vertices

Command:

```bash
./build/batsp exhaustive-n4 results/exhaustive_n4.csv
```

Observed:

| statistic | value |
|---|---:|
| all loopless labeled digraphs | 4,096 |
| pass fast necessary filter | 1,606 |
| Held–Karp feasible | **1,194** |
| HK-feasible Hamiltonian | **1,194** |
| HK-feasible non-Hamiltonian | **0** |
| wall time | ~0.01 s |

This exactly reproduces the earlier research-log value `1194`.

---

## 3. Exhaustive all labeled digraphs on 5 vertices

This experiment was added during the C++ implementation and is stronger than the earlier random search.

Command:

```bash
./build/batsp exhaustive-n5 results/exhaustive_n5_detailed.csv
```

The code enumerates all

\[
2^{5\cdot4}=1,048,576
\]

loopless labeled digraphs. Hamiltonian graphs are automatically Held–Karp feasible, so the LP is required only for non-Hamiltonian graphs that pass the structural necessary filter.

Observed:

| statistic | value |
|---|---:|
| total digraphs | **1,048,576** |
| Hamiltonian | **422,850** |
| non-Hamiltonian candidates sent to HK LP | **142,230** |
| HK-feasible non-Hamiltonian | **240** |
| total HK-feasible | **423,090** |
| wall time | ~3.1 s |

### All 240 hard graphs

For **every one** of the 240 HK-feasible non-Hamiltonian labeled graphs:

\[
\boxed{p^*=2.}
\]

For the feasible LP solution returned by the internal simplex solver, every instance also had:

\[
\boxed{\beta^*=1.}
\]

under exact supported-spanning-tree enumeration.

Additional uniform facts in this run:

```text
undirected z-support size = 7        for all 240
supported spanning trees = 24       for all 240
inverse-z MST achieved beta*=1      for all 240
random/local thin-tree search beta=1 for all 240
```

Arc-count distribution among the 240 hard labeled digraphs:

| directed arcs | count |
|---:|---:|
| 10 | 60 |
| 11 | 120 |
| 12 | 60 |

### Interpretation

This is **computational evidence**, not a proof that every HK-feasible digraph has a Hamiltonian square. It does establish exhaustively that the stronger statement is true for every labeled digraph with at most 5 vertices.

---

## 4. Random directed-graph search: 16,000 instances

Command:

```bash
./build/batsp random-search 12 2000 0.18 0.55 20261007 \
  results/random_n5_12_2000_repro.csv
```

Grid:

```text
n = 5,6,7,8,9,10,11,12
2000 instances per n
edge probability sampled uniformly from [0.18,0.55]
```

Observed:

| statistic | value |
|---|---:|
| generated | **16,000** |
| Held–Karp feasible | **6,906** |
| HK-feasible non-Hamiltonian | **8** |
| hard instances with p*=2 | **8 / 8** |
| hard instances with p*>=3 | **0** |
| wall time | ~20 s |

The eight hard samples occurred at sizes `8,9,10,10,11,11,12,12`.

Thin-tree heuristic values on these eight were:

```text
random/local beta:
1.20, 1.25, 1.20, 1.3333, 1.3333, 1.40, 1.40, 1.40

inverse-z MST beta:
1.20, 1.50, 1.20, 1.50, 1.4286, 1.50, 1.50, 2.00
```

The CSV stores a deterministic full adjacency signature for every generated graph, making all samples reconstructible from the result file.

---

## 5. Structured HK-feasible non-Hamiltonian split family

Starting from the 6-vertex witness, repeatedly apply the forced vertex-split transformation proved in `PROOF.md`.

Command:

```bash
./build/batsp split-family 12 results/split_family_pipeline.csv
```

Results:

| n | HK feasible | Hamiltonian G | p* | inverse-z beta | random/local beta | pipeline bottleneck | exact metric optimum |
|---:|:---:|:---:|---:|---:|---:|---:|---:|
| 6 | yes | no | 2 | 1.5 | 1.3333 | 2 | 2 |
| 7 | yes | no | 2 | 1.5 | 1.3333 | 2 | 2 |
| 8 | yes | no | 2 | 1.5 | 1.3333 | 2 | 2 |
| 9 | yes | no | 2 | 1.5 | 1.3333 | 2 | 2 |
| 10 | yes | no | 2 | 1.5 | 1.3333 | 2 | 2 |
| 11 | yes | no | 2 | 1.5 | 1.3333 | 2 | 2 |
| 12 | yes | no | 2 | 1.5 | 1.3333 | 2 | 2 |

Every downstream AKS circulation/shortcut run succeeded and returned an optimal bottleneck-2 tour on the shortest-path metric in these experiments.

This family is not an exhaustive test of large graphs; its value is that non-Hamiltonicity and HK feasibility have a simple structural preservation proof, so it is a reliable hard regression family.

---

## 6. Random asymmetric metrics: end-to-end pipeline

Command:

```bash
./build/batsp metric-random 8 50 20261007 results/metric_random_pipeline.csv
```

Generation:

1. start from independent complete directed integer costs in `[1,100]`;
2. take directed all-pairs shortest-path closure, producing an asymmetric metric;
3. compute exact minimum HK-feasible threshold;
4. compute exact Bottleneck ATSP optimum by threshold + exact Hamiltonian DP;
5. obtain a practical supported tree by random weighted-tree sampling + local swaps;
6. run the C++ AKS bounded-circulation and Hall-transversal shortcut pipeline.

Total instances:

\[
4\text{ sizes}\times50=200.
\]

### Aggregate results

| metric | observed value |
|---|---:|
| AKS downstream pipeline feasible | **200 / 200** |
| median `OPT / tau_HK` | **1.000** |
| maximum `OPT / tau_HK` | **1.03333** |
| instances with LP threshold gap > 1 | **1 / 200** |
| median final `ALG / OPT` | **1.000** |
| maximum final `ALG / OPT` | **1.74194** |
| median random/local beta | **1.000** |
| maximum random/local beta | **1.33333** |
| maximum inverse-z MST beta | **1.50000** |
| maximum actual Eulerian-circuit visits/vertex | **2** |
| maximum analytical shortcut power from measured beta | **11** |

Worst end-to-end ratio in this run:

```text
n = 8
replicate = 29
tau_HK = 30
OPT = 31
LP gap = 31/30 ≈ 1.03333
practical beta = 4/3
AKS k bound = 6
AKS theoretical power bound = 11
produced bottleneck = 54
ALG/OPT = 54/31 ≈ 1.74194
```

The actual circuit never visited a vertex more than twice in this benchmark even when the proof-side bound from measured β was 6.

---

## 7. Thinness versus the 2021 theoretical guarantee

The original paper uses

\[
\beta_{AKS}(n)=\frac{4\ln n}{\ln\ln n}.
\]

For the metric benchmark sizes:

| n | paper theoretical β | max practical random/local β observed |
|---:|---:|---:|
| 5 | 13.5280 | 1.0000 |
| 6 | 12.2892 | 1.3333 |
| 7 | 11.6919 | 1.3333 |
| 8 | 11.3615 | 1.3333 |

These numbers do **not** imply an improved worst-case theorem by themselves. The paper's β is a guarantee, while the experimental values are measured on small instances. Their role is to quantify how conservative the previous worst-case analysis is on the tested samples.

The theoretical constant improvement in `PROOF.md` instead comes from OpenAI Result 174, not from these empirical values.

---

## 8. Current evidence for the stronger `p=2` hypothesis

Current C++ evidence in this artifact:

- all 1,194 HK-feasible labeled digraphs on `n=4` are already Hamiltonian;
- all **240** HK-feasible non-Hamiltonian labeled digraphs on `n=5` have Hamiltonian square;
- all **8** random hard graphs in a 16,000-instance search have Hamiltonian square;
- every graph in the forced-split hard family for `n=6..12` has Hamiltonian square;
- the original 6-vertex witness has `p*=2`.

No `p*>=3` example has been found by this artifact.

This remains a **conjectural experimental direction**. The proved consequence of the strong thin-tree theorem is only that a universal constant

\[
p_0=2\lceil2C\rceil-1
\]

exists.

---

## 9. What is and is not being benchmarked against the original paper

No author-supplied implementation or official benchmark dataset was located in the current source search. The 2021 paper is primarily theoretical.

Therefore comparison is split into:

### Theoretical

Original:

\[
O(\log n/\log\log n)
\]

approximation via

\[
\beta=4\ln n/\ln\ln n.
\]

New bridge, conditional on Result 174:

\[
O(1)
\]

via

\[
\beta=C/2.
\]

### Experimental

The artifact benchmarks:

- exact HK feasibility;
- exact Hamiltonicity and graph power;
- exact/practical thinness;
- the AKS circulation/shortcut framework;
- exact small-instance Bottleneck ATSP.

It does **not** fabricate runtime comparisons against an original-paper executable that was not found.
