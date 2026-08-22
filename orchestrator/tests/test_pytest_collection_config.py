# -*- coding: utf-8 -*-
"""境界テスト: repo 直下 pytest.ini の収集契約と runner 起動形の非干渉。

背景は failures F41 の射程拡大 ([T-129])。repo に pytest 設定ファイルが 1 つも無いと
範囲指定なしの ``pytest`` が rootdir 以下を無指定収集し、ignored な生成物
(``output/s1-build-cache/`` の googletest 由来 ``*test*.py`` 等) を拾って
**赤の有無が checkout に依存する**。``testpaths`` / ``norecursedirs`` でこれを閉じる。

同時に、ini の ``addopts`` は **書いてはならない**。tools/run_tests.py の 5 ゲート
(``_is_full_suite`` / ``_has_no_execution_flag`` / ``_has_dispatch_exempt_flag`` /
``_has_bounded_scope_exempt_flag`` / ``_is_acceptance_run``) はいずれも環境変数
``PYTEST_ADDOPTS`` しか読まず ini を見ないため、
ini 側に選択オプションを置くと「全走のつもりで実は選択走」が preflight を素通りする (規律 2)。
本ファイルはその禁止を機械固定し、禁止が空虚でないこと (ini の addopts が実際に収集集合を
狭めること) を正例で示す。
"""
from __future__ import annotations

import configparser
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestrator import test_selection_contract as CONTRACT
from orchestrator.tests import conftest as CONF

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]
_INI = _REPO / "pytest.ini"

_RUNNER = _REPO / "tools" / "run_tests.py"
_SPEC = importlib.util.spec_from_file_location("run_tests_collection_config_test", _RUNNER)
assert _SPEC and _SPEC.loader
RT = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(RT)

# 設定ファイルが担う契約はこの 2 キーだけ。キーを増やす改訂は 5 ゲートに対する
# 再裁定を要するので、集合そのものを固定する。
_EXPECTED_INI_OPTIONS = {"testpaths", "norecursedirs"}
_POISON = "raise RuntimeError('poison module was collected')\n"
_GOOD_TEST = "def test_ok():\n    assert True\n"
_SORT_SWO_TEST = _REPO / "orchestrator" / "tests" / "test_sort_swo_oracle.py"
_SORT_SWO_IGNORE = f"--ignore={_SORT_SWO_TEST}"


def _patch_main_command_capture(monkeypatch):
    captured = {}
    monkeypatch.setenv("IZANAGI_TASK_RUN_AUTO_RECORD", "0")
    monkeypatch.setattr(RT, "_preflight_unstaged_deletions", lambda args, repo: 0)
    monkeypatch.setattr(RT, "_preflight_ruleops", lambda args, repo: 0)
    monkeypatch.setattr(RT, "_preflight_submodule", lambda args, repo: 0)
    monkeypatch.setattr(RT, "_ensure_xdist", lambda: False)
    monkeypatch.setattr(
        RT.subprocess,
        "call",
        lambda command, **kwargs: captured.update(
            command=command, kwargs=kwargs,
        ) or 0,
    )
    return captured


def _growth_hold_config(*argv: str):
    return SimpleNamespace(
        option=SimpleNamespace(numprocesses=None),
        args=(str(Path(CONF.__file__).resolve().parent),),
        invocation_params=SimpleNamespace(args=argv),
    )


def _read_ini(path: Path) -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    with path.open(encoding="utf-8") as handle:
        parser.read_file(handle)
    return parser


def _child_env() -> dict[str, str]:
    """親の選択オプションを子 pytest へ持ち込まない (計測でなく判定を汚すため)。"""
    env = dict(os.environ)
    for name in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTEST_DEBUG"):
        env.pop(name, None)
    env["NO_COLOR"] = "1"
    return env


def _collect(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable, "-m", "pytest", "--collect-only", "-q",
            "--color=no", "-p", "no:cacheprovider", *args,
        ],
        cwd=root,
        env={**_child_env(), "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        timeout=120,
    )


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _ini_without(token: str) -> str:
    """出荷 ini から norecursedirs の 1 要素だけを抜いた変異 ini 本文。"""
    parser = _read_ini(_INI)
    entries = parser["pytest"]["norecursedirs"].split()
    assert token in entries, (token, entries)
    entries.remove(token)
    return (
        "[pytest]\n"
        f"testpaths = {parser['pytest']['testpaths']}\n"
        f"norecursedirs = {' '.join(entries)}\n"
    )


def test_repo_pytest_ini_has_no_addopts_and_pins_testpaths():
    """唯一の破壊経路 (ini addopts) と収集範囲の要を機械固定する。"""
    assert _INI.is_file(), f"{_INI} が無い"
    parser = _read_ini(_INI)
    assert parser.sections() == ["pytest"], parser.sections()

    options = set(parser.options("pytest"))
    assert "addopts" not in options, (
        "pytest.ini に addopts を置いてはいけない — run_tests.py の 5 ゲートは "
        "PYTEST_ADDOPTS しか読まず、ini の選択オプションは preflight を素通りする"
    )
    assert options == _EXPECTED_INI_OPTIONS, (
        "pytest.ini のキー集合が変わった。増減は run_tests.py の 5 ゲート "
        "(_is_full_suite / _has_no_execution_flag / _has_dispatch_exempt_flag / "
        "_has_bounded_scope_exempt_flag / _is_acceptance_run) への影響を"
        f"再裁定してから行う: {sorted(options)}"
    )

    assert parser["pytest"]["testpaths"] == "orchestrator/tests"
    norecursedirs = parser["pytest"]["norecursedirs"].split()
    assert ".*" in norecursedirs, (
        ".* を落とすと .claude/worktrees/ 等が収集対象へ戻る"
    )
    assert "output" in norecursedirs, (
        "output を落とすと ignored な生成物 (F41) が収集対象へ戻る"
    )
    assert "external" in norecursedirs, (
        "external を落とすと第三者 submodule (CCBench) が収集対象へ戻る"
    )


_NORECURSE_PROBE = (
    "def pytest_configure(config):\n"
    "    print('CONFIGFILE ' + str(config.inipath))\n"
    "    print('NORECURSEDIRS ' + ' '.join(config.getini('norecursedirs')))\n"
)


def test_pytest_ini_norecursedirs_restates_the_installed_pytest_defaults(
    tmp_path: Path,
):
    """norecursedirs は既定を置換する。既定の再掲漏れを実 pytest から検出する。"""
    parser = _read_ini(_INI)
    entries = parser["pytest"]["norecursedirs"].split()

    # 設定ファイルの無い空 dir で config.getini を読み、導入済み pytest の既定値を得る。
    probe_root = tmp_path / "probe"
    _write(probe_root / "norecurse_probe.py", _NORECURSE_PROBE)
    probe = _collect(probe_root, "-p", "norecurse_probe")
    assert probe.returncode in (0, 5), probe.stdout + probe.stderr
    # probe が祖先の設定ファイルを拾っていたら「既定」ではない。fail-closed にする。
    assert "CONFIGFILE None" in probe.stdout, (
        "probe が設定ファイルを読んでおり既定値になっていない: " + probe.stdout
    )
    lines = [
        line for line in probe.stdout.splitlines()
        if line.startswith("NORECURSEDIRS ")
    ]
    assert len(lines) == 1, probe.stdout
    installed_defaults = lines[0].split()[1:]
    assert installed_defaults, probe.stdout

    missing = [item for item in installed_defaults if item not in entries]
    assert not missing, (
        "pytest 既定の norecursedirs エントリが再掲されていない "
        f"(既定は置換されるため収集面が広がる): {missing}"
    )
    added = [item for item in entries if item not in installed_defaults]
    assert set(added) == {"output", "external"}, (
        "既定への追加は output / external だけを意図している: " + str(added)
    )


def test_bare_pytest_collection_is_scoped_by_testpaths(tmp_path: Path):
    """正例: 範囲指定なしの pytest が testpaths で閉じ、ini を消すと赤になる。"""
    root = tmp_path / "repo"
    _write(root / "orchestrator" / "tests" / "test_ok.py", _GOOD_TEST)
    # 毒は repo 直下に置く。output/ 配下だと norecursedirs の output にも当たり、
    # testpaths を消しても緑のままになって本テストが検出力を失う (段 4 裁定 B3)。
    _write(root / "poison_test.py", _POISON)
    shutil.copyfile(_INI, root / "pytest.ini")

    scoped = _collect(root)
    assert scoped.returncode == 0, scoped.stdout + scoped.stderr
    assert "test_ok" in scoped.stdout, scoped.stdout
    assert "poison_test" not in scoped.stdout + scoped.stderr

    (root / "pytest.ini").unlink()
    unscoped = _collect(root)
    assert unscoped.returncode != 0, (
        "ini を外しても緑なら、この正例は testpaths の欠落を検出できていない: "
        + unscoped.stdout + unscoped.stderr
    )
    assert "poison_test" in unscoped.stdout + unscoped.stderr


def test_norecursedirs_excludes_generated_hidden_and_vendor_trees(tmp_path: Path):
    """明示 dir 指定 (testpaths を迂回する形) では norecursedirs だけが防壁になる。"""
    root = tmp_path / "repo"
    _write(root / "orchestrator" / "tests" / "test_ok.py", _GOOD_TEST)
    _write(root / "output" / "s1-build-cache" / "x" / "gtest_test.py", _POISON)
    _write(root / ".hiddenpoison" / "hidden_test.py", _POISON)
    _write(root / "external" / "vendor" / "vendor_test.py", _POISON)
    ini = root / "pytest.ini"
    shutil.copyfile(_INI, ini)

    scoped = _collect(root, ".")
    assert scoped.returncode == 0, scoped.stdout + scoped.stderr
    assert "test_ok" in scoped.stdout, scoped.stdout

    # 各エントリの positive control: 1 要素抜くと対応する毒が収集されて赤になる。
    for token, needle in (
        ("output", "gtest_test"),
        (".*", "hidden_test"),
        ("external", "vendor_test"),
    ):
        ini.write_text(_ini_without(token), encoding="utf-8")
        weakened = _collect(root, ".")
        combined = weakened.stdout + weakened.stderr
        assert weakened.returncode != 0, (
            f"norecursedirs から {token} を抜いても緑 — この防壁は空虚: {combined}"
        )
        assert needle in combined, (token, combined)


def test_ini_addopts_narrows_collection_while_runner_gates_stay_blind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    """禁止が空虚でないことの正例 + 環境変数側ゲートの positive control。"""
    root = tmp_path / "repo"
    _write(root / "orchestrator" / "tests" / "test_ok.py", _GOOD_TEST)
    (root / "pytest.ini").write_text(
        "[pytest]\ntestpaths = orchestrator/tests\n", encoding="utf-8",
    )
    baseline = _collect(root)
    assert baseline.returncode == 0, baseline.stdout + baseline.stderr
    assert "test_ok" in baseline.stdout

    (root / "pytest.ini").write_text(
        "[pytest]\ntestpaths = orchestrator/tests\naddopts = -k nothing_matches\n",
        encoding="utf-8",
    )
    narrowed = _collect(root)
    assert narrowed.returncode != 0, (
        "ini の addopts が収集集合を変えないなら禁止の根拠が無い: "
        + narrowed.stdout + narrowed.stderr
    )
    assert "deselected" in narrowed.stdout + narrowed.stderr

    # ゲートが見張るのは環境変数の軸だけ。ini 軸は構造的に見えない。
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    assert RT._is_full_suite([]) is True
    assert RT._is_acceptance_run([RT._DEFAULT_TARGET]) is True
    monkeypatch.setenv("PYTEST_ADDOPTS", "-k nothing_matches")
    assert RT._is_full_suite([]) is False
    assert RT._is_acceptance_run([RT._DEFAULT_TARGET]) is False


def test_runner_default_target_survives_ini(monkeypatch: pytest.MonkeyPatch):
    """runner 経路は常に明示 target を渡すので testpaths は発火しない。"""
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    command = RT._build_pytest_command(
        [], use_xdist=False, default_nproc=1, has_target=False,
    )
    assert RT._DEFAULT_TARGET in command, command
    assert command[-1] == RT._DEFAULT_TARGET, command
    assert RT._is_acceptance_run([RT._DEFAULT_TARGET]) is True
    assert RT._is_full_suite([]) is True
    assert RT._has_no_execution_flag([]) is False
    assert RT._has_dispatch_exempt_flag([]) is False
    assert RT._has_bounded_scope_exempt_flag([]) is False


def test_permanent_exclusion_table_is_exact_and_target_remains_a_file():
    entries = RT._PERMANENT_FULL_SUITE_EXCLUSIONS
    assert len(entries) in (0, 1)
    assert all(
        str(CONTRACT.normalize_path(entry.path))
        == str(RT._SANCTIONED_SORT_SWO_ORACLE_PATH)
        for entry in entries
    )
    if entries:
        assert {str(CONTRACT.normalize_path(entry.path)) for entry in entries} == {
            str(RT._SANCTIONED_SORT_SWO_ORACLE_PATH),
        }
    assert _SORT_SWO_TEST.is_file()
    assert not _SORT_SWO_TEST.is_symlink()


def test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests():
    entries = RT._PERMANENT_FULL_SUITE_EXCLUSIONS
    test_paths = {CONTRACT.normalize_path(entry.path) for entry in entries}
    forbidden_siblings = {
        path
        for path in (_REPO / "orchestrator" / "tests").glob("test_*.py")
        if CONTRACT.normalize_path(path) != CONTRACT.normalize_path(_SORT_SWO_TEST)
        and any(word in path.stem.lower() for word in ("verifier", "oracle"))
    }
    assert test_paths.isdisjoint(forbidden_siblings)
    assert test_paths <= {CONTRACT.normalize_path(_SORT_SWO_TEST)}
    if entries:
        assert test_paths == {CONTRACT.normalize_path(_SORT_SWO_TEST)}


def test_permanent_exclusion_metadata_and_version_are_nonempty():
    assert RT._PERMANENT_EXCLUSION_SET_VERSION.strip()
    for entry in RT._PERMANENT_FULL_SUITE_EXCLUSIONS:
        assert entry.ruling.strip()
        assert entry.reason.strip()
        assert entry.release_condition.strip()


def test_selection_contract_normalizes_and_serializes_all_metadata(tmp_path: Path):
    target = tmp_path / "selected.py"
    target.write_text("# target\n", encoding="utf-8")
    entry = CONTRACT.Exclusion(
        path=target,
        reason="reason",
        release_condition="release",
        ruling="ruling",
        set_version=CONTRACT.EXCLUSION_SET_VERSION,
    )

    serialized = CONTRACT.serialize_payload((entry,))
    payload = json.loads(serialized)
    assert payload == [{
        "path": str(CONTRACT.normalize_path(target)),
        "reason": entry.reason,
        "release_condition": entry.release_condition,
        "ruling": entry.ruling,
        "set_version": entry.set_version,
    }]
    assert CONTRACT.exclusion_tokens((entry,)) == (
        f"--ignore={CONTRACT.normalize_path(target)}",
    )
    assert CONTRACT.selection_receipt_line((entry,)) == (
        CONTRACT.SELECTION_RECEIPT_PREFIX
        + json.dumps(payload[0], ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    )


@pytest.mark.parametrize(
    ("args", "acceptance_shape"),
    [
        ([], True),
        (["-q"], True),
        ([RT._DEFAULT_TARGET], True),
        (["-k", "test_sort_swo_oracle"], False),
        (["--collect-only"], False),
        (["--deselect=ignored.py::test_node"], False),
        ([str(_SORT_SWO_TEST)], False),
    ],
    ids=(
        "bare-acceptance", "quiet-acceptance", "explicit-default-target",
        "selector", "collect-only", "deselect", "explicit-file-target",
    ),
)
@pytest.mark.parametrize(
    "table_active",
    [True, False],
    ids=("active-table", "empty-table"),
)
def test_main_only_injects_exclusion_for_acceptance_shapes(
    monkeypatch: pytest.MonkeyPatch, args, acceptance_shape, table_active,
):
    monkeypatch.setattr(
        RT,
        "_PERMANENT_FULL_SUITE_EXCLUSIONS",
        CONTRACT.SANCTIONED_EXCLUSIONS if table_active else (),
    )
    captured = _patch_main_command_capture(monkeypatch)
    assert RT.main(args, site=RT.site_policy.OTHER) == 0
    command = captured["command"]
    excluded = acceptance_shape and table_active
    assert (_SORT_SWO_IGNORE in command) is excluded
    if excluded:
        assert command.index(_SORT_SWO_IGNORE) < command.index(RT._DEFAULT_TARGET)
        assert command.count(RT._DEFAULT_TARGET) == 1
    else:
        assert _SORT_SWO_IGNORE not in command


@pytest.mark.parametrize("field", [
    "reason", "release_condition", "ruling", "set_version",
])
def test_runner_rejects_contract_metadata_drift(
    monkeypatch: pytest.MonkeyPatch, field: str,
):
    base = CONTRACT.SANCTIONED_EXCLUSIONS[0]
    drifted = replace(base, **{field: getattr(base, field) + " drift"})
    monkeypatch.setattr(RT, "_PERMANENT_FULL_SUITE_EXCLUSIONS", (drifted,))
    assert RT.main(["-q"], site=RT.site_policy.OTHER) == (
        RT._PERMANENT_EXCLUSION_GATE_RC
    )


def test_empty_exclusion_table_restores_the_prechange_default_command(
    monkeypatch: pytest.MonkeyPatch,
):
    captured = _patch_main_command_capture(monkeypatch)
    monkeypatch.setattr(RT, "_PERMANENT_FULL_SUITE_EXCLUSIONS", ())
    assert RT.main(["-q"], site=RT.site_policy.OTHER) == 0
    assert captured["command"] == [
        sys.executable, "-m", "pytest", RT._DEFAULT_TARGET, "-q",
    ]
    assert _SORT_SWO_IGNORE not in captured["command"]


def test_runtime_rejects_foreign_path_and_accepts_sanctioned_positive(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
):
    captured = _patch_main_command_capture(monkeypatch)
    build_calls = []
    real_build = RT._build_pytest_command
    monkeypatch.setattr(
        RT,
        "_build_pytest_command",
        lambda *args, **kwargs: build_calls.append((args, kwargs))
        or real_build(*args, **kwargs),
    )
    foreign = RT._PermanentExclusion(
        path=_REPO / "orchestrator" / "tests" / "test_pytest_collection_config.py",
        ruling="{{D:foreign}}",
        reason="foreign",
        release_condition="foreign release",
    )
    original = RT._PERMANENT_FULL_SUITE_EXCLUSIONS
    monkeypatch.setattr(RT, "_PERMANENT_FULL_SUITE_EXCLUSIONS", (foreign,))
    assert RT.main(["-q"], site=RT.site_policy.OTHER) == (
        RT._PERMANENT_EXCLUSION_GATE_RC
    )
    assert "command を作らず停止" in capsys.readouterr().err
    assert "command" not in captured
    assert build_calls == []

    monkeypatch.setattr(RT, "_PERMANENT_FULL_SUITE_EXCLUSIONS", original)
    assert RT.main(["-q"], site=RT.site_policy.OTHER) == 0
    assert (_SORT_SWO_IGNORE in captured["command"]) is bool(original)
    assert len(build_calls) == 1


@pytest.mark.parametrize(
    "table_active",
    [True, False],
    ids=("active-table", "empty-table"),
)
def test_runner_owned_exclusion_is_non_silent(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    table_active,
):
    monkeypatch.setattr(
        RT,
        "_PERMANENT_FULL_SUITE_EXCLUSIONS",
        CONTRACT.SANCTIONED_EXCLUSIONS if table_active else (),
    )
    config = _growth_hold_config(_SORT_SWO_IGNORE if table_active else "")
    if not table_active:
        config.invocation_params.args = ()
    monkeypatch.setattr(CONF, "_configure_receipt_memo_session", lambda _: None)
    monkeypatch.setattr(CONF, "_configure_oracle_environment_memo_session", lambda _: None)
    monkeypatch.setattr(CONF, "_configure_receipt_memo_run_id", lambda _: None)
    monkeypatch.setattr(CONF, "_growth_holds_opted_in", lambda: False)
    monkeypatch.setattr(CONF, "mark_pytest_session_enforcing", None)
    with RT._runner_exclusion_environment(RT._PERMANENT_FULL_SUITE_EXCLUSIONS):
        CONF.pytest_configure(config)
    lines = capsys.readouterr().err.splitlines()
    assert len(lines) == int(table_active)
    if table_active:
        assert lines[0].startswith(CONF._SELECTION_RECEIPT_PREFIX)
        payload = json.loads(lines[0][len(CONF._SELECTION_RECEIPT_PREFIX):])
        assert payload == CONF._SANCTIONED_EXCLUSION_PAYLOAD


@pytest.mark.parametrize("mismatch", ["payload", "token"])
def test_conftest_rejects_present_runner_env_drift(
    monkeypatch: pytest.MonkeyPatch, mismatch: str,
):
    config = _growth_hold_config(_SORT_SWO_IGNORE)
    with RT._runner_exclusion_environment(CONTRACT.SANCTIONED_EXCLUSIONS):
        if mismatch == "payload":
            payload = CONTRACT.payload_entries(CONTRACT.SANCTIONED_EXCLUSIONS)
            payload[0]["reason"] += " drift"
            monkeypatch.setenv(CONF._RUNNER_EXCLUSION_ENV, json.dumps(payload))
        else:
            config.invocation_params.args = ("--ignore=/not-sanctioned.py",)
        with pytest.raises(pytest.UsageError, match="runner exclusion"):
            CONF.pytest_configure(config)


def test_inherited_runner_env_without_narrowing_token_is_not_runner_owned(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
):
    config = _growth_hold_config()
    monkeypatch.setattr(CONF, "_configure_receipt_memo_session", lambda _: None)
    monkeypatch.setattr(CONF, "_configure_oracle_environment_memo_session", lambda _: None)
    monkeypatch.setattr(CONF, "_configure_receipt_memo_run_id", lambda _: None)
    monkeypatch.setattr(CONF, "_growth_holds_opted_in", lambda: False)
    monkeypatch.setattr(CONF, "mark_pytest_session_enforcing", None)
    with RT._runner_exclusion_environment(CONTRACT.SANCTIONED_EXCLUSIONS):
        CONF.pytest_configure(config)
        assert CONF._runner_owned_exclusion_payload(config) is None
        assert CONF._is_complete_growth_hold_collection(config) is True
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize(
    "table_active",
    [True, False],
    ids=("active-table", "empty-table"),
)
def test_sanctioned_runner_ignore_keeps_growth_hold_completeness_guard(
    monkeypatch: pytest.MonkeyPatch,
    table_active,
):
    monkeypatch.setattr(
        RT,
        "_PERMANENT_FULL_SUITE_EXCLUSIONS",
        CONTRACT.SANCTIONED_EXCLUSIONS if table_active else (),
    )
    monkeypatch.delenv(CONF.RUN_GROWTH_HELD_TESTS_ENV, raising=False)
    monkeypatch.setattr(
        CONF, "GROWTH_TEST_HOLDS", {"missing.py::test_missing": object()},
    )
    config = _growth_hold_config(_SORT_SWO_IGNORE if table_active else "")
    if not table_active:
        config.invocation_params.args = ()
    with RT._runner_exclusion_environment(RT._PERMANENT_FULL_SUITE_EXCLUSIONS):
        assert CONF._is_complete_growth_hold_collection(config) is True
        with pytest.raises(pytest.UsageError, match="growth-test hold keys missing"):
            list(CONF.pytest_collection_modifyitems(config, []))


@pytest.mark.parametrize(
    "token",
    ["--ignore=/user/selected.py", "--ignore-glob=*_generated.py", "--pyargs"],
)
def test_user_collection_narrowing_still_disables_growth_hold_completeness_guard(
    monkeypatch: pytest.MonkeyPatch, token,
):
    monkeypatch.delenv(CONF._RUNNER_EXCLUSION_ENV, raising=False)
    config = _growth_hold_config(token)
    assert CONF._is_complete_growth_hold_collection(config) is False


@pytest.mark.parametrize(
    "args",
    [
        ["--deselect=ignored.py::test_node"],
        ["--ignore=/user/selected.py"],
        ["--ignore-glob=*_generated.py"],
        ["--pyargs"],
    ],
)
def test_user_selection_options_remain_nonacceptance(args):
    assert RT._is_full_suite(args) is False
    assert RT._is_acceptance_run(args) is False


def test_explicit_sort_swo_target_still_collects_without_runner_ignore():
    result = _collect(_REPO, str(_SORT_SWO_TEST))
    combined = result.stdout + result.stderr
    assert result.returncode == 0, combined
    assert "test_cpp_e2e_clean_generic_lambda_positive" in result.stdout


@pytest.mark.parametrize(
    "relative",
    [
        "orchestrator/campaign/s1_direct_comparison.py",
        "orchestrator/campaign/p3_s4_loop_sort.py",
    ],
)
def test_s1_and_p3_s4_callers_still_reference_sort_swo_checker(relative):
    source = (_REPO / relative).read_text(encoding="utf-8")
    assert "from .sort_swo_oracle import" in source
    assert source.count("check_materialized_sort_swo") >= 2


def test_ini_testpaths_and_runner_default_target_point_at_the_same_tree():
    """ini と runner の既定範囲が乖離しないことを固定する。"""
    parser = _read_ini(_INI)
    from_ini = (_REPO / parser["pytest"]["testpaths"]).resolve()
    assert from_ini == Path(RT._DEFAULT_TARGET).resolve()


def test_conftest_scheduler_attestation_loads_without_xdist(tmp_path: Path):
    """xdist が import 不能でも serial controller の collection は壊れない。"""
    sample = tmp_path / "test_serial_sample.py"
    _write(sample, _GOOD_TEST)
    _write(
        tmp_path / "xdist.py",
        "raise RuntimeError('xdist must not be imported for serial run')\n",
    )
    env = _child_env()
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    env["PYTHONPATH"] = os.pathsep.join((str(tmp_path), str(_REPO)))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "orchestrator.tests.conftest",
            str(sample),
        ],
        cwd=_REPO,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    marker = 'IZANAGI_EFFECTIVE_SCHEDULER_V1 {"effective_scheduler":"serial"}'
    assert result.stdout.splitlines().count(marker) == 1
    assert result.stdout.splitlines()[-1] == marker


def _run() -> int:
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
