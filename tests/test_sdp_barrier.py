import copy
import sys
import unittest
from fractions import Fraction as F
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from appendix_a_value_oracle import AppendixASDP
from rational_ellipsoid import IterationLimitReached
from sdp_dual_certificate import serialize_sdp_value,verify_sdp_value
from sdp_barrier import repair_dual
from sdp_collinear import generic_dual


class NoncommutingSDPTest(unittest.TestCase):
    def problem(self):
        return AppendixASDP([[[F(1,2),F(0)],[F(0),F(0)]],
                            [[F(1,4),F(1,4)],[F(1,4),F(1,4)]]],
                           [F(1,3),F(-1,4)],[F(1),F(2,3)],F(1,3))

    def test_general_interval_and_independent_replay(self):
        sdp=self.problem()
        interval=sdp.value_interval(F(1,10**20),400)
        raw=serialize_sdp_value(sdp,interval,F(1,10**20))
        self.assertGreater(interval.newton_steps,0)
        self.assertEqual(interval.feasibility_calls,0)
        with patch('sdp_barrier.barrier_proposal',side_effect=AssertionError('optimizer')):
            verify_sdp_value(raw)
        bad=copy.deepcopy(raw)
        bad['dual']['multipliers'][0][0][0]='-1'
        with self.assertRaises(ValueError):
            verify_sdp_value(bad)

    def test_cap_is_operational_failure(self):
        with self.assertRaises(IterationLimitReached):
            self.problem().value_interval(F(1,100),0)

    def test_repair_rejects_non_psd_input(self):
        sdp=self.problem()
        z=generic_dual(sdp,64).multipliers
        z[0][0][0]=-1
        with self.assertRaises(ArithmeticError):
            repair_dual(sdp,z)


if __name__=='__main__': unittest.main()
