"""Contract fixtures exercise the real lexer, parser and preceding gates."""
from pathlib import Path
import difflib
import json
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from skiputil import Skip
from orchestrator.campaign.silo_policy_grammar import validate_policy
from orchestrator.campaign.coder_effect_gate import scan_host_effects
from orchestrator.campaign.diff_quarantine import DiffQuarantine, parse_template_file

FIXTURES = Path(__file__).with_name('fixtures') / 'silo_function_policy/contracts'
HAND = ROOT / 'orchestrator/campaign/silo_function_policy_hand'


def _manifest():
    rows = json.loads((FIXTURES / 'manifest.json').read_text())
    files = [r['file'] for r in rows]
    assert len(files) == len(set(files))
    assert {p.name for p in FIXTURES.iterdir()} == set(files) | {'manifest.json'}
    return rows


def _source(name):
    return (FIXTURES / (name + '.cpp')).read_text()


def _reject(name, rule):
    source = _source(name)
    d = validate_policy(source)
    assert not d.accepted and d.stage == 'grammar' and d.rule_id == rule, (name, d)
    assert d.offset is not None and 0 <= d.offset <= len(source)
    assert d.line == source.count('\n', 0, d.offset) + 1
    assert d.column == d.offset - source.rfind('\n', 0, d.offset)
    assert d.reason and len(d.reason) <= 256


def _default_body():
    patch = (ROOT / 'patches/silo-function-policy-variant.patch').read_text()
    added = '\n'.join(line[1:] for line in patch.splitlines() if line.startswith('+') and not line.startswith('+++')) + '\n'
    return added.split('// EVOLVE-BLOCK-BEGIN silo-function-policy\n#if SILO_POLICY_VARIANT\n', 1)[1].split('#else\n#endif\n// EVOLVE-BLOCK-END', 1)[0]


def test_manifest_grammar_contracts():
    for row in _manifest():
        d = validate_policy((FIXTURES / row['file']).read_text())
        assert (d.accepted, d.rule_id) == (row['grammar']['accepted'], row['grammar']['rule_id']), (row['file'], d)


def test_manifest_first_rejection_stage():
    before = ('// EVOLVE-BLOCK-BEGIN silo-function-policy\n#if SILO_POLICY_VARIANT\n' +
              _default_body() + '#else\n#endif\n// EVOLVE-BLOCK-END silo-function-policy\n')
    with tempfile.TemporaryDirectory() as tmp:
        template = Path(tmp) / 'transaction.cc'
        template.write_text(before)
        marker = parse_template_file(str(template), 'silo-function-policy')
        assert marker is not None
        for row in _manifest():
            source = (FIXTURES / row['file']).read_text()
            after = before.replace(_default_body(), source)
            diff = ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='a/transaction.cc', tofile='b/transaction.cc'))
            quarantine = DiffQuarantine(marker, diff, head_text=before).validate()
            if not quarantine.passed:
                stage = 'diff-quarantine'
                assert 'branch=content-directive' in quarantine.digest['evidence'], quarantine.digest
                rule = 'content-directive'
            else:
                effects = scan_host_effects(source)
                if effects:
                    stage, rule = 'effect', effects[0].rule_id
                else:
                    grammar = validate_policy(source)
                    stage, rule = (None, None) if grammar.accepted else ('grammar', grammar.rule_id)
            assert dict(stage=stage, rule_id=rule) == row['first_rejection'], (row['file'], stage, rule)


def test_hand_policies_and_default_grammar():
    paths = sorted(HAND.glob('*.cpp'))
    assert {'abort0', 'maxwait', 'static5', 'static10', 'retry', 'huge'} <= {p.stem for p in paths}
    for name, source in [(p.name, p.read_text()) for p in paths] + [('default', _default_body())]:
        assert validate_policy(source).accepted, name


def test_grammar_rejects_alternative_binary_tokens():
    for name in ('alternative_bitand', 'alternative_and'):
        _reject(name, 'lex.alternative-token')


def test_grammar_rejects_bool_arithmetic():
    _reject('bool_arithmetic', 'type.numeric')


def test_grammar_rejects_self_initialization():
    for name in ('self_init', 'self_nested', 'self_helper'):
        _reject(name, 'init.self')
    assert validate_policy(_source('initialized_update')).accepted


def test_grammar_requires_final_return():
    for name in ('final_if', 'final_block'):
        _reject(name, 'return.final')


def test_grammar_rejects_subexpression_assignment():
    _reject('subexpression_assignment', 'assignment.statement')


def test_grammar_requires_literal_divisor():
    for name in ('variable_divisor', 'variable_modulo'):
        _reject(name, 'rhs.literal')


def test_grammar_limits_are_candidate_rejections():
    assert validate_policy(' ' * (256 * 1024 + 1)).rule_id == 'limit.source'
    assert validate_policy('x ' * 4097).rule_id == 'limit.tokens'
    body = _source('empty_state').replace('return 0u;', 'return ' + '(' * 100 + '0u' + ')' * 100 + ';', 1)
    assert validate_policy(body).rule_id == 'limit.depth'
    body = _source('empty_state').replace('return 0u;', 'if (true) ' * 100 + 'return 0u;', 1)
    assert validate_policy(body).rule_id == 'limit.depth'


def test_grammar_internal_errors_propagate():
    try:
        validate_policy(None)
    except AttributeError:
        pass
    else:
        raise AssertionError('internal exception was converted into candidate verdict')


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
