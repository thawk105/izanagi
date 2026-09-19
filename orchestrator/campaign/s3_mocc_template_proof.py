#!/usr/bin/env python3
"""Fixed-producer MOCC template proof; no performance or exploration authority."""
from __future__ import annotations
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from collections.abc import Mapping

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import s3_mocc_mutation_proof as wave1
from . import s3_mocc_lock_coverage as legacy
from . import axis_mocc_temperature as axis
from . import condition_meaning_gate, site_policy, source_digest
from .model import Genome
from .patchharness import checkout, patch_files, apply_patch
from .materializer_admission import non_admissible_materializer
from .diff_quarantine import DiffQuarantine, parse_template_file
from .auditor_gate import (AuditorVerdict, AuditorGateFailure,
                          compute_diff_digest, apply_mandatory_deny_only_veto)

SOURCE_REL = axis.SOURCE_REL
PROOF_PIN = axis.PROOF_PIN
TEMPLATE_PATCH = "patches/" + axis.TEMPLATE_PATCH
INSTRUMENTATION_PATCH = "patches/" + axis.INSTRUMENTATION_PATCH
WAVE1_PROOF = "output/env/pegasus/calibration/s3_mocc_mutation_proof.json"
LEGACY_PROOF = wave1.LEGACY_PROOF
PROOF_PATH = "output/env/pegasus/calibration/s3_mocc_template_proof.json"
SCHEMA = "s3-mocc-template-proof/v1"
DRIVER_ID = "orchestrator.campaign.s3_mocc_template_proof"
BENIGN = "  return !(temp < threshold);"
IDENTITY_CLAIM = "実 resolver (source_digest) が定める正規化前処理 source identity の stock 一致"
TRACE0_CLAIM = "TRACE=0 の論理行・非空本文列の一致。TRACE=1 検査本文の有効性は保証しない。"
MATRIX = tuple({"run_name": f"template_stock_{work.lower()}_{regime}_t{thread}",
                "build": "B", "workload": work, "regime": regime,
                "thread": thread, "acceptance": "required"}
               for work in ("W", "U") for regime in wave1.REGIMES for thread in (1, 4))
CHECK_KEYS = (
    *(cell["run_name"] + "_certified_and_silent" for cell in MATRIX),
    "matrix_runs_complete_and_terminated", "template_off_stock_identity",
    "template_on_benign_identity_distinct", "trace0_logical_rows_identical",
    "trace0_nm_izanagi_zero", "trace0_strings_izanagi_trace_zero", "toolchain_matches_policy",
    "template_touch_set_is_exact", "instrumentation_touch_set_is_transaction_only",
    "instrumentation_body_preserved", "auditor_definition_read_only_and_projection",
    "auditor_mocc_items_present", "quarantine_accepts_benign_hole",
    "quarantine_rejects_frozen_frame_and_outside_edits", "auditor_digest_and_deny_only_controls",
    "consumer_binding_controls", "wave1_proof_bound_and_all_pass", "legacy_proof_bound_and_all_pass",
)
QUARANTINE_EXPECTED = (
    ("benign", True, None), ("stock-frame", False, "frame-altered"),
    *((key, False, "outside-region") for key in ("fallback", "CLL", "RLL", "validation", "X", "P", "write-registration", "RLL-write-registration")),
    ("directive", False, "hole-escape"), ("comment-splice", False, "hole-escape"),
    ("bad-anchor", False, "malformed"),
)
DENY_EXPECTED = ("matching-pass", "mismatched-digest", "reject-or-uncertain", "machine-reject-preserved")
_run_checked = legacy._run_checked
_sha256_file = legacy._sha256_file


def _apply_template_patch(root, source):
    patch = root / TEMPLATE_PATCH
    touched = patch_files(str(patch), str(source))
    if len(touched) != 2 or set(touched) != axis.TEMPLATE_TOUCH_SET:
        raise RuntimeError("template touch set differs")
    apply_patch(str(patch), str(source))
    return touched


def _require_condition_gate(source_root, configure_args, cxx):
    captured = condition_meaning_gate.capture_define_inputs(source_root, configure_args=tuple(configure_args))
    request = condition_meaning_gate.make_define_request(driver_id=DRIVER_ID,
        macro=axis.FLAG, requested_value=1, default_value=0)
    with condition_meaning_gate._configured_define_compile_commands(captured, request=request, cxx=cxx, cmake="cmake") as commands:
        supply = condition_meaning_gate.evaluate_define_supply_effectuation(captured, request=request, cxx=cxx, cmake="cmake", configured_commands=commands)
        meaning = condition_meaning_gate.evaluate_define_runtime_meaning(captured, request=request,
            declaration=condition_meaning_gate.declare_define_runtime_meaning(request), cxx=cxx, cmake="cmake", configured_commands=commands)
    admission = condition_meaning_gate.require_condition_gate_family([supply], [meaning], use_class="raw-measurement")
    if not admission.admitted:
        raise RuntimeError("MOCC template condition gate rejected")
    return {"macro": axis.FLAG, "driver_id": DRIVER_ID,
            "supply": json.loads(supply.canonical_json()), "meaning": json.loads(meaning.canonical_json()),
            "admission": json.loads(admission.canonical_json())}


def _build_variant(source_root, build_root, *, trace, toolchain, dependencies, enabled=False):
    args = legacy._common_configure_args(trace=trace, toolchain=toolchain, dependencies=dependencies)
    if enabled:
        args.append("-DCCBENCH_MOCC_TEMP_PREDICATE=1")
    gate = _require_condition_gate(source_root, args, str(toolchain["cxx_path"])) if enabled else None
    _run_checked(["cmake", "-S", str(source_root), "-B", str(build_root),
                  f"-DCMAKE_CXX_COMPILER={toolchain['cxx_path']}", *args])
    _run_checked(["cmake", "--build", str(build_root), "--target", "ycsb_mocc.exe", "-j",
                  str(site_policy.default_build_jobs(site_policy.current_site()))], timeout=900.0)
    binary = build_root / "cc/mocc/ycsb_mocc.exe"
    if not binary.is_file():
        raise RuntimeError("missing MOCC binary")
    return binary, gate


def _set_hole(source, expr=BENIGN):
    path = source / SOURCE_REL
    marker = parse_template_file(str(path), axis.MARKER_ID)
    assert marker is not None and len(marker.hole_text) == 1
    lines = path.read_text().splitlines(keepends=True)
    index = marker.hole_first - 1
    assert lines[index].rstrip("\n") == axis.FROZEN_TEMPLATE_HOLE_BYTES.decode()
    assert "\n" not in expr and "\r" not in expr
    lines[index] = expr + "\n"
    path.write_text("".join(lines))


def _preprocess_trace_zero(source, cxx, enabled):
    stripped = re.sub(r"(?m)^[ \t]*#[ \t]*include\b.*$", "", source)
    with tempfile.TemporaryDirectory(prefix="mocc-template-logical-") as raw:
        directory = Path(raw)
        (directory / "source.cc").write_text(stripped)
        output = _run_checked([cxx, "-E", "-nostdinc", "-Werror=undef", "-DTRACE=0", "-DRWLOCK",
            "-DADD_ANALYSIS=0", "-DBACK_OFF=0", "-DKEY_SORT=0", "-DTEMPERATURE_RESET_OPT=1",
            "-DMASSTREE_USE=1", "-DLinux", "-DKEY_SIZE=8", "-DVAL_SIZE=4",
            f"-DMOCC_TEMP_PREDICATE={int(enabled)}", "-x", "c++", "source.cc"], cwd=directory).stdout
    return wave1._logical_nonempty_rows(output)


def instrumentation_preservation(old_patch, new_patch, stock_source, template_source):
    """Compare actual patch bytes; derive restoration offsets from source alignment."""
    def parse(data):
        lines = data.splitlines(keepends=True)
        body = [line for line in lines if line.startswith(b"+") and not line.startswith((b"+++", b"+#line "))]
        restores = [int(line.split()[1]) for line in lines if line.startswith(b"+#line ")]
        contexts = []
        for hunk in re.split(rb"(?m)^@@[^\n]*\n", data)[1:]:
            rows = hunk.splitlines(keepends=True)
            indices = [i for i, line in enumerate(rows) if line.startswith(b"+")]
            if not indices:
                contexts.append(None)
            else:
                before = next((rows[i] for i in range(indices[0]-1, -1, -1) if rows[i].startswith(b" ")), None)
                after = next((rows[i] for i in range(indices[-1]+1, len(rows)) if rows[i].startswith(b" ")), None)
                contexts.append((before, after))
        return body, restores, contexts
    old, new = parse(old_patch), parse(new_patch)
    mapping = {}
    for tag, i, j, k, l in difflib.SequenceMatcher(None, stock_source.splitlines(), template_source.splitlines(), autojunk=False).get_opcodes():
        if tag == "equal":
            mapping.update({x+1: k+x-i+1 for x in range(i,j)})
    offsets = [mapping[n] - n if n in mapping else None for n in old[1]]
    return {"old_sha256": hashlib.sha256(old_patch).hexdigest(), "new_sha256": hashlib.sha256(new_patch).hexdigest(),
            "added_body_identical": bool(old[0]) and old[0] == new[0],
            "operation_contexts_identical": len(old[2]) == len(new[2]) == 6 and old[2] == new[2],
            "line_restorations_match": len(old[1]) == len(new[1]) == 7 and all(offset is not None and b == a + offset for a,b,offset in zip(old[1],new[1],offsets)),
            "old_lines": old[1], "new_lines": new[1], "offsets": offsets}


def _diff(before, after):
    return "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                     fromfile="a/"+SOURCE_REL, tofile="b/"+SOURCE_REL))


def quarantine_controls(source, instrumented_source):
    def evaluate(head, old, new):
        assert head.count(old) == 1, repr(old)
        diff = _diff(head, head.replace(old, new))
        return evaluate_diff(head, diff), diff
    def evaluate_diff(head, diff):
        with tempfile.TemporaryDirectory(prefix="mocc-quarantine-") as raw:
            path = Path(raw) / "transaction.cc"
            path.write_text(head)
            marker = parse_template_file(str(path), axis.MARKER_ID)
            assert marker is not None
            marker.source_rel = SOURCE_REL
            return DiffQuarantine(marker, diff, head).validate()
    seed = "#if MOCC_TEMP_PREDICATE\n  return temp >= threshold;\n#else"
    cases = {
        "benign": (source, seed, "#if MOCC_TEMP_PREDICATE\n"+BENIGN+"\n#else"),
        "stock-frame": (source, "#else\n  return temp >= threshold;", "#else\n  return temp > threshold;"),
        "fallback": (source, "    if (mocc_is_hot(loadepot.temp, FLAGS_temp_threshold) || (*itr).failed_verification_) {", "    if (mocc_is_hot(loadepot.temp, FLAGS_temp_threshold)) {"),
        "CLL": (source, "\n  CLL_.clear();", "\n  CLL_.resize(0);"),
        "RLL": (source, "  sort(RLL_.begin(), RLL_.end());", "  RLL_.clear();"),
        "validation": (source, "    lock((*itr).rcdptr_, true);", ""),
        "X": (instrumented_source, "    if (!izanagi_cll_has_writer ||", "    if (false ||"),
        "P": (instrumented_source, "  const std::size_t izanagi_pre_sort_size = write_set_.size();", "  const std::size_t izanagi_pre_sort_size = 0;"),
        "write-registration": (source, "  write_set_.emplace_back(s, key, tuple, std::move(body), OpType::UPDATE);", ""),
        "RLL-write-registration": (source, "    RLL_.emplace_back((*itr).rcdptr_, &((*itr).rcdptr_->rwlock_), true);", ""),
        "directive": (source, seed, "#if MOCC_TEMP_PREDICATE\n#if 1\n  return true;\n#else"),
        "comment-splice": (source, seed, "#if MOCC_TEMP_PREDICATE\n  return true; /* // \\\n#else"),
    }
    records, results, diffs = {}, {}, {}
    for name,(head,old,new) in cases.items():
        result,diff = evaluate(head,old,new)
        results[name],diffs[name] = result,diff
        records[name] = {"base_sha256": hashlib.sha256(head.encode()).hexdigest(), "diff_sha256": compute_diff_digest(diff),
                         "passed": result.passed, "subtype": result.subtype.value if result.subtype else None}
    bad = diffs["benign"].replace("-  return temp >= threshold;", "-  return false;")
    result = evaluate_diff(source,bad)
    records["bad-anchor"] = {"base_sha256": hashlib.sha256(source.encode()).hexdigest(), "diff_sha256": compute_diff_digest(bad),
                             "passed": result.passed, "subtype": result.subtype.value if result.subtype else None}
    def veto(machine, verdict, diff):
        return apply_mandatory_deny_only_veto(machine, verdict, diff, diff_region=axis.MARKER_ID, template_diff_id=TEMPLATE_PATCH)
    benign, diff = results["benign"], diffs["benign"]
    digest = compute_diff_digest(diff)
    controls = {"matching-pass": veto(benign, AuditorVerdict("pass",digest),diff) is benign}
    try:
        veto(benign, AuditorVerdict("pass","0"*64), diff)
        controls["mismatched-digest"] = False
    except AuditorGateFailure:
        controls["mismatched-digest"] = True
    controls["reject-or-uncertain"] = (not veto(benign, AuditorVerdict("uncertain",digest,uncertainty="insufficient evidence"),diff).passed
        and not veto(benign, AuditorVerdict("reject",digest,violations=[{"type":16,"reason":"read contract"}]),diff).passed)
    rejected = results["validation"]
    controls["machine-reject-preserved"] = veto(rejected, AuditorVerdict("pass",digest),diff) is rejected
    return {"cases": records, "deny_only": controls}


def binding_record(root):
    return {"schema_version": SCHEMA, "ccbench_commit": PROOF_PIN,
            "template": {"path": TEMPLATE_PATCH, "sha256": _sha256_file(root/TEMPLATE_PATCH),
                "source_rel": SOURCE_REL, "marker_id": axis.MARKER_ID, "flag": axis.FLAG,
                "touch_set": sorted(axis.TEMPLATE_TOUCH_SET)},
            "patches": {"instrumentation": {"path": INSTRUMENTATION_PATCH, "sha256": _sha256_file(root/INSTRUMENTATION_PATCH)},
                        "legacy_instrumentation": {"path": legacy.INSTRUMENTATION_PATCH, "sha256": _sha256_file(root/legacy.INSTRUMENTATION_PATCH)}}}


def consumer_binding_controls(root, proof):
    args = dict(repo_root=root, source_rel=SOURCE_REL, template_patch=TEMPLATE_PATCH,
                ccbench_commit=PROOF_PIN, instrumentation_patch=INSTRUMENTATION_PATCH)
    results = {}
    for name, override in (("alias-rejected", {"template_patch": "elsewhere/"+axis.TEMPLATE_PATCH}),
                           ("wrong-oid-rejected", {"ccbench_commit": axis.PIN})):
        try:
            axis.require_proof_binding(proof, **{**args, **override})
            results[name] = False
        except axis.MoccProofBindingError:
            results[name] = True
    axis.require_proof_binding(proof, repo_root=root, source_rel="cc/mocc/transaction.cc",
        template_patch="patches/mocc-temperature-predicate-variant.patch",
        ccbench_commit="e9e477ca1b55348ab4530de0b1cf663ce4555290",
        instrumentation_patch="patches/instr-mocc-lock-coverage-temperature.patch")
    results["literal-accepted-and-marker-detected"] = axis.introduces_mocc_marker((root/TEMPLATE_PATCH).read_text())
    return results


def _proof_reference(root, relative, keys):
    proof = json.loads((root/relative).read_text())
    return {"path": relative, "sha256": _sha256_file(root/relative),
            "all_pass": proof.get("all_pass"), "checks": proof.get("checks", {}),
            "required_checks": list(keys)}


def _matrix_complete(runs):
    if set(runs) != {cell["run_name"] for cell in MATRIX}:
        return False
    for cell in MATRIX:
        run = runs[cell["run_name"]]
        if any(run[key] != cell[key] for key in ("build","workload","regime","thread","acceptance")):
            return False
        flags = wave1._cell_flags(cell)
        if run["flags"] != flags or run["argv"][1:] != [*(f"-{k}={v}" for k,v in flags.items()), f"-clocks_per_us={wave1.CLK}"] or Path(run["argv"][0]).name != "ycsb_mocc.exe":
            return False
        verifier = run["verifier"]
        argv = verifier["argv"]
        if (len(argv) != 10 or argv[1:3] != ["-m","verifier"] or argv[4:9] != ["--json","--quiet","--protocol","mocc","--ccbench-root"]
                or not Path(argv[3]).is_absolute() or not Path(argv[9]).is_absolute()):
            return False
        if any(process["terminated"] is not True or process["returncode"] != 0
               or process["timed_out"] is not False or process.get("error") is not None for process in (run,verifier)):
            return False
        if not isinstance(verifier["record"], Mapping) or any(run[k] != v or v is None for k,v in wave1._summary(verifier["record"]).items()):
            return False
        if (sum(run["x_reasons"].values()) != run["lock_coverage_violations"]
                or sum(run["p_reasons"].values()) != run["permutation_violations"]):
            return False
    return True


def _condition_gates_valid(gates):
    if len(gates) != 3:
        return False
    for gate in gates:
        if gate["driver_id"] != DRIVER_ID or gate["macro"] != axis.FLAG or gate["admission"]["admitted"] is not True:
            return False
        for arm in ("supply", "meaning"):
            record = gate[arm]
            if record["terminal_status"] != "green" or record["driver_id"] != DRIVER_ID or record["macro"] != axis.FLAG:
                return False
        if gate["supply"]["evidence"]["owner_tu"] != SOURCE_REL:
            return False
        meaning = gate["meaning"]["evidence"]
        if meaning["source_rel"] != SOURCE_REL or meaning["start_directive"] != "#if MOCC_TEMP_PREDICATE // file-scope helper":
            return False
    return True


def _digest(value):
    return isinstance(value,str) and re.fullmatch(r"[0-9a-f]{64}",value) is not None


def _logical_valid(record):
    return (record["logical_rows_identical"] is True and type(record["base_logical_rows_count"]) is int
            and record["base_logical_rows_count"] > 0 and record["base_logical_rows_count"] == record["patched_logical_rows_count"]
            and _digest(record["base_logical_rows_sha256"]) and record["base_logical_rows_sha256"] == record["patched_logical_rows_sha256"])


def compute_checks(proof, policy):
    """Each check derives from observations; incomplete or malformed input is false."""
    checks = {}
    def check(key, predicate):
        try:
            checks[key] = bool(predicate())
        except (KeyError,TypeError,ValueError,AttributeError,IndexError):
            checks[key] = False
    for cell in MATRIX:
        check(cell["run_name"]+"_certified_and_silent", lambda: wave1._silent(proof["runs"][cell["run_name"]], update=cell["workload"]=="U")
              and proof["runs"][cell["run_name"]]["verifier"]["record"]["integrity"]["clean"] is True)
    check("matrix_runs_complete_and_terminated", lambda: _matrix_complete(proof["runs"]) and _condition_gates_valid(proof["condition_gates"]))
    def off():
        i=proof["identity"]
        return (i["claim"] == IDENTITY_CLAIM and _digest(i["stock"]["digest"])
                and i["stock"]["digest"] == i["template_off"]["digest"] == i["template_off"]["baseline"]
                and i["template_off"]["src_token"] == source_digest.STOCK)
    check("template_off_stock_identity", off)
    def on():
        i=proof["identity"]
        return (off() and _digest(i["template_on_b"]["digest"])
                and i["template_on_b"]["digest"] != i["template_off"]["digest"]
                and i["template_on_b"]["src_token"] != source_digest.STOCK
                and _digest(i["template_on_b"]["src_token"])
                and _digest(i["benign_diff_sha256"]) and i["benign_diff_sha256"] == proof["quarantine_controls"]["cases"]["benign"]["diff_sha256"])
    check("template_on_benign_identity_distinct", on)
    check("trace0_logical_rows_identical", lambda: proof["trace0"]["claim"] == TRACE0_CLAIM and all(_logical_valid(proof["trace0"][s]) for s in ("off","on_b")))
    check("trace0_nm_izanagi_zero", lambda: proof["trace0"]["binary"]["nm_izanagi_count"] == 0)
    check("trace0_strings_izanagi_trace_zero", lambda: proof["trace0"]["binary"]["strings_izanagi_trace_count"] == proof["trace0"]["binary"]["strings_izanagi_macro_count"] == 0)
    check("toolchain_matches_policy", lambda: set(proof["toolchain"]["version_body_sha256"]) == {"gcc","g++"}
          and all(_digest(proof["toolchain"]["version_body_sha256"][k]) and proof["toolchain"]["version_body_sha256"][k] == policy["expected_compiler_version_body_sha256"][k] for k in ("gcc","g++")))
    check("template_touch_set_is_exact", lambda: sorted(proof["touch_sets"][TEMPLATE_PATCH]) == sorted(axis.TEMPLATE_TOUCH_SET))
    check("instrumentation_touch_set_is_transaction_only", lambda: proof["touch_sets"][INSTRUMENTATION_PATCH] == [SOURCE_REL])
    check("instrumentation_body_preserved", lambda: all(proof["instrumentation_preservation"][k] is True for k in ("added_body_identical","operation_contexts_identical","line_restorations_match"))
          and proof["instrumentation_preservation"]["old_sha256"] == proof["patches"]["legacy_instrumentation"]["sha256"]
          and proof["instrumentation_preservation"]["new_sha256"] == proof["patches"]["instrumentation"]["sha256"])
    check("auditor_definition_read_only_and_projection", lambda: proof["auditor_definition"]["tools"] == ["Read","Grep","Glob"]
          and set(proof["auditor_definition"]["accepted_runs"]) == {c["run_name"] for c in MATRIX}
          and all(v is True for v in proof["auditor_definition"]["accepted_runs"].values())
          and proof["auditor_definition"]["performance_rejected"] is True
          and set(proof["auditor_definition"]["projections"]) == {c["run_name"] for c in MATRIX}
          and all(axis.auditor_projection(record) == record for record in proof["auditor_definition"]["projections"].values()))
    check("auditor_mocc_items_present", lambda: set(proof["auditor_definition"]["items"]) == {f"{a}_{b}" for a,b in axis.AUDITOR_MOCC_REQUIRED}
          and all(v is True for v in proof["auditor_definition"]["items"].values()))
    def dq(names):
        records=proof["quarantine_controls"]["cases"]
        return set(records) == {n for n,_,_ in QUARANTINE_EXPECTED} and all(records[n]["passed"] is passed and records[n]["subtype"] == subtype for n,passed,subtype in QUARANTINE_EXPECTED if n in names)
    check("quarantine_accepts_benign_hole", lambda: dq({"benign"}))
    check("quarantine_rejects_frozen_frame_and_outside_edits", lambda: dq({n for n,_,_ in QUARANTINE_EXPECTED}-{ "benign"}))
    check("auditor_digest_and_deny_only_controls", lambda: set(proof["quarantine_controls"]["deny_only"]) == set(DENY_EXPECTED) and all(v is True for v in proof["quarantine_controls"]["deny_only"].values()))
    check("consumer_binding_controls", lambda: set(proof["consumer_binding_controls"]) == {"alias-rejected","wrong-oid-rejected","literal-accepted-and-marker-detected"} and all(v is True for v in proof["consumer_binding_controls"].values()))
    for name,path,keys in (("wave1",WAVE1_PROOF,wave1.CHECK_KEYS),("legacy",LEGACY_PROOF,legacy.CHECK_KEYS)):
        check(name+"_proof_bound_and_all_pass", lambda: proof[name+"_proof"]["path"] == path
              and _digest(proof[name+"_proof"]["sha256"]) and proof[name+"_proof"]["all_pass"] is True
              and set(proof[name+"_proof"]["checks"]) == set(keys) and all(v is True for v in proof[name+"_proof"]["checks"].values()))
    assert tuple(checks) == CHECK_KEYS
    return checks


def _auditor_definition(root, runs, attribution):
    from orchestrator.codex_roles.spec import load_role_specs
    spec = load_role_specs(root)["auditor"]
    result = {"path": ".claude/agents/auditor.md", "sha256": _sha256_file(root/".claude/agents/auditor.md"),
              "tools": list(spec.claude_tools), "items": axis.check_auditor_definition((root/".claude/agents/auditor.md").read_text()),
              "accepted_runs": {}, "projections": {}, "performance_rejected": False}
    for name,run in runs.items():
        record = {**attribution, **{k:run[k] for k in ("verdict","certified","total_cycles","lock_coverage_violations","permutation_violations","x_reasons","p_reasons")},
                  "integrity": run["verifier"]["record"]["integrity"]}
        result["projections"][name] = axis.auditor_projection(record)
        result["accepted_runs"][name] = True
        try:
            axis.auditor_projection({**record,"wall_seconds":1.0})
        except ValueError:
            result["performance_rejected"] = True
    return result


def main(argv=None):
    site = site_policy.current_site(require_evidence=True)
    if site_policy.refuses_heavy_work(site):
        print(site_policy.heavy_work_refusal(site, "mocc template proof driver"), file=sys.stderr)
        return 2
    wave1._assert_single_tenant()
    root = legacy._repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--third-party-cache", type=Path, required=True)
    parser.add_argument("--policy", type=Path, default=root/"tools/pegasus/mocc_trace_v1_policy.json")
    parser.add_argument("--out", type=Path, default=root/PROOF_PATH)
    args = parser.parse_args(argv)
    if not args.third_party_cache.is_absolute():
        raise ValueError("--third-party-cache must be absolute")
    policy = legacy._load_policy(args.policy.resolve(strict=True))
    toolchain = legacy._resolve_toolchain(policy)
    proof = {**binding_record(root), "env_tag": legacy.ENV_TAG, "site": site, "toolchain": toolchain,
        "genome": legacy.STOCK_G.canonical(), "clocks_per_us": legacy.CLK,
        "workloads": {"W": {"single": wave1.SINGLE_FLAGS, "high": wave1.HIGH_FLAGS},
                      "U": {"single": wave1.U_SINGLE_FLAGS, "high": wave1.U_HIGH_FLAGS}},
        "regimes": dict(wave1.REGIMES), "runs": {}, "touch_sets": {}, "condition_gates": [],
        "identity": {}, "trace0": {}, "quarantine_controls": {}, "auditor_definition": {},
        "instrumentation_preservation": {}, "consumer_binding_controls": {},
        "wave1_proof": {}, "legacy_proof": {},
        "diagnostic_build_admission": non_admissible_materializer(DRIVER_ID+"._build_variant")}
    def save():
        proof["checks"] = compute_checks(proof, policy)
        proof["all_pass"] = all(proof["checks"].values()) and len(proof["runs"]) == 12
        wave1._save_json(args.out, proof)
    save()
    proof["wave1_proof"] = _proof_reference(root, WAVE1_PROOF, wave1.CHECK_KEYS)
    proof["legacy_proof"] = _proof_reference(root, LEGACY_PROOF, legacy.CHECK_KEYS)
    proof["hot_path_evidence"] = {"method": "reference-wave1-negative-control",
        "reference": {k: proof["wave1_proof"][k] for k in ("path", "sha256")}}
    proof["consumer_binding_controls"] = consumer_binding_controls(root, proof)
    save()
    with tempfile.TemporaryDirectory(prefix="mocc-template-proof-") as raw:
        scratch = Path(raw)
        dependencies = legacy._prepare_dependencies(root, policy, args.third_party_cache, scratch, toolchain)
        with checkout(PROOF_PIN, base_dir=str(root/"external/ccbench")) as value:
            source = Path(value)
            stock = (source/SOURCE_REL).read_text()
            cxx = str(toolchain["cxx_path"])
            base = source_digest.baseline(legacy.STOCK_G, PROOF_PIN, str(source), cxx)
            stock_digest = source_digest.compute(legacy.STOCK_G, str(source), cxx)
            _build_variant(source, scratch/"build-stock", trace=0, toolchain=toolchain, dependencies=dependencies)
            proof["touch_sets"][TEMPLATE_PATCH] = _apply_template_patch(root, source)
            template = (source/SOURCE_REL).read_text()
            off = {"digest": source_digest.compute(legacy.STOCK_G, str(source), cxx), "baseline": base,
                   "src_token": source_digest.resolve(legacy.STOCK_G, PROOF_PIN, str(source), cxx)}
            _build_variant(source, scratch/"build-off00", trace=0, toolchain=toolchain, dependencies=dependencies)
            off_rows = _preprocess_trace_zero(template, cxx, False)
            _set_hole(source)
            benign = (source/SOURCE_REL).read_text()
            on_g = Genome("mocc", {**legacy.STOCK_G.flags, axis.FLAG: 1})
            on = {"digest": source_digest.compute(on_g, str(source), cxx),
                  "baseline": source_digest.baseline(on_g, PROOF_PIN, str(source), cxx),
                  "src_token": source_digest.resolve(on_g, PROOF_PIN, str(source), cxx)}
            proof["identity"] = {"claim": IDENTITY_CLAIM, "stock": {"digest": stock_digest},
                "template_off": off, "template_on_b": on,
                "benign_diff_sha256": compute_diff_digest(_diff(template, benign))}
            on_binary, gate = _build_variant(source, scratch/"build-on000", trace=0,
                enabled=True, toolchain=toolchain, dependencies=dependencies)
            proof["condition_gates"].append(gate)
            on_rows = _preprocess_trace_zero(benign, cxx, True)
            proof["touch_sets"][INSTRUMENTATION_PATCH] = legacy._apply_owned_patch(root, source, INSTRUMENTATION_PATCH)
            instrumented = (source/SOURCE_REL).read_text()
            seed_inst = instrumented.replace(BENIGN, axis.FROZEN_TEMPLATE_HOLE_BYTES.decode(), 1)
            proof["trace0"] = {"claim": TRACE0_CLAIM,
                "off": wave1._logical_rows_record(off_rows, _preprocess_trace_zero(seed_inst, cxx, False)),
                "on_b": wave1._logical_rows_record(on_rows, _preprocess_trace_zero(instrumented, cxx, True))}
            proof["instrumentation_preservation"] = instrumentation_preservation(
                (root/legacy.INSTRUMENTATION_PATCH).read_bytes(), (root/INSTRUMENTATION_PATCH).read_bytes(), stock, template)
            proof["quarantine_controls"] = quarantine_controls(template, seed_inst)
            save()
            inst_binary, gate = _build_variant(source, scratch/"build-inst0", trace=0,
                enabled=True, toolchain=toolchain, dependencies=dependencies)
            proof["condition_gates"].append(gate)
            proof["trace0"]["binary"] = legacy._trace0_record(on_binary, inst_binary)
            binary, gate = _build_variant(source, scratch/"build-trace", trace=1,
                enabled=True, toolchain=toolchain, dependencies=dependencies)
            proof["condition_gates"].append(gate)
            save()
            for cell in MATRIX:
                wave1._variant_run(binary, cell, source, proof["runs"], save)
            attribution = {"base_sha256": hashlib.sha256(seed_inst.encode()).hexdigest(),
                "source_sha256": _sha256_file(source/SOURCE_REL),
                "diff_sha256": compute_diff_digest(_diff(seed_inst, instrumented)),
                "macro_context": {axis.FLAG: 1, "TRACE": 1, "RWLOCK": 1, "TEMPERATURE_RESET_OPT": 1, "KEY_SORT": 0}}
            assert seed_inst.replace(axis.FROZEN_TEMPLATE_HOLE_BYTES.decode(), BENIGN, 1) == instrumented
            proof["auditor_definition"] = _auditor_definition(root, proof["runs"], attribution)
            save()
    print(f"all_pass={proof['all_pass']} -> {args.out}")
    return 0 if proof["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
