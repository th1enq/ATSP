# Constructive strong-thin-tree audit and implementation status

**Update 2026-10-11:** the historical audit below predates the rational convex,
frame and signing components now in `scripts/`. A bounded iterative
experimental tree constructor and a supplied-tree-to-AKS interface are now
available; see `EXPERIMENTAL_PIPELINE_2026-10-11.md`. The general theorem's
deep-lemma audit and universal constant guarantee remain open.

**Date:** 2026-10-08. This continues `THEORY_AUDIT_2026-10-08.md` by reading the proof chain of [A polynomial-time construction of strong thin trees](https://github.com/openai/math/blob/main/preprints/A-polynomial-time-construction-of-strong-thin-trees-September-23-2026/paper.pdf). The checks below distinguish verified interfaces and arithmetic from unverified deep lemmas.

## Dependency chain of Theorem 1.1

| Manuscript component | Role in the algorithm | Audit status |
|---|---|---|
| Theorem 2.1 and Proposition 2.5 | Supply one matrix response to a nested chain of partitions | Statements and the dyadic counting in Proposition 2.5 checked. The geometric transfer/charging proof of Theorem 2.1 was not independently verified. |
| Proposition 3.1, Lemmas 3.2–3.4 | Extract a large packing of low-resistance trees by rational convex feasibility | The partition-separation argument and the stated inner-ball mechanism were reviewed. A standalone exact ellipsoid/SDP/matroid-partition implementation and full proof check remain open. |
| Lemma 4.1 | Build a low-norm rank-preserving normalized incidence frame | Statement and its role in preserving partition rank checked. Its log-determinant and bit-precision proof was not independently verified. |
| Lemma 5.2 and Appendix A | Deterministically sign a stacked frame with rational PSD certificates | The block inequalities and their use in Section 6 were checked. The finite-bit signing descent and its cited dependency were not independently verified. |
| Lemma 6.1 and explicit-graph proof of Theorem 1.1 | Repeatedly halve cut load while retaining a tree packing | The final ratio multiplication was checked: if `r_{i+1} <= r_i/2`, the sum of `r_i^(-1/16)` read backwards is bounded independently of `r_initial`. The step depends on the unverified components above. |
| Section 6 binary-multiplicity reduction | Compress a binary-encoded `k`-connected multigraph to fewer than `n^4` explicit copies | The cut inequalities and projection arithmetic were independently checked in `THEORY_AUDIT_2026-10-08.md`. |

The manuscript invokes absolute cutoffs (`h0`, `r0`, `R0`) and constants (`A`, `Cs`, `C1`) in these steps. The audit has not extracted concrete values or a final numeric `C`. A faithful C++ implementation of the claimed deterministic polynomial algorithm would additionally require exact convex separation, graphic matroid partition, normalized-frame computation, rational PSD certificates, and the Appendix A matrix-signing routine. These are absent from this repository. Merely implementing Section 6 compression or substituting a heuristic tree would not implement Theorem 1.1.

Later audit update: `EXPLICIT_THRESHOLD_AUDIT.md` derives very large **conditional** numerical choices for these constants from the manuscript's stated inequalities. This does not independently verify the deep lemmas or supply the missing LP, frame, and signing implementations. Graphic matroid partition and rational PSD testing have since been added as separate components; the full constructive algorithm remains absent.

Section 5 does give one usable number: `Cs = 2^20` in the signing error bound (the PDF text extraction renders this as `220`). Section 2 still chooses `h0` by several “sufficiently large” conditions, Proposition 3.1 states existential absolute `A,r0`, and Section 6 enlarges `C1,R0` without numeric values. Hence `Cs` alone does not determine an executable cutoff or a final approximation constant. The separate exact Section 6 compression is implemented in `scripts/certify_compress.py` and checked by min-cut; it does not call those constants.

## New executable reference path

`include/certified_tree.hpp` and the `construct-certified` command provide a **deterministic exhaustive reference constructor**, integrated with AKS. It is intentionally separate from the polynomial construction above.

Input is a rational Held–Karp vector with one common denominator:

```text
n D m
u v numerator
... m arc records ...
```

The constructor validates every in/out degree equality and every directed subtour cut using integers. It builds the positive undirected support, enumerates all supported spanning trees, and compares their thinness ratios by exact integer cross-products. The returned tree is optimal for that particular `z` when the search completes. The AKS integration computes all circulation ceilings and `k=ceil(4 beta)` from the exact rational certificate. This avoids presenting a floating-point rounded capacity as a proof certificate.

Example:

```bash
./build/batsp construct-certified instances/regression/witness6_hk.txt
```

Expected result: 128 supported trees checked, exact optimal thinness `4/3`, AKS feasible, and bottleneck 2 on the directed shortest-path metric. The input file includes zero-valued graph arcs so the threshold support is reproduced exactly.

Limits: `2 <= n <= 10`, `1 <= D <= 10^9`, and a configurable DFS node cap. This backend is exponential and reports an incomplete search when capped. It is a rigorous small-instance bridge and regression oracle, **not** the polynomial strong-thin-tree algorithm in the manuscript. The existing floating-point Held–Karp simplex is also not an exact LP backend; the new command requires an explicitly supplied rational certificate.

## Conclusion

The theorem-level AKS composition remains conditional on the published strong-thin-tree construction. The new executable now connects *certified rational small-instance tree construction* to AKS, while the full deterministic polynomial construction remains unimplemented and its deepest source lemmas remain independently unaudited. No runtime or approximation guarantee for the manuscript algorithm is claimed by this code.
