# A-1 balanced5 の sizing 証明書と本走 policy の凍結 — 実装と検査の記録

- authority: none
- default_effect: no-state-change
- 事前登録 (人間可読の正本) = `output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md`
- 機械可読の正本 = `orchestrator/campaign/paper_story_a1_paired.v3-sized.json`
- **本走は投入していない。** 正式測定の認可は [T-1505] により人間手番のままである。

## 何をしたか

2026-09-11 に完走した pilot (`output/insights/2026-09-01_paper-story-a1-balanced5-pilot/sizing-pilot.json`)
を入力に、凍結済みの道具で sizing 証明書を作り、別実装で再現し、本走 policy を凍結した。
pilot から取ったのは散らばりと baseline の水準だけで、差の符号も大きさも取っていない。

道具の式・確率・候補・種の定義域・停止規則はいずれも pilot のデータを読む前に凍結済みであり、
本 wave では 1 byte も変えていない (`tools/size_paper_story_a1_balanced.py` /
`tools/verify_paper_story_a1_balanced_sizing.py`)。

## 証明書の生成と再現

| 引数 | 値 | 出所 |
|---|---|---|
| root seed | `e72bc005d156caea2c89085c563c72fa04bbeb4afd98160fca968da9a7f6b3b3` | pilot 事前登録 §5.5 |
| 探索試行 | 20000 | 同 §5.5 |
| 認証試行 | 100000 | 同 §5.5 |
| 候補範囲 | 28..4096 | 同 §5.4 |

結果は `status=selected`。3 workload とも最小の実現候補 `n=30` を `order_index=0` で選び、
認証は 1 回目で通った。候補格子のうち評価したのは各 workload 1 件である。

| workload | n | df | k | planned_sigma_tps | 採った sigma |
|---|---:|---:|---|---|---|
| write-heavy | 30 | 29 | 2.8315526875186725 | 66403.452108019716 | block |
| balanced | 30 | 29 | 2.8315526875186725 | 56697.435713574683 | block |
| read-heavy | 30 | 29 | 2.8315526875186725 | 74668.489566274948 | pair |

| 成果物 | SHA-256 |
|---|---|
| 証明書 | `41d041963c8f3a175b5501810f52ab2619d9285f6f1eeb176790698131fc8299` |
| 再現の受領証 | `5027d9e7a8ef26441f44ee8bde26bb4d1aa18b99a6fa3337382ada29ddbad540` |
| 事前登録 README | `6047eff005fbd94bad8df0313124bd4ca037dedf0f2e3db05224d04ad34fd3c2` |
| 本走 policy | `a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a` |

再現の受領証は生成側と検証側の 2 つの道具の bytes を束縛する。driver は束縛していない。
**別実装であっても互いに独立な統計の権威ではない。**

## consumer 側に足した検査

裁定 D1452 (反復数を決める道具の受理範囲は証明書側で照合する) を閉じた。証明書は既に申告値を
記録していたが、consumer が事前登録の値と突き合わせていなかった。

足したのは exact 一致 5 項目 (`policy.search.trials` / `policy.certification.trials` /
`policy.candidate_grid.registered_minimum` / `.maximum` / `policy.root_seed.digest`) の型込み照合で、
既存の workload / n / df / k / sigma の検査の**後**に置いた (既存の拒否理由の優先順位を変えないため)。

**この照合が無いと何が通るか。** 段 3 の敵対相談が反例を構成した。証明書の
`candidate_grid.maximum` を `4096` から `4095` に書き替えても、実現候補列は `30,40,…,4090` のままで
選ばれる `n` も変わらないので、既存の consumer も再現側の検査も通る。登録範囲と違う設定で反復数を
決めた証明書が本走 policy に束縛されうる。

あわせて次の 2 つを直した。

- **十進文字列の受理。** 証明書の `planned_sigma_tps` は生成側 `.17g` の十進文字列で、JSON 数値へ
  落とすと `Decimal(str(float))` が別の値になる (`66403.452108019716` → `66403.45210801972`)。
  現行の consumer は sized の `k` / `planned_sigma_tps` に数値を要求していたため、本番の証明書と
  一致する policy を書けなかった。`k` (= 2.8315526875186725) は round-trip するので影響しない。
- **float 側の正値・有限条件。** 文字列を許すと `_positive_decimal` の Decimal 上の判定だけになり、
  `1e-999` のように「Decimal では正だが float では 0」の値が通る。変換後の有限性と正値も要求した。

**本走 policy の bytes の pin** も足した。`_policy_identity` は sized study に対して policy hash を
`None` で返しており、pilot と v2 にはある bytes pin が sized だけ発火していなかった。既存機構を
対称化しただけで、新しい gate は作っていない。

## 本走 policy の内容

pilot policy との差は次だけである。`sizing` block の pilot 設計値 (60 対 / 12 ブロック / 各先行 6) は
sigma の入力になった pilot の設計なので変えていない。

- `study_id` を sized へ、`final_estimate_eligible` を `true` へ
- 3 workload の `reps` 30 / `df` 29 / `pair_indices.stop_exclusive` 30 / `k` / `planned_sigma_tps`
- 3 workload の `schedule_root_seed` (事前登録 §2.1 の原像から導出、pilot とは別の値)
- 出力先 2 つ (durable 測定先と公開先) を本走専用へ
- `preregistration` の path と sha256
- `sizing_inputs` = pilot 結果と証明書の path / sha256 のちょうど 2 binding

`authority.formal` は **`false` のままである。** これは選択ではない。
`orchestrator/campaign/ident.py` と `orchestrator/campaign/wal.py` が sized study を A-1 非認証 lane の
exact identity 集合に持ち、どちらも独立に `formal is False` と `promotion_prohibited is True` を
要求する。`true` にすると campaign の identity 検査で拒否される。
`final_estimate_eligible=true` は「本走の観測値が登録済み解析の対象になる」という意味であり、
投入の認可でも正式な結果への昇格でもない。

## 検査

- 焦点走 `orchestrator/tests/test_paper_story_a1_paired.py` = **282 passed / rc=0**。
  実装子の初回は 79 赤 (failed 6 / errors 73) で、全件が単一原因
  (`sizing_inputs.pilot_result` の key 集合が 6 個で、consumer が要求する 2 個と違う) に帰着した。
  既存テストの赤は 1 件も無い。テスト関数は 124 → 133 で、削除・skip・xfail の追加は無い。
- 変異は anchor commit `30860397752b25b4391009ed720b8fd99069464a` に対して実行した。
  probe で観測 node を集め、それを完全集合として固定した本走で **5 件すべて KILLED・期待 node 完全一致**、
  baseline PASSED。台帳は `mutation-ledger.final.json`、spec は `mutation-spec.final.json`。

| ID | 変異 | kill した node 数 |
|---|---|---:|
| M1 | 登録値照合から `search.trials` の項を削除 | 7 |
| M2 | 同じく `candidate_grid.maximum` の項を削除 | 5 |
| M3 | 同じく `root_seed.digest` の項を削除 | 7 |
| M4 | float 側の正値条件 (`converted <= 0`) を削除 | 2 |
| M5 | sized policy の bytes pin を `None` へ戻す | 2 |

M2 が 5 件なのは、`candidate_grid` には項が 2 つあるため、section 自体を壊す負例 2 件が
残った `registered_minimum` の項で依然として拒否されるからである。

段 4 で登録した M1 は当初「期待値を 20000 → 19999 に変える」だったが、段 6 のレビューが
「凍結済みの正しい証明書を読む正例が先に落ちるので、負例による単独 kill にならない」と指摘した。
項の削除へ再照準した。**この訂正は観測後に行ったものであり、記録として残す。**

## 敵対検査で出た所見

- 段 3 (凍結と規律のレンズ / 受理集合と全層のレンズ) の real 所見は、本 wave の scope へ 4 件
  取り込んだ (policy bytes pin、float 正値条件、seed の凍結時点の書き方、実行面の未完了)。
- 段 6 レビュー a は must-fix 0。D1452 の 5 項目それぞれについて、単独で崩した証明書が
  hash 検査などに先取りされず新しい照合で落ちることを確認した。
- 段 6 レビュー b は事前登録本文の逐語照合で転記不一致 0 件。must-fix 2 件はいずれも本文の言い過ぎで、
  (1) `result_authority` が「実装のどこからも読まれない」という断言を「意味上の分岐には使われないが
  内容一致と bytes pin の検査対象ではある」へ限定し、(2) 感度分析の式に各反復の note 発生が独立という
  仮定を明記した。どちらも数値は変えていない。
- 親が brief に書いた「本番値でも数分」という所要時間の外挿は誤りだった。実際は 0.36 秒で、
  3 workload とも候補 1 件で停止したためである。試行回数に単純比例しない。

## この記録が主張しないこと

- **本走が起動可能になったとは言わない。** 証明書と policy の凍結、および loader の受理までである。
  計測経路には pilot 専用の分岐が残っている (source 契約が pilot の attempt を無条件に要求する、
  依存 source の staging と source binding の生成が pilot 限定、amended build の configure argv の
  受理形が pilot と sized で異なる)。
- pilot の結果から性能の優劣・改善・悪化を述べない。
- 反復数の設計は、pilot から作った sigma と baseline 水準を真値として固定した正規模型の上での
  評価である。正規性・定常性・pilot と本走の同分布性は検査していない。

## 逐語の保存

`verbatim/` に段 1 brief、段 2 プラン、段 3 敵対相談 2 本、段 4 裁定、段 5 実装報告、
段 6 の fix 3 本とレビュー 2 本を保存した。
