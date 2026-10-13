import copy
import sys
import unittest
from fractions import Fraction as F
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from continuation_solver import dyadic_g, run_continuation
from continuation_state import initial_state
from general_sparsification import SCHEMA, run_step, state_dict, verify_report, verify_frame
from verified_sparsification import automatic_sparsification_step


class GeneralSparsificationTest(unittest.TestCase):
    def test_literal_source_small_branch(self):
        graph = dict(n=3, edges=[[0,1],[1,2],[0,2]], r=1)
        with patch('general_sparsification.solve_response', side_effect=AssertionError('unexpected')):
            report = run_step(graph)
        self.assertEqual(verify_report(report)['rounds'], 0)
        report['tree'] = [0,0]
        with self.assertRaises(ValueError):
            verify_report(report)

    def test_real_response_trace_and_tampering(self):
        graph = dict(n=2, edges=[[0,1]]*3, r=1)
        report = run_step(graph, below_cutoff=True, max_steps=1, max_response_iterations=2000)
        self.assertEqual(report['status'], 'incomplete')
        self.assertEqual(len(report['responses']), 1)
        self.assertEqual(verify_report(report)['verified_responses'], 1)
        bad = copy.deepcopy(report)
        bad['responses'][0]['Y:0:0'] = '-1'
        with self.assertRaises(ValueError):
            verify_report(bad)
        bad = copy.deepcopy(report)
        bad['responses'] = []
        with self.assertRaisesRegex(ValueError, 'trace'):
            verify_report(bad)

    def test_zero_ellipsoid_budget_allows_verified_analytic_response(self):
        graph = dict(n=2, edges=[[0,1]]*3, r=1)
        report = run_step(graph, below_cutoff=True, max_steps=1, max_response_iterations=0)
        self.assertEqual(report['status'], 'incomplete')
        self.assertEqual(report['phase'], 'continuation')
        self.assertNotIn('proof', report)
        self.assertEqual(verify_report(report)['verified_responses'], 1)
        self.assertEqual(report['error'], 'continuation step cap reached')

    def test_run_continuation_propagates_response_budget(self):
        state = initial_state(2, [(0,1)]*3, 1, dyadic_g(1))
        with patch('continuation_solver.solve_response', side_effect=RuntimeError('budget')) as solve:
            with self.assertRaises(RuntimeError):
                run_continuation(state, max_response_iterations=17)
        solve.assert_called_once_with(state, max_iterations=17)

    def supplied_certificate(self):
        # A checker fixture, not evidence that Appendix A or continuation produced it.
        graph = dict(n=2, edges=[[0,1]]*8, r=8)
        state = initial_state(2, [(0,1)]*8, 8, dyadic_g(8))
        state.s = F(2)
        union = [[e] for e in range(8)]
        step = automatic_sparsification_step(state, union, tighten_error=True)
        cert = step.certificate
        return dict(schema=SCHEMA, graph=graph, origin='supplied-terminal-witness',
            start=state_dict(state), terminal=state_dict(state), responses=[], status='certified-step',
            proof=dict(union_trees=union, selected_edges=cert.selected_edges,
                packed_trees=cert.packed_trees, r_next=cert.r_next,
                cut_load_factor=str(cert.cut_load_factor), edge_ids=step.edge_ids,
                frame_weights=[str(w) for w in step.frame_weights], epsilon=str(step.epsilon),
                signs=step.signing.signs, signing_bound=str(step.signing.spectral_bound)))

    def test_independent_replay_without_optimizers(self):
        report = self.supplied_certificate()
        with patch('general_sparsification.solve_response', side_effect=AssertionError('solver')),\
             patch('general_sparsification.automatic_sparsification_step', side_effect=AssertionError('signer')):
            result = verify_report(report)
        self.assertEqual(result['r_next'], 4)
        self.assertEqual(result['cut_load_factor'], '1/2')
        self.assertEqual(result['origin'], 'supplied-terminal-witness')
        for field, value in [('signs',[1]*8), ('frame_weights',['0']*8),
                             ('cut_load_factor','0'), ('packed_trees',[[0]]*4)]:
            bad = copy.deepcopy(report)
            bad['proof'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                verify_report(bad)

    def test_lower_frame_block_independent_of_cut_block(self):
        state = initial_state(2, [(0,1)]*8, 8, dyadic_g(8))
        with self.assertRaisesRegex(ValueError, 'lower frame'):
            verify_frame(state, list(range(8)), [F(1)]*8, [0], F(0), 8)

    def test_supplied_witness_cannot_claim_source_trace(self):
        report = self.supplied_certificate()
        report['origin'] = 'source-initial-state'
        with self.assertRaisesRegex(ValueError, 'initial'):
            verify_report(report)

    def test_source_backend_reaches_appendix_a_without_fallback(self):
        graph = dict(n=2, edges=[[0,1]]*8, r=8)
        witness = dict(x=[['8']], s='2', q='8', cone_lambda={})
        report = run_step(graph, terminal_witness=witness, signing_cap=0)
        self.assertEqual(report['status'], 'incomplete')
        self.assertEqual(report['phase'], 'appendix-a-signing')
        self.assertIn('Appendix A step limit', report['error'])
        self.assertNotIn('proof', report)
        self.assertEqual(verify_report(report)['status'], 'incomplete')

    def test_inner_sdp_budget_is_recorded_as_incomplete(self):
        graph = dict(n=3, edges=[[0,1]]*8+[[1,2]]*8+[[0,2]]*8, r=8)
        witness = dict(x=[['16','-8'],['-8','16']], s='2', q='8', cone_lambda={})
        report = run_step(graph, terminal_witness=witness, sdp_iteration_cap=0)
        self.assertEqual(report['error_type'], 'IterationLimitReached')
        self.assertEqual(report['phase'], 'appendix-a-signing')
        self.assertEqual(report['status'], 'incomplete')
        self.assertNotIn('proof', report)

    def test_collinear_appendix_a_step_completes_without_ellipsoid(self):
        graph = dict(n=2, edges=[[0,1]]*8, r=8)
        witness = dict(x=[['8']], s='2', q='8', cone_lambda={})
        report = run_step(graph, terminal_witness=witness,
                          signing_cap=20, sdp_iteration_cap=0)
        self.assertEqual(report['status'], 'certified-step')
        self.assertEqual(verify_report(report)['r_next'], 3)
        self.assertEqual(len(report['proof']['selected_edges']), 3)
        self.assertEqual(report['origin'], 'supplied-terminal-witness')


if __name__ == '__main__':
    unittest.main()
