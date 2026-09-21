# 親が repo 外で実行した script の逐語 (`make_mutation_specs.py`)

```python
"""変異 spec を生成する (probe: 全件 SURVIVED 期待で観測 node を集める / final: probe の観測 node で KILLED 期待)。
anchor の一意性を wave worktree の現物で検査する。usage: python3 make_mutation_specs.py probe|final [observed.json]

登録は段 4 裁定 §5 の M0〜M13。M0 は対照 (comment だけ、SURVIVED 期待)。
"""
import hashlib
import json
import sys

W = "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2344-source-bound-emitters"
J = "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-source-bound-emitters"
CL = "orchestrator/campaign/campaign_lock.py"
AA = "orchestrator/campaign/artifact_admission.py"
CB = "orchestrator/campaign/contract_loader_binding.py"

MUTS = [
    # M0 対照 (等価変異、SURVIVED 期待。drift 核が runner に無いことの確認)
    ("m0-control-comment-only", "positive", [
        (CL, "# Frozen declaration order of the preceding exact-85 grammar.\n",
             "# Frozen declaration order of the preceding exact-85 grammar (control).\n"),
    ], "SURVIVED"),
    # 収載追加 (正例)
    ("m1-drop-s8b-oracle-report-from-96", "positive", [
        (CL, '    "orchestrator/campaign/s8b_oracle_report.py",\n    "orchestrator/campaign/s8b_outcome_stage_contract.py",\n',
             '    "orchestrator/campaign/s8b_outcome_stage_contract.py",\n'),
    ], None),
    ("m2-swap-last-two-of-96", "positive", [
        (CL, '    "orchestrator/reports/calibration_report.py",\n    "orchestrator/reports/plot.py",\n)\n',
             '    "orchestrator/reports/plot.py",\n    "orchestrator/reports/calibration_report.py",\n)\n'),
    ], None),
    ("m3-capture-skips-new-emitter-drift", "positive", [
        (CB, "        if disk != blob:\n            raise ContractLoaderBindingError(\n"
             "                f\"contract-loader-drift: disk bytes が HEAD blob と不一致: {relative}\"\n            )\n",
             "        if disk != blob and relative != \"orchestrator/campaign/s8b_oracle_report.py\":\n"
             "            raise ContractLoaderBindingError(\n"
             "                f\"contract-loader-drift: disk bytes が HEAD blob と不一致: {relative}\"\n            )\n"),
    ], None),
    # 歴史可読性 (正例)
    ("m4-exact85-branch-routes-to-pre-t733-validator", "positive", [
        (CL, "        authority = _validate_t2344_exact85_historical_authority(authority_value)\n",
             "        authority = _validate_pre_t733_historical_authority(authority_value)\n"),
    ], None),
    ("m5-skip-committed-blob-verify-for-exact85", "negative", [
        (AA, "                    campaign_lock.T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS)):\n"
             "            contract_loader_binding.verify_committed_contract_loader_blobs(\n",
             "                    campaign_lock.T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS)):\n"
             "            if (authority.recorded_contract_loader_relative_paths\n"
             "                    is campaign_lock.T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS):\n"
             "                return\n"
             "            contract_loader_binding.verify_committed_contract_loader_blobs(\n"),
    ], None),
    # 未知 grammar 拒否 (負例)
    ("m6-exact85-validator-compares-wire-as-set", "negative", [
        (CL, "    expected_wire_order = tuple(sorted(T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS))\n"
             "    if (type(blob_sha256s) is not dict\n            or tuple(blob_sha256s) != expected_wire_order):\n",
             "    expected_wire_order = tuple(sorted(T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS))\n"
             "    if (type(blob_sha256s) is not dict\n            or not set(expected_wire_order) <= set(blob_sha256s)):\n"),
    ], None),
    ("m7-authority-whitelist-accepts-superset", "negative", [
        (CL, "        if type(grammar) is not tuple or grammar not in (\n",
             "        if type(grammar) is not tuple or not any(set(known) <= set(grammar) for known in (\n"),
        (CL, "            T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS,\n        ):\n"
             "            raise TypeError(\"historical authority の記録 grammar が不正\")\n",
             "            T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS,\n        )):\n"
             "            raise TypeError(\"historical authority の記録 grammar が不正\")\n"),
    ], None),
    # certified 隔離 (負例、規律 2)
    ("m8-normal-decoder-unions-exact85", "negative", [
        (CL, "    if (type(blob_sha256s) is not dict\n            or tuple(sorted(blob_sha256s))\n"
             "            != tuple(sorted(CONTRACT_LOADER_RELATIVE_PATHS))):\n"
             "        raise CampaignLockCodecError(\n"
             "            \"authority.contract_loader_blob_sha256s の exact key 集合が不正\"\n        )\n"
             "    checked_blobs = {\n        path: _require_hex(\n"
             "            blob_sha256s[path], width=64,\n"
             "            label=f\"authority.contract_loader_blob_sha256s[{path!r}]\",\n        )\n"
             "        for path in CONTRACT_LOADER_RELATIVE_PATHS\n    }\n",
             "    if (type(blob_sha256s) is not dict\n            or tuple(sorted(blob_sha256s))\n"
             "            not in (tuple(sorted(CONTRACT_LOADER_RELATIVE_PATHS)),\n"
             "                    tuple(sorted(T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS)))):\n"
             "        raise CampaignLockCodecError(\n"
             "            \"authority.contract_loader_blob_sha256s の exact key 集合が不正\"\n        )\n"
             "    _accepted_paths = (\n"
             "        CONTRACT_LOADER_RELATIVE_PATHS\n"
             "        if len(blob_sha256s) == len(CONTRACT_LOADER_RELATIVE_PATHS)\n"
             "        else T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS\n    )\n"
             "    checked_blobs = {\n        path: _require_hex(\n"
             "            blob_sha256s[path], width=64,\n"
             "            label=f\"authority.contract_loader_blob_sha256s[{path!r}]\",\n        )\n"
             "        for path in _accepted_paths\n    }\n"),
    ], None),
    # 歴史 scope の凍結 (負例)
    ("m9-exact85-scope-number-changed", "negative", [
        (AA, "    \"2026-09-20 (f94b61fc8 の source 木、本版の 85 path を起点) の実測では 163 module、うち収載 85)\"\n",
             "    \"2026-09-20 (f94b61fc8 の source 木、本版の 85 path を起点) の実測では 164 module、うち収載 85)\"\n"),
    ], None),
    ("m10-exact85-epoch-carries-current-scope", "negative", [
        (AA, "            identity_scope=T2344_EXACT85_CAMPAIGN_VERIFIER_EPOCH_SCOPE,\n"
             "            excluded_scope=T2344_EXACT85_CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE,\n",
             "            identity_scope=CAMPAIGN_VERIFIER_EPOCH_SCOPE,\n"
             "            excluded_scope=CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE,\n"),
    ], None),
    ("m11-historical-epoch-uses-sorted-order", "negative", [
        (AA, "    payload = _CAMPAIGN_VERIFIER_EPOCH_DOMAIN + b\"\".join(\n"
             "        relative.encode(\"utf-8\") + b\"\\0\" + bytes.fromhex(recorded_map[relative])\n"
             "        for relative in relative_paths\n    )\n",
             "    payload = _CAMPAIGN_VERIFIER_EPOCH_DOMAIN + b\"\".join(\n"
             "        relative.encode(\"utf-8\") + b\"\\0\" + bytes.fromhex(recorded_map[relative])\n"
             "        for relative in sorted(relative_paths)\n    )\n"),
    ], None),
    # M12 (現行 96 scope 対を許す) は probe 2 で SURVIVED。現行 scope 対は歴史 epoch の白名単
    # (HistoricalCampaignVerifierEpoch.__post_init__) に無く、構築段で先に弾かれて到達しない (mask)。
    # DW-M02 に従い実効 gate (歴史 scope 対と map の対応) へ再照準した M12b を登録する。
    ("m12b-recorded-epoch-allows-63-map-under-85-scope", "negative", [
        (AA, "                expected_paths = campaign_lock.T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS\n"
             "            else:\n                raise TypeError(\"historical campaign verifier epoch scope の組が不正\")\n",
             "                expected_paths = campaign_lock.T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS\n"
             "                if (tuple(self.blob_sha256s)\n"
             "                        == campaign_lock.T2429_EXACT63_CONTRACT_LOADER_RELATIVE_PATHS):\n"
             "                    expected_paths = (\n"
             "                        campaign_lock.T2429_EXACT63_CONTRACT_LOADER_RELATIVE_PATHS)\n"
             "            else:\n                raise TypeError(\"historical campaign verifier epoch scope の組が不正\")\n"),
    ], None),
    ("m13-exact85-validator-returns-wire-order-map", "negative", [
        (CL, "        for path in T2344_EXACT85_CONTRACT_LOADER_RELATIVE_PATHS\n    }\n"
             "    return HistoricalCampaignLockAuthority(\n",
             "        for path in expected_wire_order\n    }\n"
             "    return HistoricalCampaignLockAuthority(\n"),
    ], None),
]


def check_unique():
    ok = True
    for mid, _cat, reps, _st in MUTS:
        for f, old, new in reps:
            src = open(f"{W}/{f}", encoding="utf-8").read()
            n = src.count(old)
            if n != 1:
                print(f"NOT UNIQUE ({n}): {mid} {f}: {old[:70]!r}")
                ok = False
            if old == new:
                print(f"NO-OP: {mid}")
                ok = False
    return ok


def build(mode, observed=None):
    muts = []
    only = {"m12b-recorded-epoch-allows-63-map-under-85-scope"} if mode == "probe-m12b" else None
    for mid, cat, reps, st in MUTS:
        if only is not None and mid not in only:
            continue
        if mode.startswith("probe"):
            status, nodes = "SURVIVED", []
        else:
            if st == "SURVIVED":
                status, nodes = "SURVIVED", []
            else:
                nodes = sorted(observed.get(mid, []))
                status = "KILLED"
                if not nodes:
                    print(f"WARNING: {mid} has no observed nodes -> cannot register KILLED")
        muts.append({
            "id": mid, "category": cat,
            "replacements": [{"file": f, "old": o, "new": n} for f, o, n in reps],
            "expected_nodes": nodes, "expected_status": status, "hang_risk": False,
        })
    spec = {
        "schema": "izanagi-dev-wave-mutation-spec/v1",
        "estimated_run_seconds": 420, "timeout_seconds": 2400, "hang_timeout_seconds": 2400,
        "mutations": muts,
    }
    path = f"{J}/mutation-spec-{mode}.json"
    data = json.dumps(spec, indent=2, ensure_ascii=False) + "\n"
    open(path, "w", encoding="utf-8").write(data)
    sha = hashlib.sha256(data.encode("utf-8")).hexdigest()
    open(f"{J}/mutation-spec-{mode}.sha256", "w").write(sha + "\n")
    print(path, sha, len(muts), "mutations")


if __name__ == "__main__":
    mode = sys.argv[1]
    if not check_unique():
        sys.exit(2)
    observed = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else None
    build(mode, observed)
```
