---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-23
wave: worktree-t2851-tpcc-heldout-prereg
seq: 1
title: [T-2851] の残り (4) TPC-C の留保条件を別の事前登録として固定した — 段 1・段 2 ごとに錨 2 点 (倉庫 1 と 48、thread 48)、倉庫数・thread 数・取引構成を 1 因子ずつ動かす留保 20 条件、TPC-C での不使用義務と段 1 → 段 2 の還流禁止、認定経路の存在を含む段ごとの解禁、固定した版の v1 から継承する解析規則と置換表、留保の効力は着地時点 (docs のみ、branch worktree-t2851-tpcc-heldout-prereg)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = insight `verbatim/request.md`): v1 (`docs/unseen-condition-transfer-preregistration.md`) §14 が必須の未完項目とした TPC-C の留保を、TPC-C の生成・探索・選択が始まる前に別の事前登録として固定する (D2212 項 2)。v1 と同じ流儀 (錨・1 因子ずつ・同等幅・区間) を段 1 (NewOrder / Payment) と段 2 の取引構成へ当てる。T-2850 の選択結果・測定の発効・runner 実装・計算・gate / 検査 / 台帳の追加は scope 外。成果物 = `docs/tpcc-unseen-condition-transfer-preregistration.md`、記録 = `output/insights/2026-09-23/t2851-tpcc-transfer-prereg/README.md`、設計判断は {{D:t2851-tpcc-reservation}}。
- 起点 = local main `cadaf3805` (fresh worktree、開始 gate rc 0 は 08:36 JST)。軽量版で段 2 を省き (親の brief を plan とした)、設計択一が割れるので段 3 の Codex 相談 2 本と段 6 の read-only review を残した。実装面の差分ゼロなので変異 matrix は免除 (DW-S04)。計算ノードの使用 0。v1 は §13.2 (着地後は本文を書き換えない) により触らず、別文書にした。
- 段 1 の事実集めは読取り専用の Claude 調査子 1 本 (sonnet) に任せ、親が要所を CCBench の現物で検算した。TPC-C の明細数 (5〜15)・remote 品目 (1%)・remote 顧客 (15%) はコンパイル時の定数でフラグでないので、v1 の 5 因子のうち「1 txn の操作数」と「アクセス集合の重なり」は CCBench の改変なしには動かせず、本書は倉庫数・thread 数・取引構成の 3 因子だけを動かす。
- 段 4 直前に裁定 inbox を再走査した。/rulings 第 32 回 (08:29) の項 1 (CCBench の pin を別 commit へ進める更新 wave の承認) を受け、本文の TPC-C の引数の記述は起草時点の pin e9e477ca の静的確認と明記し、測定に使う CCBench の同一性は発効束で固定する形にした。
- 段 3 (Codex read-only、reasoning medium、08:49 起動・08:53 / 08:54 完了): 相談 A (条件設計) は must-fix 4 / should 4、相談 B (漏洩・HARKing・v1 との整合・過剰) は must-fix 4 / should 5。17 件すべて real と判定し採用した (refuted 0)。主な変更は、1 走の値を abort 後の取引種別の再抽選を含む全取引 commit throughput と定義 (CCBench は abort した取引を再試行せず引き直す)、段 2 の各 10% の cell は未配送注文の表が 3 s の間に減る複合変更と明記、「TPC-C の性能測定 0 件・生成未開始」を検索範囲の未発見に限定 ([T-2854] の構造検査の出力に throughput 36,156 がある)、継承する v1 を commit `da869768d` の版で固定し TPC-C 固有の置換表を置く、近傍条件・短縮版・較正による適応と段 1 → 段 2 の還流を禁止、など。
- 段 6 (Codex read-only review 1 本、09:06〜09:09): NO-GO、must-fix 1 (発効の決定で cell を外せるとした費用の節の文が、着地後の凍結と衝突する) / should 2 / nit 1。一次資料の事実と算術は全て照合が取れた。すべて real と判定し、親が docs を直した (予算不足は段の発効の延期、縮小配置は別の登録)。焦点再レビュー 1 巡目 (09:12〜09:13): GO、must-fix 0、R1〜R4 すべて closed。
- 親の自分起因の誤り: 本文 §7 の最初の版で、`tpcc_silo` / `tpcc_mocc` が現れる 116 file を標本しか見ていないのに全部分類したように書いた。review 起動前に内訳を数え直して `8ea43a680` で限定し、review の R2 を受けてさらに「読んだ file と標本の範囲では」と直した。handoff の最終更新時刻を一度推定で書いた (実測で直した)。
- 三軸語の走査器 (`s8b_holdout_freeze search`) は rc 1 だが、hit は main に既存の `output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` の 3 file だけで本 wave の file は 0 件 (v1 の wave と同じ既存 hit)。Codex の出力 4 本は行末空白 7 行を除き末尾 LF を足す可逆な正規化をして写した (insight の `verbatim/NORMALIZATION.json`)。
- 並走中の [T-2850] 試走の事前登録 wave の作業木を読取りだけで確かめ、同書が TPC-C を扱わず v1 だけを参照していることを見た (衝突なし)。
- 工数: Codex 子 = consult 2 本、review 1 本、焦点再レビュー 1 本。Claude 子 = 調査 1 本 (sonnet)。計算ノード 0。

## 次の一手差分

### 更新

- [T-2851] **P1 (VLDB 差分分析 P4: 未知条件への転移と再現)**: 事前登録 v1 `docs/unseen-condition-transfer-preregistration.md` (YCSB) と、TPC-C 版
  `docs/tpcc-unseen-condition-transfer-preregistration.md` (段 1・段 2 の錨と留保 20 条件、{{D:t2851-tpcc-reservation}}) を作り、どちらも留保の効力は着地時点で生じる
  (D2223)。TPC-C の探索群の学習条件は同書 §2.1 の段ごとの錨 2 点の部分集合にし (外れるなら生成の開始前に別の登録が要る)、TPC-C の留保条件の値・結果・
  それから作った指示や設定を生成器・選択へ入れず、段 1 の留保の情報を段 2 へ渡さない。残りは 3 つ。(1) 測定の発効: YCSB は対象探索群 ([T-2850] の選択結果) の名指し、
  全手法・全独立探索の候補凍結記録、MOCC の扱いの 3 択、発効束 (v1 §13.1) の実値を揃え、凍結した候補数で費用を見積もり直してユーザーの計算確認を取り、決定に
  記録する (v1 §12 の試算は 1 cohort の性能だけで約 9.5〜616 node 時間、検証は約 19〜64 node 時間、cohort は 2 つ。D2212 項 4)。TPC-C は段ごとに別の発効で、
  段の認定経路 ([T-2854]・[T-2855]) の存在、強い参照の 3 択 (固定できなければ記述専用)、ロード時間の実測単価での見積りが加わる (TPC-C 版 §3.3・§4・§8・§9.1)。
  (2) runner の実装 (v1 §11 の欠ける部品と TPC-C 版 §5 の置換、Codex author)。(3) 性能 2 cohort と検証の実施。前提 = [T-2850] の選択結果と TPC-C の探索の結果。
  一次資料 `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P4、記録 `output/insights/2026-09-22/t2851-transfer-prereg/README.md` と
  `output/insights/2026-09-23/t2851-tpcc-transfer-prereg/README.md`。
  base: ab6229443679004787f25b93cbe83a5188c59155ade8f6f64dfa42de8b6d31f1
