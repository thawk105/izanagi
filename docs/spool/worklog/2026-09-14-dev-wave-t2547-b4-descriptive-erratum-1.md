---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-t2547-b4-descriptive-erratum
seq: 1
title: [T-2547] B-4 を記述統計へ限定する追補を事前登録へ足し、適格な赤 precursor が 0 件であることを実測した (docs のみ、branch worktree-dev-wave-t2547-b4-descriptive-erratum)
---

## 本文

- 依頼は D1936 項 8 の追補で、「まず在庫を実測し、0 件なら追補だけを着地させて在庫取得を
  別項として残す」という条件つきだった。**在庫は 0 件だった**ので、その分岐で進めた。
  一次資料 = `output/insights/2026-09-14_t2547-b4-descriptive-erratum/`。
- **在庫の実測。** 合成ループ 3 campaign の whiteboard は合計 7 行で全て `success`、
  `rejected` は 0 行。別 campaign の rejections digest にある赤 3 件は同 campaign が
  whiteboard を持たないため適格性述語の第 1 項を満たさない。段 3 の指摘で
  `layer3_report.json` 7 件も親が独立に調べたが、1 件は既存の成功 2 行の再掲、
  残る 6 件は `rejected` を 1 件も含まなかった。**前回計数 (2026-09-10) から変化なし。**
- **適格性述語の第 2〜6 項は、そもそも適格性を確認できる状態にない。** 校正済み workload、
  固定 bootstrap 集合、共通 reference、両アーム digest 非汚染のいずれも §5 の該当欄が
  未記入である。3 loop の lock は `reflux:on` なので非汚染の証拠にもならない。
  第 1 項だけで 0 件が確定するため結論は変わらないが、「適格と確認したうえで 0 件」ではなく
  「第 1 項で落ちて 0 件」であることを記録しておく。
- **段 3 の敵対相談が must-fix を 1 件出した — 追補は機械出力を 1 つも変えない。** 事前登録を
  読む consumer は §5.1.1 の bytes と §5 の表と floor セルしか見ず、追補の意味を解釈する経路が
  無い。親の当初の成果説明は「材料レポートの報告型が機械的に変わる」と誤読されうる書き方
  だった。追補本文へ「限定するのは人が報告に書いてよい主張の上限だけ」「機械が生成する
  値・分類・参照は 1 つも変わらない」を明記して閉じた。決定は {{D:b4-descriptive-erratum-scope}}。
- **裁定の「適格な少数の赤 precursor を使う」は、現在実行できない。** 適格 0 件であることに
  加えて、少数の適格赤を得たときに §5.1.1 の選択関数 (適格行が n 未満なら実走しない) と
  どう両立させるかが未解決である。追補には「方針は維持するが、その利用は本追補では実現して
  いない」と書き、**未解決点は裁定パッケージとしてユーザーへ返した**。新しい機構は作っていない。
- **分岐条件を取り違えかけた。** §5.1 の文言は「**予算上** n を確保できないなら」、
  凍結された §5.1.1 は「**適格な block を 201 件確保できない場合**」で、今回の事実は後者である。
  §5 の総計測予算欄は未記入で予算不足は確認していない。段 2・段 3 の 3 子とも同じ区別を
  独立に支持した。
- **親の資料に過大な断言が 4 件あり、段 3・段 6 の 4 子が全件指摘した。** (a)「§5.1.1 の
  2 重 sha256 がこの文書の bytes を pin する唯一の経路」— 実際は admission record が宣言 commit の
  **文書全体** sha256 と HEAD blob 一致を要求する。(b)「§5 表の parser は `### 5.1` より後ろを
  一切読まない」— parser は文書全体の markdown 文脈を走査する。読まないのは「表の値として
  評価しない」だけ。(c)「§5.1 は bytes を pin されていない」— (a) より偽。
  (d) ディレクトリの mtime を「前回計数から増えていない」証拠に使ったこと — worktree では
  同じ mtime が再現しないと段 3 が実測した。**「今回 0 件」は再読取りが支持するが、
  「前回以降増えていない」は証明していない。**4 件とも撤回して記録した。
  admission record は 3 driver 分いずれも不在なので、無効化される既存 admission は 0 件である。
- **段 6 の敵対レビュー 2 本が、両方とも同じ must-fix を出した。** 追補が「逐語を insight へ
  保存した」と断言しているのに、その実体をまだ作っていなかった。**記録より先に断言していた。**
  実体を作って断言を真にした。失敗の型は {{F:asserted-artifact-before-creating-it}}。
- **段 6 の片方が凍結境界を独立検証した。** 追補の前後で §5.1.1 の抽出 bytes は 21,833 bytes
  完全一致 (raw sha256 `0ceab4cd...`、semantic sha256 `5d0b189b...`)。3 経路とも追補を抽出範囲に
  含まない。**ただし文書全体の sha256 は変わる**ので「§5.1 は pin されていない」と一般化しない。
- **セッション異常 1: 背景待ち手の完了通知が誤報だった。** 段 6 の片方で、待ち手が空の出力で
  早期終了したのに完了通知だけが届いた。`.done` は不在、成果物も不在、producer は `ps` で生存中。
  `.done` の非空で判定する規律がそのまま効いた。待ち手を張り直して正常完了した。F883 の再発。
- **セッション異常 2: review 段に `--lane` を渡して rc=2 即死。** `--lane` は consult 専用である。
  argv を dry-run で先に検査していたため実害は 0 で、同じ prompt を lane なしで投げ直した。
- **エージェント工数:** codex 子 5 本 (plan 1 / consult 2 / review 2)。全件
  `tools/check_codex_output.py` rc=0。実装面の差分がゼロなので実装子は 0 本で、docs 本文は親が
  書いた。read-only の子は pytest を実走していない。
- **親が実走した検査:** `tools/check_docs.py` rc=0 (編集前 baseline も rc=0)、
  `git diff --check` rc=0、`python3 -m orchestrator.campaign.s8b_holdout_freeze search` rc=0
  (holdout の conjunction hit 0、positive control は 173 件で発火)。
  焦点走 14 file を fix 前後で 2 回、いずれも `1085 passed, 1 skipped` / child rc=0
  (Pegasus 計算ノードへ dispatch、request `996048.nqsv` と `996063.nqsv`、Elapse 150S と 152S)。
  焦点走の対象集合は段 3 の指摘で `test_real_repo_serialization.py` を足して 14 file にした。
  **実装面の差分がゼロなので変異 matrix は `DW-S04` により免除した。受入全走は免除していない。**

## 次の一手差分

### 完了

- [T-2547] 本項が待っていたユーザー裁定は D1936 項 8 として下り、その記述統計追補を
  事前登録へ着地させた。母集合の作り方について本項が問うていた択一 (n を下げるか、
  precursor の供給源を変えるか) は、裁定が「どちらも採らず、供給源と適格条件を変えずに
  記述統計へ限定する」と決着させている。裁定が開いたまま残した 2 点は
  {{T:b4-eligible-red-precursor-supply}} と {{T:b4-small-sample-vs-selection-function}} へ引き継いだ。
  remaining: none
  base: a369a87b9e472990284acb7b43dfb5d19b2a65f066593c08b8a6f7e741ff8b4b

### 新規

- {{T:b4-eligible-red-precursor-supply}} **P2・新規**: B-4 の適格な赤 precursor の在庫を
  0 件から増やす。供給源 (合成ループ campaign の whiteboard) と §5.1.1 の適格条件は変えない。
  成功例への置換と母集合を作るための追加基盤は D1936 項 8 が不採用にしている。
- {{T:b4-small-sample-vs-selection-function}} **P1・ユーザー裁定待ち**: D1936 項 8 の
  「適格な少数の赤 precursor を使う」と、§5.1.1 の選択関数 (適格行が n 未満なら
  `design_not_feasible` として実走しない)・D1880 の 201 行契約の関係が未解決である。
  少数を得たときに何が許されるのかを裁定する。AI は受理集合を単独で変えない。
