#!/usr/bin/env python3
"""Reproducible noncommuting SDP and Appendix A signing certificates."""
import argparse
import gzip
import json
import sys
from fractions import Fraction as F
from pathlib import Path
from time import perf_counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from appendix_a_signing import AppendixASigner
from appendix_a_value_oracle import AppendixASDP
from sdp_dual_certificate import serialize_sdp_value,verify_sdp_value
from sdp_collinear import collinear_proposal
from sdp_orthogonal import orthogonal_proposal
from exact_psd import psd_or_negative_vector


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--iteration-cap',type=int,default=400)
    args=parser.parse_args()
    matrices=[[[F(1,2),F(0)],[F(0),F(0)]],[[F(1,4),F(1,4)],[F(1,4),F(1,4)]]]
    report=dict(schema='noncommuting-sdp-experiment-v1',sdp_queries=[])
    for accuracy in (F(1,8),F(1,10**12),F(1,10**30)):
        sdp=AppendixASDP(matrices,[F(1,3),F(-1,4)],[F(1),F(2,3)],F(1,3))
        assert collinear_proposal(sdp,96) is None and orthogonal_proposal(sdp,96) is None
        started=perf_counter()
        interval=sdp.value_interval(accuracy,args.iteration_cap)
        raw=serialize_sdp_value(sdp,interval,accuracy)
        verify_sdp_value(raw)
        report['sdp_queries'].append(dict(completed=True,seconds=perf_counter()-started,
             newton_steps=interval.newton_steps,gap_float=float(interval.upper-interval.lower),certificate=raw))
    # Record every query of the actual noncommuting Appendix A descent too.
    original=AppendixASDP.value_interval
    def record(self,accuracy,**kwargs):
        result=original(self,accuracy,**kwargs)
        report['sdp_queries'].append(dict(completed=True,signing_query=True,
                certificate=serialize_sdp_value(self,result,accuracy)))
        return result
    AppendixASDP.value_interval=record
    try:
        started=perf_counter()
        result=AppendixASigner(matrices,max_feasibility_iterations=args.iteration_cap,
                              max_value_queries=200).sign(max_steps=10)
        signs=result.signs
        signed=[[sum((sign*a[i][j] for sign,a in zip(signs,matrices)),F()) for j in range(2)] for i in range(2)]
        certificate=[[result.spectral_bound_squared*int(i==j)-sum((signed[i][k]*signed[k][j] for k in range(2)),F())
                      for j in range(2)] for i in range(2)]
        assert psd_or_negative_vector(certificate)[0]
        report['signing']=dict(signs=signs,steps=result.steps,value_queries=result.value_calls,
            spectral_bound_squared=str(result.spectral_bound_squared),seconds=perf_counter()-started)
    finally:
        AppendixASDP.value_interval=original
    args.output.parent.mkdir(parents=True,exist_ok=True)
    if args.output.suffix=='.gz':
        with gzip.open(args.output,'wt') as stream: json.dump(report,stream)
    else:
        args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(intervals=len(report['sdp_queries']),signing=report['signing']),indent=2))


if __name__=='__main__': main()
