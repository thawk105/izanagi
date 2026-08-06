# -*- coding: utf-8 -*-
"""Pegasus execution queue 状態 leaf のテスト。"""

import ast
from pathlib import Path
import subprocess
import sys
from unittest import mock


_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))

from orchestrator.campaign import queue_state as QS  # noqa: E402


QSTAT_OUTPUT = """\
[EXECUTION QUEUE] Batch Server Host: nqsv
=========================================
QueueName       SCH JSVs ENA STS  PRI  TOT ARR WAI QUE PRR RUN POR EXT HLD HOL SUS MIG STG
--------------- --- ---- ------- ---- ----------------------------------------------------
gen_L             1  148 ENA ACT   30    0   0   0   0   0   0   0   0   0   0   0   0   0
gen_M             1  148 ENA ACT   30    0   0   0   0   0   0   0   0   0   0   0   0   0
gen_S             1  148 ENA ACT   30  163   0   0  95   0  68   0   0   0   0   0   0   0
--------------- --- ---- ------- ---- ----------------------------------------------------
 <TOTAL>                               163   0   0  95   0  68   0   0   0   0   0   0   0
--------------- --- ---- ------- ---- ----------------------------------------------------

[INTERACTIVE QUEUE] Batch Server Host: nqsv
QueueName       SCH JSVs ENA STS  PRI  TOT ARR WAI QUE PRR RUN POR EXT HLD HOL SUS MIG STG
interactive       1  148 ENA ACT   30    1   0   0   0   0   1   0   0   0   0   0   0   0
"""


def _runner(stdout, *, returncode=0):
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, returncode, stdout, "")

    run.calls = calls
    return run


def _replace_target_state(ena, sts):
    return QSTAT_OUTPUT.replace(
        "gen_S             1  148 ENA ACT",
        f"gen_S             1  148 {ena} {sts}",
    )


def test_real_qstat_output_reads_default_queue_counts_and_raw_line():
    runner = _runner(QSTAT_OUTPUT)
    state = QS.queue_state(runner=runner)

    assert state is not None
    assert state.queue == "gen_S"
    assert state.enabled is True
    assert state.active is True
    assert state.available is True
    assert state.queued == 95
    assert state.running == 68
    assert "gen_S" in state.raw_line
    assert len(runner.calls) == 1
    command, kwargs = runner.calls[0]
    assert command == ["qstat", "-Q"]
    assert kwargs["timeout"] == QS.QSTAT_TIMEOUT_S


def test_dis_act_is_unavailable():
    possible, reason = QS.dispatch_possible(
        runner=_runner(_replace_target_state("DIS", "ACT"))
    )
    assert possible is False
    assert "ENA=DIS" in reason
    assert "STS=ACT" in reason


def test_ena_ina_is_unavailable():
    possible, reason = QS.dispatch_possible(
        runner=_runner(_replace_target_state("ENA", "INA"))
    )
    assert possible is False
    assert "ENA=ENA" in reason
    assert "STS=INA" in reason


def test_dis_ina_is_unavailable():
    possible, reason = QS.dispatch_possible(
        runner=_runner(_replace_target_state("DIS", "INA"))
    )
    assert possible is False
    assert "ENA=DIS" in reason
    assert "STS=INA" in reason


def test_missing_target_is_unknown_and_treated_as_available():
    output = QSTAT_OUTPUT.replace("gen_S", "other_queue")
    assert QS.queue_state(runner=_runner(output)) is None
    possible, reason = QS.dispatch_possible(runner=_runner(output))
    assert possible is True
    assert "観測不能" in reason


def test_nonzero_timeout_missing_command_empty_and_broken_are_unknown():
    runners = [
        _runner(QSTAT_OUTPUT, returncode=1),
        mock.Mock(side_effect=subprocess.TimeoutExpired(["qstat", "-Q"], 1)),
        mock.Mock(side_effect=FileNotFoundError("qstat")),
        _runner(""),
        _runner(
            "[EXECUTION QUEUE] Batch Server Host: nqsv\n"
            "QueueName ENA STS QUE RUN\n"
            "gen_S ENA ACT broken 68\n"
        ),
    ]
    for runner in runners:
        assert QS.queue_state(runner=runner) is None
        possible, reason = QS.dispatch_possible(runner=runner)
        assert possible is True
        assert "観測不能" in reason


def test_same_name_in_interactive_table_is_not_execution_queue():
    output = """\
[EXECUTION QUEUE] Batch Server Host: nqsv
QueueName SCH JSVs ENA STS PRI TOT ARR WAI QUE PRR RUN
other       1 148 ENA ACT 30 0 0 0 0 0 0
[INTERACTIVE QUEUE] Batch Server Host: nqsv
QueueName SCH JSVs ENA STS PRI TOT ARR WAI QUE PRR RUN
gen_S       1 148 ENA ACT 30 9 0 0 7 0 2
"""
    assert QS.queue_state(runner=_runner(output)) is None


def test_total_and_separator_are_never_treated_as_queue_rows():
    assert QS.queue_state("<TOTAL>", runner=_runner(QSTAT_OUTPUT)) is None
    assert QS.queue_state("---------------", runner=_runner(QSTAT_OUTPUT)) is None


def test_default_queue_has_one_source_of_truth_in_dispatch_compute():
    source_path = _REPO / "orchestrator" / "campaign" / "queue_state.py"
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    string_literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert "gen_S" not in string_literals
    imports = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "tools.pegasus.dispatch_compute"
    ]
    assert len(imports) == 1
    assert [alias.name for alias in imports[0].names] == ["DEFAULT_QUEUE"]
    assert any(isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef))
               and imports[0] in ast.walk(parent)
               for parent in ast.walk(tree))


def test_dispatch_reason_contains_queue_state_and_counts():
    possible, reason = QS.dispatch_possible(runner=_runner(QSTAT_OUTPUT))
    assert possible is True
    for expected in ("gen_S", "ENA=ENA", "STS=ACT", "待ち数=95", "実行数=68"):
        assert expected in reason


def test_main_uses_dispatch_possible_and_maps_exit_status():
    with mock.patch.object(
        QS,
        "dispatch_possible",
        return_value=(False, "キュー fixture は利用できません。"),
    ) as dispatch, mock.patch("builtins.print") as output:
        assert QS.main() == 1
    output.assert_called_once_with("キュー fixture は利用できません。")
    dispatch.assert_called_once_with()

    for reason in (
        "キュー fixture は利用できます。",
        "キュー fixture は観測不能のため可用扱いです。",
    ):
        with mock.patch.object(
            QS,
            "dispatch_possible",
            return_value=(True, reason),
        ), mock.patch("builtins.print") as output:
            assert QS.main() == 0
        output.assert_called_once_with(reason)


def _run():
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
            passed += 1
        except AssertionError as exc:
            print(f"FAIL {test.__name__}: {exc}")
            failed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run())
