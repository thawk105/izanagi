# -*- coding: utf-8 -*-
"""campaign lock v2 fixture の共有 helper。"""
from __future__ import annotations

import hashlib

from orchestrator.campaign import campaign_lock, contract_loader_binding, env_contract


def _binding_from_recorded_head() -> contract_loader_binding.ContractLoaderBinding:
    """HEAD の実 blob digest から、disk 非依存の test-only binding を作る。"""
    root = contract_loader_binding._validated_root()
    commit = contract_loader_binding._head_commit(root)
    digests = {
        relative: hashlib.sha256(blob).hexdigest()
        for relative, blob in contract_loader_binding._iter_blobs(
            root, commit, campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS,
        )
    }
    return contract_loader_binding.ContractLoaderBinding(commit, digests)


def build_v2_campaign_lock(
        identity_preimage: str, *,
        authorization: env_contract.AuthorizedContract | None = None,
        binding: contract_loader_binding.ContractLoaderBinding | None = None,
) -> str:
    """current activation と記録 HEAD blob から v2 lock を動的に作る。"""
    if authorization is None:
        authorization = env_contract.authorize("linux-baremetal")
    if type(authorization) is not env_contract.AuthorizedContract:
        raise TypeError("authorization は exact AuthorizedContract が必要")
    if binding is None:
        binding = _binding_from_recorded_head()
    if type(binding) is not contract_loader_binding.ContractLoaderBinding:
        raise TypeError("binding は exact ContractLoaderBinding が必要")
    return campaign_lock.encode_campaign_lock_v2(
        identity_preimage,
        campaign_lock.CampaignLockAuthority(
            environment_contract_sha256=authorization.contract.contract_sha256,
            activation_serial=authorization.activation_serial,
            activation_state_sha256=authorization.activation_state_sha256,
            contract_loader_commit=binding.contract_loader_commit,
            contract_loader_blob_sha256s=dict(
                binding.contract_loader_blob_sha256s
            ),
        ),
    )


# Consumer fixture 移行時に短い名前でも同じ正本へ到達できるようにする。
build_v2_lock = build_v2_campaign_lock
