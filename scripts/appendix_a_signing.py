"""Rational finite-difference descent from Appendix A.4.

The proof parameters are deliberately very loose. This is a bit-complexity
construction, not a practical matrix-signing routine for large instances.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from appendix_a_potential import AppendixAPotential
from exact_psd import psd_or_negative_vector


def _dyadic_below(bound: Fraction) -> Fraction:
    if bound <= 0:
        raise ValueError("positive bound required")
    power = Fraction(1)
    while power > bound:
        power /= 2
    while 2*power <= bound:
        power *= 2
    return power


def _sqrt_upper_relative(value: Fraction, beta: Fraction) -> Fraction:
    if value <= 0 or not 0 < beta < 1:
        raise ValueError("invalid square-root request")
    hi = Fraction(1)
    while hi*hi < value:
        hi *= 2
    lo = Fraction()
    while hi - lo > beta*lo:
        mid = (lo + hi)/2
        if mid*mid < value:
            lo = mid
        else:
            hi = mid
    return hi


def _nearest_grid(value: Fraction, grid: Fraction) -> Fraction:
    quotient = value/grid
    return ((2*quotient.numerator + quotient.denominator)//(2*quotient.denominator))*grid


@dataclass
class AppendixASigningResult:
    signs: list[int]
    spectral_bound_squared: Fraction
    steps: int
    value_calls: int


class AppendixASigner:
    def __init__(self, hermitian: list[list[list[Fraction]]], *,
                 max_feasibility_iterations: int | None = None,
                 max_value_queries: int | None = None):
        self.max_feasibility_iterations = max_feasibility_iterations
        self.max_value_queries = max_value_queries
        self._original = [[[Fraction(v) for v in row] for row in matrix]
                          for matrix in hermitian]
        self.potential = AppendixAPotential(hermitian)
        p = self.potential
        n, d, eps, sigma, lam = p.n, p.d, p.epsilon, p.sigma, p.lam
        k = 100
        j = 1 + Fraction(36*k*k*n*n)/eps
        e0 = 2*j*j*(1+3*n)**2
        c1 = max(Fraction(1), Fraction(48, 23)*e0, Fraction(4*(1+9*n*n)))
        self.c0 = 8*c1
        self.a = lam/(8*self.c0*self.c0)
        big_a = 10**18*(d+1)*(1+1/eps)**4
        big_d = 10**20*(n+1)**3*(d+1)**3*(1+1/eps)**3*(1+1/sigma)**3
        z1 = big_a*big_d
        z2 = big_a*big_d*(1+z1)**2
        z3 = big_a*big_d*(1+z1)**3 + 3*(1+z1)*z2
        self.m = 1 + (1+2*d*eps)*(z2+z3) + 800*lam*n/sigma**3
        self.s = _dyadic_below(min(sigma/4, self.a/(4*self.m), Fraction(1, 4)))
        self.h = _dyadic_below(min(sigma/8, Fraction(1), self.a/(64*self.m*n)))
        self.delta = self.a*self.s*self.s
        if p.lam*p.sigma/2 < 3*self.delta/2:
            raise AssertionError('endpoint decrease does not meet source descent bound')
        self.query_accuracy = self.a*self.h*self.h/(128*n)
        self.beta = self.a/(4096*self.m)
        self.tau = self.a/(1024*self.m)
        self.rho = _dyadic_below(self.s*self.a/(4096*self.m*n))
        self.value_calls = 0

    def _value(self, x: list[Fraction], accuracy: Fraction) -> Fraction:
        result = self._interval(x, accuracy)
        return (result.lower + result.upper)/2

    def _interval(self, x: list[Fraction], accuracy: Fraction):
        if self.max_value_queries is not None and self.value_calls >= self.max_value_queries:
            raise RuntimeError("Appendix A value query budget reached")
        self.value_calls += 1
        result = self.potential.value_interval(x, accuracy,
                        max_feasibility_iterations=self.max_feasibility_iterations)
        if result.upper - result.lower > accuracy:
            raise AssertionError("potential oracle missed requested accuracy")
        return result

    def _stencil(self, x: list[Fraction], active: list[int]
                 ) -> tuple[list[Fraction], list[list[Fraction]]]:
        h = self.h
        values = {}

        def at(offsets: tuple[tuple[int, int], ...]) -> Fraction:
            key = tuple(sorted(offsets))
            if key not in values:
                point = x.copy()
                for i, sign in key:
                    point[i] += sign*h
                values[key] = self._value(point, self.query_accuracy)
            return values[key]

        center = at(())
        gradient = []
        hessian = [[Fraction() for _ in active] for _ in active]
        for z, i in enumerate(active):
            plus, minus = at(((i, 1),)), at(((i, -1),))
            gradient.append((plus-minus)/(2*h))
            hessian[z][z] = (plus - 2*center + minus)/(h*h)
            for w in range(z):
                j = active[w]
                mixed = (at(((i, 1), (j, 1))) - at(((i, 1), (j, -1)))
                         - at(((i, -1), (j, 1))) + at(((i, -1), (j, -1))))/(4*h*h)
                hessian[z][w] = hessian[w][z] = mixed
        return gradient, hessian

    def _curvature_step(self, hessian: list[list[Fraction]]) -> list[Fraction] | None:
        n = len(hessian)
        shifted = [[hessian[i][j] + self.a*7*int(i == j)
                    for j in range(n)] for i in range(n)]
        good, witness = psd_or_negative_vector(shifted)
        if good:
            return None
        assert witness is not None
        squared = sum((v*v for v in witness), Fraction())
        scale = _sqrt_upper_relative(squared, self.beta)
        w = [v/scale for v in witness]
        q = [_nearest_grid(self.s*(1-self.tau)*v, self.rho) for v in w]
        if sum((v*v for v in q), Fraction()) > self.s*self.s:
            raise AssertionError("rounded curvature direction exceeds step size")
        return q

    def sign(self, max_steps: int | None = None) -> AppendixASigningResult:
        p = self.potential
        x = [Fraction() for _ in range(p.n)]
        steps = 0
        while True:
            for i in range(p.n):
                if abs(x[i]) < 1 and 1-abs(x[i]) <= p.sigma:
                    x[i] = Fraction(1 if x[i] >= 0 else -1)
            active = [i for i in range(p.n) if abs(x[i]) < 1]
            if not active:
                break
            if max_steps is not None and steps >= max_steps:
                raise RuntimeError("Appendix A step limit reached")

            # A cheap endpoint test catches large decreases. The second
            # precision is sufficient for the quantitative endpoint lemma.
            found_endpoint = False
            for coarse in (Fraction(1, 4), p.lam*p.sigma/16):
                base = self._interval(x, coarse)
                for i in active:
                    endpoints = []
                    for sign in (-1, 1):
                        candidate = x.copy()
                        candidate[i] = Fraction(sign)
                        interval = self._interval(candidate, coarse)
                        endpoints.append((interval.upper, candidate))
                    value, endpoint = min(endpoints, key=lambda item: item[0])
                    # The source needs a certified decrease, not a global
                    # minimizer among every remaining coordinate. Use the
                    # actual interval endpoints rather than the requested
                    # accuracy as an extra artificial error penalty.
                    if base.lower-value >= p.lam*p.sigma/2:
                        x = endpoint
                        steps += 1
                        found_endpoint = True
                        break
                if found_endpoint:
                    break
            if found_endpoint:
                continue

            gradient, hessian = self._stencil(x, active)
            candidates = []
            for i in active:
                for sign in (-1, 1):
                    candidate = x.copy()
                    candidate[i] = Fraction(sign)
                    candidates.append(candidate)
            z = max(range(len(active)), key=lambda j: abs(gradient[j]))
            direction = 1 if gradient[z] >= 0 else -1
            coordinate = x.copy()
            coordinate[active[z]] -= self.s*direction
            candidates.append(coordinate)
            q = self._curvature_step(hessian)
            if q is not None:
                for sign in (-1, 1):
                    candidate = x.copy()
                    for z, i in enumerate(active):
                        candidate[i] += sign*q[z]
                    candidates.append(candidate)
            base = self._value(x, self.delta/4)
            evaluated = [(self._value(candidate, self.delta/4), candidate)
                         for candidate in candidates]
            value, candidate = min(evaluated, key=lambda item: item[0])
            if base-value < self.delta:
                raise AssertionError("Appendix A descent certificate failed")
            x = candidate
            steps += 1

        signs = p.fold_signs([int(v) for v in x])
        # A lower bound on nu_0 makes this final certificate strictly
        # stronger than the stated 40 sqrt(||sum H_i^2||) threshold.
        bound_squared = 1600*p.normalizer*p.normalizer*p.nu_lower
        signed = [[sum((signs[z]*Fraction(matrix[i][j])
                        for z, matrix in enumerate(self._original)), Fraction())
                   for j in range(p.d)] for i in range(p.d)]
        square = [[sum((signed[i][k]*signed[k][j] for k in range(p.d)), Fraction())
                   for j in range(p.d)] for i in range(p.d)]
        certificate = [[bound_squared*int(i == j) - square[i][j]
                        for j in range(p.d)] for i in range(p.d)]
        if not psd_or_negative_vector(certificate)[0]:
            raise AssertionError("Appendix A final spectral certificate failed")
        return AppendixASigningResult(signs, bound_squared, steps, self.value_calls)
