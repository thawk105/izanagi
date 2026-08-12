---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: rulings-20260812-coarse-provenance
seq: 3
title: 第 2 束 11 件を一括裁定した — T-139 land 2 の残問 5 件は承認機構を新設しない縮小で確定、fold 終端と単独 fold の穴 2 件を採用 (docs のみ、branch worktree-rulings-20260812-coarse-provenance)
---

## 本文

- **ユーザー裁定 (2026-08-12、/rulings 第 2 束)。** 逐語「推奨通りで。手番や運用は何をしてほしいか
  具体的に説明して」。11 件を確定した。一次控え =
  `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-12-second-batch-11rulings.md`。
- **T-139 land 2 の残問 Q1/Q2/Q4/Q5/Q6 を確定した** (第 1 束で確定していたのは Q3 の解除のみ)。
  Q1/Q2 の承認機構は {{D:coarse-provenance-standard}} の適用で**新設しない**。項の統合更新は
  本 wave seq 1 の fragment に行った (同一 ID の二重更新を避けるため)。この 5 問は未 land branch に
  正本があり前回の総ざらいから漏れた — inbox 控え義務 (memory 済み) が回収経路として機能した。
- **収集時点の状態**: worklog (463)、稼働 11 セッション (裁定済み実装 wave 6 本を含む)、
  未 push 0 commit (前回 22 → ユーザーが push 済み)。[T-888] (main の赤) は `ac994a33` で解消済みを
  受入ボトルネック wave の全走実測 (9323 passed / 0 failed) で確認した。
- **docs-only 受入免除判定の証拠**: 本 wave の変更は docs/spool/ の fragment のみ
  (判定手順 = `git diff --name-only main` が docs/spool 配下のみ)。実装面ゼロ、該当 nodeid 不存在。
  land は従来どおり別 wave ([T-499] 仕分け wave が cherry-pick -x で相乗り予定)。

## 次の一手差分

### 更新

- [T-886] **P1・裁定済み (2026-08-12 /rulings、(a)) → 実装 wave 起票可 (Codex author)**:
  SHA pin を持つ label に限り名前 glob の fast path を許し、pin 無しの呼出元は全走査を維持する。
  fast path 後の `_verify_rollout_sha` 照合は必須のまま (同一性の錨は pin)。
  正本 = `output/insights/2026-08-12_module-fixture-cost/`
  base: 51e091597ecc9e560ef0359ae9bcb61ce28f582966410277895ec34b3f009ad5
- [T-887] **P2・裁定済み (2026-08-12 /rulings) → 再提示可で終端**: 限定 group 化を「別案として
  再提示可能」へ戻す (実装の裁定は提案が来たときに改めて行う)。退けた根拠の D91 逆読みは撤回済み。
  受入は既にほぼ下界 (177 秒 vs 176.7 秒) のため急がない。
  base: adbbf69bc0eac96314b218be4cdea270caef8bc2c9b0db2e15ef12b5b0ceab82
- [T-889] **P2・裁定済み (2026-08-12 /rulings、(a) + 敵対検証必須) → 実装 wave 起票可 (Codex author)**:
  state 無しの検証済み fold commit を `already-landed` と認識する経路を land へ足す。受理集合を
  広げる変更のため、独立の敵対検証 (偽の「検証済み commit」を認識させられないか) を受入条件とする。
  base: 7db866dbc6ec7eb438193e73b2ccc4638dc5aadf38d33f33a95c1cb246ee29ea
- [T-890] **P2・裁定済み (2026-08-12 /rulings、(b)) → 実装 wave 起票可 (Codex author)**:
  lock-aware finalize / inspect command を作り standalone apply を封鎖する。[T-799] 裁定 (b) の
  同伴条件の履行であり、新規の設計判断を伴わない。
  base: a12d5da930b4e31e77ccd81ef0350f458aeaf113a7618ca9d51b940e7d3310c7
- [T-891] **P3・裁定済み (2026-08-12 /rulings、(b)) → 現状維持で終端**: fold commit への
  transaction ID の刻印はしない ({{D:coarse-provenance-standard}} の見送り側 — commit 級 provenance)。
  canonical bytes の正しさは既存の commit identity gate が担う。
  base: 976d76469080a7840cde1fd596f24505b085b9303e7f8a64d0d00626ae959a70
- [T-892] **P3・裁定済み (2026-08-12 /rulings、(a)) → 実装 wave 起票可 (Codex author)**:
  `_declare_default_test_site` fixture を import 順に依存しない形へ直す ((b) の 1 本対症は不採用)。
  焦点走で変異 baseline が回る状態は [T-881] 裁定の前提。
  base: a456211eaf5f25febfdc381260faed6721557d6d260bffe76ae14c956501a57f
