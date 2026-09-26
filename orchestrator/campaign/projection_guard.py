# -*- coding: utf-8 -*-
"""Ability-probe 資材が campaign proposal へ射影されるのを検知する。

これは字面 tripwire（回帰検知）であり、encoding・言い換え・semantic copy
への保証ではない。origin 保証は未実装（裁定パッケージ）。
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from .reflux_ir import parse_wire


_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_LEDGER = _ROOT / "patches" / "ledger.json"
_LEDGER_TOP_KEYS = frozenset({"schema_version", "scope", "entries"})
_POLICY_KEYS = frozenset(
    {"planner_coder_eligible", "excluded_paths", "excluded_tokens"}
)
_PATH_CONTINUATION = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_./-"
)
_PROPOSAL_TOP_REQUIRED = frozenset({"planner", "coder"})
_PROPOSAL_TOP_OPTIONAL = frozenset({"auditor", "prior_critic_reverse"})
_PLANNER_REQUIRED = frozenset({"axis", "direction", "magnitude"})
_PLANNER_OPTIONAL = frozenset({"justification", "uncertainty"})
_CODER_REQUIRED = frozenset({"axis", "implementation"})
_CODER_OPTIONAL = frozenset({"value", "justification", "confidence"})
CODER_CONTRACT_IMPLEMENTATION = "implementation"
CODER_CONTRACT_TRIGGER_WIRE = "trigger-wire"
CODER_CONTRACT_K2 = "k2-role-output"
CODER_CONTRACT_POLICY_CPP = "policy-cpp"
CODER_CONTRACT_POLICY_IR = "policy-ir"
_CODER_CONTRACTS = frozenset({
    CODER_CONTRACT_IMPLEMENTATION,
    CODER_CONTRACT_TRIGGER_WIRE,
    CODER_CONTRACT_K2,
    CODER_CONTRACT_POLICY_CPP,
    CODER_CONTRACT_POLICY_IR,
})
_POLICY_CODER_OPTIONAL = frozenset({"justification", "confidence"})
_TRIGGER_CODER_REQUIRED = frozenset({"axis", "wire"})
_TRIGGER_CODER_OPTIONAL = frozenset({"justification", "confidence"})
_K2_CODER_REQUIRED = frozenset({
    "proposal", "knowledge_use", "classification", "data_boundary_report",
})
_K2_PROPOSAL_REQUIRED = frozenset({
    "axis", "value", "implementation", "justification", "confidence",
})
_AUDITOR_REQUIRED = frozenset({"verdict", "diff_digest"})
_AUDITOR_OPTIONAL = frozenset(
    {"violations", "nits", "proposed_tests", "uncertainty"}
)


class ProjectionPolicyError(ValueError):
    """ledger / projection_policy が fail-closed 条件を満たさない。"""


class AbilityProbeMaterialError(ValueError):
    """proposal 内で検出した禁止字面を構造化して返す。"""

    def __init__(
        self,
        *,
        field_path: str,
        material_kind: str,
        prohibited: str,
    ) -> None:
        self.field_path = field_path
        self.material_kind = material_kind
        self.prohibited = prohibited
        super().__init__(
            "ability-probe projection tripwire: "
            f"field={field_path} kind={material_kind} prohibited={prohibited!r}"
        )


@dataclass(frozen=True)
class ProjectionPolicy:
    """全 ability-probe entry から集約した拒否字面。"""

    excluded_paths: tuple[str, ...]
    excluded_tokens: tuple[str, ...]


def _object_without_duplicate_keys(
    pairs: Sequence[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProjectionPolicyError(f"ledger に重複 JSON key: {key!r}")
        result[key] = value
    return result


def _require_string_list(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ProjectionPolicyError(f"{field} は 1 件以上の string list が必要")
    if any(not isinstance(item, str) or not item for item in value):
        raise ProjectionPolicyError(f"{field} は空でない string のみ許可")
    return tuple(value)


def _normalize_policy_path(value: str) -> str:
    normalized = re.sub(r"/+", "/", value.replace("\\", "/"))
    while normalized.startswith("./"):
        normalized = normalized[2:]
    components: list[str] = []
    for component in normalized.split("/"):
        if component in ("", "."):
            continue
        if component == "..":
            if not components:
                raise ProjectionPolicyError(
                    f"excluded_paths は repository-relative path のみ: {value!r}"
                )
            components.pop()
        else:
            components.append(component)
    if value.startswith(("/", "\\")) or not components:
        raise ProjectionPolicyError(
            f"excluded_paths は repository-relative path のみ: {value!r}"
        )
    return "/".join(components)


def _schema_checked_policy(entry: Mapping[str, Any], index: int) -> ProjectionPolicy:
    policy = entry.get("projection_policy")
    if not isinstance(policy, Mapping):
        raise ProjectionPolicyError(
            f"ledger.entries[{index}].projection_policy が無いか object でない"
        )
    unknown = set(policy) - _POLICY_KEYS
    missing = _POLICY_KEYS - set(policy)
    if unknown or missing:
        raise ProjectionPolicyError(
            f"ledger.entries[{index}].projection_policy key 不一致: "
            f"missing={sorted(missing)} unknown={sorted(unknown)}"
        )
    if policy["planner_coder_eligible"] is not False:
        raise ProjectionPolicyError(
            f"ledger.entries[{index}].projection_policy."
            "planner_coder_eligible は false 必須"
        )

    raw_paths = _require_string_list(
        policy["excluded_paths"],
        f"ledger.entries[{index}].projection_policy.excluded_paths",
    )
    paths = tuple(_normalize_policy_path(item) for item in raw_paths)
    tokens = _require_string_list(
        policy["excluded_tokens"],
        f"ledger.entries[{index}].projection_policy.excluded_tokens",
    )
    if len({item.casefold() for item in paths}) != len(paths):
        raise ProjectionPolicyError(
            f"ledger.entries[{index}] の excluded_paths が正規化後に重複"
        )
    if len({item.casefold() for item in tokens}) != len(tokens):
        raise ProjectionPolicyError(
            f"ledger.entries[{index}] の excluded_tokens が大文字小文字無視で重複"
        )
    return ProjectionPolicy(paths, tokens)


def load_projection_policy(
    ledger_path: os.PathLike[str] | str | None = None,
) -> ProjectionPolicy:
    """ledger を一読し、schema 検査済み ability-probe 射影 policy を返す。

    ledger 不在、read/parse 失敗、policy 欠落はすべて
    :class:`ProjectionPolicyError` として fail-closed にする。
    """
    path = Path(ledger_path) if ledger_path is not None else _DEFAULT_LEDGER
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ProjectionPolicyError(f"patch ledger を読めない: {path}: {exc}") from exc
    try:
        document = json.loads(raw, object_pairs_hook=_object_without_duplicate_keys)
    except ProjectionPolicyError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ProjectionPolicyError(f"patch ledger を parse できない: {path}: {exc}") from exc

    if not isinstance(document, Mapping):
        raise ProjectionPolicyError("patch ledger top-level は object 必須")
    if set(document) != _LEDGER_TOP_KEYS:
        raise ProjectionPolicyError(
            "patch ledger top-level key 不一致: "
            f"missing={sorted(_LEDGER_TOP_KEYS - set(document))} "
            f"unknown={sorted(set(document) - _LEDGER_TOP_KEYS)}"
        )
    if document["schema_version"] != "izanagi-patch-ledger/v1":
        raise ProjectionPolicyError(
            f"patch ledger schema_version 不一致: {document['schema_version']!r}"
        )
    if document["scope"] != "registered-entries-only":
        raise ProjectionPolicyError(f"patch ledger scope 不一致: {document['scope']!r}")
    entries = document["entries"]
    if not isinstance(entries, list) or not entries:
        raise ProjectionPolicyError("patch ledger entries は非空 list 必須")

    policies: list[ProjectionPolicy] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            raise ProjectionPolicyError(f"ledger.entries[{index}] は object 必須")
        ability_probe = entry.get("ability_probe")
        if not isinstance(ability_probe, bool):
            raise ProjectionPolicyError(
                f"ledger.entries[{index}].ability_probe は bool 必須"
            )
        if ability_probe:
            policies.append(_schema_checked_policy(entry, index))
    if not policies:
        raise ProjectionPolicyError(
            "patch ledger に projection_policy 付き ability_probe entry が無い"
        )

    # 複数 probe は ledger 自身等の共通 path を当然共有しうる。entry 内重複は
    # schema error だが、entry 間は初出順で集約し、将来 rung 追加を過剰拒否しない。
    paths = tuple(dict.fromkeys(
        path for policy in policies for path in policy.excluded_paths
    ))
    tokens = tuple(dict.fromkeys(
        token for policy in policies for token in policy.excluded_tokens
    ))
    return ProjectionPolicy(paths, tokens)


def _iter_nested_strings(obj: Any, field_path: str = "$"):
    if isinstance(obj, str):
        yield field_path, obj
    elif isinstance(obj, Mapping):
        for key, value in obj.items():
            if isinstance(key, str):
                yield f"{field_path}.<key>", key
            yield from _iter_nested_strings(value, f"{field_path}[{key!r}]")
    elif isinstance(obj, (list, tuple)):
        for index, value in enumerate(obj):
            yield from _iter_nested_strings(value, f"{field_path}[{index}]")


def _normalized_path_text(value: str) -> str:
    value = re.sub(r"/+", "/", value.replace("\\", "/"))

    def collapse(match: re.Match[str]) -> str:
        token = match.group(0)
        absolute = token.startswith("/")
        components: list[str] = []
        for component in token.split("/"):
            if component in ("", "."):
                continue
            if component == "..":
                if components and components[-1] != "..":
                    components.pop()
                elif not absolute:
                    components.append(component)
            else:
                components.append(component)
        prefix = "/" if absolute else ""
        return prefix + "/".join(components)

    return re.sub(r"[A-Za-z0-9_./-]+", collapse, value)


def _assert_key_set(
    value: Any,
    *,
    field: str,
    required: frozenset[str],
    optional: frozenset[str] = frozenset(),
) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} は object 必須")
    keys = set(value)
    missing = required - keys
    unknown = keys - required - optional
    if missing:
        raise KeyError(
            f"{field} required key 欠落: {sorted(missing)}"
        )
    if unknown:
        raise ValueError(
            f"{field} key 不一致: missing=[] unknown={sorted(unknown)}"
        )


def assert_closed_proposal_schema(
    document: Any,
    *,
    require_auditor: bool,
    require_coder_value: bool,
    coder_contract: str = CODER_CONTRACT_IMPLEMENTATION,
) -> None:
    """3 proposal loader 共通の required/optional closed key set gate。"""
    if type(coder_contract) is not str or coder_contract not in _CODER_CONTRACTS:
        raise ValueError("未知の coder contract mode")
    if coder_contract in {CODER_CONTRACT_POLICY_CPP, CODER_CONTRACT_POLICY_IR}:
        if require_coder_value or not require_auditor:
            raise ValueError('policy proposal requires auditor and no value')
        _assert_key_set(document, field='$', required=frozenset({'coder', 'auditor'}))
        _assert_key_set(
            document['coder'], field='$.coder',
            required=frozenset({'axis', 'implementation' if coder_contract == CODER_CONTRACT_POLICY_CPP else 'ir'}),
            optional=_POLICY_CODER_OPTIONAL,
        )
        _assert_key_set(document['auditor'], field='$.auditor',
                        required=_AUDITOR_REQUIRED, optional=_AUDITOR_OPTIONAL)
        return
    if (
        coder_contract == CODER_CONTRACT_TRIGGER_WIRE
        and require_coder_value
    ):
        raise ValueError("trigger-wire coder contract は value を持たない")
    top_required = set(_PROPOSAL_TOP_REQUIRED)
    if require_auditor:
        top_required.add("auditor")
    top_optional = set(_PROPOSAL_TOP_OPTIONAL)
    if require_auditor:
        top_optional.remove("auditor")
    _assert_key_set(
        document,
        field="$",
        required=frozenset(top_required),
        optional=frozenset(top_optional),
    )
    _assert_key_set(
        document["planner"],
        field="$.planner",
        required=_PLANNER_REQUIRED,
        optional=_PLANNER_OPTIONAL,
    )
    if coder_contract == CODER_CONTRACT_K2:
        _assert_key_set(
            document["coder"],
            field="$.coder",
            required=_K2_CODER_REQUIRED,
        )
        _assert_key_set(
            document["coder"]["proposal"],
            field="$.coder.proposal",
            required=_K2_PROPOSAL_REQUIRED,
        )
        return
    if coder_contract == CODER_CONTRACT_TRIGGER_WIRE:
        coder_required = set(_TRIGGER_CODER_REQUIRED)
        coder_optional = set(_TRIGGER_CODER_OPTIONAL)
    else:
        coder_required = set(_CODER_REQUIRED)
        coder_optional = set(_CODER_OPTIONAL)
        if require_coder_value:
            coder_required.add("value")
            coder_optional.remove("value")
    _assert_key_set(
        document["coder"],
        field="$.coder",
        required=frozenset(coder_required),
        optional=frozenset(coder_optional),
    )
    if coder_contract == CODER_CONTRACT_TRIGGER_WIRE:
        # Key closure precedes value validation so legacy/extra fields cannot
        # influence the canonical IR parser's rejection surface.
        parse_wire(document["coder"]["wire"])
    if require_auditor:
        _assert_key_set(
            document["auditor"],
            field="$.auditor",
            required=_AUDITOR_REQUIRED,
            optional=_AUDITOR_OPTIONAL,
        )


def _contains_path(value: str, prohibited: str) -> bool:
    haystack = _normalized_path_text(value).casefold()
    needle = prohibited.casefold()
    start = 0
    while True:
        index = haystack.find(needle, start)
        if index < 0:
            return False
        before = haystack[index - 1] if index else ""
        after_at = index + len(needle)
        after = haystack[after_at] if after_at < len(haystack) else ""
        # `/repo/patches/...` は検出するが `notpatches/...` や `.patch.bak`
        # は別 path として扱い、過剰拒否しない。
        if (
            (not before or before not in _PATH_CONTINUATION or before == "/")
            and (not after or after not in _PATH_CONTINUATION)
        ):
            return True
        start = index + 1


def assert_no_ability_probe_material(
    obj: Any,
    *,
    ledger_path: os.PathLike[str] | str | None = None,
) -> None:
    """全 nested string を ledger policy と照合し、最初の hit を構造化して拒否する。

    これは字面 tripwire（回帰検知）であり、encoding・言い換え・semantic copy
    への保証ではない。origin 保証は未実装（裁定パッケージ）。
    """
    policy = load_projection_policy(ledger_path)
    for field_path, value in _iter_nested_strings(obj):
        folded = value.casefold()
        for token in policy.excluded_tokens:
            if token.casefold() in folded:
                raise AbilityProbeMaterialError(
                    field_path=field_path,
                    material_kind="excluded_token",
                    prohibited=token,
                )
        for path in policy.excluded_paths:
            if _contains_path(value, path):
                raise AbilityProbeMaterialError(
                    field_path=field_path,
                    material_kind="excluded_path",
                    prohibited=path,
                )
