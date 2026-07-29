#!/usr/bin/env python3
"""AI 作業 provenance の commit trailer を決定的に監査する。

既定では docs/ai-provenance.md を最初に追加した commit から HEAD までを検査する。
任意範囲は --range、commit 前の message は --message-file で検査できる。
hook には配線しない。Izanagi の hook 2 本限定を維持しつつ、欠落を明示的に監査するための
独立した lint である。
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
POLICY_PATH = "docs/ai-provenance.md"
ROLES = ("author", "reviewer", "researcher", "manager", "integrator")
IDENT = r"[a-z0-9][a-z0-9._-]*"
RESERVED_PRODUCTS = {"none", "unknown", "not-exposed", "human"}
IMPLEMENTATION_POLICY_NEEDLE = (
    "実装面を変更する AI 関与 commit は Codex author を必須"
)
CO_AUTHORED_BY_POLICY_NEEDLE = (
    "Co-Authored-By 候補行はすべて最終 trailer block に置く"
)
IMPLEMENTATION_PREFIXES = (
    "orchestrator/", "tools/", "hooks/", ".github/", ".codex/", "external/",
)
IMPLEMENTATION_SUFFIXES = (
    ".py", ".sh", ".bash", ".c", ".cc", ".cpp", ".cxx",
    ".h", ".hh", ".hpp", ".hxx", ".cmake", ".patch", ".diff",
)
IMPLEMENTATION_BASENAMES = {
    "CMakeLists.txt", "Makefile", "GNUmakefile", "pyproject.toml",
}
AGENT_VALUE = re.compile(
    rf"^product=(?P<product>{IDENT}); "
    rf"model=(?P<model>{IDENT}); "
    rf"reasoning=(?P<reasoning>{IDENT}); "
    rf"role=(?P<role>{'|'.join(ROLES)})"
    rf"(?:; scope=(?P<scope>{IDENT}))?$"
)
RAW_CO_AUTHORED_BY = re.compile(
    r"^[ \t]*Co-Authored-By[ \t]*:", re.IGNORECASE | re.MULTILINE
)
CORRECTION_KEY = "AI-Agent-Correction"
RAW_AI_AGENT_CORRECTION = re.compile(
    rf"^[ \t]*{re.escape(CORRECTION_KEY)}[ \t]*:"
    r"(?P<value>[^\r\n]*)\r?$",
    re.IGNORECASE | re.MULTILINE,
)
TRAILER_PARSE_TEMP_ROOT: Path | None = None
_REPO_DISCOVERY_ENV = {
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CEILING_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_DIR",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_INDEX_FILE",
    "GIT_NAMESPACE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_PREFIX",
    "GIT_WORK_TREE",
}


@dataclass(frozen=True)
class ForwardCorrectionSpec:
    """一回限りの incident 固有 correction。一般 registry へ拡張しない。"""

    target: str

    @property
    def payload(self) -> str:
        return (
            f"target={self.target}; product=claude; model=claude-opus-5; "
            "reasoning=xhigh; role=integrator"
        )


INCIDENT_6B64D21_FORWARD_CORRECTION = ForwardCorrectionSpec(
    target="6b64d21753d2cfc790f80caba29df7a40fef3072",
)


@dataclass(frozen=True)
class CorrectionAudit:
    raw_values: tuple[str, ...]
    parsed_values: tuple[str, ...]
    final_values: tuple[str, ...]
    final_ai_agent_values: tuple[str, ...]
    findings: tuple[str, ...]

    @property
    def candidate_count(self) -> int:
        return len(self.raw_values)

    @property
    def exact(self) -> bool:
        return self.candidate_count == 1 and not self.findings


@dataclass(frozen=True)
class CommitAudit:
    commit: str
    label: str
    normal_findings: tuple[str, ...]
    correction: CorrectionAudit


@dataclass(frozen=True)
class ForwardCorrected:
    target: str
    correction: str


def _git(*args: str, input_text: str | None = None) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=REPO,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return proc.stdout


def _canonical_trailer_env(parse_cwd: Path) -> dict[str, str]:
    """ambient config と repo discovery から隔離した trailer parser 環境。"""
    env = {
        key: value for key, value in os.environ.items()
        if key != "GIT_CONFIG"
        and not key.startswith("GIT_CONFIG_")
        and key not in _REPO_DISCOVERY_ENV
    }
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CEILING_DIRECTORIES"] = str(parse_cwd)
    return env


def _isolated_parsed_trailers(
    message: str, *, no_divider: bool,
) -> dict[str, list[str]]:
    """隔離 parser の LF record を case-fold key ごとに返す。"""
    message_bytes = message.encode("utf-8")
    with tempfile.TemporaryDirectory(
        prefix="check-ai-provenance-",
        dir=TRAILER_PARSE_TEMP_ROOT,
    ) as private_dir:
        ceiling = Path(private_dir)
        parse_cwd = ceiling / "cwd"
        parse_cwd.mkdir()
        command = [
            "git", "-c", "trailer.separators=:",
            "interpret-trailers", "--parse",
        ]
        if no_divider:
            command.append("--no-divider")
        proc = subprocess.run(
            command,
            cwd=parse_cwd,
            env=_canonical_trailer_env(ceiling),
            input=message_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    if proc.returncode != 0:
        detail_bytes = proc.stderr.strip() or proc.stdout.strip()
        detail = detail_bytes.decode("utf-8", errors="backslashreplace")
        raise RuntimeError(f"git interpret-trailers failed: {detail}")
    if not isinstance(proc.stdout, bytes):
        raise RuntimeError("git interpret-trailers returned non-bytes stdout")

    records = proc.stdout.split(b"\n")
    if records and records[-1] == b"":
        records.pop()
    trailers: dict[str, list[str]] = {}
    for record in records:
        decoded = record.decode("utf-8")
        key, sep, value = decoded.partition(":")
        if not record or not sep or not key.strip(" \t"):
            raise RuntimeError(
                "git interpret-trailers returned unexpected LF record: "
                f"{record!r}"
            )
        trailers.setdefault(key.strip(" \t").casefold(), []).append(
            value.strip(" \t")
        )
    return trailers


def _parsed_trailers(message: str) -> dict[str, list[str]]:
    """CAB/correction 用の隔離 --no-divider canonical parse。"""
    return _isolated_parsed_trailers(message, no_divider=True)


def _parsed_final_trailers(message: str) -> dict[str, list[str]]:
    """correction と AI-Agent の final block を隔離 default parse で返す。"""
    return _isolated_parsed_trailers(message, no_divider=False)


def _ai_agent_values(message: str) -> list[str]:
    """従来の repo cwd・divider 既定 parser で AI-Agent 値だけを返す。"""
    parsed = _git("interpret-trailers", "--parse", input_text=message)
    values: list[str] = []
    for line in parsed.splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip().lower() == "ai-agent":
            values.append(value.strip())
    return values


def _co_authored_by_findings(
    label: str, message: str,
) -> list[str]:
    raw_count = len(RAW_CO_AUTHORED_BY.findall(message))
    trailers = _parsed_trailers(message)
    parsed_count = len(trailers.get("co-authored-by", []))
    if raw_count == parsed_count:
        return []
    return [
        f"{label}: Co-Authored-By trailer 配置違反: "
        f"raw={raw_count}, parsed={parsed_count}"
    ]


def _correction_audit(label: str, message: str) -> CorrectionAudit:
    """raw 候補を隔離 canonical/final-block parse と突き合わせる。"""
    matches = tuple(RAW_AI_AGENT_CORRECTION.finditer(message))
    if not matches:
        return CorrectionAudit((), (), (), (), ())

    raw_values = tuple(match.group("value") for match in matches)
    key = CORRECTION_KEY.casefold()
    parsed_values = tuple(
        _parsed_trailers(message).get(key, [])
    )
    final_trailers = _parsed_final_trailers(message)
    final_values = tuple(final_trailers.get(key, []))
    final_ai_agent_values = tuple(final_trailers.get("ai-agent", []))
    payload = INCIDENT_6B64D21_FORWARD_CORRECTION.payload
    findings: list[str] = []
    if len(raw_values) != 1:
        findings.append(
            f"{label}: {CORRECTION_KEY} raw candidate cardinality 違反: "
            f"raw={len(raw_values)}（物理 exact 1 行が必要）"
        )
    if raw_values and any(value != f" {payload}" for value in raw_values):
        findings.append(
            f"{label}: {CORRECTION_KEY} raw value が incident 固定値と一致しない"
        )
    if len(parsed_values) != 1:
        findings.append(
            f"{label}: {CORRECTION_KEY} canonical multiplicity 違反: "
            f"raw={len(raw_values)}, canonical={len(parsed_values)}"
        )
    if parsed_values and any(value != payload for value in parsed_values):
        findings.append(
            f"{label}: {CORRECTION_KEY} canonical value が incident 固定値と一致しない"
        )
    if len(final_values) != 1 or not final_ai_agent_values:
        findings.append(
            f"{label}: {CORRECTION_KEY} final trailer block multiplicity 違反: "
            f"correction={len(final_values)}, ai-agent={len(final_ai_agent_values)}"
        )
    if final_values and any(value != payload for value in final_values):
        findings.append(
            f"{label}: {CORRECTION_KEY} final trailer block value が "
            "incident 固定値と一致しない"
        )
    return CorrectionAudit(
        raw_values,
        parsed_values,
        final_values,
        final_ai_agent_values,
        tuple(findings),
    )


def validate_message(
    label: str, message: str, *, check_cab: bool = True,
) -> tuple[list[str], list[str], list[str]]:
    """(findings, scope_findings, cab_findings) を返す。

    scope_findings は「同じ role が複数行あるのに scope がない」違反。scope 規則の
    導入 commit より前の履歴には遡及しないため、呼び出し側が適用可否を判定する。
    CAB policy 導入前の履歴では check_cab=False とし、canonical parser 自体を呼ばない。
    """
    values = _ai_agent_values(message)
    cab_findings = (
        _co_authored_by_findings(label, message) if check_cab else []
    )
    if not values:
        return [f"{label}: AI-Agent trailer がない"], [], cab_findings

    if "none" in values:
        if values != ["none"]:
            return [
                f"{label}: AI-Agent: none は唯一の AI-Agent trailer でなければならない"
            ], [], cab_findings
        return [], [], cab_findings

    findings: list[str] = []
    seen: set[str] = set()
    by_role: dict[str, list[tuple[str, bool]]] = {}
    for value in values:
        if value in seen:
            findings.append(f"{label}: 同一 AI-Agent trailer の重複: {value}")
            continue
        seen.add(value)
        match = AGENT_VALUE.fullmatch(value)
        if not match:
            findings.append(
                f"{label}: AI-Agent の形式違反: {value!r} — "
                "product/model/reasoning/role (任意で scope) の順と許可値を確認する"
            )
            continue
        by_role.setdefault(match.group("role"), []).append(
            (value, match.group("scope") is not None)
        )
        if match.group("product") in RESERVED_PRODUCTS:
            findings.append(
                f"{label}: product={match.group('product')} は AI 製品識別子として使えない"
            )
        if match.group("model") == "none" or match.group("reasoning") == "none":
            findings.append(
                f"{label}: model/reasoning に none は使えない — "
                "not-exposed または unknown を使う"
            )

    scope_findings: list[str] = []
    for role, entries in by_role.items():
        if len(entries) < 2:
            continue
        for value, has_scope in entries:
            if not has_scope:
                scope_findings.append(
                    f"{label}: role={role} が複数行あるのに scope がない: {value}"
                )
    return findings, scope_findings, cab_findings


def _scope_policy_commit() -> str | None:
    """scope 規則を docs/ai-provenance.md へ導入した commit を内容検出する (SHA 非依存)。"""
    commits = _git(
        "log", "--reverse", "--format=%H", "-S", "scope=", "--", POLICY_PATH
    ).splitlines()
    return commits[0] if commits else None


def _implementation_policy_commit() -> str | None:
    """Codex author 契約を導入した commit を内容検出する。"""
    commits = _git(
        "log", "--reverse", "--format=%H", "-S", IMPLEMENTATION_POLICY_NEEDLE,
        "--", POLICY_PATH,
    ).splitlines()
    return commits[0] if commits else None


def _has_co_authored_by_policy(commit: str) -> bool:
    """commit ancestry に CAB policy needle の変更があれば適用済みとみなす。"""
    commits = _git(
        "log", "--full-history", "--no-renames", "--format=%H",
        "-S", CO_AUTHORED_BY_POLICY_NEEDLE, commit, "--", POLICY_PATH,
    ).splitlines()
    return bool(commits)


def _is_descendant(ancestor: str, commit: str) -> bool:
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, commit],
        cwd=REPO,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode == 0:
        return True
    if proc.returncode == 1:
        return False
    detail = proc.stderr.strip()
    raise RuntimeError(
        "git merge-base --is-ancestor "
        f"{ancestor} {commit} failed (rc={proc.returncode}): {detail}"
    )


def _is_implementation_path(path: str) -> bool:
    """Git 相対 path が実装面なら True。所在・拡張子の契約を一か所で判定する。"""
    normalized = path.removeprefix("./")
    basename = normalized.rsplit("/", 1)[-1]
    if basename in IMPLEMENTATION_BASENAMES:
        return True
    if normalized.endswith(IMPLEMENTATION_SUFFIXES):
        return True
    if normalized.startswith("patches/"):
        return False
    return (
        normalized.startswith(IMPLEMENTATION_PREFIXES)
        and not normalized.endswith((".md", ".rst"))
    )


def validate_implementation_author(
    label: str, message: str, paths: list[str],
) -> list[str]:
    """AI 関与の実装面 commit に Codex author がいることを検査する。"""
    implementation = sorted(path for path in paths if _is_implementation_path(path))
    if not implementation:
        return []
    values = _ai_agent_values(message)
    if not values or values == ["none"]:
        return []
    for value in values:
        match = AGENT_VALUE.fullmatch(value)
        if (
            match is not None
            and match.group("product") == "codex"
            and match.group("role") == "author"
        ):
            return []
    sample = ", ".join(implementation[:3])
    if len(implementation) > 3:
        sample += f", ... ({len(implementation)} paths)"
    return [
        f"{label}: 実装面に Codex role=author がない — paths={sample}"
    ]


def _nul_paths(raw: str) -> list[str]:
    return [path for path in raw.split("\0") if path]


def _commit_parents(commit: str) -> list[str]:
    return _git("show", "-s", "--format=%P", commit).split()


def _paths_changed_from(parent: str, commit: str) -> set[str]:
    raw = _git(
        "diff", "--no-renames", "--name-only",
        "--diff-filter=ACMRDTUXB", "-z", parent, commit, "--",
    )
    return set(_nul_paths(raw))


def _paths_changed_from_index(parent: str) -> set[str]:
    raw = _git(
        "diff", "--cached", "--no-renames", "--name-only",
        "--diff-filter=ACMRDTUXB", "-z", parent, "--",
    )
    return set(_nul_paths(raw))


def _intersection_path_set(path_sets: list[set[str]]) -> list[str]:
    if not path_sets:
        raise RuntimeError("combined path calculation requires at least one parent")
    return sorted(set.intersection(*path_sets))


def _commit_paths(commit: str) -> list[str]:
    """non-merge は従来差分、merge は全 parent と異なる combined path。"""
    parents = _commit_parents(commit)
    if len(parents) <= 1:
        raw = _git(
            "diff-tree", "--root", "--no-renames", "--no-commit-id",
            "--name-only", "-r", "-z", commit,
        )
        return _nul_paths(raw)
    return _intersection_path_set([
        _paths_changed_from(parent, commit) for parent in parents
    ])


def _staged_paths() -> list[str]:
    raw = _git(
        "diff", "--cached", "--no-renames", "--name-only",
        "--diff-filter=ACMRDTUXB", "-z",
    )
    return _nul_paths(raw)


def _merge_preflight_parents() -> list[str]:
    """MERGE_HEAD 不在は通常 preflight、存在時は prospective parents を返す。"""
    git_path = _git("rev-parse", "--git-path", "MERGE_HEAD").strip()
    if not git_path:
        raise RuntimeError("git rev-parse --git-path MERGE_HEAD returned empty path")
    merge_head_path = Path(git_path)
    if not merge_head_path.is_absolute():
        merge_head_path = REPO / merge_head_path
    try:
        raw = merge_head_path.read_text(encoding="ascii")
    except FileNotFoundError:
        return []
    merge_heads = raw.splitlines()
    if (
        not merge_heads
        or any(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", oid) is None
               for oid in merge_heads)
        or len(set(merge_heads)) != len(merge_heads)
    ):
        raise RuntimeError("MERGE_HEAD is malformed")
    for oid in merge_heads:
        if not _commit_exists(oid):
            raise RuntimeError(f"MERGE_HEAD parent commit object is missing: {oid}")

    head = _git("rev-parse", "--verify", "HEAD^{commit}").strip()
    return [head, *merge_heads]


def _message_file_paths(merge_parents: list[str]) -> list[str]:
    if not merge_parents:
        return _staged_paths()
    return _intersection_path_set([
        _paths_changed_from_index(parent) for parent in merge_parents
    ])


def _policy_commit() -> str:
    commits = _git(
        "log", "--diff-filter=A", "--format=%H", "--", POLICY_PATH
    ).splitlines()
    if not commits:
        raise RuntimeError(
            f"{POLICY_PATH} の導入 commit が履歴にない。"
            "commit 前は --message-file で検査すること"
        )
    return commits[-1]


def _commit_range(rev_range: str | None) -> list[str]:
    if rev_range is None:
        policy = _policy_commit()
        descendants = _git(
            "rev-list", "--reverse", "--ancestry-path", f"{policy}..HEAD"
        ).splitlines()
        return [policy, *descendants]
    return _git("rev-list", "--reverse", rev_range).splitlines()


def _read_message(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text()


def _normal_commit_audit(
    commit: str,
    *,
    scope_epoch: str | None,
    implementation_epoch: str | None,
) -> CommitAudit:
    subject = _git("show", "-s", "--format=%s", commit).strip()
    message = _git("show", "-s", "--format=%B", commit)
    label = f"{commit[:12]} {subject}"
    cab_policy_applies = _has_co_authored_by_policy(commit)
    base, scoped, cab = validate_message(
        label, message, check_cab=cab_policy_applies,
    )
    findings = list(base)
    if (
        scoped
        and scope_epoch is not None
        and _is_descendant(scope_epoch, commit)
    ):
        findings.extend(scoped)
    findings.extend(cab)
    if (
        implementation_epoch is not None
        and _is_descendant(implementation_epoch, commit)
    ):
        findings.extend(validate_implementation_author(
            label, message, _commit_paths(commit),
        ))
    return CommitAudit(
        commit=commit,
        label=label,
        normal_findings=tuple(findings),
        correction=_correction_audit(label, message),
    )


def _audit_history(
    commits: list[str],
) -> tuple[list[str], list[ForwardCorrected]]:
    """selected revision set を順序非依存の membership/lineage 条件で監査する。"""
    scope_epoch = _scope_policy_commit()
    implementation_epoch = _implementation_policy_commit()
    audits = [
        _normal_commit_audit(
            commit,
            scope_epoch=scope_epoch,
            implementation_epoch=implementation_epoch,
        )
        for commit in commits
    ]
    by_commit = {audit.commit: audit for audit in audits}
    candidate_count = sum(
        audit.correction.candidate_count for audit in audits
    )
    candidate_audits = [
        audit for audit in audits if audit.correction.candidate_count
    ]
    correction_findings = [
        finding
        for audit in audits
        for finding in audit.correction.findings
    ]
    corrected: list[ForwardCorrected] = []
    suppressed_missing: tuple[str, str] | None = None
    spec = INCIDENT_6B64D21_FORWARD_CORRECTION

    if candidate_count and candidate_count != 1:
        correction_findings.append(
            "check_ai_provenance: AI-Agent-Correction は selected revision set 内 "
            f"exact 1 件でなければならない: candidates={candidate_count}"
        )
    elif candidate_count == 1:
        correction = candidate_audits[0]
        target = by_commit.get(spec.target)
        target_selected = target is not None
        strict_descendant = (
            target_selected
            and correction.commit != spec.target
            and _is_descendant(spec.target, correction.commit)
        )
        target_missing = (
            f"{target.label}: AI-Agent trailer がない"
            if target is not None
            else None
        )
        if not target_selected:
            correction_findings.append(
                f"{correction.label}: AI-Agent-Correction target が "
                "selected revision set にない"
            )
        elif not strict_descendant:
            correction_findings.append(
                f"{correction.label}: AI-Agent-Correction commit が "
                "target の strict descendant でない"
            )
        if target is not None and target_missing not in target.normal_findings:
            correction_findings.append(
                f"{correction.label}: AI-Agent-Correction target に "
                "AI-Agent trailer の実欠落がない"
            )

        if (
            correction.correction.exact
            and target_selected
            and strict_descendant
            and target is not None
            and target_missing in target.normal_findings
            and not correction.normal_findings
        ):
            suppressed_missing = (spec.target, target_missing)
            corrected.append(ForwardCorrected(spec.target, correction.commit))

    findings: list[str] = []
    for audit in audits:
        for finding in audit.normal_findings:
            if suppressed_missing == (audit.commit, finding):
                continue
            findings.append(finding)
    findings.extend(correction_findings)
    return findings, corrected


def _commit_exists(commit: str) -> bool:
    query = f"{commit}^{{commit}}"
    proc = subprocess.run(
        ["git", "cat-file", "--batch-check=%(objectname) %(objecttype)"],
        cwd=REPO,
        input=f"{query}\n",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(
            "git cat-file --batch-check failed "
            f"(rc={proc.returncode}): {detail}"
        )
    record = proc.stdout.removesuffix("\n")
    if record == f"{query} missing":
        return False
    if re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64}) commit", record):
        return True
    raise RuntimeError(
        "git cat-file --batch-check returned unexpected record: "
        f"{record!r}"
    )


def _message_file_correction_findings(
    label: str,
    correction: CorrectionAudit,
    merge_parents: list[str],
) -> list[str]:
    """prospective parent 集合だけを仮定する非権威な correction preflight。"""
    findings = list(correction.findings)
    if correction.candidate_count != 1:
        findings.append(
            f"{label}: AI-Agent-Correction は message-file 内 exact 1 件が必要: "
            f"candidates={correction.candidate_count}"
        )
        return findings

    spec = INCIDENT_6B64D21_FORWARD_CORRECTION
    if not _commit_exists(spec.target):
        findings.append(
            f"{label}: AI-Agent-Correction target commit object が存在しない"
        )
        return findings
    ancestry_tips = merge_parents or ["HEAD"]
    if not any(_is_descendant(spec.target, tip) for tip in ancestry_tips):
        findings.append(
            f"{label}: AI-Agent-Correction target が prospective parent "
            "ancestry にない"
        )

    target_message = _git("show", "-s", "--format=%B", spec.target)
    if _ai_agent_values(target_message):
        findings.append(
            f"{label}: AI-Agent-Correction target に AI-Agent trailer の実欠落がない"
        )

    existing_candidates = 0
    for commit in _git("rev-list", *ancestry_tips).splitlines():
        message = _git("show", "-s", "--format=%B", commit)
        existing_candidates += len(RAW_AI_AGENT_CORRECTION.findall(message))
    if existing_candidates:
        findings.append(
            f"{label}: prospective parent ancestry 全体に既存 "
            "AI-Agent-Correction candidate がある: "
            f"candidates={existing_candidates}"
        )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--range", dest="rev_range", help="検査する git revision range")
    group.add_argument(
        "--message-file",
        help="commit 前の message ファイルを検査する。標準入力は -",
    )
    args = parser.parse_args()

    try:
        corrected: list[ForwardCorrected] = []
        correction_preflight = False
        merge_preflight = False
        if args.message_file is not None:
            message = _read_message(args.message_file)
            merge_parents = _merge_preflight_parents()
            merge_preflight = bool(merge_parents)
            base, scoped, cab = validate_message(
                args.message_file, message
            )
            implementation = validate_implementation_author(
                args.message_file, message, _message_file_paths(merge_parents),
            )
            findings = [*base, *scoped, *cab, *implementation]
            correction = _correction_audit(args.message_file, message)
            if correction.candidate_count:
                findings.extend(_message_file_correction_findings(
                    args.message_file, correction, merge_parents,
                ))
                correction_preflight = not findings
            checked = 1
        else:
            commits = _commit_range(args.rev_range)
            findings, corrected = _audit_history(commits)
            checked = len(commits)
    except (OSError, RuntimeError, UnicodeError) as exc:
        print(f"check_ai_provenance: 実行不能: {exc}", file=sys.stderr)
        return 2

    if findings:
        for finding in findings:
            print(finding, file=sys.stderr)
        print(
            f"check_ai_provenance: {checked} 件中 {len(findings)} 違反",
            file=sys.stderr,
        )
        return 1

    for record in corrected:
        print(
            "check_ai_provenance: forward-corrected=1 "
            f"target={record.target} correction={record.correction}"
        )
    if correction_preflight:
        spec = INCIDENT_6B64D21_FORWARD_CORRECTION
        assumption = (
            "MERGE_HEAD の prospective merge"
            if merge_preflight
            else "current HEAD の通常子"
        )
        print(
            "check_ai_provenance: AI-Agent-Correction は preflight限定 "
            f"（{assumption}を仮定）。commit後 history監査が必須 "
            f"target={spec.target}"
        )
    print(f"check_ai_provenance: {checked} 件、違反なし")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
