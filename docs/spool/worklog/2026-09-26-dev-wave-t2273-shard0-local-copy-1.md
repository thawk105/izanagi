---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-26
wave: dev-wave-t2273-shard0-local-copy
seq: 1
title: [T-2273] [T-2560] 共有 base の可視 output 複製元を session 局所の写しへ替える実装を隣接 3 対の実受入で測り、事前登録の land 条件を満たさなかったので実装は land しない (記録 + insight、実装は branch worktree-t2273-shard0-local-copy に保存)
---

## 本文

- 依頼: 受入 shard-0 の律速 (第 4 回診断の t080 共有 base builder による Lustre の output/ 可視集合の複製) を、複製元を計算ノード局所の写しに替えて解き、隣接対の実受入で効果を測ってから land する。insight `output/insights/2026-09-26/t2273-shard0-local-copy-ab/README.md`、判断 {{D:t080-visible-output-lazy-local-copy-not-landed}}。
- 結果: 有効 3 対の shard-0 W_0 の対差 +19.111 / +19.679 / −4.341 秒、対率中央値 5.2 %。事前登録の land 条件 (3 対すべて短縮 ∧ 対率中央値 ≥ 10 %) を満たさず、実装 (`eb65d322f`、Codex author) は local main へ入れない。変異 M1〜M5 は全件 KILLED、焦点走 716 passed / 9 skipped。
- ユーザー裁定: 2026-09-23 に計算量の見積り約 2.2 node 時間 (対を取り直すごとに +0.5) を示し「3 対で投入」の回答を得た。実績は受入系列 29 shard job の Elapse 合計 8,333 秒 (2.31 node 時間、失敗走を含む) と焦点走 303 秒、変異・温めは外側所要の上限でそれぞれ 4,557 秒・13 分 (queue 待ちを含む)。
- 異常: 系列の 1 走目 (2026-09-23 23:51) が infra で止まり、会話が 2026-09-26 まで止まっていた (ユーザーの「続けて」で再開)。投入 10 走のうち infra 由来の失敗 3 走 (A 2: queue 待ち超過・早期 memo 待ち超過、B 1: 早期 memo 待ち超過)。早期 memo 待ちの超過 (`real_repo_receipt_memo` の 120 秒上限) は 2026-09-22 以降の受入 66 session のうち本 wave の 2 走だけで、条件によらず 2026-09-26 午前に集中した。orphan hold は runbook §7.6 の手順 (qstat で不在または終端を確認 → HEAD・clean 確認 → hold 削除、qdel なし) で 2 回解除した。
- 段 3 / 段 6 の棄却: 段 4 で A1 (session snapshot で拒否経路が消えうる) を「受理集合の変化としては refuted、意味の差は docstring で明記」、B3 (新規 test の直接複製との mtime 照合は重複) を refuted とした。段 6 の A1 / B1 (新規 node 1 件で collection 完全一致が全対を無効にする) は real で、事前登録を erratum E1 で訂正してから系列を投入した。
- 記録の受入 1 回目 (tip `97af2ed92`、2026-09-26 13:10 投入) の赤 1 件 `orchestrator/tests/test_dev_waves_integration.py::test_malformed_child_output_is_output_invalid[oversize]` は非帰属と判定した。本文は期待 `log-limit` に対し `spawn-failed` (子起動の失敗)。記録 tip は main + docs / insight だけで、dev-wave supervisor の子起動経路に届かない。DW-O18 の単独再走 (同一 tip、29371.nqsv) は 1 passed in 5.20s で非再現。受入を投げ直した。
- 工数: Codex 子 9 本 (plan 1、consult 2、author 2、review 2、fix 1、focus 1、うち計測 probe 系は author 1 と fix 1)、Claude 調査子 1 本。

## 次の一手差分

### 更新

- [T-2273] **P1・律速対処の 1 案を実受入で棄却、次の一手はユーザー裁定待ち**: 第 4 回診断の次の一手「t080 共有 base の可視 output 複製元を局所に置く」を、session で最初の builder が写しを作る形で実装し (branch `worktree-t2273-shard0-local-copy`、`eb65d322f`)、隣接 3 対の実受入で測った。shard-0 W_0 の対差 +19.111 / +19.679 / −4.341 秒、対率中央値 5.2 % で、事前登録の land 条件を満たさず land しなかった ({{D:t080-visible-output-lazy-local-copy-not-landed}})。B の W_max 中央値 348.387 秒で 5 分上限を超えたまま。診断の −123.9 秒は写しを事前に用意した対照の値で、直列 1 本の Lustre 複製が依存 builder に残ることと整合する (未計測)。候補: (a) 写しを collection 中 (pre ≈ 64 秒) に作る形の効果を先に測る、(b) 律速を発行 subprocess (診断 X の依存 builder で 79.4 秒、CPU 支配、内訳未測定) へ移す、(c) 本実装を改善なしの中立な整理として land する (事前登録外の新しい判断)。5 分上限超過を受容しない。一次資料 `output/insights/2026-09-26/t2273-shard0-local-copy-ab/README.md`。
  base: c8be54627731fe4804a1bcd5e4347040db4389509ec42819635733485bc67911
- [T-2560] **P1・追認済み、第 4 回の次の一手を実受入で棄却**: D1936 項 35 のとおり実測で律速を選んだ (第 4 回 = 共有 base 構築の可視 output 複製、insight `output/insights/2026-09-23/t2273-shard0-bottleneck-4/README.md`)。その次の一手 (複製元の局所化、最初の builder が写しを作る形) は隣接 3 対の実受入で対率中央値 5.2 % にとどまり land しなかった ({{D:t080-visible-output-lazy-local-copy-not-landed}}、insight `output/insights/2026-09-26/t2273-shard0-local-copy-ab/README.md`)。次の一手は [T-2273] の候補から選ぶ。
  base: ac7be0cc6a5c95c5c2d8b50825d7623f7443eb02ec937ecb1086eb55a538b044
