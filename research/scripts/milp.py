"""Plain binary set-cover formulation, HiGHS single-thread baseline."""
import sys, numpy as np, highspy
edges=[];n=0
for line in sys.stdin:
 t=line.split()
 if not t or t[0]=='c':continue
 if t[0]=='p':n=int(t[2]);continue
 edges.append(sorted(set(int(x)-1 for x in t)))
h=highspy.Highs();h.setOptionValue('output_flag',False);h.setOptionValue('threads',1);h.setOptionValue('mip_rel_gap',0.0);h.setOptionValue('random_seed',0)
h.addVars(n,np.zeros(n),np.ones(n));idx=np.arange(n,dtype=np.int32)
h.changeColsCost(n,idx,np.ones(n));h.changeColsIntegrality(n,idx,np.ones(n,dtype=np.uint8))
starts=[0];indices=[]
for e in edges:indices.extend(e);starts.append(len(indices))
h.addRows(len(edges),np.ones(len(edges)),np.full(len(edges),highspy.kHighsInf),len(indices),np.array(starts,dtype=np.int32),np.array(indices,dtype=np.int32),np.ones(len(indices)))
h.run()
if h.getModelStatus()!=highspy.HighsModelStatus.kOptimal:sys.exit(2)
sol=[v+1 for v,x in enumerate(h.getSolution().col_value) if x>0.5]
print(len(sol));print('\n'.join(map(str,sol)))
