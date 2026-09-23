1) 変更の要約

mocc 用への改修を完了しました。指定4ファイルのうち `run_probe.py`・`selftest.py`・`mutation-spec.template.json` を変更し、`v3check.py` は前 wave と完全一致のままです。tracked file・`external/ccbench/`・index・HEAD は変更していません。

- commit 引数・祖先・raw diff 検査を base → C1' → C3 に変更。
- target、実行ファイルの場所、YCSB verifier の protocol を mocc に変更。
- 変異契約を D1・M1m・M2・M3m・M4m・M5m に変更。
- M5m は全21 entryを比較し、mocc transaction の4 entryだけ展開不一致、全21 entryの include 活性一致、残り17 entryの展開一致を要求。
- 自己試験を新契約に更新し、直接実行の入口を追加。
- CMake と mocc の `chkArg()`・gflags 定義を確認し、追加の走行 flag は入れていません。

検査を弱めていないことの確認箇所（変更後 `run_probe.py` の行番号）：

| 行 | 維持した検査 |
|---|---|
| 224、287、306 | archive 属性対策、抽出ファイル集合・blob 完全一致 |
| 314、374 | consumer 導出、12 source / 21 entry、両前処理モード |
| 420 | nm・strings・正規化逆アセンブル |
| 584、611 | include 活性負例9件、TRACE=1構文検査 |
| 637–676 | pristine確認、anchor出現1回、ERROR扱い、復元digest |
| 761–780 | D1/M2診断条件、M1m先頭理由、M3m/M4m理由集合 |
| 786–797 | M5mの21件・4件・17件の厳密条件 |

`clean_env`、consumer導出、前処理、binary、C0/C1/C2、段の実行順は AST 比較でも不変でした。構造検査器と、その既存自己試験本文も不変です。

以下が前 wave `verbatim/` との差分全文です。`v3check.py` の unified diff は空です。

```diff
--- verbatim/run_probe.py
+++ probe/run_probe.py
@@ -24,8 +24,8 @@
 sys.dont_write_bytecode = True
 from v3check import check, parse_witness

-TARGETS = ('tpcc_silo.exe', 'ycsb_silo.exe')
-CHANGED = {'include/trace.hh', 'include/tpcc.hh', 'cc/silo/transaction.cc'}
+TARGETS = ('tpcc_mocc.exe', 'ycsb_mocc.exe')
+CHANGED = {'include/trace.hh', 'include/tpcc.hh', 'cc/mocc/transaction.cc'}
 TPCC = ['-thread_num=2', '-extime=1', '-tpcc_num_wh=1', '-tpcc_perc_payment=43',
         '-tpcc_perc_order_status=0', '-tpcc_perc_delivery=0', '-tpcc_perc_stock_level=0',
         '-clocks_per_us=2100']
@@ -226,20 +226,20 @@
             'archive_attributes': {'path': str(attributes), 'contents': attributes.read_text()},
             'tree_checks': {}}
         git = ['git', '-C', objects]
-        for oid, parent in ((self.a.c1_oid, self.a.pin_oid), (self.a.c2_oid, self.a.c1_oid)):
+        for oid, parent in ((self.a.c1p_oid, self.a.base_oid), (self.a.c3_oid, self.a.c1p_oid)):
             need(self.text([*git, 'rev-list', '--parents', '-n', '1', oid]).split() == [oid, parent], 'commit ancestry mismatch')
         raw_diffs = {}
         for label, left, right, expected in (
-                ('pin->C1', self.a.pin_oid, self.a.c1_oid, {'include/trace.hh', 'include/tpcc.hh'}),
-                ('C1->C2', self.a.c1_oid, self.a.c2_oid, {'cc/silo/transaction.cc'}),
-                ('pin->C2', self.a.pin_oid, self.a.c2_oid, CHANGED)):
+                ("base->C1'", self.a.base_oid, self.a.c1p_oid, {'include/trace.hh', 'include/tpcc.hh'}),
+                ("C1'->C3", self.a.c1p_oid, self.a.c3_oid, {'cc/mocc/transaction.cc'}),
+                ('base->C3', self.a.base_oid, self.a.c3_oid, CHANGED)):
             raw = self.text([*git, 'diff-tree', '-r', '--raw', '--no-abbrev', '--no-renames', left, right])
             raw_diffs[label] = raw
             rows = [re.fullmatch(r':100644 100644 [0-9a-f]{40} [0-9a-f]{40} M\t(.+)', r)
                     for r in raw.splitlines()]
             need(len(rows) == len(expected) and all(rows) and {r[1] for r in rows} == expected,
                  f'{label} must modify exactly {sorted(expected)} as regular source files')
-        for oid, source in ((self.a.pin_oid, self.pin), (self.a.c2_oid, self.cnd)):
+        for oid, source in ((self.a.base_oid, self.pin), (self.a.c3_oid, self.cnd)):
             resolved = self.text([*git, 'rev-parse', f'{oid}^{{commit}}']).strip()
             need(resolved == oid, 'commit resolution mismatch')
             tree = self.command([*git, 'ls-tree', '-r', '-z', oid])
@@ -306,9 +306,9 @@
                 need(False, f'C0 source blob mismatch: {source}; see source_evidence attributes')
             row['passed'] = True
             self.flush()
-        evidence.update({'raw_diff': raw_diffs['pin->C2'], 'raw_diffs': raw_diffs,
+        evidence.update({'raw_diff': raw_diffs['base->C3'], 'raw_diffs': raw_diffs,
             'bundle_sha256': sha(self.a.bundle),
-            'blobs': {n: {'pin': sha(self.pin / n), 'C2': sha(self.cnd / n)} for n in sorted(CHANGED)}})
+            'blobs': {n: {'base': sha(self.pin / n), 'C3': sha(self.cnd / n)} for n in sorted(CHANGED)}})
         self.flush()

     def entries(self, source, build):
@@ -522,7 +522,7 @@
                   'commit_counts': commits, 'batch_commit_counts': batch, 'counts': {'C': c, 'E': e}}
         if not reasons:
             rec = self.command([sys.executable, '-B', self.a.repo_root / 'orchestrator/verify.py', directory,
-                                '--expected-commits', commits, '--protocol', 'silo', '--ccbench-root', source,
+                                '--expected-commits', commits, '--protocol', 'mocc', '--ccbench-root', source,
                                 '--json'], checked=False, timeout=300)
             payload = json.loads(Path(rec['stdout_log']).read_text()) if rec['returncode'] == 0 else {}
             result['verifier'] = payload
@@ -655,7 +655,7 @@
                 if spec['kind'] == 'preprocess':
                     # Reuse TRACE=0 flags/generated headers; no configure or build.
                     result = self.preprocess(self.epin, remap_entries(self.ecnd, self.cnd, source),
-                        self.pin, self.bpin, source, self.bcnd, spec['id'], True)
+                        self.pin, self.bpin, source, self.bcnd, spec['id'])
                     result['first_reason'] = None if result['passed'] else 'trace0-preprocess'
                     result['reasons'] = [] if result['passed'] else ['trace0-preprocess']
                 else:
@@ -722,7 +722,7 @@


 def executable(build, target):
-    path = build / 'cc/silo' / target
+    path = build / 'cc/mocc' / target
     need(path.is_file() and os.access(path, os.X_OK), f'missing executable: {path}')
     return path

@@ -763,7 +763,7 @@
                                        for f in result['files']))
     if identifier == 'D1':
         conditions['all_checks_pass'] = result['passed']
-    elif identifier == 'M1':
+    elif identifier == 'M1m':
         # Schema corruption can cause additional downstream failures.
         conditions['first_reason_schema'] = first == 'schema'
     elif identifier == 'M2':
@@ -775,25 +775,34 @@
             witness_unique=commits is not None and result['batch_commit_counts'] is not None,
             e_equals_c=e == c,
             c_exceeds_commits=commits is not None and c > commits)
-    elif identifier in ('M3', 'M4'):
-        expected = 'content-table' if identifier == 'M3' else 'content-txtype'
+    elif identifier in ('M3m', 'M4m'):
+        expected = 'content-table' if identifier == 'M3m' else 'content-txtype'
         conditions['reasons_only_' + expected] = reasons == [expected]
-    elif identifier == 'M5':
+    elif identifier == 'M5m':
         rows = result['rows']
+        mocc = [r for r in rows if r['source'] == 'cc/mocc/transaction.cc']
+        other = [r for r in rows if r['source'] != 'cc/mocc/transaction.cc']
         conditions.update(
-            nine_tpcc_consumers=(result['entry_count'] == len(rows) == 9 and
-                len({(r['source'], r['target']) for r in rows}) == 9 and
-                all(Path(r['source']).name.startswith('tpcc_') for r in rows)),
-            all_expanded_differ=bool(rows) and all(not r['modes']['expanded']['equal'] for r in rows),
-            all_include_activity_equal=bool(rows) and all(r['modes']['include_activity']['equal'] for r in rows))
+            all_21_entries=(result['entry_count'] == len(rows) == 21 and
+                len({(r['source'], r['target']) for r in rows}) == 21),
+            four_mocc_entries=(len(mocc) == 4 and
+                {r['target'] for r in mocc} ==
+                {'tpcc_mocc.exe', 'ycsb_mocc.exe', 'bomb_mocc.exe', 'sbomb_mocc.exe'}),
+            all_mocc_expanded_differ=bool(mocc) and all(
+                not r['modes']['expanded']['equal'] for r in mocc),
+            all_include_activity_equal=bool(rows) and all(
+                r['modes']['include_activity']['equal'] for r in rows),
+            other_17_entries_equal=len(other) == 17 and all(
+                r['modes'][mode]['equal'] for r in other
+                for mode in ('expanded', 'include_activity')))
     else:
         raise RuntimeError(f'unknown mutation: {identifier}')
     accepted = all(conditions.values())
     status = (('PASS' if accepted else 'FAILED') if identifier == 'D1' else
               'KILLED' if accepted else 'SURVIVED' if result['passed'] else 'WRONG_REASON')
     return dict(status=status, reasons=reasons, first_reason=first, conditions=conditions,
-                reason_match_policy=('first-reason (derived reasons allowed)' if identifier == 'M1' else
-                                     'preprocess modes' if identifier == 'M5' else
+                reason_match_policy=('first-reason (derived reasons allowed)' if identifier == 'M1m' else
+                                     'preprocess modes' if identifier == 'M5m' else
                                      'all checks' if identifier == 'D1' else 'exact reason set'))


@@ -803,19 +812,19 @@
          {'schema_version', 'anchor_status', 'note', 'entries'}, 'spec top-level key set mismatch')
     need(payload['schema_version'] == 't2854-mutation-spec/v1', 'spec schema_version mismatch')
     entries = payload['entries']
-    contracts = [('D1', 'C2', 'diag', 'pass'), ('M1', 'C2', 'run', 'schema'),
-                 ('M2', 'D1', 'run', 'witness'), ('M3', 'C2', 'run', 'content-table'),
-                 ('M4', 'C2', 'run', 'content-txtype'), ('M5', 'C2', 'preprocess', 'trace0-preprocess')]
-    need(isinstance(entries, list) and len(entries) == 6, 'spec must contain D1 and M1-M5')
+    contracts = [('D1', 'C3', 'diag', 'pass'), ('M1m', 'C3', 'run', 'schema'),
+                 ('M2', 'D1', 'run', 'witness'), ('M3m', 'C3', 'run', 'content-table'),
+                 ('M4m', 'C3', 'run', 'content-txtype'), ('M5m', 'C3', 'preprocess', 'trace0-preprocess')]
+    need(isinstance(entries, list) and len(entries) == 6, 'spec must contain D1, M1m, M2, M3m, M4m, M5m')
     for entry, contract in zip(entries, contracts):
         need(isinstance(entry, dict) and set(entry) ==
              {'id', 'base', 'file', 'anchor', 'replacement', 'target', 'kind', 'expected', 'intent'},
              f'spec entry key set mismatch: {contract[0]}')
         need(tuple(entry.get(k) for k in ('id', 'base', 'kind', 'expected')) == contract,
              f'mutation contract mismatch: {contract[0]}')
-        need(entry.get('file') == ('cc/silo/transaction.cc' if entry['id'] in ('M3', 'M4')
+        need(entry.get('file') == ('cc/mocc/transaction.cc' if entry['id'] in ('M1m', 'M3m', 'M4m', 'M5m')
                                  else 'include/tpcc.hh'), 'unexpected mutation file')
-        need(entry.get('target') == (None if entry['kind'] == 'preprocess' else 'tpcc_silo.exe'),
+        need(entry.get('target') == (None if entry['kind'] == 'preprocess' else 'tpcc_mocc.exe'),
              'unexpected mutation target')
         need(isinstance(entry.get('anchor'), str) and entry['anchor'] and
              isinstance(entry.get('replacement'), str) and entry['anchor'] != entry['replacement'],
@@ -828,7 +837,7 @@
     for name in ('repo-root', 'bundle', 'third-party-cache', 'policy', 'scratch-root',
                  'out-dir', 'keep-traces-dir', 'mutation-spec'):
         parser.add_argument('--' + name, type=Path, required=True)
-    for name in ('pin-oid', 'c1-oid', 'c2-oid'):
+    for name in ('base-oid', 'c1p-oid', 'c3-oid'):
         parser.add_argument('--' + name, required=True)
     args = parser.parse_args(argv)
     try:
@@ -837,7 +846,7 @@
                 need(value.is_absolute(), f'--{name.replace("_", "-")} must be absolute')
                 need(not value.is_symlink(), f'symlink input/output path: {value}')
                 setattr(args, name, value.resolve())
-        for name in ('pin_oid', 'c1_oid', 'c2_oid'):
+        for name in ('base_oid', 'c1p_oid', 'c3_oid'):
             need(re.fullmatch('[0-9a-f]{40}', getattr(args, name)), f'invalid {name}')
         need(args.scratch_root == Path('/scr'), 'scratch root must be /scr')
         for directory in (args.out_dir, args.keep_traces_dir):
--- verbatim/selftest.py
+++ probe/selftest.py
@@ -222,27 +222,39 @@
         cases.append(('M2-' + label, 'M2', {**m2, **update}, 'NOT_ACCEPTED'))
     cases.append(('D1-check-failed', 'D1', {**d1, 'passed': False, 'reasons': ['witness'],
                                           'first_reason': 'witness'}, 'NOT_ACCEPTED'))
-    for identifier, reason in [('M1', 'schema'), ('M3', 'content-table'), ('M4', 'content-txtype')]:
+    for identifier, reason in [('M1m', 'schema'), ('M3m', 'content-table'), ('M4m', 'content-txtype')]:
         base = dict(passed=False, first_reason=reason, reasons=[reason])
         cases.append((identifier + '-valid', identifier, base, 'KILLED'))
         extra = {**base, 'reasons': [reason, 'witness']}
         cases.append((identifier + '-derived-reason', identifier, extra,
-                      'KILLED' if identifier == 'M1' else 'NOT_ACCEPTED'))
-    cases.append(('M1-wrong-first', 'M1', dict(passed=False, first_reason='process',
+                      'KILLED' if identifier == 'M1m' else 'NOT_ACCEPTED'))
+    cases.append(('M1m-wrong-first', 'M1m', dict(passed=False, first_reason='process',
                                              reasons=['process', 'schema']), 'NOT_ACCEPTED'))
-    rows = [dict(source=f'cc/p{i}/tpcc_p{i}.cc', target=f'tpcc_p{i}.exe',
+    rows = [dict(source='cc/mocc/transaction.cc', target=f'{wl}_mocc.exe',
                  modes={'expanded': {'equal': False}, 'include_activity': {'equal': True}})
-            for i in range(9)]
+            for wl in ('tpcc', 'ycsb', 'bomb', 'sbomb')]
+    rows += [dict(source=f'cc/p{i}/tpcc_p{i}.cc', target=f'tpcc_p{i}.exe',
+                  modes={'expanded': {'equal': True}, 'include_activity': {'equal': True}})
+             for i in range(17)]
     m5 = dict(passed=False, first_reason='trace0-preprocess', reasons=['trace0-preprocess'],
-              entry_count=9, rows=rows)
-    cases.append(('M5-valid', 'M5', m5, 'KILLED'))
-    for label, mode, value in [('one-expanded-equal', 'expanded', True),
-                              ('one-include-different', 'include_activity', False)]:
+              entry_count=21, rows=rows)
+    cases.append(('M5m-valid', 'M5m', m5, 'KILLED'))
+    for label, index, mode, value in [
+            ('one-expanded-equal', 0, 'expanded', True),
+            ('one-include-different', 0, 'include_activity', False),
+            ('other-expanded-different', 4, 'expanded', False),
+            ('other-include-different', 4, 'include_activity', False)]:
         result = copy.deepcopy(m5)
-        result['rows'][0]['modes'][mode]['equal'] = value
-        cases.append(('M5-' + label, 'M5', result, 'NOT_ACCEPTED'))
-    cases.append(('M5-eight-consumers', 'M5', {**m5, 'rows': rows[:8], 'entry_count': 8}, 'NOT_ACCEPTED'))
-    cases.append(('M5-duplicate-consumer', 'M5', {**m5, 'rows': rows[:8] + rows[:1]}, 'NOT_ACCEPTED'))
+        result['rows'][index]['modes'][mode]['equal'] = value
+        cases.append(('M5m-' + label, 'M5m', result, 'NOT_ACCEPTED'))
+    cases.append(('M5m-twenty-consumers', 'M5m', {**m5, 'rows': rows[:20], 'entry_count': 20}, 'NOT_ACCEPTED'))
+    cases.append(('M5m-duplicate-consumer', 'M5m', {**m5, 'rows': rows[:20] + rows[:1]}, 'NOT_ACCEPTED'))
+    for label, index, field, value in [
+            ('wrong-source', 0, 'source', 'cc/silo/transaction.cc'),
+            ('wrong-target', 0, 'target', 'tpcc_silo.exe')]:
+        result = copy.deepcopy(m5)
+        result['rows'][index][field] = value
+        cases.append(('M5m-' + label, 'M5m', result, 'NOT_ACCEPTED'))
     failures = []
     for name, identifier, result, expected in cases:
         verdict = mutation_verdict(identifier, result)
@@ -276,3 +288,7 @@
             failures.append((name, expected, accepted))
     print('harness selftest cases: ' + ', '.join(c[0] for c in cases + spec_cases))
     return len(cases) + len(spec_cases), failures
+
+
+if __name__ == '__main__':
+    raise SystemExit(run())
--- verbatim/mutation-spec.template.json
+++ probe/mutation-spec.template.json
@@ -1,29 +1,29 @@
 {
   "schema_version": "t2854-mutation-spec/v1",
-  "anchor_status": "checked-against-author-a-worktree",
-  "note": "Parent must recheck every anchor against final C2 commit bytes; M2 is checked after D1. No C++ build has been run by author B.",
+  "anchor_status": "provisional-mocc-anchors; 親が C3 の実 bytes で確定する",
+  "note": "親が C3 の実 bytes で確定する。M1m/M3m/M4m are projected from the silo precedent; M5m uses the existing DELETE-side #line 1187. Recheck every anchor occurs once, including D1/M2; check M2 after D1. No C++ build has been run by author B.",
   "entries": [
     {
       "id": "D1",
-      "base": "C2",
+      "base": "C3",
       "file": "include/tpcc.hh",
       "anchor": "#if !TRACE\n#line 110\n    if (loadAcquire(tx.quit_)) return;\n#endif\n#line 111\n",
       "replacement": "#if TRACE\n    static thread_local unsigned long long t2854_successes = 0;\n    if (++t2854_successes == 1000) {\n      std::fprintf(stderr, \"t2854-diag-quit\\n\");\n      storeRelease(const_cast<bool&>(tx.quit_), true);\n    }\n#endif\n#if !TRACE\n#line 110\n    if (loadAcquire(tx.quit_)) return;\n#endif\n#line 111\n",
-      "target": "tpcc_silo.exe",
+      "target": "tpcc_mocc.exe",
       "kind": "diag",
       "expected": "pass",
       "intent": "Set quit after the 1000th successful commit on a worker, before the old quit/count boundary. Require stderr diagnostic marker and a worker trace with at least 1000 C frames in both D1 and M2."
     },
     {
-      "id": "M1",
-      "base": "C2",
-      "file": "include/tpcc.hh",
-      "anchor": "    izanagi_trace::set_tpcc_tx_type(get_tx_type(query.type));\n",
-      "replacement": "",
-      "target": "tpcc_silo.exe",
+      "id": "M1m",
+      "base": "C3",
+      "file": "cc/mocc/transaction.cc",
+      "anchor": "  const std::uint32_t izanagi_tx_type = izanagi_trace::tpcc_tx_type();\n",
+      "replacement": "  const std::uint32_t izanagi_tx_type = 0U;\n",
+      "target": "tpcc_mocc.exe",
       "kind": "run",
       "expected": "schema",
-      "intent": "Leave workload context zero, causing legacy v2 C records in TPC-C."
+      "intent": "Ignore the TPC-C context in mocc, causing legacy v2 C records in TPC-C."
     },
     {
       "id": "M2",
@@ -31,43 +31,43 @@
       "file": "include/tpcc.hh",
       "anchor": "#if !TRACE\n#line 110\n    if (loadAcquire(tx.quit_)) return;\n",
       "replacement": "#if 1\n#line 110\n    if (loadAcquire(tx.quit_)) return;\n",
-      "target": "tpcc_silo.exe",
+      "target": "tpcc_mocc.exe",
       "kind": "run",
       "expected": "witness",
       "intent": "After applying D1, restore the old post-commit quit return before counting."
     },
     {
-      "id": "M3",
-      "base": "C2",
-      "file": "cc/silo/transaction.cc",
+      "id": "M3m",
+      "base": "C3",
+      "file": "cc/mocc/transaction.cc",
       "anchor": "      izanagi_trace::emit_write_v3(\n          thid_, izanagi_txid, get_storage(we.storage_),\n",
       "replacement": "      izanagi_trace::emit_write_v3(\n          thid_, izanagi_txid, (get_storage(we.storage_) == 6 ? 5 : get_storage(we.storage_)),\n",
-      "target": "tpcc_silo.exe",
+      "target": "tpcc_mocc.exe",
       "kind": "run",
       "expected": "content-table",
       "intent": "Map table 6 to table 5 only at the v3 W emitter; preserve schema and witness."
     },
     {
-      "id": "M4",
-      "base": "C2",
-      "file": "cc/silo/transaction.cc",
+      "id": "M4m",
+      "base": "C3",
+      "file": "cc/mocc/transaction.cc",
       "anchor": "        read_set_.size(), write_set_.size(), 0, 0, izanagi_tx_type);\n",
       "replacement": "        read_set_.size(), write_set_.size(), 0, 0, (izanagi_tx_type == 1 ? 2 : (izanagi_tx_type == 2 ? 1 : izanagi_tx_type)));\n",
-      "target": "tpcc_silo.exe",
+      "target": "tpcc_mocc.exe",
       "kind": "run",
       "expected": "content-txtype",
       "intent": "Swap 1 and 2 only in the v3 C emitter; operation signatures remain unchanged."
     },
     {
-      "id": "M5",
-      "base": "C2",
-      "file": "include/tpcc.hh",
-      "anchor": "#line 56\n",
+      "id": "M5m",
+      "base": "C3",
+      "file": "cc/mocc/transaction.cc",
+      "anchor": "#line 1187\n",
       "replacement": "",
       "target": null,
       "kind": "preprocess",
       "expected": "trace0-preprocess",
-      "intent": "Delete the setter's logical-line restoration; compare all nine TPC-C consumers without building."
+      "intent": "Delete the DELETE-side logical-line restoration; compare all 21 entries without building. All four mocc transaction entries must differ only in expansion; the other 17 entries must match in both modes."
     }
   ]
 }
```

2) 自己確認の結果

実行場所は `pegasus02`。以下は probe ディレクトリで実行しました。

| command | rc | 結果 |
|---|---:|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 selftest.py` | 0 | **197/197 passed、failures=0** |
| `PYTHONPYCACHEPREFIX=/tmp/t2854-mocc-b-pycache python3 -m py_compile run_probe.py v3check.py selftest.py` | 0 | 3ファイル成功 |
| `python3 -B run_probe.py --help` | 0 | 新しい3個のOID引数を表示 |
| `python3 -B -c 'from run_probe import load_spec; print([e["id"] for e in load_spec("mutation-spec.template.json")])'` | 0 | 指定順の6件を受理 |

追加の `python3 -B -c` 検査も rc=0：

- 全6 entryの `id/base/kind/expected/file/target` を個別に壊した**36負例をすべて拒否**。
- 環境に `IZANAGI_MOCC_G2_WITNESS=1` を設定しても `clean_env()` が除外。
- 前 wave との AST 比較で、変更関数が意図した7関数だけであることを確認。
- `v3check.py` の bytes 完全一致、構造検査の自己試験本文の完全一致を確認。

`v3check.py` SHA-256：

```text
3c787a6487ecd68c782aa6ba830314c783b13af3acb26fefaf2a54c541c5749f
```

補助確認として実行した次の参照は rc=128 でした。この `external/ccbench` では指定OIDから当該パスを取得できず、C1' の実 bytes の追加確認はできていません。

```text
git -C external/ccbench show 6aa7a58fccff9efa218067d1b7ce83026a75357d:cc/mocc/transaction.cc
```

必読の指定ファイルはすべて読めています。silo の先例 `a6f2c7410d58ad140a62b11cc1beab29bfcd191b` の差分参照は成功しました。

**実装済み・未実走**：実bundleによるC0、TRACE=0前処理・binary、TRACE=1構文検査、TPC-C/YCSB走行、verifier認定、6変異の実走。CCBench build・benchmark・計算ノードへの投入は行っていません。C8のsuperproject受入も未実走です。

3) 裁定 §3・§4 から外れた箇所と理由

なし。

`selftest.py` の直接実行入口追加は、依頼された `python3 selftest.py` で実際に自己試験を走らせるためです。残る `silo` のsource/target文字列は、M5mが誤った対象を拒否する自己試験の負例だけです。

4) 親が C3 の実 bytes で確定すべき anchor

以下はJSON文字列表記です。空白・改行を含め、適用対象で出現がちょうど1回となることを確認してください。

| ID | file／適用時点 | anchor |
|---|---|---|
| D1 | `include/tpcc.hh`／C3 | `"#if !TRACE\n#line 110\n    if (loadAcquire(tx.quit_)) return;\n#endif\n#line 111\n"` |
| M1m | `cc/mocc/transaction.cc`／C3 | `"  const std::uint32_t izanagi_tx_type = izanagi_trace::tpcc_tx_type();\n"` |
| M2 | `include/tpcc.hh`／D1適用後 | `"#if !TRACE\n#line 110\n    if (loadAcquire(tx.quit_)) return;\n"` |
| M3m | `cc/mocc/transaction.cc`／C3 | `"      izanagi_trace::emit_write_v3(\n          thid_, izanagi_txid, get_storage(we.storage_),\n"` |
| M4m | `cc/mocc/transaction.cc`／C3 | `"        read_set_.size(), write_set_.size(), 0, 0, izanagi_tx_type);\n"` |
| M5m | `cc/mocc/transaction.cc`／C3 | `"#line 1187\n"` |

D1/M2は前 wave の文字列を維持。M1m/M3m/M4mはsilo先例からの見込み、M5mは指定されたDELETE側の行復元です。`anchor_status` と `note` に「親が C3 の実 bytes で確定する」と明記しました。

## 総括

- mocc用のcommit・target・verifier・6変異契約を実装。M5mは21 entry全件を厳密に判定。
- 自己試験197件、構文確認、help、spec読込、契約負例36件は成功。
- C0〜C6の実bundle・コンパイル・走行確認とC8受入は未実走。
- 親は全anchorの実bytes・一意性を確定し、baseに `68106660686232781bca3be792a750d3e19d7a8a` を指定して計算ノードで確認してください。