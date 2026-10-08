#pragma once
#include "graph.hpp"
#include "simplex.hpp"
#include <cmath>
#include <map>
#include <optional>
#include <unordered_map>

namespace batsp {

struct HKResult {
  bool feasible = false;
  std::vector<std::pair<int, int>> arcs;
  std::vector<double> x;
  double max_eq_error = 0.0;
  double min_cut_out = 0.0;
};

inline HKResult held_karp_feasible_allcuts(const Digraph &g,
                                           double tol = 1e-7) {
  HKResult res;
  res.arcs = g.arcs();
  const int m = (int)res.arcs.size();
  if (g.n == 0)
    return res;
  if (g.n == 1) {
    res.feasible = true;
    return res;
  }
  if (m == 0)
    return res;

  std::vector<std::vector<double>> A;
  std::vector<double> b;
  auto add_leq = [&](const std::vector<double> &row, double rhs) {
    A.push_back(row);
    b.push_back(rhs);
  };
  auto add_eq = [&](const std::vector<double> &row, double rhs) {
    add_leq(row, rhs);
    std::vector<double> neg = row;
    for (double &v : neg)
      v = -v;
    add_leq(neg, -rhs);
  };

  for (int v = 0; v < g.n; ++v) {
    std::vector<double> out(m, 0.0), in(m, 0.0);
    for (int i = 0; i < m; ++i) {
      auto [u, w] = res.arcs[i];
      if (u == v)
        out[i] = 1.0;
      if (w == v)
        in[i] = 1.0;
    }
    add_eq(out, 1.0);
    add_eq(in, 1.0);
  }

  if (g.n > 24)
    throw std::runtime_error("all-cuts HK solver supports n<=24");
  const uint64_t full = (uint64_t(1) << g.n) - 1;
  // Fix vertex 0 in S to avoid complementary duplication? Directed cut
  // constraints for S and complement differ, so we must include all nonempty
  // proper S.
  for (uint64_t S = 1; S < full; ++S) {
    std::vector<double> row(m, 0.0);
    for (int i = 0; i < m; ++i) {
      auto [u, v] = res.arcs[i];
      bool iu = (S >> u) & 1ULL, iv = (S >> v) & 1ULL;
      if (iu && !iv)
        row[i] = -1.0; // -x(delta+) <= -1
    }
    add_leq(row, -1.0);
  }

  std::vector<double> c(m, 0.0), sol;
  LPSolver lp(A, b, c);
  double opt = lp.Solve(sol);
  if (!std::isfinite(opt) || opt < -1e100)
    return res;

  // numerical validation
  double maxeq = 0.0;
  for (int v = 0; v < g.n; ++v) {
    double so = 0, si = 0;
    for (int i = 0; i < m; ++i) {
      auto [u, w] = res.arcs[i];
      if (u == v)
        so += sol[i];
      if (w == v)
        si += sol[i];
    }
    maxeq = std::max({maxeq, std::abs(so - 1.0), std::abs(si - 1.0)});
  }
  double mincut = 1e100;
  for (uint64_t S = 1; S < full; ++S) {
    double cut = 0;
    for (int i = 0; i < m; ++i) {
      auto [u, v] = res.arcs[i];
      if (((S >> u) & 1ULL) && !((S >> v) & 1ULL))
        cut += sol[i];
    }
    mincut = std::min(mincut, cut);
  }
  bool nonneg =
      std::all_of(sol.begin(), sol.end(), [&](double z) { return z >= -tol; });
  res.feasible = nonneg && maxeq <= 1e-5 && mincut >= 1.0 - 1e-5;
  if (res.feasible) {
    for (double &v : sol)
      if (std::abs(v) < 1e-10)
        v = 0;
    res.x = std::move(sol);
    res.max_eq_error = maxeq;
    res.min_cut_out = mincut;
  }
  return res;
}

inline std::vector<std::vector<double>> symmetrized_z(const HKResult &hk,
                                                      int n) {
  std::vector<std::vector<double>> z(n, std::vector<double>(n, 0.0));
  for (size_t i = 0; i < hk.arcs.size(); ++i) {
    auto [u, v] = hk.arcs[i];
    z[u][v] += hk.x[i];
    z[v][u] += hk.x[i];
  }
  // This currently doubles into symmetric entries; each unordered z value is
  // z[u][v]. Because every directed x contributes to both symmetric matrix
  // entries.
  return z;
}

inline double z_cut_weight(const std::vector<std::vector<double>> &z,
                           uint64_t S) {
  int n = (int)z.size();
  double sum = 0;
  for (int u = 0; u < n; ++u)
    if ((S >> u) & 1ULL)
      for (int v = u + 1; v < n; ++v) {
        bool iu = true, iv = ((S >> v) & 1ULL);
        if (iu != iv)
          sum += z[u][v];
      }
  for (int u = 0; u < n; ++u)
    if (!((S >> u) & 1ULL)) {
      // no-op; pairs already handled only when u in S and u<v misses crossing
      // with u outside<v inside.
    }
  // robust re-compute all unordered pairs exactly once
  sum = 0;
  for (int u = 0; u < n; ++u)
    for (int v = u + 1; v < n; ++v)
      if ((((S >> u) & 1ULL) != 0) != (((S >> v) & 1ULL) != 0))
        sum += z[u][v];
  return sum;
}

} // namespace batsp
