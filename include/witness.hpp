#pragma once
#include "graph.hpp"
#include <vector>

namespace batsp {
inline Digraph witness6_graph() {
  Digraph g(6);
  int A[][2] = {{0, 4}, {1, 0}, {1, 4}, {1, 5}, {2, 0}, {2, 3}, {3, 1},
                {3, 4}, {3, 5}, {4, 1}, {4, 2}, {5, 2}, {5, 3}, {5, 4}};
  for (auto &e : A)
    g.add_arc(e[0], e[1]);
  return g;
}
inline std::vector<std::vector<double>> witness6_z() {
  std::vector<std::vector<double>> z(6, std::vector<double>(6, 0));
  auto set = [&](int u, int v, double w) { z[u][v] = z[v][u] = w; };
  set(0, 1, .5);
  set(0, 2, .5);
  set(0, 4, 1.0);
  set(1, 3, .5);
  set(1, 4, .5);
  set(1, 5, .5);
  set(2, 3, .5);
  set(2, 4, .5);
  set(2, 5, .5);
  set(3, 5, 1.0);
  return z;
}
} // namespace batsp
