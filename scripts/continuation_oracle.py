"""Exact separating hyperplanes for one Proposition 3.1 continuation step.

This is an oracle for the convex feasibility set (3.8), (3.14)--(3.16),
not an ellipsoid feasibility solver or a strong-thin-tree constructor.
Matrices use the upper-left (n-1)-square block of a centered full matrix.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from exact_psd import psd_or_negative_vector
from weighted_partition_oracle import violated_partition


@dataclass(frozen=True)
class LinearCut:
    """Valid affine inequality constant + sum(coeff[key] * x[key]) >= 0."""

    reason: str
    constant: Fraction
    coefficients: dict[str, Fraction]

    def value(self, point: dict[str, Fraction]) -> Fraction:
        return self.constant + sum((c * point.get(key, Fraction())
                                    for key, c in self.coefficients.items()), Fraction())


def _edge_vector(n: int, edge: tuple[int, int]) -> list[int]:
    u, v = edge
    b = [0] * (n - 1)
    if u < n - 1:
        b[u] += 1
    if v < n - 1:
        b[v] -= 1
    return b


def _quad_coeff(vector: list[Fraction], prefix: str) -> dict[str, Fraction]:
    return {f"{prefix}:{i}:{j}": vector[i] * vector[j] * (1 if i == j else 2)
            for i in range(len(vector)) for j in range(i, len(vector))}


def _laplacian(n: int, edges: list[tuple[int, int]]) -> list[list[Fraction]]:
    matrix = [[Fraction() for _ in range(n - 1)] for _ in range(n - 1)]
    for u, v in edges:
        if u < n-1:
            matrix[u][u] += 1
        if v < n-1:
            matrix[v][v] += 1
        if u < n-1 and v < n-1:
            matrix[u][v] -= 1
            matrix[v][u] -= 1
    return matrix


def _matrix(point: dict[str, Fraction], prefix: str, size: int) -> list[list[Fraction]]:
    return [[Fraction(point.get(f"{prefix}:{min(i,j)}:{max(i,j)}", 0))
             for j in range(size)] for i in range(size)]


def _psd_witness(matrix: list[list[Fraction]]) -> list[Fraction] | None:
    good, witness = psd_or_negative_vector(matrix)
    return None if good else witness


def _quadratic(matrix: list[list[Fraction]], vector: list[Fraction]) -> Fraction:
    return sum((matrix[i][j] * vector[i] * vector[j]
                for i in range(len(vector)) for j in range(len(vector))), Fraction())


def separate_step(n: int, edges: list[tuple[int, int]], active: list[bool],
                  u: list[Fraction], s: Fraction, t: Fraction, kappa: Fraction,
                  q_next: Fraction, point: dict[str, Fraction]) -> LinearCut | None:
    """Return a strictly violated rational cut, or certify all step constraints.

    Keys: Y:i:j for 0<=i<=j<n-1; lambda:i:j:k for ordered distinct
    triples; y:e and z:e for active edge indices. Inactive z is fixed to
    kappa. Missing keys mean zero. All cuts are in >=0 form.
    """
    m = len(edges)
    if n < 2 or len(active) != m or len(u) != m or s <= 0 or t <= 0 or kappa <= 0 or q_next < 0:
        raise ValueError("invalid continuation dimensions or parameters")
    if any(not (0 <= a < b < n) for a, b in edges):
        raise ValueError("invalid edge")
    if any(value < 0 for value in u):
        raise ValueError("negative ramp")
    point = {key: Fraction(value) for key, value in point.items()}

    def scalar(reason: str, constant: Fraction, coeff: dict[str, Fraction]) -> LinearCut | None:
        cut = LinearCut(reason, constant, coeff)
        return cut if cut.value(point) < 0 else None

    for key, value in point.items():
        if key.startswith("lambda:") or key.startswith("y:") or key.startswith("z:"):
            cut = scalar(f"{key} lower bound", Fraction(), {key: Fraction(1)})
            if cut:
                return cut
    triples = [(i, j, k) for i in range(n) for j in range(n) for k in range(n)
               if i != j and j != k and i != k]
    for i, j, k in triples:
        key = f"lambda:{i}:{j}:{k}"
        cut = scalar(f"{key} lower bound", Fraction(), {key: Fraction(1)})
        if cut:
            return cut
    for e in range(m):
        if not active[e]:
            continue
        for reason, constant, coeff in (
            ("y upper bound", Fraction(1), {f"y:{e}": Fraction(-1)}),
            ("z upper bound", kappa + 1, {f"z:{e}": Fraction(-1)}),
            ("ramp upper bound", kappa + u[e] - 4*t,
             {f"y:{e}": 5*t, f"z:{e}": Fraction(-1)}),
        ):
            cut = scalar(f"{reason} edge {e}", constant, coeff)
            if cut:
                return cut

    vectors = [_edge_vector(n, e) for e in edges]
    lap = _laplacian(n, edges)
    y_matrix = _matrix(point, "Y", n - 1)
    minus_lap = [[y_matrix[i][j] - lap[i][j] for j in range(n - 1)]
                 for i in range(n - 1)]
    witness = _psd_witness(minus_lap)
    if witness is not None:
        cut = LinearCut("Y >= L_H", -_quadratic(lap, witness),
                        _quad_coeff(witness, "Y"))
        assert cut.value(point) < 0
        return cut

    triangle: dict[tuple[int, int, int], list[list[int]]] = {}
    second = [[3*lap[i][j] - y_matrix[i][j] for j in range(n - 1)]
              for i in range(n - 1)]
    for i, j, k in triples:
        bij, bjk, bik = (_edge_vector(n, tuple(sorted(pair)))
                         for pair in ((i, j), (j, k), (i, k)))
        tri = [[bij[a]*bij[b] + bjk[a]*bjk[b] - bik[a]*bik[b]
                for b in range(n - 1)] for a in range(n - 1)]
        triangle[i, j, k] = tri
        lam = point.get(f"lambda:{i}:{j}:{k}", Fraction())
        for a in range(n - 1):
            for b in range(n - 1):
                second[a][b] -= lam * tri[a][b]
    witness = _psd_witness(second)
    if witness is not None:
        coeff = {key: -value for key, value in _quad_coeff(witness, "Y").items()}
        for i, j, k in triples:
            coeff[f"lambda:{i}:{j}:{k}"] = -_quadratic(triangle[i, j, k], witness)
        cut = LinearCut("3L_H - Y - sum lambda T >= 0", 3*_quadratic(lap, witness), coeff)
        assert cut.value(point) < 0
        return cut

    checked_responses = set()
    for e, enabled in enumerate(active):
        if not enabled:
            continue
        b = vectors[e]
        factor = 6*s*point.get(f"y:{e}", Fraction())
        response_key = (tuple(b), factor)
        if response_key in checked_responses:
            continue
        checked_responses.add(response_key)
        response = [[y_matrix[i][j] - factor*b[i]*b[j] for j in range(n - 1)]
                    for i in range(n - 1)]
        witness = _psd_witness(response)
        if witness is not None:
            dot = sum(witness[i]*b[i] for i in range(n - 1))
            coeff = _quad_coeff(witness, "Y")
            coeff[f"y:{e}"] = -6*s*dot*dot
            cut = LinearCut(f"response LMI edge {e}", Fraction(), coeff)
            assert cut.value(point) < 0
            return cut

    capacities = [point.get(f"z:{e}", Fraction()) if active[e] else kappa
                  for e in range(m)]
    violation = violated_partition(n, edges, capacities, q_next)
    if violation is not None:
        labels, _ = violation
        crossing = [e for e, (a, b) in enumerate(edges) if labels[a] != labels[b]]
        coeff = {f"z:{e}": Fraction(1) for e in crossing if active[e]}
        constant = kappa * sum(not active[e] for e in crossing) - q_next*(len(set(labels))-1)
        cut = LinearCut("partition capacity", constant, coeff)
        assert cut.value(point) < 0
        return cut
    return None
