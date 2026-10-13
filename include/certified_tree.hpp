#pragma once

#include "held_karp.hpp"
#include "thin_tree.hpp"
#include <algorithm>
#include <bit>
#include <cstdint>
#include <functional>
#include <map>
#include <numeric>
#include <stdexcept>
#include <vector>

namespace batsp {

// A small-instance reference construction. All cut and thinness comparisons are
// integral; the search is exhaustive and is not the polynomial strong-thin-tree
// construction of OpenAI Result 174.
struct RationalArc {
  int u, v;
  uint64_t numerator;
};

struct CertifiedTreeInput {
  int n = 0;
  uint64_t denominator = 1;
  std::vector<RationalArc> arcs;
};

struct CertifiedTreeResult {
  bool complete = false;
  uint64_t search_nodes = 0;
  uint64_t trees_tested = 0;
  uint64_t beta_num = 0;
  uint64_t beta_den = 1;
  std::vector<UEdge> support;
  std::vector<int> tree_ids;
  HKResult hk_for_aks;
  std::vector<uint64_t> exact_x_numerators;
};

inline CertifiedTreeResult construct_certified_tree_small(
    const CertifiedTreeInput &input, uint64_t node_cap = 10000000ULL) {
  const int n = input.n;
  const uint64_t D = input.denominator;
  if (n < 2 || n > 10)
    throw std::runtime_error("certified tree reference supports 2<=n<=10");
  if (D == 0 || D > 1000000000ULL)
    throw std::runtime_error("certified tree denominator must be in [1,1e9]");
  if (node_cap == 0)
    throw std::runtime_error("certified tree search node cap must be positive");

  CertifiedTreeResult out;
  Digraph g(n);
  std::vector<uint64_t> indeg(n, 0), outdeg(n, 0);
  std::map<std::pair<int, int>, uint64_t> zmult;
  std::vector<std::vector<uint8_t>> seen(n, std::vector<uint8_t>(n, 0));
  for (const auto &a : input.arcs) {
    if (a.u < 0 || a.u >= n || a.v < 0 || a.v >= n || a.u == a.v ||
        seen[a.u][a.v] || a.numerator > D)
      throw std::runtime_error("invalid or duplicate rational HK arc");
    seen[a.u][a.v] = 1;
    g.add_arc(a.u, a.v);
    outdeg[a.u] += a.numerator;
    indeg[a.v] += a.numerator;
    auto key = std::minmax(a.u, a.v);
    zmult[key] += a.numerator;
  }
  for (int v = 0; v < n; ++v)
    if (indeg[v] != D || outdeg[v] != D)
      throw std::runtime_error("rational HK degree certificate failed");
  const uint64_t full = (uint64_t(1) << n) - 1;
  for (uint64_t S = 1; S < full; ++S) {
    uint64_t cut = 0;
    for (const auto &a : input.arcs)
      if ((S & (uint64_t(1) << a.u)) && !(S & (uint64_t(1) << a.v)))
        cut += a.numerator;
    if (cut < D)
      throw std::runtime_error("rational HK subtour certificate failed");
  }

  // Preserve the graph's canonical arc order expected by AKS.
  out.hk_for_aks.feasible = true;
  out.hk_for_aks.arcs = g.arcs();
  for (auto [u, v] : out.hk_for_aks.arcs) {
    uint64_t q = 0;
    for (const auto &a : input.arcs)
      if (a.u == u && a.v == v) {
        q = a.numerator;
        break;
      }
    out.hk_for_aks.x.push_back(static_cast<double>(q) / static_cast<double>(D));
    out.exact_x_numerators.push_back(q);
  }

  std::vector<uint64_t> multiplicity;
  for (const auto &[pair, q] : zmult)
    if (q > 0) {
      if (q > 2 * D)
        throw std::runtime_error("invalid symmetrized HK coordinate");
      out.support.push_back(
          {pair.first, pair.second, static_cast<double>(q) / static_cast<double>(D)});
      multiplicity.push_back(q);
    }
  const int m = static_cast<int>(out.support.size());
  if (m > 45)
    throw std::runtime_error("certified tree support too large");

  std::vector<std::pair<uint64_t, uint64_t>> cuts;
  for (uint64_t S = 1; S < full; S += 2) {
    uint64_t crossing = 0, weight = 0;
    for (int i = 0; i < m; ++i) {
      const auto &e = out.support[i];
      if (((S >> e.u) & 1ULL) != ((S >> e.v) & 1ULL)) {
        crossing |= uint64_t(1) << i;
        weight += multiplicity[i];
      }
    }
    if (weight < 2 * D)
      throw std::runtime_error("symmetrized HK cut certificate failed");
    cuts.push_back({crossing, weight});
  }

  __extension__ typedef unsigned __int128 wide_uint;
  bool found = false, capped = false;
  uint64_t best_num = 0, best_den = 1;
  uint64_t best_mask = 0;
  auto evaluate = [&](uint64_t mask) {
    uint64_t worst_num = 0, worst_den = 1;
    for (auto [crossing, weight] : cuts) {
      uint64_t count = std::popcount(mask & crossing);
      uint64_t num = D * count;
      if (static_cast<wide_uint>(num) * worst_den >
          static_cast<wide_uint>(worst_num) * weight) {
        worst_num = num;
        worst_den = weight;
      }
    }
    if (!found || static_cast<wide_uint>(worst_num) * best_den <
                      static_cast<wide_uint>(best_num) * worst_den) {
      found = true;
      best_num = worst_num;
      best_den = worst_den;
      best_mask = mask;
    }
  };
  std::function<void(int, int, DSU, uint64_t)> dfs =
      [&](int idx, int need, DSU dsu, uint64_t mask) {
        if (capped)
          return;
        if (++out.search_nodes > node_cap) {
          capped = true;
          return;
        }
        if (need == 0) {
          ++out.trees_tested;
          evaluate(mask);
          return;
        }
        if (idx >= m || m - idx < need)
          return;
        DSU next = dsu;
        if (next.unite(out.support[idx].u, out.support[idx].v))
          dfs(idx + 1, need - 1, next, mask | (uint64_t(1) << idx));
        dfs(idx + 1, need, dsu, mask);
      };
  dfs(0, n - 1, DSU(n), 0);
  out.complete = !capped;
  if (!found && capped)
    return out;
  if (!found)
    throw std::runtime_error("no supported spanning tree found before search cap");
  const uint64_t divisor = std::gcd(best_num, best_den);
  out.beta_num = best_num / divisor;
  out.beta_den = best_den / divisor;
  for (int i = 0; i < m; ++i)
    if (best_mask & (uint64_t(1) << i))
      out.tree_ids.push_back(i);
  return out;
}

} // namespace batsp
