#pragma once
#include <algorithm>
#include <cstdint>
#include <limits>
#include <queue>
#include <random>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

namespace batsp {

struct Digraph {
  int n = 0;
  std::vector<std::vector<uint8_t>> a;
  Digraph() = default;
  explicit Digraph(int n_) : n(n_), a(n_, std::vector<uint8_t>(n_, 0)) {}
  void add_arc(int u, int v) {
    if (u != v)
      a[u][v] = 1;
  }
  bool has_arc(int u, int v) const { return a[u][v] != 0; }
  int arc_count() const {
    int m = 0;
    for (int u = 0; u < n; ++u)
      for (int v = 0; v < n; ++v)
        m += (u != v && a[u][v]);
    return m;
  }
  std::vector<std::pair<int, int>> arcs() const {
    std::vector<std::pair<int, int>> e;
    for (int u = 0; u < n; ++u)
      for (int v = 0; v < n; ++v)
        if (u != v && a[u][v])
          e.emplace_back(u, v);
    return e;
  }
  std::vector<int> out_neighbors(int u) const {
    std::vector<int> r;
    for (int v = 0; v < n; ++v)
      if (a[u][v])
        r.push_back(v);
    return r;
  }
  std::vector<int> in_neighbors(int v) const {
    std::vector<int> r;
    for (int u = 0; u < n; ++u)
      if (a[u][v])
        r.push_back(u);
    return r;
  }
};

inline std::vector<std::vector<int>>
all_pairs_unweighted_dist(const Digraph &g) {
  const int INF = 1e9;
  std::vector<std::vector<int>> d(g.n, std::vector<int>(g.n, INF));
  for (int s = 0; s < g.n; ++s) {
    std::queue<int> q;
    d[s][s] = 0;
    q.push(s);
    while (!q.empty()) {
      int u = q.front();
      q.pop();
      for (int v = 0; v < g.n; ++v)
        if (g.a[u][v] && d[s][v] == INF) {
          d[s][v] = d[s][u] + 1;
          q.push(v);
        }
    }
  }
  return d;
}

inline Digraph graph_power(const Digraph &g, int p) {
  auto d = all_pairs_unweighted_dist(g);
  Digraph h(g.n);
  for (int u = 0; u < g.n; ++u)
    for (int v = 0; v < g.n; ++v) {
      if (u != v && d[u][v] >= 1 && d[u][v] <= p)
        h.add_arc(u, v);
    }
  return h;
}

inline bool strongly_connected(const Digraph &g) {
  if (g.n <= 1)
    return true;
  auto reach = [&](bool rev) {
    std::vector<int> vis(g.n, 0);
    std::queue<int> q;
    q.push(0);
    vis[0] = 1;
    while (!q.empty()) {
      int u = q.front();
      q.pop();
      for (int v = 0; v < g.n; ++v) {
        bool e = rev ? g.a[v][u] : g.a[u][v];
        if (e && !vis[v]) {
          vis[v] = 1;
          q.push(v);
        }
      }
    }
    return std::all_of(vis.begin(), vis.end(), [](int x) { return x; });
  };
  return reach(false) && reach(true);
}

struct DSU {
  std::vector<int> p, r;
  explicit DSU(int n = 0) : p(n), r(n, 0) {
    for (int i = 0; i < n; ++i)
      p[i] = i;
  }
  int find(int x) { return p[x] == x ? x : p[x] = find(p[x]); }
  bool unite(int a, int b) {
    a = find(a);
    b = find(b);
    if (a == b)
      return false;
    if (r[a] < r[b])
      std::swap(a, b);
    p[b] = a;
    if (r[a] == r[b])
      r[a]++;
    return true;
  }
};

inline Digraph split_vertex_forced(const Digraph &g, int v) {
  // Replace v by v_in=v and a new v_out=n. All old incoming arcs stay at v_in,
  // all old outgoing arcs are moved to v_out, and v_in->v_out is forced.
  // Hamiltonian cycles correspond by contraction, and HK feasibility lifts by
  // assigning x(v_in,v_out)=1.
  Digraph h(g.n + 1);
  int w = g.n;
  for (int u = 0; u < g.n; ++u)
    for (int q = 0; q < g.n; ++q)
      if (u != q && g.a[u][q]) {
        if (u == v)
          h.add_arc(w, q);
        else
          h.add_arc(u, q);
      }
  h.add_arc(v, w);
  return h;
}

inline Digraph random_er_digraph(int n, double p, std::mt19937_64 &rng) {
  std::bernoulli_distribution B(p);
  Digraph g(n);
  for (int u = 0; u < n; ++u)
    for (int v = 0; v < n; ++v)
      if (u != v && B(rng))
        g.add_arc(u, v);
  return g;
}

} // namespace batsp
