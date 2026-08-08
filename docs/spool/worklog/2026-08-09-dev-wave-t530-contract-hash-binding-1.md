---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-t530-contract-hash-binding
seq: 1
title: [T-530] contract hash を campaign identity と WAL COMMIT へ束縛した — 全経路の proof chain 完結は名乗らない (コード + docs、受入 7459 passed / 20 skipped、変異 2 走で 8/8 KILLED・SURVIVED 0、branch worktree-dev-wave-t530-contract-hash-binding)
---

## 本文

- **裁定どおり 2 箇所へ束縛し、照合まで入れた。** 設計と却下案は {{D:contract-hash-identity-and-commit-binding}}。
  ただし裁定パッケージへ返した残件があるため、**「proof chain が全経路で完結した」とは名乗らない**。
  無束縛 COMMIT は historical 分類と raw reader 経由では依然 certified 入力に到達しうる。
- **段 3 の最大争点だった D125 との衝突は、親が実測で解いた。** D125 決定 (2) は
  「OTHER の campaign_id は 1 bit も変えない」というユーザー裁定だが、**T-343 が既に破って
  land 済み**である (`test_p3_s4_loop_trigger_gating.py` が pre-T343 の `...3f72ecd5` と
  T343 後の `...ccba936e` を並べて pin している)。さらに既存 campaign の `campaign.lock` は
  30/30 が pre-T343 形式で、`ident.campaign_id` の再計算は**現時点で既に**既存 dir を
  1 本も指していない。`replay.discover_campaign_dir` は元々 dir 名 prefix で discover し
  id 非依存である。よって「identity 変更で既存成果物が到達不能になる」は本 wave が開ける穴ではなく
  status quo であり、blocker から外した。D125 の失効表記は裁定へ返す。
- **段 3 レンズ A の「別 campaign の COMMIT 行だけを複写」は refuted。** attempt topology が
  先に拒否するため発火証拠にならず、変異 fixture から外した。
- **親 brief の件数が誤っていた。** 「既存 32 campaign」は母集団混在で、正しくは
  **30 official + 2 smoke evidence** (後者は insights 配下)。レンズ B が実測で指摘した。
- **段 6 のレビューが、実測では出ない穴を 1 件見つけた。** 実装は既に束縛済みの hash を
  **黙って削除してから再束縛**しており、「値が違えば拒否」という自分の防壁を迂回していた。
  受入も subset も緑のまま通る類である。
- **焦点再レビューが、受入 subset では見えない実回帰を 1 件見つけた。** 自律試行の identity が
  実行環境を literal 固定する一方、下流は site を解決して Pegasus 契約で走るため、
  **Pegasus compute の正当な実行が WAL を作る前に拒否される**状態だった。
  本 wave が持ち込んだ受理集合の縮小なので must-fix として閉じた。
- **fix は 5 巡。`DW-O16` の 3 巡上限を 2 度超えた。** 4 巡目は上記の新規実回帰、5 巡目は
  4 巡目が自分で入れたテスト配線バグ (spy 辞書へ代入しておらず必ず `KeyError`) を閉じるため。
  いずれも争点の再 fix ではない。超過の事実をここに残す。
- **fix 2 巡ぶんを同一原因で空費した。** 詳細は
  {{F:dual-module-identity-across-test-and-production}}。
- **wave 途中で codex のサブスクリプションログインが失効し、1 度 fail-closed で停止した。**
  実装面は Codex author 必須のため親は代行せず、ユーザーがログインを回復してから再開した。
  詳細は {{F:codex-auth-expiry-mid-wave}}。
- **変異は 2 走。SURVIVED 0。** run 1 は 7 KILLED / 1 MISMATCH で、MISMATCH は gate の失敗ではなく
  親の期待 node 不足だった (no-bench の hash を潰すと resume 回復のテストも赤くなる)。
  run 1 を erratum として残し、期待集合を訂正した run 2 で **8/8 KILLED** になった。
  焦点再レビューの指摘に従い、事前登録のうち「解決処理の削除」変異は構文エラーで別理由の
  全体赤になるため「未知 hash を受理へ倒す」変異へ定義し直してから走らせた。
- **段 3 は 2 レンズとも `gpt-5.6-sol` で走らせた。** sol/luna 混成の規約は段 3 実行後に
  main へ land したもので、遡及適用していない。
- wave 中に local main を 3 回取り込んだ (計 47 commit、いずれも競合なし)。
- 一次資料 = `output/insights/2026-08-09_t530-contract-hash-binding/`
  (段 1 brief、段 2 プラン、段 3 の 2 レンズ、段 4 裁定、段 5 実装報告、段 6 の 2 レンズと
  fix 5 巡、焦点再レビュー、変異 2 走の spec と台帳)。

## 次の一手差分

### 更新

- [T-530] **P2・束縛は完了、読み出し境界が残件**: contract hash を campaign identity
  (`search_config.environment_contract_sha256`) と WAL COMMIT payload へ束縛し、
  lock 由来の期待値で照合する検査を tail repair より前に入れた。設計は
  {{D:contract-hash-identity-and-commit-binding}}。**残件は certified な読み出し境界の閉包**で、
  6 問の裁定パッケージとして {{T:certified-read-boundary-ruling-package}} が引き取る。
  base: a23ffc643b81477731304b602e0ae4adc32ae240116a1f07c5f7b28e928533b2

### 新規

- {{T:certified-read-boundary-ruling-package}} **P1・ユーザー裁定待ち**:
  [T-530] の実装 wave が scope 外に裁定して返した 6 問。
  (1) historical 分類 (`historical-not-reclassified`) の 21 campaign を certified 入力から
  外すか。外すと `docs/phase3.md` が「最終成果物」と呼ぶ既存 campaign の受理集合が変わる。
  (2) raw reader (screening driver / S1 report / known-axes freeze / S8b oracle report) へ
  照合を配線するか。既存成果物を遡って拒否しうる。
  (3) S8b の private lock を契約束縛形にし、offline report 側でも照合するか。
  (4) qualification event sink の 2 口と `attestation_mode="none"` の receipt 発行を
  どの wave が持つか。
  (5) D125 決定 (2) の失効 (T-343 が既に破っている事実) を decisions へどう記録するか。
  (6) 契約を更新すると campaign id が分裂する結合をどう扱うか。第 2 世代の活性化と直結する。
  加えて、writer と reader の identity 導出を一元化するか (ambient 参照が 15 か所残る。
  成果物の値は変わらず、既存の status quo と同じ)。
  **段 8 由来の 1 件も同じ束へ入れる**: `DW-O16` の fix 3 巡上限は「争点の再 fix」を想定した
  規定に見えるが、焦点再レビューが**新規に見つけた実回帰**の扱いが書かれていない。本 wave は
  この空白のため 2 度超過した。上限の射程を明文化するか、超過の記録義務だけにするかは裁定境界の
  変更なので実装しない。なお失敗 2 件の恒久対応は dev-wave の docs 予算 (hard ceiling) を
  超えるため reference 節ではなく memory へ置いた。予算そのものの引き上げは提案しない。
