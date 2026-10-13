#pragma once
#include "graph.hpp"
#include <cmath>
#include <functional>
#include <limits>
#include <numeric>
#include <random>
#include <set>

namespace batsp {

struct UEdge {
  int u, v;
  double z;
};
struct TreeResult {
  bool found = false;
  double beta = std::numeric_limits<double>::infinity();
  std::vector<int> edge_ids;
  uint64_t trees_tested = 0;
};

inline std::vector<UEdge>
support_edges_from_z(const std::vector<std::vector<double>> &z,
                     double eps = 1e-9) {
  int n = (int)z.size();
  std::vector<UEdge> e;
  for (int u = 0; u < n; ++u)
    for (int v = u + 1; v < n; ++v)
      if (z[u][v] > eps)
        e.push_back({u, v, z[u][v]});
  return e;
}

inline double tree_thinness(int n, const std::vector<UEdge> &edges,
                            const std::vector<int> &tree_ids,
                            uint64_t *worst_cut = nullptr) {
  if (n > 24)
    throw std::runtime_error("exact cut thinness supports n<=24");
  uint64_t full = (1ULL << n) - 1;
  double best = 0;
  uint64_t bestS = 0;
  for (uint64_t S = 1; S < full; ++S) {
    if (!(S & 1ULL))
      continue; // one representative of S/complement
    double denom = 0;
    int num = 0;
    for (size_t i = 0; i < edges.size(); ++i) {
      auto &e = edges[i];
      bool a = (S >> e.u) & 1ULL, b = (S >> e.v) & 1ULL;
      if (a != b)
        denom += e.z;
    }
    if (denom <= 1e-12)
      return std::numeric_limits<double>::infinity();
    for (int id : tree_ids) {
      auto &e = edges[id];
      if ((((S >> e.u) & 1ULL) != 0) != (((S >> e.v) & 1ULL) != 0))
        num++;
    }
    double r = num / denom;
    if (r > best + 1e-14) {
      best = r;
      bestS = S;
    }
  }
  if (worst_cut)
    *worst_cut = bestS;
  return best;
}

inline TreeResult
exact_best_thin_tree_enumerate(int n, const std::vector<UEdge> &edges,
                               uint64_t combo_cap = 50000000ULL) {
  TreeResult ans;
  const int m = (int)edges.size();
  if (n <= 1) {
    ans.found = true;
    ans.beta = 0;
    return ans;
  }
  std::vector<int> chosen;
  uint64_t visits = 0;
  std::function<void(int, int, DSU)> dfs = [&](int idx, int need, DSU dsu) {
    if (visits >= combo_cap)
      return;
    if (need == 0) {
      visits++;
      int root = dsu.find(0);
      for (int v = 1; v < n; ++v)
        if (dsu.find(v) != root)
          return;
      double b = tree_thinness(n, edges, chosen);
      if (b < ans.beta - 1e-12) {
        ans.found = true;
        ans.beta = b;
        ans.edge_ids = chosen;
      }
      return;
    }
    if (idx >= m || m - idx < need)
      return;
    // choose if doesn't create cycle
    DSU d2 = dsu;
    if (d2.unite(edges[idx].u, edges[idx].v)) {
      chosen.push_back(idx);
      dfs(idx + 1, need - 1, d2);
      chosen.pop_back();
    }
    dfs(idx + 1, need, dsu);
  };
  dfs(0, n - 1, DSU(n));
  ans.trees_tested = visits;
  return ans;
}

inline TreeResult weighted_kruskal_tree(int n, const std::vector<UEdge> &edges,
                                        int mode) {
  // mode 0: inverse-z, mode 1: -log(z)
  std::vector<int> ids(edges.size());
  std::iota(ids.begin(), ids.end(), 0);
  auto cost = [&](int id) {
    double z = std::max(edges[id].z, 1e-15);
    return mode == 0 ? 1.0 / z : -std::log(z);
  };
  std::sort(ids.begin(), ids.end(), [&](int a, int b) {
    double ca = cost(a), cb = cost(b);
    if (ca != cb)
      return ca < cb;
    return a < b;
  });
  DSU d(n);
  std::vector<int> T;
  for (int id : ids)
    if (d.unite(edges[id].u, edges[id].v)) {
      T.push_back(id);
      if ((int)T.size() == n - 1)
        break;
    }
  TreeResult r;
  if ((int)T.size() == n - 1) {
    r.found = true;
    r.edge_ids = T;
    r.beta = tree_thinness(n, edges, T);
    r.trees_tested = 1;
  }
  return r;
}

inline TreeResult random_tree_search(int n, const std::vector<UEdge> &edges,
                                     int trials, std::mt19937_64 &rng) {
  TreeResult best;
  std::vector<int> ids(edges.size());
  std::iota(ids.begin(), ids.end(), 0);
  for (int t = 0; t < trials; ++t) {
    // exponential clocks biased by z: key=-log(U)/z
    std::vector<std::pair<double, int>> keys;
    keys.reserve(edges.size());
    std::uniform_real_distribution<double> U(1e-12, 1.0);
    for (int id : ids)
      keys.push_back({-std::log(U(rng)) / std::max(edges[id].z, 1e-12), id});
    std::sort(keys.begin(), keys.end());
    DSU d(n);
    std::vector<int> T;
    for (auto [k, id] : keys)
      if (d.unite(edges[id].u, edges[id].v)) {
        T.push_back(id);
        if ((int)T.size() == n - 1)
          break;
      }
    if ((int)T.size() != n - 1)
      continue;
    double b = tree_thinness(n, edges, T);
    best.trees_tested++;
    if (b < best.beta) {
      best.found = true;
      best.beta = b;
      best.edge_ids = T;
    }
  }
  return best;
}

inline TreeResult local_swap_improve(int n, const std::vector<UEdge> &edges,
                                     TreeResult start, int max_rounds = 100) {
  if (!start.found)
    return start;
  std::vector<uint8_t> in(edges.size(), 0);
  for (int id : start.edge_ids)
    in[id] = 1;
  for (int round = 0; round < max_rounds; ++round) {
    bool improved = false;
    double cur = start.beta;
    std::vector<int> bestT;
    for (int add = 0; add < (int)edges.size(); ++add)
      if (!in[add]) {
        // path in current tree between endpoints; any removed edge on cycle
        // keeps tree.
        std::vector<std::vector<std::pair<int, int>>> adj(n);
        for (int id : start.edge_ids) {
          auto &e = edges[id];
          adj[e.u].push_back({e.v, id});
          adj[e.v].push_back({e.u, id});
        }
        std::vector<int> pv(n, -1), pe(n, -1);
        std::vector<int> q = {edges[add].u};
        pv[q[0]] = q[0];
        for (size_t qi = 0; qi < q.size(); ++qi) {
          int u = q[qi];
          for (auto [v, id] : adj[u])
            if (pv[v] < 0) {
              pv[v] = u;
              pe[v] = id;
              q.push_back(v);
            }
        }
        int v = edges[add].v;
        while (v != edges[add].u && v >= 0) {
          int rem = pe[v];
          std::vector<int> T = start.edge_ids;
          for (int &x : T)
            if (x == rem) {
              x = add;
              break;
            }
          double b = tree_thinness(n, edges, T);
          if (b < cur - 1e-12) {
            cur = b;
            bestT = T;
          }
          v = pv[v];
        }
      }
    if (!bestT.empty()) {
      start.edge_ids = bestT;
      start.beta = cur;
      std::fill(in.begin(), in.end(), 0);
      for (int id : bestT)
        in[id] = 1;
      improved = true;
    }
    if (!improved)
      break;
  }
  return start;
}

} // namespace batsp
