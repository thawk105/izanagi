#!/usr/bin/env python3
"""spool_fold の schema、遷移、transaction、golden 回帰。"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import dataclasses
import difflib
import hashlib
import importlib.util
import inspect
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from tools.dev_waves.git_state import (
    FOLD_AUTHOR_IDENTITY,
    FOLD_COMMIT_MESSAGE,
    verify_declared_fold_commit,
)
from tools.dev_waves.schema import DevWavesError


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("spool_fold_under_test", ROOT / "tools" / "spool_fold.py")
assert SPEC is not None and SPEC.loader is not None
spool_fold = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = spool_fold
SPEC.loader.exec_module(spool_fold)

_GENERATED_NEXT_ACTION_HEADING = (
    "### 次の一手 — 「(番号)」だけの項は、その番号のエントリ "
    "(archive 含む) から変わらない持ち越し"
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _run_git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def _hash_object(repo: Path, content: bytes) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), "hash-object", "--stdin"],
        check=True,
        input=content,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.decode("ascii", errors="strict").strip()


def _commit(repo: Path, message: str = "fixture") -> None:
    _run_git(repo, "add", "-A")
    _run_git(repo, "commit", "-m", message)


def _raw_commit(
    repo: Path,
    *,
    author: bytes,
    message: bytes = FOLD_COMMIT_MESSAGE,
) -> str:
    parent = _run_git(repo, "rev-parse", "HEAD")
    tree = _run_git(repo, "write-tree")
    raw = (
        f"tree {tree}\nparent {parent}\n".encode("ascii")
        + b"author " + author + b"\n"
        + b"committer Fixture <fixture@example.invalid> 1700000000 +0000\n\n"
        + message
    )
    completed = subprocess.run(
        ["git", "-C", str(repo), "hash-object", "-t", "commit", "-w", "--stdin"],
        check=True,
        input=raw,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    commit = completed.stdout.decode("ascii", errors="strict").strip()
    _run_git(repo, "update-ref", "HEAD", commit, parent)
    return commit


def _land_origin(repo: Path) -> spool_fold.FoldOrigin:
    tested_tip = _run_git(repo, "rev-parse", "HEAD")
    wave_ref = _run_git(repo, "symbolic-ref", "HEAD")
    parent = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", "HEAD^"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    trusted = parent.stdout.strip() if parent.returncode == 0 else tested_tip
    audited = tuple(
        line
        for line in _run_git(repo, "rev-list", "--reverse", f"{trusted}..{tested_tip}").splitlines()
        if line
    )
    return spool_fold.FoldOrigin(
        kind="land",
        base=trusted,
        tested_tip=tested_tip,
        wave_ref=wave_ref,
        rollback_ref=trusted,
        trusted_main_cutoff=trusted,
        audited_digest=spool_fold.audited_commit_digest(audited),
    )


def _plan_for_commit(
    repo: Path,
    *,
    fold_date: str | None = None,
) -> spool_fold.FoldPlan:
    if _run_git(repo, "status", "--porcelain=v1"):
        _commit(repo, "fold inputs")
    return spool_fold.plan_fold(repo, fold_date=fold_date, origin=_land_origin(repo))


def _finish_fold(repo: Path, plan: spool_fold.FoldPlan) -> spool_fold.FoldResult:
    state_path = spool_fold._state_path(repo)
    assert not state_path.exists() and not state_path.is_symlink()
    result = spool_fold.apply_fold(repo, plan)
    assert state_path.is_file()
    assert spool_fold._load_state(state_path)["phase"] == "applied"
    _run_git(repo, "add", "-A")
    completed = subprocess.run(
        [
            "git", "-C", str(repo), "commit", "--no-gpg-sign",
            "--cleanup=verbatim", f"--author={FOLD_AUTHOR_IDENTITY}", "-F", "-",
        ],
        check=True,
        input=FOLD_COMMIT_MESSAGE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert completed.returncode == 0
    fold_commit = _run_git(repo, "rev-parse", "HEAD")
    committed = spool_fold.mark_fold_committed(repo, plan, fold_commit=fold_commit)
    assert committed.phase == "committed"
    assert spool_fold._load_state(state_path)["phase"] == "committed"
    spool_fold.finalize_fold(repo, committed, fold_commit=fold_commit)
    assert not state_path.exists() and not state_path.is_symlink()
    return result


def _commit_applied_fold(repo: Path, plan: spool_fold.FoldPlan) -> str:
    spool_fold.apply_fold(repo, plan)
    _run_git(repo, "add", "-A")
    subprocess.run(
        [
            "git", "-C", str(repo), "commit", "--no-gpg-sign",
            "--cleanup=verbatim", f"--author={FOLD_AUTHOR_IDENTITY}", "-F", "-",
        ],
        check=True,
        input=FOLD_COMMIT_MESSAGE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return _run_git(repo, "rev-parse", "HEAD")


def _assert_declared_fold(repo: Path, plan: spool_fold.FoldPlan, fold_commit: str) -> None:
    audited = tuple(
        _run_git(
            repo,
            "rev-list",
            "--reverse",
            f"{plan.origin.trusted_main_cutoff}..{plan.origin.tested_tip}",
        ).splitlines()
    )
    declared = verify_declared_fold_commit(
        repo,
        fold_commit_sha=fold_commit,
        trusted_main_cutoff_sha=plan.origin.trusted_main_cutoff,
        landed_main_sha=fold_commit,
        landed_commits=audited,
        wave_tip=plan.origin.tested_tip,
    )
    assert declared.ok, declared


def _complete_fold(
    repo: Path,
    *,
    fold_date: str | None = None,
) -> tuple[spool_fold.FoldPlan, spool_fold.FoldResult]:
    plan = _plan_for_commit(repo, fold_date=fold_date)
    return plan, _finish_fold(repo, plan)


def _item(task_id: str, text: str) -> str:
    return f"- {task_id} {text}\n"


def _digest(block: str) -> str:
    return hashlib.sha256((block.rstrip("\n") + "\n").encode("utf-8")).hexdigest()


def _repo(tmp_path: Path, *, active: tuple[str, ...] = ("[T-001]",), limit: int = 100_000) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(repo, "init", "-q")
    _run_git(repo, "config", "user.name", "Fixture")
    _run_git(repo, "config", "user.email", "fixture@example.invalid")
    (repo / "tools").mkdir()
    shutil.copy2(ROOT / "tools/spool_fold.py", repo / "tools/spool_fold.py")
    _write(repo / "tools/check_docs.py", f"WORKLOG_ROTATE_BYTES = {limit}\n")
    next_actions = "".join(_item(task_id, f"現本文 {task_id}") for task_id in active)
    _write(
        repo / "docs/worklog.md",
        "# worklog\n\n## ローテーション\n\n---\n\n"
        "## 2026-08-01 (1) — seed\n\n"
        "- seed body\n\n### 次の一手\n\n"
        + next_actions,
    )
    _write(repo / "docs/decisions.md", "# decisions\n\n## D1. seed (2026-08-01)\n\n**決定:** seed\n")
    _write(
        repo / "docs/failures.md",
        "# failures\n\n## エントリ\n\n### F1. seed [手順漏れ]\n"
        "- 事象: seed\n- 根本原因: seed\n- 恒久対応: seed\n- 再発検知: seed\n",
    )
    _write(
        repo / "docs/phase3.md",
        "# phase3\n\n## 見送り台帳\n\n### プロセス文書系\n\n"
        "- [T-050] 既存見送り — 理由: seed\n\n"
        "### 研究・計測系\n\n- [T-051] 既存見送り — 理由: seed\n\n"
        "### 裁定・完了記録\n\n- [T-052] 完了済み\n",
    )
    _write(repo / "docs/archive/README.md", "# archive\n\n## 現在の収容物\n")
    _write(repo / "docs/archive/worklog-old.md", "## 2026-07-25 — old\n\n### 次の一手\n\n- [T-049] old\n")
    _write(repo / "docs/spool/README.md", "# spool\n")
    _write(repo / "docs/spool/FOLDED.md", "# Fold receipts\n")
    for ledger in spool_fold.LEDGERS:
        _write(repo / f"docs/spool/{ledger}/README.md", f"# {ledger}\n")
    _commit(repo, "base fixture")
    return repo


def _fragment(
    repo: Path,
    ledger: str,
    body: str,
    *,
    authored: str = "2026-08-02",
    wave: str = "wave-a",
    seq: int = 1,
    title: str = "fold test",
) -> Path:
    fields = [
        "---",
        f"schema: {spool_fold.SCHEMA}",
        f"ledger: {ledger}",
        f"authored: {authored}",
        f"wave: {wave}",
        f"seq: {seq}",
    ]
    if ledger == "worklog":
        fields.append(f"title: {title}")
    text = "\n".join(fields) + "\n---\n" + body.strip("\n") + "\n"
    path = repo / f"docs/spool/{ledger}/{authored}-{wave}-{seq}.md"
    _write(path, text)
    return path


def _worklog_body(
    repo: Path,
    *,
    carry: tuple[str, ...] = ("[T-001]",),
    completed: tuple[tuple[str, str, str], ...] = (),
    completion_remaining: bool = False,
    updated: tuple[tuple[str, str, str], ...] = (),
    new: tuple[tuple[str, str], ...] = (),
    deferred: tuple[tuple[str, str, str, str], ...] = (),
    deferred_appends: tuple[tuple[str, str], ...] = (),
    prose: str = "- fold 本文",
) -> str:
    sections = [f"## 本文\n\n{prose}\n", "## 次の一手差分\n"]
    if carry:
        sections.append("### carry\n\n" + "".join(f"- {task_id}\n" for task_id in carry))
    if completed:
        blocks = ""
        for task_id, text, base in completed:
            blocks += f"- {task_id} {text}\n  base: {base}\n"
            if completion_remaining:
                blocks += "  remaining: none\n"
        sections.append("### 完了\n\n" + blocks)
    if updated:
        blocks = ""
        for task_id, text, base in updated:
            blocks += f"- {task_id} {text}\n  base: {base}\n"
        sections.append("### 更新\n\n" + blocks)
    if new:
        sections.append("### 新規\n\n" + "".join(f"- {{{{T:{slug}}}}} {text}\n" for slug, text in new))
    if deferred:
        by_category: dict[str, list[tuple[str, str, str]]] = {}
        for category, task_id, text, base in deferred:
            by_category.setdefault(category, []).append((task_id, text, base))
        value = "### 見送り\n"
        for category, entries in by_category.items():
            value += f"\n#### {category}\n\n"
            for task_id, text, base in entries:
                value += f"- {task_id} {text}\n  base: {base}\n"
        sections.append(value)
    if deferred_appends:
        sections.append(
            "### 見送り追記\n\n"
            + "".join(f"- {task_id}{suffix}\n" for task_id, suffix in deferred_appends)
        )
    return "\n".join(section.rstrip("\n") for section in sections) + "\n"


def _failure_body(
    *,
    new: tuple[str, ...] = (),
    recurrences: tuple[tuple[int, str], ...] = (),
    supersedes: tuple[tuple[int, str], ...] = (),
) -> str:
    sections: list[str] = []
    if new:
        sections.append("## 新規\n\n" + "\n".join(entry.strip("\n") for entry in new))
    if recurrences:
        sections.append(
            "## 再発\n\n"
            + "\n".join(
                f"### F{number}\n\n{payload.strip(chr(10))}"
                for number, payload in recurrences
            )
        )
    if supersedes:
        sections.append(
            "## supersede 追記\n\n"
            + "\n".join(f"- F{number} {body}" for number, body in supersedes)
        )
    return "\n\n".join(sections) + "\n"


def _supersede(detail: str, *, date: str = "2026-08-10") -> str:
    return f"**supersede: {date}** — {detail}"


def _active_block(task_id: str) -> str:
    return _item(task_id, f"現本文 {task_id}")


def _global_entry(ordinal: int, items: str, *, title: str = "fixture") -> str:
    return (
        f"## 2026-08-01 ({ordinal}) — {title}\n\n"
        "### 次の一手\n\n"
        f"{items}"
    )


def _synthetic_worklog(*entries: str) -> str:
    return "# worklog\n\n## ローテーション\n\n---\n\n" + "\n".join(entries)


def _raises(code: str, callable_object, *args, **kwargs):
    try:
        callable_object(*args, **kwargs)
    except spool_fold.SpoolValidationError as exc:
        assert [issue.code for issue in exc.issues] == [code], [issue.code for issue in exc.issues]
        return exc
    raise AssertionError(f"{code} を拒否しなかった")


def _transaction_raises(needle: str, callable_object, *args, **kwargs):
    try:
        callable_object(*args, **kwargs)
    except spool_fold.TransactionError as exc:
        assert needle in str(exc), str(exc)
        return exc
    raise AssertionError(f"TransactionError({needle!r}) を返さなかった")


def _unchecked_plan_from_state(
    original: spool_fold.FoldPlan,
    state: dict[str, object],
) -> spool_fold.FoldPlan:
    fragments = tuple(
        spool_fold.FragmentReceipt(
            item["path"],
            item["authored"],
            item["wave"],
            item["seq"],
            item["content_sha256"],
            tuple(tuple(pair) for pair in item["allocations"]),
        )
        for item in state["fragments"]
    )
    targets = tuple(
        spool_fold.TargetChange(
            item["path"],
            item["before_sha256"],
            item["after_sha256"],
            item["before_exists"],
            spool_fold.base64.b64decode(item["after_bytes_b64"]),
        )
        for item in state["targets"]
    )
    return dataclasses.replace(
        original,
        fold_date=state["fold_date"],
        input_closure_sha256=state["input_closure_sha256"],
        fragments=fragments,
        gc_paths=tuple(state["gc_paths"]),
        projected_worklog_bytes=state["projected_worklog_bytes"],
        rotation_path=state["rotation_path"],
        targets=targets,
    )


def _target(plan, rel: str):
    return next(target for target in plan.targets if target.path == rel)


def _phase_after(repo: Path) -> bytes:
    return _target(
        spool_fold.plan_fold(repo, fold_date="2026-08-02"),
        "docs/phase3.md",
    ).after_bytes


def _failures_after(repo: Path) -> bytes:
    return _target(
        spool_fold.plan_fold(repo, fold_date="2026-08-10"),
        "docs/failures.md",
    ).after_bytes


def _line_end_offset(raw: bytes, marker: bytes) -> int:
    start = raw.index(marker)
    return raw.index(b"\n", start)


def _splice_exact(raw: bytes, insertions: tuple[tuple[int, bytes], ...]) -> bytes:
    rendered = raw
    for offset, payload in sorted(insertions, reverse=True):
        rendered = rendered[:offset] + payload + rendered[offset:]
    return rendered


def test_legacy_daily_ordinals_are_excluded_from_global_namespace(tmp_path: Path) -> None:
    """旧日次 ordinal の世代内・global との数値衝突は global uniqueness の対象外。"""

    repo = _repo(tmp_path)
    legacy = "## 2026-07-25 (1) — legacy\n\n### 次の一手\n\n- [T-001] legacy\n"
    _write(repo / "docs/archive/worklog-legacy-a.md", legacy)
    _write(repo / "docs/archive/worklog-legacy-b.md", legacy.replace("legacy\n", "legacy duplicate\n", 1))
    _fragment(repo, "worklog", _worklog_body(repo))
    plan = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    rendered = _target(plan, "docs/worklog.md").after_bytes.decode("utf-8")
    assert "## 2026-08-02 (2) — fold test" in rendered


def test_global_max_ordinal_ignores_larger_legacy_ordinal(tmp_path: Path) -> None:
    """RB-03: legacy (99) があっても global (1) の次は (2)。"""

    repo = _repo(tmp_path)
    _write(
        repo / "docs/archive/worklog-old.md",
        "## 2026-07-25 (99) — legacy\n\n### 次の一手\n\n- [T-001] legacy\n",
    )
    _fragment(repo, "worklog", _worklog_body(repo))
    plan = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    rendered = _target(plan, "docs/worklog.md").after_bytes.decode("utf-8")
    assert "## 2026-08-02 (2) — fold test" in rendered


def test_global_ordinal_duplicate_is_rejected(tmp_path: Path) -> None:
    """境界日以降の ordinal 重複は従来どおり fail-closed。"""

    repo = _repo(tmp_path)
    _write(
        repo / "docs/archive/worklog-global-duplicate.md",
        "## 2026-07-26 (1) — duplicate\n\n### 次の一手\n\n- [T-001] duplicate\n",
    )
    _fragment(repo, "worklog", _worklog_body(repo))
    _raises("worklog-ordinal", spool_fold.plan_fold, repo)


def test_global_ordinal_gap_is_allowed_and_next_uses_max_plus_one(tmp_path: Path) -> None:
    """N29: global の欠番を受理し、次番号は個数でなく最大値 + 1。"""

    repo = _repo(tmp_path)
    _write(
        repo / "docs/archive/worklog-global-gap.md",
        "## 2026-07-26 (1) — one\n\n### 次の一手\n\n- [T-001] one\n\n"
        "## 2026-07-27 (2) — two\n\n### 次の一手\n\n- [T-001] two\n",
    )
    worklog = (repo / "docs/worklog.md").read_text(encoding="utf-8")
    _write(repo / "docs/worklog.md", worklog.replace("2026-08-01 (1)", "2026-08-01 (5)"))
    _fragment(repo, "worklog", _worklog_body(repo))
    plan = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    rendered = _target(plan, "docs/worklog.md").after_bytes.decode("utf-8")
    assert "## 2026-08-02 (6) — fold test" in rendered


def test_global_carry_resolves_global_entry_not_legacy_collision(tmp_path: Path) -> None:
    """同じ ordinal が旧世代にもあっても carry の本文は global 世代へ束縛する。"""

    repo = _repo(tmp_path)
    _write(
        repo / "docs/archive/worklog-old.md",
        "## 2026-07-25 (1) — legacy\n\n### 次の一手\n\n- [T-001] legacy body\n",
    )
    _write(
        repo / "docs/archive/worklog-global.md",
        "## 2026-07-26 (1) — global\n\n### 次の一手\n\n- [T-001] global body\n",
    )
    _write(
        repo / "docs/worklog.md",
        "# worklog\n\n## ローテーション\n\n---\n\n"
        "## 2026-08-01 (2) — current\n\n### 次の一手\n\n"
        "- [T-001] 変わらず ((1) 参照)\n",
    )
    _fragment(
        repo,
        "worklog",
        _worklog_body(
            repo,
            carry=(),
            updated=(("[T-001]", "global を更新", _digest("- [T-001] global body\n")),),
        ),
    )
    plan = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    rendered = _target(plan, "docs/worklog.md").after_bytes.decode("utf-8")
    assert "- [T-001] global を更新" in rendered


def test_global_carry_cannot_fall_back_to_legacy_only_target(tmp_path: Path) -> None:
    """N28: global map にない carry 参照を旧世代だけから救済しない。"""

    repo = _repo(tmp_path)
    _write(
        repo / "docs/archive/worklog-old.md",
        "## 2026-07-25 (1) — legacy\n\n### 次の一手\n\n- [T-001] legacy body\n",
    )
    _write(
        repo / "docs/worklog.md",
        "# worklog\n\n## ローテーション\n\n---\n\n"
        "## 2026-08-01 (2) — current\n\n### 次の一手\n\n"
        "- [T-001] 変わらず ((1) 参照)\n",
    )
    _fragment(repo, "worklog", _worklog_body(repo))
    _raises("carry-reference", spool_fold.plan_fold, repo)


def test_boundary_constant_shift_is_detected_by_real_corpus_sentinel() -> None:
    """N27: 実 corpus signature が境界の 07-25 へのずれを単独で検出する。"""

    checkout = Path(__file__).resolve().parents[2]
    worklog = (checkout / "docs/worklog.md").read_text(encoding="utf-8")
    archives = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted((checkout / "docs/archive").glob("worklog-*.md"))
    }
    assert spool_fold._global_ordinal_entries(worklog, archives)
    original = spool_fold.GLOBAL_ORDINAL_START_DATE
    try:
        spool_fold.GLOBAL_ORDINAL_START_DATE = "2026-07-25"
        _raises("worklog-ordinal", spool_fold._global_ordinal_entries, worklog, archives)
        spool_fold.GLOBAL_ORDINAL_START_DATE = "2026-07-27"
        _raises("global-ordinal-boundary", spool_fold._global_ordinal_entries, worklog, archives)
        spool_fold.GLOBAL_ORDINAL_START_DATE = "9999-12-31"
        _raises("global-ordinal-boundary", spool_fold._global_ordinal_entries, worklog, archives)
    finally:
        spool_fold.GLOBAL_ORDINAL_START_DATE = original


def test_real_corpus_sentinel_rejects_missing_boundary_date() -> None:
    """RB-01: 実履歴 corpus では境界 entry が 0 件なら黙って省略しない。"""

    checkout = Path(__file__).resolve().parents[2]
    worklog = (checkout / "docs/worklog.md").read_text(encoding="utf-8")
    archives = {
        path.name: path.read_text(encoding="utf-8").replace(
            "## 2026-07-26 (", "## 2026-07-28 (",
        )
        for path in sorted((checkout / "docs/archive").glob("worklog-*.md"))
    }
    _raises("global-ordinal-boundary", spool_fold._global_ordinal_entries, worklog, archives)


def test_impossible_heading_date_is_rejected(tmp_path: Path) -> None:
    """N30: regex には一致する非実在の worklog 見出し日付を拒否する。"""

    repo = _repo(tmp_path)
    _write(
        repo / "docs/archive/worklog-impossible-date.md",
        "## 2026-99-99 (2) — impossible\n\n### 次の一手\n\n- [T-001] impossible\n",
    )
    _fragment(repo, "worklog", _worklog_body(repo))
    _raises("worklog-date", spool_fold.plan_fold, repo)


def test_fold_date_may_precede_the_current_entry_date(tmp_path: Path) -> None:
    """RB-02: global ordinal は増加させるが見出し日付の単調性は要求しない。"""

    repo = _repo(tmp_path)
    worklog = (repo / "docs/worklog.md").read_text(encoding="utf-8")
    _write(repo / "docs/worklog.md", worklog.replace("2026-08-01 (1)", "2026-07-29 (1)"))
    _fragment(
        repo, "worklog", _worklog_body(repo), authored="2026-07-28",
    )
    plan = spool_fold.plan_fold(repo, fold_date="2026-07-28")
    rendered = _target(plan, "docs/worklog.md").after_bytes.decode("utf-8")
    assert "## 2026-07-28 (2) — fold test" in rendered


def test_n01_frontmatter_filename_mismatch_is_rejected(tmp_path: Path) -> None:
    """N01: frontmatter と filename の一致 gate を単独で発火させる。"""

    repo = _repo(tmp_path)
    path = _fragment(repo, "worklog", _worklog_body(repo))
    path.rename(path.with_name("2026-08-02-wave-a-2.md"))
    issues = spool_fold.validate_spool_tree(repo)
    assert [issue.code for issue in issues] == ["filename"]


def test_n02_undefined_placeholder_is_rejected(tmp_path: Path) -> None:
    """N02: 未定義 placeholder を canonical へ素通ししない。"""

    repo = _repo(tmp_path)
    _fragment(repo, "decisions", "## {{D:defined}}. {{T:missing}} を参照\n")
    codes = [issue.code for issue in spool_fold.validate_spool_tree(repo)]
    assert codes == ["symbol-undefined"]


def test_n03_duplicate_symbol_definition_is_rejected(tmp_path: Path) -> None:
    """N03: 同一 wave/namespace/slug の重複定義を last-wins にしない。"""

    repo = _repo(tmp_path)
    _fragment(repo, "decisions", "## {{D:same}}. first\n", seq=1)
    _fragment(repo, "decisions", "## {{D:same}}. second\n", seq=2)
    codes = [issue.code for issue in spool_fold.validate_spool_tree(repo)]
    assert codes == ["symbol-duplicate"]


def test_n04_malformed_placeholder_residue_is_rejected(tmp_path: Path) -> None:
    """N04: 置換後に残る delimiter を最終 gate が拒否する。"""

    repo = _repo(tmp_path)
    _fragment(repo, "decisions", "## {{D:valid}}. fence に {{D:bad_slug}}\n")
    codes = [issue.code for issue in spool_fold.validate_spool_tree(repo)]
    assert codes == ["placeholder-malformed"]


def test_n05_task_allocation_includes_archive_population(tmp_path: Path) -> None:
    """N05: T 採番母集団に archive の最大 ID を含める。"""

    repo = _repo(tmp_path)
    _write(repo / "docs/archive/worklog-old.md", "## 2026-07-25 — old\n\n### 次の一手\n\n- [T-090] old\n")
    _fragment(repo, "worklog", _worklog_body(repo, new=(("archive-next", "新規"),)))
    plan = spool_fold.plan_fold(repo)
    assert dict(plan.allocations)["wave-a/T:archive-next"] == "[T-091]"


def test_n06_task_allocation_includes_deferred_population(tmp_path: Path) -> None:
    """N06: T 採番母集団に見送り台帳の最大 ID を含める。"""

    repo = _repo(tmp_path)
    phase = (repo / "docs/phase3.md").read_text(encoding="utf-8").replace("[T-050]", "[T-099]")
    _write(repo / "docs/phase3.md", phase)
    _fragment(repo, "worklog", _worklog_body(repo, new=(("deferred-next", "新規"),)))
    plan = spool_fold.plan_fold(repo)
    assert dict(plan.allocations)["wave-a/T:deferred-next"] == "[T-100]"


def test_n07_task_id_is_three_digit_canonical(tmp_path: Path) -> None:
    """N07: 1〜999 の T ID を 3 桁ゼロ埋めで出力する。"""

    repo = _repo(tmp_path, active=())
    phase = (repo / "docs/phase3.md").read_text(encoding="utf-8")
    phase = phase.replace("[T-050]", "[T-001]").replace("[T-051]", "[T-002]").replace("[T-052]", "T-NNN")
    _write(repo / "docs/phase3.md", phase)
    _write(repo / "docs/archive/worklog-old.md", "## 2026-07-25 — old\n\n### 次の一手\n\n")
    _fragment(repo, "worklog", _worklog_body(repo, carry=(), new=(("three-digit", "新規"),)))
    plan = spool_fold.plan_fold(repo)
    assert dict(plan.allocations)["wave-a/T:three-digit"] == "[T-003]"


def test_n08_all_carries_preserve_order_and_count(tmp_path: Path) -> None:
    """N08: carry 全数を前 list 順で再生成する。"""

    repo = _repo(tmp_path, active=("[T-001]", "[T-002]", "[T-003]"))
    _fragment(repo, "worklog", _worklog_body(repo, carry=("[T-001]", "[T-002]", "[T-003]")))
    text = _target(spool_fold.plan_fold(repo), "docs/worklog.md").after_bytes.decode()
    tail = text[text.rfind("### 次の一手"):]
    expected = (
        f"{_GENERATED_NEXT_ACTION_HEADING}\n\n"
        "- [T-001] (1)\n"
        "- [T-002] (1)\n"
        "- [T-003] (1)\n"
    )
    assert tail == expected


def test_implicit_and_explicit_carry_render_identically(tmp_path: Path) -> None:
    """未言及 active と明示 carry は同じ canonical 出力を作る。"""

    explicit_parent = tmp_path / "explicit"
    implicit_parent = tmp_path / "implicit"
    explicit_parent.mkdir()
    implicit_parent.mkdir()
    active = ("[T-001]", "[T-002]")
    explicit = _repo(explicit_parent, active=active)
    implicit = _repo(implicit_parent, active=active)
    _fragment(explicit, "worklog", _worklog_body(explicit, carry=active))
    _fragment(implicit, "worklog", _worklog_body(implicit, carry=()))
    explicit_text = _target(spool_fold.plan_fold(explicit), "docs/worklog.md").after_bytes.decode()
    implicit_text = _target(spool_fold.plan_fold(implicit), "docs/worklog.md").after_bytes.decode()
    explicit_tail = _next_action(_entry(explicit_text, 2))
    implicit_tail = _next_action(_entry(implicit_text, 2))
    assert implicit_tail == explicit_tail


def test_n09_active_conservation_postcondition_rejects_implicit_drop() -> None:
    """N09: postcondition 無効化変異を、欠落した render 結果だけで殺す。"""

    _raises(
        "transition-conservation",
        spool_fold._assert_active_conservation,
        {"[T-001]", "[T-002]"},
        set(),
        set(),
        set(),
        [spool_fold._TaskItem("[T-001]", "- [T-001] carry\n")],
    )


def test_parallel_fold_implicitly_carries_task_added_by_earlier_wave(tmp_path: Path) -> None:
    """先に fold された wave の新規 T を、古い別 wave fragment が暗黙 carry する。"""

    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo, carry=(), new=(("wave-a-task", "A の新規"),)))
    _commit(repo, "wave A fragment")
    _complete_fold(repo)
    _fragment(repo, "worklog", _worklog_body(repo, carry=()), wave="wave-b")
    text = _target(spool_fold.plan_fold(repo), "docs/worklog.md").after_bytes.decode("utf-8")
    tail = text[text.rfind("### 次の一手"):]
    assert tail == (
        f"{_GENERATED_NEXT_ACTION_HEADING}\n\n"
        "- [T-001] (2)\n"
        "- [T-052] (2)\n"
    )


def test_parallel_new_then_existing_update_uses_substantive_base_digest(tmp_path: Path) -> None:
    """F-1: A の新規 fold で carry 番号が動いても、B の既存項更新は stale にならない。"""

    repo = _repo(tmp_path)
    substantive_base = _digest(_active_block("[T-001]"))
    _fragment(
        repo,
        "worklog",
        _worklog_body(repo, carry=(), new=(("wave-a-task", "A の新規"),)),
        wave="wave-a",
    )
    _commit(repo, "wave A fragment")
    _complete_fold(repo, fold_date="2026-08-02")

    _fragment(
        repo,
        "worklog",
        _worklog_body(
            repo,
            carry=(),
            updated=(("[T-001]", "B の更新", substantive_base),),
        ),
        wave="wave-b",
    )
    plan = spool_fold.plan_fold(repo, fold_date="2026-08-03")
    text = _target(plan, "docs/worklog.md").after_bytes.decode("utf-8")
    assert "- [T-001] B の更新" in _next_action(_entry(text, 3))


def test_generated_next_action_heading_and_compact_carry_are_byte_exact() -> None:
    """末尾 reader 向け凡例と compact carry を固定 bytes で生成する。"""

    substantive = "- [T-001] substantive\n"
    section, _, _, _ = spool_fold._render_next_actions(
        [spool_fold._TaskItem("[T-001]", substantive, _digest(substantive))],
        (),
        7,
        {},
        "heading-golden",
    )
    expected = (
        "### 次の一手 — 「(番号)」だけの項は、その番号のエントリ "
        "(archive 含む) から変わらない持ち越し\n\n"
        "- [T-001] (7)\n"
    )
    assert section.encode("utf-8") == expected.encode("utf-8")
    assert "[T-" not in section.splitlines()[0]


def test_id_only_item_remains_substantive_under_compact_carry_format(tmp_path: Path) -> None:
    """ID 単独 item は compact carry に拡大解釈せず、item 自身の base で更新できる。"""

    repo = _repo(tmp_path)
    item = "- [T-001]\n"
    _write(repo / "docs/worklog.md", _synthetic_worklog(_global_entry(1, item)))
    _fragment(
        repo,
        "worklog",
        _worklog_body(
            repo,
            carry=(),
            updated=(("[T-001]", "ID 単独実体を更新", _digest(item)),),
        ),
    )
    plan = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    rendered = _target(plan, "docs/worklog.md").after_bytes.decode("utf-8")
    assert "- [T-001] ID 単独実体を更新" in _next_action(_entry(rendered, 2))


def test_compact_and_legacy_carry_chain_resolves_substantive_base(tmp_path: Path) -> None:
    """compact/legacy 混在は同一 latest entry から実体まで再帰解決する。"""

    repo = _repo(tmp_path)
    first_t001 = "- [T-001] 元実体 A\n"
    first_t002 = "- [T-002] 元実体 B\n"
    archive = (
        _global_entry(1, first_t001 + first_t002, title="substantive")
        + "\n"
        + _global_entry(
            2,
            "- [T-001] 変わらず ((1) 参照)\n"
            "- [T-002] 変わらず ((1) 参照)\n",
            title="legacy",
        )
    )
    _write(repo / "docs/archive/worklog-global-chain.md", archive)
    _write(
        repo / "docs/worklog.md",
        _synthetic_worklog(
            _global_entry(
                3,
                "- [T-001] (2)\n"
                "- [T-002] 変わらず ((1) 参照)\n",
                title="mixed latest",
            )
        ),
    )
    ordinal, active = spool_fold._extract_latest_active(
        (repo / "docs/worklog.md").read_text(encoding="utf-8"),
        {"worklog-global-chain.md": archive},
    )
    assert ordinal == 3
    assert {item.task_id: item.substantive_digest for item in active} == {
        "[T-001]": _digest(first_t001),
        "[T-002]": _digest(first_t002),
    }

    _fragment(
        repo,
        "worklog",
        _worklog_body(
            repo,
            carry=("[T-002]",),
            updated=(("[T-001]", "compact chain を更新", _digest(first_t001)),),
        ),
    )
    plan = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    rendered = _target(plan, "docs/worklog.md").after_bytes.decode("utf-8")
    assert "- [T-001] compact chain を更新" in _next_action(_entry(rendered, 4))


def test_compact_carry_missing_entry_rejects_before_stub_digest(tmp_path: Path) -> None:
    """missing entry を compact stub 自身の digest へ fail-open しない。"""

    repo = _repo(tmp_path)
    stub = "- [T-001] (1)\n"
    _write(repo / "docs/worklog.md", _synthetic_worklog(_global_entry(2, stub)))
    _fragment(
        repo,
        "worklog",
        _worklog_body(
            repo,
            carry=(),
            updated=(("[T-001]", "未解決のまま更新", _digest(stub)),),
        ),
    )
    _raises("carry-reference", spool_fold.plan_fold, repo)


def test_compact_carry_missing_task_rejects_before_stub_digest(tmp_path: Path) -> None:
    """entry に task がない compact 参照も stub digest へ fail-open しない。"""

    repo = _repo(tmp_path)
    stub = "- [T-001] (1)\n"
    _write(
        repo / "docs/archive/worklog-global-missing-task.md",
        _global_entry(1, "- [T-002] 別 task\n"),
    )
    _write(repo / "docs/worklog.md", _synthetic_worklog(_global_entry(2, stub)))
    _fragment(
        repo,
        "worklog",
        _worklog_body(
            repo,
            carry=(),
            updated=(("[T-001]", "未解決のまま更新", _digest(stub)),),
        ),
    )
    _raises("carry-reference", spool_fold.plan_fold, repo)


def test_compact_carry_future_or_self_reference_is_rejected(tmp_path: Path) -> None:
    """compact carry の self/future 参照はどちらも過去参照 gate で拒否する。"""

    for referenced in (2, 3):
        worklog = _synthetic_worklog(
            _global_entry(2, f"- [T-001] ({referenced})\n")
        )
        exc = _raises("carry-reference", spool_fold._extract_latest_active, worklog, {})
        assert "過去 entry を指さない" in exc.issues[0].message


def test_legacy_carry_future_reference_is_rejected() -> None:
    """旧書式も current (2) から archive (3) への未来参照を拒否する。"""

    worklog = _synthetic_worklog(
        _global_entry(2, "- [T-001] 変わらず ((3) 参照)\n", title="legacy future")
    )
    archive = _global_entry(3, "- [T-001] future substantive\n", title="future")
    exc = _raises(
        "carry-reference",
        spool_fold._extract_latest_active,
        worklog,
        {"worklog-global-future.md": archive},
    )
    assert "過去 entry を指さない" in exc.issues[0].message


def test_compact_stub_digest_cannot_satisfy_mutating_base(tmp_path: Path) -> None:
    """valid compact carry で stub 自身の digest を base にしても更新は通らない。"""

    repo = _repo(tmp_path)
    substantive = "- [T-001] 元実体\n"
    stub = "- [T-001] (1)\n"
    _write(
        repo / "docs/archive/worklog-global-substantive.md",
        _global_entry(1, substantive),
    )
    _write(repo / "docs/worklog.md", _synthetic_worklog(_global_entry(2, stub)))
    _fragment(
        repo,
        "worklog",
        _worklog_body(
            repo,
            carry=(),
            updated=(("[T-001]", "stub base で更新", _digest(stub)),),
        ),
    )
    _raises("base-mismatch", spool_fold.plan_fold, repo)


def test_compact_carry_gate_rejects_noncanonical_forms_as_substantive(tmp_path: Path) -> None:
    """compact 予約形以外は従来どおり実体 item として digest する。"""

    malformed_items = (
        "- [T-001] (0)\n",
        "- [T-001] (01)\n",
        "- [T-001] (1) 実体本文\n",
        "- [T-001] ()\n",
    )
    for index, item in enumerate(malformed_items):
        parent = tmp_path / f"malformed-{index}"
        parent.mkdir()
        repo = _repo(parent)
        _write(repo / "docs/worklog.md", _synthetic_worklog(_global_entry(1, item)))
        _fragment(
            repo,
            "worklog",
            _worklog_body(
                repo,
                carry=(),
                updated=(("[T-001]", f"誤形 {index} を更新", _digest(item)),),
            ),
        )
        plan = spool_fold.plan_fold(repo, fold_date="2026-08-02")
        rendered = _target(plan, "docs/worklog.md").after_bytes.decode("utf-8")
        assert f"- [T-001] 誤形 {index} を更新" in _next_action(_entry(rendered, 2))


def test_multiline_compact_prefix_item_uses_full_substantive_digest(tmp_path: Path) -> None:
    """fullmatch でない複数行 item は compact 先頭でも実体として更新できる。"""

    repo = _repo(tmp_path)
    substantive = "- [T-001] 元本文\n"
    multiline = "- [T-001] (1)\n  詳細\n"
    _write(
        repo / "docs/worklog.md",
        _synthetic_worklog(
            _global_entry(1, substantive, title="referenced"),
            _global_entry(2, multiline, title="multiline substantive"),
        ),
    )
    _fragment(
        repo,
        "worklog",
        _worklog_body(
            repo,
            carry=(),
            updated=(("[T-001]", "複数行実体を更新", _digest(multiline)),),
        ),
    )
    plan = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    rendered = _target(plan, "docs/worklog.md").after_bytes.decode("utf-8")
    assert "- [T-001] 複数行実体を更新" in _next_action(_entry(rendered, 3))


def test_four_digit_compact_carry_chain_resolves_ordinal_1000() -> None:
    """T-1000 と ordinal 1000 を含む compact chain を 3 桁固定せず解決する。"""

    substantive = "- [T-1000] four digit substantive\n"
    archive = (
        _global_entry(1000, substantive, title="four digit base")
        + "\n"
        + _global_entry(1001, "- [T-1000] (1000)\n", title="four digit carry")
    )
    worklog = _synthetic_worklog(
        _global_entry(1002, "- [T-1000] (1001)\n", title="four digit latest")
    )
    ordinal, active = spool_fold._extract_latest_active(
        worklog, {"worklog-global-four-digit.md": archive}
    )
    assert ordinal == 1002
    assert [(item.task_id, item.substantive_digest) for item in active] == [
        ("[T-1000]", _digest(substantive))
    ]


def test_compact_carry_uses_explicit_prior_across_ordinal_gap(tmp_path: Path) -> None:
    """current 末尾 (5) / archive max (9) / new (10) で carry は (5) を保持する。"""

    repo = _repo(tmp_path)
    substantive = "- [T-001] current-five\n"
    _write(repo / "docs/worklog.md", _synthetic_worklog(_global_entry(5, substantive)))
    _write(
        repo / "docs/archive/worklog-global-max.md",
        _global_entry(9, "- [T-999] archive-nine\n"),
    )
    _commit(repo, "ordinal gap canonical fixture")
    _fragment(repo, "worklog", _worklog_body(repo, carry=()))
    first = _plan_for_commit(repo, fold_date="2026-08-02")
    first_text = _target(first, "docs/worklog.md").after_bytes.decode("utf-8")
    assert "## 2026-08-02 (10) — fold test" in first_text
    assert _next_action(_entry(first_text, 10)) == (
        f"{_GENERATED_NEXT_ACTION_HEADING}\n\n- [T-001] (5)\n"
    )

    _finish_fold(repo, first)
    _fragment(
        repo,
        "worklog",
        _worklog_body(
            repo,
            carry=(),
            updated=(("[T-001]", "gap 後の更新", _digest(substantive)),),
        ),
        authored="2026-08-03",
        wave="wave-b",
    )
    second = spool_fold.plan_fold(repo, fold_date="2026-08-03")
    second_text = _target(second, "docs/worklog.md").after_bytes.decode("utf-8")
    assert "- [T-001] gap 後の更新" in _next_action(_entry(second_text, 11))


def test_two_worklog_fragments_use_immediate_prior_ordinals(tmp_path: Path) -> None:
    """同一 fold の第 2 entry は第 1 entry を carry し、apply 後も更新本文へ解決する。"""

    repo = _repo(tmp_path)
    original = _active_block("[T-001]")
    updated = "- [T-001] A の更新\n"
    _fragment(
        repo,
        "worklog",
        _worklog_body(
            repo,
            carry=(),
            updated=(("[T-001]", "A の更新", _digest(original)),),
        ),
        seq=1,
    )
    _fragment(repo, "worklog", _worklog_body(repo, carry=()), seq=2)
    first = _plan_for_commit(repo, fold_date="2026-08-02")
    first_text = _target(first, "docs/worklog.md").after_bytes.decode("utf-8")
    assert "- [T-001] A の更新" in _next_action(_entry(first_text, 2))
    assert _next_action(_entry(first_text, 3)) == (
        f"{_GENERATED_NEXT_ACTION_HEADING}\n\n- [T-001] (2)\n"
    )

    _finish_fold(repo, first)
    _fragment(
        repo,
        "worklog",
        _worklog_body(
            repo,
            carry=(),
            updated=(("[T-001]", "B の更新", _digest(updated)),),
        ),
        authored="2026-08-03",
        wave="wave-b",
    )
    second = spool_fold.plan_fold(repo, fold_date="2026-08-03")
    second_text = _target(second, "docs/worklog.md").after_bytes.decode("utf-8")
    assert "- [T-001] B の更新" in _next_action(_entry(second_text, 4))


def test_compact_carry_crosses_rotation_archive_boundary(tmp_path: Path) -> None:
    """current の compact carry が archive の明示 ordinal にある実体を解決する。"""

    repo = _repo(tmp_path)
    substantive = "- [T-001] archived substantive\n"
    _write(
        repo / "docs/archive/worklog-rotated.md",
        _global_entry(1, substantive, title="rotated target"),
    )
    _write(
        repo / "docs/worklog.md",
        _synthetic_worklog(_global_entry(2, "- [T-001] (1)\n", title="current")),
    )
    _fragment(
        repo,
        "worklog",
        _worklog_body(
            repo,
            carry=(),
            updated=(("[T-001]", "archive 境界後の更新", _digest(substantive)),),
        ),
    )
    plan = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    rendered = _target(plan, "docs/worklog.md").after_bytes.decode("utf-8")
    assert "- [T-001] archive 境界後の更新" in _next_action(_entry(rendered, 3))


def test_rotation_between_two_new_entries_preserves_compact_chain(tmp_path: Path) -> None:
    """rotation apply 後の第 2 fold が archive 内の元実体 digest まで到達する。"""

    repo = _repo(tmp_path, limit=100_000)
    substantive = _active_block("[T-001]")
    original = _synthetic_worklog(
        _global_entry(1, substantive, title="first"),
        _global_entry(
            2,
            substantive,
            title="latest original " + ("capacity filler " * 32),
        ),
    )
    _write(repo / "docs/worklog.md", original)
    _fragment(repo, "worklog", _worklog_body(repo, carry=(), prose="- projected entry"))

    preview = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    projected = _target(preview, "docs/worklog.md").after_bytes
    projected_text = projected.decode("utf-8")
    projected_entries = list(spool_fold.WORKLOG_ENTRY_RE.finditer(projected_text))
    assert [entry.group("ordinal") for entry in projected_entries] == ["1", "2", "3"]
    first_start = len(projected_text[: projected_entries[0].start()].encode("utf-8"))
    second_start = len(projected_text[: projected_entries[1].start()].encode("utf-8"))
    third_start = len(projected_text[: projected_entries[2].start()].encode("utf-8"))
    expected_current = projected[:first_start] + projected[third_start:]
    current_after_moving_only_first = projected[:first_start] + projected[second_start:]
    limit = 400
    assert len(expected_current) < limit
    assert len(current_after_moving_only_first) > limit
    _write(repo / "tools/check_docs.py", f"WORKLOG_ROTATE_BYTES = {limit}\n")
    _commit(repo, "rotation capacity fixture")

    first = _plan_for_commit(repo, fold_date="2026-08-02")
    assert first.rotation_path is not None
    archived = _target(first, first.rotation_path).after_bytes.decode("utf-8")
    current = _target(first, "docs/worklog.md").after_bytes.decode("utf-8")
    assert [entry.group("ordinal") for entry in spool_fold.WORKLOG_ENTRY_RE.finditer(archived)] == ["1", "2"]
    assert [entry.group("ordinal") for entry in spool_fold.WORKLOG_ENTRY_RE.finditer(current)] == ["3"]
    assert _next_action(_entry(current, 3)) == (
        f"{_GENERATED_NEXT_ACTION_HEADING}\n\n- [T-001] (2)\n"
    )
    _finish_fold(repo, first)

    _fragment(
        repo,
        "worklog",
        _worklog_body(
            repo,
            carry=(),
            updated=(("[T-001]", "rotation 後の更新", _digest(substantive)),),
        ),
        authored="2026-08-03",
        wave="wave-b",
    )
    second = spool_fold.plan_fold(repo, fold_date="2026-08-03")
    second_text = _target(second, "docs/worklog.md").after_bytes.decode("utf-8")
    assert "- [T-001] rotation 後の更新" in _next_action(_entry(second_text, 4))


def test_non_active_transition_target_remains_rejected(tmp_path: Path) -> None:
    """active でない ID への明示操作は暗黙 carry 導入後も fail-closed。"""

    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo, carry=("[T-999]",)))
    _raises("transition-target", spool_fold.plan_fold, repo)


def test_n10_stale_base_digest_is_rejected(tmp_path: Path) -> None:
    """N10: authoring 後に変わった item への stale 更新を拒否する。"""

    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo, carry=(), updated=(("[T-001]", "更新後", "0" * 64),)))
    _raises("base-mismatch", spool_fold.plan_fold, repo)


def test_n10_mutating_action_requires_base_field(tmp_path: Path) -> None:
    """N10: 完了/更新/見送り操作は base field 自体を必須とする。"""

    repo = _repo(tmp_path)
    body = "## 本文\n\n- body\n\n## 次の一手差分\n\n### 更新\n\n- [T-001] 更新後\n"
    _fragment(repo, "worklog", body)
    issues = spool_fold.validate_spool_tree(repo)
    assert [issue.code for issue in issues] == ["base"]


def test_all_mutating_operation_blocks_resolve_placeholders(tmp_path: Path) -> None:
    """F-3: 更新・完了・見送りの sink に placeholder を素通ししない。"""

    repo = _repo(tmp_path, active=("[T-001]", "[T-002]", "[T-003]"))
    _fragment(repo, "decisions", "## {{D:shared}}. shared\n", wave="same-wave")
    body = _worklog_body(
        repo,
        carry=(),
        completed=(("[T-001]", "完了 {{D:shared}}", _digest(_active_block("[T-001]"))),),
        completion_remaining=True,
        updated=(("[T-002]", "更新 {{D:shared}}", _digest(_active_block("[T-002]"))),),
        deferred=(("研究・計測系", "[T-003]", "見送り — 理由: {{D:shared}}", _digest(_active_block("[T-003]"))),),
    )
    _fragment(repo, "worklog", body, wave="same-wave")
    plan = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    rendered = b"\n".join(target.after_bytes for target in plan.targets)
    assert b"{{" not in rendered and b"}}" not in rendered
    assert rendered.count(b"D2") >= 4


def test_worklog_reserved_heading_in_prose_is_rejected(tmp_path: Path) -> None:
    """F-3(a): renderer が `次の一手` を二重生成する入力を plan 前に拒否する。"""

    repo = _repo(tmp_path)
    _fragment(
        repo,
        "worklog",
        _worklog_body(repo, prose="- 本文\n\n### 次の一手\n\n- injected"),
    )
    codes = [issue.code for issue in spool_fold.validate_spool_tree(repo)]
    assert "worklog-prose-heading" in codes


def test_worklog_action_prefix_payload_is_not_dropped(tmp_path: Path) -> None:
    """F-4 横展開: action item 前の非空 payload を receipt/GC の前に拒否する。"""

    repo = _repo(tmp_path)
    body = (
        "## 本文\n\n- body\n\n## 次の一手差分\n\n"
        "### 更新\n\n未解釈 payload\n\n"
        f"- [T-001] 更新\n  base: {_digest(_active_block('[T-001]'))}\n"
    )
    _fragment(repo, "worklog", body)
    codes = [issue.code for issue in spool_fold.validate_spool_tree(repo)]
    assert "worklog-action-content" in codes


def test_failure_section_payload_without_valid_h3_is_rejected(tmp_path: Path) -> None:
    """F-4: `新規` の H3 前 payload と有効 entry 0 件を両方検出する。"""

    repo = _repo(tmp_path)
    _fragment(repo, "failures", "## 新規\n\n- dropped payload\n")
    codes = [issue.code for issue in spool_fold.validate_spool_tree(repo)]
    assert codes == ["failure-new-empty", "failure-unconsumed"]


def test_failure_supersede_only_fragment_inserts_at_entry_end_byte_exact(tmp_path: Path) -> None:
    """M1/M10: supersede 単独を受理し、fold が `- ` を付けて境界へ exact splice する。"""

    repo = _repo(tmp_path)
    failures = repo / "docs/failures.md"
    with failures.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write("### F2. second [手順漏れ]\n- 事象: second\n")
    before = failures.read_bytes()
    body = _supersede("F1 だけを更新。")
    _fragment(repo, "failures", _failure_body(supersedes=((1, body),)))
    offset = before.index(b"### F2.")
    line = f"- {body}".encode()
    assert _failures_after(repo) == _splice_exact(before, ((offset, line + b"\n"),))


def test_failure_recurrence_precedes_supersede_for_same_target_byte_exact(tmp_path: Path) -> None:
    """M4: 同一 F では再発全件の後に supersede 全件を置く。"""

    repo = _repo(tmp_path)
    before = (repo / "docs/failures.md").read_bytes()
    recurrence = "- **再発: 2026-08-10** — 再発を先に置く。"
    supersede = _supersede("supersede を後に置く。")
    _fragment(
        repo,
        "failures",
        _failure_body(
            recurrences=((1, recurrence),),
            supersedes=((1, supersede),),
        ),
    )
    expected = before + f"\n{recurrence}\n- {supersede}\n".encode()
    assert _failures_after(repo) == expected


def test_failure_supersede_order_is_deterministic_by_fragment_key_and_item_index(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(
        repo,
        "failures",
        _failure_body(supersedes=((1, _supersede("A10")),)),
        wave="wave-a",
        seq=10,
    )
    _fragment(
        repo,
        "failures",
        _failure_body(supersedes=(
            (1, _supersede("A2-first")),
            (1, _supersede("A2-second")),
        )),
        wave="wave-a",
        seq=2,
    )
    _fragment(
        repo,
        "failures",
        _failure_body(supersedes=((1, _supersede("B1")),)),
        wave="wave-b",
        seq=1,
    )
    first = spool_fold.plan_fold(repo, fold_date="2026-08-10")
    second = spool_fold.plan_fold(repo, fold_date="2026-08-10")
    rendered = _target(first, "docs/failures.md").after_bytes.decode()
    assert first.as_dict() == second.as_dict()
    assert [rendered.index(label) for label in ("A2-first", "A2-second", "A10", "B1")] == sorted(
        rendered.index(label) for label in ("A2-first", "A2-second", "A10", "B1")
    )


def test_failure_supersede_body_resolves_cross_ledger_placeholder(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "decisions", "## {{D:reason}}. reason\n", wave="same-wave")
    _fragment(
        repo,
        "failures",
        _failure_body(supersedes=((1, _supersede("根拠 {{D:reason}}")),)),
        wave="same-wave",
    )
    rendered = _failures_after(repo).decode()
    assert "- **supersede: 2026-08-10** — 根拠 D2\n" in rendered
    assert "{{" not in rendered and "}}" not in rendered


def test_failure_supersede_target_placeholder_is_rejected(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    new_entry = (
        "### {{F:future}}. future [手順漏れ]\n"
        "- 事象: x\n- 根本原因: x\n- 恒久対応: x\n- 再発検知: x\n"
    )
    body = _failure_body(new=(new_entry,)) + (
        "\n## supersede 追記\n\n"
        f"- {{{{F:future}}}} {_supersede('placeholder target')}\n"
    )
    _fragment(repo, "failures", body)
    assert [issue.code for issue in spool_fold.validate_spool_tree(repo)] == [
        "failure-supersede-shape"
    ]


def test_failure_supersede_section_order_and_uniqueness_are_rejected(tmp_path: Path) -> None:
    cases = (
        (
            "## supersede 追記\n\n"
            f"- F1 {_supersede('先行')}\n\n"
            "## 再発\n\n### F1\n\n- **再発: 2026-08-10** — 後続\n"
        ),
        (
            "## supersede 追記\n\n"
            f"- F1 {_supersede('一件目')}\n\n"
            "## supersede 追記\n\n"
            f"- F1 {_supersede('二件目')}\n"
        ),
    )
    for index, body in enumerate(cases):
        parent = tmp_path / f"case-{index}"
        parent.mkdir()
        repo = _repo(parent)
        _fragment(repo, "failures", body)
        assert "failure-sections" in [
            issue.code for issue in spool_fold.validate_spool_tree(repo)
        ]


def test_empty_failure_supersede_section_is_rejected(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "failures", "## supersede 追記\n")
    assert [issue.code for issue in spool_fold.validate_spool_tree(repo)] == [
        "failure-supersede-empty"
    ]


def test_multiline_h3_and_base_failure_supersede_shapes_are_rejected(tmp_path: Path) -> None:
    cases = (
        f"- F1 {_supersede('一行目')}\n  継続行",
        "### F1\n\n" + _supersede("H3"),
        f"- F1 {_supersede('base')}\n  base: {'0' * 64}",
    )
    for index, item in enumerate(cases):
        parent = tmp_path / f"case-{index}"
        parent.mkdir()
        repo = _repo(parent)
        _fragment(repo, "failures", f"## supersede 追記\n\n{item}\n")
        codes = [issue.code for issue in spool_fold.validate_spool_tree(repo)]
        assert codes and set(codes) == {"failure-supersede-shape"}


def test_failure_supersede_body_shape_and_calendar_date_are_rejected(tmp_path: Path) -> None:
    """M6: label・区切り・本文・暦日のどれかが不正なら専用 shape issue。"""

    items = (
        "- F1 stale",
        "- F1 - **supersede: 2026-08-10** — fold が付ける marker を本文へ書いた",
        "- F01 **supersede: 2026-08-10** — non-canonical target",
        "- F1 **supersede: 2026-13-45** — x",
        "- F1 **supersede: 2026-08-10** —",
        "- F1 **supersede: 2026-08-10** —    ",
        "- F1 **supersede: 2026-08-10** - x",
    )
    for index, item in enumerate(items):
        parent = tmp_path / f"case-{index}"
        parent.mkdir()
        repo = _repo(parent)
        _fragment(repo, "failures", f"## supersede 追記\n\n{item}\n")
        assert [issue.code for issue in spool_fold.validate_spool_tree(repo)] == [
            "failure-supersede-shape"
        ]


def test_failure_supersede_unicode_line_breaks_are_rejected(tmp_path: Path) -> None:
    separators = ("\u2028", "\u2029", "\u0085", "\r", "\v", "\f")
    for index, separator in enumerate(separators):
        parent = tmp_path / f"case-{index}"
        parent.mkdir()
        repo = _repo(parent)
        _fragment(
            repo,
            "failures",
            _failure_body(supersedes=((1, _supersede(f"before{separator}after")),)),
        )
        assert "failure-supersede-shape" in [
            issue.code for issue in spool_fold.validate_spool_tree(repo)
        ]


def test_failure_supersede_accepted_body_is_preserved_byte_exact(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    before = (repo / "docs/failures.md").read_bytes()
    body = _supersede("zero-width:\u200b word-joiner:\u2060 emoji:🧭")
    _fragment(repo, "failures", _failure_body(supersedes=((1, body),)))
    assert _failures_after(repo) == before + f"- {body}\n".encode()


def test_failure_supersede_missing_target_is_rejected(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "failures", _failure_body(supersedes=((999, _supersede("不存在")),)))
    _raises("failure-supersede-missing", spool_fold.plan_fold, repo)


def test_failure_supersede_rejects_duplicate_canonical_target_ids(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    with (repo / "docs/failures.md").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write("\n### F1. duplicate [手順漏れ]\n- 事象: duplicate\n")
    _fragment(repo, "failures", _failure_body(supersedes=((1, _supersede("一意性")),)))
    _raises("failure-duplicate", spool_fold.plan_fold, repo)


def test_failure_supersede_rejects_existing_identical_line(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    body = _supersede("既存と同一。")
    with (repo / "docs/failures.md").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(f"- {body}\n")
    _fragment(repo, "failures", _failure_body(supersedes=((1, body),)))
    _raises("failure-supersede-duplicate-line", spool_fold.plan_fold, repo)


def test_failure_supersede_rejects_duplicate_line_within_same_fold(tmp_path: Path) -> None:
    body = _supersede("fold 内重複。")
    for across_fragments in (False, True):
        parent = tmp_path / ("across" if across_fragments else "within")
        parent.mkdir()
        repo = _repo(parent)
        if across_fragments:
            _fragment(repo, "decisions", "## {{D:reason}}. reason\n", wave="same-wave")
            _fragment(
                repo,
                "failures",
                _failure_body(supersedes=((1, _supersede("根拠 D2")),)),
                wave="same-wave",
                seq=1,
            )
            _fragment(
                repo,
                "failures",
                _failure_body(supersedes=((1, _supersede("根拠 {{D:reason}}")),)),
                wave="same-wave",
                seq=2,
            )
        else:
            _fragment(repo, "failures", _failure_body(supersedes=((1, body), (1, body))))
        _raises("failure-supersede-duplicate-line", spool_fold.plan_fold, repo)


def test_failure_recurrence_and_supersede_identical_line_are_rejected(tmp_path: Path) -> None:
    """R5: recurrence 適用後の exact 行を supersede helper が重複として拒否する。"""

    repo = _repo(tmp_path)
    body = _supersede("cross-section 同一行。")
    failures = (repo / "docs/failures.md").read_text(encoding="utf-8")
    after_recurrence = spool_fold._insert_failure_recurrences(
        failures,
        ((1, f"- {body}\n"),),
    )
    _raises(
        "failure-supersede-duplicate-line",
        spool_fold._insert_failure_supersedes,
        after_recurrence,
        (spool_fold._FailureSupersede(1, body),),
    )


def test_failure_supersede_substring_of_existing_line_is_accepted(tmp_path: Path) -> None:
    """M5: byte-exact でない部分一致を過剰拒否しない。"""

    repo = _repo(tmp_path)
    body = _supersede("短い本文")
    with (repo / "docs/failures.md").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(f"- {body}だが既存行は長い\n")
    _fragment(repo, "failures", _failure_body(supersedes=((1, body),)))
    assert f"- {body}\n" in _failures_after(repo).decode()


def test_failure_recurrence_supersede_misuse_is_rejected_but_prose_mention_is_accepted(tmp_path: Path) -> None:
    """M8/R4: reserved list prefix だけを拒否し、本文中の語は既存受理集合に残す。"""

    misuses = (
        "- **supersede: 2026-08-10** — 誤用",
        "- **super<!--internal-->sede: 2026-08-10** — 誤用",
        "- <!--before-label-->**supersede: 2026-08-10** — 誤用",
        "<!--before-item-->- **supersede: 2026-08-10** — 誤用",
        "- **supersede<!--after-label-->: 2026-08-10** — 誤用",
        "- **supersede:<!--after-prefix--> 2026-08-10** — 誤用",
        " - **supersede: 2026-08-10** — 誤用",
        "  - **supersede: 2026-08-10** — 誤用",
        "   - **supersede: 2026-08-10** — 誤用",
        "-\t**supersede: 2026-08-10** — 誤用",
        "- **super\u200bsede: 2026-08-10** — 誤用",
        "- **super\u200csede: 2026-08-10** — 誤用",
        "- **super\u200dsede: 2026-08-10** — 誤用",
        "- **super\u2060sede: 2026-08-10** — 誤用",
        "- **super\ufeffsede: 2026-08-10** — 誤用",
    )
    for index, payload in enumerate(misuses):
        bad_parent = tmp_path / f"bad-{index}"
        bad_parent.mkdir()
        bad = _repo(bad_parent)
        _fragment(
            bad,
            "failures",
            _failure_body(recurrences=((1, payload),)),
        )
        assert [issue.code for issue in spool_fold.validate_spool_tree(bad)] == [
            "failure-recurrence-supersede-misuse"
        ]

    fenced_parent = tmp_path / "fenced"
    fenced_parent.mkdir()
    fenced = _repo(fenced_parent)
    fenced_payload = (
        "```markdown\n"
        "- **supersede: 2026-08-10** — fence 内 decoy\n"
        "```"
    )
    _fragment(fenced, "failures", _failure_body(recurrences=((1, fenced_payload),)))
    assert spool_fold.validate_spool_tree(fenced) == []

    accepted = (
        "    - **supersede: 2026-08-10** — 4-space indent code block",
        "- **ｓｕｐｅｒｓｅｄｅ: 2026-08-10** — ASCII 予約ラベルではない",
        "- **再発: 2026-08-10** — supersede 追記が無く記録が遅れた。",
    )
    for index, payload in enumerate(accepted):
        good_parent = tmp_path / f"good-{index}"
        good_parent.mkdir()
        good = _repo(good_parent)
        _fragment(good, "failures", _failure_body(recurrences=((1, payload),)))
        assert spool_fold.validate_spool_tree(good) == []
        assert payload in _failures_after(good).decode()


def test_failure_topology_rejects_forged_heading_from_recurrence(tmp_path: Path) -> None:
    """M7: upstream parser が壊れても plan の描画後 topology が偽 F heading を拒否する。"""

    repo = _repo(tmp_path)
    _fragment(
        repo,
        "failures",
        _failure_body(recurrences=((1, "- **再発: 2026-08-10** — seed"),)),
    )
    original = spool_fold._failure_parts
    spool_fold._failure_parts = lambda *_args: ([], [(1, "### F999. forged\n")], [])
    try:
        _raises("failure-topology", spool_fold.plan_fold, repo)
    finally:
        spool_fold._failure_parts = original


def test_failure_list_marker_neutralizes_heading_if_shape_gate_regresses(tmp_path: Path) -> None:
    """M9: R2 が破れても R1 が raw heading を list item 化し topology を保存する。"""

    repo = _repo(tmp_path)
    _fragment(repo, "failures", _failure_body(supersedes=((1, _supersede("seed")),)))
    original = spool_fold._failure_parts
    spool_fold._failure_parts = lambda *_args: (
        [],
        [],
        [spool_fold._FailureSupersede(1, "### F999. forged")],
    )
    try:
        rendered = _failures_after(repo).decode()
    finally:
        spool_fold._failure_parts = original
    assert "\n- ### F999. forged\n" in rendered
    assert [int(match.group("number")) for match in spool_fold.FAILURE_ID_RE.finditer(rendered)] == [1]


def test_failure_topology_accepts_mixed_new_recurrence_and_supersede(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    first_new_entry = (
        "### {{F:first}}. first [手順漏れ]\n"
        "- 事象: x\n- 根本原因: x\n- 恒久対応: x\n- 再発検知: x\n"
    )
    second_new_entry = (
        "### {{F:second}}. second [手順漏れ]\n"
        "- 事象: x\n- 根本原因: x\n- 恒久対応: x\n- 再発検知: x\n"
    )
    _fragment(
        repo,
        "failures",
        _failure_body(
            new=(first_new_entry, second_new_entry),
            recurrences=((1, "- **再発: 2026-08-10** — mixed"),),
            supersedes=((1, _supersede("mixed")),),
        ),
    )
    rendered = _failures_after(repo).decode()
    assert [int(match.group("number")) for match in spool_fold.FAILURE_ID_RE.finditer(rendered)] == [1, 2, 3]


def test_failure_topology_uses_new_entry_append_order_across_fragments(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    first_path_entry = (
        "### {{F:first-path}}. first path [手順漏れ]\n"
        "- 事象: x\n- 根本原因: x\n- 恒久対応: x\n- 再発検知: x\n"
    )
    second_path_entry = (
        "### {{F:second-path}}. second path [手順漏れ]\n"
        "- 事象: x\n- 根本原因: x\n- 恒久対応: x\n- 再発検知: x\n"
    )
    _fragment(
        repo,
        "failures",
        "## 新規\n\n\n\n" + first_path_entry,
        authored="2026-08-01",
        wave="same-wave",
        seq=1,
    )
    _fragment(
        repo,
        "failures",
        _failure_body(new=(second_path_entry,)),
        authored="2026-08-02",
        wave="same-wave",
        seq=1,
    )
    assert spool_fold.validate_spool_tree(repo) == []
    rendered = _failures_after(repo).decode()
    assert [
        int(match.group("number"))
        for match in spool_fold.FAILURE_ID_RE.finditer(rendered)
    ] == [1, 3, 2]
    assert rendered.index("### F3. first path") < rendered.index("### F2. second path")


def test_failure_supersede_replay_guards_exact_and_changed_fragments(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    body = _failure_body(supersedes=((1, _supersede("replay")),))
    fragment = _fragment(repo, "failures", body)
    raw = fragment.read_bytes()
    _complete_fold(repo, fold_date="2026-08-10")
    fragment.parent.mkdir(parents=True, exist_ok=True)
    fragment.write_bytes(raw)
    _raises("receipt-replay", spool_fold.plan_fold, repo)
    fragment.unlink()
    _fragment(repo, "failures", body, seq=2)
    _raises("failure-supersede-duplicate-line", spool_fold.plan_fold, repo)


def test_failure_new_and_recurrence_only_output_remains_byte_exact(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    before = (repo / "docs/failures.md").read_bytes()
    recurrence = "- **再発: 2026-08-10** — legacy path"
    new_entry = (
        "### {{F:new}}. new [手順漏れ]\n"
        "- 事象: x\n- 根本原因: x\n- 恒久対応: x\n- 再発検知: x\n"
    )
    _fragment(
        repo,
        "failures",
        _failure_body(new=(new_entry,), recurrences=((1, recurrence),)),
    )
    expected = before + f"\n{recurrence}\n\n".encode() + new_entry.replace("{{F:new}}", "F2").encode()
    assert _failures_after(repo) == expected


def test_failure_supersede_real_f1_boundary_without_blank_line_is_byte_exact(tmp_path: Path) -> None:
    repo = _copy_real_canonical_family(tmp_path)
    before = (repo / "docs/failures.md").read_bytes()
    boundary = re.search(rb"^### F2\.", before, re.MULTILINE)
    assert boundary is not None
    assert before[:boundary.start()].endswith(b"\n")
    assert not before[:boundary.start()].endswith(b"\n\n")
    body = _supersede("実 canonical の空行なし境界。")
    _fragment(repo, "failures", _failure_body(supersedes=((1, body),)))
    expected = _splice_exact(before, ((boundary.start(), f"- {body}\n".encode()),))
    with _fixture_tools_imports(repo):
        assert _failures_after(repo) == expected


def test_failure_supersede_real_f196_f197_boundary_is_byte_exact(tmp_path: Path) -> None:
    """M2: F197 見出しから挿入 offset を動的に求める実 canonical golden。"""

    repo = _copy_real_canonical_family(tmp_path)
    before = (repo / "docs/failures.md").read_bytes()
    boundary = re.search(rb"^### F197\.", before, re.MULTILINE)
    assert boundary is not None
    assert before[:boundary.start()].endswith(b"\n\n")
    assert not before[:boundary.start()].endswith(b"\n\n\n")
    body = _supersede("実 canonical の F196/F197 境界。")
    _fragment(repo, "failures", _failure_body(supersedes=((196, body),)))
    expected = _splice_exact(before, ((boundary.start() - 1, f"- {body}\n".encode()),))
    with _fixture_tools_imports(repo):
        assert _failures_after(repo) == expected


def test_failure_supersede_real_final_entry_eof_is_byte_exact(tmp_path: Path) -> None:
    """M3: 最終 F の offset は既存末尾 LF の後ろである。"""

    repo = _copy_real_canonical_family(tmp_path)
    before = (repo / "docs/failures.md").read_bytes()
    headings = list(spool_fold.FAILURE_ID_RE.finditer(before.decode()))
    assert headings and before.endswith(b"\n") and not before.endswith(b"\n\n")
    assert spool_fold.FAILURE_ID_RE.search(before.decode(), headings[-1].end()) is None
    number = int(headings[-1].group("number"))
    body = _supersede("実 canonical の EOF 境界。")
    _fragment(repo, "failures", _failure_body(supersedes=((number, body),)))
    expected = _splice_exact(before, ((len(before), f"- {body}\n".encode()),))
    with _fixture_tools_imports(repo):
        assert _failures_after(repo) == expected


def test_n11_existing_canonical_bytes_are_only_appended_or_inserted(tmp_path: Path) -> None:
    """N11: parse/re-serialize で既存 canonical bytes を変更しない。"""

    repo = _repo(tmp_path)
    before = {rel: (repo / rel).read_bytes() for rel in ("docs/worklog.md", "docs/phase3.md", "docs/decisions.md", "docs/failures.md")}
    base = _digest(_active_block("[T-001]"))
    body = _worklog_body(repo, carry=(), deferred=(("プロセス文書系", "[T-001]", "見送り — 理由: 固定", base),))
    _fragment(repo, "worklog", body)
    plan = spool_fold.plan_fold(repo)
    assert _target(plan, "docs/worklog.md").after_bytes.startswith(before["docs/worklog.md"])
    phase_after = _target(plan, "docs/phase3.md").after_bytes
    inserted = b"- [T-001] \xe8\xa6\x8b\xe9\x80\x81\xe3\x82\x8a \xe2\x80\x94 \xe7\x90\x86\xe7\x94\xb1: \xe5\x9b\xba\xe5\xae\x9a\n\n"
    assert phase_after.replace(inserted, b"", 1) == before["docs/phase3.md"]
    assert (repo / "docs/decisions.md").read_bytes() == before["docs/decisions.md"]
    assert (repo / "docs/failures.md").read_bytes() == before["docs/failures.md"]


def test_n12_second_fold_after_gc_is_noop(tmp_path: Path) -> None:
    """N12: 成功適用後の 2 回目は canonical を二重追記しない。"""

    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    _commit(repo, "fragment")
    first = _plan_for_commit(repo)
    result = _finish_fold(repo, first)
    after = (repo / "docs/worklog.md").read_bytes()
    second = spool_fold.plan_fold(repo)
    assert result.status == "applied" and second.status == "noop"
    assert (repo / "docs/worklog.md").read_bytes() == after


def test_n13_same_content_replay_is_rejected_by_receipt(tmp_path: Path) -> None:
    """N13: GC 後に同一内容を再投入しても receipt が再採番を拒否する。"""

    repo = _repo(tmp_path)
    path = _fragment(repo, "worklog", _worklog_body(repo))
    raw = path.read_bytes()
    _commit(repo, "fragment")
    _complete_fold(repo)
    path.write_bytes(raw)
    _raises("receipt-replay", spool_fold.plan_fold, repo)


def test_changed_content_cannot_reuse_folded_symbol_identity(tmp_path: Path) -> None:
    """C-03: content-sha を変えても (wave, namespace, slug) の耐久 identity は再利用不可。"""

    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo, new=(("durable", "first"),)))
    _commit(repo, "first fragment")
    _complete_fold(repo)
    body = _worklog_body(repo, carry=("[T-001]", "[T-052]"), new=(("durable", "changed"),))
    _fragment(repo, "worklog", body, seq=2)
    _raises("symbol-replay", spool_fold.plan_fold, repo)


def test_n14_rotation_keeps_projected_worklog_under_shared_limit(tmp_path: Path) -> None:
    """N14: 閾値超過時に fold 自身がローテーションする。"""

    repo = _repo(tmp_path, limit=320)
    original = (repo / "docs/worklog.md").read_text(encoding="utf-8")
    second = "\n## 2026-08-01 (2) — second seed with sufficient bytes\n\n- body body body body\n\n### 次の一手\n\n- [T-001] 現本文 [T-001]\n"
    _write(repo / "docs/worklog.md", original.replace("## 2026-08-01 (1)", "## 2026-08-01 (1)") + second)
    _fragment(repo, "worklog", _worklog_body(repo, prose="- x"))
    plan = spool_fold.plan_fold(repo)
    assert plan.rotation_path is not None
    assert len(_target(plan, "docs/worklog.md").after_bytes) <= 320


def test_rotation_can_archive_original_latest_to_fit_projected_entry(tmp_path: Path) -> None:
    """F1: 新 entry だけを現行に残す分割点まで元 latest を連続移動できる。"""

    repo = _repo(tmp_path, limit=100_000)
    with (repo / "docs/worklog.md").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(
            "\n## 2026-08-01 (2) — latest original entry\n\n"
            + "- latest body "
            + ("capacity bytes " * 30)
            + "\n\n### 次の一手\n\n- [T-001] 現本文 [T-001]\n"
        )
    original = (repo / "docs/worklog.md").read_bytes()
    _fragment(repo, "worklog", _worklog_body(repo, prose="- projected entry"))

    preview = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    projected = _target(preview, "docs/worklog.md").after_bytes
    projected_text = projected.decode("utf-8")
    projected_entries = list(spool_fold.WORKLOG_ENTRY_RE.finditer(projected_text))
    assert [entry.group("ordinal") for entry in projected_entries] == ["1", "2", "3"]
    first_entry_start = len(projected_text[: projected_entries[0].start()].encode("utf-8"))
    second_entry_start = len(projected_text[: projected_entries[1].start()].encode("utf-8"))
    new_entry_start = len(projected_text[: projected_entries[2].start()].encode("utf-8"))
    expected_current = projected[:first_entry_start] + projected[new_entry_start:]
    old_split_current = projected[:first_entry_start] + projected[second_entry_start:]
    limit = len(expected_current)
    assert len(old_split_current) > limit
    _write(repo / "tools/check_docs.py", f"WORKLOG_ROTATE_BYTES = {limit}\n")
    _commit(repo, "capacity fixture")

    plan = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    assert plan.rotation_path is not None
    archive = _target(plan, plan.rotation_path).after_bytes
    current = _target(plan, "docs/worklog.md").after_bytes
    assert archive.rstrip(b"\n") == original[first_entry_start:].rstrip(b"\n")
    archive_entries = list(spool_fold.WORKLOG_ENTRY_RE.finditer(archive.decode("utf-8")))
    assert [entry.group("ordinal") for entry in archive_entries] == ["1", "2"]
    assert current == expected_current
    assert len(current) <= limit
    archive_latest_ids = set(
        spool_fold.TASK_RE.findall(_next_action(_entry(archive.decode("utf-8"), 2)))
    )
    current_first_ids = set(
        spool_fold.TASK_RE.findall(_next_action(_entry(current.decode("utf-8"), 3)))
    )
    assert archive_latest_ids == current_first_ids == {"[T-001]"}

    result = spool_fold.apply_fold(repo, plan)
    assert result.status == "applied"
    assert (repo / "docs/worklog.md").read_bytes() == current
    assert (repo / plan.rotation_path).read_bytes() == archive


def test_n15_rotation_updates_archive_index(tmp_path: Path) -> None:
    """N15: 新 archive file を README の現在の収容物へ同 transaction で載せる。"""

    repo = _repo(tmp_path, limit=320)
    with (repo / "docs/worklog.md").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("\n## 2026-08-01 (2) — second seed with sufficient bytes\n\n- body body body body\n\n### 次の一手\n\n- [T-001] 現本文 [T-001]\n")
    _fragment(repo, "worklog", _worklog_body(repo))
    plan = spool_fold.plan_fold(repo)
    assert plan.rotation_path is not None
    index = _target(plan, "docs/archive/README.md").after_bytes.decode()
    assert f"`{Path(plan.rotation_path).name}`" in index


def test_n16_transaction_rejects_third_state(tmp_path: Path) -> None:
    """N16: state 永続化後の canonical 第三状態を上書きしない。"""

    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    _commit(repo, "fragment")
    plan = spool_fold.plan_fold(repo)
    state_path = spool_fold._state_path(repo)
    state = json.dumps(spool_fold._plan_state(plan), ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode() + b"\n"
    spool_fold._atomic_write(state_path, state)
    receipt_before = (repo / "docs/spool/FOLDED.md").read_bytes()
    with (repo / "docs/worklog.md").open("a", encoding="utf-8") as handle:
        handle.write("第三状態\n")
    try:
        spool_fold.apply_fold(repo, plan)
    except spool_fold.TransactionError as exc:
        assert "第三状態" in str(exc)
    else:
        raise AssertionError("第三状態を受理した")
    assert (repo / "docs/spool/FOLDED.md").read_bytes() == receipt_before


def test_interrupted_transaction_resumes_before_and_after_targets(tmp_path: Path) -> None:
    """transaction resume: after target は skip、before target は適用し、全 after 後だけ GC する。"""

    repo = _repo(tmp_path)
    _fragment(
        repo,
        "worklog",
        _worklog_body(repo, deferred_appends=(("[T-050]", " 発火記録: resume"),)),
    )
    _commit(repo, "fragment")
    plan = spool_fold.plan_fold(repo)
    state_path = spool_fold._state_path(repo)
    state = json.dumps(spool_fold._plan_state(plan), ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode() + b"\n"
    spool_fold._atomic_write(state_path, state)
    phase_target = _target(plan, "docs/phase3.md")
    spool_fold._atomic_write(repo / phase_target.path, phase_target.after_bytes)
    writes: list[Path] = []
    atomic_write = spool_fold._atomic_write

    def recording_atomic_write(path: Path, data: bytes) -> None:
        writes.append(path.resolve())
        atomic_write(path, data)

    spool_fold._atomic_write = recording_atomic_write
    try:
        result = spool_fold.apply_fold(repo, plan)
    finally:
        spool_fold._atomic_write = atomic_write
    assert result.status == "resumed" and phase_target.path in result.resumed_paths
    assert (repo / phase_target.path).resolve() not in writes
    assert all((repo / target.path).read_bytes() == target.after_bytes for target in plan.targets)
    assert all(not (repo / rel).exists() for rel in plan.gc_paths)
    assert state_path.is_file()
    stored = spool_fold._load_state(state_path)
    assert stored["phase"] == "applied"
    assert stored["transaction_id"] == plan.transaction_id


def test_plan_fold_observes_standalone_head_and_symbolic_ref(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    _commit(repo, "fragment")
    observed_head = _run_git(repo, "rev-parse", "HEAD")
    observed_ref = _run_git(repo, "symbolic-ref", "HEAD")

    plan = spool_fold.plan_fold(repo, fold_date="2026-08-02")

    assert dataclasses.fields(spool_fold.FoldOrigin)
    assert {field.name for field in dataclasses.fields(spool_fold.FoldOrigin)} == {
        "kind", "base", "tested_tip", "wave_ref", "rollback_ref",
        "trusted_main_cutoff", "audited_digest",
    }
    assert plan.origin == spool_fold.FoldOrigin(
        "standalone",
        observed_head,
        observed_head,
        observed_ref,
        observed_head,
        observed_head,
        spool_fold.audited_commit_digest(()),
    )


def test_plan_fold_rejects_origin_not_matching_observed_git(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    _commit(repo, "fragment")
    origin = _land_origin(repo)

    for changed in (
        dataclasses.replace(origin, tested_tip=origin.base),
        dataclasses.replace(origin, wave_ref="refs/heads/not-observed"),
        dataclasses.replace(origin, audited_digest="0" * 64),
    ):
        _raises("origin", spool_fold.plan_fold, repo, origin=changed)


def test_state_v3_schema_is_exact_and_v1_v2_are_rejected(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    plan = _plan_for_commit(repo, fold_date="2026-08-02")
    state = spool_fold._plan_state(plan)

    assert frozenset(state) == spool_fold.STATE_FIELDS
    assert frozenset(state["origin"]) == spool_fold.ORIGIN_FIELDS
    assert state["version"] == 3 and state["phase"] == "applied"
    assert all(frozenset(item) == spool_fold.FRAGMENT_STATE_FIELDS for item in state["fragments"])
    assert all(frozenset(item) == spool_fold.TARGET_STATE_FIELDS for item in state["targets"])
    for legacy_version in (1, 2):
        legacy = dict(state, version=legacy_version)
        _transaction_raises("version", spool_fold._state_plan, legacy)


def test_state_v2_rejects_missing_extra_and_coerced_nested_fields(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    plan = _plan_for_commit(repo)
    state = spool_fold._plan_state(plan)

    missing = dict(state)
    missing.pop("phase")
    extra = dict(state, unexpected=False)
    coerced = json.loads(json.dumps(state))
    coerced["fragments"][0]["seq"] = "1"
    coerced_bool = json.loads(json.dumps(state))
    coerced_bool["targets"][0]["before_exists"] = 1
    for candidate in (missing, extra, coerced, coerced_bool):
        _transaction_raises("transaction state", spool_fold._state_plan, candidate)


def test_transaction_id_binds_origin_closure_and_before_exists(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    plan = _plan_for_commit(repo)

    def transaction_id(
        *,
        origin=plan.origin,
        closure=plan.input_closure_sha256,
        targets=plan.targets,
    ):
        return spool_fold._plan_transaction_id(
            plan.fold_date,
            origin,
            closure,
            plan.fragments,
            plan.gc_paths,
            plan.projected_worklog_bytes,
            plan.rotation_path,
            targets,
        )

    first = plan.targets[0]
    changed_targets = (dataclasses.replace(first, before_exists=not first.before_exists), *plan.targets[1:])
    assert transaction_id() == plan.transaction_id
    assert transaction_id(closure="0" * 64) != plan.transaction_id
    origin_changes = (
        {"kind": "standalone"},
        {"base": "0" * 40},
        {"tested_tip": "1" * 40},
        {"wave_ref": "refs/heads/changed"},
        {"rollback_ref": "2" * 40},
        {"trusted_main_cutoff": "3" * 40},
        {"audited_digest": "4" * 64},
    )
    assert all(
        transaction_id(origin=dataclasses.replace(plan.origin, **change)) != plan.transaction_id
        for change in origin_changes
    )
    assert transaction_id(targets=changed_targets) != plan.transaction_id

    committed_state = spool_fold._plan_state(plan)
    committed_state["phase"] = "committed"
    assert spool_fold._state_plan(committed_state).transaction_id == plan.transaction_id


def test_apply_rejects_each_state_transaction_id_payload_field_mutation(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    plan = _plan_for_commit(repo)
    original_state = spool_fold._plan_state(plan)

    def mutate_gc_paths(state: dict[str, object]) -> None:
        state["gc_paths"] = [*state["gc_paths"], "docs/spool/worklog/2099-01-01-other-1.md"]

    def mutate_fragment(state: dict[str, object], field: str, value: object) -> None:
        state["fragments"][0][field] = value

    def mutate_target(state: dict[str, object], field: str, value: object) -> None:
        state["targets"][0][field] = value

    cases = (
        ("fold_date", lambda state: state.__setitem__(
            "fold_date", "2000-01-02" if state["fold_date"] == "2000-01-01" else "2000-01-01",
        )),
        ("gc_paths", mutate_gc_paths),
        ("fragment.path", lambda state: mutate_fragment(
            state, "path", "docs/spool/worklog/2099-01-01-other-1.md",
        )),
        ("fragment.authored", lambda state: mutate_fragment(state, "authored", "2099-01-01")),
        ("fragment.wave", lambda state: mutate_fragment(state, "wave", "other-wave")),
        ("fragment.seq", lambda state: mutate_fragment(state, "seq", 2)),
        ("fragment.content_sha256", lambda state: mutate_fragment(
            state, "content_sha256", "0" * 64,
        )),
        ("fragment.allocations", lambda state: mutate_fragment(
            state, "allocations", [["T:payload-pin", "[T-999]"]],
        )),
        ("projected_worklog_bytes", lambda state: state.__setitem__(
            "projected_worklog_bytes", state["projected_worklog_bytes"] + 1,
        )),
        ("rotation_path", lambda state: state.__setitem__(
            "rotation_path", "docs/archive/worklog-phase3-2099-1.md",
        )),
        ("target.path", lambda state: mutate_target(
            state, "path", "docs/archive/README.md",
        )),
        ("target.before_sha256", lambda state: mutate_target(
            state, "before_sha256", "0" * 64,
        )),
        ("target.after_sha256", lambda state: mutate_target(
            state, "after_sha256", "0" * 64,
        )),
    )
    for label, mutate in cases:
        state = json.loads(json.dumps(original_state))
        mutate(state)
        candidate = _unchecked_plan_from_state(plan, state)
        exc = _transaction_raises(
            "transaction_id が payload と不一致",
            spool_fold.apply_fold,
            repo,
            candidate,
        )
        assert label not in str(exc)
        state_path = spool_fold._state_path(repo)
        assert not state_path.exists() and not state_path.is_symlink()


def test_input_closure_binds_both_rendering_engine_files(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    _commit(repo, "fragment")
    for rel in ("tools/spool_fold.py", "tools/check_docs.py"):
        plan = spool_fold.plan_fold(repo, fold_date="2026-08-02")
        path = repo / rel
        before = path.read_bytes()
        path.write_bytes(before + b"\n# changed after plan\n")
        _transaction_raises("closure", spool_fold.apply_fold, repo, plan)
        assert not spool_fold._state_path(repo).exists()
        path.write_bytes(before)


def test_resume_rejects_head_advanced_after_state_write(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    plan = _plan_for_commit(repo)
    state_path = spool_fold._state_path(repo)
    spool_fold._atomic_write(
        state_path,
        json.dumps(
            spool_fold._plan_state(plan),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode() + b"\n",
    )
    _write(repo / "unrelated.txt", "advance\n")
    _commit(repo, "advance head")

    _transaction_raises("apply HEAD", spool_fold.apply_fold, repo, plan)


def test_apply_keeps_applied_state_and_fsyncs_every_gc_parent(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    _fragment(repo, "decisions", "## {{D:one}}. one\n")
    _commit(repo, "fragments")
    plan = spool_fold.plan_fold(repo)
    observed: list[set[Path]] = []
    original = spool_fold._fsync_directories
    spool_fold._fsync_directories = lambda paths: observed.append({Path(path).resolve() for path in paths})
    try:
        spool_fold.apply_fold(repo, plan)
    finally:
        spool_fold._fsync_directories = original

    state_path = spool_fold._state_path(repo)
    state = spool_fold._load_state(state_path)
    assert state["phase"] == "applied"
    assert state["transaction_id"] == plan.transaction_id
    assert observed == [{(repo / rel).parent.resolve() for rel in plan.gc_paths}]


def test_mark_and_finalize_require_commit_identity_and_phase(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    plan = _plan_for_commit(repo)
    spool_fold.apply_fold(repo, plan)
    _transaction_raises(
        "state ID/phase",
        spool_fold.mark_fold_committed,
        repo,
        dataclasses.replace(plan, transaction_id="0" * 64),
        fold_commit=plan.origin.tested_tip,
    )
    _transaction_raises(
        "state ID/phase",
        spool_fold.finalize_fold,
        repo,
        plan,
        fold_commit=plan.origin.tested_tip,
    )


def test_commit_identity_gate_rejects_mode_only_manual_fold_commit(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    plan = _plan_for_commit(repo)
    spool_fold.apply_fold(repo, plan)
    (repo / "docs/worklog.md").chmod(0o755)
    _run_git(repo, "add", "-A")
    subprocess.run(
        [
            "git", "-C", str(repo), "commit", "--no-gpg-sign",
            "--cleanup=verbatim", f"--author={FOLD_AUTHOR_IDENTITY}", "-F", "-",
        ],
        check=True,
        input=FOLD_COMMIT_MESSAGE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    fold_commit = _run_git(repo, "rev-parse", "HEAD")
    audited = tuple(
        _run_git(
            repo,
            "rev-list",
            "--reverse",
            f"{plan.origin.trusted_main_cutoff}..{plan.origin.tested_tip}",
        ).splitlines()
    )
    declared = verify_declared_fold_commit(
        repo,
        fold_commit_sha=fold_commit,
        trusted_main_cutoff_sha=plan.origin.trusted_main_cutoff,
        landed_main_sha=fold_commit,
        landed_commits=audited,
        wave_tip=plan.origin.tested_tip,
    )
    assert declared.ok, declared
    _transaction_raises(
        "target record",
        spool_fold.verify_fold_commit_identity,
        repo,
        plan,
        fold_commit=fold_commit,
    )


def test_commit_identity_gate_rejects_author_suffix_bytes(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    plan = _plan_for_commit(repo)
    spool_fold.apply_fold(repo, plan)
    _run_git(repo, "add", "-A")
    forged_author = (
        FOLD_AUTHOR_IDENTITY.encode("utf-8")
        + b" forged-suffix 1700000000 +0000"
    )
    fold_commit = _raw_commit(repo, author=forged_author)
    raw_author = next(
        line.removeprefix(b"author ")
        for line in subprocess.run(
            ["git", "-C", str(repo), "cat-file", "commit", fold_commit],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout.splitlines()
        if line.startswith(b"author ")
    )
    assert raw_author.startswith(FOLD_AUTHOR_IDENTITY.encode("utf-8") + b" ")
    _transaction_raises(
        "author identity",
        spool_fold.verify_fold_commit_identity,
        repo,
        plan,
        fold_commit=fold_commit,
    )


def test_commit_identity_gate_rejects_extra_state_external_path(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    plan = _plan_for_commit(repo)
    spool_fold.apply_fold(repo, plan)
    extra_path = "docs/decisions.md"
    assert extra_path not in {target.path for target in plan.targets}
    with (repo / extra_path).open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("\n## D2. state-external fixture\n")
    _run_git(repo, "add", "-A")
    fold_commit = _raw_commit(
        repo,
        author=FOLD_AUTHOR_IDENTITY.encode("utf-8") + b" 1700000000 +0000",
    )
    _assert_declared_fold(repo, plan, fold_commit)
    actual = spool_fold._commit_diff_records(repo, plan.origin.tested_tip, fold_commit)
    expected_paths = {target.path for target in plan.targets} | set(plan.gc_paths)
    assert set(actual) == expected_paths | {extra_path}
    assert actual[extra_path][0] == "M"
    for target in plan.targets:
        status, old_mode, new_mode, new_oid = actual[target.path]
        assert status == ("M" if target.before_exists else "A")
        assert old_mode == ("100644" if target.before_exists else "000000")
        assert new_mode == "100644"
        assert new_oid == _hash_object(repo, target.after_bytes)
    assert all(actual[path][0] == "D" for path in plan.gc_paths)
    _transaction_raises(
        "path 集合",
        spool_fold.verify_fold_commit_identity,
        repo,
        plan,
        fold_commit=fold_commit,
    )


def test_commit_identity_gate_rejects_target_status_only(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    plan = _plan_for_commit(repo)
    fold_commit = _commit_applied_fold(repo, plan)
    _assert_declared_fold(repo, plan, fold_commit)
    actual = spool_fold._commit_diff_records(repo, plan.origin.tested_tip, fold_commit)
    target = next(target for target in plan.targets if target.before_exists)
    original_record = actual[target.path]
    assert original_record[0] == "M"
    synthetic = dict(actual)
    synthetic[target.path] = ("A", *original_record[1:])
    assert set(synthetic) == set(actual)
    assert synthetic[target.path][1:] == original_record[1:]
    original_reader = spool_fold._commit_diff_records
    spool_fold._commit_diff_records = lambda *_args: synthetic
    try:
        _transaction_raises(
            "target record",
            spool_fold.verify_fold_commit_identity,
            repo,
            plan,
            fold_commit=fold_commit,
        )
    finally:
        spool_fold._commit_diff_records = original_reader


def test_commit_identity_gate_rejects_target_blob_oid_only(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    plan = _plan_for_commit(repo)
    spool_fold.apply_fold(repo, plan)
    target = next(target for target in plan.targets if target.path == "docs/worklog.md")
    (repo / target.path).write_bytes(target.after_bytes + b"\nwrong blob only\n")
    _run_git(repo, "add", "-A")
    fold_commit = _raw_commit(
        repo,
        author=FOLD_AUTHOR_IDENTITY.encode("utf-8") + b" 1700000000 +0000",
    )
    _assert_declared_fold(repo, plan, fold_commit)
    actual = spool_fold._commit_diff_records(repo, plan.origin.tested_tip, fold_commit)
    assert set(actual) == {item.path for item in plan.targets} | set(plan.gc_paths)
    status, old_mode, new_mode, new_oid = actual[target.path]
    assert status == "M" and old_mode == new_mode == "100644"
    assert new_oid != _hash_object(repo, target.after_bytes)
    for other in plan.targets:
        if other.path == target.path:
            continue
        record = actual[other.path]
        assert record[0] == ("M" if other.before_exists else "A")
        assert record[2] == "100644"
        assert record[3] == _hash_object(repo, other.after_bytes)
    assert all(actual[path][0] == "D" for path in plan.gc_paths)
    _transaction_raises(
        "target record",
        spool_fold.verify_fold_commit_identity,
        repo,
        plan,
        fold_commit=fold_commit,
    )


def test_commit_identity_gate_rejects_gc_status_only(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    plan = _plan_for_commit(repo)
    fold_commit = _commit_applied_fold(repo, plan)
    _assert_declared_fold(repo, plan, fold_commit)
    actual = spool_fold._commit_diff_records(repo, plan.origin.tested_tip, fold_commit)
    gc_path = plan.gc_paths[0]
    original_record = actual[gc_path]
    assert original_record[0] == "D" and original_record[2] == "000000"
    synthetic = dict(actual)
    synthetic[gc_path] = ("M", *original_record[1:])
    assert set(synthetic) == set(actual)
    assert synthetic[gc_path][1:] == original_record[1:]
    original_reader = spool_fold._commit_diff_records
    spool_fold._commit_diff_records = lambda *_args: synthetic
    try:
        _transaction_raises(
            "GC record",
            spool_fold.verify_fold_commit_identity,
            repo,
            plan,
            fold_commit=fold_commit,
        )
    finally:
        spool_fold._commit_diff_records = original_reader


def test_commit_identity_gate_exception_path_reports_declared_detail(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    plan = _plan_for_commit(repo)
    fold_commit = _commit_applied_fold(repo, plan)
    _assert_declared_fold(repo, plan, fold_commit)
    _run_git(repo, "symbolic-ref", "HEAD", "refs/heads/t2608-does-not-exist")
    exc = _transaction_raises(
        "declared fold verifier が失敗: invalid-run ",
        spool_fold.verify_fold_commit_identity,
        repo,
        plan,
        fold_commit=fold_commit,
    )
    assert '{"kind":"head","label":"git"}' in str(exc)
    assert isinstance(exc.__cause__, DevWavesError)
    assert exc.__cause__.detail == {"kind": "head", "label": "git"}


def test_discover_requires_exact_expected_id_complete_targets_and_absent_gc(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    fragment = _fragment(repo, "worklog", _worklog_body(repo))
    fragment_raw = fragment.read_bytes()
    plan = _plan_for_commit(repo)
    spool_fold.apply_fold(repo, plan)

    default_issues = spool_fold.validate_spool_tree(repo)
    wrong_issues = spool_fold.validate_spool_tree(repo, expected_transaction_id="0" * 64)
    assert [issue.code for issue in default_issues] == ["transaction-active"]
    assert [issue.code for issue in wrong_issues] == ["transaction-state"]
    assert spool_fold.validate_spool_tree(
        repo, expected_transaction_id=plan.transaction_id,
    ) == []

    fragment.parent.mkdir(parents=True, exist_ok=True)
    fragment.write_bytes(fragment_raw)
    incomplete = spool_fold.validate_spool_tree(
        repo, expected_transaction_id=plan.transaction_id,
    )
    assert [issue.code for issue in incomplete] == ["transaction-state"]
    assert "complete shape" in incomplete[0].message


def test_discover_detects_dangling_state_symlink(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    state_path = spool_fold._state_path(repo)
    state_path.symlink_to("missing-state-payload")
    issues = spool_fold.validate_spool_tree(repo)
    assert [issue.code for issue in issues] == ["transaction-active"]
    assert str(state_path.absolute()) in issues[0].message


def test_receipt_v2_contains_independently_observed_git_values(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    _commit(repo, "fragment")
    observed_tip = _run_git(repo, "rev-parse", "HEAD")
    observed_base = _run_git(repo, "rev-parse", "HEAD^")
    observed_ref = _run_git(repo, "symbolic-ref", "HEAD")
    plan = spool_fold.plan_fold(repo, origin=_land_origin(repo))
    receipt = _target(plan, "docs/spool/FOLDED.md").after_bytes.decode("utf-8")
    record = spool_fold._receipt_records(receipt)[-1]
    assert frozenset(record) == spool_fold.RECEIPT_V2_FIELDS
    assert record["base"] == observed_base
    assert record["tested_tip"] == observed_tip
    assert record["wave_ref"] == observed_ref


def test_receipt_parser_enforces_positional_v2_cutover() -> None:
    legacy = {
        "allocations": {},
        "authored": "2026-08-02",
        "content_sha256": "1" * 64,
        "seq": 1,
        "wave": "wave-a",
    }
    v2 = {
        **legacy,
        "base": "2" * 40,
        "tested_tip": "3" * 40,
        "wave_ref": "refs/heads/wave-a",
    }
    line = lambda record: "- " + json.dumps(record, separators=(",", ":"), sort_keys=True)
    assert len(spool_fold._receipt_records(line(legacy) + "\n" + line(v2) + "\n")) == 2
    _raises("receipt", spool_fold._receipt_records, line(v2) + "\n" + line(legacy) + "\n")
    missing = dict(v2)
    missing.pop("base")
    _raises("receipt", spool_fold._receipt_records, line(missing) + "\n")


def test_load_rotate_limit_wraps_baseexceptions_and_restores_import_state(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "tools/check_docs.py").write_text(
        "WORKLOG_ROTATE_BYTES = True\n", encoding="utf-8",
    )
    _raises("rotate-limit", spool_fold._load_rotate_limit, repo)
    for statement in ("raise SystemExit(0)\n", "raise KeyboardInterrupt()\n"):
        path = repo / "tools/check_docs.py"
        path.write_text(statement, encoding="utf-8")
        before_modules = set(sys.modules)
        before_bytecode = sys.dont_write_bytecode
        exc = _raises("rotate-limit", spool_fold._load_rotate_limit, repo)
        assert type(exc.__cause__) in {SystemExit, KeyboardInterrupt}
        assert sys.dont_write_bytecode == before_bytecode
        assert set(sys.modules) == before_modules


def test_n17_fragment_allocation_order_is_explicitly_sorted(tmp_path: Path) -> None:
    """N17: directory 列挙・作成順でなく wave/seq/body offset 順に採番する。"""

    repo = _repo(tmp_path)
    _fragment(repo, "decisions", "## {{D:zeta}}. zeta\n", wave="wave-z", seq=9)
    _fragment(repo, "decisions", "## {{D:alpha}}. alpha\n", wave="wave-a", seq=2)
    plan1 = spool_fold.plan_fold(repo)
    plan2 = spool_fold.plan_fold(repo)
    allocations = dict(plan1.allocations)
    assert allocations["wave-a/D:alpha"] == "D2"
    assert allocations["wave-z/D:zeta"] == "D3"
    assert plan1.as_dict() == plan2.as_dict()


def test_explicit_fold_date_controls_plan_bytes_and_transaction_state(tmp_path: Path) -> None:
    """F-7: (base, fragments, fold_date) が同じなら plan/state は同一になる。"""

    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    first = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    second = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    later = spool_fold.plan_fold(repo, fold_date="2026-08-03")

    assert first.as_dict() == second.as_dict()
    assert spool_fold._plan_state(first) == spool_fold._plan_state(second)
    assert first.fold_date == "2026-08-02"
    assert first.transaction_id != later.transaction_id
    assert _target(first, "docs/worklog.md").after_bytes != _target(later, "docs/worklog.md").after_bytes


def test_explicit_dry_run_plan_object_is_directly_applicable(tmp_path: Path) -> None:
    """F-7: dry-run 相当の明示日付 plan を再計画せず apply 入力にできる。"""

    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    plan = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    result = spool_fold.apply_fold(repo, plan)
    assert result.transaction_id == plan.transaction_id
    assert "## 2026-08-02 (2)" in (repo / "docs/worklog.md").read_text(encoding="utf-8")


def test_n18_completion_with_remaining_work_is_rejected(tmp_path: Path) -> None:
    """N18: 歴史語彙の部分完了を terminal `完了` として受理しない。"""

    repo = _repo(tmp_path)
    base = _digest(_active_block("[T-001]"))
    body = _worklog_body(
        repo,
        carry=(),
        completed=(("[T-001]", "一部完了だが残件あり", base),),
        completion_remaining=True,
    )
    _fragment(repo, "worklog", body)
    issues = spool_fold.validate_spool_tree(repo)
    assert [issue.code for issue in issues] == ["completion-remaining"]


def test_completion_without_remaining_field_is_rejected(tmp_path: Path) -> None:
    """T-352-1: 禁制語がなくても構造 field のない完了を受理しない。"""

    repo = _repo(tmp_path)
    body = _worklog_body(
        repo,
        carry=(),
        completed=(("[T-001]", "初期処置を終了", _digest(_active_block("[T-001]"))),),
    )
    _fragment(repo, "worklog", body)
    _raises("completion-remaining-field", spool_fold.plan_fold, repo)


def test_completion_remaining_field_rejects_noncanonical_values(tmp_path: Path) -> None:
    """T-352-2: `none` 以外と末尾コメント付きの値を閉じた語彙から拒否する。"""

    for index, value in enumerate(("None", "なし", "some", "0", "none # comment"), 1):
        parent = tmp_path / f"value-{index}"
        parent.mkdir()
        repo = _repo(parent)
        base = _digest(_active_block("[T-001]"))
        body = (
            "## 本文\n\n- body\n\n## 次の一手差分\n\n### 完了\n\n"
            f"- [T-001] 終了\n  base: {base}\n  remaining: {value}\n"
        )
        _fragment(repo, "worklog", body)
        _raises("completion-remaining-field", spool_fold.plan_fold, repo)


def test_completion_remaining_field_rejects_duplicates(tmp_path: Path) -> None:
    """T-352-3: trailer 内の remaining field は exact-one。"""

    repo = _repo(tmp_path)
    base = _digest(_active_block("[T-001]"))
    body = (
        "## 本文\n\n- body\n\n## 次の一手差分\n\n### 完了\n\n"
        f"- [T-001] 終了\n  base: {base}\n"
        "  remaining: none\n  remaining: none\n"
    )
    _fragment(repo, "worklog", body)
    _raises("completion-remaining-field", spool_fold.plan_fold, repo)


def test_completion_remaining_decoys_in_fence_and_comment_are_rejected(tmp_path: Path) -> None:
    """T-352-4: 本文中の fence/comment decoy を trailer field と数えない。"""

    decoys = (
        "  ```yaml\n  remaining: none\n  ```\n",
        "  <!--\n  remaining: none\n  -->\n",
    )
    for index, decoy in enumerate(decoys, 1):
        parent = tmp_path / f"decoy-{index}"
        parent.mkdir()
        repo = _repo(parent)
        base = _digest(_active_block("[T-001]"))
        body = (
            "## 本文\n\n- body\n\n## 次の一手差分\n\n### 完了\n\n"
            "- [T-001] 初期処置だけ終了。後続作業は明日\n"
            f"{decoy}  base: {base}\n"
        )
        _fragment(repo, "worklog", body)
        _raises("completion-remaining-field", spool_fold.plan_fold, repo)


def test_completion_remaining_in_unclosed_list_relative_fences_is_rejected(tmp_path: Path) -> None:
    """F2: raw 4/5-space の backtick/tilde fence 内 decoy を field と数えない。"""

    cases = (("`", 4), ("`", 5), ("~", 4), ("~", 5))
    for index, (marker, indent) in enumerate(cases, 1):
        parent = tmp_path / f"list-relative-fence-{index}"
        parent.mkdir()
        repo = _repo(parent)
        base = _digest(_active_block("[T-001]"))
        body = (
            "## 本文\n\n- body\n\n## 次の一手差分\n\n### 完了\n\n"
            "- [T-001] 初期処置だけ終了。後続作業は明日\n"
            f"  base: {base}\n"
            f"{' ' * indent}{marker * 3}yaml\n"
            "  remaining: none\n"
        )
        _fragment(repo, "worklog", body)
        _raises("completion-remaining-field", spool_fold.plan_fold, repo)


def test_valid_completion_remaining_field_is_removed_from_canonical(tmp_path: Path) -> None:
    """T-352-5: valid field は authoring metadata であり canonical へ漏らさない。"""

    repo = _repo(tmp_path)
    body = _worklog_body(
        repo,
        carry=(),
        completed=(("[T-001]", "終端完了", _digest(_active_block("[T-001]"))),),
        completion_remaining=True,
    )
    _fragment(repo, "worklog", body)
    rendered = _target(
        spool_fold.plan_fold(repo, fold_date="2026-08-02"),
        "docs/worklog.md",
    ).after_bytes.decode("utf-8")
    assert "- [T-001] 終端完了" in rendered
    assert "remaining:" not in rendered


def test_completion_base_and_remaining_trailer_order_is_independent(tmp_path: Path) -> None:
    """T-352-6: base と remaining は trailer 内でどちらの順でも受理する。"""

    repo = _repo(tmp_path, active=("[T-001]", "[T-002]"))
    base1 = _digest(_active_block("[T-001]"))
    base2 = _digest(_active_block("[T-002]"))
    body = (
        "## 本文\n\n- body\n\n## 次の一手差分\n\n### 完了\n\n"
        f"- [T-001] base が先\n  base: {base1}\n  remaining: none\n"
        f"- [T-002] remaining が先\n  remaining: none\n  base: {base2}\n"
    )
    _fragment(repo, "worklog", body)
    rendered = _target(
        spool_fold.plan_fold(repo, fold_date="2026-08-02"),
        "docs/worklog.md",
    ).after_bytes.decode("utf-8")
    assert "- [T-001] base が先" in rendered
    assert "- [T-002] remaining が先" in rendered
    assert "  base:" not in rendered and "  remaining:" not in rendered


def test_update_and_defer_do_not_require_remaining_field(tmp_path: Path) -> None:
    """T-352-7: remaining field の必須化を更新・見送りへ広げない。"""

    repo = _repo(tmp_path, active=("[T-001]", "[T-002]"))
    body = _worklog_body(
        repo,
        carry=(),
        updated=(("[T-001]", "更新後", _digest(_active_block("[T-001]"))),),
        deferred=(("研究・計測系", "[T-002]", "見送り — 理由: 固定", _digest(_active_block("[T-002]"))),),
    )
    _fragment(repo, "worklog", body)
    plan = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    worklog = _target(plan, "docs/worklog.md").after_bytes.decode("utf-8")
    phase = _target(plan, "docs/phase3.md").after_bytes.decode("utf-8")
    assert "- [T-001] 更新後" in worklog
    assert "- [T-002] 見送り — 理由: 固定" in phase


def test_deferred_append_targets_single_line_item_head(tmp_path: Path) -> None:
    """T-358-9: 1 行 item の ID 行末へ suffix だけを挿入する。"""

    repo = _repo(tmp_path)
    suffix = " 発火記録: 単一"
    _fragment(repo, "worklog", _worklog_body(repo, deferred_appends=(("[T-050]", suffix),)))
    before = (repo / "docs/phase3.md").read_bytes()
    offset = _line_end_offset(before, b"- [T-050] ")
    assert _phase_after(repo) == before[:offset] + suffix.encode("utf-8") + before[offset:]


def test_deferred_append_accepts_first_suffix_seen_outside_head_line_end(tmp_path: Path) -> None:
    """F3: 同じ bytes が継続行・comment・head prose 内にあっても初回追記を受理する。"""

    suffix = " 発火記録: 初回"
    target_blocks = (
        "- [T-050] 継続行に例示を持つ\n  例示:" + suffix + "\n",
        "- [T-050] comment に例示を持つ\n  <!--" + suffix + " -->\n",
        "- [T-050] head prose 内の例示" + suffix + " は未追記\n",
    )
    for index, target_block in enumerate(target_blocks, 1):
        parent = tmp_path / f"suffix-context-{index}"
        parent.mkdir()
        repo = _repo(parent)
        phase = (repo / "docs/phase3.md").read_text(encoding="utf-8").replace(
            "- [T-050] 既存見送り — 理由: seed\n",
            target_block,
        )
        _write(repo / "docs/phase3.md", phase)
        _fragment(repo, "worklog", _worklog_body(repo, deferred_appends=(("[T-050]", suffix),)))
        before = (repo / "docs/phase3.md").read_bytes()
        offset = _line_end_offset(before, b"- [T-050] ")
        after = _phase_after(repo)
        assert after == before[:offset] + suffix.encode("utf-8") + before[offset:]


def test_deferred_append_multiline_target_preserves_continuations(tmp_path: Path) -> None:
    """T-358-10: 複数行 target でも先頭行末へ追記し継続行を不変に保つ。"""

    repo = _repo(tmp_path)
    phase = (repo / "docs/phase3.md").read_text(encoding="utf-8")
    phase = phase.replace(
        "- [T-050] 既存見送り — 理由: seed\n",
        "- [T-050] 複数行の先頭  \n  継続行その一\n  継続行その二\n",
    )
    _write(repo / "docs/phase3.md", phase)
    suffix = " 発火記録: 複数行"
    _fragment(repo, "worklog", _worklog_body(repo, deferred_appends=(("[T-050]", suffix),)))
    before = (repo / "docs/phase3.md").read_bytes()
    offset = _line_end_offset(before, b"- [T-050] ")
    after = _phase_after(repo)
    assert after == before[:offset] + suffix.encode("utf-8") + before[offset:]
    assert "\n  継続行その一\n  継続行その二\n".encode("utf-8") in after


def test_deferred_append_fenced_target_does_not_break_fence(tmp_path: Path) -> None:
    """T-358-11: target block の fenced code を閉じ行ごと byte-exact に保つ。"""

    repo = _repo(tmp_path)
    phase = (repo / "docs/phase3.md").read_text(encoding="utf-8")
    fenced = (
        "- [T-050] fence を持つ先頭\n"
        "  ```text\n"
        "  - [T-999] fence 内の例\n"
        "  ```\n"
        "  fence 後の継続\n"
    )
    phase = phase.replace("- [T-050] 既存見送り — 理由: seed\n", fenced)
    _write(repo / "docs/phase3.md", phase)
    suffix = " 発火記録: fence 安全"
    _fragment(repo, "worklog", _worklog_body(repo, deferred_appends=(("[T-050]", suffix),)))
    before = (repo / "docs/phase3.md").read_bytes()
    offset = _line_end_offset(before, b"- [T-050] ")
    after = _phase_after(repo)
    assert after == before[:offset] + suffix.encode("utf-8") + before[offset:]
    assert fenced.split("\n", 1)[1].encode("utf-8") in after


def test_deferred_append_is_byte_exact_for_all_insertion_shapes(tmp_path: Path) -> None:
    """T-358-12: 単一・同一複数・複数対象・複数行を exact splice で固定する。"""

    parent = tmp_path / "single"
    parent.mkdir()
    repo = _repo(parent)
    _fragment(repo, "worklog", _worklog_body(repo, deferred_appends=(("[T-050]", " A"),)))
    before = (repo / "docs/phase3.md").read_bytes()
    offset = _line_end_offset(before, b"- [T-050] ")
    assert _phase_after(repo) == before[:offset] + b" A" + before[offset:]

    parent = tmp_path / "same-target"
    parent.mkdir()
    repo = _repo(parent)
    _fragment(
        repo,
        "worklog",
        _worklog_body(repo, deferred_appends=(("[T-050]", " A"), ("[T-050]", " B"))),
    )
    before = (repo / "docs/phase3.md").read_bytes()
    offset = _line_end_offset(before, b"- [T-050] ")
    assert _phase_after(repo) == before[:offset] + b" A B" + before[offset:]

    parent = tmp_path / "multiple-targets"
    parent.mkdir()
    repo = _repo(parent)
    _fragment(
        repo,
        "worklog",
        _worklog_body(repo, deferred_appends=(("[T-050]", " A"), ("[T-051]", " B"))),
    )
    before = (repo / "docs/phase3.md").read_bytes()
    insertions = (
        (_line_end_offset(before, b"- [T-050] "), b" A"),
        (_line_end_offset(before, b"- [T-051] "), b" B"),
    )
    assert _phase_after(repo) == _splice_exact(before, insertions)

    parent = tmp_path / "multiline-target"
    parent.mkdir()
    repo = _repo(parent)
    phase = (repo / "docs/phase3.md").read_text(encoding="utf-8").replace(
        "- [T-050] 既存見送り — 理由: seed\n",
        "- [T-050] 複数行先頭\n  継続行  \n  最終行\n",
    )
    _write(repo / "docs/phase3.md", phase)
    _fragment(repo, "worklog", _worklog_body(repo, deferred_appends=(("[T-050]", " A"),)))
    before = (repo / "docs/phase3.md").read_bytes()
    offset = _line_end_offset(before, b"- [T-050] ")
    assert _phase_after(repo) == before[:offset] + b" A" + before[offset:]


def test_empty_deferred_append_section_is_rejected(tmp_path: Path) -> None:
    """T-358-13: 使用した見送り追記 section は item 1 件以上を要求する。"""

    repo = _repo(tmp_path)
    body = _worklog_body(repo).rstrip("\n") + "\n\n### 見送り追記\n"
    _fragment(repo, "worklog", body)
    _raises("deferred-append-empty", spool_fold.plan_fold, repo)


def test_multiline_deferred_append_item_is_rejected(tmp_path: Path) -> None:
    """T-358-14: 見送り追記 item は 1 物理行だけに限定する。"""

    repo = _repo(tmp_path)
    body = _worklog_body(
        repo,
        deferred_appends=(("[T-050]", " 最初の行\n  継続行"),),
    )
    _fragment(repo, "worklog", body)
    _raises("deferred-append-shape", spool_fold.plan_fold, repo)


def test_empty_or_whitespace_deferred_append_suffix_is_rejected(tmp_path: Path) -> None:
    """T-358-15/F4: 空 suffix を shape gate で拒否する独立 node。"""

    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo, deferred_appends=(("[T-050]", ""),)))
    _raises("deferred-append-shape", spool_fold.plan_fold, repo)


def test_whitespace_only_deferred_append_suffix_is_rejected(tmp_path: Path) -> None:
    """T-358-15/F4: 空白だけの suffix を shape gate で拒否する独立 node。"""

    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo, deferred_appends=(("[T-050]", "   "),)))
    _raises("deferred-append-shape", spool_fold.plan_fold, repo)


def test_deferred_append_missing_target_is_rejected(tmp_path: Path) -> None:
    """T-358-16: 見送り台帳に存在しない ID を fail-closed にする。"""

    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo, deferred_appends=(("[T-999]", " 発火"),)))
    _raises("deferred-append-missing", spool_fold.plan_fold, repo)


def test_deferred_append_cannot_target_completion_record(tmp_path: Path) -> None:
    """T-358-17: 裁定・完了記録 region の ID は探索対象に含めない。"""

    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo, deferred_appends=(("[T-052]", " 発火"),)))
    _raises("deferred-append-missing", spool_fold.plan_fold, repo)


def test_deferred_append_rejects_visible_duplicate_target_ids(tmp_path: Path) -> None:
    """T-358-18: 可視な top-level target ID が複数なら曖昧な追記をしない。"""

    repo = _repo(tmp_path)
    phase = (repo / "docs/phase3.md").read_text(encoding="utf-8").replace(
        "- [T-051] 既存見送り — 理由: seed\n",
        "- [T-050] 可視な重複 — 理由: duplicate\n"
        "- [T-051] 既存見送り — 理由: seed\n",
    )
    _write(repo / "docs/phase3.md", phase)
    _fragment(repo, "worklog", _worklog_body(repo, deferred_appends=(("[T-050]", " 発火"),)))
    _raises("deferred-append-duplicate", spool_fold.plan_fold, repo)


def test_deferred_append_ignores_comment_and_fence_decoy_items(tmp_path: Path) -> None:
    """T-358-19: comment/fence 内の item を target または重複として数えない。"""

    parent = tmp_path / "visible-target"
    parent.mkdir()
    repo = _repo(parent)
    decoys = (
        "<!--\n- [T-050] comment decoy\n- [T-999] comment only\n-->\n\n"
        "```text\n- [T-050] fence decoy\n- [T-999] fence only\n```\n\n"
    )
    phase = (repo / "docs/phase3.md").read_text(encoding="utf-8").replace(
        "### プロセス文書系\n\n",
        "### プロセス文書系\n\n" + decoys,
    )
    _write(repo / "docs/phase3.md", phase)
    _fragment(repo, "worklog", _worklog_body(repo, deferred_appends=(("[T-050]", " 発火"),)))
    before = (repo / "docs/phase3.md").read_bytes()
    offset = _line_end_offset(before, b"- [T-050] \xe6\x97\xa2\xe5\xad\x98")
    assert _phase_after(repo) == before[:offset] + " 発火".encode("utf-8") + before[offset:]

    parent = tmp_path / "decoy-only"
    parent.mkdir()
    repo = _repo(parent)
    phase = (repo / "docs/phase3.md").read_text(encoding="utf-8").replace(
        "### プロセス文書系\n\n",
        "### プロセス文書系\n\n" + decoys,
    )
    _write(repo / "docs/phase3.md", phase)
    _fragment(repo, "worklog", _worklog_body(repo, deferred_appends=(("[T-999]", " 発火"),)))
    _raises("deferred-append-missing", spool_fold.plan_fold, repo)


def test_deferred_append_before_defer_section_is_rejected(tmp_path: Path) -> None:
    """T-358-20: 見送り追記を見送りより前へ置く action 順序違反を拒否する。"""

    repo = _repo(tmp_path)
    base = _digest(_active_block("[T-001]"))
    body = (
        "## 本文\n\n- body\n\n## 次の一手差分\n\n"
        "### 見送り追記\n\n- [T-050] 発火\n\n"
        "### 見送り\n\n#### プロセス文書系\n\n"
        f"- [T-001] 見送り — 理由: 固定\n  base: {base}\n"
    )
    _fragment(repo, "worklog", body)
    _raises("worklog-action-order", spool_fold.plan_fold, repo)


def test_deferred_append_can_target_item_deferred_earlier_in_same_fold(tmp_path: Path) -> None:
    """T-358-21: Fragment.key 順の逐次 phase に対して見送り追記を適用する。"""

    repo = _repo(tmp_path)
    deferred_text = "同じ fold で新設 — 理由: 逐次意味論"
    _fragment(
        repo,
        "worklog",
        _worklog_body(
            repo,
            carry=(),
            deferred=(("プロセス文書系", "[T-001]", deferred_text, _digest(_active_block("[T-001]"))),),
        ),
        wave="sequential-wave",
        seq=1,
    )
    _fragment(
        repo,
        "worklog",
        _worklog_body(repo, carry=(), deferred_appends=(("[T-001]", " 発火記録: 同一 fold"),)),
        wave="sequential-wave",
        seq=2,
    )
    phase = _phase_after(repo).decode("utf-8")
    assert f"- [T-001] {deferred_text} 発火記録: 同一 fold\n" in phase


def test_deferred_append_resolves_cross_ledger_placeholder(tmp_path: Path) -> None:
    """T-358-22: suffix の cross-ledger placeholder を plan 時に解決する。"""

    repo = _repo(tmp_path)
    _fragment(
        repo,
        "decisions",
        "## {{D:append-decision}}. 追記の根拠\n\n**決定:** 固定。\n",
        wave="cross-append",
        seq=1,
    )
    _fragment(
        repo,
        "worklog",
        _worklog_body(
            repo,
            deferred_appends=(("[T-050]", " 発火記録: {{D:append-decision}}"),),
        ),
        wave="cross-append",
        seq=2,
    )
    phase = _phase_after(repo).decode("utf-8")
    assert "発火記録: D2" in phase
    assert "{{D:append-decision}}" not in phase


def test_deferred_append_order_is_deterministic_by_fragment_key_and_item_index(tmp_path: Path) -> None:
    """T-358-23: 固定日付で wave/seq/item index 順となり FS/hash 順へ依存しない。"""

    repo = _repo(tmp_path)
    _fragment(
        repo,
        "worklog",
        _worklog_body(repo, deferred_appends=(("[T-050]", " B1"),)),
        wave="wave-b",
        seq=1,
    )
    _fragment(
        repo,
        "worklog",
        _worklog_body(repo, deferred_appends=(("[T-050]", " A10"),)),
        wave="wave-a",
        seq=10,
    )
    _fragment(
        repo,
        "worklog",
        _worklog_body(
            repo,
            deferred_appends=(("[T-050]", " A2-first"), ("[T-050]", " A2-second")),
        ),
        wave="wave-a",
        seq=2,
    )
    first = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    second = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    assert first.as_dict() == second.as_dict()
    phase = _target(first, "docs/phase3.md").after_bytes.decode("utf-8")
    target_line = next(line for line in phase.splitlines() if line.startswith("- [T-050] "))
    assert target_line.endswith(" A2-first A2-second A10 B1")


def test_deferred_append_rejects_replayed_identical_suffix(tmp_path: Path) -> None:
    """T-358-24: wrapper を変えた同一 suffix の再投入も二重挿入しない。"""

    repo = _repo(tmp_path)
    suffix = " 発火記録: replay guard"
    _fragment(repo, "worklog", _worklog_body(repo, deferred_appends=(("[T-050]", suffix),)))
    _commit(repo, "first append fragment")
    _complete_fold(repo, fold_date="2026-08-02")
    _fragment(
        repo,
        "worklog",
        _worklog_body(repo, deferred_appends=(("[T-050]", suffix),), prose="- wrapper changed"),
        seq=2,
        title="changed wrapper",
    )
    _raises("deferred-append-duplicate-suffix", spool_fold.plan_fold, repo)


def test_deferred_append_only_fragment_preserves_all_active_tasks(tmp_path: Path) -> None:
    """T-358-25: 見送り追記を active 遷移へ混ぜず全 task を暗黙 carry する。"""

    repo = _repo(tmp_path, active=("[T-001]", "[T-002]", "[T-003]"))
    suffix = " 発火"
    path = _fragment(
        repo,
        "worklog",
        _worklog_body(repo, carry=(), deferred_appends=(("[T-050]", suffix),)),
    )
    fragment, fragment_issues = spool_fold._fragment_from_file(repo, "worklog", path)
    assert fragment_issues == [] and fragment is not None
    delta, delta_issues = spool_fold._parse_worklog_delta(fragment)
    assert delta_issues == [] and delta is not None
    assert delta.operations == ()
    assert tuple((append.task_id, append.suffix) for append in delta.deferred_appends) == (
        ("[T-050]", suffix),
    )

    plan = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    worklog = _target(plan, "docs/worklog.md").after_bytes.decode("utf-8")
    assert _next_action(_entry(worklog, 2)) == (
        f"{_GENERATED_NEXT_ACTION_HEADING}\n\n"
        "- [T-001] (1)\n"
        "- [T-002] (1)\n"
        "- [T-003] (1)\n"
    )


def test_p01_valid_single_worklog_fragment_applies(tmp_path: Path) -> None:
    """P01: 正しい worklog fragment 1 件を fold できる。"""

    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo, new=(("follow-up", "**P2**: 後続"),)))
    _commit(repo, "fragment")
    plan = spool_fold.plan_fold(repo)
    result = spool_fold.apply_fold(repo, plan)
    worklog = (repo / "docs/worklog.md").read_text(encoding="utf-8")
    assert result.status == "applied"
    assert "- [T-052] **P2**: 後続" in worklog
    assert not (repo / plan.gc_paths[0]).exists()


def test_p02_three_ledgers_with_cross_references_apply(tmp_path: Path) -> None:
    """P02: 3 ledger 同時と同一 wave の cross-ledger 参照を受理する。"""

    repo = _repo(tmp_path)
    _fragment(
        repo,
        "worklog",
        _worklog_body(repo, new=(("task", "{{D:decision}} と {{F:failure}} を追う"),), prose="- {{D:decision}} / {{F:failure}}"),
        wave="cross-wave",
    )
    _fragment(
        repo,
        "decisions",
        "## {{D:decision}}. cross ledger\n\n**決定:** {{T:task}} と {{F:failure}}。\n",
        wave="cross-wave",
    )
    _fragment(
        repo,
        "failures",
        "## 新規\n\n### {{F:failure}}. cross failure [手順漏れ]\n"
        "- 事象: {{T:task}}\n- 根本原因: cross\n- 恒久対応: {{D:decision}}\n- 再発検知: test\n",
        wave="cross-wave",
    )
    plan = spool_fold.plan_fold(repo)
    joined = b"\n".join(target.after_bytes for target in plan.targets)
    assert b"{{" not in joined and b"}}" not in joined
    assert b"[T-052]" in joined and b"D2" in joined and b"F2" in joined


def test_p03_empty_spool_is_noop(tmp_path: Path) -> None:
    """P03: fragment 0 件は land を塞がない rc=0 相当の no-op。"""

    repo = _repo(tmp_path)
    plan = spool_fold.plan_fold(repo)
    result = spool_fold.apply_fold(repo, plan)
    assert plan.status == "noop" and result.status == "noop" and not plan.targets


def test_apply_rejects_forged_noop_transaction_payload(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    noop = spool_fold.plan_fold(repo)
    assert spool_fold.apply_fold(repo, noop).status == "noop"

    _fragment(repo, "worklog", _worklog_body(repo))
    pending = _plan_for_commit(repo)
    forged = (
        dataclasses.replace(noop, transaction_id=pending.transaction_id),
        dataclasses.replace(noop, input_closure_sha256=pending.input_closure_sha256),
        dataclasses.replace(noop, targets=pending.targets),
        dataclasses.replace(noop, fragments=pending.fragments),
        dataclasses.replace(noop, gc_paths=pending.gc_paths),
        dataclasses.replace(pending, status="noop"),
    )
    for candidate in forged:
        _transaction_raises(
            "noop plan が non-empty transaction payload",
            spool_fold.apply_fold,
            repo,
            candidate,
        )
    state_path = spool_fold._state_path(repo)
    assert not state_path.exists() and not state_path.is_symlink()


def test_noop_plan_reports_observed_worklog_bytes_with_or_without_canonical_ledgers(
    tmp_path: Path,
) -> None:
    present_root = tmp_path / "present"
    present_root.mkdir()
    present_repo = _repo(present_root)
    worklog_bytes = (present_repo / "docs/worklog.md").read_bytes()
    present_plan = spool_fold.plan_fold(present_repo)

    absent_root = tmp_path / "absent"
    absent_root.mkdir()
    absent_repo = _repo(absent_root)
    for rel in (
        "docs/worklog.md",
        "docs/decisions.md",
        "docs/failures.md",
        "docs/phase3.md",
    ):
        (absent_repo / rel).unlink()
    absent_plan = spool_fold.plan_fold(absent_repo)

    assert present_plan.status == absent_plan.status == "noop"
    assert present_plan.projected_worklog_bytes == len(worklog_bytes)
    assert absent_plan.projected_worklog_bytes == 0


def test_noop_plan_does_not_require_canonical_ledgers_or_write_state(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    origin = _land_origin(repo)
    for rel in (
        "docs/worklog.md",
        "docs/decisions.md",
        "docs/failures.md",
        "docs/phase3.md",
    ):
        (repo / rel).unlink()

    plan = spool_fold.plan_fold(repo, fold_date="2026-08-02", origin=origin)
    result = spool_fold.apply_fold(repo, plan)

    assert plan.status == "noop" and result.status == "noop"
    assert plan.origin == origin
    assert plan.input_closure_sha256 == "" and plan.transaction_id == ""
    assert plan.phase == "applied" and plan.projected_worklog_bytes == 0
    state_path = spool_fold._state_path(repo)
    assert not state_path.exists() and not state_path.is_symlink()
    _transaction_raises(
        "transaction state の transaction_id が不正",
        spool_fold._state_plan,
        spool_fold._plan_state(plan),
    )


def test_non_noop_plan_still_requires_canonical_ledgers(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    (repo / "docs/worklog.md").unlink()

    exc = _raises(
        "canonical",
        spool_fold.plan_fold,
        repo,
        fold_date="2026-08-02",
        origin=_land_origin(repo),
    )
    assert exc.issues[0].path == "docs/worklog.md"


def test_p04_below_threshold_does_not_rotate(tmp_path: Path) -> None:
    """P04: projected worklog が閾値未満なら archive を作らない。"""

    repo = _repo(tmp_path, limit=10_000)
    _fragment(repo, "worklog", _worklog_body(repo))
    plan = spool_fold.plan_fold(repo)
    assert plan.rotation_path is None
    assert all(not target.path.startswith("docs/archive/worklog-") for target in plan.targets)


def test_completion_update_and_defer_form_explicit_sinks(tmp_path: Path) -> None:
    """完了・更新・見送り: base を照合し、本文/次の一手/見送り台帳へ各 sink を生成する。"""

    repo = _repo(tmp_path, active=("[T-001]", "[T-002]", "[T-003]"))
    body = _worklog_body(
        repo,
        carry=(),
        completed=(("[T-001]", "**完了 (本エントリ)**: 終端", _digest(_active_block("[T-001]"))),),
        completion_remaining=True,
        updated=(("[T-002]", "**P1**: 更新本文", _digest(_active_block("[T-002]"))),),
        deferred=(("研究・計測系", "[T-003]", "見送り — 理由: 条件未成立", _digest(_active_block("[T-003]"))),),
    )
    _fragment(repo, "worklog", body)
    plan = spool_fold.plan_fold(repo)
    worklog = _target(plan, "docs/worklog.md").after_bytes.decode("utf-8")
    phase = _target(plan, "docs/phase3.md").after_bytes.decode("utf-8")
    latest = _next_action(_entry(worklog, 2))
    assert "[T-001]" not in latest and "[T-003]" not in latest
    assert latest == (
        f"{_GENERATED_NEXT_ACTION_HEADING}\n\n"
        "- [T-002] **P1**: 更新本文\n"
    )
    assert "- [T-001] **完了 (本エントリ)**: 終端" in worklog
    assert "- [T-003] 見送り — 理由: 条件未成立" in phase


def test_rotation_preserves_d70_archive_current_boundary(tmp_path: Path) -> None:
    """D70: rotation archive の末尾 entry から現行先頭 entry への ID 保存境界を固定する。"""

    repo = _repo(tmp_path, limit=320)
    worklog_path = repo / "docs/worklog.md"
    seed = worklog_path.read_text(encoding="utf-8")
    _write(
        worklog_path,
        seed.replace("- seed body\n", "- seed body " + ("archive filler " * 4) + "\n", 1),
    )
    with worklog_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(
            "\n## 2026-08-01 (2) — boundary\n\n"
            "### 次の一手\n\n- [T-001] 現本文 [T-001]\n"
        )
    before = worklog_path.read_bytes()
    _fragment(repo, "worklog", _worklog_body(repo))
    plan = spool_fold.plan_fold(repo)
    assert plan.rotation_path is not None
    assert (
        len(_target(plan, plan.rotation_path).after_bytes)
        + len(_target(plan, "docs/worklog.md").after_bytes)
        > 320
    )
    archive = _target(plan, plan.rotation_path).after_bytes.decode("utf-8")
    current = _target(plan, "docs/worklog.md").after_bytes.decode("utf-8")
    assert len(current.encode("utf-8")) <= 320
    archive_ids = set(spool_fold.TASK_RE.findall(_next_action(_entry(archive, 1))))
    current_ids = set(spool_fold.TASK_RE.findall(_next_action(_entry(current, 2))))
    assert archive_ids <= current_ids
    first_entry_start = before.index(b"## 2026-08-01 (1)")
    second_entry_start = before.index(b"## 2026-08-01 (2)")
    assert _target(plan, plan.rotation_path).after_bytes == before[first_entry_start:second_entry_start]


def _cli_snapshot(repo: Path) -> dict[str, bytes]:
    return {
        path.relative_to(repo).as_posix(): path.read_bytes()
        for path in sorted(repo.rglob("*"))
        if path.is_file() and ".git" not in path.parts
    }


def _install_cli(repo: Path) -> None:
    shutil.copy2(ROOT / "tools/spool_fold.py", repo / "tools/spool_fold.py")


def _run_cli(repo: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, str(repo / "tools/spool_fold.py"), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _latest_substantive_task_bytes(repo: Path, task_id: str) -> bytes:
    encoded_id = re.escape(task_id.encode("ascii"))
    task_start = re.compile(rb"(?m)^- " + encoded_id + rb"(?= |\n)")
    item_boundary = re.compile(rb"(?m)^(?:- \[T-[0-9]+\](?= |\n)|## )")
    carry_pattern = (
        "- "
        + re.escape(task_id)
        + r" (?:\([1-9][0-9]*\)|変わらず \(\([1-9][0-9]*\) 参照\))\n"
    )
    carry = re.compile(carry_pattern.encode("utf-8"))
    sources = [
        repo / "docs/worklog.md",
        *sorted((repo / "docs/archive").glob("worklog-*.md"), reverse=True),
    ]
    for source in sources:
        source_bytes = source.read_bytes()
        for match in reversed(list(task_start.finditer(source_bytes))):
            boundary = item_boundary.search(source_bytes, match.end())
            end = boundary.start() if boundary is not None else len(source_bytes)
            candidate = source_bytes[match.start():end].rstrip(b"\n") + b"\n"
            if carry.fullmatch(candidate) is None:
                return candidate
    raise AssertionError(f"{task_id} の substantive 本文が real corpus にない")


def test_cli_base_digest_returns_non_carry_item_digest_without_writes(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _install_cli(repo)
    item_bytes = next(
        line
        for line in (repo / "docs/worklog.md").read_bytes().splitlines(keepends=True)
        if line.startswith(b"- [T-001] ")
    )
    expected = (hashlib.sha256(item_bytes).hexdigest() + "\n").encode("ascii")
    before = _cli_snapshot(repo)

    completed = _run_cli(repo, "--base-digest", "[T-001]")

    assert completed.returncode == 0
    assert completed.stdout == expected
    assert completed.stderr == b""
    assert _cli_snapshot(repo) == before


def test_cli_base_digest_resolves_mixed_carry_chain_across_ordinals(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    substantive = "- [T-001] 元実体 A\n".encode("utf-8")
    archive = (
        _global_entry(1, substantive.decode("utf-8"), title="substantive")
        + "\n"
        + _global_entry(
            2,
            "- [T-001] 変わらず ((1) 参照)\n",
            title="legacy carry",
        )
    )
    _write(repo / "docs/archive/worklog-global-chain.md", archive)
    _write(
        repo / "docs/worklog.md",
        _synthetic_worklog(
            _global_entry(3, "- [T-001] (2)\n", title="compact carry")
        ),
    )
    _install_cli(repo)
    archive_bytes = (repo / "docs/archive/worklog-global-chain.md").read_bytes()
    assert archive_bytes.count(substantive) == 1
    expected = (hashlib.sha256(substantive).hexdigest() + "\n").encode("ascii")
    before = _cli_snapshot(repo)

    completed = _run_cli(repo, "--base-digest", "[T-001]")

    assert completed.returncode == 0
    assert completed.stdout == expected
    assert completed.stderr == b""
    assert _cli_snapshot(repo) == before


def test_cli_base_digest_real_corpus_resolves_active_and_rejects_completed(
    tmp_path: Path,
    *,
    _checkout: Path = ROOT,
) -> None:
    repo = _copy_real_canonical_family(tmp_path, checkout=_checkout)
    _install_cli(repo)
    substantive = _latest_substantive_task_bytes(repo, "[T-139]")
    expected = (hashlib.sha256(substantive).hexdigest() + "\n").encode("ascii")
    before = _cli_snapshot(repo)

    active = _run_cli(repo, "--base-digest", "[T-139]")
    completed = _run_cli(repo, "--base-digest", "[T-1049]")

    assert active.returncode == 0
    assert active.stdout == expected
    assert active.stderr == b""
    assert completed.returncode == 1
    assert completed.stdout == b""
    assert completed.stderr
    payload = json.loads(completed.stderr)
    assert [issue["code"] for issue in payload["issues"]] == [
        "base-digest-not-active"
    ]
    assert _cli_snapshot(repo) == before


def test_cli_base_digest_rejects_not_active_id_without_writes(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _install_cli(repo)
    before = _cli_snapshot(repo)

    completed = _run_cli(repo, "--base-digest", "[T-999]")

    assert completed.returncode == 1
    assert completed.stdout == b""
    payload = json.loads(completed.stderr)
    assert [issue["code"] for issue in payload["issues"]] == [
        "base-digest-not-active"
    ]
    assert _cli_snapshot(repo) == before


def test_cli_base_digest_rejects_malformed_task_ids_before_file_read(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _install_cli(repo)
    worklog = repo / "docs/worklog.md"
    worklog.write_bytes(b"not valid UTF-8: \xff\n")
    before = _cli_snapshot(repo)

    for task_id in ("[T-1]", "[T-0001]", "[T-000]", "T-001"):
        completed = _run_cli(repo, "--base-digest", task_id)
        assert completed.returncode == 2
        assert completed.stdout == b""
        assert b"argument --base-digest: canonical task ID" in completed.stderr
        assert b"canonical-utf8" not in completed.stderr

    assert _cli_snapshot(repo) == before


def test_cli_base_digest_accepts_four_digit_task_id(tmp_path: Path) -> None:
    repo = _repo(tmp_path, active=("[T-1000]",))
    _install_cli(repo)
    item_bytes = next(
        line
        for line in (repo / "docs/worklog.md").read_bytes().splitlines(keepends=True)
        if line.startswith(b"- [T-1000] ")
    )
    expected = (hashlib.sha256(item_bytes).hexdigest() + "\n").encode("ascii")
    before = _cli_snapshot(repo)

    completed = _run_cli(repo, "--base-digest", "[T-1000]")

    assert completed.returncode == 0
    assert completed.stdout == expected
    assert completed.stderr == b""
    assert _cli_snapshot(repo) == before


def test_cli_base_digest_rejects_conflicting_modes_without_writes(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _install_cli(repo)
    before = _cli_snapshot(repo)
    cases = (
        (("--dry-run",), b"--base-digest cannot be combined with --dry-run"),
        (("--show-diff",), b"--base-digest cannot be combined with --show-diff"),
        (("--fold-date", "2026-08-02"), b"--base-digest cannot be combined with --fold-date"),
    )

    for extra_args, message in cases:
        completed = _run_cli(repo, "--base-digest", "[T-001]", *extra_args)
        assert completed.returncode == 2
        assert completed.stdout == b""
        assert message in completed.stderr
        assert b"--show-diff requires --dry-run" not in completed.stderr

    assert _cli_snapshot(repo) == before


def test_cli_base_digest_ignores_transaction_state(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _install_cli(repo)
    item_bytes = next(
        line
        for line in (repo / "docs/worklog.md").read_bytes().splitlines(keepends=True)
        if line.startswith(b"- [T-001] ")
    )
    expected = (hashlib.sha256(item_bytes).hexdigest() + "\n").encode("ascii")
    state_path = spool_fold._state_path(repo)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_bytes(b"sentinel transaction state\n")
    before = _cli_snapshot(repo)

    completed = _run_cli(repo, "--base-digest", "[T-001]")

    assert completed.returncode == 0
    assert completed.stdout == expected
    assert completed.stderr == b""
    assert state_path.read_bytes() == b"sentinel transaction state\n"
    assert _cli_snapshot(repo) == before


def _run_cli_with_plan(repo: Path, plan: spool_fold.FoldPlan) -> subprocess.CompletedProcess[bytes]:
    """固定済み plan を CLI へ渡し、planning 後の on-disk fault を注入する。"""

    stdout_buffer = io.BytesIO()
    stderr_buffer = io.BytesIO()
    stdout = io.TextIOWrapper(stdout_buffer, encoding="utf-8", newline="\n")
    stderr = io.TextIOWrapper(stderr_buffer, encoding="utf-8", newline="\n")
    original_stdout, original_stderr = sys.stdout, sys.stderr
    original_file = spool_fold.__file__
    original_plan_fold = spool_fold.plan_fold
    spool_fold.__file__ = str(repo / "tools/spool_fold.py")
    spool_fold.plan_fold = lambda _repo, *, fold_date=None: plan
    try:
        sys.stdout, sys.stderr = stdout, stderr
        returncode = spool_fold.main(
            ["--dry-run", "--show-diff", "--fold-date", plan.fold_date]
        )
        stdout.flush()
        stderr.flush()
        stdout_bytes = stdout_buffer.getvalue()
        stderr_bytes = stderr_buffer.getvalue()
    finally:
        sys.stdout, sys.stderr = original_stdout, original_stderr
        spool_fold.__file__ = original_file
        spool_fold.plan_fold = original_plan_fold
    return subprocess.CompletedProcess(
        [sys.executable, str(repo / "tools/spool_fold.py")],
        returncode,
        stdout_bytes,
        stderr_bytes,
    )


def _hash_line(before: bytes, after: bytes) -> bytes:
    return (
        f"# before_sha256={hashlib.sha256(before).hexdigest()} "
        f"after_sha256={hashlib.sha256(after).hexdigest()}\n"
    ).encode("ascii")


def _diff_hash_lines(diff: bytes) -> list[bytes]:
    return [
        line
        for line in diff.splitlines(keepends=True)
        if line.startswith(b"# before_sha256=")
    ]


def test_cli_dry_run_emits_json_without_writes(tmp_path: Path) -> None:
    """CLI --dry-run: 計画 JSON だけを出し、canonical/fragment/state を変更しない。"""

    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    _install_cli(repo)
    before = _cli_snapshot(repo)
    completed = _run_cli(repo, "--dry-run", "--fold-date", "2026-08-02")
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    after = _cli_snapshot(repo)
    assert payload["status"] == "planned" and payload["targets"]
    assert payload["fold_date"] == "2026-08-02"
    assert completed.stderr == b""
    assert set(payload) == {
        "allocations",
        "fold_date",
        "fragments",
        "gc_paths",
        "projected_worklog_bytes",
        "rotation_path",
        "status",
        "targets",
        "transaction_id",
    }
    assert all(
        set(target) == {"after_sha256", "before_exists", "before_sha256", "path"}
        for target in payload["targets"]
    )
    assert before == after
    assert not spool_fold._state_path(repo).exists()


def test_cli_dry_run_show_diff_keeps_stdout_byte_identical(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    _install_cli(repo)
    plain = _run_cli(repo, "--dry-run", "--fold-date", "2026-08-02")
    shown = _run_cli(repo, "--dry-run", "--show-diff", "--fold-date", "2026-08-02")
    assert plain.returncode == shown.returncode == 0
    assert plain.stderr == b""
    assert shown.stderr
    assert shown.stdout == plain.stdout


def test_cli_dry_run_show_diff_matches_target_after_bytes(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    _install_cli(repo)
    plan = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    expected_hash_lines = [
        _hash_line(
            (repo / target.path).read_bytes() if target.before_exists else b"",
            target.after_bytes,
        )
        for target in plan.targets
    ]
    expected_hash_lines.extend(
        _hash_line((repo / rel).read_bytes(), b"")
        for rel in sorted(plan.gc_paths)
    )
    completed = _run_cli(repo, "--dry-run", "--show-diff", "--fold-date", "2026-08-02")
    assert completed.returncode == 0
    assert _diff_hash_lines(completed.stderr) == expected_hash_lines
    subprocess.run(
        ["git", "-C", str(repo), "apply", "-"],
        check=True,
        input=completed.stderr,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for target in plan.targets:
        assert (repo / target.path).read_bytes() == target.after_bytes


def test_cli_dry_run_show_diff_emits_gc_deletion_diff(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    fragment = _fragment(repo, "worklog", _worklog_body(repo))
    _install_cli(repo)
    plan = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    fragment_body_line = next(
        line
        for line in fragment.read_bytes().splitlines(keepends=True)
        if line == b"- fold \xe6\x9c\xac\xe6\x96\x87\n"
    )
    completed = _run_cli(repo, "--dry-run", "--show-diff", "--fold-date", "2026-08-02")
    assert completed.returncode == 0
    rel = fragment.relative_to(repo).as_posix().encode("utf-8")
    assert b"--- a/" + rel + b"\n" in completed.stderr
    assert b"+++ /dev/null\n" in completed.stderr
    assert b"-" + fragment_body_line in completed.stderr
    subprocess.run(
        ["git", "-C", str(repo), "apply", "-"],
        check=True,
        input=completed.stderr,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert all(not (repo / rel).exists() for rel in plan.gc_paths)


def test_cli_show_diff_emits_nothing_when_target_before_mismatches(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    fragment = _fragment(repo, "worklog", _worklog_body(repo))
    _install_cli(repo)
    plan = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    target = plan.targets[-1]
    target_path = repo / target.path
    target_path.write_bytes(target_path.read_bytes() + b"fault-after-plan\n")
    before = _cli_snapshot(repo)
    fragment_before = fragment.read_bytes()
    state_path = spool_fold._state_path(repo)

    completed = _run_cli_with_plan(repo, plan)

    assert completed.returncode == 2
    assert completed.stderr == (
        json.dumps(
            {
                "error": f"{target.path}: diff before が plan と不一致",
                "status": "transaction-error",
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    assert not any(
        line.startswith((b"---", b"+++", b"@@", b"# before_sha256="))
        for line in completed.stderr.splitlines()
    )
    assert _cli_snapshot(repo) == before
    assert fragment.read_bytes() == fragment_before
    assert not state_path.exists() and not state_path.is_symlink()


def test_cli_show_diff_emits_nothing_when_gc_content_mismatches(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    fragment = _fragment(repo, "worklog", _worklog_body(repo))
    _install_cli(repo)
    plan = spool_fold.plan_fold(repo, fold_date="2026-08-02")
    fragment.write_bytes(fragment.read_bytes() + b"fault-after-plan\n")
    before = _cli_snapshot(repo)
    canonical_before = {
        target.path: (repo / target.path).read_bytes()
        for target in plan.targets
        if target.before_exists
    }
    state_path = spool_fold._state_path(repo)

    completed = _run_cli_with_plan(repo, plan)

    assert completed.returncode == 2
    rel = fragment.relative_to(repo).as_posix()
    assert completed.stderr == (
        json.dumps(
            {
                "error": f"{rel}: diff GC target content が plan と不一致",
                "status": "transaction-error",
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    assert not any(
        line.startswith((b"---", b"+++", b"@@", b"# before_sha256="))
        for line in completed.stderr.splitlines()
    )
    assert _cli_snapshot(repo) == before
    assert {
        path: (repo / path).read_bytes()
        for path in canonical_before
    } == canonical_before
    assert fragment.read_bytes() == before[fragment.relative_to(repo).as_posix()]
    assert not state_path.exists() and not state_path.is_symlink()


def test_cli_show_diff_escapes_terminal_control_bytes(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    fragment = _fragment(
        repo,
        "worklog",
        _worklog_body(
            repo,
            prose="- literal \\x1b; raw ESC \x1b; NUL \x00; DEL \x7f; tab\tok",
        ),
    )
    _install_cli(repo)
    original_fragment = fragment.read_bytes()
    completed = _run_cli(repo, "--dry-run", "--show-diff", "--fold-date", "2026-08-02")
    help_result = _run_cli(repo, "--help")

    assert completed.returncode == help_result.returncode == 0
    assert b"# payload_control_bytes=escaped-c-v1\n" in completed.stderr
    assert b"literal \\\\x1b; raw ESC \\x1b; NUL \\x00; DEL \\x7f; tab\tok" in completed.stderr
    assert not any(
        (value < 0x20 and value not in {0x09, 0x0A}) or value == 0x7F
        for value in completed.stderr
    )
    assert b"\\xNN" in help_result.stdout
    gc_hash = _hash_line(original_fragment, b"")
    assert gc_hash in completed.stderr


def test_diff_lines_escapes_every_terminal_control_byte() -> None:
    unsafe = (
        bytes(value for value in range(0x20) if value not in {0x09, 0x0A})
        + b"\x7f"
    )
    rendered = b"".join(
        spool_fold._diff_lines(
            b"",
            b"literal \\x1b " + unsafe + b" tab\tok\n",
            fromfile=b"/dev/null",
            tofile=b"b/control.txt",
        )
    )

    assert b"# payload_control_bytes=escaped-c-v1\n" in rendered
    assert b"literal \\\\x1b " in rendered
    assert b" tab\tok\n" in rendered
    assert not any(
        (value < 0x20 and value not in {0x09, 0x0A}) or value == 0x7F
        for value in rendered
    )
    for value in unsafe:
        assert f"\\x{value:02x}".encode("ascii") in rendered


def test_diff_lines_keeps_control_free_bytes_identical() -> None:
    before = b"plain \\x1b text\nold\tvalue\n"
    after = b"plain \\x1b text\nnew\tvalue\n"
    expected = b"".join(
        difflib.diff_bytes(
            difflib.unified_diff,
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=b"a/plain.txt",
            tofile=b"b/plain.txt",
        )
    )
    actual = b"".join(
        spool_fold._diff_lines(
            before,
            after,
            fromfile=b"a/plain.txt",
            tofile=b"b/plain.txt",
        )
    )
    assert actual == expected


def test_cli_dry_run_show_diff_noop_emits_no_stderr(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _install_cli(repo)
    plain = _run_cli(repo, "--dry-run", "--fold-date", "2026-08-02")
    shown = _run_cli(repo, "--dry-run", "--show-diff", "--fold-date", "2026-08-02")
    assert plain.returncode == shown.returncode == 0
    assert shown.stderr == b""
    assert shown.stdout == plain.stdout
    payload = json.loads(shown.stdout)
    assert payload["status"] == "noop" and payload["targets"] == []


def test_cli_show_diff_requires_dry_run_without_writes(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    fragment = _fragment(repo, "worklog", _worklog_body(repo))
    _install_cli(repo)
    before = _cli_snapshot(repo)
    canonical_before = (repo / "docs/worklog.md").read_bytes()
    fragment_before = fragment.read_bytes()
    completed = _run_cli(repo, "--show-diff", "--fold-date", "2026-08-02")
    assert completed.returncode == 2
    assert completed.stdout == b""
    assert b"--show-diff requires --dry-run" in completed.stderr
    assert _cli_snapshot(repo) == before
    assert (repo / "docs/worklog.md").read_bytes() == canonical_before
    assert fragment.read_bytes() == fragment_before
    assert not spool_fold._state_path(repo).exists()


def test_cli_dry_run_show_diff_leaves_git_status_unchanged(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
    _install_cli(repo)
    before = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout
    completed = _run_cli(repo, "--dry-run", "--show-diff", "--fold-date", "2026-08-02")
    after = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout
    assert completed.returncode == 0
    assert after == before


def test_cli_dry_run_reports_failure_supersede_semantic_issue_without_writes(tmp_path: Path) -> None:
    """CLI --dry-run: fold-time issue は rc=1 の JSON となり、canonical/state を変更しない。"""

    repo = _repo(tmp_path)
    _fragment(
        repo,
        "failures",
        _failure_body(supersedes=((999, _supersede("CLI missing target")),)),
    )
    shutil.copy2(ROOT / "tools/spool_fold.py", repo / "tools/spool_fold.py")
    before = {
        path.relative_to(repo).as_posix(): path.read_bytes()
        for path in sorted(repo.rglob("*"))
        if path.is_file() and ".git" not in path.parts
    }
    completed = subprocess.run(
        [
            sys.executable,
            str(repo / "tools/spool_fold.py"),
            "--dry-run",
            "--fold-date",
            "2026-08-10",
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    payload = json.loads(completed.stderr)
    after = {
        path.relative_to(repo).as_posix(): path.read_bytes()
        for path in sorted(repo.rglob("*"))
        if path.is_file() and ".git" not in path.parts
    }
    assert completed.returncode == 1 and completed.stdout == ""
    assert payload["status"] == "invalid"
    assert [issue["code"] for issue in payload["issues"]] == [
        "failure-supersede-missing"
    ]
    assert before == after
    assert not spool_fold._state_path(repo).exists()


def _entry(text: str, ordinal: int) -> str:
    headings = list(spool_fold.WORKLOG_ENTRY_RE.finditer(text))
    for index, heading in enumerate(headings):
        if int(heading.group("ordinal")) == ordinal:
            end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            return text[heading.start():end]
    raise AssertionError(f"entry ({ordinal}) がない")


def _next_action(entry: str) -> str:
    heading = spool_fold.NEXT_ACTION_HEADING_RE.search(entry)
    assert heading is not None
    start = heading.start()
    return entry[start:].rstrip("\n") + "\n"


def _active_from_entry(entry: str) -> list[spool_fold._TaskItem]:
    section = _next_action(entry)
    body = section[section.index("\n") + 1 :].lstrip("\n")
    items: list[spool_fold._TaskItem] = []
    for block, _ in spool_fold._split_top_items(body):
        match = spool_fold.TASK_HEAD_RE.match(block)
        assert match is not None
        items.append(spool_fold._TaskItem(match.group("id"), block))
    return items


def _real_entry(ordinal: int) -> str:
    matches: list[str] = []
    paths = [ROOT / "docs/worklog.md", *sorted((ROOT / "docs/archive").glob("worklog-*.md"))]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        headings = list(spool_fold.ARCHIVE_ENTRY_RE.finditer(text))
        for index, heading in enumerate(headings):
            if heading.group("date") != "2026-08-01" or heading.group("ordinal") != str(ordinal):
                continue
            end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            matches.append(text[heading.start():end])
    assert len(matches) == 1, (ordinal, len(matches))
    return matches[0]


@contextmanager
def _fixture_tools_imports(repo: Path) -> Iterator[None]:
    original_path = sys.path[:]
    original_modules = {
        name: module
        for name, module in sys.modules.items()
        if name == "dev_waves" or name.startswith("dev_waves.")
    }
    try:
        for name in original_modules:
            sys.modules.pop(name, None)
        sys.path.insert(0, str(repo / "tools"))
        yield
    finally:
        sys.path[:] = original_path
        for name in tuple(sys.modules):
            if name == "dev_waves" or name.startswith("dev_waves."):
                sys.modules.pop(name, None)
        sys.modules.update(original_modules)


def _real_canonical_sources(checkout: Path) -> tuple[Path, ...]:
    checkout = checkout.resolve()
    fixed_paths = (
        "docs/worklog.md",
        "docs/decisions.md",
        "docs/failures.md",
        "docs/phase3.md",
        "docs/archive/README.md",
        "docs/spool/README.md",
        "docs/spool/FOLDED.md",
        "docs/spool/worklog/README.md",
        "docs/spool/decisions/README.md",
        "docs/spool/failures/README.md",
        "tools/spool_fold.py",
        "tools/check_docs.py",
    )
    sources = [checkout / rel for rel in fixed_paths]
    sources.extend(sorted((checkout / "docs/archive").glob("worklog-*.md")))
    sources.extend(
        source
        for source in sorted((checkout / "tools/dev_waves").rglob("*"))
        if source.is_file() and "__pycache__" not in source.parts and source.suffix != ".pyc"
    )
    return tuple(sources)


def _copy_real_canonical_family(
    tmp_path: Path,
    *,
    checkout: Path = ROOT,
) -> Path:
    checkout = checkout.resolve()
    repo = tmp_path / "real-canonical"
    sources = _real_canonical_sources(checkout)
    for source in sources:
        destination = repo / source.relative_to(checkout)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        assert destination.read_bytes() == source.read_bytes()
    _run_git(repo, "init", "-q")
    _run_git(repo, "config", "user.name", "Fixture")
    _run_git(repo, "config", "user.email", "fixture@example.invalid")
    _commit(repo, "real canonical family")
    return repo


def test_phase3_real_canonical_plan_accepts_unique_and_rejects_generated_duplicate_id(
    tmp_path: Path,
) -> None:
    real_repo = _copy_real_canonical_family(tmp_path / "real")
    real_phase = (real_repo / "docs/phase3.md").read_text(encoding="utf-8")
    spool_fold._assert_deferred_ids_unique(real_phase)
    deferred_items = spool_fold._deferred_items(real_phase)
    assert deferred_items
    item_start, _line_end, block_end = next(iter(deferred_items.values()))[0]
    item_block = real_phase[item_start:block_end]
    duplicated_phase = real_phase[:block_end] + item_block + real_phase[block_end:]
    duplicate_error = _raises(
        "deferred-duplicate",
        spool_fold._assert_deferred_ids_unique,
        duplicated_phase,
    )
    assert [
        (issue.code, issue.path)
        for issue in duplicate_error.issues
    ] == [("deferred-duplicate", "docs/phase3.md")]

    _fragment(
        real_repo,
        "decisions",
        "## {{D:t1922-phase3-positive}}. phase3 一意性の実 canonical 正例\n",
        wave="t1922-phase3-fold-gate-positive",
    )
    with _fixture_tools_imports(real_repo):
        real_plan = spool_fold.plan_fold(real_repo, fold_date="2026-08-02")
    assert real_plan.status == "planned"

    negative_parent = tmp_path / "negative"
    negative_parent.mkdir()
    negative_repo = _repo(negative_parent, active=("[T-050]",))
    _fragment(
        negative_repo,
        "worklog",
        _worklog_body(
            negative_repo,
            carry=(),
            deferred=((
                "プロセス文書系",
                "[T-050]",
                "重複見送り — 理由: 合成負例",
                _digest(_active_block("[T-050]")),
            ),),
        ),
    )
    raised = _raises(
        "deferred-duplicate",
        spool_fold.plan_fold,
        negative_repo,
        fold_date="2026-08-02",
    )
    assert [
        (issue.path, issue.line, issue.code, issue.message)
        for issue in raised.issues
    ] == [(
        "docs/phase3.md",
        9,
        "deferred-duplicate",
        "見送り台帳の ID [T-050] が重複",
    )]

    unique_parent = tmp_path / "unique-deferred"
    unique_parent.mkdir()
    unique_repo = _repo(unique_parent, active=("[T-060]",))
    _fragment(
        unique_repo,
        "worklog",
        _worklog_body(
            unique_repo,
            carry=(),
            deferred=((
                "プロセス文書系",
                "[T-060]",
                "新規見送り — 理由: 過剰拒否防止",
                _digest(_active_block("[T-060]")),
            ),),
        ),
    )
    unique_plan = spool_fold.plan_fold(unique_repo, fold_date="2026-08-02")
    assert unique_plan.status == "planned"

    append_parent = tmp_path / "existing-append"
    append_parent.mkdir()
    append_repo = _repo(append_parent)
    _fragment(
        append_repo,
        "worklog",
        _worklog_body(
            append_repo,
            carry=(),
            deferred_appends=(("[T-050]", " 発火記録: 過剰拒否防止"),),
        ),
    )
    append_plan = spool_fold.plan_fold(append_repo, fold_date="2026-08-02")
    assert append_plan.status == "planned"


def _loaded_dev_waves_modules() -> dict[str, object]:
    return {
        name: module
        for name, module in sys.modules.items()
        if name == "dev_waves" or name.startswith("dev_waves.")
    }


def _assert_dev_waves_modules_restored(expected: dict[str, object]) -> None:
    actual = _loaded_dev_waves_modules()
    assert actual.keys() == expected.keys()
    for name, original_module in expected.items():
        assert actual[name] is original_module


def test_fixture_tools_imports_uses_fixture_restores_state_and_propagates_exceptions(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "fixture-tools"
    for source in _real_canonical_sources(ROOT):
        if source != ROOT / "tools/spool_fold.py" and not (
            ROOT / "tools/dev_waves"
        ) in source.parents:
            continue
        destination = repo / source.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        assert destination.read_bytes() == source.read_bytes()
    probe_name = "dev_waves._fixture_tools_imports_positive_control"
    _write(
        repo / "tools/dev_waves/_fixture_tools_imports_positive_control.py",
        "FIXTURE_ONLY = True\n",
    )

    with _fixture_tools_imports(ROOT):
        preloaded = importlib.import_module("dev_waves.launch_authority")
        path_before = sys.path[:]
        modules_before = _loaded_dev_waves_modules()
        assert modules_before["dev_waves.launch_authority"] is preloaded
        assert probe_name not in modules_before

        with _fixture_tools_imports(repo):
            fixture_module = importlib.import_module("dev_waves.launch_authority")
            module_file = Path(fixture_module.__file__).resolve()
            assert repo.resolve() in module_file.parents
            assert module_file.relative_to(repo.resolve()) == Path(
                "tools/dev_waves/launch_authority.py"
            )
            assert fixture_module is not preloaded
            importlib.import_module(probe_name)
            assert probe_name in sys.modules

        assert sys.path == path_before
        _assert_dev_waves_modules_restored(modules_before)
        assert sys.modules["dev_waves.launch_authority"] is preloaded

        marker = RuntimeError("fixture import context exception probe")
        try:
            with _fixture_tools_imports(repo):
                fixture_module = importlib.import_module(
                    "dev_waves.launch_authority"
                )
                module_file = Path(fixture_module.__file__).resolve()
                assert repo.resolve() in module_file.parents
                importlib.import_module(probe_name)
                assert probe_name in sys.modules
                raise marker
        except RuntimeError as raised:
            assert raised is marker
        else:
            raise AssertionError("_fixture_tools_imports が区間内の例外を握り潰した")

        assert sys.path == path_before
        _assert_dev_waves_modules_restored(modules_before)
        assert sys.modules["dev_waves.launch_authority"] is preloaded


def test_n37_real_repo_canonical_family_requires_archive_active_history(tmp_path: Path) -> None:
    """N37: 実 canonical の archive を active-history 解決へ渡す経路を固定する。"""

    repo = _copy_real_canonical_family(tmp_path)
    worklog = (repo / "docs/worklog.md").read_text(encoding="utf-8")
    archives = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted((repo / "docs/archive").glob("worklog-*.md"))
    }
    _raises("carry-reference", spool_fold._extract_latest_active, worklog, {})
    assert spool_fold._extract_latest_active(worklog, archives)[0] > 0
    current_entries = list(spool_fold.WORKLOG_ENTRY_RE.finditer(worklog))
    assert current_entries
    fold_date = current_entries[-1].group("date")
    fragment = _fragment(
        repo,
        "worklog",
        "## 本文\n\n- 実 canonical family の probe\n\n## 次の一手差分\n",
        authored=fold_date,
        wave="real-repo-probe",
        title="実 canonical family smoke",
    )

    with _fixture_tools_imports(repo):
        plan = spool_fold.plan_fold(repo, fold_date=fold_date)

    assert plan.status == "planned"
    assert len(plan.fragments) == 1
    assert plan.fragments[0].path == fragment.relative_to(repo).as_posix()
    assert plan.fragments[0].path.startswith("docs/spool/worklog/")
    assert plan.gc_paths == (plan.fragments[0].path,)
    target_paths = {target.path for target in plan.targets}
    assert {"docs/worklog.md", "docs/spool/FOLDED.md"} <= target_paths


def test_real_worklog_105_to_106_next_action_is_byte_exact_golden() -> None:
    """実データ golden: (105)→(106) を byte 再現する。歴史的 T-288 の本文語 `消化` は残すが、操作は新語彙の `更新` として扱う。"""

    source = _active_from_entry(_real_entry(105))
    expected_entry = _real_entry(106)
    expected = _next_action(expected_entry)
    frozen_heading = "### 次の一手\n"
    assert expected.startswith(frozen_heading)
    expected = (
        _GENERATED_NEXT_ACTION_HEADING
        + "\n"
        + expected[len(frozen_heading):]
    )
    legacy_carry_re = re.compile(
        r"^- (?P<id>\[T-[0-9]+\]) 変わらず "
        r"\(\((?P<ordinal>[1-9][0-9]*)\) 参照\)$",
        re.MULTILINE,
    )
    expected, replacement_count = legacy_carry_re.subn(
        lambda match: f"- {match.group('id')} ({match.group('ordinal')})",
        expected,
    )
    assert replacement_count == 215
    expected_items = {item.task_id: item.block for item in _active_from_entry(expected_entry)}
    assert len(source) == 216
    assert len(expected_items) == 222
    operations: list[spool_fold._Operation] = []
    for item in source:
        if item.task_id == "[T-288]":
            operations.append(spool_fold._Operation("更新", item.task_id, expected_items[item.task_id], _digest(item.block)))
        else:
            operations.append(spool_fold._Operation("carry", item.task_id, f"- {item.task_id}\n", None))
    allocations: dict[tuple[str, str, str], str] = {}
    for number in range(304, 310):
        task_id = f"[T-{number}]"
        slug = f"golden-{number}"
        allocations[("golden-wave", "T", slug)] = task_id
        block = expected_items[task_id].replace(task_id, f"{{{{T:{slug}}}}}", 1)
        operations.append(spool_fold._Operation("新規", None, block, None, slug=slug))
    actual, _, _, _ = spool_fold._render_next_actions(source, operations, 105, allocations, "golden-wave")
    assert actual.encode("utf-8") == expected.encode("utf-8")


def _run() -> int:
    failures = 0
    errors = 0
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        try:
            parameters = inspect.signature(test).parameters
            if "tmp_path" in parameters:
                with tempfile.TemporaryDirectory(prefix="izanagi-spool-fold-test-") as temporary:
                    test(Path(temporary))
            else:
                test()
        except AssertionError as exc:
            failures += 1
            print(f"FAIL {test.__name__}: {exc}")
        except Exception as exc:  # noqa: BLE001 - plain runner は ERROR を分離表示する。
            errors += 1
            print(f"ERROR {test.__name__}: {type(exc).__name__}: {exc}")
        else:
            print(f"PASS {test.__name__}")
    print(f"{len(tests) - failures - errors} passed, {failures} failed, {errors} errors")
    return 1 if failures or errors else 0


if __name__ == "__main__":
    raise SystemExit(_run())
