# [T-142] 段 4 裁定 — 実装しない・新事実付き再裁定待ち

## 結論

本 wave ではコード・テストを実装しない。2026-07-29 (54) の択 (a) 自体を親が不採用へ戻すのではなく、
裁定時点で未見だった下記 N1〜N4 を添えてユーザー再裁定へ返す。段 5・6 は DW-S04 に従いスキップする。

## 新事実

1. **N1 — production の skip 分岐が到達不能。** sort/trigger の現設定は `reps=2`。
   現行 `compare()` は完全分離した n=2 対 n=2 でも `p=0.1939308523` で `no-difference` を返す。
   親の実行確認でも n=4 対 n=4 で初めて `p=0.0131238068` の `slower` になった。
2. **N2 — exact floor 不在。** 現経路は linux-baremetal・100k records・4 threads・extime=1・reps=2。
   最寄りの between-run floor は 1m・48 threads・extime=3・reps=5 であり流用不可。
3. **N3 — 効果分母が不一致。** 既存 30 WAL を親が再集計すると numeric COMMIT 426、S2 済み
   numeric COMMIT 78、その campaign 内 raw new-best 18。旧 88% は全 COMMIT 混合集計で、
   S2 対象だけの raw skip 上限は 60/78 = 76.9%、実 target sort/trigger は 0/3。
4. **N4 — O の producer と tie 規則が未凍結。** 現 p3 に formal selected/stock/tie producer と
   同一 config の certified stock はない。tie は direct-winner 比較と推移閉包の二つが現存し非同値。

N1、N2、N4 は裁定 package/worklog (54) に存在しない。N3 は「将来分布へ一般化不可」の注意は既知だが、
S2 実走集合で分母を再限定した 78/18 と target 0/3 は未記録だった。

## 所見の裁定

| 所見 | 裁定 | 採否・scope |
|---|---|---|
| direct-winner を AI が O の tie 規則に選べない | real / BLOCKER | 追加ユーザー裁定まで実装外 |
| formal selector・certified stock 不在 | real / BLOCKER | O 保存の機械 positive control が作れない |
| reps=2 では `slower` 到達不能 | real / BLOCKER | G01/G04 により本格実装を止める |
| exact floor 不在 | real / BLOCKER | 別座標の floor 流用は禁止 |
| `build_start` 区切りだけの attempt 再構成 | real | 将来実装なら attempt ID/FSM が必要。今 wave は scope 外 |
| S2 tag 文字列だけの実行証明 | real | 将来実装なら config digest 束縛が必要。今 wave は scope 外 |
| layer3 全 payload redaction | real、plan 案は不採用 | D12 の full forensic ledger を保ち、certified view だけを遮断すべき |
| `STAGE_NOT_PROMOTED`・schema v3 の即時新設 | real な over-scope | 現時点は既存 ABORT reason/redaction 部品で pilot 可能。実装しない |
| replay/p2/s6/s8/freeze の一律改修 | refuted | identity/profile guard で到達不能なら blanket rewrite 不要 |
| planner が 88% を正式期待値にした | refuted | planner は外挿禁止を明記。ただし旧 package の投資根拠は訂正が必要 |

## plan v2

1. 本 wave はコード変更ゼロ、変異 matrix・受入全走の対象外とする。
2. 再開条件をユーザー裁定へ返す:
   - tie を direct-winner と推移閉包のどちらにするか。
   - 現 p3 の O を selected/stock/tie まで実装するか、O_run へ狭めるか。
   - production comparator を到達可能にする reps/測定設計と live campaign をどれにするか。
3. 実装を選ぶ場合も、先に exact-coordinate between-run calibration と paired all-S2/adaptive
   liveness pilot を行い、自然な `s2-not-promoted` 1 件以上・正の wall-time 削減・O 一致を確認する。
4. 推移閉包 tie 維持、live campaign 指定なし、または pilot で skip なしなら T-142 を close する。

## 変異

実装しないため事前登録しない。段 2 の mutation 候補は N1 により production 枝が未到達で、
F28 の単一理由性を満たさない。将来 GO 後に新しい brief/plan/review から再登録する。
