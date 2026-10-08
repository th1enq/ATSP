#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p results
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j2
ctest --test-dir build --output-on-failure
./build/batsp witness6 | tee results/witness6.log
./build/batsp exhaustive-n4 results/exhaustive_n4.csv | tee results/exhaustive_n4.log
./build/batsp exhaustive-n5 results/exhaustive_n5_detailed.csv | tee results/exhaustive_n5.log
./build/batsp split-family 12 results/split_family_pipeline.csv | tee results/split_family.log
./build/batsp random-search 12 2000 0.18 0.55 20261007 results/random_n5_12_2000_repro.csv | tee results/random.log
./build/batsp metric-random 8 50 20261007 results/metric_random_pipeline.csv | tee results/metric.log
