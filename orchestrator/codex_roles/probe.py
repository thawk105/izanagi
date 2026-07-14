"""Codex Responses request を loopback で実測する fail-closed probe。

Codex 0.144.2のknown sol/terraではtop-level ``tools`` keyが無くてもdeveloper inputの
``additional_tools``にexec/collaboration等が残る。unknown-model fallbackではさらに
top-level builtin 3件も現れる。このmoduleはcustom providerを一時loopback endpointへ
向け、外部送信せずraw request全体の該当surfaceを検査する。production proxyではない。

requestを書き換えてtool-freeと自己申告しない。additional_toolsを除去できない現在、
live roleはBLOCKED。outer bubblewrapとforced view_image ENOENTはdefense-in-depth証拠で
あり、active化の根拠にはしない。
"""
from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Mapping

from .events import EventValidationError, canonical_json, strict_json_loads


MAX_REQUEST_BYTES = 16 * 1024 * 1024

# 0.144.2 bundled catalogのknown sol/terraはcode_mode_only。code_modeを無効化した
# captureではtop-level ``body.tools`` keyが無い。ただしinput.additional_toolsは残るので
# 総合tool-freeではない。unknown model fallbackではtop-levelにも下記3件が残る。
CODEX_0_144_2_KNOWN_MODEL_TOP_LEVEL_TOOLS = frozenset()
CODEX_0_144_2_UNKNOWN_MODEL_FALLBACK_TOOLS = frozenset({
    "request_user_input",
    "update_plan",
    "view_image",
})
CODEX_0_144_2_UNKNOWN_MODEL_INSTRUCTIONS_DIGEST = (
    "ac8ae107a0d72fe3476b430afb161ea4e67da2e446d778aefc44828160559807"
)
CODEX_0_144_2_RESPONSE_INCLUDE = ("reasoning.encrypted_content",)
CODEX_0_144_2_ADDITIONAL_TOOLS_DIGEST = (
    "309eaf3ca046b9830a0929e20090508c90edfefa462288db1e893b06114e4495"
)
CODEX_0_144_2_ADDITIONAL_TOOL_NAMES = (
    "collaboration", "exec", "request_user_input", "wait",
)
CODEX_0_144_2_DECLARED_NESTED_TOOL_NAMES = (
    "apply_patch", "followup_task", "interrupt_agent", "list_agents",
    "send_message", "spawn_agent", "update_plan", "view_image", "wait_agent",
)
_DECLARED_TOOL_RE = re.compile(
    r"declare const tools: \{\s*([A-Za-z0-9_]+)\s*\("
)


class WireAttestationError(RuntimeError):
    """Responses request が固定した runtime 契約から外れた。"""


@dataclass(frozen=True)
class AttestationExpectation:
    role: str
    model: str
    reasoning_effort: str | None
    reasoning_context: str | None
    adapter_digest: str
    instruction_digest: str
    input_digest: str
    marker: str
    developer_instructions: str
    user_prompt: str
    transport_schema_digest: str
    expected_permissions_digest: str
    expected_environment_digest: str
    prompt_cache_key_required: bool
    expected_client_metadata_keys: tuple[str, ...]
    expected_text_verbosity: str | None
    expected_runtime_developer_digests: tuple[str, ...]
    expected_additional_tools_digest: str | None
    expected_additional_tool_names: tuple[str, ...] = ()
    expected_declared_nested_tool_names: tuple[str, ...] = ()
    expected_wire_tools: frozenset[str] = CODEX_0_144_2_KNOWN_MODEL_TOP_LEVEL_TOOLS
    expected_wire_tools_digest: str | None = None
    expected_top_level_instructions_digest: str | None = None
    expected_include: tuple[str, ...] = CODEX_0_144_2_RESPONSE_INCLUDE
    allow_tool_history: bool = False


@dataclass(frozen=True)
class WireAttestation:
    """実際に capture した request から計算した evidence。"""

    role: str
    model: str
    reasoning_effort: str | None
    reasoning_context: str | None
    tools_key_present: bool
    tool_names: tuple[str, ...]
    tool_choice: str
    parallel_tool_calls: bool
    tool_schema_digest: str
    permissions_instruction_digest: str
    runtime_developer_digests: tuple[str, ...]
    developer_instruction_digest: str
    transport_schema_digest: str
    top_level_instructions_digest: str | None
    response_include: tuple[str, ...]
    environment_digest: str
    prompt_cache_key_digest: str | None
    prompt_cache_key_length: int | None
    client_metadata_digest: str | None
    client_metadata_keys: tuple[str, ...]
    text_verbosity: str | None
    input_item_types: tuple[str, ...]
    additional_tools_digest: str | None
    additional_tool_names: tuple[str, ...]
    declared_nested_tool_names: tuple[str, ...]
    live_blocked: bool
    request_digest: str
    request_path: str


@dataclass(frozen=True)
class ViewImageContainmentAttestation:
    """raw Responses turnで観測したview_image ENOENTの構造化証拠。"""

    requested_path: str
    call_id: str
    function_call_output: str
    error_output_digest: str
    followup_request_digest: str


def _tool_name(tool: Any) -> str:
    if not isinstance(tool, dict):
        raise WireAttestationError("Responses tools の要素がobjectでない")
    name = tool.get("name")
    if not isinstance(name, str):
        function = tool.get("function")
        if isinstance(function, dict):
            name = function.get("name")
    if not isinstance(name, str) or not name:
        raise WireAttestationError(f"Responses tool name を取得できない: {tool!r}")
    return name


def extract_tool_names(body: Mapping[str, Any]) -> tuple[str, ...]:
    if "tools" not in body:
        return ()
    tools = body["tools"]
    if not isinstance(tools, list):
        raise WireAttestationError("Responses request の tools がarrayでない")
    names = tuple(_tool_name(tool) for tool in tools)
    if len(names) != len(set(names)):
        raise WireAttestationError(f"Responses tool name が重複: {names!r}")
    return tuple(sorted(names))


def _message_texts(entry: Any, *, role: str, label: str) -> tuple[str, ...]:
    if not isinstance(entry, Mapping) or set(entry) != {"type", "role", "content"}:
        raise WireAttestationError(f"{label} message field drift")
    if entry.get("type") != "message" or entry.get("role") != role:
        raise WireAttestationError(f"{label} message type/role drift")
    content = entry.get("content")
    if not isinstance(content, list) or not content:
        raise WireAttestationError(f"{label} message contentが非空arrayでない")
    texts: list[str] = []
    for part in content:
        if (not isinstance(part, Mapping)
                or set(part) != {"type", "text"}
                or part.get("type") != "input_text"
                or not isinstance(part.get("text"), str)):
            raise WireAttestationError(f"{label} content part shape drift")
        texts.append(part["text"])
    return tuple(texts)


def _text_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _attest_message_sequence(
        entries: list[Any], expectation: AttestationExpectation, *,
        start: int, require_tool_history: bool,
) -> tuple[str, tuple[str, ...], str]:
    """developer/user/historyを観測順・exact field setで固定する。"""

    runtime_digests = expectation.expected_runtime_developer_digests
    developer_groups = len(runtime_digests) + 1
    minimum = start + developer_groups + 2
    if len(entries) < minimum:
        raise WireAttestationError("Responses input message sequenceが短い")

    developer_text_groups = [
        _message_texts(
            entries[start + index], role="developer",
            label=f"developer[{index}]",
        )
        for index in range(developer_groups)
    ]
    if runtime_digests:
        expected_lengths = (1, 2) + (1,) * (len(runtime_digests) - 1)
        observed_lengths = tuple(len(group) for group in developer_text_groups)
        if observed_lengths != expected_lengths:
            raise WireAttestationError(
                "developer content grouping drift: "
                f"observed={observed_lengths!r}, expected={expected_lengths!r}"
            )
        runtime_texts = (
            developer_text_groups[0][0],
            *(group[0] for group in developer_text_groups[2:]),
        )
        permissions_and_role = developer_text_groups[1]
    else:
        if tuple(len(group) for group in developer_text_groups) != (2,):
            raise WireAttestationError("forced developer content grouping drift")
        runtime_texts = ()
        permissions_and_role = developer_text_groups[0]

    permissions, role_instructions = permissions_and_role
    permissions_digest = _text_digest(permissions)
    observed_runtime_digests = tuple(_text_digest(text) for text in runtime_texts)
    if (not permissions.startswith("<permissions instructions>")
            or permissions_digest != expectation.expected_permissions_digest
            or role_instructions != expectation.developer_instructions
            or observed_runtime_digests != runtime_digests):
        raise WireAttestationError(
            "developer surface drift: generated permissions/role/runtime digestが固定契約外 "
            f"(runtime_digests={observed_runtime_digests!r})"
        )

    user_start = start + developer_groups
    environment_texts = _message_texts(
        entries[user_start], role="user", label="generated environment"
    )
    projected_texts = _message_texts(
        entries[user_start + 1], role="user", label="projected user"
    )
    if len(environment_texts) != 1 or not environment_texts[0].startswith(
            "<environment_context>"):
        raise WireAttestationError("generated environment message shape drift")
    if "<cwd>/work</cwd>" not in environment_texts[0]:
        raise WireAttestationError("generated environment cwdがneutral /workでない")
    environment_digest = _text_digest(environment_texts[0])
    if environment_digest != expectation.expected_environment_digest:
        raise WireAttestationError(
            "generated environment digest drift: "
            f"observed={environment_digest}, "
            f"expected={expectation.expected_environment_digest}"
        )
    if projected_texts != (expectation.user_prompt,):
        raise WireAttestationError("canonical projected user prompt完全一致1件でない")

    history = entries[user_start + 2:]
    if not require_tool_history:
        if history:
            raise WireAttestationError("first/通常probeにtool historyが混入")
        return permissions_digest, observed_runtime_digests, environment_digest
    if not expectation.allow_tool_history:
        raise WireAttestationError("tool history requirementとexpectationが矛盾")
    if len(history) != 2:
        raise WireAttestationError("forced followup tool historyは正確に2件必要")
    call, output = history
    if (not isinstance(call, Mapping)
            or set(call) != {"type", "name", "arguments", "call_id"}
            or call.get("type") != "function_call"
            or not all(isinstance(call.get(key), str) and call.get(key)
                       for key in ("name", "arguments", "call_id"))):
        raise WireAttestationError("function_call history shape drift")
    if (not isinstance(output, Mapping)
            or set(output) != {"type", "call_id", "output"}
            or output.get("type") != "function_call_output"
            or output.get("call_id") != call.get("call_id")
            or not isinstance(output.get("output"), str)):
        raise WireAttestationError("function_call_output history shape drift")
    return permissions_digest, observed_runtime_digests, environment_digest


def _transport_schema(body: Mapping[str, Any]) -> Mapping[str, Any]:
    text = body.get("text")
    if not isinstance(text, Mapping):
        raise WireAttestationError("Responses request の text がobjectでない")
    output_format = text.get("format")
    if not isinstance(output_format, Mapping):
        raise WireAttestationError("Responses request の text.format がobjectでない")
    if output_format.get("type") != "json_schema":
        raise WireAttestationError(
            f"Responses text.format.typeがjson_schemaでない: {output_format.get('type')!r}"
        )
    if output_format.get("strict") is not True:
        raise WireAttestationError("Responses text.format.strictがtrueでない")
    if output_format.get("name") != "codex_output_schema":
        raise WireAttestationError("Responses text.format.name drift")
    if set(output_format) != {"type", "strict", "schema", "name"}:
        raise WireAttestationError(
            f"Responses text.format field drift: {sorted(output_format)}"
        )
    schema = output_format.get("schema")
    if not isinstance(schema, Mapping):
        raise WireAttestationError("Responses text.format.schemaがobjectでない")
    return schema


def _additional_tool_surface(
        body: Mapping[str, Any], expectation: AttestationExpectation,
) -> tuple[tuple[str, ...], str | None, tuple[str, ...], tuple[str, ...]]:
    entries = body.get("input")
    if not isinstance(entries, list):
        raise WireAttestationError("Responses request の input がarrayでない")
    item_types: list[str] = []
    additional: list[Mapping[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, Mapping) or not isinstance(entry.get("type"), str):
            raise WireAttestationError("Responses input itemのtypeが不正")
        item_types.append(entry["type"])
        if entry["type"] == "additional_tools":
            additional.append(entry)
    expected_digest = expectation.expected_additional_tools_digest
    if expected_digest is None:
        if additional:
            raise WireAttestationError("予期しないadditional_tools developer surfaceを検出")
        return tuple(item_types), None, (), ()
    if len(additional) != 1:
        raise WireAttestationError(
            f"additional_tools itemは正確に1件必要 (observed={len(additional)})"
        )
    if entries[0] is not additional[0]:
        raise WireAttestationError("additional_tools itemはResponses input先頭固定")
    item = additional[0]
    # exec description内のexamples、ALL_TOOLSという動的入口、全schema/grammarを含む
    # descriptor item全体をbyte-stable canonical digestでpinする。下のdeclared namesは
    # 人が読める補助inventoryであり、availabilityの全数保証ではない。
    observed_digest = hashlib.sha256(
        canonical_json(dict(item)).encode("utf-8")
    ).hexdigest()
    tools = item.get("tools")
    if not isinstance(tools, list):
        raise WireAttestationError("additional_tools.toolsがarrayでない")
    top_names: list[str] = []
    nested_names: set[str] = set()
    for tool in tools:
        if not isinstance(tool, Mapping) or not isinstance(tool.get("name"), str):
            raise WireAttestationError("additional tool nameが不正")
        top_names.append(tool["name"])
        description = tool.get("description")
        if isinstance(description, str):
            nested_names.update(_DECLARED_TOOL_RE.findall(description))
        children = tool.get("tools", [])
        if not isinstance(children, list):
            raise WireAttestationError("additional namespace toolsがarrayでない")
        for child in children:
            if not isinstance(child, Mapping) or not isinstance(child.get("name"), str):
                raise WireAttestationError("additional nested tool nameが不正")
            nested_names.add(child["name"])
    top = tuple(sorted(top_names))
    nested = tuple(sorted(nested_names))
    if (observed_digest != expected_digest
            or top != tuple(sorted(expectation.expected_additional_tool_names))
            or nested != tuple(sorted(expectation.expected_declared_nested_tool_names))):
        raise WireAttestationError(
            "additional_tools surface drift: "
            f"digest={observed_digest}, top={top!r}, declared_nested={nested!r}"
        )
    return tuple(item_types), observed_digest, top, nested


def attest_request(body: Mapping[str, Any], expectation: AttestationExpectation,
                   path: str = "/v1/responses", *,
                   require_tool_history: bool = False) -> WireAttestation:
    """raw request を検査し、変更せずに attestation を返す。"""

    if not isinstance(body, Mapping):
        raise WireAttestationError("Responses request body はobjectでなければならない")
    if path != "/v1/responses":
        raise WireAttestationError(f"Responses request path drift: {path!r}")
    expected_top_keys = {
        "model", "input", "tool_choice", "parallel_tool_calls", "reasoning",
        "store", "stream", "include", "prompt_cache_key", "text",
        "client_metadata",
    }
    if expectation.expected_wire_tools:
        expected_top_keys.add("tools")
    if expectation.expected_top_level_instructions_digest is not None:
        expected_top_keys.add("instructions")
    if set(body) != expected_top_keys:
        raise WireAttestationError(
            "Responses top-level field drift: "
            f"observed={sorted(body)}, expected={sorted(expected_top_keys)}"
        )
    if body.get("store") is not False or body.get("stream") is not True:
        raise WireAttestationError("Responses store/stream固定値がdrift")
    client_metadata = body.get("client_metadata")
    expected_client_keys = expectation.expected_client_metadata_keys
    if not expected_client_keys and client_metadata is None:
        observed_client_metadata_digest = None
    elif (expected_client_keys
            and isinstance(client_metadata, Mapping)
            and tuple(sorted(client_metadata)) == tuple(sorted(expected_client_keys))
            and all(isinstance(value, str) and value
                    for value in client_metadata.values())):
        observed_client_metadata_digest = _text_digest(
            canonical_json(dict(client_metadata))
        )
    else:
        raise WireAttestationError(
            "Responses client_metadata shape drift: "
            f"keys={sorted(client_metadata) if isinstance(client_metadata, Mapping) else None}"
        )
    prompt_cache_key = body.get("prompt_cache_key")
    if prompt_cache_key is None:
        observed_prompt_digest = None
        observed_prompt_length = None
    elif isinstance(prompt_cache_key, str) and prompt_cache_key:
        observed_prompt_digest = _text_digest(prompt_cache_key)
        observed_prompt_length = len(prompt_cache_key.encode("utf-8"))
    else:
        raise WireAttestationError("Responses prompt_cache_key shape drift")
    if expectation.prompt_cache_key_required != (prompt_cache_key is not None):
        raise WireAttestationError(
            "Responses prompt_cache_key presence drift: "
            f"required={expectation.prompt_cache_key_required}"
        )
    text_envelope = body.get("text")
    expected_text_keys = (
        {"format"} if expectation.expected_text_verbosity is None
        else {"format", "verbosity"}
    )
    if (not isinstance(text_envelope, Mapping)
            or set(text_envelope) != expected_text_keys
            or text_envelope.get("verbosity") != expectation.expected_text_verbosity):
        raise WireAttestationError(
            "Responses text envelope drift: "
            f"keys={sorted(text_envelope) if isinstance(text_envelope, Mapping) else None}, "
            f"verbosity={text_envelope.get('verbosity') if isinstance(text_envelope, Mapping) else None!r}"
        )
    observed_include = body.get("include")
    if (not isinstance(observed_include, list)
            or tuple(observed_include) != expectation.expected_include):
        raise WireAttestationError(
            "Responses include固定値がdrift: "
            f"observed={body.get('include')!r}, "
            f"expected={expectation.expected_include!r}"
        )
    instructions_digest = expectation.expected_top_level_instructions_digest
    if instructions_digest is not None:
        instructions = body.get("instructions")
        if (not isinstance(instructions, str)
                or _text_digest(instructions) != instructions_digest):
            raise WireAttestationError("top-level instructions digest drift")
    names = extract_tool_names(body)
    expected = tuple(sorted(expectation.expected_wire_tools))
    if names != expected:
        raise WireAttestationError(
            f"wire tool inventory drift: observed={names!r}, expected={expected!r}"
        )
    tools_key_present = "tools" in body
    if not expected and tools_key_present:
        raise WireAttestationError("known-model captureのtop-level body.tools keyが出現")
    if expected and not tools_key_present:
        raise WireAttestationError("forced residual fixture requestにtools keyが無い")
    tools = body.get("tools", [])
    observed_tools_digest = hashlib.sha256(
        canonical_json(tools).encode("utf-8")
    ).hexdigest()
    if expected:
        if (expectation.expected_wire_tools_digest is None
                or observed_tools_digest != expectation.expected_wire_tools_digest):
            raise WireAttestationError(
                "wire tool descriptor digest drift: "
                f"observed={observed_tools_digest}, "
                f"expected={expectation.expected_wire_tools_digest}"
            )
    elif expectation.expected_wire_tools_digest is not None:
        raise WireAttestationError("tools key無し契約にtool descriptor digestが指定された")
    tool_choice = body.get("tool_choice")
    parallel_tool_calls = body.get("parallel_tool_calls")
    if tool_choice != "auto" or parallel_tool_calls is not False:
        raise WireAttestationError(
            "tool routing field drift: "
            f"tool_choice={tool_choice!r}, parallel_tool_calls={parallel_tool_calls!r}"
        )
    observed_model = body.get("model")
    if observed_model != expectation.model:
        raise WireAttestationError(
            f"wire model drift: observed={observed_model!r}, expected={expectation.model!r}"
        )
    reasoning = body.get("reasoning")
    if (expectation.reasoning_effort is None
            and expectation.reasoning_context is None):
        # unknown-model fallback fixtureは0.144.2で明示null。fixture固有の形状として
        # exact attestationし、known role modelへ一般化しない。
        if reasoning is not None:
            raise WireAttestationError(
                f"wire reasoning shape drift: observed={reasoning!r}, expected=None"
            )
        observed_effort = None
        observed_reasoning_context = None
    else:
        if (expectation.reasoning_effort is None
                or expectation.reasoning_context is None):
            raise WireAttestationError("reasoning expectationの内部整合性がない")
        if not isinstance(reasoning, Mapping):
            raise WireAttestationError("Responses request の reasoning がobjectでない")
        observed_effort = reasoning.get("effort")
        if observed_effort != expectation.reasoning_effort:
            raise WireAttestationError(
                "wire reasoning effort drift: "
                f"observed={observed_effort!r}, expected={expectation.reasoning_effort!r}"
            )
        observed_reasoning_context = reasoning.get("context")
        if (observed_reasoning_context != expectation.reasoning_context
                or set(reasoning) != {"effort", "context"}):
            raise WireAttestationError(
                f"wire reasoning shape drift: observed={dict(reasoning)!r}"
            )
    input_item_types, additional_digest, additional_names, nested_names = (
        _additional_tool_surface(body, expectation)
    )
    entries = body["input"]
    start = 1 if additional_digest is not None else 0
    permissions_digest, runtime_digests, environment_digest = _attest_message_sequence(
        entries,
        expectation,
        start=start,
        require_tool_history=require_tool_history,
    )
    role_instructions = expectation.developer_instructions
    if expectation.marker not in role_instructions:
        raise WireAttestationError("role/adapter digest marker がdeveloper instructionsに無い")
    observed_instruction_digest = _text_digest(role_instructions)
    if observed_instruction_digest != expectation.instruction_digest:
        raise WireAttestationError(
            "developer instruction digest不一致: "
            f"observed={observed_instruction_digest}, expected={expectation.instruction_digest}"
        )
    if expectation.input_digest not in expectation.user_prompt:
        raise WireAttestationError("input digest がcanonical user promptに無い")
    schema = _transport_schema(body)
    observed_schema_digest = hashlib.sha256(
        canonical_json(dict(schema)).encode("utf-8")
    ).hexdigest()
    if observed_schema_digest != expectation.transport_schema_digest:
        raise WireAttestationError(
            "transport output schema drift: "
            f"observed={observed_schema_digest}, expected={expectation.transport_schema_digest}"
        )
    return WireAttestation(
        role=expectation.role,
        model=observed_model,
        reasoning_effort=observed_effort,
        reasoning_context=observed_reasoning_context,
        tools_key_present=tools_key_present,
        tool_names=names,
        tool_choice=tool_choice,
        parallel_tool_calls=parallel_tool_calls,
        tool_schema_digest=observed_tools_digest,
        permissions_instruction_digest=permissions_digest,
        runtime_developer_digests=runtime_digests,
        developer_instruction_digest=observed_instruction_digest,
        transport_schema_digest=observed_schema_digest,
        top_level_instructions_digest=instructions_digest,
        response_include=tuple(observed_include),
        environment_digest=environment_digest,
        prompt_cache_key_digest=observed_prompt_digest,
        prompt_cache_key_length=observed_prompt_length,
        client_metadata_digest=observed_client_metadata_digest,
        client_metadata_keys=tuple(sorted(expected_client_keys)),
        text_verbosity=expectation.expected_text_verbosity,
        input_item_types=input_item_types,
        additional_tools_digest=additional_digest,
        additional_tool_names=additional_names,
        declared_nested_tool_names=nested_names,
        live_blocked=additional_digest is not None,
        request_digest=hashlib.sha256(
            canonical_json(dict(body)).encode("utf-8")
        ).hexdigest(),
        request_path=path,
    )


def _strict_request_body(raw: bytes, *, label: str) -> Mapping[str, Any]:
    if not isinstance(raw, bytes):
        raise WireAttestationError(f"{label} bodyがbytesでない")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise WireAttestationError(f"{label} bodyがstrict UTF-8でない: {exc}") from exc
    try:
        body = strict_json_loads(text, label=label, max_bytes=MAX_REQUEST_BYTES)
    except EventValidationError as exc:
        raise WireAttestationError(f"{label} strict JSON parse失敗: {exc}") from exc
    if not isinstance(body, Mapping):
        raise WireAttestationError(f"{label} bodyはJSON objectでなければならない")
    return body


class _ProbeServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, expectation: AttestationExpectation, response_body: bytes,
                 response_status: int, response_content_type: str):
        super().__init__(("127.0.0.1", 0), _ProbeHandler)
        self.expectation = expectation
        self.response_body = response_body
        self.response_status = response_status
        self.response_content_type = response_content_type
        self.capture_event = threading.Event()
        self.attestation: WireAttestation | None = None
        self.error: WireAttestationError | None = None
        self.request_count = 0


class _ProbeHandler(BaseHTTPRequestHandler):
    server: _ProbeServer

    def log_message(self, _format: str, *_args: Any) -> None:
        return  # request metadataをstderrへ漏らさない

    def _reply(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("content-type", content_type)
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        server = self.server
        server.request_count += 1
        if server.request_count != 1:
            self._reply(409, b'{"error":"only one request is permitted"}',
                        "application/json")
            return
        try:
            raw_len = self.headers.get("content-length")
            if raw_len is None:
                raise WireAttestationError("Responses request にcontent-lengthがない")
            length = int(raw_len)
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise WireAttestationError(f"Responses request size不正: {length}")
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise WireAttestationError("Responses request bodyがcontent-lengthより短い")
            body = _strict_request_body(raw, label="Responses request")
            server.attestation = attest_request(body, server.expectation, path=self.path)
            server.capture_event.set()
            self._reply(server.response_status, server.response_body,
                        server.response_content_type)
        except (ValueError, OSError, WireAttestationError) as exc:
            error = exc if isinstance(exc, WireAttestationError) else WireAttestationError(str(exc))
            server.error = error
            server.capture_event.set()
            self._reply(412, json.dumps({"error": str(error)}).encode("utf-8"),
                        "application/json")


class AttestingResponsesProbe:
    """一回限りの loopback capture server を管理する context manager。"""

    def __init__(self, expectation: AttestationExpectation, *,
                 response_body: bytes = b'{"error":{"message":"attestation complete"}}',
                 response_status: int = 503,
                 response_content_type: str = "application/json"):
        self._server = _ProbeServer(
            expectation, response_body, response_status, response_content_type
        )
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name=f"codex-role-probe-{expectation.role}",
            daemon=True,
        )

    @property
    def base_url(self) -> str:
        host, port = self._server.server_address
        return f"http://{host}:{port}/v1"

    def __enter__(self) -> "AttestingResponsesProbe":
        self._thread.start()
        return self

    def wait(self, timeout_s: float) -> WireAttestation:
        if not self._server.capture_event.wait(timeout_s):
            raise WireAttestationError("CodexからResponses requestが届かずtimeout")
        if self._server.error is not None:
            raise self._server.error
        if self._server.attestation is None:
            raise WireAttestationError("capture eventはあるがattestationがない")
        if self._server.request_count != 1:
            raise WireAttestationError(
                f"wire probe requestは正確に1件必要 (observed={self._server.request_count})"
            )
        return self._server.attestation

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5.0)


def attest_view_image_denial(body: Mapping[str, Any],
                             expected_path: str) -> ViewImageContainmentAttestation:
    """2nd Responses requestのrouter生成function_call_outputを検査する。"""

    entries = body.get("input")
    if not isinstance(entries, list):
        raise WireAttestationError("forced fixture followup inputがarrayでない")
    calls = [
        item for item in entries
        if isinstance(item, dict) and item.get("type") == "function_call"
        and item.get("name") == "view_image"
    ]
    if len(calls) != 1:
        raise WireAttestationError(
            f"view_image function_callは正確に1件必要 (observed={len(calls)})"
        )
    call = calls[0]
    call_id = call.get("call_id")
    arguments = call.get("arguments")
    if not isinstance(call_id, str) or not call_id or not isinstance(arguments, str):
        raise WireAttestationError("view_image call_id/argumentsが不正")
    try:
        args = strict_json_loads(arguments, label="view_image arguments")
    except Exception as exc:
        raise WireAttestationError(f"view_image argumentsがstrict JSONでない: {exc}") from exc
    if not isinstance(args, dict) or args.get("path") != expected_path:
        raise WireAttestationError(
            f"view_image target drift: observed={args!r}, expected={expected_path!r}"
        )
    outputs = [
        item for item in entries
        if isinstance(item, dict) and item.get("type") == "function_call_output"
        and item.get("call_id") == call_id
    ]
    if len(outputs) != 1 or not isinstance(outputs[0].get("output"), str):
        raise WireAttestationError("matching function_call_outputは正確に1件必要")
    output = outputs[0]["output"]
    if expected_path not in output or "No such file or directory" not in output:
        raise WireAttestationError(
            "view_image outputがouter namespaceのENOENTを証明していない"
        )
    return ViewImageContainmentAttestation(
        requested_path=expected_path,
        call_id=call_id,
        function_call_output=output,
        error_output_digest=hashlib.sha256(output.encode("utf-8")).hexdigest(),
        followup_request_digest=hashlib.sha256(
            canonical_json(dict(body)).encode("utf-8")
        ).hexdigest(),
    )


def _response_object(response_id: str, status: str, model: str,
                     output: list[Mapping[str, Any]]) -> dict[str, Any]:
    usage = None
    if status == "completed":
        usage = {
            "input_tokens": 1,
            "input_tokens_details": {"cached_tokens": 0},
            "output_tokens": 1,
            "output_tokens_details": {"reasoning_tokens": 0},
            "total_tokens": 2,
        }
    return {
        "id": response_id,
        "object": "response",
        "created_at": int(time.time()),
        "status": status,
        "background": False,
        "error": None,
        "incomplete_details": None,
        "instructions": None,
        "max_output_tokens": None,
        "max_tool_calls": None,
        "model": model,
        "output": output,
        "parallel_tool_calls": False,
        "previous_response_id": None,
        "prompt_cache_key": None,
        "reasoning": {"effort": None, "summary": None},
        "safety_identifier": None,
        "service_tier": "default",
        "store": False,
        "temperature": None,
        "text": {"format": {"type": "text"}, "verbosity": "medium"},
        "tool_choice": "auto",
        "tools": [],
        "top_logprobs": 0,
        "top_p": None,
        "truncation": "disabled",
        "usage": usage,
        "user": None,
        "metadata": {},
    }


def _sse_event(kind: str, data: dict[str, Any], sequence: int) -> str:
    value = dict(data)
    value["type"] = kind
    value["sequence_number"] = sequence
    return (
        f"event: {kind}\n"
        f"data: {json.dumps(value, ensure_ascii=False, separators=(',', ':'))}\n\n"
    )


def _tool_call_sse(model: str, target: str) -> bytes:
    response_id = "resp_izanagi_view_image_probe_1"
    item = {
        "id": "fc_izanagi_probe",
        "type": "function_call",
        "status": "completed",
        "arguments": json.dumps({"path": target}, separators=(",", ":")),
        "call_id": "call_izanagi_probe",
        "name": "view_image",
    }
    events = [
        _sse_event("response.created", {
            "response": _response_object(response_id, "in_progress", model, [])
        }, 0),
        _sse_event("response.output_item.added", {
            "output_index": 0, "item": dict(item, status="in_progress")
        }, 1),
        _sse_event("response.function_call_arguments.done", {
            "item_id": item["id"], "output_index": 0, "arguments": item["arguments"]
        }, 2),
        _sse_event("response.output_item.done", {"output_index": 0, "item": item}, 3),
        _sse_event("response.completed", {
            "response": _response_object(response_id, "completed", model, [item])
        }, 4),
    ]
    return "".join(events).encode("utf-8")


def _message_sse(model: str, text: str) -> bytes:
    response_id = "resp_izanagi_view_image_probe_2"
    part = {"type": "output_text", "annotations": [], "logprobs": [], "text": text}
    item = {
        "id": "msg_izanagi_probe",
        "type": "message",
        "status": "completed",
        "role": "assistant",
        "content": [part],
    }
    pending = dict(item, status="in_progress", content=[])
    events = [
        _sse_event("response.created", {
            "response": _response_object(response_id, "in_progress", model, [])
        }, 0),
        _sse_event("response.output_item.added", {
            "output_index": 0, "item": pending
        }, 1),
        _sse_event("response.content_part.added", {
            "item_id": item["id"], "output_index": 0, "content_index": 0,
            "part": {"type": "output_text", "annotations": [], "logprobs": [], "text": ""},
        }, 2),
        _sse_event("response.output_text.delta", {
            "item_id": item["id"], "output_index": 0, "content_index": 0,
            "delta": text, "logprobs": [],
        }, 3),
        _sse_event("response.output_text.done", {
            "item_id": item["id"], "output_index": 0, "content_index": 0,
            "text": text, "logprobs": [],
        }, 4),
        _sse_event("response.content_part.done", {
            "item_id": item["id"], "output_index": 0, "content_index": 0, "part": part,
        }, 5),
        _sse_event("response.output_item.done", {"output_index": 0, "item": item}, 6),
        _sse_event("response.completed", {
            "response": _response_object(response_id, "completed", model, [item])
        }, 7),
    ]
    return "".join(events).encode("utf-8")


class _ForcedProbeServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, expectation: AttestationExpectation, target: str,
                 final_text: str):
        super().__init__(("127.0.0.1", 0), _ForcedProbeHandler)
        self.expectation = expectation
        self.target = target
        self.final_text = final_text
        self.wire: WireAttestation | None = None
        self.containment: ViewImageContainmentAttestation | None = None
        self.error: WireAttestationError | None = None
        self.done = threading.Event()
        self.request_count = 0


class _ForcedProbeHandler(BaseHTTPRequestHandler):
    server: _ForcedProbeServer

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def do_POST(self) -> None:  # noqa: N802
        server = self.server
        server.request_count += 1
        try:
            length = int(self.headers.get("content-length", "0"))
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise WireAttestationError(f"forced fixture request size不正: {length}")
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise WireAttestationError("forced fixture bodyがcontent-lengthより短い")
            body = _strict_request_body(raw, label="forced fixture request")
            if server.request_count == 1:
                server.wire = attest_request(body, server.expectation, path=self.path)
                payload = _tool_call_sse(server.expectation.model, server.target)
            elif server.request_count == 2:
                # followupでもmodel/tool/developer/user/schema contractのdriftを許さない。
                attest_request(
                    body, server.expectation, path=self.path,
                    require_tool_history=True,
                )
                server.containment = attest_view_image_denial(body, server.target)
                payload = _message_sse(server.expectation.model, server.final_text)
                server.done.set()
            else:
                raise WireAttestationError("forced fixtureは2 request固定")
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.send_header("content-length", str(len(payload)))
            self.send_header("connection", "close")
            self.end_headers()
            self.wfile.write(payload)
        except (ValueError, OSError, WireAttestationError) as exc:
            server.error = exc if isinstance(exc, WireAttestationError) else WireAttestationError(str(exc))
            server.done.set()
            payload = json.dumps({"error": str(server.error)}).encode("utf-8")
            self.send_response(412)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)


class ForcedViewImageResponsesProbe:
    """fake Responsesがview_image(host path)を強制する二往復fixture。"""

    def __init__(self, expectation: AttestationExpectation, *, target: str,
                 final_text: str):
        self._server = _ForcedProbeServer(expectation, target, final_text)
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="codex-forced-view-image-probe",
            daemon=True,
        )

    @property
    def base_url(self) -> str:
        host, port = self._server.server_address
        return f"http://{host}:{port}/v1"

    def __enter__(self) -> "ForcedViewImageResponsesProbe":
        self._thread.start()
        return self

    def wait(self, timeout_s: float) -> tuple[WireAttestation, ViewImageContainmentAttestation]:
        if not self._server.done.wait(timeout_s):
            raise WireAttestationError("forced view_image fixture timeout")
        if self._server.error is not None:
            raise self._server.error
        if self._server.wire is None or self._server.containment is None:
            raise WireAttestationError("forced fixture evidenceが欠落")
        if self._server.request_count != 2:
            raise WireAttestationError(
                f"forced fixture requestは正確に2件必要 (observed={self._server.request_count})"
            )
        return self._server.wire, self._server.containment

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5.0)
