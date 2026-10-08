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

### `aks_rounding.hpp`

Implements An–Kleinberg–Shmoys Lemmas 2–4 once a supported β-thin tree has been supplied:

- split-vertex bounded circulation;
- lower-bound feasible circulation through Dinic max flow;
- integral Eulerian multigraph;
- Hierholzer circuit;
- block/transversal bipartite matching;
- bounded-power Hamiltonian shortcut.

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
