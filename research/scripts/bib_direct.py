"""Run BIB on a VERIFIED isomorphic original DS instance, map certificate back.

This gives BIB its native graph representation. Dataset matching is solely a
baseline adapter and is never used by the proposed solver.
"""
import hashlib,json,subprocess,sys
from analyze import ROOT
maps=json.loads((ROOT/'results/verified-ds-mappings.json').read_text())
data=sys.stdin.buffer.read();digest=hashlib.sha256(data).digest();match=None
for name,info in maps.items():
 if hashlib.sha256((ROOT/'data/pace2025/private/hs/exact'/name).read_bytes()).digest()==digest:match=info;break
if match is None:sys.exit('no verified equivalent graph')
cmd=[str(ROOT/'bin/bib_ds')]+sys.argv[1:]
p=subprocess.run(cmd,input=(ROOT/'data/pace2025/private/ds/exact'/match['ds']).read_bytes(),capture_output=True)
sys.stderr.buffer.write(p.stderr)
if p.returncode:sys.exit(p.returncode)
vals=list(map(int,p.stdout.split()));inverse={v:int(k) for k,v in match['hs_to_ds'].items()}
print(vals[0]);print('\n'.join(str(inverse[v]) for v in vals[1:]))
