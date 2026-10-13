#pragma once
#include <algorithm>
#include <cmath>
#include <limits>
#include <vector>

namespace batsp {

// Two-phase simplex, adapted from the standard competitive-programming
// implementation. Solves max c^T x subject to A x <= b, x >= 0.
class LPSolver {
  static constexpr double EPS = 1e-9;
  static constexpr double INF = std::numeric_limits<double>::infinity();
  int m, n;
  std::vector<int> B, N;
  std::vector<std::vector<double>> D;

  void Pivot(int r, int s) {
    double inv = 1.0 / D[r][s];
    for (int i = 0; i < m + 2; ++i)
      if (i != r)
        for (int j = 0; j < n + 2; ++j)
          if (j != s)
            D[i][j] -= D[r][j] * D[i][s] * inv;
    for (int j = 0; j < n + 2; ++j)
      if (j != s)
        D[r][j] *= inv;
    for (int i = 0; i < m + 2; ++i)
      if (i != r)
        D[i][s] *= -inv;
    D[r][s] = inv;
    std::swap(B[r], N[s]);
  }

  bool Simplex(int phase) {
    int x = phase == 1 ? m + 1 : m;
    while (true) {
      int s = -1;
      for (int j = 0; j <= n; ++j) {
        if (phase == 2 && N[j] == -1)
          continue;
        if (s == -1 || D[x][j] < D[x][s] - EPS ||
            (std::abs(D[x][j] - D[x][s]) <= EPS && N[j] < N[s]))
          s = j;
      }
      if (D[x][s] >= -EPS)
        return true;
      int r = -1;
      for (int i = 0; i < m; ++i) {
        if (D[i][s] <= EPS)
          continue;
        if (r == -1)
          r = i;
        else {
          double lhs = D[i][n + 1] / D[i][s];
          double rhs = D[r][n + 1] / D[r][s];
          if (lhs < rhs - EPS || (std::abs(lhs - rhs) <= EPS && B[i] < B[r]))
            r = i;
        }
      }
      if (r == -1)
        return false;
      Pivot(r, s);
    }
  }

public:
  LPSolver(const std::vector<std::vector<double>> &A,
           const std::vector<double> &b, const std::vector<double> &c)
      : m((int)b.size()), n((int)c.size()), B(m), N(n + 1),
        D(m + 2, std::vector<double>(n + 2)) {
    for (int i = 0; i < m; ++i)
      for (int j = 0; j < n; ++j)
        D[i][j] = A[i][j];
    for (int i = 0; i < m; ++i) {
      B[i] = n + i;
      D[i][n] = -1;
      D[i][n + 1] = b[i];
    }
    for (int j = 0; j < n; ++j) {
      N[j] = j;
      D[m][j] = -c[j];
    }
    N[n] = -1;
    D[m + 1][n] = 1;
  }

  // returns -INF infeasible, +INF unbounded, otherwise optimum.
  double Solve(std::vector<double> &x) {
    int r = 0;
    for (int i = 1; i < m; ++i)
      if (D[i][n + 1] < D[r][n + 1])
        r = i;
    if (D[r][n + 1] < -EPS) {
      Pivot(r, n);
      if (!Simplex(1) || D[m + 1][n + 1] < -EPS)
        return -INF;
      if (D[m + 1][n + 1] < EPS) {
        auto it = std::find(B.begin(), B.end(), -1);
        if (it != B.end()) {
          r = int(it - B.begin());
          int s = 0;
          for (int j = 1; j <= n; ++j)
            if (std::abs(D[r][j]) > std::abs(D[r][s]) + EPS ||
                (std::abs(std::abs(D[r][j]) - std::abs(D[r][s])) <= EPS &&
                 N[j] < N[s]))
              s = j;
          Pivot(r, s);
        }
      }
    }
    if (!Simplex(2))
      return INF;
    x.assign(n, 0.0);
    for (int i = 0; i < m; ++i)
      if (B[i] < n)
        x[B[i]] = D[i][n + 1];
    return D[m][n + 1];
  }
};

} // namespace batsp
