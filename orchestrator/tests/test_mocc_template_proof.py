"""Template-specific evidence contracts, using real patches and registries."""
from contextlib import contextmanager
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from orchestrator.campaign import axis_mocc_temperature as A
from orchestrator.campaign import s3_mocc_template_proof as M
from orchestrator.campaign import condition_meaning_gate as G
from orchestrator.campaign import source_digest
from orchestrator.campaign.model import Genome

ROOT = Path(__file__).resolve().parents[2]


@contextmanager
def _source_root(*patches):
    with tempfile.TemporaryDirectory(prefix="mocc-template-test-") as raw:
        root = Path(raw)
        archive = subprocess.run(["git", "-C", str(ROOT/"external/ccbench"), "archive", A.PROOF_PIN],
                                 check=True, capture_output=True).stdout
        subprocess.run(["tar", "-x", "-C", raw], input=archive, check=True)
        subprocess.run(["git", "init", "-q", raw], check=True)
        # Expose existing read-only objects to this isolated repository, without
        # changing the shared checkout or creating any new commit.
        git = ROOT/"external/ccbench/.git"
        if git.is_file():
            git = (git.parent/git.read_text().strip().removeprefix("gitdir: ")).resolve()
        common = git/"commondir"
        if common.is_file():
            git = (git/common.read_text().strip()).resolve()
        (root/".git/objects/info/alternates").write_text(str(git/"objects")+"\n")
        for patch in patches:
            for option in (("--check",), ()):
                subprocess.run(["git", "-C", raw, "apply", *option, str(ROOT/patch)],
                               check=True, capture_output=True)
        yield root


def _reject(call, exception=ValueError):
    try:
        call()
    except exception:
        return
    raise AssertionError("rejection control was accepted")


def _consumer():
    path = ROOT/M.PROOF_PATH
    assert path.is_file(), f"required compute proof absent: {path}"
    proof = json.loads(path.read_text())
    assert set(proof) == {
        "schema_version", "env_tag", "site", "ccbench_commit", "toolchain", "genome",
        "clocks_per_us", "workloads", "regimes", "template", "patches", "wave1_proof",
        "legacy_proof", "identity", "trace0", "quarantine_controls", "auditor_definition",
        "consumer_binding_controls", "condition_gates", "diagnostic_build_admission",
        "runs", "checks", "all_pass", "instrumentation_preservation", "hot_path_evidence", "touch_sets",
    }
    A.require_proof_binding(proof, repo_root=ROOT, source_rel=A.SOURCE_REL,
        template_patch=M.TEMPLATE_PATCH, ccbench_commit=A.PROOF_PIN,
        instrumentation_patch=M.INSTRUMENTATION_PATCH)
    assert proof["all_pass"] is True
    assert tuple(proof["checks"]) == M.CHECK_KEYS
    assert all(v is True for v in proof["checks"].values())
    policy = M.legacy._load_policy(ROOT/"tools/pegasus/mocc_trace_v1_policy.json")
    assert proof["checks"] == M.compute_checks(proof, policy)
    for key, relative, keys in (("wave1_proof", M.WAVE1_PROOF, M.wave1.CHECK_KEYS),
                                ("legacy_proof", M.LEGACY_PROOF, M.legacy.CHECK_KEYS)):
        assert proof[key] == M._proof_reference(ROOT, relative, keys)
    assert proof["hot_path_evidence"] == {"method": "reference-wave1-negative-control",
        "reference": {k: proof["wave1_proof"][k] for k in ("path", "sha256")}}
    from orchestrator.codex_roles.spec import load_role_specs
    assert load_role_specs(ROOT)["auditor"].claude_tools == ("Read", "Grep", "Glob")
    assert proof["auditor_definition"]["sha256"] == M._sha256_file(ROOT/".claude/agents/auditor.md")
    assert all(A.check_auditor_definition((ROOT/".claude/agents/auditor.md").read_text()).values())
    assert len(proof["condition_gates"]) == 3
    for gate in proof["condition_gates"]:
        assert gate["driver_id"] == M.DRIVER_ID and gate["macro"] == A.FLAG
        assert gate["admission"]["admitted"] is True
        for arm in ("supply", "meaning"):
            assert gate[arm]["terminal_status"] == "green"
            assert gate[arm]["driver_id"] == "orchestrator.campaign.s3_mocc_template_proof"
        assert gate["supply"]["evidence"]["owner_tu"] == "cc/mocc/transaction.cc"
        assert gate["meaning"]["evidence"]["source_rel"] == "cc/mocc/transaction.cc"
    assert M._condition_gates_valid(proof["condition_gates"])
    assert M._matrix_complete(proof["runs"])


def test_mocc_mutation_surface_requires_auditor_live():
    patches = [p.read_text() for p in (ROOT/"patches").glob("*.patch")]
    if any(A.introduces_mocc_marker(p) for p in patches) or A.mocc_axis_modules(ROOT/"orchestrator/campaign"):
        _consumer()


def test_mocc_template_proof_json_is_complete_and_bound():
    _consumer()


def test_mocc_template_gate_activation_controls():
    template = (ROOT/M.TEMPLATE_PATCH).read_text()
    traces = [p.read_text() for p in (ROOT/"patches").glob("*.patch") if p.name != A.TEMPLATE_PATCH]
    modules = A.mocc_axis_modules(ROOT/"orchestrator/campaign")
    assert modules == (A,)
    for patches, axes, expected in ((traces+[template], (), True), (traces, modules, True),
                                     (traces+[template], modules, True), (traces, (), False)):
        assert (any(A.introduces_mocc_marker(p) for p in patches) or bool(axes)) is expected


def test_mocc_template_consumer_binding_controls():
    proof = M.binding_record(ROOT)
    assert M.consumer_binding_controls(ROOT, proof) == {
        "alias-rejected": True, "wrong-oid-rejected": True,
        "literal-accepted-and-marker-detected": True}
    with tempfile.TemporaryDirectory(prefix="mocc-alias-control-") as raw:
        temporary = Path(raw)
        (temporary/"elsewhere").mkdir()
        alias = temporary/"elsewhere"/A.TEMPLATE_PATCH
        alias.write_bytes((ROOT/M.TEMPLATE_PATCH).read_bytes())
        assert alias.read_bytes() == (ROOT/M.TEMPLATE_PATCH).read_bytes()
        _reject(lambda: A.require_proof_binding(proof, repo_root=temporary,
            source_rel=A.SOURCE_REL, template_patch="elsewhere/"+A.TEMPLATE_PATCH,
            ccbench_commit=A.PROOF_PIN, instrumentation_patch=M.INSTRUMENTATION_PATCH), A.MoccProofBindingError)
    for target in ("template", "instrumentation"):
        changed = copy.deepcopy(proof)
        record = changed["template"] if target == "template" else changed["patches"][target]
        record["sha256"] = "0"*64
        _reject(lambda: A.require_proof_binding(changed, repo_root=ROOT, source_rel=A.SOURCE_REL,
            template_patch=M.TEMPLATE_PATCH, ccbench_commit=A.PROOF_PIN,
            instrumentation_patch=M.INSTRUMENTATION_PATCH), A.MoccProofBindingError)


def test_mocc_temperature_axis_contract():
    assert A.PIN != A.PROOF_PIN and A.PIN == A.pin.CURRENT_PIN
    with _source_root(M.TEMPLATE_PATCH) as root:
        text = (root/A.SOURCE_REL).read_text()
        marker = M.parse_template_file(str(root/A.SOURCE_REL), A.MARKER_ID)
        assert marker is not None
        lines = text.splitlines(True)
        assert "".join(lines[marker.begin_line-1:marker.end_line]).encode() == A.FROZEN_TEMPLATE_BLOCK_BYTES
        assert list(marker.hole_text.values()) == [A.FROZEN_TEMPLATE_HOLE_BYTES.decode()]
        assert text.count("#if MOCC_TEMP_PREDICATE // file-scope helper") == 1
        assert text.count("inline bool mocc_is_hot(std::uint64_t temp, std::uint64_t threshold)") == 1
        assert text.count("mocc_is_hot(loadepot.temp, FLAGS_temp_threshold)") == 4
        assert "mocc_is_hot(loadepot.temp, FLAGS_temp_threshold) || (*itr).failed_verification_" in text
    assert "IZANAGI_" not in (ROOT/M.TEMPLATE_PATCH).read_text()


def test_mocc_template_quarantine_controls():
    with _source_root(M.TEMPLATE_PATCH) as root:
        source = (root/A.SOURCE_REL).read_text()
        M.legacy._apply_owned_patch(ROOT, root, M.INSTRUMENTATION_PATCH)
        instrumented = (root/A.SOURCE_REL).read_text()
    result = M.quarantine_controls(source, instrumented)
    expected = {"benign": (True, None), "stock-frame": (False, "frame-altered"),
        **{key: (False, "outside-region") for key in ("fallback", "CLL", "RLL", "validation", "X", "P", "write-registration", "RLL-write-registration")},
        "directive": (False, "hole-escape"), "comment-splice": (False, "hole-escape"),
        "bad-anchor": (False, "malformed")}
    assert {k: (r["passed"], r["subtype"]) for k,r in result["cases"].items()} == expected
    assert result["deny_only"] == {"matching-pass": True, "mismatched-digest": True,
        "reject-or-uncertain": True, "machine-reject-preserved": True}


def test_mocc_template_instrumentation_logical_rows():
    with _source_root(M.TEMPLATE_PATCH) as root:
        source = (root/A.SOURCE_REL).read_text()
        M.legacy._apply_owned_patch(ROOT, root, M.INSTRUMENTATION_PATCH)
        instrumented = (root/A.SOURCE_REL).read_text()
    for enabled in (False, True):
        a, b = source, instrumented
        if enabled:
            a = a.replace(A.FROZEN_TEMPLATE_HOLE_BYTES.decode(), M.BENIGN, 1)
            b = b.replace(A.FROZEN_TEMPLATE_HOLE_BYTES.decode(), M.BENIGN, 1)
        rows = M._preprocess_trace_zero(a, "g++", enabled)
        assert rows == M._preprocess_trace_zero(b, "g++", enabled)
        if not enabled:
            assert all("mocc_is_hot" not in line for _,line in rows)
        assert rows != M._preprocess_trace_zero(b.replace("#line 1204", "#line 1205"), "g++", enabled)


def test_mocc_template_instrumentation_preserves_body():
    with _source_root() as root:
        stock = (root/A.SOURCE_REL).read_text()
        M._apply_template_patch(ROOT, root)
        template = (root/A.SOURCE_REL).read_text()
    old = (ROOT/M.legacy.INSTRUMENTATION_PATCH).read_bytes()
    new = (ROOT/M.INSTRUMENTATION_PATCH).read_bytes()
    result = M.instrumentation_preservation(old, new, stock, template)
    keys = ("added_body_identical", "operation_contexts_identical", "line_restorations_match")
    assert all(result[k] for k in keys)
    with _source_root(M.TEMPLATE_PATCH, M.INSTRUMENTATION_PATCH) as root:
        text = (root/A.SOURCE_REL).read_text()
    start = text.index("#if TRACE\n    if ((*itr).op_ != OpType::INSERT &&")
    end = text.index("#line 1230\n", start) + len("#line 1230\n")
    block = text[start:end]
    moved = text[:start] + text[end:]
    operation = "    __atomic_store_n(&((*itr).rcdptr_->tidword_.obj_), maxtid.obj_,\n                     __ATOMIC_RELEASE);\n"
    assert moved.count(operation) == 1
    moved = moved.replace(operation, operation+block)
    moved_patch = M._diff(template, moved).encode()
    assert M.instrumentation_preservation(old, moved_patch, stock, template)["operation_contexts_identical"] is False
    for bad in (new.replace(b"if (!izanagi_cll_has_writer ||", b"if (false && !izanagi_cll_has_writer ||"),
                new.replace(b"if (!izanagi_perm_ok)", b"if (false && !izanagi_perm_ok)"),
                moved_patch,
                new.replace(b"+#line 1204", b"+#line 1205")):
        assert bad != new
        record = M.instrumentation_preservation(old, bad, stock, template)
        assert not all(record[k] for k in keys)


def _projection():
    record = {"base_sha256": "1"*64, "source_sha256": "2"*64, "diff_sha256": "3"*64,
        "macro_context": {"MOCC_TEMP_PREDICATE": 1, "TRACE": 1, "RWLOCK": 1, "TEMPERATURE_RESET_OPT": 1, "KEY_SORT": 0},
        "verdict": "serializable", "certified": True, "total_cycles": 0,
        "lock_coverage_violations": 0, "permutation_violations": 0, "x_reasons": {}, "p_reasons": {},
        "integrity": {k: 0 for k in ("orphan_reads", "version_dups", "dup_txids", "genesis_commits", "missing_txids",
            "write_version_mismatch", "malformed_keys", "framing_violations", "framing_violation_details",
            "write_intent_violations", "lock_coverage_violations", "permutation_violations", "clean", "permutation_violation_details", "notes")}}

    record["integrity"].update(clean=True, notes=[], framing_violation_details=[],
        permutation_violation_details={"counts": {"size-changed": 0, "rcdptr-set-changed": 0, "unknown": 0},
                                       "sample": [], "unknown_reason_sample": []})
    return record


def test_mocc_auditor_projection_rejects_performance_fields():
    record = _projection()
    assert A.auditor_projection(record) == record
    for field in ("wall_seconds", "txns", "non_insert_writes", "read_rows", "throughput", "fitness", "WAL", "expected_verdict", "unknown"):
        _reject(lambda: A.auditor_projection({**record, field: 1}))
        bad = copy.deepcopy(record)
        bad["integrity"][field] = 1
        _reject(lambda: A.auditor_projection(bad))


def test_mocc_auditor_definition_items_are_item_scoped():
    text = (ROOT/".claude/agents/auditor.md").read_text()
    assert all(A.check_auditor_definition(text).values())
    for (section, number), sentence in A.AUDITOR_MOCC_REQUIRED.items():
        assert text.count(sentence) == 1
        removed = text.replace(sentence, "")
        assert A.check_auditor_definition(removed)[f"{section}_{number}"] is False
        moved = removed + "\n## Misplaced text\n" + sentence
        assert A.check_auditor_definition(moved)[f"{section}_{number}"] is False


def test_mocc_template_condition_gate_uses_new_driver_id():
    spec = G.DEFINE_SPECS["MOCC_TEMP_PREDICATE"]
    assert spec.route == G.ROUTE_CMAKE_CACHE
    assert spec.owner_tus == ("cc/mocc/transaction.cc",)
    assert spec.target == "ycsb_mocc.exe" and spec.patch_rel == M.TEMPLATE_PATCH
    assert G.CONDITIONAL_BRANCH_WITNESSES["MOCC_TEMP_PREDICATE"] == (A.SOURCE_REL, "#if MOCC_TEMP_PREDICATE // file-scope helper")
    request = G.make_define_request(driver_id=M.DRIVER_ID, macro=A.FLAG, requested_value=1, default_value=0)
    assert request.driver_id == "orchestrator.campaign.s3_mocc_template_proof"
    assert A.FLAG in G.RELATED_DEFINE_DECODE_MACROS


def test_mocc_template_checks_are_input_derived():
    assert len(M.CHECK_KEYS) == 30 and len(M.MATRIX) == 12
    checks = M.compute_checks({}, {})
    assert tuple(checks) == M.CHECK_KEYS and not any(checks.values())
    proof = {"identity": {"claim": M.IDENTITY_CLAIM, "stock": {"digest": "1"*64},
        "template_off": {"digest": "1"*64, "baseline": "1"*64, "src_token": "stock"},
        "template_on_b": {"digest": "2"*64, "src_token": "2"*64}, "benign_diff_sha256": "3"*64},
        "quarantine_controls": {"cases": {"benign": {"diff_sha256": "3"*64}}}}
    assert M.compute_checks(proof, {})["template_on_benign_identity_distinct"]
    proof["identity"]["template_on_b"]["digest"] = "1"*64
    assert not M.compute_checks(proof, {})["template_on_benign_identity_distinct"]
    proof = {"auditor_definition": {"tools": ["Read", "Grep", "Glob", "Bash"],
        "accepted_runs": {c["run_name"]: True for c in M.MATRIX}, "performance_rejected": True}}
    assert not M.compute_checks(proof, {})["auditor_definition_read_only_and_projection"]
    runs = {}
    for cell in M.MATRIX:
        flags = M.wave1._cell_flags(cell)
        process = {"terminated": True, "timed_out": False, "returncode": 0, "error": None}
        raw = {"verdict": "serializable", "certified": True, "total_cycles": 0,
               "stats": {"txns": 2}, "integrity": _projection()["integrity"]}
        runs[cell["run_name"]] = {**cell, **process, **M.wave1._summary(raw),
            "flags": flags, "argv": ["/tmp/ycsb_mocc.exe", *(f"-{k}={v}" for k,v in flags.items()), "-clocks_per_us=2100"],
            "verifier": {**process, "record": raw,
                "argv": ["python3", "-m", "verifier", "/tmp/trace", "--json", "--quiet", "--protocol", "mocc", "--ccbench-root", "/tmp/source"]},
            "x_reasons": {}, "p_reasons": {}, "non_insert_writes": 2, "read_rows": 0}
    assert M._matrix_complete(runs)
    assert all(M.compute_checks({"runs": runs}, {})[c["run_name"]+"_certified_and_silent"] for c in M.MATRIX)
    for cell in M.MATRIX:
        name = cell["run_name"]
        for key, value in (("txns", 0), ("non_insert_writes", 0), ("certified", False), ("total_cycles", 1),
                           ("lock_coverage_violations", 1), ("permutation_violations", 1)):
            changed = copy.deepcopy(runs)
            changed[name][key] = value
            assert not M.compute_checks({"runs": changed}, {})[name+"_certified_and_silent"], (name,key)
        for side in ("benchmark", "verifier"):
            for key,value in (("terminated", False), ("timed_out", True), ("returncode", 2)):
                changed = copy.deepcopy(runs)
                process = changed[name] if side == "benchmark" else changed[name]["verifier"]
                process[key] = value
                assert not M._matrix_complete(changed), (name,side,key)
        changed = copy.deepcopy(runs)
        changed[name]["verifier"]["record"]["integrity"]["version_dups"] = 1
        assert not M.compute_checks({"runs": changed}, {})[name+"_certified_and_silent"]


def test_mocc_template_off_matches_stock_and_on_is_distinct():
    with _source_root() as root:
        try:
            base = source_digest.baseline(M.legacy.STOCK_G, A.PROOF_PIN, str(root), "g++")
            M._apply_template_patch(ROOT, root)
            off = source_digest.compute(M.legacy.STOCK_G, str(root), "g++")
            assert base == off
            assert source_digest.resolve(M.legacy.STOCK_G, A.PROOF_PIN, str(root), "g++") == "stock"
            M._set_hole(root)
            genome = Genome("mocc", {**M.legacy.STOCK_G.flags, "MOCC_TEMP_PREDICATE": 1})
            assert source_digest.compute(genome, str(root), "g++") != off
            assert source_digest.resolve(genome, A.PROOF_PIN, str(root), "g++") != "stock"
        except Exception as exc:
            raise AssertionError(f"real source_digest identity unavailable or failed: {type(exc).__name__}: {exc}") from exc


def _run():
    passed = failed = 0
    for name, test in sorted(globals().copy().items()):
        if not name.startswith("test_") or not callable(test):
            continue
        try:
            test()
            print(f"PASS {name}", flush=True)
            passed += 1
        except Exception as exc:
            print(f"FAIL {name}: {type(exc).__name__}: {exc}", flush=True)
            failed += 1
    print(f"{passed} passed, {failed} failed")
    return int(failed != 0)


if __name__ == "__main__":
    sys.exit(_run())
