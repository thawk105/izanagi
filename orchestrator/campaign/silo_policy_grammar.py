"""Typed, allowlisted policy-C++ v1 parser (LP64 GCC); no shared lexer."""
from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class PolicyDecision:
    accepted: bool
    stage: str = "grammar"
    rule_id: str | None = None
    offset: int | None = None
    line: int | None = None
    column: int | None = None
    reason: str | None = None


@dataclass(frozen=True)
class Token:
    text: str
    offset: int
    kind: str = "punct"
    value: int | None = None
    type: str | None = None


@dataclass
class Symbol:
    type: str
    const: bool = False
    ref: bool = False
    origin: str = "local"


@dataclass
class Expr:
    type: str
    lvalue: bool = False
    const: bool = False
    literal: int | None = None
    symbol: Symbol | None = None
    callable_statement: bool = False
    assigned: bool = False


class _Reject(Exception):
    def __init__(self, rule: str, token: Token, reason: str):
        self.rule, self.token, self.reason = rule, token, reason


_ALT = dict(zip(
    'and or not bitand bitor compl xor and_eq or_eq xor_eq not_eq'.split(),
    '&& || ! & | ~ ^ &= |= ^= !='.split()))
_LEX = re.compile(r'\s+|[A-Za-z_][A-Za-z_0-9]*|[0-9][A-Za-z_0-9\x27.]*|<<=|>>=|::|->|\+\+|--|&&|\|\||==|!=|<=|>=|<<|>>|[+*/%&|^\-]=|<:|:>|<%|%>|%:|.', re.DOTALL)
_NUM = re.compile(r"(0[xX][0-9a-fA-F](?:'?[0-9a-fA-F])*|0[bB][01](?:'?[01])*|0(?:'?[0-7])*|[1-9](?:'?[0-9])*)([uU](?:[lL])?)\Z")
_TYPES = {'uint32_t': 'U32', 'uint64_t': 'U64', 'bool': 'bool', 'void': 'void', 'PolicyState': 'PolicyState'}
for _name in ('PolicyAction', 'AbortReason', 'LockResponse', 'AbortContext', 'LockContext', 'CommitContext'):
    _TYPES['izanagi_silo_api::' + _name] = _name
_NUMERIC = {'U32', 'U64'}
_ENUMS = {'PolicyAction': ('retry', 'abort'), 'AbortReason': ('unset', 'lock_conflict', 'update_absent', 'read_tid', 'read_locked', 'node_validation', 'insert_node', 'scan_node')}
_FIELDS = {'AbortContext': {'reason': 'AbortReason', 'rand': 'U64'}, 'LockContext': {'attempt': 'U32', 'rand': 'U64'}, 'CommitContext': {}, 'LockResponse': {'action': 'PolicyAction', 'wait_us': 'U32'}}
_STORAGE = {'static', 'thread_local', 'extern', 'inline', 'mutable', 'volatile'}
_KEYWORDS = set(('alignas alignof asm auto bool break case catch char char16_t char32_t '
                 'class const constexpr const_cast continue decltype default delete do '
                 'double dynamic_cast else enum explicit export extern false float for '
                 'friend goto if inline int long mutable namespace new noexcept nullptr '
                 'operator private protected public register reinterpret_cast return short '
                 'signed sizeof static static_assert static_cast struct switch template this '
                 'thread_local throw true try typedef typeid typename union unsigned using '
                 'virtual void volatile wchar_t while').split())
_ASSIGN = {'=', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>='}
_PREC = {'||': 1, '&&': 2, '|': 3, '^': 4, '&': 5, '==': 6, '!=': 6, '<': 7, '<=': 7, '>': 7, '>=': 7, '<<': 8, '>>': 8, '+': 9, '-': 9, '*': 10, '/': 10, '%': 10}


def _lex(source: str) -> list[Token]:
    if len(source.encode('utf-8')) > 256 * 1024:
        raise _Reject('limit.source', Token('', 0), 'source exceeds 256 KiB')
    out = []
    for m in _LEX.finditer(source):
        s = m.group()
        if s.isspace():
            continue
        t = Token(s, m.start())
        if s in _ALT:
            t = Token(_ALT[s], m.start(), 'alternative')
            raise _Reject('lex.alternative-token', t, 'alternative operator spelling')
        if s in ('<:', ':>', '<%', '%>', '%:'):
            raise _Reject('lex.digraph', t, 'digraph')
        if '__' in s:
            raise _Reject('lex.reserved-identifier', t, 'reserved identifier')
        if s == '::' and (not out or out[-1].kind != 'identifier' or out[-1].text in {'return', 'const', 'constexpr', 'case', 'throw', 'new', 'delete', 'noexcept', 'else'}):
            raise _Reject('lex.global-qualifier', t, 'leading global qualifier')
        if s in ('[', ']', '->', '"', "'"):
            raise _Reject('lex.forbidden', t, 'forbidden lexical form')
        if s[0].isdigit():
            n = _NUM.fullmatch(s)
            if not n:
                raise _Reject('lex.literal-suffix', t, 'expected integer with u or ul suffix')
            digits, suffix = n.groups()
            digits = digits.replace("'", '')
            base = 16 if digits.lower().startswith('0x') else 2 if digits.lower().startswith('0b') else 8 if digits.startswith('0') else 10
            significant = (digits[2:] if base in (2, 16) else digits).lstrip('0') or '0'
            if len(significant) > {2: 64, 8: 22, 10: 20, 16: 16}[base]:
                raise _Reject('lex.integer-range', t, 'integer exceeds UINT64_MAX')
            value = int(significant, base)
            if value > (1 << 64) - 1:
                raise _Reject('lex.integer-range', t, 'integer exceeds UINT64_MAX')
            t = Token(s, m.start(), 'integer', value, 'U64' if suffix.lower() == 'ul' or value >= 1 << 32 else 'U32')
        elif s not in _ALT and re.fullmatch('[A-Za-z_][A-Za-z_0-9]*', s):
            t = Token(s, m.start(), 'identifier')
        out.append(t)
        if len(out) > 4096:
            raise _Reject('limit.tokens', t, 'more than 4096 tokens')
    out.append(Token('<eof>', len(source)))
    return out


class _Parser:
    def __init__(self, tokens: list[Token]):
        self.ts, self.i = tokens, 0
        self.scopes: list[dict[str, Symbol]] = [{}]
        self.functions: dict[str, tuple[str, list[Symbol]]] = {}
        self.state: dict[str, str] | None = None
        self.current = ''
        self.result = 'void'
        self.initializing: str | None = None
        self.constant = False
        self.depth = 0
        self.switch_depth = 0

    @property
    def t(self):
        return self.ts[self.i]

    def fail(self, rule, reason, token=None):
        raise _Reject(rule, token or self.t, reason)

    def eat(self, s):
        if self.t.text == s:
            self.i += 1
            return True
        return False

    def need(self, s, rule='syntax.expected'):
        if not self.eat(s):
            self.fail(rule, 'expected ' + s)

    def name(self):
        t = self.t
        if t.kind != 'identifier' or t.text in _TYPES or t.text in _KEYWORDS:
            self.fail('decl.name', 'expected declaration name')
        self.i += 1
        return t.text

    def qualified(self):
        if self.t.kind != 'identifier':
            self.fail('name.resolve', 'expected name')
        name = self.t.text
        self.i += 1
        while self.eat('::'):
            if self.t.kind != 'identifier':
                self.fail('name.resolve', 'expected qualified name')
            name += '::' + self.t.text
            self.i += 1
        return name

    def type(self):
        t = self.t
        if t.text in _STORAGE:
            self.fail('decl.storage', 'forbidden storage specifier')
        name = self.qualified()
        if name not in _TYPES:
            self.fail('decl.function', 'type outside policy contract', t)
        return _TYPES[name]

    def declare(self, name, symbol):
        if name in self.scopes[-1]:
            self.fail('decl.name', 'duplicate declaration')
        self.scopes[-1][name] = symbol

    def lookup(self, name, token):
        if name == self.initializing:
            self.fail('init.self', 'initializer refers to its own declaration', token)
        for scope in reversed(self.scopes):
            if name in scope:
                s = scope[name]
                if self.constant and s.origin != 'constant':
                    self.fail('decl.constant', 'nonconstant reference', token)
                return s
        self.fail('name.resolve', 'unresolved name: ' + name, token)

    def convertible(self, target, e):
        if target != e.type and not ({target, e.type} <= _NUMERIC):
            self.fail('type.conversion', 'incompatible types: ' + target + ' and ' + e.type)

    def numeric(self, e):
        if e.type not in _NUMERIC:
            self.fail('type.numeric', 'unsigned numeric operand required')
        return e.type

    def parse(self):
        while self.t.text != '<eof>':
            if self.eat('struct'):
                self.need('PolicyState', 'decl.state')
                if self.state is not None:
                    self.fail('decl.state', 'exactly one PolicyState required')
                self.state = {}
                self.need('{', 'decl.state')
                while not self.eat('}'):
                    ty = self.type()
                    if ty not in _NUMERIC | {'bool'} or len(self.state) >= 16:
                        self.fail('decl.state', 'invalid state member type or count')
                    name = self.name()
                    if name in self.state:
                        self.fail('decl.state', 'duplicate state member')
                    self.need('=', 'decl.state')
                    e = self.literal()
                    if e.type != ty:
                        self.fail('decl.state', 'state initializer must be literal of member type')
                    self.need(';', 'decl.state')
                    self.state[name] = ty
                self.need(';', 'decl.state')
            elif self.eat('constexpr'):
                ty = self.type()
                if ty not in _NUMERIC | {'bool'}:
                    self.fail('decl.constant', 'invalid constant type')
                name = self.name()
                self.declare(name, Symbol(ty, True, origin='constant'))
                self.need('=', 'decl.constant')
                self.initializing, self.constant = name, True
                e = self.expr()
                self.initializing, self.constant = None, False
                self.convertible(ty, e)
                self.need(';', 'decl.constant')
            else:
                self.function()
        if self.state is None:
            self.fail('decl.state', 'missing PolicyState')
        signatures = {
            'policy_after_abort': ('U32', 'AbortContext'),
            'policy_on_lock_conflict': ('LockResponse', 'LockContext'),
            'policy_on_commit': ('void', 'CommitContext'),
        }
        for name, (ret, ctx) in signatures.items():
            if name not in self.functions:
                self.fail('decl.function', 'missing required function: ' + name)
            r, args = self.functions[name]
            if r != ret or [(a.type, a.ref, a.const) for a in args] != [('PolicyState', True, False), (ctx, True, True)]:
                self.fail('decl.function', 'incorrect required signature: ' + name)

    def function(self):
        ret = self.type()
        if ret not in _NUMERIC | {'bool', 'void', 'LockResponse'}:
            self.fail('decl.function', 'invalid return type')
        name = self.name()
        if name in self.functions or name in self.scopes[0]:
            self.fail('decl.function', 'duplicate function')
        self.need('(', 'decl.function')
        args, names = [], []
        if not self.eat(')'):
            while True:
                const = self.eat('const')
                ty = self.type()
                ref = self.eat('&')
                if ref:
                    valid = ty == 'PolicyState' or (ty in {'AbortContext', 'LockContext', 'CommitContext'} and const)
                else:
                    valid = ty in _NUMERIC | {'bool'} | set(_ENUMS) and not const
                if not valid:
                    self.fail('decl.function', 'invalid parameter form')
                names.append(self.name() if self.t.kind == 'identifier' else None)
                args.append(Symbol(ty, const, ref, 'parameter'))
                if self.eat(')'):
                    break
                self.need(',', 'decl.function')
        self.need('noexcept', 'decl.function')
        self.current, self.result = name, ret
        self.scopes.append({})
        for n, a in zip(names, args):
            if n is not None:
                self.declare(n, a)
        last = self.block(new_scope=False)
        self.scopes.pop()
        if ret != 'void' and last != 'return':
            self.fail('return.final', 'nonvoid body must end with return')
        self.functions[name] = (ret, args)
        self.current = ''

    def block(self, new_scope=True):
        self.need('{')
        if new_scope:
            self.scopes.append({})
        self.depth += 1
        if self.depth > 64:
            self.fail('limit.depth', 'nesting exceeds 64')
        last = None
        while not self.eat('}'):
            last = self.statement()
        self.depth -= 1
        if new_scope:
            self.scopes.pop()
        return last

    def statement(self):
        self.depth += 1
        if self.depth > 64:
            self.fail('limit.depth', 'statement nesting exceeds 64')
        result = self._statement()
        self.depth -= 1
        return result

    def _statement(self):
        t = self.t
        if t.text in _STORAGE:
            self.fail('decl.storage', 'forbidden storage')
        if t.text == '{':
            self.block()
            return 'block'
        if self.eat('return'):
            if self.result == 'void':
                self.need(';', 'type.conversion')
            else:
                self.convertible(self.result, self.expr())
                self.need(';')
            return 'return'
        if self.eat('if'):
            self.need('(')
            self.convertible('bool', self.expr())
            self.need(')')
            self.scopes.append({})
            self.statement()
            self.scopes.pop()
            if self.eat('else'):
                self.scopes.append({})
                self.statement()
                self.scopes.pop()
            return 'if'
        if self.eat('switch'):
            self.switch()
            return 'switch'
        if self.eat('break'):
            if not self.switch_depth:
                self.fail('switch.closed', 'break outside switch', t)
            self.need(';')
            return 'break'
        if t.text == 'const' or t.text in ('uint32_t', 'uint64_t', 'bool', 'izanagi_silo_api'):
            const = self.eat('const')
            ty = self.type()
            if ty not in _NUMERIC | {'bool', 'LockResponse'} | set(_ENUMS):
                self.fail('decl.local', 'invalid local type')
            name = self.name()
            self.declare(name, Symbol(ty, const))
            self.need('=', 'decl.local')
            self.initializing = name
            e = self.expr()
            self.initializing = None
            self.convertible(ty, e)
            self.need(';')
            return 'declaration'
        if t.text in {'for', 'while', 'do', 'goto', 'throw', 'try', 'asm', 'using', 'namespace', 'typedef', 'new', 'delete', '++', '--', ';'}:
            self.fail('stmt.forbidden', 'statement outside allowlist')
        e = self.expr(allow_assignment=True)
        if not e.assigned and not (e.type == 'void' and e.callable_statement):
            self.fail('stmt.forbidden', 'only assignment and void calls are expression statements', t)
        self.need(';')
        return 'expression'

    def switch(self):
        self.need('(')
        cond = self.expr()
        if cond.type not in _NUMERIC | set(_ENUMS):
            self.fail('type.numeric', 'invalid switch condition')
        self.need(')')
        self.need('{')
        self.switch_depth += 1
        self.scopes.append({})
        labels = set()
        default = False
        while not self.eat('}'):
            if self.eat('case'):
                token = self.t
                if token.kind == 'integer':
                    e = self.literal()
                    key = e.literal
                    if cond.type not in _NUMERIC:
                        self.fail('type.conversion', 'integer case for enum')
                    key %= 1 << (32 if cond.type == 'U32' else 64)
                else:
                    name = self.qualified()
                    e = self.enum(name, token)
                    self.convertible(cond.type, e)
                    key = name
                if key in labels:
                    self.fail('switch.closed', 'duplicate case')
                labels.add(key)
            elif self.eat('default'):
                if default:
                    self.fail('switch.closed', 'duplicate default')
                default = True
            else:
                self.fail('switch.closed', 'expected case or default')
            self.need(':')
            last = None
            while self.t.text not in ('case', 'default', '}'):
                if self.t.text in ('const', 'uint32_t', 'uint64_t', 'bool', 'izanagi_silo_api'):
                    self.fail('switch.closed', 'case declarations require block')
                if self.t.text == '{':
                    last = self.block()
                else:
                    last = self.statement()
            if last not in ('break', 'return'):
                self.fail('switch.closed', 'case must end with break or return')
        self.scopes.pop()
        self.switch_depth -= 1

    def literal(self):
        t = self.t
        if t.kind == 'integer':
            self.i += 1
            return Expr(t.type, literal=t.value)
        if t.text in ('true', 'false'):
            self.i += 1
            return Expr('bool', literal=int(t.text == 'true'))
        self.fail('decl.state', 'literal required')

    def enum(self, name, token):
        parts = name.split('::')
        if len(parts) == 3 and parts[0] == 'izanagi_silo_api' and parts[1] in _ENUMS and parts[2] in _ENUMS[parts[1]]:
            return Expr(parts[1])
        self.fail('name.resolve', 'unknown enumerator: ' + name, token)

    def expr(self, minimum=0, allow_assignment=False):
        self.depth += 1
        if self.depth > 64:
            self.fail('limit.depth', 'expression nesting exceeds 64')
        left = self.primary()
        while self.t.text in _PREC and _PREC[self.t.text] >= minimum:
            op = self.t.text
            self.i += 1
            right = self.expr(_PREC[op] + 1)
            left = self.binary(op, left, right)
        if minimum == 0 and self.eat('?'):
            self.convertible('bool', left)
            a = self.expr()
            self.need(':')
            b = self.expr()
            if a.type != b.type:
                self.fail('type.branch', 'conditional branches must have identical types')
            left = Expr(a.type, a.lvalue and b.lvalue, a.const or b.const)
        if minimum == 0 and self.t.text in _ASSIGN:
            if not allow_assignment:
                self.fail('assignment.statement', 'assignment must be a standalone statement')
            op = self.t.text
            self.i += 1
            if (not left.lvalue or left.const or left.symbol is None
                    or left.symbol.origin == 'parameter'
                    or left.type in {'PolicyState', 'AbortContext', 'LockContext', 'CommitContext'}):
                self.fail('assignment.target', 'not a mutable assignment target')
            right = self.expr()
            if op == '=':
                self.convertible(left.type, right)
            else:
                self.binary(op[:-1], left, right)
            left = Expr(left.type, assigned=True)
        if self.t.text in ('++', '--'):
            self.fail('stmt.forbidden', 'increment/decrement forbidden')
        self.depth -= 1
        return left

    def primary(self):
        t = self.t
        if t.text in ('!', '~', '-'):
            self.i += 1
            e = self.expr(11)
            if t.text == '!':
                self.convertible('bool', e)
                return Expr('bool')
            return Expr(self.numeric(e))
        if self.eat('('):
            e = self.expr()
            if self.t.text == ',':
                self.fail('stmt.forbidden', 'comma operator forbidden')
            self.need(')')
            # Parentheses preserve value category, but are not integer literals.
            return Expr(e.type, e.lvalue, e.const, symbol=e.symbol)
        if t.kind == 'integer' or t.text in ('true', 'false'):
            return self.literal()
        if self.eat('static_cast'):
            self.need('<')
            ty = self.type()
            if ty not in _NUMERIC | {'bool'}:
                self.fail('type.conversion', 'invalid cast target')
            self.need('>')
            self.need('(')
            e = self.expr()
            self.need(')')
            if e.type not in _NUMERIC | {'bool'} | set(_ENUMS):
                self.fail('type.conversion', 'invalid cast source')
            return Expr(ty)
        name = self.qualified()
        if name == 'izanagi_silo_api::LockResponse':
            if self.constant:
                self.fail('decl.constant', 'aggregate is not scalar constant')
            self.need('{', 'type.conversion')
            a = self.expr()
            self.need(',')
            b = self.expr()
            self.need('}')
            if a.type != 'PolicyAction' or b.type != 'U32':
                self.fail('type.conversion', 'LockResponse requires PolicyAction and U32')
            return Expr('LockResponse')
        if name in ('std::min', 'std::max'):
            if self.constant:
                self.fail('decl.constant', 'calls forbidden in constant expression')
            self.need('(', 'type.minmax')
            a = self.expr()
            self.need(',', 'type.minmax')
            b = self.expr()
            self.need(')', 'type.minmax')
            if a.type != b.type or a.type not in _NUMERIC:
                self.fail('type.minmax', 'min/max requires identical unsigned types')
            return Expr(a.type)
        if name == self.current:
            self.fail('call.dag', 'self reference forbidden', t)
        if name in self.functions:
            if self.constant:
                self.fail('decl.constant', 'calls forbidden in constant expression')
            # Locals may shadow a function; such a local is not callable.
            if any(name in s for s in self.scopes):
                self.fail('name.resolve', 'function name shadowed', t)
            ret, params = self.functions[name]
            self.need('(', 'call.dag')
            args = []
            if not self.eat(')'):
                while True:
                    args.append(self.expr())
                    if self.eat(')'):
                        break
                    self.need(',')
            if len(args) != len(params):
                self.fail('type.conversion', 'argument count mismatch')
            for p, a in zip(params, args):
                self.convertible(p.type, a)
                if p.ref and (not a.lvalue or (not p.const and a.const)):
                    self.fail('type.conversion', 'reference binding mismatch')
            return Expr(ret, callable_statement=True)
        if name.startswith('izanagi_silo_api::'):
            if self.constant:
                self.fail('decl.constant', 'enumerator outside scalar constant grammar', t)
            return self.enum(name, t)
        s = self.lookup(name, t)
        if self.eat('.'):
            member = self.name()
            fields = self.state if s.type == 'PolicyState' else _FIELDS.get(s.type)
            if fields is None or member not in fields:
                self.fail('name.resolve', 'unknown member')
            mutable = (s.type == 'PolicyState' and s.ref and s.origin == 'parameter') or (s.type == 'LockResponse' and s.origin == 'local')
            field = Symbol(fields[member], s.const, origin='member' if mutable else 'readonly-member')
            return Expr(fields[member], True, s.const or not mutable, symbol=field)
        return Expr(s.type, True, s.const, symbol=s)

    def binary(self, op, a, b):
        if op in ('&&', '||'):
            self.convertible('bool', a)
            self.convertible('bool', b)
            return Expr('bool')
        if op in ('==', '!=') and a.type == b.type and a.type in {'bool'} | set(_ENUMS):
            return Expr('bool')
        at, bt = self.numeric(a), self.numeric(b)
        if op in ('/', '%', '<<', '>>'):
            if b.literal is None or (op in ('/', '%') and b.literal == 0) or (op in ('<<', '>>') and b.literal >= (32 if at == 'U32' else 64)):
                self.fail('rhs.literal', 'nonzero divisor or in-range literal shift required')
        if op in ('==', '!=', '<', '<=', '>', '>='):
            return Expr('bool')
        return Expr(at if op in ('<<', '>>') else 'U64' if 'U64' in (at, bt) else 'U32')


def validate_policy(source: str) -> PolicyDecision:
    """Reject candidate syntax as data; implementation failures propagate."""
    try:
        _Parser(_lex(source)).parse()
    except _Reject as e:
        offset = e.token.offset
        return PolicyDecision(False, rule_id=e.rule, offset=offset,
                              line=source.count('\n', 0, offset) + 1,
                              column=offset - source.rfind('\n', 0, offset),
                              reason=e.reason[:256])
    return PolicyDecision(True)
