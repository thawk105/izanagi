"""Real skeleton, API, hand-policy and source identity contracts for D2214."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from skiputil import Skip, skip
from orchestrator.campaign import axis_silo_function_policy as axis
from orchestrator.campaign import diff_quarantine, source_digest
from orchestrator.campaign.silo_policy_compile import find_compiler
from orchestrator.campaign.model import Genome

PATCH = ROOT / "patches" / axis.TEMPLATE_PATCH
CCBENCH = ROOT / "external/ccbench"
API_BEGIN = b"// SILO-FUNCTION-POLICY-API-BEGIN\n"
API_END = b"// SILO-FUNCTION-POLICY-API-END\n"
HOLE_BEGIN = b"// EVOLVE-BLOCK-BEGIN silo-function-policy\n#if SILO_POLICY_VARIANT\n"
HOLE_END = b"#else\n#endif\n// EVOLVE-BLOCK-END silo-function-policy"


def _git(directory, *args):
    return subprocess.check_output(
        ["git", "-C", str(directory), *args], stderr=subprocess.STDOUT,
    )


@contextmanager
def _applied_template():
    # Clone the real pinned objects; never edit the shared submodule or invent a
    # replacement fixture tree/hash. Applying the actual patch is part of the test.
    head = _git(CCBENCH, "rev-parse", "HEAD").decode().strip()
    assert head.startswith(axis.PIN)
    with tempfile.TemporaryDirectory(prefix="silo-policy-template-") as tmp:
        checkout = Path(tmp) / "ccbench"
        subprocess.run(
            ["git", "clone", "--shared", "--no-checkout", str(CCBENCH), str(checkout)],
            check=True, capture_output=True,
        )
        _git(checkout, "checkout", "--detach", head)
        _git(checkout, "apply", "--check", str(PATCH))
        _git(checkout, "apply", str(PATCH))
        yield checkout, head


def _cxx():
    # Same fallback order as test_campaign._any_cxx; compare identities within
    # this compiler, without asserting equality across compiler versions.
    for candidate in ("g++-13", "g++-12", "g++"):
        if shutil.which(candidate):
            return candidate
    skip("C++ toolchain unavailable (g++-13/g++-12/g++)")


def _genome(value):
    return Genome("silo", {
        "BACK_OFF": 1, "NO_WAIT_LOCKING_IN_VALIDATION": 1,
        "NO_WAIT_OF_TICTOC": 0, "WAL": 0, axis.FLAG: value,
    })


def _api_bytes(source):
    assert source.count(API_BEGIN) == source.count(API_END) == 1
    return source.split(API_BEGIN, 1)[1].split(API_END, 1)[0]


def _assert_api_matches(source, header):
    assert _api_bytes(source) == header.read_bytes(), "embedded API differs from header"


def test_patch_touch_set_marker_and_empty_stock():
    patch = PATCH.read_text()
    assert re.findall(r"^diff --git a/(\S+) b/(\S+)$", patch, re.M) == [
        ("cmake/Options.cmake", "cmake/Options.cmake"),
        (axis.SOURCE_REL, axis.SOURCE_REL),
    ]
    with _applied_template() as (checkout, _):
        source = (checkout / axis.SOURCE_REL).read_bytes()
        assert source.count(b"EVOLVE-BLOCK-BEGIN") == 1
        assert source.count(b"EVOLVE-BLOCK-END") == 1
        assert source.count(HOLE_BEGIN) == source.count(HOLE_END) == 1
        options = (checkout / "cmake/Options.cmake").read_text()
        assert 'set(CCBENCH_SILO_POLICY_VARIANT 0 CACHE STRING "izanagi: 0=stock, 1=function policy (EVOLVE-BLOCK, silo only)")' in options
        assert "    SILO_POLICY_VARIANT=${CCBENCH_SILO_POLICY_VARIANT}\n" in options


def test_worker_seed_uses_thid_once_and_keeps_random_sequence():
    with _applied_template() as (checkout, _):
        source = (checkout / axis.SOURCE_REL).read_text()
        tls = source.split("namespace izanagi_silo_skel {\n", 1)[1].split(
            "void wait_us(uint32_t delay) noexcept {", 1)[0]
        tls = tls[tls.index("thread_local uint64_t random_state"):]
        assert "thread_local bool random_seeded" in tls
        assert "void seed_random(uint64_t thid) noexcept" in tls
        assert "uint64_t next_random() noexcept" in tls

        begin = source.split("void TxExecutor::begin() {", 1)[1].split(
            "void TxExecutor::", 1)[0]
        branch = begin.split("#if SILO_POLICY_VARIANT\n", 1)[1].split("#endif", 1)[0]
        call = "::izanagi_silo_skel::seed_random(thid_);"
        assert branch.count(call) == 1, "begin must seed from its worker thid_"
        begin_seed = branch.split("::izanagi_silo_skel::reason =", 1)[0]
        assert call in begin_seed

        compiler = find_compiler()
        if compiler is None:
            skip("C++ toolchain unavailable (g++-13/g++-12/g++); seed behavior unverified")
        unit = (
            "#include <cstdint>\n"
            "namespace izanagi_silo_skel {\n" + tls + "}\n"
            "int main() {\n"
            "  using namespace izanagi_silo_skel;\n"
            "  auto begin_seed = [](uint64_t thid_) {\n" + begin_seed + "  };\n"
            "  begin_seed(0); auto zero = next_random();\n"
            "  random_seeded = false; begin_seed(1); auto one = next_random();\n"
            "  if (zero == one) return 1;\n"
            "  random_seeded = false; begin_seed(0);\n"
            "  if (next_random() != zero) return 2;\n"
            "  begin_seed(0); auto continued = next_random();\n"
            "  if (continued == zero) return 3;\n"
            "  return 0;\n"
            "}\n"
        )
        with tempfile.TemporaryDirectory(prefix="silo-policy-seed-") as tmp:
            path = Path(tmp) / "seed.cc"
            binary = Path(tmp) / "seed"
            path.write_text(unit)
            subprocess.run([compiler, "-std=c++17", str(path), "-o", str(binary)],
                           check=True, capture_output=True, text=True)
            result = subprocess.run([str(binary)], capture_output=True, text=True)
            failures = {1: "different thid", 2: "same thid", 3: "continued sequence"}
            assert result.returncode == 0, failures.get(result.returncode, result)


def test_flag_errors_require_closed_values_and_explicit_prerequisites():
    with _applied_template() as (checkout, _):
        source = (checkout / axis.SOURCE_REL).read_text()
        for condition in (
            "#ifndef SILO_POLICY_VARIANT",
            "#if SILO_POLICY_VARIANT != 0 && SILO_POLICY_VARIANT != 1",
            "#if !defined(BACK_OFF) || !defined(NO_WAIT_LOCKING_IN_VALIDATION) || !defined(NO_WAIT_OF_TICTOC)",
            "#elif BACK_OFF != 1 || NO_WAIT_LOCKING_IN_VALIDATION != 1 || NO_WAIT_OF_TICTOC != 0",
        ):
            assert condition + '\n#error "' in source
        assert '#if SILO_POLICY_VARIANT\n#if !defined(BACK_OFF)' in source


def test_api_bytes_and_one_byte_negative_control():
    with _applied_template() as (checkout, _):
        source = (checkout / axis.SOURCE_REL).read_bytes()
        header = ROOT / axis.API_HEADER
        _assert_api_matches(source, header)
        original = header.read_bytes()
        changed = original.replace(b"retry = 0", b"retry = 2", 1)
        assert sum(a != b for a, b in zip(original, changed)) == 1
        assert len(original) == len(changed)
        with tempfile.TemporaryDirectory() as tmp:
            negative = Path(tmp) / "api.hh"
            negative.write_bytes(changed)
            try:
                _assert_api_matches(source, negative)
            except AssertionError:
                pass
            else:
                raise AssertionError("one-byte API mutation was accepted")


def test_default_body_and_quarantine_parser():
    with _applied_template() as (checkout, _):
        path = checkout / axis.SOURCE_REL
        source = path.read_bytes()
        body = source.split(HOLE_BEGIN, 1)[1].split(HOLE_END, 1)[0]
        assert body == (ROOT / axis.HAND_POLICY_DIR / "abort0.cpp").read_bytes()
        marker = diff_quarantine.parse_template_file(str(path), axis.MARKER_ID)
        assert marker is not None
        assert marker.marker_id == axis.MARKER_ID
        assert marker.else_line + 1 == marker.endif_line
        lines = source.splitlines(keepends=True)
        assert b"".join(lines[marker.if_line:marker.else_line - 1]) == body


def test_axis_reason_enum_order_and_hand_policy_contracts():
    header = (ROOT / axis.API_HEADER).read_text()
    match = re.search(r"enum class AbortReason : uint32_t \{([^}]+)\}", header)
    assert match is not None
    assert tuple(item.strip() for item in match.group(1).split(",")) == axis.REASON_NAMES
    assert set(axis.REASON_SITES.values()) == set(axis.REASON_NAMES) - {"unset"}
    assert len(axis.REASON_SITES) == 7
    assert (axis.ABORT_WAIT_MAX_US, axis.LOCK_WAIT_MAX_US, axis.LOCK_ATTEMPT_LIMIT) == (1000, 50, 32)
    contracts = {
        "abort0": (0, "abort", 0), "maxwait": (1000, "retry", 50),
        "static5": (5, "abort", 0), "static10": (10, "abort", 0),
        "retry": (0, "retry", 0), "huge": (4294967295, "abort", 0),
    }
    assert set(axis.HAND_POLICIES) == set(contracts)
    digests = set()
    for name, (delay, action, wait) in contracts.items():
        path = ROOT / axis.HAND_POLICY_DIR / axis.HAND_POLICIES[name]
        assert path.is_file()
        # Independent fixed reference derived from the ruling's six rows. No
        # live tree hash or compiler-dependent digest is substituted into it.
        expected = (
            "struct PolicyState { };\n"
            "uint32_t policy_after_abort(PolicyState&, const izanagi_silo_api::AbortContext&) noexcept {\n"
            f"  return {delay}u;\n"
            "}\n"
            "izanagi_silo_api::LockResponse policy_on_lock_conflict(PolicyState&, const izanagi_silo_api::LockContext&) noexcept {\n"
            f"  return izanagi_silo_api::LockResponse{{izanagi_silo_api::PolicyAction::{action}, {wait}u}};\n"
            "}\n"
            "void policy_on_commit(PolicyState&, const izanagi_silo_api::CommitContext&) noexcept {\n"
            "}\n"
        ).encode()
        assert path.read_bytes() == expected
        digest = hashlib.sha256(path.read_bytes()).digest()
        assert digest == hashlib.sha256(expected).digest()
        digests.add(digest)
    assert len(digests) == 6


def test_reason_sites_are_bound_to_transaction_operations():
    # Meaning-based regions, rather than volatile line numbers or a mere count
    # of enum names: a swapped insert/scan or read-tid/read-lock store must fail.
    regions = {
        "insert_node_version_mismatch": ("if (unlikely(it->second != insert_info.old_version)) {", "return Status::ERROR_CONCURRENT_WRITE_OR_DELETE;"),
        "write_set_lock_conflict": ("if (expected.lock) {", "#else"),
        "update_target_absent": ("if (itr->op_ == OpType::UPDATE && itr->rcdptr_->tidword_.absent) {", "return;"),
        "read_set_tid_changed": ("if ((*itr).get_tidword().epoch != check.epoch ||", "return false;"),
        "read_set_locked_by_other": ("if (check.lock && !searchWriteSet((*itr).storage_, (*itr).key_)) {", "return false;"),
        "validation_node_version_mismatch": ("if (node->full_version_value() != it.second) {", "return false;"),
        "scan_node_version_mismatch": ("} else if ((*it).second != version) {", "\n  }"),
    }
    assert set(regions) == set(axis.REASON_SITES)
    with _applied_template() as (checkout, _):
        source = (checkout / axis.SOURCE_REL).read_text()
        for site, (start, stop) in regions.items():
            region = source.split(start, 1)[1].split(stop, 1)[0]
            stores = re.findall(r"::izanagi_silo_skel::reason = ::izanagi_silo_api::AbortReason::(\w+);", region)
            assert stores == [axis.REASON_SITES[site]], site


def test_lock_bounds_reload_prefix_unlock_and_hook_lifetime():
    with _applied_template() as (checkout, head):
        source = (checkout / axis.SOURCE_REL).read_text()
        stock = _git(checkout, "show", f"{head}:{axis.SOURCE_REL}").decode()
        lock = source.split("void TxExecutor::lockWriteSet() {", 1)[1].split(
            "Status TxExecutor::read(", 1)[0]
        assert lock.index("uint32_t attempt = 0;") < lock.index("for (;;) {")
        assert lock.index("if (attempt >= 32u)") < lock.index("current_attempt = attempt++;")
        assert lock.index("current_attempt = attempt++;") < lock.index("if (expected.lock)")
        assert "on_lock_conflict(current_attempt)" in lock
        assert "if (static_cast<uint32_t>(r.action) == 0u)" in lock
        assert (
            "::izanagi_silo_skel::wait_us(std::min(r.wait_us, 50u));\n"
            "          expected.obj_ = loadAcquire((*itr).rcdptr_->tidword_.obj_);\n"
            "          continue;"
        ) in lock
        abort_exit = (
            "this->status_ = TransactionStatus::aborted;\n"
            "        ::izanagi_silo_skel::reason = ::izanagi_silo_api::AbortReason::lock_conflict;\n"
            "        if (itr != write_set_.begin()) unlockWriteSet(itr);\n"
            "        return;"
        )
        assert lock.count(abort_exit) == 2  # limit and abort/unknown action
        stock_branch = stock.split("#if NO_WAIT_LOCKING_IN_VALIDATION", 1)[1].split("#endif", 1)[0]
        assert "#if NO_WAIT_LOCKING_IN_VALIDATION" + stock_branch + "#endif" in lock
        assert source.count("thread_local ::izanagi_silo_policy::PolicyState ") == 1
        assert source.count("__attribute__((noipa))") == 3
        begin = source.split("void TxExecutor::begin() {", 1)[1].split("\n}", 1)[0]
        assert "AbortReason::unset;" in begin
        assert "::izanagi_silo_skel::state" not in begin
        abort = source.split("void TxExecutor::abort() {", 1)[1].split("void TxExecutor::begin()", 1)[0]
        assert "wait_us(std::min(ret, 1000u));" in abort
        assert abort.index("std::uint64_t start(rdtscp());") < abort.index("after_abort();")
        assert abort.index("after_abort();") < abort.index("local_backoff_latency_")
        assert "::izanagi_silo_skel::on_commit();" not in abort
        commit = source.split("bool TxExecutor::commit() {", 1)[1].split("bool TxExecutor::isLeader()", 1)[0]
        assert commit.count("::izanagi_silo_skel::on_commit();") == 1
        assert commit.index("writePhase();") < commit.index("on_commit();") < commit.index("return true;")


def test_source_identity_off_inert_on_honest_includes_and_trace_diff():
    cxx = _cxx()
    with _applied_template() as (checkout, head):
        path = checkout / axis.SOURCE_REL
        template = path.read_bytes()
        on_tokens = set()
        for name in axis.HAND_POLICIES:
            body = (ROOT / axis.HAND_POLICY_DIR / axis.HAND_POLICIES[name]).read_bytes()
            before, tail = template.split(HOLE_BEGIN, 1)
            _, after = tail.split(HOLE_END, 1)
            path.write_bytes(before + HOLE_BEGIN + body + HOLE_END + after)
            for value in (0, 1):
                genome = _genome(value)
                source_digest.assert_includes_match_head(genome, head, str(checkout), cxx)
                source_digest.assert_trace_diff_matches_head(genome, head, str(checkout), cxx)
                token = source_digest.resolve(genome, head, str(checkout), cxx)
                if value == 0:
                    assert token == source_digest.STOCK, name
                else:
                    assert token != source_digest.STOCK, name
                    on_tokens.add(token)
        assert len(on_tokens) == len(axis.HAND_POLICIES)


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
