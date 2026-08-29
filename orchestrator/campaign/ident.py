# -*- coding: utf-8 -*-
"""campaign 同一性 — 内容ハッシュによる安定・無衝突・決定論的な id (D13)。

`<spec-slug>-<search-tag>-<cfg-hash8>`。ハッシュは spec の**名前でなく内容**を覆う
(編集して名前据え置きでも別 campaign になる = honest-by-construction, §3.4)。
raw env/date と certified execution authority は同一性に含めない。authority は v2 lock
envelope に分離し、inner identity は従来の exact 5 key を維持する。

`campaign.lock` は historical/guided v1 の正準 pre-image、または certified v2 envelope。
再開時はハッシュ一致に加えて inner identity と現在 config を照合する。
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from typing import TYPE_CHECKING, Any, Dict, Optional

from .build_admission import BuildAdmissionPolicy
from . import (
    campaign_lock,
    contract_loader_binding,
    env_contract,
)
from .env_contract import AuthorizedContract, ExecutionEnvironmentContract
from .layout import CampaignLayout
from .model import CampaignConfig, CampaignId
from . import wal

if TYPE_CHECKING:
    from .pipeline import ScreeningConfig


ADMISSION_POLICY_SEARCH_KEY = "build_admission"
_LEGACY_ENVIRONMENT_CONTRACT_SEARCH_KEY = "environment_contract_sha256"
_A1_NON_CERTIFYING_SCHEMA = "paper-story-a1-paired-campaign/v1"
_A1_NON_CERTIFYING_STUDY_ID = "paper-story-a1-20260826-sized-v1"


def is_a1_non_certifying_config(cfg: CampaignConfig) -> bool:
    """A-1 registered non-certifying lane の exact identity marker を判別する。"""
    if type(cfg) is not CampaignConfig or type(cfg.search_config) is not dict:
        return False
    search = cfg.search_config
    return (
        search.get("schema") == _A1_NON_CERTIFYING_SCHEMA
        and search.get("study_id") == _A1_NON_CERTIFYING_STUDY_ID
        and search.get("formal") is False
        and search.get("promotion_prohibited") is True
        and search.get("pairing_design") == "arm-grouped-positional-v1"
        and search.get("non_certifying_mode")
        == "registered-formal-non-certifying"
        and cfg.trial == _A1_NON_CERTIFYING_STUDY_ID
    )


def bind_admission_policy(
        cfg: CampaignConfig, policy: BuildAdmissionPolicy,
) -> CampaignConfig:
    """Return a config whose campaign identity contains the exact admission policy."""
    if type(policy) is not BuildAdmissionPolicy:
        raise TypeError("policy は BuildRunContext.policy の exact value が必要")
    expected = dict(policy.as_preimage())
    existing = cfg.search_config.get(ADMISSION_POLICY_SEARCH_KEY)
    if existing is not None and existing != expected:
        raise ValueError("search_config の admission policy が run context と不一致")
    return replace(
        cfg,
        search_config={**cfg.search_config, ADMISSION_POLICY_SEARCH_KEY: expected},
    )


def bind_environment_contract(
        cfg: CampaignConfig, contract: ExecutionEnvironmentContract,
) -> CampaignConfig:
    """Return a config carrying one exact runtime execution contract."""
    if type(contract) is not ExecutionEnvironmentContract:
        raise TypeError(
            "contract は exact ExecutionEnvironmentContract が必要"
        )
    if _LEGACY_ENVIRONMENT_CONTRACT_SEARCH_KEY in cfg.search_config:
        raise ValueError(
            "search_config.environment_contract_sha256 は旧 identity field であり、"
            "runtime contract と二義化できない"
        )
    existing = cfg.bound_environment_contract
    if existing is not None:
        if type(existing) is not ExecutionEnvironmentContract or existing != contract:
            raise ValueError("campaign config へ異なる environment contract を再 bind できない")
        return cfg
    return replace(cfg, bound_environment_contract=contract)


def verify_admission_preimage(
        policy: BuildAdmissionPolicy, stored_preimage: Optional[str],
) -> None:
    """Require an exact lock schema and the current run's admission policy."""
    if type(policy) is not BuildAdmissionPolicy:
        raise TypeError("policy は BuildRunContext.policy の exact value が必要")
    if stored_preimage is None:
        raise IdentityMismatch("admission-aware campaign には campaign.lock が必要")
    try:
        decoded = campaign_lock.decode_campaign_lock(stored_preimage)
    except campaign_lock.CampaignLockCodecError as exc:
        raise IdentityMismatch("campaign.lock schema が不正") from exc
    if set(decoded.identity) != campaign_lock.IDENTITY_KEYS:
        raise IdentityMismatch("campaign.lock の top-level exact key 集合が不正")
    search_config = decoded.identity["search_config"]
    if type(search_config) is not dict:
        raise IdentityMismatch("campaign.lock search_config が object でない")
    actual = search_config.get(ADMISSION_POLICY_SEARCH_KEY)
    expected = policy.as_preimage()
    if actual != expected:
        raise IdentityMismatch(
            "campaign.lock の admission policy が current run context と不一致"
        )


def screening_search_config(
        screening: Optional["ScreeningConfig"]) -> Dict[str, Dict[str, str]]:
    """screening 方針だけを campaign-id 用 search_config entry に正準化する。

    基準の再アンカーで campaign-id を割らないため、実測値と測定時刻・基準 abort 率は
    含めない。None はキー自体を返さず、歴史的 campaign-id を完全に温存する。
    """
    if screening is None:
        return {}
    return screening_policy_search_config(
        screening.baseline_ref, screening.floor, screening.k,
        screening.high_abort_factor)


def screening_policy_search_config(
        baseline_ref: str, floor: float, k: float,
        high_abort_factor: float) -> Dict[str, Dict[str, str]]:
    """実測値をまだ持たない driver が campaign identity を先に焼くための正本。"""
    return {"screening": {
        "baseline_ref": baseline_ref,
        "floor": repr(floor),
        "k": repr(k),
        "high_abort_factor": repr(high_abort_factor),
    }}


def verify_screening_preimage(
        screening: "ScreeningConfig", stored_preimage: Optional[str]) -> None:
    """runtime screening と campaign.lock に焼き込まれた方針を機械照合する。

    lock 欠落・JSON 破損・screening key 欠落・値の相違はすべて ValueError。既存 campaign
    へ runtime 引数だけで screening を混在させる迂回を、評価開始前に拒否する。
    """
    if stored_preimage is None:
        raise ValueError("screening 有効評価には campaign.lock の方針焼き込みが必要")
    try:
        decoded = campaign_lock.decode_campaign_lock(stored_preimage)
    except campaign_lock.CampaignLockCodecError as exc:
        raise ValueError(
            "campaign.lock schema が不正で screening 方針を検証できない"
        ) from exc
    search_config = decoded.identity["search_config"]
    actual = search_config.get("screening")
    expected = screening_search_config(screening)["screening"]
    if actual != expected:
        raise ValueError(
            "runtime ScreeningConfig と campaign.lock の screening 方針が不一致: "
            f"stored={actual!r}, expected={expected!r}")


def canonical_preimage(cfg: CampaignConfig) -> str:
    """ハッシュ対象の正準シリアライズ。決定論的 (キー順固定・区切り固定)。

    覆うもの: spec の内容 + ccbench-commit + 探索軸 (search_tag) + 探索 config
    (ablation/Tier/scale) + trial。**slug は覆わない** (人間ラベルで spec_content が
    真の同一性源、要件: 名前でなく内容)。raw env_tag/date/実測値と execution authority
    は覆わない。``measurement_env`` は通常の search_config key として覆う。
    """
    if ADMISSION_POLICY_SEARCH_KEY not in cfg.search_config:
        raise ValueError(
            "campaign identity には search_config.build_admission policy が必須"
        )
    if _LEGACY_ENVIRONMENT_CONTRACT_SEARCH_KEY in cfg.search_config:
        raise ValueError(
            "search_config.environment_contract_sha256 は旧 identity field であり拒否する"
        )
    obj: Dict[str, Any] = {
        "spec_content": cfg.spec_content,
        "ccbench_commit": cfg.ccbench_commit,
        "search_tag": cfg.search_tag,
        "search_config": {k: cfg.search_config[k] for k in sorted(cfg.search_config)},
        "trial": cfg.trial,
    }
    # sort_keys + 固定 separators で、同じ内容は必ず同じバイト列に。
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )


def cfg_hash(cfg: CampaignConfig) -> str:
    """正準 pre-image の SHA-256 先頭 8 hex。"""
    pre = canonical_preimage(cfg).encode("utf-8")
    return hashlib.sha256(pre).hexdigest()[:8]


def campaign_id(cfg: CampaignConfig) -> CampaignId:
    """(spec, config) から campaign-id を純粋に導く (状態を保存しない)。"""
    return CampaignId(slug=cfg.spec_slug, search_tag=cfg.search_tag,
                      cfg_hash8=cfg_hash(cfg))


class IdentityMismatch(Exception):
    """ハッシュ一致だが格納済み lock と現在 config の中身が相違 (衝突/改竄)。"""

    def __init__(self, message: str, *, reason: str = "lock-mismatch"):
        super().__init__(message)
        self.reason = reason


def _validate_identity_inputs(
        admission_policy: BuildAdmissionPolicy,
        require_environment_contract: bool,
) -> None:
    if type(admission_policy) is not BuildAdmissionPolicy:
        raise TypeError("admission_policy は exact BuildAdmissionPolicy が必要")
    if type(require_environment_contract) is not bool:
        raise TypeError("require_environment_contract は exact bool が必要")


def _load_current_activation_state(
) -> Any:
    return env_contract.verified_current_activation_state()


def _authority_source_for_new_certified_lock(
        cfg: CampaignConfig,
) -> tuple[ExecutionEnvironmentContract, Any]:
    bound = cfg.bound_environment_contract
    if type(bound) is not ExecutionEnvironmentContract:
        raise IdentityMismatch(
            "certified campaign には runtime environment contract の bind が必要",
            reason="environment-contract-missing",
        )
    try:
        state = _load_current_activation_state()
    except env_contract.EnvContractError as exc:
        raise IdentityMismatch(
            f"campaign-lock activation tuple is not authentic: {exc}",
            reason="activation-tuple-invalid",
        ) from exc
    return bound, state


def _capture_current_loader_binding(
) -> contract_loader_binding.ContractLoaderBinding:
    try:
        binding = contract_loader_binding.capture_contract_loader_binding()
        contract_loader_binding.verify_live_contract_loader_binding(binding)
        return binding
    except contract_loader_binding.ContractLoaderBindingError as exc:
        raise IdentityMismatch(
            f"contract-loader-drift: {exc}",
            reason="contract-loader-drift",
        ) from exc


def _binding_from_lock(
        decoded: campaign_lock.DecodedCampaignLock,
) -> contract_loader_binding.ContractLoaderBinding:
    authority = decoded.authority
    if authority is None:
        raise IdentityMismatch("v2 campaign.lock authority が無い")
    try:
        return contract_loader_binding.binding_from_authority(
            authority.contract_loader_commit,
            authority.contract_loader_blob_sha256s,
        )
    except contract_loader_binding.ContractLoaderBindingError as exc:
        raise IdentityMismatch(
            f"contract-loader-drift: {exc}", reason="contract-loader-drift",
        ) from exc


def verify_recorded_activation_tuple(
        decoded: campaign_lock.DecodedCampaignLock,
) -> None:
    """v2 authority の記録 activation tuple と対象 contract H を認証する。"""
    if type(decoded) is not campaign_lock.DecodedCampaignLock or not decoded.is_v2:
        raise IdentityMismatch(
            "activation tuple 検証には exact v2 campaign.lock が必要",
            reason="activation-tuple-invalid",
        )
    authority = decoded.authority
    if authority is None:
        raise IdentityMismatch(
            "v2 campaign.lock authority が無い",
            reason="activation-tuple-invalid",
        )
    try:
        current = _load_current_activation_state()
        if authority.activation_serial > current.activation_serial:
            raise env_contract.EnvContractError(
                "記録 activation serial が current chain head を越えている"
            )
        recorded = env_contract.verified_historical_activation_state(
            authority.activation_serial,
            authority.activation_state_sha256,
        )
        target_rows = tuple(
            row for row in recorded.active_contracts
            if row.contract_sha256 == authority.environment_contract_sha256
        )
        if len(target_rows) != 1:
            raise env_contract.EnvContractError(
                "記録 activation state が対象 environment contract H を active にしていない"
            )
    except env_contract.EnvContractError as exc:
        raise IdentityMismatch(
            f"campaign-lock activation tuple is not authentic: {exc}",
            reason="activation-tuple-invalid",
        ) from exc


def verify_against_lock(
        cfg: CampaignConfig, stored_preimage: str, *,
        admission_policy: BuildAdmissionPolicy,
        require_environment_contract: bool = True,
) -> None:
    """再開時の関所: 現在 config の正準 pre-image が格納済み lock と一致するか。

    一致しなければ IdentityMismatch (黙ってマージしない、D13)。8 hex 衝突や、
    ハッシュに含めていない軸の相違を捕まえる最終防壁。
    """
    _validate_identity_inputs(admission_policy, require_environment_contract)
    verify_admission_preimage(admission_policy, stored_preimage)
    try:
        decoded = campaign_lock.decode_campaign_lock(stored_preimage)
    except campaign_lock.CampaignLockCodecError as exc:
        raise IdentityMismatch("campaign.lock schema が不正") from exc

    if require_environment_contract and decoded.is_v1:
        raise IdentityMismatch(
            "certified lane では v1 campaign.lock は read-only",
            reason="legacy-lock-read-only",
        )
    if not require_environment_contract and decoded.is_v2:
        raise IdentityMismatch(
            "guided exemption で v2 campaign.lock を開けない",
            reason="v2-lock-requires-authority",
        )

    cur = canonical_preimage(cfg)
    if cur != decoded.identity_preimage:
        raise IdentityMismatch(
            "campaign.lock と現在 config の正準 pre-image が不一致。"
            "ハッシュ衝突か config ドリフト。黙ってマージせず停止する。\n"
            f"  stored : {decoded.identity_preimage}\n  current: {cur}")

    if not require_environment_contract:
        return

    authority = decoded.authority
    verify_recorded_activation_tuple(decoded)
    stored_binding = _binding_from_lock(decoded)
    try:
        contract_loader_binding.verify_live_contract_loader_binding(stored_binding)
    except contract_loader_binding.ContractLoaderBindingError as exc:
        raise IdentityMismatch(
            f"contract-loader-drift: {exc}", reason="contract-loader-drift",
        ) from exc

    bound = cfg.bound_environment_contract
    if authority is None or type(bound) is not ExecutionEnvironmentContract:
        raise IdentityMismatch(
            "certified v2 authority または bound environment contract が不正",
            reason="environment-contract-missing",
        )
    target_sha256 = bound.contract_sha256
    if authority.environment_contract_sha256 != target_sha256:
        raise IdentityMismatch(
            "campaign.lock authority と target environment contract H が不一致",
            reason="environment-contract-mismatch",
        )


def verify_a1_non_certifying_against_lock(
        cfg: CampaignConfig, stored_preimage: str, *,
        admission_policy: BuildAdmissionPolicy,
        require_environment_contract: bool = True,
) -> campaign_lock.DecodedNonCertifyingCampaignLock:
    """A-1 専用 lock を通常 v1/v2 gate と分離して再導出照合する。"""
    _validate_identity_inputs(admission_policy, require_environment_contract)
    if not is_a1_non_certifying_config(cfg):
        raise IdentityMismatch("A-1 non-certifying exact marker が無い")
    if require_environment_contract is not True:
        raise IdentityMismatch(
            "A-1 non-certifying lane は environment contract を必須とする",
            reason="environment-contract-missing",
        )
    try:
        decoded = campaign_lock.decode_non_certifying_campaign_lock(
            stored_preimage
        )
    except campaign_lock.CampaignLockCodecError as exc:
        raise IdentityMismatch("A-1 non-certifying campaign.lock schema が不正") from exc
    search = decoded.identity.get("search_config")
    if (
        type(search) is not dict
        or search.get(ADMISSION_POLICY_SEARCH_KEY) != admission_policy.as_preimage()
    ):
        raise IdentityMismatch(
            "A-1 campaign.lock の admission policy が current run context と不一致"
        )
    current = canonical_preimage(cfg)
    if current != decoded.identity_preimage:
        raise IdentityMismatch(
            "A-1 campaign.lock と現在 config の正準 pre-image が不一致"
        )
    bound = cfg.bound_environment_contract
    if type(bound) is not ExecutionEnvironmentContract:
        raise IdentityMismatch(
            "A-1 non-certifying campaign には environment contract bind が必要",
            reason="environment-contract-missing",
        )
    if decoded.common_record["environment_contract_sha256"] != bound.contract_sha256:
        raise IdentityMismatch(
            "A-1 campaign.lock と target environment contract H が不一致",
            reason="environment-contract-mismatch",
        )
    current_campaign_id = str(campaign_id(cfg))
    workload_binding = decoded.workload_binding
    if (
        workload_binding["campaign_id"] != current_campaign_id
        or current_campaign_id not in decoded.common_record["campaign_ids"]
    ):
        raise IdentityMismatch("A-1 workload binding と再導出 campaign ID が不一致")
    workload = search.get("workload")
    if (
        type(workload) is not dict
        or workload.get("name") != workload_binding["workload"]
    ):
        raise IdentityMismatch("A-1 workload binding と identity workload が不一致")
    return decoded


def ensure_resumable_wal(
        cfg: CampaignConfig, layout: CampaignLayout, *,
        admission_policy: BuildAdmissionPolicy,
        require_environment_contract: bool = True,
        authorization_contract: Optional[AuthorizedContract] = None,
) -> wal.WalTailRepairResult:
    """identity 照合後に tail repair と interrupted-attempt recovery を行う。

    lock の無い既存 WAL は、どの config の記録か照合できないため修復も追記も
    しない。初回 campaign (lock 無し・WAL byte 無し) だけは原子的に lock を
    作成し、その後に機構層の repair を呼ぶ。
    """
    ensure_campaign_identity(
        cfg, layout, admission_policy=admission_policy,
        require_environment_contract=require_environment_contract,
        authorization_contract=authorization_contract,
    )
    if is_a1_non_certifying_config(cfg):
        repair = wal.repair_truncated_tail_a1_non_certifying(
            layout, reject_active_attempt=True,
        )
        wal.recover_interrupted_attempts_a1_non_certifying(
            layout, admission_policy=admission_policy,
        )
    else:
        repair = wal.repair_truncated_tail(
            layout, reject_active_attempt=True,
        )
        wal.recover_interrupted_attempts(
            layout, admission_policy=admission_policy,
        )
    return repair


def ensure_resumable_attempts(
        cfg: CampaignConfig, layout: CampaignLayout, *,
        admission_policy: BuildAdmissionPolicy,
        require_environment_contract: bool = True,
        authorization_contract: Optional[AuthorizedContract] = None,
) -> None:
    """identity 照合後、tail を切り戻さず interrupted attempt だけを閉じる。"""
    ensure_campaign_identity(
        cfg, layout, admission_policy=admission_policy,
        require_environment_contract=require_environment_contract,
        authorization_contract=authorization_contract,
    )
    if is_a1_non_certifying_config(cfg):
        wal.recover_interrupted_attempts_a1_non_certifying(
            layout, admission_policy=admission_policy,
        )
    else:
        wal.recover_interrupted_attempts(
            layout, admission_policy=admission_policy,
        )


def ensure_campaign_identity(
        cfg: CampaignConfig, layout: CampaignLayout, *,
        admission_policy: BuildAdmissionPolicy,
        require_environment_contract: bool = True,
        authorization_contract: Optional[AuthorizedContract] = None,
) -> bool:
    """repair を行わず campaign.lock を原子的に確立・照合する。

    戻り値はこの呼び出しが lock を新規獲得したときだけ True。lock 無しで WAL
    byte がある場合は identity 不明のため拒否する。既存 lock との競合敗者は
    lock を再読して同一 config なら False を返す。
    """
    _validate_identity_inputs(admission_policy, require_environment_contract)
    if cfg.search_config.get(ADMISSION_POLICY_SEARCH_KEY) != admission_policy.as_preimage():
        raise IdentityMismatch(
            "campaign config の admission policy が current run context と不一致"
        )
    stored = wal.read_lock(layout)
    if stored is not None:
        if is_a1_non_certifying_config(cfg):
            verify_a1_non_certifying_against_lock(
                cfg, stored, admission_policy=admission_policy,
                require_environment_contract=require_environment_contract,
            )
        else:
            verify_against_lock(
                cfg, stored, admission_policy=admission_policy,
                require_environment_contract=require_environment_contract,
            )
        return False

    if is_a1_non_certifying_config(cfg):
        raise IdentityMismatch(
            "A-1 non-certifying campaign.lock は3 campaign確定後にpreseedが必要",
            reason="a1-lock-preseed-missing",
        )

    # lock 作成前に WAL の lstat/open/fstat を行う。EIO 等は fail-closed に伝播する。
    if wal.wal_bytes_present(layout):
        raise IdentityMismatch(
            "campaign.lock が無い既存 WAL は identity を照合できないため "
            "resume/repair を拒否する。WAL bytes は変更していない。",
            reason="missing-lock-with-wal-bytes",
        )

    if require_environment_contract:
        binding = _capture_current_loader_binding()
        bound, activation_state = _authority_source_for_new_certified_lock(cfg)
        identity_preimage = canonical_preimage(cfg)
        lock_text = campaign_lock.encode_campaign_lock_v2(
            identity_preimage,
            campaign_lock.CampaignLockAuthority(
                environment_contract_sha256=bound.contract_sha256,
                activation_serial=activation_state.activation_serial,
                activation_state_sha256=activation_state.activation_state_sha256,
                contract_loader_commit=binding.contract_loader_commit,
                contract_loader_blob_sha256s=dict(
                    binding.contract_loader_blob_sha256s
                ),
            ),
        )
    else:
        identity_preimage = canonical_preimage(cfg)
        lock_text = identity_preimage
    if wal.acquire_lock_atomic(layout, lock_text):
        return True

    # 並行 winner が作った lock だけを正本として読み、敗者は何も書かない。
    stored = wal.read_lock(layout)
    if stored is None:
        raise IdentityMismatch(
            "campaign.lock の原子的獲得に失敗し、既存 lock も読めない。",
            reason="lock-create-failed",
        )
    verify_against_lock(
        cfg, stored, admission_policy=admission_policy,
        require_environment_contract=require_environment_contract,
    )
    return False
