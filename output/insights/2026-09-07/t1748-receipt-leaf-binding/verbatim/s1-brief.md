# 段 1 brief — [T-1748] 受領証の cross-binding leaf を耐久束縛する

## 前提の実測 (依頼本文からの訂正 2 件)

- **出典は「段 6 レビュー B 所見 3」ではない。** 実体は同 wave (worklog 959 /
  `output/insights/2026-08-25_t822-evidence-gaps`) の **段 3 レンズ B** 冒頭所見と、段 3 レンズ A
  の同旨記述である。段 6 レビュー B の所見 3 は「完全 build 束の母数 6」で別件。依頼の主張内容
  そのものは原典に逐語で存在するので、対象は変わらない。
- **欠陥は現行 main で生きている。** `verify_acceptance_receipt` は manifest・registry・lifecycle・
  各 trial の report / attempt journal を再読して再ハッシュするが、**cross-binding leaf だけは
  受領証内の leaf 値から aggregate を再計算して突き合わせるだけ**で、leaf の元になった projection を
  再導出しない。既存 v3/v5 test の fixture は 6 本の leaf を `sha256("cross-binding-leaf-{i}")` という
  合成文字列に置いており、それで検証が成功している (`test_s8c_acceptance_receipt_v2.py:505`)。

## scope

`verify_acceptance_receipt` が cross-binding leaf を**受領証の外の現物から再導出して照合する**ように
する。発行時 (`trial_registry.py:6168` の `verify_s8c_cross_binding`) の保証が、追跡済み受領証を
後から読む側にも残る形にする。負の対照として、leaf を 1 本差し替えた受領証が拒否されることを示す。

**scope 外:** 受領証 schema の版上げ、certifying 経路の解禁、cross-binding 以外の参照の検査追加、
仮想リスク向けの gate・検査・台帳・一般化。

## 確定済みユーザー裁定

- 本題の修正だけ。追加の gate・検査・台帳・一般化は入れない。
- 規律 2 を緩めない — 受理集合を広げる方向の変更は採らない。
- Codex `role=author` (D95) が実装面を書く。親は実装面を直接編集しない。
- 着手直前の local main から fresh worktree (済み。`37cb5696b`、起動 gate 緑)。

## 不変条件

- **正当な受領証の受理集合を狭めない。** 発行器が実際に書く leaf は必ず通る。
- 受領証 schema (`p3-8c-trial-acceptance-receipt/v5`) の field 集合と canonical bytes を変えない。
- 発行済み受領証は 1 件も存在しない (`output/s8c-trial-registry/receipts/` 不在) ため、
  凍結成果物の再発行は発生しない。durable manifest の invalidate も起きない。
- `certifying` は構造上つねに False のまま。本 wave で certified 選択の値は変わらない。

## (P1) 親の provisional 裁定 — 攻撃対象

- **(P1-a) 再導出の素材は「受領証が既に名指しし、verifier が既に再読している追跡済み bytes」に
  限る。** すなわち trial の `report_path` と `attempt_journal_path`。`run_root` / `output_root` 配下の
  campaign 実体は受領証に記録が無く、受領証だけを持つ側からは所在を決められないので素材にしない。
- **(P1-b) build mode の leaf は report + events だけでは再導出できない** (artifact_refs・
  source_refs・build/bench records が run_root の現物を読む)。したがって完全な再導出は不可能で、
  **「受領証内の leaf 値を、report と journal から独立に決まる部分と照合する」**形が上限になる。
  この上限が「発行時の保証の耐久化」として十分かは段 3 の攻撃対象。
- **(P1-c) 代替案**: leaf の preimage (cross-binding projection) を受領証と同じく追跡済み成果物として
  発行時に永続化し、verifier がそれを再読して leaf を再計算する。schema を変えずに済むかは要検討。
- (P1-a)〜(P1-c) のどれを採るかは段 4 で裁定する。**恒真な検査 (同じ走行側が書いた値どうしの照合)
  になっていないこと**を採否の第一条件にする (D920 と同型)。

## 変更面 — 実アンカー表

| anchor | 役割 |
|---|---|
| `orchestrator/campaign/s8c_acceptance_receipt.py:2005-2027` | leaf aggregate の再計算だけを行う現行検査。修正の中心 |
| `orchestrator/campaign/s8c_acceptance_receipt.py:1919` | `verify_acceptance_receipt` 本体 |
| `orchestrator/campaign/s8c_acceptance_receipt.py:1150` | `_assert_digest` — 追跡済み参照の再読 (作業ツリーから読む) |
| `orchestrator/campaign/autonomous_trial_completeness.py:4217` | `verify_s8c_cross_binding` — 発行時の projection 生成 |
| `orchestrator/campaign/autonomous_trial_completeness.py:4165/4192` | no-build / build-failure mode の leaf — report + events のみに依存 |
| `orchestrator/campaign/trial_registry.py:6168, 6306, 6337` | leaf と aggregate の発行側 |
| `orchestrator/tests/test_s8c_acceptance_receipt_v2.py:505` | 合成 leaf を書いている fixture。正例側の是正が要る |
| `orchestrator/tests/test_ccbench_spawn_sites.py:230` | `s8c_acceptance_receipt.py` の subprocess 起動点を 1 に pin。新規 `_git` 呼出しを足すと赤 |
| `orchestrator/tests/acceptance_duration_ledger.json` | 新規 test の登録先 |

## 成果物影響 (DW-G05)

放置すると、任意の leaf digest を持つ追跡済み受領証から `VerifiedAcceptanceReceipt` が得られる。
現在は受領証が構造上 `certifying=False` なので certified 選択の値は変わらないが、
`require_current_verified_receipt` を通る下流 capability は「cross-binding が発行時に検証済み」
という前提で受領証を受け取る。その前提は現状 1 bit も裏取りされていない。

## 分割方針

編集面が 1 module に集中し相互依存が強いので、段 5 の実装子は 1 本。段 2 プラン 1 本、
段 3 敵対相談 2 本 (レンズ = 恒真性 / 過剰拒否)、段 6 レビュー 2 本 + fix 1 本。
正しさ防壁に触るため軽量版は採らない。
