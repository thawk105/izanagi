"""Acceptance and rejection boundaries for the Silo lock order profile."""
from pathlib import Path
from dataclasses import replace
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from skiputil import Skip
from orchestrator.campaign.silo_policy_grammar import (
    FUNCTION_POLICY_PROFILE, ORDER_POLICY_PROFILE, validate_policy,
)

HAND = ROOT / 'orchestrator/campaign/silo_lock_order_hand/version_desc.cpp'
FIXTURES = ROOT / 'orchestrator/tests/fixtures/silo_function_policy/contracts'

POSITIVE = '''struct OrderState { uint32_t streak = 0u; };
bool order_enabled(OrderState& s, const izanagi_silo_order_api::TxnContext& c) noexcept {
  return c.write_count >= 2u && s.streak < 8u;
}
uint64_t order_priority(OrderState&, const izanagi_silo_order_api::EntryContext& e) noexcept {
  if (e.locked) { return 18446744073709551615ul; }
  return (static_cast<uint64_t>(e.epoch) << 29u) | static_cast<uint64_t>(e.tid);
}
void order_after_abort(OrderState& s, const izanagi_silo_order_api::AbortContext&) noexcept { s.streak = 0u; }
void order_on_commit(OrderState& s, const izanagi_silo_order_api::CommitContext&) noexcept { s.streak = std::min(s.streak + 1u, 64u); }
'''


def _accepted(source, profile=ORDER_POLICY_PROFILE):
    return validate_policy(source, profile).accepted


def test_spec_positive_and_hand():
    assert _accepted(POSITIVE)
    assert _accepted(HAND.read_text())


def test_forbidden_names_in_each_declaration_position():
    for name in sorted(ORDER_POLICY_PROFILE.forbidden_identifiers):
        field = POSITIVE.replace('uint32_t streak', 'uint32_t ' + name + ' = 0u; uint32_t streak')
        local = POSITIVE.replace('return c.write_count >= 2u',
                                 'uint32_t ' + name + ' = 1u; return c.write_count >= 2u')
        helper = ('struct OrderState {};\nuint32_t ' + name + '() noexcept { return 1u; }\n' +
                  HAND.read_text().split('struct OrderState {};\n', 1)[1])
        parameter = HAND.read_text().replace('bool order_enabled(OrderState&,',
                                             'bool order_enabled(OrderState& ' + name + ',', 1)
        constant = POSITIVE.replace('struct OrderState', 'constexpr uint32_t ' + name + ' = 1u;\nstruct OrderState')
        for source in (field, local, helper, parameter, constant):
            assert not _accepted(source), (name, source)
        if name in {'result_', 'write_set_', 'TRACE'}:
            no_ban = replace(ORDER_POLICY_PROFILE, forbidden_identifiers=frozenset())
            for source in (field, local, helper, parameter, constant):
                assert _accepted(source, no_ban), (name, source)


def test_forbidden_names_in_reference_position():
    for name in sorted(ORDER_POLICY_PROFILE.forbidden_identifiers):
        source = POSITIVE.replace('return c.write_count >= 2u', 'return ' + name + ' >= 2u && c.write_count >= 2u')
        assert not _accepted(source), name


def test_policy_cpp_v1_rejections():
    variants = (
        POSITIVE.replace('uint32_t streak', 'uint32_t* streak'),
        POSITIVE.replace('uint32_t streak', 'uint32_t streak[2]'),
        POSITIVE.replace('return c.write_count', 'for (;;) {} return c.write_count'),
        '#define X 1\n' + POSITIVE,
        '// comment\n' + POSITIVE,
        POSITIVE.replace('return c.write_count', 'return "yes" && c.write_count'),
        POSITIVE.replace('streak', 'bad__name'),
        'using namespace std;\n' + POSITIVE,
        POSITIVE.replace('izanagi_silo_order_api', 'other_namespace'),
        'uint32_t operator+(uint32_t x) noexcept { return x; }\n' + POSITIVE,
        POSITIVE.replace('OrderState& s,', 'OrderState& s = OrderState{},'),
    )
    for source in variants:
        assert not _accepted(source), source


def test_existing_manifest_and_hand_policies_unchanged():
    rows = json.loads((FIXTURES / 'manifest.json').read_text())
    for row in rows:
        source = (FIXTURES / row['file']).read_text()
        decision = validate_policy(source)
        explicit = validate_policy(source, FUNCTION_POLICY_PROFILE)
        order = validate_policy(source, ORDER_POLICY_PROFILE)
        assert (decision.accepted, decision.rule_id) == (row['grammar']['accepted'], row['grammar']['rule_id'])
        assert (explicit.accepted, explicit.rule_id) == (decision.accepted, decision.rule_id)
        assert not order.accepted, row['file']
    hand = ROOT / 'orchestrator/campaign/silo_function_policy_hand'
    for path in hand.glob('*.cpp'):
        assert validate_policy(path.read_text()).accepted, path
        assert not validate_policy(path.read_text(), ORDER_POLICY_PROFILE).accepted, path
    assert not FUNCTION_POLICY_PROFILE.forbidden_identifiers
    old = (hand / 'static5.cpp').read_text()
    old = old.replace('struct PolicyState {', 'struct PolicyState { uint32_t result_ = 0u; ', 1)
    assert _accepted(old, FUNCTION_POLICY_PROFILE)
    assert not _accepted(POSITIVE.replace('streak', 'result_'), ORDER_POLICY_PROFILE)


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
