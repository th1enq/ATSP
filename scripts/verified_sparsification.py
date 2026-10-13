"""Certificate checker and packing update for Lemma 6.1.

Generate a retained subset by rational signing and verify its matrix and
packing certificates. Small experimental runs may tighten the error by
exact PSD tests, without assuming the source paper's large-r bounds.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction

from continuation_oracle import _edge_vector, _laplacian
from continuation_solver import dyadic_g
from continuation_state import ContinuationState
from deterministic_signing import (SigningResult, sign_stacked_data,
                                   sign_stacked_data_appendix_a, sign_stacked_data_candidate)
from exact_psd import psd_or_negative_vector
from rational_frame import find_balanced_frame_weights, find_frame_weights
from signing_padding import prepare_stacked_columns
from tree_packing import pack_forests, verify_trees


@dataclass
class SparsificationCertificate:
    selected_edges: list[int]
    packed_trees: list[list[int]]
    r_next: int
    cut_load_factor: Fraction


@dataclass
class AutomaticStep:
    certificate: SparsificationCertificate
    signing: SigningResult
    frame_iterations: int
    residual_columns: int
    edge_ids: list[int]
    frame_weights: list[Fraction]
    epsilon: Fraction


def _edge_laplacian(n: int, edges: list[tuple[int, int]], ids: list[int]
                    ) -> list[list[Fraction]]:
    return _laplacian(n, [edges[e] for e in ids])


def _is_psd(matrix: list[list[Fraction]]) -> bool:
    return psd_or_negative_vector(matrix)[0]


def verify_shortcut_cone(state: ContinuationState) -> bool:
    n = state.n
    lap = _laplacian(n, state.edges)
    if not _is_psd([[state.x[i][j] - lap[i][j] for j in range(n-1)]
                    for i in range(n-1)]):
        return False
    remainder = [[3*lap[i][j] - state.x[i][j] for j in range(n-1)]
                 for i in range(n-1)]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if i == j or j == k or i == k:
                    continue
                lam = state.cone_lambda.get(f"lambda:{i}:{j}:{k}", Fraction())
                if lam < 0:
                    return False
                if not lam:
                    continue
                bij, bjk, bik = (_edge_vector(n, tuple(sorted(pair)))
                                 for pair in ((i, j), (j, k), (i, k)))
                for a in range(n-1):
                    for b in range(n-1):
                        remainder[a][b] -= lam*(bij[a]*bij[b] + bjk[a]*bjk[b]
                                                 - bik[a]*bik[b])
    return _is_psd(remainder)


def verify_sparsification(state: ContinuationState, union_trees: list[list[int]],
                          selected_edges: list[int], epsilon: Fraction,
                          packed_trees: list[list[int]] | None = None,
                          ) -> SparsificationCertificate:
    n, r = state.n, state.r
    epsilon = Fraction(epsilon)
    if epsilon < 0 or state.s**4 < r or not state.verify_invariant() or not verify_shortcut_cone(state):
        raise ValueError("invalid terminal shortcut certificate")
    if not (r <= 2*len(union_trees) and len(union_trees) <= r):
        raise ValueError("wrong number of shortcut trees")
    full_edges = [(u, v, e) for e, (u, v) in enumerate(state.edges)]
    verify_trees(n, full_edges, union_trees)
    b_ids = sorted(e for tree in union_trees for e in tree)
    ramp = state.ramp()
    if any(ramp[e] <= 0 for e in b_ids):
        raise ValueError("shortcut tree uses a high-resistance edge")
    if len(set(selected_edges)) != len(selected_edges) or set(selected_edges) - set(b_ids):
        raise ValueError("selected set is not a subset of the tree union")
    selected = sorted(selected_edges)
    lb = _edge_laplacian(n, state.edges, b_ids)
    la = _edge_laplacian(n, state.edges, selected)
    matrix = [[Fraction(1, 2)*lb[i][j] + epsilon*state.x[i][j] - la[i][j]
               for j in range(n-1)] for i in range(n-1)]
    if not _is_psd(matrix):
        raise ValueError("signed spectral certificate fails")

    if packed_trees is not None:
        if any(e not in set(selected) for tree in packed_trees for e in tree):
            raise ValueError("packing certificate uses an unselected edge")
        verify_trees(n, full_edges, packed_trees)
        low = len(packed_trees)
        if low < 1 or 4*low < r or 2*low > r:
            raise ValueError("packing certificate fails halving bounds")
        trees = packed_trees
    else:
        trees, low = _pack_selected(n, r, full_edges, selected)
    # For X=c L_H we have the global bound X<=c L_H. Otherwise the
    # shortcut cone supplies only X<=3 L_H on cut indicators.
    lap = _laplacian(n, state.edges)
    multiplier = state.x[0][0]/lap[0][0]
    if any(state.x[i][j] != multiplier*lap[i][j]
           for i in range(n-1) for j in range(n-1)):
        multiplier = Fraction(3)
    return SparsificationCertificate(selected, trees, low,
                                     Fraction(1, 2) + multiplier*epsilon)


def _pack_selected(n: int, r: int, full_edges: list[tuple[int, int, int]],
                   selected: list[int]) -> tuple[list[list[int]], int]:
    subedges = [full_edges[e] for e in selected]
    low, high = 0, min(r//2, len(subedges)//(n-1))
    best: list[set[int]] = []
    while low < high:
        requested = (low + high + 1)//2
        forests, complete, _ = pack_forests(n, subedges, requested)
        if complete:
            low, best = requested, forests
        else:
            high = requested - 1
    if low < 1 or 4*low < r:
        raise ValueError("selected graph lacks the required tree packing")
    if not best:
        best, complete, _ = pack_forests(n, subedges, low)
        assert complete
    trees = [[selected[e] for e in sorted(forest)] for forest in best]
    verify_trees(n, full_edges, trees)
    return trees, low


def certified_spectral_error(state: ContinuationState, edge_ids: list[int],
                             selected: list[int], bits: int = 16) -> Fraction:
    """Dyadic upper bound for L_A <= L_B/2 + epsilon X, checked exactly."""
    if bits < 1:
        raise ValueError("positive error precision required")
    lb = _edge_laplacian(state.n, state.edges, edge_ids)
    la = _edge_laplacian(state.n, state.edges, selected)
    size = state.n - 1

    def passes(error: Fraction) -> bool:
        return _is_psd([[lb[i][j]/2 + error*state.x[i][j] - la[i][j]
                         for j in range(size)] for i in range(size)])

    if passes(Fraction()):
        return Fraction()
    scale = 1 << bits
    low, high = 0, scale
    # L_A<=L_H<=X and L_B>=0 imply epsilon=1 is always sufficient.
    if not passes(Fraction(1)):
        raise ValueError("shortcut does not certify the unit error bound")
    while high-low > 1:
        middle = (low+high)//2
        if passes(Fraction(middle, scale)):
            high = middle
        else:
            low = middle
    return Fraction(high, scale)


def automatic_sparsification_step(
    state: ContinuationState, union_trees: list[list[int]],
    frame_iteration_cap: int | None = None,
    signing_method: str = "frobenius",
    signing_step_cap: int | None = None,
    tighten_error: bool = False,
    try_complement: bool = False,
    frame_method: str = "gradient",
    edge_order: str = "trees",
    materialize_padding: bool = True,
    phase_callback=None,
    sdp_iteration_cap: int | None = None,
    value_query_cap: int | None = None,
) -> AutomaticStep:
    """Generate and certify one step with either signing backend."""
    n, r = state.n, state.r
    q = len(union_trees)
    if state.s**4 < r or not state.verify_invariant() or not verify_shortcut_cone(state):
        raise ValueError("invalid terminal shortcut")
    if not (r <= 2*q and q <= r):
        raise ValueError("wrong shortcut tree count")
    full_edges = [(u, v, e) for e, (u, v) in enumerate(state.edges)]
    verify_trees(n, full_edges, union_trees)
    edge_ids = [e for tree in union_trees for e in tree]
    if edge_order == "pairs":
        edge_ids.sort(key=lambda e: (state.edges[e], e))
    elif edge_order != "trees":
        raise ValueError("unknown signing edge order")
    ramp = state.ramp()
    if any(ramp[e] <= 0 for e in edge_ids):
        raise ValueError("high-resistance shortcut edge")
    if phase_callback is not None:
        phase_callback("frame")
    if frame_method == "gradient":
        weights, _, iterations = find_frame_weights(
            n, [state.edges[e] for e in edge_ids], q, r,
            max_iterations=frame_iteration_cap)
    elif frame_method == "balancing":
        weights, _, iterations = find_balanced_frame_weights(
            n, [state.edges[e] for e in edge_ids], q, r,
            max_iterations=200 if frame_iteration_cap is None else frame_iteration_cap)
    else:
        raise ValueError("unknown frame search method")
    precision_bits = (1000*len(edge_ids)*r).bit_length() + 2
    data = prepare_stacked_columns(state, edge_ids, weights, precision_bits)
    if phase_callback is not None:
        phase_callback("signing")
    if signing_method == "frobenius":
        signing, residual_count = sign_stacked_data(data, r, materialize_padding=materialize_padding)
    elif signing_method == "appendix_a":
        signing, residual_count = sign_stacked_data_appendix_a(
            data, r, max_steps=signing_step_cap,
            max_feasibility_iterations=sdp_iteration_cap,
            max_value_queries=value_query_cap)
    elif signing_method == 'certified-tree-candidate':
        if edge_order != 'trees':
            raise ValueError('tree candidate requires tree edge order')
        signs = [1 if j < q//2 else -1 for j,tree in enumerate(union_trees) for _ in tree]
        signing, residual_count = sign_stacked_data_candidate(data,r,signs)
    else:
        raise ValueError("unknown signing method")
    candidates = []
    if phase_callback is not None:
        phase_callback("packing-and-spectral-verification")
    errors = []
    for polarity in ([1, -1] if try_complement else [1]):
        selected = [e for e, sign in zip(edge_ids, signing.signs) if polarity*sign > 0]
        epsilon = (certified_spectral_error(state, edge_ids, selected)
                   if tighten_error else (1 << 20)*dyadic_g(r))
        try:
            certificate = verify_sparsification(state, union_trees, selected, epsilon)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        signed = signing if polarity == 1 else replace(
            signing, signs=[-sign for sign in signing.signs])
        candidates.append(AutomaticStep(certificate, signed, iterations, residual_count,
                                        edge_ids, weights, epsilon))
    if not candidates:
        raise ValueError("no signing polarity retained the required packing: " + "; ".join(errors))
    return min(candidates, key=lambda item: (item.certificate.cut_load_factor,
                                             -item.certificate.r_next))
