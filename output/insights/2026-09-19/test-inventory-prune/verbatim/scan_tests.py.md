# scanner 逐語 — t_inv_scanner/scan_tests.py (Codex author、fix1 後)

実装面 (probe) は repo へ入れない規律により、逐語を `.md` に保存する。実行本体は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-test-inventory-prune/t_inv_scanner/` にある。

sha256: 8909159873bd4b9897485a055860c77fedd691dba3c74fb5943eaa552f17da1d

```python
"""Static test inventory. Scanned code is never imported or executed."""
import argparse
import ast
import collections
import hashlib
import json
import pathlib
import re

PATH = re.compile(r'^(?:orchestrator|tools|docs|hooks|\.claude|external)/')
REF = re.compile(r'\b(?:D\d+|T-\d+|B-\d+|F\d+)\b')
NODE = re.compile(r'(?:orchestrator/tests/)?test_\w+\.py::\w+(?:::\w+)*')


def dotted(n):
    if isinstance(n, ast.Name):
        return n.id
    if isinstance(n, ast.Attribute):
        return dotted(n.value) + '.' + n.attr
    return ''


def strings(n):
    return [v for v in ast.walk(n) if isinstance(v, ast.Constant) and isinstance(v.value, str)]


def body(fn):
    b = fn.body
    if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) and isinstance(b[0].value.value, str):
        b = b[1:]
    return b


def fingerprint(fn, decorators=True):
    tree = ast.Tuple(elts=[fn.args, ast.Module(body=body(fn), type_ignores=[])] + (fn.decorator_list if decorators else []), ctx=ast.Load())
    return hashlib.sha256((type(fn).__name__ + ast.dump(tree, annotate_fields=False, include_attributes=False)).encode()).hexdigest()


def functions(tree, prefix=''):
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith('test_'):
            yield prefix + n.name, n
        elif isinstance(n, ast.ClassDef):
            yield from functions(n, prefix + n.name + '::')


def aliases(nodes):
    out = {}
    for n in nodes:
        if isinstance(n, ast.Import):
            for a in n.names:
                out[a.asname or a.name.split('.')[0]] = a.name if a.asname else a.name.split('.')[0]
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            for a in n.names:
                out[a.asname or a.name] = n.module + '.' + a.name
    return out


def resolve(n, mapping):
    first, sep, tail = dotted(n).partition('.')
    return mapping.get(first, first) + sep + tail


def parameters(fn, mapping):
    duplicates, unknown = [], []
    for d in fn.decorator_list:
        if not isinstance(d, ast.Call) or resolve(d.func, mapping) != 'pytest.mark.parametrize':
            continue
        kw = {k.arg: k.value for k in d.keywords}
        values = d.args[1] if len(d.args) > 1 else kw.get('argvalues')
        names = d.args[0] if d.args else kw.get('argnames')
        try:
            names = ast.literal_eval(names)
            arity = len(names.split(',')) if isinstance(names, str) else len(names)
        except (ValueError, TypeError, SyntaxError):
            arity = None
        if not isinstance(values, (ast.List, ast.Tuple)):
            unknown.append({'kind': 'unevaluable-parametrize-container', 'line': d.lineno, 'row_count': None})
            continue
        seen = []
        for i, row in enumerate(values.elts):
            try:
                if isinstance(row, ast.Call) and resolve(row.func, mapping) == 'pytest.param':
                    vals = [ast.literal_eval(v) for v in row.args]
                    value = vals[0] if arity == 1 and len(vals) == 1 else tuple(vals)
                else:
                    value = ast.literal_eval(row)
                    if arity and arity > 1 and isinstance(value, (tuple, list)):
                        value = tuple(value)
                peers = [j for j, old in seen if old == value]
                if peers:
                    duplicates.append({'kind': 'duplicate-parametrize-row', 'decorator_line': d.lineno, 'row_index_0based': i, 'line': row.lineno, 'equal_to_rows_0based': peers, 'value_repr': repr(value)})
                seen.append((i, value))
            except (ValueError, TypeError, SyntaxError, RecursionError) as exc:
                unknown.append({'kind': 'unevaluable-parametrize-row', 'row_index_0based': i, 'line': row.lineno, 'exception': type(exc).__name__})
    return duplicates, unknown


def metrics(records):
    return {'functions': len(records), 'lines': sum(r['line_count'] for r in records), 'nodeids': sum(r['nodeid_count'] for r in records), 'duration_seconds': round(sum(r['duration_seconds'] for r in records), 6), 'missing_duration_nodeids': sum(r['missing_duration_nodeids'] for r in records)}


def suppress_synthetic(fn, mapping, evidence):
    arguments = {n.arg for n in ast.walk(fn.args) if isinstance(n, ast.arg)}
    indicators = sorted(arguments & {'tmp_path', 'tmp_path_factory', 'tmpdir', 'pytester', 'testdir', 'monkeypatch'})
    bn = ast.Module(body=fn.body, type_ignores=[])
    for n in ast.walk(bn):
        name = resolve(n, mapping)
        if set(name.split('.')) & {'tempfile', 'mkdtemp', 'TemporaryDirectory', 'ScratchTree', 'write_text', 'write_bytes', 'mkdir', 'pytester'}:
            indicators.append(name)
    contexts = set()
    for n in ast.walk(fn):
        if isinstance(n, (ast.With, ast.AsyncWith)) and any(isinstance(i.context_expr, ast.Call) and resolve(i.context_expr.func, mapping) == 'pytest.raises' for i in n.items):
            for stmt in n.body:
                contexts.update(id(s) for s in strings(stmt))
        elif isinstance(n, ast.keyword) and n.arg == 'match':
            contexts.update(id(s) for s in strings(n.value))
        elif isinstance(n, ast.Assert) and isinstance(n.test, ast.Compare) and any(isinstance(op, ast.In) for op in n.test.ops):
            contexts.update(id(s) for s in strings(n.test))
    occurrences = collections.defaultdict(list)
    for s in strings(fn):
        for value in {s.value, *s.value.splitlines()}:
            occurrences[value].append(id(s))
    kept, suppressed = [], []
    literal_kinds = {'path-missing', 'subprocess-path-missing', 'flag-missing', 'docs-heading-missing'}
    for e in evidence:
        ids = occurrences.get(e.get('literal'), [])
        contextual = bool(ids) and all(i in contexts for i in ids)
        if e['kind'] in literal_kinds and (indicators or contextual):
            suppressed.append(dict(e, reason='synthetic-fixture', indicators=sorted(set(indicators)) or ['raises-or-message-only']))
        else:
            kept.append(e)
    return kept, suppressed


def production_targets(repo, file, imports, fn):
    refs = {dotted(n) for stmt in fn.body for n in ast.walk(stmt) if isinstance(n, (ast.Name, ast.Attribute)) and isinstance(n.ctx, ast.Load)}
    targets = set()
    def add(module):
        if module.split('.')[0] not in ('orchestrator', 'tools', 'hooks'):
            return
        p = repo.joinpath(*module.split('.'))
        for candidate in (p.with_suffix('.py'), p / '__init__.py'):
            if candidate.is_file():
                targets.add(candidate.relative_to(repo).as_posix())
                return
    for n in imports:
        if isinstance(n, ast.Import):
            for a in n.names:
                binding = a.asname or a.name
                if any(r.startswith(binding + '.') for r in refs):
                    add(a.name)
        else:
            module = '.'.join(file[:-3].split('/')[:-n.level] + ([n.module] if n.module else [])) if n.level else n.module
            if not module:
                continue
            for a in n.names:
                binding = a.asname or a.name
                if binding in refs:
                    child = repo.joinpath(*module.split('.'), a.name)
                    add(module + '.' + a.name if child.with_suffix('.py').is_file() or (child / '__init__.py').is_file() else module)
    return sorted(targets)


def scan(repo, collect_file, exclude_file):
    repo = pathlib.Path(repo).resolve()
    errors = []

    def error(path, exc):
        errors.append({'file': str(path.relative_to(repo)) if path.is_relative_to(repo) else str(path), 'exception': type(exc).__name__, 'message': str(exc)})

    def read(path):
        try:
            return path.read_text(encoding='utf-8')
        except Exception as exc:
            error(path, exc)
            return None

    def parse(path, source):
        try:
            return ast.parse(source, filename=str(path))
        except Exception as exc:
            error(path, exc)
            return None

    excluded = set(pathlib.Path(exclude_file).read_text().splitlines())
    collected = collections.defaultdict(list)
    for line in pathlib.Path(collect_file).read_text().splitlines():
        line = line.strip()
        if line.startswith('orchestrator/tests/test_') and '::' in line:
            collected[line.split('[', 1)[0]].append(line)
    ledger_path = repo / 'orchestrator/tests/acceptance_duration_ledger.json'
    try:
        ledger = json.loads(read(ledger_path))['duration_seconds_by_nodeid']
    except Exception as exc:
        error(ledger_path, exc)
        ledger = {}
    doc_sources = []
    for path in sorted((repo / 'docs').rglob('*.md')):
        source = read(path)
        if source is not None:
            doc_sources.append(source)
    all_docs = '\n'.join(doc_sources)
    withdrawn = collections.defaultdict(list)
    for lineno, line in enumerate((read(repo / 'docs/decisions.md') or '').splitlines(), 1):
        match = re.match(r'^## D(\d+)\.', line)
        if match and re.search('撤回|supersede|廃止|上書き', line, re.I):
            for ref in REF.findall(line):
                if ref.startswith('D') and ref != 'D' + match[1]:
                    withdrawn[ref].append({'file': 'docs/decisions.md', 'line': lineno, 'text': line})
    active = False
    for lineno, line in enumerate((read(repo / 'docs/phase3.md') or '').splitlines(), 1):
        if line.startswith('## '):
            active = line.startswith('## 見送り台帳')
        if active:
            for struck in re.findall(r'~~(.*?)~~', line):
                for ref in re.findall(r'\b(?:T-\d+|B-\d+)\b', struck):
                    withdrawn[ref].append({'file': 'docs/phase3.md', 'line': lineno, 'text': line})
    protections = collections.defaultdict(list)
    prefixes = []

    def index(nodes, file, reason):
        for n in nodes:
            for m in NODE.finditer(n.value):
                key = m[0].removeprefix('orchestrator/tests/')
                item = {'reason': reason, 'file': file, 'line': n.lineno, 'literal': n.value}
                if item not in protections[key]:
                    protections[key].append(item)

    def assignments(tree):
        for n in ast.walk(tree):
            if isinstance(n, (ast.Assign, ast.AnnAssign)):
                targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                yield [dotted(t) for t in targets], n.value

    for file in ('orchestrator/tests/conftest.py', 'orchestrator/tests/growth_test_holds.py', 'tools/update_acceptance_duration_ledger.py'):
        source = read(repo / file)
        tree = parse(repo / file, source) if source is not None else None
        if tree is None:
            continue
        if file.endswith('conftest.py'):
            for n in ast.walk(tree):
                if isinstance(n, ast.Call) and dotted(n.func) == 'frozenset':
                    index(strings(n), file, 'conftest-frozenset')
        elif file.endswith('growth_test_holds.py'):
            index(strings(tree), file, 'growth-test-hold')
        else:
            for names, value in assignments(tree):
                if value is None:
                    continue
                if '_ADD_ONLY_FROZEN_SUITE_PREFIXES' in names:
                    prefixes.extend({'prefix': s.value, 'file': file, 'line': s.lineno} for s in strings(value))
                if '_ADD_ONLY_FROZEN_REMOVED_NODEIDS' in names:
                    index(strings(value), file, 'add-only-frozen-removed-nodeid')
    records, groups = [], collections.defaultdict(list)
    body_groups = collections.defaultdict(list)
    counts = {'included_files': 0, 'included_file_lines': 0, 'excluded_files': 0, 'excluded_file_lines': 0}
    source_cache = {}

    def module_exists(module):
        path = repo.joinpath(*module.split('.'))
        return path.is_dir() or path.with_suffix('.py').is_file()

    def analyze(file, source, tree):
        global_mapping = aliases(tree.body)
        imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        lines = source.splitlines()
        for qualname, fn in functions(tree):
            base = file + '::' + qualname
            nodeids = collected.get(base, [])
            start = min([fn.lineno] + [d.lineno for d in fn.decorator_list])
            r = {'file': file, 'qualname': qualname, 'nodeid_base': base, 'start_line': start, 'end_line': fn.end_lineno, 'line_count': fn.end_lineno - start + 1, 'nodeids': nodeids, 'nodeid_count': len(nodeids), 'duration_seconds': round(sum(ledger.get(n, 0) for n in nodeids), 6), 'missing_duration_nodeids': sum(n not in ledger for n in nodeids), 'categories': [], 'evidence': {c: [] for c in 'ABCD'}, 'unresolved': [], 'always_skipped': [], 'protected': [], 'referenced_by': []}
            nodes = list(ast.walk(fn))
            mapping = dict(global_mapping)
            mapping.update(aliases(nodes))
            literals = strings(fn)
            bn = ast.Module(body=fn.body, type_ignores=[])
            body_nodes, body_literals = list(ast.walk(bn)), strings(bn)
            paths = [n for n in literals if PATH.match(n.value)]
            ev = r['evidence']
            for n in paths:
                if '\n' in n.value or '\r' in n.value or '\x00' in n.value:
                    r['unresolved'].append({'kind': 'non-path-shaped-literal', 'literal': n.value, 'line': n.lineno})
                    continue
                try:
                    exists = (repo / n.value).exists()
                except OSError as exc:
                    error(repo / file, exc)
                    r['unresolved'].append({'kind': 'path-stat-failed', 'literal': n.value, 'line': n.lineno})
                    continue
                if not exists:
                    ev['A'].append({'kind': 'path-missing', 'literal': n.value, 'line': n.lineno, 'checked_path': str(repo / n.value)})
                    for call in (v for v in nodes if isinstance(v, ast.Call) and resolve(v.func, mapping).startswith('subprocess.')):
                        if any(s is n for s in strings(call)):
                            ev['A'].append({'kind': 'subprocess-path-missing', 'literal': n.value, 'line': n.lineno, 'call_line': call.lineno, 'callee': resolve(call.func, mapping)})
            for n in imports + nodes:
                modules = []
                if isinstance(n, ast.Import):
                    modules = [a.name for a in n.names]
                elif isinstance(n, ast.ImportFrom):
                    if n.level:
                        package = file[:-3].split('/')[:-n.level]
                        modules = ['.'.join(package + ([n.module] if n.module else []))]
                    elif n.module:
                        modules = [n.module]
                elif isinstance(n, ast.Call) and resolve(n.func, mapping) in ('importlib.import_module', 'pytest.importorskip') and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
                    modules = [n.args[0].value]
                for module in modules:
                    if module.split('.')[0] in ('orchestrator', 'tools', 'hooks') and not module_exists(module):
                        ev['A'].append({'kind': 'module-missing', 'module': module, 'line': n.lineno, 'scope': 'module' if n in imports else 'function'})
            cli_paths = sorted({n.value for n in paths if re.fullmatch(r'tools/.*\.py|orchestrator/(?:.*/)?cli[^/]*\.py', n.value)})
            for n in literals:
                if n.value.startswith('--'):
                    available = []
                    for cli in cli_paths:
                        if cli not in source_cache:
                            source_cache[cli] = read(repo / cli) if (repo / cli).is_file() else None
                        if source_cache[cli] is not None:
                            available.append(cli)
                    if not available:
                        r['unresolved'].append({'kind': 'flag-source-unresolved', 'literal': n.value, 'line': n.lineno, 'referenced_sources': cli_paths})
                    elif all(n.value not in source_cache[c] for c in available):
                        ev['A'].append({'kind': 'flag-missing', 'literal': n.value, 'line': n.lineno, 'checked_sources': available})
                for heading in n.value.splitlines():
                    if re.match(r'^## (?:D\d+|DW-[A-Z]\d+)|^### ', heading) and heading not in all_docs:
                        ev['A'].append({'kind': 'docs-heading-missing', 'literal': heading, 'line': n.lineno, 'searched': 'docs/**/*.md'})
            b = body(fn)
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Call) and resolve(b[0].value.func, mapping) in ('pytest.skip', 'pytest.mark.skip', 'pytest.mark.xfail'):
                r['always_skipped'].append({'kind': 'leading-skip-or-mark', 'callee': resolve(b[0].value.func, mapping), 'line': b[0].lineno, 'note': 'A bare mark call does not itself skip execution; inspect semantics.'})
            for d in fn.decorator_list:
                name = resolve(d.func if isinstance(d, ast.Call) else d, mapping)
                if name in ('pytest.mark.skip', 'pytest.mark.xfail'):
                    if name.endswith('xfail') and isinstance(d, ast.Call):
                        conditions = list(d.args) + [k.value for k in d.keywords if k.arg == 'condition']
                        try:
                            if not all(bool(ast.literal_eval(c)) for c in conditions):
                                continue
                        except (ValueError, TypeError):
                            r['unresolved'].append({'kind': 'conditional-xfail', 'line': d.lineno})
                            continue
                    r['always_skipped'].append({'kind': name, 'line': d.lineno, 'note': 'xfail may execute unless run=False'})
            dup, unknown = parameters(fn, mapping)
            ev['B'].extend(dup)
            r['unresolved'].extend(unknown)
            refs = collections.defaultdict(list)
            for n in literals:
                for ref in set(REF.findall(n.value)):
                    refs[ref].append(n.lineno)
            for lineno in range(start, fn.end_lineno + 1):
                if '#' in lines[lineno - 1]:
                    for ref in set(REF.findall(lines[lineno - 1].split('#', 1)[1])):
                        refs[ref].append(lineno)
            r['decision_references'] = {ref: sorted(set(loc)) for ref, loc in sorted(refs.items())}
            for ref in sorted(refs.keys() & withdrawn.keys()):
                ev['C'].append({'kind': 'withdrawn-reference', 'reference': ref, 'test_lines': sorted(set(refs[ref])), 'grounds': withdrawn[ref]})
            calls = [n for n in body_nodes if isinstance(n, ast.Call)]
            prod_calls = [resolve(n.func, mapping) for n in calls if resolve(n.func, mapping).startswith(('orchestrator.', 'tools.'))]
            doc_paths = [{'literal': n.value, 'line': n.lineno} for n in body_literals if n.value.startswith('docs/') or '.md' in n.value]
            signals = sorted({dotted(n.func) for n in calls if dotted(n.func).split('.')[-1] in ('read_text', 'read_bytes', 'sha256') or 'hashlib' in resolve(n.func, mapping)})
            signals.extend(sorted({resolve(n, mapping) for n in body_nodes if isinstance(n, (ast.Name, ast.Attribute)) and (resolve(n, mapping).startswith('hashlib') or dotted(n).split('.')[-1] in ('read_text', 'read_bytes', 'sha256'))}))
            if any(isinstance(n, ast.Compare) and any(isinstance(op, ast.Eq) for op in n.ops) for n in body_nodes):
                signals.append('direct-equality')
            if any(re.fullmatch(r'[0-9a-fA-F]{64}', n.value) for n in body_literals):
                signals.append('64-hex-literal')
            if doc_paths and signals and not prod_calls:
                ev['D'].append({'kind': 'docs-pin', 'pin_targets': doc_paths, 'signals': signals, 'production_call_count': 0})
            constants = []
            only_asserts = bool(b) and all(isinstance(n, (ast.Assert, ast.Import, ast.ImportFrom, ast.Pass)) for n in b)
            for stmt in b:
                if not isinstance(stmt, ast.Assert):
                    continue
                comp = stmt.test
                if not isinstance(comp, ast.Compare) or len(comp.ops) != 1 or not isinstance(comp.ops[0], ast.Eq):
                    only_asserts = False
                    continue
                found = False
                for attr, val in ((comp.left, comp.comparators[0]), (comp.comparators[0], comp.left)):
                    if isinstance(attr, ast.Attribute) and attr.attr.isupper() and resolve(attr, mapping).startswith(('orchestrator.', 'tools.')):
                        try:
                            value = ast.literal_eval(val)
                        except (ValueError, TypeError):
                            continue
                        constants.append({'constant': resolve(attr, mapping), 'literal_repr': repr(value), 'line': stmt.lineno})
                        found = True
                only_asserts = only_asserts and found
            if constants and only_asserts and not calls:
                ev['D'].append({'kind': 'derived-value-pin', 'pin_targets': constants})
            ev['A'], r['suppressed'] = suppress_synthetic(fn, mapping, ev['A'])
            r['notes'] = []
            r['production_targets'] = production_targets(repo, file, imports, fn)
            records.append(r)
            groups[fingerprint(fn)].append(r)
            body_groups[fingerprint(fn, decorators=False)].append((fingerprint(fn), r))

    files = sorted((repo / 'orchestrator/tests').glob('test_*.py'))
    for path in files:
        file = path.relative_to(repo).as_posix()
        source = read(path)
        mode = 'excluded' if path.name in excluded else 'included'
        counts[mode + '_files'] += 1
        counts[mode + '_file_lines'] += len(source.splitlines()) if source is not None else 0
        if source is None:
            continue
        tree = parse(path, source)
        if tree is None:
            continue
        try:
            index(strings(tree), file, 'referenced-by-test')
            if path.name == 'test_real_repo_serialization.py':
                for names, value in assignments(tree):
                    if value is not None and any(n.endswith('_GOLDEN') for n in names):
                        index(strings(value), file, 'real-repo-golden')
            if mode == 'included':
                analyze(file, source, tree)
        except Exception as exc:
            error(path, exc)
    for digest, peers in groups.items():
        if len(peers) > 1:
            ids = [r['nodeid_base'] for r in peers]
            for r in peers:
                r['evidence']['B'].append({'kind': 'identical-body-and-decorators', 'group_id': digest, 'peers': [i for i in ids if i != r['nodeid_base']]})
    for digest, peers in body_groups.items():
        for full_digest, r in peers:
            ids = [p['nodeid_base'] for d, p in peers if d != full_digest]
            if ids:
                r['notes'].append({'kind': 'identical-body-only', 'group_id': digest, 'peers': ids})
    for r in records:
        keys = {r['nodeid_base'].removeprefix('orchestrator/tests/'), pathlib.Path(r['file']).name + '::' + r['qualname'].split('::')[-1]}
        for key in sorted(keys):
            for item in protections.get(key, []):
                if item['reason'] == 'referenced-by-test':
                    if item['file'] == r['file']:
                        continue
                    if item not in r['referenced_by']:
                        r['referenced_by'].append(item)
                if item not in r['protected']:
                    r['protected'].append(item)
        for item in prefixes:
            if r['nodeid_base'].startswith(item['prefix']) or any(n.startswith(item['prefix']) for n in r['nodeids']):
                r['protected'].append(dict(item, reason='add-only-frozen-suite'))
        r['categories'] = [c for c in 'ABCD' if r['evidence'][c]]
    matched = {r['nodeid_base'] for r in records}
    unmatched = {k: len(v) for k, v in collected.items() if k not in matched and pathlib.Path(k.split('::')[0]).name not in excluded}
    summary = dict(counts, discovered_files=len(files), aggregation_basis='Each category sums each matching function once (categories overlap); lines include decorators through end_lineno; nodeids count collect-file entries; seconds sum ledger lookup per entry with missing=0; file lines are whole-file splitlines counts.', totals=metrics(records), protected=metrics([r for r in records if r['protected']]), categories={c: {'including_protected': metrics([r for r in records if c in r['categories']]), 'excluding_protected': metrics([r for r in records if c in r['categories'] and not r['protected']])} for c in 'ABCD'}, always_skipped_functions=sum(bool(r['always_skipped']) for r in records), unresolved_evidence_count=sum(len(r['unresolved']) for r in records), unevaluable_parametrize_rows=sum(e['kind'] == 'unevaluable-parametrize-row' for r in records for e in r['unresolved']), unevaluable_parametrize_containers=sum(e['kind'] == 'unevaluable-parametrize-container' for r in records for e in r['unresolved']), collect_entries=sum(map(len, collected.values())), unmatched_collect_functions=unmatched, errors=errors)
    summary['suppressed_functions'] = sum(bool(r['suppressed']) for r in records)
    summary['suppressed_evidence_count'] = sum(len(r['suppressed']) for r in records)
    summary['suppressed_by_kind'] = dict(sorted(collections.Counter(e['kind'] for r in records for e in r['suppressed']).items()))
    summary['unresolved_by_kind'] = dict(sorted(collections.Counter(e['kind'] for r in records for e in r['unresolved']).items()))
    summary['abc_production_targets_excluding_protected'] = dict(sorted(collections.Counter(t for r in records if not r['protected'] and set(r['categories']) & set('ABC') for t in r['production_targets']).items()))
    summary['abc_without_production_targets_excluding_protected'] = sum(not r['production_targets'] for r in records if not r['protected'] and set(r['categories']) & set('ABC'))
    summary['aggregation_basis'] += ' Suppression counts evidence entries and affected functions; production target counts each unprotected A/B/C function once per target (targets overlap); empty targets counted separately.'
    return {'schema_version': 1, 'inputs': {'repo_root': str(repo), 'collect_file': str(collect_file), 'exclude_file': str(exclude_file), 'collect_sha256': hashlib.sha256(pathlib.Path(collect_file).read_bytes()).hexdigest(), 'exclude_sha256': hashlib.sha256(pathlib.Path(exclude_file).read_bytes()).hexdigest(), 'ledger_sha256': hashlib.sha256(ledger_path.read_bytes()).hexdigest() if ledger_path.is_file() else None}, 'summary': summary, 'records': records}


def markdown(data):
    s = data['summary']
    out = ['# Static test inventory', '', '判定は仮説。削除確定には意味確認と変異検査が必要。分類間は重複する。', '', s['aggregation_basis'], '', f"対象 {s['included_files']} files / {s['included_file_lines']} file lines; 除外 {s['excluded_files']} files / {s['excluded_file_lines']} lines.", '', '|範囲|関数|行|nodeids|台帳秒|台帳欠落 nodeids|', '|---|---:|---:|---:|---:|---:|']
    def row(label, m):
        out.append(f"|{label}|{m['functions']}|{m['lines']}|{m['nodeids']}|{m['duration_seconds']:.6f}|{m['missing_duration_nodeids']}|")
    row('全対象', s['totals'])
    row('protected', s['protected'])
    for c in 'ABCD':
        for mode, m in s['categories'][c].items():
            row(c + ' ' + mode, m)
    for c in 'ABCD':
        out.extend(['', f'## {c}: 台帳秒上位30件（protected含む）', '', '|関数|行|nodeids|台帳秒|protected|証拠種別|', '|---|---:|---:|---:|---:|---|'])
        candidates = sorted((r for r in data['records'] if c in r['categories']), key=lambda r: (-r['duration_seconds'], r['nodeid_base']))[:30]
        for r in candidates:
            kinds = ', '.join(sorted({e['kind'] for e in r['evidence'][c]}))
            out.append(f"|{r['nodeid_base']}:{r['start_line']}|{r['line_count']}|{r['nodeid_count']}|{r['duration_seconds']:.6f}|{bool(r['protected'])}|{kinds}|")
    def cell(value):
        return str(value).replace('|', '&#124;').replace('\n', '<br>').replace('\r', '')
    groups = collections.defaultdict(list)
    pins = collections.defaultdict(list)
    for r in data['records']:
        for e in r['evidence']['B']:
            if e['kind'] == 'identical-body-and-decorators':
                groups[e['group_id']].append(r)
        for target in {p.get('literal', p.get('constant')) for e in r['evidence']['D'] for p in e['pin_targets']}:
            pins[target].append(r)
    for group, members in sorted(groups.items()):
        out.extend(['', f'## B1 group {group}', '', '|file:line qualname|protected|referenced_by|台帳秒|', '|---|---|---|---:|'])
        for r in members:
            out.append(f"|{cell(r['file'])}:{r['start_line']} {cell(r['qualname'])}|{bool(r['protected'])}|{bool(r['referenced_by'])}|{r['duration_seconds']:.6f}|")
    out.extend(['', '## B2 重複 row 全件', '', '|file:decorator 行 / 関数|row位置 (0-based)|一致するrow|値 repr|', '|---|---:|---|---|'])
    for r in data['records']:
        for e in r['evidence']['B']:
            if e['kind'] == 'duplicate-parametrize-row':
                out.append(f"|{cell(r['file'])}:{e['decorator_line']} {cell(r['qualname'])}|{e['row_index_0based']}|{e['equal_to_rows_0based']}|{cell(e['value_repr'])}|")
    out.extend(['', '## C 全件', '', '|関数|参照|根拠|protected|台帳秒|', '|---|---|---|---|---:|'])
    for r in data['records']:
        for e in r['evidence']['C']:
            grounds = '; '.join(f"{g['file']}:{g['line']} {g['text']}" for g in e['grounds'])
            out.append(f"|{cell(r['nodeid_base'])}:{r['start_line']}|{e['reference']}|{cell(grounds)}|{bool(r['protected'])}|{r['duration_seconds']:.6f}|")
    out.extend(['', '## D pin先別 上位30件（台帳秒順）', '', '各pin先で関数を一度集計。複数pin先を持つ関数は表の行間で重複する。', '', '|pin先|関数|行|台帳秒|', '|---|---:|---:|---:|'])
    for target, members in sorted(pins.items(), key=lambda item: (-sum(r['duration_seconds'] for r in item[1]), item[0]))[:30]:
        m = metrics(members)
        out.append(f"|{cell(target)}|{m['functions']}|{m['lines']}|{m['duration_seconds']:.6f}|")
    out.extend(['', '## 抑制・未解決の内訳', '', f"synthetic-fixture: {s['suppressed_functions']} functions / {s['suppressed_evidence_count']} evidence entries", '', '```json', json.dumps({k: s[k] for k in ('suppressed_by_kind', 'unresolved_by_kind', 'abc_production_targets_excluding_protected', 'abc_without_production_targets_excluding_protected')}, ensure_ascii=False, indent=2), '```'])
    out.extend(['', '## 別枠・errors', '', f"always-skipped: {s['always_skipped_functions']}; unresolved evidence: {s['unresolved_evidence_count']}; unevaluable rows: {s['unevaluable_parametrize_rows']}; unevaluable containers: {s['unevaluable_parametrize_containers']}; unmatched collect functions: {len(s['unmatched_collect_functions'])}; errors: {len(s['errors'])}.", '', '```json', json.dumps(s['errors'], ensure_ascii=False, indent=2), '```', '', '## 限界', '', '動的 import・path 組立・fixture/helper 経由・継承 test・再代入 alias は追跡しない。from-import の属性/関数の存在は検査しない。本文・decorator AST同一でも global binding/fixture/class・module mark は異なり得る。合成指標は関数単位の保守的抑制で真の不在も落とし得る。module-missing は抑制対象外。production_targets は直下importと本文の名前参照のみで、shadowing・helper経由は追跡しない。parametrize の非literal容器は行数不明。保護参照は literal 内の file.py::function 形を保守的に関数単位へ広げる。class/module の skip mark は追跡しない。撤回参照は指定見出しと取り消し線の直接参照だけ。docs-pin は静的特徴の共起であり意味を保証しない。', ''])
    return '\n'.join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('repo-root', 'collect-file', 'exclude-file', 'out-json', 'out-md'):
        parser.add_argument('--' + name, required=True, type=pathlib.Path)
    args = parser.parse_args()
    data = scan(args.repo_root, args.collect_file, args.exclude_file)
    for path in (args.out_json, args.out_md):
        path.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    args.out_md.write_text(markdown(data), encoding='utf-8')
    print(json.dumps(data['summary'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
```
