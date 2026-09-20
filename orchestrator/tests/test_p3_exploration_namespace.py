# -*- coding: utf-8 -*-
"""P3 s4 family の exploration campaign namespace 配線テスト。"""
from __future__ import annotations

import ast
import argparse
import contextlib
import dataclasses
import hashlib
import importlib
import inspect
import os
import stat
import sys
import unicodedata
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Literal, Mapping, get_args, get_type_hints

import pytest


pytestmark = pytest.mark.usefixtures("ratified_enforcement_source")

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import buildcache, ident, layout as layout_module, wal  # noqa: E402
from orchestrator.campaign import env_contract, p2_2, site_policy                # noqa: E402
from orchestrator.campaign import patchharness                                  # noqa: E402
from orchestrator.campaign import p3_autonomous_workload_trial as AUTONOMOUS     # noqa: E402
from orchestrator.campaign import p3_s4_loop as LOOP                             # noqa: E402
from orchestrator.campaign import p3_s4_loop_sort as SORT                        # noqa: E402
from orchestrator.campaign import sort_swo_oracle as SWO                         # noqa: E402
from orchestrator.campaign import p3_s4_loop_trigger_gating as TRIGGER           # noqa: E402
from orchestrator.campaign import paper_story_a1_paired as PAPER_STORY           # noqa: E402
from orchestrator.campaign.build_admission import (BuildAdmissionError, BuildRunContext, GeneratorId,  # noqa: E402
                                      add_coder_build_authority_argument,
                                      build_run_context)
from orchestrator.campaign.layout import exploration_campaign_layout             # noqa: E402
from condition_gate_test_support import (                                        # noqa: E402
    SORT_VARIANT_SOURCE,
    TRIGGER_GATING_SOURCE,
    backoff_fixed_source,
    condition_gate_compilers,
    install_condition_gate_build_fixture,
)
from campaign_lock_test_support import build_v2_lock                 # noqa: E402


_CAMPAIGN_ROOT = Path(__file__).resolve().parents[1] / "campaign"
_CAMPAIGN_DRIVER_MARKER = "exploration_campaign_layout"


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


def _discover_campaign_drivers(
        campaign_root=None, *, import_modules=True,
        use_lexical_prefilter: bool = True):
    campaign_root = _CAMPAIGN_ROOT if campaign_root is None else Path(campaign_root)
    drivers = []
    for source in sorted(campaign_root.glob("*.py")):
        source_text = source.read_text(encoding="utf-8")
        if (
                use_lexical_prefilter
                and _CAMPAIGN_DRIVER_MARKER not in unicodedata.normalize(
                    "NFKC", source_text,
                )
        ):
            continue
        tree = ast.parse(source_text)
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
_ALLOW_CODER_BUILD = "--allow-coder-derived-build"
_PAPER_STORY_WORKLOAD_ORDER = (
    "write-heavy",
    "balanced",
    "read-heavy",
)
_PAPER_STORY_REQUIRED_OPTIONS = frozenset({
    "--study-id",
    "--expected-head",
    "--pbs-jobid",
    "--acquisition-receipt",
    "--acquisition-receipt-sha256",
    "--output-root",
    "--cache-root",
    "--result-root",
    "--dependency-prefix",
})


def _install_real_condition_compilers(monkeypatch) -> tuple[str, str]:
    compilers = condition_gate_compilers()
    if compilers is None:
        pytest.skip("condition gate fixture requires real compilers and CMake")
    monkeypatch.setattr(buildcache, "compilers_for_current_site", lambda: compilers)
    return compilers


def _install_driver_condition_gate_fixture(
        monkeypatch, tmp_path: Path, module) -> Path:
    """Give a synthetic public driver a real condition-gate build graph."""
    _install_real_condition_compilers(monkeypatch)
    repo_root = tmp_path / f"{module.__name__.rsplit('.', 1)[-1]}-condition-repo"
    source_root = install_condition_gate_build_fixture(
        repo_root / "external" / "ccbench",
    )
    if module is SORT:
        (source_root / SORT.SOURCE_REL).write_text(
            SORT_VARIANT_SOURCE, encoding="utf-8",
        )
    elif module is TRIGGER:
        (source_root / TRIGGER.SOURCE_REL).write_text(
            TRIGGER_GATING_SOURCE, encoding="utf-8",
        )
    elif module is LOOP:
        (source_root / LOOP.SOURCE_REL).write_text(
            backoff_fixed_source(20), encoding="utf-8",
        )
    elif module.__name__.endswith(".p3_kickoff"):
        (source_root / "include" / "backoff.hh").write_text(
            backoff_fixed_source(50), encoding="utf-8",
        )
    elif module.__name__.endswith(".p3_s4_red"):
        (source_root / "include" / "backoff.hh").write_text(
            backoff_fixed_source(1_000_000_000), encoding="utf-8",
        )
    monkeypatch.setattr(module, "_repo_root", lambda: str(repo_root))
    return source_root


@dataclasses.dataclass(frozen=True)
class DriverContract:
    cli_authority_mode: Literal["coder-opt-in", "no-coder-cli"]
    coder_entrypoint_site: str | None
    expected_generator_id: GeneratorId
    without_opt_in_argv_factory: Callable[[Path], tuple[str, ...]]
    build_spy_argv_factory: Callable[[Path], tuple[str, ...]]
    routing_argv_factory: Callable[[Path], tuple[str, ...]]
    ast_layout_calls: int
    ast_run_campaign_calls: int
    runtime_run_campaign_calls: int
    derive_expected_campaign_ids: Callable[..., tuple[str, ...]]


def _empty_argv(_tmp_path: Path) -> tuple[str, ...]:
    return ()


def _coder_argv(_tmp_path: Path) -> tuple[str, ...]:
    return (_ALLOW_CODER_BUILD,)


def _isolated_coder_argv(_tmp_path: Path) -> tuple[str, ...]:
    return (_ALLOW_CODER_BUILD, "--no-isolate-worktree")


def _autonomous_without_opt_in_argv(_tmp_path: Path) -> tuple[str, ...]:
    return ("--trial-id", "fixture", "--provider", "claude-headless")


def _autonomous_build_argv(tmp_path: Path) -> tuple[str, ...]:
    return (
        "--trial-id", "fixture",
        "--provider", "claude-headless",
        "--allow-unregistered-exploratory",
        _ALLOW_CODER_BUILD,
        "--run-root", str(tmp_path / "run"),
        "--ccbench-dir", str(tmp_path / "ccbench"),
    )


def _paper_story_measure_argv(tmp_path: Path) -> tuple[str, ...]:
    repo_root = PAPER_STORY._repo_root()
    expected_head = "a" * 40
    attempt = tmp_path / "attempt-fixture"
    (attempt / "raw").mkdir(parents=True, exist_ok=True)
    qsub_argv, qsub_options = PAPER_STORY._canonical_qsub_contract(
        repo_root=repo_root,
        study_id=PAPER_STORY.STUDY_ID,
        source_commit=expected_head,
        attempt=attempt,
    )
    source_binding = {
        "measurement_source_commit": expected_head,
        "files": {
            relative: {
                "git_blob_oid": "b" * 40,
                "working_sha256": hashlib.sha256(
                    (repo_root / relative).read_bytes()
                ).hexdigest(),
            }
            for relative in PAPER_STORY.NON_CERTIFYING_SOURCE_RELATIVE_PATHS
        },
        "evidence_level": "source-routed-trace0",
        "artifact_standalone_proof": False,
    }
    intent = {
        "schema_version": PAPER_STORY.SUBMISSION_INTENT_SCHEMA,
        "study_id": PAPER_STORY.STUDY_ID,
        "source_commit": expected_head,
        "attempt_root": os.fspath(attempt),
        "qsub_argv": qsub_argv,
        "qsub_options": qsub_options,
        "source_binding": source_binding,
    }
    intent["intent_sha256"] = PAPER_STORY._submission_intent_digest(intent)
    PAPER_STORY._exclusive_write(PAPER_STORY._attempt_intent_path(attempt), intent)
    acquisition_path = tmp_path / "attempt-fixture.submission.json"
    acquisition_raw = PAPER_STORY._canonical_json_bytes({
        "source_commit": expected_head,
        "attempt_root": os.fspath(attempt),
        "qsub_argv": qsub_argv,
        "qsub_options": qsub_options,
    })
    acquisition_path.write_bytes(acquisition_raw)
    return (
        "measure",
        "--study-id", "paper-story-a1-20260826-sized-v1",
        "--expected-head", expected_head,
        "--pbs-jobid", "12345.fixture",
        "--acquisition-receipt", str(acquisition_path),
        "--acquisition-receipt-sha256", hashlib.sha256(acquisition_raw).hexdigest(),
        "--output-root", str(attempt / "raw" / "campaign-output"),
        "--cache-root", str(attempt / "cache"),
        "--result-root", str(attempt / "raw" / "results"),
        "--dependency-prefix", (
            "/scr/fixture/gflags-install;/scr/fixture/glog-install"
        ),
    )


def _no_expected_campaign_ids(*_args) -> tuple[str, ...]:
    return ()


def _single_expected_campaign_id(cfg) -> tuple[str, ...]:
    return (str(ident.campaign_id(cfg)),)


def _main_expected_campaign_id(module) -> tuple[str, ...]:
    policy_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    cfg = ident.bind_admission_policy(module._cfg(), policy_context.policy)
    cfg = ident.bind_environment_contract(
        cfg, env_contract.lookup(module.ENV_TAG),
    )
    return (str(ident.campaign_id(cfg)),)


def _paper_story_expected_configs(module, runtime_contract):
    assert tuple(module.WORKLOAD_ORDER) == _PAPER_STORY_WORKLOAD_ORDER
    assert tuple(inspect.signature(module.default_campaign_configs).parameters) == ()
    defaults = module.default_campaign_configs()
    assert type(defaults) is tuple
    assert len(defaults) == len(_PAPER_STORY_WORKLOAD_ORDER)
    policy, _policy_sha = module.load_policy()
    expected = []
    for workload_name, default_cfg in zip(_PAPER_STORY_WORKLOAD_ORDER, defaults):
        assert default_cfg.spec_slug == f"paper-story-a1-{workload_name}"
        assert default_cfg.search_tag == "paired"
        cfg = module.campaign_config(
            policy, workload_name, contract=runtime_contract,
            non_certifying=True,
        )
        assert cfg.spec_slug == f"paper-story-a1-{workload_name}"
        assert cfg.search_tag == "paired"
        cfg = p2_2._campaign_cfg_for_site(
            cfg, site_policy.PEGASUS_COMPUTE, runtime_contract,
        )
        expected.append(cfg)
    return tuple(expected)


def _paper_story_expected_campaign_ids(
        module, runtime_contract) -> tuple[str, ...]:
    expected_generator_id = _driver_contract(
        "paper_story_a1_paired", _DRIVER_CONTRACTS,
    ).expected_generator_id
    policy_context = build_run_context(generator_id=expected_generator_id)
    expected = tuple(
        str(ident.campaign_id(
            ident.bind_admission_policy(cfg, policy_context.policy)
        ))
        for cfg in _paper_story_expected_configs(module, runtime_contract)
    )
    assert len(expected) == 3
    assert len(set(expected)) == 3
    return expected


_DRIVER_CONTRACTS = {
    "p3_autonomous_workload_trial": DriverContract(
        cli_authority_mode="coder-opt-in",
        coder_entrypoint_site=(
            "orchestrator.campaign.p3_autonomous_workload_trial.main"
        ),
        expected_generator_id=GeneratorId.S8A_TRIGGER_SWEEP,
        without_opt_in_argv_factory=_autonomous_without_opt_in_argv,
        build_spy_argv_factory=_autonomous_build_argv,
        routing_argv_factory=_autonomous_build_argv,
        ast_layout_calls=1,
        ast_run_campaign_calls=0,
        runtime_run_campaign_calls=0,
        derive_expected_campaign_ids=_no_expected_campaign_ids,
    ),
    "p3_kickoff": DriverContract(
        cli_authority_mode="coder-opt-in",
        coder_entrypoint_site="orchestrator.campaign.p3_kickoff.main",
        expected_generator_id=GeneratorId.BACKOFF_SWEEP,
        without_opt_in_argv_factory=_empty_argv,
        build_spy_argv_factory=_coder_argv,
        routing_argv_factory=_coder_argv,
        ast_layout_calls=1,
        ast_run_campaign_calls=2,
        runtime_run_campaign_calls=2,
        derive_expected_campaign_ids=_main_expected_campaign_id,
    ),
    "p3_s4_loop": DriverContract(
        cli_authority_mode="coder-opt-in",
        coder_entrypoint_site="orchestrator.campaign.p3_s4_loop.main",
        expected_generator_id=GeneratorId.BACKOFF_SWEEP,
        without_opt_in_argv_factory=_empty_argv,
        build_spy_argv_factory=_coder_argv,
        routing_argv_factory=_coder_argv,
        # B-4 authoritative gate, preflight, and consume-time rebuild add 3 calls.
        # The knowledge receipt site adds 1 call.
        # [T-2795] stock control route adds 1 layout call and 1 run_campaign call (both build_context-bound).
        ast_layout_calls=11,
        ast_run_campaign_calls=2,
        runtime_run_campaign_calls=1,
        derive_expected_campaign_ids=_single_expected_campaign_id,
    ),
    "p3_s4_loop_sort": DriverContract(
        cli_authority_mode="coder-opt-in",
        coder_entrypoint_site="orchestrator.campaign.p3_s4_loop_sort.main",
        expected_generator_id=GeneratorId.BACKOFF_SWEEP,
        without_opt_in_argv_factory=_empty_argv,
        build_spy_argv_factory=_isolated_coder_argv,
        routing_argv_factory=_isolated_coder_argv,
        ast_layout_calls=5,
        ast_run_campaign_calls=1,
        runtime_run_campaign_calls=1,
        derive_expected_campaign_ids=_single_expected_campaign_id,
    ),
    "p3_s4_loop_trigger_gating": DriverContract(
        cli_authority_mode="coder-opt-in",
        coder_entrypoint_site=(
            "orchestrator.campaign.p3_s4_loop_trigger_gating.main"
        ),
        expected_generator_id=GeneratorId.S8A_TRIGGER_SWEEP,
        without_opt_in_argv_factory=_empty_argv,
        build_spy_argv_factory=_isolated_coder_argv,
        routing_argv_factory=_isolated_coder_argv,
        ast_layout_calls=5,
        ast_run_campaign_calls=1,
        runtime_run_campaign_calls=1,
        derive_expected_campaign_ids=_single_expected_campaign_id,
    ),
    "p3_s4_red": DriverContract(
        cli_authority_mode="coder-opt-in",
        coder_entrypoint_site="orchestrator.campaign.p3_s4_red.main",
        expected_generator_id=GeneratorId.BACKOFF_SWEEP,
        without_opt_in_argv_factory=_empty_argv,
        build_spy_argv_factory=_coder_argv,
        routing_argv_factory=_coder_argv,
        ast_layout_calls=1,
        ast_run_campaign_calls=2,
        runtime_run_campaign_calls=2,
        derive_expected_campaign_ids=_main_expected_campaign_id,
    ),
    "paper_story_a1_paired": DriverContract(
        cli_authority_mode="no-coder-cli",
        coder_entrypoint_site=None,
        expected_generator_id=GeneratorId.BACKOFF_SWEEP,
        without_opt_in_argv_factory=_paper_story_measure_argv,
        build_spy_argv_factory=_paper_story_measure_argv,
        routing_argv_factory=_paper_story_measure_argv,
        ast_layout_calls=3,
        ast_run_campaign_calls=2,
        runtime_run_campaign_calls=3,
        derive_expected_campaign_ids=_paper_story_expected_campaign_ids,
    ),
}


def _driver_contract(
        name: str, contracts: Mapping[str, DriverContract]) -> DriverContract:
    return contracts[name]


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


def test_campaign_driver_discovery_names_are_pinned():
    assert tuple(name for name, _module, _tree in _CAMPAIGN_DRIVERS) == (
        "p3_autonomous_workload_trial",
        "p3_kickoff",
        "p3_s4_loop",
        "p3_s4_loop_sort",
        "p3_s4_loop_trigger_gating",
        "p3_s4_red",
        "paper_story_a1_paired",
    )


def test_campaign_driver_lexical_prefilter_matches_unfiltered_bounded_fixture(
        tmp_path):
    fixtures = {
        "alias_call_negative.py": """
from orchestrator.campaign.layout import exploration_campaign_layout as make_layout

def main():
    make_layout("fixture")
    run_campaign()
""",
        "campaign_layout_positive.py": """
def main():
    layout.exploration_campaign_layout("fixture")
    layout.CampaignLayout(root="fixture")
""",
        "comment_only_negative.py": """
# exploration_campaign_layout is documentation, not a call.
def main():
    run_campaign()
""",
        "dynamic_lookup_negative.py": """
def main():
    getattr(layout, "exploration_" + "campaign_layout")("fixture")
    run_campaign()
""",
        "marker_absent_negative.py": """
def main():
    run_campaign()
""",
        "nfkc_positive.py": """
def main():
    layout.ｅxploration_campaign_layout("fixture")
    run_campaign()
""",
        "run_campaign_positive.py": """
def main():
    layout.exploration_campaign_layout("fixture")
    run_campaign()
""",
    }
    nfkc_source = fixtures["nfkc_positive.py"]
    assert _CAMPAIGN_DRIVER_MARKER not in nfkc_source
    assert _CAMPAIGN_DRIVER_MARKER in unicodedata.normalize("NFKC", nfkc_source)
    for filename, source_text in fixtures.items():
        (tmp_path / filename).write_text(source_text, encoding="utf-8")

    filtered = _discover_campaign_drivers(
        tmp_path, import_modules=False, use_lexical_prefilter=True,
    )
    unfiltered = _discover_campaign_drivers(
        tmp_path, import_modules=False, use_lexical_prefilter=False,
    )
    filtered_names = tuple(name for name, _module, _tree in filtered)
    unfiltered_names = tuple(name for name, _module, _tree in unfiltered)
    expected_names = (
        "campaign_layout_positive",
        "nfkc_positive",
        "run_campaign_positive",
    )
    assert filtered_names == unfiltered_names
    assert filtered_names == expected_names


def test_driver_contract_registry_is_exact():
    assert set(_DRIVER_CONTRACTS) == {
        name for name, _module, _tree in _CAMPAIGN_DRIVERS
    }


def test_driver_contract_schema_has_only_required_fields_and_closed_cli_modes():
    fields = dataclasses.fields(DriverContract)
    hints = get_type_hints(DriverContract)
    assert tuple(field.name for field in fields) == (
        "cli_authority_mode",
        "coder_entrypoint_site",
        "expected_generator_id",
        "without_opt_in_argv_factory",
        "build_spy_argv_factory",
        "routing_argv_factory",
        "ast_layout_calls",
        "ast_run_campaign_calls",
        "runtime_run_campaign_calls",
        "derive_expected_campaign_ids",
    )
    assert all(
        field.default is dataclasses.MISSING
        and field.default_factory is dataclasses.MISSING
        for field in fields
    )
    assert get_args(hints["cli_authority_mode"]) == (
        "coder-opt-in", "no-coder-cli",
    )
    assert {contract.cli_authority_mode for contract in _DRIVER_CONTRACTS.values()} == {
        "coder-opt-in", "no-coder-cli",
    }
    for contract in _DRIVER_CONTRACTS.values():
        assert type(contract.expected_generator_id) is GeneratorId
        assert callable(contract.without_opt_in_argv_factory)
        assert callable(contract.build_spy_argv_factory)
        assert callable(contract.routing_argv_factory)
        assert callable(contract.derive_expected_campaign_ids)
        assert type(contract.ast_layout_calls) is int
        assert type(contract.ast_run_campaign_calls) is int
        assert type(contract.runtime_run_campaign_calls) is int
        if contract.cli_authority_mode == "coder-opt-in":
            assert type(contract.coder_entrypoint_site) is str
        else:
            assert contract.coder_entrypoint_site is None


def test_missing_driver_contract_is_hard_failure():
    missing = dict(_DRIVER_CONTRACTS)
    missing.pop("paper_story_a1_paired")
    with pytest.raises(KeyError, match="paper_story_a1_paired"):
        _driver_contract("paper_story_a1_paired", missing)


def _measure_parser(module):
    parser = module._parser()
    subparsers = [
        action for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ]
    assert len(subparsers) == 1
    return subparsers[0].choices["measure"]


def _argv_without_option(
        argv: tuple[str, ...], option: str) -> tuple[str, ...]:
    index = argv.index(option)
    assert index + 1 < len(argv)
    assert not argv[index + 1].startswith("--")
    return argv[:index] + argv[index + 2:]


@pytest.mark.parametrize(
    "name,module", [(case[0], case[1]) for case in _CAMPAIGN_DRIVERS],
    ids=[case[0] for case in _CAMPAIGN_DRIVERS],
)
def test_cli_authority_boundary_rejects_before_build_spy(
        name, module, monkeypatch, tmp_path):
    """Coder opt-in または coder CLI 不在を parser/build 境界で固定する。"""
    contract = _driver_contract(name, _DRIVER_CONTRACTS)
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
    if contract.cli_authority_mode == "no-coder-cli":
        parser = _measure_parser(module)
        option_strings = {
            option
            for action in parser._actions
            for option in action.option_strings
        }
        required_options = {
            option
            for action in parser._actions if action.required
            for option in action.option_strings
        }
        assert required_options == _PAPER_STORY_REQUIRED_OPTIONS
        assert _ALLOW_CODER_BUILD not in option_strings
        argv = contract.without_opt_in_argv_factory(tmp_path)
        for missing_option in sorted(_PAPER_STORY_REQUIRED_OPTIONS):
            with pytest.raises(SystemExit) as rejected:
                module.main(list(_argv_without_option(argv, missing_option)))
            assert rejected.value.code == 2
        with pytest.raises(SystemExit) as rejected:
            module.main([*argv, _ALLOW_CODER_BUILD])
        assert rejected.value.code == 2
        assert reached == [], f"{name}: coder authority の無い CLI が build spy に到達した"
        return

    argv = list(contract.without_opt_in_argv_factory(tmp_path))
    if module is AUTONOMOUS:
        monkeypatch.setattr(
            module, "_assert_build_site_opted_in", lambda *_a, **_k: None,
        )
        monkeypatch.setattr(
            module, "run_trial", lambda *_a, **_k: reached.append("trial"),
        )
    with pytest.raises(BuildAdmissionError, match="明示 opt-in"):
        module.main(argv)
    assert reached == [], f"{name}: flag 無しで build spy に到達した"


class _BuildSpyReached(BaseException):
    pass


class _BuildSpyContractFailure(BaseException):
    pass


class _RoutingSpyContractFailure(BaseException):
    pass


class _ExternalSpyContractFailure(BaseException):
    pass


def _argv_option_map(argv: tuple[str, ...]) -> dict[str, str]:
    assert argv[0] == "measure"
    assert len(argv[1:]) % 2 == 0
    return dict(zip(argv[1::2], argv[2::2]))


def _install_paper_story_external_spies(
        monkeypatch, tmp_path, module, argv: tuple[str, ...], *,
        pin_identity_oracle: bool):
    options = _argv_option_map(argv)
    repo_root = module._repo_root()
    expected_head = options["--expected-head"]
    pbs_jobid = options["--pbs-jobid"]
    attempt = tmp_path / "attempt-fixture"
    output_root = Path(options["--output-root"])
    cache_root = Path(options["--cache-root"])
    result_root = Path(options["--result-root"])
    acquisition_path = Path(options["--acquisition-receipt"])
    runtime_contract = env_contract.lookup("pegasus")
    authorization = SimpleNamespace(
        label="paper-story-test-authorization",
        contract=runtime_contract,
    )
    policy, _policy_sha = module.load_policy()
    if pin_identity_oracle:
        expected_configs = _paper_story_expected_configs(module, runtime_contract)
    else:
        expected_configs = tuple(
            p2_2._campaign_cfg_for_site(
                module.campaign_config(
                    policy, workload_name, contract=runtime_contract,
                    non_certifying=True,
                ),
                site_policy.PEGASUS_COMPUTE,
                runtime_contract,
            )
            for workload_name in _PAPER_STORY_WORKLOAD_ORDER
        )
    driver_contract = _driver_contract(
        "paper_story_a1_paired", _DRIVER_CONTRACTS,
    )
    policy_context = build_run_context(
        generator_id=driver_contract.expected_generator_id,
    )
    expected_configs = tuple(
        ident.bind_admission_policy(cfg, policy_context.policy)
        for cfg in expected_configs
    )
    expected_campaign_ids = tuple(
        str(ident.campaign_id(cfg))
        for cfg in expected_configs
    )
    if pin_identity_oracle:
        assert expected_campaign_ids == (
            driver_contract.derive_expected_campaign_ids(
                module, runtime_contract,
            )
        )
    assert len(set(expected_campaign_ids)) == 3

    expected_pbs_observation = {
        "pbs_jobid": pbs_jobid,
        "pbs_o_host": "fixture-submit-host",
        "pbs_o_workdir": str(repo_root),
    }
    monkeypatch.setenv("PBS_JOBID", expected_pbs_observation["pbs_jobid"])
    monkeypatch.setenv("PBS_O_HOST", expected_pbs_observation["pbs_o_host"])
    monkeypatch.setenv("PBS_O_WORKDIR", expected_pbs_observation["pbs_o_workdir"])

    trusted_roots = {
        "attempt_root": str(attempt),
        "attempt_identity": module._attempt_root_identity(attempt),
        "raw_root": str(attempt / "raw"),
        "output_root": str(output_root),
        "cache_root": str(cache_root),
        "result_root": str(result_root),
        "tmp_root": str(attempt / "raw" / "tmp"),
        "submission_receipt": str(acquisition_path),
        "completion_receipt": str(tmp_path / "attempt-fixture.completion.json"),
        "stdout_path": str(tmp_path / "attempt-fixture.stdout"),
        "stderr_path": str(tmp_path / "attempt-fixture.stderr"),
    }
    reservation_binding = {
        "job_id": pbs_jobid,
        "requested_s": 3600,
        "scheduler_started_epoch": 1000,
        "deadline_epoch": 4600,
        "host": "fixture-compute-host",
        "boot_id": "00000000-0000-0000-0000-000000000000",
        "script_sha256": "d" * 64,
        "nonce": attempt.name,
    }
    expected_dependency_prefix = options["--dependency-prefix"]
    resolved_compilers = ("/fixture/cc", "/fixture/cxx")
    toolchain_manifest = {"fixture": "paper-story-toolchain"}
    expected_git_calls = [
        (repo_root, ("rev-parse", "HEAD")),
        *[
            (repo_root, ("rev-parse", f"{expected_head}:{relative}"))
            for relative in module.NON_CERTIFYING_SOURCE_RELATIVE_PATHS
        ],
        (repo_root, ("rev-parse", "HEAD")),
        (repo_root, ("status", "--porcelain", "--untracked-files=all")),
        (repo_root, ("rev-parse", "HEAD")),
        *[
            (repo_root, ("rev-parse", f"{expected_head}:{relative}"))
            for relative in module.SOURCE_RELATIVE_PATHS
        ],
        (repo_root, ("rev-parse", "HEAD")),
        *[
            (repo_root, ("rev-parse", f"{expected_head}:{relative}"))
            for relative in module.NON_CERTIFYING_SOURCE_RELATIVE_PATHS
        ],
    ]
    calls = {
        "validate_acquisition_receipt": [],
        "validate_measure_environment": [],
        "run_git": [],
        "current_site": [],
        "validated_dependency_prefix": [],
        "reservation_binding": [],
        "resolve_site_runtime": [],
        "assert_matches_calibration": [],
        "compilers_for_current_site": [],
        "observed_toolchain_manifest": [],
        "assert_single_tenant": [],
        "campaign_config": [],
        "default_campaign_configs": [],
    }

    def acquisition_spy(receipt, *args, **kwargs):
        calls["validate_acquisition_receipt"].append((receipt, args, kwargs))
        assert args == ()
        expected_argv, expected_options = module._canonical_qsub_contract(
            repo_root=repo_root,
            study_id=options["--study-id"],
            source_commit=expected_head,
            attempt=attempt,
        )
        assert receipt == {
            "source_commit": expected_head,
            "attempt_root": os.fspath(attempt),
            "qsub_argv": expected_argv,
            "qsub_options": expected_options,
        }
        assert kwargs == {
            "repo_root": repo_root,
            "study_id": options["--study-id"],
            "source_commit": expected_head,
            "request_id": pbs_jobid,
            "pbs_observation": expected_pbs_observation,
            "policy": policy,
        }
        return dict(trusted_roots)

    def run_git_spy(observed_repo_root, *args):
        observed = (observed_repo_root, args)
        calls["run_git"].append(observed)
        index = len(calls["run_git"]) - 1
        assert index < len(expected_git_calls)
        assert observed == expected_git_calls[index]
        if args == ("status", "--porcelain", "--untracked-files=all"):
            return ""
        if args == ("rev-parse", "HEAD"):
            return expected_head
        return "b" * 40

    def current_site_spy(*args, **kwargs):
        calls["current_site"].append((args, kwargs))
        assert args == () and kwargs == {}
        return site_policy.PEGASUS_COMPUTE

    def measure_environment_spy(*args, **kwargs):
        calls["validate_measure_environment"].append((args, kwargs))
        assert args == ()
        assert kwargs == {
            "repo_root": repo_root,
            "expected_head": expected_head,
            "output_root": output_root,
            "cache_root": cache_root,
            "result_root": result_root,
            "pbs_jobid": pbs_jobid,
            "site": site_policy.PEGASUS_COMPUTE,
            "observed_head": expected_head,
            "porcelain": "",
            "attempt_root": attempt,
        }
        return {
            "output_root": str(output_root),
            "cache_root": str(cache_root),
            "result_root": str(result_root),
        }

    def dependency_prefix_spy(value, *args, **kwargs):
        calls["validated_dependency_prefix"].append((value, args, kwargs))
        assert value == expected_dependency_prefix
        assert args == () and kwargs == {"require_scr": True}
        return expected_dependency_prefix

    def reservation_spy(environ, *args, **kwargs):
        calls["reservation_binding"].append((environ, args, kwargs))
        assert environ is os.environ
        assert args == () and kwargs == {}
        return dict(reservation_binding)

    def resolve_runtime_spy(*args, **kwargs):
        calls["resolve_site_runtime"].append((args, kwargs))
        assert args == () and kwargs == {}
        return site_policy.PEGASUS_COMPUTE, runtime_contract, authorization

    def calibration_spy(contract, *args, **kwargs):
        calls["assert_matches_calibration"].append((contract, args, kwargs))
        assert contract is runtime_contract
        assert args == () and kwargs == {}
        return SimpleNamespace(sha256="c" * 64)

    def compilers_spy(*args, **kwargs):
        calls["compilers_for_current_site"].append((args, kwargs))
        assert args == () and kwargs == {}
        return resolved_compilers

    def toolchain_spy(*args, **kwargs):
        calls["observed_toolchain_manifest"].append((args, kwargs))
        assert args == resolved_compilers and kwargs == {}
        return toolchain_manifest

    def single_tenant_spy(*args, **kwargs):
        calls["assert_single_tenant"].append((args, kwargs))
        if args != () or kwargs != {}:
            raise _ExternalSpyContractFailure(
                "_assert_single_tenant arguments differ"
            )

    original_campaign_config = module.campaign_config

    def campaign_config_spy(
            observed_policy, workload_name, *, contract=None, non_certifying):
        calls["campaign_config"].append((workload_name, contract))
        assert len(calls["campaign_config"]) <= len(_PAPER_STORY_WORKLOAD_ORDER)
        assert observed_policy == policy
        assert workload_name in _PAPER_STORY_WORKLOAD_ORDER
        assert contract is runtime_contract
        assert non_certifying is True
        return original_campaign_config(
            observed_policy, workload_name, contract=contract,
            non_certifying=non_certifying,
        )

    def forbidden_default_configs(*args, **kwargs):
        calls["default_campaign_configs"].append((args, kwargs))
        raise AssertionError(
            "run_measurement must not call default_campaign_configs"
        )

    monkeypatch.setattr(module, "validate_acquisition_receipt", acquisition_spy)
    monkeypatch.setattr(module, "_run_git", run_git_spy)
    monkeypatch.setattr(site_policy, "current_site", current_site_spy)
    monkeypatch.setattr(module, "validate_measure_environment", measure_environment_spy)
    monkeypatch.setattr(module, "_validated_dependency_prefix", dependency_prefix_spy)
    monkeypatch.setattr(module, "_reservation_binding_from_environment", reservation_spy)
    monkeypatch.setattr(p2_2, "resolve_site_runtime", resolve_runtime_spy)
    monkeypatch.setattr(p2_2, "_assert_matches_calibration", calibration_spy)
    monkeypatch.setattr(buildcache, "compilers_for_current_site", compilers_spy)
    monkeypatch.setattr(buildcache, "observed_toolchain_manifest", toolchain_spy)
    monkeypatch.setattr(module, "_assert_single_tenant", single_tenant_spy)
    monkeypatch.setattr(module, "campaign_config", campaign_config_spy)
    monkeypatch.setattr(module, "default_campaign_configs", forbidden_default_configs)

    def assert_complete(expected_single_tenant_calls: int):
        assert calls["validate_acquisition_receipt"] and len(
            calls["validate_acquisition_receipt"]
        ) == 1
        assert calls["validate_measure_environment"] and len(
            calls["validate_measure_environment"]
        ) == 1
        assert calls["run_git"] == expected_git_calls
        for label in (
            "current_site",
            "validated_dependency_prefix",
            "reservation_binding",
            "resolve_site_runtime",
            "assert_matches_calibration",
            "compilers_for_current_site",
            "observed_toolchain_manifest",
        ):
            assert calls[label] and len(calls[label]) == 1, label
        assert len(calls["assert_single_tenant"]) == expected_single_tenant_calls
        assert calls["campaign_config"] == [
            (workload_name, runtime_contract)
            for workload_name in _PAPER_STORY_WORKLOAD_ORDER
        ]
        assert calls["default_campaign_configs"] == []

    return SimpleNamespace(
        module=module,
        options=options,
        policy=policy,
        runtime_contract=runtime_contract,
        authorization=authorization,
        expected_configs=expected_configs,
        expected_campaign_ids=expected_campaign_ids,
        expected_generator_id=driver_contract.expected_generator_id,
        expected_dependency_prefix=expected_dependency_prefix,
        output_root=output_root,
        cache_root=cache_root,
        result_root=result_root,
        toolchain_manifest=toolchain_manifest,
        trusted_roots=trusted_roots,
        calls=calls,
        assert_complete=assert_complete,
    )


def _assert_paper_story_run_call(
        harness, index: int, run_args: tuple, kwargs: dict) -> BuildRunContext:
    assert index < len(harness.expected_configs)
    assert len(run_args) == 5
    cfg, observed_genomes, perf, env_tag, clocks_per_us = run_args
    matches = [
        expected_index
        for expected_index, expected_cfg in enumerate(harness.expected_configs)
        if cfg == expected_cfg
    ]
    assert len(matches) == 1
    expected_index = matches[0]
    assert observed_genomes == harness.module.genomes(harness.policy)
    workload_name = _PAPER_STORY_WORKLOAD_ORDER[expected_index]
    assert perf == harness.module.PerfConfig(
        records=harness.policy["scale"]["records"],
        threads=harness.policy["scale"]["threads"],
        workload=harness.module.workload_flags(harness.policy, workload_name),
        extime=harness.policy["scale"]["extime_s"],
        reps=harness.module._expected_reps(harness.policy, workload_name),
    )
    assert env_tag == harness.runtime_contract.env_tag
    assert clocks_per_us == harness.runtime_contract.clocks_per_us
    assert kwargs["output_root"] == str(harness.output_root)
    assert set(kwargs) == {
        "numactl",
        "output_root",
        "cache_root",
        "dependency_prefix",
        "authorization_contract",
        "env_contract",
        "expected_toolchain_manifest",
        "build_context",
        "declared_use_class",
        "capability_resolver",
        "durable_root_policy",
    }
    assert kwargs["numactl"] == list(harness.runtime_contract.numactl)
    assert kwargs["cache_root"] == str(harness.cache_root)
    assert kwargs["dependency_prefix"] == harness.expected_dependency_prefix
    assert kwargs["authorization_contract"] is harness.authorization
    assert kwargs["env_contract"] is harness.runtime_contract
    assert kwargs["expected_toolchain_manifest"] == harness.toolchain_manifest
    assert kwargs["declared_use_class"] == "exploration"
    resolver = kwargs["capability_resolver"]
    assert callable(resolver)
    assert resolver.__kwdefaults__ == {"workload_name": workload_name}
    durable_policy = kwargs["durable_root_policy"]
    assert durable_policy.approved_roots == (harness.output_root.resolve(),)
    assert durable_policy.forbidden_roots == ()
    context = kwargs["build_context"]
    assert type(context) is BuildRunContext
    assert context.generator_id is harness.expected_generator_id
    assert context.policy.as_preimage()["coder_authority"] == "cli-opt-in"
    return context


def _install_paper_story_layout_spy(monkeypatch, module, harness):
    calls = []
    original = module.exploration_campaign_layout

    def layout_spy(*args, **kwargs):
        calls.append((args, kwargs))
        assert len(calls) <= len(harness.expected_campaign_ids)
        assert len(args) == 2
        assert args[0] in harness.expected_campaign_ids
        assert args[1] == str(harness.output_root)
        assert kwargs == {}
        return original(*args, **kwargs)

    monkeypatch.setattr(module, "exploration_campaign_layout", layout_spy)
    return calls


@pytest.mark.parametrize(
    "name,module", [(case[0], case[1]) for case in _RUN_CAMPAIGN_DRIVERS],
    ids=[case[0] for case in _RUN_CAMPAIGN_DRIVERS],
)
def test_driver_build_spy_receives_exact_run_context(
        name, module, monkeypatch, tmp_path,
        _activate_synthetic_env_authority):
    """Coder opt-in の実体と no-coder CLI の authority 不在を分けて検査する。"""
    contract = _driver_contract(name, _DRIVER_CONTRACTS)
    seen = []

    if contract.cli_authority_mode == "no-coder-cli":
        assert module._assert_single_tenant is p2_2._assert_single_tenant
        argv = contract.build_spy_argv_factory(tmp_path)
        harness = _install_paper_story_external_spies(
            monkeypatch, tmp_path, module, argv,
            pin_identity_oracle=False,
        )
        layout_calls = _install_paper_story_layout_spy(
            monkeypatch, module, harness,
        )

        def paper_story_capture(*run_args, **kwargs):
            try:
                assert len(run_args) == 5
                context = kwargs["build_context"]
                assert type(context) is BuildRunContext
                assert context.generator_id is contract.expected_generator_id
                assert context.policy.as_preimage()["coder_authority"] == "cli-opt-in"
                assert context._authority_nonce is None
                assert context._coder_entrypoint_site is None
            except (AssertionError, KeyError) as exc:
                raise _BuildSpyContractFailure(
                    "paper-story build context differs"
                ) from exc
            seen.append(context)
            raise _BuildSpyReached(name)

        monkeypatch.setattr(module, "run_campaign", paper_story_capture)
        with pytest.raises(_BuildSpyReached, match=name):
            module.main(list(argv))
        assert len(seen) == 1
        assert seen[0]._authority_nonce is None
        assert seen[0]._coder_entrypoint_site is None
        assert layout_calls == [
            ((campaign_id, str(harness.output_root)), {})
            for campaign_id in harness.expected_campaign_ids
        ]
        harness.assert_complete(1)
        return

    if hasattr(module, "_require_condition_gate"):
        _install_driver_condition_gate_fixture(
            monkeypatch, tmp_path, module,
        )

    def capture(*_args, **kwargs):
        context = kwargs["build_context"]
        seen.append(context)
        raise _BuildSpyReached(name)

    monkeypatch.setattr(p2_2, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(patchharness, "assert_pinned_clean", lambda *_a, **_k: None)
    monkeypatch.setattr(
        patchharness, "applied", lambda *_a, **_k: contextlib.nullcontext(),
    )

    argv = list(contract.build_spy_argv_factory(tmp_path))
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
        if module is TRIGGER:
            runtime_contract = dataclasses.replace(
                env_contract.GENERATIONS["linux-baremetal"][0].contract,
                env_tag="test", numactl=(),
            )
            _activate_synthetic_env_authority(
                runtime_contract,
                repo_root=Path(__file__).resolve().parents[2],
                authority_dir=tmp_path / "authority",
            )
            monkeypatch.setattr(
                module, "_admit_env_contract",
                lambda _site: runtime_contract,
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
    assert len(seen) == 1
    context = seen[0]
    assert type(context) is BuildRunContext
    assert context.generator_id is contract.expected_generator_id
    assert context.policy.as_preimage()["coder_authority"] == "cli-opt-in"
    assert context._authority_nonce is not None
    assert context._coder_entrypoint_site == contract.coder_entrypoint_site


def test_autonomous_coder_driver_flag_reaches_trial_with_site_bound_authority(
        monkeypatch, tmp_path):
    from orchestrator.calibrator import runner as calibrator_runner

    contract = _driver_contract(
        "p3_autonomous_workload_trial", _DRIVER_CONTRACTS,
    )
    expected_site = "orchestrator.campaign.p3_autonomous_workload_trial.main"
    assert contract.coder_entrypoint_site == expected_site
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
    assert AUTONOMOUS.main(list(
        contract.build_spy_argv_factory(tmp_path)
    )) == 0
    assert seen == [(
        BuildRunContext,
        expected_site,
    )]


def _spy_driver_layout(monkeypatch, tmp_path, module):
    roots = []
    calls = []

    def derive(*args, **kwargs):
        calls.append((args, kwargs))
        campaign_id = args[0]
        derived = exploration_campaign_layout(campaign_id, str(tmp_path))
        roots.append(Path(derived.root))
        return derived

    monkeypatch.setattr(module, "exploration_campaign_layout", derive)
    return roots, calls


@pytest.mark.parametrize(
    "name,module", _ITERATION_DRIVERS,
    ids=[case[0] for case in _ITERATION_DRIVERS],
)
def test_iteration_public_entry_routes_runtime_layout_and_selector(
        monkeypatch, tmp_path, name, module):
    """public `run_one_iteration` が実際に導出した root と sink selector を検査。"""
    contract = _driver_contract(name, _DRIVER_CONTRACTS)
    _install_real_condition_compilers(monkeypatch)
    roots, layout_calls = _spy_driver_layout(monkeypatch, tmp_path, module)
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
            template = SORT_VARIANT_SOURCE
            coder = module.CoderProposalSort(
                axis=module.MARKER_ID,
                implementation=SWO.render_sort_ir(SWO.SortComparatorIr(((
                    SWO.SortIrField.KEY, SWO.SortIrDirection.ASC,
                ),))),
            )
            cfg, perf = module.default_cfg(), module.default_perf()
        else:
            template = TRIGGER_GATING_SOURCE
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
        runtime_contract = env_contract.lookup(module.ENV_TAG)
        monkeypatch.setattr(
            module, "_lookup", lambda _env_tag: runtime_contract,
        )
        cfg = ident.bind_environment_contract(cfg, runtime_contract)
    sub = tmp_path / f"{name}-sub"
    source = sub / module.SOURCE_REL
    source.parent.mkdir(parents=True)
    source.write_text(template, encoding="utf-8")
    install_condition_gate_build_fixture(sub)
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
    expected_campaign_ids = contract.derive_expected_campaign_ids(cfg)
    assert len(expected_campaign_ids) == 1
    campaign_id = expected_campaign_ids[0]
    expected = tmp_path / "exploration" / "campaigns" / campaign_id
    assert roots and set(roots) == {expected}
    assert layout_calls
    assert all(
        args == (campaign_id,) and kwargs == {}
        for args, kwargs in layout_calls
    )
    assert expected.is_dir()
    assert (tmp_path / "exploration" / "namespace.json").read_bytes() == \
        b'{"namespace":"exploration"}\n'
    assert selectors == ["exploration"] * contract.runtime_run_campaign_calls
    assert not (tmp_path / "campaigns" / campaign_id).exists()


@pytest.mark.parametrize(
    "name,module", _MAIN_DRIVERS,
    ids=[case[0] for case in _MAIN_DRIVERS],
)
def test_main_public_entry_routes_runtime_layout_and_selector(
        monkeypatch, tmp_path, name, module):
    """public `main` を起動し、heavy build/run sink のみ fake にして配線を見る。"""
    contract = _driver_contract(name, _DRIVER_CONTRACTS)
    if contract.cli_authority_mode == "no-coder-cli":
        assert module._assert_single_tenant is p2_2._assert_single_tenant
        argv = contract.routing_argv_factory(tmp_path)
        harness = _install_paper_story_external_spies(
            monkeypatch, tmp_path, module, argv,
            pin_identity_oracle=True,
        )
        layout_calls = _install_paper_story_layout_spy(
            monkeypatch, module, harness,
        )
        selectors = []
        observed_campaign_ids = []
        forwarded_output_roots = []
        run_calls = []
        summaries = []

        def paper_story_run_sink(*run_args, **kwargs):
            index = len(run_calls)
            try:
                context = _assert_paper_story_run_call(
                    harness, index, run_args, kwargs,
                )
            except (AssertionError, IndexError, KeyError) as exc:
                raise _RoutingSpyContractFailure(
                    "paper-story routing arguments differ"
                ) from exc
            run_calls.append((run_args, kwargs))
            selectors.append(kwargs["declared_use_class"])
            forwarded_output_roots.append(kwargs["output_root"])
            observed_bound_cfg = ident.bind_admission_policy(
                run_args[0], context.policy,
            )
            campaign_id = str(ident.campaign_id(observed_bound_cfg))
            observed_campaign_ids.append(campaign_id)
            sink_layout = exploration_campaign_layout(
                campaign_id, str(harness.output_root),
            ).ensure()
            wal.write_lock(sink_layout, build_v2_lock(
                ident.canonical_preimage(observed_bound_cfg)
            ))
            Path(sink_layout.wal_file).touch(exist_ok=True)
            summary = SimpleNamespace(
                campaign_id=campaign_id,
                layout_root=sink_layout.root,
                results=[],
                total=2,
                evaluated=2,
                skipped=0,
                identity_skipped=0,
                balanced_schedule_receipt=None,
            )
            summaries.append(summary)
            return summary

        monkeypatch.setattr(module, "run_campaign", paper_story_run_sink)
        assert module.main(list(argv)) == 0
        assert tuple(observed_campaign_ids) == harness.expected_campaign_ids
        assert set(observed_campaign_ids) == set(harness.expected_campaign_ids)
        assert selectors == [
            "exploration"
        ] * contract.runtime_run_campaign_calls
        assert forwarded_output_roots == [
            str(harness.output_root)
        ] * contract.runtime_run_campaign_calls
        assert layout_calls == [
            ((campaign_id, str(harness.output_root)), {})
            for campaign_id in harness.expected_campaign_ids
        ]
        for campaign_id in harness.expected_campaign_ids:
            expected = (
                harness.output_root / "exploration" / "campaigns" / campaign_id
            )
            assert expected.is_dir()
            assert not (harness.output_root / "campaigns" / campaign_id).exists()
        assert len(run_calls) == contract.runtime_run_campaign_calls
        assert [
            summary.balanced_schedule_receipt for summary in summaries
        ] == [None] * contract.runtime_run_campaign_calls
        harness.assert_complete(contract.runtime_run_campaign_calls)
        return

    roots, layout_calls = _spy_driver_layout(monkeypatch, tmp_path, module)
    selectors = []

    if hasattr(module, "_require_condition_gate"):
        _install_driver_condition_gate_fixture(
            monkeypatch, tmp_path, module,
        )

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
    assert module.main(list(contract.routing_argv_factory(tmp_path))) == 1
    expected_campaign_ids = contract.derive_expected_campaign_ids(module)
    assert len(expected_campaign_ids) == 1
    campaign_id = expected_campaign_ids[0]
    expected = tmp_path / "exploration" / "campaigns" / campaign_id
    assert roots and set(roots) == {expected}
    assert layout_calls
    assert all(
        args == (campaign_id,) and kwargs == {}
        for args, kwargs in layout_calls
    )
    assert selectors == ["exploration"] * contract.runtime_run_campaign_calls
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
    contract = _driver_contract(name, _DRIVER_CONTRACTS)
    layout_calls = _call_nodes(tree, "exploration_campaign_layout")
    assert len(layout_calls) == contract.ast_layout_calls, name
    run_calls = _call_nodes(tree, "run_campaign")
    assert len(run_calls) == contract.ast_run_campaign_calls, name
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
