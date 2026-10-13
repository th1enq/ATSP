#include "graph.hpp"
#include "held_karp.hpp"
#include "hamiltonian.hpp"
#include "thin_tree.hpp"
#include "metric.hpp"
#include "witness.hpp"
#include "aks_rounding.hpp"
#include "certified_tree.hpp"
#include "polynomial_baseline.hpp"
#include "supplied_tree.hpp"
#include <cmath>
#include <iostream>
#include <stdexcept>
using namespace batsp;
static void req(bool x,const char* msg){if(!x)throw std::runtime_error(msg);}
int main(){
    try{
        {
            Digraph g(3);g.add_arc(0,1);g.add_arc(1,2);g.add_arc(2,0);
            req(hamiltonian_cycle_dp(g).exists,"triangle Hamiltonian");
            req(minimum_hamiltonian_power(g)==1,"triangle p*=1");
            auto hk=held_karp_feasible_allcuts(g);req(hk.feasible,"triangle HK");
        }
        {
            auto g=witness6_graph();
            auto hk=held_karp_feasible_allcuts(g);req(hk.feasible,"witness HK");
            req(!hamiltonian_cycle_dp(g).exists,"witness non-Hamiltonian");
            req(minimum_hamiltonian_power(g)==2,"witness p*=2");
            auto z=witness6_z();auto e=support_edges_from_z(z);
            auto ex=exact_best_thin_tree_enumerate(6,e,1000000);
            req(ex.found,"witness thin tree");req(ex.trees_tested==128,"witness 128 trees");req(std::abs(ex.beta-4.0/3.0)<1e-9,"witness beta=4/3");
            auto pipe=aks_round_from_thin_tree(g,hk,e,ex.edge_ids,ex.beta);req(pipe.feasible,"AKS circulation");req(pipe.max_visits<=pipe.k_bound,"AKS visit bound");
            auto c=shortest_path_metric(g);req(exact_hk_threshold(c)==1,"metric HK threshold");req(exact_bottleneck_opt(c)==2,"metric optimum");req(bottleneck_cost_of_cycle(c,pipe.ham_cycle)<=pipe.power_bound,"AKS power bound");
        }
        {
            CertifiedTreeInput input;
            input.n=6;input.denominator=2;
            input.arcs={{0,4,2},{1,0,1},{1,4,0},{1,5,1},{2,0,1},{2,3,1},
                        {3,1,1},{3,4,0},{3,5,1},{4,1,1},{4,2,1},{5,2,1},
                        {5,3,1},{5,4,0}};
            auto exact=construct_certified_tree_small(input);
            req(exact.complete && exact.trees_tested==128,"certified tree exhaustive coverage");
            req(exact.beta_num==4 && exact.beta_den==3,"certified tree exact beta");
            std::vector<std::pair<int,int>> supplied;
            for(int id:exact.tree_ids)supplied.push_back({exact.support[id].u,exact.support[id].v});
            auto checked=certify_supplied_tree(input,supplied,4,3);
            req(checked.tree_ids==exact.tree_ids,"supplied tree is preserved");
            bool false_beta_rejected=false;
            try{(void)certify_supplied_tree(input,supplied,1,1);}
            catch(const std::runtime_error&){false_beta_rejected=true;}
            req(false_beta_rejected,"supplied tree false thinness rejected");
            auto duplicate=supplied; duplicate.back()=duplicate.front();
            bool duplicate_rejected=false;
            try{(void)certify_supplied_tree(input,duplicate,4,3);}
            catch(const std::runtime_error&){duplicate_rejected=true;}
            req(duplicate_rejected,"supplied tree duplicate rejected");
            auto baseline=construct_polynomial_baseline(input);
            req(baseline.complete && baseline.tree_ids.size()==5 &&
                baseline.beta_num==2 && baseline.beta_den==1,
                "fractional HK polynomial baseline certificate");
            AKSExactData rational{input.denominator,exact.exact_x_numerators,
                                  exact.beta_num,exact.beta_den};
            auto pipe=aks_round_from_thin_tree(witness6_graph(),exact.hk_for_aks,
                                                exact.support,exact.tree_ids,4.0/3.0,&rational);
            req(pipe.feasible && pipe.power_bound==11,"certified tree AKS integration");
            req(!construct_certified_tree_small(input,1).complete,"certified search cap status");
            input.arcs[0].numerator=1;
            bool rejected=false;
            try{(void)construct_certified_tree_small(input);}catch(const std::runtime_error&){rejected=true;}
            req(rejected,"invalid rational HK certificate rejected");
        }
        {
            CertifiedTreeInput input;
            input.n=12; input.denominator=1;
            for(int v=0;v<12;++v)input.arcs.push_back({v,(v+1)%12,1});
            auto tree=construct_polynomial_baseline(input);
            req(tree.complete && tree.tree_ids.size()==11,"polynomial baseline tree");
            req(tree.beta_num==1 && tree.beta_den==1,"polynomial baseline exact beta");
            Digraph graph(12);
            for(const auto& arc:input.arcs)graph.add_arc(arc.u,arc.v);
            AKSExactData rational{input.denominator,tree.exact_x_numerators,
                                  tree.beta_num,tree.beta_den};
            auto pipe=aks_round_from_thin_tree(graph,tree.hk_for_aks,tree.support,
                                                tree.tree_ids,1.0,&rational);
            req(pipe.feasible && pipe.ham_cycle.size()==13,"polynomial baseline AKS integration");
            input.arcs.clear();
            for(int v=0;v<12;++v)input.arcs.push_back({v,v<6?(v+1)%6:6+(v-5)%6,1});
            bool rejected=false;
            try{(void)construct_polynomial_baseline(input);}catch(const std::runtime_error&){rejected=true;}
            req(rejected,"disconnected directed HK certificate rejected");
        }
        {
            CertifiedTreeInput input;
            input.n=20;input.denominator=1;
            std::vector<std::pair<int,int>> supplied;
            for(int v=0;v<20;++v){
                input.arcs.push_back({v,(v+1)%20,1});
                if(v<19)supplied.push_back({v,v+1});
            }
            auto checked=certify_supplied_tree(input,supplied,1,1,false);
            req(checked.tree_ids.size()==19,"supplied-tree polynomial verifier above 16 vertices");
            bool rejected=false;
            try{(void)certify_supplied_tree(input,supplied,1,2,false);}
            catch(const std::runtime_error&){rejected=true;}
            req(rejected,"unsupported smaller bound rejected without exhaustive cuts");
        }
        {
            CertifiedTreeInput input;
            input.n=3; input.denominator=uint64_t(1)<<63;
            for(int u=0;u<3;++u)
                for(int v=0;v<3;++v)
                    if(u!=v)input.arcs.push_back({u,v,uint64_t(1)<<62});
            auto tree=construct_polynomial_baseline(input);
            req(tree.beta_num==1 && tree.beta_den==1,
                "large-denominator polynomial baseline certificate");
            auto supplied=certify_supplied_tree(input,{{0,1},{1,2}},1,1);
            req(supplied.tree_ids.size()==2,"wide supplied-tree cut arithmetic");
        }
        std::cout<<"core tests passed\n";
        return 0;
    }catch(const std::exception& e){std::cerr<<"TEST FAILURE: "<<e.what()<<"\n";return 1;}
}
