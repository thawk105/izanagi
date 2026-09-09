# -*- coding: utf-8 -*-
"""8b floor campaign driver — holdout freeze から floor 案を実測する env-neutral driver (v2)。

役割: holdout freeze v1 の 2 holdout × 6 構成 = 12 セルを floor protocol (明示入力・未凍結数値の
デフォルト内蔵禁止) が定める schedule どおり直列・単一テナントで計測し、``s8b_floor_stats``
(formula v2) で floor 案を算出して artifact (result.json/md) に書く。**freeze への floor 書込み・
phase 文書の編集はしない** (§8 手続き: 発効はユーザー承認事項)。本 driver は「案」を出すだけで、
何も発効させない。

**この floor は単一 campaign 内で観測された session dispersion に基づく記述的下限であり、
時間ドリフト・cold-boot・温度など別 run 間の変動は含まれない** (formula v2、§9 承認状態
2026-07-18)。式は本 driver の外 (``s8b_floor_stats``, formula v2) が正本。driver は計測して
SessionRecord を作り、cell_stats / holdout_floors / verify_floor_artifact を呼ぶだけで、floor の
式を自前で持たない。session 有効性・異常判定 (session 内 CV / セル間 CV) はすべて stats 側の
``assess_session`` / ``cell_cv_exceeds`` が正本で、driver は生値の抽出だけを行う (α-8/δ-6)。

系譜: 計測は calibration driver (``between_run_floor.py``) と同型で ``measure_point`` を直接呼ぶ
(``pipeline.evaluate`` は使わない — floor は correctness gate を通す本走ではなく noise の実測。
floor 経路に settle は使わない = ``measure_point(settle_first=False)`` 既定)。build 経路だけ oracle
と揃える (共有 ``s8b_materialization.prepared_binding`` + ``buildcache.build(trace=False)``) ので、
floor を測るバイナリと oracle 本走のバイナリが同一 identity になる。

env 契約 (F4): 計測環境の固有値 (clocks_per_us / numactl) は ``env_contract.lookup(env_tag)`` から
取る。driver は env 固有 literal を持たない (γ-16 の AST 検査が機械固定)。attestation が入る登録段
までの暫定 machine-pin として、契約の env_tag が実機観測から registry-derived に解決した machine
tag と一致することを要求する。

絶対規律の適用:
- 規律1 (観測者効果): 計測は trace-disabled build (``trace=False``)。
- 規律4 (単一テナント直列): session ごとの臨界区間 (probe → measure → post-probe → journal) で
  自前の strict probe (pgrep) を計測の前後に叩く。**rc=1 のみ「競合なし」**、rc=0 の競合列挙は
  当該 session を無効 (``competing_process``, retry 可) にし、実行不能・rc>1・parse 不能は
  **CampaignAbort** で倒す。**post-probe は measure が例外を投げた経路でも finally 相当で必ず
  実行する** (β-7)。
- 規律6 (信頼境界): freeze は素性の知れない外部内容。bytes-hash pin で束縛し、以後この単一
  parse 結果だけを使う (再読込禁止)。

fail-closed の原則: 縮退・欠測・不正入力・競合はすべて null / 拒否 / 判定不能へ倒す。protocol
config の数値はコードに既定値を持たず入力必須にする (F14 対策)。CLI に env・経路・数値の上書き面は
作らない。

official mode は CLI・public wrapper・private core の各入口で同じ明示承認を要求し、入口間の
迂回を許さない。さらに official core は ``build_fn`` 注入を副作用前に拒否し、admission-aware な
``buildcache.build_v2`` だけを materializer として使う。pilot、resume、または非既定 seam を
使った artifact は ``eligible_for_refreeze: false`` とし、fresh official の既定実引数だけを
true にできる。

既知限界: durable 側が保証するのは、測定前に create-only で共有 store へ置く事前 commitment、
生成後 artifact の書換と resume 後の basis 付替えの検出、台帳と artifact が食い違うときの
下流拒否である。同一 interpreter 内の code substitution は任意コード実行と同値であり、
この argument 境界はその攻撃への耐性を主張しない。artifact 単体の offline 検証も行わず、
gateway 発行の証明や暗号学的保証でもない。
"""
from __future__ import annotations

import argparse
import copy
import contextlib
import datetime as dt
import hashlib
import inspect
import json
import os
import re
import shlex
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import asdict, dataclass, field, replace
from typing import Callable, Mapping, Optional, Sequence
from pathlib import Path

_DEFAULT_SLEEP_FN = time.sleep
_DEFAULT_MONOTONIC_FN = time.monotonic

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
_REPO_ROOT = _ORCHESTRATOR.parent
ROOT = _REPO_ROOT

from ..calibrator.runner import (  # noqa: E402
    CompetingBenchProbeError,
    classify_competing_probe,
    measure_point, measure_point as _DEFAULT_MEASURE_POINT,
)
from ..calibrator import perf_preflight as _perf_preflight  # noqa: E402
from . import buildcache, patchharness, s8b_floor_attempt_launcher, s8b_floor_stats, source_digest  # noqa: E402
from . import s8b_expected_materialization as _expected_materialization  # noqa: E402
from . import sort_swo_dependency_material as _sort_swo_dependency_material  # noqa: E402
from . import silo_ladder_rung1 as _silo_ladder  # noqa: E402
from . import toolchain_binding  # noqa: E402
from .masstree_archive_projection import (  # noqa: E402
    PROJECTION_ID as _MASSTREE_ARCHIVE_PROJECTION_ID,
    MasstreeArchiveDigests,
    MasstreeArchiveProjectionError,
    masstree_archive_digests,
)
from .build_admission import (  # noqa: E402
    GeneratorId,
    ReviewId,
    build_run_context,
    derive_build_admission,
    resolve_current_build_admission_policy,
)
from . import s8b_binary_admission as _binary_admission  # noqa: E402
from . import t080_freeze_migration as _t080_migration  # noqa: E402
from . import freeze_verification_hold as _freeze_hold  # noqa: E402
from . import s8b_floor_contract as _floor_contract  # noqa: E402
from . import s8b_approved  # noqa: E402  (承認定数の単一源 C4-3/C4-4)
from . import env_contract as _env_contract  # noqa: E402
from . import env_attestation  # noqa: E402
from . import execution_guard  # noqa: E402  (共有 machine-pin + receipt)
from . import site_policy  # noqa: E402  (実機 site 観測)
from . import campaign_claim, floor_job_checkpoint, floor_submit_receipt, reservation  # noqa: E402
from .durable_root import DurableRootError, DurableRootPolicy, WriteCapability  # noqa: E402
from . import s8b_holdout_freeze as _holdout_freeze  # noqa: E402  (launch certificate の clean scan)
from . import s8b_freeze_io as _freeze_io  # noqa: E402
from . import s8b_holdout_admission as _holdout_admission  # noqa: E402
from . import s8b_selector_freeze as _selector_freeze  # noqa: E402
from . import s8b_prediction_runner as _prediction_runner  # noqa: E402
from .layout import (  # noqa: E402
    authorize_output_root,
    ensure_directory_with_capability,
    env_scope_dir,
    open_with_write_capability,
    repo_output_root,
    write_capability_for_directory,
)
from .s1_direct_comparison import prepare_cell  # noqa: E402
from .sort_swo_oracle import (  # noqa: E402
    INFRASTRUCTURE_REASON_CODE,
    OracleEnvironmentCandidate,
    OracleEnvironmentResolutionFailure,
    OracleInfrastructureFailure,
    OracleStatus,
    SortSwoOracleResult,
    SortSwoOracleUnavailable,
    private_attempt_record,
)
from .s8b_materialization import (  # noqa: E402
    MaterializationError,
    binding_entry,
    prepared_binding,
    reviewed_source_capability,
)
from .s8b_sort_swo_receipt import (  # noqa: E402
    SortSwoReceiptError,
    project_sort_swo_pass_attempt,
)
from .s8b_launch_cert import (  # noqa: E402
    LAUNCH_CERT_SCHEMA,
    LaunchCertError,
    validate_launch_certificate as _validate_launch_certificate,
    validate_launch_certificate_strict as _validate_launch_certificate_strict,
)

# 共有 leaf の版・承認 pin を既存名で re-export する。
PROTOCOL_SCHEMA = _floor_contract.PROTOCOL_SCHEMA
FREEZE_SCHEMA = _floor_contract.FREEZE_SCHEMA
SCHEDULE_ALGORITHM = _floor_contract.SCHEDULE_ALGORITHM
RESULT_SCHEMA = _floor_contract.RESULT_SCHEMA
MANIFEST_SCHEMA = _floor_contract.MANIFEST_SCHEMA
JOURNAL_SCHEMA = _floor_contract.JOURNAL_SCHEMA
_PROTOCOL_KEYS = _floor_contract._PROTOCOL_KEYS
_FREEZE_RECORD_KEYS = _floor_contract._FREEZE_RECORD_KEYS
_APPROVED_N_SESSIONS = _floor_contract._APPROVED_N_SESSIONS
_APPROVED_REPS = s8b_approved.APPROVED_REPS
_APPROVED_RETRY_SLOTS = _floor_contract._APPROVED_RETRY_SLOTS
_APPROVED_SESSION_CV_MAX = _floor_contract._APPROVED_SESSION_CV_MAX
_APPROVED_CELL_CV_MAX = _floor_contract._APPROVED_CELL_CV_MAX
_APPROVED_SCALE_ADEQUACY = _floor_contract._APPROVED_SCALE_ADEQUACY
_APPROVED_REASONS = list(_floor_contract._APPROVED_REASONS)
_AI_RESEAL_MUTABLE_FIELDS = _floor_contract._AI_RESEAL_MUTABLE_FIELDS
_AI_RESEAL_INHERITED_FIELDS = _floor_contract._AI_RESEAL_INHERITED_FIELDS

_FLOOR_PROTOCOL_REL = "output/s8b-freeze/floor_protocol.json"
_FLOOR_PROTOCOLS_REL = "output/s8b-freeze/floor-protocols"
_FLOOR_PROTOCOL_PAIR_RE = re.compile(r"[0-9a-f]{64}--[0-9a-f]{40}\.json")
_FLOOR_JOB_STAGING_ENV = "IZANAGI_FLOOR_JOB_STAGING"
_PRIVATE_DIAGNOSTIC_MAX_BYTES = 128 * 1024
_FLOOR_BUILD_EXCEPTION_MESSAGE_MAX_BYTES = 4096
_FLOOR_BUILD_EXCEPTION_TYPE_MAX_BYTES = 128
_FLOOR_PREFLIGHT_FAILURE_FILENAME = "sort-swo-oracle-preflight-failure.json"
_FLOOR_POSTFLIGHT_FAILURE_FILENAME = "sort-swo-oracle-postflight-failure.json"
_PRIVATE_SORT_SWO_EVIDENCE_SCHEMA = "s8b-sort-swo-private-evidence/v1"
_FLOOR_THIRD_PARTY_SOURCE_NAMES = ("masstree", "mimalloc", "googletest")
_FLOOR_SUBMISSION_PAYLOAD_LEAF = "masstree-payload"
_FLOOR_FETCHCONTENT_STAGING_LEAF = "izanagi-floor-fetchcontent"
_FLOOR_PREFLIGHT_MATERIALIZED_SHA256 = hashlib.sha256(
    b"floor-sort-swo-preflight:materialized-unavailable"
).hexdigest()
_FLOOR_PREFLIGHT_PROPOSAL_SHA256 = hashlib.sha256(
    b"floor-sort-swo-preflight:proposal-unavailable"
).hexdigest()
_FLOOR_TOOLCHAIN_PREFLIGHT_DETAIL_CODES = frozenset({
    "floor-toolchain-receipt-type-invalid",
    "floor-toolchain-receipt-missing",
    "floor-toolchain-receipt-state-invalid",
    "floor-toolchain-discovery-failed",
    "floor-toolchain-tool-missing",
    "floor-toolchain-tool-not-executable-regular-file",
    "floor-toolchain-version-launch-failed",
    "floor-toolchain-version-invalid",
    "floor-toolchain-receipt-mismatch",
    "floor-toolchain-manifest-invalid",
    "floor-toolchain-cxx-manifest-missing",
    "floor-toolchain-cxx-manifest-invalid",
})
_FLOOR_DEPENDENCY_PREFLIGHT_DETAIL_CODES = frozenset({
    "floor-dependency-policy-unavailable",
    "floor-dependency-policy-pin-nonunique",
    "floor-dependency-policy-pin-invalid",
    "floor-dependency-tmpdir-unconfigured",
    "floor-dependency-base-create-failed",
    "floor-dependency-base-path-invalid",
    "floor-dependency-base-unavailable",
    "floor-dependency-base-not-directory",
    "floor-dependency-base-owner-mismatch",
    "floor-dependency-base-boundary-unavailable",
    "floor-dependency-base-inside-repository",
    "floor-dependency-ccbench-checkout-failed",
    "floor-dependency-fetchcontent-base-failed",
    "floor-dependency-fetchcontent-configure-failed",
    "floor-dependency-fetchcontent-target-failed",
    "floor-dependency-source-missing",
    "floor-dependency-source-not-directory",
    "floor-dependency-source-stat-unavailable",
    "floor-dependency-head-probe-unavailable",
    "floor-dependency-head-nonunique",
    "floor-dependency-git-root-unavailable",
    "floor-dependency-git-root-mismatch",
    "floor-dependency-head-mismatch",
    "floor-dependency-config-missing",
    "floor-dependency-config-not-regular",
    "floor-dependency-config-hash-unavailable",
    "floor-dependency-config-expected-mismatch",
    "floor-dependency-archive-missing",
    "floor-dependency-archive-not-regular",
    "floor-dependency-archive-projection-invalid",
    "floor-dependency-archive-expected-mismatch",
    "floor-dependency-staged-source-path-invalid",
    "floor-dependency-staged-source-not-directory",
    "floor-dependency-staged-source-inside-repository",
    "floor-dependency-staged-git-root-unavailable",
    "floor-dependency-staged-git-root-mismatch",
    "floor-dependency-staged-head-probe-unavailable",
    "floor-dependency-staged-head-nonunique",
    "floor-dependency-staged-head-mismatch",
    "floor-dependency-staged-source-status-unavailable",
    "floor-dependency-staged-source-dirty",
    "floor-dependency-payload-policy-unavailable",
    "floor-dependency-payload-policy-schema-invalid",
    "floor-dependency-payload-policy-pin-mismatch",
    "floor-dependency-payload-policy-hash-invalid",
    "floor-dependency-canonical-tracked-list-unavailable",
    "floor-dependency-canonical-tracked-list-invalid",
    "floor-dependency-canonical-root-create-failed",
    "floor-dependency-canonical-copy-failed",
    "floor-dependency-canonical-source-drift",
    "floor-dependency-canonical-manifest-mismatch",
    "floor-dependency-canonical-verification-failed",
})
_FLOOR_DEPENDENCY_POSTFLIGHT_DETAIL_CODES = frozenset({
    "floor-dependency-postflight-build-failed",
    "floor-dependency-postflight-result-base-mismatch",
    "floor-dependency-postflight-configure-argv-invalid",
    "floor-dependency-postflight-source-override",
    "floor-dependency-postflight-base-define-count",
    "floor-dependency-postflight-effective-root-mismatch",
    "floor-dependency-postflight-source-unavailable",
    "floor-dependency-postflight-source-identity-drift",
    "floor-dependency-postflight-head-drift",
    "floor-dependency-postflight-tracked-source-drift",
    "floor-dependency-postflight-config-drift",
    "floor-dependency-postflight-archive-drift",
    "floor-dependency-postflight-archive-expected-mismatch",
    "floor-dependency-postflight-source-set",
    "floor-dependency-postflight-config-expected-mismatch",
    "floor-dependency-postflight-payload-policy-mismatch",
    "floor-dependency-postflight-toolchain-manifest-mismatch",
    "floor-dependency-postflight-toolchain-hash-mismatch",
    "floor-dependency-postflight-canonical-drift",
    "floor-dependency-postflight-canonical-source-drift",
})
_FLOOR_PREFLIGHT_CANDIDATE_OUTCOMES = frozenset({
    "not-configured",
    "not-found",
    "selected",
    "not-executable",
    "not-regular-file",
    "missing",
    "config-h-not-regular-file",
    "config-h-missing",
    "invalid-path",
    "execution-failed",
    "identity-mismatch",
})
_HOLDOUT_FREEZE_REL = "output/s8b-freeze/holdout_freeze.json"
_SELECTOR_PREDICTIONS_REL = "output/s8b-freeze/selector_predictions.json"
_SELECTOR_RUNS_REL = "output/s8b-freeze/selector-runs"
_SELECTOR_JOURNAL_REL = f"{_SELECTOR_RUNS_REL}/journal.jsonl"
_SELECTOR_PARSER_REL = "orchestrator/campaign/s8b_selector_output.py"
_PREFLIGHT_FIXED_FILES = frozenset({
    _FLOOR_PROTOCOL_REL,
    _HOLDOUT_FREEZE_REL,
    _SELECTOR_PREDICTIONS_REL,
    _SELECTOR_JOURNAL_REL,
})
_CHAIN_RECORD_PATTERNS = (
    re.compile(r"output/s8b-freeze/holdout_freeze\.v2\.g[1-9][0-9]*\.json"),
    re.compile(r"output/s8b-freeze/approvals/[0-9a-f]{64}\.json"),
    re.compile(r"output/s8b-freeze/revocations/[0-9a-f]{64}\.json"),
    re.compile(r"output/s8b-freeze/active/[0-9a-f]{64}\.json"),
    re.compile(r"output/s8b-freeze/active-cancellations/[0-9a-f]{64}\.json"),
    re.compile(r"output/s8b-freeze/floor-protocols/[0-9a-f]{64}--[0-9a-f]{40}\.json"),
)

# 新しい共有 API は leaf 実体を直接 re-export する。
canonical_protocol_sha256 = _floor_contract.canonical_protocol_sha256
validate_ai_reseal_inheritance = _floor_contract.validate_ai_reseal_inheritance
project_protocol_for_floor_artifact = _floor_contract.project_protocol_for_floor_artifact
derive_expected_cells = _floor_contract.derive_expected_cells
build_portable_run_cmd = _floor_contract.build_portable_run_cmd
_round_seed = _floor_contract._round_seed

# driver が観測から分類する excluded_reason コード (stats の閉じた表と一致)。
_REASON_COMPETING = "competing_process"          # preflight/post probe の競合
_REASON_LAUNCH = "launch_failure"                # プロセス起動失敗 (全 rep 実行不能)
_REASON_PARTIAL = "nonfinite_or_partial_output"

_PORTABLE_BUILT_KEYS = _binary_admission.PORTABLE_BUILT_KEYS
_PORTABLE_PLACEHOLDERS = (
    "${OUT_ROOT}", "${CCBENCH_ROOT}", "${FETCHCONTENT_BASE_DIR}",
)

# W2a walltime envelope の凍結定数。build cap/finalize reserve は Pegasus
# certification job と同じ 15 分/10 分。verify cap は session ごとの binary hash +
# strict pre/post probe を 120 秒に閉じ込める上限で、bench extime×reps とは分離する。
_FLOOR_BUILD_CAP_PER_CELL_S = 900
_FLOOR_DEPENDENCY_CONFIGURE_CAP_S = 900
_FLOOR_DEPENDENCY_TARGET_CAP_S = 900
_FLOOR_VERIFY_CAP_PER_ATTEMPT_S = 120
_FLOOR_FINALIZE_RESERVE_S = 600
_FLOOR_RESERVATION_FORMULA = (
    "shared_dependency_prebuild_s + cell_count * (build_cap_per_cell_s + "
    "(scheduled_attempts_per_cell + retry_slots_per_cell) * "
    "(bench_extime_s * reps + verify_cap_per_attempt_s))"
)


class FloorCampaignError(RuntimeError):
    """floor campaign の入力・identity・実行契約を検証できない場合の fail-closed 拒否。"""

    def __init__(
        self,
        message: str,
        *,
        claim_error: campaign_claim.ClaimError | None = None,
    ) -> None:
        super().__init__(message)
        self.claim_error = claim_error
        self.claim_conflict = claim_error.conflict if claim_error is not None else None


def _machine_env_tag_for_site(site: str) -> str:
    """実機 site 観測から machine-pin の registry-derived tag を解決する。"""
    if site == site_policy.PEGASUS_COMPUTE:
        try:
            return _env_contract.lookup_required_attestation_contract().env_tag
        except _env_contract.EnvContractError as exc:
            raise FloorCampaignError(
                "machine-pin: required attestation contract を一意に解決できない"
            ) from exc
    if site == site_policy.OTHER:
        try:
            contracts = tuple(_env_contract.REGISTRY.values())
            candidate_contracts = tuple(
                contract
                for contract in contracts
                if contract.attestation_mode == "none"
            )
            candidate_tags = {contract.env_tag for contract in candidate_contracts}
            registry_tags = tuple(contract.env_tag for contract in contracts)
            registry_tag_set = set(registry_tags)
        except (_env_contract.EnvContractError, AttributeError, TypeError) as exc:
            raise FloorCampaignError(
                "machine-pin: none attestation contract を一意に解決できない"
            ) from exc
        if (len(candidate_contracts) != 1
                or len(candidate_tags) != 1
                or len(registry_tags) != len(registry_tag_set)):
            raise FloorCampaignError(
                "machine-pin: none attestation contract を一意に解決できない"
            )
        return candidate_contracts[0].env_tag
    raise FloorCampaignError(f"machine-pin: 未対応 site {site!r}")


class CampaignAbort(FloorCampaignError):
    """臨界区間 (probe 実行不能・rc>1・parse 不能等) の破れで campaign を安全側に中断する (規律4)。"""


def _policy_perf_candidates(repo_root: Path) -> tuple[str, ...]:
    """Pegasus policy の perf 候補を evidence 用にだけ読む。"""
    path = Path(repo_root) / "tools/pegasus/policy.json"
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FloorCampaignError(f"perf candidate policy を読めない: {path}: {exc}") from exc
    candidates = policy.get("perf_candidates") if isinstance(policy, Mapping) else None
    if (not isinstance(candidates, list)
            or not all(isinstance(candidate, str) and candidate for candidate in candidates)
            or len(set(candidates)) != len(candidates)):
        raise FloorCampaignError("policy.perf_candidates が一意な str list でない")
    return tuple(candidates)


def _normalize_perf_preflight(receipt) -> dict:
    try:
        normalized = _perf_preflight.validate_perf_preflight_receipt(receipt)
        _perf_preflight.use_perf_from_receipt(normalized)
    except _perf_preflight.PerfPreflightError as exc:
        raise FloorCampaignError(str(exc)) from exc
    return normalized


def _project_probed_perf_preflight(mode: str, receipt) -> dict | None:
    """内部 probe receipt を legacy-compatible な artifact 表現へ射影する。"""

    normalized = _normalize_perf_preflight(receipt)
    try:
        use_perf = _perf_preflight.use_perf_from_receipt(normalized)
    except _perf_preflight.PerfPreflightError as exc:  # pragma: no cover - normalized
        raise FloorCampaignError(str(exc)) from exc
    if mode != "pilot" and use_perf:
        return None
    return normalized


def _assert_perf_mode(mode: str, receipt) -> bool:
    try:
        use_perf = _perf_preflight.use_perf_from_receipt(receipt)
    except _perf_preflight.PerfPreflightError as exc:
        raise FloorCampaignError(str(exc)) from exc
    if mode != "pilot" and receipt is not None and use_perf:
        raise CampaignAbort("official mode では available perf_preflight receipt を拒否する")
    return use_perf


def _validate_mode(mode) -> str:
    """core 呼出しの mode を閉じた集合で検証し、path segment への注入を防ぐ。"""
    if type(mode) is not str or mode not in {"pilot", "official"}:
        raise FloorCampaignError("mode は exact {'pilot','official'} のいずれかでなければならない")
    return "pilot" if mode == "pilot" else "official"


def _assert_official_permitted(
    mode: str,
    confirm_official_floor_run: bool,
) -> None:
    """official は exact bool の明示承認がある場合だけ許可する。"""
    if mode == "official" and confirm_official_floor_run is not True:
        raise FloorCampaignError(
            "official mode は明示承認がないため core で拒否する "
            "(--confirm-official-floor-run が必要)"
        )


# --------------------------------------------------------------------------- #
# canonical JSON / hash                                                        #
# --------------------------------------------------------------------------- #

def _canonical_bytes(value) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise FloorCampaignError(f"canonical JSON に変換できない: {exc}") from exc


def _canonical_sha256(value) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _full_sha256(path: Path) -> str:
    """バイナリ内容の full sha256 (provenance snapshot; truncate しない)。"""
    try:
        return buildcache.full_sha256(path)
    except buildcache.BinaryDigestError as exc:
        raise FloorCampaignError(str(exc)) from exc


# --------------------------------------------------------------------------- #
# protocol (strict 明示入力・デフォルト内蔵禁止)                                #
# --------------------------------------------------------------------------- #

def _reject_json_constant(token: str):
    raise FloorCampaignError(f"protocol JSON に非数値定数が含まれる: {token}")


def _no_duplicate_pairs(pairs):
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise FloorCampaignError(f"protocol JSON に duplicate key: {key}")
        result[key] = value
    return result


def load_protocol(path) -> dict:
    """protocol JSON を strict parse する (duplicate key・非数値定数を拒否)。"""
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise FloorCampaignError(f"protocol を読めない: {path}: {exc}") from exc
    try:
        document = json.loads(
            text, object_pairs_hook=_no_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
    except json.JSONDecodeError as exc:
        raise FloorCampaignError(f"protocol を strict parse できない: {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise FloorCampaignError(f"protocol top-level が object でない: {path}")
    return document


def _pos_int(value, *, field: str) -> int:
    try:
        return _floor_contract._pos_int(value, field=field)
    except _floor_contract.FloorContractError as exc:
        raise FloorCampaignError(str(exc)) from exc


def _non_neg_int(value, *, field: str) -> int:
    try:
        return _floor_contract._non_neg_int(value, field=field)
    except _floor_contract.FloorContractError as exc:
        raise FloorCampaignError(str(exc)) from exc


def _non_empty_str(value, *, field: str) -> str:
    try:
        return _floor_contract._non_empty_str(value, field=field)
    except _floor_contract.FloorContractError as exc:
        raise FloorCampaignError(str(exc)) from exc


def _pinned(value, expected, *, field: str):
    """承認凍結値との完全一致を要求する (別実験への変質を開始前に拒否, β-1)。"""
    try:
        return _floor_contract._pinned(value, expected, field=field)
    except _floor_contract.FloorContractError as exc:
        raise FloorCampaignError(str(exc)) from exc


def _historical_protocol_contract(
        recorded_hash: str, env_tag: str,
) -> _env_contract.ExecutionEnvironmentContract:
    """記録 hash から protocol 世代の contract を一意に解決する。"""
    try:
        entry = _env_contract.resolve_by_contract_sha256(
            recorded_hash, expected_env_tag=env_tag,
        )
    except _env_contract.EnvContractError as exc:
        raise _floor_contract.FloorContractError(
            f"protocol の歴史 env 契約を解決できない: {exc}"
        ) from exc
    if type(entry) is not _env_contract.GenerationEntry:
        raise _floor_contract.FloorContractError(
            "protocol の歴史 env 契約 resolver が exact GenerationEntry を返さなかった"
        )
    return entry.contract


def _current_protocol_contract(
        recorded_hash: str, env_tag: str,
) -> _env_contract.ExecutionEnvironmentContract:
    """protocol の env_tag に対する current contract を解決する。"""
    del recorded_hash  # hash 一致は共通 core が exact contract object に対して検査する。
    try:
        return _env_contract.lookup(env_tag)
    except _env_contract.EnvContractError as exc:
        raise _floor_contract.FloorContractError(
            f"protocol.env_tag が current env 契約に未登録: {exc}"
        ) from exc


def _validate_protocol_with_resolver(
        document: Mapping, *,
        resolver: Callable[
            [str, str], _env_contract.ExecutionEnvironmentContract,
        ],
) -> tuple[dict, _env_contract.ExecutionEnvironmentContract]:
    """共有 leaf を resolver 1 回で検証し、同一 contract object も返す。"""
    resolved_contract = None

    def contract_sha256_lookup(env_tag: str) -> str:
        nonlocal resolved_contract
        recorded_hash = document["contract_sha256"]
        if type(recorded_hash) is not str:
            raise _floor_contract.FloorContractError(
                "protocol.contract_sha256 が exact str でない"
            )
        contract = resolver(recorded_hash, env_tag)
        if type(contract) is not _env_contract.ExecutionEnvironmentContract:
            raise _floor_contract.FloorContractError(
                "protocol env 契約 resolver が exact ExecutionEnvironmentContract "
                "を返さなかった"
            )
        if contract.env_tag != env_tag:
            raise _floor_contract.FloorContractError(
                "protocol.env_tag と resolver が返した env 契約が不一致"
            )
        if contract.contract_sha256 != recorded_hash:
            raise _floor_contract.FloorContractError(
                "protocol.contract_sha256 と resolver が返した env 契約が不一致"
            )
        resolved_contract = contract
        return contract.contract_sha256

    try:
        normalized = _floor_contract.validate_protocol(
            document, contract_sha256_lookup=contract_sha256_lookup,
        )
    except _floor_contract.FloorContractError as exc:
        raise FloorCampaignError(str(exc)) from exc
    if resolved_contract is None:
        raise FloorCampaignError("protocol env 契約 resolver が呼ばれなかった")
    return normalized, resolved_contract


def _validate_protocol_against_current(
        document: Mapping,
) -> tuple[dict, _env_contract.ExecutionEnvironmentContract]:
    """producer と live admission を current contract へ束縛する。"""
    return _validate_protocol_with_resolver(
        document, resolver=_current_protocol_contract,
    )


def validate_protocol_against_current(
        document: Mapping,
) -> tuple[dict, _env_contract.ExecutionEnvironmentContract]:
    """Public read-only live-admission leaf for the wrapper preflight."""
    return _validate_protocol_against_current(document)


def validate_protocol(document: Mapping) -> dict:
    """凍結済み protocol を記録時の歴史 contract で read-only 検証する。"""
    normalized, _contract = _validate_protocol_with_resolver(
        document, resolver=_historical_protocol_contract,
    )
    return normalized


# --------------------------------------------------------------------------- #
# protocol builder + writer (承認定数から機械組立て、C4-4/C4-7)                 #
#                                                                              #
# 凍結手順 (ユーザー): (1) master_seed / env_tag を確定 → (2) build_protocol_document #
# で組立て (承認 pin は s8b_approved 単一源から焼く) → (3) write_protocol_document で   #
# 明示出力先へ書き出し → (4) ユーザーが commit する (AI-Agent: none)。実凍結 (実 repo の #
# output/s8b-freeze/ への書込み) は AI が行わずユーザー手順で行う。                     #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class BuiltProtocol:
    """組立て済み protocol (validate_protocol 通過済み) と canonical bytes/sha256。"""

    document: dict
    canonical_bytes: bytes
    sha256: str


@dataclass(frozen=True)
class IndexedFloorProtocol:
    """strict scan 済み floor protocol の path・組・bytes identity。"""

    path: str
    document: dict
    raw_bytes: bytes
    sha256: str
    commit_oid: str = field(default="", compare=False)

    @property
    def contract_sha256(self) -> str:
        return self.document["contract_sha256"]

    @property
    def ccbench_pin(self) -> str:
        return self.document["ccbench_pin"]

    @property
    def protocol_sha256(self) -> str:
        return self.sha256

    @property
    def canonical_bytes(self) -> bytes:
        return self.raw_bytes


def _strict_parse_protocol_bytes(raw: bytes, *, source: str) -> dict:
    """取得源を固定済みの raw bytes を duplicate-key 拒否で strict parse する。"""
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise FloorCampaignError(f"protocol を UTF-8 decode できない: {source}: {exc}") from exc
    try:
        document = json.loads(
            text,
            object_pairs_hook=_no_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
    except json.JSONDecodeError as exc:
        raise FloorCampaignError(
            f"protocol を strict parse できない: {source}: {exc}"
        ) from exc
    if not isinstance(document, dict):
        raise FloorCampaignError(f"protocol top-level が object でない: {source}")
    return document


_FLOOR_GIT_AUTHORITY_ENV = frozenset({
    "GIT_REPLACE_REF_BASE",
    "GIT_CONFIG",
    "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_COUNT",
    "GIT_NAMESPACE",
    "GIT_GRAFT_FILE",
    "GIT_SHALLOW_FILE",
})
_FLOOR_GIT_CONFIG_ENTRY_RE = re.compile(r"GIT_CONFIG_(?:KEY|VALUE)_\d+")


def _sanitized_floor_git_env() -> dict[str, str]:
    """floor issuer の Git object/config authority を ambient 環境から切る。"""
    env = source_digest._sanitized_git_env()
    for name in _FLOOR_GIT_AUTHORITY_ENV:
        env.pop(name, None)
    for name in tuple(env):
        if _FLOOR_GIT_CONFIG_ENTRY_RE.fullmatch(name):
            env.pop(name, None)
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    return env


def _floor_git_read_command(*args: str) -> list[str]:
    """replacement object を argv と環境の二層で無効化した Git read argv。"""
    return ["git", "--no-replace-objects", *args]


def _head_commit_oid(root: Path) -> str:
    """ambient Git authority を除去して HEAD commit を一度だけ解決する。"""
    try:
        raw = subprocess.run(
            _floor_git_read_command("rev-parse", "--verify", "HEAD^{commit}"),
            cwd=str(root), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=_sanitized_floor_git_env(),
        ).stdout
        commit_oid = raw.decode("ascii", "strict").strip()
        if re.fullmatch(r"[0-9a-f]{40}", commit_oid) is None:
            raise FloorCampaignError(
                f"repository HEAD commit OID が 40 桁小文字 hex でない: {commit_oid!r}"
            )
        return commit_oid
    except FloorCampaignError:
        raise
    except (OSError, UnicodeError, subprocess.CalledProcessError) as exc:
        raise FloorCampaignError(f"repository HEAD commit を解決できない: {exc}") from exc


def _head_blob_100644(root: Path, rel: str, commit_oid: str) -> bytes:
    """固定 commit の exact 100644 blob OID を検査して bytes を読む。"""
    try:
        listed = subprocess.run(
            _floor_git_read_command("ls-tree", "-z", commit_oid, "--", rel),
            cwd=str(root), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=_sanitized_floor_git_env(),
        ).stdout
        entries = [entry for entry in listed.split(b"\0") if entry]
        if len(entries) != 1:
            raise FloorCampaignError(
                f"AI reseal anchor が HEAD 固定 commit に exact 1 blob ない: {rel}"
            )
        meta, separator, actual = entries[0].decode("utf-8", "strict").partition("\t")
        mode, kind, blob_oid = meta.split(" ")
        if not separator or actual != rel or mode != "100644" or kind != "blob":
            raise FloorCampaignError(
                f"AI reseal anchor が HEAD 固定 commit の 100644 blob でない: {rel}"
            )
        if re.fullmatch(r"[0-9a-f]{40}", blob_oid) is None:
            raise FloorCampaignError(
                f"AI reseal anchor の blob OID が 40 桁小文字 hex でない: {rel}"
            )
        return subprocess.run(
            _floor_git_read_command("cat-file", "blob", blob_oid),
            cwd=str(root), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=_sanitized_floor_git_env(),
        ).stdout
    except FloorCampaignError:
        raise
    except (OSError, UnicodeError, ValueError, subprocess.CalledProcessError) as exc:
        raise FloorCampaignError(
            f"AI reseal anchor の HEAD blob を検証できない: {rel}: {exc}"
        ) from exc


def _validate_floor_protocol_pair(contract_sha256: object, ccbench_pin: object) -> tuple[str, str]:
    if (not isinstance(contract_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", contract_sha256) is None):
        raise FloorCampaignError(
            f"floor protocol contract_sha256 が 64 桁小文字 hex でない: {contract_sha256!r}"
        )
    if (not isinstance(ccbench_pin, str)
            or re.fullmatch(r"[0-9a-f]{40}", ccbench_pin) is None):
        raise FloorCampaignError(
            f"floor protocol ccbench_pin が 40 桁小文字 hex でない: {ccbench_pin!r}"
        )
    return contract_sha256, ccbench_pin


def _derived_reseal_protocol_relpath(contract_sha256: object, ccbench_pin: object) -> str:
    """呼び手指定面を持たず、組から sanctioned path を一意に導出する。"""
    contract, pin = _validate_floor_protocol_pair(contract_sha256, ccbench_pin)
    return f"{_FLOOR_PROTOCOLS_REL}/{contract}--{pin}.json"


def _index_protocol_record(
        index: dict[tuple[str, str], IndexedFloorProtocol], *, path: str,
        document: dict, raw: bytes, commit_oid: str) -> None:
    pair = _validate_floor_protocol_pair(
        document["contract_sha256"], document["ccbench_pin"],
    )
    if pair in index:
        raise FloorCampaignError(
            "floor protocol index に同一組が複数ある: "
            f"pair={pair!r} paths={[index[pair].path, path]}"
        )
    index[pair] = IndexedFloorProtocol(
        path=path,
        document=document,
        raw_bytes=raw,
        sha256=hashlib.sha256(raw).hexdigest(),
        commit_oid=commit_oid,
    )


def _assert_floor_protocol_ancestors(root: Path) -> None:
    """sanctioned namespace までの祖先が実 directory であることを検査する。"""
    for rel in ("output", "output/s8b-freeze"):
        directory = root / rel
        if directory.is_symlink():
            raise FloorCampaignError(f"floor protocol index 親が symlink: {rel}")
        if directory.exists() and not directory.is_dir():
            raise FloorCampaignError(
                f"floor protocol index 親が実 directory でない: {rel}"
            )
    protocols_dir = root / _FLOOR_PROTOCOLS_REL
    if protocols_dir.is_symlink():
        raise FloorCampaignError(
            f"floor protocol namespace が symlink: {protocols_dir}"
        )
    if protocols_dir.exists() and not protocols_dir.is_dir():
        raise FloorCampaignError(
            f"floor protocol namespace が directory でない: {protocols_dir}"
        )


def _floor_protocol_paths_at_commit(root: Path, commit_oid: str) -> set[str]:
    """固定 commit の versioned namespace path 集合を衛生化 Git で読む。"""
    try:
        raw = subprocess.run(
            _floor_git_read_command(
                "ls-tree", "-r", "-z", "--name-only", commit_oid,
                "--", _FLOOR_PROTOCOLS_REL,
            ),
            cwd=str(root), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=_sanitized_floor_git_env(),
        ).stdout
        paths = [
            entry.decode("utf-8", "strict")
            for entry in raw.split(b"\0") if entry
        ]
    except (OSError, UnicodeError, subprocess.CalledProcessError) as exc:
        raise FloorCampaignError(
            f"floor protocol namespace の HEAD path 集合を検証できない: {exc}"
        ) from exc
    if len(paths) != len(set(paths)):
        raise FloorCampaignError("floor protocol namespace の HEAD path 集合に重複がある")
    prefix = f"{_FLOOR_PROTOCOLS_REL}/"
    if any(not path.startswith(prefix) for path in paths):
        raise FloorCampaignError(
            "floor protocol namespace の HEAD path が sanctioned prefix 外"
        )
    return set(paths)


def _scan_floor_protocol_index_at_commit(
        *, root: Path, commit_oid: str,
) -> dict[tuple[str, str], IndexedFloorProtocol]:
    """固定 commit の anchor と sanctioned namespace を strict index 化する。"""
    root = Path(root)
    _assert_floor_protocol_ancestors(root)
    legacy_path = root / _FLOOR_PROTOCOL_REL
    try:
        legacy_stat = legacy_path.lstat()
    except OSError as exc:
        raise FloorCampaignError(
            f"floor protocol legacy anchor が無いか検査できない: {legacy_path}: {exc}"
        ) from exc
    if stat.S_ISLNK(legacy_stat.st_mode) or not stat.S_ISREG(legacy_stat.st_mode):
        raise FloorCampaignError(
            f"floor protocol legacy anchor が regular non-symlink file でない: {legacy_path}"
        )

    # working tree の legacy も strict scan するが、lineage authority には使わない。
    try:
        working_legacy_raw = legacy_path.read_bytes()
    except OSError as exc:
        raise FloorCampaignError(f"legacy floor protocol を読めない: {legacy_path}: {exc}") from exc
    working_legacy = _strict_parse_protocol_bytes(
        working_legacy_raw, source=str(legacy_path),
    )
    validate_protocol(working_legacy)

    anchor_raw = _head_blob_100644(root, _FLOOR_PROTOCOL_REL, commit_oid)
    anchor_source = f"{commit_oid}:{_FLOOR_PROTOCOL_REL}"
    anchor_document_raw = _strict_parse_protocol_bytes(anchor_raw, source=anchor_source)
    anchor_document = validate_protocol(anchor_document_raw)
    index: dict[tuple[str, str], IndexedFloorProtocol] = {}
    _index_protocol_record(
        index, path=_FLOOR_PROTOCOL_REL, document=anchor_document, raw=anchor_raw,
        commit_oid=commit_oid,
    )

    protocols_dir = root / _FLOOR_PROTOCOLS_REL
    committed_paths = _floor_protocol_paths_at_commit(root, commit_oid)
    if not protocols_dir.exists():
        if committed_paths:
            raise FloorCampaignError(
                "floor protocol namespace の committed entry が working tree に無い: "
                f"paths={sorted(committed_paths)}"
            )
        return index
    try:
        entries = sorted(protocols_dir.iterdir(), key=lambda path: path.name)
    except OSError as exc:
        raise FloorCampaignError(
            f"floor protocol namespace を列挙できない: {protocols_dir}: {exc}"
        ) from exc
    working_paths: set[str] = set()
    for path in entries:
        rel = path.relative_to(root).as_posix()
        working_paths.add(rel)
        if path.is_symlink():
            raise FloorCampaignError(f"floor protocol namespace に symlink がある: {rel}")
        try:
            entry_stat = path.lstat()
        except OSError as exc:
            raise FloorCampaignError(f"floor protocol entry を検査できない: {rel}: {exc}") from exc
        if not stat.S_ISREG(entry_stat.st_mode):
            raise FloorCampaignError(
                f"floor protocol namespace に非通常 file がある: {rel}"
            )
        if _FLOOR_PROTOCOL_PAIR_RE.fullmatch(path.name) is None:
            raise FloorCampaignError(f"floor protocol namespace に予期しない名前がある: {rel}")
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise FloorCampaignError(f"floor protocol entry を読めない: {rel}: {exc}") from exc
        committed_raw = _head_blob_100644(root, rel, commit_oid)
        if raw != committed_raw:
            raise FloorCampaignError(
                "floor protocol entry の working tree bytes が "
                f"HEAD 固定 commit の 100644 blob と不一致: {rel}"
            )
        document_raw = _strict_parse_protocol_bytes(raw, source=rel)
        document = validate_protocol(document_raw)
        expected_rel = _derived_reseal_protocol_relpath(
            document["contract_sha256"], document["ccbench_pin"],
        )
        if rel != expected_rel:
            raise FloorCampaignError(
                f"floor protocol path が document の組からの導出値と不一致: {rel} != {expected_rel}"
            )
        try:
            validate_ai_reseal_inheritance(anchor_document_raw, document_raw)
        except _floor_contract.FloorContractError as exc:
            raise FloorCampaignError(str(exc)) from exc
        expected_document = copy.deepcopy(anchor_document)
        expected_document["contract_sha256"] = document["contract_sha256"]
        expected_document["ccbench_pin"] = document["ccbench_pin"]
        expected_raw = _canonical_bytes(expected_document)
        if raw != expected_raw:
            raise FloorCampaignError(
                f"floor protocol bytes が legacy anchor + target pair の canonical bytes でない: {rel}"
            )
        _index_protocol_record(
            index, path=rel, document=document, raw=raw,
            commit_oid=commit_oid,
        )
    if working_paths != committed_paths:
        raise FloorCampaignError(
            "floor protocol namespace の working tree entry 集合が "
            "HEAD 固定 commit と不一致: "
            f"working={sorted(working_paths)} committed={sorted(committed_paths)}"
        )
    return index


def scan_floor_protocol_index(
        *, root=ROOT) -> dict[tuple[str, str], IndexedFloorProtocol]:
    """legacy anchor と sanctioned namespace の閉集合を strict index 化する。"""
    root = Path(root)
    return _scan_floor_protocol_index_at_commit(
        root=root, commit_oid=_head_commit_oid(root),
    )


def resolve_current_floor_protocol(*, root=ROOT) -> IndexedFloorProtocol:
    """現行契約候補内の HEAD pin exact を優先し、一意候補へだけ fallback する。"""
    root = Path(root)
    head_commit = _head_commit_oid(root)
    index = _scan_floor_protocol_index_at_commit(
        root=root, commit_oid=head_commit,
    )
    candidates: list[IndexedFloorProtocol] = []
    for record in index.values():
        if record.commit_oid != head_commit:
            raise FloorCampaignError(
                "floor protocol index record の固定 commit OID が resolver と不一致: "
                f"path={record.path} record={record.commit_oid!r} "
                f"resolver={head_commit}"
            )
        env_tag = record.document["env_tag"]
        try:
            current = _env_contract.lookup(env_tag)
        except _env_contract.EnvContractError as exc:
            raise FloorCampaignError(
                f"floor protocol env_tag の現行契約を解決できない: {env_tag}: {exc}"
            ) from exc
        if record.contract_sha256 == current.contract_sha256:
            candidates.append(record)
    if not candidates:
        raise FloorCampaignError(
            "現行 env 契約の floor protocol を一意に解決できない: "
            "current_count=0 head_exact_count=0"
        )
    if len(candidates) == 1:
        return candidates[0]

    head_gitlink = _ccbench_gitlink(root, head_commit)
    head_exact = [
        record for record in candidates
        if record.ccbench_pin == head_gitlink
    ]
    if len(head_exact) == 1:
        return head_exact[0]
    raise FloorCampaignError(
        "現行 env 契約の floor protocol を一意に解決できない: "
        f"current_count={len(candidates)} "
        f"head_exact_count={len(head_exact)}"
    )


def _ccbench_gitlink(root: Path, commit_oid: str) -> str:
    """固定 commit の ``external/ccbench`` gitlink を読む (fail-closed)。"""
    try:
        completed = subprocess.run(
            _floor_git_read_command("ls-tree", commit_oid, "external/ccbench"),
            cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
            env=_sanitized_floor_git_env(),
        )
        out = completed.stdout.decode("utf-8", "strict")
    except (OSError, subprocess.CalledProcessError, UnicodeError) as exc:
        raise FloorCampaignError(f"ccbench gitlink を実測できない: {exc}") from exc
    # 期待形式: "160000 commit <40hex>\texternal/ccbench"
    fields = out.split()
    if len(fields) < 3 or fields[0] != "160000" or fields[1] != "commit":
        raise FloorCampaignError(f"external/ccbench が gitlink (submodule) でない: {out!r}")
    sha = fields[2]
    if len(sha) != 40 or any(ch not in "0123456789abcdef" for ch in sha):
        raise FloorCampaignError(f"ccbench gitlink が 40 桁 hex でない: {sha!r}")
    return sha


def _reseal_published_artifact_error(
        destination_rel: str, detail: str,
) -> FloorCampaignError:
    """自動 rollback しない発行失敗へ、復旧に必要な exact path を載せる。"""
    return FloorCampaignError(
        f"{detail}。artifact={destination_rel}。"
        "この file を取り除くまで、この repository では新しい床値 protocol を発行できない。"
        "自動削除しないため commit 禁止であり、commit してはならない"
    )


def _reseal_protocol_at_root(root: Path) -> dict[str, object]:
    """零引数 public issuer の tmp-repository テスト可能な private core。"""
    root = Path(root)
    head_commit = _head_commit_oid(root)
    index = _scan_floor_protocol_index_at_commit(root=root, commit_oid=head_commit)
    anchors = [record for record in index.values() if record.path == _FLOOR_PROTOCOL_REL]
    if len(anchors) != 1:
        raise FloorCampaignError("floor protocol index に legacy anchor が exact 1 件ない")
    anchor = anchors[0]
    env_tag = anchor.document["env_tag"]
    try:
        target_contract = _env_contract.lookup(env_tag)
    except _env_contract.EnvContractError as exc:
        raise FloorCampaignError(f"AI reseal target の current env 契約を解決できない: {exc}") from exc
    if target_contract.env_tag != env_tag:
        raise FloorCampaignError("AI reseal target contract の env_tag が anchor と不一致")
    target_pin = _ccbench_gitlink(root, head_commit)
    target_pair = _validate_floor_protocol_pair(
        target_contract.contract_sha256, target_pin,
    )
    if target_pair in index:
        raise FloorCampaignError(
            "AI reseal は同一組の protocol を再発行できない: "
            f"pair={target_pair!r} existing={index[target_pair].path}"
        )

    successor = copy.deepcopy(anchor.document)
    successor["contract_sha256"] = target_pair[0]
    successor["ccbench_pin"] = target_pair[1]

    def target_contract_lookup(candidate_env_tag: str) -> str:
        if candidate_env_tag != env_tag:
            raise _floor_contract.FloorContractError(
                "AI reseal successor の env_tag が anchor と不一致"
            )
        return target_pair[0]

    try:
        normalized = _floor_contract.validate_protocol(
            successor, contract_sha256_lookup=target_contract_lookup,
        )
        # deep copy と許可 2 field の代入後を再確認する post-condition assertion。
        # 外部 artifact の入力防壁は scan_floor_protocol_index 側が担う。
        validate_ai_reseal_inheritance(anchor.document, normalized)
    except _floor_contract.FloorContractError as exc:
        raise FloorCampaignError(str(exc)) from exc
    canonical = _canonical_bytes(normalized)
    built = BuiltProtocol(
        document=normalized,
        canonical_bytes=canonical,
        sha256=hashlib.sha256(canonical).hexdigest(),
    )
    destination_rel = _derived_reseal_protocol_relpath(*target_pair)
    destination = root / destination_rel

    # 初回 scan 後の祖先差し替えを writer の直前でも拒否する。
    _assert_floor_protocol_ancestors(root)
    try:
        _write_protocol_document_create_only(destination, built)
    except FloorCampaignError as exc:
        if os.path.lexists(destination):
            raise _reseal_published_artifact_error(
                destination_rel, f"AI reseal write 検証失敗: {exc}",
            ) from exc
        raise

    root_real = os.path.realpath(root)
    destination_real = os.path.realpath(destination)
    try:
        destination_inside_root = os.path.commonpath(
            (root_real, destination_real),
        ) == root_real
    except ValueError:
        destination_inside_root = False
    if not destination_inside_root:
        raise _reseal_published_artifact_error(
            destination_rel,
            f"destination realpath が repository 外: {destination_real}",
        )

    try:
        published_head = _head_commit_oid(root)
    except FloorCampaignError as exc:
        raise _reseal_published_artifact_error(
            destination_rel, f"AI reseal publish 後の HEAD 検証失敗: {exc}",
        ) from exc
    if published_head != head_commit:
        raise _reseal_published_artifact_error(
            destination_rel, "AI reseal publish 中に HEAD commit が変化した",
        )

    try:
        read_back = destination.read_bytes()
        reparsed = _strict_parse_protocol_bytes(read_back, source=destination_rel)
    except (OSError, FloorCampaignError) as exc:
        raise _reseal_published_artifact_error(
            destination_rel, f"AI reseal post-write 検証失敗: {exc}",
        ) from exc
    try:
        normalized_read_back = validate_protocol(reparsed)
        read_back_rel = _derived_reseal_protocol_relpath(
            normalized_read_back["contract_sha256"],
            normalized_read_back["ccbench_pin"],
        )
        canonical_read_back = _canonical_bytes(normalized_read_back)
    except FloorCampaignError as exc:
        raise _reseal_published_artifact_error(
            destination_rel,
            f"AI reseal post-write protocol 検証失敗: {exc}",
        ) from exc
    post_write_problems = []
    try:
        validate_ai_reseal_inheritance(anchor.document, normalized_read_back)
    except _floor_contract.FloorContractError as exc:
        post_write_problems.append(f"read-back inheritance が不一致: {exc}")
    if read_back != built.canonical_bytes:
        post_write_problems.append("read-back bytes が builder canonical bytes と不一致")
    if reparsed != built.document:
        post_write_problems.append("read-back strict parse が builder document と不一致")
    if read_back_rel != destination_rel:
        post_write_problems.append("read-back の導出 path が destination と不一致")
    if normalized_read_back != built.document:
        post_write_problems.append("read-back document が builder document と不一致")
    if canonical_read_back != read_back:
        post_write_problems.append("read-back bytes が canonical bytes と不一致")
    if canonical_read_back != built.canonical_bytes:
        post_write_problems.append("read-back canonical bytes が builder bytes と不一致")
    if post_write_problems:
        raise _reseal_published_artifact_error(
            destination_rel,
            "AI reseal post-write 検証失敗: " + "; ".join(post_write_problems),
        )
    return {
        "status": "resealed",
        "path": destination_rel,
        "contract_sha256": target_pair[0],
        "ccbench_pin": target_pair[1],
        "byte_length": len(read_back),
        "sha256": built.sha256,
    }


def reseal_protocol() -> dict[str, object]:
    """active contract と HEAD gitlink だけから AI reseal を create-only 発行する。"""
    return _reseal_protocol_at_root(ROOT)


def build_protocol_document(master_seed, env_tag, *, stock_configuration,
                            extime_s, wired_min_rel_floor, root=ROOT) -> BuiltProtocol:
    """承認定数を単一源から機械組立てし ``validate_protocol`` を通した protocol を返す (C4-7)。

    ``extime_s`` は validator が承認 leaf の pin で強制する。引数は凍結時の確認用であり、
    承認値以外は ``validate_protocol`` が拒否する。それ以外の引数
    ``master_seed`` / ``env_tag`` / ``stock_configuration`` / ``wired_min_rel_floor`` は
    validate_protocol が pin しない自由値で、**凍結時にユーザーが確定する欄**である。
    既定値を持たない (値の発明・追認を禁止する — 欠落は TypeError で落ちる)。

    承認 pin 値 (n_sessions=8 等・閾値・除外理由)・v1 freeze {path, sha256}・ccbench full
    commit sha は ``orchestrator.campaign.s8b_approved`` を単一源として焼く。**現在値の追認を許さない**
    (C4-4): 実 v1 bytes が ``APPROVED_FREEZE_SHA256`` と、実 gitlink が ``CCBENCH_FULL_SHA``
    と一致することを組立て前に検証する。``contract_sha256`` は ``env_tag`` から導出する
    (validate_protocol が cross-field 照合する、§5-v)。canonical bytes + sha256 も返す。

    凍結手順: master_seed / env_tag を確定 → 本 builder → write_protocol_document で明示
    出力先へ → ユーザーが commit (AI-Agent: none)。
    """
    root = Path(root)
    if not isinstance(master_seed, str) or not master_seed:
        raise FloorCampaignError("build_protocol_document: master_seed が空でない str でない")
    if not isinstance(env_tag, str) or not env_tag:
        raise FloorCampaignError("build_protocol_document: env_tag が空でない str でない")

    # 実 v1 bytes を承認定数と照合してから焼く (現在値の追認を拒否、C4-4)。
    v1_path = root / s8b_approved.APPROVED_FREEZE_PATH
    try:
        actual_v1 = hashlib.sha256(v1_path.read_bytes()).hexdigest()
    except OSError as exc:
        raise FloorCampaignError(f"v1 freeze を読めない: {v1_path}: {exc}") from exc
    if actual_v1 != s8b_approved.APPROVED_FREEZE_SHA256:
        raise FloorCampaignError(
            "v1 freeze bytes が承認定数と不一致 (現在値の追認を拒否): "
            f"実 {actual_v1} != 承認 {s8b_approved.APPROVED_FREEZE_SHA256}"
        )

    # 実 gitlink を承認定数と照合してから焼く (現在値の追認を拒否、C4-4)。
    actual_link = _ccbench_gitlink(root, _head_commit_oid(root))
    if actual_link != s8b_approved.CCBENCH_FULL_SHA:
        raise FloorCampaignError(
            "ccbench gitlink が承認定数と不一致 (現在値の追認を拒否): "
            f"実 {actual_link} != 承認 {s8b_approved.CCBENCH_FULL_SHA}"
        )

    # contract_sha256 は env_tag から導出 (validate_protocol が cross-field 検査する)。
    try:
        contract = _env_contract.lookup(env_tag)
    except _env_contract.EnvContractError as exc:
        raise FloorCampaignError(f"env_tag が env 契約に未登録: {exc}") from exc

    document = {
        "schema": PROTOCOL_SCHEMA,
        "formula": s8b_floor_stats.FORMULA_ID,
        "env_tag": env_tag,
        "ccbench_pin": s8b_approved.CCBENCH_FULL_SHA,
        "freeze": {
            "path": s8b_approved.APPROVED_FREEZE_PATH,
            "sha256": s8b_approved.APPROVED_FREEZE_SHA256,
        },
        "stock_configuration": stock_configuration,
        "n_sessions": s8b_approved.APPROVED_N_SESSIONS,
        "reps": s8b_approved.APPROVED_REPS,
        "master_seed": master_seed,
        "schedule_algorithm": SCHEDULE_ALGORITHM,
        "extime_s": extime_s,
        "wired_min_rel_floor": wired_min_rel_floor,
        "retry_slots_per_cell": s8b_approved.APPROVED_RETRY_SLOTS,
        "session_cv_max": s8b_approved.APPROVED_SESSION_CV_MAX,
        "cell_cv_max": s8b_approved.APPROVED_CELL_CV_MAX,
        "scale_adequacy_rel_tolerance": s8b_approved.APPROVED_SCALE_ADEQUACY,
        "allowed_excluded_reasons": list(s8b_approved.APPROVED_REASONS),
        "contract_sha256": contract.contract_sha256,
    }
    # validate_protocol を単一の受理ゲートに通す (builder 自身では判定を持たない)。
    normalized, _contract = _validate_protocol_against_current(document)
    canonical = _canonical_bytes(normalized)
    # 自由文字列 field (master_seed 等) 経由でも holdout 三軸 conjunction が protocol bytes に
    # 混入すれば凍結前に拒否する。検索器と同じ判定核を共用し、builder の自己申告にしない。
    hits = _holdout_freeze.holdout_conjunction_hits(
        {"floor_protocol.json": canonical.decode("utf-8")}
    )
    contaminated = {name: paths for name, paths in hits.items() if paths}
    if contaminated:
        raise FloorCampaignError(
            f"build_protocol_document: canonical bytes に holdout conjunction hit: {contaminated}"
        )
    return BuiltProtocol(
        document=normalized,
        canonical_bytes=canonical,
        sha256=hashlib.sha256(canonical).hexdigest(),
    )


def _guarded_freeze_dirs(root: Path) -> tuple:
    """writer が書込みを拒否する実凍結領域の解決済み path (存在しなくても解決)。"""
    dirs = []
    for rel in ("output/s8b-freeze", "output/env"):
        dirs.append((root / rel).resolve())
    return tuple(dirs)


def _write_protocol_document_create_only(destination: Path, built: "BuiltProtocol") -> Path:
    """canonical bytes を同一 directory の tmp から create-only link で確定する。"""
    if not isinstance(built, BuiltProtocol):
        raise FloorCampaignError("write_protocol_document: BuiltProtocol でない")
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=str(destination.parent),
            prefix=f".{destination.name}.", suffix=".tmp", delete=False,
        ) as stream:
            tmp = Path(stream.name)
            stream.write(built.canonical_bytes)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(tmp, destination)
        except FileExistsError as exc:
            raise FloorCampaignError(
                f"protocol document が既に存在する (create-only): {destination}"
            ) from exc
        dir_fd = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError as exc:
        if isinstance(exc, FileExistsError):  # pragma: no cover - 上で翻訳済み
            raise FloorCampaignError(
                f"protocol document が既に存在する (create-only): {destination}"
            ) from exc
        raise FloorCampaignError(f"protocol document を書けない: {destination}: {exc}") from exc
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
    return destination


def write_protocol_document(path, built: "BuiltProtocol", *, root=ROOT) -> Path:
    """``built`` を create-only で書き出す。**default path なし (明示出力先必須)**。

    出力先が実 repo の凍結領域 (``output/s8b-freeze/`` ・ ``output/env/``) 配下なら拒否する
    (テスト誤爆の第二防壁 — 実凍結はユーザー手順で行い、AI-Agent: none で commit する)。
    既存 path も拒否する (create-only)。ファイル bytes は canonical bytes と一致し、その
    sha256 は ``built.sha256`` (= protocol_sha256 の pre-image) に等しい。
    """
    destination = Path(path)
    if not isinstance(built, BuiltProtocol):
        raise FloorCampaignError("write_protocol_document: BuiltProtocol でない")
    resolved_parent = destination.parent.resolve()
    for guarded in _guarded_freeze_dirs(Path(root)):
        if resolved_parent == guarded or guarded in resolved_parent.parents:
            raise FloorCampaignError(
                "実 repo の凍結領域配下への書込みは拒否 (実凍結はユーザー手順): "
                f"{destination} ⊂ {guarded}"
            )
    return _write_protocol_document_create_only(destination, built)


def freeze_protocol(*, confirm_user_freeze: bool, root=ROOT, isatty_fn=None,
                    receipt_verify_fn=None, after_write_fn=None) -> dict:
    """対話 shell の誤操作防壁付きで、承認値だけから protocol を固定 path へ実凍結する。

    isatty は actor 認証ではなく、PTY 割当・module 直呼びで迂回可能な誤操作防壁である。
    実効の正本は規律、guard_write hook、AI provenance 監査の組合せに置く。

    ``root`` と三つの callable は tmp repository で防壁を実発火させるテスト seam。
    CLI はいずれも注入せず、固定 ``ROOT`` と実 stdin/T-080 verifier を使用する。
    """
    if confirm_user_freeze is not True:
        raise FloorCampaignError(
            "freeze-protocol は --confirm-user-freeze の明示確認が必須"
        )
    tty_check = sys.stdin.isatty if isatty_fn is None else isatty_fn
    if not callable(tty_check) or tty_check() is not True:
        raise FloorCampaignError(
            "実凍結は人間の対話 shell から実行する (stdin が tty でないため拒否)"
        )

    root = Path(root)
    verifier = _t080_migration.verify_receipt if receipt_verify_fn is None else receipt_verify_fn
    try:
        receipt = verifier(root=root)
    except _t080_migration.MigrationError as exc:
        raise FloorCampaignError(f"T-080 receipt 検証失敗: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 (外部 verifier seam も fail-closed)
        raise FloorCampaignError(f"T-080 receipt 検証失敗: {exc}") from exc
    if (getattr(receipt, "state", None) != "active-valid"
            or tuple(getattr(receipt, "refusals", ()))
            or not isinstance(
                getattr(receipt, "t080_freeze_migration_observation", None), Mapping
            )):
        raise FloorCampaignError(
            "T-080 receipt が発効状態でない: "
            f"state={getattr(receipt, 'state', None)!r}, "
            f"refusals={list(getattr(receipt, 'refusals', ()))}"
        )

    built = build_protocol_document(
        s8b_approved.APPROVED_MASTER_SEED,
        s8b_approved.APPROVED_ENV_TAG,
        stock_configuration=s8b_approved.APPROVED_STOCK_CONFIGURATION,
        extime_s=s8b_approved.APPROVED_EXTIME_S,
        wired_min_rel_floor=s8b_approved.APPROVED_WIRED_MIN_REL_FLOOR,
        root=root,
    )
    destination = root / _FLOOR_PROTOCOL_REL
    _write_protocol_document_create_only(destination, built)
    if after_write_fn is not None:
        after_write_fn(destination)

    try:
        raw = destination.read_bytes()
        actual_sha256 = hashlib.sha256(raw).hexdigest()
        reparsed, _contract = _validate_protocol_against_current(
            load_protocol(destination),
        )
    except (OSError, FloorCampaignError) as exc:
        raise FloorCampaignError(
            f"post-write 検証失敗。自動削除しないため commit 禁止: {exc}"
        ) from exc
    problems = []
    if raw != built.canonical_bytes:
        problems.append("read-back bytes が canonical bytes と不一致")
    if actual_sha256 != built.sha256:
        problems.append("read-back sha256 が builder sha256 と不一致")
    if reparsed != built.document:
        problems.append("strict re-parse + validate_protocol が builder document と不一致")
    if problems:
        raise FloorCampaignError(
            "post-write 検証失敗。自動削除しないため commit 禁止: " + "; ".join(problems)
        )
    return {
        "status": "frozen",
        "path": _FLOOR_PROTOCOL_REL,
        "byte_length": len(raw),
        "sha256": actual_sha256,
    }


# --------------------------------------------------------------------------- #
# freeze 構造検査 + セル列挙 (POINTS 手書き禁止・freeze から取る)               #
# --------------------------------------------------------------------------- #

def _holdout_workload(holdout: Mapping, *, holdout_id: str) -> dict:
    try:
        return _floor_contract._holdout_workload(holdout, holdout_id=holdout_id)
    except _floor_contract.FloorContractError as exc:
        raise FloorCampaignError(str(exc)) from exc


def enumerate_cells(freeze: Mapping, *, stock_configuration: str) -> list[dict]:
    """freeze から 12 セル (holdout × configuration) を決定論的に列挙する (純粋関数)。

    構成集合は全 holdout で一致し、stock_configuration を含むことを検査する。
    records/threads/workload は freeze の holdout から取る (POINTS 手書き・rr 値コピー禁止)。
    """
    try:
        return _floor_contract.enumerate_cells(
            freeze, stock_configuration=stock_configuration,
        )
    except _floor_contract.FloorContractError as exc:
        raise FloorCampaignError(str(exc)) from exc


# --------------------------------------------------------------------------- #
# schedule v2 (round 単位 seed 置換, 純粋関数)                                  #
# --------------------------------------------------------------------------- #

def build_schedule(*, cells: list[dict], master_seed: str, n_sessions: int) -> list[dict]:
    """round r=1..n_sessions ごとに 12 セル (cell_id sort・一意) を seed 置換した session 列。

    契約 (β-3): 各 round は正規化済み (sort 済み・重複なし) の全 cell_id の完全置換で、
    各セルは round ごとにちょうど 1 回現れる。seq は 0..(n_sessions×|cells|-1) の通し番号。
    エントリは {seq, round, cell_id} のみ (96 スロット一括置換ではなく round 構造を保つ)。入力
    順に依存しないよう cell_id を sort し一意検査する。
    """
    try:
        return _floor_contract.build_schedule(
            cells=cells, master_seed=master_seed, n_sessions=n_sessions,
        )
    except _floor_contract.FloorContractError as exc:
        raise FloorCampaignError(str(exc)) from exc


def _floor_reservation_budget(
    *, protocol: Mapping, cells: list[dict], schedule: list[dict],
) -> tuple[int, int]:
    """validated schedule から campaign の有限 walltime envelope を導出する。

    凍結式は ``shared_dependency_prebuild + cell_count * (build_cap_per_cell +
    (scheduled_attempts_per_cell + retry_slots_per_cell) *
    (bench_extime_s * reps + verify_cap_per_attempt)) + finalize_reserve``。
    shared dependency prebuild は sort_best がある run だけ configure/target 各 900s を一度加える。
    build cap=900s は trace-disabled v2 build 1 セルの hard upper bound、verify cap=120s は
    binary receipt + strict pre/post probe、finalize reserve=600s は terminal/result fsync と
    rejection forensic の退避枠である。leaf には前半を ``required_s``、末尾を
    ``safety_margin_s`` として渡し、合計を必ず予約させる。
    """
    if not cells or not schedule:
        raise FloorCampaignError("reservation 導出には空でない cells/schedule が必要")
    cell_ids = {cell["cell_id"] for cell in cells}
    counts = {cell_id: 0 for cell_id in cell_ids}
    for row in schedule:
        cell_id = row.get("cell_id")
        if cell_id not in counts:
            raise FloorCampaignError("reservation 導出時に schedule の未知 cell を検出")
        counts[cell_id] += 1
    occurrences = set(counts.values())
    if len(occurrences) != 1 or next(iter(occurrences)) <= 0:
        raise FloorCampaignError("reservation 導出時に schedule のセル出現数が不均一")
    scheduled_per_cell = next(iter(occurrences))
    attempt_cap = (
        protocol["extime_s"] * protocol["reps"]
        + _FLOOR_VERIFY_CAP_PER_ATTEMPT_S
    )
    per_cell = (
        _FLOOR_BUILD_CAP_PER_CELL_S
        + (scheduled_per_cell + protocol["retry_slots_per_cell"]) * attempt_cap
    )
    shared_dependency_prebuild_s = (
        _FLOOR_DEPENDENCY_CONFIGURE_CAP_S + _FLOOR_DEPENDENCY_TARGET_CAP_S
        if any(cell.get("configuration_id") == "sort_best" for cell in cells)
        else 0
    )
    required_s = shared_dependency_prebuild_s + len(cell_ids) * per_cell
    if required_s <= 0:
        raise FloorCampaignError("reservation required_s を正数として導出できない")
    return required_s, _FLOOR_FINALIZE_RESERVE_S


# --------------------------------------------------------------------------- #
# journal (append-only jsonl + fsync)                                          #
# --------------------------------------------------------------------------- #

def _journal_append(
        journal_path: Path, record: Mapping,
        *, write_capability: Optional[WriteCapability] = None) -> None:
    line = (json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    opener = (
        open_with_write_capability(write_capability, journal_path, "ab")
        if write_capability is not None else open(journal_path, "ab")
    )
    with opener as stream:
        stream.write(line)
        stream.flush()
        os.fsync(stream.fileno())


def _read_journal(journal_path: Path) -> list[dict]:
    if not journal_path.exists():
        return []
    records: list[dict] = []
    with open(journal_path, "r", encoding="utf-8") as stream:
        for lineno, raw in enumerate(stream, start=1):
            raw = raw.strip()
            if not raw:
                raise FloorCampaignError(f"journal 行 {lineno} が空 (strict JSONL 違反)")
            try:
                value = json.loads(
                    raw, object_pairs_hook=_no_duplicate_pairs,
                    parse_constant=_reject_json_constant,
                )
            except (json.JSONDecodeError, FloorCampaignError) as exc:
                # 末尾切れ (crash) の 1 行。fail-closed: truncated journal の自動続行は
                # 危険なので拒否する (都合のよい session 再現を許さない)。
                raise FloorCampaignError(
                    f"journal 行 {lineno} が壊れている (truncated crash の疑い): {exc}"
                ) from exc
            if not isinstance(value, dict):
                raise FloorCampaignError(f"journal 行 {lineno} が object でない")
            records.append(value)
    return records


def _transition_pre_measure_journal_to_v3(
        journal_path: Path, records: list[dict], *,
        write_capability: Optional[WriteCapability] = None) -> None:
    """測定 event のない v2 journal の schema 行だけを v3 へ原子的に遷移する。"""
    if not any(
            record.get("event") in {"launch-start", "campaign-start"}
            and record.get("schema") == "s8b-floor-journal/v2"
            for record in records):
        return
    if any(record.get("event") in {"session-start", "session"} for record in records):
        raise FloorCampaignError("v2→v3 transition は測定開始後には実行できない")
    targets = [
        record for record in records
        if record.get("event") in {"launch-start", "campaign-start"}
        and record.get("schema") == "s8b-floor-journal/v2"
    ]
    if not targets:
        return
    transitioned = [dict(record) for record in records]
    for record in transitioned:
        if (record.get("event") in {"launch-start", "campaign-start"}
                and record.get("schema") == "s8b-floor-journal/v2"):
            record["schema"] = JOURNAL_SCHEMA
    payload = b"".join(
        (json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        for record in transitioned
    )
    tmp = journal_path.with_name(f".{journal_path.name}.v3-transition-{uuid.uuid4().hex}")
    opener = (
        open_with_write_capability(write_capability, tmp, "xb")
        if write_capability is not None else open(tmp, "xb")
    )
    try:
        with opener as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, journal_path)
        records[:] = transitioned
    finally:
        if tmp.exists():
            tmp.unlink()


# --------------------------------------------------------------------------- #
# strict single-tenant probe (規律4, runner の共有分類器を消費)                 #
# --------------------------------------------------------------------------- #

_PROBE_ARGV = ["pgrep", "-af", r"ycsb_.*\.exe"]


def _default_probe_fn() -> tuple[int, str, str]:
    """pgrep -af 'ycsb_.*\\.exe' を 1 回叩き (rc, stdout, stderr) を返す (OSError は投げる)。"""
    result = subprocess.run(
        _PROBE_ARGV, capture_output=True, text=True,
        timeout=_FLOOR_VERIFY_CAP_PER_ATTEMPT_S,
    )
    return result.returncode, result.stdout, result.stderr


def strict_probe(probe_fn: Callable[[], tuple[int, str, str]]) -> dict:
    """計測前後の臨界区間 probe。競合検知は lag-free の確定信号 (規律4)。

    分類は runner の共有 `classify_competing_probe` に委譲する (C4-5: 二重実装排除)。
    rc==1+空 → 競合なし / rc==0+PID 行 → 自 PID (`os.getpid()`) を除いて残れば競合 /
    rc==1+付随出力・rc==0+空・rc>1・負値・**rc==1+stderr 非空 (BusyBox 罠)** →
    `CompetingBenchProbeError` を CampaignAbort へ翻訳 (fail-closed)。probe_fn は
    (rc, stdout, stderr) を返す注入シーム (テスト用) で、stderr も分類器へ実値で渡す
    — runner の `competing_bench_pids` と全く同じ strict 契約を通す (C4-5 統一の要:
    floor だけが BusyBox ガードを死なせない)。除外は自 PID のみ (B-2 裁定済み —
    自分の子孫も競合として検出する。worklog 2026-07-18 (6) /
    docs/phase3-8b-descriptor-design.md §9)。生出力は戻り値に含め、呼び手が journal に残す。
    """
    try:
        rc, stdout, stderr = probe_fn()
    except subprocess.TimeoutExpired as exc:
        raise CampaignAbort(f"strict probe を有限時間内に実行できない: {exc}") from exc
    except OSError as exc:
        raise CampaignAbort(f"strict probe が OSError: {exc}") from exc
    try:
        competing = classify_competing_probe(rc, stdout, stderr, _PROBE_ARGV)
    except CompetingBenchProbeError as exc:
        raise CampaignAbort(
            f"strict probe が競合の有無を確定できない (fail-closed): {exc}") from exc
    return {
        "rc": rc, "stdout": stdout, "stderr": stderr,
        "competing": bool(competing),
    }


# --------------------------------------------------------------------------- #
# host / process provenance (G12 capture; γ-5/γ-12: 絶対 monotonic を持たない)  #
# --------------------------------------------------------------------------- #

def _boot_id() -> Optional[str]:
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip() or None
    except (OSError, UnicodeError):
        return None


def _cpuset() -> Optional[str]:
    try:
        for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
            if line.startswith("Cpus_allowed_list:"):
                return line.split(":", 1)[1].strip() or None
    except (OSError, UnicodeError):
        return None
    return None


def _proc_starttime() -> Optional[int]:
    """/proc/self/stat の starttime (field 22)。process identity の一部 (γ-5)。"""
    try:
        data = Path("/proc/self/stat").read_text(encoding="utf-8")
        after = data.rsplit(")", 1)[1].split()  # comm を括弧ごと除いた残り (field 3..)
        return int(after[19])
    except (OSError, UnicodeError, IndexError, ValueError):
        return None


def _host_provenance(*, now_fn: Callable[[], dt.datetime]) -> dict:
    """G12 capture: hostname / boot_id / job_id / cpuset / UTC。絶対 monotonic は持たない。"""
    return {
        "hostname": socket.gethostname(),
        "boot_id": _boot_id(),
        "job_id": os.environ.get("PBS_JOBID") or os.environ.get("SLURM_JOB_ID") or None,
        "cpuset": _cpuset(),
        "utc": now_fn().isoformat(),
    }


def _process_identity() -> dict:
    """process 同一性 (γ-5): pid + starttime + execution_uuid。resume 越しの識別用。"""
    return {
        "pid": os.getpid(),
        "starttime": _proc_starttime(),
        "execution_uuid": uuid.uuid4().hex,
    }


def _utc_text(value, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise FloorCampaignError(f"{field} が空でない UTC 文字列でない")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FloorCampaignError(f"{field} が ISO-8601 UTC でない: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise FloorCampaignError(f"{field} が UTC でない: {value!r}")
    return value


def _nullable_text(value, *, field: str):
    if value is not None and (not isinstance(value, str) or not value):
        raise FloorCampaignError(f"{field} が null または空でない str でない")
    return value


def _validate_host_provenance(value) -> dict:
    keys = {"hostname", "boot_id", "job_id", "cpuset", "utc"}
    if not isinstance(value, Mapping) or set(value) != keys:
        raise FloorCampaignError("host_provenance の key 集合が不一致")
    hostname = value["hostname"]
    if not isinstance(hostname, str) or not hostname:
        raise FloorCampaignError("host_provenance.hostname が空でない str でない")
    return {
        "hostname": hostname,
        "boot_id": _nullable_text(value["boot_id"], field="host_provenance.boot_id"),
        "job_id": _nullable_text(value["job_id"], field="host_provenance.job_id"),
        "cpuset": _nullable_text(value["cpuset"], field="host_provenance.cpuset"),
        "utc": _utc_text(value["utc"], field="host_provenance.utc"),
    }


def _validate_process_identity(value) -> dict:
    keys = {"pid", "starttime", "execution_uuid"}
    if not isinstance(value, Mapping) or set(value) != keys:
        raise FloorCampaignError("process_identity の key 集合が不一致")
    pid = value["pid"]
    starttime = value["starttime"]
    execution_uuid = value["execution_uuid"]
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        raise FloorCampaignError("process_identity.pid が正整数でない")
    if (starttime is not None
            and (isinstance(starttime, bool) or not isinstance(starttime, int)
                 or starttime < 0)):
        raise FloorCampaignError("process_identity.starttime が null または非負整数でない")
    if (not isinstance(execution_uuid, str)
            or re.fullmatch(r"[0-9a-f]{32}", execution_uuid) is None):
        raise FloorCampaignError("process_identity.execution_uuid が 32 桁 lowercase hex でない")
    return {"pid": pid, "starttime": starttime, "execution_uuid": execution_uuid}


def _validate_execution_receipt(
        value, *, contract, verified_calibration=None) -> dict:
    """receipt schema と contract mode を同じ consumer gate で再照合する。"""
    if not execution_guard.receipt_matches_contract(
            value,
            env_tag=contract.env_tag,
            contract_sha256=contract.contract_sha256,
            attestation_mode=contract.attestation_mode,
            verified_calibration=verified_calibration):
        raise FloorCampaignError(
            "execution_receipt が contract/attestation_mode と整合しない"
        )
    if value.get("schema") == execution_guard.RECEIPT_SCHEMA_V2:
        try:
            execution_guard.validate_receipt_v2(value)
            return json.loads(json.dumps(value, allow_nan=False))
        except (execution_guard.ExecutionGuardError, TypeError, ValueError) as exc:
            raise FloorCampaignError(f"execution receipt v2 検証失敗: {exc}") from exc

    keys = {"schema", "env_tag", "contract_sha256", "attestation"}
    if not isinstance(value, Mapping) or set(value) != keys:
        raise FloorCampaignError("execution_receipt の key 集合が不一致")
    attestation = value["attestation"]
    akeys = {"hostname", "boot_id", "cpuset", "captured_utc"}
    if not isinstance(attestation, Mapping) or set(attestation) != akeys:
        raise FloorCampaignError("execution_receipt.attestation の key 集合が不一致")
    hostname = attestation["hostname"]
    if not isinstance(hostname, str) or not hostname:
        raise FloorCampaignError("execution_receipt.attestation.hostname が空でない str でない")
    return {
        "schema": value["schema"],
        "env_tag": value["env_tag"],
        "contract_sha256": value["contract_sha256"],
        "attestation": {
            "hostname": hostname,
            "boot_id": _nullable_text(
                attestation["boot_id"], field="execution_receipt.attestation.boot_id"),
            "cpuset": _nullable_text(
                attestation["cpuset"], field="execution_receipt.attestation.cpuset"),
            "captured_utc": _utc_text(
                attestation["captured_utc"],
                field="execution_receipt.attestation.captured_utc"),
        },
    }


# --------------------------------------------------------------------------- #
# ScalePoint → session 射影 (s8b_floor_stats の有効性契約に従う)                #
# --------------------------------------------------------------------------- #

def _project_scalepoint(scale_point, *, reps: int, expected_use_perf: bool) -> dict:
    """rep 証跡から完備な rep の tps だけを統計入力へ射影する。"""
    source_throughputs = list(getattr(scale_point, "throughputs", None) or [])
    observations = getattr(scale_point, "rep_observations", None)
    if not isinstance(observations, (list, tuple)) or len(observations) != reps:
        # 証跡 carrier 欠落は成功既定にせず、全 logical rep を unknown/incomplete とする。
        padded = source_throughputs[:reps] + [None] * max(0, reps - len(source_throughputs))
        observations = [
            {
                "rep_index": index,
                "returncode": None,
                # Carrier が無ければ runner の例外捕捉有無も観測不能。False で補わない。
                "execution_failure": None,
                "counter_status": "incomplete" if expected_use_perf else "not_required",
                "missing_perf_events": (
                    list(s8b_floor_stats.PERF_EVENTS) if expected_use_perf else []
                ),
                "perf_raw": {event: None for event in s8b_floor_stats.PERF_EVENTS},
                "throughput": padded[index],
            }
            for index in range(reps)
        ]
    else:
        observations = [dict(observation) if isinstance(observation, Mapping) else {}
                        for observation in observations]

    observed_tps = [
        observation.get("throughput") for observation in observations
        if observation.get("throughput") is not None
    ]
    if observed_tps != source_throughputs:
        raise CampaignAbort(
            "ScalePoint.throughputs と rep_observations の raw throughput 列が不一致"
        )

    failures = 0
    throughputs = []
    for expected_index, observation in enumerate(observations):
        perf_raw = observation.get("perf_raw")
        raw_complete = (
            isinstance(perf_raw, Mapping)
            and set(perf_raw) == set(s8b_floor_stats.PERF_EVENTS)
        )
        missing = []
        if raw_complete and expected_use_perf:
            missing = [
                event for event in s8b_floor_stats.PERF_EVENTS
                if type(perf_raw[event]) is not int or perf_raw[event] < 0
            ]
        elif expected_use_perf:
            missing = list(s8b_floor_stats.PERF_EVENTS)
        derived_status = (
            "not_required" if not expected_use_perf
            else "complete" if not missing else "incomplete"
        )
        complete = (
            set(observation) == {
                "rep_index", "returncode", "counter_status", "missing_perf_events",
                "perf_raw", "throughput", "execution_failure",
            }
            and type(observation.get("rep_index")) is int
            and observation["rep_index"] == expected_index
            and type(observation.get("returncode")) is int
            and observation["returncode"] == 0
            and observation.get("counter_status") == derived_status
            and observation.get("missing_perf_events") == missing
            and raw_complete
            and derived_status in {"complete", "not_required"}
            and observation.get("execution_failure") is False
        )
        if complete:
            if observation.get("throughput") is not None:
                throughputs.append(observation["throughput"])
        else:
            failures += 1
    exec_failures = sum(
        observation.get("execution_failure") is True
        for observation in observations
    )
    return {
        "throughputs": throughputs,
        "exec_failures": exec_failures,
        "rep_observations": observations,
        "rep_integrity_failures": failures,
    }


# --------------------------------------------------------------------------- #
# build 12 cells (oracle と同一経路, trace-disabled)                           #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class _FloorOraclePreflightDiagnostic:
    detail_code: str
    origin: str
    outcome: str
    path: Optional[Path] = None
    generated_manifest_sha256: Optional[str] = None
    expected_manifest_sha256: Optional[str] = None

    def __post_init__(self) -> None:
        if self.detail_code not in (
                _FLOOR_TOOLCHAIN_PREFLIGHT_DETAIL_CODES
                | _FLOOR_DEPENDENCY_PREFLIGHT_DETAIL_CODES
                | _FLOOR_DEPENDENCY_POSTFLIGHT_DETAIL_CODES):
            raise ValueError("未知の floor oracle preflight detail_code")
        if type(self.origin) is not str or not self.origin or len(self.origin) > 128:
            raise ValueError("floor oracle preflight origin が不正")
        if self.outcome not in _FLOOR_PREFLIGHT_CANDIDATE_OUTCOMES:
            raise ValueError("floor oracle preflight outcome が不正")
        if self.path is not None and not isinstance(self.path, Path):
            raise TypeError("floor oracle preflight path が Path でない")
        manifest_hashes = (
            self.generated_manifest_sha256,
            self.expected_manifest_sha256,
        )
        if any(value is not None for value in manifest_hashes):
            if (
                self.detail_code
                != "floor-dependency-canonical-manifest-mismatch"
                or any(
                    type(value) is not str
                    or re.fullmatch(r"[0-9a-f]{64}", value) is None
                    for value in manifest_hashes
                )
            ):
                raise ValueError("floor canonical manifest 診断 hash が不正")

    @property
    def phase(self) -> str:
        if self.detail_code in _FLOOR_TOOLCHAIN_PREFLIGHT_DETAIL_CODES:
            return "floor-toolchain-preflight"
        if self.detail_code in _FLOOR_DEPENDENCY_POSTFLIGHT_DETAIL_CODES:
            return "floor-dependency-postflight"
        return "floor-dependency-preflight"

    @property
    def failed_leg(self) -> str:
        if self.detail_code in _FLOOR_TOOLCHAIN_PREFLIGHT_DETAIL_CODES:
            return "compiler"
        return "dependency"

    def private_dict(self) -> dict[str, object]:
        result = {
            "detail_code": self.detail_code,
            "origin": self.origin,
            "outcome": self.outcome,
            "path": None if self.path is None else str(self.path),
        }
        if self.generated_manifest_sha256 is not None:
            result["generated_manifest_sha256"] = (
                self.generated_manifest_sha256
            )
            result["expected_manifest_sha256"] = self.expected_manifest_sha256
        return result


def _bounded_utf8_text(value: str, *, max_bytes: int, keep_tail: bool) -> str:
    encoded = value.encode("utf-8", errors="backslashreplace")
    bounded = encoded[-max_bytes:] if keep_tail else encoded[:max_bytes]
    while bounded:
        try:
            return bounded.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            bounded = bounded[1:] if keep_tail else bounded[:-1]
    return ""


@dataclass(frozen=True)
class _FloorBuildExceptionDiagnostic:
    exception_type: str
    message_tail: str
    message_tail_sha256: str
    message_truncated: bool

    def private_dict(self) -> dict[str, object]:
        return {
            "schema_version": "s8b-floor-build-exception/v1",
            "exception_type": self.exception_type,
            "message_tail": self.message_tail,
            "message_tail_sha256": self.message_tail_sha256,
            "message_truncated": self.message_truncated,
        }


def _floor_build_exception_diagnostic(
        exc: BaseException,
) -> _FloorBuildExceptionDiagnostic:
    exception_type = getattr(type(exc), "__name__", "Exception")
    if type(exception_type) is not str or not exception_type:
        exception_type = "Exception"
    exception_type = _bounded_utf8_text(
        exception_type,
        max_bytes=_FLOOR_BUILD_EXCEPTION_TYPE_MAX_BYTES,
        keep_tail=False,
    ) or "Exception"
    try:
        message = str(exc)
    except BaseException:
        message = "<exception message unavailable>"
    if type(message) is not str:
        message = "<exception message unavailable>"
    encoded = message.encode("utf-8", errors="backslashreplace")
    message_tail = _bounded_utf8_text(
        message,
        max_bytes=_FLOOR_BUILD_EXCEPTION_MESSAGE_MAX_BYTES,
        keep_tail=True,
    )
    message_tail_bytes = message_tail.encode("utf-8")
    return _FloorBuildExceptionDiagnostic(
        exception_type=exception_type,
        message_tail=message_tail,
        message_tail_sha256=hashlib.sha256(message_tail_bytes).hexdigest(),
        message_truncated=(
            len(encoded) > _FLOOR_BUILD_EXCEPTION_MESSAGE_MAX_BYTES
        ),
    )


class _FloorOraclePreflightError(FloorCampaignError):
    """production floor の oracle 前検査を閉じた診断へ運ぶ内部例外。"""

    def __init__(
            self, message: str, *, detail_code: str, origin: str,
            outcome: str, path: Optional[Path] = None,
            generated_manifest_sha256: Optional[str] = None,
            expected_manifest_sha256: Optional[str] = None):
        super().__init__(message)
        self.diagnostic = _FloorOraclePreflightDiagnostic(
            detail_code=detail_code,
            origin=origin,
            outcome=outcome,
            path=path,
            generated_manifest_sha256=generated_manifest_sha256,
            expected_manifest_sha256=expected_manifest_sha256,
        )


def _preflight_candidate_path(value: object) -> Optional[Path]:
    if value is None:
        return None
    try:
        if os.fspath(value) == "":
            return None
        return Path(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class _FloorOracleDependencyBinding:
    source_root: Path
    expected_head: str
    observed_head: str
    config_sha256: str
    archive_sha256: str
    archive_nondebug_sha256: str
    expected_toolchain_manifest_sha256: str
    source_st_dev: int
    source_st_ino: int
    oracle_root: Optional[Path] = None
    canonical_lease_root: Optional[Path] = None
    dependency_manifest_sha256: Optional[str] = None
    transport_mode: str = "base-only"
    expected_config_sha256: Optional[str] = None
    expected_archive_nondebug_sha256: Optional[str] = None
    payload_policy_sha256: Optional[str] = None
    payload_policy_pin: Optional[str] = None
    captured_policy_pins: tuple[tuple[str, str], ...] = ()

    def cache_receipt(self) -> dict[str, str]:
        return {
            "masstree_head": self.observed_head,
            "config_sha256": self.config_sha256,
        }

    def private_dict(self) -> dict[str, object]:
        result = {
            "dependency_root": str(self.source_root),
            "dependency_expected_head": self.expected_head,
            "dependency_head": self.observed_head,
            "dependency_config_sha256": self.config_sha256,
            "dependency_archive_sha256": self.archive_sha256,
            "dependency_archive_nondebug_sha256": (
                self.archive_nondebug_sha256
            ),
            "dependency_toolchain_manifest_sha256": (
                self.expected_toolchain_manifest_sha256
            ),
            "dependency_source_st_dev": self.source_st_dev,
            "dependency_source_st_ino": self.source_st_ino,
        }
        if self.oracle_root is not None:
            result["oracle_dependency_root"] = str(self.oracle_root)
        if self.dependency_manifest_sha256 is not None:
            result["dependency_manifest_sha256"] = (
                self.dependency_manifest_sha256
            )
        if self.transport_mode != "base-only":
            result["dependency_transport_mode"] = self.transport_mode
        if self.expected_config_sha256 is not None:
            result["dependency_expected_config_sha256"] = self.expected_config_sha256
        if self.expected_archive_nondebug_sha256 is not None:
            result["dependency_expected_archive_nondebug_sha256"] = (
                self.expected_archive_nondebug_sha256
            )
        if self.payload_policy_sha256 is not None:
            result["dependency_payload_policy_sha256"] = self.payload_policy_sha256
        if self.payload_policy_pin is not None:
            result["dependency_payload_policy_pin"] = self.payload_policy_pin
        if self.captured_policy_pins:
            result["dependency_captured_policy_pins"] = dict(
                self.captured_policy_pins
            )
        return result


def _post_oracle_dependency_binding(
        attempt: object, dependency: _FloorOracleDependencyBinding,
) -> dict[str, str]:
    """Project the oracle content authority into the build capability."""
    if (not isinstance(attempt, Mapping)
            or attempt.get("classification") != "pass"
            or attempt.get("reason_code") != "sort-swo-oracle-pass"):
        raise FloorCampaignError("sort_best post-oracle binding の PASS attempt が不正")
    receipt = attempt.get("oracle_receipt")
    if not isinstance(receipt, Mapping):
        raise FloorCampaignError("sort_best post-oracle binding の oracle receipt が不正")
    manifest_sha256 = receipt.get("dependency_manifest_sha256")
    config_sha256 = receipt.get("dependency_config_sha256")
    for label, value in (
            ("dependency_manifest_sha256", manifest_sha256),
            ("dependency_config_sha256", config_sha256)):
        if (type(value) is not str
                or re.fullmatch(r"[0-9a-f]{64}", value) is None):
            raise FloorCampaignError(
                f"sort_best post-oracle binding の {label} が不正"
            )
    if (
        dependency.oracle_root is None
        or dependency.canonical_lease_root is None
        or dependency.dependency_manifest_sha256 is None
    ):
        raise FloorCampaignError(
            "sort_best post-oracle binding の canonical dependency が欠落"
        )
    if manifest_sha256 != dependency.dependency_manifest_sha256:
        raise FloorCampaignError(
            "sort_best oracle receipt の manifest hash が canonical binding と不一致"
        )
    if config_sha256 != dependency.config_sha256:
        raise FloorCampaignError(
            "sort_best oracle receipt の config.h hash が実 source binding と不一致"
        )
    return {
        "fetchcontent_base_dir": str(dependency.source_root.parent),
        "oracle_dependency_root": str(dependency.oracle_root),
        "dependency_manifest_sha256": manifest_sha256,
        "masstree_head": dependency.observed_head,
        "config_sha256": config_sha256,
        "archive_sha256": dependency.archive_sha256,
    }


@dataclass(frozen=True)
class _LoadedFloorMasstreePayloadPolicy:
    schema_version: str
    name: str
    pin: str
    config_sha256: str
    archive_projection: str
    archive_nondebug_sha256: str
    raw_sha256: str


def _floor_toolchain_manifest_sha256(manifest: object) -> str:
    try:
        payload = json.dumps(
            manifest, sort_keys=True, separators=(",", ":"),
            ensure_ascii=True, allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ValueError(
            "floor toolchain manifest を canonical JSON 化できない"
        ) from exc
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class _LoadedFloorThirdPartyPolicy:
    path: Path
    entries: tuple[tuple[object, object], ...]


def _load_floor_third_party_policy(
        repo_root: Path, *, origin: str,
) -> _LoadedFloorThirdPartyPolicy:
    policy_path = _silo_ladder.third_party_policy_path(Path(repo_root))
    try:
        sources = _silo_ladder.third_party_policy(Path(repo_root))
    except Exception as exc:
        raise _FloorOraclePreflightError(
            "共有 third-party policy の検証に失敗",
            detail_code="floor-dependency-policy-unavailable",
            origin=origin,
            outcome="invalid-path",
            path=policy_path,
        ) from exc
    return _LoadedFloorThirdPartyPolicy(
        path=policy_path,
        entries=tuple(
            (item.get("name"), item.get("pin")) for item in sources
        ),
    )


def _floor_third_party_policy_pin(
        policy: _LoadedFloorThirdPartyPolicy, name: str,
) -> str:
    matches = [pin for item_name, pin in policy.entries if item_name == name]
    if len(matches) != 1:
        raise _FloorOraclePreflightError(
            f"共有 policy の {name} pin が一意でない",
            detail_code="floor-dependency-policy-pin-nonunique",
            origin=f"shared-policy:{name}",
            outcome="invalid-path",
            path=policy.path,
        )
    pin = matches[0]
    if type(pin) is not str or re.fullmatch(r"[0-9a-f]{40}", pin) is None:
        raise _FloorOraclePreflightError(
            f"共有 policy の {name} pin が不正",
            detail_code="floor-dependency-policy-pin-invalid",
            origin=f"shared-policy:{name}",
            outcome="invalid-path",
            path=policy.path,
        )
    return pin


def _masstree_policy_pin(
        repo_root_or_policy: Path | _LoadedFloorThirdPartyPolicy,
) -> str:
    policy = (
        repo_root_or_policy
        if isinstance(repo_root_or_policy, _LoadedFloorThirdPartyPolicy)
        else _load_floor_third_party_policy(
            Path(repo_root_or_policy), origin="shared-policy:masstree",
        )
    )
    return _floor_third_party_policy_pin(policy, "masstree")


def _floor_third_party_policy_pins(repo_root: Path) -> dict[str, str]:
    """共有 policy から staged 3依存の pin を一度に取得する。"""
    policy = _load_floor_third_party_policy(
        Path(repo_root), origin="shared-policy:third-party",
    )
    pins: dict[str, str] = {}
    for name in _FLOOR_THIRD_PARTY_SOURCE_NAMES:
        pin = (
            _masstree_policy_pin(policy)
            if name == "masstree"
            else _floor_third_party_policy_pin(policy, name)
        )
        if type(pin) is not str or re.fullmatch(r"[0-9a-f]{40}", pin) is None:
            raise _FloorOraclePreflightError(
                f"共有 policy の {name} pin が不正",
                detail_code="floor-dependency-policy-pin-invalid",
                origin=f"shared-policy:{name}",
                outcome="invalid-path",
                path=policy.path,
            )
        pins[name] = pin
    return pins


def _floor_masstree_payload_policy_path(repo_root: Path) -> Path:
    return Path(repo_root) / "tools/pegasus/policies/floor_masstree_payload_v1.json"


def _load_floor_masstree_payload_policy(
        repo_root: Path = ROOT, *, expected_masstree_pin: Optional[str] = None,
) -> _LoadedFloorMasstreePayloadPolicy:
    """同一 raw bytes から strict policy と receipt hash を一度に導出する。"""
    path = _floor_masstree_payload_policy_path(Path(repo_root))
    try:
        raw = path.read_bytes()
        document = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_no_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, FloorCampaignError) as exc:
        raise _FloorOraclePreflightError(
            f"floor masstree payload policy を読めない: {path}",
            detail_code="floor-dependency-payload-policy-unavailable",
            origin="floor-payload-policy:masstree",
            outcome="invalid-path",
            path=path,
        ) from exc
    expected_keys = {
        "schema_version",
        "name",
        "pin",
        "config_sha256",
        "archive_projection",
        "archive_nondebug_sha256",
    }
    if type(document) is not dict:
        raise _FloorOraclePreflightError(
            "floor masstree payload policy の top-level が object でない",
            detail_code="floor-dependency-payload-policy-schema-invalid",
            origin="floor-payload-policy:masstree",
            outcome="invalid-path",
            path=path,
        )
    if set(document) != expected_keys:
        raise _FloorOraclePreflightError(
            "floor masstree payload policy の exact key 集合が不正",
            detail_code="floor-dependency-payload-policy-schema-invalid",
            origin="floor-payload-policy:masstree",
            outcome="invalid-path",
            path=path,
        )
    if (document["schema_version"] != "s8b-floor-masstree-payload/v3"
            or document["name"] != "masstree"):
        raise _FloorOraclePreflightError(
            "floor masstree payload policy の schema/name が不正",
            detail_code="floor-dependency-payload-policy-schema-invalid",
            origin="floor-payload-policy:masstree",
            outcome="invalid-path",
            path=path,
        )
    if (type(document["pin"]) is not str
            or re.fullmatch(r"[0-9a-f]{40}", document["pin"]) is None):
        raise _FloorOraclePreflightError(
            "floor masstree payload policy の pin が不正",
            detail_code="floor-dependency-payload-policy-schema-invalid",
            origin="floor-payload-policy:masstree",
            outcome="invalid-path",
            path=path,
        )
    if document["archive_projection"] != _MASSTREE_ARCHIVE_PROJECTION_ID:
        raise _FloorOraclePreflightError(
            "floor masstree payload policy の archive projection が不正",
            detail_code="floor-dependency-payload-policy-schema-invalid",
            origin="floor-payload-policy:masstree",
            outcome="invalid-path",
            path=path,
        )
    for key in ("config_sha256", "archive_nondebug_sha256"):
        if (type(document[key]) is not str
                or re.fullmatch(r"[0-9a-f]{64}", document[key]) is None):
            raise _FloorOraclePreflightError(
                f"floor masstree payload policy の {key} が不正",
                detail_code="floor-dependency-payload-policy-hash-invalid",
                origin="floor-payload-policy:masstree",
                outcome="invalid-path",
                path=path,
            )
    shared_pin = (
        _masstree_policy_pin(Path(repo_root))
        if expected_masstree_pin is None else expected_masstree_pin
    )
    if (type(shared_pin) is not str
            or re.fullmatch(r"[0-9a-f]{40}", shared_pin) is None):
        raise _FloorOraclePreflightError(
            "captured shared policy の masstree pin が不正",
            detail_code="floor-dependency-policy-pin-invalid",
            origin="shared-policy:masstree",
            outcome="invalid-path",
            path=_silo_ladder.third_party_policy_path(Path(repo_root)),
        )
    if document["pin"] != shared_pin:
        raise _FloorOraclePreflightError(
            "floor masstree payload policy の pin が共有 policy と不一致",
            detail_code="floor-dependency-payload-policy-pin-mismatch",
            origin="floor-payload-policy:masstree",
            outcome="identity-mismatch",
            path=path,
        )
    return _LoadedFloorMasstreePayloadPolicy(
        schema_version=document["schema_version"],
        name=document["name"],
        pin=document["pin"],
        config_sha256=document["config_sha256"],
        archive_projection=document["archive_projection"],
        archive_nondebug_sha256=document["archive_nondebug_sha256"],
        raw_sha256=hashlib.sha256(raw).hexdigest(),
    )


def _floor_git_environment() -> dict[str, str]:
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
    })
    return env


def _sha256_regular_file(path: Path) -> str:
    label = "config.h"
    missing_code = "floor-dependency-config-missing"
    nonregular_code = "floor-dependency-config-not-regular"
    hash_code = "floor-dependency-config-hash-unavailable"
    missing_outcome = "config-h-missing"
    nonregular_outcome = "config-h-not-regular-file"
    try:
        info = path.lstat()
    except OSError as exc:
        raise _FloorOraclePreflightError(
            f"masstree {label} が存在しない",
            detail_code=missing_code,
            origin="floor-dependency:masstree",
            outcome=missing_outcome,
            path=path.parent,
        ) from exc
    if path.is_symlink() or not stat.S_ISREG(info.st_mode):
        raise _FloorOraclePreflightError(
            f"masstree {label} が non-symlink regular file でない",
            detail_code=nonregular_code,
            origin="floor-dependency:masstree",
            outcome=nonregular_outcome,
            path=path.parent,
        )
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(64 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise _FloorOraclePreflightError(
            f"masstree {label} を hash できない",
            detail_code=hash_code,
            origin="floor-dependency:masstree",
            outcome="invalid-path",
            path=path.parent,
        ) from exc
    return digest.hexdigest()


def _verify_masstree_archive(path: Path) -> MasstreeArchiveDigests:
    """単一 no-follow capture から raw SHA と承認対象の射影を得る。"""
    try:
        entry = path.lstat()
    except OSError as exc:
        raise _FloorOraclePreflightError(
            "masstree libkohler_masstree_json.a が存在しない",
            detail_code="floor-dependency-archive-missing",
            origin="floor-dependency:masstree",
            outcome="missing",
            path=path.parent,
        ) from exc
    if stat.S_ISLNK(entry.st_mode) or not stat.S_ISREG(entry.st_mode):
        raise _FloorOraclePreflightError(
            "masstree libkohler_masstree_json.a が non-symlink regular file でない",
            detail_code="floor-dependency-archive-not-regular",
            origin="floor-dependency:masstree",
            outcome="not-regular-file",
            path=path.parent,
        )
    try:
        return masstree_archive_digests(path)
    except MasstreeArchiveProjectionError as exc:
        raise _FloorOraclePreflightError(
            "masstree libkohler_masstree_json.a の非 debug 射影が不正",
            detail_code="floor-dependency-archive-projection-invalid",
            origin="floor-dependency:masstree",
            outcome="identity-mismatch",
            path=path.parent,
        ) from exc


def _stat_floor_dependency_root(path: Path) -> os.stat_result:
    """依存 root の identity probe を単一の注入 site に束縛する。"""
    return path.stat()


def _verify_pristine_floor_dependency_sources(
        fetchcontent_base_dir: Path, *, repo_root: Path,
        source_names: tuple[str, ...] = _FLOOR_THIRD_PARTY_SOURCE_NAMES,
        tracked_only: bool = False,
        expected_pins: Optional[Mapping[str, str]] = None,
) -> dict[str, Path]:
    """CMake 前に staged 3依存の path・pin・clean 状態を検証する。"""
    if (type(source_names) is not tuple or not source_names
            or len(set(source_names)) != len(source_names)
            or any(name not in _FLOOR_THIRD_PARTY_SOURCE_NAMES
                   for name in source_names)
            or type(tracked_only) is not bool):
        raise ValueError("staged source status 検査 mode が不正")
    try:
        raw_base = Path(fetchcontent_base_dir)
        resolved_repo = Path(repo_root).resolve(strict=True)
        resolved_base = raw_base.resolve(strict=True)
    except (TypeError, ValueError, OSError, RuntimeError) as exc:
        raise _FloorOraclePreflightError(
            "staged FetchContent base を解決できない",
            detail_code="floor-dependency-staged-source-path-invalid",
            origin="floor-fetchcontent-staged-base",
            outcome="invalid-path",
            path=_preflight_candidate_path(fetchcontent_base_dir),
        ) from exc
    if (not raw_base.is_absolute() or raw_base.is_symlink()
            or not resolved_base.is_dir() or raw_base.absolute() != resolved_base):
        raise _FloorOraclePreflightError(
            "staged FetchContent base が canonical absolute directory でない",
            detail_code="floor-dependency-staged-source-not-directory",
            origin="floor-fetchcontent-staged-base",
            outcome="not-regular-file",
            path=raw_base,
        )
    try:
        if os.path.commonpath((str(resolved_base), str(resolved_repo))) == str(resolved_repo):
            raise _FloorOraclePreflightError(
                "staged FetchContent base は repo 外でなければならない",
                detail_code="floor-dependency-staged-source-inside-repository",
                origin="floor-fetchcontent-staged-base",
                outcome="invalid-path",
                path=resolved_base,
            )
    except ValueError as exc:
        raise _FloorOraclePreflightError(
            "staged FetchContent base の repo 境界を比較できない",
            detail_code="floor-dependency-staged-source-path-invalid",
            origin="floor-fetchcontent-staged-base",
            outcome="invalid-path",
            path=resolved_base,
        ) from exc

    if expected_pins is None:
        pins = _floor_third_party_policy_pins(Path(repo_root))
    else:
        if (not isinstance(expected_pins, Mapping)
                or set(expected_pins) != set(source_names)):
            raise ValueError("captured staged source pin 集合が不正")
        pins = dict(expected_pins)
        if any(
                type(pin) is not str
                or re.fullmatch(r"[0-9a-f]{40}", pin) is None
                for pin in pins.values()):
            raise ValueError("captured staged source pin が不正")
    verified: dict[str, Path] = {}
    for name in source_names:
        unresolved_source = resolved_base / f"{name}-src"
        try:
            source_root = unresolved_source.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise _FloorOraclePreflightError(
                f"staged {name} source root が存在しない",
                detail_code="floor-dependency-staged-source-not-directory",
                origin=f"floor-dependency:{name}",
                outcome="missing",
                path=unresolved_source,
            ) from exc
        if (not unresolved_source.is_absolute()
                or unresolved_source.is_symlink()
                or not source_root.is_dir()
                or unresolved_source.absolute() != source_root):
            raise _FloorOraclePreflightError(
                f"staged {name} source root が実 non-symlink directory でない",
                detail_code="floor-dependency-staged-source-not-directory",
                origin=f"floor-dependency:{name}",
                outcome="not-regular-file",
                path=unresolved_source,
            )
        try:
            if os.path.commonpath((str(source_root), str(resolved_repo))) == str(resolved_repo):
                raise _FloorOraclePreflightError(
                    f"staged {name} source root は repo 外でなければならない",
                    detail_code="floor-dependency-staged-source-inside-repository",
                    origin=f"floor-dependency:{name}",
                    outcome="invalid-path",
                    path=source_root,
                )
        except ValueError as exc:
            raise _FloorOraclePreflightError(
                f"staged {name} source root の repo 境界を比較できない",
                detail_code="floor-dependency-staged-source-path-invalid",
                origin=f"floor-dependency:{name}",
                outcome="invalid-path",
                path=source_root,
            ) from exc

        try:
            head_probe = subprocess.run(
                [
                    "git", "-c", "core.fsmonitor=", "-c", "core.hooksPath=",
                    "-c", "core.useReplaceRefs=false", "-C", str(source_root), "rev-parse",
                    "--show-toplevel", "--verify", "HEAD",
                ],
                env=_floor_git_environment(),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise _FloorOraclePreflightError(
                f"staged {name} source HEAD を検査できない",
                detail_code="floor-dependency-staged-head-probe-unavailable",
                origin=f"floor-dependency:{name}",
                outcome="invalid-path",
                path=source_root,
            ) from exc
        if type(head_probe.stdout) is not str:
            raise _FloorOraclePreflightError(
                f"staged {name} source HEAD の出力が不正",
                detail_code="floor-dependency-staged-head-probe-unavailable",
                origin=f"floor-dependency:{name}",
                outcome="invalid-path",
                path=source_root,
            )
        lines = head_probe.stdout.splitlines()
        if head_probe.returncode != 0 or len(lines) != 2:
            raise _FloorOraclePreflightError(
                f"staged {name} source HEAD を一意に解決できない",
                detail_code="floor-dependency-staged-head-nonunique",
                origin=f"floor-dependency:{name}",
                outcome="invalid-path",
                path=source_root,
            )
        try:
            top_level = Path(lines[0]).resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise _FloorOraclePreflightError(
                f"staged {name} Git top-level を解決できない",
                detail_code="floor-dependency-staged-git-root-unavailable",
                origin=f"floor-dependency:{name}",
                outcome="invalid-path",
                path=source_root,
            ) from exc
        observed_head = lines[1]
        if top_level != source_root:
            raise _FloorOraclePreflightError(
                f"staged {name} source root が Git top-level でない",
                detail_code="floor-dependency-staged-git-root-mismatch",
                origin=f"floor-dependency:{name}",
                outcome="invalid-path",
                path=source_root,
            )
        if observed_head != pins[name]:
            raise _FloorOraclePreflightError(
                f"staged {name} source HEAD が共有 policy pin と不一致",
                detail_code="floor-dependency-staged-head-mismatch",
                origin=f"floor-dependency:{name}",
                outcome="identity-mismatch",
                path=source_root,
            )

        try:
            status_argv = [
                "git", "-c", "core.fsmonitor=", "-c", "core.hooksPath=",
                "-c", "core.useReplaceRefs=false", "-C", str(source_root),
                "status", "--porcelain=v1",
                "--untracked-files=no" if tracked_only else "--untracked-files=all",
                "--ignore-submodules=none",
            ]
            if not tracked_only:
                status_argv.append("--ignored=matching")
            status = subprocess.run(
                status_argv,
                env=_floor_git_environment(),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise _FloorOraclePreflightError(
                f"staged {name} source status を検査できない",
                detail_code="floor-dependency-staged-source-status-unavailable",
                origin=f"floor-dependency:{name}",
                outcome="invalid-path",
                path=source_root,
            ) from exc
        if status.returncode != 0 or type(status.stdout) is not str:
            raise _FloorOraclePreflightError(
                f"staged {name} source status を検査できない",
                detail_code="floor-dependency-staged-source-status-unavailable",
                origin=f"floor-dependency:{name}",
                outcome="invalid-path",
                path=source_root,
            )
        if status.stdout:
            raise _FloorOraclePreflightError(
                f"staged {name} source が clean でない",
                detail_code="floor-dependency-staged-source-dirty",
                origin=f"floor-dependency:{name}",
                outcome="identity-mismatch",
                path=source_root,
            )
        verified[name] = source_root
    return verified


def _verify_floor_oracle_dependency_source(
        fetchcontent_base_dir: Path, *, repo_root: Path,
        expected_head: str,
        expected_toolchain_manifest_sha256: str,
        require_tracked_clean: bool = False,
) -> _FloorOracleDependencyBinding:
    if (type(expected_head) is not str
            or re.fullmatch(r"[0-9a-f]{40}", expected_head) is None):
        raise _FloorOraclePreflightError(
            "共有 policy の masstree pin が不正",
            detail_code="floor-dependency-policy-pin-invalid",
            origin="shared-policy:masstree",
            outcome="invalid-path",
            path=_silo_ladder.third_party_policy_path(Path(repo_root)),
        )
    try:
        raw_cache = Path(fetchcontent_base_dir)
    except (TypeError, ValueError) as exc:
        raise _FloorOraclePreflightError(
            "FetchContent base が path として不正",
            detail_code="floor-dependency-base-path-invalid",
            origin="floor-fetchcontent-base",
            outcome="invalid-path",
        ) from exc
    if not raw_cache.is_absolute():
        raise _FloorOraclePreflightError(
            "FetchContent base は絶対 path 必須",
            detail_code="floor-dependency-base-path-invalid",
            origin="floor-fetchcontent-base",
            outcome="invalid-path",
            path=raw_cache,
        )
    try:
        resolved_repo = Path(repo_root).resolve(strict=True)
        resolved_cache = raw_cache.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise _FloorOraclePreflightError(
            "FetchContent base を解決できない",
            detail_code="floor-dependency-base-unavailable",
            origin="floor-fetchcontent-base",
            outcome="missing" if not raw_cache.exists() else "invalid-path",
            path=raw_cache,
        ) from exc
    if raw_cache.is_symlink() or not resolved_cache.is_dir():
        raise _FloorOraclePreflightError(
            "FetchContent base が実 directory でない",
            detail_code="floor-dependency-base-not-directory",
            origin="floor-fetchcontent-base",
            outcome="not-regular-file",
            path=raw_cache,
        )
    try:
        inside_repo = os.path.commonpath((
            str(resolved_cache), str(resolved_repo),
        )) == str(resolved_repo)
    except ValueError as exc:
        raise _FloorOraclePreflightError(
            "FetchContent base の境界を比較できない",
            detail_code="floor-dependency-base-boundary-unavailable",
            origin="floor-fetchcontent-base",
            outcome="invalid-path",
            path=raw_cache,
        ) from exc
    if inside_repo:
        raise _FloorOraclePreflightError(
            "FetchContent base は repo 外でなければならない",
            detail_code="floor-dependency-base-inside-repository",
            origin="floor-fetchcontent-base",
            outcome="invalid-path",
            path=raw_cache,
        )

    unresolved_source = resolved_cache / "masstree-src"
    try:
        source_root = unresolved_source.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise _FloorOraclePreflightError(
            "masstree source root が存在しない",
            detail_code="floor-dependency-source-missing",
            origin="floor-dependency:masstree",
            outcome="missing",
            path=unresolved_source,
        ) from exc
    if unresolved_source.is_symlink() or not source_root.is_dir():
        raise _FloorOraclePreflightError(
            "masstree source root が実 directory でない",
            detail_code="floor-dependency-source-not-directory",
            origin="floor-dependency:masstree",
            outcome="not-regular-file",
            path=unresolved_source,
        )
    try:
        completed = subprocess.run(
            [
                "git", "-c", "core.fsmonitor=", "-c", "core.hooksPath=",
                "-c", "core.useReplaceRefs=false", "-C", str(source_root),
                "rev-parse", "--show-toplevel", "--verify", "HEAD",
            ],
            env=_floor_git_environment(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise _FloorOraclePreflightError(
            "masstree source HEAD を検査できない",
            detail_code="floor-dependency-head-probe-unavailable",
            origin="floor-dependency:masstree",
            outcome="invalid-path",
            path=source_root,
        ) from exc
    lines = completed.stdout.splitlines()
    if completed.returncode != 0 or len(lines) != 2:
        raise _FloorOraclePreflightError(
            "masstree source HEAD を一意に解決できない",
            detail_code="floor-dependency-head-nonunique",
            origin="floor-dependency:masstree",
            outcome="invalid-path",
            path=source_root,
        )
    try:
        top_level = Path(lines[0]).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise _FloorOraclePreflightError(
            "masstree Git top-level を解決できない",
            detail_code="floor-dependency-git-root-unavailable",
            origin="floor-dependency:masstree",
            outcome="invalid-path",
            path=source_root,
        ) from exc
    observed_head = lines[1]
    if top_level != source_root:
        raise _FloorOraclePreflightError(
            "masstree source root が Git top-level でない",
            detail_code="floor-dependency-git-root-mismatch",
            origin="floor-dependency:masstree",
            outcome="invalid-path",
            path=source_root,
        )
    if observed_head != expected_head:
        raise _FloorOraclePreflightError(
            "masstree source HEAD が共有 policy pin と不一致",
            detail_code="floor-dependency-head-mismatch",
            origin="floor-dependency:masstree",
            outcome="invalid-path",
            path=source_root,
        )
    try:
        source_info = _stat_floor_dependency_root(source_root)
    except OSError as exc:
        raise _FloorOraclePreflightError(
            "masstree source root の identity を取得できない",
            detail_code="floor-dependency-source-stat-unavailable",
            origin="floor-dependency:masstree",
            outcome="missing",
            path=source_root,
        ) from exc
    if require_tracked_clean:
        _verify_floor_tracked_source_unchanged(
            source_root, repo_root=Path(repo_root),
            expected_head=expected_head,
        )
    if (type(expected_toolchain_manifest_sha256) is not str
            or re.fullmatch(
                r"[0-9a-f]{64}", expected_toolchain_manifest_sha256,
            ) is None):
        raise _FloorOraclePreflightError(
            "expected floor toolchain manifest hash が不正",
            detail_code="floor-dependency-postflight-toolchain-hash-mismatch",
            origin="floor-dependency-postflight:toolchain",
            outcome="identity-mismatch",
            path=source_root,
        )
    config_sha256 = _sha256_regular_file(source_root / "config.h")
    archive_digests = _verify_masstree_archive(
        source_root / "libkohler_masstree_json.a"
    )
    return _FloorOracleDependencyBinding(
        source_root=source_root,
        expected_head=expected_head,
        observed_head=observed_head,
        config_sha256=config_sha256,
        archive_sha256=archive_digests.raw_sha256,
        archive_nondebug_sha256=(
            archive_digests.archive_nondebug_sha256
        ),
        expected_toolchain_manifest_sha256=(
            expected_toolchain_manifest_sha256
        ),
        source_st_dev=source_info.st_dev,
        source_st_ino=source_info.st_ino,
    )


def _canonical_floor_fetchcontent_base(
        configured: Optional[os.PathLike[str] | str], *, repo_root: Path = ROOT,
) -> Path:
    """明示 seam または production TMPDIR から job-local base を一つ確定する。"""
    if configured is None:
        tmpdir = os.environ.get("TMPDIR")
        if not tmpdir:
            raise _FloorOraclePreflightError(
                "production floor の TMPDIR が未設定",
                detail_code="floor-dependency-tmpdir-unconfigured",
                origin="environment:TMPDIR",
                outcome="not-configured",
            )
        try:
            unresolved_tmp = Path(tmpdir)
        except (TypeError, ValueError) as exc:
            raise _FloorOraclePreflightError(
                "production floor の TMPDIR が path として不正",
                detail_code="floor-dependency-base-path-invalid",
                origin="environment:TMPDIR",
                outcome="invalid-path",
            ) from exc
        try:
            tmp_root = unresolved_tmp.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise _FloorOraclePreflightError(
                "production floor の TMPDIR を解決できない",
                detail_code="floor-dependency-base-unavailable",
                origin="environment:TMPDIR",
                outcome="missing",
                path=unresolved_tmp,
            ) from exc
        if (not unresolved_tmp.is_absolute() or unresolved_tmp.is_symlink()
                or not tmp_root.is_dir()):
            raise _FloorOraclePreflightError(
                "production floor の TMPDIR が実 absolute directory でない",
                detail_code="floor-dependency-base-not-directory",
                origin="environment:TMPDIR",
                outcome="not-regular-file",
                path=unresolved_tmp,
            )
        try:
            configured = tempfile.mkdtemp(
                prefix="izanagi-floor-fetchcontent-", dir=str(tmp_root),
            )
        except OSError as exc:
            raise _FloorOraclePreflightError(
                "job-local FetchContent base を作成できない",
                detail_code="floor-dependency-base-create-failed",
                origin="environment:TMPDIR",
                outcome="execution-failed",
                path=tmp_root,
            ) from exc
    try:
        unresolved = Path(configured)
        resolved = unresolved.resolve(strict=True)
        resolved_repo = Path(repo_root).resolve(strict=True)
    except (TypeError, ValueError, OSError, RuntimeError) as exc:
        raise _FloorOraclePreflightError(
            "FetchContent base を解決できない",
            detail_code="floor-dependency-base-unavailable",
            origin="floor-fetchcontent-base",
            outcome="invalid-path",
            path=_preflight_candidate_path(configured),
        ) from exc
    if (not unresolved.is_absolute() or unresolved.is_symlink()
            or not resolved.is_dir() or unresolved.absolute() != resolved):
        raise _FloorOraclePreflightError(
            "FetchContent base が canonical non-symlink absolute directory でない",
            detail_code="floor-dependency-base-not-directory",
            origin="floor-fetchcontent-base",
            outcome="not-regular-file",
            path=unresolved,
        )
    try:
        resolved_info = _stat_floor_dependency_root(resolved)
    except OSError as exc:
        raise _FloorOraclePreflightError(
            "FetchContent base の identity を取得できない",
            detail_code="floor-dependency-base-unavailable",
            origin="floor-fetchcontent-base",
            outcome="missing",
            path=resolved,
        ) from exc
    try:
        if resolved_info.st_uid != os.geteuid():
            raise _FloorOraclePreflightError(
                "FetchContent base の owner が実効 uid と不一致",
                detail_code="floor-dependency-base-owner-mismatch",
                origin="floor-fetchcontent-base",
                outcome="invalid-path",
                path=resolved,
            )
        inside_repo = os.path.commonpath((str(resolved), str(resolved_repo))) == str(resolved_repo)
    except ValueError as exc:
        raise _FloorOraclePreflightError(
            "FetchContent base の repo 境界を比較できない",
            detail_code="floor-dependency-base-boundary-unavailable",
            origin="floor-fetchcontent-base",
            outcome="invalid-path",
            path=resolved,
        ) from exc
    if inside_repo:
        raise _FloorOraclePreflightError(
            "FetchContent base は repo 外でなければならない",
            detail_code="floor-dependency-base-inside-repository",
            origin="floor-fetchcontent-base",
            outcome="invalid-path",
            path=resolved,
        )
    return resolved


def _require_floor_payload_directory_components(
        repo_root: Path, target: Path, *, origin: str,
) -> None:
    """固定 submission prefix から target までを no-follow で検査する。"""
    try:
        relative = target.relative_to(repo_root)
    except ValueError as exc:
        raise _FloorOraclePreflightError(
            "floor submission payload が canonical repo root 外",
            detail_code="floor-dependency-staged-source-path-invalid",
            origin=origin,
            outcome="invalid-path",
            path=target,
        ) from exc
    current = repo_root
    for component in relative.parts:
        current /= component
        try:
            info = current.lstat()
        except OSError as exc:
            raise _FloorOraclePreflightError(
                "floor submission payload の固定 path component が存在しない",
                detail_code="floor-dependency-staged-source-not-directory",
                origin=origin,
                outcome="missing",
                path=current,
            ) from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise _FloorOraclePreflightError(
                "floor submission payload の固定 path component が実 directory でない",
                detail_code="floor-dependency-staged-source-not-directory",
                origin=origin,
                outcome="not-regular-file",
                path=current,
            )


def _stage_default_floor_fetchcontent_payload(
        *, repo_root: Path, contract,
        reservation_binding: Optional[reservation.ReservationBinding],
) -> Path:
    """検証済み reservation に束縛された payload を固定 scratch へ複製する。"""
    if not isinstance(reservation_binding, reservation.ReservationBinding):
        raise _FloorOraclePreflightError(
            "default floor transport に検証済み reservation binding がない",
            detail_code="floor-dependency-base-unavailable",
            origin="reservation-binding:floor-fetchcontent",
            outcome="not-configured",
        )
    try:
        canonical_repo = Path(repo_root).resolve(strict=True)
        receipt = floor_submit_receipt.receipt_path(
            canonical_repo,
            env_tag=contract.env_tag,
            nonce=reservation_binding.nonce,
        )
    except (AttributeError, TypeError, OSError, RuntimeError,
            floor_submit_receipt.FloorSubmitReceiptError) as exc:
        raise _FloorOraclePreflightError(
            "default floor transport の submission payload path が不正",
            detail_code="floor-dependency-staged-source-path-invalid",
            origin="reservation-binding:floor-fetchcontent",
            outcome="invalid-path",
            path=_preflight_candidate_path(repo_root),
        ) from exc
    payload_root = receipt.parent / _FLOOR_SUBMISSION_PAYLOAD_LEAF
    _require_floor_payload_directory_components(
        canonical_repo, payload_root,
        origin="floor-submission-payload:root",
    )
    sources = {
        name: payload_root / f"{name}-src"
        for name in _FLOOR_THIRD_PARTY_SOURCE_NAMES
    }
    for name, source in sources.items():
        _require_floor_payload_directory_components(
            canonical_repo, source,
            origin=f"floor-submission-payload:{name}",
        )

    tmpdir = os.environ.get("TMPDIR")
    if not tmpdir:
        raise _FloorOraclePreflightError(
            "production floor の TMPDIR が未設定",
            detail_code="floor-dependency-tmpdir-unconfigured",
            origin="environment:TMPDIR",
            outcome="not-configured",
        )
    try:
        unresolved_tmp = Path(tmpdir)
        tmp_root = unresolved_tmp.resolve(strict=True)
    except (TypeError, ValueError, OSError, RuntimeError) as exc:
        raise _FloorOraclePreflightError(
            "production floor の TMPDIR を解決できない",
            detail_code="floor-dependency-base-unavailable",
            origin="environment:TMPDIR",
            outcome="missing",
            path=_preflight_candidate_path(tmpdir),
        ) from exc
    if (not unresolved_tmp.is_absolute() or unresolved_tmp.is_symlink()
            or not tmp_root.is_dir()):
        raise _FloorOraclePreflightError(
            "production floor の TMPDIR が実 absolute directory でない",
            detail_code="floor-dependency-base-not-directory",
            origin="environment:TMPDIR",
            outcome="not-regular-file",
            path=unresolved_tmp,
        )
    destination = tmp_root / _FLOOR_FETCHCONTENT_STAGING_LEAF
    try:
        if os.path.commonpath(
                (str(destination), str(canonical_repo))) == str(canonical_repo):
            raise _FloorOraclePreflightError(
                "default FetchContent staging は repo 外でなければならない",
                detail_code="floor-dependency-base-inside-repository",
                origin="floor-fetchcontent-staging:destination",
                outcome="invalid-path",
                path=destination,
            )
    except ValueError as exc:
        raise _FloorOraclePreflightError(
            "default FetchContent staging の repo 境界を比較できない",
            detail_code="floor-dependency-base-boundary-unavailable",
            origin="floor-fetchcontent-staging:destination",
            outcome="invalid-path",
            path=destination,
        ) from exc
    if os.path.lexists(destination):
        raise _FloorOraclePreflightError(
            "default FetchContent staging destination が既に存在する",
            detail_code="floor-dependency-base-create-failed",
            origin="floor-fetchcontent-staging:destination",
            outcome="execution-failed",
            path=destination,
        )
    try:
        destination.mkdir(mode=0o700)
    except OSError as exc:
        raise _FloorOraclePreflightError(
            "default FetchContent staging destination を排他作成できない",
            detail_code="floor-dependency-base-create-failed",
            origin="floor-fetchcontent-staging:destination",
            outcome="execution-failed",
            path=destination,
        ) from exc
    try:
        for name, source in sources.items():
            copied = destination / f"{name}-src"
            shutil.copytree(
                source, copied, symlinks=True, copy_function=shutil.copy2,
            )
            copied_info = copied.lstat()
            if stat.S_ISLNK(copied_info.st_mode) or not stat.S_ISDIR(
                    copied_info.st_mode):
                raise OSError("copied source root is not a real directory")
    except (OSError, shutil.Error) as exc:
        raise _FloorOraclePreflightError(
            "floor submission payload を staging destination へ複製できない",
            detail_code="floor-dependency-base-create-failed",
            origin="floor-fetchcontent-staging:copy",
            outcome="execution-failed",
            path=destination,
        ) from exc
    return _canonical_floor_fetchcontent_base(
        destination, repo_root=canonical_repo,
    )


def _materialize_floor_oracle_dependency(
        binding: _FloorOracleDependencyBinding, *, lease_parent: Path,
) -> tuple[
        _FloorOracleDependencyBinding,
        _sort_swo_dependency_material.CanonicalDependencyMaterial,
]:
    try:
        material = (
            _sort_swo_dependency_material.materialize_canonical_dependency(
                binding.source_root,
                lease_parent=lease_parent,
                expected_head=binding.observed_head,
            )
        )
    except _sort_swo_dependency_material.CanonicalDependencyMaterialError as exc:
        detail_map = {
            "canonical-tracked-list-unavailable": (
                "floor-dependency-canonical-tracked-list-unavailable",
                "floor-dependency-canonical:git-ls-files",
                "execution-failed",
            ),
            "canonical-tracked-list-invalid": (
                "floor-dependency-canonical-tracked-list-invalid",
                "floor-dependency-canonical:git-ls-files",
                "identity-mismatch",
            ),
            "canonical-root-create-failed": (
                "floor-dependency-canonical-root-create-failed",
                "floor-dependency-canonical:materialize",
                "execution-failed",
            ),
            "canonical-copy-failed": (
                "floor-dependency-canonical-copy-failed",
                "floor-dependency-canonical:masstree",
                "execution-failed",
            ),
            "canonical-manifest-mismatch": (
                "floor-dependency-canonical-manifest-mismatch",
                "floor-dependency-canonical:manifest",
                "identity-mismatch",
            ),
            "canonical-verification-failed": (
                "floor-dependency-canonical-verification-failed",
                "floor-dependency-canonical:root",
                "identity-mismatch",
            ),
        }
        detail_code, origin, outcome = detail_map.get(
            exc.detail_code,
            (
                "floor-dependency-canonical-source-drift",
                "floor-dependency-canonical:masstree",
                "identity-mismatch",
            ),
        )
        raise _FloorOraclePreflightError(
            str(exc), detail_code=detail_code, origin=origin,
            outcome=outcome, path=exc.path,
            generated_manifest_sha256=exc.generated_manifest_sha256,
            expected_manifest_sha256=exc.expected_manifest_sha256,
        ) from exc
    return replace(
        binding,
        oracle_root=material.root,
        canonical_lease_root=material.lease_root,
        dependency_manifest_sha256=material.manifest_sha256,
    ), material


def _bind_expected_floor_masstree_payload(
        binding: _FloorOracleDependencyBinding,
        expected_payload: _LoadedFloorMasstreePayloadPolicy,
) -> _FloorOracleDependencyBinding:
    """Materialization 前に独立 policy の config/archive 述語を閉じる。"""
    if binding.config_sha256 != expected_payload.config_sha256:
        raise _FloorOraclePreflightError(
            "masstree config.h が独立 expected hash と不一致",
            detail_code="floor-dependency-config-expected-mismatch",
            origin="floor-payload-policy:masstree",
            outcome="identity-mismatch",
            path=binding.source_root / "config.h",
        )
    if (binding.archive_nondebug_sha256
            != expected_payload.archive_nondebug_sha256):
        raise _FloorOraclePreflightError(
            "masstree archive の非 debug 射影が独立 expected hash と不一致",
            detail_code="floor-dependency-archive-expected-mismatch",
            origin="floor-payload-policy:masstree",
            outcome="identity-mismatch",
            path=binding.source_root / "libkohler_masstree_json.a",
        )
    return replace(
        binding,
        expected_config_sha256=expected_payload.config_sha256,
        expected_archive_nondebug_sha256=(
            expected_payload.archive_nondebug_sha256
        ),
        payload_policy_sha256=expected_payload.raw_sha256,
        payload_policy_pin=expected_payload.pin,
    )


def _prepare_floor_oracle_dependency(
        fetchcontent_base: Path, *, ccbench_pin: str,
        expected_toolchain_manifest: Mapping[str, object], repo_root: Path = ROOT,
        _material_sink: Optional[list[
            _sort_swo_dependency_material.CanonicalDependencyMaterial
        ]] = None,
) -> _FloorOracleDependencyBinding:
    """staged source-dir transport を検証して oracle identity を取得する。"""
    captured_policy_pins = _floor_third_party_policy_pins(Path(repo_root))
    expected_payload: Optional[_LoadedFloorMasstreePayloadPolicy] = None
    payload_policy_error: Optional[_FloorOraclePreflightError] = None
    try:
        expected_payload = _load_floor_masstree_payload_policy(
            Path(repo_root),
            expected_masstree_pin=captured_policy_pins["masstree"],
        )
    except _FloorOraclePreflightError as exc:
        # policy は一度だけ捕捉するが、より具体的な checkout/prebuild/source
        # 診断がある場合はそちらを先に確定する。いずれも無ければ
        # materialization 前に保留した policy 診断で fail-closed にする。
        payload_policy_error = exc
    try:
        expected_toolchain_manifest_sha256 = _floor_toolchain_manifest_sha256(
            expected_toolchain_manifest,
        )
    except ValueError as exc:
        raise _FloorOraclePreflightError(
            "expected floor toolchain manifest が canonical JSON でない",
            detail_code="floor-toolchain-manifest-invalid",
            origin="floor-toolchain:manifest",
            outcome="invalid-path",
        ) from exc
    effective_base = Path(fetchcontent_base)
    staged_sources = _verify_pristine_floor_dependency_sources(
        effective_base, repo_root=Path(repo_root),
        expected_pins=captured_policy_pins,
    )
    fixed_sub = Path(repo_root) / "external" / "ccbench"
    try:
        checkout = patchharness.checkout(ccbench_pin, base_dir=str(fixed_sub))
    except Exception as exc:
        raise _FloorOraclePreflightError(
            "pin 済み CCBench checkout を prebuild 用に作成できない",
            detail_code="floor-dependency-ccbench-checkout-failed",
            origin="floor-fetchcontent-prebuild:ccbench-checkout",
            outcome="execution-failed",
            path=fixed_sub,
        ) from exc
    try:
        with checkout as prebuild_source:
            try:
                prepare_kwargs = {
                    "ccbench_dir": str(Path(prebuild_source).resolve()),
                    "fetchcontent_base_dir": str(effective_base),
                    "expected_toolchain_manifest": expected_toolchain_manifest,
                    "configure_timeout_s": _FLOOR_DEPENDENCY_CONFIGURE_CAP_S,
                    "target_timeout_s": _FLOOR_DEPENDENCY_TARGET_CAP_S,
                }
                prepare_kwargs.update({
                    "masstree_source_dir": str(staged_sources["masstree"]),
                    "mimalloc_source_dir": str(staged_sources["mimalloc"]),
                    "googletest_source_dir": str(staged_sources["googletest"]),
                })
                buildcache.prepare_masstree_fetchcontent(**prepare_kwargs)
            except buildcache.MasstreeFetchContentError as exc:
                code = (
                    "floor-dependency-fetchcontent-configure-failed"
                    if exc.stage == "configure"
                    else "floor-dependency-fetchcontent-target-failed"
                )
                raise _FloorOraclePreflightError(
                    str(exc), detail_code=code,
                    origin=f"floor-fetchcontent-prebuild:{exc.stage}",
                    outcome="execution-failed", path=effective_base,
                ) from exc
            except Exception as exc:
                raise _FloorOraclePreflightError(
                    str(exc),
                    detail_code="floor-dependency-fetchcontent-base-failed",
                    origin="floor-fetchcontent-prebuild:base",
                    outcome="execution-failed",
                    path=effective_base,
                ) from exc
    except _FloorOraclePreflightError:
        raise
    except Exception as exc:
        raise _FloorOraclePreflightError(
            "pin 済み CCBench checkout を prebuild 用に作成できない",
            detail_code="floor-dependency-ccbench-checkout-failed",
            origin="floor-fetchcontent-prebuild:ccbench-checkout",
            outcome="execution-failed",
            path=fixed_sub,
        ) from exc
    binding = _verify_floor_oracle_dependency_source(
        effective_base, repo_root=Path(repo_root),
        expected_head=captured_policy_pins["masstree"],
        expected_toolchain_manifest_sha256=(
            expected_toolchain_manifest_sha256
        ),
    )
    if payload_policy_error is not None:
        raise payload_policy_error
    assert expected_payload is not None
    binding = _bind_expected_floor_masstree_payload(
        binding, expected_payload,
    )
    binding = replace(
        binding,
        captured_policy_pins=tuple(sorted(captured_policy_pins.items())),
    )
    binding = replace(
        binding,
        transport_mode="source-dir",
    )
    binding, material = _materialize_floor_oracle_dependency(
        binding, lease_parent=effective_base,
    )
    if _material_sink is not None:
        _material_sink.append(material)
    return binding


def _phase_marker_root(
        configured: Optional[os.PathLike[str] | str],
) -> Path:
    value = configured
    if value is None:
        value = os.environ.get(_FLOOR_JOB_STAGING_ENV)
    try:
        missing = value is None or os.fspath(value) == ""
    except (TypeError, ValueError) as exc:
        raise FloorCampaignError("floor job staging が path として不正") from exc
    if missing:
        raise FloorCampaignError(
            "floor job staging は明示引数または "
            f"{_FLOOR_JOB_STAGING_ENV} で必須"
        )
    try:
        unresolved = Path(value)
    except (TypeError, ValueError) as exc:
        raise FloorCampaignError("floor job staging が path として不正") from exc
    if not unresolved.is_absolute():
        raise FloorCampaignError("floor job staging は絶対 path 必須")
    try:
        resolved = unresolved.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise FloorCampaignError("floor job staging を解決できない") from exc
    if unresolved.is_symlink() or not resolved.is_dir():
        raise FloorCampaignError("floor job staging が実 directory でない")
    return resolved


def _create_private_json(path: Path, document: Mapping[str, object]) -> None:
    payload = (
        json.dumps(
            dict(document), ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ) + "\n"
    ).encode("utf-8")
    if len(payload) > _PRIVATE_DIAGNOSTIC_MAX_BYTES:
        raise FloorCampaignError("private job marker が byte 上限を超えた")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
        try:
            with os.fdopen(descriptor, "wb", closefd=False) as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        finally:
            os.close(descriptor)
        directory_flags = os.O_RDONLY
        if hasattr(os, "O_DIRECTORY"):
            directory_flags |= os.O_DIRECTORY
        directory_descriptor = os.open(path.parent, directory_flags)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except OSError as exc:
        raise FloorCampaignError("private job marker を create-only で保存できない") from exc


def _write_phase_marker(
        root: Path, *, cell: str, phase: str, compiler: str,
        dependency: Optional[_FloorOracleDependencyBinding]) -> Path:
    if phase not in {"preflight", "oracle", "build"}:
        raise FloorCampaignError("未知の floor phase marker")
    if type(cell) is not str or not cell or len(cell) > 512:
        raise FloorCampaignError("floor phase marker の cell が不正")
    cell_digest = hashlib.sha256(cell.encode("utf-8")).hexdigest()[:16]
    destination = root / f"phase-{phase}-{cell_digest}.json"
    document: dict[str, object] = {
        "cell": cell,
        "phase": phase,
        "pid": os.getpid(),
        "started": dt.datetime.now(dt.timezone.utc).isoformat(),
        "compiler": compiler,
    }
    if dependency is not None:
        document.update({
            "dependency_root": str(dependency.source_root),
            "dependency_head": dependency.observed_head,
            "dependency_expected_head": dependency.expected_head,
            "dependency_config_sha256": dependency.config_sha256,
            "dependency_archive_sha256": dependency.archive_sha256,
            "dependency_archive_nondebug_sha256": (
                dependency.archive_nondebug_sha256
            ),
            "dependency_toolchain_manifest_sha256": (
                dependency.expected_toolchain_manifest_sha256
            ),
            "dependency_source_st_dev": dependency.source_st_dev,
            "dependency_source_st_ino": dependency.source_st_ino,
        })
        if dependency.oracle_root is not None:
            document["oracle_dependency_root"] = str(dependency.oracle_root)
        if dependency.dependency_manifest_sha256 is not None:
            document["dependency_manifest_sha256"] = (
                dependency.dependency_manifest_sha256
            )
        if dependency.expected_archive_nondebug_sha256 is not None:
            document["dependency_expected_archive_nondebug_sha256"] = (
                dependency.expected_archive_nondebug_sha256
            )
    _create_private_json(destination, document)
    return destination


def _floor_oracle_preflight_unavailable_result(
        diagnostic: _FloorOraclePreflightDiagnostic, *,
        verified_compiler: Optional[str],
) -> SortSwoOracleResult:
    if diagnostic.outcome in {"execution-failed", "identity-mismatch"}:
        return SortSwoOracleResult(
            OracleStatus.UNAVAILABLE,
            _FLOOR_PREFLIGHT_MATERIALIZED_SHA256,
            _FLOOR_PREFLIGHT_PROPOSAL_SHA256,
            infrastructure=OracleInfrastructureFailure(
                INFRASTRUCTURE_REASON_CODE,
                diagnostic.phase,
                diagnostic.detail_code,
            ),
        )
    if diagnostic.failed_leg == "compiler":
        compiler_candidates = (
            OracleEnvironmentCandidate(
                diagnostic.origin, diagnostic.path, diagnostic.outcome,
            ),
        )
        dependency_candidates = (
            OracleEnvironmentCandidate(
                "floor-preflight:dependency-not-attempted",
                None,
                "not-configured",
            ),
        )
        resolution_detail = "oracle-environment-compiler-unresolved"
    else:
        compiler_path = (
            Path(verified_compiler)
            if type(verified_compiler) is str and verified_compiler else None
        )
        compiler_candidates = (
            OracleEnvironmentCandidate(
                "floor-toolchain:cxx",
                compiler_path,
                "selected" if compiler_path is not None else "not-configured",
            ),
        )
        dependency_candidates = (
            OracleEnvironmentCandidate(
                diagnostic.origin, diagnostic.path, diagnostic.outcome,
            ),
        )
        resolution_detail = "oracle-environment-dependency-unresolved"
    resolution = OracleEnvironmentResolutionFailure(
        resolution_detail,
        compiler_candidates,
        dependency_candidates,
    )
    return SortSwoOracleResult(
        OracleStatus.UNAVAILABLE,
        _FLOOR_PREFLIGHT_MATERIALIZED_SHA256,
        _FLOOR_PREFLIGHT_PROPOSAL_SHA256,
        infrastructure=OracleInfrastructureFailure(
            INFRASTRUCTURE_REASON_CODE,
            diagnostic.phase,
            diagnostic.detail_code,
            environment_resolution=resolution,
        ),
    )


def _persist_floor_oracle_preflight_failure(
        marker_root: Path, error: _FloorOraclePreflightError, *,
        verified_compiler: Optional[str],
) -> SortSwoOracleUnavailable:
    result = _floor_oracle_preflight_unavailable_result(
        error.diagnostic,
        verified_compiler=verified_compiler,
    )
    record = private_attempt_record(result)
    if error.diagnostic.outcome in {"execution-failed", "identity-mismatch"}:
        record["floor_failure_diagnostic"] = error.diagnostic.private_dict()
    _create_private_json(marker_root / _FLOOR_PREFLIGHT_FAILURE_FILENAME, record)
    return SortSwoOracleUnavailable(result)


def _persist_floor_oracle_postflight_failure(
        marker_root: Path, error: _FloorOraclePreflightError, *,
        verified_compiler: Optional[str],
        build_exception: Optional[_FloorBuildExceptionDiagnostic] = None,
) -> SortSwoOracleUnavailable:
    if error.diagnostic.detail_code not in _FLOOR_DEPENDENCY_POSTFLIGHT_DETAIL_CODES:
        raise ValueError("postflight 永続化へ preflight detail code を渡せない")
    result = _floor_oracle_preflight_unavailable_result(
        error.diagnostic,
        verified_compiler=verified_compiler,
    )
    record = private_attempt_record(result)
    diagnostic = error.diagnostic.private_dict()
    if build_exception is not None:
        if (error.diagnostic.detail_code
                != "floor-dependency-postflight-build-failed"
                or error.diagnostic.outcome != "execution-failed"):
            raise ValueError("build exception diagnostic の適用先が不正")
        diagnostic["build_exception"] = build_exception.private_dict()
    record["floor_failure_diagnostic"] = diagnostic
    _create_private_json(marker_root / _FLOOR_POSTFLIGHT_FAILURE_FILENAME, record)
    return SortSwoOracleUnavailable(result)


def _floor_postflight_error(
        message: str, *, detail_code: str, outcome: str,
        path: Optional[Path] = None,
) -> _FloorOraclePreflightError:
    return _FloorOraclePreflightError(
        message,
        detail_code=detail_code,
        origin="floor-dependency-postflight:masstree",
        outcome=outcome,
        path=path,
    )


def _verify_floor_tracked_source_unchanged(
        source_root: Path, *, repo_root: Path, expected_head: str,
) -> None:
    try:
        verified = _verify_pristine_floor_dependency_sources(
            source_root.parent, repo_root=Path(repo_root),
            source_names=("masstree",), tracked_only=True,
            expected_pins={"masstree": expected_head},
        )
    except _FloorOraclePreflightError as exc:
        if exc.diagnostic.detail_code == "floor-dependency-staged-source-dirty":
            raise _floor_postflight_error(
                "build 後に masstree tracked source が変化した",
                detail_code="floor-dependency-postflight-tracked-source-drift",
                outcome="identity-mismatch", path=source_root,
            ) from exc
        if exc.diagnostic.detail_code == "floor-dependency-staged-head-mismatch":
            raise _floor_postflight_error(
                "build 後に masstree HEAD が変化した",
                detail_code="floor-dependency-postflight-head-drift",
                outcome="identity-mismatch", path=source_root,
            ) from exc
        raise _floor_postflight_error(
            "build 後の masstree tracked source status を検査できない",
            detail_code="floor-dependency-postflight-source-unavailable",
            outcome="identity-mismatch", path=source_root,
        ) from exc
    if verified.get("masstree") != source_root:
        raise _floor_postflight_error(
            "build 後の masstree source root が binding と不一致",
            detail_code="floor-dependency-postflight-source-unavailable",
            outcome="identity-mismatch", path=source_root,
        )


def _verify_floor_build_dependency(
        result: object, configure_argv: tuple[str, ...] | list[str], *,
        fetchcontent_base: Path, before: _FloorOracleDependencyBinding,
        expected_toolchain_manifest: Mapping[str, object],
        repo_root: Path = ROOT,
        require_run_local_identity: bool = False,
) -> _FloorOracleDependencyBinding:
    """binary admission 前に build 成果物由来 root と依存内容を再照合する。"""
    if type(require_run_local_identity) is not bool:
        raise TypeError("require_run_local_identity は exact bool 必須")
    if getattr(result, "fetchcontent_base_dir", None) != str(fetchcontent_base):
        raise _floor_postflight_error(
            "build result の FetchContent base が期待値と不一致",
            detail_code="floor-dependency-postflight-result-base-mismatch",
            outcome="identity-mismatch", path=fetchcontent_base,
        )
    try:
        expected_toolchain_manifest_sha256 = _floor_toolchain_manifest_sha256(
            expected_toolchain_manifest,
        )
    except ValueError as exc:
        raise _floor_postflight_error(
            "calibration toolchain manifest を canonical JSON 化できない",
            detail_code="floor-dependency-postflight-toolchain-hash-mismatch",
            outcome="identity-mismatch", path=fetchcontent_base,
        ) from exc
    if (expected_toolchain_manifest_sha256
            != before.expected_toolchain_manifest_sha256):
        raise _floor_postflight_error(
            "calibration toolchain manifest hash が dependency binding と不一致",
            detail_code="floor-dependency-postflight-toolchain-hash-mismatch",
            outcome="identity-mismatch", path=fetchcontent_base,
        )
    result_toolchain_manifest = getattr(result, "toolchain_manifest", None)
    if (type(result_toolchain_manifest) is not dict
            or result_toolchain_manifest != expected_toolchain_manifest):
        raise _floor_postflight_error(
            "build result toolchain manifest が calibration と不一致",
            detail_code="floor-dependency-postflight-toolchain-manifest-mismatch",
            outcome="identity-mismatch", path=fetchcontent_base,
        )
    result_toolchain_manifest_sha256 = getattr(
        result, "toolchain_manifest_sha256", None,
    )
    try:
        canonical_result_toolchain_manifest_sha256 = (
            _floor_toolchain_manifest_sha256(result_toolchain_manifest)
        )
    except ValueError as exc:
        raise _floor_postflight_error(
            "build result toolchain manifest を canonical JSON 化できない",
            detail_code="floor-dependency-postflight-toolchain-hash-mismatch",
            outcome="identity-mismatch", path=fetchcontent_base,
        ) from exc
    if (canonical_result_toolchain_manifest_sha256
            != expected_toolchain_manifest_sha256
            or result_toolchain_manifest_sha256
            != expected_toolchain_manifest_sha256):
        raise _floor_postflight_error(
            "build result toolchain manifest hash が calibration/binding と不一致",
            detail_code="floor-dependency-postflight-toolchain-hash-mismatch",
            outcome="identity-mismatch", path=fetchcontent_base,
        )
    if (not isinstance(configure_argv, (list, tuple))
            or not configure_argv
            or any(type(token) is not str or not token for token in configure_argv)):
        raise _floor_postflight_error(
            "build configure argv が非空 str 列でない",
            detail_code="floor-dependency-postflight-configure-argv-invalid",
            outcome="identity-mismatch", path=fetchcontent_base,
        )
    source_defines = [
        token for token in configure_argv
        if token.startswith("-DFETCHCONTENT_SOURCE_DIR_")
    ]
    expected_source = fetchcontent_base / "masstree-src"
    if (require_run_local_identity
            and before.payload_policy_pin != before.expected_head):
        raise _floor_postflight_error(
            "captured payload policy pin が dependency binding と不一致",
            detail_code="floor-dependency-postflight-payload-policy-mismatch",
            outcome="identity-mismatch", path=expected_source,
        )
    if before.transport_mode == "source-dir":
        expected_source_defines = [
            f"-DFETCHCONTENT_SOURCE_DIR_{name.upper()}="
            f"{fetchcontent_base / f'{name}-src'}"
            for name in _FLOOR_THIRD_PARTY_SOURCE_NAMES
        ]
        if source_defines != expected_source_defines:
            raise _floor_postflight_error(
                "build configure argv の staged SOURCE_DIR 集合が不一致",
                detail_code="floor-dependency-postflight-source-set",
                outcome="identity-mismatch", path=fetchcontent_base,
            )
    elif source_defines:
        raise _floor_postflight_error(
            "build configure argv に禁止された FetchContent SOURCE_DIR override がある",
            detail_code="floor-dependency-postflight-source-override",
            outcome="identity-mismatch", path=fetchcontent_base,
        )
    expected_define = f"-DFETCHCONTENT_BASE_DIR={fetchcontent_base}"
    base_defines = [
        token for token in configure_argv
        if token.startswith("-DFETCHCONTENT_BASE_DIR=")
    ]
    if base_defines != [expected_define]:
        raise _floor_postflight_error(
            "build configure argv の FetchContent base define が exact 1 でない",
            detail_code="floor-dependency-postflight-base-define-count",
            outcome="identity-mismatch", path=fetchcontent_base,
        )
    expected_root_sha256 = hashlib.sha256(
        str(expected_source).encode("utf-8")
    ).hexdigest()
    if (getattr(result, "cached", None) is not True
            and getattr(result, "masstree_source_root_sha256", None)
            != expected_root_sha256):
        raise _floor_postflight_error(
            "build 成果物の実効 masstree source root が期待値と不一致",
            detail_code="floor-dependency-postflight-effective-root-mismatch",
            outcome="identity-mismatch", path=expected_source,
        )
    policy_path = _floor_masstree_payload_policy_path(Path(repo_root))
    try:
        current_payload_policy_sha256 = hashlib.sha256(
            policy_path.read_bytes()
        ).hexdigest()
    except OSError as exc:
        raise _floor_postflight_error(
            "独立 floor masstree payload policy の raw bytes を再読できない",
            detail_code="floor-dependency-postflight-source-unavailable",
            outcome="identity-mismatch", path=policy_path,
        ) from exc
    if (before.payload_policy_sha256 is None
            or current_payload_policy_sha256 != before.payload_policy_sha256):
        raise _floor_postflight_error(
            "build 後の floor masstree payload policy bytes が binding と不一致",
            detail_code="floor-dependency-postflight-payload-policy-mismatch",
            outcome="identity-mismatch", path=policy_path,
        )
    try:
        after = _verify_floor_oracle_dependency_source(
            fetchcontent_base, repo_root=repo_root,
            expected_head=before.expected_head,
            expected_toolchain_manifest_sha256=(
                before.expected_toolchain_manifest_sha256
            ),
            require_tracked_clean=True,
        )
    except _FloorOraclePreflightError as exc:
        if exc.diagnostic.detail_code == (
                "floor-dependency-postflight-tracked-source-drift"):
            raise
        detail_code = (
            "floor-dependency-postflight-head-drift"
            if exc.diagnostic.detail_code == "floor-dependency-head-mismatch"
            else "floor-dependency-postflight-source-unavailable"
        )
        raise _floor_postflight_error(
            "build 後の masstree dependency identity を再取得できない",
            detail_code=detail_code,
            outcome="identity-mismatch", path=expected_source,
        ) from exc
    if after.observed_head != before.observed_head:
        raise _floor_postflight_error(
            "build 後に masstree HEAD が変化した",
            detail_code="floor-dependency-postflight-head-drift",
            outcome="identity-mismatch", path=expected_source,
        )
    if (require_run_local_identity
            and (after.source_st_dev, after.source_st_ino)
            != (before.source_st_dev, before.source_st_ino)):
        raise _floor_postflight_error(
            "build 後に masstree source directory identity が変化した",
            detail_code="floor-dependency-postflight-source-identity-drift",
            outcome="identity-mismatch", path=expected_source,
        )
    if after.config_sha256 != before.config_sha256:
        raise _floor_postflight_error(
            "build 後に masstree config.h が変化した",
            detail_code="floor-dependency-postflight-config-drift",
            outcome="identity-mismatch", path=expected_source,
        )
    if (require_run_local_identity
            and after.archive_sha256 != before.archive_sha256):
        raise _floor_postflight_error(
            "build 後に masstree archive bytes が変化した",
            detail_code="floor-dependency-postflight-archive-drift",
            outcome="identity-mismatch", path=expected_source,
        )
    if require_run_local_identity:
        captured_pins = dict(before.captured_policy_pins)
        if (len(before.captured_policy_pins)
                != len(_FLOOR_THIRD_PARTY_SOURCE_NAMES)
                or set(captured_pins) != set(_FLOOR_THIRD_PARTY_SOURCE_NAMES)
                or any(
                    type(pin) is not str
                    or re.fullmatch(r"[0-9a-f]{40}", pin) is None
                    for pin in captured_pins.values()
                )
                or captured_pins.get("masstree") != before.expected_head):
            raise _floor_postflight_error(
                "captured shared policy pin 集合が dependency binding と不一致",
                detail_code="floor-dependency-postflight-source-unavailable",
                outcome="identity-mismatch", path=expected_source,
            )
    if require_run_local_identity:
        if (
            before.oracle_root is None
            or before.canonical_lease_root is None
            or before.dependency_manifest_sha256 is None
        ):
            raise _floor_postflight_error(
                "build 後の canonical dependency binding が欠落",
                detail_code="floor-dependency-postflight-canonical-drift",
                outcome="identity-mismatch", path=expected_source,
            )
        try:
            _sort_swo_dependency_material.assert_source_matches_canonical(
                expected_source,
                before.oracle_root,
                expected_head=before.observed_head,
                expected_manifest_sha256=before.dependency_manifest_sha256,
            )
        except _sort_swo_dependency_material.CanonicalDependencyMaterialError as exc:
            canonical_failure = exc.detail_code in {
                "canonical-verification-failed",
                "canonical-manifest-mismatch",
            }
            raise _floor_postflight_error(
                "build 後の canonical dependency 二根検査に失敗",
                detail_code=(
                    "floor-dependency-postflight-canonical-drift"
                    if canonical_failure
                    else "floor-dependency-postflight-canonical-source-drift"
                ),
                outcome="identity-mismatch", path=exc.path,
            ) from exc
    expected_config_sha256 = before.expected_config_sha256
    expected_archive_nondebug_sha256 = (
        before.expected_archive_nondebug_sha256
    )
    if (expected_config_sha256 is None
            or expected_archive_nondebug_sha256 is None):
        raise _floor_postflight_error(
            "独立 floor masstree payload policy binding が欠落",
            detail_code="floor-dependency-postflight-source-unavailable",
            outcome="identity-mismatch", path=expected_source,
        )
    if after.config_sha256 != expected_config_sha256:
        raise _floor_postflight_error(
            "build 後の masstree config.h が独立 expected hash と不一致",
            detail_code="floor-dependency-postflight-config-expected-mismatch",
            outcome="identity-mismatch", path=expected_source / "config.h",
        )
    if after.archive_nondebug_sha256 != expected_archive_nondebug_sha256:
        raise _floor_postflight_error(
            "build 後の masstree archive 非 debug 射影が独立 expected hash と不一致",
            detail_code=(
                "floor-dependency-postflight-archive-expected-mismatch"
            ),
            outcome="identity-mismatch",
            path=expected_source / "libkohler_masstree_json.a",
        )
    after = replace(
        after,
        oracle_root=before.oracle_root,
        canonical_lease_root=before.canonical_lease_root,
        dependency_manifest_sha256=before.dependency_manifest_sha256,
        transport_mode=before.transport_mode,
        expected_config_sha256=expected_config_sha256,
        expected_archive_nondebug_sha256=(
            expected_archive_nondebug_sha256
        ),
        payload_policy_sha256=before.payload_policy_sha256,
        payload_policy_pin=before.payload_policy_pin,
        captured_policy_pins=before.captured_policy_pins,
    )
    return after


@contextlib.contextmanager
def _prepared_binding(
        *, freeze: Mapping, holdout_id: str, configuration_id: str,
        ccbench_pin: str, cxx: str, prepare_fn):
    """共有 materializer の floor 境界 wrapper。identity 合成の MaterializationError だけを
    FloorCampaignError へ因果付き変換する。"""
    try:
        with prepared_binding(
                freeze=freeze, holdout_id=holdout_id,
                configuration_id=configuration_id, ccbench_pin=ccbench_pin, cxx=cxx,
                prepare_fn=prepare_fn) as (identity, prepared):
            yield identity, prepared
    except MaterializationError as exc:
        raise FloorCampaignError(str(exc)) from exc


@dataclass(frozen=True)
class _ObservedFloorTool:
    requested: str
    realpath: str
    version_first_line: str
    version: str

    def manifest_entry(self) -> dict[str, str]:
        return {
            "requested": self.requested,
            "realpath": self.realpath,
            "version_first_line": self.version_first_line,
            "version": self.version,
        }


def _observe_floor_tool(requested: str, role: str) -> _ObservedFloorTool:
    """Floor gate 用に実体と ``--version`` 全文を一度に観測する。"""
    origin = f"floor-toolchain:{role}"
    requested_path = _preflight_candidate_path(requested)
    try:
        found = shutil.which(requested)
    except (OSError, TypeError) as exc:
        raise _FloorOraclePreflightError(
            f"floor toolchain {role} の探索に失敗: {requested!r}: {exc}",
            detail_code="floor-toolchain-discovery-failed",
            origin=origin,
            outcome="invalid-path",
            path=requested_path,
        ) from exc
    if not found:
        raise _FloorOraclePreflightError(
            f"floor toolchain {role} が PATH に存在しない: {requested!r}",
            detail_code="floor-toolchain-tool-missing",
            origin=origin,
            outcome="not-found",
            path=requested_path,
        )
    realpath = os.path.realpath(found)
    if not os.path.isfile(realpath) or not os.access(realpath, os.X_OK):
        outcome = (
            "not-executable" if os.path.isfile(realpath)
            else "not-regular-file"
        )
        raise _FloorOraclePreflightError(
            f"floor toolchain {role} の実体が実行可能な通常ファイルでない: "
            f"{realpath!r}",
            detail_code="floor-toolchain-tool-not-executable-regular-file",
            origin=origin,
            outcome=outcome,
            path=Path(realpath),
        )
    try:
        result = subprocess.run(
            [realpath, "--version"], capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise _FloorOraclePreflightError(
            f"floor toolchain {role} --version を実行できない: {realpath}: {exc}",
            detail_code="floor-toolchain-version-launch-failed",
            origin=origin,
            outcome="invalid-path",
            path=Path(realpath),
        ) from exc
    lines = result.stdout.splitlines()
    version = (result.stdout + result.stderr).strip()
    if (result.returncode != 0 or not lines or not lines[0].strip()
            or not version):
        raise _FloorOraclePreflightError(
            f"floor toolchain {role} --version の取得に失敗 "
            f"(rc={result.returncode}): {realpath}",
            detail_code="floor-toolchain-version-invalid",
            origin=origin,
            outcome="invalid-path",
            path=Path(realpath),
        )
    return _ObservedFloorTool(
        requested=requested,
        realpath=realpath,
        version_first_line=lines[0],
        version=version,
    )


def _bind_current_toolchain(
        verified_calibration, *, cc: str, cxx: str,
) -> dict[str, dict[str, str]]:
    """Hash 検証済み calibration receipt と current toolchain を束縛する。"""
    if not isinstance(verified_calibration, env_attestation.VerifiedCalibration):
        raise _FloorOraclePreflightError(
            "floor toolchain binding に VerifiedCalibration が渡されていない",
            detail_code="floor-toolchain-receipt-type-invalid",
            origin="calibration:verified-receipt",
            outcome="invalid-path",
        )
    calibration = verified_calibration.calibration
    if calibration is None:
        if not toolchain_binding.floor_toolchain_matches(
            receipt_toolchain=None,
            receipt_build_argv=(),
            live_cc_realpath="",
            live_cxx_realpath="",
            live_cc_version="",
            live_cxx_version="",
            live_cmake_version="",
        ):
            raise _FloorOraclePreflightError(
                "floor toolchain binding に acquisition receipt がない",
                detail_code="floor-toolchain-receipt-missing",
                origin="calibration:acquisition-receipt",
                outcome="not-configured",
            )
        raise _FloorOraclePreflightError(
            "floor toolchain binding が receipt 不在を誤受理した",
            detail_code="floor-toolchain-receipt-state-invalid",
            origin="calibration:acquisition-receipt",
            outcome="invalid-path",
        )

    receipt = calibration.acquisition_receipt
    observed = {
        "cc": _observe_floor_tool(cc, "cc"),
        "cxx": _observe_floor_tool(cxx, "cxx"),
        "cmake": _observe_floor_tool("cmake", "cmake"),
    }
    receipt_toolchain = {
        "compiler_path": receipt.toolchain.compiler_path,
        "compiler_version": receipt.toolchain.compiler_version,
        "cmake_version": receipt.toolchain.cmake_version,
    }
    if not toolchain_binding.floor_toolchain_matches(
            receipt_toolchain=receipt_toolchain,
            receipt_build_argv=receipt.ccbench.build_argv,
            live_cc_realpath=observed["cc"].realpath,
            live_cxx_realpath=observed["cxx"].realpath,
            live_cc_version=observed["cc"].version,
            live_cxx_version=observed["cxx"].version,
            live_cmake_version=observed["cmake"].version):
        raise _FloorOraclePreflightError(
            "floor toolchain が registered calibration receipt と不一致",
            detail_code="floor-toolchain-receipt-mismatch",
            origin="calibration:toolchain-binding",
            outcome="invalid-path",
            path=Path(observed["cxx"].realpath),
        )
    return {
        role: observation.manifest_entry()
        for role, observation in observed.items()
    }


def _build_cells_impl(
        freeze: Mapping, cells: list[dict], *, ccbench_pin: str,
        out_root: Path, prepare_fn, contract, verified_calibration,
        build_fn=None,
        _invoke_build,
        fetchcontent_base_dir: Optional[os.PathLike[str] | str] = None,
        phase_marker_root: Optional[os.PathLike[str] | str] = None,
        repo_root: Path = ROOT,
        reservation_binding: Optional[reservation.ReservationBinding] = None,
        _canonical_material_sink: list[
            _sort_swo_dependency_material.CanonicalDependencyMaterial
        ],
) -> dict[str, dict]:
    """全セルを実体化し、runner/store 専用の absolute-path runtime view を返す。"""
    build_fn = build_fn or buildcache.build_v2
    # Human-reviewed admission では generator id は persistent receipt に入らない。API が要求する
    # run context の registered member として、S8b の直前 producer である S8a を選ぶ。
    build_context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    cache_root = str(out_root / "s8b-build-cache")
    production_floor_path = prepare_fn is prepare_cell
    marker_configured = (
        phase_marker_root is not None
        or os.environ.get(_FLOOR_JOB_STAGING_ENV) is not None
    )
    marker_root = (
        _phase_marker_root(phase_marker_root)
        if production_floor_path or marker_configured else None
    )
    try:
        cc, cxx = buildcache.compilers_for_current_site()
    except Exception as exc:
        preflight_error = _FloorOraclePreflightError(
            "floor toolchain の site compiler 選択に失敗",
            detail_code="floor-toolchain-discovery-failed",
            origin="floor-toolchain:site-selection",
            outcome="invalid-path",
        )
        if production_floor_path:
            assert marker_root is not None
            raise _persist_floor_oracle_preflight_failure(
                marker_root,
                preflight_error,
                verified_compiler=None,
            ) from exc
        raise preflight_error from exc
    if production_floor_path:
        assert marker_root is not None
        for cell in cells:
            _write_phase_marker(
                marker_root,
                cell=cell["cell_id"],
                phase="preflight",
                compiler=cxx,
                dependency=None,
            )

    dependency_binding = None
    fetchcontent_base = None
    verified_oracle_compiler = None
    try:
        expected_toolchain_manifest = _bind_current_toolchain(
            verified_calibration, cc=cc, cxx=cxx,
        )
        if production_floor_path and any(
                cell.get("configuration_id") == "sort_best" for cell in cells):
            try:
                verified_oracle_compiler = expected_toolchain_manifest[
                    "cxx"
                ]["realpath"]
            except (KeyError, TypeError) as exc:
                raise _FloorOraclePreflightError(
                    "検証済み floor cxx realpath が toolchain manifest にない",
                    detail_code="floor-toolchain-cxx-manifest-missing",
                    origin="floor-toolchain:cxx-manifest",
                    outcome="not-configured",
                ) from exc
            if (type(verified_oracle_compiler) is not str
                    or not os.path.isabs(verified_oracle_compiler)):
                raise _FloorOraclePreflightError(
                    "検証済み floor cxx realpath が絶対 path でない",
                    detail_code="floor-toolchain-cxx-manifest-invalid",
                    origin="floor-toolchain:cxx-manifest",
                    outcome="invalid-path",
                    path=_preflight_candidate_path(verified_oracle_compiler),
                )
            if fetchcontent_base_dir is None:
                fetchcontent_base = _stage_default_floor_fetchcontent_payload(
                    repo_root=Path(repo_root), contract=contract,
                    reservation_binding=reservation_binding,
                )
            else:
                fetchcontent_base = _canonical_floor_fetchcontent_base(
                    fetchcontent_base_dir, repo_root=Path(repo_root),
                )
            dependency_binding = _prepare_floor_oracle_dependency(
                fetchcontent_base,
                ccbench_pin=ccbench_pin,
                expected_toolchain_manifest=expected_toolchain_manifest,
                repo_root=Path(repo_root),
                _material_sink=_canonical_material_sink,
            )
            if (
                dependency_binding.oracle_root is None
                or dependency_binding.canonical_lease_root is None
                or dependency_binding.dependency_manifest_sha256 is None
            ):
                raise _FloorOraclePreflightError(
                    "floor canonical dependency binding が不完全",
                    detail_code=(
                        "floor-dependency-canonical-verification-failed"
                    ),
                    origin="floor-dependency-canonical:root",
                    outcome="identity-mismatch",
                    path=dependency_binding.source_root,
                )
            _create_private_json(
                marker_root / "sort-swo-oracle-dependency.json",
                {
                    "event": "sort-swo-oracle-dependency-attempt",
                    **dependency_binding.private_dict(),
                },
            )
    except _FloorOraclePreflightError as exc:
        if not production_floor_path:
            raise
        assert marker_root is not None
        raise _persist_floor_oracle_preflight_failure(
            marker_root,
            exc,
            verified_compiler=verified_oracle_compiler,
        ) from exc
    built: dict[str, dict] = {}
    for cell in cells:
        holdout_id = cell["holdout_id"]
        configuration_id = cell["configuration_id"]
        effective_prepare_fn = prepare_fn
        if dependency_binding is not None and prepare_fn is prepare_cell:
            oracle_marker = None
            if configuration_id == "sort_best":
                assert marker_root is not None
                oracle_marker = lambda: _write_phase_marker(
                    marker_root,
                    cell=cell["cell_id"],
                    phase="oracle",
                    compiler=verified_oracle_compiler,
                    dependency=dependency_binding,
                )

            def floor_prepare(
                    prepared_cell, prepared_pin, *, cxx,
                    _marker=oracle_marker,
                    _dependency=dependency_binding,
                    _compiler=verified_oracle_compiler):
                return prepare_fn(
                    prepared_cell,
                    prepared_pin,
                    cxx=cxx,
                    oracle_dependency_root=_dependency.oracle_root,
                    oracle_compiler=_compiler,
                    oracle_phase_marker=_marker,
                )

            effective_prepare_fn = floor_prepare
        with _prepared_binding(
                freeze=freeze, holdout_id=holdout_id,
                configuration_id=configuration_id, ccbench_pin=ccbench_pin,
                cxx=cxx, prepare_fn=effective_prepare_fn) as (identity, prepared):
            oracle_attempt = prepared.oracle_attempt
            if configuration_id == "sort_best":
                if oracle_attempt is None:
                    raise FloorCampaignError(
                        "sort_best cell に SWO PASS receipt がない: "
                        f"cell={cell['cell_id']}"
                    )
            elif oracle_attempt is not None:
                raise FloorCampaignError(
                    "non-sort cell に SWO receipt がある: "
                    f"cell={cell['cell_id']}"
                )
            evidence_kwargs = {}
            if prepared.sort_oracle_contract_id is not None:
                evidence_kwargs["sort_oracle_contract_id"] = (
                    prepared.sort_oracle_contract_id
                )
            evidence = source_digest.resolve_evidence(
                prepared.genome,
                ccbench_pin,
                ccbench_dir=prepared.ccbench_dir,
                cxx=cxx,
                **evidence_kwargs,
            )
            receipt_identity = dict(identity)
            if receipt_identity["src_token"] != evidence.src_token:
                # Production build_v2 は直後にこの不一致を拒否する。既存の注入 build seam だけは
                # legacy token を観測できるため、durable identity は権威ある SourceEvidence へ
                # 正規化し、build 呼出しの token 自体は変更しない。
                receipt_identity["src_token"] = evidence.src_token
                suffix = "" if evidence.src_token == "stock" else f"|src={evidence.src_token}"
                receipt_identity["variant_id"] = hashlib.sha256(
                    f"{receipt_identity['genome_canonical']}{suffix}".encode("utf-8")
                ).hexdigest()[:12]
                unsigned = {
                    key: receipt_identity[key]
                    for key in sorted(set(receipt_identity) - {"binding_sha256"})
                }
                receipt_identity["binding_sha256"] = hashlib.sha256(json.dumps(
                    unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                ).encode("utf-8")).hexdigest()
            review = reviewed_source_capability(
                review_id=ReviewId.S8B_FLOOR,
                source=evidence,
                input_sha256=identity["entry_sha256"],
            )
            admission = derive_build_admission(
                build_context, evidence, review_receipt=review,
            )
            if production_floor_path:
                assert marker_root is not None
            if marker_root is not None:
                _write_phase_marker(
                    marker_root,
                    cell=cell["cell_id"],
                    phase="build",
                    compiler=(verified_oracle_compiler or cxx),
                    dependency=dependency_binding,
                )
            build_kwargs = {}
            if prepared.sort_oracle_contract_id is not None:
                build_kwargs["sort_oracle_contract_id"] = (
                    prepared.sort_oracle_contract_id
                )
            if dependency_binding is not None:
                # The run-scoped dependency source was validated before any
                # cell build.  Reuse it only as the current compiler-input
                # masstree root; the post-oracle capability remains sort-only.
                build_kwargs["current_compiler_input_masstree_root"] = str(
                    dependency_binding.source_root
                )
            dependency_bound_sort = (
                dependency_binding is not None
                and configuration_id == "sort_best"
            )
            if dependency_bound_sort:
                if fetchcontent_base is None:
                    raise FloorCampaignError(
                        "sort_best post-oracle capability の FetchContent base がない"
                    )
                build_kwargs.update({
                    "fetchcontent_base_dir": str(fetchcontent_base),
                    "fetchcontent_dependency_receipt": (
                        dependency_binding.cache_receipt()
                    ),
                    "fetchcontent_archive_sha256": (
                        dependency_binding.archive_sha256
                    ),
                    "post_oracle_dependency_binding": (
                        _post_oracle_dependency_binding(
                            oracle_attempt, dependency_binding,
                        )
                    ),
                })
                if build_fn is not buildcache.build_v2:
                    raise FloorCampaignError(
                        "dependency-bound sort_best は exact buildcache.build_v2 "
                        "builder が必須"
                    )
                if dependency_binding.transport_mode == "source-dir":
                    build_kwargs.update({
                        "masstree_source_dir": str(
                            fetchcontent_base / "masstree-src"
                        ),
                        "mimalloc_source_dir": str(
                            fetchcontent_base / "mimalloc-src"
                        ),
                        "googletest_source_dir": str(
                            fetchcontent_base / "googletest-src"
                        ),
                    })
            if dependency_bound_sort:
                if build_fn is not buildcache.build_v2:
                    raise FloorCampaignError(
                        "dependency-bound sort_best の builder が exact "
                        "buildcache.build_v2 でない"
                    )
                if "post_oracle_dependency_binding" not in build_kwargs:
                    raise FloorCampaignError(
                        "dependency-bound sort_best の build 直前に "
                        "post-oracle capability がない"
                    )
            entry = binding_entry(freeze, holdout_id, configuration_id)
            try:
                descriptor = (
                    _expected_materialization.expected_materialization_descriptor(
                        ccbench_commit=ccbench_pin,
                        configuration=configuration_id,
                        declaration=entry,
                    )
                )
            except _expected_materialization.ExpectedMaterializationError as exc:
                raise FloorCampaignError(
                    f"floor build declaration を記述子へ固定できない: {exc}"
                ) from exc
            try:
                result = _invoke_build(
                    prepared.genome,
                    admission=admission, build_context=build_context,
                    source_evidence=evidence,
                    contract=contract, ccbench_commit=ccbench_pin,
                    trace=False, cache_root=cache_root,
                    src_token=prepared.src_token,
                    cc=cc, cxx=cxx,
                    ccbench_dir=prepared.ccbench_dir,
                    expected_materialization_descriptor=descriptor,
                    timeout_s=_FLOOR_BUILD_CAP_PER_CELL_S,
                    expected_toolchain_manifest=expected_toolchain_manifest,
                    **build_kwargs,
                )
            except Exception as exc:
                if dependency_binding is None or configuration_id != "sort_best":
                    raise
                assert marker_root is not None
                assert fetchcontent_base is not None
                error = _floor_postflight_error(
                    "sort_best cell build または build 成果物抽出に失敗",
                    detail_code="floor-dependency-postflight-build-failed",
                    outcome="execution-failed",
                    path=fetchcontent_base / "masstree-src",
                )
                raise _persist_floor_oracle_postflight_failure(
                    marker_root,
                    error,
                    verified_compiler=verified_oracle_compiler,
                    build_exception=_floor_build_exception_diagnostic(exc),
                ) from exc
            if getattr(result, "contract_sha256", None) != contract.contract_sha256:
                raise FloorCampaignError(
                    "floor build が contract namespace provenance を返さない "
                    "(legacy build 経路への落下を拒否)"
                )
            compiler_input_manifest = getattr(
                result, "compiler_input_manifest", None,
            )
            compiler_input_manifest_sha256 = getattr(
                result, "compiler_input_manifest_sha256", None,
            )
            compiler_input_dependency_prefix_roots = getattr(
                result, "compiler_input_dependency_prefix_roots", (),
            )
            source_snapshot_sha256 = getattr(
                result, "source_snapshot_sha256", None,
            )
            expected_materialization_sha256 = getattr(
                result, "expected_materialization_sha256", None,
            )
            binary_path = Path(result.binary)
            configure_argv = getattr(result, "configure_argv", ())
            build_argv = getattr(result, "build_argv", ())
            # E0 以前の局所 fake は list-valued legacy field を使っていた。shell 文字列は
            # 再解析せず拒否し、構造 list/tuple だけを移行入力として認める。
            if not configure_argv and isinstance(getattr(result, "configure_cmd", None), list):
                configure_argv = tuple(result.configure_cmd)
            if not build_argv and isinstance(getattr(result, "build_cmd", None), list):
                build_argv = tuple(result.build_cmd)
            if dependency_binding is not None and configuration_id == "sort_best":
                assert marker_root is not None
                assert fetchcontent_base is not None
                try:
                    _verify_floor_build_dependency(
                        result, configure_argv,
                        fetchcontent_base=fetchcontent_base,
                        before=dependency_binding,
                        expected_toolchain_manifest=(
                            expected_toolchain_manifest
                        ),
                        require_run_local_identity=True,
                    )
                except _FloorOraclePreflightError as exc:
                    raise _persist_floor_oracle_postflight_failure(
                        marker_root,
                        exc,
                        verified_compiler=verified_oracle_compiler,
                    ) from exc
            if (not isinstance(configure_argv, (list, tuple))
                    or not all(isinstance(token, str) for token in configure_argv)
                    or not configure_argv):
                raise FloorCampaignError("build result.configure_argv が非空 list[str] でない")
            if (not isinstance(build_argv, (list, tuple))
                    or not all(isinstance(token, str) for token in build_argv)
                    or not build_argv):
                raise FloorCampaignError("build result.build_argv が非空 list[str] でない")
            try:
                admission_receipt = _binary_admission.issue_binary_admission_receipt(
                    admission=admission, expected_policy=build_context.policy,
                    source=evidence, cell_id=cell["cell_id"],
                    holdout_id=holdout_id, configuration_id=configuration_id,
                    binding=receipt_identity, binary=binary_path,
                    binary_sha256=result.bin_sha256,
                    contract_sha256=contract.contract_sha256, trace=False,
                    source_snapshot_sha256=source_snapshot_sha256,
                    expected_materialization_sha256=(
                        expected_materialization_sha256
                    ),
                    compiler_input_manifest=compiler_input_manifest,
                    compiler_input_manifest_sha256=(
                        compiler_input_manifest_sha256
                    ),
                    current_compiler_input_masstree_root=(
                        str(dependency_binding.source_root)
                        if dependency_binding is not None else None
                    ),
                    current_compiler_input_dependency_prefix_roots=(
                        compiler_input_dependency_prefix_roots
                    ),
                )
            except _binary_admission.BinaryAdmissionError as exc:
                raise FloorCampaignError(
                    f"binary admission receipt を発行できない: {exc}"
                ) from exc
            sort_receipt = None
            if configuration_id == "sort_best":
                try:
                    sort_receipt = project_sort_swo_pass_attempt(
                        oracle_attempt,
                        cell_id=cell["cell_id"],
                        holdout_id=holdout_id,
                        configuration_id=configuration_id,
                        entry_sha256=identity["entry_sha256"],
                        binary_sha256=result.bin_sha256,
                    )
                except SortSwoReceiptError as exc:
                    raise FloorCampaignError(
                        f"sort_best SWO PASS receipt が不正: "
                        f"cell={cell['cell_id']}: {exc}"
                    ) from exc
                if marker_root is not None:
                    cell_digest = hashlib.sha256(
                        cell["cell_id"].encode("utf-8")
                    ).hexdigest()[:16]
                    _create_private_json(
                        marker_root / f"sort-swo-oracle-pass-{cell_digest}.json",
                        {
                            "schema": _PRIVATE_SORT_SWO_EVIDENCE_SCHEMA,
                            "cell_id": cell["cell_id"],
                            "oracle_attempt": oracle_attempt,
                            "portable_receipt": sort_receipt,
                        },
                    )
            record = {
                "cell_id": cell["cell_id"],
                "holdout_id": holdout_id,
                "configuration_id": configuration_id,
                "binary": str(binary_path),
                "binary_sha256": result.bin_sha256,
                "bin_hash_short": result.bin_hash,
                "binding": receipt_identity,
                "configure_argv": list(configure_argv),
                "build_argv": list(build_argv),
                "cached": result.cached,
                "admission_receipt": admission_receipt,
                "_ccbench_root": str(Path(
                    getattr(result, "ccbench_root", None) or prepared.ccbench_dir
                ).absolute()),
            }
            if sort_receipt is not None:
                record["sort_swo_oracle"] = sort_receipt
            built[cell["cell_id"]] = record
            if dependency_binding is not None and configuration_id == "sort_best":
                built[cell["cell_id"]]["_fetchcontent_base_dir"] = str(
                    fetchcontent_base
                )
    return built


def build_cells(
        freeze: Mapping, cells: list[dict], *, ccbench_pin: str,
        out_root: Path, prepare_fn, contract, verified_calibration,
        build_fn=None,
        fetchcontent_base_dir: Optional[os.PathLike[str] | str] = None,
        phase_marker_root: Optional[os.PathLike[str] | str] = None,
        repo_root: Path = ROOT,
        reservation_binding: Optional[reservation.ReservationBinding] = None,
) -> dict[str, dict]:
    """Build cells while retaining the canonical lease through postflight."""
    build_fn = build_fn or buildcache.build_v2
    try:
        build_signature = inspect.signature(build_fn)
        descriptor_aware = (
            "expected_materialization_descriptor" in build_signature.parameters
            or any(
                parameter.kind is inspect.Parameter.VAR_KEYWORD
                for parameter in build_signature.parameters.values()
            )
        )
    except (TypeError, ValueError):
        descriptor_aware = False

    def invoke_build(
            genome, *, admission, build_context, source_evidence,
            expected_toolchain_manifest,
            expected_materialization_descriptor, **kwargs):
        call_kwargs = {
            "admission": admission,
            "build_context": build_context,
            "source_evidence": source_evidence,
            "expected_toolchain_manifest": expected_toolchain_manifest,
            **kwargs,
        }
        if descriptor_aware:
            call_kwargs["expected_materialization_descriptor"] = (
                expected_materialization_descriptor
            )
        return build_fn(genome, **call_kwargs)
    materials: list[
        _sort_swo_dependency_material.CanonicalDependencyMaterial
    ] = []
    try:
        return _build_cells_impl(
            freeze, cells, ccbench_pin=ccbench_pin,
            out_root=out_root, prepare_fn=prepare_fn, contract=contract,
            verified_calibration=verified_calibration,
            build_fn=build_fn,
            _invoke_build=invoke_build,
            fetchcontent_base_dir=fetchcontent_base_dir,
            phase_marker_root=phase_marker_root,
            repo_root=repo_root,
            reservation_binding=reservation_binding,
            _canonical_material_sink=materials,
        )
    finally:
        for material in reversed(materials):
            _sort_swo_dependency_material.cleanup_canonical_dependency(
                material,
            )


def _portable_relpath(value, *, out_root: Path, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise FloorCampaignError(f"portable built {field} が空でない str でない")
    path = Path(value)
    if not path.is_absolute():
        raise FloorCampaignError(f"runtime built {field} が絶対 path でない: {value!r}")
    try:
        rel = path.relative_to(Path(out_root).absolute()).as_posix()
    except ValueError as exc:
        raise FloorCampaignError(
            f"runtime built {field} が out_root 外: {value!r}") from exc
    _validate_portable_path(rel, field=field)
    return rel


def _validate_portable_path(value, *, field: str) -> str:
    if (not isinstance(value, str) or not value or value.startswith("/")
            or "\\" in value or "//" in value
            or any(ord(ch) < 32 or 127 <= ord(ch) <= 159 for ch in value)):
        raise FloorCampaignError(f"portable built {field} path 文法が不正: {value!r}")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise FloorCampaignError(f"portable built {field} path component が不正: {value!r}")
    return value


def _replace_root_component(token: str, root: str, placeholder: str) -> str:
    """argv token 内の root を path component 境界だけで置換する（表示・照合専用）。"""
    start = 0
    while True:
        index = token.find(root, start)
        if index < 0:
            return token
        end = index + len(root)
        before_ok = index == 0 or token[index - 1] in "=,:"
        after_ok = end == len(token) or token[end] == "/"
        if before_ok and after_ok:
            token = token[:index] + placeholder + token[end:]
            start = index + len(placeholder)
        else:
            start = index + 1


def _portable_argv(
        argv, *, out_root: Path, ccbench_root: str, field: str,
        fetchcontent_base_dir: Optional[str] = None,
) -> list[str]:
    """absolute root を placeholder 化した表示・照合専用 argv（再実行は禁止）。"""
    if (not isinstance(argv, (list, tuple)) or not argv
            or not all(isinstance(token, str) for token in argv)):
        raise FloorCampaignError(f"runtime built {field} が非空 list[str] でない")
    roots = [
        (str(Path(out_root).absolute()), "${OUT_ROOT}"),
        (str(Path(ccbench_root).absolute()), "${CCBENCH_ROOT}"),
    ]
    if fetchcontent_base_dir is not None:
        if (type(fetchcontent_base_dir) is not str or not fetchcontent_base_dir
                or not Path(fetchcontent_base_dir).is_absolute()):
            raise FloorCampaignError(
                f"runtime built {field} の FetchContent base が絶対 path でない"
            )
        roots.append((
            str(Path(fetchcontent_base_dir).absolute()),
            "${FETCHCONTENT_BASE_DIR}",
        ))
    roots.sort(key=lambda item: len(item[0]), reverse=True)
    projected = []
    for raw in argv:
        if any(marker in raw for marker in _PORTABLE_PLACEHOLDERS):
            raise FloorCampaignError(
                f"runtime built {field} raw token に予約 placeholder がある: {raw!r}")
        token = raw
        for root, placeholder in roots:
            token = _replace_root_component(token, root, placeholder)
        if (fetchcontent_base_dir is not None
                and fetchcontent_base_dir in token):
            raise FloorCampaignError(
                f"runtime built {field} に raw FetchContent base が残った"
            )
        projected.append(token)
    return projected


def _validate_portable_built(
        built: Mapping, *, expected_ccbench_pin: str | None = None,
        expected_contract_sha256: str | None = None,
) -> dict[str, dict]:
    if not isinstance(built, Mapping):
        raise FloorCampaignError("portable binaries が Mapping でない")
    validated: dict[str, dict] = {}
    current_policy = resolve_current_build_admission_policy()
    for cell_id in sorted(built):
        record = built[cell_id]
        if not isinstance(cell_id, str) or not cell_id:
            raise FloorCampaignError("portable binaries の cell_id key が不正")
        configuration_id = (
            record.get("configuration_id") if isinstance(record, Mapping) else None
        )
        expected_keys = _binary_admission.portable_built_keys_for(configuration_id)
        if not isinstance(record, Mapping) or set(record) != set(expected_keys):
            raise FloorCampaignError(f"portable binaries[{cell_id}] の exact key 集合が不一致")
        if record["cell_id"] != cell_id:
            raise FloorCampaignError(f"portable binaries[{cell_id}].cell_id が key と不一致")
        for field in ("holdout_id", "configuration_id"):
            if not isinstance(record[field], str) or not record[field]:
                raise FloorCampaignError(f"portable binaries[{cell_id}].{field} が不正")
        _validate_portable_path(record["binary"], field="binary")
        _validate_portable_path(record["store_path"], field="store_path")
        sha = record["binary_sha256"]
        if not buildcache.is_full_sha256(sha):
            raise FloorCampaignError(f"portable binaries[{cell_id}].binary_sha256 が不正")
        if record["bin_hash_short"] != sha[:16]:
            raise FloorCampaignError(f"portable binaries[{cell_id}].bin_hash_short が不一致")
        if not isinstance(record["binding"], Mapping):
            raise FloorCampaignError(f"portable binaries[{cell_id}].binding が object でない")
        for field in ("configure_argv", "build_argv"):
            argv = record[field]
            if (not isinstance(argv, list) or not argv
                    or not all(isinstance(token, str) for token in argv)):
                raise FloorCampaignError(f"portable binaries[{cell_id}].{field} が不正")
        if type(record["cached"]) is not bool:
            raise FloorCampaignError(f"portable binaries[{cell_id}].cached が bool でない")
        try:
            receipt = _binary_admission.validate_portable_binary_record(
                record, expected_policy=current_policy,
                expected_ccbench_pin=expected_ccbench_pin,
                expected_contract_sha256=expected_contract_sha256,
                expected_cell_id=cell_id,
                expected_holdout_id=record["holdout_id"],
                expected_configuration_id=record["configuration_id"],
            )
        except _binary_admission.BinaryAdmissionError as exc:
            raise FloorCampaignError(
                f"portable binaries[{cell_id}] admission receipt が不正: {exc}"
            ) from exc
        validated_record = {
            key: (dict(value) if key == "binding" else receipt
                  if key == "admission_receipt" else list(value)
                  if key in {"configure_argv", "build_argv"} else value)
            for key, value in record.items()
        }
        if "sort_swo_oracle" in record:
            validated_record["sort_swo_oracle"] = json.loads(json.dumps(
                record["sort_swo_oracle"], ensure_ascii=False, sort_keys=True,
                separators=(",", ":"), allow_nan=False,
            ))
        validated[cell_id] = validated_record
    return validated


def project_built_records(
        runtime_built: Mapping, *, out_root: Path,
        expected_ccbench_pin: str | None = None,
        expected_contract_sha256: str | None = None,
) -> dict[str, dict]:
    """runtime view を manifest/result 用 PortableBuiltRecord へ copy-project する。

    ``configure_argv`` / ``build_argv`` は provenance の表示・照合専用であり、再実行用 API
    ではない。置換は token 単位・path component 境界・root longest-first で行う。
    """
    artifact: dict[str, dict] = {}
    for cell_id in sorted(runtime_built):
        rec = runtime_built[cell_id]
        configuration_id = (
            rec.get("configuration_id") if isinstance(rec, Mapping) else None
        )
        has_fetchcontent_base = (
            isinstance(rec, Mapping) and "_fetchcontent_base_dir" in rec
        )
        if (not isinstance(rec, Mapping)
                or frozenset(rec) != _runtime_built_keys_for(
                    configuration_id, stored=True,
                    fetchcontent=has_fetchcontent_base,
                )):
            raise FloorCampaignError(
                f"runtime binaries[{cell_id}] の exact key 集合が不一致"
            )
        is_sort_best = rec.get("configuration_id") == "sort_best"
        if has_fetchcontent_base and not is_sort_best:
            raise FloorCampaignError(
                f"runtime binaries[{cell_id}] の FetchContent base は "
                "sort_best にだけ許可される"
            )
        ccbench_root = rec.get("_ccbench_root")
        if not isinstance(ccbench_root, str) or not ccbench_root:
            raise FloorCampaignError(f"runtime binaries[{cell_id}] の ccbench root がない")
        fetchcontent_base = rec.get("_fetchcontent_base_dir")
        artifact_record = {
            "cell_id": rec["cell_id"],
            "holdout_id": rec["holdout_id"],
            "configuration_id": rec["configuration_id"],
            "binary": _portable_relpath(rec["binary"], out_root=out_root, field="binary"),
            "binary_sha256": rec["binary_sha256"],
            "bin_hash_short": rec["bin_hash_short"],
            "binding": dict(rec["binding"]),
            "configure_argv": _portable_argv(
                rec["configure_argv"], out_root=out_root,
                ccbench_root=ccbench_root, field="configure_argv",
                fetchcontent_base_dir=fetchcontent_base),
            "build_argv": _portable_argv(
                rec["build_argv"], out_root=out_root,
                ccbench_root=ccbench_root, field="build_argv",
                fetchcontent_base_dir=fetchcontent_base),
            "cached": rec["cached"],
            "admission_receipt": json.loads(json.dumps(
                rec["admission_receipt"], ensure_ascii=True,
                sort_keys=True, separators=(",", ":"),
            )),
            "store_path": _portable_relpath(
                rec["store_path"], out_root=out_root, field="store_path"),
        }
        if is_sort_best:
            artifact_record["sort_swo_oracle"] = json.loads(json.dumps(
                rec["sort_swo_oracle"], ensure_ascii=False, sort_keys=True,
                separators=(",", ":"), allow_nan=False,
            ))
        artifact[cell_id] = artifact_record
    return _validate_portable_built(
        artifact, expected_ccbench_pin=expected_ccbench_pin,
        expected_contract_sha256=expected_contract_sha256,
    )


def resolve_portable_built(
        artifact_built: Mapping, *, out_root: Path,
        expected_ccbench_pin: str | None = None,
        expected_contract_sha256: str | None = None,
) -> dict[str, dict]:
    """厳密検証済み artifact view を out_root 基準の runtime absolute view に解決する。"""
    artifact = _validate_portable_built(
        artifact_built, expected_ccbench_pin=expected_ccbench_pin,
        expected_contract_sha256=expected_contract_sha256,
    )
    runtime: dict[str, dict] = {}
    root = Path(out_root).absolute()
    for cell_id, rec in artifact.items():
        runtime[cell_id] = dict(rec)
        runtime[cell_id]["binary"] = str(root / rec["binary"])
        runtime[cell_id]["store_path"] = str(root / rec["store_path"])
    return runtime


# --------------------------------------------------------------------------- #
# manifest (create-only)                                                        #
# --------------------------------------------------------------------------- #

def _validate_binaries_cover_cells(
        binaries: Mapping, cells: Sequence[Mapping]) -> None:
    """producer 出力の binary 集合を外部 cell 列へ完全束縛する。"""
    if not isinstance(binaries, Mapping):
        raise FloorCampaignError("binaries が Mapping でない")
    if (not isinstance(cells, Sequence)
            or isinstance(cells, (str, bytes, bytearray)) or not cells):
        raise FloorCampaignError("cells が非空 Sequence でない")

    cell_by_id: dict[str, Mapping] = {}
    sort_count_by_holdout: dict[str, int] = {}
    for index, cell in enumerate(cells):
        if not isinstance(cell, Mapping):
            raise FloorCampaignError(f"cells[{index}] が Mapping でない")
        cell_id = cell.get("cell_id")
        holdout_id = cell.get("holdout_id")
        configuration_id = cell.get("configuration_id")
        if any(type(value) is not str or not value for value in (
                cell_id, holdout_id, configuration_id)):
            raise FloorCampaignError(f"cells[{index}] identity が不正")
        if cell_id in cell_by_id:
            raise FloorCampaignError(f"cells の cell_id が重複: {cell_id}")
        cell_by_id[cell_id] = cell
        sort_count_by_holdout.setdefault(holdout_id, 0)
        if configuration_id == "sort_best":
            sort_count_by_holdout[holdout_id] += 1

    invalid_holdouts = sorted(
        holdout_id for holdout_id, count in sort_count_by_holdout.items()
        if count != 1
    )
    if invalid_holdouts:
        raise FloorCampaignError(
            "各 holdout の sort_best cell がちょうど 1 件でない: "
            f"{invalid_holdouts}"
        )

    got_ids = set(binaries)
    expected_ids = set(cell_by_id)
    if got_ids != expected_ids:
        missing = sorted(expected_ids - got_ids, key=repr)
        extra = sorted(got_ids - expected_ids, key=repr)
        raise FloorCampaignError(
            "binaries が cells を完全被覆しない: "
            f"missing={missing}, extra={extra}"
        )
    for cell_id, cell in cell_by_id.items():
        record = binaries[cell_id]
        if not isinstance(record, Mapping):
            raise FloorCampaignError(f"binaries[{cell_id}] が Mapping でない")
        for field in ("cell_id", "holdout_id", "configuration_id"):
            if record.get(field) != cell[field]:
                raise FloorCampaignError(
                    f"binaries[{cell_id}].{field} が対応 cell と不一致"
                )

def assemble_manifest(*, protocol: Mapping, protocol_sha256: str,
                      freeze_sha256: str, cells: list[dict],
                      built: Mapping, schedule: list[dict],
                      perf_preflight=None, mode=None) -> dict:
    """参照 hash と build identity・schedule を持つ floor manifest を組み立てる (純粋)。"""
    _validate_binaries_cover_cells(built, cells)
    portable_built = _validate_portable_built(
        built, expected_ccbench_pin=protocol["ccbench_pin"],
        expected_contract_sha256=protocol.get("contract_sha256"),
    )
    use_perf = _assert_perf_mode(mode, perf_preflight)
    normalized_perf = (
        _normalize_perf_preflight(perf_preflight)
        if perf_preflight is not None else None
    )
    # _assert_perf_mode と別の producer-side gate として残す。manifest 単体の
    # M6 変異が A の拒否へ吸収されないよう、同じ条件をここでも fail-closed にする。
    if mode != "pilot" and normalized_perf is not None and use_perf:
        raise CampaignAbort(
            "available perf_preflight を持つ official manifest を拒否する"
        )
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "protocol_sha256": protocol_sha256,
        "freeze": dict(protocol["freeze"]),
        "freeze_sha256": freeze_sha256,
        "env_tag": protocol["env_tag"],
        "ccbench_pin": protocol["ccbench_pin"],
        "stock_configuration": protocol["stock_configuration"],
        "schedule_algorithm": protocol["schedule_algorithm"],
        "master_seed": protocol["master_seed"],
        "n_sessions": protocol["n_sessions"],
        "reps": protocol["reps"],
        "extime_s": protocol["extime_s"],
        "session_cv_max": protocol["session_cv_max"],
        "cell_cv_max": protocol["cell_cv_max"],
        "cells": [dict(cell) for cell in cells],
        "binaries": portable_built,
        "schedule": [dict(row) for row in schedule],
    }
    if normalized_perf is not None:
        manifest["perf_preflight"] = normalized_perf
        if mode != "pilot" and not use_perf:
            run_cmd, leading_indicators = (
                _floor_contract.manifest_perf_validation_context(manifest)
            )
            try:
                manifest["perf_observation"] = _perf_preflight.build_perf_observation(
                    normalized_perf, run_cmd=run_cmd,
                    leading_indicators=leading_indicators,
                )
            except _perf_preflight.PerfPreflightError as exc:
                raise FloorCampaignError(
                    f"manifest perf_observation を構築できない: {exc}"
                ) from exc
    return manifest


def _write_create_only_json(
        path: Path, document: Mapping,
        *, write_capability: Optional[WriteCapability] = None) -> bytes:
    """create-only で JSON を書き、書いた byte 列を返す (redo/上書きは fail-closed)。"""
    payload = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    try:
        opener = (
            open_with_write_capability(write_capability, path, "xb")
            if write_capability is not None else open(path, "xb")
        )
        with opener as stream:
            stream.write(payload.encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise FloorCampaignError(f"既に存在するため上書きしない: {path}") from exc
    return payload.encode("utf-8")


def _fsync_directory(path: Path) -> None:
    directory_fd = os.open(Path(path), os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _stage_bytes(
        path: Path, payload: bytes,
        *, write_capability: Optional[WriteCapability] = None) -> None:
    """決定的 pending file を fsync。既存時は bytes 一致だけを受理する。"""
    path = Path(path)
    if path.exists():
        if not path.is_file() or path.is_symlink() or path.read_bytes() != payload:
            raise FloorCampaignError(f"staged bytes が再計算と不一致: {path}")
        return
    _create_only_bytes(path, payload, write_capability=write_capability)


def _publish_staged_create_only(pending: Path, destination: Path, payload: bytes) -> None:
    """fsync 済み pending inode を hard-link で atomic create-only publish する。"""
    pending = Path(pending)
    destination = Path(destination)
    if destination.exists():
        if (not destination.is_file() or destination.is_symlink()
                or destination.read_bytes() != payload):
            raise FloorCampaignError(f"publish 済み bytes が再計算と不一致: {destination}")
        pending.unlink(missing_ok=True)
        return
    if not pending.is_file() or pending.is_symlink() or pending.read_bytes() != payload:
        raise FloorCampaignError(f"publish 元 staged bytes が無いか不一致: {pending}")
    try:
        os.link(pending, destination)
    except FileExistsError:
        if destination.read_bytes() != payload:
            raise FloorCampaignError(f"並行 publish bytes が不一致: {destination}")
    _fsync_directory(destination.parent)
    pending.unlink(missing_ok=True)


def _atomic_create_only_json(
        path: Path, document: Mapping,
        *, write_capability: Optional[WriteCapability] = None) -> bytes:
    """manifest 用: 一時 file fsync 後に atomic create-only publish する。"""
    payload = (json.dumps(
        document, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path = Path(path)
    # L run_dir の許可集合を汚さないよう、manifest pending は run_dir の外（同一 FS）に置く。
    pending = path.parent.parent / f".{path.parent.name}.{path.name}.pending"
    _stage_bytes(pending, payload, write_capability=write_capability)
    _publish_staged_create_only(pending, path, payload)
    return payload


# --------------------------------------------------------------------------- #
# launch certificate (C2-2) — official 開始時の clean-scan 証明                 #
#                                                                             #
# official は CLI・public wrapper・private core で同じ明示承認を独立に要求する。         #
# 承認 bool は測定 seam に含めず、発行・journal・resume の結線へも記録しない。          #
# --------------------------------------------------------------------------- #

def _pre_oracle_blob(root: Path, commit: str, rel: str, *, label: str) -> bytes:
    """pre-oracle commit の exact 100644 blob を worktree 非依存で読む。"""
    try:
        listed = subprocess.run(
            ["git", "ls-tree", "-z", commit, "--", rel], cwd=root, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout
        entries = [entry for entry in listed.split(b"\0") if entry]
        if len(entries) != 1:
            raise FloorCampaignError(
                f"launch refusal: {label} が pre_oracle_head に exact 1 blob ない"
            )
        meta, separator, actual = entries[0].decode("utf-8", "strict").partition("\t")
        mode, kind, _oid = meta.split(" ")
        if not separator or actual != rel or mode != "100644" or kind != "blob":
            raise FloorCampaignError(
                f"launch refusal: {label} が pre_oracle_head の 100644 blob でない"
            )
        return subprocess.run(
            ["git", "cat-file", "blob", f"{commit}:{rel}"], cwd=root, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout
    except FloorCampaignError:
        raise
    except (OSError, UnicodeError, ValueError, subprocess.CalledProcessError) as exc:
        raise FloorCampaignError(
            f"launch refusal: {label} の pre_oracle blob を検証できない: {exc}"
        ) from exc

def _floor_preflight_freeze_allowlist(
        root: Path, *, freeze_path: str, freeze_sha256: str,
        protocol_sha256: str,
        _read_bytes: Optional[Callable[[Path], bytes]] = None) -> dict[str, str]:
    """journal 宣言由来の有界集合を exact path + bytes hash で構成する。"""
    root = Path(root)
    held_checks = []
    read_bytes = (lambda path: path.read_bytes()) if _read_bytes is None else _read_bytes
    if freeze_path != _HOLDOUT_FREEZE_REL:
        raise FloorCampaignError(
            "launch refusal: official freeze path が holdout_freeze.json でない"
        )
    for rel in ("output", "output/s8b-freeze", _SELECTOR_RUNS_REL):
        directory = root / rel
        if directory.is_symlink() or not directory.is_dir():
            raise FloorCampaignError(
                f"launch refusal: official preflight directory が実 directory でない: {rel}"
            )

    captured: dict[str, bytes] = {}
    for rel in sorted(_PREFLIGHT_FIXED_FILES):
        path = root / rel
        if path.is_symlink() or not path.is_file():
            raise FloorCampaignError(
                f"launch refusal: official preflight 必須 file がない: {rel}"
            )
        try:
            captured[rel] = read_bytes(path)
        except OSError as exc:
            raise FloorCampaignError(
                f"launch refusal: official preflight 必須 bytes を読めない: {rel}: {exc}"
            ) from exc

    freeze_bytes = captured[_HOLDOUT_FREEZE_REL]
    actual_freeze_sha256 = hashlib.sha256(freeze_bytes).hexdigest()
    if (actual_freeze_sha256 != _selector_freeze.V1_FREEZE_SHA256
            or actual_freeze_sha256 != freeze_sha256):
        raise FloorCampaignError(
            "launch refusal: prediction 検証対象が v1 freeze bytes でない"
        )
    if _freeze_hold.HELD:
        held_checks.append(_freeze_hold.held_marker(
            "s8b-floor.protocol-bytes-expected-pin",
        ))
    elif hashlib.sha256(captured[_FLOOR_PROTOCOL_REL]).hexdigest() != protocol_sha256:
        raise FloorCampaignError(
            "launch refusal: floor protocol bytes sha256 が expected と不一致"
        )

    prediction_bytes = captured[_SELECTOR_PREDICTIONS_REL]
    try:
        freeze_for_prediction = json.loads(
            freeze_bytes.decode("utf-8"), object_pairs_hook=_no_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
        prediction, rows = _selector_freeze._validate_prediction_document_bytes(
            prediction_bytes, freeze=freeze_for_prediction,
            source=_SELECTOR_PREDICTIONS_REL,
        )
        _selector_freeze.verify_prediction_freeze(
            prediction, freeze=freeze_for_prediction, root=root,
        )
    except (UnicodeError, json.JSONDecodeError, FloorCampaignError,
            _selector_freeze.SelectorFreezeError) as exc:
        raise FloorCampaignError(
            f"launch refusal: selector prediction verify 不通過: {exc}"
        ) from exc

    try:
        records = _parse_selector_journal_bytes(captured[_SELECTOR_JOURNAL_REL])
        journal = _CapturedSelectorJournal(
            root / _SELECTOR_JOURNAL_REL, records,
        )
        pre_oracle_head = prediction["pre_oracle_head"]
        historical_protocol = _pre_oracle_blob(
            root, pre_oracle_head, _FLOOR_PROTOCOL_REL, label="floor protocol",
        )
        if historical_protocol != captured[_FLOOR_PROTOCOL_REL]:
            raise FloorCampaignError(
                "launch refusal: floor protocol が pre_oracle_head/worktree で不一致"
            )
        parser_sha256 = hashlib.sha256(_pre_oracle_blob(
            root, pre_oracle_head, _SELECTOR_PARSER_REL,
            label="selector parser module",
        )).hexdigest()
        known_cells = frozenset(
            (row["target_holdout"], row["arm"]) for row in rows
        )
        _prediction_runner.resolve_journal_for_launch(
            records,
            expected_header={
                "pre_oracle_head": pre_oracle_head,
                "protocol_sha256": hashlib.sha256(historical_protocol).hexdigest(),
                "freeze_sha256": freeze_sha256,
                "role_file_sha256": prediction["sources"]["role"]["sha256"],
                "parser_module_sha256": parser_sha256,
            },
            known_cells=known_cells,
            prediction_rows_by_cell={
                (row["target_holdout"], row["arm"]): row for row in rows
            },
        )
        # 単位 A の正本 helper が宣言集合と filesystem 集合の双方向 exact を検査する。
        _prediction_runner._assert_selector_run_declarations_from_validated_records(
            root=root, journal=journal, records=records,
        )
    except (IndexError, KeyError, TypeError,
            _prediction_runner.PredictionRunnerError) as exc:
        raise FloorCampaignError(
            f"launch refusal: selector journal 宣言検証不通過: {exc}"
        ) from exc

    allowlist = {
        _HOLDOUT_FREEZE_REL: freeze_sha256,
        _FLOOR_PROTOCOL_REL: protocol_sha256,
        _SELECTOR_PREDICTIONS_REL: hashlib.sha256(prediction_bytes).hexdigest(),
        _SELECTOR_JOURNAL_REL: hashlib.sha256(
            captured[_SELECTOR_JOURNAL_REL]
        ).hexdigest(),
    }

    def declare(rel: str, expected_sha256: str) -> None:
        if rel in allowlist:
            raise FloorCampaignError(
                f"launch refusal: selector journal 宣言 path が重複: {rel}"
            )
        try:
            actual = hashlib.sha256(read_bytes(root / rel)).hexdigest()
        except OSError as exc:
            raise FloorCampaignError(
                f"launch refusal: selector 宣言 artifact を読めない: {rel}: {exc}"
            ) from exc
        if actual != expected_sha256:
            raise FloorCampaignError(
                f"launch refusal: selector 宣言 artifact sha256 が不一致: {rel}"
            )
        allowlist[rel] = expected_sha256

    for record in records:
        record_type = record.get("record_type")
        if record_type == "claim":
            declare(record["payload_path"], record["input_payload_sha256"])
        elif record_type == "invocation":
            declare(record["raw_response_path"], record["raw_sha256"])
        elif record_type == "envelope":
            declare(record["envelope_path"], record["envelope_sha256"])
    return _freeze_hold.result_with_markers(allowlist, held_checks)


class _CapturedSelectorJournal:
    """単位 A helper へ captured records を渡し、journal path の再読を防ぐ view。"""

    def __init__(self, path: Path, records: list[dict]) -> None:
        self.path = Path(path)
        self._records = records

    def read_records(self) -> list[dict]:
        return list(self._records)


def _parse_selector_journal_bytes(raw: bytes) -> list[dict]:
    """captured journal bytes を duplicate-key/非有限数拒否で parse する。"""
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise FloorCampaignError("selector journal が UTF-8 でない") from exc
    records = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(
                line, object_pairs_hook=_no_duplicate_pairs,
                parse_constant=_reject_json_constant,
            )
        except (json.JSONDecodeError, FloorCampaignError) as exc:
            raise FloorCampaignError(
                f"selector journal 行 {index} を strict parse できない: {exc}"
            ) from exc
        if not isinstance(record, dict):
            raise FloorCampaignError(f"selector journal 行 {index} が object でない")
        records.append(record)
    if not records:
        raise FloorCampaignError("selector journal に run_header がない")
    return records


def _validate_freeze_allowlist_path(rel: object) -> str:
    """allowlist の raw POSIX relative path を正規化せず検証する。"""
    if not isinstance(rel, str) or not rel:
        raise FloorCampaignError(
            f"launch certificate: freeze_allowlist path が不正: {rel!r}"
        )
    try:
        rel.encode("utf-8")
    except UnicodeError as exc:
        raise FloorCampaignError(
            f"launch certificate: freeze_allowlist path が UTF-8 でない: {rel!r}"
        ) from exc
    components = rel.split("/")
    if (rel.startswith("/") or rel.endswith("/") or "//" in rel
            or "\\" in rel or "." in components or ".." in components
            or any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in rel)):
        raise FloorCampaignError(
            f"launch certificate: freeze_allowlist path が不正: {rel!r}"
        )
    if not (rel in _PREFLIGHT_FIXED_FILES
            or rel.startswith(_SELECTOR_RUNS_REL + "/")):
        raise FloorCampaignError(
            f"launch certificate: freeze_allowlist path が有界範囲外: {rel!r}"
        )
    return rel


def _assert_freeze_allowlist(
    root: Path, freeze_allowlist: Mapping,
) -> dict[str, str]:
    """freeze namespace 全 file を固定/selector/chain の3集合で被覆する。"""
    if not isinstance(freeze_allowlist, Mapping):
        raise FloorCampaignError("launch certificate: freeze_allowlist が Mapping でない")
    for rel, expected in freeze_allowlist.items():
        _validate_freeze_allowlist_path(rel)
        if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
            raise FloorCampaignError(
                f"launch certificate: freeze_allowlist sha256 が不正: {rel!r}"
            )

    bounded_actual: set[str] = set()
    chain_records: dict[str, str] = {}
    try:
        for rel in ("output", "output/s8b-freeze"):
            directory = root / rel
            if directory.is_symlink():
                raise FloorCampaignError(
                    f"launch certificate: preflight 親が symlink: {rel}"
                )
            if directory.exists() and not directory.is_dir():
                raise FloorCampaignError(
                    f"launch certificate: preflight 親が実 directory でない: {rel}"
                )
        namespace_root = root / "output/s8b-freeze"
        if namespace_root.is_dir():
            for path in sorted(namespace_root.rglob("*"), key=lambda item: item.as_posix()):
                rel = path.relative_to(root).as_posix()
                if path.is_symlink():
                    raise FloorCampaignError(
                        f"launch certificate: freeze namespace に symlink がある: {rel}"
                    )
                if path.is_dir():
                    continue
                if not path.is_file():
                    raise FloorCampaignError(
                        f"launch certificate: freeze namespace に非通常 file がある: {rel}"
                    )
                if (rel in _PREFLIGHT_FIXED_FILES
                        or rel.startswith(_SELECTOR_RUNS_REL + "/")):
                    bounded_actual.add(rel)
                elif any(pattern.fullmatch(rel) for pattern in _CHAIN_RECORD_PATTERNS):
                    chain_records[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
                else:
                    raise FloorCampaignError(
                        f"launch certificate: freeze namespace に未知 file がある: {rel}"
                    )
        expected_paths = set(freeze_allowlist)
        if bounded_actual != expected_paths:
            raise FloorCampaignError(
                "launch certificate: preflight scope と allowlist が不一致: "
                f"missing={sorted(expected_paths - bounded_actual)} "
                f"undeclared={sorted(bounded_actual - expected_paths)}"
            )
        for rel, expected in freeze_allowlist.items():
            path = root / rel
            if path.is_symlink() or not path.is_file():
                raise FloorCampaignError(
                    f"launch certificate: freeze allowlist phantom entry: {rel}"
                )
            actual_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual_sha256 != expected:
                raise FloorCampaignError(
                    "launch certificate: freeze allowlist hash 不一致: "
                    f"{rel}"
                )
    except FloorCampaignError:
        raise
    except OSError as exc:
        raise FloorCampaignError(
            f"launch certificate: output/s8b-freeze を検査できない: {exc}"
        ) from exc
    return chain_records


def clean_scan_digest(root: Path, *, freeze_allowlist: Mapping) -> str:
    """発行時点の clean scan を証明する: holdout hit 0 件 + 列挙 digest を返す (fail-closed)。

    同じ列挙集合を search_repository へ注入し、共有 _assert_search_pass で holdout 全件 0 hit・
    holdout 集合完全性・陽性対照を検査する。走査後に再列挙して名前集合の変化も拒否する。
    search_repository が除外する output/s8b-freeze は tracked/untracked を問わず全列挙し、
    固定4 file・journal 宣言 selector-runs・既存命名規則の chain record の3集合で被覆する。
    未知 file と全集合の symlink は拒否し、chain record も path + bytes hash を digest に含める。

    既知 residual: allowlist file は path→sha256 を束縛するが、走査中に同名 file の内容を交換して
    検査後に戻す content TOCTOU はこの証明範囲外である。
    """
    root = Path(root)
    try:
        files_before = _holdout_freeze.enumerate_repository_files(root)
        report = _holdout_freeze.search_repository(root, files=files_before)
        _holdout_freeze._assert_search_pass(report)
        chain_records = _assert_freeze_allowlist(root, freeze_allowlist)
        files_after = _holdout_freeze.enumerate_repository_files(root)
    except _holdout_freeze.FreezeError as exc:
        raise FloorCampaignError(f"launch certificate: clean scan 拒否: {exc}") from exc
    if files_before != files_after:
        raise FloorCampaignError(
            "launch certificate: repository file 列挙が走査中に変化した"
        )
    namespace_allowlist = {**freeze_allowlist, **chain_records}
    preimage = {
        "schema": "s8b-clean-scan-digest/v3",
        "repository_files": list(files_before),
        "freeze_allowlist": [
            {"path": path, "sha256": namespace_allowlist[path]}
            for path in sorted(namespace_allowlist)
        ],
    }
    try:
        canonical = json.dumps(
            preimage, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise FloorCampaignError(
            f"launch certificate: clean scan digest preimage を構成できない: {exc}"
        ) from exc
    return hashlib.sha256(canonical).hexdigest()


def build_launch_certificate(*, v1_freeze_sha256: str, clean_digest: str,
                             protocol_sha256: str, started_utc: str,
                             campaign_run_id: str) -> dict:
    """official floor 開始時の launch certificate を組み立てる (純粋、C2-2)。

    {v1_freeze_sha256, clean_scan_digest, protocol_sha256, started_utc, campaign_run_id}
    を束ねる。certificate 自身の bytes sha256 を campaign-start record が束縛し、v2 closure は
    この certificate 起点の lineage から導出する (certificate 以前に削除された痕跡は原理的に
    検出不能 — §5-viii の限界)。"""
    return {
        "schema": LAUNCH_CERT_SCHEMA,
        "v1_freeze_sha256": v1_freeze_sha256,
        "clean_scan_digest": clean_digest,
        "protocol_sha256": protocol_sha256,
        "started_utc": started_utc,
        "campaign_run_id": campaign_run_id,
    }


def validate_launch_certificate(cert: Mapping, *, expected_v1_freeze_sha256: str,
                                expected_protocol_sha256: str,
                                expected_run_id: str) -> dict:
    """共有 leaf の拒否を既存 FloorCampaignError API へ翻訳する。"""
    try:
        return _validate_launch_certificate(
            cert,
            expected_v1_freeze_sha256=expected_v1_freeze_sha256,
            expected_protocol_sha256=expected_protocol_sha256,
            expected_run_id=expected_run_id,
        )
    except LaunchCertError as exc:
        raise FloorCampaignError(str(exc)) from exc


def validate_launch_certificate_strict(
        cert: Mapping, *, expected_v1_freeze_sha256: str,
        expected_clean_scan_digest: str, expected_protocol_sha256: str,
        expected_run_id: str) -> dict:
    """共有 strict leaf の拒否を既存 FloorCampaignError API へ翻訳する。"""
    try:
        return _validate_launch_certificate_strict(
            cert,
            expected_v1_freeze_sha256=expected_v1_freeze_sha256,
            expected_clean_scan_digest=expected_clean_scan_digest,
            expected_protocol_sha256=expected_protocol_sha256,
            expected_run_id=expected_run_id,
        )
    except LaunchCertError as exc:
        raise FloorCampaignError(str(exc)) from exc


def _official_launch_preflight(root: Path, *, v1_freeze_sha256: str,
                               protocol_sha256: str, started_utc: str,
                               campaign_run_id: str,
                               freeze_allowlist: Mapping) -> tuple[dict, str]:
    """発行前に独立2回 scan し、2回目を strict expected として返す。"""
    first_clean_digest = clean_scan_digest(
        Path(root), freeze_allowlist=freeze_allowlist,
    )
    certificate = build_launch_certificate(
        v1_freeze_sha256=v1_freeze_sha256,
        clean_digest=first_clean_digest,
        protocol_sha256=protocol_sha256,
        started_utc=started_utc,
        campaign_run_id=campaign_run_id,
    )
    expected_clean_scan_digest = clean_scan_digest(
        Path(root), freeze_allowlist=freeze_allowlist,
    )
    validate_launch_certificate_strict(
        certificate,
        expected_v1_freeze_sha256=v1_freeze_sha256,
        expected_clean_scan_digest=expected_clean_scan_digest,
        expected_protocol_sha256=protocol_sha256,
        expected_run_id=campaign_run_id,
    )
    return certificate, expected_clean_scan_digest


def issue_launch_certificate(
        cert_path: Path, certificate: Mapping,
        *, write_capability: Optional[WriteCapability] = None) -> str:
    """certificate を create-only で発行し、その bytes sha256 (journal 束縛値) を返す。"""
    cert_bytes = _write_create_only_json(
        Path(cert_path), certificate, write_capability=write_capability,
    )
    return hashlib.sha256(cert_bytes).hexdigest()


def _revalidate_issued_certificate(
        cert_path: Path, *, expected_v1_freeze_sha256: str,
        expected_clean_scan_digest: str, expected_protocol_sha256: str,
        expected_run_id: str) -> tuple[dict, bytes]:
    """発行済み raw bytes を strict parse し、同じ exact validator へ再投入する。"""
    try:
        raw = Path(cert_path).read_bytes()
        document = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_no_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, FloorCampaignError) as exc:
        raise FloorCampaignError(
            f"発行済み launch certificate を strict 再検証できない: {exc}") from exc
    normalized = validate_launch_certificate_strict(
        document,
        expected_v1_freeze_sha256=expected_v1_freeze_sha256,
        expected_clean_scan_digest=expected_clean_scan_digest,
        expected_protocol_sha256=expected_protocol_sha256,
        expected_run_id=expected_run_id,
    )
    return normalized, raw


# --------------------------------------------------------------------------- #
# content-addressed binary store (C3-7) — 計測 bytes を hash 名で永続化         #
# --------------------------------------------------------------------------- #

def _runtime_built_keys_for(
        configuration_id: object, *, stored: bool,
        fetchcontent: bool) -> frozenset[str]:
    """runtime binary record の条件付き exact key 集合を返す。"""
    if type(stored) is not bool or type(fetchcontent) is not bool:
        raise FloorCampaignError("runtime binary key selector が exact bool でない")
    keys = _binary_admission.portable_built_keys_for(configuration_id)
    if not stored:
        keys = keys - {"store_path"}
    keys = keys | {"_ccbench_root"}
    if fetchcontent:
        keys = keys | {"_fetchcontent_base_dir"}
    return frozenset(keys)


def _preflight_runtime_store_record(
        cell_id: str, rec: object, *, store_root: Path,
        expected_policy, expected_ccbench_pin: str,
        expected_contract_sha256: str,
) -> tuple[Mapping, Path]:
    """Store 書込み前に runtime record 全体と admission を検査する。"""
    if not isinstance(cell_id, str) or not cell_id:
        raise FloorCampaignError("binary store runtime cell key が不正")
    if not isinstance(rec, Mapping):
        raise FloorCampaignError(f"binary store runtime record が Mapping でない: {cell_id}")
    keys = frozenset(rec)
    configuration_id = rec.get("configuration_id")
    stored = "store_path" in rec
    fetchcontent = "_fetchcontent_base_dir" in rec
    expected_runtime_keys = _runtime_built_keys_for(
        configuration_id, stored=stored, fetchcontent=fetchcontent,
    )
    expected_portable_keys = _binary_admission.portable_built_keys_for(
        configuration_id,
    )
    if keys != expected_runtime_keys and not (
            stored and not fetchcontent and keys == expected_portable_keys):
        raise FloorCampaignError(
            f"binary store runtime record の exact key 集合が不一致: cell={cell_id}"
        )
    if rec.get("cell_id") != cell_id:
        raise FloorCampaignError(
            f"binary store runtime record.cell_id が key と不一致: cell={cell_id}"
        )
    has_fetchcontent_base = "_fetchcontent_base_dir" in rec
    is_sort_best = rec.get("configuration_id") == "sort_best"
    if has_fetchcontent_base and not is_sort_best:
        raise FloorCampaignError(
            "binary store runtime record._fetchcontent_base_dir は "
            f"sort_best にだけ許可される: cell={cell_id}"
        )
    for field in ("holdout_id", "configuration_id"):
        if type(rec.get(field)) is not str or not rec[field]:
            raise FloorCampaignError(
                f"binary store runtime record.{field} が不正: cell={cell_id}"
            )
    binary = rec.get("binary")
    if type(binary) is not str or not binary or not Path(binary).is_absolute():
        raise FloorCampaignError(
            f"binary store runtime record.binary が絶対 path でない: cell={cell_id}"
        )
    sha = rec.get("binary_sha256")
    if not buildcache.is_full_sha256(sha):
        raise FloorCampaignError(
            f"binary store runtime record.binary_sha256 が不正: cell={cell_id}"
        )
    if rec.get("bin_hash_short") != sha[:16]:
        raise FloorCampaignError(
            f"binary store runtime record.bin_hash_short が不一致: cell={cell_id}"
        )
    for field in ("configure_argv", "build_argv"):
        argv = rec.get(field)
        if (type(argv) is not list or not argv
                or any(type(token) is not str or not token for token in argv)):
            raise FloorCampaignError(
                f"binary store runtime record.{field} が非空 list[str] でない: "
                f"cell={cell_id}"
            )
    if type(rec.get("cached")) is not bool:
        raise FloorCampaignError(
            f"binary store runtime record.cached が bool でない: cell={cell_id}"
        )
    if "_ccbench_root" in rec:
        ccbench_root = rec["_ccbench_root"]
        if (type(ccbench_root) is not str or not ccbench_root
                or not Path(ccbench_root).is_absolute()):
            raise FloorCampaignError(
                f"binary store runtime record._ccbench_root が絶対 path でない: "
                f"cell={cell_id}"
            )
    if "_fetchcontent_base_dir" in rec:
        fetchcontent_base = rec["_fetchcontent_base_dir"]
        if (type(fetchcontent_base) is not str or not fetchcontent_base
                or not Path(fetchcontent_base).is_absolute()
                or Path(fetchcontent_base).is_symlink()
                or not Path(fetchcontent_base).is_dir()
                or Path(fetchcontent_base).absolute() != Path(fetchcontent_base).resolve()):
            raise FloorCampaignError(
                "binary store runtime record._fetchcontent_base_dir が canonical "
                f"absolute directory でない: cell={cell_id}"
            )
    dest = Path(store_root) / sha
    if "store_path" in rec:
        store_path = rec["store_path"]
        if (type(store_path) is not str or not Path(store_path).is_absolute()
                or Path(store_path) != dest.absolute()):
            raise FloorCampaignError(
                f"binary store runtime record.store_path が content address と不一致: "
                f"cell={cell_id}"
            )
    projected = dict(rec)
    projected.pop("_ccbench_root", None)
    projected.pop("_fetchcontent_base_dir", None)
    projected["store_path"] = str(dest.absolute())
    try:
        _binary_admission.validate_portable_binary_record(
            projected, expected_policy=expected_policy,
            expected_ccbench_pin=expected_ccbench_pin,
            expected_contract_sha256=expected_contract_sha256,
            expected_cell_id=cell_id,
            expected_holdout_id=rec["holdout_id"],
            expected_configuration_id=rec["configuration_id"],
        )
    except _binary_admission.BinaryAdmissionError as exc:
        raise FloorCampaignError(
            f"binary store preflight admission 不一致: cell={cell_id}: {exc}"
        ) from exc
    return rec, dest


def store_binaries(
        built: dict, store_root: Path, *, out_root: Path,
        expected_ccbench_pin: str, expected_contract_sha256: str,
        write_capability: Optional[WriteCapability] = None) -> None:
    """計測に使う binary bytes を store_root/<sha256> へ create-only 複製する (C3-7)。

    既に同 hash の store が在れば内容 hash を照合するだけ (冪等)。各 built rec に out_root
    相対の store_path を書き込む。oracle 側の消費 (run marker 前の存在+hash 検査) は W4。"""
    store_root = Path(store_root)
    out_root = Path(out_root)
    current_policy = resolve_current_build_admission_policy()
    preflight: list[tuple[dict, str, Path, Path, bytes | None]] = []
    for cell_id in sorted(built):
        rec, dest = _preflight_runtime_store_record(
            cell_id, built[cell_id], store_root=store_root,
            expected_policy=current_policy,
            expected_ccbench_pin=expected_ccbench_pin,
            expected_contract_sha256=expected_contract_sha256,
        )
        sha = rec["binary_sha256"]
        src = Path(rec["binary"])
        try:
            data = src.read_bytes()
        except OSError as exc:
            raise FloorCampaignError(f"store 対象 binary を読めない: {src}: {exc}") from exc
        actual_source_sha256 = hashlib.sha256(data).hexdigest()
        if actual_source_sha256 != sha:
            raise FloorCampaignError(
                f"store 対象 binary の sha256 が build 記録と不一致: {src}"
            )
        if dest.exists():
            actual = _full_sha256(dest)
            if actual != sha:
                raise FloorCampaignError(
                    f"binary store 破損: {dest} の sha256={actual} != {sha}"
                )
            data = None
        preflight.append((rec, sha, src, dest, data))

    store_root.mkdir(parents=True, exist_ok=True)
    for rec, sha, src, dest, data in preflight:
        if data is not None:
            tmp = store_root / f".{sha}.tmp.{os.getpid()}"
            opener = (
                open_with_write_capability(write_capability, tmp, "xb")
                if write_capability is not None else open(tmp, "xb")
            )
            with opener as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(tmp, dest)
            except FileExistsError:
                pass  # 並走で先に作られた (content-addressed なので同一 bytes)
            finally:
                tmp.unlink(missing_ok=True)
            actual = _full_sha256(dest)
            if actual != sha:
                raise FloorCampaignError(f"store 書込後 hash 不一致: {dest} sha256={actual}")
        rec["store_path"] = str(dest.absolute())


def _verify_resume_store(
        built: Mapping, out_root: Path, *, expected_ccbench_pin: str | None = None,
        expected_contract_sha256: str | None = None,
) -> None:
    """resume: 記録済み store_path が存在し、その bytes sha256 が binary_sha256 と一致する。"""
    out_root = Path(out_root)
    current_policy = resolve_current_build_admission_policy()
    for cell_id in sorted(built):
        rec = built[cell_id]
        store_path = rec.get("store_path")
        sha = rec.get("binary_sha256")
        if not isinstance(store_path, str) or not store_path:
            # v2 の store_binaries は常に store_path を書くため、欠落は改竄か
            # store 前 manifest の混入 — 正当な消費者のない緩和を置かない (fail-closed)。
            raise FloorCampaignError(f"resume: store_path 欠落: {cell_id}")
        try:
            _binary_admission.validate_portable_binary_record(
                rec, expected_policy=current_policy,
                expected_ccbench_pin=expected_ccbench_pin,
                expected_contract_sha256=expected_contract_sha256,
                expected_cell_id=cell_id,
                expected_holdout_id=rec.get("holdout_id"),
                expected_configuration_id=rec.get("configuration_id"),
            )
        except _binary_admission.BinaryAdmissionError as exc:
            raise FloorCampaignError(
                f"resume: admission receipt 不一致: cell={cell_id}: {exc}"
            ) from exc
        candidate = Path(store_path)
        if not candidate.is_absolute():
            candidate = out_root / store_path
        if not candidate.is_file():
            raise FloorCampaignError(f"resume: store 欠落: {store_path}")
        actual = _full_sha256(candidate)
        if actual != sha:
            raise FloorCampaignError(
                f"resume: store bytes sha256 が binary_sha256 と不一致 (store={actual} rec={sha})"
            )


# --------------------------------------------------------------------------- #
# session 実行エンジン (fresh/resume 共通)                                      #
# --------------------------------------------------------------------------- #

def _project_measure_run_cmd(
        raw_run_cmd, *, runtime_binary: str, portable_binary: str,
        workload: Mapping, records: int, threads: int, protocol: Mapping,
        contract: _env_contract.ExecutionEnvironmentContract,
        perf_preflight=None, mode: str = "official") -> str:
    """production raw command を完全照合し portable canonical command へ射影する。

    calibrator は workload Mapping の挿入順で末尾 flag を出すため、raw 側では workload
    flag の順序だけを非意味的差として許す。それ以外の prefix・perf event・binary・基本
    flag・token 数は完全一致を要求する。artifact 側は leaf の確定順へ必ず正規化する。
    """
    if (type(contract) is not _env_contract.ExecutionEnvironmentContract
            or contract.env_tag != protocol["env_tag"]
            or contract.contract_sha256 != protocol["contract_sha256"]):
        raise CampaignAbort("measure run_cmd の env contract が protocol と不一致")
    use_perf = _assert_perf_mode(mode, perf_preflight)
    try:
        portable = build_portable_run_cmd(
            binary=portable_binary, workload=workload, records=records,
            threads=threads, extime_s=protocol["extime_s"],
            clocks_per_us=contract.clocks_per_us, numactl=contract.numactl,
            use_perf=use_perf,
        )
    except _floor_contract.FloorContractError as exc:
        raise CampaignAbort(f"portable run_cmd を構築できない: {exc}") from exc
    if not isinstance(raw_run_cmd, str) or not raw_run_cmd:
        raise CampaignAbort("measure が空でない raw run_cmd を返さなかった")
    try:
        raw_argv = tuple(shlex.split(raw_run_cmd))
    except ValueError as exc:
        raise CampaignAbort(f"measure raw run_cmd を shlex parse できない: {exc}") from exc

    runtime_expected = list(portable)
    if use_perf:
        try:
            binary_index = runtime_expected.index("--") + 1
        except ValueError as exc:  # leaf の内部契約破れ。安全側に停止する。
            raise CampaignAbort("portable run_cmd に binary separator がない") from exc
    else:
        binary_index = len(contract.numactl)
    runtime_expected[binary_index] = runtime_binary
    workload_count = len(workload)
    prefix_length = len(runtime_expected) - workload_count
    if (len(raw_argv) != len(runtime_expected)
            or raw_argv[:prefix_length] != tuple(runtime_expected[:prefix_length])
            or sorted(raw_argv[prefix_length:]) != sorted(runtime_expected[prefix_length:])):
        raise CampaignAbort(
            "measure raw run_cmd が runtime binary/workload/protocol/env contract と不一致"
        )
    return shlex.join(portable)


def _wrap_admission_aware_measure(
        measure_fn, *, admissions, cell_by_id, binaries, protocol,
        freeze_sha256, protocol_sha256, manifest_sha256,
        assert_admission_fn=None, consume_ticket_fn=None,
        pass_observation_to_internal_measure=False):
    """Keep the external four-argument seam behind attempt consumption."""

    if set(admissions) != set(cell_by_id):
        raise CampaignAbort("holdout admission mapping does not exactly cover cells")
    assert_admission_fn = (
        _holdout_admission.assert_cell_holdout_admission
        if assert_admission_fn is None else assert_admission_fn
    )
    consume_ticket_fn = (
        _holdout_admission.consume_attempt_ticket
        if consume_ticket_fn is None else consume_ticket_fn
    )

    def measure_attempt(cell_id, attempt_id, binary, records, threads, workload):
        cell = cell_by_id.get(cell_id)
        admission = admissions.get(cell_id)
        binary_record = binaries.get(cell_id)
        if cell is None or admission is None or binary_record is None:
            raise CampaignAbort(f"holdout admission is absent: cell={cell_id}")
        if (binary != binary_record.get("binary")
                or records != cell.get("records")
                or threads != cell.get("threads")
                or workload != cell.get("workload")):
            raise CampaignAbort(
                f"measure callback coordinates differ from frozen cell: {cell_id}"
            )
        try:
            assert_admission_fn(
                admission, cell=_admission_cell(cell), protocol=protocol,
                freeze_sha256=freeze_sha256,
                protocol_sha256=protocol_sha256,
                manifest_sha256=manifest_sha256,
            )
            observation = consume_ticket_fn(
                admission, attempt_id=attempt_id,
            )
        except _holdout_admission.HoldoutAdmissionError as exc:
            raise CampaignAbort(
                f"holdout attempt admission refused: cell={cell_id}: {exc}"
            ) from exc
        # No operation may be inserted between durable consumption and this
        # external four-argument callback.
        if pass_observation_to_internal_measure:
            return measure_fn(
                binary, records, threads, workload,
                _holdout_observation_admission=observation,
            )
        return measure_fn(binary, records, threads, workload)

    return measure_attempt


def _admission_cell(cell: Mapping[str, object]) -> dict[str, object]:
    """Translate the legacy floor artifact name only at the admission boundary."""

    return {
        "cell_id": cell.get("cell_id"),
        "freeze_holdout_key": cell.get("holdout_id"),
        "configuration_id": cell.get("configuration_id"),
        "records": cell.get("records"),
        "threads": cell.get("threads"),
        "workload": dict(cell.get("workload", {})),
    }


class _Runner:
    """schedule を直列・単一テナントで消化する実行エンジン (fresh/resume 共通)。

    臨界区間は session ごとに ``session-start (=authorization) → probe → measure → post-probe →
    session (end)`` を journal へ即時記録する。crash した session は start だけが残り、resume では
    admission が cut 6 の M+A- を証明した planned attempt だけ同じ authorization で再開し、
    それ以外は **terminal (再実行しない)** 扱いにする。retry の枠消費は authorization
    (session-start) の fsync 時点で確定し、(cell_id, retry_ordinal) は resume を跨いで再発行しない
    (β-5)。retry は失敗が起きた round の末尾で schedule 順に消化する (β-4)。
    """

    def __init__(self, *, protocol, contract, cells, cell_by_id, binaries,
                 artifact_binaries, schedule,
                 journal_path, measure_fn, holdout_admissions,
                 probe_fn, sleep_fn, monotonic_fn, now_fn,
                 protocol_sha256, freeze_sha256, manifest_sha256,
                 execution_receipt=None, launch_certificate_sha256=None,
                 records=None, host_provenance_fn=None, process_identity_fn=None,
                 reservation_check=None, write_capability=None,
                 perf_preflight=None, mode="official",
                 holdout_assert_fn=None, external_checkpoint_binding=None,
                 cut6_replay_query_fn=None, retry_trigger_query_fn=None, certified_attempt_context=None):
        self.protocol = protocol
        self.contract = contract
        self.cells = cells
        self.cell_by_id = cell_by_id
        self.binaries = binaries
        self.artifact_binaries = artifact_binaries
        self.schedule = schedule
        self.journal_path = journal_path
        self.measure_fn = measure_fn
        if not isinstance(holdout_admissions, Mapping):
            raise CampaignAbort("holdout admission mapping is required")
        self.holdout_admissions = dict(holdout_admissions)
        self.holdout_assert_fn = (
            _holdout_admission.assert_cell_holdout_admission
            if holdout_assert_fn is None else holdout_assert_fn
        )
        self.cut6_replay_query_fn = (
            _holdout_admission.floor_attempt_requires_cut6_replay
            if cut6_replay_query_fn is None else cut6_replay_query_fn
        )
        self.retry_trigger_query_fn = (
            _holdout_admission.floor_retry_trigger_for_round
            if retry_trigger_query_fn is None else retry_trigger_query_fn
        )
        self.probe_fn = probe_fn
        self.sleep_fn = sleep_fn
        self.monotonic_fn = monotonic_fn
        self.now_fn = now_fn
        self.protocol_sha256 = protocol_sha256
        self.freeze_sha256 = freeze_sha256
        self.manifest_sha256 = manifest_sha256
        # C3-10: 共有 execution guard の receipt (campaign-start journal に記録)。
        self.execution_receipt = execution_receipt
        self.launch_certificate_sha256 = launch_certificate_sha256
        self.host_provenance_fn = host_provenance_fn or _host_provenance
        self.process_identity_fn = process_identity_fn or _process_identity
        self.reservation_check = reservation_check
        self.external_checkpoint_binding = (
            None if external_checkpoint_binding is None
            else dict(external_checkpoint_binding)
        )
        self.write_capability = write_capability
        self.mode = _validate_mode(mode)
        self.perf_preflight = perf_preflight
        self.use_perf = _assert_perf_mode(self.mode, self.perf_preflight)
        self.reps = protocol["reps"]
        self.session_cv_max = protocol["session_cv_max"]
        self.retry_slots = protocol["retry_slots_per_cell"]
        self.allowed_reasons = set(protocol["allowed_excluded_reasons"])
        self.records = (_read_journal(journal_path) if records is None
                        else [dict(record) for record in records])
        self._retry_authorization_cache, self.certified_attempt_context = {}, certified_attempt_context

    # --- journal I/O ----------------------------------------------------- #

    def _emit(self, record: dict) -> None:
        _journal_append(
            self.journal_path, record, write_capability=self.write_capability,
        )
        self.records.append(record)

    def _check_reason(self, reason: str) -> str:
        if reason not in self.allowed_reasons:
            raise CampaignAbort(
                f"excluded_reason ({reason!r}) が allowed_excluded_reasons に無い "
                "(閉じた表と protocol の不一致, fail-closed)"
            )
        return reason

    # --- attempt registry / retry 予算 (fsync 時点で消費) ----------------- #

    def _authorized_retry_ordinals(self, cell_id: str) -> set:
        """当該セルで authorization (session-start) 済みの retry_ordinal 集合。crash した
        authorization も含む (枠消費は session-start の fsync 時点, β-5)。"""
        return {r.get("retry_ordinal") for r in self.records
                if r.get("event") == "session-start" and r.get("kind") == "retry"
                and r.get("cell_id") == cell_id and r.get("retry_ordinal") is not None}

    def _authorized_retries(self, cell_id: str) -> int:
        return len(self._authorized_retry_ordinals(cell_id))

    def _next_retry_ordinal(self, cell_id: str) -> int:
        used = self._authorized_retry_ordinals(cell_id)
        return (max(used) + 1) if used else 1

    def _started_seqs(self) -> set:
        return {r["seq"] for r in self.records if r.get("event") == "session-start"}

    def _next_retry_seq(self) -> int:
        seqs = [r["seq"] for r in self.records
                if r.get("event") in {"session", "session-start"} and "seq" in r]
        base = len(self.schedule) - 1
        return max(seqs + [base]) + 1

    def _completed_rounds(self) -> set:
        return {r["round"] for r in self.records if r.get("event") == "round-complete"}

    # --- round / cell の状態問い合わせ (journal から再構成) --------------- #

    def _round_rows(self, round_no: int) -> list[dict]:
        return [row for row in self.schedule if row["round"] == round_no]

    def _planned_seq(self, round_no: int, cell_id: str) -> Optional[int]:
        for row in self.schedule:
            if row["round"] == round_no and row["cell_id"] == cell_id:
                return row["seq"]
        return None

    def _planned_attempt_id(self, round_no: int, cell_id: str) -> Optional[str]:
        seq = self._planned_seq(round_no, cell_id)
        return None if seq is None else _attempt_id(cell_id, "planned", seq, None)

    def _round_failed_cells(self, round_no: int) -> list[str]:
        """Return schedule-ordered cells for which admission authorizes retry."""

        order = [row["cell_id"] for row in self._round_rows(round_no)]
        failed: list[str] = []
        for cell_id in order:
            if self._retry_authorization(round_no, cell_id) is not None:
                failed.append(cell_id)
        return failed

    def _retry_authorization(self, round_no: int, cell_id: str):
        key = (round_no, cell_id)
        if key in self._retry_authorization_cache:
            return self._retry_authorization_cache[key]
        try:
            authorization = self.retry_trigger_query_fn(
                self.holdout_admissions[cell_id], round_no=round_no,
            )
        except _holdout_admission.HoldoutAdmissionError as exc:
            raise CampaignAbort(
                f"retry trigger admission refused: cell={cell_id}: {exc}"
            ) from exc
        if authorization is not None and not isinstance(
            authorization, _holdout_admission.FloorRetryAuthorization,
        ):
            raise CampaignAbort("retry trigger admission returned an invalid verdict")
        self._retry_authorization_cache[key] = authorization
        return authorization

    def _cell_round_has_valid(self, cell_id: str, round_no: int) -> bool:
        return any(r.get("event") == "session" and r.get("cell_id") == cell_id
                   and r.get("round") == round_no and r.get("valid")
                   for r in self.records)

    # --- 1 session 実行 (precedence 固定, β-7) ---------------------------- #

    def _recheck_reservation_before_measurement(self) -> None:
        """未開始 schedule/retry 全体を再導出し、余裕喪失を terminal 化する。"""
        if self.reservation_check is None:
            return
        started = self._started_seqs()
        remaining_planned = sum(row["seq"] not in started for row in self.schedule)
        remaining_retries = sum(
            max(0, self.retry_slots - self._authorized_retries(cell["cell_id"]))
            for cell in self.cells
        )
        attempt_cap = (
            self.protocol["extime_s"] * self.protocol["reps"]
            + _FLOOR_VERIFY_CAP_PER_ATTEMPT_S
        )
        required_s = max(1, (remaining_planned + remaining_retries) * attempt_cap)
        try:
            self.reservation_check = self.reservation_check.recheck(
                required_s=required_s,
                safety_margin_s=_FLOOR_FINALIZE_RESERVE_S,
                monotonic_now_fn=self.monotonic_fn,
            )
        except reservation.ReservationError as exc:
            self._emit({
                "event": "terminal",
                "status": "reservation-lost",
                "reason": str(exc),
                "numeric_values_eligible": False,
                "bench_values": [],
            })
            # campaign terminal は retryable CampaignAbort に翻訳しない。呼び手は型で判別する。
            raise

    def _run_session(self, *, seq: int, round_no: int, cell_id: str, kind: str,
                     retry_ordinal: Optional[int], trigger: Optional[str],
                     _cut6_authorization_already_recorded: bool = False, _cut6_existing_consumption_marker: bool = False) -> dict:
        self._recheck_reservation_before_measurement()
        attempt_id = _attempt_id(cell_id, kind, seq, retry_ordinal)
        # authorization record: retry 枠はこの fsync 時点で消費される (crash しても再発行しない)。
        if not _cut6_authorization_already_recorded:
            self._emit({
                "event": "session-start", "seq": seq, "kind": kind,
                "cell_id": cell_id, "round": round_no,
                "retry_ordinal": retry_ordinal, "attempt_id": attempt_id,
                "trigger": trigger, "started_iso": self.now_fn().isoformat(),
            })
        start_mono = self.monotonic_fn()
        cell = self.cell_by_id[cell_id]
        binary = self.binaries[cell_id]["binary"]

        # binary receipt (C3-6): 実測直前に binary bytes を再 hash し build 記録と照合する。
        # 記録 (build 時 hash) と実測直前 hash が食い違えば差し替えの疑いで CampaignAbort。
        binary_record = self.binaries[cell_id]
        recorded_bin_sha = binary_record["binary_sha256"]
        measured_bin_sha = _full_sha256(Path(binary))
        if measured_bin_sha != recorded_bin_sha:
            raise CampaignAbort(
                f"binary receipt 不一致: cell={cell_id} 記録={recorded_bin_sha} "
                f"実測直前={measured_bin_sha} (計測 bytes 差し替えの疑い)"
            )
        if self.certified_attempt_context is not None: return _run_certified_floor_session(self, seq=seq, round_no=round_no, cell_id=cell_id, kind=kind, retry_ordinal=retry_ordinal, attempt_id=attempt_id, trigger=trigger, start_mono=start_mono, cut6_existing_consumption_marker=_cut6_existing_consumption_marker)
        # pre-probe: rc>1/OSError/parse 不能 → CampaignAbort。競合列挙 → competing_process。
        probe_before = strict_probe(self.probe_fn)
        if probe_before["competing"]:
            return self._finish_session(
                seq=seq, round_no=round_no, cell_id=cell_id, kind=kind,
                retry_ordinal=retry_ordinal, attempt_id=attempt_id, trigger=trigger,
                throughputs=[], exec_failures=0, excluded_reason=_REASON_COMPETING,
                rep_observations=[], rep_integrity_failures=None,
                assessed_median=None, session_cv=None,
                duration_s=self._elapsed(start_mono),
                probe_before=probe_before, probe_after=None, run_cmd=None,
                notes=["preflight probe 競合で計測をスキップ"],
                binary_sha256_at_measure=measured_bin_sha,
            )

        # measure を試みる。例外 (全 rep 起動不能) でも post-probe は finally 相当で必ず実行する。
        measure_error: Optional[BaseException] = None
        scale_point = None
        try:
            scale_point = self.measure_fn(
                cell_id, attempt_id, binary, cell["records"], cell["threads"],
                cell["workload"],
            )
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            measure_error = exc

        probe_after = strict_probe(self.probe_fn)  # 検査不能 → CampaignAbort (finally 相当)

        if scale_point is not None:
            projection = _project_scalepoint(
                scale_point, reps=self.reps, expected_use_perf=self.use_perf,
            )
            throughputs = projection["throughputs"]
            exec_failures = projection["exec_failures"]
            rep_observations = projection["rep_observations"]
            rep_integrity_failures = projection["rep_integrity_failures"]
            run_cmd = _project_measure_run_cmd(
                getattr(scale_point, "run_cmd", None),
                runtime_binary=binary,
                portable_binary=self.artifact_binaries[cell_id]["binary"],
                workload=cell["workload"], records=cell["records"],
                threads=cell["threads"], protocol=self.protocol,
                contract=self.contract,
                perf_preflight=self.perf_preflight, mode=self.mode,
            )
            notes = list(getattr(scale_point, "notes", []) or [])
        else:
            throughputs = []
            exec_failures = self.reps
            rep_observations = []
            rep_integrity_failures = None
            run_cmd = None
            notes = [f"measure 失敗: {type(measure_error).__name__}: "
                     f"{str(measure_error)[:200]}"]

        # 生値から表示 CV / 必然理由を導出 (stats の単一純関数, α-8)。理由の precedence 決定に使う。
        session_cv: Optional[float] = None
        assessed_median: Optional[float] = None
        derived_reason: Optional[str] = None
        if scale_point is not None:
            try:
                assessment = s8b_floor_stats.assess_session(
                    throughputs, reps=self.reps, session_cv_max=self.session_cv_max,
                )
            except s8b_floor_stats.FloorStatsError as exc:
                raise CampaignAbort(f"assess_session 内部不変条件破れ: {exc}") from exc
            session_cv = assessment.cv
            assessed_median = assessment.median
            derived_reason = assessment.required_reason

        # precedence: competing → launch → rep integrity → partial → performance → valid。
        if probe_after["competing"]:
            excluded_reason: Optional[str] = _REASON_COMPETING
        elif measure_error is not None:
            excluded_reason = _REASON_LAUNCH
        elif exec_failures >= self.reps:
            excluded_reason = _REASON_LAUNCH  # 全 rep 起動不能 (β-7)
        elif exec_failures > 0 and derived_reason is None:
            # 完全有限ベクトル + 起動失敗 note の矛盾状態。session は stats 側で必ず
            # 無効になる (exec_failures != 0) ため、閉表の理由なしで invalid になる
            # 行を作らない (レビュー所見)。
            excluded_reason = _REASON_LAUNCH
        elif (rep_integrity_failures and rep_integrity_failures > 0
              and derived_reason == _REASON_PARTIAL):
            excluded_reason = _REASON_PARTIAL
        else:
            excluded_reason = derived_reason  # None / partial / performance

        return self._finish_session(
            seq=seq, round_no=round_no, cell_id=cell_id, kind=kind,
            retry_ordinal=retry_ordinal, attempt_id=attempt_id, trigger=trigger,
            throughputs=throughputs, exec_failures=exec_failures,
            rep_observations=rep_observations,
            rep_integrity_failures=rep_integrity_failures,
            excluded_reason=excluded_reason, assessed_median=assessed_median,
            session_cv=session_cv,
            duration_s=self._elapsed(start_mono), probe_before=probe_before,
            probe_after=probe_after, run_cmd=run_cmd, notes=notes,
            binary_sha256_at_measure=measured_bin_sha,
        )

    def _elapsed(self, start_mono: float) -> float:
        """同一 process 内の monotonic 差 (γ-12: 絶対 monotonic は永続化しない)。"""
        return float(self.monotonic_fn() - start_mono)

    def _finish_session(self, *, seq, round_no, cell_id, kind, retry_ordinal, attempt_id,
                        trigger, throughputs, exec_failures, rep_observations,
                        rep_integrity_failures, excluded_reason, assessed_median,
                        session_cv, duration_s, probe_before, probe_after, run_cmd, notes,
                        binary_sha256_at_measure=None) -> dict:
        cell = self.cell_by_id[cell_id]
        reason = self._check_reason(excluded_reason) if excluded_reason is not None else None
        median = assessed_median if reason is None and exec_failures == 0 else None
        valid = median is not None
        exclusion_class = (
            reason if reason in {_REASON_COMPETING, _REASON_LAUNCH}
            else s8b_floor_stats.REP_INTEGRITY_EXCLUSION_CLASS
            if rep_integrity_failures is not None and rep_integrity_failures > 0
            else reason
        )
        record = {
            "event": "session", "kind": kind, "seq": seq, "round": round_no,
            "retry_ordinal": retry_ordinal, "attempt_id": attempt_id, "trigger": trigger,
            "cell_id": cell_id, "holdout_id": cell["holdout_id"],
            "configuration_id": cell["configuration_id"],
            "records": cell["records"], "threads": cell["threads"],
            "workload": cell["workload"],
            # --- SessionRecord と同じ key (verify_floor_artifact が再構成する) ---
            "throughputs": list(throughputs), "reps_expected": self.reps,
            "exec_failures": exec_failures, "excluded_reason": reason,
            "retry": (kind == "retry"),
            "rep_observations": [dict(observation) for observation in rep_observations],
            "rep_integrity_failures": rep_integrity_failures,
            # --- driver の付帯情報 (verify は無視する) ---
            "session_median": median, "valid": valid, "session_cv": session_cv,
            "exclusion_class": exclusion_class,
            "duration_s": duration_s, "run_cmd": run_cmd, "notes": list(notes or []),
            "probe_before": probe_before, "probe_after": probe_after,
            # binary receipt (C3-6): 実測直前に再計算した binary bytes の full sha256。
            "binary_sha256_at_measure": binary_sha256_at_measure,
        }
        self._emit(record)
        return record

    # --- retry (round 末尾で失敗セルを schedule 順に消化, β-4) ------------ #

    def _retry_round(self, round_no: int) -> None:
        for cell_id in self._round_failed_cells(round_no):
            authorization = self._retry_authorization(round_no, cell_id)
            if authorization is None:  # pragma: no cover - cache invariant
                raise CampaignAbort("retry authorization cache is inconsistent")
            # MUT-T1669-TRIGGER-FORWARD (retargeted from withdrawn A8).
            trigger = authorization.trigger_attempt_id
            # campaign 通算予算まで、first-authorized-valid で 1 本有効になるまで消化する。
            while (self._authorized_retries(cell_id) < self.retry_slots
                   and not self._cell_round_has_valid(cell_id, round_no)):
                self._run_session(
                    seq=self._next_retry_seq(), round_no=round_no, cell_id=cell_id,
                    kind="retry", retry_ordinal=self._next_retry_ordinal(cell_id),
                    trigger=trigger,
                )
                # MUT-T1669-ONE-ORDINAL (retargeted from withdrawn A8): one
                # verified recovery can authorize only this next ordinal.
                if authorization.source == "verified-registry-recovery":
                    break

    def _replay_cut6_start(self, start: Mapping[str, object]) -> bool:
        """Replay one existing authorization only on admission's exact verdict."""

        cell_id = str(start["cell_id"])
        attempt_id = str(start["attempt_id"])
        try:
            replay = self.cut6_replay_query_fn(
                self.holdout_admissions[cell_id], attempt_id=attempt_id,
            )
        except _holdout_admission.HoldoutAdmissionError as exc:
            raise CampaignAbort(
                f"cut-6 replay admission refused: cell={cell_id}: {exc}"
            ) from exc
        # MUT-T1669-CUT6-ADMISSION (retargeted from withdrawn A5): the runner
        # neither infers a crash type nor treats a truthy non-bool as proof.
        if type(replay) is not bool:
            raise CampaignAbort(
                "cut-6 replay admission returned an invalid verdict"
            )
        if not replay:
            return False
        self._run_session(
            seq=int(start["seq"]), round_no=int(start["round"]),
            cell_id=cell_id, kind=str(start["kind"]),
            retry_ordinal=start.get("retry_ordinal"),
            trigger=start.get("trigger"),
            _cut6_authorization_already_recorded=True, _cut6_existing_consumption_marker=True,
        )
        return True

    # --- campaign 実行 --------------------------------------------------- #

    def _validate_live_admissions(self) -> None:
        """public runner 実走前に全 cell を current protocol へ束縛する。"""
        expected_cell_ids = set(self.cell_by_id)
        if set(self.holdout_admissions) != expected_cell_ids:
            raise CampaignAbort(
                "holdout admission mapping does not exactly cover every cell"
            )
        for cell_id in sorted(expected_cell_ids):
            try:
                self.holdout_assert_fn(
                    self.holdout_admissions[cell_id],
                    cell=_admission_cell(self.cell_by_id[cell_id]),
                    protocol=self.protocol,
                    freeze_sha256=self.freeze_sha256,
                    protocol_sha256=self.protocol_sha256,
                    manifest_sha256=self.manifest_sha256,
                )
            except _holdout_admission.HoldoutAdmissionError as exc:
                raise CampaignAbort(
                    f"holdout admission receipt mismatch: cell={cell_id}: {exc}"
                ) from exc
        current_policy = resolve_current_build_admission_policy()
        for cell_id in sorted(self.binaries):
            record = self.binaries[cell_id]
            try:
                if not isinstance(record, Mapping):
                    raise _binary_admission.BinaryAdmissionError(
                        "runtime binary record が Mapping でない"
                    )
                configuration_id = record.get("configuration_id")
                portable_keys = _binary_admission.portable_built_keys_for(
                    configuration_id,
                )
                has_fetchcontent_base = "_fetchcontent_base_dir" in record
                runtime_keys = _runtime_built_keys_for(
                    configuration_id, stored=True,
                    fetchcontent=has_fetchcontent_base,
                )
                record_keys = frozenset(record)
                if record_keys not in {portable_keys, runtime_keys}:
                    raise _binary_admission.BinaryAdmissionError(
                        "runtime binary record の configuration 条件付き "
                        "exact key 集合が不一致"
                    )
                if (has_fetchcontent_base
                        and configuration_id != "sort_best"):
                    raise _binary_admission.BinaryAdmissionError(
                        "runtime binary record の FetchContent base は "
                        "sort_best にだけ許可される"
                    )
                portable_record = {
                    key: record[key] for key in portable_keys
                }
                _binary_admission.validate_portable_binary_record(
                    portable_record, expected_policy=current_policy,
                    expected_ccbench_pin=self.protocol["ccbench_pin"],
                    expected_contract_sha256=self.contract.contract_sha256,
                    expected_cell_id=cell_id,
                    expected_holdout_id=record.get("holdout_id"),
                    expected_configuration_id=record.get("configuration_id"),
                )
            except (AttributeError, _binary_admission.BinaryAdmissionError) as exc:
                raise CampaignAbort(
                    f"実測直前 admission receipt 不一致: cell={cell_id}: {exc}"
                ) from exc

    def run(self) -> None:
        self._validate_live_admissions()
        fresh = not any(r.get("event") == "campaign-start" for r in self.records)
        if fresh:
            host = _validate_host_provenance(
                self.host_provenance_fn(now_fn=self.now_fn))
            process = _validate_process_identity(self.process_identity_fn())
            self._emit({
                "event": "campaign-start", "schema": JOURNAL_SCHEMA,
                "protocol_sha256": self.protocol_sha256,
                "freeze_sha256": self.freeze_sha256,
                "manifest_sha256": self.manifest_sha256,
                **({"launch_certificate_sha256": self.launch_certificate_sha256}
                   if self.launch_certificate_sha256 is not None else {}),
                **host, **process,
                # C3-10: 共有 execution guard の receipt (env_tag + contract_sha256 +
                # 実行機 attestation)。report/verifier が env 契約と照合する。
                **({"execution_receipt": self.execution_receipt}
                   if self.execution_receipt is not None else {}),
                **({
                    "pbs_jobid": self.external_checkpoint_binding["job_id"],
                    "submission_nonce": self.external_checkpoint_binding["nonce"],
                } if self.external_checkpoint_binding is not None else {}),
            })
        else:
            # resume: 新 process の identity を記録する (γ-5)。result には含めない (決定性維持)。
            host = _validate_host_provenance(
                self.host_provenance_fn(now_fn=self.now_fn))
            process = _validate_process_identity(self.process_identity_fn())
            self._emit({
                "event": "resume-start", **host, **process,
            })
        self._certified_run_start_record = self.records[-1]
        started = self._started_seqs()
        completed_rounds = self._completed_rounds()
        started_rounds = {r["round"] for r in self.records
                          if r.get("event") == "round-start"}
        for round_no in sorted({row["round"] for row in self.schedule}):
            if round_no in completed_rounds:
                continue
            if round_no not in started_rounds:
                # resume で round 途中から再入するとき round-start を二重記録しない
                # (レビュー所見: wall_ledger の round 記録が倍加していた)。
                self._emit({"event": "round-start", "round": round_no,
                            "utc": self.now_fn().isoformat()})
            for row in self._round_rows(round_no):
                if row["seq"] in started:
                    self._replay_cut6_start({
                        "seq": row["seq"], "round": round_no,
                        "cell_id": row["cell_id"], "kind": "planned",
                        "retry_ordinal": None, "trigger": None,
                        "attempt_id": _attempt_id(
                            row["cell_id"], "planned", row["seq"], None,
                        ),
                    })
                    continue
                self._run_session(
                    seq=row["seq"], round_no=round_no, cell_id=row["cell_id"],
                    kind="planned", retry_ordinal=None, trigger=None,
                )
            retry_starts = sorted(
                (
                    record for record in self.records
                    if record.get("event") == "session-start"
                    and record.get("kind") == "retry"
                    and record.get("round") == round_no
                ),
                key=lambda record: record["seq"],
            )
            for retry_start in retry_starts:
                self._replay_cut6_start(retry_start)
            self._retry_round(round_no)
            self._emit({"event": "round-complete", "round": round_no,
                        "utc": self.now_fn().isoformat()})


def _attempt_id(cell_id: str, kind: str, seq: int, retry_ordinal: Optional[int]) -> str:
    if kind == "retry":
        return f"{cell_id}::retry{retry_ordinal}"
    return f"{cell_id}::seq{seq}"


# --------------------------------------------------------------------------- #
# terminal: floor 算出 (s8b_floor_stats) + artifact                            #
# --------------------------------------------------------------------------- #

def _session_records(records: list[dict]) -> list[dict]:
    return [r for r in records if r.get("event") == "session"]


def _attempt_lifecycle_records(records: list[dict]) -> list[dict]:
    """Project only attempt authorization/completion records for admission inspection."""

    return [
        r for r in records if r.get("event") in {"session-start", "session"}
    ]


def _journal_expected_binaries(records: list[dict]) -> dict:
    """journal の session receipt から cell_id → binary_sha256_at_measure を集約する (C3-6)。

    verify_floor_artifact の expected_binaries に渡す独立 receipt。同一 cell の複数 session が
    異なる measured hash を持てば差し替えの疑いで fail-closed (実際は _run_session が build 記録と
    食い違いを CampaignAbort するため、完走 campaign では単一値に収束する)。"""
    out: dict = {}
    for rec in _session_records(records):
        cell_id = rec.get("cell_id")
        sha = rec.get("binary_sha256_at_measure")
        if not isinstance(cell_id, str) or not isinstance(sha, str) or len(sha) != 64:
            continue
        prev = out.get(cell_id)
        if prev is not None and prev != sha:
            raise FloorCampaignError(
                f"journal receipt: cell {cell_id} の binary_sha256_at_measure が "
                f"session 間で不一致 ({prev} != {sha})"
            )
        out[cell_id] = sha
    return out


def _cellstats_to_dict(cs) -> dict:
    return {
        "holdout_id": cs.holdout_id,
        "configuration_id": cs.configuration_id,
        "n_valid": cs.n_valid,
        "medians": list(cs.medians),
        "m": cs.m,
        "s": cs.s,
        "valid": cs.valid,
        "cv": cs.cv,
        "notes": list(cs.notes),
    }


def _floors_to_dict(hf) -> dict:
    return {
        "pairs": dict(hf.pairs),           # キーは configuration_id (δ-10)
        "scalar_alt": hf.scalar_alt,
        "scale_ref": hf.scale_ref,
        "diagnostics": hf.diagnostics,     # キーは cell_id
    }


def _expected_protocol(protocol: Mapping, cells: list[dict]) -> dict:
    """verify_floor_artifact に渡す外部 expected_protocol (凍結値) を protocol + cells から組む。"""
    expected = project_protocol_for_floor_artifact(protocol)
    expected["expected_cells"] = _floor_contract.expected_cells_from_cells(cells)
    return expected


def _inspect_holdout_admission(
        *, repo_root: Path, protocol: Mapping, freeze: Mapping,
        freeze_sha256: str, manifest_sha256: str, campaign_run_id: str,
        run_relpath: str, mode: str, cells: Sequence[Mapping],
        schedule: Sequence[Mapping], records: list[dict]) -> dict[str, object]:
    """公開 result 発行直前に private/shared admission evidence を再検査する。"""
    return _holdout_admission.inspect_floor_holdout_admission_evidence(
        repo_root=repo_root,
        protocol=protocol,
        verified_freeze_document=freeze,
        freeze_sha256=freeze_sha256,
        manifest_sha256=manifest_sha256,
        campaign_run_id=campaign_run_id,
        run_relpath=run_relpath,
        mode=mode,
        cells=cells,
        schedule=schedule,
        sessions=_attempt_lifecycle_records(records),
    )


def _verify_result_with_live_admission(
        result: Mapping, expected_protocol: Mapping,
        expected_binaries: Mapping, *, repo_root: Path,
        protocol: Mapping, freeze: Mapping, freeze_sha256: str,
        manifest_sha256: str, campaign_run_id: str, run_relpath: str,
        mode: str, cells: Sequence[Mapping], schedule: Sequence[Mapping],
        records: list[dict], expected_use_perf: bool) -> list:
    """U2 の公開 live-admission verifier 入口だけを自己検査に使う。"""
    return s8b_floor_stats.verify_floor_artifact_with_live_admission(
        result,
        expected_protocol,
        expected_binaries=expected_binaries,
        repo_root=repo_root,
        protocol=protocol,
        verified_freeze_document=freeze,
        freeze_sha256=freeze_sha256,
        manifest_sha256=manifest_sha256,
        campaign_run_id=campaign_run_id,
        run_relpath=run_relpath,
        mode=mode,
        cells=cells,
        schedule=schedule,
        sessions=_attempt_lifecycle_records(records),
        expected_use_perf=expected_use_perf,
    )


def assemble_result(*, protocol, mode, protocol_sha256, freeze_sha256,
                    manifest_sha256, cells, binaries, records,
                    holdout_admission,
                    perf_preflight=None, attempt_registry=None) -> dict:
    """journal の生 session から floor artifact (result) を組み立てる (formula v2)。

    cell_stats / holdout_floors は ``s8b_floor_stats`` (formula v2) が正本。artifact の
    ``config`` / ``sessions`` / ``cells`` / ``floors`` は ``verify_floor_artifact`` が生 session
    から再計算して自己申告値 + 外部 expected_protocol と厳密比較する形に合わせる。durations /
    wall_ledger は journal から読むだけの純粋関数なので resume を跨いで決定的 (β-11 の冪等
    finalization が hash 照合に依存する)。
    """
    use_perf = _assert_perf_mode(mode, perf_preflight)
    normalized_perf = (
        _normalize_perf_preflight(perf_preflight)
        if perf_preflight is not None else None
    )
    _validate_binaries_cover_cells(binaries, cells)
    portable_binaries = _validate_portable_built(
        binaries, expected_ccbench_pin=protocol["ccbench_pin"],
        expected_contract_sha256=protocol["contract_sha256"],
    )
    try:
        normalized_holdout_admission = (
            _floor_contract.validate_floor_holdout_admission_receipt(
                holdout_admission,
            )
        )
    except _floor_contract.FloorContractError as exc:
        raise FloorCampaignError(
            f"holdout admission receipt が不正: {exc}"
        ) from exc
    n_sessions = protocol["n_sessions"]
    reps = protocol["reps"]
    session_cv_max = protocol["session_cv_max"]
    cell_cv_max = protocol["cell_cv_max"]
    stock_configuration = protocol["stock_configuration"]
    wired_min_rel_floor = protocol["wired_min_rel_floor"]

    session_records = _session_records(records)
    records_by_cell: dict[str, list] = {}
    for cell in cells:
        records_by_cell[cell["cell_id"]] = []
    for raw in session_records:
        cell_id = raw["cell_id"]
        try:
            record = s8b_floor_stats._record_from_mapping(raw)
        except (KeyError, TypeError, ValueError) as exc:
            raise FloorCampaignError(
                f"session[{raw.get('seq')!r}] の型が不正: {exc}"
            ) from exc
        records_by_cell.setdefault(cell_id, []).append(record)

    # セル別統計 (s8b_floor_stats.cell_stats)。
    cell_stats_map: dict[str, object] = {}
    cells_out: dict[str, dict] = {}
    for cell in cells:
        cell_id = cell["cell_id"]
        cs = s8b_floor_stats.cell_stats(
            records_by_cell[cell_id], n_sessions=n_sessions, reps=reps,
            session_cv_max=session_cv_max,
        )
        cell_stats_map[cell_id] = cs
        cells_out[cell_id] = _cellstats_to_dict(cs)

    # holdout 別 floor (s8b_floor_stats.holdout_floors)。pairs キーは configuration_id (δ-10)。
    holdouts = sorted({cell["holdout_id"] for cell in cells})
    configurations = sorted({cell["configuration_id"] for cell in cells})
    floors_out: dict[str, dict] = {}
    for holdout_id in holdouts:
        holdout_cells = {
            cell["cell_id"]: cell_stats_map[cell["cell_id"]]
            for cell in cells if cell["holdout_id"] == holdout_id
        }
        stock_cell_id = f"{holdout_id}::{stock_configuration}"
        hf = s8b_floor_stats.holdout_floors(
            holdout_cells, stock_id=stock_cell_id,
            wired_min_rel_floor=wired_min_rel_floor, cell_cv_max=cell_cv_max,
        )
        floors_out[holdout_id] = _floors_to_dict(hf)

    excluded = [
        {
            "seq": r["seq"], "cell_id": r["cell_id"], "kind": r.get("kind"),
            "retry": r.get("retry"), "round": r.get("round"),
            "excluded_reason": r.get("excluded_reason"),
            "exclusion_class": r.get("exclusion_class"),
            "rep_integrity_failures": r.get("rep_integrity_failures"),
            "session_cv": r.get("session_cv"),
        }
        for r in session_records if not r.get("valid")
    ]
    # 全 attempt 台帳 (α-14: CV / median / valid / 除外理由を併記, machine_anomaly と分離)。
    attempts = [
        {
            "seq": r["seq"], "cell_id": r["cell_id"], "kind": r.get("kind"),
            "round": r.get("round"), "retry_ordinal": r.get("retry_ordinal"),
            "valid": r.get("valid"), "excluded_reason": r.get("excluded_reason"),
            "exclusion_class": r.get("exclusion_class"),
            "rep_integrity_failures": r.get("rep_integrity_failures"),
            "session_cv": r.get("session_cv"), "session_median": r.get("session_median"),
            "duration_s": r.get("duration_s"),
        }
        for r in session_records
    ]
    wall_ledger = [
        dict(r) for r in records
        if r.get("event") in {"campaign-start", "round-start", "round-complete"}
    ]

    result = {
        "schema": _floor_contract.RESULT_SCHEMA_V5 if attempt_registry is not None else RESULT_SCHEMA,
        "formula": protocol["formula"],
        "mode": mode,
        # Assembly 単体は authority を持たない。core 入口で raw seam と freshness から導いた
        # lexical finalizer だけが、二相 finalize staging 前にこの値を上書きできる。
        "eligible_for_refreeze": False,
        "env_tag": protocol["env_tag"],
        "ccbench_pin": protocol["ccbench_pin"],
        "protocol_sha256": protocol_sha256,
        "freeze_sha256": freeze_sha256,
        "manifest_sha256": manifest_sha256,
        "holdout_admission": normalized_holdout_admission,
        "stock_configuration": stock_configuration,
        "wired_min_rel_floor": wired_min_rel_floor,
        "reps": protocol["reps"],
        "n_sessions": n_sessions,
        "scale_adequacy_rel_tolerance": protocol["scale_adequacy_rel_tolerance"],
        "holdouts": holdouts,
        "configurations": configurations,
        "binaries": portable_binaries,
        # --- verify_floor_artifact が読む正本フィールド (config は 7 scalar のみ, α-3) ---
        "config": {
            "formula": protocol["formula"],
            "n_sessions": n_sessions,
            "reps": reps,
            "stock_configuration": stock_configuration,
            "wired_min_rel_floor": wired_min_rel_floor,
            "session_cv_max": session_cv_max,
            "cell_cv_max": cell_cv_max,
        },
        "sessions": session_records,
        "cells": cells_out,
        "floors": floors_out,
        # --- 付帯 ---
        "wall_ledger": wall_ledger,
        "excluded": excluded,
        "attempts": attempts,
        **({"attempt_registry": dict(attempt_registry)} if attempt_registry is not None else {}), }
    if normalized_perf is not None:
        result["perf_preflight"] = normalized_perf
        if mode != "pilot" and not use_perf:
            contexts = s8b_floor_stats.floor_perf_validation_contexts(result)
            run_cmd, leading_indicators = contexts[0]
            try:
                observation = _perf_preflight.build_perf_observation(
                    normalized_perf, run_cmd=run_cmd,
                    leading_indicators=leading_indicators,
                )
                result["perf_observation"] = observation
                s8b_floor_stats.validate_floor_perf_evidence(result, observation)
            except _perf_preflight.PerfPreflightError as exc:
                raise FloorCampaignError(
                    f"result perf_observation を構築できない: {exc}"
                ) from exc
    return result


def _fmt(value) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:,.4g}"
    return str(value)


def _render_result_md(result: Mapping) -> str:
    """人間向けサマリ。**result JSON からのみ描画する** (β-9: JSON が唯一のソース)。

    セル表 + floor 案 (pair=configuration_id) + 除外理由別件数 + machine_anomaly セル一覧 +
    全 attempt の CV/median/valid (α-14) を併記する。
    """
    lines: list[str] = []
    lines.append(f"# 8b floor campaign result — {result['env_tag']} / mode={result['mode']}")
    lines.append("")
    lines.append("> floor **案** (何も発効させていない)。freeze への floor 書込みは親が行う。")
    lines.append("> 単一 campaign 内 session dispersion に基づく記述的下限 "
                 "(別 run 間の変動は含まない)。")
    lines.append(
        f"> eligible_for_refreeze (producer-reported): "
        f"{result['eligible_for_refreeze']}"
    )
    lines.append("")
    lines.append(f"- formula: `{result['formula']}`")
    lines.append(f"- ccbench_pin: `{result['ccbench_pin']}`")
    lines.append(f"- protocol_sha256: `{result['protocol_sha256']}`")
    lines.append(f"- freeze_sha256: `{result['freeze_sha256']}`")
    lines.append(f"- manifest_sha256: `{result['manifest_sha256']}`")
    perf_receipt = result.get("perf_preflight")
    if perf_receipt is not None:
        perf_mode = "enabled" if perf_receipt.get("available") else "disabled"
        perf_reason = perf_receipt.get("reason")
        perf_digest = _canonical_sha256(perf_receipt)
        lines.append(
            f"- perf: mode={perf_mode}, reason={perf_reason}, "
            f"receipt_sha256=`{perf_digest}`"
        )
    lines.append(f"- stock_configuration: `{result['stock_configuration']}`")
    lines.append(f"- wired_min_rel_floor: {result['wired_min_rel_floor']}")
    lines.append(f"- scale_adequacy_rel_tolerance: {result.get('scale_adequacy_rel_tolerance')}")
    lines.append("")

    lines.append("## セル統計 (session-median の散らばり)")
    lines.append("")
    cells = result.get("cells") or {}
    lines.append("| cell | valid | n_valid | m (median) | s (stdev) | cv |")
    lines.append("|---|:---:|---:|---:|---:|---:|")
    for cell_id in sorted(cells):
        c = cells[cell_id]
        lines.append(
            f"| `{cell_id}` | {c.get('valid')} | {c.get('n_valid')} | "
            f"{_fmt(c.get('m'))} | {_fmt(c.get('s'))} | {_fmt(c.get('cv'))} |"
        )
    lines.append("")

    lines.append("## floor 案 (holdout 別, pair = configuration_id)")
    lines.append("")
    floors = result.get("floors") or {}
    for holdout_id in sorted(floors):
        hf = floors[holdout_id]
        lines.append(f"### {holdout_id}")
        lines.append("")
        lines.append(f"- scalar_alt (全 pair の max): {_fmt(hf.get('scalar_alt'))}")
        lines.append(f"- scale_ref (m_stock): {_fmt(hf.get('scale_ref'))}")
        diag = hf.get("diagnostics") or {}
        anomaly_cells = diag.get("machine_anomaly_cells") or []
        lines.append(f"- machine_anomaly セル: "
                     f"{', '.join(f'`{c}`' for c in anomaly_cells) if anomaly_cells else '(なし)'}")
        lines.append("")
        pairs = hf.get("pairs") or {}
        lines.append("| pair (configuration_id) | floor_pair |")
        lines.append("|---|---:|")
        for cfg in sorted(pairs):
            lines.append(f"| `{cfg}` | {_fmt(pairs[cfg])} |")
        lines.append("")

    lines.append("## 除外 session (理由別件数)")
    lines.append("")
    excluded = result.get("excluded") or []
    reason_counts: dict[str, int] = {}
    for item in excluded:
        reason = item.get("exclusion_class") or item.get("excluded_reason") or "(none)"
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    if not reason_counts:
        lines.append("(なし)")
    else:
        lines.append("| reason | count |")
        lines.append("|---|---:|")
        for reason in sorted(reason_counts):
            lines.append(f"| {reason} | {reason_counts[reason]} |")
    lines.append("")

    lines.append("## 全 attempt 台帳 (CV / median / valid)")
    lines.append("")
    attempts = result.get("attempts") or []
    lines.append("| seq | cell | kind | round | valid | reason | cv | median | dur(s) |")
    lines.append("|---:|---|---|---:|:---:|---|---:|---:|---:|")
    for a in sorted(attempts, key=lambda x: x.get("seq", 0)):
        lines.append(
            f"| {a.get('seq')} | `{a.get('cell_id')}` | {a.get('kind')} | "
            f"{a.get('round')} | {a.get('valid')} | "
            f"{a.get('exclusion_class') or a.get('excluded_reason')} | "
            f"{_fmt(a.get('session_cv'))} | {_fmt(a.get('session_median'))} | "
            f"{_fmt(a.get('duration_s'))} |"
        )
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# 冪等 finalization (β-11): result.json/md/terminal の状態機械                  #
# --------------------------------------------------------------------------- #

def _result_bytes(result: Mapping) -> bytes:
    return (json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _md_bytes(md_text: str) -> bytes:
    text = md_text if md_text.endswith("\n") else md_text + "\n"
    return text.encode("utf-8")


def _stage_finalize_files(
        run_dir: Path, result: Mapping, md_text: str,
        *, write_capability: Optional[WriteCapability] = None) -> tuple:
    """phase 1: result/md bytes を deterministic pending file へ fsync する。"""
    run_dir = Path(run_dir)
    result_payload = _result_bytes(result)
    md_payload = _md_bytes(md_text)
    result_pending = run_dir / ".result.json.pending"
    md_pending = run_dir / ".result.md.pending"
    _stage_bytes(result_pending, result_payload, write_capability=write_capability)
    _stage_bytes(md_pending, md_payload, write_capability=write_capability)
    return result_pending, result_payload, md_pending, md_payload


def _append_completed_terminal(
        journal_path: Path, *, write_capability: Optional[WriteCapability] = None) -> None:
    records = _read_journal(journal_path)
    terminals = [record for record in records if record.get("event") == "terminal"]
    if terminals:
        raise FloorCampaignError("finalize: completed terminal 追記前に terminal が既にある")
    _journal_append(
        journal_path, {"event": "terminal", "status": "completed"},
        write_capability=write_capability,
    )


def _publish_finalize_files(run_dir: Path, staged: tuple) -> None:
    """phase 3: terminal fsync 後、補助 md、権威 result の順で publish する。"""
    result_pending, result_payload, md_pending, md_payload = staged
    _publish_staged_create_only(md_pending, Path(run_dir) / "result.md", md_payload)
    _publish_staged_create_only(result_pending, Path(run_dir) / "result.json", result_payload)


def _finalize(run_dir: Path, staged: tuple, journal_path: Path, *,
              terminal_already_completed: bool = False,
              write_capability: Optional[WriteCapability] = None) -> None:
    """二相 finalize: staged+fsync → completed terminal+fsync → atomic publish。

    terminal→publish 間 crash は ``M-finalize-pending`` として publish だけを再開する。
    completed terminal は一意かつ journal 最終 record である。補助 ``result.md`` は
    consumer の権威 ``result.json`` より先に publish し、二つの publish 間で停止しても
    result.json を可視にしない。``terminal_already_completed=True`` の uniqueness re-check は、
    通常の classify 済み経路では恒真となる defense-in-depth であり、独立保証には数えない。
    """
    if terminal_already_completed:
        records = _read_journal(journal_path)
        terminals = [record for record in records if record.get("event") == "terminal"]
        if (len(terminals) != 1 or terminals[0].get("status") != "completed"
                or records[-1] is not terminals[0]):
            raise FloorCampaignError("finalize-pending: completed terminal が一意・最終でない")
    else:
        _append_completed_terminal(journal_path, write_capability=write_capability)
    _publish_finalize_files(run_dir, staged)


def _create_only_bytes(
        path: Path, payload: bytes,
        *, write_capability: Optional[WriteCapability] = None) -> None:
    try:
        opener = (
            open_with_write_capability(write_capability, path, "xb")
            if write_capability is not None else open(path, "xb")
        )
        with opener as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise FloorCampaignError(f"既に存在するため上書きしない: {path}") from exc


# --------------------------------------------------------------------------- #
# run_campaign (注入点)                                                         #
# --------------------------------------------------------------------------- #

def _after_certificate_issued_noop(cert_path: Path) -> None:
    return None


_PUBLIC_CALLABLE_SEAM_NAMES = frozenset({
    "measure_fn", "probe_fn", "sleep_fn", "monotonic_fn", "prepare_fn",
    "now_fn", "host_provenance_fn", "process_identity_fn",
    "execution_receipt_fn", "build_fn", "after_certificate_issued_fn",
    "perf_preflight_fn",
})


def _nondefault_campaign_seams(
        *, measure_fn=None, probe_fn=None, sleep_fn=_DEFAULT_SLEEP_FN,
        monotonic_fn=_DEFAULT_MONOTONIC_FN, prepare_fn=None, now_fn=None,
        host_provenance_fn=None, process_identity_fn=None,
        execution_receipt_fn=None, build_fn=None, repo_root=None,
        fetchcontent_base_dir=None,
        after_certificate_issued_fn=None, durable_root_policy=None,
        _floor_preflight_fn=None, perf_preflight_fn=None,
        _holdout_repo_root=None, _holdout_signature_source=None,
) -> frozenset[str]:
    """Raw campaign 実引数から refreeze 不適格 seam 名を単一源で分類する。"""
    seam_presence = {
        "measure_fn": measure_fn is not None,
        "probe_fn": probe_fn is not None,
        "sleep_fn": sleep_fn is not _DEFAULT_SLEEP_FN,
        "monotonic_fn": monotonic_fn is not _DEFAULT_MONOTONIC_FN,
        "prepare_fn": prepare_fn is not None,
        "now_fn": now_fn is not None,
        "host_provenance_fn": host_provenance_fn is not None,
        "process_identity_fn": process_identity_fn is not None,
        "execution_receipt_fn": execution_receipt_fn is not None,
        "build_fn": build_fn is not None,
        "repo_root": repo_root is not None,
        "fetchcontent_base_dir": fetchcontent_base_dir is not None,
        "after_certificate_issued_fn": after_certificate_issued_fn is not None,
        "durable_root_policy": durable_root_policy is not None,
        "_floor_preflight_fn": _floor_preflight_fn is not None,
        "perf_preflight_fn": perf_preflight_fn is not None,
        "_holdout_repo_root": _holdout_repo_root is not None,
        "_holdout_signature_source": _holdout_signature_source is not None,
    }
    if set(seam_presence) != _floor_contract.REFREEZE_DISQUALIFYING_SEAM_NAMES:
        raise AssertionError("refreeze seam classifier differs from its closed set")
    return frozenset(name for name, present in seam_presence.items() if present)


def _derive_refreeze_eligibility(
        *, mode, resume_dir, nondefault_seams: frozenset[str],
) -> bool:
    """Canonical official・fresh・非既定 seam ゼロだけを適格化する。

    ``type(mode)`` は検証済み core local に対する defense-in-depth であり、独立保証には
    数えない。入口の exact-type 検証が主防壁である。
    """
    return (
        type(mode) is str
        and mode == "official"
        and resume_dir is None
        and not nondefault_seams
    )


def _require_supplied_protocol_authority(
        protocol: Mapping, *, root: Path,
        supplied_protocol_path: Path | str | None,
) -> IndexedFloorProtocol:
    """production 入力を resolver の固定 record へ副作用前に束縛する。"""
    root = Path(root)
    supplied_path = (
        root / _FLOOR_PROTOCOL_REL
        if supplied_protocol_path is None else Path(supplied_protocol_path)
    )
    if not supplied_path.is_absolute():
        supplied_path = (Path.cwd() / supplied_path).absolute()
    resolved = resolve_current_floor_protocol(root=root)
    resolved_path = (root / resolved.path).absolute()
    problems = []
    if resolved.document != dict(protocol):
        problems.append("document mismatch")
    try:
        supplied_raw = supplied_path.read_bytes()
    except OSError as exc:
        raise FloorCampaignError(
            "supplied floor protocol authority を読めない: "
            f"supplied_path={supplied_path} resolved_path={resolved_path}: {exc}"
        ) from exc
    supplied_sha256 = hashlib.sha256(supplied_raw).hexdigest()
    if supplied_raw != resolved.raw_bytes:
        problems.append("bytes mismatch")
    if supplied_sha256 != resolved.sha256:
        problems.append(
            f"sha256 mismatch supplied={supplied_sha256} resolved={resolved.sha256}"
        )
    if problems:
        raise FloorCampaignError(
            "supplied floor protocol authority が current resolver record と不一致: "
            f"supplied_path={supplied_path} resolved_path={resolved_path}; "
            + "; ".join(problems)
        )
    return resolved


def run_campaign(protocol, freeze_doc, *, out_root, mode, resume_dir=None,
                 measure_fn=None, probe_fn=None, sleep_fn=_DEFAULT_SLEEP_FN,
                 monotonic_fn=_DEFAULT_MONOTONIC_FN, prepare_fn=None, now_fn=None,
                 host_provenance_fn=None, process_identity_fn=None,
                 execution_receipt_fn=None, build_fn=None, repo_root=None,
                 fetchcontent_base_dir=None,
                 after_certificate_issued_fn=None,
                 durable_root_policy=None, perf_preflight_fn=None,
                 protocol_path: Path | str | None = None,
                 confirm_official_floor_run: bool = False) -> dict:
    """Production wrapper with no caller-provided callable seams."""
    mode = _validate_mode(mode)
    nondefault_seams = _nondefault_campaign_seams(
        measure_fn=measure_fn, probe_fn=probe_fn, sleep_fn=sleep_fn,
        monotonic_fn=monotonic_fn, prepare_fn=prepare_fn, now_fn=now_fn,
        host_provenance_fn=host_provenance_fn,
        process_identity_fn=process_identity_fn,
        execution_receipt_fn=execution_receipt_fn, build_fn=build_fn,
        repo_root=repo_root,
        fetchcontent_base_dir=fetchcontent_base_dir,
        after_certificate_issued_fn=after_certificate_issued_fn,
        durable_root_policy=durable_root_policy,
        perf_preflight_fn=perf_preflight_fn,
    )
    callable_seams = sorted(nondefault_seams & _PUBLIC_CALLABLE_SEAM_NAMES)
    if callable_seams:
        raise FloorCampaignError(
            f"production mode への caller callable seam 注入を拒否する: {callable_seams}"
        )
    if mode == "official":
        non_default = sorted(nondefault_seams)
        if non_default:
            raise FloorCampaignError(
                f"official mode への非 default seam 注入を拒否する: {non_default}")
    if mode == "official":
        _assert_official_permitted(mode, confirm_official_floor_run)
    authority_root = ROOT if repo_root is None else Path(repo_root)
    _require_supplied_protocol_authority(
        protocol, root=authority_root,
        supplied_protocol_path=protocol_path,
    )
    return _run_campaign_core(
        protocol, freeze_doc, out_root=out_root, mode=mode, resume_dir=resume_dir,
        measure_fn=measure_fn, probe_fn=probe_fn, sleep_fn=sleep_fn,
        monotonic_fn=monotonic_fn, prepare_fn=prepare_fn, now_fn=now_fn,
        host_provenance_fn=host_provenance_fn,
        process_identity_fn=process_identity_fn,
        execution_receipt_fn=execution_receipt_fn, build_fn=build_fn,
        repo_root=repo_root,
        fetchcontent_base_dir=fetchcontent_base_dir,
        after_certificate_issued_fn=after_certificate_issued_fn,
        durable_root_policy=durable_root_policy,
        perf_preflight_fn=perf_preflight_fn,
        confirm_official_floor_run=confirm_official_floor_run,
    )


def _run_campaign_core(protocol, freeze_doc, *, out_root, mode, resume_dir=None,
                       measure_fn=None, probe_fn=None, sleep_fn=_DEFAULT_SLEEP_FN,
                       monotonic_fn=_DEFAULT_MONOTONIC_FN, prepare_fn=None, now_fn=None,
                       host_provenance_fn=None, process_identity_fn=None,
                       execution_receipt_fn=None, build_fn=None, repo_root=None,
                       fetchcontent_base_dir=None,
                       after_certificate_issued_fn=None,
                       durable_root_policy=None, _floor_preflight_fn=None,
                       perf_preflight_fn=None, _holdout_repo_root=None,
                       _holdout_signature_source=None,
                       confirm_official_floor_run: bool = False) -> dict:
    """floor campaign を直列・単一テナントで実行し、floor 案 artifact を書いて返す。

    注入点 (テスト容易性): ``measure_fn(binary, records, threads, workload) -> ScalePoint`` /
    ``probe_fn() -> (rc, stdout, stderr)`` / ``sleep_fn`` / ``monotonic_fn`` / ``prepare_fn`` /
    ``now_fn() -> datetime``。CLI main はこれらを実物で束ねるだけにする。

    public wrapper を通らない staged builder/test 専用 core。official permit gate と materializer
    固定はこの core 自体が行う。holdout gate の関数注入点は持たない。場所を変える
    ``_holdout_repo_root`` と合成 freeze の中立表だけを解決する
    ``_holdout_signature_source`` のどちらでも、claim・ledger・ticket・authority・identity の
    全検査を実行する。

    Cell claim は ``runner.run()`` の外側で行う非計測 preflight と manifest sealing の後、
    ``runner.run()`` の直前に取得する。live admission の再検査、host provenance、process
    identity、session competition probe は ``runner.run()`` 内で claim 後に行う。それ以前に
    保護比率を実測しようとしても、最下層 ``run_once`` gateway が attempt token 無しで拒否する。
    """
    external_checkpoint_binding = floor_job_checkpoint.take_checkpoint_environment(
        os.environ,
    )
    if resume_dir is not None:
        external_checkpoint_binding = None
    mode = _validate_mode(mode)
    nondefault_seams = _nondefault_campaign_seams(
        measure_fn=measure_fn, probe_fn=probe_fn, sleep_fn=sleep_fn,
        monotonic_fn=monotonic_fn, prepare_fn=prepare_fn, now_fn=now_fn,
        host_provenance_fn=host_provenance_fn,
        process_identity_fn=process_identity_fn,
        execution_receipt_fn=execution_receipt_fn, build_fn=build_fn,
        repo_root=repo_root,
        fetchcontent_base_dir=fetchcontent_base_dir,
        after_certificate_issued_fn=after_certificate_issued_fn,
        durable_root_policy=durable_root_policy,
        _floor_preflight_fn=_floor_preflight_fn,
        perf_preflight_fn=perf_preflight_fn,
        _holdout_repo_root=_holdout_repo_root,
        _holdout_signature_source=_holdout_signature_source,
    )
    eligible_for_refreeze = _derive_refreeze_eligibility(
        mode=mode, resume_dir=resume_dir, nondefault_seams=nondefault_seams,
    )
    result = None

    def apply_refreeze_eligibility() -> None:
        """捕捉済み入口判定を result へ写す call-order invariant。

        ``result is None`` は直接 helper 呼出し向け defense-in-depth であり、現行 core の
        assembly 直後 callsite では到達不能なので独立保証には数えない。
        """
        if result is None:  # pragma: no cover - local call order invariant
            raise AssertionError("result assembly より前に refreeze finalizer が呼ばれた")
        result["eligible_for_refreeze"] = eligible_for_refreeze

    if mode == "official" and perf_preflight_fn is not None:
        raise FloorCampaignError(
            "official mode への非 default seam 注入を拒否する: ['perf_preflight_fn']"
        )
    if mode == "official" and build_fn is not None:
        raise FloorCampaignError(
            "official mode への非 default materializer 注入を拒否する: ['build_fn']"
        )
    if mode == "official":
        build_fn = buildcache.build_v2
    else:
        build_fn = build_fn or buildcache.build_v2
    _assert_official_permitted(mode, confirm_official_floor_run)

    if not isinstance(freeze_doc, _freeze_io.VerifiedFreeze):
        raise FloorCampaignError("freeze_doc が load_verified_freeze の戻り値でない")
    now_fn = now_fn or (lambda: dt.datetime.now(dt.timezone.utc))
    prepare_fn = prepare_fn or prepare_cell
    probe_fn = probe_fn or _default_probe_fn
    host_provenance_fn = host_provenance_fn or _host_provenance
    process_identity_fn = process_identity_fn or _process_identity
    repo_root = ROOT if repo_root is None else Path(repo_root)
    holdout_repo_root = (
        repo_root if _holdout_repo_root is None else Path(_holdout_repo_root)
    )
    after_certificate_issued_fn = (
        after_certificate_issued_fn or _after_certificate_issued_noop)

    def perform_perf_preflight() -> dict | None:
        producer = perf_preflight_fn or _perf_preflight.probe_perf_availability
        raw_receipt = producer(
            perf_candidates=_policy_perf_candidates(_REPO_ROOT),
        )
        return _project_probed_perf_preflight(mode, raw_receipt)

    protocol, contract = _validate_protocol_against_current(protocol)

    # current admission が解決した同一 contract object を calibration・receipt・
    # materialization の全 edge へ渡す。歴史検証済み dict を実行権限にしない。
    # 全 env で calibration bytes を hash 束縛してから mode を dispatch する。required は
    # 統合 issuer + production probe 以外に receipt 生成経路を持たず、none は従来の
    # machine-pin + v1 receipt 呼出し形を維持する。
    try:
        verified_calibration = env_attestation.load_verified_calibration(
            contract, repo_root,
        )
        if contract.attestation_mode == "required":
            if execution_receipt_fn is None:
                raw_execution_receipt = execution_guard.attest_and_build_receipt(
                    contract, verified_calibration,
                    probe_fn=env_attestation.probe, now_fn=now_fn,
                )
            else:
                raw_execution_receipt = execution_receipt_fn(
                    contract, verified_calibration, now_fn=now_fn,
                )
        else:
            execution_guard.assert_machine_pin(
                contract,
                machine_env_tag=_machine_env_tag_for_site(site_policy.current_site()),
            )
            issuer = execution_receipt_fn or execution_guard.build_receipt
            raw_execution_receipt = issuer(contract, now_fn=now_fn)
        execution_receipt = _validate_execution_receipt(
            raw_execution_receipt, contract=contract,
            verified_calibration=verified_calibration,
        )
    except (env_attestation.AttestationError,
            execution_guard.ExecutionGuardError) as exc:
        raise FloorCampaignError(str(exc)) from exc
    # isolation policy: allow_resume=False の env では別 process からの resume を拒否 (γ-5)。
    if resume_dir is not None and not contract.isolation_policy.allow_resume:
        raise FloorCampaignError(
            f"env {contract.env_tag} は allow_resume=False (別 process resume を拒否)"
        )

    freeze = freeze_doc.document
    freeze_sha256 = freeze_doc.sha256
    if freeze_sha256 != protocol["freeze"]["sha256"]:
        raise FloorCampaignError(
            "freeze byte sha256 が protocol.freeze.sha256 と不一致 (bytes-hash pin 破れ)"
        )
    if freeze.get("schema_version") != FREEZE_SCHEMA:
        raise FloorCampaignError(f"freeze.schema_version が {FREEZE_SCHEMA} でない")

    cells = enumerate_cells(freeze, stock_configuration=protocol["stock_configuration"])
    cell_by_id = {cell["cell_id"]: cell for cell in cells}
    admission_cells = [_admission_cell(cell) for cell in cells]
    schedule = build_schedule(
        cells=cells, master_seed=protocol["master_seed"],
        n_sessions=protocol["n_sessions"],
    )
    protocol_sha256, attempt_registry_plan = _protocol_sha256_and_attempt_registry_plan(protocol=protocol, cells=cells, schedule=schedule, freeze_sha256=freeze_sha256, production=measure_fn is None and measure_point is _DEFAULT_MEASURE_POINT)
    out_root = Path(out_root)
    started_at = now_fn() if resume_dir is None else None
    campaign_run_id = (
        _fresh_run_id(protocol_sha256, started_at)
        if started_at is not None else Path(resume_dir).name
    )
    if resume_dir is None:
        run_relpath = (
            Path("env") / protocol["env_tag"] / "calibration"
            / f"s8b-floor-{mode}" / campaign_run_id
        ).as_posix()
        early_resume_records = None
    else:
        early_run_dir = Path(resume_dir)
        try:
            run_relpath = early_run_dir.resolve(strict=False).relative_to(
                out_root.resolve(strict=False)
            ).as_posix()
        except ValueError as exc:
            raise FloorCampaignError("resume run_dir が out_root 配下でない") from exc
        early_resume_records = _read_journal(early_run_dir / "journal.jsonl")

    reservation_binding = None
    reservation_check = None
    reservation_required_s = None
    reservation_safety_margin_s = None
    if reservation.is_reservation_required(contract.isolation_policy):
        required_s, safety_margin_s = _floor_reservation_budget(
            protocol=protocol, cells=cells, schedule=schedule,
        )
        reservation_required_s = required_s
        reservation_safety_margin_s = safety_margin_s
        try:
            reservation_binding = reservation.read_binding(os.environ)
            reservation_check = reservation.check_reservation(
                reservation_binding,
                required_s=required_s,
                safety_margin_s=safety_margin_s,
                environ=os.environ,
                monotonic_now_fn=monotonic_fn,
            )
        except reservation.ReservationError as exc:
            raise FloorCampaignError(f"reservation preflight 失敗: {exc}") from exc
        try:
            submit_receipt = floor_submit_receipt.load_floor_submit_receipt(
                floor_submit_receipt.receipt_path(
                    repo_root,
                    env_tag=contract.env_tag,
                    nonce=reservation_binding.nonce,
                )
            )
            floor_submit_receipt.require_floor_submit_receipt_binding(
                submit_receipt,
                expected_job_id=reservation_binding.job_id,
                expected_job_script_sha256=reservation_binding.script_sha256,
                expected_nonce=reservation_binding.nonce,
            )
        except floor_submit_receipt.FloorSubmitReceiptError as exc:
            raise FloorCampaignError(
                f"submitter receipt preflight 失敗: {exc}"
            ) from exc

    try:
        output_write_capability = authorize_output_root(
            str(out_root), policy=durable_root_policy,
        )
    except DurableRootError as exc:
        raise FloorCampaignError(f"durable output root preflight 失敗: {exc}") from exc
    launch_certificate_sha256 = None
    resume_records = early_resume_records
    resume_state = None
    perf_preflight_receipt = None

    claim_identity = campaign_run_id
    if contract.isolation_policy.single_process:
        assert reservation_binding is not None
        claim_root = out_root / "claims"
        try:
            # acquire_claim 自身を campaign の最初の副作用にするため、claims/ は durable
            # approval 時に事前 provisioning 済みであることを要求し、driver は作らない。
            if claim_root.is_symlink() or not claim_root.is_dir():
                raise FloorCampaignError(
                    f"campaign claim root が事前 provisioning 済みでない: {claim_root}"
                )
            write_capability_for_directory(
                claim_root, policy=durable_root_policy,
            )
            record = campaign_claim.ClaimRecord(
                campaign_identity=claim_identity,
                protocol_digest=protocol_sha256,
                job_id=reservation_binding.job_id,
                host=reservation_binding.host,
                boot_id=reservation_binding.boot_id,
                pid=os.getpid(),
                proc_starttime=campaign_claim.read_proc_starttime(),
                created_utc=now_fn().isoformat(),
            )
            campaign_claim.acquire_claim(claim_root, record)
        except campaign_claim.ClaimError as exc:
            existing = (
                asdict(exc.existing_record) if exc.existing_record is not None else None
            )
            raise FloorCampaignError(
                f"campaign claim 取得失敗: {exc}; existing={existing}",
                claim_error=exc,
            ) from exc
        except FloorCampaignError:
            raise
        except DurableRootError as exc:
            raise FloorCampaignError(f"campaign claim root 拒否: {exc}") from exc

    if resume_dir is None:
        # fresh: official は run_dir mkdir より前に clean scan を完了させる。時刻は一度だけ捕捉し、
        # run id と certificate.started_utc に同じ値を使う。
        assert started_at is not None
        certificate = None
        if mode == "official":
            floor_preflight_fn = (
                _floor_preflight_freeze_allowlist
                if _floor_preflight_fn is None else _floor_preflight_fn
            )
            freeze_allowlist = floor_preflight_fn(
                repo_root,
                freeze_path=protocol["freeze"]["path"],
                freeze_sha256=freeze_sha256,
                protocol_sha256=protocol_sha256,
            )
            certificate, expected_clean_scan_digest = _official_launch_preflight(
                repo_root,
                v1_freeze_sha256=freeze_sha256,
                protocol_sha256=protocol_sha256,
                started_utc=started_at.isoformat(),
                campaign_run_id=campaign_run_id,
                freeze_allowlist=freeze_allowlist,
            )
        perf_preflight_receipt = perform_perf_preflight()
        _assert_perf_mode(mode, perf_preflight_receipt)

        run_dir = _fresh_run_dir(
            out_root, protocol, mode, protocol_sha256, started_at,
            write_capability=output_write_capability,
        )
        try:
            actual_run_relpath = run_dir.resolve(strict=False).relative_to(
                out_root.resolve(strict=False)
            ).as_posix()
        except ValueError as exc:
            raise FloorCampaignError("fresh run_dir が out_root 配下でない") from exc
        if actual_run_relpath != run_relpath or run_dir.name != campaign_run_id:
            raise FloorCampaignError("fresh run coordinates differ from admission claim")
        try:
            run_write_capability = write_capability_for_directory(
                run_dir.parent, policy=durable_root_policy,
            )
        except DurableRootError as exc:
            raise FloorCampaignError(f"run durable root 拒否: {exc}") from exc
        journal_path = run_dir / "journal.jsonl"
        manifest_path = run_dir / "manifest.json"
        if certificate is not None:
            cert_path = run_dir / "launch_certificate.json"
            launch_certificate_sha256 = issue_launch_certificate(
                cert_path, certificate, write_capability=run_write_capability,
            )
            _revalidate_issued_certificate(
                cert_path,
                expected_v1_freeze_sha256=freeze_sha256,
                expected_clean_scan_digest=expected_clean_scan_digest,
                expected_protocol_sha256=protocol_sha256,
                expected_run_id=run_dir.name,
            )
            after_certificate_issued_fn(cert_path)
            try:
                cert_raw_after_checkpoint = cert_path.read_bytes()
            except OSError as exc:
                raise FloorCampaignError(
                    f"checkpoint 後に launch certificate を再読できない: {exc}") from exc
            if hashlib.sha256(cert_raw_after_checkpoint).hexdigest() != launch_certificate_sha256:
                raise FloorCampaignError(
                    "checkpoint 後の launch certificate raw hash が発行時と不一致")
            _journal_append(
                journal_path, {
                    "event": "launch-start", "schema": JOURNAL_SCHEMA,
                    "launch_certificate_sha256": launch_certificate_sha256,
                    "utc": started_at.isoformat(),
                },
                write_capability=run_write_capability,
            )
        if reservation_check is not None:
            assert reservation_required_s is not None
            assert reservation_safety_margin_s is not None
            reservation_record = {
                    "event": "reservation-preflight",
                    "required_s": reservation_required_s,
                    "safety_margin_s": reservation_safety_margin_s,
                    "formula": _FLOOR_RESERVATION_FORMULA,
                    "build_cap_per_cell_s": _FLOOR_BUILD_CAP_PER_CELL_S,
                    "shared_dependency_prebuild": any(
                        cell.get("configuration_id") == "sort_best"
                        for cell in cells
                    ),
                    "dependency_configure_cap_s": _FLOOR_DEPENDENCY_CONFIGURE_CAP_S,
                    "dependency_target_cap_s": _FLOOR_DEPENDENCY_TARGET_CAP_S,
                    "verify_cap_per_attempt_s": _FLOOR_VERIFY_CAP_PER_ATTEMPT_S,
                    "finalize_reserve_s": _FLOOR_FINALIZE_RESERVE_S,
                }
            if external_checkpoint_binding is not None:
                reservation_record.update({
                    "pbs_jobid": external_checkpoint_binding["job_id"],
                    "submission_nonce": external_checkpoint_binding["nonce"],
                })
            _journal_append(
                journal_path, reservation_record,
                write_capability=run_write_capability,
            )
        if external_checkpoint_binding is not None:
            floor_job_checkpoint.try_append_checkpoint_bounded(
                path=external_checkpoint_binding["path"],
                job_id=external_checkpoint_binding["job_id"],
                nonce=external_checkpoint_binding["nonce"],
                producer="s8b_floor_campaign.py",
                stage="floor-driver",
                transition="run-linked",
                rc=None,
                command=None,
                durability="fsynced",
                repo_root=str(repo_root),
                attempt_dir=os.environ.get(_FLOOR_JOB_STAGING_ENV),
                run_dir=str(run_dir),
                journal_path=str(journal_path),
            )
        if perf_preflight_receipt is not None:
            _journal_append(
                journal_path,
                {
                    "event": "perf-preflight",
                    "schema": JOURNAL_SCHEMA,
                    "perf_preflight_receipt": _normalize_perf_preflight(
                        perf_preflight_receipt
                    ),
                },
                write_capability=run_write_capability,
            )
        runtime_built = build_cells(
            freeze, cells, ccbench_pin=protocol["ccbench_pin"],
            out_root=out_root, prepare_fn=prepare_fn, contract=contract,
            verified_calibration=verified_calibration,
            build_fn=build_fn,
            fetchcontent_base_dir=fetchcontent_base_dir,
            repo_root=repo_root,
            reservation_binding=reservation_binding,
        )
        # content-addressed store (C3-7): 計測 bytes を env scope 永続領域へ複製し store_path を記録。
        store_root = Path(env_scope_dir(protocol["env_tag"], output_root=str(out_root))) / "binaries"
        try:
            ensure_directory_with_capability(output_write_capability, store_root)
            store_write_capability = write_capability_for_directory(
                store_root, policy=durable_root_policy,
            )
        except DurableRootError as exc:
            raise FloorCampaignError(f"binary store durable root 拒否: {exc}") from exc
        store_binaries(
            runtime_built, store_root, out_root=out_root,
            expected_ccbench_pin=protocol["ccbench_pin"],
            expected_contract_sha256=contract.contract_sha256,
            write_capability=store_write_capability,
        )
        artifact_built = project_built_records(
            runtime_built, out_root=out_root,
            expected_ccbench_pin=protocol["ccbench_pin"],
            expected_contract_sha256=contract.contract_sha256,
        )
        manifest = assemble_manifest(
            protocol=protocol, protocol_sha256=protocol_sha256,
            freeze_sha256=freeze_sha256, cells=cells,
            built=artifact_built, schedule=schedule,
            perf_preflight=perf_preflight_receipt, mode=mode,
        )
        manifest_bytes = _atomic_create_only_json(
            manifest_path, manifest, write_capability=run_write_capability,
        )
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    else:
        run_dir = Path(resume_dir)
        try:
            run_write_capability = write_capability_for_directory(
                run_dir.parent, policy=durable_root_policy,
            )
        except DurableRootError as exc:
            raise FloorCampaignError(f"resume durable root 拒否: {exc}") from exc
        journal_path = run_dir / "journal.jsonl"
        manifest_path = run_dir / "manifest.json"
        assert resume_records is not None
        try:
            resume_state = _floor_contract.classify_journal_resume_state(
                resume_records, manifest_exists=manifest_path.is_file(),
                result_published=(run_dir / "result.json").is_file(),
                markdown_published=(run_dir / "result.md").is_file(),
            )
        except _floor_contract.FloorContractError as exc:
            raise FloorCampaignError(f"resume state invalid: {exc}") from exc

        if resume_state == "L":
            launch_certificate_sha256 = _verify_resume_journal(
                resume_records, run_dir=run_dir, mode=mode, schedule=schedule,
                protocol_sha256=protocol_sha256, freeze_sha256=freeze_sha256,
                manifest_sha256=None, resume_state=resume_state,
                retry_slots_per_cell=protocol["retry_slots_per_cell"],
            )
            perf_preflight_receipt = perform_perf_preflight()
            _assert_perf_mode(mode, perf_preflight_receipt)
            runtime_built = build_cells(
                freeze, cells, ccbench_pin=protocol["ccbench_pin"],
                out_root=out_root, prepare_fn=prepare_fn, contract=contract,
                verified_calibration=verified_calibration,
                build_fn=build_fn,
                fetchcontent_base_dir=fetchcontent_base_dir,
                repo_root=repo_root,
                reservation_binding=reservation_binding,
            )
            store_root = Path(env_scope_dir(
                protocol["env_tag"], output_root=str(out_root))) / "binaries"
            try:
                ensure_directory_with_capability(output_write_capability, store_root)
                store_write_capability = write_capability_for_directory(
                    store_root, policy=durable_root_policy,
                )
            except DurableRootError as exc:
                raise FloorCampaignError(f"binary store durable root 拒否: {exc}") from exc
            store_binaries(
                runtime_built, store_root, out_root=out_root,
                expected_ccbench_pin=protocol["ccbench_pin"],
                expected_contract_sha256=contract.contract_sha256,
                write_capability=store_write_capability,
            )
            artifact_built = project_built_records(
                runtime_built, out_root=out_root,
                expected_ccbench_pin=protocol["ccbench_pin"],
                expected_contract_sha256=contract.contract_sha256,
            )
            manifest = assemble_manifest(
                protocol=protocol, protocol_sha256=protocol_sha256,
                freeze_sha256=freeze_sha256, cells=cells,
                built=artifact_built, schedule=schedule,
                perf_preflight=perf_preflight_receipt, mode=mode,
            )
            manifest_bytes = _atomic_create_only_json(
                manifest_path, manifest, write_capability=run_write_capability,
            )
            manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
            resume_state = "M-prestart"
        else:
            manifest, manifest_sha256, artifact_built, runtime_built = _load_resume_manifest(
                manifest_path, protocol_sha256=protocol_sha256,
                freeze_sha256=freeze_sha256, out_root=out_root,
                protocol=protocol, cells=cells, schedule=schedule, mode=mode,
                expected_ccbench_pin=protocol["ccbench_pin"],
                expected_contract_sha256=contract.contract_sha256,
            )
            perf_preflight_receipt = manifest.get("perf_preflight")
            _assert_perf_mode(mode, perf_preflight_receipt)
            manifest_schedule = manifest.get("schedule")
            if not isinstance(manifest_schedule, list):
                raise FloorCampaignError("resume: manifest.schedule が list でない")
            if [dict(row) for row in manifest_schedule] != schedule:
                raise FloorCampaignError(
                    "resume: manifest.schedule が再導出列と不一致 (改竄の疑い, fail-closed)"
                )
            _verify_resume_binaries(
                runtime_built, expected_ccbench_pin=protocol["ccbench_pin"],
                expected_contract_sha256=contract.contract_sha256,
            )
            _verify_resume_store(
                runtime_built, out_root,
                expected_ccbench_pin=protocol["ccbench_pin"],
                expected_contract_sha256=contract.contract_sha256,
            )

        launch_certificate_sha256 = _verify_resume_journal(
            resume_records, run_dir=run_dir, mode=mode, schedule=schedule,
            protocol_sha256=protocol_sha256, freeze_sha256=freeze_sha256,
            manifest_sha256=manifest_sha256, resume_state=resume_state,
            expected_use_perf=_assert_perf_mode(mode, perf_preflight_receipt),
            expected_perf_preflight=(
                manifest.get("perf_preflight")
                if "perf_preflight" in manifest
                else None
            ),
            retry_slots_per_cell=protocol["retry_slots_per_cell"],
        )
        _transition_pre_measure_journal_to_v3(
            journal_path, resume_records, write_capability=run_write_capability,
        )
        try:
            _holdout_admission._record_floor_resume_disqualification(
                repo_root=holdout_repo_root,
                campaign_run_id=campaign_run_id,
                run_relpath=run_relpath,
                protocol_sha256=protocol_sha256,
                freeze_sha256=freeze_sha256,
            )
        except _holdout_admission.HoldoutAdmissionError as exc:
            raise FloorCampaignError(
                f"resume disqualification marker failed: {exc}"
            ) from exc

    if resume_state == "M-finalize-pending":
        try:
            holdout_admission = _inspect_holdout_admission(
                repo_root=holdout_repo_root, protocol=protocol, freeze=freeze,
                freeze_sha256=freeze_sha256, manifest_sha256=manifest_sha256,
                campaign_run_id=campaign_run_id, run_relpath=run_relpath,
                mode=mode, cells=cells, schedule=schedule,
                records=resume_records,
            )
        except _holdout_admission.FloorHoldoutEvidenceError as exc:
            raise FloorCampaignError(
                "finalize-pending floor admission evidence が不正: "
                f"category={exc.category}, reason={exc.reason}"
            ) from exc
        result = assemble_result(
            protocol=protocol, mode=mode, protocol_sha256=protocol_sha256,
            freeze_sha256=freeze_sha256, manifest_sha256=manifest_sha256,
            cells=cells, binaries=artifact_built, records=resume_records,
            holdout_admission=holdout_admission,
            perf_preflight=perf_preflight_receipt, attempt_registry=_capture_floor_attempt_registry_prefix(holdout_repo_root, attempt_registry_plan) if attempt_registry_plan is not None else None,
        )
        apply_refreeze_eligibility()
        problems = _verify_result_with_live_admission(
            result, _expected_protocol(protocol, cells),
            expected_binaries=_journal_expected_binaries(resume_records),
            repo_root=holdout_repo_root, protocol=protocol, freeze=freeze,
            freeze_sha256=freeze_sha256, manifest_sha256=manifest_sha256,
            campaign_run_id=campaign_run_id, run_relpath=run_relpath,
            mode=mode, cells=cells, schedule=schedule,
            records=resume_records,
            expected_use_perf=_assert_perf_mode(mode, perf_preflight_receipt),
        )
        if problems:
            raise FloorCampaignError(
                f"finalize-pending artifact self-check が非空: {problems}")
        staged = _stage_finalize_files(
            run_dir, result, _render_result_md(result),
            write_capability=run_write_capability,
        )
        _finalize(
            run_dir, staged, journal_path, terminal_already_completed=True,
            write_capability=run_write_capability,
        )
        return {"status": "completed", "run_dir": str(run_dir), "result": result}

    use_perf = _assert_perf_mode(mode, perf_preflight_receipt)
    default_measure = measure_fn is None
    if default_measure:
        extime_s = protocol["extime_s"]
        reps = protocol["reps"]
        clocks_per_us = contract.clocks_per_us
        numactl = list(contract.numactl)

        def measure_fn(  # noqa: ANN001
                binary, records, threads, workload, *,
                _holdout_observation_admission):
            rep_observations: list[dict] = []
            admission_kw = (
                {"holdout_observation_admission": _holdout_observation_admission}
                if _holdout_observation_admission is not None else {}
            )
            if use_perf:
                return measure_point(
                    binary, records, threads, clocks_per_us,
                    extime=extime_s, reps=reps, workload=workload,
                    numactl=numactl, rep_observations=rep_observations,
                    **admission_kw,
                )
            return measure_point(
                binary, records, threads, clocks_per_us,
                extime=extime_s, reps=reps, workload=workload,
                numactl=numactl, rep_observations=rep_observations, use_perf=False,
                **admission_kw,
            )

    # floor 実走へ入る最後の artifact gate。current policy に加え、実行中 protocol の
    # ccbench pin と env contract を外部 authority として全 cell へ再束縛する。
    artifact_built = _validate_portable_built(
        artifact_built, expected_ccbench_pin=protocol["ccbench_pin"],
        expected_contract_sha256=contract.contract_sha256,
    )

    # Cell claims are the final durable pre-measurement action outside
    # runner.run(). Environment, reservation, clean-scan, perf, output, build,
    # shared dependency prebuild, and manifest preflights have completed.
    # Live admission revalidation, host provenance, process identity, and the
    # session competition probe remain inside runner.run(), after this claim.
    try:
        holdout_reservation = (
            _holdout_admission._reserve_floor_holdout_observations_core(
                repo_root=holdout_repo_root, protocol=protocol,
                verified_freeze_document=freeze, freeze_sha256=freeze_sha256,
                cells=admission_cells, schedule=schedule,
                campaign_run_id=campaign_run_id, out_root=out_root,
                run_dir=run_dir, run_relpath=run_relpath, mode=mode,
                resume=resume_dir is not None,
                nondefault_seams=sorted(nondefault_seams),
                _neutral_holdouts=_holdout_signature_source,
            )
        )
        holdout_admissions = (
            _holdout_admission.finalize_floor_holdout_admissions(
                holdout_reservation,
            )
        )
    except _holdout_admission.HoldoutAdmissionError as exc:
        raise FloorCampaignError(f"holdout admission reservation failed: {exc}") from exc

    measure_attempt_fn = _wrap_admission_aware_measure(
        measure_fn, admissions=holdout_admissions, cell_by_id=cell_by_id,
        binaries=runtime_built, protocol=protocol,
        freeze_sha256=freeze_sha256, protocol_sha256=protocol_sha256,
        manifest_sha256=manifest_sha256,
        pass_observation_to_internal_measure=default_measure,
    )

    runner = _Runner(
        protocol=protocol, contract=contract, cells=cells, cell_by_id=cell_by_id,
        binaries=runtime_built,
        artifact_binaries=artifact_built,
        schedule=schedule, journal_path=journal_path, measure_fn=measure_attempt_fn,
        holdout_admissions=holdout_admissions,
        probe_fn=probe_fn, sleep_fn=sleep_fn, monotonic_fn=monotonic_fn, now_fn=now_fn,
        protocol_sha256=protocol_sha256, freeze_sha256=freeze_sha256,
        manifest_sha256=manifest_sha256, execution_receipt=execution_receipt,
        launch_certificate_sha256=launch_certificate_sha256,
        records=resume_records,
        host_provenance_fn=host_provenance_fn,
        process_identity_fn=process_identity_fn,
        reservation_check=reservation_check,
        external_checkpoint_binding=external_checkpoint_binding,
        write_capability=run_write_capability,
        perf_preflight=perf_preflight_receipt, mode=mode, certified_attempt_context=_certified_attempt_context(repo_root=holdout_repo_root, campaign_run_id=campaign_run_id, run_relpath=run_relpath, plan=attempt_registry_plan),
    )

    try:
        runner.run()
    except CampaignAbort as exc:
        _journal_append(
            journal_path, {
                "event": "terminal", "status": "aborted", "reason": str(exc),
            }, write_capability=run_write_capability,
        )
        raise

    try:
        holdout_admission = _inspect_holdout_admission(
            repo_root=holdout_repo_root, protocol=protocol, freeze=freeze,
            freeze_sha256=freeze_sha256, manifest_sha256=manifest_sha256,
            campaign_run_id=campaign_run_id, run_relpath=run_relpath,
            mode=mode, cells=cells, schedule=schedule,
            records=runner.records,
        )
    except _holdout_admission.FloorHoldoutEvidenceError as exc:
        reason = f"floor-admission-{exc.category}"
        _journal_append(
            journal_path, {
                "event": "terminal", "status": "artifact-invalid",
                "reason": reason, "cause": exc.reason,
                "problems": [f"{reason}: {exc.reason}"],
            }, write_capability=run_write_capability,
        )
        raise FloorCampaignError(
            "floor admission evidence が不正: "
            f"category={exc.category}, reason={exc.reason}"
        ) from exc

    result = assemble_result(
        protocol=protocol, mode=mode, protocol_sha256=protocol_sha256,
        freeze_sha256=freeze_sha256, manifest_sha256=manifest_sha256,
        cells=cells, binaries=artifact_built, records=runner.records,
        holdout_admission=holdout_admission,
        perf_preflight=perf_preflight_receipt, attempt_registry=_capture_floor_attempt_registry_prefix(holdout_repo_root, attempt_registry_plan) if attempt_registry_plan is not None else None,
    )
    apply_refreeze_eligibility()

    # 自己検査: live admission 公開入口が [] を返すまでは pending bytes も作らない。
    # C3-6/W3 申し送り: journal receipt (session ごとの実測直前 binary_sha256_at_measure) を
    # expected_binaries として渡し、binaries section の突合を恒真検査でなく実発火にする。
    # measured_bin_sha は build 記録 sha と食い違えば _run_session が CampaignAbort するため、
    # 完走した campaign では全 session が一致し、artifact.binaries と完全一致する。
    expected = _expected_protocol(protocol, cells)
    expected_binaries = _journal_expected_binaries(runner.records)
    try:
        problems = _verify_result_with_live_admission(
            result, expected, expected_binaries,
            repo_root=holdout_repo_root, protocol=protocol, freeze=freeze,
            freeze_sha256=freeze_sha256, manifest_sha256=manifest_sha256,
            campaign_run_id=campaign_run_id, run_relpath=run_relpath,
            mode=mode, cells=cells, schedule=schedule,
            records=runner.records, expected_use_perf=use_perf,
        )
    except _holdout_admission.FloorHoldoutEvidenceError as exc:
        reason = f"floor-admission-{exc.category}"
        _journal_append(
            journal_path, {
                "event": "terminal", "status": "artifact-invalid",
                "reason": reason, "cause": exc.reason,
                "problems": [f"{reason}: {exc.reason}"],
            }, write_capability=run_write_capability,
        )
        raise FloorCampaignError(
            "live admission self-check が不正: "
            f"category={exc.category}, reason={exc.reason}"
        ) from exc
    if problems:
        _journal_append(
            journal_path, {
                "event": "terminal", "status": "artifact-invalid",
                "problems": list(problems),
            }, write_capability=run_write_capability,
        )
        raise FloorCampaignError(f"verify_floor_artifact が非空: {problems}")

    # phase 1: 検査済み result/md bytes を pending file へ fsyncする。
    staged = _stage_finalize_files(
        run_dir, result, _render_result_md(result),
        write_capability=run_write_capability,
    )

    _finalize(
        run_dir, staged, journal_path, write_capability=run_write_capability,
    )
    return {"status": "completed", "run_dir": str(run_dir), "result": result}


def _fresh_run_id(protocol_sha256: str, started_at: dt.datetime) -> str:
    return f"{started_at.strftime('%Y%m%dT%H%M%SZ')}-{protocol_sha256[:8]}"


def _fresh_run_dir(out_root: Path, protocol: Mapping, mode: str,
                   protocol_sha256: str, started_at: dt.datetime,
                   *, write_capability: Optional[WriteCapability] = None) -> Path:
    base = Path(env_scope_dir(protocol["env_tag"], output_root=str(out_root)))
    run_dir = (base / "calibration" / f"s8b-floor-{mode}"
               / _fresh_run_id(protocol_sha256, started_at))
    if run_dir.exists():
        exc = FileExistsError(str(run_dir))
        raise FloorCampaignError(f"run_dir が既に存在する: {run_dir}") from exc
    try:
        if write_capability is None:
            run_dir.mkdir(parents=True, exist_ok=False)
        else:
            ensure_directory_with_capability(write_capability, run_dir.parent)
            write_capability._verify_identity()
            os.mkdir(run_dir, 0o700)
    except (FileExistsError, DurableRootError) as exc:
        raise FloorCampaignError(f"run_dir を durable root に作成できない: {run_dir}: {exc}") from exc
    return run_dir


def _load_resume_manifest(
        manifest_path: Path, *, protocol_sha256: str,
        freeze_sha256: str, out_root: Path,
        protocol: Mapping, cells: Sequence[Mapping], schedule: Sequence[Mapping],
        mode: str,
        expected_ccbench_pin: str | None = None,
        expected_contract_sha256: str | None = None,
) -> tuple:
    try:
        raw = manifest_path.read_bytes()
    except OSError as exc:
        raise FloorCampaignError(f"resume: manifest を読めない: {manifest_path}: {exc}") from exc
    try:
        manifest = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_no_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeError, json.JSONDecodeError, FloorCampaignError) as exc:
        raise FloorCampaignError(f"resume: manifest を parse できない: {exc}") from exc
    if not isinstance(manifest, Mapping):
        raise FloorCampaignError("resume: manifest が object でない")
    if manifest.get("schema_version") != MANIFEST_SCHEMA:
        raise FloorCampaignError(
            f"resume: manifest.schema_version が {MANIFEST_SCHEMA} でない "
            "(v1/v2 交差受理を拒否)"
        )
    manifest_sha256 = hashlib.sha256(raw).hexdigest()
    if manifest.get("protocol_sha256") != protocol_sha256:
        raise FloorCampaignError("resume: protocol sha256 が manifest と不一致")
    if manifest.get("freeze_sha256") != freeze_sha256:
        raise FloorCampaignError("resume: freeze sha256 が manifest と不一致")
    try:
        manifest_run_cmd, manifest_indicators = (
            _floor_contract.manifest_perf_validation_context(manifest)
        )
        _floor_contract.validate_manifest_v3(
            manifest, protocol=protocol, protocol_sha256=protocol_sha256,
            freeze_sha256=freeze_sha256, expected_cells=cells,
            expected_schedule=schedule, mode=mode,
            run_cmd=manifest_run_cmd, leading_indicators=manifest_indicators,
        )
    except _floor_contract.FloorContractError as exc:
        raise FloorCampaignError(f"resume: manifest v3 共有契約が不正: {exc}") from exc
    if "perf_preflight" in manifest:
        manifest["perf_preflight"] = _normalize_perf_preflight(
            manifest["perf_preflight"]
        )
    artifact_built = _validate_portable_built(
        manifest.get("binaries"), expected_ccbench_pin=expected_ccbench_pin,
        expected_contract_sha256=expected_contract_sha256,
    )
    runtime_built = resolve_portable_built(
        artifact_built, out_root=out_root,
        expected_ccbench_pin=expected_ccbench_pin,
        expected_contract_sha256=expected_contract_sha256,
    )
    return dict(manifest), manifest_sha256, artifact_built, runtime_built


def _verify_resume_binaries(
        built: Mapping, *, expected_ccbench_pin: str | None = None,
        expected_contract_sha256: str | None = None,
) -> None:
    """resume: manifest 記録の binary_sha256 と disk 上バイナリの実 hash を全セル再照合する。"""
    current_policy = resolve_current_build_admission_policy()
    for cell_id in sorted(built):
        rec = built[cell_id]
        try:
            _binary_admission.validate_portable_binary_record(
                rec, expected_policy=current_policy,
                expected_ccbench_pin=expected_ccbench_pin,
                expected_contract_sha256=expected_contract_sha256,
                expected_cell_id=cell_id,
                expected_holdout_id=rec.get("holdout_id"),
                expected_configuration_id=rec.get("configuration_id"),
            )
        except _binary_admission.BinaryAdmissionError as exc:
            raise FloorCampaignError(
                f"resume: admission receipt 不一致: cell={cell_id}: {exc}"
            ) from exc
        binary = rec.get("binary")
        recorded = rec.get("binary_sha256")
        if not isinstance(binary, str) or not binary:
            raise FloorCampaignError(
                f"resume: セル {cell_id} の manifest.binaries に binary path が無い"
            )
        if not isinstance(recorded, str) or not recorded:
            raise FloorCampaignError(
                f"resume: セル {cell_id} の manifest.binaries に binary_sha256 が無い"
            )
        actual = _full_sha256(Path(binary))
        if actual != recorded:
            raise FloorCampaignError(
                f"resume: セル {cell_id} のバイナリ sha256 が manifest と不一致 "
                f"(記録={recorded} 実測={actual}, path={binary})"
            )


def _verify_resume_journal(records: list[dict], *, run_dir: Path, mode: str,
                           schedule: list[dict], protocol_sha256: str,
                           freeze_sha256: str, manifest_sha256: Optional[str],
                           resume_state: str = "M-running",
                           expected_use_perf: Optional[bool] = None,
                           expected_perf_preflight=(
                               _floor_contract._RESUME_DIAGNOSTIC_EXPECTED_UNSET
                           ),
                           retry_slots_per_cell: int) -> Optional[str]:
    """resume: journal を状態機械で全件検証する (β-6)。

    official は先頭 launch-start・certificate bytes/意味・campaign-start 束縛を検証する。
    pilot は launch-start / certificate key / certificate file の混入を拒否する。その後、
    campaign-start の schema 版 + protocol/freeze/manifest hash 一致、completed の再実行拒否、
    session-start の seq 一意 (duplicate start 拒否) + attempt_id 一意 + planned seq の schedule
    cell/round 一致 + retry (cell_id, retry_ordinal) 一意、session 完了→start 対応を検査する。
    """
    _validate_mode(mode)
    try:
        _floor_contract._validate_resume_diagnostic_events(
            records, expected_perf_preflight=expected_perf_preflight,
        )
    except _floor_contract.FloorContractError as exc:
        raise FloorCampaignError(f"resume: {exc}") from exc
    if resume_state not in _floor_contract._RESUME_STATES:
        raise FloorCampaignError(f"resume state が未知: {resume_state!r}")
    run_dir = Path(run_dir)
    starts = [r for r in records if r.get("event") == "campaign-start"]
    cs = starts[0] if starts else None
    has_measurement = any(
        record.get("event") in {"session-start", "session"} for record in records
    )
    if resume_state in {"L", "M-prestart"}:
        if starts:
            raise FloorCampaignError(f"resume: {resume_state} に campaign-start がある")
    else:
        if len(starts) != 1:
            raise FloorCampaignError("resume: campaign-start はちょうど 1 件でなければならない")
        if cs.get("schema") == "s8b-floor-journal/v2":
            if has_measurement:
                raise FloorCampaignError(
                    "resume: v2 journal に session-start/session があり rep 証跡を復元不能"
                )
        elif cs.get("schema") != JOURNAL_SCHEMA:
            raise FloorCampaignError(
                f"resume: campaign-start.schema が {JOURNAL_SCHEMA} でない (旧版 journal を拒否)"
            )
        if cs.get("protocol_sha256") != protocol_sha256:
            raise FloorCampaignError("resume: campaign-start.protocol_sha256 が不一致")
        if cs.get("freeze_sha256") != freeze_sha256:
            raise FloorCampaignError("resume: campaign-start.freeze_sha256 が不一致")
        if cs.get("manifest_sha256") != manifest_sha256:
            raise FloorCampaignError("resume: campaign-start.manifest_sha256 が不一致")

    launch_certificate_sha256: Optional[str] = None
    launch_starts = [r for r in records if r.get("event") == "launch-start"]
    cert_path = run_dir / "launch_certificate.json"
    if mode == "pilot":
        if resume_state == "L":
            raise FloorCampaignError("resume: pilot は L 状態を持てない")
        if launch_starts:
            raise FloorCampaignError("resume: pilot journal に launch-start が混入している")
        if cs is not None and "launch_certificate_sha256" in cs:
            raise FloorCampaignError(
                "resume: pilot campaign-start に launch_certificate_sha256 が混入している"
            )
        if cert_path.exists():
            raise FloorCampaignError("resume: pilot run_dir に launch_certificate.json が混入している")
    else:
        if len(launch_starts) != 1:
            raise FloorCampaignError("resume: official launch-start はちょうど 1 件でなければならない")
        launch = launch_starts[0]
        if not records or records[0].get("event") != "launch-start":
            raise FloorCampaignError("resume: official launch-start が journal 先頭でない")
        launch_schema_ok = launch.get("schema") == JOURNAL_SCHEMA or (
            launch.get("schema") == "s8b-floor-journal/v2" and not has_measurement
        )
        if not launch_schema_ok:
            raise FloorCampaignError(
                f"resume: launch-start.schema が {JOURNAL_SCHEMA} でない"
            )
        if set(launch) != {"event", "schema", "launch_certificate_sha256", "utc"}:
            raise FloorCampaignError("resume: launch-start の exact key 集合が不一致")
        launch_certificate_sha256 = launch.get("launch_certificate_sha256")
        if not buildcache.is_full_sha256(launch_certificate_sha256):
            raise FloorCampaignError("resume: launch-start certificate sha256 が不正")
        _utc_text(launch.get("utc"), field="resume.launch-start.utc")
        if cs is not None and cs.get("launch_certificate_sha256") != launch_certificate_sha256:
            raise FloorCampaignError(
                "resume: campaign-start と launch-start の launch_certificate_sha256 が不一致"
            )
        if cert_path.is_symlink() or not cert_path.is_file():
            raise FloorCampaignError("resume: launch certificate が regular file でない")
        if resume_state == "L":
            try:
                names = {path.name for path in run_dir.iterdir()}
            except OSError as exc:
                raise FloorCampaignError(f"resume: L run_dir を列挙できない: {exc}") from exc
            if names != {"launch_certificate.json", "journal.jsonl"}:
                raise FloorCampaignError(
                    f"resume: L run_dir の許可 file 集合が不一致: {sorted(names)}")
            if (journal_path := run_dir / "journal.jsonl").is_symlink() \
                    or not journal_path.is_file():
                raise FloorCampaignError("resume: L journal が regular file でない")
        try:
            cert_bytes = cert_path.read_bytes()
        except OSError as exc:
            raise FloorCampaignError(
                f"resume: launch certificate を読めない: {cert_path}: {exc}"
            ) from exc
        actual_cert_sha256 = hashlib.sha256(cert_bytes).hexdigest()
        if actual_cert_sha256 != launch_certificate_sha256:
            raise FloorCampaignError(
                "resume: launch certificate bytes sha256 が launch-start と不一致"
            )

        def cert_pairs(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise FloorCampaignError(
                        f"resume: launch certificate に duplicate key: {key}"
                    )
                result[key] = value
            return result

        try:
            cert = json.loads(
                cert_bytes.decode("utf-8"), object_pairs_hook=cert_pairs,
                parse_constant=_reject_json_constant,
            )
        except FloorCampaignError:
            raise
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise FloorCampaignError(
                f"resume: launch certificate を strict parse できない: {exc}"
            ) from exc
        validate_launch_certificate(
            cert,
            expected_v1_freeze_sha256=freeze_sha256,
            expected_protocol_sha256=protocol_sha256,
            expected_run_id=run_dir.name,
        )
        if cert.get("started_utc") != launch.get("utc"):
            raise FloorCampaignError(
                "resume: launch-start.utc が certificate.started_utc と不一致")

    if resume_state != "M-finalize-pending" and any(
            r.get("event") == "terminal" for r in records):
        raise FloorCampaignError("resume: terminal 済み campaign は再実行しない")

    sched_by_seq = {row["seq"]: row for row in schedule}
    seen_seq: set = set()
    seen_attempt: set = set()
    seen_retry: set = set()
    for r in records:
        if r.get("event") != "session-start":
            continue
        seq = r.get("seq")
        if seq in seen_seq:
            raise FloorCampaignError(f"resume: session-start の seq が重複 (duplicate start): {seq}")
        seen_seq.add(seq)
        aid = r.get("attempt_id")
        if aid in seen_attempt:
            raise FloorCampaignError(f"resume: attempt_id が重複: {aid!r}")
        seen_attempt.add(aid)
        kind = r.get("kind")
        if kind == "planned":
            row = sched_by_seq.get(seq)
            if row is None:
                raise FloorCampaignError(f"resume: planned seq {seq} が schedule に無い")
            if r.get("cell_id") != row["cell_id"] or r.get("round") != row["round"]:
                raise FloorCampaignError(
                    f"resume: seq {seq} の cell/round が schedule と不一致 "
                    f"(journal={r.get('cell_id')}/{r.get('round')} "
                    f"!= schedule={row['cell_id']}/{row['round']})"
                )
        elif kind == "retry":
            key = (r.get("cell_id"), r.get("retry_ordinal"))
            if key in seen_retry:
                raise FloorCampaignError(
                    f"resume: (cell_id, retry_ordinal) が重複 (枠再発行): {key}"
                )
            seen_retry.add(key)
        else:
            raise FloorCampaignError(f"resume: session-start の kind が未知: {kind!r}")

    try:
        _floor_contract.validate_session_start_authorizations(
            [r for r in records if r.get("event") == "session-start"],
            schedule=schedule, retry_slots_per_cell=retry_slots_per_cell,
        )
    except _floor_contract.FloorContractError as exc:
        raise FloorCampaignError(
            f"resume: session-start authorization が正準でない: {exc}"
        ) from exc

    for r in records:
        if r.get("event") != "session":
            continue
        if r.get("seq") not in seen_seq:
            raise FloorCampaignError(
                f"resume: session 完了 (seq {r.get('seq')}) に対応する start が無い"
            )
        missing_evidence = [
            key for key in ("rep_observations", "rep_integrity_failures", "exclusion_class")
            if key not in r
        ]
        if missing_evidence:
            raise FloorCampaignError(
                f"resume: v3 session の rep 証跡 key 欠損: {missing_evidence}"
            )
        try:
            s8b_floor_stats._record_from_mapping(r)
        except (KeyError, TypeError, ValueError) as exc:
            raise FloorCampaignError(f"resume: session の型が不正: {exc}") from exc
        exempt = s8b_floor_stats._rep_evidence_exemption_kind(r) is not None
        derived_failures: Optional[int] = None
        if not exempt:
            if type(expected_use_perf) is not bool:
                raise FloorCampaignError("resume: session 検査に expected_use_perf が無い")
            reps_expected = r.get("reps_expected")
            if type(reps_expected) is not int or reps_expected < 2:
                raise FloorCampaignError("resume: reps_expected が exact int でない")
            evidence_errors, derived_failures, derived_exec_failures, qualified = \
                s8b_floor_stats._derive_rep_integrity(
                    r["rep_observations"], reps=reps_expected,
                    expected_use_perf=expected_use_perf,
                )
            if evidence_errors:
                raise FloorCampaignError(
                    f"resume: rep_observations が不正: {evidence_errors[0]}"
                )
            if (type(r["rep_integrity_failures"]) is not int
                    or r["rep_integrity_failures"] != derived_failures):
                raise FloorCampaignError("resume: rep_integrity_failures が再導出値と不一致")
            if r["exec_failures"] != derived_exec_failures:
                raise FloorCampaignError("resume: exec_failures が再導出値と不一致")
            if tuple(r.get("throughputs", ())) != qualified:
                raise FloorCampaignError("resume: qualified throughputs が rep 証跡と不一致")
        expected_class = (
            r.get("excluded_reason")
            if r.get("excluded_reason") in {_REASON_COMPETING, _REASON_LAUNCH}
            else s8b_floor_stats.REP_INTEGRITY_EXCLUSION_CLASS
            if derived_failures is not None and derived_failures > 0
            else r.get("excluded_reason")
        )
        if r["exclusion_class"] != expected_class:
            raise FloorCampaignError("resume: exclusion_class が再導出値と不一致")
    return launch_certificate_sha256


# --------------------------------------------------------------------------- #
# CLI                                                                           #
# --------------------------------------------------------------------------- #

def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="8b floor campaign driver (floor 案の実測。何も発効させない)",
    )
    parser.add_argument("--mode", choices=["pilot", "official"], required=True)
    parser.add_argument("--protocol", type=Path, required=True,
                        help="floor protocol JSON (s8b-floor-protocol/v2)")
    parser.add_argument("--resume", type=Path, default=None,
                        help="既存 run_dir を forward-only で続行する")
    parser.add_argument(
        "--fetchcontent-base-dir", type=Path, default=None,
        help="staged FetchContent payload の base directory (pilot専用の非default seam)",
    )
    parser.add_argument(
        "--confirm-official-floor-run", action="store_true",
        help="official floor campaign の明示承認",
    )
    return parser


def _reseal_protocol_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog=f"{Path(sys.argv[0]).name} reseal-protocol",
        description="active contract と HEAD gitlink から floor protocol を AI reseal する",
    )


def _check_protocol_index_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog=f"{Path(sys.argv[0]).name} check-protocol-index",
        description="floor protocol の legacy + versioned 組 index を read-only 検査する",
    )


def _resolve_current_protocol_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog=f"{Path(sys.argv[0]).name} resolve-current-protocol",
        description="current floor protocol の sanctioned relative path を解決する",
    )


def _freeze_protocol_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=f"{Path(sys.argv[0]).name} freeze-protocol",
        description="承認済み固定値から floor protocol を人間が実凍結する",
    )
    parser.add_argument("--confirm-user-freeze", action="store_true", required=True)
    return parser


def _resolve_freeze_path(freeze_path_text: str) -> Path:
    path = Path(freeze_path_text)
    return path if path.is_absolute() else ROOT / path


def _load_verified_freeze(path, expected_hash=None):
    """freeze loader (中立 leaf ``s8b_freeze_io``) の floor 境界 adapter。"""
    try:
        return _freeze_io.load_verified_freeze(path, expected_hash)
    except _freeze_io.FreezeIOError as exc:
        raise FloorCampaignError(str(exc)) from exc


def _bounded_diagnostic_line(document: Mapping[str, object]) -> str:
    line = json.dumps(
        dict(document), ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ) + "\n"
    if len(line.encode("utf-8")) > _PRIVATE_DIAGNOSTIC_MAX_BYTES:
        raise ValueError("oracle diagnostic exceeds byte bound")
    return line


def _diagnostic_emission_failure(
        *, stage: str, detail_code: str) -> dict[str, object]:
    return {
        "status": "error",
        "error": (
            "SortSwoOracleUnavailable: "
            "sort-swo-oracle-infrastructure-unavailable"
        ),
        "diagnostic_emission_failure": {
            "event": "diagnostic-emission-failed",
            "stage": stage,
            "detail_code": detail_code,
        },
    }


def _write_diagnostic_line(stream, line: str) -> None:
    written = stream.write(line)
    if written != len(line):
        raise OSError("short diagnostic write")
    stream.flush()


def _emit_sort_swo_unavailable(
        exc: SortSwoOracleUnavailable, *, stdout=None, stderr=None) -> int:
    """元の UNAVAILABLE を rc=1 のまま、bounded な private JSON へ射影する。"""
    output = sys.stdout if stdout is None else stdout
    error_output = sys.stderr if stderr is None else stderr
    try:
        if exc.result is None:
            raise TypeError("oracle result is absent")
        primary = {
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
            "sort_swo_oracle": private_attempt_record(exc.result),
        }
        line = _bounded_diagnostic_line(primary)
    except Exception as diagnostic_exc:
        detail_code = (
            "oracle-result-missing"
            if exc.result is None
            else f"diagnostic-payload-{type(diagnostic_exc).__name__}"
        )
        fallback = _diagnostic_emission_failure(
            stage="payload", detail_code=detail_code,
        )
        try:
            _write_diagnostic_line(output, _bounded_diagnostic_line(fallback))
        except Exception as write_exc:
            terminal = _diagnostic_emission_failure(
                stage="stdout-write",
                detail_code=f"diagnostic-write-{type(write_exc).__name__}",
            )
            try:
                _write_diagnostic_line(
                    error_output, _bounded_diagnostic_line(terminal),
                )
            except Exception:
                pass
        return 1

    try:
        _write_diagnostic_line(output, line)
    except Exception as write_exc:
        fallback = _diagnostic_emission_failure(
            stage="stdout-write",
            detail_code=f"diagnostic-write-{type(write_exc).__name__}",
        )
        try:
            _write_diagnostic_line(
                error_output, _bounded_diagnostic_line(fallback),
            )
        except Exception:
            pass
    return 1


def main(argv=None) -> int:
    cli_argv = list(sys.argv[1:] if argv is None else argv)
    if cli_argv and cli_argv[0] == "reseal-protocol":
        _reseal_protocol_parser().parse_args(cli_argv[1:])
        try:
            outcome = reseal_protocol()
        except FloorCampaignError as exc:
            print(json.dumps({
                "status": "error", "error": f"{type(exc).__name__}: {exc}",
            }, ensure_ascii=False))
            return 1
        print(json.dumps(outcome, ensure_ascii=False, sort_keys=True))
        return 0
    if cli_argv and cli_argv[0] == "check-protocol-index":
        _check_protocol_index_parser().parse_args(cli_argv[1:])
        try:
            index = scan_floor_protocol_index(root=ROOT)
        except FloorCampaignError as exc:
            print(json.dumps({
                "status": "error", "error": f"{type(exc).__name__}: {exc}",
            }, ensure_ascii=False))
            return 1
        records = [
            {
                "path": record.path,
                "contract_sha256": pair[0],
                "ccbench_pin": pair[1],
                "protocol_sha256": record.sha256,
            }
            for pair, record in sorted(index.items())
        ]
        print(json.dumps({
            "status": "ok", "count": len(records), "protocols": records,
        }, ensure_ascii=False, sort_keys=True))
        return 0
    if cli_argv and cli_argv[0] == "resolve-current-protocol":
        _resolve_current_protocol_parser().parse_args(cli_argv[1:])
        try:
            record = resolve_current_floor_protocol(root=ROOT)
        except FloorCampaignError as exc:
            print(json.dumps({
                "status": "error", "error": f"{type(exc).__name__}: {exc}",
            }, ensure_ascii=False))
            return 1
        print(record.path)
        return 0
    if cli_argv and cli_argv[0] == "freeze-protocol":
        freeze_args = _freeze_protocol_parser().parse_args(cli_argv[1:])
        try:
            outcome = freeze_protocol(
                confirm_user_freeze=freeze_args.confirm_user_freeze,
            )
        except FloorCampaignError as exc:
            print(json.dumps({
                "status": "error", "error": f"{type(exc).__name__}: {exc}",
            }, ensure_ascii=False))
            return 1
        print(json.dumps(outcome, ensure_ascii=False))
        return 0

    args = _parser().parse_args(cli_argv)

    # official は CLI でも明示承認を要求する (core も二重に拒否する, δ-3)。
    if args.mode == "official" and args.confirm_official_floor_run is not True:
        print(json.dumps({
            "status": "refused",
            "reason": "official mode は --confirm-official-floor-run による "
                      "明示承認がないため拒否する",
        }, ensure_ascii=False))
        return 2

    supplied_protocol_path = (
        args.protocol if args.protocol.is_absolute() else Path.cwd() / args.protocol
    ).absolute()

    try:
        raw_protocol = load_protocol(supplied_protocol_path)
        try:
            protocol = validate_protocol(raw_protocol)
        except FloorCampaignError as exc:
            raise FloorCampaignError(
                f"canonical protocol validation failed: {exc}"
            ) from exc
        freeze_path = _resolve_freeze_path(protocol["freeze"]["path"])
        verified = _load_verified_freeze(freeze_path, expected_hash=protocol["freeze"]["sha256"])
        out_root = Path(repo_output_root())
        outcome = run_campaign(
            protocol, verified, out_root=out_root, mode=args.mode,
            resume_dir=args.resume,
            fetchcontent_base_dir=args.fetchcontent_base_dir,
            protocol_path=supplied_protocol_path,
            confirm_official_floor_run=args.confirm_official_floor_run,
        )
    except SortSwoOracleUnavailable as exc:
        return _emit_sort_swo_unavailable(exc)
    except FloorCampaignError as exc:
        print(json.dumps({
            "status": "error", "error": f"{type(exc).__name__}: {exc}",
        }, ensure_ascii=False))
        return 1
    print(json.dumps({
        "status": outcome["status"], "run_dir": outcome["run_dir"],
    }, ensure_ascii=False))
    return 0


_FloorAttemptRegistryPlan = s8b_floor_attempt_launcher.FloorAttemptRegistryPlan


@dataclass(frozen=True, slots=True)
class _CertifiedFloorAttemptContext:
    repo_root: Path
    campaign_run_id: str
    run_relpath: str
    registry_plan: _FloorAttemptRegistryPlan


def _protocol_sha256_and_attempt_registry_plan(
        *, protocol: Mapping[str, object], cells: Sequence[Mapping[str, object]],
        schedule: Sequence[Mapping[str, object]], freeze_sha256: str,
        production: bool) -> tuple[str, Optional[_FloorAttemptRegistryPlan]]:
    protocol_sha256 = _canonical_sha256(protocol)
    return protocol_sha256, (
        _build_floor_attempt_registry_plan(
            protocol=protocol, cells=cells, schedule=schedule,
            freeze_sha256=freeze_sha256, protocol_sha256=protocol_sha256,
        ) if production else None
    )


def _certified_attempt_context(
        *, repo_root: Path, campaign_run_id: str, run_relpath: str,
        plan: Optional[_FloorAttemptRegistryPlan]) -> Optional[_CertifiedFloorAttemptContext]:
    if plan is None:
        return None
    return _CertifiedFloorAttemptContext(
        repo_root=Path(repo_root), campaign_run_id=campaign_run_id,
        run_relpath=run_relpath, registry_plan=plan,
    )


def _build_floor_attempt_registry_plan(
        *, protocol: Mapping[str, object], cells: Sequence[Mapping[str, object]],
        schedule: Sequence[Mapping[str, object]], freeze_sha256: str,
        protocol_sha256: str) -> _FloorAttemptRegistryPlan:
    """Freeze the exact planned and retry slot closure for one campaign."""
    try:
        return s8b_floor_attempt_launcher.prepare_floor_attempt_registry_plan(
            protocol=protocol, cells=cells, schedule=schedule,
            freeze_sha256=freeze_sha256, protocol_sha256=protocol_sha256,
        )
    except s8b_floor_attempt_launcher.FloorAttemptLauncherError as exc:
        raise FloorCampaignError(str(exc)) from exc


def _capture_floor_attempt_registry_prefix(
        repo_root: Path, plan: _FloorAttemptRegistryPlan) -> dict[str, object]:
    if type(plan) is not _FloorAttemptRegistryPlan:
        raise FloorCampaignError("attempt registry plan is unavailable")
    return s8b_floor_attempt_launcher.capture_floor_attempt_registry_prefix(
        Path(repo_root), plan,
    )


def _floor_measurement_capture(
        *, cell: Mapping[str, object], binary: str,
        contract: _env_contract.ExecutionEnvironmentContract,
        protocol: Mapping[str, object], expected_use_perf: bool,
        observation_admission: object,
) -> s8b_floor_attempt_launcher.FloorMeasurementCapture:
    return s8b_floor_attempt_launcher.FloorMeasurementCapture(
        binary=binary,
        records=int(cell["records"]),
        threads=int(cell["threads"]),
        clocks_per_us=contract.clocks_per_us,
        keyword_arguments={
            "extime": protocol["extime_s"],
            "reps": protocol["reps"],
            "workload": dict(cell["workload"]),
            "numactl": tuple(contract.numactl),
            "use_perf": expected_use_perf,
            "holdout_observation_admission": observation_admission,
        },
    )


def _floor_terminal_builder(
        *, runner: _Runner, seq: int, round_no: int,
        cell: Mapping[str, object], kind: str,
        retry_ordinal: Optional[int], attempt_id: str,
        trigger: Optional[str], binary: str,
) -> Callable[[s8b_floor_attempt_launcher.OpenedFloorAttempt],
              s8b_floor_attempt_launcher.FloorAttemptTerminal]:
    def build(
        opened: s8b_floor_attempt_launcher.OpenedFloorAttempt,
    ) -> s8b_floor_attempt_launcher.FloorAttemptTerminal:
        scale_point = opened.measurement
        if scale_point is None:
            throughputs = []
            exec_failures = runner.reps
            rep_observations = []
            rep_integrity_failures = None
            run_cmd = None
            failure = opened.failure or {}
            notes = [
                f"measure 失敗: {failure.get('exception_type', 'RuntimeError')}: "
                f"{str(failure.get('message', 'measurement unavailable'))[:200]}"
            ]
        else:
            projection = _project_scalepoint(
                scale_point, reps=runner.reps,
                expected_use_perf=opened.expected_use_perf,
            )
            throughputs = projection["throughputs"]
            exec_failures = projection["exec_failures"]
            rep_observations = projection["rep_observations"]
            rep_integrity_failures = projection["rep_integrity_failures"]
            run_cmd = _project_measure_run_cmd(
                getattr(scale_point, "run_cmd", None),
                runtime_binary=binary,
                portable_binary=runner.artifact_binaries[str(cell["cell_id"])]["binary"],
                workload=cell["workload"], records=int(cell["records"]),
                threads=int(cell["threads"]), protocol=runner.protocol,
                contract=runner.contract, perf_preflight=runner.perf_preflight,
                mode=runner.mode,
            )
            notes = list(getattr(scale_point, "notes", []) or [])
        assessment = None
        if scale_point is not None:
            try:
                assessment = s8b_floor_stats.assess_session(
                    throughputs, reps=runner.reps,
                    session_cv_max=runner.session_cv_max,
                )
            except s8b_floor_stats.FloorStatsError as exc:
                raise CampaignAbort(
                    f"assess_session 内部不変条件破れ: {exc}"
                ) from exc
        session_cv = None if assessment is None else assessment.cv
        assessed_median = None if assessment is None else assessment.median
        derived_reason = None if assessment is None else assessment.required_reason
        post_competing = (
            opened.probe_after is not None
            and opened.probe_after["competing"] is True
        )
        if opened.probe_before["competing"] is True or post_competing:
            excluded_reason: Optional[str] = _REASON_COMPETING
        elif opened.failure is not None:
            excluded_reason = _REASON_LAUNCH
        elif exec_failures >= runner.reps:
            excluded_reason = _REASON_LAUNCH
        elif exec_failures > 0 and derived_reason is None:
            excluded_reason = _REASON_LAUNCH
        elif (
            rep_integrity_failures is not None
            and rep_integrity_failures > 0
            and derived_reason == _REASON_PARTIAL
        ):
            excluded_reason = _REASON_PARTIAL
        else:
            excluded_reason = derived_reason
        reason = (
            runner._check_reason(excluded_reason)
            if excluded_reason is not None else None
        )
        median = (
            assessed_median if reason is None and exec_failures == 0 else None
        )
        valid = median is not None
        exclusion_class = (
            reason if reason in {_REASON_COMPETING, _REASON_LAUNCH}
            else s8b_floor_stats.REP_INTEGRITY_EXCLUSION_CLASS
            if rep_integrity_failures is not None and rep_integrity_failures > 0
            else reason
        )
        record = {
            "event": "session", "kind": kind, "seq": seq, "round": round_no,
            "retry_ordinal": retry_ordinal, "attempt_id": attempt_id,
            "trigger": trigger, "cell_id": cell["cell_id"],
            "holdout_id": cell["holdout_id"],
            "configuration_id": cell["configuration_id"],
            "records": cell["records"], "threads": cell["threads"],
            "workload": cell["workload"], "throughputs": list(throughputs),
            "reps_expected": runner.reps, "exec_failures": exec_failures,
            "excluded_reason": reason, "retry": kind == "retry",
            "rep_observations": [dict(item) for item in rep_observations],
            "rep_integrity_failures": rep_integrity_failures,
            "session_median": median, "valid": valid, "session_cv": session_cv,
            "exclusion_class": exclusion_class, "duration_s": opened.duration_s,
            "run_cmd": run_cmd, "notes": notes,
            "probe_before": dict(opened.probe_before),
            "probe_after": (
                None if opened.probe_after is None else dict(opened.probe_after)
            ),
            "binary_sha256_at_measure": opened.binary_sha256_at_measure,
        }
        raw = s8b_floor_attempt_launcher.serialize_floor_session_record(record)
        observation_sha256 = (
            s8b_floor_attempt_launcher.canonical_floor_payload_sha256(
                record["rep_observations"]
            )
            if valid else None
        )
        return s8b_floor_attempt_launcher.FloorAttemptTerminal(
            raw_output_bytes=raw,
            terminal_status="observed" if valid else "retryable-failure",
            report_sha256=hashlib.sha256(raw).hexdigest(),
            observation_sha256=observation_sha256,
            primary_value=float(median) if valid else None,
            finished_at=opened.finished_at,
            campaign_record=record,
        )

    return build


def _run_certified_floor_session(
        runner: _Runner, *, seq: int, round_no: int, cell_id: str, kind: str,
        retry_ordinal: Optional[int], attempt_id: str, trigger: Optional[str],
        start_mono: float, cut6_existing_consumption_marker: bool) -> dict:
    """Run phase 1, preserve the unconsumed competing branch, then launch."""

    context = runner.certified_attempt_context
    if type(context) is not _CertifiedFloorAttemptContext:
        raise CampaignAbort("certified attempt context is invalid")
    try:
        pre_probe = s8b_floor_attempt_launcher.probe_floor_attempt_preconditions(
            post_probe=s8b_floor_attempt_launcher.floor_post_probe_capability(),
        )
    except s8b_floor_attempt_launcher.FloorAttemptLauncherError as exc:
        raise CampaignAbort(f"certified floor pre-probe refused: {exc}") from exc
    cell = runner.cell_by_id[cell_id]
    if pre_probe.competing:
        if cut6_existing_consumption_marker:
            raise CampaignAbort(
                "cut6_replay_pre_probe_competing_existing_marker"
            )
        probe_before = s8b_floor_attempt_launcher.read_floor_attempt_pre_probe(
            pre_probe
        )
        return runner._finish_session(
            seq=seq, round_no=round_no, cell_id=cell_id, kind=kind,
            retry_ordinal=retry_ordinal, attempt_id=attempt_id, trigger=trigger,
            throughputs=[], exec_failures=0,
            excluded_reason=_REASON_COMPETING, rep_observations=[],
            rep_integrity_failures=None, assessed_median=None, session_cv=None,
            duration_s=runner._elapsed(start_mono),
            probe_before=dict(probe_before),
            probe_after=None, run_cmd=None,
            notes=["preflight probe 競合で計測をスキップ"],
            binary_sha256_at_measure=runner.binaries[cell_id]["binary_sha256"],
        )
    admission = runner.holdout_admissions[cell_id]
    measurement_ordinal = 0 if kind == "planned" else retry_ordinal
    if type(measurement_ordinal) is not int or measurement_ordinal < 0:
        raise CampaignAbort("certified floor measurement ordinal is invalid")
    slot_key = (cell_id, round_no, measurement_ordinal)
    try:
        s8b_floor_attempt_launcher.require_floor_attempt_registry_slot(
            context.registry_plan, slot_key,
        )
    except s8b_floor_attempt_launcher.FloorAttemptLauncherError as exc:
        raise CampaignAbort(str(exc)) from exc
    try:
        runner.holdout_assert_fn(
            admission, cell=_admission_cell(cell), protocol=runner.protocol,
            freeze_sha256=runner.freeze_sha256,
            protocol_sha256=runner.protocol_sha256,
            manifest_sha256=runner.manifest_sha256,
        )
        observation = _holdout_admission.consume_attempt_ticket(
            admission, attempt_id=attempt_id,
        )
        marker = _holdout_admission.validate_floor_attempt_consumption_marker(
            admission, attempt_id=attempt_id,
        )
    except _holdout_admission.HoldoutAdmissionError as exc:
        raise CampaignAbort(
            f"holdout attempt admission refused: cell={cell_id}: {exc}"
        ) from exc
    run_start = getattr(runner, "_certified_run_start_record", None)
    if not isinstance(run_start, Mapping):
        raise CampaignAbort("certified floor run-start record is unavailable")
    process_identity = {
        key: run_start.get(key) for key in ("pid", "starttime", "execution_uuid")
    }
    reservation_request = s8b_floor_attempt_launcher.floor_attempt_reservation(
        context.registry_plan,
        slot_key=slot_key,
        repo_root=context.repo_root,
        protocol=runner.protocol,
        mode=runner.mode,
        perf_preflight_receipt=runner.perf_preflight,
        consumption_marker=marker,
        run_start_receipt_sha256=(
            s8b_floor_attempt_launcher.canonical_floor_payload_sha256(
                dict(run_start)
            )
        ),
        process_identity=process_identity,
        started_at=str(run_start.get("utc")),
        admission_claim_digest=admission.measurement_generation_claim_digest,
        attempt_id=attempt_id,
        campaign_run_id=context.campaign_run_id,
        manifest_sha256=runner.manifest_sha256,
        run_relpath=context.run_relpath,
        cell_id=cell_id,
        records=int(cell["records"]),
        threads=int(cell["threads"]),
        workload=dict(cell["workload"]),
    )
    measurement = _floor_measurement_capture(
        cell=cell, binary=runner.binaries[cell_id]["binary"],
        contract=runner.contract, protocol=runner.protocol,
        expected_use_perf=runner.use_perf,
        observation_admission=observation,
    )
    terminal_builder = _floor_terminal_builder(
        runner=runner, seq=seq, round_no=round_no, cell=cell, kind=kind,
        retry_ordinal=(None if kind == "planned" else measurement_ordinal),
        attempt_id=attempt_id, trigger=trigger,
        binary=runner.binaries[cell_id]["binary"],
    )
    try:
        launched = s8b_floor_attempt_launcher.launch_probed_floor_attempt(
            reservation_request,
            s8b_floor_attempt_launcher.floor_attempt_registry_genesis(
                context.registry_plan
            ),
            measurement,
            pre_probe=pre_probe,
            classified_at=lambda: runner.now_fn().isoformat(),
            terminal_builder=terminal_builder,
        )
    except (
        s8b_floor_attempt_launcher.FloorAttemptLauncherError,
        s8b_floor_attempt_launcher.FloorAttemptRegistryError,
        _holdout_admission.HoldoutAdmissionError,
    ) as exc:
        raise CampaignAbort(f"certified floor attempt refused: {exc}") from exc
    record = launched.terminal.campaign_record
    if type(record) is not dict:
        raise CampaignAbort("certified launcher terminal campaign record is not exact dict")
    runner._emit(record)
    return record


if __name__ == "__main__":
    sys.exit(main())
