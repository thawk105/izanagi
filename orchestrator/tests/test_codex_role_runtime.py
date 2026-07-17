# -*- coding: utf-8 -*-
"""non-native Codex role runtimeの機械境界テスト（external model不使用）。"""
from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from orchestrator.codex_roles import launcher as L
from orchestrator.codex_roles import probe as P
from orchestrator.codex_roles.events import (
    EventValidationError,
    RunIdentity,
    canonical_json,
    encode_jsonl,
    enveloped_output_schema,
    strict_json_loads,
    validate_schema_instance,
    validate_event_stream,
)
from orchestrator.codex_roles.probe import (
    CODEX_0_144_2_UNKNOWN_MODEL_FALLBACK_TOOLS,
    AttestationExpectation,
    WireAttestationError,
    attest_request,
    attest_view_image_denial,
)
from tools import run_codex_role as R


IDENTITY = RunIdentity(
    role="critic",
    adapter_digest="a" * 64,
    instruction_digest="b" * 64,
    input_digest="c" * 64,
)
RESULT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["verdict"],
    "properties": {"verdict": {"type": "string", "enum": ["pass", "reject"]}},
}


def _valid_events(result: object | None = None):
    logical = {"verdict": "pass"} if result is None else result
    envelope = {
        "runtime": IDENTITY.echo(),
        "result_json": canonical_json(logical),
    }
    return [
        {"type": "thread.started", "thread_id": "019f6081-18f7-7641-ad28-4900c20873f5"},
        {"type": "turn.started"},
        {"type": "item.completed", "item": {
            "id": "msg_1", "type": "agent_message", "text": canonical_json(envelope),
        }},
        {"type": "turn.completed"},
    ]


def test_event_stream_requires_real_thread_and_two_stage_json_schema():
    validated = validate_event_stream(encode_jsonl(_valid_events()), IDENTITY, RESULT_SCHEMA)
    assert validated.thread_id == "019f6081-18f7-7641-ad28-4900c20873f5"
    assert validated.result == {"verdict": "pass"}
    assert len(validated.event_digest) == 64
    transport = enveloped_output_schema(RESULT_SCHEMA, IDENTITY)
    assert transport["required"] == ["runtime", "result_json"]
    assert transport["properties"]["result_json"] == {"type": "string"}
    assert all("enum" in prop for prop in
               transport["properties"]["runtime"]["properties"].values())


@pytest.mark.parametrize("item_type", [
    "command_execution", "file_change", "mcp_tool_call", "web_search", "plan",
    "view_image", "unknown_tool",
])
def test_jsonl_exposed_tool_or_unknown_item_is_rejected(item_type):
    events = _valid_events()
    events.insert(2, {"type": "item.completed", "item": {"type": item_type}})
    with pytest.raises(EventValidationError, match="許可外"):
        validate_event_stream(encode_jsonl(events), IDENTITY, RESULT_SCHEMA)


@pytest.mark.parametrize("mutation", [
    "natural-language", "duplicate-thread", "bad-thread", "uppercase-thread",
    "unknown-event",
    "after-complete", "missing-message", "digest-mismatch", "schema-mismatch",
    "duplicate-result-key", "result-bom", "result-cr", "result-non-nfc",
])
def test_event_stream_never_accepts_success_text_or_malformed_evidence(mutation):
    events = _valid_events()
    if mutation == "natural-language":
        events[2]["item"]["text"] = "SUCCESS"
    elif mutation == "duplicate-thread":
        events.insert(1, dict(events[0]))
    elif mutation == "bad-thread":
        events[0]["thread_id"] = "child-success"
    elif mutation == "uppercase-thread":
        events[0]["thread_id"] = events[0]["thread_id"].upper()
    elif mutation == "unknown-event":
        events.insert(2, {"type": "turn.progress"})
    elif mutation == "after-complete":
        events.append({"type": "item.completed", "item": {
            "type": "agent_message", "text": "{}",
        }})
    elif mutation == "missing-message":
        del events[2]
    else:
        envelope = json.loads(events[2]["item"]["text"])
        if mutation == "digest-mismatch":
            envelope["runtime"]["input_digest"] = "d" * 64
        elif mutation == "schema-mismatch":
            envelope["result_json"] = '{"verdict":"maybe"}'
        elif mutation == "duplicate-result-key":
            envelope["result_json"] = '{"verdict":"pass","verdict":"reject"}'
        elif mutation == "result-bom":
            envelope["result_json"] = '\ufeff{"verdict":"pass"}'
        elif mutation == "result-cr":
            envelope["result_json"] = '{\r"verdict":"pass"}'
        else:
            envelope["result_json"] = r'{"verdict":"\u0065\u0301"}'
        events[2]["item"]["text"] = canonical_json(envelope)
    with pytest.raises(EventValidationError):
        validate_event_stream(encode_jsonl(events), IDENTITY, RESULT_SCHEMA)


def test_jsonl_duplicate_key_and_size_limits_are_fail_closed():
    with pytest.raises(EventValidationError, match="重複"):
        strict_json_loads('{"x":1,"x":2}', label="fixture")
    raw = encode_jsonl(_valid_events())
    with pytest.raises(EventValidationError, match="上限"):
        validate_event_stream(raw, IDENTITY, RESULT_SCHEMA, max_bytes=len(raw) - 1)


@pytest.mark.parametrize("raw", [
    "NaN", "Infinity", "-Infinity", "1e999",
    "[" * 1100 + "]" * 1100,
    "9" * 5000,
    r'"\u0065\u0301"',
    r'"\ud800"',
])
def test_strict_json_normalizes_nonfinite_depth_and_integer_failures(raw):
    with pytest.raises(EventValidationError):
        strict_json_loads(raw, label="adversarial JSON")


def test_library_json_domain_rejects_nonfinite_and_canonical_nan():
    open_number_schema = {"type": "object", "additionalProperties": True}
    with pytest.raises(EventValidationError, match="非有限"):
        validate_schema_instance(
            {"value": float("inf")}, open_number_schema, label="library input"
        )
    with pytest.raises(EventValidationError, match="非有限"):
        canonical_json({"value": float("nan")})


def test_probe_thread_evidence_requires_canonical_uuid():
    thread_id = "019F6081-18F7-7641-AD28-4900C20873F5"
    raw = encode_jsonl([{"type": "thread.started", "thread_id": thread_id}])
    with pytest.raises(L.RuntimeIsolationError, match="canonical UUID"):
        L._extract_probe_thread_id(raw)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _wire_fixture(*, fallback_tools: bool = False):
    role_instructions = "ROLE-INSTRUCTIONS MARKER"
    user_prompt = "EXACT-PROJECTION input-digest"
    permissions = "<permissions instructions>fixed</permissions instructions>"
    runtime = ("BASE-RUNTIME", "TEAM-RUNTIME", "MODE-RUNTIME")
    environment = "<environment_context><cwd>/work</cwd></environment_context>"
    prompt_cache_key = "fixture-cache-key"
    schema = enveloped_output_schema(RESULT_SCHEMA, IDENTITY)
    fallback_instructions = "FIXED TOP LEVEL INSTRUCTIONS"
    fallback_tool_descriptors = [
        {"type": "function", "name": name, "parameters": {"type": "object"}}
        for name in sorted(CODEX_0_144_2_UNKNOWN_MODEL_FALLBACK_TOOLS)
    ]
    expected = AttestationExpectation(
        role="critic",
        model="fixture-model",
        reasoning_effort="high",
        reasoning_context="all_turns",
        adapter_digest="a" * 64,
        instruction_digest=_sha(role_instructions),
        input_digest="input-digest",
        marker="MARKER",
        developer_instructions=role_instructions,
        user_prompt=user_prompt,
        transport_schema_digest=_sha(canonical_json(schema)),
        expected_permissions_digest=_sha(permissions),
        expected_environment_digest=_sha(environment),
        prompt_cache_key_required=True,
        expected_client_metadata_keys=(),
        expected_text_verbosity="low",
        expected_runtime_developer_digests=tuple(_sha(value) for value in runtime),
        expected_additional_tools_digest=None,
        **({"expected_wire_tools": CODEX_0_144_2_UNKNOWN_MODEL_FALLBACK_TOOLS}
           if fallback_tools else {}),
        expected_wire_tools_digest=(
            _sha(canonical_json(fallback_tool_descriptors)) if fallback_tools else None
        ),
        expected_top_level_instructions_digest=(
            _sha(fallback_instructions) if fallback_tools else None
        ),
    )
    body = {
        "model": "fixture-model",
        "reasoning": {"effort": "high", "context": "all_turns"},
        "tool_choice": "auto",
        "parallel_tool_calls": False,
        "store": False,
        "stream": True,
        "include": ["reasoning.encrypted_content"],
        "prompt_cache_key": prompt_cache_key,
        "client_metadata": None,
        "text": {"verbosity": "low", "format": {
            "type": "json_schema", "strict": True,
            "name": "codex_output_schema", "schema": schema,
        }},
        "input": [
            {"type": "message", "role": "developer", "content": [
                {"type": "input_text", "text": runtime[0]},
            ]},
            {"type": "message", "role": "developer", "content": [
                {"type": "input_text", "text": permissions},
                {"type": "input_text", "text": role_instructions},
            ]},
            {"type": "message", "role": "developer", "content": [
                {"type": "input_text", "text": runtime[1]},
            ]},
            {"type": "message", "role": "developer", "content": [
                {"type": "input_text", "text": runtime[2]},
            ]},
            {"type": "message", "role": "user", "content": [
                {"type": "input_text", "text": (
                    environment
                )},
            ]},
            {"type": "message", "role": "user", "content": [
                {"type": "input_text", "text": user_prompt},
            ]},
        ],
    }
    if fallback_tools:
        body["tools"] = fallback_tool_descriptors
        body["instructions"] = fallback_instructions
    return body, expected


def test_wire_attestation_known_model_requires_absent_top_level_tools_key():
    body, expected = _wire_fixture()
    evidence = attest_request(body, expected, "/v1/responses")
    assert evidence.tool_names == ()
    assert evidence.tools_key_present is False
    assert evidence.model == "fixture-model"
    assert evidence.reasoning_effort == "high"
    assert evidence.developer_instruction_digest == expected.instruction_digest
    assert evidence.transport_schema_digest == expected.transport_schema_digest


def test_unknown_model_fallback_three_tools_are_separate_defense_fixture():
    body, base = _wire_fixture(fallback_tools=True)
    body["reasoning"] = None
    expected = AttestationExpectation(**{
        **base.__dict__,
        "reasoning_effort": None,
        "reasoning_context": None,
    })
    evidence = attest_request(body, expected)
    assert set(evidence.tool_names) == CODEX_0_144_2_UNKNOWN_MODEL_FALLBACK_TOOLS
    assert evidence.tools_key_present is True
    assert evidence.reasoning_effort is None
    body["reasoning"] = {}
    with pytest.raises(WireAttestationError, match="reasoning shape drift"):
        attest_request(body, expected)


def test_developer_additional_tools_are_evidence_and_force_live_block():
    body, base = _wire_fixture()
    item = {
        "type": "additional_tools",
        "role": "developer",
        "tools": [
            {"type": "custom", "name": "exec",
             "description": "declare const tools: { view_image(args: object): unknown; };"},
            {"type": "namespace", "name": "collaboration", "tools": [
                {"type": "function", "name": "spawn_agent"},
            ]},
        ],
    }
    body["input"].insert(0, item)
    expected = AttestationExpectation(
        **{
            **base.__dict__,
            "expected_additional_tools_digest": _sha(canonical_json(item)),
            "expected_additional_tool_names": ("collaboration", "exec"),
            "expected_declared_nested_tool_names": ("spawn_agent", "view_image"),
        }
    )
    evidence = attest_request(body, expected)
    assert evidence.live_blocked
    assert evidence.additional_tool_names == ("collaboration", "exec")
    assert evidence.declared_nested_tool_names == ("spawn_agent", "view_image")


@pytest.mark.parametrize("mutation", [
    "tools-key", "tool-choice", "parallel", "model", "effort", "context",
    "developer", "runtime", "user", "schema", "cwd", "top-extra",
    "store", "stream", "include", "developer-image", "developer-order",
    "message-field", "user-order", "tool-history", "client-metadata",
    "prompt-cache", "text-field", "verbosity", "environment",
])
def test_wire_attestation_drift_is_rejected(mutation):
    body, expected = _wire_fixture()
    if mutation == "tools-key":
        body["tools"] = []
    elif mutation == "tool-choice":
        body["tool_choice"] = "none"
    elif mutation == "parallel":
        body["parallel_tool_calls"] = True
    elif mutation == "model":
        body["model"] = "other"
    elif mutation == "effort":
        body["reasoning"]["effort"] = "low"
    elif mutation == "context":
        body["reasoning"]["context"] = "turn"
    elif mutation == "developer":
        body["input"][1]["content"][1]["text"] += " drift"
    elif mutation == "runtime":
        body["input"][0]["content"].append({"type": "input_text", "text": "EXTRA"})
    elif mutation == "user":
        body["input"].append({"type": "message", "role": "user", "content": [
            {"type": "input_text", "text": "EXTRA"},
        ]})
    elif mutation == "schema":
        body["text"]["format"]["schema"]["properties"]["result_json"] = {
            "type": "integer"
        }
    elif mutation == "cwd":
        body["input"][4]["content"][0]["text"] = (
            "<environment_context><cwd>/repo</cwd></environment_context>"
        )
    elif mutation == "top-extra":
        body["instructions"] = "ATTACK"
    elif mutation == "store":
        body["store"] = True
    elif mutation == "stream":
        body["stream"] = False
    elif mutation == "include":
        body["include"] = []
    elif mutation == "client-metadata":
        body["client_metadata"] = {}
    elif mutation == "prompt-cache":
        body["prompt_cache_key"] = ""
    elif mutation == "text-field":
        body["text"]["extra"] = True
    elif mutation == "verbosity":
        body["text"]["verbosity"] = "medium"
    elif mutation == "environment":
        body["input"][4]["content"][0]["text"] += "<extra>drift</extra>"
    elif mutation == "developer-image":
        body["input"][1]["content"][0] = {
            "type": "input_image", "image_url": "data:image/png;base64,AA==",
        }
    elif mutation == "developer-order":
        body["input"][0], body["input"][1] = body["input"][1], body["input"][0]
    elif mutation == "message-field":
        body["input"][1]["unexpected"] = True
    elif mutation == "user-order":
        body["input"][4], body["input"][5] = body["input"][5], body["input"][4]
    else:
        body["input"].append({
            "type": "function_call", "name": "view_image",
            "arguments": "{}", "call_id": "call_unexpected",
        })
    with pytest.raises(WireAttestationError):
        attest_request(body, expected)


def test_forced_tool_history_is_exact_and_explicitly_scoped():
    body, base = _wire_fixture(fallback_tools=True)
    expected = AttestationExpectation(**{**base.__dict__, "allow_tool_history": True})
    body["input"].extend([
        {"type": "function_call", "name": "view_image", "arguments": "{}",
         "call_id": "call_1"},
        {"type": "function_call_output", "call_id": "call_1", "output": "ENOENT"},
    ])
    with pytest.raises(WireAttestationError, match="first/通常probe"):
        attest_request(body, expected)
    attest_request(body, expected, require_tool_history=True)
    body["input"][-1]["extra"] = "drift"
    with pytest.raises(WireAttestationError, match="history shape drift"):
        attest_request(body, expected, require_tool_history=True)


def test_top_level_instructions_and_tool_descriptor_digests_are_pinned():
    body, expected = _wire_fixture(fallback_tools=True)
    body["instructions"] += " drift"
    with pytest.raises(WireAttestationError, match="instructions digest"):
        attest_request(body, expected)
    body, expected = _wire_fixture(fallback_tools=True)
    body["tools"][0]["description"] = "drift"
    with pytest.raises(WireAttestationError, match="tool descriptor digest"):
        attest_request(body, expected)


def test_dynamic_metadata_has_exact_keys_and_prompt_cache_is_typed_evidence():
    body, base = _wire_fixture()
    keys = ("session_id", "thread_id")
    body["client_metadata"] = {key: f"value-{key}" for key in keys}
    expected = AttestationExpectation(**{
        **base.__dict__, "expected_client_metadata_keys": keys,
    })
    first = attest_request(body, expected)
    first_prompt_digest = first.prompt_cache_key_digest
    body["prompt_cache_key"] = "new-per-turn-cache-key"
    second = attest_request(body, expected)
    assert second.prompt_cache_key_digest != first_prompt_digest
    body["client_metadata"]["unexpected"] = "drift"
    with pytest.raises(WireAttestationError, match="client_metadata shape drift"):
        attest_request(body, expected)


@pytest.mark.parametrize("raw", [
    b'{"x":1,"x":2}',
    b'{"x":NaN}',
    b'{"x":Infinity}',
    b'{"x":1e999}',
    '{"x":1}'.encode("utf-16"),
])
def test_http_request_body_uses_strict_utf8_and_strict_json(raw):
    with pytest.raises(WireAttestationError):
        P._strict_request_body(raw, label="fixture request")


def test_raw_function_call_output_proves_view_image_enoent_not_self_report():
    target = "/host/repository/secret.png"
    body = {"input": [
        {"type": "function_call", "name": "view_image", "call_id": "call_1",
         "arguments": json.dumps({"path": target})},
        {"type": "function_call_output", "call_id": "call_1",
         "output": f"unable to locate image at `{target}`: No such file or directory (os error 2)"},
    ]}
    evidence = attest_view_image_denial(body, target)
    assert evidence.call_id == "call_1"
    assert "No such file or directory" in evidence.function_call_output
    assert len(evidence.followup_request_digest) == 64
    body["input"][1]["output"] = "SUCCESS"
    with pytest.raises(WireAttestationError):
        attest_view_image_denial(body, target)


def test_launcher_uses_actual_adapter_and_rejects_schema_invalid_input():
    material = L._safe_adapter("critic", {"digest": {}}, L.RuntimeOptions())
    assert material.spec.name == "critic"
    assert material.adapter_digest == hashlib.sha256(
        (_REPO / ".codex/role-adapters/critic.json").read_bytes()
    ).hexdigest()
    with pytest.raises(EventValidationError):
        L._safe_adapter("critic", {}, L.RuntimeOptions())


def test_command_keeps_legacy_readonly_layer_and_disables_surfaces():
    material = L._safe_adapter("critic", {"digest": {}}, L.RuntimeOptions())
    args = L._codex_args(material, provider_base_url="http://127.0.0.1:1/v1")
    assert args[:5] == [
        "/opt/izanagi-codex/codex", "--ask-for-approval", "never",
        "--sandbox", "read-only",
    ]
    assert "--ignore-user-config" in args and "--ignore-rules" in args
    assert "mcp_servers={}" in args
    assert "tools.view_image=false" not in args
    for feature in ("apps", "hooks", "multi_agent", "plugins", "shell_tool",
                    "unified_exec", "use_agent_identity"):
        assert any(args[i:i + 2] == ["--disable", feature]
                   for i in range(len(args) - 1))
    with pytest.raises(L.RuntimeIsolationError, match="127.0.0.1"):
        L._codex_args(material, provider_base_url="https://api.openai.com/v1")
    fixture_args = L._forced_view_image_args(
        material,
        provider_base_url="http://127.0.0.1:12345/v1",
        model="fixture-model",
    )
    assert fixture_args[fixture_args.index("--sandbox") + 1] == "danger-full-access"


def test_containment_helper_predicate_accepts_readonly_fs_but_not_writable_mode(
        tmp_path, monkeypatch):
    helper = tmp_path / "busybox"
    helper.write_bytes(b"fixture")
    helper.chmod(0o755)

    class _ReadOnlyStatvfs:
        f_flag = os.ST_RDONLY

    monkeypatch.setattr(L.os, "statvfs", lambda _path: _ReadOnlyStatvfs())
    assert L._is_trusted_readonly_helper(helper)
    helper.chmod(0o775)
    assert not L._is_trusted_readonly_helper(helper)


def test_prepared_runtime_executes_private_verified_binary_copies(
        tmp_path, monkeypatch):
    source_dir = tmp_path / "source"
    resource_dir = source_dir / "codex-resources"
    resource_dir.mkdir(parents=True)
    source_codex = source_dir / "codex"
    source_bwrap = resource_dir / "bwrap"
    codex_bytes = b"fixture-codex"
    bwrap_bytes = b"fixture-bwrap"
    source_codex.write_bytes(codex_bytes)
    source_bwrap.write_bytes(bwrap_bytes)
    source_codex.chmod(0o755)
    source_bwrap.chmod(0o755)
    monkeypatch.setattr(L, "_CODEX_0_144_2_BINARY_DIGEST", hashlib.sha256(
        codex_bytes
    ).hexdigest())
    monkeypatch.setattr(L, "_CODEX_0_144_2_BINARY_SIZE", len(codex_bytes))
    monkeypatch.setattr(L, "_CODEX_0_144_2_BWRAP_DIGEST", hashlib.sha256(
        bwrap_bytes
    ).hexdigest())
    monkeypatch.setattr(L, "_CODEX_0_144_2_BWRAP_SIZE", len(bwrap_bytes))
    monkeypatch.setattr(
        L, "_resolve_binary_layout",
        lambda _value: L._BinaryLayout(
            codex=source_codex, codex_dir=source_dir, bwrap=source_bwrap
        ),
    )
    material = SimpleNamespace(adapter_text="{}", transport_schema={})
    options = L.RuntimeOptions(temp_parent=tmp_path)
    with L._PreparedRuntime(material, options) as layout:
        assert layout.binary.codex.is_relative_to(layout.root)
        assert layout.binary.bwrap == (
            layout.binary.codex.parent / "codex-resources" / "bwrap"
        )
        source_codex.write_bytes(b"source-mutated")
        source_bwrap.write_bytes(b"source-mutated")
        assert layout.binary.codex.read_bytes() == codex_bytes
        assert layout.binary.bwrap.read_bytes() == bwrap_bytes
        assert not layout.binary.codex.stat().st_mode & 0o022
        assert not layout.binary.bwrap.stat().st_mode & 0o022


def test_verified_executable_copy_rejects_symlink_source(tmp_path):
    target = tmp_path / "target"
    target.write_bytes(b"binary")
    target.chmod(0o755)
    link = tmp_path / "link"
    link.symlink_to(target)
    with pytest.raises(L.RuntimeIsolationError, match="openできない"):
        L._copy_verified_executable(
            link,
            tmp_path / "copy",
            expected_digest=hashlib.sha256(b"binary").hexdigest(),
            expected_size=len(b"binary"),
        )


def test_cli_file_input_read_is_bounded_to_max_plus_one(monkeypatch):
    class _TrackingStream(io.BytesIO):
        def read(self, size=-1):
            assert size == L.MAX_PROMPT_BYTES + 1
            return b"x" * size

    stream = _TrackingStream()
    monkeypatch.setattr(R.Path, "open", lambda *_args, **_kwargs: stream)
    with pytest.raises(EventValidationError, match="size上限超過"):
        R._read_input("fixture.json")


@pytest.mark.skipif(not shutil.which("busybox"), reason="busybox required")
def test_containment_helper_rejects_nonroot_parent_on_writable_fs(monkeypatch):
    helper = Path(shutil.which("busybox")).resolve(strict=True)
    immediate_parent = helper.parent
    original_stat = Path.stat
    simulated_parent_uid = {"value": 1234}

    def _root_owned_except_parent(path, *args, **kwargs):
        observed = original_stat(path, *args, **kwargs)
        fields = list(observed)
        fields[4] = (
            simulated_parent_uid["value"] if path == immediate_parent else 0
        )
        return os.stat_result(fields)

    class _WritableStatvfs:
        f_flag = 0

    monkeypatch.setattr(Path, "stat", _root_owned_except_parent)
    monkeypatch.setattr(L.os, "statvfs", lambda _path: _WritableStatvfs())
    assert not L._is_trusted_readonly_helper(helper)
    simulated_parent_uid["value"] = 0
    assert L._is_trusted_readonly_helper(helper)


def _codex_runtime_available() -> bool:
    codex = shutil.which("codex")
    busybox = shutil.which("busybox")
    return bool(
        codex
        and (Path(codex).resolve().parent / "codex-resources/bwrap").exists()
        and busybox
        and L._is_trusted_readonly_helper(Path(busybox))
    )


def test_runtime_commit_prerequisites_are_available():
    """pinned runtime の在庫番人 (D60)。

    codex の auto-update はピン (SUPPORTED_CODEX_VERSION + 同梱 bwrap) を黙って
    動かすため、無条件 hard-fail だと無関係な作業まで全マシンで恒常 fail になる。
    既定は理由付き skip (計数される) とし、codex_roles を触る作業・D56 再開儀式
    では IZANAGI_REQUIRE_CODEX_RUNTIME=1 で従来の hard-fail に戻して回す。
    実行時の fail-closed (launcher の version/digest/bwrap 検証) は不変。
    """
    if _codex_runtime_available():
        return
    assert not os.environ.get("IZANAGI_REQUIRE_CODEX_RUNTIME"), (
        "commit/release runtime gate requires pinned Codex, bundled bwrap, "
        "and trusted busybox; skip-only is not success"
    )
    pytest.skip(
        "pinned Codex runtime 不在 (codex auto-update での drift 等)。codex_roles を"
        "変更する作業と D56 再開儀式では IZANAGI_REQUIRE_CODEX_RUNTIME=1 で"
        "hard-fail に戻すこと (D60)"
    )


@pytest.mark.skipif(not _codex_runtime_available(), reason="bundled Codex/bwrap/busybox required")
def test_real_sol_and_terra_capture_hidden_additional_tools_and_block_live():
    sol = L.attest_role("critic", {"digest": {}}, L.RuntimeOptions(probe_timeout_s=15))
    terra = L.attest_role(
        "calibrator", {"request": {}, "measurements": [{"records": 1}]},
        L.RuntimeOptions(probe_timeout_s=15),
    )
    assert sol.wire.model == "gpt-5.6-sol"
    assert terra.wire.model == "gpt-5.6-terra"
    assert sol.wire.runtime_developer_digests[0] == (
        "e9778714d505f3dd04d44db4394024c5fab5bf6554fc9faa3cdf9cf776b63bb9"
    )
    assert terra.wire.runtime_developer_digests[0] == (
        "78a2fc84e1bffa421d865c1a2ade4185d3d33ef38e6a15157f0ff1a89b7d52ec"
    )
    for evidence in (sol, terra):
        assert evidence.status == L.BLOCKED_BY_RUNTIME_TOOL_SURFACE
        assert str(uuid.UUID(evidence.thread_id)) == evidence.thread_id
        assert evidence.wire.tool_names == ()
        assert evidence.wire.tools_key_present is False
        assert evidence.wire.live_blocked
        assert evidence.wire.response_include == ("reasoning.encrypted_content",)
        assert evidence.wire.environment_digest == (
            "a7dced4f994ca165603978151dc718d1fd3dcba2a6c23b34d21b5aa90f426349"
        )
        assert evidence.wire.text_verbosity == "low"
        assert evidence.wire.top_level_instructions_digest is None
        assert evidence.wire.prompt_cache_key_digest is not None
        assert evidence.wire.prompt_cache_key_length
        assert evidence.wire.client_metadata_digest is not None
        assert evidence.wire.client_metadata_keys == tuple(sorted(
            L._CODEX_0_144_2_CLIENT_METADATA_KEYS
        ))
        assert evidence.wire.additional_tools_digest == (
            "309eaf3ca046b9830a0929e20090508c90edfefa462288db1e893b06114e4495"
        )
        assert evidence.wire.additional_tool_names == (
            "collaboration", "exec", "request_user_input", "wait"
        )
        assert "spawn_agent" in evidence.wire.declared_nested_tool_names
        assert "view_image" in evidence.wire.declared_nested_tool_names
        assert evidence.containment.stage_readable
        assert evidence.containment.host_canary_hidden
        assert evidence.containment.helper_binary_digest == L._sha256_file(
            Path(shutil.which("busybox")).resolve(strict=True)
        )


@pytest.mark.skipif(not _codex_runtime_available(), reason="bundled Codex/bwrap/busybox required")
def test_live_role_is_unconditionally_blocked_after_measured_preflight():
    with pytest.raises(L.RuntimeIsolationError, match="BLOCKED_BY_RUNTIME_TOOL_SURFACE"):
        L.run_role("critic", {"digest": {}}, L.RuntimeOptions(probe_timeout_s=15))


@pytest.mark.skipif(not _codex_runtime_available(), reason="bundled Codex/bwrap/busybox required")
def test_real_forced_view_image_fixture_observes_host_path_enoent():
    evidence = L.attest_forced_view_image_containment(
        "critic", {"digest": {}}, L.RuntimeOptions(probe_timeout_s=15)
    )
    assert str(uuid.UUID(evidence.thread_id)) == evidence.thread_id
    assert set(evidence.wire.tool_names) == CODEX_0_144_2_UNKNOWN_MODEL_FALLBACK_TOOLS
    assert evidence.wire.tool_schema_digest == (
        "2925c460ec5c7b533e5c21603307fa3bce82963fc3df58e6b5ebc8fa6cab33e3"
    )
    assert evidence.wire.top_level_instructions_digest == (
        "ac8ae107a0d72fe3476b430afb161ea4e67da2e446d778aefc44828160559807"
    )
    assert evidence.wire.response_include == ()
    assert evidence.wire.environment_digest == (
        "69ddb0302e5abc401bc98703fc8b1c4838ab1232e48793217ab3ebf95c885cda"
    )
    assert evidence.wire.text_verbosity is None
    assert evidence.wire.prompt_cache_key_digest is not None
    assert evidence.wire.client_metadata_digest is not None
    assert evidence.view_image.requested_path.endswith("host-only-canary.png")
    assert evidence.view_image.call_id == "call_izanagi_probe"
    assert evidence.view_image.requested_path in evidence.view_image.function_call_output
    assert "No such file or directory" in evidence.view_image.function_call_output
    assert len(evidence.view_image.followup_request_digest) == 64
    assert evidence.containment.host_canary_hidden
