"""Exact rational weight search and leverage certificate for Lemma 4.1.

The returned positive weights specify an irrational whitened frame exactly;
its squared column norms are rational leverage scores. The module also
produces rounded frame columns and offers bounded experimental balancing.
"""

from __future__ import annotations

from fractions import Fraction
from math import isqrt

from continuation_oracle import _edge_vector
from continuation_state import inverse


class FrameError(RuntimeError):
    pass


def exp_rational_lower(x: Fraction, relative_error: Fraction) -> Fraction:
    """Return 0<a<=exp(x)<=(1+relative_error)*a exactly."""
    x = Fraction(x)
    relative_error = Fraction(relative_error)
    if relative_error <= 0 or relative_error >= 1:
        raise ValueError("relative error must be in (0,1)")
    if x == 0:
        return Fraction(1)
    positive = abs(x)
    upper_exp = 4 ** ((positive.numerator + positive.denominator - 1)
                      // positive.denominator)  # exp(t) <= 4^ceil(t)
    lower = Fraction(1)
    term = Fraction(1)
    order = 0
    while True:
        order += 1
        term *= positive / order
        lower += term
        next_term = term * positive / (order + 1)
        remainder = upper_exp * next_term
        if remainder <= relative_error * lower / 2:
            break
    upper = lower + remainder
    result = lower if x > 0 else 1 / upper
    # For positive x: exp(x)<=upper<=(1+eps/2)*lower.
    # For negative x: 1/upper<=exp(x)<=1/lower<=(1+eps/2)/upper.
    return result


def leverage_scores(n: int, edges: list[tuple[int, int]],
                    weights: list[Fraction]) -> list[Fraction]:
    if n < 2 or len(edges) != len(weights) or any(w <= 0 for w in weights):
        raise ValueError("invalid frame dimensions or weights")
    matrix = weighted_incidence_matrix(n, edges, weights)
    inv = inverse(matrix)
    result = []
    for weight, (u, v) in zip(weights, edges):
        resistance = inv[u][u]
        if v < n-1:
            resistance += inv[v][v] - inv[u][v] - inv[v][u]
        result.append(weight*resistance)
    return result


def weighted_incidence_matrix(n: int, edges: list[tuple[int, int]],
                               weights: list[Fraction]) -> list[list[Fraction]]:
    matrix = [[Fraction() for _ in range(n-1)] for _ in range(n-1)]
    for (u, v), weight in zip(edges, weights):
        if u < n-1:
            matrix[u][u] += weight
        if v < n-1:
            matrix[v][v] += weight
        if u < n-1 and v < n-1:
            matrix[u][v] -= weight
            matrix[v][u] -= weight
    return matrix


def find_frame_weights(n: int, edges: list[tuple[int, int]], q: int, r: int,
                       max_iterations: int | None = None
                       ) -> tuple[list[Fraction], list[Fraction], int]:
    """Gradient method (4.2)--(4.4), with rational exp enclosures.

    A returned tuple is exactly certified by its leverage scores. If the
    iteration cap is reached, the function raises rather than returning an
    unproved frame. The theorem's packing promise is the caller's duty.
    """
    m = len(edges)
    if n < 2 or q < 1 or r < q or m != q*(n-1):
        raise ValueError("B must have q(n-1) edges and q<=r")
    if any(not (0 <= u < v < n) for u, v in edges):
        raise ValueError("invalid frame edge")
    limit = max_iterations if max_iterations is not None else 2*n*m*(m+1)*r**4
    grid = 1
    while grid < 100*m*r*r:
        grid *= 2
    coordinates = [Fraction() for _ in edges]
    target = Fraction(1, q) + Fraction(4, r*q)
    for iteration in range(limit + 1):
        # Relative weight error O(1/(m*r^2)) gives O(1/r^2) gradient error.
        weights = [exp_rational_lower(d, Fraction(1, 100*m*r*r))
                   for d in coordinates]
        scores = leverage_scores(n, edges, weights)
        if max(scores) <= target:
            return weights, scores, iteration
        gradient = [score - Fraction(1, q) for score in scores]
        rounded = [Fraction((2*value.numerator*grid + value.denominator)
                            // (2*value.denominator), grid)
                   for value in gradient]
        squared_norm = sum((value*value for value in rounded), Fraction())
        if squared_norm <= Fraction(4, r**4):
            # The stated target must follow under the source hypotheses.
            raise FrameError("gradient stopped but exact leverage target failed")
        if iteration == limit:
            break
        step = Fraction(1, 2*(m+1))
        coordinates = [d - step*v for d, v in zip(coordinates, rounded)]
    raise FrameError("frame gradient iteration cap reached")


def find_balanced_frame_weights(n: int, edges: list[tuple[int, int]], q: int, r: int,
                                max_iterations: int = 200
                                ) -> tuple[list[Fraction], list[Fraction], int]:
    """Experimental coordinate balancing with the same exact leverage check.

    Parallel columns share a weight. Sherman--Morrison gives the weight
    multiplier taking their total leverage to count/q. Normalize and round
    positive weights to a fixed dyadic grid; verify all leverage scores again.
    The cap and final verification, rather than an all-input convergence
    theorem, define the scope of this optional practical method.
    """
    if n < 2 or q < 1 or r < q or len(edges) != q*(n-1) or max_iterations < 1:
        raise ValueError("invalid balanced-frame dimensions")
    groups: dict[tuple[int, int], list[int]] = {}
    for e, (u, v) in enumerate(edges):
        if not 0 <= u < v < n:
            raise ValueError("invalid frame edge")
        groups.setdefault((u, v), []).append(e)
    weights = [Fraction(1)]*len(edges)
    target = Fraction(1, q) + Fraction(4, r*q)
    grid = 1 << 48
    for iteration in range(max_iterations+1):
        scores = leverage_scores(n, edges, weights)
        worst = max(range(len(edges)), key=lambda e: scores[e])
        if scores[worst] <= target:
            return weights, scores, iteration
        if iteration == max_iterations:
            break
        ids = groups[edges[worst]]
        actual = sum((scores[e] for e in ids), Fraction())
        desired = Fraction(len(ids), q)
        if not 0 < desired < actual < 1:
            raise FrameError("parallel group cannot be balanced below unit leverage")
        factor = desired*(1-actual)/(actual*(1-desired))
        for e in ids:
            weights[e] *= factor
        largest = max(weights)
        normalized = [w*grid/largest for w in weights]
        weights = [Fraction(max(1, w.numerator//w.denominator), grid) for w in normalized]
    raise FrameError("balanced frame iteration cap reached")


def approximate_frame_columns(n: int, edges: list[tuple[int, int]],
                              weights: list[Fraction], bits: int
                              ) -> list[list[Fraction]]:
    """Approximate the single exact whitened frame to Euclidean error 2^-bits.

    Uses the rational LDL^T factorization N=L D L^T and computes the
    components sqrt(a_e/D_i)*(L^-1 c_e)_i by dyadic square-root bounds.
    Positive weights preserve all incidence subset ranks exactly.
    """
    if bits < 1 or n < 2 or len(edges) != len(weights) or any(a <= 0 for a in weights):
        raise ValueError("invalid frame approximation request")
    size = n - 1
    incidence = [_edge_vector(n, edge) for edge in edges]
    matrix = weighted_incidence_matrix(n, edges, weights)
    lower = [[Fraction(int(i == j)) for j in range(size)] for i in range(size)]
    diagonal = [Fraction() for _ in range(size)]
    for j in range(size):
        diagonal[j] = matrix[j][j] - sum(
            (lower[j][k]**2 * diagonal[k] for k in range(j)), Fraction())
        if diagonal[j] <= 0:
            raise ValueError("frame incidence columns do not span")
        for i in range(j+1, size):
            lower[i][j] = (matrix[i][j] - sum(
                (lower[i][k]*lower[j][k]*diagonal[k] for k in range(j)),
                Fraction())) / diagonal[j]
    solved = []
    max_numerator_bits = 1
    for column in incidence:
        t = []
        for i in range(size):
            t.append(Fraction(column[i]) - sum(
                (lower[i][j]*t[j] for j in range(i)), Fraction()))
            max_numerator_bits = max(max_numerator_bits, abs(t[-1].numerator).bit_length())
        solved.append(t)
    guard = bits + size.bit_length() + max_numerator_bits + 3
    scale = 1 << guard
    approximations = []
    for weight, t in zip(weights, solved):
        z = []
        for i in range(size):
            ratio = weight / diagonal[i]
            floor_root = isqrt((ratio.numerator * scale * scale) // ratio.denominator)
            z.append(t[i] * Fraction(floor_root, scale))
        approximations.append(z)
    return approximations
