# -*- coding: utf-8 -*-
"""段 8b selector 入力の固定 catalog、非漏洩、非干渉を検査する。"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[1]))

from orchestrator.campaign import s8b_descriptor, s8b_holdout_freeze, s8b_selector_input  # noqa: E402


FREEZE_PATH = _HERE.parents[1] / "output/s8b-freeze/holdout_freeze.json"


# 注意: holdout 三軸の JSON 形リテラルをこのファイルへ静止させない。
# descriptor 値と holdout 名は凍結済み artifact から実行時に読む。
def _freeze() -> dict:
    return json.loads(FREEZE_PATH.read_text(encoding="utf-8"))


def _descriptors() -> list[dict]:
    return [
        s8b_descriptor.descriptor_for_holdout(entry)
        for entry in _freeze()["holdouts"].values()
    ]


def _canonical_bytes(value) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def _all_strings(value) -> set[str]:
    found = set()
    if isinstance(value, dict):
        for key, child in value.items():
            found.add(key)
            found.update(_all_strings(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_all_strings(child))
    elif isinstance(value, str):
        found.add(value)
    return found


def test_both_frozen_holdout_descriptors_build_and_validate_fixed_candidates():
    catalog = s8b_selector_input.load_catalog()
    payloads = [s8b_selector_input.build_selector_payload(item) for item in _descriptors()]
    assert len(payloads) == 2

    expected_ids = ["c01", "c02", "c03", "c04", "c05", "c06"]
    for payload in payloads:
        s8b_selector_input.validate_selector_payload(payload)
        candidates = payload["candidates"]
        ids = [candidate["choice_id"] for candidate in candidates]
        assert len(candidates) == 6
        assert len(set(ids)) == 6
        assert ids == expected_ids
        assert _canonical_bytes(candidates) == _canonical_bytes(catalog["candidates"])

    assert _canonical_bytes(payloads[0]["candidates"]) == _canonical_bytes(
        payloads[1]["candidates"]
    )


def test_payload_recursively_excludes_arm_holdout_binding_and_provenance_names():
    freeze = _freeze()
    forbidden = {
        "arm",
        "anchor_workload",
        "sources",
        *freeze["holdouts"].keys(),
        *s8b_selector_input.CHOICE_TO_BINDING.values(),
    }
    for descriptor in _descriptors():
        payload = s8b_selector_input.build_selector_payload(descriptor)
        assert forbidden.isdisjoint(_all_strings(payload))


def test_canonical_selector_payloads_have_no_holdout_conjunction_hit():
    rendered = {
        f"payload-{index}.json": _canonical_bytes(
            s8b_selector_input.build_selector_payload(descriptor)
        ).decode("utf-8")
        for index, descriptor in enumerate(_descriptors())
    }
    hits = s8b_holdout_freeze.holdout_conjunction_hits(rendered)
    assert all(not paths for paths in hits.values())


def test_payload_validation_is_strict_and_hash_is_canonical():
    payload = s8b_selector_input.build_selector_payload(_descriptors()[0])
    reordered = json.loads(json.dumps(payload, sort_keys=True))
    assert s8b_selector_input.selector_payload_sha256(payload) == (
        s8b_selector_input.selector_payload_sha256(reordered)
    )

    with_extra = copy.deepcopy(payload)
    with_extra["arm"] = "injected"
    with pytest.raises(s8b_selector_input.SelectorInputError):
        s8b_selector_input.validate_selector_payload(with_extra)

    changed_candidate = copy.deepcopy(payload)
    changed_candidate["candidates"][0]["mechanism"] = "changed"
    with pytest.raises(s8b_selector_input.SelectorInputError):
        s8b_selector_input.validate_selector_payload(changed_candidate)


@pytest.mark.parametrize("key", ["measured_tps", "winner"])
def test_forbidden_descriptor_leak_positive_control_reaches_explicit_scan(key, monkeypatch):
    descriptor = _descriptors()[0]
    descriptor["scale"][key] = "injected"
    with pytest.raises(s8b_descriptor.DescriptorError):
        s8b_selector_input.build_selector_payload(descriptor)

    monkeypatch.setattr(s8b_descriptor, "validate_descriptor", lambda value: None)
    with pytest.raises(s8b_descriptor.DescriptorError, match=key):
        s8b_selector_input.build_selector_payload(descriptor)


def test_variant_binding_memory_changes_do_not_change_payload_hash():
    frozen_entry = next(iter(_freeze()["holdouts"].values()))
    changed_entry = copy.deepcopy(frozen_entry)
    changed_binding = changed_entry["variant_binding"]
    changed_binding["anchor_workload"] = "changed-in-memory"
    for entry in changed_binding["entries"].values():
        entry["sources"] = [{"path": "changed-in-memory"}]

    original = s8b_descriptor.descriptor_for_holdout(frozen_entry)
    changed = s8b_descriptor.descriptor_for_holdout(changed_entry)
    assert original == changed
    assert s8b_selector_input.selector_payload_sha256(
        s8b_selector_input.build_selector_payload(original)
    ) == s8b_selector_input.selector_payload_sha256(
        s8b_selector_input.build_selector_payload(changed)
    )


@pytest.mark.parametrize("tamper", ["add", "mechanism", "order"])
def test_catalog_tampering_is_rejected(tmp_path, monkeypatch, tamper):
    catalog = s8b_selector_input.load_catalog()
    if tamper == "add":
        catalog["candidates"].append({"choice_id": "c07", "mechanism": "extra"})
    elif tamper == "mechanism":
        catalog["candidates"][0]["mechanism"] = "changed"
    else:
        catalog["candidates"][0], catalog["candidates"][1] = (
            catalog["candidates"][1],
            catalog["candidates"][0],
        )
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(catalog), encoding="utf-8")
    monkeypatch.setattr(s8b_selector_input, "_CATALOG_PATH", path)
    with pytest.raises(s8b_selector_input.SelectorInputError):
        s8b_selector_input.load_catalog()


def test_catalog_duplicate_key_is_rejected_before_last_value_can_win(tmp_path, monkeypatch):
    catalog = s8b_selector_input.load_catalog()
    canonical = json.dumps(catalog, ensure_ascii=False, separators=(",", ":"))
    duplicate = canonical[:-1] + ',"schema_version":"8b-selector-catalog/v1"}'
    path = tmp_path / "catalog-duplicate.json"
    path.write_text(duplicate, encoding="utf-8")
    monkeypatch.setattr(s8b_selector_input, "_CATALOG_PATH", path)

    with pytest.raises(s8b_selector_input.SelectorInputError, match="duplicate key"):
        s8b_selector_input.load_catalog()
