# -*- coding: utf-8 -*-
"""T-078 positive-control fixture の test 側独立 pin。"""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

# production literal と別の値源として、S2-4.6 の承認値を逐語固定する。
POSITIVE_CONTROL_PATH = "orchestrator/tests/data/freeze_holdout_positive_control_v1.txt"
POSITIVE_CONTROL_ROOT_KEY = "positive-control/rr50/v1"
POSITIVE_CONTROL_SHA256 = (
    "caee6deabcf6209f5e8d59ee104a64b6bcf18a2a6054b1cefd6141709802faa7"
)
POSITIVE_CONTROL_FILE = REPO_ROOT / POSITIVE_CONTROL_PATH
