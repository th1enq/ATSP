# MASTER HANDOFF — Strong Thin Trees → Bottleneck ATSP
## Theory bridge, exact verification, benchmark plan, and implementation specification

**Research date:** 2026-10-07  
**Purpose:** single source of truth for an AI coding/research agent to implement, reproduce, stress-test, benchmark, and prepare thesis-quality experiments.

---

# 0. Executive summary

This project studies a new consequence of **OpenAI Math Result 174** (“The strong thin tree conjecture” + companion deterministic construction) for the paper:

> Hyung-Chan An, Robert D. Kleinberg, David B. Shmoys,  
> **Approximation Algorithms for the Bottleneck Asymmetric Traveling Salesman Problem**,  
> ACM Transactions on Algorithms 17(4), Article 35, 2021.  
> DOI: https://doi.org/10.1145/3478537  
> arXiv: https://arxiv.org/abs/2012.14233

The original Bottleneck ATSP paper gives an
\[
O\!\left(\frac{\log n}{\log\log n}\right)
\]
approximation and explicitly asks whether there is a universal constant \(p\) such that the \(p\)-th power of every digraph with a feasible Held–Karp relaxation is Hamiltonian. It also proves that a polynomial-time supported \(f(n)\)-thin-tree routine yields an \(O(f(n))\)-approximation for Bottleneck ATSP.

OpenAI Math Result 174 states that every finite loopless \(k\)-edge-connected multigraph has a spanning tree using at most a universal \(C/k\) fraction of every cut, and its companion manuscript states that such a tree can be constructed deterministically in polynomial time even when parallel-edge multiplicities are binary encoded.

The core bridge proved in this handoff is:

\[
\boxed{
\text{Held–Karp feasible }x
\Longrightarrow
z_{\{u,v\}}=x_{uv}+x_{vu}
\Longrightarrow
\text{binary-encoded }2D\text{-edge-connected multigraph}
\Longrightarrow
(C/2)\text{-thin supported tree}.
}
\]

Combining this with An–Kleinberg–Shmoys yields the candidate consequences:

\[
\boxed{
\text{deterministic polynomial-time }O(1)\text{-approximation for Bottleneck ATSP}
}
\]

and, already from the existence theorem alone,

\[
\boxed{
\exists p_0=O(1)\text{ such that every HK-feasible digraph has }G^{p_0}\text{ Hamiltonian}.
}
\]

A concrete bound in terms of the universal constant \(C\) is

\[
\boxed{
p_0 = 2\lceil 2C\rceil - 1.
}
\]

This is a **derived corollary candidate**. It must be independently audited before being presented as a publication-level novelty claim.

---

# 1. Status labels

Use these labels everywhere.

- **SOURCE-VERIFIED** — directly supported by a cited paper/repository.
- **DERIVED-PROVED** — mathematical derivation checked internally and written below.
- **SESSION-VERIFIED** — computational experiment rerun in the 2026-10-07 session.
- **RESEARCH-LOG** — previously reported experiment; must be rerun in the final repository.
- **CONJECTURE** — evidence only.
- **TODO-AUDIT** — must be checked by an independent human/agent.
- **DO-NOT-CLAIM** — not yet safe for thesis/paper wording.

---

# 2. Primary sources

## 2.1 OpenAI Math

Repository:

https://github.com/openai/math

Catalog overview:

https://github.com/openai/math/blob/main/overview.tex

Result 174 summary in the catalog:

> Deterministic construction of strong thin spanning trees. Every finite loopless \(k\)-edge-connected multigraph on at least two vertices has a spanning tree containing at most a universal \(C/k\) fraction of the edges of every cut. Such a tree can be found deterministically in polynomial time, even with binary-encoded parallel-edge multiplicities.

Main existence manuscript:

https://github.com/openai/math/blob/main/preprints/The-strong-thin-tree-conjecture-September-23-2026/paper.pdf

Companion constructive manuscript:

https://github.com/openai/math/blob/main/preprints/A-polynomial-time-construction-of-strong-thin-trees-September-23-2026/paper.pdf

Lean formalization catalog:

https://github.com/openai/math/blob/main/lean/formalization.yaml

**Important repository warning:** OpenAI explicitly states that the collection contains results at different verification stages and that some unformalized results could have issues. Therefore all downstream algorithmic claims must be independently audited.

---

## 2.2 Bottleneck ATSP paper

Journal:

https://doi.org/10.1145/3478537

arXiv:

https://arxiv.org/abs/2012.14233

Paper facts used below:

1. Held–Karp feasibility is used as a threshold lower-bound certificate.
2. A supported \(\beta\)-thin tree w.r.t.
   \[
   z^*_{\{u,v\}}=x^*_{uv}+x^*_{vu}
   \]
   can be converted in polynomial time into a spanning circuit in which every vertex is visited at most
   \[
   \lceil 4\beta\rceil
   \]
   times.
3. Their shortcutting framework then produces a Hamiltonian cycle in
   \[
   G^{2\lceil 4\beta\rceil-1}.
   \]
4. Therefore a polynomial-time supported \(f(n)\)-thin-tree routine implies an \(O(f(n))\)-approximation for Bottleneck ATSP.
5. Their explicit Question 1 asks whether a universal constant \(p\) exists such that every digraph with feasible Held–Karp relaxation has Hamiltonian \(p\)-th power.

---

## 2.3 Pre-OpenAI thin-tree state of the art

Nathan Klein, Neil Olver, Zi Song Yeoh,  
**Thin Trees for Near Minimum Cuts**, ICALP 2026:

https://doi.org/10.4230/LIPIcs.ICALP.2026.129  
https://arxiv.org/abs/2605.12669

The May/July 2026 paper states that the strong thin-tree conjecture was still open at that time and that the best general bound was
\[
O(\operatorname{polylog}\log n/k).
\]

This provides useful chronology: Result 174 is a genuinely new ingredient relative to the literature immediately before its release.

---

# 3. Problem definition — Bottleneck ATSP

Input: a complete directed asymmetric metric
\[
c:V\times V\to\mathbb R_{\ge0},
\]
with
\[
c(u,w)\le c(u,v)+c(v,w).
\]

A Hamiltonian cycle \(H\) has bottleneck cost
\[
\operatorname{bn}(H)=\max_{(u,v)\in H}c(u,v).
\]

Goal:
\[
\operatorname{OPT}_{BATSP}
=
\min_H \operatorname{bn}(H).
\]

For a threshold \(\tau\), define the threshold digraph
\[
G_{\le\tau}=(V,A_{\le\tau}),
\qquad
A_{\le\tau}=\{(u,v):c(u,v)\le\tau\}.
\]

If \(G_{\le\tau}\) is Hamiltonian, then a bottleneck tour of cost at most \(\tau\) exists.

---

# 4. Held–Karp feasibility system

For a digraph \(G=(V,A)\), use variables \(x_a\ge0\).

The feasibility form used by An–Kleinberg–Shmoys is:

\[
x(\delta^+(v))=1
\quad\forall v\in V,
\]

\[
x(\delta^-(v))=1
\quad\forall v\in V,
\]

\[
x(\delta^+(S))\ge1
\quad
\forall \varnothing\ne S\subsetneq V.
\]

For every feasible solution \(x\), define an undirected vector on the support graph:

\[
\boxed{
z_{\{u,v\}}=x_{uv}+x_{vu},
}
\]
where a missing directed arc contributes zero.

The Bottleneck ATSP algorithm of An–Kleinberg–Shmoys finds the minimum cost threshold \(\tau^*\) for which this relaxation is feasible.

Then
\[
\tau^*\le \operatorname{OPT}_{BATSP}.
\]

---

# 5. Core bridge theorem

## Theorem — Held–Karp feasible ⇒ constant supported thin tree

Assume OpenAI Result 174.

Let \(x\) be any rational feasible Held–Karp solution on \(G=(V,A)\), and let

\[
z_{\{u,v\}}=x_{uv}+x_{vu}.
\]

Then there exists a spanning tree \(T\) contained in the support of \(z\) satisfying

\[
\boxed{
|T\cap\delta(S)|
\le
\frac C2\,z(\delta(S))
\qquad
\forall\varnothing\ne S\subsetneq V.
}
\]

Hence \(T\) is a supported \(\beta\)-thin tree with

\[
\boxed{\beta=C/2.}
\]

If the constructive companion to Result 174 is valid as stated, such a tree is computable deterministically in polynomial time in the bit length of \(x\).

### Status

**DERIVED-PROVED, TODO-AUDIT externally.**

---

# 6. Proof of the bridge theorem

## Step 1 — every undirected \(z\)-cut has weight at least 2

For every proper nonempty \(S\subset V\),

\[
z(\delta(S))
=
x(\delta^+(S))
+
x(\delta^-(S)).
\]

Held–Karp gives

\[
x(\delta^+(S))\ge1.
\]

Also,

\[
\delta^-(S)=\delta^+(V\setminus S),
\]

and \(V\setminus S\) is also proper and nonempty, so

\[
x(\delta^-(S))
=
x(\delta^+(V\setminus S))
\ge1.
\]

Therefore

\[
\boxed{
z(\delta(S))\ge2.
}
\]

No separate flow-balance argument is needed.

---

## Step 2 — clear denominators

Because \(x\) is rational, choose an integer common denominator \(D\ge1\) such that

\[
Dz_e\in\mathbb Z_{\ge0}
\]

for every undirected support edge \(e\).

Construct a loopless multigraph \(H\) on \(V\) in which edge \(e\) has multiplicity

\[
m_e=Dz_e.
\]

For every proper nonempty cut \(S\),

\[
|\delta_H(S)|
=
D z(\delta(S))
\ge2D.
\]

Thus

\[
\boxed{H\text{ is }2D\text{-edge-connected}.}
\]

---

## Step 3 — apply OpenAI Result 174

Apply the strong thin-tree theorem to \(H\) with \(k=2D\).

There exists a spanning tree \(T_H\) such that

\[
|T_H\cap\delta_H(S)|
\le
\frac{C}{2D}|\delta_H(S)|.
\]

Substitute

\[
|\delta_H(S)|=Dz(\delta(S)):
\]

\[
|T_H\cap\delta_H(S)|
\le
\frac C2 z(\delta(S)).
\]

A spanning tree of a multigraph cannot use two parallel copies of the same unordered pair, since two parallel tree edges form a 2-cycle. Therefore \(T_H\) naturally projects to a simple spanning tree \(T\) on the support of \(z\), with the same cut counts.

Hence

\[
\boxed{
|T\cap\delta(S)|
\le
(C/2)\,z(\delta(S)).
}
\]

This is exactly supported \(C/2\)-thinness.

\[
\square
\]

---

# 7. Bit-complexity / polynomiality of denominator scaling

The reduction must not explicitly expand an enormous multigraph.

A rational LP solution produced in polynomial time has polynomial encoding length.

Write each \(z_e\) with a rational numerator/denominator.

Choose \(D\) as a common multiple of denominators. Its **numeric value** may be enormous, but its binary representation has polynomially many bits: a product of polynomially many polynomial-bit denominators still has polynomial total bit length.

The companion OpenAI result explicitly claims polynomial running time even when parallel-edge multiplicities are represented in binary.

Therefore the algorithmic bridge is intended to operate on:

```text
(edge e, multiplicity m_e = D z_e)
```

without materializing \(m_e\) copies.

### Hard requirement for implementation

Never expand binary multiplicities into explicit parallel edges in the full algorithm.

Small-instance validation may expand them only when \(D\) is tiny.

---

# 8. Consequence A — constant-factor Bottleneck ATSP

An–Kleinberg–Shmoys prove:

Given a supported \(\beta\)-thin tree w.r.t. \(z\), one can find in polynomial time a spanning circuit visiting every vertex at most

\[
k=\lceil4\beta\rceil
\]

times.

Their shortcutting lemma converts this to a Hamiltonian cycle in

\[
G^{2k-1}.
\]

For the threshold metric this yields approximation ratio

\[
2\lceil4\beta\rceil-1.
\]

Substitute

\[
\beta=C/2:
\]

\[
\boxed{
\rho
=
2\lceil2C\rceil-1.
}
\]

Because \(C\) is universal,

\[
\boxed{\rho=O(1).}
\]

If the constructive OpenAI theorem is correct, this gives a deterministic polynomial-time constant-factor approximation for metric Bottleneck ATSP.

### Status

**DERIVED-PROVED conditional on the constructive Result 174 claim; TODO-AUDIT the companion manuscript and full pipeline.**

---

# 9. Consequence B — affirmative answer to Question 1 of An–Kleinberg–Shmoys

Their Question 1:

> Does there exist a constant \(p\) such that the \(p\)-th power of any digraph with a feasible Held–Karp relaxation is Hamiltonian?

The bridge theorem provides a supported \(C/2\)-thin tree for every feasible Held–Karp solution.

Their Lemma 4 gives a spanning circuit visiting each vertex at most

\[
\lceil2C\rceil
\]

times.

Their shortcutting lemma then gives a Hamiltonian cycle in

\[
G^{2\lceil2C\rceil-1}.
\]

Therefore:

\[
\boxed{
p_0=2\lceil2C\rceil-1
}
\]

is a universal constant satisfying the requested property.

### Important distinction

For this **existence** consequence, the existence form of the strong thin-tree theorem is enough. The constructive companion is needed only to convert the result into an explicit polynomial-time approximation algorithm.

### Status

**DERIVED-PROVED conditional only on the existence theorem; TODO-AUDIT externally.**

---

# 10. Why this does not follow merely from the constant-factor min-sum ATSP result

Svensson–Tarnawski–Végh solved constant-factor approximation for the ordinary **min-sum** ATSP.

That does not automatically give a constant approximation for **Bottleneck ATSP**.

The Bottleneck ATSP paper explicitly remained interested in whether the new min-sum methods could be adapted, and the thin-tree route is a separate mechanism.

Do not conflate:

```text
min-sum ATSP
```

with

```text
Bottleneck ATSP.
```

---

# 11. Source chronology / novelty status

## SOURCE-VERIFIED chronology

- 2021 journal paper: Bottleneck ATSP approximation
  \[
  O(\log n/\log\log n)
  \]
  and Question 1.
- ICALP 2026 (May/July): strong thin-tree conjecture still stated as open.
- OpenAI Math Result 174 manuscript date: 2026-09-23.
- OpenAI Research Catalog shown as October 6, 2026.
- Current research date: 2026-10-07.

## Current novelty search

Searches performed include:

```text
"bottleneck ATSP" "strong thin tree" 2026
"bottleneck asymmetric traveling salesman" constant approximation 2026
"Held-Karp" Hamiltonian power 2026
OpenAI strong thin tree Bottleneck ATSP
```

No public paper was found that explicitly states the exact downstream corollary derived here.

### However

The OpenAI result is extremely recent.

Therefore use:

> “new-corollary candidate / apparently unpublished consequence”

until a systematic citation/arXiv/DBLP/Scholar audit and external review is completed.

---

# 12. Computational verification already rerun on 2026-10-07

This section contains only results recomputed in the current session.

---

## 12.1 Exhaustive labeled digraphs on 4 vertices

There are

\[
2^{4\cdot3}=4096
\]

loopless labeled directed graphs on 4 vertices.

For each graph:

1. solve Held–Karp feasibility LP;
2. if feasible, test Hamiltonicity exactly by bitmask dynamic programming.

Result:

\[
\boxed{1194}
\]

graphs are Held–Karp feasible.

Among them:

\[
\boxed{0}
\]

are non-Hamiltonian.

### Status

**SESSION-VERIFIED.**

Expected final-repository regression test:

```text
n=4 total = 4096
HK feasible = 1194
HK feasible and non-Hamiltonian = 0
```

If the implementation does not reproduce these exact numbers, stop.

---

# 13. Six-vertex hard witness

Vertices:

```text
0,1,2,3,4,5
```

Arcs:

```text
0 -> 4

1 -> 0
1 -> 4
1 -> 5

2 -> 0
2 -> 3

3 -> 1
3 -> 4
3 -> 5

4 -> 1
4 -> 2

5 -> 2
5 -> 3
5 -> 4
```

## 13.1 Explicit Held–Karp solution

Set

\[
x_{0,4}=1.
\]

Set \(x=1/2\) on:

```text
1 -> 0
1 -> 5

2 -> 0
2 -> 3

3 -> 1
3 -> 5

4 -> 1
4 -> 2

5 -> 2
5 -> 3
```

All other listed arcs receive zero.

Session verification confirms:

\[
x(\delta^+(v))=x(\delta^-(v))=1
\]

for every vertex and

\[
\min_{\varnothing\ne S\subsetneq V}x(\delta^+(S))=1.
\]

Thus it is Held–Karp feasible.

---

## 13.2 Hamiltonicity

Exact DP verifies:

\[
\boxed{G\text{ is not Hamiltonian}.}
\]

Its square is Hamiltonian.

One Hamiltonian cycle in \(G^2\) is:

```text
0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 0
```

Hence the minimum Hamiltonian power for this witness is

\[
\boxed{p^*=2.}
\]

---

## 13.3 Undirected Held–Karp vector

Positive \(z_e=x_{uv}+x_{vu}\):

```text
{0,1}: 1/2
{0,2}: 1/2
{0,4}: 1

{1,3}: 1/2
{1,4}: 1/2
{1,5}: 1/2

{2,3}: 1/2
{2,4}: 1/2
{2,5}: 1/2

{3,5}: 1
```

---

## 13.4 Exact optimal supported thinness

All supported spanning trees of the 10-edge undirected support were enumerated.

Number of supported spanning trees:

\[
\boxed{128}.
\]

For each tree \(T\), exact rational thinness was computed:

\[
\beta(T)
=
\max_{\varnothing\ne S\subsetneq V}
\frac{|T\cap\delta(S)|}{z(\delta(S))}.
\]

Optimum:

\[
\boxed{
\beta^*=4/3.
}
\]

One optimal tree is:

```text
{0,2}
{0,4}
{1,4}
{2,3}
{3,5}
```

Another session-found optimum is:

```text
{0,1}
{0,4}
{1,3}
{2,4}
{2,5}
```

### Status

**SESSION-VERIFIED.**

This witness must be hard-coded as a regression test.

---

# 14. Converting the six-vertex witness to a Bottleneck ATSP metric

Define

\[
c(u,v)=d_G(u,v),
\]

the directed shortest-path distance in the witness digraph.

This is an asymmetric metric.

The threshold-\(1\) digraph is exactly \(G\).

Held–Karp is feasible at threshold

\[
\tau^*=1.
\]

But \(G\) is non-Hamiltonian, so optimum bottleneck cannot be 1.

Since \(G^2\) is Hamiltonian,

\[
\boxed{
\operatorname{OPT}_{BATSP}=2.
}
\]

Thus this example has threshold-LP gap

\[
\boxed{2}.
\]

Use this as an end-to-end integration test.

---

# 15. Earlier research-log experiments that must be reproduced

The following were reported in the earlier exploratory phase but were **not rerun in the 2026-10-07 audit**.

They must appear in the final repo only after reproduction.

## RESEARCH-LOG A — broad random search

Reported:

```text
15,500 random directed graphs
n in {5,6,7,8,9,10,12}
rough edge probability 0.18–0.53
4,904 Held–Karp feasible
8 Held–Karp feasible but non-Hamiltonian
8/8 had Hamiltonian square
```

Status:

**RESEARCH-LOG — reproduce from scratch.**

---

## RESEARCH-LOG B — targeted hard-instance search

Reported:

```text
29 unique HK-feasible non-Hamiltonian instances
n = 6..10
```

Reported exact best supported thinness:

| n | # hard | min beta* | median beta* | max beta* | max p* |
|---:|---:|---:|---:|---:|---:|
| 6 | 6 | 1.000 | 1.250 | 1.333 | 2 |
| 7 | 4 | 1.000 | 1.292 | 1.333 | 2 |
| 8 | 7 | 1.000 | 1.333 | 1.333 | 2 |
| 9 | 6 | 1.333 | 1.333 | 1.333 | 2 |
| 10 | 6 | 1.167 | 1.333 | 1.333 | 2 |

Reported global:

\[
1\le\beta^*\le4/3,
\]

and

\[
29/29:\quad G^2\text{ Hamiltonian}.
\]

Status:

**RESEARCH-LOG — reproduce before thesis use.**

---

# 16. Experimental conjecture worth testing

Small-instance evidence motivates:

\[
\boxed{
\textbf{Conjecture: every Held–Karp feasible digraph may already have Hamiltonian square.}
}
\]

Equivalently:

\[
p=2?
\]

This is **much stronger** than the constant-power theorem obtained from strong thin trees.

The original Bottleneck ATSP paper itself points out that a square theorem would be especially attractive, but does not prove it.

### Status

**CONJECTURE ONLY.**

The benchmark should aggressively search for a counterexample.

A single HK-feasible graph with non-Hamiltonian \(G^2\) kills this conjecture but does not affect the constant-\(p\) theorem.

---

# 17. Important distinction between theorem and experiment

The main theorem candidate is **not**:

\[
p=2.
\]

The theorem candidate is:

\[
\boxed{
p=2\lceil2C\rceil-1=O(1).
}
\]

The \(p=2\) hypothesis is purely experimental.

Do not mix them.

---

# 18. No official benchmark suite located

The An–Kleinberg–Shmoys paper is theoretical.

Current searches did not locate an author benchmark dataset or reference implementation.

Therefore the final experimental study must use a transparent **reproducible benchmark suite**, not call synthetic instances “official benchmarks”.

Fair comparison targets are:

1. the paper's theoretical
   \[
   O(\log n/\log\log n)
   \]
   thin-tree factor / approximation guarantee;
2. exact optimum for small instances;
3. exact optimal thinness \(\beta^*\) for small support graphs;
4. the new OpenAI strong-thin-tree implementation if it can be reproduced.

---

# 19. Repository architecture

Recommended:

```text
bottleneck-atsp-thin-tree/
├── README.md
├── CITATION.cff
├── pyproject.toml
├── CMakeLists.txt
├── src/
│   ├── digraph.hpp
│   ├── metric.hpp
│   ├── held_karp.hpp
│   ├── held_karp.cpp
│   ├── separation.hpp
│   ├── separation.cpp
│   ├── hamiltonian_dp.hpp
│   ├── hamiltonian_dp.cpp
│   ├── graph_power.hpp
│   ├── graph_power.cpp
│   ├── thinness.hpp
│   ├── thinness.cpp
│   ├── thin_tree_exact.hpp
│   ├── thin_tree_exact.cpp
│   ├── thin_tree_heuristics.hpp
│   ├── thin_tree_heuristics.cpp
│   ├── openai_stt.hpp
│   ├── openai_stt.cpp
│   ├── aks_rounding.hpp
│   ├── aks_rounding.cpp
│   └── main.cpp
├── python/
│   ├── hk_reference.py
│   ├── ham_reference.py
│   ├── thin_tree_reference.py
│   ├── generators.py
│   ├── exhaustive.py
│   ├── hunt_counterexample.py
│   ├── benchmark.py
│   ├── aggregate.py
│   └── plots.py
├── instances/
│   ├── regression/
│   │   └── witness6.json
│   ├── generated/
│   └── hard/
├── tests/
│   ├── test_hk.py
│   ├── test_hamiltonian.py
│   ├── test_power.py
│   ├── test_thinness.py
│   ├── test_witness6.py
│   └── test_exhaustive_n4.py
├── results/
└── docs/
    ├── proof_bridge.md
    ├── benchmark_protocol.md
    └── novelty_audit.md
```

---

# 20. Recommended implementation stack

## Correctness/reference layer

Python:

- `numpy`
- `scipy.optimize.linprog`
- `scipy.optimize.milp` if useful
- `networkx`

## Final performance layer

C++20:

- graph primitives;
- bitmask Hamiltonian DP;
- min-cut/separation;
- exact subset routines.

For LP/MIP choose one available backend and document it:

- Gurobi, if licensed;
- HiGHS;
- SCIP;
- OR-Tools where appropriate.

Do not silently mix solver timings across machines.

---

# 21. Canonical instance format

JSON:

```json
{
  "n": 6,
  "arcs": [[0,4], [1,0], [1,4], [1,5]],
  "weights": null,
  "metadata": {
    "family": "witness6",
    "seed": null
  }
}
```

Metric instance:

```json
{
  "n": 20,
  "cost": [[0,1,3], [2,0,1], [1,4,0]],
  "metadata": {
    "family": "shortest_path_metric",
    "seed": 20261007
  }
}
```

Use integer costs where possible.

---

# 22. Held–Karp exact feasibility solver

For small \(n\), explicitly include all subtour cuts.

Variables:

\[
x_{uv}
\]

only for arcs present.

Constraints:

\[
x(\delta^+(v))=1,
\]

\[
x(\delta^-(v))=1,
\]

\[
x(\delta^+(S))\ge1.
\]

For \(n\le14\), explicit cuts are acceptable for correctness experiments.

For larger \(n\), implement separation:

1. solve degree-constrained LP;
2. from current \(x\), compute minimum directed cut;
3. if a cut has weight \(<1-\varepsilon\), add it;
4. repeat.

Because indegree/outdegree equations balance cuts, a directed min-cut routine is sufficient.

Always verify the final solution against an independent cut scan when \(n\) is small enough.

---

# 23. Rational reconstruction

The theoretical bridge uses rational \(x\).

Production LP solvers return floating point.

For experiments there are three modes.

## Mode R1 — floating analysis

Use doubles and evaluate thinness numerically.

This is fine for runtime studies but **not** for exact theorem witnesses.

## Mode R2 — rational small instances

Use:

- exact fractions from explicitly constructed solutions, or
- rational reconstruction from solver values with bounded denominators.

Then verify all HK constraints exactly.

## Mode R3 — exact LP backend

Optional if an exact rational LP solver is available.

For theorem regression tests, prefer explicit rational instances rather than trusting reconstructed floats.

---

# 24. Hamiltonian-cycle exact solver

For \(n\lesssim22\), use Held–Karp bitmask DP.

Fix start vertex 0.

State:

\[
DP[S][v]
\]

means there is a directed path from 0 visiting exactly \(S\) and ending at \(v\).

Runtime:

\[
O(n^2 2^n).
\]

Return a witness cycle when one exists.

This solver is required for:

- exact Hamiltonicity;
- exact graph-power threshold;
- exact metric bottleneck optimum on small \(n\).

---

# 25. Graph power and exact minimum Hamiltonian power

For unweighted digraph \(G\), define \(G^p\) by:

\[
(u,v)\in A(G^p)
\iff
1\le d_G(u,v)\le p.
\]

Compute all-pairs directed shortest-path lengths.

Then:

```text
for p = 1..diameter:
    build G^p
    test Hamiltonian
    return first feasible p
```

Call result:

\[
p^*(G).
\]

Key benchmark metric:

\[
\max p^*
\]

over all HK-feasible instances found.

---

# 26. Exact optimal supported thin tree

Given rational \(z\), define:

\[
\beta(T)=
\max_{\varnothing\ne S\subsetneq V}
\frac{|T\cap\delta(S)|}{z(\delta(S))}.
\]

Goal:

\[
\beta^*=\min_T\beta(T),
\]

where \(T\) ranges over spanning trees of the support of \(z\).

## Method E1 — enumerate spanning trees

For tiny supports.

Use this for the six-vertex regression witness.

## Method E2 — MILP

Variables:

```text
y_e in {0,1}
beta >= 0
```

Tree constraints:

\[
\sum_e y_e=n-1,
\]

\[
y(\delta(S))\ge1
\quad
\forall\varnothing\ne S\subsetneq V.
\]

Thinness constraints:

\[
y(\delta(S))
\le
\beta\,z(\delta(S))
\quad
\forall S.
\]

Minimize \(\beta\).

For \(n\le12\) enumerate all cuts directly.

For larger \(n\), cut separation for the tree constraints is easy; thinness-separation is a weighted cut-ratio problem and should be handled carefully. Do not invent a separation routine without proof.

---

# 27. Exact thinness evaluator for a fixed tree

For a fixed tree \(T\), exact \(\beta(T)\) on \(n\le24\) can be computed by enumerating one side of each cut:

```text
for mask in 1 .. 2^(n-1)-1:
    numerator = number of tree edges crossing mask
    denominator = z-weight of support edges crossing mask
    ratio = numerator / denominator
```

Fix vertex 0 outside/inside to avoid duplicate complementary cuts.

Use exact rational arithmetic for regression tests.

---

# 28. Thin-tree heuristics to benchmark

Even if reproducing the OpenAI construction is difficult, the thesis needs practical empirical baselines.

Implement:

## H1 — inverse-\(z\) MST

Edge cost:

\[
w_e=1/(z_e+\epsilon).
\]

Intuition: prefer large fractional support.

## H2 — \(-\log z\) MST

\[
w_e=-\log(z_e+\epsilon).
\]

## H3 — random weighted spanning-tree sampling

Sample trees biased toward large \(z_e\), keep the best measured \(\beta\).

## H4 — edge-swap local search

Start from a tree.

Repeatedly:

1. add non-tree edge;
2. remove one edge from the induced cycle;
3. accept if exact/estimated \(\beta\) improves.

For small \(n\), evaluate exact \(\beta\) after every candidate.

## H5 — worst-cut guided repair

1. find current worst cut;
2. identify tree edges crossing it;
3. try exchanges reducing the numerator while preserving connectivity.

Document if this is heuristic.

## H6 — exact optimum

Small-instance oracle only.

## H7 — OpenAI strong-thin-tree construction

High-priority stretch goal:

reproduce the companion manuscript faithfully.

Do not substitute a heuristic and call it the OpenAI algorithm.

---

# 29. Reproducing the OpenAI construction

The implementing agent must first read:

```text
The-strong-thin-tree-conjecture-September-23-2026/paper.pdf
A-polynomial-time-construction-of-strong-thin-trees-September-23-2026/paper.pdf
```

Then produce:

```text
docs/openai_algorithm_notes.md
```

containing:

1. exact theorem statement;
2. explicit/implicit value of universal constants if given;
3. data structures required;
4. subroutines and their complexity;
5. handling of binary multiplicities;
6. every randomized vs deterministic choice;
7. whether the manuscript gives implementable pseudocode or mainly an existence construction.

Only after this review begin coding `openai_stt`.

If direct implementation is impractical for a graduation thesis, the thesis can still:

- use Result 174 as a theoretical ingredient;
- benchmark exact and heuristic thin trees;
- clearly distinguish “theoretical constructive existence” from “our implementation”.

---

# 30. AKS baseline guarantee

The 2021 paper uses

\[
\beta_{\text{AKS}}(n)
=
\frac{4\ln n}{\ln\ln n}
\]

for the supported thin-tree bound in its general algorithm.

The resulting bottleneck factor is

\[
2\lceil4\beta_{\text{AKS}}\rceil-1.
\]

For experiments, report:

```text
beta_exact
beta_heuristic
beta_AKS_theory
```

and ratios:

\[
\beta_{\text{heuristic}}/\beta^*,
\]

\[
\beta_{\text{AKS}}/\beta^*.
\]

Do not interpret \(\beta_{\text{AKS}}\) as the actual thinness produced by a specific sampled tree unless that original sampling algorithm is implemented.

It is a theoretical guarantee.

---

# 31. Benchmark family X4 — exhaustive n=4

Enumerate every loopless labeled digraph:

\[
2^{12}=4096.
\]

For each:

1. test HK feasibility;
2. exact Hamiltonian;
3. if HK feasible:
   - record support size;
   - LP solution;
   - \(p^*\).

Acceptance targets:

```text
total = 4096
HK feasible = 1194
HK-feasible non-Hamiltonian = 0
```

This benchmark is small enough to run in CI.

---

# 32. Benchmark family X5 — exhaustive n=5

There are:

\[
2^{20}=1,048,576
\]

digraphs.

This is expensive but potentially feasible with strong preprocessing and parallelism.

Recommended filter sequence:

1. indegree/outdegree at least 1;
2. strongly connected;
3. cycle-cover feasibility / bipartite perfect matching;
4. exact Hamiltonian test;
5. HK LP only on survivors where needed.

Primary scientific question:

> Is there an HK-feasible non-Hamiltonian digraph on 5 vertices?

Do not assume the answer.

If full exhaustive LP enumeration is too costly, report exact coverage and use symmetry/isomorphism reduction.

---

# 33. Benchmark family W6 — fixed regression witness

Always run:

```text
instances/regression/witness6.json
```

Expected:

```text
HK feasible: yes
Hamiltonian G: no
Hamiltonian G^2: yes
p* = 2
support spanning trees = 128
beta* = 4/3
metric tau_HK = 1
metric optimum bottleneck = 2
```

This is the most important single regression instance.

---

# 34. Benchmark family ER — random directed Erdős–Rényi

Parameters:

```text
n = 6,8,10,12,14,16,18,20
p = 0.15,0.20,0.25,0.30,0.40,0.50,0.60
replicates = 100 or compute-budget appropriate
```

Generation:

every ordered pair \(u\ne v\) is included independently with probability \(p\).

Record:

```text
strongly_connected
cycle_cover
hk_feasible
hamiltonian
p_star
support_edges
min_cut_z
```

Small \(n\):

also exact \(\beta^*\).

Larger \(n\):

heuristic thinness only.

---

# 35. Benchmark family HARD — rejection search

Goal: obtain HK-feasible **non-Hamiltonian** digraphs.

Loop:

```text
generate candidate
if not strongly connected: reject
if no directed cycle cover: reject
solve HK
if infeasible: reject
test Hamiltonian
if Hamiltonian: reject
save
```

Diversify generation:

1. ER random digraphs;
2. start from a directed cycle then perturb;
3. start from known hard witness then vertex-split/blow-up;
4. random degree-constrained digraphs;
5. adversarial local search maximizing Hamiltonian obstruction while preserving HK feasibility.

Deduplicate by canonical graph hash/isomorphism if possible.

Target:

```text
>=100 hard instances for n <= 12
>=1000 hard instances overall
```

if compute permits.

---

# 36. Counterexample hunt for p=2

For every HK-feasible instance:

1. if \(G\) Hamiltonian → \(p^*=1\);
2. else test \(G^2\);
3. if \(G^2\) non-Hamiltonian:
   - save immediately;
   - exact-verify HK feasibility;
   - minimize graph;
   - rerun with rational certificate.

This is a **high-priority search**.

A verified HK-feasible graph with non-Hamiltonian square would be scientifically valuable even though it does not affect the constant-power result.

---

# 37. Counterexample minimization protocol

If an apparent \(p=2\) counterexample is found:

1. obtain a rational HK certificate;
2. independently verify every cut;
3. independently verify no Hamiltonian cycle in \(G^2\);
4. attempt vertex deletion;
5. attempt arc deletion;
6. preserve HK feasibility and non-Hamiltonian square;
7. canonicalize;
8. save full certificate.

Do not publish a floating-point-only counterexample.

---

# 38. Benchmark family HK-X — random fractional Held–Karp supports

Instead of sampling graphs first, sample feasible LP structures.

Methods:

## F1 — convex combination of Hamiltonian cycles

Generate several directed Hamiltonian cycles \(C_i\) and weights \(\lambda_i\):

\[
x=\sum_i\lambda_i\chi^{C_i}.
\]

This is automatically Held–Karp feasible.

But the support contains Hamiltonian cycles by construction, so it is unsuitable for non-Hamiltonian support search; it is useful for thin-tree quality.

## F2 — solve random LP objectives

On a random strongly connected digraph:

\[
\min c^\top x
\]

over Held–Karp feasibility with random \(c\).

This tends to generate extreme points / sparse supports.

Use these for thinness benchmarking.

---

# 39. Benchmark family METRIC — end-to-end Bottleneck ATSP

Generate an asymmetric metric from a weighted strongly connected digraph \(D\):

1. assign positive integer arc lengths;
2. compute all-pairs directed shortest paths;
3. define
   \[
   c(u,v)=d_D(u,v).
   \]

This satisfies the directed triangle inequality.

For small \(n\), exact optimum bottleneck:

1. sort distinct metric costs;
2. binary search threshold \(\tau\);
3. test Hamiltonian cycle in \(G_{\le\tau}\).

Also compute minimum HK-feasible threshold:

\[
\tau_{\text{HK}}.
\]

Report:

\[
\frac{\operatorname{OPT}}{\tau_{\text{HK}}}.
\]

When an approximation implementation exists, report:

\[
\frac{\operatorname{ALG}}{\operatorname{OPT}}.
\]

---

# 40. Metric generator families

Use:

## M1 — random complete asymmetric integer weights → metric closure

```text
n = 6,8,10,12,14,16
base weight = Uniform{1,...,100}
```

Compute Floyd–Warshall metric closure.

## M2 — sparse directed graph shortest-path metric

Generate strongly connected sparse digraph, positive arc weights, then metric closure.

This often creates more threshold structure.

## M3 — perturb hard threshold graphs

Take an HK-feasible non-Hamiltonian threshold graph \(G\).

Assign all arcs of \(G\) length 1 and absent direct arcs length via shortest paths.

The six-vertex witness is the canonical example.

## M4 — clustered asymmetric metrics

Build several clusters with cheap internal arcs and asymmetric intercluster bridges; take metric closure.

These may stress bottleneck thresholding.

---

# 41. Exact Bottleneck ATSP solver for small n

Given metric \(c\):

```text
values = sorted(unique c[u][v], u != v)
binary search smallest tau:
    G_tau = arcs with c[u][v] <= tau
    HamiltonianDP(G_tau)
```

This returns exact

\[
\operatorname{OPT}_{BATSP}.
\]

Separate solver:

```text
binary search smallest tau:
    HeldKarpFeasible(G_tau)
```

returns

\[
\tau_{\text{HK}}.
\]

This directly measures the threshold-LP gap.

---

# 42. End-to-end approximation pipeline

The ideal full implementation is:

```text
metric c
  |
  v
minimum HK-feasible threshold tau*
  |
  v
rational feasible Held-Karp solution x
  |
  v
z_uv = x_uv + x_vu
  |
  v
binary multiplicity multigraph H
  |
  v
OpenAI strong-thin-tree construction
  |
  v
supported beta-thin tree T
  |
  v
AKS circulation / bounded-visit spanning circuit
  |
  v
AKS partition + transversal shortcut
  |
  v
Hamiltonian cycle in G_tau*^(2 ceil(4 beta)-1)
  |
  v
metric shortcut tour
```

If full OpenAI tree construction is not implemented, create an experimental pipeline with:

```text
exact thin tree (small n)
or
heuristic thin tree (larger n)
```

and label it honestly.

---

# 43. Reproducing the AKS circulation step

This is a core implementation milestone.

Given:

- feasible \(x\),
- supported \(\beta\)-thin tree \(T\),

reproduce Lemma 4 from the Bottleneck ATSP paper.

Output:

- an integral Eulerian spanning multigraph/circuit;
- verify every vertex appears at most
  \[
  \lceil4\beta\rceil
  \]
  times.

Tests:

```text
flow conservation
support arcs all belong to G
connected/spanning
Eulerian
max visits <= ceil(4 beta)
```

Do not skip this step if claiming an actual approximation implementation.

---

# 44. Shortcutting / power-cycle step

Given a spanning circuit visiting each vertex at most \(k\) times, implement the paper's partition/transversal method yielding a Hamiltonian cycle in:

\[
G^{2k-1}.
\]

Validate every shortcut:

```text
directed distance in G <= 2k-1
```

Then in a metric:

\[
c(u,v)\le(2k-1)\tau^*
\]

by repeated triangle inequality.

This turns the graph-power statement into a bottleneck guarantee.

---

# 45. Baselines

The benchmark should include:

## B0 — exact optimum

Small n only.

## B1 — AKS theoretical guarantee

\[
\beta=4\ln n/\ln\ln n.
\]

Not an actual measured tree unless the old sampler is implemented.

## B2 — exact optimal supported thin tree

Small n.

## B3 — heuristic supported thin tree

H1–H5 above.

## B4 — OpenAI strong-thin-tree construction

If reproduced.

## B5 — direct Hamiltonian-power search

Compute exact \(p^*\) for small n.

This is independent of thin-tree rounding and helps understand how loose the theorem's constant may be.

---

# 46. Main experimental questions

## Q1 — Does the bridge work computationally?

For exact small cases:

- build HK \(x\);
- construct \(z\);
- compute \(\beta^*\);
- verify the AKS circulation/shortcut pipeline.

## Q2 — How small is \(\beta^*\) in practice?

Compare:

\[
\beta^*
\quad\text{vs}\quad
4\ln n/\ln\ln n.
\]

## Q3 — Is \(p^*=2\) always observed?

Search aggressively.

## Q4 — What is the threshold Held–Karp gap?

Measure:

\[
\operatorname{OPT}_{BATSP}/\tau_{\text{HK}}.
\]

## Q5 — How good are cheap thin-tree heuristics?

Measure:

\[
\beta_{\text{heur}}/\beta^*.
\]

## Q6 — Can the OpenAI construction be implemented practically?

Compare runtime and tree quality.

## Q7 — How loose is the theoretical constant-power route?

Compare:

```text
actual p*
AKS power using beta*
AKS power using heuristic beta
theoretical p0 from C, if an explicit C is extractable
```

---

# 47. Benchmark grid — exact small instances

Suggested:

```text
n = 4..12
```

For each n:

```text
random HK-feasible instances: 200
hard HK-feasible non-Hamiltonian: as many as found, target 50+
random metric instances: 200
```

Exact tasks:

- HK feasibility;
- Hamiltonian;
- \(p^*\);
- \(\tau_{\text{HK}}\);
- Bottleneck optimum;
- exact \(\beta^*\) where support size allows.

Timeout:

```text
60 s exact thin-tree MILP
60 s Hamiltonian DP
```

Record timeouts, do not discard them.

---

# 48. Benchmark grid — medium instances

Suggested:

```text
n = 15,20,30,40,50,75,100
```

No exact Hamiltonian DP beyond feasible size.

Measure:

- HK LP runtime;
- support sparsity;
- heuristic thinness;
- OpenAI construction runtime if available;
- AKS circulation/rounding runtime;
- produced bottleneck cost.

For metrics where exact OPT unavailable, lower bound with:

\[
\tau_{\text{HK}}.
\]

Report certified ratio to the lower bound:

\[
\operatorname{ALG}/\tau_{\text{HK}}.
\]

This is an upper bound on the actual approximation ratio, not the exact ratio.

---

# 49. Experimental metrics

Per instance store:

```text
instance_id
family
seed
n
m_arcs
strongly_connected
hk_feasible
hk_runtime_ms
hk_support_arcs
hk_min_cut
hamiltonian
ham_runtime_ms
p_star
tau_hk
opt_bottleneck
lp_gap
beta_exact
beta_heuristic
beta_openai
thin_tree_runtime_ms
aks_visit_bound
actual_max_visits
alg_bottleneck
alg_over_opt
alg_over_tau_hk
peak_rss_mb
status
git_commit
machine_id
```

Use null when unavailable.

---

# 50. Plot requirements

At minimum:

1. \(\beta^*\) vs \(n\).
2. \(\beta^*\) vs AKS theoretical \(\beta\).
3. histogram of \(p^*\) among HK-feasible non-Hamiltonian graphs.
4. support size vs \(\beta^*\).
5. \(\operatorname{OPT}/\tau_{\text{HK}}\) distribution.
6. heuristic \(\beta/\beta^*\).
7. thin-tree runtime vs \(n\).
8. end-to-end approximation ratio vs \(n\).
9. fraction of random graphs:
   - HK infeasible,
   - HK feasible Hamiltonian,
   - HK feasible non-Hamiltonian.
10. counterexample-hunt cumulative hard instances vs CPU hours.

For randomized experiments report median and IQR.

---

# 51. Reproducibility seed

Set:

```text
MASTER_SEED = 20261007
```

Derive instance seeds deterministically:

```text
SHA256(f"{MASTER_SEED}:{family}:{parameter_cell}:{replicate}")
```

Use the first 64 bits.

Store the derived seed in the result file.

---

# 52. Exact regression assertions

The CI suite must assert:

```text
X4:
    total graphs = 4096
    HK feasible = 1194
    HK feasible non-Hamiltonian = 0

W6:
    HK feasible = True
    Hamiltonian G = False
    Hamiltonian G^2 = True
    p* = 2
    support spanning-tree count = 128
    beta* = 4/3
```

If any fail, do not run performance benchmarks.

---

# 53. CLI specification

One executable:

```text
batsp
```

Examples:

```bash
batsp hk-feasible graph.json
batsp hamiltonian graph.json
batsp power graph.json --exact-p
batsp thinness graph.json --x solution.json --tree tree.json
batsp thin-tree-exact graph.json --x solution.json
batsp thin-tree-heuristic graph.json --x solution.json --method swap
batsp bottleneck-exact metric.json
batsp pipeline metric.json --thin-tree exact
batsp pipeline metric.json --thin-tree openai
```

JSON output only for machine mode.

---

# 54. Result JSON example

```json
{
  "instance_id": "hard_n8_seed123",
  "n": 8,
  "m_arcs": 23,
  "hk_feasible": true,
  "hamiltonian": false,
  "p_star": 2,
  "beta_exact": "4/3",
  "beta_exact_float": 1.3333333333333333,
  "hk_runtime_ms": 7.4,
  "thin_tree_runtime_ms": 21.8,
  "git_commit": "..."
}
```

Store exact rationals as strings.

---

# 55. Failure protocol

If a discrepancy is found:

1. save graph and LP certificate;
2. save solver logs;
3. independently verify HK;
4. independently verify Hamiltonian result;
5. minimize arcs/vertices;
6. switch to rational arithmetic;
7. create a regression test;
8. only then resume benchmark.

For a purported \(p=2\) counterexample, require two independent Hamiltonian implementations.

---

# 56. Thesis-safe claims right now

## Safe with source citation

OpenAI Result 174 states a universal \(C/k\) thin-tree theorem for \(k\)-edge-connected multigraphs and a companion deterministic polynomial-time construction with binary multiplicities.

An–Kleinberg–Shmoys prove that a polynomial-time supported \(f(n)\)-thin-tree algorithm gives an \(O(f(n))\)-approximation for Bottleneck ATSP.

They explicitly ask whether all HK-feasible digraphs have Hamiltonian \(p\)-th power for some constant \(p\).

## Safe as our derivation, pending external audit

\[
\text{HK feasible}
\Rightarrow
(C/2)\text{-thin supported tree}.
\]

Therefore

\[
p_0=2\lceil2C\rceil-1
\]

answers their Question 1 affirmatively.

If the constructive OpenAI result is correct as stated, the same bridge gives deterministic polynomial-time constant-factor Bottleneck ATSP.

## Safe computational claims from this session

- 4096 total labeled n=4 digraphs.
- 1194 HK feasible.
- 0 HK-feasible non-Hamiltonian at n=4.
- six-vertex witness values above.
- exact \(\beta^*=4/3\) on the witness.

---

# 57. Claims not yet safe

## DO-NOT-CLAIM

- “We are definitely the first to notice this corollary.”
- “The constant approximation is peer reviewed.”
- “The OpenAI companion implementation is practical.”
- “\(p=2\) for all Held–Karp feasible digraphs.”
- “\(\beta^*\le4/3\) universally.”
- “The historical 29-instance table is reproduced.”
- “The OpenAI universal constant \(C\) is small.”
- any numerical approximation factor unless the manuscript provides an explicit audited \(C\).

---

# 58. Independent proof-audit checklist

Before thesis submission, have another agent/human check:

- [ ] HK cut identity \(z(\delta(S))=x(\delta^+(S))+x(\delta^-(S))\).
- [ ] both terms are at least 1.
- [ ] common denominator has polynomial bit length.
- [ ] binary multiplicity input matches the constructive theorem's model.
- [ ] multigraph edge connectivity is at least \(2D\).
- [ ] multigraph spanning tree projects to support tree without duplicate parallel edges.
- [ ] cut counts are preserved by projection.
- [ ] thinness constant is exactly \(C/2\), not \(C\), \(2C\), etc.
- [ ] AKS Lemma 4 accepts any feasible HK solution, not only a special random extreme point.
- [ ] shortcut exponent is exactly \(2\lceil4\beta\rceil-1\).
- [ ] substitution yields \(2\lceil2C\rceil-1\).
- [ ] metric triangle inequality turns graph-power length into bottleneck factor.
- [ ] deterministic LP/flow/subroutine complexity remains polynomial in bit length.
- [ ] no hidden pseudo-polynomial expansion of \(D\).
- [ ] novelty search after OpenAI release is complete.

---

# 59. OpenAI-paper audit checklist

The agent must extract from the companion manuscript:

- [ ] exact input model;
- [ ] exact meaning of \(k\)-edge-connected for multigraphs;
- [ ] whether loops are excluded;
- [ ] whether zero multiplicities are simply omitted;
- [ ] exact form of universal \(C\);
- [ ] whether \(C\) is explicit;
- [ ] deterministic runtime polynomial;
- [ ] binary multiplicity statement;
- [ ] dependence on bit-length;
- [ ] required oracle/subroutine assumptions;
- [ ] any hidden randomness;
- [ ] Lean formalization scope: existence only or constructive theorem too.

Do not rely solely on the catalog summary for final thesis proof.

---

# 60. Potential stronger theoretical directions

After the core thesis result is secure, investigate:

## T1 — improve the constant for Held–Karp-derived multigraphs

The scaled multigraph is not arbitrary: it satisfies degree structure induced by HK.

Can this yield a better constant than generic \(C/2\)?

## T2 — prove \(p=2\) or find a counterexample

Highest-risk/high-reward direction.

## T3 — direct thin tree without denominator scaling

Prove a strong-thin theorem directly for the fractional vector \(z\).

This could simplify the bridge and implementation.

## T4 — exploit \(z(\delta(v))=2\)

HK gives

\[
z(\delta(v))=2
\]

for every vertex.

Generic strong thin-tree input does not have this regular fractional degree structure.

## T5 — exact worst-case \(\beta^*\) on small n

Enumerate HK-feasible supports and determine

\[
B_n=\max\beta^*.
\]

Small-n sequence may suggest a stronger theorem.

---

# 61. Exact-small-n research program

For each \(n\) where exhaustive search is feasible, compute:

\[
H_n=
\max\{p^*(G):G\text{ HK feasible}\},
\]

and

\[
B_n=
\max\{\beta^*(x):x\text{ selected HK certificate/support instance}\}.
\]

Note:

\(B_n\) depends on the chosen feasible \(x\) if a graph has many HK solutions. More principled alternatives:

\[
B_n^{\min x}
=
\max_G\min_{x\in HK(G)}\beta^*(x)
\]

or

\[
B_n^{\max x}
=
\max_G\max_{x\in HK(G)}\beta^*(x).
\]

These are much harder.

Be explicit about which definition is measured.

---

# 62. Choosing the Held–Karp solution in experiments

The original algorithm samples based on an extreme point solution.

Our bridge works for **any rational feasible solution**.

But \(\beta^*(x)\) can depend on \(x\).

Benchmark at least:

1. arbitrary LP feasible solution;
2. random-objective extreme point;
3. solution minimizing a thinness proxy if practical.

Record which \(x\) was used.

This can become an algorithmic contribution:

> choosing a better HK point may dramatically improve practical thinness.

---

# 63. Thinness-aware Held–Karp point selection

Exploratory heuristic:

Alternate between:

1. solve HK with current edge penalties;
2. find a thin tree;
3. identify worst cuts;
4. adjust LP objective to increase \(z\)-mass on those cuts.

This is not part of the proof.

Benchmark only after the core solver is stable.

---

# 64. Practical approximation portfolio

Even without implementing the full OpenAI construction, a strong thesis experiment can use:

```text
HK threshold
    |
    +--> exact thin tree, small n
    |
    +--> weighted MST heuristics
    |
    +--> random-tree sampling
    |
    +--> edge-swap improvement
    |
    +--> OpenAI construction, if implemented
```

Feed each tree into the same AKS rounding pipeline.

Compare final bottleneck tours.

This isolates the impact of thin-tree quality.

---

# 65. Ablation study

For heuristic pipeline:

```text
A0 inverse-z MST
A1 + random restarts
A2 + edge swaps
A3 + worst-cut repair
A4 + alternate HK point selection
```

Report:

| Variant | beta | final bottleneck | runtime | exact ratio where known |
|---|---:|---:|---:|---:|

---

# 66. Literature-comparison table for thesis

| Result | Previous literature | New bridge / this work |
|---|---|---|
| General strong thin tree | Open before Sep 2026; \(O(\mathrm{polylog}\log n/k)\) best general bound | OpenAI Result 174: \(C/k\) |
| Bottleneck ATSP | \(O(\log n/\log\log n)\) general approximation | candidate \(O(1)\) via Result 174 |
| HK-feasible graph power | explicit open Question 1 | candidate YES, \(p_0=2\lceil2C\rceil-1\) |
| Practical thinness | limited theoretical guarantee | exact/heuristic benchmark proposed |
| Square \(G^2\) | not known in general | experimental conjecture only |

---

# 67. Suggested thesis title

Primary:

> **Strong Thin Trees and Constant-Factor Approximation for Bottleneck Asymmetric TSP**

Alternative:

> **From Strong Thin Trees to Bottleneck ATSP: Theory, Algorithms, and Exact Experiments**

Vietnamese:

> **Từ cây khung mỏng mạnh đến xấp xỉ hằng số cho bài toán người du lịch bất đối xứng dạng nút thắt**

---

# 68. Suggested thesis contribution statement

Subject to proof/novelty audit:

1. **Theoretical bridge.** Show that any feasible Held–Karp solution induces, through rational scaling and the strong thin-tree theorem, a supported \(C/2\)-thin tree.
2. **Open-question consequence.** Derive a universal constant
   \[
   p_0=2\lceil2C\rceil-1
   \]
   such that every HK-feasible digraph has Hamiltonian \(p_0\)-th power.
3. **Algorithmic consequence.** Using the constructive strong-thin-tree theorem, derive a deterministic polynomial-time constant-factor approximation for Bottleneck ATSP.
4. **Exact experimental study.** Measure optimal supported thinness and minimum Hamiltonian power on small HK-feasible graphs.
5. **Heuristic study.** Develop practical thin-tree heuristics and compare them to exact optimum and theoretical bounds.
6. **Counterexample search.** Systematically test the stronger \(p=2\) hypothesis.

---

# 69. Agent milestones

## M0 — source audit

Read all primary papers and write exact theorem map.

Deliver:

```text
docs/source_audit.md
```

No code before this is done.

## M1 — exact graph core

Implement:

- directed graph;
- HK LP;
- Hamiltonian DP;
- graph powers.

Pass X4 and W6.

## M2 — exact thinness

Implement:

- cut enumeration;
- tree enumeration;
- MILP.

Reproduce W6:

\[
\beta^*=4/3.
\]

## M3 — benchmark generators

Implement ER, HARD, METRIC.

Reproduce prior research-log or document differences.

## M4 — heuristics

Implement H1–H5.

## M5 — AKS rounding

Implement circulation + shortcut pipeline.

## M6 — OpenAI construction audit

Decide whether full reproduction is feasible.

## M7 — OpenAI construction implementation

If feasible.

## M8 — full experiments

Produce all CSVs/tables/plots.

---

# 70. Acceptance criteria

The project is benchmark-ready only if:

1. X4 exact counts match:
   \[
   1194,0.
   \]
2. W6 passes all exact assertions.
3. HK solutions are independently verified on small n.
4. Hamiltonicity has two independent implementations for counterexample claims.
5. exact thinness agrees between enumeration and MILP on tiny cases.
6. deterministic seeds work.
7. every result contains commit/environment metadata.
8. no unresolved mismatch exists.
9. theorem proof has independent audit.
10. source/novelty audit is documented.

---

# 71. Recommended result table: hard instances

| id | n | m | HK | Ham(G) | Ham(G²) | p* | beta* | HK time | beta time |
|---|---:|---:|:---:|:---:|:---:|---:|---:|---:|---:|

This should become a centerpiece of the experimental chapter.

---

# 72. Recommended result table: metric instances

| family | n | tau_HK | OPT | LP gap | tree method | beta | ALG | ALG/OPT | runtime |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|

---

# 73. Machine/environment policy

Record:

```text
CPU
RAM
OS
Python
SciPy
NetworkX
C++ compiler
LP/MIP solver + version
solver threads
git commit
```

Use one thread for fair solver microbenchmarks unless stated otherwise.

For randomized algorithms, store random seed.

For MIP, store optimality gap and termination status.

---

# 74. Timeout policy

Suggested:

```text
HK LP small: 30 s
Hamiltonian exact: 60 s
thin-tree MILP: 300 s
end-to-end exact metric: 300 s
```

For medium heuristic runs:

```text
60 s per method per instance
```

Report timeout rather than silently excluding.

---

# 75. Statistical reporting

Random grids:

```text
replicates >= 20
```

when affordable.

Report:

- median;
- IQR;
- solve rate;
- timeout count.

For approximation ratios:

- median;
- max;
- 90th/95th percentile.

For exact hard instances, list every instance.

---

# 76. If OpenAI's universal C is enormous

This does not invalidate the theoretical result.

Separate:

```text
theoretical existence factor
```

from

```text
practical observed beta
```

The thesis can be interesting precisely because the generic constant may be huge while exact small-instance thinness is near 1.

Do not hide this distinction.

---

# 77. If the constructive manuscript is too hard to implement

Fallback thesis remains strong:

- prove the theoretical downstream corollary;
- independently validate small instances;
- implement exact \(\beta^*\);
- design practical thin-tree heuristics;
- implement AKS rounding using those trees;
- benchmark actual tour quality.

State clearly:

> The OpenAI companion theorem supplies polynomial-time constructibility theoretically; our experimental implementation uses separate exact/heuristic tree routines.

---

# 78. If the bridge proof is found wrong

Stop immediately.

The likely failure points to inspect are:

1. support projection from multigraph;
2. binary denominator encoding;
3. mismatch between strong-thin-tree cut measure and \(z\)-thinness;
4. AKS requirement on the Held–Karp point;
5. algorithmic constructibility.

Minimize the issue and revise all claims.

---

# 79. If a p=2 counterexample is found

This is not a failure of the thesis.

It becomes a new contribution:

> smallest known HK-feasible digraph whose square is non-Hamiltonian.

Then measure its:

- \(p^*\);
- exact \(\beta^*\);
- structural properties;
- relation to AKS Theorem 5 constructions.

---

# 80. If no p=2 counterexample is found

Do not claim a theorem.

Report:

```text
searched X graphs
Y HK feasible
Z HK feasible non-Hamiltonian
all Z had p*=2
largest n ...
CPU hours ...
```

This is strong empirical evidence only.

---

# 81. Final research priority order

1. **Independent proof audit of the bridge.**
2. **Read and audit OpenAI constructive manuscript.**
3. **Reproduce X4 and W6.**
4. **Reproduce the historical 29-hard-instance study.**
5. **Aggressive p=2 counterexample hunt.**
6. **Exact \(\beta^*\) benchmark.**
7. **Practical thin-tree heuristics.**
8. **AKS end-to-end rounding.**
9. **OpenAI construction implementation if feasible.**
10. **Full metric Bottleneck ATSP comparison.**

---

# 82. One-paragraph handoff to another AI agent

> Study OpenAI Math Result 174 and An–Kleinberg–Shmoys (Bottleneck ATSP). First independently verify the proof that a rational Held–Karp solution \(x\), after symmetrization \(z_{uv}=x_{uv}+x_{vu}\) and denominator scaling by \(D\), yields a \(2D\)-edge-connected binary-multiplicity multigraph. Apply Result 174 to derive a supported \(C/2\)-thin tree and check that AKS Lemma 4 + shortcutting gives Hamiltonian power \(p_0=2\lceil2C\rceil-1\) and a constant-factor Bottleneck ATSP approximation. Then implement exact HK feasibility, Hamiltonian DP, graph powers, and exact thinness. Reproduce the n=4 totals (4096 graphs, 1194 HK-feasible, zero non-Hamiltonian) and the 6-vertex witness (\(p^*=2,\beta^*=4/3\)). Only after zero mismatches, run the HARD and METRIC benchmark suites and attempt to reproduce the prior 29-hard-instance log. Search aggressively for an HK-feasible graph whose square is non-Hamiltonian. Keep theorem claims, OpenAI-source claims, and empirical conjectures strictly separated.

---

# 83. References

## OpenAI Math

OpenAI.  
**OpenAI Math repository.**  
https://github.com/openai/math

OpenAI.  
**The strong thin tree conjecture.**  
2026-09-23.  
https://github.com/openai/math/blob/main/preprints/The-strong-thin-tree-conjecture-September-23-2026/paper.pdf

OpenAI.  
**A polynomial-time construction of strong thin trees.**  
2026-09-23.  
https://github.com/openai/math/blob/main/preprints/A-polynomial-time-construction-of-strong-thin-trees-September-23-2026/paper.pdf

## Bottleneck ATSP

Hyung-Chan An, Robert D. Kleinberg, David B. Shmoys.  
**Approximation Algorithms for the Bottleneck Asymmetric Traveling Salesman Problem.**  
ACM Transactions on Algorithms 17(4), Article 35, 2021.  
https://doi.org/10.1145/3478537  
https://arxiv.org/abs/2012.14233

## Thin trees before Result 174

Nathan Klein, Neil Olver, Zi Song Yeoh.  
**Thin Trees for Near Minimum Cuts.**  
ICALP 2026.  
https://doi.org/10.4230/LIPIcs.ICALP.2026.129  
https://arxiv.org/abs/2605.12669

## Min-sum ATSP context

Ola Svensson, Jakub Tarnawski, László A. Végh.  
**A Constant-Factor Approximation Algorithm for the Asymmetric Traveling Salesman Problem.**  
JACM / STOC line of work.  
https://doi.org/10.1145/3424306

---

# 84. Final status

### SOURCE-VERIFIED

OpenAI Result 174 claims the strong thin-tree theorem and deterministic binary-multiplicity construction.

An–Kleinberg–Shmoys provide exactly the thin-tree-to-Bottleneck-ATSP framework needed downstream and pose the constant-Hamiltonian-power question.

### DERIVED-PROVED internally

\[
\boxed{
\text{HK feasible}\Rightarrow\text{supported }C/2\text{-thin tree}.
}
\]

\[
\boxed{
p_0=2\lceil2C\rceil-1.
}
\]

Conditional on the constructive theorem:

\[
\boxed{
\text{deterministic polynomial-time }O(1)\text{-approximation for Bottleneck ATSP}.
}
\]

### SESSION-VERIFIED

\[
4096\text{ n=4 digraphs}
\]

\[
1194\text{ HK feasible}
\]

\[
0\text{ HK-feasible non-Hamiltonian}
\]

and the explicit six-vertex witness with:

\[
\boxed{
p^*=2,\qquad \beta^*=4/3.
}
\]

### RESEARCH-LOG TO REPRODUCE

- 15,500-random-digraph exploratory search.
- 29 hard HK-feasible non-Hamiltonian instances.
- reported \(\beta^*\le4/3\) on those instances.
- reported \(29/29\) Hamiltonian squares.

### HIGH-PRIORITY OPEN EXPERIMENT

\[
\boxed{
\text{Find an HK-feasible digraph with non-Hamiltonian square, or push the search boundary much farther.}
}
