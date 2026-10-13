import copy
import sys
import unittest
from fractions import Fraction as F
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from appendix_a_value_oracle import AppendixASDP, UncertifiedSDPBound
from rational_ellipsoid import VolumeCutoffReached
from sdp_dual_certificate import (verify_dual, serialize_dual, load_dual,
                                  serialize_sdp_value, verify_sdp_value)
from sdp_collinear import generic_dual, collinear_proposal


class SDPDualCertificateTest(unittest.TestCase):
    def test_scalar_known_optimum_without_ellipsoid(self):
        sdp=AppendixASDP([[[F(1)]]],[F(0)],[F(0)],F(1))
        with patch('appendix_a_value_oracle.find_feasible',side_effect=AssertionError('solver')):
            interval=sdp.value_interval(F(1,1000000))
        self.assertEqual(interval.feasibility_calls,0)
        self.assertLessEqual(interval.lower**2,8)
        self.assertGreaterEqual(interval.upper**2,8)
        self.assertLessEqual(interval.upper-interval.lower,F(1,1000000))
        raw=serialize_sdp_value(sdp,interval,F(1,1000000))
        with patch('appendix_a_value_oracle.find_feasible',side_effect=AssertionError('solver')):
            verify_sdp_value(raw)

    def test_rotated_collinear_and_signed_queries(self):
        projector=[[F(9,25),F(12,25)],[F(12,25),F(16,25)]]
        matrices=[[[v*weight for v in row] for row in projector] for weight in (F(1,3),F(2,3))]
        for x in ([F(0),F(0)],[F(1),F(-1)],[F(1,2),F(1,3)]):
            sdp=AppendixASDP(matrices,x,[F(1,2),F(3,4)],F(1,5))
            interval=sdp.value_interval(F(1,10000),max_feasibility_iterations=0)
            self.assertEqual(interval.feasibility_calls,0)
            verify_sdp_value(serialize_sdp_value(sdp,interval,F(1,10000)))

    def test_general_dual_does_not_need_collinearity(self):
        sdp=AppendixASDP([[[F(1,2),F(0)],[F(0),F(0)]],
                         [[F(1,4),F(1,4)],[F(1,4),F(1,4)]]],
                         [F(1,2),F(-1,2)],[F(1),F(1,3)],F(1,3))
        self.assertIsNone(collinear_proposal(sdp,64))
        certificate=generic_dual(sdp,64)
        low=verify_dual(sdp.lmis,sdp.objective,load_dual(serialize_dual(certificate)))
        self.assertGreater(low,0)
        self.assertLessEqual(low,sdp.objective_value(sdp.strict_reference_point()))

    def test_tampered_dual_is_rejected(self):
        sdp=AppendixASDP([[[F(1)]]],[F(0)],[F(0)],F(1))
        certificate=generic_dual(sdp,64)
        bad=copy.deepcopy(certificate); bad.multipliers[0][0][0]=-1
        with self.assertRaisesRegex(ValueError,'PSD'):
            verify_dual(sdp.lmis,sdp.objective,bad)
        bad=copy.deepcopy(certificate); bad.multipliers[0][0][0]+=1
        with self.assertRaisesRegex(ValueError,'stationarity'):
            verify_dual(sdp.lmis,sdp.objective,bad)
        bad=copy.deepcopy(certificate); bad.bound+=1
        with self.assertRaisesRegex(ValueError,'bound'):
            verify_dual(sdp.lmis,sdp.objective,bad)

    def test_volume_without_dual_cannot_update_interval(self):
        sdp=AppendixASDP([[[F(1,2),F(0)],[F(0),F(0)]],
                         [[F(1,4),F(1,4)],[F(1,4),F(1,4)]]],
                         [F(0),F(0)],[F(1),F(1)],F(1,3))
        # Force a valid but weak proposal to exercise the retained ellipsoid path.
        with patch('appendix_a_value_oracle.orthogonal_proposal',
                   return_value=(sdp.strict_reference_point(),generic_dual(sdp,64))), \
             patch('appendix_a_value_oracle.find_feasible',side_effect=VolumeCutoffReached('collapse')):
            with self.assertRaises(UncertifiedSDPBound):
                sdp.value_interval(F(1,100))

    def test_primal_and_endpoint_tampering(self):
        sdp=AppendixASDP([[[F(1)]]],[F(0)],[F(0)],F(1))
        interval=sdp.value_interval(F(1,1000))
        raw=serialize_sdp_value(sdp,interval,F(1,1000))
        bad=copy.deepcopy(raw); bad['primal'][0]='0'
        with self.assertRaisesRegex(ValueError,'infeasible'):
            verify_sdp_value(bad)
        bad=copy.deepcopy(raw); bad['upper']='0'
        with self.assertRaisesRegex(ValueError,'endpoints'):
            verify_sdp_value(bad)


if __name__=='__main__':
    unittest.main()
