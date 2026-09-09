"""Axis 3 registered-search catalog, gates, and resumable runner.

This module is deliberately specific to the frozen Axis 3 search.  It does
not provide a general literature-search package.  The CLI may construct the
small live transport in this module, but only after the registration seal has
been checked; tests inject a local transport.
"""
from __future__ import annotations

import base64
import binascii
import copy
import csv
import fcntl
import hashlib
import http.client
import importlib
import importlib.metadata
import json
import os
import re
import subprocess
import struct
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence
from urllib.parse import parse_qsl, quote, quote_plus, unquote_plus, urlsplit

import jsonschema
from jsonschema import Draft7Validator


# The first registration-closure pass freezes the module-name set after catalog,
# schema, and OQL validation have exercised their imports.  Later checks digest
# the files behind that exact set, excluding unrelated lazy imports by callers.
_RUNTIME_IMPORT_MODULE_NAMES: tuple[str, ...] | None = None


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = REPO_ROOT / "orchestrator" / "schemas"
SCHEMA_PATHS = (
    SCHEMA_DIR / "axis3_search_catalog.schema.json",
    SCHEMA_DIR / "axis3_search_checkpoint.schema.json",
    SCHEMA_DIR / "axis3_search_page_evidence.schema.json",
    SCHEMA_DIR / "axis3_search_registration_seal.schema.json",
)
SOURCE_PATHS = (
    REPO_ROOT / "orchestrator" / "related_work_search.py",
    REPO_ROOT / "tools" / "run_axis3_search.py",
)
FROZEN_INPUT_PATHS = (
    REPO_ROOT
    / "docs"
    / "related-work"
    / "claim-survey"
    / "2026-08-27-axis3-search-preregistration.md",
    REPO_ROOT
    / "docs"
    / "related-work"
    / "claim-survey"
    / "2026-09-01-axis3-search-amendment.md",
)
PACKAGE_INIT_PATH = REPO_ROOT / "orchestrator" / "__init__.py"

CATALOG_VERSION = "axis3-search-catalog/v1"
CHECKPOINT_VERSION = "axis3-search-checkpoint/v1"
PAGE_EVIDENCE_VERSION = "axis3-search-page-evidence/v1"
REGISTRATION_SEAL_VERSION = "axis3-search-registration-seal/v1"
PREFLIGHT_REPORT_VERSION = "axis3-search-preflight-report/v2"
BUNDLE_VERSION = "axis3-search-bundle/v1"

PREFLIGHT_REPORT_SCHEMA: Mapping[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema_version",
        "registration_seal_sha256",
        "catalog_sha256",
        "rows",
        "preflight_evidence",
        "pacing_observations",
        "preflight_evidence_sha256",
        "wire_attempt_count",
        "first_external_request_at",
        "deadline_at",
        "availability_evidence",
        "checkpoint",
        "stopped_after_openalex_429",
        "status_counts",
        "all_rows_accounted",
        "axis_complete",
        "report_sha256",
        "effective_argv",
        "effective_argv_sha256",
        "phase_argv_contract_sha256",
    ],
    "properties": {
        "schema_version": {"const": PREFLIGHT_REPORT_VERSION},
        "registration_seal_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "catalog_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "rows": {"type": "array", "minItems": 2122, "maxItems": 2122},
        "preflight_evidence": {"type": "array", "minItems": 1},
        "pacing_observations": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "attempt_number",
                    "stream_id",
                    "index",
                    "host",
                    "request_intent_at",
                    "minimum_interval_seconds",
                    "observed_interval_seconds",
                ],
                "properties": {
                    "attempt_number": {"type": "integer", "minimum": 1},
                    "stream_id": {"type": "string", "minLength": 1},
                    "index": {"enum": ["arxiv", "openalex", "dblp"]},
                    "host": {
                        "enum": [
                            "export.arxiv.org",
                            "api.openalex.org",
                            "dblp.org",
                        ]
                    },
                    "request_intent_at": {
                        "type": "string",
                        "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$",
                    },
                    "minimum_interval_seconds": {
                        "type": "number",
                        "enum": [1.0, 3.0, 45.0],
                    },
                    "observed_interval_seconds": {"type": ["number", "null"]},
                },
            },
        },
        "preflight_evidence_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "wire_attempt_count": {
            "type": "integer",
            "minimum": 0,
            "maximum": 200_000,
        },
        "first_external_request_at": {
            "type": "string",
            "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$",
        },
        "deadline_at": {
            "type": "string",
            "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$",
        },
        "availability_evidence": {"type": "object"},
        "checkpoint": {"type": ["object", "null"]},
        "stopped_after_openalex_429": {"type": "boolean"},
        "status_counts": {
            "type": "object",
            "additionalProperties": False,
            "required": ["ready", "unavailable", "blocked"],
            "properties": {
                "ready": {"type": "integer", "minimum": 0},
                "unavailable": {"type": "integer", "minimum": 0},
                "blocked": {"type": "integer", "minimum": 0},
            },
        },
        "all_rows_accounted": {"const": True},
        "axis_complete": {"const": False},
        "report_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "effective_argv": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string", "minLength": 1},
        },
        "effective_argv_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "phase_argv_contract_sha256": {
            "type": "string",
            "pattern": "^[0-9a-f]{64}$",
        },
    },
}

NEW_NAMESPACE = "AX3A1-"
LEGACY_NAMESPACE = "AX3-"
ARXIV_YEARS = tuple(range(1991, 2027))
MAX_WIRE_ATTEMPTS = 200_000
RUN_DEADLINE = timedelta(days=30)
RETRYABLE_HTTP_STATUSES = frozenset({429, 503})
TERMINAL_HTTP_STATUS_MIN = 100
TERMINAL_HTTP_STATUS_MAX = 599
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
ATOM_NS = "http://www.w3.org/2005/Atom"
OPENSEARCH_NS = "http://a9.com/-/spec/opensearch/1.1/"
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{7,64}$")
FULL_COMMIT_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
OPENALEX_WORK_ID_RE = re.compile(r"^W[1-9][0-9]*$")
ARXIV_NEW_ID_RE = re.compile(r"^[0-9]{4}\.[0-9]{4,5}$")
ARXIV_OLD_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9.\-]+/[0-9]{7}$")
DBLP_WORK_ID_RE = re.compile(r"^[A-Za-z0-9_.:\-]+(?:/[A-Za-z0-9_.:\-]+)+$")

CHECKPOINT_STATE_ACTIONS: Mapping[str, frozenset[str]] = {
    "committed": frozenset({"continue_cursor", "not_applicable"}),
    "http_failure": frozenset({"restart_branch"}),
    "quota_wait": frozenset({"restart_branch"}),
    "pass_complete": frozenset({"start_independent_pass"}),
    "blocked_on_ruling": frozenset({"blocked_on_ruling"}),
}

# These literal digests are an independent acceptance oracle for the frozen
# 74 terms, ten branches, 1,543 legacy IDs, and 7/6 OQL fixture.  They must be
# changed only by a new dated amendment, never by a builder refactor.
FROZEN_SEMANTICS_SHA256 = "b1e3a611c2a61409df07e399e09fc96c5d251d58d830754cc9e8a0494a80bcf4"
FROZEN_OQL_FIXTURE_SHA256 = "dfcef2c4e5bf1cfa7d18e4dacfa70a1b29b8fd26a93359366cbea32cd57ce97e"
FROZEN_PREREGISTRATION_SHA256 = "eace24a94ed3e206b401e8264675f81b7e7278b6aa90b39a55ac26353d1cb89c"
FROZEN_AMENDMENT_SHA256 = "1fb7517081f5cc73a37021768aabf08443970b71365ba41816c623be90302b39"
FROZEN_MAIN_REQUEST_ORACLE_SHA256 = "c6d741fdb9e8fbe2e0b70a6097cd505d2100c849c375e44e99df29226a531191"
PHASE_SEMANTIC_CONTRACT_SHA256 = "7aee223744adbda6d36dfa03fdc8e08562062b486caa71689eefe149b6f0f6f6"

_PHASE_SEMANTIC_OPTIONS: Mapping[str, tuple[str, ...]] = {
    "register": ("--catalog", "--registration-inputs", "--seal"),
    "preflight": (
        "--bundle", "--catalog", "--checkpoint", "--live", "--output",
        "--registration-inputs", "--responses", "--seal", "--timeout-seconds",
    ),
    "run-ready": (
        "--bundle", "--catalog", "--live", "--output", "--preflight-bundle",
        "--preflight-report", "--registration-inputs", "--responses", "--seal",
        "--timeout-seconds",
    ),
    "resume": (
        "--bundle", "--catalog", "--live", "--preflight-bundle",
        "--registration-inputs", "--responses", "--seal", "--timeout-seconds",
    ),
    "validate-bundle": (
        "<bundle>", "--catalog", "--preflight-bundle", "--registration-inputs",
        "--seal",
    ),
}
PHASE_ARGV_CONTRACTS: Mapping[str, Mapping[str, str]] = {
    phase: {
        "phase": phase,
        "entrypoint": "tools/run_axis3_search.py",
        "command_relation": "immediately_after_entrypoint",
    }
    for phase in _PHASE_SEMANTIC_OPTIONS
}

_PATH_OPTIONS = {
    "--bundle", "--catalog", "--checkpoint", "--output", "--preflight-bundle",
    "--preflight-report", "--registration-inputs", "--responses", "--seal",
    "<bundle>",
}
_FLAG_OPTIONS = {"--live"}

ARXIV_ENDPOINT = "https://export.arxiv.org/api/query"
OPENALEX_ENDPOINT = "https://api.openalex.org/works"
DBLP_ENDPOINT = "https://dblp.org/search/publ/api"

HOST_MINIMUM_INTERVAL_SECONDS: Mapping[str, float] = {
    "export.arxiv.org": 3.0,
    "api.openalex.org": 1.0,
    "dblp.org": 45.0,
}
INDEX_HOSTS: Mapping[str, str] = {
    "arxiv": "export.arxiv.org",
    "openalex": "api.openalex.org",
    "dblp": "dblp.org",
}
MAX_PREFLIGHT_ATTEMPTS_PER_STREAM = 3
PREFLIGHT_RETRY_BACKOFF_SECONDS: Mapping[str, tuple[float, ...]] = {
    "arxiv": (3.0, 6.0, 12.0),
    "openalex": (3.0, 6.0, 12.0),
    "dblp": (15.0, 30.0, 60.0),
}
DBLP_FAILURE_COOLDOWN_SECONDS = 2700.0
_HOST_LIMITER_STATE_VERSION = "axis3-search-host-limiter-state/v1"

ARXIV_FIELD_LOCATORS = (
    "/{http://www.w3.org/2005/Atom}feed/"
    "{http://www.w3.org/2005/Atom}entry/"
    "{http://www.w3.org/2005/Atom}id",
    "/{http://www.w3.org/2005/Atom}feed/"
    "{http://a9.com/-/spec/opensearch/1.1/}totalResults",
)
OPENALEX_FIELD_LOCATORS = (
    "/results/*/id",
    "/meta/count",
    "/meta/next_cursor",
    "/meta/x_query/oql",
)
DBLP_FIELD_LOCATORS = (
    "/result/hits/hit/*/info/key",
    "/result/hits/@total",
    "/result/hits/@first",
    "/result/hits/@sent",
)

OUTSIDE_REGISTERED_MAIN_POPULATION = (
    "venue 本体の年次一覧",
    "ACM Digital Library",
    "書籍",
    "技術報告",
    "学位論文",
    "非英語文献",
    "索引化されていない実装・アーティファクト",
)

POPULATION_CONTRACT: Mapping[str, Any] = {
    "set_operation": "union",
    "main_indexes": ["arxiv", "openalex", "dblp"],
    "index_search_fields": {
        "arxiv": "abstract",
        "openalex": "title_and_abstract",
        "dblp": "bibliography_and_title",
    },
    "cutoff": "2026-12-31",
    "index_cutoff_application": {
        "arxiv": "submittedDate closed year shards through 2026-12-31",
        "openalex": "to_publication_date:2026-12-31",
        "dblp": "client-side record year <= 2026",
    },
    "version_provenance_kind": "version_unavailable_alternative_provenance",
    "retrieval_time_locator": "page_evidence.response_received_at",
    "bibliographic_database_selection": (
        "main union is exactly arXiv, OpenAlex, and DBLP; ACM Digital Library, "
        "books, reports, theses, and unindexed artifacts are outside it"
    ),
    "venue_preprint_distinction": (
        "arXiv main records and DBLP venue auxiliary records remain separate "
        "occurrences and are never merged by title alone"
    ),
    "non_english_treatment": (
        "non-English literature is outside guaranteed enumeration, but records "
        "returned by a registered index are not excluded for language alone"
    ),
    "outside_registered_main_population": list(
        OUTSIDE_REGISTERED_MAIN_POPULATION
    ),
}


class ContractError(ValueError):
    """A fail-closed Axis 3 contract violation with a stable reason code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


TERM_BLOCKS: Mapping[str, tuple[tuple[str, str], ...]] = {
    "T": (
        ("T01", "program synthesis"),
        ("T02", "code generation"),
        ("T03", "software optimization"),
        ("T04", "configuration tuning"),
        ("T05", "design space exploration"),
        ("T06", "automated experimentation"),
        ("T07", "autonomous research"),
        ("T08", "auto-tuning"),
        ("T09", "algorithm configuration"),
        ("T10", "compiler optimization"),
        ("T11", "query optimization"),
        ("T12", "program repair"),
    ),
    "F": (
        ("F01", "proof chain"),
        ("F02", "evidence binding"),
        ("F03", "provenance"),
        ("F04", "data lineage"),
        ("F05", "traceability"),
        ("F06", "audit trail"),
        ("F07", "reproducibility"),
        ("F08", "repeatability"),
        ("F09", "replicability"),
        ("F10", "experiment tracking"),
        ("F11", "research object"),
        ("F12", "build provenance"),
        ("F13", "run manifest"),
        ("F14", "artifact manifest"),
        ("F15", "environment capture"),
        ("F16", "checksum validation"),
        ("F17", "software bill of materials"),
        ("F18", "reproducible build"),
    ),
    "H": (
        ("H01", "mechanistic explanation"),
        ("H02", "causal explanation"),
        ("H03", "explanation generation"),
        ("H04", "performance explanation"),
        ("H05", "root cause analysis"),
        ("H06", "bottleneck diagnosis"),
        ("H07", "performance attribution"),
        ("H08", "explainable optimization"),
        ("H09", "causal profiling"),
        ("H10", "performance debugging"),
        ("H11", "counterfactual explanation"),
        ("H12", "interpretability"),
        ("H13", "explainability"),
        ("H14", "sensitivity analysis"),
        ("H15", "feature importance"),
        ("H16", "critical path analysis"),
        ("H17", "performance model"),
        ("H18", "what-if analysis"),
        ("H19", "variance decomposition"),
    ),
    "O": (
        ("O01", "explanation"),
        ("O02", "rationale"),
        ("O03", "provenance graph"),
        ("O04", "execution trace"),
        ("O05", "audit log"),
        ("O06", "evidence bundle"),
        ("O07", "proof certificate"),
        ("O08", "diagnostic report"),
    ),
    "V": (
        ("V01", "bijection"),
        ("V02", "consistency check"),
        ("V03", "integrity check"),
        ("V04", "tamper detection"),
        ("V05", "replay verification"),
        ("V06", "artifact verification"),
        ("V07", "attestation"),
        ("V08", "mutation testing"),
        ("V09", "end-to-end verification"),
    ),
    "W": (
        ("W01", "performance"),
        ("W02", "latency"),
        ("W03", "throughput"),
        ("W04", "benchmark"),
        ("W05", "workload"),
        ("W06", "scalability"),
        ("W07", "many-core"),
        ("W08", "transaction processing"),
    ),
}

BRANCH_SPECS: Mapping[str, tuple[str, ...]] = {
    "Q1": ("T", "F", "O"),
    "Q2": ("T", "H", "O"),
    "Q3": ("T", "F"),
    "Q4": ("T", "H"),
    "Q5": ("F", "V"),
    "Q6": ("H", "W"),
    "Q7": ("F", "W"),
    "Q8": ("H", "V"),
    "Q9": ("F", "H"),
    "Q10": ("T", "V"),
}

DBLP_BRANCHES = tuple(f"Q{number}" for number in range(3, 11))
ANCHORS = (
    ("01", "2604.24658"),
    ("02", "2507.06999"),
    ("03", "2605.22721"),
    ("04", "2605.23109"),
    ("05", "2605.15221"),
)
VENUES = (
    "SIGMOD",
    "PVLDB",
    "PODS",
    "IPAW",
    "TAPP",
    "WORKS",
    "SIGMETRICS",
    "ICPE",
    "SC",
    "ICSE",
    "ASE",
    "ISSTA",
    "OSDI",
    "SOSP",
)


def _canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _phase_contract_sha256(phase: str) -> str:
    contract = PHASE_ARGV_CONTRACTS.get(phase)
    if contract is None:
        raise ContractError("effective_argv", f"未知のAxis 3 phase: {phase}")
    return _sha256(_canonical_json(contract))


def _normalize_semantic_argv(
    values: Sequence[str], entrypoint: int, phase: str
) -> tuple[list[dict[str, str]], str]:
    allowed = set(_PHASE_SEMANTIC_OPTIONS[phase])
    tokens = list(values[entrypoint + 2 :])
    normalized: dict[str, str] = {}
    positionals: list[str] = []
    offset = 0
    while offset < len(tokens):
        token = tokens[offset]
        if token.startswith("--"):
            if "=" in token:
                name, raw_value = token.split("=", 1)
                has_inline_value = True
            else:
                name, raw_value = token, ""
                has_inline_value = False
            if name not in allowed or name in normalized:
                raise ContractError("effective_argv", f"未登録または重複semantic option: {name}")
            if name in _FLAG_OPTIONS:
                if has_inline_value:
                    raise ContractError("effective_argv", f"flagへ値を付けられない: {name}")
                normalized[name] = "true"
                offset += 1
                continue
            if not has_inline_value:
                offset += 1
                if offset >= len(tokens) or tokens[offset].startswith("--"):
                    raise ContractError("effective_argv", f"option値が無い: {name}")
                raw_value = tokens[offset]
            if not raw_value:
                raise ContractError("effective_argv", f"option値が空: {name}")
            if name == "--timeout-seconds":
                try:
                    timeout = float(raw_value)
                except ValueError as exc:
                    raise ContractError("effective_argv", "timeoutが数値でない") from exc
                if timeout <= 0 or timeout != timeout or timeout in {float("inf"), float("-inf")}:
                    raise ContractError("effective_argv", "timeoutは有限正数が必要")
                normalized[name] = format(timeout, ".17g")
            elif name in _PATH_OPTIONS:
                normalized[name] = str(Path(raw_value).resolve())
            else:
                normalized[name] = raw_value
            offset += 1
            continue
        positionals.append(token)
        offset += 1
    if positionals:
        if phase != "validate-bundle" or len(positionals) != 1:
            raise ContractError("effective_argv", "未登録positional semantic argvがある")
        normalized["<bundle>"] = str(Path(positionals[0]).resolve())
    transport_flags = {name for name in ("--live", "--responses") if name in normalized}
    if phase in {"preflight", "run-ready", "resume"}:
        if len(transport_flags) != 1:
            raise ContractError(
                "effective_argv",
                f"{phase}は--live/--responsesのexact oneが必要",
            )
        artifact_class = (
            "production" if "--live" in transport_flags else "nonproduction_simulation"
        )
        normalized.setdefault("--timeout-seconds", "30")
    else:
        artifact_class = "not_applicable"
    return (
        [{"name": name, "value": normalized[name]} for name in sorted(normalized)],
        artifact_class,
    )


def validate_effective_phase_argv(
    effective_argv: Sequence[str], phase: str
) -> dict[str, Any]:
    """Bind the observed CLI argv to the sealed phase entrypoint contract."""

    values = list(effective_argv)
    if not values or any(not isinstance(value, str) or not value for value in values):
        raise ContractError("effective_argv", "実効argvは非空string arrayが必要")
    entrypoint_positions = [
        offset
        for offset, value in enumerate(values)
        if Path(value).as_posix().endswith("tools/run_axis3_search.py")
    ]
    if len(entrypoint_positions) != 1:
        raise ContractError("effective_argv", "Axis 3 CLI entrypointがargvにexact one必要")
    entrypoint = entrypoint_positions[0]
    if entrypoint + 1 >= len(values) or values[entrypoint + 1] != phase:
        raise ContractError("effective_argv", f"実効argvが{phase} phase契約と不一致")
    semantic_options, artifact_class = _normalize_semantic_argv(
        values, entrypoint, phase
    )
    return {
        "phase": phase,
        "effective_argv": values,
        "effective_argv_sha256": _sha256(_canonical_json(values)),
        "phase_argv_contract_sha256": _phase_contract_sha256(phase),
        "semantic_options": semantic_options,
        "semantic_options_sha256": _sha256(_canonical_json(semantic_options)),
        "artifact_class": artifact_class,
    }


def _semantic_option(phase_argv: Mapping[str, Any], name: str) -> str | None:
    values = phase_argv.get("semantic_options")
    if not isinstance(values, list):
        raise ContractError("bundle_phase_argv", "normalized semantic optionsが無い")
    matches = [
        item.get("value")
        for item in values
        if isinstance(item, Mapping) and item.get("name") == name
    ]
    if len(matches) > 1 or any(not isinstance(value, str) for value in matches):
        raise ContractError("bundle_phase_argv", f"semantic optionが一意でない: {name}")
    return matches[0] if matches else None


def _bind_semantic_path(
    phase_argv: Mapping[str, Any], name: str, actual: Path | None
) -> None:
    sealed = _semantic_option(phase_argv, name)
    if sealed is not None and (actual is None or sealed != str(Path(actual).resolve())):
        raise ContractError("bundle_phase_argv", f"{name}が実呼出しpathと不一致")


def _bind_transport_semantics(
    phase_argv: Mapping[str, Any], transport: Any
) -> None:
    if type(transport) is LiveSearchSession:
        _validate_production_transport_identity(transport._transport)
        observed_class = "production"
    elif type(transport) in {
        ScriptedTransport,
        NonProductionTransport,
        NonProductionHTTPTransport,
    }:
        observed_class = "nonproduction_simulation"
    else:
        raise ContractError(
            "bundle_phase_argv", "canonical live sessionまたはexact nonproduction transportが必要"
        )
    if observed_class != phase_argv.get("artifact_class"):
        raise ContractError("bundle_phase_argv", "実transportとsemantic argv classが不一致")
    timeout = _semantic_option(phase_argv, "--timeout-seconds")
    if timeout is not None and type(transport) in {
        LiveSearchSession,
        NonProductionHTTPTransport,
    }:
        if format(float(transport.timeout_seconds), ".17g") != timeout:
            raise ContractError("bundle_phase_argv", "timeout optionが実transportと不一致")


def _frozen_semantics_payload() -> dict[str, Any]:
    return {
        "term_blocks": {
            block: [{"id": term_id, "term": term} for term_id, term in values]
            for block, values in TERM_BLOCKS.items()
        },
        "branches": {branch: list(blocks) for branch, blocks in BRANCH_SPECS.items()},
        "legacy_ids": sorted(_expected_legacy_ids()),
    }


def validate_frozen_literal_oracles() -> None:
    if _sha256(_canonical_json(_frozen_semantics_payload())) != FROZEN_SEMANTICS_SHA256:
        raise ContractError(
            "frozen_semantics_mismatch",
            "74語、10枝、旧1543 IDが独立した凍結literalと不一致",
        )
    if _sha256(oql_fixture_bytes()) != FROZEN_OQL_FIXTURE_SHA256:
        raise ContractError(
            "frozen_oql_fixture_mismatch",
            "OQL 7正例/6負例が独立した凍結digestと不一致",
        )
    if (
        _sha256(_canonical_json(_PHASE_SEMANTIC_OPTIONS))
        != PHASE_SEMANTIC_CONTRACT_SHA256
    ):
        raise ContractError(
            "phase_semantic_contract_mismatch",
            "phase別semantic argv optionが独立literal digestと不一致",
        )


def extract_frozen_registration_closure(data: bytes) -> dict[str, Any]:
    """Extract the legacy IDs and query vocabulary from the frozen bytes."""

    if _sha256(data) != FROZEN_PREREGISTRATION_SHA256:
        raise ContractError(
            "frozen_preregistration_stale",
            "旧凍結登録bytesが独立literal SHA-256と不一致",
        )
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractError("frozen_preregistration_parse", "旧凍結登録がUTF-8でない") from exc

    def section(start: str, end: str) -> str:
        if text.count(start) != 1 or text.count(end) != 1:
            raise ContractError(
                "frozen_preregistration_parse",
                f"旧凍結登録のsection境界が一意でない: {start}",
            )
        value = text.split(start, 1)[1].split(end, 1)[0]
        if not value:
            raise ContractError("frozen_preregistration_parse", f"旧凍結登録sectionが空: {start}")
        return value

    term_section = section("### 3.1 概念ブロック (74 語)", "### 3.2 登録する枝")
    term_pairs = re.findall(
        r"\|\s*`([TFHOVW][0-9]{2})`\s*\|\s*`([^`\r\n]+)`",
        term_section,
    )
    if len(term_pairs) != 74 or len({term_id for term_id, _ in term_pairs}) != 74:
        raise ContractError(
            "frozen_preregistration_query_semantics",
            "旧凍結登録の語表からexact 74 ID/語を抽出できない",
        )
    extracted_terms: dict[str, list[dict[str, str]]] = {
        block: [] for block in ("T", "F", "H", "O", "V", "W")
    }
    for term_id, term in sorted(term_pairs):
        extracted_terms[term_id[0]].append({"id": term_id, "term": term})

    branch_section = section("### 3.2 登録する枝", "### 3.3 canonical request bytes")
    branch_pairs = re.findall(
        r"\|\s*`(Q(?:10|[1-9]))`\s*\|\s*"
        r"([TFHOVW](?:\s*∧\s*[TFHOVW]){1,2})\s*\|",
        branch_section,
    )
    extracted_branches = {
        branch: re.split(r"\s*∧\s*", expression)
        for branch, expression in branch_pairs
    }
    if len(branch_pairs) != 10 or len(extracted_branches) != 10:
        raise ContractError(
            "frozen_preregistration_query_semantics",
            "旧凍結登録の枝表からexact 10枝を抽出できない",
        )

    arxiv_section = section("### 3.4 arXiv の完全 query", "### 3.5 OpenAlex の完全 query")
    openalex_section = section("### 3.5 OpenAlex の完全 query", "### 3.6 DBLP")
    direct_ids = re.findall(r"`(AX3-Q(?:10|[1-9])@arxiv)`", arxiv_section)
    direct_ids.extend(
        re.findall(r"`(AX3-Q(?:10|[1-9])@openalex)`", openalex_section)
    )
    expected_direct = [
        f"AX3-Q{number}@{index}"
        for index in ("arxiv", "openalex")
        for number in range(1, 11)
    ]
    if Counter(direct_ids) != Counter(expected_direct):
        raise ContractError(
            "frozen_preregistration_parse",
            "旧凍結登録のarXiv/OpenAlex legacy IDがexact 20でない",
        )

    dblp_section = section("### 3.6 DBLP", "### 3.7 登録した query ID")
    if (
        "`AX3-<枝>-<語1 の ID>-<語2 の ID>@dblp`" not in dblp_section
        or "`q=<語1>%20<語2>&format=json&h=100&f=<0,100,200,...>`"
        not in dblp_section
    ):
        raise ContractError(
            "frozen_preregistration_query_semantics",
            "旧凍結登録のDBLP ID/request生成規則を抽出できない",
        )
    product_rows = re.findall(
        r"\|\s*`(Q(?:10|[3-9]))`\s*\|\s*"
        r"([TFHOVW])\(([0-9]+)\)\s*×\s*([TFHOVW])\(([0-9]+)\)"
        r"\s*\|\s*([0-9]+)\s*\|",
        dblp_section,
    )
    if len(product_rows) != 8:
        raise ContractError(
            "frozen_preregistration_query_semantics",
            "旧凍結登録のDBLP exact 8直積を抽出できない",
        )
    extracted_products: dict[str, tuple[str, str]] = {}
    for branch, left, left_count, right, right_count, product_count in product_rows:
        if extracted_branches.get(branch) != [left, right]:
            raise ContractError(
                "frozen_preregistration_query_semantics",
                f"旧凍結登録の{branch}枝とDBLP直積が不一致",
            )
        if (
            len(extracted_terms[left]) != int(left_count)
            or len(extracted_terms[right]) != int(right_count)
            or int(left_count) * int(right_count) != int(product_count)
        ):
            raise ContractError(
                "frozen_preregistration_query_semantics",
                f"旧凍結登録の{branch} DBLP直積件数が不一致",
            )
        extracted_products[branch] = (left, right)
    expanded_dblp = {
        f"AX3-{branch}-{left['id']}-{right['id']}@dblp"
        for branch, (left_block, right_block) in extracted_products.items()
        for left in extracted_terms[left_block]
        for right in extracted_terms[right_block]
    }
    legacy_ids = sorted(set(expected_direct) | expanded_dblp)
    if len(legacy_ids) != 1543:
        raise ContractError(
            "frozen_preregistration_parse",
            "旧凍結登録の直積規則からlegacy IDをexact 1543展開できない",
        )
    extracted = {
        "legacy_ids": legacy_ids,
        "term_blocks": extracted_terms,
        "branches": dict(sorted(extracted_branches.items())),
        "dblp_products": {
            branch: list(blocks) for branch, blocks in sorted(extracted_products.items())
        },
    }
    frozen_payload = {
        key: extracted[key] for key in ("term_blocks", "branches", "legacy_ids")
    }
    if _sha256(_canonical_json(frozen_payload)) != FROZEN_SEMANTICS_SHA256:
        raise ContractError(
            "frozen_preregistration_query_semantics",
            "旧凍結登録から抽出した74語、10枝、1543 IDのliteral digestが不一致",
        )
    return extracted


def extract_frozen_main_request_oracle(data: bytes) -> dict[str, Any]:
    """Independently parse frozen Markdown into all 1,893 main requests."""

    if _sha256(data) != FROZEN_PREREGISTRATION_SHA256:
        raise ContractError("frozen_preregistration_stale", "旧凍結登録bytesが不一致")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractError("frozen_main_request_oracle", "旧凍結登録がUTF-8でない") from exc

    headings = list(
        re.finditer(r"(?m)^### (3\.[1-7]) ([^\r\n]+)\r?$", text)
    )
    sections: dict[str, str] = {}
    for offset, heading in enumerate(headings):
        start = heading.end()
        end = headings[offset + 1].start() if offset + 1 < len(headings) else len(text)
        sections[heading.group(1)] = text[start:end]
    if set(sections) != {"3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7"}:
        raise ContractError("frozen_main_request_oracle", "旧凍結登録3.1〜3.7を一意に切れない")

    term_rows = re.findall(
        r"\|\s*`([TFHOVW][0-9]{2})`\s*\|\s*`([^`\r\n]+)`",
        sections["3.1"],
    )
    if len(term_rows) != 74 or len({key for key, _ in term_rows}) != 74:
        raise ContractError("frozen_main_request_oracle", "独立parserでexact 74語を得られない")
    terms_by_block: dict[str, list[tuple[str, str]]] = {
        block: [] for block in "TFHOVW"
    }
    for term_id, phrase in term_rows:
        terms_by_block[term_id[0]].append((term_id, phrase))
    for values in terms_by_block.values():
        values.sort()

    branch_rows = re.findall(
        r"\|\s*`(Q(?:10|[1-9]))`\s*\|\s*"
        r"([TFHOVW](?:\s*∧\s*[TFHOVW]){1,2})\s*\|",
        sections["3.2"],
    )
    branches = {
        branch: tuple(re.split(r"\s*∧\s*", expression))
        for branch, expression in branch_rows
    }
    if len(branch_rows) != 10 or len(branches) != 10:
        raise ContractError("frozen_main_request_oracle", "独立parserでexact 10枝を得られない")

    product_rows = re.findall(
        r"\|\s*`(Q(?:10|[3-9]))`\s*\|\s*"
        r"([TFHOVW])\(([0-9]+)\)\s*×\s*([TFHOVW])\(([0-9]+)\)"
        r"\s*\|\s*([0-9]+)\s*\|",
        sections["3.6"],
    )
    products = {
        branch: (left, right)
        for branch, left, _left_count, right, _right_count, _total in product_rows
    }
    if len(product_rows) != 8 or any(branches.get(key) != value for key, value in products.items()):
        raise ContractError("frozen_main_request_oracle", "独立parserでDBLP 8直積を得られない")

    def phrase_group(block: str, *, arxiv: bool) -> str:
        prefix = "abs:" if arxiv else ""
        return "(" + " OR ".join(
            f'{prefix}"{phrase}"' for _, phrase in terms_by_block[block]
        ) + ")"

    def expression(branch: str, *, arxiv: bool) -> str:
        return " AND ".join(
            phrase_group(block, arxiv=arxiv) for block in branches[branch]
        )

    def term_ast(phrase: str) -> dict[str, Any]:
        return {"type": "term", "stemmed": True, "phrase": phrase}

    def block_ast(block: str) -> dict[str, Any]:
        children = [term_ast(phrase) for _, phrase in terms_by_block[block]]
        return {"type": "or", "children": sorted(children, key=_canonical_json)}

    def expected_oql_ast(branch: str) -> dict[str, Any]:
        search_expression = {
            "type": "and",
            "children": sorted(
                [block_ast(block) for block in branches[branch]],
                key=_canonical_json,
            ),
        }
        clauses = [
            {"type": "search", "field": "title/abstract", "expression": search_expression},
            {"type": "date", "comparator": "<=", "value": "2026-12-31"},
        ]
        return {"type": "oql", "clauses": sorted(clauses, key=_canonical_json)}

    requests: dict[str, dict[str, Any]] = {}
    for number in range(1, 11):
        branch = f"Q{number}"
        for year in range(1991, 2027):
            query = (
                f"{expression(branch, arxiv=True)} AND "
                f"submittedDate:[{year}01010000 TO {year}12312359]"
            )
            requests[f"AX3A1-Q{number:02d}-S{year}@arxiv"] = {
                "canonical_template": (
                    "https://export.arxiv.org/api/query?search_query="
                    f"{quote_plus(query, safe='()')}&start={{POS}}&max_results=200"
                ),
                "expected_oql_ast": None,
            }
        openalex_expression = expression(branch, arxiv=False)
        filter_value = (
            f"title_and_abstract.search:{openalex_expression},"
            "to_publication_date:2026-12-31"
        )
        requests[f"AX3A1-Q{number:02d}@openalex"] = {
            "canonical_template": (
                "https://api.openalex.org/works?filter="
                f"{quote(filter_value, safe='()')}&per-page=200&cursor={{CUR}}"
            ),
            "expected_oql_ast": expected_oql_ast(branch),
        }
    term_lookup = {
        term_id: phrase
        for values in terms_by_block.values()
        for term_id, phrase in values
    }
    for branch, (left_block, right_block) in sorted(products.items()):
        for left_id, _ in terms_by_block[left_block]:
            for right_id, _ in terms_by_block[right_block]:
                query = f"{term_lookup[left_id]} {term_lookup[right_id]}"
                requests[f"AX3A1-{branch}-{left_id}-{right_id}@dblp"] = {
                    "canonical_template": (
                        "https://dblp.org/search/publ/api?q="
                        f"{quote(query, safe='')}&format=json&h=100&f={{POS}}"
                    ),
                    "expected_oql_ast": None,
                }
    oracle = {"main_requests": dict(sorted(requests.items()))}
    if len(requests) != 1893:
        raise ContractError("frozen_main_request_oracle", "main request mapがexact 1893でない")
    if _sha256(_canonical_json(oracle)) != FROZEN_MAIN_REQUEST_ORACLE_SHA256:
        raise ContractError("frozen_main_request_oracle", "main request独立literal digestが不一致")
    return oracle


def validate_frozen_registration_closure(
    catalog: Mapping[str, Any], preregistration_data: bytes
) -> None:
    extracted = extract_frozen_registration_closure(preregistration_data)
    actual_ids = sorted(entry["legacy_id"] for entry in catalog["supersession"])
    if extracted["legacy_ids"] != actual_ids:
        raise ContractError(
            "frozen_preregistration_coverage",
            "旧凍結登録の全1543 IDが生成catalogとexact不一致",
        )
    if (
        extracted["term_blocks"] != catalog.get("term_blocks")
        or extracted["branches"] != catalog.get("branches")
    ):
        raise ContractError(
            "frozen_preregistration_query_semantics",
            "旧凍結登録のquery意味が生成catalogとexact不一致",
        )

    terms = {
        item["id"]: item["term"]
        for values in extracted["term_blocks"].values()
        for item in values
    }
    rows = {
        row["stream_id"]: row
        for row in catalog.get("rows", [])
        if isinstance(row, Mapping) and isinstance(row.get("stream_id"), str)
    }
    supersession = {
        entry["legacy_id"]: entry["replacement_ids"]
        for entry in catalog.get("supersession", [])
        if isinstance(entry, Mapping)
    }
    def block_expression(block: str, index: str) -> str:
        values = [item["term"] for item in extracted["term_blocks"][block]]
        prefix = "abs:" if index == "arxiv" else ""
        return "(" + " OR ".join(f'{prefix}"{value}"' for value in values) + ")"

    def branch_expression(branch: str, index: str) -> str:
        return " AND ".join(
            block_expression(block, index) for block in extracted["branches"][branch]
        )

    for number in range(1, 11):
        branch = f"Q{number}"
        legacy = f"AX3-{branch}@arxiv"
        replacements = supersession.get(legacy)
        if not isinstance(replacements, list) or len(replacements) != 36:
            raise ContractError("frozen_preregistration_coverage", f"{legacy}後継がexact 36でない")
        for year, stream_id in zip(range(1991, 2027), replacements):
            row = rows.get(stream_id)
            if row is None:
                raise ContractError("frozen_preregistration_coverage", f"{stream_id} rowが無い")
            expression = (
                f"{branch_expression(branch, 'arxiv')} AND "
                f"submittedDate:[{year}01010000 TO {year}12312359]"
            )
            expected_template = (
                "https://export.arxiv.org/api/query?search_query="
                f"{quote_plus(expression, safe='()')}&start={{POS}}&max_results=200"
            )
            if (
                row.get("request_factory", {}).get("canonical_template")
                != expected_template
                or row.get("expected_interpreted_query") != expression
            ):
                raise ContractError(
                    "frozen_preregistration_query_semantics",
                    f"{stream_id} arXiv query bytesが旧凍結登録からの再導出値と不一致",
                )

        legacy = f"AX3-{branch}@openalex"
        replacements = supersession.get(legacy)
        stream_id = f"AX3A1-Q{number:02d}@openalex"
        if replacements != [stream_id] or stream_id not in rows:
            raise ContractError("frozen_preregistration_coverage", f"{legacy}後継が不一致")
        search_expression = branch_expression(branch, "openalex")
        filter_value = (
            f"title_and_abstract.search:{search_expression},"
            "to_publication_date:2026-12-31"
        )
        expected_template = (
            "https://api.openalex.org/works?filter="
            f"{quote(filter_value, safe='()')}&per-page=200&cursor={{CUR}}"
        )
        stemmed = re.sub(r'"([^\"]+)"', r'stemmed "\1"', search_expression)
        expected_oql = (
            "works where title/abstract has ("
            f"{stemmed.replace(' OR ', ' or ').replace(' AND ', ' and ')}"
            ") and date <= (2026-12-31)"
        )
        row = rows[stream_id]
        if (
            row.get("request_factory", {}).get("canonical_template") != expected_template
            or row.get("expected_interpreted_query") != expected_oql
        ):
            raise ContractError(
                "frozen_preregistration_query_semantics",
                f"{stream_id} OpenAlex query意味が旧凍結登録からの再導出値と不一致",
            )

    for branch, blocks in extracted["dblp_products"].items():
        left_block, right_block = blocks
        for left in extracted["term_blocks"][left_block]:
            for right in extracted["term_blocks"][right_block]:
                legacy = f"AX3-{branch}-{left['id']}-{right['id']}@dblp"
                stream_id = f"AX3A1-{branch}-{left['id']}-{right['id']}@dblp"
                query = f"{terms[left['id']]} {terms[right['id']]}"
                expected_template = (
                    "https://dblp.org/search/publ/api?q="
                    f"{quote(query, safe='')}&format=json&h=100&f={{POS}}"
                )
                row = rows.get(stream_id)
                if (
                    supersession.get(legacy) != [stream_id]
                    or row is None
                    or row.get("request_factory", {}).get("canonical_template")
                    != expected_template
                    or row.get("expected_interpreted_query")
                    != _expected_dblp_query_echo(query)
                ):
                    raise ContractError(
                        "frozen_preregistration_query_semantics",
                        f"{legacy} DBLP query意味が旧凍結登録からの再導出値と不一致",
                    )

    independent = extract_frozen_main_request_oracle(preregistration_data)
    builder_projection = {
        row["stream_id"]: {
            "canonical_template": row["request_factory"]["canonical_template"],
            "expected_oql_ast": (
                parse_openalex_oql(row["expected_interpreted_query"])
                if row["index"] == "openalex"
                else None
            ),
        }
        for row in catalog.get("rows", [])
        if isinstance(row, Mapping) and row.get("role") == "main"
    }
    if independent["main_requests"] != dict(sorted(builder_projection.items())):
        raise ContractError(
            "frozen_main_request_oracle",
            "独立再構成した1893 request/OQL ASTがbuilder出力とexact不一致",
        )


def resolve_head_commit(repo_root: Path = REPO_ROOT) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=repo_root,
            check=True,
            text=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ContractError("seal_commit", "実HEADを解決できない") from exc
    commit = completed.stdout.strip().lower()
    if not FULL_COMMIT_RE.fullmatch(commit):
        raise ContractError("seal_commit", "実HEADはfull SHAでなければならない")
    return commit


def _canonical_url(value: str) -> tuple[str, str, int | None, str, tuple[tuple[str, str], ...]]:
    parsed = urlsplit(value)
    if (
        parsed.scheme.lower() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise ContractError("response_final_url", "URLはcredential/fragment無しHTTPSが必要")
    try:
        query = tuple(sorted(parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)))
    except ValueError as exc:
        raise ContractError("response_final_url", "URL queryをcanonicalizeできない") from exc
    port = parsed.port
    return parsed.scheme.lower(), parsed.hostname.lower(), port, parsed.path or "/", query


def _request_without_stream(request: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: copy.deepcopy(request[key])
        for key in ("method", "url", "headers", "body_sha256", "position_kind")
    }


def _branch_start_checkpoint_request(row: Mapping[str, Any]) -> dict[str, Any]:
    request = _request_without_stream(materialize_request(row))
    request["position_kind"] = {
        "cursor": "cursor_star",
        "offset": "offset_zero",
        "fixed": "page_zero",
    }[request["position_kind"]]
    return request


def _is_branch_start_request(index: str, request: Mapping[str, Any]) -> bool:
    try:
        pairs = parse_qsl(
            urlsplit(str(request.get("url"))).query,
            keep_blank_values=True,
            strict_parsing=True,
        )
    except ValueError:
        return False
    values = dict(pairs)
    if request.get("position_kind") == "page_zero":
        return True
    if index == "arxiv":
        return request.get("position_kind") == "offset_zero" and values.get("start") == "0"
    if index == "dblp":
        return request.get("position_kind") == "offset_zero" and values.get("f") == "0"
    if index == "openalex":
        return request.get("position_kind") == "cursor_star" and values.get("cursor") == "*"
    return request.get("position_kind") == "page_zero"


def _schema_bytes(path: Path) -> tuple[str, bytes]:
    try:
        return str(path.resolve()), path.read_bytes()
    except OSError as exc:
        raise ContractError("schema_unreadable", f"schemaを読めない: {path}") from exc


@lru_cache(maxsize=32)
def _load_schema_bytes(path_label: str, data: bytes) -> Mapping[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("schema_unreadable", f"schemaを読めない: {path_label}") from exc
    if not isinstance(value, Mapping):
        raise ContractError("schema_invalid", f"schemaがobjectでない: {path_label}")
    Draft7Validator.check_schema(value)
    return value


def _load_schema(path: Path) -> Mapping[str, Any]:
    path_label, data = _schema_bytes(path)
    return copy.deepcopy(_load_schema_bytes(path_label, data))


@lru_cache(maxsize=32)
def _schema_validator_bytes(path_label: str, data: bytes) -> Draft7Validator:
    return Draft7Validator(_load_schema_bytes(path_label, data))


def _schema_validator(path: Path) -> Draft7Validator:
    path_label, data = _schema_bytes(path)
    return _schema_validator_bytes(path_label, data)


def _validate_with_schema(value: Any, path: Path) -> None:
    errors = sorted(
        _schema_validator(path).iter_errors(value),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        error = errors[0]
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        raise ContractError("schema_validation", f"{path.name}:{location}: {error.message}")


def validate_schema_documents(paths: Sequence[Path] = SCHEMA_PATHS) -> None:
    if tuple(Path(path).resolve() for path in paths) != tuple(path.resolve() for path in SCHEMA_PATHS):
        raise ContractError("schema_closure", "Axis 3 schema closureは所定4ファイルと完全一致が必要")
    for path in paths:
        _load_schema(Path(path))


def _term_map() -> dict[str, str]:
    return {term_id: term for block in TERM_BLOCKS.values() for term_id, term in block}


def _block_expression(block: str, index: str) -> str:
    terms = [term for _, term in TERM_BLOCKS[block]]
    if index == "arxiv":
        return "(" + " OR ".join(f'abs:"{term}"' for term in terms) + ")"
    if index == "openalex":
        return "(" + " OR ".join(f'"{term}"' for term in terms) + ")"
    raise ContractError("index_unknown", f"未知の索引: {index}")


def _branch_expression(branch: str, index: str) -> str:
    return " AND ".join(_block_expression(block, index) for block in BRANCH_SPECS[branch])


def _arxiv_url(search_query: str, *, position: str = "{POS}", page_size: int = 200) -> str:
    encoded = quote_plus(search_query, safe="()")
    return (
        f"{ARXIV_ENDPOINT}?search_query={encoded}&start={position}"
        f"&max_results={page_size}"
    )


def _openalex_url(filter_value: str, *, cursor: str = "{CUR}", page_size: int = 200) -> str:
    encoded = quote(filter_value, safe="()")
    return (
        f"{OPENALEX_ENDPOINT}?filter={encoded}&per-page={page_size}&cursor={cursor}"
    )


def _dblp_url(query: str, *, position: str = "{POS}", page_size: int = 100) -> str:
    encoded = quote(query, safe="")
    return (
        f"{DBLP_ENDPOINT}?q={encoded}&format=json&h={page_size}&f={position}"
    )


def _factory(
    index: str,
    canonical_template: str,
    *,
    position_kind: str,
    page_size: int,
) -> dict[str, Any]:
    accept = "application/atom+xml" if index == "arxiv" else "application/json"
    return {
        "state": "complete",
        "method": "GET",
        "canonical_template": canonical_template,
        "headers": [["Accept", accept]],
        "body_sha256": EMPTY_SHA256,
        "position_kind": position_kind,
        "page_size": page_size,
    }


def _blocked_factory(reason: str) -> dict[str, Any]:
    return {"state": "blocked", "blocked_reason": reason}


def _field_locators(index: str, expected_interpreted_query: str | None) -> list[str]:
    if index == "arxiv":
        values = list(ARXIV_FIELD_LOCATORS)
        if expected_interpreted_query is not None:
            values.append("/atom:feed/atom:title")
        return values
    if index == "openalex":
        values = list(OPENALEX_FIELD_LOCATORS)
        if expected_interpreted_query is None:
            values.remove("/meta/x_query/oql")
        return values
    values = list(DBLP_FIELD_LOCATORS)
    if expected_interpreted_query is not None:
        values.append("/result/query")
    return values


def _row(
    stream_id: str,
    *,
    role: str,
    index: str,
    logical_branch_id: str,
    completion_kind: str,
    request_factory: Mapping[str, Any],
    dependencies: Sequence[str] = (),
    supersedes: str | None = None,
    date_shard: Mapping[str, Any] | None = None,
    expected_interpreted_query: str | None = None,
) -> dict[str, Any]:
    state = request_factory["state"]
    resolver_contract = None
    if role == "lookup":
        locator_by_index = {
            "arxiv": {
                "declared_total_locator": "/atom:feed/opensearch:totalResults",
                "elements_locator": "/atom:feed/atom:entry",
                "work_id_locator_template": "/atom:feed/atom:entry/{index}/atom:id",
            },
            "openalex": {
                "declared_total_locator": "/meta/count",
                "elements_locator": "/results",
                "work_id_locator_template": "/results/{index}/id",
            },
            "dblp": {
                "declared_total_locator": "/result/hits/@total",
                "elements_locator": "/result/hits/hit",
                "work_id_locator_template": "/result/hits/hit/{index}/info/key",
            },
        }[index]
        resolver_contract = {
            **locator_by_index,
            "resolution_cardinality": 1,
            "zero_reason": "lookup_zero_results",
            "multiple_reason": "lookup_multiple_results",
            "cardinality_mismatch_reason": "lookup_result_missing",
            "missing_reason": "lookup_work_id_missing",
        }
    return {
        "stream_id": stream_id,
        "role": role,
        "index": index,
        "logical_branch_id": logical_branch_id,
        "completion_kind": completion_kind,
        "registration_status": "ready" if state == "complete" else "blocked",
        "request_factory": dict(request_factory),
        "dependencies": list(dependencies),
        "supersedes": supersedes,
        "date_shard": dict(date_shard) if date_shard is not None else None,
        "required_response_fields": _field_locators(index, expected_interpreted_query),
        "expected_interpreted_query": expected_interpreted_query,
        "resolver_contract": resolver_contract,
        "record_year_locator": (
            "/result/hits/hit/{index}/info/year"
            if index == "dblp" and role == "main"
            else None
        ),
        "cutoff_year": 2026 if index == "dblp" and role == "main" else None,
        "preflight_response_reusable_for_run": False,
    }


def _expected_openalex_oql(search_expression: str, cutoff: str = "2026-12-31") -> str:
    stemmed = re.sub(r'"([^\"]+)"', r'stemmed "\1"', search_expression)
    stemmed = stemmed.replace(" OR ", " or ").replace(" AND ", " and ")
    return (
        f"works where title/abstract has ({stemmed}) "
        f"and date <= ({cutoff})"
    )


def _expected_dblp_query_echo(query: str) -> str:
    """Return the frozen DBLP prefix-query interpretation for a registered q."""

    words = query.replace("-", " ").split()
    return " ".join(word if word.lower() == "to" else f"{word}*" for word in words)


def _main_rows_and_supersession() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    supersession: list[dict[str, Any]] = []

    for number in range(1, 11):
        branch = f"Q{number}"
        legacy = f"AX3-{branch}@arxiv"
        replacements: list[str] = []
        for year in ARXIV_YEARS:
            stream_id = f"AX3A1-Q{number:02d}-S{year}@arxiv"
            replacements.append(stream_id)
            start = f"{year}01010000"
            end = f"{year}12312359"
            query = (
                f"{_branch_expression(branch, 'arxiv')} AND "
                f"submittedDate:[{start} TO {end}]"
            )
            rows.append(
                _row(
                    stream_id,
                    role="main",
                    index="arxiv",
                    logical_branch_id=branch,
                    completion_kind="http",
                    request_factory=_factory(
                        "arxiv",
                        _arxiv_url(query),
                        position_kind="offset",
                        page_size=200,
                    ),
                    supersedes=legacy,
                    date_shard={"year": year, "start": start, "end": end, "closed": True},
                    expected_interpreted_query=query,
                )
            )
        supersession.append({"legacy_id": legacy, "replacement_ids": replacements})

    for number in range(1, 11):
        branch = f"Q{number}"
        legacy = f"AX3-{branch}@openalex"
        stream_id = f"AX3A1-Q{number:02d}@openalex"
        filter_value = (
            f"title_and_abstract.search:{_branch_expression(branch, 'openalex')},"
            "to_publication_date:2026-12-31"
        )
        rows.append(
            _row(
                stream_id,
                role="main",
                index="openalex",
                logical_branch_id=branch,
                completion_kind="http",
                request_factory=_factory(
                    "openalex",
                    _openalex_url(filter_value),
                    position_kind="cursor",
                    page_size=200,
                ),
                supersedes=legacy,
                expected_interpreted_query=_expected_openalex_oql(
                    _branch_expression(branch, "openalex")
                ),
            )
        )
        supersession.append({"legacy_id": legacy, "replacement_ids": [stream_id]})

    terms = _term_map()
    for branch in DBLP_BRANCHES:
        left_block, right_block = BRANCH_SPECS[branch]
        for left_id, _ in TERM_BLOCKS[left_block]:
            for right_id, _ in TERM_BLOCKS[right_block]:
                legacy = f"AX3-{branch}-{left_id}-{right_id}@dblp"
                stream_id = f"AX3A1-{branch}-{left_id}-{right_id}@dblp"
                query = f"{terms[left_id]} {terms[right_id]}"
                rows.append(
                    _row(
                        stream_id,
                        role="main",
                        index="dblp",
                        logical_branch_id=branch,
                        completion_kind="http",
                        request_factory=_factory(
                            "dblp",
                            _dblp_url(query),
                            position_kind="offset",
                            page_size=100,
                        ),
                        supersedes=legacy,
                        expected_interpreted_query=_expected_dblp_query_echo(query),
                    )
                )
                supersession.append({"legacy_id": legacy, "replacement_ids": [stream_id]})

    return rows, supersession


def _control_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    full_date = "submittedDate:[199101010000 TO 202612312359]"

    arxiv_control_values = {
        "C-OR-1-A": f'abs:"provenance" AND {full_date}',
        "C-OR-1-B": f'abs:"data lineage" AND {full_date}',
        "C-OR-1-U": f'(abs:"provenance" OR abs:"data lineage") AND {full_date}',
        "C-AND-1-A": f'abs:"provenance" AND {full_date}',
        "C-AND-1-W": f'abs:"performance" AND {full_date}',
        "C-AND-1-C": f'(abs:"provenance" AND abs:"performance") AND {full_date}',
        "C-DATE-1-OLD": 'abs:"provenance" AND submittedDate:[199101010000 TO 202312312359]',
        "C-DATE-1-FULL": f'abs:"provenance" AND {full_date}',
    }
    for logical_id, value in arxiv_control_values.items():
        rows.append(
            _row(
                f"AX3A1-{logical_id}@arxiv",
                role="control",
                index="arxiv",
                logical_branch_id=logical_id,
                completion_kind="count_only",
                request_factory=_factory(
                    "arxiv",
                    _arxiv_url(value, page_size=1),
                    position_kind="offset",
                    page_size=1,
                ),
                expected_interpreted_query=value,
            )
        )

    openalex_searches = {
        "C-OR-1-A": '"provenance"',
        "C-OR-1-B": '"data lineage"',
        "C-OR-1-U": '("provenance" OR "data lineage")',
        "C-AND-1-A": '"provenance"',
        "C-AND-1-W": '"performance"',
        "C-AND-1-C": '("provenance" AND "performance")',
    }
    for logical_id, search in openalex_searches.items():
        filter_value = (
            f"title_and_abstract.search:{search},to_publication_date:2026-12-31"
        )
        rows.append(
            _row(
                f"AX3A1-{logical_id}@openalex",
                role="control",
                index="openalex",
                logical_branch_id=logical_id,
                completion_kind="count_only",
                request_factory=_factory(
                    "openalex",
                    _openalex_url(filter_value, page_size=1),
                    position_kind="cursor",
                    page_size=1,
                ),
                expected_interpreted_query=_expected_openalex_oql(search),
            )
        )
    for suffix, cutoff in (("OLD", "2023-12-31"), ("FULL", "2026-12-31")):
        logical_id = f"C-DATE-1-{suffix}"
        filter_value = f'title_and_abstract.search:"provenance",to_publication_date:{cutoff}'
        rows.append(
            _row(
                f"AX3A1-{logical_id}@openalex",
                role="control",
                index="openalex",
                logical_branch_id=logical_id,
                completion_kind="count_only",
                request_factory=_factory(
                    "openalex",
                    _openalex_url(filter_value, page_size=1),
                    position_kind="cursor",
                    page_size=1,
                ),
                expected_interpreted_query=_expected_openalex_oql(
                    '"provenance"', cutoff
                ),
            )
        )

    for logical_id, query, kind in (
        ("C-AND-1-A", "provenance", "count_only"),
        ("C-AND-1-W", "performance", "count_only"),
        ("C-AND-1-C", "provenance performance", "count_only"),
        ("C-DBLP-CONJ-X", "repeatability", "http"),
        ("C-DBLP-CONJ-XY", "repeatability provenance", "http"),
    ):
        rows.append(
            _row(
                f"AX3A1-{logical_id}@dblp",
                role="control",
                index="dblp",
                logical_branch_id=logical_id,
                completion_kind=kind,
                request_factory=_factory(
                    "dblp",
                    _dblp_url(query, page_size=1 if kind == "count_only" else 100),
                    position_kind="offset",
                    page_size=1 if kind == "count_only" else 100,
                ),
                expected_interpreted_query=_expected_dblp_query_echo(query),
            )
        )

    return rows


def _derived_controls() -> list[dict[str, Any]]:
    """Return registered zero-wire controls, which are not logical request rows."""

    return [
        {
            "control_id": f"AX3A1-C-ANCHOR@{index}",
            "index": index,
            "control_kind": "anchor_inclusion",
            "dependencies": [
                f"all AX3A1 main rows for {index}",
                f"all AX3A1 L-ID rows for {index}",
            ],
            "status": "blocked",
            "blocked_reason": "lookup到達集合と全main返却集合が未完了",
            "wire_attempt_count": 0,
        }
        for index in ("arxiv", "openalex", "dblp")
    ]


def _lookup_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, arxiv_id in ANCHORS:
        arxiv_url = (
            f"{ARXIV_ENDPOINT}?id_list={quote(arxiv_id, safe='.')}&start=0&max_results=1"
        )
        rows.append(
            _row(
                f"AX3A1-L-ID-{number}@arxiv",
                role="lookup",
                index="arxiv",
                logical_branch_id=f"L-ID-{number}",
                completion_kind="lookup",
                request_factory=_factory(
                    "arxiv", arxiv_url, position_kind="fixed", page_size=1
                ),
            )
        )
        openalex_filter = f"doi:10.48550/arxiv.{arxiv_id}"
        rows.append(
            _row(
                f"AX3A1-L-ID-{number}@openalex",
                role="lookup",
                index="openalex",
                logical_branch_id=f"L-ID-{number}",
                completion_kind="lookup",
                request_factory=_factory(
                    "openalex",
                    _openalex_url(openalex_filter, cursor="%2A", page_size=1),
                    position_kind="fixed",
                    page_size=1,
                ),
            )
        )
        rows.append(
            _row(
                f"AX3A1-L-ID-{number}-ID@dblp",
                role="lookup",
                index="dblp",
                logical_branch_id=f"L-ID-{number}-ID",
                completion_kind="lookup",
                request_factory=_factory(
                    "dblp",
                    _dblp_url(arxiv_id, position="0", page_size=1),
                    position_kind="fixed",
                    page_size=1,
                ),
            )
        )
        rows.append(
            _row(
                f"AX3A1-L-ID-{number}-TITLE@dblp",
                role="lookup",
                index="dblp",
                logical_branch_id=f"L-ID-{number}-TITLE",
                completion_kind="lookup",
                request_factory=_blocked_factory(
                    "凍結登録にDBLP題名queryの完全bytesが無い"
                ),
                dependencies=[f"anchor_title_bytes:{arxiv_id}"],
            )
        )
    return rows


def _auxiliary_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number, arxiv_id in ANCHORS:
        for kind, dependency in (
            ("BACKWARD", f"openalex_work_id:{arxiv_id}"),
            ("FORWARD", f"openalex_work_id:{arxiv_id}"),
        ):
            rows.append(
                _row(
                    f"AX3A1-AUX-{kind}-{number}@openalex",
                    role="auxiliary",
                    index="openalex",
                    logical_branch_id=f"AUX-{kind}-{number}",
                    completion_kind="auxiliary",
                    request_factory=_blocked_factory(
                        "OpenAlex work IDと完全request factoryが未解決"
                    ),
                    dependencies=[dependency],
                )
            )
        for position in ("FIRST", "LAST"):
            rows.append(
                _row(
                    f"AX3A1-AUX-AUTHOR-{number}-{position}@openalex",
                    role="auxiliary",
                    index="openalex",
                    logical_branch_id=f"AUX-AUTHOR-{number}-{position}",
                    completion_kind="auxiliary",
                    request_factory=_blocked_factory(
                        "OpenAlex author IDと一意抽出規則が未解決"
                    ),
                    dependencies=[f"openalex_{position.lower()}_author_id:{arxiv_id}"],
                )
            )
    for venue in VENUES:
        for year in range(2015, 2027):
            rows.append(
                _row(
                    f"AX3A1-AUX-VENUE-{venue}-{year}@dblp",
                    role="auxiliary",
                    index="dblp",
                    logical_branch_id=f"AUX-VENUE-{venue}-{year}",
                    completion_kind="auxiliary",
                    request_factory=_blocked_factory(
                        "DBLP venue endpoint、venue key、URL templateが未解決"
                    ),
                    dependencies=[
                        "dblp_venue_key",
                        f"dblp_venue_key:{venue}",
                        "dblp_venue_endpoint",
                    ],
                )
            )
    return rows


def build_axis3_catalog() -> dict[str, Any]:
    """Mechanically reconstruct the frozen Axis 3 catalog without network I/O."""

    main_rows, supersession = _main_rows_and_supersession()
    rows = main_rows + _control_rows() + _lookup_rows() + _auxiliary_rows()
    derived_controls = _derived_controls()
    rows.sort(key=lambda row: row["stream_id"])
    supersession.sort(key=lambda row: row["legacy_id"])

    by_role = {
        role: sum(row["role"] == role for row in rows)
        for role in ("main", "control", "lookup", "auxiliary")
    }
    by_factory_state = {
        state: sum(row["request_factory"]["state"] == state for row in rows)
        for state in ("complete", "blocked", "derived")
    }
    return {
        "schema_version": CATALOG_VERSION,
        "namespace": NEW_NAMESPACE,
        "frozen_registration": {
            "term_count": sum(len(block) for block in TERM_BLOCKS.values()),
            "branch_count": len(BRANCH_SPECS),
            "legacy_main_id_count": len(supersession),
            "new_main_row_count": len(main_rows),
            "arxiv_years": list(ARXIV_YEARS),
            "dblp_product_count": sum(
                len(TERM_BLOCKS[BRANCH_SPECS[branch][0]])
                * len(TERM_BLOCKS[BRANCH_SPECS[branch][1]])
                for branch in DBLP_BRANCHES
            ),
        },
        "population_contract": copy.deepcopy(dict(POPULATION_CONTRACT)),
        "term_blocks": {
            block: [{"id": term_id, "term": term} for term_id, term in values]
            for block, values in TERM_BLOCKS.items()
        },
        "branches": {branch: list(blocks) for branch, blocks in BRANCH_SPECS.items()},
        "supersession": supersession,
        "rows": rows,
        "derived_controls": derived_controls,
        "accounting": {
            "logical_row_count": len(rows),
            "nonlogical_derived_control_count": len(derived_controls),
            "by_role": by_role,
            "by_request_factory_state": by_factory_state,
            "wire_attempt_count": 0,
            "reason": (
                "logical rows include 1893 main rows, 41 control/lookup request rows, "
                "and 188 unresolved auxiliary rows; three C-ANCHOR inclusion controls "
                "are separately registered as zero-wire derived controls"
            ),
        },
        "selection_is_frozen": True,
    }


def catalog_bytes(catalog: Mapping[str, Any]) -> bytes:
    return _canonical_json(catalog)


def _expected_legacy_ids() -> set[str]:
    _, supersession = _main_rows_and_supersession()
    return {row["legacy_id"] for row in supersession}


def validate_supersession(catalog: Mapping[str, Any]) -> None:
    entries = catalog.get("supersession")
    if not isinstance(entries, list):
        raise ContractError("supersession_shape", "supersessionはarrayが必要")
    legacy_ids = [entry.get("legacy_id") for entry in entries if isinstance(entry, Mapping)]
    expected = _expected_legacy_ids()
    if len(legacy_ids) != 1543 or len(set(legacy_ids)) != 1543 or set(legacy_ids) != expected:
        raise ContractError(
            "supersession_coverage",
            "旧1543 main IDは欠落・重複なくちょうど1回ずつ必要",
        )
    for entry in entries:
        replacements = entry.get("replacement_ids")
        if not isinstance(replacements, list) or not replacements:
            raise ContractError("supersession_empty", "replacement_idsは1本以上必要")
        if len(replacements) != len(set(replacements)):
            raise ContractError("supersession_duplicate_replacement", "replacement IDが重複")
        if any(
            not isinstance(stream_id, str)
            or not stream_id.startswith(NEW_NAMESPACE)
            or stream_id.startswith(LEGACY_NAMESPACE + "Q")
            for stream_id in replacements
        ):
            raise ContractError("legacy_namespace", "後継IDはAX3A1 namespaceだけを許す")


def validate_year_shards(catalog: Mapping[str, Any]) -> None:
    rows = {
        row.get("stream_id"): row
        for row in catalog.get("rows", [])
        if isinstance(row, Mapping)
    }
    supersession = {
        entry["legacy_id"]: entry["replacement_ids"]
        for entry in catalog.get("supersession", [])
        if isinstance(entry, Mapping)
        and isinstance(entry.get("legacy_id"), str)
        and isinstance(entry.get("replacement_ids"), list)
    }
    for number in range(1, 11):
        legacy = f"AX3-Q{number}@arxiv"
        expected_ids = [f"AX3A1-Q{number:02d}-S{year}@arxiv" for year in ARXIV_YEARS]
        if supersession.get(legacy) != expected_ids:
            raise ContractError("year_shard_exact_cover", f"{legacy}の36年replacementが不一致")
        for year, stream_id in zip(ARXIV_YEARS, expected_ids):
            row = rows.get(stream_id)
            expected = {
                "year": year,
                "start": f"{year}01010000",
                "end": f"{year}12312359",
                "closed": True,
            }
            if row is None or row.get("date_shard") != expected:
                raise ContractError(
                    "year_shard_exact_cover",
                    f"{stream_id}にgap/overlapのない固定閉区間が必要",
                )


def validate_catalog(catalog: Mapping[str, Any]) -> Mapping[str, Any]:
    _validate_with_schema(catalog, SCHEMA_PATHS[0])
    validate_frozen_literal_oracles()
    validate_supersession(catalog)
    validate_year_shards(catalog)
    expected = build_axis3_catalog()
    if catalog != expected:
        raise ContractError(
            "catalog_frozen_mismatch",
            "catalogは凍結74語、10枝、全logical rowの機械再構成と一致しない",
        )
    return catalog["accounting"]


def reject_legacy_outgoing(row: Mapping[str, Any]) -> None:
    stream_id = row.get("stream_id")
    if not isinstance(stream_id, str) or not stream_id.startswith(NEW_NAMESPACE):
        raise ContractError("legacy_outgoing", "outgoing streamはAX3A1 namespaceだけを許す")
    if re.match(r"^AX3-Q", stream_id):
        raise ContractError("legacy_outgoing", "旧AX3-Q IDを送信できない")


def materialize_request(row: Mapping[str, Any], position: int | str | None = None) -> dict[str, Any]:
    reject_legacy_outgoing(row)
    factory = row.get("request_factory")
    if not isinstance(factory, Mapping) or factory.get("state") != "complete":
        raise ContractError("request_factory_blocked", "completeなrequest factoryだけ送信できる")
    template = factory["canonical_template"]
    position_kind = factory["position_kind"]
    if position_kind == "offset":
        value = 0 if position is None else position
        if not isinstance(value, int) or value < 0:
            raise ContractError("request_position", "offsetは非負整数が必要")
        url = template.replace("{POS}", str(value))
    elif position_kind == "cursor":
        value = "%2A" if position is None else str(position)
        url = template.replace("{CUR}", value)
    elif position_kind == "fixed":
        if position is not None:
            raise ContractError("request_position", "fixed requestへ位置を指定できない")
        url = template
    else:
        raise ContractError("request_position", "未知のposition kind")
    if "{POS}" in url or "{CUR}" in url:
        raise ContractError("request_position", "request placeholderが未解決")
    return {
        "stream_id": row["stream_id"],
        "index": row["index"],
        "method": factory["method"],
        "url": url,
        "headers": copy.deepcopy(factory["headers"]),
        "body_sha256": factory["body_sha256"],
        "position_kind": position_kind,
    }


@dataclass(frozen=True)
class _Token:
    kind: str
    value: str


def _tokenize_oql(raw: str) -> list[_Token]:
    tokens: list[_Token] = []
    position = 0
    while position < len(raw):
        character = raw[position]
        if character in " \t\r\n":
            position += 1
            continue
        if raw.startswith(("<=", ">="), position):
            tokens.append(_Token("COMPARATOR", raw[position : position + 2]))
            position += 2
            continue
        if character in "<>=":
            tokens.append(_Token("COMPARATOR", character))
            position += 1
            continue
        if character == "(":
            tokens.append(_Token("LPAREN", character))
            position += 1
            continue
        if character == ")":
            tokens.append(_Token("RPAREN", character))
            position += 1
            continue
        if character == '"':
            end = raw.find('"', position + 1)
            if end < 0:
                raise ContractError("oql_lex", "quoted phraseが閉じていない")
            phrase = raw[position + 1 : end]
            if not phrase or "\\" in phrase:
                raise ContractError("oql_lex", "空句またはescape系列を許さない")
            tokens.append(_Token("PHRASE", phrase))
            position = end + 1
            continue
        end = position
        while end < len(raw) and raw[end] not in " \t\r\n()<>='\"":
            end += 1
        if end == position:
            raise ContractError("oql_lex", f"未知の文字: {raw[position]!r}")
        tokens.append(_Token("WORD", raw[position:end]))
        position = end
    return tokens


class _OqlParser:
    def __init__(self, tokens: Sequence[_Token]):
        self.tokens = list(tokens)
        self.position = 0

    def _peek(self, kind: str | None = None, value: str | None = None) -> bool:
        if self.position >= len(self.tokens):
            return False
        token = self.tokens[self.position]
        return (kind is None or token.kind == kind) and (value is None or token.value == value)

    def _take(self, kind: str, value: str | None = None) -> _Token:
        if not self._peek(kind, value):
            expected = value if value is not None else kind
            actual = self.tokens[self.position].value if self.position < len(self.tokens) else "<eof>"
            raise ContractError("oql_parse", f"{expected}を期待したが{actual}")
        token = self.tokens[self.position]
        self.position += 1
        return token

    def parse(self) -> Mapping[str, Any]:
        self._take("WORD", "works")
        self._take("WORD", "where")
        clauses = [self._clause()]
        while self._peek("WORD", "and"):
            self._take("WORD", "and")
            clauses.append(self._clause())
        if self.position != len(self.tokens):
            raise ContractError("oql_trailing", "OQLを最後まで消費できない")
        return {"type": "oql", "clauses": _sort_nodes(clauses)}

    def _clause(self) -> Mapping[str, Any]:
        if self._peek("WORD", "date"):
            self._take("WORD", "date")
            comparator = self._take("COMPARATOR").value
            self._take("LPAREN")
            date = self._take("WORD").value
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
                raise ContractError("oql_date", "ISO dateが必要")
            self._take("RPAREN")
            return {"type": "date", "comparator": comparator, "value": date}
        field = self._take("WORD").value
        if field not in {"title/abstract", "title", "abstract"}:
            raise ContractError("oql_field", f"未知のfield: {field}")
        self._take("WORD", "has")
        self._take("LPAREN")
        expression = self._expression()
        self._take("RPAREN")
        return {"type": "search", "field": field, "expression": expression}

    def _term(self) -> Mapping[str, Any]:
        stemmed = False
        if self._peek("WORD", "stemmed"):
            self._take("WORD", "stemmed")
            stemmed = True
        phrase = self._take("PHRASE").value
        return {"type": "term", "stemmed": stemmed, "phrase": phrase}

    def _group_or_term(self) -> tuple[Mapping[str, Any], bool]:
        if self._peek("LPAREN"):
            self._take("LPAREN")
            value = self._expression()
            self._take("RPAREN")
            return value, True
        return self._term(), False

    def _expression(self) -> Mapping[str, Any]:
        first, first_grouped = self._group_or_term()
        if not self._peek("WORD") or self.tokens[self.position].value not in {"and", "or"}:
            return first
        operator = self._take("WORD").value
        children = [first]
        if operator == "or" and first_grouped:
            raise ContractError("oql_grouping", "or_exprのoperandはtermだけを許す")
        while True:
            child, grouped = self._group_or_term()
            if operator == "or" and grouped:
                raise ContractError("oql_grouping", "or_exprのoperandはtermだけを許す")
            children.append(child)
            if not self._peek("WORD", operator):
                break
            self._take("WORD", operator)
        if self._peek("WORD") and self.tokens[self.position].value in {"and", "or"}:
            raise ContractError("oql_grouping", "同一階層でand/orを混在できない")
        return {"type": operator, "children": _sort_nodes(children)}


def _sort_nodes(nodes: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return sorted(nodes, key=lambda node: _canonical_json(node))


def parse_openalex_oql(raw: str) -> Mapping[str, Any]:
    if not isinstance(raw, str) or not raw.strip():
        raise ContractError("oql_empty", "OQLは非空文字列が必要")
    return _OqlParser(_tokenize_oql(raw)).parse()


def openalex_oql_matches(raw: str, expected_raw: str) -> bool:
    try:
        return parse_openalex_oql(raw) == parse_openalex_oql(expected_raw)
    except ContractError:
        return False


def registered_oql_fixtures() -> list[dict[str, Any]]:
    single = 'works where title/abstract has (stemmed "provenance")'
    two_expected = (
        'works where title/abstract has (stemmed "data lineage" or stemmed "provenance")'
    )
    three_expected = (
        'works where title/abstract has (stemmed "audit trail" or '
        'stemmed "data lineage" or stemmed "provenance")'
    )
    grouped_expected = (
        'works where title/abstract has ((stemmed "latency" or stemmed "performance") '
        'and (stemmed "data lineage" or stemmed "provenance"))'
    )
    dated = single + " and date <= (2026-12-31)"
    fixtures = [
        {"name": "positive-single", "accepted": True, "raw": single, "expected": single},
        {
            "name": "positive-two-or-reordered",
            "accepted": True,
            "raw": 'works where title/abstract has (stemmed "provenance" or stemmed "data lineage")',
            "expected": two_expected,
        },
        {
            "name": "positive-three-or-reordered",
            "accepted": True,
            "raw": (
                'works where title/abstract has (stemmed "provenance" or '
                'stemmed "audit trail" or stemmed "data lineage")'
            ),
            "expected": three_expected,
        },
        {
            "name": "positive-two-block-and-reordered",
            "accepted": True,
            "raw": (
                'works where title/abstract has ((stemmed "provenance" or '
                'stemmed "data lineage") and (stemmed "performance" or stemmed "latency"))'
            ),
            "expected": grouped_expected,
        },
        {
            "name": "positive-date-first",
            "accepted": True,
            "raw": "date <= (2026-12-31)".join(("works where ", " and title/abstract has (stemmed \"provenance\")")),
            "expected": dated,
        },
        {"name": "positive-date-last", "accepted": True, "raw": dated, "expected": dated},
        {
            "name": "positive-whitespace",
            "accepted": True,
            "raw": "works\twhere title/abstract has ( stemmed \"provenance\" )",
            "expected": single,
        },
        {
            "name": "negative-field",
            "accepted": False,
            "raw": 'works where title has (stemmed "provenance")',
            "expected": single,
        },
        {
            "name": "negative-phrase-split",
            "accepted": False,
            "raw": 'works where title/abstract has (stemmed "data" and stemmed "lineage")',
            "expected": 'works where title/abstract has (stemmed "data lineage")',
        },
        {
            "name": "negative-comparator",
            "accepted": False,
            "raw": single + " and date < (2026-12-31)",
            "expected": dated,
        },
        {
            "name": "negative-stemmed",
            "accepted": False,
            "raw": 'works where title/abstract has ("provenance")',
            "expected": single,
        },
        {
            "name": "negative-missing-close",
            "accepted": False,
            "raw": 'works where title/abstract has (stemmed "provenance"',
            "expected": single,
        },
        {
            "name": "negative-trailing",
            "accepted": False,
            "raw": single + " unexpected",
            "expected": single,
        },
    ]
    return fixtures


def oql_fixture_bytes() -> bytes:
    return _canonical_json(registered_oql_fixtures())


def validate_registered_oql_fixtures() -> Mapping[str, int]:
    fixtures = registered_oql_fixtures()
    positives = negatives = 0
    for fixture in fixtures:
        matched = openalex_oql_matches(fixture["raw"], fixture["expected"])
        if matched != fixture["accepted"]:
            raise ContractError("oql_fixture", f"fixture不一致: {fixture['name']}")
        positives += int(fixture["accepted"])
        negatives += int(not fixture["accepted"])
    if (positives, negatives) != (7, 6):
        raise ContractError("oql_fixture_count", "OQL fixtureは正例7・負例6が必要")
    return {"positive": positives, "negative": negatives}


def _decode_json_object(entity_body: bytes) -> Mapping[str, Any]:
    try:
        value = json.loads(entity_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("response_json", "entity bodyがUTF-8 JSONでない") from exc
    if not isinstance(value, Mapping):
        raise ContractError("response_json", "response JSON rootはobjectが必要")
    return value


def canonicalize_index_work_id(index: str, raw_value: str) -> str:
    """Return the strict index-specific work ID while preserving raw elsewhere."""

    if not isinstance(raw_value, str) or raw_value != raw_value.strip() or not raw_value:
        raise ContractError("index_work_id_invalid", "work IDは前後空白のない文字列が必要")
    if index == "openalex":
        candidate = raw_value
        if raw_value.startswith("https://"):
            parsed = urlsplit(raw_value)
            if (
                parsed.scheme != "https"
                or parsed.netloc.lower() != "openalex.org"
                or parsed.query
                or parsed.fragment
                or not re.fullmatch(r"/W[1-9][0-9]*", parsed.path)
            ):
                raise ContractError("index_work_id_invalid", "OpenAlex work URLがstrict形式外")
            candidate = parsed.path[1:]
        if not OPENALEX_WORK_ID_RE.fullmatch(candidate):
            raise ContractError("index_work_id_invalid", "OpenAlex work IDはWと非零数字列が必要")
        return candidate
    if index == "arxiv":
        candidate = raw_value
        if "://" in raw_value:
            parsed = urlsplit(raw_value)
            if (
                parsed.scheme not in {"http", "https"}
                or parsed.hostname not in {"arxiv.org", "www.arxiv.org", "export.arxiv.org"}
                or parsed.query
                or parsed.fragment
                or not parsed.path.startswith("/abs/")
            ):
                raise ContractError("index_work_id_invalid", "arXiv work URLがstrict形式外")
            candidate = parsed.path[len("/abs/") :]
        candidate = re.sub(r"v[1-9][0-9]*$", "", candidate)
        if not (ARXIV_NEW_ID_RE.fullmatch(candidate) or ARXIV_OLD_ID_RE.fullmatch(candidate)):
            raise ContractError("index_work_id_invalid", "arXiv IDがstrict形式外")
        return candidate
    if index == "dblp":
        if (
            not DBLP_WORK_ID_RE.fullmatch(raw_value)
            or "//" in raw_value
            or any(segment in {".", ".."} for segment in raw_value.split("/"))
        ):
            raise ContractError("index_work_id_invalid", "DBLP keyがstrict形式外")
        return raw_value
    raise ContractError("index_unknown", f"未知の索引: {index}")


def extract_index_work_records(index: str, entity_body: bytes) -> list[dict[str, str]]:
    """Extract raw locator values, concrete locators, and canonical work IDs."""

    records: list[dict[str, str]] = []
    if index == "arxiv":
        try:
            root = ET.fromstring(entity_body)
        except ET.ParseError as exc:
            raise ContractError("response_xml", "arXiv entity bodyがXMLでない") from exc
        if root.tag != f"{{{ATOM_NS}}}feed":
            raise ContractError("index_work_id_missing", "Atom namespace付きfeedが必要")
        for offset, entry in enumerate(root.findall(f"{{{ATOM_NS}}}entry")):
            raw_before_strip = extract_index_work_id("arxiv", entry)
            raw = raw_before_strip.strip()
            records.append(
                {
                    "raw_index_work_id_before_strip": raw_before_strip,
                    "raw_index_work_id": raw,
                    "index_work_id": canonicalize_index_work_id("arxiv", raw),
                    "field_locator": f"/atom:feed/atom:entry/{offset}/atom:id",
                }
            )
        return records
    value = _decode_json_object(entity_body)
    if index == "openalex":
        values = value.get("results")
        prefix = "/results"
        suffix = "id"
    elif index == "dblp":
        try:
            values = value["result"]["hits"]["hit"]
        except (KeyError, TypeError) as exc:
            raise ContractError("index_work_id_missing", "/result/hits/hit arrayが必要") from exc
        prefix = "/result/hits/hit"
        suffix = "info/key"
    else:
        raise ContractError("index_unknown", f"未知の索引: {index}")
    if not isinstance(values, list):
        raise ContractError("index_work_id_missing", f"{prefix} arrayが必要")
    for offset, record in enumerate(values):
        raw = extract_index_work_id(index, record)
        records.append(
            {
                "raw_index_work_id": raw,
                "index_work_id": canonicalize_index_work_id(index, raw),
                "field_locator": f"{prefix}/{offset}/{suffix}",
            }
        )
    return records


def extract_index_work_ids(index: str, entity_body: bytes) -> list[str]:
    """Extract raw locator values for compatibility; use records for canonical IDs."""

    if index == "arxiv":
        try:
            root = ET.fromstring(entity_body)
        except ET.ParseError as exc:
            raise ContractError("response_xml", "arXiv entity bodyがXMLでない") from exc
        if root.tag != f"{{{ATOM_NS}}}feed":
            raise ContractError("index_work_id_missing", "Atom namespace付きfeedが必要")
        entries = root.findall(f"{{{ATOM_NS}}}entry")
        values: list[str] = []
        for entry in entries:
            values.append(extract_index_work_id("arxiv", entry))
        return values
    value = _decode_json_object(entity_body)
    if index == "openalex":
        results = value.get("results")
        if not isinstance(results, list):
            raise ContractError("index_work_id_missing", "/results arrayが必要")
        values = []
        for record in results:
            values.append(extract_index_work_id("openalex", record))
        return values
    if index == "dblp":
        try:
            hits = value["result"]["hits"]["hit"]
        except (KeyError, TypeError) as exc:
            raise ContractError(
                "index_work_id_missing", "/result/hits/hit arrayが必要"
            ) from exc
        if not isinstance(hits, list):
            raise ContractError("index_work_id_missing", "/result/hits/hit arrayが必要")
        values = []
        for hit in hits:
            values.append(extract_index_work_id("dblp", hit))
        return values
    raise ContractError("index_unknown", f"未知の索引: {index}")


def extract_index_work_id(index: str, record: Any) -> str:
    """Per-record counterpart of :func:`extract_index_work_ids`."""

    if index == "arxiv":
        if not isinstance(record, ET.Element) or record.tag != f"{{{ATOM_NS}}}entry":
            raise ContractError("index_work_id_missing", "Atom namespace付きentryが必要")
        element = record.find(f"{{{ATOM_NS}}}id")
        value = element.text if element is not None and element.text else ""
    elif index == "openalex":
        value = record.get("id") if isinstance(record, Mapping) else ""
    elif index == "dblp":
        try:
            value = record["info"]["key"]
        except (KeyError, TypeError):
            value = ""
    else:
        raise ContractError("index_unknown", f"未知の索引: {index}")
    if not isinstance(value, str) or not value.strip():
        locators = {
            "arxiv": "Atom namespace付きentry/id",
            "openalex": "/results/*/id",
            "dblp": "/result/hits/hit/*/info/key",
        }
        raise ContractError(
            "index_work_id_missing", f"{locators[index]}が非空でない"
        )
    return value if index == "arxiv" else value.strip()


def validate_dblp_record_years(
    entity_body: bytes,
    cutoff_year: int = 2026,
    locator_template: str = "/result/hits/hit/{index}/info/year",
) -> list[dict[str, Any]]:
    if locator_template != "/result/hits/hit/{index}/info/year":
        raise ContractError("dblp_year_locator", "sealed DBLP year locatorが不正")
    value = _decode_json_object(entity_body)
    try:
        hits = value["result"]["hits"]["hit"]
    except (KeyError, TypeError) as exc:
        raise ContractError("dblp_year_missing", "/result/hits/hit arrayが必要") from exc
    if not isinstance(hits, list):
        raise ContractError("dblp_year_missing", "/result/hits/hit arrayが必要")
    years = []
    for offset, hit in enumerate(hits):
        try:
            raw_year = hit["info"]["year"]
        except (KeyError, TypeError) as exc:
            raise ContractError(
                "dblp_year_missing",
                f"/result/hits/hit/{offset}/info/yearが必要",
            ) from exc
        if isinstance(raw_year, bool) or not isinstance(raw_year, (str, int)):
            raise ContractError("dblp_year_invalid", "DBLP yearは4桁文字列または整数が必要")
        raw_text = str(raw_year)
        if not re.fullmatch(r"[0-9]{4}", raw_text):
            raise ContractError("dblp_year_invalid", "DBLP yearは4桁が必要")
        year = int(raw_text)
        if year > cutoff_year:
            raise ContractError("dblp_cutoff_exceeded", f"DBLP record year {year}がcutoff外")
        years.append(
            {
                "raw_year": raw_year,
                "year": year,
                "field_locator": locator_template.replace("{index}", str(offset)),
            }
        )
    return years


def evaluate_openalex_completion(pages: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not pages:
        raise ContractError("completion_empty", "pageが1件以上必要")
    raw_occurrences: list[str] = []
    canonical_occurrences: list[str] = []
    work_id_records: list[dict[str, str]] = []
    records: list[Mapping[str, Any]] = []
    declared: list[int] = []
    last_cursor: Any = object()
    for page in pages:
        body = page.get("entity_body")
        if not isinstance(body, bytes):
            raise ContractError("completion_body", "entity_body bytesが必要")
        value = _decode_json_object(body)
        meta = value.get("meta")
        results = value.get("results")
        if (
            not isinstance(meta, Mapping)
            or not isinstance(meta.get("count"), int)
            or isinstance(meta.get("count"), bool)
            or meta["count"] < 0
        ):
            raise ContractError("completion_declared_total", "/meta/count整数が必要")
        if not isinstance(results, list):
            raise ContractError("completion_records", "/results arrayが必要")
        page_records = extract_index_work_records("openalex", body)
        raw_occurrences.extend(record["raw_index_work_id"] for record in page_records)
        canonical_occurrences.extend(record["index_work_id"] for record in page_records)
        work_id_records.extend(page_records)
        records.extend(copy.deepcopy(results))
        declared.append(meta["count"])
        last_cursor = meta.get("next_cursor")
    distinct_ids = sorted(set(canonical_occurrences))
    canonical_duplicates = sorted(
        value for value, count in Counter(canonical_occurrences).items() if count > 1
    )
    raw_duplicates = sorted(
        value for value, count in Counter(raw_occurrences).items() if count > 1
    )
    declared_stable = len(set(declared)) == 1
    declared_total = declared[0] if declared_stable else None
    cursor_exhausted = last_cursor is None
    complete = (
        declared_stable
        and cursor_exhausted
        and len(distinct_ids) == declared_total
    )
    return {
        "complete": complete,
        "declared_total": declared_total,
        "record_occurrence_count": len(records),
        "records": records,
        "index_work_id_occurrences": raw_occurrences,
        "canonical_index_work_id_occurrences": canonical_occurrences,
        "index_work_id_records": work_id_records,
        "distinct_index_work_ids": distinct_ids,
        "distinct_index_work_id_count": len(distinct_ids),
        "duplicate_index_work_ids": raw_duplicates,
        "duplicate_canonical_index_work_ids": canonical_duplicates,
        "cursor_exhausted": cursor_exhausted,
        "reason": "complete" if complete else "openalex_index_work_id_completion_failed",
    }


def evaluate_completion(
    stream_or_index: str | Mapping[str, Any], pages: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    index = (
        stream_or_index
        if isinstance(stream_or_index, str)
        else stream_or_index.get("index")
    )
    if index == "openalex":
        return evaluate_openalex_completion(pages)
    raw_occurrences: list[str] = []
    canonical_occurrences: list[str] = []
    work_id_records: list[dict[str, str]] = []
    declared: list[int] = []
    terminal = False
    for page in pages:
        body = page.get("entity_body")
        if not isinstance(body, bytes):
            raise ContractError("completion_body", "entity_body bytesが必要")
        page_records = extract_index_work_records(str(index), body)
        raw_occurrences.extend(record["raw_index_work_id"] for record in page_records)
        canonical_occurrences.extend(record["index_work_id"] for record in page_records)
        work_id_records.extend(page_records)
        total = page.get("declared_total")
        if not isinstance(total, int) or total < 0:
            raise ContractError("completion_declared_total", "declared_totalが必要")
        declared.append(total)
        terminal = page.get("terminal") is True
    canonical_duplicates = sorted(
        value for value, count in Counter(canonical_occurrences).items() if count > 1
    )
    raw_duplicates = sorted(
        value for value, count in Counter(raw_occurrences).items() if count > 1
    )
    distinct_ids = sorted(set(canonical_occurrences))
    stable = len(set(declared)) == 1
    declared_total = declared[0] if stable else None
    complete = (
        stable and terminal and not canonical_duplicates and len(distinct_ids) == declared_total
    )
    return {
        "complete": complete,
        "declared_total": declared_total,
        "index_work_id_occurrences": raw_occurrences,
        "canonical_index_work_id_occurrences": canonical_occurrences,
        "index_work_id_records": work_id_records,
        "distinct_index_work_ids": distinct_ids,
        "distinct_index_work_id_count": len(distinct_ids),
        "duplicate_index_work_ids": raw_duplicates,
        "duplicate_canonical_index_work_ids": canonical_duplicates,
        "terminal": terminal,
    }


@dataclass(frozen=True)
class TransportResponse:
    status: int
    entity_body: bytes
    headers: tuple[tuple[str, str], ...]
    endpoint: str
    final_url: str
    content_type: str
    response_received_at: str | None = None

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, Any], *, strict_transport_boundary: bool = False
    ) -> "TransportResponse":
        if "entity_body" not in value:
            raise ContractError("transport_response", "client露出entity_bodyが必要")
        body = value["entity_body"]
        if isinstance(body, str) and not strict_transport_boundary:
            body = body.encode("utf-8")
        if not isinstance(body, bytes):
            raise ContractError(
                "transport_response",
                "entity_bodyはclientが露出したbytesが必要",
            )
        headers_value = value.get("headers")
        if not isinstance(headers_value, Sequence) or isinstance(headers_value, (str, bytes)):
            raise ContractError("transport_response", "観済headersはpair arrayが必要")
        headers: list[tuple[str, str]] = []
        for item in headers_value:
            if not isinstance(item, Sequence) or isinstance(item, (str, bytes)) or len(item) != 2:
                raise ContractError("transport_response", "headerは[name,value]が必要")
            if not isinstance(item[0], str) or not isinstance(item[1], str):
                raise ContractError("transport_response", "header name/valueはstringが必要")
            headers.append((item[0], item[1]))
        status = value.get("status")
        if not isinstance(status, int) or isinstance(status, bool):
            raise ContractError("transport_response", "観済HTTP status整数が必要")
        envelope = {
            name: value.get(name)
            for name in ("endpoint", "final_url", "content_type")
        }
        if any(not isinstance(item, str) or not item for item in envelope.values()):
            raise ContractError(
                "transport_response",
                "観済endpoint、final_url、content_typeの非空文字列が必要",
            )
        return cls(
            status=status,
            entity_body=body,
            headers=tuple(headers),
            endpoint=envelope["endpoint"],
            final_url=envelope["final_url"],
            content_type=envelope["content_type"],
            response_received_at=(
                str(value["response_received_at"])
                if value.get("response_received_at") is not None
                else None
            ),
        )


_CANONICAL_HTTPS_CONNECTION = http.client.HTTPSConnection
_PRODUCTION_TRANSPORT_MARKER = "axis3-live-http-transport/v1"
_SEND_RECEIPT_VERSION = "axis3-search-send-receipt/v1"


class LiveHTTPTransport:
    """One-call/one-attempt HTTPS transport with redirects and retries disabled."""

    _axis3_artifact_class = "production"
    __slots__ = ("timeout_seconds", "calls")

    def __init__(self, *, timeout_seconds: float = 30.0):
        if timeout_seconds <= 0:
            raise ContractError("live_transport", "timeoutは正数が必要")
        self.timeout_seconds = timeout_seconds
        self.calls: list[Mapping[str, Any]] = []

    def send(self, request: Mapping[str, Any]) -> TransportResponse:
        _validate_production_transport_identity(self)
        if request.get("method") != "GET" or request.get("body_sha256") != EMPTY_SHA256:
            raise ContractError("live_transport", "Axis 3 live transportはbody無しGETだけ")
        url = request.get("url")
        if not isinstance(url, str):
            raise ContractError("live_transport", "request URLが必要")
        parsed = urlsplit(url)
        allowed_targets = {
            (urlsplit(endpoint).hostname, urlsplit(endpoint).path)
            for endpoint in (ARXIV_ENDPOINT, OPENALEX_ENDPOINT, DBLP_ENDPOINT)
        }
        if (
            parsed.scheme != "https"
            or (parsed.hostname, parsed.path) not in allowed_targets
            or parsed.username
            or parsed.password
            or parsed.port is not None
            or parsed.fragment
        ):
            raise ContractError(
                "live_transport",
                "登録3索引のcredential/port/fragment無しHTTPS URLだけを許す",
            )
        headers_value = request.get("headers")
        if not isinstance(headers_value, list):
            raise ContractError("live_transport", "string header pair arrayが必要")
        headers: dict[str, str] = {}
        header_names: set[str] = set()
        for pair in headers_value:
            if (
                not isinstance(pair, list)
                or len(pair) != 2
                or not all(isinstance(value, str) for value in pair)
            ):
                raise ContractError("live_transport", "string header pairだけを許す")
            normalized_name = pair[0].lower()
            if (
                normalized_name in header_names
                or not pair[0]
                or "\r" in pair[0]
                or "\n" in pair[0]
                or "\r" in pair[1]
                or "\n" in pair[1]
            ):
                raise ContractError("live_transport", "outgoing duplicate headerを許さない")
            header_names.add(normalized_name)
            headers[pair[0]] = pair[1]
        target = parsed.path or "/"
        if parsed.query:
            target += "?" + parsed.query
        self.calls.append(copy.deepcopy(dict(request)))
        connection = None
        try:
            connection = _CANONICAL_HTTPS_CONNECTION(
                parsed.hostname,
                port=parsed.port,
                timeout=self.timeout_seconds,
            )
            connection.request("GET", target, headers=headers)
            response = connection.getresponse()
            body = response.read()
            observed_headers = tuple((name, value) for name, value in response.getheaders())
        except (OSError, http.client.HTTPException) as exc:
            raise ContractError("live_transport", "単一HTTPS attemptが失敗") from exc
        finally:
            if connection is not None:
                connection.close()
        content_type = next(
            (value for name, value in observed_headers if name.lower() == "content-type"),
            "application/octet-stream",
        )
        return TransportResponse.from_mapping(
            {
                "status": response.status,
                "entity_body": body,
                "headers": observed_headers,
                "endpoint": f"https://{parsed.netloc}{parsed.path or '/'}",
                "final_url": url,
                "content_type": content_type,
            },
            strict_transport_boundary=True,
        )


_CANONICAL_LIVE_TRANSPORT_CLASS = LiveHTTPTransport
_CANONICAL_LIVE_SEND = LiveHTTPTransport.send


def _validate_production_transport_identity(transport: Any) -> None:
    if (
        LiveHTTPTransport is not _CANONICAL_LIVE_TRANSPORT_CLASS
        or type(transport) is not _CANONICAL_LIVE_TRANSPORT_CLASS
        or type(transport).send is not _CANONICAL_LIVE_SEND
        or http.client.HTTPSConnection is not _CANONICAL_HTTPS_CONNECTION
        or getattr(transport, "_axis3_artifact_class", None) != "production"
    ):
        raise ContractError(
            "production_transport_identity",
            "production transportのcanonical class/constructor/send identityが不一致",
        )


class NonProductionHTTPTransport:
    """Injectable HTTPS test transport; artifacts are always nonproduction."""

    _axis3_artifact_class = "nonproduction_simulation"
    __slots__ = ("timeout_seconds", "_connection_factory", "calls")

    def __init__(
        self,
        *,
        connection_factory: Callable[..., Any],
        timeout_seconds: float = 30.0,
    ):
        if timeout_seconds <= 0 or not callable(connection_factory):
            raise ContractError("test_transport", "test transport引数が不正")
        self.timeout_seconds = timeout_seconds
        self._connection_factory = connection_factory
        self.calls: list[Mapping[str, Any]] = []

    def send(self, request: Mapping[str, Any]) -> TransportResponse:
        if request.get("method") != "GET" or request.get("body_sha256") != EMPTY_SHA256:
            raise ContractError("test_transport", "test transportはbody無しGETだけ")
        url = request.get("url")
        if not isinstance(url, str):
            raise ContractError("test_transport", "request URLが必要")
        parsed = urlsplit(url)
        headers = {str(name): str(value) for name, value in request.get("headers", [])}
        target = parsed.path or "/"
        if parsed.query:
            target += "?" + parsed.query
        self.calls.append(copy.deepcopy(dict(request)))
        connection = self._connection_factory(
            parsed.hostname,
            port=parsed.port,
            timeout=self.timeout_seconds,
        )
        try:
            connection.request("GET", target, headers=headers)
            response = connection.getresponse()
            body = response.read()
            observed_headers = tuple(response.getheaders())
        finally:
            connection.close()
        content_type = next(
            (value for name, value in observed_headers if name.lower() == "content-type"),
            "application/octet-stream",
        )
        return TransportResponse.from_mapping(
            {
                "status": response.status,
                "entity_body": body,
                "headers": observed_headers,
                "endpoint": f"https://{parsed.netloc}{parsed.path or '/'}",
                "final_url": url,
                "content_type": content_type,
            },
            strict_transport_boundary=True,
        )


def _transport_response_sha256(response: TransportResponse) -> str:
    return _sha256(
        _canonical_json(
            {
                "status": response.status,
                "entity_body_sha256": _sha256(response.entity_body),
                "headers": [list(item) for item in response.headers],
                "endpoint": response.endpoint,
                "final_url": response.final_url,
                "content_type": response.content_type,
            }
        )
    )


@dataclass(frozen=True)
class _SendReceipt:
    session_id: str
    receipt_id: str
    ordinal: int
    request_sha256: str
    response_sha256: str


_LIVE_SESSION_SENTINEL = object()


class LiveSearchSession:
    """Canonical production facade owning transport, receipts, and writers."""

    _axis3_artifact_class = "production"
    __slots__ = ("_transport", "_session_id", "_issued")

    def __init__(self, *, timeout_seconds: float = 30.0, _sentinel: object = None):
        if _sentinel is not _LIVE_SESSION_SENTINEL:
            raise ContractError(
                "production_session",
                "production live sessionはcanonical CLI factory専用",
            )
        self._transport = LiveHTTPTransport(timeout_seconds=timeout_seconds)
        _validate_production_transport_identity(self._transport)
        self._session_id = _sha256(os.urandom(32))
        self._issued: dict[str, _SendReceipt] = {}

    @property
    def calls(self) -> list[Mapping[str, Any]]:
        return self._transport.calls

    @property
    def timeout_seconds(self) -> float:
        return self._transport.timeout_seconds

    def _send_with_receipt(
        self, request: Mapping[str, Any], ordinal: int
    ) -> tuple[TransportResponse, _SendReceipt]:
        if type(self) is not LiveSearchSession:
            raise ContractError("production_transport_identity", "live session subclassを拒否")
        _validate_production_transport_identity(self._transport)
        response = self._transport.send(request)
        receipt = _SendReceipt(
            session_id=self._session_id,
            receipt_id=_sha256(os.urandom(32)),
            ordinal=ordinal,
            request_sha256=_sha256(_canonical_json(request)),
            response_sha256=_transport_response_sha256(response),
        )
        self._issued[receipt.receipt_id] = receipt
        return response, receipt

    def _consume_receipt(
        self,
        receipt: _SendReceipt,
        *,
        request: Mapping[str, Any],
        response: TransportResponse,
        ordinal: int,
    ) -> dict[str, Any]:
        if type(receipt) is not _SendReceipt:
            raise ContractError("send_receipt", "canonical send receiptが必要")
        issued = self._issued.pop(receipt.receipt_id, None)
        if issued != receipt:
            raise ContractError("send_receipt_consumed", "send receiptが未発行または消費済み")
        if (
            receipt.session_id != self._session_id
            or receipt.ordinal != ordinal
            or receipt.request_sha256 != _sha256(_canonical_json(request))
            or receipt.response_sha256 != _transport_response_sha256(response)
        ):
            raise ContractError("send_receipt_identity", "send receipt identityがresponseと不一致")
        return {
            "schema_version": _SEND_RECEIPT_VERSION,
            "session_id": receipt.session_id,
            "receipt_id": receipt.receipt_id,
            "ordinal": receipt.ordinal,
            "request_sha256": receipt.request_sha256,
            "response_sha256": receipt.response_sha256,
            "transport_marker": _PRODUCTION_TRANSPORT_MARKER,
        }

    def _open_writer(self, *args: Any, **kwargs: Any) -> "BundleWriter":
        kwargs["_production_session"] = self
        return BundleWriter(*args, **kwargs)


def create_live_search_session(*, timeout_seconds: float = 30.0) -> LiveSearchSession:
    return LiveSearchSession(
        timeout_seconds=timeout_seconds,
        _sentinel=_LIVE_SESSION_SENTINEL,
    )


def _normalize_interpreted_query_text(value: str) -> str:
    return " ".join(unquote_plus(value).split())


def _normalize_arxiv_interpreted_query(value: str) -> str:
    normalized = _normalize_interpreted_query_text(value)
    return re.sub(
        r'submittedDate:(?:\[|")([0-9]{12}) TO ([0-9]{12})(?:\]|")',
        r"submittedDate:{\1 TO \2}",
        normalized,
    )


def _validate_arxiv_interpreted_query(
    expected: str, entity_body: bytes
) -> None:
    try:
        root = ET.fromstring(entity_body)
    except ET.ParseError as exc:
        raise ContractError("response_xml", "arXiv entity bodyがXMLでない") from exc
    title = root.find(f"{{{ATOM_NS}}}title")
    raw = title.text if title is not None else None
    if not isinstance(raw, str):
        raise ContractError(
            "interpreted_query_missing", "arXiv /atom:feed/atom:titleが必要"
        )
    match = re.fullmatch(
        r"arXiv Query: search_query=(.*)&id_list=&start=[0-9]+&max_results=[0-9]+",
        _normalize_interpreted_query_text(raw),
    )
    if match is None or _normalize_arxiv_interpreted_query(
        match.group(1)
    ) != _normalize_arxiv_interpreted_query(expected):
        raise ContractError(
            "interpreted_query_mismatch", "arXiv interpreted queryが登録値と不一致"
        )


def _validate_dblp_interpreted_query(
    expected: str, value: Mapping[str, Any]
) -> None:
    try:
        raw = value["result"]["query"]
    except (KeyError, TypeError) as exc:
        raise ContractError(
            "interpreted_query_missing", "DBLP /result/queryが必要"
        ) from exc
    if not isinstance(raw, str) or _normalize_interpreted_query_text(
        raw
    ) != _normalize_interpreted_query_text(expected):
        raise ContractError(
            "interpreted_query_mismatch", "DBLP interpreted queryが登録値と不一致"
        )


def observed_response_locators(index: str, entity_body: bytes, status: int) -> list[str]:
    locators: list[str] = []
    if index == "arxiv":
        try:
            root = ET.fromstring(entity_body)
        except ET.ParseError:
            return []
        if root.tag != f"{{{ATOM_NS}}}feed":
            return []
        if root.find(f"{{{ATOM_NS}}}title") is not None:
            locators.append("/atom:feed/atom:title")
        for name in ("totalResults", "startIndex", "itemsPerPage"):
            if root.find(f"{{{OPENSEARCH_NS}}}{name}") is not None:
                locators.append(f"/atom:feed/opensearch:{name}")
        for offset, entry in enumerate(root.findall(f"{{{ATOM_NS}}}entry")):
            if entry.find(f"{{{ATOM_NS}}}id") is not None:
                locators.append(f"/atom:feed/atom:entry/{offset}/atom:id")
        return locators
    try:
        value = _decode_json_object(entity_body)
    except ContractError:
        return []
    if index == "openalex":
        meta = value.get("meta")
        results = value.get("results")
        if isinstance(meta, Mapping):
            for name in ("count", "next_cursor", "per_page"):
                if name in meta:
                    locators.append(f"/meta/{name}")
            x_query = meta.get("x_query")
            if isinstance(x_query, Mapping) and "oql" in x_query:
                locators.append("/meta/x_query/oql")
        if isinstance(results, list):
            locators.append("/results")
            for offset, record in enumerate(results):
                if isinstance(record, Mapping) and "id" in record:
                    locators.append(f"/results/{offset}/id")
        return locators
    if index == "dblp":
        result = value.get("result")
        if isinstance(result, Mapping) and "query" in result:
            locators.append("/result/query")
        hits = result.get("hits") if isinstance(result, Mapping) else None
        if not isinstance(hits, Mapping):
            return locators
        for name in ("@total", "@first", "@sent"):
            if name in hits:
                locators.append(f"/result/hits/{name}")
        records = hits.get("hit")
        if isinstance(records, list):
            locators.append("/result/hits/hit")
            for offset, record in enumerate(records):
                info = record.get("info") if isinstance(record, Mapping) else None
                if isinstance(info, Mapping) and "key" in info:
                    locators.append(f"/result/hits/hit/{offset}/info/key")
                if isinstance(info, Mapping) and "year" in info:
                    locators.append(f"/result/hits/hit/{offset}/info/year")
        return locators
    raise ContractError("index_unknown", f"未知の索引: {index}")


def capture_page_evidence(
    *,
    stream_id: str,
    pass_number: int,
    page_number: int,
    request: Mapping[str, Any],
    response: TransportResponse,
    required_response_fields: Sequence[str],
) -> dict[str, Any]:
    if response.response_received_at is None:
        raise ContractError(
            "response_received_time", "page evidenceには応答受領時刻が必要"
        )
    _parse_time(response.response_received_at)
    evidence = {
        "schema_version": PAGE_EVIDENCE_VERSION,
        "stream_id": stream_id,
        "pass_number": pass_number,
        "page_number": page_number,
        "request": copy.deepcopy(dict(request)),
        "status": response.status,
        "final_url": response.final_url,
        "content_type": response.content_type,
        "response_received_at": response.response_received_at,
        "entity_body_byte_count": len(response.entity_body),
        "body_capture_kind": "http_client_exposed_entity_body_before_parser",
        "alternative_provenance": {
            "endpoint": response.endpoint,
            "required_response_fields": list(required_response_fields),
            "observed_response_fields": observed_response_locators(
                str(request["index"]), response.entity_body, response.status
            ),
            "observed_response_headers": [
                {"name": name, "value": value} for name, value in response.headers
            ],
            "entity_body_sha256": _sha256(response.entity_body),
            "digest_scope": "http_client_exposed_entity_body_bytes_before_parser",
        },
    }
    validate_page_evidence(evidence, response.entity_body)
    return evidence


def validate_page_evidence(evidence: Mapping[str, Any], entity_body: bytes) -> None:
    _validate_with_schema(evidence, SCHEMA_PATHS[2])
    _parse_time(str(evidence["response_received_at"]))
    if evidence["body_capture_kind"] != "http_client_exposed_entity_body_before_parser":
        raise ContractError(
            "evidence_scope",
            "HTTP clientが露出したentity bodyを越える捕捉scopeを許さない",
        )
    if evidence["entity_body_byte_count"] != len(entity_body):
        raise ContractError("evidence_body_size", "entity body byte countが不一致")
    if evidence["alternative_provenance"]["entity_body_sha256"] != _sha256(entity_body):
        raise ContractError("evidence_body_digest", "保存済みentity bodyのdigestが不一致")
    request = evidence["request"]
    if request["stream_id"] != evidence["stream_id"]:
        raise ContractError("evidence_identity", "evidenceとrequestのstream IDが不一致")
    expected_observed = observed_response_locators(
        request["index"], entity_body, evidence["status"]
    )
    if evidence["alternative_provenance"]["observed_response_fields"] != expected_observed:
        raise ContractError("evidence_locator", "field locatorが実entity bodyと不一致")
    requested = urlsplit(request["url"])
    endpoint = urlsplit(evidence["alternative_provenance"]["endpoint"])
    requested_origin = (requested.scheme.lower(), requested.hostname, requested.port, requested.path)
    endpoint_origin = (endpoint.scheme.lower(), endpoint.hostname, endpoint.port, endpoint.path)
    if endpoint_origin != requested_origin:
        raise ContractError(
            "evidence_endpoint",
            "観済endpointはrequestのscheme、host、pathと一致が必要",
        )
    if _canonical_url(evidence["final_url"]) != _canonical_url(request["url"]):
        raise ContractError("evidence_final_url", "final URL canonical queryがrequestと不一致")


def _relative_label(path: Path, repo_root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise ContractError("seal_path", f"seal対象がrepo外: {path}") from exc


def _digest_entries(paths: Sequence[Path], repo_root: Path) -> list[dict[str, str]]:
    entries = []
    for path in paths:
        path = Path(path)
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise ContractError("seal_path", f"seal対象を読めない: {path}") from exc
        entries.append({"path": _relative_label(path, repo_root), "sha256": _sha256(data)})
    return sorted(entries, key=lambda entry: entry["path"])


def _frozen_input_digest_entries(
    paths: Sequence[Path], repo_root: Path
) -> list[dict[str, str]]:
    entries = []
    preregistration_label = (
        "docs/related-work/claim-survey/"
        "2026-08-27-axis3-search-preregistration.md"
    )
    amendment_label = (
        "docs/related-work/claim-survey/"
        "2026-09-01-axis3-search-amendment.md"
    )
    for path in paths:
        path = Path(path)
        label = _relative_label(path, repo_root)
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise ContractError("seal_path", f"凍結入力を読めない: {path}") from exc
        digest = _sha256(data)
        if label == preregistration_label and digest != FROZEN_PREREGISTRATION_SHA256:
            raise ContractError(
                "frozen_input_stale",
                "旧凍結登録bytesが独立literal digestと不一致",
            )
        if label == amendment_label:
            _validate_frozen_amendment_bytes(data)
        entries.append({"path": label, "sha256": digest})
    return sorted(entries, key=lambda entry: entry["path"])


def _validate_frozen_amendment_bytes(data: bytes) -> None:
    """Compare the actual frozen amendment bytes with the independent literal."""

    if _sha256(data) != FROZEN_AMENDMENT_SHA256:
        raise ContractError(
            "frozen_input_stale", "amendment bytesが凍結digestと不一致"
        )


def _head_blob_bytes(repo_root: Path, label: str) -> bytes:
    try:
        completed = subprocess.run(
            ["git", "show", f"HEAD:{label}"],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ContractError("head_closure", f"HEAD:{label} bytesを解決できない") from exc
    return completed.stdout


def _verify_head_closure(paths: Sequence[Path], repo_root: Path) -> None:
    for path in paths:
        candidate = Path(path)
        label = _relative_label(candidate, repo_root)
        try:
            worktree_bytes = candidate.read_bytes()
        except OSError as exc:
            raise ContractError("head_closure", f"closure fileを読めない: {label}") from exc
        if worktree_bytes != _head_blob_bytes(repo_root, label):
            raise ContractError(
                "head_closure_dirty",
                f"closure fileがHEAD:{label} bytesと不一致",
            )


_STDLIB_RUNTIME_MODULES = (
    "base64", "copy", "csv", "fcntl", "hashlib", "http.client", "importlib",
    "importlib.metadata", "json", "os", "re", "subprocess", "struct", "tempfile",
    "time", "xml.etree.ElementTree", "collections", "dataclasses", "datetime", "functools",
    "pathlib", "typing", "urllib.parse",
)
_SITE_RUNTIME_DISTRIBUTIONS = (
    "attrs", "jsonschema", "pyrsistent", "six",
)


def _aggregate_runtime_entry(label: str, values: Sequence[Mapping[str, str]]) -> dict[str, str]:
    if not values:
        raise ContractError("package_closure", f"runtime closure categoryが空: {label}")
    return {"path": label, "sha256": _sha256(_canonical_json(list(values)))}


def _runtime_file_entry(label: str, path: Path) -> dict[str, str]:
    resolved = Path(path).resolve()
    if not resolved.is_file():
        raise ContractError("package_closure", f"runtime closureが非file: {label}")
    try:
        data = resolved.read_bytes()
    except OSError as exc:
        raise ContractError("package_closure", f"runtime fileを読めない: {label}") from exc
    return {"path": label, "sha256": _sha256(data)}


def _loaded_stdlib_runtime_material(
    repo_root: Path = REPO_ROOT,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Bind every file-backed stdlib module loaded at the closure boundary."""

    global _RUNTIME_IMPORT_MODULE_NAMES
    if _RUNTIME_IMPORT_MODULE_NAMES is None:
        _RUNTIME_IMPORT_MODULE_NAMES = tuple(sorted(sys.modules))
    module_names = sorted(
        set(_RUNTIME_IMPORT_MODULE_NAMES) | set(_STDLIB_RUNTIME_MODULES)
    )
    entries: list[dict[str, str]] = []
    nonfile_identities: list[dict[str, Any]] = []
    for module_name in module_names:
        module = sys.modules.get(module_name)
        if module is None:
            raise ContractError(
                "package_closure", f"runtime moduleが未読: {module_name}"
            )
        module_path_value = getattr(module, "__file__", None)
        spec = getattr(module, "__spec__", None)
        origin = getattr(spec, "origin", None)
        if not isinstance(module_path_value, str):
            locations_value = getattr(spec, "submodule_search_locations", None)
            locations: list[str] = []
            if locations_value is not None:
                for location in locations_value:
                    resolved_location = Path(location).resolve()
                    if not resolved_location.is_dir():
                        raise ContractError(
                            "package_closure",
                            f"runtime namespace locationがdirectoryでない: {module_name}",
                        )
                    locations.append(str(resolved_location))
            nonfile_identities.append(
                {
                    "module": module_name,
                    "origin": origin if isinstance(origin, str) else None,
                    "loader": type(getattr(spec, "loader", None)).__name__,
                    "namespace_locations": sorted(locations),
                }
            )
            continue
        if module_path_value.startswith("<") and module_path_value.endswith(">"):
            nonfile_identities.append(
                {
                    "module": module_name,
                    "origin": module_path_value,
                    "loader": type(getattr(spec, "loader", None)).__name__,
                    "namespace_locations": [],
                }
            )
            continue
        resolved = Path(module_path_value).resolve()
        if not resolved.is_file():
            raise ContractError(
                "package_closure", f"runtime moduleが非file: {module_name}"
            )
        if "site-packages" in resolved.parts or "dist-packages" in resolved.parts:
            # Site material is closed by distribution metadata and its complete
            # RECORD/package tree below, not by an ambient absolute path.
            continue
        try:
            resolved.relative_to(Path(repo_root).resolve())
        except ValueError:
            entries.append(_runtime_file_entry(f"stdlib:{module_name}", resolved))
    if not entries:
        raise ContractError("package_closure", "loaded stdlib file closureが空")
    return entries, {
        "modules": nonfile_identities,
        "implementation": sys.implementation.name,
        "version": list(sys.version_info[:3]),
    }


def _distribution_runtime_material(
    distribution_name: str,
) -> tuple[dict[str, str], list[dict[str, str]], list[dict[str, str]]]:
    try:
        distribution = importlib.metadata.distribution(distribution_name)
    except importlib.metadata.PackageNotFoundError as exc:
        raise ContractError("package_closure", f"distributionが無い: {distribution_name}") from exc
    record_text = distribution.read_text("RECORD")
    tree_paths: list[tuple[str, Path]] = []
    closure_kind: str
    if isinstance(record_text, str) and record_text:
        record_rows = list(csv.reader(record_text.splitlines()))
        if not record_rows or any(len(row) != 3 or not row[0] for row in record_rows):
            raise ContractError("package_closure", f"distribution RECORDが不正: {distribution_name}")
        tree_paths = [
            (row[0], Path(distribution.locate_file(row[0])))
            for row in sorted(record_rows, key=lambda row: row[0])
        ]
        closure_kind = "record"
    else:
        top_level_text = distribution.read_text("top_level.txt")
        roots = (
            sorted({line.strip() for line in top_level_text.splitlines() if line.strip()})
            if isinstance(top_level_text, str)
            else []
        )
        if not roots:
            raise ContractError(
                "package_closure",
                f"distributionにRECORDもtop_level package treeも無い: {distribution_name}",
            )
        for root_name in roots:
            candidate = Path(distribution.locate_file(root_name))
            if candidate.is_file():
                tree_paths.append((root_name, candidate))
            elif candidate.is_dir():
                for child in sorted(candidate.rglob("*"), key=lambda item: item.as_posix()):
                    if (
                        child.is_file()
                        and "__pycache__" not in child.parts
                        and child.suffix not in {".pyc", ".pyo"}
                    ):
                        tree_paths.append(
                            (f"{root_name}/{child.relative_to(candidate).as_posix()}", child)
                        )
            else:
                py_candidate = Path(distribution.locate_file(root_name + ".py"))
                loaded_root = sys.modules.get(root_name)
                loaded_root_file = getattr(loaded_root, "__file__", None)
                fallback = (
                    Path(loaded_root_file)
                    if isinstance(loaded_root_file, str)
                    else py_candidate
                )
                if py_candidate.is_file():
                    fallback = py_candidate
                if not fallback.is_file():
                    raise ContractError(
                        "package_closure", f"package tree rootが非file: {distribution_name}:{root_name}"
                    )
                tree_paths.append((fallback.name, fallback))
        closure_kind = "package_tree"
    tree_entries = [
        _runtime_file_entry(f"{distribution_name}:{label}", path)
        for label, path in tree_paths
    ]
    metadata_root = Path(getattr(distribution, "_path", ""))
    if not metadata_root.is_dir():
        raise ContractError("package_closure", f"distribution metadata dirが無い: {distribution_name}")
    metadata_entries = [
        _runtime_file_entry(
            f"{distribution_name}:metadata:{child.relative_to(metadata_root).as_posix()}",
            child,
        )
        for child in sorted(metadata_root.rglob("*"), key=lambda item: item.as_posix())
        if child.is_file()
    ]

    canonical_distribution = re.sub(r"[-_.]+", "-", distribution_name).lower()
    package_owners = importlib.metadata.packages_distributions()
    loaded_entries: list[dict[str, str]] = []
    for module_name, module in sorted(sys.modules.items()):
        owners = {
            re.sub(r"[-_.]+", "-", owner).lower()
            for owner in package_owners.get(module_name.split(".", 1)[0], [])
        }
        if canonical_distribution not in owners:
            continue
        module_path_value = getattr(module, "__file__", None)
        if not isinstance(module_path_value, str):
            raise ContractError("package_closure", f"loaded moduleがfloating: {module_name}")
        loaded_entries.append(
            _runtime_file_entry(f"loaded:{module_name}", Path(module_path_value))
        )
    if not loaded_entries:
        raise ContractError(
            "package_closure", f"distributionのloaded moduleが無い: {distribution_name}"
        )
    identity = {
        "path": distribution_name,
        "sha256": _sha256(
            _canonical_json(
                {
                    "version": distribution.version,
                    "closure_kind": closure_kind,
                    "metadata": metadata_entries,
                }
            )
        ),
    }
    return identity, loaded_entries, tree_entries


def _runtime_digest_entries(
    repo_root: Path = REPO_ROOT,
    *,
    source_paths: Sequence[Path] = SOURCE_PATHS,
    package_init_path: Path = PACKAGE_INIT_PATH,
) -> list[dict[str, str]]:
    project_paths = [*source_paths]
    if package_init_path.exists():
        project_paths.append(package_init_path)
    project_entries = [
        _runtime_file_entry(_relative_label(path, repo_root), path)
        for path in sorted(project_paths, key=lambda item: item.as_posix())
    ]
    stdlib_entries, nonfile_identity = _loaded_stdlib_runtime_material(repo_root)
    distribution_identities: list[dict[str, str]] = []
    loaded_site_modules: list[dict[str, str]] = []
    distribution_tree: list[dict[str, str]] = []
    for distribution_name in _SITE_RUNTIME_DISTRIBUTIONS:
        identity, loaded, tree = _distribution_runtime_material(distribution_name)
        distribution_identities.append(identity)
        loaded_site_modules.extend(loaded)
        distribution_tree.extend(tree)
    entries = [
        _aggregate_runtime_entry("python-project-source:loaded", project_entries),
        _aggregate_runtime_entry("python-stdlib:loaded", stdlib_entries),
        _runtime_file_entry("python-executable", Path(sys.executable)),
        {
            "path": "python-builtin-identity",
            "sha256": _sha256(_canonical_json(nonfile_identity)),
        },
        _aggregate_runtime_entry(
            "python-site-distribution-metadata", distribution_identities
        ),
        _aggregate_runtime_entry(
            "python-site-loaded-modules",
            sorted(loaded_site_modules, key=lambda item: item["path"]),
        ),
        _aggregate_runtime_entry(
            "python-site-package-tree",
            sorted(distribution_tree, key=lambda item: item["path"]),
        ),
    ]
    return sorted(entries, key=lambda entry: entry["path"])


def build_registration_seal(
    catalog_data: bytes,
    *,
    argv: Sequence[str],
    commit: str,
    repo_root: Path = REPO_ROOT,
    source_paths: Sequence[Path] = SOURCE_PATHS,
    schema_paths: Sequence[Path] = SCHEMA_PATHS,
    frozen_input_paths: Sequence[Path] = FROZEN_INPUT_PATHS,
    enforce_head: bool = True,
    package_init_path: Path | None = None,
    resolved_head_commit: str | None = None,
) -> dict[str, Any]:
    try:
        catalog = json.loads(catalog_data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("catalog_bytes", "catalog bytesがUTF-8 JSONでない") from exc
    validate_catalog(catalog)
    validate_registered_oql_fixtures()
    for schema_path in schema_paths:
        _load_schema(Path(schema_path))
    if not COMMIT_RE.fullmatch(commit):
        raise ContractError("seal_commit", "commitは7〜64桁の小文字hexが必要")
    if not argv or not all(isinstance(value, str) and value for value in argv):
        raise ContractError("seal_argv", "argvは非空文字列arrayが必要")
    actual_head = (
        resolve_head_commit(repo_root)
        if resolved_head_commit is None
        else resolved_head_commit
    )
    if not FULL_COMMIT_RE.fullmatch(actual_head):
        raise ContractError("seal_commit", "resolved HEADはfull SHAが必要")
    expected_sources = {
        "orchestrator/related_work_search.py",
        "tools/run_axis3_search.py",
    }
    actual_sources = {_relative_label(Path(path), repo_root) for path in source_paths}
    if actual_sources != expected_sources:
        raise ContractError("source_closure", "source closureはmoduleとCLIの2ファイルが必要")
    expected_schemas = {
        "orchestrator/schemas/axis3_search_catalog.schema.json",
        "orchestrator/schemas/axis3_search_checkpoint.schema.json",
        "orchestrator/schemas/axis3_search_page_evidence.schema.json",
        "orchestrator/schemas/axis3_search_registration_seal.schema.json",
    }
    actual_schemas = {
        _relative_label(Path(path), repo_root) for path in schema_paths
    }
    if actual_schemas != expected_schemas:
        raise ContractError("schema_closure", "Axis 3 schema closureが4ファイルと不一致")
    expected_frozen = {
        "docs/related-work/claim-survey/2026-08-27-axis3-search-preregistration.md",
        "docs/related-work/claim-survey/2026-09-01-axis3-search-amendment.md",
    }
    actual_frozen = {_relative_label(Path(path), repo_root) for path in frozen_input_paths}
    if actual_frozen != expected_frozen:
        raise ContractError("frozen_input_closure", "旧凍結登録とamendmentの2ファイルが必要")
    try:
        preregistration_data = Path(frozen_input_paths[0]).read_bytes()
    except OSError as exc:
        raise ContractError("seal_path", "旧凍結登録bytesを読めない") from exc
    validate_frozen_registration_closure(catalog, preregistration_data)
    closure_paths = tuple(Path(path) for path in (*source_paths, *schema_paths, *frozen_input_paths))
    if enforce_head:
        _verify_head_closure(closure_paths, repo_root)
    payload = {
        "schema_version": REGISTRATION_SEAL_VERSION,
        "catalog_sha256": _sha256(catalog_data),
        "source_digests": _digest_entries(source_paths, repo_root),
        "schema_digests": _digest_entries(schema_paths, repo_root),
        "fixture_sha256": _sha256(oql_fixture_bytes()),
        "frozen_semantics_sha256": FROZEN_SEMANTICS_SHA256,
        "frozen_input_digests": _frozen_input_digest_entries(frozen_input_paths, repo_root),
        "environment_identity": {
            "jsonschema_distribution_version": importlib.metadata.version("jsonschema"),
            "python_implementation": sys.implementation.name,
            "python_version": ".".join(str(value) for value in sys.version_info[:3]),
        },
        "argv": list(argv),
        "argv_sha256": _sha256(_canonical_json(list(argv))),
        "phase_argv_contracts": copy.deepcopy(dict(PHASE_ARGV_CONTRACTS)),
        "phase_argv_contracts_sha256": _sha256(
            _canonical_json(PHASE_ARGV_CONTRACTS)
        ),
        "commit": commit,
        "resolved_head_commit": actual_head,
        "head_verified": enforce_head,
    }
    payload["closure_sha256"] = _sha256(_canonical_json(payload))
    seal = dict(payload)
    seal["seal_sha256"] = _sha256(_canonical_json(payload))
    _validate_with_schema(seal, SCHEMA_PATHS[3])
    return seal


def validate_registration_seal(
    seal: Mapping[str, Any],
    catalog_data: bytes,
    *,
    argv: Sequence[str],
    commit: str,
    repo_root: Path = REPO_ROOT,
    source_paths: Sequence[Path] = SOURCE_PATHS,
    schema_paths: Sequence[Path] = SCHEMA_PATHS,
    frozen_input_paths: Sequence[Path] = FROZEN_INPUT_PATHS,
    enforce_head: bool = True,
) -> None:
    _validate_with_schema(seal, SCHEMA_PATHS[3])
    sealed_payload = copy.deepcopy(dict(seal))
    sealed_sha256 = sealed_payload.pop("seal_sha256")
    if sealed_sha256 != _sha256(_canonical_json(sealed_payload)):
        raise ContractError(
            "registration_seal_stale", "seal自身のpayload digestが不一致"
        )
    closure_payload = copy.deepcopy(sealed_payload)
    closure_sha256 = closure_payload.pop("closure_sha256")
    if closure_sha256 != _sha256(_canonical_json(closure_payload)):
        raise ContractError(
            "registration_seal_stale", "seal closure digestが不一致"
        )
    expected = build_registration_seal(
        catalog_data,
        argv=argv,
        commit=commit,
        repo_root=repo_root,
        source_paths=source_paths,
        schema_paths=schema_paths,
        frozen_input_paths=frozen_input_paths,
        enforce_head=enforce_head,
        resolved_head_commit=str(seal.get("resolved_head_commit", "")),
    )
    acceptance_fields = set(expected) - {
        "environment_identity",
        "closure_sha256",
        "seal_sha256",
    }
    if any(seal.get(field) != expected.get(field) for field in acceptance_fields):
        if seal.get("catalog_sha256") != _sha256(catalog_data):
            raise ContractError("registration_seal_stale_catalog", "catalog bytesがseal後に変化")
        raise ContractError("registration_seal_stale", "registration closureが現在bytesと不一致")


def _parse_time(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ContractError("checkpoint_time", "時刻はUTC Z表記が必要")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ContractError("checkpoint_time", "時刻を解析できない") from exc
    return parsed.astimezone(timezone.utc)


def _format_time(value: datetime) -> str:
    value = value.astimezone(timezone.utc).replace(microsecond=0)
    return value.isoformat().replace("+00:00", "Z")


def validate_checkpoint(checkpoint: Mapping[str, Any]) -> None:
    _validate_with_schema(checkpoint, SCHEMA_PATHS[1])
    first = _parse_time(checkpoint["first_external_request_at"])
    deadline = _parse_time(checkpoint["deadline_at"])
    quota_observed = _parse_time(checkpoint["quota_observed_at"])
    if deadline - first != RUN_DEADLINE:
        raise ContractError("checkpoint_deadline", "deadlineは最初の外部requestからちょうど30日")
    if not first <= quota_observed <= deadline:
        raise ContractError("checkpoint_quota_time", "quota観測時刻は30日window内が必要")
    if checkpoint["wire_attempt_count"] > MAX_WIRE_ATTEMPTS:
        raise ContractError("checkpoint_wire_budget", "wire attemptが200000を超過")
    page_identity = checkpoint["page_identity"]
    if (
        page_identity["stream_id"] != checkpoint["stream_id"]
        or page_identity["pass_number"] != checkpoint["pass_number"]
    ):
        raise ContractError("checkpoint_identity", "stream/pass/page identityが共通fieldと不一致")
    if checkpoint["last_committed_page"] > page_identity["page_number"]:
        raise ContractError("checkpoint_ledger_prefix", "ledger prefixがpage identityより先にある")
    action = checkpoint["resume_action"]
    state = checkpoint["state"]
    if action not in CHECKPOINT_STATE_ACTIONS.get(state, frozenset()):
        raise ContractError(
            "checkpoint_action", f"未登録のstate/action組: {state}/{action}"
        )
    for field in (
        "continue_cursor_request",
        "start_independent_pass_request",
    ):
        if not isinstance(checkpoint.get(field), Mapping):
            raise ContractError(
                "checkpoint_action", f"D1183の完全requestが無い: {field}"
            )
    if not _is_branch_start_request(
        checkpoint["index"], checkpoint["start_independent_pass_request"]
    ):
        raise ContractError(
            "checkpoint_action", "独立pass requestは枝の先頭でなければならない"
        )
    if action == "continue_cursor":
        position_kind = checkpoint["continue_cursor_request"]["position_kind"]
        expected_kind = {
            "cursor_traversal": "cursor",
            "offset_traversal": "offset",
        }.get(checkpoint["pass_kind"])
        if position_kind != expected_kind:
            raise ContractError(
                "checkpoint_action", "継続requestがpassの位置種別と不一致"
            )
        if position_kind == "cursor":
            source = checkpoint.get("cursor_source")
            if not isinstance(source, Mapping) or source.get(
                "page_number"
            ) != checkpoint["last_committed_page"]:
                raise ContractError(
                    "checkpoint_ledger_prefix", "cursor sourceはlast committed pageが必要"
                )
    elif action == "start_independent_pass":
        if checkpoint["pass_kind"] != "independent" or checkpoint["pass_number"] < 2:
            raise ContractError("checkpoint_action", "独立passはpass 2以降が必要")
        if checkpoint["previous_pass_complete"] is not True:
            raise ContractError("checkpoint_action", "独立pass前に前pass完了が必要")
    elif action == "restart_branch":
        restart = checkpoint.get("restart_branch_request")
        if not isinstance(restart, Mapping) or not _is_branch_start_request(
            checkpoint["index"], restart
        ):
            raise ContractError(
                "checkpoint_action", "restart_branchは枝の先頭だけを指す"
            )


def write_checkpoint_atomic(path: Path, checkpoint: Mapping[str, Any]) -> None:
    validate_checkpoint(checkpoint)
    _write_json_atomic(Path(path), checkpoint)


def _write_json_atomic(path: Path, value: Mapping[str, Any]) -> None:
    _write_bytes_atomic(path, _canonical_json(value))


def _write_bytes_atomic(path: Path, data: bytes) -> None:
    if not isinstance(data, bytes):
        raise ContractError("atomic_write", "atomic writerはbytesだけを受理する")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_bytes_immutable(path: Path, data: bytes) -> None:
    if path.exists():
        try:
            existing = path.read_bytes()
        except OSError as exc:
            raise ContractError("immutable_write", f"既存immutable materialを読めない: {path}") from exc
        if existing != data:
            raise ContractError("immutable_write", f"内容digest pathの既存bytesが不一致: {path}")
        return
    _write_bytes_atomic(path, data)


def _checkpoint_source_digests(seal: Mapping[str, Any]) -> tuple[str, str, str]:
    source_digests = {entry["path"]: entry["sha256"] for entry in seal["source_digests"]}
    return (
        source_digests["orchestrator/related_work_search.py"],
        source_digests["tools/run_axis3_search.py"],
        _sha256(_canonical_json(seal["schema_digests"])),
    )


def _response_checkpoint(
    *,
    row: Mapping[str, Any],
    request: Mapping[str, Any],
    response: TransportResponse,
    seal: Mapping[str, Any],
    budget: "WireBudget",
    now: datetime,
    run_id: str,
    pass_number: int,
    page_number: int,
    next_request: Mapping[str, Any] | None,
) -> dict[str, Any]:
    assert budget.first_external_request_at is not None
    parser_digest, runner_digest, schema_digest = _checkpoint_source_digests(seal)
    pass_kind = {
        "cursor": "cursor_traversal",
        "offset": "offset_traversal",
        "fixed": "fixed",
    }[request["position_kind"]]
    base: dict[str, Any] = {
        "schema_version": CHECKPOINT_VERSION,
        "resume_action": "not_applicable",
        "registration_seal_sha256": seal["seal_sha256"],
        "catalog_sha256": seal["catalog_sha256"],
        "parser_sha256": parser_digest,
        "runner_sha256": runner_digest,
        "schema_sha256": schema_digest,
        "run_id": run_id,
        "stream_id": row["stream_id"],
        "index": row["index"],
        "pass_number": pass_number,
        "pass_kind": pass_kind,
        "window_number": 1,
        "state": "committed" if response.status == 200 else "http_failure",
        "page_identity": {
            "stream_id": row["stream_id"],
            "pass_number": pass_number,
            "page_number": page_number,
        },
        "last_committed_page": page_number,
        "ledger_prefix_sha256": EMPTY_SHA256,
        "previous_checkpoint_sha256": None,
        "wire_attempt_count": budget.attempts,
        "first_external_request_at": _format_time(budget.first_external_request_at),
        "deadline_at": _format_time(budget.deadline_at),
        "quota_observed_at": _format_time(now),
        "quota_remaining": None,
        "continue_cursor_request": _request_without_stream(
            next_request if next_request is not None else request
        ),
        "start_independent_pass_request": _branch_start_checkpoint_request(row),
    }
    if next_request is not None:
        request_payload = _request_without_stream(next_request)
        if next_request["position_kind"] == "cursor":
            base.update(
                resume_action="continue_cursor",
                continue_cursor_request=request_payload,
                cursor_source={
                    "page_number": page_number,
                    "entity_body_path": "bound-by-bundle-ledger",
                    "entity_body_sha256": _sha256(response.entity_body),
                    "field_locator": "/meta/next_cursor",
                },
            )
        else:
            base.update(
                resume_action="continue_cursor",
            )
    elif response.status != 200:
        base.update(
            resume_action="restart_branch",
            restart_branch_request=_branch_start_checkpoint_request(row),
            failed_ledger_sha256=_sha256(response.entity_body),
        )
    return base


_GENERATION_ROOT = ".manifest-generations"
_JOURNAL_VERSION = "axis3-search-bundle-journal/v1"
_STATE_POINTER_VERSION = "axis3-search-bundle-state-pointer/v1"
_STATE_POINTER_NAME = ".bundle-state.json"
_JOURNAL_RELATIVE = "journal/events.jsonl"
_PREFLIGHT_WAL_VERSION = "axis3-search-preflight-wal-pack/v1"
_PREFLIGHT_WAL_RELATIVE = "journal/preflight.wal"
_WAL_LENGTH_SIZE = 8
_FINALIZE_MARKER_VERSION = "bundle_finalized/v1"


def _validate_finalize_marker(
    marker: Mapping[str, Any],
    *,
    pages: Sequence[Mapping[str, Any]],
    checkpoints: Sequence[Mapping[str, Any]],
    ledger_sha256: str,
) -> None:
    kind = marker.get("kind")
    result_kind = "preflight_report" if kind == "preflight" else "run_result"
    descriptor = marker.get("result_descriptor")
    if (
        marker.get("schema_version") != _FINALIZE_MARKER_VERSION
        or kind not in {"preflight", "final"}
        or marker.get("lifecycle") != "finalized"
        or marker.get("result_kind") != result_kind
        or marker.get("page_count") != len(pages)
        or marker.get("checkpoint_count") != len(checkpoints)
        or marker.get("ledger_sha256") != ledger_sha256
        or marker.get("artifact_class")
        not in {"production", "nonproduction_simulation"}
        or not HEX64_RE.fullmatch(str(marker.get("registration_seal_sha256", "")))
        or not HEX64_RE.fullmatch(str(marker.get("catalog_sha256", "")))
        or not isinstance(descriptor, Mapping)
        or not HEX64_RE.fullmatch(str(descriptor.get("sha256", "")))
    ):
        raise ContractError("bundle_finalized", "finalize markerが再導出状態と不一致")
    digest = descriptor["sha256"]
    expected_path = (
        f"reports/preflight-{digest}.json"
        if kind == "preflight"
        else f"results/run-{digest}.json"
    )
    if descriptor.get("path") != expected_path:
        raise ContractError("bundle_finalized", "finalize marker result pathが不一致")
    parent = marker.get("parent_preflight_manifest_sha256")
    if kind == "final":
        if not HEX64_RE.fullmatch(str(parent or "")):
            raise ContractError("bundle_finalized", "finalize marker parent digestが無い")
    elif parent is not None:
        raise ContractError("bundle_finalized", "preflight markerへparentを付けられない")


def _derive_finalize_eligibility(
    *,
    kind: str,
    ledger: Sequence[Mapping[str, Any]],
    attempt_intent: Mapping[str, Any] | None,
    wire_attempt_count: int,
) -> dict[str, Any]:
    """Single WAL-derived policy for every producer and resume path."""

    if kind not in {"preflight", "final"}:
        raise ContractError("finalize_eligibility", "bundle kindが不正")
    if isinstance(wire_attempt_count, bool) or not isinstance(wire_attempt_count, int):
        raise ContractError("finalize_eligibility", "wire attempt countが不正")
    policy = {
        "retryable_statuses": sorted(RETRYABLE_HTTP_STATUSES),
        "wire_attempt_limit": MAX_WIRE_ATTEMPTS,
        "deadline_seconds": int(RUN_DEADLINE.total_seconds()),
        "terminal_http_status_range": [
            TERMINAL_HTTP_STATUS_MIN,
            TERMINAL_HTTP_STATUS_MAX,
        ],
    }
    if attempt_intent is not None:
        return {"finalize_eligible": False, "reason": "pending_attempt", **policy}
    if kind == "preflight" and not ledger:
        return {"finalize_eligible": False, "reason": "availability_not_attempted", **policy}
    tail_status = ledger[-1].get("status") if ledger else None
    if tail_status is not None and (
        isinstance(tail_status, bool)
        or not isinstance(tail_status, int)
        or not TERMINAL_HTTP_STATUS_MIN
        <= tail_status
        <= TERMINAL_HTTP_STATUS_MAX
    ):
        raise ContractError("finalize_eligibility", "tail HTTP statusが不正")
    tail_stream_id = ledger[-1].get("stream_id") if ledger else None
    tail_stream_attempts = 0
    for entry in reversed(ledger):
        if entry.get("stream_id") != tail_stream_id:
            break
        tail_stream_attempts += 1
    retry_available = (
        kind == "preflight"
        and tail_status in RETRYABLE_HTTP_STATUSES
        and tail_stream_attempts < MAX_PREFLIGHT_ATTEMPTS_PER_STREAM
        and wire_attempt_count < MAX_WIRE_ATTEMPTS
    )
    if retry_available:
        return {
            "finalize_eligible": False,
            "reason": f"retryable_http_{tail_status}",
            "retry_stream_id": tail_stream_id,
            **policy,
        }
    return {
        "finalize_eligible": True,
        "reason": (
            "retry_limit_exhausted"
            if kind == "preflight" and tail_status in RETRYABLE_HTTP_STATUSES
            else "terminal_tail"
        ),
        **policy,
    }


def _new_ledger_hasher() -> Any:
    hasher = hashlib.sha256()
    hasher.update(b"[")
    return hasher


def _finish_ledger_hasher(hasher: Any) -> str:
    final = hasher.copy()
    final.update(b"]\n")
    return final.hexdigest()


def _advance_ledger_hasher(hasher: Any, ordinal: int, entry: Mapping[str, Any]) -> str:
    if ordinal > 1:
        hasher.update(b",")
    hasher.update(_canonical_json(entry)[:-1])
    return _finish_ledger_hasher(hasher)


def _ledger_hash_state(
    entries: Sequence[Mapping[str, Any]],
) -> tuple[Any, str, list[str]]:
    hasher = _new_ledger_hasher()
    prefixes: list[str] = []
    for ordinal, entry in enumerate(entries, 1):
        prefixes.append(_advance_ledger_hasher(hasher, ordinal, entry))
    return hasher, _finish_ledger_hasher(hasher), prefixes


def _preflight_wal_record_bytes(
    *,
    sequence: int,
    event: str,
    previous_record_sha256: str | None,
    payload: Mapping[str, Any],
) -> bytes:
    payload_value = copy.deepcopy(dict(payload))
    record: dict[str, Any] = {
        "schema_version": _PREFLIGHT_WAL_VERSION,
        "sequence": sequence,
        "event": event,
        "previous_record_sha256": previous_record_sha256,
        "payload_sha256": _sha256(_canonical_json(payload_value)),
        "length": 0,
        "payload": payload_value,
    }
    while True:
        encoded = _canonical_json(record)
        length = len(encoded)
        if record["length"] == length:
            return encoded
        record["length"] = length


def _decode_preflight_wal_body(value: Any) -> bytes:
    if not isinstance(value, str):
        raise ContractError("bundle_journal", "WAL entity bodyはbase64文字列が必要")
    try:
        body = base64.b64decode(value.encode("ascii"), validate=True)
    except (UnicodeError, binascii.Error) as exc:
        raise ContractError("bundle_journal", "WAL entity body base64が不正") from exc
    if base64.b64encode(body).decode("ascii") != value:
        raise ContractError("bundle_journal", "WAL entity body base64がcanonicalでない")
    return body


def _validate_preflight_wal_raw(
    *,
    intent: Mapping[str, Any],
    raw: Mapping[str, Any],
    body: bytes,
) -> None:
    ordinal = intent.get("ordinal")
    if (
        raw.get("schema_version") != "axis3-search-raw-response/v1"
        or raw.get("ordinal") != ordinal
        or raw.get("request") != intent.get("request")
        or raw.get("entity_body_path") != f"attempts/{ordinal:06d}.body"
        or raw.get("entity_body_byte_count") != len(body)
        or raw.get("entity_body_sha256") != _sha256(body)
    ):
        raise ContractError("bundle_journal", "WAL raw response chainが不一致")
    _parse_time(str(raw.get("response_received_at")))


def _replay_preflight_wal(
    root: Path,
    descriptor: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        descriptor.get("schema_version") != _PREFLIGHT_WAL_VERSION
        or descriptor.get("path") != _PREFLIGHT_WAL_RELATIVE
    ):
        raise ContractError("bundle_journal", "preflight WAL descriptorが不正")
    sealed = descriptor.get("sealed") is True
    if descriptor.get("sealed") not in {True, False}:
        raise ContractError("bundle_journal", "preflight WAL sealed状態が不正")
    path = _safe_bundle_path(root, _PREFLIGHT_WAL_RELATIVE)
    try:
        wal_bytes = path.read_bytes()
    except OSError as exc:
        raise ContractError("bundle_journal", "preflight WALを読めない") from exc
    if sealed:
        expected_size = descriptor.get("byte_count")
        if (
            isinstance(expected_size, bool)
            or not isinstance(expected_size, int)
            or expected_size < 0
            or len(wal_bytes) != expected_size
        ):
            raise ContractError("bundle_journal", "sealed WAL byte countが不一致")

    records: list[Mapping[str, Any]] = []
    offset = 0
    previous_digest: str | None = None
    partial_tail = False
    while offset < len(wal_bytes):
        frame_start = offset
        if len(wal_bytes) - offset < _WAL_LENGTH_SIZE:
            partial_tail = True
            break
        record_length = struct.unpack(">Q", wal_bytes[offset : offset + _WAL_LENGTH_SIZE])[0]
        offset += _WAL_LENGTH_SIZE
        if record_length == 0 or record_length > 512 * 1024 * 1024:
            raise ContractError("bundle_journal", "preflight WAL record lengthが不正")
        if len(wal_bytes) - offset < record_length:
            # A corrupted prefix must not masquerade as a torn append.  If a
            # complete canonical JSON record is already present after the
            # prefix, its self-declared length exposes the prefix mutation.
            try:
                remaining_text = wal_bytes[offset:].decode("utf-8")
                candidate, candidate_end = json.JSONDecoder().raw_decode(
                    remaining_text
                )
                candidate_bytes = remaining_text[:candidate_end].encode("utf-8")
            except (UnicodeError, json.JSONDecodeError):
                candidate = None
                candidate_bytes = b""
            if (
                isinstance(candidate, Mapping)
                and _canonical_json(candidate) == candidate_bytes
                and candidate.get("length") == len(candidate_bytes)
            ):
                raise ContractError(
                    "bundle_journal", "preflight WAL length prefixがrecordと不一致"
                )
            partial_tail = True
            offset = frame_start
            break
        record_bytes = wal_bytes[offset : offset + record_length]
        offset += record_length
        try:
            record = json.loads(record_bytes.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ContractError("bundle_journal", "preflight WAL recordを読めない") from exc
        if not isinstance(record, Mapping) or _canonical_json(record) != record_bytes:
            raise ContractError("bundle_journal", "preflight WAL recordがcanonicalでない")
        payload = record.get("payload")
        if (
            record.get("schema_version") != _PREFLIGHT_WAL_VERSION
            or record.get("sequence") != len(records) + 1
            or record.get("previous_record_sha256") != previous_digest
            or record.get("length") != record_length
            or not isinstance(payload, Mapping)
            or record.get("payload_sha256") != _sha256(_canonical_json(payload))
        ):
            raise ContractError("bundle_journal", "preflight WAL record chainが不一致")
        frame = wal_bytes[frame_start:offset]
        previous_digest = _sha256(frame)
        records.append(record)
    if sealed and partial_tail:
        raise ContractError("bundle_journal", "sealed WALにpartial tailがある")

    pages: list[dict[str, Any]] = []
    checkpoints: list[dict[str, Any]] = []
    checkpoint_values: dict[int, dict[str, Any]] = {}
    ledger: list[dict[str, Any]] = []
    page_bodies: list[bytes] = []
    page_evidence: list[dict[str, Any]] = []
    committed_intents: list[dict[str, Any]] = []
    raw_responses: list[dict[str, Any]] = []
    attempt_intent: dict[str, Any] | None = None
    pending_intent: dict[str, Any] | None = None
    pending_raw: tuple[dict[str, Any], bytes] | None = None
    finalize_marker: dict[str, Any] | None = None
    finalize_marker_sha256: str | None = None
    ledger_hasher = _new_ledger_hasher()
    ledger_digest = _finish_ledger_hasher(ledger_hasher)
    for record in records:
        event = record["event"]
        payload = record["payload"]
        if finalize_marker is not None:
            raise ContractError("bundle_finalized", "finalize marker後にWAL eventがある")
        if event == "bundle_finalized":
            marker = payload.get("marker")
            if (
                attempt_intent is not None
                or pending_intent is not None
                or pending_raw is not None
                or not isinstance(marker, Mapping)
            ):
                raise ContractError("bundle_finalized", "pending中のfinalize markerを拒否")
            _validate_finalize_marker(
                marker,
                pages=pages,
                checkpoints=checkpoints,
                ledger_sha256=ledger_digest,
            )
            finalize_marker = copy.deepcopy(dict(marker))
            finalize_marker_sha256 = _sha256(_canonical_json(marker))
            continue
        if event == "attempt_started":
            intent = payload.get("intent")
            ordinal = len(ledger) + 1
            if (
                attempt_intent is not None
                or not isinstance(intent, Mapping)
                or intent.get("schema_version") != "axis3-search-attempt-intent/v1"
                or intent.get("ordinal") != ordinal
                or intent.get("previous_ledger_prefix_sha256") != ledger_digest
            ):
                raise ContractError("bundle_journal", "WAL attempt start状態遷移が不正")
            _parse_time(str(intent.get("intent_at")))
            pending_intent = copy.deepcopy(dict(intent))
            intent_bytes = _canonical_json(pending_intent)
            attempt_intent = {
                "state": "pending",
                "intent_path": f"attempts/{ordinal:06d}.intent.json",
                "intent_sha256": _sha256(intent_bytes),
            }
            pending_raw = None
            continue
        if event == "response_received":
            raw = payload.get("raw_metadata")
            if (
                attempt_intent is None
                or attempt_intent.get("state") != "pending"
                or pending_raw is not None
                or not isinstance(pending_intent, Mapping)
                or not isinstance(raw, Mapping)
            ):
                raise ContractError("bundle_journal", "WAL raw response状態遷移が不正")
            body = _decode_preflight_wal_body(payload.get("entity_body_base64"))
            _validate_preflight_wal_raw(intent=pending_intent, raw=raw, body=body)
            raw_value = copy.deepcopy(dict(raw))
            pending_raw = (raw_value, body)
            attempt_intent.update(
                state="response_received",
                raw_response_path=f"attempts/{intent['ordinal']:06d}.response.json",
                raw_response_sha256=_sha256(_canonical_json(raw_value)),
            )
            continue
        if event != "response_committed":
            raise ContractError("bundle_journal", "未知のpreflight WAL event")
        intent = pending_intent
        raw = payload.get("raw_metadata")
        evidence = payload.get("evidence")
        page = payload.get("page")
        ledger_entry = payload.get("ledger_entry")
        checkpoint_material = payload.get("checkpoint")
        ordinal = len(ledger) + 1
        if (
            attempt_intent is None
            or attempt_intent.get("state") != "response_received"
            or not isinstance(intent, Mapping)
            or not isinstance(evidence, Mapping)
            or not isinstance(page, Mapping)
            or not isinstance(ledger_entry, Mapping)
        ):
            raise ContractError("bundle_journal", "WAL response commit状態遷移が不正")
        if pending_raw is None:
            raise ContractError("bundle_journal", "WAL raw-first recordが無い")
        raw, body = pending_raw
        validate_page_evidence(evidence, body)
        metadata_bytes = _canonical_json(evidence)
        expected_page = {
            "entity_body_path": raw["entity_body_path"],
            "metadata_path": f"responses/{ordinal:06d}.json",
            "entity_body_sha256": _sha256(body),
            "metadata_sha256": _sha256(metadata_bytes),
        }
        if dict(page) != expected_page:
            raise ContractError("bundle_journal", "WAL page evidence descriptorが不一致")
        expected_ledger_projection = {
            "ordinal": ordinal,
            "stream_id": evidence["stream_id"],
            "pass_number": evidence["pass_number"],
            "page_number": evidence["page_number"],
            "status": evidence["status"],
            "request": evidence["request"],
            "page_entry_sha256": _sha256(_canonical_json(expected_page)),
            "previous_ledger_prefix_sha256": ledger_digest,
            "attempt_intent_path": attempt_intent["intent_path"],
            "attempt_intent_sha256": attempt_intent["intent_sha256"],
            "raw_response_path": attempt_intent["raw_response_path"],
            "raw_response_sha256": attempt_intent["raw_response_sha256"],
        }
        if dict(ledger_entry) != expected_ledger_projection:
            raise ContractError("bundle_journal", "WAL ledger entryが再導出値と不一致")
        if checkpoint_material is not None:
            if not isinstance(checkpoint_material, Mapping):
                raise ContractError("bundle_journal", "WAL checkpoint materialが不正")
            checkpoint_entry = checkpoint_material.get("entry")
            checkpoint = checkpoint_material.get("value")
            if not isinstance(checkpoint_entry, Mapping) or not isinstance(checkpoint, Mapping):
                raise ContractError("bundle_journal", "WAL checkpoint entry/valueが不正")
            checkpoint_bytes = _canonical_json(checkpoint)
            expected_entry = {
                "path": f"checkpoints/{ordinal:06d}.json",
                "sha256": _sha256(checkpoint_bytes),
                "page_ordinal": ordinal,
            }
            if dict(checkpoint_entry) != expected_entry:
                raise ContractError("bundle_journal", "WAL checkpoint descriptorが不一致")
            validate_checkpoint(checkpoint)
            checkpoints.append(copy.deepcopy(expected_entry))
            checkpoint_values[ordinal] = copy.deepcopy(dict(checkpoint))
        pages.append(copy.deepcopy(expected_page))
        ledger.append(copy.deepcopy(expected_ledger_projection))
        ledger_digest = _advance_ledger_hasher(
            ledger_hasher, ordinal, expected_ledger_projection
        )
        page_bodies.append(body)
        page_evidence.append(copy.deepcopy(dict(evidence)))
        committed_intents.append(copy.deepcopy(dict(intent)))
        raw_responses.append(copy.deepcopy(dict(raw)))
        attempt_intent = None
        pending_intent = None
        pending_raw = None

    if finalize_marker is not None and partial_tail:
        raise ContractError("bundle_finalized", "finalize markerが物理EOFでない")
    valid_byte_count = offset
    replayed_descriptor = {
        "schema_version": _PREFLIGHT_WAL_VERSION,
        "path": _PREFLIGHT_WAL_RELATIVE,
        "sealed": sealed,
        "byte_count": valid_byte_count,
        # record_count remains the compact logical count for compatibility;
        # frame_count exposes all durable physical records, including raw.
        "record_count": sum(
            record["event"] in {"attempt_started", "response_committed"}
            for record in records
        ),
        "frame_count": len(records),
        "tail_sha256": previous_digest,
        "page_count": len(pages),
        "checkpoint_count": len(checkpoints),
        "ledger_entry_count": len(ledger),
        "ledger_sha256": ledger_digest,
        "attempt_intent": copy.deepcopy(attempt_intent),
        "finalize_marker_count": int(finalize_marker is not None),
        "finalize_marker_sha256": finalize_marker_sha256,
    }
    if sealed and any(
        descriptor.get(key) != value
        for key, value in replayed_descriptor.items()
    ):
        raise ContractError("bundle_journal", "sealed WAL集計がreplay結果と不一致")
    return {
        "pages": pages,
        "checkpoints": checkpoints,
        "checkpoint_values": checkpoint_values,
        "ledger": ledger,
        "ledger_sha256": ledger_digest,
        "attempt_intent": attempt_intent,
        "page_bodies": page_bodies,
        "page_evidence": page_evidence,
        "committed_intents": committed_intents,
        "raw_responses": raw_responses,
        "pending_intent": copy.deepcopy(pending_intent),
        "pending_raw": copy.deepcopy(pending_raw),
        "descriptor": replayed_descriptor,
        "partial_tail": partial_tail,
        "finalize_marker": finalize_marker,
    }


def _replay_bundle_journal(
    root: Path, descriptor: Mapping[str, Any]
) -> dict[str, Any]:
    if descriptor.get("schema_version") == _PREFLIGHT_WAL_VERSION:
        return _replay_preflight_wal(root, descriptor)
    if descriptor.get("schema_version") != _JOURNAL_VERSION:
        raise ContractError("bundle_journal", "bundle journal versionが不正")
    event_count = descriptor.get("event_count")
    if isinstance(event_count, bool) or not isinstance(event_count, int) or event_count < 0:
        raise ContractError("bundle_journal", "journal event countが不正")
    relative = descriptor.get("path")
    byte_count = descriptor.get("byte_count")
    tail_digest = descriptor.get("tail_sha256")
    if relative != _JOURNAL_RELATIVE:
        raise ContractError("bundle_journal", "journal pathが不正")
    if (
        isinstance(byte_count, bool)
        or not isinstance(byte_count, int)
        or byte_count < 0
    ):
        raise ContractError("bundle_journal", "journal byte countが不正")
    if event_count == 0:
        if byte_count != 0 or tail_digest is not None:
            raise ContractError("bundle_journal", "空journalにtailを付けられない")
    elif not isinstance(tail_digest, str) or not HEX64_RE.fullmatch(tail_digest):
        raise ContractError("bundle_journal", "非空journalにtail digestが必要")
    path = _safe_bundle_path(root, relative)
    try:
        journal_bytes = path.read_bytes()
    except OSError as exc:
        raise ContractError("bundle_journal", "journalを読めない") from exc
    if len(journal_bytes) < byte_count:
        raise ContractError("bundle_journal", "journalがstate pointerより短い")
    segments: list[Mapping[str, Any]] = []
    segment_bytes_values: list[bytes] = []
    previous_digest: str | None = None
    for expected_sequence, segment_bytes in enumerate(
        journal_bytes.splitlines(keepends=True), 1
    ):
        if not segment_bytes.endswith(b"\n"):
            raise ContractError("bundle_journal", "journal eventが途中で切れている")
        try:
            segment = json.loads(segment_bytes.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ContractError("bundle_journal", "journal eventを読めない") from exc
        digest = _sha256(segment_bytes)
        if (
            not isinstance(segment, Mapping)
            or segment.get("schema_version") != _JOURNAL_VERSION
            or segment.get("sequence") != expected_sequence
            or segment.get("previous_event_sha256") != previous_digest
        ):
            raise ContractError("bundle_journal", "journal event chainが不一致")
        segments.append(segment)
        segment_bytes_values.append(segment_bytes)
        previous_digest = digest
    if event_count > len(segments):
        raise ContractError("bundle_journal", "journal event countが物理eventを超える")
    prefix_bytes = sum(len(value) for value in segment_bytes_values[:event_count])
    prefix_tail = (
        _sha256(segment_bytes_values[event_count - 1]) if event_count else None
    )
    if prefix_bytes != byte_count or prefix_tail != tail_digest:
        raise ContractError("bundle_journal", "journal descriptor prefixが不一致")

    pages: list[dict[str, Any]] = []
    checkpoints: list[dict[str, str]] = []
    ledger: list[dict[str, Any]] = []
    attempt_intent: dict[str, Any] | None = None
    finalize_marker: dict[str, Any] | None = None
    finalize_marker_sha256: str | None = None
    ledger_hasher = _new_ledger_hasher()
    ledger_digest = _finish_ledger_hasher(ledger_hasher)
    for segment in segments:
        event = segment.get("event")
        payload = segment.get("payload")
        if not isinstance(payload, Mapping):
            raise ContractError("bundle_journal", "journal event payloadがobjectでない")
        if finalize_marker is not None:
            raise ContractError("bundle_finalized", "finalize marker後にjournal eventがある")
        if event == "bundle_finalized":
            marker = payload.get("marker")
            if attempt_intent is not None or not isinstance(marker, Mapping):
                raise ContractError("bundle_finalized", "pending中のfinalize markerを拒否")
            _validate_finalize_marker(
                marker,
                pages=pages,
                checkpoints=checkpoints,
                ledger_sha256=ledger_digest,
            )
            finalize_marker = copy.deepcopy(dict(marker))
            finalize_marker_sha256 = _sha256(_canonical_json(marker))
            continue
        if event == "attempt_started":
            pending = payload.get("attempt_intent")
            if (
                attempt_intent is not None
                or not isinstance(pending, Mapping)
                or pending.get("state") != "pending"
            ):
                raise ContractError("bundle_journal", "attempt start状態遷移が不正")
            attempt_intent = copy.deepcopy(dict(pending))
            continue
        if event == "response_received":
            received = payload.get("attempt_intent")
            if (
                attempt_intent is None
                or attempt_intent.get("state") != "pending"
                or not isinstance(received, Mapping)
                or received.get("state") != "response_received"
                or any(
                    received.get(key) != attempt_intent.get(key)
                    for key in ("intent_path", "intent_sha256")
                )
            ):
                raise ContractError("bundle_journal", "raw response状態遷移が不正")
            attempt_intent = copy.deepcopy(dict(received))
            continue
        if event != "response_committed":
            raise ContractError("bundle_journal", "未知のjournal event")
        page = payload.get("page")
        ledger_entry = payload.get("ledger_entry")
        checkpoint = payload.get("checkpoint")
        completed_attempt = payload.get("completed_attempt")
        ordinal = len(ledger) + 1
        if (
            attempt_intent is None
            or attempt_intent.get("state") != "response_received"
            or not isinstance(completed_attempt, Mapping)
            or dict(completed_attempt) != attempt_intent
            or completed_attempt.get("state") != "response_received"
            or not isinstance(page, Mapping)
            or not isinstance(ledger_entry, Mapping)
            or not isinstance(checkpoint, Mapping)
            or ledger_entry.get("ordinal") != ordinal
            or ledger_entry.get("previous_ledger_prefix_sha256") != ledger_digest
            or ledger_entry.get("attempt_intent_path")
            != completed_attempt.get("intent_path")
            or ledger_entry.get("attempt_intent_sha256")
            != completed_attempt.get("intent_sha256")
            or ledger_entry.get("raw_response_path")
            != completed_attempt.get("raw_response_path")
            or ledger_entry.get("raw_response_sha256")
            != completed_attempt.get("raw_response_sha256")
            or checkpoint.get("path") != f"checkpoints/{ordinal:06d}.json"
        ):
            raise ContractError("bundle_journal", "response commit eventの状態遷移が不正")
        pages.append(copy.deepcopy(dict(page)))
        ledger.append(copy.deepcopy(dict(ledger_entry)))
        ledger_digest = _advance_ledger_hasher(
            ledger_hasher, ordinal, ledger_entry
        )
        checkpoints.append(copy.deepcopy(dict(checkpoint)))
        attempt_intent = None
    replayed_descriptor = {
        "schema_version": _JOURNAL_VERSION,
        "path": _JOURNAL_RELATIVE,
        "byte_count": len(journal_bytes),
        "event_count": len(segments),
        "tail_sha256": previous_digest,
        "page_count": len(pages),
        "checkpoint_count": len(checkpoints),
        "ledger_entry_count": len(ledger),
        "ledger_sha256": ledger_digest,
        "attempt_intent": copy.deepcopy(attempt_intent),
        "finalize_marker_count": int(finalize_marker is not None),
        "finalize_marker_sha256": finalize_marker_sha256,
    }
    if len(segments) == event_count and any(
        descriptor.get(key) != value for key, value in replayed_descriptor.items()
    ):
        raise ContractError("bundle_journal", "journal集計がreplay結果と不一致")
    return {
        "pages": pages,
        "checkpoints": checkpoints,
        "ledger": ledger,
        "ledger_sha256": ledger_digest,
        "attempt_intent": attempt_intent,
        "descriptor": replayed_descriptor,
        "finalize_marker": finalize_marker,
    }


def _replace_symlink_atomic(path: Path, target: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    temporary.unlink()
    try:
        os.symlink(target, temporary)
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.lexists(temporary):
            temporary.unlink()


def _state_pointer_bytes(value: Mapping[str, Any]) -> bytes:
    payload = copy.deepcopy(dict(value))
    payload.pop("state_pointer", None)
    payload["state_pointer"] = {
        "schema_version": _STATE_POINTER_VERSION,
        "payload_sha256": _sha256(_canonical_json(payload)),
    }
    return _canonical_json(payload)


def _validate_state_pointer(value: Mapping[str, Any]) -> None:
    descriptor = value.get("state_pointer")
    payload = copy.deepcopy(dict(value))
    payload.pop("state_pointer", None)
    if (
        not isinstance(descriptor, Mapping)
        or descriptor.get("schema_version") != _STATE_POINTER_VERSION
        or descriptor.get("payload_sha256") != _sha256(_canonical_json(payload))
        or value.get("schema_version") != BUNDLE_VERSION
        or value.get("state_format") != "journal"
    ):
        raise ContractError("bundle_state_pointer", "atomic state pointer checksumが不一致")


def _logical_manifest_from_replay(
    manifest: Mapping[str, Any], replayed: Mapping[str, Any]
) -> dict[str, Any]:
    logical = copy.deepcopy(dict(manifest))
    logical["attempt_intent"] = copy.deepcopy(replayed["attempt_intent"])
    if isinstance(replayed.get("descriptor"), Mapping):
        logical["journal"] = copy.deepcopy(dict(replayed["descriptor"]))
    logical["pages"] = copy.deepcopy(replayed["pages"])
    logical["ledger"] = {
        "path": f"ledgers/{len(replayed['pages']):06d}.json",
        "sha256": replayed["ledger_sha256"],
    }
    logical["checkpoints"] = copy.deepcopy(replayed["checkpoints"])
    logical["_journal_ledger"] = copy.deepcopy(replayed["ledger"])
    marker = replayed.get("finalize_marker")
    if marker is None:
        if manifest.get("lifecycle") == "finalized":
            raise ContractError(
                "bundle_finalized", "finalized producerに物理EOF markerが無い"
            )
        return logical
    if not isinstance(marker, Mapping):
        raise ContractError("bundle_finalized", "finalize markerがobjectでない")
    if (
        marker.get("kind") != manifest.get("kind")
        or marker.get("artifact_class") != manifest.get("artifact_class")
        or marker.get("registration_seal_sha256")
        != manifest.get("registration_seal_sha256")
        or marker.get("catalog_sha256") != manifest.get("catalog_sha256")
        or marker.get("parent_preflight_manifest_sha256")
        != manifest.get("parent_preflight_manifest_sha256")
    ):
        raise ContractError("bundle_finalized", "markerとmanifest identityが不一致")
    result_key = (
        "preflight_report" if marker.get("kind") == "preflight" else "run_result"
    )
    existing_descriptor = manifest.get(result_key)
    marker_descriptor = marker.get("result_descriptor")
    if (
        manifest.get("lifecycle") == "finalized"
        and existing_descriptor != marker_descriptor
    ):
        raise ContractError("bundle_finalized", "markerとfinalized manifest descriptorが不一致")
    logical["lifecycle"] = "finalized"
    logical[result_key] = copy.deepcopy(marker_descriptor)
    logical["_finalize_recovered"] = (
        manifest.get("lifecycle") != "finalized"
        or existing_descriptor != marker_descriptor
        or manifest.get("journal") != replayed.get("descriptor")
    )
    return logical


def _read_bundle_manifest(root: Path) -> tuple[Mapping[str, Any], bytes, str, int]:
    root = Path(root)
    generation_root = root / _GENERATION_ROOT
    current = generation_root / "current"
    manifest_alias = root / "manifest.json"
    digest_alias = root / "MANIFEST.sha256"
    if manifest_alias.is_symlink() and os.readlink(manifest_alias) == _STATE_POINTER_NAME:
        try:
            manifest_bytes = (root / _STATE_POINTER_NAME).read_bytes()
            compact = json.loads(manifest_bytes.decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ContractError("bundle_state_pointer", "atomic state pointerを読めない") from exc
        if not isinstance(compact, Mapping):
            raise ContractError("bundle_state_pointer", "atomic state pointerがobjectでない")
        _validate_state_pointer(compact)
        journal = compact.get("journal")
        if not isinstance(journal, Mapping):
            raise ContractError("bundle_journal", "state pointerにjournalが無い")
        replayed = _replay_bundle_journal(root, journal)
        packed_preflight = journal.get("schema_version") == _PREFLIGHT_WAL_VERSION
        if not packed_preflight and compact.get("attempt_intent") != replayed["attempt_intent"]:
            if replayed.get("finalize_marker") is None:
                raise ContractError("bundle_state_pointer", "pending attemptがjournalと不一致")
        logical = _logical_manifest_from_replay(compact, replayed)
        generation = 0
        if current.is_symlink() and re.fullmatch(r"[0-9]{12}", os.readlink(current)):
            generation = int(os.readlink(current))
        return logical, manifest_bytes, _sha256(manifest_bytes), generation
    if not current.is_symlink() or not manifest_alias.is_symlink() or not digest_alias.is_symlink():
        raise ContractError(
            "bundle_generation_pointer",
            "bundleは単一current世代pointer経由のmanifest pairが必要",
        )
    if os.readlink(manifest_alias) != f"{_GENERATION_ROOT}/current/manifest.json" or os.readlink(
        digest_alias
    ) != f"{_GENERATION_ROOT}/current/MANIFEST.sha256":
        raise ContractError("bundle_generation_pointer", "manifest alias targetが不正")
    generation_name = os.readlink(current)
    if not re.fullmatch(r"[0-9]{12}", generation_name):
        raise ContractError("bundle_generation_pointer", "current世代名が不正")
    generation_dir = (generation_root / generation_name).resolve()
    try:
        generation_dir.relative_to(generation_root.resolve())
    except ValueError as exc:
        raise ContractError("bundle_generation_pointer", "current世代がbundle外") from exc
    try:
        manifest_bytes = (generation_dir / "manifest.json").read_bytes()
        recorded_digest = (generation_dir / "MANIFEST.sha256").read_text(
            encoding="ascii"
        ).strip()
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("bundle_manifest", "current manifest pairを読めない") from exc
    digest = _sha256(manifest_bytes)
    if recorded_digest != digest:
        raise ContractError("bundle_manifest_digest", "current manifest digestが不一致")
    if not isinstance(manifest, Mapping):
        raise ContractError("bundle_manifest", "manifest rootはobjectが必要")
    if manifest.get("state_format") == "journal":
        journal = manifest.get("journal")
        if not isinstance(journal, Mapping):
            raise ContractError("bundle_journal", "compact manifestにjournalが無い")
        replayed = _replay_bundle_journal(root, journal)
        manifest = _logical_manifest_from_replay(manifest, replayed)
    elif manifest.get("lifecycle") == "finalized":
        journal = manifest.get("journal")
        if not isinstance(journal, Mapping):
            raise ContractError("bundle_finalized", "finalized producerにjournalが無い")
        replayed = _replay_bundle_journal(root, journal)
        manifest = _logical_manifest_from_replay(manifest, replayed)
    return manifest, manifest_bytes, digest, int(generation_name)


def _load_manifest_ledger(root: Path, manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    inline = manifest.get("_journal_ledger")
    if inline is not None:
        if not isinstance(inline, list) or any(
            not isinstance(entry, Mapping) for entry in inline
        ):
            raise ContractError("bundle_ledger", "journal ledgerがarrayでない")
        return [copy.deepcopy(dict(entry)) for entry in inline]
    descriptor = manifest.get("ledger")
    if not isinstance(descriptor, Mapping):
        raise ContractError("bundle_ledger", "ledger descriptorがobjectでない")
    path = _safe_bundle_path(root, descriptor.get("path"))
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("bundle_ledger", "ledgerを読めない") from exc
    if not isinstance(value, list) or any(not isinstance(entry, Mapping) for entry in value):
        raise ContractError("bundle_ledger", "ledgerはobject arrayが必要")
    return [copy.deepcopy(dict(entry)) for entry in value]


class BundleWriter:
    """Crash-safe raw-first writer with an append journal and final fold."""

    def __init__(
        self,
        root: Path,
        *,
        kind: str,
        seal: Mapping[str, Any],
        phase_argv: Mapping[str, Any],
        parent_preflight_manifest_sha256: str | None = None,
        resume: bool = False,
        defer_manifest_fold: bool = False,
        _production_session: LiveSearchSession | None = None,
    ):
        if kind not in {"preflight", "final"}:
            raise ContractError("bundle_manifest", "bundle kindはpreflight/finalだけ")
        if kind == "final" and not HEX64_RE.fullmatch(parent_preflight_manifest_sha256 or ""):
            raise ContractError("bundle_parent", "final bundleはpreflight親digestが必要")
        expected_phase = "preflight" if kind == "preflight" else "run-ready"
        if phase_argv.get("phase") not in {expected_phase, "resume"}:
            raise ContractError("bundle_phase_argv", "bundle kindと実効phase argvが不一致")
        if phase_argv.get("phase_argv_contract_sha256") != _phase_contract_sha256(
            str(phase_argv.get("phase"))
        ):
            raise ContractError("bundle_phase_argv", "phase argv contract digestが不一致")
        production = phase_argv.get("artifact_class") == "production"
        if production and type(_production_session) is not LiveSearchSession:
            raise ContractError(
                "production_writer_receipt",
                "production writerはcanonical live session内部だけで作成できる",
            )
        if not production and _production_session is not None:
            raise ContractError(
                "production_writer_receipt",
                "nonproduction writerへlive sessionを束縛できない",
            )
        self.root = Path(root)
        self.kind = kind
        self.seal = seal
        self.phase_argv = copy.deepcopy(dict(phase_argv))
        self.origin_phase_argv = copy.deepcopy(dict(phase_argv))
        self.lifecycle = "in_progress"
        self.parent = parent_preflight_manifest_sha256
        self.pages: list[dict[str, Any]] = []
        self.checkpoints: list[dict[str, str]] = []
        self.ledger: list[dict[str, Any]] = []
        self.attempt_intent: dict[str, Any] | None = None
        self.preflight_report_descriptor: dict[str, str] | None = None
        self.run_result_descriptor: dict[str, str] | None = None
        self.generation = 0
        self.defer_manifest_fold = defer_manifest_fold
        self.packed_preflight = kind == "preflight" and defer_manifest_fold
        self._packed_pointer_active = False
        self._pending_packed_response: dict[str, Any] | None = None
        self._packed_raw_recorded = False
        self.journal_tail_sha256: str | None = None
        self.journal_event_count = 0
        self.journal_byte_count = 0
        self.finalize_marker_sha256: str | None = None
        self._last_wal_record_bytes: bytes | None = None
        self._production_session = _production_session
        if resume:
            manifest, _, _, self.generation = _read_bundle_manifest(self.root)
            if manifest.get("kind") != kind:
                raise ContractError("bundle_resume", "resume bundle kindが不一致")
            if manifest.get("lifecycle") not in {"in_progress", "finalized"}:
                raise ContractError("bundle_resume", "resume bundle lifecycleが不正")
            self.lifecycle = str(manifest["lifecycle"])
            origin_phase = manifest.get("origin_phase_argv")
            if not isinstance(origin_phase, Mapping):
                raise ContractError("bundle_resume", "bundle origin phase argvが無い")
            self.origin_phase_argv = copy.deepcopy(dict(origin_phase))
            journal = manifest.get("journal")
            if isinstance(journal, Mapping):
                self.defer_manifest_fold = True
                self.packed_preflight = (
                    kind == "preflight"
                    and journal.get("schema_version") == _PREFLIGHT_WAL_VERSION
                )
                tail = journal.get("tail_sha256")
                self.journal_tail_sha256 = str(tail) if isinstance(tail, str) else None
                self.journal_event_count = int(
                    journal.get(
                        "frame_count",
                        journal.get("record_count", journal.get("event_count", 0)),
                    )
                )
                self.journal_byte_count = int(journal.get("byte_count", 0))
                marker_digest = journal.get("finalize_marker_sha256")
                self.finalize_marker_sha256 = (
                    str(marker_digest) if isinstance(marker_digest, str) else None
                )
            self.pages = copy.deepcopy(manifest.get("pages", []))
            self.checkpoints = copy.deepcopy(manifest.get("checkpoints", []))
            self.attempt_intent = copy.deepcopy(manifest.get("attempt_intent"))
            if isinstance(manifest.get("preflight_report"), Mapping):
                self.preflight_report_descriptor = copy.deepcopy(
                    dict(manifest["preflight_report"])
                )
            if isinstance(manifest.get("run_result"), Mapping):
                self.run_result_descriptor = copy.deepcopy(
                    dict(manifest["run_result"])
                )
            self.ledger = _load_manifest_ledger(self.root, manifest)
            self._ledger_hasher, self._ledger_digest, _ = _ledger_hash_state(
                self.ledger
            )
        else:
            self._ledger_hasher, self._ledger_digest, _ = _ledger_hash_state([])
            journal_path = self.root / (
                _PREFLIGHT_WAL_RELATIVE
                if self.packed_preflight
                else _JOURNAL_RELATIVE
            )
            if journal_path.exists() and journal_path.stat().st_size != 0:
                raise ContractError("bundle_journal", "新規bundleに既存journalがある")
            _write_bytes_immutable(journal_path, b"")
            self._write_manifest()

    @property
    def ledger_digest(self) -> str:
        return self._ledger_digest

    @property
    def previous_checkpoint_digest(self) -> str | None:
        return self.checkpoints[-1]["sha256"] if self.checkpoints else None

    @property
    def ledger_relative(self) -> str:
        return f"ledgers/{len(self.pages):06d}.json"

    def _journal_descriptor(self, *, sealed: bool = True) -> dict[str, Any]:
        if self.packed_preflight:
            return {
                "schema_version": _PREFLIGHT_WAL_VERSION,
                "path": _PREFLIGHT_WAL_RELATIVE,
                "sealed": sealed,
                "byte_count": self.journal_byte_count,
                "record_count": len(self.pages) * 2 + int(self.attempt_intent is not None),
                "frame_count": self.journal_event_count,
                "tail_sha256": self.journal_tail_sha256,
                "page_count": len(self.pages),
                "checkpoint_count": len(self.checkpoints),
                "ledger_entry_count": len(self.ledger),
                "ledger_sha256": self.ledger_digest,
                "attempt_intent": copy.deepcopy(self.attempt_intent),
                "finalize_marker_count": int(self.finalize_marker_sha256 is not None),
                "finalize_marker_sha256": self.finalize_marker_sha256,
            }
        return {
            "schema_version": _JOURNAL_VERSION,
            "path": _JOURNAL_RELATIVE,
            "byte_count": self.journal_byte_count,
            "event_count": self.journal_event_count,
            "tail_sha256": self.journal_tail_sha256,
            "page_count": len(self.pages),
            "checkpoint_count": len(self.checkpoints),
            "ledger_entry_count": len(self.ledger),
            "ledger_sha256": self.ledger_digest,
            "attempt_intent": copy.deepcopy(self.attempt_intent),
            "finalize_marker_count": int(self.finalize_marker_sha256 is not None),
            "finalize_marker_sha256": self.finalize_marker_sha256,
        }

    def _base_manifest(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schema_version": BUNDLE_VERSION,
            "kind": self.kind,
            "lifecycle": self.lifecycle,
            "artifact_class": self.origin_phase_argv["artifact_class"],
            "registration_seal_sha256": self.seal["seal_sha256"],
            "catalog_sha256": self.seal["catalog_sha256"],
            "phase_argv": copy.deepcopy(self.phase_argv),
            "origin_phase_argv": copy.deepcopy(self.origin_phase_argv),
            "attempt_intent": copy.deepcopy(self.attempt_intent),
        }
        if self.kind == "final":
            value["parent_preflight_manifest_sha256"] = self.parent
        if self.preflight_report_descriptor is not None:
            value["preflight_report"] = copy.deepcopy(
                self.preflight_report_descriptor
            )
        if self.run_result_descriptor is not None:
            value["run_result"] = copy.deepcopy(self.run_result_descriptor)
        return value

    def _manifest(self) -> dict[str, Any]:
        value = self._base_manifest()
        value.update(
            pages=copy.deepcopy(self.pages),
            ledger={"path": self.ledger_relative, "sha256": self.ledger_digest},
            checkpoints=copy.deepcopy(self.checkpoints),
        )
        value["journal"] = self._journal_descriptor(sealed=True)
        return value

    def _compact_manifest(self) -> dict[str, Any]:
        value = self._base_manifest()
        value["state_format"] = "journal"
        value["journal"] = self._journal_descriptor(sealed=False)
        return value

    def _append_preflight_wal_record(
        self, event: str, payload: Mapping[str, Any]
    ) -> None:
        sequence = self.journal_event_count + 1
        record_bytes = _preflight_wal_record_bytes(
            sequence=sequence,
            event=event,
            previous_record_sha256=self.journal_tail_sha256,
            payload=payload,
        )
        frame = struct.pack(">Q", len(record_bytes)) + record_bytes
        path = _safe_bundle_path(self.root, _PREFLIGHT_WAL_RELATIVE)
        try:
            with path.open("r+b") as handle:
                handle.seek(0, os.SEEK_END)
                size = handle.tell()
                if size < self.journal_byte_count:
                    raise ContractError("bundle_journal", "preflight WALがvalid prefixより短い")
                if size > self.journal_byte_count:
                    handle.truncate(self.journal_byte_count)
                    handle.flush()
                    os.fsync(handle.fileno())
                handle.seek(self.journal_byte_count)
                handle.write(frame)
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            raise ContractError("bundle_journal", "preflight WAL recordを追記できない") from exc
        self.journal_tail_sha256 = _sha256(frame)
        self.journal_event_count = sequence
        self.journal_byte_count += len(frame)
        self._last_wal_record_bytes = record_bytes

    def _append_journal_event(
        self, event: str, payload: Mapping[str, Any]
    ) -> None:
        if self.packed_preflight:
            self._append_preflight_wal_record(event, payload)
            return
        sequence = self.journal_event_count + 1
        segment = {
            "schema_version": _JOURNAL_VERSION,
            "sequence": sequence,
            "event": event,
            "previous_event_sha256": self.journal_tail_sha256,
            "payload": copy.deepcopy(dict(payload)),
        }
        data = _canonical_json(segment)
        digest = _sha256(data)
        path = _safe_bundle_path(self.root, _JOURNAL_RELATIVE)
        try:
            with path.open("r+b") as handle:
                handle.seek(0, os.SEEK_END)
                size = handle.tell()
                if size < self.journal_byte_count:
                    raise ContractError("bundle_journal", "journalがstate pointerより短い")
                if size > self.journal_byte_count:
                    handle.truncate(self.journal_byte_count)
                    handle.flush()
                    os.fsync(handle.fileno())
                handle.seek(self.journal_byte_count)
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            raise ContractError("bundle_journal", "journal eventを追記できない") from exc
        self.journal_tail_sha256 = digest
        self.journal_event_count = sequence
        self.journal_byte_count += len(data)

    def _finalize_marker(self) -> dict[str, Any]:
        descriptor = (
            self.preflight_report_descriptor
            if self.kind == "preflight"
            else self.run_result_descriptor
        )
        if not isinstance(descriptor, Mapping):
            raise ContractError("bundle_finalized", "finalize result descriptorが無い")
        marker = {
            "schema_version": _FINALIZE_MARKER_VERSION,
            "kind": self.kind,
            "lifecycle": "finalized",
            "artifact_class": self.origin_phase_argv["artifact_class"],
            "registration_seal_sha256": self.seal["seal_sha256"],
            "catalog_sha256": self.seal["catalog_sha256"],
            "parent_preflight_manifest_sha256": self.parent,
            "page_count": len(self.pages),
            "checkpoint_count": len(self.checkpoints),
            "ledger_sha256": self.ledger_digest,
            "result_kind": (
                "preflight_report" if self.kind == "preflight" else "run_result"
            ),
            "result_descriptor": copy.deepcopy(dict(descriptor)),
        }
        _validate_finalize_marker(
            marker,
            pages=self.pages,
            checkpoints=self.checkpoints,
            ledger_sha256=self.ledger_digest,
        )
        return marker

    def _append_finalize_marker(self) -> None:
        if self.finalize_marker_sha256 is not None:
            raise ContractError("bundle_finalized", "finalize markerはexact oneだけ")
        marker = self._finalize_marker()
        self._append_journal_event("bundle_finalized", {"marker": marker})
        self.finalize_marker_sha256 = _sha256(_canonical_json(marker))

    def _write_state_pointer(self) -> None:
        pointer_bytes = _state_pointer_bytes(self._compact_manifest())
        _write_bytes_atomic(self.root / _STATE_POINTER_NAME, pointer_bytes)
        alias = self.root / "manifest.json"
        if not alias.is_symlink() or os.readlink(alias) != _STATE_POINTER_NAME:
            if os.path.lexists(alias) and not alias.is_symlink():
                raise ContractError("bundle_state_pointer", "manifest aliasがsymlinkでない")
            _replace_symlink_atomic(alias, _STATE_POINTER_NAME)
        self._packed_pointer_active = True

    def _publish_manifest(self, manifest_bytes: bytes) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        next_generation = self.generation + 1
        generation_name = f"{next_generation:012d}"
        generation_dir = self.root / _GENERATION_ROOT / generation_name
        if generation_dir.exists():
            current = self.root / _GENERATION_ROOT / "current"
            if current.is_symlink() and os.readlink(current) == generation_name:
                raise ContractError(
                    "bundle_generation_pointer",
                    "writer世代がcurrent pointerより古い",
                )
            if not generation_dir.is_dir():
                raise ContractError("bundle_generation_pointer", "未確定世代pathがdirectoryでない")
            children = list(generation_dir.iterdir())
            if any(
                child.name not in {"manifest.json", "MANIFEST.sha256"}
                or not child.is_file()
                for child in children
            ):
                raise ContractError(
                    "bundle_generation_pointer",
                    "未確定世代に未知のmaterialがある",
                )
            for child in children:
                child.unlink()
            generation_dir.rmdir()
        generation_dir.mkdir(parents=True, exist_ok=False)
        _write_bytes_atomic(generation_dir / "manifest.json", manifest_bytes)
        _write_bytes_atomic(
            generation_dir / "MANIFEST.sha256",
            (_sha256(manifest_bytes) + "\n").encode("ascii"),
        )
        _replace_symlink_atomic(self.root / _GENERATION_ROOT / "current", generation_name)
        for name in ("manifest.json", "MANIFEST.sha256"):
            alias = self.root / name
            expected = f"{_GENERATION_ROOT}/current/{name}"
            if not os.path.lexists(alias):
                _replace_symlink_atomic(alias, expected)
            elif (
                name == "manifest.json"
                and self.defer_manifest_fold
                and alias.is_symlink()
                and os.readlink(alias) == _STATE_POINTER_NAME
            ):
                _replace_symlink_atomic(alias, expected)
            elif not alias.is_symlink() or os.readlink(alias) != expected:
                raise ContractError("bundle_generation_pointer", f"{name} aliasが不正")
        self.generation = next_generation
        retained = {generation_name, f"{max(1, next_generation - 1):012d}"}
        generation_root = self.root / _GENERATION_ROOT
        for candidate in generation_root.iterdir():
            if (
                candidate.is_dir()
                and re.fullmatch(r"[0-9]{12}", candidate.name)
                and candidate.name not in retained
            ):
                for child in candidate.iterdir():
                    child.unlink()
                candidate.rmdir()

    def _write_manifest(self, *, fold: bool = False) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        if self.defer_manifest_fold and not fold:
            if not self.packed_preflight or not self._packed_pointer_active:
                self._write_state_pointer()
            return
        ledger_bytes = _canonical_json(self.ledger)
        _write_bytes_atomic(self.root / self.ledger_relative, ledger_bytes)
        _write_bytes_atomic(self.root / "ledger.json", ledger_bytes)
        self._publish_manifest(_canonical_json(self._manifest()))

    def begin_attempt(
        self,
        *,
        request: Mapping[str, Any],
        pass_number: int,
        page_number: int,
        expected_wire_attempt_count: int,
        intent_at: datetime,
    ) -> None:
        if self.lifecycle == "finalized" or self.finalize_marker_sha256 is not None:
            raise ContractError("bundle_finalized", "finalize marker後にattemptできない")
        if self.attempt_intent is not None:
            raise ContractError("bundle_pending_attempt", "未確定attempt intentが既に存在する")
        self.lifecycle = "in_progress"
        if self.defer_manifest_fold:
            # A resumed bundle's prior report/result describes only the prior
            # committed prefix.  Do not expose that stale finalization while a
            # new journal suffix is in progress.
            self.preflight_report_descriptor = None
            self.run_result_descriptor = None
            if self.packed_preflight and not self._packed_pointer_active:
                self._write_manifest()
        ordinal = len(self.ledger) + 1
        intent = {
            "schema_version": "axis3-search-attempt-intent/v1",
            "ordinal": ordinal,
            "stream_id": request["stream_id"],
            "pass_number": pass_number,
            "page_number": page_number,
            "request": copy.deepcopy(dict(request)),
            "expected_wire_attempt_count": expected_wire_attempt_count,
            "previous_ledger_prefix_sha256": self.ledger_digest,
            "intent_at": _format_time(intent_at),
        }
        relative = f"attempts/{ordinal:06d}.intent.json"
        intent_bytes = _canonical_json(intent)
        if not self.packed_preflight:
            _write_bytes_immutable(self.root / relative, intent_bytes)
        self.attempt_intent = {
            "state": "pending",
            "intent_path": relative,
            "intent_sha256": _sha256(intent_bytes),
        }
        if self.packed_preflight:
            self._pending_packed_response = {"intent": intent}
            self._packed_raw_recorded = False
            self._append_journal_event("attempt_started", {"intent": intent})
        else:
            self._append_journal_event(
                "attempt_started", {"attempt_intent": self.attempt_intent}
            )
            self._write_manifest()

    def record_raw_response(
        self,
        response: TransportResponse,
        *,
        receipt: _SendReceipt | None = None,
    ) -> TransportResponse:
        if self.attempt_intent is None or self.attempt_intent.get("state") != "pending":
            raise ContractError("bundle_pending_attempt", "送信前attempt intentが無い")
        if self.packed_preflight:
            if not isinstance(self._pending_packed_response, Mapping):
                raise ContractError("bundle_pending_attempt", "WAL pending intentが無い")
            intent = copy.deepcopy(dict(self._pending_packed_response["intent"]))
        else:
            intent_path = _safe_bundle_path(self.root, self.attempt_intent["intent_path"])
            intent = json.loads(intent_path.read_text(encoding="utf-8"))
        ordinal = intent["ordinal"]
        if response.response_received_at is None:
            raise ContractError(
                "response_received_time", "raw responseには応答受領時刻が必要"
            )
        _parse_time(response.response_received_at)
        receipt_descriptor: Mapping[str, Any] | None = None
        if self.origin_phase_argv.get("artifact_class") == "production":
            if type(self._production_session) is not LiveSearchSession or receipt is None:
                raise ContractError(
                    "production_writer_receipt",
                    "production raw responseには同sessionのone-shot receiptが必要",
                )
            receipt_descriptor = self._production_session._consume_receipt(
                receipt,
                request=intent["request"],
                response=response,
                ordinal=ordinal,
            )
        elif receipt is not None:
            raise ContractError(
                "send_receipt_identity",
                "nonproduction responseへproduction receiptを付けられない",
            )
        body_relative = f"attempts/{ordinal:06d}.body"
        metadata_relative = f"attempts/{ordinal:06d}.response.json"
        raw_metadata = {
            "schema_version": "axis3-search-raw-response/v1",
            "ordinal": ordinal,
            "request": copy.deepcopy(intent["request"]),
            "status": response.status,
            "final_url": response.final_url,
            "endpoint": response.endpoint,
            "content_type": response.content_type,
            "response_received_at": response.response_received_at,
            "headers": [[name, value] for name, value in response.headers],
            "entity_body_path": body_relative,
            "entity_body_byte_count": len(response.entity_body),
            "entity_body_sha256": _sha256(response.entity_body),
            "transport_receipt": copy.deepcopy(receipt_descriptor),
        }
        metadata_bytes = _canonical_json(raw_metadata)
        if not self.packed_preflight:
            _write_bytes_immutable(self.root / body_relative, response.entity_body)
            _write_bytes_immutable(self.root / metadata_relative, metadata_bytes)
        self.attempt_intent.update(
            state="response_received",
            raw_response_path=metadata_relative,
            raw_response_sha256=_sha256(metadata_bytes),
        )
        if self.packed_preflight:
            assert self._pending_packed_response is not None
            self._append_journal_event(
                "response_received",
                {
                    "raw_metadata": copy.deepcopy(dict(raw_metadata)),
                    "entity_body_base64": base64.b64encode(response.entity_body).decode(
                        "ascii"
                    ),
                },
            )
            if self._last_wal_record_bytes is None:
                raise ContractError("bundle_journal", "保存済みraw WAL recordが無い")
            saved_record = json.loads(self._last_wal_record_bytes.decode("utf-8"))
            saved_payload = saved_record.get("payload")
            if not isinstance(saved_payload, Mapping):
                raise ContractError("bundle_journal", "保存済みraw WAL payloadが無い")
            saved_raw = saved_payload.get("raw_metadata")
            if not isinstance(saved_raw, Mapping):
                raise ContractError("bundle_journal", "保存済みraw metadataが無い")
            saved_body = _decode_preflight_wal_body(
                saved_payload.get("entity_body_base64")
            )
            _validate_preflight_wal_raw(
                intent=intent, raw=saved_raw, body=saved_body
            )
            self._pending_packed_response.update(
                raw_metadata=copy.deepcopy(dict(saved_raw)),
                entity_body=saved_body,
            )
            self._packed_raw_recorded = True
            return TransportResponse(
                status=int(saved_raw["status"]),
                entity_body=saved_body,
                headers=tuple((str(name), str(value)) for name, value in saved_raw["headers"]),
                endpoint=str(saved_raw["endpoint"]),
                final_url=str(saved_raw["final_url"]),
                content_type=str(saved_raw["content_type"]),
                response_received_at=str(saved_raw["response_received_at"]),
            )
        else:
            self._append_journal_event(
                "response_received", {"attempt_intent": self.attempt_intent}
            )
            self._write_manifest()
            saved_raw = json.loads((self.root / metadata_relative).read_text(encoding="utf-8"))
            saved_body = (self.root / body_relative).read_bytes()
            return TransportResponse(
                status=int(saved_raw["status"]),
                entity_body=saved_body,
                headers=tuple((str(name), str(value)) for name, value in saved_raw["headers"]),
                endpoint=str(saved_raw["endpoint"]),
                final_url=str(saved_raw["final_url"]),
                content_type=str(saved_raw["content_type"]),
                response_received_at=str(saved_raw["response_received_at"]),
            )

    def materialize_pending_attempt(self) -> None:
        """Expose exceptional packed raw material without penalizing normal rows."""

        if (
            not self.packed_preflight
            or self.attempt_intent is None
            or not isinstance(self._pending_packed_response, Mapping)
        ):
            return
        intent = self._pending_packed_response.get("intent")
        raw = self._pending_packed_response.get("raw_metadata")
        body = self._pending_packed_response.get("entity_body")
        if not isinstance(intent, Mapping):
            return
        if (
            self.attempt_intent.get("state") == "response_received"
            and isinstance(raw, Mapping)
            and isinstance(body, bytes)
            and not self._packed_raw_recorded
        ):
            self._append_journal_event(
                "response_received",
                {
                    "intent": copy.deepcopy(dict(intent)),
                    "raw_metadata": copy.deepcopy(dict(raw)),
                    "entity_body_base64": base64.b64encode(body).decode("ascii"),
                },
            )
            self._packed_raw_recorded = True
        _write_bytes_immutable(
            self.root / self.attempt_intent["intent_path"], _canonical_json(intent)
        )
        if isinstance(raw, Mapping) and isinstance(body, bytes):
            _write_bytes_immutable(
                self.root / str(raw["entity_body_path"]), body
            )
            _write_bytes_immutable(
                self.root / self.attempt_intent["raw_response_path"],
                _canonical_json(raw),
            )
        self._write_state_pointer()

    def commit_response(
        self,
        *,
        evidence: Mapping[str, Any],
        entity_body: bytes,
        checkpoint: Mapping[str, Any] | None,
    ) -> Mapping[str, Any] | None:
        if self.attempt_intent is None:
            if checkpoint is None:
                raise ContractError(
                    "bundle_pending_attempt",
                    "送信前intent無しcommitにはcheckpointが必要",
                )
            self.begin_attempt(
                request=evidence["request"],
                pass_number=int(evidence["pass_number"]),
                page_number=int(evidence["page_number"]),
                expected_wire_attempt_count=int(checkpoint["wire_attempt_count"]),
                intent_at=_parse_time(checkpoint["quota_observed_at"]),
            )
        if self.attempt_intent.get("state") == "pending":
            provenance = evidence["alternative_provenance"]
            self.record_raw_response(
                TransportResponse(
                    status=int(evidence["status"]),
                    entity_body=entity_body,
                    headers=tuple(
                        (header["name"], header["value"])
                        for header in provenance["observed_response_headers"]
                    ),
                    endpoint=str(provenance["endpoint"]),
                    final_url=str(evidence["final_url"]),
                    content_type=str(evidence["content_type"]),
                    response_received_at=str(evidence["response_received_at"]),
                )
            )
        if self.attempt_intent.get("state") != "response_received":
            raise ContractError("bundle_pending_attempt", "raw response commitが未完了")
        if self.packed_preflight:
            return self._commit_packed_preflight_response(
                evidence=evidence,
                entity_body=entity_body,
                checkpoint=checkpoint,
            )
        if checkpoint is None:
            raise ContractError("bundle_checkpoint", "legacy/final responseはcheckpointが必要")
        intent_path = _safe_bundle_path(self.root, self.attempt_intent["intent_path"])
        raw_path = _safe_bundle_path(self.root, self.attempt_intent["raw_response_path"])
        intent_bytes = intent_path.read_bytes()
        raw_bytes = raw_path.read_bytes()
        intent = json.loads(intent_bytes.decode("utf-8"))
        raw = json.loads(raw_bytes.decode("utf-8"))
        raw_body = _safe_bundle_path(self.root, raw["entity_body_path"]).read_bytes()
        if (
            evidence["request"] != intent["request"]
            or raw["request"] != intent["request"]
            or evidence["status"] != raw["status"]
            or evidence["final_url"] != raw["final_url"]
            or evidence["content_type"] != raw["content_type"]
            or evidence["response_received_at"] != raw["response_received_at"]
            or raw_body != entity_body
        ):
            raise ContractError("bundle_raw_response", "raw responseと解析済みevidenceが不一致")
        ordinal = len(self.pages) + 1
        metadata_relative = f"responses/{ordinal:06d}.json"
        metadata_bytes = _canonical_json(evidence)
        _write_bytes_immutable(self.root / metadata_relative, metadata_bytes)
        page_entry = {
            "entity_body_path": raw["entity_body_path"],
            "metadata_path": metadata_relative,
            "entity_body_sha256": _sha256(entity_body),
            "metadata_sha256": _sha256(metadata_bytes),
        }
        self.pages.append(page_entry)
        ledger_entry = {
            "ordinal": ordinal,
            "stream_id": evidence["stream_id"],
            "pass_number": evidence["pass_number"],
            "page_number": evidence["page_number"],
            "status": evidence["status"],
            "request": copy.deepcopy(evidence["request"]),
            "page_entry_sha256": _sha256(_canonical_json(page_entry)),
            "previous_ledger_prefix_sha256": self.ledger_digest,
            "attempt_intent_path": self.attempt_intent["intent_path"],
            "attempt_intent_sha256": _sha256(intent_bytes),
            "raw_response_path": self.attempt_intent["raw_response_path"],
            "raw_response_sha256": _sha256(raw_bytes),
        }
        self.ledger.append(ledger_entry)
        self._ledger_digest = _advance_ledger_hasher(
            self._ledger_hasher, ordinal, ledger_entry
        )
        committed_checkpoint = copy.deepcopy(dict(checkpoint))
        committed_checkpoint["ledger_prefix_sha256"] = self.ledger_digest
        committed_checkpoint["previous_checkpoint_sha256"] = self.previous_checkpoint_digest
        committed_checkpoint["last_committed_page"] = evidence["page_number"]
        if (
            committed_checkpoint["resume_action"] == "continue_cursor"
            and committed_checkpoint["continue_cursor_request"]["position_kind"]
            == "cursor"
        ):
            committed_checkpoint["cursor_source"]["entity_body_path"] = raw["entity_body_path"]
        validate_checkpoint(committed_checkpoint)
        checkpoint_relative = f"checkpoints/{ordinal:06d}.json"
        checkpoint_bytes = _canonical_json(committed_checkpoint)
        _write_bytes_immutable(self.root / checkpoint_relative, checkpoint_bytes)
        checkpoint_entry = {
            "path": checkpoint_relative,
            "sha256": _sha256(checkpoint_bytes),
        }
        self.checkpoints.append(checkpoint_entry)
        completed_attempt = copy.deepcopy(self.attempt_intent)
        self.attempt_intent = None
        self._append_journal_event(
            "response_committed",
            {
                "page": page_entry,
                "ledger_entry": ledger_entry,
                "checkpoint": checkpoint_entry,
                "completed_attempt": completed_attempt,
            },
        )
        self._write_manifest()
        return committed_checkpoint

    def _commit_packed_preflight_response(
        self,
        *,
        evidence: Mapping[str, Any],
        entity_body: bytes,
        checkpoint: Mapping[str, Any] | None,
    ) -> Mapping[str, Any] | None:
        pending = self._pending_packed_response
        if not isinstance(pending, Mapping):
            raise ContractError("bundle_pending_attempt", "WAL raw responseが無い")
        intent = pending.get("intent")
        raw = pending.get("raw_metadata")
        raw_body = pending.get("entity_body")
        if (
            not isinstance(intent, Mapping)
            or not isinstance(raw, Mapping)
            or not isinstance(raw_body, bytes)
            or raw_body != entity_body
            or evidence.get("request") != intent.get("request")
            or raw.get("request") != intent.get("request")
            or evidence.get("status") != raw.get("status")
            or evidence.get("final_url") != raw.get("final_url")
            or evidence.get("content_type") != raw.get("content_type")
            or evidence.get("response_received_at")
            != raw.get("response_received_at")
        ):
            raise ContractError("bundle_raw_response", "WAL raw responseとevidenceが不一致")
        validate_page_evidence(evidence, entity_body)
        ordinal = len(self.pages) + 1
        metadata_bytes = _canonical_json(evidence)
        page_entry = {
            "entity_body_path": raw["entity_body_path"],
            "metadata_path": f"responses/{ordinal:06d}.json",
            "entity_body_sha256": _sha256(entity_body),
            "metadata_sha256": _sha256(metadata_bytes),
        }
        assert self.attempt_intent is not None
        ledger_entry = {
            "ordinal": ordinal,
            "stream_id": evidence["stream_id"],
            "pass_number": evidence["pass_number"],
            "page_number": evidence["page_number"],
            "status": evidence["status"],
            "request": copy.deepcopy(evidence["request"]),
            "page_entry_sha256": _sha256(_canonical_json(page_entry)),
            "previous_ledger_prefix_sha256": self.ledger_digest,
            "attempt_intent_path": self.attempt_intent["intent_path"],
            "attempt_intent_sha256": self.attempt_intent["intent_sha256"],
            "raw_response_path": self.attempt_intent["raw_response_path"],
            "raw_response_sha256": self.attempt_intent["raw_response_sha256"],
        }
        next_hasher = self._ledger_hasher.copy()
        next_ledger_digest = _advance_ledger_hasher(
            next_hasher, ordinal, ledger_entry
        )
        committed_checkpoint: dict[str, Any] | None = None
        checkpoint_entry: dict[str, Any] | None = None
        checkpoint_material: dict[str, Any] | None = None
        if checkpoint is not None:
            committed_checkpoint = copy.deepcopy(dict(checkpoint))
            committed_checkpoint["ledger_prefix_sha256"] = next_ledger_digest
            committed_checkpoint[
                "previous_checkpoint_sha256"
            ] = self.previous_checkpoint_digest
            committed_checkpoint["last_committed_page"] = evidence["page_number"]
            if (
                committed_checkpoint["resume_action"] == "continue_cursor"
                and committed_checkpoint["continue_cursor_request"][
                    "position_kind"
                ]
                == "cursor"
            ):
                committed_checkpoint["cursor_source"][
                    "entity_body_path"
                ] = raw["entity_body_path"]
            validate_checkpoint(committed_checkpoint)
            checkpoint_bytes = _canonical_json(committed_checkpoint)
            checkpoint_entry = {
                "path": f"checkpoints/{ordinal:06d}.json",
                "sha256": _sha256(checkpoint_bytes),
                "page_ordinal": ordinal,
            }
            checkpoint_material = {
                "entry": checkpoint_entry,
                "value": committed_checkpoint,
            }
            _write_bytes_immutable(
                self.root / checkpoint_entry["path"], checkpoint_bytes
            )
            _write_bytes_immutable(
                self.root / str(raw["entity_body_path"]), entity_body
            )
        self._append_journal_event(
            "response_committed",
            {
                "evidence": copy.deepcopy(dict(evidence)),
                "page": page_entry,
                "ledger_entry": ledger_entry,
                "checkpoint": checkpoint_material,
            },
        )
        self.pages.append(page_entry)
        self.ledger.append(ledger_entry)
        self._ledger_hasher = next_hasher
        self._ledger_digest = next_ledger_digest
        if checkpoint_entry is not None:
            self.checkpoints.append(checkpoint_entry)
        self.attempt_intent = None
        self._pending_packed_response = None
        self._packed_raw_recorded = False
        return committed_checkpoint

    def finalize_preflight(self, report: Mapping[str, Any]) -> str:
        if self.kind != "preflight":
            raise ContractError("bundle_manifest", "preflight reportはpreflight bundleだけ")
        if self.attempt_intent is not None:
            raise ContractError("bundle_pending_attempt", "未確定attempt中はreportをfinalizeできない")
        if self.lifecycle == "finalized" or self.finalize_marker_sha256 is not None:
            raise ContractError("bundle_finalized", "preflight二重finalizeを拒否")
        if self.packed_preflight:
            replayed = _replay_preflight_wal(
                self.root, self._journal_descriptor(sealed=True)
            )
            self.pages = copy.deepcopy(replayed["pages"])
            self.checkpoints = copy.deepcopy(replayed["checkpoints"])
            self.ledger = copy.deepcopy(replayed["ledger"])
            self._ledger_hasher, self._ledger_digest, _ = _ledger_hash_state(
                self.ledger
            )
        eligibility = _derive_finalize_eligibility(
            kind=self.kind,
            ledger=self.ledger,
            attempt_intent=self.attempt_intent,
            wire_attempt_count=int(report.get("wire_attempt_count", -1)),
        )
        if eligibility["finalize_eligible"] is not True:
            raise ContractError(
                "finalize_eligibility", str(eligibility["reason"])
            )
        report_bytes = _canonical_json(report)
        digest = _sha256(report_bytes)
        relative = f"reports/preflight-{digest}.json"
        _write_bytes_immutable(self.root / relative, report_bytes)
        self.preflight_report_descriptor = {"path": relative, "sha256": digest}
        self.lifecycle = "finalized"
        self._append_finalize_marker()
        if self.defer_manifest_fold:
            self._write_state_pointer()
        self._write_manifest(fold=True)
        return _read_bundle_manifest(self.root)[2]

    def finalize_run(self, result: Mapping[str, Any]) -> str:
        if self.kind != "final":
            raise ContractError("bundle_manifest", "run resultはfinal bundleだけ")
        if self.attempt_intent is not None:
            raise ContractError("bundle_pending_attempt", "未確定attempt中はrun resultをfinalizeできない")
        if self.lifecycle == "finalized" or self.finalize_marker_sha256 is not None:
            raise ContractError("bundle_finalized", "run二重finalizeを拒否")
        eligibility = _derive_finalize_eligibility(
            kind=self.kind,
            ledger=self.ledger,
            attempt_intent=self.attempt_intent,
            wire_attempt_count=int(result.get("wire_attempt_count", -1)),
        )
        if eligibility["finalize_eligible"] is not True:
            raise ContractError(
                "finalize_eligibility", str(eligibility["reason"])
            )
        result_bytes = _canonical_json(result)
        digest = _sha256(result_bytes)
        relative = f"results/run-{digest}.json"
        _write_bytes_immutable(self.root / relative, result_bytes)
        self.run_result_descriptor = {"path": relative, "sha256": digest}
        self.lifecycle = "finalized"
        self._append_finalize_marker()
        if self.defer_manifest_fold:
            self._write_state_pointer()
        self._write_manifest(fold=True)
        return _read_bundle_manifest(self.root)[2]


class HostLimiter:
    """Serialize one minimum-interval schedule per registered host."""

    def __init__(
        self,
        *,
        clock: Callable[[], datetime],
        sleeper: Callable[[float], None],
        state_path: Path | None = None,
    ) -> None:
        self._clock = clock
        self._sleeper = sleeper
        self._state_path = Path(state_path) if state_path is not None else None
        self._last_issued: dict[str, datetime] = {}
        self._active: tuple[str, datetime | None, int | None, dict[str, Any] | None] | None = None

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ContractError(
                "host_limiter_time", "host limiter時刻はtimezone付きが必要"
            )
        return value.astimezone(timezone.utc)

    @staticmethod
    def _decode_state(raw: bytes) -> dict[str, Any]:
        if not raw:
            return {
                "schema_version": _HOST_LIMITER_STATE_VERSION,
                "hosts": {},
            }
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ContractError(
                "host_limiter_state", "host limiter stateを読めない"
            ) from exc
        if (
            not isinstance(value, dict)
            or set(value) != {"schema_version", "hosts"}
            or value.get("schema_version") != _HOST_LIMITER_STATE_VERSION
            or not isinstance(value.get("hosts"), dict)
        ):
            raise ContractError(
                "host_limiter_state", "host limiter state schemaが不正"
            )
        for host, host_state in value["hosts"].items():
            if (
                host not in HOST_MINIMUM_INTERVAL_SECONDS
                or not isinstance(host_state, dict)
                or set(host_state) != {"last_issued_at"}
            ):
                raise ContractError(
                    "host_limiter_state", "host limiter host stateが不正"
                )
            _parse_time(str(host_state["last_issued_at"]))
        return value

    def _open_locked_state(self) -> tuple[int, dict[str, Any]]:
        assert self._state_path is not None
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_CLOEXEC", 0)
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor: int | None = None
        try:
            descriptor = os.open(self._state_path, flags, 0o600)
            os.fchmod(descriptor, 0o600)
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            os.lseek(descriptor, 0, os.SEEK_SET)
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            state = self._decode_state(b"".join(chunks))
            return descriptor, state
        except ContractError:
            if descriptor is not None:
                self._unlock(descriptor)
            raise
        except OSError as exc:
            if descriptor is not None:
                os.close(descriptor)
            raise ContractError(
                "host_limiter_state", "host limiter stateをlockできない"
            ) from exc

    @staticmethod
    def _unlock(descriptor: int) -> None:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)

    def acquire(self, host: str, minimum_interval_seconds: float) -> float:
        """Wait before WAL intent creation and retain the host lock until send."""

        if self._active is not None:
            raise ContractError("host_limiter_state", "host limiter leaseが既に存在する")
        if HOST_MINIMUM_INTERVAL_SECONDS.get(host) != minimum_interval_seconds:
            raise ContractError("host_limiter_host", "host最小間隔が固定値と不一致")
        descriptor: int | None = None
        state: dict[str, Any] | None = None
        if self._state_path is None:
            previous = self._last_issued.get(host)
        else:
            descriptor, state = self._open_locked_state()
            host_state = state["hosts"].get(host)
            previous = (
                _parse_time(str(host_state["last_issued_at"]))
                if isinstance(host_state, Mapping)
                else None
            )
        self._active = (host, previous, descriptor, state)
        try:
            wait_seconds = 0.0
            if previous is not None:
                wait_seconds = max(
                    0.0,
                    (previous + timedelta(seconds=minimum_interval_seconds) - self._now()).total_seconds(),
                )
                if wait_seconds:
                    self._sleeper(wait_seconds)
            return wait_seconds
        except BaseException:
            self.release()
            raise

    def issue(self, host: str) -> tuple[datetime, float | None]:
        """Take the real issue timestamp immediately before transport.send."""

        if self._active is None or self._active[0] != host:
            raise ContractError("host_limiter_state", "host limiter leaseが無い")
        previous = self._active[1]
        issued_at = self._now()
        observed = (
            None
            if previous is None
            else (issued_at - previous).total_seconds()
        )
        return issued_at, observed

    def finish_issue(self, host: str, issued_at: datetime) -> None:
        """Persist the already-observed issue time after the send call returns."""

        if self._active is None or self._active[0] != host:
            raise ContractError("host_limiter_state", "host limiter leaseが無い")
        _active_host, _previous, descriptor, state = self._active
        try:
            if descriptor is None:
                self._last_issued[host] = issued_at
                return
            assert state is not None
            state["hosts"][host] = {
                "last_issued_at": issued_at.isoformat(timespec="microseconds").replace(
                    "+00:00", "Z"
                )
            }
            payload = _canonical_json(state)
            os.lseek(descriptor, 0, os.SEEK_SET)
            os.ftruncate(descriptor, 0)
            view = memoryview(payload)
            while view:
                written = os.write(descriptor, view)
                view = view[written:]
            os.fsync(descriptor)
        except OSError as exc:
            raise ContractError(
                "host_limiter_state", "host limiter stateを永続化できない"
            ) from exc
        finally:
            self._active = None
            if descriptor is not None:
                self._unlock(descriptor)

    def release(self) -> None:
        """Release an unissued lease without changing pacing state."""

        if self._active is None:
            return
        descriptor = self._active[2]
        self._active = None
        if descriptor is not None:
            self._unlock(descriptor)


def _request_pacing(request: Mapping[str, Any]) -> tuple[str, float]:
    index = request.get("index")
    url = request.get("url")
    host = urlsplit(url).hostname if isinstance(url, str) else None
    if (
        not isinstance(index, str)
        or host != INDEX_HOSTS.get(index)
        or host not in HOST_MINIMUM_INTERVAL_SECONDS
    ):
        raise ContractError(
            "host_limiter_host", "request indexと固定pacing hostが不一致"
        )
    return host, HOST_MINIMUM_INTERVAL_SECONDS[host]


def _host_limiter(
    writer: BundleWriter | None,
    clock: Callable[[], datetime],
    sleeper: Callable[[float], None],
) -> HostLimiter:
    return HostLimiter(
        clock=clock,
        sleeper=sleeper,
        state_path=(writer.root / "state" / "host-limiter.json" if writer else None),
    )


@dataclass
class WireBudget:
    attempts: int = 0
    first_external_request_at: datetime | None = None

    @property
    def deadline_at(self) -> datetime | None:
        if self.first_external_request_at is None:
            return None
        return self.first_external_request_at + RUN_DEADLINE

    def check(self, now: datetime) -> None:
        """Validate the next attempt without changing either budget field."""

        if now.tzinfo is None or now.utcoffset() is None:
            raise ContractError("wire_budget_time", "wire attempt時刻はtimezone付きが必要")
        now = now.astimezone(timezone.utc)
        first = self.first_external_request_at or now
        if now > first + RUN_DEADLINE:
            raise ContractError("deadline_exceeded", "最初の外部requestから30日を超過")
        if self.attempts >= MAX_WIRE_ATTEMPTS:
            raise ContractError("wire_budget_exceeded", "wire attempt上限200000を超過")

    def consume(self, now: datetime) -> None:
        self.check(now)
        now = now.astimezone(timezone.utc)
        if self.first_external_request_at is None:
            self.first_external_request_at = now
        self.attempts += 1


def _send(
    transport: Any,
    request: Mapping[str, Any],
    budget: WireBudget,
    clock: Callable[[], datetime],
) -> TransportResponse:
    budget.consume(clock())
    outgoing = copy.deepcopy(dict(request))
    if type(transport) is LiveSearchSession:
        raise ContractError(
            "production_writer_receipt",
            "live session sendはwriter-bound receipt経路だけを許す",
        )
    response_value = transport.send(outgoing)
    if isinstance(response_value, TransportResponse):
        return response_value
    if not isinstance(response_value, Mapping):
        raise ContractError("transport_response", "transport responseの型が不正")
    return TransportResponse.from_mapping(response_value, strict_transport_boundary=True)


def _send_with_raw_commit(
    transport: Any,
    request: Mapping[str, Any],
    budget: WireBudget,
    clock: Callable[[], datetime],
    *,
    limiter: HostLimiter,
    writer: BundleWriter | None,
    pass_number: int,
    page_number: int,
    pacing_observations: list[dict[str, Any]] | None = None,
) -> TransportResponse:
    """Persist intent before send and raw bytes immediately after return."""

    host, minimum_interval_seconds = _request_pacing(request)
    limiter.acquire(host, minimum_interval_seconds)
    attempt_at = clock()
    try:
        budget.check(attempt_at)
        if writer is not None:
            writer.begin_attempt(
                request=request,
                pass_number=pass_number,
                page_number=page_number,
                expected_wire_attempt_count=budget.attempts + 1,
                intent_at=attempt_at,
            )
        budget.consume(attempt_at)
    except BaseException:
        limiter.release()
        raise

    outgoing = copy.deepcopy(dict(request))
    live_send = type(transport) is LiveSearchSession
    if live_send and writer is None:
        limiter.release()
        raise ContractError(
            "production_writer_receipt",
            "production sendにはlive session所有writerが必要",
        )
    live_ordinal = len(writer.ledger) + 1 if live_send and writer is not None else None
    receipt: _SendReceipt | None = None
    try:
        issued_at, observed_interval_seconds = limiter.issue(host)
        try:
            if live_send:
                assert writer is not None and live_ordinal is not None
                response_value, receipt = transport._send_with_receipt(
                    outgoing, live_ordinal
                )
            else:
                response_value = transport.send(outgoing)
        finally:
            limiter.finish_issue(host, issued_at)
    except BaseException:
        limiter.release()
        if writer is not None:
            writer.materialize_pending_attempt()
        raise
    if pacing_observations is not None:
        pacing_observations.append(
            {
                "attempt_number": budget.attempts,
                "stream_id": request["stream_id"],
                "index": request["index"],
                "host": host,
                "request_intent_at": _format_time(attempt_at),
                "minimum_interval_seconds": minimum_interval_seconds,
                "observed_interval_seconds": observed_interval_seconds,
            }
        )
    try:
        if isinstance(response_value, TransportResponse):
            response = response_value
        else:
            if not isinstance(response_value, Mapping):
                raise ContractError(
                    "transport_response", "transport responseの型が不正"
                )
            response = TransportResponse.from_mapping(
                response_value, strict_transport_boundary=True
            )
    except BaseException:
        if writer is not None:
            writer.materialize_pending_attempt()
        raise
    received_at = clock()
    if received_at.tzinfo is None or received_at.utcoffset() is None:
        raise ContractError(
            "response_received_time", "応答受領時刻はtimezone付きが必要"
        )
    response = TransportResponse(
        status=response.status,
        entity_body=response.entity_body,
        headers=response.headers,
        endpoint=response.endpoint,
        final_url=response.final_url,
        content_type=response.content_type,
        response_received_at=_format_time(received_at),
    )
    if writer is not None:
        response = writer.record_raw_response(response, receipt=receipt)
    return response


def _open_bundle_writer(transport: Any, *args: Any, **kwargs: Any) -> BundleWriter:
    if type(transport) is LiveSearchSession:
        return transport._open_writer(*args, **kwargs)
    return BundleWriter(*args, **kwargs)


def _header_values(response: TransportResponse, name: str) -> list[str]:
    return [value for key, value in response.headers if key.lower() == name.lower()]


def _validate_response_envelope(
    row: Mapping[str, Any], request: Mapping[str, Any], response: TransportResponse
) -> None:
    requested = urlsplit(request["url"])
    final = urlsplit(response.final_url)
    endpoint = urlsplit(response.endpoint)
    if (final.scheme, final.netloc, final.path) != (
        requested.scheme,
        requested.netloc,
        requested.path,
    ):
        raise ContractError("response_final_url", "final URLのscheme/host/pathがrequestと不一致")
    if (endpoint.scheme, endpoint.netloc, endpoint.path) != (
        requested.scheme,
        requested.netloc,
        requested.path,
    ):
        raise ContractError("response_endpoint", "観測endpointがrequest endpointと不一致")
    if _canonical_url(response.final_url) != _canonical_url(request["url"]):
        raise ContractError("response_final_url", "final URL canonical queryがrequestと不一致")
    if response.status == 200:
        expected_mime = (
            "application/atom+xml" if row["index"] == "arxiv" else "application/json"
        )
        actual_mime = response.content_type.split(";", 1)[0].strip().lower()
        if actual_mime != expected_mime:
            raise ContractError("response_mime", f"{row['index']} response MIMEが不一致")


def _validate_required_response_fields(
    row: Mapping[str, Any], response: TransportResponse
) -> None:
    if response.status != 200:
        return
    if row["index"] == "arxiv":
        extract_index_work_ids("arxiv", response.entity_body)
        try:
            root = ET.fromstring(response.entity_body)
        except ET.ParseError as exc:
            raise ContractError("response_required_field", "arXiv XMLが必要") from exc
        total = root.find(f"{{{OPENSEARCH_NS}}}totalResults")
        if total is None or total.text is None or not total.text.strip().isdigit():
            raise ContractError("response_required_field", "arXiv totalResultsが必要")
        expected = row.get("expected_interpreted_query")
        if expected is not None:
            _validate_arxiv_interpreted_query(str(expected), response.entity_body)
        return
    value = _decode_json_object(response.entity_body)
    if row["index"] == "openalex":
        meta = value.get("meta")
        results = value.get("results")
        if (
            not isinstance(meta, Mapping)
            or not isinstance(meta.get("count"), int)
            or isinstance(meta.get("count"), bool)
            or meta["count"] < 0
            or "next_cursor" not in meta
            or not isinstance(results, list)
        ):
            raise ContractError("response_required_field", "OpenAlex meta/results fieldが不足")
        extract_index_work_ids("openalex", response.entity_body)
        expected = row.get("expected_interpreted_query")
        if expected is not None:
            x_query = meta.get("x_query")
            raw = x_query.get("oql") if isinstance(x_query, Mapping) else None
            if not isinstance(raw, str) or not openalex_oql_matches(raw, expected):
                raise ContractError("oql_interpretation_mismatch", "OpenAlex OQL ASTが登録値と不一致")
        return
    try:
        hits = value["result"]["hits"]
        int(hits["@total"])
        int(hits["@first"])
        int(hits["@sent"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractError("response_required_field", "DBLP hits fieldが不足") from exc
    extract_index_work_ids("dblp", response.entity_body)
    expected = row.get("expected_interpreted_query")
    if expected is not None:
        _validate_dblp_interpreted_query(str(expected), value)


def _probe_response(row: Mapping[str, Any], response: TransportResponse) -> dict[str, Any]:
    if response.status != 200:
        return {
            "status": "unavailable",
            "reason": f"http_{response.status}",
            "transport_available": False,
            "lookup_resolved": None,
            "declared_total": None,
        }
    index = row["index"]
    declared_total: int
    lookup_resolved: bool | None = None
    actual_count: int
    try:
        if index == "openalex":
            value = _decode_json_object(response.entity_body)
            meta = value.get("meta")
            results = value.get("results")
            if (
                not isinstance(meta, Mapping)
                or not isinstance(meta.get("count"), int)
                or isinstance(meta.get("count"), bool)
                or meta["count"] < 0
            ):
                raise ContractError("lookup_declared_total_missing", "/meta/countが必要")
            if not isinstance(results, list):
                raise ContractError("lookup_elements_missing", "/results arrayが必要")
            declared_total = meta["count"]
            actual_count = len(results)
        elif index == "arxiv":
            try:
                root = ET.fromstring(response.entity_body)
            except ET.ParseError as exc:
                raise ContractError("lookup_elements_missing", "arXiv XMLが必要") from exc
            total = root.find(f"{{{OPENSEARCH_NS}}}totalResults")
            if total is None or total.text is None or not total.text.strip().isdigit():
                raise ContractError("lookup_declared_total_missing", "arXiv totalResultsが必要")
            declared_total = int(total.text.strip())
            actual_count = len(root.findall(f"{{{ATOM_NS}}}entry"))
        else:
            value = _decode_json_object(response.entity_body)
            try:
                hits = value["result"]["hits"]
                raw_total = hits["@total"]
                results = hits["hit"]
                declared_total = int(raw_total)
            except (KeyError, TypeError, ValueError) as exc:
                raise ContractError("lookup_declared_total_missing", "DBLP total/hitが必要") from exc
            if declared_total < 0 or not isinstance(results, list):
                raise ContractError("lookup_elements_missing", "DBLP hit arrayが必要")
            actual_count = len(results)
    except ContractError as exc:
        if row["role"] != "lookup":
            raise ContractError("preflight_response", str(exc)) from exc
        return {
            "status": "blocked",
            "reason": exc.code,
            "transport_available": True,
            "lookup_resolved": False,
            "declared_total": None,
            "actual_element_count": None,
        }

    resolved_record: dict[str, str] | None = None
    lookup_reason: str | None = None
    if row["role"] == "lookup":
        resolver_contract = row.get("resolver_contract")
        if not isinstance(resolver_contract, Mapping):
            raise ContractError("lookup_contract_missing", "lookup rowにsealed resolver契約が無い")
        cardinality = resolver_contract.get("resolution_cardinality")
        if cardinality != 1:
            raise ContractError("lookup_contract_missing", "lookup cardinalityはexact 1が必要")
        if declared_total == 0 and actual_count == 0:
            lookup_reason = str(resolver_contract["zero_reason"])
        elif declared_total > cardinality or actual_count > cardinality:
            lookup_reason = str(resolver_contract["multiple_reason"])
        elif declared_total != cardinality or actual_count != cardinality:
            lookup_reason = str(resolver_contract["cardinality_mismatch_reason"])
        else:
            try:
                resolved_record = extract_index_work_records(index, response.entity_body)[0]
            except ContractError:
                lookup_reason = str(resolver_contract["missing_reason"])
        lookup_resolved = lookup_reason is None

    status = "ready"
    reason = "preflight_ready"
    if index == "arxiv" and declared_total > 10_000:
        status = "blocked"
        reason = "arxiv_result_window_requires_new_amendment"
    if lookup_resolved is False:
        status = "blocked"
        reason = str(lookup_reason)
    result = {
        "status": status,
        "reason": reason,
        "transport_available": True,
        "lookup_resolved": lookup_resolved,
        "declared_total": declared_total,
        "actual_element_count": actual_count,
    }
    if resolved_record is not None:
        result.update(resolved_record)
    return result


def _validate_and_classify_response(
    *,
    row: Mapping[str, Any],
    request: Mapping[str, Any],
    response: TransportResponse,
    pass_number: int,
    page_number: int,
    classify_preflight: bool,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Complete all meaning gates before a raw response may be committed."""

    _validate_response_envelope(row, request, response)
    evidence = capture_page_evidence(
        stream_id=row["stream_id"],
        pass_number=pass_number,
        page_number=page_number,
        request=request,
        response=response,
        required_response_fields=row["required_response_fields"],
    )
    if response.status == 200 and row["role"] != "lookup":
        _validate_required_response_fields(row, response)
    classification = (
        _probe_response(row, response)
        if classify_preflight or row["role"] == "lookup"
        else None
    )
    return evidence, classification


def _report_digest(report: Mapping[str, Any]) -> str:
    payload = {key: value for key, value in report.items() if key != "report_sha256"}
    return _sha256(_canonical_json(payload))


def _evidence_digest(evidence: Mapping[str, Any]) -> str:
    return _sha256(_canonical_json(evidence))


def _pacing_observations_from_intents(
    intents: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Reconstruct non-gating scheduling observations from second-granularity WAL."""

    previous_by_host: dict[str, datetime] = {}
    observations: list[dict[str, Any]] = []
    for attempt_number, intent in enumerate(intents, 1):
        request = intent.get("request")
        if not isinstance(request, Mapping):
            raise ContractError("bundle_resume", "WAL intent requestが無い")
        host, minimum_interval_seconds = _request_pacing(request)
        intent_at = str(intent.get("intent_at"))
        observed_at = _parse_time(intent_at)
        previous = previous_by_host.get(host)
        observations.append(
            {
                "attempt_number": attempt_number,
                "stream_id": request["stream_id"],
                "index": request["index"],
                "host": host,
                "request_intent_at": intent_at,
                "minimum_interval_seconds": minimum_interval_seconds,
                "observed_interval_seconds": (
                    None
                    if previous is None
                    else (observed_at - previous).total_seconds()
                ),
            }
        )
        previous_by_host[host] = observed_at
    return observations


def _preflight_row_base(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "stream_id": row["stream_id"],
        "index": row["index"],
        "role": row["role"],
        "registration_row_sha256": _sha256(_canonical_json(row)),
        "attempted": False,
        "attempt_number": None,
        "evidence_sha256": None,
    }


def _finish_report(report: dict[str, Any]) -> dict[str, Any]:
    report["status_counts"] = {
        status: sum(row["status"] == status for row in report["rows"])
        for status in ("ready", "unavailable", "blocked")
    }
    report["all_rows_accounted"] = len({row["stream_id"] for row in report["rows"]}) == len(
        report["rows"]
    )
    report["axis_complete"] = False
    report["preflight_evidence_sha256"] = _sha256(
        _canonical_json(report["preflight_evidence"])
    )
    report["report_sha256"] = _report_digest(report)
    return report


def _finalize_preflight_report(
    report: dict[str, Any],
    catalog: Mapping[str, Any],
    seal: Mapping[str, Any],
) -> dict[str, Any]:
    """Finalize, serialize, read back, and validate a complete report in memory."""

    finished = _finish_report(report)
    restored = json.loads(_canonical_json(finished).decode("utf-8"))
    validate_preflight_report(restored, catalog, seal)
    if restored != finished:
        raise ContractError(
            "preflight_report", "finalized reportのread-backがproducer値と不一致"
        )
    return finished


def _validate_preflight_wal_attempt_sequence(
    catalog: Mapping[str, Any], evidences: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Require the registered plan prefix and at most three inline attempts."""

    rows_by_id = {row["stream_id"]: row for row in catalog["rows"]}
    planned_ids = _preflight_planned_stream_ids(catalog)
    history: list[Mapping[str, Any]] = []
    initial_offset = 0
    current_stream_id: str | None = None
    current_stream_attempts = 0

    def retry_stream_id() -> str | None:
        if (
            not history
            or history[-1].get("status") not in RETRYABLE_HTTP_STATUSES
            or current_stream_attempts >= MAX_PREFLIGHT_ATTEMPTS_PER_STREAM
        ):
            return None
        return current_stream_id

    for evidence in evidences:
        stream_id = evidence.get("stream_id")
        if stream_id not in rows_by_id:
            raise ContractError(
                "bundle_preflight_sequence", "WAL attempt streamがcatalogに無い"
            )
        if stream_id == current_stream_id:
            if (
                not history
                or history[-1].get("status") not in RETRYABLE_HTTP_STATUSES
                or current_stream_attempts >= MAX_PREFLIGHT_ATTEMPTS_PER_STREAM
            ):
                raise ContractError(
                    "bundle_preflight_sequence",
                    "同一preflight streamのattempt上限またはretry順が不正",
                )
            current_stream_attempts += 1
            history.append(evidence)
            continue
        if initial_offset >= len(planned_ids) or stream_id != planned_ids[initial_offset]:
            raise ContractError(
                "bundle_preflight_sequence",
                "WAL attemptが登録preflight planの完了prefixでない",
            )
        initial_offset += 1
        current_stream_id = str(stream_id)
        current_stream_attempts = 1
        history.append(evidence)

    next_initial = (
        planned_ids[initial_offset]
        if initial_offset < len(planned_ids)
        else None
    )
    return {
        "planned_stream_ids": planned_ids,
        "initial_plan_complete": initial_offset == len(planned_ids),
        "next_initial_stream_id": next_initial,
        "retry_stream_id": retry_stream_id(),
        "current_stream_attempts": current_stream_attempts,
    }


def _preflight_planned_stream_ids(catalog: Mapping[str, Any]) -> list[str]:
    """Return the exact registered preflight order without executing transport."""

    availability_id = "AX3A1-L-ID-01@openalex"
    return [
        availability_id,
        *(
            row["stream_id"]
            for row in catalog["rows"]
            if row["stream_id"] != availability_id
            and row["request_factory"]["state"] == "complete"
        ),
    ]


def _ordered_ready_rows(
    catalog: Mapping[str, Any], statuses: Mapping[str, str]
) -> list[Mapping[str, Any]]:
    """Return every ready row in the frozen arXiv/OpenAlex/DBLP order."""

    rank = {"arxiv": 0, "openalex": 1, "dblp": 2}
    return sorted(
        (
            row
            for row in catalog["rows"]
            if statuses.get(row["stream_id"]) == "ready"
        ),
        key=lambda row: (rank[row["index"]], row["stream_id"]),
    )


def _derive_preflight_report_from_wal(
    *,
    catalog: Mapping[str, Any],
    seal: Mapping[str, Any],
    evidences: Sequence[Mapping[str, Any]],
    bodies: Sequence[bytes],
    intents: Sequence[Mapping[str, Any]],
    origin_phase_argv: Mapping[str, Any],
    stopped_initial_availability_429: bool,
    stop_checkpoint: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not evidences or not (
        len(evidences) == len(bodies) == len(intents)
    ):
        raise ContractError("bundle_resume", "preflight WAL material件数が不一致")
    _validate_preflight_wal_attempt_sequence(catalog, evidences)
    expected_origin = validate_effective_phase_argv(
        origin_phase_argv.get("effective_argv", []), "preflight"
    )
    if dict(origin_phase_argv) != expected_origin:
        raise ContractError("bundle_phase_argv", "preflight origin argvが不正")
    rows_by_id = {row["stream_id"]: row for row in catalog["rows"]}
    availability_id = "AX3A1-L-ID-01@openalex"
    report_rows: dict[str, dict[str, Any]] = {}
    for row in catalog["rows"]:
        complete = row["request_factory"]["state"] == "complete"
        report_rows[row["stream_id"]] = {
            **_preflight_row_base(row),
            "status": "blocked",
            "reason": (
                "preflight_stopped_after_openalex_429"
                if complete and stopped_initial_availability_429
                else row["request_factory"].get(
                    "blocked_reason", "preflight_attempt_not_committed"
                )
            ),
            "transport_available": None,
            "lookup_resolved": None,
            "declared_total": None,
            "preflight_response_reusable_for_run": False,
        }
    for attempt_number, (evidence, body, intent) in enumerate(
        zip(evidences, bodies, intents), 1
    ):
        stream_id = evidence.get("stream_id")
        row = rows_by_id.get(stream_id)
        if row is None or row["request_factory"]["state"] != "complete":
            raise ContractError("bundle_resume", "WAL attempt rowが送信可能catalog rowでない")
        if (
            evidence.get("pass_number") != 0
            or evidence.get("page_number") != 0
            or evidence.get("request") != materialize_request(row)
            or intent.get("ordinal") != attempt_number
            or intent.get("expected_wire_attempt_count") != attempt_number
            or intent.get("request") != evidence.get("request")
        ):
            raise ContractError("bundle_resume", "WAL preflight attempt identityが不一致")
        response = _response_from_evidence(evidence, body)
        _validate_response_envelope(row, evidence["request"], response)
        if response.status == 200 and row["role"] != "lookup":
            _validate_required_response_fields(row, response)
        report_rows[stream_id] = {
            **_preflight_row_base(row),
            **_probe_response(row, response),
            "entity_body_sha256": _sha256(body),
            "attempted": True,
            "attempt_number": attempt_number,
            "evidence_sha256": _evidence_digest(evidence),
            "preflight_response_reusable_for_run": False,
        }
    if evidences[0].get("stream_id") != availability_id:
        raise ContractError("bundle_resume", "WAL先頭が固定availability IDでない")
    if stopped_initial_availability_429:
        if len(evidences) != 1 or evidences[0].get("status") != 429:
            raise ContractError("bundle_resume", "最初のavailability 429だけがstop reportになれる")
        if not isinstance(stop_checkpoint, Mapping):
            raise ContractError("bundle_resume", "availability 429 stop checkpointが無い")
    elif any(
        row["request_factory"]["state"] == "complete"
        and report_rows[row["stream_id"]]["attempted"] is not True
        for row in catalog["rows"]
    ):
        raise ContractError("bundle_resume", "未attempt complete rowをfinalizeできない")
    first = _parse_time(str(intents[0].get("intent_at")))
    report = {
        "schema_version": PREFLIGHT_REPORT_VERSION,
        "registration_seal_sha256": seal["seal_sha256"],
        "catalog_sha256": seal["catalog_sha256"],
        "rows": [report_rows[row["stream_id"]] for row in catalog["rows"]],
        "preflight_evidence": copy.deepcopy(list(evidences)),
        "pacing_observations": _pacing_observations_from_intents(intents),
        "wire_attempt_count": len(evidences),
        "first_external_request_at": _format_time(first),
        "deadline_at": _format_time(first + RUN_DEADLINE),
        "availability_evidence": copy.deepcopy(dict(evidences[0])),
        "checkpoint": copy.deepcopy(dict(stop_checkpoint)) if stop_checkpoint else None,
        "stopped_after_openalex_429": stopped_initial_availability_429,
        "effective_argv": copy.deepcopy(origin_phase_argv["effective_argv"]),
        "effective_argv_sha256": origin_phase_argv["effective_argv_sha256"],
        "phase_argv_contract_sha256": origin_phase_argv[
            "phase_argv_contract_sha256"
        ],
    }
    return _finalize_preflight_report(report, catalog, seal)


def _quota_checkpoint(
    *,
    row: Mapping[str, Any],
    request: Mapping[str, Any],
    response: TransportResponse,
    seal: Mapping[str, Any],
    budget: WireBudget,
    now: datetime,
) -> dict[str, Any]:
    assert budget.first_external_request_at is not None
    remaining_values = _header_values(response, "X-RateLimit-Remaining")
    retry_values = _header_values(response, "Retry-After")
    remaining = (
        int(remaining_values[-1])
        if remaining_values and remaining_values[-1].isdigit()
        else None
    )
    source_digests = {entry["path"]: entry["sha256"] for entry in seal["source_digests"]}
    return {
        "schema_version": CHECKPOINT_VERSION,
        "resume_action": "restart_branch",
        "registration_seal_sha256": seal["seal_sha256"],
        "catalog_sha256": seal["catalog_sha256"],
        "parser_sha256": source_digests["orchestrator/related_work_search.py"],
        "runner_sha256": source_digests["tools/run_axis3_search.py"],
        "schema_sha256": _sha256(_canonical_json(seal["schema_digests"])),
        "run_id": "axis3-live-preflight",
        "stream_id": row["stream_id"],
        "index": row["index"],
        "pass_number": 1,
        "pass_kind": "fixed",
        "window_number": 1,
        "state": "quota_wait",
        "page_identity": {"stream_id": row["stream_id"], "pass_number": 1, "page_number": 0},
        "last_committed_page": -1,
        "ledger_prefix_sha256": EMPTY_SHA256,
        "previous_checkpoint_sha256": None,
        "wire_attempt_count": budget.attempts,
        "first_external_request_at": _format_time(budget.first_external_request_at),
        "deadline_at": _format_time(budget.first_external_request_at + RUN_DEADLINE),
        "quota_observed_at": _format_time(now),
        "quota_remaining": remaining,
        "retry_after": retry_values[-1] if retry_values else None,
        "continue_cursor_request": _request_without_stream(request),
        "start_independent_pass_request": _branch_start_checkpoint_request(row),
        "restart_branch_request": _branch_start_checkpoint_request(row),
        "failed_ledger_sha256": _sha256(response.entity_body),
    }


def run_preflight(
    catalog: Mapping[str, Any],
    catalog_data: bytes,
    seal: Mapping[str, Any],
    *,
    argv: Sequence[str],
    commit: str,
    transport: Any,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    sleeper: Callable[[float], None] = time.sleep,
    checkpoint_path: Path | None = None,
    bundle_dir: Path | None = None,
    repo_root: Path = REPO_ROOT,
    source_paths: Sequence[Path] = SOURCE_PATHS,
    schema_paths: Sequence[Path] = SCHEMA_PATHS,
    effective_argv: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Run live page-0 probes only after the registration closure is valid."""

    if type(transport) is LiveSearchSession and bundle_dir is None:
        raise ContractError("bundle_preflight", "live preflightはraw bundle無しで実行できない")
    validate_catalog(catalog)
    observed_argv = list(effective_argv if effective_argv is not None else argv)
    phase_argv = validate_effective_phase_argv(observed_argv, "preflight")
    _bind_transport_semantics(phase_argv, transport)
    _bind_semantic_path(phase_argv, "--bundle", bundle_dir)
    _bind_semantic_path(phase_argv, "--checkpoint", checkpoint_path)
    if bundle_dir is not None and phase_argv["artifact_class"] != "production":
        raise ContractError(
            "bundle_nonproduction",
            "simulation transportはtop-level preflight bundleを発行できない",
        )
    validate_registration_seal(
        seal,
        catalog_data,
        argv=argv,
        commit=commit,
        repo_root=repo_root,
        source_paths=source_paths,
        schema_paths=schema_paths,
        enforce_head=phase_argv["artifact_class"] == "production",
    )
    writer = (
        _open_bundle_writer(
            transport,
            bundle_dir,
            kind="preflight",
            seal=seal,
            phase_argv=phase_argv,
            defer_manifest_fold=True,
        )
        if bundle_dir is not None
        else None
    )
    budget = WireBudget()
    limiter = _host_limiter(writer, clock, sleeper)
    pacing_observations: list[dict[str, Any]] = []
    rows_by_id = {row["stream_id"]: row for row in catalog["rows"]}
    availability_id = "AX3A1-L-ID-01@openalex"
    availability_row = rows_by_id[availability_id]
    preflight_evidence: list[dict[str, Any]] = []

    def attempt_row(
        row: Mapping[str, Any], *, initial_availability: bool = False
    ) -> tuple[TransportResponse, dict[str, Any], dict[str, Any], Mapping[str, Any] | None]:
        request = materialize_request(row)
        response = _send_with_raw_commit(
            transport,
            request,
            budget,
            clock,
            limiter=limiter,
            writer=writer,
            pass_number=0,
            page_number=0,
            pacing_observations=pacing_observations,
        )
        try:
            evidence, probe = _validate_and_classify_response(
                row=row,
                request=request,
                response=response,
                pass_number=0,
                page_number=0,
                classify_preflight=True,
            )
        except ContractError:
            if writer is not None:
                writer.materialize_pending_attempt()
            raise
        assert probe is not None
        preflight_evidence.append(evidence)
        checkpoint: Mapping[str, Any] | None = None
        if initial_availability and response.status == 429 and budget.attempts == 1:
            checkpoint = _quota_checkpoint(
                row=row,
                request=request,
                response=response,
                seal=seal,
                budget=budget,
                now=clock(),
            )
        elif response.status != 200:
            checkpoint = _response_checkpoint(
                row=row,
                request=request,
                response=response,
                seal=seal,
                budget=budget,
                now=clock(),
                run_id="axis3-live-preflight",
                pass_number=1,
                page_number=0,
                next_request=None,
            )
        if writer is not None:
            checkpoint = writer.commit_response(
                evidence=evidence,
                entity_body=response.entity_body,
                checkpoint=checkpoint,
            )
        return response, evidence, probe, checkpoint

    def finish_retries(
        row: Mapping[str, Any],
        response: TransportResponse,
        evidence: dict[str, Any],
        probe: dict[str, Any],
    ) -> tuple[TransportResponse, dict[str, Any], dict[str, Any]]:
        attempts_for_row = 1
        while (
            response.status in RETRYABLE_HTTP_STATUSES
            and attempts_for_row < MAX_PREFLIGHT_ATTEMPTS_PER_STREAM
        ):
            sleeper(PREFLIGHT_RETRY_BACKOFF_SECONDS[str(row["index"])][attempts_for_row - 1])
            response, evidence, probe, _checkpoint = attempt_row(row)
            attempts_for_row += 1
        return response, evidence, probe

    (
        availability_response,
        availability_evidence,
        availability_probe,
        availability_checkpoint,
    ) = attempt_row(availability_row, initial_availability=True)

    report_rows: dict[str, dict[str, Any]] = {}
    if availability_response.status == 429:
        for row in catalog["rows"]:
            factory_state = row["request_factory"]["state"]
            report_rows[row["stream_id"]] = {
                **_preflight_row_base(row),
                "status": "blocked",
                "reason": (
                    row["request_factory"].get("blocked_reason", "preflight_stopped_after_openalex_429")
                    if factory_state != "complete"
                    else "preflight_stopped_after_openalex_429"
                ),
                "transport_available": None,
                "lookup_resolved": None,
                "declared_total": None,
                "preflight_response_reusable_for_run": False,
            }
        report_rows[availability_id].update(
            status="unavailable",
            reason="http_429",
            transport_available=False,
            entity_body_sha256=_sha256(availability_response.entity_body),
            attempted=True,
            attempt_number=1,
            evidence_sha256=_evidence_digest(availability_evidence),
        )
        checkpoint = availability_checkpoint
        assert checkpoint is not None
        validate_checkpoint(checkpoint)
        if checkpoint_path is not None:
            write_checkpoint_atomic(checkpoint_path, checkpoint)
        report = {
            "schema_version": PREFLIGHT_REPORT_VERSION,
            "registration_seal_sha256": seal["seal_sha256"],
            "catalog_sha256": seal["catalog_sha256"],
            "rows": [report_rows[row["stream_id"]] for row in catalog["rows"]],
            "preflight_evidence": preflight_evidence,
            "pacing_observations": pacing_observations,
            "wire_attempt_count": budget.attempts,
            "first_external_request_at": _format_time(budget.first_external_request_at),
            "deadline_at": _format_time(budget.deadline_at),
            "availability_evidence": availability_evidence,
            "checkpoint": checkpoint,
            "stopped_after_openalex_429": True,
            "effective_argv": observed_argv,
            "effective_argv_sha256": _sha256(_canonical_json(observed_argv)),
            "phase_argv_contract_sha256": phase_argv[
                "phase_argv_contract_sha256"
            ],
        }
        finished = _finalize_preflight_report(report, catalog, seal)
        if writer is not None:
            writer._write_state_pointer()
        return finished

    availability_response, availability_latest_evidence, availability_probe = finish_retries(
        availability_row,
        availability_response,
        availability_evidence,
        availability_probe,
    )
    assert availability_probe is not None
    report_rows[availability_id] = {
        **_preflight_row_base(availability_row),
        **availability_probe,
        "entity_body_sha256": _sha256(availability_response.entity_body),
        "attempted": True,
        "attempt_number": budget.attempts,
        "evidence_sha256": _evidence_digest(availability_latest_evidence),
        "preflight_response_reusable_for_run": False,
    }
    for row_offset, row in enumerate(catalog["rows"]):
        stream_id = row["stream_id"]
        if stream_id == availability_id:
            continue
        if row["request_factory"]["state"] != "complete":
            report_rows[stream_id] = {
                **_preflight_row_base(row),
                "status": "blocked",
                "reason": row["request_factory"]["blocked_reason"],
                "transport_available": None,
                "lookup_resolved": None,
                "declared_total": None,
                "preflight_response_reusable_for_run": False,
            }
            continue
        response, evidence, probe, _checkpoint = attempt_row(row)
        response, evidence, probe = finish_retries(row, response, evidence, probe)
        assert probe is not None
        report_rows[stream_id] = {
            **_preflight_row_base(row),
            **probe,
            "entity_body_sha256": _sha256(response.entity_body),
            "attempted": True,
            "attempt_number": budget.attempts,
            "evidence_sha256": _evidence_digest(evidence),
            "preflight_response_reusable_for_run": False,
        }
        if (
            row["index"] == "dblp"
            and response.status in RETRYABLE_HTTP_STATUSES
            and any(
                later["request_factory"]["state"] == "complete"
                for later in catalog["rows"][row_offset + 1 :]
            )
        ):
            sleeper(DBLP_FAILURE_COOLDOWN_SECONDS)
    report = {
        "schema_version": PREFLIGHT_REPORT_VERSION,
        "registration_seal_sha256": seal["seal_sha256"],
        "catalog_sha256": seal["catalog_sha256"],
        "rows": [report_rows[row["stream_id"]] for row in catalog["rows"]],
        "preflight_evidence": preflight_evidence,
        "pacing_observations": pacing_observations,
        "wire_attempt_count": budget.attempts,
        "first_external_request_at": _format_time(budget.first_external_request_at),
        "deadline_at": _format_time(budget.deadline_at),
        "availability_evidence": availability_evidence,
        "checkpoint": None,
        "stopped_after_openalex_429": False,
        "effective_argv": observed_argv,
        "effective_argv_sha256": _sha256(_canonical_json(observed_argv)),
        "phase_argv_contract_sha256": phase_argv["phase_argv_contract_sha256"],
    }
    finished = _finalize_preflight_report(report, catalog, seal)
    if writer is not None:
        eligibility = _derive_finalize_eligibility(
            kind="preflight",
            ledger=writer.ledger,
            attempt_intent=writer.attempt_intent,
            wire_attempt_count=budget.attempts,
        )
        if eligibility["finalize_eligible"] is True:
            writer.finalize_preflight(finished)
            load_preflight_bundle(
                bundle_dir,
                catalog,
                seal,
            )
        else:
            writer._write_state_pointer()
    return finished


def validate_preflight_report(
    report: Mapping[str, Any], catalog: Mapping[str, Any], seal: Mapping[str, Any]
) -> None:
    errors = sorted(
        Draft7Validator(PREFLIGHT_REPORT_SCHEMA).iter_errors(report),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        raise ContractError("preflight_report_schema", errors[0].message)
    if report.get("registration_seal_sha256") != seal.get("seal_sha256"):
        raise ContractError("preflight_report", "registration sealとの束縛が不一致")
    if report.get("catalog_sha256") != seal.get("catalog_sha256"):
        raise ContractError("preflight_report", "catalog bytesとの束縛が不一致")
    if report.get("effective_argv_sha256") != _sha256(
        _canonical_json(report.get("effective_argv"))
    ):
        raise ContractError("preflight_argv", "実効argv digestが不一致")
    phase_argv = validate_effective_phase_argv(report.get("effective_argv", []), "preflight")
    if report.get("phase_argv_contract_sha256") != phase_argv[
        "phase_argv_contract_sha256"
    ]:
        raise ContractError("preflight_argv", "preflight phase argv contractが不一致")
    rows = report.get("rows")
    assert isinstance(rows, list)
    expected_ids = [row["stream_id"] for row in catalog["rows"]]
    actual_ids = [row.get("stream_id") for row in rows if isinstance(row, Mapping)]
    if actual_ids != expected_ids or len(set(actual_ids)) != len(expected_ids):
        raise ContractError("preflight_accounting", "catalog全logical rowの一意accountingが必要")
    if any(row.get("status") not in {"ready", "unavailable", "blocked"} for row in rows):
        raise ContractError("preflight_status", "行statusはready/unavailable/blockedだけ")
    status_counts = {
        status: sum(row.get("status") == status for row in rows)
        for status in ("ready", "unavailable", "blocked")
    }
    if report.get("status_counts") != status_counts:
        raise ContractError("preflight_status_counts", "status_countsがrowsと不一致")
    attempts = report.get("wire_attempt_count")
    if isinstance(attempts, bool) or not isinstance(attempts, int) or not 0 <= attempts <= MAX_WIRE_ATTEMPTS:
        raise ContractError("preflight_wire_attempts", "wire attemptは非負かつ上限以下が必要")
    first = _parse_time(report["first_external_request_at"])
    deadline = _parse_time(report["deadline_at"])
    if deadline - first != RUN_DEADLINE:
        raise ContractError("preflight_deadline", "deadlineは最初の外部requestからちょうど30日")
    evidence_values = report.get("preflight_evidence")
    assert isinstance(evidence_values, list)
    if len(evidence_values) != attempts:
        raise ContractError("preflight_wire_attempts", "全wire attemptにevidenceが1件必要")
    pacing_values = report.get("pacing_observations")
    assert isinstance(pacing_values, list)
    if len(pacing_values) != attempts:
        raise ContractError(
            "preflight_pacing", "全wire attemptにpacing observationが1件必要"
        )
    for attempt_number, (observation, evidence) in enumerate(
        zip(pacing_values, evidence_values), 1
    ):
        if not isinstance(observation, Mapping) or not isinstance(evidence, Mapping):
            raise ContractError(
                "preflight_pacing", "pacing observationとevidenceはobjectが必要"
            )
        request = evidence.get("request")
        if not isinstance(request, Mapping):
            raise ContractError("preflight_evidence", "evidence requestが無い")
        host, minimum_interval_seconds = _request_pacing(request)
        if (
            observation.get("attempt_number") != attempt_number
            or observation.get("stream_id") != evidence.get("stream_id")
            or observation.get("index") != request.get("index")
            or observation.get("host") != host
            or observation.get("minimum_interval_seconds")
            != minimum_interval_seconds
        ):
            raise ContractError(
                "preflight_pacing", "pacing observation順がevidenceと不一致"
            )
        _parse_time(str(observation.get("request_intent_at")))
    _validate_preflight_wal_attempt_sequence(catalog, evidence_values)
    evidence_by_stream: dict[str, list[tuple[int, Mapping[str, Any]]]] = {}
    for attempt_number, evidence in enumerate(evidence_values, 1):
        if not isinstance(evidence, Mapping):
            raise ContractError("preflight_evidence", "preflight evidenceはobjectが必要")
        _validate_with_schema(evidence, SCHEMA_PATHS[2])
        stream_id = evidence.get("stream_id")
        if not isinstance(stream_id, str):
            raise ContractError("preflight_evidence", "preflight evidenceにstream IDが必要")
        if evidence.get("pass_number") != 0 or evidence.get("page_number") != 0:
            raise ContractError("preflight_evidence", "preflight evidenceはpass/page 0が必要")
        evidence_by_stream.setdefault(stream_id, []).append((attempt_number, evidence))
    attempt_numbers: list[int] = []
    for preflight_row, catalog_row in zip(rows, catalog["rows"]):
        if preflight_row.get("registration_row_sha256") != _sha256(
            _canonical_json(catalog_row)
        ):
            raise ContractError("preflight_registration_row", "rowがregistration catalogと不一致")
        if preflight_row["status"] == "ready" and catalog_row["request_factory"]["state"] != "complete":
            raise ContractError("preflight_status", "未解決request factoryをreadyにできない")
        if preflight_row.get("preflight_response_reusable_for_run") is not False:
            raise ContractError("preflight_reuse", "live preflight responseを本走page0へ再利用できない")
        attempted = preflight_row.get("attempted")
        if not isinstance(attempted, bool):
            raise ContractError("preflight_attempt", "attempted booleanが必要")
        stream_evidence = evidence_by_stream.get(preflight_row["stream_id"], [])
        latest = stream_evidence[-1] if stream_evidence else None
        evidence = latest[1] if latest is not None else None
        if attempted:
            number = preflight_row.get("attempt_number")
            if isinstance(number, bool) or not isinstance(number, int):
                raise ContractError("preflight_attempt", "attempted rowにattempt numberが必要")
            attempt_numbers.append(number)
            if latest is None or number != latest[0]:
                raise ContractError("preflight_attempt", "row attempt numberが最新attemptと不一致")
            if evidence is None or preflight_row.get("evidence_sha256") != _evidence_digest(evidence):
                raise ContractError("preflight_evidence", "row evidence digestが保存attemptと不一致")
            provenance = evidence["alternative_provenance"]
            if preflight_row.get("entity_body_sha256") != provenance["entity_body_sha256"]:
                raise ContractError("preflight_evidence", "row body digestがevidenceと不一致")
            if evidence["status"] != 200 and preflight_row["status"] != "unavailable":
                raise ContractError("preflight_status", "non-200 attemptをready/blockedにできない")
            if evidence["status"] == 200 and preflight_row["status"] == "unavailable":
                raise ContractError("preflight_status", "200 attemptをunavailableにできない")
            if preflight_row["status"] == "ready" and preflight_row.get("transport_available") is not True:
                raise ContractError("preflight_status", "ready rowはtransport availableが必要")
            if catalog_row["role"] == "lookup" and preflight_row["status"] == "ready":
                if (
                    preflight_row.get("lookup_resolved") is not True
                    or preflight_row.get("declared_total") != 1
                    or preflight_row.get("actual_element_count") != 1
                    or not isinstance(preflight_row.get("index_work_id"), str)
                    or not isinstance(preflight_row.get("raw_index_work_id"), str)
                ):
                    raise ContractError("preflight_lookup", "lookup readyはexact one resolvedが必要")
        else:
            if stream_evidence or preflight_row.get("evidence_sha256") is not None:
                raise ContractError("preflight_evidence", "未attempt rowにevidenceを付けられない")
            if preflight_row.get("attempt_number") is not None:
                raise ContractError("preflight_attempt", "未attempt rowのattempt numberはnull")
            if preflight_row["status"] != "blocked":
                raise ContractError("preflight_status", "未attempt rowはblockedだけ")
        if catalog_row["request_factory"]["state"] != "complete" and attempted:
            raise ContractError("preflight_attempt", "blocked factoryへwire attemptできない")
    if any(number < 1 or number > attempts for number in attempt_numbers):
        raise ContractError("preflight_attempt", "row latest attempt numberがwire範囲外")
    stopped_after_429 = report.get("stopped_after_openalex_429") is True
    availability_id = "AX3A1-L-ID-01@openalex"
    if (
        not evidence_values
        or evidence_values[0].get("stream_id") != availability_id
        or report.get("availability_evidence") != evidence_values[0]
    ):
        raise ContractError(
            "preflight_availability",
            "availability evidenceは固定IDの最初の保存raw attemptが必要",
        )
    if stopped_after_429:
        if len(evidence_values) != 1 or any(
            evidence.get("stream_id") != availability_id
            or evidence.get("status") != 429
            for evidence in evidence_values
        ):
            raise ContractError(
                "preflight_stop_boundary",
                "OpenAlex 429 stop reportにavailability以外のattemptを含められない",
            )
        if any(
            row.get("attempted") is True and row.get("stream_id") != availability_id
            for row in rows
        ):
            raise ContractError(
                "preflight_stop_boundary",
                "OpenAlex 429後に別rowをattempt済みにできない",
            )
    else:
        for preflight_row, catalog_row in zip(rows, catalog["rows"]):
            expected_attempted = catalog_row["request_factory"]["state"] == "complete"
            if preflight_row.get("attempted") is not expected_attempted:
                raise ContractError(
                    "preflight_attempt",
                    "非停止preflightは全complete factoryをexact一度以上attemptする",
                )
    if report.get("preflight_evidence_sha256") != _sha256(_canonical_json(evidence_values)):
        raise ContractError("preflight_evidence", "attempt evidence集合digestが不一致")
    if report.get("axis_complete") is not False:
        raise ContractError("axis_completion", "ready行の存在を軸完走に読み替えられない")
    if report.get("report_sha256") != _report_digest(report):
        raise ContractError("preflight_report_digest", "preflight report digestが不一致")


def _page_progress(
    row: Mapping[str, Any], response: TransportResponse, position: int | str | None
) -> tuple[int, int | str | None, bool]:
    index = row["index"]
    page_size = row["request_factory"]["page_size"]
    if index == "openalex":
        value = _decode_json_object(response.entity_body)
        meta = value.get("meta")
        results = value.get("results")
        if (
            not isinstance(meta, Mapping)
            or not isinstance(meta.get("count"), int)
            or isinstance(meta.get("count"), bool)
            or meta["count"] < 0
            or not isinstance(results, list)
        ):
            raise ContractError("run_response", "OpenAlex meta/resultsが必要")
        actual_count = len(results)
        if row["completion_kind"] == "count_only":
            return meta["count"], None, True
        next_cursor = meta.get("next_cursor")
        if next_cursor is None:
            return meta["count"], None, True
        if not isinstance(next_cursor, str) or not next_cursor:
            raise ContractError("run_response", "next_cursorは非空文字列またはnull")
        if actual_count == 0:
            raise ContractError("page_empty_progress", "OpenAlex cursorがある空pageを拒否")
        if actual_count != page_size:
            raise ContractError("page_short_nonterminal", "OpenAlex非終端pageが要求件数未満")
        next_position = quote(next_cursor, safe="")
        if position is not None and next_position == str(position):
            raise ContractError("page_cursor_repeated", "OpenAlex cursor反復を拒否")
        return meta["count"], next_position, False
    if index == "arxiv":
        try:
            root = ET.fromstring(response.entity_body)
        except ET.ParseError as exc:
            raise ContractError("run_response", "arXiv XMLが必要") from exc
        total_element = root.find(f"{{{OPENSEARCH_NS}}}totalResults")
        if total_element is None or total_element.text is None:
            raise ContractError("run_response", "arXiv totalResultsが必要")
        try:
            total = int(total_element.text.strip())
        except ValueError as exc:
            raise ContractError("run_response", "arXiv totalResults整数が必要") from exc
        if total < 0:
            raise ContractError("run_response", "arXiv totalResultsは非負が必要")
        count = len(root.findall(f"{{{ATOM_NS}}}entry"))
        current = int(position or 0)
        if row["completion_kind"] == "count_only":
            return total, None, True
        start_element = root.find(f"{{{OPENSEARCH_NS}}}startIndex")
        items_element = root.find(f"{{{OPENSEARCH_NS}}}itemsPerPage")
        if row["role"] == "main" and total > 0:
            try:
                response_position = int(start_element.text.strip())  # type: ignore[union-attr]
                response_requested = int(items_element.text.strip())  # type: ignore[union-attr]
            except (AttributeError, ValueError) as exc:
                raise ContractError(
                    "page_response_position_missing",
                    "arXiv main pageはstartIndex/itemsPerPageが必要",
                ) from exc
            if response_position != current:
                raise ContractError("page_response_position", "arXiv response位置がrequestと不一致")
            if response_requested != page_size:
                raise ContractError("page_requested_count", "arXiv itemsPerPageが要求件数と不一致")
        if current + count > total:
            raise ContractError("page_declared_total", "arXiv pageが宣言総数を超過")
        terminal = current + count == total
        if not terminal and count != page_size:
            raise ContractError("page_short_nonterminal", "arXiv非終端pageが要求件数未満")
        if not terminal and count == 0:
            raise ContractError("page_empty_progress", "arXiv空進行を拒否")
        return total, None if terminal else current + count, terminal
    value = _decode_json_object(response.entity_body)
    try:
        hits = value["result"]["hits"]
        total = int(hits["@total"])
        first = int(hits["@first"])
        sent = int(hits["@sent"])
        actual_count = len(hits["hit"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractError("run_response", "DBLP hits total/first/sent/hitが必要") from exc
    if total < 0 or first < 0 or sent < 0:
        raise ContractError("run_response", "DBLP total/first/sentは非負が必要")
    current = int(position or 0)
    if row["completion_kind"] == "count_only":
        return total, None, True
    if first != current:
        raise ContractError("page_response_position", "DBLP @firstがrequest offsetと不一致")
    if sent != actual_count:
        raise ContractError("page_actual_count", "DBLP @sentが実hit数と不一致")
    if current + actual_count > total:
        raise ContractError("page_declared_total", "DBLP pageが宣言総数を超過")
    terminal = current + actual_count == total
    if not terminal and actual_count != page_size:
        raise ContractError("page_short_nonterminal", "DBLP非終端pageが要求件数未満")
    if not terminal and actual_count == 0:
        raise ContractError("page_empty_progress", "DBLP空進行を拒否")
    return total, None if terminal else current + actual_count, terminal


def _run_stream(
    row: Mapping[str, Any],
    transport: Any,
    budget: WireBudget,
    clock: Callable[[], datetime],
    *,
    limiter: HostLimiter,
    writer: BundleWriter | None = None,
    seal: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    pages = []
    completion_pages = []
    position: int | str | None = None
    page_number = 0
    seen_requests: set[tuple[str, str, int | None, str, tuple[tuple[str, str], ...]]] = set()
    while True:
        request = materialize_request(row, position)
        request_identity = _canonical_url(request["url"])
        if request_identity in seen_requests:
            raise ContractError("page_request_repeated", "同一page requestの反復を拒否")
        seen_requests.add(request_identity)
        response = _send_with_raw_commit(
            transport,
            request,
            budget,
            clock,
            limiter=limiter,
            writer=writer,
            pass_number=1,
            page_number=page_number,
        )
        evidence, lookup_probe = _validate_and_classify_response(
            row=row,
            request=request,
            response=response,
            pass_number=1,
            page_number=page_number,
            classify_preflight=False,
        )
        pages.append(evidence)
        if response.status != 200:
            checkpoint = None
            if writer is not None:
                if seal is None:
                    raise ContractError("bundle_writer", "bundle writerにregistration sealが必要")
                checkpoint = writer.commit_response(
                    evidence=evidence,
                    entity_body=response.entity_body,
                    checkpoint=_response_checkpoint(
                        row=row,
                        request=request,
                        response=response,
                        seal=seal,
                        budget=budget,
                        now=clock(),
                        run_id="axis3-run-ready",
                        pass_number=1,
                        page_number=page_number,
                        next_request=None,
                    ),
                )
            return {
                "stream_id": row["stream_id"],
                "complete": False,
                "reason": f"http_{response.status}",
                "pages": pages,
                "checkpoint": checkpoint,
            }
        total, next_position, terminal = _page_progress(row, response, position)
        if row["index"] == "dblp" and row["role"] == "main":
            validate_dblp_record_years(
                response.entity_body,
                int(row["cutoff_year"]),
                str(row["record_year_locator"]),
            )
        next_request = None if terminal else materialize_request(row, next_position)
        checkpoint = None
        if writer is not None:
            if seal is None:
                raise ContractError("bundle_writer", "bundle writerにregistration sealが必要")
            checkpoint = writer.commit_response(
                evidence=evidence,
                entity_body=response.entity_body,
                checkpoint=_response_checkpoint(
                    row=row,
                    request=request,
                    response=response,
                    seal=seal,
                    budget=budget,
                    now=clock(),
                    run_id="axis3-run-ready",
                    pass_number=1,
                    page_number=page_number,
                    next_request=next_request,
                ),
            )
        if lookup_probe is not None and lookup_probe["status"] != "ready":
            return {
                "stream_id": row["stream_id"],
                "complete": False,
                "reason": lookup_probe["reason"],
                "completion": {
                    "complete": False,
                    "completion_kind": "lookup",
                    **lookup_probe,
                },
                "pages": pages,
                "checkpoint": checkpoint,
            }
        if row["completion_kind"] == "count_only":
            return {
                "stream_id": row["stream_id"],
                "complete": False,
                "reason": "control_evaluator_unimplemented",
                "completion": {
                    "complete": False,
                    "completion_kind": "count_only",
                    "declared_total": total,
                    "reason": "control_evaluator_unimplemented",
                },
                "pages": pages,
                "checkpoint": checkpoint,
            }
        completion_pages.append(
            {"entity_body": response.entity_body, "declared_total": total, "terminal": terminal}
        )
        if terminal:
            break
        position = next_position
        page_number += 1
    completion = evaluate_completion(row, completion_pages)
    if row["completion_kind"] == "lookup":
        completion["completion_kind"] = "lookup"
        completion["lookup_resolved"] = completion["complete"]
    return {
        "stream_id": row["stream_id"],
        "complete": completion["complete"],
        "completion": completion,
        "pages": pages,
        "checkpoint": checkpoint,
    }


def run_ready(
    catalog: Mapping[str, Any],
    catalog_data: bytes,
    seal: Mapping[str, Any],
    preflight_report: Mapping[str, Any] | None,
    *,
    argv: Sequence[str],
    commit: str,
    transport: Any,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    sleeper: Callable[[float], None] = time.sleep,
    preflight_bundle_dir: Path | None = None,
    bundle_dir: Path | None = None,
    repo_root: Path = REPO_ROOT,
    source_paths: Sequence[Path] = SOURCE_PATHS,
    schema_paths: Sequence[Path] = SCHEMA_PATHS,
    effective_argv: Sequence[str] | None = None,
) -> dict[str, Any]:
    if preflight_bundle_dir is None or bundle_dir is None:
        raise ContractError(
            "bundle_preflight",
            "production run-readyはpreflight bundleとfinal raw bundleが必要",
        )
    validate_catalog(catalog)
    observed_argv = list(effective_argv if effective_argv is not None else argv)
    phase_argv = validate_effective_phase_argv(observed_argv, "run-ready")
    _bind_transport_semantics(phase_argv, transport)
    _bind_semantic_path(phase_argv, "--bundle", bundle_dir)
    _bind_semantic_path(
        phase_argv, "--preflight-bundle", preflight_bundle_dir
    )
    validate_registration_seal(
        seal,
        catalog_data,
        argv=argv,
        commit=commit,
        repo_root=repo_root,
        source_paths=source_paths,
        schema_paths=schema_paths,
        enforce_head=phase_argv["artifact_class"] == "production",
    )
    parent_preflight_manifest_sha256: str | None = None
    bundled_report, parent_preflight_manifest_sha256 = load_preflight_bundle(
        preflight_bundle_dir,
        catalog,
        seal,
    )
    if preflight_report is not None and preflight_report != bundled_report:
        raise ContractError("bundle_preflight", "引数reportがbundle内reportと不一致")
    preflight_report = bundled_report
    if preflight_report is None:
        raise ContractError("bundle_preflight", "run-readyにはpreflight bundle/reportが必要")
    validate_preflight_report(preflight_report, catalog, seal)
    if bundle_dir is not None and parent_preflight_manifest_sha256 is None:
        raise ContractError("bundle_parent", "final bundle作成にはpreflight bundle親が必要")
    writer = _open_bundle_writer(
        transport,
        bundle_dir,
        kind="final",
        seal=seal,
        phase_argv=phase_argv,
        parent_preflight_manifest_sha256=parent_preflight_manifest_sha256,
        defer_manifest_fold=True,
    )
    first = _parse_time(preflight_report["first_external_request_at"])
    budget = WireBudget(
        attempts=int(preflight_report["wire_attempt_count"]),
        first_external_request_at=first,
    )
    limiter = _host_limiter(writer, clock, sleeper)
    statuses = {row["stream_id"]: row["status"] for row in preflight_report["rows"]}
    ready_rows = _ordered_ready_rows(catalog, statuses)
    results = []
    executed_rows = []
    for row in ready_rows:
        stream_result = _run_stream(
            row,
            transport,
            budget,
            clock,
            limiter=limiter,
            writer=writer,
            seal=seal,
        )
        results.append(stream_result)
        executed_rows.append(row["stream_id"])
        if not stream_result["complete"]:
            break
    result = {
        "schema_version": "axis3-search-run-ready/v1",
        "registration_seal_sha256": seal["seal_sha256"],
        "preflight_report_sha256": preflight_report["report_sha256"],
        "parent_preflight_manifest_sha256": parent_preflight_manifest_sha256,
        "execution_order": executed_rows,
        "registered_ready_order": [row["stream_id"] for row in ready_rows],
        "effective_argv": observed_argv,
        "effective_argv_sha256": _sha256(_canonical_json(observed_argv)),
        "phase_argv_contract_sha256": phase_argv["phase_argv_contract_sha256"],
        "results": results,
        "wire_attempt_count": budget.attempts,
        "first_external_request_at": _format_time(budget.first_external_request_at),
        "deadline_at": _format_time(budget.deadline_at),
        "axis_complete": False,
        "axis_incomplete_reason": (
            "row-level ready execution does not complete blocked/unavailable rows, "
            "record screening, work-family adjudication, or sensitivity audit"
        ),
    }
    if writer is not None:
        eligibility = _derive_finalize_eligibility(
            kind="final",
            ledger=writer.ledger,
            attempt_intent=writer.attempt_intent,
            wire_attempt_count=budget.attempts,
        )
        if eligibility["finalize_eligible"] is True:
            writer.finalize_run(result)
            validate_bundle(
                bundle_dir,
                catalog=catalog,
                seal=seal,
                parent_preflight_bundle_dir=preflight_bundle_dir,
            )
        else:
            writer._write_state_pointer()
    return result


def _safe_bundle_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ContractError("bundle_path", "bundle pathは非空relative pathが必要")
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ContractError("bundle_path", "bundle外pathを参照できない") from exc
    return path


def _response_from_evidence(
    evidence: Mapping[str, Any], entity_body: bytes
) -> TransportResponse:
    provenance = evidence["alternative_provenance"]
    return TransportResponse(
        status=int(evidence["status"]),
        entity_body=entity_body,
        headers=tuple(
            (header["name"], header["value"])
            for header in provenance["observed_response_headers"]
        ),
        endpoint=str(provenance["endpoint"]),
        final_url=str(evidence["final_url"]),
        content_type=str(evidence["content_type"]),
        response_received_at=str(evidence["response_received_at"]),
    )


def _derive_stream_result(
    row: Mapping[str, Any],
    materials: Sequence[tuple[Mapping[str, Any], bytes, Mapping[str, Any]]],
) -> dict[str, Any]:
    """Re-run page, ID, cutoff, lookup, and completion gates from saved bytes."""

    if not materials:
        raise ContractError("bundle_completion", "stream pageが1件以上必要")
    position: int | str | None = None
    completion_pages: list[dict[str, Any]] = []
    evidences: list[Mapping[str, Any]] = []
    last_checkpoint: Mapping[str, Any] | None = None
    logical_page_number = 0
    successful_requests: set[
        tuple[str, str, int | None, str, tuple[tuple[str, str], ...]]
    ] = set()
    expected_pass_number = materials[0][0].get("pass_number")
    if (
        isinstance(expected_pass_number, bool)
        or not isinstance(expected_pass_number, int)
        or expected_pass_number < 1
    ):
        raise ContractError("bundle_page_progress", "stream pass番号が不正")
    for material_offset, (evidence, body, checkpoint) in enumerate(materials):
        if (
            evidence.get("stream_id") != row["stream_id"]
            or evidence.get("pass_number") != expected_pass_number
            or evidence.get("page_number") != logical_page_number
        ):
            raise ContractError(
                "bundle_page_progress",
                "streamのpass/page identityが0起点で単調連続でない",
            )
        expected_request = materialize_request(row, position)
        if evidence.get("request") != expected_request:
            raise ContractError(
                "bundle_page_progress",
                "保存requestがcatalogと前page bodyからの再導出値に不一致",
            )
        request_identity = _canonical_url(expected_request["url"])
        if request_identity in successful_requests:
            raise ContractError(
                "bundle_page_progress",
                "保存streamが成功済みpage requestを反復している",
            )
        response = _response_from_evidence(evidence, body)
        _validate_response_envelope(row, expected_request, response)
        if checkpoint.get(
            "start_independent_pass_request"
        ) != _branch_start_checkpoint_request(row):
            raise ContractError(
                "bundle_checkpoint_rederived",
                "独立pass requestがcatalogの枝先頭と不一致",
            )
        evidences.append(evidence)
        last_checkpoint = checkpoint
        if response.status != 200:
            expected_restart = _branch_start_checkpoint_request(row)
            if (
                checkpoint.get("resume_action") != "restart_branch"
                or checkpoint.get("restart_branch_request") != expected_restart
                or checkpoint.get("failed_ledger_sha256") != _sha256(body)
            ):
                raise ContractError("bundle_checkpoint_rederived", "non-200 checkpointがbody/requestと不一致")
            if material_offset == len(materials) - 1:
                return {
                    "stream_id": row["stream_id"],
                    "complete": False,
                    "reason": f"http_{response.status}",
                    "pages": evidences,
                    "checkpoint": checkpoint,
                    "next_position": position,
                }
            continue
        successful_requests.add(request_identity)
        lookup_probe = _probe_response(row, response) if row["completion_kind"] == "lookup" else None
        if lookup_probe is None:
            _validate_required_response_fields(row, response)
        total, next_position, terminal = _page_progress(row, response, position)
        if row["index"] == "dblp" and row["role"] == "main":
            validate_dblp_record_years(
                body,
                int(row["cutoff_year"]),
                str(row["record_year_locator"]),
            )
        expected_next = None if terminal else materialize_request(row, next_position)
        if expected_next is None:
            if checkpoint.get("resume_action") != "not_applicable":
                raise ContractError("bundle_checkpoint_rederived", "terminal checkpoint actionが不一致")
        elif expected_next["position_kind"] == "cursor":
            if (
                checkpoint.get("resume_action") != "continue_cursor"
                or checkpoint.get("continue_cursor_request")
                != _request_without_stream(expected_next)
            ):
                raise ContractError("bundle_checkpoint_rederived", "cursor checkpoint requestが再導出値と不一致")
        else:
            if (
                checkpoint.get("resume_action") != "continue_cursor"
                or checkpoint.get("continue_cursor_request")
                != _request_without_stream(expected_next)
            ):
                raise ContractError(
                    "bundle_checkpoint_rederived",
                    "offset continuation requestが再導出値と不一致",
                )
        if lookup_probe is not None and lookup_probe["status"] != "ready":
            if material_offset != len(materials) - 1:
                raise ContractError("bundle_page_progress", "blocked lookupの後続pageを許さない")
            return {
                "stream_id": row["stream_id"],
                "complete": False,
                "reason": lookup_probe["reason"],
                "completion": {
                    "complete": False,
                    "completion_kind": "lookup",
                    **lookup_probe,
                },
                "pages": evidences,
                "checkpoint": checkpoint,
                "next_position": None,
            }
        if row["completion_kind"] == "count_only":
            if material_offset != len(materials) - 1:
                raise ContractError("bundle_page_progress", "count-onlyの後続pageを許さない")
            return {
                "stream_id": row["stream_id"],
                "complete": False,
                "reason": "control_evaluator_unimplemented",
                "completion": {
                    "complete": False,
                    "completion_kind": "count_only",
                    "declared_total": total,
                    "reason": "control_evaluator_unimplemented",
                },
                "pages": evidences,
                "checkpoint": checkpoint,
                "next_position": None,
            }
        completion_pages.append(
            {"entity_body": body, "declared_total": total, "terminal": terminal}
        )
        if terminal:
            if material_offset != len(materials) - 1:
                raise ContractError("bundle_page_progress", "terminal pageの後続pageを許さない")
            completion = evaluate_completion(row, completion_pages)
            if row["completion_kind"] == "lookup":
                completion["completion_kind"] = "lookup"
                completion["lookup_resolved"] = completion["complete"]
            return {
                "stream_id": row["stream_id"],
                "complete": completion["complete"],
                "completion": completion,
                "pages": evidences,
                "checkpoint": checkpoint,
                "next_position": None,
            }
        position = next_position
        logical_page_number += 1
    assert last_checkpoint is not None
    return {
        "stream_id": row["stream_id"],
        "complete": False,
        "reason": "stream_nonterminal",
        "pages": evidences,
        "checkpoint": last_checkpoint,
        "next_position": position,
    }


def _derive_latest_stream_result(
    row: Mapping[str, Any],
    materials: Sequence[
        tuple[Mapping[str, Any], bytes, Mapping[str, Any]]
    ],
) -> dict[str, Any]:
    """Preserve failed pass evidence while deriving the latest restarted pass."""

    pass_groups: list[
        tuple[int, list[tuple[Mapping[str, Any], bytes, Mapping[str, Any]]]]
    ] = []
    for material in materials:
        pass_number = material[0].get("pass_number")
        if isinstance(pass_number, bool) or not isinstance(pass_number, int):
            raise ContractError("bundle_page_progress", "stream pass番号が不正")
        if pass_groups and pass_groups[-1][0] == pass_number:
            pass_groups[-1][1].append(material)
        else:
            if any(previous == pass_number for previous, _ in pass_groups):
                raise ContractError(
                    "bundle_page_progress", "完了済みpassへ後から戻れない"
                )
            pass_groups.append((pass_number, [material]))
    if [number for number, _ in pass_groups] != list(
        range(1, len(pass_groups) + 1)
    ):
        raise ContractError(
            "bundle_page_progress", "stream pass番号は1始まりの連続列が必要"
        )
    derived = [
        _derive_stream_result(row, group) for _number, group in pass_groups
    ]
    if any(result["complete"] for result in derived[:-1]):
        raise ContractError(
            "bundle_page_progress", "完走済みpassの後にbranchをrestartできない"
        )
    return derived[-1]


def _validate_bundle_checkpoint_entries(
    checkpoints: Sequence[Any],
) -> list[Mapping[str, Any]]:
    """Reject legacy string descriptors before checkpoint material validation."""

    if any(not isinstance(entry, Mapping) for entry in checkpoints):
        raise ContractError(
            "bundle_checkpoint_downgrade",
            "旧文字列checkpoint entryへのdowngradeを拒否",
        )
    return list(checkpoints)


def _validate_checkpoint_ledger_prefix(
    checkpoint: Mapping[str, Any], expected_prefix: str
) -> None:
    """Bind one replayed checkpoint to its independently derived ledger prefix."""

    if checkpoint.get("ledger_prefix_sha256") != expected_prefix:
        raise ContractError(
            "bundle_checkpoint_ledger", "checkpointがledger prefixと不一致"
        )


def validate_bundle(
    bundle_dir: Path,
    *,
    catalog: Mapping[str, Any] | None = None,
    seal: Mapping[str, Any] | None = None,
    parent_preflight_bundle_dir: Path | None = None,
    _allow_in_progress: bool = False,
    _allow_nonproduction: bool = False,
) -> Mapping[str, int]:
    root = Path(bundle_dir)
    manifest, manifest_bytes, _, _ = _read_bundle_manifest(root)
    if not isinstance(manifest, Mapping) or manifest.get("schema_version") != "axis3-search-bundle/v1":
        raise ContractError("bundle_manifest", "bundle schema versionが不正")
    kind = manifest.get("kind")
    if kind not in {"preflight", "final"}:
        raise ContractError("bundle_manifest", "bundle kindはpreflight/finalだけ")
    if kind == "final" and not HEX64_RE.fullmatch(str(manifest.get("parent_preflight_manifest_sha256", ""))):
        raise ContractError("bundle_parent", "final manifestはimmutable preflight親digestが必要")
    lifecycle = manifest.get("lifecycle")
    if lifecycle not in {"in_progress", "finalized"}:
        raise ContractError("bundle_lifecycle", "bundle lifecycleはin_progress/finalizedが必要")
    if lifecycle == "in_progress" and not _allow_in_progress:
        raise ContractError("bundle_lifecycle", "in-progress bundleはresume内部loader専用")
    artifact_class = manifest.get("artifact_class")
    if artifact_class not in {"production", "nonproduction_simulation"}:
        raise ContractError("bundle_phase_argv", "bundle artifact classが不正")
    if artifact_class != "production" and not _allow_nonproduction:
        raise ContractError(
            "bundle_nonproduction",
            "simulation bundleをproduction validationへ使用できない",
        )
    if catalog is None or seal is None:
        raise ContractError(
            "bundle_registration_inputs",
            "bundle検証はcatalogとregistration sealの明示入力が必要",
        )
    validate_catalog(catalog)
    seal_argv = seal.get("argv")
    seal_commit = seal.get("commit")
    if (
        not isinstance(seal_argv, list)
        or any(not isinstance(value, str) for value in seal_argv)
        or not isinstance(seal_commit, str)
    ):
        raise ContractError("bundle_registration", "registration sealのargv/commitが不正")
    validate_registration_seal(
        seal,
        catalog_bytes(catalog),
        argv=seal_argv,
        commit=seal_commit,
        enforce_head=artifact_class == "production",
    )
    if (
        manifest.get("registration_seal_sha256") != seal.get("seal_sha256")
        or manifest.get("catalog_sha256") != seal.get("catalog_sha256")
        or seal.get("catalog_sha256") != _sha256(catalog_bytes(catalog))
    ):
        raise ContractError("bundle_registration", "bundle registration closureが不一致")
    phase_argv = manifest.get("phase_argv")
    if not isinstance(phase_argv, Mapping):
        raise ContractError("bundle_phase_argv", "bundleにphase argv evidenceが無い")
    phase = phase_argv.get("phase")
    if phase not in ({"preflight", "resume"} if kind == "preflight" else {"run-ready", "resume"}):
        raise ContractError("bundle_phase_argv", "bundle kindとphase argvが不一致")
    expected_phase_argv = validate_effective_phase_argv(
        phase_argv.get("effective_argv", []), str(phase)
    )
    if phase_argv != expected_phase_argv:
        raise ContractError("bundle_phase_argv", "bundle phase argv evidenceが再導出値と不一致")
    origin_phase_argv = manifest.get("origin_phase_argv")
    if not isinstance(origin_phase_argv, Mapping):
        raise ContractError("bundle_phase_argv", "bundle origin phase argv evidenceが無い")
    origin_phase = "preflight" if kind == "preflight" else "run-ready"
    expected_origin = validate_effective_phase_argv(
        origin_phase_argv.get("effective_argv", []), origin_phase
    )
    if origin_phase_argv != expected_origin:
        raise ContractError("bundle_phase_argv", "origin phase argv evidenceが再導出値と不一致")
    if origin_phase_argv.get("artifact_class") != artifact_class:
        raise ContractError("bundle_phase_argv", "origin artifact classがmanifestと不一致")
    pages = manifest.get("pages")
    checkpoints = manifest.get("checkpoints", [])
    if not isinstance(pages, list) or not isinstance(checkpoints, list):
        raise ContractError("bundle_manifest", "pages/checkpoints arrayが必要")
    journal = manifest.get("journal")
    packed_replayed: dict[str, Any] | None = None
    if (
        kind == "preflight"
        and isinstance(journal, Mapping)
        and journal.get("schema_version") == _PREFLIGHT_WAL_VERSION
    ):
        packed_replayed = _replay_preflight_wal(root, journal)
        if (
            packed_replayed["pages"] != pages
            or packed_replayed["checkpoints"] != checkpoints
        ):
            raise ContractError("bundle_journal", "manifestがpreflight WAL foldと不一致")
    page_evidence: list[Mapping[str, Any]] = []
    page_bodies: list[bytes] = []
    committed_intents: list[Mapping[str, Any]] = []
    consumed_receipt_ids: set[str] = set()
    for page_offset, page in enumerate(pages):
        if not isinstance(page, Mapping):
            raise ContractError("bundle_manifest", "page entryがobjectでない")
        if packed_replayed is not None:
            body_bytes = packed_replayed["page_bodies"][page_offset]
            evidence = packed_replayed["page_evidence"][page_offset]
            metadata_bytes = _canonical_json(evidence)
        else:
            body = _safe_bundle_path(root, page.get("entity_body_path"))
            metadata = _safe_bundle_path(root, page.get("metadata_path"))
            try:
                body_bytes = body.read_bytes()
                metadata_bytes = metadata.read_bytes()
                evidence = json.loads(metadata_bytes.decode("utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ContractError("bundle_page", "page evidenceを読めない") from exc
        validate_page_evidence(evidence, body_bytes)
        page_evidence.append(evidence)
        page_bodies.append(body_bytes)
        if (
            page.get("entity_body_sha256") != _sha256(body_bytes)
            or page.get("metadata_sha256") != _sha256(metadata_bytes)
        ):
            raise ContractError(
                "bundle_page_manifest_digest",
                "manifestがentity bodyとpage evidence metadataを束縛していない",
            )
    ledger: list[Mapping[str, Any]] | None = None
    ledger_descriptor = manifest.get("ledger")
    if ledger_descriptor is None:
        raise ContractError("bundle_ledger", "全bundleにledger descriptorが必要")
    if ledger_descriptor is not None:
        if not isinstance(ledger_descriptor, Mapping):
            raise ContractError("bundle_ledger", "ledger descriptorがobjectでない")
        if manifest.get("_journal_ledger") is not None:
            loaded_ledger = _load_manifest_ledger(root, manifest)
            ledger_bytes = _canonical_json(loaded_ledger)
        else:
            ledger_path = _safe_bundle_path(root, ledger_descriptor.get("path"))
            try:
                ledger_bytes = ledger_path.read_bytes()
                loaded_ledger = json.loads(ledger_bytes.decode("utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ContractError("bundle_ledger", "ledgerを読めない") from exc
        if (
            ledger_descriptor.get("sha256") != _sha256(ledger_bytes)
            or not isinstance(loaded_ledger, list)
            or any(not isinstance(entry, Mapping) for entry in loaded_ledger)
            or len(loaded_ledger) != len(pages)
        ):
            raise ContractError("bundle_ledger", "ledger digest/countがmanifestと不一致")
        ledger = list(loaded_ledger)
        prefix_hasher = _new_ledger_hasher()
        prefix_digest = _finish_ledger_hasher(prefix_hasher)
        ledger_prefix_digests: list[str] = []
        for ordinal, entry in enumerate(ledger, 1):
            if not isinstance(entry, Mapping) or entry.get("ordinal") != ordinal:
                raise ContractError("bundle_ledger", "ledger ordinalが単調連続でない")
            if entry.get("previous_ledger_prefix_sha256") != prefix_digest:
                raise ContractError("bundle_ledger_chain", "ledger prefix digest chainが不一致")
            if entry.get("page_entry_sha256") != _sha256(_canonical_json(pages[ordinal - 1])):
                raise ContractError("bundle_ledger", "ledgerがpage manifest entryと不一致")
            evidence = page_evidence[ordinal - 1]
            expected_ledger_projection = {
                "stream_id": evidence["stream_id"],
                "pass_number": evidence["pass_number"],
                "page_number": evidence["page_number"],
                "status": evidence["status"],
                "request": evidence["request"],
            }
            if any(entry.get(key) != value for key, value in expected_ledger_projection.items()):
                raise ContractError("bundle_ledger", "ledgerがpage evidence identityと不一致")
            if packed_replayed is not None:
                intent = packed_replayed["committed_intents"][ordinal - 1]
                raw = packed_replayed["raw_responses"][ordinal - 1]
                raw_body = packed_replayed["page_bodies"][ordinal - 1]
                if (
                    entry.get("attempt_intent_sha256")
                    != _sha256(_canonical_json(intent))
                    or entry.get("raw_response_sha256")
                    != _sha256(_canonical_json(raw))
                ):
                    raise ContractError(
                        "bundle_raw_response", "WAL attempt raw material digestが不一致"
                    )
            else:
                for path_key, digest_key in (
                    ("attempt_intent_path", "attempt_intent_sha256"),
                    ("raw_response_path", "raw_response_sha256"),
                ):
                    material_path = _safe_bundle_path(root, entry.get(path_key))
                    try:
                        material_bytes = material_path.read_bytes()
                    except OSError as exc:
                        raise ContractError("bundle_raw_response", "attempt raw materialを読めない") from exc
                    if entry.get(digest_key) != _sha256(material_bytes):
                        raise ContractError("bundle_raw_response", "attempt raw material digestが不一致")
                try:
                    intent = json.loads(
                        _safe_bundle_path(root, entry["attempt_intent_path"]).read_text(
                            encoding="utf-8"
                        )
                    )
                    raw = json.loads(
                        _safe_bundle_path(root, entry["raw_response_path"]).read_text(
                            encoding="utf-8"
                        )
                    )
                    raw_body = _safe_bundle_path(root, raw.get("entity_body_path")).read_bytes()
                except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                    raise ContractError(
                        "bundle_raw_response",
                        "attempt intent/raw responseを再構成できない",
                    ) from exc
            if (
                intent.get("schema_version") != "axis3-search-attempt-intent/v1"
                or intent.get("ordinal") != ordinal
                or intent.get("stream_id") != evidence["stream_id"]
                or intent.get("pass_number") != evidence["pass_number"]
                or intent.get("page_number") != evidence["page_number"]
                or intent.get("request") != evidence["request"]
                or intent.get("previous_ledger_prefix_sha256")
                != entry["previous_ledger_prefix_sha256"]
                or isinstance(intent.get("expected_wire_attempt_count"), bool)
                or not isinstance(intent.get("expected_wire_attempt_count"), int)
                or intent["expected_wire_attempt_count"] < 1
                or raw.get("ordinal") != ordinal
                or raw.get("request") != evidence["request"]
                or raw.get("status") != evidence["status"]
                or raw.get("final_url") != evidence["final_url"]
                or raw.get("content_type") != evidence["content_type"]
                or raw.get("response_received_at")
                != evidence["response_received_at"]
                or raw.get("endpoint")
                != evidence["alternative_provenance"]["endpoint"]
                or raw.get("headers")
                != [
                    [header["name"], header["value"]]
                    for header in evidence["alternative_provenance"][
                        "observed_response_headers"
                    ]
                ]
                or raw.get("entity_body_sha256") != _sha256(page_bodies[ordinal - 1])
                or raw.get("entity_body_byte_count") != len(raw_body)
                or raw_body != page_bodies[ordinal - 1]
                or raw.get("entity_body_path")
                != pages[ordinal - 1]["entity_body_path"]
            ):
                raise ContractError("bundle_raw_response", "intent/raw/page chainが不一致")
            receipt = raw.get("transport_receipt")
            if artifact_class == "production":
                reconstructed_response = _response_from_evidence(
                    evidence, page_bodies[ordinal - 1]
                )
                if (
                    not isinstance(receipt, Mapping)
                    or receipt.get("schema_version") != _SEND_RECEIPT_VERSION
                    or not HEX64_RE.fullmatch(str(receipt.get("session_id", "")))
                    or not HEX64_RE.fullmatch(str(receipt.get("receipt_id", "")))
                    or receipt.get("ordinal") != ordinal
                    or receipt.get("request_sha256")
                    != _sha256(_canonical_json(evidence["request"]))
                    or receipt.get("response_sha256")
                    != _transport_response_sha256(reconstructed_response)
                    or receipt.get("transport_marker")
                    != _PRODUCTION_TRANSPORT_MARKER
                    or receipt["receipt_id"] in consumed_receipt_ids
                ):
                    raise ContractError(
                        "send_receipt_identity",
                        "production pageのone-shot send receiptが不一致",
                    )
                consumed_receipt_ids.add(str(receipt["receipt_id"]))
            elif receipt is not None:
                raise ContractError(
                    "send_receipt_identity",
                    "nonproduction pageへproduction receiptを付けられない",
                )
            _parse_time(str(intent.get("intent_at")))
            committed_intents.append(intent)
            prefix_digest = _advance_ledger_hasher(prefix_hasher, ordinal, entry)
            ledger_prefix_digests.append(prefix_digest)
        if manifest.get("state_format") != "journal" and journal is not None:
            if not isinstance(journal, Mapping):
                raise ContractError("bundle_journal", "journal descriptorがobjectでない")
            replayed = (
                packed_replayed
                if packed_replayed is not None
                else _replay_bundle_journal(root, journal)
            )
            if (
                replayed["pages"] != pages
                or replayed["checkpoints"] != checkpoints
                or replayed["ledger"] != ledger
                or replayed["ledger_sha256"] != ledger_descriptor.get("sha256")
            ):
                raise ContractError("bundle_journal", "fold済みmanifestがjournal replayと不一致")
    pending = manifest.get("attempt_intent")
    if pending is not None:
        if not isinstance(pending, Mapping) or pending.get("state") not in {
            "pending",
            "response_received",
        }:
            raise ContractError("bundle_pending_attempt", "pending attempt descriptorが不正")
        if packed_replayed is not None:
            intent = packed_replayed.get("pending_intent")
            if not isinstance(intent, Mapping):
                raise ContractError("bundle_pending_attempt", "WAL pending intentが無い")
            intent_bytes = _canonical_json(intent)
        else:
            intent_path = _safe_bundle_path(root, pending.get("intent_path"))
            try:
                intent_bytes = intent_path.read_bytes()
                intent = json.loads(intent_bytes.decode("utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ContractError("bundle_pending_attempt", "pending intentを読めない") from exc
        if (
            pending.get("intent_sha256") != _sha256(intent_bytes)
            or intent.get("ordinal") != len(pages) + 1
            or intent.get("previous_ledger_prefix_sha256")
            != ledger_descriptor.get("sha256")
        ):
            raise ContractError("bundle_pending_attempt", "pending intent chainが不一致")
        if pending["state"] == "response_received":
            if packed_replayed is not None:
                pending_raw = packed_replayed.get("pending_raw")
                if (
                    not isinstance(pending_raw, tuple)
                    or len(pending_raw) != 2
                    or not isinstance(pending_raw[0], Mapping)
                    or not isinstance(pending_raw[1], bytes)
                ):
                    raise ContractError("bundle_pending_attempt", "WAL pending raw responseが無い")
                raw = pending_raw[0]
                raw_body = pending_raw[1]
                raw_bytes = _canonical_json(raw)
            else:
                raw_path = _safe_bundle_path(root, pending.get("raw_response_path"))
                try:
                    raw_bytes = raw_path.read_bytes()
                    raw = json.loads(raw_bytes.decode("utf-8"))
                    raw_body = _safe_bundle_path(root, raw.get("entity_body_path")).read_bytes()
                except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ContractError("bundle_pending_attempt", "pending raw responseを読めない") from exc
            if (
                pending.get("raw_response_sha256") != _sha256(raw_bytes)
                or raw.get("request") != intent.get("request")
                or raw.get("entity_body_sha256") != _sha256(raw_body)
                or raw.get("entity_body_byte_count") != len(raw_body)
            ):
                raise ContractError("bundle_pending_attempt", "pending raw response chainが不一致")
            pending_receipt = raw.get("transport_receipt")
            if artifact_class == "production":
                pending_response = TransportResponse(
                    status=int(raw["status"]),
                    entity_body=raw_body,
                    headers=tuple(tuple(item) for item in raw["headers"]),
                    endpoint=str(raw["endpoint"]),
                    final_url=str(raw["final_url"]),
                    content_type=str(raw["content_type"]),
                    response_received_at=str(raw["response_received_at"]),
                )
                if (
                    not isinstance(pending_receipt, Mapping)
                    or pending_receipt.get("schema_version")
                    != _SEND_RECEIPT_VERSION
                    or pending_receipt.get("ordinal") != len(pages) + 1
                    or pending_receipt.get("request_sha256")
                    != _sha256(_canonical_json(intent["request"]))
                    or pending_receipt.get("response_sha256")
                    != _transport_response_sha256(pending_response)
                    or pending_receipt.get("transport_marker")
                    != _PRODUCTION_TRANSPORT_MARKER
                    or pending_receipt.get("receipt_id") in consumed_receipt_ids
                ):
                    raise ContractError(
                        "send_receipt_identity", "pending production receiptが不一致"
                    )
            elif pending_receipt is not None:
                raise ContractError(
                    "send_receipt_identity", "nonproduction pending rawにreceiptがある"
                )
    report_descriptor = manifest.get("preflight_report")
    report_value: Mapping[str, Any] | None = None
    if report_descriptor is not None:
        if not isinstance(report_descriptor, Mapping):
            raise ContractError("bundle_preflight", "preflight report descriptorがobjectでない")
        expected_report_path = (
            f"reports/preflight-{report_descriptor.get('sha256')}.json"
        )
        if report_descriptor.get("path") != expected_report_path:
            raise ContractError("bundle_preflight", "preflight report pathが内容digestと不一致")
        report_path = _safe_bundle_path(root, report_descriptor.get("path"))
        try:
            report_bytes = report_path.read_bytes()
            decoded_report = json.loads(report_bytes.decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ContractError("bundle_preflight", "preflight reportを読めない") from exc
        if report_descriptor.get("sha256") != _sha256(report_bytes):
            raise ContractError("bundle_preflight", "preflight report digestが不一致")
        if not isinstance(decoded_report, Mapping):
            raise ContractError("bundle_preflight", "preflight report rootがobjectでない")
        report_value = decoded_report
    run_descriptor = manifest.get("run_result")
    if run_descriptor is not None:
        if not isinstance(run_descriptor, Mapping):
            raise ContractError("bundle_run", "run result descriptorがobjectでない")
        expected_run_path = f"results/run-{run_descriptor.get('sha256')}.json"
        if run_descriptor.get("path") != expected_run_path:
            raise ContractError("bundle_run", "run result pathが内容digestと不一致")
        run_path = _safe_bundle_path(root, run_descriptor.get("path"))
        try:
            run_bytes = run_path.read_bytes()
            run_value = json.loads(run_bytes.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ContractError("bundle_run", "run resultを読めない") from exc
        if run_descriptor.get("sha256") != _sha256(run_bytes):
            raise ContractError("bundle_run", "run result digestが不一致")
        if (
            isinstance(run_value, Mapping)
            and run_value.get("schema_version") == "axis3-search-run-ready/v1"
        ):
            if (
                run_value.get("registration_seal_sha256")
                != manifest.get("registration_seal_sha256")
                or run_value.get("parent_preflight_manifest_sha256")
                != manifest.get("parent_preflight_manifest_sha256")
                or run_value.get("effective_argv_sha256")
                != _sha256(_canonical_json(run_value.get("effective_argv")))
            ):
                raise ContractError("bundle_run", "run resultのseal/parent/実効argv束縛が不一致")
    if lifecycle == "finalized":
        wire_attempt_count = (
            int(committed_intents[-1]["expected_wire_attempt_count"])
            if committed_intents
            else 0
        )
        eligibility = _derive_finalize_eligibility(
            kind=str(kind),
            ledger=ledger or [],
            attempt_intent=pending if isinstance(pending, Mapping) else None,
            wire_attempt_count=wire_attempt_count,
        )
        if eligibility["finalize_eligible"] is not True:
            raise ContractError(
                "finalize_eligibility", str(eligibility["reason"])
            )
        if pending is not None:
            raise ContractError("bundle_lifecycle", "finalized bundleにpending attemptを置けない")
        if kind == "preflight" and report_descriptor is None:
            raise ContractError("bundle_lifecycle", "finalized preflightはreport必須")
        if kind == "final" and run_descriptor is None:
            raise ContractError("bundle_lifecycle", "finalized finalはrun-result必須")
    elif report_descriptor is not None or run_descriptor is not None:
        raise ContractError("bundle_lifecycle", "in-progress bundleにfinal resultを置けない")
    checkpoints = _validate_bundle_checkpoint_entries(checkpoints)
    if ledger is None:
        raise ContractError("bundle_checkpoint", "producer bundleはledgerが必要")
    if packed_replayed is None and len(checkpoints) != len(pages):
        raise ContractError("bundle_checkpoint", "producer bundleは全page checkpointが必要")
    if packed_replayed is not None and len(checkpoints) > len(pages):
        raise ContractError("bundle_checkpoint", "preflight checkpoint数がpage数を超過")
    previous_checkpoint_digest: str | None = None
    previous_wire_attempts = -1
    loaded_checkpoints: list[Mapping[str, Any]] = []
    loaded_checkpoint_ordinals: list[int] = []
    for checkpoint_offset, checkpoint_entry in enumerate(checkpoints, 1):
        assert isinstance(checkpoint_entry, Mapping)
        page_ordinal = (
            checkpoint_entry.get("page_ordinal")
            if packed_replayed is not None
            else checkpoint_offset
        )
        if (
            isinstance(page_ordinal, bool)
            or not isinstance(page_ordinal, int)
            or not 1 <= page_ordinal <= len(pages)
        ):
            raise ContractError("bundle_checkpoint", "checkpoint page ordinalが不正")
        checkpoint_path = checkpoint_entry.get("path")
        expected_checkpoint_digest = checkpoint_entry.get("sha256")
        if packed_replayed is not None:
            checkpoint = packed_replayed["checkpoint_values"].get(page_ordinal)
            if not isinstance(checkpoint, Mapping):
                raise ContractError("bundle_checkpoint", "WAL checkpoint valueが無い")
            checkpoint_bytes = _canonical_json(checkpoint)
        else:
            path = _safe_bundle_path(root, checkpoint_path)
            try:
                checkpoint_bytes = path.read_bytes()
                checkpoint = json.loads(checkpoint_bytes.decode("utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ContractError("bundle_checkpoint", "checkpointを読めない") from exc
        validate_checkpoint(checkpoint)
        loaded_checkpoints.append(checkpoint)
        loaded_checkpoint_ordinals.append(page_ordinal)
        checkpoint_digest = _sha256(checkpoint_bytes)
        if expected_checkpoint_digest != checkpoint_digest:
            raise ContractError("bundle_checkpoint_digest", "manifestがcheckpoint bytesを束縛していない")
        if checkpoint["previous_checkpoint_sha256"] != previous_checkpoint_digest:
            raise ContractError("bundle_checkpoint_chain", "前checkpoint digest chainが不一致")
        if checkpoint["wire_attempt_count"] < previous_wire_attempts:
            raise ContractError("bundle_checkpoint_chain", "wire attemptがcheckpoint間で減少")
        previous_wire_attempts = checkpoint["wire_attempt_count"]
        assert ledger is not None
        expected_prefix = ledger_prefix_digests[page_ordinal - 1]
        _validate_checkpoint_ledger_prefix(checkpoint, expected_prefix)
        evidence = page_evidence[page_ordinal - 1]
        intent = committed_intents[page_ordinal - 1]
        expected_checkpoint_pass = 1 if kind == "preflight" else evidence["pass_number"]
        expected_pass_kind = {
            "cursor": "cursor_traversal",
            "offset": "offset_traversal",
            "fixed": "fixed",
        }[evidence["request"]["position_kind"]]
        expected_state = (
            "quota_wait"
            if kind == "preflight"
            and page_ordinal == 1
            and evidence["stream_id"] == "AX3A1-L-ID-01@openalex"
            and evidence["status"] == 429
            else "committed"
            if evidence["status"] == 200
            else "http_failure"
        )
        if (
            checkpoint["stream_id"] != evidence["stream_id"]
            or checkpoint["index"] != evidence["request"]["index"]
            or checkpoint["pass_number"] != expected_checkpoint_pass
            or checkpoint["page_identity"]["pass_number"] != expected_checkpoint_pass
            or checkpoint["pass_kind"] != expected_pass_kind
            or checkpoint["state"] != expected_state
            or checkpoint["page_identity"]["page_number"] != evidence["page_number"]
            or checkpoint["last_committed_page"] != evidence["page_number"]
            or intent["expected_wire_attempt_count"] != checkpoint["wire_attempt_count"]
        ):
            raise ContractError("bundle_checkpoint_ledger", "checkpointがcommitted pageと不一致")
        if (
            checkpoint["resume_action"] == "continue_cursor"
            and checkpoint["continue_cursor_request"]["position_kind"]
            == "cursor"
        ):
            source = checkpoint["cursor_source"]
            page = pages[page_ordinal - 1]
            if (
                source["entity_body_path"] != page["entity_body_path"]
                or source["entity_body_sha256"] != _sha256(page_bodies[page_ordinal - 1])
                or source["field_locator"] != "/meta/next_cursor"
            ):
                raise ContractError("bundle_checkpoint_ledger", "cursor sourceがentity bodyと不一致")
            body_value = _decode_json_object(page_bodies[page_ordinal - 1])
            meta = body_value.get("meta")
            next_cursor = meta.get("next_cursor") if isinstance(meta, Mapping) else None
            try:
                cursor_query = dict(
                    parse_qsl(
                        urlsplit(checkpoint["continue_cursor_request"]["url"]).query,
                        keep_blank_values=True,
                        strict_parsing=True,
                    )
                ).get("cursor")
            except ValueError as exc:
                raise ContractError(
                    "bundle_checkpoint_ledger",
                    "resume cursor queryを解析できない",
                ) from exc
            if not isinstance(next_cursor, str) or cursor_query != next_cursor:
                raise ContractError("bundle_checkpoint_ledger", "resume cursorが保存bodyと不一致")
        previous_checkpoint_digest = checkpoint_digest
    parser_digest, runner_digest, schema_digest = _checkpoint_source_digests(seal)
    for checkpoint in loaded_checkpoints:
        if (
            checkpoint["registration_seal_sha256"] != seal["seal_sha256"]
            or checkpoint["catalog_sha256"] != seal["catalog_sha256"]
            or checkpoint["parser_sha256"] != parser_digest
            or checkpoint["runner_sha256"] != runner_digest
            or checkpoint["schema_sha256"] != schema_digest
        ):
            raise ContractError(
                "bundle_checkpoint_rederived",
                "checkpoint closure identityがregistration sealと不一致",
            )
    rows_by_id = {row["stream_id"]: row for row in catalog["rows"]}
    if kind == "preflight":
        if packed_replayed is not None:
            _validate_preflight_wal_attempt_sequence(catalog, page_evidence)
        for evidence in page_evidence:
            row = rows_by_id.get(evidence["stream_id"])
            if (
                row is None
                or evidence["pass_number"] != 0
                or evidence["page_number"] != 0
                or evidence["request"] != materialize_request(row)
            ):
                raise ContractError(
                    "bundle_preflight",
                    "preflight requestが登録page 0からの再導出値と不一致",
                )
        for page_ordinal, checkpoint in zip(
            loaded_checkpoint_ordinals, loaded_checkpoints
        ):
            if checkpoint["wire_attempt_count"] != page_ordinal:
                raise ContractError(
                    "bundle_checkpoint_rederived",
                    "preflight checkpoint wire countがraw attempt数と不一致",
                )
        if packed_replayed is not None:
            required_checkpoint_ordinals = [
                ordinal
                for ordinal, evidence in enumerate(page_evidence, 1)
                if evidence["status"] != 200
            ]
            if loaded_checkpoint_ordinals != required_checkpoint_ordinals:
                raise ContractError(
                    "bundle_checkpoint_rederived",
                    "preflight checkpointは失敗responseだけに必要",
                )
        if report_value is not None:
            _validate_preflight_report_against_bundle_material(
                report_value,
                catalog,
                seal,
                page_evidence,
                page_bodies,
                loaded_checkpoints,
            )
    else:
        if parent_preflight_bundle_dir is None:
            raise ContractError(
                "bundle_parent",
                "final bundle検証にはpreflight親bundleの明示入力が必要",
            )
        parent_report, parent_digest = load_preflight_bundle(
            parent_preflight_bundle_dir,
            catalog,
            seal,
            _allow_nonproduction=_allow_nonproduction,
        )
        if manifest.get("parent_preflight_manifest_sha256") != parent_digest:
            raise ContractError("bundle_parent", "final bundleのpreflight親digestが不一致")
        base_attempts = int(parent_report["wire_attempt_count"])
        for ordinal, checkpoint in enumerate(loaded_checkpoints, 1):
            if checkpoint["wire_attempt_count"] != base_attempts + ordinal:
                raise ContractError(
                    "bundle_checkpoint_rederived",
                    "final checkpoint wire countが親attemptとraw page数からの再導出値に不一致",
                )
        statuses = {row["stream_id"]: row["status"] for row in parent_report["rows"]}
        ready_rows = _ordered_ready_rows(catalog, statuses)
        ready_ids = [row["stream_id"] for row in ready_rows]
        grouped: list[tuple[str, list[tuple[Mapping[str, Any], bytes, Mapping[str, Any]]]]] = []
        for evidence, body, checkpoint in zip(
            page_evidence, page_bodies, loaded_checkpoints
        ):
            stream_id = str(evidence["stream_id"])
            if grouped and grouped[-1][0] == stream_id:
                grouped[-1][1].append((evidence, body, checkpoint))
            else:
                if any(previous_id == stream_id for previous_id, _ in grouped):
                    raise ContractError(
                        "bundle_execution_order",
                        "完了済みstreamへ後から戻るledger順を許さない",
                    )
                grouped.append((stream_id, [(evidence, body, checkpoint)]))
        execution_order = [stream_id for stream_id, _ in grouped]
        if execution_order != ready_ids[: len(execution_order)]:
            raise ContractError(
                "bundle_execution_order",
                "ledger stream順がpreflight ready登録順prefixと不一致",
            )
        derived_results: list[dict[str, Any]] = []
        for offset, (stream_id, materials) in enumerate(grouped):
            row = rows_by_id.get(stream_id)
            if row is None:
                raise ContractError("bundle_execution_order", "ledger streamがcatalogに無い")
            derived = _derive_latest_stream_result(row, materials)
            derived.pop("next_position", None)
            if not derived["complete"] and offset != len(grouped) - 1:
                raise ContractError(
                    "bundle_execution_order",
                    "incomplete stream後に次ready rowを実行できない",
                )
            derived_results.append(derived)
        if run_descriptor is not None:
            if not isinstance(run_value, Mapping) or run_value.get(
                "schema_version"
            ) != "axis3-search-run-ready/v1":
                raise ContractError(
                    "bundle_run",
                    "run-result schema名変更による意味検査回避を拒否",
                )
            expected_run_value = {
                "schema_version": "axis3-search-run-ready/v1",
                "registration_seal_sha256": seal["seal_sha256"],
                "preflight_report_sha256": parent_report["report_sha256"],
                "parent_preflight_manifest_sha256": manifest[
                    "parent_preflight_manifest_sha256"
                ],
                "execution_order": execution_order,
                "registered_ready_order": ready_ids,
                "effective_argv": phase_argv["effective_argv"],
                "effective_argv_sha256": phase_argv["effective_argv_sha256"],
                "phase_argv_contract_sha256": phase_argv[
                    "phase_argv_contract_sha256"
                ],
                "results": derived_results,
                "wire_attempt_count": base_attempts + len(pages),
                "first_external_request_at": parent_report[
                    "first_external_request_at"
                ],
                "deadline_at": parent_report["deadline_at"],
                "axis_complete": False,
                "axis_incomplete_reason": (
                    "row-level ready execution does not complete blocked/unavailable rows, "
                    "record screening, work-family adjudication, or sensitivity audit"
                ),
            }
            if dict(run_value) != expected_run_value:
                raise ContractError(
                    "bundle_run",
                    "run-resultがpage ledgerとpreflight親からの再導出値に不一致",
                )
    return {"pages": len(pages), "checkpoints": len(checkpoints)}


def _validate_bundle_for_resume(
    bundle_dir: Path,
    *,
    catalog: Mapping[str, Any],
    seal: Mapping[str, Any],
    parent_preflight_bundle_dir: Path | None = None,
) -> Mapping[str, int]:
    return validate_bundle(
        bundle_dir,
        catalog=catalog,
        seal=seal,
        parent_preflight_bundle_dir=parent_preflight_bundle_dir,
        _allow_in_progress=True,
        _allow_nonproduction=True,
    )


def _validate_preflight_report_against_bundle_material(
    report: Mapping[str, Any],
    catalog: Mapping[str, Any],
    seal: Mapping[str, Any],
    page_evidence: Sequence[Mapping[str, Any]],
    page_bodies: Sequence[bytes],
    checkpoints: Sequence[Mapping[str, Any]],
) -> None:
    validate_preflight_report(report, catalog, seal)
    evidence_digests = Counter(
        _evidence_digest(evidence) for evidence in report["preflight_evidence"]
    )
    page_metadata_digests = Counter(
        _evidence_digest(evidence) for evidence in page_evidence
    )
    if evidence_digests != page_metadata_digests:
        raise ContractError(
            "bundle_preflight",
            "全preflight evidenceがraw bundle pageとexact対応しない",
        )
    page_material = {
        _evidence_digest(evidence): (evidence, body)
        for evidence, body in zip(page_evidence, page_bodies)
    }
    rows_by_id = {row["stream_id"]: row for row in catalog["rows"]}
    for report_row in report["rows"]:
        catalog_row = rows_by_id[report_row["stream_id"]]
        if report_row["attempted"]:
            attempt_number = report_row["attempt_number"]
            evidence = report["preflight_evidence"][attempt_number - 1]
            evidence_digest = _evidence_digest(evidence)
            if (
                evidence["stream_id"] != catalog_row["stream_id"]
                or report_row["evidence_sha256"] != evidence_digest
                or evidence["request"] != materialize_request(catalog_row)
                or evidence_digest not in page_material
            ):
                raise ContractError(
                    "bundle_preflight",
                    "attempt evidenceが登録page 0 requestと不一致",
                )
            _, body = page_material[evidence_digest]
            provenance = evidence["alternative_provenance"]
            response = TransportResponse(
                status=evidence["status"],
                entity_body=body,
                headers=tuple(
                    (header["name"], header["value"])
                    for header in provenance["observed_response_headers"]
                ),
                endpoint=provenance["endpoint"],
                final_url=evidence["final_url"],
                content_type=evidence["content_type"],
                response_received_at=evidence["response_received_at"],
            )
            _validate_response_envelope(catalog_row, evidence["request"], response)
            if response.status == 200 and catalog_row["role"] != "lookup":
                _validate_required_response_fields(catalog_row, response)
            expected_row = {
                **_preflight_row_base(catalog_row),
                **_probe_response(catalog_row, response),
                "entity_body_sha256": _sha256(body),
                "attempted": True,
                "attempt_number": attempt_number,
                "evidence_sha256": evidence_digest,
                "preflight_response_reusable_for_run": False,
            }
        else:
            if catalog_row["request_factory"]["state"] == "complete":
                if report.get("stopped_after_openalex_429") is not True:
                    raise ContractError(
                        "bundle_preflight", "complete factoryの未attempt理由が無い"
                    )
                reason = "preflight_stopped_after_openalex_429"
            else:
                reason = catalog_row["request_factory"]["blocked_reason"]
            expected_row = {
                **_preflight_row_base(catalog_row),
                "status": "blocked",
                "reason": reason,
                "transport_available": None,
                "lookup_resolved": None,
                "declared_total": None,
                "preflight_response_reusable_for_run": False,
            }
        if report_row != expected_row:
            raise ContractError(
                "bundle_preflight", "preflight statusが保存raw evidenceと不一致"
            )
    availability_id = "AX3A1-L-ID-01@openalex"
    if (
        _evidence_digest(report["availability_evidence"])
        != _evidence_digest(page_evidence[0])
        or report["availability_evidence"] != page_evidence[0]
        or page_evidence[0]["stream_id"] != availability_id
    ):
        raise ContractError(
            "bundle_preflight", "availability evidenceが固定IDの最初のraw attemptと不一致"
        )
    if report.get("stopped_after_openalex_429") is True:
        if not checkpoints or not isinstance(report.get("checkpoint"), Mapping):
            raise ContractError("bundle_preflight", "429 stopにcheckpointが無い")
        if report["checkpoint"] != checkpoints[-1]:
            raise ContractError(
                "bundle_preflight", "report checkpointがbundle tailと不一致"
            )
    elif report.get("checkpoint") is not None:
        raise ContractError("bundle_preflight", "非停止reportにcheckpointを付けられない")


def load_preflight_bundle(
    bundle_dir: Path,
    catalog: Mapping[str, Any],
    seal: Mapping[str, Any],
    *,
    _allow_nonproduction: bool = False,
) -> tuple[Mapping[str, Any], str]:
    validate_bundle(
        bundle_dir,
        catalog=catalog,
        seal=seal,
        _allow_nonproduction=_allow_nonproduction,
    )
    root = Path(bundle_dir)
    manifest, manifest_bytes, manifest_digest, _ = _read_bundle_manifest(root)
    if manifest.get("kind") != "preflight":
        raise ContractError("bundle_preflight", "run-readyにはpreflight bundleが必要")
    if (
        manifest.get("registration_seal_sha256") != seal.get("seal_sha256")
        or manifest.get("catalog_sha256") != seal.get("catalog_sha256")
    ):
        raise ContractError("bundle_preflight", "preflight bundleのregistration親が不一致")
    descriptor = manifest.get("preflight_report")
    if not isinstance(descriptor, Mapping):
        raise ContractError("bundle_preflight", "保存済みpreflight reportが必要")
    report_path = _safe_bundle_path(root, descriptor.get("path"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, Mapping):
        raise ContractError("bundle_preflight", "preflight report rootはobjectが必要")
    return report, manifest_digest


def _resume_preflight_from_wal(
    *,
    root: Path,
    manifest: Mapping[str, Any],
    catalog: Mapping[str, Any],
    seal: Mapping[str, Any],
    transport: Any,
    clock: Callable[[], datetime],
    sleeper: Callable[[float], None],
    limiter: HostLimiter,
    phase_argv: Mapping[str, Any],
) -> Mapping[str, Any]:
    journal = manifest.get("journal")
    if (
        not isinstance(journal, Mapping)
        or journal.get("schema_version") != _PREFLIGHT_WAL_VERSION
    ):
        raise ContractError("bundle_resume", "preflight resumeはpacked WALが必要")
    replayed = _replay_preflight_wal(root, journal)
    if replayed["attempt_intent"] is not None:
        return {
            "schema_version": "axis3-search-resume/v1",
            "status": "blocked",
            "complete": False,
            "reason": "unconfirmed_attempt_intent",
            "wire_attempt_count": None,
            "checkpoint": None,
            **phase_argv,
        }
    evidences = list(replayed["page_evidence"])
    bodies = list(replayed["page_bodies"])
    intents = list(replayed["committed_intents"])
    sequence_plan = _validate_preflight_wal_attempt_sequence(catalog, evidences)
    origin_phase_argv = manifest.get("origin_phase_argv")
    if not isinstance(origin_phase_argv, Mapping):
        raise ContractError("bundle_resume", "preflight origin phase argvが無い")
    rows_by_id = {row["stream_id"]: row for row in catalog["rows"]}
    availability_id = "AX3A1-L-ID-01@openalex"
    planned_rows = [
        rows_by_id[stream_id]
        for stream_id in sequence_plan["planned_stream_ids"]
    ]
    attempted_ids = {str(evidence["stream_id"]) for evidence in evidences}
    retry_row: Mapping[str, Any] | None = None
    lifecycle = manifest.get("lifecycle")
    if lifecycle == "finalized":
        descriptor = manifest.get("preflight_report")
        if not isinstance(descriptor, Mapping):
            raise ContractError("bundle_lifecycle", "finalized preflight reportが無い")
        try:
            existing_report = json.loads(
                _safe_bundle_path(root, descriptor.get("path")).read_text(encoding="utf-8")
            )
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ContractError("bundle_preflight", "finalized preflight reportを読めない") from exc
        if not isinstance(existing_report, Mapping):
            raise ContractError("bundle_preflight", "finalized preflight reportがobjectでない")
        if existing_report.get("stopped_after_openalex_429") is True:
            retry_row = rows_by_id[availability_id]
        elif sequence_plan["retry_stream_id"] is not None:
            retry_row = rows_by_id[str(sequence_plan["retry_stream_id"])]
        if retry_row is None:
            return {
                "schema_version": "axis3-search-resume/v1",
                "status": "already_finalized",
                "complete": True,
                "wire_attempt_count": len(evidences),
                "checkpoint": None,
                "preflight_report_sha256": existing_report["report_sha256"],
                "manifest_sha256": _read_bundle_manifest(root)[2],
                **phase_argv,
            }
    elif lifecycle != "in_progress":
        raise ContractError("bundle_lifecycle", "preflight resume lifecycleが不正")
    elif (
        evidences
        and evidences[-1].get("status") in RETRYABLE_HTTP_STATUSES
        and sequence_plan["retry_stream_id"] is not None
    ):
        retry_row = rows_by_id[str(evidences[-1]["stream_id"])]

    writer = _open_bundle_writer(
        transport,
        root,
        kind="preflight",
        seal=seal,
        phase_argv=phase_argv,
        resume=True,
    )
    if intents:
        budget = WireBudget(
            attempts=len(intents),
            first_external_request_at=_parse_time(str(intents[0]["intent_at"])),
        )
    else:
        budget = WireBudget()
    latest_checkpoint: Mapping[str, Any] | None = None

    def send_and_commit(row: Mapping[str, Any]) -> TransportResponse:
        nonlocal latest_checkpoint
        request = materialize_request(row)
        response = _send_with_raw_commit(
            transport,
            request,
            budget,
            clock,
            limiter=limiter,
            writer=writer,
            pass_number=0,
            page_number=0,
        )
        try:
            evidence, _classification = _validate_and_classify_response(
                row=row,
                request=request,
                response=response,
                pass_number=0,
                page_number=0,
                classify_preflight=True,
            )
        except ContractError:
            writer.materialize_pending_attempt()
            raise
        first_availability_429 = (
            budget.attempts == 1
            and row["stream_id"] == availability_id
            and response.status == 429
        )
        checkpoint: Mapping[str, Any] | None = None
        if first_availability_429:
            checkpoint = _quota_checkpoint(
                row=row,
                request=request,
                response=response,
                seal=seal,
                budget=budget,
                now=clock(),
            )
        elif response.status != 200:
            checkpoint = _response_checkpoint(
                row=row,
                request=request,
                response=response,
                seal=seal,
                budget=budget,
                now=clock(),
                run_id="axis3-live-preflight",
                pass_number=1,
                page_number=0,
                next_request=None,
            )
        latest_checkpoint = writer.commit_response(
            evidence=evidence,
            entity_body=response.entity_body,
            checkpoint=checkpoint,
        )
        return response

    first_response: TransportResponse | None = None
    resumed_row: Mapping[str, Any] | None = retry_row

    def send_retry_sequence(
        row: Mapping[str, Any], attempts_so_far: int
    ) -> tuple[TransportResponse, int]:
        nonlocal first_response, resumed_row
        response: TransportResponse | None = None
        while attempts_so_far < MAX_PREFLIGHT_ATTEMPTS_PER_STREAM:
            if attempts_so_far:
                sleeper(
                    PREFLIGHT_RETRY_BACKOFF_SECONDS[str(row["index"])][
                        attempts_so_far - 1
                    ]
                )
            response = send_and_commit(row)
            attempts_so_far += 1
            if first_response is None:
                first_response = response
                resumed_row = row
            if response.status not in RETRYABLE_HTTP_STATUSES:
                break
            if (
                len(writer.ledger) == 1
                and row["stream_id"] == availability_id
                and response.status == 429
            ):
                break
        assert response is not None
        return response, attempts_so_far

    if retry_row is not None:
        retry_count = int(sequence_plan["current_stream_attempts"])
        retry_response, retry_count = send_retry_sequence(retry_row, retry_count)
        attempted_ids.add(str(retry_row["stream_id"]))
        if (
            retry_row["index"] == "dblp"
            and retry_response.status in RETRYABLE_HTTP_STATUSES
            and retry_count >= MAX_PREFLIGHT_ATTEMPTS_PER_STREAM
        ):
            sleeper(DBLP_FAILURE_COOLDOWN_SECONDS)
    for planned in planned_rows:
        if planned["stream_id"] in attempted_ids:
            continue
        response, attempts_for_row = send_retry_sequence(planned, 0)
        attempted_ids.add(str(planned["stream_id"]))
        if (
            len(writer.ledger) == 1
            and planned["stream_id"] == availability_id
            and response.status == 429
        ):
            break
        if (
            planned["index"] == "dblp"
            and response.status in RETRYABLE_HTTP_STATUSES
            and attempts_for_row >= MAX_PREFLIGHT_ATTEMPTS_PER_STREAM
        ):
            remaining_ids = set(sequence_plan["planned_stream_ids"])
            if any(
                candidate["stream_id"] in remaining_ids
                and candidate["stream_id"] not in attempted_ids
                for candidate in planned_rows
            ):
                sleeper(DBLP_FAILURE_COOLDOWN_SECONDS)

    replayed = _replay_preflight_wal(root, writer._journal_descriptor(sealed=False))
    eligibility = _derive_finalize_eligibility(
        kind="preflight",
        ledger=replayed["ledger"],
        attempt_intent=replayed["attempt_intent"],
        wire_attempt_count=len(replayed["page_evidence"]),
    )
    if eligibility["finalize_eligible"] is not True:
        writer._write_state_pointer()
        return {
            "schema_version": "axis3-search-resume/v1",
            "stream_id": resumed_row["stream_id"] if resumed_row is not None else None,
            "request": materialize_request(resumed_row) if resumed_row is not None else None,
            "status": first_response.status if first_response is not None else "retryable_tail",
            "complete": False,
            "wire_attempt_count": len(replayed["page_evidence"]),
            "checkpoint": latest_checkpoint,
            "finalize_eligibility": eligibility,
            **phase_argv,
        }
    stop_initial = (
        len(replayed["page_evidence"]) == 1
        and replayed["page_evidence"][0]["stream_id"] == availability_id
        and replayed["page_evidence"][0]["status"] == 429
    )
    finished = _derive_preflight_report_from_wal(
        catalog=catalog,
        seal=seal,
        evidences=replayed["page_evidence"],
        bodies=replayed["page_bodies"],
        intents=replayed["committed_intents"],
        origin_phase_argv=writer.origin_phase_argv,
        stopped_initial_availability_429=stop_initial,
        stop_checkpoint=(replayed["checkpoint_values"].get(1) if stop_initial else None),
    )
    manifest_digest = writer.finalize_preflight(finished)
    load_preflight_bundle(
        root,
        catalog,
        seal,
    )
    return {
        "schema_version": "axis3-search-resume/v1",
        "stream_id": resumed_row["stream_id"] if resumed_row is not None else None,
        "request": materialize_request(resumed_row) if resumed_row is not None else None,
        "status": first_response.status if first_response is not None else "finalized_prefix",
        "complete": not stop_initial,
        "wire_attempt_count": len(replayed["page_evidence"]),
        "checkpoint": latest_checkpoint,
        "preflight_report_sha256": finished["report_sha256"],
        "manifest_sha256": manifest_digest,
        **phase_argv,
    }


def _request_position_from_url(row: Mapping[str, Any], url: str) -> int | str | None:
    position_kind = row["request_factory"]["position_kind"]
    if not isinstance(url, str):
        raise ContractError("bundle_resume_request", "checkpoint request URLが無い")
    try:
        query_pairs = parse_qsl(
            urlsplit(url).query,
            keep_blank_values=True,
            strict_parsing=True,
        )
    except ValueError as exc:
        raise ContractError("bundle_resume_request", "checkpoint request queryが不正") from exc
    if position_kind == "fixed":
        return None
    elif position_kind == "offset":
        position_key = "start" if row["index"] == "arxiv" else "f"
        values = [value for key, value in query_pairs if key == position_key]
        if len(values) != 1 or not values[0].isdigit():
            raise ContractError("bundle_resume_request", "offset request位置が一意な非負整数でない")
        return int(values[0])
    elif position_kind == "cursor":
        values = [value for key, value in query_pairs if key == "cursor"]
        if len(values) != 1 or not values[0]:
            raise ContractError("bundle_resume_request", "cursor request位置が一意でない")
        return quote(values[0], safe="")
    else:
        raise ContractError("bundle_resume_request", "未知のrequest位置kind")


def _validated_resume_request(
    row: Mapping[str, Any], resume_request: Mapping[str, Any]
) -> dict[str, Any]:
    """Reconstruct and compare the registered request before any transport call."""

    url = resume_request.get("url")
    position = _request_position_from_url(row, url)
    position_kind = row["request_factory"]["position_kind"]
    expected = materialize_request(row, position)
    candidate = {
        "stream_id": row["stream_id"],
        "index": row["index"],
        **copy.deepcopy(dict(resume_request)),
        "position_kind": position_kind,
    }
    if candidate != expected:
        raise ContractError("bundle_resume_request", "checkpoint requestがregistration catalogと不一致")
    return expected


def _resume_final_request_sequence(
    *,
    row: Mapping[str, Any],
    initial_request: Mapping[str, Any],
    checkpoint: Mapping[str, Any],
    transport: Any,
    budget: WireBudget,
    clock: Callable[[], datetime],
    limiter: HostLimiter,
    writer: BundleWriter,
    seal: Mapping[str, Any],
    successful_requests: set[
        tuple[str, str, int | None, str, tuple[tuple[str, str], ...]]
    ],
) -> tuple[Mapping[str, Any], int, Mapping[str, Any]]:
    """Finish every remaining page of the resumed stream before returning."""

    restart = checkpoint["resume_action"] == "restart_branch"
    resume_pass_number = checkpoint["pass_number"] + 1 if restart else checkpoint[
        "pass_number"
    ]
    page_number = 0 if restart else checkpoint["page_identity"]["page_number"]
    if checkpoint["resume_action"] == "continue_cursor":
        page_number += 1
    request = copy.deepcopy(dict(initial_request))
    while True:
        request_identity = _canonical_url(request["url"])
        if request_identity in successful_requests:
            raise ContractError("page_request_repeated", "resume中の成功済みrequest反復を拒否")
        response = _send_with_raw_commit(
            transport,
            request,
            budget,
            clock,
            limiter=limiter,
            writer=writer,
            pass_number=resume_pass_number,
            page_number=page_number,
        )
        evidence, lookup_probe = _validate_and_classify_response(
            row=row,
            request=request,
            response=response,
            pass_number=resume_pass_number,
            page_number=page_number,
            classify_preflight=False,
        )
        next_request = None
        if response.status == 200:
            position = _request_position_from_url(row, request["url"])
            _, next_position, terminal = _page_progress(row, response, position)
            if row["index"] == "dblp" and row["role"] == "main":
                validate_dblp_record_years(
                    response.entity_body,
                    int(row["cutoff_year"]),
                    str(row["record_year_locator"]),
                )
            if not terminal and (
                lookup_probe is None or lookup_probe["status"] == "ready"
            ):
                next_request = materialize_request(row, next_position)
        committed = writer.commit_response(
            evidence=evidence,
            entity_body=response.entity_body,
            checkpoint=_response_checkpoint(
                row=row,
                request=request,
                response=response,
                seal=seal,
                budget=budget,
                now=clock(),
                run_id=checkpoint["run_id"],
                pass_number=resume_pass_number,
                page_number=page_number,
                next_request=next_request,
            ),
        )
        if response.status == 200:
            successful_requests.add(request_identity)
        if next_request is None:
            return request, response.status, committed
        request = next_request
        page_number += 1


def _finalized_run_resume_status(
    root: Path,
    descriptor: Mapping[str, Any],
    phase_argv: Mapping[str, Any],
) -> dict[str, Any]:
    """Report lifecycle finality separately from the saved axis predicate."""

    try:
        run_result = json.loads(
            _safe_bundle_path(root, descriptor.get("path")).read_text(
                encoding="utf-8"
            )
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("bundle_run", "finalized run resultを読めない") from exc
    axis_complete = run_result.get("axis_complete") if isinstance(
        run_result, Mapping
    ) else None
    if not isinstance(axis_complete, bool):
        raise ContractError("bundle_run", "finalized run resultにaxis_completeが無い")
    return {
        "schema_version": "axis3-search-resume/v1",
        "status": "already_finalized",
        "lifecycle_complete": True,
        "axis_complete": axis_complete,
        "complete": axis_complete,
        "wire_attempt_count": None,
        "checkpoint": None,
        "run_result_sha256": descriptor["sha256"],
        **phase_argv,
    }


def resume_bundle(
    bundle_dir: Path,
    catalog: Mapping[str, Any],
    catalog_data: bytes,
    seal: Mapping[str, Any],
    *,
    argv: Sequence[str],
    commit: str,
    transport: Any,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    sleeper: Callable[[float], None] = time.sleep,
    preflight_bundle_dir: Path | None = None,
    effective_argv: Sequence[str] | None = None,
) -> Mapping[str, Any]:
    """Reconstruct saved state, resume exactly, then rejoin the ready-order loop."""

    validate_catalog(catalog)
    root = Path(bundle_dir)
    manifest, _, _, _ = _read_bundle_manifest(root)
    phase_argv = validate_effective_phase_argv(
        list(effective_argv if effective_argv is not None else argv), "resume"
    )
    _bind_transport_semantics(phase_argv, transport)
    _bind_semantic_path(phase_argv, "--bundle", bundle_dir)
    _bind_semantic_path(
        phase_argv, "--preflight-bundle", preflight_bundle_dir
    )
    validate_registration_seal(
        seal,
        catalog_data,
        argv=argv,
        commit=commit,
        enforce_head=phase_argv["artifact_class"] == "production",
    )
    if manifest.get("artifact_class") != phase_argv.get("artifact_class"):
        raise ContractError(
            "bundle_nonproduction",
            "resume transport classがorigin artifact classと不一致",
        )
    validate_bundle(
        bundle_dir,
        catalog=catalog,
        seal=seal,
        parent_preflight_bundle_dir=(
            preflight_bundle_dir if manifest.get("kind") == "final" else None
        ),
        _allow_in_progress=True,
    )
    if manifest.get("_finalize_recovered") is True:
        recovery_writer = _open_bundle_writer(
            transport,
            root,
            kind=str(manifest["kind"]),
            seal=seal,
            phase_argv=phase_argv,
            parent_preflight_manifest_sha256=manifest.get(
                "parent_preflight_manifest_sha256"
            ),
            resume=True,
        )
        recovery_writer._write_manifest(fold=True)
        manifest, _, _, _ = _read_bundle_manifest(root)
    pending = manifest.get("attempt_intent")
    if pending is not None:
        return {
            "schema_version": "axis3-search-resume/v1",
            "status": "blocked",
            "complete": False,
            "reason": "unconfirmed_attempt_intent",
            "wire_attempt_count": None,
            "checkpoint": None,
            **phase_argv,
        }
    limiter = HostLimiter(
        clock=clock,
        sleeper=sleeper,
        state_path=root / "state" / "host-limiter.json",
    )
    if manifest.get("kind") == "preflight":
        return _resume_preflight_from_wal(
            root=root,
            manifest=manifest,
            catalog=catalog,
            seal=seal,
            transport=transport,
            clock=clock,
            sleeper=sleeper,
            limiter=limiter,
            phase_argv=phase_argv,
        )
    if manifest.get("lifecycle") == "finalized":
        descriptor = manifest.get("run_result")
        if not isinstance(descriptor, Mapping):
            raise ContractError("bundle_lifecycle", "finalized final run-resultが無い")
        resumed = _finalized_run_resume_status(root, descriptor, phase_argv)
        resumed["manifest_sha256"] = _read_bundle_manifest(root)[2]
        return resumed
    checkpoints = manifest.get("checkpoints")
    if not isinstance(checkpoints, list) or not checkpoints:
        raise ContractError("bundle_resume", "resume可能なcheckpointが無い")
    last_entry = checkpoints[-1]
    if not isinstance(last_entry, Mapping):
        raise ContractError("bundle_checkpoint_downgrade", "文字列checkpointを拒否")
    relative = last_entry.get("path")
    checkpoint = json.loads(_safe_bundle_path(root, relative).read_text(encoding="utf-8"))
    validate_checkpoint(checkpoint)
    parser_digest, runner_digest, schema_digest = _checkpoint_source_digests(seal)
    if (
        checkpoint["registration_seal_sha256"] != seal["seal_sha256"]
        or checkpoint["catalog_sha256"] != seal["catalog_sha256"]
        or checkpoint["parser_sha256"] != parser_digest
        or checkpoint["runner_sha256"] != runner_digest
        or checkpoint["schema_sha256"] != schema_digest
    ):
        raise ContractError("bundle_resume", "checkpoint registration closureが現在sealと不一致")
    action = checkpoint["resume_action"]
    if action == "continue_cursor":
        resume_request = checkpoint["continue_cursor_request"]
    elif action == "restart_branch":
        resume_request = checkpoint["restart_branch_request"]
    elif action == "not_applicable" and manifest.get("kind") == "final":
        resume_request = None
    else:
        raise ContractError("bundle_resume", f"checkpoint action {action}はrequest resume不可")
    rows_by_id = {row["stream_id"]: row for row in catalog["rows"]}
    row = rows_by_id.get(checkpoint["stream_id"])
    if row is None:
        raise ContractError("bundle_resume", "checkpoint streamがcatalogに無い")
    request = (
        _validated_resume_request(row, resume_request)
        if resume_request is not None
        else None
    )
    try:
        saved_ledger = _load_manifest_ledger(root, manifest)
    except ContractError as exc:
        raise ContractError("bundle_resume", "resume ledgerを再構成できない") from exc
    if not isinstance(saved_ledger, list):
        raise ContractError("bundle_resume", "resume ledgerはarrayが必要")
    successful_requests = {
        _canonical_url(entry["request"]["url"])
        for entry in saved_ledger
        if isinstance(entry, Mapping)
        and entry.get("stream_id") == row["stream_id"]
        and entry.get("status") == 200
        and isinstance(entry.get("request"), Mapping)
        and isinstance(entry["request"].get("url"), str)
    }
    if (
        request is not None
        and action != "restart_branch"
        and _canonical_url(request["url"]) in successful_requests
    ):
        raise ContractError("bundle_resume_request", "成功済みpage requestの再送を拒否")
    budget = WireBudget(
        attempts=checkpoint["wire_attempt_count"],
        first_external_request_at=_parse_time(checkpoint["first_external_request_at"]),
    )
    writer = _open_bundle_writer(
        transport,
        root,
        kind=str(manifest["kind"]),
        seal=seal,
        phase_argv=phase_argv,
        parent_preflight_manifest_sha256=manifest.get(
            "parent_preflight_manifest_sha256"
        ),
        resume=True,
    )
    if request is None:
        resumed_request: Mapping[str, Any] | None = None
        resumed_status: int | str = "already_committed"
        committed = checkpoint
    else:
        resumed_request, resumed_status, committed = _resume_final_request_sequence(
            row=row,
            initial_request=request,
            checkpoint=checkpoint,
            transport=transport,
            budget=budget,
            clock=clock,
            limiter=limiter,
            writer=writer,
            seal=seal,
            successful_requests=(
                set() if action == "restart_branch" else successful_requests
            ),
        )
    current_manifest, _, _, _ = _read_bundle_manifest(root)
    page_entries = current_manifest["pages"]
    checkpoint_entries = current_manifest["checkpoints"]
    ledger = _load_manifest_ledger(root, current_manifest)
    materials_by_stream: list[
        tuple[str, list[tuple[Mapping[str, Any], bytes, Mapping[str, Any]]]]
    ] = []
    for page_entry, checkpoint_entry, ledger_entry in zip(
        page_entries, checkpoint_entries, ledger
    ):
        metadata = json.loads(
            _safe_bundle_path(root, page_entry["metadata_path"]).read_text(
                encoding="utf-8"
            )
        )
        body = _safe_bundle_path(root, page_entry["entity_body_path"]).read_bytes()
        saved_checkpoint = json.loads(
            _safe_bundle_path(root, checkpoint_entry["path"]).read_text(
                encoding="utf-8"
            )
        )
        stream_id = str(ledger_entry["stream_id"])
        if materials_by_stream and materials_by_stream[-1][0] == stream_id:
            materials_by_stream[-1][1].append((metadata, body, saved_checkpoint))
        else:
            materials_by_stream.append(
                (stream_id, [(metadata, body, saved_checkpoint)])
            )
    if preflight_bundle_dir is None:
        raise ContractError("bundle_parent", "final resumeにはpreflight親bundleが必要")
    parent_report, parent_digest = load_preflight_bundle(
        preflight_bundle_dir,
        catalog,
        seal,
    )
    if parent_digest != current_manifest["parent_preflight_manifest_sha256"]:
        raise ContractError("bundle_parent", "resume preflight親digestが不一致")
    statuses = {item["stream_id"]: item["status"] for item in parent_report["rows"]}
    ready_rows = _ordered_ready_rows(catalog, statuses)
    ready_ids = [item["stream_id"] for item in ready_rows]
    if [stream_id for stream_id, _ in materials_by_stream] != ready_ids[
        : len(materials_by_stream)
    ]:
        raise ContractError("bundle_execution_order", "resume ledgerがready順prefixでない")
    results: list[dict[str, Any]] = []
    for stream_id, materials in materials_by_stream:
        derived = _derive_latest_stream_result(rows_by_id[stream_id], materials)
        derived.pop("next_position", None)
        results.append(derived)
    if results and results[-1]["complete"]:
        for next_row in ready_rows[len(results) :]:
            stream_result = _run_stream(
                next_row,
                transport,
                budget,
                clock,
                limiter=limiter,
                writer=writer,
                seal=seal,
            )
            results.append(stream_result)
            if not stream_result["complete"]:
                break
    execution_order = [result["stream_id"] for result in results]
    run_result = {
        "schema_version": "axis3-search-run-ready/v1",
        "registration_seal_sha256": seal["seal_sha256"],
        "preflight_report_sha256": parent_report["report_sha256"],
        "parent_preflight_manifest_sha256": parent_digest,
        "execution_order": execution_order,
        "registered_ready_order": ready_ids,
        "effective_argv": phase_argv["effective_argv"],
        "effective_argv_sha256": phase_argv["effective_argv_sha256"],
        "phase_argv_contract_sha256": phase_argv["phase_argv_contract_sha256"],
        "results": results,
        "wire_attempt_count": budget.attempts,
        "first_external_request_at": parent_report["first_external_request_at"],
        "deadline_at": parent_report["deadline_at"],
        "axis_complete": False,
        "axis_incomplete_reason": (
            "row-level ready execution does not complete blocked/unavailable rows, "
            "record screening, work-family adjudication, or sensitivity audit"
        ),
    }
    eligibility = _derive_finalize_eligibility(
        kind="final",
        ledger=writer.ledger,
        attempt_intent=writer.attempt_intent,
        wire_attempt_count=budget.attempts,
    )
    if eligibility["finalize_eligible"] is not True:
        writer._write_state_pointer()
        current_result = next(
            result for result in results if result["stream_id"] == row["stream_id"]
        )
        return {
            "schema_version": "axis3-search-resume/v1",
            "stream_id": row["stream_id"],
            "request": resumed_request,
            "status": resumed_status,
            "complete": current_result["complete"],
            "wire_attempt_count": budget.attempts,
            "checkpoint": committed,
            "finalize_eligibility": eligibility,
            **phase_argv,
        }
    manifest_digest = writer.finalize_run(run_result)
    validate_bundle(
        root,
        catalog=catalog,
        seal=seal,
        parent_preflight_bundle_dir=preflight_bundle_dir,
    )
    current_result = next(
        result for result in results if result["stream_id"] == row["stream_id"]
    )
    return {
        "schema_version": "axis3-search-resume/v1",
        "stream_id": row["stream_id"],
        "request": resumed_request,
        "status": resumed_status,
        "complete": current_result["complete"],
        "wire_attempt_count": budget.attempts,
        "checkpoint": committed,
        "run_result": run_result,
        "manifest_sha256": manifest_digest,
        **phase_argv,
    }


class NonProductionTransport:
    """Exact callback transport for hermetic tests; never production-capable."""

    _axis3_artifact_class = "nonproduction_simulation"
    __slots__ = ("_handler", "calls")

    def __init__(self, handler: Callable[[Mapping[str, Any]], Any]):
        if not callable(handler):
            raise ContractError("test_transport", "handlerがcallableでない")
        self._handler = handler
        self.calls: list[Mapping[str, Any]] = []

    def send(self, request: Mapping[str, Any]) -> Any:
        outgoing = copy.deepcopy(dict(request))
        self.calls.append(outgoing)
        return self._handler(outgoing)


class ScriptedTransport:
    """Finite fake transport used by the CLI and tests; it cannot access HTTP."""

    _axis3_artifact_class = "nonproduction_simulation"
    __slots__ = ("_responses", "calls")

    def __init__(self, responses: Sequence[Mapping[str, Any]]):
        self._responses = [copy.deepcopy(dict(response)) for response in responses]
        self.calls: list[Mapping[str, Any]] = []

    def send(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        self.calls.append(copy.deepcopy(dict(request)))
        if not self._responses:
            raise ContractError("fake_transport_exhausted", "fake response scriptを使い切った")
        return self._responses.pop(0)
