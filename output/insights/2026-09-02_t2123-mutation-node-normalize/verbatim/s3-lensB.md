## 検査項目 1〜8 の結果

**1. 座の網羅**

`tools/mutation_harness.py` の node 文字列に関する比較、照合、集合演算を独立走査した結果は次のとおり。

| 座 | file:line | 役割 | 評価 |
|---|---|---|---|
| spec raw 重複・空集合契約 | `tools/mutation_harness.py:593-605` | `set(expected_nodes)`、KILLED/非KILLED の空集合契約 | plan は `:593-600` に言及。変更不要 |
| registration key 重複 | `tools/mutation_harness.py:1109-1113` | `_match_key` 後の重複拒否 | A8、plan とも対象 |
| failed node dedup | `tools/mutation_harness.py:1253-1255` | 観測表記の同一文字列を `not in` で重複除去 | A3 の関数内。変更不要 |
| collected node dedup | `tools/mutation_harness.py:1266-1270` | collection の観測表記を `not in` で重複除去 | A4 の関数内。変更不要 |
| flaky hold 交差 | `tools/mutation_harness.py:1309-1310` | expected key と hold 集合の交差 | A9。held 側も key 化する plan が必要かつ正しい |
| 初回 collection 差集合 | `tools/mutation_harness.py:1469-1476` | expected − collected | A5。両側 `_match_key` 化が必要 |
| runtime 完全集合比較 | `tools/mutation_harness.py:2011-2013` | failed key `==` expected key | A7。A2 の変更で直る |
| runtime への入力 | `tools/mutation_harness.py:2186-2193` | failed 抽出、expected 正規化、`_observed_status` 呼出し | plan の A2 変更が到達する |
| resume collection raw 照合 | `tools/mutation_harness.py:2376-2378` | 台帳と artifact の順序込み完全一致 | plan が維持を明記。key 化してはならない |
| resume collection 実在検査 | `tools/mutation_harness.py:2379-2388` | expected − collected | A6。両側 `_match_key` 化が必要 |
| baseline replay | `tools/mutation_harness.py:2434-2446` | raw failed list 完全一致、空集合判定 | A1〜A9 と plan の明示一覧外。変更不要 |
| mutation record の spec 照合 | `tools/mutation_harness.py:2476-2494` | `expected_nodes` を registration と raw 完全一致 | 明示一覧外。表記保存のため変更不要 |
| mutation record の failed 照合 | `tools/mutation_harness.py:2507-2526` | raw failed list 一致後、A7 で status 再導出 | raw 比較は変更不要。A2 は再導出にも効く |
| resume registration 照合 | `tools/mutation_harness.py:2641-2644` | `registration_preflight` の深い完全一致 | 明示一覧外。表記保存のため変更不要 |
| baseline 最終 gate | `tools/mutation_harness.py:3173-3174` | `failed_nodes == []` | 明示一覧外。変更不要 |

A1〜A9 と段 2 plan に無い行単位の座は `:2435`、`:2493` の `expected_nodes`、`:2511`、`:2641`、`:3173` です。ただし、いずれも観測値、spec、台帳の raw 完全性を守る座であり、接尾辞正規化を入れる対象ではありません。意味比較の座に取り残しはありません。

**2. 四方向の経路**

plan 適用後は四方向とも通ります。

- 期待=接尾辞なし × 記録=接尾辞あり:
  初回 collection は `:1469-1476` で双方を base key 化。実走 command は変更されず `:2164-2172`、接尾辞付き failure を `:1241-1255` で記録し、`:2011-2013` で双方を base key 化して `KILLED`。
- 期待=接尾辞あり × 記録=接尾辞あり:
  `:1109-1117` は期待表記を保持する一方、初回 collection は key 比較で通過。runtime は `:2011-2013` で両方から同じ接尾辞を落として `KILLED`。
- 期待=接尾辞あり × collection=接尾辞なし:
  初回は `:1469-1476`、resume は `:2379-2388` の両側 key 化で一致する。
- 期待=接尾辞なし × collection=接尾辞なし:
  同じ二座で従来どおり同一 key になる。

段 2 plan の正例 1 が二番目と三番目、正例 2 が一番目と四番目を一続きの実経路で覆います。四方向の欠落はありません。

**3. resume 経路**

A6 は直っています。`_load_resume_ledger` は `tools/mutation_harness.py:2646-2655` から `_validate_collection_record` を呼び、artifact と台帳の raw 一致 `:2376-2378` を維持した後、期待 node の実在だけを `:2379-2388` で key 比較します。

さらに過去 mutation record も `:2684-2695` から `:2514-2523` を経て共通 `_observed_status` へ戻るため、A2 の新しい key が過去の KILLED/MISMATCH 再導出にも効きます。plan の resume 正例はこの二層を通ります。

**4. `tools/mutation_fanout.py`**

`expected_nodes`、`failed_nodes`、`collected_nodes`、nodeid、node key を検索して 0 件でした。

- shard spec の内容は `tools/mutation_fanout_contract.py:552-565` が mutation object をそのまま分配し、fanout 本体は assignment と path だけを扱います。
- fanout 本体は wrapper argv を組み立てるだけです。`tools/mutation_fanout.py:656-688`
- child 回収は rc のみです。`tools/mutation_fanout.py:741-785`
- 統合は `merge_group` への委譲です。`tools/mutation_fanout.py:1745-1752`
- shard 間の `collected_nodes` 比較 `tools/mutation_fanout_contract.py:1427-1437` は同一 collection 証拠の順序込み raw 一致であり、expected node との意味比較ではありません。

したがって `mutation_fanout.py` 本体は変更不要です。一方、直接 consumer の `mutation_fanout_contract.py:335-352,899-903` は独立した status/collection 比較器を持つため、plan の同形修正は必須です。

**5. 実在する `@` nodeid**

`orchestrator/tests/acceptance_duration_ledger.json` の 19,519 nodeid を全件走査しました。

- `@` を含むもの: 26 件
- parametrize ID 内: 25 件
- xdist group 接尾辞: 1 件
- その他: 0 件

parametrize ID 25 件には、catalog ID `:143-145`、コード片や `\n` エスケープを含むもの `:690-692,1127,8608`、`::`、複数 `@`、入れ子括弧を含む scheduler oracle `:2037-2046` が含まれます。唯一の接尾辞は `:16709` の `...explicit_binding@real-repo` です。

実 collection の group 名は独立 golden の六種に閉じています。`orchestrator/tests/test_real_repo_serialization.py:247-255,1176-1205`。いずれも `@` を含みません。group 名自体に `@` を含む定義は 0 件です。

**6. `_collected_nodes` の巻き込み**

誤除去は起きません。

- `_collected_nodes` は `tools/mutation_harness.py:1262-1269` で `::` を含む一行全体を `_normalize_node` へ渡します。
- `_normalize_node` は最初の `::` だけを path/test 境界に使うため、parametrize ID 内の追加 `::` は test 部分に残ります。`:1230-1234`
- ledger の改行付きコード片は実改行ではなく `\n` 文字列として nodeid 一行内に存在します。`:690-692,1127`
- 25 件すべてで最後の `@` は外側の最後の `]` より前です。新規規則は何も削りません。
- `[param@value]@group` だけは group 側の `@` が最後の `]` より後になり、group だけが落ちます。

**7. 既存テストへの波及**

既存テストで期待結果そのものが変わるものは 0 件です。比較 seam を通る次の既存期待値はすべて維持すべきです。

- 通常 KILLED: `orchestrator/tests/test_mutation_harness.py:689-714`
- collection 不在拒否と parameter exact MISMATCH: `:838-857`
- strict superset/subset、別 path/class/test の MISMATCH: `:860-935`
- 異常 rc と failure 0 件の PARSE_ERROR: `:938-961`
- resume の raw expected/failed 証拠拒否: `:1199-1299`
- base node の flaky hold 拒否: `orchestrator/tests/test_flaky_test_holds_contract.py:697-719`

通常 `_argv` は `-n/--dist` を付けません。`test_mutation_harness.py:323-357`。したがって fixture に marker を追加しても、専用 loadgroup helper 以外の既存 nodeid は変わりません。plan の「既存期待値を変更しない」は正しいです。

**8. 実行対象**

直接テストに加え、変更 production file を全件内容走査または AST 走査する検査が存在します。詳細は下の対象一覧にまとめます。

## 所見一覧 (BLOCKER / MAJOR / MINOR、file:line 付き)

- BLOCKER: 0 件。
- MAJOR: 0 件。
- MINOR: 段 2 plan のテスト設計は新規テストを `test_mutation_harness.py` と `test_mutation_fanout_contract.py` に置くことまでは明記していますが、実 harness を wrapper 経由で動かす `test_mutation_worktree.py:639-675,1431-1479`、外部 policy consumer `test_flaky_test_holds_contract.py:697-719`、repo-wide production 走査群を実行対象として列挙していません。`stage2-plan.md:133-179`。
  放置すると、新しい単体正例は通っても、wrapper resume と production 全件 AST inventory への波及が未検証のまま残ります。

## 親の provisional 裁定 (P1)〜(P5) への評価

- P1: 採用。実在 26 件に対し `rfind("@") > rfind("]")` は 25 件の parametrize ID を保持し、1 件の実 group 接尾辞だけを除去します。
- P2: 採用。親 handoff の xdist producer 実測 `handoff.md:127-149` により、複数 marker は `_` 連結で `@` は一個です。さらに実 suite の group 名六種は `@` を含みません。段 2 plan の「producer を断定できない」という残存不確実性 `stage2-plan.md:189-192` は、現在の親資料では解消済みです。
- P3: 採用。raw 証拠一致の座 `tools/mutation_harness.py:2376-2378,2434-2436,2492-2494,2511-2512,2641-2644` を見ると、比較専用 `_match_key` だけへ入れる必要があります。
- P4: 狭義の文面どおり採用。`mutation_fanout.py` 自体には node 比較器がありません。ただし fanout 経路の終端 verifier `mutation_fanout_contract.py:335-352,899-903` は直す必要があり、段 2 plan の補足が正しいです。
- P5: 採用。初回 `mutation_harness.py:1469-1476`、resume `:2379-2388`、fanout merge `mutation_fanout_contract.py:899-903` の三座とも両側 key 化が必要です。

## 親が走らせるべき pytest 対象

直接の機能・consumer 対象:

- `orchestrator/tests/test_mutation_harness.py`
- `orchestrator/tests/test_flaky_test_holds_contract.py`
- `orchestrator/tests/test_mutation_fanout_contract.py`
- `orchestrator/tests/test_mutation_fanout.py`
- `orchestrator/tests/test_mutation_worktree.py`
- `orchestrator/tests/test_pytest_failure_digest.py`

変更 production file を列挙・内容走査・AST 走査する対象:

- `orchestrator/tests/test_pegasus_dispatch_compute.py` — `tools/` と `orchestrator/` の全 Python を AST 走査。`:2246-2259`
- `orchestrator/tests/test_campaign.py` — tests 等を除く repo-wide Python を解析。`:5258-5308`
- `orchestrator/tests/test_login_headroom.py` — `tools/` と `orchestrator/` の全 Python を AST 走査。`:1625-1643`
- `orchestrator/tests/test_t338_submission_gate_unit5.py` — repo 全 Python の production call site を AST 走査。`:490-515`
- `orchestrator/tests/test_official_perf_closure.py` — `tools/` と `orchestrator/` の production source を内容走査。`:514-540`

## 探して 0 件だったもの

- `tools/mutation_fanout.py` 内の `expected_nodes`、`failed_nodes`、`collected_nodes`、nodeid、node key: 0 件。
- shard 分割時に expected node を key 化、比較、書換えする経路: 0 件。
- `tools/mutation_fanout.py` 自身が結果 node を突き合わせる経路: 0 件。
- 実 suite の xdist group 名に `@` を含むもの: 0 件。
- acceptance ledger の `@` nodeid のうち parametrize ID、group 接尾辞以外のもの: 0 件。
- nodeid の path 部分に `@` を持つもの: 0 件。
- 新しい比較 key により期待値変更が必要な既存テスト: 0 件。
- A1〜A9 と段 2 plan の双方から漏れた意味比較の座: 0 件。

## 総括

段 2 plan は実装上必要な意味比較の座を網羅しています。四方向、resume、flaky hold、fanout 終端 verifier のいずれにも未修正経路は残りません。raw 台帳照合の追加座は複数ありますが、そこは観測表記の完全性を守るため変更しないのが正解です。

判定は BLOCKER 0、MAJOR 0、MINOR 1 です。MINOR は実行対象の列挙不足だけで、実装方針の欠落ではありません。pytest は実行しておらず、以上は静的検査結果です。