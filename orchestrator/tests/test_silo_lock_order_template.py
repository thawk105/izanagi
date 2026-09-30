"""Pinned lock-order skeleton contracts, including executable sort behavior."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from skiputil import Skip, skip
from orchestrator.campaign import axis_silo_lock_order, diff_quarantine, source_digest
from orchestrator.campaign.model import Genome
from orchestrator.campaign.diff_quarantine import DiffRejectSubtype
from orchestrator.campaign.silo_lock_order_gate import order_gate

PATCH = ROOT / "patches/silo-lock-order-variant.patch"
PIN = axis_silo_lock_order.PIN
SOURCE = "cc/silo/transaction.cc"
API_HEADER = ROOT / axis_silo_lock_order.API_HEADER
HAND = ROOT / axis_silo_lock_order.HAND_POLICY_DIR / "version_desc.cpp"
API_BEGIN = b"// SILO-LOCK-ORDER-API-BEGIN\n"
API_END = b"// SILO-LOCK-ORDER-API-END\n"
HOLE_BEGIN = b"// EVOLVE-BLOCK-BEGIN silo-lock-order-policy\n#if SILO_ORDER_VARIANT\n"
HOLE_END = b"#else\n#endif\n// EVOLVE-BLOCK-END silo-lock-order-policy"
SORT_BEGIN = b"// SILO-LOCK-ORDER-SORT-BEGIN\n"
SORT_END = b"// SILO-LOCK-ORDER-SORT-END\n"


def _git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.STDOUT)


@contextmanager
def _applied():
    head = _git(ROOT / "external/ccbench", "rev-parse", "HEAD").decode().strip()
    assert head.startswith(PIN)
    with tempfile.TemporaryDirectory(prefix="silo-lock-order-template-") as tmp:
        checkout = Path(tmp) / "ccbench"
        subprocess.run(["git", "clone", "--shared", "--no-checkout",
                        str(ROOT / "external/ccbench"), str(checkout)],
                       check=True, capture_output=True)
        _git(checkout, "checkout", "--detach", head)
        _git(checkout, "apply", "--check", str(PATCH))
        _git(checkout, "apply", str(PATCH))
        yield checkout, head


@pytest.fixture(scope="module")
def applied():
    with _applied() as pair:
        yield pair


def _cxx():
    for name in ("g++-13", "g++-12", "g++"):
        if shutil.which(name):
            return name
    skip("C++ compiler unavailable; compile behavior unverified")


def _genome(value):
    return Genome("silo", {
        "BACK_OFF": 1, "NO_WAIT_LOCKING_IN_VALIDATION": 1,
        "NO_WAIT_OF_TICTOC": 0, "WAL": 0, "SILO_ORDER_VARIANT": value,
    })


def _between(source, start, end):
    assert source.count(start) == source.count(end) == 1
    return source.split(start, 1)[1].split(end, 1)[0]


def test_touch_markers_api_and_quarantine(applied):
    checkout, _ = applied
    patch = PATCH.read_text()
    assert re.findall(r"^diff --git a/(\S+) b/(\S+)$", patch, re.M) == [
        (SOURCE, SOURCE), ("cmake/Options.cmake", "cmake/Options.cmake"),
    ]
    source = (checkout / SOURCE).read_bytes()
    assert source.count(b"EVOLVE-BLOCK-BEGIN") == source.count(b"EVOLVE-BLOCK-END") == 1
    assert _between(source, API_BEGIN, API_END) == API_HEADER.read_bytes()
    assert b"void sort_write_set(" in _between(source, SORT_BEGIN, SORT_END)
    assert b"struct OrderState { };" in _between(source, HOLE_BEGIN, HOLE_END)
    marker = diff_quarantine.parse_template_file(str(checkout / SOURCE), "silo-lock-order-policy")
    assert marker is not None and marker.else_line + 1 == marker.endif_line
    options = (checkout / "cmake/Options.cmake").read_text()
    assert "set(CCBENCH_SILO_ORDER_VARIANT 0 CACHE STRING" in options
    assert "SILO_ORDER_VARIANT=$" + "{CCBENCH_SILO_ORDER_VARIANT}" in options


def test_required_flags_fail_closed(applied):
    checkout, _ = applied
    cxx = _cxx()
    source = (checkout / SOURCE).read_text()
    guards = "#ifndef SILO_ORDER_VARIANT" + source.split(
        "#ifndef SILO_ORDER_VARIANT", 1)[1].split(
        "// SILO-LOCK-ORDER-API-BEGIN", 1)[0] + "#endif\n"
    cases = [
        ({}, "SILO_ORDER_VARIANT must be supplied", False),
        ({"SILO_ORDER_VARIANT": 2}, "SILO_ORDER_VARIANT must be 0 or 1", False),
        ({"SILO_ORDER_VARIANT": 1, "NO_WAIT_OF_TICTOC": 0},
         "NO_WAIT_LOCKING_IN_VALIDATION must be supplied", False),
        ({"SILO_ORDER_VARIANT": 1, "NO_WAIT_LOCKING_IN_VALIDATION": 0,
          "NO_WAIT_OF_TICTOC": 0}, "NO_WAIT_LOCKING_IN_VALIDATION must be 1", False),
        ({"SILO_ORDER_VARIANT": 1, "NO_WAIT_LOCKING_IN_VALIDATION": 1},
         "NO_WAIT_OF_TICTOC must be supplied", False),
        ({"SILO_ORDER_VARIANT": 1, "NO_WAIT_LOCKING_IN_VALIDATION": 1,
          "NO_WAIT_OF_TICTOC": 1}, "NO_WAIT_OF_TICTOC must be 0", False),
        ({"SILO_ORDER_VARIANT": 1, "NO_WAIT_LOCKING_IN_VALIDATION": 1,
          "NO_WAIT_OF_TICTOC": 0}, "", True),
        ({"SILO_ORDER_VARIANT": 0}, "", True),
    ]
    for defines, diagnostic, passes in cases:
        command = [cxx, "-std=c++17", "-E", "-x", "c++", "-o", "/dev/null"]
        command += [f"-D{k}={v}" for k, v in defines.items()]
        command.append("-")
        result = subprocess.run(command, input=guards, cwd=checkout,
                                capture_output=True, text=True)
        assert (result.returncode == 0) == passes, (defines, result.stderr)
        if diagnostic:
            assert diagnostic in result.stderr, (defines, result.stderr)


def test_off_resolves_stock_and_on_is_distinct(applied):
    checkout, head = applied
    cxx = _cxx()
    path = checkout / SOURCE
    original = path.read_bytes()
    default = _between(original, HOLE_BEGIN, HOLE_END)
    version_desc = HAND.read_bytes()
    for body in (default, version_desc):
        path.write_bytes(original.replace(HOLE_BEGIN + default + HOLE_END,
                                          HOLE_BEGIN + body + HOLE_END, 1))
        for flag in (0, 1):
            genome = _genome(flag)
            source_digest.assert_includes_match_head(genome, head, str(checkout), cxx)
            source_digest.assert_trace_diff_matches_head(genome, head, str(checkout), cxx)
            token = source_digest.resolve(genome, head, str(checkout), cxx)
            assert (token == source_digest.STOCK) == (flag == 0)
    path.write_bytes(original)


def test_real_patch_gate_writes_hand_body_only(applied):
    checkout, _ = applied
    cxx = _cxx()
    path = checkout / SOURCE
    before = path.read_bytes()
    default = _between(before, HOLE_BEGIN, HOLE_END)
    body_bytes = HAND.read_bytes()
    body = body_bytes.decode()
    expected = before.replace(HOLE_BEGIN + default + HOLE_END,
                              HOLE_BEGIN + body_bytes + b"\n" + HOLE_END, 1)
    try:
        result, _ = order_gate(checkout, body, None, compiler=cxx,
                               scratch_dir=str(checkout), write=True, origin="initial")
        assert result.passed, result
        assert path.read_bytes() == expected
        assert _between(path.read_bytes(), HOLE_BEGIN, HOLE_END) == body_bytes + b"\n"
    finally:
        path.write_bytes(before)


def test_real_patch_gate_rejects_forbidden_field_without_write(applied):
    checkout, _ = applied
    cxx = _cxx()
    path = checkout / SOURCE
    before = path.read_bytes()
    body = HAND.read_text().replace("struct OrderState {};",
                                    "struct OrderState { uint64_t write_set_; };", 1)
    assert body != HAND.read_text()
    result, _ = order_gate(checkout, body, None, compiler=cxx,
                           scratch_dir=str(checkout), write=True, origin="initial")
    assert not result.passed and result.subtype == DiffRejectSubtype.POLICY_GRAMMAR
    assert path.read_bytes() == before


def test_sort_behavior_and_hook_counts(applied):
    checkout, _ = applied
    cxx = _cxx()
    sort_body = _between((checkout / SOURCE).read_bytes(), SORT_BEGIN, SORT_END).decode()
    unit = r'''
#include <algorithm>
#include <cstdint>
#include <string>
#include <tuple>
#include <utility>
#include <vector>
using std::sort;
enum class OpType { UPDATE, INSERT, DELETE };
struct Word { uint32_t epoch, tid; bool locked; };
struct Element {
  OpType op_;
  int storage_;
  std::string key_;
  Word rcdptr_;
  int id;
  bool operator<(const Element& b) const {
    return std::tie(storage_, key_) < std::tie(b.storage_, b.key_);
  }
};
namespace izanagi_silo_order_skel {
''' + sort_body + r'''
}
int main() {
  using namespace izanagi_silo_order_skel;
  const std::vector<Element> base{
      {OpType::UPDATE, 2, "z", {3, 1, false}, 1},
      {OpType::UPDATE, 1, "b", {2, 1, true}, 2},
      {OpType::UPDATE, 1, "a", {2, 1, false}, 3},
      {OpType::UPDATE, 1, "c", {1, 1, false}, 4}};
  auto ids = [](const auto& ws) {
    std::vector<int> out;
    for (const auto& e : ws) out.push_back(e.id);
    return out;
  };
  auto original = ids(base);
  sort(original.begin(), original.end());
  auto run = [&](std::vector<Element> ws, bool use, int ec, int pc, int rc,
                 std::vector<int> expected) {
    int enabled_calls = 0, priority_calls = 0, read_calls = 0;
    sort_write_set(ws,
      [&](uint32_t count) { ++enabled_calls; return use && count == ws.size(); },
      [&](Word w) { ++priority_calls; return (uint64_t(w.epoch) << 29u) | w.tid; },
      [&](const Element& e) { ++read_calls; return e.rcdptr_; });
    auto got = ids(ws);
    auto members = got;
    sort(members.begin(), members.end());
    return got == expected && members == original &&
           enabled_calls == ec && priority_calls == pc && read_calls == rc;
  };
  if (!run(base, true, 1, 4, 4, {1, 3, 2, 4})) return 1;
  if (!run(base, false, 1, 0, 0, {3, 2, 4, 1})) return 2;
  for (auto op : {OpType::INSERT, OpType::DELETE}) {
    auto mixed = base;
    mixed[0].op_ = op;
    if (!run(mixed, true, 0, 0, 0, {3, 2, 4, 1})) return 3;
  }
  return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix="silo-lock-sort-") as tmp:
        source = Path(tmp) / "sort.cc"
        binary = Path(tmp) / "sort"
        source.write_text(unit)
        build = subprocess.run([cxx, "-std=c++17", "-Wall", "-Wextra", "-Werror",
                                str(source), "-o", str(binary)], capture_output=True, text=True)
        assert build.returncode == 0, build.stderr
        result = subprocess.run([str(binary)], capture_output=True, text=True)
        assert result.returncode == 0, result


def _run():
    passed = failed = skipped = 0
    with _applied() as pair:
        for name, fn in sorted(globals().items()):
            if not name.startswith("test_") or not callable(fn):
                continue
            try:
                fn(pair)
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
    raise SystemExit(_run())
