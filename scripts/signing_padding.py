"""Exact identity completion from Lemma 5.2, equations (5.5)--(5.7).

Input data columns must have rational covariance <= I. Padding returns an
exact rational identity decomposition in a larger dimension, used by the
Frobenius and Appendix A signing backends.
"""

from __future__ import annotations

from fractions import Fraction
from math import isqrt

from continuation_oracle import _edge_vector
from continuation_state import ContinuationState
from exact_psd import psd_or_negative_vector, rational_psd_columns
from rational_frame import approximate_frame_columns


def prepare_stacked_columns(state: ContinuationState, edge_ids: list[int],
                            frame_weights: list[Fraction], bits: int
                            ) -> list[list[Fraction]]:
    """Approximate (X^-1/2 b_e, z_e)/2 in rational orthogonal coordinates."""
    if bits < 1 or len(edge_ids) != len(frame_weights) or not edge_ids:
        raise ValueError("invalid stacked frame request")
    n = state.n
    edges = [state.edges[e] for e in edge_ids]
    size = n - 1
    matrix = state.x
    lower = [[Fraction(int(i == j)) for j in range(size)] for i in range(size)]
    diagonal = [Fraction() for _ in range(size)]
    for j in range(size):
        diagonal[j] = matrix[j][j] - sum(
            (lower[j][k]**2 * diagonal[k] for k in range(j)), Fraction())
        if diagonal[j] <= 0:
            raise ValueError("shortcut matrix is not positive definite")
        for i in range(j+1, size):
            lower[i][j] = (matrix[i][j] - sum(
                (lower[i][k]*lower[j][k]*diagonal[k] for k in range(j)),
                Fraction())) / diagonal[j]
    solved = []
    numerator_bits = 1
    for edge in edges:
        column = _edge_vector(n, edge)
        t = []
        for i in range(size):
            t.append(Fraction(column[i]) - sum(
                (lower[i][j]*t[j] for j in range(i)), Fraction()))
            numerator_bits = max(numerator_bits, abs(t[-1].numerator).bit_length())
        solved.append(t)
    guard = bits + size.bit_length() + numerator_bits + 3
    scale = 1 << guard
    first_block = []
    for t in solved:
        column = []
        for i in range(size):
            ratio = 1 / diagonal[i]
            floor_root = isqrt((ratio.numerator * scale * scale) // ratio.denominator)
            column.append(t[i] * Fraction(floor_root, scale))
        first_block.append(column)
    second_block = approximate_frame_columns(n, edges, frame_weights, bits)
    data = [[x/2 for x in first+second]
            for first, second in zip(first_block, second_block)]
    dimension = 2*size
    residual = [[Fraction(int(i == j)) - sum((v[i]*v[j] for v in data), Fraction())
                 for j in range(dimension)] for i in range(dimension)]
    if not psd_or_negative_vector(residual)[0]:
        raise ValueError("rounded stacked data exceeds identity")
    return data


def pad_to_identity(data_columns: list[list[Fraction]], r: int
                    ) -> tuple[list[list[Fraction]], int]:
    if r < 1 or not data_columns:
        raise ValueError("invalid padding input")
    dimension = len(data_columns[0])
    if dimension < 1 or any(len(column) != dimension for column in data_columns):
        raise ValueError("inconsistent data column dimensions")
    data = [[Fraction(x) for x in column] for column in data_columns]
    residual = [[Fraction(int(i == j)) - sum((v[i]*v[j] for v in data), Fraction())
                 for j in range(dimension)] for i in range(dimension)]
    if not psd_or_negative_vector(residual)[0]:
        raise ValueError("data covariance exceeds identity")
    residual_columns = rational_psd_columns(residual)
    if any(sum((v[i]*v[j] for v in residual_columns), Fraction()) != residual[i][j]
           for i in range(dimension) for j in range(dimension)):
        raise AssertionError("residual factorization failed")
    extra = len(residual_columns)
    extended = [column + [Fraction()]*extra for column in data]
    copies = (2*r)**2
    for j, column in enumerate(residual_columns):
        for k in range(copies):
            padded = [x/(2*r) for x in column] + [Fraction()]*extra
            padded[dimension+j] = Fraction(1 if k < copies//2 else -1, 2*r)
            extended.append(padded)
    # The checked residual sum supplies the upper block. Each extra diagonal
    # has copies*(1/(2r))^2=1, and half of the fixed tau signs are positive,
    # so all off-diagonal blocks vanish exactly.
    return extended, len(data)
