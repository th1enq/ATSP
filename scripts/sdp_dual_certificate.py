"""Exact weak-duality certificates for affine rational LMIs.

For F_j(u)=C_j+sum_k u_k A_jk >= 0, PSD multipliers Z_j
with sum_j <Z_j,A_jk>=c_k prove c.u >= -sum_j <Z_j,C_j>.
No volume condition, floating-point optimization, or strong duality is used.
"""
from dataclasses import dataclass
from fractions import Fraction as F
from math import isqrt
from exact_psd import psd_or_negative_vector


@dataclass
class DualCertificate:
    multipliers: list[list[list[F]]]
    bound: F


def inner(a, b):
    return sum((a[i][j]*b[j][i] for i in range(len(a)) for j in range(len(a))
                if a[i][j] and b[j][i]), F())


def verify_dual(lmis, objective, certificate):
    if len(certificate.multipliers) != len(lmis):
        raise ValueError('wrong number of dual multipliers')
    coefficients = [F() for _ in objective]
    constant = F()
    for (matrix, bases), z in zip(lmis, certificate.multipliers):
        n = len(matrix)
        if len(z) != n or any(len(row) != n for row in z):
            raise ValueError('wrong dual matrix dimension')
        if not any(any(row) for row in z):
            continue
        if not psd_or_negative_vector(z)[0]:
            raise ValueError('dual multiplier is not PSD')
        constant += inner(z,matrix)
        for k, basis in enumerate(bases):
            coefficients[k] += inner(z,basis)
    if coefficients != objective:
        raise ValueError('dual stationarity fails')
    if certificate.bound != -constant:
        raise ValueError('altered dual bound')
    return certificate.bound


def sqrt_lower(value, bits):
    if value < 0 or bits < 1:
        raise ValueError('invalid square root request')
    scale = 1 << bits
    return F(isqrt((value.numerator*scale*scale)//value.denominator),scale)


def serialize_dual(certificate):
    return dict(bound=str(certificate.bound),
                multipliers=[[[str(v) for v in row] for row in z] for z in certificate.multipliers])


def load_dual(raw):
    return DualCertificate([[[F(v) for v in row] for row in z] for z in raw['multipliers']],F(raw['bound']))


def serialize_sdp_value(sdp, interval, accuracy):
    return dict(matrices=[[[str(v) for v in row] for row in a] for a in sdp.a],
        x=[str(v) for v in sdp.x],psi=[str(v) for v in sdp.psi],
        epsilon=str(sdp.epsilon),coupling=str(sdp.coupling),accuracy=str(accuracy),
        primal=[str(v) for v in interval.optimizer],lower=str(interval.lower),upper=str(interval.upper),
        dual=serialize_dual(interval.lower_certificate))


def verify_sdp_value(raw):
    from appendix_a_value_oracle import AppendixASDP
    sdp=AppendixASDP([[[F(v) for v in row] for row in a] for a in raw['matrices']],
                     [F(v) for v in raw['x']],[F(v) for v in raw['psi']],F(raw['epsilon']),F(raw['coupling']))
    low=verify_dual(sdp.lmis,sdp.objective,load_dual(raw['dual']))
    primal=[F(v) for v in raw['primal']]
    if sdp.separate(primal) is not None:
        raise ValueError('primal SDP witness is infeasible')
    high=sdp.objective_value(primal)
    accuracy=F(raw['accuracy'])
    if not 0<accuracy<=1 or not 0<=high-low<=accuracy:
        raise ValueError('primal-dual gap does not meet accuracy')
    if low!=F(raw['lower']) or high!=F(raw['upper']):
        raise ValueError('altered SDP interval endpoints')
    return dict(lower=str(low),upper=str(high),gap=str(high-low))
