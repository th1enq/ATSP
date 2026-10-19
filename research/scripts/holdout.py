"""Fresh WS instances after freezing dense_v1; supplementary, not PACE data."""
import csv,hashlib,itertools,json,os,pathlib,random,signal,subprocess,sys,time
import networkx as nx
from analyze import ROOT,read_hgr
from benchmark import verify
def generate():
 out=ROOT/'data/holdout';out.mkdir(exist_ok=True);rows=[]
 for idx,(n,fraction,p) in enumerate(itertools.product([200,300],[0.2,0.5],[0.1,0.5])):
  k=int(n*fraction);k-=k%2;seed=2026101901+idx;g=nx.watts_strogatz_graph(n,k,p,seed=seed)
  # Independently permute vertex and edge labels; do not expose a ring ordering.
  rng=random.Random(seed+1000);order=list(range(1,n+1));rng.shuffle(order)
  es=[sorted(order[v] for v in set(g.neighbors(u))|{u}) for u in range(n)];rng.shuffle(es)
  name=f'holdout_{idx:02d}';path=out/(name+'.hgr');path.write_text(f'p hs {n} {len(es)}\n'+''.join(' '.join(map(str,e))+'\n' for e in es))
  rows.append(dict(instance=name,n=n,k=k,p=p,seed=seed,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
 (out/'metadata.json').write_text(json.dumps({'networkx':nx.__version__,'frozen_binary_sha256':hashlib.sha256((ROOT/'bin/dense_v1').read_bytes()).hexdigest(),'instances':rows},indent=2))
 print('generated',len(rows),'fresh instances')
def run(shard):
 os.sched_setaffinity(0,{6+shard});out=ROOT/'results'/f'holdout-shard{shard}';out.mkdir(exist_ok=False)
 commands={'dense':[str(ROOT/'bin/dense_v1')],'uzl':[str(ROOT/'vendor/uzl/target/release/uzl_hs')]}
 jobs=[(p,name) for i,p in enumerate(sorted((ROOT/'data/holdout').glob('*.hgr'))) if i%2==shard for name in commands];random.Random(130+shard).shuffle(jobs)
 with (out/'runs.csv').open('w',buffering=1) as f:
  w=csv.DictWriter(f,fieldnames=['instance','solver','status','objective','seconds']);w.writeheader()
  for p,name in jobs:
   n,es=read_hgr(p);start=time.monotonic();proc=subprocess.Popen(commands[name],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True);obj=None;status='timeout'
   try:
    stdout,stderr=proc.communicate(p.read_bytes(),timeout=10)
    if proc.returncode==0:
     vals=list(map(int,stdout.split()));obj=vals[0];assert len(vals)==obj+1 and verify(n,es,vals[1:]);status='ok'
    else:status='error'
   except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);stdout,stderr=proc.communicate()
   elapsed=time.monotonic()-start;tag=p.stem+'-'+name;(out/(tag+'.stdout')).write_bytes(stdout);(out/(tag+'.stderr')).write_bytes(stderr)
   row=dict(instance=p.stem,solver=name,status=status,objective=obj,seconds=elapsed);w.writerow(row);print(json.dumps(row),flush=True)
if __name__=='__main__':
 if sys.argv[1]=='generate':generate()
 else:run(int(sys.argv[1]))
