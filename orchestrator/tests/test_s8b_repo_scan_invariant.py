# -*- coding: utf-8 -*-
"""実 repository の holdout scan 結果を既知 hit 台帳へ束縛する。

``KNOWN_CONJUNCTION_HITS`` に entry を追加する場合は、なぜ clean scan の例外として
許容されるのかを説明する根拠コメントを、その entry と同じ変更に必須とする。
テスト自身が新たな三軸 conjunction を作らないよう、検索 pattern は production の
``search_repository`` だけから取得する。
"""
from __future__ import annotations

import sys
from pathlib import Path

ORCHESTRATOR = Path(__file__).resolve().parents[1]
REPOSITORY = ORCHESTRATOR.parent
sys.path.insert(0, str(ORCHESTRATOR))

from campaign import s8b_holdout_freeze as M  # noqa: E402


KNOWN_CONJUNCTION_HITS: dict[str, list[str]] = {
    "rr80": [],
    "rr20": [],
}


def test_real_repository_scan_matches_known_hits_and_has_positive_control():
    report = M.search_repository(REPOSITORY)
    actual_hits = {
        name: result["conjunction_hits"]
        for name, result in report["holdouts"].items()
    }

    assert actual_hits == KNOWN_CONJUNCTION_HITS
    assert report["positive_control"]["hit_count"] > 0


def _run() -> int:
    try:
        test_real_repository_scan_matches_known_hits_and_has_positive_control()
    except AssertionError as exc:
        print(f"FAIL test_real_repository_scan_matches_known_hits_and_has_positive_control: {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001
        print(
            "ERROR test_real_repository_scan_matches_known_hits_and_has_positive_control: "
            f"{type(exc).__name__}: {exc}"
        )
        return 1
    print("PASS test_real_repository_scan_matches_known_hits_and_has_positive_control")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
