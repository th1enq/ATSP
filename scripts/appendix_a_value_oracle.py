"""Rational SDP value oracle for the Appendix A signing potential.

The matrices A_i are rational PSD rank one with sum_i Tr(A_i)=1. At a rational
fractional signing x and rational budget coefficients psi_i in [0,1], this
solves the boxed Schur-complement SDP for R(x) to a requested additive gap.
This is one component of Appendix A, not the derivative-based descent.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from exact_psd import psd_or_negative_vector
from rational_ellipsoid import FeasibilityError, VolumeCutoffReached, find_feasible
from sdp_dual_certificate import DualCertificate, verify_dual
from sdp_collinear import collinear_proposal, generic_dual
from sdp_orthogonal import orthogonal_proposal


def _zero(size: int) -> list[list[Fraction]]:
    return [[Fraction() for _ in range(size)] for _ in range(size)]


@dataclass
class ValueInterval:
    lower: Fraction
    upper: Fraction
    optimizer: list[Fraction]
    feasibility_calls: int
    lower_certificate: DualCertificate | None = None
    newton_steps: int = 0


class UncertifiedSDPBound(FeasibilityError):
    """Volume/collapse alone did not certify an SDP lower endpoint."""


class AppendixASDP:
    def __init__(self, matrices: list[list[list[Fraction]]], x: list[Fraction],
                 psi: list[Fraction], epsilon: Fraction, coupling: int = 384):
        if not matrices or len(matrices) != len(x) or len(x) != len(psi):
            raise ValueError("invalid Appendix A dimensions")
        self.n = len(matrices[0])
        if self.n < 1 or any(len(a) != self.n or any(len(row) != self.n for row in a)
                             for a in matrices):
            raise ValueError("matrix dimensions mismatch")
        self.a = [[[Fraction(v) for v in row] for row in a] for a in matrices]
        self.x = [Fraction(v) for v in x]
        self.psi = [Fraction(v) for v in psi]
        self.epsilon = Fraction(epsilon)
        self.coupling = Fraction(coupling)
        if self.epsilon <= 0 or self.coupling < 0 or any(abs(v) > 1 for v in self.x) or any(not 0 <= v <= 1 for v in self.psi):
            raise ValueError("invalid Appendix A scalar parameters")
        if any(not psd_or_negative_vector(a)[0] for a in self.a):
            raise ValueError("input matrices must be PSD")
        for a in self.a:
            if any(a[i][j] != a[j][i] for i in range(self.n) for j in range(self.n)):
                raise ValueError("input matrices must be symmetric")
        if sum((a[i][i] for a in self.a for i in range(self.n)), Fraction()) != 1:
            raise ValueError("Appendix A matrices must have total trace one")
        self.keys = [("t", -1, -1)]
        self.keys += [("X", i, j) for i in range(self.n) for j in range(i, self.n)]
        self.keys += [("Y", i, j) for i in range(self.n) for j in range(i, self.n)]
        self.dimension = len(self.keys)
        self.objective = [Fraction(int(kind == "t") +
                                   int(kind in ("X", "Y") and i == j)*self.epsilon)
                          for kind, i, j in self.keys]
        self.identity = [[Fraction(int(i == j)) for j in range(self.n)]
                         for i in range(self.n)]
        self.s = [[sum((self.x[k]*self.a[k][i][j] for k in range(len(self.a))), Fraction())
                   for j in range(self.n)] for i in range(self.n)]
        grouped = {}
        for a, weight in zip(self.a,self.psi):
            key = tuple(tuple(row) for row in a)
            grouped[key] = grouped.get(key,Fraction())+weight
        self._coupling_terms = []
        for key,weight in grouped.items():
            if not weight:
                continue
            a = [list(row) for row in key]
            trace = sum((a[i][i] for i in range(self.n)),Fraction())
            rank_one = trace*trace == sum((v*v for row in a for v in row),Fraction())
            self._coupling_terms.append((a,weight,rank_one))
        self._build_affine_lmis()
        # Compile symmetric affine entries once. The block LMIs have many
        # zeros; evaluating every zero coefficient repeatedly costs gcds.
        self.sparse_lmis = []
        for constant, coefficients in self.lmis:
            entries = [(i, j, constant[i][j],
                        [(k, c[i][j]) for k,c in enumerate(coefficients) if c[i][j]])
                       for i in range(len(constant)) for j in range(i, len(constant))]
            self.sparse_lmis.append((len(constant), entries))

    def _basis(self, i: int, j: int) -> list[list[Fraction]]:
        e = _zero(self.n)
        e[i][j] = 1
        e[j][i] = 1
        return e

    def _coupling_on_basis(self, basis: list[list[Fraction]]) -> list[list[Fraction]]:
        n = self.n
        result = _zero(n)
        entries = [(u,v,basis[u][v]) for u in range(n) for v in range(n) if basis[u][v]]
        for a, weight, rank_one in self._coupling_terms:
            if rank_one:
                # A B A = Tr(A B) A for rank-one symmetric A.
                factor = self.coupling*weight*sum((a[v][u]*b for u,v,b in entries),Fraction())
                for i in range(n):
                    for j in range(n):
                        if a[i][j]:
                            result[i][j] += factor*a[i][j]
                continue
            for i in range(n):
                for j in range(n):
                    result[i][j] += self.coupling*weight*sum(
                        (a[i][u]*b*a[v][j] for u,v,b in entries
                         if a[i][u] and a[v][j]), Fraction())
        return result

    def _block(self, top: list[list[Fraction]], bottom: list[list[Fraction]],
               off_identity: bool = False) -> list[list[Fraction]]:
        n = self.n
        out = _zero(2*n)
        for i in range(n):
            for j in range(n):
                out[i][j] = top[i][j]
                out[n+i][n+j] = bottom[i][j]
                if off_identity:
                    out[i][n+j] = out[n+j][i] = Fraction(int(i == j))
        return out

    def _build_affine_lmis(self) -> None:
        n = self.n
        first_constant = self._block([[-self.s[i][j] for j in range(n)]
                                      for i in range(n)], _zero(n), True)
        second_constant = self._block(self.s, _zero(n), True)
        first_coeff = []
        second_coeff = []
        for kind, i, j in self.keys:
            if kind == "t":
                first_coeff.append(self._block(self.identity, _zero(n)))
                second_coeff.append(self._block(self.identity, _zero(n)))
            else:
                basis = self._basis(i, j)
                coupled = self._coupling_on_basis(basis)
                negative = [[-v for v in row] for row in coupled]
                first_coeff.append(self._block(_zero(n), basis) if kind == "X"
                                   else self._block(negative, _zero(n)))
                second_coeff.append(self._block(negative, _zero(n)) if kind == "X"
                                    else self._block(_zero(n), basis))
        self.lmis = [(first_constant, first_coeff),
                     (second_constant, second_coeff)]
        upper = Fraction(200) / self.epsilon
        for kind in ("X", "Y"):
            lower_constant = [[-Fraction(int(i == j), 400) for j in range(n)]
                              for i in range(n)]
            upper_constant = [[upper*int(i == j) for j in range(n)]
                              for i in range(n)]
            lower_coeff = []
            upper_coeff = []
            for key_kind, i, j in self.keys:
                basis = self._basis(i, j) if key_kind == kind else _zero(n)
                lower_coeff.append(basis)
                upper_coeff.append([[-v for v in row] for row in basis])
            self.lmis += [(lower_constant, lower_coeff),
                          (upper_constant, upper_coeff)]

    def objective_value(self, point: list[Fraction]) -> Fraction:
        if len(point) != self.dimension:
            raise ValueError("wrong SDP point dimension")
        return sum((a*b for a, b in zip(self.objective, point)), Fraction())

    def separate(self, point: list[Fraction], target: Fraction | None = None
                 ) -> tuple[Fraction, list[Fraction]] | None:
        if len(point) != self.dimension:
            raise ValueError("wrong SDP point dimension")
        point = [Fraction(v) for v in point]
        t = point[0]
        if t < 0:
            return Fraction(), [Fraction(int(i == 0)) for i in range(self.dimension)]
        if t > 100:
            return Fraction(100), [Fraction(-int(i == 0)) for i in range(self.dimension)]
        for size, entries in self.sparse_lmis:
            matrix = _zero(size)
            for i, j, constant, coefficients in entries:
                value = constant + sum((point[k]*a for k,a in coefficients if point[k]), Fraction())
                matrix[i][j] = matrix[j][i] = value
            good, witness = psd_or_negative_vector(matrix)
            if not good:
                assert witness is not None
                cut_constant = Fraction()
                cut_coefficients = [Fraction() for _ in range(self.dimension)]
                for i, j, constant, coefficients in entries:
                    if not witness[i] or not witness[j]:
                        continue
                    factor = witness[i]*witness[j]*(1 if i == j else 2)
                    if constant:
                        cut_constant += constant*factor
                    for k,a in coefficients:
                        cut_coefficients[k] += a*factor
                cut = cut_constant, cut_coefficients
                assert cut[0] + sum((v*c for v, c in zip(point, cut[1])), Fraction()) < 0
                return cut
        if target is not None and self.objective_value(point) > target:
            return Fraction(target), [-v for v in self.objective]
        return None

    def strict_reference_point(self) -> list[Fraction]:
        point = []
        for kind, i, j in self.keys:
            point.append(Fraction(50) if kind == "t" else
                         Fraction(int(i == j), 20))
        if self.separate(point) is not None:
            raise ValueError("normalization promise fails at strict SDP reference point")
        return point

    def value_interval(self, accuracy: Fraction,
                       max_feasibility_iterations: int | None = None) -> ValueInterval:
        """Weak optimization; upper endpoint has an exactly feasible witness."""
        accuracy = Fraction(accuracy)
        if not 0 < accuracy <= 1:
            raise ValueError("accuracy must be in (0,1]")
        best = self.strict_reference_point()
        bits = max(80, accuracy.denominator.bit_length()+64)
        certificate = generic_dual(self,bits)
        proposal = collinear_proposal(self,bits)
        if proposal is None:
            proposal = orthogonal_proposal(self,bits)
        if proposal is None:
            from sdp_barrier import barrier_proposal
            try:
                candidate, candidate_certificate, iterations = barrier_proposal(
                    self, accuracy, max_feasibility_iterations)
            except ArithmeticError as exc:
                raise FeasibilityError('noncommuting SDP numerical proposal failed; no infeasibility claim') from exc
            return ValueInterval(candidate_certificate.bound, self.objective_value(candidate),
                                 candidate, 0, candidate_certificate, iterations)
        if proposal is not None:
            candidate, candidate_certificate = proposal
            if self.objective_value(candidate) < self.objective_value(best):
                best = candidate
            if candidate_certificate is not None and candidate_certificate.bound > certificate.bound:
                certificate = candidate_certificate
        low, high = verify_dual(self.lmis,self.objective,certificate), self.objective_value(best)
        if low > high:
            raise AssertionError('dual lower bound exceeds primal upper bound')
        if high > 100:
            raise ValueError("strict reference objective exceeds the box")
        calls = 0
        # A threshold >= optimum + accuracy/8 has a ball of radius
        # accuracy/10^10 by mixing an optimizer with the strict reference.
        inner_radius = accuracy / 10**10
        outer_radius = Fraction(400*(self.n+1)) / self.epsilon
        while high - low > accuracy:
            target = (low + high)/2
            try:
                candidate, _ = find_feasible(
                    self.dimension,
                    lambda point: self.separate(point, target),
                    outer_radius, inner_radius,
                    max_iterations=max_feasibility_iterations)
            except VolumeCutoffReached as exc:
                # No independently checked ball promise is available here.
                # A collapsed ellipsoid is not an exact dual witness.
                raise UncertifiedSDPBound('volume/collapse has no verified dual lower bound') from exc
            else:
                if self.separate(candidate) is not None:
                    raise AssertionError("weak SDP oracle returned an infeasible point")
                best = candidate
                high = self.objective_value(candidate)
            calls += 1
            if calls > 4*(high.numerator.bit_length() + accuracy.denominator.bit_length() + 10):
                raise FeasibilityError("weak SDP bisection did not converge")
        return ValueInterval(low, high, best, calls, certificate)
