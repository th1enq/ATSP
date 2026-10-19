// Input/output adapter to IJCAI24-MDS's published EMDSP implementation.
// An incidence bipartite graph: ignore variable vertices, exclude edge vertices.
#include <bits/stdc++.h>
using namespace std;
#include "branch.hpp"
#include <sstream>
template<size_t flags> int run(const ugraph&g,ui variables,ui edges){
 mds_branch_t<flags,mds_highs_lb_t,mds_reduce_t> solver(g);
 for(ui v=0;v<variables;v++)solver.ignore(v);
 for(ui e=0;e<edges;e++)solver.exclude(variables+e);
 solver.best.resize(variables);iota(solver.best.begin(),solver.best.end(),0);
 solver.solve();
 cerr<<"nodes "<<solver.nodes<<'\n';cout<<solver.best.size()<<'\n';
 for(auto v:solver.best){if(v>=variables)return 6;cout<<v+1<<'\n';}return 0;
}
int main(int argc,char**argv){
 ui n=0;vector<vector<ui>>edges;
 for(string line;getline(cin,line);){istringstream in(line);string t;if(!(in>>t)||t=="c")continue;if(t=="p"){string hs;int m;in>>hs>>n>>m;continue;}vector<ui>e{(ui)stoul(t)-1};ui v;while(in>>v)e.push_back(v-1);sort(e.begin(),e.end());e.erase(unique(e.begin(),e.end()),e.end());edges.push_back(e);}
 vector<pii>inc;for(ui e=0;e<edges.size();e++)for(ui v:edges[e])inc.emplace_back(v,n+e);
 ugraph g(n+edges.size(),inc);
 if(argc>1&&string(argv[1])=="lp")return run<flg_red|flg_lplb>(g,n,edges.size());
 return run<flg_red|flg_ddlb|flg_mcslb>(g,n,edges.size());
}
