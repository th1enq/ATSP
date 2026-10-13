"""Exact rational state transitions for Proposition 3.1.

The response Y,y,z must be supplied externally. This module checks it with
the exact separator and verifies the packing invariant after the transition.
It does not solve the convex feasibility problem.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

from continuation_oracle import _edge_vector, _laplacian, _matrix, separate_step
from weighted_partition_oracle import violated_partition


def inverse(matrix: list[list[Fraction]]) -> list[list[Fraction]]:
    n = len(matrix)
    if any(len(row) != n for row in matrix):
        raise ValueError("matrix must be square")
    aug = [[Fraction(x) for x in row] + [Fraction(int(i == j)) for j in range(n)]
           for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = next((row for row in range(col, n) if aug[row][col]), None)
        if pivot is None:
            raise ValueError("singular centered matrix")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        value = aug[col][col]
        aug[col] = [x / value for x in aug[col]]
        for row in range(n):
            if row != col:
                value = aug[row][col]
                aug[row] = [a - value*b for a, b in zip(aug[row], aug[col])]
    return [row[n:] for row in aug]


@dataclass
class ContinuationState:
    n: int
    edges: list[tuple[int, int]]
    r: int
    g: Fraction
    x: list[list[Fraction]]
    s: Fraction
    q: Fraction
    cone_lambda: dict[str, Fraction] = field(default_factory=dict)

    @property
    def kappa(self) -> Fraction:
        return Fraction(1, len(self.edges) + 1)

    @property
    def t(self) -> Fraction:
        return self.kappa / 32

    def ramp(self) -> list[Fraction]:
        inv = inverse(self.x)
        result = []
        cache = {}
        for edge in self.edges:
            if edge in cache:
                result.append(cache[edge])
                continue
            b = _edge_vector(self.n, edge)
            nonzero = [i for i, value in enumerate(b) if value]
            resistance = sum((b[i]*inv[i][j]*b[j] for i in nonzero for j in nonzero), Fraction())
            if resistance <= 0:
                raise ValueError("nonpositive effective resistance")
            value = max(Fraction(), min(Fraction(2), 1/(self.s*resistance)) - 1)
            cache[edge] = value
            result.append(value)
        return result

    def verify_invariant(self) -> bool:
        capacities = [value + self.kappa for value in self.ramp()]
        return violated_partition(self.n, self.edges, capacities, self.q) is None

    def advance(self, response: dict[str, Fraction]) -> "ContinuationState":
        u = self.ramp()
        active = [value > 0 for value in u]
        q_next = self.q - 2*self.g*self.r*self.t
        if q_next < 0:
            raise ValueError("negative next packing target")
        if not self.verify_invariant():
            raise ValueError("old packing invariant fails")
        cut = separate_step(self.n, self.edges, active, u, self.s, self.t,
                            self.kappa, q_next, response)
        if cut is not None:
            raise ValueError(f"invalid response: {cut.reason}, slack {cut.value(response)}")
        y = _matrix(response, "Y", self.n - 1)
        next_x = [[(1-self.t)*self.x[i][j] + self.t*y[i][j]
                   for j in range(self.n - 1)] for i in range(self.n - 1)]
        next_lambda = {key: (1-self.t)*self.cone_lambda.get(key, Fraction())
                       + self.t*value for key, value in response.items()
                       if key.startswith("lambda:")}
        for key, value in self.cone_lambda.items():
            if key not in next_lambda:
                next_lambda[key] = (1-self.t)*value
        next_state = ContinuationState(self.n, self.edges, self.r, self.g,
                                       next_x, (1+self.t)*self.s, q_next, next_lambda)
        if not next_state.verify_invariant():
            raise AssertionError("continuation invariant failed after valid response")
        return next_state


def initial_state(n: int, edges: list[tuple[int, int]], r: int,
                  g: Fraction) -> ContinuationState:
    if n < 2 or r < 1 or g <= 0 or any(not (0 <= a < b < n) for a, b in edges):
        raise ValueError("invalid initial state")
    if violated_partition(n, edges, [Fraction(1)]*len(edges), Fraction(r)) is not None:
        raise ValueError("graph does not contain the required tree packing")
    state = ContinuationState(n, edges, r, Fraction(g), _laplacian(n, edges),
                              Fraction(1, 2), Fraction(r))
    if not state.verify_invariant():
        raise ValueError("initial packing invariant fails")
    return state
