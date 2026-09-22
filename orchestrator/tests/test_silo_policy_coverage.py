"""C1 diagnostic contracts; real patch application and real policy validators."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from skiputil import Skip
from test_silo_function_policy_template import _applied_template, _git, _cxx
from orchestrator.campaign import silo_policy_coverage as coverage


def _probe_totals():
    # Small synthetic observations for pure predicates, not captured payloads.
    p = dict.fromkeys(coverage.PROBE_KEYS, 0)
    p.update(aborts=3, locks=5, commits=7, retry_success=2, limit_aborts=1,
             clamps=1, reason_lock_conflict=3, site_lock_conflict=3,
             abort_match=5, lock_match=3, commit_match=3, reason_match=3)
    return p


def _certified():
    return {"certified": True, "verdict": "serializable", "exit_code": 0,
            "total_cycles": 0, "commits": 7, "aborts": 3,
            "probe": {"totals": _probe_totals()}}


def _complete_runs():
    runs = {}
    for case in coverage.COVERAGE_CASES:
        r = _certified()
        if case in coverage.NEGATIVE_CASES:
            kind = case.split("/")[0]
            r.update(certified=False, break_evidence={"target_difference": True})
            if kind == "norw":
                r.update(verdict="non-serializable", total_cycles=1, exit_code=1)
            else:
                r.update(verdict="indeterminate", lock_coverage_violations=1,
                         x_reasons={"lock-lost-before-write": 1})
                if kind == "lockskip":
                    r["x_reasons"]["not-locked-at-entry"] = 1
        elif case.startswith("mutation/"):
            layer = coverage.MUTATIONS[case.split("/")[1]][2]
            if layer == "trace-timeout":
                r = {"reason": "trace-timeout"}
            elif layer == "retry_success":
                r["probe"]["totals"]["retry_success"] = 0
            elif layer != "NON_DETECTION_CONTROL":
                p = r["probe"]["totals"]
                p[layer + "_mismatch"] = p[layer + "_match"]
                p[layer + "_match"] = 0
                # The focus encoding carries counters across hook returns.
                additional = {"mutation/no-abort-hook": ("lock", "commit"),
                              "mutation/no-lock-hook": ("abort",)}.get(case, ())
                for hook in additional:
                    p[hook + "_mismatch"] = p[hook + "_match"]
                    p[hook + "_match"] = 0
        elif case.startswith("flag/"):
            r = {"returncode": 1, "stderr": "Silo function policy requires BACK_OFF=1 and no-wait flags 1/0"}
        elif case == "trace0":
            r = {"clean": True}
        runs[case] = r
    return runs


def _checks(runs):
    return {case + ":" + key: value for case, r in runs.items()
            for key, value in coverage.check_case(case, r).items()}


def test_judge_rejects_missing_or_empty_checks():
    """M-CHK-EMPTY: exact run/check sets, bool types, and reached events."""
    runs = _complete_runs()
    checks = _checks(runs)
    assert set(checks) == coverage.COVERAGE_CHECKS
    assert coverage.judge(runs, checks)["all_pass"] is True
    assert coverage.judge({}, {})["all_pass"] is False
    assert coverage.judge(runs, {})["all_pass"] is False
    one_policy = {c: r for c, r in runs.items() if not c.endswith("/maxwait")}
    assert coverage.judge(one_policy, _checks(one_policy))["all_pass"] is False
    for case in coverage.COVERAGE_CASES:
        missing = {c: r for c, r in runs.items() if c != case}
        assert coverage.judge(missing, _checks(missing))["all_pass"] is False
    for value in (1, "true", None, [], {}):
        malformed = dict(checks)
        malformed[next(iter(checks))] = value
        assert coverage.judge(runs, malformed)["all_pass"] is False
    for key in ("commits", "aborts", "locks", "abort_match", "lock_match", "commit_match"):
        empty = deepcopy(runs)
        empty["focus/focus"]["probe"]["totals"][key] = 0
        # Even a caller-provided all-True check record cannot mask missing reach.
        assert coverage.judge(empty, checks)["all_pass"] is False
        assert coverage.judge(empty, _checks(empty))["all_pass"] is False
    extra = {**checks, "unexpected": True}
    assert coverage.judge(runs, extra)["all_pass"] is False
    empty = deepcopy(runs)
    empty["focus/focus"]["commits"] = 0
    assert coverage.judge(empty, checks)["all_pass"] is False


def test_smoke_judge_requires_every_policy_and_real_success():
    runs = {name: {"commits": 7, "legacy": _certified(), "performance": _certified(),
                   "bench": {"throughput": 1.0},
                   "src_token": coverage.source_digest.STOCK if name == "stock" else "body-" + name,
                   "contract": {"accepted": True, "stock": name == "stock",
                                "checked_sha256": coverage.sha(name),
                                "materialized_sha256": coverage.sha(name)}}
            for name in coverage.SMOKE_CASES}
    checks = coverage.smoke_checks(runs)
    assert coverage.judge(runs, checks, mode="smoke")["all_pass"] is True
    for name in coverage.SMOKE_CASES:
        missing = {k: v for k, v in runs.items() if k != name}
        assert coverage.judge(missing, checks, mode="smoke")["all_pass"] is False
    for target, key, value in (("legacy", "commits", 0), ("performance", "certified", False),
                               ("bench", "throughput", 0), ("contract", "accepted", False),
                               ("contract", "materialized_sha256", coverage.sha("different"))):
        broken = deepcopy(runs)
        broken["retry"][target][key] = value
        assert coverage.judge(broken, checks, mode="smoke")["all_pass"] is False
    duplicate = deepcopy(runs)
    duplicate["retry"]["src_token"] = duplicate["abort0"]["src_token"]
    assert coverage.judge(duplicate, checks, mode="smoke")["all_pass"] is False


def test_norw_judgement_requires_exit_code_one():
    """M-CHK-NORW: an abnormal verifier exit is not a detected anomaly."""
    r = {"verdict": "non-serializable", "total_cycles": 1, "exit_code": 2}
    assert coverage.judge_norw(r) is False
    assert coverage.judge_norw({**r, "exit_code": 1}) is True
    for changes in ({"total_cycles": 0}, {"verdict": "indeterminate"},
                    {"total_cycles": True}, {"exit_code": True}):
        assert coverage.judge_norw({**r, "exit_code": 1, **changes}) is False


def test_characterization_and_mechanism_predicates():
    for case, r in _complete_runs().items():
        assert all(coverage.check_case(case, r).values()), case
    runs = _complete_runs()
    for policy in ("abort0", "maxwait"):
        ls = deepcopy(runs["lockskip/" + policy])
        del ls["x_reasons"]["not-locked-at-entry"]
        assert coverage.check_case("lockskip/" + policy, ls)["detected"] is False
        early = deepcopy(runs["early-unlock/" + policy])
        early["x_reasons"]["not-locked-at-entry"] = 1
        assert coverage.check_case("early-unlock/" + policy, early)["detected"] is False
    for name, (_, _, layer) in coverage.MUTATIONS.items():
        normal = _certified()
        expected = layer == "NON_DETECTION_CONTROL"
        assert coverage.check_case("mutation/" + name, normal)["expected"] is expected
    assert coverage.check_case("mutation/no-reload", {"reason": "trace-timeout"})["expected"] is False
    assert coverage.check_case("mutation/no-limit", {"reason": "trace-timeout"})["expected"] is False
    for case, key in (("focus/retry", "retry_success"), ("focus/retry", "limit_aborts"),
                      ("focus/huge", "clamps"), ("focus/focus", "reason_match")):
        r = _certified()
        r["probe"]["totals"][key] = 0
        assert not all(coverage.check_case(case, r).values())


def test_no_lock_hook_rejects_extra_commit_mismatch():
    r = _complete_runs()["mutation/no-lock-hook"]
    assert coverage.check_case("mutation/no-lock-hook", r)["expected"] is True
    r["probe"]["totals"]["commit_mismatch"] = 1
    assert coverage.check_case("mutation/no-lock-hook", r)["expected"] is False


def test_no_lock_hook_rejects_missing_abort_mismatch():
    r = _complete_runs()["mutation/no-lock-hook"]
    assert coverage.check_case("mutation/no-lock-hook", r)["expected"] is True
    r["probe"]["totals"].update(abort_mismatch=0, abort_match=5)
    assert coverage.check_case("mutation/no-lock-hook", r)["expected"] is False


def _line(worker=0):
    return coverage.PROBE_DEFINE + " worker=" + str(worker) + " " + " ".join(
        key + "=" + str(value) for key, value in sorted(_probe_totals().items()))


def test_probe_parser_rejects_incomplete_duplicate_unknown_negative_records():
    line = _line()
    report = coverage.parse_probe("ordinary stdout\n" + line + "\n" + _line(1), workers=2)
    assert report["totals"]["commits"] == 14
    assert report["reasons"]["lock_conflict"] == "measured"
    assert report["reasons"]["scan_node"] == "unmeasured"
    bad = ["", line.replace(" commits=7", ""), line + " commits=7", line + " unknown=0",
           line.replace("commits=7", "commits=-1"), line.replace(" worker=0", ""),
           line + "\n" + line, line.replace("worker=0", "worker=1")]
    for text in bad:
        try:
            coverage.parse_probe(text, workers=1)
        except ValueError:
            pass
        else:
            raise AssertionError("malformed probe accepted: " + text)
    try:
        coverage.parse_probe(line, workers=2)
    except ValueError:
        pass
    else:
        raise AssertionError("missing worker accepted")


def _select_mutation(source: str, enabled: bool) -> str:
    """Select just the mutation's outer conditional, preserving nested bytes."""
    lines = source.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line == "#if IZANAGI_BREAK_SILO_POLICY\n"]
    assert len(starts) == 1
    start = starts[0]
    depth, middle, end = 1, None, None
    for i in range(start + 1, len(lines)):
        if re.match(r"\s*#\s*if(?:def|ndef)?\b", lines[i]):
            depth += 1
        elif re.match(r"\s*#\s*endif\b", lines[i]):
            depth -= 1
            if depth == 0:
                end = i
                break
        elif re.match(r"\s*#\s*else\b", lines[i]) and depth == 1:
            assert middle is None
            middle = i
    assert middle is not None and end is not None
    branch = lines[start + 1:middle] if enabled else lines[middle + 1:end]
    return "".join(lines[:start] + branch + lines[end + 1:])


def test_strict_patch_stacks_and_one_site_mutations():
    with _applied_template() as (checkout, _):
        path = checkout / coverage.axis.SOURCE_REL
        skeleton = path.read_text()
        for patch, _macro in coverage.NEGATIVES.values():
            path.write_text(skeleton)
            _git(checkout, "apply", "--check", str(ROOT / "patches" / patch))
            _git(checkout, "apply", str(ROOT / "patches" / patch))
            assert path.read_text() != skeleton
        path.write_text(skeleton)
        probe_patch = ROOT / "patches" / coverage.PROBE_PATCH
        _git(checkout, "apply", "--check", str(probe_patch))
        _git(checkout, "apply", str(probe_patch))
        probe = path.read_text()
        for name in coverage.MUTATIONS:
            path.write_text(probe)
            patch = ROOT / "patches" / ("broken-silo-policy-" + name + ".patch")
            assert patch.read_text().count("+#if IZANAGI_BREAK_SILO_POLICY\n") == 1
            _git(checkout, "apply", "--check", str(patch))
            _git(checkout, "apply", str(patch))
            mutated = path.read_text()
            assert _select_mutation(mutated, False) == probe, name
            assert _select_mutation(mutated, True) != probe, name


def test_probe_sites_independently_stamp_all_seven_reasons():
    with _applied_template() as (checkout, _):
        _git(checkout, "apply", str(ROOT / "patches" / coverage.PROBE_PATCH))
        source = (checkout / coverage.axis.SOURCE_REL).read_text()
        stores = re.findall(
            r"record_site\((\d+)u\);\n#endif\n\s*"
            r"::izanagi_silo_skel::reason = ::izanagi_silo_api::AbortReason::(\w+);", source)
        assert len(stores) == 8  # seven reasons; lock conflict has abort and limit exits
        assert {reason for _, reason in stores} == set(coverage.REASONS[1:])
        for number, reason in stores:
            assert coverage.REASONS[int(number)] == reason
        wrapper = source.split("__attribute__((noipa)) uint32_t after_abort()", 1)[1].split(
            "}  // namespace izanagi_silo_skel", 1)[0]
        for field in ("aborts", "locks", "commits"):
            assert "++::izanagi_silo_probe::counts." + field not in wrapper
        assert "ret.wait_us & 7u" in wrapper and "ret >> 3u" in wrapper


def test_focus_accepted_by_real_unit_b_interface():
    from orchestrator.campaign.silo_policy_grammar import validate_policy
    from orchestrator.campaign.silo_policy_compile import compile_policy
    body = (ROOT / coverage.axis.HAND_POLICY_DIR / "focus.cpp").read_text()
    assert validate_policy(body).accepted is True
    with tempfile.TemporaryDirectory() as tmp:
        result = compile_policy(body, compiler=_cxx(), scratch_dir=tmp)
        assert result.accepted is True, result
        assert result.returncode == 0 and not result.timed_out and not result.unavailable


def test_prepare_policy_real_four_stages_and_body_binding():
    with _applied_template() as (checkout, _), tempfile.TemporaryDirectory() as tmp:
        path = checkout / coverage.axis.SOURCE_REL
        before = path.read_bytes()
        body = (ROOT / coverage.axis.HAND_POLICY_DIR / "focus.cpp").read_text()
        rendered, record = coverage.prepare_policy(path, body, compiler=_cxx(), scratch_dir=tmp)
        assert record["stages"] == ("quarantine", "effects", "grammar", "compile")
        assert record["checked_sha256"] == record["materialized_sha256"] == coverage.sha(body)
        assert body in rendered
        assert path.read_bytes() == before  # caller has not materialized yet
        invalid = (ROOT / coverage.axis.HAND_POLICY_DIR / "abort0.cpp").read_text().replace(
            "return 0u;", "return true;", 1)
        try:
            coverage.prepare_policy(path, invalid, compiler=_cxx(), scratch_dir=tmp)
        except ValueError as exc:
            assert "grammar/compile rejected" in str(exc)
        else:
            raise AssertionError("U32 bool return passed smoke preparation")
        assert path.read_bytes() == before


def _run():
    passed = failed = skipped = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"PASS {name}")
            passed += 1
        except Skip as exc:
            print(f"SKIP {name}: {exc}")
            skipped += 1
        except Exception as exc:
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
