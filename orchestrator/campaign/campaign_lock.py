# -*- coding: utf-8 -*-
"""``campaign.lock`` v1/v2 の低層 codec。

この module は import graph の最下層に置く。campaign の model、identity、WAL には
依存せず、wire format の検証と inner identity の取り出しだけを担う。
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import re
from typing import Any, Mapping


CAMPAIGN_LOCK_V2_SCHEMA = "campaign-lock/v2"
NON_CERTIFYING_CAMPAIGN_LOCK_SCHEMA = "campaign-lock/non-certifying/v1"
IDENTITY_KEYS = frozenset({
    "spec_content", "ccbench_commit", "search_tag", "search_config", "trial",
})
AUTHORITY_KEYS = frozenset({
    "environment_contract_sha256",
    "activation_serial",
    "activation_state_sha256",
    "contract_loader_commit",
    "contract_loader_blob_sha256s",
})
V2_KEYS = frozenset({"schema_version", "identity_preimage", "authority"})
NON_CERTIFYING_KEYS = frozenset({
    "schema_version", "identity_preimage", "a1_non_certifying",
})
NON_CERTIFYING_RESERVED_V1_KEYS = frozenset({"a1_non_certifying"})
NON_CERTIFYING_ENVELOPE_KEYS = frozenset({
    "common_record", "workload_binding", "identity_tag",
})
NON_CERTIFYING_COMMON_KEYS = frozenset({
    "mode", "certifying", "study_id", "policy_sha256",
    "preregistration_sha256", "source_commit", "source_binding_sha256",
    "environment_contract_sha256", "intent_sha256", "campaign_ids",
})
NON_CERTIFYING_WORKLOAD_KEYS = frozenset({
    "workload", "campaign_id", "ordinal",
})
_DISCLOSED_IDENTITY_KEY_DOMAIN = b"izanagi-a1-disclosed-identity-key/v1\0"
_LOCK_IDENTITY_TAG_DOMAIN = b"izanagi-a1-lock-identity-tag/v1\0"
# ``contract_loader_*`` は歴史的名称であり、この値は exact 63 path の
# enforcement source closure である。
CONTRACT_LOADER_RELATIVE_PATHS = (
    "orchestrator/campaign/env_contract.py",
    "orchestrator/campaign/env_contract_activation.py",
    "orchestrator/campaign/execution_guard.py",
    "orchestrator/campaign/loop.py",
    "orchestrator/campaign/pipeline.py",
    "orchestrator/campaign/wal.py",
    "orchestrator/campaign/ident.py",
    "orchestrator/campaign/artifact_admission.py",
    "orchestrator/verifier/core.py",
    "orchestrator/verifier/dsg.py",
    "orchestrator/verifier/model.py",
    "orchestrator/verifier/parse.py",
    "orchestrator/verifier/__init__.py",
    "orchestrator/verifier/report.py",
    "orchestrator/campaign/s8c_preregistration.py",
    "orchestrator/campaign/s8c_preregistration_evidence.py",
    "orchestrator/campaign/s8c_generation_projection.py",
    "orchestrator/campaign/campaign_lock.py",
    "orchestrator/campaign/contract_loader_binding.py",
    "orchestrator/campaign/guided.py",
    "orchestrator/campaign/replay.py",
    "orchestrator/qualification/artifacts.py",
    "orchestrator/qualification/t126_driver.py",
    "orchestrator/verifier/commit_receipt.py",
    "orchestrator/calibrator/__init__.py",
    "orchestrator/calibrator/effective_clock_policy.py",
    "orchestrator/calibrator/perf_preflight.py",
    "orchestrator/calibrator/runner.py",
    "orchestrator/calibrator/schema_v2.py",
    "orchestrator/calibrator/stability.py",
    "orchestrator/campaign/__init__.py",
    "orchestrator/campaign/axis_trigger_gating.py",
    "orchestrator/campaign/build_admission.py",
    "orchestrator/campaign/buildcache.py",
    "orchestrator/campaign/calibration_verify.py",
    "orchestrator/campaign/campaign_claim.py",
    "orchestrator/campaign/diff_quarantine.py",
    "orchestrator/campaign/env_attestation.py",
    "orchestrator/campaign/genome.py",
    "orchestrator/campaign/layout.py",
    "orchestrator/campaign/lock.py",
    "orchestrator/campaign/model.py",
    "orchestrator/campaign/p2_2.py",
    "orchestrator/campaign/p3_b4_launcher.py",
    "orchestrator/campaign/p3_b4_protocol.py",
    "orchestrator/campaign/reflux_ir.py",
    "orchestrator/campaign/reservation.py",
    "orchestrator/campaign/search_baselines.py",
    "orchestrator/campaign/site_policy.py",
    "orchestrator/campaign/source_digest.py",
    "orchestrator/campaign/trigger_gate_binding.py",
    "orchestrator/critic/__init__.py",
    "orchestrator/critic/online_digest.py",
    "orchestrator/holdout_observation.py",
    "orchestrator/qualification/__init__.py",
    "orchestrator/qualification/attempt_ledger.py",
    "orchestrator/qualification/collector.py",
    "orchestrator/qualification/contract.py",
    "orchestrator/qualification/identity.py",
    "orchestrator/qualification/qsub_binding.py",
    "orchestrator/qualification/retry_index.py",
    "orchestrator/qualification/series.py",
    "orchestrator/campaign/verify_fanout_worker.py",
)

# T-733 より前に実在した v2 lock の歴史閲覧 grammar。現行 closure の
# prefix から導出すると将来の追加・並べ替えで過去の epoch が変わるため、独立した
# ordered literal として固定する。
PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS = (
    "orchestrator/campaign/env_contract.py",
    "orchestrator/campaign/env_contract_activation.py",
    "orchestrator/campaign/execution_guard.py",
    "orchestrator/campaign/loop.py",
    "orchestrator/campaign/pipeline.py",
    "orchestrator/campaign/wal.py",
    "orchestrator/campaign/ident.py",
    "orchestrator/campaign/artifact_admission.py",
    "orchestrator/verifier/core.py",
    "orchestrator/verifier/dsg.py",
    "orchestrator/verifier/model.py",
    "orchestrator/verifier/parse.py",
    "orchestrator/verifier/__init__.py",
    "orchestrator/verifier/report.py",
    "orchestrator/campaign/s8c_preregistration.py",
    "orchestrator/campaign/s8c_preregistration_evidence.py",
    "orchestrator/campaign/s8c_generation_projection.py",
    "orchestrator/campaign/campaign_lock.py",
    "orchestrator/campaign/contract_loader_binding.py",
    "orchestrator/campaign/guided.py",
    "orchestrator/campaign/replay.py",
    "orchestrator/qualification/artifacts.py",
    "orchestrator/qualification/t126_driver.py",
    "orchestrator/verifier/commit_receipt.py",
)

# T-733 exact-62 の記録 grammar。2a9ba783f^ の宣言順を独立に固定する。
T733_EXACT62_CONTRACT_LOADER_RELATIVE_PATHS = (
    "orchestrator/campaign/env_contract.py",
    "orchestrator/campaign/env_contract_activation.py",
    "orchestrator/campaign/execution_guard.py",
    "orchestrator/campaign/loop.py",
    "orchestrator/campaign/pipeline.py",
    "orchestrator/campaign/wal.py",
    "orchestrator/campaign/ident.py",
    "orchestrator/campaign/artifact_admission.py",
    "orchestrator/verifier/core.py",
    "orchestrator/verifier/dsg.py",
    "orchestrator/verifier/model.py",
    "orchestrator/verifier/parse.py",
    "orchestrator/verifier/__init__.py",
    "orchestrator/verifier/report.py",
    "orchestrator/campaign/s8c_preregistration.py",
    "orchestrator/campaign/s8c_preregistration_evidence.py",
    "orchestrator/campaign/s8c_generation_projection.py",
    "orchestrator/campaign/campaign_lock.py",
    "orchestrator/campaign/contract_loader_binding.py",
    "orchestrator/campaign/guided.py",
    "orchestrator/campaign/replay.py",
    "orchestrator/qualification/artifacts.py",
    "orchestrator/qualification/t126_driver.py",
    "orchestrator/verifier/commit_receipt.py",
    "orchestrator/calibrator/__init__.py",
    "orchestrator/calibrator/effective_clock_policy.py",
    "orchestrator/calibrator/perf_preflight.py",
    "orchestrator/calibrator/runner.py",
    "orchestrator/calibrator/schema_v2.py",
    "orchestrator/calibrator/stability.py",
    "orchestrator/campaign/__init__.py",
    "orchestrator/campaign/axis_trigger_gating.py",
    "orchestrator/campaign/build_admission.py",
    "orchestrator/campaign/buildcache.py",
    "orchestrator/campaign/calibration_verify.py",
    "orchestrator/campaign/campaign_claim.py",
    "orchestrator/campaign/diff_quarantine.py",
    "orchestrator/campaign/env_attestation.py",
    "orchestrator/campaign/genome.py",
    "orchestrator/campaign/layout.py",
    "orchestrator/campaign/lock.py",
    "orchestrator/campaign/model.py",
    "orchestrator/campaign/p2_2.py",
    "orchestrator/campaign/p3_b4_launcher.py",
    "orchestrator/campaign/p3_b4_protocol.py",
    "orchestrator/campaign/reflux_ir.py",
    "orchestrator/campaign/reservation.py",
    "orchestrator/campaign/search_baselines.py",
    "orchestrator/campaign/site_policy.py",
    "orchestrator/campaign/source_digest.py",
    "orchestrator/campaign/trigger_gate_binding.py",
    "orchestrator/critic/__init__.py",
    "orchestrator/critic/online_digest.py",
    "orchestrator/holdout_observation.py",
    "orchestrator/qualification/__init__.py",
    "orchestrator/qualification/attempt_ledger.py",
    "orchestrator/qualification/collector.py",
    "orchestrator/qualification/contract.py",
    "orchestrator/qualification/identity.py",
    "orchestrator/qualification/qsub_binding.py",
    "orchestrator/qualification/retry_index.py",
    "orchestrator/qualification/series.py",
)

_HEX40_RE = re.compile(r"[0-9a-f]{40}\Z")
_HEX64_RE = re.compile(r"[0-9a-f]{64}\Z")


class CampaignLockCodecError(ValueError):
    """campaign lock が既知の exact wire contract を満たさない。"""


@dataclass(frozen=True)
class CampaignLockAuthority:
    """検証済み v2 authority。"""

    environment_contract_sha256: str
    activation_serial: int
    activation_state_sha256: str
    contract_loader_commit: str
    contract_loader_blob_sha256s: dict[str, str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "environment_contract_sha256": self.environment_contract_sha256,
            "activation_serial": self.activation_serial,
            "activation_state_sha256": self.activation_state_sha256,
            "contract_loader_commit": self.contract_loader_commit,
            "contract_loader_blob_sha256s": dict(
                self.contract_loader_blob_sha256s
            ),
        }


@dataclass(frozen=True)
class DecodedCampaignLock:
    """検証済み lock と、そのまま再利用できる元の文字列。"""

    schema_version: str
    identity_preimage: str
    identity: dict[str, Any]
    authority: CampaignLockAuthority | None
    original_text: str

    @property
    def is_v1(self) -> bool:
        return self.schema_version == "campaign-lock/v1"

    @property
    def is_v2(self) -> bool:
        return self.schema_version == CAMPAIGN_LOCK_V2_SCHEMA

    def preserved_v1_text(self) -> str:
        """v1 の元文字列を再書式化せず返す。"""
        if not self.is_v1:
            raise CampaignLockCodecError("v2 lock を v1 bytes として保存できない")
        return self.original_text


@dataclass(frozen=True)
class HistoricalCampaignLockAuthority:
    """歴史閲覧 decoder が検証した v2 authority と記録 grammar。"""

    environment_contract_sha256: str
    activation_serial: int
    activation_state_sha256: str
    contract_loader_commit: str
    contract_loader_blob_sha256s: dict[str, str]
    recorded_contract_loader_relative_paths: tuple[str, ...]

    def __post_init__(self) -> None:
        grammar = self.recorded_contract_loader_relative_paths
        if type(grammar) is not tuple or grammar not in (
            CONTRACT_LOADER_RELATIVE_PATHS,
            PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS,
            T733_EXACT62_CONTRACT_LOADER_RELATIVE_PATHS,
        ):
            raise TypeError("historical authority の記録 grammar が不正")
        if (type(self.contract_loader_blob_sha256s) is not dict
                or tuple(self.contract_loader_blob_sha256s) != grammar):
            raise TypeError(
                "historical authority の blob map 順序が記録 grammar と不一致"
            )


@dataclass(frozen=True)
class DecodedHistoricalCampaignLock:
    """歴史閲覧専用に検証した lock。通常 decoder の返却型とは非互換。"""

    schema_version: str
    identity_preimage: str
    identity: dict[str, Any]
    authority: HistoricalCampaignLockAuthority | None
    original_text: str

    @property
    def is_v1(self) -> bool:
        return self.schema_version == "campaign-lock/v1"

    @property
    def is_v2(self) -> bool:
        return self.schema_version == CAMPAIGN_LOCK_V2_SCHEMA


@dataclass(frozen=True)
class DecodedNonCertifyingCampaignLock:
    """検証済み A-1 非認証 lock。

    ``identity_tag`` は intent digest から導出できる disclosed-key HMAC であり、
    field 間の偶発的な結合切断を検出する。発行者認証、秘密鍵 custody、または
    同一 Unix user による意図的な再生成への耐性は表さない。
    """

    schema_version: str
    identity_preimage: str
    identity: dict[str, Any]
    common_record: dict[str, Any]
    workload_binding: dict[str, Any]
    identity_tag: str
    original_text: str


def _reject_constant(value: str) -> None:
    raise CampaignLockCodecError(f"非有限 JSON number は許可されない: {value}")


def _exact_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CampaignLockCodecError(f"duplicate JSON key は許可されない: {key!r}")
        result[key] = value
    return result


def _loads(text: str, *, label: str) -> Any:
    if type(text) is not str:
        raise CampaignLockCodecError(f"{label} は exact str でなければならない")
    try:
        return json.loads(
            text,
            object_pairs_hook=_exact_object,
            parse_constant=_reject_constant,
        )
    except CampaignLockCodecError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise CampaignLockCodecError(f"{label} が有効な JSON でない") from exc


def canonical_json(value: Any) -> str:
    """lock wire contract の唯一の canonical JSON encoder。"""
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise CampaignLockCodecError("canonical JSON に変換できない値") from exc


def _validate_identity(value: Any) -> dict[str, Any]:
    if type(value) is not dict or set(value) != IDENTITY_KEYS:
        raise CampaignLockCodecError(
            "identity の exact key 集合が不正"
        )
    for key in ("spec_content", "ccbench_commit", "search_tag"):
        if type(value[key]) is not str:
            raise CampaignLockCodecError(f"identity.{key} は exact str が必要")
    if type(value["search_config"]) is not dict:
        raise CampaignLockCodecError("identity.search_config は exact object が必要")
    if value["trial"] is not None and type(value["trial"]) is not str:
        raise CampaignLockCodecError("identity.trial は exact str または null が必要")
    return value


def _require_hex(value: Any, *, width: int, label: str) -> str:
    regex = _HEX40_RE if width == 40 else _HEX64_RE
    if type(value) is not str or regex.fullmatch(value) is None:
        raise CampaignLockCodecError(
            f"{label} は {width} 桁の lowercase hex でなければならない"
        )
    return value


def _validate_authority(value: Any) -> CampaignLockAuthority:
    if type(value) is not dict or set(value) != AUTHORITY_KEYS:
        raise CampaignLockCodecError("authority の exact key 集合が不正")
    activation_serial = value["activation_serial"]
    if type(activation_serial) is not int or activation_serial <= 0:
        raise CampaignLockCodecError("authority.activation_serial は正の exact int が必要")
    blob_sha256s = value["contract_loader_blob_sha256s"]
    if (type(blob_sha256s) is not dict
            or tuple(sorted(blob_sha256s))
            != tuple(sorted(CONTRACT_LOADER_RELATIVE_PATHS))):
        raise CampaignLockCodecError(
            "authority.contract_loader_blob_sha256s の exact key 集合が不正"
        )
    checked_blobs = {
        path: _require_hex(
            blob_sha256s[path], width=64,
            label=f"authority.contract_loader_blob_sha256s[{path!r}]",
        )
        for path in CONTRACT_LOADER_RELATIVE_PATHS
    }
    return CampaignLockAuthority(
        environment_contract_sha256=_require_hex(
            value["environment_contract_sha256"], width=64,
            label="authority.environment_contract_sha256",
        ),
        activation_serial=activation_serial,
        activation_state_sha256=_require_hex(
            value["activation_state_sha256"], width=64,
            label="authority.activation_state_sha256",
        ),
        contract_loader_commit=_require_hex(
            value["contract_loader_commit"], width=40,
            label="authority.contract_loader_commit",
        ),
        contract_loader_blob_sha256s=checked_blobs,
    )


def _historical_authority_from_current(
        authority: CampaignLockAuthority,
) -> HistoricalCampaignLockAuthority:
    return HistoricalCampaignLockAuthority(
        environment_contract_sha256=authority.environment_contract_sha256,
        activation_serial=authority.activation_serial,
        activation_state_sha256=authority.activation_state_sha256,
        contract_loader_commit=authority.contract_loader_commit,
        contract_loader_blob_sha256s={
            path: authority.contract_loader_blob_sha256s[path]
            for path in CONTRACT_LOADER_RELATIVE_PATHS
        },
        recorded_contract_loader_relative_paths=CONTRACT_LOADER_RELATIVE_PATHS,
    )


def _validate_pre_t733_historical_authority(
        value: Any,
) -> HistoricalCampaignLockAuthority:
    if type(value) is not dict or set(value) != AUTHORITY_KEYS:
        raise CampaignLockCodecError("authority の exact key 集合が不正")
    activation_serial = value["activation_serial"]
    if type(activation_serial) is not int or activation_serial <= 0:
        raise CampaignLockCodecError(
            "authority.activation_serial は正の exact int が必要"
        )
    blob_sha256s = value["contract_loader_blob_sha256s"]
    expected_wire_order = tuple(sorted(PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS))
    if (type(blob_sha256s) is not dict
            or tuple(blob_sha256s) != expected_wire_order):
        raise CampaignLockCodecError(
            "authority.contract_loader_blob_sha256s の歴史 grammar が不正"
        )
    checked_blobs = {
        path: _require_hex(
            blob_sha256s[path], width=64,
            label=f"authority.contract_loader_blob_sha256s[{path!r}]",
        )
        for path in PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS
    }
    return HistoricalCampaignLockAuthority(
        environment_contract_sha256=_require_hex(
            value["environment_contract_sha256"], width=64,
            label="authority.environment_contract_sha256",
        ),
        activation_serial=activation_serial,
        activation_state_sha256=_require_hex(
            value["activation_state_sha256"], width=64,
            label="authority.activation_state_sha256",
        ),
        contract_loader_commit=_require_hex(
            value["contract_loader_commit"], width=40,
            label="authority.contract_loader_commit",
        ),
        contract_loader_blob_sha256s=checked_blobs,
        recorded_contract_loader_relative_paths=(
            PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS
        ),
    )


def _validate_t733_exact62_historical_authority(
        value: Any,
) -> HistoricalCampaignLockAuthority:
    if type(value) is not dict or set(value) != AUTHORITY_KEYS:
        raise CampaignLockCodecError("authority の exact key 集合が不正")
    activation_serial = value["activation_serial"]
    if type(activation_serial) is not int or activation_serial <= 0:
        raise CampaignLockCodecError(
            "authority.activation_serial は正の exact int が必要"
        )
    blob_sha256s = value["contract_loader_blob_sha256s"]
    expected_wire_order = tuple(sorted(T733_EXACT62_CONTRACT_LOADER_RELATIVE_PATHS))
    if (type(blob_sha256s) is not dict
            or tuple(blob_sha256s) != expected_wire_order):
        raise CampaignLockCodecError(
            "authority.contract_loader_blob_sha256s の歴史 grammar が不正"
        )
    checked_blobs = {
        path: _require_hex(
            blob_sha256s[path], width=64,
            label=f"authority.contract_loader_blob_sha256s[{path!r}]",
        )
        for path in T733_EXACT62_CONTRACT_LOADER_RELATIVE_PATHS
    }
    return HistoricalCampaignLockAuthority(
        environment_contract_sha256=_require_hex(
            value["environment_contract_sha256"], width=64,
            label="authority.environment_contract_sha256",
        ),
        activation_serial=activation_serial,
        activation_state_sha256=_require_hex(
            value["activation_state_sha256"], width=64,
            label="authority.activation_state_sha256",
        ),
        contract_loader_commit=_require_hex(
            value["contract_loader_commit"], width=40,
            label="authority.contract_loader_commit",
        ),
        contract_loader_blob_sha256s=checked_blobs,
        recorded_contract_loader_relative_paths=(
            T733_EXACT62_CONTRACT_LOADER_RELATIVE_PATHS
        ),
    )


def _require_non_empty_str(value: Any, *, label: str) -> str:
    if type(value) is not str or not value:
        raise CampaignLockCodecError(f"{label} は non-empty exact str が必要")
    return value


def _validate_non_certifying_common(value: Any) -> dict[str, Any]:
    if type(value) is not dict or set(value) != NON_CERTIFYING_COMMON_KEYS:
        raise CampaignLockCodecError(
            "A-1 non-certifying common_record の exact key 集合が不正"
        )
    if value["mode"] != "registered-formal-non-certifying":
        raise CampaignLockCodecError("A-1 non-certifying mode が不正")
    if value["certifying"] is not False:
        raise CampaignLockCodecError("A-1 non-certifying certifying は false が必要")
    _require_non_empty_str(value["study_id"], label="common_record.study_id")
    for key in (
        "policy_sha256", "preregistration_sha256", "source_binding_sha256",
        "environment_contract_sha256", "intent_sha256",
    ):
        _require_hex(value[key], width=64, label=f"common_record.{key}")
    _require_hex(value["source_commit"], width=40, label="common_record.source_commit")
    campaign_ids = value["campaign_ids"]
    if (
        type(campaign_ids) is not list
        or len(campaign_ids) != 3
        or any(type(item) is not str or not item for item in campaign_ids)
        or len(set(campaign_ids)) != 3
    ):
        raise CampaignLockCodecError(
            "common_record.campaign_ids は一意な exact 3 non-empty str が必要"
        )
    return value


def _validate_non_certifying_workload(
        value: Any, *, common_record: Mapping[str, Any],
) -> dict[str, Any]:
    if type(value) is not dict or set(value) != NON_CERTIFYING_WORKLOAD_KEYS:
        raise CampaignLockCodecError(
            "A-1 workload_binding の exact key 集合が不正"
        )
    _require_non_empty_str(value["workload"], label="workload_binding.workload")
    campaign_id = _require_non_empty_str(
        value["campaign_id"], label="workload_binding.campaign_id",
    )
    ordinal = value["ordinal"]
    if type(ordinal) is not int or ordinal not in range(3):
        raise CampaignLockCodecError("workload_binding.ordinal は 0..2 の exact int が必要")
    if common_record["campaign_ids"][ordinal] != campaign_id:
        raise CampaignLockCodecError(
            "workload_binding campaign_id/ordinal が common_record と不一致"
        )
    return value


def disclosed_identity_key(intent_sha256: str) -> bytes:
    """公開 intent digest から A-1 の disclosed HMAC key を決定的に導出する。"""
    _require_hex(intent_sha256, width=64, label="intent_sha256")
    return hashlib.sha256(
        _DISCLOSED_IDENTITY_KEY_DOMAIN + bytes.fromhex(intent_sha256)
    ).digest()


def non_certifying_identity_tag(
        *, identity_preimage: str, common_record: Mapping[str, Any],
        workload_binding: Mapping[str, Any],
) -> str:
    """A-1 lock field の disclosed-key identity binding tag を返す。"""
    payload = canonical_json({
        "identity_preimage": identity_preimage,
        "common_record": dict(common_record),
        "workload_binding": dict(workload_binding),
    }).encode("utf-8")
    return hmac.new(
        disclosed_identity_key(common_record["intent_sha256"]),
        _LOCK_IDENTITY_TAG_DOMAIN + payload,
        hashlib.sha256,
    ).hexdigest()


def decode_campaign_lock(text: str) -> DecodedCampaignLock:
    """v1/v2 を downgrade なしで判別し、exact wire contract を検査する。"""
    value = _loads(text, label="campaign.lock")
    if type(value) is not dict:
        raise CampaignLockCodecError("campaign.lock top-level は object が必要")

    if "schema_version" in value:
        if set(value) != V2_KEYS:
            raise CampaignLockCodecError("campaign-lock/v2 top-level の exact key 集合が不正")
        if (type(value["schema_version"]) is not str
                or value["schema_version"] != CAMPAIGN_LOCK_V2_SCHEMA):
            raise CampaignLockCodecError("未知または不正な campaign lock schema_version")
        identity_preimage = value["identity_preimage"]
        identity = _validate_identity(
            _loads(identity_preimage, label="identity_preimage")
        )
        if canonical_json(identity) != identity_preimage:
            raise CampaignLockCodecError("identity_preimage が canonical JSON でない")
        authority = _validate_authority(value["authority"])
        if canonical_json(value) != text:
            raise CampaignLockCodecError("campaign-lock/v2 outer が canonical JSON でない")
        return DecodedCampaignLock(
            schema_version=CAMPAIGN_LOCK_V2_SCHEMA,
            identity_preimage=identity_preimage,
            identity=identity,
            authority=authority,
            original_text=text,
        )

    if NON_CERTIFYING_RESERVED_V1_KEYS & set(value):
        raise CampaignLockCodecError(
            "非認証 lock reserved field を schema 無し v1 として受理できない"
        )
    identity = value
    return DecodedCampaignLock(
        schema_version="campaign-lock/v1",
        identity_preimage=text,
        identity=identity,
        authority=None,
        original_text=text,
    )


def _historical_decoded_from_current(
        decoded: DecodedCampaignLock,
) -> DecodedHistoricalCampaignLock:
    authority = (
        None
        if decoded.authority is None
        else _historical_authority_from_current(decoded.authority)
    )
    return DecodedHistoricalCampaignLock(
        schema_version=decoded.schema_version,
        identity_preimage=decoded.identity_preimage,
        identity=decoded.identity,
        authority=authority,
        original_text=decoded.original_text,
    )


def decode_historical_campaign_lock(
        text: str,
) -> DecodedHistoricalCampaignLock:
    """現行・T733 exact-62・pre-T733 exact-24 を歴史閲覧用に decode する。"""
    value = _loads(text, label="historical campaign.lock")
    if type(value) is not dict:
        raise CampaignLockCodecError("campaign.lock top-level は object が必要")

    if "schema_version" not in value:
        return _historical_decoded_from_current(decode_campaign_lock(text))

    if set(value) != V2_KEYS:
        raise CampaignLockCodecError(
            "campaign-lock/v2 top-level の exact key 集合が不正"
        )
    if (type(value["schema_version"]) is not str
            or value["schema_version"] != CAMPAIGN_LOCK_V2_SCHEMA):
        raise CampaignLockCodecError("未知または不正な campaign lock schema_version")

    authority_value = value["authority"]
    blob_sha256s = (
        authority_value.get("contract_loader_blob_sha256s")
        if type(authority_value) is dict
        else None
    )
    current_wire_order = tuple(sorted(CONTRACT_LOADER_RELATIVE_PATHS))
    if type(blob_sha256s) is dict and tuple(blob_sha256s) == current_wire_order:
        return _historical_decoded_from_current(decode_campaign_lock(text))

    identity_preimage = value["identity_preimage"]
    identity = _validate_identity(
        _loads(identity_preimage, label="identity_preimage")
    )
    if canonical_json(identity) != identity_preimage:
        raise CampaignLockCodecError("identity_preimage が canonical JSON でない")
    if (type(blob_sha256s) is dict
            and tuple(blob_sha256s)
            == tuple(sorted(T733_EXACT62_CONTRACT_LOADER_RELATIVE_PATHS))):
        authority = _validate_t733_exact62_historical_authority(authority_value)
    else:
        authority = _validate_pre_t733_historical_authority(authority_value)
    if canonical_json(value) != text:
        raise CampaignLockCodecError("campaign-lock/v2 outer が canonical JSON でない")
    return DecodedHistoricalCampaignLock(
        schema_version=CAMPAIGN_LOCK_V2_SCHEMA,
        identity_preimage=identity_preimage,
        identity=identity,
        authority=authority,
        original_text=text,
    )


def decode_non_certifying_campaign_lock(
        text: str,
) -> DecodedNonCertifyingCampaignLock:
    """A-1 専用非認証 lock の exact schema と disclosed tag を検証する。"""
    value = _loads(text, label="A-1 non-certifying campaign.lock")
    if type(value) is not dict or set(value) != NON_CERTIFYING_KEYS:
        raise CampaignLockCodecError(
            "A-1 non-certifying lock top-level の exact key 集合が不正"
        )
    if value["schema_version"] != NON_CERTIFYING_CAMPAIGN_LOCK_SCHEMA:
        raise CampaignLockCodecError("A-1 non-certifying lock schema_version が不正")
    identity_preimage = value["identity_preimage"]
    identity = _validate_identity(
        _loads(identity_preimage, label="identity_preimage")
    )
    if canonical_json(identity) != identity_preimage:
        raise CampaignLockCodecError("identity_preimage が canonical JSON でない")
    envelope = value["a1_non_certifying"]
    if type(envelope) is not dict or set(envelope) != NON_CERTIFYING_ENVELOPE_KEYS:
        raise CampaignLockCodecError(
            "A-1 non-certifying envelope の exact key 集合が不正"
        )
    common = _validate_non_certifying_common(envelope["common_record"])
    workload = _validate_non_certifying_workload(
        envelope["workload_binding"], common_record=common,
    )
    tag = _require_hex(
        envelope["identity_tag"], width=64,
        label="a1_non_certifying.identity_tag",
    )
    expected = non_certifying_identity_tag(
        identity_preimage=identity_preimage,
        common_record=common,
        workload_binding=workload,
    )
    if not hmac.compare_digest(tag, expected):
        raise CampaignLockCodecError("A-1 non-certifying identity tag mismatch")
    if canonical_json(value) != text:
        raise CampaignLockCodecError("A-1 non-certifying outer が canonical JSON でない")
    return DecodedNonCertifyingCampaignLock(
        schema_version=NON_CERTIFYING_CAMPAIGN_LOCK_SCHEMA,
        identity_preimage=identity_preimage,
        identity=identity,
        common_record=dict(common),
        workload_binding=dict(workload),
        identity_tag=tag,
        original_text=text,
    )


def encode_non_certifying_campaign_lock(
        identity_preimage: str, *, common_record: Mapping[str, Any],
        workload_binding: Mapping[str, Any],
) -> str:
    """A-1 専用非認証 lock を canonical encode して自己検証する。"""
    identity = _validate_identity(
        _loads(identity_preimage, label="identity_preimage")
    )
    if canonical_json(identity) != identity_preimage:
        raise CampaignLockCodecError("identity_preimage が canonical JSON でない")
    common = _validate_non_certifying_common(dict(common_record))
    workload = _validate_non_certifying_workload(
        dict(workload_binding), common_record=common,
    )
    tag = non_certifying_identity_tag(
        identity_preimage=identity_preimage,
        common_record=common,
        workload_binding=workload,
    )
    text = canonical_json({
        "schema_version": NON_CERTIFYING_CAMPAIGN_LOCK_SCHEMA,
        "identity_preimage": identity_preimage,
        "a1_non_certifying": {
            "common_record": common,
            "workload_binding": workload,
            "identity_tag": tag,
        },
    })
    decode_non_certifying_campaign_lock(text)
    return text


def encode_campaign_lock_v2(
        identity_preimage: str,
        authority: CampaignLockAuthority | Mapping[str, Any],
) -> str:
    """canonical な v2 envelope を構築し、自己検証して返す。"""
    try:
        authority_value = (
            authority.as_dict()
            if type(authority) is CampaignLockAuthority
            else dict(authority)
        )
    except (TypeError, ValueError) as exc:
        raise CampaignLockCodecError("authority は object が必要") from exc
    value = {
        "schema_version": CAMPAIGN_LOCK_V2_SCHEMA,
        "identity_preimage": identity_preimage,
        "authority": authority_value,
    }
    text = canonical_json(value)
    decode_campaign_lock(text)
    return text


def preserve_v1_campaign_lock_text(text: str) -> str:
    """検証済み v1 の元文字列を 1 文字も変えず返す。"""
    return decode_campaign_lock(text).preserved_v1_text()


def encode_campaign_lock_v1(identity_preimage: str) -> str:
    """v1 object を検証し、入力文字列を再書式化せず返す。"""
    return preserve_v1_campaign_lock_text(identity_preimage)


def preserve_v1_campaign_lock_bytes(raw: bytes) -> bytes:
    """検証済み v1 の元 bytes を 1 byte も変えず返す。"""
    if type(raw) is not bytes:
        raise CampaignLockCodecError("campaign.lock raw value は exact bytes が必要")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CampaignLockCodecError("campaign.lock bytes が UTF-8 でない") from exc
    preserve_v1_campaign_lock_text(text)
    return raw


def decode_campaign_lock_bytes(raw: bytes) -> DecodedCampaignLock:
    """UTF-8 の raw lock bytes を検証して decode する。"""
    if type(raw) is not bytes:
        raise CampaignLockCodecError("campaign.lock raw value は exact bytes が必要")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CampaignLockCodecError("campaign.lock bytes が UTF-8 でない") from exc
    return decode_campaign_lock(text)


def decode_historical_campaign_lock_bytes(
        raw: bytes,
) -> DecodedHistoricalCampaignLock:
    """UTF-8 raw lock bytes を歴史閲覧専用 grammar で decode する。"""
    if type(raw) is not bytes:
        raise CampaignLockCodecError("campaign.lock raw value は exact bytes が必要")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CampaignLockCodecError("campaign.lock bytes が UTF-8 でない") from exc
    return decode_historical_campaign_lock(text)


def inner_identity_preimage(text: str) -> str:
    """検証済み v1/v2 lock から inner identity 文字列を返す。"""
    return decode_campaign_lock(text).identity_preimage
