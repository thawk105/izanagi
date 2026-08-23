# [T-986] freeze v2 budget pin — pre-approval decision dossier

```text
authority: none
default_effect: no-state-change
STATUS: NOT APPROVED / NON-CANONICAL / NON-OPERATIONAL
```

## 結論

freeze v2 の budget 数値は、現時点では**承認保留**を推奨する。

- `n=8` を仮定した planning candidate は `total_bench_s=2592`、
  `per_holdout_bench_s={rr20:1296, rr80:1296}`。
- これは既存 Pegasus pilot の最大 session duration を 27 秒へ切り上げた条件付き見積りであり、
  承認値、approval JSON、pin、official launch のいずれでもない。
- 現行 consumer は承認上限とは別に、名目 `25 秒 × schedule 行数` を reservation にする。
  `n=8` では 2400/1200 秒であり、承認上限を 2592/1296 秒へ増やしても実行中の envelope は
  2400/1200 秒のままである。
- pilot の `session duration` と consumer が計上する `pipeline.bench_wall_s` は同一量ではない。
  したがって 2592/1296 を operational な値として承認する根拠も、2400/1200 で必ず失敗すると
  断定する根拠も、まだ揃っていない。

本 dossier が整備するのは、見積り根拠、pilot 実測、数値択、不確実性、停止条件である。
数値承認、`BUDGET_APPROVAL_SHA256` の変更、official guard 解禁、正式 launch は scope 外である。

## 1. 現在の authority と schema

| 項目 | 現況 |
|---|---|
| canonical approval path | `output/s8b-freeze-budget-approvals/g1.json` |
| canonical approval file | 不在 |
| trust-root pin | `BUDGET_APPROVAL_SHA256 = None` |
| v2 durable candidate | 未発行 |
| official eligible floor result | 不在 |
| synthetic fixture | schema 正例だけ。100/50 の便宜値を見積り根拠に不使用 |

固定 path と `None` pin は `orchestrator/campaign/s8b_holdout_freeze.py:47-60`、budget validator と
approval loader は同 `:1267-1339` にある。budget の exact key は次の 3 つである。

```text
total_bench_s
per_holdout_bench_s
oracle_shared = true
```

各数値は有限非負、holdout key 集合は active freeze と完全一致する。candidate producer は pinned
approval の raw hash、入力 budget との canonical bytes 一致、official eligible floor を要求する
(`s8b_holdout_freeze.py:1689-1756`)。本 dossier はこの producer を起動しない。

## 2. 量の crosswalk

| 記号 | 実体 | 境界・比較先 |
|---|---|---|
| `B` | approval schema の上限 | reservation `R` が `B` 以下かを admission で検査 |
| `R` | `extime × reps × bench_max_rounds × rows` | ledger の初期 reserved/charged。crash 時は保持 |
| `X(k)` | k 行目までの `pipeline.bench_wall_s` 累積 | `B` でなく `R` と比較 |
| `D` | n-pilot の `session duration` | admission + `measure_point` + 直後検査。build は session 外 |
| `W` | allocation wall | session 外の小さい残余も含む。budget へ自動加算しない |

設計上の第一単位は累積ベンチ実時間であり、build/verify/bench/timeout の wall は別途記録する
(`docs/phase3-8b-descriptor-design.md:199-212`)。correctness は trace-enabled、性能値は
trace-disabled の別 build・別 run であり、性能 pilot の rc を correctness 証拠に昇格しない。

現行 reservation は `s8b_oracle_driver.py:1523-1543`、admission は
`s8b_budget.py:453-505`、実測累積を reservation と比較する箇所は同 `:559-585` にある。
`bench_wall_s` は `pipeline.py:488-522` の `bench_started` から測る。

正確な含意は次である。

```text
R <= B なら admission 成立後の実行時 envelope は R
R > B なら allocation 自体が admission 不成立
X(k) > R なら reservation envelope failure
```

`B-R` は現行 driver の当該 reservation では実測超過の吸収に使えない。

## 3. pilot 一次資料

| field | value |
|---|---|
| raw result | `/work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/alloc/t1142-run-1/result.json` |
| raw SHA-256 | `cdd5ade4017e86ba8079a8f7c6e9ed5a42332967a779f0777e9833998417d3fd` |
| schema/status | `pilot-result/v1` / `completed` |
| host | Pegasus `bnode009` |
| source commit | `0b35d79141259a0ccbb84b4987918c9e3f173c9f` |
| ccbench pin | `511c9538e4e8efa54b45cda62e72389ed3b706ec` |
| environment contract | `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` |
| performance lane | trace-disabled、perf unavailable/off |
| shape | rr20/rr80 × 6 configurations × 11 rounds = 132 sessions |
| per session | reps=5、extime=5 秒 |
| eligibility | certified/floor_input/oracle_input/n_decision は全て false |

これは 2026-08-16 に sanctioned `oracle n pilot` が計算ノードで取得した実測である。今回、新しい
performance run は投入していない。T-1484/T-1505 の acceptance と計測面を重ねていない。

## 4. 再集計契約

再集計は raw bytes の SHA-256 を先に照合し、次を全て満たす record だけを採用した。

1. `sessions` は 132 件、`seq` は重複なしの 0..131。
2. `(pilot_round, cell_id)` は 132 組すべて一意。
3. round 集合は 1..11、cell 集合は rr20/rr80 × 6 configurations の完全積。
4. 各 session の duration は有限正、return code は exactly 5 件かつ全て 0。
5. 欠測、重複、非有限、cell/holdout 不完全は補間せず再集計無効。

quantile は昇順列 `v` の `v[floor((N-1)*p)]` とした。表示は小数 6 桁、積と比率は raw full
precision で計算するため、表示値を使う式は `≈` とする。

### 全体・holdout 別

| group | N | min s | mean s | p50 s | p95 s | p99 s | max s | sum s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all | 132 | 26.708816 | 26.781041 | 26.775756 | 26.840070 | 26.853454 | 26.868566 | 3535.097348 |
| rr20 | 66 | 26.718392 | 26.778202 | 26.775204 | 26.840070 | 26.846620 | 26.853454 | 1767.361320 |
| rr80 | 66 | 26.708816 | 26.783879 | 26.782421 | 26.838093 | 26.864512 | 26.868566 | 1767.736028 |

allocation wall は 3537.500289 秒で、session 合計との差は 2.402940 秒だった。この差は `X` と
同一と証明されていないので budget 値へ加算しない。

### cell 別

| cell | N | min s | mean s | p50 s | p95/p99 s | max s |
|---|---:|---:|---:|---:|---:|---:|
| rr20/backoff_fixed_best | 11 | 26.751527 | 26.773713 | 26.775204 | 26.783791 | 26.796092 |
| rr20/ident_all | 11 | 26.718392 | 26.775297 | 26.768134 | 26.803468 | 26.840070 |
| rr20/p2_2_flag_opt | 11 | 26.771679 | 26.803312 | 26.798975 | 26.846620 | 26.853454 |
| rr20/sort_best | 11 | 26.739093 | 26.762029 | 26.755989 | 26.783476 | 26.813514 |
| rr20/stock_common | 11 | 26.731443 | 26.766297 | 26.750212 | 26.827924 | 26.836852 |
| rr20/system_gate | 11 | 26.738776 | 26.788563 | 26.788611 | 26.844006 | 26.846588 |
| rr80/backoff_fixed_best | 11 | 26.783804 | 26.808362 | 26.806104 | 26.838093 | 26.847388 |
| rr80/ident_all | 11 | 26.714163 | 26.758994 | 26.768999 | 26.782452 | 26.796374 |
| rr80/p2_2_flag_opt | 11 | 26.782421 | 26.816424 | 26.817239 | 26.839058 | 26.864512 |
| rr80/sort_best | 11 | 26.746102 | 26.779131 | 26.762769 | 26.820264 | 26.831202 |
| rr80/stock_common | 11 | 26.719295 | 26.770174 | 26.769713 | 26.816023 | 26.821796 |
| rr80/system_gate | 11 | 26.708816 | 26.770190 | 26.766275 | 26.822623 | 26.868566 |

N=11 では p95 と p99 が同じ index になる。細かい percentile を精密推定したという意味ではない。

## 5. 見積り式と `n=8` 条件の候補

oracle schedule は 1 replicate ごとに `holdout × configuration` の完全積を作る
(`s8b_oracle_manifest.py:234-285`)。holdout=2、configuration=6 なら、

```text
L_total(n) = 12n
L_holdout(n) = 6n
R_total(n) = 25 * 12n = 300n
R_holdout(n) = 25 * 6n = 150n
```

run contract は legacy+s2、screening off、bench_max_rounds=1、承認凍結済み reps/extime を強制する
(`s8b_oracle_manifest.py:424-454`)。`n=8` は別 package の未承認値である。

| 数値 | total s | rr20 s | rr80 s | 意味 |
|---|---:|---:|---:|---|
| nominal reservation | 2400 | 1200 | 1200 | 現行 R。余裕ゼロ |
| pilot global mean projection | 2570.979890 | — | — | D を X の代理にした推定 |
| holdout mean projection | — | 1285.353687 | 1285.626202 | holdout 別 D 平均 × 48 |
| observed global max projection | 2579.382345 | — | — | 単一 allocation の観測最大外挿 |
| 27 s/session planning candidate | 2592 | 1296 | 1296 | conditional、non-operational |

平均 session duration は nominal 25 秒より約 7.124%長い。27 秒は観測最大 26.868566 秒より約
0.489%長いだけで、allocation 間変動や将来環境への安全 margin ではない。

## 6. 不確実性

| 不確実性 | 現況 | 承認への影響 |
|---|---|---|
| D と X の数量同値性 | 未成立 | pilot 値を operational budget へ直接使えない |
| reservation envelope | B を増やしても R は名目値 | 数値承認だけでは余裕を実行時に使えない |
| n | 8 は未承認 | 全固定値は n=8 条件に限る |
| allocation 間変動 | 単一 allocation で未推定 | observed max を上側保証にできない |
| perf-off | 代表性への影響 unknown | perf-on 系列へ外挿しない |
| certification | pilot eligibility 全 false | official/floor/oracle proof に昇格しない |
| correctness | trace-disabled、rep rc=0 | correctness pass を意味しない |
| build/verify/timeout wall | session duration の外 | bench cap と混ぜず別 wall 記録が必要 |
| source/env drift | 1 commit・1 host 条件 | 変更が測定量へ効くかで再利用可否を再評価 |

## 7. fail-closed matrix

| 条件 | 判定 |
|---|---|
| `R > B` | allocation を起動しない |
| `X(k) > R` | envelope failure。性能値を採用しない |
| raw hash 不一致 | 再集計無効 |
| 欠測・重複・非有限・cell/holdout 不完全 | 補間せず再集計無効 |
| correctness gate 不在・失敗 | official eligibility / floor / candidate を開かない |
| 未実行 arm | 対称に indeterminate |
| trace-disabled pilot / rep rc=0 | performance 実行健全性だけ。correctness 証拠ではない |

通る正例は、本 raw の hash exact、132 unique sessions、12 cell 各11件、全 duration 有限正、全 rep
rc=0 である。それでも出力は planning evidence にしかならない。

## 8. proof-chain の現在地

| edge | status |
|---|---|
| raw bytes → SHA-256 | 成立 |
| raw → deterministic reaggregation | 成立 (本 dossier の規則) |
| pilot D → consumer X の quantity equivalence | **未成立** |
| n / schedule mapping | n=8 条件の式だけ。n は未承認 |
| user numeric ruling | **未実施・scope 外** |
| canonical approval JSON equality | **未作成・scope 外** |
| `BUDGET_APPROVAL_SHA256` pin | **None のまま・scope 外** |
| official eligible floor | **不在・scope 外** |
| v2 candidate | **未発行・scope 外** |

package 自体を approval record に見せない。canonical loader が読める JSON や approval path 配下の
模擬成果物は作らない。

## 9. T-1484/T-1505 との ownership

| 面 | T-986 | T-1484/T-1505 |
|---|---|---|
| code edit | なし | attempt registry core、8c facade、8b profile |
| tests | 今回は既存関連検査を実走するだけ | mutation 完了後の acceptance |
| performance measurement | 既存 T-1142 raw の再集計のみ。新規投入なし | なし (acceptance は test) |
| artifacts | 本 insight、spool fragment、専用 handoff | 別 worktree/job dir/acceptance receipt |

開始時と段 4 で worktree・branch・外部 handoff・生存 process を照合した。共有編集、floor campaign、
oracle campaign、同一 measurement output のいずれも起こしていない。

## 10. 将来の数値裁定択 (今回は裁定しない)

### (a) 保留 — 推奨

quantity equivalence と reservation 契約を解き、n が確定してから operational 値を再提示する。
本 dossier の 2592/1296 は planning scale としてだけ保持する。

### (b) 2592/1296 を operational approval にする — 現証拠では非推奨

pilot D を consumer X と同一視できず、B-R の余裕が現行 envelope で使えない。

### (c) 2400/1200 を operational approval にする — 非推奨

現行 nominal reservation と一致するだけで、consumer observable に対する正の余裕がない。

## 11. scope 外所見と再開条件

1. consumer と同じ `pipeline.bench_wall_s`、正式 schedule mapping、複数 allocation、pinned
   source/config、欠測禁止を持つ nonofficial calibration があれば quantity equivalence を閉じられる。
2. approved limit の余裕を reservation へ反映するか、別の正しい envelope 意味論にする設計が必要。
   correctness-red、欠測、timeout を予算緩和で受理してはならない。
3. これらは実装面または追加性能計測であり、D95 と Pegasus runbook に従う別 wave の対象である。

本 wave は所見の記録までで止める。暫定 pin、追加 probe、reservation 修正、official 解禁、正式 launch
を同 scope に追加しない。

## 12. 関連検査

焦点走は `tools/run_tests.py` 経由で次の 21 node を実走した。

- `orchestrator/tests/test_s8b_budget.py` 全体
- budget approval 未批准の先行拒否
- approval と入力 budget の canonical 数値 bytes 比較
- `bench_wall_s=26` が名目 reservation を超える fail-closed 経路

最初の 2 走は test logic より前に `official-output-root` で refusal となった。原因は、pytest の
`/tmp` ancestor に空の `/tmp/.git` があり、job dir ancestor にも `dev-wave-jobs/.git` があるため、
既知 F457 の `_has_git_ancestor()` が basetemp を repository 内と分類したことだった。どちらも
production predicate を変更せず、Git ancestor の無い `/work/1/SFC/tanab/` 直下の `mktemp -d` を
basetemp parent にして再走した。最終結果は **21 passed in 17.12s**。local main `402a5752`
取込み後の再走も **21 passed in 15.65s**。この焦点走は受入全走ではない。

## 13. dev-wave 改善候補

段2 plan の初回 dispatch を `--max-model-calls 1` に狭めたところ、1 call 目が射影資料の読取で
終わり、`f45_missing_output` (output 0 byte) になった。receipt/done を削除せず別 job ID・4 calls で
再投入して完了した。将来 `DW-O01` に「projection を読む plan/consult は1 callへ狭めず、既定または
2以上を使う」と明確化する候補を routing する。新しい失敗型や長期設計判断ではないため、新規 F/D は
作らない。ユーザー指示に従い、本 wave では改善実装を行わない。

## 14. dev-wave の検証資料

- 段 1 brief: repo 外 job dir `stage1-brief.md`
- 段 2 plan: 同 `stage2-plan.md`
- 段 3 adversarial lenses: 同 `stage3-lensA.md` / `stage3-lensB.md`
- 段 4 adjudication: 同 `stage4-adjudication.md`

これらは開発過程の監査資料であり、budget approval や official proof chain ではない。
