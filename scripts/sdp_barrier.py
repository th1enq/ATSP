"""Noncommuting SDP proposals, with rational primal and dual verification.

Decimal Newton arithmetic only proposes witnesses. Box multipliers repair
stationarity exactly; neither convergence nor a numeric residual is a proof.
"""
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
from exact_psd import psd_or_negative_vector
from sdp_dual_certificate import DualCertificate, inner, verify_dual


def _solve(a, b):
    a = [list(row)+[value] for row,value in zip(a,b)]
    n = len(b)
    for k in range(n):
        pivot = max(range(k,n), key=lambda i: abs(a[i][k]))
        a[k], a[pivot] = a[pivot], a[k]
        if not a[k][k]:
            raise ArithmeticError('singular Newton system')
        for i in range(k+1,n):
            v = a[i][k]/a[k][k]
            for j in range(k+1,n+1):
                a[i][j] -= v*a[k][j]
            a[i][k] = D(0)
    x = [D(0)]*n
    for i in reversed(range(n)):
        x[i] = (a[i][n]-sum((a[i][j]*x[j] for j in range(i+1,n)),D(0)))/a[i][i]
    return x


def _inverse_logdet(a, need_inverse=True):
    n = len(a)
    l = [[D(int(i==j)) for j in range(n)] for i in range(n)]
    diag = []
    for i in range(n):
        v = a[i][i]-sum((l[i][k]**2*diag[k] for k in range(i)),D(0))
        if v <= 0:
            raise ArithmeticError('outside positive definite cone')
        diag.append(v)
        for j in range(i+1,n):
            l[j][i] = (a[j][i]-sum((l[j][k]*l[i][k]*diag[k] for k in range(i)),D(0)))/v
    logdet = sum((v.ln() for v in diag),D(0))
    if not need_inverse:
        return None,logdet
    inv_l = [[D(int(i==j)) for j in range(n)] for i in range(n)]
    for i in range(n):
        for j in range(i):
            inv_l[i][j] = -sum((l[i][k]*inv_l[k][j] for k in range(j,i)),D(0))
    inv = [[sum((inv_l[k][i]*inv_l[k][j]/diag[k] for k in range(max(i,j),n)),D(0))
            for j in range(n)] for i in range(n)]
    return inv,logdet


def repair_dual(sdp, multipliers):
    """Repair rounded PSD multipliers using the four existing box LMIs."""
    z = [[[F(v) for v in row] for row in a] for a in multipliers]
    if any(not psd_or_negative_vector(a)[0] for a in z):
        raise ArithmeticError('rounded dual multiplier is not PSD')
    scale = sum((inner(a,coeffs[0]) for a,(_,coeffs) in zip(z,sdp.lmis)),F())
    if scale <= 0:
        raise ArithmeticError('nonpositive dual normalization')
    z = [[[v/scale for v in row] for row in a] for a in z]
    residual = [c-sum((inner(a,bases[k]) for a,(_,bases) in zip(z,sdp.lmis)),F())
                for k,c in enumerate(sdp.objective)]
    if residual[0]:
        raise AssertionError('t stationarity normalization failed')
    for kind,lower in [('X',2),('Y',4)]:
        e = [[F() for _ in range(sdp.n)] for _ in range(sdp.n)]
        for k,(name,i,j) in enumerate(sdp.keys):
            if name == kind:
                e[i][j] = e[j][i] = residual[k]/(1 if i==j else 2)
        radius = max(sum(map(abs,row),F()) for row in e)
        correction = [[e[i][j]+radius*int(i==j) for j in range(sdp.n)] for i in range(sdp.n)]
        if not psd_or_negative_vector(correction)[0]:
            raise AssertionError('diagonal dominance repair failed')
        for i in range(sdp.n):
            for j in range(sdp.n):
                z[lower][i][j] += correction[i][j]
            z[lower+1][i][i] += radius
    cert = DualCertificate(z,-sum((inner(a,c) for a,(c,_) in zip(z,sdp.lmis)),F()))
    verify_dual(sdp.lmis,sdp.objective,cert)
    return cert


def barrier_proposal(sdp, accuracy, max_iterations=None):
    """Solve any affine orientation; return only exactly certified intervals.

    Iteration limits count Newton steps here, independently of ellipsoid cuts.
    No closed-form commuting decomposition is assumed.
    """
    from rational_ellipsoid import IterationLimitReached
    bits = max(96,accuracy.denominator.bit_length()+sdp.epsilon.denominator.bit_length()+96)
    precision = max(90,2*int(bits*.302)+50)
    with localcontext() as context:
        context.prec = precision
        decimal = lambda v: D(v.numerator)/D(v.denominator)
        objective = [decimal(v) for v in sdp.objective]
        blocks = []
        for c,bases in sdp.lmis:
            n = len(c)
            entries = [(k,[(i,j,decimal(a[i][j])) for i in range(n) for j in range(n) if a[i][j]])
                       for k,a in enumerate(bases) if any(any(row) for row in a)]
            blocks.append(([[decimal(v) for v in row] for row in c],entries))
        point = [decimal(v) for v in sdp.strict_reference_point()]
        target_mu = decimal(accuracy)/(1000*sum(len(c) for c,_ in blocks))
        mu = D(1)
        steps = 0
        step_cap = max_iterations if max_iterations is not None else 100*(precision+sdp.dimension)

        def evaluate(u, derivatives=False):
            gradient = list(objective)
            hessian = [[D(0) for _ in u] for _ in u]
            value = sum((v*c for v,c in zip(u,objective)),D(0))
            inverses = []
            for constant,entries in blocks:
                n = len(constant)
                a = [list(row) for row in constant]
                for k,terms in entries:
                    for i,j,v in terms:
                        a[i][j] += u[k]*v
                inv,logdet = _inverse_logdet(a,derivatives)
                inverses.append(inv)
                value -= mu*logdet
                if not derivatives:
                    continue
                products = []
                for k,terms in entries:
                    gradient[k] -= mu*sum((inv[j][i]*v for i,j,v in terms),D(0))
                    product = [[D(0) for _ in range(n)] for _ in range(n)]
                    for i,j,v in terms:
                        for row in range(n):
                            product[row][j] += inv[row][i]*v
                    products.append((k,product))
                for idx,(k,a) in enumerate(products):
                    for ell,b in products[idx:]:
                        v = mu*sum((a[i][j]*b[j][i] for i in range(n) for j in range(n)),D(0))
                        hessian[k][ell] += v
                        if k != ell:
                            hessian[ell][k] += v
            if not 0 < u[0] < 100:
                raise ArithmeticError('outside t box')
            value -= mu*(u[0].ln()+(100-u[0]).ln())
            if derivatives:
                gradient[0] += mu*(-1/u[0]+1/(100-u[0]))
                hessian[0][0] += mu*(1/u[0]**2+1/(100-u[0])**2)
            return value,gradient,hessian,inverses

        while True:
            value,gradient,hessian,inverses = evaluate(point,True)
            direction = _solve(hessian,[-v for v in gradient])
            decrement = -sum((v*g for v,g in zip(direction,gradient)),D(0))
            # Accuracy of stationarity must absorb the large box constants.
            centered = decrement <= mu*D('1e-35')
            if mu <= target_mu:
                centered = centered and max(map(abs,gradient)) <= target_mu*D('1e-10')
            if centered:
                if mu <= target_mu:
                    break
                mu = max(target_mu,mu/D(10))
                continue
            if steps >= step_cap:
                raise IterationLimitReached('noncommuting SDP Newton iteration cap reached')
            alpha = D(1)
            for _ in range(512):
                candidate = [v+alpha*d for v,d in zip(point,direction)]
                try:
                    new_value = evaluate(candidate)[0]
                    if new_value <= value-alpha*decrement/D(100):
                        point = candidate
                        break
                except ArithmeticError:
                    pass
                alpha /= 2
            else:
                raise ArithmeticError('SDP Newton line search stalled')
            steps += 1
        scale = 1 << bits
        rational = lambda v: F(int(v*scale),scale)
        primal = [rational(v) for v in point]
        if sdp.separate(primal) is not None:
            raise ArithmeticError('rounded primal failed exact feasibility')
        multipliers = [[[rational(mu*v) for v in row] for row in inv] for inv in inverses]
        cert = repair_dual(sdp,multipliers)
        gap = sdp.objective_value(primal)-cert.bound
        if not 0 <= gap <= accuracy:
            raise ArithmeticError('rounded primal-dual gap exceeds requested accuracy')
        return primal,cert,steps
