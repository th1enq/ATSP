"""Export standalone figures from the completed confirmation data."""
import csv,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analyze import ROOT
s=json.loads((ROOT/'results/summary.json').read_text())
rows=[]
for i in range(3):rows+=list(csv.DictReader((ROOT/'results'/f'full-private-shard{i}'/'runs.csv').open()))
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})
fig,axes=plt.subplots(1,2,figsize=(11,4.3),gridspec_kw={'width_ratios':[1.15,1]})
for name,label,color in [('portfolio','Proposed portfolio','#1565c0'),('uzl','Original UzL','#bf4b28')]:
 times=sorted(float(r['wall_s']) for r in rows if r['solver']==name and r['status']=='ok')
 axes[0].step([.001]+times+[10],[0]+list(range(1,len(times)+1))+[len(times)],where='post',label=f'{label}: {len(times)}/100',color=color,lw=2)
axes[0].set(xscale='log',xlim=(.001,10),ylim=(0,100),xlabel='Wall time limit (seconds)',ylabel='Instances solved to optimality',title='All 100 private instances')
axes[0].grid(axis='y',alpha=.2);axes[0].legend(loc='upper left',frameon=False)
names=['dense','no_pair','uzl','bibco_native','biblp_native'];labels=['Dual-bitset completion','Without two-completion','Original UzL','BIBCO (native graph)','BIBLP (native graph)']
values=[s['small_dense_private'][name]['solved'] for name in names]
axes[1].barh(labels,values,color=['#1565c0','#c59431','#7a7a7a','#7a7a7a','#7a7a7a']);axes[1].invert_yaxis()
axes[1].set(xlim=(0,30),xlabel='Instances solved within 10 seconds',title='All 30 small/dense private instances')
axes[1].grid(axis='x',alpha=.2);axes[1].set_axisbelow(True)
for i,v in enumerate(values):axes[1].text(v+.4,i,f'{v}/30',va='center')
fig.suptitle('PACE 2025 Hitting Set — local short-budget evaluation',fontsize=13)
fig.tight_layout()
for ext in ['pdf','svg','png']:fig.savefig(ROOT/'results'/f'benchmark_summary.{ext}',dpi=180,bbox_inches='tight')
print('Exported benchmark_summary.pdf, .svg, .png')
