# Bottleneck ATSP via Strong Thin Trees — C++ research artifact

This repository is a correctness-first experimental artifact for the bridge

\[
\text{Held–Karp feasibility} \Rightarrow \text{constant supported thin tree}
\Rightarrow \text{constant Hamiltonian power / Bottleneck-ATSP approximation}.
\]

The theoretical bridge uses OpenAI Math Result 174 together with An–Kleinberg–Shmoys (TALG 2021). See `docs/PROOF.md`, `docs/THEORY_AUDIT_2026-10-08.md`, and `docs/MASTER_HANDOFF.md`. The audit validates the reduction conditional on the source theorems; it does not certify their full proofs or a numerical approximation constant.

The follow-up constructive audit is in `docs/CONSTRUCTIVE_AUDIT_2026-10-08.md`. The `construct-certified` command exhaustively constructs an optimal supported tree from a small rational Held–Karp certificate and passes it to AKS. This reference backend is exponential and is not the new polynomial strong-thin-tree construction.

The staged verification and implementation plan for the polynomial construction is in `docs/POLYNOMIAL_CONSTRUCTION_PLAN.md`.

The exact preprocessing stage of that plan is now available in Python 3 (standard library only):

```bash
python3 scripts/certify_compress.py instances/regression/witness6_hk.txt
python3 scripts/certify_compress.py --kind binary path/to/multigraph.txt --output compressed.json
```

The first form checks rational Held–Karp degrees and all directed subtour cuts by exact min-cut. The second expects `n k pair_count` followed by `u v multiplicity` for each unordered pair and verifies that the original graph is `k`-edge-connected. Both return compact multiplicities from Section 6 of the [constructive manuscript](https://github.com/openai/math/blob/main/preprints/A-polynomial-time-construction-of-strong-thin-trees-September-23-2026/paper.pdf), the actual compressed min-cut, and the copy-count bound. Input multiplicities may have arbitrary bit length. This stage **does not construct a thin tree**. See `docs/THESIS_EXPERIMENTAL_AUDIT.md` for the measured scope.

The next polynomial subroutine now constructs and certifies edge-disjoint spanning-tree packings on the compressed graph:

```bash
python3 scripts/certify_compress.py instances/regression/witness6_hk.txt --output /tmp/witness6_compressed.json
python3 scripts/tree_packing.py /tmp/witness6_compressed.json --trees 18 --output /tmp/witness6_packing.json
python3 scripts/tree_packing.py /tmp/witness6_compressed.json --verify /tmp/witness6_packing.json
```

The packing output is a list of tree edge IDs or a violated vertex partition. It does not select a strong thin tree. Matrix sparsification remains open; see `docs/PACKING_AND_CONSTANTS_AUDIT.md`.

Exact weighted partition separation is in `scripts/weighted_partition_oracle.py`; it uses the Baiou–Barahona–Mahjoub min-cut algorithm and works with arbitrary rational capacities. `scripts/continuation_oracle.py` returns exact separating hyperplanes for a Proposition 3.1 step. `scripts/rational_ellipsoid.py` implements dyadic rounded central cuts, and `scripts/continuation_solver.py` uses them to find rational responses, run the exact schedule, and pack terminal low-resistance trees. The source paper's inner-ball guarantee applies only under its large-r hypotheses; the tests exercise small steps and do not validate a full large-r execution.

`scripts/rational_frame.py` finds positive rational weights with an exact leverage certificate and approximates the corresponding whitened columns. `scripts/signing_padding.py` forms rational approximations of the stacked shortcut/frame columns and completes them to an exact identity decomposition. `scripts/deterministic_signing.py` offers the fast Frobenius signer and an Appendix A backend. The latter uses `appendix_a_potential.py`, `appendix_a_value_oracle.py`, and `appendix_a_signing.py` for rational normalization, SDP value intervals, finite differences, endpoint tests, and negative-curvature moves; it checks the final spectral bound exactly. `scripts/verified_sparsification.py` can use it via `signing_method="appendix_a"`. The explicit proof constants make this path impractical beyond tiny instances, and the full large-parameter AKS run is still unverified. See `docs/DETERMINISTIC_SIGNING_AUDIT.md`.

`scripts/exact_psd.py` also contains the exact real rational rank-one PSD decomposition used by Lemma 5.1. This prepares rational padding for either signing backend.

The executable now also has a deterministic polynomial **baseline** from a rational HK certificate to an AKS tour:

```bash
./build/batsp construct-polynomial-baseline instances/regression/witness6_hk.txt
```

It validates degrees and directed subtour cuts using integer min-cut, builds a supported BFS tree, and passes the exact bound `beta = min(D, (n-1)/2)` to AKS, where `D` is the input denominator. The bound follows because every symmetrized HK cut has mass at least 2, and every selected tree edge has positive integer multiplicity in `D*z`. Runtime is polynomial in the explicit input size, but this beta can grow with `n` or `D`. It is not the constant-thin-tree algorithm of Result 174.

An explicit but very large *conditional* full-chain cutoff and thinness constant are derived in `docs/EXPLICIT_THRESHOLD_AUDIT.md`. They assume the source lemmas and are not an implemented approximation guarantee.

## Iterative experimental constructor (2026-10-11)

The new `scripts/experimental_tree.py` connects exact HK compression, tree
packing, several certified sparsification rounds, final tree projection, and
the C++ AKS rounder. Each round checks a terminal shortcut `X=c L_H` for
`c=1,2,3`, builds a positive normalized frame, signs its stacked columns,
checks the retained graph by exact PSD and packing certificates, and measures
the all-cut load. Bounded coordinate balancing and two deterministic edge
orders are practical experimental choices. The general continuation and
Appendix A proof guarantees are not assumed by this driver.

The default CLI now runs with spectral certificates and supported-tree
bounds, without exhaustive cuts, spanning-tree references, or optimal-tour
DP. `--exact-small` explicitly enables all-cut measurements for `n<=16`.
When reduced original multiplicities need fewer copies than Section 6
compression, the default uses those copies and their certified packing.

```bash
python3 scripts/experimental_tree.py instances/regression/witness6_hk.txt \
  --batsp ./build/batsp --output /tmp/witness6_tree.json
python3 scripts/experimental_tree.py --verify /tmp/witness6_tree.json
python3 benchmarks/bench_experimental_tree.py --batsp ./build/batsp
python3 benchmarks/bench_scalable_tree.py --batsp ./build/batsp --sizes 20 32
```

The certificate verifier rechecks compression, the matrix inequalities,
supplied disjoint trees, all cut ratios, and the projected tree. It does not
rerun signing, frame search, or matroid-union construction. The C++ command
`round-supplied-tree HK_FILE TREE_FILE` independently checks the supplied
tree's support, connectivity, and claimed thinness before rounding it.

The saved campaign contains 16 cases and 40 certified rounds. All 16 reach
the experimental packing cutoff and produce an AKS tour; 14 tours attain
the exact instance optimum. The largest observed tour ratio is 2. These
are sample measurements, not universal approximation bounds.

The optional all-cut verifiers are restricted to `2<=n<=16`. The default
certificate path has no such vertex cutoff. `round-supported-tree` in C++
checks HK, tree support and the bound `min(D,(n-1)/2)` by polynomial routines;
it does not compute an optimal tour. See `docs/SCALABLE_PIPELINE_2026-10-11.md`.
If a bounded experimental
step fails, the report records its reason and returns a tree from the last
certified packing. Such a run still supplies a valid instance certificate;
it does not establish a universal constant-thin-tree guarantee. See
`docs/EXPERIMENTAL_PIPELINE_2026-10-11.md` and
`results/experimental_tree/summary.csv` for the measured results.

## TSPLIB matrices (2026-10-11)

The current constructor and AKS can be benchmarked on ten inputs from the
official TSPLIB ATSP catalog, using the stored plaintext mirrors in
`instances/tsplib/`. The adapter finds the minimum feasible weighted HK
threshold using HiGHS and integral min-cut separation. Feasible HK inputs
and infeasible predecessor thresholds are checked with exact rational
certificates. The constructor and rounder are unchanged.

```bash
python3 -m pip install -r benchmarks/requirements-tsplib.txt
g++ -std=c++20 -O2 -Iinclude src/main.cpp -o /tmp/kltn-batsp
python3 benchmarks/bench_tsplib.py --batsp /tmp/kltn-batsp --timeout 180
python3 benchmarks/bench_tsplib.py --verify-results
```

For this workspace's cached wheels on NixOS, the run command is
`bash benchmarks/run_tsplib_cached.sh --batsp /tmp/kltn-batsp --timeout 180`.
Verification of saved costs and lower bounds needs only standard Python.
Raw results, including timeouts, are in `results/tsplib/summary.csv`; the
report is `docs/TSPLIB_BENCHMARK_2026-10-11.md`. The reported objective uses
original weighted costs and published **bottleneck** optima, with no
metric closure. Three inputs violate the triangle inequality and are
annotated accordingly. This subset is not the full TSPLIB catalog, and it
does not validate the general Result 174 construction.

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

The full September-2026 OpenAI deterministic strong-thin-tree construction is **not reimplemented here**. Its mathematical theorem is used in `docs/PROOF.md`; the executable provides a polynomial baseline, an exhaustive reference oracle, and heuristic thin-tree oracles. The AKS circulation/shortcut pipeline **is implemented**. The polynomial baseline has a nonconstant thinness bound; do not claim the repository is an implementation of Result 174 itself.

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
./build/batsp construct-certified instances/regression/witness6_hk.txt
./build/batsp construct-polynomial-baseline instances/regression/witness6_hk.txt
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

### Backend một bước sparsification theo nguồn

Luồng mới và bộ replay chính xác: [GENERAL_SPARSIFICATION_2026-10-11.md](docs/GENERAL_SPARSIFICATION_2026-10-11.md).
`python3 scripts/general_sparsification.py --help` cung cấp lệnh `step` và `verify`.
Luồng đã nối continuation, gradient frame và Appendix A; hiện chưa hoàn thành một vòng từ trạng thái khởi đầu trên dữ liệu thực tế. Các lần dừng/quá thời gian được lưu riêng, không tính là bước thành công.

Đo chi phí Appendix A và sửa giới hạn SDP: [APPENDIX_A_PROFILE_2026-10-11.md](docs/APPENDIX_A_PROFILE_2026-10-11.md).

Chứng nhận đối ngẫu SDP và kết quả một bước Appendix A trên terminal witness nhỏ: [SDP_DUAL_AUDIT_2026-10-11.md](docs/SDP_DUAL_AUDIT_2026-10-11.md).

Một bước trên mẫu nhiều hướng trực giao: [MULTI_DIRECTION_SDP_2026-10-11.md](docs/MULTI_DIRECTION_SDP_2026-10-11.md) (mốc lịch sử).

Cập nhật SDP không giao hoán, continuation từ đầu với tham số thực nghiệm và bộ dựng cây có replay: [GENERAL_COMPLETION_2026-10-11.md](docs/GENERAL_COMPLETION_2026-10-11.md). Có chứng nhận trên mẫu nhỏ; chưa xác lập triển khai hiệu quả có bảo đảm phổ quát của paper hoặc kết quả TSPLIB mới.
