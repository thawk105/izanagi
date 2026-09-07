# 軸 1 検索の実行記録 — 新 epoch `AX1-20260902-E1` の OpenAlex 3 窓目 (2026-09-07)

**これは実行記録であって、登録でも改訂でもない。** 登録の正本は
`2026-09-02-axis1-search-amendment.md`、query program の正本は
`2026-09-02-axis1-search-catalog.json`、1 窓目の実行記録は
`2026-09-03-axis1-search-execution.md`、2 窓目は `2026-09-05-axis1-search-execution.md` である。
本文書は凍結物であり、後から上書きしない。内容を更新したいときは新しい日付の実行記録を足す。

**軸 1 は `未完走` であり、成熟度は `RW1` のままである。**

## 0. この走行の身元

| 項目 | 値 |
|---|---|
| 作成日 | 2026-09-07 (JST) |
| 登録 epoch | `AX1-20260902-E1` |
| 登録 commit | `4ec3eba04354f9ba86117a2dd488c72d007045e6` (1・2 窓目と同じ。main の祖先を detach した木を cwd にした) |
| catalog | `docs/related-work/claim-survey/2026-09-02-axis1-search-catalog.json` |
| catalog SHA-256 | `8e23d63a799c8ab9d25151012c34bc738dbb422ac3dfb237999c359137c816ab` |
| 文献 cutoff | `2026-12-31` |
| run ID | `t2090-openalex-20260907` (本窓の初回取得。2 走目は 1 本も起動していない) |
| 索引 | OpenAlex のみ (arXiv / DBLP は本走行でも 1 request も出していない) |
| 生証拠 bundle | `/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle` (1・2 窓目と同じ root) |
| bundle manifest SHA-256 (取得後) | `7fd6a7a2c95056e93e999a03dd331c6e5e53ca3b0a703f768863f9f68efbf462` |
| 逐語と部分 mirror | `output/insights/2026-09-07_t2090-axis1-openalex-window3/` |

登録検査 (`tools/check_axis1_search.py registration`) は detach した木で `passed: true` を返した。

## 1. 何を起動したか

| 区分 | 起動 | request | 結果 |
|---|---|---|---|
| 初回取得 (`--query-id`、`Q3-SY2019`〜`Q3-SY2026`) | 8 | 51 | 6 本 `pass_complete`、2 本 `blocked_on_ruling` (条件 5) |
| 初回取得 (`--query-id`、`Q6-SY1991`〜`Q6-SY2013`) | 23 | 30 | 全部 `pass_complete` |
| 独立 2 走目 (`--checkpoint`) | 0 | 0 | 起動していない |
| 合計 | 31 | 81 | 残量 189 で停止 (`Q6-SY2014` の手前) |

起動は 11:38:01〜11:44:07 JST。新しい checkpoint は `000031`〜`000059` の 29 本。

**無償枠は D1624 の優先順位に従って未走 leaf の初回取得に使い、独立 2 走目には届かなかった。**
条件 5 で `未完走` の `Q1` / `Q4` / `Q5` は本走行でも起動していない。

頁数は枝と年で大きく違う。`Q6` の年 shard は 2006 年まで 1 頁、2007 年以降 2 頁。`Q3` の最近年は
`SY2019`〜`SY2023` が 4 頁、`SY2024` が 6 頁、`SY2025` が 9 頁、`SY2026` が 16 頁で、
`Q3-SY2026` 1 本で 16 request (160 credit) を使う。

重複除去は台帳ではなく bundle の証拠 (`pages/<ID>_p0.a01.json` と `ledgers/<ID>.pass2.*`) で行った。
**checkpoint 側の照合 key は `query_id` ではなく `leaf_query_id` である** — `query_id` は shard 親
(`AX1-20260902-E1-Q3@openalex`) で、台帳の file 名は shard の leaf ID で付く。2 窓目の駆動 script は
`query_id` で照合しており 2 走目の重複除去が 1 件も効いていなかった (当時は pass2 台帳が 0 件で実害なし)。

**本窓で pass 1 を取った leaf の 2 走目は回していない。** 初回取得が書いた checkpoint は
`second_pass.state = not_started` なので即座に 2 走目の候補になるが、それは同日内の 2 走目にあたり、
間隔の可否は [T-2258] の未裁定事項である。checkpoint の `quota.observed_at_jst` が当日のものは
計画から外した。

## 2. leaf ごとの結果

OpenAlex の登録 leaf は 78 本。本走行の後の状態は次のとおり。

| 状態 | 件数 | 内訳 |
|---|---|---|
| `完走` | 8 | 2 窓目から変わらない (本走行は 2 走目を 1 本も回していない) |
| pass 1 完了・独立 2 走目待ち (再開点あり) | 51 | `checkpoints/000009.json`〜`000059.json` |
| 条件 5 で `未完走` (再開点なし) | 3 | `Q1@openalex`、`Q4@openalex`、`Q5@openalex` |
| 独立 2 走目の不一致で `未完走` (再開点なし) | 1 | `Q3-SY1992` |
| 条件 5 で pass 1 が落ちた (再開点なし) | 2 | `Q3-SY2025`、`Q3-SY2026` |
| 未走 | 13 | `Q6-SY2014`〜`Q6-SY2026` |

## 3. 条件 5 で落ちた 2 leaf — 申告総数は動かず、重複と欠落が同時に出た

`Q3-SY2025` と `Q3-SY2026` は `distinct_work_id_total_mismatch` で `blocked_on_ruling` になり、
後継 checkpoint が書かれない。数値は bundle の page evidence と pass 1 台帳の現物から読んだ。

| leaf | 頁数 | 申告総数 (全頁で一定) | 返却 occurrences | distinct | 重複 | 申告に届かない分 |
|---|---|---|---|---|---|---|
| `Q3-SY2025` | 9 | 1678 | 1681 | 1676 | 5 | 2 |
| `Q3-SY2026` | 16 | 3034 | 3035 | 3031 | 4 | 3 |

- **申告総数は 1 leaf の取得中 (数十秒) の全頁で 1 度も動かなかった。** 2 窓目の `Q3-SY1992` は
  2 日を隔てた独立 2 走目で申告総数ごと動いており、本件はそれとは別の現象である。
- 形は U11 (同じ work ID を頁境界で 2 回返しつつ総件数では 1 回と数える) に一致する。
  ただし**重複を除いても distinct が申告総数に 2〜3 件届かない**ので、重複だけでは説明が付かず、
  申告されながら 1 度も返らない ID が残る。D1331 の (a) に関わる観測だが、snapshot 識別子が無いので
  機序は確定しない。
- D1623 は U11 に免除を与えず現契約どおり `未完走` とすると裁定しており、本走行の結果はその裁定の
  とおりである。**条件 5 は緩めていない。**

## 4. 無償枠の扱い

| 項目 | 値 |
|---|---|
| `x-ratelimit-limit` | 1000 |
| 生死確認 (`per-page=1`) の消費 | 1 credit (11:35:29 JST、残量 999、reset 77071 秒 → 翌 2026-09-08 09:00 JST) |
| 取得 (`per-page=200`) の消費 | 1 request あたり 10 credit、81 request で 810 credit |
| 停止時の残量 | 189 |
| 自己施錠 | 入っていない |

駆動 loop は起動と起動の間に `state/runtime.json` の残量を読み、200 未満で新規起動を止めた。
`runtime.json` の持続観測は走り出しの時点で前窓 (9/5 13:11 JST、`remaining=189`) のままであり、
今窓の実値は runner が 1 request 出すまで更新されない。2 窓目と同じく、閾値検査を緩めず、
正規 runner を 1 本だけ手動起動して観測を今窓の値に更新してから loop を回した。
実行器の発行規範 (`remaining - 30 >= cost`) は変えていない。

## 5. この走行が実装していないこと

1・2 窓目と同じ。窓をまたぐ継続取得の設計 (U12)、証拠時点の外部束縛 (U13)、条件 5 の扱い (U11、
D1564 / D1623 で現状維持)、arXiv / DBLP の再取得は、いずれも行っていない。repo の実装面の差分は 0。

## 6. 検査器の出力

`tools/check_axis1_search.py bundle` は次を返した (全文は insight の `bundle-check.json`)。

- `bundle_validation_complete: true`、`exact_identity_map: true`
- `passed: false` / `reason_code: leaf_not_run` (arXiv / DBLP と OpenAlex 13 leaf が未走)
- `leaf_state_counts`: `complete: 8` / `incomplete_with_evidence: 4` / `incomplete_without_complete_pass: 251`
- `incomplete_checkpoint_counts`: `present: 51` / `missing: 200` / `not_run: 198`

**検査器の leaf 診断は `Q3-SY2025` / `Q3-SY2026` を `leaf_page_evidence_missing` と報告する。**
独立 2 走を要する shard leaf なので `expected_passes` が `[1, 2]` になり、「pass 2 の証拠が無い」が
先に立つためで、走行時の理由 `distinct_work_id_total_mismatch` は台帳側にしか残らない。
非 shard の `Q1` / `Q4` / `Q5` は `expected_passes` が `[1]` なので条件 5 が leaf 診断に出る。

## 7. 次の窓の再開点

- 未走 13 leaf: `--query-id AX1-20260902-E1-Q6-SY2014@openalex` 〜 `Q6-SY2026@openalex` で新規開始。
- 独立 2 走目 51 本: `--checkpoint <bundle>/checkpoints/000009.json`〜`000059.json`
  (各 checkpoint の `canonical_runner_argv` が逐語の argv)。1 窓には収まらない。
  `000031`〜`000059` は本窓に pass 1 を取ったので、9/8 以降なら同日内にならない。
- 再開点の無い 6 leaf (`Q1`、`Q4`、`Q5`、`Q3-SY1992`、`Q3-SY2025`、`Q3-SY2026`) は再取得しか経路が無い。

## 8. 母集合の外

本走行は改訂契約 §1 が引き継いだ母集合をそのまま使う。本走行が新たに除外したものは無い。
