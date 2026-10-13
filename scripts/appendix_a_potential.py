"""Exact normalization and a certified rational value oracle for Appendix A."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from appendix_a_value_oracle import AppendixASDP
from exact_psd import psd_or_negative_vector


def cube_root_interval(value: Fraction, width: Fraction) -> tuple[Fraction, Fraction]:
    """Enclose the cube root of a rational in [0,1] with dyadic endpoints."""
    value, width = Fraction(value), Fraction(width)
    if not 0 <= value <= 1 or width <= 0:
        raise ValueError("invalid cube-root interval request")
    if value in (0, 1):
        return value, value
    scale = 1
    while Fraction(1, scale) > width:
        scale *= 2
    numerator = value.numerator*scale**3
    denominator = value.denominator
    lo, hi = 0, scale
    while lo < hi:
        mid = (lo + hi + 1)//2
        if mid**3*denominator <= numerator:
            lo = mid
        else:
            hi = mid - 1
    lower = Fraction(lo, scale)
    return lower, Fraction(lo+1, scale)


def spectral_norm_interval(matrix: list[list[Fraction]],
                           count: int) -> tuple[Fraction, Fraction]:
    d = len(matrix)
    identity = [[Fraction(int(i == j)) for j in range(d)] for i in range(d)]
    lo = Fraction(1, count*d*d)
    hi = Fraction(1)
    while hi > Fraction(10002, 10000)*lo:
        mid = (lo + hi)/2
        trial = [[mid*identity[i][j] - matrix[i][j] for j in range(d)]
                 for i in range(d)]
        if psd_or_negative_vector(trial)[0]:
            hi = mid
        else:
            lo = mid
    return lo, hi


def _sqrt_upper(value: Fraction, relative_denominator: int = 10000) -> Fraction:
    lo, hi = Fraction(), Fraction(1)
    while hi - lo > Fraction(1, relative_denominator)*lo:
        mid = (lo + hi)/2
        if mid*mid < value:
            lo = mid
        else:
            hi = mid
    return hi


@dataclass
class PotentialInterval:
    lower: Fraction
    upper: Fraction
    optimizer: list[Fraction]
    feasibility_calls: int


class AppendixAPotential:
    def __init__(self, hermitian: list[list[list[Fraction]]]):
        if not hermitian or not hermitian[0]:
            raise ValueError("nonempty matrices required")
        d = len(hermitian[0])
        if any(len(a) != d or any(len(row) != d for row in a) for a in hermitian):
            raise ValueError("matrix dimensions mismatch")
        matrices = [[[Fraction(v) for v in row] for row in a] for a in hermitian]
        if any(a[i][j] != a[j][i] for a in matrices for i in range(d) for j in range(d)):
            raise ValueError("real symmetric matrices required")
        traces = [sum((a[i][i] for i in range(d)), Fraction()) for a in matrices]
        for a, trace in zip(matrices, traces):
            signed = [[v*(1 if trace >= 0 else -1) for v in row] for row in a]
            if not psd_or_negative_vector(signed)[0]:
                raise ValueError("each matrix must be rank-one semidefinite")
            # A nonzero semidefinite matrix has rank one exactly when
            # Tr(A)^2 = Tr(A^2).
            tr_square = sum((a[i][j]*a[j][i] for i in range(d) for j in range(d)), Fraction())
            if tr_square != trace*trace:
                raise ValueError("each matrix must have rank at most one")
        nonzero = [k for k, tr in enumerate(traces) if tr]
        if not nonzero:
            raise ValueError("all matrices are zero; signs are arbitrary")
        self.original_count = len(matrices)
        self.original_indices = nonzero
        self.trace_signs = [1 if traces[k] > 0 else -1 for k in nonzero]
        self.d = d
        self.n = len(nonzero)
        self.normalizer = sum((abs(traces[k]) for k in nonzero), Fraction())
        self.a = [[[v*self.trace_signs[z]/self.normalizer for v in row]
                   for row in matrices[k]] for z, k in enumerate(nonzero)]
        square_sum = [[sum((sum((a[i][k]*a[k][j] for k in range(d)), Fraction())
                            for a in self.a), Fraction()) for j in range(d)] for i in range(d)]
        self.nu_lower, norm_upper = spectral_norm_interval(square_sum, self.n)
        root_upper = _sqrt_upper(norm_upper)
        self.epsilon = min(Fraction(1, d), root_upper/d)
        self.nu = (d*self.epsilon)**2
        self.lam = d*self.epsilon/(150*self.n)
        self.sigma = self.lam*self.lam/self.nu
        assert self.sigma == Fraction(1, 22500*self.n*self.n)

    def value_interval(self, x: list[Fraction], accuracy: Fraction,
                       max_feasibility_iterations: int | None = None) -> PotentialInterval:
        x = [Fraction(v) for v in x]
        accuracy = Fraction(accuracy)
        if len(x) != self.n or any(abs(v) > 1 for v in x) or not 0 < accuracy <= 1:
            raise ValueError("invalid potential query")
        error_coefficient = 384*100*self.d + self.lam*self.n
        width = accuracy/(8*error_coefficient)
        psi = []
        for value in x:
            lo, hi = cube_root_interval(1 - value*value, width)
            psi.append((lo + hi)/2)
        sdp = AppendixASDP(self.a, x, psi, self.epsilon)
        result = sdp.value_interval(accuracy/2,
                                   max_feasibility_iterations=max_feasibility_iterations)
        uncertainty = error_coefficient*width/2
        shift = self.lam*sum(psi, Fraction())
        return PotentialInterval(result.lower + shift - uncertainty,
                                 result.upper + shift + uncertainty,
                                 result.optimizer, result.feasibility_calls)

    def fold_signs(self, normalized_signs: list[int]) -> list[int]:
        if len(normalized_signs) != self.n or any(v not in (-1, 1) for v in normalized_signs):
            raise ValueError("invalid normalized signs")
        signs = [1]*self.original_count
        for z, k in enumerate(self.original_indices):
            signs[k] = self.trace_signs[z]*normalized_signs[z]
        return signs
