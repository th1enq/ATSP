# Proof dossier: Strong thin trees imply a constant-factor Bottleneck ATSP approximation

**Status:** the reduction and its source interfaces were audited on 2026-10-08; the corollaries remain conditional on the two strong-thin-tree source theorems. See [`docs/THEORY_AUDIT_2026-10-08.md`](docs/THEORY_AUDIT_2026-10-08.md). The source manuscripts' full proofs and novelty have not been independently certified.

This document separates (A) source theorems from (B) the new bridge derived in this project.

---

## 1. Source theorems used

### 1.1 An–Kleinberg–Shmoys, Bottleneck ATSP

Source:

- H.-C. An, R. Kleinberg, D. B. Shmoys, *Approximation Algorithms for the Bottleneck Asymmetric Traveling Salesman Problem*, ACM Transactions on Algorithms 17(4), 2021.
- DOI: https://doi.org/10.1145/3478537
- arXiv: https://arxiv.org/abs/2012.14233

The source defines the Held–Karp feasibility system on a digraph `G=(V,A)`:

\[
 x(\delta^+(v))=x(\delta^-(v))=1 \quad \forall v\in V,
\]

\[
 x(\delta^+(S))\ge 1 \quad \forall \varnothing\ne S\subsetneq V,
\]

\[
 x\ge0.
\]

For a feasible solution `x`, define the undirected vector

\[
 z_{\{u,v\}}=x_{uv}+x_{vu}.
\]

Their Definition 2 calls a spanning tree `T` a **supported β-thin tree** with respect to `z` when it is contained in the support of `z` and

\[
 |T\cap\delta(S)|\le \beta z(\delta(S))
 \quad \forall S\subsetneq V.
\]

The source results used here are:

- **Theorem 1:** a probabilistic algorithm finds a supported
  \[
  \beta=\frac{4\ln n}{\ln\ln n}
  \]
  thin tree with high probability for an extreme Held–Karp point.
- **Lemma 4:** given any feasible Held–Karp solution and a supported β-thin tree, a spanning circuit visiting every vertex at most
  \[
  \lceil4\beta\rceil
  \]
  times can be found in polynomial time.
- **Lemmas 2–3:** a spanning circuit visiting every vertex at most `k` times can be shortcut to a Hamiltonian cycle in
  \[
  G^{2k-1}.
  \]
- **Theorem 2:** this yields an
  \[
  O(\log n/\log\log n)
  \]
  approximation for metric Bottleneck ATSP.
- **Theorem 3:** if a supported `f(n)`-thin tree can be found in polynomial time for a class, then an `O(f(n))` Bottleneck ATSP approximation follows.
- **Question 1:** does there exist a universal constant `p` such that `G^p` is Hamiltonian for every digraph whose Held–Karp relaxation is feasible?

The arXiv PDF states these results explicitly in Sections 2, 3, and 5.

### 1.2 OpenAI Math Result 174

Source repository:

https://github.com/openai/math

Catalog entry:

https://github.com/openai/math/blob/main/overview.tex

The Result 174 catalog entry states that every finite loopless `k`-edge-connected multigraph has a spanning tree `T` such that every cut satisfies

\[
 |T\cap\delta(S)|\le \frac{C}{k}|\delta(S)|
\]

for a universal constant `C`. The companion result states that such a tree can be constructed deterministically in polynomial time even when parallel-edge multiplicities are binary encoded. For deductions using both the existence and constructive statements, choose `C` at least as large as the constants in both source theorems.

The catalog points to:

- `The strong thin tree conjecture`, 2026-09-23.
- `A polynomial-time construction of strong thin trees`, 2026-09-23.

**Caution.** OpenAI's repository explicitly notes that its manuscripts have different levels of verification. The existence result is listed with Lean notes in the public catalog, while the constructive companion must still be independently audited before a downstream algorithm is presented as externally verified.

---

## 2. New bridge theorem

### Theorem 1 — Held–Karp feasible ⇒ constant supported thin tree

Let `x` be any rational feasible Held–Karp solution on a digraph `G=(V,A)`. Define

\[
 z_{\{u,v\}}=x_{uv}+x_{vu}.
\]

Assuming OpenAI Result 174, there exists a spanning tree `T` in the support of `z` such that

\[
 \boxed{
 |T\cap\delta(S)|\le \frac{C}{2}z(\delta(S))
 }
 \qquad
 \forall \varnothing\ne S\subsetneq V.
\]

Thus every feasible Held–Karp solution admits a supported `C/2`-thin tree.

### Proof

For a proper nonempty set `S`,

\[
 z(\delta(S))
 =x(\delta^+(S))+x(\delta^-(S)).
\]

Held–Karp gives

\[
 x(\delta^+(S))\ge1.
\]

Since

\[
 \delta^-(S)=\delta^+(V\setminus S),
\]

and `V\S` is also proper and nonempty,

\[
 x(\delta^-(S))\ge1.
\]

Therefore

\[
 \boxed{z(\delta(S))\ge2.}
\]

Because `x` is rational, choose a common denominator `D` for all coordinates of `z`. Form a loopless multigraph `H` by replacing every support edge `e` with

\[
 m_e=Dz_e
\]

parallel copies. For every proper cut,

\[
 |\delta_H(S)|=Dz(\delta(S))\ge2D.
\]

Hence `H` is `2D`-edge-connected.

Apply Result 174 with `k=2D`. There exists a spanning tree `T_H` satisfying

\[
 |T_H\cap\delta_H(S)|
 \le
 \frac{C}{2D}|\delta_H(S)|.
\]

Substitute `|δ_H(S)|=Dz(δ(S))`:

\[
 |T_H\cap\delta_H(S)|
 \le
 \frac C2 z(\delta(S)).
\]

A spanning tree cannot contain two parallel copies of one unordered pair, because two parallel copies already form a 2-cycle in the multigraph. Therefore `T_H` projects to a simple spanning tree `T` in the support of `z`, preserving every cut count. Consequently

\[
 |T\cap\delta(S)|\le(C/2)z(\delta(S)).
\]

`T` is a supported `C/2`-thin tree. ∎

---

## 3. Bit complexity of the scaling step

The reduction does **not** require explicit expansion of `Dz_e` parallel copies.

A rational polynomial-time LP solution has polynomial encoding length. If its denominators have polynomial total bit length, a common denominator `D` also has polynomial bit length even if its numerical value is exponentially large.

The constructive Result 174 catalog entry explicitly states polynomial time under **binary-encoded parallel-edge multiplicities**. Thus the intended input to the strong-thin-tree algorithm is a weighted/multiplicity representation

```text
(edge e, multiplicity D z_e)
```

rather than an explicitly expanded multigraph.

This is the key algorithmic reason denominator clearing is compatible with polynomial bit complexity.

---

## 4. Consequence: constant Hamiltonian power

An–Kleinberg–Shmoys Lemma 4 converts a supported β-thin tree into a spanning circuit that visits every vertex at most

\[
 k=\lceil4\beta\rceil
\]

times. Lemma 3 converts such a circuit into a Hamiltonian cycle in

\[
 G^{2k-1}.
\]

Set

\[
 \beta=C/2.
\]

Then

\[
 k=\lceil2C\rceil,
\]

and therefore

\[
 \boxed{
 p_0=2\lceil2C\rceil-1
 }
\]

is a universal constant such that every Held–Karp-feasible digraph has a Hamiltonian cycle in `G^{p0}`.

This gives an affirmative answer to Question 1 of the Bottleneck ATSP paper, conditional on the strong thin-tree theorem.

**Important:** this existence consequence uses only the existence theorem. It does not require an implementation of the constructive companion.

---

## 5. Consequence: constant-factor Bottleneck ATSP

For a metric instance, let `τ*` be the minimum threshold for which Held–Karp is feasible on `G_{≤τ*}`. Then

\[
 \tau^*\le OPT.
\]

With β=`C/2`, the AKS framework constructs a Hamiltonian cycle in

\[
 G_{\le\tau^*}^{\,2\lceil2C\rceil-1}.
\]

Every shortcut corresponds to a directed path of at most

\[
 2\lceil2C\rceil-1
\]

arcs of cost at most `τ*`. By the directed triangle inequality, each Hamiltonian-cycle edge has metric cost at most

\[
 (2\lceil2C\rceil-1)\tau^*.
\]

Hence

\[
 \boxed{
 ALG\le(2\lceil2C\rceil-1)OPT.
 }
\]

Thus a deterministic polynomial-time implementation follows **if** the constructive OpenAI Result 174 is correct exactly as summarized in the catalog.

---

## 6. Comparison with the 2021 paper

The 2021 paper uses

\[
 \beta_{AKS}=\frac{4\ln n}{\ln\ln n}
\]

and obtains factor

\[
 2\left\lceil\frac{16\ln n}{\ln\ln n}\right\rceil-1
 =O(\log n/\log\log n).
\]

The bridge above replaces the thinness term by the universal constant

\[
 \beta=C/2,
\]

so the factor becomes

\[
 \boxed{2\lceil2C\rceil-1=O(1).}
\]

The Held–Karp thresholding, circulation construction, degree-bounded Eulerian circuit, and Hall-transversal shortcutting are still the framework of An–Kleinberg–Shmoys. The new argument supplies the previously missing constant-thin-tree ingredient.

---

## 7. Implemented downstream AKS pipeline

The C++ artifact implements the **downstream** rounding in the 2021 paper for any supplied supported β-thin tree:

1. orient every tree edge along a positive Held–Karp arc;
2. assign arc lower bounds `1` on oriented tree arcs and `0` elsewhere;
3. assign unrounded arc upper bounds
   \[
   \ell(a)+2\beta x_a;
   \]
4. split every vertex into `v_in -> v_out` and assign the vertex-arc capacity equal to the sum of its unrounded outgoing upper bounds;
5. round upper bounds upward and solve an **integral feasible circulation** by a lower-bound-to-max-flow reduction;
6. contract split vertices and construct an Eulerian circuit with Hierholzer's algorithm;
7. set
   \[
   k=\lceil4\beta\rceil;
   \]
8. partition the circuit into length-`k` blocks;
9. find a system of distinct representatives by bipartite matching (Hall's theorem guarantees success);
10. retain one occurrence of every vertex, including all representatives, obtaining a Hamiltonian cycle in
    \[
    G^{2k-1}.
    \]

The implementation independently verifies that every produced shortcut has directed distance at most `2k-1` in the original threshold graph.

### What is **not** implemented

The C++ artifact does **not** claim to reproduce the September-2026 OpenAI strong-thin-tree construction itself. It supplies:

- exact optimal supported thin trees for tiny supports;
- inverse-`z` spanning-tree heuristics;
- weighted random tree search;
- local edge-swap improvement;
- the complete downstream AKS circulation/shortcut pipeline.

This separation prevents a heuristic from being mislabeled as the new theorem's deterministic construction.

---

## 8. Forced vertex-split hard-family lemma

The benchmark uses a simple transformation to turn the 6-vertex HK-feasible non-Hamiltonian witness into arbitrarily larger HK-feasible non-Hamiltonian digraphs.

Choose a vertex `v`. Replace it by `v_in=v` and a new `v_out`. Keep all old incoming arcs entering `v_in`, move every old outgoing arc of `v` to leave `v_out`, and add the sole bridge

\[
 v_{in}\to v_{out}.
\]

### Non-Hamiltonicity is preserved

`v_in` has only one outgoing arc, to `v_out`, and `v_out` has only one incoming arc, from `v_in`. Therefore every Hamiltonian cycle of the split graph must use the consecutive pair

\[
 v_{in}\to v_{out}.
\]

Contracting this pair would produce a Hamiltonian cycle in the original graph. Thus if the original graph is non-Hamiltonian, so is the split graph.

### Held–Karp feasibility is preserved

Given a feasible `x` in the original graph:

- copy every incoming `u->v` value to `u->v_in`;
- copy every outgoing `v->w` value to `v_out->w`;
- assign
  \[
  x(v_{in},v_{out})=1;
  \]
- leave all other values unchanged.

Degree equalities remain one. Cuts not separating the pair contract to old cuts. A cut separating `v_in` from `v_out` has at least the unit bridge or a unit total old in/out flow crossing in the required direction. Hence every subtour cut remains at least one.

The C++ LP solver revalidates the transformed family independently for every generated size.

---

## 9. Claims and caution

### Internally established

- the bridge proof above;
- the `C/2` constant substitution;
- the constant-power corollary;
- the conditional constant-factor Bottleneck ATSP corollary;
- the downstream AKS rounding implementation;
- exact small-instance checks described in `BENCHMARK_RESULTS.md`.

### Requires external audit

- novelty after the very recent OpenAI Math release;
- exact assumptions and proof details of the constructive strong-thin-tree companion;
- whether an explicit usable numerical value of `C` is supplied by the manuscript;
- publication-level claim that this is the first constant-factor Bottleneck ATSP approximation.

Do not replace these caveats by stronger wording without independent review.
