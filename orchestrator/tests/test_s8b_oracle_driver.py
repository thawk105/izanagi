# -*- coding: utf-8 -*-
"""8b oracle driver の gate、binding、budget、WAL 契約を検査する。"""
from __future__ import annotations

from orchestrator.tests.s8b_v2_freeze_fixture import in_sealed_fixture_process

import ast
import atexit
import contextlib
import copy
import dataclasses
import errno
import functools
import hashlib
import importlib
import inspect
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

ORCHESTRATOR = Path(__file__).resolve().parents[1]
ROOT = ORCHESTRATOR.parent


def _assert_t080_temp_root_outside_real_output(temp_root: Path) -> Path:
    """T-080 E2E の一時 root が実 repo の output/ を汚さないことを固定する。"""
    resolved = Path(temp_root).resolve()
    real_output = (ROOT / "output").resolve()
    if resolved == real_output or resolved.is_relative_to(real_output):
        raise AssertionError(
            "T-080 E2E temp root は実 repo の output/ 配下に置けない: "
            f"{resolved}"
        )
    return resolved


def _assert_t080_import_temp_environment() -> Path:
    """tempfile の書込可否 probe より前に ambient temp path を検査する。"""
    for name in ("TMPDIR", "TEMP", "TMP"):
        value = os.environ.get(name)
        if value:
            _assert_t080_temp_root_outside_real_output(Path(value))
    return _assert_t080_temp_root_outside_real_output(Path(tempfile.gettempdir()))


# pytest が tmp_path / basetemp を作るより前の module import 境界で拒否する。
_T080_IMPORT_TEMP_ROOT = _assert_t080_import_temp_environment()

sys.path.insert(0, str(ORCHESTRATOR.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import real_repo_ratified_memo as ratified_memo  # noqa: E402
from orchestrator.tests import real_repo_receipt_memo as receipt_memo  # noqa: E402
import s8b_oracle_spec_fixture as spec_fixture  # noqa: E402
import s8b_v2_freeze_fixture as v2_fixture  # noqa: E402
import test_s1_direct_comparison as s1_condition_fixtures  # noqa: E402
import test_s8b_ratified_freeze as ratified_fixture  # noqa: E402
from orchestrator.campaign import env_contract as ec  # noqa: E402
from orchestrator.campaign.build_admission import (  # noqa: E402
    BuildRunContext,
    GeneratorId,
    ReviewId,
    ReviewReceipt,
    build_run_context,
)
from orchestrator.campaign import env_attestation  # noqa: E402
from orchestrator.campaign import artifact_admission  # noqa: E402
from orchestrator.campaign import execution_guard  # noqa: E402
from orchestrator.campaign import (model, pipeline, s8b_budget,  # noqa: E402
                                   s8b_oracle_driver as driver, wal)
from orchestrator.campaign import s8b_oracle_artifacts as oracle_artifacts  # noqa: E402
from orchestrator.campaign import s8b_freeze_io  # noqa: E402
from orchestrator.campaign import s8b_materialization  # noqa: E402
from orchestrator.campaign import s8b_oracle_manifest as manifest_module  # noqa: E402
from orchestrator.campaign import s8b_oracle_spec as oracle_spec  # noqa: E402
from orchestrator.campaign import s8b_oracle_report as report_module  # noqa: E402
from orchestrator.campaign import s8b_oracle_judge as judge_module  # noqa: E402
from orchestrator.campaign import s8b_holdout_freeze  # noqa: E402
from orchestrator.campaign import s8b_ratified_freeze  # noqa: E402
from orchestrator.campaign import s8b_run_marker  # noqa: E402
from orchestrator.campaign import t080_freeze_migration as migration  # noqa: E402
from orchestrator.campaign.layout import campaign_layout  # noqa: E402
from orchestrator.campaign.model import Genome  # noqa: E402
from orchestrator.campaign.s1_direct_comparison import PreparedCell  # noqa: E402
from orchestrator.campaign.source_digest import SourceEvidence  # noqa: E402
from orchestrator.tests import commit_receipt_support as receipt_support  # noqa: E402
from orchestrator.tests.output_snapshot_ignores import (  # noqa: E402
    _check_rule_candidates,
    git_ignored_output_ancestor_directories,
    git_ignored_output_prefixes,
    git_ignored_output_snapshot_rules,
    git_visible_output_metadata_snapshot,
    is_git_ignored_output_path,
)

from test_schema_v2 import _valid_document as _valid_calibration_v2  # noqa: E402


REAL_FREEZE = ROOT / "output/s8b-freeze/holdout_freeze.json"
CONFIGURATIONS = (
    "p2_2_flag_opt", "backoff_fixed_best", "sort_best",
    "system_gate", "ident_all", "stock_common",
)
# driver v2 実走 fixture の none-attestation env (env_contract registry の登録値)。
V2_ENV_TAG = "linux-baremetal"
GENERATOR_SOURCES = {
    "materializer": "orchestrator/campaign/s1_direct_comparison.py",
    "report": "orchestrator/campaign/s8b_oracle_report.py",
    "judge": "orchestrator/campaign/s8b_oracle_judge.py",
    "outcome_stage_contract": (
        "orchestrator/campaign/s8b_outcome_stage_contract.py"
    ),
    "artifacts": "orchestrator/campaign/s8b_oracle_artifacts.py",
}
_NO_ACTIVE_REFUSAL = (
    "freeze-ratify: [no-active] [no-active] live active pointer が無い "
    "(v2 未発効)"
)
_APPROVED_BY_PATH: dict[Path, spec_fixture.ReviewedSpecFixture] = {}
_ACTIVE_APPROVED: spec_fixture.ReviewedSpecFixture | None = None


@pytest.fixture(autouse=True)
def _approved_spec_loader(monkeypatch):
    """driver test の直前に組み立てた explicit spec snapshot を production へ渡す。"""
    global _ACTIVE_APPROVED
    _ACTIVE_APPROVED = None

    def load_approved_spec(_root):
        if _ACTIVE_APPROVED is None:
            raise oracle_spec.ReviewedSpecError("no-approved-spec")
        monkeypatch.setattr(
            oracle_spec, "APPROVED_SPEC_SHA256", _ACTIVE_APPROVED.sha256,
        )
        return _ACTIVE_APPROVED.reviewed_spec

    monkeypatch.setattr(
        driver.s8b_oracle_spec, "load_approved_spec", load_approved_spec,
    )

_T080_SOURCE_GOLDEN = (
    ("known_axes", "/entries/balanced/ident_all/sources/3/sha256", "3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1"),
    ("known_axes", "/entries/balanced/sort_best/sources/5/sha256", "0c7dcd30caf7a1e6bd97273c9273ae808516a5cdea5ce004b060edfaa29888a2"),
    ("known_axes", "/entries/balanced/sort_best/sources/6/sha256", "9b64f34bac3711f2384fd89e8d387e2e9d736af6e2d7c9b246c059b52267dbf4"),
    ("known_axes", "/entries/balanced/system_gate/sources/4/sha256", "3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1"),
    ("known_axes", "/entries/read-heavy/ident_all/sources/3/sha256", "3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1"),
    ("known_axes", "/entries/read-heavy/sort_best/sources/2/sha256", "0c7dcd30caf7a1e6bd97273c9273ae808516a5cdea5ce004b060edfaa29888a2"),
    ("known_axes", "/entries/read-heavy/sort_best/sources/3/sha256", "9b64f34bac3711f2384fd89e8d387e2e9d736af6e2d7c9b246c059b52267dbf4"),
    ("known_axes", "/entries/read-heavy/system_gate/sources/4/sha256", "3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1"),
    ("known_axes", "/entries/write-heavy/ident_all/sources/3/sha256", "3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1"),
    ("known_axes", "/entries/write-heavy/sort_best/sources/5/sha256", "0c7dcd30caf7a1e6bd97273c9273ae808516a5cdea5ce004b060edfaa29888a2"),
    ("known_axes", "/entries/write-heavy/sort_best/sources/6/sha256", "9b64f34bac3711f2384fd89e8d387e2e9d736af6e2d7c9b246c059b52267dbf4"),
    ("known_axes", "/entries/write-heavy/system_gate/sources/4/sha256", "3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1"),
    ("holdout", "/design_source/sha256", "1829af7fec4140fedaceae7c35ed5349e6d478e9d688de77a70f3be845a4a27d"),
)
_T080_METADATA_GOLDEN = (
    ("known_axes", "/generator/sha256", "1d4d45a3de4926c6aae76906f7b4b72d3fead51e9cdf62ff03f80a0379c364e0"),
    ("holdout", "/generator/sha256", "1910fff38edf0e58f5bff221c29660a8f85dd0ed1b5c980234ec1af098584e5f"),
)
_T080_REAL_REPO_SOURCE_GOLDEN = (
    (
        "known_axes", "/entries/balanced/ident_all/sources/3/sha256",
        "3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1",
        "orchestrator/campaign/s8a_trigger_sweep.py",
        "8c3abd486b0b280c4e7ea6938147360fdacd1454d3eadb84ae1d663c9f395311",
    ),
    (
        "known_axes", "/entries/balanced/sort_best/sources/5/sha256",
        "0c7dcd30caf7a1e6bd97273c9273ae808516a5cdea5ce004b060edfaa29888a2",
        "orchestrator/campaign/s6_sort_sweep.py",
        "28270e905785c787f1eb74cebcf34f8feb98e1e7cec738dee14611c9ab3dad1a",
    ),
    (
        "known_axes", "/entries/balanced/sort_best/sources/6/sha256",
        "9b64f34bac3711f2384fd89e8d387e2e9d736af6e2d7c9b246c059b52267dbf4",
        "orchestrator/campaign/p3_s4_loop_sort.py",
        "0e716a6cda268e3d158774c344d002a8daf49fa7dd4ab9bbb1bb5c9e0d30d8b0",
    ),
    (
        "known_axes", "/entries/balanced/system_gate/sources/4/sha256",
        "3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1",
        "orchestrator/campaign/s8a_trigger_sweep.py",
        "8c3abd486b0b280c4e7ea6938147360fdacd1454d3eadb84ae1d663c9f395311",
    ),
    (
        "known_axes", "/entries/read-heavy/ident_all/sources/3/sha256",
        "3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1",
        "orchestrator/campaign/s8a_trigger_sweep.py",
        "8c3abd486b0b280c4e7ea6938147360fdacd1454d3eadb84ae1d663c9f395311",
    ),
    (
        "known_axes", "/entries/read-heavy/sort_best/sources/2/sha256",
        "0c7dcd30caf7a1e6bd97273c9273ae808516a5cdea5ce004b060edfaa29888a2",
        "orchestrator/campaign/s6_sort_sweep.py",
        "28270e905785c787f1eb74cebcf34f8feb98e1e7cec738dee14611c9ab3dad1a",
    ),
    (
        "known_axes", "/entries/read-heavy/sort_best/sources/3/sha256",
        "9b64f34bac3711f2384fd89e8d387e2e9d736af6e2d7c9b246c059b52267dbf4",
        "orchestrator/campaign/p3_s4_loop_sort.py",
        "0e716a6cda268e3d158774c344d002a8daf49fa7dd4ab9bbb1bb5c9e0d30d8b0",
    ),
    (
        "known_axes", "/entries/read-heavy/system_gate/sources/4/sha256",
        "3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1",
        "orchestrator/campaign/s8a_trigger_sweep.py",
        "8c3abd486b0b280c4e7ea6938147360fdacd1454d3eadb84ae1d663c9f395311",
    ),
    (
        "known_axes", "/entries/write-heavy/ident_all/sources/3/sha256",
        "3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1",
        "orchestrator/campaign/s8a_trigger_sweep.py",
        "8c3abd486b0b280c4e7ea6938147360fdacd1454d3eadb84ae1d663c9f395311",
    ),
    (
        "known_axes", "/entries/write-heavy/sort_best/sources/5/sha256",
        "0c7dcd30caf7a1e6bd97273c9273ae808516a5cdea5ce004b060edfaa29888a2",
        "orchestrator/campaign/s6_sort_sweep.py",
        "28270e905785c787f1eb74cebcf34f8feb98e1e7cec738dee14611c9ab3dad1a",
    ),
    (
        "known_axes", "/entries/write-heavy/sort_best/sources/6/sha256",
        "9b64f34bac3711f2384fd89e8d387e2e9d736af6e2d7c9b246c059b52267dbf4",
        "orchestrator/campaign/p3_s4_loop_sort.py",
        "0e716a6cda268e3d158774c344d002a8daf49fa7dd4ab9bbb1bb5c9e0d30d8b0",
    ),
    (
        "known_axes", "/entries/write-heavy/system_gate/sources/4/sha256",
        "3e94735a974fa494b12691e418f0b593ee2ac22dba4e67fb0f8874523d2175a1",
        "orchestrator/campaign/s8a_trigger_sweep.py",
        "8c3abd486b0b280c4e7ea6938147360fdacd1454d3eadb84ae1d663c9f395311",
    ),
    (
        "holdout", "/design_source/sha256",
        "1829af7fec4140fedaceae7c35ed5349e6d478e9d688de77a70f3be845a4a27d",
        "docs/phase3-8b-descriptor-design.md",
        "5fbdd7ef2028ebbdd1187fb601c427d6b3b1250b4f86611f3ddfbd7f9be23cae",
    ),
)
_T080_REAL_REPO_METADATA_GOLDEN = (
    (
        "known_axes", "/generator/sha256",
        "1d4d45a3de4926c6aae76906f7b4b72d3fead51e9cdf62ff03f80a0379c364e0",
        "orchestrator/campaign/s1_known_axes_freeze.py",
        "1d4d45a3de4926c6aae76906f7b4b72d3fead51e9cdf62ff03f80a0379c364e0",
    ),
    (
        "holdout", "/generator/sha256",
        "1910fff38edf0e58f5bff221c29660a8f85dd0ed1b5c980234ec1af098584e5f",
        "orchestrator/campaign/s8b_holdout_freeze.py",
        "41c0b6a7b348acb0960b354f80ab79ba3376d4214a73f11d5ee739b04337d4b0",
    ),
)

_T080_RECEIPT_INTRODUCTION = "8bec195d096f852fd2b47070aa18a3b151613f0a"
_T080_RECEIPT_RAW_SHA256 = "b84f783218496f0750ed583a317be474a2207b3fe5661a67fab54b2d53723e3c"
_T080_MIGRATION_BASIS = "f04ae50b3c7be800885447be514b59f2405a4e83"
_T080_LIVE_HELD_CHECK_IDS = frozenset({
    "t080.live-known-axes-artifact-bytes",
    "t080.live-holdout-artifact-bytes",
    "t080.live-known-axes-ccbench-current-pin",
})
_T080_HELD_REASON = {
    "decision": "freeze-verification-hold",
    "ruling": "rulings-4th-batch-2026-08-12",
    "ruled_on": "2026-08-12",
    "authority": "user",
    "release": "ユーザーの明示命令のみ",
    "release_condition": "explicit-user-command-only",
}


def _assert_exact_refusals(actual, expected: set[str]) -> None:
    """refusal 集合の完全一致を要求する。

    len も比較するため、同一 refusal の重複追加も検出する
    (set 比較だけでは重複を落としてしまう)。
    """
    assert len(actual) == len(expected), actual
    assert set(actual) == expected, actual


def _assert_exact_t080_live_held_markers(actual) -> None:
    """live verify の保留 marker を ID と全 field で完全固定する。"""
    expected = {
        check_id: {
            "check_id": check_id,
            "status": "held",
            "reason": _T080_HELD_REASON,
        }
        for check_id in _T080_LIVE_HELD_CHECK_IDS
    }
    assert len(actual) == len(expected), actual
    assert {marker["check_id"]: marker for marker in actual} == expected


def _assert_structural_source_mismatch_refusal(
        refusal: str, *, document: dict, root: Path, prefix: str) -> None:
    """source mismatch 診断を実測値の自己期待にせず入力構造へ束縛する。"""
    expected_prefix = f"{prefix}: FreezeError: source sha256 不一致: "
    assert refusal.startswith(expected_prefix), refusal
    payload = refusal.removeprefix(expected_prefix)
    path, recorded_separator, hashes = payload.partition(" recorded=")
    recorded, actual_separator, actual = hashes.partition(" actual=")
    assert recorded_separator == " recorded=" and path, refusal
    assert actual_separator == " actual=", refusal
    assert len(recorded) == 64 and all(c in "0123456789abcdef" for c in recorded)
    assert len(actual) == 64 and all(c in "0123456789abcdef" for c in actual)
    assert recorded != actual

    records: set[tuple[str, str]] = set()

    def collect(value) -> None:
        if isinstance(value, dict):
            path = value.get("path")
            sha256 = value.get("sha256")
            if isinstance(path, str) and isinstance(sha256, str):
                records.add((path, sha256))
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(document)
    assert (path, recorded) in records, (refusal, sorted(records))
    assert (root / path).is_file(), path
    assert hashlib.sha256((root / path).read_bytes()).hexdigest() == actual


def _assert_refusal_reasons(actual, expected_prefixes: list[str]) -> None:
    """件数の完全一致 + 理由 prefix の 1:1 対応を要求する。

    実 repo の working tree bytes に依存する診断 payload (sha256 の実測値など) を
    期待値へ焼き込むと、無関係な正当編集で false red になる。理由の同一性と件数は
    厳密に固定しつつ、揮発する payload 部分だけを期待値から外す。
    完全一致が使える hermetic fixture では `_assert_exact_refusals` を使うこと。
    """
    assert len(actual) == len(expected_prefixes), actual
    remaining = list(expected_prefixes)
    for reason in actual:
        match = [p for p in remaining if reason.startswith(p)]
        assert len(match) == 1, (reason, remaining)
        remaining.remove(match[0])
    assert not remaining, remaining


def _never_issued_resolution():
    """Git 状態機械を対象にしない既存 fixture 用の未発行 resolution。"""
    return migration.ReceiptResolution(
        state="never-issued", refusals=(),
        t080_freeze_migration_observation=None,
        validation_head="0" * 40,
    )


def _sanitized_git_env() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_OPTIONAL_LOCKS": "0",
    })
    return env


def _run_git(root: Path, *args: str) -> str:
    """hermetic T-080 fixture 用の最小 Git runner。"""
    return subprocess.run(
        ["git", *args], cwd=root, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        env=_sanitized_git_env(),
    ).stdout.strip()


def _git_blob_sha256(root: Path, commit: str, path: str) -> str:
    """test 側だけで Git blob の内容 SHA-256 を導出する。"""
    raw = subprocess.run(
        ["git", "cat-file", "blob", f"{commit}:{path}"],
        cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=_sanitized_git_env(),
    ).stdout
    return hashlib.sha256(raw).hexdigest()


def _independent_t080_receipt_blob(root: Path) -> tuple[str, bytes] | None:
    commits = _run_git(
        root, "log", "--reverse", "--format=%H", "--", migration.RECEIPT_REL,
    ).splitlines()
    if not commits:
        return None
    introduction = commits[0]
    raw = subprocess.run(
        ["git", "show", f"{introduction}:{migration.RECEIPT_REL}"],
        cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=_sanitized_git_env(),
    ).stdout
    return introduction, raw


def _independent_ancestry_item(
        root: Path, *, artifact: str, recorded: str, validation_head: str) -> dict:
    kind = subprocess.run(
        ["git", "cat-file", "-t", recorded], cwd=root,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        env=_sanitized_git_env(),
    )
    if kind.returncode != 0:
        status, observed = "missing-commit", None
    else:
        assert kind.stdout.strip() == "commit"
        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", recorded, validation_head],
            cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=_sanitized_git_env(),
        )
        assert ancestry.returncode in {0, 1}
        status, observed = (
            ("ancestor", validation_head) if ancestry.returncode == 0
            else ("not-ancestor", validation_head)
        )
    return {
        "artifact": artifact, "kind": "ancestry", "subject": "/frozen_at_head",
        "recorded": recorded, "observed": observed, "status": status,
    }


def _t080_receipt_document(basis: str, *, invalid_confirmation: bool = False) -> dict:
    """U1 が必要とする active schema の receipt を自ファイル内で構成する。"""
    repins = [
        {
            "artifact": spec.artifact,
            "json_pointer": spec.json_pointer,
            "path": spec.path,
            "recorded_sha256": spec.recorded_sha256,
            "migration_blob_sha256": "b" * 64,
        }
        for spec in migration.SOURCE_REPIN_SPECS
    ]
    metadata = [
        {
            "artifact": spec.artifact,
            "json_pointer": spec.json_pointer,
            "path": spec.path,
            "recorded_sha256": spec.recorded_sha256,
            "migration_blob_sha256": "c" * 64,
            "disposition": "metadata-only",
        }
        for spec in migration.METADATA_SPECS
    ]
    report = [
        {
            **record,
            "provenance": {
                "status": "provenance_unverified",
                "commit": None,
                "distance_from_basis": None,
            },
            "diff_summary": {
                "status": "diff_unverified",
                "path": record["path"],
                "old_line_count": None,
                "new_line_count": 1,
                "added_lines": None,
                "deleted_lines": None,
            },
        }
        for record in repins
    ]
    return {
        "schema_version": migration.SCHEMA_VERSION,
        "migration_id": migration.MIGRATION_ID,
        "migration_basis_commit": basis,
        "artifacts": {
            "known_axes": {
                "path": migration.KNOWN_AXES_REL,
                "raw_sha256": migration.KNOWN_AXES_RAW_SHA256,
                "recorded_frozen_at_head": migration.KNOWN_AXES_RECORDED_HEAD,
            },
            "holdout": {
                "path": migration.HOLDOUT_REL,
                "raw_sha256": migration.HOLDOUT_RAW_SHA256,
                "recorded_frozen_at_head": migration.HOLDOUT_RECORDED_HEAD,
            },
        },
        "source_repins": repins,
        "metadata_fields": metadata,
        "reconstruction": {
            "known_axes": {
                "status": "pass",
                "projected_document_sha256": "d" * 64,
                "rebuilt_document_sha256": "d" * 64,
            },
            "holdout": {
                "status": "pass",
                "projected_document_sha256": "e" * 64,
                "live_scan_sha256": "f" * 64,
            },
        },
        "repin_report": report,
        "confirmed_by": "invalid confirmation" if invalid_confirmation else "human.test",
        "confirmed_at": "2026-07-22T12:34:56Z",
    }


def _t080_repo(tmp_path: Path, *, receipt: str) -> tuple[Path, Path]:
    """legacy artifact と任意の receipt 状態を持つ hermetic Git repo を作る。"""
    root = tmp_path / f"t080-{receipt}"
    root.mkdir()
    _run_git(root, "init", "-q")
    _run_git(root, "config", "user.name", "T080 U1 Test")
    _run_git(root, "config", "user.email", "t080-u1@example.invalid")
    for relative in (
        migration.KNOWN_AXES_REL,
        migration.HOLDOUT_REL,
    ):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    (root / "base.txt").write_text("base\n", encoding="utf-8")
    _run_git(root, "add", "-A")
    _run_git(root, "commit", "-q", "-m", "basis", "-m", "AI-Agent: none")
    basis = _run_git(root, "rev-parse", "HEAD")
    if receipt != "never-issued":
        document = _t080_receipt_document(
            basis, invalid_confirmation=(receipt == "invalid"),
        )
        path = root / migration.RECEIPT_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(migration._canonical_bytes(document))
        _run_git(root, "add", migration.RECEIPT_REL)
        _run_git(
            root, "commit", "-q", "-m", "introduce receipt",
            "-m", "AI-Agent: none",
        )
    return root, root / migration.HOLDOUT_REL


def _copy_t080_basis_file(root: Path, relative: str) -> None:
    source = ROOT / relative
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def _copy_t080_migration_basis_file(root: Path, relative: str, basis: str) -> None:
    """実 repo の発行済み receipt が束縛する migration basis blob をコピーする。"""
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(_run_git_bytes(ROOT, "show", f"{basis}:{relative}"))


_T080_E2E_BASE_CACHE: dict[tuple, tuple[Path, dict]] = {}


def _t080_output_snapshot(root: Path) -> tuple[tuple[object, ...], ...]:
    """Git-visible entry と非 ignore 祖先での一時作成後削除を捉える。

    規則由来 ignore prefix の祖先 directory だけ size / mtime / ctime を正規化する。
    """
    return git_visible_output_metadata_snapshot(root, ROOT)


def test_t080_output_snapshot_detects_git_visible_real_output_changes(tmp_path):
    ignored_prefixes = git_ignored_output_prefixes(ROOT)
    assert not is_git_ignored_output_path("visible", ignored_prefixes)
    control = tmp_path / "visible"
    before = _t080_output_snapshot(tmp_path)
    control.mkdir()
    (control / "nested").mkdir()
    payload = control / "nested" / "payload.bin"
    payload.write_bytes(b"git-visible t080 snapshot positive control")

    after = _t080_output_snapshot(tmp_path)
    assert after != before
    relative_control = control.relative_to(tmp_path).as_posix()
    relative_payload = payload.relative_to(tmp_path).as_posix()
    assert any(row[0] == relative_control for row in after)
    assert any(row[0] == relative_payload for row in after)


def test_t080_output_snapshot_excludes_git_ignored_real_output_changes(tmp_path):
    ignored_prefixes = git_ignored_output_prefixes(ROOT)
    assert "runs" in ignored_prefixes
    before = _t080_output_snapshot(tmp_path)
    ignored_parent = tmp_path / "runs"
    ignored_parent.mkdir()
    control = ignored_parent / "snapshot-ignored-t080"
    control.mkdir()
    (control / "nested").mkdir()
    (control / "nested" / "payload.bin").write_bytes(
        b"git-ignored t080 snapshot control"
    )

    assert _t080_output_snapshot(tmp_path) == before

    assert not is_git_ignored_output_path("runs-visible", ignored_prefixes)
    visible_before = _t080_output_snapshot(tmp_path)
    visible = tmp_path / "runs-visible" / "nested"
    visible.mkdir(parents=True)
    (visible / "payload.bin").write_bytes(b"git-visible runs prefix control")
    visible_after = _t080_output_snapshot(tmp_path)
    assert visible_after != visible_before, (
        "rule-derived ignore prefix 'runs' must not hide Git-visible 'runs-visible'"
    )


def test_t080_output_snapshot_observes_git_visible_create_and_delete(tmp_path):
    ignored_ancestors = git_ignored_output_ancestor_directories(ROOT)
    parent = tmp_path / "visible-transient-parent"
    assert not ignored_ancestors.contains(parent.name)
    parent.mkdir()
    before = _t080_output_snapshot(tmp_path)
    transient = parent / "visible-transient"
    transient.mkdir()
    (transient / "payload").write_bytes(b"visible transient")
    shutil.rmtree(transient)
    after = _t080_output_snapshot(tmp_path)
    assert after != before, "Git-visible create-and-delete must remain observable"


def _output_ignore_contract_repo(
        tmp_path: Path, root_rules: bytes, *, force_tracked: bool = False,
) -> Path:
    repo = tmp_path / "output-ignore-repo"
    repo.mkdir()
    _run_git(repo, "init", "-q")
    global_rules = tmp_path / "global-ignore"
    global_rules.write_bytes(b"output/global-cache/\n")
    _run_git(repo, "config", "core.excludesFile", str(global_rules))
    (repo / ".gitignore").write_bytes(root_rules)
    info_path = Path(_run_git(repo, "rev-parse", "--git-path", "info/exclude"))
    if not info_path.is_absolute():
        info_path = repo / info_path
    info_path.write_bytes(b"output/info-cache/\n")
    (repo / "output").mkdir()
    (repo / "output" / "README").write_bytes(b"tracked output sentinel")
    _run_git(
        repo, "add", *(('-f',) if force_tracked else ()), "output/README",
    )
    return repo


def test_git_ignored_output_prefixes_uses_rule_sources_before_paths_exist(tmp_path):
    repo = _output_ignore_contract_repo(
        tmp_path,
        b"""\
output/runs/
output/cache/deep/
output/variants/*/bin/
output/cancelled/deep/
!output/cancelled/deep/
output/**/recursive/
output/escaped\\ name/
other*/output/outside/
""",
    )

    prefixes_before = git_ignored_output_prefixes(repo)
    assert prefixes_before == (
        "cache/deep", "global-cache", "info-cache", "runs",
    )
    ancestors_before = git_ignored_output_ancestor_directories(repo)
    assert ancestors_before.exact == frozenset({".", "cache"})
    assert ancestors_before.subtree_roots == frozenset({"variants"})
    assert ancestors_before.contains("variants/branch/deeper")
    assert not ancestors_before.contains("cache/unrelated")
    assert not is_git_ignored_output_path("runs-visible", prefixes_before)

    (repo / "output" / "variants" / "v1" / "bin").mkdir(parents=True)
    # tracked descendant の無い ignored-only subtree は Git が各祖先も除外可能な directory として畳む。
    assert git_ignored_output_prefixes(repo) == (
        "cache/deep", "global-cache", "info-cache", "runs", "variants",
        "variants/v1", "variants/v1/bin",
    )
    assert git_ignored_output_ancestor_directories(repo) == ancestors_before


def test_git_ignored_output_prefixes_preserve_tracked_rule_descendant(tmp_path):
    repo = _output_ignore_contract_repo(tmp_path, b"output/runs/\n")
    tracked = repo / "output" / "runs" / "nested" / "tracked.txt"
    tracked.parent.mkdir(parents=True)
    tracked.write_bytes(b"force-added tracked descendant")
    _run_git(repo, "add", "-f", "output/runs/nested/tracked.txt")
    untracked = tracked.with_name("untracked.txt")
    untracked.write_bytes(b"ignored untracked peer")

    ignored_prefixes, ignored_ancestors = git_ignored_output_snapshot_rules(repo)
    visible = {
        path.relative_to(repo / "output").as_posix()
        for path in (repo / "output").rglob("*")
        if not is_git_ignored_output_path(
            path.relative_to(repo / "output").as_posix(), ignored_prefixes,
        )
    }

    assert "runs" in ignored_prefixes
    assert {"runs", "runs/nested", "runs/nested/tracked.txt"} <= visible
    assert "runs/nested/untracked.txt" not in visible
    assert ignored_ancestors.contains("runs")
    assert ignored_ancestors.contains("runs/nested")


def test_git_ignored_output_prefixes_rejects_entire_output_ignore(tmp_path):
    repo = _output_ignore_contract_repo(
        tmp_path, b"output/\n", force_tracked=True,
    )

    with pytest.raises(AssertionError, match="output/ 全体が Git ignore 対象"):
        git_ignored_output_prefixes(repo)


def test_check_rule_candidates_fails_closed_on_git_error(tmp_path):
    completed = subprocess.CompletedProcess(
        args=("git", "check-ignore"), returncode=128,
        stdout=b"", stderr=b"fatal: fixture git error",
    )

    with mock.patch(
            "orchestrator.tests.output_snapshot_ignores.subprocess.run",
            return_value=completed,
            ) as run:
        with pytest.raises(AssertionError, match=r"git check-ignore .* に失敗"):
            _check_rule_candidates(tmp_path, {b"output/runs": True})

    assert run.call_count == 1


def test_check_rule_candidates_rejects_rc1_with_stdout(tmp_path):
    completed = subprocess.CompletedProcess(
        args=("git", "check-ignore"), returncode=1,
        stdout=b"output/runs/\0", stderr=b"",
    )

    with mock.patch(
            "orchestrator.tests.output_snapshot_ignores.subprocess.run",
            return_value=completed,
            ):
        with pytest.raises(AssertionError, match=r"rc=1 で stdout を返した"):
            _check_rule_candidates(tmp_path, {b"output/runs": True})


def test_check_rule_candidates_rejects_rc0_without_nul_terminator(tmp_path):
    completed = subprocess.CompletedProcess(
        args=("git", "check-ignore"), returncode=0,
        stdout=b"output/runs/", stderr=b"",
    )

    with mock.patch(
            "orchestrator.tests.output_snapshot_ignores.subprocess.run",
            return_value=completed,
            ):
        with pytest.raises(AssertionError, match=r"rc=0 で正しい NUL 出力を返さない"):
            _check_rule_candidates(tmp_path, {b"output/runs": True})


def _run_git_bytes(root: Path, *args: str) -> bytes:
    """Git の失敗理由を stderr 本文付きで fail-closed に返す。"""
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root, check=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=_sanitized_git_env(),
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raw = getattr(exc, "stderr", b"")
        if isinstance(raw, bytes):
            detail = raw.decode("utf-8", "replace")
        else:
            detail = str(raw)
        raise AssertionError(
            f"git {' '.join(args)} に失敗: {detail.strip() or str(exc)}"
        ) from exc
    return completed.stdout


def _git_visible_output_paths(root: Path) -> set[str]:
    """本番列挙と同じ Git-visible regular file のうち output/ 配下を返す。"""
    tracked = _run_git_bytes(root, "ls-files", "-z", "-s", "--", "output")
    visible: set[str] = set()
    for raw_entry in tracked.split(b"\0"):
        if not raw_entry:
            continue
        entry = raw_entry.decode("utf-8")
        meta, separator, relative = entry.partition("\t")
        if not separator or not relative:
            raise AssertionError(
                f"git ls-files -s の出力を解釈できない: {entry!r}"
            )
        mode = meta.split(" ", 1)[0]
        if mode not in {"100644", "100755", "120000", "160000"}:
            raise AssertionError(f"未知の git file mode: {mode} ({relative})")
        if mode in {"100644", "100755"}:
            visible.add(relative)

    untracked = _run_git_bytes(
        root, "ls-files", "-z", "--others", "--exclude-standard",
        "--", "output",
    )
    for raw_relative in untracked.split(b"\0"):
        if not raw_relative:
            continue
        relative = raw_relative.decode("utf-8")
        path = root / relative
        if path.is_file() and not path.is_symlink():
            visible.add(relative)
    return visible


def _copy_git_visible_output(source_root: Path, destination: Path) -> set[str]:
    """Git-visible な output regular file だけを fixture へ複製する。"""
    visible_output = _git_visible_output_paths(source_root)
    excluded_artifacts = {
        migration.RECEIPT_REL,
        migration.DRAFT_REL,
    }
    for relative in sorted(visible_output - excluded_artifacts):
        source = source_root / relative
        if not source.is_file() or source.is_symlink():
            raise AssertionError(
                "Git-visible output path が regular file ではない: "
                f"{relative}"
            )

    visible_output_ancestors = {
        parent.as_posix()
        for relative in visible_output
        for parent in Path(relative).parents
        if parent != Path(".")
    }
    copyable_output = visible_output | visible_output_ancestors

    def ignore_non_visible_output_and_t080_artifacts(directory, names):
        ignored = {
            name
            for name in names
            if (Path(directory) / name).relative_to(source_root).as_posix()
            not in copyable_output
        }
        ignored.update({
            name
            for name in names
            if (Path(directory) / name).relative_to(source_root).as_posix()
            in excluded_artifacts
        })
        return ignored

    # 実 repo で ignored な s1-build-cache (1.8GB / 36,158 files) まで複製すると、
    # 列挙 17,119 件・scan text 16,423 件となり、fixture 構築が 15〜22 秒から
    # 121.7 秒へ膨らんだ ([T-128] 実測 2026-07-27)。Git を可視性の正本とし、
    # untracked の増減を隠す process 内 memo は置かない。
    shutil.copytree(
        source_root / "output", destination,
        ignore=ignore_non_visible_output_and_t080_artifacts,
    )
    return visible_output


def _t080_stub_free_e2e_repo(
        tmp_path: Path, *, r_trailer: str = "AI-Agent: none",
        extra_r_path: bool = False, issue_receipt: bool = True,
        distinct_basis_blob: bool = False,
        ) -> tuple[Path, Path, dict]:
    """`_build_t080_stub_free_e2e_repo` を process 内で引数ごとに 1 回だけ組む ([T-057])。

    この fixture は 36MB / 2300 ファイルの copytree + `git submodule add` + 子 python での
    draft→finalize→commit→verify で **1 回 15〜22 秒**かかり、そのうち同一引数の組み合わせが
    7 回作り直されていた (実測: 本番 git 畳み込み後に残った tail の最大要因)。
    base を 1 回だけ組み、各テストへは独立した実体コピーを渡す。

    テストは受け取った repo を破壊的に変異させる (ファイル追記・submodule への commit・削除) ため、
    **コピーは共有しない実体**でなければならない。返す document も deepcopy して渡す。
    """
    tmp_path = _assert_t080_temp_root_outside_real_output(tmp_path)
    base_temp_root = _assert_t080_temp_root_outside_real_output(
        Path(tempfile.gettempdir())
    )
    key = (r_trailer, extra_r_path, issue_receipt, distinct_basis_blob)
    cached = _T080_E2E_BASE_CACHE.get(key)
    if cached is None:
        base_parent = _assert_t080_temp_root_outside_real_output(Path(
            tempfile.mkdtemp(
                prefix="izanagi-t080-e2e-base-", dir=base_temp_root,
            )
        ))
        atexit.register(shutil.rmtree, base_parent, ignore_errors=True)
        base_root, _receipt, document = _build_t080_stub_free_e2e_repo(
            base_parent, r_trailer=r_trailer, extra_r_path=extra_r_path,
            issue_receipt=issue_receipt, distinct_basis_blob=distinct_basis_blob,
        )
        cached = (base_root, document)
        _T080_E2E_BASE_CACHE[key] = cached
    base_root, document = cached
    root = tmp_path / base_root.name
    shutil.copytree(base_root, root, symlinks=True)
    return root, root / migration.RECEIPT_REL, copy.deepcopy(document)


def test_t080_stub_free_e2e_exact_consumers_and_nodeids_b5():
    """helper の全 direct consumer と対象 6 function / 11 node を固定する。"""
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    expected_consumers = {
        "test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5": 1,
        "test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5": 4,
        "test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5": 1,
        "test_t080_full_valid_history_defects_have_one_baseline_reason_f28": 3,
        "test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28": 1,
        "test_never_issued_generator_tamper_reaches_public_driver_gate_g7": 1,
    }
    expected_parametrizations = {
        "test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5": (
            "defect, expected_reason",
            (
                ("known-artifact", "known_axes.artifact_bytes"),
                ("holdout-artifact", "holdout.artifact_bytes"),
                ("ccbench-current", "known_axes.ccbench_current"),
                ("unknownness-layer2", "holdout.unknownness_layer2"),
            ),
        ),
        "test_t080_full_valid_history_defects_have_one_baseline_reason_f28": (
            "defect, expected_reason",
            (
                ("bad-trailer", "receipt.user_commit_trailer"),
                ("extra-r-path", "receipt.introduction_diff"),
                ("modify-revert", "receipt.history_mutated"),
            ),
        ),
    }
    helper_consumer_nodes = [
        function
        for function in functions
        if any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_t080_stub_free_e2e_repo"
            for node in ast.walk(function)
        )
    ]
    helper_consumers = {function.name for function in helper_consumer_nodes}

    assert len(helper_consumer_nodes) == len(helper_consumers)
    assert helper_consumers == set(expected_consumers) | {
        "test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary",
    }

    expanded_nodeids = {}
    functions_by_name = {
        function.name: function
        for function in helper_consumer_nodes
        if function.name in expected_consumers
    }
    for name in sorted(functions_by_name):
        count = 1
        observed_parametrizations = []
        for decorator in functions_by_name[name].decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "parametrize"
            ):
                assert not decorator.keywords, ast.unparse(decorator)
                parameter_names = ast.literal_eval(decorator.args[0])
                parameters = tuple(ast.literal_eval(decorator.args[1]))
                observed_parametrizations.append((parameter_names, parameters))
                count *= len(parameters)
        expected = expected_parametrizations.get(name)
        assert observed_parametrizations == ([] if expected is None else [expected])
        expanded_nodeids[name] = count
    assert expanded_nodeids == expected_consumers
    assert sum(expanded_nodeids.values()) == 11


def _build_t080_stub_free_e2e_repo(
        tmp_path: Path, *, r_trailer: str = "AI-Agent: none",
        extra_r_path: bool = False, issue_receipt: bool = True,
        distinct_basis_blob: bool = False,
        ) -> tuple[Path, Path, dict]:
    """production builder/verifier/gate を一度も stub しない T-080 発行 repo。"""
    tmp_path = _assert_t080_temp_root_outside_real_output(tmp_path)
    root = tmp_path / "t080-stub-free-e2e"
    root.mkdir()
    _run_git(root, "init", "-q")
    _run_git(root, "config", "user.name", "T080 E2E Human")
    _run_git(root, "config", "user.email", "t080-e2e@example.invalid")

    # subprocess が import closure を host から補えないよう orchestrator 全体を配置する。
    shutil.copytree(
        ROOT / "orchestrator", root / "orchestrator",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )

    _copy_git_visible_output(ROOT, root / "output")

    known = json.loads((ROOT / migration.KNOWN_AXES_REL).read_text(encoding="utf-8"))
    source_paths: set[str] = set()

    def collect(value) -> None:
        if isinstance(value, dict):
            if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
                source_paths.add(value["path"])
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(known)
    operational = {
        migration.KNOWN_AXES_REL,
        migration.HOLDOUT_REL,
        "orchestrator/campaign/s1_known_axes_freeze.py",
        "orchestrator/campaign/s8b_holdout_freeze.py",
        "docs/phase3-8b-descriptor-design.md",
        migration.POSITIVE_CONTROL_PATH,
    }
    real_receipt = json.loads(
        (ROOT / migration.RECEIPT_REL).read_text(encoding="utf-8")
    )
    real_basis = real_receipt["migration_basis_commit"]
    in_repo_sources = {
        path for path in source_paths if not path.startswith("external/ccbench/")
    }
    current_runtime_sources = {
        path for path in in_repo_sources
        if path.startswith("orchestrator/campaign/") and path.endswith(".py")
    }
    current_production_sources = {
        "orchestrator/campaign/t080_freeze_migration.py",
        "orchestrator/campaign/s8b_oracle_driver.py",
        "orchestrator/campaign/s8b_holdout_freeze.py",
    }
    assert current_runtime_sources
    assert current_production_sources.isdisjoint(in_repo_sources)
    # T-080 は一回限りの historical migration。現在の作業ツリー bytes を basis に
    # すると、後続 wave が既存の unchanged source を変更しただけで閉包を偽造してしまう。
    # 発行済み receipt の commit から source closure を復元し、検査本体の exact 12/51
    # predicate は一切緩めない。
    for relative in sorted(in_repo_sources):
        _copy_t080_migration_basis_file(root, relative, real_basis)
    for relative in sorted(operational - in_repo_sources):
        _copy_t080_basis_file(root, relative)
    if distinct_basis_blob:
        # real-repo 固定値を返す退化を検出できるよう、この fixture の basis だけを
        # 安全な非実行 blob で意図的に分岐させる。期待値は下で Git から独立導出する。
        descriptor = root / "docs/phase3-8b-descriptor-design.md"
        descriptor.write_bytes(
            descriptor.read_bytes() + b"\n<!-- T-093 fixture-local basis blob -->\n"
        )

    _run_git(
        root, "-c", "protocol.file.allow=always", "submodule", "add", "-q",
        str(ROOT / migration.CCBENCH_REL), migration.CCBENCH_REL,
    )
    _run_git(root / migration.CCBENCH_REL, "checkout", "-q", known["ccbench_pin"])
    _run_git(root, "add", "-A")
    _run_git(root, "commit", "-q", "-m", "T080 migration basis", "-m", "AI-Agent: none")
    basis_history = migration.inspect_receipt_history(root=root, check_worktree=True)
    assert basis_history.state == "never-issued", (
        "T-080 E2E fixture basis は never-issued 必須: "
        f"observed={basis_history.state}"
    )

    receipt = root / migration.RECEIPT_REL
    if not issue_receipt:
        return root, receipt, {}
    # pin 済み source は fixture repo では historical data のまま保持する。一方、
    # production builder/verifier/gate が import する閉包は現行世代で統一するため、
    # fixture 外の source を限定 loader から canonical module 名へ供給する。
    runtime_source_root = tmp_path / "t080-current-runtime"
    for relative in sorted(current_runtime_sources):
        _copy_t080_basis_file(runtime_source_root, relative)
    child = textwrap.dedent("""
        import importlib
        import importlib.abc
        import importlib.util
        import json
        import os
        import subprocess
        import sys
        from pathlib import Path

        def _sanitized_git_env():
            env = {
                key: value for key, value in os.environ.items()
                if not key.startswith("GIT_")
            }
            env.update({
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_TERMINAL_PROMPT": "0",
                "GIT_OPTIONAL_LOCKS": "0",
            })
            return env

        root = Path(sys.argv[1]).resolve()
        runtime_source_root = Path(sys.argv[4]).resolve()
        runtime_relatives = tuple(json.loads(sys.argv[5]))
        runtime_modules = {
            ".".join(Path(relative).with_suffix("").parts): relative
            for relative in runtime_relatives
        }

        class _CurrentSourceLoader(importlib.abc.Loader):
            def __init__(self, fullname, repository_path, source_path):
                self.fullname = fullname
                self.repository_path = repository_path
                self.source_path = source_path

            def create_module(self, spec):
                return None

            def exec_module(self, module):
                source = self.source_path.read_bytes()
                code = compile(source, str(self.repository_path), "exec")
                exec(code, module.__dict__)

        class _CurrentSourceFinder(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                relative = runtime_modules.get(fullname)
                if relative is None:
                    return None
                repository_path = root / relative
                source_path = runtime_source_root / relative
                loader = _CurrentSourceLoader(
                    fullname, repository_path, source_path,
                )
                spec = importlib.util.spec_from_loader(
                    fullname, loader, origin=str(repository_path),
                )
                assert spec is not None
                spec.has_location = True
                return spec

        sys.meta_path.insert(0, _CurrentSourceFinder())
        sys.path[0] = str(root)
        from orchestrator.campaign import s1_known_axes_freeze as known
        from orchestrator.campaign import s8b_holdout_freeze as holdout
        from orchestrator.campaign import s8b_oracle_driver as driver
        from orchestrator.campaign import t080_freeze_migration as migration
        for module_name in sorted(runtime_modules):
            importlib.import_module(module_name)
        loaded_runtime_modules = tuple(
            sys.modules[module_name] for module_name in sorted(runtime_modules)
        )
        assert all(
            isinstance(module.__loader__, _CurrentSourceLoader)
            for module in loaded_runtime_modules
        ), loaded_runtime_modules

        sys.path.insert(0, str(root))
        modules = (
            migration, known, holdout, driver,
            driver._t080_migration,
            driver.s1_known_axes_freeze,
            driver.s8b_holdout_freeze,
        )
        assert Path(sys.path[0]).resolve() == root
        module_files = tuple(Path(module.__file__).resolve() for module in modules)
        assert all(path.is_relative_to(root) for path in module_files), module_files
        module_roots = (migration.ROOT.resolve(), known.ROOT.resolve(), holdout.ROOT.resolve())
        assert module_roots == (root, root, root), module_roots
        for relative in runtime_relatives:
            committed = subprocess.run(
                ["git", "show", f"HEAD:{relative}"], cwd=root, check=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=_sanitized_git_env(),
            ).stdout
            assert (root / relative).read_bytes() == committed, relative

        basis = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            env=_sanitized_git_env(),
        ).stdout.strip()
        migration.draft_receipt(
            basis=basis, out=migration.DRAFT_REL, root=root,
        )
        migration.validate_draft(path=migration.DRAFT_REL, root=root)
        document = migration.finalize_receipt(
            draft=migration.DRAFT_REL,
            confirmed_by="t080.e2e.human",
            confirmed_at="2026-07-22T12:34:56Z",
            out=migration.RECEIPT_REL,
            root=root,
        )
        (root / migration.DRAFT_REL).unlink()
        subprocess.run(
            ["git", "add", migration.RECEIPT_REL], cwd=root, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=_sanitized_git_env(),
        )
        if sys.argv[3] == "1":
            (root / "r-extra.txt").write_text("extra in R\\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", "r-extra.txt"], cwd=root, check=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=_sanitized_git_env(),
            )
        subprocess.run(
            ["git", "commit", "-q", "-m", "activate T080 receipt", "-m", sys.argv[2]],
            cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=_sanitized_git_env(),
        )
        resolution = migration.verify_receipt(root=root)
        decision = driver.gate_check(
            freeze_path=root / migration.HOLDOUT_REL, root=root,
        )
        if sys.argv[2] == "AI-Agent: none" and sys.argv[3] == "0":
            assert resolution.state == "active-valid" and resolution.refusals == ()
            assert decision.allowed is False
            assert len(decision.refusals) == 2
            assert all(
                refusal.startswith(("floor-null:", "budget-null:"))
                for refusal in decision.refusals
            )
        else:
            assert resolution.state == "invalid"
        print(json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    """)
    completed = subprocess.run(
        [sys.executable, "-I", "-B", "-c", child, str(root), r_trailer,
         "1" if extra_r_path else "0", str(runtime_source_root),
         json.dumps(sorted(current_runtime_sources))],
        cwd=root, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True,
        env={
            **_sanitized_git_env(),
            "PYTHONPATH": "",
            "PYTHONNOUSERSITE": "1",
        },
    )
    assert completed.returncode == 0, completed.stderr
    document = json.loads(completed.stdout)
    return root, receipt, document


def test_t080_output_copy_visibility_matches_production_enumeration(
        tmp_path, monkeypatch):
    for key in tuple(os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)

    root = tmp_path / "source"
    output = root / "output"
    ccbench = root / "external" / "ccbench"
    output.mkdir(parents=True)
    ccbench.mkdir(parents=True)
    _run_git(root, "init", "-q")
    _run_git(root, "config", "user.name", "T080 visibility test")
    _run_git(root, "config", "user.email", "t080-visibility@example.invalid")
    _run_git(ccbench, "init", "-q")

    (root / ".gitignore").write_text(
        "output/ignored.txt\n", encoding="utf-8",
    )
    (output / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    deep = output / "a" / "b" / "c.txt"
    deep.parent.mkdir(parents=True)
    deep.write_text("deep tracked\n", encoding="utf-8")
    (output / "untracked.txt").write_text("untracked\n", encoding="utf-8")
    (output / "ignored.txt").write_text("ignored\n", encoding="utf-8")
    (output / "tracked-symlink").symlink_to("tracked.txt")
    (output / "untracked-symlink").symlink_to("untracked.txt")
    receipt = root / migration.RECEIPT_REL
    draft = root / migration.DRAFT_REL
    retained = receipt.parent / "retained.txt"
    receipt.parent.mkdir(parents=True)
    receipt.write_text("stale receipt\n", encoding="utf-8")
    draft.write_text("stale draft\n", encoding="utf-8")
    retained.write_text("retained\n", encoding="utf-8")
    _run_git(
        root, "add", ".gitignore", "output/tracked.txt", "output/a/b/c.txt",
        "output/tracked-symlink", migration.RECEIPT_REL,
        migration.DRAFT_REL, retained.relative_to(root).as_posix(),
    )

    expected_visible = {
        "output/tracked.txt",
        "output/a/b/c.txt",
        "output/untracked.txt",
        migration.RECEIPT_REL,
        migration.DRAFT_REL,
        retained.relative_to(root).as_posix(),
    }
    copied_output = tmp_path / "copied-output"
    fixture_visible = _copy_git_visible_output(root, copied_output)
    production_visible = {
        relative
        for relative in s8b_holdout_freeze.enumerate_repository_files(root)
        if relative.startswith("output/")
    }
    copied_regular = {
        path.relative_to(copied_output).as_posix()
        for path in copied_output.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    expected_copied = {
        Path(relative).relative_to("output").as_posix()
        for relative in expected_visible
        if relative not in {migration.RECEIPT_REL, migration.DRAFT_REL}
    }

    assert fixture_visible == expected_visible
    assert fixture_visible == production_visible
    assert copied_regular == expected_copied

    (output / "tracked.txt").unlink()
    with pytest.raises(
            AssertionError,
            match=r"Git-visible output path が regular file ではない: output/tracked\.txt",
            ):
        _copy_git_visible_output(root, tmp_path / "missing-tracked-output")


def test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary(
        tmp_path, monkeypatch):
    forbidden = ROOT / "output"
    before = _t080_output_snapshot(forbidden)
    with pytest.raises(
            AssertionError, match=r"T-080 E2E temp root は実 repo の output/ 配下"):
        _build_t080_stub_free_e2e_repo(forbidden, issue_receipt=False)
    with pytest.raises(
            AssertionError, match=r"T-080 E2E temp root は実 repo の output/ 配下"):
        _t080_stub_free_e2e_repo(forbidden, issue_receipt=False)

    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(forbidden))
    with pytest.raises(
            AssertionError, match=r"T-080 E2E temp root は実 repo の output/ 配下"):
        _t080_stub_free_e2e_repo(tmp_path, issue_receipt=False)
    assert _t080_output_snapshot(forbidden) == before


def test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5(tmp_path):
    root, _receipt_path, document = _t080_stub_free_e2e_repo(
        tmp_path, distinct_basis_blob=True,
    )
    assert tuple(
        (item["artifact"], item["json_pointer"], item["recorded_sha256"])
        for item in document["source_repins"]
    ) == _T080_SOURCE_GOLDEN
    assert tuple(
        (item["artifact"], item["json_pointer"], item["recorded_sha256"])
        for item in document["metadata_fields"]
    ) == _T080_METADATA_GOLDEN
    marker_sentinel = "t080-held-marker-negative-witness"
    with mock.patch.object(
            migration._freeze_hold, "held_marker",
            side_effect=RuntimeError(marker_sentinel),
            ) as held_marker_witness:
        marker_failure = migration.verify_receipt(root=root)
    assert held_marker_witness.call_count > 0
    assert marker_failure.state == "invalid"
    assert marker_failure.held_checks == ()
    assert any(marker_sentinel in refusal for refusal in marker_failure.refusals)

    resolution = migration.verify_receipt(root=root)
    assert resolution.state == "active-valid"
    assert resolution.refusals == ()
    _assert_exact_t080_live_held_markers(resolution.held_checks)
    assert resolution.t080_freeze_migration_observation is not None
    items = resolution.t080_freeze_migration_observation["items"]
    assert len(items) == 17
    fixture_basis = _run_git(root, "rev-parse", "HEAD^")
    basis_golden = tuple(
        (kind, artifact, pointer, path)
        for kind, golden in (
            ("source-repin", _T080_REAL_REPO_SOURCE_GOLDEN),
            ("generator-metadata", _T080_REAL_REPO_METADATA_GOLDEN),
        )
        for artifact, pointer, _recorded, path, _real_observed in golden
    )
    observed_by_path = {
        path: _git_blob_sha256(root, fixture_basis, path)
        for path in dict.fromkeys(path for _kind, _artifact, _pointer, path in basis_golden)
    }
    expected_blob_observations = tuple(
        (artifact, kind, pointer, observed_by_path[path])
        for kind, artifact, pointer, path in basis_golden
    )
    assert tuple(
        (item["artifact"], item["kind"], item["subject"], item["observed"])
        for item in items[:15]
    ) == expected_blob_observations

    with mock.patch.object(migration._freeze_hold, "HELD", False):
        released = migration.verify_receipt(root=root)
    assert released.state == "active-valid"
    assert released.refusals == ()
    assert released.held_checks == ()

    decision = driver.gate_check(
        freeze_path=root / migration.HOLDOUT_REL, root=root,
    )
    _assert_exact_refusals(decision.refusals, {_FLOOR_REFUSAL, _BUDGET_REFUSAL})
    assert decision.allowed is False
    assert decision.t080_freeze_migration_observation is None

    # 同じ R blob/H_v から report が envelope を byte-exact に再導出する。
    record = dataclasses.make_dataclass(
        "Record", [("stage", str), ("payload", dict)],
    )(report_module.SESSION_STAGE, {
        "event": "campaign-start",
        "t080_freeze_migration_observation": resolution.t080_freeze_migration_observation,
    })
    classified = report_module._campaign_t080_observation(
        [record], repo_root=root, current_receipt_invalid=False,
    )
    assert classified.kind == "envelope" and classified.issue is None
    assert json.loads(classified.canonical) == resolution.t080_freeze_migration_observation

    (root / migration.RECEIPT_REL).unlink()
    current = migration.inspect_receipt_history(root=root)
    assert current.state == "issued-but-missing"
    invalidated = report_module._campaign_t080_observation(
        [record], repo_root=root, current_receipt_invalid=True,
    )
    assert invalidated.kind == "malformed"
    assert invalidated.issue == (
        "t080-freeze-migration-observation: malformed envelope: "
        "report 生成時の receipt が issued-but-missing/invalid"
    )


@pytest.mark.parametrize(
    "defect, expected_reason",
    [
        ("known-artifact", "known_axes.artifact_bytes"),
        ("holdout-artifact", "holdout.artifact_bytes"),
        ("ccbench-current", "known_axes.ccbench_current"),
        ("unknownness-layer2", "holdout.unknownness_layer2"),
    ],
)
def test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5(
        tmp_path, defect, expected_reason):
    root, _receipt_path, _document = _t080_stub_free_e2e_repo(tmp_path)
    if defect == "known-artifact":
        path = root / migration.KNOWN_AXES_REL
        path.write_bytes(path.read_bytes() + b" ")
    elif defect == "holdout-artifact":
        path = root / migration.HOLDOUT_REL
        path.write_bytes(path.read_bytes() + b" ")
    elif defect == "ccbench-current":
        positive_held = migration.verify_receipt(root=root)
        assert positive_held.state == "active-valid"
        assert positive_held.refusals == ()
        _assert_exact_t080_live_held_markers(positive_held.held_checks)
        with mock.patch.object(migration._freeze_hold, "HELD", False):
            positive_released = migration.verify_receipt(root=root)
        assert positive_released.state == "active-valid"
        assert positive_released.refusals == ()
        assert positive_released.held_checks == ()

        submodule = root / migration.CCBENCH_REL
        tree = _run_git(submodule, "rev-parse", "HEAD^{tree}")
        commit_env = _sanitized_git_env()
        commit_env.update({
            "GIT_AUTHOR_NAME": "T080 E2E", "GIT_AUTHOR_EMAIL": "t080@example.invalid",
            "GIT_COMMITTER_NAME": "T080 E2E", "GIT_COMMITTER_EMAIL": "t080@example.invalid",
        })
        replacement = subprocess.run(
            ["git", "commit-tree", tree], cwd=submodule, input="same tree\n",
            check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=commit_env,
        ).stdout.strip()
        _run_git(submodule, "checkout", "-q", replacement)
        known = json.loads(
            (root / migration.KNOWN_AXES_REL).read_text(encoding="utf-8")
        )
        assert _run_git(root, "rev-parse", f"HEAD:{migration.CCBENCH_REL}") == (
            known["ccbench_pin"]
        )
        assert _run_git(submodule, "rev-parse", "HEAD") == replacement
        with mock.patch.object(migration._freeze_hold, "HELD", False):
            checkout_only = migration.verify_receipt(root=root)
        assert checkout_only.state == "invalid"
        assert checkout_only.held_checks == ()
        assert len(checkout_only.refusals) == 1, checkout_only.refusals
        assert checkout_only.refusals[0].startswith(
            f"{migration.KNOWN_PREFIX}: [known_axes.ccbench_current]"
        )

        _run_git(root, "add", migration.CCBENCH_REL)
        _run_git(
            root, "commit", "-q", "-m", "commit mismatched ccbench gitlink",
            "-m", "AI-Agent: none",
        )
        assert _run_git(root, "rev-parse", f"HEAD:{migration.CCBENCH_REL}") == replacement
        assert _run_git(root, "status", "--porcelain", "--untracked-files=all") == ""
    else:
        (root / "rr80-known.txt").write_text(
            "ycsb_" + "rratio=8" + "0\n"
            + "ycsb_" + "zipf_skew=0" + ".9\n"
            + "ycsb_" + "rmw=" + "0\n",
            encoding="utf-8",
        )
    result = migration.verify_receipt(root=root)
    if defect in {"known-artifact", "holdout-artifact", "ccbench-current"}:
        assert result.state == "active-valid", result.refusals
        assert result.refusals == ()
        _assert_exact_t080_live_held_markers(result.held_checks)
        with mock.patch.object(migration._freeze_hold, "HELD", False):
            released = migration.verify_receipt(root=root)
        assert released.state == "invalid"
        assert len(released.refusals) == 1, released.refusals
        assert released.held_checks == ()
        assert released.refusals[0].startswith(
            (migration.KNOWN_PREFIX if expected_reason.startswith("known_axes.")
             else migration.HOLDOUT_PREFIX)
            + f": [{expected_reason}]"
        )
        return
    assert result.state == "invalid"
    assert len(result.refusals) == 1, result.refusals
    assert result.refusals[0].startswith(
        (migration.KNOWN_PREFIX if expected_reason.startswith("known_axes.")
         else migration.HOLDOUT_PREFIX)
        + f": [{expected_reason}]"
    )
    assert result.t080_freeze_migration_observation is None


def test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5(tmp_path):
    root, _receipt_path, receipt = _t080_stub_free_e2e_repo(tmp_path)
    known = json.loads((root / migration.KNOWN_AXES_REL).read_text(encoding="utf-8"))
    holdout = json.loads((root / migration.HOLDOUT_REL).read_text(encoding="utf-8"))

    def exact_reason(call, reason):
        with pytest.raises(migration.MigrationError) as caught:
            call()
        assert caught.value.reason == reason

    bad_known_closure = copy.deepcopy(receipt)
    bad_known_closure["source_repins"][0]["migration_blob_sha256"] = "0" * 64
    exact_reason(
        lambda: migration._verify_known_closure(bad_known_closure, known, root),
        "known_axes.source_closure",
    )
    bad_holdout_closure = copy.deepcopy(receipt)
    bad_holdout_closure["source_repins"][-1]["migration_blob_sha256"] = "0" * 64
    exact_reason(
        lambda: migration._verify_holdout_closure(
            bad_holdout_closure, known, holdout, root,
        ),
        "holdout.design_closure",
    )
    bad_metadata = copy.deepcopy(receipt)
    bad_metadata["metadata_fields"][0]["migration_blob_sha256"] = "0" * 64
    exact_reason(
        lambda: migration._verify_metadata_closure(bad_metadata, known, holdout, root),
        "receipt.repin_invalid",
    )
    bad_schema = copy.deepcopy(known)
    bad_schema["unexpected"] = "tampered"
    exact_reason(
        lambda: migration._verify_known_schema(receipt, bad_schema),
        "known_axes.schema",
    )
    bad_pairing = copy.deepcopy(known)
    bad_pairing["s1b_pairing"] = []
    exact_reason(
        lambda: migration._verify_known_pairing(receipt, bad_pairing),
        "known_axes.pairing",
    )
    exact_reason(
        lambda: migration._verify_ccbench_basis(
            receipt["migration_basis_commit"], "0" * 40, root,
        ),
        "known_axes.ccbench_gitlink",
    )
    bad_reconstruction = copy.deepcopy(receipt)
    bad_reconstruction["reconstruction"]["known_axes"][
        "projected_document_sha256"
    ] = "0" * 64
    exact_reason(
        lambda: migration._verify_reconstruction_static(
            bad_reconstruction, known, holdout,
        ),
        "receipt.reconstruction_invalid",
    )
    positive = root / migration.POSITIVE_CONTROL_PATH
    original_positive = positive.read_bytes()
    positive.write_bytes(original_positive + b"tamper")
    try:
        exact_reason(
            lambda: migration._validate_positive_control(root),
            "holdout.positive_control",
        )
    finally:
        positive.write_bytes(original_positive)
    blob = subprocess.run(
        ["git", "hash-object", "-w", "--stdin"], cwd=root, input=b"not commit",
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=_sanitized_git_env(),
    ).stdout.decode().strip()
    ancestry = migration._classify_ancestry(
        blob, _run_git(root, "rev-parse", "HEAD"), root, artifact="known_axes",
    )
    assert ancestry.refusal_reason == "known_axes.ancestry_object_type"


def test_t080_static_adapter_rejects_noncanonical_known_predicate_as_schema():
    receipt = _t080_receipt_document("a" * 40)
    resolution = migration.ReceiptResolution(
        state="active-valid",
        refusals=(),
        t080_freeze_migration_observation={},
        validation_head="a" * 40,
        receipt=receipt,
    )
    known = json.loads((ROOT / migration.KNOWN_AXES_REL).read_text(encoding="utf-8"))
    known["entries"]["balanced"]["system_gate"][
        "gate_predicate"] = "izanagi_gate_pass = true;"
    known_raw = migration._canonical_bytes(known)
    holdout_raw = (ROOT / migration.HOLDOUT_REL).read_bytes()

    with mock.patch.multiple(
            migration,
            _verify_known_closure=mock.DEFAULT,
            _verify_holdout_closure=mock.DEFAULT,
            _verify_metadata_closure=mock.DEFAULT,
            _verify_reconstruction_static=mock.DEFAULT,
            _verify_ccbench_current=mock.DEFAULT,
            _verify_ccbench_basis_from_receipt=mock.DEFAULT,
            _validate_positive_control=mock.DEFAULT,
            _verify_known_pairing=mock.DEFAULT,
            _verify_holdout_live_scan=mock.DEFAULT):
        held = migration.static_gate_adapter(
            resolution=resolution,
            known_raw=known_raw,
            holdout_raw=holdout_raw,
            root=ROOT,
        )

    _assert_exact_refusals(held.refusals, {
        "known-axes-freeze-verify: [known_axes.schema] "
        "entries.balanced.system_gate.gate_predicate が正準集合外",
    })
    assert "t080.static-known-axes-artifact-bytes" in {
        marker["check_id"] for marker in held.held_checks
    }

    with mock.patch.multiple(
            migration,
            _verify_known_closure=mock.DEFAULT,
            _verify_holdout_closure=mock.DEFAULT,
            _verify_metadata_closure=mock.DEFAULT,
            _verify_reconstruction_static=mock.DEFAULT,
            _verify_ccbench_current=mock.DEFAULT,
            _verify_ccbench_basis_from_receipt=mock.DEFAULT,
            _validate_positive_control=mock.DEFAULT,
            _verify_known_pairing=mock.DEFAULT,
            _verify_holdout_live_scan=mock.DEFAULT), \
            mock.patch.object(migration._freeze_hold, "HELD", False):
        released = migration.static_gate_adapter(
            resolution=resolution,
            known_raw=known_raw,
            holdout_raw=holdout_raw,
            root=ROOT,
        )
    _assert_exact_refusals(released.refusals, {
        "known-axes-freeze-verify: [known_axes.artifact_bytes]",
        "known-axes-freeze-verify: [known_axes.schema] "
        "entries.balanced.system_gate.gate_predicate が正準集合外",
    })


def test_oracle_recorded_known_pin_hold_and_release_positive_control(tmp_path):
    root = tmp_path
    holdout_raw = (ROOT / migration.HOLDOUT_REL).read_bytes()
    known_raw = (ROOT / migration.KNOWN_AXES_REL).read_bytes()
    freeze = json.loads(holdout_raw)
    freeze["known_axes_freeze"]["sha256"] = "0" * 64
    freeze_path = root / migration.HOLDOUT_REL
    known_path = root / migration.KNOWN_AXES_REL
    freeze_path.parent.mkdir(parents=True)
    known_path.parent.mkdir(parents=True)
    freeze_path.write_bytes(holdout_raw)
    known_path.write_bytes(known_raw)
    receipt = _t080_receipt_document("a" * 40)
    receipt["artifacts"]["holdout"]["raw_sha256"] = hashlib.sha256(
        holdout_raw,
    ).hexdigest()
    resolution = migration.ReceiptResolution(
        "active-valid", (), {}, "a" * 40, receipt=receipt,
    )
    adapted = migration.AdapterResult((), {})
    with mock.patch.object(migration, "static_gate_adapter", return_value=adapted):
        held = driver._t080_adapter_refusals(
            resolution=resolution, freeze=freeze,
            freeze_sha256=hashlib.sha256(holdout_raw).hexdigest(),
            freeze_path=freeze_path, root=root,
        )
        assert held is not None
        assert "s8b-oracle.known-axes-recorded-pin" in {
            marker["check_id"] for marker in held.held_checks
        }
        with mock.patch.object(driver._freeze_hold, "HELD", False):
            assert driver._t080_adapter_refusals(
                resolution=resolution, freeze=freeze,
                freeze_sha256=hashlib.sha256(holdout_raw).hexdigest(),
                freeze_path=freeze_path, root=root,
            ) is None


def test_oracle_live_known_bytes_hold_and_release_positive_control(tmp_path):
    root = tmp_path
    holdout_raw = (ROOT / migration.HOLDOUT_REL).read_bytes()
    known_raw = (ROOT / migration.KNOWN_AXES_REL).read_bytes() + b" "
    freeze = json.loads(holdout_raw)
    freeze_path = root / migration.HOLDOUT_REL
    known_path = root / migration.KNOWN_AXES_REL
    freeze_path.parent.mkdir(parents=True)
    known_path.parent.mkdir(parents=True)
    freeze_path.write_bytes(holdout_raw)
    known_path.write_bytes(known_raw)
    receipt = _t080_receipt_document("a" * 40)
    receipt["artifacts"]["holdout"]["raw_sha256"] = hashlib.sha256(
        holdout_raw,
    ).hexdigest()
    resolution = migration.ReceiptResolution(
        "active-valid", (), {}, "a" * 40, receipt=receipt,
    )
    adapted = migration.AdapterResult((), {})
    with mock.patch.object(migration, "static_gate_adapter", return_value=adapted):
        held = driver._t080_adapter_refusals(
            resolution=resolution, freeze=freeze,
            freeze_sha256=hashlib.sha256(holdout_raw).hexdigest(),
            freeze_path=freeze_path, root=root,
        )
        assert held == []
        assert "s8b-oracle.known-axes-live-bytes" in {
            marker["check_id"] for marker in held.held_checks
        }
        with mock.patch.object(driver._freeze_hold, "HELD", False):
            released = driver._t080_adapter_refusals(
                resolution=resolution, freeze=freeze,
                freeze_sha256=hashlib.sha256(holdout_raw).hexdigest(),
                freeze_path=freeze_path, root=root,
            )
        assert released == [
            "known-axes-freeze-verify: [known_axes.artifact_bytes] "
            "known_axes raw bytes が legacy pin と不一致"
        ]


@pytest.mark.parametrize(
    "defect, expected_reason",
    [
        ("bad-trailer", "receipt.user_commit_trailer"),
        ("extra-r-path", "receipt.introduction_diff"),
        ("modify-revert", "receipt.history_mutated"),
    ],
)
def test_t080_full_valid_history_defects_have_one_baseline_reason_f28(
        tmp_path, defect, expected_reason):
    root, receipt_path, _document = _t080_stub_free_e2e_repo(
        tmp_path,
        r_trailer=("AI-Agent: codex" if defect == "bad-trailer" else "AI-Agent: none"),
        extra_r_path=(defect == "extra-r-path"),
    )
    if defect == "modify-revert":
        original = receipt_path.read_bytes()
        changed = json.loads(original)
        changed["confirmed_at"] = "2026-07-22T12:34:57Z"
        receipt_path.write_bytes(migration._canonical_bytes(changed))
        _run_git(root, "add", migration.RECEIPT_REL)
        _run_git(root, "commit", "-q", "-m", "modify receipt", "-m", "AI-Agent: none")
        receipt_path.write_bytes(original)
        _run_git(root, "add", migration.RECEIPT_REL)
        _run_git(root, "commit", "-q", "-m", "revert receipt", "-m", "AI-Agent: none")
    result = migration.verify_receipt(root=root)
    assert result.state in {"invalid", "issued-but-missing"}
    assert len(result.refusals) == 1, result.refusals
    assert result.refusals[0].startswith(
        f"{migration.RECEIPT_PREFIX}: [{expected_reason}]"
    )
    assert result.t080_freeze_migration_observation is None


def test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28(tmp_path):
    root, receipt_path, _document = _t080_stub_free_e2e_repo(tmp_path)
    receipt_path.unlink()
    _run_git(root, "add", "-u", migration.RECEIPT_REL)
    _run_git(root, "commit", "-q", "-m", "delete receipt", "-m", "AI-Agent: none")
    basis = _run_git(root, "rev-parse", "HEAD")
    known = json.loads(
        (root / migration.KNOWN_AXES_REL).read_text(encoding="utf-8")
    )
    source_paths: set[str] = set()

    def collect_source_paths(value) -> None:
        if isinstance(value, dict):
            if isinstance(value.get("path"), str) and isinstance(
                    value.get("sha256"), str):
                source_paths.add(value["path"])
            for child_value in value.values():
                collect_source_paths(child_value)
        elif isinstance(value, list):
            for child_value in value:
                collect_source_paths(child_value)

    collect_source_paths(known)
    runtime_relatives = sorted(
        path for path in source_paths
        if path.startswith("orchestrator/campaign/") and path.endswith(".py")
    )
    assert runtime_relatives
    runtime_source_root = tmp_path / "t080-post-r-current-runtime"
    for relative in runtime_relatives:
        _copy_t080_basis_file(runtime_source_root, relative)
    historical_runtime_bytes = {
        relative: (root / relative).read_bytes()
        for relative in runtime_relatives
    }
    child = textwrap.dedent("""
        import importlib
        import importlib.abc
        import importlib.util
        import json
        import sys
        from pathlib import Path

        root = Path(sys.argv[1]).resolve()
        runtime_source_root = Path(sys.argv[3]).resolve()
        runtime_relatives = tuple(json.loads(sys.argv[4]))
        runtime_modules = {
            ".".join(Path(relative).with_suffix("").parts): relative
            for relative in runtime_relatives
        }

        class _CurrentSourceLoader(importlib.abc.Loader):
            def __init__(self, fullname, repository_path, source_path):
                self.fullname = fullname
                self.repository_path = repository_path
                self.source_path = source_path

            def create_module(self, spec):
                return None

            def exec_module(self, module):
                source = self.source_path.read_bytes()
                code = compile(source, str(self.repository_path), "exec")
                exec(code, module.__dict__)

        class _CurrentSourceFinder(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                relative = runtime_modules.get(fullname)
                if relative is None:
                    return None
                repository_path = root / relative
                source_path = runtime_source_root / relative
                loader = _CurrentSourceLoader(
                    fullname, repository_path, source_path,
                )
                spec = importlib.util.spec_from_loader(
                    fullname, loader, origin=str(repository_path),
                )
                assert spec is not None
                spec.has_location = True
                return spec

        sys.meta_path.insert(0, _CurrentSourceFinder())
        sys.path[0] = str(root)
        from orchestrator.campaign import t080_freeze_migration as migration
        for module_name in sorted(runtime_modules):
            importlib.import_module(module_name)
        loaded_runtime_modules = tuple(
            sys.modules[module_name] for module_name in sorted(runtime_modules)
        )
        assert all(
            type(module.__loader__) is _CurrentSourceLoader
            for module in loaded_runtime_modules
        ), loaded_runtime_modules
        try:
            migration.draft_receipt(
                basis=sys.argv[2], out=migration.DRAFT_REL, root=root,
            )
        except migration.MigrationError as exc:
            print(json.dumps({"reason": exc.reason, "detail": exc.detail}))
        else:
            raise AssertionError("post-R 再発行が拒否されなかった")
    """)
    completed = subprocess.run(
        [sys.executable, "-I", "-B", "-c", child, str(root), basis,
         str(runtime_source_root), json.dumps(runtime_relatives)],
        cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True,
        env={
            **_sanitized_git_env(),
            "PYTHONPATH": "",
            "PYTHONNOUSERSITE": "1",
        },
    )
    assert {
        relative: (root / relative).read_bytes()
        for relative in runtime_relatives
    } == historical_runtime_bytes
    refusal = json.loads(completed.stdout)
    assert refusal["reason"] == "receipt.invalid"
    assert "issued-but-missing" in refusal["detail"]


@contextlib.contextmanager
def _t080_static_checks_pass():
    """U1 の結線に直交する U0 の重い静的検査だけを合格へ固定する。"""
    with mock.patch.multiple(
        migration,
        _validate_repin_report_git=mock.DEFAULT,
        _validate_positive_control=mock.DEFAULT,
        _verify_ccbench_current=mock.DEFAULT,
        _verify_ccbench_basis_from_receipt=mock.DEFAULT,
        _verify_known_closure=mock.DEFAULT,
        _verify_holdout_closure=mock.DEFAULT,
        _verify_metadata_closure=mock.DEFAULT,
        _verify_reconstruction_static=mock.DEFAULT,
        _verify_receipt_derivation=mock.DEFAULT,
        _verify_known_schema=mock.DEFAULT,
        _verify_known_pairing=mock.DEFAULT,
        _verify_holdout_live_scan=mock.DEFAULT,
    ) as patched:
        for name, mocked in patched.items():
            mocked.return_value = {} if name == "_verify_holdout_live_scan" else None
        yield


_LEGACY_HOLDOUT_REFUSAL = "holdout-freeze-verify: FreezeError: fixture holdout drift"
_LEGACY_KNOWN_REFUSAL = "known-axes-freeze-verify: FreezeError: fixture known drift"
_FLOOR_REFUSAL = "floor-null: freeze.floor が null"
_BUDGET_REFUSAL = "budget-null: freeze.budget が null"


@contextlib.contextmanager
def _legacy_four_refusals():
    """legacy 2 診断を安定 payload にし、floor/budget と合わせて exact 化する。"""
    with mock.patch.object(
            driver.s8b_holdout_freeze, "verify",
            side_effect=driver.s8b_holdout_freeze.FreezeError("fixture holdout drift")), \
            mock.patch.object(
                driver.s1_known_axes_freeze, "verify",
                side_effect=driver.s1_known_axes_freeze.FreezeError("fixture known drift")):
        yield


def _contract_sha256() -> str:
    return ec.lookup(V2_ENV_TAG).contract_sha256


def test_machine_env_tag_for_site_uses_required_registry_contract(monkeypatch):
    expected_tags = {
        contract.env_tag
        for contract in ec.REGISTRY.values()
        if contract.attestation_mode == "required"
    }
    assert len(expected_tags) == 1
    monkeypatch.setattr(
        driver.site_policy,
        "current_site",
        lambda: driver.site_policy.PEGASUS_COMPUTE,
    )
    observed_site = driver.site_policy.current_site()
    assert observed_site == driver.site_policy.PEGASUS_COMPUTE
    assert driver._machine_env_tag_for_site(observed_site) == next(iter(expected_tags))


def test_machine_env_tag_for_site_rejects_zero_required_contracts(monkeypatch):
    monkeypatch.setattr(
        driver.site_policy,
        "current_site",
        lambda: driver.site_policy.PEGASUS_COMPUTE,
    )
    monkeypatch.setattr(driver._env_contract, "REGISTRY", {})
    with pytest.raises(driver.OracleDriverError, match="required attestation"):
        driver._machine_env_tag_for_site(driver.site_policy.current_site())


def test_machine_env_tag_for_site_rejects_multiple_required_contracts(monkeypatch):
    monkeypatch.setattr(
        driver.site_policy,
        "current_site",
        lambda: driver.site_policy.PEGASUS_COMPUTE,
    )
    monkeypatch.setattr(
        driver._env_contract,
        "REGISTRY",
        {
            "required-first": SimpleNamespace(
                env_tag="fixture-required-first", attestation_mode="required",
            ),
            "required-second": SimpleNamespace(
                env_tag="fixture-required-second", attestation_mode="required",
            ),
        },
    )
    with pytest.raises(driver.OracleDriverError, match="required attestation"):
        driver._machine_env_tag_for_site(driver.site_policy.current_site())


def test_machine_env_tag_for_site_rejects_required_lookup_exception(monkeypatch):
    monkeypatch.setattr(
        driver.site_policy,
        "current_site",
        lambda: driver.site_policy.PEGASUS_COMPUTE,
    )

    def fail_required_lookup():
        raise ec.EnvContractError("fixture required lookup failure")

    monkeypatch.setattr(
        driver._env_contract,
        "lookup_required_attestation_contract",
        fail_required_lookup,
    )
    with pytest.raises(driver.OracleDriverError, match="required attestation"):
        driver._machine_env_tag_for_site(driver.site_policy.current_site())


def test_machine_env_tag_for_site_uses_unique_none_registry_contract(monkeypatch):
    expected_tags = {
        contract.env_tag
        for contract in ec.REGISTRY.values()
        if contract.attestation_mode == "none"
    }
    assert len(expected_tags) == 1
    monkeypatch.setattr(
        driver.site_policy,
        "current_site",
        lambda: driver.site_policy.OTHER,
    )
    observed_site = driver.site_policy.current_site()
    assert observed_site == driver.site_policy.OTHER
    assert driver._machine_env_tag_for_site(observed_site) == next(iter(expected_tags))


def test_machine_env_tag_for_site_rejects_zero_none_contracts(monkeypatch):
    monkeypatch.setattr(
        driver.site_policy,
        "current_site",
        lambda: driver.site_policy.OTHER,
    )
    monkeypatch.setattr(driver._env_contract, "REGISTRY", {})
    with pytest.raises(driver.OracleDriverError, match="none attestation"):
        driver._machine_env_tag_for_site(driver.site_policy.current_site())


def test_machine_env_tag_for_site_rejects_multiple_none_contracts(monkeypatch):
    monkeypatch.setattr(
        driver.site_policy,
        "current_site",
        lambda: driver.site_policy.OTHER,
    )
    monkeypatch.setattr(
        driver._env_contract,
        "REGISTRY",
        {
            "first": SimpleNamespace(env_tag="fixture-none-first", attestation_mode="none"),
            "second": SimpleNamespace(env_tag="fixture-none-second", attestation_mode="none"),
        },
    )
    with pytest.raises(driver.OracleDriverError, match="none attestation"):
        driver._machine_env_tag_for_site(driver.site_policy.current_site())


def test_machine_env_tag_for_site_rejects_duplicate_registry_env_tag(monkeypatch):
    monkeypatch.setattr(
        driver.site_policy,
        "current_site",
        lambda: driver.site_policy.OTHER,
    )
    monkeypatch.setattr(
        driver._env_contract,
        "REGISTRY",
        {
            "none": SimpleNamespace(
                env_tag="fixture-duplicate", attestation_mode="none",
            ),
            "required": SimpleNamespace(
                env_tag="fixture-duplicate", attestation_mode="required",
            ),
        },
    )
    with pytest.raises(driver.OracleDriverError, match="none attestation"):
        driver._machine_env_tag_for_site(driver.site_policy.current_site())


def test_machine_env_tag_for_site_rejects_unhandled_site(monkeypatch):
    monkeypatch.setattr(
        driver.site_policy,
        "current_site",
        lambda: driver.site_policy.PEGASUS_LOGIN,
    )
    with pytest.raises(driver.OracleDriverError, match="未対応 site"):
        driver._machine_env_tag_for_site(driver.site_policy.current_site())


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _real_document() -> dict:
    return json.loads(REAL_FREEZE.read_text(encoding="utf-8"))


def _holdout_ids() -> tuple[str, ...]:
    return tuple(_real_document()["holdouts"])


def _synthetic_freeze(tmp_path: Path, *, total_bench_s: float = 1000.0) -> Path:
    document = _real_document()
    # 並行中の設計再凍結 draft は freeze 生成後の未コミット差分なので、fixture は
    # 現在の source byte を記録して provenance 検査を通す。
    design = ROOT / document["design_source"]["path"]
    document["design_source"]["sha256"] = _sha256(design)
    # strict v2: per-pair floor + budget を共有 fixture で充填する (C3-4)。
    v2_fixture.fill(
        document, total_bench_s=total_bench_s, per_holdout_bench_s=total_bench_s,
    )
    path = tmp_path / "holdout_freeze.json"
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    return path


def _floor_only_freeze(tmp_path: Path) -> Path:
    document = _real_document()
    design = ROOT / document["design_source"]["path"]
    document["design_source"]["sha256"] = _sha256(design)
    # floor だけ per-pair で充填し budget は null のまま (v2 refusal 経路の fixture)。
    document["floor"] = v2_fixture.per_pair_floor(document)
    path = tmp_path / "holdout_freeze_floor_only.json"
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    return path


@functools.lru_cache(maxsize=None)
def _issued_condition_records(
        flags: tuple[tuple[str, object], ...], driver_id: str,
):
    records = s1_condition_fixtures._issued_condition_records(flags, driver_id)
    if not records[0] and not records[1]:
        return records
    admission = s1_condition_fixtures._assert_promotion_admission_contract(
        *records, use_class="oracle",
    )
    assert admission.admitted is True
    return records


def _condition_records(
        genome: Genome,
        driver_id: str = "orchestrator.campaign.s1_direct_comparison.prepare_cell",
):
    return _issued_condition_records(
        tuple(sorted(genome.flags.items())), driver_id,
    )


def _with_condition_records(result):
    supply, meaning = _condition_records(result.genome)
    result.condition_supply_records = supply
    result.condition_meaning_records = meaning
    return result


def _prepare_factory(
    *, fail_first: bool = False, token_suffix: str = "",
    suffix_first_only: bool = False,
):
    from orchestrator.campaign.sort_swo_oracle import ORACLE_CONTRACT_ID

    calls: list[dict] = []

    @contextlib.contextmanager
    def fake_prepare(cell, ccbench_pin, *, cxx):
        calls.append({"cell": cell, "ccbench_pin": ccbench_pin, "cxx": cxx})
        if fail_first and len(calls) == 1:
            raise OSError("transient checkout failure")
        entry = cell["variant"]
        genome = Genome("silo", dict(entry["flags"]))
        token = "fixture-" + hashlib.sha256(
            json.dumps(entry, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        if not suffix_first_only or len(calls) == 1:
            token += token_suffix
        supply, meaning = _condition_records(genome)
        yield PreparedCell(
            genome=genome, src_token=token,
            ccbench_dir="/tmp/fixture-ccbench", cache_root="/tmp/fixture-cache",
            condition_supply_records=supply,
            condition_meaning_records=meaning,
            sort_oracle_contract_id=(
                ORACLE_CONTRACT_ID
                if cell["configuration"] == "sort_best" else None
            ),
        )

    fake_prepare.calls = calls
    return fake_prepare


@pytest.fixture(autouse=True)
def _synthetic_materialization_for_oracle_fixtures(monkeypatch, request):
    """Oracle の synthetic identity fixture を filesystem gate から分離する。"""
    if request.node.name.startswith("test_slow_oracle_"):
        return

    @contextlib.contextmanager
    def fixture_prepared_binding(
            *, freeze, holdout_id, configuration_id, ccbench_pin, cxx,
            prepare_fn):
        entry = s8b_materialization.binding_entry(
            freeze, holdout_id, configuration_id,
        )
        resource = prepare_fn(
            {"configuration": configuration_id, "variant": entry},
            ccbench_pin, cxx=cxx,
        )
        manager = (
            resource if hasattr(resource, "__enter__")
            else contextlib.nullcontext(resource)
        )
        with manager as prepared:
            yield s8b_materialization.binding_from_prepared(
                entry, prepared,
            ), prepared

    def fixture_prepare_binding(**kwargs):
        with fixture_prepared_binding(**kwargs) as (identity, _prepared):
            return identity

    monkeypatch.setattr(
        s8b_materialization, "prepare_binding", fixture_prepare_binding,
    )
    monkeypatch.setattr(
        driver, "_materialization_prepared_binding",
        fixture_prepared_binding,
    )


def _schedule(*, master_seed="driver-fixture") -> dict:
    return manifest_module.build_schedule(
        n=1, master_seed=master_seed, block_sizes={"b0": 1},
        holdout_ids=_holdout_ids(), configuration_ids=CONFIGURATIONS,
    )


def _source(path: str, *, root=ROOT) -> dict:
    source = Path(root) / path
    return {"path": path, "sha256": _sha256(source)}


def _write_manifest(tmp_path: Path, freeze_path: Path, prepare_fn,
                    *, source_root=ROOT, generator_paths=None,
                    contract=None, master_seed="driver-fixture",
                    activate_approved=True, name="oracle_manifest.json",
                    campaign_id="s8b-oracle-fixture-b0",
                    ccbench_pin="fixture-pin") -> tuple[Path, dict]:
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    schedule = _schedule(master_seed=master_seed)
    bindings = []
    for holdout_id in _holdout_ids():
        for configuration_id in CONFIGURATIONS:
            identity = s8b_materialization.prepare_binding(
                freeze=freeze, holdout_id=holdout_id,
                configuration_id=configuration_id,
                ccbench_pin=ccbench_pin, cxx="site-cxx",
                prepare_fn=prepare_fn,
            )
            bindings.append({
                "holdout_id": holdout_id,
                "configuration_id": configuration_id,
                **identity,
            })
    if generator_paths is None:
        generator_paths = GENERATOR_SOURCES
    contract = contract or ec.lookup(V2_ENV_TAG)
    run_contract = {
        "ccbench_pin": ccbench_pin, "env_tag": contract.env_tag,
        "clocks": contract.clocks_per_us, "reps": 5, "extime": 5,
        "verify": "legacy+s2", "screening": "off",
        "bench_max_rounds": 1,
        "contract_sha256": contract.contract_sha256,
    }
    generators = {
        role: _source(generator_paths[role], root=source_root)
        for role in GENERATOR_SOURCES
    }
    approved = spec_fixture.make_reviewed_spec(
        root=source_root, n=1, master_seed=master_seed,
        block_sizes={"b0": 1}, holdout_ids=_holdout_ids(),
        configuration_ids=CONFIGURATIONS, run_contract=run_contract,
        campaign_ids={"b0": campaign_id},
        binding_identity=bindings,
        allowed_excluded_reasons=["machine-failure"],
        generator_versions=generators,
    )
    global _ACTIVE_APPROVED
    if activate_approved:
        _ACTIVE_APPROVED = approved
    document = manifest_module._build_manifest(
        freeze_path=freeze_path,
        spec_sha256=approved.sha256,
        schedule=schedule,
        run_contract=run_contract,
        binding_identity=bindings,
        campaign_ids={"b0": campaign_id},
        allowed_excluded_reasons=["machine-failure"],
        generator_versions=generators,
    )
    path = tmp_path / name
    manifest_module._write_manifest(path, document)
    _APPROVED_BY_PATH[path.resolve()] = approved
    return path, document


def _verify_manifest(path, *, root, freeze_document, freeze_sha256):
    approved = _APPROVED_BY_PATH[Path(path).resolve()]
    with mock.patch.object(
            oracle_spec, "APPROVED_SPEC_SHA256", approved.sha256):
        return manifest_module.verify_manifest(
            path, root=root, freeze_document=freeze_document,
            freeze_sha256=freeze_sha256,
            approved_spec=approved.reviewed_spec,
        )


def _fake_evaluate_factory(*, bench_wall_s: float = 0.25):
    calls: list[dict] = []

    def fake_evaluate(genome, layout, env_tag, ccbench_commit, perf,
                      clocks_per_us, **kwargs):
        calls.append({
            "genome": genome, "layout": layout, "env_tag": env_tag,
            "ccbench_commit": ccbench_commit, "perf": perf,
            "clocks_per_us": clocks_per_us, "kwargs": kwargs,
        })
        variant = pipeline.variant_id(genome, kwargs["src_token"])
        attempt_id = f"s8b-{len(calls)}-{variant}"
        wal.log(layout, variant, "build_start", env_tag, {
            "genome": genome.canonical(), "src_token": kwargs["src_token"],
            "build_attempt_id": attempt_id,
        })
        wal.log(layout, variant, "build_done", env_tag, {
            "trace_bin": "trace", "perf_bin": "perf",
            "build_attempt_id": attempt_id,
        })
        for tag in (pipeline.LEGACY_TAG, pipeline.S2_TAG):
            wal.log(layout, variant, "verify_done", env_tag, {
                "build_attempt_id": attempt_id,
                "verdict": "serializable", "certified": True,
                "anomalies": 0,
                "workload": {"tag": tag},
            })
        bench_payload = {
            "tps": [10.0, 11.0, 12.0, 13.0, 14.0], "median_tps": 12.0,
            "bench_wall_s": bench_wall_s, "build_attempt_id": attempt_id,
        }
        if kwargs.get("record_rep_returncodes") is True:
            bench_payload["rep_returncodes"] = [0, 0, 0, 0, 0]
        wal.log(layout, variant, "bench_done", env_tag, bench_payload)
        receipt_support.log_receipted_commit(
            layout, variant, env_tag, {
            "fitness_tps": 12.0,
            "verify_configs": [pipeline.LEGACY_TAG, pipeline.S2_TAG],
            "build_attempt_id": attempt_id,
            },
            operation_identity=attempt_id,
            tags=(pipeline.LEGACY_TAG, pipeline.S2_TAG),
        )
        return _with_condition_records(pipeline.EvalResult(
            genome=genome, variant=variant, certified=True, aborted=False,
            fitness_tps=12.0,
        ))

    fake_evaluate.calls = calls
    return fake_evaluate


def _fake_abort_evaluate_factory(reason: str):
    calls: list[dict] = []

    def fake_evaluate(genome, layout, env_tag, ccbench_commit, perf,
                      clocks_per_us, **kwargs):
        calls.append({"reason": reason})
        variant = pipeline.variant_id(genome, kwargs["src_token"])
        wal.log(layout, variant, "build_start", env_tag, {
            "genome": genome.canonical(), "src_token": kwargs["src_token"],
        })
        wal.log(layout, variant, "build_done", env_tag, {
            "trace_bin": "trace", "perf_bin": "perf",
        })
        wal.log(layout, variant, "abort", env_tag, {
            "reason": reason, "workload": {"tag": pipeline.LEGACY_TAG},
        })
        return _with_condition_records(pipeline.EvalResult(
            genome=genome, variant=variant, certified=False, aborted=True,
        ))

    fake_evaluate.calls = calls
    return fake_evaluate


def _canned_plan(**kwargs) -> "driver._V2Plan":
    """WAL/budget 契約テスト用の canned v2 plan (git/store の実検査を迂回)。

    _prepare_v2_execution の差し替えとして使う。渡された ``schedule`` kwarg から cell を
    列挙するため manifest/freeze を再読しない (read カウント系テストを汚さない)。contract は
    実 env 契約 lookup (clocks/numactl の正本)、receipt は実 guard 生成、perf_sha_by_cell は
    全 cell を dummy 64hex で埋める (fake evaluate は expected_perf_sha256 を捕捉するだけ)。"""
    contract = ec.lookup(V2_ENV_TAG)
    perf = {
        (row["holdout_id"], row["configuration_id"]): "0" * 64
        for row in kwargs["schedule"]
    }
    return driver._V2Plan(
        contract=contract,
        authorization_contract=ec.authorize(V2_ENV_TAG),
        receipt=execution_guard.build_receipt(contract),
        perf_sha_by_cell=perf,
    )


def _fake_launch_validated(freeze_path: Path, *, env_tag=None):
    """WAL/budget unit 用の LaunchValidatedFreeze 型境界 fixture。"""
    raw = Path(freeze_path).read_bytes()
    document = json.loads(raw)
    if env_tag is not None:
        document["env_tag"] = env_tag
    ratified = s8b_ratified_freeze.RatifiedFreeze(
        document=document, sha256=hashlib.sha256(raw).hexdigest(),
        generation_number=1, activation_head="f" * 40,
        generation_commit="e" * 40,
    )
    floor = s8b_ratified_freeze.VerifiedFloorArtifact(
        path="fixture/result.json", raw_bytes=b"{}",
        sha256=hashlib.sha256(b"{}").hexdigest(), document={},
    )
    return s8b_ratified_freeze.LaunchValidatedFreeze(
        ratified=ratified, activation_head=ratified.activation_head,
        search_digest="d" * 64, symlink_gitlink_inventory=(),
        floor_artifact=floor, binaries_by_cell={},
    )


def test_gate_check_core_rejects_reverified_freeze_token(tmp_path):
    """live gate core は historical token を exact type 境界で拒否する。"""
    freeze_path = tmp_path / "freeze.json"
    freeze_path.write_text("{}\n", encoding="utf-8")
    live = _fake_launch_validated(freeze_path)
    historical = s8b_ratified_freeze.ReverifiedFreeze(
        ratified=live.ratified,
        activation_head=live.activation_head,
        search_digest=live.search_digest,
        symlink_gitlink_inventory=live.symlink_gitlink_inventory,
        floor_artifact=live.floor_artifact,
        binaries_by_cell=live.binaries_by_cell,
    )
    resolution = migration.ReceiptResolution(
        "never-issued", (), None, "a" * 40,
    )

    decision = driver._gate_check_core(
        freeze_path=freeze_path,
        root=tmp_path,
        t080_resolution=resolution,
        approved_spec=None,
        manifest_verification_error=None,
        standalone_manifest_verification=False,
        launch_validated=historical,
    )

    assert not decision.allowed
    _assert_exact_refusals(decision.refusals, {
        "v2-execution: launch-validate: validated freeze object の型が不正",
    })


def _required_contract(repo_root: Path):
    document = copy.deepcopy(_valid_calibration_v2())
    # U-2/U-3 による current admission の正当な縮小: required fixture は policy と一致させる。
    document["attestation_profile"]["effective_clock"]["tolerance_pct"] = 2.0
    raw = json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    sha256 = hashlib.sha256(raw).hexdigest()
    relative = Path(
        "output", "env", document["env_tag"], "calibration", "registered",
        f"calibration-{sha256[:16]}.json",
    )
    artifact = repo_root / relative
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(raw)
    contract = ec.ExecutionEnvironmentContract(
        env_tag=document["env_tag"], clocks_per_us=document["clocks_per_us"],
        numactl=(), attestation_mode="required",
        isolation_policy=ec.IsolationPolicy(single_process=True, allow_resume=False),
        calibration_ref=ec.CalibrationRef(
            path=relative.as_posix(), sha256=sha256,
        ),
    )
    verified = env_attestation.load_verified_calibration(contract, repo_root)
    return contract, verified


def _observed(profile):
    raw = env_attestation.profile_to_dict(profile)
    del raw["effective_clock"]["tolerance_pct"]
    return env_attestation.normalize_observed_profile(raw)


def _reservation_env(*, requested_s: int = 100_000) -> dict[str, str]:
    started = time.time() - 10
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
    return {
        "PBS_JOBID": "fixture.server",
        "IZANAGI_RESERVATION_JOB_ID": "fixture.server",
        "IZANAGI_RESERVATION_REQUESTED_S": str(requested_s),
        "IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH": str(started),
        "IZANAGI_RESERVATION_DEADLINE_EPOCH": str(started + requested_s),
        "IZANAGI_RESERVATION_HOST": "fixture-host",
        "IZANAGI_RESERVATION_BOOT_ID": boot_id,
        "IZANAGI_RESERVATION_SCRIPT_SHA256": "a" * 64,
        "IZANAGI_RESERVATION_NONCE": "fixture-nonce",
    }


def _durable_policy(path: Path):
    candidate = Path(path).absolute()
    approved = candidate
    while not approved.exists():
        approved = approved.parent
    return driver.DurableRootPolicy(
        approved_roots=(approved.resolve(),), forbidden_roots=(),
    )


@contextlib.contextmanager
def _isolated_oracle_admission_root(tmp_path: Path):
    admission_root = Path(tempfile.mkdtemp(
        prefix="oracle-admission-", dir=tmp_path,
    ))
    (admission_root / "claims").mkdir()
    (admission_root / "consumed").mkdir()
    (admission_root / "measurement-generation-claims").mkdir()
    (admission_root / "measurement-generation-consumed").mkdir()
    (admission_root / "ledger.lock").write_bytes(b"")
    with mock.patch.object(
            driver._holdout_admission,
            "provision_shared_admission_root",
            return_value=admission_root):
        yield admission_root


def _run(tmp_path: Path, freeze_path: Path, manifest_path: Path,
         prepare_fn, evaluate_fn, *, output_root=None, budget_path=None,
         marker_root=None, memo_receipt: bool = True):
    # driver 内部の WAL/budget 契約テストは v2 gate/launch/store/env の実検査を迂回し、
    # future-approved gate + canned v2 plan を代入して WAL・budget・schedule 契約だけを
    # 突く (v2 gate/store/env の実発火は専用テストが git fixture で検査する)。
    #
    # [T-057] root=ROOT のため run_block は実 repo の T-080 receipt を解決する
    # (1 回 22.4 秒 = git subprocess 1845 本、commit 数に比例)。この経路の consumer は
    # receipt 解決が incidental (対象は WAL / budget / schedule 契約) なので、実解決値を
    # process 内 memo で共有する。**解決の回数や世代差そのものを検査する node は
    # `memo_receipt=False` を渡すこと** (memo はその機序を消す)。
    validated = _fake_launch_validated(freeze_path)
    with contextlib.ExitStack() as stack:
        if memo_receipt:
            stack.enter_context(receipt_memo.patch_driver_resolver())
        stack.enter_context(mock.patch.object(
            driver, "_gate_check_validated",
            return_value=driver.GateDecision(True, [], None)))
        stack.enter_context(mock.patch.object(
            driver.s8b_ratified_freeze, "load_ratified_freeze",
            return_value=validated.ratified))
        stack.enter_context(mock.patch.object(
            driver.s8b_ratified_freeze, "launch_validate",
            return_value=validated))
        stack.enter_context(
            mock.patch.object(driver, "_prepare_v2_execution", _canned_plan))
        stack.enter_context(_isolated_oracle_admission_root(tmp_path))
        return driver.run_block(
            manifest_path=manifest_path, block_id="b0",
            freeze_path=freeze_path, root=ROOT,
            output_root=output_root or (tmp_path / "out"),
            budget_path=budget_path or (tmp_path / "budget.json"),
            marker_root=marker_root or (tmp_path / "markers"),
            prepare_fn=prepare_fn, evaluate_fn=evaluate_fn,
        )


def _run_with_real_manifest_gate(
        *, root, freeze_path, manifest_path, output_root, budget_path,
        marker_root, prepare_fn, evaluate_fn):
    validated = _fake_launch_validated(freeze_path)
    with mock.patch.object(
            driver, "_resolve_t080_receipt",
            return_value=_never_issued_resolution()), mock.patch.object(
            driver.s8b_ratified_freeze, "load_ratified_freeze",
            return_value=validated.ratified), mock.patch.object(
            driver.s8b_ratified_freeze, "launch_validate",
            return_value=validated), mock.patch.object(
            driver.s1_known_axes_freeze, "verify", return_value=None), mock.patch.object(
            driver, "_prepare_v2_execution", side_effect=_canned_plan), \
            _isolated_oracle_admission_root(Path(output_root).parent):
        return driver.run_block(
            manifest_path=manifest_path, block_id="b0",
            freeze_path=freeze_path, root=root,
            output_root=output_root, budget_path=budget_path,
            marker_root=marker_root,
            prepare_fn=prepare_fn, evaluate_fn=evaluate_fn,
        )


def test_oracle_evaluate_fn_without_condition_records_cannot_complete(tmp_path):
    freeze_path = _synthetic_freeze(tmp_path, total_bench_s=1000.0)
    prepare_fn = _prepare_factory()
    manifest_path, _document = _write_manifest(
        tmp_path, freeze_path, prepare_fn,
    )
    prepare_fn.calls.clear()
    recorded_evaluate = _fake_evaluate_factory()

    def evidence_less_evaluate(*args, **kwargs):
        result = recorded_evaluate(*args, **kwargs)
        del result.condition_supply_records
        del result.condition_meaning_records
        return result

    with pytest.raises(driver.OracleDriverError, match="condition evidence"):
        _run(
            tmp_path, freeze_path, manifest_path,
            prepare_fn, evidence_less_evaluate,
        )


def test_spec_matching_gate_and_run_reach_execution_but_other_spec_refuses_without_outputs(
        tmp_path):
    freeze_path = _synthetic_freeze(tmp_path, total_bench_s=1000.0)
    positive_prepare = _prepare_factory()
    positive_manifest, _ = _write_manifest(
        tmp_path, freeze_path, positive_prepare, name="manifest-a.json",
    )
    approved_a = _ACTIVE_APPROVED
    positive_prepare.calls.clear()
    positive_eval = _fake_evaluate_factory()
    validated = _fake_launch_validated(freeze_path)
    with mock.patch.object(
            driver, "_resolve_t080_receipt",
            return_value=_never_issued_resolution()), mock.patch.object(
            driver.s8b_ratified_freeze, "load_ratified_freeze",
            return_value=validated.ratified), mock.patch.object(
            driver.s8b_ratified_freeze, "launch_validate",
            return_value=validated), mock.patch.object(
            driver.s1_known_axes_freeze, "verify", return_value=None):
        allowed = driver.gate_check(
            freeze_path=freeze_path, manifest_path=positive_manifest, root=ROOT,
        )
    assert allowed.allowed, allowed.refusals

    positive = _run_with_real_manifest_gate(
        root=ROOT, freeze_path=freeze_path, manifest_path=positive_manifest,
        output_root=tmp_path / "positive-out",
        budget_path=tmp_path / "positive-budget.json",
        marker_root=tmp_path / "positive-markers",
        prepare_fn=positive_prepare, evaluate_fn=positive_eval,
    )
    assert positive["status"] == "completed", positive
    assert positive_prepare.calls and positive_eval.calls

    negative_prepare = _prepare_factory()
    negative_manifest, _ = _write_manifest(
        tmp_path, freeze_path, negative_prepare,
        master_seed="driver-fixture-other-spec", activate_approved=False,
        name="manifest-b.json",
    )
    assert _ACTIVE_APPROVED is approved_a
    negative_prepare.calls.clear()
    negative_eval = _fake_evaluate_factory()
    negative_out = tmp_path / "negative-out"
    negative_budget = tmp_path / "negative-budget.json"
    negative_markers = tmp_path / "negative-markers"
    refused = _run_with_real_manifest_gate(
        root=ROOT, freeze_path=freeze_path, manifest_path=negative_manifest,
        output_root=negative_out, budget_path=negative_budget,
        marker_root=negative_markers,
        prepare_fn=negative_prepare, evaluate_fn=negative_eval,
    )
    assert refused["status"] == "refused"
    assert not refused["allowed"]
    assert len(refused["refusals"]) == 1
    assert refused["refusals"][0].startswith("manifest-verify:")
    assert negative_prepare.calls == []
    assert negative_eval.calls == []
    assert not negative_out.exists()
    assert not negative_budget.exists()
    assert not negative_markers.exists()


@pytest.mark.parametrize(
    ("axis", "message"),
    [
        ("exact-type", "VerifiedManifest exact type"),
        ("file-hash", "実 bytes/document と不一致"),
        ("document-hash", "実 bytes/document と不一致"),
        ("spec-hash", "approved spec と不一致"),
    ],
)
def test_gate_check_rebinds_each_injected_verified_manifest_axis(
        tmp_path, axis, message):
    global _ACTIVE_APPROVED
    freeze_path = _synthetic_freeze(tmp_path, total_bench_s=1000.0)
    prepare = _prepare_factory()
    manifest_path, _ = _write_manifest(
        tmp_path, freeze_path, prepare, name="injection-a.json",
    )
    approved_a = _ACTIVE_APPROVED
    verified = _verify_manifest(
        manifest_path, root=ROOT,
        freeze_document=json.loads(freeze_path.read_text(encoding="utf-8")),
        freeze_sha256=hashlib.sha256(freeze_path.read_bytes()).hexdigest(),
    )
    validated = _fake_launch_validated(freeze_path)

    def gate(candidate):
        return driver.gate_check(
            freeze_path=freeze_path, manifest_path=manifest_path, root=ROOT,
            verified_manifest=candidate,
        )

    with mock.patch.object(
            driver, "_resolve_t080_receipt",
            return_value=_never_issued_resolution()), mock.patch.object(
            driver.s8b_ratified_freeze, "load_ratified_freeze",
            return_value=validated.ratified), mock.patch.object(
            driver.s8b_ratified_freeze, "launch_validate",
            return_value=validated), mock.patch.object(
            driver.s1_known_axes_freeze, "verify", return_value=None):
        accepted = gate(verified)
        assert accepted.allowed, accepted.refusals

        candidate = verified
        if axis == "exact-type":
            candidate = mock.Mock(
                document=verified.document, sha256=verified.sha256,
            )
        elif axis == "file-hash":
            changed = json.loads(manifest_path.read_text(encoding="utf-8"))
            changed["manifest_id"] = "changed-file-manifest-id"
            manifest_path.write_text(
                json.dumps(changed, ensure_ascii=False), encoding="utf-8",
            )
        elif axis == "document-hash":
            verified.document["manifest_id"] = "changed-token-document-id"
        elif axis == "spec-hash":
            _write_manifest(
                tmp_path, freeze_path, _prepare_factory(),
                master_seed="injection-other-spec",
                name="injection-other-authority.json",
            )
            assert _ACTIVE_APPROVED is not approved_a

        decision = gate(candidate)

    assert not decision.allowed
    assert len(decision.refusals) == 1
    assert message in decision.refusals[0]


def _run_required_preflight(
        tmp_path: Path, *, activate_authority, receipt_issuer=None, verified_override=None,
        environ: dict[str, str] | None = None):
    """run_block production entry から required preflight を実発火する。"""
    contract, verified = _required_contract(tmp_path)
    authorization = activate_authority(
        contract, repo_root=tmp_path, authority_dir=tmp_path / "authority",
    )
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, manifest_document = _write_manifest(
        tmp_path, freeze_path, prepare_fn, contract=contract,
    )
    verified_freeze = s8b_freeze_io.load_verified_freeze(freeze_path)
    verified_manifest = _verify_manifest(
        manifest_path,
        root=ROOT,
        freeze_document=verified_freeze.document,
        freeze_sha256=verified_freeze.sha256,
    )
    validated = _fake_launch_validated(freeze_path, env_tag=contract.env_tag)
    issuer = receipt_issuer
    if issuer is None:
        original = execution_guard.attest_and_build_receipt

        def issuer(receipt_contract, receipt_verified):
            return original(
                receipt_contract, receipt_verified,
                probe_fn=lambda: _observed(receipt_verified.attestation_profile),
            )

    env = _reservation_env() if environ is None else environ
    output_root = tmp_path / "required-out"
    budget_path = tmp_path / "required-budget.json"
    marker_root = tmp_path / "required-markers"
    with mock.patch.object(driver, "_gate_check_validated",
                           return_value=driver.GateDecision(True, [], None)), \
            mock.patch.object(driver, "_resolve_t080_receipt",
                              return_value=_never_issued_resolution()), \
            mock.patch.object(driver.s8b_ratified_freeze, "load_ratified_freeze",
                              return_value=validated.ratified), \
            mock.patch.object(driver.s8b_ratified_freeze, "launch_validate",
                              return_value=validated), \
            mock.patch.object(driver, "verify_manifest", return_value=verified_manifest), \
            mock.patch.object(
                driver._env_contract, "authorize",
                return_value=authorization,
            ), \
            mock.patch.object(
                driver.site_policy, "current_site",
                return_value=driver.site_policy.PEGASUS_COMPUTE,
            ), \
            mock.patch.object(driver._env_attestation, "load_verified_calibration",
                              return_value=(verified_override or verified)), \
            mock.patch.object(driver.execution_guard, "attest_and_build_receipt",
                              side_effect=issuer), \
            mock.patch.dict(os.environ, env, clear=True), \
            _isolated_oracle_admission_root(tmp_path):
        result = driver.run_block(
            manifest_path=manifest_path, block_id="b0", freeze_path=freeze_path,
            root=tmp_path, output_root=output_root, budget_path=budget_path,
            marker_root=marker_root, prepare_fn=prepare_fn,
            evaluate_fn=_fake_evaluate_factory(),
        )
    return result, output_root, budget_path, marker_root, contract, verified


def _required_plan(contract, verified, schedule, environ, authorization):
    original = execution_guard.attest_and_build_receipt
    receipt = original(
        contract, verified, probe_fn=lambda: _observed(verified.attestation_profile),
    )
    binding = driver._reservation.read_binding(environ)
    check = driver._reservation.check_reservation(
        binding, required_s=driver._reservation_required_s(schedule),
        safety_margin_s=driver.ORACLE_RESERVATION_SAFETY_MARGIN_S,
        environ=environ,
    )
    return driver._V2Plan(
        contract=contract,
        authorization_contract=authorization,
        receipt=receipt,
        perf_sha_by_cell={
            (row["holdout_id"], row["configuration_id"]): "0" * 64
            for row in schedule
        },
        verified_calibration=verified, reservation_check=check,
    )


def _required_run_fixture(tmp_path: Path, activate_authority):
    contract, verified = _required_contract(tmp_path)
    authorization = activate_authority(
        contract, repo_root=tmp_path, authority_dir=tmp_path / "authority",
    )
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, document = _write_manifest(
        tmp_path, freeze_path, prepare_fn, contract=contract,
    )
    prepare_fn.calls.clear()
    validated = _fake_launch_validated(freeze_path, env_tag=contract.env_tag)
    verified_freeze = s8b_freeze_io.load_verified_freeze(freeze_path)
    verified_manifest = _verify_manifest(
        manifest_path,
        root=ROOT,
        freeze_document=verified_freeze.document,
        freeze_sha256=verified_freeze.sha256,
    )
    environ = _reservation_env()
    plan = _required_plan(
        contract, verified, document["schedule"]["rows"], environ, authorization,
    )
    marker_root = tmp_path / "required-marker-root"
    marker_root.mkdir()
    output_root = tmp_path / "required-run-out"
    (output_root / "claims").mkdir(parents=True, mode=0o700)
    return {
        "root": tmp_path,
        "contract": contract, "verified": verified, "freeze_path": freeze_path,
        "manifest_path": manifest_path, "document": document,
        "prepare_fn": prepare_fn, "validated": validated,
        "verified_manifest": verified_manifest, "environ": environ, "plan": plan,
        "marker_root": marker_root, "output_root": output_root,
        "budget_path": tmp_path / "required-run-budget.json",
    }


def _run_required_fixture(fixture, *, receipt_side_effect=None, durable_policy=None):
    original_issuer = execution_guard.attest_and_build_receipt

    def default_issuer(contract, verified):
        return original_issuer(
            contract, verified, probe_fn=lambda: _observed(verified.attestation_profile),
        )

    issuer = receipt_side_effect or default_issuer
    with mock.patch.object(driver, "_gate_check_validated",
                           return_value=driver.GateDecision(True, [], None)), \
            mock.patch.object(driver, "_resolve_t080_receipt",
                              return_value=_never_issued_resolution()), \
            mock.patch.object(driver.s8b_ratified_freeze, "load_ratified_freeze",
                              return_value=fixture["validated"].ratified), \
            mock.patch.object(driver.s8b_ratified_freeze, "launch_validate",
                              return_value=fixture["validated"]), \
            mock.patch.object(driver, "verify_manifest",
                              return_value=fixture["verified_manifest"]), \
            mock.patch.object(driver, "_prepare_v2_execution",
                              return_value=fixture["plan"]), \
            mock.patch.object(driver.execution_guard, "attest_and_build_receipt",
                              side_effect=issuer), \
            mock.patch.dict(os.environ, fixture["environ"], clear=True), \
            _isolated_oracle_admission_root(fixture["root"]):
        return driver.run_block(
            manifest_path=fixture["manifest_path"], block_id="b0",
            freeze_path=fixture["freeze_path"], root=fixture["root"],
            output_root=fixture["output_root"], budget_path=fixture["budget_path"],
            marker_root=fixture["marker_root"], prepare_fn=fixture["prepare_fn"],
            evaluate_fn=_fake_evaluate_factory(),
            durable_root_policy=(durable_policy
                                 or _durable_policy(fixture["output_root"])),
        )


def test_cli_output_root_default_is_none_and_run_block_refuses_without_root(tmp_path):
    """CLI omission is fail-closed and is transported as a classified refusal."""
    parsed = driver._parser().parse_args([
        "run-block", "--manifest", str(tmp_path / "manifest.json"),
        "--block-id", "b0",
    ])
    assert parsed.output_root is None

    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, prepare_fn)
    validated = _fake_launch_validated(freeze_path)
    verified_manifest = _verify_manifest(
        manifest_path, root=ROOT, freeze_document=validated.ratified.document,
        freeze_sha256=validated.ratified.sha256,
    )
    budget_path = tmp_path / "missing-output-budget.json"
    marker_root = tmp_path / "missing-output-markers"
    with receipt_memo.patch_driver_resolver(), \
            mock.patch.object(
                driver, "_gate_check_validated",
                return_value=driver.GateDecision(True, [], None)), \
            mock.patch.object(
                driver.s8b_ratified_freeze, "load_ratified_freeze",
                return_value=validated.ratified), \
            mock.patch.object(
                driver.s8b_ratified_freeze, "launch_validate",
                return_value=validated), \
            mock.patch.object(
                driver, "verify_manifest", return_value=verified_manifest), \
            _isolated_oracle_admission_root(tmp_path):
        result = driver.run_block(
            manifest_path=manifest_path, block_id="b0", freeze_path=freeze_path,
            root=ROOT, output_root=None, budget_path=budget_path,
            marker_root=marker_root, prepare_fn=prepare_fn,
            evaluate_fn=_fake_evaluate_factory(),
        )

    assert result["status"] == "refused"
    assert result["allowed"] is False
    assert len(result["refusals"]) == 1
    assert result["refusals"][0].startswith("official-output-root: official output_root")
    assert not budget_path.exists()
    assert not marker_root.exists()


def test_main_injects_external_policy_and_required_run_writes_claim_wal_and_lock(
        tmp_path, _activate_synthetic_env_authority,
):
    """CLI policy wiring permits the already-admitted external required root."""
    fixture = _required_run_fixture(tmp_path, _activate_synthetic_env_authority)
    original_budget_path = driver.DEFAULT_BUDGET_PATH
    original_issuer = execution_guard.attest_and_build_receipt
    original_run_block = driver.run_block
    captured_result = {}
    evaluate_fn = _fake_evaluate_factory()

    def issuer(contract, verified):
        return original_issuer(
            contract, verified,
            probe_fn=lambda: _observed(verified.attestation_profile),
        )

    def run_block_wrapper(*args, **kwargs):
        result = original_run_block(*args, **kwargs)
        captured_result["value"] = result
        return result

    try:
        driver.DEFAULT_BUDGET_PATH = fixture["budget_path"]
        with mock.patch.object(driver, "_gate_check_validated",
                               return_value=driver.GateDecision(True, [], None)), \
                mock.patch.object(driver, "_resolve_t080_receipt",
                                  return_value=_never_issued_resolution()), \
                mock.patch.object(
                    driver.s8b_ratified_freeze, "load_ratified_freeze",
                    return_value=fixture["validated"].ratified), \
                mock.patch.object(
                    driver.s8b_ratified_freeze, "launch_validate",
                    return_value=fixture["validated"]), \
                mock.patch.object(
                    driver, "verify_manifest",
                    return_value=fixture["verified_manifest"]), \
                mock.patch.object(
                    driver, "_prepare_v2_execution",
                    return_value=fixture["plan"]), \
                mock.patch.object(
                    driver, "prepare_cell", fixture["prepare_fn"]), \
                mock.patch.object(
                    driver.pipeline, "evaluate", evaluate_fn), \
                mock.patch.object(
                    driver.execution_guard, "attest_and_build_receipt",
                    side_effect=issuer), \
                mock.patch.dict(os.environ, fixture["environ"], clear=True), \
                _isolated_oracle_admission_root(fixture["root"]), \
                mock.patch.object(
                    driver, "run_block", side_effect=run_block_wrapper,
                ) as call:
            rc = driver.main([
                "run-block", "--manifest", str(fixture["manifest_path"]),
                "--block-id", "b0", "--freeze", str(fixture["freeze_path"]),
                "--root", str(fixture["root"]),
                "--output-root", str(fixture["output_root"]),
            ])
            result = captured_result["value"]
            policy = call.call_args.kwargs["durable_root_policy"]
    finally:
        driver.DEFAULT_BUDGET_PATH = original_budget_path

    assert rc == 0, result
    assert result["status"] == "completed", result
    assert policy == driver.DurableRootPolicy(
        approved_roots=(fixture["output_root"].resolve(),), forbidden_roots=(),
    )
    claim_files = list((fixture["output_root"] / "claims").glob("*.claim"))
    assert len(claim_files) == 1
    campaign_root = (
        fixture["output_root"] / "campaigns" / result["campaign_id"]
    )
    assert (campaign_root / "campaign.lock").is_file()
    assert (campaign_root / "runs" / "wal.jsonl").is_file()


def test_real_freeze_gate_lists_floor_and_budget_null():
    independent = _independent_t080_receipt_blob(ROOT)
    assert independent is not None, (
        "real-repo T-080 gate test には full history が必要 (R が履歴に無い)"
    )
    introduction, raw = independent
    assert introduction == _T080_RECEIPT_INTRODUCTION
    assert hashlib.sha256(raw).hexdigest() == _T080_RECEIPT_RAW_SHA256
    # [T-057] この node は実 repo receipt の observation 自体が検査対象。実解決は collection
    # barrier の prewarm で本番 verify_receipt へ委譲されるので (canned 値は作らない)、
    # 検出力は変わらず gate_check 側の重複解決 (同 22.4 秒) だけが畳まれる。
    with receipt_memo.patch_driver_resolver():
        decision = driver.gate_check(freeze_path=REAL_FREEZE, root=ROOT)
    assert not decision.allowed
    resolution = receipt_memo.real_repo_receipt()
    assert resolution.state == "active-valid", resolution
    _assert_exact_refusals(decision.refusals, {
        _FLOOR_REFUSAL,
        _BUDGET_REFUSAL,
    })
    observation = decision.t080_freeze_migration_observation
    assert observation is None
    actual = resolution.t080_freeze_migration_observation
    validation_head = _run_git(ROOT, "rev-parse", "HEAD")
    expected_items = [
        {
            "artifact": artifact, "kind": "source-repin", "subject": pointer,
            "recorded": recorded, "observed": observed,
            "status": "repinned-to-basis-blob",
        }
        for artifact, pointer, recorded, _path, observed
        in _T080_REAL_REPO_SOURCE_GOLDEN
    ]
    expected_items.extend(
        {
            "artifact": artifact, "kind": "generator-metadata", "subject": pointer,
            "recorded": recorded, "observed": observed,
            "status": "metadata-only",
        }
        for artifact, pointer, recorded, _path, observed
        in _T080_REAL_REPO_METADATA_GOLDEN
    )
    expected_items.extend((
        _independent_ancestry_item(
            ROOT, artifact="known_axes",
            recorded="2066ce6b47c6a5d43ca2c8ab3cc7728d32336be1",
            validation_head=validation_head,
        ),
        _independent_ancestry_item(
            ROOT, artifact="holdout",
            recorded="2e20d441aaf7ae267e941ecda09e4b53050943cf",
            validation_head=validation_head,
        ),
    ))
    assert actual == {
        "schema_version": "izanagi-t080-freeze-migration-observation/v1",
        "migration_id": "T-080",
        "receipt": {
            "path": "output/t080-migration/legacy-freeze-repin.receipt.json",
            "raw_sha256": _T080_RECEIPT_RAW_SHA256,
        },
        "migration_basis_commit": _T080_MIGRATION_BASIS,
        "validation_head": validation_head,
        "items": expected_items,
    }


@pytest.mark.parametrize("receipt_state", ["never-issued", "active-valid", "invalid"])
def test_t080_gate_hermetic_primary_states_exact(tmp_path, receipt_state):
    fixture_state = {
        "never-issued": "never-issued",
        "active-valid": "active-valid",
        "invalid": "invalid",
    }[receipt_state]
    root, freeze_path = _t080_repo(tmp_path, receipt=fixture_state)
    verify_spy = mock.patch.object(
        migration, "verify_receipt", wraps=migration.verify_receipt,
    )
    with _t080_static_checks_pass(), verify_spy as verify_call:
        if receipt_state == "active-valid":
            legacy_context = contextlib.ExitStack()
            legacy_context.enter_context(mock.patch.object(
                driver.s8b_holdout_freeze, "verify",
                side_effect=AssertionError("active-valid で legacy holdout verifier を呼んだ"),
            ))
            legacy_context.enter_context(mock.patch.object(
                driver.s1_known_axes_freeze, "verify",
                side_effect=AssertionError("active-valid で legacy known verifier を呼んだ"),
            ))
        else:
            legacy_context = _legacy_four_refusals()
        with legacy_context:
            decision = driver.gate_check(freeze_path=freeze_path, root=root)

    assert verify_call.call_count == 1
    if receipt_state == "never-issued":
        _assert_exact_refusals(decision.refusals, {
            _LEGACY_HOLDOUT_REFUSAL,
            _LEGACY_KNOWN_REFUSAL,
            _FLOOR_REFUSAL,
            _BUDGET_REFUSAL,
        })
        assert decision.t080_freeze_migration_observation is None
    elif receipt_state == "active-valid":
        _assert_exact_refusals(decision.refusals, {_FLOOR_REFUSAL, _BUDGET_REFUSAL})
        assert decision.t080_freeze_migration_observation is None
    else:
        _assert_exact_refusals(decision.refusals, {
            "migration-receipt-verify: [receipt.confirmation_invalid] "
            "confirmed_by の形式が不正",
            _LEGACY_HOLDOUT_REFUSAL,
            _LEGACY_KNOWN_REFUSAL,
            _FLOOR_REFUSAL,
            _BUDGET_REFUSAL,
        })
        assert decision.t080_freeze_migration_observation is None


def test_gate_decision_is_built_only_by_factory_and_all_run_returns_propagate():
    """factory 外の直接構築と run_block return の observation 欠落を AST で拒否する。"""
    tree = ast.parse(inspect.getsource(driver))
    constructors = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if any(
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id == "GateDecision"
                for child in ast.walk(node)):
            constructors.append(node.name)
    assert constructors == ["_make_gate_decision"]

    assert sum(
        1 for node in ast.walk(tree)
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == "GateDecision")
    ) == 1

    run_node = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_block"
    )
    categories = []
    returns = sorted(
        (node for node in ast.walk(run_node) if isinstance(node, ast.Return)),
        key=lambda node: node.lineno,
    )
    for returned in returns:
        assert isinstance(returned.value, ast.Dict), returned.lineno
        literal_keys = {
            key.value for key in returned.value.keys
            if isinstance(key, ast.Constant) and isinstance(key.value, str)
        }
        via_asdict = any(
            key is None
            and isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "asdict"
            for key, value in zip(returned.value.keys, returned.value.values)
        )
        status = next((
            value.value for key, value in zip(returned.value.keys, returned.value.values)
            if (isinstance(key, ast.Constant) and key.value == "status"
                and isinstance(value, ast.Constant))
        ), None)
        if via_asdict:
            assert status == "refused"
            categories.append("refused-via-gate-decision")
            continue
        assert "t080_freeze_migration_observation" in literal_keys
        t080_value = next(
            value for key, value in zip(returned.value.keys, returned.value.values)
            if isinstance(key, ast.Constant)
            and key.value == "t080_freeze_migration_observation"
        )
        assert isinstance(t080_value, ast.Name) and t080_value.id == "t080_campaign_value"
        categories.append(status or "terminal-status-variable")
    assert categories == [
        *("refused-via-gate-decision" for _ in range(15)),
        "budget_exhausted_before_attempt",
        "terminal-status-variable",
    ]


@pytest.mark.parametrize("with_observation", [False, True])
def test_run_block_resolves_receipt_once_and_propagates_observation_to_wal_and_result(
        tmp_path, with_observation):
    envelope = {
        "schema_version": migration.OBSERVATION_SCHEMA_VERSION,
        "migration_id": migration.MIGRATION_ID,
        "receipt": {"path": migration.RECEIPT_REL, "raw_sha256": "a" * 64},
        "migration_basis_commit": "b" * 40,
        "validation_head": "c" * 40,
        "items": [],
    }
    observation = envelope if with_observation else None
    resolution = migration.ReceiptResolution(
        state="active-valid" if with_observation else "never-issued", refusals=(),
        t080_freeze_migration_observation=observation,
        validation_head="c" * 40,
        receipt={} if with_observation else None,
    )
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()

    with mock.patch.object(
            migration, "verify_receipt", return_value=resolution) as verify_call:
        # [T-057] 解決回数そのものが検査対象 (下の call_count == 2)。memo は畳んでしまう。
        result = _run(
            tmp_path, freeze_path, manifest_path, prepare_fn,
            _fake_evaluate_factory(), memo_receipt=False,
        )

    assert verify_call.call_count == 2
    expected_campaign_value = (
        observation if with_observation else {
            "state": "never-issued", "validation_head": "c" * 40,
        }
    )
    assert result["t080_freeze_migration_observation"] == expected_campaign_value
    start = next(event for event in result["events"] if event["event"] == "campaign-start")
    assert start["t080_freeze_migration_observation"] == expected_campaign_value


def test_run_block_rejects_receipt_epoch_drift_before_campaign_start_g4(tmp_path):
    initial = migration.ReceiptResolution(
        "never-issued", (), None, "c" * 40,
    )
    changed = migration.ReceiptResolution(
        "never-issued", (), None, "d" * 40,
    )
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    evaluate_fn = _fake_evaluate_factory()
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    output_root = tmp_path / "epoch-drift-out"
    budget_path = tmp_path / "epoch-drift-budget.json"

    with mock.patch.object(
            migration, "verify_receipt", side_effect=[initial, changed]) as verify_call:
        # [T-057] campaign-start 前後で**別々の解決**が起きることが検査対象。
        # memo は 2 回目を畳んで drift 検出を消すため opt-out する。
        result = _run(
            tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn,
            output_root=output_root, budget_path=budget_path, memo_receipt=False,
        )

    assert verify_call.call_count == 2
    assert result["status"] == "refused" and result["allowed"] is False
    assert result["refusals"] == [
        "migration-receipt-verify: receipt epoch が campaign-start 前に変化した"
    ]
    assert prepare_fn.calls == [] and evaluate_fn.calls == []
    assert not budget_path.exists()
    assert (not list(output_root.rglob("wal.jsonl"))) if output_root.exists() else True


def test_t080_epoch_identity_covers_state_introduction_raw_and_head_g4():
    baseline = migration.ReceiptResolution(
        "active-valid", (), {}, "c" * 40, "a" * 40, {}, b"receipt-a",
    )
    variants = (
        dataclasses.replace(baseline, state="invalid"),
        dataclasses.replace(baseline, introduction_commit="b" * 40),
        dataclasses.replace(baseline, receipt_raw=b"receipt-b"),
        dataclasses.replace(baseline, validation_head="d" * 40),
    )
    identity = driver._t080_epoch_identity(baseline)
    assert all(driver._t080_epoch_identity(item) != identity for item in variants)


def test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing(tmp_path):
    manifest_freeze = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, manifest_freeze, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory()
    output_root = tmp_path / "refused-out"
    budget_path = tmp_path / "refused-budget.json"

    # [T-057] 対象は no-active refusal。実 repo receipt 解決は incidental なので memo する。
    # [T-117] active 世代解決 (1 回 4.4 秒) も incidental — 対象は「refusal なら 1 byte も
    # 書かない」であり、解決そのものの検出力は
    # test_nonnull_floor_without_active_generation_is_refused (memo 非使用) が持つ。
    with receipt_memo.patch_driver_resolver(), ratified_memo.patch_ratified_loader():
        result = driver.run_block(
            manifest_path=manifest_path, block_id="b0", freeze_path=REAL_FREEZE,
            root=ROOT, output_root=output_root, budget_path=budget_path,
            prepare_fn=prepare_fn, evaluate_fn=evaluate_fn,
        )

    assert result["status"] == "refused" and result["allowed"] is False
    _assert_exact_refusals(result["refusals"], {_NO_ACTIVE_REFUSAL})
    assert prepare_fn.calls == [] and evaluate_fn.calls == []
    assert not output_root.exists() and not budget_path.exists()


def _assert_required_refusal_has_zero_side_effects(result, output_root, budget_path,
                                                    marker_root):
    assert result["status"] == "refused" and result["allowed"] is False, result
    assert not output_root.exists()
    assert not budget_path.exists()
    assert not marker_root.exists()


def test_required_binding_missing_refuses_at_production_entry_without_side_effects(
        tmp_path, _activate_synthetic_env_authority):
    result, out, budget, markers, _contract, _verified = _run_required_preflight(
        tmp_path, activate_authority=_activate_synthetic_env_authority, environ={},
    )
    _assert_required_refusal_has_zero_side_effects(result, out, budget, markers)
    _assert_exact_refusals(result["refusals"], {
        "v2-execution: reservation binding 検査失敗: "
        "必須環境変数 IZANAGI_RESERVATION_JOB_ID がない",
    })


def test_required_v1_receipt_refuses_at_production_entry_without_side_effects(
        tmp_path, _activate_synthetic_env_authority):
    def v1_issuer(contract, _verified):
        return execution_guard.build_receipt(contract)

    result, out, budget, markers, _contract, _verified = _run_required_preflight(
        tmp_path, activate_authority=_activate_synthetic_env_authority,
        receipt_issuer=v1_issuer,
    )
    _assert_required_refusal_has_zero_side_effects(result, out, budget, markers)
    _assert_exact_refusals(result["refusals"], {
        "v2-execution: execution receipt の契約再検算に失敗",
    })


def test_required_verified_calibration_from_other_contract_is_refused_without_side_effects(
        tmp_path, _activate_synthetic_env_authority):
    _contract, verified = _required_contract(tmp_path)
    wrong_verified = dataclasses.replace(verified, sha256="b" * 64)
    result, out, budget, markers, _contract, _verified = _run_required_preflight(
        tmp_path, activate_authority=_activate_synthetic_env_authority,
        verified_override=wrong_verified,
    )
    _assert_required_refusal_has_zero_side_effects(result, out, budget, markers)
    _assert_exact_refusals(result["refusals"], {
        "v2-execution: verified calibration sha256 が contract ref と不一致",
    })


def test_required_secondary_calibration_identity_recheck_fires_with_monkeypatched_loader(
        tmp_path, _activate_synthetic_env_authority):
    contract, verified = _required_contract(tmp_path)
    assert verified.calibration is not None
    drifted = dataclasses.replace(
        verified,
        calibration=dataclasses.replace(verified.calibration, env_tag="drifted-env"),
    )
    result, out, budget, markers, _contract, _verified = _run_required_preflight(
        tmp_path, activate_authority=_activate_synthetic_env_authority,
        verified_override=drifted,
    )
    _assert_required_refusal_has_zero_side_effects(result, out, budget, markers)
    _assert_exact_refusals(result["refusals"], {
        "v2-execution: verified calibration が別 contract に属する",
    })


def test_required_missing_preprovisioned_oracle_claim_root_is_fail_closed(
        tmp_path, _activate_synthetic_env_authority):
    fixture = _required_run_fixture(tmp_path, _activate_synthetic_env_authority)
    (fixture["output_root"] / "claims").rmdir()
    before = _tree_file_snapshot(fixture["output_root"])

    result = _run_required_fixture(fixture)

    assert result["status"] == "refused" and result["allowed"] is False
    claim_root = (fixture["output_root"] / "claims").resolve()
    _assert_exact_refusals(result["refusals"], {
        "v2-execution: G12 campaign claim root が durable out_root 下に"
        f"事前 provisioning 済みでない: {claim_root}",
    })
    assert _tree_file_snapshot(fixture["output_root"]) == before
    assert not fixture["budget_path"].exists()


def test_required_oracle_claim_root_outside_durable_approval_is_fail_closed(
        tmp_path, _activate_synthetic_env_authority):
    fixture = _required_run_fixture(tmp_path, _activate_synthetic_env_authority)
    unrelated = tmp_path / "unrelated-approved-root"
    unrelated.mkdir()
    policy = driver.DurableRootPolicy(
        approved_roots=(unrelated.resolve(),), forbidden_roots=(),
    )
    before = _tree_file_snapshot(fixture["output_root"])

    result = _run_required_fixture(fixture, durable_policy=policy)

    assert result["status"] == "refused" and result["allowed"] is False
    _assert_exact_refusals(result["refusals"], {
        "v2-execution: candidate が approved root 配下でない",
    })
    assert _tree_file_snapshot(fixture["output_root"]) == before
    assert not fixture["budget_path"].exists()


def test_required_existing_claim_refuses_production_entry_without_new_side_effects(
        tmp_path, _activate_synthetic_env_authority):
    fixture = _required_run_fixture(tmp_path, _activate_synthetic_env_authority)
    identity = driver._execution_identity(fixture["plan"])
    driver._acquire_g12_claim(
        plan=fixture["plan"], claim_root=fixture["output_root"] / "claims",
        manifest_sha256=fixture["verified_manifest"].sha256,
        freeze_sha256=fixture["validated"].ratified.sha256,
        schedule_sha256=fixture["document"]["schedule_sha256"],
        campaign_id=fixture["document"]["campaign_ids"]["b0"], identity=identity,
    )
    claim_paths = list((fixture["output_root"] / "claims").glob("*.claim"))
    assert len(claim_paths) == 1
    claim_payload = json.loads(claim_paths[0].read_text(encoding="utf-8"))
    assert claim_payload["protocol_digest"] == claim_payload["campaign_identity"]
    before = _tree_file_snapshot(fixture["output_root"])

    result = _run_required_fixture(fixture)

    assert result["status"] == "refused" and result["allowed"] is False
    # claim 所有 PID は実行 process に依存するため、その直前までを厳密に固定する。
    _assert_refusal_reasons(result["refusals"], [
        "v2-execution: G12 campaign claim 取得失敗: "
        "campaign claim は既に ",
    ])
    assert _tree_file_snapshot(fixture["output_root"]) == before
    assert not fixture["budget_path"].exists()


def test_oracle_claim_schema_uses_identity_preimage_as_protocol_digest(tmp_path):
    """Oracle follows the required schema without claiming a new gate surface."""
    claim_root = tmp_path / "claims"
    claim_root.mkdir()
    plan = SimpleNamespace(
        contract=SimpleNamespace(
            isolation_policy=ec.IsolationPolicy(
                single_process=True, allow_resume=False,
            ),
        ),
    )
    inputs = {
        "manifest_sha256": "a" * 64,
        "freeze_sha256": "b" * 64,
        "schedule_sha256": "c" * 64,
        "campaign_id": "fixture-campaign",
    }
    driver._acquire_g12_claim(
        plan=plan,
        claim_root=claim_root,
        identity={
            "job": "fixture-job",
            "host": "fixture-host",
            "boot": Path(
                "/proc/sys/kernel/random/boot_id"
            ).read_text(encoding="ascii").strip(),
            "pid": os.getpid(),
            "starttime": driver._campaign_claim.read_proc_starttime(),
        },
        **inputs,
    )

    claim_paths = list(claim_root.glob("*.claim"))
    assert len(claim_paths) == 1
    payload = json.loads(claim_paths[0].read_text(encoding="utf-8"))
    expected = driver._claim_identity(**inputs)
    assert payload["campaign_identity"] == expected
    assert payload["protocol_digest"] == expected


def test_required_initial_reservation_includes_schedule_attestation_probes(
        tmp_path, _activate_synthetic_env_authority):
    probe_calls = []
    original_issuer = execution_guard.attest_and_build_receipt

    def issuer(contract, verified):
        def probe():
            probe_calls.append(verified.attestation_profile)
            return _observed(verified.attestation_profile)

        return original_issuer(contract, verified, probe_fn=probe)

    with mock.patch.object(
            driver._reservation, "check_reservation",
            wraps=driver._reservation.check_reservation) as check_call:
        result, _out, _budget, _markers, _contract, _verified = _run_required_preflight(
            tmp_path,
            activate_authority=_activate_synthetic_env_authority,
            receipt_issuer=issuer,
        )

    assert result["status"] == "refused", result
    _assert_exact_refusals(result["refusals"], {
        "v2-execution: floor artifact に schedule cell の binary receipt が無い: "
        "('rr80', 'system_gate')",
    })
    assert check_call.call_count == 1
    assert check_call.call_args.kwargs["required_s"] == pytest.approx(43802.4)
    assert len(probe_calls) == 1


def test_required_recheck_includes_remaining_attestation_probe(
        tmp_path, _activate_synthetic_env_authority):
    fixture = _required_run_fixture(tmp_path, _activate_synthetic_env_authority)
    original_check = fixture["plan"].reservation_check
    probe_calls = []
    original_issuer = execution_guard.attest_and_build_receipt

    def issuer(contract, verified):
        def probe():
            probe_calls.append(verified.attestation_profile)
            return _observed(verified.attestation_profile)

        return original_issuer(contract, verified, probe_fn=probe)

    with mock.patch.object(
            driver.execution_guard, "attest_and_build_receipt",
            side_effect=issuer):
        driver._recheck_required_execution(fixture["plan"], remaining_rows=1)

    assert fixture["plan"].reservation_check is not original_check
    assert fixture["plan"].reservation_check.required_s == pytest.approx(4200.2)
    assert len(probe_calls) == 1


def test_required_recheck_reservation_shortfall_skips_attestation(
        tmp_path, _activate_synthetic_env_authority):
    fixture = _required_run_fixture(tmp_path, _activate_synthetic_env_authority)
    fixture["plan"].reservation_check = dataclasses.replace(
        fixture["plan"].reservation_check,
        monotonic_deadline=time.monotonic() + 1.0,
    )
    attest_calls = []

    def issuer(*_args, **_kwargs):
        attest_calls.append(True)
        raise AssertionError("reservation 不足時に attestation を呼んだ")

    with mock.patch.object(
            driver.execution_guard, "attest_and_build_receipt",
            side_effect=issuer), pytest.raises(
                driver.OracleDriverError, match="reservation"):
        driver._recheck_required_execution(fixture["plan"], remaining_rows=1)

    assert attest_calls == []


def test_required_recheck_attestation_failure_follows_reservation_check(
        tmp_path, _activate_synthetic_env_authority):
    fixture = _required_run_fixture(tmp_path, _activate_synthetic_env_authority)
    original_check = fixture["plan"].reservation_check
    attest_calls = []

    def issuer(*_args, **_kwargs):
        attest_calls.append(True)
        raise execution_guard.ExecutionGuardError("fixture attestation failure")

    with mock.patch.object(
            driver.execution_guard, "attest_and_build_receipt",
            side_effect=issuer), pytest.raises(
                driver.OracleDriverError, match="fixture attestation failure"):
        driver._recheck_required_execution(fixture["plan"], remaining_rows=1)

    assert len(attest_calls) == 1
    assert fixture["plan"].reservation_check is not original_check
    assert fixture["plan"].reservation_check.required_s == pytest.approx(4200.2)


def test_required_recheck_real_reservation_shortfall_writes_aborted_terminal(
        tmp_path, _activate_synthetic_env_authority):
    fixture = _required_run_fixture(tmp_path, _activate_synthetic_env_authority)
    fixture["plan"].reservation_check = dataclasses.replace(
        fixture["plan"].reservation_check,
        monotonic_deadline=time.monotonic() + 1.0,
    )
    result = _run_required_fixture(fixture)

    assert result["status"] == "error"
    deviation = next(event for event in result["events"] if event["event"] == "deviation")
    assert deviation["kind"] == "execution-guard-lost"
    assert "reservation" in deviation["message"]
    terminals = [event for event in result["events"]
                 if event["event"] == "campaign-terminal"]
    assert len(terminals) == 1
    assert terminals[0]["status"] == "aborted"
    assert terminals[0]["completed_rows"] == 0
    assert terminals[0]["scheduled_rows"] == len(fixture["document"]["schedule"]["rows"])


def test_required_recheck_real_receipt_validation_catches_midcampaign_drift(
        tmp_path, _activate_synthetic_env_authority):
    fixture = _required_run_fixture(tmp_path, _activate_synthetic_env_authority)
    valid = execution_guard.attest_and_build_receipt(
        fixture["contract"], fixture["verified"],
        probe_fn=lambda: _observed(fixture["verified"].attestation_profile),
    )
    drifted = copy.deepcopy(valid)
    drifted["contract_sha256"] = "0" * 64

    result = _run_required_fixture(
        fixture, receipt_side_effect=mock.Mock(return_value=drifted),
    )

    assert result["status"] == "error"
    deviation = next(event for event in result["events"] if event["event"] == "deviation")
    assert deviation["kind"] == "execution-guard-lost"
    assert "attestation receipt" in deviation["message"]
    terminal = result["events"][-1]
    assert terminal["event"] == "campaign-terminal"
    assert terminal["status"] == "aborted" and terminal["completed_rows"] == 0


def test_two_real_subprocess_oracle_submissions_only_one_acquires_g12_claim(tmp_path):
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, document = _write_manifest(tmp_path, freeze_path, prepare_fn)
    approved = _APPROVED_BY_PATH[manifest_path.resolve()]
    receipt_root = tmp_path / "receipt-free-repo"
    receipt_root.mkdir()
    _run_git(receipt_root, "init", "-q", "--object-format=sha1")
    _run_git(receipt_root, "config", "user.name", "S8B G12 Test")
    _run_git(receipt_root, "config", "user.email", "s8b-g12@example.invalid")
    _run_git(receipt_root, "config", "commit.gpgsign", "false")
    _run_git(receipt_root, "config", "core.autocrlf", "false")
    assert _run_git(receipt_root, "rev-parse", "--show-object-format") == "sha1"
    _run_git(
        receipt_root, "commit", "-q", "--allow-empty",
        "-m", "receipt-free basis", "-m", "AI-Agent: none",
    )
    shared_out_root = tmp_path / "shared-oracle-output-root"
    claim_root = shared_out_root / "claims"
    claim_root.mkdir(parents=True)
    marker_root = tmp_path / "shared-oracle-marker-root"
    marker_root.mkdir()
    script = textwrap.dedent(
        f"""
        import dataclasses, hashlib, json, sys, time
        from pathlib import Path
        from unittest import mock
        sys.path.insert(0, {str(ORCHESTRATOR.parent)!r})
        from orchestrator.campaign import env_contract, execution_guard
        from orchestrator.campaign.durable_root import DurableRootPolicy
        from orchestrator.campaign import s8b_oracle_driver as driver
        from orchestrator.campaign import (
            s8b_oracle_manifest, s8b_oracle_spec, s8b_ratified_freeze,
        )

        freeze_path = Path({str(freeze_path)!r})
        raw = freeze_path.read_bytes()
        ratified = s8b_ratified_freeze.RatifiedFreeze(
            document=json.loads(raw), sha256=hashlib.sha256(raw).hexdigest(),
            generation_number=1, activation_head="f" * 40, generation_commit="e" * 40)
        floor = s8b_ratified_freeze.VerifiedFloorArtifact(
            path="fixture/result.json", raw_bytes=b"{{}}",
            sha256=hashlib.sha256(b"{{}}").hexdigest(), document={{}})
        validated = s8b_ratified_freeze.LaunchValidatedFreeze(
            ratified=ratified, activation_head=ratified.activation_head,
            search_digest="d" * 64, symlink_gitlink_inventory=(),
            floor_artifact=floor, binaries_by_cell={{}})
        spec_raw = {approved.raw_bytes!r}
        spec_document = json.loads(spec_raw)
        validated_spec, spec_schedule = s8b_oracle_spec.validate_reviewed_spec(
            spec_document, root=Path({str(ROOT)!r}))
        approved_spec = s8b_oracle_spec.ReviewedSpec(
            document=validated_spec, raw_bytes=spec_raw,
            sha256={approved.sha256!r}, schedule=spec_schedule)
        s8b_oracle_spec.APPROVED_SPEC_SHA256 = approved_spec.sha256
        verified_manifest = s8b_oracle_manifest.verify_manifest(
            Path({str(manifest_path)!r}), root=Path({str(ROOT)!r}),
            freeze_document=json.loads(raw),
            freeze_sha256=hashlib.sha256(raw).hexdigest(),
            approved_spec=approved_spec)
        base = env_contract.lookup("linux-baremetal")
        required = dataclasses.replace(
            base, attestation_mode="required",
            isolation_policy=env_contract.IsolationPolicy(
                single_process=True, allow_resume=False))
        plan = driver._V2Plan(
            contract=required,
            authorization_contract=env_contract.authorize("linux-baremetal"),
            receipt=execution_guard.build_receipt(required),
            perf_sha_by_cell={{}})

        def won_claim_then_stop(*_args, **_kwargs):
            time.sleep(0.25)
            raise driver.OracleDriverError("fixture stop after global claim")

        try:
            with mock.patch.object(driver, "_gate_check_validated",
                                   return_value=driver.GateDecision(True, [], None)), \
                    mock.patch.object(driver.s8b_ratified_freeze,
                                      "load_ratified_freeze", return_value=ratified), \
                    mock.patch.object(driver.s8b_ratified_freeze,
                                      "launch_validate", return_value=validated), \
                    mock.patch.object(driver, "verify_manifest",
                                      return_value=verified_manifest), \
                    mock.patch.object(driver.s8b_oracle_spec, "load_approved_spec",
                                      return_value=approved_spec), \
                    mock.patch.object(driver, "_prepare_v2_execution",
                                      return_value=plan), \
                    mock.patch.object(driver, "_ensure_campaign",
                                      side_effect=won_claim_then_stop):
                result = driver.run_block(
                    manifest_path={str(manifest_path)!r}, block_id="b0",
                    freeze_path={str(freeze_path)!r}, root={str(receipt_root)!r},
                    output_root={str(shared_out_root)!r},
                    budget_path={str(tmp_path / 'subprocess-budget.json')!r},
                    marker_root={str(marker_root)!r},
                    durable_root_policy=DurableRootPolicy(
                        approved_roots=(Path({str(shared_out_root)!r}).resolve(),),
                        forbidden_roots=()))
            print(json.dumps(result, sort_keys=True))
        except driver.OracleDriverError as exc:
            print(json.dumps({{"status": "claim-won", "error": str(exc)}}, sort_keys=True))
        """
    )
    processes = []
    results = []
    try:
        for _ in range(2):
            processes.append(subprocess.Popen(
                [sys.executable, "-c", script], stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True,
            ))
        for process in processes:
            stdout, stderr = process.communicate(timeout=10)
            assert process.returncode == 0, stderr
            results.append(json.loads(stdout))
    finally:
        for process in processes:
            try:
                if process.poll() is None:
                    process.kill()
                process.wait()
            except Exception:
                pass

    # loser reason は競合タイミング依存で非決定のため status のみ固定する。
    assert sorted(result["status"] for result in results) == ["claim-won", "refused"]
    assert len(list(claim_root.glob("*.claim"))) == 1


def test_nonnull_floor_without_active_generation_is_refused(tmp_path):
    """v2 (floor 充填) freeze だが実 repo に承認束縛済み active 世代が無い場合、
    active 解決失敗を freeze-ratify refusal に翻訳し、一切書かずに倒す (RatifiedFreezeError
    を例外として漏らさない)。"""
    freeze_path = _floor_only_freeze(tmp_path)
    manifest_freeze = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, manifest_freeze, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory()
    output_root = tmp_path / "v2-refused-out"
    budget_path = tmp_path / "v2-refused-budget.json"

    # [T-057] 対象は active 世代の解決失敗の翻訳。receipt 解決は incidental なので memo する。
    # [T-117] **この node は active 世代解決を memo しない正本 payer** である。実 repo の
    # 履歴走査 (git 39 本・4.4 秒) を node 順序に依らず毎 session 必ず 1 回走らせ、
    # 「解決失敗 → freeze-ratify refusal」の検出力を memo に委ねない (規律 2)。
    # 不変条件は test_real_repo_serialization.py の payer 検査が機械固定する。
    with receipt_memo.patch_driver_resolver():
        result = driver.run_block(
            manifest_path=manifest_path, block_id="b0", freeze_path=freeze_path,
            root=ROOT, output_root=output_root, budget_path=budget_path,
            prepare_fn=prepare_fn, evaluate_fn=evaluate_fn,
        )

    assert result["status"] == "refused"
    _assert_exact_refusals(result["refusals"], {_NO_ACTIVE_REFUSAL})
    assert prepare_fn.calls == [] and evaluate_fn.calls == []
    assert not output_root.exists() and not budget_path.exists()


def test_active_resolution_and_manifest_structure_refusals_are_aggregated(tmp_path):
    """active 解決失敗時も独立 manifest 構造検査の refusal を落とさない。"""
    freeze_path = _floor_only_freeze(tmp_path)
    manifest_freeze = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, document = _write_manifest(tmp_path, manifest_freeze, prepare_fn)
    prepare_fn.calls.clear()
    document["unexpected_top_level_key"] = True
    manifest_path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    evaluate_fn = _fake_evaluate_factory()
    output_root = tmp_path / "aggregate-refused-out"
    budget_path = tmp_path / "aggregate-refused-budget.json"

    # [T-057] 対象は refusal の集約。receipt 解決は incidental なので memo する。
    # [T-117] active 世代解決も incidental (対象は manifest 構造 refusal を落とさないこと)。
    with receipt_memo.patch_driver_resolver(), ratified_memo.patch_ratified_loader():
        result = driver.run_block(
            manifest_path=manifest_path, block_id="b0", freeze_path=freeze_path,
            root=ROOT, output_root=output_root, budget_path=budget_path,
            prepare_fn=prepare_fn, evaluate_fn=evaluate_fn,
        )

    assert result["status"] == "refused" and result["allowed"] is False
    _assert_exact_refusals(result["refusals"], {
        _NO_ACTIVE_REFUSAL,
        "manifest-verify: ManifestError: manifest top-level schema が不一致",
    })
    assert prepare_fn.calls == [] and evaluate_fn.calls == []
    assert not output_root.exists() and not budget_path.exists()


def test_success_wal_order_budget_and_evaluate_contract(tmp_path):
    from orchestrator.campaign.sort_swo_oracle import ORACLE_CONTRACT_ID

    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, document = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory()

    result = _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn)

    assert result["status"] == "completed"
    assert result["completed_trials"] == len(document["schedule"]["rows"])
    session_events = [event["event"] for event in result["events"]]
    assert session_events == ["campaign-start", *(
        event for _row in document["schedule"]["rows"]
        for event in ("trial-start", "trial-result")
    ), "campaign-terminal"]
    terminal = result["events"][-1]
    assert terminal["status"] == "completed"
    assert terminal["scheduled_rows"] == terminal["completed_rows"] == len(
        document["schedule"]["rows"]
    )
    assert set(terminal["execution_identity"]) == {
        "job", "host", "boot", "pid", "starttime",
    }
    assert len(prepare_fn.calls) == len(evaluate_fn.calls) == len(
        document["schedule"]["rows"]
    )
    seen_unbound = set()
    saw_sort_best = False
    for prepare_call, call in zip(prepare_fn.calls, evaluate_fn.calls):
        kwargs = call["kwargs"]
        configuration = prepare_call["cell"]["configuration"]
        if configuration == "sort_best":
            saw_sort_best = True
            assert kwargs["sort_oracle_contract_id"] == ORACLE_CONTRACT_ID
        else:
            assert "sort_oracle_contract_id" not in kwargs
            if configuration in {"backoff_fixed_best", "stock_common"}:
                seen_unbound.add(configuration)
        assert kwargs["do_bench"] is True
        assert kwargs["screening"] is None
        assert kwargs["env_contract"] is ec.lookup(V2_ENV_TAG)
        assert "admission" not in kwargs
        assert type(kwargs["build_context"]) is BuildRunContext
        assert callable(kwargs["capability_resolver"])
        evidence = SourceEvidence(
            schema_version="source-evidence/v1",
            source_root=str((tmp_path / "oracle-source-Ω").resolve()),
            ccbench_commit=call["ccbench_commit"],
            genome_sha256=hashlib.sha256(
                call["genome"].canonical().encode("utf-8")
            ).hexdigest(),
            src_token="1" * 64,
            source_bytes_sha256="2" * 64,
            tracked_clean=False,
            tracked_diff_sha256="3" * 64,
            tracked_paths=("include/backoff.hh",),
        )
        capability = kwargs["capability_resolver"](evidence)
        assert type(capability) is ReviewReceipt
        capability_body = capability.as_receipt()
        assert capability_body["review_id"] == ReviewId.S8B_ORACLE.value
        assert capability_body["source"] == evidence.as_receipt()
        assert len(kwargs["extra_correctness"]) == 1
        tag, workload = kwargs["extra_correctness"][0]
        assert tag == pipeline.S2_TAG
        assert workload.flags == pipeline.s2_correctness_workload().flags
    assert saw_sort_best
    assert seen_unbound == {"backoff_fixed_best", "stock_common"}
    ledger = s8b_budget.read_ledger(
        tmp_path / "budget.json",
        manifest_sha256=result["manifest_sha256"],
        freeze_sha256=result["freeze_sha256"],
        schedule_sha256=result["schedule_sha256"],
    )
    assert len(ledger["entries"]) == len(document["schedule"]["rows"])
    assert ledger["spent"]["bench_s"] == pytest.approx(
        0.25 * len(document["schedule"]["rows"])
    )
    # terminal 後の精算: charged==actual==実測、reserved は分離して残る。
    reservation = ledger["reservation"]
    assert reservation["status"] == "settled"
    assert reservation["charged_bench_s"] == pytest.approx(
        0.25 * len(document["schedule"]["rows"])
    )
    assert reservation["actual_bench_s"] == pytest.approx(
        0.25 * len(document["schedule"]["rows"])
    )
    assert reservation["reserved_bench_s"] == pytest.approx(
        25.0 * len(document["schedule"]["rows"])
    )
    assert not list((tmp_path / "markers").glob("*.claim"))  # mode=none 回帰


def test_campaign_terminal_driver_guard_rejects_second_terminal(tmp_path):
    layout = campaign_layout("oracle-terminal-double", output_root=str(tmp_path)).ensure()
    identity = {
        "job": "j", "host": "h", "boot": "b", "pid": 1, "starttime": 2,
    }
    driver._append_campaign_terminal(
        layout, V2_ENV_TAG, status="completed", scheduled_rows=1,
        completed_rows=1, execution_identity=identity,
    )
    with pytest.raises(driver.OracleDriverError, match="二重"):
        driver._append_campaign_terminal(
            layout, V2_ENV_TAG, status="aborted", scheduled_rows=1,
            completed_rows=0, execution_identity=identity,
        )
    terminals = [event for event in driver._session_events(layout)
                 if event["event"] == "campaign-terminal"]
    assert len(terminals) == 1 and terminals[0]["status"] == "completed"


def test_oracle_pipeline_contract_keyword_is_mandatory_positive_control(tmp_path):
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, prepare_fn)
    base = _fake_evaluate_factory()

    def requires_contract(genome, layout, env_tag, ccbench_commit, perf,
                          clocks_per_us, *, env_contract, **kwargs):
        assert env_contract is ec.lookup(V2_ENV_TAG)
        return base(
            genome, layout, env_tag, ccbench_commit, perf, clocks_per_us,
            env_contract=env_contract, **kwargs,
        )

    result = _run(
        tmp_path, freeze_path, manifest_path, prepare_fn, requires_contract,
    )
    assert result["status"] == "completed"


def test_build_result_contract_mismatch_aborts_campaign_before_measurement(tmp_path):
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, prepare_fn)
    guard_failures = []

    def fake_evaluate(genome, *_args, **_kwargs):
        # driver の production evaluate 境界内で build_v2 result guard を発火する。
        try:
            pipeline.buildcache.build_v2()
        except AssertionError as exc:
            guard_failures.append(str(exc))
            raise
        raise AssertionError("contract guard did not reject")

    wrong = pipeline.buildcache.BuildResult(
        genome=Genome("silo", {}), trace=True, binary="/tmp/not-run",
        bin_sha256="0" * 64, build_dir="/tmp/not-run", cached=True,
        contract_sha256="f" * 64,
    )
    with mock.patch.object(pipeline.buildcache, "build_v2", return_value=wrong):
        result = _run(
            tmp_path, freeze_path, manifest_path, prepare_fn, fake_evaluate,
        )

    assert result["status"] == "error"
    assert guard_failures and "BuildResult.contract_sha256" in guard_failures[0]
    terminal = next(event for event in result["events"]
                    if event["event"] == "campaign-terminal")
    assert terminal["status"] == "aborted"
    assert terminal["completed_rows"] == 0


def test_binding_mismatch_refuses_only_that_row_before_evaluate(tmp_path):
    freeze_path = _synthetic_freeze(tmp_path)
    manifest_prepare = _prepare_factory()
    manifest_path, document = _write_manifest(
        tmp_path, freeze_path, manifest_prepare,
    )
    prepare_fn = _prepare_factory(token_suffix="-changed", suffix_first_only=True)
    evaluate_fn = _fake_evaluate_factory()

    result = _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn)

    assert [event["event"] for event in result["events"][:3]] == [
        "campaign-start", "trial-start", "binding-refused",
    ]
    assert len(evaluate_fn.calls) == len(document["schedule"]["rows"]) - 1


def test_v8_bulk_reservation_unavailable_runs_nothing(tmp_path):
    """V8: 残枠が全行最大費用未満なら一行も走らず budget_exhausted_before_attempt を耐久化。

    reservation 総額 = extime×reps×bench_max_rounds×行数。total_bench_s=0.0 では確保できず、
    driver は trial-start を一つも出さず terminal を budget ledger と WAL の双方へ書く。
    """
    freeze_path = _synthetic_freeze(tmp_path, total_bench_s=0.0)
    prepare_fn = _prepare_factory()
    manifest_path, document = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory()

    result = _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn)

    assert result["status"] == "budget_exhausted_before_attempt"
    assert result["completed_trials"] == 0
    events = result["events"]
    assert [event["event"] for event in events] == [
        "campaign-start", "budget-exhausted-before-attempt", "campaign-terminal",
    ]
    assert events[-1]["status"] == "aborted"
    assert events[-1]["scheduled_rows"] == len(document["schedule"]["rows"])
    assert events[-1]["completed_rows"] == 0
    # 一行も走らせない: prepare も evaluate も trial-start も発火しない。
    assert prepare_fn.calls == [] and evaluate_fn.calls == []
    assert not any(event["event"] == "trial-start" for event in events)
    # terminal は budget ledger にも耐久化される (reservation status=exhausted)。
    ledger = s8b_budget.read_ledger(
        tmp_path / "budget.json",
        manifest_sha256=result["manifest_sha256"],
        freeze_sha256=result["freeze_sha256"],
        schedule_sha256=result["schedule_sha256"],
    )
    assert ledger["reservation"]["status"] == "exhausted"
    assert ledger["reservation"]["reserved_bench_s"] == pytest.approx(
        25.0 * len(document["schedule"]["rows"])
    )
    assert ledger["entries"] == []


def test_reservation_envelope_exceeded_is_fail_closed(tmp_path):
    """実測 bench が予約枠を超過したら fail-closed で error に倒す (protocol violation)。

    reservation 枠 = 行数×(extime×reps×rounds)=行数×25。1 行目の実測 26 で単 holdout 枠
    (6 行×25=150) は超えないが、全 12 行を 26 で回すと総枠 300 を超える経路がある。ここでは
    per-holdout 枠超過 (h の 6 行×26=156 > 予約 150) を fixture で発火させる。
    """
    freeze_path = _synthetic_freeze(tmp_path, total_bench_s=1000.0)
    prepare_fn = _prepare_factory()
    manifest_path, document = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    # 各 trial の実測 bench_wall_s=26 > per-row 予約 25。holdout 枠 (6 行×25=150) を
    # 同一 holdout の 6 行目 (実測累計 156) で超える。
    evaluate_fn = _fake_evaluate_factory(bench_wall_s=26.0)

    result = _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn)

    assert result["status"] == "error"
    deviation = next(event for event in result["events"]
                     if event["event"] == "deviation")
    assert deviation["kind"] == "reservation-envelope-exceeded"
    # error では精算しない (予約枠を非解放のまま残す)。
    ledger = s8b_budget.read_ledger(
        tmp_path / "budget.json",
        manifest_sha256=result["manifest_sha256"],
        freeze_sha256=result["freeze_sha256"],
        schedule_sha256=result["schedule_sha256"],
    )
    assert ledger["reservation"]["status"] == "held"
    # 所見4: entries 永続化状態を検査する。append_entry は _atomic_replace_json を
    # 呼ぶ前に BudgetError を raise するため、超過を起こした行の entry は台帳に
    # 一切残らない。超過より前に (schedule 順で) 成功した行の entry はそのまま
    # 残る。schedule は擬似乱数で shuffle 済みのため holdout ごとに連続しない
    # ので、実際の schedule 順で厳密に検査する (固定 index を仮定しない)。
    rows = document["schedule"]["rows"]
    failing_index = deviation["schedule_index"]
    failing_position = next(
        position for position, row in enumerate(rows)
        if row["schedule_index"] == failing_index
    )
    expected_persisted_indices = {
        row["schedule_index"] for row in rows[:failing_position]
    }
    persisted_indices = {entry["schedule_index"] for entry in ledger["entries"]}
    assert failing_position > 0  # 超過前に成功した行が実在する
    assert persisted_indices == expected_persisted_indices
    assert failing_index not in persisted_indices
    assert len(ledger["entries"]) == failing_position


def test_verify_inconclusive_and_unknown_abort_reasons_are_fail_closed(tmp_path):
    trace_root = tmp_path / "trace"
    trace_root.mkdir()
    freeze_path = _synthetic_freeze(trace_root)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(trace_root, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    trace_empty = _fake_abort_evaluate_factory("trace-empty")

    trace_result = _run(
        trace_root, freeze_path, manifest_path, prepare_fn, trace_empty,
    )

    trace_outcomes = [event["outcome"] for event in trace_result["events"]
                      if event["event"] == "trial-result"]
    assert trace_outcomes and set(trace_outcomes) == {"verify-inconclusive"}

    unknown_root = tmp_path / "unknown"
    unknown_root.mkdir()
    unknown_freeze = _synthetic_freeze(unknown_root)
    unknown_prepare = _prepare_factory()
    unknown_manifest, _ = _write_manifest(
        unknown_root, unknown_freeze, unknown_prepare,
    )
    unknown_prepare.calls.clear()
    unknown_evaluate = _fake_abort_evaluate_factory("future-unclassified-abort")

    unknown_result = _run(
        unknown_root, unknown_freeze, unknown_manifest,
        unknown_prepare, unknown_evaluate,
    )

    assert unknown_result["status"] == "error"
    assert not any(event["event"] == "trial-result"
                   for event in unknown_result["events"])
    deviation = next(event for event in unknown_result["events"]
                     if event["event"] == "deviation")
    assert deviation["kind"] == "unknown-abort-reason"
    assert deviation["abort_reason"] == "future-unclassified-abort"
    assert len(unknown_evaluate.calls) == 1


@pytest.mark.parametrize("reason", ["bench-probe-error", "verify-probe-error"])
def test_probe_error_reason_is_fail_closed_unknown_abort(tmp_path, reason):
    """B-7 置換裁定 (D-4): probe 故障 abort reason (bench/verify-probe-error) が oracle
    driver に到達すると、_outcome_for の凍結バケツに無いため _UnknownAbortReason 経路で
    deviation (kind=unknown-abort-reason) + error_stopped になる (fail-closed)。oracle 側
    判定表は D-4 で不変ゆえ trial-result 化 (reservation 精算) しない。"""
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_abort_evaluate_factory(reason)

    result = _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn)

    assert result["status"] == "error"
    assert not any(event["event"] == "trial-result" for event in result["events"])
    deviation = next(event for event in result["events"]
                     if event["event"] == "deviation")
    assert deviation["kind"] == "unknown-abort-reason"
    assert deviation["abort_reason"] == reason
    assert len(evaluate_fn.calls) == 1


@in_sealed_fixture_process
def test_transient_prepare_failure_retries_once(tmp_path):
    root, freeze_path, _gen_sha, _binaries, _topology = _build_v2_repo(
        tmp_path,
    )
    manifest_path, document = _emitter_manifest(
        tmp_path, root, freeze_path,
    )
    retrying_prepare = _prepare_factory(fail_first=True)
    evaluate_fn = _fake_evaluate_factory()

    output_root = root.parent / "output"
    result = _run_v2(
        root, freeze_path, manifest_path, retrying_prepare, evaluate_fn,
        out_root=output_root, tmp_path=tmp_path,
    )

    prefix = [event["event"] for event in result["events"][:5]]
    assert prefix == [
        "campaign-start", "trial-start", "retry", "trial-start", "trial-result",
    ]
    assert result["events"][2]["attempt"] == 2
    assert len(evaluate_fn.calls) == len(document["schedule"]["rows"])
    observations_path = tmp_path / "retry-observations.json"
    _authorize_official_report_output(output_root)
    assert report_module.main([
        "report", "--manifest", str(manifest_path),
        "--output-root", str(output_root), "--out", str(observations_path),
        "--repo-root", str(root),
    ]) == 0
    observations = json.loads(observations_path.read_bytes())
    assert all(row["status"] == "completed" for row in observations["rows"])
    assert all(row["lifecycle_ok"] is True for row in observations["rows"])


def test_tampered_freeze_fails_source_verification(tmp_path):
    """valid receipt 下の confirmed_by 単独改変を legacy verifier が拒否する。"""
    root, canonical_freeze = _t080_repo(tmp_path, receipt="active-valid")
    freeze_path = tmp_path / "tampered-holdout-freeze.json"
    document = json.loads(canonical_freeze.read_text(encoding="utf-8"))
    document["confirmed_by"] += "-tampered"
    freeze_path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    search_report = {
        "holdouts": {
            name: {
                "expressions": entry["unknownness_check"]["expressions"],
                "conjunction_hits": [],
            }
            for name, entry in document["holdouts"].items()
        },
        "positive_control": {
            "expressions": document["positive_control"]["expressions"],
            "hit_count": 1,
        },
    }

    with _t080_static_checks_pass(), \
            mock.patch.object(driver.s8b_holdout_freeze, "_verify_source"), \
            mock.patch.object(driver.s8b_holdout_freeze, "_verify_head"), \
            mock.patch.object(driver.s8b_holdout_freeze, "search_repository",
                              return_value=search_report), \
            mock.patch.object(driver.s1_known_axes_freeze, "verify"):
        decision = driver.gate_check(freeze_path=freeze_path, root=root)

    assert not decision.allowed
    first_holdout = next(iter(document["holdouts"]))
    _assert_exact_refusals(decision.refusals, {
        "holdout-freeze-verify: FreezeError: "
        f"holdouts.{first_holdout}.unknownness_check.confirmed_by 不一致",
        _FLOOR_REFUSAL,
        _BUDGET_REFUSAL,
    })
    assert decision.t080_freeze_migration_observation is None


def test_perf_for_holdout_accepts_authoritative_freeze_entry():
    authority = s8b_holdout_freeze.HOLDOUTS["rr80"]
    freeze_entry = copy.deepcopy(authority)
    freeze_entry.update({
        "unknownness_check": {
            "expressions": ["fixture"], "confirmed_by": "test",
        },
        "variant_binding": {"variant_id": "fixture"},
    })

    perf = driver._perf_for_holdout(
        {"holdouts": {"rr80": freeze_entry}}, "rr80",
        {"extime": 30.0, "reps": 2},
    )

    assert perf.records == authority["records"]
    assert perf.threads == authority["threads"]
    assert perf.workload == dict(authority["ycsb"])
    assert perf.extime == 30.0
    assert perf.reps == 2


def test_perf_for_holdout_rejects_authority_value_tampering():
    freeze_entry = copy.deepcopy(s8b_holdout_freeze.HOLDOUTS["rr80"])
    freeze_entry.update({
        "unknownness_check": {
            "expressions": ["fixture"], "confirmed_by": "test",
        },
        "variant_binding": {"variant_id": "fixture"},
    })
    freeze_entry["records"] += 1

    with pytest.raises(driver.OracleDriverError,
                       match="holdout perf binding が不正"):
        driver._perf_for_holdout(
            {"holdouts": {"rr80": freeze_entry}}, "rr80",
            {"extime": 30.0, "reps": 2},
        )


def test_perf_for_holdout_rejects_unknown_holdout_id():
    with pytest.raises(driver.OracleDriverError,
                       match="holdout perf binding が不正"):
        driver._perf_for_holdout(
            {"holdouts": {}}, "unknown-holdout",
            {"extime": 30.0, "reps": 2},
        )


def test_never_issued_legacy_generator_tamper_has_exact_single_refusal_b7(tmp_path):
    root = tmp_path / "legacy-generator"
    generator = root / driver.s8b_holdout_freeze.SCRIPT_REL
    generator.parent.mkdir(parents=True)
    generator.write_bytes((ROOT / driver.s8b_holdout_freeze.SCRIPT_REL).read_bytes())
    recorded = hashlib.sha256(generator.read_bytes()).hexdigest()
    document = {
        "generator": {
            "path": driver.s8b_holdout_freeze.SCRIPT_REL,
            "sha256": recorded,
        },
    }
    generator.write_bytes(generator.read_bytes() + b"# generator-only-tamper\n")
    actual = hashlib.sha256(generator.read_bytes()).hexdigest()
    with pytest.raises(driver.s8b_holdout_freeze.FreezeError) as caught:
        driver.s8b_holdout_freeze._verify_source(
            document, "generator", root, driver.s8b_holdout_freeze.SCRIPT_REL,
        )
    assert str(caught.value) == (
        "generator sha256 不一致: "
        f"recorded={recorded} actual={actual}"
    )


def test_never_issued_generator_tamper_reaches_public_driver_gate_g7(tmp_path):
    root, _receipt_path, _document = _t080_stub_free_e2e_repo(
        tmp_path, issue_receipt=False,
    )
    freeze = json.loads((root / migration.HOLDOUT_REL).read_text(encoding="utf-8"))

    def historical_bytes(relative: str, expected: str) -> bytes:
        commits = _run_git(ROOT, "log", "--format=%H", "--", relative).splitlines()
        for commit in commits:
            completed = subprocess.run(
                ["git", "show", f"{commit}:{relative}"], cwd=ROOT,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=_sanitized_git_env(),
            )
            if (completed.returncode == 0
                    and hashlib.sha256(completed.stdout).hexdigest() == expected):
                return completed.stdout
        raise AssertionError(f"recorded bytes が Git 履歴にない: {relative} {expected}")

    for field in ("design_source", "generator"):
        record = freeze[field]
        target = root / record["path"]
        target.write_bytes(historical_bytes(record["path"], record["sha256"]))
    known = json.loads((root / migration.KNOWN_AXES_REL).read_text(encoding="utf-8"))
    # ROOT identifies live modules/reconstruction; root resolves copied inputs.
    # Releasing the shared hold also checks the live ccbench pin, independently
    # of the historical code-source differences accepted by D1936 item 22.
    actual_pin = _run_git(ROOT / "external/ccbench", "rev-parse", "HEAD")
    assert actual_pin != known["ccbench_pin"]
    known_pin_refusal = (
        "known-axes-freeze-verify: FreezeError: ccbench_pin 不一致: "
        f"recorded={known['ccbench_pin']} actual={actual_pin}"
    )
    generator = root / freeze["generator"]["path"]
    generator.write_bytes(generator.read_bytes() + b"# driver-gate-generator-tamper\n")
    generator_refusal = (
        "holdout-freeze-verify: FreezeError: generator sha256 不一致: "
        f"recorded={freeze['generator']['sha256']} "
        f"actual={hashlib.sha256(generator.read_bytes()).hexdigest()}"
    )

    verifier_sentinel = "t080-holdout-verifier-sentinel"
    with mock.patch.object(
            driver.s8b_holdout_freeze, "verify",
            side_effect=driver.s8b_holdout_freeze.FreezeError(verifier_sentinel),
            ) as sentinel_verify:
        sentinel_decision = driver.gate_check(
            freeze_path=root / migration.HOLDOUT_REL, root=root,
        )
    assert sentinel_verify.call_args_list == [
        mock.call(root / migration.HOLDOUT_REL, root=root),
    ]

    holdout_verify = driver.s8b_holdout_freeze.verify
    with mock.patch.object(
            driver.s8b_holdout_freeze, "verify", wraps=holdout_verify,
            ) as verify_witness:
        decision = driver.gate_check(
            freeze_path=root / migration.HOLDOUT_REL, root=root,
        )
        with mock.patch.object(
                driver.s8b_holdout_freeze._freeze_hold, "HELD", False):
            released = driver.gate_check(
                freeze_path=root / migration.HOLDOUT_REL, root=root,
            )

    # Held positive control: live known-axes semantic reconstruction succeeds;
    # only the existing floor/budget prerequisites refuse the public gate.
    assert decision.allowed is False
    _assert_exact_refusals(decision.refusals, {
        _FLOOR_REFUSAL,
        _BUDGET_REFUSAL,
    })

    assert released.allowed is False
    # M8: disabling the holdout generator check must remove generator_refusal
    # and fail this exact set, even though floor/budget still forbid execution.
    _assert_exact_refusals(released.refusals, {
        known_pin_refusal,
        generator_refusal,
        _FLOOR_REFUSAL,
        _BUDGET_REFUSAL,
    })
    assert verify_witness.call_args_list == [
        mock.call(root / migration.HOLDOUT_REL, root=root),
        mock.call(root / migration.HOLDOUT_REL, root=root),
    ]

    _assert_exact_refusals(sentinel_decision.refusals, {
        "holdout-freeze-verify: FreezeError: " + verifier_sentinel,
        _FLOOR_REFUSAL,
        _BUDGET_REFUSAL,
    })


def test_exit_code_priority_table():
    """rc 優先順位表: internal-error(1) > protocol_violation(3) >
    budget-refused(2) > completed(0)。gate-refused も 2、未知 status は 1。"""
    assert driver._exit_code("completed") == 0
    assert driver._exit_code("error") == 1
    assert driver._exit_code("protocol_violation") == 3
    assert driver._exit_code("budget_exhausted_before_attempt") == 2
    assert driver._exit_code("refused") == 2
    # 未知・欠測 status は fail-closed で internal-error(1)。
    assert driver._exit_code("something-unexpected") == 1
    assert driver._exit_code(None) == 1


def test_v3_all_rows_binding_refused_is_protocol_violation(tmp_path):
    """V3 (in-process): 全行 binding-refused で evaluate 0 回、status=protocol_violation。

    現行契約では completed / rc 0 に潰れていた (全行 refused でも budget_stopped で
    なければ completed)。強い completed 定義の下では 1 行でも terminal outcome を
    得なければ protocol_violation に倒す。
    """
    freeze_path = _synthetic_freeze(tmp_path)
    manifest_prepare = _prepare_factory()
    manifest_path, document = _write_manifest(
        tmp_path, freeze_path, manifest_prepare,
    )
    # manifest とは異なる src_token を全行で作らせ、全 binding を不一致にする。
    prepare_fn = _prepare_factory(token_suffix="-changed")
    evaluate_fn = _fake_evaluate_factory()

    result = _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn)

    assert result["status"] == "protocol_violation"
    assert result["completed_trials"] == 0
    # 一行も evaluate に到達しない。
    assert evaluate_fn.calls == []
    # 全予定行が未解決として列挙される。
    rows = document["schedule"]["rows"]
    assert set(result["unresolved_rows"]) == {
        row["schedule_index"] for row in rows
    }
    # terminal event が耐久化される。
    events = [event["event"] for event in result["events"]]
    assert events[-2:] == ["protocol-violation", "campaign-terminal"]
    terminal = result["events"][-1]
    assert terminal["status"] == "aborted"
    assert terminal["completed_rows"] == 0
    assert terminal["scheduled_rows"] == len(rows)
    # protocol_violation では精算しない (reservation は held のまま非解放)。
    ledger = s8b_budget.read_ledger(
        tmp_path / "budget.json",
        manifest_sha256=result["manifest_sha256"],
        freeze_sha256=result["freeze_sha256"],
        schedule_sha256=result["schedule_sha256"],
    )
    assert ledger["reservation"]["status"] == "held"
    assert ledger["entries"] == []


def test_v3_partial_binding_refused_is_protocol_violation(tmp_path):
    """1 行だけ binding-refused でも強い completed 定義を満たさず protocol_violation。"""
    freeze_path = _synthetic_freeze(tmp_path)
    manifest_prepare = _prepare_factory()
    manifest_path, document = _write_manifest(
        tmp_path, freeze_path, manifest_prepare,
    )
    # 1 行目だけ src_token を変えて binding を不一致にする。
    prepare_fn = _prepare_factory(token_suffix="-changed", suffix_first_only=True)
    evaluate_fn = _fake_evaluate_factory()

    result = _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn)

    rows = document["schedule"]["rows"]
    assert result["status"] == "protocol_violation"
    assert result["completed_trials"] == len(rows) - 1
    assert len(result["unresolved_rows"]) == 1
    # held のまま (精算しない)。
    ledger = s8b_budget.read_ledger(
        tmp_path / "budget.json",
        manifest_sha256=result["manifest_sha256"],
        freeze_sha256=result["freeze_sha256"],
        schedule_sha256=result["schedule_sha256"],
    )
    assert ledger["reservation"]["status"] == "held"


def test_v3_cli_subprocess_returns_rc_3_on_protocol_violation(tmp_path):
    """V3 (subprocess): 全行 binding-refused の CLI 実行が rc 3 を返す。

    in-process だけでなく実プロセス起動で rc を固定する。gate は strict v2
    verifier 未実装のため子プロセス内で future-approved に差し替え、canonical
    budget path も tmp に退避して repo 出力を汚さない。現行 CLI は completed 以外を
    一律 rc 2 (gate-refused/非 completed) に潰し、この経路は rc 0 だった。
    """
    freeze_path = _synthetic_freeze(tmp_path)
    manifest_prepare = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, manifest_prepare)
    approved = _APPROVED_BY_PATH[manifest_path.resolve()]
    output_root = tmp_path / "cli-out"
    budget_path = tmp_path / "cli-budget.json"
    admission_root = tmp_path / "cli-admission"
    admission_root.mkdir()
    (admission_root / "claims").mkdir()
    (admission_root / "consumed").mkdir()
    (admission_root / "measurement-generation-claims").mkdir()
    (admission_root / "measurement-generation-consumed").mkdir()
    (admission_root / "ledger.lock").write_bytes(b"")

    # 全行 binding-refused を CLI 経路で再現するため、driver.prepare_cell を
    # manifest とは異なる src_token を返す fixture に差し替える。
    script = textwrap.dedent(
        f"""
        import contextlib, hashlib, json, sys
        from pathlib import Path
        from unittest import mock
        sys.path.insert(0, {str(ORCHESTRATOR.parent)!r})
        from orchestrator.campaign import s8b_oracle_driver as driver
        from orchestrator.campaign import env_contract as ec
        from orchestrator.campaign import execution_guard
        from orchestrator.campaign import s8b_oracle_spec
        from orchestrator.campaign import s8b_ratified_freeze
        from orchestrator.campaign.model import Genome
        from orchestrator.campaign.s1_direct_comparison import PreparedCell

        @contextlib.contextmanager
        def fake_prepare(cell, ccbench_pin, *, cxx):
            entry = cell["variant"]
            genome = Genome("silo", dict(entry["flags"]))
            token = "fixture-" + hashlib.sha256(
                json.dumps(entry, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")).encode("utf-8")
            ).hexdigest() + "-changed"
            yield PreparedCell(
                genome=genome, src_token=token,
                ccbench_dir="/tmp/fixture-ccbench",
                cache_root="/tmp/fixture-cache",
            )

        freeze_raw = Path({str(freeze_path)!r}).read_bytes()
        ratified = s8b_ratified_freeze.RatifiedFreeze(
            document=json.loads(freeze_raw),
            sha256=hashlib.sha256(freeze_raw).hexdigest(), generation_number=1,
            activation_head="f" * 40, generation_commit="e" * 40)
        floor = s8b_ratified_freeze.VerifiedFloorArtifact(
            path="fixture/result.json", raw_bytes=b"{{}}",
            sha256=hashlib.sha256(b"{{}}").hexdigest(), document={{}})
        validated = s8b_ratified_freeze.LaunchValidatedFreeze(
            ratified=ratified, activation_head=ratified.activation_head,
            search_digest="d" * 64, symlink_gitlink_inventory=(),
            floor_artifact=floor, binaries_by_cell={{}})

        def fake_plan(**kwargs):
            contract = ec.lookup("linux-baremetal")
            perf = {{(r["holdout_id"], r["configuration_id"]): "0" * 64
                     for r in kwargs["schedule"]}}
            return driver._V2Plan(
                contract=contract,
                authorization_contract=ec.authorize("linux-baremetal"),
                receipt=execution_guard.build_receipt(contract),
                perf_sha_by_cell=perf)

        stable_receipt_epoch = driver._t080_migration.ReceiptResolution(
            "never-issued", (), None, "c" * 40,
        )

        spec_raw = {approved.raw_bytes!r}
        spec_document = json.loads(spec_raw)
        validated_spec, spec_schedule = s8b_oracle_spec.validate_reviewed_spec(
            spec_document, root=Path({str(ROOT)!r}),
        )
        approved_spec = s8b_oracle_spec.ReviewedSpec(
            document=validated_spec, raw_bytes=spec_raw,
            sha256={approved.sha256!r}, schedule=spec_schedule,
        )
        s8b_oracle_spec.APPROVED_SPEC_SHA256 = approved_spec.sha256

        driver.DEFAULT_BUDGET_PATH = {str(budget_path)!r}
        with mock.patch.object(
                driver, "_gate_check_validated",
                return_value=driver.GateDecision(True, [], None)), \\
             mock.patch.object(driver, "_resolve_t080_receipt",
                               return_value=stable_receipt_epoch), \\
             mock.patch.object(driver.s8b_ratified_freeze,
                               "load_ratified_freeze", return_value=ratified), \\
             mock.patch.object(driver.s8b_ratified_freeze,
                               "launch_validate", return_value=validated), \\
             mock.patch.object(driver.s8b_oracle_spec,
                               "load_approved_spec", return_value=approved_spec), \\
             mock.patch.object(driver, "_prepare_v2_execution", fake_plan), \\
             mock.patch.object(driver._holdout_admission,
                               "provision_shared_admission_root",
                               return_value=Path({str(admission_root)!r})), \\
             mock.patch.object(driver, "prepare_cell", fake_prepare):
            rc = driver.main([
                "run-block", "--manifest", {str(manifest_path)!r},
                "--block-id", "b0", "--freeze", {str(freeze_path)!r},
                "--root", {str(ROOT)!r}, "--output-root", {str(output_root)!r},
            ])
        sys.exit(rc)
        """
    )
    proc = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True,
    )
    assert proc.returncode == 3, (proc.returncode, proc.stdout, proc.stderr)
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["status"] == "protocol_violation"
    assert payload["completed_trials"] == 0


def test_cli_subprocess_returns_rc_2_on_gate_refused(tmp_path):
    """gate 拒否 (real freeze に active generation 無し) を CLI 実行が rc 2 +
    stdout JSON の refusal へ transport する。"""
    manifest_freeze = _synthetic_freeze(tmp_path)
    manifest_prepare = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, manifest_freeze, manifest_prepare)
    output_root = tmp_path / "gate-out"
    budget_path = tmp_path / "gate-budget.json"

    script = textwrap.dedent(
        f"""
        import sys
        sys.path.insert(0, {str(ORCHESTRATOR.parent)!r})
        from orchestrator.campaign import s8b_oracle_driver as driver
        driver.DEFAULT_BUDGET_PATH = {str(budget_path)!r}
        rc = driver.main([
            "run-block", "--manifest", {str(manifest_path)!r},
            "--block-id", "b0", "--freeze", {str(REAL_FREEZE)!r},
            "--root", {str(ROOT)!r}, "--output-root", {str(output_root)!r},
        ])
        sys.exit(rc)
        """
    )
    proc = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True,
    )
    assert proc.returncode == 2, (proc.returncode, proc.stdout, proc.stderr)
    payload = json.loads(proc.stdout)
    assert payload["status"] == "refused"
    assert payload["allowed"] is False
    _assert_exact_refusals(payload["refusals"], {_NO_ACTIVE_REFUSAL})
    assert not output_root.exists() and not budget_path.exists()


def test_load_verified_freeze_single_read_hash_and_strict_parse(tmp_path):
    """loader 単体 (中立 leaf s8b_freeze_io) は byte sha256 を返し、expected_hash
    不一致と非 strict JSON を拒否する (単一 read の hash 束縛と strict parse の直接
    検査)。loader 単体の例外型は FreezeIOError で固定する。"""
    freeze_path = _synthetic_freeze(tmp_path)
    expected = _sha256(freeze_path)

    verified = s8b_freeze_io.load_verified_freeze(freeze_path)
    assert verified.sha256 == expected
    assert verified.document == json.loads(freeze_path.read_text(encoding="utf-8"))

    # expected_hash と一致すれば同じ object を返す。
    assert s8b_freeze_io.load_verified_freeze(
        freeze_path, expected_hash=expected).sha256 == expected
    # 不一致は fail-closed (loader 単体経路は FreezeIOError)。
    with pytest.raises(s8b_freeze_io.FreezeIOError) as mismatch:
        s8b_freeze_io.load_verified_freeze(freeze_path, expected_hash="0" * 64)
    assert "expected_hash" in str(mismatch.value)

    # strict parse: NaN 等の非数値定数を拒否する。
    bad = tmp_path / "bad_freeze.json"
    bad.write_text('{"floor": NaN}', encoding="utf-8")
    with pytest.raises(s8b_freeze_io.FreezeIOError) as strict:
        s8b_freeze_io.load_verified_freeze(bad)
    assert "strict parse" in str(strict.value) or "非数値定数" in str(strict.value)


def test_driver_boundary_wraps_freeze_io_error_as_oracle_driver_error(tmp_path):
    """driver 境界 adapter (_load_verified_freeze) は leaf の FreezeIOError を
    OracleDriverError へ因果付き変換し、message 本文を維持する (driver 経路の
    例外型は OracleDriverError で固定)。"""
    bad = tmp_path / "bad_freeze.json"
    bad.write_text('{"floor": NaN}', encoding="utf-8")
    with pytest.raises(driver.OracleDriverError) as wrapped:
        driver._load_verified_freeze(bad)
    assert isinstance(wrapped.value.__cause__, s8b_freeze_io.FreezeIOError)
    assert "非数値定数" in str(wrapped.value)


def test_run_block_reuses_launch_validated_and_legacy_loader_is_dead(tmp_path):
    """同一 LaunchValidatedFreeze を gate / plan へ渡し、旧 loader は呼ばない。"""
    freeze_path = _synthetic_freeze(tmp_path, total_bench_s=1000.0)
    prepare_fn = _prepare_factory()
    manifest_path, _document = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory()

    real_read_bytes = Path.read_bytes
    freeze_reads: list[Path] = []

    def counting_read_bytes(self):
        if Path(self) == Path(freeze_path):
            freeze_reads.append(Path(self))
        return real_read_bytes(self)

    validated = _fake_launch_validated(freeze_path)
    captured: dict = {}

    def recording_gate(*, freeze_path, manifest_path, root, t080_resolution=None,
                       verified=None,
                       verified_manifest=None, launch_validated=None,
                       approved_spec=None, manifest_verification_error=None,
                       ratified=None, ratified_error=None):
        captured["launch_validated"] = launch_validated
        captured["verified_manifest"] = verified_manifest
        return driver.GateDecision(True, [], None)

    def recording_plan(**kwargs):
        captured["plan_validated"] = kwargs["validated"]
        return _canned_plan(**kwargs)

    # [T-057] 対象は loader identity と read 回数。receipt 解決は incidental なので memo する。
    with receipt_memo.patch_driver_resolver(), \
            mock.patch.object(Path, "read_bytes", counting_read_bytes), \
            mock.patch.object(
                driver, "_load_verified_freeze",
                side_effect=AssertionError("legacy freeze loader called")), \
            mock.patch.object(
                driver._freeze_io, "load_verified_freeze",
                side_effect=AssertionError("legacy freeze leaf loader called")), \
            mock.patch.object(driver.s8b_ratified_freeze,
                              "load_ratified_freeze",
                              return_value=validated.ratified), \
            mock.patch.object(driver.s8b_ratified_freeze,
                              "launch_validate", return_value=validated), \
            mock.patch.object(driver, "_prepare_v2_execution", recording_plan), \
            mock.patch.object(driver, "_gate_check_validated", recording_gate), \
            _isolated_oracle_admission_root(tmp_path):
        result = driver.run_block(
            manifest_path=manifest_path, block_id="b0",
            freeze_path=freeze_path, root=ROOT,
            output_root=tmp_path / "out", budget_path=tmp_path / "budget.json",
            marker_root=tmp_path / "markers",
            prepare_fn=prepare_fn, evaluate_fn=evaluate_fn,
        )

    assert result["status"] == "completed"
    # freeze_path は active bytes hash 照合 1 回だけ。document は別 loader で読まない。
    assert len(freeze_reads) == 1
    assert captured["launch_validated"] is validated
    assert captured["plan_validated"] is validated
    # C2-9: gate_check には検証済み VerifiedManifest が渡り (再検証させない)、
    # run_block はそれを本体でも使い回す (再読込しない)。
    assert isinstance(captured["verified_manifest"], manifest_module.VerifiedManifest)


def test_run_block_verifies_manifest_once_and_reuses_object(tmp_path):
    """C2-9 / A3-6 (manifest 側): run_block は manifest を厳密 1 回だけ verify し、
    その単一 VerifiedManifest object を gate と本体で共有する (verify->use 間の
    再読込・再検証をしない)。freeze 側の read=1 + 同一 object 固定
    (test_run_block_loads_freeze_once...) の manifest 版。

    恒真回避: verify_manifest 呼び出し数・manifest byte read 数・gate へ渡った
    object の identity を同時に固定する。本体が manifest を disk から再読込する
    (raw re-read) か再検証する (verify_manifest 再呼び出し) 退行はどちらも
    read>1 / verify>1 で kill される。
    """
    freeze_path = _synthetic_freeze(tmp_path, total_bench_s=1000.0)
    prepare_fn = _prepare_factory()
    manifest_path, _document = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory()
    validated = _fake_launch_validated(freeze_path)

    real_read_text = Path.read_text
    manifest_reads: list[Path] = []

    def counting_read_text(self, *args, **kwargs):
        if Path(self) == Path(manifest_path):
            manifest_reads.append(Path(self))
        return real_read_text(self, *args, **kwargs)

    real_verify = driver.verify_manifest
    verify_calls: list[Path] = []
    captured: dict = {}

    def counting_verify(path, **kwargs):
        verify_calls.append(Path(path))
        result = real_verify(path, **kwargs)
        captured["verified_manifest"] = result
        return result

    def recording_gate(*, freeze_path, manifest_path, root, t080_resolution=None,
                       verified=None,
                       verified_manifest=None, launch_validated=None,
                       approved_spec=None, manifest_verification_error=None,
                       ratified=None, ratified_error=None):
        captured["gate_manifest"] = verified_manifest
        captured["approved_spec"] = approved_spec
        return driver.GateDecision(True, [], None)

    # [T-057] 対象は manifest verify / read 回数。receipt 解決は incidental なので memo する。
    with receipt_memo.patch_driver_resolver(), \
            mock.patch.object(Path, "read_text", counting_read_text), \
            mock.patch.object(driver, "verify_manifest", counting_verify), \
            mock.patch.object(driver.s8b_ratified_freeze,
                              "load_ratified_freeze",
                              return_value=validated.ratified), \
            mock.patch.object(driver.s8b_ratified_freeze,
                              "launch_validate", return_value=validated), \
            mock.patch.object(driver, "_prepare_v2_execution", _canned_plan), \
            mock.patch.object(driver, "_gate_check_validated", recording_gate), \
            _isolated_oracle_admission_root(tmp_path):
        result = driver.run_block(
            manifest_path=manifest_path, block_id="b0",
            freeze_path=freeze_path, root=ROOT,
            output_root=tmp_path / "out", budget_path=tmp_path / "budget.json",
            marker_root=tmp_path / "markers",
            prepare_fn=prepare_fn, evaluate_fn=evaluate_fn,
        )

    assert result["status"] == "completed"
    # manifest は厳密 1 回だけ verify され (本体は再検証しない)。
    assert len(verify_calls) == 1
    # manifest byte read もちょうど 1 回 (本体は verified object を使い再読込しない)。
    assert len(manifest_reads) == 1
    # gate へ渡った VerifiedManifest は verify_manifest が返したまさに同一 object。
    assert isinstance(captured["verified_manifest"], manifest_module.VerifiedManifest)
    assert captured["gate_manifest"] is captured["verified_manifest"]
    assert captured["approved_spec"] is _ACTIVE_APPROVED.reviewed_spec


def test_v6_freeze_swap_after_verify_is_not_observed(tmp_path):
    """V6: gate/manifest 検証後に freeze bytes を差し替えても、単一 object 使い回し
    (load_verified_freeze) により差替え後の値 (budget limits・perf 三軸) が一切
    使われない。

    verify_manifest 直後に freeze ファイルを悪性 bytes (holdout records を +777、
    budget を 0.0) へ差し替える。単一 object を使う実装では driver は元の verified
    値だけを使い completed になる。もし verify 後に freeze を再読込する構造なら、
    差替え後の budget=0 で budget_exhausted に倒れ、perf.records も +777 に汚染
    されるため FAIL する (verify-use 間 TOCTOU の再現を kill する)。
    """
    freeze_path = _synthetic_freeze(tmp_path, total_bench_s=1000.0)
    prepare_fn = _prepare_factory()
    manifest_path, _document = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory()

    original = json.loads(freeze_path.read_text(encoding="utf-8"))
    original_records = {
        holdout_id: original["holdouts"][holdout_id]["records"]
        for holdout_id in _holdout_ids()
    }
    poisoned_records = {value + 777 for value in original_records.values()}
    real_verify = manifest_module.verify_manifest

    def swapping_verify(path, **kwargs):
        result = real_verify(path, **kwargs)
        # 検証が通った直後に freeze ファイルを悪性 bytes へ差し替える。
        malicious = json.loads(freeze_path.read_text(encoding="utf-8"))
        for holdout_id in _holdout_ids():
            malicious["holdouts"][holdout_id]["records"] = (
                original_records[holdout_id] + 777
            )
        malicious["budget"]["total_bench_s"] = 0.0
        malicious["budget"]["per_holdout_bench_s"] = {
            holdout_id: 0.0 for holdout_id in _holdout_ids()
        }
        freeze_path.write_text(
            json.dumps(malicious, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return result

    with mock.patch.object(driver, "verify_manifest", swapping_verify):
        result = _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn)

    # 差替え後の budget=0 が使われていれば budget_exhausted。単一 object なら completed。
    assert result["status"] == "completed"
    # perf 三軸: records は元の値で、+777 の汚染値を一切含まない。
    assert evaluate_fn.calls
    for call in evaluate_fn.calls:
        assert call["perf"].records in original_records.values()
        assert call["perf"].records not in poisoned_records
    # budget limits も元の 1000.0 (差替え後の 0.0 でない)。
    ledger = s8b_budget.read_ledger(
        tmp_path / "budget.json",
        manifest_sha256=result["manifest_sha256"],
        freeze_sha256=result["freeze_sha256"],
        schedule_sha256=result["schedule_sha256"],
    )
    assert ledger["limits"]["total_bench_s"] == pytest.approx(1000.0)


def test_v7_manifest_swap_after_verify_is_not_observed(tmp_path):
    """V7: gate/本体で共有する VerifiedManifest により、verify 後に manifest bytes を
    差し替えても差替え後の値 (campaign_id) が一切使われない (C2-9 の manifest 版)。

    verify_manifest 直後に manifest ファイルの campaign_ids を悪性値へ差し替える。
    単一 object を使う実装では driver は元の verified document だけを使い、
    result["campaign_id"] は差替え前の値のまま completed になる。もし verify 後に
    manifest を再読込 (raw) または再検証する構造なら差替え後の campaign_id を観測して
    FAIL する (verify-use 間 TOCTOU の再現を kill する)。V6 が freeze に対して行うのと
    同型。
    """
    freeze_path = _synthetic_freeze(tmp_path, total_bench_s=1000.0)
    prepare_fn = _prepare_factory()
    manifest_path, document = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory()

    original_campaign_id = manifest_module.config_for_block(
        document, "b0")["campaign_id"]
    poisoned_campaign_id = original_campaign_id + "-POISONED"
    real_verify = manifest_module.verify_manifest

    def swapping_verify(path, **kwargs):
        result = real_verify(path, **kwargs)
        # 検証が通った直後に manifest の campaign_ids を悪性値へ差し替える。
        malicious = json.loads(manifest_path.read_text(encoding="utf-8"))
        malicious["campaign_ids"]["b0"] = poisoned_campaign_id
        manifest_path.write_text(
            json.dumps(malicious, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return result

    with mock.patch.object(driver, "verify_manifest", swapping_verify):
        result = _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn)

    # 単一 object 実装なら差替え前の campaign_id で completed。再読込/再検証する退行は
    # 差替え後の POISONED を観測する。
    assert result["status"] == "completed"
    assert result["campaign_id"] == original_campaign_id
    assert result["campaign_id"] != poisoned_campaign_id


def test_layer3_strict_consumer_accepts_optional_bench_wall_s():
    """layer3_schema.json の runs 定義で bench_wall_s の型と非必須性を構造として pin する。layer3_report._validate_schema / build_report は呼ばない。"""
    schema = json.loads(
        (ORCHESTRATOR / "campaign/layer3_schema.json").read_text(encoding="utf-8")
    )
    runs = schema["properties"]["runs"]["items"]
    assert runs["additionalProperties"] is False
    assert runs["properties"]["bench_wall_s"] == {
        "type": "number", "minimum": 0,
    }
    assert "bench_wall_s" not in runs["required"]


# ---- R6: resume 拒否の強化 (原子的 lock + 実走済みマーカー + truncated WAL 閉鎖) ----

def _campaign_id(manifest_path: Path) -> str:
    # campaign_id の抽出だけが目的なので verify (freeze_document 必須) は経由せず、
    # plain load + config_for_block で射影する。
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    return manifest_module.config_for_block(document, "b0")["campaign_id"]


def test_v2_resume_rejected_at_s1_s2_s3_boundaries(tmp_path):
    """V2 (択 a): S1/S2/S3 各境界直後の crash を模擬し、再起動が全拒否されること。

    S1 = 実走済みマーカー + lock 生成済み・WAL なし、S2 = ledger も生成済み・WAL なし、
    S3 = campaign-start が WAL に耐久化済み。いずれの境界でも新プロセスの resume は
    構造化拒否 (OracleDriverError) で倒れ、prepare/evaluate に一切到達しない。
    """
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory()

    output_root = tmp_path / "out"
    marker_root = tmp_path / "markers"
    identity = s8b_run_marker.freeze_identity(freeze_path)
    layout = campaign_layout(_campaign_id(manifest_path), output_root=str(output_root))

    def attempt():
        return _run(tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn,
                    output_root=output_root, marker_root=marker_root)

    # S1: マーカー + lock 生成済み、WAL/ledger なし。
    layout.ensure()
    assert wal.acquire_lock_atomic(layout, "s1-preimage") is True
    s8b_run_marker.create_run_marker(marker_root, identity, {"stage": "s1"})
    with pytest.raises(driver.OracleDriverError) as s1:
        attempt()
    assert "マーカー" in str(s1.value)

    # S2: ledger 生成済みでも WAL がまだ無い段階。境界は S1 と同じくマーカーが捕捉する。
    s8b_budget.create_ledger(
        tmp_path / "budget.json", manifest_sha256="deadbeef",
        freeze_sha256=identity, schedule_sha256="cafebabe",
        limits={"total_bench_s": 1.0,
                "per_holdout_bench_s": {h: 1.0 for h in _holdout_ids()},
                "oracle_shared": True},
    )
    with pytest.raises(driver.OracleDriverError) as s2:
        attempt()
    assert "マーカー" in str(s2.value)

    # S3: campaign-start が WAL に耐久化済み (実走中 crash)。WAL byte 存在で拒否。
    driver._append_session(layout, "fixture-env", "campaign-start", {
        "campaign_id": layout.root, "block_id": "b0",
    })
    assert wal.wal_bytes_present(layout) is True
    with pytest.raises(driver.OracleDriverError) as s3:
        attempt()
    assert "WAL byte" in str(s3.value)

    assert prepare_fn.calls == [] and evaluate_fn.calls == []


def test_atomic_one_shot_lock_rejects_second_start(tmp_path):
    """既存 campaign.lock (マーカー無し) の resume/並行起動を原子的 lock が拒否する。

    O_CREAT|O_EXCL による one-shot lock の獲得失敗 = 着手済み/並行として fail-closed。
    非原子の write_lock (exists→上書きなし) では二重通過しうる経路を閉じる。
    """
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()

    output_root = tmp_path / "out"
    layout = campaign_layout(_campaign_id(manifest_path), output_root=str(output_root))
    layout.ensure()
    assert wal.acquire_lock_atomic(layout, "prior-holder") is True
    # 同じ lock の二度目の原子的獲得は False。
    assert wal.acquire_lock_atomic(layout, "second-holder") is False

    with pytest.raises(driver.OracleDriverError) as excinfo:
        _run(tmp_path, freeze_path, manifest_path, prepare_fn,
             _fake_evaluate_factory(), output_root=output_root,
             marker_root=tmp_path / "markers-lock")
    assert "campaign.lock" in str(excinfo.value)
    assert prepare_fn.calls == []


def test_resume_wal_lstat_eio_propagates_fail_closed_from_public_driver(
        tmp_path, monkeypatch):
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    output_root = tmp_path / "eio-out"
    layout = campaign_layout(
        _campaign_id(manifest_path), output_root=str(output_root),
    )
    real_lstat = wal.os.lstat

    def fail_wal_lstat(path, *args, **kwargs):
        if os.fspath(path) == os.fspath(layout.wal_file):
            raise OSError(errno.EIO, "injected s8b WAL lstat EIO")
        return real_lstat(path, *args, **kwargs)

    monkeypatch.setattr(wal.os, "lstat", fail_wal_lstat)
    with pytest.raises(OSError) as excinfo:
        _run(
            tmp_path, freeze_path, manifest_path, prepare_fn,
            _fake_evaluate_factory(), output_root=output_root,
            marker_root=tmp_path / "eio-markers",
        )
    assert excinfo.value.errno == errno.EIO
    assert prepare_fn.calls == []
    assert not os.path.exists(layout.lock_file)
    assert not os.path.exists(layout.wal_file)


def test_driver_full_frame_fsync_eio_is_not_folded_or_followed_up(
        tmp_path, monkeypatch):
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    output_root = tmp_path / "fsync-out"
    layout = campaign_layout(
        _campaign_id(manifest_path), output_root=str(output_root),
    )
    real_fsync = wal.os.fsync
    injection = {"active": False, "calls": 0}

    def fail_target_fsync(fd):
        try:
            path = os.readlink("/proc/self/fd/%d" % fd)
        except OSError:
            path = ""
        if injection["active"] and path == layout.wal_file:
            injection["calls"] += 1
            raise OSError(errno.EIO, "injected s8b full-frame fsync EIO")
        return real_fsync(fd)

    def fail_inside_evaluate(genome, candidate_layout, env_tag, *_args, **kwargs):
        injection["active"] = True
        variant = pipeline.variant_id(genome, kwargs["src_token"])
        wal.log(candidate_layout, variant, model.STAGE_BUILD_START, env_tag, {
            "genome": genome.canonical(), "src_token": kwargs["src_token"],
        })
        raise AssertionError("WalAppendError の後へ到達してはならない")

    monkeypatch.setattr(wal.os, "fsync", fail_target_fsync)
    with pytest.raises(wal.WalAppendError) as excinfo:
        _run(
            tmp_path, freeze_path, manifest_path, prepare_fn,
            fail_inside_evaluate, output_root=output_root,
            marker_root=tmp_path / "fsync-markers",
        )
    assert excinfo.value.phase == "fsync"
    assert excinfo.value.written_bytes == excinfo.value.total_bytes
    assert injection["calls"] == 1
    records, truncated = wal.read_records_checked(layout)
    assert truncated is False
    assert [record.payload.get("event") for record in records
            if record.stage == driver.SESSION_STAGE] == [
                "campaign-start", "trial-start",
            ]
    assert records[-1].stage == model.STAGE_BUILD_START


def test_v4_marker_fires_across_output_root_change(tmp_path):
    """V4: 実走済みマーカーが --output-root 非依存に発火し、別 output-root での再走を拒否。"""
    freeze_path = _synthetic_freeze(tmp_path)
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, _prepare_factory())
    marker_root = tmp_path / "freeze-side"

    # 1 回目: output-root A で完走。マーカーは marker_root (output-root 非依存) に残る。
    result_a = _run(
        tmp_path, freeze_path, manifest_path,
        _prepare_factory(), _fake_evaluate_factory(),
        output_root=tmp_path / "out-a", budget_path=tmp_path / "budget-a.json",
        marker_root=marker_root,
    )
    assert result_a["status"] == "completed"
    identity = s8b_run_marker.freeze_identity(freeze_path)
    assert s8b_run_marker.marker_exists(marker_root, identity)

    # 2 回目: 別 output-root・別 budget (WAL も lock も無い新出力先)。マーカーが
    # output-root 非依存で残るため再走を全拒否する。マーカーを output_root 配下に
    # 置く実装ならここは素通りしてしまう (迂回) — その変異を kill する。
    prepare_b = _prepare_factory()
    with pytest.raises(driver.OracleDriverError) as excinfo:
        _run(
            tmp_path, freeze_path, manifest_path,
            prepare_b, _fake_evaluate_factory(),
            output_root=tmp_path / "out-b", budget_path=tmp_path / "budget-b.json",
            marker_root=marker_root,
        )
    assert "マーカー" in str(excinfo.value)
    assert prepare_b.calls == []


@pytest.mark.parametrize(
    "tail",
    [
        pytest.param(
            b'{"variant":"oracle-session","stage":"s8b-oracle-session"',
            id="fragment",
        ),
        pytest.param(
            json.dumps({
                "variant": "oracle-session",
                "stage": model.STAGE_S8B_ORACLE_SESSION,
                "env_tag": "fixture-env",
                "ts": 1,
                "payload": {"event": "campaign-start"},
            }, separators=(",", ":")).encode("utf-8"),
            id="complete-json-without-newline",
        ),
        pytest.param(
            b'{"variant":"oracle-\xe3\x81',
            id="multibyte-partial",
        ),
    ],
)
def test_v5_truncated_wal_rejects_resume_even_with_zero_parseable_records(
        tmp_path, tail):
    """V5: newline 無終端 WAL (parse 可能 record 0 件) は内容によらず拒否。

    read_records は末尾切れの 1 行を捨てて [] を返す。resume 判定を「parse 可能 record」
    でなく「byte の存在」で行うことで、この truncated WAL 迂回を閉じる (fail-closed)。
    """
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()

    output_root = tmp_path / "out"
    layout = campaign_layout(_campaign_id(manifest_path), output_root=str(output_root))
    layout.ensure()
    with open(layout.wal_file, "wb") as stream:
        stream.write(tail)
    assert wal.read_records(layout) == []          # parse 可能 record 0 件
    assert os.path.getsize(layout.wal_file) > 0     # だが byte は存在する

    with pytest.raises(driver.OracleDriverError) as excinfo:
        _run(tmp_path, freeze_path, manifest_path, prepare_fn,
             _fake_evaluate_factory(), output_root=output_root,
             marker_root=tmp_path / "markers-v5")
    assert "WAL byte" in str(excinfo.value)
    assert prepare_fn.calls == []


def test_session_stage_reexports_shared_model_authority():
    # '-' 入り literal を CPython が自動 intern しないことに依存し、再 literal 化を検出する。
    assert driver.SESSION_STAGE is model.STAGE_S8B_ORACLE_SESSION


def test_session_issuer_alias_and_append_use_model_authority(tmp_path, monkeypatch):
    sentinel = "".join(("sentinel", "-session-issuer"))
    try:
        with monkeypatch.context() as scoped:
            scoped.setattr(model, "S8B_ORACLE_SESSION_ISSUER", sentinel)
            importlib.reload(driver)
            assert driver.SESSION_ISSUER is model.S8B_ORACLE_SESSION_ISSUER

            layout = campaign_layout(
                "issuer-authority", output_root=str(tmp_path),
            ).ensure()
            driver._append_session(
                layout, "linux-baremetal", "campaign-start",
                {"campaign_id": "issuer-authority"},
            )
            records = wal.read_records(layout)

            assert len(records) == 1
            assert records[0].variant == sentinel
            assert records[0].stage == model.STAGE_S8B_ORACLE_SESSION
    finally:
        importlib.reload(driver)


# ===========================================================================
# W4: v2 実走 gate (承認束縛 active 世代) の実発火テスト (git fixture)
#
# E3a の production-emitter fixture が生成した official result bytes と store をそのまま
# 使い、gate / launch_validate / env 契約 / store 消費 / receipt 伝搬を発火させる。
# ===========================================================================

def _build_v2_repo(tmp_path: Path, *, floor_extime_s: int = 5):
    """E3a production-emitter bytes から oracle 実走 fixture を返す。"""
    def fill_execution_snapshot(g1):
        # emitter が result.floors から独立投影した floor は保持し、
        # oracle 実走 fixture に必要な budget だけを追加する。
        g1["budget"] = v2_fixture.budget(
            g1, total_bench_s=1000.0, per_holdout_bench_s=1000.0,
        )

    mutate = None
    if floor_extime_s != 5:
        def mutate(state):
            # production emitter が正式 bytes を生成した後の protocol だけを変更する。
            # raw hash と generation record は emitter 自身が再構築するため、static
            # ratified loader は通り、full launch validation の数値 pin だけを攻撃できる。
            state["protocol"]["extime_s"] = floor_extime_s

    root, ratified, topology = ratified_fixture.load_emitter_g1(
        tmp_path, mutate=mutate, mutate_g1=fill_execution_snapshot,
    )
    # Keep the emitter artifacts in the git-backed repo, but run the official
    # campaign against its uninitialized sibling root.
    shutil.copytree(root / "output", tmp_path / "output")
    return (
        root, root / topology["generation_path"], ratified.sha256,
        topology["result"]["binaries"], topology,
    )


def _emitter_manifest(tmp_path: Path, root: Path, freeze_path: Path):
    generator_paths = dict(GENERATOR_SOURCES)
    for role, relative_path in generator_paths.items():
        source = root / relative_path
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(f"hermetic generator fixture: {role}\n".encode("utf-8"))
    generation = json.loads(freeze_path.read_bytes())
    protocol_path = root / generation["floor_protocol"]["path"]
    floor_protocol = json.loads(protocol_path.read_bytes())
    with mock.patch.object(manifest_module, "ROOT", root):
        return _write_manifest(
            tmp_path, freeze_path, _prepare_factory(), source_root=root,
            generator_paths=generator_paths,
            ccbench_pin=floor_protocol["ccbench_pin"],
        )


def _tree_file_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _sha256(path)
        for path in root.rglob("*") if path.is_file()
    }


def _authorize_official_report_output(output_root: Path) -> None:
    """report consumer fixture に exact official runtime role を付与する。"""
    (output_root / "namespace.json").write_bytes(
        oracle_artifacts.OFFICIAL_NAMESPACE_BYTES,
    )


def _unique_store_victim(binaries: dict) -> dict:
    victims = [
        rec for rec in binaries.values()
        if sum(
            candidate["store_path"] == rec["store_path"]
            for candidate in binaries.values()
        ) == 1
    ]
    assert victims, binaries
    victim = victims[0]
    assert sum(
        candidate["store_path"] == victim["store_path"]
        for candidate in binaries.values()
    ) == 1
    return victim


def _run_v2(root: Path, freeze_path: Path, manifest_path: Path, prepare_fn,
            evaluate_fn, *, out_root: Path, tmp_path: Path):
    """v2 実走 (承認束縛 gate/launch/env/store を実発火)。

    known_axes freeze の source provenance 検査だけは orthogonal な legacy 検査で、実 repo の
    external/ccbench submodule (この環境では未初期化) を要求するため tmp repo では成立しない。
    本レーンの検査対象 (v2 承認束縛 gate + launch_validate + env 契約 + store 消費) を分離する
    ため、この 1 検査だけ no-op に差し替える (ccbench 未初期化はこの環境の制約)。"""
    with mock.patch.object(driver.s1_known_axes_freeze, "verify",
                           lambda *a, **k: None):
        return driver.run_block(
            manifest_path=manifest_path, block_id="b0", freeze_path=freeze_path,
            root=root, output_root=out_root,
            budget_path=tmp_path / "v2-budget.json",
            marker_root=tmp_path / "v2-markers",
            prepare_fn=prepare_fn, evaluate_fn=evaluate_fn,
        )


def _assert_extime_launch_refusal(decision):
    assert not decision.allowed
    _assert_exact_refusals(decision.refusals, {
        "v2-execution: launch-validate: [floor-artifact-invalid] "
        "[floor-artifact-invalid] floor protocol full validation 失敗: "
        "protocol.extime_s が承認凍結値と不一致 (受領 3 != 承認 5)",
    })


@in_sealed_fixture_process
def test_v2_standalone_gate_check_requires_full_floor_validation(tmp_path):
    """standalone v2 gate は self-load / injected static freeze を full validate する。"""
    real_load = driver.s8b_ratified_freeze.load_ratified_freeze
    real_launch = driver.s8b_ratified_freeze.launch_validate

    valid_root, valid_freeze, _sha, _bins, _topology = _build_v2_repo(
        tmp_path / "valid", floor_extime_s=5,
    )
    load_results = []
    launch_calls = []

    def recording_load(root):
        loaded = real_load(root)
        load_results.append(loaded)
        return loaded

    def recording_launch(candidate, root):
        launch_calls.append((candidate, root))
        return real_launch(candidate, root)

    with mock.patch.object(driver.s1_known_axes_freeze, "verify",
                           lambda *a, **k: None), \
            mock.patch.object(driver.s8b_ratified_freeze, "load_ratified_freeze",
                              side_effect=recording_load), \
            mock.patch.object(driver.s8b_ratified_freeze, "launch_validate",
                              side_effect=recording_launch):
        valid = driver.gate_check(freeze_path=valid_freeze, root=valid_root)
    assert valid.allowed, valid.refusals
    assert len(load_results) == 1 and len(launch_calls) == 1
    assert launch_calls[0][0] is load_results[0]
    assert launch_calls[0][1] == valid_root

    bad_root, bad_freeze, _sha, _bins, _topology = _build_v2_repo(
        tmp_path / "bad", floor_extime_s=3,
    )
    load_results.clear()
    launch_calls.clear()
    with mock.patch.object(driver.s1_known_axes_freeze, "verify",
                           lambda *a, **k: None), \
            mock.patch.object(driver.s8b_ratified_freeze, "load_ratified_freeze",
                              side_effect=recording_load), \
            mock.patch.object(driver.s8b_ratified_freeze, "launch_validate",
                              side_effect=recording_launch):
        bad_self_load = driver.gate_check(
            freeze_path=bad_freeze, root=bad_root,
        )
    _assert_extime_launch_refusal(bad_self_load)
    assert len(load_results) == 1 and len(launch_calls) == 1
    assert launch_calls[0][0] is load_results[0]
    assert launch_calls[0][1] == bad_root

    injected = real_load(bad_root)
    launch_calls.clear()
    with mock.patch.object(driver.s1_known_axes_freeze, "verify",
                           lambda *a, **k: None), \
            mock.patch.object(
                driver.s8b_ratified_freeze, "load_ratified_freeze",
                side_effect=AssertionError("injected RatifiedFreeze を再 load した")), \
            mock.patch.object(driver.s8b_ratified_freeze, "launch_validate",
                              side_effect=recording_launch):
        bad_injected = driver.gate_check(
            freeze_path=bad_freeze, root=bad_root, ratified=injected,
        )
    _assert_extime_launch_refusal(bad_injected)
    assert launch_calls == [(injected, bad_root)]


def test_private_validated_gate_has_only_run_block_as_production_caller():
    """public gate に validated bypass を再導入せず、private caller を本線だけに固定。"""
    assert "launch_validated" not in inspect.signature(driver.gate_check).parameters
    tree = ast.parse(inspect.getsource(driver))
    callers = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if any(
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id == "_gate_check_validated"
                for child in ast.walk(node)):
            callers.append(node.name)
    assert callers == ["run_block"]


@in_sealed_fixture_process
def test_v2_gate_happy_path_completes_and_binds_env_store_receipt(tmp_path):
    """v2 正常系: freeze==active 世代 + launch_validate 成立 + store 全一致 →
    gate 通過・completed。expected_perf_sha256 が cell の store binary sha と一致して
    evaluate に伝搬し、clocks/numactl は env 契約由来 (NUMACTL ハードコード撤去)、
    campaign-start に execution receipt が記録される。"""
    root, freeze_path, _gen_sha, binaries, _topology = _build_v2_repo(tmp_path)
    out_root = root.parent / "output"
    manifest_path, document = _emitter_manifest(tmp_path, root, freeze_path)
    evaluate_fn = _fake_evaluate_factory()

    result = _run_v2(root, freeze_path, manifest_path, _prepare_factory(),
                     evaluate_fn, out_root=out_root, tmp_path=tmp_path)

    assert result["status"] == "completed", result
    assert result["completed_trials"] == len(document["schedule"]["rows"])
    # expected_perf_sha256 が各 cell の store binary sha と一致して伝搬する。
    contract = ec.lookup(V2_ENV_TAG)
    authorization = ec.authorize(V2_ENV_TAG)
    for call in evaluate_fn.calls:
        assert call["clocks_per_us"] == contract.clocks_per_us  # env 契約由来
        assert call["kwargs"]["numactl"] == list(contract.numactl)  # NUMACTL 撤去
        assert call["kwargs"]["expected_perf_sha256"] in {
            rec["binary_sha256"] for rec in binaries.values()
        }
    # execution receipt が campaign-start に記録され manifest と整合する。
    start = next(e for e in result["events"] if e["event"] == "campaign-start")
    receipt = start["execution_receipt"]
    assert execution_guard.receipt_matches_contract(
        receipt, env_tag=V2_ENV_TAG, contract_sha256=contract.contract_sha256,
        attestation_mode="none",
    )


@in_sealed_fixture_process
def test_v2_foreign_cell_admission_receipt_is_refused_before_store_read(tmp_path):
    root, freeze_path, _gen_sha, _binaries, _topology = _build_v2_repo(tmp_path)
    out_root = root.parent / "output"
    _manifest_path, document = _emitter_manifest(tmp_path, root, freeze_path)
    validated = s8b_ratified_freeze.launch_validate(
        s8b_ratified_freeze.load_ratified_freeze(root), root,
    )
    binaries = s8b_ratified_freeze._plain_json(validated.binaries_by_cell)
    pair = None
    values = list(binaries.values())
    for first in values:
        for second in values:
            if (first["cell_id"] != second["cell_id"]
                    and first["configuration_id"] == second["configuration_id"]
                    and first["binary_sha256"] == second["binary_sha256"]
                    and first["binding"] == second["binding"]):
                pair = (first, second)
                break
        if pair is not None:
            break
    assert pair is not None, "cell/holdout だけが異なる receipt swap fixture が必要"
    first, second = pair
    first["admission_receipt"], second["admission_receipt"] = (
        second["admission_receipt"], first["admission_receipt"],
    )
    swapped = dataclasses.replace(validated, binaries_by_cell=binaries)
    with mock.patch.object(
            driver, "_store_sha256",
            side_effect=AssertionError("receipt 全件 preflight 前に store を読んだ")):
        with pytest.raises(driver.OracleDriverError, match="admission-mismatch"):
            driver._prepare_v2_execution(
                validated=swapped, run_contract=document["run_contract"],
                schedule=document["schedule"]["rows"], out_root=out_root,
                repo_root=root,
            )


@in_sealed_fixture_process
def test_oracle_driver_accepts_conditional_sort_receipt_and_rejects_its_absence(
        tmp_path):
    root, freeze_path, _gen_sha, _binaries, _topology = _build_v2_repo(tmp_path)
    out_root = root.parent / "output"
    _manifest_path, document = _emitter_manifest(tmp_path, root, freeze_path)
    validated = s8b_ratified_freeze.launch_validate(
        s8b_ratified_freeze.load_ratified_freeze(root), root,
    )
    sort_cells = [
        cell_id for cell_id, record in validated.binaries_by_cell.items()
        if record["configuration_id"] == "sort_best"
    ]
    assert sort_cells
    driver._prepare_v2_execution(
        validated=validated, run_contract=document["run_contract"],
        schedule=document["schedule"]["rows"], out_root=out_root,
        repo_root=root,
    )

    missing = s8b_ratified_freeze._plain_json(validated.binaries_by_cell)
    missing[sort_cells[0]].pop("sort_swo_oracle")
    without_receipt = dataclasses.replace(validated, binaries_by_cell=missing)
    with pytest.raises(driver.OracleDriverError, match="admission-mismatch"):
        driver._prepare_v2_execution(
            validated=without_receipt, run_contract=document["run_contract"],
            schedule=document["schedule"]["rows"], out_root=out_root,
            repo_root=root,
        )


@in_sealed_fixture_process
def test_v2_store_bytes_are_checked_against_admission_subject_independently(tmp_path):
    """M5 の独立性は主張せず、実 store 改変が既存 record SHA gate で拒否される。"""
    root, freeze_path, _gen_sha, binaries, _topology = _build_v2_repo(tmp_path)
    out_root = root.parent / "output"
    _manifest_path, document = _emitter_manifest(tmp_path, root, freeze_path)
    validated = s8b_ratified_freeze.launch_validate(
        s8b_ratified_freeze.load_ratified_freeze(root), root,
    )
    victim = _unique_store_victim(binaries)
    (out_root / victim["store_path"]).write_bytes(b"real-store-corruption")
    with pytest.raises(driver.OracleDriverError, match="store-hash-mismatch"):
        driver._prepare_v2_execution(
            validated=validated, run_contract=document["run_contract"],
            schedule=document["schedule"]["rows"], out_root=out_root,
            repo_root=root,
        )


@in_sealed_fixture_process
def test_v2_completed_driver_adapter_campaign_is_accepted_by_report(tmp_path):
    """driver adapter の completed WAL は report で 5 個の bench 証拠として読める。"""
    root, freeze_path, _gen_sha, _binaries, _topology = _build_v2_repo(tmp_path)
    out_root = root.parent / "output"
    manifest_path, document = _emitter_manifest(tmp_path, root, freeze_path)
    result = _run_v2(
        root, freeze_path, manifest_path, _prepare_factory(),
        _fake_evaluate_factory(), out_root=out_root, tmp_path=tmp_path,
    )
    assert result["status"] == "completed", result

    reverified = s8b_ratified_freeze.reverify_published_freeze(
        s8b_ratified_freeze.load_ratified_freeze(root), root,
    )
    loaded_manifest = _verify_manifest(
        manifest_path,
        root=root,
        freeze_document=reverified.ratified.document,
        freeze_sha256=reverified.ratified.sha256,
    )
    _authorize_official_report_output(out_root)
    with mock.patch.object(
            report_module,
            "_campaign_verifier_epoch_from_lock_bytes",
            lambda lock_bytes: artifact_admission.CampaignVerifierEpoch(
                campaign_verifier_epoch=f"E1:{'e' * 64}",
                state="E1", reason_code="recorded-closure",
            ),
    ):
        observations = report_module.build_observations(
            manifest=loaded_manifest, output_root=out_root, repo_root=root,
            reverified_freeze=reverified,
        )
    assert len(observations["rows"]) == len(document["schedule"]["rows"])
    assert all(row["status"] == "completed" for row in observations["rows"])
    assert all(row["lifecycle_ok"] is True for row in observations["rows"])
    assert all(row["bench_values"] == [10.0, 11.0, 12.0, 13.0, 14.0]
               for row in observations["rows"])
    receipt = observations["store_reverification"]
    assert set(receipt) == {"state", "cells"}
    assert receipt["state"] == "verified"
    assert [cell["cell_id"] for cell in receipt["cells"]] == sorted(
        reverified.binaries_by_cell
    )
    assert all(
        set(cell) == {
            "cell_id", "store_path", "expected_sha256", "actual_sha256", "state",
        }
        and cell["state"] == "match"
        and cell["expected_sha256"] == cell["actual_sha256"]
        == reverified.binaries_by_cell[cell["cell_id"]]["binary_sha256"]
        for cell in receipt["cells"]
    )
    oracle = judge_module.judge_oracle(
        observations,
        schedule_projection=judge_module.project_verified_manifest_schedule(
            loaded_manifest,
        ),
        verified_manifest_sha256=loaded_manifest.sha256,
        approved_spec_sha256=loaded_manifest.document["spec_sha256"],
    )
    assert oracle["status"] == "determinate"


@pytest.mark.parametrize("change", ["replaced", "removed"])
@in_sealed_fixture_process
def test_v2_post_run_store_change_is_reported_and_refused(tmp_path, change):
    root, freeze_path, _gen_sha, binaries, _topology = _build_v2_repo(tmp_path)
    out_root = root.parent / "output"
    manifest_path, _document = _emitter_manifest(tmp_path, root, freeze_path)
    result = _run_v2(
        root, freeze_path, manifest_path, _prepare_factory(),
        _fake_evaluate_factory(), out_root=out_root, tmp_path=tmp_path,
    )
    assert result["status"] == "completed", result
    reverified = s8b_ratified_freeze.reverify_published_freeze(
        s8b_ratified_freeze.load_ratified_freeze(root), root,
    )
    loaded_manifest = _verify_manifest(
        manifest_path,
        root=root,
        freeze_document=reverified.ratified.document,
        freeze_sha256=reverified.ratified.sha256,
    )
    victim = _unique_store_victim(binaries)
    victim_path = out_root / victim["store_path"]
    if change == "replaced":
        victim_path.write_bytes(b"post-run replacement")
        expected_state = "mismatch"
        expected_reason = "store-reverification-mismatch"
    else:
        victim_path.unlink()
        expected_state = "missing"
        expected_reason = "store-reverification-store-missing"

    _authorize_official_report_output(out_root)
    with mock.patch.object(
            report_module._artifact_admission,
            "require_campaign_verifier_epoch",
            lambda campaign, *, purpose: artifact_admission.CampaignVerifierEpoch(
                campaign_verifier_epoch=f"E1:{'e' * 64}",
                state="E1", reason_code="recorded-closure",
            ),
    ):
        observations = report_module.build_observations(
            manifest=loaded_manifest, output_root=out_root, repo_root=root,
            reverified_freeze=reverified,
        )
    receipt = observations["store_reverification"]
    victim_cell = next(
        cell for cell in receipt["cells"]
        if cell["cell_id"] == victim["cell_id"]
    )
    assert receipt["state"] == "unverified"
    assert victim_cell["state"] == expected_state
    assert victim_cell["expected_sha256"] == victim["binary_sha256"]
    if change == "replaced":
        assert victim_cell["actual_sha256"] != victim_cell["expected_sha256"]
    else:
        assert victim_cell["actual_sha256"] is None
    oracle = judge_module.judge_oracle(
        observations,
        schedule_projection=judge_module.project_verified_manifest_schedule(
            loaded_manifest,
        ),
        verified_manifest_sha256=loaded_manifest.sha256,
        approved_spec_sha256=loaded_manifest.document["spec_sha256"],
    )
    assert oracle["status"] == "indeterminate"
    assert expected_reason in {reason["code"] for reason in oracle["reasons"]}


def test_oracle_admission_uses_verified_manifest_schedule_and_reps(tmp_path):
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, document = _write_manifest(
        tmp_path, freeze_path, prepare_fn,
    )
    verified_freeze = s8b_freeze_io.load_verified_freeze(freeze_path)
    verified_manifest = _verify_manifest(
        manifest_path,
        root=ROOT,
        freeze_document=verified_freeze.document,
        freeze_sha256=verified_freeze.sha256,
    )
    launch_validated = _fake_launch_validated(freeze_path)
    api = driver._holdout_admission

    with _isolated_oracle_admission_root(tmp_path) as admission_root:
        admitted = api.reserve_oracle_holdout_observations(
            repo_root=ROOT,
            verified_manifest=verified_manifest,
            launch_validated=launch_validated,
            block_id="b0",
        )
        expected_indexes = {
            row["schedule_index"] for row in document["schedule"]["rows"]
        }
        assert set(admitted) == expected_indexes
        first_index = min(expected_indexes)
        observation = api.consume_oracle_attempt_ticket(
            admitted[first_index], schedule_index=first_index,
        )
        assert observation.permitted_run_once_calls == document["run_contract"]["reps"]
        rows = api._read_ledger(admission_root / "ledger.jsonl")
        assert rows
        assert {row["observation_role"] for row in rows} == {
            api.OBSERVATION_ROLE_ORACLE_DRIVER,
        }


def test_oracle_repeated_reservation_is_admitted(tmp_path):
    freeze_path = _synthetic_freeze(tmp_path)
    first_campaign_id = "s8b-oracle-fixture-repeat-a"
    second_campaign_id = "s8b-oracle-fixture-repeat-b"
    first_manifest_path, _first_document = _write_manifest(
        tmp_path, freeze_path, _prepare_factory(),
        name="oracle-manifest-repeat-a.json", campaign_id=first_campaign_id,
    )
    second_manifest_path, _second_document = _write_manifest(
        tmp_path, freeze_path, _prepare_factory(),
        name="oracle-manifest-repeat-b.json", campaign_id=second_campaign_id,
    )
    verified_freeze = s8b_freeze_io.load_verified_freeze(freeze_path)
    first_verified_manifest = _verify_manifest(
        first_manifest_path, root=ROOT,
        freeze_document=verified_freeze.document,
        freeze_sha256=verified_freeze.sha256,
    )
    second_verified_manifest = _verify_manifest(
        second_manifest_path, root=ROOT,
        freeze_document=verified_freeze.document,
        freeze_sha256=verified_freeze.sha256,
    )
    launch_validated = _fake_launch_validated(freeze_path)
    api = driver._holdout_admission
    with _isolated_oracle_admission_root(tmp_path) as admission_root:
        first = api.reserve_oracle_holdout_observations(
            repo_root=ROOT, verified_manifest=first_verified_manifest,
            launch_validated=launch_validated, block_id="b0",
        )
        second = api.reserve_oracle_holdout_observations(
            repo_root=ROOT, verified_manifest=second_verified_manifest,
            launch_validated=launch_validated, block_id="b0",
        )
        assert set(first) == set(second)
        first_state = api._oracle_cell_state(first[min(first)])
        second_state = api._oracle_cell_state(second[min(second)])
        assert first_state.cell_effect_digest == second_state.cell_effect_digest
        assert first_state.measurement_generation_digest != (
            second_state.measurement_generation_digest
        )
        rows = api._read_ledger(admission_root / "ledger.jsonl")
        assert len(rows) == 24


def test_oracle_attempt_single_use_is_scoped_to_measurement_generation(tmp_path):
    freeze_path = _synthetic_freeze(tmp_path)
    first_campaign_id = "s8b-oracle-fixture-attempt-a"
    second_campaign_id = "s8b-oracle-fixture-attempt-b"
    first_manifest_path, document = _write_manifest(
        tmp_path, freeze_path, _prepare_factory(),
        name="oracle-manifest-attempt-a.json", campaign_id=first_campaign_id,
    )
    second_manifest_path, _second_document = _write_manifest(
        tmp_path, freeze_path, _prepare_factory(),
        name="oracle-manifest-attempt-b.json", campaign_id=second_campaign_id,
    )
    verified_freeze = s8b_freeze_io.load_verified_freeze(freeze_path)
    first_verified_manifest = _verify_manifest(
        first_manifest_path, root=ROOT,
        freeze_document=verified_freeze.document,
        freeze_sha256=verified_freeze.sha256,
    )
    second_verified_manifest = _verify_manifest(
        second_manifest_path, root=ROOT,
        freeze_document=verified_freeze.document,
        freeze_sha256=verified_freeze.sha256,
    )
    launch_validated = _fake_launch_validated(freeze_path)
    api = driver._holdout_admission
    with _isolated_oracle_admission_root(tmp_path) as admission_root:
        first = api.reserve_oracle_holdout_observations(
            repo_root=ROOT, verified_manifest=first_verified_manifest,
            launch_validated=launch_validated, block_id="b0",
        )
        second = api.reserve_oracle_holdout_observations(
            repo_root=ROOT, verified_manifest=second_verified_manifest,
            launch_validated=launch_validated, block_id="b0",
        )
        schedule_index = min(
            row["schedule_index"] for row in document["schedule"]["rows"]
        )
        first_token = api.consume_oracle_attempt_ticket(
            first[schedule_index], schedule_index=schedule_index,
        )
        second_token = api.consume_oracle_attempt_ticket(
            second[schedule_index], schedule_index=schedule_index,
        )
        assert first_token.attempt_id.removeprefix(
            f"{first_campaign_id}::"
        ) == second_token.attempt_id.removeprefix(
            f"{second_campaign_id}::"
        )
        with pytest.raises(api.HoldoutAdmissionError, match="already consumed"):
            api.consume_oracle_attempt_ticket(
                first[schedule_index], schedule_index=schedule_index,
            )
        assert len(list((
            admission_root / "measurement-generation-consumed"
        ).iterdir())) == 2


def test_official_driver_records_returncodes_through_real_producer_flow(tmp_path):
    """M-P5: driver opt-in から run_once までを通し、subprocess だけを fake にする。"""
    from orchestrator.calibrator import runner as calibrator_runner

    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, document = _write_manifest(
        tmp_path, freeze_path, prepare_fn,
    )
    prepare_fn.calls.clear()
    output_root = tmp_path / "producer-flow-out"
    subprocess_calls = []
    evaluate_flags = []
    admission_allowances = []
    evaluate_errors = []

    def fake_subprocess(cmd, **kwargs):
        subprocess_calls.append(list(cmd))
        perf_path = Path(cmd[cmd.index("-o") + 1])
        perf_path.write_text(
            "10,,LLC-load-misses\n"
            "100,,LLC-loads\n"
            "300,,instructions\n"
            "200,,cycles\n",
            encoding="utf-8",
        )
        return type("Completed", (), {
            "returncode": 0,
            "stdout": (
                "throughput[tps]:\t1000\n"
                "maxrss:\t100 kB\n"
                "abort_counts_:\t1\n"
                "commit_counts_:\t1000\n"
                "latency[ns]:\t10\n"
            ),
            "stderr": "",
        })()

    real_measure_point = calibrator_runner.measure_point

    def measure_with_fake_subprocess(*args, **kwargs):
        return real_measure_point(
            *args, **kwargs, require_complete_metrics=True,
            subprocess_runner=fake_subprocess,
        )

    def integrated_evaluate(genome, layout, env_tag, ccbench_commit, perf,
                            clocks_per_us, **kwargs):
        opted_in = kwargs.get("record_rep_returncodes") is True
        evaluate_flags.append(opted_in)
        admission_allowances.append(
            kwargs["holdout_observation_admission"].permitted_run_once_calls
        )
        variant = pipeline.variant_id(genome, kwargs["src_token"])

        def abort(reason, note, extra=None):
            wal.log(layout, variant, pipeline.STAGE_ABORT, env_tag,
                    {"reason": reason, **(extra or {})})
            return _with_condition_records(pipeline.EvalResult(
                genome=genome, variant=variant, certified=False, aborted=True,
                notes=[note],
            ))

        try:
            aborted, bench = pipeline._run_bench(
                "/fake/ycsb.exe", perf, clocks_per_us, kwargs["numactl"], False,
                layout, variant, env_tag, abort, log=lambda _message: None,
                build_attempt_id=f"oracle-test-{variant}",
                bench_max_rounds=kwargs["bench_max_rounds"],
                record_rep_returncodes=opted_in,
                holdout_observation_admission=(
                    kwargs["holdout_observation_admission"]
                ),
            )
        except Exception as exc:
            evaluate_errors.append(f"{type(exc).__name__}: {exc}")
            raise
        if aborted is not None:
            return aborted
        assert bench is not None
        return _with_condition_records(pipeline.EvalResult(
            genome=genome, variant=variant, certified=True, aborted=False,
            fitness_tps=bench.median_tps,
        ))

    with mock.patch.object(pipeline, "measure_point", measure_with_fake_subprocess), \
            mock.patch.object(pipeline, "competing_bench_pids", return_value=[]), \
            mock.patch.dict(os.environ, {
                "IZANAGI_BENCH_LOCK": str(tmp_path / "producer-flow.lock"),
            }):
        result = _run(
            tmp_path, freeze_path, manifest_path, prepare_fn,
            integrated_evaluate, output_root=output_root,
        )

    assert not evaluate_errors, evaluate_errors
    assert result["status"] == "completed", result
    assert evaluate_flags == [True] * len(document["schedule"]["rows"])
    assert admission_allowances == [
        document["run_contract"]["reps"]
    ] * len(document["schedule"]["rows"])
    assert len(subprocess_calls) == 5 * len(evaluate_flags)
    layout = campaign_layout(result["campaign_id"], output_root=str(output_root))
    bench_records = [record for record in wal.read_records(layout)
                     if record.stage == pipeline.STAGE_BENCH_DONE]
    assert len(bench_records) == len(evaluate_flags)
    assert all(record.payload["rep_returncodes"] == [0, 0, 0, 0, 0]
               for record in bench_records)


@pytest.mark.skipif(
    not ((ROOT / "external" / "ccbench" / ".git").exists()
         and all(shutil.which(tool) for tool in ("cmake", "gcc-13", "g++-13", "nm"))),
    reason="slow oracle real-build v2 control: initialized ccbench + pinned toolchain が必要",
)
def test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2(tmp_path):
    """oracle evaluate 境界で fake build を使わず trace/perf の実 build_v2 を通す。"""
    from test_campaign import _green_vr  # 局所 import: verifier fixture のみ共有

    freeze = _real_document()
    holdout_id = next(iter(freeze["holdouts"]))
    configuration_id = "stock_common"
    pin = subprocess.run(
        ["git", "-C", str(ROOT / "external" / "ccbench"), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
        env=_sanitized_git_env(),
    ).stdout.strip()
    contract = ec.lookup(V2_ENV_TAG)
    built = []
    real_build_v2 = pipeline.buildcache.build_v2

    def recording_build_v2(*args, **kwargs):
        result = real_build_v2(*args, **kwargs)
        built.append(result)
        return result

    build_context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    with driver._prepared_binding(
            freeze=freeze, holdout_id=holdout_id,
            configuration_id=configuration_id, ccbench_pin=pin,
            cxx="g++-13",
            prepare_fn=driver.prepare_cell) as (identity, prepared), \
            mock.patch.object(pipeline.buildcache, "build_v2", recording_build_v2), \
            mock.patch.object(
                pipeline, "_run_trace",
                return_value=pipeline._TraceRunResult(
                    trace_c_lines=1,
                    returncode=0,
                    abort_counts=1,
                    commit_count_witness=1,
                    batch_commit_count_witness=0,
                ),
            ), \
            mock.patch.object(
                pipeline, "verify_trace_dir",
                side_effect=lambda _p, *, expected_commits=None: _green_vr(),
            ), \
            driver._assert_v2_build_contract(contract):
        layout = campaign_layout(
            "oracle-real-v2-build-control", output_root=str(tmp_path / "wal"),
        ).ensure()
        result = pipeline.evaluate(
            prepared.genome, layout, contract.env_tag, pin,
            pipeline.PerfConfig(records=1000, threads=2),
            contract.clocks_per_us, do_bench=False,
            numactl=contract.numactl,
            authorization_contract=authorization,
            src_token=prepared.src_token, ccbench_dir=prepared.ccbench_dir,
            cache_root=str(tmp_path / "cache"), env_contract=contract,
            log=lambda _message: None, build_context=build_context,
            capability_resolver=lambda source: (
                s8b_materialization.reviewed_source_capability(
                    review_id=ReviewId.S8B_ORACLE,
                    source=source,
                    input_sha256=identity["entry_sha256"],
                )
            ),
        )

    assert result.certified and not result.aborted
    assert len(built) == 2 and {item.trace for item in built} == {False, True}
    assert all(Path(item.binary).is_file() for item in built)
    assert all(item.contract_sha256 == contract.contract_sha256 for item in built)
    assert all(Path(item.ccbench_root) == Path(prepared.ccbench_dir).absolute()
               for item in built)


@in_sealed_fixture_process
def test_v2_floor_disk_swap_after_launch_uses_same_validated_object(tmp_path):
    """launch 後の floor disk 差替えを無視し、旧 blob reader も呼ばない。"""
    root, freeze_path, _gen_sha, _binaries, topology = _build_v2_repo(tmp_path)
    out_root = root.parent / "output"
    manifest_path, _ = _emitter_manifest(tmp_path, root, freeze_path)
    result_path = root / topology["paths"]["result"]
    original_raw = result_path.read_bytes()
    real_launch = driver.s8b_ratified_freeze.launch_validate
    real_prepare = driver._prepare_v2_execution
    captured = {}

    def launch_then_swap(ratified, launch_root):
        validated = real_launch(ratified, launch_root)
        captured["launched"] = validated
        result_path.write_bytes(b'{"poisoned-after-launch":true}\n')
        return validated

    def record_prepare(**kwargs):
        captured["consumed"] = kwargs["validated"]
        return real_prepare(**kwargs)

    with mock.patch.object(
            driver.s8b_ratified_freeze, "launch_validate", launch_then_swap), \
            mock.patch.object(
                driver.s8b_ratified_freeze, "read_floor_source_blob",
                side_effect=AssertionError("legacy floor blob reader called")), \
            mock.patch.object(driver, "_prepare_v2_execution", record_prepare):
        result = _run_v2(
            root, freeze_path, manifest_path, _prepare_factory(),
            _fake_evaluate_factory(), out_root=out_root, tmp_path=tmp_path,
        )

    assert result["status"] == "completed", result
    assert captured["consumed"] is captured["launched"]
    assert captured["launched"].floor_artifact.raw_bytes == original_raw
    assert result_path.read_bytes() != original_raw


@in_sealed_fixture_process
def test_v2_freeze_bytes_not_active_generation_is_refused(tmp_path):
    """与えられた freeze bytes が active 世代と 1 byte でも違えば
    freeze-not-active-generation で拒否 (何も書かない)。"""
    root, freeze_path, _gen_sha, _bin, _topology = _build_v2_repo(tmp_path)
    out_root = root.parent / "output"
    manifest_path, _ = _emitter_manifest(tmp_path, root, freeze_path)
    # active 世代とは別 bytes の freeze を渡す (floor/budget は充填済み = v2 経路)。
    tampered = tmp_path / "tampered_freeze.json"
    doc = json.loads(freeze_path.read_text(encoding="utf-8"))
    doc["refreeze_note"] = str(doc.get("refreeze_note")) + " tampered"
    tampered.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")

    result = driver.run_block(
        manifest_path=manifest_path, block_id="b0", freeze_path=tampered,
        root=root, output_root=out_root, budget_path=tmp_path / "b.json",
        marker_root=tmp_path / "m", prepare_fn=_prepare_factory(),
        evaluate_fn=_fake_evaluate_factory(),
    )
    assert result["status"] == "refused"
    _assert_exact_refusals(result["refusals"], {
        "freeze-not-active-generation: 与えられた freeze bytes sha256 が"
        "承認束縛済み active 世代と不一致",
    })


@in_sealed_fixture_process
def test_v2_launch_validate_failure_is_refused(tmp_path):
    """launch_validate 失敗 (closure 外の未申告 hit) は v2-execution refusal に翻訳。"""
    root, freeze_path, _gen_sha, _bin, _topology = _build_v2_repo(tmp_path)
    out_root = root.parent / "output"
    manifest_path, _ = _emitter_manifest(tmp_path, root, freeze_path)
    # closure 外の untracked ファイルに rr80 params を仕込む → 未申告 hit で launch_validate 落ち。
    (root / "sneaky.txt").write_bytes(ratified_fixture._RR80_PARAMS)

    result = _run_v2(root, freeze_path, manifest_path, _prepare_factory(),
                     _fake_evaluate_factory(), out_root=out_root, tmp_path=tmp_path)
    assert result["status"] == "refused"
    _assert_exact_refusals(result["refusals"], {
        "v2-execution: launch-validate: [closure-hit-mismatch] "
        "[closure-hit-mismatch] rr80: 現 hit が closure 導出と不一致 "
        "(未申告=['sneaky.txt'] 消失=[])",
    })


@in_sealed_fixture_process
def test_v2_launch_validate_non_ratified_error_is_refused(tmp_path):
    """launch_validate が RatifiedFreezeError 以外 (内部 _hf の git/os 走査由来の
    FreezeError 等) を投げても、stack trace を漏らさず v2-execution refusal に翻訳する
    (run_block の refusal 契約を破らない・fail-closed で何も書かない)。"""
    from orchestrator.campaign import s8b_holdout_freeze  # noqa: PLC0415

    root, freeze_path, _gen_sha, _bin, _topology = _build_v2_repo(tmp_path)
    out_root = root.parent / "output"
    manifest_path, _ = _emitter_manifest(tmp_path, root, freeze_path)

    def _boom(*_a, **_k):
        # _hf.search_repository / enumerate_repository_files が git/os 失敗を包む型。
        raise s8b_holdout_freeze.FreezeError("git enumerate 失敗 (模擬)")

    with mock.patch.object(driver.s1_known_axes_freeze, "verify",
                           lambda *a, **k: None), \
            mock.patch.object(driver.s8b_ratified_freeze, "launch_validate", _boom):
        result = driver.run_block(
            manifest_path=manifest_path, block_id="b0", freeze_path=freeze_path,
            root=root, output_root=out_root,
            budget_path=tmp_path / "v2-budget.json",
            marker_root=tmp_path / "v2-markers",
            prepare_fn=_prepare_factory(), evaluate_fn=_fake_evaluate_factory(),
        )

    assert result["status"] == "refused", result
    _assert_exact_refusals(result["refusals"], {
        "v2-execution: launch-validate: FreezeError: git enumerate 失敗 (模擬)",
    })
    # fail-closed: run marker / WAL / budget を一切書いていない。
    assert not (tmp_path / "v2-budget.json").exists()
    assert not (tmp_path / "v2-markers").exists()


@in_sealed_fixture_process
def test_v2_store_missing_is_refused(tmp_path):
    """store 実体が欠落していれば refusal (再ビルド fallback は書かない)。"""
    root, freeze_path, _gen_sha, binaries, _topology = _build_v2_repo(tmp_path)
    out_root = root.parent / "output"
    manifest_path, _ = _emitter_manifest(tmp_path, root, freeze_path)
    baseline = s8b_ratified_freeze.launch_validate(
        s8b_ratified_freeze.load_ratified_freeze(root), root,
    )
    assert isinstance(baseline, s8b_ratified_freeze.LaunchValidatedFreeze)
    # 1 cell の store 実体を消す。
    victim = _unique_store_victim(binaries)
    (out_root / victim["store_path"]).unlink()
    before = _tree_file_snapshot(out_root)
    prepare_fn = _prepare_factory()
    evaluate_fn = _fake_evaluate_factory()

    result = _run_v2(root, freeze_path, manifest_path, prepare_fn,
                     evaluate_fn, out_root=out_root, tmp_path=tmp_path)
    assert result["status"] == "refused" and result["allowed"] is False
    cell = (victim["holdout_id"], victim["configuration_id"])
    _assert_exact_refusals(result["refusals"], {
        "v2-execution: [store-missing] floor 計測 binary の store 実体が無い: "
        f"{victim['store_path']} (cell={cell})",
    })
    assert _tree_file_snapshot(out_root) == before
    assert prepare_fn.calls == [] and evaluate_fn.calls == []
    assert not (tmp_path / "v2-budget.json").exists()
    assert not (tmp_path / "v2-markers").exists()


@in_sealed_fixture_process
def test_v2_store_hash_mismatch_is_refused(tmp_path):
    """store 実体の bytes が floor receipt の binary_sha256 と不一致なら refusal。"""
    root, freeze_path, _gen_sha, binaries, _topology = _build_v2_repo(tmp_path)
    out_root = root.parent / "output"
    manifest_path, _ = _emitter_manifest(tmp_path, root, freeze_path)
    baseline = s8b_ratified_freeze.launch_validate(
        s8b_ratified_freeze.load_ratified_freeze(root), root,
    )
    assert isinstance(baseline, s8b_ratified_freeze.LaunchValidatedFreeze)
    victim = _unique_store_victim(binaries)
    (out_root / victim["store_path"]).write_bytes(b"corrupted-binary-bytes")
    before = _tree_file_snapshot(out_root)
    prepare_fn = _prepare_factory()
    evaluate_fn = _fake_evaluate_factory()

    result = _run_v2(root, freeze_path, manifest_path, prepare_fn,
                     evaluate_fn, out_root=out_root, tmp_path=tmp_path)
    assert result["status"] == "refused" and result["allowed"] is False
    cell = (victim["holdout_id"], victim["configuration_id"])
    _assert_exact_refusals(result["refusals"], {
        "v2-execution: [store-hash-mismatch] store binary sha256 が floor receipt "
        f"と不一致: {victim['store_path']} (cell={cell})",
    })
    assert _tree_file_snapshot(out_root) == before
    assert prepare_fn.calls == [] and evaluate_fn.calls == []
    assert not (tmp_path / "v2-budget.json").exists()
    assert not (tmp_path / "v2-markers").exists()


@in_sealed_fixture_process
def test_v2_contract_sha256_mismatch_is_refused(tmp_path):
    """run_contract.contract_sha256 が env 契約 lookup 結果と不一致なら refusal。"""
    global _ACTIVE_APPROVED
    root, freeze_path, _gen_sha, _bin, _topology = _build_v2_repo(tmp_path)
    out_root = root.parent / "output"
    manifest_path, document = _emitter_manifest(tmp_path, root, freeze_path)
    original_approved = _APPROVED_BY_PATH[manifest_path.resolve()]
    # env_tag は維持し、manifest 内部だけ整合する別 contract_sha256 へ再封する。
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    original_sha256 = document["run_contract"]["contract_sha256"]
    document["run_contract"]["contract_sha256"] = (
        ("0" if original_sha256[0] != "0" else "1") + original_sha256[1:]
    )
    parameters = original_approved.document["schedule_parameters"]
    changed_approved = spec_fixture.make_reviewed_spec(
        root=root,
        n=parameters["n"],
        master_seed=parameters["master_seed"],
        block_sizes=parameters["block_sizes"],
        holdout_ids=parameters["holdout_ids"],
        configuration_ids=parameters["configuration_ids"],
        run_contract=document["run_contract"],
        campaign_ids=original_approved.document["campaign_ids"],
        binding_identity=original_approved.document["binding_identity"],
        allowed_excluded_reasons=(
            original_approved.document["allowed_excluded_reasons"]
        ),
        generator_versions=original_approved.document["generator_versions"],
    )
    _ACTIVE_APPROVED = changed_approved
    document["spec_sha256"] = changed_approved.sha256
    document["campaign_config_preimages"] = (
        manifest_module._campaign_config_preimages(
            schedule=document["schedule"],
            run_contract=document["run_contract"],
            campaign_ids=document["campaign_ids"],
        )
    )
    document["manifest_id"] = manifest_module._manifest_id(
        {k: v for k, v in document.items() if k != "manifest_id"})
    bad_manifest = tmp_path / "bad_manifest.json"
    bad_manifest.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    _APPROVED_BY_PATH[bad_manifest.resolve()] = changed_approved

    result = _run_v2(root, freeze_path, bad_manifest, _prepare_factory(),
                     _fake_evaluate_factory(), out_root=out_root, tmp_path=tmp_path)
    assert result["status"] == "refused" and result["allowed"] is False
    _assert_exact_refusals(result["refusals"], {
        "v2-execution: run_contract.contract_sha256 が env 契約 lookup 結果と不一致",
    })


@in_sealed_fixture_process
def test_v2_binary_mismatch_abort_maps_to_binary_mismatch_outcome(tmp_path):
    """pipeline の bench-binary-mismatch abort (TOCTOU 第二防壁) が driver の
    binary-mismatch terminal outcome に射影される。"""
    root, freeze_path, _gen_sha, _bin, _topology = _build_v2_repo(tmp_path)
    out_root = root.parent / "output"
    manifest_path, _ = _emitter_manifest(tmp_path, root, freeze_path)
    evaluate_fn = _fake_abort_evaluate_factory("bench-binary-mismatch")

    result = _run_v2(root, freeze_path, manifest_path, _prepare_factory(),
                     evaluate_fn, out_root=out_root, tmp_path=tmp_path)
    outcomes = [e["outcome"] for e in result["events"] if e["event"] == "trial-result"]
    assert outcomes and set(outcomes) == {"binary-mismatch"}, result


def _canonical_perf_receipt(status: str) -> dict:
    available = status == "available"
    return {
        "schema": driver._perf_preflight.SCHEMA,
        "status": status,
        "available": available,
        "probe_argv": list(driver._perf_preflight._BASE_PROBE_ARGV),
        "rc": 0 if available else None,
        "parsed_events": (
            list(driver._perf_preflight.PERF_EVENTS) if available else []
        ),
        "reason": (
            "available" if available else
            "probe-os-error" if status == "probe_error" else
            "perf-not-found"
        ),
        "stderr_sha256": "0" * 64,
        "candidates": [],
    }


@pytest.fixture(autouse=True)
def _pin_oracle_perf_available():
    """既存の perf-present fixture を実行 host の availability から隔離する。"""
    with mock.patch.object(
            driver._perf_preflight, "probe_perf_availability",
            return_value=_canonical_perf_receipt("available")):
        yield


def test_unavailable_preflight_creates_bound_measurement_manifest_and_passes_false_kwargs(
        tmp_path):
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, document = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory()
    unavailable = _canonical_perf_receipt("unavailable")

    with mock.patch.object(
            driver._perf_preflight, "probe_perf_availability",
            return_value=unavailable) as probe:
        result = _run(
            tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn,
        )

    probe.assert_called_once_with()
    assert result["status"] == "completed"
    assert evaluate_fn.calls
    for call in evaluate_fn.calls:
        assert call["kwargs"]["use_perf"] is False
        assert call["kwargs"]["perf_preflight_receipt"] == unavailable

    start = result["events"][0]
    assert set(start) == {
        "event", "manifest_sha256", "block_id", "campaign_id",
        "t080_freeze_migration_observation", "execution_receipt",
        "measurement_manifest",
    }
    record = start["measurement_manifest"]
    assert set(record) == {"path", "sha256"}
    assert record["path"] == "measurement-manifest.json"
    sidecar = (
        tmp_path / "out" / "campaigns" / result["campaign_id"] / record["path"]
    )
    assert record["sha256"] == hashlib.sha256(sidecar.read_bytes()).hexdigest()
    assert json.loads(sidecar.read_text(encoding="utf-8")) == {
        "schema_version": "8b-oracle-measurement-manifest/v1",
        "oracle_manifest_sha256": result["manifest_sha256"],
        "campaign_id": document["campaign_ids"]["b0"],
        "block_id": "b0",
        "perf_observation": driver._perf_preflight.build_perf_observation(
            unavailable, run_cmd=["ccbench"],
            leading_indicators={"ipc": None, "llc_miss_rate": None},
        ),
    }


def test_available_preflight_preserves_call_and_artifact_shape(tmp_path):
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    evaluate_fn = _fake_evaluate_factory()
    available = _canonical_perf_receipt("available")

    with mock.patch.object(
            driver._perf_preflight, "probe_perf_availability",
            return_value=available) as probe:
        result = _run(
            tmp_path, freeze_path, manifest_path, prepare_fn, evaluate_fn,
        )

    probe.assert_called_once_with()
    assert result["status"] == "completed"
    assert evaluate_fn.calls
    for call in evaluate_fn.calls:
        assert "use_perf" not in call["kwargs"]
        assert "perf_preflight_receipt" not in call["kwargs"]
    assert set(result["events"][0]) == {
        "event", "manifest_sha256", "block_id", "campaign_id",
        "t080_freeze_migration_observation", "execution_receipt",
    }
    assert not (
        tmp_path / "out" / "campaigns" / result["campaign_id"]
        / "measurement-manifest.json"
    ).exists()


def test_probe_error_precedes_claim_marker_wal_and_budget(tmp_path):
    freeze_path = _synthetic_freeze(tmp_path)
    prepare_fn = _prepare_factory()
    manifest_path, _ = _write_manifest(tmp_path, freeze_path, prepare_fn)
    prepare_fn.calls.clear()
    output_root = tmp_path / "probe-error-out"
    budget_path = tmp_path / "probe-error-budget.json"
    marker_root = tmp_path / "probe-error-markers"

    with mock.patch.object(
            driver._perf_preflight, "probe_perf_availability",
            return_value=_canonical_perf_receipt("probe_error")) as probe, \
            mock.patch.object(driver, "_acquire_g12_claim") as claim, \
            mock.patch.object(driver, "_ensure_campaign") as ensure, \
            mock.patch.object(driver, "_append_session") as append, \
            mock.patch.object(driver.s8b_budget, "create_ledger") as ledger:
        result = _run(
            tmp_path, freeze_path, manifest_path, prepare_fn,
            _fake_evaluate_factory(), output_root=output_root,
            budget_path=budget_path, marker_root=marker_root,
        )

    probe.assert_called_once_with()
    assert result["status"] == "refused"
    assert result["refusals"] and result["refusals"][0].startswith("perf-preflight: ")
    claim.assert_not_called()
    ensure.assert_not_called()
    append.assert_not_called()
    ledger.assert_not_called()
    assert not output_root.exists()
    assert not budget_path.exists()
    assert not marker_root.exists()


from orchestrator.tests.growth_test_holds import enforce_held_functions  # noqa: E402
enforce_held_functions(globals(), __file__, plain_runner="none")
