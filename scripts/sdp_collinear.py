"""Certified proposals for SDP inputs whose nonzero matrices share one ray.

Floats propose a primal point and dual weights. Only exact rational LMI,
stationarity, and gap checks can authorize a returned value interval.
The generic certificate uses P=I/(2d) and does not need this special case.
"""
from fractions import Fraction as F
from math import sqrt, isfinite
from sdp_dual_certificate import DualCertificate, inner, sqrt_lower, verify_dual


def _zero(n):
    return [[F() for _ in range(n)] for _ in range(n)]


def _combine(projector, support, complement):
    return [[support*projector[i][j]+complement*(int(i==j)-projector[i][j])
             for j in range(len(projector))] for i in range(len(projector))]


def _block(p,q,w):
    n=len(p); z=_zero(2*n)
    for i in range(n):
        for j in range(n):
            z[i][j]=p[i][j]; z[n+i][n+j]=q[i][j]
            z[i][n+j]=z[n+j][i]=-w[i][j]
    return z


def _certificate(sdp, p1,p2,w1,w2):
    fp1,fp2=sdp._coupling_on_basis(p1),sdp._coupling_on_basis(p2)
    q1=[[sdp.epsilon*int(i==j)+fp2[i][j]
         for j in range(sdp.n)] for i in range(sdp.n)]
    q2=[[sdp.epsilon*int(i==j)+fp1[i][j]
         for j in range(sdp.n)] for i in range(sdp.n)]
    zs=[_block(p1,q1,w1),_block(p2,q2,w2)]
    zs += [_zero(len(c)) for c,_ in sdp.lmis[2:]]
    cert=DualCertificate(zs,-sum((inner(z,c) for z,(c,_) in zip(zs,sdp.lmis)),F()))
    verify_dual(sdp.lmis,sdp.objective,cert)
    return cert


def generic_dual(sdp, bits):
    p=[[F(int(i==j),2*sdp.n) for j in range(sdp.n)] for i in range(sdp.n)]
    wvalue=sqrt_lower(sdp.epsilon/F(2*sdp.n),bits)
    w=[[wvalue*int(i==j) for j in range(sdp.n)] for i in range(sdp.n)]
    return _certificate(sdp,p,p,w,w)


def collinear_proposal(sdp, bits):
    traces=[sum((a[i][i] for i in range(sdp.n)),F()) for a in sdp.a]
    index=next((i for i,tr in enumerate(traces) if tr),None)
    if index is None:
        return None
    projector=[[v/traces[index] for v in row] for row in sdp.a[index]]
    if any(a[i][j] != tr*projector[i][j] for a,tr in zip(sdp.a,traces)
           for i in range(sdp.n) for j in range(sdp.n)):
        return None
    if any(sum((projector[i][k]*projector[k][j] for k in range(sdp.n)),F()) != projector[i][j]
           for i in range(sdp.n) for j in range(sdp.n)):
        return None  # common matrices must have rank one
    mu=sdp.coupling*sum((p*tr*tr for p,tr in zip(sdp.psi,traces)),F())
    s=sum((x*tr for x,tr in zip(sdp.x,traces)),F())
    try:
        mf,sf,ef=float(mu),float(s),float(sdp.epsilon)
        if ef <= 0 or not all(isfinite(v) for v in (mf,sf,ef)):
            return None
        lo,hi=1/400,200/ef
        def point(z):
            delta=2*sf/(mf+1/(z*z))
            larger=(sqrt(delta*delta+4*z*z)+abs(delta))/2
            smaller=z*z/larger
            x,y=(larger,smaller) if delta>=0 else (smaller,larger)
            t=max(sf+mf*y+1/x,-sf+mf*x+1/y)
            null=max(lo,1/t)
            return x,y,t,null
        def objective(z):
            x,y,t,null=point(z)
            return t+ef*(x+y+2*(sdp.n-1)*null)
        # This search is a proposal, not a claim about the optimizer.
        left,right=lo,min(hi,4/sqrt(mf+2*ef)+1)
        for _ in range(100):
            a=left+(right-left)/3; b=right-(right-left)/3
            if objective(a)<objective(b): right=b
            else: left=a
        xf,yf,_,_=point((left+right)/2)
        scale=1 << bits
        def dyadic(value):
            exact=F(value)
            return F((2*exact.numerator*scale+exact.denominator)//(2*exact.denominator),scale)
        x,y=dyadic(xf),dyadic(yf)
        if x<=0 or y<=0: return None
        t=max(s+mu*y+1/x,-s+mu*x+1/y)
        null=max(F(1,400),1/t)
        xm=_combine(projector,x,null); ym=_combine(projector,y,null)
        primal=[t if kind=='t' else (xm if kind=='X' else ym)[i][j] for kind,i,j in sdp.keys]
        if sdp.separate(primal) is not None:
            return None
        # Complementarity suggests support weights. Normalize them exactly
        # so Tr(P1+P2)=1; the checker proves all stationarity equations.
        denom=1-mu*mu*x*x*y*y
        if denom<=0: return primal,None
        a=sdp.epsilon*x*x*(1+mu*y*y)/denom
        b=sdp.epsilon*y*y*(1+mu*x*x)/denom
        c=sdp.epsilon/(t*t)
        total=a+b+2*(sdp.n-1)*c
        a,b,c=a/total,b/total,c/total
        p1=_combine(projector,a,c); p2=_combine(projector,b,c)
        w1=_combine(projector,sqrt_lower(a*(sdp.epsilon+mu*b),bits),sqrt_lower(c*sdp.epsilon,bits))
        w2=_combine(projector,sqrt_lower(b*(sdp.epsilon+mu*a),bits),sqrt_lower(c*sdp.epsilon,bits))
        return primal,_certificate(sdp,p1,p2,w1,w2)
    except (OverflowError,ValueError,ZeroDivisionError):
        return None
