# -*- coding: utf-8 -*-
"""凍結成果物の exact path→sha256 manifest 機械検査 (C4-9)。

「凍結対象の sha256 不変を毎 commit 照合」の対象を曖昧語 (「相談逐語 3 本」等) でなく
exact path→sha256 の manifest として固定し、テストで全件一致を強制する。s1 freeze 2 本
+ v1 holdout freeze + floor protocol + selector prediction 証拠一式 (prediction +
selector-runs) + 2026-07-16 の裁定資料 2 本と相談逐語 3 本を列挙する
(プラン §横断規律 line 140 の enumeration に整合)。

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

sys.path.insert(0, os.path.dirname(_ORCH))
from skiputil import Skip  # noqa: E402  (二重 runner 契約: _run が捕捉する)

# 凍結成果物の exact path (repo-relative) → sha256。実物から採取済み。
# - s1-freeze 2 本 (known_axes は B-2 holdout freeze から直接参照される)
# - v1 holdout freeze (v2 連鎖の trust root、C2-5)
# - floor protocol (floor データ閲覧前の盲検 protocol trust root、s8b-floor-protocol/v2。
#   seal が承認定数からの canonical 再導出と HEAD blob を照合する対象)
# - selector prediction 証拠 (盲検封印。prediction 1 + selector-runs 13 = journal +
#   4 セル × payload/envelope/raw。sha256 は seal 後採取で非決定的、bytes 凍結で改変検出)
# - 2026-07-16 裁定資料 2 本 (F6 = 択 a / F7 = 推奨案の正本、不変)
# - 2026-07-16 相談逐語 3 本 (裁定資料に対応する codex 敵対相談の逐語。プラン line 140 =
#   「相談逐語 3 本」。名称に -consultations を持つ凍結 insight = floor-protocol /
#   freeze / ruling-prep の 3 本。ruling-prep は C-C=freeze v2 設計骨子 / C-D=プラン全体
#   の裁定根拠であり、F20 恒久対応で凍結族に属す)
FROZEN_MANIFEST = {
    "output/s1-freeze/known_axes_freeze.json":
        "7d6790d2b04dbce2786e3186adfaa04fb4058ae40e30aebcf7bc282b8857dc13",
    "output/s1-freeze/measurement_freeze.json":
        "4d4fa53ff29ba554b36659b595c6cf1af00a4fa55ed2bfedabd09e0e323c325a",
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
    "output/s8b-freeze/selector_predictions.json":
        "5884c83f010f73914fe121e9eb7b2fe047a4739087a984d17287cfa338fd73f1",
    "output/s8b-freeze/selector-runs/envelope_rr20_on.json":
        "03518a1c75cc09a36c2bc93487eff4c883e0da88015d04473398623c8a113365",
    "output/s8b-freeze/selector-runs/envelope_rr20_swapped.json":
        "4ab24b43901cf52f5ea2e7f650a30eab2e05a3f883d6eb8808d761ca9990ce73",
    "output/s8b-freeze/selector-runs/envelope_rr80_on.json":
        "8379a6500e957965d488d3e231aa053e8f65d4639260ba4168b2c14a243858ab",
    "output/s8b-freeze/selector-runs/envelope_rr80_swapped.json":
        "6980ad84e7906146a29c0a553ee1847cc12ef7baebc2c3c77c6b3e23576e54f9",
    "output/s8b-freeze/selector-runs/journal.jsonl":
        "d41135998cff3047cf792047239a3147a1154929e560b4a2e413e4ac14f9e000",
    "output/s8b-freeze/selector-runs/payload_rr20_on.json":
        "bedc2c4961cc91361319a19642472583245342b8df10617fda3512aa0d5bbb55",
    "output/s8b-freeze/selector-runs/payload_rr20_swapped.json":
        "f894acc13008681d79ceb0e786f79d562742eee7305c8b4f3056526df61955c2",
    "output/s8b-freeze/selector-runs/payload_rr80_on.json":
        "f894acc13008681d79ceb0e786f79d562742eee7305c8b4f3056526df61955c2",
    "output/s8b-freeze/selector-runs/payload_rr80_swapped.json":
        "bedc2c4961cc91361319a19642472583245342b8df10617fda3512aa0d5bbb55",
    "output/s8b-freeze/selector-runs/raw_rr20_on.txt":
        "28fe26abf5b666952d0b23c05b7a5443455fbdba10e97af307b0b023025143c5",
    "output/s8b-freeze/selector-runs/raw_rr20_swapped.txt":
        "9b23d5703596a98070fb9cd7161a35ba162a1dbb0c2173f09af10c0d499700f8",
    "output/s8b-freeze/selector-runs/raw_rr80_on.txt":
        "20691240bef7f84215441955279b1cd1a2cda941d7c86062f1aecd2eaae98381",
    "output/s8b-freeze/selector-runs/raw_rr80_swapped.txt":
        "925b5e1155509da7bcca0df775622d2cf2f7c04559a7bf462912f8641af42ed3",
}

# seal 82803d6d 時点の現行 23 件だけを固定する暫定・独立 key-set pin。
# manifest-only 編集 (同数 path 差し替え) に対する運用 sentinel であり、独立改竄境界でも、
# 恒久 freeze-family membership (D76 恒久形は別ファイル golden を要求) でもない。
FROZEN_KEYSET_PROVISIONAL_82803D6D = frozenset({
    "output/s1-freeze/known_axes_freeze.json",
    "output/s1-freeze/measurement_freeze.json",
    "output/s8b-freeze/holdout_freeze.json",
    "output/s8b-freeze/floor_protocol.json",
    "output/insights/2026-07-16_s8b-floor-protocol-package.md",
    "output/insights/2026-07-16_s8b-freeze-v2-design-material.md",
    "output/insights/2026-07-16_s8b-floor-protocol-consultations.md",
    "output/insights/2026-07-16_s8b-freeze-consultations.md",
    "output/insights/2026-07-16_s8b-ruling-prep-consultations.md",
    "output/s8b-freeze/selector_predictions.json",
    "output/s8b-freeze/selector-runs/envelope_rr20_on.json",
    "output/s8b-freeze/selector-runs/envelope_rr20_swapped.json",
    "output/s8b-freeze/selector-runs/envelope_rr80_on.json",
    "output/s8b-freeze/selector-runs/envelope_rr80_swapped.json",
    "output/s8b-freeze/selector-runs/journal.jsonl",
    "output/s8b-freeze/selector-runs/payload_rr20_on.json",
    "output/s8b-freeze/selector-runs/payload_rr20_swapped.json",
    "output/s8b-freeze/selector-runs/payload_rr80_on.json",
    "output/s8b-freeze/selector-runs/payload_rr80_swapped.json",
    "output/s8b-freeze/selector-runs/raw_rr20_on.txt",
    "output/s8b-freeze/selector-runs/raw_rr20_swapped.txt",
    "output/s8b-freeze/selector-runs/raw_rr80_on.txt",
    "output/s8b-freeze/selector-runs/raw_rr80_swapped.txt",
})


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
    assert len(FROZEN_MANIFEST) == 23, \
        "凍結対象は 23 件 (s1 2 + v1 1 + protocol 1 + selector prediction 1 + " \
        "selector-runs 13 + 裁定資料 2 + 逐語 3)"
    for rel, sha in FROZEN_MANIFEST.items():
        assert rel.startswith("output/"), f"repo-relative path でない: {rel}"
        assert len(sha) == 64 and all(c in "0123456789abcdef" for c in sha), \
            f"64hex sha256 でない: {rel}={sha}"
    actual_keys = frozenset(FROZEN_MANIFEST)
    assert actual_keys == FROZEN_KEYSET_PROVISIONAL_82803D6D, (
        "FROZEN_MANIFEST の key-set 不一致 (同数 path 差し替え検出):"
        f"\nmissing_from_manifest={sorted(FROZEN_KEYSET_PROVISIONAL_82803D6D - actual_keys)}"
        f"\nunexpected_in_manifest={sorted(actual_keys - FROZEN_KEYSET_PROVISIONAL_82803D6D)}"
    )


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
