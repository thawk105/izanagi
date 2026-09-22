"""Isolated policy translation units and a finite UBSan conformance harness."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import tempfile

from .silo_policy_grammar import PolicyDecision, validate_policy

API_HEADER = Path(__file__).with_name('silo_function_policy_api.hh').resolve()
COMPILE_TIMEOUT = 10.0
RUN_TIMEOUT = 3.0
DIAGNOSTIC_LIMIT = 16 * 1024
# Also bounds on-disk compiler diagnostics (and executable output files).
FILE_LIMIT = 64 * 1024 * 1024


@dataclass(frozen=True)
class CompileDecision:
    accepted: bool
    returncode: int | None
    timed_out: bool
    unavailable: bool
    diagnostic: str
    diagnostic_truncated: bool
    command: tuple[str, ...]
    compiler_version: str | None


def find_compiler() -> str | None:
    for name in ('g++-13', 'g++-12', 'g++'):
        found = shutil.which(name)
        if found:
            return found
    return None


def _limits():
    resource.setrlimit(resource.RLIMIT_CPU, (8, 9))
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (FILE_LIMIT, FILE_LIMIT))


def _environment():
    env = os.environ.copy()
    for key in ('CPATH', 'CPLUS_INCLUDE_PATH', 'C_INCLUDE_PATH', 'GCC_EXEC_PREFIX', 'COMPILER_PATH'):
        env.pop(key, None)
    env['LC_ALL'] = 'C'
    env['UBSAN_OPTIONS'] = 'halt_on_error=1:print_stacktrace=0'
    return env


def _run(command, directory, timeout):
    """No unbounded PIPE buffering; kill the whole session on timeout."""
    with tempfile.TemporaryFile(dir=directory) as diagnostic:
        try:
            proc = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                    stdout=diagnostic, stderr=diagnostic,
                                    env=_environment(), cwd=directory,
                                    start_new_session=True, preexec_fn=_limits)
        except OSError as e:
            return None, False, True, str(e)[:DIAGNOSTIC_LIMIT], False
        timed_out = False
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            # Reap descendants even if the driver exited before its children.
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
        size = diagnostic.seek(0, os.SEEK_END)
        diagnostic.seek(0)
        text = diagnostic.read(DIAGNOSTIC_LIMIT).decode('utf-8', errors='replace')
        text = text.encode('utf-8')[:DIAGNOSTIC_LIMIT].decode('utf-8', errors='ignore')
        return proc.returncode, timed_out, False, text, size > DIAGNOSTIC_LIMIT


def _version(compiler, directory):
    rc, timed, missing, text, _ = _run([compiler, '--version'], directory, 2.0)
    return text.splitlines()[0][:512] if rc == 0 and not timed and not missing and text else None


def _translation_unit(source):
    return ('#include <cstdint>\n#include <algorithm>\n'
            f'#include "{API_HEADER}"\n'
            'namespace izanagi_silo_policy {\n' + source + '\n}\n')


def compile_policy(source: str, *, compiler: str, scratch_dir: str) -> CompileDecision:
    root = Path(scratch_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='policy-', dir=root) as directory:
        tu = Path(directory) / 'policy.cpp'
        tu.write_text(_translation_unit(source), encoding='utf-8')
        command = (compiler, '-std=c++17', '-Wall', '-Wextra', '-Werror', '-fsyntax-only', str(tu))
        rc, timed, missing, text, truncated = _run(command, directory, COMPILE_TIMEOUT)
        version = None if missing else _version(compiler, directory)
        return CompileDecision(rc == 0 and not timed and not missing, rc, timed, missing,
                               text, truncated, command, version)


def check_policy_body(source: str, *, compiler: str, scratch_dir: str
                      ) -> tuple[PolicyDecision, CompileDecision | None]:
    grammar = validate_policy(source)
    return grammar, compile_policy(source, compiler=compiler, scratch_dir=scratch_dir) if grammar.accepted else None


_HARNESS = r'''
#include <cstdio>
int main() {
  using namespace izanagi_silo_api;
  using namespace izanagi_silo_policy;
  unsigned calls = 0;
  volatile uint64_t sink = 0;
  for (uint32_t reason = 0; reason < 8; ++reason) {
    for (uint32_t attempt = 0; attempt < 34; ++attempt) {
      PolicyState s{};
      AbortContext a{static_cast<AbortReason>(reason), 0xFEDCBA9876543210ul + attempt};
      LockContext l{attempt, 0x123456789ABCDEF0ul + reason};
      CommitContext c{};
      sink = policy_after_abort(s, a); ++calls;
      auto r = policy_on_lock_conflict(s, l); ++calls;
      sink = r.wait_us;
      policy_on_commit(s, c); ++calls;
      r = policy_on_lock_conflict(s, l); ++calls;
      sink = r.wait_us;
      sink = policy_after_abort(s, a); ++calls;
      PolicyState abort_only{};
      sink = policy_after_abort(abort_only, a); ++calls;
      sink = policy_after_abort(abort_only, a); ++calls;
    }
  }
  (void)sink;
  std::printf("calls=%u\n", calls);
  return 0;
}
'''

_UB_CASES = {
    'division_zero': 'volatile uint32_t value = static_cast<uint32_t>(c.rand); volatile uint32_t zero = c.attempt; sink = value / zero;',
    'overshift': 'volatile uint32_t value = static_cast<uint32_t>(c.rand); volatile uint32_t shift = c.attempt; sink = value << shift;',
    'signed_overflow': 'volatile int value = static_cast<int>(c.rand); volatile int delta = static_cast<int>(c.attempt); sink = value + delta;',
}


def run_ubsan_harness(policy_dir: str, *, compiler: str, scratch_dir: str) -> dict:
    root = Path(scratch_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    policies = sorted(Path(policy_dir).glob('*.cpp'))
    results = {}
    with tempfile.TemporaryDirectory(prefix='ubsan-', dir=root) as directory:
        version = _version(compiler, directory)
        sources = {p.stem: (_translation_unit(p.read_text()) + _HARNESS, False) for p in policies}
        for name, expression in _UB_CASES.items():
            # Runtime input is parsed in a separate process; no constant-folded UB.
            source = ('#include <cstdint>\n#include <cstdlib>\n' + f'#include "{API_HEADER}"\n' +
                      'int main(int argc, char** argv) { if (argc != 3) return 2; '
                      'izanagi_silo_api::LockContext c{static_cast<uint32_t>(std::strtoul(argv[1], nullptr, 10)), '
                      'std::strtoul(argv[2], nullptr, 10)}; volatile uint32_t sink = 0; ' + expression + ' (void)sink; return 0; }\n')
            sources['ub_' + name] = (source, True)
        for name, (source, negative) in sources.items():
            tu = Path(directory) / (name + '.cpp')
            exe = Path(directory) / name
            tu.write_text(source)
            command = (compiler, '-std=c++17', '-Wall', '-Wextra', '-Werror', '-fsanitize=undefined', '-fno-sanitize-recover=undefined', '-O1', '-g', str(tu), '-o', str(exe))
            rc, timed, missing, diagnostic, truncated = _run(command, directory, COMPILE_TIMEOUT)
            row = dict(negative=negative, build_returncode=rc, returncode=None, timed_out=timed,
                       unavailable=missing, calls=0, ubsan=False, diagnostic=diagnostic,
                       diagnostic_truncated=truncated, command=command, passed=False)
            if rc == 0 and not timed and not missing:
                args = [str(exe)]
                if negative:
                    args += [str(32 if name == 'ub_overshift' else 1 if name == 'ub_signed_overflow' else 0), '2147483647']
                rc, timed, missing, diagnostic, truncated = _run(args, directory, RUN_TIMEOUT)
                reported = 'runtime error:' in diagnostic
                count = 1904 if 'calls=1904\n' in diagnostic else 0
                row.update(returncode=rc, timed_out=timed, unavailable=missing, calls=count,
                           ubsan=reported, diagnostic=diagnostic, diagnostic_truncated=truncated,
                           passed=not timed and not missing and ((rc != 0 and reported) if negative else (rc == 0 and not reported and count == 1904)))
            results[name] = row
    return dict(compiler=compiler, compiler_version=version, policies=results,
                abort_reasons=8, attempts=34, sequences=['abort-lock-commit-lock-abort', 'abort-abort'],
                all_pass=bool(policies) and all(r['passed'] for r in results.values()))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    check = sub.add_parser('check')
    check.add_argument('file')
    ubsan = sub.add_parser('ubsan')
    ubsan.add_argument('--policy-dir', required=True)
    ubsan.add_argument('--out', required=True)
    for p in (check, ubsan):
        p.add_argument('--compiler', default=find_compiler() or 'g++')
        p.add_argument('--scratch-dir', default=None)
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory(prefix='silo-policy-', dir=args.scratch_dir) as scratch:
        if args.mode == 'check':
            g, c = check_policy_body(Path(args.file).read_text(), compiler=args.compiler, scratch_dir=scratch)
            result = dict(grammar=asdict(g), compile=asdict(c) if c else None)
            good = g.accepted and c is not None and c.accepted
        else:
            result = run_ubsan_harness(args.policy_dir, compiler=args.compiler, scratch_dir=scratch)
            Path(args.out).write_text(json.dumps(result, indent=2) + '\n')
            good = result['all_pass']
        print(json.dumps(result, indent=2))
        return 0 if good else 1


if __name__ == '__main__':
    raise SystemExit(main())
