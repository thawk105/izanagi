# [T-2850] 試走 v2 後段 — 段 4 裁定 (2026-09-27 JST、親)

入力: s2/plan.md、s3/consult-a.md (統計・事前登録適合)、s3/consult-b.md (案 (a)・運用・過剰)。wave 開始後の local main の前進 0 (裁定 inbox の更新なし)。

## 所見の裁定

| 所見 | 判定 | 採否・扱い |
|---|---|---|
| a1 §8.1(c) の判定を Elapse 総和 > 200 で代用 | real | 採用。section8.py を「費用上限による未完 (未投入・中断の系列) の有無」で判定し直す (全 18 job 投入・全系列 series-end b-complete)。値の影響なし |
| a2 T_c・s・n の検算 | 問題なし | 追補に到達本数 12/12 と「算出しない場合」(a)(b)(c) 非該当を書く |
| a3 session の集合 (300 slot) と ℓ の集計対象 | 問題なし | 追補に内訳 (系列 270 + block job 30) と score だけの中央値 250.404 s を別記 |
| a4 未試走課題の換算の一般化が強い (P1 の「rh を含む案は 510 超」) | real | 採用。登録式の値 (wh 流用) と換算 (B-5 v1 直列検査) を常に別欄。「510 超」は換算の条件付き |
| a5 score 閲覧の開示 | 疑い → 採用 | 追補 3 に「親は aggregate の出力で score を見た。使ったのは cell ごとの ln score の SD だけ。Q の判断に手法間差・曲線を使っていない」と開示 |
| a6 固定値と発効値の切り分け | 問題なし | plan A どおり |
| b1/b2 案 (a) の導入費・節約は未測定 (P2 の「約 20」も plan の「28.70 が基準」も確定でない) | real | P2 を改める。根拠 = 節約 26.65 node 時間は試走中央値の外挿で回収可能額ではなく、導入費 (再試走・実装・検査・smoke・追加 job) も未測定。本登録 §3.1・追補 2 §5 の先例では実行方法の変更後は試走 v2 の分散・T_c を引き継げず再試走が要る (現方式の実績 28.70 node 時間は参考)。「残る待ち > 導入費」を実測で示せないので設計しない |
| b3 全 arm 分割の job 数下限 | real | 採用。11〜13 job/系列 (切り方次第) と書く |
| b4 実行方法の変更で分散を混ぜない | 問題なし | 上に含める |
| b5 schedule.py の `main()` 名衝突 | real | 採用。spec 生成は `main_comparison(root, n, tasks)`、CLI に `main` 選択肢 (n・課題集合を引数) |
| b6 p ≤ 4 を test で保証と書かない | 疑い → 採用 | 投入手順 (LLM 系列は同時 4 本まで投入・親 config へ載せ、series-end を見て次を載せる) として追補・insight に書く。機械保証とは書かない |
| b7 保全口の env 経路 | 問題なし (静的) | submit test で qsub -v を確かめる。pipeline までの経路は MOCC 疎通 (D2261) の実走で保全 552 反復 complete の先例あり、と書く |
| b8 暦の見積りの欠落 | real | 採用。node 時間・LLM 直列時間 (外挿)・p = 4 の理想下限・系列完了の見込みを別欄。queue と 429 を含む暦の上限は算出不能と明記 |
| b9 [T-2869] | real (開示) | 失敗内訳と A の見積りに反映。修正は本 wave の scope 外 (登録契約との食い違いを示せたときだけ追補で) |
| b10 過剰 | 採用 | glue v4 は schedule・保全 env・小さい test だけ |

## plan v2 (確定)

1. 追補 3 (新規 docs) に: 位置づけ (試走の後・本比較の最初の生成より前、結果を見た後の規則変更は無い)、試走 v2 の実行と欠測の記録、§8.1 の入力 (値と当て方)、
   §8.2 の候補表 (|Q| = 1〜3、n₁・n₂、C(n) の登録式と換算)、Q の推奨 (wh、第 2 段 n = 10、C = 110.5 node 時間) と理由 (費用・実行可能性・失敗の種類)、
   本比較の固定値 (R = 100 + b、cohort `t2850-main-v1`、投入順の鍵、固定 commit 299aa022e、walltime 24:00:00 / 08:53:30、保全口の opt-in、p ≤ 4 の投入手順)、
   ユーザー確認後に発効の決定へ回すもの (C_max、最終の Q と n、保全先の実 path)、案 (a) の判定、score 閲覧の開示。
2. insight `output/insights/2026-09-27/t2850-trial-v2-analysis/README.md`: 集計の方法と表、見積り、暦、(a) 判定、段 2・3 の要約、repo 外成果物の所在。
3. glue v4 (repo 外): 子 worktree の scratch で Codex author、親が pytest・dry-run、job dir `glue-v4/` へ写し出す。
4. spool: worklog 1 (T-2850 更新) と decisions 1。
5. 変異 matrix: repo の実装面の差分 0 のため免除 (DW-S04)。受入全走 1 回。段 6 は read-only レビュー 1 本 (一次資料からの再抽出の検算 + glue v4)。

## scope 外 (起票しない、insight に記録)

- 案 (a) の設計・実装、bal・rh の同時検査の harness 拡張、[T-2869] の修正。
