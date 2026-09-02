## 現状の挙動 (file:line 付き)

- `DW-M08` は、期待 node と同形式へ正規化した記録 node の完全一致だけを `KILLED` とするよう要求している。`DW-M08.md:3-7`、`F33.md:17-24`。
- [`_normalize_node`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:1223>) は path・区切り・空白だけを正規化し、`@group` を保持する。
- [`_match_key`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:1237>) は現在 `_normalize_node` の恒等 wrapper であり、比較形式を揃えていない。
- [`_failed_nodes`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:1241>) は `FAILED ` 後を取り、` - ` が無ければ行末を node として、接尾辞付きのまま `failed_nodes` へ記録する。`tools/mutation_harness.py:1247-1255`。
- [`_collected_nodes`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_harness.py:1259>) は collection stdout を同じ `_normalize_node` で記録するが、今回の `--collect-only` 出力には group 接尾辞が無い。
- 実行時判定は両集合を `_match_key` へ通したうえで `failed_keys == expected_keys` を要求している。部分一致ではない。`tools/mutation_harness.py:1997-2013`。
- 初回 collection 事前検査は期待側だけを `_normalize_node` へ通し、収集値と生集合比較している。接尾辞込み期待を拒否する直接原因である。`tools/mutation_harness.py:1469-1479`。
- resume の collection record 再照合も同じ生集合比較である。`tools/mutation_harness.py:2376-2388`。
- registration は `_normalize_node` 後に `_match_key` で重複を検査している。`tools/mutation_harness.py:1109-1117`。したがって `_match_key` を直せば、接尾辞有無の二表記も重複になる。
- `tools/mutation_fanout.py` 自身には node 抽出器や比較器はない。しかし [`merge_group` 呼び出し](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/tools/mutation_fanout.py:1745>) の先に、独立 verifier が存在する。
- その verifier である `tools/mutation_fanout_contract.py` は、独自の `_failed_nodes`、`_collected_nodes`、`_observed_status` を持つ。`tools/mutation_fanout_contract.py:281-352`。さらに collection の期待 node を生集合で検査する。`tools/mutation_fanout_contract.py:887-903`。harness だけ直すと fanout merge が新しい台帳を旧規則で拒否する。

## 論点 1〜7 への回答

**1. 正規化を入れる座**

親 P3 の「`_match_key` だけを変更し、`_normalize_node` は据え置く」は正しい。

- `_match_key` だけを変更する場合、F71 の実例では `failed_nodes` は `...@s8c-predicate-snapshot` のまま、`collected_nodes` は接尾辞なしのまま残る。観測面の差が台帳に保存され、比較時だけ同形になる。
- `_normalize_node` で接尾辞を落とす場合、`_failed_nodes` が返す台帳値まで接尾辞なしになる。接尾辞付き collection artifact が来た場合は `collected_nodes` も書き換わる。今回の collection は元から接尾辞なしなので、結果として両欄が同じ base node に見え、runtime が実際に接尾辞を出した事実を失う。
- registration の `expected_nodes` も `_normalize_node` を通るため、spec に接尾辞込みで書いた事実まで失われる。`tools/mutation_harness.py:1109-1117,2186-2205`。

fanout verifier 側も同様に `_normalize_node` を据え置き、比較専用 `_match_key` を追加する。

**2. 接尾辞の判別規則**

`nodeid.rfind("@") > nodeid.rfind("]")` は、指定された実在例を守る。

- 実例は [`acceptance_duration_ledger.json:143`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/acceptance_duration_ledger.json:143>) の `test_real_catalog_leaf_resolves_every_runner_field[arxiv-AX1-20260829-E1-Q1@arxiv]`。
- 最後の `@` は最後の `]` より前なので条件は偽になり、parametrize ID は削られない。
- `[param@value]@group` なら group の `@` が最後の `]` より後なので、group だけが落ちる。

ただし、この規則は一般には一段しか落とせない。具体的な反例は [`test_acceptance_schedule_order.py:491`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2123-mutation-node-normalize/orchestrator/tests/test_acceptance_schedule_order.py:491>) の

`orchestrator/tests/test_group.py::test_case@first@second`

である。現 helper は `@second` だけを落とし、`...::test_case@first` を返す。単一 group 名自体が `g1@g2` の場合も同じ形で壊れる。

**3. 複数 group の結合形**

射影された source から証明できるのは次の二点までである。

- installed xdist の `LoadGroupScheduling._split_scope` は `name@first@second` を入力として扱える。repo の differential oracle が直接比較している。`orchestrator/tests/test_acceptance_schedule_order.py:485-504`。
- ただし、複数 marker から xdist がその文字列を実際に生成する producer 実装は、許可された射影内にない。したがって「xdist が実際に `name@g1@g2` を生成する」とは断定しない。

一方、現 repo からの到達は否定できる。

- suite 契約は item 当たり marker を最大 1 個に固定する。`orchestrator/tests/test_real_repo_serialization.py:1176-1185`。
- shard canonicalizer も 2 個以上を `multiple-xdist-group` で拒否する。`tools/acceptance_shards.py:742-768`。
- production hook は既存 marker が一つでもあれば `real-repo` を追加しない。`orchestrator/tests/conftest.py:1993-2000`。
- 許可 group 名の独立 golden は 6 個で、いずれも `@` を含まない。`orchestrator/tests/test_real_repo_serialization.py:247-255`。

したがって本 wave の現 repo 到達範囲では一段の `rfind` 規則で足りる。複数段対応を本実装へ持ち込むのは scope 外の一般化になる。

**4. 事前検査を直す座**

二箇所とも期待側と collection 側を `_match_key` へ通す。

- 初回 collection: `tools/mutation_harness.py:1469-1476`
- resume collection record: `tools/mutation_harness.py:2379-2386`
- fanout merge の再検査: `tools/mutation_fanout_contract.py:899-903`

変更後は次のようになる。

- collection が `tests/x.py::test_a` を持つとき、期待の `tests/x.py::test_a` と `tests/x.py::test_a@g` の双方を受理する。
- collection record 自体の `collected_nodes` と artifact からの再抽出値の完全一致は維持する。`tools/mutation_harness.py:2376-2378`、`tools/mutation_fanout_contract.py:892-897`。
- path、class、test 名、parametrize ID が異なる期待は引き続き拒否する。
- parametrize ID 内だけにある `@` は比較 key に残る。
- 接尾辞込み期待だけを key 化する片側修正ではなく、必ず collection 側も同じ key 集合にする。

**5. 重複検査の基準**

接尾辞込みと接尾辞なしの同一テスト二表記は重複として拒否すべきである。完全集合の一要素を二回書いただけであり、二つの失敗を意味しない。

`tools/mutation_harness.py:1112` の既存 `{_match_key(...)}` を基準にする。`_normalize_node` 後の値は台帳用、重複同一性は `_match_key` 用という分離を保つ。`tools/mutation_harness.py:593-600` の raw 文字列重複検査も残す。

**6. `tools/mutation_fanout.py`**

P4 は「本体に比較器がない」という狭い意味では正しいが、fanout 経路全体については誤りである。

- `mutation_fanout.py` は wrapper を通じて harness を起動する。`tools/mutation_fanout.py:656-688`。
- 子の終了時は wrapper rc だけを回収する。`tools/mutation_fanout.py:741-785`。
- その後 `merge_group` を呼ぶ。`tools/mutation_fanout.py:1745-1752`。
- `merge_group` は ledger を読み、`_validate_ledger` を呼ぶ。`tools/mutation_fanout_contract.py:1228-1241`。
- `_validate_ledger` は collection expected node を再照合し、failed node を再抽出し、`KILLED` / `MISMATCH` を再判定する。`tools/mutation_fanout_contract.py:887-903,953-979`。

従って `tools/mutation_fanout.py` 本体の編集は不要だが、既存 consumer の `tools/mutation_fanout_contract.py` は同時修正が必須である。

**7. 緩めてはならないもの**

- `rc != 0` かつ抽出 0 件の `PARSE_ERROR`: `tools/mutation_harness.py:2000-2008` と `tools/mutation_fanout_contract.py:340-346` を変更しない。接尾辞 key 化はその後だけで行う。
- ` - ` 無しの `FAILED` 行: `tools/mutation_harness.py:1247-1250` と `tools/mutation_fanout_contract.py:303-311` を変更しない。
- 完全一致: harness は `failed_keys == expected_keys`、fanout verifier も同じ二集合の `==` とし、包含や部分文字列比較へ変えない。
- `SURVIVED` / `TIMEOUT` の空集合契約: `tools/mutation_harness.py:601-605` と `tools/mutation_fanout_contract.py:474-489` を変更しない。
- flaky hold: `tools/mutation_harness.py:1309-1310` で expected と held の双方を `_match_key` 集合にし、同一 base node の接尾辞有無を同じ policy 対象として拒否する。

## 実装プラン (file:line 粒度)

1. `tools/mutation_harness.py:1237-1238`

   `_match_key` 内でまず `_normalize_node` を呼び、その結果について最後の `@` が最後の `]` より後にある場合だけ、その `@` 以降を一段除去する。`_normalize_node` は変更しない。

2. `tools/mutation_harness.py:1469-1476`

   `collected_set` を raw normalized node 集合ではなく `_match_key(node, repo)` の集合にする。全 `expected_nodes` も `_match_key` へ通して差集合を取る。返却する `collection["collected_nodes"]` は従来の `collected` をそのまま保存する。

3. `tools/mutation_harness.py:2376-2388`

   artifact から再導出した `collected_nodes` と台帳値の順序込み完全一致は先に維持する。その後の期待 node 実在検査だけを、両側の `_match_key` 集合比較へ変更する。

4. `tools/mutation_harness.py:1109-1113`

   構造は変更不要。新しい `_match_key` により、接尾辞有無の二表記が同じ key へ畳まれ、既存の「正規化後に重複」で拒否されることをテストで固定する。

5. `tools/mutation_harness.py:1305-1315`

   held registry 側も `{_match_key(node, repo) ...}` に変換してから expected key 集合と交差させる。base node、接尾辞付き表記の双方で同じ hold を拒否し、無関係 node は拒否しない。

6. `tools/mutation_fanout_contract.py:281-352`

   `_normalize_node` は据え置く。その直後に harness と同じ一段規則の `_match_key` を追加する。`_observed_status` は記録用 `failed` list を変更せず、期待集合と失敗集合を `_match_key` 化して `==` で判定する。

7. `tools/mutation_fanout_contract.py:887-903`

   `collected_nodes` と artifact 再抽出値の完全一致は維持し、shard spec の expected node 包含検査だけを両側の `_match_key` 集合で行う。

8. `tools/mutation_fanout.py:35-41,1745-1752`

   編集しない。既存の `merge_group` 配線をそのまま使い、contract 側のテストでこの実経路を固定する。

## テスト設計 (正例・負例の対)

`orchestrator/tests/test_mutation_harness.py` では、fixture の `test_gate` に `xdist_group("mutation-group")` を付ける。対象は現在の fixture 定義 `:53-63,188-232`。既存の通常 argv では suffix を生成させず、新しい専用 helper だけが `-n 2 --dist loadgroup` を付ける。helper の座は既存 `_argv` の直後 `:306-358` とする。

- **正例 1: 接尾辞込み期待**

  `test_group_suffixed_expected_node_is_collected_and_killed` を `:838-857` 周辺へ追加する。期待を `tests/test_gate.py::test_gate[one]@mutation-group` とし、変異後の実失敗も同じ suffix 付きになる実走で `KILLED` を要求する。

  併せて `failed_nodes` が suffix 付き、`procedure.collection.collected_nodes` が suffix なし、registration の `expected_nodes` が suffix 付きのままであることを assert する。A5 または比較 key を無効化すると、その座の理由で赤になる。

- **正例 2: 接尾辞なし期待**

  `test_group_unsuffixed_expected_node_matches_suffixed_failure` を追加する。期待は `tests/test_gate.py::test_gate[one]`、記録失敗は `...test_gate[one]@mutation-group` とし、`KILLED` を要求する。`_match_key` の suffix 除去だけを無効化すると `MISMATCH` になる。

- **正例 3: resume**

  接尾辞込み期待で作った正当 ledger を `--resume` し、runner 呼び出し数が増えず成功するテストを分離する。A6 だけを旧比較へ戻すと resume collection record 再照合で赤になる。

- **負例 1: 別テスト**

  `test_group_suffix_normalization_does_not_match_different_test` を追加する。期待を `[one]`、実失敗を `[two]@mutation-group` とし、`MISMATCH` と suffix 付き `failed_nodes` を要求する。完全一致を包含、固定真、接尾辞だけの比較へ緩めると赤になる。既存の strict superset/subset 負例 `:860-886` も変更しない。

- **負例 2: parametrize ID 内の `@`**

  `test_match_key_preserves_at_inside_parametrize_id` を追加し、`acceptance_duration_ledger.json:143` の完全 nodeid を literal として `_match_key(node) == node` と assert する。さらに `[...@arxiv]@mutation-group` では group だけが落ちる対を置く。単純な `split("@")`、`rpartition("@")` に置き換えた場合だけ赤になる。

- **負例 3: 抽出 0 件**

  `test_group_suffix_normalization_keeps_nonzero_empty_failure_parse_error` を既存 `:951-961` の隣へ追加する。接尾辞付き期待、`rc=1`、`failed=[]` で必ず `PARSE_ERROR` を要求する。suffix 正規化を理由に空集合同士の一致へ進める実装を拒否する。

- **負例 4: 二表記重複**

  同一 node の接尾辞あり・なしを一つの `expected_nodes` に入れ、`_validate_registrations` が「正規化後に重複」で runner 前に拒否するテストを追加する。重複基準を raw node に戻した場合だけ赤になる。

- **policy 対**

  `_flaky_hold_node_ids_for_policy` を base node 一件へ固定し、base 表記と suffix 表記の双方が `policy mismatch`、無関係 node は通るテストを追加する。新 key 導入で hold 集合が抜けるのを防ぐ。

`orchestrator/tests/test_mutation_fanout_contract.py` にも独立 verifier 用の対を追加する。

- fixture builder `:75-114,122-303` に、期待 node の suffix 有無と runtime failed node の suffix 有無を明示できる引数を追加する。
- suffix なし期待、suffix 付き failure でも merge が `KILLED` を再導出する正例を追加する。
- suffix 付き期待、suffix なし collection record でも `collection に expected node がない` にならない正例を追加する。
- 異なる test node の suffix 付き failure は merge が `MISMATCH` と再導出し、偽 `KILLED` ledger を拒否する負例を追加する。
- raw `failed_nodes` と `collected_nodes` が artifact の観測表記のままであることも assert する。

既存テストの期待値は変更せず、xfail・skip は追加しない。

## 親の provisional 裁定 (P1)〜(P5) への評価

- **P1: 条件付きで採用。** `rfind("@") > rfind("]")` は実在 parametrize ID を守り、現 repo の一段 suffix には十分。ただし `name@first@second` では最後の一段しか落とせないため、一般規則として完全ではない。
- **P2: 到達不能という結論は採用、根拠を補強。** xdist producer が `name@g1@g2` を生成するかは射影 source から断定できない。しかし現 repo は marker 最大一個、group 名に `@` なし、hook も二個目を追加しないため到達不能である。
- **P3: 採用。** `_match_key` のみを比較 seam とし、`_normalize_node` と台帳観測値は維持する。
- **P4: 狭義のみ採用、fanout 経路としては棄却。** `mutation_fanout.py` 本体は変更不要だが、その直接 consumer である `mutation_fanout_contract.py` が比較器、抽出器、KILLED 再判定を持つため同形修正が必要。
- **P5: 採用。** 初回、resume、fanout merge の三箇所すべてで両側を同じ `_match_key` へ通す。片側だけでは接尾辞込み期待を救えない。

## 残る不確実性

- 許可された射影には pytest-xdist の marker-to-nodeid producer 実装がないため、複数 marker が実際に生成する具体的 suffix 文字列までは静的に確定できない。ただし現 repo から複数 marker 形へ到達しないことは source 上で確定できる。
- 指示どおり pytest は実行していない。上記は静的検査に基づくプランであり、緑の主張はしない。
- 編集後は行番号が移動するため、実装者は関数名と現行アンカーの双方で変更座を確認する。

## 総括

修正の中心は `tools/mutation_harness.py` の比較専用 `_match_key`、初回 collection、resume collection、flaky hold key である。観測値を保持する `_normalize_node`、`failed_nodes`、`collected_nodes` は変えない。

加えて、fanout の終端 verifier が同じ比較を独自再実装しているため、`tools/mutation_fanout_contract.py` の `_observed_status` と collection 再照合も同時に直す必要がある。`tools/mutation_fanout.py` 本体は編集不要である。