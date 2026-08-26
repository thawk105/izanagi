## 契約と実装の対応表

| 順 | 確定契約 | 実装箇所 | 判定 |
|---:|---|---|---|
| 1 | `_validated_root()` | [`_committed_ratification_digests()` 先頭](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:517) | 一致 |
| 2 | shallow が exact `false` 以外なら拒否 | [`_assert_full_history_repository()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:274) | 一致。`b"false\n"` と完全比較 |
| 3 | 実効 graft 拒否、replace ref は拒否しない | [同 helper の graft 検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:281) | 一致。空行と先頭 `#` だけを除外 |
| 4 | HEAD を解決 | [`_head_commit()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:318) | 一致。40 桁 lowercase hex、1 行、末尾 LF を検査 |
| 5 | HEAD の到達可能 DAG と実親を列挙 | [`_reachable_commit_parents()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:335) | 一致。path 制限なし。全親が列挙集合内にあることも検査 |
| 6 | 全 commit の entry を 1 回の batch で取得 | [`_ledger_blob_oids()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:385) | 部分一致。行数、末尾 LF、OID、type、size の字句は検査するが、成功応答と query の対応は位置だけに依存 |
| 7 | type 検査後、異なる blob を個別取得 | [`_rows_by_blob_oid()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:496) | 部分一致。OID 再利用は正しい。batch の size は捨てられ、個別取得 byte 数と照合されない。mode は契約より強い exact allowlist |
| 8 | 各 commit の削除、導入、欠落、追加数、部分列検査 | [commit loop](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:534) | 一致。指定された順序どおり。親数判定も台帳親数ではなく実親数 |
| 9 | 到達可能 DAG 全体の導入一意性 | [導入収集と件数検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:534) | 一致。全列挙 commit が対象。0 件は従来どおり台帳不在として扱い、2 件以上を拒否 |
| 10 | HEAD の行集合を `frozenset` で返す | [返却部](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:579) | 一致 |

追加の静的照合結果:

- 既存 4 メッセージは逐語で維持されている。
- 差分上、既存テスト本文の変更・削除はない。既存 10 test 関数のうち 1 件が 3 parameter node を持つため、既存 12 node という報告と整合する。
- `_load_rows` の実質差分は `splitlines()` から `split(b"\n")[:-1]` への変更だけ。他の schema、canonical JSON、重複 digest 検査は維持され、CR/CRLF を新たに拒否する方向である。
- production の `subprocess.run` は [`_git()` 内の 1 か所](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:201)だけ。spawn inventory も [exact 1 件](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/tests/test_ccbench_spawn_sites.py:81)のまま。
- pytest は実行していない。

## 所見

### must-fix: batch の成功応答が query に結び付いていない

[`batch_object()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:414)は `missing` の場合だけ query 文字列を照合する。成功行は `<oid> <type> <size>` しか持たず、[`lines[index * 2]`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:443)をその commit の結果とみなす。したがって行数を保った成功応答の順序ずれを検出できない。

`ambiguous` など通常の 2 field 異常応答、行数不一致、末尾 LF 欠落は拒否できている。穴は「成功形のまま別 query の応答と入れ替わる」場合である。固定 `/usr/bin/git` の通常 batch protocol は入力順で返すため、commit だけではこのずれを発生させられないが、今回求められた fail-closed な出力対応検査には達していない。

成果物影響: 応答 block が入れ替わると HEAD に無い digest が批准済み集合へ入り、その digest の certified 選択が受理され、レポートの批准参照が実 HEAD 台帳と食い違う。

### must-fix: batch の object size を取得後の bytes と照合していない

[`batch_object()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:414)は size の十進表現だけを検査し、その値を返さない。[個別 blob 取得](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:496)でも `len(stdout)` を照合しない。成功扱いの `cat-file blob` 出力が canonical 行の境界で短くなった場合、末尾 LF 検査にも通る。

通常の Git 成功応答が切れる経路は見つからないが、exact 出力検査としては明白な未使用値であり、上の位置対応問題と同じく異常出力時に fail-open になる。

成果物影響: 2 行導入 blob が 1 行目直後で短く観測されると本来の拒否集合が受理集合へ移り、残った digest に対応する certified 選択が通る。

### should-fix: tree mode の exact allowlist は確定契約より強い

[tree entry 検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:462)は mode を `100644` または `100755` に限定する。確定契約は commit 間の mode 比較を入れず、entry が blob であることを要求している。

symlink も object type 自体は blob なので mode の分類は必要だが、exact 2 値に限定することまでは契約にない。raw tree に `100664` などの非 canonical な regular-file mode と正しい blob OID がある場合、Git が blob と解決できても実装は拒否する。fsck 不正 tree を一律拒否する意図なら、その強化を契約へ明記すべきである。

成果物影響: 契約上は批准済みである regular blob 履歴が `not a blob in committed history` になり、certified 選択が偽赤となりレポートの拒否理由も変わる。

### nit: batch 異常系の regression test がない

[追加テスト群](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/tests/test_enforcement_source_ratification.py:432)は実履歴形を広く覆うが、batch の行数不一致、順序ずれ、`ambiguous`、size 不一致を直接注入するテストはない。

成果物影響: 現行成果物は直ちに変わらないが、成功応答の誤対応や短縮取得を将来も検出できず、上記の誤受理集合が固定される。

## 構成した反例履歴

### 1. 成功応答の順序ずれで不正履歴を受理

実際の履歴を次とする。`A`、`B`、`C` は異なる canonical digest。

```text
R: 台帳なし
|
I: [A]          正常な導入
|
J: [A, B, C]    1 commit で 2 行追加。本来ここで拒否
|
H: [A, B]       C を削除。本来ここでも拒否。HEAD
```

batch query は `H, J, I, R` の順になる。`H` と `J` の ledger 応答と directory 応答を block 単位で入れ替えると、実装内の対応は次になる。

```text
I -> [A]
J -> [A, B]
H -> [A, B, C]
```

実装からは「1 行導入、B を 1 行追加、C を 1 行追加」という正常な履歴に見え、HEAD の集合として `{A,B,C}` を返す。実 HEAD の台帳は `{A,B}` である。

これは通常の固定 Git が順序保証を守る限り commit だけでは発火しない。しかし、処理自身は順序ずれを検出できない。

### 2. byte 数不一致で複数行導入を受理

```text
R: 台帳なし
|
I: [A, B]       導入時 2 行。本来拒否。HEAD
```

batch-check は正しい 2 行分の size を返す。その後の `cat-file blob <oid>` が成功扱いのまま `A` の行と LF までしか返さなければ、`_load_rows` は正常な 1 行 blob とみなし、導入を受理して `{A}` を返す。取得 size を保存して比較すれば拒否できる。

### 3. 契約より強い mode 検査による偽赤

```text
R: 台帳なし
|
I: mode=100664、object type=blob、内容=[A]
```

確定契約の type と行遷移だけなら 1 行導入として受理される。実装は mode が exact allowlist 外なので拒否する。これは誤受理ではなく受理集合の過剰縮小である。

通常の `/usr/bin/git` が規定 protocol を守る条件では、commit 配列だけで契約違反履歴を受理させる経路は見つからなかった。独立導入、履歴中間の違反、親行欠落、追加数、並べ替えはいずれも到達可能 DAG 全体で拒否される。

## 総括

評価順 1〜10の履歴規則そのものはほぼ確定契約どおりで、純粋な Git 履歴だけによる検出力後退は見つからない。既存メッセージ、既存 12 test node、`_load_rows` の他の検査、subprocess 起動口も維持されている。

ただし Git 出力を exact に扱う境界には、成功応答の query 対応と取得 byte 数の 2 つの穴がある。どちらも異常出力時には批准集合そのものを変え、誤った certified 選択へ到達するため must-fix と判定する。加えて exact mode allowlist は確定契約より強く、契約への追記か実装の一般化が必要である。