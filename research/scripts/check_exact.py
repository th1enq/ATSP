"""Independent brute-force oracle for the experimental exact solvers."""
import itertools, random, subprocess, json
from analyze import ROOT
rng=random.Random(20261019)
cases=[]
for n in range(1,13):
    for rep in range(25):
        edges=[rng.sample(range(1,n+1),rng.randint(1,n)) for _ in range(rng.randrange(0,2*n+1))]
        cases.append((n,edges))
commands=[[str(ROOT/'bin/dense')],[str(ROOT/'bin/dense'),'--learn'],[str(ROOT/'bin/dense'),'--no-pair'],[str(ROOT/'bin/contract'),'contract'],[str(ROOT/'bin/contract')]]
for idx,(n,edges) in enumerate(cases):
    optimum=next(k for k in range(n+1) if any(all(set(s).intersection(e) for e in edges) for s in itertools.combinations(range(1,n+1),k)))
    data=f'p hs {n} {len(edges)}\n'+''.join(' '.join(map(str,e))+'\n' for e in edges)
    for cmd in commands:
        p=subprocess.run(cmd,input=data,text=True,capture_output=True,timeout=10,check=True)
        vals=list(map(int,p.stdout.split()));assert vals[0]==optimum,(idx,cmd,optimum,p.stdout)
        sol=vals[1:];assert len(sol)==len(set(sol))==vals[0] and all(set(sol).intersection(e) for e in edges)
print(json.dumps({'cases':len(cases),'solver_configurations':len(commands),'verified_runs':len(commands)*len(cases),'seed':20261019,'result':'passed'}))
