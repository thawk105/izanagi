---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t1473-d58-ablation-preflight
seq: 1
title: D58 bench-first screening v2 の初回ablationをPegasusで試みる前にscreening/floor編集面の並行占有を検知し本走を見送った (docsのみ、branch worktree-dev-wave-t1473-d58-ablation-preflight)
---

## 本文

- 背景: ユーザーが command 引数で「T-1473」と呼んだ依頼は、D58 bench-first screening v2 の初回
  ablation (`output/insights/2026-07-14_bench-first-screening-design.md` §5-7 の4基準 = 誤棄却
  ゼロ・結論不変・機械時間削減率実測・同一 genome の on/off fitness が floor 内一致) を進めるもの
  だった。同じ試みは `docs/archive/worklog-phase3-0819-701.md` (entry701、2026-08-19) に先例があり、
  当時は Pegasus に `g++-13` が無く `source_digest.resolve()` の fails-closed (D23) で起動6秒後に
  停止していた。
- g++-13 blocker は解消済みと確認した: T-1444 (`docs/decisions.md` D601/D628/D629、本日
  2026-08-21 land 済み) の site 依存 compiler 解決により、`orchestrator/campaign/buildcache.py`
  の `compilers_for_current_site()` が Pegasus compute では無印 `gcc`/`g++` (system 実在確認済みの
  gcc 11.4.0 相当) を選ぶよう変更されている。D629 は screening 経路の attestation 非対称・floor
  calibration の Linux 固定 directory も解消済みである。
- しかし wave 開始直後の棚卸しで、command が指示した T425/T972/T1438 の screening/floor/
  calibration 編集面と計算ジョブの重複を実測した:
  - [T-425] (`worktree-dev-wave-t425-floor-bounded-prep`) が生存中 (claude session pid 799659、
    受入投入 pid 1004978 実行中、経過26分超) で、`orchestrator/campaign/screening_driver.py` の
    `load_between_run_floor()` と `orchestrator/campaign/between_run_floor.py` を直接改変する
    commit (`3ef63484`、本日10:49、段6敵対レビュー言及あり) を持つ。同 wave の handoff は
    「between_run_floor.py の screening 接続を新規配線し直すと重複実装になる」と明記している。
  - [T-972] (`worktree-dev-wave-t972-perf-preflight-receipt`) も生存中 (受入投入 pid 663654
    実行中、経過40分超) で `s8b_floor_campaign.py`/`s8b_floor_contract.py`/`s8b_ratified_freeze.py`
    (S8b 系の別 floor 機構) を改変しており、直近の受入 attempt で実際に `owned-path-overlap`
    (rc=70) 衝突を経験済みと実測した。この編集面クラスタでの並行作業は理論上でなく実際に衝突する。
  - [T-425] の merge ログから、別の (未特定・main へ着地済み) wave が直近数時間で
    `screening_driver.py` の `_default_calibration_dir()` を変更した形跡を検出し、calibration-dir
    解決自体も流動的と判明した。
  - [T-1438] (`worktree-dev-wave-t1438-oracle-prewarm-design`) は real-repo serialization テスト
    のみを対象とし、screening/floor/calibration とは無関係 (free) と確認した。
  - 受入 lease は wave 開始時点で他 holder (`3bf5d510308c`) が保持中だった
    (`tools/wave_land_window.py status --json` 実測、age≈568秒)。
  - `output/env/pegasus/calibration/registered/` の既存2件を実測すると、いずれも
    `ycsb_rratio="50"` (balanced) であり、command が指定した read-heavy (`ycsb_rratio="95"`) 用の
    Pegasus between-run floor 較正はまだ存在しないと確認した。
  - `docs/pegasus-runbook.md:1444-1445` が明記する「`campaign` の dispatch task は未実装であり、
    campaign を計算ノードへ送る sanctioned 経路は存在しない」という既知の欠落 (`tools/pegasus/
    dispatch_compute.py` の `TASKS` は `tests`/`provenance` のみ) も現時点で解消されていないと
    確認した。entry701 が使った投入手段 (qsub 直接投入) も sanctioned submit script として repo 内
    に特定できなかった。
- 裁定 (P1、段4相当): 上記の資源競合 (2件の生存 wave による同一編集面の能動改変、直近の実
  owned-path 衝突実績、read-heavy 用 Pegasus calibration 欠如、sanctioned dispatch 経路欠如) に
  より、本走 (計算ノードでの `backoff_sweep.py --screening` 実行) を見送り、command の代替指示
  どおり zero-diff preflight として記録に留めた。実装差分・計測はいずれもゼロ。「次の一手差分」の
  新規項目に、次回試行の exact command と前提条件を記録する (古い結果を新規結果として扱わない)。

## 次の一手差分

### 新規

- {{T:d58-ablation-pegasus-preflight}} **P2・新規**: D58 bench-first screening v2 の初回 ablation
  (`output/insights/2026-07-14_bench-first-screening-design.md` §5-7 の4基準) を Pegasus 計算ノード
  で実施する。g++-13 blocker (旧 entry701) は T-1444 (D601/D628/D629) で解消済み。
  **次回試行の前提条件 (本 wave で確認済み):**
  1. [T-425]・[T-972] が着地し、`screening_driver.py`/`between_run_floor.py`/calibration-dir
     解決が安定していることを確認する (本 wave 時点で両方とも生存中の並行 wave として同じ編集面を
     改変中だった)。
  2. read-heavy (`ycsb_zipf_skew=0.9, ycsb_rratio=95, ycsb_rmw=0`, records=1,000,000, threads=48)
     の Pegasus 側 between-run floor calibration を新規取得する (本 wave 時点で
     `output/env/pegasus/calibration/registered/` の登録2件はいずれも balanced=rratio50 のみ)。
  3. `backoff_sweep.py` 系 campaign を計算ノードへ送る sanctioned dispatch 経路が repo 内に無い
     (`docs/pegasus-runbook.md` 1444-1445行、`dispatch_compute.py` の `TASKS` は `tests`/
     `provenance` のみ) — entry701 同様の手作業 qsub を踏襲するか、新規 sanctioned submit script
     を用意するかを次回 wave の段1 brief で決める。
  4. exact command (記録): screening off (基準・全8 genome の verify+bench) =
     `python3 orchestrator/campaign/backoff_sweep.py read-heavy`。screening on =
     `python3 orchestrator/campaign/backoff_sweep.py read-heavy --screening --calibration-dir
     <resolved pegasus calibration dir>` (省略時は resolved env scope を自動使用)。両方を計算
     ノードで実行し、同一 genome 集合 (無backoff・適応・静的6点=計8) の WAL を比較して D58 の
     4基準を判定する。期待 artifact = `output/campaigns/backoff-sweep-silo-read-heavy-sweep-
     <off-hash>/runs/wal.jsonl` と `-<on-hash>/runs/wal.jsonl` の2本、および両者を比較する
     ablation report (形式は次回 wave の段1 brief で設計、既存テンプレートなし)。
