import json
import subprocess
import sys
import tempfile
from pathlib import Path


root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as folder:
    compressed = Path(folder) / "compressed.json"
    packing = Path(folder) / "packing.json"
    subprocess.run([sys.executable, str(root / "scripts/certify_compress.py"),
                    str(root / "instances/regression/witness6_hk.txt"),
                    "--output", str(compressed)], check=True)
    subprocess.run([sys.executable, str(root / "scripts/tree_packing.py"),
                    str(compressed), "--trees", "18", "--output", str(packing)], check=True)
    result = json.loads(packing.read_text(encoding="utf-8"))
    assert result["complete"] and len(result["trees"]) == 18
    subprocess.run([sys.executable, str(root / "scripts/tree_packing.py"),
                    str(compressed), "--verify", str(packing)], check=True)
