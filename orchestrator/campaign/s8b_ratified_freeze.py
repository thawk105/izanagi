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

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from campaign.s8b_holdout_freeze import TOP_LEVEL_KEYS as V1_TOP_LEVEL_KEYS

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


# ---------------------------------------------------------------------------
# 例外 (単一型 + 構造化 reason code)
# ---------------------------------------------------------------------------

class RatifiedFreezeError(RuntimeError):
    """承認束縛検証の fail-closed 拒否。``reason`` に構造化 reason code を持つ。"""

    def __init__(self, reason: str, detail: str = "") -> None:
        self.reason = reason
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
    """`AI-Agent: none` を逐語で持つ人間 commit か (C1-6 の二重判定)。

    parse 上の AI-Agent 値が厳密に ["none"] であり、かつ raw message に行として
    byte-for-byte `AI-Agent: none` がちょうど 1 本存在し他に AI-Agent 系行が無い。"""
    message = _commit_message(commit, root)
    raw_lines = _raw_ai_agent_lines(message)
    if len(raw_lines) != 1 or raw_lines[0] != "AI-Agent: none":
        return False
    return _parsed_ai_agent_values(message, root) == ["none"]


def _assert_user_commit(commit: str, graph: _CommitGraph, root: Path) -> None:
    """approval/pointer/revocation/cancellation の導入 commit 検証 (C1-6)。

    非 merge かつ `AI-Agent: none` 逐語かつ H ancestry。満たさない record の存在は
    「無視」でなく検証エラー (fail-closed)。"""
    if len(graph.parents.get(commit, ())) > 1:
        raise RatifiedFreezeError("user-commit-merge", f"user commit {commit} が merge")
    if not _is_none_commit(commit, root):
        raise RatifiedFreezeError(
            "user-commit-trailer", f"commit {commit} が `AI-Agent: none` 逐語でない"
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


def _added_paths(commit: str, root: Path) -> Tuple[frozenset, Tuple[Tuple[str, str], ...]]:
    """非 merge commit の diff-tree name-status から (追加 path 集合, 非追加 (status,path))。"""
    out = _git_text(["diff-tree", "--no-commit-id", "--name-status", "-r", commit], root)
    added: set = set()
    other: List[Tuple[str, str]] = []
    for line in out.splitlines():
        status, _, path = line.partition("\t")
        if status == "A":
            added.add(path)
        else:
            other.append((status, path))
    return frozenset(added), tuple(other)


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


@dataclass(frozen=True)
class LegacyFreeze:
    """v1 単一 filename freeze の型 (C2-5)。bytes 定数照合 + strict parse のみ。

    v1 の source/head 再検証はしない — frozen_at_head は履歴書換えで dangling
    (§5-viii)。RatifiedFreeze とは別型で、consumer が誤って v2 実走経路へ流せない。"""
    document: Mapping
    sha256: str


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


def _verify_generation_semantics(document: Mapping, resolution: "ActiveResolution", root: Path) -> None:
    """世代 document の**内容**検証の拡張点 (W3 が実装)。

    本レーン (RV-core) は record/連鎖/承認 machinery のみを所有し、ここは意図的に
    no-op で残す。W3 (RV-verify) が source blob 照合・未知性 closure・transition table・
    frozen_at_head (G^ 一致) の中身検証をここへ差し込む。fail-open ではない — 承認
    連鎖・active 判定 (structural) は resolve_active_generation で既に fail-closed 済みで、
    ここは内容の追加ゲートを重ねる seam である。"""
    return None


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
    """approval と active pointer が同一 commit A で導入され、A の diff がこの 2 record の
    追加のみであること (C1-4)。G ≠ A も検査する。"""
    if approval.intro != pointer.intro:
        raise RatifiedFreezeError(
            "pairing-commit",
            f"approval と pointer の導入 commit 不一致: {approval.intro} vs {pointer.intro}",
        )
    commit_a = approval.intro
    if commit_a == generation.commit:
        raise RatifiedFreezeError(
            "generation-approval-same-commit",
            f"世代導入 commit G と approval commit A が同一: {commit_a}",
        )
    added, other = _added_paths(commit_a, root)
    if added != frozenset({approval.path, pointer.path}) or other:
        raise RatifiedFreezeError(
            "approval-commit-diff",
            f"approval commit {commit_a} の diff が {{approval, pointer}} の追加のみでない: "
            f"added={sorted(added)} other={list(other)}",
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
