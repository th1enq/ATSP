#include "graph.hpp"
#include "held_karp.hpp"
#include "hamiltonian.hpp"
#include "thin_tree.hpp"
#include "metric.hpp"
#include "witness.hpp"
#include "aks_rounding.hpp"
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
        std::cout<<"core tests passed\n";
        return 0;
    }catch(const std::exception& e){std::cerr<<"TEST FAILURE: "<<e.what()<<"\n";return 1;}
}
