# -*- coding: utf-8 -*-
"""v2 世代の承認束縛 machinery (F6a 裁定・load_ratified_freeze の record/連鎖/承認 層)。

本モジュールは floor protocol v2 の「承認済み世代」を **検証開始時に捕捉した単一
commit H に対する純関数** として機械判定する (C1-1/C1-10 の linearization point)。
責務は record の構造・履歴不変条件・approval/active pointer 連鎖・revocation/
cancellation tombstone の検証までであり、世代 document の**内容**検証 (source blob
照合・未知性 closure・transition table・frozen_at_head の中身) は次段 (W3) が
``_verify_generation_semantics`` を拡張して差し込む。拡張点は関数分離で残す。

s8b_freeze_io.py の docstring が「load_ratified_freeze は別モジュールの責務」と明記
しているため、strict 型 (RatifiedFreeze/LegacyFreeze) と連鎖検証はここに置く。
freeze_io の primitive (VerifiedFreeze/strict parse) とは責務が異なる。

fail-closed 原則: あらゆる構造・履歴・provenance の不整合は「active なし」に倒し
``RatifiedFreezeError`` を送出する (可用性 DoS は fail-closed 設計の許容内、C1-3)。
「最新 = 有効」「番号最大 = 有効」の判定は書かない — active は明示 pointer 連鎖の
一意な先端からのみ導く。

移行注記 (C2-5): v1 単一 filename freeze は ``LegacyFreeze`` として型分離し、bytes
定数 (V1_FREEZE_SHA256) でのみ束縛する。v1 の ``frozen_at_head`` (2e20d441…) は
2026-07-17 の trailer 廃止に伴う履歴書換えで dangling となり非 shallow repo にも
存在しないため、v1 の source/head 再検証はしない (bytes hash 束縛で代替、§5-viii)。
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import shlex
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple, Type

from ..calibrator import perf_preflight as _perf_preflight
from . import env_contract as _env_contract
from . import env_attestation as _env_attestation
from . import execution_guard as _execution_guard
from . import s8b_floor_contract as _floor_contract
from . import s8b_floor_stats as _floor_stats
from . import s8b_binary_admission as _binary_admission
from .build_admission import resolve_current_build_admission_policy
from . import s8b_holdout_freeze as _hf
from .s8b_holdout_freeze import TOP_LEVEL_KEYS as V1_TOP_LEVEL_KEYS
from .s8b_launch_cert import (
    LaunchCertError as _LaunchCertError,
    parse_official_run_path as _parse_official_run_path,
    validate_launch_certificate as _validate_launch_certificate,
)

# ---------------------------------------------------------------------------
# 定数 (実 repo には作らない相対 path 規約 + v1 trust root)
# ---------------------------------------------------------------------------

_ORCHESTRATOR = Path(__file__).resolve().parent.parent
ROOT = _ORCHESTRATOR.parent

# v1 trust root (C2-5、親が直接 sha256 照合済み)。v1 は LegacyFreeze で束縛する。
V1_FREEZE_PATH = "output/s8b-freeze/holdout_freeze.json"
V1_FREEZE_SHA256 = "315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688"

# namespace (path 正規形。実 repo にファイルを作るのは「発効」であり本 wave の禁止事項)。
FREEZE_DIR = "output/s8b-freeze"
APPROVAL_DIR = "output/s8b-freeze/approvals"
REVOCATION_DIR = "output/s8b-freeze/revocations"
ACTIVE_DIR = "output/s8b-freeze/active"
ACTIVE_CANCEL_DIR = "output/s8b-freeze/active-cancellations"

_SELECTOR_PREDICTIONS_PATH = "output/s8b-freeze/selector_predictions.json"
_SELECTOR_JOURNAL_PATH = "output/s8b-freeze/selector-runs/journal.jsonl"
_SELECTOR_RUNS_DIR = "output/s8b-freeze/selector-runs"
_SELECTOR_PROTOCOL_PATH = "output/s8b-freeze/floor_protocol.json"
_SELECTOR_PARSER_PATH = "orchestrator/campaign/s8b_selector_output.py"
_SELECTOR_SOURCE_PATHS = {
    "holdout_freeze": V1_FREEZE_PATH,
    "builder": "orchestrator/campaign/s8b_selector_input.py",
    "role": ".claude/agents/selector-8b.md",
    "input_schema": "orchestrator/campaign/s8b_selector_catalog.json",
    "output_schema": "orchestrator/campaign/s8b_selector_output_schema.json",
}

# path 正規形パーサ (連番飛び・不正 filename を構造的に拒否する)。
_GEN_RE = re.compile(r"^output/s8b-freeze/holdout_freeze\.v2\.g([1-9][0-9]*)\.json$")
_APPROVAL_RE = re.compile(r"^output/s8b-freeze/approvals/([0-9a-f]{64})\.json$")
_REVOCATION_RE = re.compile(r"^output/s8b-freeze/revocations/([0-9a-f]{64})\.json$")
_ACTIVE_RE = re.compile(r"^output/s8b-freeze/active/([0-9a-f]{64})\.json$")
_CANCEL_RE = re.compile(r"^output/s8b-freeze/active-cancellations/([0-9a-f]{64})\.json$")

_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")

_V2_SCHEMA_VERSION = "8b-holdout-freeze/v2"

# v2 世代 top-level exact 集合 (C1-8)。v1 の 18 key に v2 header の新規 6 key を加える。
# schema_version/frozen_at_head/refreeze_note は v1 に既存のため「加える」対象外。
# confirmed_at/confirmed_by は §9 に除去の明文がないため v1 のまま維持する
# (設計判断: 除去は親追認事項。除くと Legacy→v2 の連続性が切れるため既定は維持)。
_V2_ADDED_KEYS = frozenset({
    "generation_number", "supersedes_sha256", "env_tag",
    "floor_protocol", "floor_source", "measurement_closure",
})
V2_TOP_LEVEL_KEYS = frozenset(V1_TOP_LEVEL_KEYS) | _V2_ADDED_KEYS

# 世代に現れてはならない approval 系 field (C1-8。承認は外部 record へ分離した)。
# exact-set 検査でも落ちるが、明示拒否で reason code を明瞭化する。
_FORBIDDEN_GENERATION_KEYS = frozenset({
    "approved_by", "approved_at", "approval_scope", "change_reason",
    "approver", "scope",
})

# approval / pointer / tombstone の exact schema。
_APPROVAL_KEYS = frozenset({"generation_sha256", "approver", "approved_at", "scope"})
_POINTER_KEYS = frozenset({
    "generation_number", "path", "sha256", "parent_active_sha256", "approval_sha256",
})
# tombstone schema は F6 裁定に明文がないため最小 exact schema を定める
# (設計判断: 親追認事項。keyed hash + 監査 field、未知 key は fail-closed で拒否)。
_REVOCATION_KEYS = frozenset({"generation_sha256", "revoked_by", "revoked_at", "reason"})
_CANCEL_KEYS = frozenset({"pointer_sha256", "cancelled_by", "cancelled_at", "reason"})

# F5 transition table (C1-8: JSON Pointer 完全列挙)。値は「変わってよい / 新設されてよい」
# JSON Pointer の exact 集合。subtree (object/list) を許す pointer はその子孫も許す。
# 列挙外の pointer は前世代の値と厳密一致でなければならない (F5: それ以外の diff は拒否)。
#
# v1→g1: floor/budget/experiment 系 header + generator/design_source の sha256 (path は不変)。
_TRANSITION_V1_TO_G1 = frozenset({
    "/floor", "/budget", "/refreeze_note", "/schema_version",
    "/generator/sha256", "/design_source/sha256", "/frozen_at_head", "/env_tag",
    "/floor_protocol", "/floor_source", "/measurement_closure",
    "/generation_number", "/supersedes_sha256",
})
# gN→gN+1 (N>=1): floor・budget・floor_protocol・floor_source・measurement_closure・
# header (refreeze_note/generation_number/supersedes_sha256/frozen_at_head) のみ。
# env_tag の変更は拒否する (環境が変わる = 別実験。列挙外 → protected → 厳密一致要求)。
# この解釈 (F5 の「floor・budget・experiment_numbers 系 + header」の展開) は親追認事項。
_TRANSITION_GN_TO_GN1 = frozenset({
    "/floor", "/budget", "/floor_protocol", "/floor_source", "/measurement_closure",
    "/refreeze_note", "/generation_number", "/supersedes_sha256", "/frozen_at_head",
})


# §8.4 equality chain の accessor 単位 adjacency list。圧縮表記へ戻すと個別辺が
# 落ちるため、検証実装と edge mutation test の共通索引として省略なしに保持する。
EQUALITY_CHAIN_ADJACENCY: Tuple[Tuple[str, str], ...] = (
    ("P", "result.protocol_sha256"),
    ("result.protocol_sha256", "journal.campaign-start.protocol_sha256"),
    ("journal.campaign-start.protocol_sha256", "cert.protocol_sha256"),
    ("cert.protocol_sha256", "manifest.protocol_sha256"),
    ("P[:8]", "official-path.proto8"),
    ("V1_FREEZE_SHA256", "result.freeze_sha256"),
    ("result.freeze_sha256", "journal.campaign-start.freeze_sha256"),
    ("journal.campaign-start.freeze_sha256", "cert.v1_freeze_sha256"),
    ("cert.v1_freeze_sha256", "protocol.freeze.sha256"),
    ("protocol.freeze.sha256", "manifest.freeze_sha256"),
    ("manifest.freeze_sha256", "manifest.freeze.sha256"),
    ("V1_FREEZE_PATH", "protocol.freeze.path"),
    ("protocol.freeze.path", "manifest.freeze.path"),
    ("sha256(manifest.raw)", "result.manifest_sha256"),
    ("result.manifest_sha256", "journal.campaign-start.manifest_sha256"),
    ("sha256(cert.raw)", "journal.launch-start.launch_certificate_sha256"),
    ("journal.launch-start.launch_certificate_sha256",
     "journal.campaign-start.launch_certificate_sha256"),
    ("journal.campaign-start.launch_certificate_sha256",
     "result.wall_ledger[campaign-start].launch_certificate_sha256"),
    ("journal[event=session]", "result.sessions"),
    ("result.binaries", "manifest.binaries"),
    ("generation.env_tag", "official-path.env_tag"),
    ("official-path.env_tag", "protocol.env_tag"),
    ("protocol.env_tag", "result.env_tag"),
    ("result.env_tag", "manifest.env_tag"),
    ("manifest.env_tag", "journal.campaign-start.execution_receipt.env_tag"),
    ("protocol.contract_sha256",
     "journal.campaign-start.execution_receipt.contract_sha256"),
    ("official-path.run_id.ts", "cert.started_utc(second)"),
    ("cert.started_utc", "journal.launch-start.utc"),
    ("sha256(result.raw)", "generation.floor_source.sha256"),
)

_SORT_SWO_ORACLE_AXIS_SAFE_KEYS = frozenset({
    "schema", "cell_id", "holdout_id", "configuration_id", "entry_sha256",
    "binary_sha256", "classification", "reason_code", "oracle_contract_id",
    "materialized_hole_sha256", "proposal_sha256", "corpus_id",
    "corpus_version", "compiler_version_sha256", "compile_flags_sha256",
    "tu_sha256", "tu_template_sha256", "dependency_config_sha256",
    "dependency_manifest_sha256", "guarantee_boundary", "receipt_sha256",
})
_BINDING_KEYS = frozenset({
    "genome_canonical", "src_token", "variant_id", "entry_sha256", "binding_sha256",
})
_MANIFEST_KEYS = frozenset({
    "schema_version", "protocol_sha256", "freeze", "freeze_sha256", "env_tag",
    "ccbench_pin", "stock_configuration", "schedule_algorithm", "master_seed",
    "n_sessions", "reps", "extime_s", "session_cv_max", "cell_cv_max", "cells",
    "binaries", "schedule",
})
_MANIFEST_CELL_KEYS = frozenset({
    "cell_id", "holdout_id", "configuration_id", "records", "threads", "workload",
})
_SCHEDULE_KEYS = frozenset({"seq", "round", "cell_id"})
_RESULT_CONFIG_KEYS = frozenset({
    "formula", "n_sessions", "reps", "stock_configuration", "wired_min_rel_floor",
    "session_cv_max", "cell_cv_max",
})
_RESULT_CELL_KEYS = frozenset({
    "holdout_id", "configuration_id", "n_valid", "medians", "m", "s", "valid", "cv",
    "notes",
})
_RESULT_FLOOR_KEYS = frozenset({"pairs", "scalar_alt", "scale_ref", "diagnostics"})
_EXCLUDED_KEYS = frozenset({
    "seq", "cell_id", "kind", "retry", "round", "excluded_reason", "session_cv",
    "exclusion_class", "rep_integrity_failures",
})
_ATTEMPT_KEYS = frozenset({
    "seq", "cell_id", "kind", "round", "retry_ordinal", "valid", "excluded_reason",
    "exclusion_class", "rep_integrity_failures", "session_cv", "session_median",
    "duration_s",
})


@dataclass(frozen=True)
class _ValidatedManifest:
    """Ratified manifest の既存 3 値と receipt 由来 perf 条件を運ぶ。"""

    cells: list[dict]
    schedule: list[dict]
    binaries: Dict[str, dict]
    expected_use_perf: bool

    def __iter__(self):
        """既存の private test caller の 3 値 unpack を維持する。"""
        yield self.cells
        yield self.schedule
        yield self.binaries

_JOURNAL_BINDING_KEYS = frozenset({"pbs_jobid", "submission_nonce"})
_JOURNAL_KEYS = {
    "reservation-preflight": frozenset({
        "event", "required_s", "safety_margin_s", "formula",
        "build_cap_per_cell_s", "shared_dependency_prebuild",
        "dependency_configure_cap_s", "dependency_target_cap_s",
        "verify_cap_per_attempt_s", "finalize_reserve_s",
    }),
    "launch-start": frozenset({
        "event", "schema", "launch_certificate_sha256", "utc",
    }),
    "perf-preflight": frozenset({
        "event", "schema", "perf_preflight_receipt",
    }),
    "campaign-start": frozenset({
        "event", "schema", "protocol_sha256", "freeze_sha256", "manifest_sha256",
        "launch_certificate_sha256", "hostname", "boot_id", "job_id", "cpuset", "utc",
        "pid", "starttime", "execution_uuid", "execution_receipt",
    }),
    "resume-start": frozenset({
        "event", "hostname", "boot_id", "job_id", "cpuset", "utc", "pid", "starttime",
        "execution_uuid",
    }),
    "round-start": frozenset({"event", "round", "utc"}),
    "round-complete": frozenset({"event", "round", "utc"}),
    "session-start": frozenset({
        "event", "seq", "kind", "cell_id", "round", "retry_ordinal", "attempt_id",
        "trigger", "started_iso",
    }),
    "session": frozenset({
        "event", "kind", "seq", "round", "retry_ordinal", "attempt_id", "trigger",
        "cell_id", "holdout_id", "configuration_id", "records", "threads", "workload",
        "throughputs", "reps_expected", "exec_failures", "excluded_reason", "retry",
        "rep_observations", "rep_integrity_failures", "exclusion_class",
        "session_median", "valid", "session_cv", "duration_s", "run_cmd", "notes",
        "probe_before", "probe_after", "binary_sha256_at_measure",
    }),
    "terminal-completed": frozenset({"event", "status"}),
    "terminal-aborted": frozenset({"event", "status", "reason"}),
    "terminal-artifact-invalid": frozenset({"event", "status", "problems"}),
}
_PROBE_KEYS = frozenset({"rc", "stdout", "stderr", "competing"})
_RECEIPT_KEYS = frozenset({"schema", "env_tag", "contract_sha256", "attestation"})
_ATTESTATION_KEYS = frozenset({"hostname", "boot_id", "cpuset", "captured_utc"})

_RUN_BASENAMES = {
    "cert": "launch_certificate.json",
    "journal": "journal.jsonl",
    "manifest": "manifest.json",
    "result": "result.json",
}


# ---------------------------------------------------------------------------
# 例外 (単一型 + 構造化 reason code)
# ---------------------------------------------------------------------------

class RatifiedFreezeError(RuntimeError):
    """承認束縛検証の fail-closed 拒否。``reason`` に構造化 reason code を持つ。"""

    def __init__(self, reason: str, detail: str = "", *, cause: Optional[str] = None) -> None:
        self.reason = reason
        self.cause = cause
        super().__init__(f"[{reason}] {detail}" if detail else reason)


# ---------------------------------------------------------------------------
# H-pure git primitive (worktree 直読み禁止。全 query を捕捉済み H に固定)
# ---------------------------------------------------------------------------

# 全 git 呼出しに前置する hardening flag。core.useReplaceRefs=false は refs/replace/* を
# 無効化し、object 解決 (cat-file/rev-list/ls-tree/diff-tree) が過去 bytes を out-of-band に
# 差し替える攻撃を封じる (§5-viii)。ref 列挙自体は無効化されないため replace/grafts の存在は
# _capture_head で別途 fail-closed 拒否する。
_GIT_HARDEN: Tuple[str, ...] = ("-c", "core.useReplaceRefs=false")


def _git(args: Sequence[str], root: Path, *, stdin: Optional[bytes] = None) -> bytes:
    """git を bytes で叩く。失敗は RatifiedFreezeError に倒す (fail-closed)。"""
    try:
        completed = subprocess.run(
            ["git", *_GIT_HARDEN, *args], cwd=root, input=stdin,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", b"") or str(exc).encode("utf-8", "replace")
        text = detail.decode("utf-8", "replace") if isinstance(detail, bytes) else str(detail)
        raise RatifiedFreezeError("git-failed", f"git {' '.join(args)}: {text.strip()}") from exc
    return completed.stdout


def _git_text(args: Sequence[str], root: Path, *, stdin: Optional[bytes] = None) -> str:
    return _git(args, root, stdin=stdin).decode("utf-8", "strict").strip()


def _git_ok(args: Sequence[str], root: Path) -> bool:
    """exit 0 を True に。git 起動失敗 (OSError) だけは fail-closed で送出する。"""
    try:
        completed = subprocess.run(
            ["git", *_GIT_HARDEN, *args], cwd=root,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except OSError as exc:
        raise RatifiedFreezeError("git-failed", f"git {' '.join(args)}: {exc}") from exc
    return completed.returncode == 0


def _capture_head(root: Path) -> str:
    if _git_text(["rev-parse", "--is-shallow-repository"], root) == "true":
        raise RatifiedFreezeError("shallow-repo", "shallow repository は導入履歴を証明できない")
    # replace refs / grafts はローカル out-of-band 状態で object 解決・rev-list を書換え、
    # H-pure な履歴検証 (history-mutated / multiple-introduction) を静かに無効化し得る。
    # 呼出しは core.useReplaceRefs=false で replace を無効化済みだが、存在自体も拒否して
    # 改竄の試みを露出する (shallow を拒否しながら replace/grafts を素通しにしない)。
    if _git_text(["for-each-ref", "--format=%(refname)", "refs/replace/"], root):
        raise RatifiedFreezeError(
            "replace-refs", "refs/replace/* が存在する (replace object は履歴検証を無効化し得る)"
        )
    grafts_rel = _git_text(["rev-parse", "--git-path", "info/grafts"], root)
    if grafts_rel and (root / grafts_rel).exists():
        raise RatifiedFreezeError(
            "grafts", f"grafts が存在する ({grafts_rel} は rev-list を out-of-band に書換える)"
        )
    head = _git_text(["rev-parse", "HEAD"], root)
    if not _SHA1_RE.match(head):
        raise RatifiedFreezeError("bad-head", f"HEAD が 40 桁 SHA でない: {head!r}")
    return head


def _blob_bytes(head: str, path: str, root: Path) -> bytes:
    """H の tree の <path> の blob bytes を読む (worktree 直読みしない)。"""
    return _git([f"cat-file", "blob", f"{head}:{path}"], root)


def _assert_namespace_clean(root: Path) -> None:
    """namespace 配下の dirty (worktree ≠ H の index/HEAD) を拒否する (C1-10)。

    namespace 内の untracked/modified/deleted を全て捕捉する。namespace 外の dirty は
    対象外 (発効に無関係)。"""
    out = _git_text(
        ["status", "--porcelain", "--untracked-files=all", "--", FREEZE_DIR], root
    )
    if out:
        raise RatifiedFreezeError(
            "namespace-dirty", f"{FREEZE_DIR} 配下が dirty: {out.splitlines()[0]!r} 他"
        )


# ---------------------------------------------------------------------------
# strict parse / canonical / hash
# ---------------------------------------------------------------------------

def _sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _reject_constant(token: str):
    raise RatifiedFreezeError("json-nan", f"非数値定数を含む: {token}")


def _no_duplicate_keys(pairs):
    seen: Dict[str, object] = {}
    for key, value in pairs:
        if key in seen:
            raise RatifiedFreezeError("json-duplicate-key", f"duplicate key: {key!r}")
        seen[key] = value
    return seen


def _strict_load(raw: bytes, *, what: str) -> dict:
    """strict parse: utf-8 厳密・duplicate key 拒否・NaN/Infinity 拒否・top-level object。"""
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise RatifiedFreezeError("bad-utf8", f"{what} が UTF-8 でない") from exc
    try:
        value = json.loads(
            text, parse_constant=_reject_constant, object_pairs_hook=_no_duplicate_keys,
        )
    except json.JSONDecodeError as exc:
        raise RatifiedFreezeError("bad-json", f"{what} を strict parse できない: {exc}") from exc
    if not isinstance(value, dict):
        raise RatifiedFreezeError("not-object", f"{what} top-level が object でない")
    return value


def _canonical_bytes(value: Mapping) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def _load_canonical(raw: bytes, keys: frozenset, *, what: str) -> dict:
    """strict parse + exact keys + canonical 形 (raw が canonical bytes と byte 一致)。

    approval/pointer/tombstone record は「strict canonical JSON」を要求する。canonical
    form を byte-for-byte で強制することで、同一 filename に別 bytes を仕込む余地を消す。"""
    doc = _strict_load(raw, what=what)
    if frozenset(doc) != keys:
        raise RatifiedFreezeError(
            "schema-keys", f"{what} keys 不一致: {sorted(set(doc) ^ set(keys))}"
        )
    if _canonical_bytes(doc) != raw:
        raise RatifiedFreezeError("not-canonical", f"{what} が canonical JSON でない")
    return doc


# ---------------------------------------------------------------------------
# commit graph / 履歴不変条件 (C1-5) と provenance 判定 (C1-6)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _CommitGraph:
    commits: Tuple[str, ...]                       # rev-list H の全 commit
    parents: Mapping[str, Tuple[str, ...]]         # commit -> parents


def _commit_graph(head: str, root: Path) -> _CommitGraph:
    out = _git_text(["rev-list", "--parents", head], root)
    commits: List[str] = []
    parents: Dict[str, Tuple[str, ...]] = {}
    for line in out.splitlines():
        parts = line.split()
        if not parts:
            continue
        commits.append(parts[0])
        parents[parts[0]] = tuple(parts[1:])
    return _CommitGraph(tuple(commits), parents)


def _blob_oid_by_commit(graph: _CommitGraph, path: str, root: Path) -> Dict[str, Optional[str]]:
    """全 commit での <path> の blob OID を batch-check で一括判定する (per-commit 起動なし)。

    出力は入力順に 1:1 対応するため zip で commit へ帰属させる。tree など blob 以外に
    解決されたら fail-closed。"""
    if not graph.commits:
        return {}
    stdin = ("".join(f"{c}:{path}\n" for c in graph.commits)).encode("utf-8")
    out = _git(["cat-file", "--batch-check"], root, stdin=stdin).decode("utf-8", "strict")
    lines = out.splitlines()
    if len(lines) != len(graph.commits):
        raise RatifiedFreezeError("batch-check-mismatch", "batch-check 出力数が commit 数と不一致")
    result: Dict[str, Optional[str]] = {}
    for commit, line in zip(graph.commits, lines):
        tokens = line.split()
        if tokens and tokens[-1] == "missing":
            result[commit] = None
            continue
        if len(tokens) >= 2 and _SHA1_RE.match(tokens[0]) and tokens[1] == "blob":
            result[commit] = tokens[0]
            continue
        raise RatifiedFreezeError(
            "path-not-blob", f"{path} が commit {commit} で blob に解決しない: {line!r}"
        )
    return result


def _immutable_introductions(
    graph: _CommitGraph, path: str, expected_oid: str, root: Path,
) -> Tuple[str, ...]:
    """履歴不変条件を検査し、導入 commit 集合を返す (C1-5)。

    不変条件 = 「∀C ∈ rev-list(H): entry(C,path) ∈ {absent, expected_oid}」。異なる
    bytes が一度でも歴史に現れたら拒否 (削除→別 bytes 再作成の遮断)。導入 commit =
    「entry が present かつ全 parent で absent」全件 (削除→同一 bytes 再作成は不変条件を
    破らないため許容され、複数導入になり得る)。path history simplification に依存せず全
    DAG を自前で辿る。"""
    oids = _blob_oid_by_commit(graph, path, root)
    for commit, oid in oids.items():
        if oid is not None and oid != expected_oid:
            raise RatifiedFreezeError(
                "history-mutated",
                f"{path} が commit {commit} で別 bytes (oid={oid}) に変異している",
            )
    intro: List[str] = []
    for commit in graph.commits:
        if oids.get(commit) != expected_oid:
            continue
        if all(oids.get(parent) is None for parent in graph.parents.get(commit, ())):
            intro.append(commit)
    if not intro:
        raise RatifiedFreezeError("no-introduction", f"{path} の導入 commit が無い")
    return tuple(intro)


def _raw_ai_agent_lines(message: str) -> List[str]:
    """raw message から key が (大小文字・空白違い含み) AI-Agent の行を全件返す。"""
    lines: List[str] = []
    for line in message.split("\n"):
        head = line.split(":", 1)[0] if ":" in line else None
        if head is not None and head.strip().lower() == "ai-agent":
            lines.append(line)
    return lines


def _parsed_ai_agent_values(message: str, root: Path) -> List[str]:
    """interpret-trailers --parse の AI-Agent 値 (separator を : に pin)。"""
    out = _git_text(
        ["-c", "trailer.separators=:", "interpret-trailers", "--parse"],
        root, stdin=message.encode("utf-8"),
    )
    values: List[str] = []
    for line in out.splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip().lower() == "ai-agent":
            values.append(value.strip())
    return values


def _commit_message(commit: str, root: Path) -> str:
    return _git(["show", "-s", "--format=%B", commit], root).decode("utf-8", "strict")


def _is_none_commit(commit: str, root: Path) -> bool:
    """逐語 `AI-Agent: none` の trailer 判定 (raw 行 byte-for-byte + parse 値)。

    parse 上の AI-Agent 値が厳密に ["none"] であり、かつ raw message に行として
    byte-for-byte `AI-Agent: none` がちょうど 1 本存在し他に AI-Agent 系行が無い。
    世代導入 commit の none 拒否 (`_assert_candidate_commit`) が使う。
    approval / pointer 等の導入 commit の trailer 検査は
    `_user_commit_trailer_problem` が担う。人間 commit の証明ではない。
    """
    message = _commit_message(commit, root)
    raw_lines = _raw_ai_agent_lines(message)
    if len(raw_lines) != 1 or raw_lines[0] != "AI-Agent: none":
        return False
    return _parsed_ai_agent_values(message, root) == ["none"]


# 文法の正本: tools/check_ai_provenance.py (AGENT_VALUE / RESERVED_PRODUCTS)。
# コピー fixture は tools を含まないため複製し、test で pattern・flags・意味条件を照合する。
_PROVENANCE_IDENT = r"[a-z0-9][a-z0-9._-]*"
_PROVENANCE_ROLES = ("author", "reviewer", "researcher", "manager", "integrator")
_PROVENANCE_RESERVED_PRODUCTS = frozenset({"none", "unknown", "not-exposed", "human"})
_PROVENANCE_AGENT_VALUE = re.compile(
    rf"^product=(?P<product>{_PROVENANCE_IDENT}); "
    rf"model=(?P<model>{_PROVENANCE_IDENT}); "
    rf"reasoning=(?P<reasoning>{_PROVENANCE_IDENT}); "
    rf"role=(?P<role>{'|'.join(_PROVENANCE_ROLES)})"
    rf"(?:; scope=(?P<scope>{_PROVENANCE_IDENT}))?$"
)


def _user_commit_trailer_problem(commit: str, root: Path) -> Optional[str]:
    """受理なら None、拒否なら診断文字列を返す。"""
    message = _commit_message(commit, root)
    raw_lines = _raw_ai_agent_lines(message)
    if len(raw_lines) != 1:
        return f"AI-Agent raw 行数が 1 でない: {len(raw_lines)}"
    values = _parsed_ai_agent_values(message, root)
    if len(values) != 1:
        return f"AI-Agent trailer 値数が 1 でない: {len(values)}"
    if raw_lines[0] != "AI-Agent: " + values[0]:
        return "AI-Agent 行が canonical 表記でない"
    if values[0] == "none":
        return None
    match = _PROVENANCE_AGENT_VALUE.fullmatch(values[0])
    if not match:
        return "AI-Agent 構造化値が provenance 文法に適合しない"
    if match.group("product") in _PROVENANCE_RESERVED_PRODUCTS:
        return f"AI-Agent product が予約語: {match.group('product')}"
    if match.group("model") == "none" or match.group("reasoning") == "none":
        return "AI-Agent model/reasoning に none は使えない"
    return None


def _assert_user_commit(commit: str, graph: _CommitGraph, root: Path) -> None:
    """approval/pointer/revocation/cancellation の導入 commit 検証 (C1-6)。

    非 merge、AI-Agent trailer ちょうど 1 行、逐語 none または規約適合の構造化値、
    H ancestry。満たさない record の存在は
    「無視」でなく検証エラー (fail-closed)。"""
    if len(graph.parents.get(commit, ())) > 1:
        raise RatifiedFreezeError("user-commit-merge", f"user commit {commit} が merge")
    problem = _user_commit_trailer_problem(commit, root)
    if problem is not None:
        raise RatifiedFreezeError(
            "user-commit-trailer", f"commit {commit}: {problem}"
        )
    if not _git_ok(["merge-base", "--is-ancestor", commit, graph.commits[0]], root):
        raise RatifiedFreezeError("user-commit-ancestry", f"commit {commit} が H ancestor でない")


def _assert_candidate_commit(commit: str, graph: _CommitGraph, root: Path) -> None:
    """世代導入 commit G の検証 (C1-4/C2-6 の本レーン分)。

    非 merge、かつ `none` trailer なら拒否 (AI 生成世代を人間 commit に混ぜる provenance
    虚偽の検出)、かつ AI-Agent trailer を持つ (candidate は AI trailer 付き)。G^ ==
    frozen_at_head の検査は frozen_at_head 内容検証と一体で W3。"""
    if len(graph.parents.get(commit, ())) > 1:
        raise RatifiedFreezeError("generation-commit-merge", f"世代導入 commit {commit} が merge")
    if _is_none_commit(commit, root):
        raise RatifiedFreezeError(
            "generation-commit-none",
            f"世代導入 commit {commit} が `AI-Agent: none` — AI 生成物の provenance 虚偽",
        )
    message = _commit_message(commit, root)
    values = _parsed_ai_agent_values(message, root)
    if not values or values == ["none"]:
        raise RatifiedFreezeError(
            "generation-commit-provenance",
            f"世代導入 commit {commit} に非 none の AI-Agent trailer が無い",
        )


def _unique_introduction(intro: Tuple[str, ...], path: str) -> str:
    """発効トポロジー検証では導入 commit を一意に要求する (fail-closed)。

    削除→再作成で複数導入になった governance record は topology 検査の対象として拒否する
    (履歴不変条件そのものは _immutable_introductions が別途担保する)。"""
    if len(intro) != 1:
        raise RatifiedFreezeError(
            "multiple-introduction", f"{path} の導入 commit が一意でない: {intro}"
        )
    return intro[0]


def _assert_artifact_introduction_interval(
        graph: _CommitGraph, path: str, oid: str, *,
        cert_commit: str, gen_commit: str, root: Path,
) -> None:
    """捕捉済み graph と full OID のみで、一意・非 merge 導入を [C, G] に束縛する。"""
    intro = _unique_introduction(_immutable_introductions(graph, path, oid, root), path)
    if len(graph.parents.get(intro, ())) > 1:
        raise RatifiedFreezeError(
            "binding-chain-mismatch", f"{path} の導入 {intro} が merge",
            cause="artifact-introduction-merge",
        )
    if not _git_ok(["merge-base", "--is-ancestor", cert_commit, intro], root):
        raise RatifiedFreezeError(
            "binding-chain-mismatch", f"{path}: cert C が導入 i の祖先でない",
            cause="artifact-introduction-before-cert",
        )
    # 段階 3 の G-tree 実在検査と一意導入から従う重複検査。独立保証に数えない。
    if not _git_ok(["merge-base", "--is-ancestor", intro, gen_commit], root):
        raise RatifiedFreezeError(
            "binding-chain-mismatch", f"{path}: 導入 i が G の祖先でない",
            cause="artifact-introduction-outside-generation",
        )


def _added_paths(commit: str, root: Path) -> Tuple[frozenset, Tuple[Tuple[str, str], ...]]:
    """非 merge commit の diff-tree name-status から (追加 path 集合, 非追加 (status,path))。"""
    out = _git_text(
        ["diff-tree", "--no-commit-id", "--no-renames", "--name-status", "-r", commit],
        root,
    )
    added: set = set()
    other: List[Tuple[str, str]] = []
    for line in out.splitlines():
        status, _, path = line.partition("\t")
        if status == "A":
            added.add(path)
        else:
            other.append((status, path))
    return frozenset(added), tuple(other)


def _parents_of(commit: str, root: Path) -> Tuple[str, ...]:
    """commit の親 OID 列を返す (rev-list --parents -n 1、H-pure)。"""
    out = _git_text(["rev-list", "--parents", "-n", "1", commit], root)
    parts = out.split()
    if not parts or not _SHA1_RE.match(parts[0]):
        raise RatifiedFreezeError("bad-commit", f"commit を解決できない: {commit!r}")
    return tuple(parts[1:])


def _blob_oid_at(commit: str, path: str, root: Path) -> Optional[str]:
    """commit の tree の <path> の blob OID を返す (missing→None、blob 以外→fail-closed)。"""
    stdin = f"{commit}:{path}\n".encode("utf-8")
    out = _git(["cat-file", "--batch-check"], root, stdin=stdin).decode("utf-8", "strict")
    tokens = out.split()
    if tokens and tokens[-1] == "missing":
        return None
    if len(tokens) >= 2 and _SHA1_RE.match(tokens[0]) and tokens[1] == "blob":
        return tokens[0]
    raise RatifiedFreezeError(
        "path-not-blob", f"{path} が {commit} で blob に解決しない: {out.strip()!r}"
    )


# ---------------------------------------------------------------------------
# F5 transition table (JSON Pointer 完全列挙、C1-8)
# ---------------------------------------------------------------------------

def _leaf_pointers(value, prefix: str = "") -> Dict[str, object]:
    """JSON 値の全 leaf pointer→値の辞書を返す (RFC6901 の ~ / エスケープ込み)。

    dict/list は再帰し、scalar (str/num/bool/None) を leaf とする。空 dict/空 list も
    leaf として扱い、追加/削除を pointer 集合差として露出する。"""
    if isinstance(value, Mapping):
        if not value:
            return {prefix or "": value}
        out: Dict[str, object] = {}
        for key, child in value.items():
            token = str(key).replace("~", "~0").replace("/", "~1")
            out.update(_leaf_pointers(child, f"{prefix}/{token}"))
        return out
    if isinstance(value, (list, tuple)):
        if not value:
            return {prefix or "": list(value)}
        out = {}
        for index, child in enumerate(value):
            out.update(_leaf_pointers(child, f"{prefix}/{index}"))
        return out
    return {prefix or "": value}


def _pointer_allowed(pointer: str, allowed: frozenset) -> bool:
    """pointer が allowed 集合の要素そのものか、その subtree (prefix + '/') 配下か。"""
    for entry in allowed:
        if pointer == entry or pointer.startswith(entry + "/"):
            return True
    return False


def _assert_transition(prev: Mapping, nxt: Mapping, allowed: frozenset, *, label: str) -> None:
    """prev→nxt の diff が allowed pointer 集合の内側だけであることを要求する (F5)。

    allowed 外の pointer で値が変わった / 追加された / 削除された場合はすべて拒否する
    (列挙外の diff は 1 つでも fail-closed)。"""
    prev_leaves = _leaf_pointers(prev)
    next_leaves = _leaf_pointers(nxt)
    sentinel = object()
    for pointer in set(prev_leaves) | set(next_leaves):
        if _pointer_allowed(pointer, allowed):
            continue
        pv = prev_leaves.get(pointer, sentinel)
        nv = next_leaves.get(pointer, sentinel)
        if pv is sentinel or nv is sentinel or pv != nv:
            raise RatifiedFreezeError(
                "transition-violation",
                f"{label}: 列挙外の pointer {pointer} が変化/新設/削除された "
                f"(prev={pv!r} next={nv!r})",
            )


# ---------------------------------------------------------------------------
# 中間検証結果 (record レベル)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _Generation:
    number: int
    path: str
    raw: bytes
    sha256: str
    doc: dict
    commit: str            # 導入 commit G


@dataclass(frozen=True)
class _Approval:
    generation_sha256: str
    path: str
    raw: bytes
    sha256: str            # approval record 自身の bytes hash (pointer.approval_sha256 が参照)
    doc: dict
    intro: str


@dataclass(frozen=True)
class _Pointer:
    number: int
    path: str
    raw: bytes
    sha256: str            # pointer record 自身の bytes hash (= filename)
    doc: dict
    intro: str


# ---------------------------------------------------------------------------
# 公開型 (C1-7)
# ---------------------------------------------------------------------------

def _deep_freeze(value):
    """dict→MappingProxyType、list→tuple の再帰 immutable 化 (深い不変性)。"""
    if isinstance(value, dict):
        return MappingProxyType({k: _deep_freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_deep_freeze(v) for v in value)
    return value


@dataclass(frozen=True)
class RatifiedFreeze:
    """公開 API から昇格不能な承認済み実走型 (C1-7)。

    保証は「公開 API (load_ratified_freeze) 経由でしか構築されない」に限定する
    (任意 Python コードに対する偽造不能ではない)。constructor の直接使用は本 loader
    内に閉じ、production module が RatifiedFreeze( を直接書かないことを静的テストで縛る。
    document は再帰 immutable 化した形で保持し raw mutable dict を公開しない。"""
    document: Mapping
    sha256: str
    generation_number: int
    activation_head: str
    generation_commit: str

    @property
    def holdouts(self) -> Mapping[str, Mapping[str, object]]:
        """Return the ratified holdout entries as an immutable projection.

        ``_verify_snapshot_layer1`` already validates the generation document's
        snapshot fields.  This projection additionally binds each entry's
        candidate identity to the static holdout authority before exposing it
        to consumers, so a candidate swap cannot pass as a set-only match.
        """
        document = self.document
        holdouts = document.get("holdouts")
        if not isinstance(holdouts, Mapping) or set(holdouts) != set(_hf.HOLDOUTS):
            raise RatifiedFreezeError(
                "holdouts-schema", "holdouts の集合が静的な holdout authority と不一致"
            )
        for name, frozen in _hf.HOLDOUTS.items():
            entry = holdouts.get(name)
            if not isinstance(entry, Mapping):
                raise RatifiedFreezeError(
                    "holdout-entry", f"holdouts.{name} が object でない"
                )
            if entry.get("candidate_id") != frozen["candidate_id"]:
                raise RatifiedFreezeError(
                    "holdout-entry",
                    f"holdouts.{name}.candidate_id が静的な candidate_id と不一致",
                )
        return _deep_freeze(
            {name: dict(entry) for name, entry in holdouts.items()}
        )


@dataclass(frozen=True)
class LegacyFreeze:
    """v1 単一 filename freeze の型 (C2-5)。bytes 定数照合 + strict parse のみ。

    v1 の source/head 再検証はしない — frozen_at_head は履歴書換えで dangling
    (§5-viii)。RatifiedFreeze とは別型で、consumer が誤って v2 実走経路へ流せない。"""
    document: Mapping
    sha256: str


@dataclass(frozen=True)
class VerifiedFloorArtifact:
    """同一 G blob から一度だけ構築する floor artifact の atomic invariant。

    ``raw_bytes`` を捕捉して直ちに sha256 を照合し、``document`` はその同じ bytes の
    strict parse 結果を deep-freeze する。worktree や別 read の document と混成しない。
    """
    path: str
    raw_bytes: bytes
    sha256: str
    document: Mapping


@dataclass(frozen=True)
class LaunchValidatedFreeze:
    """実走前検証 (full scan 済み) を通した freeze (C2-10 の型分離)。

    ``load_ratified_freeze`` が返す静的 ``RatifiedFreeze`` (source/transition/snapshot 層1
    まで) を、``launch_validate`` が未知性層2 (現時点 search 再実行 + closure 完全一致 +
    列挙前後 digest + 陽性対照) を通してこの型へ昇格する。実走 consumer (oracle driver)
    はこの型を要求する — skip flag は作らない。unknownness 層2 は launch_validate 側。"""
    ratified: "RatifiedFreeze"
    activation_head: str
    search_digest: str
    validation_root: Path
    search_report: Mapping
    symlink_gitlink_inventory: Tuple[str, ...]
    floor_artifact: VerifiedFloorArtifact
    binaries_by_cell: Mapping


@dataclass(frozen=True)
class ReverifiedFreeze:
    """publish 済み freeze の read-only 再検証を通した型。

    この型分離は偽造耐性を主張しない。効くのは自分たちの consumer が黙って
    広がらないことだけである。実走 consumer は ``LaunchValidatedFreeze`` を要求し、
    historical contract で再検証した値を admission token として受理しない。
    """
    ratified: "RatifiedFreeze"
    activation_head: str
    search_digest: str
    validation_root: Path
    search_report: Mapping
    symlink_gitlink_inventory: Tuple[str, ...]
    floor_artifact: VerifiedFloorArtifact
    binaries_by_cell: Mapping


@dataclass(frozen=True)
class ActiveResolution:
    """resolve_active_generation の中間結果 (H・世代 bytes・G・approval/pointer 検証済み)。"""
    activation_head: str
    generation_number: int
    generation_path: str
    generation_bytes: bytes
    generation_sha256: str
    generation_commit: str
    approval_sha256: str
    approval_document: Mapping
    pointer_sha256: str
    pointer_document: Mapping


# ---------------------------------------------------------------------------
# namespace 列挙 (H の tree から。worktree directory は見ない)
# ---------------------------------------------------------------------------

def _list_namespace(head: str, root: Path) -> List[Tuple[str, str, str]]:
    """H の tree の namespace 配下を (mode, oid, path) で返す。blob 以外は fail-closed。"""
    out = _git(["ls-tree", "-r", "-z", head, "--", FREEZE_DIR], root)
    entries: List[Tuple[str, str, str]] = []
    for chunk in out.split(b"\0"):
        if not chunk:
            continue
        try:
            meta, sep, path = chunk.decode("utf-8", "strict").partition("\t")
        except UnicodeError as exc:
            raise RatifiedFreezeError("bad-path-utf8", "namespace path が UTF-8 でない") from exc
        if not sep:
            raise RatifiedFreezeError("bad-ls-tree", f"ls-tree 出力を解釈できない: {chunk!r}")
        mode, _, rest = meta.partition(" ")
        typ, _, oid = rest.partition(" ")
        if typ != "blob":
            raise RatifiedFreezeError(
                "non-blob-entry", f"namespace 内に blob 以外 (type={typ}): {path}"
            )
        if mode not in ("100644", "100755"):
            raise RatifiedFreezeError(
                "non-regular-entry", f"namespace 内に非通常ファイル (mode={mode}): {path}"
            )
        entries.append((mode, oid, path))
    return entries


# ---------------------------------------------------------------------------
# 世代 schema (structural)。内容検証は W3 の seam。
# ---------------------------------------------------------------------------

def _parse_generation_document(raw: bytes, number: int) -> dict:
    """v2 世代 document を strict parse + exact schema + 番号一致まで検査する (structural)。

    floor_protocol/floor_source/measurement_closure/frozen_at_head の**中身**検証は
    _verify_generation_semantics (W3 拡張点) の責務。"""
    doc = _strict_load(raw, what="世代 document")
    forbidden = _FORBIDDEN_GENERATION_KEYS & set(doc)
    if forbidden:
        raise RatifiedFreezeError(
            "generation-approval-field",
            f"世代に approval 系 field: {sorted(forbidden)} (承認は外部 record へ分離)",
        )
    if frozenset(doc) != V2_TOP_LEVEL_KEYS:
        raise RatifiedFreezeError(
            "generation-schema-keys",
            f"世代 top-level keys 不一致: {sorted(set(doc) ^ set(V2_TOP_LEVEL_KEYS))}",
        )
    if doc.get("schema_version") != _V2_SCHEMA_VERSION:
        raise RatifiedFreezeError(
            "generation-schema-version", f"schema_version 不一致: {doc.get('schema_version')!r}"
        )
    if doc.get("generation_number") != number:
        raise RatifiedFreezeError(
            "generation-number-body",
            f"generation_number 本文 {doc.get('generation_number')!r} が path N={number} と不一致",
        )
    return doc


def _source_record_path_sha(document: Mapping, field: str) -> Tuple[str, str]:
    """{path, sha256} record を厳密に取り出す (schema 逸脱は fail-closed)。"""
    rec = document.get(field)
    if not isinstance(rec, Mapping) or set(rec) != {"path", "sha256"}:
        raise RatifiedFreezeError("source-record-schema", f"{field} が {{path, sha256}} でない")
    path, sha = rec["path"], rec["sha256"]
    if not isinstance(path, str) or not path or not isinstance(sha, str) or not _SHA_RE.match(sha):
        raise RatifiedFreezeError("source-record-schema", f"{field}.path/sha256 が不正")
    return path, sha


def _assert_canonical_relative_path(path: object, *, reason: str, label: str) -> str:
    """root-relative raw POSIX path を正規化せず exact 文法で検査する。"""
    if not isinstance(path, str) or not path:
        raise RatifiedFreezeError(reason, f"{label} が空でない文字列でない")
    components = path.split("/")
    if (path.startswith("/") or path.endswith("/") or "//" in path or "\\" in path
            or "." in components or ".." in components
            or any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in path)):
        raise RatifiedFreezeError(reason, f"{label} の raw POSIX path が非正規: {path!r}")
    return path


def _closure_entries(document: Mapping) -> List[Tuple[str, str, str]]:
    """floor_protocol/floor_source/measurement_closure を (kind, path, sha256) 列に正規化する。

    floor_protocol/floor_source = 単一 {path, sha256}。measurement_closure = [{canonical_path,
    sha256}]。いずれも G tree の blob として実在・bytes sha256 一致・dirty 拒否・履歴不変を課す。"""
    entries: List[Tuple[str, str, str]] = []
    for field in ("floor_protocol", "floor_source"):
        path, sha = _source_record_path_sha(document, field)
        entries.append((field, path, sha))
    closure = document.get("measurement_closure")
    if not isinstance(closure, (list, tuple)):
        raise RatifiedFreezeError("closure-schema", "measurement_closure が list でない")
    seen: set = set()
    for index, item in enumerate(closure):
        if not isinstance(item, Mapping) or set(item) != {"canonical_path", "sha256"}:
            raise RatifiedFreezeError(
                "closure-schema", f"measurement_closure[{index}] が {{canonical_path, sha256}} でない"
            )
        path, sha = item["canonical_path"], item["sha256"]
        if not isinstance(path, str) or not path or not isinstance(sha, str) or not _SHA_RE.match(sha):
            raise RatifiedFreezeError("closure-schema", f"measurement_closure[{index}] の値が不正")
        # canonical: root-relative・raw POSIX 正規形・一意 (重複 path は fail-closed)。
        _assert_canonical_relative_path(
            path, reason="closure-path", label=f"measurement_closure[{index}].canonical_path",
        )
        if path in seen:
            raise RatifiedFreezeError("closure-duplicate", f"measurement_closure に重複 path: {path}")
        seen.add(path)
        entries.append(("measurement_closure", path, sha))
    return entries


def _verify_generation_semantics(document: Mapping, resolution: "ActiveResolution", root: Path) -> None:
    """世代 document の**内容**検証 (V1 source blob + V2 transition + V3 層1、静的)。

    ここは実走 scan を行わない静的層 (H-pure)。full scan を伴う未知性層2 は launch_validate。
    - V1: 世代導入 commit G は非 merge で G^ == frozen_at_head。design_source/generator/
      known_axes_freeze は frozen_at_head の blob bytes と sha256 一致 (worktree でなく blob)。
      floor_protocol/floor_source/measurement_closure は G tree に blob 実在 + sha256 一致 +
      worktree==H blob (dirty 拒否) + 履歴不変条件。env_tag は env_contract registry に実在。
      floor_protocol は strict parse 可能 (dup key/NaN 拒否で読める) まで (数値検証は Lane J)。
    - V2: v1→g1→…→gN の transition を F5 JSON Pointer 完全列挙で検査。
    - V3 層1: 各 holdout の zero_hit_output_sha256 を記録フィールドから再計算し一致 +
      conjunction_hits が空。

    fail-closed: いかなる不整合も RatifiedFreezeError。承認連鎖・active (structural) は
    resolve_active_generation で既に検証済みで、ここは内容ゲートを重ねる。"""
    head = resolution.activation_head
    gen_commit = resolution.generation_commit

    # --- V1a: G^ == frozen_at_head (非 merge、G は H ancestry 上の実在 commit) ---
    frozen = document.get("frozen_at_head")
    if not isinstance(frozen, str) or not _SHA1_RE.match(frozen):
        raise RatifiedFreezeError("frozen-at-head-format", "frozen_at_head が 40 桁 SHA でない")
    parents = _parents_of(gen_commit, root)
    if len(parents) != 1:
        raise RatifiedFreezeError(
            "generation-parent-count", f"世代導入 commit G の親が 1 個でない: {len(parents)}"
        )
    if parents[0] != frozen:
        raise RatifiedFreezeError(
            "frozen-at-head-mismatch",
            f"G^ ({parents[0]}) != frozen_at_head ({frozen})",
        )

    # --- V1b: source blob 照合 (frozen_at_head の blob bytes、worktree でなく blob) ---
    for field in ("design_source", "generator", "known_axes_freeze"):
        path, sha = _source_record_path_sha(document, field)
        blob = _blob_at_or_fail(frozen, path, root, reason="source-blob-missing")
        if _sha256_hex(blob) != sha:
            raise RatifiedFreezeError(
                "source-blob-mismatch",
                f"{field}: frozen_at_head:{path} の blob sha256 が記録と不一致",
            )

    # --- V1c: env_tag registry lookup ---
    env_tag = document.get("env_tag")
    try:
        _env_contract.lookup(env_tag)
    except _env_contract.EnvContractError as exc:
        raise RatifiedFreezeError("env-tag-unknown", f"env_tag が registry に無い: {exc}") from exc

    # --- V1d: closure artifact (G tree 実在 + sha256 + dirty + 履歴不変) ---
    graph = _commit_graph(head, root)
    for kind, path, sha in _closure_entries(document):
        g_blob = _blob_at_or_fail(gen_commit, path, root, reason="closure-not-in-generation")
        if _sha256_hex(g_blob) != sha:
            raise RatifiedFreezeError(
                "closure-sha-mismatch", f"{kind}:{path} の G blob sha256 が記録と不一致"
            )
        h_oid = _blob_oid_at(head, path, root)
        if h_oid is None:
            raise RatifiedFreezeError("closure-not-at-head", f"{kind}:{path} が H tree に無い")
        h_blob = _blob_bytes(head, path, root)
        try:
            wt_blob = (root / path).read_bytes()
        except OSError as exc:
            raise RatifiedFreezeError("closure-dirty", f"{kind}:{path} を worktree で読めない") from exc
        if wt_blob != h_blob:
            raise RatifiedFreezeError("closure-dirty", f"{kind}:{path} の worktree bytes が H blob と不一致")
        _immutable_introductions(graph, path, h_oid, root)
        # floor_protocol は strict parse 可能性まで (数値検証は Lane J の protocol builder)。
        if kind == "floor_protocol":
            _strict_load(g_blob, what="floor_protocol")

    # g1 の凍結 floor は、記録された floor_source blob の diagnostics 除外投影に限る。
    # current policy や worktree namespace は参照せず、loader を H-pure に保つ。
    if resolution.generation_number == 1:
        floor_source_path, _floor_source_sha = _source_record_path_sha(
            document, "floor_source",
        )
        floor_source_blob = _blob_at_or_fail(
            gen_commit, floor_source_path, root, reason="closure-not-in-generation",
        )
        try:
            floor_source_document = _strict_load(
                floor_source_blob, what="floor_source",
            )
            projected_floor = _hf._project_floor_for_freeze(  # noqa: SLF001
                floor_source_document,
            )
            projection_matches = (
                _canonical_bytes(projected_floor)
                == _canonical_bytes(document.get("floor"))
            )
        except (RatifiedFreezeError, _hf.FreezeError, TypeError, ValueError) as exc:
            raise RatifiedFreezeError(
                "floor-source-projection-mismatch",
                f"floor_source の凍結投影を検証できない: {exc}",
                cause="floor-source-projection",
            ) from exc
        if not projection_matches:
            raise RatifiedFreezeError(
                "floor-source-projection-mismatch",
                "generation.floor が floor_source.result.floors の投影と不一致",
                cause="floor-source-projection",
            )

    # --- V2: transition table (v1→g1→…→gN、F5 JSON Pointer 完全列挙) ---
    _verify_chain_transitions(document, resolution, head, root)

    # --- V3 層1: snapshot 整合 (記録フィールドから zero_hit_output_sha256 を再計算) ---
    _verify_snapshot_layer1(document)


def _blob_at_or_fail(commit: str, path: str, root: Path, *, reason: str) -> bytes:
    """commit:path の blob bytes を読む。missing/非 blob は指定 reason で fail-closed。"""
    if _blob_oid_at(commit, path, root) is None:
        raise RatifiedFreezeError(reason, f"{commit}:{path} が blob として存在しない")
    return _blob_bytes(commit, path, root)


def _verify_chain_transitions(
    tip_document: Mapping, resolution: "ActiveResolution", head: str, root: Path,
) -> None:
    """v1→g1→…→gN の全 transition を F5 で検査する (C1-8)。

    各世代 document を H tree の blob から strict parse し、直前世代 (g1 は v1 LegacyFreeze
    document) との diff が allowed pointer 集合の内側だけであることを要求する。"""
    n = resolution.generation_number
    # v1 document (H tree の blob。bytes sha は supersedes 連鎖で既に束縛済み)。
    v1_raw = _blob_at_or_fail(head, V1_FREEZE_PATH, root, reason="v1-missing-at-head")
    if _sha256_hex(v1_raw) != V1_FREEZE_SHA256:
        raise RatifiedFreezeError("v1-anchor-mismatch", "H tree の v1 freeze bytes が定数と不一致")
    prev_doc = _strict_load(v1_raw, what="v1 legacy freeze")
    allowed = _TRANSITION_V1_TO_G1
    for k in range(1, n + 1):
        gen_path = _gen_path(k)
        gen_raw = _blob_at_or_fail(head, gen_path, root, reason="chain-generation-missing")
        gen_doc = _parse_generation_document(gen_raw, k)
        _assert_transition(prev_doc, gen_doc, allowed, label=f"g{k-1 if k>1 else 'v1'}→g{k}")
        prev_doc = gen_doc
        allowed = _TRANSITION_GN_TO_GN1


def _gen_path(number: int) -> str:
    return f"{FREEZE_DIR}/holdout_freeze.v2.g{number}.json"


def _verify_snapshot_layer1(document: Mapping) -> None:
    """未知性層1: 各 holdout の zero_hit_output_sha256 を記録フィールドから再計算し一致 (C2-8)。"""
    holdouts = document.get("holdouts")
    if not isinstance(holdouts, Mapping) or set(holdouts) != set(_hf.HOLDOUTS):
        raise RatifiedFreezeError("holdouts-schema", "holdouts の集合が v1 の holdout と不一致")
    for name, frozen in _hf.HOLDOUTS.items():
        entry = holdouts.get(name)
        if not isinstance(entry, Mapping):
            raise RatifiedFreezeError("holdout-entry", f"holdouts.{name} が object でない")
        unknownness = entry.get("unknownness_check")
        if not isinstance(unknownness, Mapping):
            raise RatifiedFreezeError("unknownness-missing", f"holdouts.{name}.unknownness_check が無い")
        recorded_hits = unknownness.get("conjunction_hits")
        if recorded_hits != []:
            raise RatifiedFreezeError(
                "layer1-nonempty-hits", f"holdouts.{name}.conjunction_hits が空でない"
            )
        expressions = unknownness.get("expressions")
        per_axis = unknownness.get("per_axis_counts")
        if not isinstance(expressions, Mapping) or not isinstance(per_axis, Mapping):
            raise RatifiedFreezeError("unknownness-schema", f"holdouts.{name} の未知性フィールド不正")
        expected = _hf.recompute_snapshot_zero_hit_sha256(
            frozen["candidate_id"], expressions, per_axis,
        )
        if unknownness.get("zero_hit_output_sha256") != expected:
            raise RatifiedFreezeError(
                "layer1-snapshot-mismatch",
                f"holdouts.{name}.zero_hit_output_sha256 が記録フィールドの再計算値と不一致",
            )


# ---------------------------------------------------------------------------
# 検証本体
# ---------------------------------------------------------------------------

def _collect_records(head: str, graph: _CommitGraph, root: Path):
    """namespace を分類し、各 record を構造・履歴・provenance で検証して index を返す。"""
    generations: Dict[int, _Generation] = {}
    approvals_by_gen: Dict[str, _Approval] = {}
    approvals_by_self: Dict[str, _Approval] = {}
    pointers: Dict[str, _Pointer] = {}
    revoked: set = set()
    cancelled: set = set()

    for _mode, oid, path in _list_namespace(head, root):
        raw = _blob_bytes(head, path, root)
        intro_all = _immutable_introductions(graph, path, oid, root)

        m = _GEN_RE.match(path)
        if m:
            number = int(m.group(1))
            sha = _sha256_hex(raw)
            doc = _parse_generation_document(raw, number)
            commit = _unique_introduction(intro_all, path)
            _assert_candidate_commit(commit, graph, root)
            if number in generations:
                raise RatifiedFreezeError("duplicate-generation", f"世代 g{number} が重複")
            generations[number] = _Generation(number, path, raw, sha, doc, commit)
            continue

        m = _APPROVAL_RE.match(path)
        if m:
            gen_sha = m.group(1)
            doc = _load_canonical(raw, _APPROVAL_KEYS, what="approval record")
            if doc.get("generation_sha256") != gen_sha:
                raise RatifiedFreezeError(
                    "approval-filename", f"approval filename と generation_sha256 不一致: {path}"
                )
            intro = _unique_introduction(intro_all, path)
            _assert_user_commit(intro, graph, root)
            approval = _Approval(gen_sha, path, raw, _sha256_hex(raw), doc, intro)
            approvals_by_gen[gen_sha] = approval
            approvals_by_self[approval.sha256] = approval
            continue

        m = _ACTIVE_RE.match(path)
        if m:
            ptr_sha = m.group(1)
            doc = _load_canonical(raw, _POINTER_KEYS, what="active pointer")
            if _sha256_hex(raw) != ptr_sha:
                raise RatifiedFreezeError(
                    "pointer-filename", f"pointer filename が bytes hash と不一致: {path}"
                )
            intro = _unique_introduction(intro_all, path)
            _assert_user_commit(intro, graph, root)
            pointers[ptr_sha] = _Pointer(
                doc["generation_number"], path, raw, ptr_sha, doc, intro
            )
            continue

        m = _REVOCATION_RE.match(path)
        if m:
            gen_sha = m.group(1)
            doc = _load_canonical(raw, _REVOCATION_KEYS, what="revocation tombstone")
            if doc.get("generation_sha256") != gen_sha:
                raise RatifiedFreezeError(
                    "revocation-filename", f"revocation filename と generation_sha256 不一致: {path}"
                )
            intro = _unique_introduction(intro_all, path)
            _assert_user_commit(intro, graph, root)
            revoked.add(gen_sha)
            continue

        m = _CANCEL_RE.match(path)
        if m:
            ptr_sha = m.group(1)
            doc = _load_canonical(raw, _CANCEL_KEYS, what="cancellation tombstone")
            if doc.get("pointer_sha256") != ptr_sha:
                raise RatifiedFreezeError(
                    "cancellation-filename", f"cancellation filename と pointer_sha256 不一致: {path}"
                )
            intro = _unique_introduction(intro_all, path)
            _assert_user_commit(intro, graph, root)
            cancelled.add(ptr_sha)
            continue

        # v1 legacy freeze は v2 resolution の対象外 (LegacyFreeze で別途束縛)。
        if path == V1_FREEZE_PATH:
            continue
        # その他の非該当 file は active を付与し得ないため resolution 対象から除外する。

    return generations, approvals_by_gen, approvals_by_self, pointers, revoked, cancelled


def _verify_generation_chain(generations: Dict[int, _Generation]) -> None:
    """supersedes 連鎖を検査する (C1-2/C1-8)。g1 は v1 hash、gN は g(N-1) bytes hash。"""
    for number in sorted(generations):
        gen = generations[number]
        supersedes = gen.doc.get("supersedes_sha256")
        if number == 1:
            expected = V1_FREEZE_SHA256
        else:
            parent = generations.get(number - 1)
            if parent is None:
                raise RatifiedFreezeError(
                    "generation-chain-gap", f"g{number} の親 g{number - 1} が存在しない"
                )
            expected = parent.sha256
        if supersedes != expected:
            raise RatifiedFreezeError(
                "generation-supersedes",
                f"g{number} の supersedes_sha256 が親 hash と不一致",
            )


def _verify_pairing(
    approval: _Approval, pointer: _Pointer, generation: _Generation, root: Path,
) -> None:
    """approval A と active pointer X が別 commit A→X で導入されたことを検査する。"""
    commit_a = approval.intro
    commit_x = pointer.intro
    if commit_a == commit_x:
        # 診断専用。A の exact diff 検査も同一 commit の A+X を必ず拒否するため、
        # この guard 自体は受理集合を狭めない。
        raise RatifiedFreezeError(
            "approval-pointer-same-commit",
            f"approval commit A と pointer commit X が同一: {commit_a}",
        )
    if commit_a == generation.commit:
        raise RatifiedFreezeError(
            "generation-approval-same-commit",
            f"世代導入 commit G と approval commit A が同一: {commit_a}",
        )
    added, other = _added_paths(commit_a, root)
    if added != frozenset({approval.path}) or other:
        raise RatifiedFreezeError(
            "approval-commit-diff",
            f"approval commit {commit_a} の diff が approval 1 件の追加のみでない: "
            f"added={sorted(added)} other={list(other)}",
        )
    added, other = _added_paths(commit_x, root)
    if added != frozenset({pointer.path}) or other:
        raise RatifiedFreezeError(
            "pointer-commit-diff",
            f"pointer commit {commit_x} の diff が pointer 1 件の追加のみでない: "
            f"added={sorted(added)} other={list(other)}",
        )
    parents = _parents_of(commit_x, root)
    if parents != (commit_a,):
        raise RatifiedFreezeError(
            "pointer-approval-parent",
            f"pointer commit X の parent が selected approval commit A ちょうど 1 件でない: "
            f"parents={parents} approval={commit_a}",
        )


def resolve_active_generation(root=ROOT) -> ActiveResolution:
    """H に対する純関数として active 世代を解決する (structural machinery)。

    検証開始時に H を 1 回捕捉し、以後の列挙・blob 読取・履歴検査を全て H に固定する。
    active は live pointer 連鎖の一意な先端からのみ導く (「最新 = 有効」は書かない)。
    あらゆる不整合 (fork・連番飛び・第二 genesis・record 不整合・approval 不成立・
    tip 世代 revoked) は「active なし」に倒し RatifiedFreezeError を送出する。"""
    root = Path(root)
    head = _capture_head(root)
    _assert_namespace_clean(root)
    graph = _commit_graph(head, root)

    generations, approvals_by_gen, approvals_by_self, pointers, revoked, cancelled = \
        _collect_records(head, graph, root)
    _verify_generation_chain(generations)

    # 各 pointer を検証: 参照整合 + approval + pairing。
    for ptr_sha, pointer in pointers.items():
        gen_sha = pointer.doc.get("sha256")
        number = pointer.doc.get("generation_number")
        generation = generations.get(number) if isinstance(number, int) else None
        if generation is None or generation.sha256 != gen_sha \
                or pointer.doc.get("path") != generation.path:
            raise RatifiedFreezeError(
                "pointer-generation", f"pointer {ptr_sha} が指す世代が不整合"
            )
        approval_sha = pointer.doc.get("approval_sha256")
        approval = approvals_by_self.get(approval_sha)
        if approval is None or approval.generation_sha256 != generation.sha256:
            raise RatifiedFreezeError(
                "pointer-approval", f"pointer {ptr_sha} の approval が不成立"
            )
        parent = pointer.doc.get("parent_active_sha256")
        if parent is not None and parent not in pointers:
            raise RatifiedFreezeError(
                "pointer-parent", f"pointer {ptr_sha} の parent が存在しない: {parent}"
            )
        _verify_pairing(approval, pointer, generation, root)

    # live pointer 連鎖の一意な先端を求める。
    live = {sha: ptr for sha, ptr in pointers.items() if sha not in cancelled}
    if not live:
        raise RatifiedFreezeError("no-active", "live active pointer が無い (v2 未発効)")

    genesis = [ptr for ptr in live.values() if ptr.doc.get("parent_active_sha256") is None]
    if len(genesis) != 1:
        raise RatifiedFreezeError(
            "genesis-count", f"live genesis pointer がちょうど 1 個でない: {len(genesis)}"
        )

    child_map: Dict[str, List[_Pointer]] = {}
    for ptr in live.values():
        parent = ptr.doc.get("parent_active_sha256")
        if parent is not None:
            child_map.setdefault(parent, []).append(ptr)
    for parent_sha, children in child_map.items():
        if len(children) > 1:
            raise RatifiedFreezeError(
                "pointer-fork", f"parent {parent_sha} に live child が {len(children)} 個 (fork)"
            )

    chain: List[_Pointer] = [genesis[0]]
    while True:
        children = child_map.get(chain[-1].sha256, [])
        if not children:
            break
        chain.append(children[0])
    if len(chain) != len(live):
        raise RatifiedFreezeError(
            "pointer-disconnected",
            f"live pointer 連鎖に孤立/分断がある: chain={len(chain)} live={len(live)}",
        )
    for index, ptr in enumerate(chain):
        if ptr.doc.get("generation_number") != index + 1:
            raise RatifiedFreezeError(
                "pointer-number-gap",
                f"pointer 連鎖 {index} 番目の generation_number が {index + 1} でない",
            )

    tip = chain[-1]
    generation = generations[tip.doc["generation_number"]]
    if generation.sha256 in revoked:
        raise RatifiedFreezeError(
            "tip-revoked", f"active tip 世代 g{generation.number} が revoked"
        )
    approval = approvals_by_self[tip.doc["approval_sha256"]]

    return ActiveResolution(
        activation_head=head,
        generation_number=generation.number,
        generation_path=generation.path,
        generation_bytes=generation.raw,
        generation_sha256=generation.sha256,
        generation_commit=generation.commit,
        approval_sha256=approval.sha256,
        approval_document=MappingProxyType(dict(approval.doc)),
        pointer_sha256=tip.sha256,
        pointer_document=MappingProxyType(dict(tip.doc)),
    )


def load_ratified_freeze(root=ROOT) -> RatifiedFreeze:
    """承認済み active 世代を検証して RatifiedFreeze を返す (唯一の実走 loader)。

    resolve_active_generation で record/連鎖/承認 (structural) を fail-closed 検証し、
    世代 document を strict parse (structural) して deep-immutable な RatifiedFreeze を
    構築する。世代内容の追加ゲート (source/closure/transition/frozen_at_head) は
    _verify_generation_semantics (W3) を経由する。"""
    root = Path(root)
    resolution = resolve_active_generation(root)
    document = _parse_generation_document(
        resolution.generation_bytes, resolution.generation_number
    )
    _verify_generation_semantics(document, resolution, root)
    return RatifiedFreeze(
        document=_deep_freeze(document),
        sha256=resolution.generation_sha256,
        generation_number=resolution.generation_number,
        activation_head=resolution.activation_head,
        generation_commit=resolution.generation_commit,
    )


def read_floor_source_blob(ratified: "RatifiedFreeze", root=ROOT) -> bytes:
    """RatifiedFreeze の floor_source が指す floor artifact の blob bytes を返す (C3-7)。

    世代導入 commit G の tree から 1 回だけ blob を読み、記録 sha256 との一致を確認する
    (worktree 再読込でなく blob 1 回読み — H-pure と同じ規律)。floor_source blob 自体は
    load_ratified_freeze の _verify_generation_semantics (V1d) で既に blob 実在 + sha256 +
    dirty + 履歴不変を検査済みだが、consumer (oracle driver の binary store 消費) が期待
    binary hash を引くために内容 bytes を取り出す helper を分離する。"""
    root = Path(root)
    path, sha = _source_record_path_sha(ratified.document, "floor_source")
    blob = _blob_at_or_fail(
        ratified.generation_commit, path, root, reason="floor-source-missing",
    )
    if _sha256_hex(blob) != sha:
        raise RatifiedFreezeError(
            "floor-source-mismatch",
            f"floor_source:{path} の blob sha256 が記録と不一致",
        )
    return blob


def load_legacy_freeze(root=ROOT) -> LegacyFreeze:
    """v1 単一 filename freeze を bytes 定数で束縛して LegacyFreeze を返す (C2-5)。

    v1 canonical path の bytes を読み、sha256 == V1_FREEZE_SHA256 を要求する。source/head
    再検証はしない (frozen_at_head dangling、§5-viii)。RatifiedFreeze とは別型で consumer
    が v2 実走経路へ誤って流せない。"""
    root = Path(root)
    path = root / V1_FREEZE_PATH
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RatifiedFreezeError("legacy-read", f"v1 freeze を読めない: {path}") from exc
    sha = _sha256_hex(raw)
    if sha != V1_FREEZE_SHA256:
        raise RatifiedFreezeError(
            "legacy-hash", f"v1 freeze bytes sha256 が定数と不一致: {sha}"
        )
    document = _strict_load(raw, what="v1 legacy freeze")
    return LegacyFreeze(document=_deep_freeze(document), sha256=sha)


# ---------------------------------------------------------------------------
# 実走前検証 (未知性層2 = full scan。C2-10 の型分離)
# ---------------------------------------------------------------------------

_CCBENCH_GITLINK = "external/ccbench"


def _enumeration_digest(root: Path) -> str:
    """検索対象**ファイル名集合**の digest (走査前後で一致比較する。C2-8)。

    列挙集合 (path のみ) の sha256 であり、走査中のファイル追加/削除 (=集合変化) を露出する。
    列挙後・当該 read 前の内容改竄 (空白化→復元) は名前が不変なら検出しない — この内容 TOCTOU
    窓は single-tenant 前提に依存する既知残余 (§5-viii)。内容まで締めるには full-repo 内容 hash
    が要るが、それは C2-3 で退けた GB 級 scan コストのため採らない。"""
    files = _hf.enumerate_repository_files(root)
    joined = "\n".join(files).encode("utf-8")
    return _sha256_hex(joined)


def _symlink_gitlink_inventory(head: str, root: Path) -> Tuple[str, ...]:
    """H tree の symlink (120000) / gitlink (160000) を明示列挙する (黙殺しない、C2-3)。

    既知の external/ccbench gitlink (search が意図的に再帰する submodule) は除く。列挙
    自体を LaunchValidatedFreeze へ surface することで、v1 と同じ「ignored 領域は scan
    境界外」の既知限界 (§5-viii) を沈黙させない。closure は blob 検証済みのためここに
    現れない (現れたら別経路で fail-closed)。"""
    out = _git(["ls-tree", "-r", "-z", head], root)
    inventory: List[str] = []
    for chunk in out.split(b"\0"):
        if not chunk:
            continue
        meta, sep, path = chunk.decode("utf-8", "strict").partition("\t")
        if not sep:
            continue
        mode = meta.split(" ", 1)[0]
        if mode in ("120000", "160000") and path != _CCBENCH_GITLINK:
            inventory.append(path)
    return tuple(sorted(inventory))


def _assert_search_operational(report: Mapping) -> None:
    """陽性対照 (rr50) が hit することを要求する (C2-10: 検索式の偽保証を排除、_assert_search_pass
    から陽性対照だけを分離)。holdout hit の 0 件要求は v2 では課さない (post-floor は closure
    と完全一致)。"""
    positive = report.get("positive_control")
    hit_count = positive.get("hit_count") if isinstance(positive, Mapping) else None
    if not isinstance(hit_count, int) or isinstance(hit_count, bool) or hit_count <= 0:
        raise RatifiedFreezeError(
            "search-not-operational", "rr50 陽性対照が 0 件 (検索式の偽保証を排除できない)"
        )


def _plain_json(value):
    if isinstance(value, Mapping):
        return {key: _plain_json(child) for key, child in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain_json(child) for child in value]
    return value


def _exact_keys(value, expected: frozenset, *, reason: str, label: str) -> Mapping:
    if not isinstance(value, Mapping) or set(value) != set(expected):
        actual = set(value) if isinstance(value, Mapping) else set()
        raise RatifiedFreezeError(
            reason, f"{label} exact keys 不一致: {sorted(actual ^ set(expected), key=repr)}",
            cause="schema-keys",
        )
    return value


def _assert_equality_adjacency(nodes: Mapping[str, object]) -> None:
    """``EQUALITY_CHAIN_ADJACENCY`` の全辺を accessor 名で一律検査する。"""
    expected_nodes = {node for edge in EQUALITY_CHAIN_ADJACENCY for node in edge}
    if set(nodes) != expected_nodes:
        raise RatifiedFreezeError(
            "binding-chain-mismatch",
            f"equality node 集合が不一致: {sorted(set(nodes) ^ expected_nodes)}",
            cause="equality-node-set",
        )
    for left, right in EQUALITY_CHAIN_ADJACENCY:
        if nodes[left] != nodes[right] or type(nodes[left]) is not type(nodes[right]):
            raise RatifiedFreezeError(
                "binding-chain-mismatch", f"equality edge が不一致: {left} != {right}",
                cause=f"equality-edge:{left}->{right}",
            )


def _strict_jsonl(raw: bytes) -> Tuple[dict, ...]:
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise RatifiedFreezeError(
            "journal-state-invalid", "journal が UTF-8 でない", cause="bad-utf8",
        ) from exc
    if not text or not text.endswith("\n"):
        raise RatifiedFreezeError(
            "journal-state-invalid", "journal が空または末尾改行なし", cause="truncated-jsonl",
        )
    records: List[dict] = []
    for index, line in enumerate(text.splitlines()):
        if not line:
            raise RatifiedFreezeError(
                "journal-state-invalid", f"journal[{index}] が空行", cause="blank-jsonl-line",
            )
        records.append(_strict_load(line.encode("utf-8"), what=f"journal[{index}]"))
    return tuple(records)


def _require_utc(value: object, *, reason: str, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise RatifiedFreezeError(reason, f"{label} が空でない UTC str でない", cause="utc-type")
    try:
        parsed = dt.datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError as exc:
        raise RatifiedFreezeError(reason, f"{label} が ISO-8601 でない", cause="utc-format") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise RatifiedFreezeError(reason, f"{label} が UTC でない", cause="utc-zone")
    return value


def _validate_host_process_fields(record: Mapping, *, label: str) -> None:
    if not isinstance(record["hostname"], str) or not record["hostname"]:
        raise RatifiedFreezeError(
            "journal-state-invalid", f"{label}.hostname が空でない str でない",
            cause="host-provenance",
        )
    for key in ("boot_id", "job_id", "cpuset"):
        if record[key] is not None and (not isinstance(record[key], str) or not record[key]):
            raise RatifiedFreezeError(
                "journal-state-invalid", f"{label}.{key} が null/str でない",
                cause="host-provenance",
            )
    _require_utc(record["utc"], reason="journal-state-invalid", label=f"{label}.utc")
    if type(record["pid"]) is not int or record["pid"] <= 0:
        raise RatifiedFreezeError(
            "journal-state-invalid", f"{label}.pid が正整数でない", cause="process-identity",
        )
    if (record["starttime"] is not None
            and (type(record["starttime"]) is not int or record["starttime"] < 0)):
        raise RatifiedFreezeError(
            "journal-state-invalid", f"{label}.starttime が null/非負整数でない",
            cause="process-identity",
        )
    if (not isinstance(record["execution_uuid"], str)
            or re.fullmatch(r"[0-9a-f]{32}", record["execution_uuid"]) is None):
        raise RatifiedFreezeError(
            "journal-state-invalid", f"{label}.execution_uuid が 32 lower-hex でない",
            cause="process-identity",
        )


def _tree_mode_oid(commit: str, path: str, root: Path) -> Tuple[str, str]:
    out = _git(["ls-tree", "-z", commit, "--", path], root)
    chunks = [chunk for chunk in out.split(b"\0") if chunk]
    if len(chunks) != 1:
        raise RatifiedFreezeError(
            "floor-artifact-invalid", f"{commit}:{path} が一意な tree entry でない",
            cause="artifact-missing",
        )
    try:
        meta, sep, actual_path = chunks[0].decode("utf-8", "strict").partition("\t")
    except UnicodeError as exc:
        raise RatifiedFreezeError(
            "floor-artifact-invalid", f"{commit}:{path} の path が UTF-8 でない",
            cause="bad-path-utf8",
        ) from exc
    mode, typ, oid = meta.split(" ")
    if not sep or actual_path != path or typ != "blob" or mode not in ("100644", "100755"):
        raise RatifiedFreezeError(
            "floor-artifact-invalid", f"{commit}:{path} が regular blob でない (mode={mode})",
            cause="artifact-mode",
        )
    return mode, oid


def _read_worktree_nofollow(root: Path, path: str) -> bytes:
    """root から component ごとに lstat し、leaf は O_NOFOLLOW で一度だけ読む。"""
    _assert_canonical_relative_path(path, reason="floor-artifact-invalid", label=path)
    try:
        root_st = root.lstat()
    except OSError as exc:
        raise RatifiedFreezeError(
            "floor-artifact-invalid", f"repo root を lstat できない: {root}",
            cause="worktree-lstat",
        ) from exc
    if stat.S_ISLNK(root_st.st_mode) or not stat.S_ISDIR(root_st.st_mode):
        raise RatifiedFreezeError(
            "floor-artifact-invalid", f"repo root が実 directory でない: {root}",
            cause="worktree-symlink",
        )
    current = root
    components = path.split("/")
    for index, component in enumerate(components):
        current = current / component
        try:
            st = current.lstat()
        except OSError as exc:
            raise RatifiedFreezeError(
                "floor-artifact-invalid", f"worktree artifact を lstat できない: {path}",
                cause="worktree-lstat",
            ) from exc
        if stat.S_ISLNK(st.st_mode):
            raise RatifiedFreezeError(
                "floor-artifact-invalid", f"worktree path component が symlink: {current}",
                cause="worktree-symlink",
            )
        if index < len(components) - 1 and not stat.S_ISDIR(st.st_mode):
            raise RatifiedFreezeError(
                "floor-artifact-invalid", f"worktree parent が directory でない: {current}",
                cause="worktree-component",
            )
        if index == len(components) - 1 and not stat.S_ISREG(st.st_mode):
            raise RatifiedFreezeError(
                "floor-artifact-invalid", f"worktree leaf が regular file でない: {current}",
                cause="worktree-mode",
            )
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(current, flags)
        try:
            chunks: List[bytes] = []
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            return b"".join(chunks)
        finally:
            os.close(fd)
    except OSError as exc:
        raise RatifiedFreezeError(
            "floor-artifact-invalid", f"worktree artifact を no-follow read できない: {path}",
            cause="worktree-read",
        ) from exc


def _capture_g_h_worktree(
        *, generation_commit: str, validation_head: str, path: str, root: Path,
) -> Tuple[bytes, str]:
    """G/H/worktree の bytes+regular mode 三点一致を捕捉する。"""
    g_mode, _ = _tree_mode_oid(generation_commit, path, root)
    h_mode, _ = _tree_mode_oid(validation_head, path, root)
    g_raw = _blob_bytes(generation_commit, path, root)
    h_raw = _blob_bytes(validation_head, path, root)
    wt_raw = _read_worktree_nofollow(root, path)
    try:
        wt_stat = (root / path).lstat()
    except OSError as exc:
        raise RatifiedFreezeError(
            "floor-artifact-invalid", f"worktree mode を再取得できない: {path}",
            cause="worktree-lstat",
        ) from exc
    wt_mode = "100755" if wt_stat.st_mode & 0o111 else "100644"
    if g_mode != h_mode or h_mode != wt_mode or g_raw != h_raw or h_raw != wt_raw:
        raise RatifiedFreezeError(
            "floor-artifact-invalid", f"G/H/worktree bytes+mode が一致しない: {path}",
            cause="g-h-worktree-mismatch",
        )
    return g_raw, g_mode


def _validate_portable_binaries(
        binaries: object, *, cells_by_id: Mapping[str, Mapping], ratified: RatifiedFreeze,
        protocol: Mapping, expected_policy,
) -> Dict[str, dict]:
    if not isinstance(binaries, Mapping) or set(binaries) != set(cells_by_id):
        raise RatifiedFreezeError(
            "manifest-invalid", "binaries の cell 集合が expected cells と不一致",
            cause="binaries-cell-set",
        )
    out: Dict[str, dict] = {}
    policy_sha256s: set[str] = set()
    for cell_id, raw in binaries.items():
        configuration_id = raw.get("configuration_id") if isinstance(raw, Mapping) else None
        rec = _exact_keys(
            raw, _binary_admission.portable_built_keys_for(configuration_id),
            reason="manifest-invalid", label=f"binaries[{cell_id}]",
        )
        cell = cells_by_id[cell_id]
        for key in ("cell_id", "holdout_id", "configuration_id"):
            if rec[key] != cell[key]:
                raise RatifiedFreezeError(
                    "manifest-invalid", f"binaries[{cell_id}].{key} が cell と不一致",
                    cause="binary-cell-binding",
                )
        sha = rec["binary_sha256"]
        if (not isinstance(sha, str) or _SHA_RE.fullmatch(sha) is None
                or rec["bin_hash_short"] != sha[:16]):
            raise RatifiedFreezeError(
                "manifest-invalid", f"binaries[{cell_id}] の hash identity が不正",
                cause="binary-hash",
            )
        for key in ("binary", "store_path"):
            _assert_canonical_relative_path(
                rec[key], reason="manifest-invalid", label=f"binaries[{cell_id}].{key}",
            )
        for key in ("configure_argv", "build_argv"):
            argv = rec[key]
            if (not isinstance(argv, list) or not argv
                    or any(not isinstance(token, str) or not token for token in argv)):
                raise RatifiedFreezeError(
                    "manifest-invalid", f"binaries[{cell_id}].{key} が non-empty list[str] でない",
                    cause="binary-argv",
                )
        if type(rec["cached"]) is not bool:
            raise RatifiedFreezeError(
                "manifest-invalid", f"binaries[{cell_id}].cached が bool でない",
                cause="binary-cached-type",
            )
        binding = _exact_keys(
            rec["binding"], _BINDING_KEYS, reason="manifest-invalid",
            label=f"binaries[{cell_id}].binding",
        )
        for key in ("genome_canonical", "src_token", "variant_id"):
            if not isinstance(binding[key], str) or not binding[key]:
                raise RatifiedFreezeError(
                    "manifest-invalid", f"binaries[{cell_id}].binding.{key} が空でない str でない",
                    cause="binding-type",
                )
        for key in ("entry_sha256", "binding_sha256"):
            if not isinstance(binding[key], str) or _SHA_RE.fullmatch(binding[key]) is None:
                raise RatifiedFreezeError(
                    "manifest-invalid", f"binaries[{cell_id}].binding.{key} が SHA-256 でない",
                    cause="binding-type",
                )
        preimage = {key: binding[key] for key in sorted(_BINDING_KEYS - {"binding_sha256"})}
        if binding["binding_sha256"] != _sha256_hex(_canonical_bytes(preimage)):
            raise RatifiedFreezeError(
                "manifest-invalid", f"binaries[{cell_id}].binding_sha256 が再計算不一致",
                cause="binding-sha",
            )
        try:
            entry = ratified.document["holdouts"][cell["holdout_id"]]["variant_binding"]["entries"][
                cell["configuration_id"]]
        except (KeyError, TypeError) as exc:
            raise RatifiedFreezeError(
                "manifest-invalid", f"binaries[{cell_id}] の freeze binding が無い",
                cause="binding-entry",
            ) from exc
        if binding["entry_sha256"] != _sha256_hex(_canonical_bytes(_plain_json(entry))):
            raise RatifiedFreezeError(
                "manifest-invalid", f"binaries[{cell_id}].entry_sha256 が freeze entry と不一致",
                cause="binding-entry-sha",
            )
        try:
            receipt = _binary_admission.validate_portable_binary_record(
                rec, expected_policy=expected_policy,
                expected_ccbench_pin=protocol["ccbench_pin"],
                expected_contract_sha256=protocol["contract_sha256"],
                expected_cell_id=cell_id,
                expected_holdout_id=cell["holdout_id"],
                expected_configuration_id=cell["configuration_id"],
                expected_entry_sha256=binding["entry_sha256"],
                expected_binding_sha256=binding["binding_sha256"],
            )
        except _binary_admission.BinaryAdmissionError as exc:
            raise RatifiedFreezeError(
                "manifest-invalid",
                f"binaries[{cell_id}] admission receipt が不正: {exc}",
                cause="binary-admission",
            ) from exc
        policy_sha256s.add(receipt["admission"]["policy_sha256"])
        out[cell_id] = _plain_json(rec)
    if len(policy_sha256s) != 1:
        raise RatifiedFreezeError(
            "manifest-invalid",
            "binaries の admission policy が cell 間で一意でない",
            cause="binary-admission-policy-mixed",
        )
    return out


def _validate_manifest(
        document: dict, *, protocol: Mapping, protocol_sha256: str,
        ratified: RatifiedFreeze, expected_policy,
) -> _ValidatedManifest:
    receipt = document.get("perf_preflight") if isinstance(document, Mapping) else None
    try:
        expected_use_perf = _perf_preflight.use_perf_from_receipt(receipt)
        expected_keys = _floor_contract.manifest_keys_for_mode(
            "official", perf_preflight=receipt,
        )
    except (_perf_preflight.PerfPreflightError,
            _floor_contract.FloorContractError) as exc:
        raise RatifiedFreezeError(
            "manifest-invalid", f"manifest perf 条件が不正: {exc}",
            cause="manifest-perf-condition",
        ) from exc
    ratified_expected_keys = _MANIFEST_KEYS | (
        frozenset() if expected_use_perf
        else frozenset({"perf_preflight", "perf_observation"})
    )
    if expected_keys != ratified_expected_keys:
        raise RatifiedFreezeError(
            "manifest-invalid",
            "ratified/shared manifest key 契約が不一致",
            cause="manifest-key-contract-drift",
        )
    _exact_keys(document, expected_keys, reason="manifest-invalid", label="manifest")
    if document["schema_version"] != _floor_contract.MANIFEST_SCHEMA:
        raise RatifiedFreezeError(
            "manifest-invalid",
            f"manifest.schema_version が {_floor_contract.MANIFEST_SCHEMA} でない",
            cause="manifest-schema",
        )
    expected_mirrors = {
        "protocol_sha256": protocol_sha256,
        "freeze": _plain_json(protocol["freeze"]),
        "freeze_sha256": V1_FREEZE_SHA256,
        "env_tag": protocol["env_tag"],
        "ccbench_pin": protocol["ccbench_pin"],
        "stock_configuration": protocol["stock_configuration"],
        "schedule_algorithm": protocol["schedule_algorithm"],
        "master_seed": protocol["master_seed"],
        "n_sessions": protocol["n_sessions"],
        "reps": protocol["reps"],
        "extime_s": protocol["extime_s"],
        "session_cv_max": protocol["session_cv_max"],
        "cell_cv_max": protocol["cell_cv_max"],
    }
    for key, expected in expected_mirrors.items():
        if document[key] != expected or type(document[key]) is not type(expected):
            raise RatifiedFreezeError(
                "binding-chain-mismatch", f"manifest.{key} が protocol/anchor と不一致",
                cause=f"manifest-{key}",
            )
    try:
        expected_cells = _floor_contract.enumerate_cells(
            ratified.document, stock_configuration=protocol["stock_configuration"],
        )
    except _floor_contract.FloorContractError as exc:
        raise RatifiedFreezeError(
            "manifest-invalid", f"freeze から cells を導出できない: {exc}",
            cause="expected-cells",
        ) from exc
    cells = document["cells"]
    if not isinstance(cells, list):
        raise RatifiedFreezeError("manifest-invalid", "manifest.cells が list でない", cause="cells-type")
    for index, cell in enumerate(cells):
        _exact_keys(
            cell, _MANIFEST_CELL_KEYS, reason="manifest-invalid", label=f"manifest.cells[{index}]",
        )
    if cells != expected_cells:
        raise RatifiedFreezeError(
            "manifest-invalid", "manifest.cells が freeze からの独立導出と不一致",
            cause="cells-derivation",
        )
    cells_by_id = {cell["cell_id"]: cell for cell in expected_cells}
    if len(cells_by_id) != len(expected_cells):
        raise RatifiedFreezeError("manifest-invalid", "cell_id が重複", cause="cell-id-duplicate")
    try:
        expected_schedule = _floor_contract.build_schedule(
            cells=expected_cells, master_seed=protocol["master_seed"],
            n_sessions=protocol["n_sessions"],
        )
    except _floor_contract.FloorContractError as exc:
        raise RatifiedFreezeError(
            "manifest-invalid", f"schedule を独立導出できない: {exc}", cause="schedule-derive",
        ) from exc
    schedule = document["schedule"]
    if not isinstance(schedule, list):
        raise RatifiedFreezeError(
            "manifest-invalid", "manifest.schedule が list でない", cause="schedule-type",
        )
    for index, row in enumerate(schedule):
        _exact_keys(row, _SCHEDULE_KEYS, reason="manifest-invalid", label=f"schedule[{index}]")
    if schedule != expected_schedule:
        raise RatifiedFreezeError(
            "manifest-invalid", "manifest.schedule が独立再導出と不一致",
            cause="schedule-derivation",
        )
    binaries = _validate_portable_binaries(
        document["binaries"], cells_by_id=cells_by_id, ratified=ratified,
        protocol=protocol, expected_policy=expected_policy,
    )
    try:
        run_cmd, leading_indicators = _floor_contract.manifest_perf_validation_context(
            document,
        )
        _floor_contract.validate_manifest_v3(
            document, protocol=protocol, protocol_sha256=protocol_sha256,
            freeze_sha256=V1_FREEZE_SHA256,
            expected_cells=expected_cells, expected_schedule=expected_schedule,
            mode="official",
            run_cmd=run_cmd, leading_indicators=leading_indicators,
        )
    except _floor_contract.FloorContractError as exc:
        raise RatifiedFreezeError(
            "manifest-invalid", f"共有 manifest v3 契約に不一致: {exc}",
            cause="manifest-shared-contract",
        ) from exc
    return _ValidatedManifest(
        cells=expected_cells, schedule=expected_schedule, binaries=binaries,
        expected_use_perf=expected_use_perf,
    )


def _journal_schema_key(record: Mapping) -> str:
    event = record.get("event")
    if event == "terminal":
        return f"terminal-{record.get('status')}"
    return event if isinstance(event, str) else ""


def _validate_journal(
        records: Tuple[dict, ...], *, protocol: Mapping, schedule: list[dict],
        cells: list[dict], binaries: Mapping[str, Mapping], cert_sha256: str,
        manifest_sha256: str, root: Path,
        contract: _env_contract.ExecutionEnvironmentContract,
        expected_use_perf: bool = True,
) -> dict:
    """official run journal の allowlist・型・構造を検査する。

    reservation-preflight は任意・高々 1 件で、campaign-start より前に置く。
    binding (pbs_jobid / submission_nonce) は両 event で claim 状態と値の一致を
    要求するが、記録内の整合情報であり PBS job の外部認証ではない。
    """
    if not records:
        raise RatifiedFreezeError("journal-state-invalid", "journal が空", cause="journal-empty")
    try:
        verified_calibration = _env_attestation.load_verified_calibration(contract, root)
    except _env_attestation.AttestationError as exc:
        raise RatifiedFreezeError(
            "journal-state-invalid", f"execution env contract を検証できない: {exc}",
            cause="receipt-contract",
        ) from exc
    for index, record in enumerate(records):
        key = _journal_schema_key(record)
        expected = _JOURNAL_KEYS.get(key)
        if expected is None:
            raise RatifiedFreezeError(
                "journal-state-invalid", f"journal[{index}] event/status が未知: {key!r}",
                cause="journal-event",
            )
        claims_binding = (
            key in {"reservation-preflight", "campaign-start"}
            and bool(_JOURNAL_BINDING_KEYS & set(record))
        )
        if claims_binding:
            expected = expected | _JOURNAL_BINDING_KEYS
        _exact_keys(
            record, expected, reason="journal-state-invalid", label=f"journal[{index}]/{key}",
        )
        if claims_binding and any(
                type(record[field]) is not str or record[field] == ""
                for field in _JOURNAL_BINDING_KEYS):
            raise RatifiedFreezeError(
                "journal-state-invalid", f"journal[{index}] binding 型が不正",
                cause="journal-binding-type",
            )
        if key == "reservation-preflight":
            integer_fields = _JOURNAL_KEYS[key] - {
                "event", "formula", "shared_dependency_prebuild",
            }
            if (type(record["formula"]) is not str or not record["formula"]
                    or type(record["shared_dependency_prebuild"]) is not bool
                    or any(type(record[field]) is not int or record[field] <= 0
                           for field in integer_fields)):
                raise RatifiedFreezeError(
                    "journal-state-invalid", f"journal[{index}] reservation 型が不正",
                    cause="reservation-preflight-type",
                )
        if key == "perf-preflight":
            try:
                _perf_preflight.validate_perf_preflight_receipt(
                    record["perf_preflight_receipt"]
                )
            except _perf_preflight.PerfPreflightError as exc:
                raise RatifiedFreezeError(
                    "journal-state-invalid",
                    f"journal[{index}] perf-preflight receipt が不正: {exc}",
                    cause="perf-preflight-receipt",
                ) from exc
        if key == "launch-start":
            _require_utc(
                record["utc"], reason="journal-state-invalid", label="launch-start.utc",
            )
        if key == "campaign-start":
            _validate_host_process_fields(record, label="campaign-start")
            receipt = record["execution_receipt"]
            if contract.attestation_mode == "none":
                # legacy v1 の既存 shape/UTC 検証チェーンは維持する。
                receipt = _exact_keys(
                    receipt, _RECEIPT_KEYS,
                    reason="journal-state-invalid", label="campaign-start.execution_receipt",
                )
                _exact_keys(
                    receipt["attestation"], _ATTESTATION_KEYS,
                    reason="journal-state-invalid", label="execution_receipt.attestation",
                )
                if receipt["schema"] != _execution_guard.RECEIPT_SCHEMA:
                    raise RatifiedFreezeError(
                        "journal-state-invalid", "execution_receipt.schema が不正",
                        cause="receipt-schema",
                    )
                if (not isinstance(receipt["env_tag"], str)
                        or _SHA_RE.fullmatch(receipt["contract_sha256"]) is None):
                    raise RatifiedFreezeError(
                        "journal-state-invalid", "execution_receipt env/hash 型が不正",
                        cause="receipt-type",
                    )
                attestation = receipt["attestation"]
                if (not isinstance(attestation["hostname"], str)
                        or not attestation["hostname"]):
                    raise RatifiedFreezeError(
                        "journal-state-invalid", "receipt attestation.hostname が不正",
                        cause="receipt-attestation",
                    )
                for nullable in ("boot_id", "cpuset"):
                    if (attestation[nullable] is not None
                            and (not isinstance(attestation[nullable], str)
                                 or not attestation[nullable])):
                        raise RatifiedFreezeError(
                            "journal-state-invalid", f"receipt attestation.{nullable} が不正",
                            cause="receipt-attestation",
                        )
                _require_utc(
                    attestation["captured_utc"], reason="journal-state-invalid",
                    label="receipt.attestation.captured_utc",
                )
            if not _execution_guard.receipt_matches_contract(
                    receipt, env_tag=contract.env_tag,
                    contract_sha256=contract.contract_sha256,
                    attestation_mode=contract.attestation_mode,
                    verified_calibration=(verified_calibration
                                          if contract.attestation_mode == "required"
                                          else None)):
                raise RatifiedFreezeError(
                    "journal-state-invalid", "execution receipt の契約再検算に失敗",
                    cause="receipt-contract",
                )
        if key == "resume-start":
            _validate_host_process_fields(record, label=f"resume-start[{index}]")
        if key in {"round-start", "round-complete"} and type(record["round"]) is not int:
            raise RatifiedFreezeError(
                "journal-state-invalid", f"journal[{index}].round が int でない",
                cause="round-type",
            )
        if key in {"round-start", "round-complete"}:
            _require_utc(
                record["utc"], reason="journal-state-invalid", label=f"journal[{index}].utc",
            )
        if key == "session":
            for probe_key in ("probe_before", "probe_after"):
                probe = record[probe_key]
                if probe is not None:
                    _exact_keys(
                        probe, _PROBE_KEYS, reason="journal-state-invalid",
                        label=f"journal[{index}].{probe_key}",
                    )

    launch = [(i, r) for i, r in enumerate(records) if r["event"] == "launch-start"]
    starts = [(i, r) for i, r in enumerate(records) if r["event"] == "campaign-start"]
    terminals = [(i, r) for i, r in enumerate(records) if r["event"] == "terminal"]
    if len(launch) != 1 or launch[0][0] != 0:
        raise RatifiedFreezeError(
            "journal-state-invalid", "launch-start が一意な先頭 record でない",
            cause="launch-start-order",
        )
    if len(starts) != 1:
        raise RatifiedFreezeError(
            "journal-state-invalid", "campaign-start が一意でない", cause="campaign-start-count",
        )
    if len(terminals) != 1 or terminals[0][0] != len(records) - 1 \
            or terminals[0][1].get("status") != "completed":
        raise RatifiedFreezeError(
            "journal-state-invalid", "terminal が一意・最終・completed でない",
            cause="terminal-state",
        )
    campaign = starts[0][1]
    reservations = [(i, r) for i, r in enumerate(records)
                    if r["event"] == "reservation-preflight"]
    if len(reservations) > 1:
        raise RatifiedFreezeError(
            "journal-state-invalid", "reservation-preflight が複数ある",
            cause="reservation-preflight-count",
        )
    if reservations and reservations[0][0] >= starts[0][0]:
        raise RatifiedFreezeError(
            "journal-state-invalid", "reservation-preflight が campaign-start より前でない",
            cause="reservation-preflight-order",
        )
    # binding は記録内の整合情報であり PBS job の外部認証ではない。
    campaign_claim = bool(_JOURNAL_BINDING_KEYS & set(campaign))
    reservation = reservations[0][1] if reservations else {}
    reservation_claim = bool(_JOURNAL_BINDING_KEYS & set(reservation))
    if campaign_claim != reservation_claim:
        raise RatifiedFreezeError(
            "journal-state-invalid", "campaign/reservation の binding claim が不一致",
            cause="journal-binding-claim",
        )
    if campaign_claim and reservation_claim and any(
            campaign[key] != reservation[key] for key in _JOURNAL_BINDING_KEYS):
        raise RatifiedFreezeError(
            "journal-state-invalid", "campaign/reservation の binding 値が不一致",
            cause="journal-binding-mismatch",
        )
    mirrors = {
        "protocol_sha256": _floor_contract.canonical_protocol_sha256(protocol),
        "freeze_sha256": V1_FREEZE_SHA256,
        "manifest_sha256": manifest_sha256,
        "launch_certificate_sha256": cert_sha256,
    }
    for key, expected in mirrors.items():
        if campaign[key] != expected:
            raise RatifiedFreezeError(
                "binding-chain-mismatch", f"campaign-start.{key} が不一致",
                cause=f"campaign-start-{key}",
            )
    if launch[0][1]["schema"] != _floor_contract.JOURNAL_SCHEMA \
            or campaign["schema"] != _floor_contract.JOURNAL_SCHEMA:
        raise RatifiedFreezeError(
            "journal-state-invalid", "journal schema が v3 でない", cause="journal-schema",
        )

    cell_by_id = {cell["cell_id"]: cell for cell in cells}
    planned_by_seq = {row["seq"]: row for row in schedule}
    expected_rounds = set(range(1, protocol["n_sessions"] + 1))
    round_starts = {
        round_no: [(i, r) for i, r in enumerate(records)
                   if r["event"] == "round-start" and r["round"] == round_no]
        for round_no in expected_rounds
    }
    round_completes = {
        round_no: [(i, r) for i, r in enumerate(records)
                   if r["event"] == "round-complete" and r["round"] == round_no]
        for round_no in expected_rounds
    }
    seen_round_values = {
        r["round"] for r in records if r["event"] in {"round-start", "round-complete"}
    }
    if seen_round_values != expected_rounds:
        raise RatifiedFreezeError(
            "journal-state-invalid", "round event 集合が protocol.n_sessions と不一致",
            cause="round-set",
        )
    for round_no in sorted(expected_rounds):
        if len(round_starts[round_no]) != 1 or len(round_completes[round_no]) != 1 \
                or round_starts[round_no][0][0] >= round_completes[round_no][0][0]:
            raise RatifiedFreezeError(
                "journal-state-invalid", f"round {round_no} の start/complete が一意順序でない",
                cause="round-state",
            )
        if round_no > 1 and round_completes[round_no - 1][0][0] >= round_starts[round_no][0][0]:
            raise RatifiedFreezeError(
                "journal-state-invalid", f"round {round_no - 1} と {round_no} が forward-only でない",
                cause="round-order",
            )
    session_starts: Dict[int, Tuple[int, dict]] = {}
    attempt_ids: set = set()
    retry_slots: Dict[str, set] = {}
    for index, record in enumerate(records):
        if record["event"] != "session-start":
            continue
        seq = record["seq"]
        if isinstance(seq, bool) or not isinstance(seq, int) or seq < 0 or seq in session_starts:
            raise RatifiedFreezeError(
                "journal-state-invalid", f"session-start seq が不正/重複: {seq!r}",
                cause="session-seq",
            )
        if not isinstance(record["attempt_id"], str) or record["attempt_id"] in attempt_ids:
            raise RatifiedFreezeError(
                "journal-state-invalid", "attempt_id が不正/重複", cause="attempt-id",
            )
        attempt_ids.add(record["attempt_id"])
        _require_utc(
            record["started_iso"], reason="journal-state-invalid",
            label=f"session-start[{seq}].started_iso",
        )
        if not isinstance(record["cell_id"], str) or not record["cell_id"]:
            raise RatifiedFreezeError(
                "journal-state-invalid", f"session-start[{seq}].cell_id が不正",
                cause="session-cell-id",
            )
        session_starts[seq] = (index, record)
        if type(record["round"]) is not int or record["round"] not in expected_rounds:
            raise RatifiedFreezeError(
                "journal-state-invalid", f"session-start round が不正: {record['round']!r}",
                cause="session-round",
            )
        kind = record["kind"]
        if kind == "planned":
            row = planned_by_seq.get(seq)
            if (row is None or record["cell_id"] != row["cell_id"]
                    or record["round"] != row["round"] or record["retry_ordinal"] is not None
                    or record["trigger"] is not None
                    or record["attempt_id"] != f"{record['cell_id']}::seq{seq}"):
                raise RatifiedFreezeError(
                    "journal-state-invalid", f"planned session-start が schedule[{seq}] と不一致",
                    cause="planned-schedule",
                )
        elif kind == "retry":
            ordinal = record["retry_ordinal"]
            if (seq in planned_by_seq or isinstance(ordinal, bool) or not isinstance(ordinal, int)
                    or seq < len(schedule)
                    or not 1 <= ordinal <= protocol["retry_slots_per_cell"]
                    or record["attempt_id"] != f"{record['cell_id']}::retry{ordinal}"):
                raise RatifiedFreezeError(
                    "journal-state-invalid", "retry authorization の seq/ordinal が不正",
                    cause="retry-authorization",
                )
            used = retry_slots.setdefault(record["cell_id"], set())
            if ordinal in used:
                raise RatifiedFreezeError(
                    "journal-state-invalid", "(cell_id,retry_ordinal) が重複",
                    cause="retry-slot-duplicate",
                )
            used.add(ordinal)
        else:
            raise RatifiedFreezeError(
                "journal-state-invalid", f"session-start.kind が未知: {kind!r}",
                cause="session-kind",
            )
        start_index = round_starts[record["round"]][0][0]
        complete_index = round_completes[record["round"]][0][0]
        if not start_index < index < complete_index:
            raise RatifiedFreezeError(
                "journal-state-invalid", f"session-start[{seq}] が round 境界外",
                cause="session-round-order",
            )
    if set(planned_by_seq) != {seq for seq, (_, rec) in session_starts.items()
                               if rec["kind"] == "planned"}:
        raise RatifiedFreezeError(
            "journal-state-invalid", "session-start と schedule row が 1:1 でない",
            cause="schedule-start-bijection",
        )
    try:
        _floor_contract.validate_session_start_authorizations(
            [record for record in records if record["event"] == "session-start"],
            schedule=schedule,
            retry_slots_per_cell=protocol["retry_slots_per_cell"],
        )
    except _floor_contract.FloorContractError as exc:
        raise RatifiedFreezeError(
            "journal-state-invalid", f"session-start authorization が正準でない: {exc}",
            cause="session-start-authorization",
        ) from exc

    sessions: List[dict] = []
    seen_session_seq: set = set()
    receipts: Dict[str, str] = {}
    for index, record in enumerate(records):
        if record["event"] != "session":
            continue
        seq = record["seq"]
        start = session_starts.get(seq)
        if start is None or start[0] >= index or seq in seen_session_seq:
            raise RatifiedFreezeError(
                "journal-state-invalid", f"session[{seq}] の start 対応/順序が不正",
                cause="session-start-pairing",
            )
        seen_session_seq.add(seq)
        start_rec = start[1]
        for key in ("kind", "seq", "round", "retry_ordinal", "attempt_id", "trigger", "cell_id"):
            if record[key] != start_rec[key] or type(record[key]) is not type(start_rec[key]):
                raise RatifiedFreezeError(
                    "journal-state-invalid", f"session[{seq}].{key} が start と不一致",
                    cause="session-start-field",
                )
        cell = cell_by_id.get(record["cell_id"])
        if cell is None:
            raise RatifiedFreezeError(
                "journal-state-invalid", f"session[{seq}] の cell が expected に無い",
                cause="session-cell",
            )
        for key in ("holdout_id", "configuration_id", "records", "threads", "workload"):
            if record[key] != cell[key] or type(record[key]) is not type(cell[key]):
                raise RatifiedFreezeError(
                    "journal-state-invalid", f"session[{seq}].{key} が manifest cell と不一致",
                    cause="session-workload-binding",
                )
        if record["valid"] is True and not isinstance(record.get("run_cmd"), str):
            raise RatifiedFreezeError(
                "journal-state-invalid",
                f"valid session[{seq}].run_cmd が文字列でない",
                cause="run-cmd-required",
            )
        if not _run_cmd_matches_portable_session(
                record, protocol=protocol, binaries=binaries, contract=contract,
                expected_use_perf=expected_use_perf):
            raise RatifiedFreezeError(
                "journal-state-invalid",
                f"session[{seq}].run_cmd が portable canonical argv と不一致",
                cause="run-cmd-projection",
            )
        if record["retry"] is not (record["kind"] == "retry"):
            raise RatifiedFreezeError(
                "journal-state-invalid", f"session[{seq}].retry の bool identity が不正",
                cause="session-retry-flag",
            )
        measured = record["binary_sha256_at_measure"]
        if measured != binaries[record["cell_id"]]["binary_sha256"]:
            raise RatifiedFreezeError(
                "binding-chain-mismatch", f"session[{seq}] の binary receipt が manifest と不一致",
                cause="binary-receipt",
            )
        previous = receipts.get(record["cell_id"])
        if previous is not None and previous != measured:
            raise RatifiedFreezeError(
                "binding-chain-mismatch", f"cell {record['cell_id']} の receipt が session 間で不一致",
                cause="binary-receipt-drift",
            )
        receipts[record["cell_id"]] = measured
        sessions.append(record)
    sessions_by_attempt = {record["attempt_id"]: record for record in sessions}
    for _seq, (_index, record) in session_starts.items():
        if record["kind"] != "retry":
            continue
        trigger = sessions_by_attempt.get(record["trigger"])
        if (trigger is None or trigger["kind"] != "planned" or trigger["valid"] is not False
                or trigger["cell_id"] != record["cell_id"]
                or trigger["round"] != record["round"]):
            raise RatifiedFreezeError(
                "journal-state-invalid", "retry trigger が同一 cell/round の invalid planned でない",
                cause="retry-trigger",
            )
    for cell_id, ordinals in retry_slots.items():
        if sorted(ordinals) != list(range(1, len(ordinals) + 1)):
            raise RatifiedFreezeError(
                "journal-state-invalid", f"retry ordinal が 1 起点連続でない: {cell_id}",
                cause="retry-ordinal-gap",
            )
    return {
        "launch": launch[0][1], "campaign": campaign, "terminal": terminals[0][1],
        "sessions": sessions, "records": records, "receipts": receipts,
    }


def _validate_result_top_level_keys(
        document: object, *, expected_use_perf: bool = True,
        expected_perf_preflight: object | None = None,
        expected_perf_observation: object | None = None) -> None:
    """ratified 固有の cause を保って result の exact keys を検査する。"""
    receipt = document.get("perf_preflight") if isinstance(document, Mapping) else None
    schema = document.get("schema") if isinstance(document, Mapping) else None
    key_schema = (
        _floor_contract.RESULT_SCHEMA_V5
        if schema == _floor_contract.RESULT_SCHEMA_V5
        else _floor_contract.LEGACY_RESULT_SCHEMA
    )
    try:
        derived_use_perf = _perf_preflight.use_perf_from_receipt(receipt)
        expected_keys = _floor_contract.result_keys_for_mode(
            "official", schema=key_schema, perf_preflight=receipt,
        )
    except (_perf_preflight.PerfPreflightError,
            _floor_contract.FloorContractError) as exc:
        raise RatifiedFreezeError(
            "floor-artifact-invalid", f"result perf 条件が不正: {exc}",
            cause="result-perf-condition",
        ) from exc
    if derived_use_perf is not expected_use_perf:
        raise RatifiedFreezeError(
            "binding-chain-mismatch",
            "result perf_preflight が manifest の perf 条件と不一致",
            cause="result-perf-condition",
        )
    _exact_keys(document, expected_keys, reason="floor-artifact-invalid", label="result")
    if receipt != expected_perf_preflight:
        raise RatifiedFreezeError(
            "binding-chain-mismatch",
            "result.perf_preflight != manifest.perf_preflight",
            cause="result-manifest-perf-preflight",
        )
    observation = (
        document.get("perf_observation") if isinstance(document, Mapping) else None
    )
    if observation != expected_perf_observation:
        raise RatifiedFreezeError(
            "binding-chain-mismatch",
            "result.perf_observation != manifest.perf_observation",
            cause="result-manifest-perf-observation",
        )


def _validate_result(
        document: dict, *, protocol: Mapping, cells: list[dict], binaries: Mapping[str, Mapping],
        journal: Mapping, contract: _env_contract.ExecutionEnvironmentContract,
        expected_use_perf: bool = True, expected_perf_preflight: object | None = None,
        expected_perf_observation: object | None = None,
) -> None:
    _validate_result_top_level_keys(
        document, expected_use_perf=expected_use_perf,
        expected_perf_preflight=expected_perf_preflight,
        expected_perf_observation=expected_perf_observation,
    )
    result_schema = document.get("schema")
    if (
        result_schema != _floor_contract.LEGACY_RESULT_SCHEMA
        and result_schema != _floor_contract.RESULT_SCHEMA_V5
    ):
        raise RatifiedFreezeError(
            "floor-artifact-invalid",
            f"result.schema が {_floor_contract.RESULT_SCHEMA} でない",
            cause="result-schema",
        )
    _exact_keys(
        document["config"], _RESULT_CONFIG_KEYS, reason="floor-artifact-invalid",
        label="result.config",
    )
    for cell_id, cell_stats in document["cells"].items() \
            if isinstance(document["cells"], Mapping) else ():
        _exact_keys(
            cell_stats, _RESULT_CELL_KEYS, reason="floor-artifact-invalid",
            label=f"result.cells[{cell_id}]",
        )
    if not isinstance(document["floors"], Mapping):
        raise RatifiedFreezeError(
            "floor-artifact-invalid", "result.floors が object でない", cause="floors-type",
        )
    for holdout, floor in document["floors"].items():
        _exact_keys(
            floor, _RESULT_FLOOR_KEYS, reason="floor-artifact-invalid",
            label=f"result.floors[{holdout}]",
        )
    if not isinstance(document["excluded"], list) or not isinstance(document["attempts"], list):
        raise RatifiedFreezeError(
            "floor-artifact-invalid", "result excluded/attempts が list でない",
            cause="projection-type",
        )
    for index, row in enumerate(document["excluded"]):
        _exact_keys(
            row, _EXCLUDED_KEYS, reason="floor-artifact-invalid",
            label=f"result.excluded[{index}]",
        )
    for index, row in enumerate(document["attempts"]):
        _exact_keys(
            row, _ATTEMPT_KEYS, reason="floor-artifact-invalid",
            label=f"result.attempts[{index}]",
        )
    result_sessions = document["sessions"] if isinstance(document["sessions"], list) else ()
    for index, record in enumerate(result_sessions):
        if (not isinstance(record, Mapping)
                or not _run_cmd_matches_portable_session(
                    record, protocol=protocol, binaries=binaries, contract=contract,
                    expected_use_perf=expected_use_perf)):
            raise RatifiedFreezeError(
                "floor-artifact-invalid",
                f"result.sessions[{index}].run_cmd が portable canonical argv と不一致",
                cause="run-cmd-projection",
            )

    sessions = journal["sessions"]
    excluded = [
        {
            "seq": r["seq"], "cell_id": r["cell_id"], "kind": r["kind"],
            "retry": r["retry"], "round": r["round"],
            "excluded_reason": r["excluded_reason"], "session_cv": r["session_cv"],
            "exclusion_class": r["exclusion_class"],
            "rep_integrity_failures": r["rep_integrity_failures"],
        }
        for r in sessions if not r["valid"]
    ]
    attempts = [
        {
            "seq": r["seq"], "cell_id": r["cell_id"], "kind": r["kind"],
            "round": r["round"], "retry_ordinal": r["retry_ordinal"],
            "valid": r["valid"], "excluded_reason": r["excluded_reason"],
            "exclusion_class": r["exclusion_class"],
            "rep_integrity_failures": r["rep_integrity_failures"],
            "session_cv": r["session_cv"], "session_median": r["session_median"],
            "duration_s": r["duration_s"],
        }
        for r in sessions
    ]
    wall_ledger = [
        _plain_json(record) for record in journal["records"]
        if record["event"] in {"campaign-start", "round-start", "round-complete"}
    ]
    mirrors = {
        "formula": protocol["formula"], "mode": "official", "env_tag": protocol["env_tag"],
        "ccbench_pin": protocol["ccbench_pin"],
        "protocol_sha256": _floor_contract.canonical_protocol_sha256(protocol),
        "freeze_sha256": V1_FREEZE_SHA256,
        "stock_configuration": protocol["stock_configuration"],
        "wired_min_rel_floor": protocol["wired_min_rel_floor"], "reps": protocol["reps"],
        "n_sessions": protocol["n_sessions"],
        "scale_adequacy_rel_tolerance": protocol["scale_adequacy_rel_tolerance"],
        "holdouts": sorted({cell["holdout_id"] for cell in cells}),
        "configurations": sorted({cell["configuration_id"] for cell in cells}),
        "binaries": _plain_json(binaries), "sessions": _plain_json(sessions),
        "wall_ledger": wall_ledger, "excluded": excluded, "attempts": attempts,
    }
    for key, expected in mirrors.items():
        if document[key] != expected or type(document[key]) is not type(expected):
            raise RatifiedFreezeError(
                "binding-chain-mismatch", f"result.{key} が journal/protocol 再導出と不一致",
                cause=f"result-{key}",
            )
    if document["eligible_for_refreeze"] is not True:
        raise RatifiedFreezeError(
            "binding-chain-mismatch", "eligible_for_refreeze が bool True でない",
            cause="eligible-flag",
        )


def _json_pointer_token(token: object) -> str:
    return str(token).replace("~", "~0").replace("/", "~1")


def _walk_json(value, pointer: str = ""):
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_pointer = pointer + "/" + _json_pointer_token(key)
            yield child_pointer, key, child
            yield from _walk_json(child, child_pointer)
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            child_pointer = pointer + f"/{index}"
            yield child_pointer, index, child
            yield from _walk_json(child, child_pointer)


def _run_cmd_matches_portable_session(
        record: Mapping, *, protocol: Mapping,
        binaries: Mapping[str, Mapping],
        contract: _env_contract.ExecutionEnvironmentContract,
        expected_use_perf: bool = True) -> bool:
    """session.run_cmd が検証済み構造値からの leaf 再構築と完全一致するか返す。"""
    run_cmd = record.get("run_cmd")
    if run_cmd is None:
        return True
    if not isinstance(run_cmd, str):
        return False
    cell_id = record.get("cell_id")
    binary_record = binaries.get(cell_id) if isinstance(cell_id, str) else None
    if not isinstance(binary_record, Mapping):
        return False
    try:
        tokens = shlex.split(run_cmd)
        expected = _floor_contract.build_portable_run_cmd(
            binary=binary_record["binary"], workload=record["workload"],
            records=record["records"], threads=record["threads"],
            extime_s=protocol["extime_s"], clocks_per_us=contract.clocks_per_us,
            numactl=contract.numactl,
            use_perf=expected_use_perf,
        )
    except (ValueError, KeyError, TypeError, _floor_contract.FloorContractError):
        return False
    return tuple(tokens) == expected


def _validate_axis_occurrences(
        *, artifacts: Sequence[Tuple[str, object, Optional[bytes]]], protocol: Mapping,
        binaries: Mapping[str, Mapping],
        contract: _env_contract.ExecutionEnvironmentContract,
        expected_use_perf: bool = True,
        closure_paths: frozenset = frozenset(),
) -> Dict[str, list]:
    """軸 occurrence を path/record-index/pointer/holdout/axis/encoding 単位で検査する。"""
    axis_keys = {
        "rratio": _hf.RRATIO_KEY, "skew": _hf.SKEW_KEY, "rmw": _hf.RMW_KEY,
    }
    per_holdout_paths = {name: {axis: set() for axis in axis_keys} for name in _hf.HOLDOUTS}
    raw_texts: Dict[str, str] = {}
    for path, document, raw in artifacts:
        if raw is not None:
            try:
                raw_texts[path] = raw.decode("utf-8", "strict")
            except UnicodeError as exc:
                raise RatifiedFreezeError(
                    "floor-artifact-invalid", f"scan union artifact が UTF-8 でない: {path}",
                    cause="union-nontext",
                ) from exc
        if path in closure_paths:
            text = raw_texts.get(path, "")
            for holdout, frozen in _hf.HOLDOUTS.items():
                workload = frozen["ycsb"]
                expressions = _hf._expressions(
                    workload[_hf.RRATIO_KEY], workload[_hf.SKEW_KEY], workload[_hf.RMW_KEY],
                )
                for axis, expression in expressions.items():
                    if re.search(expression, text):
                        per_holdout_paths[holdout][axis].add(path)
        records = document if isinstance(document, tuple) else (document,)
        for record_index, record in enumerate(records):
            if not isinstance(record, Mapping):
                continue
            for pointer, key, value in _walk_json(record):
                for holdout, frozen in _hf.HOLDOUTS.items():
                    workload = frozen["ycsb"]
                    expressions = _hf._expressions(
                        workload[_hf.RRATIO_KEY], workload[_hf.SKEW_KEY], workload[_hf.RMW_KEY],
                    )
                    for axis, axis_key in axis_keys.items():
                        occurred = False
                        encoding = ""
                        if key == axis_key and value == workload[axis_key]:
                            occurred, encoding = True, "json-field"
                        if isinstance(value, str):
                            expression = expressions[axis]
                            if re.search(expression, value):
                                occurred, encoding = True, "string"
                        if not occurred:
                            continue
                        per_holdout_paths[holdout][axis].add(path)
                        allowed = path in closure_paths
                        if encoding == "json-field":
                            if path.endswith("manifest.json") and re.fullmatch(
                                    r"/cells/[0-9]+/workload/[^/]+", pointer):
                                allowed = True
                            elif path.endswith("result.json") and re.fullmatch(
                                    r"/sessions/[0-9]+/workload/[^/]+", pointer):
                                allowed = True
                            elif path.endswith("journal.jsonl") and record.get("event") == "session" \
                                    and re.fullmatch(r"/workload/[^/]+", pointer):
                                allowed = True
                        cmd_record = None
                        if (path.endswith("journal.jsonl")
                                and record.get("event") == "session"
                                and pointer == "/run_cmd"):
                            cmd_record = record
                        elif path.endswith("result.json"):
                            match = re.fullmatch(r"/sessions/([0-9]+)/run_cmd", pointer)
                            sessions = record.get("sessions")
                            if match and isinstance(sessions, list):
                                index = int(match.group(1))
                                if index < len(sessions) and isinstance(sessions[index], Mapping):
                                    cmd_record = sessions[index]
                        if (cmd_record is not None
                                and _run_cmd_matches_portable_session(
                                    cmd_record, protocol=protocol, binaries=binaries,
                                    contract=contract,
                                    expected_use_perf=expected_use_perf)):
                            allowed = True
                        if path.endswith(("manifest.json", "result.json")):
                            receipt_match = re.fullmatch(
                                r"/binaries/[^/]+/sort_swo_oracle/([^/]+)", pointer,
                            )
                            if (receipt_match is not None
                                    and receipt_match.group(1)
                                    in _SORT_SWO_ORACLE_AXIS_SAFE_KEYS):
                                allowed = True
                        if not allowed:
                            raise RatifiedFreezeError(
                                "floor-artifact-invalid",
                                "unauthorized axis occurrence: "
                                f"({path}, record={record_index}, pointer={pointer}, "
                                f"holdout={holdout}, axis={axis}, encoding={encoding})",
                                cause="axis-occurrence",
                            )
    raw_hits = _hf.holdout_conjunction_hits(raw_texts)
    occurrence_hits = {
        holdout: sorted(set.intersection(*[paths for paths in axes.values()]))
        for holdout, axes in per_holdout_paths.items()
    }
    if occurrence_hits != raw_hits:
        raise RatifiedFreezeError(
            "floor-artifact-invalid", "raw scanner と occurrence validator が非同値",
            cause="occurrence-scanner-drift",
        )
    return raw_hits


def _assert_no_untracked_symlink(root: Path) -> None:
    raw = _git(["ls-files", "-z", "--others", "--exclude-standard"], root)
    for part in raw.split(b"\0"):
        if not part:
            continue
        try:
            rel = part.decode("utf-8", "strict")
        except UnicodeError as exc:
            raise RatifiedFreezeError(
                "scan-exemption-invalid", "untracked path が UTF-8 でない",
                cause="untracked-path-utf8",
            ) from exc
        current = root
        for component in rel.split("/"):
            current = current / component
            try:
                st = current.lstat()
            except OSError as exc:
                raise RatifiedFreezeError(
                    "scan-exemption-invalid", f"untracked path を lstat できない: {rel}",
                    cause="untracked-lstat",
                ) from exc
            if stat.S_ISLNK(st.st_mode):
                raise RatifiedFreezeError(
                    "scan-exemption-invalid", f"untracked symlink は scan 不能: {rel}",
                    cause="untracked-symlink",
                )


def _selector_tree_entry(head: str, path: str, root: Path) -> Tuple[str, str] | None:
    """H:path の exact tree entry を返す。不存在だけ None、曖昧/非 blob は拒否。"""
    out = _git(["ls-tree", "-z", head, "--", path], root)
    chunks = [chunk for chunk in out.split(b"\0") if chunk]
    if not chunks:
        return None
    if len(chunks) != 1:
        raise RatifiedFreezeError(
            "scan-exemption-invalid", f"selector evidence tree entry が一意でない: {path}",
            cause="selector-evidence-path",
        )
    try:
        meta, sep, actual = chunks[0].decode("utf-8", "strict").partition("\t")
        mode, typ, oid = meta.split(" ")
    except (UnicodeError, ValueError) as exc:
        raise RatifiedFreezeError(
            "scan-exemption-invalid", f"selector evidence tree entry が不正: {path}",
            cause="selector-evidence-path",
        ) from exc
    if not sep or actual != path or typ != "blob":
        raise RatifiedFreezeError(
            "scan-exemption-invalid", f"selector evidence が exact blob でない: {path}",
            cause="selector-evidence-path",
        )
    return mode, oid


def _selector_evidence_exempt_exact(*, head: str, root: Path) -> Dict[str, str]:
    """H 錨定の selector 証拠鎖を検証し、exact path→H-bytes hash を返す。"""
    predictions_entry = _selector_tree_entry(head, _SELECTOR_PREDICTIONS_PATH, root)
    if predictions_entry is None:
        return {}

    try:
        from . import s8b_prediction_runner as _prediction_runner
        from . import s8b_selector_freeze as _selector_freeze
    except ImportError as exc:  # pragma: no cover - package installation failure
        raise RatifiedFreezeError(
            "scan-exemption-invalid", f"selector verifier を import できない: {exc}",
            cause="selector-declaration-invalid",
        ) from exc

    def fail(message: str, cause: str, exc: BaseException | None = None):
        error = RatifiedFreezeError("scan-exemption-invalid", message, cause=cause)
        if exc is None:
            raise error
        raise error from exc

    def h_blob_100644(path: str) -> bytes:
        _assert_canonical_relative_path(
            path, reason="scan-exemption-invalid", label="selector evidence path",
        )
        entry = _selector_tree_entry(head, path, root)
        if entry is None:
            fail(f"selector evidence が H tree にない: {path}", "selector-evidence-missing")
        assert entry is not None
        mode, _oid = entry
        if mode != "100644":
            fail(
                f"selector evidence の H mode が 100644 でない: {path} ({mode})",
                "selector-evidence-mode",
            )
        try:
            return _blob_bytes(head, path, root)
        except RatifiedFreezeError as exc:
            fail(f"selector evidence の H bytes を読めない: {path}",
                 "selector-evidence-missing", exc)

    exempt: Dict[str, str] = {}

    def add_exempt(path: str, *, declared_sha256: str | None = None) -> bytes:
        if path in exempt:
            fail(f"selector evidence path が重複: {path}", "selector-evidence-duplicate")
        raw = h_blob_100644(path)
        try:
            worktree = _read_worktree_nofollow(root, path)
        except RatifiedFreezeError as exc:
            fail(
                f"selector evidence worktree bytes を no-follow で読めない: {path}",
                "selector-evidence-bytes", exc,
            )
        if worktree != raw:
            fail(
                f"selector evidence bytes が H/worktree で不一致: {path}",
                "selector-evidence-bytes",
            )
        actual_sha = _sha256_hex(raw)
        if declared_sha256 is not None and declared_sha256 != actual_sha:
            fail(
                f"selector evidence 宣言 sha256 が H bytes と不一致: {path}",
                "selector-evidence-hash",
            )
        exempt[path] = actual_sha
        return raw

    predictions_raw = add_exempt(_SELECTOR_PREDICTIONS_PATH)
    try:
        prediction_document = _selector_freeze._parse_json_object(
            predictions_raw, source=f"{head}:{_SELECTOR_PREDICTIONS_PATH}",
        )
    except _selector_freeze.SelectorFreezeError as exc:
        fail(f"selector prediction strict parse 失敗: {exc}",
             "selector-declaration-invalid", exc)

    v1_raw = h_blob_100644(V1_FREEZE_PATH)
    if _sha256_hex(v1_raw) != V1_FREEZE_SHA256:
        fail("H tree の v1 freeze bytes が定数と不一致", "selector-declaration-invalid")
    try:
        v1 = _strict_load(v1_raw, what="selector basis v1 freeze")
        prediction_document, rows = _selector_freeze._validate_prediction_document_for_launch(
            prediction_document, freeze=v1,
        )
    except (RatifiedFreezeError, _selector_freeze.SelectorFreezeError) as exc:
        fail(f"selector prediction 構造/basis 検証失敗: {exc}",
             "selector-declaration-invalid", exc)

    pre_oracle_head = prediction_document["pre_oracle_head"]
    if not _git_ok(["merge-base", "--is-ancestor", pre_oracle_head, head], root):
        fail(
            "selector prediction pre_oracle_head が H の ancestor でない",
            "selector-declaration-invalid",
        )

    sources = prediction_document["sources"]
    if set(sources) != set(_SELECTOR_SOURCE_PATHS):
        fail("selector sources の name 集合が固定集合と不一致",
             "selector-declaration-invalid")
    for name, expected_path in _SELECTOR_SOURCE_PATHS.items():
        record = sources[name]
        if record["path"] != expected_path:
            fail(f"selector sources.{name}.path が固定 path と不一致",
                 "selector-evidence-path")
        entry = _selector_tree_entry(pre_oracle_head, expected_path, root)
        if entry is None:
            fail(
                f"selector source が pre_oracle_head にない: {expected_path}",
                "selector-evidence-missing",
            )
        assert entry is not None
        mode, _oid = entry
        if mode != "100644":
            fail(
                f"selector source の pre_oracle_head mode が 100644 でない: {expected_path}",
                "selector-evidence-mode",
            )
        source_raw = _blob_bytes(pre_oracle_head, expected_path, root)
        if _sha256_hex(source_raw) != record["sha256"]:
            fail(
                f"selector sources.{name}.sha256 が pre_oracle_head blob と不一致",
                "selector-evidence-hash",
            )

    def pre_oracle_blob_sha(path: str, *, label: str) -> str:
        entry = _selector_tree_entry(pre_oracle_head, path, root)
        if entry is None:
            fail(
                f"{label} が pre_oracle_head にない: {path}",
                "selector-evidence-missing",
            )
        assert entry is not None
        mode, _oid = entry
        if mode != "100644":
            fail(
                f"{label} の pre_oracle_head mode が 100644 でない: {path}",
                "selector-evidence-mode",
            )
        return _sha256_hex(_blob_bytes(pre_oracle_head, path, root))

    protocol_sha256 = pre_oracle_blob_sha(
        _SELECTOR_PROTOCOL_PATH, label="selector protocol",
    )
    parser_module_sha256 = pre_oracle_blob_sha(
        _SELECTOR_PARSER_PATH, label="selector parser module",
    )

    journal_raw = add_exempt(_SELECTOR_JOURNAL_PATH)
    try:
        records = _strict_jsonl(journal_raw)
        if not records:
            raise _prediction_runner.PredictionRunnerError("journal が空")
        _, _, targets = _selector_freeze._freeze_axes(v1)
        known_cells = frozenset((target, arm) for target in targets
                                for arm in _selector_freeze.ARMS)
        row_by_cell = {(row["target_holdout"], row["arm"]): row for row in rows}
        statuses = _prediction_runner.resolve_journal_for_launch(
            records,
            expected_header={
                "pre_oracle_head": pre_oracle_head,
                "protocol_sha256": protocol_sha256,
                "freeze_sha256": V1_FREEZE_SHA256,
                "role_file_sha256": sources["role"]["sha256"],
                "parser_module_sha256": parser_module_sha256,
            },
            known_cells=known_cells,
            prediction_rows_by_cell=row_by_cell,
        )
    except (RatifiedFreezeError, _prediction_runner.PredictionRunnerError) as exc:
        fail(f"selector journal 検証失敗: {exc}", "selector-declaration-invalid", exc)

    if set(row_by_cell) != known_cells:
        fail("selector rows の cell 集合が freeze axes と不一致",
             "selector-declaration-invalid")

    declared_paths = set(exempt)
    for cell in sorted(known_cells):
        row = row_by_cell[cell]
        status = statuses.get(cell)
        if status is None:
            fail(f"selector journal に cell がない: {cell!r}",
                 "selector-declaration-invalid")
        assert status is not None
        target, arm = cell
        if arm == "off":
            if status.kind != "static" or row["status"] != "valid":
                fail(f"selector journal/off row が不一致: {cell!r}",
                     "selector-declaration-invalid")
            continue
        claim = status.claim
        if claim is None:
            fail(f"selector agent cell に claim がない: {cell!r}",
                 "selector-declaration-invalid")
        expected_payload = f"{_SELECTOR_RUNS_DIR}/payload_{target}_{arm}.json"
        if (claim["payload_path"] != expected_payload
                or claim["input_payload_sha256"] != row["input_payload_sha256"]):
            fail(f"selector claim と row/payload path が不一致: {cell!r}",
                 "selector-declaration-invalid")

        if status.kind == "claimed_missing":
            if row["status"] != "missing":
                fail(f"selector missing journal/row が不一致: {cell!r}",
                     "selector-declaration-invalid")
        elif status.kind == "resolved":
            invocation = status.invocation
            assert invocation is not None
            expected_raw = f"{_SELECTOR_RUNS_DIR}/raw_{target}_{arm}.txt"
            if (row["status"] not in {"valid", "invalid"}
                    or invocation["status"] != row["status"]
                    or invocation["choice_id"] != row["choice_id"]
                    or invocation["rationale"] != row["rationale"]
                    or invocation["parser_error_code"] != row["parser_error_code"]
                    or invocation["receipt"] != row["agent_provenance"]
                    or invocation["raw_response_path"] != row["raw_response_path"]
                    or invocation["raw_sha256"] != row["raw_sha256"]
                    or row["raw_response_path"] != expected_raw):
                fail(f"selector invocation と prediction row が不一致: {cell!r}",
                     "selector-declaration-invalid")
            if expected_raw in declared_paths:
                fail(f"selector raw path が重複: {expected_raw}",
                     "selector-evidence-duplicate")
            add_exempt(expected_raw, declared_sha256=row["raw_sha256"])
            declared_paths.add(expected_raw)
        else:
            fail(f"selector journal cell status が不正: {cell!r}",
                 "selector-declaration-invalid")

        envelope = status.envelope
        if envelope is not None:
            expected_envelope = f"{_SELECTOR_RUNS_DIR}/envelope_{target}_{arm}.json"
            if envelope["envelope_path"] != expected_envelope:
                fail(f"selector envelope path が cell と不一致: {cell!r}",
                     "selector-evidence-path")
            if expected_envelope in declared_paths:
                fail(f"selector envelope path が重複: {expected_envelope}",
                     "selector-evidence-duplicate")
            add_exempt(
                expected_envelope,
                declared_sha256=envelope["envelope_sha256"],
            )
            declared_paths.add(expected_envelope)
        elif status.kind == "resolved":
            fail(f"resolved selector cell に envelope 宣言がない: {cell!r}",
                 "selector-declaration-invalid")
    return exempt


def _active_chain_exempt_exact(
        ratified: RatifiedFreeze, *, head: str, root: Path,
) -> Dict[str, str]:
    """H で再解決した active chain の exact record だけを scan 免除する。"""
    try:
        resolution = resolve_active_generation(root)
    except RatifiedFreezeError as exc:
        raise RatifiedFreezeError(
            "scan-exemption-invalid", f"active chain を再解決できない: {exc}",
            cause=exc.reason,
        ) from exc
    if (resolution.activation_head != head
            or resolution.generation_number != ratified.generation_number
            or resolution.generation_sha256 != ratified.sha256
            or resolution.generation_commit != ratified.generation_commit):
        raise RatifiedFreezeError(
            "scan-exemption-invalid", "RatifiedFreeze と H active chain が不一致",
            cause="active-chain-mismatch",
        )
    paths = {
        V1_FREEZE_PATH,
        resolution.generation_path,
        f"{APPROVAL_DIR}/{resolution.generation_sha256}.json",
        f"{ACTIVE_DIR}/{resolution.pointer_sha256}.json",
    }
    exempt: Dict[str, str] = {}
    namespace = {path: (mode, oid) for mode, oid, path in _list_namespace(head, root)}
    if not paths <= set(namespace):
        raise RatifiedFreezeError(
            "scan-exemption-invalid", f"active chain record が H namespace に無い: {sorted(paths-set(namespace))}",
            cause="exemption-missing",
        )
    for path in sorted(paths):
        mode, _oid = namespace[path]
        if mode not in ("100644", "100755"):
            raise RatifiedFreezeError(
                "scan-exemption-invalid", f"namespace exemption が regular でない: {path}",
                cause="exemption-mode",
            )
        raw = _blob_bytes(head, path, root)
        if _read_worktree_nofollow(root, path) != raw:
            raise RatifiedFreezeError(
                "scan-exemption-invalid", f"namespace exemption bytes が H/worktree で不一致: {path}",
                cause="exemption-bytes",
            )
        exempt[path] = _sha256_hex(raw)
    return exempt


def _resolve_current_contract_sha256(
        contract_sha256: str, *, expected_env_tag: Optional[str] = None,
) -> _env_contract.ExecutionEnvironmentContract:
    """live admission 用に recorded hash を current contract とのみ照合する。"""
    if not isinstance(expected_env_tag, str) or not expected_env_tag:
        raise _env_contract.EnvContractError("expected_env_tag が空でない文字列でない")
    contract = _env_contract.lookup(expected_env_tag)
    if contract.contract_sha256 != contract_sha256:
        raise _env_contract.EnvContractError(
            "記録 contract_sha256 が current contract と不一致"
        )
    return contract


def _resolve_historical_contract_sha256(
        contract_sha256: str, *, expected_env_tag: Optional[str] = None,
) -> _env_contract.ExecutionEnvironmentContract:
    """recorded hash を production historical resolver で一意解決する。"""
    entry = _env_contract.resolve_by_contract_sha256(
        contract_sha256, expected_env_tag=expected_env_tag,
    )
    if type(entry) is not _env_contract.GenerationEntry:
        raise _env_contract.EnvContractError(
            "contract resolver が exact GenerationEntry を返さなかった"
        )
    contract = entry.contract
    if (contract.env_tag != expected_env_tag
            or contract.contract_sha256 != contract_sha256):
        raise _env_contract.EnvContractError(
            "contract resolver の返却 entry が記録 env/hash と不一致"
        )
    return contract


def _validate_published_protocol(
        document: Mapping, *,
        contract_resolver: Callable[..., _env_contract.ExecutionEnvironmentContract],
) -> Tuple[dict, _env_contract.ExecutionEnvironmentContract]:
    """protocol を検証し、記録 hash を一度だけ解決した contract と対で返す。"""
    resolved: List[_env_contract.ExecutionEnvironmentContract] = []

    def contract_sha256_lookup(env_tag: str) -> str:
        if resolved:
            raise _env_contract.EnvContractError(
                "artifact の contract_sha256 resolver が複数回呼ばれた"
            )
        contract = contract_resolver(
            document["contract_sha256"], expected_env_tag=env_tag,
        )
        if type(contract) is not _env_contract.ExecutionEnvironmentContract:
            raise _env_contract.EnvContractError(
                "contract resolver が exact ExecutionEnvironmentContract を返さなかった"
            )
        if (contract.env_tag != env_tag
                or contract.contract_sha256 != document["contract_sha256"]):
            raise _env_contract.EnvContractError(
                "contract resolver の返却 entry が記録 env/hash と不一致"
            )
        resolved.append(contract)
        return contract.contract_sha256

    protocol = _floor_contract.validate_protocol(
        document, contract_sha256_lookup=contract_sha256_lookup,
    )
    if len(resolved) != 1:
        raise _floor_contract.FloorContractError(
            "protocol contract が一度だけ解決されなかった"
        )
    return protocol, resolved[0]


def _launch_validate(
        ratified: RatifiedFreeze, root=ROOT, *,
        contract_resolver: Callable[..., _env_contract.ExecutionEnvironmentContract],
        result_type: Type[LaunchValidatedFreeze] | Type[ReverifiedFreeze],
) -> LaunchValidatedFreeze | ReverifiedFreeze:
    """§8.4 の全 binding graph と未知性層2を通す full validation core。

    reason 優先順は §2.8 固定: (1) 引数型/HEAD、(2) generation==1、(3) path・
    存在・mode・strict parse、(4) semantic、(5) binding、(6) lineage、(7) exact
    exemption (active-chain + selector evidence)、(8) occurrence/union/full scan。cert raw hit は到達可能性を保つため cert
    schema より先に検査する。

    保証境界: cert C の一意導入・非 merge・C<G、result / measurement_closure の
    各 path の一意導入・非 merge・I_entry ⊆ [C, G] (DAG 上の祖先関係、同一を含む)、
    世代文書 path の導入集合 {G} は捕捉済み H 内の記録順だけを保証する。
    上限 i ≤ G は段階 3 の G-tree 実在検査と一意導入から従う重複検査で独立保証に数えない。
    実時間順・履歴再構成への耐性・cert 発行と result 走行の実時間順は保証しない。
    floor_protocol/journal/manifest は raw hash・semantic consistency・G/H/worktree endpoint を検査するが、
    導入 commit や C 後の append chronology を課さない (裁定どおり)。

    TOCTOU は component lstat + leaf O_NOFOLLOW、一度捕捉した小 artifact の scan 後再読で
    縮小する。full repository content hash は行わないため、その他の同名 file 内容交換には
    single-tenant 前提が残る。
    """
    root = Path(root)
    if not isinstance(ratified, RatifiedFreeze):
        raise RatifiedFreezeError(
            "floor-artifact-invalid", "ratified が RatifiedFreeze でない", cause="argument-type",
        )
    head = _capture_head(root)
    if head != ratified.activation_head:
        raise RatifiedFreezeError(
            "activation-head-moved",
            f"HEAD ({head}) が ratified.activation_head ({ratified.activation_head}) と不一致",
        )
    if ratified.generation_number != 1:
        raise RatifiedFreezeError(
            "certificate-generation-scope", "launch certificate は generation_number==1 専用",
        )

    # --- 3: path / G-H-worktree capture / raw cert hit / strict parse ---
    gen_commit = ratified.generation_commit
    protocol_path, protocol_record_sha = _source_record_path_sha(
        ratified.document, "floor_protocol",
    )
    result_path, result_record_sha = _source_record_path_sha(ratified.document, "floor_source")
    _assert_canonical_relative_path(
        protocol_path, reason="floor-artifact-invalid", label="floor_protocol.path",
    )
    _assert_canonical_relative_path(
        result_path, reason="floor-artifact-invalid", label="floor_source.path",
    )
    try:
        result_path_info = _parse_official_run_path(result_path, expected_basename="result.json")
    except _LaunchCertError as exc:
        raise RatifiedFreezeError(
            "floor-artifact-invalid", f"result official path が不正: {exc}", cause="result-path",
        ) from exc
    run_dir = result_path.rsplit("/", 1)[0]
    role_paths = {
        role: f"{run_dir}/{basename}" for role, basename in _RUN_BASENAMES.items()
    }
    role_paths["result"] = result_path
    for role, path in role_paths.items():
        _assert_canonical_relative_path(
            path, reason="floor-artifact-invalid", label=f"{role}.path",
        )

    closure_entries = _closure_entries(ratified.document)
    measurement = [(path, sha) for kind, path, sha in closure_entries
                   if kind == "measurement_closure"]
    dedicated = {
        protocol_path, result_path, role_paths["cert"], role_paths["journal"],
        role_paths["manifest"], _gen_path(ratified.generation_number),
    }
    for path, _sha in measurement:
        if path in dedicated or path.startswith(FREEZE_DIR + "/"):
            raise RatifiedFreezeError(
                "closure-role-conflict", f"measurement_closure path が専用 role と衝突: {path}",
            )
    if len(dedicated) != 6:
        raise RatifiedFreezeError("closure-role-conflict", "bound artifact role path が衝突")

    bound_paths = [protocol_path, *role_paths.values(), *[path for path, _ in measurement]]
    captured: Dict[str, bytes] = {}
    captured_modes: Dict[str, str] = {}
    for path in dict.fromkeys(bound_paths):
        raw, mode = _capture_g_h_worktree(
            generation_commit=gen_commit, validation_head=head, path=path, root=root,
        )
        captured[path] = raw
        captured_modes[path] = mode
    if _sha256_hex(captured[protocol_path]) != protocol_record_sha:
        raise RatifiedFreezeError(
            "floor-artifact-invalid", "floor_protocol raw hash が generation record と不一致",
            cause="protocol-record-sha",
        )
    if _sha256_hex(captured[result_path]) != result_record_sha:
        raise RatifiedFreezeError(
            "floor-artifact-invalid", "floor_source raw hash が generation record と不一致",
            cause="result-record-sha",
        )
    for path, expected_sha in measurement:
        if _sha256_hex(captured[path]) != expected_sha:
            raise RatifiedFreezeError(
                "floor-artifact-invalid", f"measurement_closure sha が不一致: {path}",
                cause="closure-record-sha",
            )
        _closure_text(captured[path])  # UTF-8/no-NUL を fail-closed で強制。

    cert_raw = captured[role_paths["cert"]]
    try:
        cert_text = cert_raw.decode("utf-8", "strict")
    except UnicodeError as exc:
        raise RatifiedFreezeError(
            "floor-artifact-invalid", "cert が UTF-8 でない", cause="cert-utf8",
        ) from exc
    cert_hits = _hf.holdout_conjunction_hits({role_paths["cert"]: cert_text})
    if any(cert_hits.values()):
        raise RatifiedFreezeError(
            "floor-artifact-invalid", "hits(cert) が空でない", cause="certificate-holdout-hit",
        )

    protocol_doc = _strict_load(captured[protocol_path], what="floor_protocol")
    cert_doc = _strict_load(cert_raw, what="launch certificate")
    manifest_doc = _strict_load(captured[role_paths["manifest"]], what="manifest")
    result_doc = _strict_load(captured[result_path], what="floor result")
    journal_records = _strict_jsonl(captured[role_paths["journal"]])

    # --- 4: semantic validation ---
    try:
        protocol, contract = _validate_published_protocol(
            protocol_doc, contract_resolver=contract_resolver,
        )
    except (_floor_contract.FloorContractError, _env_contract.EnvContractError) as exc:
        raise RatifiedFreezeError(
            "floor-artifact-invalid", f"floor protocol full validation 失敗: {exc}",
            cause="protocol-invalid",
        ) from exc
    protocol_sha = _floor_contract.canonical_protocol_sha256(protocol)
    if protocol["freeze"] != {"path": V1_FREEZE_PATH, "sha256": V1_FREEZE_SHA256}:
        raise RatifiedFreezeError(
            "binding-chain-mismatch", "protocol.freeze が v1 trust root と不一致",
            cause="protocol-freeze",
        )
    try:
        cert = _validate_launch_certificate(
            cert_doc, expected_v1_freeze_sha256=V1_FREEZE_SHA256,
            expected_protocol_sha256=protocol_sha,
            expected_run_id=result_path_info["run_id"],
        )
    except _LaunchCertError as exc:
        raise RatifiedFreezeError(
            "binding-chain-mismatch", f"launch certificate invalid: {exc}",
            cause="certificate-invalid",
        ) from exc
    expected_admission_policy = (
        resolve_current_build_admission_policy()
        if result_type is LaunchValidatedFreeze else None
    )
    validated_manifest = _validate_manifest(
        manifest_doc, protocol=protocol, protocol_sha256=protocol_sha, ratified=ratified,
        expected_policy=expected_admission_policy,
    )
    cells, schedule, binaries = validated_manifest
    expected_use_perf = validated_manifest.expected_use_perf
    expected_perf_preflight = manifest_doc.get("perf_preflight")
    expected_perf_observation = manifest_doc.get("perf_observation")
    cert_sha = _sha256_hex(cert_raw)
    manifest_sha = _sha256_hex(captured[role_paths["manifest"]])
    journal = _validate_journal(
        journal_records, protocol=protocol, schedule=schedule, cells=cells,
        binaries=binaries, cert_sha256=cert_sha, manifest_sha256=manifest_sha,
        root=root, contract=contract, expected_use_perf=expected_use_perf,
    )
    expected_floor_protocol = _floor_contract.project_protocol_for_floor_artifact(protocol)
    # cells は ratified freeze から独立導出・manifest と exact 照合済みであり、
    # result の自己申告集合を期待値へ流用しない。
    expected_floor_protocol["expected_cells"] = (
        _floor_contract.expected_cells_from_cells(cells)
    )
    # 共有 verifier の汎用 floor-projection より、ratified 固有の
    # schema-keys を優先する。通過後も共有 verifier 自体は必ず実行する。
    _validate_result_top_level_keys(
        result_doc, expected_use_perf=expected_use_perf,
        expected_perf_preflight=expected_perf_preflight,
        expected_perf_observation=expected_perf_observation,
    )
    from .s8b_holdout_admission import FloorHoldoutEvidenceError
    try:
        admission_problems = _floor_stats.verify_floor_artifact_with_live_admission(
            result_doc, expected_floor_protocol,
            expected_binaries=journal["receipts"], repo_root=root,
            protocol=protocol, verified_freeze_document=ratified.document,
            freeze_sha256=V1_FREEZE_SHA256, manifest_sha256=manifest_sha,
            campaign_run_id=result_path_info["run_id"],
            run_relpath=run_dir.removeprefix("output/"), mode="official",
            cells=cells, schedule=schedule,
            sessions=[
                record for record in journal["records"]
                if record.get("event") in {"session-start", "session"}
            ],
            expected_use_perf=expected_use_perf,
        )
    except FloorHoldoutEvidenceError as exc:
        reason = (
            "floor-admission-unverifiable"
            if exc.category == "unverifiable"
            else "floor-admission-mismatch"
        )
        raise RatifiedFreezeError(
            reason, f"floor admission evidence 検査に失敗: {exc.reason}",
            cause=exc.reason,
        ) from exc
    if admission_problems:
        if any("holdout_admission" in problem for problem in admission_problems):
            raise RatifiedFreezeError(
                "floor-admission-mismatch", admission_problems[0],
                cause="artifact-receipt-mismatch",
            )
        raise RatifiedFreezeError(
            "floor-artifact-invalid",
            f"verify_floor_artifact_with_live_admission: {admission_problems[0]}",
            cause="floor-projection",
        )
    _validate_result(
        result_doc, protocol=protocol, cells=cells, binaries=binaries, journal=journal,
        contract=contract, expected_use_perf=expected_use_perf,
        expected_perf_preflight=expected_perf_preflight,
        expected_perf_observation=expected_perf_observation,
    )
    if result_type is LaunchValidatedFreeze:
        try:
            _hf._assert_floor_selection_identity(  # noqa: SLF001
                root=root, selected_rel=result_path,
                selected_path_info=result_path_info, protocol=protocol,
                v1=ratified.document,
            )
        except _hf.FreezeError as exc:
            detail = str(exc)
            if detail.startswith("floor-selection-eligibility-underivable:"):
                reason = "floor-selection-eligibility-underivable"
                cause = detail
            elif detail.startswith("floor-selection-rule-mismatch:"):
                reason = "floor-selection-rule-mismatch"
                cause = _hf._FLOOR_SELECTION_RULE_VERSION  # noqa: SLF001
            else:
                reason = "floor-selection-unverifiable"
                cause = detail
            raise RatifiedFreezeError(reason, detail, cause=cause) from exc

    # --- 5: §8.4 binding graph (adjacency list の全辺) ---
    wall_campaigns = [row for row in result_doc["wall_ledger"]
                      if row.get("event") == "campaign-start"]
    if len(wall_campaigns) != 1:
        raise RatifiedFreezeError(
            "binding-chain-mismatch", "result.wall_ledger campaign-start が一意でない",
            cause="wall-ledger-campaign",
        )
    try:
        cert_second = dt.datetime.fromisoformat(
            cert["started_utc"][:-1] + "+00:00"
            if cert["started_utc"].endswith("Z") else cert["started_utc"]
        ).astimezone(dt.timezone.utc).replace(microsecond=0).isoformat()
    except (TypeError, ValueError) as exc:
        raise RatifiedFreezeError(
            "binding-chain-mismatch", "cert.started_utc を正規化できない",
            cause="cert-started-utc",
        ) from exc
    path_second = result_path_info["ts"].astimezone(dt.timezone.utc).isoformat()
    equality_nodes = {
        "P": protocol_sha,
        "result.protocol_sha256": result_doc["protocol_sha256"],
        "journal.campaign-start.protocol_sha256": journal["campaign"]["protocol_sha256"],
        "cert.protocol_sha256": cert["protocol_sha256"],
        "manifest.protocol_sha256": manifest_doc["protocol_sha256"],
        "P[:8]": protocol_sha[:8],
        "official-path.proto8": result_path_info["proto8"],
        "V1_FREEZE_SHA256": V1_FREEZE_SHA256,
        "result.freeze_sha256": result_doc["freeze_sha256"],
        "journal.campaign-start.freeze_sha256": journal["campaign"]["freeze_sha256"],
        "cert.v1_freeze_sha256": cert["v1_freeze_sha256"],
        "protocol.freeze.sha256": protocol["freeze"]["sha256"],
        "manifest.freeze_sha256": manifest_doc["freeze_sha256"],
        "manifest.freeze.sha256": manifest_doc["freeze"]["sha256"],
        "V1_FREEZE_PATH": V1_FREEZE_PATH,
        "protocol.freeze.path": protocol["freeze"]["path"],
        "manifest.freeze.path": manifest_doc["freeze"]["path"],
        "sha256(manifest.raw)": manifest_sha,
        "result.manifest_sha256": result_doc["manifest_sha256"],
        "journal.campaign-start.manifest_sha256": journal["campaign"]["manifest_sha256"],
        "sha256(cert.raw)": cert_sha,
        "journal.launch-start.launch_certificate_sha256":
            journal["launch"]["launch_certificate_sha256"],
        "journal.campaign-start.launch_certificate_sha256":
            journal["campaign"]["launch_certificate_sha256"],
        "result.wall_ledger[campaign-start].launch_certificate_sha256":
            wall_campaigns[0]["launch_certificate_sha256"],
        "journal[event=session]": _plain_json(journal["sessions"]),
        "result.sessions": result_doc["sessions"],
        "result.binaries": result_doc["binaries"],
        "manifest.binaries": manifest_doc["binaries"],
        "generation.env_tag": ratified.document["env_tag"],
        "official-path.env_tag": result_path_info["env_tag"],
        "protocol.env_tag": protocol["env_tag"],
        "result.env_tag": result_doc["env_tag"],
        "manifest.env_tag": manifest_doc["env_tag"],
        "journal.campaign-start.execution_receipt.env_tag":
            journal["campaign"]["execution_receipt"]["env_tag"],
        "protocol.contract_sha256": protocol["contract_sha256"],
        "journal.campaign-start.execution_receipt.contract_sha256":
            journal["campaign"]["execution_receipt"]["contract_sha256"],
        "official-path.run_id.ts": path_second,
        "cert.started_utc(second)": cert_second,
        "cert.started_utc": cert["started_utc"],
        "journal.launch-start.utc": journal["launch"]["utc"],
        "sha256(result.raw)": _sha256_hex(captured[result_path]),
        "generation.floor_source.sha256": result_record_sha,
    }
    _assert_equality_adjacency(equality_nodes)

    if result_path_info["proto8"] != protocol_sha[:8]:
        raise RatifiedFreezeError(
            "binding-chain-mismatch", "official path proto8 != P[:8]", cause="path-proto8",
        )
    if ratified.document.get("env_tag") != result_path_info["env_tag"] \
            or result_path_info["env_tag"] != protocol["env_tag"]:
        raise RatifiedFreezeError(
            "binding-chain-mismatch", "generation/path/protocol env が不一致", cause="env-chain",
        )
    if manifest_doc["protocol_sha256"] != protocol_sha \
            or result_doc["protocol_sha256"] != protocol_sha \
            or cert["protocol_sha256"] != protocol_sha:
        raise RatifiedFreezeError(
            "binding-chain-mismatch", "protocol hash chain が不一致", cause="protocol-chain",
        )
    if (manifest_doc["freeze_sha256"] != V1_FREEZE_SHA256
            or manifest_doc["freeze"] != protocol["freeze"]
            or result_doc["freeze_sha256"] != V1_FREEZE_SHA256
            or journal["campaign"]["freeze_sha256"] != V1_FREEZE_SHA256):
        raise RatifiedFreezeError(
            "binding-chain-mismatch", "freeze hash/path chain が不一致", cause="freeze-chain",
        )
    if result_doc["manifest_sha256"] != manifest_sha:
        raise RatifiedFreezeError(
            "binding-chain-mismatch", "result.manifest_sha256 != sha256(manifest.raw)",
            cause="manifest-chain",
        )
    if journal["launch"]["launch_certificate_sha256"] != cert_sha \
            or journal["campaign"]["launch_certificate_sha256"] != cert_sha:
        raise RatifiedFreezeError(
            "binding-chain-mismatch", "cert raw hash chain が不一致", cause="cert-chain",
        )
    if journal["launch"]["utc"] != cert["started_utc"]:
        raise RatifiedFreezeError(
            "binding-chain-mismatch", "launch-start.utc != cert.started_utc",
            cause="launch-time-chain",
        )
    receipt = journal["campaign"]["execution_receipt"]
    if (receipt["env_tag"] != protocol["env_tag"]
            or receipt["contract_sha256"] != protocol["contract_sha256"]):
        raise RatifiedFreezeError(
            "binding-chain-mismatch", "execution receipt env/contract chain が不一致",
            cause="receipt-chain",
        )
    if result_doc["binaries"] != manifest_doc["binaries"]:
        raise RatifiedFreezeError(
            "binding-chain-mismatch", "result.binaries != manifest.binaries",
            cause="binaries-chain",
        )

    verified_floor = VerifiedFloorArtifact(
        path=result_path, raw_bytes=captured[result_path], sha256=result_record_sha,
        document=_deep_freeze(result_doc),
    )

    # --- 6: lineage (journal/manifest の introduction 条件は意図的に課さない) ---
    graph = _commit_graph(head, root)
    _cert_mode, cert_oid = _tree_mode_oid(head, role_paths["cert"], root)
    cert_intro = _immutable_introductions(graph, role_paths["cert"], cert_oid, root)
    cert_commit = _unique_introduction(cert_intro, role_paths["cert"])
    if len(graph.parents.get(cert_commit, ())) > 1:
        raise RatifiedFreezeError("binding-chain-mismatch", "cert introduction が merge", cause="cert-merge")
    if cert_commit == gen_commit or not _git_ok(
            ["merge-base", "--is-ancestor", cert_commit, gen_commit], root):
        raise RatifiedFreezeError(
            "binding-chain-mismatch", "cert C が G の厳密祖先でない", cause="cert-lineage",
        )
    for path in [result_path, *[path for path, _ in measurement]]:
        _mode, oid = _tree_mode_oid(head, path, root)
        _assert_artifact_introduction_interval(
            graph, path, oid, cert_commit=cert_commit, gen_commit=gen_commit, root=root,
        )
    generation_path = _gen_path(ratified.generation_number)
    _mode, generation_oid = _tree_mode_oid(head, generation_path, root)
    introductions = _immutable_introductions(graph, generation_path, generation_oid, root)
    if set(introductions) != {gen_commit}:
        raise RatifiedFreezeError(
            "binding-chain-mismatch", f"{generation_path} の introduction set != {{G}}",
            cause="generation-introduction",
        )

    # --- 7: verified exact exemption ---
    _assert_no_untracked_symlink(root)
    active_exempt = _active_chain_exempt_exact(ratified, head=head, root=root)
    selector_exempt = _selector_evidence_exempt_exact(head=head, root=root)
    overlap = set(active_exempt) & set(selector_exempt)
    if overlap:
        raise RatifiedFreezeError(
            "scan-exemption-invalid",
            f"active-chain と selector evidence exemption が衝突: {sorted(overlap)}",
            cause="selector-evidence-duplicate",
        )
    exempt_exact = {**active_exempt, **selector_exempt}

    # --- 8: occurrence / expected union / full scan ---
    closure_paths = frozenset(path for path, _ in measurement)
    occurrence_artifacts: List[Tuple[str, object, Optional[bytes]]] = [
        (protocol_path, protocol_doc, captured[protocol_path]),
        (result_path, result_doc, captured[result_path]),
        (role_paths["journal"], journal_records, captured[role_paths["journal"]]),
        (role_paths["manifest"], manifest_doc, captured[role_paths["manifest"]]),
    ]
    for path, _sha in measurement:
        occurrence_artifacts.append((path, None, captured[path]))
    expected_hits = _validate_axis_occurrences(
        artifacts=occurrence_artifacts, protocol=protocol, binaries=binaries,
        contract=contract, expected_use_perf=expected_use_perf,
        closure_paths=closure_paths,
    )

    digest_before = _enumeration_digest(root)
    try:
        report = _hf.search_repository(root, exempt_exact=exempt_exact)
    except _hf.FreezeError as exc:
        raise RatifiedFreezeError(
            "scan-exemption-invalid", f"repository scan を完遂できない: {exc}",
            cause="scan-failed",
        ) from exc
    digest_after = _enumeration_digest(root)
    if digest_before != digest_after:
        raise RatifiedFreezeError(
            "enumeration-shifted", "search 前後で列挙集合の digest が変化 (走査中の追加の疑い)"
        )
    _assert_search_operational(report)

    # per-holdout の完全一致 (C2-4)。closure 外の新規 hit / 導出されたのに現れない hit で fail。
    for name in _hf.HOLDOUTS:
        current = set(report["holdouts"][name]["conjunction_hits"])
        expected = set(expected_hits.get(name, []))
        if current != expected:
            undeclared = sorted(current - expected)
            missing = sorted(expected - current)
            raise RatifiedFreezeError(
                "closure-hit-mismatch",
                f"{name}: 現 hit が closure 導出と不一致 "
                f"(未申告={undeclared} 消失={missing})",
            )

    # 小さい bound artifact を scan 後に no-follow で再捕捉し、内容交換窓を縮小する。
    for path, before in captured.items():
        after = _read_worktree_nofollow(root, path)
        after_stat = (root / path).lstat()
        after_mode = "100755" if after_stat.st_mode & 0o111 else "100644"
        if after != before or after_mode != captured_modes[path]:
            raise RatifiedFreezeError(
                "floor-artifact-invalid", f"scan 前後で bound artifact が変化: {path}",
                cause="artifact-toctou",
            )

    inventory = _symlink_gitlink_inventory(head, root)
    return result_type(
        ratified=ratified,
        activation_head=head,
        search_digest=digest_after,
        validation_root=Path(root).resolve(),
        search_report=_deep_freeze(report),
        symlink_gitlink_inventory=inventory,
        floor_artifact=verified_floor,
        binaries_by_cell=_deep_freeze(binaries),
    )


def launch_validate(ratified: RatifiedFreeze, root=ROOT) -> LaunchValidatedFreeze:
    """current contract に束縛した live 実走 admission を行う。"""
    validated = _launch_validate(
        ratified, root, contract_resolver=_resolve_current_contract_sha256,
        result_type=LaunchValidatedFreeze,
    )
    assert type(validated) is LaunchValidatedFreeze
    return validated


def assert_g1_floor_selection_identity(
        ratified: RatifiedFreeze, root=ROOT,
) -> None:
    """g1 の批准床値に選択規則だけを再強制する。

    g2 以降の選択・投影は未定義のため、非 g1 は観測せずに返る。
    protocol は generation commit に記録された contract で解決し、
    activation HEAD・build policy・closure・live scan はこの境界では検査しない。
    """
    if type(ratified) is not RatifiedFreeze:
        raise RatifiedFreezeError(
            "floor-artifact-invalid", "ratified が RatifiedFreeze でない",
            cause="argument-type",
        )
    if ratified.generation_number != 1:
        return

    root = Path(root)
    try:
        protocol_path, protocol_record_sha = _source_record_path_sha(
            ratified.document, "floor_protocol",
        )
        selected_rel, _selected_record_sha = _source_record_path_sha(
            ratified.document, "floor_source",
        )
        _assert_canonical_relative_path(
            protocol_path, reason="floor-selection-unverifiable",
            label="floor_protocol.path",
        )
        _assert_canonical_relative_path(
            selected_rel, reason="floor-selection-unverifiable",
            label="floor_source.path",
        )
        selected_path_info = _parse_official_run_path(
            selected_rel, expected_basename="result.json",
        )
        protocol_raw = _blob_at_or_fail(
            ratified.generation_commit, protocol_path, root,
            reason="floor-selection-unverifiable",
        )
        if _sha256_hex(protocol_raw) != protocol_record_sha:
            raise RatifiedFreezeError(
                "floor-selection-unverifiable",
                "floor_protocol raw hash が generation record と不一致",
                cause="protocol-record-sha",
            )
        protocol_doc = _strict_load(protocol_raw, what="floor_protocol")
        protocol, _contract = _validate_published_protocol(
            protocol_doc, contract_resolver=_resolve_historical_contract_sha256,
        )
        protocol_sha = _floor_contract.canonical_protocol_sha256(protocol)
        if selected_path_info["proto8"] != protocol_sha[:8]:
            raise RatifiedFreezeError(
                "floor-selection-unverifiable",
                "official path proto8 が記録 protocol hash と不一致",
                cause="selection-path-proto8",
            )
        if (ratified.document.get("env_tag") != selected_path_info["env_tag"]
                or selected_path_info["env_tag"] != protocol["env_tag"]):
            raise RatifiedFreezeError(
                "floor-selection-unverifiable",
                "generation/path/protocol env が不一致",
                cause="selection-env-chain",
            )
    except RatifiedFreezeError as exc:
        if exc.reason == "floor-selection-unverifiable":
            raise
        raise RatifiedFreezeError(
            "floor-selection-unverifiable",
            f"選択規則の入力を解決できない: {exc}", cause=exc.reason,
        ) from exc
    except (
        _LaunchCertError, _floor_contract.FloorContractError,
        _env_contract.EnvContractError, KeyError, TypeError, ValueError,
    ) as exc:
        raise RatifiedFreezeError(
            "floor-selection-unverifiable",
            f"選択規則の入力を解決できない: {exc}", cause=str(exc),
        ) from exc

    try:
        _hf._assert_floor_selection_identity(  # noqa: SLF001
            root=root, selected_rel=selected_rel,
            selected_path_info=selected_path_info, protocol=protocol,
            v1=ratified.document,
        )
    except _hf.FreezeError as exc:
        detail = str(exc)
        if detail.startswith("floor-selection-eligibility-underivable:"):
            reason = "floor-selection-eligibility-underivable"
            cause = detail
        elif detail.startswith("floor-selection-rule-mismatch:"):
            reason = "floor-selection-rule-mismatch"
            cause = _hf._FLOOR_SELECTION_RULE_VERSION  # noqa: SLF001
        else:
            reason = "floor-selection-unverifiable"
            cause = detail
        raise RatifiedFreezeError(reason, detail, cause=cause) from exc


def reverify_published_freeze(
        ratified: RatifiedFreeze, root=ROOT,
) -> ReverifiedFreeze:
    """記録 contract hash の世代で publish 済み freeze を read-only 再検証する。"""
    reverified = _launch_validate(
        ratified, root,
        contract_resolver=_resolve_historical_contract_sha256,
        result_type=ReverifiedFreeze,
    )
    assert type(reverified) is ReverifiedFreeze
    return reverified


def _closure_text(blob: bytes) -> str:
    """closure blob は UTF-8/no-NUL に限定する (binary closure は未裁定のため fail-closed)。"""
    if b"\0" in blob:
        raise RatifiedFreezeError("closure-nontext", "closure blob が NUL を含む")
    try:
        return blob.decode("utf-8")
    except UnicodeError as exc:
        raise RatifiedFreezeError("closure-nontext", "closure blob が UTF-8 でない") from exc
