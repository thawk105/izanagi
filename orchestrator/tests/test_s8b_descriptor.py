# -*- coding: utf-8 -*-
"""段 8b descriptor 射影と二段の fails-closed gate を検査する。"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import jsonschema
import pytest

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[1]))

from orchestrator.campaign import p2_2, s8b_descriptor  # noqa: E402


SCHEMA_PATH = _HERE.parent / "campaign/s8b_descriptor_schema.json"


# 注意: このファイルに holdout の三軸を JSON 形の静止リテラル (キーと値の隣接) で書くと、
# s8b_holdout_freeze の未既知性検索に自己一致する。値は必ず引数・変数経由で組み立てる。
def _search_config(rratio="80", rmw="0", skew="0.9", *, records=1_000_000, threads=48):
    return {
        "records": records,
        "threads": threads,
        "ycsb": {
            "ycsb_zipf_skew": skew,
            "ycsb_rratio": rratio,
            "ycsb_rmw": rmw,
        },
    }


@pytest.mark.parametrize(
    "workload",
    [item[1] for item in p2_2.WORKLOADS]
    + [
        _search_config(rratio="80")["ycsb"],
        _search_config(rratio="20")["ycsb"],
    ],
)
def test_known_and_holdout_workloads_project_and_validate(workload):
    descriptor = s8b_descriptor.project_from_search_config(
        {"records": p2_2.RECORDS, "threads": p2_2.THREADS, "ycsb": workload}
    )
    s8b_descriptor.validate_descriptor(descriptor)
    if workload["ycsb_rratio"] == "80":
        assert descriptor["read_write"]["read_ratio_percent"] == 80
        assert descriptor["contention"] == {"skew": 0.9, "label": "high"}


@pytest.mark.parametrize(
    ("section", "key", "expected_path"),
    [
        ("read_write", "measured_tps", "$.read_write.measured_tps"),
        ("contention", "winner", "$.contention.winner"),
    ],
)
def test_forbidden_field_positive_controls_fail_both_gates(section, key, expected_path):
    descriptor = s8b_descriptor.descriptor_for_holdout(_search_config())
    descriptor[section][key] = "injected"

    with pytest.raises(s8b_descriptor.DescriptorError) as whole:
        s8b_descriptor.validate_descriptor(descriptor)
    assert expected_path in str(whole.value)

    with pytest.raises(s8b_descriptor.DescriptorError) as scan:
        s8b_descriptor.scan_forbidden_keys(descriptor)
    assert expected_path in str(scan.value)


def test_schema_failure_precedes_forbidden_key_scan():
    descriptor = s8b_descriptor.descriptor_for_holdout(_search_config())
    descriptor["read_write"]["winnerName"] = "injected"
    with pytest.raises(s8b_descriptor.DescriptorError, match="schema") as caught:
        s8b_descriptor.validate_descriptor(descriptor)
    assert isinstance(caught.value.__cause__, jsonschema.ValidationError)


def test_unknown_skew_is_not_reclassified():
    with pytest.raises(s8b_descriptor.DescriptorError, match="未知 skew"):
        s8b_descriptor.project_from_search_config(_search_config(skew="0.7"))


@pytest.mark.parametrize(
    "search_config",
    [
        _search_config(rratio="080"),
        _search_config(rmw=True),
        _search_config(records=True),
        {"records": 1_000_000, "threads": 48},
        {"records": 1_000_000, "threads": 48,
         "ycsb": {k: v for k, v in _search_config()["ycsb"].items()
                  if k != "ycsb_zipf_skew"}},
    ],
)
def test_invalid_types_and_missing_keys_fail_closed(search_config):
    with pytest.raises(s8b_descriptor.DescriptorError):
        s8b_descriptor.project_from_search_config(search_config)


def test_projection_record_is_deterministic_and_hashes_real_schema():
    search_config = _search_config()
    descriptor = s8b_descriptor.descriptor_for_holdout(search_config)
    first = s8b_descriptor.projection_record(search_config, descriptor)
    second = s8b_descriptor.projection_record(copy.deepcopy(search_config), copy.deepcopy(descriptor))
    assert first == second
    assert first["projection_version"] == s8b_descriptor.PROJECTION_VERSION
    assert first["schema_sha256"] == hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest()
    assert len(first["input_sha256"]) == len(first["output_sha256"]) == 64

    reordered = json.loads(json.dumps(search_config, sort_keys=True))
    assert s8b_descriptor.projection_record(reordered, descriptor) == first


@pytest.mark.parametrize("key", ["winnerName", "median_TPS"])
def test_forbidden_scan_is_case_insensitive_substring_match(key):
    with pytest.raises(s8b_descriptor.DescriptorError, match=key):
        s8b_descriptor.scan_forbidden_keys({"safe": [{key: 1}]})


def test_forbidden_scan_does_not_scan_values():
    descriptor = s8b_descriptor.descriptor_for_holdout(_search_config())
    assert descriptor["objective"] == "maximize_throughput_tps"
    s8b_descriptor.scan_forbidden_keys(descriptor)
