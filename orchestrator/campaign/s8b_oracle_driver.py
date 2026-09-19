# -*- coding: utf-8 -*-
"""8b oracle の実行 gate、binding 実体化、block 単位 driver。"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import inspect
import json
import math
import os
import re
import socket
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from typing import Mapping, Optional, Sequence
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

_HERE = Path(__file__).resolve().parent
_ORCHESTRATOR = _HERE.parent
ROOT = _ORCHESTRATOR.parent

from . import buildcache, model, pipeline, s8b_budget, s8b_run_marker, wal  # noqa: E402
from . import s8b_expected_materialization as _expected_materialization  # noqa: E402
from orchestrator.calibrator import perf_preflight as _perf_preflight  # noqa: E402
from .build_admission import (  # noqa: E402
    GeneratorId,
    ReviewId,
    build_run_context,
    resolve_current_build_admission_policy,
)
from . import s8b_binary_admission as _binary_admission  # noqa: E402
from . import s8b_abort_reason_contract as _abort_reason_contract  # noqa: E402
from . import campaign_claim as _campaign_claim  # noqa: E402
from . import s8b_freeze_io as _freeze_io  # noqa: E402
from . import s8b_oracle_manifest as _oracle_manifest  # noqa: E402
from . import s8b_holdout_admission as _holdout_admission  # noqa: E402
from . import s8b_oracle_spec  # noqa: E402
from . import env_contract as _env_contract  # noqa: E402
from . import env_attestation as _env_attestation  # noqa: E402
from . import execution_guard  # noqa: E402
from . import site_policy  # noqa: E402  (実機 site 観測)
from . import reservation as _reservation  # noqa: E402
from . import s8b_ratified_freeze  # noqa: E402
from . import s8b_oracle_artifacts as _oracle_artifacts  # noqa: E402
from . import t080_freeze_migration as _t080_migration  # noqa: E402
from . import freeze_verification_hold as _freeze_hold  # noqa: E402
from .layout import (  # noqa: E402
    _OFFICIAL_OUTPUT_ROOT_ENV,
    campaign_layout,
)
from .layout import write_capability_for_directory  # noqa: E402
from .durable_root import DurableRootError, DurableRootPolicy  # noqa: E402
from .s1_direct_comparison import (  # noqa: E402
    DriverError as S1DriverError,
    PreparedCell,
    _condition_driver_id,
    _condition_request_digests_for_flags,
    condition_gate_receipt,
    prepare_cell,
    require_returned_condition_evidence,
)
from .s8b_materialization import (  # noqa: E402
    MaterializationError,
    binding_entry,
    prepared_binding as _materialization_prepared_binding,
    reviewed_source_capability,
)
from . import s1_known_axes_freeze, s8b_holdout_freeze  # noqa: E402
from .s8b_oracle_manifest import (  # noqa: E402
    VerifiedManifest,
    config_for_block,
    verify_manifest,
)


SESSION_STAGE = model.STAGE_S8B_ORACLE_SESSION
SESSION_ISSUER = model.S8B_ORACLE_SESSION_ISSUER
DEFAULT_FREEZE_PATH = ROOT / "output/s8b-freeze/holdout_freeze.json"
DEFAULT_BUDGET_PATH = ROOT / "output/s8b-budget/time_ledger.json"
_BINDING_KEYS = {
    "genome_canonical", "src_token", "variant_id", "entry_sha256",
    "binding_sha256",
}

# C2-2: oracle の完走予約式。schedule や CLI から上書きできない凍結定数である。
# per-attempt cap は build + legacy/S2 verify + bench + materialize/cleanup を含む
# end-to-end 上限。最大 1 retry と terminal/fsync 用 reserve を別項で数える。
ORACLE_MAX_ATTEMPTS = 2
ORACLE_PER_ATTEMPT_CAP_S = 30 * 60
# attestation probe 1 回あたりの所要時間を別項で数える。
ORACLE_ATTESTATION_PROBE_S = 0.2
ORACLE_FINALIZE_RESERVE_S = 600
ORACLE_RESERVATION_SAFETY_MARGIN_S = 0


class OracleDriverError(RuntimeError):
    """8b oracle の入力・identity・実行契約を検証できない場合の拒否。"""


def _machine_env_tag_for_site(site: str) -> str:
    """実機 site 観測から machine-pin の registry-derived tag を解決する。"""
    if site == site_policy.PEGASUS_COMPUTE:
        try:
            return _env_contract.lookup_required_attestation_contract().env_tag
        except _env_contract.EnvContractError as exc:
            raise OracleDriverError(
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
            raise OracleDriverError(
                "machine-pin: none attestation contract を一意に解決できない"
            ) from exc
        if (len(candidate_contracts) != 1
                or len(candidate_tags) != 1
                or len(registry_tags) != len(registry_tag_set)):
            raise OracleDriverError(
                "machine-pin: none attestation contract を一意に解決できない"
            )
        return candidate_contracts[0].env_tag
    raise OracleDriverError(f"machine-pin: 未対応 site {site!r}")


class _UnknownAbortReason(OracleDriverError):
    """pipeline の abort reason を凍結済み outcome へ射影できない。"""

    def __init__(self, reason: str):
        super().__init__(f"未知の pipeline abort reason: {reason}")
        self.reason = reason


@dataclass
class GateDecision:
    allowed: bool
    refusals: list[str]
    t080_freeze_migration_observation: Optional[Mapping[str, object]]
    held_checks: tuple[Mapping[str, object], ...] = ()


class _AdapterRefusals(list):
    """既存の list 契約を保ったまま held marker を gate factory へ運ぶ。"""

    def __init__(self, values=(), *, held_checks=()):
        super().__init__(values)
        self.held_checks = tuple(held_checks)


def _resolve_t080_receipt(*, root: Path, launch_validated=None) -> "_t080_migration.ReceiptResolution":
    """T-080 receipt を一度だけ解決し、分類不能も明示拒否へ閉じる。"""
    try:
        if launch_validated is not None:
            return _t080_migration.verify_receipt(
                root=Path(root), launch_validated=launch_validated,
            )
        return _t080_migration.verify_receipt(root=Path(root))
    except _t080_migration.MigrationError as exc:
        detail = f" {exc.detail}" if exc.detail else ""
        refusal = f"migration-receipt-verify: [{exc.reason}]{detail}"
    except Exception as exc:  # noqa: BLE001 (分類不能は拒否側へ倒す)
        refusal = (
            "migration-receipt-verify: [receipt.invalid] "
            f"{type(exc).__name__}: {exc}"
        )
    return _t080_migration.ReceiptResolution(
        state="invalid",
        refusals=(refusal,),
        t080_freeze_migration_observation=None,
        validation_head="",
    )


def _make_gate_decision(
        resolution: "_t080_migration.ReceiptResolution", *,
        refusals: Sequence[str],
        held_checks: Sequence[Mapping[str, object]] = ()) -> GateDecision:
    """receipt refusal と observation を欠落なく GateDecision へ束ねる。"""
    merged = [*resolution.refusals, *refusals]
    unique_held = {}
    for marker in (*getattr(resolution, "held_checks", ()), *held_checks):
        unique_held[marker["check_id"]] = marker
    return GateDecision(
        allowed=not merged,
        refusals=merged,
        t080_freeze_migration_observation=(
            resolution.t080_freeze_migration_observation
            if (not merged and resolution.state == "active-valid") else None
        ),
        held_checks=tuple(unique_held.values()),
    )


def _campaign_t080_value(
        resolution: "_t080_migration.ReceiptResolution") -> Mapping[str, object]:
    """campaign-start/run result 用の耐久 epoch record を作る。"""
    if (resolution.state == "active-valid" and not resolution.refusals
            and resolution.t080_freeze_migration_observation is not None):
        return resolution.t080_freeze_migration_observation
    if (resolution.state == "never-issued" and not resolution.refusals
            and re.fullmatch(r"[0-9a-f]{40}", resolution.validation_head)):
        return {"state": "never-issued", "validation_head": resolution.validation_head}
    raise OracleDriverError(
        "T-080 campaign epoch を active-valid/never-issued のどちらにも固定できない"
    )


def _t080_epoch_identity(
        resolution: "_t080_migration.ReceiptResolution") -> tuple[object, ...]:
    """campaign-start 境界で再照合する receipt epoch の決定論 identity。"""
    raw_sha256 = (
        hashlib.sha256(resolution.receipt_raw).hexdigest()
        if isinstance(resolution.receipt_raw, bytes) else None
    )
    return (
        resolution.state,
        resolution.introduction_commit,
        raw_sha256,
        resolution.validation_head,
    )


def _t080_adapter_refusals(
        *, resolution: "_t080_migration.ReceiptResolution",
        freeze: Mapping, freeze_sha256: str, freeze_path: Path,
        root: Path) -> Optional[list[str]]:
    """発火条件を満たす場合だけ static adapter の refusal を返す。

    ``None`` は legacy verifier へ委譲することを表す。発火後の raw 再読で
    差替え・欠落を検出した場合は legacy へ戻さず migration 側の拒否にする。
    """
    receipt = resolution.receipt
    if resolution.state != "active-valid" or not isinstance(receipt, Mapping):
        return None
    known_record = freeze.get("known_axes_freeze")
    held_checks = []
    known_record_pin_matches = (
        isinstance(known_record, Mapping)
        and known_record.get("sha256") == _t080_migration.KNOWN_AXES_RAW_SHA256
    )
    if _freeze_hold.HELD:
        held_checks.append(_freeze_hold.held_marker(
            "s8b-oracle.known-axes-recorded-pin",
        ))
        known_record_pin_matches = isinstance(known_record, Mapping)
    fires = (
        isinstance(known_record, Mapping)
        and freeze_sha256 == receipt["artifacts"]["holdout"]["raw_sha256"]
        and known_record.get("path") == _t080_migration.KNOWN_AXES_REL
        and known_record_pin_matches
    )
    if not fires:
        return None

    try:
        holdout_raw = Path(freeze_path).read_bytes()
    except OSError as exc:
        return _AdapterRefusals([
            "holdout-freeze-verify: [holdout.artifact_bytes] "
            f"holdout bytes を読めない: {type(exc).__name__}: {exc}"
        ], held_checks=held_checks)
    if hashlib.sha256(holdout_raw).hexdigest() != freeze_sha256:
        return _AdapterRefusals([
            "holdout-freeze-verify: [holdout.artifact_bytes] "
            "検証後に holdout raw bytes が変化した"
        ], held_checks=held_checks)

    known_path = root / _t080_migration.KNOWN_AXES_REL
    try:
        known_raw = known_path.read_bytes()
    except OSError as exc:
        return _AdapterRefusals([
            "known-axes-freeze-verify: [known_axes.artifact_bytes] "
            f"known_axes bytes を読めない: {type(exc).__name__}: {exc}"
        ], held_checks=held_checks)
    if _freeze_hold.HELD:
        held_checks.append(_freeze_hold.held_marker(
            "s8b-oracle.known-axes-live-bytes",
        ))
    elif hashlib.sha256(known_raw).hexdigest() != _t080_migration.KNOWN_AXES_RAW_SHA256:
        return _AdapterRefusals([
            "known-axes-freeze-verify: [known_axes.artifact_bytes] "
            "known_axes raw bytes が legacy pin と不一致"
        ], held_checks=held_checks)

    try:
        adapted = _t080_migration.static_gate_adapter(
            resolution=resolution,
            known_raw=known_raw,
            holdout_raw=holdout_raw,
            root=root,
        )
    except _t080_migration.MigrationError as exc:
        prefix = "migration-receipt-verify"
        if exc.reason.startswith("known_axes."):
            prefix = "known-axes-freeze-verify"
        elif exc.reason.startswith("holdout."):
            prefix = "holdout-freeze-verify"
        detail = f" {exc.detail}" if exc.detail else ""
        return _AdapterRefusals(
            [f"{prefix}: [{exc.reason}]{detail}"], held_checks=held_checks,
        )
    except Exception as exc:  # noqa: BLE001 (adapter 分類不能も拒否)
        return _AdapterRefusals([
            "migration-receipt-verify: [receipt.invalid] "
            f"{type(exc).__name__}: {exc}"
        ], held_checks=held_checks)
    held_checks.extend(adapted.held_checks)
    return _AdapterRefusals(adapted.refusals, held_checks=held_checks)


def _canonical_bytes(value) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise OracleDriverError(f"canonical JSON に変換できない: {exc}") from exc


def _canonical_sha256(value) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _mutable_json_tree(value):
    """deep-frozen JSON tree を legacy manifest verifier の入力 shape へ射影する。

    検証や再 parse は行わず、Mapping→dict / tuple→list の container 型だけを戻す。
    oracle の freeze/floor consumer 自体は LaunchValidatedFreeze の同一 object を使う。
    """
    if isinstance(value, Mapping):
        return {key: _mutable_json_tree(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_mutable_json_tree(child) for child in value]
    return value


def _load_json_object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise OracleDriverError(f"JSON を読めない: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise OracleDriverError(f"JSON top-level が object でない: {path}")
    return value


def _load_verified_freeze(path, expected_hash: Optional[str] = None):
    """freeze loader (中立 leaf ``s8b_freeze_io``) の driver 境界 adapter。

    leaf は ``FreezeIOError`` を投げる。driver 経路 (gate_check / run_block / main)
    が観測する例外型・message・rc・refusal 文字列を現行と一致させるため、ここで
    ``OracleDriverError`` へ因果付き変換する (message 本文は leaf 側で現行文字列を
    維持している)。再エクスポートはしない (leaf 単体の例外型は ``FreezeIOError``、
    driver 経路の例外型は ``OracleDriverError``)。"""
    try:
        return _freeze_io.load_verified_freeze(path, expected_hash)
    except _freeze_io.FreezeIOError as exc:
        raise OracleDriverError(str(exc)) from exc


def _manifest_structural_refusal(path: Path) -> Optional[str]:
    """active 解決不能時にも freeze 非依存の manifest 構造異常を集約する。

    実走の full verify は引き続き ``verify_manifest`` 1 回だけ。ここでは top-level /
    schedule / binding schema だけを同 module の validator で検査し、freeze bytes や
    floor artifact を別 loader で読まない。
    """
    try:
        document = _oracle_manifest._load_json_object(Path(path))
        if set(document) != _oracle_manifest._MANIFEST_KEYS:
            raise _oracle_manifest.ManifestError("manifest top-level schema が不一致")
        if document.get("schema_version") != _oracle_manifest.SCHEMA_VERSION:
            raise _oracle_manifest.ManifestError("manifest schema_version が不一致")
        _oracle_manifest.validate_schedule(document.get("schedule"))
        _oracle_manifest._validate_binding_identity(
            document.get("binding_identity"), schedule=document["schedule"],
        )
    except Exception as exc:  # noqa: BLE001 (構造検査不能も refusal として集約)
        return f"manifest-verify: {type(exc).__name__}: {exc}"
    return None


def _resolve_recorded_path(path_text: str, *, root: Path) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else root / path


def _gate_check_core(*, freeze_path=None, manifest_path=None, root,
                     t080_resolution: "_t080_migration.ReceiptResolution",
                     approved_spec,
                     manifest_verification_error: Optional[BaseException],
                     standalone_manifest_verification: bool,
                     verified: Optional["_freeze_io.VerifiedFreeze"] = None,
                     verified_manifest: Optional["VerifiedManifest"] = None,
                     launch_validated: Optional[
                         "s8b_ratified_freeze.LaunchValidatedFreeze"
                     ] = None,
                     ratified_error: Optional[str] = None) -> GateDecision:
    """検証済み入力を共通の gate predicates へ通す内部実装。

    ``launch_validated`` を与えた実走経路では、その同一 object の ratified document /
    sha256 だけを使う。``verified`` (legacy ``load_verified_freeze`` の戻り値) を
    与えた gate 単体経路では freeze を
    再読込せず、その単一 object の document/sha256 だけを使う (A3-6: verify-use
    間差替えの遮断)。与えない場合は自身で ``load_verified_freeze`` を一度呼ぶ。

    run-block から ``verified_manifest`` を与えた場合は manifest を再検証・再読込せず、
    その単一 object だけを使う (C2-9)。公開 gate の注入経路だけは token exact type、
    manifest 実 bytes の canonical hash、approved spec hash を再束縛する。

    v2 (floor/budget のいずれかが non-null) の freeze は exact type
    ``LaunchValidatedFreeze`` が無い限り admission しない。``ratified_error``
    (呼出側の active 世代解決失敗の構造化 message) があれば ``freeze-ratify:``
    refusal へ翻訳する。無くて token も無ければ refusal
    ``v2-execution: launch-validate: LaunchValidatedFreeze exact type が必要``
    を積む。error が無くて token があれば sha256 を照合する。いずれの場合も
    拒否理由の集約 (known-axes / floor / budget / manifest) は継続する。
    core は ``load_ratified_freeze`` を呼ばない。
    """
    if (launch_validated is not None
            and type(launch_validated) is not s8b_ratified_freeze.LaunchValidatedFreeze):
        return _make_gate_decision(
            t080_resolution,
            refusals=[
                "v2-execution: launch-validate: validated freeze object の型が不正"
            ],
        )
    root = Path(root)
    refusals: list[str] = []
    held_checks: list[Mapping[str, object]] = []
    freeze: Optional[dict] = None
    freeze_sha: Optional[str] = None
    adapter_refusals: Optional[list[str]] = None

    if launch_validated is not None:
        freeze = launch_validated.ratified.document
        freeze_sha = launch_validated.ratified.sha256
    elif verified is not None:
        freeze = verified.document
        freeze_sha = verified.sha256
    else:
        try:
            loaded = _load_verified_freeze(Path(freeze_path))
        except Exception as exc:
            refusals.append(f"holdout-freeze-verify: {type(exc).__name__}: {exc}")
        else:
            freeze = loaded.document
            freeze_sha = loaded.sha256

    if freeze is not None:
        adapter_refusals = _t080_adapter_refusals(
            resolution=t080_resolution,
            freeze=freeze,
            freeze_sha256=freeze_sha,
            freeze_path=Path(freeze_path),
            root=root,
        )
        if adapter_refusals is not None:
            refusals.extend(adapter_refusals)
            held_checks.extend(adapter_refusals.held_checks)
        elif freeze.get("floor") is None and freeze.get("budget") is None:
            try:
                # v1 verifier は floor/budget がともに null の freeze だけを対象にする。
                # v2 実走経路はこの枝に入らず下の承認束縛検証へ倒れるため、ここでの
                # path 再読込は A3-6 の単一 object 対象外。
                s8b_holdout_freeze.verify(Path(freeze_path), root=root)
            except Exception as exc:
                refusals.append(
                    f"holdout-freeze-verify: {type(exc).__name__}: {exc}"
                )
        else:
            # v2 (floor または budget が non-null) freeze: exact な LaunchValidatedFreeze
            # を要求する。core は active 世代を自分で解決しない (D1872)。
            if ratified_error is not None:
                refusals.append(f"freeze-ratify: {ratified_error}")
            elif launch_validated is None:
                refusals.append(
                    "v2-execution: launch-validate: "
                    "LaunchValidatedFreeze exact type が必要"
                )
            elif (freeze_sha is None
                  or freeze_sha != launch_validated.ratified.sha256):
                refusals.append(
                    "freeze-not-active-generation: "
                    "与えられた freeze bytes sha256 が承認束縛済み active 世代と不一致"
                )

    if adapter_refusals is None:
        try:
            known_record = freeze.get("known_axes_freeze") if isinstance(freeze, Mapping) else None
            if not isinstance(known_record, Mapping):
                raise OracleDriverError("known_axes_freeze source record がない")
            known_path_text = known_record.get("path")
            if not isinstance(known_path_text, str) or not known_path_text:
                raise OracleDriverError("known_axes_freeze.path が空でない文字列でない")
            known_path = _resolve_recorded_path(known_path_text, root=root)
            s1_known_axes_freeze.verify(
                known_path, source_resolver=lambda relative: root / relative,
            )
        except Exception as exc:
            refusals.append(f"known-axes-freeze-verify: {type(exc).__name__}: {exc}")

    if not isinstance(freeze, Mapping) or freeze.get("floor") is None:
        refusals.append("floor-null: freeze.floor が null")
    if not isinstance(freeze, Mapping) or freeze.get("budget") is None:
        refusals.append("budget-null: freeze.budget が null")

    if manifest_path is not None:
        manifest_path = Path(manifest_path)
        if freeze is None or freeze_sha is None:
            # freeze が読めない場合は manifest を freeze に対して検証できない
            # (freeze byte hash 照合が不能)。freeze 側 refusal は既に積まれている。
            refusals.append(
                "manifest-verify: freeze が読めず manifest を検証できない"
            )
        elif standalone_manifest_verification and verified_manifest is None:
            # 単体 gate 経路: freeze byte hash 照合は verify_manifest 内で担保される
            # (freeze_document/freeze_sha256 必須)。C2-9 の共有経路では run_block が
            # 検証済み object を渡すためこの枝には入らない。
            try:
                approved = s8b_oracle_spec.load_approved_spec(root)
                verify_manifest(
                    manifest_path, root=root,
                    freeze_document=freeze, freeze_sha256=freeze_sha,
                    approved_spec=approved,
                )
            except Exception as exc:
                refusals.append(f"manifest-verify: {type(exc).__name__}: {exc}")
        elif standalone_manifest_verification:
            try:
                approved = s8b_oracle_spec.load_approved_spec(root)
                if type(verified_manifest) is not VerifiedManifest:
                    raise OracleDriverError(
                        "verified_manifest が VerifiedManifest exact type でない"
                    )
                actual = _oracle_manifest._load_json_object(manifest_path)
                if (verified_manifest.sha256
                        != _oracle_manifest._canonical_sha256(actual)
                        or verified_manifest.sha256
                        != _oracle_manifest._canonical_sha256(
                            verified_manifest.document
                        )):
                    raise OracleDriverError(
                        "verified_manifest.sha256 が manifest 実 bytes/document と不一致"
                    )
                if verified_manifest.document.get("spec_sha256") != approved.sha256:
                    raise OracleDriverError(
                        "verified_manifest.spec_sha256 が approved spec と不一致"
                    )
            except Exception as exc:
                refusals.append(f"manifest-verify: {type(exc).__name__}: {exc}")
        elif verified_manifest is None:
            exc = manifest_verification_error
            if exc is None:
                refusals.append("manifest-verify: 検証済み manifest object がない")
            else:
                refusals.append(
                    f"manifest-verify: {type(exc).__name__}: {exc}"
                )
        elif (type(verified_manifest) is not VerifiedManifest
              or type(approved_spec) is not s8b_oracle_spec.ReviewedSpec
              or verified_manifest.document.get("spec_sha256")
              != approved_spec.sha256):
            refusals.append(
                "manifest-verify: run flow の manifest/spec snapshot 束縛が不正"
            )

    return _make_gate_decision(
        t080_resolution, refusals=refusals, held_checks=held_checks,
    )


def gate_check(*, freeze_path=None, manifest_path=None, root,
               verified: Optional["_freeze_io.VerifiedFreeze"] = None,
               verified_manifest: Optional["VerifiedManifest"] = None,
               ratified: Optional["s8b_ratified_freeze.RatifiedFreeze"] = None,
               ratified_error: Optional[str] = None) -> GateDecision:
    """standalone gate。v2 freeze は full launch validation を通らない限り受理しない。

    ``RatifiedFreeze`` の注入は active static loader の代替候補にすぎず、検証済み型の
    注入口にはしない。v2 候補は同一 object のまま ``launch_validate`` へ厳密 1 回
    渡し、失敗は単一の ``v2-execution: launch-validate:`` refusal へ変換する。
    """
    root = Path(root)
    if ratified_error is not None:
        return _make_gate_decision(
            _resolve_t080_receipt(root=root), refusals=[f"freeze-ratify: {ratified_error}"],
        )

    loaded = verified
    if loaded is None:
        try:
            loaded = _load_verified_freeze(Path(freeze_path))
        except Exception:
            # 従来どおり freeze / known axes / floor / budget / manifest の refusal を
            # 集約する。core が loader 例外を構造化する。
            return _gate_check_core(
                freeze_path=freeze_path, manifest_path=manifest_path, root=root,
                t080_resolution=_resolve_t080_receipt(root=root),
                approved_spec=None, manifest_verification_error=None,
                standalone_manifest_verification=True,
                verified_manifest=verified_manifest,
            )

    freeze = loaded.document
    is_v2 = (isinstance(freeze, Mapping)
             and (freeze.get("floor") is not None
                  or freeze.get("budget") is not None))
    if not is_v2:
        return _gate_check_core(
            freeze_path=freeze_path, manifest_path=manifest_path, root=root,
            t080_resolution=_resolve_t080_receipt(root=root),
            approved_spec=None, manifest_verification_error=None,
            standalone_manifest_verification=True,
            verified=loaded, verified_manifest=verified_manifest,
        )

    candidate = ratified
    if candidate is None:
        try:
            candidate = s8b_ratified_freeze.load_ratified_freeze(root)
        except s8b_ratified_freeze.RatifiedFreezeError as exc:
            return _gate_check_core(
                freeze_path=freeze_path, manifest_path=manifest_path, root=root,
                t080_resolution=_resolve_t080_receipt(root=root),
                approved_spec=None, manifest_verification_error=None,
                standalone_manifest_verification=True,
                verified=loaded, verified_manifest=verified_manifest,
                ratified_error=f"[{exc.reason}] {exc}",
            )
        except Exception as exc:  # noqa: BLE001 (fail-closed)
            return _gate_check_core(
                freeze_path=freeze_path, manifest_path=manifest_path, root=root,
                t080_resolution=_resolve_t080_receipt(root=root),
                approved_spec=None, manifest_verification_error=None,
                standalone_manifest_verification=True,
                verified=loaded, verified_manifest=verified_manifest,
                ratified_error=f"{type(exc).__name__}: {exc}",
            )
    try:
        validated = s8b_ratified_freeze.launch_validate(candidate, root)
    except s8b_ratified_freeze.RatifiedFreezeError as exc:
        return _make_gate_decision(
            _resolve_t080_receipt(root=root),
            refusals=[f"v2-execution: launch-validate: [{exc.reason}] {exc}"],
        )
    except Exception as exc:  # noqa: BLE001 (fail-closed)
        return _make_gate_decision(
            _resolve_t080_receipt(root=root),
            refusals=[
                f"v2-execution: launch-validate: {type(exc).__name__}: {exc}"
            ],
        )
    return _gate_check_core(
        freeze_path=freeze_path, manifest_path=manifest_path, root=root,
        t080_resolution=_resolve_t080_receipt(root=root, launch_validated=validated),
        approved_spec=None, manifest_verification_error=None,
        standalone_manifest_verification=True,
        verified=loaded, verified_manifest=verified_manifest,
        launch_validated=validated,
    )


def _gate_check_validated(
        *, freeze_path=None, manifest_path=None, root,
        t080_resolution: "_t080_migration.ReceiptResolution",
        launch_validated: "s8b_ratified_freeze.LaunchValidatedFreeze",
        approved_spec,
        manifest_verification_error: Optional[BaseException],
        verified_manifest: Optional["VerifiedManifest"] = None) -> GateDecision:
    """run-block 専用 gate。呼出側が得た同一 validated object を再検証しない。"""
    if type(launch_validated) is not s8b_ratified_freeze.LaunchValidatedFreeze:
        return _make_gate_decision(
            t080_resolution,
            refusals=[
                "v2-execution: launch-validate: validated freeze object の型が不正"
            ],
        )
    return _gate_check_core(
        freeze_path=freeze_path, manifest_path=manifest_path, root=root,
        t080_resolution=t080_resolution,
        approved_spec=approved_spec,
        manifest_verification_error=manifest_verification_error,
        standalone_manifest_verification=False,
        launch_validated=launch_validated,
        verified_manifest=verified_manifest,
    )


@contextlib.contextmanager
def _prepared_binding(
        *, freeze: Mapping, holdout_id: str, configuration_id: str,
        ccbench_pin: str, cxx: str, prepare_fn):
    """共有 materializer の境界 wrapper。identity 合成の MaterializationError だけを
    OracleDriverError へ因果付き変換する (WAL・ログの reason 文字列を現行と一致させる)。
    consumer body から投げ返される他例外・cleanup 例外はそのまま透過させる。"""
    try:
        with _materialization_prepared_binding(
                freeze=freeze, holdout_id=holdout_id,
                configuration_id=configuration_id, ccbench_pin=ccbench_pin, cxx=cxx,
                prepare_fn=prepare_fn) as (identity, prepared):
            yield identity, prepared
    except MaterializationError as exc:
        raise OracleDriverError(str(exc)) from exc


def _expected_binding(manifest: Mapping, holdout_id: str,
                      configuration_id: str) -> dict:
    raw = manifest.get("binding_identity")
    candidate = None
    if isinstance(raw, Mapping):
        for key in (f"{holdout_id}:{configuration_id}",
                    f"{holdout_id}/{configuration_id}"):
            if isinstance(raw.get(key), Mapping):
                candidate = raw[key]
                break
        if candidate is None:
            for value in raw.values():
                if (isinstance(value, Mapping)
                        and value.get("holdout_id") == holdout_id
                        and value.get("configuration_id") == configuration_id):
                    candidate = value
                    break
    elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
        for value in raw:
            if (isinstance(value, Mapping)
                    and value.get("holdout_id") == holdout_id
                    and value.get("configuration_id") == configuration_id):
                candidate = value
                break
    if not isinstance(candidate, Mapping):
        raise OracleDriverError(
            f"manifest binding_identity がない: {holdout_id}/{configuration_id}"
        )
    projected = {
        key: value for key, value in candidate.items()
        if key not in {"holdout_id", "configuration_id"}
    }
    if set(projected) != _BINDING_KEYS:
        raise OracleDriverError(
            f"manifest binding_identity schema が不一致: {sorted(set(projected) ^ _BINDING_KEYS)}"
        )
    _canonical_bytes(projected)
    return projected


def _append_session(layout, env_tag: str, event: str, payload: Mapping) -> None:
    wal.log(
        layout, SESSION_ISSUER, SESSION_STAGE, env_tag,
        {"event": event, **dict(payload)},
    )


def _session_events(layout) -> list[dict]:
    return [dict(record.payload) for record in wal.read_records(layout)
            if record.stage == SESSION_STAGE]


def _iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _is_transient_prepare_failure(exc: BaseException) -> bool:
    current: Optional[BaseException] = exc
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, (OSError, subprocess.SubprocessError)):
            return True
        current = current.__cause__ or current.__context__
    return False


def _perf_for_holdout(freeze: Mapping, holdout_id: str,
                      run_contract: Mapping) -> pipeline.PerfConfig:
    try:
        authority = s8b_holdout_freeze.HOLDOUTS[holdout_id]
        expected_projection = {
            "candidate_id": authority["candidate_id"],
            "records": authority["records"],
            "threads": authority["threads"],
            "ycsb": dict(authority["ycsb"]),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise OracleDriverError(
            f"holdout perf binding が不正: {holdout_id}"
        ) from exc

    try:
        holdout = freeze["holdouts"][holdout_id]
        records = holdout["records"]
        threads = holdout["threads"]
        workload = holdout["ycsb"]
        extime = run_contract["extime"]
        reps = run_contract["reps"]
    except (KeyError, TypeError) as exc:
        raise OracleDriverError(f"holdout/perf 構成が不完全: {holdout_id}") from exc
    if (isinstance(records, bool) or not isinstance(records, int) or records <= 0
            or isinstance(threads, bool) or not isinstance(threads, int) or threads <= 0
            or not isinstance(workload, Mapping)):
        raise OracleDriverError(f"holdout perf schema が不正: {holdout_id}")
    actual_projection = {
        "candidate_id": holdout.get("candidate_id"),
        "records": records,
        "threads": threads,
        "ycsb": dict(workload),
    }
    if _canonical_bytes(actual_projection) != _canonical_bytes(
            expected_projection):
        raise OracleDriverError(
            f"holdout perf binding が不正: {holdout_id}"
        )
    return pipeline.PerfConfig(
        records=records, threads=threads, workload=dict(workload),
        extime=extime, reps=reps,
    )


def _trial_measurements(records: Sequence[object]) -> tuple[dict, float]:
    abort_payload: dict = {}
    bench_wall_s = 0.0
    for record in records:
        payload = getattr(record, "payload", None)
        if not isinstance(payload, Mapping):
            continue
        if getattr(record, "stage", None) == "abort":
            abort_payload = dict(payload)
        if getattr(record, "stage", None) in {"bench_done", "abort"}:
            value = payload.get("bench_wall_s")
            if (not isinstance(value, bool) and isinstance(value, (int, float))
                    and math.isfinite(float(value)) and float(value) >= 0):
                bench_wall_s = max(bench_wall_s, float(value))
    return abort_payload, bench_wall_s


def _outcome_for(result, abort_payload: Mapping) -> str:
    if getattr(result, "certified", False) and not getattr(result, "aborted", True):
        return "committed"
    reason = str(abort_payload.get("reason") or getattr(result, "abort_reason", "") or "abort")
    verdict = str(getattr(result, "verdict", "") or "")
    if abort_payload.get("verify") is not None or (verdict and verdict != "serializable"):
        return "correctness-red"
    if reason in _abort_reason_contract.BUILD_FAILED_ABORT_REASONS:
        return "build-failed"
    if reason == "bench-binary-mismatch":
        # C3-5: 事前 store 検査 (第一防壁) を抜けた TOCTOU 差替えを pipeline 照合
        # (第二防壁) が捕捉した terminal outcome。build_done 後・verify 前に起きるため
        # 既存の build/verify/bench バケツのどれにも適合しない専用 terminal を新設し、
        # report の閉表・証拠 truth table・judge の unknown 伝播まで一貫して通す。
        return "binary-mismatch"
    if reason in _abort_reason_contract.TIMEOUT_ABORT_REASONS:
        return "timeout"
    if reason in _abort_reason_contract.VERIFY_INCONCLUSIVE_ABORT_REASONS:
        return "verify-inconclusive"
    if reason in _abort_reason_contract.BENCH_FAILED_ABORT_REASONS:
        return "bench-failed"
    raise _UnknownAbortReason(reason)


@dataclass
class _V2Plan:
    """v2 実走前検査 (_prepare_v2_execution) の成果。

    ``contract`` = authorized contract 内の契約 (clocks_per_us / numactl の正本)。
    ``authorization_contract`` = certified sink へ渡す process-local receipt。
    ``receipt`` = 共有 execution guard の receipt (WAL campaign-start に記録)。
    """
    contract: "_env_contract.ExecutionEnvironmentContract"
    authorization_contract: "_env_contract.AuthorizedContract"
    receipt: dict
    verified_calibration: Optional["_env_attestation.VerifiedCalibration"] = None
    reservation_check: Optional["_reservation.ReservationCheck"] = None


def _reservation_required_s(schedule: Sequence[Mapping]) -> float:
    """validated schedule の行数だけから worst-case 秒数を導出する。"""
    if (not isinstance(schedule, Sequence)
            or isinstance(schedule, (str, bytes, bytearray)) or not schedule):
        raise OracleDriverError("reservation 導出対象 schedule が空または sequence でない")
    return (
        len(schedule) * ORACLE_MAX_ATTEMPTS * ORACLE_PER_ATTEMPT_CAP_S
        + ORACLE_FINALIZE_RESERVE_S
        + len(schedule) * ORACLE_ATTESTATION_PROBE_S
    )


def _store_sha256(out_root, store_path: str) -> Optional[str]:
    """out_root 相対 (または絶対) store_path の bytes full sha256 (無ければ None)。"""
    candidate = Path(store_path)
    if not candidate.is_absolute():
        candidate = Path(out_root) / store_path
    try:
        data = candidate.read_bytes()
    except OSError:
        return None
    return hashlib.sha256(data).hexdigest()


def _prepare_v2_execution(*, validated, run_contract, schedule,
                          out_root, repo_root=ROOT, environ=None) -> _V2Plan:
    """v2 実走前検査を一括で行い _V2Plan を返す (run marker 作成前)。

    ``validated`` は run_block が一度だけ launch_validate して得た同一 object であり、
    floor artifact の再読込・再 parse・再正規化は行わない。順に: (1) 型境界、
    (2) run contract の env 導出 (env_tag が RatifiedFreeze と一致・env 契約 lookup・
    contract_sha256/clocks 完全一致・machine-pin)、(3) 共有 guard receipt 生成、
    (4) ``validated.binaries_by_cell`` だけを使う binary store 消費 (schedule 全行の store 実体の
    存在 + full sha256 一致)。いずれの不整合も OracleDriverError (呼び出し元が refusal
    に翻訳)。store の内部整合を検査し、hash は測定側へ渡さない。"""
    if not isinstance(validated, s8b_ratified_freeze.LaunchValidatedFreeze):
        raise OracleDriverError("LaunchValidatedFreeze が無い (v2 実走の前提破れ)")
    ratified = validated.ratified

    # (2) env 導出 (C3-9 部分): run_contract.env_tag == RatifiedFreeze.env_tag。
    env_tag = run_contract.get("env_tag")
    ratified_env = ratified.document.get("env_tag")
    if env_tag != ratified_env:
        raise OracleDriverError(
            f"run_contract.env_tag ({env_tag!r}) が RatifiedFreeze.env_tag "
            f"({ratified_env!r}) と不一致"
        )
    try:
        authorization_contract = _env_contract.authorize(env_tag)
        contract = authorization_contract.contract
    except _env_contract.EnvContractError as exc:
        raise OracleDriverError(f"env 契約 authorize 失敗: {exc}") from exc
    # (3) machine-pin + contract_sha256/clocks 完全一致 (共有 guard 経由)。
    try:
        execution_guard.assert_machine_pin(
            contract,
            machine_env_tag=_machine_env_tag_for_site(site_policy.current_site()),
        )
    except execution_guard.ExecutionGuardError as exc:
        raise OracleDriverError(str(exc)) from exc
    if run_contract.get("contract_sha256") != contract.contract_sha256:
        raise OracleDriverError(
            "run_contract.contract_sha256 が env 契約 lookup 結果と不一致"
        )
    if run_contract.get("clocks") != contract.clocks_per_us:
        raise OracleDriverError(
            "run_contract.clocks が env 契約 clocks_per_us と不一致"
        )
    try:
        verified = _env_attestation.load_verified_calibration(contract, Path(repo_root))
        if verified.sha256 != contract.calibration_ref.sha256:
            raise OracleDriverError("verified calibration sha256 が contract ref と不一致")
        if contract.attestation_mode == "required":
            calibration = verified.calibration
            if (calibration is None or calibration.env_tag != contract.env_tag
                    or calibration.clocks_per_us != contract.clocks_per_us):
                raise OracleDriverError("verified calibration が別 contract に属する")
        if contract.attestation_mode == "required":
            receipt = execution_guard.attest_and_build_receipt(contract, verified)
        else:
            # mode=none は既存 v1 issuer を不変に保つ。
            receipt = execution_guard.build_receipt(contract)
        if not execution_guard.receipt_matches_contract(
                receipt, env_tag=contract.env_tag,
                contract_sha256=contract.contract_sha256,
                attestation_mode=contract.attestation_mode,
                verified_calibration=(verified if contract.attestation_mode == "required"
                                      else None)):
            raise OracleDriverError("execution receipt の契約再検算に失敗")
    except (_env_attestation.AttestationError,
            execution_guard.ExecutionGuardError) as exc:
        raise OracleDriverError(f"execution attestation 失敗: {exc}") from exc

    reservation_check = None
    if _reservation.is_reservation_required(contract.isolation_policy):
        env = os.environ if environ is None else environ
        try:
            binding = _reservation.read_binding(env)
            reservation_check = _reservation.check_reservation(
                binding,
                required_s=_reservation_required_s(schedule),
                safety_margin_s=ORACLE_RESERVATION_SAFETY_MARGIN_S,
                environ=env,
            )
        except _reservation.ReservationError as exc:
            raise OracleDriverError(f"reservation binding 検査失敗: {exc}") from exc

    # (4) binary store 消費 (C3-7): receipt を store 読込前に検査し、全 schedule
    # 行分の store 実体 + record SHA + receipt subject SHA を検査する。
    expected = validated.binaries_by_cell
    current_admission_policy = resolve_current_build_admission_policy()
    preflight: list[tuple[tuple[str, str], Mapping]] = []
    for row in schedule:
        cell = (row["holdout_id"], row["configuration_id"])
        cell_id = f"{cell[0]}::{cell[1]}"
        rec = expected.get(cell_id)
        if rec is None:
            raise OracleDriverError(
                f"floor artifact に schedule cell の binary receipt が無い: {cell}"
            )
        if ("admission_receipt" not in rec
                or rec.get("admission_receipt") is None
                or rec.get("admission_receipt") == {}):
            raise OracleDriverError(
                f"[admission-missing] floor binary admission receipt が無い: {cell}"
            )
        expected_binary_keys = _binary_admission.portable_built_keys_for(cell[1])
        if not isinstance(rec, Mapping) or set(rec) != set(expected_binary_keys):
            raise OracleDriverError(
                f"[admission-mismatch] floor binary の configuration 条件付き "
                f"exact key 集合が不一致: {cell}"
            )
        try:
            _binary_admission.validate_portable_binary_record(
                rec, expected_policy=current_admission_policy,
                expected_ccbench_pin=run_contract["ccbench_pin"],
                expected_contract_sha256=run_contract.get("contract_sha256"),
                expected_cell_id=cell_id,
                expected_holdout_id=cell[0],
                expected_configuration_id=cell[1],
                expected_entry_sha256=rec["binding"]["entry_sha256"],
                expected_binding_sha256=rec["binding"]["binding_sha256"],
            )
        except (KeyError, TypeError, _binary_admission.BinaryAdmissionError) as exc:
            raise OracleDriverError(
                f"[admission-mismatch] floor binary admission receipt が不正: {cell}: {exc}"
            ) from exc
        preflight.append((cell, rec))

    for cell, rec in preflight:
        actual = _store_sha256(out_root, rec["store_path"])
        if actual is None:
            raise OracleDriverError(
                f"[store-missing] floor 計測 binary の store 実体が無い: "
                f"{rec['store_path']} (cell={cell})"
            )
        if actual != rec["binary_sha256"]:
            raise OracleDriverError(
                f"[store-hash-mismatch] store binary sha256 が floor receipt と不一致: "
                f"{rec['store_path']} (cell={cell})"
            )
    return _V2Plan(
        contract=contract, authorization_contract=authorization_contract,
        receipt=receipt,
        verified_calibration=verified, reservation_check=reservation_check,
    )


def _execution_identity(plan: _V2Plan) -> dict:
    """terminal/claim で共有する job/host/boot/process identity。"""
    binding = plan.reservation_check.binding if plan.reservation_check is not None else None
    attestation = plan.receipt.get("attestation")
    hostname = binding.host if binding is not None else (
        attestation.get("hostname") if isinstance(attestation, Mapping) else socket.gethostname()
    )
    boot_id = binding.boot_id if binding is not None else (
        attestation.get("boot_id") if isinstance(attestation, Mapping) else None
    )
    return {
        "job": binding.job_id if binding is not None else (os.environ.get("PBS_JOBID") or "unbound"),
        "host": hostname or socket.gethostname(),
        "boot": boot_id or "unavailable",
        "pid": os.getpid(),
        "starttime": _campaign_claim.read_proc_starttime(),
    }


def _claim_identity(*, manifest_sha256: str, freeze_sha256: str,
                    schedule_sha256: str, campaign_id: str) -> str:
    return _canonical_sha256({
        "manifest_sha256": manifest_sha256,
        "freeze_sha256": freeze_sha256,
        "schedule_sha256": schedule_sha256,
        "campaign_id": campaign_id,
    })


def _acquire_g12_claim(*, plan: _V2Plan, claim_root: Path,
                       manifest_sha256: str, freeze_sha256: str,
                       schedule_sha256: str, campaign_id: str,
                       identity: Mapping) -> None:
    """required single-process contract の global one-shot claim を取得する。

    ``claim_root`` は共有 durable ``out_root/claims`` でなければならない。複数 clone
    間の排他は clone が同じ out_root を共有するときだけ成立する。
    """
    if not _reservation.is_reservation_required(plan.contract.isolation_policy):
        return
    claim_identity = _claim_identity(
        manifest_sha256=manifest_sha256, freeze_sha256=freeze_sha256,
        schedule_sha256=schedule_sha256, campaign_id=campaign_id,
    )
    record = _campaign_claim.ClaimRecord(
        campaign_identity=claim_identity,
        protocol_digest=claim_identity,
        job_id=str(identity["job"]), host=str(identity["host"]),
        boot_id=str(identity["boot"]), pid=int(identity["pid"]),
        proc_starttime=int(identity["starttime"]), created_utc=_iso_now(),
    )
    try:
        _campaign_claim.acquire_claim(claim_root, record)
    except _campaign_claim.ClaimError as exc:
        raise OracleDriverError(f"G12 campaign claim 取得失敗: {exc}") from exc


def _append_campaign_terminal(layout, env_tag: str, *, status: str,
                              scheduled_rows: int, completed_rows: int,
                              execution_identity: Mapping) -> None:
    """exactly-one campaign terminal を WAL へ耐久化する。"""
    if status not in {"completed", "aborted"}:
        raise OracleDriverError(f"campaign terminal status が不正: {status!r}")
    existing = [event for event in _session_events(layout)
                if event.get("event") == "campaign-terminal"]
    if existing:
        raise OracleDriverError("campaign-terminal を二重に書こうとした")
    _append_session(layout, env_tag, "campaign-terminal", {
        "status": status,
        "scheduled_rows": scheduled_rows,
        "completed_rows": completed_rows,
        "execution_identity": dict(execution_identity),
    })


def _recheck_required_execution(plan: _V2Plan, *, remaining_rows: int) -> None:
    """各 schedule 行の直前に reservation と required attestation を再検査する。"""
    if plan.reservation_check is None:
        return
    required_s = (
        remaining_rows * ORACLE_MAX_ATTEMPTS * ORACLE_PER_ATTEMPT_CAP_S
        + ORACLE_FINALIZE_RESERVE_S
        + remaining_rows * ORACLE_ATTESTATION_PROBE_S
    )
    try:
        plan.reservation_check = plan.reservation_check.ensure_remaining(
            required_s=required_s,
            safety_margin_s=ORACLE_RESERVATION_SAFETY_MARGIN_S,
        )
        refreshed = execution_guard.attest_and_build_receipt(
            plan.contract, plan.verified_calibration,
        )
        if not execution_guard.receipt_matches_contract(
                refreshed, env_tag=plan.contract.env_tag,
                contract_sha256=plan.contract.contract_sha256,
                attestation_mode=plan.contract.attestation_mode,
                verified_calibration=plan.verified_calibration):
            raise OracleDriverError("途中 attestation receipt の契約再検算に失敗")
    except (_reservation.ReservationError, execution_guard.ExecutionGuardError) as exc:
        raise OracleDriverError(f"途中 execution guard 失敗: {exc}") from exc


@contextlib.contextmanager
def _assert_v2_build_contract(contract: "_env_contract.ExecutionEnvironmentContract"):
    """Assert BuildResult contract provenance for non-driver unit callers."""
    original = pipeline.buildcache.build_v2

    def checked(*args, **kwargs):
        result = original(*args, **kwargs)
        assert result.contract_sha256 == contract.contract_sha256, (
            "pipeline BuildResult.contract_sha256 が oracle contract と不一致: "
            f"{result.contract_sha256!r} != {contract.contract_sha256!r}"
        )
        return result

    pipeline.buildcache.build_v2 = checked
    try:
        yield
    finally:
        pipeline.buildcache.build_v2 = original


@contextlib.contextmanager
def _assert_v2_build_contract_for_snapshot(
        contract: "_env_contract.ExecutionEnvironmentContract", *,
        entry: Mapping, configuration_id: str, ccbench_pin: str,
        cxx: str, prepared):
    """Pass one declaration to each real ``build_v2`` and assert provenance.

    A replacement builder that does not expose the descriptor keyword skips
    the build-owned gate together with the real compiler.  It cannot produce
    declaration proof fields accepted at the S8b receipt boundary.
    """
    original = pipeline.buildcache.build_v2
    try:
        signature = inspect.signature(original)
        descriptor_aware = (
            "expected_materialization_descriptor" in signature.parameters
            or any(
                parameter.kind is inspect.Parameter.VAR_KEYWORD
                for parameter in signature.parameters.values()
            )
        )
    except (TypeError, ValueError):
        descriptor_aware = False
    try:
        descriptor = (
            _expected_materialization.expected_materialization_descriptor(
                ccbench_commit=ccbench_pin,
                configuration=configuration_id,
                declaration=entry,
            )
        )
    except _expected_materialization.ExpectedMaterializationError as exc:
        raise OracleDriverError(
            f"oracle build declaration を記述子へ固定できない: {exc}"
        ) from exc

    def checked(*args, **kwargs):
        if descriptor_aware:
            kwargs["expected_materialization_descriptor"] = descriptor
        result = original(*args, **kwargs)
        assert result.contract_sha256 == contract.contract_sha256, (
            "pipeline BuildResult.contract_sha256 が oracle contract と不一致: "
            f"{result.contract_sha256!r} != {contract.contract_sha256!r}"
        )
        return result

    pipeline.buildcache.build_v2 = checked
    try:
        yield
    finally:
        pipeline.buildcache.build_v2 = original


def _ensure_campaign(layout, *, manifest_sha256: str, block_id: str,
                     campaign_id: str, freeze_sha256: str, marker_root) -> None:
    """実走前に claim を確立する。既に着手済みなら択 (a) で resume を全拒否する。

    R6: WAL byte の存在 / 実走済みマーカーの存在 / campaign.lock の存在の三重判定で、
    どれか一つでも存在すれば当該 freeze/campaign は着手済みとみなし resume を拒否する
    (§9 項 8 択 (a) = 途中 crash は実験全体を判定不能へ)。順序は「マーカー生成 →
    (呼び出し元が) campaign-start」。マーカーは `--output-root` 非依存の場所に置くため、
    出力先の付け替えで拒否を迂回できない。
    """
    layout.ensure()
    preimage = _canonical_bytes({
        "manifest_sha256": manifest_sha256,
        "block_id": block_id,
        "campaign_id": campaign_id,
    }).decode("utf-8")

    # (1) truncated/汚染 WAL を含む「byte が存在する WAL」の resume を閉じる。
    #     read_records() が末尾切れの 1 行を捨てて [] を返す経路でも byte 存在で拒否。
    if wal.wal_bytes_present(layout):
        raise OracleDriverError(
            "既存 WAL byte を持つ oracle campaign の resume は拒否 (択 a・truncated 含む)"
        )
    # (2) 実走済みマーカー (--output-root 非依存・freeze byte hash 束縛) の存在で全拒否。
    if s8b_run_marker.marker_exists(marker_root, freeze_sha256):
        raise OracleDriverError(
            "実走済みマーカーが存在する freeze の再走は全拒否 (択 a)"
        )
    # (3) 原子的 one-shot lock。既存 lock = 並行起動 or 着手済み → resume 拒否。
    #     ここから campaign-start までが排他区間。
    if not wal.acquire_lock_atomic(layout, preimage):
        raise OracleDriverError(
            "campaign.lock が既に存在するため resume/並行起動を拒否 (択 a)"
        )
    # (4) マーカー生成 (campaign-start より前)。原子的 exclusive-create が競合を捕捉する。
    try:
        s8b_run_marker.create_run_marker(marker_root, freeze_sha256, {
            "campaign_id": campaign_id,
            "block_id": block_id,
            "manifest_sha256": manifest_sha256,
        })
    except s8b_run_marker.RunMarkerError as exc:
        raise OracleDriverError(
            f"実走済みマーカーの原子的生成に失敗 (再走の可能性): {exc}"
        ) from exc


def run_block(
        *, manifest_path, block_id, freeze_path, root, output_root, budget_path,
        marker_root=None, evaluate_fn=None, prepare_fn=None,
        durable_root_policy: Optional[DurableRootPolicy] = None) -> dict:
    """一つの immutable block を直列実行し、terminal status を耐久化して返す。

    gate 拒否時は一切書き込まず ``status="refused"`` を返す。

    ``evaluate_fn`` は既存 oracle テスト用 seam だが、注入 callable の返却物にも
    materializer が採取した supply/meaning の二 record と完全一致する evidence を要求する。
    build 0 回で evidence の無い callable は terminal outcome へ進めない。production の既定
    ``pipeline.evaluate`` が呼ぶ実 build は引き続き
    ``_assert_v2_build_contract_for_snapshot`` が descriptor 付きにする。

    戻り値 JSON 契約 (CLI が ``_exit_code`` で終了コードへ射影する):

    - ``status`` — 次のいずれか (かっこ内は CLI rc):
      ``completed`` (0): 全予定行が一意 terminal outcome + 対応 budget terminal
      record を耐久化し、held reservation を実測へ精算した (強い completed 定義)。
      ``protocol_violation`` (3): 1 行以上が binding-refused / prepare 恒久失敗 /
      未実行で強い completed 定義を満たさない。``unresolved_rows`` に未達
      schedule_index を載せ、reservation は精算せず held のまま残す (fail-closed)。
      ``budget_exhausted_before_attempt`` (2): 一括予約が確保できず一行も走らない。
      ``error`` (1): 実行中の内部逸脱 (未分類 abort reason / reservation 枠超過)。
      reservation を非解放のまま残し ``error`` に理由を載せる。
      ``refused`` (2): 実走前 gate が拒否し ``refusals`` に全拒否理由を載せる。
    - ``completed_trials`` — 一意 terminal outcome + budget entry を得た行数。
    - ``unresolved_rows`` — protocol_violation 時のみ。未達 schedule_index の列。
    - ``error`` — error 時のみ。逸脱理由の文字列。
    - ``events`` — WAL に耐久化した session event の逐次列 (terminal event を含む)。
    - ``allowed`` / ``refusals`` / ``campaign_id`` / ``manifest_sha256`` /
      ``freeze_sha256`` / ``schedule_sha256`` — gate 判定と block identity。

    rc 優先順位は ``_exit_code`` を正本とする:
    internal-error(1) > protocol_violation(3) > budget-refused(2) > completed(0)。
    """
    freeze_path = Path(freeze_path)
    root = Path(root)
    # E3b: active 世代を一度だけ解決して launch validation 済み型へ昇格する。
    # 以後の freeze / floor / binary consumer はこの同一 object だけを使う。
    try:
        ratified = s8b_ratified_freeze.load_ratified_freeze(root)
    except s8b_ratified_freeze.RatifiedFreezeError as exc:
        refusals = [f"freeze-ratify: [{exc.reason}] {exc}"]
        manifest_refusal = _manifest_structural_refusal(Path(manifest_path))
        if manifest_refusal is not None:
            refusals.append(manifest_refusal)
        decision = _make_gate_decision(_resolve_t080_receipt(root=root), refusals=refusals)
        return {"status": "refused", **asdict(decision)}
    except Exception as exc:  # noqa: BLE001 (fail-closed: active 解決不能)
        refusals = [f"freeze-ratify: {type(exc).__name__}: {exc}"]
        manifest_refusal = _manifest_structural_refusal(Path(manifest_path))
        if manifest_refusal is not None:
            refusals.append(manifest_refusal)
        decision = _make_gate_decision(_resolve_t080_receipt(root=root), refusals=refusals)
        return {"status": "refused", **asdict(decision)}
    try:
        validated = s8b_ratified_freeze.launch_validate(ratified, root)
    except s8b_ratified_freeze.RatifiedFreezeError as exc:
        decision = _make_gate_decision(
            _resolve_t080_receipt(root=root),
            refusals=[f"v2-execution: launch-validate: [{exc.reason}] {exc}"],
        )
        return {"status": "refused", **asdict(decision)}
    except Exception as exc:  # noqa: BLE001 (fail-closed: 走査不能)
        decision = _make_gate_decision(
            _resolve_t080_receipt(root=root),
            refusals=[f"v2-execution: launch-validate: {type(exc).__name__}: {exc}"],
        )
        return {"status": "refused", **asdict(decision)}

    t080_resolution = _resolve_t080_receipt(root=root, launch_validated=validated)

    # CLI で指定された freeze bytes 自体も active generation と一致させる。ただし
    # document は parse せず、consumer は validated.ratified.document のみを使う。
    try:
        requested_freeze_sha = hashlib.sha256(freeze_path.read_bytes()).hexdigest()
    except OSError as exc:
        decision = _make_gate_decision(
            t080_resolution,
            refusals=[f"holdout-freeze-verify: {type(exc).__name__}: {exc}"],
        )
        return {"status": "refused", **asdict(decision)}
    if requested_freeze_sha != validated.ratified.sha256:
        decision = _make_gate_decision(
            t080_resolution,
            refusals=[
                "freeze-not-active-generation: 与えられた freeze bytes sha256 が"
                "承認束縛済み active 世代と不一致"
            ],
        )
        return {"status": "refused", **asdict(decision)}

    # deep-frozen ratified document から legacy consumer 用 container view を一度だけ
    # 作る。disk 再読・JSON 再 parse は行わず、この view を全 legacy consumer で共有する。
    freeze_document = _mutable_json_tree(validated.ratified.document)

    # C2-9 / A3-6: manifest を厳密 1 回だけ verify し、gate と本体で同一
    # VerifiedManifest object を共有する (再読込・再検証しない)。verify 失敗時は
    # verified_manifest=None で gate へ渡し、gate が同一 refusal を集約する。
    verified_manifest: Optional[VerifiedManifest] = None
    approved_spec = None
    manifest_verification_error: Optional[BaseException] = None
    try:
        approved_spec = s8b_oracle_spec.load_approved_spec(root)
        verified_manifest = verify_manifest(
            Path(manifest_path), root=root,
            freeze_document=freeze_document,
            freeze_sha256=validated.ratified.sha256,
            approved_spec=approved_spec,
        )
    except Exception as exc:
        manifest_verification_error = exc
        verified_manifest = None

    decision = _gate_check_validated(
        freeze_path=freeze_path, manifest_path=manifest_path, root=root,
        t080_resolution=t080_resolution,
        launch_validated=validated, approved_spec=approved_spec,
        manifest_verification_error=manifest_verification_error,
        verified_manifest=verified_manifest,
    )
    if not decision.allowed:
        return {"status": "refused", **asdict(decision)}
    if verified_manifest is None:
        # gate は通ったが manifest を検証できていない (TOCTOU 等) → fail-closed。
        decision = _make_gate_decision(
            t080_resolution,
            refusals=["manifest-verify: 検証済み manifest object がない"],
        )
        return {"status": "refused", **asdict(decision)}
    try:
        t080_campaign_value = _campaign_t080_value(t080_resolution)
    except OracleDriverError as exc:
        decision = _make_gate_decision(
            t080_resolution, refusals=[f"migration-receipt-verify: {exc}"],
        )
        return {"status": "refused", **asdict(decision)}

    budget_path = Path(budget_path)
    # マーカーは --output-root 非依存 (freeze 正本側)。既定は freeze ファイルと同じ
    # ディレクトリ = production では output/s8b-freeze/ 配下。
    marker_root = Path(marker_root) if marker_root is not None else freeze_path.parent
    manifest = verified_manifest.document
    freeze = freeze_document
    block = config_for_block(manifest, block_id)
    limits = s8b_budget.load_oracle_limits(freeze)
    manifest_sha = verified_manifest.sha256
    freeze_sha = validated.ratified.sha256
    schedule_sha = manifest["schedule_sha256"]
    campaign_id = block["campaign_id"]
    run_contract = block["run_contract"]
    env_tag = run_contract["env_tag"]
    if prepare_fn is None:
        prepare_fn = prepare_cell
    _, cxx = buildcache.compilers_for_current_site()
    # Human-reviewed admission の persistent receipt に generator id は入らない。run context
    # の閉じた registry member には S8b の直前 producer である S8a を用いる。
    build_context = build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)
    raw_output_root = "" if output_root is None else os.fspath(output_root)
    try:
        layout = campaign_layout(campaign_id, output_root=raw_output_root)
    except ValueError as exc:
        decision = _make_gate_decision(
            t080_resolution, refusals=[f"official-output-root: {exc}"],
        )
        return {"status": "refused", **asdict(decision)}
    # campaign_layout has already applied the central resolver.  Reuse that
    # canonical base for every later cache and durable-root consumer.
    output_root = Path(layout.root).parent.parent

    # v2 実走前の一括検査 (run marker 作成前・第一防壁): launch_validate +
    # env 契約導出 + 共有 execution guard/receipt + binary store 消費。いずれの
    # 不整合も refusal に翻訳し、run marker・WAL・budget を一切書かずに倒す。
    try:
        plan = _prepare_v2_execution(
            validated=validated, run_contract=run_contract,
            schedule=block["schedule"], out_root=output_root, repo_root=root,
        )
    except OracleDriverError as exc:
        decision = _make_gate_decision(
            t080_resolution, refusals=[f"v2-execution: {exc}"],
        )
        return {"status": "refused", **asdict(decision)}
    except Exception as exc:  # 想定外も refusal 契約で倒す (兄弟の ratified 解決経路と対称)
        decision = _make_gate_decision(
            t080_resolution,
            refusals=[f"v2-execution-unexpected: {type(exc).__name__}: {exc}"],
        )
        return {"status": "refused", **asdict(decision)}

    # Measurement authority is resolved exactly once after the side-effect-free plan
    # gate and before the durable claim/marker/WAL/budget chain begins.
    try:
        perf_preflight_receipt = _perf_preflight.probe_perf_availability()
        use_perf = _perf_preflight.use_perf_from_receipt(perf_preflight_receipt)
        perf_observation = (
            None if use_perf else _perf_preflight.build_perf_observation(
                perf_preflight_receipt,
                run_cmd=["ccbench"],
                leading_indicators={"ipc": None, "llc_miss_rate": None},
            )
        )
    except _perf_preflight.PerfPreflightError as exc:
        decision = _make_gate_decision(
            t080_resolution, refusals=[f"perf-preflight: {exc}"],
        )
        return {"status": "refused", **asdict(decision)}

    refusal: Optional[str]
    try:
        execution_identity = _execution_identity(plan)
        claim_root = output_root / "claims"
        if _reservation.is_reservation_required(plan.contract.isolation_policy):
            if claim_root.is_symlink() or not claim_root.is_dir():
                raise OracleDriverError(
                    f"G12 campaign claim root が durable out_root 下に事前 provisioning "
                    f"済みでない: {claim_root}"
                )
            write_capability_for_directory(
                claim_root, policy=durable_root_policy,
            )
        _acquire_g12_claim(
            plan=plan, claim_root=claim_root,
            manifest_sha256=manifest_sha, freeze_sha256=freeze_sha,
            schedule_sha256=schedule_sha, campaign_id=campaign_id,
            identity=execution_identity,
        )
    except (OracleDriverError, _campaign_claim.ClaimError, DurableRootError) as exc:
        # claim 競合は既存 claim 以外を作らず、WAL/marker/budget より前に拒否する。
        refusal = f"v2-execution: {exc}"
    else:
        try:
            oracle_admissions = _holdout_admission.reserve_oracle_holdout_observations(
                repo_root=root,
                verified_manifest=verified_manifest,
                launch_validated=validated,
                block_id=block_id,
            )
        except _holdout_admission.HoldoutAdmissionError as exc:
            refusal = f"holdout-observation-admission: {exc}"
        else:
            refusal = None

    if refusal is not None:
        decision = _make_gate_decision(t080_resolution, refusals=[refusal])
        return {"status": "refused", **asdict(decision)}

    campaign_start_resolution = _resolve_t080_receipt(
        root=root, launch_validated=validated,
    )
    if _t080_epoch_identity(campaign_start_resolution) != _t080_epoch_identity(t080_resolution):
        refusal = "migration-receipt-verify: receipt epoch が campaign-start 前に変化した"
    if refusal is not None:
        decision = _make_gate_decision(
            t080_resolution,
            refusals=[refusal],
        )
        return {"status": "refused", **asdict(decision)}

    _ensure_campaign(
        layout, manifest_sha256=manifest_sha, block_id=block_id,
        campaign_id=campaign_id, freeze_sha256=freeze_sha, marker_root=marker_root,
    )
    campaign_start_payload = {
        "manifest_sha256": manifest_sha,
        "block_id": block_id,
        "campaign_id": campaign_id,
        "t080_freeze_migration_observation": t080_campaign_value,
        # C3-10: 共有 execution guard/receipt を run 記録に残す (report が manifest の
        # env_tag/contract_sha256 と照合する)。
        "execution_receipt": plan.receipt,
    }
    perf_evaluate_kwargs = {}
    if not use_perf:
        measurement_manifest_path = Path(layout.root) / "measurement-manifest.json"
        _oracle_artifacts.write_measurement_manifest(
            measurement_manifest_path,
            oracle_manifest_sha256=manifest_sha,
            campaign_id=campaign_id,
            block_id=block_id,
            perf_observation=perf_observation,
            run_cmd=["ccbench"],
            leading_indicators={"ipc": None, "llc_miss_rate": None},
        )
        campaign_start_payload["measurement_manifest"] = {
            "path": measurement_manifest_path.name,
            "sha256": _oracle_artifacts.measurement_manifest_sha256(
                measurement_manifest_path
            ),
        }
        perf_evaluate_kwargs = {
            "use_perf": False,
            "perf_preflight_receipt": perf_preflight_receipt,
        }
    _append_session(layout, env_tag, "campaign-start", campaign_start_payload)
    ledger_identity = {
        "manifest_sha256": manifest_sha,
        "freeze_sha256": freeze_sha,
        "schedule_sha256": schedule_sha,
    }
    s8b_budget.create_ledger(budget_path, limits=limits, **ledger_identity)

    schedule = block["schedule"]
    per_row_bench_s = float(
        run_contract["extime"] * run_contract["reps"]
        * run_contract["bench_max_rounds"]
    )
    reserved_bench_s = per_row_bench_s * len(schedule)
    by_holdout_reserved: dict[str, float] = {}
    for row in schedule:
        by_holdout_reserved[row["holdout_id"]] = (
            by_holdout_reserved.get(row["holdout_id"], 0.0) + per_row_bench_s
        )
    reserved_iso = _iso_now()

    # 事前一括 reservation。確保できなければ一行も走らせず terminal を耐久化する
    # (§5.2 の予算不足 = 未実施 arm を対称に判定不能へ倒す契約)。
    try:
        s8b_budget.reserve(
            budget_path, reserved_bench_s=reserved_bench_s,
            by_holdout_reserved=by_holdout_reserved, reserved_iso=reserved_iso,
            **ledger_identity,
        )
    except s8b_budget.BudgetError as exc:
        s8b_budget.mark_exhausted(
            budget_path, requested_bench_s=reserved_bench_s,
            by_holdout_requested=by_holdout_reserved, reserved_iso=reserved_iso,
            **ledger_identity,
        )
        _append_session(layout, env_tag, "budget-exhausted-before-attempt", {
            "reason": str(exc),
            "reserved_bench_s": reserved_bench_s,
        })
        _append_campaign_terminal(
            layout, env_tag, status="aborted", scheduled_rows=len(schedule),
            completed_rows=0, execution_identity=execution_identity,
        )
        return {
            "status": "budget_exhausted_before_attempt",
            "allowed": True,
            "refusals": [],
            "t080_freeze_migration_observation": t080_campaign_value,
            "campaign_id": campaign_id,
            "manifest_sha256": manifest_sha,
            "freeze_sha256": freeze_sha,
            "schedule_sha256": schedule_sha,
            "completed_trials": 0,
            "events": _session_events(layout),
        }

    completed = 0
    # 強い completed 定義の未達行 (binding-refused / prepare 恒久失敗 / 未実行) を集める。
    # 1 件でも残れば terminal は protocol_violation に倒す (fail-closed)。
    unresolved_rows: list[int] = []
    error_stopped = False
    error_message: Optional[str] = None
    for position, row in enumerate(schedule):
        try:
            _recheck_required_execution(plan, remaining_rows=len(schedule) - position)
        except OracleDriverError as exc:
            _append_session(layout, env_tag, "deviation", {
                "message": str(exc), "kind": "execution-guard-lost",
                "schedule_index": row["schedule_index"],
            })
            error_stopped = True
            error_message = str(exc)
            break
        schedule_index = row["schedule_index"]
        holdout_id = row["holdout_id"]
        configuration_id = row["configuration_id"]
        row_done = False
        for attempt in (1, 2):
            started_iso = _iso_now()
            attempt_started = time.monotonic()
            _append_session(layout, env_tag, "trial-start", {
                "schedule_index": schedule_index,
                "holdout_id": holdout_id,
                "configuration_id": configuration_id,
                "attempt": attempt,
            })
            evaluate_started = False
            row_condition_gate = None
            try:
                with _prepared_binding(
                        freeze=freeze, holdout_id=holdout_id,
                        configuration_id=configuration_id,
                        ccbench_pin=run_contract["ccbench_pin"],
                        cxx=cxx, prepare_fn=prepare_fn) as (actual_binding, prepared):
                    expected_entry = binding_entry(
                        freeze, holdout_id, configuration_id,
                    )
                    expected_request_digests = _condition_request_digests_for_flags(
                        expected_entry["flags"],
                        driver_id=_condition_driver_id(configuration_id),
                    )
                    condition_admission = require_returned_condition_evidence(
                        prepared, expected_request_digests=expected_request_digests,
                        use_class="oracle", label="oracle prepare_fn return",
                    )
                    prepared_records = (
                        prepared.condition_supply_records,
                        prepared.condition_meaning_records,
                    )
                    row_condition_gate = condition_gate_receipt(
                        prepared_records[0], prepared_records[1],
                        condition_admission,
                    )
                    expected_binding = _expected_binding(
                        manifest, holdout_id, configuration_id,
                    )
                    if _canonical_bytes(actual_binding) != _canonical_bytes(expected_binding):
                        _append_session(layout, env_tag, "binding-refused", {
                            "schedule_index": schedule_index,
                            "reason": "manifest binding_identity と再実体化 identity が不一致",
                        })
                        unresolved_rows.append(schedule_index)
                        row_done = True
                        break

                    try:
                        observation_admission = (
                            _holdout_admission.consume_oracle_attempt_ticket(
                                oracle_admissions[schedule_index],
                                schedule_index=schedule_index,
                            )
                        )
                    except (KeyError, _holdout_admission.HoldoutAdmissionError) as exc:
                        _append_session(layout, env_tag, "deviation", {
                            "message": (
                                "oracle holdout observation admission failed: "
                                f"{type(exc).__name__}: {exc}"
                            ),
                            "kind": "holdout-observation-admission",
                            "schedule_index": schedule_index,
                        })
                        error_stopped = True
                        error_message = str(exc)
                        row_done = True
                        break

                    prepared_for_eval = PreparedCell(
                        genome=prepared.genome,
                        src_token=prepared.src_token,
                        ccbench_dir=prepared.ccbench_dir,
                        cache_root=str(output_root / "s8b-build-cache"),
                        condition_supply_records=prepared.condition_supply_records,
                        condition_meaning_records=prepared.condition_meaning_records,
                        sort_oracle_contract_id=prepared.sort_oracle_contract_id,
                    )
                    perf = _perf_for_holdout(freeze, holdout_id, run_contract)
                    before = len(wal.read_records(layout))
                    evaluate_started = True
                    try:
                        with _assert_v2_build_contract_for_snapshot(
                                plan.contract,
                                entry=binding_entry(
                                    freeze, holdout_id, configuration_id,
                                ),
                                configuration_id=configuration_id,
                                ccbench_pin=run_contract["ccbench_pin"],
                                cxx=cxx,
                                prepared=prepared_for_eval):
                            evaluate_kwargs = dict(
                                numactl=list(plan.contract.numactl),
                                correctness=None,
                                extra_correctness=[(
                                    pipeline.S2_TAG, pipeline.s2_correctness_workload(),
                                )],
                                do_bench=True,
                                do_settle=True,
                                src_token=prepared_for_eval.src_token,
                                log=lambda _message: None,
                                ccbench_dir=prepared_for_eval.ccbench_dir,
                                cache_root=prepared_for_eval.cache_root,
                                screening=None,
                                build_context=build_context,
                                capability_resolver=(
                                    lambda source, input_sha256=(
                                        actual_binding["entry_sha256"]
                                    ): reviewed_source_capability(
                                        review_id=ReviewId.S8B_ORACLE,
                                        source=source,
                                        input_sha256=input_sha256,
                                    )
                                ),
                                bench_max_rounds=run_contract["bench_max_rounds"],
                                env_contract=plan.contract,
                                record_rep_returncodes=True,
                                holdout_observation_admission=(
                                    observation_admission
                                ),
                            )
                            if prepared_for_eval.sort_oracle_contract_id is not None:
                                evaluate_kwargs["sort_oracle_contract_id"] = (
                                    prepared_for_eval.sort_oracle_contract_id
                                )
                            if evaluate_fn is None:
                                result = pipeline.evaluate(
                                    prepared_for_eval.genome, layout, env_tag,
                                    run_contract["ccbench_pin"], perf,
                                    # C3-9: clocks/numactl は env 契約 lookup 結果を使う
                                    # (NUMACTL ハードコード撤去)。
                                    plan.contract.clocks_per_us,
                                    authorization_contract=(
                                        plan.authorization_contract
                                    ),
                                    **evaluate_kwargs,
                                    **perf_evaluate_kwargs,
                                )
                            else:
                                result = evaluate_fn(
                                    prepared_for_eval.genome, layout, env_tag,
                                    run_contract["ccbench_pin"], perf,
                                    # C3-9: clocks/numactl は env 契約 lookup 結果を使う
                                    # (NUMACTL ハードコード撤去)。
                                    plan.contract.clocks_per_us,
                                    authorization_contract=(
                                        plan.authorization_contract
                                    ),
                                    **evaluate_kwargs,
                                    **perf_evaluate_kwargs,
                                )
                            if evaluate_fn is not None:
                                require_returned_condition_evidence(
                                    result,
                                    expected_request_digests=expected_request_digests,
                                    use_class="oracle",
                                    label="oracle evaluate_fn return",
                                    expected_records=prepared_records,
                                )
                    except (wal.WalAppendError, wal.WalFramingError):
                        # 不確かな同一 WAL へ trial-result/deviation を重ねない。
                        raise
                    except S1DriverError as exc:
                        raise OracleDriverError(
                            f"oracle condition evidence rejected: {exc}"
                        ) from exc
                    except Exception as exc:
                        result = pipeline.EvalResult(
                            genome=prepared_for_eval.genome,
                            variant=pipeline.variant_id(
                                prepared_for_eval.genome, prepared_for_eval.src_token),
                            certified=False, aborted=True,
                            notes=[f"evaluate exception: {type(exc).__name__}: {exc}"],
                        )
                    new_records = wal.read_records(layout)[before:]
                    abort_payload, bench_s = _trial_measurements(new_records)
                    try:
                        outcome = _outcome_for(result, abort_payload)
                    except _UnknownAbortReason as exc:
                        _append_session(layout, env_tag, "deviation", {
                            "message": str(exc),
                            "kind": "unknown-abort-reason",
                            "schedule_index": schedule_index,
                            "abort_reason": exc.reason,
                        })
                        error_stopped = True
                        error_message = str(exc)
                        row_done = True
                        break
            except (wal.WalAppendError, wal.WalFramingError):
                # materializer 境界でも元の構造化 WAL 例外を保全する。
                raise
            except Exception as exc:
                if evaluate_started:
                    _append_session(layout, env_tag, "deviation", {
                        "message": f"evaluate 後の materializer cleanup 失敗: {type(exc).__name__}: {exc}",
                    })
                    raise
                if attempt == 1 and _is_transient_prepare_failure(exc):
                    _append_session(layout, env_tag, "retry", {
                        "schedule_index": schedule_index,
                        "attempt": 2,
                        "reason": f"prepare {type(exc).__name__}: {exc}",
                    })
                    continue
                _append_session(layout, env_tag, "binding-refused", {
                    "schedule_index": schedule_index,
                    "reason": f"prepare {type(exc).__name__}: {exc}",
                })
                unresolved_rows.append(schedule_index)
                row_done = True
                break

            if error_stopped or row_done:
                break
            finished_iso = _iso_now()
            wall_s = float(max(0.0, time.monotonic() - attempt_started))
            _append_session(layout, env_tag, "trial-result", {
                "schedule_index": schedule_index,
                "holdout_id": holdout_id,
                "configuration_id": configuration_id,
                "attempt": attempt,
                "outcome": outcome,
                "excluded_reason": None,
                "screen_outcome": "not_enabled",
                **({"condition_gate": row_condition_gate}
                   if row_condition_gate is not None else {}),
            })
            completed += 1
            budget_entry = {
                "campaign_id": campaign_id,
                "block_id": block_id,
                "schedule_index": schedule_index,
                "holdout_id": holdout_id,
                "configuration_id": configuration_id,
                "attempt": attempt,
                "outcome": outcome,
                "bench_s": bench_s,
                "wall_s": wall_s,
                "started_iso": started_iso,
                "finished_iso": finished_iso,
            }
            # reservation 済み枠内の実測計上。枠超過は protocol violation として fail-closed。
            try:
                s8b_budget.append_entry(
                    budget_path, entry=budget_entry, **ledger_identity,
                )
            except s8b_budget.BudgetError as exc:
                _append_session(layout, env_tag, "deviation", {
                    "message": f"実測 bench が予約枠を超過し台帳に拒否された: {exc}",
                    "kind": "reservation-envelope-exceeded",
                    "schedule_index": schedule_index,
                    "bench_s": bench_s,
                    "reserved_bench_s": reserved_bench_s,
                })
                error_stopped = True
                error_message = str(exc)
                row_done = True
                break
            row_done = True
            break
        if error_stopped:
            break
        if not row_done:
            raise OracleDriverError(f"schedule_index={schedule_index} が終端に到達しない")

    if error_stopped:
        # 内部逸脱 (未分類 abort / reservation 枠超過)。精算せず予約枠を非解放の
        # まま残す (fail-closed)。terminal status は internal-error。
        status = "error"
    elif completed == len(schedule) and not unresolved_rows:
        # 強い completed 定義: 全予定行が一意 terminal outcome + budget entry を
        # 耐久化した。held reservation を実測へ確定し未使用枠を解放する。
        s8b_budget.settle(
            budget_path, settled_iso=_iso_now(), **ledger_identity,
        )
        status = "completed"
    else:
        # 1 行以上が binding-refused / prepare 恒久失敗で terminal outcome を
        # 得ていない。強い completed 定義を満たさず protocol_violation に倒す。
        # 精算せず予約枠を held のまま残す (fail-closed)。
        _append_session(layout, env_tag, "protocol-violation", {
            "unresolved_rows": unresolved_rows,
            "completed_trials": completed,
            "scheduled_rows": len(schedule),
        })
        status = "protocol_violation"

    _append_campaign_terminal(
        layout, env_tag,
        status="completed" if status == "completed" else "aborted",
        scheduled_rows=len(schedule), completed_rows=completed,
        execution_identity=execution_identity,
    )

    return {
        "status": status,
        "allowed": True,
        "refusals": [],
        "t080_freeze_migration_observation": t080_campaign_value,
        "campaign_id": campaign_id,
        "manifest_sha256": manifest_sha,
        "freeze_sha256": freeze_sha,
        "schedule_sha256": schedule_sha,
        "completed_trials": completed,
        **({"error": error_message} if error_message is not None else {}),
        **({"unresolved_rows": unresolved_rows}
           if status == "protocol_violation" else {}),
        "events": _session_events(layout),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="8b oracle 実行 gate / block driver")
    subparsers = parser.add_subparsers(dest="command", required=True)
    gate = subparsers.add_parser("gate-check")
    gate.add_argument("--freeze", type=Path, required=True)
    gate.add_argument("--manifest", type=Path)
    gate.add_argument("--root", type=Path, default=ROOT)

    run = subparsers.add_parser("run-block")
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--block-id", required=True)
    run.add_argument("--freeze", type=Path, default=DEFAULT_FREEZE_PATH)
    run.add_argument("--root", type=Path, default=ROOT)
    run.add_argument("--output-root", type=Path, default=None)
    # 実走済みマーカーの置き場は CLI から上書きできない (freeze ファイルと同じ
    # ディレクトリ = production では output/s8b-freeze/ 配下に固定)。R6: --output-root を
    # 変えても同じ場所を指すため resume 拒否を出力先付け替えで迂回できない。--budget と
    # 同じ判断 (別 path 指定 = fail-open) で CLI 面から撤去。run_block の引数はテスト専用
    # --budget override は廃止。台帳 path は canonical 固定 (別 path 指定による
    # 総枠複製 = fail-open を塞ぐ。T 層項 6)。
    return parser


# terminal status → CLI 終了コードの固定表。rc 優先順位:
# internal-error(1) > protocol_violation(3) > budget-refused(2) > completed(0)。
# gate-refused も rc 2。ここに無い status は fail-closed で internal-error(1)。
_EXIT_CODE_BY_STATUS = {
    "completed": 0,
    "error": 1,  # 内部逸脱 = internal-error
    "protocol_violation": 3,
    "budget_exhausted_before_attempt": 2,  # budget-refused
    "refused": 2,  # gate-refused
}


def _exit_code(status: object) -> int:
    """run_block / gate の terminal status を CLI 終了コードへ射影する。

    rc 優先順位 = internal-error(1) > protocol_violation(3) > budget-refused(2)
    > completed(0)。gate-refused も rc 2。未知・欠測 status は fail-closed で
    internal-error(1) に倒す。
    """
    return _EXIT_CODE_BY_STATUS.get(status, 1)


def _cli_durable_root_policy(
        output_root: Optional[Path],
) -> Optional[DurableRootPolicy]:
    """Build the narrow official policy without performing the root gate early.

    The central resolver remains the source of truth for admission and refusal
    ordering.  This helper only canonicalizes the candidate so the CLI can
    inject a policy into ``run_block``; invalid candidates are still rejected
    at the existing campaign-layout choke point.
    """
    raw = (
        os.fspath(output_root)
        if output_root is not None
        else os.environ.get(_OFFICIAL_OUTPUT_ROOT_ENV)
    )
    if not raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = candidate.absolute()
    try:
        resolved = candidate.resolve(strict=False)
    except OSError:
        return None
    return DurableRootPolicy(approved_roots=(resolved,), forbidden_roots=())


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "gate-check":
            decision = gate_check(
                freeze_path=args.freeze, manifest_path=args.manifest, root=args.root,
            )
            print(json.dumps(asdict(decision), ensure_ascii=False, sort_keys=True))
            return 0 if decision.allowed else _exit_code("refused")
        result = run_block(
            manifest_path=args.manifest, block_id=args.block_id,
            freeze_path=args.freeze, root=args.root,
            output_root=args.output_root, budget_path=DEFAULT_BUDGET_PATH,
            durable_root_policy=_cli_durable_root_policy(args.output_root),
        )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return _exit_code(result.get("status"))
    except Exception as exc:
        print(json.dumps({
            "status": "error", "error": f"{type(exc).__name__}: {exc}",
        }, ensure_ascii=False, sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())
