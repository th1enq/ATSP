#!/usr/bin/env python3
"""Compose verified general sparsification steps into an explicit graph tree.

Instance mode selects g from the exact schedule budget. This parameter is
outside the source schedule promise. Every accepted step is replayable;
there is no universal constant thinness or practical convergence claim.
"""
import argparse
import json
import signal
from fractions import Fraction as F
from pathlib import Path
from continuation_solver import dyadic_g,schedule_budget
from continuation_state import initial_state
from general_sparsification import run_step,verify_report
from tree_packing import pack_forests,verify_trees

SCHEMA='general-tree-v1'


def instance_g(graph):
    state=initial_state(graph['n'],[tuple(e) for e in graph['edges']],graph['r'],dyadic_g(graph['r']))
    steps,_=schedule_budget(state)
    if not steps:
        return state.g
    bound=F(1,16)/(steps*state.t)
    g=state.g
    while g>bound:
        g/=2
    return g


def verify_tree_report(report):
    if report['schema']!=SCHEMA:
        raise ValueError('unsupported tree schema')
    if report['mode'] not in ('source','instance'):
        raise ValueError('unknown tree mode')
    graph=report['graph']
    initial_state(graph['n'],[tuple(e) for e in graph['edges']],graph['r'],dyadic_g(graph['r']))
    ids=list(range(len(graph['edges'])))
    r=graph['r']
    factor=F(1)
    for step in report['steps']:
        expected=dict(n=graph['n'],edges=[graph['edges'][e] for e in ids],r=r)
        if step['graph']!=expected:
            raise ValueError('step input differs from retained graph')
        verified=verify_report(step)
        if verified['status']!='certified-step':
            raise ValueError('tree chain contains an incomplete step')
        required_origin='source-initial-state' if report['mode']=='source' else 'instance-parameter-continuation'
        if step['origin']!=required_origin:
            raise ValueError('step origin differs from tree construction mode')
        proof=step['proof']
        ids=[ids[e] for e in proof['selected_edges']]
        r=proof['r_next']
        factor*=F(proof['cut_load_factor'])
    if report['status'] not in ('certified-tree','incomplete'):
        raise ValueError('unknown tree status')
    if 'failed_step' in report:
        failed=report['failed_step']
        expected=dict(n=graph['n'],edges=[graph['edges'][e] for e in ids],r=r)
        if failed['graph']!=expected or verify_report(failed)['status']!='incomplete':
            raise ValueError('invalid failed step prefix')
    tree=report['tree']
    if any(e not in set(ids) for e in tree):
        raise ValueError('tree leaves the retained graph')
    verify_trees(graph['n'],[(u,v,e) for e,(u,v) in enumerate(graph['edges'])],[tree])
    # A retained r-packing supplies L_G(S)>=r for each nontrivial cut.
    bound=min(F(graph['n']-1,graph['r']),factor*F(graph['n']-1,r))
    if report['retained_r']!=r or F(report['cut_ratio_bound'])!=bound:
        raise ValueError('altered tree cut bound')
    return dict(status=report['status'],rounds=len(report['steps']),vertices=graph['n'],
                retained_r=r,cut_ratio_bound=str(bound),mode=report['mode'])


def build_tree(graph,*,mode='source',signing_method='appendix_a',stop_r=4,max_rounds=32,**caps):
    if mode not in ('source','instance') or stop_r<4 or max_rounds<0:
        raise ValueError('invalid tree construction options')
    ids=list(range(len(graph['edges'])))
    r=graph['r']
    report=dict(schema=SCHEMA,graph=graph,mode=mode,steps=[],status='certified-tree')
    while r>stop_r:
        if len(report['steps'])>=max_rounds:
            report.update(status='incomplete',stop_reason='round cap reached')
            break
        current=dict(n=graph['n'],edges=[graph['edges'][e] for e in ids],r=r)
        try:
            step=run_step(current,continuation_g=instance_g(current) if mode=='instance' else None,
                          signing_method=signing_method,**caps)
        except RuntimeError as exc:
            report.update(status='incomplete',stop_reason=str(exc))
            break
        if step['status']=='below-source-cutoff':
            report['stop_reason']='source cutoff'
            break
        if step['status']!='certified-step':
            report.update(status='incomplete',stop_reason=step.get('error','step incomplete'),failed_step=step)
            break
        report['steps'].append(step)
        ids=[ids[e] for e in step['proof']['selected_edges']]
        r=step['proof']['r_next']
    subedges=[(graph['edges'][e][0],graph['edges'][e][1],e) for e in ids]
    forests,complete,_=pack_forests(graph['n'],subedges,1)
    if not complete:
        raise AssertionError('verified retained graph lacks a tree')
    report['tree']=[ids[e] for e in sorted(forests[0])]
    report['retained_r']=r
    product=F(1)
    for step in report['steps']:
        product*=F(step['proof']['cut_load_factor'])
    report['cut_ratio_bound']=str(min(F(graph['n']-1,graph['r']),product*F(graph['n']-1,r)))
    verify_tree_report(report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    build=sub.add_parser('build')
    build.add_argument('input',type=Path)
    build.add_argument('--output',type=Path,required=True)
    build.add_argument('--mode',choices=['source','instance'],default='source')
    build.add_argument('--signing-method',choices=['appendix_a','certified-tree-candidate'],default='appendix_a')
    build.add_argument('--stop-r',type=int,default=4)
    build.add_argument('--max-rounds',type=int,default=32)
    build.add_argument('--max-response-iterations',type=int)
    build.add_argument('--sdp-iteration-cap',type=int)
    build.add_argument('--value-query-cap',type=int)
    build.add_argument('--seconds',type=int)
    check=sub.add_parser('verify')
    check.add_argument('certificate',type=Path)
    args=parser.parse_args()
    if args.command=='verify':
        print(json.dumps(verify_tree_report(json.loads(args.certificate.read_text())),indent=2))
        return
    if any(v is not None and v<0 for v in (args.max_rounds,args.max_response_iterations,args.sdp_iteration_cap,args.value_query_cap)):
        parser.error('caps must be nonnegative')
    if args.seconds is not None:
        if args.seconds<1: parser.error('seconds must be positive')
        def expire(signum,frame): raise RuntimeError('tree construction wall time budget reached')
        signal.signal(signal.SIGALRM,expire)
        signal.alarm(args.seconds)
    try:
        report=build_tree(json.loads(args.input.read_text()),mode=args.mode,signing_method=args.signing_method,
           stop_r=args.stop_r,max_rounds=args.max_rounds,max_response_iterations=args.max_response_iterations,
           sdp_iteration_cap=args.sdp_iteration_cap,value_query_cap=args.value_query_cap)
    finally:
        signal.alarm(0)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(verify_tree_report(report),indent=2))
    if report['status']=='incomplete': raise SystemExit(2)


if __name__=='__main__': main()
