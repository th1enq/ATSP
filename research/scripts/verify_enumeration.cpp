// Independent optimality checker: plain increasing-index subset enumeration.
// No packing, search bounds, pivoting, or two-completion oracle is used.
#include <bitset>
#include <chrono>
#include <fstream>
#include <iostream>
#include <sstream>
#include <vector>
using namespace std;
vector<bitset<512>> cover;
uint64_t checked=0;
bool smaller_exists(bitset<512> missing,int start,int left){
 if(missing.none())return true;
 if(!left){checked++;return false;}
 for(int v=start;v<=(int)cover.size()-left;v++)if(smaller_exists(missing&~cover[v],v+1,left-1))return true;
 return false;
}
int main(int argc,char**argv){
 if(argc!=3)return 2;ifstream in(argv[1]);int n=0,m=0;vector<vector<int>>edges;
 for(string line;getline(in,line);){istringstream s(line);string t;if(!(s>>t)||t=="c")continue;if(t=="p"){string hs;s>>hs>>n>>m;continue;}vector<int>e{stoi(t)-1};int v;while(s>>v)e.push_back(v-1);edges.push_back(e);}
 if(n>512||m>512||m!=(int)edges.size())return 3;
 cover.resize(n);bitset<512>all,selected;
 for(int e=0;e<m;e++){all.set(e);for(int v:edges[e])cover[v].set(e);}
 ifstream cert(argv[2]);int k,v;cert>>k;for(int i=0;i<k;i++){if(!(cert>>v)||v<1||v>n||selected[v-1])return 4;selected.set(v-1);}
 auto uncovered=all;for(int v=0;v<n;v++)if(selected[v])uncovered&=~cover[v];if(uncovered.any())return 5;
 auto start=chrono::steady_clock::now();bool counterexample=k>0&&smaller_exists(all,0,k-1);
 cout<<"{\"certified_optimal\":"<<(counterexample?"false":"true")<<",\"objective\":"<<k<<",\"enumerated_subsets\":"<<checked<<",\"seconds\":"<<chrono::duration<double>(chrono::steady_clock::now()-start).count()<<"}\n";
 return counterexample?6:0;
}
