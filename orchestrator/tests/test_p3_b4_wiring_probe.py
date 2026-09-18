# -*- coding: utf-8 -*-
"""Acceptance and mutation-red controls for the B-4 non-sample probe."""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap
from dataclasses import replace

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))

from orchestrator.campaign import contract_loader_binding as B  # noqa: E402
from orchestrator.campaign import p3_b4_wiring_probe as P  # noqa: E402


def _clean_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "TZ": "UTC",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    if extra:
        env.update(extra)
    return env


def _run_child(
    source: str,
    *,
    extra_env: dict[str, str] | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    prefix = (
        "import sys\n"
        f"sys.path.insert(0, {str(_REPO_ROOT)!r})\n"
    )
    return subprocess.run(
        [sys.executable, "-I", "-B", "-c", prefix + textwrap.dedent(source)],
        cwd=_REPO_ROOT,
        env=_clean_env(extra_env),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def _call_allow_read_only_git(
    operation: tuple[str, ...],
    *,
    argv: tuple[str, ...] | None = None,
) -> tuple[bool, P._ProcessGuard]:
    guard = P._ProcessGuard(())
    env = {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
    }
    if argv is None:
        argv = (
            os.fspath(B._GIT_EXECUTABLE),
            *B._GIT_HARDEN,
            "--no-replace-objects",
            "-C", str(_REPO_ROOT),
            *operation,
        )
    argv = list(argv)
    namespace = {
        "__name__": "orchestrator.campaign.contract_loader_binding",
        "audit_args": ("/usr/bin/git", argv, None, env),
        "guard": guard,
    }
    exec(
        "def _run_git():\n"
        "    return guard._allow_read_only_git(audit_args)\n",
        namespace,
    )
    return namespace["_run_git"](), guard


def test_allow_read_only_git_accepts_exact_batch_loader_argv() -> None:
    commit = "a" * 40
    operations = (
        (
            "ls-tree", "-r", "-z", commit, "--",
            ":(literal)orchestrator/campaign/env_contract.py",
            ":(literal)orchestrator/campaign/ident.py",
        ),
        ("cat-file", "--batch"),
    )

    for operation in operations:
        allowed, guard = _call_allow_read_only_git(operation)
        assert allowed is True, operation
        assert len(guard.allowed_git_argv_sha256) == 1


def test_allow_read_only_git_rejects_nonproduction_batch_argv() -> None:
    commit = "a" * 40
    invalid_operations = (
        (
            "old-cat-file-blob",
            ("cat-file", "blob", f"{commit}:orchestrator/campaign/ident.py"),
        ),
        (
            "pathspec-without-literal",
            ("ls-tree", "-r", "-z", commit, "--", "dir/loader.py"),
        ),
        (
            "nonhex-commit",
            ("ls-tree", "-r", "-z", "g" * 40, "--", ":(literal)dir/loader.py"),
        ),
        (
            "cat-file-extra-word",
            ("cat-file", "--batch", "extra"),
        ),
        (
            "parent-pathspec",
            ("ls-tree", "-r", "-z", commit, "--", ":(literal).."),
        ),
        (
            "absolute-pathspec",
            ("ls-tree", "-r", "-z", commit, "--", ":(literal)/tmp/x"),
        ),
        (
            "empty-pathspec",
            ("ls-tree", "-r", "-z", commit, "--", ":(literal)"),
        ),
        (
            "missing-pathspec",
            ("ls-tree", "-r", "-z", commit, "--"),
        ),
        (
            "nul-pathspec",
            ("ls-tree", "-r", "-z", commit, "--", ":(literal)dir/nul\0.py"),
        ),
        (
            "duplicate-pathspec",
            (
                "ls-tree", "-r", "-z", commit, "--",
                ":(literal)dir/loader.py", ":(literal)dir/loader.py",
            ),
        ),
        (
            "other-magic",
            ("ls-tree", "-r", "-z", commit, "--", ":(glob)dir/*.py"),
        ),
    )

    for label, operation in invalid_operations:
        allowed, guard = _call_allow_read_only_git(operation)
        assert allowed is False, label
        assert guard.allowed_git_argv_sha256 == []

    root = str(_REPO_ROOT)
    batch = ("cat-file", "--batch")
    invalid_argvs = (
        (
            "foreign-git-dir",
            (
                "/usr/bin/git", "--git-dir=/tmp/foreign.git",
                *B._GIT_HARDEN, "--no-replace-objects", "-C", root, *batch,
            ),
        ),
        (
            "extra-config",
            (
                "/usr/bin/git", "-c", "safe.directory=*",
                *B._GIT_HARDEN, "--no-replace-objects", "-C", root, *batch,
            ),
        ),
        (
            "missing-harden-option",
            (
                "/usr/bin/git", "--no-pager",
                "-c", "core.useReplaceRefs=false",
                "-c", "core.fsmonitor=false",
                "--no-replace-objects", "-C", root, *batch,
            ),
        ),
        (
            "duplicate-harden-option",
            (
                "/usr/bin/git", "--no-pager",
                "-c", "core.useReplaceRefs=false",
                "-c", "core.commitGraph=false",
                "-c", "core.commitGraph=false",
                "-c", "core.fsmonitor=false",
                "--no-replace-objects", "-C", root, *batch,
            ),
        ),
        (
            "harden-option-order",
            (
                "/usr/bin/git", "--no-pager",
                "-c", "core.commitGraph=false",
                "-c", "core.useReplaceRefs=false",
                "-c", "core.fsmonitor=false",
                "--no-replace-objects", "-C", root, *batch,
            ),
        ),
        (
            "duplicate-C",
            (
                "/usr/bin/git", *B._GIT_HARDEN, "--no-replace-objects",
                "-C", root, "-C", root, *batch,
            ),
        ),
    )

    for label, argv in invalid_argvs:
        allowed, guard = _call_allow_read_only_git((), argv=argv)
        assert allowed is False, label
        assert guard.allowed_git_argv_sha256 == []


def _tree_manifest(root: Path) -> tuple[tuple[str, str, int], ...]:
    if not root.exists():
        return ()
    rows: list[tuple[str, str, int]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            rows.append((relative, f"symlink:{os.readlink(path)}", 0))
        elif path.is_dir():
            rows.append((relative, "directory", 0))
        else:
            raw = path.read_bytes()
            rows.append((relative, hashlib.sha256(raw).hexdigest(), len(raw)))
    return tuple(rows)


@pytest.fixture(scope="module")
def static_runtime():
    guard = P._ProcessGuard(P._protected_campaign_roots())
    static = P._load_static_modules()
    runtime = P._load_runtime(guard, static)
    return runtime, static


def test_child_runner_is_isolated_bytecode_free_and_clean():
    completed = _run_child(
        """
        import json, os, sys
        print(json.dumps({
            "isolated": sys.flags.isolated,
            "no_bytecode": sys.dont_write_bytecode,
            "env": sorted(os.environ),
        }))
        """,
        check=True,
    )
    value = json.loads(completed.stdout)
    assert value["isolated"] == 1
    assert value["no_bytecode"] is True
    assert value["env"] == sorted(_clean_env())


def test_source_avoids_materializer_and_exploration_driver_classification():
    source = (_REPO_ROOT / P._PROBE_RELATIVE).read_text(encoding="utf-8")
    forbidden_flag = "--" + "build"
    forbidden_factory = "exploration_campaign_" + "layout"
    assert forbidden_flag not in source
    tree = __import__("ast").parse(source)
    calls = {
        __import__("ast").unparse(node.func)
        for node in __import__("ast").walk(tree)
        if isinstance(node, __import__("ast").Call)
    }
    assert forbidden_factory not in calls


def test_cli_has_no_root_or_negative_control_injection():
    completed = _run_child(
        """
        from orchestrator.campaign import p3_b4_wiring_probe as P
        P.main(["--driver", "base", "--evidence-set-id", "x", "--root", "/tmp/x"])
        """
    )
    assert completed.returncode != 0
    assert "unrecognized arguments" in completed.stderr
    for spelling in ("campaign-dir", "output-root", "negative-control"):
        assert spelling not in (_REPO_ROOT / P._PROBE_RELATIVE).read_text(encoding="utf-8")


def test_static_candidate_paths_and_driver_specific_guards(static_runtime):
    runtime, static = static_runtime
    values = {
        name: P._proof_switchpoint(static, runtime.drivers[name])
        for name in ("base", "sort", "trigger")
    }
    run_guard = "a.run_iteration"
    build_guard = 'do_build and out["outcome"] != "dry-pass"'
    assert [edge["guard"] for edge in values["base"]["conditional_edges"]] == [
        run_guard, build_guard,
    ]
    assert [edge["guard"] for edge in values["sort"]["conditional_edges"]] == [
        run_guard,
    ]
    assert [edge["guard"] for edge in values["trigger"]["conditional_edges"]] == [
        run_guard, build_guard,
    ]
    for value in values.values():
        assert value["reachable"] is True
        assert value["runtime_candidate_main_passage_claimed"] is False
        assert value["evidence_kind"] == (
            "static candidate-main path + probe direct call to the real switchpoint"
        )
        assert all("guards" in edge for edge in value["path"])


def test_source_segment_helper_matches_stdlib_for_all_static_ifs(monkeypatch):
    static = P._load_static_modules()
    # 47 = 46 + orchestrator.campaign.agent_outputs (p3_s4_loop の静的 import 依存、[T-2746])
    assert len(static) == 47

    stdlib_splitter = ast._splitlines_no_ff
    reference_cache: dict[str, list[str]] = {}

    def cached_stdlib_splitter(source: str) -> list[str]:
        if source not in reference_cache:
            reference_cache[source] = stdlib_splitter(source)
        return reference_cache[source]

    monkeypatch.setattr(ast, "_splitlines_no_ff", cached_stdlib_splitter)
    compared = 0
    for module in sorted(static.values(), key=lambda value: value.relative_path):
        lines = P._split_source_lines(module.source)
        for node in ast.walk(module.tree):
            if not isinstance(node, ast.If):
                continue
            actual = P._get_source_segment(lines, node.test)
            expected = ast.get_source_segment(module.source, node.test)
            assert actual == expected, (
                f"source segment mismatch: {module.relative_path}:"
                f"{node.test.lineno}"
            )
            compared += 1
    assert compared > 0


def test_source_segment_helper_matches_stdlib_at_boundaries():
    def located(
        lineno: int, col_offset: int, end_lineno: int, end_col_offset: int,
    ) -> ast.Name:
        node = ast.Name(id="synthetic", ctx=ast.Load())
        node.lineno = lineno
        node.col_offset = col_offset
        node.end_lineno = end_lineno
        node.end_col_offset = end_col_offset
        return node

    def assert_matches(
        source: str, node: ast.AST, *, padded: bool = False,
    ) -> None:
        lines = P._split_source_lines(source)
        try:
            expected = ast.get_source_segment(source, node, padded=padded)
        except Exception as expected_error:
            with pytest.raises(type(expected_error)):
                P._get_source_segment(lines, node, padded=padded)
        else:
            assert P._get_source_segment(lines, node, padded=padded) == expected

    before_source = "\u03b1 target suffix"
    assert_matches(
        before_source,
        located(
            1,
            len("\u03b1 ".encode("utf-8")),
            1,
            len("\u03b1 target".encode("utf-8")),
        ),
    )
    inside_source = "prefix \u03b1 suffix"
    assert_matches(
        inside_source,
        located(
            1,
            len("prefix ".encode("utf-8")),
            1,
            len("prefix \u03b1".encode("utf-8")),
        ),
    )

    for newline in ("\n", "\r\n", "\r"):
        source = f"\u03b1 prefix{newline}\u03b2 suffix"
        assert_matches(
            source,
            located(
                1,
                len("\u03b1 ".encode("utf-8")),
                2,
                len("\u03b2".encode("utf-8")),
            ),
        )

    for separator in (
        "\f", "\x0b", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029",
    ):
        source = f"\u03b1 {separator}\u03b2"
        assert_matches(
            source,
            located(
                1,
                len("\u03b1 ".encode("utf-8")),
                1,
                len(source.encode("utf-8")),
            ),
        )

    padded_source = "\t\fxxfirst\nlast!"
    padded_node = located(1, 4, 2, len("last".encode("utf-8")))
    assert_matches(padded_source, padded_node)
    assert_matches(padded_source, padded_node, padded=True)
    assert_matches("first\nsecond\n", located(1, 0, 2, 0))
    assert_matches("", located(1, 0, 1, 0))
    assert_matches("value\n", located(2, 0, 2, 0))

    missing_location = ast.Name(id="missing", ctx=ast.Load())
    assert ast.get_source_segment("missing", missing_location) is None
    assert P._get_source_segment(
        P._split_source_lines("missing"), missing_location,
    ) is None


def test_analyze_source_preserves_guard_wiring_and_fallback(monkeypatch):
    module_name = "orchestrator.campaign.synthetic_guard_wiring"
    relative_path = "orchestrator/campaign/synthetic_guard_wiring.py"
    source = textwrap.dedent("""\
        def target():
            pass
        def caller(cond):
            if cond:
                target()
            else:
                target()
    """)

    analyzed = P._analyze_source(module_name, relative_path, source)
    calls = analyzed.functions[f"{module_name}.caller"].calls
    assert [call.guards for call in calls] == [
        ("cond",),
        ("not (cond)",),
    ]

    fallback = "fallback_guard"
    monkeypatch.setattr(P.ast, "unparse", lambda _node: fallback)
    for missing_segment in (None, ""):
        monkeypatch.setattr(
            P,
            "_get_source_segment",
            lambda _lines, _node, result=missing_segment: result,
        )
        analyzed = P._analyze_source(module_name, relative_path, source)
        calls = analyzed.functions[f"{module_name}.caller"].calls
        assert [call.guards for call in calls] == [
            (fallback,),
            (f"not ({fallback})",),
        ]


def test_analyze_source_splits_each_module_exactly_once(monkeypatch):
    source = textwrap.dedent("""\
        def target():
            pass
        def first(left, right):
            if left:
                target()
            if right:
                target()
        def second(left, right):
            if left:
                target()
            if right:
                target()
    """)
    original_splitter = P._split_source_lines
    original_get_source_segment = P._get_source_segment
    split_calls = 0
    split_results: list[list[str]] = []
    segment_inputs: list[list[str]] = []

    def split_spy(value: str) -> list[str]:
        nonlocal split_calls
        split_calls += 1
        result = original_splitter(value)
        split_results.append(result)
        return result

    def segment_spy(
        lines: list[str], node: ast.AST, *, padded: bool = False,
    ) -> str | None:
        segment_inputs.append(lines)
        return original_get_source_segment(lines, node, padded=padded)

    monkeypatch.setattr(P, "_split_source_lines", split_spy)
    monkeypatch.setattr(P, "_get_source_segment", segment_spy)
    analyzed = P._analyze_source(
        "orchestrator.campaign.synthetic_split_count",
        "orchestrator/campaign/synthetic_split_count.py",
        source,
    )
    assert len(analyzed.functions) == 3
    assert sum(
        isinstance(node, ast.If) for node in ast.walk(analyzed.tree)
    ) == 4
    assert split_calls == 1
    assert len(segment_inputs) == 4
    assert all(lines is split_results[0] for lines in segment_inputs)


def test_static_preflight_mapping_matches_runtime_import_targets(static_runtime):
    """_load_runtime imports each preflight mapping name into runtime.modules."""
    runtime, static = static_runtime
    assert set(runtime.modules) == set(static)
    assert set(P._MODULE_RELATIVE_PATHS) < set(static)
    for name in (
        "orchestrator.campaign.artifact_admission",
        "orchestrator.campaign.layout",
        "orchestrator.campaign.model",
    ):
        assert name in static
    manifest = P._static_module_manifest(static)
    assert [row["module"] for row in manifest] == sorted(static)
    assert all(set(row) == {"module", "path", "source_sha256"} for row in manifest)


@pytest.mark.parametrize(
    ("preamble", "body", "message"),
    (
        (
            "import importlib\nfrom . import p3_s4_loop as L",
            "loader = importlib.import_module\n    loader(name)",
            "dynamic import",
        ),
        (
            "import sys\nfrom . import p3_s4_loop as L",
            "mods = sys.modules\n    mods[name].make_critic_digest()",
            "sys.modules callable",
        ),
        (
            "from . import p3_s4_loop as L",
            "getter = getattr\n    getter(L, name)()",
            "non-literal getattr",
        ),
        (
            "from . import p3_s4_loop as L",
            "target = choose()\n    target()",
            "unresolved local assignment",
        ),
    ),
)
def test_aliased_dynamic_bindings_on_proof_path_fail_closed(
    static_runtime, preamble, body, message,
):
    runtime, static = static_runtime
    name = runtime.drivers["base"].module
    source = f"""
{preamble}
def main():
    return drive_iteration()
def drive_iteration():
    {body}
    return L.make_critic_digest()
"""
    mutated = dict(static)
    mutated[name] = P._analyze_source(
        name, runtime.drivers["base"].relative_path, textwrap.dedent(source),
    )
    with pytest.raises(P.StaticInventoryError, match=message):
        P._proof_switchpoint(mutated, runtime.drivers["base"])


def test_nonliteral_getattr_on_proof_path_fails_closed(static_runtime):
    runtime, static = static_runtime
    name = runtime.drivers["base"].module
    source = """
from . import p3_s4_loop as L
def main():
    return drive_iteration()
def drive_iteration():
    return getattr(L, dynamic_name)()
"""
    mutated = dict(static)
    mutated[name] = P._analyze_source(
        name, runtime.drivers["base"].relative_path, textwrap.dedent(source),
    )
    with pytest.raises(P.StaticInventoryError, match="non-literal getattr"):
        P._proof_switchpoint(mutated, runtime.drivers["base"])


@pytest.mark.parametrize(
    "statement",
    (
        "import atexit\natexit.register(lambda: None)",
        (
            "import atexit\n"
            "def helper():\n    atexit.register(lambda: None)\n"
            "helper()"
        ),
        "import atexit\n@atexit.register\ndef cleanup():\n    pass",
        "import signal\nsignal.signal(signal.SIGTERM, lambda *_: None)",
        "import weakref\nweakref.finalize(object(), lambda: None)",
        "import threading\nthreading.Thread().start()",
    ),
)
def test_import_time_delayed_effects_are_rejected(statement):
    module = P._analyze_source(
        "orchestrator.campaign.synthetic_probe_import",
        "orchestrator/campaign/synthetic_probe_import.py",
        statement + "\n",
    )
    with pytest.raises(P.StaticInventoryError, match="import-time delayed effect"):
        P._reject_import_side_effects(module)


def test_preexisting_non_main_thread_rejects_main_before_import(tmp_path):
    evidence_root = tmp_path / "thread-rejected"
    completed = _run_child(
        f"""
        import threading
        from pathlib import Path
        from orchestrator.campaign import p3_b4_wiring_probe as P
        P._EVIDENCE_ROOT = Path({str(evidence_root)!r})
        stop = threading.Event()
        worker = threading.Thread(target=stop.wait)
        worker.start()
        try:
            P.main(["--driver", "base", "--evidence-set-id", "threaded"])
        except P.ProbeIsolationError as exc:
            print(type(exc).__name__)
        else:
            raise AssertionError("preexisting thread was accepted")
        finally:
            stop.set()
            worker.join()
        """,
        check=True,
    )
    assert completed.stdout.strip() == "ProbeIsolationError"
    assert list(evidence_root.rglob("*")) == []


def _inventory_symbols(inventory) -> set[str]:
    return {f"{entry['module']}.{entry['qualname']}" for entry in inventory}


def test_anchor_seed_alone_load_bears_pipeline_evaluate(static_runtime):
    runtime, static = static_runtime
    baseline = _inventory_symbols(P._build_inventory(static, runtime.modules))
    anchor = P._GENERATION_SEEDS[0]
    assert anchor in baseline
    target = "orchestrator.campaign.pipeline.evaluate"
    assert target in baseline
    without_anchor = tuple(seed for seed in P._GENERATION_SEEDS if seed != anchor)
    mutated = _inventory_symbols(
        P._build_inventory(static, runtime.modules, seeds=without_anchor)
    )
    assert anchor not in mutated
    assert target not in mutated


def test_save_loop_state_seed_is_independently_load_bearing(static_runtime):
    runtime, static = static_runtime
    target = "orchestrator.campaign.p3_s4_loop.save_loop_state"
    baseline = _inventory_symbols(P._build_inventory(static, runtime.modules))
    assert target in baseline
    mutated = _inventory_symbols(P._build_inventory(
        static, runtime.modules,
        seeds=tuple(seed for seed in P._GENERATION_SEEDS if seed != target),
    ))
    assert target not in mutated


def test_project_whiteboard_seed_is_independently_load_bearing(static_runtime):
    runtime, static = static_runtime
    target = "orchestrator.campaign.p3_s4_loop.project_whiteboard"
    baseline = _inventory_symbols(P._build_inventory(static, runtime.modules))
    assert target in baseline
    mutated = _inventory_symbols(P._build_inventory(
        static, runtime.modules,
        seeds=tuple(seed for seed in P._GENERATION_SEEDS if seed != target),
    ))
    assert target not in mutated


def test_inventory_names_real_producers_and_excludes_probe_consumers(static_runtime):
    runtime, static = static_runtime
    symbols = _inventory_symbols(P._build_inventory(static, runtime.modules))
    expected = {"orchestrator.campaign.pipeline.evaluate"}
    for module in (
        "p3_s4_loop", "p3_s4_loop_sort", "p3_s4_loop_trigger_gating",
    ):
        expected.add(f"orchestrator.campaign.{module}.run_one_iteration")
        expected.add(f"orchestrator.campaign.{module}.drive_iteration")
    assert expected <= symbols
    assert "orchestrator.campaign.p3_s4_loop.make_critic_digest" not in symbols
    assert "orchestrator.campaign.p3_s4_loop.record_diff_reject" not in symbols
    assert "orchestrator.campaign.p3_s4_loop.default_cfg" not in symbols


def test_inventory_builder_rejects_recorded_unresolved_issue(static_runtime):
    runtime, static = static_runtime
    symbol = "orchestrator.campaign.pipeline.evaluate"
    module_name = "orchestrator.campaign.pipeline"
    module = static[module_name]
    functions = dict(module.functions)
    functions[symbol] = replace(
        functions[symbol], issues=("aliased dynamic import at line 1",),
    )
    mutated = dict(static)
    mutated[module_name] = replace(module, functions=functions)
    with pytest.raises(P.StaticInventoryError, match="generation inventory"):
        P._build_inventory(mutated, runtime.modules)


@pytest.mark.parametrize(
    "symbol",
    (
        "orchestrator.campaign.p3_s4_loop.run_one_iteration",
        "orchestrator.campaign.p3_s4_loop.drive_iteration",
        "orchestrator.campaign.p3_s4_loop_sort.run_one_iteration",
        "orchestrator.campaign.p3_s4_loop_sort.drive_iteration",
        "orchestrator.campaign.p3_s4_loop_trigger_gating.run_one_iteration",
        "orchestrator.campaign.p3_s4_loop_trigger_gating.drive_iteration",
        "orchestrator.campaign.pipeline.evaluate",
        "orchestrator.campaign.p3_s4_loop.save_loop_state",
        "orchestrator.campaign.p3_s4_loop.project_whiteboard",
    ),
)
def test_real_producer_entry_is_interdicted_before_body(symbol):
    completed = _run_child(
        f"""
        import inspect, json
        from orchestrator.campaign import p3_b4_wiring_probe as P
        guard = P._ProcessGuard(P._protected_campaign_roots())
        guard.install_audit()
        static = P._load_static_modules()
        runtime = P._load_runtime(guard, static)
        inventory = P._build_inventory(static, runtime.modules)
        guard.seal(inventory, runtime.modules)
        function = P._runtime_function(runtime.modules, {symbol!r})
        positional = []
        keywords = {{}}
        for parameter in inspect.signature(function).parameters.values():
            if parameter.default is not inspect.Parameter.empty:
                continue
            if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY,
                                  inspect.Parameter.POSITIONAL_OR_KEYWORD):
                positional.append(None)
            elif parameter.kind is inspect.Parameter.KEYWORD_ONLY:
                keywords[parameter.name] = None
        try:
            function(*positional, **keywords)
        except P.OutcomeGenerationError as exc:
            print(json.dumps({{
                "module": exc.module,
                "qualname": exc.qualname,
                "path": exc.path,
                "firstlineno": exc.firstlineno,
                "attempts": len(guard.blocked_outcome_attempts),
            }}))
        else:
            raise AssertionError("real producer body was entered")
        """,
        check=True,
    )
    value = json.loads(completed.stdout)
    assert f"{value['module']}.{value['qualname']}" == symbol
    assert value["path"].startswith("orchestrator/campaign/")
    assert value["firstlineno"] > 0
    assert value["attempts"] == 1


def test_main_wiring_interdicts_real_pipeline_and_publishes_nothing(tmp_path):
    evidence_root = tmp_path / "evidence"
    completed = _run_child(
        f"""
        from pathlib import Path
        from orchestrator.campaign import p3_b4_wiring_probe as P
        P._EVIDENCE_ROOT = Path({str(evidence_root)!r})
        original = P._CHECKS
        def call_real_pipeline(ctx):
            ctx.runtime.pipeline.evaluate(
                None, None, "probe", "probe", None, 1,
                authorization_contract=None, build_context=None,
            )
        P._CHECKS = ((
            "static_candidate_plus_direct_switchpoint_call",
            call_real_pipeline,
        ), *original[1:])
        try:
            P.main(["--driver", "base", "--evidence-set-id", "negative-main"])
        except P.OutcomeGenerationError:
            print("OUTCOME_INTERDICTED")
        else:
            raise AssertionError("actual main did not interdict pipeline.evaluate")
        """,
        check=True,
    )
    assert completed.stdout.strip() == "OUTCOME_INTERDICTED"
    assert list(evidence_root.rglob("*.json")) == []
    assert list(evidence_root.rglob("*.sha256")) == []


def test_evidence_hook_booleans_are_observation_derived():
    class FakeGuard:
        def profile_active(self):
            return False

    observations = {
        "audit_hook_active": False,
        "opened_before_campaign_imports": False,
        "sealed_before_checks": False,
        "active_during_json_publish": False,
        "active_during_sha256_publish": False,
    }
    value = P._interdiction_report(FakeGuard(), observations)
    assert value["profile_hook_active"] is False
    assert value["audit_hook_active"] is False
    assert set(value["window"].values()) == {False}


def test_publish_observes_each_real_write_and_link_boundary(tmp_path, monkeypatch):
    class FakeGuard:
        def __init__(self):
            self.stages = []

        def verify_publish_boundary(self):
            return None

        def publish_boundary_active(self, stage):
            self.stages.append(stage)
            return True

    monkeypatch.setattr(P, "_validate_evidence_schema", lambda _value: None)
    guard = FakeGuard()
    value = {"interdiction": {"window": {}}}
    json_path = tmp_path / "evidence" / "value.json"
    sidecar = tmp_path / "evidence" / "value.json.sha256"
    digest = P._publish_evidence(guard, value, json_path, sidecar)
    assert guard.stages == [
        "json-publish-window-open",
        "sha256-publish-window-open",
        "directory-create-before",
        "directory-create-after",
        "json-write-before",
        "json-write-after",
        "sha256-write-before",
        "sha256-write-after",
        "sha256-link-before",
        "sha256-link-after",
        "json-link-before",
        "json-link-after",
        "publish-window-closed",
    ]
    assert value["interdiction"]["window"] == {
        "active_during_json_publish": True,
        "active_during_sha256_publish": True,
    }
    assert hashlib.sha256(json_path.read_bytes()).hexdigest() == digest
    assert sidecar.read_text(encoding="ascii") == f"{digest}  value.json\n"


def test_failed_check_publish_gate_is_schema_independent():
    guard = P._ProcessGuard(())
    guard.verify_seal = lambda: None
    guard.failed_check_attempts.append("synthetic-failed-check")
    with pytest.raises(P.ProbeIsolationError, match="failed check attempt preceded publish"):
        guard.verify_publish_boundary()


def test_identity_preimage_hash_uses_versioned_domain_and_hides_cfg_hash8(
    static_runtime,
):
    runtime, _static = static_runtime
    assert P._IDENTITY_PREIMAGE_DOMAIN.endswith(b"\0")
    assert b"/v1\0" in P._IDENTITY_PREIMAGE_DOMAIN
    pair = P._identity_pair(runtime, runtime.L)
    on = runtime.L.default_cfg(reflux=True)
    off = runtime.L.default_cfg(reflux=False)
    assert pair["on_preimage_sha256"][:8] != runtime.ident.cfg_hash(on)
    assert pair["off_preimage_sha256"][:8] != runtime.ident.cfg_hash(off)
    assert pair["domain_separated_from_campaign_locator"] is True


def test_trigger_site_projection_records_resolver_site_and_verbatim_refusal(
    static_runtime, monkeypatch,
):
    runtime, _static = static_runtime
    site = "RESOLVER_DERIVED_REJECTED_SITE"
    reason = "production refusal text must remain verbatim"
    admitted_sites: list[str] = []
    execution_guard = runtime.modules[
        "orchestrator.campaign.execution_guard"
    ]

    monkeypatch.setattr(runtime.trigger, "_current_site", lambda: site)

    def reject(resolved_site):
        admitted_sites.append(resolved_site)
        raise execution_guard.ExecutionGuardError(reason)

    monkeypatch.setattr(runtime.trigger, "_admit_env_contract", reject)
    context = P._CheckContext(
        runtime=runtime,
        guard=P._ProcessGuard(()),
        spec=runtime.drivers["trigger"],
        view=object(),
        static_switchpoint={},
    )
    result = P._check_identity(context)

    assert admitted_sites == [site]
    assert result["passed"] is True
    assert result["site_projected_cfg"] == {
        "status": "not_measured",
        "site": site,
        "reason": reason,
    }


def test_trigger_site_projection_is_measured_when_production_accepts_site(
    static_runtime, monkeypatch,
):
    runtime, _static = static_runtime
    site = "RESOLVER_DERIVED_MEASURED_SITE"
    contract = object()
    calls: list[tuple[object, ...]] = []

    monkeypatch.setattr(runtime.trigger, "_current_site", lambda: site)

    def admit(resolved_site):
        calls.append(("admit", resolved_site))
        return contract

    def project(cfg, resolved_site, *, _contract):
        calls.append(("project", resolved_site, _contract))
        return cfg

    monkeypatch.setattr(runtime.trigger, "_admit_env_contract", admit)
    monkeypatch.setattr(runtime.trigger, "_campaign_cfg_for_site", project)
    context = P._CheckContext(
        runtime=runtime,
        guard=P._ProcessGuard(()),
        spec=runtime.drivers["trigger"],
        view=object(),
        static_switchpoint={},
    )
    result = P._check_identity(context)

    assert calls == [
        ("admit", site),
        ("project", site, contract),
        ("project", site, contract),
    ]
    assert result["passed"] is True
    projected = result["site_projected_cfg"]
    assert projected["status"] == "measured"
    assert projected["site"] == site
    assert projected["only_reflux_differs"] is True
    assert projected["different"] is True


def test_seal_uses_import_free_excepthook_and_preserves_primary_exception():
    completed = _run_child(
        """
        import sys
        from orchestrator.campaign import p3_b4_wiring_probe as P

        def importing_hook(_kind, _value, _traceback):
            __import__("_p3_b4_missing_hook_dependency")

        sys.excepthook = importing_hook
        guard = P._ProcessGuard(())
        guard.install_audit()
        guard.seal((), {})
        assert sys.excepthook is sys.__excepthook__
        try:
            __import__("_p3_b4_missing_hook_dependency")
        except P.ProbeIsolationError as exc:
            assert str(exc) == "dynamic interpreter mutation is forbidden: import"
        else:
            raise AssertionError("sealed import was not blocked")
        raise RuntimeError("PRIMARY_EXCEPTION_REPORT")
        """,
    )
    assert completed.returncode != 0
    assert "RuntimeError: PRIMARY_EXCEPTION_REPORT" in completed.stderr
    assert "Error in sys.excepthook" not in completed.stderr
    assert (
        "dynamic interpreter mutation is forbidden: import"
        not in completed.stderr
    )


def test_fixture_is_type_generated_reserved_and_rejects_outcome_fields():
    payload = P._fixture_payload_from_types()
    assert P._validate_fixture_payload(payload) == payload
    assert payload["marker"] == P._FIXTURE_MARKER
    assert inspect.signature(P._make_probe_view).parameters == {}
    contaminated = {**payload, "fitness_tps": 1}
    with pytest.raises(P.ProbeIsolationError, match="fixture field is forbidden"):
        P._validate_fixture_payload(contaminated)


def test_record_diff_reject_requires_issued_layout_root_without_mutation(tmp_path):
    protected = tmp_path / "official" / "campaigns"
    protected.mkdir(parents=True)
    (protected / "canary.txt").write_text("unchanged", encoding="utf-8")
    before = _tree_manifest(protected)
    completed = _run_child(
        f"""
        import shutil
        from orchestrator.campaign import p3_b4_wiring_probe as P
        from orchestrator.campaign.layout import CampaignLayout
        static = P._load_static_modules()
        runtime = P._load_runtime(P._ProcessGuard(P._protected_campaign_roots()), static)
        workspace = P._issue_probe_workspace()
        P._ACTIVE_RUNTIME = runtime
        try:
            layout = CampaignLayout(root={str(protected / 'probe-negative')!r})
            P._record_probe_diff_reject(
                workspace, layout, P._fixture_payload_from_types(),
            )
        except P.ProbeIsolationError:
            print("BINDING_REJECTED")
        else:
            raise AssertionError("protected layout reached the writer")
        finally:
            P._ACTIVE_RUNTIME = None
            shutil.rmtree(workspace.verify())
        """,
        extra_env={"IZANAGI_OFFICIAL_OUTPUT_ROOT": str(tmp_path / "official")},
        check=True,
    )
    assert completed.stdout.strip() == "BINDING_REJECTED"
    assert _tree_manifest(protected) == before


def test_workspace_symlink_to_protected_root_is_rejected(static_runtime):
    runtime, _static = static_runtime
    workspace = P._issue_probe_workspace()
    root = workspace.verify()
    (root / "fixture").symlink_to(P._protected_campaign_roots()[0], target_is_directory=True)
    previous = P._ACTIVE_RUNTIME
    P._ACTIVE_RUNTIME = runtime
    try:
        with pytest.raises(P.ProbeIsolationError, match="symlink"):
            P._layout_for_workspace(workspace)
    finally:
        P._ACTIVE_RUNTIME = previous
        __import__("shutil").rmtree(root, ignore_errors=True)


def test_ambient_temp_inside_campaign_root_is_rejected_without_mutation(tmp_path):
    campaign_root = tmp_path / "official" / "campaigns"
    campaign_root.mkdir(parents=True)
    canary = campaign_root / "canary.txt"
    canary.write_text("unchanged", encoding="utf-8")
    before = _tree_manifest(campaign_root)
    completed = _run_child(
        """
        from orchestrator.campaign import p3_b4_wiring_probe as P
        try:
            P._issue_probe_workspace()
        except P.ProbeIsolationError:
            print("AMBIENT_REJECTED")
        else:
            raise AssertionError("campaign-root ambient temp was accepted")
        """,
        extra_env={
            "IZANAGI_OFFICIAL_OUTPUT_ROOT": str(tmp_path / "official"),
            "TMPDIR": str(campaign_root),
        },
        check=True,
    )
    assert completed.stdout.strip() == "AMBIENT_REJECTED"
    assert _tree_manifest(campaign_root) == before


def test_audit_blocks_protected_wal_read_and_write_without_mutation(tmp_path):
    campaign_root = tmp_path / "official" / "campaigns"
    wal_path = campaign_root / "campaign-x" / "runs" / "wal.jsonl"
    wal_path.parent.mkdir(parents=True)
    wal_path.write_text('{"canary":true}\n', encoding="utf-8")
    before = _tree_manifest(campaign_root)
    completed = _run_child(
        f"""
        import json
        from orchestrator.campaign import p3_b4_wiring_probe as P
        guard = P._ProcessGuard(P._protected_campaign_roots())
        guard.install_audit()
        blocked = []
        for mode in ("rb", "ab"):
            try:
                open({str(wal_path)!r}, mode).close()
            except P.ProbeIsolationError:
                blocked.append(mode)
        print(json.dumps({{
            "blocked": blocked,
            "reads": guard.protected_read_attempts,
            "writes": guard.protected_write_attempts,
        }}))
        """,
        extra_env={"IZANAGI_OFFICIAL_OUTPUT_ROOT": str(tmp_path / "official")},
        check=True,
    )
    value = json.loads(completed.stdout)
    assert value == {"blocked": ["rb", "ab"], "reads": 1, "writes": 1}
    assert _tree_manifest(campaign_root) == before


@pytest.mark.parametrize("operation", ("rename", "replace", "link", "symlink"))
def test_audit_blocks_each_protected_destination_with_dir_fd_without_mutation(
    operation, tmp_path,
):
    campaign_root = tmp_path / "official" / "campaigns"
    campaign_root.mkdir(parents=True)
    source = tmp_path / f"source-{operation}"
    source.write_text("source", encoding="utf-8")
    (campaign_root / "canary.txt").write_text("unchanged", encoding="utf-8")
    before = _tree_manifest(campaign_root)
    completed = _run_child(
        f"""
        import json, os
        from orchestrator.campaign import p3_b4_wiring_probe as P
        destination_fd = os.open(
            {str(campaign_root)!r},
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
        )
        guard = P._ProcessGuard(P._protected_campaign_roots())
        guard.install_audit()
        try:
            if {operation!r} == "rename":
                os.rename({str(source)!r}, "destination", dst_dir_fd=destination_fd)
            elif {operation!r} == "replace":
                os.replace({str(source)!r}, "destination", dst_dir_fd=destination_fd)
            elif {operation!r} == "link":
                os.link({str(source)!r}, "destination", dst_dir_fd=destination_fd)
            else:
                os.symlink({str(source)!r}, "destination", dir_fd=destination_fd)
        except P.ProbeIsolationError:
            print(json.dumps({{
                "operation": {operation!r},
                "writes": guard.protected_write_attempts,
            }}))
        else:
            raise AssertionError("protected destination mutation was accepted")
        finally:
            os.close(destination_fd)
        """,
        extra_env={"IZANAGI_OFFICIAL_OUTPUT_ROOT": str(tmp_path / "official")},
        check=True,
    )
    assert json.loads(completed.stdout) == {"operation": operation, "writes": 1}
    assert _tree_manifest(campaign_root) == before
    assert source.read_text(encoding="utf-8") == "source"


def test_audit_resolves_preopened_fd_before_protected_mutation(tmp_path):
    campaign_root = tmp_path / "official" / "campaigns"
    target = campaign_root / "campaign-x" / "runs" / "wal.jsonl"
    target.parent.mkdir(parents=True)
    target.write_text("unchanged\n", encoding="utf-8")
    before = _tree_manifest(campaign_root)
    completed = _run_child(
        f"""
        import json, os
        from orchestrator.campaign import p3_b4_wiring_probe as P
        descriptor = os.open({str(target)!r}, os.O_RDWR)
        guard = P._ProcessGuard(P._protected_campaign_roots())
        guard.install_audit()
        try:
            os.truncate(descriptor, 0)
        except P.ProbeIsolationError:
            print(json.dumps({{"writes": guard.protected_write_attempts}}))
        else:
            raise AssertionError("pre-opened protected fd was accepted")
        finally:
            os.close(descriptor)
        """,
        extra_env={"IZANAGI_OFFICIAL_OUTPUT_ROOT": str(tmp_path / "official")},
        check=True,
    )
    assert json.loads(completed.stdout) == {"writes": 1}
    assert _tree_manifest(campaign_root) == before


def test_module_swap_writer_restore_is_rejected_at_publish(tmp_path):
    evidence_root = tmp_path / "restored-swap"
    completed = _run_child(
        f"""
        import json
        from pathlib import Path
        from types import ModuleType
        from orchestrator.campaign import p3_b4_wiring_probe as P
        guard = P._ProcessGuard(P._protected_campaign_roots())
        guard.install_audit()
        static = P._load_static_modules()
        runtime = P._load_runtime(guard, static)
        inventory = P._build_inventory(static, runtime.modules)
        guard.seal(inventory, runtime.modules)
        name = "orchestrator.campaign.pipeline"
        original_module = sys.modules[name]
        sys.modules[name] = ModuleType(name)
        writer_rejected = False
        try:
            runtime.pipeline.evaluate(
                None, None, "probe", "probe", None, 1,
                authorization_contract=None, build_context=None,
            )
        except P.OutcomeGenerationError:
            writer_rejected = True
        finally:
            sys.modules[name] = original_module
        json_path = Path({str(evidence_root / 'value.json')!r})
        publish_rejected = False
        try:
            P._publish_evidence(
                guard, {{}}, json_path, json_path.with_suffix(".json.sha256"),
            )
        except P.ProbeIsolationError:
            publish_rejected = True
        print(json.dumps({{
            "writer_rejected": writer_rejected,
            "publish_rejected": publish_rejected,
            "attempts": len(guard.blocked_outcome_attempts),
        }}))
        """,
        check=True,
    )
    assert json.loads(completed.stdout) == {
        "writer_rejected": True,
        "publish_rejected": True,
        "attempts": 1,
    }
    assert list(evidence_root.rglob("*")) == []


def test_profile_setters_and_code_assignment_are_continuously_blocked():
    completed = _run_child(
        """
        import json, threading
        from orchestrator.campaign import p3_b4_wiring_probe as P
        guard = P._ProcessGuard(P._protected_campaign_roots())
        guard.install_audit()
        static = P._load_static_modules()
        runtime = P._load_runtime(guard, static)
        guard.seal(P._build_inventory(static, runtime.modules), runtime.modules)
        blocked = []
        for name, action in (
            ("sys.setprofile", lambda: sys.setprofile(None)),
            ("threading.setprofile", lambda: threading.setprofile(None)),
        ):
            try:
                action()
            except P.ProbeIsolationError:
                blocked.append(name)
        original_code = runtime.pipeline.evaluate.__code__
        def replacement():
            return None
        try:
            runtime.pipeline.evaluate.__code__ = replacement.__code__
        except P.ProbeIsolationError:
            blocked.append("function.__code__")
        assert runtime.pipeline.evaluate.__code__ is original_code
        print(json.dumps({
            "blocked": blocked,
            "ledger": guard.interpreter_mutation_attempts,
        }))
        """,
        check=True,
    )
    value = json.loads(completed.stdout)
    assert value["blocked"] == [
        "sys.setprofile", "threading.setprofile", "function.__code__",
    ]
    assert {"sys.setprofile", "threading.setprofile", "object.__setattr__"} <= set(
        value["ledger"]
    )


def test_exec_compile_and_new_import_are_rejected_after_seal():
    completed = _run_child(
        """
        import importlib, json, shutil, tempfile
        from pathlib import Path
        from orchestrator.campaign import p3_b4_wiring_probe as P
        late_root = Path(tempfile.mkdtemp(prefix="t1769-late-import-"))
        (late_root / "probe_late_import.py").write_text(
            "VALUE = 1\\n", encoding="utf-8",
        )
        sys.path.insert(0, str(late_root))
        guard = P._ProcessGuard(P._protected_campaign_roots())
        guard.install_audit()
        static = P._load_static_modules()
        runtime = P._load_runtime(guard, static)
        guard.seal(P._build_inventory(static, runtime.modules), runtime.modules)
        rejected = []
        try:
            exec("probe_dynamic_value = 1")
        except P.ProbeIsolationError:
            rejected.append("exec")
        try:
            importlib.import_module("probe_late_import")
        except P.ProbeIsolationError:
            rejected.append("import")
        finally:
            shutil.rmtree(late_root, ignore_errors=True)
        print(json.dumps(rejected))
        """,
        check=True,
    )
    assert json.loads(completed.stdout) == ["exec", "import"]


def test_failed_check_does_not_publish(tmp_path):
    evidence_root = tmp_path / "failed-evidence"
    completed = _run_child(
        f"""
        from pathlib import Path
        from orchestrator.campaign import p3_b4_wiring_probe as P
        P._EVIDENCE_ROOT = Path({str(evidence_root)!r})
        def fail_check(ctx):
            return {{"passed": False}}
        P._CHECKS = (("static_candidate_plus_direct_switchpoint_call", fail_check),)
        try:
            P.main(["--driver", "base", "--evidence-set-id", "failed-check"])
        except P.ProbeIsolationError:
            print("FAILED_CLOSED")
        else:
            raise AssertionError("failed check published evidence")
        """,
        check=True,
    )
    assert completed.stdout.strip() == "FAILED_CLOSED"
    assert list(evidence_root.rglob("*.json")) == []
    assert list(evidence_root.rglob("*.sha256")) == []


def test_cleanup_failure_keeps_primary_exception_and_publishes_nothing(tmp_path):
    evidence_root = tmp_path / "cleanup-failed-evidence"
    completed = _run_child(
        f"""
        import json
        from pathlib import Path
        from orchestrator.campaign import p3_b4_wiring_probe as P
        P._EVIDENCE_ROOT = Path({str(evidence_root)!r})
        def primary_failure(ctx):
            raise ValueError("PRIMARY_CHECK_FAILURE")
        original_release = P._release_probe_view
        def cleanup_failure(view):
            original_release(view)
            raise RuntimeError("CLEANUP_FAILURE")
        P._CHECKS = ((
            "static_candidate_plus_direct_switchpoint_call",
            primary_failure,
        ),)
        P._release_probe_view = cleanup_failure
        try:
            P.main(["--driver", "base", "--evidence-set-id", "cleanup-failed"])
        except BaseException as exc:
            print(json.dumps({{
                "primary": type(exc).__name__,
                "primary_message": str(exc),
                "cause": type(exc.__cause__).__name__,
                "cause_message": str(exc.__cause__),
            }}))
        else:
            raise AssertionError("primary failure was lost")
        """,
        check=True,
    )
    assert json.loads(completed.stdout) == {
        "primary": "ValueError",
        "primary_message": "PRIMARY_CHECK_FAILURE",
        "cause": "RuntimeError",
        "cause_message": "CLEANUP_FAILURE",
    }
    assert list(evidence_root.rglob("*.json")) == []
    assert list(evidence_root.rglob("*.sha256")) == []


@pytest.mark.parametrize("driver", ("base", "sort", "trigger"))
def test_actual_main_positive_baseline_all_drivers(driver, tmp_path):
    evidence_root = tmp_path / "positive-evidence"
    completed = _run_child(
        f"""
        from pathlib import Path
        from orchestrator.campaign import p3_b4_wiring_probe as P
        P._EVIDENCE_ROOT = Path({str(evidence_root)!r})
        raise SystemExit(P.main([
            "--driver", {driver!r},
            "--evidence-set-id", "positive-baseline",
        ]))
        """,
    )
    assert completed.returncode == 0, completed.stderr
    json_path = evidence_root / "positive-baseline" / f"{driver}.json"
    sidecar = evidence_root / "positive-baseline" / f"{driver}.json.sha256"
    evidence = json.loads(json_path.read_text(encoding="utf-8"))
    raw = json_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert sidecar.read_text(encoding="ascii") == f"{digest}  {driver}.json\n"
    assert completed.stdout.strip() == f"{json_path} {digest}"
    assert evidence["result"]["passed"] is True
    assert all(check["passed"] is True for check in evidence["checks"].values())
    assert evidence["claim"] == {
        "evidence_kind": (
            "static candidate-main path + probe direct call to the real switchpoint"
        ),
        "runtime_candidate_main_passage_claimed": False,
    }
    assert evidence["admission_reads"]["reads"] == [{
        "path": P._OVERLAY_RELATIVE,
        "sha256": hashlib.sha256(
            (_REPO_ROOT / P._OVERLAY_RELATIVE).read_bytes()
        ).hexdigest(),
    }]
    assert evidence["admission_reads"]["other_campaign_artifact_reads"] == 0
    assert evidence["isolation"]["protected_read_attempts"] == 0
    assert evidence["isolation"]["protected_write_attempts"] == 0
    assert evidence["interdiction"]["profile_hook_active"] is True
    assert evidence["interdiction"]["audit_hook_active"] is True
    assert set(evidence["interdiction"]["window"].values()) == {True}
    assert evidence["interdiction"]["thread_census"]["unchanged"] is True
    assert evidence["interdiction"]["interpreter_mutation_attempts"] == []
    assert evidence["interdiction"]["failed_check_attempts"] == []
    assert evidence["interdiction"]["allowed_read_only_git"]
    assert {
        row["returncode"]
        for row in evidence["interdiction"]["allowed_read_only_git"]
    } == {0}
    assert len(evidence["interdiction"]["generation_seeds"]) == 3
    assert "outside the exact analyzed set" in evidence[
        "interdiction"
    ]["generation_scope_exclusion"]
    analyzed = evidence["interdiction"]["analyzed_modules"]
    assert [row["module"] for row in analyzed] == sorted(
        row["module"] for row in analyzed
    )
    assert evidence["interdiction"]["analyzed_modules_sha256"] == hashlib.sha256(
        P._canonical_bytes(analyzed).rstrip(b"\n")
    ).hexdigest()
    identity = evidence["checks"]["campaign_identity"]
    serialized_identity = json.dumps(identity, sort_keys=True)
    assert "campaign_id" not in serialized_identity
    assert identity["raw_cfg"]["different"] is True
    assert identity["raw_cfg"]["preimage_hash_domain"].endswith("/v1")
    assert identity["raw_cfg"]["domain_separated_from_campaign_locator"] is True
    if driver == "trigger":
        projected = identity["site_projected_cfg"]
        assert projected["status"] in {"measured", "not_measured"}
        assert isinstance(projected["site"], str) and projected["site"]
        if projected["status"] == "measured":
            assert projected["different"] is True
        else:
            assert set(projected) == {"status", "site", "reason"}
            assert isinstance(projected["reason"], str) and projected["reason"]
    else:
        assert identity["site_projected_cfg"] is None
    conditional = evidence["checks"][
        "static_candidate_plus_direct_switchpoint_call"
    ]["static"][
        "conditional_edges"
    ]
    if driver == "sort":
        assert [edge["guard"] for edge in conditional] == ["a.run_iteration"]
    else:
        assert [edge["guard"] for edge in conditional] == [
            "a.run_iteration",
            'do_build and out["outcome"] != "dry-pass"'
        ]
    off = evidence["checks"]["off_negative_controls"]
    assert set(off["on_loader_calls"].values()) == {1}
    assert set(off["off_loader_calls"].values()) == {0}
    assert off["off_equals_green_bytes"] is True


def test_second_main_call_in_same_interpreter_is_rejected(tmp_path):
    evidence_root = tmp_path / "single-use-main"
    completed = _run_child(
        f"""
        from pathlib import Path
        from orchestrator.campaign import p3_b4_wiring_probe as P
        P._EVIDENCE_ROOT = Path({str(evidence_root)!r})
        assert P.main([
            "--driver", "base", "--evidence-set-id", "first-call",
        ]) == 0
        try:
            P.main([
                "--driver", "base", "--evidence-set-id", "second-call",
            ])
        except P.ProbeIsolationError as exc:
            print("SECOND_REJECTED", str(exc))
        else:
            raise AssertionError("second main call was accepted")
        """,
        check=True,
    )
    assert completed.stdout.splitlines()[-1].startswith(
        "SECOND_REJECTED probe main may run only once"
    )
    assert (evidence_root / "first-call" / "base.json").is_file()
    assert not (evidence_root / "second-call").exists()


def test_source_and_test_are_the_only_non_output_worktree_changes():
    completed = subprocess.run(
        ["git", "status", "--short"],
        cwd=_REPO_ROOT,
        env=_clean_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    changed = {
        line[3:]
        for line in completed.stdout.splitlines()
        if line.strip() and not line[3:].startswith("output/")
    }
    assert changed <= {
        "orchestrator/campaign/p3_b4_wiring_probe.py",
        "orchestrator/tests/test_p3_b4_wiring_probe.py",
    }


def _run() -> int:
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
