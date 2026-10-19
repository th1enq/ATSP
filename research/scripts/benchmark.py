"""Serial subprocess benchmark, raw certificates, independent feasibility checks."""
import argparse, csv, json, pathlib, subprocess, time, random, os, signal
from analyze import ROOT,read_hgr
def verify(n,edges,solution):
    return len(set(solution))==len(solution) and all(1<=v<=n for v in solution) and all(set(e).intersection(solution) for e in edges)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--solver',required=True);ap.add_argument('--seconds',type=float,default=10);ap.add_argument('--ids',default='all');ap.add_argument('--output',required=True);ap.add_argument('--format',choices=['pace','findminhs'],default='pace');ap.add_argument('--repeat',type=int,default=1);ap.add_argument('--seed',type=int,default=817);ap.add_argument('--reduced',action='store_true');ap.add_argument('--private',action='store_true');a=ap.parse_args()
    files=sorted((ROOT/('data/reduced' if a.reduced else ('data/pace2025/private/hs/exact' if a.private else 'data/pace2025/hs/exact'))).glob('*.hgr'))
    if a.ids!='all':
        ids=set(int(x) for x in a.ids.split(','));files=[f for f in files if int(f.stem.split('_')[-1]) in ids]
    out=ROOT/'results'/a.output;out.mkdir(parents=True,exist_ok=True)
    jobs=[(r,f) for r in range(a.repeat) for f in files];random.Random(a.seed).shuffle(jobs)
    with (out/'runs.csv').open('w',buffering=1) as csvout:
        w=csv.DictWriter(csvout,fieldnames=['instance','repeat','seconds','status','objective','returncode']);w.writeheader()
        for rep,path in jobs:
            n,edges=read_hgr(path);stem=f'{path.stem}-r{rep}'
            cmd=a.solver.split();input_data=path.read_bytes()
            if a.format=='findminhs':
                converted=out/(stem+'.json');converted.write_text(json.dumps(dict(num_nodes=n,edges=[[v-1 for v in e] for e in edges])))
                cmd += ['solve',str(converted),str(ROOT/'vendor/findminhs/settings.json'),'-j','-s',str(out/(stem+'.solution.json')),'-r',str(out/(stem+'.report.json'))];input_data=None
            t=time.monotonic();status='error';rc=None;obj=None
            try:
                p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
                try: stdout,stderr=p.communicate(input=input_data,timeout=a.seconds)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate();raise subprocess.TimeoutExpired(cmd,a.seconds,stdout,stderr)
                elapsed=time.monotonic()-t;rc=p.returncode
                (out/(stem+'.stdout')).write_bytes(stdout);(out/(stem+'.stderr')).write_bytes(stderr)
                if rc==0:
                    if a.format=='findminhs': sol=[v+1 for v in json.loads((out/(stem+'.solution.json')).read_text())]
                    else:
                        lines=[l.strip() for l in stdout.decode().splitlines() if l.strip() and not l.startswith(('c','o','s'))]
                        vals=[int(x) for l in lines for x in l.split()];sol=vals[1:]
                        assert vals[0]==len(sol),stdout
                    status='ok' if verify(n,edges,sol) else 'invalid';obj=len(sol)
            except subprocess.TimeoutExpired as e:
                elapsed=time.monotonic()-t;status='timeout';(out/(stem+'.stderr')).write_bytes(e.stderr or b'')
            row=dict(instance=path.stem,repeat=rep,seconds=elapsed,status=status,objective=obj,returncode=rc)
            w.writerow(row);print(json.dumps(row),flush=True)
if __name__=='__main__':main()
