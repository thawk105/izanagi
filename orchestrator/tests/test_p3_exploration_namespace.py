# -*- coding: utf-8 -*-
"""P3 s4 family の exploration campaign namespace 配線テスト。"""
from __future__ import annotations

import ast
import argparse
import contextlib
import dataclasses
import importlib
import os
import stat
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


pytestmark = pytest.mark.usefixtures("ratified_enforcement_source")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import ident, layout as layout_module, wal            # noqa: E402
from orchestrator.campaign import env_contract                                  # noqa: E402
from orchestrator.campaign import patchharness                                  # noqa: E402
from orchestrator.campaign import p3_autonomous_workload_trial as AUTONOMOUS     # noqa: E402
from orchestrator.campaign import p3_s4_loop as LOOP                             # noqa: E402
from orchestrator.campaign import p3_s4_loop_sort as SORT                        # noqa: E402
from orchestrator.campaign import sort_swo_oracle as SWO                         # noqa: E402
from orchestrator.campaign import p3_s4_loop_trigger_gating as TRIGGER           # noqa: E402
from orchestrator.campaign.build_admission import (BuildAdmissionError, BuildRunContext, GeneratorId,  # noqa: E402
                                      add_coder_build_authority_argument,
                                      build_run_context)
from orchestrator.campaign.layout import exploration_campaign_layout             # noqa: E402
from campaign_lock_test_support import build_v2_lock                 # noqa: E402


_CAMPAIGN_ROOT = Path(__file__).resolve().parents[1] / "campaign"


def _call_name(call):
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _call_nodes(tree, name):
    return [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _call_name(node) == name
    ]


def _call_names(tree):
    return {
        name for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        for name in [_call_name(node)]
        if name is not None
    }


def _has_run_campaign_call(tree):
    return bool(_call_nodes(tree, "run_campaign"))


def _is_campaign_root_creator(tree):
    """AST の実体で exploration campaign root producer を見つける。"""
    calls = _call_names(tree)
    return (
        "exploration_campaign_layout" in calls
        and (
            _has_run_campaign_call(tree)
            or "CampaignLayout" in calls
        )
    )


def _module_level_declared_use_class(tree):
    for node in tree.body:
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        if any(
                isinstance(target, ast.Name)
                and target.id == "DECLARED_USE_CLASS"
                for target in targets
        ):
            value = node.value
            return value.value if isinstance(value, ast.Constant) else None
    return None


def _campaign_driver_is_closed(tree):
    """実際の campaign-root 閉包検査を返す。fixture もこの経路を使う。"""
    if not _is_campaign_root_creator(tree):
        return True
    if _module_level_declared_use_class(tree) != "exploration":
        return False
    for call in _call_nodes(tree, "run_campaign"):
        selectors = [
            keyword.value for keyword in call.keywords
            if keyword.arg == "declared_use_class"
        ]
        if len(selectors) != 1:
            return False
        if not isinstance(selectors[0], ast.Name):
            return False
        if selectors[0].id != "DECLARED_USE_CLASS":
            return False
    return True


def _discover_campaign_drivers(campaign_root=None, *, import_modules=True):
    campaign_root = _CAMPAIGN_ROOT if campaign_root is None else Path(campaign_root)
    drivers = []
    for source in sorted(campaign_root.glob("*.py")):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        if not _is_campaign_root_creator(tree):
            continue
        module = None
        if import_modules:
            module = importlib.import_module(
                f"orchestrator.campaign.{source.stem}"
            )
        drivers.append((source.stem, module, tree))
    return tuple(drivers)


_CAMPAIGN_DRIVERS = _discover_campaign_drivers()
_RUN_CAMPAIGN_DRIVERS = tuple(
    driver for driver in _CAMPAIGN_DRIVERS if _has_run_campaign_call(driver[2])
)
_ITERATION_DRIVERS = tuple(
    driver[:2] for driver in _RUN_CAMPAIGN_DRIVERS
    if hasattr(driver[1], "run_one_iteration")
)
_MAIN_DRIVERS = tuple(
    driver[:2] for driver in _RUN_CAMPAIGN_DRIVERS
    if not hasattr(driver[1], "run_one_iteration")
)
_EXPECTED_CALL_COUNTS = {
    "p3_autonomous_workload_trial": (1, 0),
    "p3_kickoff": (1, 2),
    "p3_s4_loop": (6, 1),
    "p3_s4_loop_sort": (5, 1),
    "p3_s4_loop_trigger_gating": (5, 1),
    "p3_s4_red": (1, 2),
}
_PARSER = argparse.ArgumentParser()
add_coder_build_authority_argument(_PARSER)
_AUTHORITY = _PARSER.parse_args(["--allow-coder-derived-build"]).coder_build_authority
_CODER_CONTEXT = build_run_context(
    generator_id=GeneratorId.BACKOFF_SWEEP, coder_authority=_AUTHORITY,
)


@pytest.fixture(autouse=True)
def _stub_real_sort_swo_oracle(monkeypatch):
    receipt = SWO.OracleReceipt(
        SWO.ORACLE_CONTRACT_ID, "1" * 64, "2" * 64,
        SWO.CORPUS_ID, SWO.CORPUS_VERSION,
        "/fixture/cxx", "fixture-cxx 1", SWO.COMPILE_FLAGS_SHA256,
        "3" * 64, SWO.TU_TEMPLATE_SHA256,
        "/fixture/dependency", "4" * 64,
        SWO.DEPENDENCY_MANIFEST_SHA256,
    )
    passed = SWO.SortSwoOracleResult(
        SWO.OracleStatus.PASS, "1" * 64, "2" * 64, receipt=receipt,
    )
    monkeypatch.setattr(
        SWO, "check_materialized_sort_swo", lambda *_a, **_k: passed,
    )


@pytest.mark.parametrize(
    "name,module", [(case[0], case[1]) for case in _CAMPAIGN_DRIVERS],
    ids=[case[0] for case in _CAMPAIGN_DRIVERS],
)
def test_coder_driver_without_flag_rejects_before_build_spy(name, module, monkeypatch):
    """M2: 各 coder CLI の既定拒否を、materialization 以前の単一理由で固定する。"""
    reached = []
    if hasattr(module, "run_campaign"):
        monkeypatch.setattr(
            module, "run_campaign", lambda *_a, **_k: reached.append("campaign"),
        )
    if hasattr(module, "run_one_iteration"):
        monkeypatch.setattr(
            module, "run_one_iteration",
            lambda *_a, **_k: reached.append("iteration"),
        )
    argv = []
    if module is AUTONOMOUS:
        monkeypatch.setattr(
            module, "_assert_build_site_opted_in", lambda *_a, **_k: None,
        )
        monkeypatch.setattr(
            module, "run_trial", lambda *_a, **_k: reached.append("trial"),
        )
        argv = ["--trial-id", "fixture", "--provider", "claude-headless"]
    with pytest.raises(BuildAdmissionError, match="明示 opt-in"):
        module.main(argv)
    assert reached == [], f"{name}: flag 無しで build spy に到達した"


class _BuildSpyReached(RuntimeError):
    pass


@pytest.mark.parametrize(
    "name,module", [(case[0], case[1]) for case in _RUN_CAMPAIGN_DRIVERS],
    ids=[case[0] for case in _RUN_CAMPAIGN_DRIVERS],
)
def test_coder_driver_flag_reaches_build_spy_with_exact_run_context(
        name, module, monkeypatch, tmp_path,
        _activate_synthetic_env_authority):
    """各 coder CLI の正例は exact CODER_DERIVED/opt-in true だけを検査する。"""
    from orchestrator.campaign import p2_2

    seen = []

    def capture(*_args, **kwargs):
        context = kwargs["build_context"]
        seen.append((type(context), context.policy.as_preimage()["coder_authority"]))
        raise _BuildSpyReached(name)

    monkeypatch.setattr(p2_2, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(patchharness, "assert_pinned_clean", lambda *_a, **_k: None)
    monkeypatch.setattr(
        patchharness, "applied", lambda *_a, **_k: contextlib.nullcontext(),
    )

    argv = ["--allow-coder-derived-build"]
    if module in {LOOP, SORT, TRIGGER}:
        monkeypatch.setattr(module, "run_campaign", capture)
        monkeypatch.setattr(
            module, "exploration_campaign_layout",
            lambda campaign_id: exploration_campaign_layout(
                campaign_id, str(tmp_path / name)),
        )
        passed = SimpleNamespace(passed=True)
        monkeypatch.setattr(
            LOOP, "quarantine",
            lambda *_a, **_k: (passed, "", "", "fixture"),
        )
        if module in {SORT, TRIGGER}:
            argv.append("--no-isolate-worktree")
        if module is TRIGGER:
            contract = dataclasses.replace(
                env_contract.GENERATIONS["linux-baremetal"][0].contract,
                env_tag="test", numactl=(),
            )
            _activate_synthetic_env_authority(
                contract,
                repo_root=Path(__file__).resolve().parents[2],
                authority_dir=tmp_path / "authority",
            )
            monkeypatch.setattr(
                module, "_admit_env_contract",
                lambda _site: contract,
            )
    else:
        monkeypatch.setattr(module, "_assert_single_tenant", lambda: None)
        monkeypatch.setattr(module, "assert_pinned_clean", lambda *_a, **_k: None)
        monkeypatch.setattr(
            module, "applied", lambda *_a, **_k: contextlib.nullcontext(),
        )
        monkeypatch.setattr(module, "run_campaign", capture)
    with pytest.raises(_BuildSpyReached, match=name):
        module.main(argv)
    assert seen == [(BuildRunContext, "cli-opt-in")]


def test_autonomous_coder_driver_flag_reaches_trial_with_site_bound_authority(
        monkeypatch, tmp_path):
    from orchestrator.calibrator import runner as calibrator_runner

    seen = []

    def capture(**kwargs):
        context = build_run_context(
            generator_id=GeneratorId.S8A_TRIGGER_SWEEP,
            coder_authority=kwargs["coder_authority"],
        )
        seen.append((type(context), context._coder_entrypoint_site))
        return {"status": "complete", "cells": []}

    monkeypatch.setattr(
        AUTONOMOUS, "_assert_build_site_opted_in", lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        AUTONOMOUS, "_trial_launch_admission", lambda **_k: SimpleNamespace(),
    )
    monkeypatch.setattr(
        AUTONOMOUS, "checkout",
        lambda *_a, **_k: contextlib.nullcontext(str(tmp_path / "ccbench")),
    )
    monkeypatch.setattr(calibrator_runner, "competing_bench_pids", lambda: [])
    monkeypatch.setattr(AUTONOMOUS, "run_trial", capture)
    assert AUTONOMOUS.main([
        "--trial-id", "fixture",
        "--provider", "claude-headless",
        "--allow-unregistered-exploratory",
        "--allow-coder-derived-build",
        "--run-root", str(tmp_path / "run"),
        "--ccbench-dir", str(tmp_path / "ccbench"),
    ]) == 0
    assert seen == [(
        BuildRunContext,
        "orchestrator.campaign.p3_autonomous_workload_trial.main",
    )]


def _spy_driver_layout(monkeypatch, tmp_path, module):
    roots = []

    def derive(campaign_id):
        derived = exploration_campaign_layout(campaign_id, str(tmp_path))
        roots.append(Path(derived.root))
        return derived

    monkeypatch.setattr(module, "exploration_campaign_layout", derive)
    return roots


@pytest.mark.parametrize(
    "name,module", _ITERATION_DRIVERS,
    ids=[case[0] for case in _ITERATION_DRIVERS],
)
def test_iteration_public_entry_routes_runtime_layout_and_selector(
        monkeypatch, tmp_path, name, module):
    """public `run_one_iteration` が実際に導出した root と sink selector を検査。"""
    roots = _spy_driver_layout(monkeypatch, tmp_path, module)
    selectors = []

    def run_sink(*run_args, **kwargs):
        selectors.append(kwargs.get("declared_use_class"))
        cfg = run_args[0]
        campaign_id = str(ident.campaign_id(cfg))
        sink_layout = module.exploration_campaign_layout(campaign_id).ensure()
        wal.write_lock(sink_layout, build_v2_lock(
            ident.canonical_preimage(cfg)
        ))
        Path(sink_layout.wal_file).touch(exist_ok=True)
        return SimpleNamespace(results=[], skipped=0)

    monkeypatch.setattr(module, "run_campaign", run_sink)
    monkeypatch.setattr(
        patchharness, "applied", lambda *_a, **_k: contextlib.nullcontext())
    planner = LOOP.PlannerProposal(
        axis=LOOP.MARKER_ID, direction="increase", magnitude="small")
    state = LOOP.LoopState()
    if module is LOOP:
        template = '''#pragma once
#include "atomic_tool.hh"
class Backoff {
 public:
  static void backoff(size_t clocks_per_us) {
    uint64_t start(rdtscp()), stop;
    // EVOLVE-BLOCK-BEGIN silo-backoff-magnitude
    // fixture
#if BACKOFF_FIXED >= 0
    double now_backoff = static_cast<double>(BACKOFF_FIXED);
#else
    double now_backoff = Backoff_.load(std::memory_order_acquire);
#endif
    // EVOLVE-BLOCK-END silo-backoff-magnitude
    while (stop - start < clocks_per_us * now_backoff) stop = rdtscp();
  }
};
'''
        coder = LOOP.CoderProposal(
            axis=LOOP.MARKER_ID, value=20.0,
            implementation="double now_backoff = 20.0;",
        )
        cfg, perf = module.default_cfg(), module.default_perf()
    else:
        if module is SORT:
            template = '''#pragma once
#include "storage.hh"
class TxExecutor {
 public:
  bool validationPhase() {
#ifndef SORT_VARIANT
#error "SORT_VARIANT must be defined"
#endif
    // EVOLVE-BLOCK-BEGIN silo-writeset-sort
    // fixture
#if SORT_VARIANT
    sort(write_set_.begin(), write_set_.end());
#else
    sort(write_set_.begin(), write_set_.end());
#endif
    // EVOLVE-BLOCK-END silo-writeset-sort
    return true;
  }
};
'''
            coder = module.CoderProposalSort(
                axis=module.MARKER_ID,
                implementation=(
                    "    sort(write_set_.begin(), write_set_.end(),\n"
                    "         [](const auto& a, const auto& b) { "
                    "return a.key_ < b.key_; });"
                ),
            )
            cfg, perf = module.default_cfg(), module.default_perf()
        else:
            template = '''#pragma once
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
  // fixture
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
'''
            coder = module.CoderProposalTriggerGating(
                axis=module.MARKER_ID,
                wire="10100",
            )
            planner = LOOP.PlannerProposal(
                axis=module.MARKER_ID,
                direction="increase",
                magnitude="small",
            )
            cfg, perf = module.default_cfg(), module.default_perf()
            monkeypatch.setattr(module, "_current_site", lambda: module.site_policy.OTHER)

    cfg = ident.bind_admission_policy(cfg, _CODER_CONTEXT.policy)
    if module is TRIGGER:
        contract = env_contract.lookup(module.ENV_TAG)
        monkeypatch.setattr(module, "_lookup", lambda _env_tag: contract)
        cfg = ident.bind_environment_contract(cfg, contract)
    sub = tmp_path / f"{name}-sub"
    source = sub / module.SOURCE_REL
    source.parent.mkdir(parents=True)
    source.write_text(template, encoding="utf-8")
    if module is LOOP:
        module.run_one_iteration(
            cfg, perf, planner, coder, state, str(sub), True,
            build_context=_CODER_CONTEXT, log=lambda *_: None)
    else:
        implementation = (
            coder.implementation
            if module is SORT
            else module.emit_predicate(module.parse_wire(coder.wire))
        )
        preview = LOOP.quarantine(
            str(sub), implementation, marker_id=module.MARKER_ID,
            source_rel=module.SOURCE_REL, write=False,
        )
        assert preview[0].passed
        auditor = module.AuditorVerdict(
            verdict="pass", diff_digest=module.compute_diff_digest(preview[3]))
        module.run_one_iteration(
            cfg, perf, planner, coder, auditor, state, str(sub), True,
            build_context=_CODER_CONTEXT, log=lambda *_: None)
    campaign_id = str(ident.campaign_id(cfg))
    expected = tmp_path / "exploration" / "campaigns" / campaign_id
    assert roots and set(roots) == {expected}
    assert expected.is_dir()
    assert (tmp_path / "exploration" / "namespace.json").read_bytes() == \
        b'{"namespace":"exploration"}\n'
    assert selectors == ["exploration"]
    assert not (tmp_path / "campaigns" / campaign_id).exists()


@pytest.mark.parametrize(
    "name,module", _MAIN_DRIVERS,
    ids=[case[0] for case in _MAIN_DRIVERS],
)
def test_main_public_entry_routes_runtime_layout_and_selector(
        monkeypatch, tmp_path, name, module):
    """public `main` を起動し、heavy build/run sink のみ fake にして配線を見る。"""
    roots = _spy_driver_layout(monkeypatch, tmp_path, module)
    selectors = []

    def run_sink(*run_args, **kwargs):
        selectors.append(kwargs.get("declared_use_class"))
        cfg = run_args[0]
        campaign_id = str(ident.campaign_id(cfg))
        sink_layout = module.exploration_campaign_layout(campaign_id).ensure()
        wal.write_lock(sink_layout, build_v2_lock(
            ident.canonical_preimage(cfg)
        ))
        Path(sink_layout.wal_file).touch(exist_ok=True)
        return SimpleNamespace(results=[], skipped=0)

    monkeypatch.setattr(module, "run_campaign", run_sink)
    monkeypatch.setattr(module, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(module, "assert_pinned_clean", lambda *_a, **_k: None)
    monkeypatch.setattr(
        module, "applied", lambda *_a, **_k: contextlib.nullcontext())
    # fake run sink は directory を作らないため、後半の read-only WAL
    # 機械判定が実 helper で導出した layout を触れるよう spy 側で保証する。
    original_spy = module.exploration_campaign_layout

    def ensured_spy(campaign_id):
        return original_spy(campaign_id).ensure()

    monkeypatch.setattr(module, "exploration_campaign_layout", ensured_spy)
    assert module.main(["--allow-coder-derived-build"]) == 1
    policy_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    cfg = ident.bind_admission_policy(module._cfg(), policy_context.policy)
    cfg = ident.bind_environment_contract(
        cfg, env_contract.lookup(module.ENV_TAG),
    )
    campaign_id = str(ident.campaign_id(cfg))
    expected = tmp_path / "exploration" / "campaigns" / campaign_id
    assert roots and set(roots) == {expected}
    assert selectors == ["exploration", "exploration"]
    assert not (tmp_path / "campaigns" / campaign_id).exists()


@pytest.mark.parametrize(
    "name,module,tree", _CAMPAIGN_DRIVERS,
    ids=[case[0] for case in _CAMPAIGN_DRIVERS],
)
def test_driver_ast_supplements_runtime_namespace_gate(
        name, module, tree):
    """宣言を起点に族を閉包し、operative kill の唯一根拠にはしない。"""
    assert _is_campaign_root_creator(tree), name
    assert _campaign_driver_is_closed(tree), name
    expected_layout_count, expected_run_count = _EXPECTED_CALL_COUNTS[name]
    layout_calls = _call_nodes(tree, "exploration_campaign_layout")
    assert len(layout_calls) == expected_layout_count, name
    run_calls = _call_nodes(tree, "run_campaign")
    assert len(run_calls) == expected_run_count, name
    for call in run_calls:
        contexts = [keyword.value for keyword in call.keywords
                    if keyword.arg == "build_context"]
        assert len(contexts) == 1, name


def test_campaign_root_declaration_meta_gate_has_negative_and_positive_fixtures(
        tmp_path):
    """新しい root producer の宣言漏れを落とし、宣言済み producer を通す。"""
    body = """
from orchestrator.campaign import layout
from orchestrator.campaign import loop

def main():
    loop.run_campaign(
        None, (), None, None, None, declared_use_class=DECLARED_USE_CLASS,
    )
    layout.exploration_campaign_layout("fixture")
    layout.CampaignLayout(root="fixture")
"""
    fixture = tmp_path / "fixture_driver.py"
    fixture.write_text(body, encoding="utf-8")
    missing_drivers = _discover_campaign_drivers(
        tmp_path, import_modules=False,
    )
    assert [name for name, _module, _tree in missing_drivers] == [
        "fixture_driver",
    ]
    name, _module, missing = missing_drivers[0]
    assert _is_campaign_root_creator(missing)
    assert not _campaign_driver_is_closed(missing), name

    fixture.write_text("DECLARED_USE_CLASS = 'exploration'\n" + body,
                       encoding="utf-8")
    declared_drivers = _discover_campaign_drivers(
        tmp_path, import_modules=False,
    )
    assert [name for name, _module, _tree in declared_drivers] == [
        "fixture_driver",
    ]
    name, _module, declared = declared_drivers[0]
    assert _is_campaign_root_creator(declared)
    assert _campaign_driver_is_closed(declared), name


def test_exploration_marker_is_atomically_published_and_directory_synced(
        monkeypatch, tmp_path):
    """F3: exact temp のfile fsync→no-overwrite link→directory fsync の順を固定。"""
    observed = []
    real_fsync = layout_module.os.fsync
    real_link = layout_module.os.link

    def fsync(fd):
        mode = os.fstat(fd).st_mode
        observed.append("directory-fsync" if stat.S_ISDIR(mode) else "file-fsync")
        return real_fsync(fd)

    def link(source, marker):
        assert observed == ["file-fsync"]
        assert not Path(marker).exists()
        assert Path(source).read_bytes() == b'{"namespace":"exploration"}\n'
        observed.append("link")
        return real_link(source, marker)

    monkeypatch.setattr(layout_module.os, "fsync", fsync)
    monkeypatch.setattr(layout_module.os, "link", link)
    marker = Path(layout_module.ensure_exploration_namespace(str(tmp_path)))
    assert marker.read_bytes() == b'{"namespace":"exploration"}\n'
    assert observed == ["file-fsync", "link", "directory-fsync"]


def test_exploration_marker_publish_failure_removes_unique_temp(monkeypatch, tmp_path):
    """F3: atomic publish 例外で partial marker/temp を残さない。"""
    def fail_link(_source, _marker):
        raise OSError("injected link failure")

    monkeypatch.setattr(layout_module.os, "link", fail_link)
    with pytest.raises(OSError, match="injected link failure"):
        layout_module.ensure_exploration_namespace(str(tmp_path))
    assert not (tmp_path / "namespace.json").exists()
    assert list(tmp_path.glob(".namespace.*.tmp")) == []


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
