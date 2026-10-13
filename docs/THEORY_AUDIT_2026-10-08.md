# Theory audit — Strong thin trees to Bottleneck ATSP

**Audit date:** 2026-10-08  
**Scope:** Check the theorem interfaces, the repository's reduction, its complexity claim, and the stated AKS consequences against the primary manuscripts. This is an independent audit of the *reduction and source matching*, not a line-by-line verification of the two new strong-thin-tree proofs.

The subsequent dependency audit and exact small-instance implementation are documented in [`CONSTRUCTIVE_AUDIT_2026-10-08.md`](CONSTRUCTIVE_AUDIT_2026-10-08.md).

## Verdict

The reduction in `PROOF.md` is mathematically valid **conditional on** the two OpenAI strong-thin-tree Theorem 1.1 statements. The AKS lemmas apply to the tree it produces. No gap was found in the cut calculation, denominator scaling, tree projection, or constant substitution. The source manuscripts' full proofs, and therefore the unconditional truth of their theorems, have **not** been independently certified by this audit. The repository also does not implement the constructive theorem.

The constant-factor guarantee should be stated symbolically. Let `C_exist` and `C_alg` denote constants valid for the existence and algorithmic theorems, and take `C = max(C_exist, C_alg)`. Then the asserted universal graph-power and approximation bound is

\[
p_0=2\lceil 2C\rceil-1.
\]

The manuscripts state existence of an absolute constant; this audit did not extract a usable numerical value. This expression does not certify a specific numeric ratio such as 2, 11, or 1.74194.

## Source statements checked

| Dependency | Direct source location | Audit result |
|---|---|
| Strong thin tree exists for every finite loopless undirected `k`-edge-connected multigraph with at least two vertices, with all-cut bound `C_exist/k` | [Existence manuscript, Theorem 1.1, p. 1](https://github.com/openai/math/blob/main/preprints/The-strong-thin-tree-conjecture-September-23-2026/paper.pdf) | Statement matches the reduction's hypothesis. Its internal proof was not fully verified. |
| Deterministic construction in time polynomial in binary input length, including binary-encoded parallel multiplicities | [Construction manuscript, Theorem 1.1, p. 2](https://github.com/openai/math/blob/main/preprints/A-polynomial-time-construction-of-strong-thin-trees-September-23-2026/paper.pdf) | Statement matches the required input representation. Section 6 explicitly describes a reduction from binary multiplicities to a polynomial-size explicit graph. The many intermediate geometric/algorithmic lemmas were not fully verified. |
| Supported tree means every selected unordered pair lies in the positive support of `z`; Lemma 4 accepts **any feasible** Held–Karp vector and gives at most `ceil(4 beta)` visits | [AKS, Definitions 1–2 and Lemma 4, pp. 4, 6–7](https://arxiv.org/pdf/2012.14233) | Matches the repository. Extremality is needed by AKS's tree-sampling Theorem 1, not by Lemma 4. |
| A circuit with at most `k` visits per vertex gives a Hamiltonian cycle in `G^(2k-1)` | [AKS, Lemma 3, pp. 5–6](https://arxiv.org/pdf/2012.14233) | Matches the power calculation. |
| Threshold Held–Karp plus a supported thin-tree routine yields a Bottleneck ATSP approximation | [AKS, Theorems 2–3, pp. 7–8](https://arxiv.org/pdf/2012.14233) | Matches the composition, under an asymmetric metric cost. |

## Independent check of the bridge

Assume `n >= 2`, a loopless digraph, and a feasible rational Held–Karp vector `x`. For each unordered pair `e={u,v}` let `z_e=x_uv+x_vu`, treating absent arcs as zero. For every nonempty proper `S`,

\[
z(\delta(S))=x(\delta^+(S))+x(\delta^+(V\setminus S))\ge 2.
\]

Choose a positive common denominator `D` for all `z_e` and give pair `e` the integer multiplicity `m_e=D z_e`. The resulting multigraph has every cut of size at least `2D` and is loopless; hence it satisfies the existence theorem with `k=2D`. Its tree satisfies

\[
|T_H\cap\delta_H(S)|\le \frac{C}{2D}\,D z(\delta(S))=(C/2)z(\delta(S)).
\]

A multigraph tree cannot contain two parallel copies of a pair, since they form a 2-cycle. Projecting copies to unordered pairs therefore preserves acyclicity, connectivity, and every tree cut count. Every selected pair has `m_e>0`, so the projected tree is supported. Thus it is a supported `C/2`-thin tree in precisely the sense required by AKS.

**Result:** The bridge is valid under the stated theorem. In particular, it applies to any feasible rational `x`; no extreme-point premise is needed for this step.

## Bit complexity and algorithmic scope

The Held–Karp system has rational coefficients. Feasibility implies the existence of a rational basic feasible solution: degree equalities make the feasible set bounded, and its basic solution has polynomial binary encoding length by determinant bounds. Feasibility and such a point can be obtained in polynomial time through the standard directed minimum-cut separation oracle and rational LP methods. This is a theoretical algorithm; the repository's explicit-cut floating-point simplex is **not** that implementation.

There are `O(n^2)` coordinates of `z`. Taking `D` as the product of their positive denominators gives `log D` at most the sum of their bit lengths. Each binary multiplicity `D z_e` therefore has polynomial bit length. The construction manuscript's Theorem 1.1 expressly accepts that representation. Expanding `D z_e` parallel copies would invalidate the claimed polynomial running time.

The manuscript's Section 6 binary-input reduction was also checked at its interface. For each pair of original multiplicity `c_e`, it sets `c'_e=min(c_e,k)` and `a_e=floor(2n^2 c'_e/k)`. Every cut retains `c'`-mass at least `k`; rounding loses less than one per crossing pair, and at most `n^2/4` pairs cross a cut. Hence the explicit graph has cut size at least `2n^2-n^2/4 >= n^2`, contains fewer than `n^4` copies, and has each cut at most `(2n^2/k)` times the original cut. An explicit-graph `C_0/n^2`-thin tree therefore projects to a `2C_0/k`-thin tree in the binary-input graph. This checks the stated compression arithmetic; it does not verify the manuscript's algorithm for the explicit-graph case.

For a polynomial-bit algorithmic approximation claim, assume the metric costs are rationally encoded, or specify a suitable exact comparison/arithmetic model. A threshold is chosen from the finitely many input edge costs. At the least Held–Karp-feasible threshold `tau`, `tau <= OPT`; a `G_tau^(p_0)` tour has every metric edge of cost at most `p_0 tau` by the directed triangle inequality. Consequently `ALG <= p_0 OPT`.

**Result:** Polynomiality follows at the level of the cited construction theorem and standard exact LP/flow/matching routines, not from the current C++ executable.

## Additional theoretical claim in the repo

The forced vertex-split lemma in `PROOF.md` was checked separately. A Hamiltonian cycle of the split graph must use the new `v_in -> v_out` bridge, so contracting the pair yields an original Hamiltonian cycle. For Held–Karp feasibility, transferring the old arc values and assigning 1 to the bridge preserves degree equalities. A cut with `v_in` inside and `v_out` outside has outgoing bridge value 1. A cut with `v_out` inside and `v_in` outside has incoming bridge value 1; flow balance makes its outgoing value 1 or more. Cuts keeping the pair together reduce to original cuts. This proof is valid.

## Limits on claims and remaining audit

1. **Source-proof status:** This audit checked both Theorem 1.1 statements and the construction paper's binary-multiplicity section, but did not reprove all geometric, fixed-point, matrix-signing, and finite-precision lemmas in the two manuscripts. Present the corollaries as conditional on those source theorems until specialist peer review or formal verification is available. An index entry for a Lean formalization is not, by itself, a verification of every theorem and algorithmic claim.
2. **Numeric guarantee:** The symbolic `p_0` is valid after choosing a common universal `C`; a numerical ratio requires an extracted explicit constant from a checked proof. The empirically observed `p*=2` and `ALG/OPT <= 1.74194` on benchmark instances do not prove universal bounds.
3. **Novelty:** The implication from constant supported thin trees to constant-factor Bottleneck ATSP was already explicit in AKS Theorem 3 and its discussion. The [Svensson–Tarnawski–Végh paper, Section 6](https://www.laszlovegh.eu/papers/svensson-tarnawski-vegh-atsp-stoc.pdf) also states the conditional implication. The repo's bridge supplies the algebra connecting the new strong-thin-tree theorem to that known implication; this audit does not establish priority or novelty of the resulting corollary.
4. **Executable status:** The current repository supplies exact/heuristic trees on small instances and implements downstream AKS rounding, but not the new deterministic strong-thin-tree construction. Its experiments verify examples, not the universal theorem.

## Recommended statement

> Assuming the existence and binary-input constructive theorems on strong thin spanning trees as stated in the September 2026 OpenAI manuscripts, every feasible rational Held–Karp solution has a supported constant-thin tree. Combining this with the AKS rounding lemmas gives a universal constant Hamiltonian power; for rationally encoded asymmetric metrics it gives a deterministic polynomial-time constant-factor Bottleneck ATSP algorithm at the theorem level. The new tree construction is not implemented in this repository, and the source manuscripts' full proofs have not been independently certified here.
