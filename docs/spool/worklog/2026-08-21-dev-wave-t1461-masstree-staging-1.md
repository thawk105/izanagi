---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t1461-masstree-staging
seq: 1
title: floor campaign の masstree staging transport を調査したが command 前提が実効性ゼロと判明し実装しなかった (docsのみ、branch worktree-dev-wave-t1461-masstree-staging)
---

## 本文

- D399 の設計 (`IZANAGI_SORT_SWO_MASSTREE_ROOT` env var transport) に従い
  `tools/pegasus/floor_campaign.sh`/`submit_floor.sh` の 2 file へ masstree staging 配線を
  追加する「最小実装」を目的として着手した。開始時重複チェック (ListAgents 15 peer、
  全 13 locked worktree の diff 走査) では重複なしと確認した。
- **brief 段階で command 前提を覆す事実を確認した**: `IZANAGI_SORT_SWO_MASSTREE_ROOT` は
  floor campaign の実行経路 (`orchestrator/campaign/s8b_floor_campaign.py`) から一切
  参照されない。floor の実際の masstree 依存解決は独立した `build_cells()` の
  `fetchcontent_base_dir` 引数 (段2 codex が親の初期認定「`_run_campaign_core`」を訂正)
  を通るが、production wrapper/CLI はこれを一切転送していない。よって 2 file だけの
  配線は効果ゼロ (dead wiring)。
- 段2 codex (read-only、reasoning=max) がこの認定を独立検証し、案A (command 文字通り、
  効果ゼロ)・案B (`s8b_floor_campaign.py` への pass-through 追加、measurement logic 領域)・
  案C (shell 内 monkeypatch、提示形は `TypeError` で動作せず) の 3 案を file:line 粒度で
  提示した。
- 段3 敵対相談 3 レンズ (scope・権限/正しさ・信頼境界/技術的実効性、いずれも
  `--lane luna --reasoning max`) が独立に「本 wave では実装しない」へ収束した。scope
  レンズは (iv) docs-only 裁定パッケージ返却を推奨。correctness レンズは config.h/archive
  の期待 hash 不在と pin 検査が CMake 実行後という 2 件の CONFIRMED/P1 所見を検出。
  **effectiveness レンズが最重要所見**: `_prepare_floor_oracle_dependency()` は
  `fetchcontent_base_dir` の中身に関わらず毎回無条件でネットワーク越し buildcache 呼出しを
  行うため、案B/C の pass-through 追加だけでは T-1431 の障害を解消しない。
- **裁定: 本 wave ではコードを一切実装しない。** DW-S04 に従い設計択一・所見を
  裁定パッケージとして記録する。新規 decisions エントリは、何も採用しないため見送った。
  詳細・file:line 根拠は `output/insights/2026-08-21_t1461-masstree-staging-scope-finding/README.md`
  参照。
- F1 — D399/[T-1431] insight が指した意図された consumer が、floor 実際の呼出し経路とは
  独立に分岐していたため、決定文が指す機構の存在確認だけでは不十分だった (F1 と同型の
  近似再発として記録、詳細は failures fragment 参照)。
- T-1431 床値 pilot 再実行は元の command 指示どおり本 wave scope 外のまま。
- エージェント工数: Codex 子 4 本 (段2 plan 1 本、段3 consult 3 本、すべて
  `gpt-5.6-luna`/`reasoning=max`/`sandbox=read-only`)。実装子 0 本。

## 次の一手差分

### 更新

- [T-1461] **P1・実装は次 wave (ユーザーの scope 拡大裁定待ち)**: 「floor_campaign.sh/
  submit_floor.sh の 2 file への `IZANAGI_SORT_SWO_MASSTREE_ROOT` 配線」という元の記述は、
  floor 実行経路に到達しない dead wiring と判明したため無効。実効化には
  `_prepare_floor_oracle_dependency` への network-build skip-logic 新設 (measurement logic
  変更、Codex `role=author` 必須)、config.h/archive の期待 hash 独立束縛、pin 検査の前倒し、
  DW-G01 生死実験が要る。詳細は
  `output/insights/2026-08-21_t1461-masstree-staging-scope-finding/README.md` 参照。
  base: c615a0d0911e851d65d2b7797883d96f4d3931ae9636b8dcc1e282dea96d036c
