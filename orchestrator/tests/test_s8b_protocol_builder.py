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
from orchestrator.tests.growth_test_holds import enforce_held_functions  # noqa: E402
from orchestrator.tests.skiputil import Skip, skip  # noqa: E402

# 固定 golden 引数。env_tag は登録済み linux-baremetal、freeze/ccbench は実 repo を要求する。
_G_SEED = "golden-master-seed"
_G_ENV = "linux-baremetal"
_G_STOCK = "stock_common"
_G_EXTIME = 5
_G_FLOOR = 0.05

# 独立 golden (期待 canonical bytes/sha256 をテスト側に literal で保持)。
_T816_GOLDEN_BYTES = (
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
_T816_GOLDEN_SHA = "32e306c1e009adf03eabcbb314bb3542d7c76e892462213d759660c618e7dc4d"
_T816_APPROVED_SHA = "2c8cf9be929d83653814ecf5f2d5ed134a2af89686d796b8144da2fd45dfa58a"

# T-2304 builder output, independently recalculated and retained as literal bytes.
_GOLDEN_BYTES = (
    b'{"allowed_excluded_reasons":["competing_process","launch_failure",'
    b'"nonfinite_or_partial_output","performance_anomaly"],'
    b'"ccbench_pin":"e9e477ca1b55348ab4530de0b1cf663ce4555290",'
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
_GOLDEN_SHA = "481fdf8e1ead63ef485a231ea92f3b8ee25c2df63c03688d7689cf56aeb40e1b"


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
    assert built.sha256 == "62f1387dba4f191ec4545cf533671ece52532139237f275fa87351a0e9e812db"


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


def _init_reseal_protocol_repo(
        tmp_path: Path, *, name: str = "reseal-repo",
        include_ccbench_gitlink: bool = True,
) -> Path:
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
    if include_ccbench_gitlink:
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


def _commit_fixture_paths(repo: Path, *relative_paths: str, message: str) -> None:
    subprocess.run(
        ["git", "add", "--", *relative_paths], cwd=str(repo),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    subprocess.run(
        [
            "git", "-c", "user.name=Izanagi Test",
            "-c", "user.email=izanagi-test@example.invalid",
            "commit", "-qm", message,
        ],
        cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )


def _commit_versioned_protocol(repo: Path, *, pin: str) -> str:
    candidate = fc.validate_protocol(fc.load_protocol(repo / fc._FLOOR_PROTOCOL_REL))
    candidate["ccbench_pin"] = pin
    destination_rel = fc._derived_reseal_protocol_relpath(
        candidate["contract_sha256"], candidate["ccbench_pin"],
    )
    destination = repo / destination_rel
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(_canonical_protocol_bytes(candidate))
    _commit_fixture_paths(
        repo, destination_rel, message=f"commit protocol for {pin}",
    )
    return destination_rel


def _install_replacement_authority(
        repo: Path, *, ref_base: str = "refs/replace",
) -> tuple[dict, dict, str]:
    """表示上の HEAD OID を保ったまま別 anchor/gitlink を読ませる ref を置く。"""
    base_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(repo),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True,
    ).stdout.strip()
    base_anchor = fc.validate_protocol(fc.load_protocol(repo / fc._FLOOR_PROTOCOL_REL))
    poisoned_anchor = copy.deepcopy(base_anchor)
    poisoned_anchor["master_seed"] = "replacement-object-poison"
    (repo / fc._FLOOR_PROTOCOL_REL).write_bytes(
        _canonical_protocol_bytes(poisoned_anchor),
    )
    poisoned_pin = "d" * 40
    subprocess.run(
        ["git", "add", fc._FLOOR_PROTOCOL_REL], cwd=str(repo),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    subprocess.run(
        [
            "git", "update-index", "--add", "--cacheinfo",
            f"160000,{poisoned_pin},external/ccbench",
        ],
        cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    subprocess.run(
        [
            "git", "-c", "user.name=Izanagi Test",
            "-c", "user.email=izanagi-test@example.invalid",
            "commit", "-qm", "replacement authority",
        ],
        cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    replacement_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(repo),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True,
    ).stdout.strip()
    subprocess.run(
        ["git", "reset", "--hard", "-q", base_commit], cwd=str(repo),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    subprocess.run(
        ["git", "update-ref", f"{ref_base}/{base_commit}", replacement_commit],
        cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    return base_anchor, poisoned_anchor, poisoned_pin


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
        "sha256": "62f1387dba4f191ec4545cf533671ece52532139237f275fa87351a0e9e812db",
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
            _commit_fixture_paths(
                repo, rel, message=f"commit inherited field mutation {field}",
            )
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
            fc, "_head_commit_oid", wraps=fc._head_commit_oid,
    ) as head_mock, mock.patch.object(
            fc, "_ccbench_gitlink", wraps=fc._ccbench_gitlink,
    ) as gitlink_mock:
        outcome = fc.reseal_protocol()
    expected_rel = fc._derived_reseal_protocol_relpath(
        g2.contract_sha256, s8b_approved.CCBENCH_FULL_SHA,
    )
    assert outcome["status"] == "resealed"
    assert outcome["path"] == expected_rel
    assert lookup_mock.call_count == 1, "PID-cache authority の恒真な再照合を追加してはいけない"
    assert head_mock.call_count == 2, "publish 後に実際の HEAD 移動を検査する"
    assert all(call.args == (repo,) for call in head_mock.call_args_list)
    assert gitlink_mock.call_count == 1, "固定 commit の gitlink を恒真再読してはいけない"
    versioned = list((repo / fc._FLOOR_PROTOCOLS_REL).iterdir())
    assert versioned == [repo / expected_rel]
    assert hashlib.sha256(versioned[0].read_bytes()).hexdigest() == outcome["sha256"]


def test_reseal_protocol_public_entry_accepts_same_contract_with_new_pin(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path)
    g1 = ec.GENERATIONS["pegasus"][0].contract
    legacy = repo / fc._FLOOR_PROTOCOL_REL
    legacy_bytes = legacy.read_bytes()
    anchor = fc.validate_protocol(fc.load_protocol(legacy))
    assert anchor["contract_sha256"] == g1.contract_sha256
    assert anchor["ccbench_pin"] != s8b_approved.CCBENCH_FULL_SHA
    with mock.patch.object(fc, "ROOT", repo), mock.patch.object(
            fc._env_contract, "lookup", return_value=g1,
    ):
        outcome = fc.reseal_protocol()
    expected_pair = (g1.contract_sha256, s8b_approved.CCBENCH_FULL_SHA)
    expected_rel = fc._derived_reseal_protocol_relpath(*expected_pair)
    with pytest.raises(fc.FloorCampaignError, match="HEAD 固定 commit"):
        fc.scan_floor_protocol_index(root=repo)
    _commit_fixture_paths(repo, expected_rel, message="commit resealed protocol")
    index = fc.scan_floor_protocol_index(root=repo)
    assert outcome["status"] == "resealed"
    assert outcome["path"] == expected_rel
    assert set(index) == {
        (anchor["contract_sha256"], anchor["ccbench_pin"]),
        expected_pair,
    }
    assert index[expected_pair].path == expected_rel
    assert legacy.read_bytes() == legacy_bytes


def test_reseal_protocol_rejects_second_issue_for_same_pair_before_write(tmp_path):
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
        _commit_fixture_paths(repo, first["path"], message="commit first reseal")
        with mock.patch.object(
                fc, "_write_protocol_document_create_only",
                wraps=fc._write_protocol_document_create_only,
        ) as writer_mock:
            with pytest.raises(fc.FloorCampaignError, match="同一組") as exc_info:
                fc.reseal_protocol()
    writer_mock.assert_not_called()
    assert first["path"] in str(exc_info.value)
    assert "artifact=" not in str(exc_info.value)
    assert destination.read_bytes() == first_bytes


def test_reseal_protocol_rejects_pair_already_held_by_legacy_anchor(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path)
    legacy = repo / fc._FLOOR_PROTOCOL_REL
    anchor = fc.validate_protocol(fc.load_protocol(legacy))
    subprocess.run(
        [
            "git", "update-index", "--add", "--cacheinfo",
            f"160000,{anchor['ccbench_pin']},external/ccbench",
        ],
        cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    subprocess.run(
        [
            "git", "-c", "user.name=Izanagi Test",
            "-c", "user.email=izanagi-test@example.invalid",
            "commit", "-qm", "align fixture gitlink with legacy anchor",
        ],
        cwd=str(repo), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    current = ec.GENERATIONS["pegasus"][0].contract
    assert anchor["contract_sha256"] == current.contract_sha256
    with mock.patch.object(fc, "ROOT", repo), mock.patch.object(
            fc._env_contract, "lookup", return_value=current,
    ), mock.patch.object(
            fc, "_write_protocol_document_create_only",
            wraps=fc._write_protocol_document_create_only,
    ) as writer_mock:
        with pytest.raises(fc.FloorCampaignError, match="同一組") as exc_info:
            fc.reseal_protocol()
    writer_mock.assert_not_called()
    assert fc._FLOOR_PROTOCOL_REL in str(exc_info.value)
    assert "artifact=" not in str(exc_info.value)
    assert not (repo / fc._FLOOR_PROTOCOLS_REL).exists()


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
        with pytest.raises(fc.FloorCampaignError, match="HEAD commit が変化") as exc_info:
            fc.reseal_protocol()
    destination_rel = fc._derived_reseal_protocol_relpath(
        g2.contract_sha256, s8b_approved.CCBENCH_FULL_SHA,
    )
    destination = repo / destination_rel
    assert destination.is_file(), "publish 後の拒否でも artifact を自動削除してはいけない"
    message = str(exc_info.value)
    assert f"artifact={destination_rel}" in message
    assert "この file を取り除くまで" in message
    assert "commit してはならない" in message


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


def test_reseal_protocol_post_write_validation_accepts_uncommitted_output(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path)
    g2 = _pegasus_g2_contract()
    with mock.patch.object(fc, "ROOT", repo), mock.patch.object(
            fc._env_contract, "lookup", return_value=g2,
    ), mock.patch.object(
            fc, "_historical_protocol_contract",
            side_effect=_registered_protocol_contract,
    ), mock.patch.object(
            fc, "_scan_floor_protocol_index_at_commit",
            wraps=fc._scan_floor_protocol_index_at_commit,
    ) as scan_mock:
        outcome = fc.reseal_protocol()
    assert scan_mock.call_count == 1, "未 commit 出力を full index で再走査してはいけない"
    destination = repo / outcome["path"]
    assert destination.is_file()
    assert subprocess.run(
        ["git", "ls-files", "--error-unmatch", outcome["path"]], cwd=str(repo),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    ).returncode != 0


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


def test_reseal_git_environment_scrubs_replace_and_config_authority(monkeypatch):
    poisoned = {
        "GIT_REPLACE_REF_BASE": "refs/poisoned-replacements",
        "GIT_CONFIG": "/poisoned/config",
        "GIT_CONFIG_PARAMETERS": "'core.useReplaceRefs=true'",
        "GIT_CONFIG_COUNT": "2",
        "GIT_CONFIG_KEY_0": "core.useReplaceRefs",
        "GIT_CONFIG_VALUE_0": "true",
        "GIT_CONFIG_KEY_17": "alias.rev-parse",
        "GIT_CONFIG_VALUE_17": "!false",
        "GIT_NAMESPACE": "poisoned",
        "GIT_GRAFT_FILE": "/poisoned/grafts",
        "GIT_SHALLOW_FILE": "/poisoned/shallow",
        "GIT_NO_REPLACE_OBJECTS": "0",
    }
    for name, value in poisoned.items():
        monkeypatch.setenv(name, value)

    sanitized = fc._sanitized_floor_git_env()

    assert sanitized["GIT_NO_REPLACE_OBJECTS"] == "1"
    assert all(name not in sanitized for name in fc._FLOOR_GIT_AUTHORITY_ENV)
    assert not any(
        fc._FLOOR_GIT_CONFIG_ENTRY_RE.fullmatch(name) for name in sanitized
    )


def test_reseal_protocol_ignores_repository_replacement_ref(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path, name="replacement-ref-repo")
    base_anchor, poisoned_anchor, poisoned_pin = _install_replacement_authority(repo)
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
    assert outcome["ccbench_pin"] != poisoned_pin
    assert issued["master_seed"] == base_anchor["master_seed"]
    assert issued["master_seed"] != poisoned_anchor["master_seed"]


def test_reseal_protocol_scrubs_git_config_count_injection(tmp_path, monkeypatch):
    repo = _init_reseal_protocol_repo(tmp_path, name="config-injection-repo")
    custom_base = "refs/config-injected-replacements"
    base_anchor, poisoned_anchor, poisoned_pin = _install_replacement_authority(
        repo, ref_base=custom_base,
    )
    monkeypatch.setenv("GIT_REPLACE_REF_BASE", custom_base)
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.useReplaceRefs")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "true")
    monkeypatch.setenv("GIT_NO_REPLACE_OBJECTS", "0")
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
    assert outcome["ccbench_pin"] != poisoned_pin
    assert issued["master_seed"] == base_anchor["master_seed"]
    assert issued["master_seed"] != poisoned_anchor["master_seed"]


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
    duplicate_rel = duplicate.relative_to(repo).as_posix()
    _commit_fixture_paths(repo, duplicate_rel, message="commit duplicate pair")
    with pytest.raises(fc.FloorCampaignError, match="同一組"):
        fc.scan_floor_protocol_index(root=repo)


def _resolver_record(*, contract, pin: str, label: str) -> fc.IndexedFloorProtocol:
    raw = label.encode("ascii")
    return fc.IndexedFloorProtocol(
        path=fc._derived_reseal_protocol_relpath(contract.contract_sha256, pin),
        document={
            "env_tag": contract.env_tag,
            "contract_sha256": contract.contract_sha256,
            "ccbench_pin": pin,
        },
        raw_bytes=raw,
        sha256=hashlib.sha256(raw).hexdigest(),
        commit_oid="c" * 40,
    )


def _resolver_index(*records: fc.IndexedFloorProtocol):
    return {
        (record.contract_sha256, record.ccbench_pin): record
        for record in records
    }


def test_current_floor_protocol_resolver_selects_exact_index_record():
    current = ec.GENERATIONS["pegasus"][0].contract
    head_pin = "a" * 40
    fallback = _resolver_record(contract=current, pin="b" * 40, label="fallback")
    exact = _resolver_record(contract=current, pin=head_pin, label="exact")
    with mock.patch.object(
            fc, "_head_commit_oid", return_value="c" * 40,
    ), mock.patch.object(
            fc, "_scan_floor_protocol_index_at_commit",
            return_value=_resolver_index(fallback, exact),
    ), mock.patch.object(
            fc, "_ccbench_gitlink", return_value=head_pin,
    ), mock.patch.object(fc._env_contract, "lookup", return_value=current):
        resolved = fc.resolve_current_floor_protocol(root=ROOT)
    assert resolved is exact


def test_current_floor_protocol_resolver_falls_back_to_one_current_candidate():
    current = ec.GENERATIONS["pegasus"][0].contract
    fallback = _resolver_record(contract=current, pin="b" * 40, label="fallback")
    with mock.patch.object(
            fc, "_head_commit_oid", return_value="c" * 40,
    ), mock.patch.object(
            fc, "_scan_floor_protocol_index_at_commit",
            return_value=_resolver_index(fallback),
    ), mock.patch.object(
            fc, "_ccbench_gitlink", return_value="a" * 40,
    ) as gitlink_mock, mock.patch.object(
            fc._env_contract, "lookup", return_value=current,
    ):
        resolved = fc.resolve_current_floor_protocol(root=ROOT)
    assert resolved is fallback
    gitlink_mock.assert_not_called()


def test_current_floor_protocol_resolver_without_gitlink_accepts_one_candidate(tmp_path):
    repo = _init_reseal_protocol_repo(
        tmp_path, name="one-candidate-no-gitlink", include_ccbench_gitlink=False,
    )
    with mock.patch.object(
            fc, "_ccbench_gitlink", wraps=fc._ccbench_gitlink,
    ) as gitlink_mock:
        resolved = fc.resolve_current_floor_protocol(root=repo)
    assert resolved.path == fc._FLOOR_PROTOCOL_REL
    gitlink_mock.assert_not_called()


def test_current_floor_protocol_resolver_without_gitlink_rejects_two_candidates(tmp_path):
    repo = _init_reseal_protocol_repo(
        tmp_path, name="two-candidates-no-gitlink", include_ccbench_gitlink=False,
    )
    _commit_versioned_protocol(repo, pin="a" * 40)
    with pytest.raises(fc.FloorCampaignError, match="gitlink \\(submodule\\) でない"):
        fc.resolve_current_floor_protocol(root=repo)


def test_current_floor_protocol_resolver_with_gitlink_prefers_head_exact(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path, name="two-candidates-with-gitlink")
    exact_rel = _commit_versioned_protocol(
        repo, pin=s8b_approved.CCBENCH_FULL_SHA,
    )
    resolved = fc.resolve_current_floor_protocol(root=repo)
    assert resolved.path == exact_rel
    assert resolved.ccbench_pin == s8b_approved.CCBENCH_FULL_SHA


def test_current_floor_protocol_resolver_uses_one_head_oid_for_index_and_gitlink():
    current = ec.GENERATIONS["pegasus"][0].contract
    head_commit = "c" * 40
    fallback = _resolver_record(contract=current, pin="b" * 40, label="fallback")
    exact = _resolver_record(contract=current, pin="a" * 40, label="exact")
    with mock.patch.object(
            fc, "_head_commit_oid", return_value=head_commit,
    ) as head_mock, mock.patch.object(
            fc, "_scan_floor_protocol_index_at_commit",
            return_value=_resolver_index(fallback, exact),
    ) as scan_mock, mock.patch.object(
            fc, "_ccbench_gitlink", return_value="a" * 40,
    ) as gitlink_mock, mock.patch.object(
            fc._env_contract, "lookup", return_value=current,
    ):
        fc.resolve_current_floor_protocol(root=ROOT)
    head_mock.assert_called_once_with(ROOT)
    scan_mock.assert_called_once_with(root=ROOT, commit_oid=head_commit)
    gitlink_mock.assert_called_once_with(ROOT, head_commit)


def test_current_floor_protocol_resolver_returns_index_commit_oid(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path, name="resolver-commit-oid")
    expected_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(repo), check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()

    resolved = fc.resolve_current_floor_protocol(root=repo)

    assert resolved.commit_oid == expected_commit


def test_current_floor_protocol_resolver_has_only_root_selection_argument():
    parameters = inspect.signature(fc.resolve_current_floor_protocol).parameters
    assert tuple(parameters) == ("root",)
    assert parameters["root"].kind is inspect.Parameter.KEYWORD_ONLY


def test_current_floor_protocol_resolver_rejects_zero_current_matches():
    current = ec.GENERATIONS["pegasus"][0].contract
    stale = mock.Mock(env_tag=current.env_tag, contract_sha256="0" * 64)
    record = _resolver_record(contract=stale, pin="1" * 40, label="stale")
    with mock.patch.object(
            fc, "_head_commit_oid", return_value="c" * 40,
    ), mock.patch.object(
            fc, "_scan_floor_protocol_index_at_commit",
            return_value=_resolver_index(record),
    ), mock.patch.object(
            fc, "_ccbench_gitlink", return_value="2" * 40,
    ) as gitlink_mock, mock.patch.object(
            fc._env_contract, "lookup", return_value=current,
    ):
        with pytest.raises(
                fc.FloorCampaignError,
                match="current_count=0 head_exact_count=0",
        ):
            fc.resolve_current_floor_protocol(root=ROOT)
    gitlink_mock.assert_not_called()


def test_current_floor_protocol_resolver_rejects_two_current_contract_matches():
    current = ec.GENERATIONS["pegasus"][0].contract
    records = (
        _resolver_record(contract=current, pin="1" * 40, label="first"),
        _resolver_record(contract=current, pin="2" * 40, label="second"),
    )
    with mock.patch.object(
            fc, "_head_commit_oid", return_value="c" * 40,
    ), mock.patch.object(
            fc, "_scan_floor_protocol_index_at_commit",
            return_value=_resolver_index(*records),
    ), mock.patch.object(
            fc, "_ccbench_gitlink", return_value="3" * 40,
    ), mock.patch.object(fc._env_contract, "lookup", return_value=current):
        with pytest.raises(
                fc.FloorCampaignError,
                match="current_count=2 head_exact_count=0",
        ):
            fc.resolve_current_floor_protocol(root=ROOT)


def test_current_floor_protocol_resolver_does_not_select_stale_head_exact():
    current = ec.GENERATIONS["pegasus"][0].contract
    stale = mock.Mock(env_tag=current.env_tag, contract_sha256="0" * 64)
    head_pin = "a" * 40
    stale_exact = _resolver_record(contract=stale, pin=head_pin, label="stale")
    fallback = _resolver_record(contract=current, pin="b" * 40, label="current")
    current_exact = _resolver_record(
        contract=current, pin=head_pin, label="current-exact",
    )
    with mock.patch.object(
            fc, "_head_commit_oid", return_value="c" * 40,
    ), mock.patch.object(
            fc, "_scan_floor_protocol_index_at_commit",
            return_value=_resolver_index(stale_exact, fallback, current_exact),
    ), mock.patch.object(
            fc, "_ccbench_gitlink", return_value=head_pin,
    ), mock.patch.object(fc._env_contract, "lookup", return_value=current):
        resolved = fc.resolve_current_floor_protocol(root=ROOT)
    assert resolved is current_exact


def test_floor_protocol_historical_anchors_remain_legacy():
    assignments = {
        "orchestrator/campaign/s8b_holdout_freeze.py": (
            r'^FLOOR_PROTOCOL_REL = "([^"]+)"$',
        ),
        "orchestrator/campaign/s8b_prediction_runner.py": (
            r'^_PROTOCOL_PATH = Path\("([^"]+)"\)$',
        ),
        "orchestrator/campaign/s8b_ratified_freeze.py": (
            r'^_SELECTOR_PROTOCOL_PATH = "([^"]+)"$',
        ),
    }
    observed = {}
    for relative, (pattern,) in assignments.items():
        source = (ROOT / relative).read_text(encoding="utf-8")
        matches = re.findall(pattern, source, flags=re.MULTILINE)
        assert len(matches) == 1, f"{relative}: protocol path assignment が exact 1 件でない"
        observed[relative] = matches[0]
    assert set(observed) == set(assignments)
    assert fc._FLOOR_PROTOCOL_REL == "output/s8b-freeze/floor_protocol.json"
    assert set(observed.values()) == {fc._FLOOR_PROTOCOL_REL}


def test_floor_protocol_index_rejects_uncommitted_versioned_entry(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path)
    candidate = fc.validate_protocol(fc.load_protocol(repo / fc._FLOOR_PROTOCOL_REL))
    candidate["ccbench_pin"] = "a" * 40
    destination = repo / fc._derived_reseal_protocol_relpath(
        candidate["contract_sha256"], candidate["ccbench_pin"],
    )
    destination.parent.mkdir(parents=True)
    destination.write_bytes(_canonical_protocol_bytes(candidate))
    with pytest.raises(fc.FloorCampaignError, match="HEAD 固定 commit"):
        fc.scan_floor_protocol_index(root=repo)


def test_floor_protocol_index_accepts_committed_versioned_entry(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path)
    candidate = fc.validate_protocol(fc.load_protocol(repo / fc._FLOOR_PROTOCOL_REL))
    candidate["ccbench_pin"] = "a" * 40
    destination_rel = fc._derived_reseal_protocol_relpath(
        candidate["contract_sha256"], candidate["ccbench_pin"],
    )
    destination = repo / destination_rel
    destination.parent.mkdir(parents=True)
    destination.write_bytes(_canonical_protocol_bytes(candidate))
    _commit_fixture_paths(repo, destination_rel, message="commit versioned protocol")
    index = fc.scan_floor_protocol_index(root=repo)
    anchor_pair = (
        candidate["contract_sha256"],
        fc.load_protocol(repo / fc._FLOOR_PROTOCOL_REL)["ccbench_pin"],
    )
    candidate_pair = (candidate["contract_sha256"], candidate["ccbench_pin"])
    assert set(index) == {anchor_pair, candidate_pair}
    assert index[anchor_pair].path == fc._FLOOR_PROTOCOL_REL
    assert index[candidate_pair].path == destination.relative_to(repo).as_posix()


def test_floor_protocol_index_rejects_dirty_versioned_entry(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path)
    candidate = fc.validate_protocol(fc.load_protocol(repo / fc._FLOOR_PROTOCOL_REL))
    candidate["ccbench_pin"] = "a" * 40
    destination_rel = fc._derived_reseal_protocol_relpath(
        candidate["contract_sha256"], candidate["ccbench_pin"],
    )
    destination = repo / destination_rel
    destination.parent.mkdir(parents=True)
    destination.write_bytes(_canonical_protocol_bytes(candidate))
    _commit_fixture_paths(repo, destination_rel, message="commit versioned protocol")
    destination.write_bytes(destination.read_bytes() + b"\n")
    with pytest.raises(fc.FloorCampaignError, match="working tree bytes"):
        fc.scan_floor_protocol_index(root=repo)


def test_floor_protocol_index_rejects_deleted_committed_versioned_entry(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path)
    candidate = fc.validate_protocol(fc.load_protocol(repo / fc._FLOOR_PROTOCOL_REL))
    candidate["ccbench_pin"] = "a" * 40
    destination_rel = fc._derived_reseal_protocol_relpath(
        candidate["contract_sha256"], candidate["ccbench_pin"],
    )
    destination = repo / destination_rel
    destination.parent.mkdir(parents=True)
    destination.write_bytes(_canonical_protocol_bytes(candidate))
    _commit_fixture_paths(repo, destination_rel, message="commit versioned protocol")
    destination.unlink()
    with pytest.raises(fc.FloorCampaignError, match="HEAD 固定 commit と不一致"):
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


def test_reseal_protocol_rechecks_ancestor_symlink_immediately_before_write(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path, name="pre-write-symlink-swap")
    g2 = _pegasus_g2_contract()
    destination_rel = fc._derived_reseal_protocol_relpath(
        g2.contract_sha256, s8b_approved.CCBENCH_FULL_SHA,
    )
    freeze_dir = repo / "output/s8b-freeze"
    outside_freeze = tmp_path / "outside-freeze"
    original_check = fc._assert_floor_protocol_ancestors
    check_count = 0

    def swap_before_second_check(root):
        nonlocal check_count
        check_count += 1
        if check_count == 2:
            shutil.move(str(freeze_dir), str(outside_freeze))
            freeze_dir.symlink_to(outside_freeze, target_is_directory=True)
        return original_check(root)

    with mock.patch.object(fc, "ROOT", repo), mock.patch.object(
            fc._env_contract, "lookup", return_value=g2,
    ), mock.patch.object(
            fc, "_historical_protocol_contract",
            side_effect=_registered_protocol_contract,
    ), mock.patch.object(
            fc, "_assert_floor_protocol_ancestors",
            side_effect=swap_before_second_check,
    ):
        with pytest.raises(fc.FloorCampaignError, match="親が symlink"):
            fc.reseal_protocol()

    assert check_count == 2
    assert not (outside_freeze / Path(destination_rel).relative_to(
        "output/s8b-freeze"
    )).exists(), "祖先差し替え時に repository 外へ artifact を作ってはいけない"


def test_reseal_protocol_rejects_destination_realpath_outside_repo_after_write(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path, name="post-write-realpath-swap")
    g2 = _pegasus_g2_contract()
    destination_rel = fc._derived_reseal_protocol_relpath(
        g2.contract_sha256, s8b_approved.CCBENCH_FULL_SHA,
    )
    freeze_dir = repo / "output/s8b-freeze"
    outside_freeze = tmp_path / "outside-after-precheck"
    outside_destination = outside_freeze / Path(destination_rel).relative_to(
        "output/s8b-freeze"
    )
    original_writer = fc._write_protocol_document_create_only

    def swap_inside_writer(destination, built):
        shutil.move(str(freeze_dir), str(outside_freeze))
        freeze_dir.symlink_to(outside_freeze, target_is_directory=True)
        return original_writer(destination, built)

    with mock.patch.object(fc, "ROOT", repo), mock.patch.object(
            fc._env_contract, "lookup", return_value=g2,
    ), mock.patch.object(
            fc, "_historical_protocol_contract",
            side_effect=_registered_protocol_contract,
    ), mock.patch.object(
            fc, "_write_protocol_document_create_only",
            side_effect=swap_inside_writer,
    ):
        with pytest.raises(
                fc.FloorCampaignError, match="destination realpath が repository 外",
        ) as exc_info:
            fc.reseal_protocol()

    assert outside_destination.is_file(), "失敗した発行 artifact は自動削除しない"
    assert f"artifact={destination_rel}" in str(exc_info.value)


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
    versioned = copy.deepcopy(pinned_anchor)
    versioned["ccbench_pin"] = "a" * 40
    versioned_rel = fc._derived_reseal_protocol_relpath(
        versioned["contract_sha256"], versioned["ccbench_pin"],
    )
    versioned_path = repo / versioned_rel
    versioned_path.parent.mkdir(parents=True)
    versioned_path.write_bytes(_canonical_protocol_bytes(versioned))
    subprocess.run(
        ["git", "add", fc._FLOOR_PROTOCOL_REL, versioned_rel], cwd=str(repo),
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
        observed = (
            [command[0], *command[2:]]
            if command[:2] == ["git", "--no-replace-objects"]
            else command
        )
        commands.append(tuple(observed))
        completed = original_run(command, **kwargs)
        if (not moved and observed[:3] == ["git", "ls-tree", "-z"]
                and observed[3] == pinned_commit):
            original_run(
                ["git", "reset", "--soft", "-q", old_commit], cwd=str(repo),
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
    assert index[(versioned["contract_sha256"], versioned["ccbench_pin"])].path == versioned_rel
    assert any(command[:4] == ("git", "ls-tree", "-z", pinned_commit)
               for command in commands)
    assert any(
        command[:6] == (
            "git", "ls-tree", "-r", "-z", "--name-only", pinned_commit,
        )
        for command in commands
    )
    cat_file = [command for command in commands if command[:3] == ("git", "cat-file", "blob")]
    assert len(cat_file) == 2
    assert all(command[3] != f"HEAD:{fc._FLOOR_PROTOCOL_REL}" for command in cat_file)


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
    _commit_fixture_paths(repo, wrong_rel, message="commit misderived protocol path")
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
        _commit_fixture_paths(repo, rel, message=f"commit {case} protocol")
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


def test_floor_protocol_index_requires_versioned_head_100644_blob(tmp_path):
    repo = _init_reseal_protocol_repo(tmp_path, name="executable-versioned")
    candidate = fc.validate_protocol(fc.load_protocol(repo / fc._FLOOR_PROTOCOL_REL))
    candidate["ccbench_pin"] = "a" * 40
    rel = fc._derived_reseal_protocol_relpath(
        candidate["contract_sha256"], candidate["ccbench_pin"],
    )
    destination = repo / rel
    destination.parent.mkdir(parents=True)
    destination.write_bytes(_canonical_protocol_bytes(candidate))
    destination.chmod(0o755)
    _commit_fixture_paths(repo, rel, message="commit executable versioned protocol")
    with pytest.raises(fc.FloorCampaignError, match="100644 blob"):
        fc.scan_floor_protocol_index(root=repo)


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


def test_resolve_current_protocol_cli_has_no_caller_arguments():
    for option in ("--path", "--contract-sha256", "--ccbench-pin", "--root"):
        with pytest.raises(SystemExit) as exc_info:
            fc.main(["resolve-current-protocol", option, "attacker-selected"])
        assert exc_info.value.code == 2


def test_resolve_current_protocol_cli_prints_one_relative_path_line():
    current = ec.GENERATIONS["pegasus"][0].contract
    record = _resolver_record(contract=current, pin="a" * 40, label="resolved")
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream), mock.patch.object(
            fc, "resolve_current_floor_protocol", return_value=record,
    ) as resolver_mock:
        assert fc.main(["resolve-current-protocol"]) == 0
    resolver_mock.assert_called_once_with(root=fc.ROOT)
    assert stream.getvalue() == f"{record.path}\n"
    assert not Path(record.path).is_absolute()


def test_resolve_current_protocol_cli_returns_nonzero_on_resolution_failure():
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream), mock.patch.object(
            fc, "resolve_current_floor_protocol",
            side_effect=fc.FloorCampaignError("fixture ambiguity"),
    ):
        assert fc.main(["resolve-current-protocol"]) == 1
    payload = json.loads(stream.getvalue())
    assert payload["status"] == "error"
    assert "fixture ambiguity" in payload["error"]


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
        committed_legacy_raw = subprocess.run(
            [
                "git", "--no-replace-objects", "show",
                f"HEAD:{fc._FLOOR_PROTOCOL_REL}",
            ],
            cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=True, env=fc._sanitized_floor_git_env(),
        ).stdout
        committed_legacy_document = fc.validate_protocol(
            json.loads(committed_legacy_raw.decode("utf-8")),
        )
        legacy_pair = (
            committed_legacy_document["contract_sha256"],
            committed_legacy_document["ccbench_pin"],
        )
        assert legacy_pair in index
        assert index[legacy_pair].path == fc._FLOOR_PROTOCOL_REL
        namespace_prefix = f"{fc._FLOOR_PROTOCOLS_REL}/"
        for record in index.values():
            if record.path != fc._FLOOR_PROTOCOL_REL:
                assert record.path.startswith(namespace_prefix)
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


enforce_held_functions(globals(), __file__, plain_runner="manual")


if __name__ == "__main__":
    sys.exit(_run())
