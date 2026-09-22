# 段 1 brief — [T-2856] → [T-2857] silo-function-policy 軸の段階 C (2026-09-22、親 = Claude manager)

基準: wave worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2857-silo-policy-stage-c` (branch `worktree-dev-wave-t2857-silo-policy-stage-c`)。
起点 local main `8fd2a2f5c`、ccbench submodule `e9e477ca` (pin.CURRENT_PIN = `e9e477c`)。T-2856 の docs は wave 上で commit 済み `4c0eb08b9`。
T: は `external/ccbench/cc/silo/transaction.cc` (pin `e9e477ca` で親が行を実測)。設計の正本 = insight
`output/insights/2026-09-21/silo-function-synthesis-space/README.md` (以下「設計」)、採用判断 = `docs/decisions.md` の `## D2214.`。

## 研究前進と完了判定
- VLDB 方針 項 3 (LLM が関数単位でコードを書ける空間、正しさゲート不変) の最初の実証 (D 段の IR 偵察と ComSys 向け LLM×C++ 1 系列) を止めている前提が段階 C。
- 完了判定 = 設計 §9 の C 段出口 4 項を実測で満たす: (6) 軸 OFF の inert identity・軸 ON の honest identity・include 一致・diff-of-diffs、(7) 既存 3 負例を軸 ON 経路で 2 方策の下で再走し期待 verdict と完全一致、(8) probe build で 3 hook の発火・上限・再読込・prefix unlock・要因記録、(9) 契約負例が全て赤・検査段ごとの自己試験・UBSan harness 1 回。加えて手書き方策の生死確認 (build・verify 緑・honest identity)。
- 成果物影響 (DW-G05): 検査器か骨格が誤ると、この軸の後続 (D/E/F 段) の certified 選択が UB 入り候補・lock 漏れ骨格の上に立ち、報告の有効率・reject 分類・certified 数が意味を失う。

## scope (本題だけ)
- 内: 骨格 patch、api header (単一正本)、軸定数、型付き構文検査 (policy-C++ v1、設計 §2.7)、単独 TU compile、UBSan 単独 TU harness 1 回、probe build と焦点試験 (3 hook)、既存 3 負例の軸 ON 積み直し × 2 方策 (即 abort / 最大待機)、機構の変異 (設計 §3.3 の表)、契約負例 (構文・単独 TU・骨格 #error)、検査段ごとの自己試験、手書き方策の生死確認、各 test。
- 外: D 段 IR・E 段 driver / coder role / auditor 目録・`.claude/agents/`・p3_s4_loop の quarantine 分岐 (E 段)・新 reject 理由・per-worker 分布・候補ごとの sanitizer / TRACE 計数・PIN 前進・push・gate / 検査 / 台帳の一般化。

## 確定済み裁定 (攻撃対象外、ただし前提の誤りは指摘してよい)
- D2214 決定 1〜8 と「実装着手前の必須条件」、D2212 項 3・項 4 (計算 2 node 時間以上は投入前確認)、依頼文 (逐語 `verbatim/request.md`)。
- 依頼文: 計算は投入前に合計見積りを示してユーザー確認。正しさゲートは不変・規律 2 を緩めない。実装面は Codex author (D95)。

## 不変条件
- 軸 OFF (`SILO_POLICY_VARIANT=0`、既定) で領域・骨格・呼出し点が全て消え、stock と preprocess 一致 (src_token=stock)。既存 3 軸 (backoff・sort・trigger) の受理集合と identity を変えない。
- 規律 1: 方策・要因記録・待機器は両 build に載る CC 本来の状態、trace と被覆検査は `#if TRACE` のまま。既存 TRACE ブロックを新しい `#else` に巻き込まない (設計 §2.6)。
- 規律 2: 壊した負例・probe・機構変異のマクロは `CCBENCH_` 名前空間外で pipeline から定義不能。負例・変異の赤を「LLM 方策の anomaly」と数えない。
- submodule 本体・gitlink・pin・`source_digest` の EVOLVE_BLOCK_SOURCES / ALLOWLIST を変えない (骨格は patch のみ)。
- 計算ノード投入はユーザー確認後。CCBench の build は計算ノード (login の `cmake --build` は hook が拒否)。login は構文検査・単独 TU compile・UBSan harness (秒単位) だけ。

## 暫定裁定 (親の provisional、攻撃対象)
- (P1) 単位分割: A = 骨格 patch + api header + 軸定数 + 静的 identity test。B = 構文検査 + 単独 TU compile + UBSan harness + 契約負例・自己試験 test。C = probe patch・負例の軸 ON 版・機構変異 patch + coverage driver + 手書き方策 + 生死確認 driver + test。A を先に、B と C は A の api header / 骨格に依存して並列。
- (P2) 置き場: 軸定数 `orchestrator/campaign/axis_silo_function_policy.py` (命名は `axis_trigger_gating.py` 型)、構文検査は専用の新 module (`backoff_hole_grammar.py` の tokenizer の再利用可否は plan が判断)、api header は repo 内の単一正本 1 file で、骨格 patch 内の api block と byte 一致を test で検査。
- (P3) 骨格 patch `patches/silo-function-policy-variant.patch` は `cmake/Options.cmake` + `cc/silo/transaction.cc` の 2 file (trigger-gating 骨格と同型)。PIN を前進させない。
- (P4) 積み直しは trigger-gating の「骨格 → 計装 → 負例」3 段適用 (`s8a_trigger_coverage.py:358-364`) を型とする。既存 3 patch はそれぞれ lock ループ内側 (lockskip)・validation の abort 点 (norw、骨格が要因記録を足す行)・writePhase (early-unlock) に当たり、既存 patch の hunk 行番号は現行 T と一致しない (norw `@@ -385` に対し現行の該当は T:458 近傍)。既存 patch がそのまま軸 ON 経路に当たらない負例だけ、軸 ON 版の新 patch を作る。
- (P5) 新マクロ (`SILO_POLICY_VARIANT`・probe・機構変異・負例の軸 ON 版) は `condition_meaning_gate.py` の `_DEFINE_SPECS` (79 行〜) と `_CONDITIONAL_BRANCH_WITNESSES` (260 行〜) に登録し、閉集合 test (`test_condition_meaning_gate.py:3380` 近傍の `test_v1_domain_and_claim_boundaries_are_exact`) の期待集合を同時に更新する。「break が軸 ON の compile 経路に載っている証拠」を既存機構で取るための登録で、新しい gate ではない、と親は見る (代案: driver 内の preprocess 証拠)。DW-O13 に当たるので登録数を最小にする。
- (P6) 機構変異は設計 §3.3 の 8 走 (clamp 削除・再読込削除・上限削除・prefix unlock 省略・hook 配線解除 3・要因誤記録)。上限削除は検出を期待しない (検出力の主張に使わない)。束ね方 (1 patch に複数マクロ / 個別 patch) は plan が決める。
- (P7) 生死確認: 手書き方策 3〜4 本 (待機 0 + 即 abort、静的 5 µs / 10 µs、上限内 retry) と同 job の stock 対照を、build + legacy verify + 性能構成 verify + bench の既存経路 (`pipeline.evaluate`、`pipeline.py:2585`) か 100 行以内の driver で 1 回。性能値は同 job 対照つきの予備値として記録し、比較主張はしない。
- (P8) 計算の見積り単価は job Elapse の実測 (T-2844 の coverage driver 1 走 132 秒・焦点走 136 秒、受入 1 回 ≈ 0.25 node 時間、B-5 の 1 session 217〜510 秒)。合計見積りは段 4 後にユーザーへ示す。

## 実アンカー表
| 対象 | anchor |
|---|---|
| abort / 待機 | T:27-53 (`Backoff::backoff` T:47、`#if BACK_OFF` T:42) |
| begin (要因 reset) | T:55 |
| lockWriteSet | T:145-193 (内側ループ T:158-184、競合枝 T:160-167、CAS T:171-181、absent T:185-189、TRACE `clear_shadow` T:152・`record_lock` T:179) |
| 要因記録 7 点 | T:98 insert_node・T:162 lock_conflict・T:187 update_absent・T:458 read_tid・T:470 read_locked・T:481 node_validation・T:739 scan_node |
| validation / writePhase / commit | T:383- / T:557- / T:706-713 |
| flag | `external/ccbench/cmake/Options.cmake:20,27,28,60-63`、`external/ccbench/cc/silo/CMakeLists.txt:5-6` |
| 骨格の型 | `patches/silo-backoff-trigger-gating-variant.patch` (要因 store は patch 内 124〜194 行)、`orchestrator/campaign/axis_trigger_gating.py` |
| 積み重ね・probe の型 | `orchestrator/campaign/s8a_trigger_coverage.py:91,274,358-364,394`、`orchestrator/campaign/patchharness.py:174,204,247` |
| 既存 3 負例 | `patches/broken-silo-{norw,lockskip,early-unlock}-validation.patch`、`orchestrator/campaign/s2_verify_calibration.py:82-86`、`orchestrator/campaign/s3_lock_coverage.py:63-66,82-105,240-328` |
| define gate | `orchestrator/campaign/condition_meaning_gate.py:79-259,260-`、`orchestrator/tests/test_condition_meaning_gate.py:3380` |
| 構文検査・TU compile の前例 | `orchestrator/campaign/backoff_hole_grammar.py:360-454`、`orchestrator/campaign/sort_swo_oracle.py:113-114,2454,2538` |
| 検疫・effect gate・identity | `orchestrator/campaign/diff_quarantine.py:567,590-591`、`orchestrator/campaign/coder_effect_gate.py:114-115`、`orchestrator/campaign/source_digest.py:85-100,1647,2160,2205` |
| 評価経路・dispatch | `orchestrator/campaign/pipeline.py:147,169-215,2585`、`tools/pegasus/dispatch_compute.py:116` |

## 受入・実測環境
- 計算ノード: Pegasus (`python3 tools/pegasus/dispatch_compute.py --task generic ...`、所在は worklog エントリ 1818 と `docs/pegasus-runbook.md`)。焦点走・変異・受入も計算ノード。
- login: g++ 11.4.0 (親が実測)。構文検査・単独 TU compile・UBSan harness の秒単位の検査だけ。
