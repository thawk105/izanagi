# -*- coding: utf-8 -*-
"""段 8a trigger-gating 自律ループ harness (p3_s4_loop_trigger_gating) の単体テスト。

`test_p3_s4_loop_sort.py` の型 (共有機構は再検証せず、正しい軸引数での呼び出しと
軸固有の新規機構だけを固める、axis-onboarding §7.4)。本軸固有 = 構文契約の禁止識別子
grep (subtype="syntax-contract") と provenance 情報源記録の受け皿 (E 段レビュー
2026-07-12 裁定の fails-closed 群)。build/verify/bench を伴わない機械部分のみ。
"""
from __future__ import annotations

import ast
import inspect
import json
import os
import sys
import tempfile
import time
from dataclasses import replace
from types import SimpleNamespace

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import env_contract, execution_guard, ident, p3_s4_loop as L  # noqa: E402
from campaign import p3_s4_loop_sort as SORT                        # noqa: E402
from campaign import p3_s4_loop_trigger_gating as T                 # noqa: E402
from campaign import site_policy                                    # noqa: E402
from campaign import wal                                            # noqa: E402
from campaign.auditor_gate import AuditorGateFailure, AuditorVerdict  # noqa: E402
from campaign.build_admission import (BuildAdmission, BuildAdmissionError,  # noqa: E402
                                      BuildProvenance)
from campaign.layout import CampaignLayout                          # noqa: E402
from campaign.model import Genome                                   # noqa: E402
from campaign.pipeline import SEARCH_CONFIG_VERIFY_KEY               # noqa: E402
from campaign.pipeline import VERIFY_LEGACY_PLUS_S2                  # noqa: E402
from critic.digest import load_diff_rejections                      # noqa: E402

_CODER_ADMISSION = BuildAdmission(
    BuildProvenance.CODER_DERIVED, coder_derived_opt_in=True,
)

# 実 transaction.cc の EVOLVE-BLOCK 骨格 (trigger-gating marker) を写した fixture。
# silo-backoff-trigger-gating-variant.patch と同型 — hole は #if 枝の述語代入 1 行、
# gate 変数宣言と gated call は marker 外 (coder 不可触)。
_TEMPLATE = """#pragma once
#include "backoff.hh"

class TxExecutor {
 public:
  void abort() {
#ifndef BACKOFF_TRIGGER_GATING
#error "BACKOFF_TRIGGER_GATING must be defined"
#endif
#if BACKOFF_TRIGGER_GATING
  bool izanagi_gate_pass = true;
#endif
  // EVOLVE-BLOCK-BEGIN silo-backoff-trigger-gating
  // izanagi Phase 3 (D48/phase3.md): coder の編集面はこの #if 枝の代入 1 行のみ。
#if BACKOFF_TRIGGER_GATING
  izanagi_gate_pass = true;
#else
  Backoff::backoff(FLAGS_clocks_per_us);
#endif
  // EVOLVE-BLOCK-END silo-backoff-trigger-gating
#if BACKOFF_TRIGGER_GATING
  if (izanagi_gate_pass) {
    Backoff::backoff(FLAGS_clocks_per_us);
  }
#endif
  }
};
"""
_SRC_REL = T.SOURCE_REL
_G = Genome("silo", dict(T._BASE))
_CLEAN_IMPL = ("  izanagi_gate_pass = "
               "(izanagi_abort_reason_ != IzanagiAbortReason::kNodeVali);")
_FORBIDDEN_IMPL = "  izanagi_gate_pass = (thid_ % 2 == 0);"
_DIFF_QUARANTINE_IMPL = "#define EVIL 1\n" + _CLEAN_IMPL


def _mk_template_dir() -> str:
    d = tempfile.mkdtemp(prefix="izanagi_s8atrigloop_")
    full = os.path.join(d, _SRC_REL)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(_TEMPLATE)
    return d


def _tmp_layout(tag: str) -> CampaignLayout:
    return CampaignLayout(
        root=tempfile.mkdtemp(prefix=f"izanagi_s8atrigloop_{tag}_")).ensure()


def _planner() -> "L.PlannerProposal":
    return L.PlannerProposal(axis=T.MARKER_ID, direction="explore_both", magnitude="small")


def _digest_for(d: str, impl: str = _CLEAN_IMPL) -> str:
    _res, _b, _e, working_diff = L.quarantine(d, impl, marker_id=T.MARKER_ID,
                                              source_rel=_SRC_REL, write=False)
    from campaign.auditor_gate import compute_diff_digest
    return compute_diff_digest(working_diff)


def _driver_source() -> str:
    with open(T.__file__, encoding="utf-8") as f:
        return f.read()


def _assert_literal_env_tag_assignment(source: str) -> None:
    tree = ast.parse(source)
    stores = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and node.id == "ENV_TAG"
        and isinstance(node.ctx, ast.Store)
    ]
    assignments = [
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and node.targets[0] in stores
    ]
    assert len(stores) == 1
    assert len(assignments) == 1
    value = assignments[0].value
    assert type(value) is ast.Constant
    assert value.value == "linux-baremetal"


def _assert_no_legacy_env_attributes(source: str) -> None:
    tree = ast.parse(source)
    hits = [
        (node.attr, node.lineno)
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and node.attr in {"CLK", "NUMA"}
    ]
    assert hits == []


def _assert_no_legacy_env_imports(source: str) -> None:
    tree = ast.parse(source)
    forbidden = {"CLK", "NUMA"}
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        for alias in node.names:
            imported_name = alias.name.rsplit(".", 1)[-1]
            if isinstance(node, ast.Import):
                bound_name = alias.asname or alias.name.split(".", 1)[0]
            else:
                bound_name = alias.asname or alias.name
            if imported_name in forbidden or bound_name in forbidden:
                hits.append((type(node).__name__, alias.name, alias.asname, node.lineno))
    assert hits == []


def _assert_exact_admission_guard_and_lookup(source: str) -> None:
    tree = ast.parse(source)
    admission_defs = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_admit_env_contract"
    ]
    assert len(admission_defs) == 1
    admission = admission_defs[0]
    assert [arg.arg for arg in admission.args.args] == ["site"]
    guards = [node for node in admission.body if isinstance(node, ast.If)]
    returns = [node for node in admission.body if isinstance(node, ast.Return)]
    assert len(guards) == 1
    assert len(returns) == 1

    expected_guard = ast.UnaryOp(
        op=ast.Not(),
        operand=ast.Call(
            func=ast.Name(id="_site_admits_measurement", ctx=ast.Load()),
            args=[ast.Name(id="site", ctx=ast.Load())],
            keywords=[],
        ),
    )
    expected_lookup = ast.Call(
        func=ast.Name(id="_lookup", ctx=ast.Load()),
        args=[ast.Subscript(
            value=ast.Name(id="_SITE_ENV_TAGS", ctx=ast.Load()),
            slice=ast.Name(id="site", ctx=ast.Load()),
            ctx=ast.Load(),
        )],
        keywords=[],
    )
    assert ast.dump(guards[0].test, include_attributes=False) == ast.dump(
        expected_guard, include_attributes=False,
    )
    assert ast.dump(returns[0].value, include_attributes=False) == ast.dump(
        expected_lookup, include_attributes=False,
    )


def _assert_env_names_scoped_to_admission(source: str) -> None:
    tree = ast.parse(source)
    admission_defs = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_admit_env_contract"
    ]
    assert len(admission_defs) == 1
    admission_body_ids = {
        id(node)
        for statement in admission_defs[0].body
        for node in ast.walk(statement)
    }
    module_assignment_ids = {
        id(node)
        for statement in tree.body
        if isinstance(statement, (ast.Assign, ast.AnnAssign))
        for node in ast.walk(statement.target if isinstance(statement, ast.AnnAssign)
                             else ast.Tuple(elts=statement.targets, ctx=ast.Store()))
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    env_tag_stores = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and node.id == "ENV_TAG"
        and isinstance(node.ctx, ast.Store)
    ]
    assert len(env_tag_stores) == 1
    assert id(env_tag_stores[0]) in module_assignment_ids
    lookup_nodes = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id == "_lookup"
    ]
    assert len(lookup_nodes) == 2
    assert all(
        id(node) in module_assignment_ids or id(node) in admission_body_ids
        for node in lookup_nodes
    )
    current_site_nodes = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id == "_current_site"
    ]
    assert len(current_site_nodes) == 3
    getenv_hits = [
        node.lineno for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Attribute)
        and isinstance(node.func.value.value, ast.Name)
        and node.func.value.value.id == "os"
        and node.func.value.attr == "environ"
    ]
    assert getenv_hits == []
    attribute_occurrences = [
        (node.attr, node.lineno)
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and node.attr in {"ENV_TAG", "_lookup", "_current_site"}
    ]
    assert attribute_occurrences == []
    record_def = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_record_diff_reject_admitted"
    )
    env_keywords = [
        keyword.value for node in ast.walk(record_def)
        if isinstance(node, ast.Call)
        for keyword in node.keywords
        if keyword.arg == "env_tag"
    ]
    assert len(env_keywords) == 1
    assert ast.dump(env_keywords[0], include_attributes=False) == ast.dump(
        ast.Attribute(
            value=ast.Name(id="contract", ctx=ast.Load()),
            attr="env_tag", ctx=ast.Load(),
        ),
        include_attributes=False,
    )


def _replace_once(source: str, old: str, new: str) -> str:
    assert source.count(old) == 1
    return source.replace(old, new)


def _load_fresh_driver(monkeypatch, *, current_site, lookup, suffix):
    """依存を先に差し替え、fresh driver が既定 seam を束縛する形でロードする。"""
    import importlib.util

    monkeypatch.setattr(site_policy, "current_site", current_site)
    monkeypatch.setattr(env_contract, "lookup", lookup)
    module_name = f"{T.__name__}__{suffix}"
    spec = importlib.util.spec_from_file_location(module_name, T.__file__)
    assert spec is not None and spec.loader is not None
    fresh_module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, fresh_module)
    spec.loader.exec_module(fresh_module)
    assert fresh_module._current_site is site_policy.current_site
    assert fresh_module._lookup is env_contract.lookup
    return fresh_module


def _sentinel_contract(*, numactl=("numactl", "--sentinel")):
    return env_contract.ExecutionEnvironmentContract(
        env_tag="sentinel-env",
        clocks_per_us=4242,
        numactl=numactl,
        attestation_mode="none",
        isolation_policy=env_contract.IsolationPolicy(
            single_process=False, allow_resume=True,
        ),
        calibration_ref=env_contract.CalibrationRef(
            path="output/sentinel-calibration.json", sha256="0" * 64,
        ),
    )


def _measurement_case(
    monkeypatch, *, site, lookup, order=None, dependency_prefix="", receipt=None,
    admission=_CODER_ADMISSION,
):
    """clean proposal を run_campaign 直前まで進める一時 layout の case。"""
    import contextlib
    from campaign import patchharness

    sub = _mk_template_dir()
    lay = _tmp_layout("measurement")
    calls = []
    monkeypatch.setattr(T, "_current_site", lambda: site)
    monkeypatch.setattr(T, "_lookup", lookup)
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *_args, **_kwargs: contextlib.nullcontext(),
    )
    monkeypatch.setattr(T, "exploration_campaign_layout", lambda *_args, **_kwargs: lay)

    def run_spy(cfg, genomes, perf, env_tag, clocks_per_us, numactl=None, **kwargs):
        if order is not None:
            order.append("run_campaign")
        assert kwargs.get("admission") is _CODER_ADMISSION
        calls.append({
            "campaign_id": str(ident.campaign_id(cfg)),
            "env_tag": env_tag,
            "clocks_per_us": clocks_per_us,
            "numactl": numactl,
            "env_contract": kwargs.get("env_contract"),
            "dependency_prefix": kwargs.get("dependency_prefix"),
            "campaign_namespace": kwargs.get("campaign_namespace"),
        })
        return SimpleNamespace(
            results=[], skipped=0, execution_receipt=receipt,
            campaign_id=str(ident.campaign_id(cfg)), layout_root=lay.root,
        )

    monkeypatch.setattr(T, "run_campaign", run_spy)
    state = L.LoopState(start_ts=time.monotonic())
    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, implementation=_CLEAN_IMPL)
    auditor = AuditorVerdict(verdict="pass", diff_digest=_digest_for(sub))

    def invoke():
        return T.run_one_iteration(
            T.default_cfg(), T.default_perf(), _planner(), coder, auditor, state,
            sub, do_build=True, log=lambda *_args: None,
            admission=admission,
            dependency_prefix=dependency_prefix,
        )

    return invoke, lay, calls


def _reject_case(monkeypatch, *, site, reject_kind="syntax",
                 lookup=env_contract.lookup):
    """指定した reject branch を sink まで進める一時 layout の case。"""
    import contextlib
    from campaign import patchharness

    sub = _mk_template_dir()
    lay = _tmp_layout("reject")
    monkeypatch.setattr(T, "_current_site", lambda: site)
    monkeypatch.setattr(T, "_lookup", lookup)
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *_args, **_kwargs: contextlib.nullcontext(),
    )
    state = L.LoopState(start_ts=time.monotonic())
    if reject_kind == "diff-quarantine":
        implementation = _DIFF_QUARANTINE_IMPL
        auditor = AuditorVerdict(
            verdict="pass", diff_digest="irrelevant-diff-quarantine-precedes-gate",
        )
    elif reject_kind == "syntax":
        implementation = _FORBIDDEN_IMPL
        auditor = AuditorVerdict(
            verdict="pass", diff_digest="irrelevant-syntax-precedes-gate",
        )
    elif reject_kind == "auditor":
        implementation = _CLEAN_IMPL
        auditor = AuditorVerdict(
            verdict="reject", diff_digest=_digest_for(sub),
            violations=[{"type": 16}],
        )
    else:
        raise ValueError(f"unknown reject kind: {reject_kind}")
    coder = T.CoderProposalTriggerGating(
        axis=T.MARKER_ID, implementation=implementation,
    )

    def invoke():
        return T.run_one_iteration(
            T.default_cfg(), T.default_perf(), _planner(), coder, auditor, state,
            sub, do_build=False, layout=lay, log=lambda *_args: None,
        )

    return invoke, lay


# ==== environment contract admission ===========================================

def test_site_admission_matrix():
    assert T._site_admits_measurement(site_policy.OTHER) is True
    assert T._site_admits_measurement(site_policy.PEGASUS_COMPUTE) is True
    for site in (
        site_policy.PEGASUS_LOGIN,
        site_policy.PEGASUS_SUSPECT,
        "UNKNOWN_SITE",
    ):
        assert T._site_admits_measurement(site) is False


def test_environment_module_surface_and_default_seams():
    assert T.ENV_TAG == "linux-baremetal"
    assert not hasattr(T, "CLK")
    assert not hasattr(T, "NUMA")
    assert T._current_site is site_policy.current_site
    assert T._lookup is env_contract.lookup
    assert "site" not in inspect.signature(T.run_one_iteration).parameters
    assert "site" not in inspect.signature(T.drive_iteration).parameters


def test_contract_sentinel_flows_to_run_campaign(monkeypatch):
    contract = _sentinel_contract()
    looked_up = []

    def lookup(env_tag):
        looked_up.append(env_tag)
        return contract

    invoke, lay, calls = _measurement_case(
        monkeypatch, site=site_policy.OTHER, lookup=lookup,
    )
    invoke()
    assert looked_up == [T.ENV_TAG]
    assert calls == [{
        "campaign_id": str(ident.campaign_id(T.default_cfg())),
        "env_tag": contract.env_tag,
        "clocks_per_us": contract.clocks_per_us,
        "numactl": list(contract.numactl),
        "env_contract": None,
        "dependency_prefix": None,
        "campaign_namespace": "exploration",
    }]


def test_same_selector_contract_flows_to_run_campaign(monkeypatch):
    registry_contract = env_contract.lookup(T.ENV_TAG)
    contract = replace(
        registry_contract,
        clocks_per_us=registry_contract.clocks_per_us + 777,
        numactl=(*registry_contract.numactl, "--same-selector-sentinel"),
    )
    assert contract.env_tag == T.ENV_TAG
    assert contract.clocks_per_us != registry_contract.clocks_per_us
    assert contract.numactl != registry_contract.numactl
    assert contract.clocks_per_us != T.L.CLK
    assert list(contract.numactl) != T.L.NUMA

    invoke, _lay, calls = _measurement_case(
        monkeypatch, site=site_policy.OTHER,
        lookup=lambda _env_tag: contract,
    )
    invoke()
    assert calls == [{
        "campaign_id": str(ident.campaign_id(T.default_cfg())),
        "env_tag": T.ENV_TAG,
        "clocks_per_us": contract.clocks_per_us,
        "numactl": list(contract.numactl),
        "env_contract": None,
        "dependency_prefix": None,
        "campaign_namespace": "exploration",
    }]


def test_empty_numactl_contract_flows_as_empty_list(monkeypatch):
    contract = _sentinel_contract(numactl=())
    invoke, _lay, calls = _measurement_case(
        monkeypatch, site=site_policy.OTHER, lookup=lambda _env_tag: contract,
    )
    invoke()
    assert calls[0]["numactl"] == []


def test_campaign_identity_is_unchanged_for_other_and_split_for_compute():
    cfg = T.default_cfg()
    other_cfg = T._campaign_cfg_for_site(cfg, site_policy.OTHER)
    compute_cfg = T._campaign_cfg_for_site(cfg, site_policy.PEGASUS_COMPUTE)
    assert other_cfg is cfg
    assert str(ident.campaign_id(other_cfg)) == str(ident.campaign_id(cfg))
    assert str(ident.campaign_id(other_cfg)) == (
        "p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5"
    )
    assert str(ident.campaign_id(compute_cfg)) == (
        "p3-s8a-trigger-loop-s8a-trigger-autonomous-75727902"
    )
    assert compute_cfg.search_config["measurement_env"] == "pegasus"
    assert "measurement_env" not in cfg.search_config


def test_fixture_cli_uses_authoritative_layout_and_preserves_legacy_bytes(
    tmp_path, monkeypatch,
):
    import contextlib
    from campaign import patchharness

    legacy = CampaignLayout(str(tmp_path / "legacy")).ensure()
    legacy_digest = os.path.join(legacy.root, T.DIGEST_BASENAME)
    with open(legacy_digest, "wb") as stream:
        stream.write(b"legacy-linux-bytes\n")
    before = {
        os.path.relpath(os.path.join(root, name), legacy.root):
            open(os.path.join(root, name), "rb").read()
        for root, _dirs, files in os.walk(legacy.root)
        for name in files
    }
    compute = CampaignLayout(str(tmp_path / "compute")).ensure()
    monkeypatch.setattr(patchharness, "assert_pinned_clean", lambda *_a, **_k: None)
    monkeypatch.setattr(
        patchharness, "applied", lambda *_a, **_k: contextlib.nullcontext(),
    )
    monkeypatch.setattr(
        L, "quarantine",
        lambda *_a, **_k: (SimpleNamespace(), "", "", "fixture-diff"),
    )
    monkeypatch.setattr(
        T, "run_one_iteration",
        lambda *_a, **_k: {
            "outcome": "dry-pass", "variant": None,
            "campaign_id": "p3-s8a-trigger-loop-s8a-trigger-autonomous-75727902",
            "layout_root": compute.root,
        },
    )
    monkeypatch.setattr(L, "make_critic_digest", lambda *_a, **_k: "compute-only\n")
    monkeypatch.setattr(
        T, "exploration_campaign_layout",
        lambda campaign_id: (
            CampaignLayout(compute.root)
            if campaign_id == "p3-s8a-trigger-loop-s8a-trigger-autonomous-75727902"
            else pytest.fail("CLI が返却された campaign_id 以外から layout を再計算した")
        ),
    )
    assert T.main(["--no-build", "--no-isolate-worktree"]) == 0
    after = {
        os.path.relpath(os.path.join(root, name), legacy.root):
            open(os.path.join(root, name), "rb").read()
        for root, _dirs, files in os.walk(legacy.root)
        for name in files
    }
    assert after == before
    assert open(
        os.path.join(compute.root, T.DIGEST_BASENAME), encoding="utf-8",
    ).read() == "compute-only\n"


def test_compute_forwards_required_contract_and_records_sink_receipt(monkeypatch):
    contract = env_contract.lookup("pegasus")
    order = []
    receipt = {"schema": "fixture-required-receipt"}
    invoke, lay, calls = _measurement_case(
        monkeypatch, site=site_policy.PEGASUS_COMPUTE,
        lookup=lambda tag: contract if tag == "pegasus" else pytest.fail(tag),
        order=order,
        dependency_prefix="/scr/fixture-prefix",
        receipt=receipt,
    )
    invoke()
    assert order == ["run_campaign"]
    assert calls[0]["env_contract"] is contract
    assert calls[0]["dependency_prefix"] == "/scr/fixture-prefix"
    T._append_provenance_entry(lay, 0, {"outcome": "aborted", "variant": "v-fixture"})
    with open(T._provenance_path(lay), encoding="utf-8") as f:
        entry = json.load(f)["entries"]["0"]
    assert entry["site"] == site_policy.PEGASUS_COMPUTE
    assert entry["contract_sha256"] == contract.contract_sha256
    assert entry["execution_receipt"] == receipt
    assert len(entry["execution_receipt_sha256"]) == 64
    assert entry["outcome"] == "aborted"


def test_attestation_failure_from_campaign_sink_propagates_without_wal(monkeypatch):
    contract = env_contract.lookup("pegasus")
    invoke, lay, calls = _measurement_case(
        monkeypatch, site=site_policy.PEGASUS_COMPUTE,
        lookup=lambda _tag: contract,
    )
    monkeypatch.setattr(
        T, "run_campaign",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            execution_guard.ExecutionGuardError("fixture probe failure")
        ),
    )
    with pytest.raises(execution_guard.ExecutionGuardError):
        invoke()
    assert calls == []
    assert wal.read_records(lay) == []


def test_compute_measurement_sink_requires_coder_admission_before_campaign(monkeypatch):
    contract = env_contract.lookup("pegasus")
    invoke, lay, calls = _measurement_case(
        monkeypatch, site=site_policy.PEGASUS_COMPUTE,
        lookup=lambda _tag: contract, admission=None,
    )
    with pytest.raises(BuildAdmissionError):
        invoke()
    assert calls == []
    assert wal.read_records(lay) == []


def test_compute_existing_loop_state_rejected_after_neutralized_freshness(monkeypatch):
    from campaign import p3_autonomous_workload_trial as autonomous

    contract = env_contract.lookup("pegasus")
    invoke, lay, calls = _measurement_case(
        monkeypatch, site=site_policy.PEGASUS_COMPUTE,
        lookup=lambda _tag: contract,
    )
    L.save_loop_state(lay, L.LoopState(start_wall=time.time()))
    monkeypatch.setattr(autonomous, "_assert_fresh_campaign_state", lambda _layout: None)
    autonomous._assert_fresh_campaign_state(lay)
    with pytest.raises(execution_guard.ExecutionGuardError, match="allow_resume=False"):
        invoke()
    assert calls == []
    assert wal.read_records(lay) == []


@pytest.mark.parametrize("reject_kind", ["diff-quarantine", "syntax", "auditor"])
def test_compute_no_resume_precedes_all_reject_writes(monkeypatch, reject_kind):
    invoke, lay = _reject_case(
        monkeypatch, site=site_policy.PEGASUS_COMPUTE,
        reject_kind=reject_kind,
    )
    L.save_loop_state(lay, L.LoopState(start_wall=time.time()))
    state_before = open(L.loop_state_path(lay), "rb").read()
    with pytest.raises(execution_guard.ExecutionGuardError, match="allow_resume=False"):
        invoke()
    assert open(L.loop_state_path(lay), "rb").read() == state_before
    assert wal.read_records(lay) == []
    assert not os.path.exists(T._provenance_path(lay))


def test_compute_no_resume_rejects_wal_only_crash_tail_without_mutation(monkeypatch):
    invoke, lay = _reject_case(
        monkeypatch, site=site_policy.PEGASUS_COMPUTE, reject_kind="syntax",
    )
    wal.log(lay, "crash-tail", "build_start", "pegasus", {"fixture": True})
    before = open(lay.wal_file, "rb").read()
    assert not os.path.exists(L.loop_state_path(lay))
    with pytest.raises(execution_guard.ExecutionGuardError, match="allow_resume=False"):
        invoke()
    assert open(lay.wal_file, "rb").read() == before
    assert not os.path.exists(L.loop_state_path(lay))
    assert not os.path.exists(T._provenance_path(lay))


def test_lookup_error_propagates_before_campaign_and_wal(monkeypatch):
    error = env_contract.EnvContractError("sentinel lookup failure")

    def fail_lookup(_env_tag):
        raise error

    invoke, lay, calls = _measurement_case(
        monkeypatch, site=site_policy.OTHER, lookup=fail_lookup,
    )
    with pytest.raises(env_contract.EnvContractError) as excinfo:
        invoke()
    assert excinfo.value is error
    assert calls == []
    assert wal.read_records(lay) == []


def test_measurement_sink_rejects_login_before_campaign_and_wal(monkeypatch):
    invoke, lay, calls = _measurement_case(
        monkeypatch, site=site_policy.PEGASUS_LOGIN,
        lookup=lambda _env_tag: pytest.fail("拒否 site で contract lookup へ到達した"),
    )
    with pytest.raises(execution_guard.ExecutionGuardError):
        invoke()
    assert calls == []
    assert wal.read_records(lay) == []


def test_measurement_sink_admits_compute_with_pegasus_contract_and_identity(monkeypatch):
    contract = env_contract.lookup("pegasus")
    invoke, lay, calls = _measurement_case(
        monkeypatch,
        site=site_policy.PEGASUS_COMPUTE,
        lookup=lambda _env_tag: contract,
    )
    invoke()
    assert len(calls) == 1
    assert calls[0]["env_tag"] == "pegasus"
    assert calls[0]["env_contract"] is contract
    assert calls[0]["campaign_id"] != str(ident.campaign_id(T.default_cfg()))
    assert wal.read_records(lay) == []


@pytest.mark.parametrize("reject_kind", [
    "diff-quarantine",
    "syntax",
    "auditor",
])
def test_reject_sink_compute_records_pegasus_without_attestation(monkeypatch, reject_kind):
    invoke, lay = _reject_case(
        monkeypatch, site=site_policy.PEGASUS_COMPUTE,
        reject_kind=reject_kind, lookup=env_contract.lookup,
    )
    out = invoke()
    assert out["outcome"] == "rejected"
    assert {record.env_tag for record in wal.read_records(lay)} == {"pegasus"}


@pytest.mark.parametrize("reject_kind", [
    "diff-quarantine",
    "syntax",
    "auditor",
])
def test_reject_sink_refuses_login_without_wal(monkeypatch, reject_kind):
    invoke, lay = _reject_case(
        monkeypatch, site=site_policy.PEGASUS_LOGIN,
        reject_kind=reject_kind,
        lookup=lambda _env_tag: pytest.fail("拒否 site で contract lookup へ到達した"),
    )
    with pytest.raises(execution_guard.ExecutionGuardError):
        invoke()
    assert wal.read_records(lay) == []


def test_reject_sink_other_writes_two_contract_tagged_records(monkeypatch):
    contract = _sentinel_contract()
    looked_up = []

    def lookup(env_tag):
        looked_up.append(env_tag)
        return contract

    invoke, lay = _reject_case(
        monkeypatch, site=site_policy.OTHER, lookup=lookup,
    )
    out = invoke()
    records = wal.read_records(lay)
    assert out["outcome"] == "rejected"
    assert looked_up == [T.ENV_TAG]
    assert len(records) == 2
    assert [record.env_tag for record in records] == [
        contract.env_tag, contract.env_tag,
    ]


def test_reject_lookup_error_propagates_without_wal(monkeypatch):
    error = env_contract.EnvContractError("sentinel reject lookup failure")

    def fail_lookup(_env_tag):
        raise error

    invoke, lay = _reject_case(
        monkeypatch, site=site_policy.OTHER, lookup=fail_lookup,
    )
    with pytest.raises(env_contract.EnvContractError) as excinfo:
        invoke()
    assert excinfo.value is error
    assert wal.read_records(lay) == []


def test_default_path_resolves_pegasus_contract_from_site_policy(monkeypatch):
    import importlib.util

    module_name = f"{T.__name__}__default_path_test"
    def sentinel_current_site():
        return site_policy.PEGASUS_COMPUTE

    monkeypatch.setattr(site_policy, "current_site", sentinel_current_site)
    spec = importlib.util.spec_from_file_location(module_name, T.__file__)
    assert spec is not None and spec.loader is not None
    fresh_module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, fresh_module)
    spec.loader.exec_module(fresh_module)

    assert fresh_module._admit_env_contract(site_policy.PEGASUS_COMPUTE).env_tag == "pegasus"


def test_default_path_rejects_login_from_site_policy(monkeypatch):
    def sentinel_current_site():
        return site_policy.PEGASUS_LOGIN

    fresh_module = _load_fresh_driver(
        monkeypatch, current_site=sentinel_current_site,
        lookup=lambda _env_tag: pytest.fail("拒否 site で contract lookup へ到達した"),
        suffix="default_login_rejection_test",
    )
    with pytest.raises(execution_guard.ExecutionGuardError):
        fresh_module._admit_env_contract(fresh_module._current_site())


@pytest.mark.parametrize("site", [
    site_policy.PEGASUS_LOGIN,
    site_policy.PEGASUS_SUSPECT,
    "UNKNOWN_SITE",
])
def test_admit_env_contract_behaviorally_rejects_non_admitted_sites(site):
    with pytest.raises(execution_guard.ExecutionGuardError):
        T._admit_env_contract(site)


def test_fresh_default_seams_flow_distinct_contract_to_measurement_sink(monkeypatch):
    """R16 measurement 実経路。import 後の module 再束縛や動的 reflection は保証外。"""
    import contextlib
    from campaign import patchharness

    contract = _sentinel_contract()
    looked_up = []

    def current_site():
        return site_policy.OTHER

    def lookup(env_tag):
        looked_up.append(env_tag)
        return contract

    fresh = _load_fresh_driver(
        monkeypatch, current_site=current_site, lookup=lookup,
        suffix="default_measurement_sink_test",
    )
    sub = _mk_template_dir()
    lay = _tmp_layout("fresh-default-measurement")
    calls = []
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *_args, **_kwargs: contextlib.nullcontext(),
    )
    monkeypatch.setattr(
        fresh, "exploration_campaign_layout", lambda *_args, **_kwargs: lay,
    )

    def run_spy(cfg, genomes, perf, env_tag, clocks_per_us, numactl=None, **kwargs):
        assert kwargs.get("admission") is _CODER_ADMISSION
        calls.append({
            "env_tag": env_tag,
            "clocks_per_us": clocks_per_us,
            "numactl": numactl,
            "campaign_namespace": kwargs.get("campaign_namespace"),
        })
        return SimpleNamespace(results=[], skipped=0)

    monkeypatch.setattr(fresh, "run_campaign", run_spy)
    coder = fresh.CoderProposalTriggerGating(
        axis=fresh.MARKER_ID, implementation=_CLEAN_IMPL,
    )
    auditor = AuditorVerdict(verdict="pass", diff_digest=_digest_for(sub))
    fresh.run_one_iteration(
        fresh.default_cfg(), fresh.default_perf(), _planner(), coder, auditor,
        L.LoopState(start_ts=time.monotonic()), sub, do_build=True,
        log=lambda *_args: None, admission=_CODER_ADMISSION,
    )

    assert fresh._current_site is current_site
    assert fresh._lookup is lookup
    assert looked_up == [fresh.ENV_TAG]
    assert calls == [{
        "env_tag": contract.env_tag,
        "clocks_per_us": contract.clocks_per_us,
        "numactl": list(contract.numactl),
        "campaign_namespace": "exploration",
    }]


def test_fresh_default_seams_flow_distinct_contract_to_reject_sink(monkeypatch):
    """R16 reject 実経路。import 後の module 再束縛や動的 reflection は保証外。"""
    import contextlib
    from campaign import patchharness

    contract = _sentinel_contract()
    looked_up = []

    def current_site():
        return site_policy.OTHER

    def lookup(env_tag):
        looked_up.append(env_tag)
        return contract

    fresh = _load_fresh_driver(
        monkeypatch, current_site=current_site, lookup=lookup,
        suffix="default_reject_sink_test",
    )
    sub = _mk_template_dir()
    lay = _tmp_layout("fresh-default-reject")
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *_args, **_kwargs: contextlib.nullcontext(),
    )
    coder = fresh.CoderProposalTriggerGating(
        axis=fresh.MARKER_ID, implementation=_FORBIDDEN_IMPL,
    )
    auditor = AuditorVerdict(
        verdict="pass", diff_digest="irrelevant-syntax-precedes-gate",
    )
    out = fresh.run_one_iteration(
        fresh.default_cfg(), fresh.default_perf(), _planner(), coder, auditor,
        L.LoopState(start_ts=time.monotonic()), sub, do_build=False, layout=lay,
        log=lambda *_args: None,
    )

    records = wal.read_records(lay)
    assert fresh._current_site is current_site
    assert fresh._lookup is lookup
    assert out["outcome"] == "rejected"
    assert looked_up == [fresh.ENV_TAG]
    assert len(records) == 2
    assert [record.env_tag for record in records] == [
        contract.env_tag, contract.env_tag,
    ]


def test_clean_dry_pass_still_admitted_on_pegasus(monkeypatch):
    import contextlib
    from campaign import patchharness

    sub = _mk_template_dir()
    lay = _tmp_layout("dry-pass-pegasus")
    lookup_calls = 0

    def lookup(_env_tag):
        nonlocal lookup_calls
        lookup_calls += 1
        return _sentinel_contract()

    site_calls = 0

    def current_site():
        nonlocal site_calls
        site_calls += 1
        return site_policy.PEGASUS_COMPUTE

    monkeypatch.setattr(T, "_current_site", current_site)
    monkeypatch.setattr(T, "_lookup", lookup)
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *_args, **_kwargs: contextlib.nullcontext(),
    )
    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, implementation=_CLEAN_IMPL)
    auditor = AuditorVerdict(verdict="pass", diff_digest=_digest_for(sub))
    out = T.run_one_iteration(
        T.default_cfg(), T.default_perf(), _planner(), coder, auditor,
        L.LoopState(start_ts=time.monotonic()), sub, do_build=False, layout=lay,
        log=lambda *_args: None,
    )
    assert out == {
        "outcome": "dry-pass", "variant": None,
        "campaign_id": "p3-s8a-trigger-loop-s8a-trigger-autonomous-75727902",
        "layout_root": lay.root,
    }
    assert site_calls == 1
    assert lookup_calls == 1
    assert wal.read_records(lay) == []


def test_driver_has_no_hardcoded_resolved_env_literals():
    assert env_contract.find_env_literals(
        _driver_source(), {1800, "--interleave=all"},
    ) == []


def test_driver_env_tag_assignment_is_literal_constant():
    """R10 の source AST pin。getattr + 文字列連結等の故意の難読化は保証外。"""
    _assert_literal_env_tag_assignment(_driver_source())


def test_driver_has_no_legacy_env_attribute_references():
    """R11 の source AST pin。getattr 等の故意の難読化に対する防壁は主張しない。"""
    _assert_no_legacy_env_attributes(_driver_source())


def test_driver_has_no_legacy_env_imports():
    """R14 の import pin。動的 import・star import の解決結果までは保証しない。"""
    _assert_no_legacy_env_imports(_driver_source())


def test_driver_admission_guard_and_lookup_are_exact():
    """R13 の exact-shape pin。等価 helper 分割や動的呼出しまで意味解析しない。"""
    _assert_exact_admission_guard_and_lookup(_driver_source())


def test_driver_env_names_are_scoped_to_admission():
    """R12/R15 pin。直接属性再設定は拒否するが setattr・exec 等の動的変更は保証外。"""
    _assert_env_names_scoped_to_admission(_driver_source())


def test_driver_ast_pins_reject_m20_through_m23_source_mutants():
    """登録変異の source 検出を固定する。動的 import・setattr・難読化は保証外。"""
    source = _driver_source()
    m20 = _replace_once(
        source,
        "return _lookup(_SITE_ENV_TAGS[site])",
        'return _lookup(os.environ.get("IZANAGI_ENV_TAG", ENV_TAG))',
    )
    m21 = _replace_once(
        source,
        "if not _site_admits_measurement(site):",
        "if not _site_admits_measurement(site) and "
        'not os.environ.get("IZANAGI_ALLOW_PEGASUS"):',
    )
    legacy_import = (
        "from campaign import p3_s4_loop as L                              "
        "# noqa: E402\n"
    )
    m22 = _replace_once(
        source,
        legacy_import,
        legacy_import + "from campaign.p3_s4_loop import CLK as LEGACY_CLK\n",
    )
    m22 = _replace_once(
        m22,
        "contract.env_tag, contract.clocks_per_us,",
        "contract.env_tag, (LEGACY_CLK if _current_site is "
        "site_policy.current_site else contract.clocks_per_us),",
    )
    m23 = _replace_once(
        source,
        "env_tag=contract.env_tag",
        'env_tag=(contract.env_tag if site != site_policy.PEGASUS_COMPUTE '
        'else "linux-baremetal")',
    )

    with pytest.raises(AssertionError):
        _assert_exact_admission_guard_and_lookup(m20)
    with pytest.raises(AssertionError):
        _assert_exact_admission_guard_and_lookup(m21)
    with pytest.raises(AssertionError):
        _assert_no_legacy_env_imports(m22)
    with pytest.raises(AssertionError):
        _assert_env_names_scoped_to_admission(m22)
    with pytest.raises(AssertionError):
        _assert_env_names_scoped_to_admission(m23)


def test_driver_env_name_scope_rejects_direct_module_attribute_reset():
    """直接 sys.modules 属性再設定は拒否する。setattr・exec・別名経由の変更は保証外。"""
    source = _replace_once(
        _driver_source(),
        'ENV_TAG = "linux-baremetal"',
        'ENV_TAG = "linux-baremetal"\n'
        'sys.modules[__name__].ENV_TAG = os.environ.get('
        '"IZANAGI_ENV_TAG", "linux-baremetal")',
    )
    with pytest.raises(AssertionError):
        _assert_env_names_scoped_to_admission(source)


# ==== 構文契約の禁止識別子 grep =================================================

def test_check_syntax_contract_clean_and_forbidden():
    assert T.check_syntax_contract(_CLEAN_IMPL) == []
    assert T.check_syntax_contract(_FORBIDDEN_IMPL) == ["thid_"]
    multi = "  izanagi_gate_pass = (thid_ > 0) && write_set_.empty();"
    assert T.check_syntax_contract(multi) == ["thid_", "write_set_"]


def test_check_syntax_contract_requires_identifier_boundary():
    """前方境界 (\\b): 別識別子の内部 (例: xthid_) にはマッチしない。合成語の前方一致
    (write_set_foo) は過検出安全側で許容 (レビュー FC-N1 裁定)。"""
    assert T.check_syntax_contract("  izanagi_gate_pass = (xthid_ > 0);") == []
    assert T.check_syntax_contract("  izanagi_gate_pass = write_set_foo;") == ["write_set_"]


def test_quarantine_and_audit_rejects_forbidden_identifier(monkeypatch):
    """禁止識別子は diff 検疫 pass 後でも subtype='syntax-contract' で機械 reject
    (hard gate、fails-closed — auditor verdict=pass でも通らない。レビュー FC-8 裁定)。"""
    monkeypatch.setattr(T, "_current_site", lambda: site_policy.OTHER)
    d = _mk_template_dir()
    auditor = AuditorVerdict(verdict="pass", diff_digest="irrelevant-syntax-precedes-gate")
    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, implementation=_FORBIDDEN_IMPL)
    state = L.LoopState(start_ts=time.monotonic())
    lay = _tmp_layout("syntax")
    gate = T._quarantine_and_audit(
        d, coder, auditor, _G, lay, state, _planner(), write=False,
        contract=T._admit_env_contract(site_policy.OTHER),
    )
    assert gate is not None
    assert gate["outcome"] == "rejected"
    assert gate["digest"]["subtype"] == "syntax-contract"
    assert gate["digest"]["rejection_type"] == "diff-quarantine"
    # 既存 consumer がそのまま拾える (相乗り経路)
    dqs = load_diff_rejections(lay)
    assert len(dqs) == 1 and dqs[0].subtype == "syntax-contract"
    # evidence はマッチ識別子名のみ — coder の gate 式本文を critic へ運ばない (リーク裁定)
    assert "thid_" in gate["digest"]["evidence"]
    assert "% 2 == 0" not in gate["digest"]["evidence"]
    assert state.whiteboard[-1].result == "rejected"


def test_render_rejections_uses_syntax_contract_hint(monkeypatch):
    from critic.digest import render_rejections
    monkeypatch.setattr(T, "_current_site", lambda: site_policy.OTHER)
    d = _mk_template_dir()
    auditor = AuditorVerdict(verdict="pass", diff_digest="irrelevant")
    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, implementation=_FORBIDDEN_IMPL)
    state = L.LoopState(start_ts=time.monotonic())
    lay = _tmp_layout("synthint")
    T._quarantine_and_audit(
        d, coder, auditor, _G, lay, state, _planner(), write=False,
        contract=T._admit_env_contract(site_policy.OTHER),
    )
    out = render_rejections([], [], {}, None, diff_rejections=load_diff_rejections(lay))
    tail = out.split("syntax-contract")[-1]
    assert "構文契約違反" in tail
    assert "フレーム/hole 逸脱" not in tail[:400]


# ==== auditor gate (共有部品の軸引数配線のみ確認 — 本体は test_auditor_gate.py) ====

def test_quarantine_and_audit_dry_pass_when_clean_and_digest_matches(monkeypatch):
    monkeypatch.setattr(T, "_current_site", lambda: site_policy.PEGASUS_COMPUTE)
    d = _mk_template_dir()
    auditor = AuditorVerdict(verdict="pass", diff_digest=_digest_for(d))
    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, implementation=_CLEAN_IMPL)
    state = L.LoopState(start_ts=time.monotonic())
    gate = T._quarantine_and_audit(
        d, coder, auditor, _G, _tmp_layout("pass"), state,
        _planner(), write=False,
        contract=T._admit_env_contract(site_policy.PEGASUS_COMPUTE),
    )
    assert gate is None


def test_quarantine_and_audit_raises_on_digest_mismatch(monkeypatch):
    monkeypatch.setattr(T, "_current_site", lambda: site_policy.PEGASUS_COMPUTE)
    d = _mk_template_dir()
    auditor = AuditorVerdict(verdict="pass", diff_digest="0" * 64)
    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, implementation=_CLEAN_IMPL)
    state = L.LoopState(start_ts=time.monotonic())
    try:
        T._quarantine_and_audit(
            d, coder, auditor, _G, _tmp_layout("mm"), state,
            _planner(), write=False,
            contract=T._admit_env_contract(site_policy.PEGASUS_COMPUTE),
        )
        raise AssertionError("digest 不一致を素通しした")
    except AuditorGateFailure as e:
        assert "digest" in str(e)


def test_auditor_reject_carries_trigger_axis_identity(monkeypatch):
    monkeypatch.setattr(T, "_current_site", lambda: site_policy.OTHER)
    d = _mk_template_dir()
    auditor = AuditorVerdict(verdict="reject", diff_digest=_digest_for(d),
                             violations=[{"type": 16}])
    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, implementation=_CLEAN_IMPL)
    state = L.LoopState(start_ts=time.monotonic())
    lay = _tmp_layout("audrej")
    gate = T._quarantine_and_audit(
        d, coder, auditor, _G, lay, state, _planner(), write=False,
        contract=T._admit_env_contract(site_policy.OTHER),
    )
    assert gate["digest"]["subtype"] == "auditor-violation"
    assert gate["digest"]["template_diff_id"] == T.MARKER_ID
    assert gate["digest"]["diff_region"] == T.SOURCE_REL


# ==== load_proposal_file (schema 検証 — 共有 parse の配線) =======================

def _write_json(obj: dict, name: str) -> str:
    p = os.path.join(tempfile.mkdtemp(prefix="izanagi_s8atrigprop_"), name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return p


def test_load_proposal_file_roundtrip_and_fails_closed():
    base = {"planner": {"axis": T.MARKER_ID, "direction": "increase", "magnitude": "small"},
            "coder": {"axis": T.MARKER_ID, "implementation": _CLEAN_IMPL}}
    # auditor キー欠落 → KeyError (fails-closed)
    try:
        T.load_proposal_file(_write_json(base, "no_auditor.json"))
        raise AssertionError("auditor 欠落を素通しした")
    except KeyError:
        pass
    # 正常 roundtrip (coder に value フィールドは無い)
    ok = {**base, "auditor": {"verdict": "pass", "diff_digest": "a" * 64},
          "prior_critic_reverse": True}
    planner, coder, auditor, prior = T.load_proposal_file(_write_json(ok, "ok.json"))
    assert coder.implementation == _CLEAN_IMPL and not hasattr(coder, "value")
    assert auditor.verdict == "pass" and prior is True

    # uncertain は violations なし + 非空 uncertainty が必須 (共有 parser 境界)。
    bad_uncertain = {**base,
                     "auditor": {"verdict": "uncertain", "diff_digest": "b" * 64}}
    try:
        T.load_proposal_file(_write_json(bad_uncertain, "uncertain_without_reason.json"))
        raise AssertionError("根拠なし uncertain を素通しした")
    except T.AuditorGateFailure:
        pass


# ==== campaign 設定 =============================================================

def test_default_cfg_wires_s2_verify_and_axis():
    cfg = T.default_cfg()
    assert cfg.search_config.get(SEARCH_CONFIG_VERIFY_KEY) == VERIFY_LEGACY_PLUS_S2
    assert cfg.search_config.get("axis") == T.MARKER_ID
    assert cfg.ccbench_commit == T.PIN == "d706650"


def test_default_cfg_identity_distinct_from_sort():
    """spec_slug/search_tag/trial は sort から流用しない — campaign 出力の軸別分離
    (レビュー regression SF3 裁定)。"""
    cfg, scfg = T.default_cfg(), SORT.default_cfg()
    assert cfg.spec_slug != scfg.spec_slug
    assert cfg.search_tag != scfg.search_tag
    assert cfg.trial != scfg.trial


# ==== provenance 情報源記録 (E 段レビュー 2026-07-12 裁定の fails-closed 群) ======

def test_provenance_header_writes_sources_gate_record_and_firewall():
    lay = _tmp_layout("provhdr")
    T._write_provenance_header(lay)
    with open(T._provenance_path(lay), encoding="utf-8") as f:
        prov = json.load(f)
    assert prov["axis"] == T.MARKER_ID and prov["pin"] == T.PIN
    assert len(prov["information_sources"]) >= len(T.INFORMATION_SOURCES)
    assert any("不読" in s["role"] for s in prov["information_sources"])
    assert set(prov["gate_record"]) == {"basis", "approval", "firewall_scope"}
    assert prov["liveness_binary"] == "alive"
    assert prov["entries"] == {}
    # 偵察診断キーの否定 assert (リークレンズ SF1 裁定)
    assert not ({"effective_reasons", "floor_cv", "freq_source"} & set(prov))


def test_provenance_header_fails_closed_on_empty_sources(monkeypatch):
    monkeypatch.setattr(T, "INFORMATION_SOURCES", ())
    lay = _tmp_layout("provempty")
    try:
        T._write_provenance_header(lay)
        raise AssertionError("INFORMATION_SOURCES 空を素通しした")
    except ValueError as e:
        assert "情報源" in str(e)
    assert not os.path.exists(T._provenance_path(lay))


def test_provenance_header_unions_extra_sources_across_rewrites():
    """--extra-source の追記分は、extra 再指定なしの header 焼き直し (次 iteration 相当)
    でも消えない。07-12 (5) real 裁定の恒久修正 (回避策「毎回再指定」の廃止) の回帰テスト。"""
    lay = _tmp_layout("provunion")
    extra = {"path": "output/insights/some-review.md", "role": "grep 部分読み"}
    T._write_provenance_header(lay, extra_sources=(extra,))
    T._write_provenance_header(lay)  # 再指定なしの焼き直し
    with open(T._provenance_path(lay), encoding="utf-8") as f:
        prov = json.load(f)
    paths = [s["path"] for s in prov["information_sources"]]
    assert extra["path"] in paths, "動的追加分が焼き直しで消えた (上書き置換への退行)"
    assert paths.count(extra["path"]) == 1, "union の重複排除が壊れた"
    for src in T.INFORMATION_SOURCES:
        assert src["path"] in paths, "固定定数分が union から欠落した"
    assert len(paths) == len(set(paths)), "information_sources に重複 path がある"


def test_provenance_write_rejects_recon_diagnostic_keys():
    lay = _tmp_layout("provforbid")
    try:
        T._write_provenance(lay, {"axis": T.MARKER_ID, "effective_reasons": ["lc"]})
        raise AssertionError("偵察診断キーを素通しした")
    except ValueError as e:
        assert "effective_reasons" in str(e)


def test_provenance_entry_merge_preserves_existing_and_is_idempotent():
    lay = _tmp_layout("provmerge")
    T._write_provenance_header(lay)
    T._append_provenance_entry(lay, 1, {"outcome": "rejected", "variant": None,
                                        "proposal_path": "p1.json",
                                        "auditor_diff_digest": "a" * 64})
    # ヘッダ再書き (次 iteration 入口) で entries が truncate されない
    T._write_provenance_header(lay)
    # 同 iteration キーの上書き = 冪等 (再実行、regression SF2 裁定)
    T._append_provenance_entry(lay, 1, {"outcome": "duplicate", "variant": "v1",
                                        "proposal_path": "p1.json",
                                        "auditor_diff_digest": "a" * 64})
    T._append_provenance_entry(lay, 2, {"outcome": "certified", "variant": "v2",
                                        "proposal_path": "p2.json",
                                        "auditor_diff_digest": "b" * 64})
    with open(T._provenance_path(lay), encoding="utf-8") as f:
        prov = json.load(f)
    assert set(prov["entries"]) == {"1", "2"}
    assert prov["entries"]["1"]["outcome"] == "duplicate"
    assert prov["information_sources"]     # ヘッダも健在


def test_provenance_preserves_unknown_keys_forward_compat():
    """スキーマ進化した既存ファイルの未知キーを merge で捨てない (レビュー FC-3 裁定)。"""
    lay = _tmp_layout("provfwd")
    os.makedirs(os.path.dirname(T._provenance_path(lay)), exist_ok=True)
    with open(T._provenance_path(lay), "w", encoding="utf-8") as f:
        json.dump({"future_key": "keep-me", "entries": {"9": {"outcome": "certified"}}}, f)
    T._write_provenance_header(lay)
    with open(T._provenance_path(lay), encoding="utf-8") as f:
        prov = json.load(f)
    assert prov["future_key"] == "keep-me"
    assert prov["entries"]["9"]["outcome"] == "certified"


def test_provenance_corrupt_file_quarantined_and_raises():
    """decode 不能は .corrupt.* へ退避して例外停止 — silent reset (記録義務の黙殺) も
    そのまま brick も避ける (レビュー FC-3 × regression SF4 の折衷裁定)。"""
    lay = _tmp_layout("provcorrupt")
    path = T._provenance_path(lay)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write('{"truncated": ')
    try:
        T._load_provenance(lay)
        raise AssertionError("破損 JSON を素通しした")
    except RuntimeError as e:
        assert "破損" in str(e)
    assert not os.path.exists(path)
    corrupts = [n for n in os.listdir(os.path.dirname(path)) if ".corrupt." in n]
    assert len(corrupts) == 1


def test_parse_extra_source():
    assert T.parse_extra_source("docs/x.md:読了 — 追加参照") == {
        "path": "docs/x.md", "role": "読了 — 追加参照"}
    # ROLE 内コロン許容 (最初のコロンのみで分割、レビュー FC-6 裁定)
    assert T.parse_extra_source("a.md:role: with colon")["role"] == "role: with colon"
    for bad in ("no-colon", ":role-only", "path-only:", "  :  "):
        try:
            T.parse_extra_source(bad)
            raise AssertionError(f"malformed {bad!r} を素通しした")
        except ValueError:
            pass


# ==== drive_iteration (checkpoint 継続 + provenance funnel) =====================

def test_drive_iteration_stops_before_running_but_writes_header(monkeypatch):
    """入口停止でも provenance ヘッダは焼かれる (ヘッダは入口 = build 前、FC-1(a))。
    sub に不在パスを渡しても到達しないことが実行前停止の証拠。"""
    monkeypatch.setattr(T, "_current_site", lambda: site_policy.OTHER)
    lay = _tmp_layout("stopbefore")
    seed = L.LoopState(iteration=0, start_wall=time.time(),
                       reverse_recommendations=L.REVERSE_STREAK - 1)
    L.save_loop_state(lay, seed)
    cfg, perf = T.default_cfg(), T.default_perf()
    cd = T.CoderProposalTriggerGating(axis=T.MARKER_ID, implementation=_CLEAN_IMPL)
    au = AuditorVerdict(verdict="pass", diff_digest="a" * 64)
    out = T.drive_iteration(cfg, perf, _planner(), cd, au, prior_critic_reverse=True,
                            sub="/nonexistent/should/not/be/touched",
                            do_build=False, layout=lay)
    assert out["ran"] is False
    assert out["stop_reason"] == "reverse-exhausted"
    assert os.path.exists(T._provenance_path(lay))


def test_compute_no_resume_precedes_drive_entry_stop_and_provenance(monkeypatch):
    monkeypatch.setattr(T, "_current_site", lambda: site_policy.PEGASUS_COMPUTE)
    lay = _tmp_layout("compute-stop-before")
    seed = L.LoopState(
        iteration=0, start_wall=time.time(),
        reverse_recommendations=L.REVERSE_STREAK - 1,
    )
    L.save_loop_state(lay, seed)
    state_before = open(L.loop_state_path(lay), "rb").read()
    coder = T.CoderProposalTriggerGating(
        axis=T.MARKER_ID, implementation=_CLEAN_IMPL,
    )
    auditor = AuditorVerdict(verdict="pass", diff_digest="a" * 64)
    with pytest.raises(execution_guard.ExecutionGuardError, match="allow_resume=False"):
        T.drive_iteration(
            T.default_cfg(), T.default_perf(), _planner(), coder, auditor,
            prior_critic_reverse=True, sub="/must-not-run", do_build=False,
            layout=lay,
        )
    assert open(L.loop_state_path(lay), "rb").read() == state_before
    assert not os.path.exists(T._provenance_path(lay))
    assert wal.read_records(lay) == []


def _pinned_clean_sub_or_skip():
    import subprocess
    import pytest
    root = os.path.dirname(_ORCH)
    sub = os.path.join(root, "external", "ccbench")
    try:
        head = subprocess.check_output(["git", "-C", sub, "rev-parse", "--short", "HEAD"],
                                       text=True).strip()
        dirty = subprocess.check_output(["git", "-C", sub, "status", "--porcelain"],
                                        text=True).strip()
    except Exception:
        pytest.skip("submodule 未取得")
    if not head.startswith(T.PIN[:7]) or dirty:
        pytest.skip(f"submodule が pinned-clean でない (head={head} dirty={bool(dirty)}, "
                    f"要求 pin={T.PIN})")
    return sub


def test_drive_iteration_writes_entry_and_checkpoint(monkeypatch):
    """fresh reject 後も次候補の public funnel が identity を照合して resume する。"""
    import contextlib
    from campaign import patchharness

    monkeypatch.setattr(T, "_current_site", lambda: site_policy.OTHER)
    sub = _mk_template_dir()
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *_args, **_kwargs: contextlib.nullcontext(),
    )
    lay = _tmp_layout("driveprov")
    cfg, perf = T.default_cfg(), T.default_perf()
    bad = T.CoderProposalTriggerGating(axis=T.MARKER_ID,
                                       implementation="#define EVIL 1\n" + _CLEAN_IMPL)
    au = AuditorVerdict(verdict="pass", diff_digest="irrelevant-hole-escape-precedes-gate")
    out = T.drive_iteration(cfg, perf, _planner(), bad, au, None, sub, do_build=False,
                            layout=lay, proposal_path="/scratch/prop1.json")
    assert out["ran"] is True and out["outcome"] == "rejected" and out["iteration"] == 1
    assert wal.read_lock(lay) == ident.canonical_preimage(cfg)
    next_bad = T.CoderProposalTriggerGating(
        axis=T.MARKER_ID, implementation="#define EVIL_NEXT 1\n" + _CLEAN_IMPL,
    )
    resumed = T.drive_iteration(
        cfg, perf, _planner(), next_bad, au, None, sub, do_build=False,
        layout=lay, proposal_path="/scratch/prop2.json",
    )
    assert resumed["iteration"] == 2 and resumed["outcome"] == "rejected"
    with open(T._provenance_path(lay), encoding="utf-8") as f:
        prov = json.load(f)
    assert prov["entries"]["1"]["outcome"] == "rejected"
    assert prov["entries"]["1"]["proposal_path"] == "/scratch/prop1.json"
    assert prov["entries"]["2"]["proposal_path"] == "/scratch/prop2.json"
    st = L.load_loop_state(lay)
    assert st.iteration == 2 and [e.result for e in st.whiteboard] == [
        "rejected", "rejected",
    ]


def test_drive_iteration_entry_failure_blocks_checkpoint(monkeypatch):
    """provenance entry が書けない iteration は checkpoint を前進させない (FC-1(b) 裁定 —
    「WAL/checkpoint は進んだが記録なし」の中途半端を作らない)。"""
    import contextlib
    from campaign import patchharness

    monkeypatch.setattr(T, "_current_site", lambda: site_policy.OTHER)
    sub = _mk_template_dir()
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *_args, **_kwargs: contextlib.nullcontext(),
    )
    lay = _tmp_layout("provblock")
    cfg, perf = T.default_cfg(), T.default_perf()
    bad = T.CoderProposalTriggerGating(axis=T.MARKER_ID,
                                       implementation="#define EVIL 1\n" + _CLEAN_IMPL)
    au = AuditorVerdict(verdict="pass", diff_digest="irrelevant")

    def boom(layout, iteration, entry):
        raise OSError("simulated provenance write failure")
    monkeypatch.setattr(T, "_append_provenance_entry", boom)
    try:
        T.drive_iteration(cfg, perf, _planner(), bad, au, None, sub, do_build=False,
                          layout=lay)
        raise AssertionError("provenance 書き込み失敗を素通しした")
    except OSError:
        pass
    assert L.load_loop_state(lay) is None   # checkpoint は前進していない


if __name__ == "__main__":
    import pytest as _pytest
    raise SystemExit(_pytest.main([__file__, "-v"]))
