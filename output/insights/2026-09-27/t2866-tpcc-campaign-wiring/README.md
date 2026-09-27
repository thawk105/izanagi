# [T-2866] と [T-2854] 残り (2) — TPC-C の候補を campaign の評価単位で build・評価する配線と、転移実行器の TPC-C 段 1 検証の認定経路への接続 (2026-09-27)

authority: none / default_effect: no-state-change (記録。可変状態の正本は worklog 末尾と現行 phase doc)

## 0. 何をしたか・主張しないこと

依頼 (T-2866 と T-2854 残り (2)) のうち、次をコード + test にした (Codex author、D95)。統合 commit `2bb35c7a4`、fix `724088a08`。

| 面 | 変更 |
|---|---|
| build (`orchestrator/campaign/buildcache.py`) | `build()`・`build_v2()` ほかに `workload` (`ycsb` / `tpcc`、既定 `ycsb`)。target・binary path・compiler input の target を `<workload>_<protocol>.exe` の 1 箇所から作る。legacy key と v2 preimage は tpcc のときだけ workload を足し、ycsb の bytes は変えない |
| 評価 (`orchestrator/campaign/pipeline.py`) | `evaluate(..., workload=)` を build と、保持した準備状態 (`_PreparedEvaluation`) 経由で通常・screening の bench へ通す。TPC-C の `perf.workload` に `tpcc_num_wh` を入れたら既存の `ycsb_tuple_num` 拒否と同形で拒否。bench / commit payload に `workload` key は足さない (受入の赤を受けて取り下げ、§1) |
| 測定 (`orchestrator/calibrator/runner.py`) | `measure_point` / `capture_measure_point` の `workload_name` で件数 flag を `-ycsb_tuple_num` / `-tpcc_num_wh` に切り替える (ycsb の argv は不変) |
| critic (`orchestrator/critic/digest.py`) | `trace-witness-unsupported-workload` の説明文を TPC-C の v2 reject と 57:43 以外に合わせた (reason は不変) |
| 転移実行器 (`orchestrator/campaign/t2851_transfer_runner.py`) | TPC-C は段 s1 の 57:43 cell だけ trace → witness → 実 verifier → v3 要求 (D2238 項 3 と同じ判定) へ通す。v2 は未確定 (anomaly・非直列化は失格が優先)、s2 と s1 の非 57:43 は「認定経路なし」のまま |

**主張しないこと:** TPC-C の certified、認定の本測定、pin 前進 (D297 規則 v2 は別 wave)、留保 cell の走行 (0 走)。campaign の探索 loop (`loop.run_campaign` の verify mode 選択、TPC-C の calibration、`calibrator/cli.py:416` の `ycsb_<protocol>.exe` 固定) は TPC-C の探索設計 (事前登録 §10 が閉じないもの) に属し、今回は触っていない。「campaign で評価できる」は campaign の評価単位 `pipeline.evaluate` までを指す。

`_run_trace` の受理 (57:43、文字列一致) と verifier 後の v3 要求 (D2238) は変えていない。現 pin の tpcc binary は v2 を出すので、実機では検証と evaluate がこの既存経路で拒否される (§3)。

## 1. 段の経過

- 段 1 brief (`verbatim/brief.md`)、段 2 plan (`verbatim/s2-plan.md`)、段 3 相談 2 本 (`verbatim/s3-consult-a.md` 正しさ境界・整合、`verbatim/s3-consult-b.md` 過剰・削除)、段 4 裁定 (`verbatim/s4-ruling.md`、plan v2 と変異 M1〜M14 の事前登録)。
- 親 brief の誤り 2 点を相談が反証した: 「実行器の `cell.flags` は int」(実際は `_cell` が全値を str 化済み。文字列化の差分は作らなかった)、「認定面は X/P/I の三面」(認定 gate は X/P の二面)。
- 段 5: 実装子 3 本 (単位 A buildcache / B pipeline・calibrator・critic / C 実行器 + 使い捨て driver D、所有 path 素集合)。子の sandbox は qstat を拒否するため子は pytest を実走できず、親の焦点走で確認した。
- 段 6: 焦点走 1 回目 12 赤 (2,753 passed)。1 件は新 test が見つけた実欠陥 — `_prepare_evaluation_core` の `for tag, workload, fullscale_isolated in passes:` が引数 `workload` を CorrectnessWorkload で上書きし、v3 を通った TPC-C 候補の bench が落ちる。11 件は `_PreparedEvaluation` を直接作る既存 fixture が新しい必須 field を渡していない取り残し。
  review 2 本は両 NO-GO (`verbatim/s6-review-a.md`、`verbatim/s6-review-b.md`)。裁定 1 (`verbatim/s6-ruling-1.md`) で fix 1 巡 (pipeline・fixture) と driver の fix。焦点走 2 回目 2,765 passed・5 skipped (HEAD `724088a08`)。焦点再レビュー (`verbatim/s6-focus1.md`) は F1・RA1・RA3 closed、driver 系は実機で確かめるまで partial、新規 FA1 (driver の evaluate が `numactl` を渡さず認可ゲートで必ず拒否) → driver fix 2。
- 計算ノードの生死確認で driver が 2 回、production の build 入口検査に落ちた (§3)。driver を production の job body と同じ形に揃えて 3 回目で全項目が期待どおりになった。
- 受入 attempt 1 (tested main `19d3f2bae`、tip `73197863c`) は 1 failed / 27,882 passed / 74 skipped。赤は `test_layer3_report.py::test_run_bench_ast_assignments_exactly_match_declared_payload_keys`
  (bench payload の条件付き key が 4 → 5)。本 wave に帰属: 統合 commit が bench payload に `workload` を足したが、親は private symbol `_BENCH_DONE_*_PAYLOAD_KEYS` の consumer である
  この test を焦点走の集合に入れていなかった (DW-O26 の symbol grep の漏れ)。裁定 2 (`verbatim/s6-ruling-2.md`) で bench・commit payload への `workload` 追加を取り下げた
  (既存の `run_cmd` と build 記録で識別でき、WAL の `workload` key は検証記録の `{"tag": ...}` と二義になる)。fix `3b95bf8b6` (Codex author) の後、変更した private symbol の
  consumer test 44 file と inventory 群の焦点走 3 回目は 5,716 passed・20 skipped (HEAD `d8d337e7b`)、変異 final も同 HEAD で再走した (§2)。

## 2. 変異 matrix

`tools/mutation_worktree.py` を独立 clone (D1009、main を `724088a08` に固定) で `--runner-mode dispatch` で 2 回走らせた。対象 test は
`test_buildcache_v2.py`・`test_calibrator.py`・`test_campaign.py`・`test_t2851_transfer_runner.py` の `-k "tpcc or workload"` (23 node)。
1 回目は全件 SURVIVED 期待の dispatch probe で観測 node を集め (DW-M08 の初回 probe)、2 回目はその node を期待とした final。spec と要約は `evidence/mutation-spec-final.json`・`evidence/mutation-summary.json`。

| 回 | spec sha256 | baseline | 結果 |
|---|---|---|---|
| probe | `1b14c268a2663a3b057c6dd5998d458869803a53dde151fe005ed8546dfc2b7c` | PASSED | M1〜M14 すべて失敗 node あり (probe では期待が SURVIVED なので MISMATCH と表示)、M15 SURVIVED |
| final | `c6c04783c29fb3b0f2ee2ae4bb4001438e2fa5414397df202cc7049c342a451d` | PASSED | M1〜M14 すべて KILLED、M15 SURVIVED、期待との一致 15/15 (対象 `724088a08`) |
| final 再走 | 同上 | PASSED | 受入の赤を受けた fix (`3b95bf8b6`) の後の `d8d337e7b` で同じ spec を再走。M1〜M14 すべて KILLED、M15 SURVIVED、一致 15/15 |

| ID | 変異 | 殺した test |
|---|---|---|
| M1 | `_bench_prepared` が bench へ workload を渡さない | `test_campaign.py::test_tpcc_evaluate_v3_reaches_bench_with_workload` |
| M2 | `_build_one` の v2 build が workload を渡さない | `test_campaign.py::test_tpcc_evaluate_v2_aborts_before_bench_and_builds_tpcc[v2-build]` |
| M3 | tpcc でも `-ycsb_tuple_num` を出す | `test_calibrator.py::test_measure_point_workload_record_flags_preserve_ycsb_argv[direct/deferred]`、`test_tpcc_evaluate_v3_reaches_bench_with_workload` |
| M4 | ycsb の件数 flag の形を変える | `test_measure_point_workload_record_flags_preserve_ycsb_argv[direct/deferred]` |
| M5 | v2 preimage が workload を無視 | `test_buildcache_v2.py::test_workload_identity_preserves_ycsb_golden_and_separates_tpcc`、`test_tpcc_fresh_hit_compiler_target_and_cross_workload_misses` |
| M6 | legacy key が workload を無視 | 同 golden test、`test_legacy_tpcc_target_and_cross_workload_misses` |
| M7 | cache hit の compiler target を ycsb 固定 | `test_tpcc_fresh_hit_compiler_target_and_cross_workload_misses` |
| M8 | ycsb でも preimage に workload を入れる | `test_workload_identity_preserves_ycsb_golden_and_separates_tpcc` |
| M9 | 実行器の v2 判定を外す | `test_t2851_transfer_runner.py::test_verify_tpcc_s1_real_verifier_v3_v2_and_witness` |
| M10 | tpcc の verifier へ source root を渡さない | 同上 |
| M11 | 早期 return の比率判定を外す | `test_verify_tpcc_anchor_is_indeterminate[s1-s1-H-pay20]` |
| M12 | 早期 return を元に戻す (s1 57:43 も経路なし) | `test_verify_tpcc_s1_real_verifier_v3_v2_and_witness` |
| M13 | v2 の anomaly を未確定にする | 同上 |
| M14 | `tpcc_num_wh` の重複拒否を外す | `test_campaign.py::test_tpcc_bench_rejects_duplicate_warehouse_flag` |
| M15 (等価) | target 名の書式を `%` 形式へ (生成文字列は同じ) | なし (SURVIVED 期待どおり、harness の SURVIVED 検出の正例) |

M9・M10・M12・M13 は同じ複合 test の別 assertion で落ちる (実 verifier・合成 v3 trace の正例と、source root なし・v2・anomaly の負例を 1 本にまとめた test)。
変異ごとに落ちた assertion は別で、単独の test 名だけでは理由を区別しない。probe の 1 走 (M3) は計算ノードの Pre-running が 18 分続いたが、qdel せず自然に解消した。

## 3. 計算ノードでの生死確認 (錨 s1-H-base だけ、留保 cell は 0 走)

使い捨て driver (repo 外、Codex author、commit しない)。wave commit `724088a08`、CCBench `68106660`、Pegasus gen_S。

| 回 | request | driver sha256 | 結果 | 原因 / 所見 |
|---|---|---|---|---|
| 1 | 31859.nqsv | `8c80aa84…` | rc=1、Elapse 32 秒 | `build_v2` が「v2 toolchain manifest が caller の事前観測と不一致」。driver が manifest を site 既定の `gcc`/`g++` で観測し、build には依存準備 policy の compiler path を渡していた → production (`pipeline.py` の `_compilers_for_current_site()`) と同じ選択へ |
| 2 | 31867.nqsv | `a6f1e567…` | rc=1、Elapse 38 秒 | `build_v2` が「FetchContent dependency の実効 source root が期待値と不一致」。受領証付きの build は masstree の実効 source が `<fetchcontent_base>/masstree-src` であることを要求するが、driver は依存準備の別 path を渡していた → `tools/pegasus/p3_s4_loop_pegasus.sh:675-790` と同じく third-party を `<fetchcontent_base>/<名>-src` へ複写 |
| 3 | 31897.nqsv | `1ab39faf…` | rc=0、Elapse 374 秒 | 期待照合の不一致 0 (`evidence/smoke3-summary.json`) |

3 回目の記録 (`evidence/smoke3-*.json`):

- **build:** production の `buildcache.build_v2(workload="tpcc")` で silo の R0 (BACK_OFF=1) と R1 (BACK_OFF=0) を perf (TRACE=0) / trace (TRACE=1) の 4 本 build。出力は `cc/silo/tpcc_silo.exe`。R1 perf sha256 `576b7b50…`、R1 trace sha256 `3a9919e3…` (全値は `evidence/smoke3-freeze.json`)。
- **実行器の job:** 錨 `s1-H-base` (倉庫 1・48 thread・Payment 43・他 3 取引 0・think 0・extime 3 s) の cohort 1 の 1 job。bnode018、32 block 完走、単独性は開始・終了とも成立、next_action none。平均 tps R0 192,615.2 / R1 270,916.4 (min–max R0 187,347–196,282、R1 269,073–272,033)。smoke は R1 を固定した動作確認で、事前登録の測定ではない。
- **実行器の検証 (R1):** `indeterminate`、reason `trace-witness-unsupported-workload`。verifier は serializable・cycle 0 だが v2 trace なので certified に数えない (現 pin は v2)。
- **bench の直接確認:** `measure_point(workload_name="tpcc")` の argv は `-thread_num=48 -tpcc_num_wh=1 -extime=3 ...` で `-ycsb_tuple_num` を含まない。rc=0、271,626 tps。
- **pipeline.evaluate (R1、独立 layout):** WAL は build_start → build_done → abort (`trace-witness-unsupported-workload`、note「v3 trace でない TPC-C workload (legacy) → reject」)。bench は起動せず COMMIT なし。
- **単独性:** 同じ時点で composite probe (ycsb canary) は passed。TPC-C perf binary の実行中は `pgrep -af tpcc_.*\.exe` に既知 PID が出て `_probe("tpcc")` = False、終了後は pgrep rc=1 で True。driver 自身の cmdline に `tpcc_` を含まない (`evidence/smoke3-probe.json`)。
- **source root:** freeze の `trace_ccbench_root` は build 用の一時 checkout で、終了時に消える。pin・HEAD・clean status と再取得手順を `evidence/smoke3-source.json` に残した。

所要: 3 回の job Elapse 合計 444 秒 (32 + 38 + 374)。焦点走 2 回と変異走は別 (§2、§5)。D2212 項 4 の確認ライン (2 node 時間) 未満。

### 3.1 範囲外の所見 (記録のみ)

- **取引別の commit / abort 件数が出ない:** 現 pin の perf binary の stdout は `Details per transaction type:` の下が空で、実行器の `parse_tpcc_counts` は None を返した (`evidence/smoke3-job.json` の `transaction_counts`)。TPC-C 版事前登録 §5 は 1 走で取引別件数も記録すると定める。出力源 (計数修正 C1 は trace build 限定) の確認は発効束の項目になる。
- **倉庫 1・48 thread で `insert order failed` が多数出る:** 単独性 probe の 20 秒走の stdout 末尾に各 thread の行がある (`evidence/smoke3-probe.json` の `child_stdout_tail`)。TPC-C 仕様との差 (設計 README §9) か負荷由来かは切り分けていない。
- **production の compute build の前提:** 受領証付きの `build_v2` は、caller が (a) manifest の観測と build で同じ compiler を使い、(b) third-party を `<fetchcontent_base>/<名>-src` に複写しておくことを要求する。production の job body は両方を満たしているが、使い捨て driver が自前で揃えないと入口検査で必ず落ちる。

## 4. [T-156] の発火条件の再評価

T-156 は「TPC-C の候補を campaign が評価する wave で改めて判断する」としていた。本 wave で `pipeline.evaluate` が TPC-C の候補を build し検証へ通せるようになったが、現 pin では v2 で拒否され、TPC-C の探索 loop (8b の descriptor を使う段) も未配線である。
8b descriptor の拡張を設計する段に至っていないので着手しない。既裁定の順序 (着手前に workload 別の set-size 分布を測る) は維持し、TPC-C の探索 loop を配線する wave で再評価する。

## 5. 記録前の機械走査

`python3 -m orchestrator.campaign.s8b_holdout_freeze search` は rc=1。hit は rr80・rr20 とも
`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` の既存 3 file (journal.jsonl・manifest.json・result.json) だけで、
本 wave の file (本書・verbatim・evidence・spool fragment・変更 source と test) は hit に含まれない (前 wave の insight §5 と同じ既存の記録)。

`verbatim/s6-review-b.md` は `git diff --check` に抵触する行末空白 (Markdown の改行用の 2 空白) を 3 行目と 4 行目から 2 個ずつ除いた可逆な最小正規化である (可視文字は不変)。
原文は sha256 `65d3c48a2de1150bd8a12dc6edad38a3999e4f895d8f7796b92b98127db1b2c3`・2,130 bytes、正規化後は 2,126 bytes。復元は 3・4 行目の行末に半角空白 2 個を戻す。

## 6. 残るもの

- TPC-C の探索 loop への配線 (`loop.run_campaign` の workload、verify mode、TPC-C の calibration、`calibrator/cli.py:416`)。TPC-C の探索設計と一緒に行う。
- pin 前進 (C2'、D297 規則 v2 の実装 wave の後) で v3 を出す binary になれば、同じ経路で certified に届くかを実機で確かめる。
- 発効束: 取引別件数の出力源 (§3.1)、s1 の 57:43 以外の留保 cell (pay20 / pay70) は D2238 の受理外で「認定経路なし」のままであること。
