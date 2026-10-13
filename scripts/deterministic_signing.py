"""Deterministic exact Frobenius signing with a spectral success certificate.

This is a polynomial-time signing subroutine for the instances where its
Frobenius bound implies Lemma 5.2's checked threshold. It is not the general
Appendix A algorithm: if its exact PSD test fails, it raises instead of
claiming the theorem's all-dimension guarantee.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from exact_psd import psd_or_negative_vector, rational_psd_columns
from signing_certificate import check_signing


class SigningGuaranteeUnavailable(RuntimeError):
    pass


@dataclass
class SigningResult:
    signs: list[int]
    spectral_bound: Fraction
    max_squared_norm: Fraction
    frobenius_budget: Fraction
    frobenius_guaranteed: bool


def _dyadic_sqrt_upper(value: Fraction) -> Fraction:
    if value <= 0:
        raise ValueError("positive squared norm required")
    bound = Fraction(1)
    if bound*bound < value:
        while bound*bound < value:
            bound *= 2
    else:
        while (bound/2)**2 >= value:
            bound /= 2
    return bound


def sign_by_frobenius(columns: list[list[Fraction]],
                      require_identity: bool = True,
                      spectral_bound: Fraction | None = None) -> SigningResult:
    if not columns or not columns[0]:
        raise ValueError("nonempty rational columns required")
    dimension = len(columns[0])
    if any(len(v) != dimension for v in columns):
        raise ValueError("inconsistent column dimensions")
    columns = [[Fraction(x) for x in v] for v in columns]
    norms = [sum((x*x for x in v), Fraction()) for v in columns]
    delta = max(norms)
    if delta <= 0:
        raise ValueError("zero columns cannot form the identity")
    budget = sum((norm*norm for norm in norms), Fraction())
    d0 = _dyadic_sqrt_upper(delta)
    threshold = Fraction(spectral_bound) if spectral_bound is not None else (1 << 15)*d0
    signed = [[Fraction() for _ in range(dimension)] for _ in range(dimension)]
    signs = []
    for vector in columns:
        inner = sum((vector[i]*signed[i][j]*vector[j]
                     for i in range(dimension) for j in range(dimension)), Fraction())
        sign = -1 if inner > 0 else 1
        signs.append(sign)
        for i in range(dimension):
            for j in range(dimension):
                signed[i][j] += sign*vector[i]*vector[j]
    # The exact descent calculation already proves ||S||_op^2<=budget.
    # For non-identity data this scalar certificate avoids repeating two
    # expensive dense PSD tests when the bound is sufficient.
    certified = ((not require_identity and budget <= threshold*threshold)
                 or check_signing(columns, signs, threshold, require_identity=require_identity))
    if not certified:
        raise SigningGuaranteeUnavailable(
            "Frobenius signing missed the spectral threshold; Appendix A search is required")
    return SigningResult(signs, threshold, delta, budget,
                         budget <= threshold*threshold)


def sign_stacked_data(data_columns: list[list[Fraction]], r: int,
                      materialize_padding: bool = True,
                      ) -> tuple[SigningResult, int]:
    """Sign data; pair padding signs so their entire signed sum is zero.

    The rational residual is factored exactly. For each residual vector,
    padding copies have tau=+1 on the first half and -1 on the second.
    Alternating signs within each even-sized half give both sum sigma=0 and
    sum sigma*tau=0. Thus the padded signed matrix equals the data signed
    matrix in its upper block and zero elsewhere, without materializing the
    O(r^2) copies. Returns the data result and number of residual columns.
    """
    if r < 1 or not data_columns or not data_columns[0]:
        raise ValueError("invalid stacked data")
    dimension = len(data_columns[0])
    data = [[Fraction(x) for x in column] for column in data_columns]
    if any(len(v) != dimension for v in data):
        raise ValueError("inconsistent stacked columns")
    residual = [[Fraction(int(i == j)) - sum((v[i]*v[j] for v in data), Fraction())
                 for j in range(dimension)] for i in range(dimension)]
    if not psd_or_negative_vector(residual)[0]:
        raise ValueError("data covariance exceeds identity")
    if not materialize_padding:
        # Any rank-one PSD decomposition has each squared column norm <=
        # tr(residual). The paired padding signs cancel irrespective of the
        # decomposition. This certified upper bound avoids expanding it.
        data_delta = max(sum((x*x for x in v), Fraction()) for v in data)
        padding_delta = (1 + sum((residual[i][i] for i in range(dimension)), Fraction()))/(4*r*r)
        delta_bound = max(data_delta, padding_delta)
        threshold = (1 << 15)*_dyadic_sqrt_upper(delta_bound)
        result = sign_by_frobenius(data, require_identity=False, spectral_bound=threshold)
        result.max_squared_norm = delta_bound
        return result, 0  # residual columns are represented implicitly
    residual_columns = rational_psd_columns(residual)
    if any(sum((v[i]*v[j] for v in residual_columns), Fraction()) != residual[i][j]
           for i in range(dimension) for j in range(dimension)):
        raise AssertionError("residual factorization failed")
    data_delta = max(sum((x*x for x in v), Fraction()) for v in data)
    padding_delta = max(((1 + sum((x*x for x in v), Fraction())) / (4*r*r)
                         for v in residual_columns), default=Fraction())
    delta = max(data_delta, padding_delta)
    threshold = (1 << 15)*_dyadic_sqrt_upper(delta)
    result = sign_by_frobenius(data, require_identity=False,
                               spectral_bound=threshold)
    result.max_squared_norm = delta
    return result, len(residual_columns)


def sign_stacked_data_appendix_a(data_columns: list[list[Fraction]], r: int,
                                 max_steps: int | None = None,
                                 max_feasibility_iterations: int | None = None,
                                 max_value_queries: int | None = None,
                                 ) -> tuple[SigningResult, int]:
    """Use Appendix A.4 for the data columns and cancel structured padding."""
    from appendix_a_signing import AppendixASigner

    if r < 1 or not data_columns or not data_columns[0]:
        raise ValueError("invalid stacked data")
    data = [[Fraction(x) for x in column] for column in data_columns]
    dimension = len(data[0])
    if any(len(v) != dimension for v in data):
        raise ValueError("inconsistent stacked columns")
    residual = [[Fraction(int(i == j)) - sum((v[i]*v[j] for v in data), Fraction())
                 for j in range(dimension)] for i in range(dimension)]
    if not psd_or_negative_vector(residual)[0]:
        raise ValueError("data covariance exceeds identity")
    residual_columns = rational_psd_columns(residual)
    norms = [sum((x*x for x in v), Fraction()) for v in data]
    padding_delta = max(((1 + sum((x*x for x in v), Fraction()))/(4*r*r)
                         for v in residual_columns), default=Fraction())
    delta = max(max(norms), padding_delta)
    threshold = (1 << 15)*_dyadic_sqrt_upper(delta)
    matrices = [[[v[i]*v[j] for j in range(dimension)] for i in range(dimension)]
                for v in data]
    if all(not any(vector) for vector in data):
        signs = [1]*len(data)
    else:
        signs = AppendixASigner(matrices,
                    max_feasibility_iterations=max_feasibility_iterations,
                    max_value_queries=max_value_queries).sign(max_steps=max_steps).signs
    if not check_signing(data, signs, threshold, require_identity=False):
        raise AssertionError("Appendix A signs failed the stacked-data certificate")
    budget = sum((v*v for v in norms), Fraction())
    return SigningResult(signs, threshold, delta, budget,
                         budget <= threshold*threshold), len(residual_columns)


def sign_stacked_data_candidate(data_columns, r, signs):
    """Check a proposed signing, with paired padding represented implicitly.

    This is an instance certificate, not Appendix A descent. Failure is
    explicit; there is no existence or convergence claim for the proposal.
    """
    if r < 1 or len(signs) != len(data_columns) or any(s not in (-1,1) for s in signs):
        raise ValueError('invalid signing candidate')
    d = len(data_columns[0])
    residual = [[Fraction(int(i==j))-sum((v[i]*v[j] for v in data_columns),Fraction())
                 for j in range(d)] for i in range(d)]
    if not psd_or_negative_vector(residual)[0]:
        raise ValueError('candidate data covariance exceeds identity')
    # The residual padding construction has squared column norm <= 1/(2r²).
    delta = max(max(sum((x*x for x in v),Fraction()) for v in data_columns), Fraction(1,2*r*r))
    threshold = (1 << 15)*_dyadic_sqrt_upper(delta)
    if not check_signing(data_columns,signs,threshold,require_identity=False):
        raise SigningGuaranteeUnavailable('candidate failed exact stacked signing certificate')
    return SigningResult(list(signs),threshold,delta,Fraction(),False), 0
