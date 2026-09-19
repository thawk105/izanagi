---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2766-pairing-ab
seq: 1
title: [T-2766] shard 内 pairing を同一 tip の実受入で A/B 隣接対 3 組で対比較し、3 対とも B が 102〜144 秒短い (中央値 112.9 秒 / 24.2 %) を記録した (実装は opt-in のまま impl branch、docs-only land、branch record-dev-wave-t2766-pairing-ab)
---

## 本文

- D2148 項 6 とユーザー依頼 (A/B 交互 3 対以上、採用済みとして本番に入れない、実装面は Codex author) の範囲で 1 wave。
  一次資料は `output/insights/2026-09-19/t2766-pairing-ab/README.md` (対表・witness・裁定パッケージ・再現資料)、設計判断は {{D:t2766-pairing-ab-measurement}}。
  専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-ab/HANDOFF.md`。
- 段 3 相談 1 本 (2 レンズ) は must-fix 5 を出し全採用。最重要は「待ち手 `dev_wave_wait.py acceptance` は claim 直後に main を取り込むので
  隣接 2 走でも tip が変わる」→ 測定走は同一 SHA の wave worktree から `IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py` を直接投入した
  (lease / merge / receipt なし、dispatch と shard child は受入と同一経路)。
- 段 5 は Codex author 1 本 (conftest の後段 1 関数 + opt-in + junit property の witness、allowlist 1 行、G12 test 9 本)。author sandbox では
  pytest が起動できず (guard と qstat preflight) 親の焦点走で 968 passed / 3 failed → test harness の fix1 → 971 passed / 0 failed。
  実装 commit `0eabe67ba` (= 測定 tip)。段 6 はレビュー 2 本 + fix 2 本 (集計器) + 焦点再レビュー 1 本 (NO-GO → launcher 改訂で解消)。
  変異 6 件は probe で観測 node を集めてから final で **6/6 KILLED、期待 node 完全一致**。
- 測定 (2026-09-20 02:03〜05:11 JST): 01-A は dispatch-infrastructure (receipt memo prewarm の memo publication timeout、rc=16) で除外し
  slot 1 を同順序で取り直した。有効 3 対 (03-A/04-B、05-B/06-A、07-A/08-B) の最遅 shard (shard-0) の対差 ΔW = 101.7 / 112.9 / 144.3 秒
  (対率 22.4 / 24.2 / 30.0 %)、対差の中央値 112.9 秒、対率の中央値 24.2 %、条件別中央値差 112.9 秒 → 事前登録の判定 (i) 方向一致・閾値以上。
  shard-1 / 2 は 1〜3 秒差で効果は shard-0 だけ。B 4 走 × 3 shard の witness は全部一致し、`[ccbench-current]` e2e の worker の 2 個目は
  cost 0.0 の partner。同時刻の他 wave 9 session の shard-0 W (378.8〜563.3、中央値 481.1) に対し A は内側、B は全部より短い。
- 棄却・限界: 機序は未同定 (A の律速 worker 386〜411 秒 / 13〜34 item の中身は未観測、相方 20 秒の除去では説明できない)。隣接対は同 allocation で
  なく node も対内で異なる。3/3 は有意差判定ではない。B でも 300 秒目標には届かない (336〜362)。順序依存の赤は B 4 走で観測しなかっただけ。
  warm-up は login の headroom 0 のため計算ノードから共有 FS へ pyc を書かせた (`PYTHONDONTWRITEBYTECODE=` を allowlist 経由で渡す)。
- 採否はユーザー裁定へ返す (README §7: (a) 採用 wave で既定 on にし待ち手経由の実受入 3 対で再確認 / (b) 先に機序調査 / (c) 見送り。推奨 (a))。
  本 wave は実装を main に入れず branch `impl-t2766-pairing-optin` (tip `0eabe67ba`) に保存し、landing は本 insight と fragment だけ。
- 工数: codex 8 本 (consult 1、author 1、fix 3、review 2、focus 1)、計算ノード job = 焦点走 2 + 変異 14 (probe 7 + final 7) + warm 2 + 測定 8 走 × 3 shard。
  land 調停 (別 session) の規則に従い GO 待ちで land した。

## 次の一手差分

### 更新

- [T-2766] **P1・ユーザー裁定待ち (採否)**: 実受入の隣接対 3 組で pairing (B) が 3 対とも 102〜144 秒短い (中央値 112.9 秒 / 24.2 %、事前登録 (i))。
  採否は `output/insights/2026-09-19/t2766-pairing-ab/README.md` §7 の (a) 既定 on にして採用 wave で待ち手経由の実受入 3 対で再確認 /
  (b) 先に機序調査 (A 側 witness) / (c) 見送り。推奨 (a)。実装は branch `impl-t2766-pairing-optin` (`0eabe67ba`、opt-in、main 未収載)。
  機序未同定・同 allocation でない隣接対・regime 依存 (本夜の A ≈ 455〜481 秒) が限界。
  base: 26735ef2f5c861c9a0c13477243bda5644cf676117a9d830a11afbd55e48bf5f
