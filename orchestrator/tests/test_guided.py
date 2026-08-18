# -*- coding: utf-8 -*-
"""P2-5 誘導アーム + ベースラインの単体テスト (machine 非依存・mock WAL)。

リーク制御 (online digest が評価済みしか含まない) と到達判定・ベースライン期待値の回帰固定。
pytest でも 素の `python orchestrator/tests/test_guided.py` でも走る。
"""
from __future__ import annotations

import atexit
import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import types

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import guided, ident, pipeline, replay, wal         # noqa: E402
import commit_receipt_support as receipt_support                              # noqa: E402
from orchestrator.campaign.build_admission import (                            # noqa: E402
    GeneratorId,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.genome import SILO_SPACE                            # noqa: E402
from orchestrator.campaign.layout import CampaignLayout                        # noqa: E402
from orchestrator.campaign.model import (STAGE_BENCH_DONE, STAGE_BUILD_START,  # noqa: E402
                            STAGE_BUILD_DONE, STAGE_COMMIT,
                            CampaignConfig, Genome)
from orchestrator.campaign.pin import CURRENT_PIN                              # noqa: E402
from orchestrator.campaign.source_digest import (                              # noqa: E402
    EMPTY_TRACKED_DIFF_SHA256,
    SourceEvidence,
)
from orchestrator.campaign.search_baselines import (exact_perm_pvalue_A,       # noqa: E402
                                       expectation, oracle_ceiling,
                                       prob_superiority,
                                       prob_superiority_two_sample,
                                       random_reach_distribution, reached_cost)
from orchestrator.critic.online_digest import LeakageError, online_digest      # noqa: E402

_G = "silo|BACK_OFF={b},NO_WAIT_LOCKING_IN_VALIDATION={l},NO_WAIT_OF_TICTOC={t},WAL={w}"


def _tmp_layout():
    d = tempfile.mkdtemp(prefix="izanagi_guided_")
    atexit.register(shutil.rmtree, d, ignore_errors=True)
    return CampaignLayout(root=d).ensure()


def _gr(canon, med):
    source_payload = {"fitness_tps": med}
    return replay.GenomeResult(genome=canon, flags=replay.parse_flags(canon),
                               fitness_tps=med, tps=[med] * 5,
                               leading_indicators={}, certified=True,
                               verification_evidence=receipt_support.replay_evidence(
                                   source_variant=canon,
                                   source_payload=source_payload,
                               ))


# ---- label ↔ genome 逆写像 (誘導の次手翻訳) ----

def test_genome_label_roundtrip():
    """全 8 genome で genome_label → genome_from_label が canonical に戻る。"""
    for g in SILO_SPACE.enumerate():
        lab = replay.genome_label(g.flags)
        back = replay.genome_from_label(lab)
        assert back.canonical() == g.canonical(), (lab, g.canonical(), back.canonical())


def test_genome_from_label_rejects_invalid():
    """不正/空間外ラベルは ValueError (空間外を黙って評価しない、規律6)。"""
    for bad in ["B0-X-W0", "B2-L-W0", "garbage", "B0-L", "B0-L-W2", "B0-L-W0-extra"]:
        try:
            replay.genome_from_label(bad)
            raise AssertionError(f"{bad!r} を弾けなかった")
        except ValueError:
            pass


# ---- リーク制御: online digest は評価済みしか含まない ----

def test_online_digest_leakage_assert():
    """digest の genome 数 > iterations なら LeakageError (配線 sanity: iterations 誤計算検知)。

    注: この assert は独立な第二防壁ではない — genome 数も iterations も同一誘導 WAL の
    STAGE_COMMIT 由来ゆえ同一 layout 経路では恒真化する (D26)。中立性の真の担保は WAL 分離
    + load_p2_2 非 import。ここで固定するのは「iterations を誤って渡した配線ミスを捕える」挙動。"""
    guided_v1_layout = _tmp_layout()
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    guided_v1_cfg = ident.bind_admission_policy(CampaignConfig(
        spec_slug="guided-online-digest-fixture",
        search_tag="critic-replay",
        spec_content="guided online digest post-policy fixture",
        ccbench_commit=CURRENT_PIN,
        search_config={"fixture": "post-admission-schema"},
        trial="online-digest",
    ), context.policy)
    wal.write_lock(
        guided_v1_layout, ident.canonical_preimage(guided_v1_cfg),
    )
    genomes = (
        _G.format(b=0, l=1, t=0, w=0),
        _G.format(b=1, l=1, t=0, w=0),
    )
    for ordinal, canonical in enumerate(genomes):
        genome = Genome("silo", replay.parse_flags(canonical))
        evidence = SourceEvidence(
            schema_version="source-evidence/v1",
            source_root=os.path.realpath(guided_v1_layout.root),
            ccbench_commit=CURRENT_PIN,
            genome_sha256=hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            src_token="stock",
            source_bytes_sha256=hashlib.sha256(
                f"guided-fixture:{canonical}".encode("utf-8")
            ).hexdigest(),
            tracked_clean=True,
            tracked_diff_sha256=EMPTY_TRACKED_DIFF_SHA256,
            tracked_paths=(),
        )
        receipt = derive_build_admission(context, evidence).as_wal_receipt()
        attempt_id = f"guided-fixture-attempt-{ordinal}"
        propagated = {
            "build_attempt_id": attempt_id,
            "build_admission_receipt_sha256": receipt["receipt_sha256"],
        }
        variant = pipeline.variant_id(genome)
        wal.log(guided_v1_layout, variant, STAGE_BUILD_START, "test", {
            "genome": canonical,
            "src_token": "stock",
            "build_admission": receipt,
            **propagated,
        })
        wal.log(
            guided_v1_layout, variant, STAGE_BUILD_DONE, "test",
            dict(propagated),
        )
        wal.log(guided_v1_layout, variant, STAGE_BENCH_DONE, "test", {
            "leading_indicators": {"throughput_tps": 1.0},
            **propagated,
        })
        receipt_support.log_receipted_commit(
            guided_v1_layout, variant, "test", {
            "fitness_tps": 1.0,
            **propagated,
            }, operation_identity=attempt_id,
        )
    # committed 2 genome。iterations=1 と誤計算したら sanity が発火する。
    try:
        online_digest(guided_v1_layout, "x", {}, iterations=1)
        raise AssertionError("LeakageError が出なかった (配線 sanity が壊れている)")
    except LeakageError:
        pass
    d = online_digest(guided_v1_layout, "x", {}, iterations=2)  # 整合 → OK
    assert len(d.genomes) == 2


# ---- 到達コスト (全戦略共通定義) ----

def test_reached_cost():
    assert reached_cost(["a", "b", "c"], {"c"}) == 3
    assert reached_cost(["x"], {"x"}) == 1
    assert reached_cost(["a", "b", "c"], {"a"}) == 1
    assert reached_cost(["a", "b"], {"z"}) == 2          # 未到達 → 予算上限 (= len)


# ---- ベースライン期待値 (1.4 でなく 1.80 を回帰固定、批判2-#5) ----

def test_random_distribution_sums_and_expectation():
    for n, k, exp in [(8, 1, 4.5), (8, 4, 1.8), (8, 2, 3.0)]:
        d = random_reach_distribution(n, k)
        assert abs(sum(d.values()) - 1.0) < 1e-9, (n, k, sum(d.values()))
        assert abs(expectation(d) - exp) < 1e-9, (n, k, expectation(d))


def test_oracle_ceiling():
    assert abs(oracle_ceiling(8, 4) - 1.5) < 1e-9
    assert abs(oracle_ceiling(8, 1) - 1.875) < 1e-9


# ---- 確率優越 a の校正 (D29: 同分布で厳密 0.500、p_lt は系統バイアス) ----

def test_prob_superiority_a_calibrated_at_null():
    """戦略が random と完全同分布なら a = 0.500 (厳密)。p_lt は 0.5 を下回る
    系統バイアスを持つ (k=1 で 0.4375、k=4 で <0.4) ことも回帰固定する —
    p_lt を 0.5 基準で読むと negative result を実態より強く見せる (D29)。"""
    for n, k in [(8, 1), (8, 4), (8, 2)]:
        d = random_reach_distribution(n, k)
        # 「戦略のコスト標本 = random 分布そのもの」を重み付きで再現
        # (各コスト j を確率質量ぶんだけ並べる代わりに、期待値として直接計算)
        ps = prob_superiority(list(d.keys()), d)
        a_null = sum(p * (sum(q for j, q in d.items() if j > c) +
                          0.5 * sum(q for j, q in d.items() if j == c))
                     for c, p in d.items())
        assert abs(a_null - 0.5) < 1e-9, (n, k, a_null)          # a は厳密に校正
        p_lt_null = sum(p * sum(q for j, q in d.items() if j > c)
                        for c, p in d.items())
        assert p_lt_null < 0.5 - 1e-9, (n, k, p_lt_null)          # p_lt は系統的に下方
        assert ps["a"] == (ps["p_lt"] + ps["p_le"]) / 2           # 定義の整合


def test_prob_superiority_two_sample_null_and_direction():
    """二標本 A: 同一標本同士は 0.5、一様に速い/遅い標本は 1.0/0.0。"""
    xs = [1, 2, 3, 4]
    assert abs(prob_superiority_two_sample(xs, xs) - 0.5) < 1e-9
    assert prob_superiority_two_sample([1, 1], [5, 6]) == 1.0
    assert prob_superiority_two_sample([7, 8], [1, 2]) == 0.0


def test_exact_perm_pvalue_hand_calculated():
    """厳密 permutation の校正: 分割を手で列挙できる小ケースと突合。

    xs=[1,2] vs ys=[1,3]: pooled {1:2,2:1,3:1} から 2 本選ぶ C(4,2)=6 分割は
    構成 (A値, 重み) = (1.0,1)/(0.625,2)/(0.375,2)/(0.0,1)。観測 A=0.625 なので
    less: P(A≤0.625)=5/6、greater: P(A≥0.625)=3/6。"""
    res = exact_perm_pvalue_A([1, 2], [1, 3], "less")
    assert abs(res["p"] - 5 / 6) < 1e-12
    assert abs(res["A"] - 0.625) < 1e-12
    assert res["A"] == prob_superiority_two_sample([1, 2], [1, 3])  # A の定義一致
    assert abs(exact_perm_pvalue_A([1, 2], [1, 3], "greater")["p"] - 0.5) < 1e-12
    # 2 標本 1 本ずつ: 選抜 2 通りのみ
    assert exact_perm_pvalue_A([1], [2], "less")["p"] == 1.0
    assert exact_perm_pvalue_A([2], [1], "less")["p"] == 0.5
    # 同一多重集合同士は対称: A=0.5 で less/greater とも中央値を含み ≥0.5
    sym = exact_perm_pvalue_A([1, 2, 3], [1, 2, 3], "less")
    assert abs(sym["A"] - 0.5) < 1e-12 and sym["p"] >= 0.5
    try:
        exact_perm_pvalue_A([1], [2], "two-sided")
        raise AssertionError("alternative='two-sided' が ValueError にならなかった")
    except ValueError:
        pass


def test_exact_perm_pvalue_frozen_write_heavy():
    """P2-5 write-heavy 誘導 vs 貪欲の p の凍結回帰 (correction_2026_07_03)。

    guided_costs は p2-5-summary.json 凍結値、greedy 500 本は
    run_workload('write-heavy', k_trials=500, seed0=0) の決定論 replay の度数分布
    (凍結 greedy_p_lt=0.45475 と byte 一致することは summary.json provenance で確認済み)。
    旧記録「permutation p<1e-4」は方式未記録の Monte Carlo による過大表示で、
    厳密値は 2.52×10⁻⁴ (Holm ×6 でも <0.05 なので「有意に有害」の結論は不変)。"""
    guided = [1, 3, 4, 4, 8, 8, 8, 8, 8, 8, 8, 8]
    greedy_hist = {1: 62, 2: 66, 3: 67, 4: 35, 5: 31, 6: 182, 7: 57}
    greedy = [v for v, c in greedy_hist.items() for _ in range(c)]
    assert len(greedy) == 500
    res = exact_perm_pvalue_A(guided, greedy, "less")
    assert abs(res["p"] - 2.521080185096e-04) < 1e-12
    assert abs(res["A"] - 0.230416666667) < 1e-9   # 凍結 guided_vs_greedy_A=0.2304
    assert res["n_configs"] == 50268
    assert 1e-4 < res["p"] < 3e-4                  # 「p<1e-4」が過大表示だったことの固定
    assert res["p"] * 6 < 0.05                     # Holm ×6 でも有意 = 結論不変


# ---- winner-tied set = no-difference 連結成分 (winner pivot 非依存) ----

def test_winner_tied_set_basic():
    win = _G.format(b=0, l=1, t=0, w=0)
    near = _G.format(b=0, l=1, t=0, w=1)      # 1% 差 < floor → tied
    far = _G.format(b=1, l=1, t=0, w=0)       # 50% 差 → not tied
    land = {win: _gr(win, 100.0), near: _gr(near, 99.0), far: _gr(far, 50.0)}
    tied = replay.winner_tied_set(land, between_run_cv=0.03)
    assert tied == {win, near}, tied


def test_winner_tied_set_transitive_chain():
    """a-b・b-c が floor 内なら a-c が floor 超でも連結成分で全て tied。"""
    a = _G.format(b=0, l=1, t=0, w=0)         # 100
    b = _G.format(b=0, l=1, t=0, w=1)         # 98  (a と 2%)
    c = _G.format(b=0, l=0, t=1, w=0)         # 96  (b と ~2%、a と ~4%)
    d = _G.format(b=1, l=1, t=0, w=0)         # 50  (far)
    land = {a: _gr(a, 100.0), b: _gr(b, 98.0), c: _gr(c, 96.0), d: _gr(d, 50.0)}
    tied = replay.winner_tied_set(land, between_run_cv=0.03)
    assert tied == {a, b, c}, tied            # 連結で 3 つ、far は除外


def test_cmd_evaluate_repairs_committed_tail_before_four_new_frames():
    root = _tmp_layout().root
    trial = "balanced-s-resume"
    layout = guided._trial_layout(trial, root)
    layout.ensure()
    meta = {"tag": "balanced", "workload": {"ycsb_rratio": "50"},
            "seed": "7", "trial": trial}
    guided._write_meta(layout, meta)
    ident.ensure_resumable_wal(
        guided._trial_config(meta, trial), layout,
        admission_policy=guided._NO_BUILD_POLICY,
        require_environment_contract=False,
    )
    first, second = SILO_SPACE.enumerate()[:2]
    guided._log_eval(layout, _gr(first.canonical(), 100.0))
    with open(layout.wal_file, "ab") as stream:
        stream.write(b'{"partial":')

    saved_load = guided.replay.load_landscape
    saved_eval = guided.replay.replay_evaluate
    saved_print = guided._print_state
    guided.replay.load_landscape = lambda tag: {}
    guided.replay.replay_evaluate = lambda landscape, genome: _gr(
        genome.canonical(), 90.0)
    guided._print_state = lambda *args: None
    try:
        rc = guided.cmd_evaluate(types.SimpleNamespace(
            trial=trial, root=root, genome=replay.genome_label(second.flags)))
    finally:
        guided.replay.load_landscape = saved_load
        guided.replay.replay_evaluate = saved_eval
        guided._print_state = saved_print
    records, truncated = wal.read_records_checked(layout)
    assert rc == 0 and truncated is False
    assert len(records) == 8
    assert [record.variant for record in records[:4]] == [first.canonical()] * 4
    assert [record.variant for record in records[4:]] == [second.canonical()] * 4
    assert len([name for name in os.listdir(layout.runs_dir)
                if name.startswith("wal-tail-repair-")]) == 1


def test_cmd_evaluate_checks_meta_trial_before_repair():
    root = _tmp_layout().root
    requested = "requested"
    layout = guided._trial_layout(requested, root)
    layout.ensure()
    guided._write_meta(layout, {
        "tag": "balanced", "workload": {}, "seed": "1", "trial": "other"})
    with open(layout.wal_file, "wb") as stream:
        stream.write(b"unframed")
    before = open(layout.wal_file, "rb").read()
    try:
        guided.cmd_evaluate(types.SimpleNamespace(
            trial=requested, root=root, genome="B0-L-W0"))
        raise AssertionError("meta trial mismatch を拒否すべき")
    except ValueError as exc:
        assert "trial が引数と不一致" in str(exc)
    assert open(layout.wal_file, "rb").read() == before
    assert not os.path.exists(layout.lock_file)


def test_cmd_start_acquires_lock_before_winner_writes_meta():
    root = _tmp_layout().root
    trial = "balanced-start-winner"
    args = types.SimpleNamespace(
        trial=trial, root=root, workload="balanced", seed="7",
    )
    layout = guided._trial_layout(trial, root)
    real_write_meta = guided._write_meta
    saved = (
        guided.replay.load_landscape,
        guided.replay.assert_complete,
        guided.replay.replay_evaluate,
        guided._print_state,
    )

    def checked_write_meta(candidate_layout, meta):
        assert wal.read_lock(candidate_layout) == ident.canonical_preimage(
            guided._trial_config(meta, trial),
        )
        real_write_meta(candidate_layout, meta)

    guided._write_meta = checked_write_meta
    guided.replay.load_landscape = lambda _tag: {}
    guided.replay.assert_complete = lambda _landscape, _tag: None
    guided.replay.replay_evaluate = lambda _landscape, genome: _gr(
        genome.canonical(), 100.0)
    guided._print_state = lambda *_args: None
    try:
        rc = guided.cmd_start(args)
    finally:
        guided._write_meta = real_write_meta
        (guided.replay.load_landscape,
         guided.replay.assert_complete,
         guided.replay.replay_evaluate,
         guided._print_state) = saved
    assert rc == 0
    assert os.path.exists(guided._meta_path(layout))
    assert len(wal.read_records(layout)) == 4


def test_cmd_start_atomic_loser_is_structured_and_touches_no_meta_or_wal():
    root = _tmp_layout().root
    trial = "balanced-start-loser"
    args = types.SimpleNamespace(
        trial=trial, root=root, workload="balanced", seed="7",
    )
    layout = guided._trial_layout(trial, root).ensure()
    meta = {"tag": "balanced", "workload": guided._workload_of("balanced"),
            "seed": "7", "trial": trial}
    assert ident.ensure_campaign_identity(
        guided._trial_config(meta, trial), layout,
        admission_policy=guided._NO_BUILD_POLICY,
        require_environment_contract=False,
    ) is True

    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        rc = guided.cmd_start(args)
    rejection = json.loads(stderr.getvalue())
    assert rc == 2
    assert rejection["reason"] == "campaign-lock-already-acquired"
    assert not os.path.exists(guided._meta_path(layout))
    assert not os.path.exists(layout.wal_file)


def test_cmd_evaluate_does_not_rewrite_pre_policy_lock():
    """既存 pre-T343 guided trial は current policy へ黙って移植しない。"""
    root = _tmp_layout().root
    trial = "historical-guided-lock"
    layout = guided._trial_layout(trial, root).ensure()
    meta = {"tag": "balanced", "workload": {"ycsb_rratio": "50"},
            "seed": "7", "trial": trial}
    guided._write_meta(layout, meta)
    historical = json.dumps({
        "ccbench_commit": "p2-2-replay-landscape",
        "search_config": {
            "seed": "7", "tag": "balanced",
            "workload": {"ycsb_rratio": "50"},
        },
        "search_tag": "critic-replay",
        "spec_content": "P2-5 critic-in-the-loop replay trial",
        "trial": trial,
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    wal.write_lock(layout, historical)

    try:
        guided.cmd_evaluate(types.SimpleNamespace(
            trial=trial, root=root, genome="B0-L-W0"))
        raise AssertionError("pre-policy lock の current-policy resume を拒否すべき")
    except ident.IdentityMismatch:
        pass
    assert wal.read_lock(layout) == historical


def test_cmd_start_existing_wal_is_rejected_before_lock_and_meta():
    root = _tmp_layout().root
    trial = "balanced-start-existing-wal"
    layout = guided._trial_layout(trial, root).ensure()
    with open(layout.wal_file, "wb") as stream:
        stream.write(b"existing")
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        rc = guided.cmd_start(types.SimpleNamespace(
            trial=trial, root=root, workload="balanced", seed="7"))
    assert rc == 2 and "既存" in stderr.getvalue()
    assert not os.path.exists(layout.lock_file)
    assert not os.path.exists(guided._meta_path(layout))


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in fns:
        try:
            fn(); print(f"PASS {fn.__name__}"); passed += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}"); failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}"); failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
