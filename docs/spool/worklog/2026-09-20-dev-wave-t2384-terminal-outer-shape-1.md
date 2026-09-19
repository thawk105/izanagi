---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2384-terminal-outer-shape
seq: 1
title: [T-2384] 8c formal consumer の FC07 に terminal record の外枠 exact gate (D1730) を実装し、変異 9 本を 8 KILLED + 逐語 B-057-M5 は等価 SURVIVED で完全一致させた (コード、branch worktree-dev-wave-t2384-terminal-outer-shape)
---

## 本文

- D1730 (ユーザー裁定 2026-09-07) の実装を 1 wave で行った。実装 commit `2579b4638` (Codex author)。一次資料は
  `output/insights/2026-09-20/t2384-terminal-outer-shape/README.md`、設計判断は {{D:terminal-outer-shape-gate-impl}}。
  専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2384-terminal-outer-shape/HANDOFF.md`。
- 段 1 で条件 dispatch 13 (DW-O13、期限 = 段 2 前) を辿らず段 3 の後に気づいたため、段 2〜4 の r1 成果物を無効化し、実環境 log
  (campaign 実走 32 file・terminal 490 件、outer 5 key exact 490/490、attempt 世代は attempt ごとに terminal 1 件 = 16/16) を実測してから
  段 2〜4 をやり直した (F50 型の再発、実害なし。r1 / r2 の結論は同じだったが流用していない)。
- 段 3 相談 (r2、2 レンズ) は must-fix 0 / nit 5。親 brief の (P3)「gate 後は `_wal_field` の fallback が死ぬ」は逆で、死ぬのは `stage` の分だけ
  (`build_attempt_id` / `verify` 等は payload fallback が必須) と訂正。plan の末尾性項は既存 stage 判定と過剰決定なので落とし、
  焦点走は `test_reflux_campaign_issuer.py` を足して 12 file にした。
- 段 5 は Codex author 1 本 (2 file、+119 行)。author sandbox では dispatch preflight (qstat) で pytest 未起動 → 親の焦点走 12 file
  (計算ノード、job 11911): **1016 passed / 0 failed**。段 6 レビュー 2 本は must-fix 0 (nit 1 = 焦点走 log の file 集合は dispatch receipt で補う)、fix 子なし。
- 変異 (事前登録 9 本: 逐語 B-057-M5 = 等価 SURVIVED 期待の positive、gate 無効化 + M5 の合成 = both-layers、gate 固有 6 本、過剰拒否の正例 1 本):
  probe → final の 2 段で **8/8 KILLED、期待 node 完全一致、M01 (逐語 M5) は等価どおり SURVIVED (注入 diff で実在確認)、matches 9/9**
  (final spec sha 6032ea62…、repo_head 2579b4638)。probe の観測 node は段 4 の静的予測と 9 本すべて一致。
  独立 clone は `dev_wave_submodule_init.py` に拒否されたため、裁定に書いた fallback (主 repo の登録 worktree + `mutation_harness.py --repo`) で走らせた (README §5 の erratum)。
- 限界: certified 選択集合は変わらない (`P6Unavailable`)。rejected 側の本番 projection が FC07 で止まる件 (D1715) は未解消。新 test は canonical-list 経路だけ。
- 工数: codex 子 9 (plan 2、相談 4、author 1、レビュー 2)、計算ノード job = 焦点走 1 + provenance 監査 1 + 変異 probe 10 run + final 10 run + 受入。
- 段 8 候補: 条件 13 の読了遅れは F50 型の再発として記録する (入口・reference の編集は行わない。段 1 brief 直後に条件表 08/09/10/13 を一括再評価する習慣は memory 側へ)。

## 次の一手差分

### 完了

- [T-2384] D1730 の terminal record 外枠 exact gate を FC07 へ実装した (commit `2579b4638`、負例 12 / 正例 2 node、焦点走 12 file 緑、変異 8/8 KILLED + M5 等価 SURVIVED)。
  remaining: none
  base: cc7438f14aa41fb9e3e3de84d6875dca7e796d0c4b268c92ce2490d3598e5264
