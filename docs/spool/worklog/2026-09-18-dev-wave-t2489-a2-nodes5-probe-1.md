---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2489-a2-nodes5-probe
seq: 1
title: [T-2489] A-2 認証を nodes=5 で 1 attempt 実走し判断材料を揃えた — 50 分が 12 分 08 秒 (4.17 倍)、検査 24 件・遠隔 16 件すべて受理、node 秒 +16 %。副産物として 2 request が共有 home の bench.lock で cluster 越しに直列化している強い推測を得た (docs のみ、branch worktree-dev-wave-t2489-a2-nodes5-probe、変異 matrix 免除 = 実装面差分ゼロ)
---

## 本文

- ユーザー依頼は「[T-2489] (D1910 項 2 → AI 実測手番) A-2 (rr5 / rr50) 認証系列の `scheduler.nodes` を 5 にするかの判断材料を実測する — A-2 固有の 5-node 実走か同等の probe で、出力同値性・所要短縮・queue 費用を現行 (`orchestrator/campaign/paper_story_a2_certification.py` の policy) と比較し insight に構造化する。A-6 の nodes=5 結果は A-2 へ一般化しない。恒久採用の裁定は本 wave では下さず、実測後に索引へ戻す形で報告する。実装差分は既定ゼロ (policy を変える場合は別 wave)。規律 2 を緩めない。本題の実測だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **実測は取れた。裁定は下していない。** 一次資料は `output/insights/2026-09-18/t2489-a2-nodes5-probe/README.md`。decisions fragment は無し (新しい設計判断なし)。
- 実走: attempt `t2489-20260918a` (request `4978.nqsv` = rr5、`4979.nqsv` = rr50、各 5 ノード、gen_S)。投入元は job dir の使い捨て submit-tree (main tip `d2ebef7a4` + A-2 policy の `scheduler.nodes` 1→5 の 1 行だけの commit `3f61c3408`、branch `probe/t2489-a2-nodes5-submit`。wave branch / main へは入れない)。Elapse 680 s / 728 s (現行 nodes=1 の `t2364-20260907b` は 3020 / 3037 s)。queue 待ち 87 s / 18 s。検査 24 件すべて serializable / certified / anomaly 0、遠隔 result 16 件すべて success で head の MAC 照合を通過。driver_rc 0。`finish-group` まで行い `collect` は行わない。
- 費用: Σ nodes × Elapse は 6057 → 7040 node 秒 (+16.2 %)。兄弟 4 ノードの実働は予約の 41 %。`protocol_sha256` は nodes=1 / 5 で同一 (`d99f08bc…`、現行 attempt の `136b823e…` との差は T-2198 の policy 改版によるもので nodes 無関係)。
- **副産物 (段 1 で判明):** 現行 A-2 の 50 分は検査 5 本の直列だけでは説明できず、rr5 / rr50 の 2 request が別ノードで走りながら `~/.izanagi/bench.lock` (`lock.py:default_lock_path`、job body は `IZANAGI_BENCH_LOCK` 未設定、`/home` は Lustre `flock` mount) で performance 検査 pass と bench を cluster 越しに直列化している。WAL の時刻と fan-out task.json の作成 mtime が 3 attempt × 2 cell で秒単位に整合する**強い推測** (WAL に lock 記録が無いので立証ではない)。nodes=5 でも 2 head は同じ lock で直列化したまま。lock を node-local にした静的見積りは nodes=1 で約 30 分、nodes=5 で約 8 分 (未実測)。
- 段 3 相談 1 本 (read-only、`gpt-6-astra` / medium): 11 所見 (must-fix 9 / nit 2) をすべて採用 — 投入 command の必須引数、片側投入の記録手順、lock 直列化は「強い推測」として書く、fan-out でも head は lock を保持、A-2 trace の容量は未確認と明記、失敗分類の是正、同値性を「科学的条件」と「成果物の対応」に分ける、親の 24 分見積りの誤り (正しくは 12〜15 分、実測 12 分)、費用は Σ nodes_i × Elapse_i。段 6 レビュー子は省略 (軽量版)。
- 工数: codex 子 2 本 (consult 1、author 1 = submit-tree の 1 key 編集のみ、全段 `gpt-6-astra` / `medium`)。親の実測: 5 ノード実走 1 attempt (2 request、計 1.96 node 時間)、現行 attempt 3 本の WAL 解析、protocol_sha256 の実測 2 回、`/proc/mounts` 確認。受入全走は docs commit 後の最終 tip (結果は land の受領証)。
- 残置: 使い捨て submit-tree (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2489-a2-nodes5-probe/submit-tree`、worktree lock 済み) と branch `probe/t2489-a2-nodes5-submit`。撤去・branch 削除はユーザー指示時のみ。

## 次の一手差分

### 更新

- [T-2489] **P2・ユーザー裁定待ち (D1910 項 2 の実測完了)**: A-2 の `scheduler.nodes` を 5 にするかの判断材料は
  `output/insights/2026-09-18/t2489-a2-nodes5-probe/README.md` §9 に揃った。裁定は 3 点 — (i) A-2 policy の nodes=5
  採否 (実測: 壁時計 50 分 → 12 分 08 秒、node 秒 +16 %、検査 24 件・遠隔 16 件すべて受理。採るなら別 wave で
  policy 1 key + テストの policy sha256 pin 更新 + 波及閉包、T-2429 と同形)、(ii) A-2 / A-6 の job body で
  `IZANAGI_BENCH_LOCK` を node-local (`$TMPDIR/bench.lock`、b10 / a5 と同形) にするか (共有 home の lock による
  cluster 越し直列化は強い推測。静的見積り nodes=1 で約 30 分、nodes=5 で約 8 分。採るなら実測 1 本)、
  (iii) 遠隔実行に walltime より短い総 timeout を入れるか (T-2457 §9 の再掲)。
  base: 710e56bf58bc6262b3c7f71bc743a3a358a8454b0195651af8ed239b7703ce36
