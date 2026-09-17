---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2760-tictoc-floor-baseline
seq: 1
title: [T-2760] between-run floor の BASELINES に根拠つき TicToc baseline を登録した — CMake cache 既定 = 認定較正と同 genome、引数解析・protocol 別出力・hook 不在時の build 前拒否を test と変異で固定、実測は開通させない (コード + テスト + docs、branch worktree-dev-wave-t2760-tictoc-floor-baseline、変異 matrix = baseline PASSED・負例 7/7 KILLED 期待 node 完全一致・等価 M0 SURVIVED・MISMATCH 0)
---

## 本文

- ユーザー依頼は「[T-2760] (P2、D2114 項 4) `orchestrator/campaign/between_run_floor.py` の `BASELINES` に根拠つき TicToc
  baseline を追加し、引数解析・protocol 別出力・hook 不在時拒否を確認する。着手直前の local main から fresh worktree を作る。
  完了条件に実測を含めない。baseline の根拠は既存の silo / mocc 登録と同じ形で書く。実装面は Codex author (D95)、変異事前登録 =
  hook 不在で拒否・protocol 別出力の負例。規律 2 を緩めない。本題の baseline 追加だけ。仮想リスク向けの gate・検査・台帳・
  一般化は scope 外」。
- **閉じた。** 一次資料は `output/insights/2026-09-17/t2760-tictoc-floor-baseline/README.md`。設計判断は
  {{D:tictoc-floor-baseline-cmake-default}}。実装 commit `5fa44cfb1` (Codex author、2 file、+191)。
- **根拠 (親が brief 前に実測):** tictoc の stock genome = `tictoc|BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,PREEMPTIVE_ABORTS=1,TIMESTAMP_HISTORY=1`
  は (1) 現行 pin 511c9538 の `external/ccbench/cmake/Options.cmake` の cache 既定と一致 (mocc 登録の根拠「CMake defaults」と同形、silo だけ
  p2_2 の歴史的 stock BACK_OFF=0)、(2) `TICTOC_SPACE` の点 (no-wait (1,0)、D1418)、(3) D2083 が登録した accepted な tictoc 認定較正
  record 2 件 (rr50 `calibration-9b49335d02ad4d2e.json`、rr95 `calibration-cb98513996e5ae35.json`) の `genome` と文字列一致、
  `tools/pegasus/certify_calibration.sh` の tictoc 軸表 (D1863) とも一致。mocc の record 2 件も `BASELINES["mocc"]` と一致。
- **受理集合不変を実測:** 現行 pin で `_protocol_source_has_trace_hook_evidence_only` は silo True / mocc False / tictoc False。
  `--protocol tictoc` は引数解析を通り、D1373 の関門が build 前に `ValueError` で拒否 (`_assert_single_tenant`・build・measure・
  write のいずれも呼ばれない、test で calls 空を固定)。関門の bytes・silo / mocc entry・出力 stem・既存 floor JSON 4 件は不変。
  D2083 項 6「BASELINES へ tictoc を足すことも行わない」は同 wave の scope 判断で、D2114 項 4 が本 T として起票した。
- 軽量版 (DW-C00 の 3 条件: 設計択一なし・防壁コード非接触・floor 生成の受理集合不変) で段 2・3・段 6 review 子を省き、Codex author 1 本。
  author 子の wrapper pytest は sandbox の uid 名前空間で `qstat -Q` が EACCTAUTH → rc=16 (親側は rc=0、実 dispatch の障害ではない)。
  親の焦点走: `test_between_run_floor.py` 34 passed (login 4.9 秒)、consumer / meta-test (use_perf closed-set、floor_pair_driver、
  g5 ledger coverage、test_screening_driver / test_pegasus_floor_scoping / test_codex_agents) 115 passed (login 54 秒)。
- **変異 matrix (container worktree `dev-wave-jobs/…/mutation-tree` @ 5fa44cfb1、`run_tests.py --force-dispatch` 1 file、probe と本走で各 9 run =
  baseline + 8 変異、計算ノード dispatch)。** probe (全件 SURVIVED 登録、baseline 27.6 秒) で観測 node を集め、段 4 の事前登録と全件一致を
  確認してから本走 (baseline 684 秒、queue 待ち込み)。本走は baseline PASSED、負例 M1〜M7 すべて KILLED で期待 node と観測 node が完全一致
  (matching 8/8)、等価 M0 (entry 行の末尾 comment) SURVIVED、MISMATCH 0、TIMEOUT 0、anchor 全件 1 箇所。M1 登録不在 → 新規 6 node、
  M2 BACK_OFF 1→0 → Options.cmake 束縛 test だけ、M3 no-wait (1,1) → 空間所属 + Options 束縛の 2 node、M4 hook 関門の恒偽 (規律 2 の負例)
  → tictoc / mocc の拒否 test 2 node、M5 stem が silo と衝突 (protocol 別出力の負例) → stem test だけ、M6 引数解析の恒偽 → cicada 拒否
  test だけ、M7 baseline を silo 固定 → tictoc / mocc の経路 test 2 node。走行後の container は実装 commit と同一 bytes。
- 段 8 (自己改善): 候補ゼロ。
- 工数: codex 子 1 本 (author、`gpt-6-astra` / `medium`、14 call)。親の実測: 焦点走 2、provenance full 1、変異 2 走 (probe + 本走、計算ノード dispatch)、受入全走は docs commit 後の最終 tip に対し land 前に行う (結果は land の受領証)。

## 次の一手差分

### 完了

- [T-2760] `BASELINES["tictoc"]` を根拠つきで登録し、引数解析・protocol 別出力・hook 不在時の build 前拒否を test と変異で固定した。
  実測の開通は hook 移植 (T-2759) と pin 再承認 (D1603) の別件。
  remaining: none
  base: 199b26551dd645b97b888f4ddaaec264186909c14d1f69e6dd031330a891c8c1
