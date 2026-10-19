"""Reduce official instances and record cheap structural bounds (no tuning)."""
import csv, json, subprocess, pathlib, time
ROOT = pathlib.Path(__file__).resolve().parents[1]
def read_hgr(path):
    edges=[]; n=0
    for line in path.read_text().splitlines():
        t=line.split()
        if not t or t[0]=='c': continue
        if t[0]=='p': n=int(t[2]); continue
        edges.append(tuple(map(int,t)))
    return n, edges
def packing(n,edges):
    deg=[0]*(n+1)
    for e in edges:
        for v in e: deg[v]+=1
    order=sorted(range(len(edges)),key=lambda i:(sum(deg[v] for v in edges[i]),len(edges[i]),i))
    used=set(); p=[]
    for i in order:
        if not used.intersection(edges[i]): p.append(i); used.update(edges[i])
    return p,used
def main():
    rows=[]
    for path in sorted((ROOT/'data/pace2025/hs/exact').glob('*.hgr')):
        t=time.monotonic()
        r=subprocess.run([str(ROOT/'bin/presolve')],input=path.read_bytes(),capture_output=True,check=True)
        out=ROOT/'data/reduced'/path.name
        out.write_bytes(r.stdout);out.with_suffix('.map').write_bytes(r.stderr)
        n,edges=read_hgr(out); pn,pe=read_hgr(path)
        pack,used=packing(n,edges)
        row=dict(instance=path.stem,original_n=pn,original_m=len(pe),n=n,m=len(edges),incidences=sum(map(len,edges)),packing=len(pack),packed_vertices=len(used),pair_edges=sum(len(e)==2 for e in edges),preprocess_s=time.monotonic()-t)
        rows.append(row)
    with (ROOT/'results/structure.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
