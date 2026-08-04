---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: wave-t244-p5-injection-gate
seq: 1
title: [T-244] D121 P5 のうち 2 要件を実装した — 正式判定を token の自己申告から既存 provider 値へ移し、未予約 token は未実装のまま残す (コード + docs、branch worktree-wave-t244-p5-injection-gate)
---

## 本文

- **段 3 の敵対相談 2 本が独立に、段 2 起草の中核設計を恒真だと判定した。** 起草は
  「正式 token を提示した run だけ 3 つの注入 seam を拒否する」設計だったが、token を発行できる面
  (CLI) には注入口が無く、注入口のある面 (programmatic な公開関数) には issuer が無い。
  **両者が交差しないため、runbook のどのコマンドでも新 gate は一度も発火しない。**
  親はこれを real と裁定し、正式判定を**既に consumer が閉集合として検査している provider 値**へ
  移した。設計の詳細と却下理由は {{D:p5-provider-and-session-isolation}}
- **receipt 設計も落とした。** レンズ B が下流 consumer を全数調査し、artifact admission・
  材料レポート・certified 選択のいずれも新 receipt を読まないことを実測した。
  「書いた本人だけが読み返す」自己申告は恒真な保証にあたる
- **親 brief 自身の誤りが 2 件反証された。** (1) 「role 間の session 共有は構造的に検出不能」は過大で、
  durable な `provenance.child_id` から成果物側で検査できる。この反証が実行時 + 成果物再検証の
  2 層設計を生んだ。(2) 成果物影響 3 行のうち certified 選択・材料レポートへ波及すると読める 2 行は
  現時点では成立しない (本試行は `scientific_claim=False` の配線 pilot)。書ける影響へ書き換えた
- **段 6 レビューの BLOCKER 1 件は事実誤認だった。** 「既存 node が `child_id` 欠落で赤化する」との
  主張だったが、当該 fixture は委譲先の provider が `child_id` を持つ。親が該当 node を単独実走して
  1 passed を確認し、refuted と裁定した。**残る所見 4 件は採用したが、いずれも判定ロジックの変更を
  伴わない境界テストの純増と docstring の表現修正だった**
- **`drive` / `preview` の注入は塞げなかった。** 実 Claude provider + no-build の構成でこの 2 つを
  正当に注入している既存テストが 2 件あり、塞ぐと期待値の変更が要る。受理集合の縮小は
  `providers` に限った (裁定パッケージ U-1)
- **未予約 token (P5 第 3 要件) は実装しない。** 要求されている token は origin/query slot の予約
  receipt であり、発行主体の ledger は**同日の別 wave が敵対 2 レンズの NO-GO で差し戻したまま
  未実装**である (エントリ (165))。process 内で自分が発行し自分で検証する token は儀式にすぎない
- **段 8 の改善候補は 2 件記録したが、いずれも文書を変更しない裁定とした。**
  (1) **変異 harness の走行中は、親が作業ツリーへ一切触れられない。** 本 wave で 2 回中断させた —
  1 回目は台帳 fragment の新規作成 (未追跡) で `untracked file を検出`、2 回目は**追跡下の
  fragment の編集**で `固定 HEAD 外の変更を検出`。2 回目は 1 回目の警告文が予告しない形であり、
  親が「docs 作業は変異と並行してよい」と誤認しやすい。中断時に変異ソースは正しく復元された。
  ただし **`docs/dev-wave/**` の予算残は 7 bytes (25,193 / 25,200)** で追記の余地がなく、
  同一 wave 内の同一原因は独立 2 例に当たらないため、**記録のみ**とする
  (2) 台帳 fragment の `base:` は、対象が carry stub のとき**参照先エントリの実体本文**の digest を
  要る (stub 自身の digest ではない)。fold の dry-run が即座に検出するため実害は小さい

## 次の一手差分

### 更新

- [T-244] **P1・P5 は 2/3 要件を実装済み → 残余 3 件がユーザー裁定待ち**:
  provider 注入の拒否 (実 Claude 試行に限る) と role 間 session 共有の拒否 (実行時 + 成果物再検証の
  2 層) を実装し、{{D:p5-provider-and-session-isolation}} に記録した。**P5 全体は未充足**。
  **U-1** `drive` / `preview` 注入も塞ぐか (塞ぐなら既存 2 テストの注入手段を別 seam へ移す設計が要る)、
  **U-2** 未予約 token を P3 の予約 receipt に依存させるか、それとも P5 の第 3 要件自体を
  origin ledger の充足条件へ移すか、**U-3** provider executable の真正性 (許可 digest registry) を
  要求するか、の 3 件。U-2 は P3 の裁定 (エントリ (165) の U-A〜U-D) が先行する。
  逐語 (brief・プラン・敵対相談 2 本・裁定・レビュー 2 本・変異台帳) は
  `output/insights/2026-08-04_t244-p5-injection-gate/` に凍結済み
  base: a7f609f9cacafc73e60462b33df8dad4ace97f115c85bdabf96abee224b1df1b
