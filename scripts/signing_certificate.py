"""Exact rational certificate checker for a supplied rank-one signing.

This module checks a proposed signing without floats. The separate
appendix_a_signing module implements the deterministic search procedure.
"""

from __future__ import annotations

from fractions import Fraction

from exact_psd import psd_or_negative_vector


def check_signing(columns: list[list[Fraction]], signs: list[int],
                  bound: Fraction, require_identity: bool = True) -> bool:
    if len(columns) != len(signs) or bound < 0 or any(s not in (-1, 1) for s in signs):
        raise ValueError("invalid signs or discrepancy bound")
    dimension = len(columns[0]) if columns else 0
    if any(len(column) != dimension for column in columns):
        raise ValueError("inconsistent column dimensions")
    unsigned = [[sum((Fraction(v[i])*v[j] for v in columns), Fraction())
                 for j in range(dimension)] for i in range(dimension)]
    if require_identity and any(unsigned[i][j] != int(i == j)
                                for i in range(dimension) for j in range(dimension)):
        raise ValueError("columns do not sum to identity")
    signed = [[sum((signs[e]*Fraction(v[i])*v[j] for e, v in enumerate(columns)), Fraction())
               for j in range(dimension)] for i in range(dimension)]
    for direction in (-1, 1):
        matrix = [[bound*int(i == j) + direction*signed[i][j]
                   for j in range(dimension)] for i in range(dimension)]
        if not psd_or_negative_vector(matrix)[0]:
            return False
    return True
