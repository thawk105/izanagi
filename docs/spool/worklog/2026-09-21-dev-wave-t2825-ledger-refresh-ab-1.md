---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-t2825-ledger-refresh-ab
seq: 1
title: [T-2825] 受入所要時間台帳を refresh mode で再生成し、固定 2 tree の隣接対 3 対で shard-0 wall を測った — 事前登録の判定は (i) 方向一致・閾値以上 (対差の中央値 147.8 秒・対率 30.6 %、対 3 は 7.9 % で 1 走比較として変化なし)、L の node は入れ替わったが事前登録した L 伸長の条件は満たさない (台帳 + insight、branch worktree-dev-wave-t2825-ledger-refresh-ab)
---

## 本文

- 依頼 (command 引数、D2107 / D1936 項 35 / T-2817 README §5 (a)) を軽量版 + 段 3 相談 1 本 + 段 6 review 2 本で処理した。段 3 相談 (高 3 / 中 3) は全件採用
  (開始時刻は観測でなく推定、入力の collection 一致の実測、有効走・無効対の全列挙、shard 構成の変化、warm の対称化、land の bytes 照合)。相談の「変異 matrix 適用外」だけは
  D95 決定 2 (台帳は `orchestrator/` 配下 = 実装面) により refuted とし、既存 test が新台帳の凍結 pin と被覆を束縛することを変異 3 本 + 等価 1 本で確かめた (final: KILLED 3 / SURVIVED 1、matching 4/4)。
- 依頼の「同一 tip」は台帳 path が conftest と割付器で固定のため literal には作れず、D2177 の固定 2 tree (A = `21641fee7` / B = A + 台帳 1 file) で測った。D2068 の同一 tree 条件は満たさない。
- 入力走は選定締切 08:47 JST の最新適格走 `9d955ce2…` (より新しい 2 本は赤 1 件 / 未完走で不適格)。main collection と nodeid・marker 行の多重集合が完全一致。
- 依頼の「未収載 334 unit の再登録」は、T-2817 の 334 件のうち 202 件が登録され、132 件 (すべて凍結 8 suite 内) は D2107 どおり据え置きになった。「334 件を再登録した」とは書かない (段 6 review B の指摘)。
- 測定: 投入 7 走 (09:53〜13:31 JST)。03-B は別 session の worktree 撤去で `test_t810_coordinator.py` 3 件が赤 (F633 の再発)、単独再走 3 passed で infra に分類し対を同順序で取り直した。
  shard-0 の構成は A / B で同一 (台帳が変えたのは shard-1 ↔ 2 の割付と shard 内の順序)。B では active_v2 系 8 node が最初の配布窓に入り t=0 から並んで 209.7〜246.3 秒ずつ走った。
- land 前に local main `d99c556df` を取り込んだ。T-2344 の add-only 433 件と台帳が競合し、Codex fix 子が main の現物を base に同じ入力で `--refresh` を再走した結果は測定 B と bytes 一致
  (落ちた node 312 件 = T-2344 の新設 172 件 + 旧名 140 件、取り込み後 collection への被覆 98.25 %)。
- 落とし穴: review / fix / focus 段の launcher に `--reasoning` を書くと起動器が rc=2 (F953 の再発、子 0 call)。`check_wave_startup.py --mode midflight` は `--external-handoff` を受けず、
  merge 途中は rc=1 (merge を中止して検査を通し、子の後に merge し直した)。隔離 session の guard は python `-c` の書き込みを拒否することがあり、行末空白の正規化は grep / sed / Write に分けた。
- 工数: codex 子 = consult 1 + author 3 (台帳 / probe / 変異 spec) + review 2 + fix 3 (probe 2 巡 + 台帳 1) + focus 2 の 11 本 (review 2 本は初回 rc=2 で再投入)。
  計算ノード = 変異 2 系列 (probe / final)、warm 2、測定 7、単独再走 1。壁時計は開始 gate 08:35 JST (`startup-gate.log`) → 記録 commit (本 entry 直後の commit 日時) まで。
- 一次資料 `output/insights/2026-09-21/t2825-ledger-refresh-ab/README.md`。

## 次の一手差分

### 完了

- [T-2825] 台帳を D2107 の refresh mode で再生成し (B commit `26387b617`、凍結 426 entry 不変)、固定 2 tree の隣接対 3 対で測った: W_0 の対差 147.8 / 200.7 / 29.6 秒 (対率 30.6 / 39.2 / 7.9 %)、判定 (i) 方向一致・閾値以上、W_max も (i)、O_0 は各対 148.2 / 200.9 / 29.1 秒減、L は判定条件を満たさない (ΔL +7.3 / −9.0 / +1.1 秒、L の node は b5 → failed_launch に交代)。参考値 (model 差 19.5 秒、観測 `O_max − L` 62.7 秒) は判定に使っていない。land 前の main 現物からの再走は測定 B と bytes 一致。
  remaining: none
  base: 113235b125eefb80870373b1d7f1428c4ab800966a34e089e1d846fff137183a

### 更新

- [T-2273] **P1・律速を再同定 (第 3 回)、refresh 後の床を [T-2825] で観測**: T-2817 が同定した「ledger 未収載 → 後方 rank → 別 worker の直列」は、refresh 後の B 3 走では観測されなかった (shard-0 W_0 310.7〜344.9 秒、O_0 237.0〜270.5、`O_0 − L_0` 14.7〜43.1)。refresh 後の shard-0 の最大占有 worker は、t=0 から並んで走る active_v2 系 8 node の 1 本 (213.0〜237.0 秒) の後に 20〜31 秒の item が 1〜2 個続く形で、8 node はそれぞれ 209.7〜246.3 秒 (A で t ≈ 55 秒から先頭に立った同系 node は 189.98〜208.09 秒、原因は未測定)。L は `test_t080_failed_launch_preserves_receipt_refusal` (222.3〜246.3 秒)。固定費 F_0 (A 72.7〜74.9 / B 73.2〜74.5 秒、pre 62.6〜64.4 + post 10.03〜10.07) は条件差が見えず、pre の内訳は [T-2826]、post は [T-2827]。次の律速同定はこの形から始める。5 分上限超過を受容しない。一次資料 `output/insights/2026-09-21/t2825-ledger-refresh-ab/README.md`。
  base: f6519a881093d747cd7d15291482296b573b48fe83e5fa7901bedb5d35f6945b
