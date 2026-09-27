# 段 4 裁定 — [T-2866] + [T-2854] 残り (2) (2026-09-27 JST、親)

入力: brief.md、codex/s2-plan.md、codex/s3-consult-a.md (レンズ A)、codex/s3-consult-b.md (レンズ B)。裁定 inbox 再走査: 開始後の main 着地は rulings 第 38 回 (6740c511e) と fold のみ、本題への影響なし。

## 所見の裁定

| ID | 裁定 | 採否 / scope | 理由 |
|---|---|---|---|
| plan P1 修正 (evaluate は verify-first) | real | 採用 | 親が pipeline.py:702-708 と evaluate の順序を確認。現 pin の evaluate の実機到達点は build → trace → v2 reject の WAL、bench 未実行。 |
| A1 `_PreparedEvaluation` に workload 無し | real | 採用 (must-fix) | pipeline.py:1258-1275 に欄なし、`_run_bench` の measure_point 2 箇所 (:1442-1455) は保存済み perf だけを使う。放置時は v3 通過後の TPC-C bench に `-ycsb_tuple_num` が付き fitness が取れない。 |
| A2 / B2 bench の生死確認 | real | 採用 | driver から TPC-C perf binary へ `measure_point(workload_name="tpcc")` を 1 回直接呼び、argv・rc・tps を記録する。 |
| A3 records の二義化 | real (should) | 部分採用 | `measure_point` の records 位置の flag を workload ごとに `-ycsb_tuple_num` / `-tpcc_num_wh` に切り替える (plan 案) を採る。新しい測定型は作らない。代わりに、既存の `ycsb_tuple_num` 重複拒否 (pipeline.py:1410-1414) と同じ理由で、TPC-C のとき `perf.workload` に `tpcc_num_wh` を入れたら拒否する (gflags last-wins の無言上書き防止。既存防壁の対称形であり新しい gate の一般化ではない)。PerfConfig の docstring に「records は YCSB では行数、TPC-C では倉庫数」と書く。bench の WAL / 受領証に workload を示す既存 field (receipt_workload_tag 等) があればそれで足り、無ければ TPC-C のときだけ workload 名を載せる (ycsb の bytes 不変)。 |
| A4 probe の可視性 | real (should) | 採用 (実機確認) | driver で既知 TPC-C PID が見える状態で `_probe("tpcc")`=False、終了後 True、driver 自身の argv に `tpcc_.*\.exe` を含めない。可視性が示せなければ合格と書かない。コード修正は欠陥が出た場合だけ。 |
| A5 実 verifier と source root の正例 | real | 採用 | 実行器の TPC-C 正例は合成 v3 trace を実 `verify_trace_dir` に通し、trace を作った source root で certified、root なし / 不正で certified にならない。verifier の fixture 差し替えで certified を作る正例は不可 (F649)。 |
| A6 / B1 YCSB bytes 不変と v1/v2 両 API | real | 採用 | `build()` と `build_v2()` の両方に通す (evaluate は env_contract の有無で使い分け、pipeline.py:2027-2053)。ycsb の cache key・bdir 名・v2 preimage・compiler manifest・argv は既存の golden と一致すること、ycsb↔tpcc の相互 hit が起きないことを test で固定する。 |
| A 「cell.flags は int」/ B4 | real (brief の誤り) | 採用 = 文字列化の差分と専用 test を削除 | `_cell` (t2851_transfer_runner.py:48-50) が全値を str 化済み。親 brief の実測の一般化ミス (dict literal だけ見て `_cell` を読まなかった)。 |
| A: `vr.certified` の認定面は X/P の二面 | real (brief の誤り) | 記録 | brief の「X/P/I 三面」は不正確。insight に正しく書く。 |
| A: 事前登録 §3.3 の解禁 | real | 記録 | 本 wave は留保 cell を解禁しない。解禁は発効の決定で段と認定経路を記録する (activation の既存検査、:268-273)。 |
| B3 run_once 置換はしない | real | 採用 | 既存 measure_point を局所変更。`capture_measure_point` は measure_point が経由する場合だけ同じ変更。 |
| B5 run_campaign は workload を渡さない | real | scope 外・記録 | 本 wave の「campaign で評価できる」は campaign の評価単位 `pipeline.evaluate` (build・verify・bench・flag の受け渡し) までとする。loop / run_campaign の verify mode 選択・TPC-C の calibration (calibrator/cli.py:416 の ycsb 固定を含む) は TPC-C の探索設計 (事前登録 §10 が閉じないもの) に属し、insight と carry に残す。plan の `search_config.workload` の production 記録は入れない (driver の独立 layout 内だけ)。 |
| B6 run_job の 32 block | real | 採用 (full job を維持) | run_job に縮小 mode を足すのは追加実装。前 wave の YCSB 錨 job は build 込みで Elapse 351 秒。TPC-C も同程度と見込み、2 node 時間を大きく下回る。smoke は R1 を固定した動作確認で、事前登録の測定ではないと記録する。 |
| B7 test の最少化 | real | 採用 | 層ごとに最少本数。既存の拒否 test は弱めない (s1-H の「経路なし」test は s2 と s1 非 57:43 へ移す)。 |
| B8 calibrator/cli.py | real | 触らない・記録 | |
| B9 critic 説明文 | real | 採用 | reason 集合は不変、説明文だけ。 |
| P3 (v2 → indeterminate、anomaly / 非 serializable は disqualified 優先) | — | 維持 | 両レンズとも維持。 |

## plan v2 (実装の正本)

単位 A (所有: `orchestrator/campaign/buildcache.py`、`orchestrator/tests/test_buildcache.py`、`orchestrator/tests/test_buildcache_v2.py`)
- `build()`・`build_v2()`・`_build_v2_impl()`・`_v2_commands()`・`cache_key()`・`_v2_identity()`・再現コマンド生成に keyword `workload: str = "ycsb"` を通す。値は exact str の `"ycsb"` / `"tpcc"` だけ、他は ValueError。
- target は 1 箇所で `f"{workload}_{genome.protocol}.exe"` を作り、configure/build argv、binary relpath、hit 時の compiler target、fresh 時の収集・検証、legacy build、再現コマンドの全てで使う。
- legacy key の raw 末尾へ tpcc のときだけ `|workload=tpcc`。v2 preimage は tpcc のときだけ `"workload": "tpcc"`。ycsb の bytes は不変。
- test: ycsb の key / bdir / v2 digest が変更前の golden と一致、tpcc の key / digest が ycsb と異なる、tpcc の target・binary path、tpcc の fresh→hit で compiler manifest が再検証される、ycsb 行を tpcc 要求で hit しない (逆も)、不正 workload の拒否。

単位 B (所有: `orchestrator/campaign/pipeline.py`、`orchestrator/calibrator/runner.py`、`orchestrator/critic/digest.py`、`orchestrator/tests/test_campaign.py`、`orchestrator/tests/test_calibrator.py` (実在の calibrator test file 名を確認)、`orchestrator/tests/test_critic.py`)
- `evaluate(..., *, workload: str = "ycsb")` → `_prepare_evaluation_core` → `_build_one` の v1/v2 両呼び出しへ `workload=`。`_PreparedEvaluation` に workload を保持し、通常 bench と screening の `_run_bench` 呼び出しの両方から `measure_point(..., workload_name=...)` へ通す。
- `calibrator/runner.py` の `measure_point` / (経由するなら) `capture_measure_point` に keyword `workload_name: str = "ycsb"`。records 位置の flag を ycsb → `-ycsb_tuple_num=`、tpcc → `-tpcc_num_wh=` にし、ycsb の argv は bytes 不変。
- `_run_bench` で TPC-C のとき `perf.workload` に `tpcc_num_wh` があれば既存 `ycsb_tuple_num` 拒否と同形で拒否。PerfConfig の docstring 更新。PerfConfig の field は増やさない。
- TPC-C の correctness は caller が `CorrectnessWorkload` を渡す。入口の新しい拒否は足さない (未指定なら YCSB の既定 flag になり、既存 `_run_trace` が tpcc binary を `trace-witness-unsupported-workload` で拒否する。fail-closed は既存経路で成立)。`performance_correctness_workload` は変えない。
- `digest.py:1336-1337` の説明文を「commit witness 契約・v3 契約を満たさない workload または TPC-C の構成・trace (YCSB 以外、TPC-C 段 1 の 57:43 以外、v2 trace の TPC-C)」の趣旨へ。reason 文字列・登録集合は不変。
- test: tpcc の evaluate が v2 trace で WAL reject・bench 未起動、v3 trace で bench に到達し argv に `-tpcc_num_wh` があり `-ycsb_tuple_num` が無い (実 `_bench_prepared` 経由)、tpcc で `_build_one` が tpcc target を要求する、`perf.workload` の `tpcc_num_wh` 重複を拒否、measure_point の ycsb argv 不変と tpcc argv、critic の説明文。

単位 C (所有: `orchestrator/campaign/t2851_transfer_runner.py`、`orchestrator/tests/test_t2851_transfer_runner.py`)
- `verify_candidate` の早期 return を「tpcc かつ (stage != "s1" または 4 比率 flag が 43/0/0/0 でない)」に限定し reason「認定経路なし」は維持。s1 の 57:43 cell は YCSB と同じ `_binary` → `trace_runner` → `_trace_witness_ok` → `verifier(..., ccbench_root=trace_ccbench_root)`。flags はそのまま (既に str)。
- verifier 後、tpcc で `vr.integrity.existence_violation_details is None` (v2) なら reason `trace-witness-unsupported-workload`、`verification_status(..., certified=False)` (anomaly / 非 serializable は disqualified が先)。v3 (list) のときだけ `vr.certified` を使う。TPC-C の verifier 記録は `result_to_dict_v3`、YCSB は既存 `result_to_dict` のまま。
- test: s2 と s1 非 57:43 は trace を呼ばず「認定経路なし」、s1-H で実 verifier + 合成 v3 trace + 正しい source root で certified、source root なしで certified にならない、v2 は indeterminate、anomaly は disqualified、witness 失敗は indeterminate。既存の `test_verify_tpcc_anchor_is_indeterminate` は s2 / 非 57:43 側へ書き換え (弱めない)。

単位 D (repo 外の使い捨て driver、Codex author。子の木の `scratch/` に書かせ親が job dir へ退避、commit しない)
- 計算ノード 1 job。依存は `tools/pegasus/p3_s4_loop_pegasus.sh:617-673` と同じ source / pin から gflags・glog を `$TMPDIR` に入れ、`dependency_prefix` / `CMAKE_PREFIX_PATH` で渡す (値は既存 policy から読む)。
- R0 / R1 (前 wave と同じ silo genome) を production の buildcache (`build_v2` を優先、必要な context が揃わなければ `build`) で `workload="tpcc"` の perf (TRACE=0) / trace (TRACE=1) に build。
- 実行器: freeze → 錨 `s1-H-base` の `run_job` 1 本 → `verify_candidate(R1)` 1 本。留保 cell は選ばない。
- bench: R1 の perf binary に `measure_point(workload_name="tpcc", records=1, threads=48, extime=3, reps=1, workload={s1 の 4 比率と tpcc_interactive_ms})` を 1 回。
- evaluate: 独立 layout で `pipeline.evaluate(..., workload="tpcc", correctness=s1-H 錨 flags)` を R1 genome 1 件。期待 = v2 reject の WAL、bench 未起動。
- 単独性: driver 自身の argv に `tpcc_` を含めない。既知の tpcc 実行中 (`run_once` を別 thread / subprocess で起動中) に `_probe("tpcc")`=False、終了後 True、pgrep の rc・stdout・driver PID の argv を記録。
- 全記録を JSON で出力 dir へ (create-only)。見積り 30〜60 分 (2 node 時間未満、ユーザー確認不要)。

## 変異の事前登録 (段 6 で実施、位置と単一理由性は実装後に確認)

| ID | 対象 | 変異 | 殺すべき test (実装後に nodeid 確定) |
|---|---|---|---|
| M1 | pipeline | `_bench_prepared` / `_run_bench` へ workload を渡さない (ycsb 既定に落ちる) | v3 の tpcc evaluate が bench argv に `-tpcc_num_wh` を持つ test |
| M2 | pipeline | `_build_one` が workload を buildcache へ渡さない | tpcc evaluate が tpcc target を要求する test |
| M3 | calibrator | tpcc でも `-ycsb_tuple_num` を出す | measure_point の tpcc argv test |
| M4 | calibrator | ycsb の flag 順または形を変える (ycsb bytes 不変の保護) | measure_point の ycsb argv golden test |
| M5 | buildcache | v2 preimage に workload を入れない | tpcc と ycsb の v2 digest が異なる test |
| M6 | buildcache | legacy cache_key に workload を入れない | tpcc と ycsb の legacy key が異なる test |
| M7 | buildcache | hit 時の compiler target を ycsb 固定に戻す | tpcc の fresh→hit manifest 再検証 test |
| M8 | buildcache | ycsb でも preimage に workload を入れる | ycsb の v2 digest golden test |
| M9 | runner C | v2 判定を外す (tpcc も `vr.certified` を使う) | v2 は indeterminate の test (実 verifier) |
| M10 | runner C | tpcc の verifier へ `ccbench_root` を渡さない | 実 verifier + source root の certified 正例 |
| M11 | runner C | 早期 return の条件から比率判定を外す (s1 非 57:43 も trace へ) | s1 非 57:43 が trace を呼ばない test |
| M12 | runner C | 早期 return を元に戻す (s1 57:43 も経路なし) | s1-H の certified 正例 |
| M13 | runner C | anomaly のある v2 を indeterminate にする | v2 anomaly は disqualified の test |
| M14 | pipeline | TPC-C のとき `perf.workload` の `tpcc_num_wh` 重複拒否を外す | `tpcc_num_wh` 重複の拒否 test |
