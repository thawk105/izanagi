# -*- coding: utf-8 -*-
"""Evidence-derived admission metadata for campaign builds.

The sealed runtime values and exact canonical receipts in this module prevent accidental class
selection and make provenance structurally checkable.  The repository AST audit covers direct
calls reached from imports of this module, non-call uses of those imported low-level bindings,
and statically resolved ``import_module`` / ``getattr`` / ``globals`` lookups.  It does not model
``eval`` / ``exec``, strings assembled only at runtime, values injected from outside the scanned
module, monkeypatched import machinery or builtins, or non-Python issuers.  Registered CLI actions
enforce the registered inventory at flag use.  They do **not** authenticate an issuer: a caller in
the same process can invoke the private factories directly, register an ``argparse`` action of its
own, or mutate process memory.  This is misuse prevention and provenance structuring, not a
security boundary against an in-process caller.

The following boundaries are deliberately still open and receive no security credit here:
in-process issuers, shell materializers, arbitrary binary paths, runnable scripts under
``output/**``, the ABA/mixed-snapshot window between evidence capture and compilation, and
transitive provenance through older artifacts.  registry への登録は下流の拒否を起こさない。成果物の
隔離は成立しておらず、それは T-841 の範囲である。In particular, a receipt proves canonical
structure and internal consistency, not that a human or generator really acted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from .axis_trigger_gating import (
    FROZEN_TEMPLATE_BLOCK_BYTES,
    FROZEN_TEMPLATE_EPILOGUE_BYTES,
    FROZEN_TEMPLATE_HOLE_BYTES,
    MARKER_ID as TRIGGER_MARKER_ID,
    PREDICATE_HOLE_INDENT as TRIGGER_PREDICATE_HOLE_INDENT,
    SOURCE_REL as TRIGGER_SOURCE_REL,
)
from .materializer_admission import require_registered_coder_entrypoint
from .pin import CURRENT_PIN
from .reflux_ir import TriggerGateIR, emit_predicate
from .source_digest import STOCK, SourceEvidence


ADMISSION_SCHEMA = "build-admission/v1"
POLICY_SCHEMA = "build-admission-policy/v1"
GENERATOR_RECEIPT_SCHEMA = "generator-receipt/v1"
REVIEW_RECEIPT_SCHEMA = "source-review/v1"
_AUTHORITY_KIND = "cli-opt-in"
_SEAL = object()
_ISSUED_AUTHORITY_NONCES: set[str] = set()
_CLAIMED_AUTHORITY_NONCES: set[str] = set()
_TRIGGER_MARKER_BYTES = TRIGGER_MARKER_ID.encode("ascii")
_TRIGGER_BEGIN_DIRECTIVE_RE = re.compile(
    rb"^[ \t]*//[ \t]*EVOLVE-BLOCK-BEGIN[ \t]+"
    + re.escape(_TRIGGER_MARKER_BYTES)
    + rb"[ \t]*(?:\r\n|\n|\r|\Z)",
    re.IGNORECASE | re.MULTILINE,
)
_TRIGGER_END_DIRECTIVE_RE = re.compile(
    rb"^[ \t]*//[ \t]*EVOLVE-BLOCK-END[ \t]+"
    + re.escape(_TRIGGER_MARKER_BYTES)
    + rb"[ \t]*(?:\r\n|\n|\r|\Z)",
    re.IGNORECASE | re.MULTILINE,
)
_TRIGGER_SKELETON_TOKENS = (b"BACKOFF_TRIGGER_GATING", b"izanagi_gate_pass")
_TRIGGER_REJECTION_MESSAGE = "trigger axis predicate が materialized source と不一致"
_TRIGGER_EXPECTED_HOLE_BYTES = tuple(
    (
        TRIGGER_PREDICATE_HOLE_INDENT
        + emit_predicate(TriggerGateIR(mask))
    ).encode("utf-8")
    for mask in range(32)
)
_TRIGGER_TEMPLATE_PREFIX, _TRIGGER_TEMPLATE_SEPARATOR, _TRIGGER_TEMPLATE_SUFFIX = (
    FROZEN_TEMPLATE_BLOCK_BYTES.partition(FROZEN_TEMPLATE_HOLE_BYTES)
)
if (
    not _TRIGGER_TEMPLATE_SEPARATOR
    or FROZEN_TEMPLATE_HOLE_BYTES in _TRIGGER_TEMPLATE_SUFFIX
):
    raise RuntimeError("frozen trigger template hole must occur exactly once")


class BuildAdmissionError(RuntimeError):
    """Source evidence did not support exactly one admitted build class."""


class BuildProvenance(str, Enum):
    """Classes derived by :func:`derive_build_admission`, never selected by callers."""

    STOCK_BASELINE = "stock-baseline"
    CODER_AUTHORED = "coder-authored"
    MACHINE_GENERATED = "machine-generated"
    HUMAN_REVIEWED = "human-reviewed"

    # Source-compatible names for code migrating from T-316.  Construction remains sealed, so
    # these aliases do not retain the old caller-declaration acceptance path.
    STOCK_OR_PINNED = STOCK_BASELINE
    CODER_DERIVED = CODER_AUTHORED
    MACHINE_SWEEP = MACHINE_GENERATED


class GeneratorId(str, Enum):
    """Closed registry of production source generators."""

    BACKOFF_OVERTHROTTLE = "backoff-overthrottle"
    BACKOFF_PROFILE = "backoff-profile"
    BACKOFF_REPRO = "backoff-repro"
    BACKOFF_SWEEP = "backoff-sweep"
    S1_EXTIME_CALIBRATION = "s1-extime-calibration"
    S6_SORT_SWEEP = "s6-sort-sweep"
    S8A_TRIGGER_SWEEP = "s8a-trigger-sweep"


class ReviewId(str, Enum):
    """Closed registry of source-bound human-review checkpoints."""

    S1_KNOWN_AXES = "s1-known-axes"
    S8B_FLOOR = "s8b-floor"
    S8B_ORACLE = "s8b-oracle"


def _canonical_json(value: Mapping[str, object]) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    except (TypeError, ValueError) as exc:
        raise BuildAdmissionError("receipt は canonical JSON に変換可能である必要がある") from exc


def _sha256_map(value: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _is_sha256(value: object) -> bool:
    if type(value) is not str or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def _require_exact_keys(value: object, expected: frozenset[str], label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != expected:
        got = sorted(repr(key) for key in value) if isinstance(value, Mapping) else type(value).__name__
        raise BuildAdmissionError(f"{label} の key 集合が不正: expected={sorted(expected)} got={got}")
    if any(type(key) is not str for key in value):
        raise BuildAdmissionError(f"{label} の key は exact str が必要")
    return value


def _source_map(source: SourceEvidence) -> dict[str, object]:
    if type(source) is not SourceEvidence:
        raise BuildAdmissionError("source は resolve_evidence() 由来の exact SourceEvidence が必要")
    try:
        return source.as_receipt()
    except (AttributeError, TypeError, ValueError) as exc:
        raise BuildAdmissionError("SourceEvidence の canonical body が不正") from exc


def _reject_trigger_axis() -> None:
    raise BuildAdmissionError(_TRIGGER_REJECTION_MESSAGE) from None


def _require_materialized_trigger_axis_predicate(evidence: SourceEvidence) -> None:
    """凍結 frame と隣接 epilogue の raw bytes だけを検査する。

    生きた C++ であることは保証しない。R1 のコメント化、raw string の囮、前処理器による
    識別子置換、R3 の evidence 取得から compiler read までの ABA 窓は残る。さらに R4 の
    prologue での ``izanagi_gate_pass`` 再宣言（型差し替えによる代入・真理値の無効化）、
    R5 の宣言と BEGIN の間の制御流変更（``return;`` 等）による hole/gated call の非到達化、
    R6 の epilogue 直後への dangling ``else`` 付加による常時 backoff 化、R7 の block と epilogue を
    逐語一致させたまま行う call target／引数の名前解決差し替え（宣言と BEGIN の間等での
    ``Backoff`` や ``FLAGS_clocks_per_us`` の local shadowing）も残る。
    source が存在しない場合（``FileNotFoundError``）と、BEGIN/END marker も skeleton token も無い
    source の場合、この検査は発火せず受理する。
    C++ 字句解析、BOM/NUL/decode の source 全体検査は行わない。
    """

    source_path = os.path.join(evidence.source_root, TRIGGER_SOURCE_REL)
    try:
        with open(source_path, "rb") as source_file:
            raw = source_file.read()
    except FileNotFoundError:
        return
    except OSError:
        _reject_trigger_axis()

    begins = tuple(_TRIGGER_BEGIN_DIRECTIVE_RE.finditer(raw))
    ends = tuple(_TRIGGER_END_DIRECTIVE_RE.finditer(raw))
    if not begins and not ends:
        if any(token in raw for token in _TRIGGER_SKELETON_TOKENS):
            _reject_trigger_axis()
        return
    if len(begins) != 1 or len(ends) != 1 or begins[0].start() >= ends[0].start():
        _reject_trigger_axis()

    epilogue_start = ends[0].end()
    epilogue_end = epilogue_start + len(FROZEN_TEMPLATE_EPILOGUE_BYTES)
    if raw[epilogue_start:epilogue_end] != FROZEN_TEMPLATE_EPILOGUE_BYTES:
        _reject_trigger_axis()

    block = raw[begins[0].start():ends[0].end()]
    if block == FROZEN_TEMPLATE_BLOCK_BYTES:
        return
    if not (
        block.startswith(_TRIGGER_TEMPLATE_PREFIX)
        and block.endswith(_TRIGGER_TEMPLATE_SUFFIX)
    ):
        _reject_trigger_axis()
    hole_end = len(block) - len(_TRIGGER_TEMPLATE_SUFFIX)
    hole = block[len(_TRIGGER_TEMPLATE_PREFIX):hole_end]
    if hole not in _TRIGGER_EXPECTED_HOLE_BYTES:
        _reject_trigger_axis()


@dataclass(frozen=True, slots=True, init=False)
class CoderBuildAuthority:
    """Opaque, process-local token issued only by a private argparse action."""

    _nonce: str
    _coder_entrypoint_site: str | None

    def __init__(
        self,
        nonce: str,
        coder_entrypoint_site: str | None,
        *,
        _seal: object = None,
    ) -> None:
        if _seal is not _SEAL:
            raise BuildAdmissionError("CoderBuildAuthority は parser action だけが発行できる")
        object.__setattr__(self, "_nonce", nonce)
        object.__setattr__(self, "_coder_entrypoint_site", coder_entrypoint_site)


@dataclass(frozen=True, slots=True, init=False)
class BuildAdmissionPolicy:
    """Stable, nonce-free admission policy identity."""

    _preimage_json: str
    sha256: str

    def __init__(self, preimage: Mapping[str, object], *, _seal: object = None) -> None:
        if _seal is not _SEAL:
            raise BuildAdmissionError("BuildAdmissionPolicy は build_run_context() が発行する")
        rendered = _canonical_json(preimage)
        object.__setattr__(self, "_preimage_json", rendered)
        object.__setattr__(self, "sha256", hashlib.sha256(rendered.encode("utf-8")).hexdigest())

    def as_preimage(self) -> Mapping[str, object]:
        return json.loads(self._preimage_json)


_HISTORICAL_POLICY_KEYS = frozenset({
    "schema", "repo_stock_pin", "coder_authority",
    "generator_registry", "review_registry",
})
_HISTORICAL_POLICY_SCHEMA = "build-admission-policy/v1"


@dataclass(frozen=True, slots=True, init=False)
class HistoricalBuildAdmissionPolicy:
    """Recorded policy shape and identity, not proof of historical authority."""

    _preimage_json: str
    sha256: str

    def __init__(self, preimage: Mapping[str, object], *, _seal: object = None) -> None:
        if _seal is not _SEAL:
            raise BuildAdmissionError("HistoricalBuildAdmissionPolicy requires historical decoder")
        rendered = _canonical_json(preimage)
        object.__setattr__(self, "_preimage_json", rendered)
        object.__setattr__(self, "sha256", hashlib.sha256(rendered.encode("utf-8")).hexdigest())

    def as_preimage(self) -> Mapping[str, object]:
        return json.loads(self._preimage_json)


def decode_historical_build_admission_policy(value: object) -> HistoricalBuildAdmissionPolicy:
    """Preserve recorded values; validate only the independently fixed v1 shape."""
    if type(value) is not dict:
        raise BuildAdmissionError("historical build admission policy requires exact dict")
    body = _require_exact_keys(value, _HISTORICAL_POLICY_KEYS, "historical build admission policy")
    if body["schema"] != _HISTORICAL_POLICY_SCHEMA:
        raise BuildAdmissionError("historical build admission policy schema differs")
    for key in ("repo_stock_pin", "coder_authority"):
        if type(body[key]) is not str:
            raise BuildAdmissionError(f"historical build admission policy {key} requires exact str")
    for key in ("generator_registry", "review_registry"):
        if type(body[key]) is not list or any(type(item) is not str for item in body[key]):
            raise BuildAdmissionError(f"historical build admission policy {key} requires list of exact str")
    return HistoricalBuildAdmissionPolicy(body, _seal=_SEAL)


@dataclass(frozen=True, slots=True, init=False)
class BuildRunContext:
    """One process-local run context for generator and optional CLI authority receipts."""

    _policy: BuildAdmissionPolicy
    _generator_id: GeneratorId
    _context_nonce: str
    _authority_nonce: str | None
    _coder_entrypoint_site: str | None

    def __init__(
        self,
        policy: BuildAdmissionPolicy,
        generator_id: GeneratorId,
        context_nonce: str,
        authority_nonce: str | None,
        coder_entrypoint_site: str | None,
        *,
        _seal: object = None,
    ) -> None:
        if _seal is not _SEAL:
            raise BuildAdmissionError("BuildRunContext は build_run_context() が発行する")
        object.__setattr__(self, "_policy", policy)
        object.__setattr__(self, "_generator_id", generator_id)
        object.__setattr__(self, "_context_nonce", context_nonce)
        object.__setattr__(self, "_authority_nonce", authority_nonce)
        object.__setattr__(self, "_coder_entrypoint_site", coder_entrypoint_site)

    @property
    def policy(self) -> BuildAdmissionPolicy:
        return self._policy

    @property
    def generator_id(self) -> GeneratorId:
        return self._generator_id


@dataclass(frozen=True, slots=True, init=False)
class GeneratorReceipt:
    """Runtime generator receipt with a full canonical persistent body."""

    _body_json: str
    _context_nonce: str

    def __init__(self, body: Mapping[str, object], context_nonce: str, *, _seal: object = None) -> None:
        if _seal is not _SEAL:
            raise BuildAdmissionError("GeneratorReceipt は attest_generator_output() が発行する")
        object.__setattr__(self, "_body_json", _canonical_json(body))
        object.__setattr__(self, "_context_nonce", context_nonce)

    def as_receipt(self) -> Mapping[str, object]:
        return json.loads(self._body_json)


@dataclass(frozen=True, slots=True, init=False)
class ReviewReceipt:
    """Validated source-bound review receipt; authenticity is outside this process boundary."""

    _body_json: str

    def __init__(self, body: Mapping[str, object], *, _seal: object = None) -> None:
        if _seal is not _SEAL:
            raise BuildAdmissionError("ReviewReceipt は verify_review_receipt() が発行する")
        object.__setattr__(self, "_body_json", _canonical_json(body))

    def as_receipt(self) -> Mapping[str, object]:
        return json.loads(self._body_json)


@dataclass(frozen=True, slots=True, init=False)
class BuildAdmission:
    """Sealed admission whose persistent projection contains every receipt body."""

    _provenance: BuildProvenance
    _body_json: str

    def __init__(
        self,
        provenance: BuildProvenance,
        body: Mapping[str, object],
        *,
        _seal: object = None,
    ) -> None:
        if _seal is not _SEAL:
            raise BuildAdmissionError("BuildAdmission は derive_build_admission() だけが発行する")
        object.__setattr__(self, "_provenance", provenance)
        object.__setattr__(self, "_body_json", _canonical_json(body))

    @property
    def provenance(self) -> BuildProvenance:
        return self._provenance

    @property
    def provenance_class(self) -> BuildProvenance:
        """Compatibility spelling for callers migrating from T-316."""

        return self._provenance

    @property
    def receipt_sha256(self) -> str:
        return str(json.loads(self._body_json)["receipt_sha256"])

    def as_cache_identity(self) -> Mapping[str, object]:
        return json.loads(self._body_json)

    def as_wal_receipt(self) -> Mapping[str, object]:
        return json.loads(self._body_json)


class _CoderAuthorityAction(argparse.Action):
    """Low-level action retained for build-admission unit fixtures only."""

    def __call__(self, parser, namespace, values, option_string=None) -> None:
        self._issue(namespace, coder_entrypoint_site=None)

    def _issue(self, namespace, *, coder_entrypoint_site: str | None) -> None:
        nonce = secrets.token_hex(32)
        _ISSUED_AUTHORITY_NONCES.add(nonce)
        setattr(
            namespace,
            self.dest,
            CoderBuildAuthority(nonce, coder_entrypoint_site, _seal=_SEAL),
        )


class _RegisteredCoderAuthorityAction(_CoderAuthorityAction):
    """Flag-time registry gate for production coder authority issuers."""

    def __init__(self, *args, coder_entrypoint_site: str, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._coder_entrypoint_site = coder_entrypoint_site

    def __call__(self, parser, namespace, values, option_string=None) -> None:
        try:
            require_registered_coder_entrypoint(self._coder_entrypoint_site)
        except ValueError as exc:
            raise BuildAdmissionError(str(exc)) from exc
        self._issue(
            namespace,
            coder_entrypoint_site=self._coder_entrypoint_site,
        )


def add_coder_build_authority_argument(
    parser: argparse.ArgumentParser,
    *,
    dest: str = "coder_build_authority",
) -> None:
    """Add the low-level flag issuer retained for admission-unit fixtures.

    Production entry points must use
    :func:`add_registered_coder_build_authority_argument`.  Keeping this in-process issuer
    callable is an explicit compatibility seam, not an authentication boundary.
    """

    if type(parser) is not argparse.ArgumentParser:
        raise TypeError("parser は argparse.ArgumentParser の exact instance が必要")
    parser.add_argument(
        "--allow-coder-derived-build",
        dest=dest,
        action=_CoderAuthorityAction,
        nargs=0,
        default=None,
        help="permit coder-derived source builds for this invocation",
    )


def add_registered_coder_build_authority_argument(
    parser: argparse.ArgumentParser,
    *,
    coder_entrypoint_site: str,
    dest: str = "coder_build_authority",
) -> None:
    """Add the public flag with an exact, flag-time registered-site requirement.

    The site is 保存済み・未消費: it is stored on the process-local authority object and run
    context but is not consumed by admission derivation, so it is not a rejection gate.  It is not
    added to the persistent admission receipt, WAL, cache identity, COMMIT, or freeze data.
    Registration also does not prove quarantine ran or cause downstream artifact rejection.  A
    same-process caller can still invoke the low-level issuer directly, so this is not an
    authentication boundary.
    """

    if type(parser) is not argparse.ArgumentParser:
        raise TypeError("parser は argparse.ArgumentParser の exact instance が必要")
    if type(coder_entrypoint_site) is not str:
        raise TypeError("coder_entrypoint_site は exact str が必要")
    parser.add_argument(
        "--allow-coder-derived-build",
        dest=dest,
        action=_RegisteredCoderAuthorityAction,
        coder_entrypoint_site=coder_entrypoint_site,
        nargs=0,
        default=None,
        help="permit coder-derived source builds for this invocation",
    )


def _new_policy() -> BuildAdmissionPolicy:
    preimage: dict[str, object] = {
        "schema": POLICY_SCHEMA,
        "repo_stock_pin": CURRENT_PIN,
        "coder_authority": _AUTHORITY_KIND,
        "generator_registry": sorted(member.value for member in GeneratorId),
        "review_registry": sorted(member.value for member in ReviewId),
    }
    return BuildAdmissionPolicy(preimage, _seal=_SEAL)


def resolve_current_build_admission_policy() -> BuildAdmissionPolicy:
    """Artifact から独立に現行 build admission policy を再構築する。

    durable consumer は receipt 内の policy を期待値へ流用せず、この resolver を
    authority として使う。返却値は nonce を持たず、同じ ``CURRENT_PIN`` と registry
    から常に同じ identity を導く。
    """

    return _new_policy()


def build_run_context(
    *,
    generator_id: GeneratorId,
    coder_authority: CoderBuildAuthority | None = None,
) -> BuildRunContext:
    """Create one run context, consuming an optional parser-issued authority exactly once."""

    if type(generator_id) is not GeneratorId:
        raise BuildAdmissionError("generator_id は registered GeneratorId の exact member が必要")
    authority_nonce = None
    coder_entrypoint_site = None
    if coder_authority is not None:
        if type(coder_authority) is not CoderBuildAuthority:
            raise BuildAdmissionError("coder_authority は parser 発行 token の exact type が必要")
        authority_nonce = coder_authority._nonce
        if authority_nonce not in _ISSUED_AUTHORITY_NONCES:
            raise BuildAdmissionError("coder_authority はこの process の parser が発行していない")
        if authority_nonce in _CLAIMED_AUTHORITY_NONCES:
            raise BuildAdmissionError("coder_authority は別 run context で既に使用済み")
        _CLAIMED_AUTHORITY_NONCES.add(authority_nonce)
        coder_entrypoint_site = coder_authority._coder_entrypoint_site
    return BuildRunContext(
        _new_policy(), generator_id, secrets.token_hex(32), authority_nonce,
        coder_entrypoint_site, _seal=_SEAL
    )


def attest_generator_output(
    context: BuildRunContext,
    source: SourceEvidence,
    *,
    generator_input_sha256: str,
) -> GeneratorReceipt:
    """Bind the context's registered generator and input digest to exact source evidence."""

    if type(context) is not BuildRunContext:
        raise BuildAdmissionError("context は build_run_context() 由来の exact value が必要")
    source_body = _source_map(source)
    if not _is_sha256(generator_input_sha256):
        raise BuildAdmissionError("generator_input_sha256 は lowercase SHA-256 が必要")
    body: dict[str, object] = {
        "schema": GENERATOR_RECEIPT_SCHEMA,
        "generator_id": context.generator_id.value,
        "source": source_body,
        "generator_input_sha256": generator_input_sha256,
    }
    body["receipt_sha256"] = _sha256_map(body)
    return GeneratorReceipt(body, context._context_nonce, _seal=_SEAL)


_GENERATOR_KEYS = frozenset({
    "schema", "generator_id", "source", "generator_input_sha256", "receipt_sha256",
})
_REVIEW_KEYS = frozenset({
    "schema", "review_id", "source", "input_sha256", "receipt_sha256",
})
_ADMISSION_KEYS = frozenset({
    "schema", "class", "policy_sha256", "source", "generator_id", "review_id",
    "input_sha256", "generator_receipt", "review_receipt", "authority_kind",
    "receipt_sha256",
})


def _validate_generator_body(value: object, source_body: Mapping[str, object]) -> Mapping[str, object]:
    body = _require_exact_keys(value, _GENERATOR_KEYS, "generator receipt")
    if body["schema"] != GENERATOR_RECEIPT_SCHEMA:
        raise BuildAdmissionError("generator receipt schema が不一致")
    try:
        GeneratorId(body["generator_id"])
    except (TypeError, ValueError) as exc:
        raise BuildAdmissionError("generator receipt の generator_id が未登録") from exc
    if body["source"] != source_body:
        raise BuildAdmissionError("generator receipt は対象 source evidence に束縛されていない")
    if not _is_sha256(body["generator_input_sha256"]):
        raise BuildAdmissionError("generator receipt の input digest が不正")
    if not _is_sha256(body["receipt_sha256"]):
        raise BuildAdmissionError("generator receipt の outer SHA が不正")
    unsigned = dict(body)
    outer = unsigned.pop("receipt_sha256")
    if _sha256_map(unsigned) != outer:
        raise BuildAdmissionError("generator receipt の outer SHA が canonical body と不一致")
    return body


def verify_review_receipt(
    review_id: ReviewId,
    source: SourceEvidence,
    *,
    receipt: Mapping[str, object],
) -> ReviewReceipt:
    """Validate an exact, source-bound review body and return its sealed runtime projection.

    This checks structure and equality only.  It does not authenticate the human reviewer.
    """

    if type(review_id) is not ReviewId:
        raise BuildAdmissionError("review_id は registered ReviewId の exact member が必要")
    source_body = _source_map(source)
    body = _require_exact_keys(receipt, _REVIEW_KEYS, "review receipt")
    if body["schema"] != REVIEW_RECEIPT_SCHEMA or body["review_id"] != review_id.value:
        raise BuildAdmissionError("review receipt の schema/review_id が不一致")
    if body["source"] != source_body:
        raise BuildAdmissionError("review receipt は対象 source evidence に束縛されていない")
    if not _is_sha256(body["input_sha256"]) or not _is_sha256(body["receipt_sha256"]):
        raise BuildAdmissionError("review receipt の input/outer SHA が不正")
    unsigned = dict(body)
    outer = unsigned.pop("receipt_sha256")
    if _sha256_map(unsigned) != outer:
        raise BuildAdmissionError("review receipt の outer SHA が canonical body と不一致")
    return ReviewReceipt(body, _seal=_SEAL)


def _validated_review_body(value: ReviewReceipt, source_body: Mapping[str, object]) -> Mapping[str, object]:
    if type(value) is not ReviewReceipt:
        raise BuildAdmissionError("review_receipt は verify_review_receipt() 由来の exact value が必要")
    try:
        body = value.as_receipt()
    except (AttributeError, TypeError, ValueError) as exc:
        raise BuildAdmissionError("review receipt の sealed body が不正") from exc
    checked = _require_exact_keys(body, _REVIEW_KEYS, "review receipt")
    try:
        review_id = ReviewId(checked["review_id"])
    except (TypeError, ValueError) as exc:
        raise BuildAdmissionError("review receipt の review_id が未登録") from exc
    # Re-run the persistent validator instead of trusting the runtime seal alone.
    verified = verify_review_receipt(review_id, _source_from_body_proxy(source_body), receipt=checked)
    return verified.as_receipt()


def _source_from_body_proxy(source_body: Mapping[str, object]) -> SourceEvidence:
    """Rehydrate an already validated source body for internal receipt revalidation."""

    return SourceEvidence.from_receipt(source_body)


def derive_build_admission(
    context: BuildRunContext,
    source: SourceEvidence,
    *,
    generator_receipt: GeneratorReceipt | None = None,
    review_receipt: ReviewReceipt | None = None,
) -> BuildAdmission:
    """Derive one class in the ruled order; reject missing or ambiguous evidence."""

    if type(context) is not BuildRunContext:
        raise BuildAdmissionError("context は build_run_context() 由来の exact value が必要")
    source_body = _source_map(source)
    _require_materialized_trigger_axis_predicate(source)
    if generator_receipt is not None and review_receipt is not None:
        raise BuildAdmissionError("generator と review receipt の同時提示は曖昧なので拒否")

    generator_body = review_body = None
    generator_id = review_id = input_sha256 = authority_kind = None
    if source.src_token == STOCK and source.tracked_clean is True \
            and source.ccbench_commit == CURRENT_PIN:
        provenance = BuildProvenance.STOCK_BASELINE
    elif review_receipt is not None:
        review_body = _validated_review_body(review_receipt, source_body)
        review_id = review_body["review_id"]
        input_sha256 = review_body["input_sha256"]
        provenance = BuildProvenance.HUMAN_REVIEWED
    elif generator_receipt is not None:
        if type(generator_receipt) is not GeneratorReceipt:
            raise BuildAdmissionError(
                "generator_receipt は attest_generator_output() 由来の exact value が必要"
            )
        if generator_receipt._context_nonce != context._context_nonce:
            raise BuildAdmissionError("generator receipt は別 run context 由来")
        generator_body = _validate_generator_body(generator_receipt.as_receipt(), source_body)
        if generator_body["generator_id"] != context.generator_id.value:
            raise BuildAdmissionError("generator receipt の id が run context と不一致")
        generator_id = generator_body["generator_id"]
        input_sha256 = generator_body["generator_input_sha256"]
        provenance = BuildProvenance.MACHINE_GENERATED
    elif context._authority_nonce is not None:
        if context._authority_nonce not in _CLAIMED_AUTHORITY_NONCES:
            raise BuildAdmissionError("coder authority は同一 run context で有効でない")
        authority_kind = _AUTHORITY_KIND
        provenance = BuildProvenance.CODER_AUTHORED
    else:
        raise BuildAdmissionError("source evidence は stock/review/generator/coder のどれも支持しない")

    body: dict[str, object] = {
        "schema": ADMISSION_SCHEMA,
        "class": provenance.value,
        "policy_sha256": context.policy.sha256,
        "source": source_body,
        "generator_id": generator_id,
        "review_id": review_id,
        "input_sha256": input_sha256,
        "generator_receipt": generator_body,
        "review_receipt": review_body,
        "authority_kind": authority_kind,
    }
    body["receipt_sha256"] = _sha256_map(body)
    return BuildAdmission(provenance, body, _seal=_SEAL)


def _validate_admission_body(
    value: object,
    *,
    expected_policy: BuildAdmissionPolicy,
    expected_source: SourceEvidence | None,
) -> Mapping[str, object]:
    if type(expected_policy) is not BuildAdmissionPolicy:
        raise BuildAdmissionError("expected_policy は BuildRunContext.policy の exact value が必要")
    return _validate_admission_body_against_policy(
        value, policy_sha256=expected_policy.sha256, stock_pin=CURRENT_PIN,
        expected_source=expected_source,
    )


def _validate_admission_body_against_policy(
    value: object, *, policy_sha256: str, stock_pin: str,
    expected_source: SourceEvidence | None,
) -> Mapping[str, object]:
    body = _require_exact_keys(value, _ADMISSION_KEYS, "build admission receipt")
    if body["schema"] != ADMISSION_SCHEMA or body["policy_sha256"] != policy_sha256:
        raise BuildAdmissionError("build admission receipt の schema/policy が不一致")
    source_body = body["source"]
    try:
        source = SourceEvidence.from_receipt(source_body)
    except (TypeError, ValueError) as exc:
        raise BuildAdmissionError("build admission receipt の source evidence が不正") from exc
    if expected_source is not None and source_body != _source_map(expected_source):
        raise BuildAdmissionError("build admission receipt の source evidence/root が不一致")
    try:
        provenance = BuildProvenance(body["class"])
    except (TypeError, ValueError) as exc:
        raise BuildAdmissionError("build admission receipt の class が不正") from exc
    if not _is_sha256(body["receipt_sha256"]):
        raise BuildAdmissionError("build admission receipt の outer SHA が不正")
    unsigned = dict(body)
    outer = unsigned.pop("receipt_sha256")
    if _sha256_map(unsigned) != outer:
        raise BuildAdmissionError("build admission receipt の outer SHA が canonical body と不一致")

    if provenance is BuildProvenance.STOCK_BASELINE:
        if not (source.src_token == STOCK and source.tracked_clean is True
                and source.ccbench_commit == stock_pin):
            raise BuildAdmissionError("stock class を repo pin/clean/source evidence が支持しない")
        expected_null = ("generator_id", "review_id", "input_sha256",
                         "generator_receipt", "review_receipt", "authority_kind")
        if any(body[key] is not None for key in expected_null):
            raise BuildAdmissionError("stock class に他 class の evidence が混在")
    elif provenance is BuildProvenance.HUMAN_REVIEWED:
        checked = _require_exact_keys(body["review_receipt"], _REVIEW_KEYS, "review receipt")
        try:
            review_id = ReviewId(checked["review_id"])
        except (TypeError, ValueError) as exc:
            raise BuildAdmissionError("review receipt の review_id が未登録") from exc
        verify_review_receipt(review_id, source, receipt=checked)
        if (body["review_id"] != review_id.value or body["input_sha256"] != checked["input_sha256"]
                or body["generator_id"] is not None or body["generator_receipt"] is not None
                or body["authority_kind"] is not None):
            raise BuildAdmissionError("human-reviewed class の canonical body が不整合")
    elif provenance is BuildProvenance.MACHINE_GENERATED:
        checked = _validate_generator_body(body["generator_receipt"], source_body)
        if (body["generator_id"] != checked["generator_id"]
                or body["input_sha256"] != checked["generator_input_sha256"]
                or body["review_id"] is not None or body["review_receipt"] is not None
                or body["authority_kind"] is not None):
            raise BuildAdmissionError("machine-generated class の canonical body が不整合")
    else:
        if body["authority_kind"] != _AUTHORITY_KIND:
            raise BuildAdmissionError("coder-authored class は CLI authority kind が必要")
        expected_null = ("generator_id", "review_id", "input_sha256",
                         "generator_receipt", "review_receipt")
        if any(body[key] is not None for key in expected_null):
            raise BuildAdmissionError("coder-authored class に他 class の evidence が混在")
    return body


def require_build_admission(
    value: object,
    *,
    expected_policy: BuildAdmissionPolicy,
    expected_source: SourceEvidence,
) -> BuildAdmission:
    """Revalidate a sealed runtime admission against the current policy and source/root."""

    if type(value) is not BuildAdmission:
        raise BuildAdmissionError("admission は derive_build_admission() 由来の exact value が必要")
    _source_map(expected_source)
    _require_materialized_trigger_axis_predicate(expected_source)
    try:
        body = value.as_wal_receipt()
    except (AttributeError, TypeError, ValueError) as exc:
        raise BuildAdmissionError("BuildAdmission の sealed body が不正") from exc
    checked = _validate_admission_body(
        body, expected_policy=expected_policy, expected_source=expected_source
    )
    if value.provenance.value != checked["class"]:
        raise BuildAdmissionError("runtime provenance と canonical receipt class が不一致")
    return value


def validate_build_admission_receipt(
    value: object,
    *,
    expected_policy: BuildAdmissionPolicy,
    expected_source: SourceEvidence | None = None,
) -> Mapping[str, object]:
    """Validate a persistent exact-key receipt and return a detached canonical mapping."""

    checked = _validate_admission_body(
        value, expected_policy=expected_policy, expected_source=expected_source
    )
    return json.loads(_canonical_json(checked))


def validate_historical_build_admission_receipt(
    value: object, *, expected_policy: HistoricalBuildAdmissionPolicy,
    expected_source: SourceEvidence | None = None,
) -> Mapping[str, object]:
    """Check recorded policy/stock consistency, retaining current registries and authority."""
    if type(expected_policy) is not HistoricalBuildAdmissionPolicy:
        raise BuildAdmissionError("expected_policy requires exact HistoricalBuildAdmissionPolicy")
    checked = _validate_admission_body_against_policy(
        value, policy_sha256=expected_policy.sha256,
        stock_pin=expected_policy.as_preimage()["repo_stock_pin"],
        expected_source=expected_source,
    )
    return json.loads(_canonical_json(checked))
