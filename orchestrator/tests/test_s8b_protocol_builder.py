# -*- coding: utf-8 -*-
"""protocol builder / writer と contract_sha256 cross-field pin の契約テスト。

裁定: C4-4 (freeze/ccbench 充填元・追認禁止)、C4-7 (production path 事故防止)、
§5-v (contract_sha256 = 18 key)。

- 独立 golden: 固定引数に対する canonical bytes/sha256 をテスト側に literal で持つ
  (builder 自己整合ではなく期待 bytes を外から与える)。
- 全 pin field の一項目 mutation を validate_protocol が拒否する。
- builder: 実 v1 bytes / 実 gitlink が承認定数と不一致なら組立て前に拒否 (追認禁止)、
  master_seed / env_tag 欠落は TypeError。
- writer: create-only・既存拒否・実 repo 凍結領域拒否・tmp では成功。
- 実行前後で実 repo tree が不変であること。
"""
from __future__ import annotations

import copy
import contextlib
import hashlib
import io
import inspect
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

ORCHESTRATOR = Path(__file__).resolve().parents[1]
ROOT = ORCHESTRATOR.parent
sys.path.insert(0, str(ORCHESTRATOR.parent))

from orchestrator.campaign import env_contract as ec  # noqa: E402
from orchestrator.campaign import s8b_approved  # noqa: E402
from orchestrator.campaign import s8b_floor_campaign as fc  # noqa: E402
from orchestrator.tests import repo_tree_util  # noqa: E402
from orchestrator.tests.skiputil import Skip, skip  # noqa: E402

# 固定 golden 引数。env_tag は登録済み linux-baremetal、freeze/ccbench は実 repo を要求する。
_G_SEED = "golden-master-seed"
_G_ENV = "linux-baremetal"
_G_STOCK = "stock_common"
_G_EXTIME = 5
_G_FLOOR = 0.05

# 独立 golden (期待 canonical bytes/sha256 をテスト側に literal で保持)。
_GOLDEN_BYTES = (
    b'{"allowed_excluded_reasons":["competing_process","launch_failure",'
    b'"nonfinite_or_partial_output","performance_anomaly"],'
    b'"ccbench_pin":"511c9538e4e8efa54b45cda62e72389ed3b706ec",'
    b'"cell_cv_max":"0.15",'
    b'"contract_sha256":"1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7",'
    b'"env_tag":"linux-baremetal","extime_s":5,"formula":"s8b-floor-stats/v2",'
    b'"freeze":{"path":"output/s8b-freeze/holdout_freeze.json",'
    b'"sha256":"315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688"},'
    b'"master_seed":"golden-master-seed","n_sessions":8,"reps":5,'
    b'"retry_slots_per_cell":2,"scale_adequacy_rel_tolerance":"0.10",'
    b'"schedule_algorithm":"round-permutation/v2","schema":"s8b-floor-protocol/v2",'
    b'"session_cv_max":"0.10","stock_configuration":"stock_common",'
    b'"wired_min_rel_floor":0.05}'
)
_GOLDEN_SHA = "32e306c1e009adf03eabcbb314bb3542d7c76e892462213d759660c618e7dc4d"


def _requires_repo() -> None:
    """builder は実 v1 bytes と実 gitlink を要求する。前提が無ければ SKIP。"""
    if not (ROOT / s8b_approved.APPROVED_FREEZE_PATH).is_file():
        skip("v1 freeze 不在 (builder の実 bytes 照合ができない)")
    try:
        subprocess.run(
            ["git", "ls-tree", "HEAD", "external/ccbench"],
            cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        skip("git ls-tree 実行不能 (builder の gitlink 照合ができない)")


def _build_golden() -> fc.BuiltProtocol:
    _requires_repo()
    return fc.build_protocol_document(
        _G_SEED, _G_ENV, stock_configuration=_G_STOCK,
        extime_s=_G_EXTIME, wired_min_rel_floor=_G_FLOOR,
    )


# --------------------------------------------------------------------------- #
# golden + validate 通過                                                        #
# --------------------------------------------------------------------------- #

def test_builder_golden_bytes_and_sha_are_stable():
    built = _build_golden()
    assert built.canonical_bytes == _GOLDEN_BYTES, "canonical bytes が独立 golden と不一致"
    assert built.sha256 == _GOLDEN_SHA
    assert hashlib.sha256(built.canonical_bytes).hexdigest() == built.sha256


def test_builder_document_roundtrips_validate_protocol():
    built = _build_golden()
    # builder 出力は validate_protocol を再度通しても不変 (受理ゲート整合)。
    assert fc.validate_protocol(built.document) == built.document
    assert set(built.document) == set(fc._PROTOCOL_KEYS)
    assert len(fc._PROTOCOL_KEYS) == 18, "contract_sha256 追加で 18 key"
    # contract_sha256 は env 契約から導出された実値である。
    assert built.document["contract_sha256"] == ec.lookup(_G_ENV).contract_sha256


def test_approved_constants_protocol_bytes_match_parent_precalculation():
    _requires_repo()
    built = fc.build_protocol_document(
        s8b_approved.APPROVED_MASTER_SEED,
        s8b_approved.APPROVED_ENV_TAG,
        stock_configuration=s8b_approved.APPROVED_STOCK_CONFIGURATION,
        extime_s=s8b_approved.APPROVED_EXTIME_S,
        wired_min_rel_floor=s8b_approved.APPROVED_WIRED_MIN_REL_FLOOR,
    )
    assert len(built.canonical_bytes) == 774
    assert built.sha256 == "2c8cf9be929d83653814ecf5f2d5ed134a2af89686d796b8144da2fd45dfa58a"


def test_builder_rejects_holdout_conjunction_in_master_seed():
    _requires_repo()
    holdout = next(iter(fc._holdout_freeze.HOLDOUTS.values()))
    ycsb = holdout["ycsb"]
    axes = (
        ("rratio", fc._holdout_freeze.RRATIO_KEY),
        ("skew", fc._holdout_freeze.SKEW_KEY),
        ("rmw", fc._holdout_freeze.RMW_KEY),
    )
    # 実 holdout 値は source literal にせず、正本から取得して実行時に文字列結合する。
    contaminated_seed = " ".join(
        fc._holdout_freeze.concrete_axis_encodings(axis, ycsb[key])[0]
        for axis, key in axes
    )
    with pytest.raises(fc.FloorCampaignError, match="conjunction hit"):
        fc.build_protocol_document(
            contaminated_seed, _G_ENV, stock_configuration=_G_STOCK,
            extime_s=_G_EXTIME, wired_min_rel_floor=_G_FLOOR,
        )


# --------------------------------------------------------------------------- #
# 全 pin field mutation 拒否                                                    #
# --------------------------------------------------------------------------- #

def test_validate_protocol_rejects_each_pinned_field_mutation():
    base = _build_golden().document
    reversed_reasons = list(reversed(base["allowed_excluded_reasons"]))
    # validate_protocol が値 pin する全 field と、承認と異なる値。
    mutations = {
        "schema": "s8b-floor-protocol/v1",
        "formula": "s8b-floor-stats/v1",
        "schedule_algorithm": "round-permutation/v1",
        "n_sessions": 7,
        "reps": 4,
        "retry_slots_per_cell": 3,
        "session_cv_max": "0.20",
        "cell_cv_max": "0.10",
        "scale_adequacy_rel_tolerance": "0.05",
        "allowed_excluded_reasons": reversed_reasons,
        "contract_sha256": "1" * 64,
    }
    for field, bad in mutations.items():
        doc = copy.deepcopy(base)
        doc[field] = bad
        try:
            fc.validate_protocol(doc)
        except fc.FloorCampaignError:
            continue
        raise AssertionError(f"pin field {field} の mutation を拒否しなかった: {bad!r}")


def test_validate_protocol_rejects_contract_sha256_mismatch():
    base = _build_golden().document
    doc = copy.deepcopy(base)
    doc["contract_sha256"] = "0" * 64
    with pytest.raises(fc.FloorCampaignError, match="contract_sha256"):
        fc.validate_protocol(doc)


def test_validate_protocol_rejects_unregistered_env_tag():
    base = _build_golden().document
    doc = copy.deepcopy(base)
    doc["env_tag"] = "unregistered-env"
    doc["contract_sha256"] = "0" * 64
    with pytest.raises(fc.FloorCampaignError, match="env 契約"):
        fc.validate_protocol(doc)


# --------------------------------------------------------------------------- #
# builder の追認禁止 (C4-4)                                                     #
# --------------------------------------------------------------------------- #

def test_builder_rejects_v1_bytes_mismatch():
    _requires_repo()
    # 承認定数を実 bytes と異なる値へ差し替え → builder は組立て前に拒否する。
    with mock.patch.object(s8b_approved, "APPROVED_FREEZE_SHA256", "1" * 64):
        with pytest.raises(fc.FloorCampaignError, match="v1 freeze bytes が承認定数と不一致"):
            fc.build_protocol_document(
                _G_SEED, _G_ENV, stock_configuration=_G_STOCK,
                extime_s=_G_EXTIME, wired_min_rel_floor=_G_FLOOR,
            )


def test_builder_rejects_ccbench_gitlink_mismatch():
    _requires_repo()
    with mock.patch.object(s8b_approved, "CCBENCH_FULL_SHA", "0" * 40):
        with pytest.raises(fc.FloorCampaignError, match="ccbench gitlink が承認定数と不一致"):
            fc.build_protocol_document(
                _G_SEED, _G_ENV, stock_configuration=_G_STOCK,
                extime_s=_G_EXTIME, wired_min_rel_floor=_G_FLOOR,
            )


def test_builder_requires_master_seed_and_env_tag():
    # 必須引数の欠落は default を持たないため TypeError (値の発明を禁止)。
    with pytest.raises(TypeError):
        fc.build_protocol_document(stock_configuration=_G_STOCK, extime_s=_G_EXTIME,
                                   wired_min_rel_floor=_G_FLOOR)
    with pytest.raises(TypeError):
        fc.build_protocol_document(_G_SEED, stock_configuration=_G_STOCK,
                                   extime_s=_G_EXTIME, wired_min_rel_floor=_G_FLOOR)


def test_builder_rejects_unregistered_env_tag_before_assembly():
    _requires_repo()
    with pytest.raises(fc.FloorCampaignError, match="env 契約"):
        fc.build_protocol_document(
            _G_SEED, "unregistered-env", stock_configuration=_G_STOCK,
            extime_s=_G_EXTIME, wired_min_rel_floor=_G_FLOOR,
        )


# --------------------------------------------------------------------------- #
# writer                                                                        #
# --------------------------------------------------------------------------- #

def test_writer_create_only_and_bytes_match(tmp_path):
    built = _build_golden()
    dest = tmp_path / "nested" / "protocol.json"
    written = fc.write_protocol_document(dest, built, root=tmp_path)
    assert written == dest
    # ファイル bytes は canonical bytes と一致し sha256 は built.sha256 に等しい。
    raw = dest.read_bytes()
    assert raw == built.canonical_bytes
    assert hashlib.sha256(raw).hexdigest() == built.sha256
    # create-only: 既存 path への再書込みは拒否。
    with pytest.raises(fc.FloorCampaignError, match="既に存在"):
        fc.write_protocol_document(dest, built, root=tmp_path)


def test_writer_rejects_real_repo_freeze_dir():
    built = _build_golden()
    # 実 repo の凍結領域配下は第二防壁で拒否 (実凍結はユーザー手順)。書込みは起きない。
    dest = ROOT / "output" / "s8b-freeze" / "should_not_be_written.json"
    with pytest.raises(fc.FloorCampaignError, match="凍結領域配下への書込みは拒否"):
        fc.write_protocol_document(dest, built)
    assert not dest.exists(), "拒否したのにファイルが生成された"
    dest2 = ROOT / "output" / "env" / "should_not_be_written.json"
    with pytest.raises(fc.FloorCampaignError, match="凍結領域配下への書込みは拒否"):
        fc.write_protocol_document(dest2, built)
    assert not dest2.exists()


def test_writer_rejects_non_built_protocol(tmp_path):
    with pytest.raises(fc.FloorCampaignError, match="BuiltProtocol でない"):
        fc.write_protocol_document(tmp_path / "x.json", {"not": "built"}, root=tmp_path)


# --------------------------------------------------------------------------- #
# freeze-protocol (人間専用の実凍結 API / CLI)                                 #
# --------------------------------------------------------------------------- #

def _init_freeze_protocol_repo(tmp_path: Path) -> Path:
    _requires_repo()
    repo = tmp_path / "freeze-repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "-q"], cwd=str(repo),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    freeze_rel = Path(s8b_approved.APPROVED_FREEZE_PATH)
    freeze_path = repo / freeze_rel
    freeze_path.parent.mkdir(parents=True)
    freeze_path.write_bytes((ROOT / freeze_rel).read_bytes())
    subprocess.run(
        ["git", "add", freeze_rel.as_posix()], cwd=str(repo),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    subprocess.run(
        [
            "git", "update-index", "--add", "--cacheinfo",
            f"160000,{s8b_approved.CCBENCH_FULL_SHA},external/ccbench",
        ],
        cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    subprocess.run(
        [
            "git", "-c", "user.name=Izanagi Test",
            "-c", "user.email=izanagi-test@example.invalid",
            "commit", "-qm", "fixture basis",
        ],
        cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    return repo


def _init_reseal_protocol_repo(tmp_path: Path, *, name: str = "reseal-repo") -> Path:
    """committed legacy anchor と任意 HEAD gitlink だけを持つ tmp repository。"""
    repo = tmp_path / name
    repo.mkdir()
    subprocess.run(
        ["git", "init", "-q"], cwd=str(repo),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    anchor = repo / fc._FLOOR_PROTOCOL_REL
    anchor.parent.mkdir(parents=True)
    anchor.write_bytes((ROOT / fc._FLOOR_PROTOCOL_REL).read_bytes())
    subprocess.run(
        ["git", "add", fc._FLOOR_PROTOCOL_REL], cwd=str(repo),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    subprocess.run(
        [
            "git", "update-index", "--add", "--cacheinfo",
            f"160000,{s8b_approved.CCBENCH_FULL_SHA},external/ccbench",
        ],
        cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    subprocess.run(
        [
            "git", "-c", "user.name=Izanagi Test",
            "-c", "user.email=izanagi-test@example.invalid",
            "commit", "-qm", "reseal fixture basis",
        ],
        cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    return repo


def _registered_protocol_contract(recorded_hash: str, env_tag: str):
    """activation fixture 前の g2 も schema 検査できる test-only historical resolver。"""
    matches = [
        entry.contract
        for entry in ec.GENERATIONS.get(env_tag, ())
        if entry.contract.contract_sha256 == recorded_hash
    ]
    if len(matches) != 1:
        raise fc.FloorCampaignError("test historical contract を一意に解決できない")
    return matches[0]


def _pegasus_g2_contract():
    return ec.GENERATIONS["pegasus"][1].contract


def _canonical_protocol_bytes(document: dict) -> bytes:
    return json.dumps(
        document, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def _active_receipt(*, root):
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(root),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True,
    ).stdout.strip()
    return fc._t080_migration.ReceiptResolution(
        state="active-valid", refusals=(),
        t080_freeze_migration_observation={"fixture": "active"},
        validation_head=head,
    )


def test_freeze_protocol_confirm_flag_is_required(tmp_path):
    with pytest.raises(fc.FloorCampaignError, match="confirm-user-freeze"):
        fc.freeze_protocol(
            confirm_user_freeze=False, root=tmp_path,
            isatty_fn=lambda: True,
        )
    with pytest.raises(SystemExit) as exc_info:
        fc.main(["freeze-protocol"])
    assert exc_info.value.code == 2


def test_freeze_protocol_non_tty_is_refused_even_with_active_receipt(tmp_path):
    """isatty 防壁の受理集合検査: receipt が active でも非 tty なら凍結は成立しない。

    CLI の pipe-stdin テストは実 repo で receipt 段より手前に落ちるため、isatty 検査を
    無効化しても別層拒否で rc が同値になりうる。ここでは他の全前提を成立させた上で
    isatty だけを False にし、「destination が生まれない」ことを受理集合として固定する
    (変異 kill の帰属をこのテストが担う)。"""
    repo = _init_freeze_protocol_repo(tmp_path)
    with pytest.raises(fc.FloorCampaignError, match="対話 shell"):
        fc.freeze_protocol(
            confirm_user_freeze=True, root=repo,
            isatty_fn=lambda: False, receipt_verify_fn=_active_receipt,
        )
    assert not (repo / fc._FLOOR_PROTOCOL_REL).exists()


def test_freeze_protocol_cli_rejects_pipe_stdin():
    completed = subprocess.run(
        [
            sys.executable, str(ORCHESTRATOR / "campaign" / "s8b_floor_campaign.py"),
            "freeze-protocol", "--confirm-user-freeze",
        ],
        cwd=str(ROOT), input=b"", stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 1
    payload = json.loads(completed.stdout.decode("utf-8"))
    assert payload["status"] == "error"
    assert "実凍結は人間の対話 shell から実行する" in payload["error"]


def test_freeze_protocol_rejects_inactive_t080_receipt(tmp_path):
    repo = _init_freeze_protocol_repo(tmp_path)
    with pytest.raises(fc.FloorCampaignError, match="T-080 receipt が発効状態でない"):
        fc.freeze_protocol(
            confirm_user_freeze=True, root=repo,
            isatty_fn=lambda: True,
        )
    assert not (repo / fc._FLOOR_PROTOCOL_REL).exists()


def test_freeze_protocol_rejects_existing_destination(tmp_path):
    repo = _init_freeze_protocol_repo(tmp_path)
    destination = repo / fc._FLOOR_PROTOCOL_REL
    destination.write_bytes(b"existing")
    with pytest.raises(fc.FloorCampaignError, match="既に存在"):
        fc.freeze_protocol(
            confirm_user_freeze=True, root=repo,
            isatty_fn=lambda: True, receipt_verify_fn=_active_receipt,
        )
    assert destination.read_bytes() == b"existing"


def test_freeze_protocol_detects_post_write_readback_tamper_without_deleting(tmp_path):
    repo = _init_freeze_protocol_repo(tmp_path)

    def tamper(destination: Path) -> None:
        destination.write_bytes(destination.read_bytes() + b"\n")

    with pytest.raises(fc.FloorCampaignError, match="commit 禁止"):
        fc.freeze_protocol(
            confirm_user_freeze=True, root=repo,
            isatty_fn=lambda: True, receipt_verify_fn=_active_receipt,
            after_write_fn=tamper,
        )
    destination = repo / fc._FLOOR_PROTOCOL_REL
    assert destination.exists(), "post-write 検証失敗時に自動削除してはいけない"
    assert destination.read_bytes().endswith(b"\n")


def test_freeze_protocol_success_writes_only_fixed_tmp_repo_path(tmp_path):
    repo = _init_freeze_protocol_repo(tmp_path)
    outcome = fc.freeze_protocol(
        confirm_user_freeze=True, root=repo,
        isatty_fn=lambda: True, receipt_verify_fn=_active_receipt,
    )
    destination = repo / fc._FLOOR_PROTOCOL_REL
    raw = destination.read_bytes()
    assert outcome == {
        "status": "frozen",
        "path": fc._FLOOR_PROTOCOL_REL,
        "byte_length": 774,
        "sha256": "2c8cf9be929d83653814ecf5f2d5ed134a2af89686d796b8144da2fd45dfa58a",
    }
    assert len(raw) == outcome["byte_length"]
    assert hashlib.sha256(raw).hexdigest() == outcome["sha256"]
    assert fc.validate_protocol(fc.load_protocol(destination))["master_seed"] == (
        s8b_approved.APPROVED_MASTER_SEED
    )


# --------------------------------------------------------------------------- #
# AI reseal inheritance / index / issuer                                       #
# --------------------------------------------------------------------------- #

def test_ai_reseal_inheritance_exact_16_field_partition_and_mutations():
    predecessor = fc.validate_protocol(fc.load_protocol(ROOT / fc._FLOOR_PROTOCOL_REL))
    assert fc._AI_RESEAL_MUTABLE_FIELDS == frozenset({"contract_sha256", "ccbench_pin"})
    assert len(fc._AI_RESEAL_INHERITED_FIELDS) == 16
    successor = copy.deepcopy(predecessor)
    successor["contract_sha256"] = "1" * 64
    successor["ccbench_pin"] = "2" * 40
    fc.validate_ai_reseal_inheritance(predecessor, successor)

    mutations = {
        "schema": "another-schema",
        "formula": "another-formula",
        "env_tag": "another-env",
        "freeze": {"path": "another-path", "sha256": "3" * 64},
        "stock_configuration": "another-stock",
        "n_sessions": 9,
        "reps": 6,
        "master_seed": "another-seed",
        "schedule_algorithm": "another-schedule",
        "extime_s": 6,
        "wired_min_rel_floor": 1,
        "retry_slots_per_cell": 3,
        "session_cv_max": "0.11",
        "cell_cv_max": "0.16",
        "scale_adequacy_rel_tolerance": "0.11",
        "allowed_excluded_reasons": list(reversed(predecessor["allowed_excluded_reasons"])),
    }
    assert set(mutations) == set(fc._AI_RESEAL_INHERITED_FIELDS)
    for field, bad in mutations.items():
        mutated = copy.deepcopy(successor)
        mutated[field] = bad
        with pytest.raises(fc._floor_contract.FloorContractError, match="人間専有 field"):
            fc.validate_ai_reseal_inheritance(predecessor, mutated)

    integer = copy.deepcopy(predecessor)
    floating = copy.deepcopy(predecessor)
    integer["wired_min_rel_floor"] = 1
    floating["wired_min_rel_floor"] = 1.0
    with pytest.raises(fc._floor_contract.FloorContractError, match="wired_min_rel_floor"):
        fc.validate_ai_reseal_inheritance(integer, floating)


def test_public_index_rejects_validator_admitted_anchor_field_mutations(tmp_path):
    anchor = fc.validate_protocol(fc.load_protocol(ROOT / fc._FLOOR_PROTOCOL_REL))
    g2 = _pegasus_g2_contract()
    mutations = {
        "master_seed": "validator-admitted-different-seed",
        "wired_min_rel_floor": 0.000001,
        "stock_configuration": "validator-admitted-different-stock",
    }
    for field, bad in mutations.items():
        repo = _init_reseal_protocol_repo(tmp_path, name=f"public-mutation-{field}")
        candidate = copy.deepcopy(anchor)
        candidate["contract_sha256"] = g2.contract_sha256
        candidate["ccbench_pin"] = s8b_approved.CCBENCH_FULL_SHA
        candidate[field] = bad
        with mock.patch.object(
                fc, "_historical_protocol_contract",
                side_effect=_registered_protocol_contract,
        ):
            # 先取り確認: 単体 validator はこの変異を受理し、新しい継承 gate まで到達する。
            normalized = fc.validate_protocol(candidate)
            assert normalized[field] == bad
            rel = fc._derived_reseal_protocol_relpath(
                normalized["contract_sha256"], normalized["ccbench_pin"],
            )
            destination = repo / rel
            destination.parent.mkdir(parents=True)
            destination.write_bytes(_canonical_protocol_bytes(normalized))
            with pytest.raises(fc.FloorCampaignError, match="人間専有 field"):
                fc.scan_floor_protocol_index(root=repo)


def test_reseal_protocol_public_entry_accepts_unoccupied_contract_and_derived_path(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path)
    g2 = _pegasus_g2_contract()
    with mock.patch.object(fc, "ROOT", repo), mock.patch.object(
            fc._env_contract, "lookup", return_value=g2,
    ) as lookup_mock, mock.patch.object(
            fc, "_historical_protocol_contract",
            side_effect=_registered_protocol_contract,
    ), mock.patch.object(
            fc, "_ccbench_gitlink", wraps=fc._ccbench_gitlink,
    ) as gitlink_mock:
        outcome = fc.reseal_protocol()
    expected_rel = fc._derived_reseal_protocol_relpath(
        g2.contract_sha256, s8b_approved.CCBENCH_FULL_SHA,
    )
    assert outcome["status"] == "resealed"
    assert outcome["path"] == expected_rel
    assert lookup_mock.call_count == 1, "PID-cache authority の恒真な再照合を追加してはいけない"
    assert gitlink_mock.call_count == 2, "HEAD gitlink は build 前後に subprocess 再実測する"
    assert len({call.args[1] for call in gitlink_mock.call_args_list}) == 1
    versioned = list((repo / fc._FLOOR_PROTOCOLS_REL).iterdir())
    assert versioned == [repo / expected_rel]
    assert hashlib.sha256(versioned[0].read_bytes()).hexdigest() == outcome["sha256"]


def test_reseal_protocol_public_entry_rejects_contract_already_in_index(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path)
    g1 = ec.GENERATIONS["pegasus"][0].contract
    with mock.patch.object(fc, "ROOT", repo), mock.patch.object(
            fc._env_contract, "lookup", return_value=g1,
    ):
        with pytest.raises(fc.FloorCampaignError, match="同じ contract_sha256"):
            fc.reseal_protocol()
    assert not (repo / fc._FLOOR_PROTOCOLS_REL).exists()


def test_reseal_protocol_second_issue_preserves_first_bytes(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path)
    g2 = _pegasus_g2_contract()
    patches = (
        mock.patch.object(fc, "ROOT", repo),
        mock.patch.object(fc._env_contract, "lookup", return_value=g2),
        mock.patch.object(
            fc, "_historical_protocol_contract",
            side_effect=_registered_protocol_contract,
        ),
    )
    with patches[0], patches[1], patches[2]:
        first = fc.reseal_protocol()
        destination = repo / first["path"]
        first_bytes = destination.read_bytes()
        with pytest.raises(fc.FloorCampaignError, match="同じ contract_sha256"):
            fc.reseal_protocol()
    assert destination.read_bytes() == first_bytes


def test_reseal_protocol_rejects_head_move_immediately_after_publish(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path)
    g2 = _pegasus_g2_contract()
    original_writer = fc._write_protocol_document_create_only

    def moving_writer(destination, built):
        written = original_writer(destination, built)
        subprocess.run(
            [
                "git", "-c", "user.name=Izanagi Test",
                "-c", "user.email=izanagi-test@example.invalid",
                "commit", "--allow-empty", "-qm", "move head after publish",
            ],
            cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        )
        return written

    with mock.patch.object(fc, "ROOT", repo), mock.patch.object(
            fc._env_contract, "lookup", return_value=g2,
    ), mock.patch.object(
            fc, "_historical_protocol_contract",
            side_effect=_registered_protocol_contract,
    ), mock.patch.object(
            fc, "_write_protocol_document_create_only", side_effect=moving_writer,
    ):
        with pytest.raises(fc.FloorCampaignError, match="HEAD commit が変化"):
            fc.reseal_protocol()
    destination = repo / fc._derived_reseal_protocol_relpath(
        g2.contract_sha256, s8b_approved.CCBENCH_FULL_SHA,
    )
    assert destination.is_file(), "publish 後の拒否でも artifact を自動削除してはいけない"


def test_reseal_protocol_readback_tamper_is_not_deleted(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path)
    g2 = _pegasus_g2_contract()
    original_writer = fc._write_protocol_document_create_only

    def tampering_writer(destination, built):
        written = original_writer(destination, built)
        written.write_bytes(written.read_bytes() + b"\n")
        return written

    with mock.patch.object(fc, "ROOT", repo), mock.patch.object(
            fc._env_contract, "lookup", return_value=g2,
    ), mock.patch.object(
            fc, "_historical_protocol_contract",
            side_effect=_registered_protocol_contract,
    ), mock.patch.object(
            fc, "_write_protocol_document_create_only",
            side_effect=tampering_writer,
    ):
        with pytest.raises(fc.FloorCampaignError, match="read-back bytes"):
            fc.reseal_protocol()
    destination = repo / fc._derived_reseal_protocol_relpath(
        g2.contract_sha256, s8b_approved.CCBENCH_FULL_SHA,
    )
    assert destination.read_bytes().endswith(b"\n")


def test_reseal_protocol_readback_parse_mismatch_has_specific_reason(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path)
    g2 = _pegasus_g2_contract()
    destination_rel = fc._derived_reseal_protocol_relpath(
        g2.contract_sha256, s8b_approved.CCBENCH_FULL_SHA,
    )
    original_parser = fc._strict_parse_protocol_bytes

    def mismatching_parser(raw, *, source):
        parsed = original_parser(raw, source=source)
        if source == destination_rel:
            parsed = copy.deepcopy(parsed)
            parsed["master_seed"] = "read-back-parser-mismatch"
        return parsed

    with mock.patch.object(fc, "ROOT", repo), mock.patch.object(
            fc._env_contract, "lookup", return_value=g2,
    ), mock.patch.object(
            fc, "_historical_protocol_contract",
            side_effect=_registered_protocol_contract,
    ), mock.patch.object(
            fc, "_strict_parse_protocol_bytes", side_effect=mismatching_parser,
    ):
        with pytest.raises(fc.FloorCampaignError, match="read-back strict parse"):
            fc.reseal_protocol()


def test_reseal_protocol_post_write_index_mismatch_has_specific_reason(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path)
    g2 = _pegasus_g2_contract()
    target_pair = (g2.contract_sha256, s8b_approved.CCBENCH_FULL_SHA)
    original_scan = fc._scan_floor_protocol_index_at_commit
    scan_count = 0

    def omit_target_on_post_scan(*, root, commit_oid):
        nonlocal scan_count
        scan_count += 1
        index = original_scan(root=root, commit_oid=commit_oid)
        if scan_count == 2:
            return {pair: record for pair, record in index.items() if pair != target_pair}
        return index

    with mock.patch.object(fc, "ROOT", repo), mock.patch.object(
            fc._env_contract, "lookup", return_value=g2,
    ), mock.patch.object(
            fc, "_historical_protocol_contract",
            side_effect=_registered_protocol_contract,
    ), mock.patch.object(
            fc, "_scan_floor_protocol_index_at_commit",
            side_effect=omit_target_on_post_scan,
    ):
        with pytest.raises(fc.FloorCampaignError, match="post-write full index"):
            fc.reseal_protocol()
    assert scan_count == 2


def test_reseal_protocol_uses_committed_anchor_not_validator_admitted_dirty_copy(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path)
    committed = fc.validate_protocol(fc.load_protocol(repo / fc._FLOOR_PROTOCOL_REL))
    dirty = copy.deepcopy(committed)
    dirty["master_seed"] = "dirty-working-tree-seed"
    # 先取り確認: dirty 値は既存 validator を通り、D4 が無ければ継承され得る。
    assert fc.validate_protocol(dirty)["master_seed"] == "dirty-working-tree-seed"
    (repo / fc._FLOOR_PROTOCOL_REL).write_bytes(_canonical_protocol_bytes(dirty))

    g2 = _pegasus_g2_contract()
    with mock.patch.object(fc, "ROOT", repo), mock.patch.object(
            fc._env_contract, "lookup", return_value=g2,
    ), mock.patch.object(
            fc, "_historical_protocol_contract",
            side_effect=_registered_protocol_contract,
    ):
        outcome = fc.reseal_protocol()
    issued = fc.load_protocol(repo / outcome["path"])
    assert issued["master_seed"] == committed["master_seed"]
    assert issued["master_seed"] != dirty["master_seed"]


def test_reseal_protocol_scrubs_ambient_git_dir_authority(tmp_path, monkeypatch):
    repo = _init_reseal_protocol_repo(tmp_path, name="target-repo")
    decoy = _init_reseal_protocol_repo(tmp_path, name="decoy-repo")
    target_anchor = fc.validate_protocol(fc.load_protocol(repo / fc._FLOOR_PROTOCOL_REL))
    decoy_anchor = fc.validate_protocol(fc.load_protocol(decoy / fc._FLOOR_PROTOCOL_REL))
    decoy_anchor["master_seed"] = "ambient-git-dir-decoy"
    (decoy / fc._FLOOR_PROTOCOL_REL).write_bytes(_canonical_protocol_bytes(decoy_anchor))
    decoy_pin = "d" * 40
    subprocess.run(
        ["git", "add", fc._FLOOR_PROTOCOL_REL], cwd=str(decoy),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    subprocess.run(
        [
            "git", "update-index", "--add", "--cacheinfo",
            f"160000,{decoy_pin},external/ccbench",
        ],
        cwd=str(decoy), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    subprocess.run(
        [
            "git", "-c", "user.name=Izanagi Test",
            "-c", "user.email=izanagi-test@example.invalid",
            "commit", "-qm", "decoy authority",
        ],
        cwd=str(decoy), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    monkeypatch.setenv("GIT_DIR", str(decoy / ".git"))

    g2 = _pegasus_g2_contract()
    with mock.patch.object(fc, "ROOT", repo), mock.patch.object(
            fc._env_contract, "lookup", return_value=g2,
    ), mock.patch.object(
            fc, "_historical_protocol_contract",
            side_effect=_registered_protocol_contract,
    ):
        outcome = fc.reseal_protocol()

    issued = fc.load_protocol(repo / outcome["path"])
    assert outcome["ccbench_pin"] == s8b_approved.CCBENCH_FULL_SHA
    assert outcome["ccbench_pin"] != decoy_pin
    assert issued["master_seed"] == target_anchor["master_seed"]
    assert issued["master_seed"] != decoy_anchor["master_seed"]


def test_floor_protocol_index_includes_legacy_and_rejects_duplicate_pair(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path)
    anchor = fc.validate_protocol(fc.load_protocol(repo / fc._FLOOR_PROTOCOL_REL))
    pair = (anchor["contract_sha256"], anchor["ccbench_pin"])
    clean_index = fc.scan_floor_protocol_index(root=repo)
    assert set(clean_index) == {pair}
    assert clean_index[pair].path == fc._FLOOR_PROTOCOL_REL

    duplicate = repo / fc._derived_reseal_protocol_relpath(*pair)
    duplicate.parent.mkdir(parents=True)
    duplicate.write_bytes((repo / fc._FLOOR_PROTOCOL_REL).read_bytes())
    with pytest.raises(fc.FloorCampaignError, match="同一組"):
        fc.scan_floor_protocol_index(root=repo)


def test_floor_protocol_index_rejects_same_contract_with_different_pin(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path)
    candidate = fc.validate_protocol(fc.load_protocol(repo / fc._FLOOR_PROTOCOL_REL))
    candidate["ccbench_pin"] = "a" * 40
    destination = repo / fc._derived_reseal_protocol_relpath(
        candidate["contract_sha256"], candidate["ccbench_pin"],
    )
    destination.parent.mkdir(parents=True)
    destination.write_bytes(_canonical_protocol_bytes(candidate))
    with pytest.raises(fc.FloorCampaignError, match="同一 contract_sha256"):
        fc.scan_floor_protocol_index(root=repo)


@pytest.mark.parametrize("ancestor", ["output", "output/s8b-freeze"])
def test_floor_protocol_index_rejects_symlink_ancestors(tmp_path, ancestor):
    repo = _init_reseal_protocol_repo(tmp_path, name=ancestor.replace("/", "-"))
    path = repo / ancestor
    if path.is_dir():
        shutil.rmtree(path)
    external = tmp_path / f"external-{ancestor.replace('/', '-')}"
    external.mkdir()
    path.symlink_to(external, target_is_directory=True)
    with pytest.raises(fc.FloorCampaignError, match=rf"親が symlink: {ancestor}$"):
        fc.scan_floor_protocol_index(root=repo)


def test_floor_protocol_index_binds_blob_read_to_one_head_commit(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path)
    original_run = fc.subprocess.run
    old_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(repo),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    ).stdout.decode("ascii").strip()
    pinned_anchor = fc.validate_protocol(fc.load_protocol(repo / fc._FLOOR_PROTOCOL_REL))
    pinned_anchor["master_seed"] = "pinned-head-anchor"
    (repo / fc._FLOOR_PROTOCOL_REL).write_bytes(_canonical_protocol_bytes(pinned_anchor))
    subprocess.run(
        ["git", "add", fc._FLOOR_PROTOCOL_REL], cwd=str(repo),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    subprocess.run(
        [
            "git", "-c", "user.name=Izanagi Test",
            "-c", "user.email=izanagi-test@example.invalid",
            "commit", "-qm", "second anchor",
        ],
        cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    pinned_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(repo),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    ).stdout.decode("ascii").strip()
    commands = []
    moved = False

    def move_head_after_ls_tree(command, **kwargs):
        nonlocal moved
        commands.append(tuple(command))
        completed = original_run(command, **kwargs)
        if (not moved and command[:3] == ["git", "ls-tree", "-z"]
                and command[3] == pinned_commit):
            original_run(
                ["git", "reset", "--hard", "-q", old_commit], cwd=str(repo),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
                env=fc.source_digest._sanitized_git_env(),
            )
            moved = True
        return completed

    with mock.patch.object(fc.subprocess, "run", side_effect=move_head_after_ls_tree):
        index = fc.scan_floor_protocol_index(root=repo)

    anchor = next(record for record in index.values() if record.path == fc._FLOOR_PROTOCOL_REL)
    assert moved
    assert anchor.document["master_seed"] == "pinned-head-anchor"
    assert any(command[:4] == ("git", "ls-tree", "-z", pinned_commit)
               for command in commands)
    cat_file = [command for command in commands if command[:3] == ("git", "cat-file", "blob")]
    assert len(cat_file) == 1
    assert cat_file[0][3] != f"HEAD:{fc._FLOOR_PROTOCOL_REL}"


def test_floor_protocol_index_rejects_misderived_path(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path)
    candidate = fc.validate_protocol(fc.load_protocol(repo / fc._FLOOR_PROTOCOL_REL))
    g2 = _pegasus_g2_contract()
    candidate["contract_sha256"] = g2.contract_sha256
    candidate["ccbench_pin"] = s8b_approved.CCBENCH_FULL_SHA
    wrong_rel = fc._derived_reseal_protocol_relpath("0" * 64, candidate["ccbench_pin"])
    destination = repo / wrong_rel
    destination.parent.mkdir(parents=True)
    destination.write_bytes(_canonical_protocol_bytes(candidate))
    with mock.patch.object(
            fc, "_historical_protocol_contract",
            side_effect=_registered_protocol_contract,
    ):
        # 先取り確認: document 自体は valid で、path/document 束縛だけが拒否理由になる。
        fc.validate_protocol(candidate)
        with pytest.raises(fc.FloorCampaignError, match="導出値と不一致"):
            fc.scan_floor_protocol_index(root=repo)


def test_floor_protocol_index_rejects_closed_namespace_violations(tmp_path):
    cases = {
        "unknown-name": "予期しない名前",
        "nested-directory": "非通常 file",
        "symlink": "namespace に symlink",
    }
    for case, reason in cases.items():
        repo = _init_reseal_protocol_repo(tmp_path, name=f"closed-{case}")
        namespace = repo / fc._FLOOR_PROTOCOLS_REL
        namespace.mkdir(parents=True)
        if case == "unknown-name":
            (namespace / "unexpected.json").write_bytes(b"{}")
        elif case == "nested-directory":
            (namespace / "nested").mkdir()
        else:
            (namespace / "link.json").symlink_to(repo / fc._FLOOR_PROTOCOL_REL)
        with pytest.raises(fc.FloorCampaignError, match=reason):
            fc.scan_floor_protocol_index(root=repo)


def test_floor_protocol_index_rejects_strict_and_canonical_member_violations(tmp_path):
    anchor = fc.validate_protocol(fc.load_protocol(ROOT / fc._FLOOR_PROTOCOL_REL))
    g2 = _pegasus_g2_contract()
    candidate = copy.deepcopy(anchor)
    candidate["contract_sha256"] = g2.contract_sha256
    candidate["ccbench_pin"] = s8b_approved.CCBENCH_FULL_SHA
    rel = fc._derived_reseal_protocol_relpath(
        candidate["contract_sha256"], candidate["ccbench_pin"],
    )
    payloads = {
        "duplicate-key": (b'{"x":1,"x":2}', "duplicate key"),
        "noncanonical": (
            (json.dumps(candidate, ensure_ascii=False, indent=2) + "\n").encode(),
            "canonical bytes",
        ),
        "extra-key": (
            _canonical_protocol_bytes({**candidate, "extra": True}),
            "key 集合",
        ),
    }
    for case, (payload, reason) in payloads.items():
        repo = _init_reseal_protocol_repo(tmp_path, name=f"strict-{case}")
        destination = repo / rel
        destination.parent.mkdir(parents=True)
        destination.write_bytes(payload)
        with mock.patch.object(
                fc, "_historical_protocol_contract",
                side_effect=_registered_protocol_contract,
        ):
            with pytest.raises(fc.FloorCampaignError, match=reason):
                fc.scan_floor_protocol_index(root=repo)


def test_floor_protocol_index_requires_head_100644_blob(tmp_path):
    executable_repo = _init_reseal_protocol_repo(tmp_path, name="executable-anchor")
    anchor = executable_repo / fc._FLOOR_PROTOCOL_REL
    anchor.chmod(0o755)
    subprocess.run(
        ["git", "add", fc._FLOOR_PROTOCOL_REL], cwd=str(executable_repo),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    subprocess.run(
        [
            "git", "-c", "user.name=Izanagi Test",
            "-c", "user.email=izanagi-test@example.invalid",
            "commit", "-qm", "executable anchor",
        ], cwd=str(executable_repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    with pytest.raises(fc.FloorCampaignError, match="100644 blob"):
        fc.scan_floor_protocol_index(root=executable_repo)

    missing_repo = _init_reseal_protocol_repo(tmp_path, name="missing-head-anchor")
    subprocess.run(
        ["git", "rm", "--cached", "-q", fc._FLOOR_PROTOCOL_REL], cwd=str(missing_repo),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    subprocess.run(
        [
            "git", "-c", "user.name=Izanagi Test",
            "-c", "user.email=izanagi-test@example.invalid",
            "commit", "-qm", "untrack anchor",
        ], cwd=str(missing_repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    assert (missing_repo / fc._FLOOR_PROTOCOL_REL).is_file()
    with pytest.raises(fc.FloorCampaignError, match="HEAD"):
        fc.scan_floor_protocol_index(root=missing_repo)


def _clean_scan_with_isolated_repository_search(root: Path) -> str:
    with mock.patch.object(
            fc._holdout_freeze, "enumerate_repository_files", return_value=(),
    ), mock.patch.object(
            fc._holdout_freeze, "search_repository", return_value=object(),
    ), mock.patch.object(
            fc._holdout_freeze, "_assert_search_pass", return_value=None,
    ):
        return fc.clean_scan_digest(root, freeze_allowlist={})


def test_clean_scan_accepts_exact_versioned_protocol_chain_record(tmp_path):
    root = tmp_path / "positive-chain-record"
    path = root / fc._derived_reseal_protocol_relpath("a" * 64, "b" * 40)
    path.parent.mkdir(parents=True)
    path.write_bytes(b"versioned protocol bytes")
    digest = _clean_scan_with_isolated_repository_search(root)
    assert re.fullmatch(r"[0-9a-f]{64}", digest)


def test_clean_scan_rejects_overbroad_versioned_protocol_names(tmp_path):
    valid_name = f"{'a' * 64}--{'b' * 40}.json"
    invalid_relpaths = {
        "short-contract": f"{fc._FLOOR_PROTOCOLS_REL}/{'a' * 63}--{'b' * 40}.json",
        "short-pin": f"{fc._FLOOR_PROTOCOLS_REL}/{'a' * 64}--{'b' * 39}.json",
        "nested": f"{fc._FLOOR_PROTOCOLS_REL}/nested/{valid_name}",
        "alias": f"{fc._FLOOR_PROTOCOLS_REL}/alias-{valid_name}",
        "uppercase": f"{fc._FLOOR_PROTOCOLS_REL}/{'A' * 64}--{'b' * 40}.json",
    }
    for label, rel in invalid_relpaths.items():
        root = tmp_path / label
        path = root / rel
        path.parent.mkdir(parents=True)
        path.write_bytes(b"not sanctioned")
        with pytest.raises(fc.FloorCampaignError, match="未知 file"):
            _clean_scan_with_isolated_repository_search(root)


def test_check_protocol_index_cli_is_read_only_and_deterministic(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path)
    outputs = []

    def action():
        for _ in range(2):
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream), mock.patch.object(fc, "ROOT", repo):
                assert fc.main(["check-protocol-index"]) == 0
            outputs.append(stream.getvalue())

    repo_tree_util.assert_repo_tree_unchanged(repo, action)
    assert outputs[0] == outputs[1]
    payload = json.loads(outputs[0])
    assert payload["status"] == "ok"
    assert payload["count"] == 1
    assert payload["protocols"][0]["path"] == fc._FLOOR_PROTOCOL_REL


def test_reseal_protocol_cli_has_no_caller_selected_authority_options():
    for option in ("--path", "--contract-sha256", "--ccbench-pin"):
        with pytest.raises(SystemExit) as exc_info:
            fc.main(["reseal-protocol", option, "attacker-selected"])
        assert exc_info.value.code == 2


# --------------------------------------------------------------------------- #
# 実 repo tree 不変                                                             #
# --------------------------------------------------------------------------- #

def test_repo_status_scrubs_git_environment_and_disables_optional_locks(monkeypatch):
    """repo status と ls-files は同じ衛生化 Git env を使う。"""
    forbidden = (
        "GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES",
    )
    for name in forbidden:
        monkeypatch.setenv(name, f"decoy-{name}")
    monkeypatch.setenv("GIT_OPTIONAL_LOCKS", "1")
    captured = []

    def runner(command, **kwargs):
        captured.append((command, kwargs))
        stdout = (
            b" M tracked.txt\0" if "status" in command
            else b"tracked.txt\0untracked.txt\0"
        )
        return subprocess.CompletedProcess(
            command, 0, stdout=stdout, stderr=b"",
        )

    monkeypatch.setattr(repo_tree_util.subprocess, "run", runner)
    assert repo_tree_util._repo_status(Path("/real/repo")) == b" M tracked.txt\0"
    assert repo_tree_util.list_tracked_and_untracked_files(Path("/real/repo")) == (
        Path("tracked.txt"), Path("untracked.txt"),
    )
    assert len(captured) == 2
    environments = [kwargs["env"] for _, kwargs in captured]
    assert environments[0] == environments[1]
    assert environments[0]["GIT_OPTIONAL_LOCKS"] == "0"
    assert all(name not in environments[0] for name in forbidden)
    assert all(kwargs["check"] is True for _, kwargs in captured)
    assert all(kwargs["cwd"] == "/real/repo" for _, kwargs in captured)

@pytest.mark.parametrize(
    "relative_dest",
    [Path("protocol.json"), Path("nested/protocol.json")],
    ids=["top-level", "nested"],
)
def test_build_and_write_leave_repo_tree_unchanged(tmp_path, relative_dest):
    # 2 instance は top-level/nested writer の双方を踏むと同時に、real-repo 収集監査が
    # parameter suffix 単位で欠落を検出するための positive control になる。
    def action():
        built = _build_golden()
        fc.write_protocol_document(tmp_path / relative_dest, built, root=tmp_path)
        index = fc.scan_floor_protocol_index(root=ROOT)
        legacy_document = fc.validate_protocol(
            fc.load_protocol(ROOT / fc._FLOOR_PROTOCOL_REL),
        )
        legacy_pair = (
            legacy_document["contract_sha256"], legacy_document["ccbench_pin"],
        )
        assert legacy_pair in index
        assert index[legacy_pair].path == fc._FLOOR_PROTOCOL_REL
        assert index[legacy_pair].document == legacy_document
        assert len({pair[0] for pair in index}) == len(index)
        for pair, record in index.items():
            assert pair == (record.contract_sha256, record.ccbench_pin)
            assert fc.validate_protocol(record.document) == record.document
            assert hashlib.sha256(record.raw_bytes).hexdigest() == record.sha256
            if record.path != fc._FLOOR_PROTOCOL_REL:
                assert record.path == fc._derived_reseal_protocol_relpath(*pair)
        # 実 repo 凍結領域への書込みは拒否されること (副作用ゼロ) も併せて踏む。
        with pytest.raises(fc.FloorCampaignError):
            fc.write_protocol_document(
                ROOT / "output" / "s8b-freeze" / "nope.json", built)

    try:
        repo_tree_util.assert_repo_tree_unchanged(ROOT, action)
    except repo_tree_util.RepoTreeSnapshotError:
        skip("git status 実行不能")


def _snapshot_positive_control_repo(root: Path) -> tuple[Path, Path]:
    root.mkdir()
    subprocess.run(
        ["git", "init", "-q"], cwd=str(root),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    tracked = root / "tracked.txt"
    tracked.write_text("base\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "tracked.txt"], cwd=str(root),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    existing_untracked = root / "scratch" / "first.txt"
    existing_untracked.parent.mkdir()
    existing_untracked.write_text("first\n", encoding="utf-8")
    return tracked, existing_untracked


def test_repo_tree_unchanged_detector_positive_controls(tmp_path):
    # これは検出器の positive control であり、SUT の E2E 漏出注入ではない。
    # 各 action は独立した tmp git repo だけを変え、実 repo は汚さない。
    cases = (
        ("tracked-change", "tracked.txt",
         lambda tracked, _untracked: tracked.write_text("changed\n", encoding="utf-8")),
        ("new-untracked", "new.txt",
         lambda tracked, _untracked: (tracked.parent / "new.txt").write_text(
             "new\n", encoding="utf-8")),
        ("second-in-untracked-dir", "scratch/second.txt",
         lambda _tracked, untracked: (untracked.parent / "second.txt").write_text(
             "second\n", encoding="utf-8")),
        ("tracked-deletion", "tracked.txt",
         lambda tracked, _untracked: tracked.unlink()),
    )
    for label, expected_path, mutate in cases:
        repo = tmp_path / label
        tracked, existing_untracked = _snapshot_positive_control_repo(repo)
        try:
            repo_tree_util.assert_repo_tree_unchanged(
                repo, lambda: mutate(tracked, existing_untracked),
            )
        except AssertionError as exc:
            assert expected_path in str(exc), (
                f"{label}: 差分 path が失敗メッセージにない: {exc}"
            )
        else:
            raise AssertionError(f"{label}: repo tree 変化を検出しなかった")


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = skipped = 0
    for fn in fns:
        tmp = None
        try:
            kwargs = {}
            if "tmp_path" in inspect.signature(fn).parameters:
                tmp = tempfile.mkdtemp(prefix="izanagi_protobuilder_")
                kwargs["tmp_path"] = Path(tmp)
            if "relative_dest" in inspect.signature(fn).parameters:
                kwargs["relative_dest"] = Path("protocol.json")
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
