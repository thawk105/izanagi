"""AI provenance の Codex-first 実装面 gate。"""
from __future__ import annotations

import ast
import importlib.util
import os
import sys
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from unittest import mock

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import check_ai_provenance as provenance  # noqa: E402
import check_docs  # noqa: E402
import run_tests as run_tests_tool  # noqa: E402
from orchestrator.campaign import login_headroom as LH  # noqa: E402

site_policy = provenance.site_policy

POLICY_NEEDLE_LITERAL = (
    "Co-Authored-By 候補行はすべて最終 trailer block に置く"
)
IMPLEMENTATION_POLICY_EPOCH = "8c6d3f3bdc716c1ede8febb83ced1b0351a99118"
CLAUDE_AUTHOR = (
    "change\n\n"
    "AI-Agent: product=claude; model=fable-5; reasoning=xhigh; role=author\n"
)
CODEX_AUTHOR = (
    "change\n\n"
    "AI-Agent: product=codex; model=gpt-5.6-sol; reasoning=high; role=author\n"
)
SPLIT_CAB_NONE = (
    "change\n\n"
    "Co-Authored-By: same-value\n\n"
    "AI-Agent: none\n"
)
MULTI_ROLE_NO_SCOPE = (
    "change\n\n"
    "AI-Agent: product=codex; model=gpt-5.6-sol; reasoning=high; role=author\n"
    "AI-Agent: product=claude; model=fable-5; reasoning=xhigh; role=author\n"
)
WAIVER_REASON = "codex-outage"
WAIVER_RATIFIED = "2026-07-31"
WAIVER_LINE = (
    f"AI-Agent-Waiver: reason={WAIVER_REASON}; ratified={WAIVER_RATIFIED}\n"
)
CLAUDE_AUTHOR_WAIVED = CLAUDE_AUTHOR + WAIVER_LINE


def _git(root: Path, *args: str, input_text: str | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _init_repo(root: Path) -> None:
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "Provenance Test")
    _git(root, "config", "user.email", "provenance@example.invalid")


def _commit(root: Path, files: dict[str, str], message: str) -> str:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-F", "-", input_text=message)
    return _git(root, "rev-parse", "HEAD")


def _commit_dated(
    root: Path, files: dict[str, str], message: str, when: str,
) -> str:
    """commit date を明示する。rev-list の既定順 (date 順) を topo 順とずらすため。"""
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    _git(root, "add", "-A")
    result = subprocess.run(
        ["git", "commit", "-q", "-F", "-"],
        cwd=root,
        input=message,
        text=True,
        env={**os.environ, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return _git(root, "rev-parse", "HEAD")


def _policy_history(root: Path) -> tuple[str, str, str]:
    legacy = _commit(
        root,
        {"docs/ai-provenance.md": "# legacy policy\n"},
        SPLIT_CAB_NONE,
    )
    epoch = _commit(
        root,
        {
            "docs/ai-provenance.md": (
                "# policy\n"
                f"{POLICY_NEEDLE_LITERAL}\n"
            ),
        },
        SPLIT_CAB_NONE,
    )
    violating = _commit(
        root,
        {"docs/post-policy.md": "post\n"},
        SPLIT_CAB_NONE,
    )
    return legacy, epoch, violating


def _side_branch_epoch_history(
    root: Path,
    *,
    epoch_text: str,
    side_files: dict[str, str],
    side_message: str,
) -> tuple[list[str], str, str, str]:
    """epoch 導入前に分岐した side commit を merge した最小履歴。"""
    _init_repo(root)
    policy = _commit(
        root,
        {provenance.POLICY_PATH: "# legacy policy\n"},
        CODEX_AUTHOR,
    )
    main_branch = _git(root, "branch", "--show-current")
    _git(root, "switch", "-q", "-c", "side", policy)
    side = _commit(root, side_files, side_message)
    _git(root, "switch", "-q", main_branch)
    epoch = _commit(
        root,
        {provenance.POLICY_PATH: epoch_text},
        CODEX_AUTHOR,
    )
    _git(root, "merge", "--no-ff", "--no-commit", "side")
    head = _commit(root, {}, CODEX_AUTHOR)
    commits = [
        policy,
        *_git(root, "rev-list", "--reverse", f"{policy}..{head}").splitlines(),
    ]
    return commits, head, side, epoch


@dataclass(frozen=True)
class CorrectionHistory:
    base: str
    first_parent: str
    side: str
    target: str
    correction: str
    payload: str


def _install_synthetic_correction_spec(
    monkeypatch: pytest.MonkeyPatch,
    target: str,
) -> str:
    payload = (
        f"target={target}; product=claude; model=claude-opus-5; "
        "reasoning=xhigh; role=integrator"
    )
    monkeypatch.setattr(
        provenance,
        "INCIDENT_6B64D21_FORWARD_CORRECTION",
        provenance.ForwardCorrectionSpec(target=target),
    )
    return payload


def _correction_message(
    payload: str,
    *,
    ai_agent_lines: str = (
        "AI-Agent: product=codex; model=gpt-5.6-sol; "
        "reasoning=high; role=author\n"
    ),
    body: str = "",
) -> str:
    return (
        "forward correction\n\n"
        f"{body}"
        f"{ai_agent_lines}"
        f"AI-Agent-Correction: {payload}\n"
    )


def _make_correction_history(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    target_message: str = "target merge\n",
    side_message: str = CODEX_AUTHOR,
    intermediate: tuple[dict[str, str], str] | None = None,
    correction_builder: Callable[[str], str] | None = None,
    correction_files: dict[str, str] | None = None,
) -> CorrectionHistory:
    _init_repo(root)
    base = _commit(
        root,
        {
            provenance.POLICY_PATH: (
                "# policy\n"
                "scope=\n"
                f"{provenance.IMPLEMENTATION_POLICY_NEEDLE}\n"
                f"{POLICY_NEEDLE_LITERAL}\n"
            ),
        },
        CODEX_AUTHOR,
    )
    main_branch = _git(root, "branch", "--show-current")
    _git(root, "switch", "-q", "-c", "side", base)
    side = _commit(
        root,
        {"docs/side.md": "side\n"},
        side_message,
    )
    _git(root, "switch", "-q", main_branch)
    first_parent = _commit(
        root,
        {"docs/main.md": "main\n"},
        CODEX_AUTHOR,
    )
    _git(root, "merge", "--no-ff", "--no-commit", "side")
    target = _commit(root, {}, target_message)
    payload = _install_synthetic_correction_spec(monkeypatch, target)
    if intermediate is not None:
        _commit(root, intermediate[0], intermediate[1])
    message = (
        correction_builder(payload)
        if correction_builder is not None
        else _correction_message(payload)
    )
    correction = _commit(
        root,
        correction_files or {"docs/correction.md": "correction\n"},
        message,
    )
    monkeypatch.setattr(provenance, "REPO", root)
    return CorrectionHistory(
        base=base,
        first_parent=first_parent,
        side=side,
        target=target,
        correction=correction,
        payload=payload,
    )


def _run_range(
    monkeypatch: pytest.MonkeyPatch,
    rev_range: str,
) -> int:
    """site を必ず明示する。ambient に落とすと実行ホスト依存の別テストに化ける。

    既定 (site=None) は current_site() を読むので、PEGASUS_LOGIN 分類のホストで
    suite を回すと node ごとに実 PBS job を投入して poll し、PEGASUS_SUSPECT では
    全 node が rc=16 で赤になる。site gate の検出力は site= を明示する専用 node
    (login dispatch / suspect 拒否 / message-file 免除 / compute・OTHER 局所監査) が持つ。
    """
    range_arg = (
        f"--range={rev_range}" if rev_range.startswith("--") else "--range"
    )
    argv = (
        ["check_ai_provenance.py", range_arg]
        if rev_range.startswith("--")
        else ["check_ai_provenance.py", range_arg, rev_range]
    )
    monkeypatch.setattr(
        sys,
        "argv",
        argv,
    )
    return provenance.main(site=site_policy.OTHER)


def _known_spec(
    commit: str,
    finding_kind: str = "missing-ai-agent",
    *,
    note: str = "",
    expected_finding_value: str = "",
) -> provenance.KnownViolationSpec:
    return provenance.KnownViolationSpec(
        commit=commit,
        expected_finding_kind=finding_kind,
        ruling="worklog(284) 2026-08-07 /rulings",
        note=note,
        expected_finding_value=expected_finding_value,
    )


@pytest.mark.parametrize(
    ("case", "message"),
    [
        ("cab-absent", "change\n\nAI-Agent: none\n"),
        (
            "cab-before-ai",
            "change\n\nCo-Authored-By: value\nAI-Agent: none\n",
        ),
        (
            "ai-before-cab",
            "change\n\nAI-Agent: none\nCo-Authored-By: value\n",
        ),
        (
            "case-and-colon-whitespace",
            "change\n\ncO-aUtHoReD-bY \t: value\nAI-Agent: none\n",
        ),
        (
            "continuation",
            "change\n\nCo-Authored-By: value\n continuation\nAI-Agent: none\n",
        ),
        (
            "crlf",
            "change\r\n\r\nCo-Authored-By: value\r\nAI-Agent: none\r\n",
        ),
        (
            "exact-duplicate",
            "change\n\nCo-Authored-By: same\n"
            "Co-Authored-By: same\nAI-Agent: none\n",
        ),
        (
            "bullet-and-quote-body",
            "change\n\n- Co-Authored-By: bullet\n"
            "> Co-Authored-By: quote\n\nAI-Agent: none\n",
        ),
        (
            "not-an-email",
            "change\n\nCo-Authored-By: not-an-email\nAI-Agent: none\n",
        ),
    ],
    ids=[
        "cab-absent",
        "cab-before-ai",
        "ai-before-cab",
        "case-and-colon-whitespace",
        "continuation",
        "crlf",
        "exact-duplicate",
        "bullet-and-quote-body",
        "not-an-email",
    ],
)
def test_co_authored_by_accepted_boundary(case: str, message: str):
    base, scoped, cab = provenance.validate_message(case, message)
    assert base == []
    assert scoped == []
    assert cab == []


@pytest.mark.parametrize(
    ("case", "message", "base_needle", "raw", "parsed"),
    [
        (
            "leading-space-indent",
            "change\n\n Co-Authored-By: value\n\nAI-Agent: none\n",
            None,
            1,
            0,
        ),
        (
            "leading-tab-indent",
            "change\n\n\tCo-Authored-By: value\n\nAI-Agent: none\n",
            None,
            1,
            0,
        ),
        (
            "cab-then-blank-then-ai",
            SPLIT_CAB_NONE,
            None,
            1,
            0,
        ),
        (
            "ai-then-blank-then-cab",
            "change\n\nAI-Agent: none\n\nCo-Authored-By: value\n",
            "AI-Agent trailer がない",
            1,
            1,
        ),
        (
            "cab-looking-continuation",
            "change\n\nCo-Authored-By: same\n"
            " Co-Authored-By: same\nAI-Agent: none\n",
            None,
            2,
            1,
        ),
        (
            "body-and-final-same-value",
            "change\n\nCo-Authored-By: same\n\n"
            "Co-Authored-By: same\nAI-Agent: none\n",
            None,
            2,
            1,
        ),
        (
            "trailers-before-divider-body",
            "change\n\nCo-Authored-By: value\nAI-Agent: none\n"
            "---\nbody\n",
            None,
            1,
            0,
        ),
        (
            "backtick-fence-column-zero",
            "change\n\n```text\nCo-Authored-By: fenced\n```\n\n"
            "AI-Agent: none\n",
            None,
            1,
            0,
        ),
        (
            "tilde-fence-column-zero",
            "change\n\n~~~text\nCo-Authored-By: fenced\n~~~\n\n"
            "AI-Agent: none\n",
            None,
            1,
            0,
        ),
    ],
    ids=[
        "leading-space-indent",
        "leading-tab-indent",
        "cab-then-blank-then-ai",
        "ai-then-blank-then-cab",
        "cab-looking-continuation",
        "body-and-final-same-value",
        "trailers-before-divider-body",
        "backtick-fence-column-zero",
        "tilde-fence-column-zero",
    ],
)
def test_co_authored_by_rejected_boundary(
    case: str, message: str, base_needle: str | None, raw: int, parsed: int,
):
    base, _, cab = provenance.validate_message(case, message)
    if base_needle is None:
        assert base == []
    else:
        assert any(base_needle in finding for finding in base)
    if raw == parsed:
        assert cab == []
    else:
        assert cab == [
            f"{case}: Co-Authored-By trailer 配置違反: "
            f"raw={raw}, parsed={parsed}"
        ]


def test_cab_finding_coexists_with_ai_format_and_scope_findings():
    malformed = (
        "change\n\n"
        "Co-Authored-By: body\n\n"
        "AI-Agent: malformed\n"
    )
    base, scoped, cab = provenance.validate_message("format", malformed)
    assert any("AI-Agent の形式違反" in finding for finding in base)
    assert scoped == []
    assert cab == [
        "format: Co-Authored-By trailer 配置違反: raw=1, parsed=0"
    ]

    missing_scope = (
        "change\n\n"
        "Co-Authored-By: body\n\n"
        "AI-Agent: product=codex; model=gpt-5.6-sol; "
        "reasoning=high; role=author\n"
        "AI-Agent: product=claude; model=fable-5; "
        "reasoning=xhigh; role=author\n"
    )
    base, scoped, cab = provenance.validate_message("scope", missing_scope)
    assert base == []
    assert len(scoped) == 2
    assert cab == [
        "scope: Co-Authored-By trailer 配置違反: raw=1, parsed=0"
    ]


def test_legacy_ai_parser_keeps_repo_cwd_alias_and_default_divider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    _init_repo(tmp_path)
    _git(tmp_path, "config", "trailer.agent.key", "AI-Agent:")
    monkeypatch.setattr(provenance, "REPO", tmp_path)

    assert provenance._ai_agent_values(
        "change\n\nAgent: none\n---\nbody\n"
    ) == ["none"]
    assert provenance._ai_agent_values(
        "change\n\n---\nbody\n\nAI-Agent: none\n"
    ) == []


def test_m1_no_divider_changes_only_cab_finding():
    message = (
        "change\n\nCo-Authored-By: value\nAI-Agent: none\n"
        "---\nbody\n"
    )
    base, scoped, cab = provenance.validate_message("m1", message)
    assert base == []
    assert scoped == []
    assert cab == [
        "m1: Co-Authored-By trailer 配置違反: raw=1, parsed=0"
    ]

    legacy = subprocess.run(
        ["git", "interpret-trailers", "--parse"],
        input=message.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    canonical = subprocess.run(
        ["git", "interpret-trailers", "--parse", "--no-divider"],
        input=message.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert legacy.returncode == canonical.returncode == 0
    assert b"AI-Agent: none\n" in legacy.stdout
    assert b"Co-Authored-By: value\n" in legacy.stdout
    assert canonical.stdout == b""


def test_canonical_parser_uses_fresh_ceiling_below_hostile_local_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    hostile = tmp_path / "hostile"
    hostile.mkdir()
    _init_repo(hostile)
    _git(hostile, "config", "trailer.foo.key", "Co-Authored-By:")
    temp_root = hostile / "parser-tmp"
    temp_root.mkdir()
    monkeypatch.setattr(provenance, "TRAILER_PARSE_TEMP_ROOT", temp_root)

    real_run = subprocess.run
    parse_calls: list[tuple[Path, dict[str, str]]] = []

    def recording_run(*args, **kwargs):
        command = args[0]
        if "--no-divider" in command:
            parse_calls.append((Path(kwargs["cwd"]), kwargs["env"]))
        return real_run(*args, **kwargs)

    monkeypatch.setattr(provenance.subprocess, "run", recording_run)
    split_with_alias = (
        "change\n\n"
        "Co-Authored-By: body\n\n"
        "Foo: alias-value\n"
        "AI-Agent: none\n"
    )
    for _ in range(2):
        assert provenance._co_authored_by_findings(
            "hostile-local", split_with_alias
        ) == [
            "hostile-local: Co-Authored-By trailer 配置違反: raw=1, parsed=0"
        ]

    assert len(parse_calls) == 2
    assert parse_calls[0][0] != parse_calls[1][0]
    for cwd, env in parse_calls:
        assert cwd.parent.parent == temp_root
        assert env["GIT_CEILING_DIRECTORIES"] == str(cwd.parent)
        assert not cwd.exists()


def test_canonical_parser_ignores_valid_system_global_and_env_aliases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    global_config = tmp_path / "global.gitconfig"
    global_config.write_text(
        "[trailer \"foo\"]\n"
        "\tkey = Co-Authored-By:\n"
        "[trailer]\n"
        "\tseparators = %\n",
        encoding="utf-8",
    )
    system_config = tmp_path / "system.gitconfig"
    system_config.write_text(
        "[trailer \"baz\"]\n"
        "\tkey = Co-Authored-By:\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(global_config))
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(system_config))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "trailer.bar.key")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "Co-Authored-By:")

    split_with_alias = (
        "change\n\n"
        "Co-Authored-By: body\n\n"
        "Foo: alias-value\n"
        "Bar: alias-value\n"
        "Baz: alias-value\n"
        "AI-Agent: none\n"
    )
    assert provenance._co_authored_by_findings(
        "ambient", split_with_alias
    ) == [
        "ambient: Co-Authored-By trailer 配置違反: raw=1, parsed=0"
    ]


@pytest.mark.parametrize(
    ("case", "separator"),
    [
        ("bare-cr", "\r"),
        ("vertical-tab", "\v"),
        ("form-feed", "\f"),
        ("nel", "\u0085"),
        ("line-separator", "\u2028"),
        ("paragraph-separator", "\u2029"),
    ],
)
def test_canonical_parser_splits_stdout_on_lf_bytes_only(
    case: str, separator: str,
):
    message = (
        "change\n\n"
        "Co-Authored-By: body\n\n"
        f"X: value{separator}Co-Authored-By: phantom\n"
        "AI-Agent: none\n"
    )
    assert provenance._co_authored_by_findings(case, message) == [
        f"{case}: Co-Authored-By trailer 配置違反: raw=1, parsed=0"
    ]


@pytest.mark.parametrize(
    ("stdout", "exception"),
    [
        (b"\xff\n", UnicodeDecodeError),
        (b"AI-Agent: none\nunexpected\n", RuntimeError),
    ],
)
def test_canonical_parser_fails_closed_on_invalid_bytes_or_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stdout: bytes,
    exception: type[Exception],
):
    observed: dict[str, object] = {}

    def fake_run(command, **kwargs):
        observed.update(kwargs)
        return subprocess.CompletedProcess(command, 0, stdout, b"")

    monkeypatch.setattr(provenance, "TRAILER_PARSE_TEMP_ROOT", tmp_path)
    monkeypatch.setattr(provenance.subprocess, "run", fake_run)
    with pytest.raises(exception):
        provenance._parsed_trailers("change\n\nAI-Agent: none\n")
    assert observed["input"] == b"change\n\nAI-Agent: none\n"
    assert "text" not in observed
    assert isinstance(observed["cwd"], Path)
    assert observed["env"]["GIT_CEILING_DIRECTORIES"] == str(
        observed["cwd"].parent
    )


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("orchestrator/campaign/loop.py", True),
        ("orchestrator/schema/receipt.json", True),
        ("orchestrator/README.md", False),
        ("output/env/probe/run.sh", True),
        ("output/insights/result.json", False),
        ("patches/rung.patch", True),
        ("patches/README.md", False),
        ("docs/worklog.md", False),
        ("CMakeLists.txt", True),
        # 受入全走の収集集合を決める制御ファイル。repo 直下なので prefix にも
        # suffix にも当たらず、basename 分類だけが実装面へ入れる (段 4 裁定 M8)。
        ("pytest.ini", True),
        ("./pytest.ini", True),
        # 分類は basename で決まる。同名でない ini は従来どおり非実装面のまま。
        ("docs/notes.ini", False),
    ],
)
def test_implementation_path_contract(path: str, expected: bool):
    assert provenance._is_implementation_path(path) is expected


def test_repo_root_pytest_ini_requires_codex_author():
    """pytest.ini だけを触る AI commit にも D95 の Codex author 契約を発火させる。"""
    assert "pytest.ini" in provenance.IMPLEMENTATION_BASENAMES
    findings, waived_applied = provenance.validate_implementation_author(
        "candidate", CLAUDE_AUTHOR, ["pytest.ini"],
    )
    assert findings == [
        "candidate: 実装面に Codex role=author がない — paths=pytest.ini"
    ]
    assert waived_applied is False
    assert provenance.validate_implementation_author(
        "candidate", CODEX_AUTHOR, ["pytest.ini"],
    ) == ([], False)


def test_repo_ships_the_pytest_ini_that_the_classifier_now_covers():
    """分類の追加が実在ファイルに結線されていること (恒真な保証にしない)。"""
    assert (REPO / "pytest.ini").is_file()
    assert provenance._is_implementation_path("pytest.ini") is True


def test_claude_only_author_is_rejected_for_implementation_positive_control():
    findings, waived_applied = provenance.validate_implementation_author(
        "candidate", CLAUDE_AUTHOR, ["tools/checker.py"],
    )
    assert findings == [
        "candidate: 実装面に Codex role=author がない — paths=tools/checker.py"
    ]
    assert waived_applied is False


def test_codex_author_and_nonimplementation_changes_are_accepted():
    assert provenance.validate_implementation_author(
        "candidate", CODEX_AUTHOR, ["tools/checker.py"],
    ) == ([], False)
    assert provenance.validate_implementation_author(
        "candidate", CLAUDE_AUTHOR, ["docs/worklog.md"],
    ) == ([], False)


def test_human_only_implementation_is_not_misattributed_to_codex():
    assert provenance.validate_implementation_author(
        "candidate", "change\n\nAI-Agent: none\n", ["tools/checker.py"],
    ) == ([], False)


def test_history_gate_starts_at_policy_epoch_and_rejects_followup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    legacy = _commit(
        tmp_path,
        {
            "docs/ai-provenance.md": "# legacy policy\n",
            "tools/legacy.py": "LEGACY = True\n",
        },
        CLAUDE_AUTHOR,
    )
    epoch = _commit(
        tmp_path,
        {
            "docs/ai-provenance.md": (
                "# policy\n"
                f"{provenance.IMPLEMENTATION_POLICY_NEEDLE}\n"
            ),
        },
        CODEX_AUTHOR,
    )
    violating = _commit(
        tmp_path, {"tools/new.py": "NEW = True\n"}, CLAUDE_AUTHOR,
    )

    monkeypatch.setattr(provenance, "REPO", tmp_path)
    assert provenance._implementation_policy_commit() == epoch
    assert not provenance._is_descendant(epoch, legacy)
    assert provenance._commit_paths(violating) == ["tools/new.py"]
    monkeypatch.setattr(
        sys, "argv", ["check_ai_provenance.py", "--range", f"{legacy}..{violating}"],
    )
    assert provenance.main(site=site_policy.OTHER) == 1
    captured = capsys.readouterr()
    assert "実装面に Codex role=author がない — paths=tools/new.py" in captured.err


def test_default_commit_range_uses_plain_reachability_and_policy_prefix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    _init_repo(tmp_path)
    legacy = _commit(tmp_path, {"docs/base.md": "base\n"}, CODEX_AUTHOR)
    main_branch = _git(tmp_path, "branch", "--show-current")
    _git(tmp_path, "switch", "-q", "-c", "pre-policy-side", legacy)
    side = _commit(tmp_path, {"docs/side.md": "side\n"}, CODEX_AUTHOR)
    _git(tmp_path, "switch", "-q", main_branch)
    policy = _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# policy\n"},
        CODEX_AUTHOR,
    )
    _commit(tmp_path, {"docs/main.md": "main\n"}, CODEX_AUTHOR)
    _git(tmp_path, "merge", "--no-ff", "--no-commit", "pre-policy-side")
    head = _commit(tmp_path, {}, CODEX_AUTHOR)

    monkeypatch.setattr(provenance, "REPO", tmp_path)
    expected = _git(
        tmp_path, "rev-list", "--reverse", f"{policy}..{head}",
    ).splitlines()
    observed = provenance._commit_range(None, head=head)
    assert observed == [policy, *expected]
    assert side in observed
    assert side not in _git(
        tmp_path,
        "rev-list",
        "--reverse",
        "--ancestry-path",
        f"{policy}..{head}",
    ).splitlines()


def test_authoritative_scope_epoch_predicate_covers_merged_side_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    side_message = (
        "scope side\n\n"
        "AI-Agent: product=codex; model=gpt-5.6-sol; reasoning=high; "
        "role=author; scope=side\n"
        "AI-Agent: product=codex; model=gpt-5.6-sol; reasoning=high; "
        "role=author\n"
    )
    commits, head, side, _ = _side_branch_epoch_history(
        tmp_path,
        epoch_text="# policy\nscope=\n",
        side_files={"docs/side-scope.md": "side\n"},
        side_message=side_message,
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)

    authoritative = provenance._audit_history(
        commits, authoritative=True, head=head,
    )
    expected = (
        f"{side[:12]} scope side: role=author が複数行あるのに scope がない: "
        "product=codex; model=gpt-5.6-sol; reasoning=high; role=author",
    )
    assert authoritative.findings == list(expected)

    explicit_range = provenance._audit_history(commits)
    assert explicit_range.findings == []


def test_authoritative_implementation_epoch_predicate_covers_merged_side_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    commits, head, side, _ = _side_branch_epoch_history(
        tmp_path,
        epoch_text=f"# policy\n{provenance.IMPLEMENTATION_POLICY_NEEDLE}\n",
        side_files={"tools/side-implementation.py": "side\n"},
        side_message=CLAUDE_AUTHOR,
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)

    authoritative = provenance._audit_history(
        commits, authoritative=True, head=head,
    )
    assert authoritative.findings == [
        f"{side[:12]} change: 実装面に Codex role=author がない — "
        "paths=tools/side-implementation.py",
    ]

    explicit_range = provenance._audit_history(commits)
    assert explicit_range.findings == []


def test_authoritative_cab_predicate_covers_merged_side_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    commits, head, side, _ = _side_branch_epoch_history(
        tmp_path,
        epoch_text=f"# policy\n{POLICY_NEEDLE_LITERAL}\n",
        side_files={"docs/side-cab.md": "side\n"},
        side_message=SPLIT_CAB_NONE,
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)

    authoritative = provenance._audit_history(
        commits, authoritative=True, head=head,
    )
    assert authoritative.findings == [
        f"{side[:12]} change: Co-Authored-By trailer 配置違反: raw=1, parsed=0",
    ]

    explicit_range = provenance._audit_history(commits)
    assert explicit_range.findings == []


def test_authoritative_epoch_and_cab_predicates_keep_absent_rules_inactive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    _init_repo(tmp_path)
    scope_commit = _commit(
        tmp_path,
        {"docs/scope.md": "scope\n"},
        (
            "scope\n\n"
            "AI-Agent: product=codex; model=gpt-5.6-sol; reasoning=high; "
            "role=author; scope=present\n"
            "AI-Agent: product=codex; model=gpt-5.6-sol; reasoning=high; "
            "role=author\n"
        ),
    )
    implementation_commit = _commit(
        tmp_path,
        {"tools/implementation.py": "implementation\n"},
        CLAUDE_AUTHOR,
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    ancestry = provenance._Ancestry(
        {scope_commit: 0, implementation_commit: 1},
        (1, 2),
        0,
    )

    scope_audit = provenance._normal_commit_audit(
        scope_commit,
        scope_epoch=None,
        implementation_epoch=None,
        ancestry=ancestry,
        authoritative=True,
    )
    implementation_audit = provenance._normal_commit_audit(
        implementation_commit,
        scope_epoch=None,
        implementation_epoch=None,
        ancestry=ancestry,
        authoritative=True,
    )
    assert scope_audit.normal_findings == ()
    assert implementation_audit.normal_findings == ()
    assert ancestry.has_cab_policy(scope_commit, authoritative=True) is False
    assert ancestry.has_cab_policy(implementation_commit, authoritative=True) is False


def test_normal_commit_audit_rejects_authoritative_oracle_without_ancestry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    _init_repo(tmp_path)
    commit = _commit(tmp_path, {"docs/commit.md": "commit\n"}, CODEX_AUTHOR)
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    with pytest.raises(RuntimeError, match="authoritative normal audit"):
        provenance._normal_commit_audit(
            commit,
            scope_epoch=None,
            implementation_epoch=None,
            authoritative=True,
        )


def test_authoritative_history_pins_head_once_and_rejects_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# policy\n"},
        CODEX_AUTHOR,
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    real_resolve = provenance._resolve_head
    resolve = mock.Mock(side_effect=real_resolve)
    monkeypatch.setattr(provenance, "_resolve_head", resolve)

    def drift_after_selection(commits, **kwargs):
        _commit(tmp_path, {"docs/drift.md": "drift\n"}, CODEX_AUTHOR)
        return provenance.HistoryAudit(
            ["synthetic finding for drift regression"], [], [],
        )

    monkeypatch.setattr(provenance, "_audit_history", drift_after_selection)
    assert provenance.main([], site=site_policy.OTHER) == 2
    resolve.assert_called_once_with()
    captured = capsys.readouterr().err
    assert "HEAD が監査中に変化した" in captured
    assert "synthetic finding for drift regression" not in captured


def test_explicit_range_and_message_file_skip_authoritative_repository_guards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    _init_repo(tmp_path)
    commit = _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# policy\n"},
        CODEX_AUTHOR,
    )
    message = tmp_path / "message.txt"
    message.write_text("ordinary\n\nAI-Agent: none\n", encoding="utf-8")
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    for name in (
        "_resolve_head",
        "_assert_head_unchanged",
        "_assert_authoritative_repository",
    ):
        monkeypatch.setattr(
            provenance,
            name,
            mock.Mock(side_effect=AssertionError(f"{name} must be skipped")),
        )

    assert provenance.main(
        ["--range", f"{commit}^!"], site=site_policy.OTHER,
    ) == 0
    assert provenance.main(
        ["--message-file", str(message)], site=site_policy.OTHER,
    ) == 0


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("shallow", "shallow repository"),
        ("graft", "with grafts"),
        ("replace", "with git replace"),
    ],
    ids=["shallow", "graft", "replace"],
)
def test_authoritative_repository_rejects_shallow_graft_and_replace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mode: str,
    expected: str,
):
    _init_repo(tmp_path)
    base = _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# policy\n"},
        CODEX_AUTHOR,
    )
    tip = _commit(
        tmp_path, {"docs/tip.md": "tip\n"}, CODEX_AUTHOR,
    )
    if mode == "shallow":
        head = _git(tmp_path, "rev-parse", "HEAD")
        (tmp_path / ".git" / "shallow").write_text(
            f"{head}\n", encoding="ascii",
        )
    elif mode == "graft":
        grafts = Path(_git(tmp_path, "rev-parse", "--git-path", "info/grafts"))
        if not grafts.is_absolute():
            grafts = tmp_path / grafts
        grafts.parent.mkdir(parents=True, exist_ok=True)
        grafts.write_text(f"{tip} {base}\n", encoding="ascii")
    else:
        replacement = _commit(
            tmp_path, {"docs/replacement.md": "replacement\n"}, CODEX_AUTHOR,
        )
        _git(tmp_path, "replace", replacement, base)

    monkeypatch.setattr(provenance, "REPO", tmp_path)
    assert provenance.main([], site=site_policy.OTHER) == 2
    assert expected in capsys.readouterr().err


def test_authoritative_repository_rejects_nonunique_policy_add(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# first policy\n"},
        CODEX_AUTHOR,
    )
    policy_path = tmp_path / provenance.POLICY_PATH
    policy_path.unlink()
    _commit(tmp_path, {"docs/between.md": "between\n"}, CODEX_AUTHOR)
    _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# second policy\n"},
        CODEX_AUTHOR,
    )
    hits = _git(
        tmp_path,
        "log", "--full-history", "--no-renames", "--diff-filter=A",
        "--format=%H", "HEAD", "--", provenance.POLICY_PATH,
    ).splitlines()
    assert len(hits) == 2
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    assert provenance.main([], site=site_policy.OTHER) == 2
    assert "導入 commit が一意でない: hits=2" in capsys.readouterr().err


def test_policy_needle_literal_matches_production_and_repo_policy_exactly_once():
    assert provenance.CO_AUTHORED_BY_POLICY_NEEDLE == POLICY_NEEDLE_LITERAL
    policy = (REPO / provenance.POLICY_PATH).read_text(encoding="utf-8")
    assert policy.count(POLICY_NEEDLE_LITERAL) == 1


def test_cab_default_history_is_nonretroactive_and_rejects_post_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    legacy, _, violating = _policy_history(tmp_path)
    assert SPLIT_CAB_NONE.strip() == _git(
        tmp_path, "show", "-s", "--format=%B", violating,
    )

    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(sys, "argv", ["check_ai_provenance.py"])
    assert provenance.main(site=site_policy.OTHER) == 1
    captured = capsys.readouterr()
    assert "Co-Authored-By trailer 配置違反: raw=1, parsed=0" in captured.err
    assert legacy[:12] not in captured.err


def test_cab_explicit_ranges_accept_pre_policy_and_reject_post_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    legacy, epoch, violating = _policy_history(tmp_path)
    monkeypatch.setattr(provenance, "REPO", tmp_path)

    monkeypatch.setattr(
        sys, "argv", ["check_ai_provenance.py", "--range", legacy],
    )
    assert provenance.main(site=site_policy.OTHER) == 0
    assert "違反なし" in capsys.readouterr().out

    monkeypatch.setattr(
        sys, "argv",
        ["check_ai_provenance.py", "--range", f"{epoch}..{violating}"],
    )
    assert provenance.main(site=site_policy.OTHER) == 1
    assert "Co-Authored-By trailer 配置違反" in capsys.readouterr().err


def test_cab_pre_policy_range_does_not_call_canonical_parser(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    legacy, _, _ = _policy_history(tmp_path)
    parser_calls = 0

    def fail_if_called(message: str) -> dict[str, list[str]]:
        nonlocal parser_calls
        parser_calls += 1
        raise AssertionError(f"pre-policy parser call: {message!r}")

    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(provenance, "_parsed_trailers", fail_if_called)
    monkeypatch.setattr(
        sys, "argv", ["check_ai_provenance.py", "--range", legacy],
    )
    assert provenance.main(site=site_policy.OTHER) == 0
    assert parser_calls == 0
    assert "違反なし" in capsys.readouterr().out


def test_cab_post_policy_parser_failure_fails_closed_with_rc2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    _, epoch, _ = _policy_history(tmp_path)
    parser_calls = 0

    def failing_parser(message: str) -> dict[str, list[str]]:
        nonlocal parser_calls
        parser_calls += 1
        raise RuntimeError("synthetic canonical parser failure")

    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(provenance, "_parsed_trailers", failing_parser)
    monkeypatch.setattr(
        sys, "argv",
        ["check_ai_provenance.py", "--range", f"{epoch}^..{epoch}"],
    )
    assert provenance.main(site=site_policy.OTHER) == 2
    assert parser_calls == 1
    assert "synthetic canonical parser failure" in capsys.readouterr().err


def test_cab_policy_introduction_commit_itself_rejects_split_cab(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    _, epoch, _ = _policy_history(tmp_path)
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_ai_provenance.py", "--range", f"{epoch}^..{epoch}"],
    )
    assert provenance.main(site=site_policy.OTHER) == 1
    captured = capsys.readouterr()
    assert "1 件中 1 違反" in captured.err
    assert "Co-Authored-By trailer 配置違反: raw=1, parsed=0" in captured.err


def test_cab_policy_is_detected_on_range_from_separate_lineage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    legacy = _commit(
        tmp_path,
        {"docs/ai-provenance.md": "# legacy\n"},
        CODEX_AUTHOR,
    )
    main_branch = _git(tmp_path, "branch", "--show-current")
    _git(tmp_path, "switch", "-q", "-c", "policy-lineage", legacy)
    _commit(
        tmp_path,
        {
            "docs/ai-provenance.md": (
                f"{POLICY_NEEDLE_LITERAL}\n"
            ),
        },
        CODEX_AUTHOR,
    )
    violating = _commit(
        tmp_path, {"docs/lineage.md": "bad\n"}, SPLIT_CAB_NONE,
    )
    _git(tmp_path, "switch", "-q", main_branch)

    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        sys, "argv",
        ["check_ai_provenance.py", "--range", f"{violating}^..{violating}"],
    )
    assert provenance.main(site=site_policy.OTHER) == 1
    assert "Co-Authored-By trailer 配置違反" in capsys.readouterr().err


def test_cab_policy_remains_effective_after_policy_text_is_deleted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    _commit(
        tmp_path,
        {
            "docs/ai-provenance.md": (
                f"{POLICY_NEEDLE_LITERAL}\n"
            ),
        },
        CODEX_AUTHOR,
    )
    _commit(
        tmp_path,
        {"docs/ai-provenance.md": "# policy moved\n"},
        CODEX_AUTHOR,
    )
    violating = _commit(
        tmp_path, {"docs/after-deletion.md": "bad\n"}, SPLIT_CAB_NONE,
    )

    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        sys, "argv",
        ["check_ai_provenance.py", "--range", f"{violating}^..{violating}"],
    )
    assert provenance.main(site=site_policy.OTHER) == 1
    assert "Co-Authored-By trailer 配置違反" in capsys.readouterr().err


@pytest.mark.parametrize("diff_renames", ["true", "false"])
def test_cab_policy_detects_rename_in_and_out_with_ambient_renames(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    diff_renames: str,
):
    for direction in ("in", "out"):
        root = tmp_path / direction
        root.mkdir()
        _init_repo(root)
        _git(root, "config", "diff.renames", diff_renames)
        if direction == "in":
            _commit(
                root,
                {"docs/legacy-policy.md": f"{POLICY_NEEDLE_LITERAL}\n"},
                CODEX_AUTHOR,
            )
            _git(
                root,
                "mv",
                "docs/legacy-policy.md",
                provenance.POLICY_PATH,
            )
            renamed = _commit(root, {}, CODEX_AUTHOR)
        else:
            _commit(
                root,
                {provenance.POLICY_PATH: f"{POLICY_NEEDLE_LITERAL}\n"},
                CODEX_AUTHOR,
            )
            _git(
                root,
                "mv",
                provenance.POLICY_PATH,
                "docs/moved-policy.md",
            )
            renamed = _commit(root, {}, CODEX_AUTHOR)

        monkeypatch.setattr(provenance, "REPO", root)
        assert provenance._has_co_authored_by_policy(renamed)


@pytest.mark.parametrize("keep_policy_in_merge", [True, False])
def test_cab_policy_detects_full_history_merge_that_keeps_or_drops_policy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    keep_policy_in_merge: bool,
):
    root = tmp_path / ("keep" if keep_policy_in_merge else "drop")
    root.mkdir()
    _init_repo(root)
    base = _commit(
        root,
        {provenance.POLICY_PATH: "# legacy\n"},
        CODEX_AUTHOR,
    )
    main_branch = _git(root, "branch", "--show-current")
    _git(root, "switch", "-q", "-c", "policy-side", base)
    _commit(
        root,
        {provenance.POLICY_PATH: f"{POLICY_NEEDLE_LITERAL}\n"},
        CODEX_AUTHOR,
    )
    _git(root, "switch", "-q", main_branch)
    _commit(root, {"docs/main.md": "main\n"}, CODEX_AUTHOR)
    _git(root, "merge", "--no-ff", "--no-commit", "policy-side")
    merge_text = (
        f"{POLICY_NEEDLE_LITERAL}\n" if keep_policy_in_merge else "# dropped\n"
    )
    merge_commit = _commit(
        root,
        {provenance.POLICY_PATH: merge_text},
        CODEX_AUTHOR,
    )

    monkeypatch.setattr(provenance, "REPO", root)
    assert provenance._has_co_authored_by_policy(merge_commit)


def test_cab_policy_detects_needle_count_changes_zero_two_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    _init_repo(tmp_path)
    doubled = _commit(
        tmp_path,
        {
            provenance.POLICY_PATH: (
                f"{POLICY_NEEDLE_LITERAL}\n{POLICY_NEEDLE_LITERAL}\n"
            ),
        },
        CODEX_AUTHOR,
    )
    single = _commit(
        tmp_path,
        {provenance.POLICY_PATH: f"{POLICY_NEEDLE_LITERAL}\n"},
        CODEX_AUTHOR,
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    assert provenance._has_co_authored_by_policy(doubled)
    assert provenance._has_co_authored_by_policy(single)


def test_cab_policy_git_error_fails_closed_with_rc2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    _, epoch, violating = _policy_history(tmp_path)
    real_git = provenance._git

    def failing_git(*args: str, input_text: str | None = None) -> str:
        if (
            args[:4] == (
                "log", "--full-history", "--no-renames", "--format=%H"
            )
            and provenance.CO_AUTHORED_BY_POLICY_NEEDLE in args
        ):
            raise RuntimeError("synthetic ancestry failure")
        return real_git(*args, input_text=input_text)

    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(provenance, "_git", failing_git)
    monkeypatch.setattr(
        sys, "argv",
        ["check_ai_provenance.py", "--range", f"{epoch}..{violating}"],
    )
    assert provenance.main(site=site_policy.OTHER) == 2
    assert "synthetic ancestry failure" in capsys.readouterr().err


def test_message_file_gate_uses_staged_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    _commit(
        tmp_path,
        {
            "docs/ai-provenance.md": provenance.IMPLEMENTATION_POLICY_NEEDLE + "\n",
        },
        CODEX_AUTHOR,
    )
    staged = tmp_path / "tools" / "staged.py"
    staged.parent.mkdir(parents=True)
    staged.write_text("STAGED = True\n", encoding="utf-8")
    _git(tmp_path, "add", "tools/staged.py")
    message = tmp_path / "message.txt"
    message.write_text(CLAUDE_AUTHOR, encoding="utf-8")

    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        sys, "argv", ["check_ai_provenance.py", "--message-file", str(message)],
    )
    assert provenance.main(site=site_policy.OTHER) == 1
    captured = capsys.readouterr()
    assert "実装面に Codex role=author がない — paths=tools/staged.py" in captured.err


def test_merge_preflight_and_history_ignore_side_only_implementation_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    base = _commit(
        tmp_path,
        {
            provenance.POLICY_PATH: (
                "scope=\n"
                f"{provenance.IMPLEMENTATION_POLICY_NEEDLE}\n"
            ),
        },
        CODEX_AUTHOR,
    )
    main_branch = _git(tmp_path, "branch", "--show-current")
    _git(tmp_path, "switch", "-q", "-c", "implementation-side", base)
    side = _commit(
        tmp_path,
        {"tools/side_only.py": "SIDE_ONLY = True\n"},
        CODEX_AUTHOR,
    )
    _git(tmp_path, "switch", "-q", main_branch)
    _commit(tmp_path, {"docs/main.md": "main\n"}, CODEX_AUTHOR)
    _git(tmp_path, "merge", "--no-ff", "--no-commit", side)
    monkeypatch.setattr(provenance, "REPO", tmp_path)

    parents = provenance._merge_preflight_parents()
    assert provenance._message_file_paths(parents) == []
    message = tmp_path / ".git" / "preflight-message"
    message.write_text(CLAUDE_AUTHOR, encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_ai_provenance.py", "--message-file", str(message)],
    )
    assert provenance.main(site=site_policy.OTHER) == 0
    assert "違反なし" in capsys.readouterr().out

    merge = _commit(tmp_path, {}, CLAUDE_AUTHOR)
    assert provenance._commit_paths(merge) == []
    audit = provenance._normal_commit_audit(
        merge,
        scope_epoch=base,
        implementation_epoch=base,
    )
    assert audit.normal_findings == ()


def test_merge_preflight_and_history_ignore_nonconflicting_shared_implementation_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _init_repo(tmp_path)
    shared_lines = [f"line {index}" for index in range(1, 37)]

    def render(lines: list[str]) -> str:
        return "\n".join(lines) + "\n"

    base = _commit(
        tmp_path,
        {
            provenance.POLICY_PATH: (
                "scope=\n"
                f"{provenance.IMPLEMENTATION_POLICY_NEEDLE}\n"
            ),
            "tools/shared_lines.py": render(shared_lines),
        },
        CODEX_AUTHOR,
    )
    main_branch = _git(tmp_path, "branch", "--show-current")
    _git(tmp_path, "switch", "-q", "-c", "implementation-side", base)
    side_lines = shared_lines.copy()
    side_lines[4] = "side edit line 5"
    side = _commit(
        tmp_path,
        {"tools/shared_lines.py": render(side_lines)},
        CODEX_AUTHOR,
    )
    _git(tmp_path, "switch", "-q", main_branch)
    main_lines = shared_lines.copy()
    main_lines[31] = "main edit line 32"
    _commit(
        tmp_path,
        {"tools/shared_lines.py": render(main_lines)},
        CODEX_AUTHOR,
    )

    merged = subprocess.run(
        ["git", "merge", "--no-ff", "--no-commit", side],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert merged.returncode == 0, merged.stderr
    monkeypatch.setattr(provenance, "REPO", tmp_path)

    # 意図した既知の非対称性: _message_file_paths() (commit前のpreflight) は今回のwaveでは
    # 未修正のまま残しており、この非衝突mergeでも保守的にCodex role=authorを要求し続ける
    # (段4裁定・ユーザー承認済み。_commit_paths() だけが修正対象)。
    parents = provenance._merge_preflight_parents()
    assert provenance._message_file_paths(parents) == ["tools/shared_lines.py"]

    merge = _commit(tmp_path, {}, CLAUDE_AUTHOR)
    assert len(provenance._commit_parents(merge)) == 2
    assert provenance._commit_paths(merge) == []
    audit = provenance._normal_commit_audit(
        merge,
        scope_epoch=base,
        implementation_epoch=base,
    )
    assert audit.normal_findings == ()


def test_combined_diff_uses_raw_bytes_for_invalid_utf8_shared_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _init_repo(tmp_path)
    invalid_path = tmp_path / "tools" / "invalid_utf8.py"
    invalid_path.parent.mkdir(parents=True, exist_ok=True)
    invalid_path.write_bytes(b"line 1\n\xff\xfe invalid utf8 line\nline 3\n")
    base = _commit(
        tmp_path,
        {
            provenance.POLICY_PATH: (
                "scope=\n"
                f"{provenance.IMPLEMENTATION_POLICY_NEEDLE}\n"
            ),
        },
        CODEX_AUTHOR,
    )
    main_branch = _git(tmp_path, "branch", "--show-current")
    _git(tmp_path, "switch", "-q", "-c", "invalid-utf8-side", base)
    invalid_path.write_bytes(b"line 1\n\xff\xfe invalid utf8 line\nside line 3\n")
    side = _commit(tmp_path, {}, CODEX_AUTHOR)
    _git(tmp_path, "switch", "-q", main_branch)
    invalid_path.write_bytes(b"main line 1\n\xff\xfe invalid utf8 line\nline 3\n")
    _commit(tmp_path, {}, CODEX_AUTHOR)

    merged = subprocess.run(
        ["git", "merge", "--no-ff", "-m", CLAUDE_AUTHOR, side],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert merged.returncode == 0, merged.stderr
    merge = _git(tmp_path, "rev-parse", "HEAD")
    monkeypatch.setattr(provenance, "REPO", tmp_path)

    assert len(provenance._commit_parents(merge)) == 2
    # 3行の file で 1 行目・3 行目をそれぞれ別 parent が編集すると、間の context が
    # 1 行しかないため git の combined diff は 1 hunk へ結合され非自明になる (親が
    # 素の git コマンドで実測済み)。このテストの目的は trivial 判定の正しさではなく、
    # 不正 UTF-8 バイト列を含む merge でもクラッシュせず正しく (非自明として) 検出できる
    # ことの確認である。
    assert provenance._commit_paths(merge) == ["tools/invalid_utf8.py"]


def test_octopus_merge_combined_diff_filters_nonconflicting_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _init_repo(tmp_path)
    base_lines = [f"line {index}" for index in range(1, 37)]

    def render(lines: list[str]) -> str:
        return "\n".join(lines) + "\n"

    base = _commit(
        tmp_path,
        {
            provenance.POLICY_PATH: (
                "scope=\n"
                f"{provenance.IMPLEMENTATION_POLICY_NEEDLE}\n"
            ),
            "tools/shared_lines.py": render(base_lines),
            "tools/resolution.py": render(base_lines),
        },
        CODEX_AUTHOR,
    )
    main_branch = _git(tmp_path, "branch", "--show-current")
    branches: list[str] = []
    for branch_index, line_index in enumerate((4, 18, 32)):
        branch_name = f"octopus-side-{branch_index}"
        _git(tmp_path, "switch", "-q", "-c", branch_name, base)
        branch_lines = base_lines.copy()
        branch_lines[line_index] = f"side {branch_index} edit line {line_index + 1}"
        branches.append(
            _commit(
                tmp_path,
                {
                    "tools/shared_lines.py": render(branch_lines),
                    "tools/resolution.py": render(branch_lines),
                },
                CODEX_AUTHOR,
            )
        )
    _git(tmp_path, "switch", "-q", main_branch)

    merged = subprocess.run(
        ["git", "merge", "--no-ff", "--no-commit", *branches],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert merged.returncode == 0, merged.stderr
    resolution = (tmp_path / "tools" / "resolution.py").read_text(
        encoding="utf-8",
    ) + "merge-authored line\n"
    merge = _commit(
        tmp_path,
        {"tools/resolution.py": resolution},
        CLAUDE_AUTHOR,
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)

    assert len(provenance._commit_parents(merge)) == 4
    assert provenance._commit_paths(merge) == ["tools/resolution.py"]
    audit = provenance._normal_commit_audit(
        merge,
        scope_epoch=base,
        implementation_epoch=base,
    )
    assert audit.normal_findings == (
        provenance.NormalFinding(
            f"{audit.label}: 実装面に Codex role=author がない — "
            "paths=tools/resolution.py",
            "missing-codex-author",
        ),
    )


def test_merge_preflight_and_history_count_all_parent_different_resolution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    base = _commit(
        tmp_path,
        {
            provenance.POLICY_PATH: (
                "scope=\n"
                f"{provenance.IMPLEMENTATION_POLICY_NEEDLE}\n"
            ),
            "tools/resolution.py": "VALUE = 'base'\n",
        },
        CODEX_AUTHOR,
    )
    main_branch = _git(tmp_path, "branch", "--show-current")
    _git(tmp_path, "switch", "-q", "-c", "resolution-side", base)
    side = _commit(
        tmp_path,
        {"tools/resolution.py": "VALUE = 'side'\n"},
        CODEX_AUTHOR,
    )
    _git(tmp_path, "switch", "-q", main_branch)
    _commit(
        tmp_path,
        {"tools/resolution.py": "VALUE = 'main'\n"},
        CODEX_AUTHOR,
    )
    conflict = subprocess.run(
        ["git", "merge", "--no-ff", "--no-commit", side],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert conflict.returncode == 1
    (tmp_path / "tools" / "resolution.py").write_text(
        "VALUE = 'resolved'\n",
        encoding="utf-8",
    )
    _git(tmp_path, "add", "tools/resolution.py")
    monkeypatch.setattr(provenance, "REPO", tmp_path)

    parents = provenance._merge_preflight_parents()
    assert provenance._message_file_paths(parents) == ["tools/resolution.py"]
    message = tmp_path / ".git" / "preflight-message"
    message.write_text(CLAUDE_AUTHOR, encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_ai_provenance.py", "--message-file", str(message)],
    )
    assert provenance.main(site=site_policy.OTHER) == 1
    captured = capsys.readouterr()
    assert "実装面に Codex role=author がない — paths=tools/resolution.py" in captured.err

    merge = _commit(tmp_path, {}, CLAUDE_AUTHOR)
    assert provenance._commit_paths(merge) == ["tools/resolution.py"]
    audit = provenance._normal_commit_audit(
        merge,
        scope_epoch=base,
        implementation_epoch=base,
    )
    assert audit.normal_findings == (
        provenance.NormalFinding(
            f"{audit.label}: 実装面に Codex role=author がない — "
            "paths=tools/resolution.py",
            "missing-codex-author",
        ),
    )


def test_message_file_malformed_merge_head_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    _commit(tmp_path, {"docs/base.md": "base\n"}, CODEX_AUTHOR)
    (tmp_path / ".git" / "MERGE_HEAD").write_text(
        "not-an-object-id\n",
        encoding="ascii",
    )
    message = tmp_path / ".git" / "preflight-message"
    message.write_text(CODEX_AUTHOR, encoding="utf-8")
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_ai_provenance.py", "--message-file", str(message)],
    )
    assert provenance.main(site=site_policy.OTHER) == 2
    assert "MERGE_HEAD is malformed" in capsys.readouterr().err


def test_message_file_merge_head_read_error_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    commit = _commit(tmp_path, {"docs/base.md": "base\n"}, CODEX_AUTHOR)
    (tmp_path / ".git" / "MERGE_HEAD").write_text(
        f"{commit}\n",
        encoding="ascii",
    )
    message = tmp_path / ".git" / "preflight-message"
    message.write_text(CODEX_AUTHOR, encoding="utf-8")
    real_read_text = Path.read_text

    def fail_merge_head(path: Path, *args, **kwargs):
        if path.name == "MERGE_HEAD":
            raise PermissionError("synthetic MERGE_HEAD read failure")
        return real_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fail_merge_head)
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_ai_provenance.py", "--message-file", str(message)],
    )
    assert provenance.main(site=site_policy.OTHER) == 2
    assert "synthetic MERGE_HEAD read failure" in capsys.readouterr().err


def test_message_file_always_rejects_split_cab_without_policy_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    message = tmp_path / "message.txt"
    message.write_text(SPLIT_CAB_NONE, encoding="utf-8")

    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        sys, "argv", ["check_ai_provenance.py", "--message-file", str(message)],
    )
    assert provenance.main(site=site_policy.OTHER) == 1
    captured = capsys.readouterr()
    assert "Co-Authored-By trailer 配置違反: raw=1, parsed=0" in captured.err
    assert "AI-Agent trailer がない" not in captured.err


def test_message_file_parser_failure_fails_closed_with_rc2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    message = tmp_path / "message.txt"
    message.write_text(
        "change\n\nAI-Agent: none\n",
        encoding="utf-8",
    )
    parser_calls = 0

    def failing_parser(message_text: str) -> dict[str, list[str]]:
        nonlocal parser_calls
        parser_calls += 1
        raise RuntimeError("synthetic message-file parser failure")

    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(provenance, "_parsed_trailers", failing_parser)
    monkeypatch.setattr(
        sys, "argv", ["check_ai_provenance.py", "--message-file", str(message)],
    )
    assert provenance.main(site=site_policy.OTHER) == 2
    assert parser_calls == 1
    assert "synthetic message-file parser failure" in capsys.readouterr().err


def test_message_file_accepts_contiguous_cab_without_policy_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    message = tmp_path / "message.txt"
    message.write_text(
        "change\n\nCo-Authored-By: value\nAI-Agent: none\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        sys, "argv", ["check_ai_provenance.py", "--message-file", str(message)],
    )
    assert provenance.main(site=site_policy.OTHER) == 0
    assert "違反なし" in capsys.readouterr().out


def test_known_violation_ledger_matches_literal_entries():
    malformed_value = (
        "product=claude; model=claude-opus-5[1m]; reasoning=high; "
        "role=orchestrator"
    )
    malformed_ruling = (
        "2026-08-09 dev-wave-jobs/rulings-inbox/"
        "2026-08-09-t139-r4-probe-provenance-format-violation.md"
    )
    malformed_note = (
        "実装面は Codex `role=author` が書き親が統合したため内容は正確で綴りだけの誤り；"
        "不適合は model の角括弧と role=orchestrator；22 件の trailer literal は同一；"
    )
    t316_ruling = (
        "2026-08-12 dev-wave-t316-r2-oracle land 前裁定 "
        "(ユーザー選択: known-violation 登録)"
    )
    t316_note = (
        "main 取り込み merge が `external/ccbench` の gitlink（submodule ポインタ）を"
        "古い側で確定させたことの是正；変更は d706650c → 511c9538 のポインタ更新のみで"
        "ソース著作なし；親作成 commit のため Codex 著者とは記さない"
    )
    t470_merge2_ruling = (
        "2026-08-20 dev-wave-t470-accepted-consumer land 前裁定 "
        "(2回目、ユーザー選択: known-violation 登録)"
    )
    t470_merge2_note = (
        "2回目の local main 取り込み merge。`tools/check_ai_provenance.py` / "
        "`orchestrator/tests/test_check_ai_provenance.py` で、本 wave が追加した T-470 の "
        "known-violation エントリと main 側の別裁定 (T-619) のエントリが同じ末尾へ競合し、"
        "両方を残すだけの union で解決した。`orchestrator/tests/test_layer3_report.py` は "
        "main 側の新規変更と衝突しなかった。`git diff-tree --cc a5b7045b` は全差分行が "
        "いずれかの親に既存で、両親のどちらにも無い新規行はない。wave 側の実装面は Codex "
        "`role=author` が commit `c0936079` / `2d111bfc` / `d59f53d4` で書き、main 側は各 wave "
        "の land 時に監査済み。親作成 merge のため Codex 著者とは記さない。"
    )
    t567_merge2_ruling = (
        "2026-08-21 dev-wave-t567-attempt-binding land 前裁定 "
        "(2回目、ユーザー選択: known-violation 登録)"
    )
    t567_merge2_note = (
        "2回目の受入投入前 local main 取り込み merge "
        "`5823caf328a5985476cd2f6f7aa0d13daa5b08f6`。`tools/check_ai_provenance.py` / "
        "`orchestrator/tests/test_check_ai_provenance.py` で、本 wave が追加した T-567 の "
        "known-violation エントリと main 側の別 wave (T-565、merge "
        "`76248294bf40eb7fa0d806ce4df5010d685036de`) のエントリが同じ末尾へ競合し、"
        "両方を残すだけの union で解決した。`orchestrator/tests/test_campaign.py` は "
        "main 側の新規変更と衝突しなかった。`git diff-tree --cc "
        "5823caf328a5985476cd2f6f7aa0d13daa5b08f6 -- "
        "orchestrator/tests/test_campaign.py orchestrator/tests/test_check_ai_provenance.py "
        "tools/check_ai_provenance.py` では `test_campaign.py` が combined diff に現れず、"
        "2 checker file の追加行もいずれかの親に既存で、両親のどちらにも無い新規行はない。"
        "結果は両側の known-violation エントリを並べただけの union で、競合解決による新規著作なし。"
        "親作成 merge のため Codex 著者とは記さない。"
    )
    t1479_merge_ruling = (
        "2026-08-22 dev-wave-t1479-known-violation-merge-authorship "
        "受入前裁定 (ユーザー選択: known-violation 登録)"
    )
    t1479_merge_note = (
        "受入投入前に親が作成した local main `a714e8e0` 取り込み merge。wave 側が削除済みと検証した "
        "19 SHA は main 側に残っていても削除し、main 側が独立追加した新規5エントリ "
        "(T-1371 の3 merge、`09ce607b`、`13101ab3`) は保持する基準で解決した。"
        "この基準は新規著作ではなく既存 entry の取捨選択である。`git diff-tree --cc "
        "8440a14850718e63d73dfc510aa66b853a526424 -- tools/check_ai_provenance.py "
        "orchestrator/tests/test_check_ai_provenance.py` が非自明になるのは、削除された行と保持された行が"
        "混在するためである。`dev_wave_codex.py` の authority-snapshot 検査が mid-merge・conflict マーカーありの "
        "working tree を拒否したため Codex に委任できず、親が直接解決した（job-id `t1479-merge-resolve1`、rc=2）。"
        "親作成 merge のため Codex 著者とは記さない。"
    )
    t1479_merge2_ruling = (
        "2026-08-22 dev-wave-t1479-known-violation-merge-authorship "
        "受入前裁定 (2回目、ユーザー選択: known-violation 登録)"
    )
    t1479_merge2_note = (
        "受入投入前に親が作成した local main `aa20419e` 取り込み merge。wave側 (T-1479のmerge登録) と"
        " main側 (T-755起源の3件) が `KNOWN_PROVENANCE_VIOLATIONS` タプル末尾で競合したが、削除は無く"
        "純粋な追加同士のunionで解決した。`git diff-tree --cc e39a8d46567a02d231fce52abae5aee759634ff7 -- "
        "tools/check_ai_provenance.py orchestrator/tests/test_check_ai_provenance.py` が非自明になるのは、"
        "両側の追加が互いに相手に無い新規行として現れるためである。親作成 merge のため Codex 著者とは記さない。"
    )
    t1479_merge3_ruling = (
        "2026-08-22 dev-wave-t1479-known-violation-merge-authorship "
        "受入前裁定 (3回目、ユーザー選択: known-violation 登録)"
    )
    t1479_merge3_note = (
        "受入投入前に親が作成した local main `93a274a2` 取り込み merge。wave側の既存2件 "
        "(`8440a14850718e63d73dfc510aa66b853a526424`、`e39a8d46567a02d231fce52abae5aee759634ff7`) と "
        "main側 (T-1476) の既存2件 (`6f2d97c88aa66e571771d5b83992fcfd6d2aefaa`、"
        "`3eaf2038ec2ac3e7965c2a1eedcadb1ed1266626`) が `KNOWN_PROVENANCE_VIOLATIONS` タプル末尾で競合し、"
        "削除なしの純粋なunionで解決した。親作成mergeのためCodex著者とは記さない。"
    )
    t1477_ruling = (
        "2026-08-22 [T-1477] provenance known-violation登録 "
        "(ユーザー選択: known-violation 登録)"
    )
    t1477_note = (
        "`role=fix` は許可値でなく `author` の誤記。実装は Codex `role=author` が書き親が統合したもので、"
        "内容は正確で綴りだけの誤り"
    )
    t1477_malformed_value = (
        "product=codex; model=gpt-5.6-luna; reasoning=unknown; "
        "role=fix"
    )
    observed = tuple(
        (
            spec.commit,
            spec.expected_finding_kind,
            spec.ruling,
            spec.note,
            spec.expected_finding_value,
        )
        for spec in provenance.KNOWN_PROVENANCE_VIOLATIONS
    )
    expected = (
        ("88f0f9f081f7c76c8ab5fc4a94e2640f70af129b", "missing-ai-agent", "worklog(284) 2026-08-07 /rulings", "", ""),
        ("85dacc27054db0bd3db55d73cab4f8ca3b4843e5", "missing-ai-agent", "worklog(284) 2026-08-07 /rulings", "", ""),
        ("6e69ca5c2bc2df403e1cda595aeffcba3a97c248", "missing-ai-agent", "worklog(284) 2026-08-07 /rulings", "", ""),
        ("16affe169185040b33f8c6cbdd452260bddc4089", "missing-ai-agent", "worklog(284) 2026-08-07 /rulings", "", ""),
        ("905c867a7b2342ff250a1bcf28a3ce74abdacc06", "missing-ai-agent", "worklog(284) 2026-08-07 /rulings", "", ""),
        ("b0a07672737cf03424ec1790cc25a06e4c85b737", "missing-codex-author", "worklog(284) 2026-08-07 /rulings", "", ""),
        (
            "3f2c43d7580b8c26724d90278589862057508965",
            "missing-ai-agent",
            "worklog(293) 2026-08-07 /rulings",
            "trailer は本文に実在するが、AI-Agent 行と Co-Authored-By 行の間の空行で trailer block 不成立",
            "",
        ),
        ("f277efd4461d361d5c9aa6db9a7e00b194b76083", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=実装面（test・probe・PBS wrapper・機械設定、insight docs 併記）", malformed_value),
        ("74b501962092373ba2e8bbca1566d0732e0f16c6", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=merge（全 parent 共通の combined path なし）", malformed_value),
        ("7ec088163dee920f0b8e1e9783faa6e36b22b730", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=実装面（test・probe・PBS wrapper・契約、runbook・insight docs 併記）", malformed_value),
        ("1d09940463ccacb0dbb0ab3e69ca0698a960fdf1", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=merge（全 parent 共通の combined path なし）", malformed_value),
        ("f1406c22abece76276b43dde897750a46aae877e", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=実装面（test・probe・shell wrapper）", malformed_value),
        ("a567eb68d85d2ea4db6002c12a0ee59d2a5cd69f", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=変異台帳（mutation-spec.json）", malformed_value),
        ("ff264975a04aa19f36f861ca97efe9dc59c88659", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=変異台帳（mutation-spec.json）", malformed_value),
        (
            "2c1929533a6f641b513f4f7990fe06e6cdb383b1",
            "missing-codex-author",
            "2026-08-09 dev-wave-jobs/rulings-inbox/2026-08-09-t659-provenance-and-f37-rulings.md",
            "親作成の所在不問 Python probe を含む実装面 commit に Codex role=author が欠落；変更 path 種別=実装面（verbatim/probe_split_window.py、.md 逐語移行対象）",
            "",
        ),
        ("9af3e7a0f1c82fb91f310b5c9d197ec4a45f1320", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=変異台帳（mutation-spec.json）", malformed_value),
        ("6fa5bde0d4e685141e3aa7f6de0ebdcda6b148ec", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=変異台帳（mutation-ledger.json）", malformed_value),
        ("2b3d06cbe81b1ae2675c153bdf307d508fc35a20", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=docs（submission receipt）", malformed_value),
        ("30719e517dcee45c014cbf1052c6dc70a8fcf693", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=docs（submission receipt）", malformed_value),
        ("1fa2b75b09b0b0e2e0e27a6f2cbedb058e8eb9f7", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=実装面（test・probe、実測成果物併記）", malformed_value),
        ("622bd786191d40bda388596fa2adbf119ee84c9a", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=実測成果物・docs（追補 A・package・receipt）", malformed_value),
        ("c75fde903384b6eb9e4d45239b66008b7639cbf7", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=merge（combined path は docs/pegasus-runbook.md）", malformed_value),
        ("c55ace29e55bba948d7bdca89f6fc1fb1a5191da", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=docs（worklog fragment）", malformed_value),
        ("edf74c94427686f2b91519ef10e94446d0fe89d5", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=merge（全 parent 共通の combined path なし）", malformed_value),
        ("7e3cc116f2466fb439ec2bddd38f35dab928c942", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=merge（全 parent 共通の combined path なし）", malformed_value),
        ("66769067ee57d78650b208b9a86438ff2f1bf73b", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=merge（全 parent 共通の combined path なし）", malformed_value),
        ("1f884f6f6042cd8b1ce3f16f0bc7db3d97b768aa", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=docs（worklog fragment）", malformed_value),
        ("aaffa644a969f0a58969b2661318bda4c42ac767", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=merge（全 parent 共通の combined path なし）", malformed_value),
        ("6f5411ceb7cc5d872e3112fb6d04013367ac092e", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=docs（worklog fragment）", malformed_value),
        ("797db5def66ef1d318d06c7aa189ea51a66c9312", "malformed-ai-agent", malformed_ruling, malformed_note + "変更 path 種別=docs（worklog fragment）", malformed_value),
        ("8ceebcdbe40fac27cb2a1fbd7a1b1e016894bd0e", "missing-codex-author", t316_ruling, t316_note, ""),
        ("a5b7045b129d062c4731acc7667262795abd3f67", "missing-codex-author", t470_merge2_ruling, t470_merge2_note, ""),
        (
            "333605d680ec15f3f74b00e9e2746ae317b85dc5",
            "missing-codex-author",
            "2026-08-07 [T-619] docs/archive/worklog-phase3-0807-299.md entry 299 (/rulings 第5回、D230 統一述語 5点採用)",
            "",
            "",
        ),
        (
            "311d463f89d1d1708a309b86d5bf63f5b034f89d",
            "missing-codex-author",
            "2026-08-21 dev-wave-t1371-official-run-root "
            "受入lease待機長期化に伴う2回目のlocal main取り込み裁定 "
            "(ユーザー選択: known-violation 登録)",
            "受入投入前に親が作成した local main 取り込み merge "
            "`311d463f89d1d1708a309b86d5bf63f5b034f89d`。実装面で両側が触ったのは "
            "`orchestrator/campaign/layout.py` / "
            "`orchestrator/campaign/s8b_oracle_driver.py` / "
            "`orchestrator/tests/conftest.py` / "
            "`orchestrator/tests/test_campaign.py` / "
            "`orchestrator/tests/test_check_ai_provenance.py` / "
            "`orchestrator/tests/test_s8b_oracle_driver.py` / "
            "`tools/check_ai_provenance.py` の 7 file で、7 path を個別に `git diff-tree --cc "
            "311d463f89d1d1708a309b86d5bf63f5b034f89d -- <path>` で確認した。"
            "`layout.py` / `conftest.py` / `test_campaign.py` / `test_s8b_oracle_driver.py` は commit SHA 行のみで"
            "実質空、`s8b_oracle_driver.py` は wave 側が Codex `role=author` の commit `756228db` で既に書いた "
            "`_OFFICIAL_OUTPUT_ROOT_ENV` import と main 側が独立追加した `site_policy` / `MACHINE_ENV_TAG` "
            "import の除去の和集合で、`MACHINE_ENV_TAG` の孤立参照もない。2 checker file は本 wave の "
            "`_T1371_MERGE_RULING` / `_T1371_MERGE_NOTE` と main 側の複数 wave "
            "(`_T565_MERGE_RULING` / `_T972_MERGE_RULING` / `_T567_MERGE*_RULING` 等) の "
            "known-violation エントリを両方残す union で解決した。競合解決による新規著作はなく、結果は両側の"
            "変更の単純な和集合。main 側の T-1444 site-aware 化は別 wave が Codex `role=author` で書き、"
            "各 wave の land 時に監査済み。親作成 merge のため Codex 著者とは記さない。",
            "",
        ),
        ("5823caf328a5985476cd2f6f7aa0d13daa5b08f6", "missing-codex-author", t567_merge2_ruling, t567_merge2_note, ""),
        (
            "09ce607b779272fda5629a350676471a16bea9bb",
            "missing-ai-agent",
            "2026-08-21 Claude セッション内でのユーザー直接commit (ユーザー承認: known-violation 登録の続行)",
            "ユーザーが直接作成した superproject commit による `external/ccbench` の gitlink "
            "（submodule ポインタ）前進；変更は 511c9538 → ef9328a3 の線形1コミット分の"
            "ポインタ更新のみ（分岐・衝突なし）で、ef9328a3 はリポジトリ owner 本人が 100% "
            "書いた C++ の MOCC correctness trace v2 hook（`#if TRACE ... #endif` で完全に囲まれ"
            "既定 inert）；AI関与なしのため `missing-ai-agent` は正当な既知違反",
            "",
        ),
        (
            "13101ab3ec09a54e1f30462d1c2b4621b121ba65",
            "missing-ai-agent",
            "2026-08-21 Claude セッション内でのユーザー裁定 (T-755への影響確認済み、09ce607bのrevert)",
            "この revert commit 自体は親の Claude セッションが `git revert --no-edit` を直接実行して機械的に生成したもの；"
            "`external/ccbench` の gitlink（submodule ポインタ）を `ef9328a3` → `511c9538` に"
            "戻した1行差分のみで、S8b floor campaign の SHA 不一致を是正し、git revert は既存 commit の"
            "逆操作のみのため独自のソース著作なし；`--no-edit` により trailer は一切付与されず"
            "AI-Agent trailer が存在しないため `missing-ai-agent` として登録；T-755 の wave は"
            "outer gitlink を参照しないため影響なし",
            "",
        ),
        (
            "8440a14850718e63d73dfc510aa66b853a526424",
            "missing-codex-author",
            t1479_merge_ruling,
            t1479_merge_note,
            "",
        ),
        (
            "d87fd42c0335c1396c1f79557e45357e9bfc163f",
            "missing-ai-agent",
            "2026-08-21 [T-755] wave内でのlocal main取り込みmerge (ユーザー承認: known-violation登録の続行)",
            "親 (Claude session) が `git merge --no-edit main` で作成した local main 取り込み。"
            "`git diff-tree --cc d87fd42c` は commit header のみで実質空 = 競合解決による新規著作なし。"
            "取り込んだのは external/ccbench の gitlink pointer 変更 (511c9538→ef9328a3、"
            "ユーザー直接commit 09ce607b) 1 file のみ。--no-edit の自動生成 message には trailer が"
            "付与されない",
            "",
        ),
        (
            "75d57796ea8c6af4f80f32031afc952cfef2903a",
            "missing-ai-agent",
            "2026-08-21 [T-755] wave内でのlocal main取り込みmerge (ユーザー承認: known-violation登録の続行)",
            "親 (Claude session) が `git merge --no-edit main` で作成した local main 取り込み。"
            "`git diff-tree --cc 75d57796` は commit header のみで実質空 = 競合解決による新規著作なし。"
            "取り込んだのは external/ccbench の gitlink revert (13101ab3) と、別セッション"
            "(t-1458) が既に Codex role=author で書き main land 時に監査済みの provenance"
            "registry 追加 (89ab8093, fdbb549b) + docs/spool 記録 fragment",
            "",
        ),
        (
            "216493593dbee40fbdac65207ca328bae5bc9f52",
            "missing-ai-agent",
            "2026-08-21 [T-755] wave内でのlocal main取り込みmerge (ユーザー承認: known-violation登録の続行)",
            "親 (Claude session) が `git merge --no-edit main` で作成した local main 取り込み。"
            "`git diff-tree --cc 21649359` は commit header のみで実質空 = 競合解決による新規著作なし。"
            "main 側 (t-1458 の land 由来) で `tools/check_ai_provenance.py`/`orchestrator/tests/"
            "test_check_ai_provenance.py` へ独立に追加された known-violation entry と、本 wave が"
            "同じ file へ追加した known-violation entry が非競合で union された",
            "",
        ),
        (
            "e39a8d46567a02d231fce52abae5aee759634ff7",
            "missing-codex-author",
            t1479_merge2_ruling,
            t1479_merge2_note,
            "",
        ),
        (
            "3eaf2038ec2ac3e7965c2a1eedcadb1ed1266626",
            "missing-codex-author",
            "2026-08-21 dev-wave-t1476-verify-state-committed 受入前裁定 "
            "(ユーザー選択: known-violation 登録)",
            "受入全走4回目が owned-path-overlap で終端し親が作成した3回目の local main 取り込み"
            "merge。tools/check_ai_provenance.py と orchestrator/tests/test_check_ai_provenance.py の"
            "KNOWN_PROVENANCE_VIOLATIONS/expected tuple 末尾に、本wave (6f2d97c8の1エントリ) とmain側"
            "(T-755、d87fd42c/75d57796/216493593の3エントリ) がそれぞれ独立に別内容のエントリを追加した"
            "union型の競合。git diff-tree --cc 3eaf2038は両側の追加分がそれぞれ現れる単純なunionで、"
            "既存2ブロックの連結のみ (一字一句の変更・削除なし)、新規著作なし。authority docs"
            "(docs/dev-wave/{core,operations}.md) とtools/pegasus/admission_registry.jsonがmerge中で"
            "working tree driftしCodex dispatchが構造的に使えなかったため親が直接union解消した。"
            "親作成mergeのためCodex著者とは記さない。",
            "",
        ),
        (
            "387a1daab0d713cf86f19449e88559686f1eb575",
            "missing-codex-author",
            t1479_merge3_ruling,
            t1479_merge3_note,
            "",
        ),
        (
            "649fe5a060a39de295f90d2002e8f97082729ea6",
            "malformed-ai-agent",
            t1477_ruling,
            t1477_note,
            t1477_malformed_value,
        ),
        (
            "649fe5a060a39de295f90d2002e8f97082729ea6",
            "missing-codex-author",
            t1477_ruling,
            t1477_note,
            "",
        ),
        (
            "e86d363a876ab00e7e6b37dfdd94385e5ab03816",
            "missing-codex-author",
            "本セッション内でユーザーへ状況を説明し known-violation 登録の続行を承認された (2026-08-21、3回目)",
            "merge commit `e86d363a876ab00e7e6b37dfdd94385e5ab03816` は、本waveとmain側の別waveが独立にcommit "
            "`09ce607b779272fda5629a350676471a16bea9bb` (ユーザーのccbench pin更新commit) を "
            "known-violation登録したことによる重複エントリの競合を、親のClaudeセッションが直接解決したものである。"
            "実装面で競合したのは `tools/check_ai_provenance.py` と "
            "`orchestrator/tests/test_check_ai_provenance.py` の2 fileで、解決は両親のいずれかに既存するテキストの"
            "選択・配置のみ (新規著作なし) であることを、親セッションが両親の内容と結合結果を行単位で"
            "機械比較して確認済み (結合結果の全行がどちらかの親に存在)。`git diff-tree --cc` combined diff実測 "
            "(2026-08-22、T-1479のロジック改修後に親が再検証) でも `tools/check_ai_provenance.py` のpatch本体が"
            "非空であることを確認しており、新ロジックの下でも引き続き実装面著作として検出される。",
            "",
        ),
        (
            "0c0f3e71b3208370be8d4e7e20a84a2152afe4b2",
            "missing-codex-author",
            "本セッション内でユーザーへ状況を説明し known-violation 登録の続行を承認された (2026-08-21、4回目)",
            "merge commit `0c0f3e71b3208370be8d4e7e20a84a2152afe4b2` は、main側off-arm neutralization (C02) 対応と"
            "複数waveのccbench provenance known-violation登録を取り込んだもの。"
            "`tools/check_ai_provenance.py`/`orchestrator/tests/test_check_ai_provenance.py`の競合は親が両親のいずれかに"
            "既存するテキストの選択・配置のみで解決 (新規著作なし)。"
            "`orchestrator/campaign/autonomous_trial_completeness.py`他4fileは競合マーカーなしで自動マージされ、"
            "結合結果の全行がどちらかの親に存在することを機械比較で確認済み (新規著作0行)。"
            "ただし自動マージの結果、`registered`→`arm_execution_permitted`改名箇所とmain側off-arm処理が追加した"
            "同名の古い変数参照が意味的に衝突しNameErrorになったため、直後のcommit `b7c9c5af` (Codex role=author) で"
            "1行修正し焦点走1378 passedを確認した。`git diff-tree --cc` combined diff実測 (2026-08-22、T-1479のロジック"
            "改修後に親が再検証) でも `tools/check_ai_provenance.py`/`test_check_ai_provenance.py` 双方のpatch本体が"
            "非空であることを確認しており、新ロジックの下でも引き続き実装面著作として検出される。",
            "",
        ),
        (
            "bf92f327cadfbe626e37cab73d55abe80d3994dd",
            "missing-codex-author",
            "本セッション内でユーザーへ状況を説明し known-violation 登録の続行を承認された (2026-08-22、6回目)",
            "受入投入前に local main 側36コミット（dev-wave-t1476-verify-state-committed の s8b oracle "
            "report/holdout freeze 関連実装、T-1434 の cache probe insight、T-646 の master seed toctou 修正、"
            "docs系spool/fold多数）を取り込んだ6回目の merge "
            "`bf92f327cadfbe626e37cab73d55abe80d3994dd`。"
            "`tools/check_ai_provenance.py` / `orchestrator/tests/test_check_ai_provenance.py` の "
            "KNOWN_PROVENANCE_VIOLATIONS / expected tuple 末尾への、本 wave の4エントリ "
            "(664dfc62 / e86d363a / 0c0f3e71 / dd58c9ca) と main 側の別 wave "
            "(dev-wave-t1476-verify-state-committed、6f2d97c8 / 3eaf2038) の独立追加が3箇所で競合し、"
            "親の Claude セッションが直接両側の既存エントリを残す union で解決した。"
            "`git diff-tree --cc bf92f327cadfbe626e37cab73d55abe80d3994dd` 相当の確認では、"
            "3箇所の結合結果は両親に既存する known-violation エントリの単純な unionであり、"
            "競合解決による新規著作なしと確認済み。"
            "本 wave 担当5 file（`orchestrator/campaign/autonomous_trial_completeness.py` 等）は main 側が変更せず、"
            "`git status` にも現れなかった。main 側由来で自動マージされた "
            "`orchestrator/campaign/s8b_holdout_freeze.py` / `orchestrator/campaign/s8b_oracle_report.py` 他も"
            "構文確認済みで、焦点走は対象3 fileで762 passed、s8b/pegasus関連5 fileで527 passed・2 skippedを確認した。"
            "merge commit は `AI-Agent: product=claude; model=claude-sonnet-5; reasoning=not-exposed; role=integrator` "
            "だけで Codex `role=author` 行がないため checker が missing-codex-author を検出した。"
            "親作成 merge のため Codex 著者とは記さない。`git diff-tree --cc` combined diff実測 "
            "(2026-08-22、T-1479のロジック改修後に親が再検証) でも両fileのpatch本体が非空であることを確認しており、"
            "新ロジックの下でも引き続き実装面著作として検出される。",
            "",
        ),
        (
            "b9c07cc22d483a9103dac208a83446872161ffad",
            "missing-codex-author",
            "本セッション内でユーザーへ状況を説明し known-violation 登録の続行を承認された (2026-08-22、7回目)",
            "受入投入前に local main 側11コミット（T-1479による `KNOWN_PROVENANCE_VIOLATIONS` 判定ロジック改修）を"
            "取り込んだ7回目の merge commit `b9c07cc22d483a9103dac208a83446872161ffad`。T-1479は `_commit_paths()` の"
            "merge分岐を pairwise diff の積集合のみで判定する方式から、`git diff-tree --cc` のcombined diff patch本体が"
            "空かどうかを `_combined_diff_paths()` で判定する方式へ置き換え、実装面 finding が消えると確認できた19件を"
            "台帳から削除した。これに伴い本 wave の5エントリ (664dfc62 / e86d363a / 0c0f3e71 / dd58c9ca / bf92f327) を"
            "新ロジックで個別に再検証し、`git diff-tree --cc <sha> -- <path>` の対象pathへのpatch本体が実質空 (bytes=0)"
            "だった `664dfc62` / `dd58c9ca` は削除し、`e86d363a` / `0c0f3e71` / `bf92f327` はそれぞれ4515 bytes、"
            "2906+4030 bytes、9196+7766 bytesでpatch本体が非空だったため保持した。"
            "`tools/check_ai_provenance.py` / `orchestrator/tests/test_check_ai_provenance.py` の競合解決は親の Claude セッションが"
            "main側 (T-1479整理後) の内容を丸ごとベースに採用し、自waveのエントリを個別に再配置した。merge commit は "
            "`AI-Agent: product=claude; model=claude-sonnet-5; reasoning=not-exposed; role=integrator` だけで Codex "
            "`role=author` 行がないため checker が `missing-codex-author` (paths=orchestrator/tests/test_check_ai_provenance.py, "
            "tools/check_ai_provenance.py) を検出した。親作成 merge のため Codex 著者とは記さない。",
            "",
        ),
        (
            "25614f868c1a1b562a68072233fdf55b0be93cd1",
            "missing-codex-author",
            "本セッション内でユーザーへ状況を説明し known-violation 登録の承認を得た (2026-08-23)",
            "D662 (受入 lease claim 待ちの廃止) 対応で `tools/dev_wave_wait.py` へ実装した "
            "`--lease-optional` (commit 0c89ec77、Codex role=author) を今後の全 wave が自動的に"
            "使うよう、`docs/dev-wave/operations.md` の DW-O27 追加・`.claude/commands/dev-wave.md` "
            "条件18への追記・`tools/check_docs.py` の dispatch 契約 (REQUIRED_REFERENCE_SECTIONS / "
            "CONDITION_DISPATCH_CONTRACT[\"18\"]) 登録を commit 25614f86 で行った。3箇所とも既存の"
            "文字列集合へのリテラル追加のみでロジック変更はないが、manager (claude) が直接 commit した"
            "ため `tools/check_docs.py` への変更に Codex `role=author` trailer がなく、checker が "
            "`missing-codex-author` (paths=tools/check_docs.py) を検出した。",
            "",
        ),
        (
            "94815c57976806da56a3f067ade91c0041b2e2d1",
            "missing-codex-author",
            "本セッション内でユーザーへ状況を説明し known-violation 登録の承認を得た (2026-08-23)",
            "commit `94815c57976806da56a3f067ade91c0041b2e2d1` は `tools/check_ai_provenance.py` へ "
            "`_T1458_DOCS_REGISTRY_RULING`/`_T1458_DOCS_REGISTRY_NOTE` 定数と、commit "
            "`25614f868c1a1b562a68072233fdf55b0be93cd1` に対応する `KnownViolationSpec` エントリ1件を追加した。"
            "manager (claude) が直接 commit したため Codex `role=author` trailer がなく、"
            "`missing-codex-author` として検出された。",
            "",
        ),
        (
            "3a5e5feb5f5c65e5e91752f847c623ce37e9b14d",
            "missing-codex-author",
            "本セッション内でユーザーへ状況を説明し known-violation 登録の承認を得た (2026-08-23)",
            "commit `3a5e5feb5f5c65e5e91752f847c623ce37e9b14d` は "
            "`orchestrator/tests/test_check_ai_provenance.py` の "
            "`test_known_violation_ledger_matches_literal_entries` の `expected` タプルへ、commit "
            "`94815c57976806da56a3f067ade91c0041b2e2d1` の known-violation エントリ（commit SHA、"
            "`missing-codex-author`、ruling、note、空文字列）の逐語ミラーを追加した。"
            "manager (claude) が直接 commit したため Codex `role=author` trailer がなく、"
            "`missing-codex-author` として検出された。",
            "",
        ),
    )
    assert len(provenance.KNOWN_PROVENANCE_VIOLATIONS) == len(expected)
    assert observed == expected
    assert len({(row[0], row[1]) for row in expected}) == len(expected)
    assert provenance._LEDGER_FINDING_KINDS == frozenset({
        "missing-ai-agent", "missing-codex-author", "malformed-ai-agent",
    })
    assert provenance._NOTE_REQUIRED_FINDING_KINDS == frozenset({
        "malformed-ai-agent",
    })


def test_known_violation_ledger_matches_real_commit_findings():
    commits = [
        "88f0f9f081f7c76c8ab5fc4a94e2640f70af129b",
        "85dacc27054db0bd3db55d73cab4f8ca3b4843e5",
        "6e69ca5c2bc2df403e1cda595aeffcba3a97c248",
        "16affe169185040b33f8c6cbdd452260bddc4089",
        "905c867a7b2342ff250a1bcf28a3ce74abdacc06",
        "b0a07672737cf03424ec1790cc25a06e4c85b737",
        "3f2c43d7580b8c26724d90278589862057508965",
        "f277efd4461d361d5c9aa6db9a7e00b194b76083",
        "74b501962092373ba2e8bbca1566d0732e0f16c6",
        "7ec088163dee920f0b8e1e9783faa6e36b22b730",
        "1d09940463ccacb0dbb0ab3e69ca0698a960fdf1",
        "f1406c22abece76276b43dde897750a46aae877e",
        "a567eb68d85d2ea4db6002c12a0ee59d2a5cd69f",
        "ff264975a04aa19f36f861ca97efe9dc59c88659",
        "2c1929533a6f641b513f4f7990fe06e6cdb383b1",
        "9af3e7a0f1c82fb91f310b5c9d197ec4a45f1320",
        "6fa5bde0d4e685141e3aa7f6de0ebdcda6b148ec",
        "2b3d06cbe81b1ae2675c153bdf307d508fc35a20",
        "30719e517dcee45c014cbf1052c6dc70a8fcf693",
        "1fa2b75b09b0b0e2e0e27a6f2cbedb058e8eb9f7",
        "622bd786191d40bda388596fa2adbf119ee84c9a",
        "c75fde903384b6eb9e4d45239b66008b7639cbf7",
        "c55ace29e55bba948d7bdca89f6fc1fb1a5191da",
        "edf74c94427686f2b91519ef10e94446d0fe89d5",
        "7e3cc116f2466fb439ec2bddd38f35dab928c942",
        "66769067ee57d78650b208b9a86438ff2f1bf73b",
        "1f884f6f6042cd8b1ce3f16f0bc7db3d97b768aa",
        "aaffa644a969f0a58969b2661318bda4c42ac767",
        "6f5411ceb7cc5d872e3112fb6d04013367ac092e",
        "797db5def66ef1d318d06c7aa189ea51a66c9312",
        "8ceebcdbe40fac27cb2a1fbd7a1b1e016894bd0e",
    ]
    audit = provenance._audit_history(commits)
    assert audit.findings == []
    assert audit.corrected == []
    assert audit.waived == []
    assert [(spec.commit, spec.expected_finding_kind) for spec in audit.known_violations] == [
        ("88f0f9f081f7c76c8ab5fc4a94e2640f70af129b", "missing-ai-agent"),
        ("85dacc27054db0bd3db55d73cab4f8ca3b4843e5", "missing-ai-agent"),
        ("6e69ca5c2bc2df403e1cda595aeffcba3a97c248", "missing-ai-agent"),
        ("16affe169185040b33f8c6cbdd452260bddc4089", "missing-ai-agent"),
        ("905c867a7b2342ff250a1bcf28a3ce74abdacc06", "missing-ai-agent"),
        ("b0a07672737cf03424ec1790cc25a06e4c85b737", "missing-codex-author"),
        ("3f2c43d7580b8c26724d90278589862057508965", "missing-ai-agent"),
        ("f277efd4461d361d5c9aa6db9a7e00b194b76083", "malformed-ai-agent"),
        ("74b501962092373ba2e8bbca1566d0732e0f16c6", "malformed-ai-agent"),
        ("7ec088163dee920f0b8e1e9783faa6e36b22b730", "malformed-ai-agent"),
        ("1d09940463ccacb0dbb0ab3e69ca0698a960fdf1", "malformed-ai-agent"),
        ("f1406c22abece76276b43dde897750a46aae877e", "malformed-ai-agent"),
        ("a567eb68d85d2ea4db6002c12a0ee59d2a5cd69f", "malformed-ai-agent"),
        ("ff264975a04aa19f36f861ca97efe9dc59c88659", "malformed-ai-agent"),
        ("2c1929533a6f641b513f4f7990fe06e6cdb383b1", "missing-codex-author"),
        ("9af3e7a0f1c82fb91f310b5c9d197ec4a45f1320", "malformed-ai-agent"),
        ("6fa5bde0d4e685141e3aa7f6de0ebdcda6b148ec", "malformed-ai-agent"),
        ("2b3d06cbe81b1ae2675c153bdf307d508fc35a20", "malformed-ai-agent"),
        ("30719e517dcee45c014cbf1052c6dc70a8fcf693", "malformed-ai-agent"),
        ("1fa2b75b09b0b0e2e0e27a6f2cbedb058e8eb9f7", "malformed-ai-agent"),
        ("622bd786191d40bda388596fa2adbf119ee84c9a", "malformed-ai-agent"),
        ("c75fde903384b6eb9e4d45239b66008b7639cbf7", "malformed-ai-agent"),
        ("c55ace29e55bba948d7bdca89f6fc1fb1a5191da", "malformed-ai-agent"),
        ("edf74c94427686f2b91519ef10e94446d0fe89d5", "malformed-ai-agent"),
        ("7e3cc116f2466fb439ec2bddd38f35dab928c942", "malformed-ai-agent"),
        ("66769067ee57d78650b208b9a86438ff2f1bf73b", "malformed-ai-agent"),
        ("1f884f6f6042cd8b1ce3f16f0bc7db3d97b768aa", "malformed-ai-agent"),
        ("aaffa644a969f0a58969b2661318bda4c42ac767", "malformed-ai-agent"),
        ("6f5411ceb7cc5d872e3112fb6d04013367ac092e", "malformed-ai-agent"),
        ("797db5def66ef1d318d06c7aa189ea51a66c9312", "malformed-ai-agent"),
        ("8ceebcdbe40fac27cb2a1fbd7a1b1e016894bd0e", "missing-codex-author"),
    ]


def test_t619_known_violation_is_absorbed_in_authoritative_audit(
    monkeypatch: pytest.MonkeyPatch,
):
    target = "333605d680ec15f3f74b00e9e2746ae317b85dc5"
    head = _git(REPO, "rev-parse", "HEAD")
    assert provenance._is_descendant(target, head)
    seen_authoritative: list[object] = []
    real_ledger = provenance._known_violation_audit

    def capture_ledger(*args, **kwargs):
        seen_authoritative.append(kwargs.get("authoritative"))
        return real_ledger(*args, **kwargs)

    monkeypatch.setattr(provenance, "_known_violation_audit", capture_ledger)
    audit = provenance._audit_history(
        [target], authoritative=True, head=head,
    )
    assert audit.findings == []
    assert seen_authoritative == [True]
    assert [(spec.commit, spec.expected_finding_kind) for spec in audit.known_violations] == [
        (target, provenance.MISSING_CODEX_AUTHOR),
    ]


def test_t619_authoritative_ledger_visibility_wiring_is_explicit(
    monkeypatch: pytest.MonkeyPatch,
):
    target = "333605d680ec15f3f74b00e9e2746ae317b85dc5"
    head = _git(REPO, "rev-parse", "HEAD")
    monkeypatch.setattr(
        provenance,
        "validate_implementation_author",
        lambda *args, **kwargs: ([], False),
    )
    with pytest.raises(
        RuntimeError,
        match=(
            "known-violation-stale: .*"
            "reason=expected-finding-missing checker-regression-suspected"
        ),
    ) as excinfo:
        provenance._audit_history(
            [target], authoritative=True, head=head,
        )
    assert "policy-epoch-not-visible" not in str(excinfo.value)


def test_known_violation_requires_exact_full_sha_positive_and_negative_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    _init_repo(tmp_path)
    base = _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# policy\n"},
        CODEX_AUTHOR,
    )
    known = _commit(tmp_path, {"docs/known.md": "known\n"}, "known\n")
    other = _commit(tmp_path, {"docs/other.md": "other\n"}, "other\n")
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        provenance, "KNOWN_PROVENANCE_VIOLATIONS", (_known_spec(known),),
    )

    audit = provenance._audit_history([known, other])
    assert [spec.commit for spec in audit.known_violations] == [known]
    assert audit.findings == [f"{other[:12]} other: AI-Agent trailer がない"]
    assert base != known != other


def test_known_violation_exact_sha_with_shared_eight_digit_prefix():
    shared_prefix = "1234abcd"
    known = shared_prefix + "a" * 32
    other = shared_prefix + "b" * 32
    shared_subject = "same subject"
    shared_path = "docs/same-path.md"

    def audit(commit: str) -> provenance.CommitAudit:
        label = f"{commit[:12]} {shared_subject}"
        return provenance.CommitAudit(
            commit=commit,
            label=label,
            normal_findings=(
                provenance.NormalFinding(
                    f"{label}: AI-Agent trailer がない ({shared_path})",
                    provenance.MISSING_AI_AGENT,
                ),
            ),
            correction=provenance.CorrectionAudit((), (), (), (), ()),
        )

    spec = _known_spec(known)
    result = provenance._known_violation_audit(
        [audit(known), audit(other)],
        registry={known: spec},
        suppressed_missing=None,
        stale_eligible_commits={known},
    )
    assert result == provenance.KnownViolationAudit(
        findings=(
            f"{other[:12]} {shared_subject}: "
            f"AI-Agent trailer がない ({shared_path})",
        ),
        known_violations=(spec,),
        stale=(),
    )


def test_broken_short_sha_registry_is_rc2_but_message_file_is_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    commit = _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# policy\n"},
        CODEX_AUTHOR,
    )
    message = tmp_path / "message.txt"
    message.write_text("change\n\nAI-Agent: none\n", encoding="utf-8")
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        provenance,
        "KNOWN_PROVENANCE_VIOLATIONS",
        (_known_spec(commit[:12]),),
    )

    assert provenance.main(
        ["--range", f"{commit}^!"], site=site_policy.OTHER,
    ) == 2
    captured = capsys.readouterr()
    assert "invalid full SHA" in captured.err
    assert "known-violation" not in captured.out

    assert provenance.main(
        ["--message-file", str(message)], site=site_policy.OTHER,
    ) == 0
    captured = capsys.readouterr()
    assert captured.out == "check_ai_provenance: 1 件、違反なし\n"
    assert captured.err == ""


@pytest.mark.parametrize(
    ("case", "error"),
    [
        ("container", "invalid container"),
        ("commit", "invalid SHA type"),
        ("kind", "invalid finding kind type"),
    ],
)
def test_broken_registry_types_are_rc2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    case: str,
    error: str,
):
    _init_repo(tmp_path)
    commit = _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# policy\n"},
        CODEX_AUTHOR,
    )
    if case == "container":
        registry: object = object()
    elif case == "commit":
        registry = (
            provenance.KnownViolationSpec(
                7, provenance.MISSING_AI_AGENT, "ruling",
            ),
        )
    else:
        registry = (
            provenance.KnownViolationSpec(commit, [], "ruling"),
        )
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(provenance, "KNOWN_PROVENANCE_VIOLATIONS", registry)

    assert provenance.main(
        ["--range", f"{commit}^!"], site=site_policy.OTHER,
    ) == 2
    captured = capsys.readouterr()
    assert error in captured.err
    assert captured.out == ""


@pytest.mark.parametrize(
    ("bad_note", "error"),
    [
        (None, "invalid note type: NoneType"),
        ("first\nsecond", "line break in note"),
        ("first\rsecond", "line break in note"),
        ("first\r\nsecond", "line break in note"),
        ("first\u2028second", "line break in note"),
    ],
    ids=["non-str", "lf", "cr", "crlf", "ls"],
)
def test_broken_registry_note_is_rc2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    bad_note: object,
    error: str,
):
    _init_repo(tmp_path)
    _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# policy\n"},
        CODEX_AUTHOR,
    )
    commit = _commit(
        tmp_path,
        {"docs/known.md": "known\n"},
        "known\n",
    )
    matching_spec = provenance.KnownViolationSpec(
        commit=commit,
        expected_finding_kind="missing-ai-agent",
        ruling="matching synthetic ruling",
        note=bad_note,
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        provenance, "KNOWN_PROVENANCE_VIOLATIONS", (matching_spec,),
    )

    assert provenance.main(
        ["--range", f"{commit}^!"], site=site_policy.OTHER,
    ) == 2
    captured = capsys.readouterr()
    expected_diagnostic = (
        "check_ai_provenance: 実行不能: "
        "known provenance violation registry has "
        + (
            error
            if bad_note is None
            else f"{error}: {commit}"
        )
        + "\n"
    )
    assert captured.err == expected_diagnostic
    assert captured.out == ""


@pytest.mark.parametrize("note", ["", " \t"], ids=["empty", "blank"])
def test_malformed_kind_requires_nonblank_note_rc2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    note: str,
):
    _init_repo(tmp_path)
    commit = _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# policy\n"},
        "malformed\n\nAI-Agent: bad value\n",
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        provenance,
        "KNOWN_PROVENANCE_VIOLATIONS",
        (
            _known_spec(
                commit,
                provenance.MALFORMED_AI_AGENT,
                note=note,
                expected_finding_value="bad value",
            ),
        ),
    )

    assert provenance.main(
        ["--range", f"{commit}^!"], site=site_policy.OTHER,
    ) == 2
    captured = capsys.readouterr()
    assert f"empty required note: {commit}" in captured.err
    assert captured.out == ""
    missing = _commit(tmp_path, {"docs/missing.md": "missing\n"}, "missing\n")
    malformed_spec = _known_spec(
        commit,
        provenance.MALFORMED_AI_AGENT,
        note="single-line explanation",
        expected_finding_value="bad value",
    )
    missing_spec = _known_spec(missing)
    monkeypatch.setattr(
        provenance,
        "KNOWN_PROVENANCE_VIOLATIONS",
        (malformed_spec, missing_spec),
    )

    audit = provenance._audit_history([commit, missing])
    assert audit.findings == []
    assert audit.known_violations == (malformed_spec, missing_spec)


@pytest.mark.parametrize(
    ("selector", "expected_diagnostic", "character"),
    [
        ("note", "prohibited character in note", "\x00"),
        ("note", "prohibited character in note", "\x1f"),
        ("note", "prohibited character in note", "\u200b"),
        ("note", "prohibited character in note", "\u200c"),
        ("note", "prohibited character in note", "\u200d"),
        ("note", "prohibited character in note", "\ufeff"),
        ("note", "prohibited character in note", "\u00ad"),
        ("note", "prohibited character in note", "\u2060"),
        ("note", "prohibited character in note", "\t"),
        ("note", "line break in note", "\n"),
        ("note", "prohibited character in note", "\x7f"),
        ("note", "line break in note", "\u2028"),
        ("note", "line break in note", "\u2029"),
        ("value", "prohibited character in finding value", "\x00"),
        ("value", "prohibited character in finding value", "\x1f"),
        ("value", "prohibited character in finding value", "\u200b"),
        ("value", "prohibited character in finding value", "\u200c"),
        ("value", "prohibited character in finding value", "\u200d"),
        ("value", "prohibited character in finding value", "\ufeff"),
        ("value", "prohibited character in finding value", "\u00ad"),
        ("value", "prohibited character in finding value", "\u2060"),
        ("value", "prohibited character in finding value", "\t"),
        ("value", "prohibited character in finding value", "\n"),
        ("value", "prohibited character in finding value", "\x7f"),
        ("value", "prohibited character in finding value", "\u2028"),
        ("value", "prohibited character in finding value", "\u2029"),
    ],
    ids=[
        "note-\\x00", "note-\\x1f", "note-\\u200b", "note-\\u200c",
        "note-\\u200d", "note-\\ufeff", "note-\\u00ad", "note-\\u2060",
        "note-\\t", "note-\\n", "note-\\x7f", "note-\\u2028",
        "note-\\u2029", "value-\\x00", "value-\\x1f", "value-\\u200b",
        "value-\\u200c", "value-\\u200d", "value-\\ufeff", "value-\\u00ad",
        "value-\\u2060", "value-\\t", "value-\\n", "value-\\x7f",
        "value-\\u2028", "value-\\u2029",
    ],
)
def test_registry_rejects_control_and_zero_width_characters(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    selector: str,
    expected_diagnostic: str,
    character: str,
):
    _init_repo(tmp_path)
    commit = _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# policy\n"},
        "malformed\n\nAI-Agent: bad value\n",
    )
    note = (
        f"explanation{character}" if selector == "note" else "explanation"
    )
    value = f"bad{character}value" if selector == "value" else "bad value"
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        provenance,
        "KNOWN_PROVENANCE_VIOLATIONS",
        (
            _known_spec(
                commit,
                provenance.MALFORMED_AI_AGENT,
                note=note,
                expected_finding_value=value,
            ),
        ),
    )

    assert provenance.main(
        ["--range", f"{commit}^!"], site=site_policy.OTHER,
    ) == 2
    captured = capsys.readouterr()
    assert expected_diagnostic in captured.err
    assert captured.out == ""


@pytest.mark.parametrize(
    "note",
    ["\u034f", "\ufe0f", "\u3164"],
    ids=["combining-grapheme-joiner", "variation-selector-16", "hangul-filler"],
)
def test_registry_rejects_non_descriptive_required_note_rc2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    note: str,
):
    _init_repo(tmp_path)
    commit = _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# policy\n"},
        "malformed\n\nAI-Agent: bad value\n",
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        provenance,
        "KNOWN_PROVENANCE_VIOLATIONS",
        (
            _known_spec(
                commit,
                provenance.MALFORMED_AI_AGENT,
                note=note,
                expected_finding_value="bad value",
            ),
        ),
    )

    assert provenance.main(
        ["--range", f"{commit}^!"], site=site_policy.OTHER,
    ) == 2
    captured = capsys.readouterr()
    assert captured.err == (
        "check_ai_provenance: 実行不能: known provenance violation registry "
        f"has non-descriptive required note: {commit}\n"
    )
    assert captured.out == ""


def test_production_registry_notes_satisfy_descriptive_contract():
    registry = provenance._known_violation_registry()
    flattened = tuple(
        spec
        for specs in registry.values()
        for spec in specs
    )

    assert len(flattened) == len(provenance.KNOWN_PROVENANCE_VIOLATIONS)
    assert flattened == provenance.KNOWN_PROVENANCE_VIOLATIONS


def test_registry_accepts_visible_character_mixed_with_non_descriptive_characters(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    commit = _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# policy\n"},
        "malformed\n\nAI-Agent: bad value\n",
    )
    non_descriptive = "\u034f\u115f\u1160\u17b4\u17b5\u2065\u3164\ufe0f\uffa0"
    spec = _known_spec(
        commit,
        provenance.MALFORMED_AI_AGENT,
        note=f"A{non_descriptive}",
        expected_finding_value="bad value",
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        provenance, "KNOWN_PROVENANCE_VIOLATIONS", (spec,),
    )

    assert provenance.main(
        ["--range", f"{commit}^!"], site=site_policy.OTHER,
    ) == 0
    captured = capsys.readouterr()
    assert captured.out.endswith("check_ai_provenance: 1 件、新規違反なし\n")
    assert captured.err == ""


@pytest.mark.parametrize(
    ("spec", "error"),
    [
        (
            provenance.KnownViolationSpec(
                "1" * 40,
                "malformed-ai-agent",
                "ruling",
                note="explanation",
                expected_finding_value=None,
            ),
            "invalid finding value type: NoneType",
        ),
        (
            provenance.KnownViolationSpec(
                "1" * 40,
                "malformed-ai-agent",
                "ruling",
                note="explanation",
            ),
            "empty required finding value",
        ),
        (
            provenance.KnownViolationSpec(
                "1" * 40,
                "missing-ai-agent",
                "ruling",
                expected_finding_value="unexpected",
            ),
            "unexpected finding value",
        ),
    ],
    ids=["non-string", "malformed-empty", "non-malformed-nonempty"],
)
def test_expected_finding_value_registry_contract_is_rc2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    spec: provenance.KnownViolationSpec,
    error: str,
):
    _init_repo(tmp_path)
    commit = _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# policy\n"},
        CODEX_AUTHOR,
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        provenance,
        "KNOWN_PROVENANCE_VIOLATIONS",
        (
            provenance.KnownViolationSpec(
                commit=commit,
                expected_finding_kind=spec.expected_finding_kind,
                ruling=spec.ruling,
                note=spec.note,
                expected_finding_value=spec.expected_finding_value,
            ),
        ),
    )

    assert provenance.main(
        ["--range", f"{commit}^!"], site=site_policy.OTHER,
    ) == 2
    captured = capsys.readouterr()
    assert error in captured.err
    assert captured.out == ""
    if error == "unexpected finding value":
        label = f"{commit[:12]} subject"
        actual_value = "actual malformed value"
        finding = provenance.NormalFinding(
            f"{label}: AI-Agent の形式違反: {actual_value!r} — detail",
            provenance.MALFORMED_AI_AGENT,
        )
        audit = provenance.CommitAudit(
            commit,
            label,
            (finding,),
            provenance.CorrectionAudit((), (), (), (), ()),
        )
        matching_kind_wrong_value = _known_spec(
            commit,
            provenance.MALFORMED_AI_AGENT,
            note="explanation",
            expected_finding_value="different malformed value",
        )
        result = provenance._known_violation_audit(
            [audit],
            registry={commit: matching_kind_wrong_value},
            suppressed_missing=None,
            stale_eligible_commits={commit},
        )
        assert result.findings == (finding.text,)
        assert result.known_violations == ()
        assert result.stale == (matching_kind_wrong_value,)


@pytest.mark.parametrize(
    ("message", "expected_kind"),
    [
        ("AI-Agent: malformed\n", "malformed-ai-agent"),
        (
            "AI-Agent: product=codex; model=gpt-5; reasoning=high; role=author\n"
            "AI-Agent: product=codex; model=gpt-5; reasoning=high; role=author\n",
            None,
        ),
        ("AI-Agent: none\nAI-Agent: malformed\n", None),
        (
            "AI-Agent: product=none; model=gpt-5; reasoning=high; role=author\n",
            None,
        ),
        (
            "AI-Agent: product=codex; model=none; reasoning=high; role=author\n",
            None,
        ),
    ],
    ids=["malformed", "duplicate", "none-mixed", "reserved", "model-none"],
)
def test_base_finding_kind_is_anchored_after_full_label(
    message: str, expected_kind: str | None,
):
    label = "123456789abc subject: AI-Agent の形式違反: injected"
    base, _, _ = provenance.validate_message("label-probe", f"body\n\n{message}")
    assert base
    rewritten = [finding.replace("label-probe", label, 1) for finding in base]
    assert [
        provenance._base_finding_ledger_kind(label, finding)
        for finding in rewritten
    ] == [expected_kind] * len(rewritten)


def test_registered_malformed_finding_uses_normal_commit_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    _init_repo(tmp_path)
    malformed_value = "bad value"
    commit = _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# policy\n"},
        f"malformed\n\nAI-Agent: {malformed_value}\n",
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    normal = provenance._normal_commit_audit(
        commit,
        scope_epoch=None,
        implementation_epoch=None,
    )
    assert normal.normal_findings == (
        provenance.NormalFinding(
            f"{normal.label}: AI-Agent の形式違反: {malformed_value!r} — "
            "product/model/reasoning/role (任意で scope) の順と許可値を確認する",
            provenance.MALFORMED_AI_AGENT,
        ),
    )
    spec = _known_spec(
        commit,
        provenance.MALFORMED_AI_AGENT,
        note="explanation",
        expected_finding_value=malformed_value,
    )
    monkeypatch.setattr(
        provenance, "KNOWN_PROVENANCE_VIOLATIONS", (spec,),
    )
    audit = provenance._audit_history([commit])
    assert audit.findings == []
    assert audit.known_violations == (spec,)


def test_unregistered_malformed_finding_remains_rc1_with_production_registry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    commit = _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# policy\n"},
        "outside registry\n\nAI-Agent: malformed\n",
    )
    assert commit not in {spec.commit for spec in provenance.KNOWN_PROVENANCE_VIOLATIONS}
    monkeypatch.setattr(provenance, "REPO", tmp_path)

    assert provenance.main(
        ["--range", f"{commit}^!"], site=site_policy.OTHER,
    ) == 1
    captured = capsys.readouterr()
    assert f"{commit[:12]} outside registry: AI-Agent の形式違反" in captured.err
    assert "known-violation" not in captured.out


def test_malformed_known_violation_missing_finding_is_stale_rc2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    clean = _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# policy\n"},
        CODEX_AUTHOR,
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        provenance,
        "KNOWN_PROVENANCE_VIOLATIONS",
        (
            _known_spec(
                clean,
                provenance.MALFORMED_AI_AGENT,
                note="explanation",
                expected_finding_value="bad value",
            ),
        ),
    )

    assert provenance.main(
        ["--range", f"{clean}^!"], site=site_policy.OTHER,
    ) == 2
    captured = capsys.readouterr()
    assert (
        f"sha={clean} finding=malformed-ai-agent "
        "reason=expected-finding-missing checker-regression-suspected"
        in captured.err
    )
    assert captured.out == ""


def test_ai_agent_acceptance_language_is_unchanged():
    assert provenance.ROLES == (
        "author", "reviewer", "researcher", "manager", "integrator",
    )
    assert provenance.IDENT == r"[a-z0-9][a-z0-9._-]*"
    accepted = [
        f"product=claude; model=claude-opus-5-1m; reasoning=high; role={role}"
        for role in provenance.ROLES
    ]
    accepted.append(
        "product=codex.v2; model=gpt_5-6; reasoning=x.high; role=author"
    )
    rejected = [
        accepted[0] + "; extra=x",
        "model=claude-opus-5-1m; product=claude; reasoning=high; role=manager",
        "product=claude; modell=claude-opus-5-1m; reasoning=high; role=manager",
        "product=claude; model=claude-opus-5[1m]; reasoning=high; role=manager",
        "product=claude; model=claude-opus-5-1m; reasoning=high; role=orchestrator",
        "product=Claude; model=claude-opus-5-1m; reasoning=high; role=manager",
    ]
    assert all(provenance.AGENT_VALUE.fullmatch(value) for value in accepted)
    assert all(provenance.AGENT_VALUE.fullmatch(value) is None for value in rejected)
    for value in accepted:
        base, _, _ = provenance.validate_message(
            "accepted", f"change\n\nAI-Agent: {value}\n",
        )
        assert base == []
    for value in rejected:
        base, _, _ = provenance.validate_message(
            "rejected", f"change\n\nAI-Agent: {value}\n",
        )
        assert len(base) == 1
        assert "AI-Agent の形式違反" in base[0]


def test_known_violation_expected_kind_coexists_with_other_new_finding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    _init_repo(tmp_path)
    base = _commit(
        tmp_path,
        {
            provenance.POLICY_PATH: (
                "scope=\n"
                f"{provenance.IMPLEMENTATION_POLICY_NEEDLE}\n"
                f"{POLICY_NEEDLE_LITERAL}\n"
            ),
        },
        CODEX_AUTHOR,
    )
    mixed = _commit(
        tmp_path,
        {"tools/mixed.py": "MIXED = True\n"},
        "mixed\n\nCo-Authored-By: body\n\n"
        "AI-Agent: product=claude; model=fable-5; reasoning=xhigh; "
        "role=author\n",
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        provenance,
        "KNOWN_PROVENANCE_VIOLATIONS",
        (_known_spec(mixed, "missing-codex-author"),),
    )

    audit = provenance._audit_history([mixed])
    assert [spec.commit for spec in audit.known_violations] == [mixed]
    assert audit.findings == [
        f"{mixed[:12]} mixed: Co-Authored-By trailer 配置違反: raw=1, parsed=0"
    ]
    assert base != mixed


def test_known_violation_suppresses_only_one_expected_finding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    _init_repo(tmp_path)
    base = _commit(
        tmp_path,
        {
            provenance.POLICY_PATH: (
                f"{provenance.IMPLEMENTATION_POLICY_NEEDLE}\n"
            ),
        },
        CODEX_AUTHOR,
    )
    commit = _commit(
        tmp_path,
        {"tools/duplicate.py": "DUPLICATE = True\n"},
        CLAUDE_AUTHOR,
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        provenance,
        "KNOWN_PROVENANCE_VIOLATIONS",
        (_known_spec(commit, "missing-codex-author"),),
    )
    monkeypatch.setattr(
        provenance,
        "validate_implementation_author",
        lambda *args, **kwargs: (["duplicate-kind", "duplicate-kind"], False),
    )

    audit = provenance._audit_history([commit])
    assert [spec.commit for spec in audit.known_violations] == [commit]
    assert audit.findings == ["duplicate-kind"]
    assert base != commit


def test_known_violation_selected_clean_entry_is_stale_rc2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    clean = _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# clean\n"},
        CODEX_AUTHOR,
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        provenance, "KNOWN_PROVENANCE_VIOLATIONS", (_known_spec(clean),),
    )

    assert provenance.main(
        ["--range", f"{clean}^!"], site=site_policy.OTHER,
    ) == 2
    captured = capsys.readouterr()
    assert f"known-violation-stale: sha={clean} finding=missing-ai-agent" in captured.err
    assert captured.out == ""


def test_known_violation_missing_expected_finding_diagnoses_regression(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    clean = _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# clean\n"},
        CODEX_AUTHOR,
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        provenance, "KNOWN_PROVENANCE_VIOLATIONS", (_known_spec(clean),),
    )

    assert provenance.main(
        ["--range", f"{clean}^!"], site=site_policy.OTHER,
    ) == 2
    captured = capsys.readouterr()
    assert (
        f"known-violation-stale: sha={clean} finding=missing-ai-agent "
        "reason=expected-finding-missing checker-regression-suspected"
        in captured.err
    )
    assert "policy-epoch-not-visible" not in captured.err
    assert captured.out == ""


def test_known_violation_other_kind_does_not_hide_selected_stale(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    base = _commit(
        tmp_path,
        {
            provenance.POLICY_PATH: f"{POLICY_NEEDLE_LITERAL}\n",
        },
        CODEX_AUTHOR,
    )
    selected = _commit(
        tmp_path,
        {"docs/selected.md": "selected\n"},
        "selected\n\nCo-Authored-By: body\n\nAI-Agent: none\n",
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        provenance, "KNOWN_PROVENANCE_VIOLATIONS", (_known_spec(selected),),
    )

    assert provenance.main(
        ["--range", f"{selected}^!"], site=site_policy.OTHER,
    ) == 2
    captured = capsys.readouterr()
    assert f"known-violation-stale: sha={selected} finding=missing-ai-agent" in captured.err
    assert "Co-Authored-By trailer 配置違反" not in captured.err
    assert captured.out == ""
    assert base != selected


def test_known_violation_outside_range_is_not_stale_end_to_end(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    outside = _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# policy\n"},
        CODEX_AUTHOR,
    )
    selected = _commit(tmp_path, {"docs/selected.md": "ok\n"}, CODEX_AUTHOR)
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        provenance, "KNOWN_PROVENANCE_VIOLATIONS", (_known_spec(outside),),
    )

    assert provenance.main(
        ["--range", f"{selected}^!"], site=site_policy.OTHER,
    ) == 0
    captured = capsys.readouterr()
    assert captured.out == "check_ai_provenance: 1 件、違反なし\n"
    assert captured.err == ""


def test_known_violation_off_head_policy_guard_is_stale_rc2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    epoch = _commit(
        tmp_path,
        {
            provenance.POLICY_PATH: (
                f"{provenance.IMPLEMENTATION_POLICY_NEEDLE}\n"
            ),
        },
        CODEX_AUTHOR,
    )
    target = _commit(
        tmp_path,
        {"tools/target.py": "TARGET = True\n"},
        CLAUDE_AUTHOR,
    )
    _git(tmp_path, "switch", "-q", "--orphan", "unrelated-head")
    unrelated = _commit(
        tmp_path,
        {"docs/unrelated.md": "unrelated\n"},
        CODEX_AUTHOR,
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        provenance,
        "KNOWN_PROVENANCE_VIOLATIONS",
        (_known_spec(target, provenance.MISSING_CODEX_AUTHOR),),
    )

    assert provenance._implementation_policy_commit() is None
    assert provenance._is_descendant(epoch, target)
    assert not provenance._is_descendant(epoch, unrelated)
    assert provenance.main(
        ["--range", f"{target}^!"], site=site_policy.OTHER,
    ) == 2
    captured = capsys.readouterr()
    assert (
        f"known-violation-stale: sha={target} "
        "finding=missing-codex-author "
        "reason=policy-epoch-not-visible non-authoritative-invocation"
        in captured.err
    )
    assert "expected-finding-missing" not in captured.err
    assert captured.out == ""


def test_known_violation_stdout_is_public_on_rc0_and_rc1(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    base = _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# policy\n"},
        CODEX_AUTHOR,
    )
    known = _commit(tmp_path, {"docs/known.md": "known\n"}, "known\n")
    new = _commit(tmp_path, {"docs/new.md": "new\n"}, "new\n")
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        provenance, "KNOWN_PROVENANCE_VIOLATIONS", (_known_spec(known),),
    )

    assert provenance.main(
        ["--range", f"{known}^!"], site=site_policy.OTHER,
    ) == 0
    captured = capsys.readouterr()
    assert captured.out == (
        "check_ai_provenance: known-violation "
        f"sha={known} finding=missing-ai-agent\n"
        "check_ai_provenance: known-violations=1\n"
        "check_ai_provenance: 1 件、新規違反なし\n"
    )
    assert captured.err == ""

    assert provenance.main(
        ["--range", f"{base}..{new}"], site=site_policy.OTHER,
    ) == 1
    captured = capsys.readouterr()
    assert captured.out == (
        "check_ai_provenance: known-violation "
        f"sha={known} finding=missing-ai-agent\n"
        "check_ai_provenance: known-violations=1\n"
    )
    assert f"{new[:12]} new: AI-Agent trailer がない" in captured.err
    assert "2 件中 1 新規違反" in captured.err


def test_known_violation_nonempty_note_is_public_on_rc1(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    base = _commit(
        tmp_path,
        {provenance.POLICY_PATH: "# policy\n"},
        CODEX_AUTHOR,
    )
    known = _commit(tmp_path, {"docs/known.md": "known\n"}, "known\n")
    new = _commit(tmp_path, {"docs/new.md": "new\n"}, "new\n")
    note = "synthetic single-line note"
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        provenance,
        "KNOWN_PROVENANCE_VIOLATIONS",
        (
            provenance.KnownViolationSpec(
                commit=known,
                expected_finding_kind="missing-ai-agent",
                ruling="matching synthetic ruling",
                note=note,
            ),
        ),
    )

    assert provenance.main(
        ["--range", f"{base}..{new}"], site=site_policy.OTHER,
    ) == 1
    captured = capsys.readouterr()
    assert captured.out == (
        "check_ai_provenance: known-violation "
        f"sha={known} finding=missing-ai-agent note={note}\n"
        "check_ai_provenance: known-violations=1\n"
    )
    assert f"{new[:12]} new: AI-Agent trailer がない" in captured.err
    assert "2 件中 1 新規違反" in captured.err


def test_empty_registry_restores_all_thirty_real_findings(
    monkeypatch: pytest.MonkeyPatch,
):
    commits = [
        "88f0f9f081f7c76c8ab5fc4a94e2640f70af129b",
        "85dacc27054db0bd3db55d73cab4f8ca3b4843e5",
        "6e69ca5c2bc2df403e1cda595aeffcba3a97c248",
        "16affe169185040b33f8c6cbdd452260bddc4089",
        "905c867a7b2342ff250a1bcf28a3ce74abdacc06",
        "b0a07672737cf03424ec1790cc25a06e4c85b737",
        "3f2c43d7580b8c26724d90278589862057508965",
        "f277efd4461d361d5c9aa6db9a7e00b194b76083",
        "74b501962092373ba2e8bbca1566d0732e0f16c6",
        "7ec088163dee920f0b8e1e9783faa6e36b22b730",
        "1d09940463ccacb0dbb0ab3e69ca0698a960fdf1",
        "f1406c22abece76276b43dde897750a46aae877e",
        "a567eb68d85d2ea4db6002c12a0ee59d2a5cd69f",
        "ff264975a04aa19f36f861ca97efe9dc59c88659",
        "2c1929533a6f641b513f4f7990fe06e6cdb383b1",
        "9af3e7a0f1c82fb91f310b5c9d197ec4a45f1320",
        "6fa5bde0d4e685141e3aa7f6de0ebdcda6b148ec",
        "2b3d06cbe81b1ae2675c153bdf307d508fc35a20",
        "30719e517dcee45c014cbf1052c6dc70a8fcf693",
        "1fa2b75b09b0b0e2e0e27a6f2cbedb058e8eb9f7",
        "622bd786191d40bda388596fa2adbf119ee84c9a",
        "c75fde903384b6eb9e4d45239b66008b7639cbf7",
        "c55ace29e55bba948d7bdca89f6fc1fb1a5191da",
        "edf74c94427686f2b91519ef10e94446d0fe89d5",
        "7e3cc116f2466fb439ec2bddd38f35dab928c942",
        "66769067ee57d78650b208b9a86438ff2f1bf73b",
        "1f884f6f6042cd8b1ce3f16f0bc7db3d97b768aa",
        "aaffa644a969f0a58969b2661318bda4c42ac767",
        "6f5411ceb7cc5d872e3112fb6d04013367ac092e",
        "797db5def66ef1d318d06c7aa189ea51a66c9312",
    ]
    production = provenance._audit_history(commits)
    assert production.findings == []
    assert len(production.known_violations) == 30

    monkeypatch.setattr(provenance, "KNOWN_PROVENANCE_VIOLATIONS", ())
    audit = provenance._audit_history(commits)
    malformed_value = (
        "product=claude; model=claude-opus-5[1m]; reasoning=high; "
        "role=orchestrator"
    )
    malformed_suffix = (
        f": AI-Agent の形式違反: {malformed_value!r} — "
        "product/model/reasoning/role (任意で scope) の順と許可値を確認する"
    )
    assert audit.findings == [
        "88f0f9f081f7 Merge branch 'main' into worktree-rulings-20260806-a: AI-Agent trailer がない",
        "85dacc27054d Merge branch 'main' into worktree-rulings-20260806-a: AI-Agent trailer がない",
        "6e69ca5c2bc2 Merge branch 'main' into worktree-rulings-20260806-a: AI-Agent trailer がない",
        "16affe169185 Merge branch 'main' into worktree-rulings-20260806-a: AI-Agent trailer がない",
        "905c867a7b23 Merge branch 'main' into worktree-rulings-20260806-a: AI-Agent trailer がない",
        (
            "b0a07672737c docs(token-hygiene): 逐語・変異台帳・spool fragment を置く: "
            "実装面に Codex role=author がない — paths="
            "output/insights/2026-08-06_token-hygiene/analyze_codex.py, "
            "output/insights/2026-08-06_token-hygiene/analyze_v2.py"
        ),
        (
            "3f2c43d7580b docs(t503): 変異本走の停止原因の誤診断を訂正し、F148/F149 の再発として記録する: "
            "AI-Agent trailer がない"
        ),
        "f277efd4461d feat(t139): R4 環境 probe の実装 (段 5、レビュー前の中間 commit)" + malformed_suffix,
        "74b501962092 Merge local main 4816049f into worktree-dev-wave-t139-r4-probe" + malformed_suffix,
        "7ec088163dee fix(t139): R4 probe の段 6 所見を閉じ、判定写像を凍結する" + malformed_suffix,
        "1d09940463cc Merge local main ee2da0bf into worktree-dev-wave-t139-r4-probe (2 回目)" + malformed_suffix,
        "f1406c22abec fix(t139): 焦点再レビューの blocker を閉じ、到達不能な 1 件を限界として記録する" + malformed_suffix,
        "a567eb68d85d test(t139): R4 probe の変異 spec を事前登録する" + malformed_suffix,
        "ff264975a04a test(t139): 変異 spec の category を harness の固定語彙へ揃える" + malformed_suffix,
        (
            "2c1929533a6f docs(t659): activation 発行→配備の分裂窓の設計択一を裁定へ返す: "
            "実装面に Codex role=author がない — paths="
            "output/insights/2026-08-09_t659-activation-deploy-window/verbatim/probe_split_window.py"
        ),
        "9af3e7a0f1c8 test(t139): M3 の期待 node を parametrize 済みの実 node id へ直す" + malformed_suffix,
        "6fa5bde0d4e6 test(t139): R4 probe の変異 matrix 結果を台帳へ収める" + malformed_suffix,
        "2b3d06cbe81b docs(t139): R4 probe の submission receipt を qsub より前に作る" + malformed_suffix,
        "30719e517dce docs(t139): submission receipt の期待 commit を自己参照しない形へ直す" + malformed_suffix,
        "1fa2b75b09b0 fix(t139): compile_commands の command 文字列形式を受理する" + malformed_suffix,
        "622bd786191d docs(t139): R4 環境 probe の実測を反映して追補 A を再発行する" + malformed_suffix,
        "c75fde903384 Merge local main 9233308a into worktree-dev-wave-t139-r4-probe (3 回目)" + malformed_suffix,
        "c55ace29e55b docs(t139): R4 環境 probe の worklog fragment を spool へ書く" + malformed_suffix,
        "edf74c944276 Merge local main eede11af into worktree-dev-wave-t139-r4-probe (4 回目)" + malformed_suffix,
        "7e3cc116f246 Merge local main 1f625c32 into worktree-dev-wave-t139-r4-probe (5 回目)" + malformed_suffix,
        "66769067ee57 Merge local main 5e75328d into worktree-dev-wave-t139-r4-probe (6 回目)" + malformed_suffix,
        "1f884f6f6042 docs(t139): worklog fragment の base を裁定記録後の現本文へ合わせる" + malformed_suffix,
        "aaffa644a969 Merge local main 34957a24 into worktree-dev-wave-t139-r4-probe (7 回目)" + malformed_suffix,
        "6f5411ceb7cc docs(t139): 受入結果と段 8 の改善候補を worklog fragment へ反映する" + malformed_suffix,
        "797db5def66e docs(t139): land 対象 tip の受入再走 (7570 passed / 20 skipped) を記録する" + malformed_suffix,
    ]
    assert len(audit.findings) == 30
    assert sum("AI-Agent trailer がない" in finding for finding in audit.findings) == 6
    assert sum("実装面に Codex role=author がない" in finding for finding in audit.findings) == 2
    assert sum("AI-Agent の形式違反" in finding for finding in audit.findings) == 22
    assert audit.known_violations == ()


def test_ledgered_3f2c43d7580b_is_known_and_rc0(
    capsys: pytest.CaptureFixture[str],
):
    commit = "3f2c43d7580b8c26724d90278589862057508965"
    assert provenance.main(
        ["--range", f"{commit}^!"], site=site_policy.OTHER,
    ) == 0
    captured = capsys.readouterr()
    assert captured.out == (
        "check_ai_provenance: known-violation "
        f"sha={commit} finding=missing-ai-agent "
        "note=trailer は本文に実在するが、AI-Agent 行と Co-Authored-By 行の間の"
        "空行で trailer block 不成立\n"
        "check_ai_provenance: known-violations=1\n"
        "check_ai_provenance: 1 件、新規違反なし\n"
    )
    assert captured.err == ""


def test_forward_correction_production_literal_and_target_object_are_pinned():
    spec = provenance.INCIDENT_6B64D21_FORWARD_CORRECTION
    assert spec == provenance.ForwardCorrectionSpec(
        target="6b64d21753d2cfc790f80caba29df7a40fef3072",
    )
    assert provenance.CORRECTION_KEY == "AI-Agent-Correction"
    assert spec.payload == (
        "target=6b64d21753d2cfc790f80caba29df7a40fef3072; "
        "product=claude; model=claude-opus-5; "
        "reasoning=xhigh; role=integrator"
    )
    target_and_parents = _git(
        REPO, "rev-list", "--parents", "-n", "1", spec.target,
    ).split()
    assert target_and_parents[0] == spec.target
    assert len(target_and_parents) == 3
    target_message = _git(REPO, "show", "-s", "--format=%B", spec.target)
    assert "AI-Agent:" not in target_message
    assert "AI-Agent-Correction:" not in target_message
    audit = provenance._normal_commit_audit(
        spec.target,
        scope_epoch=provenance._scope_policy_commit(),
        implementation_epoch=provenance._implementation_policy_commit(),
    )
    assert audit.normal_findings == (
        provenance.NormalFinding(
            f"{audit.label}: AI-Agent trailer がない",
            "missing-ai-agent",
        ),
    )
    assert audit.correction.candidate_count == 0


def test_forward_correction_exact_raw_and_canonical_value_is_accepted(
    monkeypatch: pytest.MonkeyPatch,
):
    payload = _install_synthetic_correction_spec(monkeypatch, "1" * 40)
    audit = provenance._correction_audit(
        "valid",
        _correction_message(payload),
    )
    assert audit.exact
    assert audit.candidate_count == 1
    assert audit.raw_values == (f" {payload}",)
    assert audit.parsed_values == (payload,)
    assert audit.final_values == (payload,)
    assert audit.final_ai_agent_values == (
        "product=codex; model=gpt-5.6-sol; reasoning=high; role=author",
    )
    assert audit.findings == ()


def test_forward_correction_canonical_parser_is_lazy_without_raw_candidate(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_if_called(message: str) -> dict[str, list[str]]:
        raise AssertionError(f"unexpected correction parser call: {message!r}")

    monkeypatch.setattr(provenance, "_parsed_trailers", fail_if_called)
    audit = provenance._correction_audit(
        "ordinary",
        "ordinary\n\nAI-Agent: none\n",
    )
    assert audit == provenance.CorrectionAudit((), (), (), (), ())
    assert not audit.exact


def test_forward_correction_continuation_fails_raw_exactness(
    monkeypatch: pytest.MonkeyPatch,
):
    target = "2" * 40
    payload = _install_synthetic_correction_spec(monkeypatch, target)
    message = (
        "forward correction\n\n"
        "AI-Agent: product=codex; model=gpt-5.6-sol; "
        "reasoning=high; role=author\n"
        f"AI-Agent-Correction: target={target}; product=claude;\n"
        " model=claude-opus-5; reasoning=xhigh; role=integrator\n"
    )
    audit = provenance._correction_audit("continuation", message)
    assert not audit.exact
    assert audit.parsed_values == (payload,)
    assert any("raw value" in finding for finding in audit.findings)
    assert not any("canonical value が incident" in finding for finding in audit.findings)


def test_forward_correction_body_candidate_plus_valid_trailer_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
):
    payload = _install_synthetic_correction_spec(monkeypatch, "3" * 40)
    message = (
        "body example\n"
        f"AI-Agent-Correction: {payload}\n\n"
        "AI-Agent: product=codex; model=gpt-5.6-sol; "
        "reasoning=high; role=author\n"
        f"AI-Agent-Correction: {payload}\n"
    )
    audit = provenance._correction_audit("body-plus-valid", message)
    assert not audit.exact
    assert audit.candidate_count == 2
    assert audit.parsed_values == (payload,)
    assert any("raw candidate cardinality 違反" in finding
               for finding in audit.findings)
    assert any("物理 exact 1 行" in finding for finding in audit.findings)


def test_forward_correction_body_only_candidate_fails_canonical_presence(
    monkeypatch: pytest.MonkeyPatch,
):
    payload = _install_synthetic_correction_spec(monkeypatch, "6" * 40)
    message = (
        "body example\n"
        f"AI-Agent-Correction: {payload}\n\n"
        "ordinary prose after the candidate\n"
    )
    audit = provenance._correction_audit("body-only", message)
    assert not audit.exact
    assert audit.raw_values == (f" {payload}",)
    assert audit.parsed_values == ()
    assert any("canonical multiplicity 違反" in finding
               for finding in audit.findings)


def test_forward_correction_rejects_ai_agent_across_divider(
    monkeypatch: pytest.MonkeyPatch,
):
    payload = _install_synthetic_correction_spec(monkeypatch, "8" * 40)
    message = (
        "forward correction\n\n"
        "AI-Agent: product=codex; model=gpt-5.6-sol; "
        "reasoning=high; role=author\n"
        "---\n"
        "body\n\n"
        f"AI-Agent-Correction: {payload}\n"
    )
    audit = provenance._correction_audit("split-block", message)
    assert not audit.exact
    assert audit.parsed_values == (payload,)
    assert audit.final_values == ()
    assert audit.final_ai_agent_values
    assert any("final trailer block multiplicity 違反" in finding
               for finding in audit.findings)


@pytest.mark.parametrize(
    "line",
    [
        "AI-Agent-Correction:{payload}",
        "AI-Agent-Correction: \t{payload}",
        "AI-Agent-Correction:  {payload}",
        "AI-Agent-Correction: {payload} ",
        " AI-Agent-Correction: {payload}",
    ],
    ids=[
        "no-space",
        "tab-after-colon",
        "double-space",
        "trailing-space",
        "indented-key",
    ],
)
def test_forward_correction_rejects_representative_raw_whitespace(
    monkeypatch: pytest.MonkeyPatch,
    line: str,
):
    payload = _install_synthetic_correction_spec(monkeypatch, "9" * 40)
    message = (
        "forward correction\n\n"
        "AI-Agent: product=codex; model=gpt-5.6-sol; "
        "reasoning=high; role=author\n"
        f"{line.format(payload=payload)}\n"
    )
    audit = provenance._correction_audit("raw-whitespace", message)
    assert not audit.exact
    assert audit.findings


def test_forward_correction_canonical_parser_failure_is_not_accepted(
    monkeypatch: pytest.MonkeyPatch,
):
    payload = _install_synthetic_correction_spec(monkeypatch, "7" * 40)

    def failing_parser(message: str) -> dict[str, list[str]]:
        raise RuntimeError(f"synthetic correction parser failure: {len(message)}")

    monkeypatch.setattr(provenance, "_parsed_trailers", failing_parser)
    with pytest.raises(RuntimeError, match="synthetic correction parser failure"):
        provenance._correction_audit(
            "parser-failure",
            _correction_message(payload),
        )


@pytest.mark.parametrize(
    "mutated_payload",
    [
        (
            "target={target}; product=claude; model=claude-opus-5; "
            "reasoning=xhigh; role=integrator; scope=main-sync"
        ),
        (
            "target={target}; product=codex; model=claude-opus-5; "
            "reasoning=xhigh; role=integrator"
        ),
        (
            "target={target}; product=claude; model=claude-opus-5-1m; "
            "reasoning=xhigh; role=integrator"
        ),
        (
            "target={target}; product=claude; model=claude-opus-5; "
            "reasoning=default; role=integrator"
        ),
        (
            "target={target}; product=claude; model=claude-opus-5; "
            "reasoning=xhigh; role=manager"
        ),
        (
            "product=claude; target={target}; model=claude-opus-5; "
            "reasoning=xhigh; role=integrator"
        ),
        (
            "target={target}; product=claude; model=claude-opus-5; "
            "reasoning=xhigh; role=integrator; extra=unknown"
        ),
        (
            "target=0000000000000000000000000000000000000000; "
            "product=claude; model=claude-opus-5; "
            "reasoning=xhigh; role=integrator"
        ),
    ],
    ids=[
        "scope-added",
        "product-drift",
        "model-drift",
        "reasoning-drift",
        "role-drift",
        "field-order",
        "unknown-field",
        "target-drift",
    ],
)
def test_forward_correction_each_payload_drift_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    mutated_payload: str,
):
    target = "4" * 40
    _install_synthetic_correction_spec(monkeypatch, target)
    value = mutated_payload.format(target=target)
    audit = provenance._correction_audit(
        "field-drift",
        _correction_message(value),
    )
    assert not audit.exact
    assert any("raw value" in finding for finding in audit.findings)
    assert any("canonical value" in finding for finding in audit.findings)


def test_forward_correction_parser_ignores_ambient_aliases(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    payload = _install_synthetic_correction_spec(monkeypatch, "5" * 40)
    global_config = tmp_path / "global.gitconfig"
    global_config.write_text(
        "[trailer \"correction\"]\n"
        "\tkey = AI-Agent-Correction:\n"
        "[trailer]\n"
        "\tseparators = %\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(global_config))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "trailer.other.key")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "AI-Agent-Correction:")
    audit = provenance._correction_audit(
        "ambient",
        _correction_message(payload),
    )
    assert audit.exact
    assert audit.findings == ()


def test_forward_correction_two_parent_target_singleton_ranges(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    history = _make_correction_history(tmp_path, monkeypatch)
    assert len(
        _git(
            tmp_path,
            "rev-list",
            "--parents",
            "-n",
            "1",
            history.target,
        ).split()
    ) == 3

    assert _run_range(monkeypatch, f"{history.target}^!") == 1
    captured = capsys.readouterr()
    assert f"{history.target[:12]} target merge: AI-Agent trailer がない" in captured.err
    assert "1 件中 1 違反" in captured.err

    assert _run_range(monkeypatch, f"{history.correction}^!") == 1
    captured = capsys.readouterr()
    assert "target が selected revision set にない" in captured.err
    assert "1 件中 1 違反" in captured.err

    assert _run_range(
        monkeypatch,
        f"{history.target}^1..{history.correction}",
    ) == 0
    captured = capsys.readouterr()
    assert (
        "forward-corrected=1 "
        f"target={history.target} correction={history.correction}"
    ) in captured.out
    assert "3 件、違反なし" in captured.out
    assert captured.err == ""


def test_forward_correction_acceptance_is_commit_order_invariant(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    history = _make_correction_history(tmp_path, monkeypatch)
    forward = provenance.ForwardCorrected(
        history.target,
        history.correction,
    )
    forward_order = provenance._audit_history(
        [history.target, history.correction]
    )
    reverse_order = provenance._audit_history(
        [history.correction, history.target]
    )
    assert forward_order.findings == reverse_order.findings == []
    assert forward_order.corrected == reverse_order.corrected == [forward]
    assert forward_order.waived == reverse_order.waived == []
    assert forward_order.known_violations == reverse_order.known_violations == ()


def test_known_violation_composes_with_forward_correction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    history = _make_correction_history(
        tmp_path,
        monkeypatch,
        intermediate=(
            {"docs/other.md": "other\n"},
            "other missing\n",
        ),
    )
    commits = _git(
        tmp_path,
        "rev-list",
        "--reverse",
        f"{history.target}^1..{history.correction}",
    ).splitlines()
    other = commits[-2]
    spec = _known_spec(history.target)
    monkeypatch.setattr(
        provenance, "KNOWN_PROVENANCE_VIOLATIONS", (spec,),
    )
    real_audit = provenance._known_violation_audit
    ledger_results: list[provenance.KnownViolationAudit] = []

    def capture_ledger(*args, **kwargs):
        result = real_audit(*args, **kwargs)
        ledger_results.append(result)
        return result

    monkeypatch.setattr(provenance, "_known_violation_audit", capture_ledger)

    with pytest.raises(
        RuntimeError,
        match=(
            "known-violation-stale: "
            f"sha={history.target} finding=missing-ai-agent"
        ),
    ):
        provenance._audit_history(commits)
    assert ledger_results == [
        provenance.KnownViolationAudit(
            findings=(
                f"{other[:12]} other missing: AI-Agent trailer がない",
            ),
            known_violations=(),
            stale=(spec,),
        ),
    ]


def test_forward_correction_multiple_tip_selected_set_is_accepted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    history = _make_correction_history(tmp_path, monkeypatch)
    _git(tmp_path, "branch", "extra-tip", history.first_parent)
    assert _run_range(monkeypatch, "--all") == 0
    captured = capsys.readouterr()
    assert (
        "forward-corrected=1 "
        f"target={history.target} correction={history.correction}"
    ) in captured.out
    assert captured.err == ""


def test_forward_correction_split_trailer_blocks_do_not_suppress_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    def split_builder(payload: str) -> str:
        return (
            "forward correction\n\n"
            "AI-Agent: product=codex; model=gpt-5.6-sol; "
            "reasoning=high; role=author\n"
            "---\n"
            "body\n\n"
            f"AI-Agent-Correction: {payload}\n"
        )

    history = _make_correction_history(
        tmp_path,
        monkeypatch,
        correction_builder=split_builder,
    )
    assert _run_range(
        monkeypatch,
        f"{history.target}^1..{history.correction}",
    ) == 1
    captured = capsys.readouterr()
    assert "final trailer block multiplicity 違反" in captured.err
    assert f"{history.target[:12]} target merge: AI-Agent trailer がない" in captured.err
    assert "forward-corrected=1" not in captured.out


def test_forward_correction_sibling_is_not_rehabilitated_by_later_merge(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    history = _make_correction_history(tmp_path, monkeypatch)
    _git(
        tmp_path,
        "switch",
        "-q",
        "-c",
        "sibling-correction",
        history.first_parent,
    )
    sibling = _commit(
        tmp_path,
        {"docs/sibling-correction.md": "sibling\n"},
        _correction_message(history.payload),
    )
    _git(
        tmp_path,
        "switch",
        "-q",
        "-c",
        "aggregate",
        history.target,
    )
    _git(tmp_path, "merge", "--no-ff", "--no-commit", "sibling-correction")
    aggregate = _commit(
        tmp_path,
        {"docs/aggregate.md": "aggregate\n"},
        CODEX_AUTHOR,
    )

    assert _run_range(
        monkeypatch,
        f"{history.base}..{aggregate}",
    ) == 1
    captured = capsys.readouterr()
    assert "strict descendant でない" in captured.err
    assert f"{history.target[:12]} target merge: AI-Agent trailer がない" in captured.err
    assert sibling[:12] in captured.err
    assert "forward-corrected=1" not in captured.out


def test_forward_correction_duplicate_in_selected_set_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    history = _make_correction_history(tmp_path, monkeypatch)
    duplicate = _commit(
        tmp_path,
        {"docs/duplicate-correction.md": "duplicate\n"},
        _correction_message(history.payload),
    )
    assert _run_range(
        monkeypatch,
        f"{history.target}^1..{duplicate}",
    ) == 1
    captured = capsys.readouterr()
    assert "selected revision set 内 exact 1 件" in captured.err
    assert "candidates=2" in captured.err
    assert f"{history.target[:12]} target merge: AI-Agent trailer がない" in captured.err
    assert "forward-corrected=1" not in captured.out


def test_forward_correction_preserves_merge_side_missing_finding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    history = _make_correction_history(
        tmp_path,
        monkeypatch,
        side_message="side missing\n",
    )
    assert _run_range(
        monkeypatch,
        f"{history.target}^1..{history.correction}",
    ) == 1
    captured = capsys.readouterr()
    assert f"{history.side[:12]} side missing: AI-Agent trailer がない" in captured.err
    assert f"{history.target[:12]} target merge: AI-Agent trailer がない" not in captured.err
    assert "3 件中 1 違反" in captured.err
    assert "forward-corrected=1" not in captured.out


def test_forward_correction_suppresses_only_target_missing_not_target_cab(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    history = _make_correction_history(
        tmp_path,
        monkeypatch,
        target_message=(
            "target split CAB\n\n"
            "Co-Authored-By: body-only\n\n"
            "body after the CAB candidate\n"
        ),
    )
    assert _run_range(
        monkeypatch,
        f"{history.target}^1..{history.correction}",
    ) == 1
    captured = capsys.readouterr()
    assert "Co-Authored-By trailer 配置違反: raw=1, parsed=0" in captured.err
    assert "target split CAB: AI-Agent trailer がない" not in captured.err
    assert "3 件中 1 違反" in captured.err
    assert "forward-corrected=1" not in captured.out


@pytest.mark.parametrize(
    ("files", "message", "needle", "finding_count"),
    [
        (
            {"docs/other.md": "missing\n"},
            "other missing\n",
            "other missing: AI-Agent trailer がない",
            1,
        ),
        (
            {"docs/other.md": "format\n"},
            "other format\n\nAI-Agent: malformed\n",
            "other format: AI-Agent の形式違反",
            1,
        ),
        (
            {"docs/other.md": "scope\n"},
            (
                "other scope\n\n"
                "AI-Agent: product=codex; model=gpt-5.6-sol; "
                "reasoning=high; role=author\n"
                "AI-Agent: product=claude; model=fable-5; "
                "reasoning=xhigh; role=author\n"
            ),
            "other scope: role=author が複数行あるのに scope がない",
            2,
        ),
        (
            {"docs/other.md": "cab\n"},
            (
                "other CAB\n\n"
                "Co-Authored-By: body-only\n\n"
                "AI-Agent: none\n"
            ),
            "other CAB: Co-Authored-By trailer 配置違反",
            1,
        ),
        (
            {"tools/other.py": "OTHER = True\n"},
            CLAUDE_AUTHOR,
            "実装面に Codex role=author がない — paths=tools/other.py",
            1,
        ),
    ],
    ids=["missing", "format", "scope", "cab", "codex-author"],
)
def test_forward_correction_preserves_other_commit_findings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    files: dict[str, str],
    message: str,
    needle: str,
    finding_count: int,
):
    history = _make_correction_history(
        tmp_path,
        monkeypatch,
        intermediate=(files, message),
    )
    assert _run_range(
        monkeypatch,
        f"{history.target}^1..{history.correction}",
    ) == 1
    captured = capsys.readouterr()
    assert needle in captured.err
    assert f"{history.target[:12]} target merge: AI-Agent trailer がない" not in captured.err
    assert f"4 件中 {finding_count} 違反" in captured.err
    assert "forward-corrected=1" not in captured.out


@pytest.mark.parametrize(
    ("builder", "files", "needle", "finding_count"),
    [
        (
            lambda payload: _correction_message(payload, ai_agent_lines=""),
            {"docs/correction.md": "missing\n"},
            "forward correction: AI-Agent trailer がない",
            3,
        ),
        (
            lambda payload: _correction_message(
                payload,
                ai_agent_lines="AI-Agent: malformed\n",
            ),
            {"docs/correction.md": "format\n"},
            "forward correction: AI-Agent の形式違反",
            2,
        ),
        (
            lambda payload: _correction_message(
                payload,
                ai_agent_lines=(
                    "AI-Agent: product=codex; model=gpt-5.6-sol; "
                    "reasoning=high; role=author\n"
                    "AI-Agent: product=claude; model=fable-5; "
                    "reasoning=xhigh; role=author\n"
                ),
            ),
            {"docs/correction.md": "scope\n"},
            "forward correction: role=author が複数行あるのに scope がない",
            3,
        ),
        (
            lambda payload: _correction_message(
                payload,
                body="Co-Authored-By: body-only\n\n",
            ),
            {"docs/correction.md": "cab\n"},
            "forward correction: Co-Authored-By trailer 配置違反",
            2,
        ),
        (
            lambda payload: _correction_message(
                payload,
                ai_agent_lines=(
                    "AI-Agent: product=claude; model=fable-5; "
                    "reasoning=xhigh; role=author\n"
                ),
            ),
            {"tools/correction.py": "CORRECTION = True\n"},
            "実装面に Codex role=author がない — paths=tools/correction.py",
            2,
        ),
    ],
    ids=["missing", "format", "scope", "cab", "codex-author"],
)
def test_forward_correction_commit_must_be_normally_green(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    builder: Callable[[str], str],
    files: dict[str, str],
    needle: str,
    finding_count: int,
):
    history = _make_correction_history(
        tmp_path,
        monkeypatch,
        correction_builder=builder,
        correction_files=files,
    )
    assert _run_range(
        monkeypatch,
        f"{history.target}^1..{history.correction}",
    ) == 1
    captured = capsys.readouterr()
    assert needle in captured.err
    assert f"{history.target[:12]} target merge: AI-Agent trailer がない" in captured.err
    assert f"3 件中 {finding_count} 違反" in captured.err
    assert "forward-corrected=1" not in captured.out


def test_forward_correction_rejects_target_without_actual_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    history = _make_correction_history(
        tmp_path,
        monkeypatch,
        target_message=CODEX_AUTHOR,
    )
    assert _run_range(
        monkeypatch,
        f"{history.target}^1..{history.correction}",
    ) == 1
    captured = capsys.readouterr()
    assert "target に AI-Agent trailer の実欠落がない" in captured.err
    assert "3 件中 1 違反" in captured.err
    assert "forward-corrected=1" not in captured.out


def test_forward_correction_message_file_success_is_preflight_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    history = _make_correction_history(tmp_path, monkeypatch)
    _git(
        tmp_path,
        "switch",
        "-q",
        "-c",
        "before-correction",
        history.target,
    )
    message = tmp_path / "correction-message.txt"
    message.write_text(
        _correction_message(history.payload),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_ai_provenance.py", "--message-file", str(message)],
    )
    assert provenance.main(site=site_policy.OTHER) == 0
    captured = capsys.readouterr()
    assert "AI-Agent-Correction は preflight限定" in captured.out
    assert "current HEAD の通常子を仮定" in captured.out
    assert "commit後 history監査が必須" in captured.out
    assert f"target={history.target}" in captured.out
    assert "1 件、違反なし" in captured.out
    assert captured.err == ""


def test_forward_correction_message_file_rejects_second_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    history = _make_correction_history(tmp_path, monkeypatch)
    message = tmp_path / "second-correction-message.txt"
    message.write_text(
        _correction_message(history.payload),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_ai_provenance.py", "--message-file", str(message)],
    )
    assert provenance.main(site=site_policy.OTHER) == 1
    captured = capsys.readouterr()
    assert (
        "prospective parent ancestry 全体に既存 "
        "AI-Agent-Correction candidate がある"
    ) in captured.err
    assert "candidates=1" in captured.err
    assert "preflight限定" not in captured.out


def test_forward_correction_message_file_finds_candidate_on_merge_side(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    history = _make_correction_history(tmp_path, monkeypatch)
    _git(
        tmp_path,
        "switch",
        "-q",
        "-c",
        "preflight-first-parent",
        history.target,
    )
    _git(
        tmp_path,
        "merge",
        "--no-ff",
        "--no-commit",
        history.correction,
    )
    message = tmp_path / "merge-side-second-correction.txt"
    message.write_text(
        _correction_message(history.payload),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_ai_provenance.py", "--message-file", str(message)],
    )
    assert provenance.main(site=site_policy.OTHER) == 1
    captured = capsys.readouterr()
    assert (
        "prospective parent ancestry 全体に既存 "
        "AI-Agent-Correction candidate がある"
    ) in captured.err
    assert "candidates=1" in captured.err
    assert "preflight限定" not in captured.out


def test_forward_correction_message_file_rejects_target_outside_parent_ancestry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    base = _commit(tmp_path, {"docs/base.md": "base\n"}, CODEX_AUTHOR)
    main_branch = _git(tmp_path, "branch", "--show-current")
    _git(tmp_path, "switch", "-q", "-c", "target-side", base)
    target = _commit(tmp_path, {"docs/target.md": "target\n"}, "target\n")
    payload = _install_synthetic_correction_spec(monkeypatch, target)
    _git(tmp_path, "switch", "-q", main_branch)
    _commit(tmp_path, {"docs/main.md": "main\n"}, CODEX_AUTHOR)
    monkeypatch.setattr(provenance, "REPO", tmp_path)

    message = tmp_path / "outside-ancestry-correction.txt"
    message.write_text(_correction_message(payload), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_ai_provenance.py", "--message-file", str(message)],
    )
    assert provenance.main(site=site_policy.OTHER) == 1
    captured = capsys.readouterr()
    assert "target が prospective parent ancestry にない" in captured.err
    assert "target commit object が存在しない" not in captured.err


def test_forward_correction_message_file_rejects_missing_target_object(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    _commit(tmp_path, {"docs/base.md": "base\n"}, CODEX_AUTHOR)
    payload = _install_synthetic_correction_spec(monkeypatch, "f" * 40)
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    assert not provenance._commit_exists("f" * 40)
    message = tmp_path / "missing-target-message.txt"
    message.write_text(_correction_message(payload), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_ai_provenance.py", "--message-file", str(message)],
    )
    assert provenance.main(site=site_policy.OTHER) == 1
    captured = capsys.readouterr()
    assert "target commit object が存在しない" in captured.err
    assert "preflight限定" not in captured.out


def test_forward_correction_git_object_backend_failure_is_rc2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    _commit(tmp_path, {"docs/base.md": "base\n"}, CODEX_AUTHOR)
    payload = _install_synthetic_correction_spec(monkeypatch, "e" * 40)
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    real_run = subprocess.run

    def failing_cat_file(command, **kwargs):
        if command[:2] == ["git", "cat-file"]:
            return subprocess.CompletedProcess(
                command,
                128,
                "",
                "synthetic object database failure",
            )
        return real_run(command, **kwargs)

    monkeypatch.setattr(provenance.subprocess, "run", failing_cat_file)
    message = tmp_path / "backend-failure-message.txt"
    message.write_text(_correction_message(payload), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_ai_provenance.py", "--message-file", str(message)],
    )
    assert provenance.main(site=site_policy.OTHER) == 2
    captured = capsys.readouterr()
    assert "cat-file --batch-check failed (rc=128)" in captured.err
    assert "target commit object が存在しない" not in captured.err


def test_regular_message_file_acceptance_does_not_require_correction_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    message = tmp_path / "ordinary-message.txt"
    message.write_text(
        "ordinary\n\nAI-Agent: none\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_ai_provenance.py", "--message-file", str(message)],
    )
    assert provenance.main(site=site_policy.OTHER) == 0
    captured = capsys.readouterr()
    assert captured.out == "check_ai_provenance: 1 件、違反なし\n"
    assert captured.err == ""


def test_forward_correction_unrelated_history_remains_native_valid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    commit = _commit(
        tmp_path,
        {"docs/unrelated.md": "unrelated\n"},
        CODEX_AUTHOR,
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    assert _run_range(monkeypatch, f"{commit}^!") == 0
    captured = capsys.readouterr()
    assert captured.out == "check_ai_provenance: 1 件、違反なし\n"
    assert captured.err == ""


def test_forward_correction_merge_base_rc128_fails_closed_with_rc2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    history = _make_correction_history(tmp_path, monkeypatch)
    monkeypatch.setattr(provenance, "_scope_policy_commit", lambda: None)
    monkeypatch.setattr(provenance, "_implementation_policy_commit", lambda: None)
    real_run = subprocess.run

    def rc128_for_ancestry(command, **kwargs):
        if command[:3] == ["git", "merge-base", "--is-ancestor"]:
            return subprocess.CompletedProcess(
                command,
                128,
                "",
                "synthetic merge-base graph failure",
            )
        return real_run(command, **kwargs)

    monkeypatch.setattr(provenance.subprocess, "run", rc128_for_ancestry)
    assert _run_range(
        monkeypatch,
        f"{history.target}^1..{history.correction}",
    ) == 2
    captured = capsys.readouterr()
    assert "merge-base --is-ancestor" in captured.err
    assert "rc=128" in captured.err
    assert "synthetic merge-base graph failure" in captured.err


def _waiver_history(root: Path) -> dict[str, str]:
    """免除の計上意味論を固定するための最小履歴 (epoch / 免除 / docs / 違反)。"""
    _init_repo(root)
    epoch = _commit(
        root,
        {
            provenance.POLICY_PATH: (
                "# policy\n"
                f"{provenance.IMPLEMENTATION_POLICY_NEEDLE}\n"
            ),
        },
        CODEX_AUTHOR,
    )
    waived_implementation = _commit(
        root, {"tools/waived.py": "WAIVED = True\n"}, CLAUDE_AUTHOR_WAIVED,
    )
    waived_docs = _commit(
        root, {"docs/waived.md": "docs only\n"}, CLAUDE_AUTHOR_WAIVED,
    )
    violating = _commit(
        root, {"tools/violating.py": "BAD = True\n"}, CLAUDE_AUTHOR,
    )
    return {
        "epoch": epoch,
        "waived_implementation": waived_implementation,
        "waived_docs": waived_docs,
        "violating": violating,
    }


def test_known_violation_composes_with_waiver(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    history = _waiver_history(tmp_path)
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    spec = _known_spec(
        history["waived_implementation"],
        provenance.MISSING_CODEX_AUTHOR,
    )
    monkeypatch.setattr(
        provenance, "KNOWN_PROVENANCE_VIOLATIONS", (spec,),
    )
    real_audit = provenance._known_violation_audit
    ledger_results: list[provenance.KnownViolationAudit] = []

    def capture_ledger(*args, **kwargs):
        result = real_audit(*args, **kwargs)
        ledger_results.append(result)
        return result

    monkeypatch.setattr(provenance, "_known_violation_audit", capture_ledger)

    with pytest.raises(
        RuntimeError,
        match=(
            "known-violation-stale: "
            f"sha={history['waived_implementation']} "
            "finding=missing-codex-author"
        ),
    ):
        provenance._audit_history([
            history["waived_implementation"],
            history["violating"],
        ])
    assert ledger_results == [
        provenance.KnownViolationAudit(
            findings=(
                f"{history['violating'][:12]} change: "
                "実装面に Codex role=author がない — "
                "paths=tools/violating.py",
            ),
            known_violations=(),
            stale=(spec,),
        ),
    ]


def _mixed_history(
    root: Path, monkeypatch: pytest.MonkeyPatch,
) -> tuple[list[str], str, str]:
    """root 複数・merge・correction・CAB 違反・実装面 path・scope 複数行の合成履歴。"""
    _init_repo(root)
    base = _commit(
        root,
        {
            provenance.POLICY_PATH: (
                "# policy\n"
                "scope=\n"
                f"{provenance.IMPLEMENTATION_POLICY_NEEDLE}\n"
                f"{POLICY_NEEDLE_LITERAL}\n"
            ),
        },
        CODEX_AUTHOR,
    )
    main_branch = _git(root, "branch", "--show-current")
    _commit(root, {"tools/waived.py": "WAIVED = True\n"}, CLAUDE_AUTHOR_WAIVED)
    _commit(root, {"tools/violating.py": "BAD = True\n"}, CLAUDE_AUTHOR)
    _commit(root, {"docs/scope.md": "scope\n"}, MULTI_ROLE_NO_SCOPE)
    _commit(root, {"docs/cab.md": "cab\n"}, SPLIT_CAB_NONE)
    _git(root, "switch", "-q", "-c", "side", base)
    _commit(root, {"docs/side.md": "side\n"}, CODEX_AUTHOR)
    _commit(root, {"tools/side.py": "SIDE = True\n"}, CODEX_AUTHOR)
    _git(root, "switch", "-q", main_branch)
    _git(root, "merge", "--no-ff", "--no-commit", "side")
    target = _commit(root, {}, "target merge\n")
    payload = _install_synthetic_correction_spec(monkeypatch, target)
    _git(root, "switch", "-q", "--orphan", "second-root")
    _commit(root, {"docs/second.md": "second root\n"}, CODEX_AUTHOR)
    _git(root, "switch", "-q", main_branch)
    _git(
        root, "merge", "--no-ff", "--no-commit",
        "--allow-unrelated-histories", "second-root",
    )
    _commit(root, {}, CODEX_AUTHOR)
    correction = _commit(
        root,
        {"docs/correction.md": "correction\n"},
        _correction_message(payload),
    )
    monkeypatch.setattr(provenance, "REPO", root)
    commits = _git(root, "rev-list", "--reverse", main_branch).splitlines()
    return commits, target, correction


# --- W: waiver 逐語と needle の positive control -----------------------------


def test_policy_anchor_literals_exist_only_in_entry_with_hard_coded_oracle():
    anchors = (
        "実装面を変更する AI 関与 commit は Codex author を必須",
        "Co-Authored-By 候補行はすべて最終 trailer block に置く",
        "AI-Agent-Waiver: reason=<ident>; ratified=<YYYY-MM-DD>",
    )
    entry = (REPO / "docs/ai-provenance.md").read_text(encoding="utf-8")
    references = (
        (REPO / "docs/provenance/correction.md").read_text(encoding="utf-8"),
        (REPO / "docs/provenance/audit.md").read_text(encoding="utf-8"),
    )
    for anchor in anchors:
        assert entry.count(anchor) == 1
        assert all(reference.count(anchor) == 0 for reference in references)
    assert provenance.IMPLEMENTATION_POLICY_NEEDLE == anchors[0]
    assert provenance.CO_AUTHORED_BY_POLICY_NEEDLE == anchors[1]
    assert provenance.WAIVER_POLICY_LITERAL == anchors[2]
    nonretroactive = (
        "既定監査は各規則の内容検出 commit 自身と、その祖先でない "
        "HEAD 到達 commit に適用する。導入祖先は legacy とし、履歴を書き換えない。"
    )
    assert entry.count(nonretroactive) == 1
    assert len(entry.encode("utf-8")) == 6102
    assert entry.count(provenance.IMPLEMENTATION_POLICY_NEEDLE) == 1
    assert entry.count(provenance.CO_AUTHORED_BY_POLICY_NEEDLE) == 1


def test_scope_epoch_anchor_occurs_exactly_once_in_entry():
    entry = (REPO / "docs/ai-provenance.md").read_text(encoding="utf-8")
    assert entry.count("scope=") == 1


def test_provenance_policy_path_is_shared_and_hard_coded():
    assert (
        provenance.POLICY_PATH
        == check_docs.PROVENANCE_ENTRY
        == "docs/ai-provenance.md"
    )


def test_implementation_policy_epoch_is_pinned_in_this_repo():
    """needle 行を壊すと実装面 gate 全体が無効化される最悪型への positive control。"""
    epoch = provenance._implementation_policy_commit()
    assert epoch == IMPLEMENTATION_POLICY_EPOCH
    assert provenance._is_descendant(epoch, "HEAD")


# --- W: waiver の単体境界 ---------------------------------------------------


def test_waiver_exact_line_exempts_implementation_author_gate():
    waiver = provenance._waiver_audit("candidate", CLAUDE_AUTHOR_WAIVED)
    assert waiver.exact
    assert (waiver.reason, waiver.ratified) == (WAIVER_REASON, WAIVER_RATIFIED)
    assert provenance.validate_implementation_author(
        "candidate", CLAUDE_AUTHOR_WAIVED, ["tools/checker.py"], waived=True,
    ) == ([], True)
    assert provenance.validate_implementation_author(
        "candidate", CLAUDE_AUTHOR_WAIVED, ["tools/checker.py"], waived=False,
    ) == (
        [
            "candidate: 実装面に Codex role=author がない — "
            "paths=tools/checker.py"
        ],
        False,
    )
    # 免除は「codex author が居ない」と判定した後にだけ効く。
    assert provenance.validate_implementation_author(
        "candidate", CODEX_AUTHOR + WAIVER_LINE, ["tools/checker.py"],
        waived=True,
    ) == ([], False)
    # 実装面 path が無ければ免除は発火しない。
    assert provenance.validate_implementation_author(
        "candidate", CLAUDE_AUTHOR_WAIVED, ["docs/worklog.md"], waived=True,
    ) == ([], False)


def test_waiver_requires_own_role_author_ai_agent_line():
    message = (
        "change\n\n"
        "AI-Agent: product=claude; model=fable-5; reasoning=xhigh; "
        "role=reviewer\n"
        + WAIVER_LINE
    )
    waiver = provenance._waiver_audit("reviewer-only", message)
    assert not waiver.exact
    assert any(
        "role=author の AI-Agent がない" in finding
        for finding in waiver.findings
    )


@pytest.mark.parametrize(
    ("case", "message", "needle"),
    [
        (
            "two-lines",
            CLAUDE_AUTHOR + WAIVER_LINE + WAIVER_LINE,
            "raw candidate cardinality 違反",
        ),
        (
            "continuation",
            CLAUDE_AUTHOR
            + "AI-Agent-Waiver: reason=codex-outage;\n"
            + " ratified=2026-07-31\n",
            "raw value が形式に一致しない",
        ),
        (
            "body-plus-valid",
            "body example\n"
            + WAIVER_LINE
            + "\n"
            + "AI-Agent: product=claude; model=fable-5; reasoning=xhigh; "
            "role=author\n"
            + WAIVER_LINE,
            "raw candidate cardinality 違反",
        ),
        (
            "uppercase-reason",
            CLAUDE_AUTHOR
            + "AI-Agent-Waiver: reason=Codex-Outage; ratified=2026-07-31\n",
            "canonical value が形式に一致しない",
        ),
        (
            "unpadded-date",
            CLAUDE_AUTHOR
            + "AI-Agent-Waiver: reason=codex-outage; ratified=2026-7-31\n",
            "canonical value が形式に一致しない",
        ),
        (
            "missing-ratified",
            CLAUDE_AUTHOR + "AI-Agent-Waiver: reason=codex-outage\n",
            "canonical value が形式に一致しない",
        ),
        (
            "missing-separator-space",
            CLAUDE_AUTHOR
            + "AI-Agent-Waiver: reason=codex-outage;ratified=2026-07-31\n",
            "canonical value が形式に一致しない",
        ),
        (
            "body-only",
            "body example\n" + WAIVER_LINE + "\nprose after the candidate\n",
            "canonical multiplicity 違反",
        ),
        (
            "across-divider",
            "change\n\n"
            "AI-Agent: product=claude; model=fable-5; reasoning=xhigh; "
            "role=author\n"
            "---\n"
            "body\n\n"
            + WAIVER_LINE,
            "final trailer block multiplicity 違反",
        ),
        (
            "split-blocks",
            CLAUDE_AUTHOR + "\n" + WAIVER_LINE,
            "role=author の AI-Agent がない",
        ),
    ],
    ids=[
        "two-lines", "continuation", "body-plus-valid", "uppercase-reason",
        "unpadded-date", "missing-ratified", "missing-separator-space",
        "body-only", "across-divider", "split-blocks",
    ],
)
def test_waiver_boundary_rejects_malformed_and_out_of_block(
    case: str, message: str, needle: str,
):
    waiver = provenance._waiver_audit(case, message)
    assert not waiver.exact
    assert any(needle in finding for finding in waiver.findings), waiver.findings
    # 免除は exact のときだけ発火する。
    assert provenance.validate_implementation_author(
        case, message, ["tools/checker.py"], waived=waiver.exact,
    )[1] is False


def test_waiver_parser_is_lazy_without_raw_candidate(
    monkeypatch: pytest.MonkeyPatch,
):
    def fail_if_called(message: str) -> dict[str, list[str]]:
        raise AssertionError(f"unexpected waiver parser call: {message!r}")

    monkeypatch.setattr(provenance, "_parsed_trailers", fail_if_called)
    monkeypatch.setattr(provenance, "_parsed_final_trailers", fail_if_called)
    waiver = provenance._waiver_audit("ordinary", CODEX_AUTHOR)
    assert waiver == provenance.EMPTY_WAIVER
    assert not waiver.exact


# --- W: 前方訂正の受理集合を広げない ----------------------------------------


def test_waiver_does_not_widen_forward_correction_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    """実装面 path + claude-only author + waiver の correction commit を弾く。"""
    history = _make_correction_history(
        tmp_path,
        monkeypatch,
        correction_builder=lambda payload: (
            "forward correction\n\n"
            "AI-Agent: product=claude; model=fable-5; reasoning=xhigh; "
            "role=author\n"
            f"AI-Agent-Correction: {payload}\n"
            + WAIVER_LINE
        ),
        correction_files={"tools/correction.py": "CORRECTION = True\n"},
    )
    assert _run_range(
        monkeypatch, f"{history.target}^1..{history.correction}",
    ) == 1
    captured = capsys.readouterr()
    assert (
        f"{history.target[:12]} target merge: AI-Agent trailer がない"
        in captured.err
    )
    # 失格の理由 finding が 1 本増えるので 2 違反 (target 側 + 担い手失格)。
    assert "3 件中 2 違反" in captured.err
    assert "forward-corrected=1" not in captured.out
    # 免除自体は発火しており (だから normal_findings は空)、公開もされている。
    assert (
        "check_ai_provenance: implementation-author-waived "
        f"label={history.correction} reason={WAIVER_REASON} "
        f"ratified={WAIVER_RATIFIED}"
    ) in captured.out
    assert "implementation-author-waived=1" in captured.out


def test_forward_correction_without_waiver_is_still_accepted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    """受理集合の過剰縮小 (waiver 無しの正常な前方訂正まで拒否) を検出する。"""
    history = _make_correction_history(tmp_path, monkeypatch)
    assert _run_range(
        monkeypatch, f"{history.target}^1..{history.correction}",
    ) == 0
    captured = capsys.readouterr()
    assert (
        "forward-corrected=1 "
        f"target={history.target} correction={history.correction}"
    ) in captured.out
    assert "implementation-author-waived" not in captured.out
    assert captured.err == ""


def test_waiver_disqualified_correction_carrier_explains_the_reason(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    """規律 3: 担い手失格を沈黙 (pass/fail) で終わらせず理由を構造化して返す。

    理由が無いと、stderr に出るのは target 側の「AI-Agent trailer がない」だけで、
    運用者は correction をもう 1 件足そうとして exact 1 件規則に当たる。
    無条件に出す実装 (恒真化) は、直前の
    test_forward_correction_without_waiver_is_still_accepted が
    captured.err == "" で殺す。
    """
    history = _make_correction_history(
        tmp_path,
        monkeypatch,
        correction_builder=lambda payload: (
            "forward correction\n\n"
            "AI-Agent: product=claude; model=fable-5; reasoning=xhigh; "
            "role=author\n"
            f"AI-Agent-Correction: {payload}\n"
            + WAIVER_LINE
        ),
        correction_files={"tools/correction.py": "CORRECTION = True\n"},
    )
    assert _run_range(
        monkeypatch, f"{history.target}^1..{history.correction}",
    ) == 1
    captured = capsys.readouterr()
    assert (
        f"{history.correction[:12]} forward correction: "
        "AI-Agent-Correction commit が AI-Agent-Waiver 行を持つため"
        "前方訂正の担い手になれない"
    ) in captured.err


# --- W: 免除件数の意味論 ----------------------------------------------------


def test_waived_count_excludes_docs_only_commits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    history = _waiver_history(tmp_path)
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    assert _run_range(
        monkeypatch, f"{history['epoch']}..{history['waived_docs']}",
    ) == 0
    captured = capsys.readouterr()
    assert (
        "check_ai_provenance: implementation-author-waived "
        f"label={history['waived_implementation']} reason={WAIVER_REASON} "
        f"ratified={WAIVER_RATIFIED}"
    ) in captured.out
    assert history["waived_docs"] not in captured.out
    assert "implementation-author-waived=1" in captured.out
    assert captured.err == ""


def test_waived_count_is_reported_on_stdout_on_both_green_and_red(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    history = _waiver_history(tmp_path)
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    assert _run_range(
        monkeypatch, f"{history['epoch']}..{history['violating']}",
    ) == 1
    captured = capsys.readouterr()
    assert "implementation-author-waived=1" in captured.out
    assert (
        "実装面に Codex role=author がない — paths=tools/violating.py"
        in captured.err
    )
    assert "3 件中 1 違反" in captured.err


def test_waiver_is_nonretroactive_before_implementation_policy_epoch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    legacy = _commit(
        tmp_path,
        {
            "docs/ai-provenance.md": "# legacy policy\n",
            "tools/legacy.py": "LEGACY = True\n",
        },
        CLAUDE_AUTHOR + "AI-Agent-Waiver: reason=BAD; ratified=nope\n",
    )
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    assert provenance._implementation_policy_commit() is None
    assert _run_range(monkeypatch, f"{legacy}^!") == 0
    captured = capsys.readouterr()
    # epoch 前は waiver の形式検査も免除も動かない。
    assert "AI-Agent-Waiver" not in captured.err
    assert "implementation-author-waived" not in captured.out


def test_waiver_message_file_gate_exempts_staged_implementation_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    _commit(
        tmp_path,
        {
            "docs/ai-provenance.md": (
                provenance.IMPLEMENTATION_POLICY_NEEDLE + "\n"
            ),
        },
        CODEX_AUTHOR,
    )
    staged = tmp_path / "tools" / "staged.py"
    staged.parent.mkdir(parents=True)
    staged.write_text("STAGED = True\n", encoding="utf-8")
    _git(tmp_path, "add", "tools/staged.py")
    message = tmp_path / "message.txt"
    message.write_text(CLAUDE_AUTHOR_WAIVED, encoding="utf-8")

    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        sys, "argv",
        ["check_ai_provenance.py", "--message-file", str(message)],
    )
    assert provenance.main(site=site_policy.OTHER) == 0
    captured = capsys.readouterr()
    assert (
        "check_ai_provenance: implementation-author-waived "
        f"label={message} reason={WAIVER_REASON} ratified={WAIVER_RATIFIED}"
    ) in captured.out
    assert "implementation-author-waived=1" in captured.out
    assert captured.err == ""


def test_waiver_message_file_docs_only_change_is_not_counted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    _init_repo(tmp_path)
    _commit(
        tmp_path,
        {
            "docs/ai-provenance.md": (
                provenance.IMPLEMENTATION_POLICY_NEEDLE + "\n"
            ),
        },
        CODEX_AUTHOR,
    )
    staged = tmp_path / "docs" / "staged.md"
    staged.write_text("docs only\n", encoding="utf-8")
    _git(tmp_path, "add", "docs/staged.md")
    message = tmp_path / "message.txt"
    message.write_text(CLAUDE_AUTHOR_WAIVED, encoding="utf-8")

    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        sys, "argv",
        ["check_ai_provenance.py", "--message-file", str(message)],
    )
    assert provenance.main(site=site_policy.OTHER) == 0
    captured = capsys.readouterr()
    assert "implementation-author-waived" not in captured.out


# --- C-2: site gate (第一層) ------------------------------------------------


def test_login_history_audit_dispatches_to_compute_and_returns_child_rc(
    monkeypatch: pytest.MonkeyPatch,
):
    seen: dict[str, list[str]] = {}

    def fake_dispatch(argv):
        seen["argv"] = list(argv)
        return 7

    def refuse_audit(commits):
        raise AssertionError("login node must not run the history audit")

    monkeypatch.setattr(provenance, "_audit_history", refuse_audit)
    assert provenance.main(
        ["--range", "aaa..bbb"],
        site=site_policy.PEGASUS_LOGIN,
        dispatch_fn=fake_dispatch,
        admit_fn=lambda estimate: (LH.Admission.DISPATCH, "test"),
    ) == 7
    assert seen["argv"] == ["--range", "aaa..bbb"]


def test_force_dispatch_login_bypasses_provenance_headroom_and_queue(
    monkeypatch: pytest.MonkeyPatch,
):
    dispatch = mock.Mock(return_value=7)
    monkeypatch.setattr(provenance, "_bounded_scope_membership", lambda: None)
    monkeypatch.setattr(
        LH,
        "grant_budget",
        mock.Mock(side_effect=AssertionError("headroom must not be read")),
    )
    monkeypatch.setattr(
        provenance,
        "_queue_dispatch_possible",
        mock.Mock(side_effect=AssertionError("queue must not be read")),
    )
    monkeypatch.setattr(
        provenance,
        "_audit_history",
        mock.Mock(side_effect=AssertionError("login must not audit locally")),
    )

    assert provenance.main(
        ["--force-dispatch", "--range", "aaa..bbb"],
        site=site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
    ) == 7
    dispatch.assert_called_once_with(["--range", "aaa..bbb"])


def test_without_force_dispatch_provenance_login_with_headroom_runs_local(
    monkeypatch: pytest.MonkeyPatch,
):
    grant = mock.Mock(return_value=(LH.Admission.LOCAL, 1234, "test"))
    scope = mock.Mock(return_value=provenance._ScopeResult("child_rc", 0))
    monkeypatch.setattr(LH, "grant_budget", grant)
    monkeypatch.setattr(provenance, "_run_bounded_scope", scope)
    monkeypatch.setattr(
        provenance,
        "_queue_dispatch_possible",
        mock.Mock(side_effect=AssertionError("local headroom needs no queue")),
    )

    assert provenance.main(
        ["--range", "aaa..bbb"],
        site=site_policy.PEGASUS_LOGIN,
        dispatch_fn=mock.Mock(side_effect=AssertionError("must stay local")),
    ) == 0
    grant.assert_called_once_with(operation="provenance-range")
    scope.assert_called_once_with(["--range", "aaa..bbb"], 1234)


def test_default_login_admission_uses_login_headroom_grant_budget(
    monkeypatch: pytest.MonkeyPatch,
):
    grant = mock.Mock(return_value=(LH.Admission.DISPATCH, None, "test"))
    monkeypatch.setattr(LH, "grant_budget", grant)
    monkeypatch.setattr(
        provenance,
        "_queue_dispatch_possible",
        lambda: (True, "queue"),
    )
    assert provenance.main(
        ["--range", "aaa..bbb"],
        site=site_policy.PEGASUS_LOGIN,
        dispatch_fn=lambda argv: 7,
    ) == 7
    grant.assert_called_once_with(operation="provenance-range")


def test_provenance_without_range_uses_operation_and_releases_lease(
    monkeypatch: pytest.MonkeyPatch,
):
    lease = mock.Mock()
    grant = LH.BudgetGrant(LH.Admission.LOCAL, 1234, "小さい前回ピーク", lease)
    budget = mock.Mock(return_value=grant)
    monkeypatch.setattr(LH, "grant_budget", budget)
    monkeypatch.setattr(
        provenance,
        "_run_bounded_scope",
        lambda argv, cap: provenance._ScopeResult("child_rc", 0),
    )

    assert provenance.main(
        [],
        site=site_policy.PEGASUS_LOGIN,
        dispatch_fn=mock.Mock(side_effect=AssertionError("must stay local")),
    ) == 0
    budget.assert_called_once_with(operation="provenance")
    lease.release.assert_called_once_with()


def test_provenance_releases_budget_lease_on_interrupt(
    monkeypatch: pytest.MonkeyPatch,
):
    lease = mock.Mock()
    grant = LH.BudgetGrant(LH.Admission.LOCAL, 1234, "test", lease)
    monkeypatch.setattr(LH, "grant_budget", lambda **kwargs: grant)
    monkeypatch.setattr(
        provenance,
        "_run_bounded_scope",
        mock.Mock(side_effect=KeyboardInterrupt),
    )

    with pytest.raises(KeyboardInterrupt):
        provenance.main(
            [],
            site=site_policy.PEGASUS_LOGIN,
            dispatch_fn=mock.Mock(side_effect=AssertionError("must not dispatch")),
        )
    lease.release.assert_called_once_with()


def test_provenance_peak_and_lease_failures_are_best_effort():
    broken = mock.Mock()
    broken.bind_scope.side_effect = RuntimeError("bind failed")
    broken.release.side_effect = RuntimeError("release failed")
    module = mock.Mock()
    module.remember_peak.side_effect = RuntimeError("write failed")

    provenance._safe_bind_scope(broken, Path("/sys/fs/cgroup/test.scope"))
    provenance._safe_release_grant(broken)
    provenance._safe_remember_peak(module, "provenance", 1)


def test_previous_provenance_cap_estimate_dispatches_without_local_scope(
    monkeypatch: pytest.MonkeyPatch,
):
    budget = mock.Mock(
        return_value=(LH.Admission.DISPATCH, None, "前回の監査は cap 到達"),
    )
    dispatch = mock.Mock(return_value=9)
    scope = mock.Mock(side_effect=AssertionError("estimated audit must dispatch"))
    monkeypatch.setattr(LH, "grant_budget", budget)
    monkeypatch.setattr(
        provenance, "_queue_dispatch_possible", lambda: (True, "queue"),
    )
    monkeypatch.setattr(provenance, "_run_bounded_scope", scope)

    assert provenance.main(
        ["--range", "aaa..bbb"],
        site=site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
    ) == 9
    budget.assert_called_once_with(operation="provenance-range")
    scope.assert_not_called()
    dispatch.assert_called_once_with(["--range", "aaa..bbb"])


@pytest.mark.parametrize(
    ("headroom_available", "queue_available", "expected"),
    [
        (True, True, "local"),
        (True, False, "local"),
        (False, True, "dispatch"),
        (False, False, "local"),
    ],
)
def test_provenance_headroom_and_queue_four_quadrants(
    monkeypatch: pytest.MonkeyPatch,
    headroom_available: bool,
    queue_available: bool,
    expected: str,
):
    grants = []
    queue_checks = []
    caps = []
    dispatch = mock.Mock(return_value=7)

    def grant_budget(**kwargs):
        grants.append(kwargs)
        if headroom_available:
            return LH.Admission.LOCAL, 2000, "観測余裕=2000 bytes"
        if kwargs.get("min_bytes") == 0:
            return LH.Admission.LOCAL, 500, "観測余裕=500 bytes"
        return LH.Admission.DISPATCH, None, "観測余裕=500 bytes"

    def queue_status():
        queue_checks.append(True)
        return queue_available, "キュー gen_S は ENA=DIS、STS=INA"

    def run_scope(argv, cap):
        caps.append(cap)
        return provenance._ScopeResult("child_rc", 0)

    monkeypatch.setattr(LH, "grant_budget", grant_budget)
    monkeypatch.setattr(provenance, "_queue_dispatch_possible", queue_status)
    monkeypatch.setattr(
        provenance,
        "_run_bounded_scope",
        run_scope,
    )

    rc = provenance.main(
        ["--range", "aaa..bbb"],
        site=site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
    )

    assert rc == (0 if expected == "local" else 7)
    assert len(queue_checks) == (0 if headroom_available else 1)
    expected_grants = (
        [{"operation": "provenance-range"}]
        if headroom_available or queue_available
        else [
            {"operation": "provenance-range"},
            {"min_bytes": 0, "operation": "provenance-range"},
        ]
    )
    assert grants == expected_grants
    assert caps == ([2000 if headroom_available else 500] if expected == "local" else [])
    assert dispatch.call_count == (1 if expected == "dispatch" else 0)


def test_provenance_headroom_short_queue_unavailable_cap_oom_stops(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    def grant_budget(**kwargs):
        if kwargs.get("min_bytes") == 0:
            return LH.Admission.LOCAL, 500, "観測余裕=500 bytes"
        return LH.Admission.DISPATCH, None, "観測余裕=500 bytes"

    dispatch = mock.Mock(side_effect=AssertionError("must not dispatch"))
    monkeypatch.setattr(LH, "grant_budget", grant_budget)
    monkeypatch.setattr(
        provenance,
        "_queue_dispatch_possible",
        lambda: (False, "キュー gen_S は ENA=DIS、STS=INA"),
    )
    monkeypatch.setattr(
        provenance,
        "_run_bounded_scope",
        lambda argv, cap: provenance._ScopeResult("cap_oom"),
    )

    assert provenance.main(
        ["--range", "aaa..bbb"],
        site=site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
    ) == provenance.PEGASUS_DISPATCH_RC
    error = capsys.readouterr().err
    assert "ログインの余裕もキューも無いため、いまは実行できません" in error
    assert "500 bytes" in error
    assert "ENA=DIS" in error
    assert "STS=INA" in error
    dispatch.assert_not_called()


def test_provenance_headroom_short_queue_unavailable_zero_budget_stops(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    reason = "予約控除後の観測余裕=0 bytes、現在使用量=99 bytes、実効天井=99 bytes"
    dispatch = mock.Mock(side_effect=AssertionError("must not dispatch"))
    scope = mock.Mock(side_effect=AssertionError("scope must not start"))
    monkeypatch.setattr(
        LH,
        "grant_budget",
        lambda **kwargs: (LH.Admission.DISPATCH, None, reason),
    )
    monkeypatch.setattr(
        provenance,
        "_queue_dispatch_possible",
        lambda: (False, "キュー gen_S は ENA=ENA、STS=INA"),
    )
    monkeypatch.setattr(provenance, "_run_bounded_scope", scope)

    assert provenance.main(
        ["--range", "aaa..bbb"],
        site=site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
    ) == provenance.PEGASUS_DISPATCH_RC
    error = capsys.readouterr().err
    assert "0 bytes" in error
    assert "ENA=ENA" in error
    assert "STS=INA" in error
    dispatch.assert_not_called()
    scope.assert_not_called()


def test_login_local_scope_returns_child_rc_without_dispatch(
    monkeypatch: pytest.MonkeyPatch,
):
    dispatch = []
    monkeypatch.setattr(
        provenance,
        "_run_bounded_scope",
        lambda argv, cap: provenance._ScopeResult("child_rc", 3),
    )

    def refuse_dispatch(argv):
        dispatch.append(list(argv))
        raise AssertionError("child rc must not fallback")

    assert provenance.main(
        ["--range", "aaa..bbb"],
        site=site_policy.PEGASUS_LOGIN,
        dispatch_fn=refuse_dispatch,
        admit_fn=lambda estimate: (LH.Admission.LOCAL, "test"),
    ) == 3
    assert dispatch == []


def test_provenance_cap_oom_dirty_before_unchanged_after_dispatches_once(
    monkeypatch: pytest.MonkeyPatch,
):
    seen = []
    dirty = provenance._TreeFingerprint("a" * 64, (91, 127, 44, 0, 0))
    monkeypatch.setattr(
        provenance,
        "_run_bounded_scope",
        lambda argv, cap: provenance._ScopeResult("cap_oom"),
    )
    fingerprint = mock.Mock(side_effect=[dirty, dirty])
    monkeypatch.setattr(
        provenance,
        "_tree_and_submodules_fingerprint",
        fingerprint,
    )

    def dispatch(argv):
        seen.append(list(argv))
        return 8

    assert provenance.main(
        ["--range", "aaa..bbb"],
        site=site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
        admit_fn=lambda estimate: (LH.Admission.LOCAL, "test"),
    ) == 8
    assert seen == [["--range", "aaa..bbb"]]
    assert fingerprint.call_count == 2


def test_provenance_cap_oom_changed_tree_does_not_dispatch(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    before = provenance._TreeFingerprint("a" * 64, (91, 127, 44, 0, 0))
    after = provenance._TreeFingerprint("b" * 64, (112, 203, 44, 0, 0))
    monkeypatch.setattr(
        provenance,
        "_run_bounded_scope",
        lambda argv, cap: provenance._ScopeResult("cap_oom"),
    )
    monkeypatch.setattr(
        provenance,
        "_tree_and_submodules_fingerprint",
        mock.Mock(side_effect=[before, after]),
    )
    dispatch = mock.Mock(side_effect=AssertionError("changed tree must not dispatch"))

    assert provenance.main(
        ["--range", "aaa..bbb"],
        site=site_policy.PEGASUS_LOGIN,
        dispatch_fn=dispatch,
        admit_fn=lambda estimate: (LH.Admission.LOCAL, "test"),
    ) == provenance.PEGASUS_DISPATCH_RC
    dispatch.assert_not_called()
    assert "状態が変化" in capsys.readouterr().err


def test_provenance_scope_infra_does_not_become_audit_failure(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        provenance,
        "_run_bounded_scope",
        lambda argv, cap: provenance._ScopeResult("dispatch_infra"),
    )
    assert provenance.main(
        [],
        site=site_policy.PEGASUS_LOGIN,
        dispatch_fn=lambda argv: (_ for _ in ()).throw(
            AssertionError("infra must not dispatch"),
        ),
        admit_fn=lambda estimate: (LH.Admission.LOCAL, "test"),
    ) == provenance.PEGASUS_DISPATCH_RC


def test_provenance_scope_argv_uses_only_supported_memory_properties():
    cap = LH.RESERVE_BYTES // 2
    unit = "izanagi-provenance-1234-deadbeef.scope"

    command = provenance._scope_command(["--range", "aaa..bbb"], cap, unit)

    assert command == [
        "systemd-run", "--user", "--scope", "-q", f"--unit={unit}",
        "-p", "MemoryAccounting=yes", "-p", f"MemoryMax={cap}",
        "-p", "MemorySwapMax=0", "--", sys.executable,
        str(Path(provenance.__file__).resolve()), "--range", "aaa..bbb",
    ]
    assert all("MemoryOOMGroup" not in arg for arg in command)


def test_provenance_scope_marker_writes_oom_group_then_requires_cap_and_group(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    unit = "izanagi-provenance-1234-deadbeef.scope"
    cap = LH.RESERVE_BYTES // 2
    proc = tmp_path / "self.cgroup"
    proc.write_text(
        f"0::/user.slice/user-123.slice/app.slice/{unit}\n",
        encoding="utf-8",
    )
    cgroup_root = tmp_path / "cgroup"
    scope = cgroup_root / "user.slice" / "user-123.slice" / "app.slice" / unit
    scope.mkdir(parents=True)
    (scope / "memory.max").write_text(f"{cap}\n", encoding="utf-8")
    (scope / "memory.oom.group").write_text("0\n", encoding="utf-8")
    monkeypatch.setenv(provenance._BOUNDED_SCOPE_UNIT_ENV, unit)
    monkeypatch.setenv(provenance._BOUNDED_SCOPE_CAP_ENV, str(cap))
    monkeypatch.setattr(provenance, "_PROC_SELF_CGROUP", proc)
    monkeypatch.setattr(provenance, "_CGROUP_ROOT", cgroup_root)

    assert provenance._bounded_scope_membership() is True
    assert (scope / "memory.oom.group").read_text(encoding="utf-8") == "1\n"
    (scope / "memory.max").write_text(f"{cap + 1}\n", encoding="utf-8")
    assert provenance._bounded_scope_membership() is False


def _write_provenance_scope_properties(
    scope: Path,
    memory_max: str,
    *,
    oom_group: str = "1",
) -> None:
    (scope / "memory.max").write_text(f"{memory_max}\n", encoding="utf-8")
    (scope / "memory.oom.group").write_text(f"{oom_group}\n", encoding="utf-8")


_FULLWIDTH_DIGIT_TRANSLATION = str.maketrans(
    "0123456789",
    "０１２３４５６７８９",
)


def _stub_page_size(name: str, value: object) -> object:
    assert name == "SC_PAGE_SIZE", (
        f"unexpected os.sysconf key {name!r}; expected 'SC_PAGE_SIZE'"
    )
    return value


def _fullwidth_decimal(value: int) -> str:
    return str(value).translate(_FULLWIDTH_DIGIT_TRANSLATION)


@pytest.mark.parametrize("page_size", [4096, 65536], ids=["page-4k", "page-64k"])
def test_provenance_scope_properties_accept_page_floor_and_reject_other_values(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    page_size: int,
):
    cap = 3 * page_size + page_size // 4 + 17
    floor = cap - cap % page_size
    assert cap % page_size != 0
    assert floor != cap
    monkeypatch.setattr(
        provenance.os,
        "sysconf",
        lambda name: _stub_page_size(name, page_size),
    )
    scope = tmp_path / "scope"
    scope.mkdir()

    _write_provenance_scope_properties(scope, str(floor))
    assert provenance._scope_properties_are_enforced(scope, cap) is True
    _write_provenance_scope_properties(scope, str(cap))
    assert provenance._scope_properties_are_enforced(scope, cap) is True

    for rejected in (
        str(cap + 1),
        str(floor + 1),
        str(floor - 1),
        str(cap - 1),
        "max",
        "",
        "   ",
        f"+{cap}",
        f"0{cap}",
        _fullwidth_decimal(cap),
        _fullwidth_decimal(floor),
    ):
        _write_provenance_scope_properties(scope, rejected)
        assert provenance._scope_properties_are_enforced(scope, cap) is False

    _write_provenance_scope_properties(scope, str(floor), oom_group="0")
    assert provenance._scope_properties_are_enforced(scope, cap) is False


@pytest.mark.parametrize("page_size", [4096, 65536], ids=["page-4k", "page-64k"])
@pytest.mark.parametrize(
    "invalid_page_size",
    [
        pytest.param(OSError("unavailable"), id="oserror"),
        pytest.param(ValueError("unavailable"), id="valueerror"),
        pytest.param(0, id="zero"),
        pytest.param(-1, id="negative"),
        pytest.param(True, id="bool"),
        pytest.param(None, id="none"),
        pytest.param("4096", id="string"),
    ],
)
def test_provenance_scope_properties_sysconf_failure_or_invalid_is_exact_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    page_size: int,
    invalid_page_size: object,
):
    cap = 3 * page_size + page_size // 4 + 17
    floor = cap - cap % page_size
    assert cap % page_size != 0
    assert floor != cap
    monkeypatch.setattr(
        provenance.os,
        "sysconf",
        lambda name: _stub_page_size(name, page_size),
    )
    scope = tmp_path / "scope"
    scope.mkdir()
    _write_provenance_scope_properties(scope, str(floor))
    assert provenance._scope_properties_are_enforced(scope, cap) is True

    if isinstance(invalid_page_size, BaseException):
        def fail_sysconf(name: str) -> int:
            _stub_page_size(name, None)
            raise invalid_page_size

        monkeypatch.setattr(provenance.os, "sysconf", fail_sysconf)
    else:
        monkeypatch.setattr(
            provenance.os,
            "sysconf",
            lambda name: _stub_page_size(name, invalid_page_size),
        )
    _write_provenance_scope_properties(scope, str(floor))
    assert provenance._scope_properties_are_enforced(scope, cap) is False
    _write_provenance_scope_properties(scope, str(cap))
    assert provenance._scope_properties_are_enforced(scope, cap) is True


@pytest.mark.parametrize("page_size", [4096, 65536], ids=["page-4k", "page-64k"])
def test_provenance_scope_properties_preserve_cap_boundaries(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    page_size: int,
):
    detector_cap = 3 * page_size + page_size // 4 + 17
    detector_floor = detector_cap - detector_cap % page_size
    assert detector_cap % page_size != 0
    assert detector_floor != detector_cap
    monkeypatch.setattr(
        provenance.os,
        "sysconf",
        lambda name: _stub_page_size(name, page_size),
    )
    scope = tmp_path / "scope"
    scope.mkdir()
    _write_provenance_scope_properties(scope, str(detector_floor))
    assert provenance._scope_properties_are_enforced(scope, detector_cap) is True

    for cap, accepted, rejected in (
        (1, ("1", "0"), ("2",)),
        (page_size, (str(page_size),), (str(page_size - 1),)),
        (
            page_size + 1,
            (str(page_size + 1), str(page_size)),
            (str(page_size - 1), str(page_size + 2)),
        ),
        (0, ("0",), (str(-page_size),)),
        (-1, ("-1",), (str(-page_size),)),
    ):
        for memory_max in accepted:
            _write_provenance_scope_properties(scope, memory_max)
            assert provenance._scope_properties_are_enforced(scope, cap) is True
        for memory_max in rejected:
            _write_provenance_scope_properties(scope, memory_max)
            assert provenance._scope_properties_are_enforced(scope, cap) is False

    monkeypatch.setattr(
        provenance.os,
        "sysconf",
        lambda _name: (_ for _ in ()).throw(
            AssertionError("nonpositive cap must not query page size"),
        ),
    )
    for cap in (0, -1):
        _write_provenance_scope_properties(scope, str(cap))
        assert provenance._scope_properties_are_enforced(scope, cap) is True


@pytest.mark.parametrize("page_size", [4096, 65536], ids=["page-4k", "page-64k"])
def test_scope_property_implementations_have_behavior_parity(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    page_size: int,
):
    cap = 3 * page_size + page_size // 4 + 17
    floor = cap - cap % page_size
    assert cap % page_size != 0
    assert floor != cap
    scope = tmp_path / "scope"
    scope.mkdir()
    monkeypatch.setattr(
        provenance.os,
        "sysconf",
        lambda name: _stub_page_size(name, page_size),
    )
    _write_provenance_scope_properties(scope, str(floor))
    assert (
        run_tests_tool._scope_properties_are_enforced(scope, cap),
        provenance._scope_properties_are_enforced(scope, cap),
    ) == (True, True)

    cases = (
        (page_size, cap, str(cap), "1", True),
        (page_size, cap, str(floor), "1", True),
        (page_size, cap, str(floor + 1), "1", False),
        (page_size, cap, str(cap + 1), "1", False),
        (page_size, cap, "max", "1", False),
        (page_size, cap, _fullwidth_decimal(cap), "1", False),
        (page_size, cap, _fullwidth_decimal(floor), "1", False),
        (page_size, cap, str(floor), "0", False),
        (page_size, 1, "0", "1", True),
        (page_size, page_size, str(page_size), "1", True),
        (page_size, page_size + 1, str(page_size), "1", True),
        (page_size, 0, "0", "1", True),
        (page_size, -1, "-1", "1", True),
        (None, cap, str(cap), "1", True),
        (None, cap, str(floor), "1", False),
    )
    for page_value, case_cap, memory_max, oom_group, expected in cases:
        monkeypatch.setattr(
            provenance.os,
            "sysconf",
            lambda name: _stub_page_size(name, page_value),
        )
        _write_provenance_scope_properties(
            scope,
            memory_max,
            oom_group=oom_group,
        )
        actual = (
            run_tests_tool._scope_properties_are_enforced(scope, case_cap),
            provenance._scope_properties_are_enforced(scope, case_cap),
        )
        assert actual == (expected, expected)


@pytest.mark.parametrize(
    ("failure", "readback", "expected_events"),
    [
        ("write", "1\n", ["write"]),
        ("read", "1\n", ["write", "read"]),
        (None, "0\n", ["write", "read"]),
    ],
)
def test_provenance_scope_oom_group_write_and_readback_fail_closed(
    failure, readback, expected_events,
):
    events = []

    class OomGroupFile:
        def write_text(self, value, *, encoding):
            events.append("write")
            assert (value, encoding) == ("1\n", "utf-8")
            if failure == "write":
                raise OSError("injected write failure")

        def read_text(self, *, encoding):
            events.append("read")
            assert encoding == "utf-8"
            if failure == "read":
                raise OSError("injected read failure")
            return readback

    class Scope:
        def __truediv__(self, name):
            assert name == "memory.oom.group"
            return OomGroupFile()

    assert provenance._attest_scope_oom_group(Scope()) is False
    assert events == expected_events


def test_failed_provenance_scope_oom_attestation_refuses_with_infra_rc(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    monkeypatch.setattr(provenance, "_bounded_scope_membership", lambda: False)
    monkeypatch.setattr(
        provenance,
        "_audit_history",
        lambda commits: (_ for _ in ()).throw(
            AssertionError("child must fail before provenance audit"),
        ),
    )

    assert provenance.main([], site=site_policy.OTHER) == 16
    assert "memory.oom.group" in capsys.readouterr().err


def test_provenance_scope_disappearance_after_sample_keeps_child_rc(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    state = {"disappeared": False}
    process = mock.Mock(pid=4242)
    process.poll.return_value = None

    def wait(*args, **kwargs):
        state["disappeared"] = True
        return 1

    process.wait.side_effect = wait
    monkeypatch.setattr(provenance.subprocess, "Popen", lambda *a, **kw: process)
    def cgroup_path(path, unit):
        return None if state["disappeared"] else tmp_path

    def attest(path):
        assert not state["disappeared"], "post-run re-attestation is forbidden"
        return True

    def properties(path, cap):
        assert not state["disappeared"], "post-run property read is forbidden"
        return True

    def current(path):
        if state["disappeared"]:
            raise OSError("scope disappeared")
        return 424242

    monkeypatch.setattr(provenance, "_scope_cgroup_path", cgroup_path)
    monkeypatch.setattr(provenance, "_attest_scope_oom_group", attest)
    monkeypatch.setattr(provenance, "_scope_properties_are_enforced", properties)
    monkeypatch.setattr(provenance, "_read_scope_current", current)

    def events(path):
        if state["disappeared"]:
            raise OSError("scope disappeared")
        return 0, 0

    monkeypatch.setattr(provenance, "_read_scope_events", events)
    grant = mock.Mock()
    remember = mock.Mock()
    monkeypatch.setattr(LH, "remember_peak", remember)
    token = provenance._scope_accounting.set(
        provenance._ScopeAccounting(LH, "provenance-range", grant),
    )

    try:
        result = provenance._run_bounded_scope(
            ["--range", "aaa..bbb"], LH.RESERVE_BYTES // 2,
        )
    finally:
        provenance._scope_accounting.reset(token)
    assert result == provenance._ScopeResult("child_rc", 1)
    assert "bounded scope の観測ピーク: 424242 bytes" in capsys.readouterr().err
    grant.bind_scope.assert_called_once_with(tmp_path)
    remember.assert_called_once_with("provenance-range", 424242)


def test_provenance_scope_without_event_sample_is_dispatch_infra(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    process = mock.Mock(pid=4242)
    process.poll.return_value = None
    process.wait.return_value = 3
    monkeypatch.setattr(provenance.subprocess, "Popen", lambda *a, **kw: process)
    monkeypatch.setattr(
        provenance, "_scope_cgroup_path", lambda path, unit: tmp_path,
    )
    monkeypatch.setattr(
        provenance, "_attest_scope_oom_group", lambda path: True,
    )
    monkeypatch.setattr(
        provenance, "_scope_properties_are_enforced", lambda path, cap: True,
    )
    monkeypatch.setattr(provenance, "_read_scope_current", lambda path: 1)
    monkeypatch.setattr(
        provenance,
        "_read_scope_events",
        mock.Mock(side_effect=OSError("unreadable")),
    )

    result = provenance._run_bounded_scope(
        ["--range", "aaa..bbb"], LH.RESERVE_BYTES // 2,
    )
    assert result == provenance._ScopeResult("dispatch_infra")


@pytest.mark.parametrize(
    ("oom_group_attested", "properties_attested"),
    [(False, True), (True, False)],
)
def test_provenance_scope_attestation_failure_stops_scope(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    oom_group_attested: bool,
    properties_attested: bool,
):
    process = mock.Mock(pid=4242)
    process.poll.return_value = None
    stop = mock.Mock()
    monkeypatch.setattr(provenance.subprocess, "Popen", lambda *a, **kw: process)
    monkeypatch.setattr(
        provenance, "_scope_cgroup_path", lambda path, unit: tmp_path,
    )
    monkeypatch.setattr(
        provenance,
        "_attest_scope_oom_group",
        lambda path: oom_group_attested,
    )
    monkeypatch.setattr(
        provenance,
        "_scope_properties_are_enforced",
        lambda path, cap: properties_attested,
    )
    monkeypatch.setattr(provenance, "_stop_bounded_scope", stop)

    result = provenance._run_bounded_scope(
        ["--range", "aaa..bbb"], LH.RESERVE_BYTES // 2,
    )

    assert result == provenance._ScopeResult("dispatch_infra")
    stop.assert_called_once_with(process, mock.ANY)
    process.wait.assert_not_called()


def test_provenance_continuing_samples_retain_cap_oom_and_highest_peak(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    state = {"disappeared": False, "event_reads": 0, "current_reads": 0}
    second_sample = threading.Event()
    process = mock.Mock(pid=4242)
    process.poll.return_value = None

    def wait(*args, **kwargs):
        assert second_sample.wait(1), "sampler did not continue to a second sample"
        state["disappeared"] = True
        return 137

    process.wait.side_effect = wait
    monkeypatch.setattr(provenance.subprocess, "Popen", lambda *a, **kw: process)
    monkeypatch.setattr(
        provenance, "_scope_cgroup_path", lambda path, unit: tmp_path,
    )
    monkeypatch.setattr(
        provenance, "_attest_scope_oom_group", lambda path: True,
    )
    monkeypatch.setattr(
        provenance, "_scope_properties_are_enforced", lambda path, cap: True,
    )

    def current(path):
        if state["disappeared"]:
            raise OSError("scope disappeared")
        state["current_reads"] += 1
        return 100 if state["current_reads"] == 1 else 900

    def events(path):
        if state["disappeared"]:
            return 1, 1
        state["event_reads"] += 1
        if state["event_reads"] == 1:
            return 0, 0
        second_sample.set()
        return 1, 1

    monkeypatch.setattr(provenance, "_read_scope_current", current)
    monkeypatch.setattr(provenance, "_read_scope_events", events)
    grant = mock.Mock()
    remember = mock.Mock()
    monkeypatch.setattr(LH, "remember_peak", remember)
    token = provenance._scope_accounting.set(
        provenance._ScopeAccounting(LH, "provenance-range", grant),
    )

    cap = LH.RESERVE_BYTES // 2
    try:
        result = provenance._run_bounded_scope(
            ["--range", "aaa..bbb"], cap,
        )
    finally:
        provenance._scope_accounting.reset(token)
    assert result == provenance._ScopeResult("cap_oom")
    assert "bounded scope の観測ピーク: 900 bytes" in capsys.readouterr().err
    grant.bind_scope.assert_called_once_with(tmp_path)
    remember.assert_called_once_with("provenance-range", cap)


@pytest.mark.parametrize("returncode", [137, -9], ids=["rc137", "sigkill"])
def test_provenance_signal_without_final_cap_proof_is_dispatch_infra(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    returncode: int,
):
    state = {"disappeared": False}
    process = mock.Mock(pid=4242)
    process.poll.return_value = None

    def wait(*args, **kwargs):
        state["disappeared"] = True
        return returncode

    process.wait.side_effect = wait
    monkeypatch.setattr(provenance.subprocess, "Popen", lambda *a, **kw: process)
    monkeypatch.setattr(
        provenance, "_scope_cgroup_path", lambda path, unit: tmp_path,
    )
    monkeypatch.setattr(provenance, "_attest_scope_oom_group", lambda path: True)
    monkeypatch.setattr(
        provenance, "_scope_properties_are_enforced", lambda path, cap: True,
    )
    monkeypatch.setattr(provenance, "_read_scope_current", lambda path: 1)

    def events(path):
        if state["disappeared"]:
            raise OSError("scope disappeared before final events")
        return 0, 0

    monkeypatch.setattr(provenance, "_read_scope_events", events)

    result = provenance._run_bounded_scope(
        ["--range", "aaa..bbb"], LH.RESERVE_BYTES // 2,
    )
    assert result == provenance._ScopeResult("dispatch_infra")


@pytest.mark.parametrize(
    ("events", "expected"),
    [
        ((1, 0), provenance._ScopeResult("dispatch_infra")),
        ((0, 1), provenance._ScopeResult("dispatch_infra")),
        ((1, 1), provenance._ScopeResult("cap_oom")),
    ],
)
def test_provenance_cap_oom_requires_both_max_and_oom_events(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    events: tuple[int, int],
    expected: provenance._ScopeResult,
):
    state = {"disappeared": False}
    process = mock.Mock(pid=4242)
    process.poll.return_value = None

    def wait(*args, **kwargs):
        state["disappeared"] = True
        return 137

    process.wait.side_effect = wait
    monkeypatch.setattr(provenance.subprocess, "Popen", lambda *a, **kw: process)
    monkeypatch.setattr(
        provenance, "_scope_cgroup_path", lambda path, unit: tmp_path,
    )
    monkeypatch.setattr(
        provenance, "_attest_scope_oom_group", lambda path: True,
    )
    monkeypatch.setattr(
        provenance, "_scope_properties_are_enforced", lambda path, cap: True,
    )

    def current(path):
        if state["disappeared"]:
            raise OSError("scope disappeared")
        return 1

    def read_events(path):
        return events

    monkeypatch.setattr(provenance, "_read_scope_current", current)
    monkeypatch.setattr(provenance, "_read_scope_events", read_events)

    result = provenance._run_bounded_scope(
        ["--range", "aaa..bbb"], LH.RESERVE_BYTES // 2,
    )
    assert result == expected


def test_provenance_login_headroom_import_failure_dispatches(
    monkeypatch: pytest.MonkeyPatch,
):
    real_import = provenance.importlib.import_module

    def fail_login_headroom(name, *args, **kwargs):
        if name == "orchestrator.campaign.login_headroom":
            raise ImportError("injected")
        return real_import(name, *args, **kwargs)

    seen = []
    monkeypatch.setattr(provenance.importlib, "import_module", fail_login_headroom)
    assert provenance.main(
        ["--range", "aaa..bbb"],
        site=site_policy.PEGASUS_LOGIN,
        dispatch_fn=lambda argv: seen.append(list(argv)) or 6,
    ) == 6
    assert seen == [["--range", "aaa..bbb"]]


def test_provenance_queue_state_import_failure_is_dispatch_available(
    monkeypatch: pytest.MonkeyPatch,
):
    real_import = provenance.importlib.import_module

    def fail_queue_state(name, *args, **kwargs):
        if name == "orchestrator.campaign.queue_state":
            raise ImportError("injected")
        return real_import(name, *args, **kwargs)

    seen = []
    monkeypatch.setattr(
        LH,
        "grant_budget",
        lambda **kwargs: (LH.Admission.DISPATCH, None, "観測余裕=0 bytes"),
    )
    monkeypatch.setattr(provenance.importlib, "import_module", fail_queue_state)

    assert provenance.main(
        ["--range", "aaa..bbb"],
        site=site_policy.PEGASUS_LOGIN,
        dispatch_fn=lambda argv: seen.append(list(argv)) or 6,
    ) == 6
    assert seen == [["--range", "aaa..bbb"]]


@pytest.mark.parametrize("flag", ["--message-file", "--message-f"])
def test_login_message_file_is_dispatch_exempt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    flag: str,
):
    """接頭辞省略形も免除される (raw token allowlist だと queue に詰まる)。"""
    _init_repo(tmp_path)
    message = tmp_path / "message.txt"
    message.write_text("ordinary\n\nAI-Agent: none\n", encoding="utf-8")

    def refuse_dispatch(argv):
        raise AssertionError("message-file preflight must not dispatch")

    monkeypatch.setattr(provenance, "REPO", tmp_path)
    assert provenance.main(
        [flag, str(message)],
        site=site_policy.PEGASUS_LOGIN,
        dispatch_fn=refuse_dispatch,
        admit_fn=lambda estimate: (LH.Admission.DISPATCH, "test"),
    ) == 0
    assert "違反なし" in capsys.readouterr().out


@pytest.mark.parametrize("flag", ["--message-file", "--message-f"])
def test_login_message_file_returns_before_admission_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    flag: str,
):
    _init_repo(tmp_path)
    message = tmp_path / "message.txt"
    message.write_text("ordinary\n\nAI-Agent: none\n", encoding="utf-8")
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(
        provenance,
        "_bounded_scope_membership",
        lambda: (_ for _ in ()).throw(AssertionError("gate must be exempt")),
    )

    assert provenance.main(
        [flag, str(message)],
        site=site_policy.PEGASUS_LOGIN,
        dispatch_fn=lambda argv: (_ for _ in ()).throw(
            AssertionError("dispatch must be exempt"),
        ),
        admit_fn=lambda estimate: (_ for _ in ()).throw(
            AssertionError("admission must be exempt"),
        ),
    ) == 0


def test_suspect_history_audit_refuses_with_infra_rc_without_dispatch(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    def refuse_dispatch(argv):
        raise AssertionError("suspect site must not dispatch")

    def refuse_audit(commits):
        raise AssertionError("suspect site must not run the history audit")

    monkeypatch.setattr(provenance, "_audit_history", refuse_audit)
    assert provenance.main(
        [], site=site_policy.PEGASUS_SUSPECT, dispatch_fn=refuse_dispatch,
    ) == provenance.PEGASUS_DISPATCH_RC
    assert "provenance 履歴監査 を拒否します" in capsys.readouterr().err


def test_force_dispatch_provenance_suspect_still_returns_infra_rc(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        provenance, "_queue_dispatch_possible", lambda: (True, "queue"),
    )

    assert provenance.main(
        ["--force-dispatch", "--range", "aaa..bbb"],
        site=site_policy.PEGASUS_SUSPECT,
        dispatch_fn=mock.Mock(side_effect=AssertionError("must not dispatch")),
    ) == provenance.PEGASUS_DISPATCH_RC


def test_suspect_history_refusal_observes_queue_once_and_includes_hint(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    queue_status = mock.Mock(return_value=(
        False,
        "キュー gen_S は ENA=DIS、STS=INAで、現在利用できません。",
    ))
    monkeypatch.setattr(provenance, "_queue_dispatch_possible", queue_status)

    assert provenance.main(
        [],
        site=site_policy.PEGASUS_SUSPECT,
    ) == provenance.PEGASUS_DISPATCH_RC

    queue_status.assert_called_once_with()
    error = capsys.readouterr().err
    assert "ENA=DIS" in error
    assert "STS=INA" in error
    assert "性能測定は現時点では実施できません" in error


def test_suspect_history_audit_never_enters_local_admission(
    monkeypatch: pytest.MonkeyPatch,
):
    assert provenance.main(
        [],
        site=site_policy.PEGASUS_SUSPECT,
        dispatch_fn=lambda argv: (_ for _ in ()).throw(
            AssertionError("suspect must not dispatch"),
        ),
        admit_fn=lambda estimate: (_ for _ in ()).throw(
            AssertionError("suspect must not admit local"),
        ),
    ) == provenance.PEGASUS_DISPATCH_RC


@pytest.mark.parametrize(
    "site", [site_policy.PEGASUS_COMPUTE, site_policy.OTHER],
)
def test_compute_and_other_sites_audit_locally(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    site: str,
):
    _init_repo(tmp_path)
    commit = _commit(tmp_path, {"docs/local.md": "local\n"}, CODEX_AUTHOR)

    def refuse_dispatch(argv):
        raise AssertionError(f"{site} must audit locally")

    monkeypatch.setattr(provenance, "REPO", tmp_path)
    assert provenance.main(
        ["--range", f"{commit}^!"], site=site, dispatch_fn=refuse_dispatch,
    ) == 0
    assert "1 件、違反なし" in capsys.readouterr().out


@pytest.mark.parametrize(
    "site", [site_policy.PEGASUS_COMPUTE, site_policy.OTHER],
)
def test_force_dispatch_provenance_compute_and_other_audit_locally(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    site: str,
):
    _init_repo(tmp_path)
    commit = _commit(tmp_path, {"docs/local.md": "local\n"}, CODEX_AUTHOR)
    monkeypatch.setattr(provenance, "REPO", tmp_path)

    assert provenance.main(
        ["--force-dispatch", "--range", f"{commit}^!"],
        site=site,
        dispatch_fn=mock.Mock(side_effect=AssertionError("must audit locally")),
    ) == 0
    assert "1 件、違反なし" in capsys.readouterr().out


def test_range_helper_pins_site_and_never_reads_the_ambient_site(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    """_run_range 経由の node が実行ホストの hostname 分類を読まないことを固定する。

    site を渡し忘れると PEGASUS_LOGIN 分類のホストでは node ごとに実 PBS job が
    飛び、PEGASUS_SUSPECT では全 node が rc=16 で赤になる。current_site() を
    発火即失敗にして、この退行が起きた瞬間に落ちるようにする。
    """
    _init_repo(tmp_path)
    commit = _commit(tmp_path, {"docs/pinned.md": "pinned\n"}, CODEX_AUTHOR)

    def refuse_ambient_site() -> str:
        raise AssertionError("range node must not read the ambient site")

    def refuse_dispatch(argv):
        raise AssertionError("range node must not dispatch a PBS job")

    monkeypatch.setattr(provenance, "REPO", tmp_path)
    monkeypatch.setattr(site_policy, "current_site", refuse_ambient_site)
    # dispatch が起きれば例外は rc=16 へ畳まれるので rc 側でも捕まえる。
    monkeypatch.setattr(provenance, "_default_dispatch", refuse_dispatch)
    assert _run_range(monkeypatch, f"{commit}^!") == 0
    assert "1 件、違反なし" in capsys.readouterr().out


def test_every_checker_main_call_in_this_suite_pins_the_site():
    """新設 node が site= を渡し忘れる退行を、その node の追加時点で止める。

    ソース走査が正当な唯一の対象 — 被検査物が production gate ではなく
    このテスト suite 自身の呼出規約だからである。
    """
    tree = ast.parse(Path(__file__).resolve().read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "main"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "provenance"
    ]
    # 恒真化防止: 走査が 1 件も拾えていない状態を先に排除する。
    assert len(calls) >= 30
    unpinned = [
        node.lineno
        for node in calls
        if not any(keyword.arg == "site" for keyword in node.keywords)
    ]
    assert unpinned == []


def test_dispatch_exception_is_folded_into_infra_rc(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    def exploding_dispatch(argv):
        raise OSError("qsub is unavailable")

    def refuse_audit(commits):
        raise AssertionError("login node must not run the history audit")

    monkeypatch.setattr(provenance, "_audit_history", refuse_audit)
    assert provenance.main(
        [], site=site_policy.PEGASUS_LOGIN, dispatch_fn=exploding_dispatch,
        admit_fn=lambda estimate: (LH.Admission.DISPATCH, "test"),
    ) == provenance.PEGASUS_DISPATCH_RC
    assert (
        "Pegasus dispatcher を完了できませんでした: OSError"
        in capsys.readouterr().err
    )


def test_provenance_dispatch_rc_matches_run_tests_contract():
    assert provenance.PEGASUS_DISPATCH_RC == 16
    spec = importlib.util.spec_from_file_location(
        "run_tests_rc_probe", REPO / "tools" / "run_tests.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module._PEGASUS_DISPATCH_RC == provenance.PEGASUS_DISPATCH_RC


def test_default_dispatch_requests_the_provenance_task(
    monkeypatch: pytest.MonkeyPatch,
):
    from tools.pegasus import dispatch_compute

    seen: dict[str, object] = {}

    def fake_dispatch(args, **kwargs):
        seen["args"] = list(args)
        seen["kwargs"] = kwargs
        return 0

    monkeypatch.setattr(dispatch_compute, "dispatch", fake_dispatch)
    assert provenance._default_dispatch(["--range", "aaa..bbb"]) == 0
    assert seen["args"] == ["--range", "aaa..bbb"]
    assert seen["kwargs"]["task"] == "provenance"
    assert seen["kwargs"]["repo_root"] == provenance.REPO


# --- D: 祖先 bitset と並列化 ------------------------------------------------


@pytest.mark.parametrize(
    ("cpus", "expected"), [(0, 1), (1, 1), (3, 3), (32, 32), (48, 32)],
)
def test_audit_workers_default_is_site_derived_and_capped(
    monkeypatch: pytest.MonkeyPatch, cpus: int, expected: int,
):
    assert provenance.AUDIT_WORKERS_CAP == 32
    monkeypatch.setattr(site_policy, "available_cpus", lambda: cpus)
    assert provenance.AUDIT_WORKERS() == expected


def test_audit_history_concurrency_high_water_follows_audit_workers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    """並列度は実際の同時実行数で測る (ソース文字列 grep は恒真ゲート)。"""
    commits, _, _ = _mixed_history(tmp_path, monkeypatch)
    assert len(commits) >= 8
    real_audit = provenance._normal_commit_audit

    def measure(workers: int) -> int:
        lock = threading.Lock()
        state = {"live": 0, "peak": 0}

        def instrumented(commit, **kwargs):
            with lock:
                state["live"] += 1
                state["peak"] = max(state["peak"], state["live"])
            try:
                time.sleep(0.05)
                return real_audit(commit, **kwargs)
            finally:
                with lock:
                    state["live"] -= 1

        monkeypatch.setattr(
            provenance, "AUDIT_WORKERS", lambda count=workers: count,
        )
        monkeypatch.setattr(provenance, "_normal_commit_audit", instrumented)
        try:
            provenance._audit_history(list(commits))
        finally:
            monkeypatch.setattr(
                provenance, "_normal_commit_audit", real_audit,
            )
        return state["peak"]

    assert measure(1) == 1
    assert measure(4) >= 2


def test_audit_history_is_identical_across_worker_counts_and_ancestry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    commits, _, _ = _mixed_history(tmp_path, monkeypatch)
    real_build = provenance._build_ancestry
    results: dict[str, provenance.HistoryAudit] = {}
    for name, workers, use_ancestry in (
        ("sequential-oracle", 1, False),
        ("bitset-1", 1, True),
        ("bitset-2", 2, True),
        ("bitset-16", 16, True),
    ):
        monkeypatch.setattr(
            provenance, "AUDIT_WORKERS", lambda count=workers: count,
        )
        monkeypatch.setattr(
            provenance,
            "_build_ancestry",
            real_build if use_ancestry else (lambda selected, **kwargs: None),
        )
        results[name] = provenance._audit_history(list(commits))

    baseline = results["sequential-oracle"]
    # 恒真化防止: 3 種の出力がすべて非空であることを先に固定する。
    assert baseline.findings
    assert baseline.corrected
    assert baseline.waived
    for name, audit in results.items():
        assert audit.findings == baseline.findings, name
        assert audit.corrected == baseline.corrected, name
        assert audit.waived == baseline.waived, name
        assert audit.known_violations == baseline.known_violations, name


def test_audit_history_findings_follow_input_order_under_skewed_latency(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    """audits が入力順であることを直接固定する (完了順の観測に依存しない)。

    決定性の根拠は Executor.map の契約であって「速いタスクの完了順がたまたま
    入力順と一致すること」ではない。後の commit ほど速く終わる人工的な非対称
    遅延を入れ、完了順を入力順の逆へ倒しても findings の順序が動かないことを
    見る。これで完了順に依存する実装 (as_completed) の帰属が決定的になる。
    """
    _init_repo(tmp_path)
    _commit(
        tmp_path,
        {
            provenance.POLICY_PATH: (
                "# policy\n"
                f"{provenance.IMPLEMENTATION_POLICY_NEEDLE}\n"
            ),
        },
        CODEX_AUTHOR,
    )
    for step in range(5):
        _commit(
            tmp_path, {f"tools/step{step}.py": f"STEP = {step}\n"},
            CLAUDE_AUTHOR,
        )
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    commits = _git(tmp_path, "rev-list", "--reverse", "HEAD").splitlines()
    expected = [
        f"{commit[:12]} change: 実装面に Codex role=author がない — "
        f"paths=tools/step{step}.py"
        for step, commit in enumerate(commits[1:])
    ]
    # 恒真化防止: 順序を観測できるだけの相異なる finding が実在すること。
    assert len(expected) == 5
    assert len(set(expected)) == 5

    real_audit = provenance._normal_commit_audit
    rank = {commit: n for n, commit in enumerate(commits)}

    def skewed(commit, **kwargs):
        # 先頭ほど遅く終わらせる = 完了順は入力順の逆になる。
        time.sleep(0.05 * (len(commits) - rank[commit]))
        return real_audit(commit, **kwargs)

    monkeypatch.setattr(
        provenance, "AUDIT_WORKERS", lambda count=len(commits): count,
    )
    monkeypatch.setattr(provenance, "_normal_commit_audit", skewed)
    audit = provenance._audit_history(list(commits))
    assert audit.findings == expected


def test_ancestry_bitset_matches_merge_base_oracle_for_every_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    """commit-date 順と topo 順が食い違う形を含む (--topo-order を外すと落ちる)。"""
    _init_repo(tmp_path)
    parent = _commit_dated(
        tmp_path, {"docs/parent.md": "p\n"}, CODEX_AUTHOR,
        "2020-01-10T00:00:00+00:00",
    )
    main_branch = _git(tmp_path, "branch", "--show-current")
    later_child = _commit_dated(
        tmp_path, {"docs/later.md": "l\n"}, CODEX_AUTHOR,
        "2020-01-05T00:00:00+00:00",
    )
    _git(tmp_path, "switch", "-q", "-c", "earlier", parent)
    earlier_child = _commit_dated(
        tmp_path, {"docs/earlier.md": "e\n"}, CODEX_AUTHOR,
        "2020-01-01T00:00:00+00:00",
    )
    _git(tmp_path, "switch", "-q", main_branch)
    _git(tmp_path, "merge", "--no-ff", "--no-commit", "earlier")
    merge = _commit_dated(
        tmp_path, {}, CODEX_AUTHOR, "2020-01-20T00:00:00+00:00",
    )
    _git(tmp_path, "switch", "-q", "--orphan", "other-root")
    other_root = _commit_dated(
        tmp_path, {"docs/other.md": "o\n"}, CODEX_AUTHOR,
        "2020-01-15T00:00:00+00:00",
    )
    _git(tmp_path, "switch", "-q", main_branch)

    monkeypatch.setattr(provenance, "REPO", tmp_path)
    selected = _git(
        tmp_path, "rev-list", "--reverse", main_branch,
    ).splitlines()
    everything = _git(tmp_path, "rev-list", "--reverse", "--all").splitlines()
    ancestry = provenance._build_ancestry(selected)
    for commit in selected:
        for ancestor in everything:
            assert ancestry.is_descendant(ancestor, commit) is (
                provenance._is_descendant(ancestor, commit)
            ), (ancestor, commit)
    assert ancestry.is_descendant(merge, merge)
    assert ancestry.is_descendant(parent, earlier_child)
    assert ancestry.is_descendant(later_child, merge)
    assert not ancestry.is_descendant(merge, parent)
    assert not ancestry.is_descendant(other_root, merge)


def test_ancestry_pickaxe_mask_matches_per_commit_oracle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    _init_repo(tmp_path)
    without_policy = _commit(
        tmp_path, {provenance.POLICY_PATH: "# legacy\n"}, CODEX_AUTHOR,
    )
    main_branch = _git(tmp_path, "branch", "--show-current")
    _commit(
        tmp_path,
        {
            provenance.POLICY_PATH: (
                f"{POLICY_NEEDLE_LITERAL}\n{POLICY_NEEDLE_LITERAL}\n"
            ),
        },
        CODEX_AUTHOR,
    )
    _commit(
        tmp_path,
        {provenance.POLICY_PATH: f"{POLICY_NEEDLE_LITERAL}\n"},
        CODEX_AUTHOR,
    )
    _git(tmp_path, "switch", "-q", "-c", "no-policy", without_policy)
    _commit(tmp_path, {"docs/side.md": "side\n"}, CODEX_AUTHOR)
    _git(tmp_path, "switch", "-q", main_branch)
    _git(tmp_path, "merge", "--no-ff", "--no-commit", "no-policy")
    _commit(tmp_path, {provenance.POLICY_PATH: "# dropped\n"}, CODEX_AUTHOR)
    _git(tmp_path, "mv", provenance.POLICY_PATH, "docs/moved-policy.md")
    _commit(tmp_path, {}, CODEX_AUTHOR)

    monkeypatch.setattr(provenance, "REPO", tmp_path)
    commits = _git(tmp_path, "rev-list", "--reverse", "--all").splitlines()
    ancestry = provenance._build_ancestry(commits)
    seeds = _git(
        tmp_path,
        "log", "--full-history", "--no-renames", "--format=%H",
        "-S", POLICY_NEEDLE_LITERAL, *commits, "--", provenance.POLICY_PATH,
    ).splitlines()
    observed = set()
    for commit in commits:
        lineage_oracle = any(
            provenance._is_descendant(seed, commit) for seed in seeds
        )
        assert ancestry.has_cab_policy(commit) is lineage_oracle, commit
        authoritative_oracle = bool(seeds) and (
            lineage_oracle
            or not any(
                provenance._is_descendant(commit, seed) for seed in seeds
            )
        )
        assert ancestry.has_cab_policy(
            commit, authoritative=True,
        ) is authoritative_oracle, commit
        observed.add(lineage_oracle)
    assert observed == {True, False}


def test_audit_history_empty_range_returns_zero_findings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    def refuse_git(*args, **kwargs):
        raise AssertionError("empty selected set must not touch git")

    monkeypatch.setattr(provenance, "_git", refuse_git)
    monkeypatch.setattr(provenance, "_build_ancestry", refuse_git)
    assert provenance._audit_history([]) == provenance.HistoryAudit([], [], [])
    monkeypatch.undo()

    _init_repo(tmp_path)
    commit = _commit(tmp_path, {"docs/empty.md": "empty\n"}, CODEX_AUTHOR)
    monkeypatch.setattr(provenance, "REPO", tmp_path)
    assert _run_range(monkeypatch, f"{commit}..{commit}") == 0
    captured = capsys.readouterr()
    assert captured.out == "check_ai_provenance: 0 件、違反なし\n"
    assert captured.err == ""


def test_audit_history_propagates_first_exception_in_input_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    commits, _, _ = _mixed_history(tmp_path, monkeypatch)
    real_audit = provenance._normal_commit_audit
    failing = {commits[2], commits[5]}

    def flaky(commit, **kwargs):
        if commit in failing:
            raise RuntimeError(f"synthetic audit failure {commit[:12]}")
        return real_audit(commit, **kwargs)

    monkeypatch.setattr(provenance, "AUDIT_WORKERS", lambda: 8)
    monkeypatch.setattr(provenance, "_normal_commit_audit", flaky)
    with pytest.raises(RuntimeError) as excinfo:
        provenance._audit_history(list(commits))
    assert f"synthetic audit failure {commits[2][:12]}" in str(excinfo.value)


def test_forward_correction_ancestry_still_uses_merge_base(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    """:634 の fail-closed が bitset 化で空洞になっていないことの証拠。"""
    history = _make_correction_history(tmp_path, monkeypatch)
    real_run = subprocess.run
    observed: list[tuple[str, ...]] = []

    def recording_run(command, **kwargs):
        if list(command[:3]) == ["git", "merge-base", "--is-ancestor"]:
            observed.append(tuple(command))
        return real_run(command, **kwargs)

    monkeypatch.setattr(provenance.subprocess, "run", recording_run)
    assert _run_range(
        monkeypatch, f"{history.target}^1..{history.correction}",
    ) == 0
    assert "forward-corrected=1" in capsys.readouterr().out
    assert any(command[3] == history.target for command in observed), observed


def _run() -> int:
    """parameterized path matrix を含む同一 node 集合を素の runner からも実行する。"""
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
