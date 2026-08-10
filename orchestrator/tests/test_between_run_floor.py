# -*- coding: utf-8 -*-
"""between_run_floor の単一テナント admission が F3 強化 (path 非依存 pgrep) の
波及を受けることを確認する (レーン B 付録3、machine 非依存・モックのみ)。

between_run_floor.py は `_assert_single_tenant` を campaign.p2_2 から素通しで使う
(自身に admission ロジックを持たない)。p2_2._assert_single_tenant は内部で
calibrator.runner.competing_bench_pids を呼ぶ一本道なので、runner 側の検知強化は
between_run_floor 側のコード変更なしに効く — それをここで固定する。
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.calibrator import runner                          # noqa: E402
from orchestrator.campaign import between_run_floor                 # noqa: E402
from orchestrator.campaign.p2_2 import _assert_single_tenant         # noqa: E402


def test_between_run_floor_uses_p2_2_assert_single_tenant():
    """between_run_floor モジュールが campaign.p2_2._assert_single_tenant を
    そのまま import して使っていること (between_run_floor 独自の admission 経路が
    無いこと) を固定する — F3 強化は runner.competing_bench_pids 一箇所を直せば
    between_run_floor にも波及する、という設計前提の裏付け。"""
    assert between_run_floor._assert_single_tenant is _assert_single_tenant


def test_between_run_floor_admission_detects_s8b_build_cache_orphan_via_runner_fix():
    """**配線 (routing) の固定**: competing_bench_pids が非空を返したとき、
    between_run_floor が呼ぶ p2_2._assert_single_tenant がその結果を素通しで受け取り
    拒否まで波及することを確認する。

    ここでは competing_bench_pids そのものを fake で置換しているため、F3 の
    path 非依存パターンによる**実検知**は検証しない (fixture の orphan_line は
    「s8b-build-cache 配下の孤児が返った」状況を模した入力にすぎない)。実 pgrep
    越しの検知は test_calibrator.py::
    test_competing_bench_pids_real_orphan_under_s8b_build_cache_detected が担い、
    本テストは between-run floor の admission 経路がその検知結果に依存して
    fails-closed する配線だけを固定する (検知強化を 1 箇所直せば floor driver にも
    波及する、という設計前提の裏付け)。"""
    orphan_line = "31415 /out/env/pegasus/s8b-build-cache/gen3/ycsb_orphan.exe"

    def fake_competing_bench_pids():
        return [orphan_line]

    orig = runner.competing_bench_pids
    runner.competing_bench_pids = fake_competing_bench_pids
    try:
        raised = False
        try:
            between_run_floor._assert_single_tenant()
        except RuntimeError as e:
            raised = True
            assert orphan_line in str(e)
        assert raised, ("competing_bench_pids の非空結果が "
                        "between_run_floor の admission (拒否) まで波及しなかった")
    finally:
        runner.competing_bench_pids = orig


def test_between_run_floor_admission_passes_when_no_competitor():
    """競合なしなら between_run_floor 側の admission も通過する (回帰確認)。"""
    orig = runner.competing_bench_pids
    runner.competing_bench_pids = lambda: []
    try:
        between_run_floor._assert_single_tenant()   # 例外を出さないこと
    finally:
        runner.competing_bench_pids = orig


# ---- 素の runner (pytest 無しでも) ----

def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
            failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
