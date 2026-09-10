静的計画では、332 bytes を捻出し、候補 (a)〜(d) を合計 303 bytes の増分で全件採録できます。最終見積りは 25,158 / 25,200 bytes です。

以下の byte 数は raw UTF-8、置換対象末尾の LF を含みます。pytest、`check_docs.py` は実走していません。

## 1. 捻出プラン

### 1-A. DW-M08 を tool pointer へ縮約

対象: [mutation.md:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/mutation.md:51)

before — 383 bytes:

```text
harness は rc に加え赤くなった test node を毎回記録する。pytest は `-rf` を指定し、
node 抽出は F71 に従う（正本は job stdout 全文、行前置と ANSI を除去、` - ` 無しは行末まで、
rc≠0 で 0 件は fail-closed 停止）。
事前登録の期待 node と記録 node は突き合わせ前に同じ形式へ正規化する（F33）。
```

after — 124 bytes:

```text
rc と失敗 node の記録・抽出・期待集合照合は `tools/mutation_harness.py` を正本とする（F33/F71）。
```

差分: **−259 bytes**

削られた義務の担い手は次のとおりです。

| 義務 | 機械強制 | 現在の pin / 追加予定 |
|---|---|---|
| baseline・各 mutation の rc / failed node 記録 | field 閉包 [mutation_harness.py:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/mutation_harness.py:56)、記録生成 [同:1232](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/mutation_harness.py:1232)、[同:1302](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/mutation_harness.py:1302)、再検証 [同:1494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/mutation_harness.py:1494)、[同:1567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/mutation_harness.py:1567) | 既存 [test_mutation_harness.py:205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/orchestrator/tests/test_mutation_harness.py:205) |
| `-rf` 必須 | [mutation_harness.py:1881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/mutation_harness.py:1881) | **現状は無い**。工程 1 で専用 test を追加 |
| canonical job stdout の使用 | baseline / mutation [mutation_harness.py:1210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/mutation_harness.py:1210)、[同:1290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/mutation_harness.py:1290) | dispatch console との分離は既存 [test_mutation_harness.py:968](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/orchestrator/tests/test_mutation_harness.py:968) |
| ANSI・行前置除去 | [mutation_harness.py:791](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/mutation_harness.py:791) | 既存 [test_mutation_harness.py:257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/orchestrator/tests/test_mutation_harness.py:257) |
| `" - "` が無い行は行末まで node | [mutation_harness.py:816](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/mutation_harness.py:816) | **現状は無い**。工程 1 で追加 |
| rc=1 かつ node 0 件を `PARSE_ERROR` | mutation [mutation_harness.py:1177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/mutation_harness.py:1177)、baseline [同:1220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/mutation_harness.py:1220) | **`failed=[]` の pin は無い**。両分岐へ追加 |
| 期待・観測 node の同一正規化 | [mutation_harness.py:798](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/mutation_harness.py:798)、[同:1191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/mutation_harness.py:1191)、[同:1293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/mutation_harness.py:1293) | **同値表記を照合する pin は無い**。工程 1 で追加 |
| 期待集合との完全一致 | [mutation_harness.py:1191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/mutation_harness.py:1191) | 既存の strict superset [test_mutation_harness.py:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/orchestrator/tests/test_mutation_harness.py:352)、strict subset [同:365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/orchestrator/tests/test_mutation_harness.py:365)、parameter exact [同:341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/orchestrator/tests/test_mutation_harness.py:341) |

この置換は新規 pin が入るまで実施しません。

### 1-B. DW-O19 の重複義務を DW-S01 へ一本化

対象: [operations.md:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/operations.md:112)

before — 73 bytes:

```text
段 1 前提実測は本走でないが、この復元規律に従う。
```

after — 0 bytes:

```text
```

差分: **−73 bytes**

義務の担い手: [core.md:32-35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/core.md:32) が、段 1 前提実測を `DW-O19` の復元規律へ明示的に束縛しています。DW-S01 は段 1 で無条件に読むため、義務は消えず一本化されます。

これは「安全義務ではない」という判断ではありません。安全義務の重複記載を load-bearing な無条件節へ集約する案です。`DW-O19` の H2 と残りの復元契約は維持します。

捻出合計: **259 + 73 = 332 bytes**

## 2. テスト化プラン

追加先はすべて [test_mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/orchestrator/tests/test_mutation_harness.py) です。

| 現在の挿入 anchor | nodeid 案 | 対象と assert | 既存との差、純増検出力 |
|---|---|---|---|
| parser test 後の現行 `:266` | `test_failed_node_parser_uses_line_end_without_detail_separator` | `FAILED tests/test_gate.py::test_gate[one]\n` を `_failed_nodes()` に渡し、完全 node 1 件を assert | 既存 `:257` は必ず `" - AssertionError"` を含むため、`:824-825` の fallback を削除しても検出できない。**純増あり** |
| fake-runner test 後の現行 `:327` | `test_main_rejects_missing_rf_before_runner_and_ledger` | `_argv()` から `-rf` を除き、`HarnessError` の `"DW-M08 の -rf"`、runner call なし、ledger なしを assert | 既存 fake-runner test は `-rf` を含み entrypoint identity だけを検査する。**純増あり** |
| exact-match 群の手前、現行 `:340` | `test_expected_and_failed_nodes_share_normalization` | expected=`./tests/...`、failed=`<repo絶対path>/tests/...`、rc=1 で `_observed_status()=="KILLED"` | 既存群は「異なる node を混同しない」性質を検査するが、「異なる表記の同一 node」を揃える性質は検出しない。**純増あり** |
| abnormal-rc test 後の現行 `:440` | `test_nonzero_normal_rc_without_failed_nodes_is_parse_error` | rc=1、`failed=[]`、期待 node 非空で `_observed_status()=="PARSE_ERROR"` | 既存 `:430` は rc=2/3/5 かつ failed node あり。正常 pytest failure rc=1 の node 抽出失敗を検出しない。**純増あり** |
| 同じく現行 `:440` 付近 | `test_baseline_nonzero_rc_without_failed_nodes_is_parse_error` | `_run_tests` を rc=1・空 stdout へ差し替えて `_baseline()` を呼び、status=`PARSE_ERROR`、rc=1、`failed_nodes=[]` を assert | `_baseline()` は `_observed_status()` と別の分岐を持つため、前項だけでは baseline 側の弱化を検出できない。**純増あり** |

追加しないもの:

- 完全集合一致の専用 test は既に strict superset / strict subset の両方向があります。さらに足しても**純増検出力なし**です。
- ANSI・relay prefix 除去も既存 `test_failed_node_parser_keeps_parameter_and_full_node` が検出します。
- rc / failed-node field の存在は、既存 end-to-end test が exact field validator を通しているため、新 nodeid の純増検出力はありません。

## 3. 採録プラン

### (a) 残留 `.done` の再利用禁止

対象: [operations.md:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/operations.md:9)

before — 101 bytes:

```text
投入前に prompt の非空を検査し、完了は `.done` と exit code だけで判定する。
```

after — 167 bytes:

```text
投入前に prompt の非空を検査し、既存 `.done` は消さず再利用せず、再投入を止め、完了は `.done` と exit code だけで判定する。
```

予算増分: **+66 bytes**

候補単独で表示した場合は次の 70 bytes です。

```text
既存 `.done` は消さず再利用せず、再投入を止める。
```

既存行へ融合するため実増分は 66 bytesです。旧 draft 130 bytes 中の「前回分の exit code を誤読する」は理由説明であり追加義務ではないため省きました。「消さない・再利用しない・停止する」はすべて残っています。

### (b) 待ち手規約 3 条

挿入先: [operations.md:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/operations.md:12) の後

本文案 — **94 bytes**:

```text
待ち手は 1 条件 1 本。生産者と共に止め、その死も待ち条件とする。
```

旧 draft は 263 bytes でした。最小化の根拠は次のとおりです。

- 「通知のたびに作り直さない」は「1 条件 1 本」の具体例で、独立した第 4 義務ではありません。
- 「終了語だけを待つ条件は沈黙したまま残る」は理由説明です。
- 「監視対象を書く process」を「生産者」と抽象化しても対象範囲は狭まりません。
- 「共に止める」と「その死も待ち条件」は、第 2・第 3 条を別々に保持します。

4 候補中で最長ですが、旧 draft 比 **−169 bytes** です。

### (c) 機構名でも見送り裁定を検索

挿入先: [core.md:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/core.md:40) の後

本文案 — **79 bytes**:

```text
対象機構名の語でも見送り台帳を検索してから着手する。
```

予算増分: **+79 bytes**

### (d) 保留裁定の解除条件を条文単位で棚卸し

同じく [core.md:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/core.md:40) の後、(c) に続けて挿入します。

本文案 — **64 bytes**:

```text
保留裁定の解除条件は条文単位で棚卸しする。
```

予算増分: **+64 bytes**

採録増分合計:

- (a) 実増分 66
- (b) 94
- (c) 79
- (d) 64
- 合計 **303 bytes**

要求された (a)〜(d) は全件入ります。親 brief が挙げる別候補 `[T-595] run_sN.sh 起動形` は今回の本文指定外で、採録後の operations 余白が 2 bytes しかないため追加回収なしには入りません。

## 4. 工程順

不変条件を満たす順序は次です。

1. Codex author が `test_mutation_harness.py` に上記 5 nodeid を追加する。docs はまだ変更しない。
2. 親が追加 nodeid、既存の exact-set / parser pin を実測する。この回答では結果を主張しない。
3. pin が確認された実装 commit を先に確定する。赤または未実走なら DW-M08 は現行 prose のまま止める。
4. その commit を祖先に持つ状態で、親が M08 pointer 化、O19 重複削除、(a)〜(d) の採録を行う。
5. 親が関連検査と `tools/check_docs.py` を実測する。

したがって、機械強制を指す prose 削除が test pin より先に現れる状態は作りません。

## 5. 予算の事後検証

| 文書 | 現在 | 変更 | 変更後 | 個別 cap | 余白 |
|---|---:|---:|---:|---:|---:|
| core | 8,534 | +79 +64 | **8,677** | 9,600 | 923 |
| workers | 4,668 | 0 | **4,668** | 5,000 | 332 |
| mutation | 3,674 | −259 | **3,415** | 3,750 | 335 |
| operations | 8,311 | −73 +66 +94 | **8,398** | 8,400 | 2 |
| 合計 | 25,187 | −332 +303 | **25,158** | 25,200 | 42 |

3 gate の静的判定:

1. 個別 cap: 4 文書すべて [check_docs.py:176-181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/check_docs.py:176) 以下です。
2. aggregate: **25,158 ≤ 25,200**。[check_docs.py:3509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/check_docs.py:3509) の述語を満たします。
3. cap 総和 110%: cap は変更しないため **26,750 ≤ 27,720**、余裕 970 bytes。[check_docs.py:3342](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/check_docs.py:3342) の述語を満たします。

cap・aggregate・110% は既存 test でも固定されています: [test_check_docs.py:1770](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/orchestrator/tests/test_check_docs.py:1770)、[同:1790](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/orchestrator/tests/test_check_docs.py:1790)、[同:2093](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/orchestrator/tests/test_check_docs.py:2093)。

H2、予算値、`.claude/commands/dev-wave.md`、可読性用空白は変更しません。

## 総括

- 捻出合計: **332 bytes**
- 採録増分: **303 bytes**
- 変更後 aggregate: **25,158 / 25,200 bytes**
- 採録できる候補: **(a) `.done`、(b) 待ち手 3 条、(c) 機構名検索、(d) 条文単位棚卸しの全件**
- 入らない候補: 指定された (a)〜(d) にはなし。別候補 `[T-595] run_sN.sh` は未採録
- 親 brief の誤り:
  - [brief.md:35-37](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t597-budget/brief.md:35) の「完全一致も専用 pin が無い」は誤りです。strict superset / subset の専用 test が既にあります。
  - したがって [brief.md:77-79](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t597-budget/brief.md:77) の「完全一致分岐を消しても既存テストが緑」は成立しません。
  - 逆に brief が未列挙だった未 pin 性質として、`" - "` 無し fallback、期待・観測の同一正規化、baseline 側の rc=1/node 0 件分岐があります。DW-M08 全体を pointer 化するなら、これらも先に pin する必要があります。