---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-t659-evidence-erratum
seq: 1
title: [T-659] 裁定パッケージの中核証拠を親 probe から既存テストへ差し替えた — probe は不適切かつ不要だった (docs のみ、実装差分なし、受入 7505 passed / 20 skipped、変異は免除、branch worktree-dev-wave-t659-evidence-erratum)
---

## 本文

- **ユーザーの問い「このセッションではやり直しが特にない？」を受けた再点検で判明した erratum。**
  ユーザー裁定 (発話「b」) により、次弾送りにせず訂正版を即 land した。
- **[T-659] パッケージの中核 (§1.1「分裂の両方向が fail-closed」) の証拠を、親が書いた probe から
  tracked なテストへ差し替えた。** `orchestrator/tests/test_env_contract_activation.py` の
  `test_issued_valid_suffix_is_not_active_until_source_head_update_and_restart` (:1498)、
  `test_production_loader_rejects_tail_deletion_with_source_head_unchanged` (:1477)、
  `test_production_loader_passes_source_head_constants_to_leaf` (:1544) が、
  `ec.lookup()` / `ec.current_activation_state()` を通る **production の読み込み経路**
  (process cache・root 解決・較正検証を含む) で同じことを断言しており、
  **実際の発行 tool 経由**である点で親 probe より強い。エントリ 323 の受入全走
  (7495 passed) に含まれ緑で通っていた。
- **したがって親 probe (`verbatim/probe_split_window.py`) は、規律違反であると同時に不要だった。**
  段 3 レンズ A の A-7 は「probe は leaf validator を測っており production 経路を測っていない」と
  指摘し、親は「実測範囲は leaf まで」と主張を縮めたが、**その訂正も不十分だった** —
  正しくは「既存被覆を検索していれば probe を書かずに、より強い証拠を得られた」である。
  package / README の該当箇所に erratum を明記し、**probe を証拠として引かないよう禁じた**
  (逐語は歴史として `verbatim/` に残す)。
- **推奨は変わらない。** R1 (機構を作らず手順で担う) の根拠は弱まるのではなく強まる。
  設問 R0〜R4 と不変条件に変更はない。
- **規律面の帰結は既存項目が持つ。** probe を repo へ入れたことによる provenance 違反は
  [T-682] (処置の裁定待ち、main の監査は依然 rc=1)、親が probe を書いてよいかの境界は
  [T-317] (未裁定) が所有する。本エントリはそこへ「**書く前に既存被覆を検索する**」という
  手前の問いを材料として足すだけで、新規起票はしない。
- 本 wave は docs-only のため D95 決定 (1) により子ゼロ。実装面 path を触らないので
  Codex `role=author` は不要 (`git diff --stat` で `.md` のみを確認)。変異 matrix は
  実装差分ゼロのため `DW-S04` の免除条項どおり免除。
- **受入は tip `2b09b2ea` で 1 走** (request 896548.nqsv、1493 秒、**7505 passed / 20 skipped、
  rc=0**)。lease は 30 秒間隔の待ち手が約 3 分で取得した (前 wave の 120 秒間隔では 80 分
  取り逃していた実測と整合する)。この受入値を書く commit 自体は、その走行の対象に含まれない。
- **検査は今回すべて rc を直接見た** (`check_docs` rc=0、`spool_fold --dry-run` rc=0、
  `check_ai_provenance` rc=1 = 既知の `2c192953` のみ、本 wave の commit は clean)。
  前 wave で `| tail -2` により赤を緑と誤判定した F37 再発への直接の是正である。

## 次の一手差分

### 更新

- [T-659] **P2・ユーザー裁定待ち**: 発行から配備までの分裂窓。設計パッケージを
  `output/insights/2026-08-09_t659-activation-deploy-window/package.md` へ返した (R0〜R4)。
  推奨は R0 = 列挙できる閉集合に限る、R1 = 機構を作らず手順で担う (発行 tool に head を
  書かせる案は選択肢から落とす)、R2 = 活性化専用の作業窓を手順で置く、R3 = R1/R2 の採用分が
  land するまで次の活性化を始めない、R4 = runbook に専用節を作る。実装は [T-657] land 後。
  **中核証拠は親 probe でなく tracked なテスト 3 本 (2026-08-09 erratum)。**
  base: e6eec75e79e35ba170586716705e14ba1063390aa45d48cd2bca7c5d2479f15d
