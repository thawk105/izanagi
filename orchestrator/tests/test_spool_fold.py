#!/usr/bin/env python3
"""spool_fold の schema、遷移、transaction、golden 回帰。"""

from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("spool_fold_under_test", ROOT / "tools" / "spool_fold.py")
assert SPEC is not None and SPEC.loader is not None
spool_fold = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = spool_fold
SPEC.loader.exec_module(spool_fold)


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


def _commit(repo: Path, message: str = "fixture") -> None:
    _run_git(repo, "add", "-A")
    _run_git(repo, "commit", "-m", message)


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


def _active_block(task_id: str) -> str:
    return _item(task_id, f"現本文 {task_id}")


def _raises(code: str, callable_object, *args):
    try:
        callable_object(*args)
    except spool_fold.SpoolValidationError as exc:
        assert [issue.code for issue in exc.issues] == [code], [issue.code for issue in exc.issues]
        return exc
    raise AssertionError(f"{code} を拒否しなかった")


def _target(plan, rel: str):
    return next(target for target in plan.targets if target.path == rel)


def _phase_after(repo: Path) -> bytes:
    return _target(
        spool_fold.plan_fold(repo, fold_date="2026-08-02"),
        "docs/phase3.md",
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
    expected = "### 次の一手\n\n- [T-001] 変わらず ((1) 参照)\n- [T-002] 変わらず ((1) 参照)\n- [T-003] 変わらず ((1) 参照)\n"
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
    spool_fold.apply_fold(repo, spool_fold.plan_fold(repo))
    _fragment(repo, "worklog", _worklog_body(repo, carry=()), wave="wave-b")
    text = _target(spool_fold.plan_fold(repo), "docs/worklog.md").after_bytes.decode("utf-8")
    tail = text[text.rfind("### 次の一手"):]
    assert tail == (
        "### 次の一手\n\n"
        "- [T-001] 変わらず ((2) 参照)\n"
        "- [T-052] 変わらず ((2) 参照)\n"
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
    spool_fold.apply_fold(repo, spool_fold.plan_fold(repo, fold_date="2026-08-02"))

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
    first = spool_fold.plan_fold(repo)
    result = spool_fold.apply_fold(repo, first)
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
    spool_fold.apply_fold(repo, spool_fold.plan_fold(repo))
    path.write_bytes(raw)
    _raises("receipt-replay", spool_fold.plan_fold, repo)


def test_changed_content_cannot_reuse_folded_symbol_identity(tmp_path: Path) -> None:
    """C-03: content-sha を変えても (wave, namespace, slug) の耐久 identity は再利用不可。"""

    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo, new=(("durable", "first"),)))
    _commit(repo, "first fragment")
    spool_fold.apply_fold(repo, spool_fold.plan_fold(repo))
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
    assert not state_path.exists()


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
    spool_fold.apply_fold(repo, spool_fold.plan_fold(repo, fold_date="2026-08-02"))
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
        "### 次の一手\n\n"
        "- [T-001] 変わらず ((1) 参照)\n"
        "- [T-002] 変わらず ((1) 参照)\n"
        "- [T-003] 変わらず ((1) 参照)\n"
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
    assert latest == "### 次の一手\n\n- [T-002] **P1**: 更新本文\n"
    assert "- [T-001] **完了 (本エントリ)**: 終端" in worklog
    assert "- [T-003] 見送り — 理由: 条件未成立" in phase


def test_rotation_preserves_d70_archive_current_boundary(tmp_path: Path) -> None:
    """D70: rotation archive の末尾 entry から現行先頭 entry への ID 保存境界を固定する。"""

    repo = _repo(tmp_path, limit=320)
    before = (repo / "docs/worklog.md").read_bytes()
    with (repo / "docs/worklog.md").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("\n## 2026-08-01 (2) — boundary seed\n\n- body body body body\n\n### 次の一手\n\n- [T-001] 現本文 [T-001]\n")
    before = (repo / "docs/worklog.md").read_bytes()
    _fragment(repo, "worklog", _worklog_body(repo))
    plan = spool_fold.plan_fold(repo)
    assert plan.rotation_path is not None
    archive = _target(plan, plan.rotation_path).after_bytes.decode("utf-8")
    current = _target(plan, "docs/worklog.md").after_bytes.decode("utf-8")
    archive_ids = set(spool_fold.TASK_RE.findall(_next_action(_entry(archive, 1))))
    current_ids = set(spool_fold.TASK_RE.findall(_next_action(_entry(current, 2))))
    assert archive_ids <= current_ids
    first_entry_start = before.index(b"## 2026-08-01 (1)")
    second_entry_start = before.index(b"## 2026-08-01 (2)")
    assert _target(plan, plan.rotation_path).after_bytes == before[first_entry_start:second_entry_start]


def test_cli_dry_run_emits_json_without_writes(tmp_path: Path) -> None:
    """CLI --dry-run: 計画 JSON だけを出し、canonical/fragment/state を変更しない。"""

    repo = _repo(tmp_path)
    _fragment(repo, "worklog", _worklog_body(repo))
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
            "2026-08-02",
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    payload = json.loads(completed.stdout)
    after = {
        path.relative_to(repo).as_posix(): path.read_bytes()
        for path in sorted(repo.rglob("*"))
        if path.is_file() and ".git" not in path.parts
    }
    assert payload["status"] == "planned" and payload["targets"]
    assert payload["fold_date"] == "2026-08-02"
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


def _copy_real_canonical_family(tmp_path: Path) -> Path:
    checkout = Path(__file__).resolve().parents[2]
    repo = tmp_path / "real-canonical"
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
        "tools/check_docs.py",
    )
    sources = [checkout / rel for rel in fixed_paths]
    sources.extend(sorted((checkout / "docs/archive").glob("worklog-*.md")))
    for source in sources:
        destination = repo / source.relative_to(checkout)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        assert destination.read_bytes() == source.read_bytes()
    return repo


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
