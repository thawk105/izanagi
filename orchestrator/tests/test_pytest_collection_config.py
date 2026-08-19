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
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

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
