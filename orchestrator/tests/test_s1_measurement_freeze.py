# -*- coding: utf-8 -*-
"""S-1 measurement freeze v2 の統合テストと改竄 positive control。"""
from __future__ import annotations

import ast
import copy
import json
import os
import sys
from pathlib import Path

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)
sys.path.insert(0, _ORCH)

import s1_expected_goldens  # noqa: E402
from campaign import s1_known_axes_freeze as K  # noqa: E402
from campaign import s1_measurement_freeze as M  # noqa: E402
from campaign import t080_freeze_migration as T080  # noqa: E402
from skiputil import skip  # noqa: E402


_SUBMODULE_DIR = K.ROOT / "external" / "ccbench"


def _submodule_initialized(sub: Path = _SUBMODULE_DIR) -> bool:
    """external/ccbench が init 済みかを gitlink `.git` の存在だけで判定する。"""
    return (sub / ".git").exists()


def _require_submodule_sources() -> None:
    """実 known-axes 生成に必要な submodule が未 init の場合だけ skip する。"""
    if not _submodule_initialized():
        skip(
            "submodule 未 init (external/ccbench に .git 無し) — "
            "build_document は実 ccbench ソースが要る"
        )


@pytest.fixture(scope="module")
def real_known_axes_doc():
    """外部 golden と自己検証を通した実 known-axes 文書を module 内で共有する。"""
    from campaign import pin

    _require_submodule_sources()
    doc = K.build_document()
    ccbench_pin = doc["ccbench_pin"]
    assert len(ccbench_pin) == 40 and all(
        c in "0123456789abcdef" for c in ccbench_pin
    ), f"ccbench_pin が 40 桁 full SHA でない: {ccbench_pin}"
    assert ccbench_pin.startswith(pin.CURRENT_PIN), (
        f"ccbench worktree HEAD {ccbench_pin} が CURRENT_PIN "
        f"{pin.CURRENT_PIN} を prefix に持たない"
    )
    s1_expected_goldens.assert_known_axes_goldens(doc)
    K.verify_document(doc)
    return doc


@pytest.fixture
def freeze_env(tmp_path, real_known_axes_doc):
    """実 known-axes 文書を毎テスト fresh なファイルへ直列化する。"""
    known_path = tmp_path / "known_axes_freeze.json"
    known_path.write_text(
        json.dumps(real_known_axes_doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    stats_path = tmp_path / "s1_stats.py"
    stats_path.write_text("# dummy stats implementation\n", encoding="utf-8")

    def resolver(path_rel: str) -> Path:
        return {
            M.KNOWN_AXES_REL: known_path,
            M.STATS_REL: stats_path,
            M.SCRIPT_REL: M.SCRIPT_PATH,
        }[path_rel]

    return {
        "known_path": known_path,
        "stats_path": stats_path,
        "resolver": resolver,
    }


def _build(env) -> dict:
    return M.build_document(
        known_axes_path=env["known_path"],
        stats_path=env["stats_path"],
    )


def _generate(path: Path, env) -> dict:
    return M.generate(
        path,
        known_axes_path=env["known_path"],
        stats_path=env["stats_path"],
    )


def _verify(path: Path, env) -> dict:
    return M.verify(
        path,
        source_resolver=env["resolver"],
    )


def test_generate_builds_registered_cells_comparisons_and_schedule(
        freeze_env, real_known_axes_doc):
    doc = _build(freeze_env)
    assert len(doc["cells"]) == 18
    for cell in doc["cells"].values():
        s1_expected_goldens.assert_json_exact(
            cell["variant"],
            real_known_axes_doc["entries"][cell["workload"]][
                cell["configuration"]
            ],
            f"cells.{cell['workload']}:{cell['configuration']}.variant",
        )
    assert len(doc["comparisons"]) == 12
    assert sum(c["family"] == "S-1a" for c in doc["comparisons"]) == 9
    assert sum(c["family"] == "S-1b" for c in doc["comparisons"]) == 3
    assert {c["alternative"] for c in doc["comparisons"]} == {"greater"}
    s1_expected_goldens.assert_json_exact(
        doc["comparisons"],
        s1_expected_goldens.EXPECTED_COMPARISONS,
        "comparisons",
    )
    assert doc["master_seed"] == s1_expected_goldens.EXPECTED_MASTER_SEED
    assert doc["schedule_hash"] == s1_expected_goldens.EXPECTED_SCHEDULE_HASH
    assert sum(len(order) for rounds in doc["schedule"].values()
               for order in rounds) == 288
    assert doc["operating_point"] == {
        "RECORDS": 1_000_000, "THREADS": 48, "EXTIME": 3, "REPS": 5,
    }
    assert doc["workload_flags"] == {
        "balanced": {"ycsb_rratio": "50"},
        "write-heavy": {"ycsb_rratio": "5"},
        "read-heavy": {"ycsb_rratio": "95"},
    }


def test_generate_refuses_existing_freeze(tmp_path, freeze_env):
    path = tmp_path / "measurement_freeze.json"
    _generate(path, freeze_env)
    with pytest.raises(M.FreezeError, match="既に存在"):
        _generate(path, freeze_env)


def test_verify_rejects_one_byte_freeze_tamper(tmp_path, freeze_env):
    path = tmp_path / "measurement_freeze.json"
    _generate(path, freeze_env)
    original = path.read_bytes()
    tampered = original.replace(b'"what": "S-1', b'"what": "X-1', 1)
    assert tampered != original
    assert len(tampered) == len(original)
    path.write_bytes(tampered)
    with pytest.raises(M.FreezeError) as excinfo:
        _verify(path, freeze_env)
    assert str(excinfo.value) == (
        "freeze JSON の内容が現行 generator による機械再構成と不一致"
    )


def test_verify_rejects_one_byte_workload_flag_tamper(tmp_path, freeze_env):
    path = tmp_path / "measurement_freeze.json"
    _generate(path, freeze_env)
    original = path.read_bytes()
    tampered = original.replace(b'"ycsb_rratio": "50"',
                                b'"ycsb_rratio": "51"', 1)
    assert tampered != original
    assert len(tampered) == len(original)
    path.write_bytes(tampered)
    with pytest.raises(M.FreezeError, match="workload_flags"):
        _verify(path, freeze_env)


def test_verify_rejects_stats_implementation_tamper(tmp_path, freeze_env):
    path = tmp_path / "measurement_freeze.json"
    _generate(path, freeze_env)
    freeze_env["stats_path"].write_text(
        "# dummy stats implementation changed\n", encoding="utf-8")
    with pytest.raises(M.FreezeError, match="implementation_hashes.s1_stats"):
        _verify(path, freeze_env)


def test_verify_rejects_known_axes_material_tamper(tmp_path, freeze_env):
    path = tmp_path / "measurement_freeze.json"
    _generate(path, freeze_env)
    freeze_env["known_path"].write_bytes(
        freeze_env["known_path"].read_bytes() + b" ")
    with pytest.raises(M.FreezeError, match="implementation_hashes.known_axes_freeze"):
        _verify(path, freeze_env)


def test_schedule_is_balanced_and_reproducible(freeze_env):
    first = _build(freeze_env)
    second = _build(freeze_env)
    expected_cells = set(first["cells"])
    total = 0
    for campaign, rounds in first["schedule"].items():
        assert len(rounds) == M.CAMPAIGN_ROUNDS[campaign]
        for order in rounds:
            assert len(order) == 18
            assert len(set(order)) == 18
            assert set(order) == expected_cells
            total += len(order)
    assert total == 288
    assert first["schedule"] == second["schedule"]
    assert first["schedule_hash"] == second["schedule_hash"]


def test_s1b_pairing_rejects_mismatched_flags(freeze_env):
    doc = _build(freeze_env)
    forged = copy.deepcopy(doc)
    forged["cells"]["balanced:ident_all"]["variant"]["flags"]["BACK_OFF"] = 0
    with pytest.raises(M.FreezeError, match="flags 不一致"):
        M.verify_document(
            forged,
            source_resolver=freeze_env["resolver"],
        )


def test_build_document_rejects_tampered_known_axes_semantics(
        tmp_path, real_known_axes_doc):
    tampered = copy.deepcopy(real_known_axes_doc)
    tampered["what"] = "TAMPERED"
    known_path = tmp_path / "known_axes_freeze.json"
    known_path.write_text(
        json.dumps(tampered, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    stats_path = tmp_path / "s1_stats.py"
    stats_path.write_text("# dummy stats implementation\n", encoding="utf-8")

    with pytest.raises(M.FreezeError) as excinfo:
        M.build_document(known_axes_path=known_path, stats_path=stats_path)
    message = str(excinfo.value)
    assert message.startswith("known_axes_freeze 照合失敗:")
    assert "機械再構成と不一致" in message


def test_receipt_exists_but_measurement_verify_stays_legacy_strict(
        tmp_path, monkeypatch, freeze_env):
    receipt = tmp_path / T080.RECEIPT_REL
    receipt.parent.mkdir(parents=True)
    receipt.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(T080, "ROOT", tmp_path)

    def adapter_must_not_run(*_args, **_kwargs):
        pytest.fail("measurement legacy 経路が T-080 adapter を呼んだ")

    monkeypatch.setattr(T080, "verify_receipt", adapter_must_not_run)
    monkeypatch.setattr(T080, "static_gate_adapter", adapter_must_not_run)
    assert (T080.ROOT / T080.RECEIPT_REL).is_file()

    freeze_path = tmp_path / "measurement-freeze.json"
    freeze_path.write_text(
        json.dumps(_build(freeze_env), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    verified = _verify(freeze_path, freeze_env)
    assert len(verified["cells"]) == 18


def test_measurement_production_module_does_not_import_t080_adapter():
    source = Path(M.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
            imports.extend(alias.name for alias in node.names)
    assert not [name for name in imports if "t080_freeze_migration" in name]
    assert "verify_receipt" not in source and "static_gate_adapter" not in source


def test_build_schedule_is_deterministic_and_balanced_without_submodule():
    first = M.build_schedule(M.MASTER_SEED)
    second = M.build_schedule(M.MASTER_SEED)
    assert first == second
    total = 0
    for rounds in first.values():
        for order in rounds:
            assert len(order) == 18
            assert len(set(order)) == 18
            total += len(order)
    assert total == 288


def test_build_comparisons_structure_without_submodule():
    comparisons = M._build_comparisons()
    assert len(comparisons) == 12
    assert sum(c["family"] == "S-1a" for c in comparisons) == 9
    assert sum(c["family"] == "S-1b" for c in comparisons) == 3
    assert {c["alternative"] for c in comparisons} == {"greater"}
    assert all("stock_common" in c["note"] for c in comparisons)
