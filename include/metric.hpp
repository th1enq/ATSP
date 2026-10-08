#pragma once
#include "graph.hpp"
#include "hamiltonian.hpp"
#include "held_karp.hpp"
#include <algorithm>
#include <limits>

namespace batsp {
using Metric = std::vector<std::vector<int>>;

inline Metric shortest_path_metric(const Digraph &g) {
  auto d = all_pairs_unweighted_dist(g);
  for (int i = 0; i < g.n; ++i)
    for (int j = 0; j < g.n; ++j)
      if (d[i][j] >= 1000000000)
        throw std::runtime_error("graph not strongly connected");
  return d;
}

inline Digraph threshold_graph(const Metric &c, int tau) {
  int n = (int)c.size();
  Digraph g(n);
  for (int u = 0; u < n; ++u)
    for (int v = 0; v < n; ++v)
      if (u != v && c[u][v] <= tau)
        g.add_arc(u, v);
  return g;
}

inline int exact_bottleneck_opt(const Metric &c) {
  std::vector<int> vals;
  int n = (int)c.size();
  for (int u = 0; u < n; ++u)
    for (int v = 0; v < n; ++v)
      if (u != v)
        vals.push_back(c[u][v]);
  std::sort(vals.begin(), vals.end());
  vals.erase(std::unique(vals.begin(), vals.end()), vals.end());
  int lo = 0, hi = (int)vals.size() - 1, ans = -1;
  while (lo <= hi) {
    int mid = (lo + hi) / 2;
    if (hamiltonian_cycle_dp(threshold_graph(c, vals[mid])).exists) {
      ans = vals[mid];
      hi = mid - 1;
    } else
      lo = mid + 1;
  }
  return ans;
}

inline int exact_hk_threshold(const Metric &c) {
  std::vector<int> vals;
  int n = (int)c.size();
  for (int u = 0; u < n; ++u)
    for (int v = 0; v < n; ++v)
      if (u != v)
        vals.push_back(c[u][v]);
  std::sort(vals.begin(), vals.end());
  vals.erase(std::unique(vals.begin(), vals.end()), vals.end());
  int lo = 0, hi = (int)vals.size() - 1, ans = -1;
  while (lo <= hi) {
    int mid = (lo + hi) / 2;
    auto hk = held_karp_feasible_allcuts(threshold_graph(c, vals[mid]));
    if (hk.feasible) {
      ans = vals[mid];
      hi = mid - 1;
    } else
      lo = mid + 1;
  }
  return ans;
}

} // namespace batsp
