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
# 1. NaN 乖離の characterization (known-drift の可視化)
# --------------------------------------------------------------------------- #
#
# 既知の実装間乖離。manifest 側の canonicalizer (permissive, allow_nan=False 無し、
# s8b_oracle_manifest._canonical_bytes:46-56) は非有限値 (NaN 等) を "NaN" token
# として受理し、report 側の canonicalizer (strict, allow_nan=False、
# s8b_oracle_report._canonical_sha256:56-59) は同じ値を ValueError で拒否する。
# 統合と manifest 側 strict 化 (allow_nan=False) は v2 / ユーザー裁定材料
# (2026-07-18 裁定 B-1)。この乖離を「正しい」と主張しない —— 現行挙動を実測固定する
# だけである。


def _nan_binding():
    """非有限値を含む genome と、manifest permissive canonicalizer で整合する sha。"""
    genome = {"weight": float("nan")}
    projected = {
        "genome_canonical": genome,
        "src_token": "src-token",
        "variant_id": "variant-id",
        "entry_sha256": _HEX64,
    }
    # manifest の permissive canonicalizer で binding_sha256 を計算 (allow_nan=False
    # 無しなので NaN を受理する)。これが manifest 側の再計算値と一致する。
    binding_sha256 = manifest_module._canonical_sha256(projected)
    entry = _binding_entry(
        holdout_id="h0", configuration_id="c0", genome=genome,
        binding_sha256=binding_sha256,
    )
    return entry, genome


def test_nan_binding_accepted_by_manifest_validator():
    """manifest 経路: 非有限 genome の binding entry を受理する (permissive canonicalizer)。

    manifest の _canonical_sha256 は allow_nan=False を渡さないため NaN を "NaN"
    token として通す。事前計算した binding_sha256 が再計算値と一致し、
    _validate_binding_identity は entry を受理して validated list を返す。この検査が
    赤化したら manifest 側が strict 化された合図 (v2 の期待挙動)。
    """
    entry, _genome = _nan_binding()
    schedule = manifest_module.build_schedule(
        n=1, master_seed="driftguard", block_sizes={"b0": 1},
        holdout_ids=["h0"], configuration_ids=["c0"],
    )
    validated = manifest_module._validate_binding_identity(
        [entry], schedule=schedule,
    )
    assert len(validated) == 1
    assert (validated[0]["holdout_id"], validated[0]["configuration_id"]) == ("h0", "c0")
    assert validated[0]["binding_sha256"] == entry["binding_sha256"]


def test_nan_binding_rejected_by_report_schema_issues():
    """report 経路: 同一 entry を strict canonicalizer が ValueError で拒否する。

    report の _canonical_sha256 は allow_nan=False を渡すため、binding_sha256 の
    再計算 (_binding_schema_issues:275) で json.dumps が ValueError を送出する。
    これは issue list ではなく例外として観測される (実測固定)。manifest が受理し
    report が拒否する —— この非同値が現行の known-drift である。
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

    decision = driver.gate_check(
        freeze_path=freeze_path, manifest_path=broken_path, root=ROOT,
    )

    assert decision.allowed is False
    assert any(r.startswith("manifest-verify:")
               and "binding_identity entry schema が不一致" in r
               for r in decision.refusals), decision.refusals


if __name__ == "__main__":
    # pytest 依存 (fixtures / parametrize / raises) のため自走 harness は pytest.main
    # に委譲する。`python3 test_s8b_binding_driftguards.py` で実走し、0 件実行の偽緑を
    # 避ける (test_plain_runner_coverage の自走契約を満たす)。
    sys.exit(pytest.main([__file__, "-q"]))
