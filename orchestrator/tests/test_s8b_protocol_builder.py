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
import hashlib
import inspect
import json
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
# 実 repo tree 不変                                                             #
# --------------------------------------------------------------------------- #

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
