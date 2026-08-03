# -*- coding: utf-8 -*-
"""P3 s4 family の exploration campaign namespace 配線テスト。"""
from __future__ import annotations

import ast
import argparse
import contextlib
import inspect
import os
import stat
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import ident, layout as layout_module                 # noqa: E402
from campaign import patchharness                                  # noqa: E402
from campaign import p3_kickoff as KICKOFF                          # noqa: E402
from campaign import p3_s4_loop as LOOP                             # noqa: E402
from campaign import p3_s4_loop_sort as SORT                        # noqa: E402
from campaign import p3_s4_loop_trigger_gating as TRIGGER           # noqa: E402
from campaign import p3_s4_red as RED                               # noqa: E402
from campaign.build_admission import (BuildAdmissionError, BuildRunContext, GeneratorId,  # noqa: E402
                                      add_coder_build_authority_argument,
                                      build_run_context)
from campaign.layout import exploration_campaign_layout             # noqa: E402


_DRIVERS = (
    ("loop", LOOP, LOOP.default_cfg, 1, 5),
    ("sort", SORT, SORT.default_cfg, 1, 5),
    ("trigger_gating", TRIGGER, TRIGGER.default_cfg, 1, 5),
    ("red", RED, RED._cfg, 2, 1),
    ("kickoff", KICKOFF, KICKOFF._cfg, 2, 1),
)
_PARSER = argparse.ArgumentParser()
add_coder_build_authority_argument(_PARSER)
_AUTHORITY = _PARSER.parse_args(["--allow-coder-derived-build"]).coder_build_authority
_CODER_CONTEXT = build_run_context(
    generator_id=GeneratorId.BACKOFF_SWEEP, coder_authority=_AUTHORITY,
)


@pytest.mark.parametrize(
    "name,module", [(case[0], case[1]) for case in _DRIVERS],
    ids=[case[0] for case in _DRIVERS],
)
def test_coder_driver_without_flag_rejects_before_build_spy(name, module, monkeypatch):
    """M2: 各 coder CLI の既定拒否を、materialization 以前の単一理由で固定する。"""
    reached = []
    monkeypatch.setattr(
        module, "run_campaign", lambda *_a, **_k: reached.append("campaign"),
    )
    if hasattr(module, "run_one_iteration"):
        monkeypatch.setattr(
            module, "run_one_iteration",
            lambda *_a, **_k: reached.append("iteration"),
        )
    with pytest.raises(BuildAdmissionError, match="明示 opt-in"):
        module.main([])
    assert reached == [], f"{name}: flag 無しで build spy に到達した"


class _BuildSpyReached(RuntimeError):
    pass


@pytest.mark.parametrize(
    "name,module", [(case[0], case[1]) for case in _DRIVERS],
    ids=[case[0] for case in _DRIVERS],
)
def test_coder_driver_flag_reaches_build_spy_with_exact_run_context(
        name, module, monkeypatch, tmp_path):
    """各 coder CLI の正例は exact CODER_DERIVED/opt-in true だけを検査する。"""
    from campaign import p2_2

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
    if name in {"loop", "sort", "trigger_gating"}:
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
        if name in {"sort", "trigger_gating"}:
            argv.append("--no-isolate-worktree")
        if name == "trigger_gating":
            monkeypatch.setattr(
                module, "_admit_env_contract",
                lambda _site: SimpleNamespace(env_tag="test", clocks_per_us=1800,
                                              numactl=(), isolation_policy=SimpleNamespace(
                                                  allow_resume=True)),
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


def _spy_driver_layout(monkeypatch, tmp_path, module):
    roots = []

    def derive(campaign_id):
        derived = exploration_campaign_layout(campaign_id, str(tmp_path))
        roots.append(Path(derived.root))
        return derived

    monkeypatch.setattr(module, "exploration_campaign_layout", derive)
    return roots


@pytest.mark.parametrize(
    "name,module", (("loop", LOOP), ("sort", SORT), ("trigger_gating", TRIGGER)),
    ids=("loop", "sort", "trigger_gating"),
)
def test_iteration_public_entry_routes_runtime_layout_and_selector(
        monkeypatch, tmp_path, name, module):
    """public `run_one_iteration` が実際に導出した root と sink selector を検査。"""
    roots = _spy_driver_layout(monkeypatch, tmp_path, module)
    selectors = []

    def run_sink(*_args, **kwargs):
        selectors.append(kwargs.get("campaign_namespace"))
        return SimpleNamespace(results=[], skipped=0)

    monkeypatch.setattr(module, "run_campaign", run_sink)
    monkeypatch.setattr(
        patchharness, "applied", lambda *_a, **_k: contextlib.nullcontext())
    planner = LOOP.PlannerProposal(
        axis=LOOP.MARKER_ID, direction="increase", magnitude="small")
    state = LOOP.LoopState()
    if name == "loop":
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
        if name == "sort":
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
                implementation=(
                    "  izanagi_gate_pass = (izanagi_abort_reason_ != "
                    "IzanagiAbortReason::kNodeVali);"
                ),
            )
            cfg, perf = module.default_cfg(), module.default_perf()
            monkeypatch.setattr(module, "_current_site", lambda: module.site_policy.OTHER)

    cfg = ident.bind_admission_policy(cfg, _CODER_CONTEXT.policy)
    sub = tmp_path / f"{name}-sub"
    source = sub / module.SOURCE_REL
    source.parent.mkdir(parents=True)
    source.write_text(template, encoding="utf-8")
    if name == "loop":
        module.run_one_iteration(
            cfg, perf, planner, coder, state, str(sub), True,
            build_context=_CODER_CONTEXT, log=lambda *_: None)
    else:
        preview = LOOP.quarantine(
            str(sub), coder.implementation, marker_id=module.MARKER_ID,
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
    "name,module", (("red", RED), ("kickoff", KICKOFF)), ids=("red", "kickoff"),
)
def test_main_public_entry_routes_runtime_layout_and_selector(
        monkeypatch, tmp_path, name, module):
    """public `main` を起動し、heavy build/run sink のみ fake にして配線を見る。"""
    roots = _spy_driver_layout(monkeypatch, tmp_path, module)
    selectors = []

    def run_sink(*_args, **kwargs):
        selectors.append(kwargs.get("campaign_namespace"))
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
    campaign_id = str(ident.campaign_id(ident.bind_admission_policy(
        module._cfg(), policy_context.policy,
    )))
    expected = tmp_path / "exploration" / "campaigns" / campaign_id
    assert roots and set(roots) == {expected}
    assert selectors == ["exploration", "exploration"]
    assert not (tmp_path / "campaigns" / campaign_id).exists()


@pytest.mark.parametrize(
    "name,module,_cfg_factory,run_count,layout_count", _DRIVERS,
    ids=[case[0] for case in _DRIVERS],
)
def test_driver_ast_supplements_runtime_namespace_gate(
        name, module, _cfg_factory, run_count, layout_count):
    """Structural sensitivity の補助 AST gate。operative kill の唯一根拠にしない。"""
    tree = ast.parse(inspect.getsource(module))
    layout_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"campaign_layout", "exploration_campaign_layout"}
    ]
    assert len(layout_calls) == layout_count, name
    assert {node.func.id for node in layout_calls} == {"exploration_campaign_layout"}, name

    run_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_campaign"
    ]
    assert len(run_calls) == run_count, name
    for call in run_calls:
        selectors = [
            keyword.value for keyword in call.keywords
            if keyword.arg == "campaign_namespace"
        ]
        assert len(selectors) == 1, name
        assert isinstance(selectors[0], ast.Constant), name
        assert selectors[0].value == "exploration", name
        contexts = [keyword.value for keyword in call.keywords
                    if keyword.arg == "build_context"]
        assert len(contexts) == 1, name


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
