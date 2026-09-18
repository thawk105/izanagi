# -*- coding: utf-8 -*-
"""承認定数の単一源 (``campaign.s8b_approved``) の契約テスト (C4-3/C4-4)。

- ccbench full sha: ``pin.CURRENT_PIN`` が prefix であること、および実 repo の
  ``external/ccbench`` gitlink と完全一致することを固定する (定数の追認を許さない)。
- v1 trust root: s8b_ratified_freeze の ``V1_*`` を単一源として再輸出していること
  (import 束縛の identity) を drift-killer として固定する。
- 承認実験数値: s8b_experiment_numbers を単一源として再輸出していることを固定する。
- その他の承認 pin: floor_campaign の内部束縛と s8b_floor_stats の除外理由表が同一源から
  来ることを固定する (二重リテラルの再発防止)。
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ORCHESTRATOR = Path(__file__).resolve().parents[1]
ROOT = ORCHESTRATOR.parent
sys.path.insert(0, str(ORCHESTRATOR.parent))

from orchestrator.campaign import env_contract  # noqa: E402
from orchestrator.campaign import pin  # noqa: E402
from orchestrator.campaign import s8b_approved  # noqa: E402
from orchestrator.campaign import s8b_experiment_numbers  # noqa: E402
from orchestrator.campaign import s8b_floor_campaign  # noqa: E402
from orchestrator.campaign import s8b_floor_stats  # noqa: E402
from orchestrator.campaign import s8b_ratified_freeze  # noqa: E402
from orchestrator.tests.skiputil import Skip, skip  # noqa: E402


def _actual_gitlink() -> str:
    """実 repo の external/ccbench gitlink (40 hex) を実測する。git 不在なら SKIP。"""
    try:
        out = subprocess.run(
            ["git", "ls-tree", "HEAD", "external/ccbench"],
            cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        ).stdout.decode("utf-8", "strict")
    except (OSError, subprocess.CalledProcessError, UnicodeError) as exc:
        skip(f"git ls-tree 実行不能: {exc}")
    fields = out.split()
    assert len(fields) >= 3 and fields[0] == "160000" and fields[1] == "commit", \
        f"external/ccbench が gitlink でない: {out!r}"
    return fields[2]


def test_ccbench_full_sha_is_40hex_and_current_pin_is_prefix():
    full = s8b_approved.CCBENCH_FULL_SHA
    assert len(full) == 40 and all(c in "0123456789abcdef" for c in full), \
        f"CCBENCH_FULL_SHA が 40 hex でない: {full}"
    # pin.CURRENT_PIN (short 7) はこの full sha の prefix でなければならない。
    assert full.startswith(pin.CURRENT_PIN), \
        f"CURRENT_PIN {pin.CURRENT_PIN} が CCBENCH_FULL_SHA の prefix でない"


def test_ccbench_full_sha_matches_real_gitlink():
    actual = _actual_gitlink()
    assert actual == s8b_approved.CCBENCH_FULL_SHA, \
        f"gitlink 実測 {actual} != 承認定数 {s8b_approved.CCBENCH_FULL_SHA}"
    # gitlink 側からも prefix 一致を二重に固定する (submodule 前進の検出)。
    assert actual.startswith(pin.CURRENT_PIN), \
        f"gitlink {actual} が CURRENT_PIN {pin.CURRENT_PIN} を prefix に持たない"


def test_v1_trust_root_is_single_sourced_from_ratified():
    # drift-killer: 重複リテラルでなく s8b_ratified_freeze の V1_* を単一源とする。
    assert s8b_approved.APPROVED_FREEZE_PATH == s8b_ratified_freeze.V1_FREEZE_PATH
    assert s8b_approved.APPROVED_FREEZE_SHA256 == s8b_ratified_freeze.V1_FREEZE_SHA256


def test_v1_freeze_sha_matches_real_file_bytes():
    v1 = ROOT / s8b_approved.APPROVED_FREEZE_PATH
    if not v1.is_file():
        skip(f"v1 freeze 不在: {v1}")
    actual = hashlib.sha256(v1.read_bytes()).hexdigest()
    assert actual == s8b_approved.APPROVED_FREEZE_SHA256, \
        f"v1 freeze bytes {actual} != 承認定数 {s8b_approved.APPROVED_FREEZE_SHA256}"


def test_floor_campaign_pins_are_single_sourced():
    # validate_protocol の内部束縛 (_APPROVED_*) が s8b_approved と同値であること。
    assert s8b_floor_campaign._APPROVED_N_SESSIONS == s8b_approved.APPROVED_N_SESSIONS == 8
    assert s8b_floor_campaign._APPROVED_REPS == s8b_approved.APPROVED_REPS == 5
    assert s8b_floor_campaign._APPROVED_RETRY_SLOTS == s8b_approved.APPROVED_RETRY_SLOTS == 2
    assert s8b_floor_campaign._APPROVED_SESSION_CV_MAX == s8b_approved.APPROVED_SESSION_CV_MAX == "0.10"
    assert s8b_floor_campaign._APPROVED_CELL_CV_MAX == s8b_approved.APPROVED_CELL_CV_MAX == "0.15"
    assert s8b_floor_campaign._APPROVED_SCALE_ADEQUACY == s8b_approved.APPROVED_SCALE_ADEQUACY == "0.10"
    # 除外理由表は s8b_floor_stats が正本 (再輸出は tuple、順序を保つ)。
    assert s8b_approved.APPROVED_REASONS == tuple(s8b_floor_stats.ALLOWED_EXCLUDED_REASONS)
    assert list(s8b_floor_campaign._APPROVED_REASONS) == list(s8b_approved.APPROVED_REASONS)


def test_experiment_numbers_are_single_sourced_from_leaf():
    assert s8b_approved.APPROVED_EXTIME_S == s8b_experiment_numbers.APPROVED_EXTIME_S == 5
    assert s8b_approved.APPROVED_REPS == s8b_experiment_numbers.APPROVED_REPS == 5


def test_approved_protocol_free_values_match_rulings():
    # 独立 literal で裁定値を固定し、実装側の現在値を追認しない。
    assert s8b_approved.APPROVED_MASTER_SEED == "2026-07-18T17:16:12+09:00"
    assert s8b_approved.APPROVED_ENV_TAG == "pegasus"
    assert s8b_approved.APPROVED_STOCK_CONFIGURATION == "stock_common"
    assert s8b_approved.APPROVED_WIRED_MIN_REL_FLOOR == 0.03
    # canonical JSON bytes を変えないよう、F1 承認値は float 型まで固定する。
    assert type(s8b_approved.APPROVED_WIRED_MIN_REL_FLOOR) is float


def test_approved_stock_configuration_exists_in_every_v1_holdout():
    freeze_path = ROOT / "output/s8b-freeze/holdout_freeze.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    holdouts = freeze["holdouts"]
    assert holdouts, "v1 freeze の holdouts が空"
    for holdout_id, holdout in holdouts.items():
        entries = holdout["variant_binding"]["entries"]
        assert s8b_approved.APPROVED_STOCK_CONFIGURATION in entries, \
            f"{holdout_id} の variant_binding.entries に承認 stock 構成がない"


def test_approved_env_tag_is_registered_in_env_contract():
    contract = env_contract.lookup(s8b_approved.APPROVED_ENV_TAG)
    assert contract.env_tag == "pegasus"


def test_approved_master_seed_has_builder_required_form():
    seed = s8b_approved.APPROVED_MASTER_SEED
    assert isinstance(seed, str)
    assert seed


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
