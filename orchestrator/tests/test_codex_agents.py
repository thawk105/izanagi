# -*- coding: utf-8 -*-
"""Codex custom agent adapter の fail-closed 同期テスト。"""
from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_CHECKER = _REPO / "tools" / "check_codex_agents.py"
_SPEC = importlib.util.spec_from_file_location("check_codex_agents", _CHECKER)
assert _SPEC and _SPEC.loader
CCA = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = CCA
_SPEC.loader.exec_module(CCA)


def _fixture() -> Path:
    root = Path(tempfile.mkdtemp(prefix="izanagi-codex-agents-"))
    shutil.copytree(_REPO / ".claude" / "agents", root / ".claude" / "agents")
    shutil.copytree(_REPO / ".codex" / "agents", root / ".codex" / "agents")
    return root


def test_current_profiles_are_in_sync():
    assert CCA.check(_REPO) == []


def test_prompt_drift_is_rejected():
    root = _fixture()
    try:
        profile = root / ".codex" / "agents" / "critic.toml"
        profile.write_text(profile.read_text(encoding="utf-8") + "# drift\n", encoding="utf-8")
        assert any("drift" in finding for finding in CCA.check(root))
    finally:
        shutil.rmtree(root)


def test_invalid_toml_from_control_character_is_rejected():
    root = _fixture()
    try:
        source = root / ".claude" / "agents" / "verifier.md"
        data = source.read_bytes()
        assert data.endswith(b"\n")
        source.write_bytes(data[:-1] + b"\x00\n")
        assert any("TOML parse" in finding for finding in CCA.check(root))
    finally:
        shutil.rmtree(root)


def test_blocked_and_unknown_profiles_are_rejected():
    root = _fixture()
    try:
        blocked = root / ".codex" / "agents" / "planner-v4.toml"
        blocked.write_text('name = "planner-v4"\n', encoding="utf-8")
        extra = root / ".codex" / "agents" / "mystery.toml"
        extra.write_text('name = "mystery"\n', encoding="utf-8")
        findings = CCA.check(root)
        assert any("file-read" in finding for finding in findings)
        assert any("余分" in finding for finding in findings)
    finally:
        shutil.rmtree(root)


def test_missing_profile_is_rejected_and_write_repairs_it():
    root = _fixture()
    try:
        missing = root / ".codex" / "agents" / "verifier.toml"
        missing.unlink()
        assert any("欠落" in finding for finding in CCA.check(root))
        CCA.write_profiles(root)
        assert CCA.check(root) == []
    finally:
        shutil.rmtree(root)


def test_new_claude_role_must_be_classified():
    root = _fixture()
    try:
        (root / ".claude" / "agents" / "new-role.md").write_text(
            "---\nname: new-role\ndescription: test\ntools: []\nmodel: opus\neffort: high\n---\n\nbody\n",
            encoding="utf-8",
        )
        assert any("未分類 role" in finding for finding in CCA.check(root))
    finally:
        shutil.rmtree(root)


def test_claude_tool_contract_drift_requires_reclassification():
    root = _fixture()
    try:
        path = root / ".claude" / "agents" / "verifier.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(
            text.replace('tools: ["Read", "Grep", "Glob", "Bash"]', "tools: []", 1),
            encoding="utf-8",
        )
        assert any("source contract drift" in finding for finding in CCA.check(root))
    finally:
        shutil.rmtree(root)


def test_unquoted_hash_in_description_is_rejected():
    root = _fixture()
    try:
        path = root / ".claude" / "agents" / "coder.md"
        text = path.read_text(encoding="utf-8")
        quoted = next(line for line in text.splitlines() if line.startswith("description: "))
        decoded = __import__("json").loads(quoted.removeprefix("description: "))
        path.write_text(text.replace(quoted, f"description: {decoded}"), encoding="utf-8")
        assert any("JSON quote" in finding for finding in CCA.check(root))
    finally:
        shutil.rmtree(root)


def test_profiles_encode_permission_and_input_fail_closed_contracts():
    root = _fixture()
    try:
        CCA.write_profiles(root)
        for role in CCA.SUPPORTED:
            text = (root / ".codex" / "agents" / f"{role}.toml").read_text(encoding="utf-8")
            assert "ADAPTER-REFUSED" in text
            assert "親 turn の実効 sandbox を read-only" in text
            assert "Codex role-specific input override" in text
        critic = (root / ".codex" / "agents" / "critic.toml").read_text(encoding="utf-8")
        assert "digest.py` の自走許可はこの Codex adapter では無効" in critic
    finally:
        shutil.rmtree(root)


def _run():
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as exc:  # noqa: BLE001 - 単体 runner の集計
            failed += 1
            print(f"FAIL {test.__name__}: {exc}")
    print(f"{len(tests) - failed} passed, {failed} failed")
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(_run())
