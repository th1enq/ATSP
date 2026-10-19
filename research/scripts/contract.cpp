// Exact pair-packing contraction. Based on the public UzL EvalMaxSAT backend.
#include <algorithm>
#include <chrono>
#include <iostream>
#include <numeric>
#include <sstream>
#include <string>
#include <vector>
#include "Formula.hpp"
using namespace std;
int main(int argc,char** argv) {
    bool contract=argc>1 && string(argv[1])=="contract";
    int n=0; vector<vector<int>> edges;
    for(string line;getline(cin,line);) {
        istringstream in(line); string t; if(!(in>>t)||t=="c")continue;
        if(t=="p"){string hs;int m;in>>hs>>n>>m;continue;}
        vector<int> e; e.push_back(stoi(t));int v;while(in>>v)e.push_back(v);
        sort(e.begin(),e.end());e.erase(unique(e.begin(),e.end()),e.end());edges.push_back(e);
    }
    vector<int> degree(n+1),used(n+1),lit(n+1),defect(n+1);
    for(auto&e:edges)for(int v:e)degree[v]++;
    vector<pair<int,int>> pairs;
    if(contract) {
        vector<int> order;
        for(int i=0;i<(int)edges.size();i++)if(edges[i].size()==2)order.push_back(i);
        stable_sort(order.begin(),order.end(),[&](int a,int b){return degree[edges[a][0]]+degree[edges[a][1]]<degree[edges[b][0]]+degree[edges[b][1]];});
        for(int i:order){int a=edges[i][0],b=edges[i][1];if(!used[a]&&!used[b]){used[a]=used[b]=1;pairs.emplace_back(a,b);}}
    }
    Eval::Formula f; int nv=0;vector<int> soft;
    for(auto [a,b]:pairs) {int y=++nv,d=++nv;lit[a]=y;lit[b]=-y;defect[a]=defect[b]=d;soft.push_back(d);}
    for(int v=1;v<=n;v++)if(!lit[v]){lit[v]=++nv;soft.push_back(lit[v]);}
    int count=0;
    for(auto&e:edges) {
        vector<int> c;
        for(int v:e) {c.push_back(lit[v]);if(defect[v])c.push_back(defect[v]);}
        sort(c.begin(),c.end());c.erase(unique(c.begin(),c.end()),c.end());
        bool taut=false;for(int x:c)if(binary_search(c.begin(),c.end(),-x)){taut=true;break;}
        if(!taut){f.addClause(c.data(),c.size());count++;}
    }
    for(int x:soft){int neg=-x;f.addClause(&neg,1,1);}
    cerr<<"pairs "<<pairs.size()<<" variables "<<nv<<" soft "<<soft.size()<<" hard "<<count<<"\n";
    cout.setstate(ios_base::failbit);bool ok=f.solve();cout.clear();
    if(!ok)return 2;
    vector<int> sol;
    for(int v=1;v<=n;v++)if((f.getValue(abs(lit[v]))==(lit[v]>0))||(defect[v]&&f.getValue(defect[v])))sol.push_back(v);
    cout<<sol.size()<<'\n';for(int v:sol)cout<<v<<'\n';
}
