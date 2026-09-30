# 走査器・分類器・索引生成器の逐語 (Codex author 作、repo 外の使い捨て道具)

実装面を repo へ入れないため、source を md の逐語で残す (実行するときは repo 外へ書き出す)。
著者: Codex `gpt-6-sol` reasoning=medium、role=author (段 5 author 1 本 + fix 3 本)。子 branch の終端 commit は
`output-pruning-scan-fix3` (ed832c62ef2ee48f4a45565788259cb04092c49b)。仕様は s1-brief と、親 job dir の
author / fix prompt (本 dir の README §7 に所在)。

使い方 (本 wave の実走):

```text
python3 scan_refs.py --repo <abs> --commit 035fc11fa601547f5d68e54f5661c5daa70b93a5 --out <dir>   # 2,287 秒
python3 classify.py --refs <dir>/refs.jsonl --roots <dir>/roots.jsonl --config classify-config-v4.json --out <dir2>
python3 build_index.py build --repo <abs> --commit <40hex> --classes <classes.jsonl> --prune-list <list> --out output/PRUNED-INDEX.jsonl
python3 build_index.py verify --repo <abs> --base <40hex> --new <40hex> --index output/PRUNED-INDEX.jsonl
```

既知の穴 (次段で直す): README §6 を参照。

## scan_refs.py

```python
#!/usr/bin/env python3
"""Reference scanner for a fixed Git tree."""
import argparse
import fnmatch
import gzip
import hashlib
import io
import json
import os
import posixpath
import re
import subprocess
import time
from collections import Counter, defaultdict

AXES = ('R1', 'R2', 'R3', 'R4', 'R4t', 'R5', 'R5t', 'R7')
TOKEN = re.compile(r'[A-Za-z0-9._~@%+=,:*?\[\]{}/-]+')
SHA = re.compile(r'(?<![A-Za-z0-9])([a-f0-9]{64})(?![A-Za-z0-9])')
BLOB = re.compile(r'(?<![A-Za-z0-9])([a-f0-9]{40})(?![A-Za-z0-9])')
DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def git(repo, *args):
    return subprocess.check_output(['git', '-C', repo, *args])


def tree(repo, commit):
    entries = {}
    for record in git(repo, 'ls-tree', '-r', '-z', '-l', commit).split(b'\0'):
        if not record:
            continue
        header, raw_path = record.split(b'\t', 1)
        mode, kind, oid, size = header.split()
        path = raw_path.decode('utf-8', 'surrogateescape')
        if path in entries:
            raise ValueError('duplicate tree path: ' + path)
        if mode == b'160000':
            continue
        if kind != b'blob' or not size.isdigit():
            raise ValueError('unsupported tree entry: ' + path)
        entries[path] = {'blob': oid.decode(), 'size': int(size)}
    return entries


class Blobs:
    def __init__(self, repo):
        self.proc = subprocess.Popen(['git', '-C', repo, 'cat-file', '--batch'],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def get(self, oid):
        self.proc.stdin.write((oid + '\n').encode())
        self.proc.stdin.flush()
        header = self.proc.stdout.readline().split()
        if len(header) != 3 or header[0] != oid.encode() or header[1] != b'blob':
            raise ValueError('unreadable blob: ' + oid)
        size = int(header[2])
        data = self.proc.stdout.read(size)
        if len(data) != size or self.proc.stdout.read(1) != b'\n':
            raise ValueError('truncated blob: ' + oid)
        return data

    def close(self):
        self.proc.stdin.close()
        self.proc.stdout.close()
        if self.proc.wait():
            raise ValueError('git cat-file failed')


def root_for(path):
    bits = path.split('/')
    return '/'.join(bits[:4] if len(bits) >= 5 and DATE.fullmatch(bits[2]) else bits[:3])


def ancestors(path):
    bits = path.split('/')
    return ['/'.join(bits[:n]) for n in range(3, len(bits))]


def category(source, root):
    if '/tests/' in '/' + source or posixpath.basename(source).startswith('test_'):
        return 'tests'
    if source.startswith('docs/'):
        if re.fullmatch(r'docs/decisions[^/]*\.md', source): return 'docs/decisions'
        if source == 'docs/worklog.md' or re.fullmatch(r'docs/archive/worklog-[^/]*', source): return 'docs/worklog'
        if re.fullmatch(r'docs/failures[^/]*\.md', source): return 'docs/failures'
        if 'paper' in source: return 'docs/paper'
        if source.startswith('docs/spool/'): return 'docs/spool'
        return 'docs/other'
    for prefix, label in [('tools/', 'tools'), ('orchestrator/', 'orchestrator'),
                          ('hooks/', 'hooks'), ('.claude/', 'dotclaude'), ('.codex/', 'dotcodex')]:
        if source.startswith(prefix): return label
    if source.startswith('output/insights/'):
        return 'output-same-root' if root_for(source) == root else 'output-other-insights'
    if source.startswith('output/'): return 'output-non-insights'
    return 'other'


def forms(token, source):
    token = token.rstrip('/')
    full = set()
    for marker in ('output/insights/', 'insights/'):
        offset = 0
        while True:
            at = token.find(marker, offset)
            if at < 0: break
            if at == 0 or token[at - 1] == '/':
                full.add(('output/' if marker == 'insights/' else '') + token[at:])
            offset = at + 1
    relative = posixpath.normpath(posixpath.join(posixpath.dirname(source), token))
    return full, relative


def write_jsonl(path, rows):
    with open(path, 'w', encoding='utf-8') as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + '\n')


def last_commits(repo, commit, roots):
    found, current = {}, None
    raw = git(repo, 'log', '--first-parent', '-m', '--format=%H%x09%ct',
              '--name-only', commit, '--', 'output/insights')
    for line in raw.decode('utf-8', 'surrogateescape').splitlines():
        if re.fullmatch(r'[a-f0-9]{40}\t\d+', line):
            oid, stamp = line.split('\t')
            current = (oid, int(stamp))
        elif line.startswith('output/insights/') and current:
            root = root_for(line)
            if root in roots and root not in found:
                found[root] = current
    return found


def run(args):
    start = time.monotonic()
    entries = tree(args.repo, args.commit)
    paths = sorted(p for p in entries if p.startswith('output/insights/'))
    if args.limit is not None: paths = paths[:args.limit]
    roots = sorted({root_for(path) for path in paths})
    last = last_commits(args.repo, args.commit, set(roots))
    for root in roots:
        if root not in last: raise ValueError('missing last commit: ' + root)
    selected = set(paths)
    all_basenames = Counter(posixpath.basename(p) for p in entries)
    by_base, by_sha, by_blob = defaultdict(set), defaultdict(set), defaultdict(set)
    targets = {}
    blobs = Blobs(args.repo)
    try:
        for path in paths:
            data = blobs.get(entries[path]['blob'])
            if len(data) != entries[path]['size']: raise ValueError('size mismatch: ' + path)
            digest = hashlib.sha256(data).hexdigest()
            base = posixpath.basename(path)
            by_base[base].add(path)
            by_sha[digest].add(path)
            by_blob[entries[path]['blob']].add(path)
            targets[path] = dict(path=path, root=root_for(path), blob=entries[path]['blob'],
                                 size=len(data), sha256=digest,
                                 ext=base.rsplit('.', 1)[-1].lower() if '.' in base else '',
                                 basename_unique=all_basenames[base] == 1)
        dirs = {d for path in paths for d in ancestors(path)}
        hits = {axis: defaultdict(set) for axis in AXES}
        dir_hits = defaultdict(set)
        stats = Counter()
        glob_cache = {}
        broad_globs = defaultdict(set)
        for source in sorted(entries):
            data = blobs.get(entries[source]['blob'])
            if len(data) != entries[source]['size']: raise ValueError('size mismatch: ' + source)
            stats['corpus_blobs'] += 1
            stats['corpus_bytes'] += len(data)
            if source.endswith('.gz'):
                try:
                    with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
                        data = stream.read(args.gz_max_bytes + 1)
                    stats['gz_expanded'] += 1
                    if len(data) > args.gz_max_bytes:
                        stats['gz_exceeded'] += 1
                        data = data[:args.gz_max_bytes]
                except (OSError, EOFError):
                    stats['gz_failed'] += 1
                    continue
            if b'\0' in data[:8192]:
                stats['binary_skipped'] += 1
                continue
            body = data.decode('utf-8', 'replace')
            for digest in set(SHA.findall(body)):
                for path in by_sha.get(digest, ()):
                    if path != source:
                        hits['R4t' if targets[path]['size'] <= args.trivial_max_bytes else 'R4'][path].add(source)
            for oid in set(BLOB.findall(body)):
                for path in by_blob.get(oid, ()):
                    if path != source:
                        hits['R5t' if targets[path]['size'] <= args.trivial_max_bytes else 'R5'][path].add(source)
            for match in TOKEN.finditer(body):
                token = match.group().strip(',:;)]}>\'"').rstrip('.')
                if not token.startswith(('./', '../')):
                    token = token.lstrip('.')
                if not token: continue
                for path in by_base.get(token.rstrip('/').rsplit('/', 1)[-1], ()):
                    if path != source: hits['R3'][path].add(source)
                if '/' not in token and '.' not in token: continue
                full, relative = forms(token, source)
                if any(ch in token for ch in '*?['):
                    for pattern in full | {relative}:
                        if pattern not in glob_cache:
                            glob_cache[pattern] = [p for p in paths if fnmatch.fnmatchcase(p, pattern)]
                        if len(glob_cache[pattern]) > args.glob_max_matches:
                            broad_globs[pattern].add(source)
                            continue
                        for path in glob_cache[pattern]:
                            if path != source: hits['R7'][path].add(source)
                    continue
                for path in full & selected:
                    if path != source: hits['R1'][path].add(source)
                if relative in selected and relative != source: hits['R2'][relative].add(source)
                for directory in full & dirs: dir_hits[directory].add(source)
                if relative in dirs: dir_hits[relative].add(source)
    finally:
        blobs.close()

    def summary(sources, root, exclude=None):
        paths_here = sorted(s for s in sources if s != exclude)
        return {'count': len(paths_here),
                'by_category': dict(sorted(Counter(category(s, root) for s in paths_here).items())),
                'sample': paths_here[:args.sample_cap]}

    for path in paths:
        root = targets[path]['root']
        for axis in AXES: targets[path][axis] = summary(hits[axis][path], root, path)
        targets[path]['R6root'] = summary(dir_hits[root], root, path)
        targets[path]['R6'] = {d: summary(dir_hits[d], root, path)
                               for d in ancestors(path) if d.startswith(root + '/') and dir_hits[d] - {path}}
    rows = []
    for root in roots:
        members = [p for p in paths if targets[p]['root'] == root]
        rows.append({'root': root, 'files': len(members),
                     'bytes': sum(targets[p]['size'] for p in members),
                     'has_readme': root + '/README.md' in entries,
                     'root_refs': summary(dir_hits[root], root),
                     'last_commit': last[root][0], 'last_commit_time': last[root][1]})
    os.makedirs(args.out, exist_ok=True)
    write_jsonl(os.path.join(args.out, 'refs.jsonl'), (targets[p] for p in paths))
    write_jsonl(os.path.join(args.out, 'roots.jsonl'), rows)
    metrics = {'args': vars(args), 'commit': args.commit, 'targets': len(paths),
               **{key: stats[key] for key in ('corpus_blobs', 'corpus_bytes', 'binary_skipped',
                                               'gz_expanded', 'gz_exceeded', 'gz_failed')},
               'targets_with_refs': {axis: sum(bool(targets[p][axis]['count']) for p in paths)
                                     for axis in AXES},
               'elapsed_seconds': round(time.monotonic() - start, 3)}
    metrics['targets_with_refs']['R6'] = sum(bool(targets[p]['R6']) for p in paths)
    metrics['targets_with_refs']['R6root'] = sum(bool(targets[p]['R6root']['count']) for p in paths)
    metrics['broad_globs'] = [dict(pattern=pattern, sources=sorted(sources),
                                   matches=len(glob_cache[pattern]))
                              for pattern, sources in sorted(broad_globs.items())]
    with open(os.path.join(args.out, 'summary.json'), 'w', encoding='utf-8') as stream:
        json.dump(metrics, stream, sort_keys=True, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--limit', type=int)
    parser.add_argument('--gz-max-bytes', type=int, default=50000000)
    parser.add_argument('--glob-max-matches', type=int, default=50)
    parser.add_argument('--trivial-max-bytes', type=int, default=64)
    parser.add_argument('--sample-cap', type=int, default=200)
    args = parser.parse_args()
    if not os.path.isabs(args.repo) or not re.fullmatch(r'[a-f0-9]{40}', args.commit):
        parser.error('repo must be absolute and commit must be 40 lowercase hex digits')
    if (args.limit is not None and args.limit < 0 or
            min(args.gz_max_bytes, args.glob_max_matches,
                args.trivial_max_bytes, args.sample_cap) < 0):
        parser.error('limits must be nonnegative')
    run(args)


if __name__ == '__main__':
    main()
```

## classify.py

```python
#!/usr/bin/env python3
"""Apply a reviewable, external JSON policy to scan_refs output."""
import argparse
import json
import os
import re
from collections import Counter, defaultdict
from scan_refs import category


def read_jsonl(path, key):
    rows = {}
    with open(path, encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            value = row[key]
            if value in rows: raise ValueError('duplicate ' + key + ': ' + value)
            rows[value] = row
    return rows


def write_jsonl(path, rows):
    with open(path, 'w', encoding='utf-8') as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + '\n')


def records_for(row, axis):
    return row['R6'].items() if axis == 'R6' else ((axis, row[axis]),)


def filtered_record(record, root, ignored):
    # A truncated sample cannot prove that all ignored sources were removed.
    if record['count'] > len(record['sample']):
        return record
    sources = [source for source in record['sample'] if not ignored(source)]
    return {'count': len(sources), 'sample': sources,
            'by_category': dict(sorted(Counter(category(source, root) for source in sources).items()))}


def filter_refs(row, ignored, has_ignored_sources):
    result = dict(row)
    unfilterable = []
    unfilterable_axes = {'R1', 'R2', 'R4', 'R5', 'R7'}
    if row['basename_unique']:
        unfilterable_axes.add('R3')
    for axis in ('R1', 'R2', 'R3', 'R4', 'R4t', 'R5', 'R5t', 'R6root', 'R7'):
        if (has_ignored_sources and axis in unfilterable_axes and
                row[axis]['count'] > len(row[axis]['sample'])):
            unfilterable.append((axis, row[axis]))
        result[axis] = filtered_record(row[axis], row['root'], ignored)
    if has_ignored_sources:
        unfilterable.extend(('R6:' + directory, record) for directory, record in row['R6'].items()
                            if record['count'] > len(record['sample']))
    result['R6'] = {directory: filtered_record(record, row['root'], ignored)
                    for directory, record in row['R6'].items()}
    result['R6'] = {directory: record for directory, record in result['R6'].items()
                    if record['count']}
    result['_unfilterable'] = unfilterable
    return result


def first_source(record):
    return record['sample'][0] if record['sample'] else '?'


def axis_categories(row, axes):
    result = Counter()
    for axis in axes:
        for _, record in records_for(row, axis):
            result.update(record['by_category'])
    return result


def any_refs(row):
    return any(row[axis]['count'] for axis in ('R1', 'R2', 'R3', 'R4', 'R4t', 'R5', 'R5t', 'R6root', 'R7')) or any(
        record['count'] for record in row['R6'].values())


def classify(row, roots, config, blob_groups):
    path, root, ext = row['path'], row['root'], row['ext']
    if ext in config['impl_exts']: return 'D', 'impl_exts:' + ext
    for pattern in config['protect_path_regexes']:
        if re.search(pattern, path, re.IGNORECASE): return 'D', 'protect_path_regexes:' + pattern
    if root in config['protect_roots']: return 'D', 'protect_roots:' + root
    if root.rsplit('/', 1)[-1] in config['protect_root_names']:
        return 'D', 'protect_root_names:' + root.rsplit('/', 1)[-1]
    for axis in ('R4', 'R5'):
        if row[axis]['count']:
            return 'D', axis + ':' + str(row[axis]['count']) + ':' + first_source(row[axis])
    strong = set(config['strong_categories'])
    for axis in ('R1', 'R2', 'R6', 'R7'):
        for detail, record in records_for(row, axis):
            found = sorted(strong & record['by_category'].keys())
            if found:
                sources = [s for s in record['sample'] if category(s, root) == found[0]]
                return 'D', 'strong_categories:' + axis + ':' + detail + ':' + found[0] + ':' + (sources[0] if sources else first_source(record))
    if roots[root]['last_commit_time'] >= config['cutoff_unix']:
        return 'D', 'cutoff_unix:' + str(roots[root]['last_commit_time'])
    if root in config['c_roots']: return 'C', 'c_roots:' + root
    if ext not in config['machine_exts']: return 'D', 'machine_exts:' + ext
    if row['_unfilterable']:
        axis, record = row['_unfilterable'][0]
        return 'D', 'unfilterable:' + axis + ':' + first_source(record)
    if not any(row[axis]['count'] for axis in ('R1', 'R2', 'R7')) and (
        not row['basename_unique'] or not row['R3']['count']) and not row['R6']:
        return 'A', 'unreferenced'
    peers = blob_groups[row['blob']]
    if len(peers) > 1 and not any_refs(row):
        referenced = [p for p in peers if any_refs(p)]
        keeper = min(referenced or peers, key=lambda p: p['path'])['path']
        if keeper != path: return 'A', 'duplicate-of:' + keeper
    allowed = {'output-same-root', 'docs/worklog', 'docs/spool', 'docs/other'}
    all_categories = axis_categories(row, ('R1', 'R2', 'R3', 'R4', 'R4t', 'R5', 'R5t', 'R6', 'R7'))
    if set(all_categories) <= allowed and root in config['b_roots']:
        source = next((axis + ':' + first_source(record) for axis in
                       ('R1', 'R2', 'R3', 'R4t', 'R5t', 'R6', 'R7')
                       for _, record in records_for(row, axis) if record['count']), 'none')
        return 'B', 'b_roots:' + root + ':' + source
    source = next((axis + ':' + first_source(record) for axis in
                   ('R1', 'R2', 'R3', 'R4t', 'R5t', 'R6', 'R7')
                   for _, record in records_for(row, axis) if record['count']), 'none')
    return 'D', 'remaining-references:' + ','.join(sorted(all_categories)) + ':' + source


def main():
    parser = argparse.ArgumentParser()
    for key in ('refs', 'roots', 'config', 'out'): parser.add_argument('--' + key, required=True)
    args = parser.parse_args()
    refs = read_jsonl(args.refs, 'path')
    roots = read_jsonl(args.roots, 'root')
    with open(args.config, encoding='utf-8') as stream: config = json.load(stream)
    required = ('machine_exts', 'impl_exts', 'protect_path_regexes', 'protect_roots',
                'protect_root_names', 'strong_categories', 'cutoff_unix', 'b_roots', 'c_roots')
    for key in required:
        if key not in config: raise ValueError('missing config key: ' + key)
    ignored_sources = set(config.get('ignore_sources', []))
    ignored_patterns = [re.compile(pattern) for pattern in config.get('ignore_source_regexes', [])]
    def ignored(source):
        return source in ignored_sources or any(pattern.search(source) for pattern in ignored_patterns)
    has_ignored_sources = bool(ignored_sources or ignored_patterns)
    refs = {path: filter_refs(row, ignored, has_ignored_sources) for path, row in refs.items()}
    groups = defaultdict(list)
    for row in refs.values():
        if row['root'] not in roots: raise ValueError('missing root: ' + row['root'])
        groups[row['blob']].append(row)
    rows = []
    for path in sorted(refs):
        row = refs[path]
        kind, reason = classify(row, roots, config, groups)
        rows.append({'path': path, 'root': row['root'], 'class': kind,
                     'reason': reason, 'size': row['size'], 'blob': row['blob']})
    os.makedirs(args.out, exist_ok=True)
    write_jsonl(os.path.join(args.out, 'classes.jsonl'), rows)
    by_root = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    counts = defaultdict(lambda: [0, 0])
    reasons = Counter()
    for row in rows:
        by_root[row['root']][row['class']][0] += 1
        by_root[row['root']][row['class']][1] += row['size']
        counts[row['class']][0] += 1
        counts[row['class']][1] += row['size']
        reasons[row['reason']] += 1
    with open(os.path.join(args.out, 'by_root.tsv'), 'w', encoding='utf-8') as stream:
        stream.write('root\tA\tA_bytes\tB\tB_bytes\tC\tC_bytes\tD\tD_bytes\n')
        for root in sorted(by_root, key=lambda x: (-sum(v[0] for v in by_root[x].values()), x)):
            fields = [root]
            for kind in 'ABCD': fields.extend(map(str, by_root[root][kind]))
            stream.write('\t'.join(fields) + '\n')
    with open(os.path.join(args.out, 'counts.json'), 'w', encoding='utf-8') as stream:
        json.dump({'classes': {k: {'files': counts[k][0], 'bytes': counts[k][1]} for k in 'ABCD'},
                   'reasons': dict(sorted(reasons.items()))}, stream, sort_keys=True, ensure_ascii=False, indent=2)
        stream.write('\n')
    for kind in 'ABC':
        with open(os.path.join(args.out, 'prune-' + kind + '.txt'), 'w', encoding='utf-8') as stream:
            for row in rows:
                if row['class'] == kind: stream.write(row['path'] + '\n')


if __name__ == '__main__':
    main()
```

## build_index.py

```python
#!/usr/bin/env python3
"""Build and verify a recoverable deletion index."""
import argparse
import json
import os
import re
import subprocess
import sys
sys.dont_write_bytecode = True
from scan_refs import tree, write_jsonl


def read_rows(path, key):
    rows = {}
    with open(path, encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            if row[key] in rows: raise ValueError('duplicate ' + key + ': ' + row[key])
            rows[row[key]] = row
    return rows


def build(args):
    entries = tree(args.repo, args.commit)
    classes = read_rows(args.classes, 'path')
    wanted = set()
    for filename in args.prune_list:
        with open(filename, encoding='utf-8') as stream:
            for raw in stream:
                path = raw.rstrip('\n')
                if not path or path in wanted: raise ValueError('empty or duplicate prune path: ' + path)
                if path not in entries: raise ValueError('path absent from tree: ' + path)
                if path not in classes: raise ValueError('path absent from classes: ' + path)
                if classes[path]['blob'] != entries[path]['blob'] or classes[path]['size'] != entries[path]['size']:
                    raise ValueError('class/tree mismatch: ' + path)
                wanted.add(path)
    rows = [{'path': p, 'blob': entries[p]['blob'], 'size': entries[p]['size'],
             'commit': args.commit, 'class': classes[p]['class'], 'reason': classes[p]['reason']}
            for p in sorted(wanted)]
    write_jsonl(args.out, rows)
    with open(args.out + '.pathspec', 'wb') as stream:
        for path in sorted(wanted): stream.write(path.encode('utf-8') + b'\0')


def verify(args):
    entries = read_rows(args.index, 'path')
    base, new = tree(args.repo, args.base), tree(args.repo, args.new)
    raw = subprocess.check_output(['git', '-C', args.repo, 'diff', '--name-status', '--no-renames',
                                   '-z', args.base, args.new])
    parts = raw.split(b'\0')
    if parts[-1] != b'': raise ValueError('truncated git diff')
    deleted = set()
    unexpected = []
    for i in range(0, len(parts) - 1, 2):
        status = parts[i].decode('ascii')
        path = parts[i + 1].decode('utf-8', 'surrogateescape')
        if status == 'D': deleted.add(path)
        elif status not in ('A', 'M', 'T'): unexpected.append(status + ':' + path)
    indexed = set(entries)
    errors = []
    if deleted != indexed:
        errors.append('deleted-only=' + repr(sorted(deleted - indexed)))
        errors.append('indexed-only=' + repr(sorted(indexed - deleted)))
    if unexpected: errors.append('unexpected-status=' + repr(unexpected))
    for path in sorted(indexed):
        row = entries[path]
        if path not in base: errors.append('absent-from-base:' + path)
        elif base[path]['blob'] != row['blob'] or base[path]['size'] != row['size']:
            errors.append('base-blob-or-size-mismatch:' + path)
        if path in new: errors.append('still-in-new:' + path)
    if errors: raise ValueError('\n'.join(errors))
    print('verified', len(indexed), 'deletions')


def main():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest='command', required=True)
    b = subs.add_parser('build')
    for key in ('repo', 'commit', 'classes', 'out'): b.add_argument('--' + key, required=True)
    b.add_argument('--prune-list', nargs='+', required=True)
    v = subs.add_parser('verify')
    for key in ('repo', 'base', 'new', 'index'): v.add_argument('--' + key, required=True)
    args = parser.parse_args()
    if not os.path.isabs(args.repo): parser.error('repo must be absolute')
    for key in ('commit', 'base', 'new'):
        if hasattr(args, key) and not re.fullmatch('[a-f0-9]{40}', getattr(args, key)):
            parser.error(key + ' must be 40 lowercase hex digits')
    if args.command == 'build': build(args)
    else: verify(args)


if __name__ == '__main__':
    main()
```
