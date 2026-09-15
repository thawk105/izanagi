## 不変リストの実測

**不変条件の破壊は見つかりませんでした。［refuted / nit：修正不要］**

比較基準は変更前 HEAD。改行を保持したバイト比較で、差分は次の3箇所だけでした。提示された patch も実際の差分と完全一致しました。

- script：旧10–11行 → 新10–24行のコメント。
- script：旧774行 → 新787–806行の formula 文字列。
- test：旧212–213行 → 新212–239行の pin。

これ以外の空白・改行・encoding の変更はありません。

| 不変対象 | 実測結果 |
|---|---|
| `frozen_required_s` | 代入式はバイト一致。`10 + 1200 + 5 * 3 * 120 + 10 * 120 + 2 * 3 * 120 + 1080 + int(reserve_s)` に600を代入して **6610** |
| PBS directive | `#PBS -l elapstim_req=02:00:00` のまま |
| 両 policy | ファイル全体が HEAD とバイト一致。`certify_walltime="02:00:00"`、`certify_walltime_s=7200` |
| wrapper の reserve | policy の `finalize_reserve_s=600` と、その読み取り・変数への代入が不変 |
| timeout | **19記述箇所すべて不変**。qstat 30、probe 各120、gflags 各60、glog 各120、copy 120×3、pristine検証120、configure/build各900、hash/nm各60、perf各10、post-probe120 |
| outer timeout | `--signal=TERM "$remaining"`、`remaining=DEADLINE_EPOCH-now-FINALIZE_RESERVE_S` が不変 |
| 標本数 | 1m→16mの倍増による最大5点、sweep 3回、noise 10回。CLI既定値とwrapper argvが不変 |
| cooldown | load1≤1.0、30秒間隔、3回連続、上限1200秒。関数全体が不変 |
| `cli.py` | **51,035 bytes 全体一致** |
| 過去 receipt | HEAD管理下の **335ファイルすべて** Git blob とバイト一致 |

CLI内部の `FINALIZE_RESERVE_S=60` も従来どおりです。wrapper側の600とは別の予約項です。

**成果物影響：** 予約値・標本数・timeout・既存台帳の値を変更する差分はありません。

## 受理集合の不変

**受理条件変更の疑いは反証されました。［refuted / nit：修正不要］**

[cli.py:707](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2563-impl/orchestrator/calibrator/cli.py:707) の `_acquisition_reasons` は、以下の全条件と例外処理がバイト一致しています。

| 条件 | 変更前後 |
|---|---|
| job ID | 正規化した qsub request ID と PBS job ID を比較 |
| host | `assigned_host_qstat != hostname_observed` |
| nodes | `qsub["nodes"] != 1` |
| binary | receipt の SHA と実測 SHA を比較 |
| `reservation-mismatch` | `reserve_s <= 0` または `budget["required_s"] + walltime["reserve_s"] > walltime["required_s"]` |
| `reservation-qsub-mismatch` | `walltime["required_s"] > qsub["elapstim_req_s"]` |
| known values | passed、CPU名、physical cores、affinity、HT無効、SMT無効の全条件 |
| effective clock | 同じ自己比較関数による判定 |
| 不正入力 | 同じ `KeyError / TypeError / ValueError` を `receipt-invalid` に変換 |

既定入力の時間条件は **4990 + 600 ≤ 6610 ≤ 7200** のまま。裁定の6点例も **5350 + 600 = 5950 ≤ 6610** で変わりません。

`finalize_reserve\((\d+)\)` の実測結果は次のとおりです。

- コメント10行：600、1件。
- formula 787行：600、1件。
- 合計2件、集合 `{600}`。600以外は0件。

**成果物影響：** 同じ取得事実・予算入力に対する受理／拒否判定は不変です。formula はこの判定関数から参照されません。

## pin の強さ

**検出力低下・循環比較の疑いは反証されました。［refuted / nit：修正不要］**

[test_pegasus_tools.py:212](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2563-impl/orchestrator/tests/test_pegasus_tools.py:212) は、実装から期待値を生成せず、独立した文字列リテラルで代入式全体とformula全体を固定しています。

新旧sourceをメモリ上で変更し、それぞれの実際のpinリテラルとの包含関係を評価しました。

| productionだけへの変異 | 旧pin | 新pin |
|---|---|---|
| 代入式の1080→1081 | 検出 | 検出 |
| 代入式の120→121 | 検出 | 検出 |
| formulaの配分1080→1081 | 検出 | 検出 |
| formulaの合計6610→6611 | 検出 | 検出 |
| 新しい完遂保証の限定節を削除 | 対象節なし | 検出 |
| コメントのreserve 600→599 | 別のreserve検査で検出 | 同じ検査で検出 |

旧pinが守った数式断片は新しい代入式pinに含まれ、旧build項に対応する新配分項はformula全体pinが守ります。**今回の置換によって検出できなくなった誤変更は確認できませんでした。**

ただし限定節削除は、旧sourceでは変更自体が起きません。これは新文面の診断感度の確認であり、変異killの実証ではありません。source内の包含検査という既存方式の限界も残ります。

**成果物影響：** productionの数値・説明を単独で誤変更した場合の検出力は維持され、新しい限定文も検査対象になります。

## 規律 1・2

**規律を緩める変更はありません。［refuted / nit：修正不要］**

- 全protocolの `-DCCBENCH_TRACE=0` が不変。
- wrapperの `nm -C`、空のsymbol table拒否、`izanagi_trace` 検出時の終了が不変。
- CLIのnm起動不能・非ゼロ終了・trace symbol検出時の停止が不変。
- `--effective-clock-tolerance-pct` は追加されず、旧環境変数入力の禁止も不変。
- certifyでの `require_all_reps=True`、`require_complete_metrics=True`、実行異常・timeout・必須指標欠落時の例外経路が不変。
- 品質判定のreasonがあればrejectedとする条件も不変。関連する `runner.py`・`sweep.py`・`report.py` もHEADとバイト一致。

**成果物影響：** trace有効binaryや異常標本を新たに認定へ通す経路は増えていません。

## 所有外への波及

**文字列変更による所有外テストの破損は静的には見つかりませんでした。［refuted / nit：修正不要］**

| 参照元 | 現物で確認した読み取り関係・判定 |
|---|---|
| `test_pegasus_tools.py` | script直接読込、PBS解析、文字列pin、アンカーで抽出した断片、fixtureコピー。変更したpin以外の検査条件・抽出アンカーは維持 |
| `test_ccbench_spawn_sites.py:871` | `_production_build_sources()` が `tools/pegasus` を走査し、shellのcmake build箇所を抽出。3つのbuild箇所は行番号が13増えるだけ。このscriptの行番号を固定する期待値はない |
| `test_official_perf_closure.py:536` | production sourceからperf条件のあるファイルを発見。追加説明文はshell条件パターンに該当せず、既存perf条件も不変 |
| `test_pegasus_calibration_workload.py` | `JOB.read_text()` でworkload、protocol表、build/calibrate argv、copy・検証・interpreter断片を取得。fixtureではtoolsディレクトリもコピー。対象アンカー・否定条件を壊す変更なし |
| `test_pegasus_policy_registry.py:327` | tracked shellのheredocから共有policy由来の移設済みkey読取りを検査。formula内の説明追加はkeyアクセスを増やさない |

検索で現れた `test_pegasus_floor_tools.py` は **floor script内の出典コメント**をアンカーとして読んでいます。`test_hooks.py` の該当参照はコマンド文字列・分類表です。これらをcertify sourceの直接読込と数えていません。

**成果物影響：** 所有外の検査破損は未検出。一方、新しいformulaとscript SHAは今後のreceiptに入り、receiptを内包する認定JSONのhashと公開ファイル名も変わります。これは今回の記述変更に伴う意図された参照変更です。

読めなかった追加path：`orchestrator/calibrator/measure.py`。当該ファイルは存在せず、実際のimport先 `runner.py::measure_point` を追跡して検査を続けました。必読8ファイルはすべて読取可能でした。

## 総括

**must-fix：0件。指定された不変条件の破壊、受理条件の変更、pinの弱体化は確認できませんでした。**

今回の確認はバイト比較・静的追跡・メモリ上のpin評価です。テストスイートは再実行しておらず、実装報告の「69 passed」は独立に再確認していません。

最大経路の完遂保証と公開後TERMの既存問題は残ります。今回の変更をT-2563の再凍結完了とは扱いません。