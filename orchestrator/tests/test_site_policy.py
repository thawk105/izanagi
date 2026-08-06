# -*- coding: utf-8 -*-
"""Pegasus site policy の分類・並列度・拒否境界テスト。

pytest と ``python3 orchestrator/tests/test_site_policy.py`` の両方で走る。
"""

import ast
import os
from pathlib import Path
import sys
import tempfile
from unittest import mock


_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO))

from orchestrator.campaign import site_policy as SP  # noqa: E402


def test_public_states_are_four_distinct_strings():
    states = (
        SP.OTHER,
        SP.PEGASUS_LOGIN,
        SP.PEGASUS_COMPUTE,
        SP.PEGASUS_SUSPECT,
    )
    assert all(type(state) is str for state in states)
    assert len(set(states)) == 4


def test_login_fallback_regex_and_classifier_are_mechanically_consistent():
    """M1: LOGIN 枝を OTHER に落とす変異を kill する regex 整合メタテスト。"""
    assert SP.LOGIN_FALLBACK_RE.pattern == r"^pegasus0[1-9]$"
    candidates = [f"pegasus{number:02d}" for number in range(100)]
    matched = [
        hostname
        for hostname in candidates
        if SP.LOGIN_FALLBACK_RE.fullmatch(hostname)
    ]
    assert matched == [f"pegasus0{number}" for number in range(1, 10)]
    for hostname in matched:
        assert SP.classify_site(hostname, {}, True) == SP.PEGASUS_LOGIN


def test_login_requires_both_nqsv_markers_and_normalizes_hostname():
    """M1: site 証拠のある login だけを LOGIN とする枝を固定する。"""
    assert (
        SP.classify_site("PEGASUS02.CCS.EXAMPLE.", {}, True)
        == SP.PEGASUS_LOGIN
    )
    assert (
        SP.classify_site("pegasus02.example.invalid", {}, False)
        == SP.OTHER
    )
    assert SP.classify_site("pegasus04", {}, True) == SP.PEGASUS_LOGIN
    assert SP.classify_site("pegasus04", {}, False) == SP.OTHER


def test_compute_is_bnode_digits_regardless_of_nqsv_or_pbs_jobid():
    assert (
        SP.classify_site("bnode123.other.example", {}, False)
        == SP.PEGASUS_COMPUTE
    )
    assert (
        SP.classify_site("bnode114", {}, False)
        == SP.PEGASUS_COMPUTE
    )
    assert (
        SP.classify_site(
            "bnode114",
            {"PBS_JOBID": "873225.nqsv"},
            False,
        )
        == SP.PEGASUS_COMPUTE
    )
    assert SP.classify_site("bnode", {"PBS_JOBID": "0:1.nqsv"}, True) == SP.OTHER
    assert (
        SP.classify_site("bnodeABC", {"PBS_JOBID": "0:1.nqsv"}, True)
        == SP.OTHER
    )


def test_pegasus_unknown_names_are_suspect_only_with_site_evidence():
    """M4: SUSPECT を重い処理の拒否集合から外す変異の分類側 positive control。"""
    for hostname in ("pegasus", "pegasus10", "pegasus-next.example"):
        assert (
            SP.classify_site(hostname, {}, True)
            == SP.PEGASUS_SUSPECT
        )
        assert SP.classify_site(hostname, {}, False) == SP.OTHER


def test_current_site_hostname_exception_uses_nqsv_evidence():
    """M4: hostname 取得例外でも NQSV 証拠があれば SUSPECT として閉じる。"""
    with mock.patch.object(
        SP.socket,
        "gethostname",
        side_effect=OSError("hostname unavailable"),
    ), mock.patch.object(
        SP.shutil,
        "which",
        side_effect=lambda name: f"/fixture/{name}",
    ):
        assert SP.current_site() == SP.PEGASUS_SUSPECT

    with mock.patch.object(
        SP.socket,
        "gethostname",
        side_effect=RuntimeError("resolver failed"),
    ), mock.patch.object(
        SP.shutil,
        "which",
        return_value=None,
    ), mock.patch.object(SP.os.path, "isdir", return_value=False):
        assert SP.current_site() == SP.OTHER


def test_current_site_requires_qsub_and_qstat_together():
    def classify_with(markers):
        with mock.patch.object(
            SP.socket,
            "gethostname",
            return_value="pegasus02",
        ), mock.patch.object(
            SP.shutil,
            "which",
            side_effect=lambda name: markers.get(name),
        ), mock.patch.object(
            SP.os.path,
            "isdir",
            return_value=False,
        ):
            return SP.current_site()

    assert classify_with({"qsub": "/bin/qsub", "qstat": "/bin/qstat"}) == (
        SP.PEGASUS_LOGIN
    )
    assert classify_with({"qsub": "/bin/qsub"}) == SP.OTHER
    assert classify_with({"qstat": "/bin/qstat"}) == SP.OTHER


def test_has_nqsv_accepts_marker_without_path_evidence():
    with tempfile.TemporaryDirectory() as marker:
        with mock.patch.object(SP.shutil, "which", return_value=None):
            assert SP._has_nqsv(marker) is True


def test_has_nqsv_rejects_when_path_and_marker_are_absent():
    with tempfile.TemporaryDirectory() as directory:
        marker = os.path.join(directory, "missing-nqsv")
        with mock.patch.object(SP.shutil, "which", return_value=None):
            assert SP._has_nqsv(marker) is False


def test_has_nqsv_accepts_path_evidence_without_marker():
    with tempfile.TemporaryDirectory() as directory:
        marker = os.path.join(directory, "missing-nqsv")
        with mock.patch.object(
            SP.shutil,
            "which",
            side_effect=lambda name: f"/fixture/{name}",
        ):
            assert SP._has_nqsv(marker) is True


def test_has_nqsv_marker_oserror_fails_closed_without_leaking():
    with mock.patch.object(
        SP.shutil,
        "which",
        return_value=None,
    ), mock.patch.object(
        SP.os.path,
        "isdir",
        side_effect=OSError("marker unavailable"),
    ):
        assert SP._has_nqsv("/fixture/nqsv") is False


def test_current_site_uses_marker_when_path_is_empty():
    with tempfile.TemporaryDirectory() as marker:
        with mock.patch.object(
            SP.socket,
            "gethostname",
            return_value="pegasus02",
        ), mock.patch.object(
            SP.shutil,
            "which",
            return_value=None,
        ), mock.patch.object(SP, "NQSV_MARKER_DIR", marker):
            assert SP.current_site() == SP.PEGASUS_LOGIN


def test_classify_site_does_not_resolve_the_real_environment():
    with mock.patch.object(
        SP.socket,
        "gethostname",
        side_effect=AssertionError("impure hostname access"),
    ), mock.patch.object(
        SP.shutil,
        "which",
        side_effect=AssertionError("impure PATH access"),
    ):
        assert (
            SP.classify_site("pegasus01", {"PBS_JOBID": "ignored"}, True)
            == SP.PEGASUS_LOGIN
        )


def test_available_cpus_prefers_process_count_then_affinity():
    with mock.patch.object(
        SP.os,
        "process_cpu_count",
        return_value=6,
        create=True,
    ), mock.patch.object(
        SP.os,
        "sched_getaffinity",
        side_effect=AssertionError("affinity fallback must not run"),
    ):
        assert SP.available_cpus() == 6

    with mock.patch.object(
        SP.os,
        "process_cpu_count",
        return_value=None,
        create=True,
    ), mock.patch.object(
        SP.os,
        "sched_getaffinity",
        return_value={1, 3, 5, 7},
    ), mock.patch.object(
        SP.os,
        "cpu_count",
        side_effect=AssertionError("cpu_count fallback must not run"),
    ):
        assert SP.available_cpus() == 4


def test_available_cpus_permission_error_falls_back_to_cpu_count():
    """M3: sched_getaffinity の OSError 捕捉削除を PermissionError で kill する。"""
    for error in (
        AttributeError("affinity unavailable"),
        PermissionError("affinity denied"),
    ):
        with mock.patch.object(
            SP.os,
            "process_cpu_count",
            return_value=None,
            create=True,
        ), mock.patch.object(
            SP.os,
            "sched_getaffinity",
            side_effect=error,
        ), mock.patch.object(SP.os, "cpu_count", return_value=7):
            assert SP.available_cpus() == 7


def test_compute_defaults_use_all_available_cpus_without_test_cap():
    """M2: COMPUTE 分岐を消して常時 cap する変異を kill する。"""
    with mock.patch.object(SP, "available_cpus", return_value=48):
        assert SP.default_test_jobs(SP.PEGASUS_COMPUTE) == 48
        assert SP.default_test_jobs(SP.PEGASUS_COMPUTE, cap=2) == 48
        assert SP.default_build_jobs(SP.PEGASUS_COMPUTE) == 48


def test_other_preserves_existing_test_cap_and_build_jobs():
    """M13: 非 Pegasus を LOGIN に過剰分類する正例変異を kill する negative test。"""
    site = SP.classify_site("developer-box.example", {}, True)
    assert site == SP.OTHER
    with mock.patch.object(SP, "available_cpus", return_value=96):
        assert SP.default_test_jobs(site) == min(96, 32)
        assert SP.default_build_jobs(site) == 16
    assert not SP.refuses_heavy_work(site)


def test_refusal_helpers_cover_login_and_suspect_but_not_compute():
    """M4: refuses_heavy_work から SUSPECT を外す変異を kill する。"""
    assert SP.is_pegasus_login(SP.PEGASUS_LOGIN)
    assert not SP.is_pegasus_login(SP.PEGASUS_COMPUTE)
    assert SP.is_pegasus_compute(SP.PEGASUS_COMPUTE)
    assert not SP.is_pegasus_compute(SP.PEGASUS_LOGIN)
    assert SP.refuses_heavy_work(SP.PEGASUS_LOGIN)
    assert SP.refuses_heavy_work(SP.PEGASUS_SUSPECT)
    assert not SP.refuses_heavy_work(SP.PEGASUS_COMPUTE)
    assert not SP.refuses_heavy_work(SP.OTHER)


def test_heavy_work_refusal_is_japanese_and_names_compliant_route():
    for site in (SP.PEGASUS_LOGIN, SP.PEGASUS_SUSPECT):
        message = SP.heavy_work_refusal(site, "pytest")
        assert "pytest" in message
        assert "拒否" in message
        assert "計算ノード" in message
        assert "qsub" in message
        assert "qlogin" in message


def test_heavy_work_refusal_is_pure_and_keeps_existing_text_without_hint():
    expected = (
        "pytest を拒否します: Pegasus ログインノードでは重い処理を実行できません。"
        "qsub または qlogin を使い、Pegasus 計算ノードで実行してください。"
    )
    with mock.patch(
        "subprocess.run",
        side_effect=AssertionError("拒否文面の生成で subprocess を起動してはならない"),
    ) as run:
        assert SP.heavy_work_refusal(SP.PEGASUS_LOGIN, "pytest") == expected
    run.assert_not_called()


def test_heavy_work_refusal_keeps_existing_text_when_queue_is_available():
    expected = (
        "pytest を拒否します: Pegasus ログインノードでは重い処理を実行できません。"
        "qsub または qlogin を使い、Pegasus 計算ノードで実行してください。"
    )
    assert SP.heavy_work_refusal(
        SP.PEGASUS_LOGIN,
        "pytest",
        queue_hint=(True, "キューは利用できます。"),
    ) == expected


def test_heavy_work_refusal_adds_queue_diagnosis_only_with_unavailable_hint():
    existing = (
        "性能測定 を拒否します: Pegasus ログインノードでは重い処理を実行できません。"
        "qsub または qlogin を使い、Pegasus 計算ノードで実行してください。"
    )
    queue_reason = (
        "キュー gen_S は ENA=DIS、STS=INA、待ち数=95、実行数=68で、"
        "現在利用できません。"
    )
    without_hint = SP.heavy_work_refusal(SP.PEGASUS_LOGIN, "性能測定")
    message = SP.heavy_work_refusal(
        SP.PEGASUS_LOGIN,
        "性能測定",
        queue_hint=(False, queue_reason),
    )
    assert without_hint == existing
    assert queue_reason not in without_hint
    assert message.startswith(existing)
    assert queue_reason in message
    assert "投入しても実行されません" in message
    assert "したがって性能測定は現時点では実施できません" in message


def test_site_policy_imports_only_approved_stdlib_modules():
    source = (_REPO / "orchestrator" / "campaign" / "site_policy.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
    assert imports == {"__future__", "os", "re", "shutil", "socket"}


def test_fa3_all_changed_production_modules_defer_annotation_evaluation():
    """FA-3: Python 3.9 import 回帰を全変更 production module の静的契約で拒否する。"""

    modules = (
        _REPO / "orchestrator" / "campaign" / "site_policy.py",
        _REPO / "tools" / "run_tests.py",
        _REPO / "tools" / "pegasus" / "dispatch_compute.py",
    )
    for path in modules:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        futures = [
            node
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module == "__future__"
        ]
        assert len(futures) == 1, path
        assert [alias.name for alias in futures[0].names] == ["annotations"], path


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
