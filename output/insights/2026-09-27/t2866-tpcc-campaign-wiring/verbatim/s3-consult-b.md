## 総括

- **buildcache は v1 と v2 の両方を変更する必要がある。** `pipeline.evaluate` は `env_contract` の有無で呼び分け、計算ノードの production 経路は v2 を使う。
- **bench 配線は残す。** 現 pin の実行では v2 trace が verify で拒否され bench に進まないが、TPC-C 候補を「評価できる配線」には、pin 前進後に throughput を測れる経路が要る。
- `calibrator/runner.py` の測定関数に workload を渡す案は妥当。`run_once` への置換は `_run_bench` の反復測定・記録契約を作り直すため、縮小にならない。
- `search_config.workload="tpcc"` の記録だけでは実行引数と結び付かない。今回の直呼び生死確認では独立 layout の記録にとどめ、production campaign への接続は別設計と明記する。
- 実行器の flags 文字列化は削除できる。`Cell.flags` は生成時点で文字列になっている。
- 生死確認の `run_job` は warmup と **32 block** を実行する。本測定を scope 外とするなら、投入前にこの費用と記録の用途を明示する。
- 試験は既存の TPC-C v3 fixture を再利用し、同じ正例を複数層に重複追加しない。既存 YCSB golden と拒否条件は維持する。

## 所見

| ID・種別 | 根拠 | 成果物への影響 | 提案 |
|---|---|---|---|
| **B1・維持** | `pipeline.py:2027-2053, 2075-2104`、`p3_s4_loop.py:2570-2573, 2608-2623` | v2 だけなら `env_contract` のない評価が YCSB を build し、v1 だけなら計算ノードで TPC-C を build できない。 | 両 API の target と cache identity を変更する。 |
| **B2・維持** | `pipeline.py:702-708, 1382-1455, 3180-3192`、`calibrator/runner.py:1117-1126` | bench 配線を外すと、将来 v3 が通っても TPC-C に YCSB 専用 flag が付き、fitness を記録できない。 | `measure_point` の flag 選択を局所変更し、現 pin の実測結果は「bench 未実行」と記録する。 |
| **B3・縮小** | `calibrator/runner.py:584-757, 825-867, 1085-1126`、`pipeline.py:1463-1525` | `run_once` への置換は反復・安定性・return code の扱いを変え、レポートの fitness の意味を変えうる。 | 既存 `measure_point` を使う。`capture_measure_point` は今回の TPC-C 呼出しに必要な場合だけ変更する。 |
| **B4・削除** | `t2851_transfer_runner.py:37-50, 77-86, 308-309`、`pipeline.py:458-466` | flags の再文字列化を外しても 57:43 の受理集合は変わらない。 | C の文字列変換とその専用試験を削る。 |
| **B5・不足** | `loop.py:522-560, 899-941, 973-987`、`p3_s4_loop.py:2643-2651`、`ident.py:196-229` | lock に `tpcc` と書くだけでは `run_campaign` が `evaluate` に workload を渡さない。production campaign の候補・レポートを TPC-C として評価したとは言えない。 | 今回は `evaluate` 直呼びまでを達成範囲として明示する。production campaign を成果に含めるなら、lock の値を実行引数へ結ぶ配線が別途必要。 |
| **B6・縮小** | `t2851_transfer_runner.py:357-454`、`brief.md:4, 27-30` | `run_job` 1 本は warmup に加え 32 block × 各 identity を走らせる。生死確認記録が本測定に近い費用と意味を帯びる。 | build・投入・判定の確認に full job が必要か親が判断し、必要なら実 run 数から 2 node 時間未満を再見積りする。静的には所要時間を保証できない。 |
| **B7・縮小** | `s2-plan.md`「A — buildcache と試験」「B — pipeline、calibrator、critic と試験」「C — 転移実行器と試験」、`test_campaign.py:7620-7680`（plan が示す既存 fixture） | 重複する v3 正例・負例は受理集合を広げず、保守対象だけを増やす。 | buildcache の identity・target・hit、pipeline の v2 abort と bench argv、実行器の v2／v3 判定を各層で最少本数にまとめる。既存の「s1-H は経路なし」は s2 等へ移し、拒否試験を弱めない。 |
| **B8・維持** | `calibrator/cli.py:403-425` | calibration receipt 経路で TPC-C target は引き続き拒否されるが、今回の `evaluate` 直呼びの受理集合は変わらない。 | 今回は触らず、TPC-C calibration は未対応と記録する。 |
| **B9・維持** | `critic/digest.py:1332-1337`、`pipeline.py:702-708` | 現文言は TPC-C v2 reject を「YCSB allowlist 外」と誤説明し、レポートの解釈を誤らせる。 | reason 集合を変えず説明文だけ直す。 |

## brief と plan の誤り

- **brief P1 は現 pin では達成不能。** 通常の `evaluate` は verify 後に bench へ進む。TPC-C v2 は先に拒否されるため、実機で記録できるのは build・trace 投入・WAL reject まで（`pipeline.py:702-708, 3145-3192`）。plan の修正が正しい。
- **brief S4 と plan C の flags 前提が誤り。** `Cell.flags` は `_cell` で既に `str(value)` 化される（`t2851_transfer_runner.py:48-50`）。
- **plan の `search_config` 記録は campaign 配線を完成させない。** 現在の `run_campaign` は workload を `evaluate` へ渡さない（`loop.py:899-987`）。P2 は直呼びの識別記録として扱い、production 探索の完成とは呼ばない。
- **生死確認の時間は未実測。** 4 build に加え full `run_job` は 32 block を持つ（`t2851_transfer_runner.py:419-454`）。plan の「30〜60 分、2 node 時間未満」は投入前の見積りであり、確認結果ではない。
- **P3・P4 は維持。** v2 を certified にせず、anomaly／非直列化を失格優先とする。合成 v3 正例は経路の到達可能性を示すが、現 pin の実 TPC-C certified を示さない（`pipeline.py:702-708`、`t2851_transfer_runner.py:465-470`）。
- **S5・S6 は記録中心で足りる。** `_probe("tpcc")` は実機で不在／実行中／終了後を確認し、欠陥時だけ修正する。T-156 は発火条件の再評価を記録する。S3 は文言の局所修正で足りる。静的検査のみ行い、テスト・実機確認は行っていない。