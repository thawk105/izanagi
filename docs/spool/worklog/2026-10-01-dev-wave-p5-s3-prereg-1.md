---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-10-01
wave: dev-wave-p5-s3-prereg
seq: 1
title: [T-2852] P5 の事前登録草稿を S1 版から S3 版へ改版した — 4 cell × n = 4 の向き、T-2867 の LLM が受け取る情報の露出の棚卸し、失敗理由の履歴への接続を発効の前提に (docs + insight、計算なし・未発効、branch dev-wave-p5-s3-prereg)
---

## 本文

- 依頼 (D2322 項 5) どおり docs だけを改めた。n の確定・発効・実装・投入はしていない。草稿 `docs/workload-description-critic-intervention-preregistration.md`、
  記録 `output/insights/2026-10-01/t2852-p5-s3-prereg-revision/README.md`。
- 中断: 2026-10-01 00:4x に land 調整役 (manager: parallel land) から 5 時間の利用上限による停止依頼を受けて止め、09:43 のユーザーの「続けて」で再開した。
  再開時に local main が進んでおり T-2867 本走が完了していたので `--ff-only` で取り込んだ。起草者は T-2867 本走の commit 題 (4 比較とも floor 内の同等) を読んだが、
  score・endpoint・report は開いていない (草稿 §11 に開示)。
- 棚卸しの結論: 段階 D の二値・射程文・baseline の abort 率は workload の名前・読み比率を示さないが、write-heavy の情報を運ぶ (射影は全 cell 同じ bytes、
  baseline は系列ごとの実測値、critic の材料は critic ありの cell だけ)。確認した固定の入力には正しい workload 名を表示する欄が無く、coder の文脈 (backoff 軸用の旧文書) は
  読み比率 50 の配線規模を表示していた。したがって T-2867 の LLM×IR の系列は「正しい記述」の cell に当たらない。
- 段 6 (軽量版で段 2・3 は省略): read-only の Codex レビュー 2 本 (gpt-6-astra、事実照合レンズと過剰・削除レンズ、同じ worktree で直列) がどちらも NO-GO、must-fix 計 3 件。
  最重要は、T-2867 の対照の経路では自系列の履歴に評価の結果の verifier の digest と一部の拒否 (schema の拒否と auditor の出力の形式・digest の不一致による拒否) が入っていない (段 1 で置いた「失敗理由は履歴で critic と独立に届く」が
  schema の上だけの話だった) という所見で、親がコードと本走の coder 入力 249 件の履歴の欄の集計で裏取りし、履歴の欄の接続を critic なしの cell の発効の前提にした ({{F:contrast-history-fields-unfilled}})。
  refuted 0。焦点再レビューの結果は insight §6。

## 次の一手差分

### 更新

- [T-2852] **P1・S3 版の草稿へ改版済み (未発効) → [T-2867] 本走の分散と週上限の実測を見て n を確定し、発効・実装・投入の判断をユーザーに示す。2026-11-02 の再提示 (ii) は別に残る (VLDB 差分分析 P5: 介入による理由の説明)**: 進め方の択一は (c) に決めた (D2283、
  ユーザーの判断委任による判断)。S1-wh の本走は今は投入しない。事前登録の草稿 `docs/workload-description-critic-intervention-preregistration.md` は S3 版 (2026-10-01 改版) で未発効。
  本線は S3 の write-heavy・LLM×IR だけの 4 cell (正-あり・伏せ-あり・入替-あり・正-なし) × n = 4 の向き (D2322 項 5、換算 21.4〜24.7 node 時間、LLM の直列 15.2〜64.0 時間)。
  n の確定・発効・実装・投入は、[T-2867] 本走の LLM×IR の系列の分散と週上限 (429 の件数・時刻、週あたりの機会) を読んでから計算確認付きで改めて示し、D2283 (iii) の逆算で収まらなければ P5 を限界として明記する。
  発効に要る実装は草稿 §13 (記述の表示の切替・失敗理由の履歴への接続・critic なしの経路・cohort の glue・集計・評定用の資料)。表示の切替は、[T-2870] の文脈の差し替えが先に着地していればその文脈の上で行う (草稿 §13 の 1)。
  記録は `output/insights/2026-10-01/t2852-p5-s3-prereg-revision/README.md`。
  base: 78a21b0744b02f26c68d61cc53ede99f6df7d94ffadd0bb943c66db40ba64800

### 新規

- {{T:t2867-llm-input-disclosure}} **P2・新規 (T-2867 の LLM の入力の実態の開示と修復)**: P5 の改版の棚卸しと段 6 で、T-2867 の LLM の 2 arm の入力について 2 つの事実が分かった。
  (a) coder の `leakproof_context` は backoff 軸用の旧文書のままで、実際 (読み比率 5) と違う読み比率 50 の配線規模を表示し、確認した固定の入力には正しい workload 名を表示する欄が無い
  (旧文書であること自体は段階 F の insight §3.4 と [T-2870] で既知)。(b) T-2867 登録 §4.1 は「自系列の履歴は … verifier の digest を載せ」と書くが、対照の経路は評価の結果の
  verifier の digest も、schema の拒否と auditor の出力の形式・digest の不一致による拒否も履歴に入れない ({{F:contrast-history-fields-unfilled}})。確認した本走の coder 入力 249 件の履歴に現れた評価の結果は全部 certified だった (本走全体の失敗の有無はこの集計では確かめていない)。
  T-2867 の報告で LLM の構成を書くときに (a)(b) を開示し、(a) が LLM 対 非 LLM の比較に効いたかを評価する。(b) の修復は P5 の発効の前提 (草稿 §13 の 2) でもある。
  記録は `output/insights/2026-10-01/t2852-p5-s3-prereg-revision/README.md` §2。
