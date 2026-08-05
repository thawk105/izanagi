# -*- coding: utf-8 -*-
"""S-1 既知軸 freeze の統合テストと改竄 positive control。"""
from __future__ import annotations

import ast
import copy
import inspect
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

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
_NONCANONICAL_PREDICATE = "izanagi_gate_pass = true;"


def _current_frozen_document() -> dict:
    return json.loads((M.ROOT / M.FREEZE_REL).read_text(encoding="utf-8"))


def _trigger_provenance(
        *, gate_name: str, gate_predicate: str, ident_predicate: str) -> dict:
    return {
        "entries": {
            gate_name: {"implementation": gate_predicate},
            "ident_all": {"implementation": ident_predicate},
        },
    }


def _call_trigger_entries_with_mocked_provenance(
        *, workload: str, gate_name: str, provenance: dict):
    with mock.patch.object(M, "_campaign_file", side_effect=(
                M.ROOT / "remeasure", M.ROOT / "main")), \
            mock.patch.object(M, "_load_json", side_effect=(
                copy.deepcopy(provenance), copy.deepcopy(provenance))), \
            mock.patch.object(
                M.s8a_trigger_sweep, "_genome",
                return_value=mock.Mock(flags=dict(M.trigger_axis._BASE))), \
            mock.patch.object(M, "_source", return_value={}), \
            mock.patch.object(M, "_module_source", return_value={}):
        return M._trigger_entries(workload, gate_name)


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


def test_current_six_frozen_trigger_predicates_pass_semantic_membership():
    doc = _current_frozen_document()
    predicates = [
        doc["entries"][workload][configuration]["gate_predicate"]
        for workload in M.WORKLOADS
        for configuration in ("system_gate", "ident_all")
    ]
    assert len(predicates) == 6
    M._validate_schema(doc)


def test_trigger_name_mask_binding_accepts_all_32_masks():
    for mask in range(32):
        reasons = tuple(
            reason
            for bit, reason in enumerate(M.trigger_axis.GATEABLE_REASONS)
            if mask & (1 << bit)
        )
        name = M.s8a_trigger_sweep.subset_name(reasons)
        predicate = M.s8a_trigger_sweep.predicate_for(reasons)
        M._require_trigger_name_mask_binding(
            name, f" \n{predicate}\t",
            workload="balanced", configuration="system_gate")

    all_reasons = M.trigger_axis.GATEABLE_REASONS
    M._require_trigger_name_mask_binding(
        M.s8a_trigger_sweep.IDENT_NAME,
        f"\r\n{M.s8a_trigger_sweep.predicate_for(all_reasons)}\u3000",
        workload="balanced", configuration="ident_all")


def test_validate_schema_accepts_both_mask31_names():
    current = _current_frozen_document()
    predicate = M.s8a_trigger_sweep.predicate_for(
        M.trigger_axis.GATEABLE_REASONS)
    regular_name = M.s8a_trigger_sweep.subset_name(
        M.trigger_axis.GATEABLE_REASONS)
    for name in (regular_name, M.s8a_trigger_sweep.IDENT_NAME):
        doc = copy.deepcopy(current)
        record = doc["entries"]["balanced"]["ident_all"]
        record["name"] = name
        record["gate_predicate"] = predicate
        M._validate_schema(doc)


def test_duplicate_trigger_names_and_alias_collisions_fail_closed():
    with mock.patch.object(
            M.s8a_trigger_sweep, "subset_name", return_value="duplicate"):
        with pytest.raises(M.FreezeError) as excinfo:
            M._build_trigger_name_mask_index()
    assert type(excinfo.value) is M.FreezeError
    assert "mask 間で重複" in str(excinfo.value)

    with mock.patch.object(
            M.s8a_trigger_sweep, "IDENT_NAME", "g_none"):
        with pytest.raises(M.FreezeError) as excinfo:
            M._build_trigger_name_mask_index()
    assert type(excinfo.value) is M.FreezeError
    assert "alias が既存名と衝突" in str(excinfo.value)


def test_consumer_import_defers_trigger_name_collision_until_first_check():
    script = inspect.cleandoc(
        """
        from campaign import s8a_trigger_sweep

        original_subset_name = s8a_trigger_sweep.subset_name
        canonical_name = original_subset_name(())
        predicate = s8a_trigger_sweep.predicate_for(())
        s8a_trigger_sweep.subset_name = lambda _reasons: "duplicate"

        from campaign import s1_measurement_freeze as consumer

        known_axes = consumer.known_axes
        assert known_axes._TRIGGER_NAME_MASK_BINDING_CACHE is None
        try:
            known_axes._require_trigger_name_mask_binding(
                canonical_name, predicate,
                workload="balanced", configuration="system_gate")
        except known_axes.FreezeError as exc:
            assert "mask 間で重複" in str(exc)
        else:
            raise AssertionError("最初の検査呼出しが衝突を拒否しなかった")
        assert known_axes._TRIGGER_NAME_MASK_BINDING_CACHE is None

        s8a_trigger_sweep.subset_name = original_subset_name
        cached = known_axes._trigger_name_mask_binding_index()
        assert known_axes._TRIGGER_NAME_MASK_BINDING_CACHE is not None

        s8a_trigger_sweep.subset_name = lambda _reasons: "duplicate"
        assert known_axes._trigger_name_mask_binding_index() is cached
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=M.ROOT / "orchestrator",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def _assert_trigger_name_rejected(name: object) -> None:
    predicate = M.s8a_trigger_sweep.predicate_for(())
    with pytest.raises(M.FreezeError) as excinfo:
        M._require_trigger_name_mask_binding(
            name, predicate,
            workload="balanced", configuration="system_gate")
    assert type(excinfo.value) is M.FreezeError
    assert "name と gate_predicate の mask が不一致" in str(excinfo.value)


def test_trigger_name_mask_binding_rejects_unknown_string_name():
    _assert_trigger_name_rejected("unknown")


def test_trigger_name_mask_binding_rejects_none_name():
    _assert_trigger_name_rejected(None)


def test_trigger_name_mask_binding_rejects_integer_name():
    _assert_trigger_name_rejected(1)


def test_trigger_name_mask_binding_rejects_bytes_name():
    _assert_trigger_name_rejected(b"g_none")


def test_trigger_name_mask_binding_rejects_str_subclass_name():
    class NameSubclass(str):
        pass

    _assert_trigger_name_rejected(NameSubclass("g_none"))


def test_trigger_name_mask_binding_rejects_comparison_spoof_name():
    class EqualToCanonicalName:
        def __hash__(self):
            return hash("g_none")

        def __eq__(self, _other):
            return True

    _assert_trigger_name_rejected(EqualToCanonicalName())


def test_trigger_name_mask_binding_non_string_diagnostics_ignore_repr():
    class ReprBomb:
        def __repr__(self):
            raise RuntimeError("repr must not be called")

    name = ReprBomb()
    predicate = M.s8a_trigger_sweep.predicate_for(())
    with pytest.raises(M.FreezeError) as excinfo:
        M._require_trigger_name_mask_binding(
            name, predicate,
            workload="balanced", configuration="system_gate")
    assert type(excinfo.value) is M.FreezeError
    assert "name_type=ReprBomb" in str(excinfo.value)

    with mock.patch.object(
            M.s8a_trigger_sweep, "subset_name", return_value=name):
        with pytest.raises(M.FreezeError) as excinfo:
            M._build_trigger_name_mask_index()
    assert type(excinfo.value) is M.FreezeError
    assert "type=ReprBomb" in str(excinfo.value)

    with mock.patch.object(M.s8a_trigger_sweep, "IDENT_NAME", name):
        with pytest.raises(M.FreezeError) as excinfo:
            M._build_trigger_name_mask_index()
    assert type(excinfo.value) is M.FreezeError
    assert "type=ReprBomb" in str(excinfo.value)


def test_validate_schema_rejects_missing_trigger_name():
    doc = _current_frozen_document()
    del doc["entries"]["balanced"]["system_gate"]["name"]
    with pytest.raises(M.FreezeError) as excinfo:
        M._validate_schema(doc)
    assert type(excinfo.value) is M.FreezeError
    assert "name と gate_predicate の mask が不一致" in str(excinfo.value)


def test_trigger_name_mask_binding_has_complete_diagnostic():
    predicate = M.s8a_trigger_sweep.predicate_for(("readvali-tid",))
    with pytest.raises(M.FreezeError) as excinfo:
        M._require_trigger_name_mask_binding(
            "g_rl", predicate,
            workload="balanced", configuration="system_gate")
    assert type(excinfo.value) is M.FreezeError
    assert str(excinfo.value) == (
        "entries.balanced.system_gate.name と gate_predicate の mask が不一致: "
        "name='g_rl' predicate_mask=4 expected_names=('g_rt',)")


def test_trigger_entries_rejects_coordinated_noncanonical_system_gate():
    entries = _current_frozen_document()["entries"]
    for workload in M.WORKLOADS:
        gate_name = entries[workload]["system_gate"]["name"]
        provenance = _trigger_provenance(
            gate_name=gate_name,
            gate_predicate=_NONCANONICAL_PREDICATE,
            ident_predicate=entries[workload]["ident_all"]["gate_predicate"],
        )
        with pytest.raises(M.FreezeError) as excinfo:
            _call_trigger_entries_with_mocked_provenance(
                workload=workload, gate_name=gate_name, provenance=provenance)
        assert str(excinfo.value) == (
            f"entries.{workload}.system_gate.gate_predicate が正準集合外")


def test_trigger_entries_rejects_coordinated_noncanonical_ident_all():
    entries = _current_frozen_document()["entries"]
    for workload in M.WORKLOADS:
        gate_name = entries[workload]["system_gate"]["name"]
        provenance = _trigger_provenance(
            gate_name=gate_name,
            gate_predicate=entries[workload]["system_gate"]["gate_predicate"],
            ident_predicate=_NONCANONICAL_PREDICATE,
        )
        with pytest.raises(M.FreezeError) as excinfo:
            _call_trigger_entries_with_mocked_provenance(
                workload=workload, gate_name=gate_name, provenance=provenance)
        assert str(excinfo.value) == (
            f"entries.{workload}.ident_all.gate_predicate が正準集合外")


def test_trigger_entries_rejects_coordinated_canonical_name_mask_tamper():
    entries = _current_frozen_document()["entries"]
    alternate_predicate = M.s8a_trigger_sweep.predicate_for(())
    for workload in M.WORKLOADS:
        gate_name = entries[workload]["system_gate"]["name"]
        for configuration in ("system_gate", "ident_all"):
            gate_predicate = entries[workload]["system_gate"]["gate_predicate"]
            ident_predicate = entries[workload]["ident_all"]["gate_predicate"]
            if configuration == "system_gate":
                gate_predicate = alternate_predicate
            else:
                ident_predicate = alternate_predicate
            provenance = _trigger_provenance(
                gate_name=gate_name,
                gate_predicate=gate_predicate,
                ident_predicate=ident_predicate,
            )
            with pytest.raises(M.FreezeError) as excinfo:
                _call_trigger_entries_with_mocked_provenance(
                    workload=workload,
                    gate_name=gate_name,
                    provenance=provenance,
                )
            assert type(excinfo.value) is M.FreezeError
            assert "name と gate_predicate の mask が不一致" in str(
                excinfo.value)


def test_validate_schema_rejects_noncanonical_system_gate():
    current = _current_frozen_document()
    for workload in M.WORKLOADS:
        doc = copy.deepcopy(current)
        doc["entries"][workload]["system_gate"][
            "gate_predicate"] = _NONCANONICAL_PREDICATE
        with pytest.raises(M.FreezeError) as excinfo:
            M._validate_schema(doc)
        assert str(excinfo.value) == (
            f"entries.{workload}.system_gate.gate_predicate が正準集合外")


def test_validate_schema_rejects_noncanonical_ident_all():
    current = _current_frozen_document()
    for workload in M.WORKLOADS:
        doc = copy.deepcopy(current)
        doc["entries"][workload]["ident_all"][
            "gate_predicate"] = _NONCANONICAL_PREDICATE
        with pytest.raises(M.FreezeError) as excinfo:
            M._validate_schema(doc)
        assert str(excinfo.value) == (
            f"entries.{workload}.ident_all.gate_predicate が正準集合外")


def test_validate_schema_rejects_coordinated_canonical_name_mask_tamper():
    current = _current_frozen_document()
    alternate_predicate = M.s8a_trigger_sweep.predicate_for(())
    for workload in M.WORKLOADS:
        for configuration in ("system_gate", "ident_all"):
            doc = copy.deepcopy(current)
            doc["entries"][workload][configuration][
                "gate_predicate"] = alternate_predicate
            with pytest.raises(M.FreezeError) as excinfo:
                M._validate_schema(doc)
            assert type(excinfo.value) is M.FreezeError
            assert "name と gate_predicate の mask が不一致" in str(
                excinfo.value)


def test_generate_rejects_noncanonical_predicate_before_writing(tmp_path):
    current = _current_frozen_document()["entries"]["balanced"]
    provenance = _trigger_provenance(
        gate_name=current["system_gate"]["name"],
        gate_predicate=_NONCANONICAL_PREDICATE,
        ident_predicate=current["ident_all"]["gate_predicate"],
    )
    output_path = tmp_path / "known_axes_freeze.json"
    with mock.patch.object(M, "_p2_entry", return_value=({}, "mocked")), \
            mock.patch.object(M, "_fixed_gates_from_recon", return_value={
                workload: "g_rl" for workload in M.WORKLOADS}), \
            mock.patch.object(M, "_stock_common", return_value={}), \
            mock.patch.object(M, "_backoff_entry", return_value={}), \
            mock.patch.object(M, "_sort_entry", return_value={}), \
            mock.patch.object(
                M, "_campaign_file",
                side_effect=lambda campaign, relative: M.ROOT / campaign / relative), \
            mock.patch.object(
                M, "_load_json",
                side_effect=lambda _path: copy.deepcopy(provenance)), \
            mock.patch.object(
                M.s8a_trigger_sweep, "_genome",
                return_value=mock.Mock(flags=dict(M.trigger_axis._BASE))), \
            mock.patch.object(M, "_source", return_value={}), \
            mock.patch.object(M, "_module_source", return_value={}), \
            mock.patch.object(M, "_run_git", return_value="a" * 40), \
            mock.patch.object(M, "_sha256", return_value="b" * 64):
        with pytest.raises(M.FreezeError) as excinfo:
            M.generate(output_path)
    assert str(excinfo.value) == (
        "entries.balanced.system_gate.gate_predicate が正準集合外")
    assert not output_path.exists()


def test_verify_document_rejects_noncanonical_predicate_before_rebuild():
    doc = copy.deepcopy(_current_frozen_document())
    doc["entries"]["balanced"]["system_gate"][
        "gate_predicate"] = _NONCANONICAL_PREDICATE
    with mock.patch.object(
            M, "build_document",
            side_effect=AssertionError("schema 拒否後に再構成へ到達した")) as rebuild:
        with pytest.raises(M.FreezeError) as excinfo:
            M.verify_document(doc)
    assert str(excinfo.value) == (
        "entries.balanced.system_gate.gate_predicate が正準集合外")
    rebuild.assert_not_called()


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


def test_silo_cmake_rel_matches_source_digest_template():
    """[T-149] protocol→CMakeLists パスの同族ドリフト検査 (T-148 が導入した
    source_digest._PROTOCOL_CMAKE との整合)。s1 本体は generator 自己 hash + sources pin
    (known_axes_freeze.json) で凍結されているため**編集せず**、外部から関係だけを機械検査
    する (2026-07-28 段 4 裁定、F27 回避)。"""
    from campaign import source_digest
    assert M.SILO_CMAKE_REL == (
        "external/ccbench/" + source_digest._PROTOCOL_CMAKE.format(protocol="silo")), \
        "s1 の SILO_CMAKE_REL と source_digest._PROTOCOL_CMAKE がドリフト。s1 は凍結 pin " \
        "済みのため、揃え直しは freeze migration の裁定を経ること"


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
