import sys
import unittest
from fractions import Fraction as F
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from appendix_a_value_oracle import AppendixASDP
from sdp_orthogonal import orthogonal_rays,orthogonal_proposal
from sdp_dual_certificate import serialize_sdp_value,verify_sdp_value


class OrthogonalSDPTest(unittest.TestCase):
    def test_two_rays_known_optimum(self):
        matrices=[[[F(1,2),F(0)],[F(0),F(0)]],[[F(0),F(0)],[F(0),F(1,2)]]]
        sdp=AppendixASDP(matrices,[F(0),F(0)],[F(1),F(1)],F(1,3))
        self.assertEqual(len(orthogonal_rays(sdp)),2)
        with patch('appendix_a_value_oracle.find_feasible',side_effect=AssertionError('ellipsoid')):
            interval=sdp.value_interval(F(1,10**10))
        # Symmetric case: min (96+4 epsilon)*x+1/x = 2 sqrt(96+4 epsilon).
        optimum_squared=4*(96+F(4,3))
        self.assertLessEqual(interval.lower**2,optimum_squared)
        self.assertGreaterEqual(interval.upper**2,optimum_squared)
        self.assertEqual(interval.feasibility_calls,0)
        verify_sdp_value(serialize_sdp_value(sdp,interval,F(1,10**10)))

    def test_rotated_distinct_rays_signed_and_unequal_weights(self):
        first=[[F(9,25),F(12,25)],[F(12,25),F(16,25)]]
        second=[[F(int(i==j))-first[i][j] for j in range(2)] for i in range(2)]
        matrices=[[[v/3 for v in row] for row in first],[[2*v/3 for v in row] for row in second]]
        for psi in ([F(1,2),F(3,4)],[F(0),F(1)],[F(0),F(0)]):
            sdp=AppendixASDP(matrices,[F(1),F(-1)],psi,F(1,5))
            interval=sdp.value_interval(F(1,10**10),max_feasibility_iterations=0)
            verify_sdp_value(serialize_sdp_value(sdp,interval,F(1,10**10)))

    def test_nonorthogonal_rays_are_rejected(self):
        sdp=AppendixASDP([[[F(1,2),F(0)],[F(0),F(0)]],
                         [[F(1,4),F(1,4)],[F(1,4),F(1,4)]]],
                         [F(0),F(0)],[F(1),F(1)],F(1,3))
        self.assertIsNone(orthogonal_rays(sdp))
        self.assertIsNone(orthogonal_proposal(sdp,100))

    def test_coupling_matches_dense_for_rank_one_and_rank_two(self):
        matrices=[[[F(1,4),F(0)],[F(0),F(1,4)]],
                  [[F(1,4),F(1,4)],[F(1,4),F(1,4)]]]
        sdp=AppendixASDP(matrices,[F(0),F(0)],[F(1,3),F(2,3)],F(1,3))
        basis=[[F(1),F(-2)],[F(-2),F(3)]]
        expected=[[384*sum((weight*sum((a[i][u]*basis[u][v]*a[v][j]
                    for u in range(2) for v in range(2)),F())
                    for a,weight in zip(sdp.a,sdp.psi)),F())
                    for j in range(2)] for i in range(2)]
        self.assertEqual(sdp._coupling_on_basis(basis),expected)


if __name__=='__main__':
    unittest.main()
