"""Primal/dual proposals for several exactly orthogonal rank-one rays.

Different rays share one SDP variable t. Decimal proposes its value;
only exact rational primal feasibility, dual stationarity/PSD, and the
requested gap authorize a result. Noncommuting rays are rejected here.
"""
from decimal import Decimal, localcontext
from fractions import Fraction as F
from sdp_dual_certificate import sqrt_lower
from sdp_collinear import _certificate


def orthogonal_rays(sdp):
    groups=[]
    for a,x,psi in zip(sdp.a,sdp.x,sdp.psi):
        trace=sum((a[i][i] for i in range(sdp.n)),F())
        if not trace: continue
        r=[[v/trace for v in row] for row in a]
        if any(sum((r[i][k]*r[k][j] for k in range(sdp.n)),F())!=r[i][j]
               for i in range(sdp.n) for j in range(sdp.n)):
            return None
        index=next((k for k,g in enumerate(groups) if g['r']==r),None)
        if index is None:
            if any(any(sum((r[i][k]*g['r'][k][j] for k in range(sdp.n)),F())
                       for i in range(sdp.n) for j in range(sdp.n)) for g in groups):
                return None
            index=len(groups); groups.append(dict(r=r,s=F(),mu=F()))
        groups[index]['s']+=x*trace
        groups[index]['mu']+=sdp.coupling*psi*trace*trace
    return groups or None


def orthogonal_proposal(sdp,bits):
    groups=orthogonal_rays(sdp)
    if groups is None or len(groups)<2:
        return None
    d=sdp.n; nullity=d-len(groups)
    if nullity<0: return None
    precision=max(70,int(bits*0.302)+30)
    def dec(v): return Decimal(v.numerator)/Decimal(v.denominator)
    with localcontext() as ctx:
        ctx.prec=precision
        eps=dec(sdp.epsilon)
        modes=[(dec(g['s']),dec(g['mu'])) for g in groups]
        floor=max((s*s+4*mu).sqrt() for s,mu in modes)
        left=floor+Decimal(10)**(-precision+15)*max(Decimal(1),floor)
        right=Decimal(50)
        if left>=right: return None
        def derivative(t):
            total=Decimal(1)-2*eps*nullity/(t*t)
            for s,mu in modes:
                u=t*t-s*s
                root=(u*(u-4*mu)).sqrt()
                denom=u+root
                rate=2*t+2*t*(u-2*mu)/root
                total+=eps*(4/denom-4*t*rate/(denom*denom))
            return total
        if derivative(left)>=0 or derivative(right)<=0:
            return None
        for _ in range(bits+160):
            middle=(left+right)/2
            if derivative(middle)<0: left=middle
            else: right=middle
        exact=F((left+right)/2)
        scale=1 << bits
        t=F((2*exact.numerator*scale+exact.denominator)//(2*exact.denominator),scale)
    # Decimal only suggests t; assemble the witnesses in rational arithmetic.
    null=1/t
    rest=[[F(int(i==j))-sum((g['r'][i][j] for g in groups),F())
           for j in range(d)] for i in range(d)]
    xm=[[null*v for v in row] for row in rest]
    ym=[[null*v for v in row] for row in rest]
    weights=[]
    for g in groups:
        s,mu=g['s'],g['mu']; u=t*t-s*s
        if u<=4*mu: return None
        k=2/(1+sqrt_lower(1-4*mu/u,bits))
        x,y=k/(t-s),k/(t+s)
        denom=1-mu*mu*x*x*y*y
        if denom<=0: return None
        a=sdp.epsilon*x*x*(1+mu*y*y)/denom
        b=sdp.epsilon*y*y*(1+mu*x*x)/denom
        weights.append((a,b))
        for i in range(d):
            for j in range(d):
                xm[i][j]+=x*g['r'][i][j]; ym[i][j]+=y*g['r'][i][j]
    primal=[t if kind=='t' else (xm if kind=='X' else ym)[i][j] for kind,i,j in sdp.keys]
    if sdp.separate(primal) is not None:
        return None
    c=sdp.epsilon/(t*t)
    total=sum((a+b for a,b in weights),F())+2*nullity*c
    c/=total
    p1=[[c*v for v in row] for row in rest]; p2=[row[:] for row in p1]
    wnull=sqrt_lower(c*sdp.epsilon,bits)
    w1=[[wnull*v for v in row] for row in rest]; w2=[row[:] for row in w1]
    for g,(a,b) in zip(groups,weights):
        a/=total; b/=total
        w_a=sqrt_lower(a*(sdp.epsilon+g['mu']*b),bits)
        w_b=sqrt_lower(b*(sdp.epsilon+g['mu']*a),bits)
        for i in range(d):
            for j in range(d):
                r=g['r'][i][j]
                p1[i][j]+=a*r; p2[i][j]+=b*r
                w1[i][j]+=w_a*r; w2[i][j]+=w_b*r
    return primal,_certificate(sdp,p1,p2,w1,w2)
