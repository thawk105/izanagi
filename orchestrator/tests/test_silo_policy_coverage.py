"""C1 diagnostic contracts; real patch application and real policy validators."""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

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
             prefix_held_limit_aborts=1, prefix_held_action_aborts=2,
             clamps=1, reason_lock_conflict=3, site_lock_conflict=3,
             abort_match=5, lock_match=3, commit_match=3, reason_match=3, post_commit_match=2)
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
        if case in ("focus/retry", "mutation/no-prefix-unlock-limit"):
            r["case_definition"] = {"policy": "retry", "workload": dict(coverage.LEGACY)}
        if case in ("focus/abort0", "mutation/no-prefix-unlock-conflict"):
            r["case_definition"] = {"policy": "abort0", "workload": dict(coverage.LEGACY)}
        runs[case] = r
    return runs


def _checks(runs):
    return coverage.coverage_checks(runs)


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


def test_coverage_reuses_controls_and_separates_prefix_exits():
    observed = {}
    builds = []
    fixtures = _complete_runs()

    @contextmanager
    def source(policy, *, compiler, scratch, probe_patch=False, patch=None):
        case = next(c for c in coverage.COVERAGE_CASES if c.replace("/", "-") == scratch.name)
        observed[case] = (policy, probe_patch, patch)
        yield scratch, {"accepted": True}

    def build(source, build, **kwargs):
        builds.append(source.name)
        return source / "binary", {}

    def run(binary, flags, *, source, trace, probe=False, numa=False):
        case = next(c for c in fixtures if c.replace("/", "-") == source.name)
        return deepcopy(fixtures[case])

    def preprocess(command, overrides=None):
        return SimpleNamespace(returncode=1 if overrides else 0, stdout="",
                               stderr="Silo function policy requires BACK_OFF=1 and no-wait flags 1/0")

    with tempfile.TemporaryDirectory() as tmp, \
         patch.object(coverage, "_source", source), \
         patch.object(coverage, "_build_variant", build), \
         patch.object(coverage, "_run", run), \
         patch.object(coverage, "_owner_command", return_value={"arguments": []}), \
         patch.object(coverage, "_preprocess", preprocess), \
         patch.object(coverage, "_break_evidence", return_value={"target_difference": True}), \
         patch.object(coverage.compute, "_sha256_file", return_value="digest"):
        result = coverage.run_coverage(Path(tmp), {"cxx_path": "unused"}, {})
    assert result["all_pass"] is True
    # Build negative, focus, unshared control, and mutation cases, plus one shared TRACE=0 build.
    assert len(builds) == (len(coverage.NEGATIVE_CASES) + len(coverage.FOCUS_CASES)
                           + len(set(coverage.CONTROL_CASES) - set(coverage.CONTROL_OBSERVATIONS))
                           + len(coverage.MUTATION_CASES) + 1)
    assert set(coverage.CONTROL_OBSERVATIONS) == {
        "control/no-reload", "control/no-abort-hook", "control/no-lock-hook",
        "control/no-commit-hook", "control/wrong-reason",
    }
    for control, focus in coverage.CONTROL_OBSERVATIONS.items():
        assert control not in observed
        assert result["runs"][control]["observation_case"] == focus
        assert result["runs"][control]["case_sha256"] == result["runs"][focus]["case_sha256"]
        assert coverage.check_case(control, result["runs"][focus]) == {"expected": True}
    for name, policy, exit_name, mutation_patch in (
            ("no-prefix-unlock-conflict", "abort0", "action-abort",
             "broken-silo-policy-no-prefix-unlock.patch"),
            ("no-prefix-unlock-limit", "retry", "attempt-limit",
             "broken-silo-policy-no-prefix-unlock-limit.patch")):
        for kind in ("control", "mutation"):
            case = kind + "/" + name
            assert observed[case] == (policy, True, mutation_patch
                                      if kind == "mutation" else None)
            assert result["runs"][case]["case_definition"]["target_exit"] == exit_name
            assert result["checks"][case + ":expected"] is True
    assert (observed["mutation/no-prefix-unlock-conflict"][2]
            != observed["mutation/no-prefix-unlock-limit"][2])


def test_prefix_limit_requires_matching_retry_probe_reach():
    case = "mutation/no-prefix-unlock-limit"
    key = case + ":expected"
    runs = _complete_runs()
    assert runs[case]["reason"] == "trace-timeout"
    checks = _checks(runs)
    assert checks[key] is True
    assert coverage.judge(runs, checks)["all_pass"] is True
    for count in (0, -1, None, True):
        missing = deepcopy(runs)
        missing["focus/retry"]["probe"]["totals"]["limit_aborts"] = count
        assert _checks(missing)[key] is False
        assert coverage.judge(missing, _checks(missing))["all_pass"] is False
        assert coverage.judge(missing, checks)["all_pass"] is False
    for target in (case, "focus/retry"):
        for field, value in (("policy", "maxwait"), ("workload", {}),
                             ("workload", {**coverage.LEGACY, "thread_num": "99"})):
            mismatch = deepcopy(runs)
            mismatch[target]["case_definition"][field] = value
            assert _checks(mismatch)[key] is False
            assert coverage.judge(mismatch, checks)["all_pass"] is False
        missing = deepcopy(runs)
        del missing[target]["case_definition"]
        assert _checks(missing)[key] is False
    missing = deepcopy(runs)
    del missing["focus/retry"]
    assert _checks(missing)[key] is False
    missing = deepcopy(runs)
    del missing["focus/retry"]["probe"]
    assert _checks(missing)[key] is False
    no_timeout = deepcopy(runs)
    no_timeout[case]["reason"] = "verifier-timeout"
    assert _checks(no_timeout)[key] is False


def test_prefix_exit_case_configuration():
    assert coverage.MUTATION_PATCHES["no-prefix-unlock-conflict"] == "broken-silo-policy-no-prefix-unlock.patch"
    assert coverage.MUTATION_PATCHES["no-prefix-unlock-limit"] == "broken-silo-policy-no-prefix-unlock-limit.patch"
    assert len(set(coverage.MUTATION_PATCHES.values())) == 9
    assert "focus/abort0" in coverage.FOCUS_CASES
    assert coverage.MUTATIONS["no-prefix-unlock-conflict"] == ("abort0", False, "trace-timeout")
    assert coverage.MUTATIONS["no-prefix-unlock-limit"] == ("retry", False, "trace-timeout")
    runs = _complete_runs()
    assert set(runs) == coverage.COVERAGE_CASES
    assert set(_checks(runs)) == coverage.COVERAGE_CHECKS
    assert coverage.judge(runs, _checks(runs))["all_pass"] is True


def _assert_prefix_held_reach_required(case, observation, counter, policy):
    runs = _complete_runs()
    checks = _checks(runs)
    key = case + ":expected"
    assert runs[case]["reason"] == "trace-timeout"
    assert checks[key] is True
    assert coverage.judge(runs, checks)["all_pass"] is True
    for count in (0, -1, None, True):
        missing = deepcopy(runs)
        missing[observation]["probe"]["totals"][counter] = count
        assert _checks(missing)[key] is False
        assert coverage.judge(missing, _checks(missing))["all_pass"] is False
        assert coverage.judge(missing, checks)["all_pass"] is False
    for target in (case, observation):
        for field, value in (("policy", "maxwait"), ("workload", {}),
                             ("workload", {**coverage.LEGACY, "thread_num": "99"})):
            mismatch = deepcopy(runs)
            mismatch[target]["case_definition"][field] = value
            assert _checks(mismatch)[key] is False
        assert runs[target]["case_definition"]["policy"] == policy
    for field in ("probe", "case_definition"):
        missing = deepcopy(runs)
        del missing[observation][field]
        assert _checks(missing)[key] is False
    missing = deepcopy(runs)
    del missing[observation]
    assert _checks(missing)[key] is False
    missing = deepcopy(runs)
    del missing[observation]["probe"]["totals"][counter]
    assert _checks(missing)[key] is False
    wrong_timeout = deepcopy(runs)
    wrong_timeout[case]["reason"] = "verifier-timeout"
    assert _checks(wrong_timeout)[key] is False


def test_prefix_limit_requires_prefix_held_limit_reach():
    """M-PREFIX-REACH: total limit reach cannot replace prefix-held reach."""
    _assert_prefix_held_reach_required(
        "mutation/no-prefix-unlock-limit", "focus/retry", "prefix_held_limit_aborts", "retry")


def test_prefix_conflict_requires_prefix_held_action_reach():
    _assert_prefix_held_reach_required(
        "mutation/no-prefix-unlock-conflict", "focus/abort0", "prefix_held_action_aborts", "abort0")


def test_probe_parser_requires_prefix_held_exit_keys():
    report = coverage.parse_probe(_line(0) + "\n" + _line(1), workers=2)
    for counter, value in (("prefix_held_limit_aborts", 1), ("prefix_held_action_aborts", 2)):
        assert report["totals"][counter] == 2 * value
        for worker in (0, 1):
            assert report["workers"][worker][counter] == value
        for line in (_line().replace(f" {counter}={value}", ""),
                     _line() + f" {counter}={value}"):
            try:
                coverage.parse_probe(line, workers=1)
            except ValueError:
                pass
            else:
                raise AssertionError("missing or duplicated prefix reach accepted")


def test_prefix_unlock_patches_remove_only_the_target_exit():
    with _applied_template() as (checkout, _):
        path = checkout / coverage.axis.SOURCE_REL
        _git(checkout, "apply", "--check", str(ROOT / "patches" / coverage.PROBE_PATCH))
        _git(checkout, "apply", str(ROOT / "patches" / coverage.PROBE_PATCH))
        probe = path.read_text()
        unlock = "        if (itr != write_set_.begin()) unlockWriteSet(itr);\n"
        for name, target_index in (("no-prefix-unlock-limit", 0), ("no-prefix-unlock-conflict", 1)):
            path.write_text(probe)
            patch_path = ROOT / "patches" / coverage.MUTATION_PATCHES[name]
            _git(checkout, "apply", "--check", str(patch_path))
            _git(checkout, "apply", str(patch_path))
            mutated = path.read_text()
            assert _select_mutation(mutated, False) == probe
            loop_start = probe.index("      if (attempt >= 32u)")
            sites = [m.start() for m in re.finditer(re.escape(unlock), probe) if m.start() > loop_start]
            target = sites[target_index]
            # Exact source equality proves the other exit (and every other byte) survives.
            assert _select_mutation(mutated, True) == probe[:target] + probe[target + len(unlock):]


def test_focus_requires_post_commit_state_observation():
    runs = _complete_runs()
    assert coverage.judge(runs, _checks(runs))["all_pass"] is True
    p = runs["focus/focus"]["probe"]["totals"]
    p["post_commit_match"] = 0
    assert coverage.check_case("focus/focus", runs["focus/focus"])["commit"] is False
    assert coverage.judge(runs, _checks(runs))["all_pass"] is False
    p["post_commit_match"] = 2
    p["post_commit_mismatch"] = 1
    assert coverage.check_case("focus/focus", runs["focus/focus"])["commit"] is False
    assert coverage.judge(runs, _checks(runs))["all_pass"] is False


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
            patch = ROOT / "patches" / coverage.MUTATION_PATCHES[name]
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


def test_condition_gates_isolate_each_macro_and_keep_axis_cache():
    args = coverage.GENOME.cmake_defines() + ["-DCCBENCH_TRACE=1"]
    assert "-DCCBENCH_SILO_POLICY_VARIANT=1" in args
    cases = [((), [coverage.axis.FLAG])]
    cases += [((macro,), [coverage.axis.FLAG, macro])
              for _, macro in coverage.NEGATIVES.values()]
    cases += [((coverage.PROBE_DEFINE,), [coverage.axis.FLAG, coverage.PROBE_DEFINE]),
              ((coverage.BREAK_DEFINE,), [coverage.BREAK_DEFINE]),
              ((coverage.PROBE_DEFINE, coverage.BREAK_DEFINE), [coverage.BREAK_DEFINE])]
    for macros, expected in cases:
        with patch.object(coverage, "_condition_gate", return_value={"admission": {"admitted": True}}) as gate:
            receipts = coverage._condition_gates(Path("source"), macros, args, "c++", stock=False)
        assert len(receipts) == len(expected)
        assert [call.args[1] for call in gate.call_args_list] == expected
        for call in gate.call_args_list:
            assert call.args[2] == args
            assert not any(a.startswith("-DCMAKE_CXX_FLAGS=") for a in call.args[2])


def test_build_requires_gate_before_configure_and_keeps_build_macros():
    for admitted in (False, True):
        events = []

        def gates(source, macros, args, cxx, *, stock):
            events.append("gate")
            assert "-DCCBENCH_SILO_POLICY_VARIANT=1" in args
            assert not any(a.startswith("-DCMAKE_CXX_FLAGS=") for a in args)
            return [{"admission": {"admitted": admitted}}]

        def configure(argv):
            assert events == ["gate"]
            events.append("configure")
            assert "-DCCBENCH_SILO_POLICY_VARIANT=1" in argv
            assert ("-DCMAKE_CXX_FLAGS=-DIZANAGI_SILO_POLICY_PROBE=1 "
                    "-DIZANAGI_BREAK_SILO_POLICY=1") in argv

        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(coverage.site_policy, "current_site", return_value="test"), \
             patch.object(coverage.site_policy, "refuses_heavy_work", return_value=False), \
             patch.object(coverage.compute, "_common_configure_args", return_value=[]), \
             patch.object(coverage, "_condition_gates", gates), \
             patch.object(coverage.compute, "_run_checked", configure), \
             patch.object(coverage.locks, "_run_cmake_build") as build:
            root = Path(tmp)
            binary = root / "cc/silo/ycsb_silo.exe"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b"fixture")
            try:
                coverage._build_variant(root, root, trace=1, toolchain={"cxx_path": "c++"},
                                        dependencies={}, macros=(coverage.PROBE_DEFINE, coverage.BREAK_DEFINE))
            except RuntimeError as exc:
                assert not admitted
                assert str(exc) == "condition gates rejected before build"
            else:
                assert admitted
            assert events == (["gate", "configure"] if admitted else ["gate"])
            assert build.call_count == int(admitted)


def test_build_variant_passes_backoff_fixed_to_configure(tmp_path):
    configure_argv = []

    def configure(argv):
        configure_argv.append(argv)

    def build(argv, **kwargs):
        binary = Path(argv[2]) / "cc/silo/ycsb_silo.exe"
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b"fixture")

    with patch.object(coverage.site_policy, "current_site", return_value="test"), \
         patch.object(coverage.site_policy, "refuses_heavy_work", return_value=False), \
         patch.object(coverage.compute, "_common_configure_args", return_value=[]), \
         patch.object(coverage, "_condition_gates", return_value=[]), \
         patch.object(coverage.compute, "_run_checked", side_effect=configure), \
         patch.object(coverage.locks, "_run_cmake_build", side_effect=build):
        coverage._build_variant(tmp_path, tmp_path / "fixed10", trace=1,
                                toolchain={"cxx_path": "c++"}, dependencies={},
                                stock=True, stock_backoff=1, stock_backoff_fixed=10)
        coverage._build_variant(tmp_path, tmp_path / "stock", trace=1,
                                toolchain={"cxx_path": "c++"}, dependencies={},
                                stock=True, stock_backoff=1)
    assert len(configure_argv) == 2
    assert configure_argv[0].count("-DCCBENCH_BACKOFF_FIXED=10") == 1
    assert configure_argv[0].count("-DCCBENCH_BACK_OFF=1") == 1
    assert not any(arg.startswith("-DCCBENCH_BACKOFF_FIXED=") for arg in configure_argv[1])


def test_command_arguments_accepts_both_compile_command_forms():
    argv = ["c++", "-DNAME=two words", "-c", "source file.cc"]
    for row in ({"arguments": argv}, {"command": "c++ '-DNAME=two words' -c 'source file.cc'"}):
        assert coverage._command_arguments(row) == argv
        with patch.object(coverage.compute, "_run_checked") as run:
            coverage._preprocess({**row, "directory": "/tmp"})
        assert run.call_args.args[0] == ["c++", "-DNAME=two words", "source file.cc", "-E", "-P"]
    assert coverage._command_arguments({"arguments": []}) == []
    assert coverage._command_arguments({"arguments": [], "command": "must not be used"}) == []


def test_condition_gate_rejection_preserves_arm_reasons_in_result_json():
    supply = SimpleNamespace(terminal_status="green", reason_code="requested-default-preprocess-different")
    meaning = SimpleNamespace(terminal_status="red", reason_code="compile-time-branch-selection-mismatch")
    supply.canonical_json = lambda: json.dumps(vars_without_methods(supply))
    meaning.canonical_json = lambda: json.dumps(vars_without_methods(meaning))
    admission = SimpleNamespace(admitted=False, canonical_json=lambda: '{"admitted":false}')

    @contextmanager
    def configured(*args, **kwargs):
        yield object()

    with patch.object(coverage.condition, "capture_define_inputs", return_value=object()), \
         patch.object(coverage.condition, "_configured_define_compile_commands", configured), \
         patch.object(coverage.condition, "evaluate_define_supply_effectuation", return_value=supply), \
         patch.object(coverage.condition, "evaluate_define_runtime_meaning", return_value=meaning), \
         patch.object(coverage.condition, "require_condition_gate_family", return_value=admission):
        try:
            coverage._condition_gate(Path("source"), coverage.axis.FLAG, [], "c++")
        except RuntimeError as exc:
            rejection = exc
        else:
            raise AssertionError("rejected gate returned normally")
    expected = ("condition gate rejected SILO_POLICY_VARIANT: "
                "supply=green/requested-default-preprocess-different, "
                "meaning=red/compile-time-branch-selection-mismatch")
    assert str(rejection) == expected
    with tempfile.TemporaryDirectory() as tmp, \
         patch.object(coverage.site_policy, "current_site", return_value="test"), \
         patch.object(coverage.site_policy, "refuses_heavy_work", return_value=False), \
         patch.object(coverage, "_assert_single_tenant"), \
         patch.object(coverage.compute, "_load_policy", return_value={}), \
         patch.object(coverage.compute, "_resolve_toolchain", return_value={}), \
         patch.object(coverage.compute, "_prepare_dependencies", return_value={}), \
         patch.object(coverage, "_prepare_build_dependencies", return_value={}), \
         patch.object(coverage, "run_coverage", side_effect=rejection):
        out = Path(tmp) / "result.json"
        assert coverage.main(["coverage", "--third-party-cache", tmp,
                              "--policy", __file__, "--out", str(out)]) == 1
        result = json.loads(out.read_text())
    assert result["all_pass"] is False
    assert result["error"] == "RuntimeError: " + expected


def vars_without_methods(record):
    return {key: value for key, value in vars(record).items() if not callable(value)}


def test_condition_gate_failure_keeps_complete_receipts_and_stops_build():
    payloads = {
        "supply": {"terminal_status": "red", "reason_code": "preprocess-failed",
                   "evidence": {"detail": "rc=1; stderr=b'config.h: No such file or directory'",
                                "expected": None, "observed": {"nested": [1, 2]}}},
        "meaning": {"terminal_status": "red", "reason_code": "compile-time-branch-preprocess-failed",
                    "evidence": {"detail": "instrumented owner: config.h absent", "context_index": None}},
        "admission": {"admitted": False, "reasons": ["supply", "meaning"]},
    }
    records = {key: SimpleNamespace(**value, canonical_json=lambda value=value: json.dumps(value))
               for key, value in payloads.items()}

    @contextmanager
    def configured(*args, **kwargs):
        yield object()

    def rejected_case(scratch, toolchain, dependencies, *, runs):
        coverage._build_variant(scratch, scratch / "case", trace=1,
                                toolchain=toolchain, dependencies=dependencies)

    for mode in ("coverage", "smoke"):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(coverage.site_policy, "current_site", return_value="test"), \
             patch.object(coverage.site_policy, "refuses_heavy_work", return_value=False), \
             patch.object(coverage, "_assert_single_tenant"), \
             patch.object(coverage.compute, "_load_policy", return_value={}), \
             patch.object(coverage.compute, "_resolve_toolchain", return_value={"cxx_path": "c++"}), \
             patch.object(coverage.compute, "_prepare_dependencies", return_value={}), \
             patch.object(coverage, "_prepare_build_dependencies", return_value={}), \
             patch.object(coverage.compute, "_common_configure_args", return_value=[]), \
             patch.object(coverage.condition, "capture_define_inputs", return_value=object()), \
             patch.object(coverage.condition, "_configured_define_compile_commands", configured), \
             patch.object(coverage.condition, "evaluate_define_supply_effectuation", return_value=records["supply"]), \
             patch.object(coverage.condition, "evaluate_define_runtime_meaning", return_value=records["meaning"]), \
             patch.object(coverage.condition, "require_condition_gate_family", return_value=records["admission"]), \
             patch.object(coverage.compute, "_run_checked") as configure, \
             patch.object(coverage.locks, "_run_cmake_build") as build, \
             patch.object(coverage, "run_" + mode, rejected_case):
            out = Path(tmp) / "result.json"
            assert coverage.main([mode, "--third-party-cache", tmp,
                                  "--policy", __file__, "--out", str(out)]) == 1
            result = json.loads(out.read_text())
            assert result["all_pass"] is False
            assert result["condition_gate_evidence"] == {"macro": coverage.axis.FLAG, **payloads}
            assert "supply=red/preprocess-failed" in result["error"]
            assert "meaning=red/compile-time-branch-preprocess-failed" in result["error"]
            configure.assert_not_called()
            build.assert_not_called()


def test_main_prepares_dependencies_once_before_gates_in_either_case_order():
    for mode in ("coverage", "smoke"):
        for reverse in (False, True):
            events = []
            dependencies = {"masstree": Path("per-job-masstree")}
            cases = (["norw/abort0", "lockskip/maxwait"] if mode == "coverage"
                     else ["stock", "abort0", "retry"])
            if reverse:
                cases.reverse()

            @contextmanager
            def source(policy, *, compiler, scratch):
                assert policy == "stock"
                events.append("prepare")
                yield scratch, {"accepted": True, "stock": True}

            def configure(argv):
                events.append("configure")

            def build(argv, *, site):
                root = Path(argv[argv.index("--build") + 1])
                binary = root / "cc/silo/ycsb_silo.exe"
                binary.parent.mkdir(parents=True)
                binary.write_bytes(b"fixture")
                events.append("prepared" if root.parent.name == "dependency-stock" else "built")

            def gate(source, macro, args, cxx):
                assert events.count("prepare") == events.count("prepared") == 1
                events.append("gate")
                return {"admission": {"admitted": True}}

            def runner(scratch, toolchain, supplied, *, runs):
                assert supplied is dependencies
                assert events == ["prepare", "configure", "prepared"]
                for case in cases:
                    coverage._build_variant(scratch, scratch / case.replace("/", "-"),
                                            trace=1, toolchain=toolchain,
                                            dependencies=supplied, stock=case == "stock")
                return {"all_pass": False}

            with tempfile.TemporaryDirectory() as tmp, \
                 patch.object(coverage.site_policy, "current_site", return_value="test"), \
                 patch.object(coverage.site_policy, "refuses_heavy_work", return_value=False), \
                 patch.object(coverage, "_assert_single_tenant"), \
                 patch.object(coverage.compute, "_load_policy", return_value={}), \
                 patch.object(coverage.compute, "_resolve_toolchain", return_value={"cxx_path": "c++"}), \
                 patch.object(coverage.compute, "_prepare_dependencies", return_value=dependencies), \
                 patch.object(coverage.compute, "_common_configure_args", return_value=[]), \
                 patch.object(coverage.compute, "_sha256_file", return_value="fixture-digest"), \
                 patch.object(coverage, "_source", source), \
                 patch.object(coverage, "_condition_gate", gate), \
                 patch.object(coverage.compute, "_run_checked", configure), \
                 patch.object(coverage.locks, "_run_cmake_build", build), \
                 patch.object(coverage, "run_" + mode, runner):
                out = Path(tmp) / "result.json"
                assert coverage.main([mode, "--third-party-cache", tmp,
                                      "--policy", __file__, "--out", str(out)]) == 1
                result = json.loads(out.read_text())
                assert "error" not in result
                assert result["dependency_preparation"]["condition_gates"] == []
                assert result["dependency_preparation"]["binary_sha256"] == "fixture-digest"
            assert events.count("prepare") == events.count("prepared") == 1
            assert events.count("gate") == sum(case != "stock" for case in cases)


def test_owner_command_selects_ycsb_from_four_targets_and_rejects_ambiguity():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for form in ("output", "command", "arguments", "joined-output"):
            rows = []
            for workload in ("tpcc", "ycsb", "bomb", "sbomb"):
                output = f"cc/silo/CMakeFiles/{workload}_silo.exe.dir/transaction.cc.o"
                argv = ["c++", "-c", str(root / coverage.axis.SOURCE_REL), "-o", output]
                row = {"directory": tmp, "file": coverage.axis.SOURCE_REL}
                if form == "output":
                    row.update(output=output, arguments=argv)
                elif form == "command":
                    row["command"] = coverage.shlex.join(argv)
                else:
                    row["arguments"] = argv if form == "arguments" else argv[:-2] + ["-o" + output]
                rows.append(row)
            database = root / "compile_commands.json"
            database.write_text(json.dumps(rows))
            assert coverage._owner_command(root, root) == rows[1]
            for invalid in (rows[:1] + rows[2:], rows + [rows[1]]):
                database.write_text(json.dumps(invalid))
                try:
                    coverage._owner_command(root, root)
                except RuntimeError as exc:
                    assert "not unique" in str(exc)
                else:
                    raise AssertionError("missing or ambiguous YCSB owner accepted")


def test_preprocess_strips_output_and_dependency_forms_and_replaces_defines():
    for attached in (False, True):
        outputs = (["-oowner.o", "-MFowner.d", "-MTowner", "-MQowner"] if attached else
                   ["-o", "owner.o", "-MF", "owner.d", "-MT", "owner", "-MQ", "owner"])
        row = {"directory": "/tmp", "arguments": ["c++", "-DBACK_OFF=1", "-D", "TRACE=0",
               "-DKEEP=1", "-c", "-MD", "-MMD", "-MP", *outputs, "owner.cc"]}
        with patch.object(coverage.compute, "_run_checked") as run:
            coverage._preprocess(row, {"BACK_OFF": "2", "TRACE": "1"})
        assert run.call_args.args[0] == ["c++", "-DKEEP=1", "owner.cc", "-E", "-P",
                                          "-DBACK_OFF=2", "-DTRACE=1"]
        assert run.call_args.kwargs == {"cwd": Path("/tmp"), "allowed_returncodes": frozenset({0, 1})}


def test_lockskip_evidence_ignores_preprocessor_indentation_but_requires_target():
    off = "void TxExecutor::lockWriteSet() { max_wset_ = std::max(max_wset_, expected); for (;;) {} }"
    on = "void TxExecutor::lockWriteSet() { max_wset_ = std::max(max_wset_, expected);\n continue; for (;;) {} }"
    for enabled, expected in ((on, True), (off, False), (on.replace("continue;", "break;"), False)):
        with patch.object(coverage, "_preprocess", side_effect=[
                SimpleNamespace(returncode=0, stdout=off), SimpleNamespace(returncode=0, stdout=enabled)]), \
             patch.object(coverage.compute, "_sha256_file", return_value="digest"):
            result = coverage._break_evidence("lockskip/abort0", {}, Path("source"), Path("patch"), "BREAK")
        assert result["target_difference"] is expected


def test_trace_timeout_preserves_partial_output_and_exact_reason():
    for payload in (b"partial probe\n", "partial probe\n"):
        failure = coverage.subprocess.TimeoutExpired("binary", 120, output=payload, stderr=b"diagnostic")
        with patch.object(coverage, "_assert_single_tenant"), \
             patch.object(coverage.subprocess, "run", side_effect=failure), \
             patch.object(coverage, "_verify") as verify:
            result = coverage._run(Path("/binary"), coverage.LEGACY, source=Path("source"), trace=True)
        assert result["reason"] == "trace-timeout"
        assert result["timeout_s"] == 120
        assert result["stdout"] == "partial probe\n" and result["stderr"] == "diagnostic"
        assert "probe" not in result and "certified" not in result
        verify.assert_not_called()
        for case in ("mutation/no-clamp", "mutation/no-prefix-unlock-conflict", "mutation/no-prefix-unlock-limit"):
            assert coverage.check_case(case, result) == {"expected": True}


def test_verifier_timeout_keeps_run_witnesses_without_becoming_trace_timeout():
    totals = _probe_totals()
    stdout = "commit_counts_: 7\nbatch_commit_counts_: 0\nabort_counts_: 3\n"
    stdout += "IZANAGI_SILO_POLICY_PROBE worker=0 " + " ".join(f"{k}={v}" for k, v in totals.items()) + "\n"
    failure = RuntimeError("command could not be executed")
    failure.__cause__ = coverage.subprocess.TimeoutExpired("verifier", 600)
    with patch.object(coverage, "_assert_single_tenant"), \
         patch.object(coverage.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=stdout, stderr="")), \
         patch.object(coverage, "_verify", side_effect=failure), \
         patch.object(coverage.locks, "_count_x_reasons", return_value={}):
        result = coverage._run(Path("/binary"), coverage.locks.SINGLE_FLAGS,
                               source=Path("source"), trace=True, probe=True)
    assert result["reason"] == "verifier-timeout" and result["timeout_s"] == 600
    assert result["commits"] == 7 and result["aborts"] == 3
    assert result["probe"]["totals"] == totals
    assert coverage.check_case("mutation/no-clamp", result) == {"expected": False}
    assert coverage._certified(result) is False


def test_verify_cli_and_projection_match_verifier_result():
    record = {"verdict": "non-serializable", "certified": False, "total_cycles": 2,
              "stats": {"txns": 7}, "integrity": {"lock_coverage_violations": 3}}
    completed = SimpleNamespace(returncode=1, stdout=json.dumps({"results": [record]}))
    with patch.object(coverage.compute, "_run_checked", return_value=completed) as run:
        result = coverage._verify("trace-dir", Path("/isolated/source"), 7)
    assert run.call_args.args[0] == [sys.executable, "-m", "verifier", "trace-dir", "--json", "--quiet",
                                    "--protocol", "silo", "--ccbench-root", "/isolated/source",
                                    "--expected-commits", "7"]
    assert run.call_args.kwargs == {"cwd": ROOT / "orchestrator", "timeout": 600.0,
                                    "allowed_returncodes": frozenset({0, 1, 2, 3})}
    assert result == {"exit_code": 1, "verdict": "non-serializable", "certified": False,
                      "total_cycles": 2, "txns": 7, "lock_coverage_violations": 3}


def test_run_cli_trace_location_counters_probe_and_bench_projection():
    performance = coverage.performance_correctness_workload(coverage.PERF).flags
    assert performance == {**coverage.calibration.S2_FLAGS, "extime": "3"}
    stdout = "commit_counts_:\t7\nbatch_commit_counts_:\t0\nabort_counts_:\t3\nthroughput[tps]:\t7\n"
    stdout += "\n".join(_line(i) for i in range(4)) + "\n"
    for flags, trace, probe, numa in (
            (coverage.LEGACY, True, True, False),
            (coverage.locks.SINGLE_FLAGS, True, False, False),
            (performance, True, False, True), (performance, False, False, True)):
        def execute(argv, **kwargs):
            expected = (coverage.calibration.NUMA if numa else []) + ["/binary"]
            expected += [f"-{k}={v}" for k, v in flags.items()] + ["-clocks_per_us=2100"]
            assert argv == expected
            assert Path(kwargs["cwd"], "log").is_dir()
            assert kwargs["env"].get("IZANAGI_TRACE_DIR") == (kwargs["cwd"] if trace else None)
            assert kwargs["timeout"] == 120 and kwargs["capture_output"] and kwargs["text"]
            return SimpleNamespace(returncode=0, stdout=stdout, stderr="glog diagnostics")

        def verify(directory, source, commits):
            assert Path(directory, "log").is_dir() and source == Path("/source") and commits == 7
            return {"exit_code": 0, "certified": True, "verdict": "serializable", "total_cycles": 0,
                    "lock_coverage_violations": 0}

        with patch.object(coverage, "_assert_single_tenant"), \
             patch.dict(coverage.os.environ, {"IZANAGI_TRACE_DIR": "/stale"}), \
             patch.object(coverage.subprocess, "run", side_effect=execute), \
             patch.object(coverage, "_verify", side_effect=verify) as verifier, \
             patch.object(coverage.locks, "_count_x_reasons", return_value={"lock-lost-before-write": 2}):
            result = coverage._run(Path("/binary"), flags, source=Path("/source"),
                                   trace=trace, probe=probe, numa=numa)
        assert result["commits"] == 7 and result["aborts"] == 3
        assert verifier.call_count == int(trace)
        if trace:
            assert result["x_reasons"] == {"lock-lost-before-write": 2}
            assert result["exit_code"] == 0 and result["total_cycles"] == 0
        else:
            assert result["throughput"] == 7
        if probe:
            assert set(result["probe"]["workers"]) == {0, 1, 2, 3}


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
