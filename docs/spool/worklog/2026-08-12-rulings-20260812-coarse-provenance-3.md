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
  Q1/Q2 の承認機構は D320 の適用で**新設しない**。この 5 問は未 land branch に
  正本があり前回の総ざらいから漏れた — inbox 控え義務 (memory 済み) が回収経路として機能した。
- **land wave (2026-08-12 23 時台) での移送。** 本項の [T-139] 統合更新は当初 seq 1 の fragment に
  置いていたが、seq 1 は別 branch (`worktree-dev-wave-t499-triage`) が改変版を先に fold 済みで
  (`FOLDED.md` の content_sha256 `9d765127…`、本文は `docs/archive/worklog-phase3-0812-462-465.md`)、
  再 fold は同題エントリの二重計上になる。そこで seq 1 を落とし、未 fold の本 fragment へ
  [T-139] 更新だけを移した。移送時に main 側の a12 実測 (完走・前提 #3 充足) を保存して統合した。
  seq 1 の他の更新 16 項 (T-513/679/687/689/691/694/725/751/837/864/868/871/872/873/874/881) は
  先行 fold が既に終端させており、fold の `transition-target` 検査で非 active と実測されたため落とした。
  本 fragment の [T-886] 更新も同様に落とした — 裁定 (a) は既にエントリ 486/487 で実装・終端済みで
  (`docs/archive/worklog-phase3-0812-486-487.md` に「ユーザー裁定 (2026-08-12 第 2 束) T-886 = (a) の実装」
  が着地)、内容の欠落は生じない。本 fragment の [T-887] 更新も落とした — 同じ項を第 6 束
  (`rulings7-20260812`) が後発の内容で更新しており、fold は同一 T の二重操作を
  `transition-duplicate` で拒否するため。第 2 束の判断内容は本文に残る。
- **収集時点の状態**: worklog (463)、稼働 11 セッション (裁定済み実装 wave 6 本を含む)、
  未 push 0 commit (前回 22 → ユーザーが push 済み)。[T-888] (main の赤) は `ac994a33` で解消済みを
  受入ボトルネック wave の全走実測 (9323 passed / 0 failed) で確認した。
- **docs-only 受入免除判定の証拠**: 本 wave の変更は docs/spool/ の fragment のみ
  (判定手順 = `git diff --name-only main` が docs/spool 配下のみ)。実装面ゼロ、該当 nodeid 不存在。
  land は従来どおり別 wave ([T-499] 仕分け wave が cherry-pick -x で相乗り予定)。

## 次の一手差分

### 更新

- [T-139] **P1・裁定済み (2026-08-12 /rulings、2 束) → land 2 は完了 land 可、pilot は投入経路 wave で**:
  `a12` は完走し前提 #3 は充足 (エントリ 501 の実測)。第 1 束 = pilot/本走の投入禁止を Q3 (b) から
  切り離して解除。追補 P の blob 凍結は実施しない (値の承認 `p01`/`α_pub` は不変)。
  第 2 束 = land 2 session 2/3 の残問を確定 — Q1 (受理述語の入力欠落 4 件を閉じる decision) と
  Q2 (approval manifest の新表現) は D320 により**機構を新設しない**。Q4 = scope を組み替え、投入の
  実務経路 (`submit_pilot`・PBS driver・collector) + D292 を上書きする解除 decision + 束縛検査だけを
  1 session・同一 land で組む (解除 decision だけ先に land しない)。Q5 = 段 8 候補 3 件は機械化移管を
  先に試し、散文の残余のみ既開の独立審査束へ。Q6 = (a) S6 (a) を維持し可視性は repo 外控えで担保。
  エントリ 501 が「Q1 / Q2 が未裁定」としていたのは本裁定が未 land だったためで、この更新が是正する
  — 残る 7 件 (#1・#4〜#9) の待ちは解け、land 2 は現土台 + Q4 scope で完了 land できる。
  正本 = branch `worktree-dev-wave-t139-manifest-w2` の
  `output/insights/2026-08-11_t139-manifest-land2-s2/package.md`、一次控え = rulings-inbox の
  `2026-08-12-t139-land2-s2-five-rulings.md` / `2026-08-12-coarse-provenance-45rulings.md` /
  `2026-08-12-second-batch-11rulings.md`。
  base: 5194e8c4b1e160cf495050abf19114b2f91742c0681fc07cc5cf787f516c5c29
- [T-889] **P2・裁定済み (2026-08-12 /rulings、(a) + 敵対検証必須) → 実装 wave 起票可 (Codex author)**:
  state 無しの検証済み fold commit を `already-landed` と認識する経路を land へ足す。受理集合を
  広げる変更のため、独立の敵対検証 (偽の「検証済み commit」を認識させられないか) を受入条件とする。
  base: 7db866dbc6ec7eb438193e73b2ccc4638dc5aadf38d33f33a95c1cb246ee29ea
- [T-890] **P2・裁定済み (2026-08-12 /rulings、(b)) → 実装 wave 起票可 (Codex author)**:
  lock-aware finalize / inspect command を作り standalone apply を封鎖する。[T-799] 裁定 (b) の
  同伴条件の履行であり、新規の設計判断を伴わない。
  base: a12d5da930b4e31e77ccd81ef0350f458aeaf113a7618ca9d51b940e7d3310c7
- [T-891] **P3・裁定済み (2026-08-12 /rulings、(b)) → 現状維持で終端**: fold commit への
  transaction ID の刻印はしない (D320 の見送り側 — commit 級 provenance)。
  canonical bytes の正しさは既存の commit identity gate が担う。
  base: 976d76469080a7840cde1fd596f24505b085b9303e7f8a64d0d00626ae959a70
- [T-892] **P3・裁定済み (2026-08-12 /rulings、(a)) → 実装 wave 起票可 (Codex author)**:
  `_declare_default_test_site` fixture を import 順に依存しない形へ直す ((b) の 1 本対症は不採用)。
  焦点走で変異 baseline が回る状態は [T-881] 裁定の前提。
  base: a456211eaf5f25febfdc381260faed6721557d6d260bffe76ae14c956501a57f
