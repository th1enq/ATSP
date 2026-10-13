"""Source backend for one explicit-graph step, with exact JSON replay.

No Frobenius, scalar search, balancing, or brute-force fallback. The cutoff
is a conditional sufficient bound from docs/EXPLICIT_THRESHOLD_AUDIT.md.
A supplied terminal witness proves an instance; it does not prove that the
continuation algorithm reached that witness.
"""
from __future__ import annotations

import argparse
import json
import signal
from fractions import Fraction as F
from pathlib import Path

from continuation_oracle import _edge_vector
from continuation_solver import dyadic_g, finalize_shortcut, solve_response, schedule_budget
from continuation_state import ContinuationState, initial_state, inverse
from exact_psd import psd_or_negative_vector
from signing_certificate import check_signing
from signing_padding import prepare_stacked_columns
from tree_packing import pack_forests, verify_trees
from verified_sparsification import (automatic_sparsification_step,
                                     verify_shortcut_cone, verify_sparsification)

R0 = 1 << 4097
SCHEMA = 'general-sparsification-v1'


def state_dict(state):
    return dict(x=[[str(v) for v in row] for row in state.x], s=str(state.s),
                q=str(state.q), cone_lambda={k: str(v) for k, v in state.cone_lambda.items()})


def load_state(graph, witness):
    state = initial_state(graph['n'], [tuple(e) for e in graph['edges']], graph['r'], dyadic_g(graph['r']))
    size = state.n - 1
    if len(witness['x']) != size or any(len(row) != size for row in witness['x']):
        raise ValueError('wrong witness matrix dimension')
    state.x = [[F(v) for v in row] for row in witness['x']]
    if any(state.x[i][j] != state.x[j][i] for i in range(size) for j in range(size)):
        raise ValueError('nonsymmetric witness matrix')
    state.s, state.q = F(witness['s']), F(witness['q'])
    state.cone_lambda = {k: F(v) for k, v in witness.get('cone_lambda', {}).items()}
    allowed = {f'lambda:{i}:{j}:{k}' for i in range(state.n) for j in range(state.n)
               for k in range(state.n) if len({i,j,k}) == 3}
    if set(state.cone_lambda) - allowed or state.s <= 0 or state.q < 0:
        raise ValueError('invalid witness parameters')
    if not verify_shortcut_cone(state) or not state.verify_invariant():
        raise ValueError('invalid shortcut witness')
    return state


def verify_frame(state, ids, weights, selected, epsilon, q):
    """Exact leverage upper bound and lower covariance block by congruence."""
    if len(weights) != len(ids) or any(w <= 0 for w in weights):
        raise ValueError('invalid frame weights')
    vectors = [_edge_vector(state.n, state.edges[e]) for e in ids]
    d = state.n - 1
    total = [[sum((w*b[i]*b[j] for w,b in zip(weights,vectors)), F())
              for j in range(d)] for i in range(d)]
    inv = inverse(total)
    bound = (1+F(4,state.r))/q
    for w,b in zip(weights,vectors):
        score = w*sum((b[i]*inv[i][j]*b[j] for i in range(d) for j in range(d)), F())
        if score > bound:
            raise ValueError('frame leverage certificate fails')
    retained = set(selected)
    lower = [[sum((w*b[i]*b[j] for e,w,b in zip(ids,weights,vectors) if e in retained), F())
              -(F(1,2)-epsilon)*total[i][j] for j in range(d)] for i in range(d)]
    if not psd_or_negative_vector(lower)[0]:
        raise ValueError('lower frame covariance certificate fails')


def verify_report(report):
    if report['schema'] != SCHEMA:
        raise ValueError('unsupported certificate schema')
    graph = report['graph']
    g = F(report['continuation_g']) if report['origin'] == 'instance-parameter-continuation' else dyadic_g(graph['r'])
    state = initial_state(graph['n'], [tuple(e) for e in graph['edges']],
                          graph['r'], g)
    if report['origin'] == 'supplied-terminal-witness':
        if report['responses']:
            raise ValueError('supplied witness must not claim a continuation trace')
        state = load_state(graph, report['start'])
    elif report['origin'] not in ('source-initial-state', 'instance-parameter-continuation'):
        raise ValueError('unknown certificate origin')
    elif state_dict(state) != report['start']:
        raise ValueError('altered initial state')
    if 'schedule_budget' in report:
        count, q = schedule_budget(state)
        if report['schedule_budget'] != dict(steps=count, terminal_q=str(q)):
            raise ValueError('altered deterministic schedule budget')
    for raw in report['responses']:
        if state.s**4 >= state.r:
            raise ValueError('response after terminal state')
        state = state.advance({k:F(v) for k,v in raw.items()})
        if not verify_shortcut_cone(state):
            raise ValueError('continuation shortcut cone fails')
    if state_dict(state) != report['terminal']:
        raise ValueError('continuation trace does not match final state')
    status = report['status']
    if status == 'below-source-cutoff':
        if state.r >= R0 or report['responses'] or report['origin'] != 'source-initial-state':
            raise ValueError('invalid source stopping branch')
        verify_trees(state.n, [(u,v,e) for e,(u,v) in enumerate(state.edges)], [report['tree']])
        return dict(status=status, r=state.r, rounds=0)
    if status == 'incomplete':
        return dict(status=status, verified_responses=len(report['responses']), phase=report['phase'])
    if status != 'certified-step':
        raise ValueError('unknown certificate status')
    proof = report['proof']
    union = proof['union_trees']
    ids = [e for tree in union for e in tree]
    cert = verify_sparsification(state, union, proof['selected_edges'], F(proof['epsilon']),
                                 packed_trees=proof['packed_trees'])
    if ids != proof['edge_ids']:
        raise ValueError('signing edge order differs from tree union')
    weights = [F(w) for w in proof['frame_weights']]
    verify_frame(state, ids, weights, cert.selected_edges, F(proof['epsilon']), len(union))
    bits = (1000*len(ids)*state.r).bit_length()+2
    data = prepare_stacked_columns(state, ids, weights, bits)
    signs = proof['signs']
    if len(signs) != len(ids) or any(type(s) is not int or s not in (-1,1) for s in signs):
        raise ValueError('invalid signing vector')
    if sorted(e for e,s in zip(ids,signs) if s > 0) != cert.selected_edges:
        raise ValueError('selected edges disagree with signing')
    if not check_signing(data, signs, F(proof['signing_bound']), require_identity=False):
        raise ValueError('stacked signing certificate fails')
    if cert.r_next != proof['r_next'] or str(cert.cut_load_factor) != proof['cut_load_factor']:
        raise ValueError('altered step bound')
    return dict(status=status, r=state.r, r_next=cert.r_next,
                cut_load_factor=str(cert.cut_load_factor),
                ratio_loss_bound=str(cert.cut_load_factor*state.r/cert.r_next),
                origin=report['origin'], above_conditional_cutoff=state.r >= R0)


def run_step(graph, *, below_cutoff=False, terminal_witness=None,
             max_steps=None, max_response_iterations=None,
             frame_cap=None, signing_cap=None, sdp_iteration_cap=None, value_query_cap=None,
             continuation_g=None, signing_method='appendix_a'):
    if continuation_g is not None and (F(continuation_g) <= 0 or terminal_witness is not None):
        raise ValueError('instance continuation requires positive g and no supplied witness')
    state = initial_state(graph['n'], [tuple(e) for e in graph['edges']],
                          graph['r'], dyadic_g(graph['r']) if continuation_g is None else F(continuation_g))
    origin = 'source-initial-state' if continuation_g is None else 'instance-parameter-continuation'
    if terminal_witness is not None:
        state = load_state(graph, terminal_witness)
        if state.s**4 < state.r:
            raise ValueError('supplied witness is not terminal')
        origin = 'supplied-terminal-witness'
    report = dict(schema=SCHEMA, graph=graph, origin=origin, start=state_dict(state),
                  responses=[], status='incomplete', phase='initialization')
    if continuation_g is not None:
        report['continuation_g'] = str(state.g)
    report['signing_method'] = signing_method
    # This is the J=0 stopping branch of the source, not a sparsification.
    if state.r < R0 and not below_cutoff and terminal_witness is None and continuation_g is None:
        forests, complete, _ = pack_forests(state.n,
            [(u,v,e) for e,(u,v) in enumerate(state.edges)], 1)
        if not complete:
            raise ValueError('connected input unexpectedly lacks a spanning tree')
        report.update(status='below-source-cutoff', tree=sorted(forests[0]), terminal=state_dict(state))
        verify_report(report)
        return report
    try:
        report['phase'] = 'continuation'
        if max_steps is None and terminal_witness is None:
            steps, terminal_q = schedule_budget(state)
            report['schedule_budget'] = dict(steps=steps, terminal_q=str(terminal_q))
            if terminal_q <= 0:
                raise ValueError('prescribed schedule exhausts Q before termination; this is not graph infeasibility')
        while state.s**4 < state.r:
            if max_steps is not None and len(report['responses']) >= max_steps:
                raise ValueError('continuation step cap reached')
            response, _ = solve_response(state, max_iterations=max_response_iterations)
            next_state = state.advance(response)
            if not verify_shortcut_cone(next_state):
                raise ValueError('continuation cone certificate fails')
            report['responses'].append({k:str(v) for k,v in response.items()})
            state = next_state
        report['phase'] = 'extraction'
        _, union = finalize_shortcut(state)
        # The source discards excess trees before normalization.
        union = union[:state.r]
        report['phase'] = 'frame'
        def phase_changed(phase):
            report['phase'] = 'appendix-a-signing' if phase == 'signing' else phase
        step = automatic_sparsification_step(state, union, frame_iteration_cap=frame_cap,
                    signing_method=signing_method, signing_step_cap=signing_cap,
                    frame_method='gradient', phase_callback=phase_changed,
                    sdp_iteration_cap=sdp_iteration_cap, value_query_cap=value_query_cap)
        c = step.certificate
        report['proof'] = dict(union_trees=union, selected_edges=c.selected_edges,
            packed_trees=c.packed_trees, r_next=c.r_next, cut_load_factor=str(c.cut_load_factor),
            edge_ids=step.edge_ids, frame_weights=[str(w) for w in step.frame_weights],
            epsilon=str(step.epsilon), signs=step.signing.signs,
            signing_bound=str(step.signing.spectral_bound))
        report.update(status='certified-step', phase='complete')
    except (ValueError, RuntimeError, AssertionError) as exc:
        report.update(status='incomplete', error_type=type(exc).__name__, error=str(exc))
    report['terminal'] = state_dict(state)
    # Never emit a success until all independent checks pass.
    try:
        verify_report(report)
    except (ValueError, AssertionError) as exc:
        report.update(status='incomplete', phase='certificate-replay', error=str(exc))
        report.pop('proof', None)
        verify_report(report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    step = sub.add_parser('step')
    step.add_argument('input', type=Path, help='JSON: n, edges (explicit copies), r')
    step.add_argument('--output', type=Path, required=True)
    step.add_argument('--below-cutoff', action='store_true', help='diagnostic outside the source promise')
    step.add_argument('--terminal-witness', type=Path)
    step.add_argument('--continuation-g', type=F, help='instance parameter; outside source schedule promise')
    step.add_argument('--signing-method', choices=['appendix_a','certified-tree-candidate'], default='appendix_a')
    step.add_argument('--max-steps', type=int)
    step.add_argument('--max-response-iterations', type=int)
    step.add_argument('--frame-cap', type=int)
    step.add_argument('--signing-cap', type=int)
    step.add_argument('--seconds', type=int, help='wall time budget for construction (Linux)')
    step.add_argument('--sdp-iteration-cap', type=int, help='Newton steps or cuts per inner SDP solve')
    step.add_argument('--value-query-cap', type=int, help='potential queries per signing')
    check = sub.add_parser('verify')
    check.add_argument('certificate', type=Path)
    args = parser.parse_args()
    if args.command == 'verify':
        print(json.dumps(verify_report(json.loads(args.certificate.read_text())), indent=2))
        return
    for key in ('max_steps','max_response_iterations','frame_cap','signing_cap',
                'sdp_iteration_cap','value_query_cap'):
        value = getattr(args,key)
        if value is not None and value < 0:
            parser.error(f'{key} must be nonnegative')
    if args.seconds is not None:
        if args.seconds < 1:
            parser.error('seconds must be positive')
        def budget_expired(signum, frame):
            raise RuntimeError('construction wall time budget reached; no infeasibility claim')
        signal.signal(signal.SIGALRM, budget_expired)
        signal.alarm(args.seconds)
    try:
        report = run_step(json.loads(args.input.read_text()), below_cutoff=args.below_cutoff,
            terminal_witness=json.loads(args.terminal_witness.read_text()) if args.terminal_witness else None,
            max_steps=args.max_steps, max_response_iterations=args.max_response_iterations,
            frame_cap=args.frame_cap, signing_cap=args.signing_cap,
            sdp_iteration_cap=args.sdp_iteration_cap, value_query_cap=args.value_query_cap,
            continuation_g=args.continuation_g, signing_method=args.signing_method)
    finally:
        signal.alarm(0)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(verify_report(report), indent=2))
    if report['status'] == 'incomplete':
        raise SystemExit(2)


if __name__ == '__main__':
    main()
