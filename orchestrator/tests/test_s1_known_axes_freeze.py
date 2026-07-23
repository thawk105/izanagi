# -*- coding: utf-8 -*-
"""S-1 既知軸 freeze の統合テストと改竄 positive control。"""
from __future__ import annotations

import ast
import copy
import inspect
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)
sys.path.insert(0, _ORCH)

from campaign import s1_known_axes_freeze as M  # noqa: E402
from s1_expected_goldens import (  # noqa: E402
    EXPECTED_BACKOFF,
    EXPECTED_P2,
    EXPECTED_SORT,
    EXPECTED_SWEEP_US,
    assert_known_axes_goldens,
)
from skiputil import Skip, skip  # noqa: E402

_SUBMODULE_DIR = M.ROOT / "external" / "ccbench"


def _submodule_initialized(sub: Path = _SUBMODULE_DIR) -> bool:
    """external/ccbench submodule が init 済みか (作業ツリー内に .git があるか)。
    未 init の submodule ディレクトリは空 (`.git` 不在)、init 後は gitlink ファイル `.git`
    を持つ。この 1 点だけが skip と実検査を分ける。"""
    return (sub / ".git").exists()


def _require_submodule_sources():
    """build_document()/generate() は external/ccbench の実ファイル (Options.cmake /
    silo CMakeLists) を読み、submodule に対し git rev-parse する。skip は submodule 未 init
    (external/ccbench に .git 無し) のときだけ — init 済みで必須ファイルが欠けている場合は
    skip せず実検査を走らせ、build_document が自然に FAIL する (新 pin がファイルを消した
    互換性回帰を skip に化けさせないため; README『依存物不在時の skip』の精密化)。"""
    if not _submodule_initialized():
        skip("submodule 未 init (external/ccbench に .git 無し) — build_document は実 ccbench ソースが要る")


def test_generate_selects_registered_expected_points():
    _require_submodule_sources()
    doc = M.build_document()
    assert_known_axes_goldens(doc)
    entries = doc["entries"]
    for workload, expected in EXPECTED_P2.items():
        selected = entries[workload]["p2_2_flag_opt"]
        assert selected["variant"] == expected["variant"]
        assert selected["reference_fitness_tps"] == expected["reference_fitness_tps"]
    for workload, expected in EXPECTED_BACKOFF.items():
        assert entries[workload]["backoff_fixed_best"]["backoff_us"] == expected["backoff_us"]
    for workload, expected in EXPECTED_SORT.items():
        assert entries[workload]["sort_best"]["name"] == expected["name"]
    assert entries["read-heavy"]["sort_best"]["name"] == EXPECTED_SORT["read-heavy"]["name"]


def test_backoff_sweep_grid_matches_registered_golden():
    from campaign import backoff_sweep

    assert tuple(backoff_sweep.SWEEP_US) == EXPECTED_SWEEP_US


def test_goldens_helper_is_independent_of_production():
    helper_path = Path(_HERE) / "s1_expected_goldens.py"
    tree = ast.parse(helper_path.read_text(encoding="utf-8"), filename=str(helper_path))
    imports = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    unexpected_imports = [
        ast.unparse(node)
        for node in imports
        if not isinstance(node, ast.ImportFrom) or node.module != "__future__"
    ]
    assert unexpected_imports == [], (
        "golden helper は __future__ 以外を import してはならない: "
        f"{unexpected_imports}"
    )

    campaign_dir = Path(_ORCH) / "campaign"
    consumers = sorted(
        path.name
        for path in campaign_dir.glob("*.py")
        if "s1_expected_goldens" in path.read_text(encoding="utf-8")
    )
    assert consumers == [], (
        "production は test-local golden helper を参照してはならない: "
        f"{consumers}"
    )


def test_build_document_is_self_consistent_and_detects_tamper():
    """独立 golden 全体の代替ではなく、実 build_document() の自己無矛盾性
    (二重生成の一致) と単一フィールド改竄の検出を確認する positive control。
    凍結成果物 (output/s1-freeze/known_axes_freeze.json) の現状ドリフトに非依存 —
    frozen_at_head/ccbench_pin は現在の実 HEAD を使うため、常に自身の ancestor になる。
    """
    _require_submodule_sources()
    doc = M.build_document()
    M.verify_document(doc)
    tampered = copy.deepcopy(doc)
    tampered["what"] = "TAMPERED"
    with pytest.raises(M.FreezeError, match="機械再構成と不一致"):
        M.verify_document(tampered)


def test_generate_refuses_existing_freeze(tmp_path):
    _require_submodule_sources()
    path = tmp_path / "known_axes_freeze.json"
    M.generate(path)
    with pytest.raises(M.FreezeError, match="既に存在"):
        M.generate(path)


def test_verify_rejects_one_byte_freeze_tamper(tmp_path):
    _require_submodule_sources()
    doc = M.build_document()
    serialized = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    path = tmp_path / "known_axes_freeze.json"
    path.write_text(serialized, encoding="utf-8")
    original = path.read_bytes()
    assert b'"sp_dd"' in original
    tampered = original.replace(b'"sp_dd"', b'"xp_dd"', 1)
    assert len(tampered) == len(original)
    path.write_bytes(tampered)
    with pytest.raises(M.FreezeError) as excinfo:
        M.verify(path)
    assert str(excinfo.value) == "freeze JSON の内容が現行 generator による機械再構成と不一致"


def test_verify_rejects_tampered_source_copy(tmp_path):
    _require_submodule_sources()
    doc = M.build_document()
    target_rel = doc["entries"]["balanced"]["system_gate"]["sources"][0]["path"]
    copied = tmp_path / Path(target_rel).name
    shutil.copyfile(M.ROOT / target_rel, copied)
    copied.write_bytes(copied.read_bytes() + b" ")

    def resolver(path_rel: str) -> Path:
        return copied if path_rel == target_rel else M.ROOT / path_rel

    with pytest.raises(M.FreezeError) as excinfo:
        M.verify_document(doc, source_resolver=resolver)
    assert str(excinfo.value).startswith(f"source sha256 不一致: {target_rel}")


def test_verify_rejects_generator_sha_tamper():
    _require_submodule_sources()
    doc = M.build_document()
    doc["generator"]["sha256"] = "0" * 64
    with pytest.raises(M.FreezeError) as excinfo:
        M.verify_document(doc)
    assert str(excinfo.value).startswith("generator sha256 不一致")
    assert "0" * 64 in str(excinfo.value)


def test_verify_rejects_non_ancestor_head():
    _require_submodule_sources()
    doc = M.build_document()
    doc["frozen_at_head"] = "f" * 40
    with pytest.raises(M.FreezeError) as excinfo:
        M.verify_document(doc)
    assert "現行 HEAD の commit ancestor でない" in str(excinfo.value)
    assert "f" * 40 in str(excinfo.value)


def test_verify_rejects_foreign_ccbench_pin():
    _require_submodule_sources()
    doc = M.build_document()
    doc["ccbench_pin"] = "0" * 40
    with pytest.raises(M.FreezeError) as excinfo:
        M.verify_document(doc)
    assert str(excinfo.value).startswith("ccbench_pin 不一致")
    assert "0" * 40 in str(excinfo.value)


def test_s1b_pairing_rejects_mismatched_flags():
    _require_submodule_sources()
    doc = M.build_document()
    forged = copy.deepcopy(doc)
    forged["entries"]["balanced"]["ident_all"]["flags"]["BACK_OFF"] = 0
    with pytest.raises(M.FreezeError, match="flags 不一致"):
        M.assert_s1b_pairing(forged)


def test_submodule_init_predicate_distinguishes_uninit_from_missing_file(tmp_path):
    """所見 A の positive control: skip 判定 (_submodule_initialized) は submodule の
    init 状態 (.git の有無) だけで決まり、必須ソースファイルの有無では変わらない。
    init 済みで Options.cmake / silo CMakeLists が欠落 (新 pin がファイルを削除した互換性
    回帰) しても『init 済み』と判定され、build_document が自然に FAIL できる (skip に化けない)。
    さらに (4) で guard 本体 _require_submodule_sources を直接叩き、init 済み判定なら必須ソース
    欠落でも skip しないことを確かめる — 旧 file-based fail-open へ退行すると実環境 (ソース欠落)
    で skip に化けるため、その skip を AssertionError に変換して発火させる。"""
    import sys as _sys
    _mod = _sys.modules[__name__]
    # skiputil.skip を pytest 配下でも custom Skip に統一する (統一しないと (3)(4) の guard 呼び
    # 出しが pytest.skip を投げ、この検査自体が skip に化けて positive control が発火しない)。
    _saved_env = os.environ.pop("PYTEST_CURRENT_TEST", None)
    _saved_pred = _mod._submodule_initialized
    try:
        # (1) 未 init (空 dir・.git 無し) → False (skip 側)
        uninit = tmp_path / "uninit"
        uninit.mkdir()
        assert _submodule_initialized(uninit) is False

        # (2) init 済み (.git あり) だが必須ソース欠落 → True (skip せず実検査へ)
        initd = tmp_path / "initd"
        initd.mkdir()
        (initd / ".git").write_text("gitdir: /elsewhere\n")   # gitlink ファイル相当
        assert not (initd / "cmake").exists()                 # 必須ソースは無い
        assert _submodule_initialized(initd) is True

        # (3) 本環境の実 submodule (未 init) では _require_submodule_sources が確かに skip する
        if not _submodule_initialized():
            raised = False
            try:
                _require_submodule_sources()
            except Skip:
                raised = True
            assert raised, "未 init 環境では _require_submodule_sources は skip すべき"

        # (4) guard 本体の positive control: 判定が「init 済み」を返す限り、必須ソースが実環境で
        #     欠落していても _require_submodule_sources は skip してはいけない (build_document を
        #     自然 FAIL させる契約)。file-based fail-open へ退行するとここで skip → AssertionError。
        _mod._submodule_initialized = lambda *a, **k: True
        try:
            _require_submodule_sources()
        except Skip:
            raise AssertionError(
                "init 済み判定なら必須ソース欠落でも skip してはいけない (fail-open 回帰)")
    finally:
        _mod._submodule_initialized = _saved_pred
        if _saved_env is not None:
            os.environ["PYTEST_CURRENT_TEST"] = _saved_env


# ---- 素の runner (二重 runner 契約: pytest 非依存で走る) ----
#
# tmp_path fixture を要するテストには tempfile ベースの一時 dir を供給する。これが無いと
# `python3 test_s1_known_axes_freeze.py` が 0 件実行・exit 0 の偽緑になる (所見 B / README:3)。

def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = skipped = 0
    for fn in fns:
        tmp = None
        try:
            kwargs = {}
            if "tmp_path" in inspect.signature(fn).parameters:
                tmp = tempfile.mkdtemp(prefix="izanagi_s1known_")
                kwargs["tmp_path"] = Path(tmp)
            fn(**kwargs)
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
        finally:
            if tmp:
                shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
