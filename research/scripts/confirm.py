"""Pinned, serial confirmation; deterministic job order and raw certificates."""
import argparse,csv,datetime,hashlib,json,os,pathlib,random,resource,signal,subprocess,time,sys
from analyze import ROOT,read_hgr
from benchmark import verify
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--solvers',default='dense,uzl');ap.add_argument('--seconds',type=float,default=10);ap.add_argument('--repeat',type=int,default=1);ap.add_argument('--cpu',type=int,default=2);ap.add_argument('--output',default='confirmation');ap.add_argument('--ids');ap.add_argument('--all-private',action='store_true');ap.add_argument('--shard',default='0/1');a=ap.parse_args()
 commands={'dense':[str(ROOT/'bin/dense_v1')],'no_pair':[str(ROOT/'bin/dense'),'--no-pair'],'learn':[str(ROOT/'bin/dense'),'--learn'],'uzl':[str(ROOT/'vendor/uzl/target/release/uzl_hs')],'shadoks':[str(ROOT/'vendor/shadoks/exact')],'bibco':[str(ROOT/'bin/bib_hs')],'biblp':[str(ROOT/'bin/bib_hs'),'lp'],'sat_seq':[str(ROOT/'.venv/bin/python'),str(ROOT/'scripts/sat_baseline.py')],'highs':[str(ROOT/'.venv/bin/python'),str(ROOT/'scripts/milp.py')]}
 commands['portfolio']=[sys.executable,str(ROOT/'scripts/solve.py')]
 commands['portable']=[str(ROOT/'bin/dense_portable')]
 commands['bibco_native']=[sys.executable,str(ROOT/'scripts/bib_direct.py')]
 commands['biblp_native']=[sys.executable,str(ROOT/'scripts/bib_direct.py'),'lp']
 names=a.solvers.split(',');files=[]
 for p in sorted((ROOT/'data/pace2025/private/hs/exact').glob('*.hgr')):
  n,es=read_hgr(p)
  if a.all_private or (n<=512 and len(es)<=512):files.append(p)
 if a.ids:
  ids=set(map(int,a.ids.split(',')));files=[p for p in files if int(p.stem.split('_')[-1]) in ids]
 shard,total=map(int,a.shard.split('/'));files=[p for i,p in enumerate(files) if i%total==shard]
 out=ROOT/'results'/a.output;out.mkdir(exist_ok=False,parents=True)
 hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
 metadata={'utc_start':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cpu':a.cpu,'seconds':a.seconds,'repeat':a.repeat,'job_order_seed':981733,'commands':{k:commands[k] for k in names},'binary_sha256':{k:hashlib.sha256(pathlib.Path(commands[k][0]).read_bytes()).hexdigest() for k in names},'input_sha256':hashes}
 (out/'metadata.json').write_text(json.dumps(metadata,indent=2))
 os.sched_setaffinity(0,{a.cpu})
 jobs=[(rep,p,name) for rep in range(a.repeat) for p in files for name in names];random.Random(981733).shuffle(jobs)
 with (out/'runs.csv').open('w',buffering=1) as f:
  w=csv.DictWriter(f,fieldnames=['instance','solver','repeat','wall_s','cpu_s','status','objective','returncode']);w.writeheader()
  for rep,p,name in jobs:
   n,es=read_hgr(p);tag=f'{p.stem}-{name}-r{rep}'
   before=resource.getrusage(resource.RUSAGE_CHILDREN);start=time.monotonic()
   proc=subprocess.Popen(commands[name],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
   status='error';obj=None
   try:stdout,stderr=proc.communicate(input=p.read_bytes(),timeout=a.seconds)
   except subprocess.TimeoutExpired:
    os.killpg(proc.pid,signal.SIGKILL);stdout,stderr=proc.communicate();status='timeout'
   wall=time.monotonic()-start;after=resource.getrusage(resource.RUSAGE_CHILDREN)
   (out/(tag+'.stdout')).write_bytes(stdout);(out/(tag+'.stderr')).write_bytes(stderr)
   if proc.returncode==0:
    try:
     vals=[int(x) for l in stdout.decode().splitlines() if l.strip() and not l.startswith(('c','o','s')) for x in l.split()]
     sol=vals[1:];obj=vals[0];status='ok' if obj==len(sol) and verify(n,es,sol) else 'invalid'
    except (ValueError,IndexError):status='parse_error'
   cpu=(after.ru_utime+after.ru_stime)-(before.ru_utime+before.ru_stime)
   row=dict(instance=p.stem,solver=name,repeat=rep,wall_s=wall,cpu_s=cpu,status=status,objective=obj,returncode=proc.returncode)
   w.writerow(row);print(json.dumps(row),flush=True)
if __name__=='__main__':main()
