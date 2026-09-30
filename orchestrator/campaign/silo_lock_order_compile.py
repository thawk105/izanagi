"""Isolated C++17 checking and separate UBSan checks for hand order policies."""
from __future__ import annotations

from pathlib import Path
import tempfile

from . import axis_silo_lock_order as axis
from .silo_policy_compile import (COMPILE_TIMEOUT, RUN_TIMEOUT, CompileDecision,
                                  _run, _version, find_compiler)
from .silo_policy_grammar import ORDER_POLICY_PROFILE, PolicyDecision, validate_policy

API_HEADER = Path(__file__).resolve().parents[2] / axis.API_HEADER


def _translation_unit(source: str) -> str:
    return ('#include <cstdint>\n#include <algorithm>\n'
            f'#include "{API_HEADER}"\n'
            'namespace izanagi_silo_order {\n' + source + '\n}\n')


def compile_order(source: str, *, compiler: str, scratch_dir: str) -> CompileDecision:
    root = Path(scratch_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='silo-order-', dir=root) as directory:
        tu = Path(directory) / 'order.cpp'
        tu.write_text(_translation_unit(source), encoding='utf-8')
        command = (compiler, '-std=c++17', '-Wall', '-Wextra', '-Werror',
                   '-fsyntax-only', str(tu))
        rc, timed, missing, diagnostic, truncated = _run(command, directory, COMPILE_TIMEOUT)
        version = None if missing else _version(compiler, directory)
        return CompileDecision(rc == 0 and not timed and not missing, rc, timed, missing,
                               diagnostic, truncated, command, version)


def check_order_body(source: str, *, compiler: str, scratch_dir: str
                     ) -> tuple[PolicyDecision, CompileDecision | None]:
    grammar = validate_policy(source, ORDER_POLICY_PROFILE)
    return grammar, compile_order(source, compiler=compiler, scratch_dir=scratch_dir) if grammar.accepted else None


_HARNESS = r'''
#include <cstdio>
#include <limits>
int main() {
  using namespace izanagi_silo_order_api;
  using namespace izanagi_silo_order;
  volatile uint64_t sink = 0;
  unsigned calls = 0;
  for (uint32_t epoch : {0u, UINT32_MAX}) {
    for (uint32_t tid : {0u, (1u << 29u) - 1u}) {
      for (bool locked : {false, true}) {
        OrderState state{};
        sink = order_priority(state, EntryContext{epoch, tid, locked}); ++calls;
      }
    }
  }
  for (uint32_t count : {0u, 1u, 2u, 17u}) {
    for (uint64_t random : {0ul, UINT64_MAX}) {
      OrderState state{};
      sink = order_enabled(state, TxnContext{count, random}); ++calls;
      order_on_commit(state, CommitContext{}); ++calls;
      for (uint32_t reason = 0; reason < 8; ++reason) {
        order_after_abort(state, AbortContext{static_cast<AbortReason>(reason), random}); ++calls;
      }
      order_after_abort(state, AbortContext{AbortReason::lock_conflict, random}); ++calls;
      order_after_abort(state, AbortContext{AbortReason::lock_conflict, random}); ++calls;
    }
  }
  (void)sink;
  std::printf("calls=%u\n", calls);
  return 0;
}
'''
_EXPECTED_CALLS = 2 * 2 * 2 + 4 * 2 * (1 + 1 + 8 + 2)


def run_ubsan_harness(policy_dir: str, *, compiler: str, scratch_dir: str) -> dict:
    """Check hand policies separately; candidate gate never invokes this harness."""
    root = Path(scratch_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    policies = sorted(Path(policy_dir).glob('*.cpp'))
    results = {}
    with tempfile.TemporaryDirectory(prefix='silo-order-ubsan-', dir=root) as directory:
        version = _version(compiler, directory)
        for policy in policies:
            tu = Path(directory) / (policy.stem + '.cpp')
            exe = Path(directory) / policy.stem
            tu.write_text(_translation_unit(policy.read_text()) + _HARNESS, encoding='utf-8')
            command = (compiler, '-std=c++17', '-Wall', '-Wextra', '-Werror',
                       '-fsanitize=undefined', '-fno-sanitize-recover=undefined',
                       '-O1', '-g', str(tu), '-o', str(exe))
            rc, timed, missing, diagnostic, truncated = _run(command, directory, COMPILE_TIMEOUT)
            row = dict(build_returncode=rc, returncode=None, timed_out=timed,
                       unavailable=missing, calls=0, ubsan=False, diagnostic=diagnostic,
                       diagnostic_truncated=truncated, command=command, passed=False)
            if rc == 0 and not timed and not missing:
                rc, timed, missing, diagnostic, truncated = _run((str(exe),), directory, RUN_TIMEOUT)
                reported = 'runtime error:' in diagnostic
                calls = _EXPECTED_CALLS if f'calls={_EXPECTED_CALLS}\n' in diagnostic else 0
                row.update(returncode=rc, timed_out=timed, unavailable=missing,
                           calls=calls, ubsan=reported, diagnostic=diagnostic,
                           diagnostic_truncated=truncated,
                           passed=rc == 0 and not timed and not missing and not reported
                                  and calls == _EXPECTED_CALLS)
            results[policy.stem] = row
    return dict(compiler=compiler, compiler_version=version, policies=results,
                abort_reasons=8, entry_contexts=8, write_counts=(0, 1, 2, 17),
                all_pass=bool(policies) and all(row['passed'] for row in results.values()))
