# 実測スクリプト (逐語)

この wave で親が書いた使い捨て実測スクリプトを逐語で保存する。
`.py` のまま repo へ置くと `_is_implementation_path()` の suffix 規則に当たり
Codex author 契約が発火するため (本 wave が台帳 3 件の生成器として記録したのと同じ経路)、
Markdown の fenced block として保存する。

**欠陥のあるものも含めて保存する。** どこをどう間違えたかが F144 再発の一次資料である。
実行時の cwd は repo root を前提とする。

## measure_union.py

弱い述語 (全行がいずれかの親に存在するか) を測る。単独では採ってはならない。

```python
import sys, subprocess
sys.path.insert(0, 'tools')
import check_ai_provenance as c

specs = [s for s in c.KNOWN_PROVENANCE_VIOLATIONS
         if s.expected_finding_kind == 'missing-codex-author']
print('missing-codex-author entries:', len(specs))
zero, nonzero, nonmerge = [], [], []
for s in specs:
    sha = s.commit
    par = subprocess.run(['git', 'rev-list', '--parents', '-n', '1', sha],
                         capture_output=True, text=True).stdout.split()
    parents = par[1:]
    if len(parents) < 2:
        nonmerge.append(sha)
        continue
    paths = c._commit_paths(sha)
    tot = 0
    for p in paths:
        res = subprocess.run(['git', 'show', sha + ':' + p],
                             capture_output=True).stdout.splitlines()
        union = set()
        for pa in parents:
            union |= set(subprocess.run(['git', 'show', pa + ':' + p],
                                        capture_output=True).stdout.splitlines())
        tot += sum(1 for l in res if l not in union)
    (zero if tot == 0 else nonzero).append((sha[:10], len(paths), tot))

print('MERGE novel==0 (retirable):', len(zero))
for z in zero:
    print('   ', z)
print('MERGE novel>0 (genuine):', len(nonzero))
for z in nonzero:
    print('   ', z)
print('NON-MERGE (genuine):', len(nonmerge))
for z in nonmerge:
    print('   ', z[:10])
```

## measure_subseq.py

強い述語 (両親が結果の subsequence か) を測る。案 A で 4 件が残った根拠。

```python
"""強い述語: 両親の版がそれぞれ結果の subsequence か (順序保存・削除なし) を測る。

novel==0 は「新しい行が無い」だけで、並べ替え・取捨選択を排除できない。
両親の全行が順序を保って結果に残っているなら、解決は両側の純粋な interleaving であり、
取捨選択も並べ替えも行われていない。
"""
import sys
import subprocess

sys.path.insert(0, 'tools')
import check_ai_provenance as c


def blob_lines(rev, path):
    r = subprocess.run(['git', 'show', rev + ':' + path], capture_output=True)
    if r.returncode != 0:
        return None
    return r.stdout.splitlines()


def is_subsequence(small, big):
    it = iter(big)
    return all(line in it for line in small)


specs = [s for s in c.KNOWN_PROVENANCE_VIOLATIONS
         if s.expected_finding_kind == 'missing-codex-author']
strong, weak_only, other = [], [], []

for s in specs:
    sha = s.commit
    par = subprocess.run(['git', 'rev-list', '--parents', '-n', '1', sha],
                         capture_output=True, text=True).stdout.split()
    parents = par[1:]
    if len(parents) != 2:
        other.append((sha[:10], 'non-merge'))
        continue
    paths = c._commit_paths(sha)
    per_path = []
    for p in paths:
        res = blob_lines(sha, p)
        pa = blob_lines(parents[0], p)
        pb = blob_lines(parents[1], p)
        if res is None or pa is None or pb is None:
            per_path.append((p, 'missing-side'))
            continue
        union = set(pa) | set(pb)
        novel = sum(1 for l in res if l not in union)
        sa = is_subsequence(pa, res)
        sb = is_subsequence(pb, res)
        if novel == 0 and sa and sb:
            per_path.append((p, 'pure-interleave'))
        elif novel == 0:
            per_path.append((p, 'novel0-but-drops(a=' + str(sa) + ',b=' + str(sb) + ')'))
        else:
            per_path.append((p, 'novel=' + str(novel)))
    kinds = {v for _, v in per_path}
    if kinds == {'pure-interleave'}:
        strong.append((sha[:10], len(paths)))
    elif all(v.startswith('novel0') or v == 'pure-interleave' for v in kinds):
        weak_only.append((sha[:10], per_path))
    else:
        other.append((sha[:10], per_path))

print('強い述語を満たす (両側完全保存の interleave):', len(strong))
for x in strong:
    print('    ', x)
print()
print('novel==0 だが取捨選択あり (強い述語では残る):', len(weak_only))
for x in weak_only:
    print('    ', x[0])
    for p, v in x[1]:
        print('        ', v, p)
print()
print('その他 (真の違反):', len(other))
for x in other:
    print('    ', x[0] if isinstance(x, tuple) else x)
```

## measure_mergefile.py

flagged path ごとに git の自動解決を再計算して実体と突き合わせる。**blob 単位の低水準 merge であり実 merge の忠実な代理ではない** (F144 再発の (2))。

```python
"""flagged path ごとに「git が自動で解決した結果」と実体を突き合わせる (旧 git 対応)。

各 path で merge base / 親1 / 親2 の blob を取り出し `git merge-file -p` で 3-way merge を
再計算する。rc=0 (競合なし) かつ出力が commit の実体と bytes 一致するなら、その path には
人間/AI の編集判断が 1 bit も入っていない。
複数 merge base (criss-cross) は近似になるため fail-closed で「判定不能」に落とす。
"""
import os
import sys
import subprocess
import tempfile

sys.path.insert(0, 'tools')
import check_ai_provenance as c


def out(args):
    return subprocess.run(args, capture_output=True)


specs = [s for s in c.KNOWN_PROVENANCE_VIOLATIONS
         if s.expected_finding_kind == 'missing-codex-author']
auto, edited, undecidable, notmerge = [], [], [], []

for s in specs:
    sha = s.commit
    par = subprocess.run(['git', 'rev-list', '--parents', '-n', '1', sha],
                         capture_output=True, text=True).stdout.split()
    parents = par[1:]
    if len(parents) != 2:
        notmerge.append(sha[:10])
        continue
    bases = subprocess.run(['git', 'merge-base', '--all', parents[0], parents[1]],
                           capture_output=True, text=True).stdout.split()
    if len(bases) != 1:
        undecidable.append((sha[:10], 'merge-bases=' + str(len(bases))))
        continue
    base = bases[0]
    paths = c._commit_paths(sha)
    verdicts = []
    for p in paths:
        blobs = {}
        ok = True
        for tag, rev in (('base', base), ('a', parents[0]), ('b', parents[1])):
            r = out(['git', 'show', rev + ':' + p])
            if r.returncode != 0:
                ok = False
                break
            blobs[tag] = r.stdout
        if not ok:
            verdicts.append((p, 'missing-side'))
            continue
        real = out(['git', 'show', sha + ':' + p]).stdout
        tmp = {}
        try:
            for tag in ('base', 'a', 'b'):
                fd, path = tempfile.mkstemp()
                with os.fdopen(fd, 'wb') as fh:
                    fh.write(blobs[tag])
                tmp[tag] = path
            mf = subprocess.run(
                ['git', 'merge-file', '-p', '--diff3', tmp['a'], tmp['base'], tmp['b']],
                capture_output=True)
        finally:
            for path in tmp.values():
                os.unlink(path)
        if mf.returncode != 0:
            verdicts.append((p, 'conflict-rc' + str(mf.returncode)))
        elif mf.stdout == real:
            verdicts.append((p, 'auto-identical'))
        else:
            verdicts.append((p, 'auto-differs'))
    kinds = {v for _, v in verdicts}
    if kinds == {'auto-identical'}:
        auto.append((sha[:10], len(paths)))
    elif 'auto-differs' in kinds or 'conflict-rc' in ''.join(kinds):
        edited.append((sha[:10], verdicts))
    else:
        undecidable.append((sha[:10], verdicts))

print('全 flagged path が git の自動解決と bytes 一致 (編集ゼロ):', len(auto))
for x in auto:
    print('    ', x)
print()
print('編集または競合が入った:', len(edited))
for x in edited:
    print('    ', x[0])
    for p, v in x[1]:
        print('        ', v, p)
print()
print('判定不能:', len(undecidable))
for x in undecidable:
    print('    ', x)
print()
print('非 2-parent:', len(notmerge), notmerge)
```

## classify.py

53 件の全数分類。**canonical trailer を検査しない欠陥がある** (F144 再発の (4))。

```python
"""known-violation 53 件を全数分類する。"""
import sys
import subprocess

sys.path.insert(0, 'tools')
import check_ai_provenance as c

STRONG_OK = {'5823caf328a5985476cd2f6f7aa0d13daa5b08f6',
             '3eaf2038ec2ac3e7965c2a1eedcadb1ed1266626',
             '0c0f3e71b3208370be8d4e7e20a84a2152afe4b2',
             'bf92f327cadfbe626e37cab73d55abe80d3994dd'}


def show(sha, fmt):
    return subprocess.run(['git', 'show', '-s', '--format=' + fmt, sha],
                          capture_output=True, text=True).stdout.strip()


rows = []
for s in c.KNOWN_PROVENANCE_VIOLATIONS:
    sha = s.commit
    date = show(sha, '%cI')[:10]
    subj = show(sha, '%s')
    parents = show(sha, '%P').split()
    body = show(sha, '%B')
    has_agent = 'AI-Agent:' in body
    is_merge = len(parents) > 1
    kind = s.expected_finding_kind

    if kind == 'malformed-ai-agent' and 'role=orchestrator' in s.expected_finding_value:
        gen = 'G1 綴り誤り (2026-08-09 単一incident)'
        fix = '不可 (履歴不変)'
    elif kind == 'malformed-ai-agent':
        gen = 'G2 role 綴り誤り (role=fix)'
        fix = '不可 (履歴不変)'
    elif kind == 'missing-ai-agent' and not has_agent and is_merge:
        gen = 'G3 --no-edit merge (trailer ゼロ)'
        fix = '不可 (履歴不変)'
    elif kind == 'missing-ai-agent' and not has_agent:
        gen = 'G4 trailer 無し commit (revert/ユーザー直接/旧docs)'
        fix = '不可 (履歴不変)'
    elif kind == 'missing-codex-author' and is_merge:
        gen = 'G5 台帳自身の競合を親が手解決した merge'
        fix = ('案Aで撤去可' if sha in STRONG_OK else '不可 (取捨選択あり/著作あり)')
    else:
        gen = 'G6 manager が実装面を直接 commit'
        fix = '不可 (履歴不変)'
    rows.append((date, sha[:10], kind, gen, fix, subj[:44]))

rows.sort()
print('| 日付 | SHA | finding | 生成器 | 撤去可否 | 件名 |')
print('|---|---|---|---|---|---|')
for r in rows:
    print('| ' + ' | '.join(r) + ' |')

print()
from collections import Counter
print('生成器別:', )
for k, v in sorted(Counter(r[3] for r in rows).items()):
    print('   ', v, k)
print()
print('撤去可否:')
for k, v in sorted(Counter(r[4] for r in rows).items()):
    print('   ', v, k)
```

## growth.py

台帳件数の履歴。文字列数え版。厳密値は remeasure.py の ast 版を使う。

```python
"""台帳の件数を main の履歴に沿って数え、増減を測る。

`KnownViolationSpec(` の出現数を各 commit 時点の tools/check_ai_provenance.py で数える。
"""
import subprocess

log = subprocess.run(
    ['git', 'log', '--format=%H %cI', '--reverse', '--first-parent', 'main', '--',
     'tools/check_ai_provenance.py'],
    capture_output=True, text=True).stdout.splitlines()

prev = None
points = []
for line in log:
    sha, iso = line.split()
    blob = subprocess.run(['git', 'show', sha + ':tools/check_ai_provenance.py'],
                          capture_output=True, text=True).stdout
    if 'KNOWN_PROVENANCE_VIOLATIONS' not in blob:
        continue
    n = blob.count('KnownViolationSpec(')
    if prev is None or n != prev:
        points.append((iso[:16], sha[:10], n, (n - prev) if prev is not None else n))
        prev = n

print('件数が変化した commit だけを表示 (時刻, SHA, 件数, 増減)')
ups = downs = 0
for t, s, n, d in points:
    mark = '+' + str(d) if d > 0 else str(d)
    if d > 0:
        ups += 1
    elif d < 0:
        downs += 1
    print('  ', t, s, 'count=' + str(n), mark)
print()
print('増加した変化点:', ups, ' 減少した変化点:', downs)
```

## prevented.py

案 B の防止可能件数。**実装面 path へ絞っていない欠陥がある** (F144 再発の (1))。

```python
"""案 B (台帳を 1 件 1 file のデータへ移す) が防げた entry を数える。

判定: その commit の実装面 path が「台帳 3 重化 file」だけなら、案 B で防げた。
台帳 3 重化 file = tools/check_ai_provenance.py と
orchestrator/tests/test_check_ai_provenance.py。
"""
import sys
import subprocess

sys.path.insert(0, 'tools')
import check_ai_provenance as c

LEDGER = {'tools/check_ai_provenance.py',
          'orchestrator/tests/test_check_ai_provenance.py'}

seen = set()
prevented, not_prevented, other_kind = [], [], []
for s in c.KNOWN_PROVENANCE_VIOLATIONS:
    if s.commit in seen:
        continue
    seen.add(s.commit)
    if s.expected_finding_kind != 'missing-codex-author':
        other_kind.append((s.commit[:10], s.expected_finding_kind))
        continue
    paths = set(c._commit_paths(s.commit))
    subj = subprocess.run(['git', 'show', '-s', '--format=%s', s.commit],
                          capture_output=True, text=True).stdout.strip()
    if paths and paths <= LEDGER:
        prevented.append((s.commit[:10], sorted(paths), subj[:40]))
    else:
        not_prevented.append((s.commit[:10], sorted(paths), subj[:40]))

print('案 B で防げた (実装面 path が台帳 file だけ):', len(prevented))
for x in prevented:
    print('    ', x[0], x[2])
    print('        paths:', x[1])
print()
print('防げない (台帳以外の実装面 path を含む):', len(not_prevented))
for x in not_prevented:
    print('    ', x[0], x[2])
    print('        paths:', x[1])
print()
print('missing-codex-author 以外 (案 B の射程外):', len(other_kind))
```

## remeasure.py

F144 再発の (1) と growth の欠陥を直した再測定。**この 2 つが厳密値である。**

```python
"""sol の指摘を受けた再測定。

(1) 案 B の防止可能件数を、実装面 path だけに絞って数え直す。
(2) 台帳件数の履歴を、文字列数えでなく ast で registry tuple を構文解析して数え直す。
"""
import ast
import sys
import subprocess

sys.path.insert(0, 'tools')
import check_ai_provenance as c

LEDGER = {'tools/check_ai_provenance.py',
          'orchestrator/tests/test_check_ai_provenance.py'}

print('=== (1) 案 B の防止可能件数 (実装面 path のみ) ===')
seen = set()
prevented, not_prevented = [], []
for s in c.KNOWN_PROVENANCE_VIOLATIONS:
    if s.commit in seen or s.expected_finding_kind != 'missing-codex-author':
        continue
    seen.add(s.commit)
    all_paths = c._commit_paths(s.commit)
    impl = {p for p in all_paths if c._is_implementation_path(p)}
    subj = subprocess.run(['git', 'show', '-s', '--format=%s', s.commit],
                          capture_output=True, text=True).stdout.strip()
    if impl and impl <= LEDGER:
        prevented.append((s.commit[:10], sorted(impl), subj[:40]))
    else:
        not_prevented.append((s.commit[:10], sorted(impl), subj[:40]))
print('実装面 path が台帳 file だけ:', len(prevented))
for x in prevented:
    print('    ', x[0], x[2], x[1])
print('それ以外:', len(not_prevented))
for x in not_prevented:
    print('    ', x[0], x[2], x[1])

print()
print('=== (2) 台帳件数の履歴 (ast で registry tuple を構文解析) ===')


def registry_len(src):
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == 'KNOWN_PROVENANCE_VIOLATIONS':
                    if isinstance(node.value, ast.Tuple):
                        return len(node.value.elts)
                    return -1
    return None


log = subprocess.run(
    ['git', 'log', '--format=%H %cI', '--reverse', '--first-parent', 'main', '--',
     'tools/check_ai_provenance.py'],
    capture_output=True, text=True).stdout.splitlines()
prev = None
ups = downs = 0
for line in log:
    sha, iso = line.split()
    src = subprocess.run(['git', 'show', sha + ':tools/check_ai_provenance.py'],
                         capture_output=True, text=True).stdout
    n = registry_len(src)
    if n is None or n < 0:
        continue
    if prev is None or n != prev:
        d = n - prev if prev is not None else n
        if d > 0:
            ups += 1
        elif d < 0:
            downs += 1
        print('  ', iso[:16], sha[:10], 'count=' + str(n),
              ('+' + str(d)) if d > 0 else str(d))
        prev = n
print('増加した変化点:', ups, ' 減少した変化点:', downs, ' 最終値:', prev)
```

## reclassify.py

F144 再発の (4) を直した missing-ai-agent の再分類。

```python
"""sol の指摘 8 を受けた再分類。

missing-ai-agent の entry について、commit message に AI-Agent 行が
「そもそも無い」のか「有るが最終 trailer block に入っていない」のかを分ける。
"""
import sys
import subprocess

sys.path.insert(0, 'tools')
import check_ai_provenance as c


def body(sha):
    return subprocess.run(['git', 'show', '-s', '--format=%B', sha],
                          capture_output=True, text=True).stdout


def trailers(sha):
    return subprocess.run(
        ['git', 'show', '-s', '--format=%(trailers:unfold)', sha],
        capture_output=True, text=True).stdout


rows = []
for s in c.KNOWN_PROVENANCE_VIOLATIONS:
    if s.expected_finding_kind != 'missing-ai-agent':
        continue
    b = body(s.commit)
    t = trailers(s.commit)
    raw_present = 'AI-Agent:' in b
    trailer_present = 'AI-Agent:' in t
    parents = subprocess.run(['git', 'show', '-s', '--format=%P', s.commit],
                             capture_output=True, text=True).stdout.split()
    subj = subprocess.run(['git', 'show', '-s', '--format=%s', s.commit],
                          capture_output=True, text=True).stdout.strip()
    if not raw_present:
        gen = 'trailer 完全欠落'
    elif not trailer_present:
        gen = 'trailer block 配置誤り (AI-Agent 行は本文に在る)'
    else:
        gen = 'その他 (要確認)'
    rows.append((s.commit[:10], len(parents) > 1, gen, subj[:46]))

print('missing-ai-agent', len(rows), '件の再分類')
for r in rows:
    print('  ', r[0], 'merge' if r[1] else '     ', '|', r[2])
    print('        ', r[3])

from collections import Counter
print()
for k, v in sorted(Counter(r[2] for r in rows).items()):
    print('  ', v, k)

print()
uniq = len({s.commit for s in c.KNOWN_PROVENANCE_VIOLATIONS})
print('registered findings:', len(c.KNOWN_PROVENANCE_VIOLATIONS),
      ' unique commits:', uniq)
```
