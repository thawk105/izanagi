"""Real compiler, isolation, diagnostics, timeout and UBSan contracts."""
from pathlib import Path
import json
import os
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from skiputil import Skip, skip
from orchestrator.campaign.silo_policy_compile import (
    check_policy_body, compile_policy, find_compiler, run_ubsan_harness,
)

FIXTURES = Path(__file__).with_name('fixtures') / 'silo_function_policy/contracts'
HAND = ROOT / 'orchestrator/campaign/silo_function_policy_hand'


def _compiler():
    compiler = find_compiler()
    if compiler is None:
        skip('C++ toolchain unavailable (g++-13/g++-12/g++)')
    return compiler


def _source(name):
    return (FIXTURES / (name + '.cpp')).read_text()


def test_manifest_compile_contracts():
    rows = json.loads((FIXTURES / 'manifest.json').read_text())
    files = [r['file'] for r in rows]
    assert len(files) == len(set(files))
    assert {p.name for p in FIXTURES.iterdir()} == set(files) | {'manifest.json'}
    compiler = _compiler()
    with tempfile.TemporaryDirectory() as tmp:
        for row in rows:
            d = compile_policy((FIXTURES / row['file']).read_text(), compiler=compiler, scratch_dir=tmp)
            assert not d.unavailable and not d.timed_out, (row['file'], d)
            assert d.accepted == row['compile_accepted'], (row['file'], d)
            assert d.accepted == (d.returncode == 0)
            assert len(d.diagnostic.encode('utf-8')) <= 16384
            assert not any(a.startswith(('-D', '-I')) for a in d.command[1:])
            assert d.compiler_version


def test_hand_policies_and_default_compile():
    compiler = _compiler()
    patch = (ROOT / 'patches/silo-function-policy-variant.patch').read_text()
    added = '\n'.join(line[1:] for line in patch.splitlines() if line.startswith('+') and not line.startswith('+++')) + '\n'
    default = added.split('// EVOLVE-BLOCK-BEGIN silo-function-policy\n#if SILO_POLICY_VARIANT\n', 1)[1].split('#else\n#endif\n// EVOLVE-BLOCK-END', 1)[0]
    paths = sorted(HAND.glob('*.cpp'))
    assert {'abort0', 'maxwait', 'static5', 'static10', 'retry', 'huge'} <= {p.stem for p in paths}
    with tempfile.TemporaryDirectory() as tmp:
        for name, source in [(p.name, p.read_text()) for p in paths] + [('default', default)]:
            g, c = check_policy_body(source, compiler=compiler, scratch_dir=tmp)
            assert g.accepted and c is not None and c.accepted, (name, g, c)


def _compile_reject(name):
    with tempfile.TemporaryDirectory() as tmp:
        d = compile_policy(_source(name), compiler=_compiler(), scratch_dir=tmp)
    assert not d.accepted and not d.unavailable and not d.timed_out and d.returncode != 0, d


def test_compile_rejects_external_global():
    _compile_reject('external_global')


def test_compile_rejects_unsupplied_macro():
    _compile_reject('external_macro')


def test_compile_unavailable_and_grammar_short_circuit():
    with tempfile.TemporaryDirectory() as tmp:
        missing = str(Path(tmp) / 'compiler-does-not-exist')
        d = compile_policy(_source('empty_state'), compiler=missing, scratch_dir=tmp)
        assert d.unavailable and not d.accepted and not d.timed_out and d.returncode is None
        g, c = check_policy_body(_source('bool_return'), compiler=missing, scratch_dir=tmp)
        assert not g.accepted and c is None


def test_compile_timeout_kills_process_group():
    # A real compiler launcher delays a real g++ invocation: no Popen stub.
    compiler = _compiler()
    with tempfile.TemporaryDirectory() as tmp:
        wrapper = Path(tmp) / 'delayed-compiler'
        pidfile = Path(tmp) / 'child.pid'
        wrapper.write_text('#!/bin/sh\nif [ "$1" = "--version" ]; then exec "' + compiler + '" "$@"; fi\n'
                           'sleep 60 &\necho $! > "' + str(pidfile) + '"\nwait\nexec "' + compiler + '" "$@"\n')
        wrapper.chmod(0o700)
        d = compile_policy(_source('empty_state'), compiler=str(wrapper), scratch_dir=tmp)
        assert d.timed_out and not d.accepted and not d.unavailable, d
        assert pidfile.exists()
        child_stat = Path('/proc') / pidfile.read_text().strip() / 'stat'
        if child_stat.exists():
            assert child_stat.read_text().split(') ', 1)[1].split()[0] == 'Z'


def test_compile_diagnostic_bound():
    source = '\n'.join('uint32_t bad' + str(i) + ' = absent' + str(i) + ';' for i in range(1000))
    with tempfile.TemporaryDirectory() as tmp:
        d = compile_policy(source, compiler=_compiler(), scratch_dir=tmp)
    assert not d.accepted and d.diagnostic_truncated and len(d.diagnostic.encode()) <= 16384, d


def test_compile_environment_isolation():
    compiler = _compiler()
    keys = ('CPATH', 'CPLUS_INCLUDE_PATH', 'C_INCLUDE_PATH', 'GCC_EXEC_PREFIX', 'COMPILER_PATH')
    old = {key: os.environ.get(key) for key in keys}
    try:
        for key in keys:
            os.environ[key] = '/nonexistent/silo-policy-contract'
        with tempfile.TemporaryDirectory() as tmp:
            d = compile_policy(_source('empty_state'), compiler=compiler, scratch_dir=tmp)
        assert d.accepted, d
    finally:
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_ubsan_harness_real_execution():
    with tempfile.TemporaryDirectory() as tmp:
        result = run_ubsan_harness(str(HAND), compiler=_compiler(), scratch_dir=tmp)
    expected = {p.stem for p in HAND.glob('*.cpp')} | {'ub_division_zero', 'ub_overshift', 'ub_signed_overflow'}
    assert set(result['policies']) == expected and result['all_pass'], result
    for name, row in result['policies'].items():
        assert row['passed'] and row['build_returncode'] == 0, (name, row)
        if row['negative']:
            assert row['ubsan'] and row['returncode'] != 0
        else:
            assert not row['ubsan'] and row['returncode'] == 0 and row['calls'] == 8 * 34 * 7


def _run():
    passed = failed = skipped = 0
    for name, fn in sorted(globals().items()):
        if name.startswith('test_') and callable(fn):
            try:
                fn()
                passed += 1
                print('PASS', name)
            except Skip as e:
                skipped += 1
                print('SKIP', name, e)
            except Exception as e:
                failed += 1
                print('FAIL', name, repr(e))
    print(f'{passed} passed, {failed} failed, {skipped} skipped')
    return int(failed != 0)


if __name__ == '__main__':
    sys.exit(_run())
