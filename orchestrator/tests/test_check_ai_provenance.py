"""AI provenance の Codex-first 実装面 gate。"""
from __future__ import annotations

import sys
import subprocess
from pathlib import Path

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


def _run() -> int:
    """parameterized path matrix を含む同一 node 集合を素の runner からも実行する。"""
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
