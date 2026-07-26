# -*- coding: utf-8 -*-
"""s8b binding 検証の盲点を機械固定する drift-guard (Lane B′)。

裁定 2026-07-18 (C-β 表 B-1/B-2/B-4/B-9) は、binding 検証統合本体を v2 (closed
source bundle pin 裁定後) へ延期し、Lane B を「テストのみ・production 0 byte 不変」
の Lane B′ に縮小した。本ファイルはその 3 群を実装する:

1. NaN 乖離の characterization —— manifest の permissive canonicalizer が受理する
   非有限 genome を、report の strict canonicalizer が ValueError で拒否する既知
   ドリフトを両方向で固定する。
2. report の cell identity 検査の positive control —— 検索 cell と中身が食い違う
   binding entry を report の各探索形で与え、mismatch が issue として捕捉される
   (= 将来の統合で cell 照合を落とす変異を殺す) ことを固定する。
3. run_block 統合負テスト —— schema を壊した manifest を実 run_block / gate_check
   経路に与えたときの現行の fail-closed 挙動 (構造化 refusal・fake の不発火・
   出力ゼロ) を実測固定する。

すべて characterization: 現行挙動を実測して固定する (期待の決め打ちはしない)。
production コードは 1 byte も変更しない。テストは公開挙動 (関数の受理・拒否・
例外型・構造化 refusal) だけに依存し、loader の定義位置には依存しない
(``load_verified_freeze`` は import しない)。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ORCHESTRATOR = Path(__file__).resolve().parents[1]
ROOT = ORCHESTRATOR.parent
sys.path.insert(0, str(ORCHESTRATOR))
sys.path.insert(0, str(ORCHESTRATOR / "tests"))

from campaign import s8b_oracle_driver as driver  # noqa: E402
from campaign import s8b_oracle_manifest as manifest_module  # noqa: E402
from campaign import s8b_oracle_report as report_module  # noqa: E402

# Lane A が並行編集中の driver test から fixture helper だけを import 再利用する
# (編集はしない)。helper は freeze/manifest を公開 API 経由で構築するため、loader
# の定義位置には依存しない。
import test_s8b_oracle_driver as driver_fixtures  # noqa: E402
import real_repo_receipt_memo as receipt_memo  # noqa: E402


_HEX64 = "a" * 64
_ALT_HEX64 = "b" * 64


def _binding_entry(*, holdout_id: str, configuration_id: str, genome,
                   binding_sha256: str) -> dict:
    """report._BINDING_KEYS / manifest._BINDING_KEYS を満たす完全な binding entry。"""
    return {
        "holdout_id": holdout_id,
        "configuration_id": configuration_id,
        "entry_sha256": _HEX64,
        "genome_canonical": genome,
        "src_token": "src-token",
        "variant_id": "variant-id",
        "binding_sha256": binding_sha256,
    }


# --------------------------------------------------------------------------- #
# 1. NaN 統一後挙動の characterization (両側拒否)
# --------------------------------------------------------------------------- #
#
# かつては manifest 側 canonicalizer (permissive) が NaN を "NaN" token として受理し、
# report 側 (strict, allow_nan=False) だけが拒否する既知 drift だった。B-1 裁定で
# manifest の _canonical_bytes も allow_nan=False へ strict 化したため、両側が非有限値を
# 拒否する。ここでは統一後の「両側拒否」を実測固定する。


def _nan_binding():
    """非有限値 (NaN) を含む genome を持つ binding entry。

    binding_sha256 は placeholder。manifest 側は再計算 (canonical_sha256) の時点で
    NaN 拒否に倒れるため、比較値としては使われない。
    """
    genome = {"weight": float("nan")}
    entry = _binding_entry(
        holdout_id="h0", configuration_id="c0", genome=genome,
        binding_sha256=_HEX64,
    )
    return entry, genome


def test_nan_binding_rejected_by_manifest_validator():
    """manifest 経路: 非有限 genome の binding entry を拒否する (strict canonicalizer)。

    B-1 適用後、manifest の _canonical_sha256 は allow_nan=False を渡すため、
    _validate_binding_identity の binding_sha256 再計算で ManifestError に倒れる。
    かつての受理 (permissive) からの反転を固定する。
    """
    entry, _genome = _nan_binding()
    schedule = manifest_module.build_schedule(
        n=1, master_seed="driftguard", block_sizes={"b0": 1},
        holdout_ids=["h0"], configuration_ids=["c0"],
    )
    with pytest.raises(manifest_module.ManifestError):
        manifest_module._validate_binding_identity([entry], schedule=schedule)


def test_nan_binding_rejected_by_report_schema_issues():
    """report 経路: 同一 entry を strict canonicalizer が ValueError で拒否する。

    report の _canonical_sha256 は allow_nan=False を渡すため、binding_sha256 の
    再計算で json.dumps が ValueError を送出する。manifest (ManifestError) と report
    (ValueError) が共に拒否する —— これが統一後の挙動である。
    """
    entry, _genome = _nan_binding()
    with pytest.raises(ValueError):
        report_module._binding_schema_issues(
            entry, holdout="h0", configuration="c0",
        )


# --------------------------------------------------------------------------- #
# 2. report の cell identity 検査の positive control (mutation-killing)
# --------------------------------------------------------------------------- #
#
# report の binding 探索が受理する各形で、検索対象 cell と中身が食い違う entry を
# 与える。map 系の形 (nested / composite "H:C" / "H/C") は key で entry を引くため、
# 中身が cell と食い違う entry が返り、_binding_schema_issues が cell identity
# mismatch を issue として捕捉する。list 形は holdout_id/configuration_id の内容
# 一致で引くため、cell と食い違う entry は _binding_entry が返さず (None)、
# _binding_schema_issues が「expected cell がない」issue を返す。いずれの形でも
# 「食い違う entry が黙って受理される」ことはない —— cell 照合を落とす変異を殺す。


def _wrong_cell_entry() -> dict:
    """searched cell (h0/c0) と holdout_id/configuration_id が食い違う完全 entry。"""
    return _binding_entry(
        holdout_id="mismatch-h", configuration_id="mismatch-c",
        genome="genome-json", binding_sha256=_ALT_HEX64,
    )


def test_report_list_form_wrong_cell_is_not_returned():
    """list 形: 内容一致で引くため、cell 違いの entry は返らず (None) issue になる。

    _binding_entry が list 内 entry を holdout_id/configuration_id の一致で選ぶため、
    (h0,c0) を検索しても mismatch entry は選ばれない。返り値 None を
    _binding_schema_issues が「expected cell がない」で捕捉する。_binding_entry の
    list cell 照合を落とす変異 (先頭 entry を無条件に返す等) はこの検査で赤化する。
    """
    for key in ("binding_identity", "bindings", "binding_identities"):
        manifest = {key: [_wrong_cell_entry()]}
        entry = report_module._binding_entry(manifest, "h0", "c0")
        assert entry is None
        issues = report_module._binding_schema_issues(
            entry, holdout="h0", configuration="c0",
        )
        assert issues == ["manifest.binding_identity に expected cell がない"]


def test_report_nested_mapping_form_wrong_cell_is_flagged():
    """nested mapping 形: key で引いた entry の内 cell 不一致を issue が捕捉する。

    raw[holdout][configuration] = entry を key で引くため、内容が (h0,c0) と食い違う
    entry が返る。_binding_schema_issues:254 の cell identity 照合がこれを捕捉する。
    この照合を落とす変異はここで赤化する。
    """
    manifest = {"binding_identity": {"h0": {"c0": _wrong_cell_entry()}}}
    entry = report_module._binding_entry(manifest, "h0", "c0")
    assert isinstance(entry, dict)
    assert (entry["holdout_id"], entry["configuration_id"]) == ("mismatch-h", "mismatch-c")
    issues = report_module._binding_schema_issues(
        entry, holdout="h0", configuration="c0",
    )
    assert "manifest.binding_identity の cell identity が不一致" in issues


@pytest.mark.parametrize("separator", [":", "/"])
def test_report_composite_key_form_wrong_cell_is_flagged(separator):
    """複合キー "H:C" / "H/C" 形: key で引いた entry の内 cell 不一致を捕捉する。"""
    composite = f"h0{separator}c0"
    manifest = {"binding_identity": {composite: _wrong_cell_entry()}}
    entry = report_module._binding_entry(manifest, "h0", "c0")
    assert isinstance(entry, dict)
    assert (entry["holdout_id"], entry["configuration_id"]) == ("mismatch-h", "mismatch-c")
    issues = report_module._binding_schema_issues(
        entry, holdout="h0", configuration="c0",
    )
    assert "manifest.binding_identity の cell identity が不一致" in issues


def test_report_matching_cell_entry_has_no_issue_non_vacuity():
    """非空証明 (negative control): cell 一致 + 整合 sha の entry は issue ゼロ。

    positive control が恒真でないことを示す。cell が一致し binding_sha256 が report
    の strict canonicalizer 再計算値と一致する完全 entry は、_binding_schema_issues
    が空 list を返す (受理)。
    """
    genome = "genome-json"
    projected = {
        "genome_canonical": genome,
        "src_token": "src-token",
        "variant_id": "variant-id",
        "entry_sha256": _HEX64,
    }
    binding_sha256 = report_module._canonical_sha256(projected)
    good = _binding_entry(
        holdout_id="h0", configuration_id="c0", genome=genome,
        binding_sha256=binding_sha256,
    )
    manifest = {"binding_identity": {"h0": {"c0": good}}}
    entry = report_module._binding_entry(manifest, "h0", "c0")
    assert entry is good
    assert report_module._binding_schema_issues(
        entry, holdout="h0", configuration="c0",
    ) == []


# --------------------------------------------------------------------------- #
# 3. run_block 統合負テスト (fail-closed の実経路固定)
# --------------------------------------------------------------------------- #
#
# binding entry の schema を壊した (必須キー欠落) manifest を実 run_block / gate_check
# 経路へ与える。現行の実測挙動: verify_manifest 内 _validate_binding_identity が
# ManifestError を送出し、gate_check がそれを捕捉して "manifest-verify: ..." refusal
# を refusals に積み allowed=False を返す。run_block は gate 拒否時に一切書き込まず
# status="refused" を返す (例外は伝播せず構造化 refusal になる —— 実測に従う)。
# fake prepare/evaluate は一度も呼ばれず、campaign 出力・budget 台帳・実走マーカーへの
# 書き込みも発生しない。


def _broken_binding_manifest(tmp_path: Path):
    """valid manifest を組んでから 1 binding entry の必須キーを落として壊す。"""
    freeze_path = driver_fixtures._synthetic_freeze(tmp_path)
    manifest_prepare = driver_fixtures._prepare_factory()
    manifest_path, _document = driver_fixtures._write_manifest(
        tmp_path, freeze_path, manifest_prepare,
    )
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    # 1 entry の必須 identity field (src_token) を落として schema を壊す。
    # set(entry) != _BINDING_KEYS -> "binding_identity entry schema が不一致"。
    del document["binding_identity"][0]["src_token"]
    broken_path = tmp_path / "broken_binding_manifest.json"
    broken_path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    return freeze_path, broken_path


def test_run_block_broken_binding_manifest_refuses_and_writes_nothing(tmp_path):
    """run_block: schema を壊した binding manifest は refused で fail-closed。

    実測固定: 例外は伝播せず status="refused" / allowed=False の構造化 refusal に
    倒れ、refusals に "manifest-verify: ManifestError: ..." が binding schema 不一致で
    積まれる。fake prepare/evaluate は一度も呼ばれず、output_root・budget・marker_root
    のいずれも生成されない (書き込みゼロ)。
    """
    freeze_path, broken_path = _broken_binding_manifest(tmp_path)
    prepare_fn = driver_fixtures._prepare_factory()
    prepare_fn.calls.clear()
    evaluate_fn = driver_fixtures._fake_evaluate_factory()
    output_root = tmp_path / "b-out"
    budget_path = tmp_path / "b-budget.json"
    marker_root = tmp_path / "b-markers"

    # [T-057] 対象は binding schema 不一致の fail-closed 挙動。実 repo receipt の解決は
    # incidental (1 回 22.4 秒) なので process 内 memo と共有する。
    with receipt_memo.patch_driver_resolver():
        result = driver.run_block(
            manifest_path=broken_path, block_id="b0", freeze_path=freeze_path,
            root=ROOT, output_root=output_root, budget_path=budget_path,
            marker_root=marker_root, prepare_fn=prepare_fn, evaluate_fn=evaluate_fn,
        )

    assert result["status"] == "refused"
    assert result["allowed"] is False
    manifest_verify = [r for r in result["refusals"]
                       if r.startswith("manifest-verify:")]
    assert manifest_verify, result["refusals"]
    assert any("ManifestError" in r and "binding_identity entry schema が不一致" in r
               for r in manifest_verify)
    # fake が一度も呼ばれない (実走前 gate で倒れる)。
    assert prepare_fn.calls == []
    assert evaluate_fn.calls == []
    # campaign 出力・budget 台帳・実走マーカーへの書き込みが発生しない。
    assert not output_root.exists()
    assert not budget_path.exists()
    assert not marker_root.exists()


def test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal(tmp_path):
    """gate_check 経路: 壊れた binding manifest で manifest-verify refusal を積む。

    run_block が委譲する gate 単体でも、_validate_binding_identity の ManifestError を
    構造化 refusal ("manifest-verify: ...") として refusals に積み allowed=False を
    返すことを固定する (run_block の refused 判定の根)。
    """
    freeze_path, broken_path = _broken_binding_manifest(tmp_path)

    # [T-057] 同上。gate 単体経路でも receipt 解決は incidental。
    with receipt_memo.patch_driver_resolver():
        decision = driver.gate_check(
            freeze_path=freeze_path, manifest_path=broken_path, root=ROOT,
        )

    assert decision.allowed is False
    assert any(r.startswith("manifest-verify:")
               and "binding_identity entry schema が不一致" in r
               for r in decision.refusals), decision.refusals


#
# 4. [T-057] real-repo receipt memo の positive control —— 上記 2 群が使う
#    `real_repo_receipt_memo` が「本番 verify_receipt へ委譲する」「テストが import する
#    module object を patch する」「実 repo 以外を拒否する」ことを、実 repo を歩かずに
#    (実 verifier を stub して) 固定する。memo が canned 値・別 module object・guard 無しへ
#    退行すると、これらが赤になる。


def _clear_receipt_memo():
    receipt_memo.real_repo_receipt.cache_clear()


def test_receipt_memo_delegates_to_production_verifier_exactly_once():
    """memo は本番 verify_receipt を root=実 repo でちょうど 1 回呼び、戻り object を
    再構築せずそのまま返す (canned 値・deepcopy への退行を殺す)。

    memo が包むのは本番 `_resolve_t080_receipt` なので、その内側の
    `t080_freeze_migration.verify_receipt` を stub して委譲を観測する
    (= 例外 → 構造化 refusal の翻訳経路も本番のまま通る)。
    """
    resolution = driver_fixtures.migration.ReceiptResolution(
        state="never-issued", refusals=(), t080_freeze_migration_observation=None,
        validation_head="c" * 40,
    )
    seen: list[Path] = []

    def fake_verify(*, root):
        seen.append(Path(root))
        return resolution

    _clear_receipt_memo()
    try:
        with pytest.MonkeyPatch.context() as patcher:
            # session cache (xdist 用) を切って process 内経路だけを検査する。
            patcher.setattr(receipt_memo, "_session_cache_path", lambda: None)
            patcher.setattr(receipt_memo.migration, "verify_receipt", fake_verify)
            first = receipt_memo.real_repo_receipt()
            second = receipt_memo.real_repo_receipt()
    finally:
        _clear_receipt_memo()

    assert seen == [receipt_memo.ROOT], seen
    assert first is resolution and second is resolution


def test_receipt_memo_patches_the_driver_module_the_tests_import():
    """patch 先は `campaign.s8b_oracle_driver` (テストが使う側)。

    同一ファイルでも `orchestrator.campaign.s8b_oracle_driver` は別 module object であり、
    そちらを patch すると memo は 1 度も発火せず静かに空振りする。その退行では
    実 verifier の呼び出しが 2 回に戻るのでここが赤になる。
    spy の呼び出し回数 (2) も同時に固定し、回数を観測しているテストの計数が memo で
    壊れないことを示す。
    """
    resolution = driver_fixtures.migration.ReceiptResolution(
        state="never-issued", refusals=(), t080_freeze_migration_observation=None,
        validation_head="d" * 40,
    )
    calls = {"real": 0}

    def fake_verify(*, root):
        calls["real"] += 1
        return resolution

    _clear_receipt_memo()
    try:
        with pytest.MonkeyPatch.context() as patcher:
            # session cache (xdist 用) を切って process 内経路だけを検査する。
            patcher.setattr(receipt_memo, "_session_cache_path", lambda: None)
            patcher.setattr(receipt_memo.migration, "verify_receipt", fake_verify)
            with receipt_memo.patch_driver_resolver() as spy:
                got_a = driver._resolve_t080_receipt(root=ROOT)
                got_b = driver._resolve_t080_receipt(root=ROOT)
    finally:
        _clear_receipt_memo()

    assert got_a is resolution and got_b is resolution
    assert spy.call_count == 2, spy.call_args_list
    assert calls["real"] == 1, calls


def test_receipt_memo_refuses_roots_other_than_the_real_repository(tmp_path):
    """tmp / tamper 経路へ patch が漏れたら、cached な valid 値で偽緑にせず赤で止める。"""
    with pytest.raises(AssertionError):
        receipt_memo.memo_resolver(root=tmp_path)


def test_receipt_memo_session_cache_round_trip_preserves_the_resolution(tmp_path):
    """xdist 用 session cache は値を保存し、壊れた cache では実解決へ倒す。

    worker 間共有は pickle 往復になるため、observation・refusals・raw bytes が
    落ちないことを固定する (frozen dataclass の等値比較)。cache が読めない場合に
    None を返す (= 呼び出し側が実解決へ倒す) ことも同時に固定する。
    """
    resolution = driver_fixtures.migration.ReceiptResolution(
        state="active-valid",
        refusals=("floor-null: x",),
        t080_freeze_migration_observation={"items": [{"a": 1}], "validation_head": "c" * 40},
        validation_head="c" * 40,
        introduction_commit="a" * 40,
        receipt={"confirmed_by": "human.test"},
        receipt_raw=b"receipt-bytes",
    )
    path = tmp_path / "cache.pickle"
    receipt_memo._cache_store(path, resolution)
    assert receipt_memo._cache_load(path) == resolution

    path.write_bytes(b"not a pickle")
    assert receipt_memo._cache_load(path) is None


if __name__ == "__main__":
    # pytest 依存 (fixtures / parametrize / raises) のため自走 harness は pytest.main
    # に委譲する。`python3 test_s8b_binding_driftguards.py` で実走し、0 件実行の偽緑を
    # 避ける (test_plain_runner_coverage の自走契約を満たす)。
    sys.exit(pytest.main([__file__, "-q"]))
