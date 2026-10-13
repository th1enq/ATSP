"""Exact response search for Proposition 3.1 via rational ellipsoid cuts.

The source paper's radius promise applies only under its large-r hypotheses.
A returned response is always checked exactly; a volume-cutoff exception is
not a mathematical infeasibility certificate.
"""

from __future__ import annotations

from fractions import Fraction

from continuation_oracle import separate_step, _laplacian
from continuation_state import ContinuationState
from rational_ellipsoid import find_feasible
from tree_packing import pack_forests, verify_trees


def dyadic_g(r: int) -> Fraction:
    """Choose r^(-1/8) <= g < 2*r^(-1/8) without roots or floats."""
    if r < 1:
        raise ValueError("r must be positive")
    return Fraction(1, 2**((r.bit_length() - 1)//8))


def variable_keys(n: int, active: list[bool]) -> list[str]:
    keys = [f"Y:{i}:{j}" for i in range(n-1) for j in range(i, n-1)]
    keys += [f"lambda:{i}:{j}:{k}" for i in range(n) for j in range(n)
             for k in range(n) if i != j and j != k and i != k]
    keys += [f"y:{e}" for e, enabled in enumerate(active) if enabled]
    keys += [f"z:{e}" for e, enabled in enumerate(active) if enabled]
    return keys


def schedule_budget(state):
    """Exact loss dictated by the schedule, independent of response search."""
    steps, s = 0, state.s
    while s**4 < state.r:
        s *= 1+state.t
        steps += 1
    return steps, state.q-2*state.g*state.r*state.t*steps


def solve_response(state: ContinuationState, max_iterations: int | None = None
                   ) -> tuple[dict[str, Fraction], int]:
    if not state.verify_invariant():
        raise ValueError("old continuation invariant fails")
    u = state.ramp()
    active = [value > 0 for value in u]
    keys = variable_keys(state.n, active)
    q_next = state.q - 2*state.g*state.r*state.t
    if q_next <= 0:
        raise ValueError("nonpositive next packing target")
    P = state.n + len(state.edges) + 2

    # A cheap response is a proposal, accepted only by the full separator.
    # It is useful for graphs with uniformly small edge resistance.
    lap = _laplacian(state.n, state.edges)
    scales = [Fraction(2), Fraction(3)]
    c = state.x[0][0]/lap[0][0]
    if all(state.x[i][j] == c*lap[i][j] for i in range(state.n-1) for j in range(state.n-1)):
        # Keep the *next* scalar matrix on a fixed grid, through a fully
        # checked response, rather than accumulating enormous denominators.
        next_c = (1-state.t)*c+2*state.t
        grid = 1 << 20
        rounded = Fraction((next_c*grid).numerator//(next_c*grid).denominator,grid)
        scales.insert(0,(rounded-(1-state.t)*c)/state.t)
    for scale in scales:
        proposal = {f'Y:{i}:{j}': scale*lap[i][j]
                    for i in range(state.n-1) for j in range(i,state.n-1)}
        for e, enabled in enumerate(active):
            if enabled:
                proposal[f'y:{e}'] = Fraction(1)
                proposal[f'z:{e}'] = state.kappa + 1
        if separate_step(state.n, state.edges, active, u, state.s,
                         state.t, state.kappa, q_next, proposal) is None:
            return proposal, 0

    def separator(vector: list[Fraction]):
        point = dict(zip(keys, vector))
        cut = separate_step(state.n, state.edges, active, u, state.s,
                            state.t, state.kappa, q_next, point)
        return None if cut is None else (
            cut.constant, [cut.coefficients.get(key, Fraction()) for key in keys])

    vector, iterations = find_feasible(len(keys), separator,
                                       Fraction(2*P**3), Fraction(1, P**30),
                                       max_iterations=max_iterations)
    response = dict(zip(keys, vector))
    if separate_step(state.n, state.edges, active, u, state.s,
                     state.t, state.kappa, q_next, response) is not None:
        raise AssertionError("ellipsoid returned an unverified response")
    return response, iterations


def run_continuation(state: ContinuationState, max_steps: int | None = None,
                     max_response_iterations: int | None = None,
                     responses: list[dict[str, Fraction]] | None = None,
                     ) -> tuple[ContinuationState, list[int]]:
    """Run the exact schedule to s^4 >= r, verifying every returned step."""
    cuts_per_step = []
    while state.s**4 < state.r:
        if max_steps is not None and len(cuts_per_step) >= max_steps:
            raise ValueError("continuation step cap reached")
        response, cuts = solve_response(state, max_iterations=max_response_iterations)
        state = state.advance(response)
        if responses is not None:
            responses.append(response.copy())
        cuts_per_step.append(cuts)
    return state, cuts_per_step


def finalize_shortcut(state: ContinuationState) -> tuple[list[int], list[list[int]]]:
    """Pack trees on terminal low-resistance edges, or reject the state."""
    if state.s**4 < state.r or not state.verify_invariant():
        raise ValueError("state is not a verified terminal continuation state")
    ramp = state.ramp()
    active_ids = [e for e, value in enumerate(ramp) if value > 0]
    count = state.q.numerator // state.q.denominator - 1
    if count < 1:
        raise ValueError("terminal packing target too small")
    edges = [(state.edges[e][0], state.edges[e][1], e) for e in active_ids]
    forests, complete, obstruction = pack_forests(state.n, edges, count)
    if not complete:
        raise ValueError(f"low-resistance packing failed: {obstruction}")
    trees = [[active_ids[e] for e in sorted(forest)] for forest in forests]
    verify_trees(state.n, [(u, v, e) for e, (u, v) in enumerate(state.edges)], trees)
    return active_ids, trees
