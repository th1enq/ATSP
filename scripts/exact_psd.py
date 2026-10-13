"""Exact rational PSD test with a negative quadratic-form witness."""

from __future__ import annotations

from fractions import Fraction


def psd_or_negative_vector(matrix: list[list[Fraction]]) -> tuple[bool, list[Fraction] | None]:
    n = len(matrix)
    if any(len(row) != n for row in matrix):
        raise ValueError("matrix must be square")
    original = [[Fraction(x) for x in row] for row in matrix]
    if any(original[i][j] != original[j][i] for i in range(n) for j in range(i)):
        raise ValueError("matrix must be symmetric")
    reduced = [row[:] for row in original]
    basis = [[Fraction(int(i == j)) for i in range(n)] for j in range(n)]
    while reduced:
        size = len(reduced)
        for i in range(size):
            if reduced[i][i] < 0:
                return False, basis[i]
            if reduced[i][i] == 0:
                for j in range(size):
                    if reduced[i][j]:
                        t = -reduced[i][j] / (abs(reduced[j][j]) + 1)
                        witness = [basis[i][p] + t * basis[j][p] for p in range(n)]
                        return False, witness
        positive = next((i for i in range(size) if reduced[i][i] > 0), None)
        if positive is None:
            return True, None
        i = positive
        keep = [j for j in range(size) if j != i]
        pivot = reduced[i][i]
        new_basis = [[basis[j][p] - reduced[j][i] / pivot * basis[i][p]
                      for p in range(n)] for j in keep]
        reduced = [[reduced[j][k] - reduced[j][i] * reduced[i][k] / pivot
                    for k in keep] for j in keep]
        basis = new_basis
    return True, None


def quadratic_form(matrix: list[list[Fraction]], vector: list[Fraction]) -> Fraction:
    return sum((Fraction(matrix[i][j]) * vector[i] * vector[j]
                for i in range(len(vector)) for j in range(len(vector))), Fraction())


def rational_psd_columns(matrix: list[list[Fraction]]) -> list[list[Fraction]]:
    """Exact real rational rank-one decomposition from Lemma 5.1.

    Returns columns v with A=sum(v v^T), using at most three base-4 digit
    columns per bit-pair of each positive rational pivot. Input must be PSD.
    """
    good, _ = psd_or_negative_vector(matrix)
    if not good:
        raise ValueError("matrix is not positive semidefinite")
    n = len(matrix)
    remaining = list(range(n))
    reduced = [[Fraction(x) for x in row] for row in matrix]
    columns: list[list[Fraction]] = []
    while remaining:
        size = len(remaining)
        pivot = next((i for i in range(size) if reduced[i][i] > 0), None)
        if pivot is None:
            break
        if pivot:
            reduced[0], reduced[pivot] = reduced[pivot], reduced[0]
            for row in reduced:
                row[0], row[pivot] = row[pivot], row[0]
            remaining[0], remaining[pivot] = remaining[pivot], remaining[0]
        d = reduced[0][0]
        u = [Fraction() for _ in range(n)]
        u[remaining[0]] = 1
        for i in range(1, size):
            u[remaining[i]] = reduced[i][0] / d
        # d=a/b=(a*b)/b^2. Expand a*b in base 4 as a sum of squares.
        digits = d.numerator * d.denominator
        power = 1
        while digits:
            digits, count = divmod(digits, 4)
            column = [Fraction(power, d.denominator) * value for value in u]
            columns.extend([column.copy() for _ in range(count)])
            power *= 2
        reduced = [[reduced[i][j] - reduced[i][0]*reduced[0][j]/d
                    for j in range(1, size)] for i in range(1, size)]
        remaining.pop(0)
    return columns
