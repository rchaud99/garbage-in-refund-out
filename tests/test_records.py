"""The committed 2026-09-28 run records reproduce the committed results, through two independent code paths."""

import json
import subprocess
import sys
from pathlib import Path

from refundout import ladder_analysis

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "records" / "ladder-2026-09-28"


def test_frozen_analysis_reproduces_committed_results():
    dirs = sorted(str(d) for d in RECORDS.glob("*_ladder-*"))
    res = ladder_analysis.analyse(ladder_analysis.load(dirs))
    committed = json.loads((ROOT / "reports" / "ladder-results.json").read_text())
    assert json.loads(json.dumps(res, default=str)) == committed
    assert ladder_analysis.markdown(res) == (ROOT / "reports" / "ladder-results.md").read_text()


def test_independent_recompute_matches_quoted_numbers():
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "verify_headline.py"), str(RECORDS)],
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr
