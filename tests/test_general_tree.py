import copy
import sys
import unittest
from fractions import Fraction as F
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from general_tree import build_tree,verify_tree_report,instance_g
from general_sparsification import run_step,verify_report
from continuation_solver import schedule_budget
from continuation_state import initial_state


class GeneralTreeTest(unittest.TestCase):
    def test_source_cutoff_tree_and_tamper(self):
        graph=dict(n=3,edges=[[0,1],[1,2],[0,2]]*8,r=8)
        report=build_tree(graph)
        self.assertEqual(verify_tree_report(report)['rounds'],0)
        self.assertEqual(report['cut_ratio_bound'],'1/4')
        bad=copy.deepcopy(report);bad['tree']=[0,0]
        with self.assertRaises(ValueError): verify_tree_report(bad)
        bad=copy.deepcopy(report);bad['cut_ratio_bound']='0'
        with self.assertRaises(ValueError): verify_tree_report(bad)

    def test_instance_budget_preserves_target(self):
        graph=dict(n=3,edges=[[0,1],[1,2],[0,2]]*8,r=8)
        g=instance_g(graph)
        state=initial_state(3,[tuple(e) for e in graph['edges']],8,g)
        _,q=schedule_budget(state)
        self.assertGreaterEqual(q,F(7*8,8))

    def test_complete_chain_maps_edges_and_replays_without_solvers(self):
        graph=dict(n=2,edges=[[0,1]]*8,r=8)
        report=build_tree(graph,mode='instance',signing_method='certified-tree-candidate',
                          max_response_iterations=0)
        self.assertEqual(report['status'],'certified-tree')
        self.assertEqual(len(report['steps']),1)
        with patch('general_sparsification.solve_response',side_effect=AssertionError('solver')), \
             patch('general_sparsification.automatic_sparsification_step',side_effect=AssertionError('signer')):
            self.assertEqual(verify_tree_report(report)['retained_r'],3)
        bad=copy.deepcopy(report);bad['steps'][0]['graph']['edges'][0]=[0,0]
        with self.assertRaises(ValueError): verify_tree_report(bad)
        bad=copy.deepcopy(report);bad['mode']='source'
        with self.assertRaises(ValueError): verify_tree_report(bad)

    def test_source_diagnostic_rejects_exhausted_schedule(self):
        graph=dict(n=2,edges=[[0,1]]*8,r=8)
        with patch('general_sparsification.solve_response',side_effect=AssertionError('response')):
            report=run_step(graph,below_cutoff=True)
        self.assertEqual(report['status'],'incomplete')
        self.assertIn('exhausts Q',report['error'])
        self.assertEqual(verify_report(report)['verified_responses'],0)
        report['schedule_budget']['terminal_q']='1'
        with self.assertRaises(ValueError): verify_report(report)

    def test_instance_prefix_cannot_be_relabeled_as_source(self):
        graph=dict(n=2,edges=[[0,1]]*8,r=8)
        report=run_step(graph,continuation_g=F(1,64),max_steps=1,max_response_iterations=0)
        self.assertEqual(verify_report(report)['verified_responses'],1)
        bad=copy.deepcopy(report);bad['origin']='source-initial-state'
        with self.assertRaises(ValueError): verify_report(bad)


if __name__=='__main__': unittest.main()
