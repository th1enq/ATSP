#include <algorithm>
#include <array>
#include <bit>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <numeric>
#include <sstream>
#include <string>
#include <vector>
using namespace std;
constexpr int W=8;
struct Bits {
 array<uint64_t,W> b{};
 void set(int i){b[i/64]|=1ULL<<(i%64);}
 int count()const{int s=0;for(auto x:b)s+=popcount(x);return s;}
 bool empty()const{for(auto x:b)if(x)return false;return true;}
 Bits minus(const Bits&c)const{Bits r;for(int i=0;i<W;i++)r.b[i]=b[i]&~c.b[i];return r;}
 Bits meet(const Bits&c)const{Bits r;for(int i=0;i<W;i++)r.b[i]=b[i]&c.b[i];return r;}
 vector<int> list()const{vector<int>r;for(int i=0;i<W;i++){auto x=b[i];while(x){int j=countr_zero(x);r.push_back(64*i+j);x&=x-1;}}return r;}
};
int n,m;vector<Bits> cols,rows;vector<vector<int>> rowlist;vector<int>answer;
uint64_t nodes=0,paircalls=0;
bool learn=false,usepair=true,usebound=true;
vector<vector<uint64_t>> pairgood;
vector<Bits> witnesses;
uint64_t cachehits=0,learned=0;
void learn_witness(const Bits&R){
 if(pairgood.empty()){
  int np=n*(n+1)/2,pw=(np+63)/64;
  pairgood.assign(m,vector<uint64_t>(pw));
  for(int e=0;e<m;e++){
   int idx=0;
   for(int a=0;a<n;a++)for(int b=a;b<n;b++,idx++)
    if((rows[e].b[a/64]>>(a%64)&1)||(rows[e].b[b/64]>>(b%64)&1))pairgood[e][idx/64]|=1ULL<<(idx%64);
  }
 }
 int np=n*(n+1)/2,pw=(np+63)/64;
 vector<uint64_t> alive(pw,~0ULL);if(np%64)alive.back()=(1ULL<<(np%64))-1;
 auto choices=R.list();Bits witness;
 while(true){
  int best=-1,bestsize=np+1;
  for(int e:choices)if(!(witness.b[e/64]>>(e%64)&1)){
   int size=0;for(int w=0;w<pw;w++)size+=popcount(alive[w]&pairgood[e][w]);
   if(size<bestsize){bestsize=size;best=e;if(size==0)break;}
  }
  if(best<0){cerr<<"witness construction failed\n";exit(5);}
  witness.set(best);if(bestsize==0)break;
  for(int w=0;w<pw;w++)alive[w]&=pairgood[best][w];
 }
 if(witnesses.size()>=128)witnesses.erase(witnesses.begin());
 witnesses.push_back(witness);learned++;
}
bool pair_complete(const Bits&R,vector<int>&partial){
 paircalls++;
 if(learn)for(auto&w:witnesses)if(w.minus(R).empty()){cachehits++;return false;}
 auto unhit=R.list();int ei=*min_element(unhit.begin(),unhit.end(),[](int a,int b){return rowlist[a].size()<rowlist[b].size();});
 for(int v:rowlist[ei]){
  Bits rest=R.minus(cols[v]);if(rest.empty()){answer=partial;answer.push_back(v);return true;}
  Bits poss;for(int w=0;w<W;w++)poss.b[w]=~0ULL;
  bool alive=true;
  for(int w=0;w<W&&alive;w++){
   auto x=rest.b[w];
   while(x){int e=64*w+countr_zero(x);x&=x-1;poss=poss.meet(rows[e]);if(poss.empty()){alive=false;break;}}
  }
  if(!poss.empty()){answer=partial;answer.push_back(v);answer.push_back(poss.list()[0]);return true;}
 }
 if(learn&&paircalls%256==1)learn_witness(R);
 return false;
}
bool dfs(const Bits&R,Bits allowed,int k,vector<int>&partial){
 nodes++;
 if(R.empty()){answer=partial;return true;}
 if(k<=0)return false;
 if(k==1||(k==2&&usepair)){
  if(k==2)return pair_complete(R,partial);
  auto rr=R.list();Bits poss=rows[rr[0]];for(size_t i=1;i<rr.size()&&!poss.empty();i++)poss=poss.meet(rows[rr[i]]);
  if(poss.empty())return false;answer=partial;answer.push_back(poss.list()[0]);return true;
 }
 vector<int> gains(n);auto cand=allowed.list();vector<int> sortedg;
 for(int v:cand){gains[v]=R.meet(cols[v]).count();sortedg.push_back(gains[v]);}
 sort(sortedg.begin(),sortedg.end(),greater<int>());int cap=0;for(int i=0;i<min(k,(int)sortedg.size());i++)cap+=sortedg[i];
 int nr=R.count();if(usebound&&cap<nr)return false;
 int ei=-1,best=n+1;
 for(int e:R.list()){int s=rows[e].meet(allowed).count();if(s<best){best=s;ei=e;if(s<=1)break;}}
 if(best==0)return false;
 auto branch=rows[ei].meet(allowed).list();sort(branch.begin(),branch.end(),[&](int a,int b){return gains[a]>gains[b];});
 for(int v:branch){
  allowed.b[v/64]&=~(1ULL<<(v%64));
  partial.push_back(v);
  if(dfs(R.minus(cols[v]),allowed,k-1,partial))return true;
  partial.pop_back();
 }
 return false;
}
int main(int argc,char**argv){
 for(int i=1;i<argc;i++){string a=argv[i];if(a=="--learn")learn=true;else if(a=="--no-pair")usepair=false;else if(a=="--no-bound")usebound=false;else return 4;}
 vector<vector<int>>edges;
 for(string line;getline(cin,line);){istringstream in(line);string t;if(!(in>>t)||t=="c")continue;if(t=="p"){string hs;in>>hs>>n>>m;continue;}vector<int>e{stoi(t)-1};int v;while(in>>v)e.push_back(v-1);edges.push_back(e);}
 m=edges.size();if(n>W*64||m>W*64){cerr<<"instance exceeds bitset capacity\n";return 3;}
 cols.resize(n);rows.resize(m);rowlist=edges;Bits R,allowed;
 for(int e=0;e<m;e++){R.set(e);for(int v:edges[e]){cols[v].set(e);rows[e].set(v);}}
 for(int v=0;v<n;v++)allowed.set(v);
 auto rest=R;vector<int>greedy;
 while(!rest.empty()){int bv=0,bg=0;for(int v=0;v<n;v++){int g=rest.meet(cols[v]).count();if(g>bg){bg=g;bv=v;}}if(!bg)return 2;greedy.push_back(bv);rest=rest.minus(cols[bv]);}
 answer=greedy;int ub=answer.size();cerr<<"greedy "<<ub<<'\n';
 for(int k=1;k<ub;k++){vector<int>p;auto t=chrono::steady_clock::now();if(dfs(R,allowed,k,p))break;cerr<<"unsat "<<k<<" seconds "<<chrono::duration<double>(chrono::steady_clock::now()-t).count()<<" nodes "<<nodes<<" paircalls "<<paircalls<<'\n';}
 cerr<<"nodes "<<nodes<<" paircalls "<<paircalls<<" cachehits "<<cachehits<<" learned "<<learned<<'\n';
 cout<<answer.size()<<'\n';for(int v:answer)cout<<v+1<<'\n';
}
