# 軸 1 検索の実行記録 — 新 epoch `AX1-20260902-E1` の OpenAlex 1 窓目 (2026-09-03)

**これは実行記録であって、登録でも改訂でもない。** 登録の正本は
`2026-09-02-axis1-search-amendment.md`、query program の正本は
`2026-09-02-axis1-search-catalog.json` である。本文書は凍結物であり、後から上書きしない。
内容を更新したいときは新しい日付の実行記録を足す。

**軸 1 は `未完走` であり、成熟度は `RW1` のままである。**

## 0. この走行の身元

| 項目 | 値 |
|---|---|
| 作成日 | 2026-09-03 (JST) |
| 登録 epoch | `AX1-20260902-E1` |
| 登録 commit | `4ec3eba04354f9ba86117a2dd488c72d007045e6` |
| catalog | `docs/related-work/claim-survey/2026-09-02-axis1-search-catalog.json` |
| catalog SHA-256 | `8e23d63a799c8ab9d25151012c34bc738dbb422ac3dfb237999c359137c816ab` |
| 文献 cutoff | `2026-12-31` |
| run ID | `t2090-openalex-20260903` |
| 索引 | OpenAlex のみ (arXiv / DBLP は本走行では 1 request も出していない) |
| 生証拠 bundle | `/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle` |
| bundle manifest SHA-256 | `ff25f09af3840d35b4bc3cb36c0fa8b9df283f0cce055c6c117b71707832e9ca` |
| 逐語と部分 mirror | `output/insights/2026-09-03_t2090-axis1-openalex-window1/` |

登録検査 (`tools/check_axis1_search.py registration`) は `passed: true` を返した。
`HEAD == 登録 commit`、登録 path の clean、catalog blob の一致、旧凍結物の bytes 一致の 4 点である。

**登録 commit は local main の当時の HEAD であり、本 wave が新しく作った commit ではない。**
したがって再開に必要な `HEAD == registration_commit` は、main の祖先を detach するだけで満たせる。

## 1. 条件 1 の照合は順序非依存の規則で行った

改訂契約 §5 が要求する明示である。本走行の条件 1 は、
`filter_rows` を暗黙の論理積とみなす再帰的な正規化比較 (`_openalex_oqo_matches`) で行った。
論理積・論理和として結合される兄弟の順序だけを無視し、多重度・入れ子・join の値・
field の有無と型・`get_rows` はすべて保存する。

**取得した全 93 頁で条件 1 は `可` だった。** 順序を理由に `否` になった頁はゼロである。

取得前のオフライン診断でも、旧 epoch に実在する唯一の OpenAlex 生応答に対し、
旧の完全一致比較が `不一致`、現行の順序非依存比較が `一致` を返した。
この診断は bundle の外で行っており、旧生応答を新 epoch の証拠へ再包装していない (§4 の規範)。

## 2. leaf ごとの結果

OpenAlex の登録 leaf は 78 本。本走行の後の状態は次のとおり。

| 状態 | 件数 | 内訳 |
|---|---|---|
| `完走` | 1 | `Q2@openalex` |
| pass 1 完了・独立 2 走目待ち (再開点あり) | 8 | `Q3-SPRE1991`, `Q3-SY1991`〜`Q3-SY1996`, `Q6-SPRE1991` |
| 条件 5 で `未完走` (再開点なし) | 3 | `Q1@openalex`, `Q4@openalex`, `Q5@openalex` |
| 未走 | 66 | 残りの shard |

再開点は bundle 内 `checkpoints/000001.json`〜`000008.json` で、いずれも
`state=pass_complete` / `resume_action=start_independent_pass` である。

| leaf | checkpoint |
|---|---|
| `AX1-20260902-E1-Q3-SPRE1991@openalex` | `checkpoints/000001.json` |
| `AX1-20260902-E1-Q6-SPRE1991@openalex` | `checkpoints/000002.json` |
| `AX1-20260902-E1-Q3-SY1991@openalex` | `checkpoints/000003.json` |
| `AX1-20260902-E1-Q3-SY1992@openalex` | `checkpoints/000004.json` |
| `AX1-20260902-E1-Q3-SY1993@openalex` | `checkpoints/000005.json` |
| `AX1-20260902-E1-Q3-SY1994@openalex` | `checkpoints/000006.json` |
| `AX1-20260902-E1-Q3-SY1995@openalex` | `checkpoints/000007.json` |
| `AX1-20260902-E1-Q3-SY1996@openalex` | `checkpoints/000008.json` |

**条件 5 で止まった 3 leaf には checkpoint が無い。** 実行器は完走述語が落ちた leaf に
後継 checkpoint を書かないため、この 3 本は「再開」ではなく「再取得」しか経路が無い。
未走の 66 leaf も checkpoint を持たず、`--query-id` で新規に起動する。

## 3. 条件 5 で `未完走` になった面 — 順序以外のどこが違ったか

改訂契約 §5 が要求する構造化である。**順序の差ではない。**
落ちたのは leaf 全体の条件 5 (`distinct_work_id_total_mismatch`) で、
索引の申告総数と、頁を通して集めた distinct な work ID 数が一致しない。

| leaf | 索引の申告総数 | 取得行数 | distinct | 頁境界の重複 | distinct − 申告 |
|---|---|---|---|---|---|
| `Q1@openalex` (1 回目) | 736 | 736 | 736 | 0 | 0 |
| `Q2@openalex` (1 回目) | 1606 | 1607 | 1605 | 2 | −1 |
| `Q4@openalex` | 4698 | 4705 | 4694 | 11 | −4 |
| `Q5@openalex` | 6122 | 6130 | 6116 | 14 | −6 |

**頁ごとの条件 1〜6 はすべての頁で `可` である。** 落ちるのは leaf 全体の集計だけである。
結果集合が大きいほど頁境界の重複が増え、distinct が申告総数を下回る。

これは改訂契約 §8 の未決項目 **U11** が想定した状況である。同項は
「索引が同じ work ID を頁境界で 2 回返しつつ総件数では 1 回しか数える場合の、条件 5 の扱い。
現契約では `未完走` になる。本再改訂はこの条件に触れていない」と書いている。
**本走行はこれを実データで観測した最初の記録である。**

## 4. 条件 5 は走行間で非決定的である

本走行は、親の driver の重複除去条件が壊れていたために `Q1` と `Q2` を意図せず再走した。
その結果、**同じ登録 request を同じ日に 2 回投げて条件 5 の判定が両方向に反転した。**

| leaf | 1 回目 | 2 回目 |
|---|---|---|
| `Q1@openalex` | `branch_complete` | `blocked_on_ruling` / `distinct_work_id_total_mismatch` |
| `Q2@openalex` | `blocked_on_ruling` / `distinct_work_id_total_mismatch` | `branch_complete` |

索引側の申告総数と返却集合が走査中に動くためであり、実装の欠陥ではない。
**条件 5 は現行の形では OpenAlex に対して安定した判定にならない。**

機構はこの再走を正しく扱っている。2 回目は `attempt_number=2`・別 raw file (`.a02`) として
記録され、1 回目の証拠は上書きされていない。**検査器の leaf 判定は最後の attempt を採る。**

## 5. 無償枠の扱い

| 項目 | 値 |
|---|---|
| `x-ratelimit-limit` | 1000 |
| `x-ratelimit-credits-used` (1 request あたり) | 10 |
| 契約の `quota_credit_reserve` | 30 |
| 1 窓の発行可能数 | 97 request (`remaining - 30 >= 10`、すなわち残量 40 以上) |
| 本走行の消費 | 94 request (生死確認 1 + 取得 93) |
| 終了時の残量 | 60 |
| 終了時の `x-ratelimit-reset` | 22583 秒 (観測 2026-09-03T02:43:38 JST) |

**自己施錠には入っていない。** 実行器は残量だけを見て発行可否を決めるので、
窓を使い切った観測 (`remaining < 40`) が持続化されると次窓が止まる。
本走行は leaf の起動と起動の間で残量を読み、残量 200 で新規起動を止めた。
**実行器を変えずに窓に収めた。**

## 6. この走行が実装していないこと

- **窓をまたぐ継続取得の設計 (U12) は実装していない。** 持続化した観測に失効を入れる案は、
  枠の発行規範 `remaining - 30 >= 直近観測 cost` (旧改訂 §4.1) を緩める。同節は
  「窓が明ける瞬間は観測していない」と明記しており、`observed_at + reset_seconds` を
  期限とする式は有力な仮説であって凍結済みの発行規範ではない。
  独立レビューがこれを凍結契約の改訂に当たると判定し、親は U12 の裁定なしに採らないと決めた。
- **証拠の時点を外部の事実へ束縛する方式 (U13) は実装していない。** 現行契約にこの束縛は無く、
  検査器は旧生応答の再包装を拒否しない。本走行の証拠は登録 commit の後に新規取得したものだが、
  **検査器はその事実を検証していない。**
- **U11 (条件 5 の扱い) は裁定されていない。** §3 と §4 の観測はその裁定の材料である。
- arXiv と DBLP の再取得は行っていない。新 epoch は全枝の再実行を要求するので、
  両索引も未完走のままである。

## 7. 検査器の出力

`tools/check_axis1_search.py bundle` は次を返した。

- `bundle_validation_complete: true` (manifest の path 集合・digest・schema は健全)
- `passed: false` / `reason_code: leaf_not_run`
- `axis_complete: false`、`classification_complete: false`、`family_ledger_complete: false`、
  `controls_valid: false`
- `incomplete_checkpoint_counts`: `present: 8` / `missing: 251` / `not_run: 251`

`passed: false` は正しい。catalog の 263 leaf のうち本走行が起動したのは OpenAlex の 12 leaf
だけであり、残りは未走だからである。**部分 bundle は例外ではなく既定である** (D1316 の系)。

## 8. 母集合の外

本走行は改訂契約 §1 が引き継いだ母集合をそのまま使う。本走行が新たに除外したものは無い。
