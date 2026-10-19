#!/usr/bin/env bash
set -euo pipefail
KLTN_RESEARCH_DIR="$(cd -- "$(dirname -- "$0")/.." && pwd)"
mkdir -p "$KLTN_RESEARCH_DIR/bin"
g++ -O3 -march=native -std=c++20 "$KLTN_RESEARCH_DIR/scripts/dense_v1.cpp" -o "$KLTN_RESEARCH_DIR/bin/dense_v1"
g++ -O3 -std=c++20 "$KLTN_RESEARCH_DIR/scripts/dense_v1.cpp" -o "$KLTN_RESEARCH_DIR/bin/dense_portable"
g++ -O3 -march=native -std=c++20 "$KLTN_RESEARCH_DIR/scripts/dense.cpp" -o "$KLTN_RESEARCH_DIR/bin/dense"
g++ -O3 -march=native -std=c++20 "$KLTN_RESEARCH_DIR/scripts/verify_enumeration.cpp" -o "$KLTN_RESEARCH_DIR/bin/verify_enumeration"
cd "$KLTN_RESEARCH_DIR/vendor/uzl"
cargo build --release --locked -j 4
