# -*- coding: utf-8 -*-
"""Official positive 経路用の reviewed-spec 共有 fixture factory。"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from orchestrator.campaign import s8b_oracle_manifest as manifest
from orchestrator.campaign import s8b_oracle_spec as oracle_spec


@dataclass(frozen=True)
class ReviewedSpecFixture:
    """独立 serializer の bytes/hash と検証済み snapshot の一組。"""

    document: dict
    raw_bytes: bytes
    sha256: str
    reviewed_spec: oracle_spec.ReviewedSpec
    schedule: dict


def independent_canonical_bytes(document: Mapping) -> bytes:
    """production serializer に依存しない canonical JSON serializer。"""
    return json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def make_reviewed_spec(
        *, root: Path, n: int, master_seed: str,
        block_sizes: Mapping[str, int], holdout_ids: Sequence[str],
        configuration_ids: Sequence[str], run_contract: Mapping,
        campaign_ids: Mapping[str, str], binding_identity: Sequence[Mapping],
        allowed_excluded_reasons: Sequence[str], generator_versions: Mapping,
) -> ReviewedSpecFixture:
    """明示された全 spec 軸から official positive snapshot を構築する。"""
    schedule = manifest.build_schedule(
        n=n,
        master_seed=master_seed,
        block_sizes=block_sizes,
        holdout_ids=holdout_ids,
        configuration_ids=configuration_ids,
    )
    schedule_raw = independent_canonical_bytes(schedule)
    document = {
        "allowed_excluded_reasons": copy.deepcopy(
            list(allowed_excluded_reasons)
        ),
        "binding_identity": copy.deepcopy(list(binding_identity)),
        "campaign_ids": copy.deepcopy(dict(campaign_ids)),
        "generator_versions": copy.deepcopy(dict(generator_versions)),
        "run_contract": copy.deepcopy(dict(run_contract)),
        "schedule_parameters": {
            "block_sizes": copy.deepcopy(dict(block_sizes)),
            "configuration_ids": copy.deepcopy(list(configuration_ids)),
            "holdout_ids": copy.deepcopy(list(holdout_ids)),
            "master_seed": master_seed,
            "n": n,
        },
        "schedule_sha256": hashlib.sha256(schedule_raw).hexdigest(),
        "schema_version": oracle_spec.SCHEMA_VERSION,
    }
    validated, regenerated = oracle_spec.validate_reviewed_spec(
        document, root=root,
    )
    raw = independent_canonical_bytes(document)
    sha256 = hashlib.sha256(raw).hexdigest()
    reviewed = oracle_spec.ReviewedSpec(
        document=validated,
        raw_bytes=raw,
        sha256=sha256,
        schedule=regenerated,
    )
    return ReviewedSpecFixture(
        document=copy.deepcopy(document),
        raw_bytes=raw,
        sha256=sha256,
        reviewed_spec=reviewed,
        schedule=copy.deepcopy(schedule),
    )


def install_reviewed_spec_sources(
        root: Path, *, source_root: Path, relative_paths: Sequence[str],
) -> None:
    """fixture repo に spec 検証が読む source bytes を設置する。"""
    for relative in relative_paths:
        destination = Path(root) / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((Path(source_root) / relative).read_bytes())


def install_reviewed_spec(
        root: Path, fixture: ReviewedSpecFixture, *, monkeypatch=None,
) -> Path:
    """fixed path へ設置し、任意で canonical approval pin も差し替える。"""
    path = Path(root) / oracle_spec.SPEC_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(fixture.raw_bytes)
    if monkeypatch is not None:
        monkeypatch.setattr(
            oracle_spec, "APPROVED_SPEC_SHA256", fixture.sha256,
        )
    return path


def install_reviewed_spec_document(root: Path, document: Mapping) -> bytes:
    """schema mutation tests 用に document を独立 serialize して fixed path へ置く。"""
    raw = independent_canonical_bytes(document)
    path = Path(root) / oracle_spec.SPEC_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return raw
