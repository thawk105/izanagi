# -*- coding: utf-8 -*-
"""S-1 既知軸 freeze の統合テストと改竄 positive control。"""
from __future__ import annotations

import copy
import json
import os
import shutil
import sys
from pathlib import Path

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import s1_known_axes_freeze as M  # noqa: E402
from skiputil import skip  # noqa: E402


def _require_submodule_sources():
    """build_document()/generate() は external/ccbench の実ファイル (Options.cmake /
    silo CMakeLists) を読み、submodule に対し git rev-parse する。submodule 未 checkout の
    環境では該当ファイルの不在を検知して skip (README の『submodule が無い環境では skip
    として数える』契約)。checkout 済みの環境では従来どおり実検査が走る。"""
    for rel in (M.OPTIONS_REL, M.SILO_CMAKE_REL):
        if not (M.ROOT / rel).exists():
            skip(f"submodule 未 checkout ({rel} 不在) — build_document は実 ccbench ソースが要る")


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
