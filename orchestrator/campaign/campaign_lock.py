# -*- coding: utf-8 -*-
"""``campaign.lock`` v1/v2 の低層 codec。

この module は import graph の最下層に置く。campaign の model、identity、WAL には
依存せず、wire format の検証と inner identity の取り出しだけを担う。
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Mapping


CAMPAIGN_LOCK_V2_SCHEMA = "campaign-lock/v2"
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
# ``contract_loader_*`` は歴史的名称であり、この値は exact 25 path の
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
    "orchestrator/campaign/enforcement_source_ratification.py",
    "orchestrator/campaign/guided.py",
    "orchestrator/campaign/replay.py",
    "orchestrator/qualification/artifacts.py",
    "orchestrator/qualification/t126_driver.py",
    "orchestrator/verifier/commit_receipt.py",
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

    identity = value
    return DecodedCampaignLock(
        schema_version="campaign-lock/v1",
        identity_preimage=text,
        identity=identity,
        authority=None,
        original_text=text,
    )


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


def inner_identity_preimage(text: str) -> str:
    """検証済み v1/v2 lock から inner identity 文字列を返す。"""
    return decode_campaign_lock(text).identity_preimage
