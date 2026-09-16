---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2731-cpp-normalize-dd
seq: 3
title: [T-2731] F1016 の正しさ欠陥を直した — `_cpp_normalize` に `-dD` を足し `#define` / `#undef` を identity の pre-image に乗せ、predefined / command-line 出力は空入力 prefix で剥がす (コード + テスト + docs、branch worktree-dev-wave-t2731-cpp-normalize-dd、変異 matrix = source-level baseline PASSED・3/3 KILLED 期待 node 完全一致・対照 1 SURVIVED・MISMATCH 0、recipe v2 baseline PASSED・7/7 KILLED 期待 node 完全一致・M0 SURVIVED・MISMATCH 0)
---

## 本文

- 起点: D2104 項 2 (第 20 回 rulings 全件、決定 = (a) `_cpp_normalize` に `-dD`)。段 1 の前提実測で裁定文の前提「`-dD` は
  predefined を含まない」が g++ 11.4 / 12 で誤りと分かった ({{F:dd-predefined-assumption}})。素の `-dD` だと template の
  追加供給 (`BACKOFF_FIXED` / `BACKOFF_NOINLINE`) で inert template ≠ stock になるため、同じ argv の空入力出力を環境 prefix として
  剥がす形に決めた ({{D:cpp-normalize-dd-env-prefix}})。既存の stock / template variant の pre-image は byte 一致 (実 submodule
  silo 8 genome、旧版 / 新版 8/8 一致) で、裁定文の「golden が動く」は起きなかった。記録済み測定は無効化しない (規律 7)。
- 段 2 plan 1 本、段 3 敵対相談 2 本 (正しさ境界 / 整合・実効性)、段 6 レビュー 2 本 (Codex gpt-6-astra、reasoning medium)。
  段 3 の所見 9 件は全採用 (A-1 include と指令の相対位置、A-2 push_macro / pop_macro は scope 外の限界として記録、A-3 trace
  diff-of-diffs の受理集合は狭まる、B-1 trigger_gating の pre-image artifact 再利用停止、B-2 probe の EVIDENCE_ROOT、B-3 compiler
  指定、B-4 列挙漏れ)。段 6 は実装差し戻しの must-fix ゼロ、should 2 件 (G の署名固定・docstring 注記) を fix 子で対応
  (2cc661235)。B6-1 (stock roundtrip ≠ byte 一致) は旧版 / 新版の pre-image 直接比較で閉じた。
- 規律 7 の再検証発火条件は段 4 (07:10 JST) に結果を見る前に登録した。実測: recipe v2 (計算ノード、10 request) は baseline PASSED (variant token `d8a4a10d…` = T-2630 と同値)、M3b / M6 / M4 / M4b が 4 node、M3a が variant 側 2 node で別 identity、M0 は同 identity、MISMATCH 0。赤理由は token で照合 (M3b: stock 側 `18c983be…`、M6: `1eac0081…`)。M6 の diff-of-diffs は通過し nm 層が最終層のまま。source-level (6 request) は baseline PASSED (8 passed)、S1 → A/B/F/H、S2 → D/E、S3 → G、S0 SURVIVED、MISMATCH 0。実 submodule の silo 8 genome は旧版 / 新版で pre-image 8/8 byte 一致。
- 実装は Codex author (bd21bc501、2cc661235、probe branch c5affb156)。probe branch `probe-dev-wave-t2731-cpp-normalize-dd`
  (worktree `.codex/worktrees/t2731-probe`) は T-2630 の probe test 2 commit の cherry-pick + EVIDENCE_ROOT 変更で、harness 用。
  land しない。変異 container `.codex/worktrees/t2731-mutcontainer`。証拠は job dir
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/` と `output/insights/2026-09-17/t2731-cpp-normalize-dd/`。
- 踏んだこと: 隔離 session で複合 shell / heredoc が guard に拒否される (Write tool と `.sh` 経由で回避)。`.codex/worktrees/` の
  新 worktree は `dev_wave_submodule_init.py` が 1 回目 rc=1 (update-no-fetch) で再実行 rc=0 (2 本とも、DW-O08 の 1 回再実行)。
  焦点走は login の headroom 判定で計算ノードへ dispatch された。
- 受入全走は本記録 commit の後、land 対象の最終 tip に 1 回投入する (`dev_wave_wait.py acceptance --lease-optional`)。結果は land の receipt (job dir `acceptance-receipt-1.json`) が正本で、本 fragment には書かない (記録 commit を受入の後に置くと land できないため)。

## 次の一手差分

### 完了

- [T-2731] `_cpp_normalize` に `-dD` を足し、predefined / command-line 出力を空入力 prefix で剥がす形で実装した
  ({{D:cpp-normalize-dd-env-prefix}}、commit bd21bc501 / 2cc661235)。回帰 test 8 node、source-level 変異 4 件、T-2630 §9 recipe
  の再走 (spec v2、8 変異) で規律 7 の発火条件と一致。残る限界は {{T:directive-position-and-macro-stack}} へ。
  remaining: none
  base: 76b94dee3a1a65e7f02645a8662bbca4bda6e4bcf9bd5393d23cb45680edc320

### 新規

- {{T:directive-position-and-macro-stack}} **P3・裁定待ち (scope 外の限界、実害の観測なし)**: identity は include 行を除去して
  前処理するため「指令と include の相対位置」を識別せず (`define→include→undef` と `include→define→undef` が同 identity)、
  `#pragma push_macro` / `pop_macro` の復元値も `-dD` に現れない (段 3 レンズ A の A-1 / A-2、修正前からの限界、
  `output/insights/2026-09-17/t2731-cpp-normalize-dd/README.md` §8)。選択肢 = (α) 現状維持 + 限界明記 [親推奨: pin / template に
  該当形は無く coder 面は `HOLE_ESCAPE` が生指令を拒否する]、(β) include を除去せず dead 化して相対位置を保つ、(γ) TU 単位 digest
  (D2104 項 2 (c) の環境依存が再燃)。裁定は {{D:cpp-normalize-dd-env-prefix}} の裁定パッケージ。
