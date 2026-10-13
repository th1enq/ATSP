#!/usr/bin/env python3
"""Fixed-work comparison of exact dense and sparse Appendix A separators.

The dense variant is a frozen evaluation formula, used only for comparison.
Both runs retain the same theoretical precision and ellipsoid equations.
"""
import argparse
import cProfile
import hashlib
import gzip
import json
import platform
import signal
import sys
from fractions import Fraction as F
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import appendix_a_value_oracle as oracle
from appendix_a_potential import AppendixAPotential
from exact_psd import psd_or_negative_vector, quadratic_form
from general_sparsification import run_step, verify_report
from sdp_dual_certificate import serialize_sdp_value


def dense_separate(self, point, target=None):
    if len(point) != self.dimension:
        raise ValueError('wrong SDP point dimension')
    point = [F(v) for v in point]
    if point[0] < 0:
        return F(), [F(int(i==0)) for i in range(self.dimension)]
    if point[0] > 100:
        return F(100), [F(-int(i==0)) for i in range(self.dimension)]
    for constant, coefficients in self.lmis:
        size = len(constant)
        matrix = [[constant[i][j]+sum((point[k]*coefficients[k][i][j]
                   for k in range(self.dimension)),F()) for j in range(size)] for i in range(size)]
        good,witness = psd_or_negative_vector(matrix)
        if not good:
            return quadratic_form(constant,witness), [quadratic_form(c,witness) for c in coefficients]
    if target is not None and self.objective_value(point) > target:
        return F(target), [-v for v in self.objective]
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--separator', choices=['dense','sparse'], default='sparse')
    parser.add_argument('--iteration-cap', type=int, default=400)
    parser.add_argument('--seconds', type=int, default=30)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cprofile', type=Path)
    parser.add_argument('--certificates', action='store_true', help='save exact primal/dual witnesses for completed SDP queries')
    parser.add_argument('--input', type=Path, help='explicit graph JSON; defaults to parallel-eight')
    parser.add_argument('--terminal-witness', type=Path, help='checked terminal state JSON')
    parser.add_argument('--step-output', type=Path, help='save the generated sparsification certificate')
    args = parser.parse_args()
    if args.seconds < 1 or args.iteration_cap < 0:
        parser.error('positive seconds and nonnegative iteration cap required')
    if bool(args.input) != bool(args.terminal_witness):
        parser.error('input and terminal-witness must be supplied together')
    graph=json.loads(args.input.read_text()) if args.input else dict(n=2,edges=[[0,1]]*8,r=8)
    witness=json.loads(args.terminal_witness.read_text()) if args.terminal_witness else dict(x=[['8']],s='2',q='8',cone_lambda={})
    potentials, sdps, ellipsoids = [], [], []
    base_potential = AppendixAPotential.value_interval
    base_sdp = oracle.AppendixASDP.value_interval
    base_ellipsoid = oracle.find_feasible
    base_separate = dense_separate if args.separator == 'dense' else oracle.AppendixASDP.separate
    separator_metrics = dict(calls=0, seconds=0.0, max_numerator_bits=0, max_denominator_bits=0)
    point_digest = hashlib.sha256()

    def timed_separate(self, point, target=None):
        separator_metrics['calls'] += 1
        point_digest.update(json.dumps([str(v) for v in point]+[str(target)],
                                      separators=(',',':')).encode()+b'\n')
        for v in point:
            separator_metrics['max_numerator_bits'] = max(separator_metrics['max_numerator_bits'], abs(v.numerator).bit_length())
            separator_metrics['max_denominator_bits'] = max(separator_metrics['max_denominator_bits'], v.denominator.bit_length())
        started = perf_counter()
        try:
            return base_separate(self, point, target)
        finally:
            separator_metrics['seconds'] += perf_counter()-started

    def timed_potential(self, x, accuracy, **kwargs):
        record = dict(accuracy=str(accuracy), accuracy_denominator_bits=accuracy.denominator.bit_length(),
                      variables=self.n, matrix_dimension=self.d, completed=False)
        potentials.append(record)
        started = perf_counter()
        try:
            result = base_potential(self, x, accuracy, **kwargs)
            record['completed'] = True
            return result
        finally:
            record['seconds'] = perf_counter()-started

    def timed_sdp(self, accuracy, **kwargs):
        record = dict(accuracy=str(accuracy), variables=self.dimension, completed=False)
        sdps.append(record)
        started = perf_counter()
        try:
            result = base_sdp(self, accuracy, **kwargs)
            record.update(completed=True, feasibility_calls=result.feasibility_calls,
                          newton_steps=result.newton_steps,
                          lower=str(result.lower), upper=str(result.upper),
                          dual_certified=result.lower_certificate is not None)
            if args.certificates:
                record['certificate'] = serialize_sdp_value(self,result,accuracy)
            return result
        finally:
            record['seconds'] = perf_counter()-started

    def timed_ellipsoid(dimension, separate, outer_radius, inner_radius, **kwargs):
        record = dict(dimension=dimension, iterations=0, completed=False,
                      inner_radius=str(inner_radius), max_iterations=kwargs.get('max_iterations'))
        ellipsoids.append(record)
        def count(point):
            record['iterations'] += 1
            return separate(point)
        started = perf_counter()
        try:
            result = base_ellipsoid(dimension, count, outer_radius, inner_radius, **kwargs)
            record['completed'] = True
            return result
        except RuntimeError as exc:
            record['error_type'] = type(exc).__name__
            raise
        finally:
            record['seconds'] = perf_counter()-started

    oracle.AppendixASDP.separate = timed_separate
    oracle.AppendixASDP.value_interval = timed_sdp
    oracle.find_feasible = timed_ellipsoid
    AppendixAPotential.value_interval = timed_potential
    def expire(signum, frame):
        raise RuntimeError('profiling wall time budget reached')
    signal.signal(signal.SIGALRM, expire)
    profile = cProfile.Profile() if args.cprofile else None
    if profile:
        profile.enable()
    started = perf_counter()
    signal.alarm(args.seconds)
    try:
        report = run_step(graph,
            terminal_witness=witness,
            sdp_iteration_cap=args.iteration_cap, signing_cap=20)
    finally:
        signal.alarm(0)
        if profile:
            profile.disable()
            args.cprofile.parent.mkdir(parents=True,exist_ok=True)
            profile.dump_stats(str(args.cprofile))
    result = dict(separator=args.separator, iteration_cap=args.iteration_cap,
                  wall_budget_seconds=args.seconds, cprofile_enabled=bool(profile),
                  python=platform.python_version(), elapsed_seconds=perf_counter()-started,
                  graph=graph, terminal_witness=witness,
                  status=report['status'], phase=report['phase'], error=report.get('error'),
                  error_type=report.get('error_type'), separator_metrics=separator_metrics,
                  potential_queries=potentials, sdp_queries=sdps, ellipsoid_solves=ellipsoids,
                  replay=verify_report(report))
    result['separator_metrics']['point_sequence_sha256'] = point_digest.hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    serialized=json.dumps(result,indent=2)+'\n'
    if args.output.suffix=='.gz':
        with gzip.open(args.output,'wt') as stream:
            stream.write(serialized)
    else:
        args.output.write_text(serialized)
    if args.step_output:
        args.step_output.parent.mkdir(parents=True,exist_ok=True)
        args.step_output.write_text(json.dumps(report,indent=2)+'\n')
    # Certificate payloads can be large; the detailed data is in the artifact.
    print(json.dumps({k:result[k] for k in ('status','phase','elapsed_seconds','error_type')},indent=2))


if __name__ == '__main__':
    main()
