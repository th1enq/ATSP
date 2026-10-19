"""Standard SAT + cardinality baseline, no problem-specific search."""
import sys,math
from pysat.solvers import Solver
from pysat.card import CardEnc,EncType
edges=[];n=0
for line in sys.stdin:
 t=line.split()
 if not t or t[0]=='c':continue
 if t[0]=='p':n=int(t[2]);continue
 edges.append(sorted(set(map(int,t))))
rest=set(range(len(edges)));cols=[set() for _ in range(n+1)]
for i,e in enumerate(edges):
 for v in e:cols[v].add(i)
greedy=[]
while rest:
 v=max(range(1,n+1),key=lambda v:len(cols[v]&rest));greedy.append(v);rest-=cols[v]
enc=EncType.seqcounter if len(sys.argv)<2 or sys.argv[1]=='seq' else EncType.totalizer
lb=math.ceil(len(edges)/max(map(len,cols))) if edges else 0
for k in range(lb,len(greedy)):
 cnf=CardEnc.atmost(list(range(1,n+1)),k,top_id=n,encoding=enc)
 with Solver(name='cadical195',bootstrap_with=edges+cnf.clauses) as s:
  if s.solve():
   model=set(s.get_model());greedy=[v for v in range(1,n+1) if v in model];break
print(len(greedy));print('\n'.join(map(str,greedy)))
