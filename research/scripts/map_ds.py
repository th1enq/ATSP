"""Find and VERIFY equivalence to released DS instances despite relabelling.

Joint color refinement proposes a mapping; exact neighborhood multiset equality
checks it. Failure to find a mapping makes no claim of non-isomorphism.
"""
from collections import Counter,defaultdict
import json,pathlib
from analyze import ROOT,read_hgr
def signature(edges,n):return tuple(sorted(map(len,edges)))
def refine_map(a,b,n):
 graphs=[]
 for es in [a,b]:
  adj=[[] for _ in range(2*n)]
  for i,e in enumerate(es):
   for v in e:adj[i].append(n+v-1);adj[n+v-1].append(i)
  graphs.append(adj)
 colors=[[((i>=n),len(adj[i])) for i in range(2*n)] for adj in graphs]
 for _ in range(8):
  lookup={};new=[]
  for adj,col in zip(graphs,colors):
   cc=[]
   for i in range(2*n):
    sig=(col[i],tuple(sorted(col[j] for j in adj[i])))
    if sig not in lookup:lookup[sig]=len(lookup)
    cc.append(lookup[sig])
   new.append(cc)
  if Counter(new[0])!=Counter(new[1]):return None
  colors=new
  if len(set(new[0]))==2*n:break
 pools=[defaultdict(list),defaultdict(list)]
 for gi,col in enumerate(colors):
  for v,c in enumerate(col[n:]):pools[gi][c].append(v+1)
 mapping={}
 for c,vs in pools[0].items():
  for v,w in zip(vs,pools[1][c]):mapping[v]=w
 if len(mapping)!=n:return None
 if Counter(frozenset(mapping[v] for v in e) for e in a)!=Counter(map(frozenset,b)):return None
 return mapping
def main():
 pool=defaultdict(list)
 for p in sorted((ROOT/'data/pace2025/private/ds/exact').glob('*.gr')):
  es=None
  for line in p.read_text().splitlines():
   t=line.split()
   if not t or t[0]=='c':continue
   if t[0]=='p':
    n=int(t[2])
    if n>512:break
    es=[{v+1} for v in range(n)];continue
   u,v=map(int,t);es[u-1].add(v);es[v-1].add(u)
  if es is not None:pool[(n,signature(es,n))].append((p,es))
 out={}
 for p in sorted((ROOT/'data/pace2025/private/hs/exact').glob('*.hgr')):
  n,es=read_hgr(p)
  if n>512 or len(es)!=n:continue
  for q,ds in pool.get((n,signature(es,n)),[]):
   mapping=refine_map(es,ds,n)
   if mapping:
    out[p.name]={'ds':q.name,'hs_to_ds':mapping};print(p.name,q.name,flush=True);break
 (ROOT/'results/verified-ds-mappings.json').write_text(json.dumps(out,indent=2))
 print('verified mappings',len(out))
if __name__=='__main__':main()
