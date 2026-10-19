"""Metamorphic check: vertex labels, edge order and within-edge order."""
import csv,json,os,random,subprocess,time
from analyze import ROOT,read_hgr
from benchmark import verify
os.sched_setaffinity(0,{6});rng=random.Random(746193)
references={r['instance']:int(r['objective']) for r in csv.DictReader((ROOT/'results/dense-v1-private/runs.csv').open()) if r['status']=='ok'}
out=ROOT/'results/permutations';out.mkdir(exist_ok=True)
ids=[1,36,41,43,45,47,48,96];rows=[]
for idx in ids:
 stem=f'private_exact_{idx:03d}';n,original=read_hgr(ROOT/'data/pace2025/private/hs/exact'/(stem+'.hgr'))
 for repeat in range(3):
  order=list(range(1,n+1));rng.shuffle(order);edges=[[order[v-1] for v in e] for e in original];rng.shuffle(edges)
  for e in edges:rng.shuffle(e)
  data=f'p hs {n} {len(edges)}\n'+''.join(' '.join(map(str,e))+'\n' for e in edges)
  tag=f'{stem}-perm{repeat}';(out/(tag+'.hgr')).write_text(data)
  start=time.monotonic();status='timeout';obj=None
  try:
   p=subprocess.run([str(ROOT/'bin/dense_v1')],input=data,text=True,capture_output=True,timeout=10,check=True);elapsed=time.monotonic()-start;vals=list(map(int,p.stdout.split()));obj=vals[0];assert obj==references[stem] and len(vals)==obj+1 and verify(n,edges,vals[1:]);status='ok';(out/(tag+'.solution')).write_text(p.stdout)
  except subprocess.TimeoutExpired:elapsed=time.monotonic()-start
  row=dict(instance=stem,repeat=repeat,status=status,objective=obj,seconds=elapsed);rows.append(row);print(json.dumps(row),flush=True)
with (out/'runs.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
(out/'metadata.json').write_text(json.dumps({'seed':746193,'cpu':6,'timeout_s':10,'test':'independent permutations of vertices and edge orders'},indent=2))
