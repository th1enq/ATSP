#pragma once

#include "polynomial_baseline.hpp"

namespace batsp {

// Compare positive rational numbers without overflowing cross-products.
inline bool wide_fraction_less(WideDinic::Wide a, WideDinic::Wide b,
                               WideDinic::Wide c, WideDinic::Wide d) {
  bool reversed = false;
  for (;;) {
    auto qa = a / b, qc = c / d;
    if (qa != qc) return reversed ? qa > qc : qa < qc;
    a %= b; c %= d;
    if (!a || !c) return reversed ? c < a : a < c;
    std::swap(a, b); std::swap(c, d);
    reversed = !reversed;
  }
}

// Verify an externally constructed supported tree. Exact min-cut validates
// HK. Optional small-n mode checks every cut; the polynomial mode checks
// the universal support bound, avoiding cuts and optimal-tour enumeration.
inline CertifiedTreeResult certify_supplied_tree(
    const CertifiedTreeInput& input, const std::vector<std::pair<int,int>>& pairs,
    uint64_t beta_num, uint64_t beta_den, bool enumerate_cuts = true) {
  if (input.n < 2 || (enumerate_cuts && input.n > 16) || pairs.size() != static_cast<size_t>(input.n-1))
    throw std::runtime_error("invalid supplied tree dimensions; all-cut mode is limited to n<=16");
  if (!beta_num || !beta_den || beta_num > std::numeric_limits<uint64_t>::max()/2)
    throw std::runtime_error("supplied tree beta outside exact AKS arithmetic range");
  auto result = construct_polynomial_baseline(input);
  if (!enumerate_cuts && wide_fraction_less(beta_num,beta_den,result.beta_num,result.beta_den))
    throw std::runtime_error("supplied bound is below the independently certified support bound");
  result.tree_ids.clear();
  DSU components(input.n);
  for (auto [u, v] : pairs) {
    if (u < 0 || u >= v || v >= input.n || !components.unite(u, v))
      throw std::runtime_error("supplied tree has invalid endpoints or a cycle");
    auto it = std::find_if(result.support.begin(), result.support.end(),
                           [=](const UEdge& e){ return e.u == u && e.v == v; });
    if (it == result.support.end())
      throw std::runtime_error("supplied tree edge outside positive HK support");
    result.tree_ids.push_back(static_cast<int>(it-result.support.begin()));
  }
  if (enumerate_cuts) {
    uint64_t full = (uint64_t(1)<<input.n)-1;
    for (uint64_t mask=1; mask<full; mask+=2) {
    WideDinic::Wide weight=0;
    uint64_t crossing=0;
    for (const auto& arc : input.arcs)
      if (((mask>>arc.u) ^ (mask>>arc.v)) & 1) weight += arc.numerator;
    for (auto [u, v] : pairs)
      crossing += ((mask>>u) ^ (mask>>v)) & 1;
    if (!weight || wide_fraction_less(beta_num, beta_den,
                        static_cast<WideDinic::Wide>(input.denominator)*crossing, weight))
      throw std::runtime_error("supplied tree thinness certificate failed");
    }
  }
  uint64_t divisor=std::gcd(beta_num,beta_den);
  result.beta_num=beta_num/divisor;
  result.beta_den=beta_den/divisor;
  return result;
}

} // namespace batsp
