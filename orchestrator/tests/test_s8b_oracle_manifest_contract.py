# -*- coding: utf-8 -*-
"""T-804 manifest/spec の伝播欠落を検知する限定的な機械契約。"""
from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from orchestrator.campaign import s8b_oracle_manifest as manifest  # noqa: E402


CAMPAIGN = ROOT / "orchestrator/campaign"

LOADER_EXPECTED_CONSUMERS = {
    "load_official_manifest": {
        "orchestrator/campaign/s8b_oracle_judge.py",
        "orchestrator/campaign/s8b_oracle_report.py",
    },
    "load_official_observations": {
        "orchestrator/campaign/s8b_oracle_judge.py",
        "orchestrator/campaign/s8b_verdict.py",
    },
    "load_official_verdict": {
        "orchestrator/campaign/s8b_verdict.py",
    },
}
VERIFY_EXPECTED_CONSUMERS = {
    "orchestrator/campaign/s8b_oracle_driver.py",
    "orchestrator/campaign/s8b_oracle_judge.py",
    "orchestrator/campaign/s8b_oracle_report.py",
    "orchestrator/campaign/s8b_verdict.py",
}


def _production_calls(function_names: set[str], *, module_leaf: str):
    def dotted_name(node) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            prefix = dotted_name(node.value)
            return None if prefix is None else f"{prefix}.{node.attr}"
        return None

    consumers = {name: set() for name in function_names}
    for path in sorted(CAMPAIGN.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        module_aliases: set[str] = set()
        direct_aliases: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for imported in node.names:
                    if imported.name.rsplit(".", 1)[-1] == module_leaf:
                        module_aliases.add(imported.asname or imported.name)
            elif isinstance(node, ast.ImportFrom):
                imported_module = (node.module or "").rsplit(".", 1)[-1]
                if imported_module == module_leaf:
                    for imported in node.names:
                        if imported.name in function_names:
                            direct_aliases[
                                imported.asname or imported.name
                            ] = imported.name
                else:
                    for imported in node.names:
                        if imported.name == module_leaf:
                            module_aliases.add(imported.asname or imported.name)
        relative = path.relative_to(ROOT).as_posix()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            called = node.func
            target = None
            if isinstance(called, ast.Name):
                target = direct_aliases.get(called.id)
            elif isinstance(called, ast.Attribute):
                owner = dotted_name(called.value)
                if owner in module_aliases and called.attr in function_names:
                    target = called.attr
            if target is not None:
                consumers[target].add(relative)
    return consumers


def test_loader_production_consumer_sets_are_pinned_for_spec_reverification():
    """直接呼出しと module 階層の import alias 解決までを捕捉する。

    動的 ``getattr`` / 動的 import は捕捉しない。この限定 AST inventory は
    loader-only consumer の追加を可視化するもので、全実行経路の全称保証ではない。
    """
    assert _production_calls(
        set(LOADER_EXPECTED_CONSUMERS),
        module_leaf="s8b_oracle_artifacts",
    ) == LOADER_EXPECTED_CONSUMERS


def test_verify_manifest_production_consumer_set_is_auxiliary_pin():
    """loader pin を補助する直接 caller inventory（動的呼出しは対象外）。"""
    calls = _production_calls(
        {"verify_manifest"}, module_leaf="s8b_oracle_manifest",
    )
    assert calls["verify_manifest"] == VERIFY_EXPECTED_CONSUMERS


def test_verify_manifest_public_and_seal_wrapper_signatures_require_approved_spec():
    signature = inspect.signature(manifest.verify_manifest)
    approved = signature.parameters["approved_spec"]
    assert approved.kind is inspect.Parameter.KEYWORD_ONLY
    assert approved.default is inspect.Parameter.empty

    tree = ast.parse(
        (CAMPAIGN / "s8b_oracle_manifest.py").read_text(encoding="utf-8")
    )
    wrapper = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "verified"
        and any(argument.arg == "approved_spec" for argument in node.args.kwonlyargs)
    )
    defaults = dict(zip(
        (argument.arg for argument in wrapper.args.kwonlyargs),
        wrapper.args.kw_defaults,
    ))
    assert defaults["approved_spec"] is None


def test_schema_v1_has_no_durable_manifest_candidate_or_reviewed_spec():
    durable_files = []
    for relative in (
        "output/s8b-oracle-manifest-candidates",
        "output/s8b-oracle-spec",
    ):
        directory = ROOT / relative
        if directory.exists():
            durable_files.extend(
                path.relative_to(ROOT).as_posix()
                for path in directory.rglob("*")
                if path.is_file()
            )
    assert durable_files == [], (
        "schema version 据え置きの前提が崩れた。durable artifact の再発行が要る: "
        f"{sorted(durable_files)!r}"
    )


def _run() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
