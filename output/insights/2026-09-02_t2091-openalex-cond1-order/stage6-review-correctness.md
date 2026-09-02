## 総括

最も重い所見は、期待値 catalog の raw JSON だけは重複 member を拒否しない非対称が残ること。ただし現行 catalog は生成器出力と byte 一致しており、現成果物の受理集合は広がらないため must-fix ではない。  
response 側について、多重度・入れ子・`join`・field・型・整列キーが順序以外を吸収する反例は見つからなかった。未知構造と重複 member は不一致へ落ちる。  
M1〜M8 は対応テストで検出可能。ただし M2 は mutant を生の `set` にすると `TypeError` で赤になるため、単一理由性には型を保つ mutant が必要。  
既存の空 `filter_rows` 負例が削除されたが、現在の実装・登録 catalogでは受理拡大につながらない。  
scope 外項目への実装接触はない。pytest は実走しておらず、以下は静的検査結果である。

## 所見

### 1. canonical 化による「順序以外の差」の吸収は見つからない

- **主張:** JSON primitive から成る有効な `oqo` について、兄弟順以外が同一 canonical 値になる入力対は作れなかった。
- **反例となる具体入力または file:line:** `A/B/C` を異なる filter としたとき、`[A,A,B]` 対 `[A,B]`、`or(A,or(B,C))` 対 `or(A,B,C)`、`and(A,B)` 対 `or(A,B)`、`operator` 欠落対 `null` 対 `""` はすべて [validator.py:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2091-openalex-cond1-order/orchestrator/axis1_search/validator.py:171) 以降で異なる tupleになるか `_InvalidOpenAlexOQO` になる。整列キーは canonical tuple の JSON 表現であり、canonical node が文字列と tuple だけから成るため、この入力域では非単射の組を作れない。
- **帰結:** response の受理集合は、実装上も兄弟順だけ広がる。
- **確度:** 静的推論のみ。
- **成果物への影響:** must-fix なし。新 amendment §3 の中心保証は実装されている。

### 2. 期待値 catalog の raw JSON だけは重複 member を拒否しない

- **主張:** response と期待値の canonical 化は対称だが、canonical 化前の raw JSON parse は非対称である。
- **反例となる具体入力または file:line:** catalog の期待値を  
  `{"join":"xor","join":"or","filters":[A]}`、response を  
  `{"join":"or","filters":[A]}`  
  とする。[catalog.py:822](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2091-openalex-cond1-order/orchestrator/axis1_search/catalog.py:822) の通常の `json.loads` は期待値を後勝ちの `or` として読み、`:846-848` の生成 document 比較も通りうる。一方、response は [runner.py:461](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2091-openalex-cond1-order/orchestrator/axis1_search/runner.py:461) と [validator.py:925](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2091-openalex-cond1-order/orchestrator/axis1_search/validator.py:925) で重複を拒否する。
- **帰結:** 将来 catalog を手編集して登録した場合、raw expectation の曖昧さを `load_catalog()` が検出しない。ただし契約 §3:136 は「応答」の重複拒否だけを要求している。
- **確度:** 現物で確認した。
- **成果物への影響:** 現行 catalog は生成器出力と byte 一致し重複もないため影響なし。プラン v2 の実装 scopeを広げる must-fixにはしない。

### 3. 既存の空 `filter_rows` 負例が明示的には残っていない

- **主張:** 旧 `test_openalex_condition1_compares_structured_oqo_not_oql_text` にあった `filter_rows=[]` の拒否 assertion は、新しいテスト群への置換時に削除された。
- **反例となる具体入力または file:line:** 現在の正例は [test_axis1_search_runner.py:233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2091-openalex-cond1-order/orchestrator/tests/test_axis1_search_runner.py:233)、負例表は同 `:274-460`。空 root/group array の case はない。一方、production は [validator.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2091-openalex-cond1-order/orchestrator/axis1_search/validator.py:183) と `:216-217` で拒否する。
- **帰結:** テスト被覆は純粋な加算ではない。ただし有効な登録期待値は非空であり、空 actual は非空 expected と一致しないため、現在の受理集合は広がらない。
- **確度:** 現物で確認した。
- **成果物への影響:** 非 blocking。既存負例を厳密に保存する方針なら空 root/group caseを復元すべきだが、M1〜M8 の kill 能力には影響しない。

## 契約条項と実装の対応

| amendment §3 条項 | 発火箇所 | 判定 |
|---|---|---|
| expected / actual 双方へ同じ正規化 | [validator.py:231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2091-openalex-cond1-order/orchestrator/axis1_search/validator.py:231)、`:273-281` | 発火する |
| root と `and` / `or` group の兄弟順だけ無視 | `validator.py:185-191,218-227` の `sorted(...)` | 発火する |
| 多重度保存 | 同箇所が `set` 化せず tupleへ全要素を残す | 発火する |
| 入れ子境界・深さ保存 | `validator.py:187,191` の再帰した `"group"` node | 発火する |
| `join` 値保存 | `validator.py:179-191` | 発火する |
| field の有無保存 | `validator.py:193-204` の exact key setとkey込み tuple | 発火する |
| field 型 | `validator.py:199-200` で exact `str` 以外を拒否 | 発火する。未知型は保存せず fail-closed |
| `get_rows` | `validator.py:210-227` | 発火する |
| 未知 `join` / key / 型を両側同形でも拒否 | `validator.py:175-200,208-217,231-237` | 発火する |
| response の重複 member拒否 | [runner.py:446](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2091-openalex-cond1-order/orchestrator/axis1_search/runner.py:446)、[validator.py:910](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2091-openalex-cond1-order/orchestrator/axis1_search/validator.py:910) | live・resume・offline の全 condition-1 経路で発火する |
| `oql` を判定に使わない | `validator.py:273-282`。production callerは構造期待値を必ず渡す | 発火する |

`parsers.py:277-288` にも `oqo` 抽出があるが、これは evidence 用 `interpreted_query` の生成と欠落検出であり、条件1の判定値ではない。実際の条件1は runner `:860-868,1347-1354` と validator `:1441-1446` で raw bodyを重複拒否付きで再抽出する。第三の受理経路は見つからなかった。

`_InvalidOpenAlexOQO` は `ValueError` を継承するが、比較関数はその subclassだけを捕捉する。offline の外側の広い `ValueError` 捕捉へ届いても結果は `bundle_check_error` の偽側であり、一致側へ落ちる経路はない。

## 変異と検出テストの対応

以下はすべて `orchestrator/tests/test_axis1_search_runner.py`。

| 変異 | kill nodeid | 静的判定 |
|---|---|---|
| M1 兄弟整列削除 | `::test_openalex_condition1_compares_structured_oqo_not_oql_text` | kill。root・複数階層の順序が違う正例 |
| M2 兄弟を `set()` 化 | `::test_openalex_condition1_rejects_every_non_order_difference[multiplicity-difference]` | 型を保つ set 化なら clean kill。生の `set` を canonical tupleへ入れる mutantは `TypeError` で赤となり単一理由性なし |
| M3 同一 join flatten | `::test_openalex_condition1_rejects_every_non_order_difference[same-join-flatten-difference]` | clean kill |
| M4 canonical値から join削除 | `::test_openalex_condition1_rejects_every_non_order_difference[join-difference]` | clean kill |
| M5 未知 joinを `and` 化 | `::test_openalex_condition1_rejects_every_non_order_difference[unknown-join-on-both-sides]` | clean kill |
| M6 欠落 fieldを空文字列化 | `::test_openalex_condition1_rejects_every_non_order_difference[missing-vs-empty-string]` | clean kill |
| M7 重複 member拒否削除 | `::test_runner_openalex_oqo_rejects_duplicate_raw_response_members`、`::test_validator_openalex_structure_rejects_duplicate_raw_response_members` | 各 extractorの変異を個別に clean kill |
| M8 期待値側だけ canonical 化 | `::test_openalex_condition1_compares_structured_oqo_not_oql_text` | kill。正例が不一致になる |

条件1の正負例は local `_page` を使うが、判定対象は stub comparatorではなく production の `evaluate_page()` と canonical helperである。重複 memberテストも production extractorを直接呼ぶ。fixture hash の差込み、skip、期待値反転、揮発 payloadの焼込みは見つからなかった。

## scope 外への接触

| scope 外項目 | 接触 |
|---|---|
| 凍結集合拡張 | なし。`FROZEN_BASE_COMMIT` / `FROZEN_PREDECESSOR_PATHS` は [validator.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2091-openalex-cond1-order/orchestrator/axis1_search/validator.py:20) のまま |
| epoch 欠落 gate | なし。runner は16個の fallback literal置換のみ |
| anti-replay | 実装接触なし。新 amendmentに未保証との記述だけ |
| bundle / output書込み先防護 | なし |
| 無償枠 gate | なし。`permits_next` / `reset_seconds` は [runner.py:241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2091-openalex-cond1-order/orchestrator/axis1_search/runner.py:241) から不変 |
| versioned schema dispatch | なし。現行 schemaのepoch const更新だけ |
| `output/insights/**` | 変更なし |
| 旧 amendment・catalog・実行記録・bundle | 変更なし |

新 catalog は、旧 catalogへ epoch・amendment・supersedes の裁定済み3置換を施した内容と byte比較で一致した。HTTP、pytest、bundle生成は実行していない。