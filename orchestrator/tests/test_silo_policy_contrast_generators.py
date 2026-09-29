from orchestrator.campaign import silo_policy_contrast_generators as G
from orchestrator.campaign.silo_policy_ir import parse_policy_ir, render_policy

VERSION = 'silo-policy-contrast-test-2026-09-29'


def test_random_fixed_preimage_and_tagged_ir():
    first = G.random_ir(VERSION, 1, 1)
    assert first == G.random_ir(VERSION, 1, 1)
    document, provenance = first
    assert provenance['preimage'] == f'{VERSION}|random|1|1|{provenance["counter"]}'
    assert provenance['name'] == 'random-ir'
    assert 'policy_after_abort' in render_policy(parse_policy_ir(document))
    assert G.random_ir(VERSION, 1, 2) != first


def test_zero_mixture_and_retry(monkeypatch):
    class Draw:
        def __init__(self, zero): self.zero = zero
        def below(self, limit): return 0 if limit == 8 and self.zero else (1 if limit == 8 else 0)
    assert G._constant('u32', Draw(True), (1,)) == G.Const('u32', 0)
    assert G._constant('u32', Draw(False), (1,)) == G.Const('u32', 1)
    calls = []
    def maker(draw, weights):
        calls.append(draw.preimage)
        return G.PolicyIR((), G.AbortHook(G.Const('u32', -1 if len(calls) == 1 else 0)),
                          G.LockHook(G.Const('action', 'abort'), G.Const('u32', 0)), G.CommitHook())
    monkeypatch.setattr(G, 'weights_table', lambda: (1,))
    document, provenance = G._generate(VERSION, 2, 3, 'random', maker)
    assert document['kind'] == 'PolicyIR'
    assert provenance['counter'] == 1
    assert calls == [f'{VERSION}|random|2|3|0', f'{VERSION}|random|2|3|1']


def test_evolution_tie_parent_and_field_extension(monkeypatch):
    a, _ = G.random_ir(VERSION, 3, 1)
    b, _ = G.random_ir(VERSION, 3, 2)
    points = [{'slot_order': 0, 'fitness_tps': 100, 'ir': a},
              {'slot_order': 1, 'fitness_tps': 100, 'ir': b}]
    captured = []
    original_evolve = G._evolve
    def observe(parent, draw, weights):
        captured.append(render_policy(parent))
        return original_evolve(parent, draw, weights)
    monkeypatch.setattr(G, '_evolve', observe)
    child, provenance = G.evolve_ir(VERSION, 3, 4, points)
    assert captured and all(body == render_policy(parse_policy_ir(a)) for body in captured)
    assert provenance['name'] == 'evo-ir'
    assert child is None or render_policy(parse_policy_ir(child)) != render_policy(parse_policy_ir(a))
    class FieldDraw:
        def below(self, limit): return 0
        def choose(self, values): return values[0]
    parent = parse_policy_ir(a)
    if len(parent.fields) < 4:
        evolved = G._evolve(parent, FieldDraw(), (1,))
        assert len(evolved.fields) == len(parent.fields) + 1
        for name in ('after_abort', 'on_lock_conflict', 'on_commit'):
            hook = getattr(evolved, name)
            assert hook.next_state is not None
            assert len(hook.next_state) == len(evolved.fields)


def test_evolution_fallback():
    document, provenance = G.evolve_ir(VERSION, 4, 1, [])
    assert provenance['preimage'].startswith(f'{VERSION}|evo-fallback|4|1|')
    assert provenance['name'] == 'evo-fallback-ir'
    parse_policy_ir(document)


def test_retry_cap_returns_empty(monkeypatch):
    monkeypatch.setattr(G, 'weights_table', lambda: (1,))
    invalid = lambda draw, weights: G.PolicyIR((), G.AbortHook(G.Const('u32', -1)),
        G.LockHook(G.Const('action', 'abort'), G.Const('u32', 0)), G.CommitHook())
    document, provenance = G._generate(VERSION, 5, 6, 'random', invalid)
    assert document is None
    assert provenance['counter'] == 1000


def test_bool_grow_selects_operator_before_compare_operand():
    class Draw:
        def __init__(self, operator):
            self.operator = operator
            self.operations = []
        def below(self, limit):
            return 1 if limit == 2 and not self.operations else 0
        def choose(self, values):
            if tuple(values) == ('select', 'compare'):
                self.operations.append(tuple(values))
                return values[self.operator]
            return values[0]
    outputs = []
    for operator in (0, 1, 0, 1):
        draw = Draw(operator)
        outputs.append(type(G._grow('bool', 'lock', (), 1, draw, (1,))).__name__)
        assert draw.operations == [('select', 'compare')]
    assert outputs == ['Select', 'Compare', 'Select', 'Compare']
