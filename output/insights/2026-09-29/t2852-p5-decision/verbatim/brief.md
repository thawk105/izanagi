# [T-2852] 進め方の択一 — 相談用 brief (親、2026-09-29 JST)

## 決めること
T-2852 (VLDB 差分分析 P5: workload 記述 × critic の介入) の事前登録の草稿は local main `539556aa1` に着地済み (未発効、D2278)。
次のどちらにするかを決める。
- (a) S1-wh で本走する: 6 cell × n = 3 / 4 / 5 で 72.3 / 96.4 / 120.5 node 時間 (中央値の単価)、LLM の直列 48.0 / 64.0 / 80.0 時間、原提案機会 198〜420。
- (c) 今は投げない: 介入と出力コードの分類を、S3 (関数方策軸、T-2867) の生成器対照の後に別の登録で行う。

## 親の推奨は (c)。材料
1. D2272 項 2 が T-2850 本比較を止めた 3 理由が本書にも残る: (i) S1 で分類が弱い (s_plan を当てると計画半幅 0.049〜0.172 で、同等を言う目安 δ/2 = 0.0148 にどの規模でも届かない)、
   (ii) T-2869 (planner の axis 名の揺れによる拒否) — 本書は D2273 の修正を全 cell に入れるが、修正後の本番の拒否率は未測定で、cell 間で率が違えば効果と混ざる、
   (iii) LLM の待ちが node 上に残る (試走 v2 実測で LLM 系列 job Elapse の 69.9%、block 込みで 60.8%)。429 の週上限で欠測と node 浪費が同時に出うる。
2. S1 の coder 出力は `double now_backoff = <数値>;` の 1 行に固定され、他は文法で拒否される。受理候補に機構の変更は構造上 0 件で、出力コードの分類は機構を説明できない。
3. D2259 は B-5 v2 を「値 1 個での LLM 対照は査読の決め手になりにくい」として見送った。

## (a) を今夜実行できるかの事実
- 草稿 §13 の実装がまだ無い: 記述の水準の切替 (巡 tool・親の指示文)、失敗理由の写し、critic なしの経路 (harness の継承の照合が評価 2 以降に critic 診断を必須にしており、変更が要る)、
  役割文書 (`.claude/agents/planner-v4.md`・`coder-v4-autonomous.md`) の入力節の改訂 (D2256 項 7・D2273 項 2 の先例でユーザー承認事項)、glue、集計。いずれも Codex author の実装 wave と受入が要る。
- 計算投入は D2212 項 4 (1 タスク 2 node 時間以上はユーザー確認、一括承認にしない) の対象。ユーザーの記憶には「計算費用は私に確認を取って欲しい。重大な話です」がある。
  今夜のマネージャー session からの連絡は「計算時間の確認で止まる判断は codex と相談して進める」とユーザー指示を中継しているが、ユーザー本人の発話ではない。
- 研究上の文脈: VLDB EA&B、最終締切 2027-03-01。T-2867 (S3 の生成器対照) は 4 arm に決まっており (D2272 項 4)、段階 F の生死確認の後に系列数を決める段階。

## 一次資料 (worktree ではなく main checkout の現物)
- 草稿: /work/1/SFC/tanab/izanagi/docs/workload-description-critic-intervention-preregistration.md (§7・§9.4・§12・§13・§14)
- 起草 insight: /work/1/SFC/tanab/izanagi/output/insights/2026-09-28/t2852-p5-intervention-prereg-draft/README.md (§3・§4・§5)
- D2272 項 2・項 4、D2259、D2273、D2212 項 4: /work/1/SFC/tanab/izanagi/docs/decisions.md の各「## Dxxxx.」節
- 差分分析: /work/1/SFC/tanab/izanagi/output/insights/2026-09-21/vldb-direction/gap-analysis.md §0・§4 P1・P5
