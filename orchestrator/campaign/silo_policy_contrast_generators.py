"""Deterministic typed generators for the silo policy contrast.

Each counter has an independent SHA-256 preimage. Draw number n uses
SHA-256(preimage + '|draw|' + str(n)); rejection sampling removes modulo bias.
No mutable random state or performance observation enters random_ir.
"""
from __future__ import annotations

from dataclasses import fields, is_dataclass, replace
import hashlib
from typing import Sequence

from .axis_silo_function_policy import REASON_NAMES
from .b5_generator_contrast import weights_table
from .silo_policy_ir import (AbortHook, Attempt, CommitHook, Compare, Const,
    LockHook, Max, Min, PolicyIR, Reason, SatAdd, SatSub, Select, Shift,
    StateField, StateRef, parse_policy_ir, render_policy, validate_ir)


def tagged(value):
    if is_dataclass(value):
        return {'kind': type(value).__name__, **{f.name: tagged(getattr(value, f.name)) for f in fields(value)}}
    if isinstance(value, tuple):
        return [tagged(x) for x in value]
    return value


class _Draw:
    def __init__(self, preimage):
        self.preimage, self.n = preimage, 0

    def below(self, limit):
        if limit <= 0:
            raise ValueError('empty draw range')
        bound = (1 << 256) - ((1 << 256) % limit)
        while True:
            digest = hashlib.sha256(f'{self.preimage}|draw|{self.n}'.encode()).digest()
            self.n += 1
            value = int.from_bytes(digest, 'big')
            if value < bound:
                return value % limit

    def choose(self, values):
        return values[self.below(len(values))]


def _constant(ty, draw, weights):
    if ty in ('u32', 'u64'):
        if draw.below(8) == 0:
            return Const(ty, 0)
        ticket = draw.below(sum(weights))
        for number, weight in enumerate(weights, 1):
            ticket -= weight
            if ticket < 0:
                return Const(ty, number)
        raise AssertionError('weight table')
    if ty == 'bool':
        return Const(ty, bool(draw.below(2)))
    if ty == 'reason':
        return Const(ty, draw.choose(REASON_NAMES))
    return Const('action', draw.choose(('retry', 'abort')))


def _leaf(ty, hook, state, draw, weights):
    choices = [('constant', None)]
    if ty == 'reason' and hook == 'abort':
        choices.append(('reason', None))
    if ty == 'u32' and hook == 'lock':
        choices.append(('attempt', None))
    choices += [('field', i) for i, field in enumerate(state) if field.type == ty]
    kind, index = draw.choose(choices)
    return (Reason() if kind == 'reason' else Attempt() if kind == 'attempt'
            else StateRef(index) if kind == 'field' else _constant(ty, draw, weights))


def _grow(ty, hook, state, depth, draw, weights):
    if depth >= 4 or draw.below(2) == 0:
        return _leaf(ty, hook, state, draw, weights)
    ops = ['select']
    if ty == 'bool':
        ops += ['compare-u32', 'compare-u64', 'compare-bool']
        if hook == 'abort':
            ops.append('compare-reason')
    if ty in ('u32', 'u64'):
        ops += ['min', 'max', 'add', 'sub', 'shift']
    op = draw.choose(ops)
    child = lambda kind: _grow(kind, hook, state, depth + 1, draw, weights)
    if op == 'select':
        return Select(child('bool'), child(ty), child(ty))
    if op.startswith('compare-'):
        operand = op.split('-', 1)[1]
        comparisons = ('==', '!=') if operand in ('bool', 'reason') else ('==', '!=', '<', '<=', '>', '>=')
        return Compare(draw.choose(comparisons), child(operand), child(operand))
    if op == 'shift':
        return Shift(draw.choose(('<<', '>>')), child(ty), draw.below(32 if ty == 'u32' else 64))
    cls = {'min': Min, 'max': Max, 'add': SatAdd, 'sub': SatSub}[op]
    return cls(child(ty), child(ty))


def _state(draw, weights):
    return tuple(StateField(ty := draw.choose(('u32', 'u64', 'bool')),
                            _constant(ty, draw, weights)) for _ in range(draw.below(5)))


def _next(hook, state, draw, weights):
    return None if draw.below(2) == 0 else tuple(_grow(f.type, hook, state, 1, draw, weights) for f in state)


def _random(draw, weights):
    state = _state(draw, weights)
    return PolicyIR(state,
        AbortHook(_grow('u32', 'abort', state, 1, draw, weights), _next('abort', state, draw, weights)),
        LockHook(_grow('action', 'lock', state, 1, draw, weights),
                 _grow('u32', 'lock', state, 1, draw, weights), _next('lock', state, draw, weights)),
        CommitHook(_next('commit', state, draw, weights)))


def _valid(ir):
    try:
        validate_ir(ir)
        document = tagged(ir)
        parse_policy_ir(document)
        render_policy(ir)
        return document
    except ValueError:
        return None


def _generate(version, series, a, mode, maker):
    weights = weights_table()
    for counter in range(1000):
        preimage = f'{version}|{mode}|{series}|{a}|{counter}'
        document = _valid(maker(_Draw(preimage), weights))
        if document is not None:
            return document, {'name': {'random': 'random-ir', 'evo': 'evo-ir',
                                      'evo-fallback': 'evo-fallback-ir'}[mode],
                              'version': version, 'series': series, 'a': a,
                              'counter': counter, 'preimage': preimage}
    return None, {'name': {'random': 'random-ir', 'evo': 'evo-ir',
                          'evo-fallback': 'evo-fallback-ir'}[mode],
                  'version': version, 'series': series, 'a': a,
                  'counter': 1000, 'preimage': f'{version}|{mode}|{series}|{a}|999'}


def random_ir(version: str, series: int, a: int):
    return _generate(version, series, a, 'random', _random)


def _sites(ir):
    """Return (path, type, hook, depth) for every mutable expression node."""
    sites = []
    def visit(expr, path, ty, hook, depth):
        sites.append((path, ty, hook, depth))
        if isinstance(expr, Select):
            for name, child, child_ty in (('condition', expr.condition, 'bool'),
                                         ('yes', expr.yes, ty), ('no', expr.no, ty)):
                visit(child, path + (name,), child_ty, hook, depth + 1)
        elif isinstance(expr, Compare):
            operand = _expr_type(expr.left, ir.fields)
            visit(expr.left, path + ('left',), operand, hook, depth + 1)
            visit(expr.right, path + ('right',), operand, hook, depth + 1)
        elif isinstance(expr, (Min, Max, SatAdd, SatSub)):
            visit(expr.left, path + ('left',), ty, hook, depth + 1)
            visit(expr.right, path + ('right',), ty, hook, depth + 1)
        elif isinstance(expr, Shift):
            visit(expr.value, path + ('value',), ty, hook, depth + 1)
    for i, field in enumerate(ir.fields):
        sites.append((('fields', i, 'initial_literal'), field.type, 'abort', 1))
    for name, hook, outputs in (('after_abort', ir.after_abort, (('wait', 'u32'),)),
                                ('on_lock_conflict', ir.on_lock_conflict, (('action', 'action'), ('wait', 'u32'))),
                                ('on_commit', ir.on_commit, ())):
        context = {'after_abort': 'abort', 'on_lock_conflict': 'lock', 'on_commit': 'commit'}[name]
        for member, ty in outputs:
            visit(getattr(hook, member), (name, member), ty, context, 1)
        if hook.next_state is not None:
            for i, expr in enumerate(hook.next_state):
                visit(expr, (name, 'next_state', i), ir.fields[i].type, context, 1)
    return sites


def _expr_type(expr, state):
    if isinstance(expr, Const): return expr.type
    if isinstance(expr, Reason): return 'reason'
    if isinstance(expr, Attempt): return 'u32'
    if isinstance(expr, StateRef): return state[expr.index].type
    if isinstance(expr, Compare): return 'bool'
    if isinstance(expr, Select): return _expr_type(expr.yes, state)
    return _expr_type(expr.value if isinstance(expr, Shift) else expr.left, state)


def _replace_path(obj, path, value):
    if not path:
        return value
    key, *tail = path
    if isinstance(key, int):
        items = list(obj)
        items[key] = _replace_path(items[key], tail, value)
        return tuple(items)
    return replace(obj, **{key: _replace_path(getattr(obj, key), tail, value)})


def _evolve(parent, draw, weights):
    ir = parent
    if len(ir.fields) < 4 and draw.below(5) == 0:
        ty = draw.choose(('u32', 'u64', 'bool'))
        new_fields = ir.fields + (StateField(ty, _constant(ty, draw, weights)),)
        new_index = len(ir.fields)
        hooks = {}
        for name in ('after_abort', 'on_lock_conflict', 'on_commit'):
            hook = getattr(ir, name)
            hooks[name] = replace(hook, next_state=(hook.next_state + (StateRef(new_index),)
                             if hook.next_state is not None else None))
        ir = replace(ir, fields=new_fields, **hooks)
    # Omitted next_state is expanded only for mutation site enumeration.
    hooks = {}
    for name in ('after_abort', 'on_lock_conflict', 'on_commit'):
        hook = getattr(ir, name)
        if hook.next_state is None:
            hooks[name] = replace(hook, next_state=tuple(StateRef(i) for i in range(len(ir.fields))))
    expanded = replace(ir, **hooks)
    path, ty, hook, depth = draw.choose(_sites(expanded))
    replacement = _constant(ty, draw, weights) if path[0] == 'fields' else _grow(ty, hook, expanded.fields, depth, draw, weights)
    return _replace_path(expanded, path, replacement)


def evolve_ir(version: str, series: int, a: int, points: Sequence[dict]):
    if not points:
        return _generate(version, series, a, 'evo-fallback', _random)
    parent = min(points, key=lambda p: (-p['fitness_tps'], p['slot_order']))
    parent_ir = parse_policy_ir(parent['ir'])
    parent_body = render_policy(parent_ir)
    weights = weights_table()
    for counter in range(1000):
        preimage = f'{version}|evo|{series}|{a}|{counter}'
        try:
            child = _evolve(parent_ir, _Draw(preimage), weights)
            document = _valid(child)
            if document is None or render_policy(child) == parent_body:
                continue
        except ValueError:
            continue
        return document, {'name': 'evo-ir', 'version': version, 'series': series,
                          'a': a, 'counter': counter, 'preimage': preimage}
    return None, {'name': 'evo-ir', 'version': version, 'series': series,
                  'a': a, 'counter': 1000, 'preimage': f'{version}|evo|{series}|{a}|999'}
