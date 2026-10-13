#pragma once
#include "graph.hpp"
#include "held_karp.hpp"
#include "thin_tree.hpp"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <queue>
#include <stdexcept>
#include <unordered_set>

namespace batsp {

struct Dinic {
  struct E {
    int to, rev, cap, orig;
  };
  int n;
  std::vector<std::vector<E>> g;
  std::vector<int> level, it;
  explicit Dinic(int n) : n(n), g(n), level(n), it(n) {}
  std::pair<int, int> add_edge(int s, int t, int cap) {
    E a{t, (int)g[t].size(), cap, cap}, b{s, (int)g[s].size(), 0, 0};
    g[s].push_back(a);
    g[t].push_back(b);
    return {s, (int)g[s].size() - 1};
  }
  bool bfs(int s, int t) {
    std::fill(level.begin(), level.end(), -1);
    std::queue<int> q;
    q.push(s);
    level[s] = 0;
    while (!q.empty()) {
      int v = q.front();
      q.pop();
      for (auto &e : g[v])
        if (e.cap > 0 && level[e.to] < 0) {
          level[e.to] = level[v] + 1;
          q.push(e.to);
        }
    }
    return level[t] >= 0;
  }
  int dfs(int v, int t, int f) {
    if (v == t)
      return f;
    for (int &i = it[v]; i < (int)g[v].size(); ++i) {
      E &e = g[v][i];
      if (e.cap > 0 && level[v] + 1 == level[e.to]) {
        int d = dfs(e.to, t, std::min(f, e.cap));
        if (d) {
          e.cap -= d;
          g[e.to][e.rev].cap += d;
          return d;
        }
      }
    }
    return 0;
  }
  int maxflow(int s, int t) {
    int flow = 0, inf = 1e9;
    while (bfs(s, t)) {
      std::fill(it.begin(), it.end(), 0);
      while (int f = dfs(s, t, inf))
        flow += f;
    }
    return flow;
  }
  int used(std::pair<int, int> ref) const {
    auto [u, i] = ref;
    return g[u][i].orig - g[u][i].cap;
  }
};

struct BoundedArc {
  int u, v, lo, hi;
};
struct CirculationResult {
  bool feasible = false;
  std::vector<int> flow;
};

inline CirculationResult
feasible_circulation(int n, const std::vector<BoundedArc> &A) {
  int SS = n, TT = n + 1;
  Dinic D(n + 2);
  std::vector<int> bal(n, 0);
  std::vector<std::pair<int, int>> refs;
  refs.reserve(A.size());
  for (auto &e : A) {
    if (e.lo < 0 || e.hi < e.lo)
      return {};
    refs.push_back(D.add_edge(e.u, e.v, e.hi - e.lo));
    bal[e.u] -= e.lo;
    bal[e.v] += e.lo;
  }
  int need = 0;
  for (int v = 0; v < n; ++v) {
    if (bal[v] > 0) {
      D.add_edge(SS, v, bal[v]);
      need += bal[v];
    } else if (bal[v] < 0)
      D.add_edge(v, TT, -bal[v]);
  }
  int got = D.maxflow(SS, TT);
  if (got != need)
    return {};
  CirculationResult r;
  r.feasible = true;
  r.flow.resize(A.size());
  for (size_t i = 0; i < A.size(); ++i)
    r.flow[i] = A[i].lo + D.used(refs[i]);
  return r;
}

struct AKSCircuitResult {
  bool feasible = false;
  int k_bound = 0;
  int max_visits = 0;
  std::vector<std::vector<int>> multiplicity;
  std::vector<int>
      circuit; // cyclic vertex sequence without repeated final start
  std::vector<int> ham_cycle; // vertex cycle with repeated first at end
  int power_bound = 0;
};

inline int ceil_tol(double x) { return (int)std::ceil(x - 1e-9); }

struct AKSExactData {
  uint64_t denominator;
  std::vector<uint64_t> x_numerators; // aligned with HKResult::arcs
  uint64_t beta_num;
  uint64_t beta_den;
};

__extension__ typedef unsigned __int128 AKSWideUInt;

inline int ceil_exact_ratio(AKSWideUInt numerator, AKSWideUInt denominator) {
  if (denominator == 0)
    throw std::runtime_error("AKS: zero exact denominator");
  AKSWideUInt value = numerator / denominator + (numerator % denominator != 0);
  if (value > static_cast<AKSWideUInt>(std::numeric_limits<int>::max()))
    throw std::runtime_error("AKS: exact capacity too large");
  return static_cast<int>(value);
}

inline AKSCircuitResult
aks_round_from_thin_tree(const Digraph &G, const HKResult &hk,
                         const std::vector<UEdge> &support,
                         const std::vector<int> &tree_ids, double beta,
                         const AKSExactData *exact = nullptr) {
  const int n = G.n;
  if (!hk.feasible)
    throw std::runtime_error("AKS: HK infeasible");
  if (exact && (exact->denominator == 0 || exact->beta_den == 0 ||
                exact->x_numerators.size() != hk.arcs.size()))
    throw std::runtime_error("AKS: invalid exact certificate");
  std::vector<std::vector<double>> X(n, std::vector<double>(n, 0.0));
  std::vector<std::vector<uint64_t>> Xnum(n, std::vector<uint64_t>(n, 0));
  for (size_t i = 0; i < hk.arcs.size(); ++i) {
    auto [u, v] = hk.arcs[i];
    X[u][v] = hk.x[i];
    if (exact)
      Xnum[u][v] = exact->x_numerators[i];
  }
  // orient tree using any supported positive HK arc
  std::vector<std::vector<uint8_t>> tree_arc(n, std::vector<uint8_t>(n, 0));
  for (int id : tree_ids) {
    auto e = support[id];
    if (exact ? Xnum[e.u][e.v] > 0 : X[e.u][e.v] > 1e-9)
      tree_arc[e.u][e.v] = 1;
    else if (exact ? Xnum[e.v][e.u] > 0 : X[e.v][e.u] > 1e-9)
      tree_arc[e.v][e.u] = 1;
    else
      throw std::runtime_error("AKS: tree edge unsupported by x");
  }

  // split graph nodes: vin=2v, vout=2v+1.
  std::vector<BoundedArc> B;
  std::vector<std::pair<int, int>> orig_arc_of_bounded; // -1,-1 vertex arcs
  std::vector<int> orig_bidx;
  for (int v = 0; v < n; ++v) {
    double sumu = 0;
    for (int w = 0; w < n; ++w)
      if (G.has_arc(v, w))
        sumu += (tree_arc[v][w] ? 1.0 : 0.0) + 2.0 * beta * X[v][w];
    int cap = exact ?
        std::accumulate(tree_arc[v].begin(), tree_arc[v].end(), 0) +
            ceil_exact_ratio(2 * static_cast<AKSWideUInt>(exact->beta_num), exact->beta_den)
        : ceil_tol(sumu);
    if (cap < 0)
      cap = 0;
    B.push_back({2 * v, 2 * v + 1, 0, cap});
    orig_arc_of_bounded.push_back({-1, -1});
  }
  for (size_t i = 0; i < hk.arcs.size(); ++i) {
    auto [u, v] = hk.arcs[i];
    int lo = tree_arc[u][v] ? 1 : 0;
    double up = lo + 2.0 * beta * X[u][v];
    int hi = exact ? lo + ceil_exact_ratio(
                  2 * static_cast<AKSWideUInt>(exact->beta_num) * exact->x_numerators[i],
                  static_cast<AKSWideUInt>(exact->beta_den) * exact->denominator)
                   : ceil_tol(up);
    if (hi < lo)
      hi = lo;
    orig_bidx.push_back((int)B.size());
    B.push_back({2 * u + 1, 2 * v, lo, hi});
    orig_arc_of_bounded.push_back({u, v});
  }
  auto cr = feasible_circulation(2 * n, B);
  if (!cr.feasible)
    return {};
  AKSCircuitResult out;
  out.feasible = true;
  out.k_bound = exact ? ceil_exact_ratio(4 * static_cast<AKSWideUInt>(exact->beta_num),
                                         exact->beta_den) : ceil_tol(4.0 * beta);
  out.power_bound = 2 * out.k_bound - 1;
  out.multiplicity.assign(n, std::vector<int>(n, 0));
  for (size_t bi = 0; bi < B.size(); ++bi) {
    auto [u, v] = orig_arc_of_bounded[bi];
    if (u >= 0)
      out.multiplicity[u][v] = cr.flow[bi];
  }
  // validate balances and build Euler circuit via explicit copies
  // (small-experiment implementation)
  int total = 0;
  std::vector<int> outdeg(n, 0), indeg(n, 0);
  for (int u = 0; u < n; ++u)
    for (int v = 0; v < n; ++v) {
      int f = out.multiplicity[u][v];
      outdeg[u] += f;
      indeg[v] += f;
      total += f;
    }
  for (int v = 0; v < n; ++v)
    if (outdeg[v] != indeg[v])
      throw std::runtime_error("AKS: circulation imbalance");
  int start = 0;
  while (start < n && outdeg[start] == 0)
    start++;
  if (start == n)
    return {};
  std::vector<std::vector<int>> cnt = out.multiplicity;
  std::vector<int> st{start}, tour;
  while (!st.empty()) {
    int u = st.back(), v = -1;
    for (int w = 0; w < n; ++w)
      if (cnt[u][w] > 0) {
        v = w;
        break;
      }
    if (v < 0) {
      tour.push_back(u);
      st.pop_back();
    } else {
      cnt[u][v]--;
      st.push_back(v);
    }
  }
  if ((int)tour.size() != total + 1)
    return {};
  std::reverse(tour.begin(), tour.end());
  if (tour.front() != tour.back())
    return {};
  tour.pop_back();
  out.circuit = tour;
  std::vector<int> visits(n, 0);
  for (int v : tour)
    visits[v]++;
  out.max_visits = *std::max_element(visits.begin(), visits.end());

  // Lemma 2/3: partition into pieces of size k, find SDR by bipartite matching
  // pieces->vertices.
  int k = out.k_bound;
  if (k <= 0)
    return {};
  int L = (total + k - 1) / k;
  std::vector<std::vector<int>> piece_vertices(L),
      positions(L, std::vector<int>(n, -1));
  for (int pi = 0; pi < L; ++pi) {
    int lo = pi * k, hi = std::min(total, (pi + 1) * k);
    std::vector<uint8_t> seen(n, 0);
    for (int pos = lo; pos < hi; ++pos) {
      int v = tour[pos];
      if (!seen[v]) {
        seen[v] = 1;
        piece_vertices[pi].push_back(v);
        positions[pi][v] = pos;
      }
    }
  }
  std::vector<int> matchV(n, -1);
  std::function<bool(int, std::vector<uint8_t> &)> aug =
      [&](int p, std::vector<uint8_t> &seen) {
        for (int v : piece_vertices[p])
          if (!seen[v]) {
            seen[v] = 1;
            if (matchV[v] < 0 || aug(matchV[v], seen)) {
              matchV[v] = p;
              return true;
            }
          }
        return false;
      };
  for (int p = 0; p < L; ++p) {
    std::vector<uint8_t> seen(n, 0);
    if (!aug(p, seen))
      throw std::runtime_error("AKS: Hall matching unexpectedly failed");
  }
  std::vector<int> chosenPos(n, -1);
  for (int v = 0; v < n; ++v)
    if (matchV[v] >= 0) {
      int p = matchV[v];
      chosenPos[v] = positions[p][v];
    }
  for (int v = 0; v < n; ++v)
    if (chosenPos[v] < 0) {
      for (int pos = 0; pos < total; ++pos)
        if (tour[pos] == v) {
          chosenPos[v] = pos;
          break;
        }
      if (chosenPos[v] < 0)
        throw std::runtime_error("AKS: circuit not spanning");
    }
  std::vector<std::pair<int, int>> ord;
  for (int v = 0; v < n; ++v)
    ord.push_back({chosenPos[v], v});
  std::sort(ord.begin(), ord.end());
  for (auto [pos, v] : ord)
    out.ham_cycle.push_back(v);
  if (!out.ham_cycle.empty())
    out.ham_cycle.push_back(out.ham_cycle.front());
  // Verify each shortcut is within power bound in G.
  auto d = all_pairs_unweighted_dist(G);
  for (int i = 0; i < n; ++i) {
    int u = out.ham_cycle[i], v = out.ham_cycle[i + 1];
    if (d[u][v] > out.power_bound)
      throw std::runtime_error("AKS: shortcut exceeds power bound");
  }
  return out;
}

inline int bottleneck_cost_of_cycle(const Metric &c,
                                    const std::vector<int> &cyc) {
  if (cyc.size() < 2)
    return 0;
  int b = 0;
  for (size_t i = 1; i < cyc.size(); ++i)
    b = std::max(b, c[cyc[i - 1]][cyc[i]]);
  return b;
}

} // namespace batsp
