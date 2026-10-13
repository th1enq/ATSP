#!/usr/bin/env python3
"""Check integer inequalities used by the conditional threshold audit.

This checks arithmetic at the stated endpoints.  The monotonicity arguments
and dependencies on the manuscript's lemmas are documented separately in
docs/EXPLICIT_THRESHOLD_AUDIT.md.
"""

from __future__ import annotations

import json
from fractions import Fraction as F


def checked_constants() -> dict:
    h_exponent = 4096
    r_exponent = 4097
    t = h_exponent
    assert 12 <= F(t, 256)  # log2(t) <= t/256 at t=4096
    assert F(2 * t, 25) >= 28  # Lemma 2.4 smallness
    assert F(17 * t, 800) - F(84, 5) >= 18  # assignment strength
    assert F(1) - F(t, 40) <= -2  # first hierarchy loss <= 1/4
    assert F(68) - F(3 * t, 25) <= -2  # second hierarchy loss <= 1/4
    assert 17 + F(261 * t, 320) <= 2 * t  # L bound
    assert 36 + F(581 * t, 160) <= 4 * t  # H0 bound

    k_geometric = 384 * 36 * 102400 * 320000
    assert k_geometric < 2**49
    r_response = 2**53
    assert r_response**2 >= 96**3
    assert r_response**23 >= 576**120

    a = 12
    c_sign = 2**20
    b = a + 2 * c_sign + 6
    c_step = 6 * c_sign + 2 * b + 12 * c_sign * b
    r0 = 2**r_exponent
    assert r0 >= max((8 * a)**16, (16 * c_sign)**8, (2 * b)**16, 64)
    assert 64 * c_step < 2**256  # exponent in final product < 1/2
    return {
        "conditional_on_source_lemmas": True,
        "h0": "2^4096",
        "proposition_2_5_cutoff": "2^4097",
        "proposition_3_1_candidate_A": a,
        "proposition_3_1_candidate_r0": "2^4097",
        "signing_Cs": c_sign,
        "sparsification_candidate_C1": c_step,
        "sparsification_candidate_R0": "2^4097",
        "binary_thinness_constant_upper_bound": "12*2^4097",
    }


if __name__ == "__main__":
    print(json.dumps(checked_constants(), indent=2))
