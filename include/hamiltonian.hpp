#pragma once
#include "graph.hpp"
#include <cstdint>
#include <limits>
#include <vector>

namespace batsp {

struct HamResult {
  bool exists = false;
  std::vector<int> cycle;
};

inline HamResult hamiltonian_cycle_dp(const Digraph &g) {
  HamResult out;
  const int n = g.n;
  if (n == 0)
    return out;
  if (n == 1) {
    out.exists = true;
    out.cycle = {0, 0};
    return out;
  }
  if (n > 22)
    throw std::runtime_error("Hamiltonian bitmask DP supports n<=22");
  const uint32_t N = 1u << n;
  std::vector<uint32_t> reach(N, 0u);
  std::vector<std::vector<int8_t>> parent; // only allocate for modest n
  bool keep_parent = n <= 18;
  if (keep_parent)
    parent.assign(N, std::vector<int8_t>(n, -1));
  reach[1u] = 1u; // path starting at 0 and ending at 0
  for (uint32_t S = 1; S < N; ++S) {
    if (!(S & 1u))
      continue;
    uint32_t ends = reach[S];
    while (ends) {
      int u = __builtin_ctz(ends);
      ends &= ends - 1;
      for (int v = 1; v < n; ++v)
        if (!(S & (1u << v)) && g.has_arc(u, v)) {
          uint32_t T = S | (1u << v);
          if (!(reach[T] & (1u << v)) && keep_parent)
            parent[T][v] = (int8_t)u;
          reach[T] |= (1u << v);
        }
    }
  }
  uint32_t full = N - 1;
  int end = -1;
  for (int u = 1; u < n; ++u)
    if ((reach[full] & (1u << u)) && g.has_arc(u, 0)) {
      end = u;
      break;
    }
  if (end < 0)
    return out;
  out.exists = true;
  if (keep_parent) {
    std::vector<int> rev;
    rev.push_back(0); // will reconstruct separately
    uint32_t S = full;
    int cur = end;
    std::vector<int> path;
    path.push_back(cur);
    while (cur != 0) {
      int p = parent[S][cur];
      if (p < 0)
        break;
      S ^= (1u << cur);
      cur = p;
      path.push_back(cur);
    }
    std::reverse(path.begin(), path.end());
    if ((int)path.size() == n) {
      path.push_back(0);
      out.cycle = std::move(path);
    }
  }
  return out;
}

inline int minimum_hamiltonian_power(const Digraph &g, int max_p = -1) {
  auto d = all_pairs_unweighted_dist(g);
  int diam = 0;
  for (int u = 0; u < g.n; ++u)
    for (int v = 0; v < g.n; ++v)
      if (u != v) {
        if (d[u][v] >= 1000000000)
          return -1;
        diam = std::max(diam, d[u][v]);
      }
  if (max_p < 0)
    max_p = diam;
  for (int p = 1; p <= max_p; ++p) {
    Digraph h(g.n);
    for (int u = 0; u < g.n; ++u)
      for (int v = 0; v < g.n; ++v)
        if (u != v && d[u][v] <= p)
          h.add_arc(u, v);
    if (hamiltonian_cycle_dp(h).exists)
      return p;
  }
  return -1;
}

} // namespace batsp
