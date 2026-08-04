段6 fix を実装しました。段5 staged baseline は保持し、今回の変更は unstaged 差分です。commit/push は行っていません。

### 所見対応表

| # | Fix | 状態 | 対応 |
|---:|---|---|---|
| 1 | F-A | closed | ledger を path-only 受理にし、seal 検証後に全 record を source/provenance から再検査。record 集合・commit・src_token を束縛 |
| 2 | F-B | closed | marker、完全一致 `#if`、同階層 `#else/#endif`、stock frame を binary-mode で厳格化 |
| 3 | F-C | closed | S8A configure 直前・build 直後に `SourceEvidence` を再計算・完全比較 |
| 4 | F-D | closed | receipt 発行時に fresh `resolve_evidence()` と入力 evidence の完全等値を要求 |
| 5 | F-E | closed | artifact topology に lock 由来 `trigger_grammar_locked` を伝播。実 v2 trigger 正例追加 |
| 6 | F-F | closed | abort を active attempt に必須束縛。receiptless reason を共有 closed enum 化 |
| 7 | F-G | closed | oracle lock に policy/grammar を束縛し、report を共有 admitted view に移行 |
| 8 | F-H | closed | Layer3 API/render/CLI に ledger path を公開。decision receipt に ledger hash を保持 |
| 9 | F-I | closed | v4 admission decision を classification 別 `oneOf` 化。historical proof を必須化 |
| 10 | F-J | closed | pinned 2ファイルに recognizer source SHA literal と live 照合を追加 |
| 11 | F-K | closed | `prepare_cell` の full evidence 解決を trigger cell のみに限定 |
| 12 | F-L | closed | deterministic campaign ID literal 3件を grammar-version 束縛後の値へ更新 |
| 13 | F-M | closed | canary を実 binary inspector 経路化。P1–P9×raw/indent の全層テスト追加 |
| 14 | R1-8 | closed/refuted | 裁定どおり変更なし |

### 変更ファイル

Campaign 実装、16ファイル:

`artifact_admission.py`, `build_admission.py`, `layer3_report.py`, `layer3_schema.json`, `loop.py`, `p3_s4_loop.py`, `pipeline.py`, `s1_direct_comparison.py`, `s1_verify_extime_calibration.py`, `s8a_trigger_coverage.py`, `s8b_floor_campaign.py`, `s8b_oracle_driver.py`, `s8b_oracle_report.py`, `source_digest.py`, `trigger_gate_reinspection.py`, `wal.py`

テスト、10ファイル:

`test_artifact_admission.py`, `test_build_admission.py`, `test_buildcache_v2.py`, `test_campaign.py`, `test_layer3_report.py`, `test_p3_autonomous_workload_trial.py`, `test_p3_s4_loop_trigger_gating.py`, `test_s8a_trigger_sweep.py`, `test_s8b_oracle_report.py`, `test_trigger_gate_reinspection.py`

### 期待値変更

承認範囲以外の既存期待値は変更していません。

- F-A fixture 箇所:

  - `test_old_trigger_campaign_requires_record_bound_reinspection`
  - `test_old_trigger_campaign_rejects_self_hashed_raw_mapping`

- F-L の3 node:

  - `test_campaign_identity_is_unchanged_for_other_and_split_for_compute`
  - `test_compute_forwards_required_contract_and_records_sink_receipt`
  - `test_no_build_campaign_identity_binds_shared_policy_context`

新しい値は `362e5961`、`fbceada4`、`4a7be342` です。

### 検査

- `python3 -m py_compile`: 変更 Python 25ファイル成功
- `python3 -m json.tool orchestrator/campaign/layer3_schema.json`: 成功
- `git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 成功
- pytest dispatch: **0 nodeid**。`pegasus02` login node かつ実測 dispatch は親担当のため未実走
- commit 未作成のため `check_ai_provenance.py` は未実行

## 総括

- closed: **14**、partial: **0**、regressed: **0**。
- real fix 13件を実装し、R1-8 は refuted のまま無変更。
- 残リスクは計算ノードで pytest/build を一件も実測していないこと。
- 親は関連10テストファイルに加え既存 campaign/S1/S8B floor 回帰を dispatch すべき。
- 特に real v2 admission、record別 ledger、S8A swap、oracle receipt改竄を実測対象にすること。
- Layer3 v4 の正負 schema、P1–P9×18経路、campaign ID 3件も実測が必要。