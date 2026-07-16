# -*- coding: utf-8 -*-
"""S-1 既知軸 freeze の統合テストと改竄 positive control。"""
from __future__ import annotations

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
sys.path.insert(0, _ORCH)

from campaign import s1_known_axes_freeze as M  # noqa: E402
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
    entries = doc["entries"]
    for workload, (variant, fitness) in M.EXPECTED_P2.items():
        selected = entries[workload]["p2_2_flag_opt"]
        assert selected["variant"] == variant
        assert selected["reference_fitness_tps"] == fitness
    for workload, backoff_us in M.EXPECTED_BACKOFF.items():
        assert entries[workload]["backoff_fixed_best"]["backoff_us"] == backoff_us
    for workload, name in M.EXPECTED_SORT.items():
        assert entries[workload]["sort_best"]["name"] == name
    assert entries["read-heavy"]["sort_best"]["name"] == "sk_ad"


def test_generate_refuses_existing_freeze(tmp_path):
    _require_submodule_sources()
    path = tmp_path / "known_axes_freeze.json"
    M.generate(path)
    with pytest.raises(M.FreezeError, match="既に存在"):
        M.generate(path)


def test_verify_rejects_one_byte_freeze_tamper(tmp_path):
    original = M.FREEZE_PATH.read_bytes()
    assert b'"sp_dd"' in original
    tampered = original.replace(b'"sp_dd"', b'"xp_dd"', 1)
    assert len(tampered) == len(original)
    path = tmp_path / "known_axes_freeze.json"
    path.write_bytes(tampered)
    with pytest.raises(M.FreezeError):
        M.verify(path)


def test_verify_rejects_tampered_source_copy(tmp_path):
    doc = json.loads(M.FREEZE_PATH.read_text(encoding="utf-8"))
    target_rel = doc["entries"]["balanced"]["p2_2_flag_opt"]["sources"][0]["path"]
    copied = tmp_path / "wal.jsonl"
    shutil.copyfile(M.ROOT / target_rel, copied)
    copied.write_bytes(copied.read_bytes() + b" ")

    def resolver(path_rel: str) -> Path:
        return copied if path_rel == target_rel else M.ROOT / path_rel

    with pytest.raises(M.FreezeError, match="source sha256 不一致"):
        M.verify_document(doc, source_resolver=resolver)


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
