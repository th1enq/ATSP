#!/usr/bin/env bash
set -euo pipefail
KLTN_RESEARCH_DIR="$(cd -- "$(dirname -- "$0")/.." && pwd)"
HIGHS_PREFIX="${1:?Pass the HiGHS installation prefix (include/highs and lib).}"
for adapter in bib_hs bib_ds; do
  g++ "$KLTN_RESEARCH_DIR/scripts/$adapter.cpp" \
    -o "$KLTN_RESEARCH_DIR/bin/$adapter" \
    -std=c++17 -O3 -DNDEBUG -DLOG_LEVEL=2 -DNO_ASSERT \
    -I"$KLTN_RESEARCH_DIR/vendor/bib/src" -I"$HIGHS_PREFIX/include/highs" \
    -L"$HIGHS_PREFIX/lib" -Wl,-rpath,"$HIGHS_PREFIX/lib" -lhighs
done
