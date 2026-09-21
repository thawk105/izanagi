# read-only probe の逐語 (Codex author + fix1 が書き、親が login で実行した)

- 実行 file: `dev-wave-jobs/dev-wave-t2812-old-series-realignment/probe/t2812_old_series_probe.py` (repo 外)
- sha256 (probe-2 を実行した版): 6e280172f42149a00b584f02183be534322d7934d8eafb152793199d506117a2
- 初版 (probe-1 を実行した版) の sha256: db193956e44167a154e022693d9ed32f6d691a85bff4679c8ff3e8d3194055f6
- 逐語を `.py` でなく `.md` に貼るのは AI provenance 規約 (実装面は Codex author が書く / probe を repo へ入れない) に従うため

```python
#!/usr/bin/env python3
"""T2812 read-only probe. Only --out is created; no production writes.

Each nested cell has its own outcome envelope. Outer ok also reflects nested
validator failures; the result retains their full individual exceptions.
Output is reserved before baseline status so its creation is accounted for.
"""
import argparse
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True
P = 'orchestrator.campaign.'
STUDY = 'paper-story-a1-20260901-balanced5-sized-v1'


def observe(id_, target, call, fn):
    start = time.monotonic()
    row = dict(id=id_, target=str(target), call=call)
    try:
        value = fn()
        row.update(ok=True, result=value)
        if isinstance(value, dict):
            row['ok'] = all(c['ok'] for c in value.get('checks', []))
            if 'unchanged' in value:
                row['ok'] = row['ok'] and value['unchanged']
    except Exception as exc:
        detail = dict(type=type(exc).__name__, message=str(exc))
        for key in ('reason', 'cause'):
            if hasattr(exc, key):
                detail[key] = getattr(exc, key)
        row.update(ok=False, error=detail)
    row['elapsed_s'] = time.monotonic() - start
    return row


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True,
                          capture_output=True, text=True).stdout.rstrip('\n')


def snapshot(roots):
    result = {}
    for name, root in roots.items():
        result[name] = {}
        for label, target, argv in (
                ('status', root, ('status', '--porcelain=v1', '--untracked-files=all', '--ignore-submodules=none')),
                ('submodule_head', root / 'external/ccbench', ('rev-parse', 'HEAD'))):
            result[name][label] = observe(label, target, ['git', *argv],
                                         lambda: git(target, *argv))
    return result


def stable(value):
    if isinstance(value, dict):
        return {k: stable(v) for k, v in value.items() if k != 'elapsed_s'}
    return value


def compare(old, new):
    return {k: dict(recorded=old.get(k), current=new.get(k),
                    equal=k in old and k in new and old[k] == new[k])
            for k in sorted(set(old) | set(new))}


def policies(value, location='$', depth=0):
    if depth > 100:
        raise ValueError('embedded JSON nesting exceeds 100')
    if isinstance(value, str) and 'repo_stock_pin' in value:
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return
        yield from policies(decoded, location + ':json', depth + 1)
    elif isinstance(value, dict):
        search = value.get('search_config')
        if isinstance(search, dict) and isinstance(search.get('build_admission'), dict):
            yield location + '.search_config.build_admission', search['build_admission']
        for k, v in value.items():
            yield from policies(v, location + '.' + k, depth + 1)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from policies(v, location + '[' + str(i) + ']', depth + 1)


def receipt_summary(record):
    receipt = record['admission_receipt']
    body = receipt['admission']
    return {'class': body['class'], 'policy_sha256': body['policy_sha256'],
            'source.ccbench_commit': body['source']['ccbench_commit'],
            'source.src_token': body['source']['src_token'],
            'subject.contract_sha256': receipt['subject']['contract_sha256']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('repo-root', 'route-h-root', 'b4-w1-root', 'k2-pair-lock', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if os.path.lexists(args.out):
        print('output already exists: ' + str(args.out), file=sys.stderr)
        return 2
    try:
        output = args.out.open('x', encoding='utf-8')
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    os.environ['GIT_OPTIONAL_LOCKS'] = '0'
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    root = args.repo_root.resolve()
    roots = dict(new=root, route_h=args.route_h_root.resolve(), b4_w1=args.b4_w1_root.resolve())
    sys.path.insert(0, str(root))
    before = snapshot(roots)
    store = root / 'output/env/pegasus/binaries'
    store_before = store.exists()
    rows, cache = [], {}

    def mod(name):
        module = importlib.import_module(P + name)
        Path(module.__file__).resolve().relative_to(root)
        return module

    def policy():
        return mod('build_admission').resolve_current_build_admission_policy()

    def add(id_, target, call, fn):
        row = observe(id_, target, call, fn)
        rows.append(row)
        return row

    def ratified():
        if 'ratified' not in cache:
            cache['ratified'] = mod('s8b_ratified_freeze').load_ratified_freeze(root)
        return cache['ratified']

    def g1():
        if 'g1' in cache:
            return cache['g1']
        rf, rat = mod('s8b_ratified_freeze'), ratified()
        head = rf._capture_head(root)
        if head != rat.activation_head:
            raise RuntimeError('activation HEAD moved')
        pp, psha = rf._source_record_path_sha(rat.document, 'floor_protocol')
        rp, _ = rf._source_record_path_sha(rat.document, 'floor_source')
        rf._parse_official_run_path(rp, expected_basename='result.json')
        # _launch_validate has no separate role-path helper: use its exact
        # resolution expression and production basename mapping.
        run_dir = rp.rsplit('/', 1)[0]
        mp = f"{run_dir}/{rf._RUN_BASENAMES['manifest']}"
        captured = {}
        for label, path in (('floor_protocol', pp), ('manifest', mp)):
            rf._assert_canonical_relative_path(path, reason='floor-artifact-invalid', label=label)
            captured[label], _ = rf._capture_g_h_worktree(
                generation_commit=rat.generation_commit, validation_head=head, path=path, root=root)
        if rf._sha256_hex(captured['floor_protocol']) != psha:
            raise RuntimeError('protocol generation record hash mismatch')
        protocol, _ = rf._validate_published_protocol(
            rf._strict_load(captured['floor_protocol'], what='floor_protocol'),
            contract_resolver=rf._resolve_current_contract_sha256)
        manifest = rf._strict_load(captured['manifest'], what='manifest')
        cells = rf._floor_contract.enumerate_cells(
            rat.document, stock_configuration=protocol['stock_configuration'])
        cache['g1'] = protocol, manifest, {c['cell_id']: c for c in cells}, pp, mp
        return cache['g1']

    def kwargs(cid, rec, protocol, cells):
        cell = cells[cid]
        return dict(expected_ccbench_pin=protocol['ccbench_pin'],
                    expected_contract_sha256=protocol['contract_sha256'], expected_cell_id=cid,
                    expected_holdout_id=cell['holdout_id'], expected_configuration_id=cell['configuration_id'],
                    expected_entry_sha256=rec['binding']['entry_sha256'],
                    expected_binding_sha256=rec['binding']['binding_sha256'])

    bp = root / 'output/insights/2026-09-16/t2636-b4-binary-record/records/rr20--stock_common.json'

    def b4():
        if 'b4' not in cache:
            cache['b4'] = json.loads(bp.read_text())
        return cache['b4']

    def pinned(target, source=False):
        pin = (mod('paper_story_a1_source').load_contract(root, STUDY)['canonical_head']
               if source else mod('p3_s4_loop').PIN)
        mod('patchharness').assert_pinned_clean(str(target / 'external/ccbench'), pin)
        return {'pin': pin}

    for label, target in (('NEW', root), ('H', roots['route_h'])):
        add('K2-PIN-' + label, target, P + 'patchharness.assert_pinned_clean(sub, p3_s4_loop.PIN)',
            lambda: pinned(target))
    add('POLICY-CURRENT', root, P + 'build_admission.resolve_current_build_admission_policy()',
        lambda: dict(sha256=policy().sha256, preimage=policy().as_preimage(),
                     CURRENT_PIN=mod('pin').CURRENT_PIN, CCBENCH_FULL_SHA=mod('s8b_approved').CCBENCH_FULL_SHA,
                     K2_PIN=mod('p3_s4_loop').PIN, A1_PIN=mod('paper_story_a1_paired').CANONICAL_CCBENCH_OID))

    def pair_lock():
        codec = mod('campaign_lock')
        text = args.k2_pair_lock.read_text()
        decoded = None
        rejected = False
        def current():
            nonlocal decoded, rejected
            try:
                decoded = codec.decode_campaign_lock(text)
            except codec.CampaignLockCodecError:
                rejected = True
                raise
            return {'readable': True}
        current_codec = observe('current_codec', args.k2_pair_lock,
                                P + 'campaign_lock.decode_campaign_lock(text)', current)
        result = dict(current_codec=current_codec,
                      historical_codec={'attempted': False}, checks=[current_codec])
        if rejected:
            def historical():
                nonlocal decoded
                decoded = codec.decode_historical_campaign_lock(text)
                return {'readable': True}
            historical_codec = observe('historical_codec', args.k2_pair_lock,
                P + 'campaign_lock.decode_historical_campaign_lock(text)', historical)
            result['historical_codec'] = historical_codec
            result['checks'].append(historical_codec)
        if decoded is None:
            return result
        identity = json.loads(decoded.identity_preimage)
        old = identity['search_config'][mod('ident').ADMISSION_POLICY_SEARCH_KEY]
        cache['k2_preimage'] = old
        result.update(ccbench_commit=identity['ccbench_commit'], preimage=old,
                      comparison=compare(old, policy().as_preimage()))
        return result
    add('K2-LOCK-PAIR', args.k2_pair_lock, P + 'campaign_lock.decode_campaign_lock(text)', pair_lock)
    for label, target in (('NEW', root), ('H', roots['route_h'])):
        def boundary():
            a1 = mod('paper_story_a1_paired')
            body, sha = a1._load_policy_for_study(STUDY)
            a1._assert_ccbench_acceptance(target, body, boundary='login-submit')
            return {'policy_sha256': sha}
        add('A1-BOUNDARY-' + label, target, P + "paper_story_a1_paired._load_policy_for_study(STUDY); " + P + "paper_story_a1_paired._assert_ccbench_acceptance(root, policy, boundary='login-submit')", boundary)
    for label, target in (('NEW', root), ('H', roots['route_h'])):
        add('A1-SOURCE-' + label, target, P + 'paper_story_a1_source.load_contract(repo_root, STUDY); ' + P + 'patchharness.assert_pinned_clean(sub, canonical_head)', lambda: pinned(target, True))

    def identities():
        base = root / 'output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002'
        matches, checks = [], []
        cache['a1_preimages'] = []
        for path in sorted(base.rglob('*')):
            if not path.is_file() or (path.suffix != '.json' and path.name != 'campaign.lock'):
                continue
            def scan():
                for location, old in policies(json.loads(path.read_text())):
                    cache['a1_preimages'].append(dict(path=str(path), location=location, preimage=old))
                    matches.append(dict(path=str(path), location=location, repo_stock_pin=old.get('repo_stock_pin'),
                                        comparison=compare(old, policy().as_preimage())))
                return None
            checks.append(observe(path.name, path, 'json.loads (including embedded JSON)', scan))
        return dict(state='found' if matches else '不在', matches=matches, checks=checks)
    add('A1-IDENTITY', root, 'recursive JSON identity search', identities)
    add('G1-LOAD', root, P + 's8b_ratified_freeze.load_ratified_freeze(root)',
        lambda: {k: getattr(ratified(), k) for k in ('generation_number', 'sha256', 'generation_commit')})
    add('G1-LAUNCH', root, P + 's8b_ratified_freeze.launch_validate(ratified, root)',
        lambda: {'type': type(mod('s8b_ratified_freeze').launch_validate(ratified(), root)).__name__})

    def binaries():
        p, manifest, cells, pp, mp = g1()
        return dict(protocol_path=pp, manifest_path=mp,
                    protocol={k: p[k] for k in ('ccbench_pin', 'contract_sha256')},
                    cells=[dict(cell_id=cid, **receipt_summary(rec), validation_kwargs=kwargs(cid, rec, p, cells))
                           for cid, rec in manifest['binaries'].items()])
    add('G1-BINARIES', root, P + 's8b_ratified_freeze._source_record_path_sha; _capture_g_h_worktree; _strict_load; _validate_published_protocol(contract_resolver=_resolve_current_contract_sha256)', binaries)

    def validate(rec, current, options):
        mod('s8b_binary_admission').validate_portable_binary_record(
            rec, expected_policy=policy() if current else None, **options)
        return receipt_summary(rec)

    for id_, current in (('G1-BIN-HIST', False), ('G1-BIN-CURRENT', True)):
        def validate_cells():
            p, manifest, cells, _, mp = g1()
            checks = []
            for cid, rec in manifest['binaries'].items():
                options = kwargs(cid, rec, p, cells)
                checks.append(observe(cid, mp, dict(function=P + 's8b_binary_admission.validate_portable_binary_record',
                                                    expected_policy='current' if current else None, **options),
                                      lambda: validate(rec, current, options)))
            return {'checks': checks}
        add(id_, root, P + 's8b_binary_admission.validate_portable_binary_record (stage 4 kwargs)', validate_cells)

    def protocols():
        floor = mod('s8b_floor_campaign')
        checked = observe('resolve', root, P + 's8b_floor_campaign.resolve_current_floor_protocol(root=root)',
                          lambda: {'path': floor.resolve_current_floor_protocol(root=root).path})
        def index():
            head = git(root, 'rev-parse', 'HEAD')
            records = floor._scan_floor_protocol_index_at_commit(root=root, commit_oid=head)
            return dict(head=head, gitlink=floor._ccbench_gitlink(root, head),
                        records=[dict(path=r.path, env_tag=r.document['env_tag'], contract_sha256=r.contract_sha256,
                                      ccbench_pin=r.ccbench_pin) for r in records.values()],
                        current_contracts={r.document['env_tag']: mod('env_contract').lookup(r.document['env_tag']).contract_sha256
                                           for r in records.values()})
        return {'checks': [checked, observe('index', root, P + 's8b_floor_campaign._scan_floor_protocol_index_at_commit(root=root, commit_oid=HEAD); _ccbench_gitlink; env_contract.lookup', index)]}
    add('B4-PROTOCOL', root, P + 's8b_floor_campaign.resolve_current_floor_protocol(root=root)', protocols)
    for id_, current in (('B4-RECORD-HIST', False), ('B4-RECORD-CURRENT', True)):
        add(id_, bp, P + 's8b_binary_admission.validate_portable_binary_record',
            lambda: dict(receipt=receipt_summary(b4()), checks=[observe('record', bp,
                dict(function=P + 's8b_binary_admission.validate_portable_binary_record', expected_policy='current' if current else None),
                lambda: validate(b4(), current, {}))]))

    def w1():
        tree = roots['b4_w1']
        paths = sorted((tree / 'output/env/pegasus/floor-pair/t2288-f1').glob('window__*-c1.jsonl'))
        new, old = git(root, 'rev-parse', 'HEAD'), git(tree, 'rev-parse', 'HEAD')
        def first(path):
            with path.open() as stream:
                loaded = json.loads(stream.readline())['loaded_head']
            return dict(loaded_head=loaded, equals_new_head=loaded == new, equals_b4_w1_head=loaded == old)
        checks = [observe(p.name, p, 'json.loads(stream.readline())[loaded_head]', lambda: first(p)) for p in paths]
        if len(paths) != 3:
            raise ValueError(f'expected 3 w1 JSONL files, found {len(paths)}')
        return dict(new_head=new, b4_w1_head=old, checks=checks)
    add('B4-W1-HEAD', roots['b4_w1'], 'git rev-parse HEAD; JSONL first line only', w1)

    def readmit():
        records, checks = [], []
        def collect_g1():
            _, manifest, _, _, mp = g1()
            records.extend((mp + ':' + cid, rec) for cid, rec in manifest['binaries'].items())
        def collect_b4():
            records.append((str(bp), b4()))
        checks.append(observe('collect-g1', root, 'captured manifest', collect_g1))
        checks.append(observe('collect-b4', bp, 'record JSON read', collect_b4))
        for target, rec in records:
            def admission():
                body = rec['admission_receipt']['admission']
                current_policy = policy().as_preimage()
                if body['class'] != 'stock-baseline':
                    return {'class': body['class'], **{key: dict(recorded=body.get(key), registered=body.get(key) in current_policy[registry])
                        for key, registry in (('generator_id', 'generator_registry'), ('review_id', 'review_registry'))}}
                source, ba = body['source'], mod('build_admission')
                predicate = dict(src_token_is_STOCK=source['src_token'] == ba.STOCK,
                                 tracked_clean_is_True=source['tracked_clean'] is True,
                                 ccbench_commit_is_CURRENT_PIN=source['ccbench_commit'] == mod('pin').CURRENT_PIN)
                def derive():
                    evidence = mod('source_digest').SourceEvidence.from_receipt(source)
                    context = ba.build_run_context(generator_id=ba.GeneratorId.BACKOFF_OVERTHROTTLE)
                    return {'class': ba.derive_build_admission(context, evidence).provenance.value}
                return dict(predicate=predicate, stock_baseline=all(predicate.values()), checks=[observe(
                    'derive', target, P + 'build_admission.derive_build_admission(build_run_context(generator_id=GeneratorId.BACKOFF_OVERTHROTTLE), SourceEvidence.from_receipt(recorded_source))', derive)])
            checks.append(observe(rec.get('cell_id', 'record'), target, 'stock predicate + derive, otherwise registry membership only', admission))
        return {'checks': checks}
    add('READMIT-STOCK', root, P + 'build_admission.derive_build_admission; source_digest.SourceEvidence.from_receipt', readmit)

    def series_pin():
        ba, current = mod('build_admission'), policy()
        protocol, manifest, _, _, _ = g1()
        receipts = {cid: rec['admission_receipt']['admission']['policy_sha256']
                    for cid, rec in manifest['binaries'].items()}
        if len(receipts) != 12:
            raise ValueError(f'expected 12 g1 receipts, found {len(receipts)}')
        g1_shas = sorted(set(receipts.values()))
        b4_sha = b4()['admission_receipt']['admission']['policy_sha256']
        a1_preimages = cache['a1_preimages']
        k2_preimage = cache['k2_preimage']
        current_pin = mod('pin').CURRENT_PIN
        current_full = mod('s8b_approved').CCBENCH_FULL_SHA
        if current_full[:7] != current_pin:
            raise ValueError('CURRENT_PIN differs from CCBENCH_FULL_SHA prefix')
        checks = []
        for source, full in (
                ('g1.protocol.ccbench_pin', protocol['ccbench_pin']),
                ('p3_s4_loop.PIN', mod('p3_s4_loop').PIN),
                ('paper_story_a1_paired.CANONICAL_CCBENCH_OID', mod('paper_story_a1_paired').CANONICAL_CCBENCH_OID),
                ('pin.CURRENT_PIN', current_full)):
            def rebuild():
                if (type(full) is not str or len(full) != 40
                        or any(c not in '0123456789abcdef' for c in full)):
                    raise ValueError(f'{source} requires a 40-digit lowercase OID')
                preimage = dict(current.as_preimage())
                preimage['repo_stock_pin'] = full[:7]
                rebuilt = ba.decode_historical_build_admission_policy(preimage)
                preimage = rebuilt.as_preimage()
                comparison = dict(
                    g1_policy_sha256s={sha: rebuilt.sha256 == sha for sha in g1_shas},
                    g1_policy_sha256_set_equal=set(g1_shas) == {rebuilt.sha256},
                    b4_policy_sha256_equal=rebuilt.sha256 == b4_sha,
                    a1_preimages=[dict(path=item['path'], location=item['location'],
                                       equal=preimage == item['preimage']) for item in a1_preimages],
                    k2_preimage_equal=preimage == k2_preimage,
                    current_policy_sha256_equal=rebuilt.sha256 == current.sha256)
                result = dict(pin_full=full, pin_short=full[:7], preimage=preimage,
                              sha256=rebuilt.sha256, comparison=comparison)
                if source == 'pin.CURRENT_PIN':
                    result['checks'] = [dict(id='current-policy-control',
                        ok=comparison['current_policy_sha256_equal'])]
                return result
            checks.append(observe(source, root,
                P + 'build_admission.decode_historical_build_admission_policy(preimage)', rebuild))
        return dict(g1_receipt_policy_sha256s=receipts, g1_policy_sha256s=g1_shas,
                    b4_policy_sha256=b4_sha, current_policy_sha256=current.sha256,
                    a1_preimages_available=bool(a1_preimages), checks=checks)
    add('POLICY-SERIES-PIN', root,
        P + 'build_admission.resolve_current_build_admission_policy().as_preimage(); '
        + P + 'build_admission.decode_historical_build_admission_policy(preimage).sha256', series_pin)

    def readonly():
        after = snapshot(roots)
        available = all(item[key]['ok'] for snap in (before, after) for item in snap.values()
                        for key in ('status', 'submodule_head'))
        return dict(before=before, after=after, observations_available=available,
                    snapshots_equal=stable(before) == stable(after), binary_store_before=store_before,
                    binary_store_after=store.exists(), output_reserved_before_baseline=str(args.out),
                    unchanged=available and stable(before) == stable(after) and store_before == store.exists())
    add('READONLY', roots, 'git status --porcelain=v1 --untracked-files=all --ignore-submodules=none; submodule rev-parse HEAD; Path.exists', readonly)
    with output:
        json.dump(dict(schema='t2812-old-series-probe/v1', checks=rows), output, ensure_ascii=False, indent=2, allow_nan=False)
        output.write('\n')
    for row in rows:
        print(row['id'] + ': ' + ('ok' if row['ok'] else 'err'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
```
