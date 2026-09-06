# 軸 1 検索の実行記録 — 新 epoch `AX1-20260902-E1` の OpenAlex 2 窓目 (2026-09-05)

**これは実行記録であって、登録でも改訂でもない。** 登録の正本は
`2026-09-02-axis1-search-amendment.md`、query program の正本は
`2026-09-02-axis1-search-catalog.json`、1 窓目の実行記録は
`2026-09-03-axis1-search-execution.md` である。本文書は凍結物であり、後から上書きしない。
内容を更新したいときは新しい日付の実行記録を足す。

**軸 1 は `未完走` であり、成熟度は `RW1` のままである。**

## 0. この走行の身元

| 項目 | 値 |
|---|---|
| 作成日 | 2026-09-05 (JST) |
| 登録 epoch | `AX1-20260902-E1` |
| 登録 commit | `4ec3eba04354f9ba86117a2dd488c72d007045e6` (1 窓目と同じ。main の祖先を detach した木を cwd にした) |
| catalog | `docs/related-work/claim-survey/2026-09-02-axis1-search-catalog.json` |
| catalog SHA-256 | `8e23d63a799c8ab9d25151012c34bc738dbb422ac3dfb237999c359137c816ab` |
| 文献 cutoff | `2026-12-31` |
| run ID | `t2090-openalex-20260903` (1 窓目と同じ。2 走目は checkpoint の run ID に束縛される) |
| 索引 | OpenAlex のみ (arXiv / DBLP は本走行でも 1 request も出していない) |
| 生証拠 bundle | `/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle` (1 窓目と同じ root) |
| bundle manifest SHA-256 (取得後) | `99f06ae73f9749fc1d0b32cf92ae0a989c0abe3a5e6805fd98004369e00e3057` |
| 逐語と部分 mirror | `output/insights/2026-09-05_t2090-axis1-openalex-window2/` |

登録検査 (`tools/check_axis1_search.py registration`) は detach した木で `passed: true` を返した。

## 1. 何を起動したか

| 区分 | 起動 | request | 結果 |
|---|---|---|---|
| 独立 2 走目 (`--checkpoint` 000001〜000008) | 8 | 12 | 7 本 `branch_complete`、1 本 `second_pass_digest_mismatch` |
| 初回取得 (`--query-id`、`Q3-SY1997`〜`Q3-SY2018`) | 22 | 69 | 全部 `pass_complete` (checkpoint 000009〜000030) |
| 合計 | 30 | 81 | 残量 189 で停止 (`Q3-SY2019` の手前) |

条件 5 で `未完走` の `Q1` / `Q4` / `Q5` は起動していない (D1624 の優先順位に従い、無償枠を未走 leaf の
初回取得に使った。`Q1` は既に attempt 2 まであり、`Q4` / `Q5` は 24 / 31 request で窓に収まらない)。

重複除去は台帳ではなく bundle の証拠で行った。1 窓目の起動台帳には `Q3-SPRE1991` (5 頁、
checkpoint 000001) が無く、台帳だけで除去すると再走していた。

## 2. leaf ごとの結果

OpenAlex の登録 leaf は 78 本。本走行の後の状態は次のとおり。

| 状態 | 件数 | 内訳 |
|---|---|---|
| `完走` | 8 | `Q2@openalex`、`Q3-SPRE1991`、`Q6-SPRE1991`、`Q3-SY1991`、`Q3-SY1993`〜`Q3-SY1996` |
| pass 1 完了・独立 2 走目待ち (再開点あり) | 22 | `Q3-SY1997`〜`Q3-SY2018` (`checkpoints/000009.json`〜`000030.json`、起動順) |
| 条件 5 で `未完走` (再開点なし) | 3 | `Q1@openalex`、`Q4@openalex`、`Q5@openalex` |
| 独立 2 走目の不一致で `未完走` (再開点なし) | 1 | `Q3-SY1992` |
| 未走 | 44 | `Q3-SY2019`〜`Q3-SY2026` (8)、`Q6-SY1991`〜`Q6-SY2026` (36) |

## 3. 独立 2 走目の照合 — pass 1 (9/3) と pass 2 (9/5) の差

改訂契約の独立 2 走目は、主鍵集合の digest が pass 1 と一致することを要求する。
8 leaf の pass 1 は 2026-09-03 02 時台、pass 2 は 2026-09-05 13 時台で、**2 日の間隔**がある。

| leaf | pass 1 distinct | pass 2 distinct | 集合 | 返却順序 | 判定 |
|---|---|---|---|---|---|
| `Q3-SPRE1991` | 951 | 951 | 一致 | 変化 | `branch_complete` |
| `Q6-SPRE1991` | 53 | 53 | 一致 | 変化 | `branch_complete` |
| `Q3-SY1991` | 117 | 117 | 一致 | 変化 | `branch_complete` |
| `Q3-SY1992` | 187 | 188 | **pass 2 に 1 件増** | 変化 | `second_pass_digest_mismatch` |
| `Q3-SY1993` | 175 | 175 | 一致 | 変化 | `branch_complete` |
| `Q3-SY1994` | 166 | 166 | 一致 | 変化 | `branch_complete` |
| `Q3-SY1995` | 182 | 182 | 一致 | 変化 | `branch_complete` |
| `Q3-SY1996` | 194 | 194 | 一致 | 変化 | `branch_complete` |

- 返却順序は 8 leaf すべてで変わった。条件 1 は順序非依存なので判定に影響しない。
- `Q3-SY1992` で増えたのは `https://openalex.org/W7208063655` (`publication_date` 1992-01-01) で、
  pass 1 に無く pass 2 にある。**申告総数 (`declared_total`) も 187 → 188 に動いた。**
  `2026-09-03b-axis1-cond5-confirmations.md` は同日内の 2 走について「申告総数は動かない、動くのは
  順序」と確かめ (§4)、「登録された独立第 2 走の安定性は未観測」と書いていた (§7.1)。本走行はその
  未観測点を初めて埋める: **2 日を隔てた登録第 2 走では 8 leaf 中 7 leaf で集合が安定し、1 leaf で
  申告総数ごと 1 件増えた。** 索引に後から追加された work と読むのが自然だが、snapshot 識別子が無いので
  機序は 9/3b と同じく確定しない。D1331 の (a) は本走行では扱っていない (9/3b が完了済み)。
- 不一致の leaf には後継 checkpoint が書かれない。再取得しか経路が無く、再取得しても索引が動けば同じ形で落ちる。
  2 走目の間隔を短くする (同日内に 2 走を終える) ことで避けられる可能性が高いが、本走行は試していない。
  取得 program の裁定事項として [T-2258] / U11 の材料に加える。

## 4. 無償枠の扱い

| 項目 | 値 |
|---|---|
| `x-ratelimit-limit` | 1000 |
| 生死確認 (`per-page=1`) の消費 | 1 credit (12:49 JST、残量 999、reset 72643 秒) |
| 取得 (`per-page=200`) の消費 | 1 request あたり 10 credit、81 request で 810 credit |
| 停止時の残量 | 189 (13:11:42 JST、reset 71299 秒 → 翌 09:00 JST) |
| 自己施錠 | 入っていない |

**request の消費 credit は頁の大きさに比例する** (`per-page=1` で 1、`per-page=200` で 10)。
1 窓目の記録は 200 頁の値だけを見ていた。生死確認は `per-page=1` なら取得 1 頁の 1/10 で済む。

駆動 loop は起動と起動の間に `state/runtime.json` の残量を読み、200 未満で新規起動を止めた。
1 回目の loop は、前窓 (9/3) の持続観測 `remaining=60` を今窓の残量と読んで 1 本も投げずに止まった。
閾値検査を緩めずに、正規 runner で checkpoint 000001 の 2 走目を 1 本手動起動して観測を今窓の値に
更新し、同じ loop を再起動した。実行器の発行規範 (`remaining - 30 >= cost`) は変えていない。

## 5. この走行が実装していないこと

1 窓目と同じ。窓をまたぐ継続取得の設計 (U12)、証拠時点の外部束縛 (U13)、条件 5 の扱い (U11、
D1564 で現状維持)、arXiv / DBLP の再取得は、いずれも行っていない。repo の実装面の差分は 0。

## 6. 検査器の出力

`tools/check_axis1_search.py bundle` は次を返した (全文は insight の `bundle-check.json`)。

- `bundle_validation_complete: true`、`exact_identity_map: true`
- `passed: false` / `reason_code: leaf_not_run` (catalog 263 leaf のうち arXiv / DBLP と OpenAlex 44 leaf が未走)
- `leaf_state_counts`: `complete: 8` / `incomplete_with_evidence: 4` / `incomplete_without_complete_pass: 251`
- `incomplete_checkpoint_counts`: `present: 22` / `missing: 229` / `not_run: 229`

pass 1 だけ完了した 22 leaf は `leaf_page_evidence_missing` を理由に `incomplete_without_complete_pass`
と診断される。これは「独立 2 走目の証拠が無い」の意味であり、checkpoint と `resume_action=start_independent_pass` を持つ。

## 7. 次の窓の再開点

- 独立 2 走目 22 本: `--checkpoint <bundle>/checkpoints/000009.json`〜`000030.json`
  (各 checkpoint の `canonical_runner_argv` が逐語の argv)。
- 未走 44 leaf: `--query-id <ID>` で新規開始。
- 再開点の無い 4 leaf (`Q1`、`Q4`、`Q5`、`Q3-SY1992`) は再取得しか経路が無い。

## 8. 母集合の外

本走行は改訂契約 §1 が引き継いだ母集合をそのまま使う。本走行が新たに除外したものは無い。
