# [T-004] WAL framing wave — 変異台帳 (2026-07-22)

B-057 の事前登録 → 実測 → erratum を 1 箇所に凍結する。ハーネスは flock 単一走行 guard・
内容比較復元・subprocess timeout・ANSI 除去つき FAILED node 解析 (F32 準拠)。
kill の判定基準は「受理集合または fail-closed 挙動が期待方向へ変わった」であり、
指定 kill テストが赤集合に含まれることを帰属条件とする。

## 事前登録の変遷

- 段 4 で candidate 15 件を登録 (プラン候補 M01..M10 から M02 取り下げ [単一 exact diff 不成立]、
  M10 条件付き→今回は不採用、M06 を parse/writer の 2 site へ分割、M11..M14b/DP1 を追加)
- 1 巡目実測後、レビュー R1-9/R2-7/R2-8 と親のコード裁定により M14a/M14b/M07 を再設計
  (erratum 1..3)。fix 後に M14 単層 (再設計 fixture)・M07b 両層・M06ab 両層・M15・M16 を登録し
  18 変異で再実測

## 最終結果 (fix 後、2 巡目 + 両層再走)

| ID | 枠 | 結果 | 指定 kill テスト |
|---|---|---|---|
| M01 | acceptance | killed | test_wal_unterminated_complete_json_is_always_truncated_tail |
| M03 | durability | killed | test_wal_append_rejects_every_unterminated_tail_without_changing_bytes |
| M04 | durability | killed | test_wal_repair_tail_then_append_restores_independent_frames |
| M05 | durability | killed | test_wal_append_completes_short_writes_and_rejects_zero_progress |
| M06a | acceptance | killed | test_wal_reader_stage_contract_is_exact_and_unknown_stage_fails_closed |
| M06b | equivalent-probe | survived-as-designed | — |
| M06ab | acceptance | killed | test_wal_writer_stage_contract_is_exact_and_unknown_stage_fails_closed |
| M07a | diagnostic-pin | killed | test_wal_writer_rejects_nonstring_json_key_before_writing |
| M07b | acceptance | killed | test_wal_writer_rejects_nonstring_json_key_before_writing |
| M08 | acceptance | killed | test_wal_payload_deep_type_rejections_happen_before_open |
| M09 | acceptance | killed | test_wal_reader_rejects_raw_nonfinite_payload_constants_and_overflow |
| M11 | durability | killed | test_wal_append_and_repair_wait_for_exclusive_flock |
| M12 | durability | killed | test_ensure_resumable_wal_rejects_missing_lock_with_bytes_unchanged |
| M13 | acceptance | killed | test_foreign_known_stage_is_inert_record_protocol_violation |
| M14 | acceptance | killed | test_unframed_wal_tail_fails_but_keeps_completed_prefix_evidence |
| M15 | durability | killed | test_ensure_campaign_identity_propagates_wal_lstat_eio_before_lock |
| M16 | wiring | killed | test_drive_iteration_checkpoint_survives_across_calls |
| DP1 | diagnostic-pin | diagnostic-red | — |

集計: **acceptance 8 kill (M01/M06a/M06ab/M07b/M08/M09/M13/M14) / durability 6 kill
(M03/M04/M05/M11/M12/M15) / wiring 1 kill (M16) / diagnostic-pin 2 (M07a = 診断型後退 pin、
DP1 = literal NaN 診断 pin) / equivalent 1 (M06b)**。SURVIVED (未説明の生存) は 0。

## erratum (すべて実測・レビューで検出済み、恒久対応は F33 と skill 作法)

1. **1 巡目の M14a/M14b の kill 帰属は誤分類だった** (R1-9 採用、R2 の「妥当」は親がコードで
   refuted)。fixture の deviation event が独立赤を持つ過剰決定で、赤は理由文字列の変化 =
   診断赤であり受理集合変化の証拠ではない。fix の F-H で fixture を「完走 prefix + 無終端 tail」
   単一理由へ再設計し、M14 は単層 acceptance として kill を実測した
2. **1 巡目の M07 も同型** (R2-7/R1)。隣接 `_validate_string(key)` の TypeError が同じ入力を
   落とすため単層では acceptance が開かない。M07a (診断 pin) と M07b (両層 acceptance) に分割した
3. **1 巡目の「M06ab 両層 kill で裏取り」は帰属不能だった** (R2-8)。複合テストが reader assert で
   停止し writer 側を証明していなかった。fix の F-K で reader/writer を別 node に分割し、
   M06ab は writer node の赤で kill を再実測した
4. **2 巡目ハーネスに同一ファイル複数置換のバグ** (= F33)。各置換を毎回 originals から適用して
   おり後の置換が前を上書き、M06ab/M07b が偽 SURVIVED になった。累積適用 + 累積後一意性 assert に
   修正し、当該 2 件の再走で kill を確認した。偽 SURVIVED が「bad」として即座に表面化したのは、
   両層変異に kill 期待を事前登録していたため (期待なしなら equivalent と誤結論し得た)

## 走行記録

- 1 巡目 (fix 前 15 変異): `mutation_run.log` (job tmp、セッション限り)。結論は本文の変遷どおり
- 2 巡目 (fix 後 18 変異): 下記 JSON
- 両層 2 件の再走 (ハーネス修正後): 下記 JSON

### 2 巡目 JSON
```json
[
 {
  "id": "M01",
  "ledger": "acceptance",
  "kill": "test_wal_unterminated_complete_json_is_always_truncated_tail",
  "sites": [
   "orchestrator/campaign/wal.py"
  ],
  "rc": 1,
  "failed": [
   "orchestrator/tests/test_campaign.py::test_wal_tolerates_truncated_last_line",
   "orchestrator/tests/test_campaign.py::test_wal_unterminated_complete_json_is_always_truncated_tail",
   "orchestrator/tests/test_campaign.py::test_wal_multibyte_partial_tail_is_not_decoded"
  ],
  "status": "killed"
 },
 {
  "id": "M03",
  "ledger": "durability",
  "kill": "test_wal_append_rejects_every_unterminated_tail_without_changing_bytes",
  "sites": [
   "orchestrator/campaign/wal.py"
  ],
  "rc": 1,
  "failed": [
   "orchestrator/tests/test_campaign.py::test_wal_append_rejects_every_unterminated_tail_without_changing_bytes"
  ],
  "status": "killed"
 },
 {
  "id": "M04",
  "ledger": "durability",
  "kill": "test_wal_repair_tail_then_append_restores_independent_frames",
  "sites": [
   "orchestrator/campaign/wal.py"
  ],
  "rc": 1,
  "failed": [
   "orchestrator/tests/test_campaign.py::test_wal_repair_tail_then_append_restores_independent_frames",
   "orchestrator/tests/test_campaign.py::test_wal_repair_without_any_newline_truncates_to_zero",
   "orchestrator/tests/test_campaign.py::test_wal_repair_receipt_is_durable_and_complete_before_truncate",
   "orchestrator/tests/test_campaign.py::test_loop_resume_repairs_tail_before_replay_and_surfaces_receipt"
  ],
  "status": "killed"
 },
 {
  "id": "M05",
  "ledger": "durability",
  "kill": "test_wal_append_completes_short_writes_and_rejects_zero_progress",
  "sites": [
   "orchestrator/campaign/wal.py"
  ],
  "rc": 1,
  "failed": [
   "orchestrator/tests/test_campaign.py::test_wal_append_completes_short_writes_and_rejects_zero_progress"
  ],
  "status": "killed"
 },
 {
  "id": "M06a",
  "ledger": "acceptance",
  "kill": "test_wal_reader_stage_contract_is_exact_and_unknown_stage_fails_closed",
  "sites": [
   "orchestrator/campaign/wal.py"
  ],
  "rc": 1,
  "failed": [
   "orchestrator/tests/test_campaign.py::test_wal_reader_stage_contract_is_exact_and_unknown_stage_fails_closed"
  ],
  "status": "killed"
 },
 {
  "id": "M06b",
  "ledger": "equivalent-probe",
  "kill": null,
  "sites": [
   "orchestrator/campaign/wal.py"
  ],
  "rc": 0,
  "failed": [],
  "status": "survived-as-designed"
 },
 {
  "id": "M06ab",
  "ledger": "acceptance",
  "kill": "test_wal_writer_stage_contract_is_exact_and_unknown_stage_fails_closed",
  "sites": [
   "orchestrator/campaign/wal.py",
   "orchestrator/campaign/wal.py"
  ],
  "rc": 0,
  "failed": [],
  "status": "SURVIVED"
 },
 {
  "id": "M07a",
  "ledger": "diagnostic-pin",
  "kill": "test_wal_writer_rejects_nonstring_json_key_before_writing",
  "sites": [
   "orchestrator/campaign/wal.py"
  ],
  "rc": 1,
  "failed": [
   "orchestrator/tests/test_campaign.py::test_wal_writer_rejects_nonstring_json_key_before_writing",
   "orchestrator/tests/test_campaign.py::test_wal_payload_deep_type_rejections_happen_before_open"
  ],
  "status": "killed"
 },
 {
  "id": "M07b",
  "ledger": "acceptance",
  "kill": "test_wal_writer_rejects_nonstring_json_key_before_writing",
  "sites": [
   "orchestrator/campaign/wal.py",
   "orchestrator/campaign/wal.py"
  ],
  "rc": 0,
  "failed": [],
  "status": "SURVIVED"
 },
 {
  "id": "M08",
  "ledger": "acceptance",
  "kill": "test_wal_payload_deep_type_rejections_happen_before_open",
  "sites": [
   "orchestrator/campaign/wal.py"
  ],
  "rc": 1,
  "failed": [
   "orchestrator/tests/test_campaign.py::test_wal_payload_deep_type_rejections_happen_before_open"
  ],
  "status": "killed"
 },
 {
  "id": "M09",
  "ledger": "acceptance",
  "kill": "test_wal_reader_rejects_raw_nonfinite_payload_constants_and_overflow",
  "sites": [
   "orchestrator/campaign/wal.py"
  ],
  "rc": 1,
  "failed": [
   "orchestrator/tests/test_campaign.py::test_wal_payload_deep_type_rejections_happen_before_open",
   "orchestrator/tests/test_campaign.py::test_wal_reader_rejects_raw_nonfinite_payload_constants_and_overflow"
  ],
  "status": "killed"
 },
 {
  "id": "M11",
  "ledger": "durability",
  "kill": "test_wal_append_and_repair_wait_for_exclusive_flock",
  "sites": [
   "orchestrator/campaign/wal.py"
  ],
  "rc": 1,
  "failed": [
   "orchestrator/tests/test_campaign.py::test_wal_append_fsyncs_directory_under_flock_on_every_append",
   "orchestrator/tests/test_campaign.py::test_wal_append_and_repair_wait_for_exclusive_flock"
  ],
  "status": "killed"
 },
 {
  "id": "M12",
  "ledger": "durability",
  "kill": "test_ensure_resumable_wal_rejects_missing_lock_with_bytes_unchanged",
  "sites": [
   "orchestrator/campaign/ident.py"
  ],
  "rc": 1,
  "failed": [
   "orchestrator/tests/test_campaign.py::test_ensure_campaign_identity_propagates_wal_lstat_eio_before_lock",
   "orchestrator/tests/test_campaign.py::test_ensure_campaign_identity_rejects_symlink_and_nonregular_wal_before_lock",
   "orchestrator/tests/test_campaign.py::test_ensure_campaign_identity_fstat_rejects_lstat_open_race_to_nonregular",
   "orchestrator/tests/test_campaign.py::test_ensure_resumable_wal_rejects_missing_lock_with_bytes_unchanged"
  ],
  "status": "killed"
 },
 {
  "id": "M13",
  "ledger": "acceptance",
  "kill": "test_foreign_known_stage_is_inert_record_protocol_violation",
  "sites": [
   "orchestrator/campaign/s8b_oracle_report.py"
  ],
  "rc": 1,
  "failed": [
   "orchestrator/tests/test_s8b_oracle_report.py::test_foreign_known_stage_is_inert_record_protocol_violation"
  ],
  "status": "killed"
 },
 {
  "id": "M14",
  "ledger": "acceptance",
  "kill": "test_unframed_wal_tail_fails_but_keeps_completed_prefix_evidence",
  "sites": [
   "orchestrator/campaign/s1_report.py"
  ],
  "rc": 1,
  "failed": [
   "orchestrator/tests/test_s1_report.py::test_unframed_wal_tail_fails_but_keeps_completed_prefix_evidence",
   "orchestrator/tests/test_s1_report.py::test_line_issue_and_unframed_tail_are_both_reported_with_prefix_kept"
  ],
  "status": "killed"
 },
 {
  "id": "M15",
  "ledger": "durability",
  "kill": "test_ensure_campaign_identity_propagates_wal_lstat_eio_before_lock",
  "sites": [
   "orchestrator/campaign/wal.py"
  ],
  "rc": 1,
  "failed": [
   "orchestrator/tests/test_campaign.py::test_ensure_campaign_identity_propagates_wal_lstat_eio_before_lock"
  ],
  "status": "killed"
 },
 {
  "id": "M16",
  "ledger": "wiring",
  "kill": "test_drive_iteration_checkpoint_survives_across_calls",
  "sites": [
   "orchestrator/campaign/p3_s4_loop.py"
  ],
  "rc": 1,
  "failed": [
   "orchestrator/tests/test_p3_s4_loop.py::test_drive_iteration_checkpoint_survives_across_calls"
  ],
  "status": "killed"
 },
 {
  "id": "DP1",
  "ledger": "diagnostic-pin",
  "kill": null,
  "sites": [
   "orchestrator/campaign/wal.py"
  ],
  "rc": 1,
  "failed": [
   "orchestrator/tests/test_campaign.py::test_wal_reader_rejects_raw_nonfinite_payload_constants_and_overflow"
  ],
  "status": "diagnostic-red"
 }
]
```

### 両層再走 JSON
```json
[
 {
  "id": "M06ab",
  "ledger": "acceptance",
  "kill": "test_wal_writer_stage_contract_is_exact_and_unknown_stage_fails_closed",
  "sites": [
   "orchestrator/campaign/wal.py",
   "orchestrator/campaign/wal.py"
  ],
  "rc": 1,
  "failed": [
   "orchestrator/tests/test_campaign.py::test_wal_reader_stage_contract_is_exact_and_unknown_stage_fails_closed",
   "orchestrator/tests/test_campaign.py::test_wal_writer_stage_contract_is_exact_and_unknown_stage_fails_closed"
  ],
  "status": "killed"
 },
 {
  "id": "M07b",
  "ledger": "acceptance",
  "kill": "test_wal_writer_rejects_nonstring_json_key_before_writing",
  "sites": [
   "orchestrator/campaign/wal.py",
   "orchestrator/campaign/wal.py"
  ],
  "rc": 1,
  "failed": [
   "orchestrator/tests/test_campaign.py::test_wal_writer_rejects_nonstring_json_key_before_writing",
   "orchestrator/tests/test_campaign.py::test_wal_payload_deep_type_rejections_happen_before_open"
  ],
  "status": "killed"
 }
]
```
