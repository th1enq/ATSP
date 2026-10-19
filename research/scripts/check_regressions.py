"""Known-optimum cases across 64-bit boundaries and portfolio fallbacks."""
import json,random,subprocess,sys
from analyze import ROOT
from benchmark import verify
rng=random.Random(1019);cases=[]
for n in [1,13,63,64,65,127,128,129,255,256,257,511,512]:
    for m in [1,63,64,65,127,128,129,255,256,257,511,512]:
        k=min(n,m,7);picks=rng.sample(range(1,n+1),k);edges=[[v] for v in picks]
        for _ in range(m-k):
            e=set(rng.sample(range(1,n+1),min(n,rng.randint(1,12))));e.add(rng.choice(picks));edges.append(sorted(e))
        rng.shuffle(edges);cases.append((n,edges,k))
commands=[[str(ROOT/'bin/dense_v1')],[str(ROOT/'bin/dense_portable')]]
checked=0
for n,edges,k in cases:
    data=f'p hs {n} {len(edges)}\n'+''.join(' '.join(map(str,e))+'\n' for e in edges)
    for cmd in commands:
        p=subprocess.run(cmd,input=data,text=True,capture_output=True,timeout=10,check=True);v=list(map(int,p.stdout.split()));assert v[0]==k and len(v)==k+1 and verify(n,edges,v[1:]);checked+=1
for n,edges,k in [(513,[[513]],1),(3,[[1]]*513,1),(512,[[1,512]],1),(0,[],0),(2,[[1],[2]],2)]:
    data=f'c parser robustness\np   hs   {n}   {len(edges)}\n\n'+''.join('  '.join(map(str,e))+' \n' for e in edges)
    p=subprocess.run([sys.executable,str(ROOT/'scripts/solve.py')],input=data,text=True,capture_output=True,timeout=10,check=True);v=list(map(int,p.stdout.split()));assert v[0]==k and len(v)==k+1 and verify(n,edges,v[1:]);checked+=1
result={'seed':1019,'boundary_cases':len(cases),'fallback_cases':5,'verified_runs':checked,'result':'passed'}
print(json.dumps(result))
