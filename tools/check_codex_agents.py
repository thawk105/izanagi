#!/usr/bin/env python3
"""Codex native 0件と、全16 dormant projection adapter の静的契約を検査する。

native custom profile は現行 collaboration surface の selector/権限隔離を保証できない
ため引き続き禁止する。一方 `.codex/role-adapters/*.json` は自動発見されない source
adapter であり、Claude 16 role と全単射、capability lowering、I/O schema、semantic policy、
consumer、renderer の期待 byte と照合する。runtime activation は全件blocked固定である。

``input.additional_tools`` inventoryと隔離の実効性はruntime launcher側の証拠が正本であり、
このstatic checkerはtool-free/activeを主張せず、自然言語の成功申告を証拠に数えない。
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:  # Python 3.10
    try:
        import tomli as tomllib  # type: ignore[import-not-found,no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from orchestrator.codex_roles import spec as ROLE_SPEC  # noqa: E402

ProfileError = ROLE_SPEC.RoleSpecError
ClaudeAgent = ROLE_SPEC.ClaudeAgent
parse_claude_agent = ROLE_SPEC.parse_claude_agent
load_inventory = ROLE_SPEC.load_claude_inventory

# native profile とstatic adapterを混同しない。runtime gate未解決のためactivate禁止。
ACTIVE: dict[str, object] = {}
NATIVE_ACTIVE = ACTIVE
STATIC_ADAPTERS = frozenset(ROLE_SPEC.load_role_specs(REPO))

_AGENT_GLOBAL_KEYS = {
    "max_threads",
    "max_depth",
    "job_max_runtime_seconds",
    "interrupt_message",
}
_SOURCE_EXAMPLE_PARITY_ROLES = frozenset({
    "axis-proposer",
    "planner-v4",
    "coder-v4-autonomous",
    "coder-v4-autonomous-k2",
    "coder-v4-autonomous-sort",
    "coder-v4-autonomous-policy",
    "coder-v4-autonomous-policy-ir",
    "coder-v4-autonomous-trigger-gating",
    "selector-8b",
})


def load_project_agent_roles(root: Path) -> set[str]:
    """project config 経由でnative discoveryされるagent role名を返す。"""
    config = root / ".codex" / "config.toml"
    if not config.exists():
        return set()
    if tomllib is None:
        raise ProfileError(
            f"{config}: TOML parser がない。Python 3.11+ または tomli が必要"
        )
    try:
        parsed = tomllib.loads(config.read_text(encoding="utf-8"))
    except Exception as exc:  # tomllib/tomli で例外 class が異なる
        raise ProfileError(f"{config}: TOML parse 失敗: {exc}") from exc
    agents = parsed.get("agents")
    if agents is None:
        return set()
    if not isinstance(agents, dict):
        raise ProfileError(f"{config}: agents は table でなければならない")
    return set(agents) - _AGENT_GLOBAL_KEYS


def _function_required_fields(path: Path, function_name: str) -> set[str]:
    """parser の `arg["field"]` を必須fieldとしてASTから取り出す。"""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        raise ProfileError(f"{path}: consumer parse 失敗: {exc}") from exc
    function = next(
        (node for node in tree.body
         if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
         and node.name == function_name),
        None,
    )
    if function is None or not function.args.args:
        raise ProfileError(f"{path}: consumer function {function_name!r} がない")
    argument = function.args.args[0].arg
    required: set[str] = set()
    for node in ast.walk(function):
        if not isinstance(node, ast.Subscript):
            continue
        if not isinstance(node.value, ast.Name) or node.value.id != argument:
            continue
        key: Any = node.slice
        # Python 3.8 compatibility (3.9+ は ast.Constant が直接入る)。
        if isinstance(key, ast.Index):  # pragma: no cover - Python 3.8 only
            key = key.value
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            required.add(key.value)
    if not required:
        raise ProfileError(
            f"{path}: {function_name} の必須fieldを検出できない。consumer検査を黙って空にしない"
        )
    return required


def _validate_consumer(root: Path, role: ROLE_SPEC.RoleSpec) -> None:
    if role.consumer is None:
        return
    consumer = role.consumer
    path = root / consumer["path"]
    if path.is_symlink():
        raise ProfileError(f"{path}: consumer symlink は禁止")
    observed = _function_required_fields(path, consumer["parser"])
    declared = set(consumer["required_fields"])
    if observed != declared:
        raise ProfileError(
            f"{path}:{consumer['parser']}: consumer required field drift "
            f"observed={sorted(observed)}, manifest={sorted(declared)}"
        )
    schema_required = set(role.output_schema["required"])
    if not observed <= schema_required:
        raise ProfileError(
            f"{role.name}: consumer必須fieldがoutput schema requiredに無い: "
            f"{sorted(observed-schema_required)}"
        )


def _source_json_example(role: ROLE_SPEC.RoleSpec, heading: str) -> Any:
    marker = f"\n## {heading}\n"
    if marker not in role.source.body:
        raise ProfileError(f"{role.source.path}: `## {heading}`節がない")
    section = role.source.body.split(marker, 1)[1]
    match = re.search(r"```json\s*\n(.*?)\n```", section, flags=re.DOTALL)
    if match is None:
        raise ProfileError(f"{role.source.path}: {heading}JSON例がない")
    # coder-v4-autonomousの`<1-1000>`等、意図的なunquoted placeholderは
    # key shapeだけを照合するためnullへ正規化する。
    example_text = re.sub(
        r"(:\s*)<[^>\n]+>(\s*[,}])", r"\1null\2", match.group(1)
    )
    try:
        return json.loads(example_text)
    except json.JSONDecodeError as exc:
        raise ProfileError(
            f"{role.source.path}: {heading}JSON例を解釈できない: {exc}"
        ) from exc


def _validate_example_shape(value: Any, schema: dict[str, Any], label: str) -> None:
    """JSON例が宣言schemaのrequired/closed key treeを満たすことを再帰照合する。"""

    raw_types = schema.get("type")
    types = {raw_types} if isinstance(raw_types, str) else set(raw_types or ())
    if isinstance(value, dict):
        if "object" not in types:
            raise ProfileError(f"{label}: source例はobjectだがschema typeが異なる")
        properties = schema.get("properties")
        if not isinstance(properties, dict):
            # 意図的にopenなobject subtreeはtrusted producer責任であり、例の内部を
            # schema parityの根拠にしない。
            return
        required = set(schema.get("required", ()))
        missing = required - set(value)
        if missing:
            raise ProfileError(f"{label}: source例のrequired key欠落={sorted(missing)}")
        extra = set(value) - set(properties)
        if schema.get("additionalProperties") is False and extra:
            raise ProfileError(f"{label}: source例の未宣言key={sorted(extra)}")
        for key in sorted(set(value) & set(properties)):
            child = properties[key]
            if not isinstance(child, dict):
                raise ProfileError(f"{label}.{key}: schema nodeはobjectでなければならない")
            _validate_example_shape(value[key], child, f"{label}.{key}")
        return
    if isinstance(value, list):
        if "array" not in types:
            raise ProfileError(f"{label}: source例はarrayだがschema typeが異なる")
        items = schema.get("items")
        if isinstance(items, dict):
            for index, child in enumerate(value):
                _validate_example_shape(child, items, f"{label}[{index}]")


def _validate_source_shape(role: ROLE_SPEC.RoleSpec, heading: str,
                           schema: dict[str, Any]) -> None:
    if role.name not in _SOURCE_EXAMPLE_PARITY_ROLES:
        return
    example = _source_json_example(role, heading)
    try:
        _validate_example_shape(example, schema, f"{role.name}.{heading}")
    except ProfileError as exc:
        raise ProfileError(
            f"{role.source.path}: source {heading} shape parity drift: {exc}"
        ) from exc


def _validate_source_input_shape(role: ROLE_SPEC.RoleSpec) -> None:
    _validate_source_shape(role, "入力", role.input_schema)


def _validate_source_output_shape(role: ROLE_SPEC.RoleSpec) -> None:
    _validate_source_shape(role, "出力", role.output_schema)


def _validate_adapter_inventory(root: Path,
                                specs: dict[str, ROLE_SPEC.RoleSpec]) -> None:
    adapter_dir = root / ROLE_SPEC.ADAPTER_DIR_REL
    if not adapter_dir.is_dir():
        raise ProfileError(f"{adapter_dir}: non-native adapter directory がない")
    if adapter_dir.is_symlink():
        raise ProfileError(f"{adapter_dir}: adapter directory symlink は禁止")
    expected = ROLE_SPEC.expected_adapters(root)
    expected_paths = set(expected)
    actual_paths = {path for path in adapter_dir.iterdir() if path.is_file() or path.is_symlink()}
    if actual_paths != expected_paths:
        missing = sorted(str(path.relative_to(root)) for path in expected_paths - actual_paths)
        extra = sorted(str(path.relative_to(root)) for path in actual_paths - expected_paths)
        raise ProfileError(
            f"{adapter_dir}: adapter inventory 不一致 missing={missing}, extra={extra}"
        )
    if set(specs) != {path.stem for path in expected_paths}:
        raise ProfileError("Claude role と Codex adapter が全単射でない")
    for path, rendered in expected.items():
        if path.is_symlink():
            raise ProfileError(f"{path}: adapter symlink は禁止")
        # duplicate key/BOM/NFC等もbyte比較とは独立に検査する。
        parsed = ROLE_SPEC.load_json_strict(path)
        if not isinstance(parsed, dict):
            raise ProfileError(f"{path}: adapter top-level は object")
        actual = path.read_text(encoding="utf-8")
        if actual != rendered:
            raise ProfileError(
                f"{path}: rendered adapter byte parity drift。manifest/Claude sourceから再生成する"
            )
        if parsed.get("mode") != "static-dormant":
            raise ProfileError(f"{path}: adapter modeはstatic-dormant固定")
        if parsed.get("runtime_activation") != ROLE_SPEC.RUNTIME_ACTIVATION:
            raise ProfileError(
                f"{path}: uncontrollable additional_tools解決までruntime activationはblocked"
            )
        forbidden_runtime_claims = {"wire_contract", "wire_tools_attested_by", "capabilities"}
        if forbidden_runtime_claims & set(parsed):
            raise ProfileError(
                f"{path}: static adapterにtool-free/runtime claimを含めてはならない"
            )
        instructions = parsed.get("developer_instructions")
        if not isinstance(instructions, str):
            raise ProfileError(f"{path}: developer_instructionsはstring")
        if instructions.count(specs[path.stem].source.body) != 1:
            raise ProfileError(
                f"{path}: Claude source.bodyがdeveloper_instructionsへexact 1回入っていない"
            )
        body_end = instructions.find("<<<CLAUDE_ROLE_BODY_END>>>")
        override = instructions.find("<<<CODEX_PRODUCT_OVERRIDE_BEGIN>>>")
        if body_end < 0 or override <= body_end:
            raise ProfileError(f"{path}: product overrideはClaude本文後でなければならない")
        required_override = (
            "tool使用、repository探索、実行loop、write/edit命令はtrusted projection/driverへlower済み",
            "adapter logical schemaを優先",
            "schemaが許すunknown/unknowns/uncertainty/confidenceへ",
        )
        if not all(text in instructions[override:] for text in required_override):
            raise ProfileError(f"{path}: product override契約が欠落")
        spec = specs[path.stem]
        expected_input_policy = {
            "version": ROLE_SPEC.POLICY_VERSION,
            "recursive_forbidden_key_tokens": list(spec.forbidden_key_tokens),
            "opaque_string_content": ROLE_SPEC.OPAQUE_STRING_POLICY,
            "open_object_subtrees": ROLE_SPEC.OPEN_SUBTREE_POLICY,
        }
        if parsed.get("input_policy") != expected_input_policy:
            raise ProfileError(f"{path}: recursive input policy metadataが不一致")
        expected_consumer = (
            {"use": "trusted-integration", "status": "trusted-parser-wired"}
            if spec.consumer is not None
            else {
                "use": "standalone-typed-proposal-only",
                "status": "trusted-integration-unwired",
            }
        )
        if parsed.get("consumer_contract") != expected_consumer:
            raise ProfileError(f"{path}: consumer integration statusが不一致")


def validate_inventory(root: Path) -> dict[str, ROLE_SPEC.RoleSpec]:
    root = root.resolve()
    specs = ROLE_SPEC.load_role_specs(root)
    if set(specs) != set(STATIC_ADAPTERS):
        raise ProfileError(
            f"static adapter inventory drift expected={sorted(STATIC_ADAPTERS)}, "
            f"actual={sorted(specs)}"
        )
    if ACTIVE:
        raise ProfileError("native active profile は0件固定")
    ledger_direct = {
        name for name, contract in ROLE_SPEC.ROLE_IO_CONTRACTS.items()
        if contract["mode"] == "direct-json-example"
    }
    if ledger_direct != set(_SOURCE_EXAMPLE_PARITY_ROLES):
        raise ProfileError(
            "direct JSON source parity coverage drift "
            f"ledger={sorted(ledger_direct)}, checker={sorted(_SOURCE_EXAMPLE_PARITY_ROLES)}"
        )
    _validate_adapter_inventory(root, specs)
    for role in specs.values():
        _validate_consumer(root, role)
        _validate_source_input_shape(role)
        _validate_source_output_shape(role)
    return specs


def check(root: Path = REPO) -> list[str]:
    root = root.resolve()
    try:
        validate_inventory(root)
        configured_roles = load_project_agent_roles(root)
    except (OSError, ProfileError) as exc:
        return [str(exc)]

    findings: list[str] = []
    native_dir = root / ".codex" / "agents"
    for path in sorted(native_dir.glob("*.toml")):
        findings.append(
            f"{path}: native discovery profileは禁止。role-adaptersはstatic/dormantでactivate不可"
        )
    config = root / ".codex" / "config.toml"
    for role in sorted(configured_roles):
        findings.append(
            f"{config}: native discovery agent role {role!r}は禁止。"
            "role-adaptersはstatic/dormantでactivate不可"
        )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--root", type=Path, default=REPO, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.write:
        print(
            "ERROR: --write はnative profile生成と誤認されるため使用しない。"
            "role-adaptersはmanifest rendererの期待byteをreviewしてapplyする",
            file=sys.stderr,
        )
        return 1
    findings = check(args.root)
    if findings:
        for finding in findings:
            print(f"ERROR: {finding}", file=sys.stderr)
        return 1
    print(
        "OK: Codex agent roles "
        f"({len(ACTIVE)} native active / {len(STATIC_ADAPTERS)} static dormant; "
        "runtime activation blocked: uncontrollable_additional_tools)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
