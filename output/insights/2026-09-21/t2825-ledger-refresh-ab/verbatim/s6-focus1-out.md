## 対応表

参照先は修正後の [probe ディレクトリ](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2825-probe/t2825-probe)。以下、`analyze.py` は `t2825_ab_analyze.py` の略記です。

| 所見 ID | 判定 | 根拠 | 残件 |
|---|---|---|---|
| A-1 | **partial** | `analyze.py:504–520` は無効対後に同じ slot の先頭条件だけを許可。`run-measure.sh:42,55–73` は flock 内、`run-series.sh:47–52` も同じ `check_request()` を使用。拒否は RUN 作成（`:132`）より前で、走番号を消費しない。 | **履歴削除を検出できない。** 無効対の片側再利用・12走上限の迂回が可能。走番号の逆順投入も事前拒否しない。詳細は下記。 |
| B-2 | **closed** | `analyze.py:477–478` は「事前登録した L 伸長の判定条件を満たさない」。Markdown は同じ値を表示（`:541`）、selftest の期待も更新済み（`:728`）。 | 5ファイル内に「非観測」「伸長なし」の残存なし。JSON の `L_observation` も不在を断定する名前ではない。 |
| B-3 | **closed** | `analyze.py:90–107` は固定 SHA の `git show SHA:path` の bytes から hash と負荷用辞書を生成。worktree は比較 hash 専用。取得失敗は `:374–375` で系列エラーとなる。JSON・Markdown に両 hash を別欄で出す（`:105–107,544–546`）。 | worktree の後日変更で測定 hash・予測負荷は変わらない。git／SHA が読めない場合の worktree fallback はない。 |
| A-3 | **closed** | `analyze.py:110–114,130–131` と割付器 `acceptance_shards.py:397–404` はともに base → `nodeid@group` → 1.0。group は実物 `observed_universe[].group` を使用。独立再計算も一致。 | なし。 |
| A-4 | **closed** | `analyze.py:461,485,488–500` は有効対に採用された tag だけを抽出。無効走、無効対の健全な片側、未対化の健全走は入らない。条件別・shard 別に6量と対象走番号を出す。 | 偶数個は `statistics.median` により中央2値の算術平均。0件は `null`。この定義は出力本文には未記載（nit）。 |

## 独立再計算

集計器を呼ばず、指定 session の JSON／XML と、A の固定 SHA `21641fee777d24642d54119b660a7b7880636e71` の台帳を読み、負荷を十進数で加算しました。

| shard-0 の量 | 旧 base-only | suffix 対応後 | 判定 |
|---|---:|---:|---|
| 予測負荷（秒） | 7750.334 | 7749.524 | **一致：−0.810秒** |
| 未登録件数 | 368 | 367 | **一致：−1件** |

差を生むのは `test_sort_swo_oracle.py::test_real_patchharness_checkout_and_resolver_use_explicit_binding` の1件だけです。実物 group は `real-repo`、suffix 台帳値は **0.19秒**でした。

実物1走の **W₀＝382.090秒、L＝229.056秒、L worker＝gw5** も一致。L は `test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]`、rank 5、partner 0 です。

T-2724 は以下の **8件**を抽出しました。全件 shard-0、partner 0。開始 offset は同 worker の XML 順で先行 time を累積した推定値です。名称は共通のファイル名と `test_` を省略しています。

| node 名 | worker | rank | time 秒 | 推定 offset 秒 |
|---|---|---:|---:|---:|
| t080_shared_base_separates_active_v2_and_reuses_legacy_identity | gw33 | 455 | 0.004 | 55.435 |
| t080_active_v2_delegation_accepts_full_receipt | gw33 | 456 | 189.183 | 55.439 |
| t080_failed_launch_preserves_receipt_refusal | gw33 | 457 | 47.857 | 244.622 |
| v1_gate_does_not_delegate_with_active_v2 | gw42 | 459 | 40.685 | 244.438 |
| t080_active_v2_preserves_nonlayer2_receipt_refusal | gw47 | 460 | 191.540 | 55.848 |
| t080_delegated_campaign_start_rechecks_receipt[changed] | gw40 | 461 | 191.961 | 56.635 |
| t080_delegated_campaign_start_rechecks_receipt[missing] | gw40 | 462 | 38.547 | 248.596 |
| t080_delegated_campaign_start_rejects_late_hit_file | gw47 | 463 | 44.292 | 247.388 |

fix 報告の8件という件数、および掲載された gw33 の rank・time・offset は一致しました。

親の **334 → 202／132** も固定 A／B 台帳と一覧を独立照合しました。重複なし334件、A 登録0件、B 登録202件、残存132件。残存内訳は `test_p3_s4_loop_sort.py` 29、`test_real_repo_serialization.py` 66、`test_sort_swo_oracle.py` 37で一致します。これは指定された334件の一覧に対する照合です。

## 新規所見

**must-fix — A-1残件：既存 runs の削除で、対の取り直し規則と投入上限を迂回できる。**

`run-measure.sh:44–64` は現存ディレクトリだけを数え、集計器も渡された履歴だけを解析します。別の投入記録との突合はありません。

具体例として、`01 A 1`／`02 B 1` が skipped 不一致だった場合、`02-B` を削除すると `01-A` は健全な未完対に見えます。`next_allowed()` は **B／slot 1** を許し、`03 B 1` で健全な片側を再利用できます。全履歴を退避・削除すれば、投入数と固定終了もリセットされます。これはコードからの追跡であり、実際の削除はしていません。

投入履歴を RUN 成果物とは別に保持し、欠落・不一致を投入前に拒否する必要があります。

**should — 新しい走番号の順序を照合せず、投入後に系列を壊せる。**

`run-measure.sh:75` は番号重複だけを拒否します。例えば健全な `05 A 1` の後、未使用の `01 B 1` は condition／slot 照合を通ります。しかし `analyze.py:368` は番号順に並べるため、次回解析では B→A となり系列が無効になります。新番号が過去の最大番号を上回ることも flock 内で確認すべきです。

**nit — 条件別中央値の定義を出力に追記する。**

「偶数個は中央2値の算術平均、対象0件は欠測」と明記すると、中間集計の読み方が確定します。

## 見つからなかったこと

- 履歴を保持した通常経路では、直接 `run-measure.sh` を呼ぶ方法や slot 引数の変更による要求照合の迂回は見つかりませんでした。
- 有効走の rc、複製hash、完走・赤、HEAD／clean、門番、collection、対内 skipped 一致の検査に、今回の修正による欠落は見つかりませんでした。
- 履歴が保持されている場合の12走上限・有効3対固定終了、判定 (i)/(ii)/(iii)、10%境界、W_max の補助扱い、参考値の非使用に回帰は見つかりませんでした。
- 必須の走別出力が今回の修正で失われた箇所は見つかりませんでした。条件別6量は追加されています。
- pytest、selftest、測定走は実行していません。fix 報告の検査 rc を本レビューの実行結果として扱っていません。

## 総括

**判定：修正後 GO。残る must-fix は1件です。**
B-2・B-3・A-3・A-4 は closed、A-1 は履歴削除への対処がなく partial です。
実物の負荷差 −0.810秒、未登録 −1件、W₀・L・T-2724 8件、334件の内訳は独立再計算で一致しました。
履歴欠落の拒否を修正し、走番号の順序チェックも追加してから測定着手する判断です。