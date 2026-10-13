#!/usr/bin/env bash
# Offline runner for this workspace's existing Python wheel cache on NixOS.
set -euo pipefail
task_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
task_deps="/tmp/kltn-benchmark-deps"
python3 - "$task_deps" <<'PY'
import pathlib, sys, zipfile
target = pathlib.Path(sys.argv[1])
cache = pathlib.Path('/tmp/batsp-wheels')
if not (target/'scipy').is_dir() or not (target/'numpy').is_dir():
    target.mkdir(parents=True, exist_ok=True)
    for name in ['numpy-2.3.2-cp313-cp313-manylinux_2_27_x86_64.whl',
                 'scipy-1.16.1-cp313-cp313-manylinux_2_17_x86_64.whl']:
        with zipfile.ZipFile(cache/name) as archive:
            archive.extractall(target)
PY
task_cpp_lib="$(dirname -- "$(g++ -print-file-name=libstdc++.so.6)")"
task_zlib="/nix/store/61a1nwx3w6rqyaisj5rn1sal1981apm7-zlib-1.3.2/lib"
export LD_LIBRARY_PATH="${task_cpp_lib}:${task_zlib}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
export PYTHONPATH="${task_deps}${PYTHONPATH:+:${PYTHONPATH}}"
export OPENBLAS_NUM_THREADS=1
exec python3 "${task_root}/benchmarks/bench_tsplib.py" "$@"
