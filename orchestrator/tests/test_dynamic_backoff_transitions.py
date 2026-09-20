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
PATCH_C = ROOT / "patches" / "cicada-adaptive-counterfactual.patch"
PIN_FULL = "e9e477ca1b55348ab4530de0b1cf663ce4555290"
STEP_POLICY_SEED = "11400714819323198485"

DEFAULT_DEFINES = (
    "-DADD_ANALYSIS=0",
    "-DBACKOFF_INCR_MILLI=100000",
    "-DBACKOFF_MAX_US=1000",
    "-DBACKOFF_UPDATE_US=10",
    "-DBACKOFF_COUNT_WINDOW=0",
    "-DBACKOFF_COUNT_CAP_US=0",
    "-DBACKOFF_STEP_ADAPT=0",
    "-DBACKOFF_STEP_POLICY=0",
    f"-DBACKOFF_STEP_POLICY_SEED={STEP_POLICY_SEED}",
    "-DBACKOFF_STEP_MIN_MILLI=100000",
    "-DBACKOFF_STEP_MAX_MILLI=100000",
    "-DBACKOFF_DYN_CEILING=0",
    "-DBACKOFF_TRACE=0",
    "-DBACKOFF_TRACE_TERMINAL_US=0",
)
CCBENCH_WARNING_FLAGS = ("-Wall", "-Wextra", "-Werror")
RULING_COMMON_DEFINES = (
    "-DADD_ANALYSIS=0",
    "-DBACKOFF_INCR_MILLI=1000",
    "-DBACKOFF_MAX_US=1000",
    "-DBACKOFF_UPDATE_US=2560",
    "-DBACKOFF_COUNT_WINDOW=10000",
    "-DBACKOFF_COUNT_CAP_US=10240",
    "-DBACKOFF_TRACE_TERMINAL_US=0",
)
WARNING_COMPILE_VARIANTS = (
    *(
        (
            f"policy={policy},step={step_adapt},ceiling={dyn_ceiling},trace={trace}",
            RULING_COMMON_DEFINES
            + (
                f"-DBACKOFF_STEP_ADAPT={step_adapt}",
                f"-DBACKOFF_STEP_POLICY={policy}",
                f"-DBACKOFF_STEP_POLICY_SEED={STEP_POLICY_SEED}",
                "-DBACKOFF_STEP_MIN_MILLI=1000",
                "-DBACKOFF_STEP_MAX_MILLI=4000",
                f"-DBACKOFF_DYN_CEILING={dyn_ceiling}",
                f"-DBACKOFF_TRACE={trace}",
            ),
        )
        for policy in (0, 1, 2)
        for step_adapt in (0, 1)
        for dyn_ceiling in (0, 1)
        for trace in (0, 1)
    ),
)
PREEXISTING_WARNING_COMPILE_VARIANTS = (
    ("default", DEFAULT_DEFINES),
    (
        "cw",
        RULING_COMMON_DEFINES
        + (
            "-DBACKOFF_STEP_ADAPT=0",
            "-DBACKOFF_STEP_POLICY=0",
            f"-DBACKOFF_STEP_POLICY_SEED={STEP_POLICY_SEED}",
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
            "-DBACKOFF_STEP_POLICY=0",
            f"-DBACKOFF_STEP_POLICY_SEED={STEP_POLICY_SEED}",
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
            "-DBACKOFF_STEP_POLICY=0",
            f"-DBACKOFF_STEP_POLICY_SEED={STEP_POLICY_SEED}",
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
            "-DBACKOFF_STEP_POLICY=0",
            f"-DBACKOFF_STEP_POLICY_SEED={STEP_POLICY_SEED}",
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

static size_t default_counter_reads = 0;
template <typename T>
static T default_counting_load_acquire(T& ptr) {
  ++default_counter_reads;
  return loadAcquire(ptr);
}

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
#define loadAcquire default_counting_load_acquire
#include "variants/default_dynamic/backoff.hh"
#undef loadAcquire
#undef leaderBackoffWork
#undef Backoff

static size_t dynamic_counter_reads = 0;
static uint64_t dynamic_last_scan_tsc = 0;
template <typename T>
static T dynamic_counting_load_acquire(T& ptr) {
  ++dynamic_counter_reads;
  const uint64_t delay_start = rdtscp();
  while (rdtscp() - delay_start < 10000) {
    _mm_pause();
  }
  const T value = loadAcquire(ptr);
  dynamic_last_scan_tsc = rdtscp();
  return value;
}

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
#define loadAcquire dynamic_counting_load_acquire
#include "variants/dynamic/backoff.hh"
#undef loadAcquire
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
#define BACKOFF_TRACE 1
#define Backoff TraceBackoff
#define leaderBackoffWork trace_leaderBackoffWork
#include "variants/trace/backoff.hh"
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

static int run_ceiling_growth() {
  DynamicBackoff backoff(1);
  reset_dynamic(backoff);
  backoff.ceiling_ = 50;
  std::vector<double> ceilings{static_cast<double>(backoff.ceiling_)};
  for (size_t i = 0; i < 6; ++i) {
    force_gradient(backoff, 1, static_cast<double>(backoff.ceiling_));
    ceilings.push_back(static_cast<double>(backoff.ceiling_));
  }
  print_values(ceilings);
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

static int run_stock_gradient() {
  StockBackoff stock(1);
  DefaultDynamicBackoff dynamic(1);
  std::vector<double> stock_values;
  std::vector<double> dynamic_values;

  StockBackoff::Backoff_.store(100, std::memory_order_release);
  stock.last_committed_txs_ = 0;
  stock.last_committed_tput_ = 0;
  stock.last_backoff_ = 0;
  stock.last_time_ = rdtscp();
  stock.update_backoff(1);
  stock_values.push_back(
      StockBackoff::Backoff_.load(std::memory_order_acquire));

  DefaultDynamicBackoff::Backoff_.store(100, std::memory_order_release);
  dynamic.last_committed_txs_ = 0;
  dynamic.last_committed_tput_ = 0;
  dynamic.last_backoff_ = 0;
  dynamic.last_time_ = 0;
  dynamic.update_backoff_at(100, 1);
  dynamic_values.push_back(
      DefaultDynamicBackoff::Backoff_.load(std::memory_order_acquire));

  StockBackoff::Backoff_.store(200, std::memory_order_release);
  stock.last_committed_txs_ = 1;
  stock.last_committed_tput_ = 1;
  stock.last_backoff_ = 199;
  stock.last_time_ = rdtscp();
  stock.update_backoff(1);
  stock_values.push_back(
      StockBackoff::Backoff_.load(std::memory_order_acquire));

  DefaultDynamicBackoff::Backoff_.store(200, std::memory_order_release);
  dynamic.last_committed_txs_ = 1;
  dynamic.last_committed_tput_ = 1;
  dynamic.last_backoff_ = 199;
  dynamic.last_time_ = 0;
  dynamic.update_backoff_at(100, 1);
  dynamic_values.push_back(
      DefaultDynamicBackoff::Backoff_.load(std::memory_order_acquire));

  print_values(stock_values);
  print_values(dynamic_values);
  return 0;
}

static int run_leader() {
  std::vector<Result> results(2);
  results[0].local_commit_counts_ = 5;
  results[1].local_commit_counts_ = 5;

  default_counter_reads = 0;
  DefaultDynamicBackoff default_early(1000000000000ULL);
  default_dynamic_leaderBackoffWork(default_early, results);
  const size_t default_early_reads = default_counter_reads;

  dynamic_counter_reads = 0;
  DynamicBackoff dynamic_early(1000000000000ULL);
  dynamic_leaderBackoffWork(dynamic_early, results);
  const size_t dynamic_early_reads = dynamic_counter_reads;

  dynamic_counter_reads = 0;
  dynamic_last_scan_tsc = 0;
  DynamicBackoff dynamic_due(1);
  reset_dynamic(dynamic_due);
  dynamic_leaderBackoffWork(dynamic_due, results);
  std::cout << "default_early=" << default_early_reads
            << " dynamic_early=" << dynamic_early_reads
            << " dynamic_due=" << dynamic_counter_reads
            << " sample_after_scan="
            << (dynamic_last_scan_tsc != 0 &&
                dynamic_due.last_time_ >= dynamic_last_scan_tsc)
            << '\n';
  return 0;
}

static int run_sample_window() {
  TraceBackoff backoff(1);
  TraceBackoff::Backoff_.store(0, std::memory_order_release);
  backoff.last_committed_txs_ = 0;
  backoff.last_committed_tput_ = 0;
  backoff.last_backoff_ = 0;
  backoff.last_time_ = 0;
  backoff.last_count_check_time_ = 0;
  backoff.adaptive_step_ = 1;
  backoff.last_gradient_sign_ = 0;
  backoff.has_last_gradient_sign_ = false;
  backoff.ceiling_ = 1000;
  auto& state = TraceBackoff::izanagi_backoff_trace_state_;
  state.izanagi_backoff_trace_write = 0;
  state.izanagi_backoff_trace_retained = 0;
  state.izanagi_backoff_trace_updates = 0;
  state.izanagi_backoff_trace_dropped = 0;

  // t0=10 opens the read gate; t1=25 models 15 cycles spent scanning counters.
  const bool gate = backoff.check_count_window_at(10);
  backoff.update_backoff_at(25, 10);
  const auto& record = state.izanagi_backoff_trace_ring[0];
  std::cout << "gate=" << gate
            << " window_us=" << record.izanagi_backoff_trace_window_us
            << " tsc=" << record.izanagi_backoff_trace_tsc << '\n';
  return 0;
}

int main(int argc, char** argv) {
  if (argc != 2) return 2;
  const std::string mode(argv[1]);
  if (mode == "window") return run_window();
  if (mode == "poll") return run_poll();
  if (mode == "step") return run_step();
  if (mode == "ceiling") return run_ceiling();
  if (mode == "ceiling-growth") return run_ceiling_growth();
  if (mode == "stock") return run_stock();
  if (mode == "stock-gradient") return run_stock_gradient();
  if (mode == "leader") return run_leader();
  if (mode == "sample-window") return run_sample_window();
  return 2;
}
'''

POLICY_DRIVER_SOURCE = r'''\
#include <iostream>
#include <string>
#include <vector>

#define GLOBAL_VALUE_DEFINE
#include "backoff.hh"

static void reset_backoff(Backoff& backoff) {
  Backoff::Backoff_.store(0, std::memory_order_release);
  backoff.last_committed_txs_ = 0;
  backoff.last_committed_tput_ = 0;
  backoff.last_backoff_ = 0;
  backoff.last_time_ = 0;
#if BACKOFF_COUNT_WINDOW > 0
  backoff.last_count_check_time_ = 0;
#endif
#if BACKOFF_STEP_ADAPT
  backoff.adaptive_step_ = 1;
  backoff.last_gradient_sign_ = 0;
  backoff.has_last_gradient_sign_ = false;
#endif
#if BACKOFF_DYN_CEILING
  backoff.ceiling_ = static_cast<uint64_t>(Backoff::kMaxBackoff);
#endif
#if BACKOFF_STEP_POLICY == 2
  backoff.backoff_step_policy_state_ = Backoff::kBackoffStepPolicySeed;
#endif
#if BACKOFF_TRACE
  backoff.start_time_ = 0;
  backoff.terminal_recorded_ = false;
  auto& state = Backoff::izanagi_backoff_trace_state_;
  state.izanagi_backoff_trace_write = 0;
  state.izanagi_backoff_trace_retained = 0;
  state.izanagi_backoff_trace_updates = 0;
  state.izanagi_backoff_trace_flushes = 0;
  state.izanagi_backoff_trace_dropped = 0;
#endif
}

static void force_gradient(Backoff& backoff, int sign, double current_backoff,
                           uint64_t committed_txs = 100) {
  Backoff::Backoff_.store(current_backoff, std::memory_order_release);
  backoff.last_time_ = 0;
  backoff.last_committed_txs_ = committed_txs - 100;
  backoff.last_committed_tput_ = sign < 0 ? 2000000.0 : 0.0;
  if (sign == 0)
    backoff.last_backoff_ = static_cast<uint64_t>(current_backoff);
  else if (current_backoff >= 1)
    backoff.last_backoff_ = static_cast<uint64_t>(current_backoff - 1);
  else
    backoff.last_backoff_ = 0;
  backoff.update_backoff_at(100, committed_txs);
}

static void print_values(const std::vector<double>& values) {
  for (size_t i = 0; i < values.size(); ++i) {
    if (i != 0)
      std::cout << ',';
    std::cout << values[i];
  }
  std::cout << '\n';
}

static int run_series() {
  Backoff backoff(1);
  std::vector<double> values;
  for (const auto& input :
       std::vector<std::pair<int, uint64_t>>{{1, 100}, {-1, 100},
                                             {0, 100}, {0, 101}}) {
    reset_backoff(backoff);
    force_gradient(backoff, input.first, 100, input.second);
    values.push_back(Backoff::Backoff_.load(std::memory_order_acquire));
  }
  print_values(values);
  return 0;
}

static int run_safe() {
  Backoff backoff(1);
  reset_backoff(backoff);
  force_gradient(backoff, 1, 100);
  const double positive =
      Backoff::Backoff_.load(std::memory_order_acquire);
  reset_backoff(backoff);
  force_gradient(backoff, -1, 100);
  const double negative =
      Backoff::Backoff_.load(std::memory_order_acquire);
  std::cout << positive << ',' << negative << '\n';
  return 0;
}

#if BACKOFF_TRACE
static const Backoff::izanagi_backoff_trace_record& trace_record(size_t index) {
  return Backoff::izanagi_backoff_trace_state_
      .izanagi_backoff_trace_ring[index];
}

static int run_lcg() {
  Backoff backoff(1);
  reset_backoff(backoff);
  std::string bits;
  std::vector<double> values;
  for (size_t i = 0; i < 16; ++i) {
    force_gradient(backoff, 1, 100);
    const auto& record = trace_record(i);
    bits.push_back(static_cast<char>(
        '0' + record.izanagi_backoff_trace_assigned_invert));
    values.push_back(Backoff::Backoff_.load(std::memory_order_acquire));
  }
  std::cout << bits << '\n';
  print_values(values);
  return 0;
}

static int run_advance_special() {
  Backoff backoff(1);
  reset_backoff(backoff);
  force_gradient(backoff, 1, 100);
  force_gradient(backoff, 0, 100, 100);
  force_gradient(backoff, 0, 9007199254740992.0, 101);
  force_gradient(backoff, 1, 0.5);
  const double clamp_after =
      Backoff::Backoff_.load(std::memory_order_acquire);
  force_gradient(backoff, 1, 100);

  std::string bits;
  std::string gradients;
  std::string recommendations;
  for (size_t i = 0; i < 5; ++i) {
    const auto& record = trace_record(i);
    bits.push_back(static_cast<char>(
        '0' + record.izanagi_backoff_trace_assigned_invert));
    if (i != 0) {
      gradients.push_back(',');
      recommendations.push_back(',');
    }
    gradients += std::to_string(
        record.izanagi_backoff_trace_gradient_sign);
    recommendations += std::to_string(
        record.izanagi_backoff_trace_recommended_delta_sign);
  }
  std::cout << "bits=" << bits << " gradients=" << gradients
            << " recommendations=" << recommendations
            << " clamp_after=" << clamp_after << '\n';
  return 0;
}

#if BACKOFF_COUNT_WINDOW > 0
static int run_terminal() {
  Backoff backoff(1);
  reset_backoff(backoff);
  force_gradient(backoff, 1, 100, 100);
  const uint64_t lcg_before_terminal = backoff.backoff_step_policy_state_;
  const double backoff_before_terminal =
      Backoff::Backoff_.load(std::memory_order_acquire);

  std::vector<Result> results(2);
  results[0].local_commit_counts_ = 55;
  results[1].local_commit_counts_ = 55;
  backoff.last_count_check_time_ = 0;
  leaderBackoffWork(backoff, results);
  const uint64_t lcg_after_terminal = backoff.backoff_step_policy_state_;
  const double backoff_after_terminal =
      Backoff::Backoff_.load(std::memory_order_acquire);

  results[0].local_commit_counts_ = 60;
  results[1].local_commit_counts_ = 60;
  backoff.last_count_check_time_ = 0;
  leaderBackoffWork(backoff, results);
  const uint64_t lcg_after_repeat = backoff.backoff_step_policy_state_;
  const uint64_t expected_lcg_after_repeat =
      lcg_after_terminal * 6364136223846793005ULL +
      1442695040888963407ULL;
  const double backoff_after_repeat =
      Backoff::Backoff_.load(std::memory_order_acquire);
  const auto& terminal = trace_record(1);
  const auto& state = Backoff::izanagi_backoff_trace_state_;
  std::cout
      << "updates=" << state.izanagi_backoff_trace_updates
      << " retained=" << state.izanagi_backoff_trace_retained
      << " dropped=" << state.izanagi_backoff_trace_dropped
      << " flushes=" << state.izanagi_backoff_trace_flushes
      << " terminal_recorded=" << backoff.terminal_recorded_
      << " seq=" << terminal.izanagi_backoff_trace_seq
      << " trigger=" << terminal.izanagi_backoff_trace_trigger
      << " assigned=" << terminal.izanagi_backoff_trace_assigned_invert
      << " recommended="
      << terminal.izanagi_backoff_trace_recommended_delta_sign
      << " realized=" << terminal.izanagi_backoff_trace_inversion_realized
      << " feasible="
      << terminal.izanagi_backoff_trace_both_actions_feasible
      << " terminal_flush="
      << terminal.izanagi_backoff_trace_terminal_flush
      << " lcg_terminal_unchanged="
      << (lcg_after_terminal == lcg_before_terminal)
      << " lcg_repeat_advanced="
      << (lcg_after_repeat == expected_lcg_after_repeat &&
          lcg_after_repeat != lcg_after_terminal)
      << " controller_repeat_updated="
      << (backoff.last_committed_txs_ == 120 && backoff.last_time_ > 100)
      << " backoff_terminal_unchanged="
      << (backoff_after_terminal == backoff_before_terminal)
      << " backoff_after_repeat=" << backoff_after_repeat
      << '\n';
  return 0;
}
#endif

static int run_trace_point(const std::string& mode) {
  Backoff backoff(1);
  reset_backoff(backoff);
  if (mode == "safe-trace") {
    force_gradient(backoff, 1, 100);
  } else if (mode == "parity") {
    force_gradient(backoff, 0, 100, 100);
  } else if (mode == "partial-lower") {
    force_gradient(backoff, 1, 0.5);
  } else if (mode == "fixed-upper") {
    force_gradient(backoff, -1, 999.5);
  } else if (mode == "recommended-upper") {
    force_gradient(backoff, 1, 999.5);
  } else if (mode == "safe-negative-trace") {
    force_gradient(backoff, -1, 100);
  } else if (mode == "dynamic-shrink") {
#if BACKOFF_DYN_CEILING
    backoff.ceiling_ = 200;
    force_gradient(backoff, -1, 200);
#else
    return 3;
#endif
  } else if (mode == "emit") {
    force_gradient(backoff, 1, 100);
    return 0;
  } else {
    return 2;
  }
  const auto& record = trace_record(0);
  std::cout
      << "before=" << record.izanagi_backoff_trace_backoff_before
      << " after=" << record.izanagi_backoff_trace_backoff_after
      << " gradient=" << record.izanagi_backoff_trace_gradient_sign
      << " step=" << record.izanagi_backoff_trace_step_us
      << " recommended="
      << record.izanagi_backoff_trace_recommended_delta_sign
      << " assigned=" << record.izanagi_backoff_trace_assigned_invert
      << " realized=" << record.izanagi_backoff_trace_inversion_realized
      << " feasible="
      << record.izanagi_backoff_trace_both_actions_feasible
      << " ceiling=" << record.izanagi_backoff_trace_ceiling_us << '\n';
  return 0;
}
#endif

int main(int argc, char** argv) {
  if (argc != 2)
    return 2;
  const std::string mode(argv[1]);
  if (mode == "series")
    return run_series();
  if (mode == "safe")
    return run_safe();
#if BACKOFF_TRACE
  if (mode == "lcg")
    return run_lcg();
  if (mode == "advance-special")
    return run_advance_special();
#if BACKOFF_COUNT_WINDOW > 0
  if (mode == "terminal")
    return run_terminal();
#endif
  return run_trace_point(mode);
#else
  return 2;
#endif
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
    pin_only_c = _run_patch(tree, PATCH_C, dry_run=True)
    assert pin_only_c.returncode != 0, (
        "patch C unexpectedly applies to the pin alone\n"
        + pin_only_c.stdout
        + pin_only_c.stderr
    )
    applied_a = _run_patch(tree, PATCH_A)
    assert applied_a.returncode == 0, applied_a.stdout + applied_a.stderr
    after_a = (tree / "include" / "backoff.hh").read_text(encoding="utf-8")
    pin_a_c = _run_patch(tree, PATCH_C, dry_run=True)
    assert pin_a_c.returncode != 0, (
        "patch C unexpectedly applies to pin+A\n" + pin_a_c.stdout + pin_a_c.stderr
    )
    pin_a_b = _run_patch(tree, PATCH_B, dry_run=True)
    assert pin_a_b.returncode == 0, pin_a_b.stdout + pin_a_b.stderr
    applied_b = _run_patch(tree, PATCH_B)
    assert applied_b.returncode == 0, applied_b.stdout + applied_b.stderr
    after_b = (tree / "include" / "backoff.hh").read_text(encoding="utf-8")
    after_b_options = (tree / "cmake" / "Options.cmake").read_text(encoding="utf-8")
    pin_a_b_c = _run_patch(tree, PATCH_C, dry_run=True)
    assert pin_a_b_c.returncode == 0, pin_a_b_c.stdout + pin_a_b_c.stderr
    applied_c = _run_patch(tree, PATCH_C)
    assert applied_c.returncode == 0, applied_c.stdout + applied_c.stderr
    after_c = (tree / "include" / "backoff.hh").read_text(encoding="utf-8")
    after_c_options = (tree / "cmake" / "Options.cmake").read_text(encoding="utf-8")
    return SimpleNamespace(
        tree=tree,
        after_a=after_a,
        after_b=after_b,
        after_b_options=after_b_options,
        after_c=after_c,
        after_c_options=after_c_options,
        pin_only_b=pin_only_b,
        pin_only_c=pin_only_c,
        pin_a_c=pin_a_c,
        pin_a_b=pin_a_b,
        pin_a_b_c=pin_a_b_c,
    )


@pytest.fixture(scope="session")
def transition_driver(patched_sources, tmp_path_factory: pytest.TempPathFactory) -> Path:
    work = tmp_path_factory.mktemp("dynamic-backoff-driver")
    variants = work / "variants"
    for name, text in (
        ("stock", patched_sources.after_a),
        ("default_dynamic", patched_sources.after_b),
        ("dynamic", patched_sources.after_b),
        ("trace", patched_sources.after_b),
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
    return [
        line
        for line in result.stdout.strip().splitlines()
        if not line.startswith("IZANAGI_BACKOFF_TRACE")
    ]


def _policy_defines(
    *,
    policy: int,
    step_adapt: int = 0,
    dyn_ceiling: int = 0,
    trace: int = 1,
    max_us: str = "1000",
    seed: str = STEP_POLICY_SEED,
    count_window: str = "0",
    count_cap_us: str = "0",
    terminal_us: str = "0",
) -> tuple[str, ...]:
    return (
        "-DADD_ANALYSIS=0",
        "-DBACKOFF_INCR_MILLI=1000",
        f"-DBACKOFF_MAX_US={max_us}",
        "-DBACKOFF_UPDATE_US=10",
        f"-DBACKOFF_COUNT_WINDOW={count_window}",
        f"-DBACKOFF_COUNT_CAP_US={count_cap_us}",
        f"-DBACKOFF_STEP_ADAPT={step_adapt}",
        f"-DBACKOFF_STEP_POLICY={policy}",
        f"-DBACKOFF_STEP_POLICY_SEED={seed}",
        "-DBACKOFF_STEP_MIN_MILLI=1000",
        "-DBACKOFF_STEP_MAX_MILLI=4000",
        f"-DBACKOFF_DYN_CEILING={dyn_ceiling}",
        f"-DBACKOFF_TRACE={trace}",
        f"-DBACKOFF_TRACE_TERMINAL_US={terminal_us}",
    )


def _compile_policy_driver(
    *,
    work: Path,
    name: str,
    header_text: str,
    dependency_include: Path,
    defines: tuple[str, ...],
) -> Path:
    variant = work / name
    variant.mkdir()
    (variant / "backoff.hh").write_text(header_text, encoding="utf-8")
    source = variant / "driver.cc"
    source.write_text(POLICY_DRIVER_SOURCE, encoding="utf-8")
    binary = variant / "driver"
    compiled = subprocess.run(
        [
            "g++",
            "-std=c++17",
            "-O0",
            *CCBENCH_WARNING_FLAGS,
            f"-I{variant}",
            f"-I{dependency_include}",
            *defines,
            str(source),
            "-o",
            str(binary),
        ],
        capture_output=True,
        text=True,
    )
    assert compiled.returncode == 0, (
        f"{name} failed policy-driver compilation\n"
        + compiled.stdout
        + compiled.stderr
    )
    assert compiled.stderr == "", f"{name} emitted diagnostics\n{compiled.stderr}"
    return binary


@pytest.fixture(scope="session")
def policy_binaries(patched_sources, tmp_path_factory: pytest.TempPathFactory):
    work = tmp_path_factory.mktemp("backoff-policy-drivers")
    include = patched_sources.tree / "include"
    configs = {
        "b0": (patched_sources.after_b, _policy_defines(policy=0, trace=0)),
        "p0": (
            patched_sources.after_c,
            _policy_defines(policy=0, trace=0),
        ),
        "p0-trace": (patched_sources.after_c, _policy_defines(policy=0)),
        "p1": (patched_sources.after_c, _policy_defines(policy=1)),
        "p2": (patched_sources.after_c, _policy_defines(policy=2)),
        "p2-alt-seed": (
            patched_sources.after_c,
            _policy_defines(policy=2, seed="5744733223455690259"),
        ),
        "p0-dyn": (
            patched_sources.after_c,
            _policy_defines(policy=0, dyn_ceiling=1),
        ),
        "p1-dyn": (
            patched_sources.after_c,
            _policy_defines(policy=1, dyn_ceiling=1),
        ),
        "p2-special": (
            patched_sources.after_c,
            _policy_defines(
                policy=2, max_us="18014398509481984"
            ),
        ),
        "p2-terminal": (
            patched_sources.after_c,
            _policy_defines(
                policy=2,
                count_window="10",
                count_cap_us="9223372036854775807",
                terminal_us="1",
            ),
        ),
    }
    return {
        name: _compile_policy_driver(
            work=work,
            name=name,
            header_text=header,
            dependency_include=include,
            defines=defines,
        )
        for name, (header, defines) in configs.items()
    }


def _raw_driver_output(binary: Path, mode: str) -> str:
    result = subprocess.run(
        [str(binary), mode], check=True, capture_output=True, text=True
    )
    return result.stdout


def test_ruling_variants_compile_with_ccbench_warning_flags(
    patched_sources, tmp_path: Path
) -> None:
    source = tmp_path / "preexisting-warning-compile.cc"
    source.write_text('#include "backoff.hh"\n', encoding="utf-8")
    for variant_name, defines in PREEXISTING_WARNING_COMPILE_VARIANTS:
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
            f"{variant_name} failed CCBench warning compilation\n"
            + result.stdout
            + result.stderr
        )
        assert result.stderr == "", (
            f"{variant_name} emitted a diagnostic under -Werror\n"
            + result.stderr
        )


@pytest.mark.parametrize(
    ("variant_name", "defines"),
    WARNING_COMPILE_VARIANTS,
    ids=tuple(name for name, _ in WARNING_COMPILE_VARIANTS),
)
def test_all_24_step_policy_compile_variants_are_warning_clean(
    patched_sources, tmp_path: Path, variant_name: str, defines: tuple[str, ...]
) -> None:
    safe_name = re.sub(r"[^a-zA-Z0-9]+", "-", variant_name)
    source = tmp_path / f"warning-compile-{safe_name}.cc"
    source.write_text('#include "backoff.hh"\n', encoding="utf-8")
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
        f"{variant_name} failed CCBench warning compilation\n"
        + result.stdout
        + result.stderr
    )
    assert result.stderr == "", (
        f"{variant_name} emitted a diagnostic under -Werror\n" + result.stderr
    )


def test_count_window_fires_at_k_boundary_not_k_minus_one(transition_driver: Path) -> None:
    k_minus_one, k_exact, _, _ = _driver_output(transition_driver, "window")[0].split()
    assert (k_minus_one, k_exact) == ("0", "1")


def test_count_window_cap_alone_fires_with_insufficient_count(transition_driver: Path) -> None:
    _, _, cap_only, _ = _driver_output(transition_driver, "window")[0].split()
    assert cap_only == "1"


def test_count_window_cap_comparison_is_overflow_safe(patched_sources) -> None:
    match = re.search(
        r"bool check_update_backoff_at\(.*?\n  \}",
        patched_sources.after_c,
        re.DOTALL,
    )
    assert match is not None
    function = match.group(0)
    division = "elapsed / clocks_per_us_ >= cap_us"
    zero_guard = "if (clocks_per_us_ == 0)\n      return false;"
    assert division in function
    assert "elapsed >= clocks_per_us_ * cap_us" not in function
    assert zero_guard in function
    assert function.index(zero_guard) < function.index(division)


def test_count_window_never_fires_before_minimum_elapsed_time(transition_driver: Path) -> None:
    _, _, _, before_minimum = _driver_output(transition_driver, "window")[0].split()
    assert before_minimum == "0"


def test_count_scan_is_rate_limited_to_once_per_window(transition_driver: Path) -> None:
    assert _driver_output(transition_driver, "poll")[0] == "0 1 0 0 1"


def test_k_positive_leader_skips_counter_scan_before_minimum_elapsed(
    transition_driver: Path,
) -> None:
    assert "dynamic_early=0" in _driver_output(transition_driver, "leader")[0]


def test_k_zero_leader_skips_counter_scan_before_stock_time_gate(
    transition_driver: Path,
) -> None:
    assert "default_early=0" in _driver_output(transition_driver, "leader")[0]


def test_k_positive_leader_samples_timestamp_after_counter_scan(
    transition_driver: Path,
) -> None:
    line = _driver_output(transition_driver, "leader")[0]
    assert "dynamic_due=2" in line
    assert "sample_after_scan=1" in line


def test_trace_window_uses_post_scan_sample_timestamp(
    transition_driver: Path,
) -> None:
    assert _driver_output(transition_driver, "sample-window")[0] == (
        "gate=1 window_us=25 tsc=25"
    )


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


def test_positive_gradient_doubles_dynamic_ceiling_and_clamps_at_max(
    transition_driver: Path,
) -> None:
    assert _driver_output(transition_driver, "ceiling-growth")[0] == (
        "50,100,200,400,800,1000,1000"
    )


def test_default_dynamic_path_matches_pin_plus_a_stock_transitions(
    transition_driver: Path,
) -> None:
    stock, dynamic = _driver_output(transition_driver, "stock")
    assert stock == "100,0,200,900,400"
    assert dynamic == stock


def test_default_dynamic_path_matches_stock_for_nonzero_gradients(
    transition_driver: Path,
) -> None:
    stock, dynamic = _driver_output(transition_driver, "stock-gradient")
    assert stock == "200,100"
    assert dynamic == stock


def test_public_define_relation_static_asserts_are_fail_closed(patched_sources) -> None:
    source = patched_sources.after_b
    assert "BACKOFF_COUNT_CAP_US == 0 ||" in source
    assert "BACKOFF_COUNT_CAP_US >= BACKOFF_UPDATE_US" in source
    assert "!BACKOFF_STEP_ADAPT || kStepMin > 0" in source
    assert "!BACKOFF_DYN_CEILING || kStepMax <= 50 / 4" in source
    assert "!BACKOFF_DYN_CEILING || kStepMax * 4 <= 50" not in source


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


def test_patch_c_uses_numeric_if_and_adds_no_include(patched_sources) -> None:
    patch_text = PATCH_C.read_text(encoding="utf-8")
    changed_paths = tuple(
        re.findall(r"^diff --git a/(\S+) b/(\S+)$", patch_text, re.MULTILINE)
    )
    assert changed_paths == (
        ("cmake/Options.cmake", "cmake/Options.cmake"),
        ("include/backoff.hh", "include/backoff.hh"),
    )
    assert re.search(
        r"^\+#if BACKOFF_STEP_POLICY(?: == 2| > 0| == 1)$",
        patch_text,
        re.MULTILINE,
    )
    assert re.search(
        r"^\+#ifdef BACKOFF_STEP_POLICY(?:\s|$)", patch_text, re.MULTILINE
    ) is None
    assert patch_text.count("+#ifndef BACKOFF_STEP_POLICY\n") == 1
    assert patch_text.count("+#ifndef BACKOFF_STEP_POLICY_SEED\n") == 1
    assert patch_text.count("+#ifndef BACKOFF_TRACE_TERMINAL_US\n") == 1
    assert re.search(r"^\+\s*#\s*include", patch_text, re.MULTILINE) is None
    assert patched_sources.pin_only_c.returncode != 0
    assert patched_sources.pin_a_c.returncode != 0
    assert patched_sources.pin_a_b_c.returncode == 0
    assert _include_lines(patched_sources.after_c) == _include_lines(
        patched_sources.after_b
    )


def test_patch_c_pins_trace_stdout_version_three() -> None:
    patch_text = PATCH_C.read_text(encoding="utf-8")
    assert patch_text.count('IZANAGI_BACKOFF_TRACE v=3 seq=') == 1
    assert patch_text.count('IZANAGI_BACKOFF_TRACE_SUMMARY v=3 updates=') == 1
    assert re.search(r'^\+.*IZANAGI_BACKOFF_TRACE v=2 ', patch_text, re.MULTILINE) is None
    assert (
        re.search(
            r'^\+.*IZANAGI_BACKOFF_TRACE_SUMMARY v=2 ',
            patch_text,
            re.MULTILINE,
        )
        is None
    )


def test_patch_c_seed_guard_is_exact_policy_two() -> None:
    patch_text = PATCH_C.read_text(encoding="utf-8")
    seed_symbol = patch_text.index(
        "+  static constexpr uint64_t kBackoffStepPolicySeed"
    )
    seed_guard = patch_text.rfind("+#if ", 0, seed_symbol)
    assert patch_text[seed_guard:seed_symbol].splitlines()[0] == (
        "+#if BACKOFF_STEP_POLICY == 2"
    )


def test_patch_c_seed_literal_uses_no_token_paste() -> None:
    patch_text = PATCH_C.read_text(encoding="utf-8")
    assert "##" not in patch_text
    assert "%:%:" not in patch_text
    assert patch_text.count(
        "+#define BACKOFF_STEP_POLICY_SEED_STRING_INNER(value) #value\n"
    ) == 1


def test_patch_c_cmake_cache_default_is_zero(patched_sources) -> None:
    policy_line = (
        'set(CCBENCH_BACKOFF_STEP_POLICY 0 CACHE STRING '
        '"backoff step policy (0=stock, 1=invert, 2=randomized)")'
    )
    seed_line = (
        "set(CCBENCH_BACKOFF_STEP_POLICY_SEED 11400714819323198485 "
        'CACHE STRING "deterministic backoff step policy seed")'
    )
    terminal_line = (
        "set(CCBENCH_BACKOFF_TRACE_TERMINAL_US 0 CACHE STRING "
        '"count-closed terminal trace deadline in us (0=off)")'
    )
    patch_text = PATCH_C.read_text(encoding="utf-8")
    assert patch_text.count(f"+{policy_line}\n") == 1
    assert patch_text.count(f"+{seed_line}\n") == 1
    assert patch_text.count(f"+{terminal_line}\n") == 1
    assert patched_sources.after_b_options.count(policy_line) == 0
    assert patched_sources.after_b_options.count(seed_line) == 0
    assert patched_sources.after_b_options.count(terminal_line) == 0
    assert patched_sources.after_c_options.count(policy_line) == 1
    assert patched_sources.after_c_options.count(seed_line) == 1
    assert patched_sources.after_c_options.count(terminal_line) == 1


def test_patch_c_universal_definition_is_inside_the_function(
    patched_sources,
) -> None:
    options = patched_sources.after_c_options
    match = re.search(
        r"function\(ccbench_universal_definitions out_var\).*?endfunction\(\)",
        options,
        re.DOTALL,
    )
    assert match is not None
    function_body = match.group(0)
    expected_lines = (
        "BACKOFF_STEP_POLICY=${CCBENCH_BACKOFF_STEP_POLICY}",
        "BACKOFF_STEP_POLICY_SEED=${CCBENCH_BACKOFF_STEP_POLICY_SEED}",
        "BACKOFF_TRACE_TERMINAL_US=${CCBENCH_BACKOFF_TRACE_TERMINAL_US}",
    )
    for line in expected_lines:
        assert options.count(line) == 1
        assert function_body.count(line) == 1


@pytest.mark.parametrize("invalid_policy", (-1, 3))
def test_step_policy_static_assert_rejects_out_of_domain_values(
    patched_sources, tmp_path: Path, invalid_policy: int
) -> None:
    source = tmp_path / f"invalid-policy-{invalid_policy}.cc"
    source.write_text('#include "backoff.hh"\n', encoding="utf-8")
    defines = tuple(
        item
        for item in DEFAULT_DEFINES
        if not item.startswith("-DBACKOFF_STEP_POLICY=")
    )
    result = subprocess.run(
        [
            "g++",
            "-std=c++17",
            "-O0",
            *CCBENCH_WARNING_FLAGS,
            "-fsyntax-only",
            f"-I{patched_sources.tree / 'include'}",
            *defines,
            f"-DBACKOFF_STEP_POLICY={invalid_policy}",
            str(source),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "backoff step policy must be 0, 1 or 2" in result.stderr


@pytest.mark.parametrize("invalid_terminal_us", ("-1", "1.5"))
def test_terminal_deadline_static_assert_rejects_out_of_domain_values(
    patched_sources, tmp_path: Path, invalid_terminal_us: str
) -> None:
    source = tmp_path / f"invalid-terminal-{invalid_terminal_us}.cc"
    source.write_text('#include "backoff.hh"\n', encoding="utf-8")
    defines = tuple(
        item
        for item in _policy_defines(policy=0, trace=1)
        if not item.startswith("-DBACKOFF_TRACE_TERMINAL_US=")
    )
    result = subprocess.run(
        [
            "g++",
            "-std=c++17",
            "-O0",
            *CCBENCH_WARNING_FLAGS,
            "-fsyntax-only",
            f"-I{patched_sources.tree / 'include'}",
            *defines,
            f"-DBACKOFF_TRACE_TERMINAL_US={invalid_terminal_us}",
            str(source),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert (
        "terminal trace deadline must be a nonnegative whole number of us"
        in result.stderr
    )


def test_policy_zero_matches_patch_b_transitions_exactly(policy_binaries) -> None:
    b_only = _driver_output(policy_binaries["b0"], "series")
    policy_zero = _driver_output(policy_binaries["p0"], "series")
    assert policy_zero == b_only


def test_policy_one_reverses_safe_positive_and_negative_recommendations(
    policy_binaries,
) -> None:
    assert _driver_output(policy_binaries["p0"], "safe") == ["101,99"]
    assert _driver_output(policy_binaries["p1"], "safe") == ["99,101"]


def test_safe_negative_scene_reports_the_intended_prestate_and_gradient(
    policy_binaries,
) -> None:
    assert _driver_output(
        policy_binaries["p0-trace"], "safe-negative-trace"
    ) == [
        "before=100 after=99 gradient=-1 step=1 recommended=-1 assigned=0 "
        "realized=0 feasible=1 ceiling=1000"
    ]


def test_policy_inversion_is_shared_by_all_step_ceiling_combinations(
    patched_sources, tmp_path: Path
) -> None:
    observed: dict[tuple[int, int], str] = {}
    for step_adapt in (0, 1):
        for dyn_ceiling in (0, 1):
            name = f"policy-one-step-{step_adapt}-ceiling-{dyn_ceiling}"
            binary = _compile_policy_driver(
                work=tmp_path,
                name=name,
                header_text=patched_sources.after_c,
                dependency_include=patched_sources.tree / "include",
                defines=_policy_defines(
                    policy=1,
                    step_adapt=step_adapt,
                    dyn_ceiling=dyn_ceiling,
                    trace=1,
                ),
            )
            output = _driver_output(binary, "safe-negative-trace")
            assert len(output) == 1
            observed[(step_adapt, dyn_ceiling)] = output[0]
    assert observed == {
        (0, 0): "before=100 after=101 gradient=-1 step=1 recommended=-1 "
        "assigned=1 realized=1 feasible=1 ceiling=1000",
        (0, 1): "before=100 after=101 gradient=-1 step=1 recommended=-1 "
        "assigned=1 realized=1 feasible=1 ceiling=1000",
        (1, 0): "before=100 after=101 gradient=-1 step=1 recommended=-1 "
        "assigned=1 realized=1 feasible=1 ceiling=1000",
        (1, 1): "before=100 after=101 gradient=-1 step=1 recommended=-1 "
        "assigned=1 realized=1 feasible=1 ceiling=1000",
    }


def test_inversion_is_applied_before_clamp(policy_binaries) -> None:
    assert _driver_output(policy_binaries["p1"], "partial-lower") == [
        "before=0.5 after=0 gradient=1 step=1 recommended=1 assigned=1 realized=0 "
        "feasible=0 ceiling=1000"
    ]


def test_policy_two_assignment_sequence_is_exact(policy_binaries) -> None:
    sequence, values = _driver_output(policy_binaries["p2"], "lcg")
    assert sequence == "0111001000100110"
    assert values == "101,99,99,99,101,101,99,101,101,101,99,101,101,99,99,101"


def test_policy_two_nondefault_seed_assignment_matches_independent_lcg(
    policy_binaries,
) -> None:
    observed, _values = _driver_output(policy_binaries["p2-alt-seed"], "lcg")
    state = 5_744_733_223_455_690_259
    expected = []
    for _ in range(16):
        state = (
            state * 6_364_136_223_846_793_005
            + 1_442_695_040_888_963_407
        ) % (2**64)
        expected.append(str((state >> 63) & 1))
    assert observed == "".join(expected)


def test_policy_two_lcg_literals_are_exact() -> None:
    patch_text = PATCH_C.read_text(encoding="utf-8")
    update = (
        "+    backoff_step_policy_state_ =\n"
        "+        backoff_step_policy_state_ * 6364136223846793005ULL +\n"
        "+        1442695040888963407ULL;\n"
    )
    assert patch_text.count(update) == 1


def test_policy_two_assigned_zero_follows_recommendation(policy_binaries) -> None:
    sequence, values = _driver_output(policy_binaries["p2"], "lcg")
    assert sequence[0] == "0"
    assert values.split(",")[0] == "101"


def test_policy_two_assigned_one_reverses_recommendation(policy_binaries) -> None:
    sequence, values = _driver_output(policy_binaries["p2"], "lcg")
    assert sequence[1] == "1"
    assert values.split(",")[1] == "99"


def test_policy_two_lcg_advances_on_every_update(policy_binaries) -> None:
    assert _driver_output(policy_binaries["p2-special"], "advance-special") == [
        "bits=01110 gradients=1,0,0,1,1 "
        "recommendations=1,-1,0,1,1 clamp_after=0"
    ]


def test_trace_v3_records_parity_recommendation_not_gradient_alias(
    policy_binaries,
) -> None:
    assert _driver_output(policy_binaries["p0-trace"], "parity") == [
        "before=100 after=99 gradient=0 step=1 recommended=-1 assigned=0 realized=0 "
        "feasible=1 ceiling=1000"
    ]


def test_inversion_realized_is_one_only_for_unclamped_exact_inverse(
    policy_binaries,
) -> None:
    assert _driver_output(policy_binaries["p1"], "safe-trace") == [
        "before=100 after=99 gradient=1 step=1 recommended=1 assigned=1 realized=1 "
        "feasible=1 ceiling=1000"
    ]
    assert _driver_output(policy_binaries["p1"], "partial-lower") == [
        "before=0.5 after=0 gradient=1 step=1 recommended=1 assigned=1 realized=0 "
        "feasible=0 ceiling=1000"
    ]


def test_inversion_realized_is_zero_at_lower_and_fixed_upper_clamps(
    policy_binaries,
) -> None:
    assert _driver_output(policy_binaries["p1"], "partial-lower") == [
        "before=0.5 after=0 gradient=1 step=1 recommended=1 assigned=1 realized=0 "
        "feasible=0 ceiling=1000"
    ]
    assert _driver_output(policy_binaries["p1"], "fixed-upper") == [
        "before=999.5 after=1000 gradient=-1 step=1 recommended=-1 "
        "assigned=1 realized=0 "
        "feasible=0 ceiling=1000"
    ]


def test_dynamic_ceiling_shrink_can_make_both_arms_equal(policy_binaries) -> None:
    assert _driver_output(policy_binaries["p0-dyn"], "dynamic-shrink") == [
        "before=200 after=100 gradient=-1 step=1 recommended=-1 assigned=0 realized=0 "
        "feasible=0 ceiling=100"
    ]
    assert _driver_output(policy_binaries["p1-dyn"], "dynamic-shrink") == [
        "before=200 after=100 gradient=-1 step=1 recommended=-1 assigned=1 realized=0 "
        "feasible=0 ceiling=100"
    ]


def test_both_actions_feasible_checks_recommended_upper_boundary(
    policy_binaries,
) -> None:
    assert _driver_output(policy_binaries["p0-trace"], "recommended-upper") == [
        "before=999.5 after=1000 gradient=1 step=1 recommended=1 assigned=0 "
        "realized=0 feasible=0 ceiling=1000"
    ]


def test_both_actions_feasible_is_computed_before_assignment(
    patched_sources, policy_binaries
) -> None:
    source = patched_sources.after_c
    feasible = source.index(
        "const int izanagi_backoff_trace_both_actions_feasible ="
    )
    policy_assignment = source.index("#if BACKOFF_STEP_POLICY == 1", feasible)
    clamp = source.index("if (new_backoff < kMinBackoff)", policy_assignment)
    assert feasible < policy_assignment < clamp
    assert _driver_output(policy_binaries["p1"], "partial-lower") == [
        "before=0.5 after=0 gradient=1 step=1 recommended=1 assigned=1 realized=0 "
        "feasible=0 ceiling=1000"
    ]


def test_lcg_preprocesses_out_of_policy_zero_and_into_policy_two(
    patched_sources, tmp_path: Path
) -> None:
    source = tmp_path / "preprocess-policy-lcg.cc"
    source.write_text('#include "backoff.hh"\n', encoding="utf-8")
    outputs: dict[int, str] = {}
    alternate_seed = "5744733223455690259"
    for policy in (0, 2):
        result = subprocess.run(
            [
                "g++",
                "-std=c++17",
                "-E",
                "-P",
                f"-I{patched_sources.tree / 'include'}",
                *_policy_defines(policy=policy, trace=0, seed=alternate_seed),
                str(source),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"policy {policy} preprocessing failed\n"
            + result.stdout
            + result.stderr
        )
        outputs[policy] = result.stdout

    normalized_outputs = {
        policy: " ".join(output.split()) for policy, output in outputs.items()
    }
    lcg_tokens = (
        alternate_seed,
        "kBackoffStepPolicySeed",
        "backoff_step_policy_state_",
        "backoff_step_policy_state_ * 6364136223846793005ULL",
        "backoff_step_policy_state_ * 6364136223846793005ULL + "
        "1442695040888963407ULL",
    )
    for token in lcg_tokens:
        assert token not in normalized_outputs[0], f"policy 0 retained {token}"
        assert token in normalized_outputs[2], f"policy 2 omitted {token}"


def test_trace_preprocesses_out_of_trace_zero_builds(
    patched_sources, tmp_path: Path
) -> None:
    source = tmp_path / "preprocess-policy.cc"
    source.write_text('#include "backoff.hh"\n', encoding="utf-8")
    forbidden = (
        "izanagi_backoff_trace",
        "IZANAGI_BACKOFF_TRACE",
        "recommended_delta_sign",
        "assigned_invert",
        "inversion_realized",
        "both_actions_feasible",
        "BACKOFF_TRACE_TERMINAL_US",
        "kTraceTerminalUs",
        "terminal_recorded_",
        "terminal_flush",
        "izanagi_backoff_trace_flushes",
    )
    for policy in (0, 1, 2):
        result = subprocess.run(
            [
                "g++",
                "-std=c++17",
                "-E",
                "-P",
                f"-I{patched_sources.tree / 'include'}",
                *_policy_defines(policy=policy, trace=0),
                str(source),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"policy {policy} preprocessing failed\n"
            + result.stdout
            + result.stderr
        )
        for symbol in forbidden:
            assert symbol not in result.stdout, (
                f"policy {policy} trace=0 retained {symbol}"
            )


def test_terminal_instrumentation_preprocesses_completely_out_of_trace_zero(
    patched_sources, tmp_path: Path
) -> None:
    source = tmp_path / "preprocess-terminal-trace-zero.cc"
    source.write_text('#include "backoff.hh"\n', encoding="utf-8")
    result = subprocess.run(
        [
            "g++",
            "-std=c++17",
            "-E",
            "-P",
            f"-I{patched_sources.tree / 'include'}",
            *_policy_defines(
                policy=2,
                trace=0,
                count_window="10000",
                count_cap_us="9223372036854775807",
                terminal_us="5000000",
            ),
            str(source),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    forbidden = (
        "BACKOFF_TRACE_TERMINAL_US",
        "kTraceTerminalUs",
        "start_time_",
        "terminal_recorded_",
        "izanagi_backoff_trace_handle_terminal_at",
        "izanagi_backoff_trace_terminal_flush",
        "izanagi_backoff_trace_flushes",
        "IZANAGI_BACKOFF_TRACE v=3",
    )
    for token in forbidden:
        assert token not in result.stdout, f"trace=0 retained {token}"


def test_trace_zero_compiles_without_terminal_deadline_define(
    patched_sources, tmp_path: Path
) -> None:
    source = tmp_path / "compile-trace-zero-without-terminal-define.cc"
    source.write_text('#include "backoff.hh"\n', encoding="utf-8")
    defines = tuple(
        item
        for item in _policy_defines(policy=2, trace=0)
        if not item.startswith("-DBACKOFF_TRACE_TERMINAL_US=")
    )
    assert all("BACKOFF_TRACE_TERMINAL_US" not in item for item in defines)
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
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""


def test_terminal_is_recorded_once_and_remains_the_last_event(policy_binaries) -> None:
    stdout = _raw_driver_output(policy_binaries["p2-terminal"], "terminal")
    event_lines = [
        line
        for line in stdout.splitlines()
        if line.startswith("IZANAGI_BACKOFF_TRACE v=3 ")
    ]
    assert len(event_lines) == 2
    assert "seq=0 " in event_lines[0]
    assert "terminal_flush=0" in event_lines[0]
    assert "seq=1 " in event_lines[1]
    assert "trigger=3 " in event_lines[1]
    assert "terminal_flush=1" in event_lines[1]
    assert sum("terminal_flush=1" in line for line in event_lines) == 1
    assert (
        "IZANAGI_BACKOFF_TRACE_SUMMARY v=3 updates=1 retained=1 "
        "dropped=0 flushes=1"
    ) in stdout


def test_terminal_call_stops_once_then_controller_lcg_and_assignment_resume(
    policy_binaries,
) -> None:
    assert _driver_output(policy_binaries["p2-terminal"], "terminal") == [
        "updates=1 retained=1 dropped=0 flushes=1 terminal_recorded=1 "
        "seq=1 trigger=3 assigned=-1 recommended=0 realized=0 feasible=0 "
        "terminal_flush=1 lcg_terminal_unchanged=1 lcg_repeat_advanced=1 "
        "controller_repeat_updated=1 backoff_terminal_unchanged=1 "
        "backoff_after_repeat=102"
    ]


def test_terminal_recorded_guard_resumes_controller_before_eligibility_checks(
    patched_sources,
) -> None:
    source = patched_sources.after_c
    handler = re.search(
        r"bool izanagi_backoff_trace_handle_terminal_at\(.*?\n  \}",
        source,
        re.DOTALL,
    )
    assert handler is not None
    body = handler.group(0)
    recorded_guard = "if (terminal_recorded_)\n      return false;"
    eligibility = "if (kTraceTerminalUs == 0 || clocks_per_us_ == 0 ||"
    assert recorded_guard in body
    assert eligibility in body
    assert body.index(recorded_guard) < body.index(eligibility)


@pytest.mark.parametrize(
    ("binary_name", "mode", "expected_terminal_count"),
    (("p2", "emit", 0), ("p2-terminal", "terminal", 1)),
    ids=("terminal-0", "terminal-1"),
)
def test_emitter_stdout_parses_with_the_real_parser(
    policy_binaries, binary_name: str, mode: str, expected_terminal_count: int
) -> None:
    from tools.pegasus.probes import t2187_adaptive_const_probe as driver

    stdout = _raw_driver_output(policy_binaries[binary_name], mode)
    event_lines = [
        line
        for line in stdout.splitlines()
        if line.startswith("IZANAGI_BACKOFF_TRACE v=3 ")
    ]
    assert len(event_lines) == 1 + expected_terminal_count
    assert sum(" terminal_flush=1" in line for line in event_lines) == (
        expected_terminal_count
    )
    assert "IZANAGI_BACKOFF_TRACE_SUMMARY v=3 " in stdout
    assert f" flushes={expected_terminal_count}\n" in stdout
    events, summary, _directional = driver._parse_backoff_trace(stdout)
    assert sum(event["terminal_flush"] for event in events) == (
        expected_terminal_count
    )
    assert summary == {
        "updates": 1,
        "retained": 1,
        "dropped": 0,
        "flushes": expected_terminal_count,
    }


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
