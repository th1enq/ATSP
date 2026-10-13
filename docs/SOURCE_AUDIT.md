# Source audit

## OpenAI Math Result 174

Public catalog:

https://github.com/openai/math/blob/main/overview.tex

The catalog states:

- every finite loopless `k`-edge-connected multigraph has a spanning tree meeting every cut in at most a universal `C/k` fraction of that cut;
- a companion result gives a deterministic polynomial-time construction;
- binary-encoded parallel-edge multiplicities are allowed.

Associated manuscripts listed by the catalog:

- https://github.com/openai/math/blob/main/preprints/The-strong-thin-tree-conjecture-September-23-2026/paper.pdf
- https://github.com/openai/math/blob/main/preprints/A-polynomial-time-construction-of-strong-thin-trees-September-23-2026/paper.pdf

The public OpenAI Math index also marks the existence paper with Lean notes. The repository warns that its papers are at different verification stages, so the constructive manuscript still needs an independent reading before final thesis submission.

## Bottleneck ATSP

H.-C. An, R. Kleinberg, D. B. Shmoys,
*Approximation Algorithms for the Bottleneck Asymmetric Traveling Salesman Problem*, TALG 17(4), 2021.

- DOI: https://doi.org/10.1145/3478537
- arXiv: https://arxiv.org/abs/2012.14233

Relevant exact locations in the arXiv PDF:

- Held–Karp LP: Section 2, equation (1).
- supported thin tree: Definitions 1–2.
- `4 ln n / ln ln n` tree: Theorem 1.
- circuit shortcut criterion: Lemma 2.
- degree-bounded circuit shortcut: Lemma 3.
- supported β-thin tree → at most `ceil(4β)` visits: Lemma 4.
- main `O(log n/log log n)` approximation: Theorem 2.
- generic `f(n)`-thin tree → `O(f(n))` approximation: Theorem 3.
- constant Hamiltonian-power open problem: Question 1 in Section 5.

## Immediate pre-Result-174 context

N. Klein, N. Olver, Z. S. Yeoh,
*Thin Trees for Near Minimum Cuts*, ICALP 2026 / arXiv:2605.12669.

The May 2026 paper describes the strong thin-tree conjecture as open and gives a near-minimum-cut result rather than the full universal-cut `O(1/k)` theorem. This establishes useful chronology immediately before the September 2026 OpenAI result.

## Novelty caution

Result 174 is extremely recent. The project has not found a public paper explicitly spelling out the same Bottleneck-ATSP corollary, but absence from a quick search is not proof of novelty. Before submission, check arXiv, DBLP, Google Scholar citations, Semantic Scholar, author pages, and any updates to the OpenAI manuscripts.
