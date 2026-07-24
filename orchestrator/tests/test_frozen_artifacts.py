# -*- coding: utf-8 -*-
"""凍結成果物の exact path→sha256 manifest 機械検査 (C4-9)。

「凍結対象の sha256 不変を毎 commit 照合」の対象を曖昧語 (「相談逐語 3 本」等) でなく
exact path→sha256 の manifest として固定し、テストで全件一致を強制する。s1 freeze 2 本
+ v1 holdout freeze + floor protocol + 2026-07-16 の裁定資料 2 本と相談逐語 3 本を
列挙する (プラン §横断規律 line 140 の enumeration に整合)。

sha256 は実物から採取して埋めた値であり、凍結ファイルの改変・移動・削除を機械検出する。
自走 harness を持つため pytest 非依存で走る (二重 runner 規律)。
"""
from __future__ import annotations

import hashlib
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_ORCH)

sys.path.insert(0, _ORCH)
from skiputil import Skip  # noqa: E402  (二重 runner 契約: _run が捕捉する)

# 凍結成果物の exact path (repo-relative) → sha256。実物から採取済み。
# - s1-freeze 2 本 (known_axes は B-2 holdout freeze から直接参照される)
# - v1 holdout freeze (v2 連鎖の trust root、C2-5)
# - floor protocol (floor データ閲覧前の盲検 protocol trust root、s8b-floor-protocol/v2。
#   seal が承認定数からの canonical 再導出と HEAD blob を照合する対象)
# - 2026-07-16 裁定資料 2 本 (F6 = 択 a / F7 = 推奨案の正本、不変)
# - 2026-07-16 相談逐語 3 本 (裁定資料に対応する codex 敵対相談の逐語。プラン line 140 =
#   「相談逐語 3 本」。名称に -consultations を持つ凍結 insight = floor-protocol /
#   freeze / ruling-prep の 3 本。ruling-prep は C-C=freeze v2 設計骨子 / C-D=プラン全体
#   の裁定根拠であり、F20 恒久対応で凍結族に属す)
FROZEN_MANIFEST = {
    "output/s1-freeze/known_axes_freeze.json":
        "354f4b875a3c8106169252afc71cee1fd08df83b0f3024c72bda0a791e11f516",
    "output/s1-freeze/measurement_freeze.json":
        "203de36b9749b9021d1b944d26fad4c8ed617a0fdd1438435cb67e90a0efcf7a",
    "output/s8b-freeze/holdout_freeze.json":
        "315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688",
    "output/s8b-freeze/floor_protocol.json":
        "261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac",
    "output/insights/2026-07-16_s8b-floor-protocol-package.md":
        "150438a4ce2d0e5cab772c3eb9bfa05f44307a5dae5e47a1034778a3e3d9f6ba",
    "output/insights/2026-07-16_s8b-freeze-v2-design-material.md":
        "833dce66f4d61e5512298f6075061aa4f714ffba5fd44c4239173ed37ee91835",
    "output/insights/2026-07-16_s8b-floor-protocol-consultations.md":
        "d5bf4954e7ab3de657e47f7a7512b9ca13631818a2c1f046bd3dfdba09bcbcc1",
    "output/insights/2026-07-16_s8b-freeze-consultations.md":
        "5a8a2dcbcbb74decff502dffe01a389012d086ced2dd6db1f3b948153ccce149",
    "output/insights/2026-07-16_s8b-ruling-prep-consultations.md":
        "1a2db02903de83aefb18ce87ee926ec0c7bb5c2d90c4a5bf6dee017148a2a391",
}


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def test_frozen_artifacts_match_manifest():
    """凍結成果物が manifest の sha256 と全件一致する (改変・移動・削除の検出)。"""
    mismatches = []
    for rel, expected in sorted(FROZEN_MANIFEST.items()):
        abs_path = os.path.join(_ROOT, rel)
        if not os.path.isfile(abs_path):
            mismatches.append(f"{rel}: 不在")
            continue
        actual = _sha256(abs_path)
        if actual != expected:
            mismatches.append(f"{rel}: expected={expected} actual={actual}")
    assert not mismatches, "凍結成果物の sha256 不一致:\n" + "\n".join(mismatches)


def test_manifest_shape_is_exact():
    """manifest が exact path→64hex sha256 で、重複や不正 hex を持たない。"""
    assert len(FROZEN_MANIFEST) == 9, \
        "凍結対象は 9 件 (s1 2 + v1 1 + protocol 1 + 裁定資料 2 + 逐語 3)"
    for rel, sha in FROZEN_MANIFEST.items():
        assert rel.startswith("output/"), f"repo-relative path でない: {rel}"
        assert len(sha) == 64 and all(c in "0123456789abcdef" for c in sha), \
            f"64hex sha256 でない: {rel}={sha}"


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = skipped = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except Skip as e:
            print(f"SKIP {fn.__name__}: {e}")
            skipped += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
            failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
