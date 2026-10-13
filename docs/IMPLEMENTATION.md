# C++ implementation notes

The artifact is C++20 and has no external solver dependency.

## Components

### `simplex.hpp`

Two-phase floating-point simplex for

```text
max c^T x
subject to A x <= b, x >= 0.
```

Used only for research-sized Held–Karp LPs with every subtour cut materialized.

### `held_karp.hpp`

Builds the full feasibility LP:

- in-degree = 1;
- out-degree = 1;
- every directed subtour cut >= 1;
- nonnegative variables.

Current explicit-cut implementation is intentionally exponential in `n`, suitable for exact experiments up to roughly low teens.

### `hamiltonian.hpp`

Exact directed Hamiltonian cycle DP, `O(n^2 2^n)`, and exact minimum Hamiltonian graph power `p*`.

### `thin_tree.hpp`

- exact cut thinness evaluation;
- exhaustive supported spanning-tree enumeration on small supports;
- inverse-`z` MST;
- `-log z` MST;
- randomized exponential-clock weighted trees;
- edge-swap local improvement.

### `certified_tree.hpp`

Deterministic exhaustive construction for small rational Held–Karp inputs. It checks degree and subtour constraints with integers, enumerates supported spanning trees, and evaluates every cut with exact rational comparisons. It is capped at 10 vertices and is not the polynomial strong-thin-tree algorithm. The `construct-certified` CLI command sends the selected tree and exact rational ceiling data to AKS.

### `polynomial_baseline.hpp`

The `construct-polynomial-baseline` command validates a rational Held–Karp certificate with exact integral directed min-cut, constructs a supported BFS tree, and sends it to AKS with `beta = min(D,(n-1)/2)`. This is a polynomial-time end-to-end baseline without an instance-independent thinness bound. The directed-flow accumulator uses 128-bit unsigned integers, sufficient for the input's `int` arc count and `uint64_t` numerators; AKS still uses `int` circulation capacities and explicit tour copies, so large instances can exhaust its practical integer or memory limits.

### `aks_rounding.hpp`

Implements An–Kleinberg–Shmoys Lemmas 2–4 once a supported β-thin tree has been supplied:

- split-vertex bounded circulation;
- lower-bound feasible circulation through Dinic max flow;
- integral Eulerian multigraph;
- Hierholzer circuit;
- block/transversal bipartite matching;
- bounded-power Hamiltonian shortcut.

For `construct-certified`, the circulation ceilings and visit bound are computed with integer rational arithmetic rather than floating-point tolerance.

### `metric.hpp`

- directed shortest-path metric;
- threshold graphs;
- exact Bottleneck ATSP optimum for small `n`;
- exact minimum Held–Karp-feasible threshold.

### `witness.hpp`

Hard-coded 6-vertex regression graph and exact rational `z` certificate used for the exact `β*=4/3` thin-tree test.

## Numerical policy

- LP feasibility uses doubles and independent post-validation of degree/cut constraints.
- the fixed 6-vertex thinness certificate uses exact half/integer values represented exactly in binary floating point;
- exact thinness uses exhaustive cuts;
- theorem claims do not depend on the floating-point experimental solver.

For publication-scale exact LP certificates, replace the internal simplex by an exact rational LP backend or export certificates for exact checking.
