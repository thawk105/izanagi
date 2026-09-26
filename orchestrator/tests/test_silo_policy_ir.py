"""IR boundaries and finite semantics, checked by real grammar and C++."""
from dataclasses import replace
from pathlib import Path
import sys
import tempfile
from dataclasses import fields, is_dataclass

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from skiputil import skip
from orchestrator.campaign import silo_policy_ir as ir
from orchestrator.campaign.silo_policy_compile import (
    check_policy_body, find_compiler, _run, _translation_unit,
)

CASES = [(c.case_id, c.ir) for c in ir.enumerate_recon()] + [('abort0', ir.degenerate_policy())]
ZERO = ir.Const('u32', 0)
HAND = ROOT / 'orchestrator/campaign/silo_function_policy_hand'


def _tagged(value):
    if is_dataclass(value):
        return {'kind': type(value).__name__, **{
            field.name: _tagged(getattr(value, field.name)) for field in fields(value)}}
    if type(value) is tuple:
        return [_tagged(item) for item in value]
    return value


def test_parse_policy_ir_all_node_kinds_and_closed_types():
    zero = {'kind': 'Const', 'type': 'u32', 'value': 0}
    one = {'kind': 'Const', 'type': 'u32', 'value': 1}
    field = {'kind': 'StateField', 'type': 'u32', 'initial_literal': zero}
    ref = {'kind': 'StateRef', 'index': 0}
    expressions = [
        {'kind': 'Min', 'left': ref, 'right': one},
        {'kind': 'Max', 'left': ref, 'right': one},
        {'kind': 'SatAdd', 'left': ref, 'right': one},
        {'kind': 'SatSub', 'left': ref, 'right': one},
        {'kind': 'Shift', 'direction': '<<', 'value': ref, 'amount': 1},
        {'kind': 'Select', 'condition': {'kind': 'Compare', 'op': '==',
                                      'left': {'kind': 'Reason'},
                                      'right': {'kind': 'Const', 'type': 'reason', 'value': 'unset'}},
         'yes': ref, 'no': one},
    ]
    root = _tagged(ir.degenerate_policy())
    root['fields'] = [field]
    root['on_lock_conflict']['wait'] = {'kind': 'Attempt'}
    root['on_commit']['next_state'] = [ref]
    for expression in expressions:
        root['after_abort']['wait'] = expression
        parsed = ir.parse_policy_ir(root)
        assert ir.render_policy(parsed)
    for bad in (
        {'kind': 'Unknown'},
        dict(one, extra=1),
        {'kind': 'Const', 'type': 'u32'},
        {'kind': 'Const', 'type': 'u32', 'value': True},
        {'kind': 'Const', 'type': 'u32', 'value': 2**32},
        {'kind': 'StateRef', 'index': True},
        {'kind': 'StateRef', 'index': 2},
        {'kind': 'Shift', 'direction': '<<', 'value': ref, 'amount': True},
        {'kind': 'Shift', 'direction': '<<', 'value': ref, 'amount': 32},
    ):
        invalid = _tagged(ir.degenerate_policy())
        invalid['fields'] = [field]
        invalid['after_abort']['wait'] = bad
        with pytest.raises(ValueError):
            ir.parse_policy_ir(invalid)
    missing = _tagged(ir.degenerate_policy())
    del missing['after_abort']['next_state']
    with pytest.raises(ValueError):
        ir.parse_policy_ir(missing)


def _compiler():
    compiler = find_compiler()
    if compiler is None:
        skip('C++ toolchain unavailable (g++-13/g++-12/g++)')
    return compiler


def _policy(wait=ZERO, fields=(), updates=None):
    return replace(ir.degenerate_policy(), fields=fields, after_abort=ir.AbortHook(wait, updates))


def _accepted(policy):
    body = ir.render_policy(policy)
    with tempfile.TemporaryDirectory() as tmp:
        g, c = check_policy_body(body, compiler=_compiler(), scratch_dir=tmp)
    assert g.accepted and c is not None and c.accepted, (g, c)


@pytest.mark.parametrize('case_id,policy', CASES, ids=[c[0] for c in CASES])
def test_all_cases_grammar_compile_unused_arguments(case_id, policy):
    # Real -Wall -Wextra -Werror also checks unused arguments.
    _accepted(policy)


def test_deterministic_render_and_seed_bytes():
    again = [(c.case_id, c.ir) for c in ir.enumerate_recon()] + [('abort0', ir.degenerate_policy())]
    assert [name for name, _ in CASES[:-1]] == [f'{i:04b}' for i in range(16)]
    for (name, policy), (other, rebuilt) in zip(CASES, again):
        assert name == other
        assert ir.render_policy(policy).encode() == ir.render_policy(rebuilt).encode()
    for case_id, hand in [('0000', 'static5'), ('0001', 'static10'), ('abort0', 'abort0')]:
        # Literal-only policies need no locals, so exact legacy bytes are appropriate.
        assert ir.render_policy(dict(CASES)[case_id]).encode() == (HAND / f'{hand}.cpp').read_bytes()


def test_depth_boundary():
    expr = ZERO
    for _ in range(3):
        expr = ir.Max(expr, ZERO)
    _accepted(_policy(expr))
    with pytest.raises(ValueError, match='depth'):
        ir.render_policy(_policy(ir.Max(expr, ZERO)))


def test_node_occurrence_boundary():
    # Shared objects count once per occurrence, not once per identity.
    b = ir.Const('bool', True)
    n4 = ir.Select(b, ZERO, ZERO)
    n10 = ir.Select(b, n4, n4)
    n22 = ir.Select(b, n10, n10)
    n21 = ir.Max(n10, n10)
    fields = (ir.StateField('u32', ZERO),) * 4
    # 21 + (22+10+4+1) + 2 lock outputs + 4 commit updates = 64.
    policy = replace(_policy(n21, fields, (n22, n10, n4, ZERO)),
                     on_commit=ir.CommitHook((ZERO,) * 4))
    _accepted(policy)
    with pytest.raises(ValueError, match='node'):
        ir.render_policy(replace(policy, after_abort=ir.AbortHook(n22, policy.after_abort.next_state)))


def test_field_boundary():
    fields = (ir.StateField('u32', ZERO),) * 4
    _accepted(_policy(fields=fields))
    with pytest.raises(ValueError, match='field limit'):
        ir.render_policy(_policy(fields=fields + fields[:1]))


@pytest.mark.parametrize('ty,width', [('u32', 32), ('u64', 64)])
@pytest.mark.parametrize('direction', ['<<', '>>'])
def test_shift_boundary(ty, width, direction):
    field = ir.StateField(ty, ir.Const(ty, 1))
    def policy(amount):
        return _policy(fields=(field,), updates=(ir.Shift(direction, ir.StateRef(0), amount),))
    _accepted(policy(width - 1))
    for amount in (width, -1, True, ZERO):
        with pytest.raises(ValueError, match='shift'):
            ir.render_policy(policy(amount))


@pytest.mark.parametrize('bad', [
    ir.Const('u32', -1), ir.Const('u32', 2**32), ir.Const('u64', 2**64),
    ir.Const('u32', True), ir.Const('bool', 1), ir.Const('reason', 'absent'),
    ir.Const('action', 'absent'), ir.Const('bad', 0),
    ir.Min(ZERO, ir.Const('u64', 0)), ir.Max(ir.Const('bool', True), ir.Const('bool', False)),
    ir.SatAdd(ZERO, ir.Const('u64', 0)), ir.SatSub(ZERO, ir.Const('bool', False)),
    ir.Compare('<', ir.Const('action', 'retry'), ir.Const('action', 'abort')),
    ir.Compare('||', ZERO, ZERO), ir.Select(ZERO, ZERO, ZERO),
    ir.Select(ir.Const('bool', True), ZERO, ir.Const('u64', 0)), ir.StateRef(0),
    ir.StateRef(True), ir.Attempt(), ir.Const('bool', True),
])
def test_reject_types_literals_and_abort_inputs(bad):
    with pytest.raises(ValueError):
        ir.render_policy(_policy(bad))


def test_hook_inputs_and_state_types():
    _accepted(replace(ir.degenerate_policy(), on_lock_conflict=ir.LockHook(ir.Const('action', 'retry'), ir.Attempt())))
    reason_wait = ir.Select(ir.Compare('==', ir.Reason(), ir.Const('reason', 'unset')), ZERO, ZERO)
    _accepted(_policy(reason_wait))
    with pytest.raises(ValueError, match='Reason'):
        ir.render_policy(replace(ir.degenerate_policy(), on_lock_conflict=ir.LockHook(ir.Const('action', 'abort'), reason_wait)))
    fields = (ir.StateField('u32', ZERO),)
    for expr in (ir.Attempt(), reason_wait):
        with pytest.raises(ValueError):
            ir.render_policy(replace(_policy(fields=fields), on_commit=ir.CommitHook((expr,))))
    for policy in (
        _policy(fields=fields, updates=()),
        _policy(fields=fields, updates=(ir.Const('u64', 0),)),
        _policy(fields=(ir.StateField('u64', ZERO),)),
    ):
        with pytest.raises(ValueError):
            ir.render_policy(policy)


def _execute(policy, checks):
    body = ir.render_policy(policy)
    compiler = _compiler()
    with tempfile.TemporaryDirectory() as tmp:
        grammar, compiled = check_policy_body(body, compiler=compiler, scratch_dir=tmp)
        assert grammar.accepted and compiled and compiled.accepted, (grammar, compiled)
        source = Path(tmp) / 'meaning.cpp'
        exe = Path(tmp) / 'meaning'
        source.write_text(_translation_unit(body) + '''
#include <cassert>
#include <initializer_list>
int main() {
  using namespace izanagi_silo_api;
  using namespace izanagi_silo_policy;
  PolicyState s{};
''' + checks + '\n}\n')
        built = _run([compiler, '-std=c++17', '-Wall', '-Wextra', '-Werror', str(source), '-o', str(exe)], tmp, 10)
        assert built[0] == 0 and not built[1] and not built[2], built
        ran = _run([str(exe)], tmp, 3)
        assert ran[0] == 0 and not ran[1] and not ran[2], ran


@pytest.mark.parametrize('ty,width', [('u32', 32), ('u64', 64)])
def test_saturation_execution(ty, width):
    maximum = (1 << width) - 1
    fields = (ir.StateField(ty, ir.Const(ty, 0)),) * 2
    policy = _policy(fields=fields, updates=(ir.SatAdd(ir.StateRef(0), ir.Const(ty, 5)), ir.SatSub(ir.StateRef(1), ir.Const(ty, 5))))
    suffix = 'u' if ty == 'u32' else 'ul'
    _execute(policy, f'''
  s.f0 = {maximum - 6}{suffix}; s.f1 = 6{suffix};
  policy_after_abort(s, AbortContext{{AbortReason::unset, 0ul}});
  assert(s.f0 == {maximum - 1}{suffix} && s.f1 == 1{suffix});
  policy_after_abort(s, AbortContext{{AbortReason::unset, 0ul}});
  assert(s.f0 == {maximum}{suffix} && s.f1 == 0{suffix});
  policy_after_abort(s, AbortContext{{AbortReason::unset, 0ul}});
  assert(s.f0 == {maximum}{suffix} && s.f1 == 0{suffix});
  s.f0 = {maximum - 5}{suffix}; s.f1 = 5{suffix};
  policy_after_abort(s, AbortContext{{AbortReason::unset, 0ul}});
  assert(s.f0 == {maximum}{suffix} && s.f1 == 0{suffix});
''')


def test_snapshot_swap_execution():
    fields = (ir.StateField('u32', ir.Const('u32', 7)), ir.StateField('u32', ir.Const('u32', 11)))
    _execute(_policy(ir.StateRef(0), fields, (ir.StateRef(1), ir.StateRef(0))), '''
  assert(policy_after_abort(s, AbortContext{AbortReason::unset, 0ul}) == 7u);
  assert(s.f0 == 11u && s.f1 == 7u);
''')


def test_snapshot_output_before_reset_execution():
    fields = (ir.StateField('u32', ir.Const('u32', 7)),)
    _execute(_policy(ir.StateRef(0), fields, (ZERO,)), '''
  assert(policy_after_abort(s, AbortContext{AbortReason::unset, 0ul}) == 7u);
  assert(s.f0 == 0u);
''')


@pytest.mark.parametrize('case', ir.enumerate_recon(), ids=lambda c: c.case_id)
def test_recon_semantics_execution(case):
    l, s, r, m = case.factors
    base = 10 if m else 5
    state_checks = 'assert(s.f0 == expected);' if s else ''
    reset_check = 'assert(s.f0 == 0u);' if s else ''
    _execute(case.ir, f'''
  uint32_t expected = 0u;
  for (uint32_t i = 0; i < 205; ++i) {{
    expected = {f'std::min(1000u, expected + {base}u)' if s else f'{base}u'};
    auto reason = i % 2u ? AbortReason::lock_conflict : AbortReason::read_tid;
    uint32_t wait = policy_after_abort(s, AbortContext{{reason, 0ul}});
    assert(wait == ({'reason == AbortReason::lock_conflict ? expected : 0u' if r else 'expected'}));
    {state_checks}
  }}
  policy_on_commit(s, CommitContext{{}});
  {reset_check}
  assert(policy_after_abort(s, AbortContext{{AbortReason::lock_conflict, 0ul}}) == {base}u);
  for (uint32_t attempt : {{3u, 4u, 31u, 32u}}) {{
    auto response = policy_on_lock_conflict(s, LockContext{{attempt, 0ul}});
    assert(response.wait_us == 0u);
    assert(response.action == ({'attempt < 4u ? PolicyAction::retry : PolicyAction::abort' if l else 'PolicyAction::abort'}));
  }}
''')


def test_other_operators_and_lock_commit_updates_execution():
    fields = (ir.StateField('u64', ir.Const('u64', 1)), ir.StateField('bool', ir.Const('bool', False)))
    policy = replace(_policy(fields=fields),
        on_lock_conflict=ir.LockHook(ir.Select(ir.Compare('!=', ir.StateRef(1), ir.Const('bool', True)), ir.Const('action', 'retry'), ir.Const('action', 'abort')), ZERO,
                                    (ir.Shift('<<', ir.StateRef(0), 63), ir.Const('bool', True))),
        on_commit=ir.CommitHook((ir.Max(ir.Shift('>>', ir.StateRef(0), 63), ir.Const('u64', 2)), ir.Const('bool', False))))
    _execute(policy, '''
  assert(policy_on_lock_conflict(s, LockContext{0u, 0ul}).action == PolicyAction::retry);
  assert(s.f0 == 9223372036854775808ul && s.f1);
  policy_on_commit(s, CommitContext{});
  assert(s.f0 == 2ul && !s.f1);
''')


def test_job_factor_balance():
    seen = []
    for job in range(8):
        cases = [c for c in ir.enumerate_recon() if ir.job_of(c.case_id) == job]
        assert len(cases) == 2
        seen.extend(c.case_id for c in cases)
        for factor in range(4):
            assert sum(c.factors[factor] for c in cases) == 1
    assert sorted(seen) == [c.case_id for c in ir.enumerate_recon()]
    for invalid in ('abort0', '000', '00000', '0002', ''):
        with pytest.raises(ValueError):
            ir.job_of(invalid)


if __name__ == '__main__':
    from tools.run_tests import main as _run
    raise SystemExit(_run([__file__, *sys.argv[1:]]))
