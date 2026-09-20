# -*- coding: utf-8 -*-
"""段 8a trigger-gating 自律ループ harness (p3_s4_loop_trigger_gating) の単体テスト。

`test_p3_s4_loop_sort.py` の型 (共有機構は再検証せず、正しい軸引数での呼び出しと
軸固有の新規機構だけを固める、axis-onboarding §7.4)。本軸固有 = 構文契約の禁止識別子
grep (subtype="syntax-contract") と provenance 情報源記録の受け皿 (E 段レビュー
2026-07-12 裁定の fails-closed 群)。build/verify/bench を伴わない機械部分のみ。
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
import os
import shutil
import sys
import tempfile
import time
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import env_contract, execution_guard, ident, p3_s4_loop as L  # noqa: E402
from orchestrator.campaign import p3_b4_closed_critic as B4_CLOSED                # noqa: E402
from orchestrator.campaign import p3_b4_launcher as B4_LAUNCHER                   # noqa: E402
from orchestrator.campaign import p3_s4_loop_sort as SORT                        # noqa: E402
from orchestrator.campaign import p3_s4_loop_trigger_gating as T                 # noqa: E402
from orchestrator.campaign import site_policy                                    # noqa: E402
from orchestrator.campaign import wal                                            # noqa: E402
from orchestrator.campaign.artifact_admission import (                           # noqa: E402
    ArtifactAdmissionError,
    CampaignReadPurpose,
    require_admitted_campaign,
)
from orchestrator.campaign.auditor_gate import (AuditorGateFailure, AuditorVerdict,  # noqa: E402
                                    auditor_reject_result,
                                    parse_auditor_dict)
from orchestrator.campaign.build_admission import (GeneratorId, add_coder_build_authority_argument,  # noqa: E402
                                      build_run_context)
from orchestrator.campaign.layout import CampaignLayout                          # noqa: E402
from orchestrator.campaign.model import CampaignConfig, Genome                  # noqa: E402
from orchestrator.campaign.pipeline import SEARCH_CONFIG_VERIFY_KEY               # noqa: E402
from orchestrator.campaign.pipeline import VERIFY_LEGACY_PLUS_S2                  # noqa: E402
from orchestrator.campaign.projection_guard import (                              # noqa: E402
    CODER_CONTRACT_IMPLEMENTATION,
    CODER_CONTRACT_TRIGGER_WIRE,
    assert_closed_proposal_schema,
)
from orchestrator.campaign.reflux_ir import (RefluxIRError, TriggerGateIR,        # noqa: E402
                                emit_predicate, encode_wire, parse_wire)
from orchestrator.campaign.trigger_gate_binding import (                          # noqa: E402
    SCHEMA_VERSION as TRIGGER_GATE_BINDING_SCHEMA,
    WAL_RECORD_STAGE as TRIGGER_GATE_BINDING_WAL_STAGE,
    TriggerGateBinding,
    expected_predicate_sha256,
)

_REAL_CONDITION_GATE = T._require_condition_gate


@pytest.fixture(autouse=True)
def _avoid_condition_compiler_work_in_mechanical_tests(monkeypatch):
    monkeypatch.setattr(T, "_require_condition_gate", lambda *_a, **_k: None)


def test_trigger_condition_gate_precedes_run_campaign():
    source = inspect.getsource(T._run_one_iteration_resolved)
    assert source.index("_require_condition_gate(") < source.index(
        "summary = run_campaign("
    )
    helper = inspect.getsource(_REAL_CONDITION_GATE)
    assert 'macro="BACKOFF_TRIGGER_GATING"' in helper
    assert 'use_class="certified-selection"' in helper
    assert '"condition_gate": condition_gate' in source


def test_drive_iteration_carries_only_non_none_holdout_admission_to_campaign():
    drive_parameter = inspect.signature(T.drive_iteration).parameters[
        "holdout_observation_admission"
    ]
    resolved_parameter = inspect.signature(
        T._run_one_iteration_resolved
    ).parameters["holdout_observation_admission"]
    for parameter in (drive_parameter, resolved_parameter):
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is None

    drive_source = inspect.getsource(T.drive_iteration)
    resolved_source = inspect.getsource(T._run_one_iteration_resolved)
    assert (
        'resolved_options["holdout_observation_admission"] = ('
        in drive_source
    )
    assert "**resolved_options" in drive_source
    assert (
        'campaign_options["holdout_observation_admission"] = ('
        in resolved_source
    )
    assert "**campaign_options" in resolved_source


def test_resolved_iteration_forwards_holdout_admission_object_identity(
    tmp_path, monkeypatch,
) -> None:
    import contextlib
    from orchestrator.campaign import patchharness

    layout = CampaignLayout(root=str(tmp_path / "campaign")).ensure()
    contract = env_contract.GENERATIONS["linux-baremetal"][0].contract
    admission = object()
    captured = []
    monkeypatch.setattr(
        patchharness,
        "applied",
        lambda *_args, **_kwargs: contextlib.nullcontext(),
    )
    monkeypatch.setattr(T, "_quarantine_and_audit", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        T.ident,
        "ensure_resumable_attempts",
        lambda *_args, **_kwargs: None,
    )

    def capture_campaign(*_args, **kwargs):
        captured.append(kwargs["holdout_observation_admission"])
        return SimpleNamespace(execution_receipt=None, results=[], skipped=0)

    monkeypatch.setattr(T, "run_campaign", capture_campaign)
    T._run_one_iteration_resolved(
        T.default_cfg(),
        T.default_perf(),
        _planner(),
        T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire="00000"),
        AuditorVerdict(verdict="pass", diff_digest="a" * 64),
        L.LoopState(start_wall=time.time()),
        str(tmp_path),
        True,
        layout,
        contract,
        site_policy.OTHER,
        build_context=_CODER_CONTEXT,
        holdout_observation_admission=admission,
    )
    assert captured == [admission]
from campaign_lock_test_support import build_v2_lock                # noqa: E402
from test_p3_b4_closed_critic import (                              # noqa: E402
    _production_launch_context as _verified_b4_context,
)


_B4_TEST_CONTEXT = B4_LAUNCHER.create_b4_launch_context_for_test(
    driver_kind="trigger"
)
def _b4_production_context(cfg, *, arm="on", site=None):
    return _verified_b4_context(
        cfg,
        driver_kind="trigger",
        arm=arm,
        trigger_site=site,
    )

_AUTHORITY_PARSER = argparse.ArgumentParser()
add_coder_build_authority_argument(_AUTHORITY_PARSER)
_CODER_CONTEXT = build_run_context(
    generator_id=GeneratorId.S8A_TRIGGER_SWEEP,
    coder_authority=_AUTHORITY_PARSER.parse_args(
        ["--allow-coder-derived-build"]
    ).coder_build_authority,
)

# 実 transaction.cc の EVOLVE-BLOCK 骨格 (trigger-gating marker) を写した fixture。
# silo-backoff-trigger-gating-variant.patch と同型 — hole は #if 枝の述語代入 1 行、
# gate 変数宣言と gated call は marker 外 (coder 不可触)。
_TEMPLATE = """#include "../../include/backoff.hh"

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
_CLEAN_WIRE = "10100"
_CLEAN_IMPL = emit_predicate(parse_wire(_CLEAN_WIRE))
_FORBIDDEN_IMPL = "  izanagi_gate_pass = (thid_ % 2 == 0);"
_PRE_T343_OTHER_CAMPAIGN_ID = (
    "p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5"
)
_PRE_T343_COMPUTE_CAMPAIGN_ID = (
    "p3-s8a-trigger-loop-s8a-trigger-autonomous-75727902"
)
_T343_OTHER_CAMPAIGN_ID = (
    "p3-s8a-trigger-loop-s8a-trigger-autonomous-ccba936e"
)
_T343_COMPUTE_CAMPAIGN_ID = (
    "p3-s8a-trigger-loop-s8a-trigger-autonomous-9a92049d"
)
_T816_OTHER_CAMPAIGN_ID = (
    "p3-s8a-trigger-loop-s8a-trigger-autonomous-03045c77"
)
_T816_COMPUTE_CAMPAIGN_ID = (
    "p3-s8a-trigger-loop-s8a-trigger-autonomous-0f292633"
)
_T530_OTHER_CAMPAIGN_ID = (
    "p3-s8a-trigger-loop-s8a-trigger-autonomous-25c37015"
)
_T530_COMPUTE_CAMPAIGN_ID = (
    "p3-s8a-trigger-loop-s8a-trigger-autonomous-6c3e7a27"
)


def _critic_view(layout: CampaignLayout):
    cfg = T._campaign_cfg_for_site(T.default_cfg(), site_policy.OTHER)
    wal.write_lock(layout, build_v2_lock(ident.canonical_preimage(cfg)))
    return require_admitted_campaign(
        layout, purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    )


def _mk_template_dir() -> str:
    d = tempfile.mkdtemp(prefix="izanagi_s8atrigloop_")
    full = os.path.join(d, _SRC_REL)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(_TEMPLATE)
    return d


def _install_condition_gate_build_fixture(source_root: str) -> None:
    """Add a real CMake owner-TU graph around the trigger source fixture."""
    root = Path(source_root)
    (root / "cmake").mkdir(parents=True)
    (root / "cc" / "silo").mkdir(parents=True, exist_ok=True)
    (root / "include").mkdir(parents=True, exist_ok=True)
    (root / "CMakeLists.txt").write_text(
        """cmake_minimum_required(VERSION 3.16)
project(trigger_condition_gate_fixture LANGUAGES CXX)
include(cmake/Options.cmake)
ccbench_universal_definitions(condition_gate_defines)
add_executable(ycsb_silo.exe cc/silo/transaction.cc)
target_compile_definitions(ycsb_silo.exe PRIVATE ${condition_gate_defines})
""",
        encoding="utf-8",
    )
    (root / "cmake" / "Options.cmake").write_text(
        """set(CCBENCH_BACKOFF_TRIGGER_GATING 0 CACHE STRING "trigger gate")
function(ccbench_universal_definitions out_var)
  set(${out_var}
    BACKOFF_TRIGGER_GATING=${CCBENCH_BACKOFF_TRIGGER_GATING}
    PARENT_SCOPE)
endfunction()
""",
        encoding="utf-8",
    )
    (root / "include" / "backoff.hh").write_text(
        "// condition gate preprocessing fixture\n",
        encoding="utf-8",
    )


def _tmp_layout(
        tag: str, *, cfg: CampaignConfig | None = None,
) -> CampaignLayout:
    # Runtime contract authority is outside campaign identity (R2(a)).
    cfg = T.default_cfg() if cfg is None else cfg
    parent = tempfile.mkdtemp(prefix=f"izanagi_s8atrigloop_{tag}_")
    return CampaignLayout(
        root=os.path.join(parent, str(ident.campaign_id(cfg)))
    ).ensure()


def _planner() -> "L.PlannerProposal":
    return L.PlannerProposal(axis=T.MARKER_ID, direction="explore_both", magnitude="small")


def _digest_for(d: str, wire: str = _CLEAN_WIRE) -> str:
    predicate = emit_predicate(parse_wire(wire))
    _res, _b, _e, working_diff = L.quarantine(d, predicate, marker_id=T.MARKER_ID,
                                              source_rel=_SRC_REL, write=False)
    from orchestrator.campaign.auditor_gate import compute_diff_digest
    return compute_diff_digest(working_diff)


def _binding(wire: str = _CLEAN_WIRE) -> TriggerGateBinding:
    ir = parse_wire(wire)
    return TriggerGateBinding(
        ir.mask, expected_predicate_sha256(ir.mask), "a" * 64, source=None,
    )


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
    calibration_ref = (
        env_contract.GENERATIONS["linux-baremetal"][0].contract.calibration_ref
    )
    return env_contract.ExecutionEnvironmentContract(
        env_tag="sentinel-env",
        clocks_per_us=4242,
        numactl=numactl,
        attestation_mode="none",
        isolation_policy=env_contract.IsolationPolicy(
            single_process=False, allow_resume=True,
        ),
        calibration_ref=calibration_ref,
    )


def _measurement_case(
    monkeypatch, *, site, lookup, order=None, dependency_prefix="", receipt=None,
    build_context=_CODER_CONTEXT,
):
    """clean proposal を run_campaign 直前まで進める一時 layout の case。"""
    import contextlib
    from orchestrator.campaign import patchharness

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
        assert kwargs.get("build_context") is _CODER_CONTEXT
        binding = kwargs.get("trigger_gate_binding")
        assert type(binding) is TriggerGateBinding
        assert binding.source is None
        calls.append({
            "campaign_id": str(ident.campaign_id(cfg)),
            "env_tag": env_tag,
            "clocks_per_us": clocks_per_us,
            "numactl": numactl,
            "env_contract": kwargs.get("env_contract"),
            "dependency_prefix": kwargs.get("dependency_prefix"),
            "declared_use_class": kwargs.get("declared_use_class"),
        })
        return SimpleNamespace(
            results=[], skipped=0, execution_receipt=receipt,
            campaign_id=str(ident.campaign_id(cfg)), layout_root=lay.root,
        )

    monkeypatch.setattr(T, "run_campaign", run_spy)
    state = L.LoopState(start_ts=time.monotonic())
    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=_CLEAN_WIRE)
    auditor = AuditorVerdict(verdict="pass", diff_digest=_digest_for(sub))

    def invoke():
        return T.run_one_iteration(
            T.default_cfg(), T.default_perf(), _planner(), coder, auditor, state,
            sub, do_build=True, log=lambda *_args: None,
            build_context=build_context,
            dependency_prefix=dependency_prefix,
        )

    return invoke, lay, calls


def _reject_case(monkeypatch, *, site, wire=_CLEAN_WIRE,
                 lookup=env_contract.lookup):
    """正準 wire の auditor reject を sink まで進める一時 layout の case。"""
    import contextlib
    from orchestrator.campaign import patchharness

    sub = _mk_template_dir()
    lay = _tmp_layout("reject")
    monkeypatch.setattr(T, "_current_site", lambda: site)
    monkeypatch.setattr(T, "_lookup", lookup)
    monkeypatch.setattr(T, "exploration_campaign_layout", lambda _id: lay)
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *_args, **_kwargs: contextlib.nullcontext(),
    )
    original_record_diff_reject = L.record_diff_reject

    def record_diff_reject_spy(*args, **kwargs):
        binding = kwargs.get("trigger_gate_binding")
        assert type(binding) is TriggerGateBinding
        assert binding.source is None
        return original_record_diff_reject(*args, **kwargs)

    monkeypatch.setattr(L, "record_diff_reject", record_diff_reject_spy)
    state = L.LoopState(start_ts=time.monotonic())
    auditor = AuditorVerdict(
        verdict="reject", diff_digest=_digest_for(sub, wire),
        violations=[{"type": 16}],
    )
    coder = T.CoderProposalTriggerGating(
        axis=T.MARKER_ID, wire=wire,
    )

    def invoke():
        return T.run_one_iteration(
            T.default_cfg(), T.default_perf(), _planner(), coder, auditor, state,
            sub, do_build=False, layout=lay, log=lambda *_args: None,
        )

    return invoke, lay


# ==== WAL binding commitment diagnostics =======================================

def test_wal_binding_missing_build_start_exposes_abort_context():
    reason = "eval-exception: ValueError: required numactl prefix is empty"
    records = {
        "verify_done": {"verdict": "reject"},
        "abort": {
            "reason": reason,
            "error": "fixture stderr",
            "build_attempt_id": "attempt-fixture",
        },
    }

    with pytest.raises(T.WalBuildStartEvidenceMissingError) as exc_info:
        T._wal_binding_commitment(records, variant="variant-fixture")

    exc = exc_info.value
    assert reason in str(exc)
    assert "fixture stderr" in str(exc)
    assert "attempt-fixture" in str(exc)
    assert "variant-fixture" in str(exc)
    assert "stages=['abort', 'verify_done']" in str(exc)
    assert exc.variant == "variant-fixture"
    assert exc.failure_reason == "build_start_missing"
    assert exc.available_stages == ("abort", "verify_done")
    assert exc.stages == exc.available_stages
    assert exc.abort_record_present is True
    assert exc.abort_details == {
        "reason": reason,
        "error": "fixture stderr",
        "build_attempt_id": "attempt-fixture",
    }
    assert exc.abort_reason == reason
    assert exc.abort_error == "fixture stderr"
    assert exc.abort_build_attempt_id == "attempt-fixture"


@pytest.mark.parametrize(
    ("records", "expected_stages"),
    [
        pytest.param({}, (), id="empty-records"),
        pytest.param(
            {"verify_done": {"verdict": "reject"}},
            ("verify_done",),
            id="nonempty-without-abort",
        ),
    ],
)
def test_wal_binding_missing_build_start_without_abort_is_structured(
        records, expected_stages):
    with pytest.raises(T.WalBuildStartEvidenceMissingError) as exc_info:
        T._wal_binding_commitment(records, variant="variant-fixture")

    exc = exc_info.value
    assert exc.failure_reason == "build_start_missing"
    assert exc.available_stages == expected_stages
    assert exc.abort_record_present is False
    assert exc.abort_details == {}
    assert "abort レコードなし" in str(exc)


def test_wal_binding_missing_commitment_is_distinct_structured_error():
    # helper の局所契約を固定する。実 WAL 経路では先に AttemptTopologyError になる。
    records = {"build_start": {"build_attempt_id": "attempt-fixture"}}

    with pytest.raises(T.WalBuildStartEvidenceMissingError) as exc_info:
        T._wal_binding_commitment(records, variant="variant-fixture")

    exc = exc_info.value
    assert exc.failure_reason == "binding_commitment_missing"
    assert "binding_commitment_missing" in str(exc)
    assert exc.available_stages == ("build_start",)
    assert exc.abort_record_present is False
    assert exc.abort_details == {}
    assert "abort レコードなし" in str(exc)


def test_wal_binding_commitment_success_is_unchanged():
    expected = "a" * 64
    records = {
        "build_start": {wal.TRIGGER_BINDING_COMMITMENT_KEY: expected},
    }

    assert T._wal_binding_commitment(
        records, variant="variant-fixture",
    ) == expected


@pytest.mark.parametrize("path", ["duplicate", "normal"])
@pytest.mark.usefixtures("ratified_enforcement_source")
def test_missing_build_start_propagates_from_both_iteration_paths(
        monkeypatch, path):
    expected_variant = f"variant-{path}"
    reason = f"eval-exception: fixture {path} failure"
    records = {"abort": {"reason": reason}}
    records_by_stage_calls = []
    invoke, _lay, _calls = _measurement_case(
        monkeypatch, site=site_policy.OTHER, lookup=env_contract.lookup,
    )
    if path == "duplicate":
        monkeypatch.setattr(
            T, "run_campaign",
            lambda *_args, **_kwargs: SimpleNamespace(
                results=[], skipped=1, execution_receipt=None,
            ),
        )
        monkeypatch.setattr(
            T, "_resolve_duplicate",
            lambda *_args, **_kwargs: {
                "outcome": "aborted", "variant": expected_variant,
                "records": records,
            },
        )
    else:
        monkeypatch.setattr(
            T, "run_campaign",
            lambda *_args, **_kwargs: SimpleNamespace(
                results=[SimpleNamespace(
                    variant=expected_variant,
                    certified=False,
                    aborted=True,
                    verdict="reject",
                    fitness_tps=0.0,
                )],
                skipped=0, execution_receipt=None,
            ),
        )

        def records_by_stage_spy(layout_arg, variant_arg):
            records_by_stage_calls.append((layout_arg, variant_arg))
            return records

        monkeypatch.setattr(
            wal, "records_by_stage", records_by_stage_spy,
        )

    with pytest.raises(T.WalBuildStartEvidenceMissingError) as exc_info:
        invoke()

    assert exc_info.value.variant == expected_variant
    assert exc_info.value.abort_reason == reason
    if path == "normal":
        assert len(records_by_stage_calls) == 1
        layout_arg, variant_arg = records_by_stage_calls[0]
        assert layout_arg is not None
        assert variant_arg == expected_variant


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


def test_recorded_pegasus_hostname_reaches_measurement_site_admission():
    # calibration-753f535a8d024727.json の host.node を独立 literal で replay する。
    classified_site = site_policy.classify_site("bnode011", {}, True)
    assert classified_site == "PEGASUS_COMPUTE"
    assert T._site_admits_measurement(classified_site) is True


def test_recorded_compute_site_and_opt_in_pass_build_site_admission(monkeypatch):
    from orchestrator.campaign import p3_autonomous_workload_trial as trial

    # calibration-753f535a8d024727.json の host.node を独立 literal で replay する。
    classified_site = site_policy.classify_site("bnode011", {}, True)
    assert classified_site == "PEGASUS_COMPUTE"
    monkeypatch.setattr(trial.trigger, "_current_site", lambda: classified_site)

    trial._assert_build_site_opted_in(
        True, allow_pegasus_compute_transport=True,
    )
    with pytest.raises(trial.AutonomousTrialError, match="明示 transport opt-in"):
        trial._assert_build_site_opted_in(
            True, allow_pegasus_compute_transport=False,
        )


def test_environment_module_surface_and_default_seams():
    assert T.ENV_TAG == "linux-baremetal"
    assert not hasattr(T, "CLK")
    assert not hasattr(T, "NUMA")
    assert T._current_site is site_policy.current_site
    assert T._lookup is env_contract.lookup
    assert "environment_contract_sha256" not in T.default_cfg().search_config
    assert "site" not in inspect.signature(T.run_one_iteration).parameters
    assert "site" not in inspect.signature(T.drive_iteration).parameters


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_contract_sentinel_flows_to_run_campaign(
        monkeypatch, tmp_path, _activate_synthetic_env_authority):
    contract = _sentinel_contract()
    _activate_synthetic_env_authority(
        contract, repo_root=ROOT, authority_dir=tmp_path / "authority",
    )
    looked_up = []

    def lookup(env_tag):
        looked_up.append(env_tag)
        return contract

    invoke, lay, calls = _measurement_case(
        monkeypatch, site=site_policy.OTHER, lookup=lookup,
    )
    invoke()
    assert looked_up == [T.ENV_TAG]
    expected_cfg = T._campaign_cfg_for_site(
        T.default_cfg(), site_policy.OTHER, _contract=contract,
    )
    assert calls == [{
        "campaign_id": str(ident.campaign_id(expected_cfg)),
        "env_tag": contract.env_tag,
        "clocks_per_us": contract.clocks_per_us,
        "numactl": list(contract.numactl),
        "env_contract": None,
        "dependency_prefix": None,
        "declared_use_class": "exploration",
    }]


@pytest.mark.usefixtures("ratified_enforcement_source")
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
    expected_cfg = T._campaign_cfg_for_site(
        T.default_cfg(), site_policy.OTHER, _contract=contract,
    )
    assert calls == [{
        "campaign_id": str(ident.campaign_id(expected_cfg)),
        "env_tag": T.ENV_TAG,
        "clocks_per_us": contract.clocks_per_us,
        "numactl": list(contract.numactl),
        "env_contract": None,
        "dependency_prefix": None,
        "declared_use_class": "exploration",
    }]


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_empty_numactl_contract_flows_as_empty_list(
        monkeypatch, tmp_path, _activate_synthetic_env_authority):
    contract = _sentinel_contract(numactl=())
    _activate_synthetic_env_authority(
        contract, repo_root=ROOT, authority_dir=tmp_path / "authority",
    )
    invoke, _lay, calls = _measurement_case(
        monkeypatch, site=site_policy.OTHER, lookup=lambda _env_tag: contract,
    )
    invoke()
    assert calls[0]["numactl"] == []


def test_campaign_identity_is_unchanged_for_other_and_split_for_compute():
    linux_contract = env_contract.GENERATIONS["linux-baremetal"][0].contract
    pegasus_contract = env_contract.GENERATIONS["pegasus"][0].contract
    saved_lookup = T.env_contract.lookup
    saved_site_lookup = T._lookup
    T.env_contract.lookup = lambda env_tag: {
        "linux-baremetal": linux_contract,
        "pegasus": pegasus_contract,
    }[env_tag]
    T._lookup = T.env_contract.lookup
    try:
        unbound = T.default_cfg()
        cfg = T._campaign_cfg_for_site(
            unbound, site_policy.OTHER, _contract=linux_contract,
        )
        other_cfg = T._campaign_cfg_for_site(
            cfg, site_policy.OTHER, _contract=linux_contract,
        )
        compute_cfg = T._campaign_cfg_for_site(
            unbound, site_policy.PEGASUS_COMPUTE,
            _contract=pegasus_contract,
        )
    finally:
        T.env_contract.lookup = saved_lookup
        T._lookup = saved_site_lookup
    assert other_cfg is cfg
    assert str(ident.campaign_id(other_cfg)) == str(ident.campaign_id(cfg))
    assert str(ident.campaign_id(other_cfg)) == _T816_OTHER_CAMPAIGN_ID
    assert str(ident.campaign_id(compute_cfg)) == _T816_COMPUTE_CAMPAIGN_ID
    assert str(ident.campaign_id(other_cfg)) not in {
        _T343_OTHER_CAMPAIGN_ID,
        _T530_OTHER_CAMPAIGN_ID,
    }
    assert str(ident.campaign_id(compute_cfg)) not in {
        _T343_COMPUTE_CAMPAIGN_ID,
        _T530_COMPUTE_CAMPAIGN_ID,
    }
    t816_compute = replace(
        unbound,
        search_config={
            **unbound.search_config,
            T._CAMPAIGN_ENV_KEY: T._SITE_ENV_TAGS[site_policy.PEGASUS_COMPUTE],
        },
    )
    t816_compute_hash = hashlib.sha256(
        ident.canonical_preimage(t816_compute).encode("utf-8")
    ).hexdigest()[:8]
    assert (
        f"{t816_compute.spec_slug}-{t816_compute.search_tag}-{t816_compute_hash}"
        == _T816_COMPUTE_CAMPAIGN_ID
    )
    assert _PRE_T343_OTHER_CAMPAIGN_ID == (
        "p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5"
    )
    assert _PRE_T343_COMPUTE_CAMPAIGN_ID == (
        "p3-s8a-trigger-loop-s8a-trigger-autonomous-75727902"
    )
    assert compute_cfg.search_config["measurement_env"] == "pegasus"
    assert "measurement_env" not in cfg.search_config


def test_campaign_site_projection_rejects_conflicting_prebound_contract():
    linux_contract = env_contract.GENERATIONS["linux-baremetal"][0].contract
    pegasus_contract = env_contract.GENERATIONS["pegasus"][0].contract
    cfg = T._campaign_cfg_for_site(
        T.default_cfg(), site_policy.OTHER, _contract=linux_contract,
    )
    before = dict(cfg.search_config)
    with pytest.raises(ValueError, match="environment contract"):
        T._campaign_cfg_for_site(
            cfg, site_policy.PEGASUS_COMPUTE, _contract=pegasus_contract,
        )
    assert cfg.search_config == before


def test_injected_layout_must_match_final_campaign_id(monkeypatch):
    contract = env_contract.GENERATIONS["linux-baremetal"][0].contract
    monkeypatch.setattr(T, "_current_site", lambda: site_policy.OTHER)
    monkeypatch.setattr(T, "_lookup", lambda _env_tag: contract)
    # Contract H no longer changes campaign-id, so mismatch on the retained records axis.
    mismatched_cfg = replace(
        T.default_cfg(),
        search_config={**T.default_cfg().search_config, "records": 100_001},
    )
    with pytest.raises(ValueError, match="layout 注入"):
        T.run_one_iteration(
            T.default_cfg(), T.default_perf(), _planner(),
            T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=_CLEAN_WIRE),
            AuditorVerdict(verdict="pass", diff_digest="a" * 64),
            L.LoopState(start_ts=time.monotonic()),
            "/must-not-be-read", do_build=False,
            layout=_tmp_layout("identity-mismatch", cfg=mismatched_cfg),
        )


def test_fixture_cli_uses_authoritative_layout_and_preserves_legacy_bytes(
    tmp_path, monkeypatch,
):
    import contextlib
    from orchestrator.campaign import patchharness

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

    def fake_drive(*_args, **_kwargs):
        state = L.LoopState(iteration=1, start_wall=time.time())
        L.project_whiteboard(state, _planner(), "fail")
        L.save_loop_state(compute, state)
        T._write_provenance_header(compute)
        with open(os.path.join(compute.root, T.DIGEST_BASENAME), "w",
                  encoding="utf-8") as stream:
            stream.write("compute-only\n")
        return {
            "outcome": "aborted", "variant": None,
            "campaign_id": _T530_COMPUTE_CAMPAIGN_ID,
            "layout_root": compute.root,
        }

    def critic_digest_spy(
        view, tag="p3-s4", reflux=True, *, identity_projection,
    ):
        assert view is not None
        assert isinstance(tag, str)
        assert isinstance(reflux, bool)
        assert identity_projection is not None
        return "compute-only\n"

    monkeypatch.setattr(T, "drive_iteration", fake_drive)
    monkeypatch.setattr(L, "make_critic_digest", critic_digest_spy)
    monkeypatch.setattr(
        T, "exploration_campaign_layout",
        lambda campaign_id: (
            CampaignLayout(compute.root)
            if campaign_id == _T530_COMPUTE_CAMPAIGN_ID
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


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_fixture_no_build_cli_fresh_layout_uses_provenance_without_digest_mock(
    tmp_path, monkeypatch,
):
    import contextlib
    from orchestrator.campaign import patchharness

    root = tmp_path / "repo"
    fixed_sub = root / "external" / "ccbench"
    source = fixed_sub / T.SOURCE_REL
    source.parent.mkdir(parents=True)
    source.write_text(_TEMPLATE, encoding="utf-8")
    output_root = tmp_path / "fresh-layouts"
    monkeypatch.setattr(T, "_repo_root", lambda: str(root))
    monkeypatch.setattr(T, "_current_site", lambda: site_policy.OTHER)
    monkeypatch.setattr(patchharness, "assert_pinned_clean", lambda *_a, **_k: None)
    monkeypatch.setattr(
        patchharness, "applied", lambda *_a, **_k: contextlib.nullcontext(),
    )
    monkeypatch.setattr(
        T, "exploration_campaign_layout",
        lambda campaign_id: CampaignLayout(str(output_root / campaign_id)),
    )

    assert T.main(["--no-build", "--no-isolate-worktree"]) == 0
    campaign_id = str(ident.campaign_id(T._campaign_cfg_for_site(
        T.default_cfg(), site_policy.OTHER,
    )))
    layout = CampaignLayout(str(output_root / campaign_id))
    assert os.path.exists(T._provenance_path(layout))
    assert os.path.exists(L.loop_state_path(layout))
    assert not os.path.exists(os.path.join(layout.root, T.DIGEST_BASENAME))


@pytest.mark.usefixtures("ratified_enforcement_source")
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


@pytest.mark.usefixtures("ratified_enforcement_source")
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


def test_compute_measurement_sink_requires_build_context_before_campaign(monkeypatch):
    contract = env_contract.lookup("pegasus")
    invoke, lay, calls = _measurement_case(
        monkeypatch, site=site_policy.PEGASUS_COMPUTE,
        lookup=lambda _tag: contract, build_context=None,
    )
    with pytest.raises(TypeError, match="build_context"):
        invoke()
    assert calls == []
    assert wal.read_records(lay) == []


def test_compute_existing_loop_state_rejected_after_neutralized_freshness(monkeypatch):
    from orchestrator.campaign import p3_autonomous_workload_trial as autonomous

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


@pytest.mark.parametrize("wire", ["00000", "10100", "11111"])
def test_compute_no_resume_precedes_all_reject_writes(monkeypatch, wire):
    invoke, lay = _reject_case(
        monkeypatch, site=site_policy.PEGASUS_COMPUTE,
        wire=wire,
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
        monkeypatch, site=site_policy.PEGASUS_COMPUTE, wire="10000",
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


@pytest.mark.usefixtures("ratified_enforcement_source")
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
    other = T._campaign_cfg_for_site(
        T.default_cfg(), site_policy.OTHER,
        _contract=env_contract.GENERATIONS["linux-baremetal"][0].contract,
    )
    assert calls[0]["campaign_id"] != str(ident.campaign_id(other))
    assert wal.read_records(lay) == []


@pytest.mark.parametrize("wire", ["00000", "10100", "11111"])
@pytest.mark.usefixtures("ratified_enforcement_source")
def test_reject_sink_compute_records_pegasus_without_attestation(monkeypatch, wire):
    invoke, lay = _reject_case(
        monkeypatch, site=site_policy.PEGASUS_COMPUTE,
        wire=wire, lookup=env_contract.lookup,
    )
    out = invoke()
    assert out["outcome"] == "rejected"
    assert {record.env_tag for record in wal.read_records(lay)} == {"pegasus"}


@pytest.mark.parametrize("wire", ["00000", "10100", "11111"])
def test_reject_sink_refuses_login_without_wal(monkeypatch, wire):
    invoke, lay = _reject_case(
        monkeypatch, site=site_policy.PEGASUS_LOGIN,
        wire=wire,
        lookup=lambda _env_tag: pytest.fail("拒否 site で contract lookup へ到達した"),
    )
    with pytest.raises(execution_guard.ExecutionGuardError):
        invoke()
    assert wal.read_records(lay) == []


@pytest.mark.usefixtures("ratified_enforcement_source")
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
    assert [record.stage for record in records] == [
        TRIGGER_GATE_BINDING_WAL_STAGE, "build_start", "abort",
    ]
    assert [record.env_tag for record in records] == [contract.env_tag] * 3


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


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_fresh_default_seams_flow_distinct_contract_to_measurement_sink(
        monkeypatch, tmp_path, _activate_synthetic_env_authority):
    """R16 measurement 実経路。import 後の module 再束縛や動的 reflection は保証外。"""
    import contextlib
    from orchestrator.campaign import patchharness

    contract = _sentinel_contract()
    _activate_synthetic_env_authority(
        contract, repo_root=ROOT, authority_dir=tmp_path / "authority",
    )
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
    _install_condition_gate_build_fixture(sub)
    real_cxx = next(
        (path for candidate in ("g++-13", "g++-12", "g++")
         if (path := shutil.which(candidate)) is not None),
        None,
    )
    if real_cxx is None or shutil.which("cmake") is None:
        pytest.skip("condition gate fixture requires a real C++ compiler and CMake")
    monkeypatch.setattr(fresh.buildcache, "DEFAULT_CXX", real_cxx)
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
        assert kwargs.get("build_context") is _CODER_CONTEXT
        calls.append({
            "env_tag": env_tag,
            "clocks_per_us": clocks_per_us,
            "numactl": numactl,
            "declared_use_class": kwargs.get("declared_use_class"),
        })
        return SimpleNamespace(results=[], skipped=0)

    monkeypatch.setattr(fresh, "run_campaign", run_spy)
    coder = fresh.CoderProposalTriggerGating(
        axis=fresh.MARKER_ID, wire=_CLEAN_WIRE,
    )
    auditor = AuditorVerdict(verdict="pass", diff_digest=_digest_for(sub))
    fresh.run_one_iteration(
        fresh.default_cfg(), fresh.default_perf(), _planner(), coder, auditor,
        L.LoopState(start_ts=time.monotonic()), sub, do_build=True,
        log=lambda *_args: None, build_context=_CODER_CONTEXT,
    )

    assert fresh._current_site is current_site
    assert fresh._lookup is lookup
    assert looked_up == [fresh.ENV_TAG]
    assert calls == [{
        "env_tag": contract.env_tag,
        "clocks_per_us": contract.clocks_per_us,
        "numactl": list(contract.numactl),
        "declared_use_class": "exploration",
    }]


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_fresh_default_seams_flow_distinct_contract_to_reject_sink(monkeypatch):
    """R16 reject 実経路。import 後の module 再束縛や動的 reflection は保証外。"""
    import contextlib
    from orchestrator.campaign import patchharness

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
        fresh, "exploration_campaign_layout", lambda _campaign_id: lay,
    )
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *_args, **_kwargs: contextlib.nullcontext(),
    )
    coder = fresh.CoderProposalTriggerGating(
        axis=fresh.MARKER_ID, wire=_CLEAN_WIRE,
    )
    auditor = AuditorVerdict(
        verdict="reject", diff_digest=_digest_for(sub),
        violations=[{"type": 16}],
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
    assert [record.stage for record in records] == [
        TRIGGER_GATE_BINDING_WAL_STAGE, "build_start", "abort",
    ]
    assert [record.env_tag for record in records] == [contract.env_tag] * 3


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_clean_dry_pass_still_admitted_on_pegasus(monkeypatch):
    import contextlib
    from orchestrator.campaign import patchharness

    sub = _mk_template_dir()
    lay = _tmp_layout("dry-pass-pegasus")
    lookup_calls = 0
    contract = _sentinel_contract()

    def lookup(_env_tag):
        nonlocal lookup_calls
        lookup_calls += 1
        return contract

    site_calls = 0

    def current_site():
        nonlocal site_calls
        site_calls += 1
        return site_policy.PEGASUS_COMPUTE

    monkeypatch.setattr(T, "_current_site", current_site)
    monkeypatch.setattr(T, "_lookup", lookup)
    monkeypatch.setattr(T, "exploration_campaign_layout", lambda _id: lay)
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *_args, **_kwargs: contextlib.nullcontext(),
    )
    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=_CLEAN_WIRE)
    auditor = AuditorVerdict(verdict="pass", diff_digest=_digest_for(sub))
    expected_cfg = T._campaign_cfg_for_site(
        T.default_cfg(), site_policy.PEGASUS_COMPUTE, _contract=contract,
    )
    out = T.run_one_iteration(
        T.default_cfg(), T.default_perf(), _planner(), coder, auditor,
        L.LoopState(start_ts=time.monotonic()), sub, do_build=False, layout=lay,
        log=lambda *_args: None,
    )
    assert out["outcome"] == "dry-pass" and out["variant"] is None
    assert out["campaign_id"] == str(ident.campaign_id(expected_cfg))
    assert out["layout_root"] == lay.root
    assert len(out["trigger_gate_binding_commitment"]) == 64
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
        "from . import p3_s4_loop as L                              "
        "# noqa: E402\n"
    )
    m22 = _replace_once(
        source,
        legacy_import,
        legacy_import + "from orchestrator.campaign.p3_s4_loop import CLK as LEGACY_CLK\n",
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


# ==== trusted emitter の内部 drift assertion ==================================

def test_check_syntax_contract_is_not_a_candidate_acceptance_gate():
    assert all(
        T.check_syntax_contract(emit_predicate(TriggerGateIR(mask))) == []
        for mask in range(32)
    )
    assert T.check_syntax_contract(_FORBIDDEN_IMPL) == ["thid_"]


def test_quarantine_and_audit_stops_on_internal_syntax_drift(monkeypatch):
    d = _mk_template_dir()
    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=_CLEAN_WIRE)
    monkeypatch.setattr(T, "check_syntax_contract", lambda _predicate: ["drift"])
    with pytest.raises(
        RuntimeError,
        match="^canonical trigger predicate violates syntax contract$",
    ) as excinfo:
        T._quarantine_and_audit(
            d, coder, AuditorVerdict(verdict="pass", diff_digest="unused"),
            _G, _tmp_layout("syntax-drift"),
            L.LoopState(start_ts=time.monotonic()), _planner(), write=False,
            contract=T._admit_env_contract(site_policy.OTHER),
            binding=_binding(),
        )
    assert _CLEAN_WIRE not in str(excinfo.value)


def test_wire_bit_order_is_gateable_reason_order_lsb_first():
    members = (
        "kLockConflict", "kUpdateAbsent", "kReadValiTid",
        "kReadValiLocked", "kNodeVali",
    )
    for bit, member in enumerate(members):
        wire = "".join("1" if index == bit else "0" for index in range(5))
        ir = parse_wire(wire)
        assert ir.mask == 1 << bit
        assert encode_wire(ir) == wire
        predicate = emit_predicate(ir)
        assert f"IzanagiAbortReason::{member}" in predicate
        for other in members:
            assert (f"IzanagiAbortReason::{other}" in predicate) == (other == member)


def test_all_32_wires_materialize_byte_exact_frozen_emitter(monkeypatch):
    original = L.quarantine
    seen = []

    def quarantine_spy(sub, predicate, **kwargs):
        seen.append(predicate)
        return original(sub, predicate, **kwargs)

    monkeypatch.setattr(L, "quarantine", quarantine_spy)
    for mask in range(32):
        wire = encode_wire(TriggerGateIR(mask))
        expected = emit_predicate(TriggerGateIR(mask))
        sub = _mk_template_dir()
        auditor = AuditorVerdict(
            verdict="pass", diff_digest=_digest_for(sub, wire),
        )
        # _digest_for also uses the spy; isolate the materializer call itself.
        seen.clear()
        assert T._quarantine_and_audit(
            sub,
            T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=wire),
            auditor, _G, _tmp_layout(f"wire-{mask}"),
            L.LoopState(start_ts=time.monotonic()), _planner(), write=False,
            contract=T._admit_env_contract(site_policy.OTHER),
            binding=_binding(wire),
        ) is None
        assert seen == [expected]


def test_quarantine_and_audit_allows_predicate_outer_indentation(monkeypatch):
    sub = _mk_template_dir()
    canonical = emit_predicate(parse_wire(_CLEAN_WIRE))
    indented = f"  {canonical}  "
    _res, _base, _edited, working_diff = L.quarantine(
        sub, indented, marker_id=T.MARKER_ID, source_rel=T.SOURCE_REL,
        write=False,
    )
    from orchestrator.campaign.auditor_gate import compute_diff_digest
    monkeypatch.setattr(T, "emit_predicate", lambda _ir: indented)
    assert T._quarantine_and_audit(
        sub,
        T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=_CLEAN_WIRE),
        AuditorVerdict(
            verdict="pass", diff_digest=compute_diff_digest(working_diff),
        ),
        _G, _tmp_layout("predicate-outer-indentation"),
        L.LoopState(start_ts=time.monotonic()), _planner(), write=False,
        contract=T._admit_env_contract(site_policy.OTHER),
        binding=_binding(),
    ) is None


@pytest.mark.parametrize(
    "mutate",
    (
        lambda predicate: predicate.replace(" = ", "  = ", 1),
        lambda predicate: predicate + " trailing-garbage",
    ),
)
def test_quarantine_and_audit_rejects_predicate_content_whitespace_drift_before_materialize(
    monkeypatch, mutate,
):
    canonical = emit_predicate(parse_wire(_CLEAN_WIRE))
    monkeypatch.setattr(T, "emit_predicate", lambda _ir: mutate(canonical))
    monkeypatch.setattr(
        L, "quarantine",
        lambda *_args, **_kwargs: pytest.fail(
            "predicate/binding 不一致が materialize に到達した"
        ),
    )
    with pytest.raises(
        RuntimeError, match="^trigger predicate と binding が不一致$",
    ) as excinfo:
        T._quarantine_and_audit(
            _mk_template_dir(),
            T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=_CLEAN_WIRE),
            AuditorVerdict(verdict="pass", diff_digest="unused"),
            _G, _tmp_layout("predicate-content-drift"),
            L.LoopState(start_ts=time.monotonic()), _planner(), write=False,
            contract=T._admit_env_contract(site_policy.OTHER),
            binding=_binding(),
        )
    assert _CLEAN_WIRE not in str(excinfo.value)


def test_quarantine_and_audit_rejects_crossed_predicate_and_binding_before_materialize(
    monkeypatch,
):
    wire_a = _CLEAN_WIRE
    wire_b = "01000"
    monkeypatch.setattr(
        L, "quarantine",
        lambda *_args, **_kwargs: pytest.fail(
            "predicate A / binding B の交差が materialize に到達した"
        ),
    )
    with pytest.raises(
        RuntimeError, match="^trigger predicate と binding が不一致$",
    ) as excinfo:
        T._quarantine_and_audit(
            _mk_template_dir(),
            T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=wire_a),
            AuditorVerdict(verdict="pass", diff_digest="unused"),
            _G, _tmp_layout("crossed-predicate-binding"),
            L.LoopState(start_ts=time.monotonic()), _planner(), write=False,
            contract=T._admit_env_contract(site_policy.OTHER),
            binding=_binding(wire_b),
        )
    assert wire_a not in str(excinfo.value)
    assert wire_b not in str(excinfo.value)


def test_preview_and_run_share_canonical_materialization(monkeypatch):
    import contextlib
    from orchestrator.campaign import patchharness

    monkeypatch.setattr(
        patchharness, "assert_pinned_clean", lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *_args, **_kwargs: contextlib.nullcontext(),
    )
    sub = _mk_template_dir()
    preview = T._preview_wire(_CLEAN_WIRE, sub, "/unused")
    captured = []
    original = L.quarantine

    def quarantine_spy(*args, **kwargs):
        result = original(*args, **kwargs)
        captured.append(result[3])
        return result

    monkeypatch.setattr(L, "quarantine", quarantine_spy)
    assert T._quarantine_and_audit(
        sub,
        T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=_CLEAN_WIRE),
        AuditorVerdict(verdict="pass", diff_digest=preview["diff_digest"]),
        _G, _tmp_layout("preview-run"),
        L.LoopState(start_ts=time.monotonic()), _planner(), write=False,
        contract=T._admit_env_contract(site_policy.OTHER),
        binding=_binding(),
    ) is None
    assert captured == [preview["working_diff"]]


def test_preview_cli_accepts_wire_and_rejects_old_diff_flag(monkeypatch):
    seen = []
    monkeypatch.setattr(
        T, "_preview_wire",
        lambda wire, *_args: seen.append(wire) or {"passed": True},
    )
    assert T.main(["--preview-wire", _CLEAN_WIRE]) == 0
    assert seen == [_CLEAN_WIRE]
    with pytest.raises(SystemExit) as excinfo:
        T.main(["--preview-diff", "fixture.txt"])
    assert excinfo.value.code == 2


# ==== auditor gate (共有部品の軸引数配線のみ確認 — 本体は test_auditor_gate.py) ====

def test_auditor_closed_entry_schema_rejects_raw_candidate_without_disclosure():
    raw_entry = {"wire": "10100", "mask": 5}
    cases = (
        {"verdict": "reject", "diff_digest": "a" * 64,
         "violations": [raw_entry]},
        {"verdict": "pass", "diff_digest": "a" * 64,
         "nits": [raw_entry]},
    )
    for value in cases:
        with pytest.raises(AuditorGateFailure) as excinfo:
            parse_auditor_dict(value)
        message = str(excinfo.value)
        assert "10100" not in message and "mask" not in message

    with pytest.raises(AuditorGateFailure) as excinfo:
        AuditorVerdict(
            verdict="reject", diff_digest="a" * 64,
            violations=[raw_entry],
        )
    assert "10100" not in str(excinfo.value)

    document = _proposal_document(
        {"axis": T.MARKER_ID, "wire": _CLEAN_WIRE},
    )
    document["auditor"] = {
        "verdict": "reject", "diff_digest": "a" * 64,
        "violations": [raw_entry],
    }
    with pytest.raises(AuditorGateFailure) as excinfo:
        T.load_proposal_file(_write_json(document, "auditor-raw-candidate.json"))
    assert "10100" not in str(excinfo.value)


def test_auditor_all_existing_violation_codes_and_legacy_fixed_fields_are_accepted():
    for code in range(1, 22):
        parsed = parse_auditor_dict({
            "verdict": "reject",
            "diff_digest": "a" * 64,
            "violations": [{"type": code}],
        })
        assert parsed.violations == [{"type": code}]

    parsed = parse_auditor_dict({
        "verdict": "reject",
        "diff_digest": "b" * 64,
        "violations": [{"type": 14, "note": "非SWO疑い"}],
        "nits": [{"note": "n1"}],
    })
    assert parsed.violations == [{"type": 14, "note": "非SWO疑い"}]
    assert parsed.nits == [{"note": "n1"}]


def test_auditor_sink_projects_only_closed_codes_not_free_text():
    auditor = AuditorVerdict(
        verdict="reject", diff_digest="a" * 64,
        violations=[{
            "type": 16,
            "location": "wire=10100 mask=5",
            "correctness_impact": "candidate 10100",
            "verifier_blind_spot": "mask 5",
        }],
        nits=[{"finding": "wire 10100"}],
    )
    result = auditor_reject_result(
        "auditor-violation", auditor,
        diff_region=T.SOURCE_REL, template_diff_id=T.MARKER_ID,
    )
    projected = json.dumps(result.digest, ensure_ascii=False, sort_keys=True)
    assert "violations=type-16" in projected
    assert "nits=1" in projected
    assert "10100" not in projected and "mask 5" not in projected

    auditor.violations.append({"wire": "10100", "mask": 5})
    with pytest.raises(AuditorGateFailure) as excinfo:
        auditor_reject_result(
            "auditor-violation", auditor,
            diff_region=T.SOURCE_REL, template_diff_id=T.MARKER_ID,
        )
    assert "10100" not in str(excinfo.value)

def test_quarantine_and_audit_dry_pass_when_clean_and_digest_matches(monkeypatch):
    monkeypatch.setattr(T, "_current_site", lambda: site_policy.PEGASUS_COMPUTE)
    d = _mk_template_dir()
    auditor = AuditorVerdict(verdict="pass", diff_digest=_digest_for(d))
    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=_CLEAN_WIRE)
    state = L.LoopState(start_ts=time.monotonic())
    gate = T._quarantine_and_audit(
        d, coder, auditor, _G, _tmp_layout("pass"), state,
        _planner(), write=False,
        contract=T._admit_env_contract(site_policy.PEGASUS_COMPUTE),
        binding=_binding(),
    )
    assert gate is None


def test_quarantine_and_audit_raises_on_digest_mismatch(monkeypatch):
    monkeypatch.setattr(T, "_current_site", lambda: site_policy.PEGASUS_COMPUTE)
    d = _mk_template_dir()
    auditor = AuditorVerdict(verdict="pass", diff_digest="0" * 64)
    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=_CLEAN_WIRE)
    state = L.LoopState(start_ts=time.monotonic())
    try:
        T._quarantine_and_audit(
            d, coder, auditor, _G, _tmp_layout("mm"), state,
            _planner(), write=False,
            contract=T._admit_env_contract(site_policy.PEGASUS_COMPUTE),
            binding=_binding(),
        )
        raise AssertionError("digest 不一致を素通しした")
    except AuditorGateFailure as e:
        assert "digest" in str(e)


def test_auditor_reject_carries_trigger_axis_identity(monkeypatch):
    monkeypatch.setattr(T, "_current_site", lambda: site_policy.OTHER)
    d = _mk_template_dir()
    auditor = AuditorVerdict(verdict="reject", diff_digest=_digest_for(d),
                             violations=[{"type": 16}])
    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=_CLEAN_WIRE)
    state = L.LoopState(start_ts=time.monotonic())
    lay = _tmp_layout("audrej")
    gate = T._quarantine_and_audit(
        d, coder, auditor, _G, lay, state, _planner(), write=False,
        contract=T._admit_env_contract(site_policy.OTHER),
        binding=_binding(),
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


def _proposal_document(coder: dict, *, auditor: bool = True) -> dict:
    document = {
        "planner": {
            "axis": T.MARKER_ID, "direction": "increase", "magnitude": "small",
        },
        "coder": coder,
    }
    if auditor:
        document["auditor"] = {"verdict": "pass", "diff_digest": "a" * 64}
    return document


def test_coder_proposal_accepts_all_32_wires_loader_and_direct():
    for mask in range(32):
        wire = encode_wire(TriggerGateIR(mask))
        direct = T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=wire)
        assert direct.wire == wire
        _planner_value, loaded, _auditor, _prior = T.load_proposal_file(
            _write_json(
                _proposal_document({"axis": T.MARKER_ID, "wire": wire}),
                f"wire-{mask}.json",
            )
        )
        assert loaded == direct
    frozen = T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=_CLEAN_WIRE)
    with pytest.raises(FrozenInstanceError):
        frozen.wire = "00000"


@pytest.mark.parametrize(
    "bad_wire",
    [None, True, False, 0, 1, [], {}, "", "0", "0000", "000000",
     "0000x", " 0000", "0000\n", "１２３４５"],
)
def test_coder_proposal_rejects_invalid_wire_corpus(bad_wire):
    with pytest.raises(RefluxIRError, match="^invalid reflux IR$"):
        T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=bad_wire)
    with pytest.raises(RefluxIRError, match="^invalid reflux IR$"):
        T.load_proposal_file(_write_json(
            _proposal_document({"axis": T.MARKER_ID, "wire": bad_wire}),
            "bad-wire.json",
        ))


def test_old_implementation_cpp_and_extra_key_rejected_before_materialize(monkeypatch):
    calls = []
    monkeypatch.setattr(L, "quarantine", lambda *_args, **_kwargs: calls.append(True))
    with pytest.raises(RefluxIRError):
        T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=_CLEAN_IMPL)
    invalid_coders = (
        {"axis": T.MARKER_ID, "implementation": _CLEAN_IMPL},
        {"axis": T.MARKER_ID, "wire": _CLEAN_IMPL},
        {"axis": T.MARKER_ID, "wire": _CLEAN_WIRE, "extra": "no"},
        {"axis": T.MARKER_ID, "wire": _CLEAN_WIRE, "value": 1},
    )
    for index, coder in enumerate(invalid_coders):
        with pytest.raises((KeyError, ValueError, RefluxIRError)):
            T.load_proposal_file(_write_json(
                _proposal_document(coder), f"closed-{index}.json",
            ))
    assert calls == []


def test_coder_axis_mismatch_rejected_by_loader_and_direct_constructor():
    other_axis = "silo-backoff-magnitude"
    with pytest.raises(ValueError, match="coder axis"):
        T.CoderProposalTriggerGating(axis=other_axis, wire=_CLEAN_WIRE)
    with pytest.raises(ValueError, match="coder axis"):
        T.load_proposal_file(_write_json(
            _proposal_document({"axis": other_axis, "wire": _CLEAN_WIRE}),
            "axis-mismatch.json",
        ))


def test_planner_axis_mismatch_and_planner_enums_rejected_by_loader_and_sink():
    document = _proposal_document(
        {"axis": T.MARKER_ID, "wire": _CLEAN_WIRE},
    )
    document["planner"]["axis"] = "silo-backoff-magnitude"
    with pytest.raises(ValueError, match="planner/coder axis"):
        T.load_proposal_file(_write_json(document, "planner-axis-mismatch.json"))
    for field, value in (("direction", "sideways"), ("magnitude", "huge")):
        invalid = _proposal_document(
            {"axis": T.MARKER_ID, "wire": _CLEAN_WIRE},
        )
        invalid["planner"][field] = value
        with pytest.raises(ValueError):
            T.load_proposal_file(_write_json(
                invalid, f"planner-{field}-invalid.json",
            ))

    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=_CLEAN_WIRE)
    auditor = AuditorVerdict(verdict="pass", diff_digest="unused")
    bad_planners = (
        L.PlannerProposal(axis="silo-backoff-magnitude",
                          direction="increase", magnitude="small"),
        L.PlannerProposal(axis=T.MARKER_ID, direction="sideways", magnitude="small"),
        L.PlannerProposal(axis=T.MARKER_ID, direction="increase", magnitude="huge"),
    )
    for planner in bad_planners:
        with pytest.raises(ValueError):
            T.run_one_iteration(
                T.default_cfg(), T.default_perf(), planner, coder, auditor,
                L.LoopState(iteration=1), "/must-not-be-read", do_build=False,
                layout=_tmp_layout("planner-sink"),
            )


def test_load_proposal_file_auditor_and_prior_still_fail_closed():
    base = _proposal_document(
        {"axis": T.MARKER_ID, "wire": _CLEAN_WIRE}, auditor=False,
    )
    # auditor キー欠落 → KeyError (fails-closed)
    with pytest.raises(KeyError):
        T.load_proposal_file(_write_json(base, "no_auditor.json"))
    ok = {**base, "auditor": {"verdict": "pass", "diff_digest": "a" * 64},
          "prior_critic_reverse": True}
    _planner_value, coder, auditor, prior = T.load_proposal_file(
        _write_json(ok, "ok.json")
    )
    assert coder.wire == _CLEAN_WIRE and not hasattr(coder, "value")
    assert auditor.verdict == "pass" and prior is True

    # uncertain は violations なし + 非空 uncertainty が必須 (共有 parser 境界)。
    bad_uncertain = {**base,
                     "auditor": {"verdict": "uncertain", "diff_digest": "b" * 64}}
    with pytest.raises(T.AuditorGateFailure):
        T.load_proposal_file(_write_json(bad_uncertain, "uncertain_without_reason.json"))


def test_projection_guard_trigger_mode_and_legacy_modes_are_closed():
    trigger_document = _proposal_document(
        {"axis": T.MARKER_ID, "wire": _CLEAN_WIRE},
    )
    assert_closed_proposal_schema(
        trigger_document, require_auditor=True, require_coder_value=False,
        coder_contract=CODER_CONTRACT_TRIGGER_WIRE,
    )
    for unknown in (None, 1, True, "trigger_wire", ""):
        with pytest.raises(ValueError, match="coder contract mode"):
            assert_closed_proposal_schema(
                trigger_document, require_auditor=True,
                require_coder_value=False, coder_contract=unknown,
            )
    with pytest.raises(ValueError, match="value"):
        assert_closed_proposal_schema(
            trigger_document, require_auditor=True, require_coder_value=True,
            coder_contract=CODER_CONTRACT_TRIGGER_WIRE,
        )

    legacy = _proposal_document(
        {"axis": "silo-backoff-magnitude", "implementation": "x", "value": 20},
    )
    assert_closed_proposal_schema(
        legacy, require_auditor=True, require_coder_value=True,
        coder_contract=CODER_CONTRACT_IMPLEMENTATION,
    )
    sort_document = _proposal_document({
        "axis": SORT.MARKER_ID,
        "implementation": "sort(write_set_.begin(), write_set_.end());",
    })
    sort_document["planner"]["axis"] = SORT.MARKER_ID
    assert_closed_proposal_schema(
        sort_document, require_auditor=True, require_coder_value=False,
    )
    assert_closed_proposal_schema(
        _proposal_document(
            {"axis": "silo-backoff-magnitude", "implementation": "x"},
            auditor=False,
        ),
        require_auditor=False, require_coder_value=False,
    )
    with pytest.raises(KeyError):
        assert_closed_proposal_schema(
            _proposal_document(
                {"axis": "silo-backoff-magnitude", "implementation": "x"},
                auditor=False,
            ),
            require_auditor=False, require_coder_value=True,
        )
    with pytest.raises(KeyError):
        assert_closed_proposal_schema(
            _proposal_document(
                {"axis": "silo-backoff-magnitude", "implementation": "x",
                 "value": 20}, auditor=False,
            ),
            require_auditor=True, require_coder_value=True,
        )


# ==== campaign 設定 =============================================================

def test_default_cfg_wires_s2_verify_and_axis():
    cfg = T.default_cfg()
    assert cfg.search_config.get(SEARCH_CONFIG_VERIFY_KEY) == VERIFY_LEGACY_PLUS_S2
    assert cfg.search_config.get("axis") == T.MARKER_ID
    assert cfg.search_config.get("trigger_gate_binding_schema") == \
        TRIGGER_GATE_BINDING_SCHEMA
    assert cfg.ccbench_commit == T.PIN == "e9e477c"


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

@pytest.mark.usefixtures("ratified_enforcement_source")
def test_drive_iteration_stops_before_running_but_writes_header(monkeypatch):
    """入口停止でも provenance ヘッダは焼かれる (ヘッダは入口 = build 前、FC-1(a))。
    sub に不在パスを渡しても到達しないことが実行前停止の証拠。"""
    monkeypatch.setattr(T, "_current_site", lambda: site_policy.OTHER)
    lay = _tmp_layout("stopbefore")
    monkeypatch.setattr(T, "exploration_campaign_layout", lambda _id: lay)
    seed = L.LoopState(iteration=0, start_wall=time.time(),
                       reverse_recommendations=L.REVERSE_STREAK - 1)
    L.save_loop_state(lay, seed)
    cfg = T._campaign_cfg_for_site(T.default_cfg(), site_policy.OTHER)
    perf = T.default_perf()
    cd = T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=_CLEAN_WIRE)
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
    monkeypatch.setattr(T, "exploration_campaign_layout", lambda _id: lay)
    seed = L.LoopState(
        iteration=0, start_wall=time.time(),
        reverse_recommendations=L.REVERSE_STREAK - 1,
    )
    L.save_loop_state(lay, seed)
    state_before = open(L.loop_state_path(lay), "rb").read()
    coder = T.CoderProposalTriggerGating(
        axis=T.MARKER_ID, wire=_CLEAN_WIRE,
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


def test_drive_trigger_crash_tail_fails_before_stop_checkpoint_and_provenance(
        monkeypatch):
    monkeypatch.setattr(T, "_current_site", lambda: site_policy.OTHER)
    lay = _tmp_layout("trigger-recovery-before-stop")
    monkeypatch.setattr(T, "exploration_campaign_layout", lambda _id: lay)
    cfg = T._campaign_cfg_for_site(T.default_cfg(), site_policy.OTHER)
    perf = T.default_perf()
    wal.write_lock(lay, build_v2_lock(ident.canonical_preimage(cfg)))
    attempt_id = "trigger-crashed-attempt"
    binding = _binding()
    commitment_value = wal.log_trigger_binding(
        lay, "trigger-crashed-v", "test-env", attempt_id, binding,
    )
    wal.log(lay, "trigger-crashed-v", "build_start", "test-env", {
        "build_attempt_id": attempt_id,
        wal.TRIGGER_BINDING_COMMITMENT_KEY: commitment_value,
    })
    seed = L.LoopState(
        iteration=0, start_wall=time.time(),
        reverse_recommendations=L.REVERSE_STREAK - 1,
    )
    L.save_loop_state(lay, seed)
    checkpoint_before = open(L.loop_state_path(lay), "rb").read()
    wal_before = open(lay.wal_file, "rb").read()
    coder = T.CoderProposalTriggerGating(
        axis=T.MARKER_ID, wire=_CLEAN_WIRE,
    )
    auditor = AuditorVerdict(verdict="pass", diff_digest="a" * 64)

    with pytest.raises(wal.InterruptedAttemptRecoveryError) as excinfo:
        T.drive_iteration(
            cfg, perf, _planner(), coder, auditor,
            prior_critic_reverse=True, sub="/must-not-run", do_build=False,
            layout=lay,
        )
    assert excinfo.value.condition == "trigger-campaign"
    assert excinfo.value.variant == "trigger-crashed-v"
    assert excinfo.value.attempt_id == attempt_id
    assert open(lay.wal_file, "rb").read() == wal_before
    assert open(L.loop_state_path(lay), "rb").read() == checkpoint_before
    assert not os.path.exists(T._provenance_path(lay))


def test_inner_run_reject_start_crash_fails_before_second_start(monkeypatch):
    import contextlib
    from orchestrator.campaign import patchharness

    monkeypatch.setattr(T, "_current_site", lambda: site_policy.OTHER)
    cfg = T._campaign_cfg_for_site(T.default_cfg(), site_policy.OTHER)
    policy = _CODER_CONTEXT.policy
    attempt_id = "crashed-trigger-reject-attempt"
    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=_CLEAN_WIRE)
    predicate = emit_predicate(parse_wire(coder.wire))
    variant = L.diffq_variant_id(_G, predicate)
    sub = _mk_template_dir()
    auditor = AuditorVerdict(
        verdict="reject", diff_digest=_digest_for(sub),
        violations=[{"type": 16}],
    )

    def new_layout(tag):
        parent = tempfile.mkdtemp(prefix=f"izanagi_s8atrigloop_{tag}_")
        return CampaignLayout(
            root=os.path.join(parent, str(ident.campaign_id(cfg))),
        ).ensure()

    def seed_active_attempt(layout):
        wal.write_lock(layout, build_v2_lock(ident.canonical_preimage(cfg)))
        commitment_value = wal.log_trigger_binding(
            layout, variant, "test-env", attempt_id, _binding(),
        )
        wal.log(layout, variant, "build_start", "test-env", {
            "genome": _G.canonical(), "src_token": "",
            "build_attempt_id": attempt_id,
            wal.TRIGGER_BINDING_COMMITMENT_KEY: commitment_value,
        })

    def write_provenance_for_starts(layout, records):
        T._write_provenance_header(layout)
        starts = [record for record in records if record.stage == "build_start"]
        for iteration, start in enumerate(starts, 1):
            T._append_provenance_entry(layout, iteration, {
                "variant": start.variant,
                "build_attempt_id": start.payload["build_attempt_id"],
                wal.TRIGGER_BINDING_COMMITMENT_KEY:
                    start.payload[wal.TRIGGER_BINDING_COMMITMENT_KEY],
            })

    current = new_layout("inner-trigger-reject-current")
    seed_active_attempt(current)
    before = open(current.wal_file, "rb").read()
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *_args, **_kwargs: contextlib.nullcontext(),
    )

    recovery_error = None
    try:
        T.run_one_iteration(
            cfg, T.default_perf(), _planner(), coder, auditor,
            L.LoopState(start_wall=time.time()), sub,
            do_build=False, layout=current, log=lambda *_args: None,
        )
    except wal.InterruptedAttemptRecoveryError as exc:
        recovery_error = exc
    assert open(current.wal_file, "rb").read() == before
    current_records = wal.read_records(current)
    assert [record.stage for record in current_records] == [
        TRIGGER_GATE_BINDING_WAL_STAGE, "build_start",
    ]
    assert recovery_error is not None
    assert recovery_error.condition == "trigger-campaign"
    assert variant in wal.replay(current, admission_policy=policy)
    write_provenance_for_starts(current, current_records)
    assert require_admitted_campaign(
        current, purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    ).decision.admitted

    mutant = new_layout("inner-trigger-reject-identity-only")
    seed_active_attempt(mutant)
    mutant_before = open(mutant.wal_file, "rb").read()

    def identity_only(campaign_cfg, layout, *, admission_policy):
        ident.ensure_campaign_identity(
            campaign_cfg, layout, admission_policy=admission_policy,
        )

    monkeypatch.setattr(T.ident, "ensure_resumable_attempts", identity_only)
    out = T.run_one_iteration(
        cfg, T.default_perf(), _planner(), coder, auditor,
        L.LoopState(start_wall=time.time()), sub,
        do_build=False, layout=mutant, log=lambda *_args: None,
    )
    assert out["outcome"] == "rejected"
    assert out["variant"] == variant
    assert open(mutant.wal_file, "rb").read() != mutant_before
    mutant_records = wal.read_records(mutant)
    assert [record.stage for record in mutant_records] == [
        TRIGGER_GATE_BINDING_WAL_STAGE, "build_start",
        TRIGGER_GATE_BINDING_WAL_STAGE, "build_start", "abort",
    ]
    bindings = [
        record for record in mutant_records
        if record.stage == TRIGGER_GATE_BINDING_WAL_STAGE
    ]
    starts = [record for record in mutant_records if record.stage == "build_start"]
    assert [record.variant for record in bindings] == [variant, variant]
    assert [record.variant for record in starts] == [variant, variant]
    assert (
        bindings[0].payload["build_attempt_id"]
        == starts[0].payload["build_attempt_id"]
    )
    assert (
        bindings[1].payload["build_attempt_id"]
        == starts[1].payload["build_attempt_id"]
    )
    assert starts[0].payload["build_attempt_id"] == attempt_id
    assert starts[1].payload["build_attempt_id"] != attempt_id
    assert mutant_records[-1].payload["build_attempt_id"] == (
        starts[1].payload["build_attempt_id"]
    )
    with pytest.raises(wal.AttemptTopologyError, match="variant に未終端 attempt"):
        wal.replay(mutant, admission_policy=policy)
    write_provenance_for_starts(mutant, mutant_records)
    with pytest.raises(ArtifactAdmissionError, match="variant に未終端 attempt"):
        require_admitted_campaign(
            mutant, purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
        )


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_drive_iteration_writes_entry_and_checkpoint(monkeypatch):
    """fresh reject 後も次候補の public funnel が identity を照合して resume する。"""
    import contextlib
    from orchestrator.campaign import patchharness

    monkeypatch.setattr(T, "_current_site", lambda: site_policy.OTHER)
    sub = _mk_template_dir()
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *_args, **_kwargs: contextlib.nullcontext(),
    )
    lay = _tmp_layout("driveprov")
    monkeypatch.setattr(T, "exploration_campaign_layout", lambda _id: lay)
    cfg = T._campaign_cfg_for_site(T.default_cfg(), site_policy.OTHER)
    perf = T.default_perf()
    first_wire = "10100"
    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=first_wire)
    auditor = AuditorVerdict(
        verdict="reject", diff_digest=_digest_for(sub, first_wire),
        violations=[{"type": 16}],
    )
    out = T.drive_iteration(cfg, perf, _planner(), coder, auditor, None, sub, do_build=False,
                            layout=lay, proposal_path="/scratch/prop1.json")
    assert out["ran"] is True and out["outcome"] == "rejected" and out["iteration"] == 1
    assert wal.read_lock(lay) == build_v2_lock(ident.canonical_preimage(cfg))
    second_wire = "01000"
    next_coder = T.CoderProposalTriggerGating(
        axis=T.MARKER_ID, wire=second_wire,
    )
    next_auditor = AuditorVerdict(
        verdict="reject", diff_digest=_digest_for(sub, second_wire),
        violations=[{"type": 16}],
    )
    resumed = T.drive_iteration(
        cfg, perf, _planner(), next_coder, next_auditor, None, sub, do_build=False,
        layout=lay, proposal_path="/scratch/prop2.json",
    )
    assert resumed["iteration"] == 2 and resumed["outcome"] == "rejected"
    with open(T._provenance_path(lay), encoding="utf-8") as f:
        prov = json.load(f)
    assert prov["entries"]["1"]["outcome"] == "rejected"
    assert prov["entries"]["1"]["proposal_path"] == "/scratch/prop1.json"
    assert prov["entries"]["2"]["proposal_path"] == "/scratch/prop2.json"
    for entry in prov["entries"].values():
        assert set(entry) >= {"trigger_gate_binding_commitment"}
        assert len(entry["trigger_gate_binding_commitment"]) == 64
        encoded = json.dumps(entry, sort_keys=True)
        assert "wire" not in encoded and "mask" not in encoded
    st = L.load_loop_state(lay)
    assert st.iteration == 2 and [e.result for e in st.whiteboard] == [
        "rejected", "rejected",
    ]


def test_source_preimage_writer_is_idempotent_and_rejects_different_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    layout = CampaignLayout(root=str(tmp_path / "campaign")).ensure()
    proposal = tmp_path / "proposal.json"
    proposal.write_bytes(b'{"proposal":"fixture"}')
    emitted = {"bytes": b"first-preimage"}
    monkeypatch.setattr(
        T.buildcache, "compilers_for_current_site", lambda: ("gcc", "g++-13"),
    )
    monkeypatch.setattr(
        T.source_digest,
        "canonical_source_preimage_bytes",
        lambda *_args, **_kwargs: emitted["bytes"],
    )
    kwargs = {
        "layout": layout,
        "proposal_path": str(proposal),
        "genome": Genome("silo", {}),
        "sub": str(tmp_path),
    }
    first = T._write_source_preimage_artifact(**kwargs)
    second = T._write_source_preimage_artifact(**kwargs)
    assert first == second
    artifact = Path(layout.root) / first
    assert artifact.read_bytes() == b"first-preimage"

    emitted["bytes"] = b"different-preimage"
    with pytest.raises(
        RuntimeError,
        match=(r"source preimage artifact differs on idempotent reuse: "
               r"proposal_sha256=[0-9a-f]{64} path=.*\.preimage "
               r"expected_sha256=[0-9a-f]{64} actual_sha256=[0-9a-f]{64}$"),
    ):
        T._write_source_preimage_artifact(**kwargs)
    assert artifact.read_bytes() == b"first-preimage"


def test_materialized_source_preimage_is_written_before_run_campaign(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    import contextlib
    from orchestrator.campaign import patchharness

    order: list[str] = []
    layout = CampaignLayout(root=str(tmp_path / "campaign")).ensure()

    @contextlib.contextmanager
    def materialized_scope():
        order.append("materialize-enter")
        try:
            yield
        finally:
            order.append("materialize-exit")

    monkeypatch.setattr(
        patchharness, "applied", lambda *_args, **_kwargs: materialized_scope(),
    )
    monkeypatch.setattr(T, "_quarantine_and_audit", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(T.ident, "ensure_resumable_attempts", lambda *_args, **_kwargs: None)
    def write_source_preimage(**_kwargs):
        assert order == ["materialize-enter"]
        order.append("source-preimage")
        return "source-bindings/x.preimage"

    monkeypatch.setattr(T, "_write_source_preimage_artifact", write_source_preimage)

    def run_campaign(*_args, **_kwargs):
        assert order == ["materialize-enter", "source-preimage"]
        order.append("run-campaign")
        return SimpleNamespace(execution_receipt=None, results=[], skipped=0)

    monkeypatch.setattr(T, "run_campaign", run_campaign)
    contract = env_contract.GENERATIONS["linux-baremetal"][0].contract
    T._run_one_iteration_resolved(
        T.default_cfg(), T.default_perf(), _planner(),
        T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire="00000"),
        AuditorVerdict(verdict="pass", diff_digest="a" * 64),
        L.LoopState(start_wall=time.time()), str(tmp_path), True,
        layout, contract, site_policy.OTHER,
        proposal_path=str(tmp_path / "proposal.json"),
        build_context=_CODER_CONTEXT,
        require_source_preimage_artifact=True,
    )
    assert order == [
        "materialize-enter", "source-preimage", "run-campaign", "materialize-exit",
    ]


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_drive_iteration_provenance_copies_each_reject_wal_build_attempt_id(monkeypatch):
    """同じ variant の build 前 reject も attempt ごとに provenance へ転記する。"""
    import contextlib
    from orchestrator.campaign import patchharness

    monkeypatch.setattr(T, "_current_site", lambda: site_policy.OTHER)
    sub = _mk_template_dir()
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *_args, **_kwargs: contextlib.nullcontext(),
    )
    lay = _tmp_layout("reject-attempt-provenance")
    monkeypatch.setattr(T, "exploration_campaign_layout", lambda _id: lay)
    auditor = AuditorVerdict(
        verdict="reject", diff_digest=_digest_for(sub),
        violations=[{"type": 16}],
    )

    outcomes = [
        T.drive_iteration(
            T.default_cfg(), T.default_perf(), _planner(),
            T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=_CLEAN_WIRE),
            auditor, None, sub, do_build=False, layout=lay,
        )
        for _ in range(2)
    ]
    starts = [
        record.payload for record in wal.read_records(lay)
        if record.stage == "build_start"
    ]
    with open(T._provenance_path(lay), encoding="utf-8") as f:
        entries = json.load(f)["entries"]

    assert outcomes[0]["variant"] == outcomes[1]["variant"]
    assert len(starts) == 2
    assert starts[0]["build_attempt_id"] != starts[1]["build_attempt_id"]
    assert [entries[str(i)]["build_attempt_id"] for i in (1, 2)] == [
        start["build_attempt_id"] for start in starts
    ]
    assert [entries[str(i)]["trigger_gate_binding_commitment"] for i in (1, 2)] == [
        start["trigger_gate_binding_commitment"] for start in starts
    ]


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_drive_iteration_dry_pass_provenance_has_no_attempt_id(monkeypatch):
    """WAL build_start のない dry-pass を admission 対象 attempt に偽装しない。"""
    import contextlib
    from orchestrator.campaign import patchharness

    monkeypatch.setattr(T, "_current_site", lambda: site_policy.OTHER)
    sub = _mk_template_dir()
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *_args, **_kwargs: contextlib.nullcontext(),
    )
    lay = _tmp_layout("dry-pass-no-attempt")
    monkeypatch.setattr(T, "exploration_campaign_layout", lambda _id: lay)
    auditor = AuditorVerdict(
        verdict="pass", diff_digest=_digest_for(sub),
    )

    out = T.drive_iteration(
        T.default_cfg(), T.default_perf(), _planner(),
        T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=_CLEAN_WIRE),
        auditor, None, sub, do_build=False, layout=lay,
    )
    with open(T._provenance_path(lay), encoding="utf-8") as f:
        entry = json.load(f)["entries"]["1"]

    assert out["outcome"] == "dry-pass"
    assert entry["variant"] is None
    assert "build_attempt_id" not in entry
    assert not any(record.stage == "build_start" for record in wal.read_records(lay))


@pytest.mark.usefixtures("ratified_enforcement_source")
def test_drive_iteration_entry_failure_blocks_checkpoint(monkeypatch):
    """provenance entry が書けない iteration は checkpoint を前進させない (FC-1(b) 裁定 —
    「WAL/checkpoint は進んだが記録なし」の中途半端を作らない)。"""
    import contextlib
    from orchestrator.campaign import patchharness

    monkeypatch.setattr(T, "_current_site", lambda: site_policy.OTHER)
    sub = _mk_template_dir()
    monkeypatch.setattr(
        patchharness, "applied",
        lambda *_args, **_kwargs: contextlib.nullcontext(),
    )
    lay = _tmp_layout("provblock")
    monkeypatch.setattr(T, "exploration_campaign_layout", lambda _id: lay)
    cfg, perf = T.default_cfg(), T.default_perf()
    coder = T.CoderProposalTriggerGating(axis=T.MARKER_ID, wire=_CLEAN_WIRE)
    auditor = AuditorVerdict(
        verdict="reject", diff_digest=_digest_for(sub),
        violations=[{"type": 16}],
    )

    def boom(layout, iteration, entry):
        raise OSError("simulated provenance write failure")
    monkeypatch.setattr(T, "_append_provenance_entry", boom)
    try:
        T.drive_iteration(cfg, perf, _planner(), coder, auditor, None, sub, do_build=False,
                          layout=lay)
        raise AssertionError("provenance 書き込み失敗を素通しした")
    except OSError:
        pass
    assert L.load_loop_state(lay) is None   # checkpoint は前進していない


# ==== B-4 mandatory continuation wiring ======================================

def _b4_file_tree_bytes(root: str) -> dict[str, bytes]:
    base = Path(root)
    return {
        str(path.relative_to(base)): path.read_bytes()
        for path in sorted(base.rglob("*"))
        if path.is_file()
    }


def _seed_trigger_b4_continuation(layout: CampaignLayout) -> None:
    state = L.LoopState(iteration=1, start_wall=time.time())
    state.whiteboard.append(L.WhiteboardEntry(
        iteration=1,
        direction="increase",
        magnitude="small",
        result="rejected",
        delta_pct=None,
    ))
    L.save_loop_state(layout, state)


def _b4_trigger_receipt(cfg, *, reverse_recommended: bool) -> SimpleNamespace:
    return SimpleNamespace(
        schema_version=B4_CLOSED.B4_CLOSED_CRITIC_RECEIPT_SCHEMA,
        status="success",
        evidence_class="certified",
        campaign_id=str(ident.campaign_id(cfg)),
        arm=cfg.search_config["reflux"],
        iteration=1,
        pair_id="b4-trigger-pair",
        decision_sha256="e" * 64,
        decision_reverse_recommended=reverse_recommended,
    )


def _b4_trigger_proposal(receipt_sha256: str | None = None) -> dict:
    document = _proposal_document(
        {"axis": T.MARKER_ID, "wire": _CLEAN_WIRE},
    )
    if receipt_sha256 is not None:
        document[L.B4_PROPOSAL_RECEIPT_SHA256_KEY] = receipt_sha256
    return document


def test_b4_trigger_marker_is_opt_in_and_ordinary_contract_digest_is_unchanged(
        tmp_path, monkeypatch):
    ordinary = T.default_cfg(reflux=True)
    explicit_false = T.default_cfg(
        reflux=True, b4_reflux_ablation=False,
    )
    marked = T.default_cfg(
        reflux=True, b4_reflux_ablation=True,
        _b4_launch_context=_B4_TEST_CONTEXT,
    )
    assert inspect.signature(T.default_cfg).parameters[
        "b4_reflux_ablation"
    ].kind is inspect.Parameter.KEYWORD_ONLY
    assert ordinary == explicit_false
    assert L.B4_PROTOCOL_KEY not in ordinary.search_config
    assert marked.search_config[L.B4_PROTOCOL_KEY] == L.B4_PROTOCOL_VALUE
    assert str(ident.campaign_id(ordinary)) == _T816_OTHER_CAMPAIGN_ID
    assert ident.campaign_id(marked) != ident.campaign_id(ordinary)

    legacy_document = _b4_trigger_proposal()
    legacy_document["prior_critic_reverse"] = False
    planner, coder, auditor, prior = T.load_proposal_file(
        _write_json(legacy_document, "ordinary-trigger-contract.json")
    )
    assert prior is False

    layout = CampaignLayout(root=str(tmp_path / "ordinary-trigger")).ensure()
    monkeypatch.setattr(T, "_current_site", lambda: site_policy.OTHER)
    monkeypatch.setattr(T, "exploration_campaign_layout", lambda _id: layout)
    monkeypatch.setattr(T.ident, "ensure_resumable_attempts", lambda *_a, **_k: None)
    monkeypatch.setattr(
        T,
        "_run_one_iteration_resolved",
        lambda *_a, **_k: {"outcome": "rejected", "variant": None},
    )
    monkeypatch.setattr(L, "require_admitted_campaign", lambda *_a, **_k: object())
    monkeypatch.setattr(
        L, "make_critic_identity_projection", lambda _view: object(),
    )
    digest_spy = mock.Mock(return_value="ordinary-trigger-digest")
    monkeypatch.setattr(L, "make_critic_digest", digest_spy)
    out = T.drive_iteration(
        ordinary, T.default_perf(), planner, coder, auditor, prior,
        sub="unused", do_build=True, layout=layout,
        build_context=_CODER_CONTEXT,
    )
    assert out["ran"] is True and out["critic_digest_generated"] is True
    assert digest_spy.call_count == 1
    assert (Path(layout.root) / T.DIGEST_BASENAME).read_text(
        encoding="utf-8"
    ) == "ordinary-trigger-digest"


def test_m03_b4_trigger_default_cfg_rejects_unsealed_marker_creation():
    """M03: the real trigger default_cfg cannot mint a marker without G1."""
    with pytest.raises(
        B4_LAUNCHER.B4LauncherAuthorizationError,
        match="trigger marker creation",
    ):
        T.default_cfg(b4_reflux_ablation=True)


def test_m06_b4_trigger_resolved_iteration_requires_launcher(tmp_path):
    """M06: the real resolved trigger iteration rejects before side effects."""
    raw_cfg = T.default_cfg(
        b4_reflux_ablation=True,
        _b4_launch_context=_B4_TEST_CONTEXT,
    )
    site = site_policy.OTHER
    contract = T._admit_env_contract(site)
    cfg = T._campaign_cfg_for_site(raw_cfg, site, _contract=contract)
    root = tmp_path / "m06-campaign"
    state = L.LoopState()
    with pytest.raises(
        B4_LAUNCHER.B4LauncherAuthorizationError,
        match="trigger resolved run_one_iteration",
    ):
        T._run_one_iteration_resolved(
            cfg,
            T.default_perf(),
            _planner(),
            T.CoderProposalTriggerGating(T.MARKER_ID, _CLEAN_WIRE),
            AuditorVerdict("pass", "a" * 64),
            state,
            "unused",
            False,
            CampaignLayout(str(root)),
            contract,
            site,
            build_context=_CODER_CONTEXT,
        )
    assert not root.exists()
    assert state.iteration == 0 and state.whiteboard == []


def test_m07_b4_trigger_public_iteration_requires_launcher(
    tmp_path, monkeypatch,
):
    """M07: the real public trigger iteration rejects before site resolution."""
    cfg = T.default_cfg(
        b4_reflux_ablation=True,
        _b4_launch_context=_B4_TEST_CONTEXT,
    )
    site_spy = mock.Mock(side_effect=AssertionError("site resolution reached"))
    monkeypatch.setattr(T, "_current_site", site_spy)
    root = tmp_path / "m07-campaign"
    state = L.LoopState()
    with pytest.raises(
        B4_LAUNCHER.B4LauncherAuthorizationError,
        match="trigger public run_one_iteration",
    ):
        T.run_one_iteration(
            cfg,
            T.default_perf(),
            _planner(),
            T.CoderProposalTriggerGating(T.MARKER_ID, _CLEAN_WIRE),
            AuditorVerdict("pass", "a" * 64),
            state,
            "unused",
            False,
            layout=CampaignLayout(str(root)),
        )
    assert site_spy.call_count == 0
    assert not root.exists()
    assert state.iteration == 0 and state.whiteboard == []


def test_m10_b4_trigger_drive_rejects_before_layout_and_state_progress(
    tmp_path, monkeypatch,
):
    """M10: G3 precedes root creation and iteration-1 handoff to real G2."""
    raw_cfg = T.default_cfg(
        b4_reflux_ablation=True,
        _b4_launch_context=_B4_TEST_CONTEXT,
    )
    site = site_policy.OTHER
    contract = T._admit_env_contract(site)
    root = tmp_path / "m10-campaign"
    layout = CampaignLayout(str(root))
    observed_iterations = []
    real_run_one_iteration = T._run_one_iteration_resolved

    def observing_run_one_iteration(*args, **kwargs):
        observed_iterations.append(args[5].iteration)
        return real_run_one_iteration(*args, **kwargs)

    monkeypatch.setattr(T, "exploration_campaign_layout", lambda _id: layout)
    monkeypatch.setattr(L, "exploration_campaign_layout", lambda _id: layout)
    monkeypatch.setattr(
        T, "_run_one_iteration_resolved", observing_run_one_iteration,
    )
    with pytest.raises(B4_LAUNCHER.B4LauncherAuthorizationError) as caught:
        T.drive_iteration(
            raw_cfg,
            T.default_perf(),
            _planner(),
            T.CoderProposalTriggerGating(T.MARKER_ID, _CLEAN_WIRE),
            AuditorVerdict("pass", "a" * 64),
            None,
            "unused",
            True,
            layout=layout,
            build_context=_CODER_CONTEXT,
            _resolved_site=site,
            _contract=contract,
        )
    # A G3 deletion reaches G2; kill it on effects before pinning the G3 message.
    assert observed_iterations == []
    assert not root.exists()
    assert "trigger drive_iteration" in str(caught.value)


def test_b4_trigger_certified_receipt_advances_through_shared_gate(
        tmp_path, monkeypatch):
    raw_cfg = T.default_cfg(
        reflux=False, b4_reflux_ablation=True,
        _b4_launch_context=_B4_TEST_CONTEXT,
    )
    site = site_policy.OTHER
    contract = T._admit_env_contract(site)
    campaign_cfg = T._campaign_cfg_for_site(
        raw_cfg, site, _contract=contract,
    )
    campaign_cfg = ident.bind_admission_policy(
        campaign_cfg, _CODER_CONTEXT.policy,
    )
    layout = CampaignLayout(root=str(tmp_path / "resolved-trigger")).ensure()
    _seed_trigger_b4_continuation(layout)
    receipt_path = tmp_path / "terminal.json"
    receipt_path.write_bytes(b'{"evidence_class":"certified"}')
    receipt_sha256 = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    planner, coder, auditor, prior = T.load_proposal_file(
        _write_json(
            _b4_trigger_proposal(receipt_sha256),
            "b4-trigger-positive.json",
        ),
        b4_reflux_ablation=True,
        b4_closed_critic_receipt_sha256=receipt_sha256,
    )
    receipt = _b4_trigger_receipt(campaign_cfg, reverse_recommended=True)
    verified_campaign_ids = []

    def certified_gate(path, *, cfg, layout):
        assert Path(path) == receipt_path
        verified_campaign_ids.append(str(ident.campaign_id(cfg)))
        assert str(ident.campaign_id(cfg)) == receipt.campaign_id
        return receipt

    observed_reverse = []

    def run_spy(_cfg, _perf, planner_value, _coder, _auditor, state,
                *_args, **_kwargs):
        observed_reverse.append(state.reverse_recommendations)
        L.project_whiteboard(state, planner_value, "fail")
        return {
            "outcome": "rejected",
            "variant": None,
            "campaign_id": receipt.campaign_id,
            "layout_root": layout.root,
        }

    monkeypatch.setattr(T, "exploration_campaign_layout", lambda _id: layout)
    monkeypatch.setattr(L, "exploration_campaign_layout", lambda _id: layout)
    monkeypatch.setattr(B4_CLOSED, "require_b4_closed_critic_receipt", certified_gate)
    monkeypatch.setattr(T.ident, "ensure_resumable_attempts", lambda *_a, **_k: None)
    monkeypatch.setattr(T, "_run_one_iteration_resolved", run_spy)
    monkeypatch.setattr(L, "require_admitted_campaign", lambda *_a, **_k: object())
    monkeypatch.setattr(
        L, "make_critic_identity_projection", lambda _view: object(),
    )
    monkeypatch.setattr(L, "make_critic_digest", lambda *_a, **_k: "b4-trigger-digest")
    out = T.drive_iteration(
        raw_cfg, T.default_perf(), planner, coder, auditor, prior,
        sub="unused", do_build=True, layout=layout,
        build_context=_CODER_CONTEXT,
        b4_closed_critic_receipt=receipt_path,
        b4_proposal_receipt_sha256=receipt_sha256,
        _resolved_site=site,
        _contract=contract,
        _b4_launch_context=_b4_production_context(
            campaign_cfg, arm="off", site=site,
        ),
    )
    assert out["ran"] is True and out["iteration"] == 2
    assert out["campaign_id"] == receipt.campaign_id
    assert verified_campaign_ids == [receipt.campaign_id]
    assert observed_reverse == [1]
    records = list(Path(layout.root).glob("b4_closed_critic_consumption_*.json"))
    assert len(records) == 1


def test_b4_trigger_proposal_rejects_unbound_hash_and_self_reported_reverse():
    receipt_sha256 = "a" * 64
    mismatch = _b4_trigger_proposal("b" * 64)
    with pytest.raises(L.B4ProtocolError, match="differs from terminal"):
        T.load_proposal_file(
            _write_json(mismatch, "b4-trigger-mismatch.json"),
            b4_reflux_ablation=True,
            b4_closed_critic_receipt_sha256=receipt_sha256,
        )
    self_reported = _b4_trigger_proposal(receipt_sha256)
    self_reported["prior_critic_reverse"] = False
    with pytest.raises(L.B4ProtocolError, match="must not self-report"):
        T.load_proposal_file(
            _write_json(self_reported, "b4-trigger-self-report.json"),
            b4_reflux_ablation=True,
            b4_closed_critic_receipt_sha256=receipt_sha256,
        )


def test_b4_trigger_gate_gets_site_resolved_cfg_and_failure_is_write_free_m17(
        tmp_path, monkeypatch):
    raw_cfg = T.default_cfg(
        reflux=True, b4_reflux_ablation=True,
        _b4_launch_context=_B4_TEST_CONTEXT,
    )
    site = site_policy.PEGASUS_COMPUTE
    contract = T._admit_env_contract(site)
    expected_cfg = T._campaign_cfg_for_site(
        raw_cfg, site, _contract=contract,
    )
    expected_cfg = ident.bind_admission_policy(
        expected_cfg, _CODER_CONTEXT.policy,
    )
    expected_id = str(ident.campaign_id(expected_cfg))
    assert expected_id != str(ident.campaign_id(raw_cfg))
    layout = CampaignLayout(root=str(tmp_path / "resolved-gate-failure")).ensure()
    _seed_trigger_b4_continuation(layout)
    receipt_path = tmp_path / "terminal.json"
    receipt_path.write_bytes(b"certified-shaped-but-rejected")
    observed_ids = []

    def rejecting_gate(gate_cfg, _layout, _state, **_kwargs):
        observed_ids.append(str(ident.campaign_id(gate_cfg)))
        if observed_ids[-1] != expected_id:
            raise AssertionError("gate received the pre-site cfg")
        raise L.B4ProtocolError("trigger gate sentinel")

    fold_spy = mock.Mock()
    candidate_spy = mock.Mock()
    monkeypatch.setattr(T, "exploration_campaign_layout", lambda _id: layout)
    monkeypatch.setattr(T, "_assert_resume_allowed", lambda *_a, **_k: None)
    monkeypatch.setattr(L, "require_b4_iteration_authorization", rejecting_gate)
    monkeypatch.setattr(L, "_fold_critic_reverse", fold_spy)
    monkeypatch.setattr(T, "_run_one_iteration_resolved", candidate_spy)
    before = _b4_file_tree_bytes(layout.root)
    with pytest.raises(L.B4ProtocolError, match="trigger gate sentinel"):
        T.drive_iteration(
            raw_cfg, T.default_perf(), _planner(),
            T.CoderProposalTriggerGating(T.MARKER_ID, _CLEAN_WIRE),
            AuditorVerdict("pass", "a" * 64), None,
            sub="unused", do_build=True, layout=layout,
            build_context=_CODER_CONTEXT,
            b4_closed_critic_receipt=receipt_path,
            b4_proposal_receipt_sha256=hashlib.sha256(
                receipt_path.read_bytes()
            ).hexdigest(),
            _resolved_site=site,
            _contract=contract,
            _b4_launch_context=_b4_production_context(
                expected_cfg, site=site,
            ),
        )
    assert observed_ids == [expected_id]
    assert fold_spy.call_count == 0
    assert candidate_spy.call_count == 0
    assert _b4_file_tree_bytes(layout.root) == before
    assert not os.path.exists(T._provenance_path(layout))
    assert not os.path.exists(layout.wal_file)


def test_b4_trigger_no_build_and_fixture_routes_are_write_free(
        tmp_path, monkeypatch):
    cfg = T.default_cfg(
        b4_reflux_ablation=True,
        _b4_launch_context=_B4_TEST_CONTEXT,
    )
    layout = CampaignLayout(root=str(tmp_path / "no-build-trigger")).ensure()
    monkeypatch.setattr(T, "_current_site", lambda: site_policy.OTHER)
    monkeypatch.setattr(T, "exploration_campaign_layout", lambda _id: layout)
    monkeypatch.setattr(L, "exploration_campaign_layout", lambda _id: layout)
    before = _b4_file_tree_bytes(layout.root)
    with pytest.raises(L.B4ProtocolError, match="forbids --no-build"):
        T.drive_iteration(
            cfg, T.default_perf(), _planner(),
            T.CoderProposalTriggerGating(T.MARKER_ID, _CLEAN_WIRE),
            AuditorVerdict("pass", "a" * 64), None,
            sub="unused", do_build=False, layout=layout,
            _b4_launch_context=_b4_production_context(cfg),
        )
    assert _b4_file_tree_bytes(layout.root) == before

    from orchestrator.campaign import patchharness
    pinned_spy = mock.Mock()
    candidate_spy = mock.Mock()
    monkeypatch.setattr(patchharness, "assert_pinned_clean", pinned_spy)
    monkeypatch.setattr(T, "drive_iteration", candidate_spy)
    with pytest.raises(L.B4ProtocolError, match="forbids --no-build"):
        T.main(["--b4-reflux-ablation", "--no-build"])
    with pytest.raises(L.B4ProtocolError, match="fixture run_one_iteration"):
        T.main(["--b4-reflux-ablation"])
    assert pinned_spy.call_count == 0
    assert candidate_spy.call_count == 0


def test_b4_trigger_cli_receipt_is_continuation_only(tmp_path):
    receipt = tmp_path / "terminal.json"
    with pytest.raises(L.B4ProtocolError, match="requires --run-iteration"):
        T.main(["--b4-closed-critic-receipt", str(receipt)])
    with pytest.raises(L.B4ProtocolError, match="requires --b4-reflux-ablation"):
        T.main([
            "--run-iteration", str(tmp_path / "proposal.json"),
            "--b4-closed-critic-receipt", str(receipt),
        ])


if __name__ == "__main__":
    import pytest as _pytest
    raise SystemExit(_pytest.main([__file__, "-v"]))
