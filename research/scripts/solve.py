"""Exact portfolio: bounded dense search, then the original UzL solver.

Only a completed exact solve is returned. A timeout in the dense probe is not
interpreted as infeasibility. This wrapper accepts PACE 2025 Hitting Set on stdin.
"""
import argparse,subprocess,sys
from analyze import ROOT
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--dense-seconds',type=float,default=10);a=ap.parse_args()
 if a.dense_seconds<=0:ap.error('--dense-seconds must be positive')
 lines=[];n=None;edges=[];expected=None
 for line in sys.stdin:
  t=line.split()
  if not t or t[0]=='c':continue
  if t[0]=='p':
   if len(t)!=4 or t[1]!='hs':raise ValueError('expected p hs n m')
   n,expected=map(int,t[2:]);continue
  edges.append(sorted(set(map(int,t))))
 if n is None or expected!=len(edges):raise ValueError('invalid hypergraph header or edge count')
 if any(not e or e[0]<1 or e[-1]>n for e in edges):raise ValueError('invalid edge')
 data=(f'p hs {n} {len(edges)}\n'+''.join(' '.join(map(str,e))+'\n' for e in edges)).encode()
 dense=n<=512 and len(edges)<=512 and sum(map(len,edges))>=n*len(edges)/16
 if dense:
  p=subprocess.Popen([str(ROOT/'bin/dense_v1')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  try:
   out,err=p.communicate(data,timeout=a.dense_seconds)
   if p.returncode==0:
    sys.stderr.buffer.write(b'portfolio: dense exact solve\n'+err);sys.stdout.buffer.write(out);return
   sys.stderr.buffer.write(b'portfolio: dense probe failed, using UzL\n'+err)
  except subprocess.TimeoutExpired:
   p.kill();p.communicate();sys.stderr.write('portfolio: dense probe timed out, using UzL\n')
 p=subprocess.run([str(ROOT/'vendor/uzl/target/release/uzl_hs')],input=data)
 sys.exit(p.returncode)
if __name__=='__main__':main()
