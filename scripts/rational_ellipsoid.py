"""Rational central-cut ellipsoid feasibility with bounded dyadic encodings.

The caller promises a feasible ball of radius ``inner_radius`` inside the
convex set and an enclosing origin-centered ball of radius ``outer_radius``.
Every returned point is checked by the caller's exact separating oracle.
All iterates are dyadic and all cuts are rational. The exact central-cut
ellipsoid is enlarged after rounding, preserving containment of the set.
"""

from __future__ import annotations

from fractions import Fraction
from math import isqrt
from typing import Callable


class FeasibilityError(RuntimeError):
    pass


class IterationLimitReached(FeasibilityError):
    """An operational cap, without any mathematical volume conclusion."""


class VolumeCutoffReached(FeasibilityError):
    """The source's volume/inner-ball stopping condition was reached."""


def _dyadic_round(x: Fraction, scale: int) -> Fraction:
    numerator = x.numerator * scale
    return Fraction((2*numerator + x.denominator) // (2*x.denominator), scale)


def _sqrt_upper(q: Fraction, dimension: int) -> Fraction:
    """Upper dyadic square root with relative error <= 1/(100*dimension)."""
    scale = 1
    while True:
        h = isqrt((q.numerator * scale * scale) // q.denominator)
        if h >= 100 * dimension:
            return Fraction(h + 1, scale)
        scale *= 2


def find_feasible(
    dimension: int,
    separate: Callable[[list[Fraction]], tuple[Fraction, list[Fraction]] | None],
    outer_radius: Fraction,
    inner_radius: Fraction,
    max_iterations: int | None = None,
) -> tuple[list[Fraction], int]:
    """Return (exactly accepted dyadic point, number of separating cuts).

    A cut is (constant, coefficients) for ``constant + a*x >= 0``.
    Failure at the polynomial volume cutoff means an oracle/ball-promise
    error; it is never interpreted as proof of infeasibility.
    """
    d = dimension
    radius = Fraction(outer_radius)
    rho = Fraction(inner_radius)
    if d < 2 or radius <= rho or rho <= 0 or rho > 1:
        raise ValueError("invalid ellipsoid dimensions or radii")
    epsilon = Fraction(1, 100*d*d)
    grid_limit = epsilon * rho * rho / d
    scale = 1
    while Fraction(1, scale) > grid_limit:
        scale *= 2
    ratio = radius / rho
    log2_ratio = ratio.numerator.bit_length() + ratio.denominator.bit_length()
    volume_limit = 8*d*(d+1)*(log2_ratio+1)
    if max_iterations is not None and max_iterations < 0:
        raise ValueError("invalid iteration limit")
    limit = min(volume_limit, max_iterations) if max_iterations is not None else volume_limit

    center = [Fraction() for _ in range(d)]
    shape = [[radius*radius if i == j else Fraction() for j in range(d)]
             for i in range(d)]
    rank_factor = Fraction(2, d+1)
    inflated_shape_factor = Fraction(d*d, d*d-1)*(1+10*epsilon)
    for iteration in range(limit + 1):
        violation = separate(center)
        if violation is None:
            return center, iteration
        if iteration == limit:
            break
        constant, coefficients = violation
        coefficients = [Fraction(x) for x in coefficients]
        if len(coefficients) != d or constant + sum(
            (x*y for x, y in zip(coefficients, center)), Fraction()) >= 0:
            raise FeasibilityError("separator did not return a violated affine cut")
        # Feasible points satisfy (-a)*x <= constant. Cut centrally through c.
        normal = [-x for x in coefficients]
        active = [j for j,v in enumerate(normal) if v]
        a = [sum((shape[i][j]*normal[j] for j in active), Fraction())
             for i in range(d)]
        q = sum((normal[i]*a[i] for i in range(d)), Fraction())
        if q <= 0:
            # Without the promised feasible ball, successive central cuts may
            # collapse the rounded shape before the iteration cutoff. Under
            # the promise q must be positive, so this is another cutoff case.
            raise VolumeCutoffReached("volume cutoff reached: ellipsoid collapsed")
        sqrt_hi = _sqrt_upper(q, d)
        translated = [center[i] - a[i] / ((d+1)*sqrt_hi) for i in range(d)]
        rank_left = [rank_factor*v/q for v in a]
        # The ideal central-cut ellipsoid contains the feasible set. Its
        # minimum shape eigenvalue is >= rho^2 because it contains the promised
        # radius-rho ball. Both center errors have ideal-Mahalanobis norm <= eps.
        # Entrywise shape rounding has operator error <= eps*rho^2 <= eps*ideal.
        center = [_dyadic_round(x, scale) for x in translated]
        next_shape = [[Fraction() for _ in range(d)] for _ in range(d)]
        for i in range(d):
            for j in range(i, d):
                entry = _dyadic_round(inflated_shape_factor *
                                     (shape[i][j]-rank_left[i]*a[j]), scale)
                next_shape[i][j] = next_shape[j][i] = entry
        shape = next_shape
    if limit < volume_limit:
        raise IterationLimitReached("ellipsoid iteration budget reached; no volume conclusion")
    raise VolumeCutoffReached("volume cutoff reached: inner-ball promise or oracle failed")
