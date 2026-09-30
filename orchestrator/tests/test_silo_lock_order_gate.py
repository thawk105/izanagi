"""Real quarantine, grammar and compiler order before source writes."""
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from skiputil import Skip, skip
from orchestrator.campaign.axis_silo_lock_order import MARKER_ID, SOURCE_REL
from orchestrator.campaign.diff_quarantine import DiffRejectSubtype
from orchestrator.campaign.silo_lock_order_compile import check_order_body, find_compiler
from orchestrator.campaign.silo_lock_order_gate import order_gate

HAND = ROOT / 'orchestrator/campaign/silo_lock_order_hand/version_desc.cpp'


def _compiler():
    compiler = find_compiler()
    if compiler is None:
        skip('C++ toolchain unavailable; skip is not a green gate result')
    return compiler


def _source(root):
    source = root / SOURCE_REL
    source.parent.mkdir(parents=True)
    source.write_text('// EVOLVE-BLOCK-BEGIN ' + MARKER_ID + '\n'
                      '#if SILO_ORDER_VARIANT\n'
                      + HAND.read_text() +
                      '#else\n'
                      '/* stock */\n'
                      '#endif\n'
                      '// EVOLVE-BLOCK-END ' + MARKER_ID + '\n')
    return source


def test_gate_rejects_grammar_before_write():
    body = HAND.read_text().replace('return true;', 'return 1u;', 1)
    grammar, compiled = check_order_body(body, compiler=_compiler(), scratch_dir=tempfile.gettempdir())
    assert not grammar.accepted and compiled is None
    with tempfile.TemporaryDirectory() as tmp:
        source = _source(Path(tmp))
        before = source.read_bytes()
        result, _ = order_gate(tmp, body, None, compiler=_compiler(), scratch_dir=tmp,
                               write=True, origin='initial')
        assert not result.passed and result.subtype == DiffRejectSubtype.POLICY_GRAMMAR
        assert result.digest['template_diff_id'] == MARKER_ID
        assert source.read_bytes() == before


def test_gate_rejects_compile_before_write():
    body = HAND.read_text().replace('bool order_enabled(OrderState&', 'bool order_enabled(OrderState& unused', 1)
    grammar, compiled = check_order_body(body, compiler=_compiler(), scratch_dir=tempfile.gettempdir())
    assert grammar.accepted and compiled is not None and not compiled.accepted, (grammar, compiled)
    with tempfile.TemporaryDirectory() as tmp:
        source = _source(Path(tmp))
        before = source.read_bytes()
        result, _ = order_gate(tmp, body, None, compiler=_compiler(), scratch_dir=tmp,
                               write=True, origin='initial')
        assert not result.passed and result.subtype == DiffRejectSubtype.POLICY_COMPILE
        assert source.read_bytes() == before


def test_gate_writes_only_after_all_checks():
    body = HAND.read_text().replace('return true;', 'return false;', 1)
    with tempfile.TemporaryDirectory() as tmp:
        source = _source(Path(tmp))
        before = source.read_bytes()
        preview, _ = order_gate(tmp, body, None, compiler=_compiler(), scratch_dir=tmp,
                                write=False)
        assert preview.passed and source.read_bytes() == before
        result, _ = order_gate(tmp, body, None, compiler=_compiler(), scratch_dir=tmp,
                               write=True, origin='initial')
        assert result.passed and source.read_bytes() != before
        assert body.encode() in source.read_bytes()


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
