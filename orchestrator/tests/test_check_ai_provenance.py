"""AI provenance の Codex-first 実装面 gate。"""
from __future__ import annotations

import sys
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

import check_ai_provenance as provenance  # noqa: E402


POLICY_NEEDLE_LITERAL = (
    "Co-Authored-By 候補行はすべて最終 trailer block に置く"
)
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
    return provenance.main()


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
    ],
)
def test_implementation_path_contract(path: str, expected: bool):
    assert provenance._is_implementation_path(path) is expected


def test_claude_only_author_is_rejected_for_implementation_positive_control():
    findings = provenance.validate_implementation_author(
        "candidate", CLAUDE_AUTHOR, ["tools/checker.py"],
    )
    assert findings == [
        "candidate: 実装面に Codex role=author がない — paths=tools/checker.py"
    ]


def test_codex_author_and_nonimplementation_changes_are_accepted():
    assert provenance.validate_implementation_author(
        "candidate", CODEX_AUTHOR, ["tools/checker.py"],
    ) == []
    assert provenance.validate_implementation_author(
        "candidate", CLAUDE_AUTHOR, ["docs/worklog.md"],
    ) == []


def test_human_only_implementation_is_not_misattributed_to_codex():
    assert provenance.validate_implementation_author(
        "candidate", "change\n\nAI-Agent: none\n", ["tools/checker.py"],
    ) == []


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
    assert provenance.main() == 1
    captured = capsys.readouterr()
    assert "実装面に Codex role=author がない — paths=tools/new.py" in captured.err


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
    assert provenance.main() == 1
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
    assert provenance.main() == 0
    assert "違反なし" in capsys.readouterr().out

    monkeypatch.setattr(
        sys, "argv",
        ["check_ai_provenance.py", "--range", f"{epoch}..{violating}"],
    )
    assert provenance.main() == 1
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
    assert provenance.main() == 0
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
    assert provenance.main() == 2
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
    assert provenance.main() == 1
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
    assert provenance.main() == 1
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
    assert provenance.main() == 1
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
    assert provenance.main() == 2
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
    assert provenance.main() == 1
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
    assert provenance.main() == 0
    assert "違反なし" in capsys.readouterr().out

    merge = _commit(tmp_path, {}, CLAUDE_AUTHOR)
    assert provenance._commit_paths(merge) == []
    audit = provenance._normal_commit_audit(
        merge,
        scope_epoch=base,
        implementation_epoch=base,
    )
    assert audit.normal_findings == ()


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
    assert provenance.main() == 1
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
        f"{audit.label}: 実装面に Codex role=author がない — "
        "paths=tools/resolution.py",
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
    assert provenance.main() == 2
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
    assert provenance.main() == 2
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
    assert provenance.main() == 1
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
    assert provenance.main() == 2
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
    assert provenance.main() == 0
    assert "違反なし" in capsys.readouterr().out


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
        f"{audit.label}: AI-Agent trailer がない",
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
    forward_order_findings, forward_order_records = provenance._audit_history(
        [history.target, history.correction]
    )
    reverse_order_findings, reverse_order_records = provenance._audit_history(
        [history.correction, history.target]
    )
    assert forward_order_findings == reverse_order_findings == []
    assert forward_order_records == reverse_order_records == [forward]


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
    assert provenance.main() == 0
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
    assert provenance.main() == 1
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
    assert provenance.main() == 1
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
    assert provenance.main() == 1
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
    assert provenance.main() == 1
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
    assert provenance.main() == 2
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
    assert provenance.main() == 0
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


def _run() -> int:
    """parameterized path matrix を含む同一 node 集合を素の runner からも実行する。"""
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
