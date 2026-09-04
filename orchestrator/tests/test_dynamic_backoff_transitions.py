from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[2]
CCBENCH = ROOT / "external" / "ccbench"
PATCH_A = ROOT / "patches" / "cicada-adaptive-params.patch"
PATCH_B = ROOT / "patches" / "cicada-adaptive-dynamic.patch"
PIN_FULL = "511c9538e4e8efa54b45cda62e72389ed3b706ec"

DEFAULT_DEFINES = (
    "-DADD_ANALYSIS=0",
    "-DBACKOFF_INCR_MILLI=100000",
    "-DBACKOFF_MAX_US=1000",
    "-DBACKOFF_UPDATE_US=10",
    "-DBACKOFF_COUNT_WINDOW=0",
    "-DBACKOFF_COUNT_CAP_US=0",
    "-DBACKOFF_STEP_ADAPT=0",
    "-DBACKOFF_STEP_MIN_MILLI=100000",
    "-DBACKOFF_STEP_MAX_MILLI=100000",
    "-DBACKOFF_DYN_CEILING=0",
    "-DBACKOFF_TRACE=0",
)
CCBENCH_WARNING_FLAGS = ("-Wall", "-Wextra", "-Werror")
RULING_COMMON_DEFINES = (
    "-DADD_ANALYSIS=0",
    "-DBACKOFF_INCR_MILLI=1000",
    "-DBACKOFF_MAX_US=1000",
    "-DBACKOFF_UPDATE_US=2560",
    "-DBACKOFF_COUNT_WINDOW=10000",
    "-DBACKOFF_COUNT_CAP_US=10240",
)
WARNING_COMPILE_VARIANTS = (
    ("default", DEFAULT_DEFINES),
    (
        "cw",
        RULING_COMMON_DEFINES
        + (
            "-DBACKOFF_STEP_ADAPT=0",
            "-DBACKOFF_STEP_MIN_MILLI=100000",
            "-DBACKOFF_STEP_MAX_MILLI=100000",
            "-DBACKOFF_DYN_CEILING=0",
            "-DBACKOFF_TRACE=0",
        ),
    ),
    (
        "cw-as",
        RULING_COMMON_DEFINES
        + (
            "-DBACKOFF_STEP_ADAPT=1",
            "-DBACKOFF_STEP_MIN_MILLI=1000",
            "-DBACKOFF_STEP_MAX_MILLI=4000",
            "-DBACKOFF_DYN_CEILING=0",
            "-DBACKOFF_TRACE=0",
        ),
    ),
    (
        "cw-as-dyn",
        RULING_COMMON_DEFINES
        + (
            "-DBACKOFF_STEP_ADAPT=1",
            "-DBACKOFF_STEP_MIN_MILLI=1000",
            "-DBACKOFF_STEP_MAX_MILLI=4000",
            "-DBACKOFF_DYN_CEILING=1",
            "-DBACKOFF_TRACE=0",
        ),
    ),
    (
        "BACKOFF_TRACE=1",
        RULING_COMMON_DEFINES
        + (
            "-DBACKOFF_STEP_ADAPT=1",
            "-DBACKOFF_STEP_MIN_MILLI=1000",
            "-DBACKOFF_STEP_MAX_MILLI=4000",
            "-DBACKOFF_DYN_CEILING=1",
            "-DBACKOFF_TRACE=1",
        ),
    ),
)

DRIVER_SOURCE = r'''\
#include <cstdlib>
#include <iostream>
#include <string>
#include <vector>

#define GLOBAL_VALUE_DEFINE
#define Backoff StockBackoff
#define leaderBackoffWork stock_leaderBackoffWork
#include "variants/stock/backoff.hh"
#undef leaderBackoffWork
#undef Backoff

#undef BACKOFF_INCR_MILLI
#undef BACKOFF_MAX_US
#undef BACKOFF_UPDATE_US
#undef BACKOFF_COUNT_WINDOW
#undef BACKOFF_COUNT_CAP_US
#undef BACKOFF_STEP_ADAPT
#undef BACKOFF_STEP_MIN_MILLI
#undef BACKOFF_STEP_MAX_MILLI
#undef BACKOFF_DYN_CEILING
#undef BACKOFF_TRACE
#define BACKOFF_INCR_MILLI 100000
#define BACKOFF_MAX_US 1000
#define BACKOFF_UPDATE_US 10
#define BACKOFF_COUNT_WINDOW 0
#define BACKOFF_COUNT_CAP_US 0
#define BACKOFF_STEP_ADAPT 0
#define BACKOFF_STEP_MIN_MILLI 100000
#define BACKOFF_STEP_MAX_MILLI 100000
#define BACKOFF_DYN_CEILING 0
#define BACKOFF_TRACE 0
#define Backoff DefaultDynamicBackoff
#define leaderBackoffWork default_dynamic_leaderBackoffWork
#include "variants/default_dynamic/backoff.hh"
#undef leaderBackoffWork
#undef Backoff

#undef BACKOFF_INCR_MILLI
#undef BACKOFF_MAX_US
#undef BACKOFF_UPDATE_US
#undef BACKOFF_COUNT_WINDOW
#undef BACKOFF_COUNT_CAP_US
#undef BACKOFF_STEP_ADAPT
#undef BACKOFF_STEP_MIN_MILLI
#undef BACKOFF_STEP_MAX_MILLI
#undef BACKOFF_DYN_CEILING
#undef BACKOFF_TRACE
#define BACKOFF_INCR_MILLI 1000
#define BACKOFF_MAX_US 1000
#define BACKOFF_UPDATE_US 10
#define BACKOFF_COUNT_WINDOW 10
#define BACKOFF_COUNT_CAP_US 30
#define BACKOFF_STEP_ADAPT 1
#define BACKOFF_STEP_MIN_MILLI 1000
#define BACKOFF_STEP_MAX_MILLI 4000
#define BACKOFF_DYN_CEILING 1
#define BACKOFF_TRACE 0
#define Backoff DynamicBackoff
#define leaderBackoffWork dynamic_leaderBackoffWork
#include "variants/dynamic/backoff.hh"
#undef leaderBackoffWork
#undef Backoff

static void reset_dynamic(DynamicBackoff& backoff) {
  DynamicBackoff::Backoff_.store(0, std::memory_order_release);
  backoff.last_committed_txs_ = 0;
  backoff.last_committed_tput_ = 0;
  backoff.last_backoff_ = 0;
  backoff.last_time_ = 0;
  backoff.last_count_check_time_ = 0;
  backoff.adaptive_step_ = 1;
  backoff.last_gradient_sign_ = 0;
  backoff.has_last_gradient_sign_ = false;
  backoff.ceiling_ = 1000;
}

static void force_gradient(DynamicBackoff& backoff, int sign,
                           double current_backoff) {
  DynamicBackoff::Backoff_.store(current_backoff,
                                 std::memory_order_release);
  backoff.last_time_ = 0;
  backoff.last_committed_txs_ = 0;
  backoff.last_committed_tput_ = sign < 0 ? 2000000.0 : 0.0;
  backoff.last_backoff_ = sign == 0
                              ? static_cast<uint64_t>(current_backoff)
                              : static_cast<uint64_t>(current_backoff) - 1;
  backoff.update_backoff_at(100, 100);
}

static void print_values(const std::vector<double>& values) {
  for (size_t i = 0; i < values.size(); ++i) {
    if (i != 0) std::cout << ',';
    std::cout << values[i];
  }
  std::cout << '\n';
}

static int run_window() {
  DynamicBackoff backoff(1);
  reset_dynamic(backoff);
  std::cout << backoff.check_update_backoff_at(10, 9) << ' '
            << backoff.check_update_backoff_at(10, 10) << ' '
            << backoff.check_update_backoff_at(30, 9) << ' '
            << backoff.check_update_backoff_at(9, 10) << '\n';
  return 0;
}

static int run_step() {
  DynamicBackoff backoff(1);
  reset_dynamic(backoff);
  std::vector<double> steps;
  for (int sign : {1, 1, 1, 1, -1, 1, 0}) {
    force_gradient(backoff, sign, 100);
    steps.push_back(backoff.adaptive_step_);
  }
  print_values(steps);
  return 0;
}

static int run_poll() {
  DynamicBackoff backoff(1);
  reset_dynamic(backoff);
  std::cout << backoff.check_count_window_at(9) << ' '
            << backoff.check_count_window_at(10) << ' '
            << backoff.check_count_window_at(10) << ' '
            << backoff.check_count_window_at(19) << ' '
            << backoff.check_count_window_at(20) << '\n';
  return 0;
}

static int run_ceiling() {
  DynamicBackoff backoff(1);
  reset_dynamic(backoff);
  backoff.ceiling_ = 200;
  force_gradient(backoff, -1, 200);
  std::cout << "mono_before=200 mono_after=" << backoff.ceiling_ << '\n';

  reset_dynamic(backoff);
  backoff.ceiling_ = 62;
  force_gradient(backoff, -1, 62);
  std::cout << "floor_after=" << backoff.ceiling_ << '\n';
  return 0;
}

static int run_stock() {
  StockBackoff stock(1);
  DefaultDynamicBackoff dynamic(1);
  const std::vector<std::pair<double, uint64_t>> inputs = {
      {0, 1}, {100, 2}, {100, 3}, {1000, 3}, {500, 2}};
  std::vector<double> stock_values;
  std::vector<double> dynamic_values;
  for (const auto& input : inputs) {
    const double current = input.first;
    const uint64_t committed = input.second;

    StockBackoff::Backoff_.store(current, std::memory_order_release);
    stock.last_committed_txs_ = committed;
    stock.last_committed_tput_ = 0;
    stock.last_backoff_ = static_cast<uint64_t>(current);
    stock.last_time_ = rdtscp();
    stock.update_backoff(committed);
    stock_values.push_back(
        StockBackoff::Backoff_.load(std::memory_order_acquire));

    DefaultDynamicBackoff::Backoff_.store(current,
                                          std::memory_order_release);
    dynamic.last_committed_txs_ = committed;
    dynamic.last_committed_tput_ = 0;
    dynamic.last_backoff_ = static_cast<uint64_t>(current);
    dynamic.last_time_ = 0;
    dynamic.update_backoff_at(100, committed);
    dynamic_values.push_back(
        DefaultDynamicBackoff::Backoff_.load(std::memory_order_acquire));
  }
  print_values(stock_values);
  print_values(dynamic_values);
  return 0;
}

int main(int argc, char** argv) {
  if (argc != 2) return 2;
  const std::string mode(argv[1]);
  if (mode == "window") return run_window();
  if (mode == "poll") return run_poll();
  if (mode == "step") return run_step();
  if (mode == "ceiling") return run_ceiling();
  if (mode == "stock") return run_stock();
  return 2;
}
'''


def _run_patch(tree: Path, patch: Path, *, dry_run: bool = False):
    argv = ["patch", "--batch", "--forward"]
    if dry_run:
        argv.append("--dry-run")
    argv.extend(("-p1", "-i", str(patch)))
    return subprocess.run(argv, cwd=tree, capture_output=True, text=True)


def _include_lines(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"^\s*#\s*include[^\n]*$", text, re.MULTILINE))


@pytest.fixture(scope="session")
def patched_sources(tmp_path_factory: pytest.TempPathFactory):
    assert shutil.which("g++") is not None, "g++ is required by the acceptance contract"
    assert shutil.which("patch") is not None, "patch is required by the acceptance contract"
    head = subprocess.run(
        ["git", "-C", str(CCBENCH), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert head == PIN_FULL

    tree = tmp_path_factory.mktemp("dynamic-backoff-sources")
    shutil.copytree(CCBENCH / "include", tree / "include")
    (tree / "cmake").mkdir()
    shutil.copy2(CCBENCH / "cmake" / "Options.cmake", tree / "cmake" / "Options.cmake")

    pin_only_b = _run_patch(tree, PATCH_B, dry_run=True)
    assert pin_only_b.returncode != 0, (
        "patch B unexpectedly applies without patch A\n" + pin_only_b.stdout + pin_only_b.stderr
    )
    applied_a = _run_patch(tree, PATCH_A)
    assert applied_a.returncode == 0, applied_a.stdout + applied_a.stderr
    after_a = (tree / "include" / "backoff.hh").read_text(encoding="utf-8")
    pin_a_b = _run_patch(tree, PATCH_B, dry_run=True)
    assert pin_a_b.returncode == 0, pin_a_b.stdout + pin_a_b.stderr
    applied_b = _run_patch(tree, PATCH_B)
    assert applied_b.returncode == 0, applied_b.stdout + applied_b.stderr
    after_b = (tree / "include" / "backoff.hh").read_text(encoding="utf-8")
    return SimpleNamespace(
        tree=tree,
        after_a=after_a,
        after_b=after_b,
        pin_only_b=pin_only_b,
        pin_a_b=pin_a_b,
    )


@pytest.fixture(scope="session")
def transition_driver(patched_sources, tmp_path_factory: pytest.TempPathFactory) -> Path:
    work = tmp_path_factory.mktemp("dynamic-backoff-driver")
    variants = work / "variants"
    for name, text in (
        ("stock", patched_sources.after_a),
        ("default_dynamic", patched_sources.after_b),
        ("dynamic", patched_sources.after_b),
    ):
        destination = variants / name
        destination.mkdir(parents=True)
        variant_text = (
            text
            + ("" if text.endswith("\n") else "\n")
            + f"// izanagi transition-test variant: {name}\n"
        )
        (destination / "backoff.hh").write_text(variant_text, encoding="utf-8")
    source = work / "driver.cc"
    source.write_text(DRIVER_SOURCE, encoding="utf-8")
    binary = work / "driver"
    compiled = subprocess.run(
        [
            "g++",
            "-std=c++17",
            "-O0",
            *CCBENCH_WARNING_FLAGS,
            f"-I{work}",
            f"-I{patched_sources.tree / 'include'}",
            *DEFAULT_DEFINES,
            str(source),
            "-o",
            str(binary),
        ],
        capture_output=True,
        text=True,
    )
    assert compiled.returncode == 0, compiled.stdout + compiled.stderr
    return binary


def _driver_output(binary: Path, mode: str) -> list[str]:
    result = subprocess.run(
        [str(binary), mode], check=True, capture_output=True, text=True
    )
    return result.stdout.strip().splitlines()


def test_ruling_variants_compile_with_ccbench_warning_flags(
    patched_sources, tmp_path: Path
) -> None:
    source = tmp_path / "warning_compile.cc"
    source.write_text('#include "backoff.hh"\n', encoding="utf-8")
    for name, defines in WARNING_COMPILE_VARIANTS:
        result = subprocess.run(
            [
                "g++",
                "-std=c++17",
                "-O0",
                *CCBENCH_WARNING_FLAGS,
                "-fsyntax-only",
                f"-I{patched_sources.tree / 'include'}",
                *defines,
                str(source),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"{name} failed CCBench warning compilation\n"
            + result.stdout
            + result.stderr
        )


def test_count_window_fires_at_k_boundary_not_k_minus_one(transition_driver: Path) -> None:
    k_minus_one, k_exact, _, _ = _driver_output(transition_driver, "window")[0].split()
    assert (k_minus_one, k_exact) == ("0", "1")


def test_count_window_cap_alone_fires_with_insufficient_count(transition_driver: Path) -> None:
    _, _, cap_only, _ = _driver_output(transition_driver, "window")[0].split()
    assert cap_only == "1"


def test_count_window_never_fires_before_minimum_elapsed_time(transition_driver: Path) -> None:
    _, _, _, before_minimum = _driver_output(transition_driver, "window")[0].split()
    assert before_minimum == "0"


def test_count_scan_is_rate_limited_to_once_per_window(transition_driver: Path) -> None:
    assert _driver_output(transition_driver, "poll")[0] == "0 1 0 0 1"


def test_adaptive_step_doubles_and_halves_with_exact_bounds(transition_driver: Path) -> None:
    values = tuple(float(item) for item in _driver_output(transition_driver, "step")[0].split(","))
    assert values == (1.0, 2.0, 4.0, 4.0, 2.0, 1.0, 1.0)


def test_negative_gradient_never_increases_dynamic_ceiling(transition_driver: Path) -> None:
    match = re.fullmatch(
        r"mono_before=(\d+) mono_after=(\d+)",
        _driver_output(transition_driver, "ceiling")[0],
    )
    assert match is not None
    before, after = (int(value) for value in match.groups())
    assert after < before


def test_dynamic_ceiling_has_exact_fifty_microsecond_floor(transition_driver: Path) -> None:
    line = _driver_output(transition_driver, "ceiling")[1]
    assert line == "floor_after=50"


def test_default_dynamic_path_matches_pin_plus_a_stock_transitions(
    transition_driver: Path,
) -> None:
    stock, dynamic = _driver_output(transition_driver, "stock")
    assert stock == "100,0,200,900,400"
    assert dynamic == stock


def test_trace_is_numeric_if_and_preprocesses_completely_out(
    patched_sources, tmp_path: Path
) -> None:
    patch_text = PATCH_B.read_text(encoding="utf-8")
    assert re.search(r"^\+#if BACKOFF_TRACE$", patch_text, re.MULTILINE)
    assert re.search(r"^\+#ifdef BACKOFF_TRACE$", patch_text, re.MULTILINE) is None

    source = tmp_path / "preprocess.cc"
    source.write_text('#include "backoff.hh"\n', encoding="utf-8")
    outputs: dict[int, str] = {}
    for trace in (0, 1):
        defines = [item for item in DEFAULT_DEFINES if not item.startswith("-DBACKOFF_TRACE=")]
        result = subprocess.run(
            [
                "g++",
                "-std=c++17",
                "-E",
                "-P",
                f"-I{patched_sources.tree / 'include'}",
                *defines,
                f"-DBACKOFF_TRACE={trace}",
                str(source),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        outputs[trace] = result.stdout
    assert "izanagi_backoff_trace" not in outputs[0]
    assert "IZANAGI_BACKOFF_TRACE" not in outputs[0]
    assert "izanagi_backoff_trace" in outputs[1]
    assert "IZANAGI_BACKOFF_TRACE" in outputs[1]


def test_patch_b_requires_a_and_preserves_include_lines(patched_sources) -> None:
    assert patched_sources.pin_only_b.returncode != 0
    assert patched_sources.pin_a_b.returncode == 0
    assert _include_lines(patched_sources.after_b) == _include_lines(patched_sources.after_a)


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
