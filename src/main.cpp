#include "graph.hpp"
#include "held_karp.hpp"
#include "hamiltonian.hpp"
#include "thin_tree.hpp"
#include "metric.hpp"
#include "witness.hpp"
#include "aks_rounding.hpp"
#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <sstream>

using namespace batsp;

static void usage(){
    std::cerr << "batsp commands:\n"
              << "  witness6\n"
              << "  exhaustive-n4 [csv]\n"
              << "  exhaustive-n5 [csv]\n"
              << "  random-search N PER_N P_LO P_HI SEED [csv]\n"
              << "  split-family MAXN [csv]\n"
              << "  metric-random N REPS SEED [csv]\n"
              << "  metric-witness6\n";
}

static bool fast_hk_necessary(const Digraph& g){
    if(!strongly_connected(g)) return false;
    for(int v=0;v<g.n;++v){
        bool out=false,in=false;
        for(int u=0;u<g.n;++u){out|=g.has_arc(v,u);in|=g.has_arc(u,v);} if(!out||!in)return false;
    }
    return true;
}

static int run_witness6(){
    Digraph g=witness6_graph();
    auto t0=std::chrono::steady_clock::now();
    auto hk=held_karp_feasible_allcuts(g);
    auto t1=std::chrono::steady_clock::now();
    auto ham=hamiltonian_cycle_dp(g);
    int p=minimum_hamiltonian_power(g,6);
    auto z=witness6_z();
    auto edges=support_edges_from_z(z);
    auto ex=exact_best_thin_tree_enumerate(g.n,edges,1000000);
    auto mst=weighted_kruskal_tree(g.n,edges,0);
    std::mt19937_64 rng(20261007);
    auto rnd=random_tree_search(g.n,edges,5000,rng);
    auto loc=local_swap_improve(g.n,edges,rnd);
    auto pipeline=aks_round_from_thin_tree(g,hk,edges,ex.edge_ids,ex.beta);
    auto metric=shortest_path_metric(g);
    int opt=exact_bottleneck_opt(metric);
    int tau=exact_hk_threshold(metric);
    int alg = pipeline.feasible ? bottleneck_cost_of_cycle(metric,pipeline.ham_cycle) : -1;
    double ms=std::chrono::duration<double,std::milli>(t1-t0).count();
    std::cout<<std::fixed<<std::setprecision(9);
    std::cout<<"witness6\n";
    std::cout<<"n="<<g.n<<" arcs="<<g.arc_count()<<"\n";
    std::cout<<"hk_feasible="<<hk.feasible<<" hk_ms="<<ms<<" hk_min_cut="<<hk.min_cut_out<<"\n";
    std::cout<<"hamiltonian="<<ham.exists<<" p_star="<<p<<"\n";
    std::cout<<"support_edges="<<edges.size()<<" spanning_trees="<<ex.trees_tested<<" beta_exact="<<ex.beta<<"\n";
    std::cout<<"beta_invz_mst="<<mst.beta<<" beta_random="<<rnd.beta<<" beta_local="<<loc.beta<<"\n";
    std::cout<<"aks_feasible="<<pipeline.feasible<<" k_bound="<<pipeline.k_bound<<" max_visits="<<pipeline.max_visits<<" power_bound="<<pipeline.power_bound<<" alg_bottleneck="<<alg<<"\n";
    std::cout<<"metric_tau_hk="<<tau<<" metric_opt="<<opt<<" lp_gap="<<(double)opt/tau<<" alg_over_opt="<<(alg>0?(double)alg/opt:0)<<"\n";
    std::cout<<"best_tree=";
    for(int id:ex.edge_ids) std::cout<<" ("<<edges[id].u<<","<<edges[id].v<<")";
    std::cout<<"\n";
    return (hk.feasible && !ham.exists && p==2 && std::abs(ex.beta-4.0/3.0)<1e-9 && ex.trees_tested==128 && tau==1 && opt==2 && pipeline.feasible)?0:2;
}

static int run_n4(const std::string& csv){
    const int n=4; const int bits=n*(n-1); const uint64_t total=1ULL<<bits;
    uint64_t hkcnt=0, hknonham=0, hamcnt=0, necessary=0;
    std::ofstream out;
    if(!csv.empty()){out.open(csv);out<<"mask,arcs,hk_feasible,hamiltonian,p_star\n";}
    auto start=std::chrono::steady_clock::now();
    std::vector<std::pair<int,int>> order;
    for(int u=0;u<n;++u)for(int v=0;v<n;++v)if(u!=v)order.push_back({u,v});
    for(uint64_t mask=0;mask<total;++mask){
        Digraph g(n); for(int i=0;i<bits;++i)if((mask>>i)&1ULL)g.add_arc(order[i].first,order[i].second);
        bool hkf=false;
        if(fast_hk_necessary(g)){necessary++; hkf=held_karp_feasible_allcuts(g).feasible;}
        bool ham=false; int p=-1;
        if(hkf){
            hkcnt++; ham=hamiltonian_cycle_dp(g).exists; if(ham)hamcnt++; else {hknonham++;p=minimum_hamiltonian_power(g,4);} 
        }
        if(out)out<<mask<<","<<g.arc_count()<<","<<hkf<<","<<ham<<","<<p<<"\n";
    }
    double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
    std::cout<<"exhaustive_n4 total="<<total<<" necessary="<<necessary<<" hk_feasible="<<hkcnt
             <<" hk_hamiltonian="<<hamcnt<<" hk_nonham="<<hknonham<<" seconds="<<sec<<"\n";
    return (hkcnt==1194 && hknonham==0)?0:3;
}


static int run_n5(const std::string& csv){
    const int n=5,bits=n*(n-1);const uint64_t total=1ULL<<bits;
    std::vector<std::pair<int,int>> order;for(int u=0;u<n;++u)for(int v=0;v<n;++v)if(u!=v)order.push_back({u,v});
    uint64_t hamcnt=0,hk_nonham=0,necessary_nonham=0,lp_calls=0;
    std::ofstream out;if(!csv.empty()){out.open(csv);out<<"mask,arcs,hamiltonian,hk_nonham,p_star,beta_exact,beta_mst,beta_random,support_edges,trees_tested\n";}
    auto t0=std::chrono::steady_clock::now();
    for(uint64_t mask=0;mask<total;++mask){
        Digraph g(n);for(int i=0;i<bits;++i)if((mask>>i)&1ULL)g.add_arc(order[i].first,order[i].second);
        bool ham=hamiltonian_cycle_dp(g).exists;bool hkn=false;int ps=-1;double be=0,bm=0,br=0;int se=0;uint64_t tt=0;
        if(ham)hamcnt++;
        else if(fast_hk_necessary(g)){
            necessary_nonham++;lp_calls++;auto hk=held_karp_feasible_allcuts(g);
            if(hk.feasible){
                hkn=true;hk_nonham++;ps=minimum_hamiltonian_power(g,5);
                auto z=symmetrized_z(hk,n);auto e=support_edges_from_z(z);se=e.size();
                auto ex=exact_best_thin_tree_enumerate(n,e,1000000);be=ex.found?ex.beta:0;tt=ex.trees_tested;
                auto mt=weighted_kruskal_tree(n,e,0);bm=mt.found?mt.beta:0;
                std::mt19937_64 rr(20261007ULL^mask);auto rt=random_tree_search(n,e,500,rr);auto li=local_swap_improve(n,e,rt,20);br=li.found?li.beta:0;
            }
        }
        if(out && (hkn || mask%10000==0))out<<mask<<","<<g.arc_count()<<","<<ham<<","<<hkn<<","<<ps<<","<<be<<","<<bm<<","<<br<<","<<se<<","<<tt<<"\n";
    }
    double sec=std::chrono::duration<double>(std::chrono::steady_clock::now()-t0).count();
    std::cout<<"exhaustive_n5 total="<<total<<" hamiltonian="<<hamcnt<<" necessary_nonham="<<necessary_nonham<<" lp_calls="<<lp_calls<<" hk_nonham="<<hk_nonham<<" hk_total="<<(hamcnt+hk_nonham)<<" seconds="<<sec<<"\n";
    return 0;
}


static std::string graph_signature(const Digraph& g){
    std::string s; s.reserve(g.n*(g.n-1));
    for(int u=0;u<g.n;++u)for(int v=0;v<g.n;++v)if(u!=v)s.push_back(g.has_arc(u,v)?'1':'0');
    return s;
}

static int run_random_search(int N,int per,double plo,double phi,uint64_t seed,const std::string& csv){
    std::mt19937_64 rng(seed); std::uniform_real_distribution<double>P(plo,phi);
    std::ofstream out; if(!csv.empty()){out.open(csv);out<<"n,rep,p,arcs,hk,ham,p_star,beta_invz,beta_random,graph_signature\n";}
    uint64_t total=0,hkcnt=0,hard=0,p2=0,pge3=0;
    for(int n=5;n<=N;++n){
        if(n>18) break;
        for(int rep=0;rep<per;++rep){
            total++; double p=P(rng); Digraph g=random_er_digraph(n,p,rng);
            if(!fast_hk_necessary(g)){if(out)out<<n<<","<<rep<<","<<p<<","<<g.arc_count()<<",0,0,-1,,,"<<graph_signature(g)<<"\n";continue;}
            auto hk=held_karp_feasible_allcuts(g); if(!hk.feasible){if(out)out<<n<<","<<rep<<","<<p<<","<<g.arc_count()<<",0,0,-1,,,"<<graph_signature(g)<<"\n";continue;}
            hkcnt++; auto ham=hamiltonian_cycle_dp(g); int ps=1; double bm=0,br=0;
            if(!ham.exists){
                hard++; ps=minimum_hamiltonian_power(g,std::min(n,5)); if(ps==2)p2++; if(ps>=3)pge3++;
                auto z=symmetrized_z(hk,n); auto e=support_edges_from_z(z);
                if(n<=12){
                    auto mst=weighted_kruskal_tree(n,e,0); bm=mst.found?mst.beta:0;
                    std::mt19937_64 rr(seed ^ (uint64_t(n)<<32) ^ rep);
                    auto r=random_tree_search(n,e,1000,rr); auto l=local_swap_improve(n,e,r,20); br=l.found?l.beta:0;
                }
            }
            if(out)out<<n<<","<<rep<<","<<p<<","<<g.arc_count()<<",1,"<<ham.exists<<","<<ps<<","<<bm<<","<<br<<","<<graph_signature(g)<<"\n";
        }
    }
    std::cout<<"random_search total="<<total<<" hk="<<hkcnt<<" hard_nonham="<<hard<<" p2="<<p2<<" p_ge_3="<<pge3<<" seed="<<seed<<"\n";
    return 0;
}


static int run_split_family(int maxn,const std::string& csv){
    Digraph g=witness6_graph();
    std::ofstream out; if(!csv.empty()){out.open(csv);out<<"n,arcs,hk,ham,p_star,hk_ms,beta_mst,beta_random,aks_feasible,aks_k,aks_max_visits,aks_power,alg_bottleneck,opt_bottleneck\n";}
    for(int n=6;n<=maxn;++n){
        auto t0=std::chrono::steady_clock::now(); auto hk=held_karp_feasible_allcuts(g); auto t1=std::chrono::steady_clock::now();
        bool ham=hamiltonian_cycle_dp(g).exists; int ps=minimum_hamiltonian_power(g,std::min(4,n));
        double bm=0,br=0;bool af=false;int ak=0,av=0,ap=0,alg=-1,opt=-1;
        if(hk.feasible && n<=14){
            auto z=symmetrized_z(hk,n);auto e=support_edges_from_z(z);auto m=weighted_kruskal_tree(n,e,0);bm=m.found?m.beta:0;
            std::mt19937_64 rr(20261007+n);auto r=random_tree_search(n,e,2000,rr);auto l=local_swap_improve(n,e,r,30);br=l.found?l.beta:0;
            if(l.found){auto pipe=aks_round_from_thin_tree(g,hk,e,l.edge_ids,l.beta);af=pipe.feasible;if(af){ak=pipe.k_bound;av=pipe.max_visits;ap=pipe.power_bound;auto c=shortest_path_metric(g);alg=bottleneck_cost_of_cycle(c,pipe.ham_cycle);opt=exact_bottleneck_opt(c);}}
        }
        double ms=std::chrono::duration<double,std::milli>(t1-t0).count();
        std::cout<<"split n="<<n<<" arcs="<<g.arc_count()<<" hk="<<hk.feasible<<" ham="<<ham<<" p*="<<ps<<" hk_ms="<<ms<<" beta_mst="<<bm<<" beta_rand="<<br<<" aks="<<af<<" alg="<<alg<<" opt="<<opt<<"\n";
        if(out)out<<n<<","<<g.arc_count()<<","<<hk.feasible<<","<<ham<<","<<ps<<","<<ms<<","<<bm<<","<<br<<","<<af<<","<<ak<<","<<av<<","<<ap<<","<<alg<<","<<opt<<"\n";
        if(n<maxn) g=split_vertex_forced(g,0);
    }
    return 0;
}

static std::vector<std::vector<int>> random_metric_complete(int n,std::mt19937_64& rng){
    std::uniform_int_distribution<int> W(1,100); const int INF=1e8;
    std::vector<std::vector<int>> d(n,std::vector<int>(n,INF));
    for(int i=0;i<n;++i){d[i][i]=0;for(int j=0;j<n;++j)if(i!=j)d[i][j]=W(rng);}
    for(int k=0;k<n;++k)for(int i=0;i<n;++i)for(int j=0;j<n;++j)d[i][j]=std::min(d[i][j],d[i][k]+d[k][j]);
    return d;
}

static int run_metric_random(int N,int reps,uint64_t seed,const std::string& csv){
    std::mt19937_64 rng(seed); std::ofstream out; if(!csv.empty())out.open(csv);
    if(out)out<<"n,rep,tau_hk,opt,gap,support_edges,beta_mst,beta_random,beta_aks,aks_feasible,aks_k,aks_max_visits,aks_power,alg_bottleneck,alg_over_opt\n";
    for(int n=5;n<=N;++n){
        for(int rep=0;rep<reps;++rep){
            auto c=random_metric_complete(n,rng); int tau=exact_hk_threshold(c); int opt=exact_bottleneck_opt(c);
            auto gt=threshold_graph(c,tau); auto hk=held_karp_feasible_allcuts(gt); double bm=0,br=0;int se=0;
            bool af=false; int ak=0,av=0,ap=0,alg=-1;
            if(hk.feasible){
                auto z=symmetrized_z(hk,n);auto e=support_edges_from_z(z);se=e.size();auto m=weighted_kruskal_tree(n,e,0);bm=m.found?m.beta:0;
                std::mt19937_64 rr(seed^(uint64_t(n)<<32)^rep);auto r=random_tree_search(n,e,500,rr);auto l=local_swap_improve(n,e,r,10);br=l.found?l.beta:0;
                if(l.found){auto pipe=aks_round_from_thin_tree(gt,hk,e,l.edge_ids,l.beta);af=pipe.feasible;if(af){ak=pipe.k_bound;av=pipe.max_visits;ap=pipe.power_bound;alg=bottleneck_cost_of_cycle(c,pipe.ham_cycle);}}
            }
            double baks = n>2 && std::log(std::log((double)n))>0 ? 4*std::log((double)n)/std::log(std::log((double)n)) : 0;
            if(out)out<<n<<","<<rep<<","<<tau<<","<<opt<<","<<(double)opt/tau<<","<<se<<","<<bm<<","<<br<<","<<baks<<","<<af<<","<<ak<<","<<av<<","<<ap<<","<<alg<<","<<(alg>0?(double)alg/opt:0)<<"\n";
        }
        std::cout<<"metric_random finished n="<<n<<" reps="<<reps<<"\n";
    }
    return 0;
}

int main(int argc,char**argv){
    try{
        if(argc<2){usage();return 1;}
        std::string cmd=argv[1];
        if(cmd=="witness6")return run_witness6();
        if(cmd=="metric-witness6")return run_witness6();
        if(cmd=="exhaustive-n4")return run_n4(argc>=3?argv[2]:"");
        if(cmd=="exhaustive-n5")return run_n5(argc>=3?argv[2]:"");
        if(cmd=="split-family"){if(argc<3){usage();return 1;}return run_split_family(std::stoi(argv[2]),argc>=4?argv[3]:"");}
        if(cmd=="metric-random"){if(argc<5){usage();return 1;}return run_metric_random(std::stoi(argv[2]),std::stoi(argv[3]),std::stoull(argv[4]),argc>=6?argv[5]:"");}
        if(cmd=="random-search"){
            if(argc<7){usage();return 1;}
            int N=std::stoi(argv[2]),per=std::stoi(argv[3]); double lo=std::stod(argv[4]),hi=std::stod(argv[5]); uint64_t seed=std::stoull(argv[6]);
            return run_random_search(N,per,lo,hi,seed,argc>=8?argv[7]:"");
        }
        usage(); return 1;
    }catch(const std::exception&e){std::cerr<<"ERROR: "<<e.what()<<"\n";return 10;}
}
