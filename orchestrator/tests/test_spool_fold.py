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
    updated: tuple[tuple[str, str, str], ...] = (),
    new: tuple[tuple[str, str], ...] = (),
    deferred: tuple[tuple[str, str, str, str], ...] = (),
    prose: str = "- fold 本文",
) -> str:
    sections = [f"## 本文\n\n{prose}\n", "## 次の一手差分\n"]
    if carry:
        sections.append("### carry\n\n" + "".join(f"- {task_id}\n" for task_id in carry))
    if completed:
        blocks = ""
        for task_id, text, base in completed:
            blocks += f"- {task_id} {text}\n  base: {base}\n"
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
    _fragment(repo, "worklog", _worklog_body(repo))
    _commit(repo, "fragment")
    plan = spool_fold.plan_fold(repo)
    state_path = spool_fold._state_path(repo)
    state = json.dumps(spool_fold._plan_state(plan), ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode() + b"\n"
    spool_fold._atomic_write(state_path, state)
    first = plan.targets[0]
    spool_fold._atomic_write(repo / first.path, first.after_bytes)
    result = spool_fold.apply_fold(repo, plan)
    assert result.status == "resumed" and first.path in result.resumed_paths
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
    body = _worklog_body(repo, carry=(), completed=(("[T-001]", "一部完了だが残件あり", base),))
    _fragment(repo, "worklog", body)
    issues = spool_fold.validate_spool_tree(repo)
    assert [issue.code for issue in issues] == ["completion-remaining"]


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
