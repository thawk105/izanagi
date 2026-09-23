"""Finite typed policy trees and the fixed LSRM reconnaissance space.

State updates are simultaneous; omitted next_state retains all fields.
Rendering is a subset of policy-C++ v1, not an alternative admission gate.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Literal

from .axis_silo_function_policy import REASON_NAMES
from .silo_policy_compile import check_policy_body, find_compiler, run_ubsan_harness

ScalarType = Literal['u32', 'u64', 'bool']
ExprType = Literal['u32', 'u64', 'bool', 'reason', 'action']


@dataclass(frozen=True)
class Const:
    type: ExprType
    value: int | bool | str


@dataclass(frozen=True)
class Reason:
    pass


@dataclass(frozen=True)
class Attempt:
    pass


@dataclass(frozen=True)
class StateRef:
    index: int


@dataclass(frozen=True)
class Compare:
    op: str
    left: Expr
    right: Expr


@dataclass(frozen=True)
class Select:
    condition: Expr
    yes: Expr
    no: Expr


@dataclass(frozen=True)
class Min:
    left: Expr
    right: Expr


@dataclass(frozen=True)
class Max:
    left: Expr
    right: Expr


@dataclass(frozen=True)
class SatAdd:
    left: Expr
    right: Expr


@dataclass(frozen=True)
class SatSub:
    left: Expr
    right: Expr


@dataclass(frozen=True)
class Shift:
    direction: Literal['<<', '>>']
    value: Expr
    amount: int


Expr = Const | Reason | Attempt | StateRef | Compare | Select | Min | Max | SatAdd | SatSub | Shift


@dataclass(frozen=True)
class StateField:
    type: ScalarType
    initial_literal: Const


@dataclass(frozen=True)
class AbortHook:
    wait: Expr
    next_state: tuple[Expr, ...] | None = None


@dataclass(frozen=True)
class LockHook:
    action: Expr
    wait: Expr
    next_state: tuple[Expr, ...] | None = None


@dataclass(frozen=True)
class CommitHook:
    next_state: tuple[Expr, ...] | None = None


@dataclass(frozen=True)
class PolicyIR:
    fields: tuple[StateField, ...]
    after_abort: AbortHook
    on_lock_conflict: LockHook
    on_commit: CommitHook


@dataclass(frozen=True)
class ReconCase:
    case_id: str
    factors: tuple[int, int, int, int]  # L, S, R, M
    ir: PolicyIR


_NUMERIC = {'u32', 'u64'}
_CPP = dict(u32='uint32_t', u64='uint64_t', bool='bool',
            reason='izanagi_silo_api::AbortReason', action='izanagi_silo_api::PolicyAction')


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _literal(expr):
    _require(type(expr) is Const and expr.type in _CPP, 'invalid literal type')
    if expr.type in _NUMERIC:
        width = 32 if expr.type == 'u32' else 64
        _require(type(expr.value) is int and 0 <= expr.value < 1 << width, 'literal range')
    elif expr.type == 'bool':
        _require(type(expr.value) is bool, 'bool literal required')
    else:
        values = REASON_NAMES if expr.type == 'reason' else ('retry', 'abort')
        _require(type(expr.value) is str and expr.value in values, 'invalid enumerator')
    return expr.type


def _children(expr):
    if isinstance(expr, Select):
        return (expr.condition, expr.yes, expr.no)
    if isinstance(expr, Shift):
        return (expr.value,)
    if isinstance(expr, (Compare, Min, Max, SatAdd, SatSub)):
        return (expr.left, expr.right)
    return ()


def _outputs(hook):
    if isinstance(hook, AbortHook):
        return (hook.wait,)
    if isinstance(hook, LockHook):
        return (hook.action, hook.wait)
    return ()


def validate_ir(ir: PolicyIR) -> None:
    """Raise ValueError on type, input, literal or structural violations."""
    _require(type(ir) is PolicyIR, 'PolicyIR required')
    _require(type(ir.fields) is tuple and len(ir.fields) <= 4, 'field limit (4) or tuple')
    for field in ir.fields:
        _require(type(field) is StateField and field.type in _NUMERIC | {'bool'}, 'state field type')
        _require(_literal(field.initial_literal) == field.type, 'state initializer type')
    nodes = 0

    def visit(expr, hook, depth=1):
        nonlocal nodes
        _require(depth <= 4, 'depth limit (4)')
        nodes += 1
        _require(nodes <= 64, 'node limit (64)')
        if type(expr) is Const:
            return _literal(expr)
        if type(expr) is Reason:
            _require(hook == 'abort', 'Reason requires abort hook')
            return 'reason'
        if type(expr) is Attempt:
            _require(hook == 'lock', 'Attempt requires lock hook')
            return 'u32'
        if type(expr) is StateRef:
            _require(type(expr.index) is int and 0 <= expr.index < len(ir.fields), 'state index')
            return ir.fields[expr.index].type
        _require(type(expr) in (Compare, Select, Min, Max, SatAdd, SatSub, Shift), 'unknown expression')
        types = tuple(visit(child, hook, depth + 1) for child in _children(expr))
        if type(expr) is Select:
            _require(types[0] == 'bool' and types[1] == types[2], 'select types')
            return types[1]
        if type(expr) is Shift:
            _require(types[0] in _NUMERIC, 'shift type')
            _require(expr.direction in ('<<', '>>') and type(expr.amount) is int
                     and 0 <= expr.amount < (32 if types[0] == 'u32' else 64), 'shift amount/direction')
            return types[0]
        _require(types[0] == types[1], 'binary operands must have same type')
        if type(expr) is Compare:
            _require(expr.op in ('==', '!=', '<', '<=', '>', '>='), 'comparison operator')
            _require(expr.op in ('==', '!=') or types[0] in _NUMERIC, 'comparison type')
            return 'bool'
        _require(types[0] in _NUMERIC, 'numeric operands required')
        return types[0]

    for name, hook, cls, expected in (
        ('abort', ir.after_abort, AbortHook, ('u32',)),
        ('lock', ir.on_lock_conflict, LockHook, ('action', 'u32')),
        ('commit', ir.on_commit, CommitHook, ()),
    ):
        _require(type(hook) is cls, 'hook type')
        for expr, ty in zip(_outputs(hook), expected):
            _require(visit(expr, name) == ty, 'hook output type')
        if hook.next_state is not None:
            _require(type(hook.next_state) is tuple and len(hook.next_state) == len(ir.fields), 'next_state arity')
            for expr, field in zip(hook.next_state, ir.fields):
                _require(visit(expr, name) == field.type, 'next_state type')


def _render_literal(expr):
    if expr.type in _NUMERIC:
        return str(expr.value) + ('u' if expr.type == 'u32' else 'ul')
    if expr.type == 'bool':
        return 'true' if expr.value else 'false'
    return _CPP[expr.type] + '::' + expr.value


def render_policy(ir: PolicyIR) -> str:
    validate_ir(ir)
    fields = ' '.join(f'{_CPP[f.type]} f{i} = {_render_literal(f.initial_literal)};'
                      for i, f in enumerate(ir.fields))
    lines = ['struct PolicyState { ' + (fields + ' ' if fields else '') + '};']
    for hook, name, context, result in (
        (ir.after_abort, 'policy_after_abort', 'AbortContext', 'uint32_t'),
        (ir.on_lock_conflict, 'policy_on_lock_conflict', 'LockContext', 'izanagi_silo_api::LockResponse'),
        (ir.on_commit, 'policy_on_commit', 'CommitContext', 'void'),
    ):
        roots = _outputs(hook) + (hook.next_state or ())
        refs = set()
        uses_context = False

        def scan(expr):
            nonlocal uses_context
            if isinstance(expr, StateRef):
                refs.add(expr.index)
            if isinstance(expr, (Reason, Attempt)):
                uses_context = True
            for child in _children(expr):
                scan(child)

        for expr in roots:
            scan(expr)
        state_arg = ' s' if refs or hook.next_state else ''
        ctx_arg = ' c' if uses_context else ''
        lines.append(f'{result} {name}(PolicyState&{state_arg}, const izanagi_silo_api::{context}&{ctx_arg}) noexcept {{')
        for i in sorted(refs):
            lines.append(f'  {_CPP[ir.fields[i].type]} v{i} = s.f{i};')
        count = 0

        def local(ty, value):
            nonlocal count
            var = f't{count}'
            count += 1
            lines.append(f'  {_CPP[ty]} {var} = {value};')
            return var, ty

        def emit(expr):
            if isinstance(expr, Const):
                return _render_literal(expr), expr.type
            if isinstance(expr, StateRef):
                return f'v{expr.index}', ir.fields[expr.index].type
            if isinstance(expr, Reason):
                return 'c.reason', 'reason'
            if isinstance(expr, Attempt):
                return 'c.attempt', 'u32'
            args = [emit(child) for child in _children(expr)]
            a, ty = args[0]
            if isinstance(expr, Shift):
                return local(ty, f'{a} {expr.direction} {expr.amount}u')
            b = args[1][0]
            if isinstance(expr, Compare):
                return local('bool', f'{a} {expr.op} {b}')
            if isinstance(expr, Select):
                return local(args[1][1], f'{a} ? {b} : {args[2][0]}')
            if isinstance(expr, (Min, Max)):
                return local(ty, f'std::{"min" if isinstance(expr, Min) else "max"}({a}, {b})')
            # Even leaf children are materialized before the saturating operation.
            a, _ = local(ty, a)
            b, _ = local(ty, b)
            if isinstance(expr, SatAdd):
                maximum = _render_literal(Const(ty, (1 << (32 if ty == 'u32' else 64)) - 1))
                return local(ty, f'{a} > {maximum} - {b} ? {maximum} : {a} + {b}')
            zero = _render_literal(Const(ty, 0))
            return local(ty, f'{a} < {b} ? {zero} : {a} - {b}')

        outputs = [emit(expr)[0] for expr in _outputs(hook)]
        updates = [emit(expr)[0] for expr in (hook.next_state or ())]
        for i, value in enumerate(updates):
            lines.append(f'  s.f{i} = {value};')
        if isinstance(hook, AbortHook):
            lines.append(f'  return {outputs[0]};')
        elif isinstance(hook, LockHook):
            lines.append(f'  return izanagi_silo_api::LockResponse{{{outputs[0]}, {outputs[1]}}};')
        lines.append('}')
    return '\n'.join(lines) + '\n'


def degenerate_policy() -> PolicyIR:
    return PolicyIR((), AbortHook(Const('u32', 0)),
                    LockHook(Const('action', 'abort'), Const('u32', 0)), CommitHook())


def enumerate_recon() -> tuple[ReconCase, ...]:
    """ID-sorted fixed template space; factors are in LSRM order."""
    cases = []
    for number in range(16):
        case_id = f'{number:04b}'
        l, s, r, m = factors = tuple(map(int, case_id))
        zero = Const('u32', 0)
        base = Const('u32', 10 if m else 5)
        x = Min(Const('u32', 1000), SatAdd(StateRef(0), base)) if s else base
        wait = Select(Compare('==', Reason(), Const('reason', 'lock_conflict')), x, zero) if r else x
        action = Const('action', 'abort')
        if l:
            action = Select(Compare('<', Attempt(), Const('u32', 4)), Const('action', 'retry'), action)
        ir = PolicyIR((StateField('u32', zero),) if s else (),
                      AbortHook(wait, (x,) if s else None), LockHook(action, zero),
                      CommitHook((zero,) if s else None))
        cases.append(ReconCase(case_id, factors, ir))
    return tuple(cases)


def job_of(case_id: str) -> int:
    _require(isinstance(case_id, str) and len(case_id) == 4 and set(case_id) <= {'0', '1'}, 'expected LSRM case ID')
    number = int(case_id, 2)
    return min(number, number ^ 15)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    check = sub.add_parser('check')
    check.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    compiler = find_compiler() or 'g++'
    policies = [(case.case_id, case.ir) for case in enumerate_recon()] + [('abort0', degenerate_policy())]
    rows = {}
    with tempfile.TemporaryDirectory(prefix='silo-ir-') as scratch:
        policy_dir = Path(scratch) / 'policies'
        policy_dir.mkdir()
        for case_id, ir in policies:
            body = render_policy(ir)
            (policy_dir / f'{case_id}.cpp').write_text(body, encoding='utf-8')
            grammar, compiled = check_policy_body(body, compiler=compiler, scratch_dir=scratch)
            rows[case_id] = dict(body_sha256=hashlib.sha256(body.encode()).hexdigest(), ir=repr(ir),
                                 grammar=asdict(grammar), compile=asdict(compiled) if compiled else None)
        ubsan = run_ubsan_harness(str(policy_dir), compiler=compiler, scratch_dir=scratch)
    good = all(row['grammar']['accepted'] and row['compile'] and row['compile']['accepted'] for row in rows.values()) and ubsan['all_pass']
    result = dict(compiler=compiler, compiler_version=ubsan['compiler_version'], policies=rows,
                  ubsan=ubsan, all_pass=bool(good))
    Path(args.out).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(all_pass=bool(good), policies=len(rows), compiler_version=ubsan['compiler_version'])))
    return 0 if good else 1


if __name__ == '__main__':
    raise SystemExit(main())
