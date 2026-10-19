// PACE graph I/O adapter; the published IJCAI 2024 solver is unchanged.
#include <bits/stdc++.h>
using namespace std;
#include "branch.hpp"
template<size_t flags>int run(ugraph&g){
 mds_branch_t<flags,mds_highs_lb_t,mds_reduce_t> s(g);s.solve();cerr<<"nodes "<<s.nodes<<'\n';cout<<s.best.size()<<'\n';for(ui v:s.best)cout<<v+1<<'\n';return 0;
}
int main(int argc,char**argv){
 ui n=0;vector<pii>es;
 for(string line;getline(cin,line);){istringstream in(line);string t;if(!(in>>t)||t=="c")continue;if(t=="p"){string ds;int m;in>>ds>>n>>m;continue;}ui u=stoul(t),v;in>>v;es.emplace_back(u-1,v-1);}
 ugraph g(n,es);if(argc>1&&string(argv[1])=="lp")return run<flg_red|flg_lplb>(g);return run<flg_red|flg_ddlb|flg_mcslb>(g);
}
