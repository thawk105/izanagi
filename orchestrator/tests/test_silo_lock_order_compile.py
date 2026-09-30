"""Real isolated compiler and UBSan coverage for the hand order policy."""
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from skiputil import Skip, skip
from orchestrator.campaign.silo_lock_order_compile import (
    check_order_body, compile_order, find_compiler, run_ubsan_harness,
)
from test_silo_lock_order_grammar import POSITIVE

HAND = ROOT / 'orchestrator/campaign/silo_lock_order_hand'


def _compiler():
    compiler = find_compiler()
    if compiler is None:
        skip('C++ toolchain unavailable; skip is not a green compiler result')
    return compiler


def test_compile_positive_and_hand():
    with tempfile.TemporaryDirectory() as tmp:
        for source in (POSITIVE, (HAND / 'version_desc.cpp').read_text()):
            grammar, compiled = check_order_body(source, compiler=_compiler(), scratch_dir=tmp)
            assert grammar.accepted and compiled is not None and compiled.accepted, (grammar, compiled)


def test_compile_rejects_unresolved_external():
    source = POSITIVE.replace('return c.write_count >= 2u', 'return external_value >= 2u && c.write_count >= 2u')
    with tempfile.TemporaryDirectory() as tmp:
        decision = compile_order(source, compiler=_compiler(), scratch_dir=tmp)
    assert not decision.accepted and not decision.unavailable and not decision.timed_out


def test_ubsan_hand_policy():
    with tempfile.TemporaryDirectory() as tmp:
        result = run_ubsan_harness(str(HAND), compiler=_compiler(), scratch_dir=tmp)
    assert result['all_pass'] and 'version_desc' in result['policies'], result
    row = result['policies']['version_desc']
    assert row['passed'] and not row['ubsan'] and row['calls'] == 8 + 4 * 2 * 12


def _run():
    passed = failed = skipped = 0
    for name, fn in sorted(globals().items()):
        if name.startswith('test_') and callable(fn):
            try:
                fn(); passed += 1; print('PASS', name)
            except Skip as e:
                skipped += 1; print('SKIP', name, e)
            except Exception as e:
                failed += 1; print('FAIL', name, repr(e))
    print(f'{passed} passed, {failed} failed, {skipped} skipped')
    return int(failed != 0)


if __name__ == '__main__':
    sys.exit(_run())
