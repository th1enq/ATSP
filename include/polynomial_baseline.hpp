#pragma once

#include "certified_tree.hpp"
#include <algorithm>
#include <cstdint>
#include <limits>
#include <map>
#include <numeric>
#include <queue>
#include <stdexcept>
#include <vector>

namespace batsp {

// Exact integral directed flow for the input range of RationalArc. A sum of
// at most INT_MAX arcs, each at most UINT64_MAX, fits in unsigned __int128.
struct WideDinic {
  __extension__ typedef unsigned __int128 Wide;
  struct Edge { int to, rev; Wide cap; };
  std::vector<std::vector<Edge>> graph;
  std::vector<int> level, next;

  explicit WideDinic(int n) : graph(n), level(n), next(n) {}
  void add(int u, int v, Wide cap) {
    if (!cap) return;
    Edge a{v, static_cast<int>(graph[v].size()), cap};
    Edge b{u, static_cast<int>(graph[u].size()), 0};
    graph[u].push_back(a);
    graph[v].push_back(b);
  }
  bool bfs(int s, int t) {
    std::fill(level.begin(), level.end(), -1);
    std::queue<int> queue;
    level[s] = 0;
    queue.push(s);
    while (!queue.empty()) {
      int u = queue.front(); queue.pop();
      for (const auto& e : graph[u])
        if (e.cap && level[e.to] < 0) {
          level[e.to] = level[u] + 1;
          queue.push(e.to);
        }
    }
    return level[t] >= 0;
  }
  Wide dfs(int u, int t, Wide available) {
    if (u == t) return available;
    for (int& i = next[u]; i < static_cast<int>(graph[u].size()); ++i) {
      Edge& e = graph[u][i];
      if (!e.cap || level[e.to] != level[u] + 1) continue;
      Wide sent = dfs(e.to, t, std::min(available, e.cap));
      if (!sent) continue;
      e.cap -= sent;
      graph[e.to][e.rev].cap += sent;
      return sent;
    }
    return 0;
  }
  Wide flow(int s, int t) {
    Wide total = 0;
    while (bfs(s, t)) {
      std::fill(next.begin(), next.end(), 0);
      while (Wide sent = dfs(s, t, static_cast<Wide>(-1))) total += sent;
    }
    return total;
  }
};

inline CertifiedTreeResult construct_polynomial_baseline(const CertifiedTreeInput& input) {
  const int n = input.n;
  const uint64_t D = input.denominator;
  if (n < 2 || D == 0 || input.arcs.size() > static_cast<size_t>(std::numeric_limits<int>::max()))
    throw std::runtime_error("invalid polynomial baseline dimensions");
  std::vector<WideDinic::Wide> incoming(n), outgoing(n);
  std::vector<std::vector<uint8_t>> seen(n, std::vector<uint8_t>(n));
  std::vector<std::vector<uint64_t>> arc_numerators(n, std::vector<uint64_t>(n));
  std::map<std::pair<int,int>, WideDinic::Wide> support_numerators;
  Digraph graph(n);
  CertifiedTreeResult result;
  result.complete = true;
  if (static_cast<WideDinic::Wide>(2) * D <= static_cast<uint64_t>(n - 1)) {
    result.beta_num = D;
    result.beta_den = 1;
  } else {
    result.beta_num = static_cast<uint64_t>(n - 1);
    result.beta_den = 2;
  }
  uint64_t divisor = std::gcd(result.beta_num, result.beta_den);
  result.beta_num /= divisor;
  result.beta_den /= divisor;

  for (const auto& arc : input.arcs) {
    if (arc.u < 0 || arc.u >= n || arc.v < 0 || arc.v >= n || arc.u == arc.v ||
        seen[arc.u][arc.v] || arc.numerator > D)
      throw std::runtime_error("invalid or duplicate rational HK arc");
    seen[arc.u][arc.v] = 1;
    arc_numerators[arc.u][arc.v] = arc.numerator;
    graph.add_arc(arc.u, arc.v);
    outgoing[arc.u] += arc.numerator;
    incoming[arc.v] += arc.numerator;
    if (arc.numerator)
      support_numerators[std::minmax(arc.u, arc.v)] += arc.numerator;
  }
  for (int v = 0; v < n; ++v)
    if (incoming[v] != D || outgoing[v] != D)
      throw std::runtime_error("rational HK degree certificate failed");

  // Root-v cuts in both directions cover every nontrivial directed cut.
  for (int v = 1; v < n; ++v)
    for (int orientation = 0; orientation < 2; ++orientation) {
      WideDinic cut(n);
      for (const auto& arc : input.arcs)
        cut.add(arc.u, arc.v, arc.numerator);
      if (cut.flow(orientation ? v : 0, orientation ? 0 : v) < D)
        throw std::runtime_error("rational HK subtour certificate failed");
    }

  result.hk_for_aks.feasible = true;
  result.hk_for_aks.arcs = graph.arcs();
  for (auto [u, v] : graph.arcs()) {
    uint64_t numerator = arc_numerators[u][v];
    result.hk_for_aks.x.push_back(static_cast<double>(numerator) / D);
    result.exact_x_numerators.push_back(numerator);
  }
  for (const auto& [pair, numerator] : support_numerators)
    result.support.push_back({pair.first, pair.second,
                              static_cast<double>(numerator) / D});
  std::vector<std::vector<std::pair<int,int>>> adjacency(n);
  for (int id = 0; id < static_cast<int>(result.support.size()); ++id) {
    const auto& e = result.support[id];
    adjacency[e.u].push_back({e.v, id});
    adjacency[e.v].push_back({e.u, id});
  }
  std::vector<uint8_t> visited(n);
  std::queue<int> queue;
  visited[0] = 1; queue.push(0);
  while (!queue.empty()) {
    int u = queue.front(); queue.pop();
    for (auto [v, id] : adjacency[u])
      if (!visited[v]) {
        visited[v] = 1;
        result.tree_ids.push_back(id);
        queue.push(v);
      }
  }
  if (result.tree_ids.size() != static_cast<size_t>(n - 1))
    throw std::runtime_error("positive HK support is disconnected");
  // Every cut of the symmetrized HK vector has mass >= 2, while a spanning
  // tree crosses it at most n-1 times. Also each chosen edge has positive
  // integer multiplicity in D*z, so tree crossing <= D*z crossing. Thus
  // beta=min(D,(n-1)/2) is valid exactly.
  return result;
}

} // namespace batsp
