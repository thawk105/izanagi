spec を repo 外へ作成しました。

[mutation-spec.json](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/mutation-spec.json)

- anchor: `61fc5202dcc141fc873eda10469a638763978b26`
- 変異: KILLED 対象 24 件 + diagnostic pin 3 件
- 全件 `hang_risk: false`
- 時間設定: estimate 180秒/run、timeout 900秒、hang timeout 300秒
- repo 内のコード・テストは未編集、`git status --short` は空
- pytest、変異適用、harness 本走は未実行

## 期待 nodeid

以下の prefix はすべて `orchestrator/tests/test_reflux_origin_ledger.py::` です。

| 略称 | 関数名 |
|---|---|
| V01 | `test_v01_literal_manifest_event_state_and_receipt_goldens` |
| V02 | `test_v02_exact_five_phase_five_event_transition_matrix_and_no_legacy_tombstone` |
| V07 | `test_v07_batch_prefix_cardinality_distinctness_and_single_inflight` |
| V08 | `test_v08_tombstone_no_refund_cardinality_accounting_and_no_provider` |
| V14 | `test_v14_i_q_k_sealed_evidence_row_proxy_floor_not_physical_query_and_aborted_seal` |
| V16a | `test_v16_commit_reveal_privacy_order_exact_class_and_positive_cycle` |
| V16b | `test_v16_salt_contract_and_observer_reconstructs_preseal_bytes` |
| V17 | `test_v17_member_identity_replicates_and_sealed_evidence_row_proxy_not_physical_query` |
| V18 | `test_v18_evidence_outcome_contract_and_fixed_member_tombstones` |
| V19 | `test_v19_authority_policy_and_sealed_evidence_row_proxy_partition_not_physical_query` |
| V20 | `test_v20_preseal_projection_hides_execution_counters_and_replicates` |
| V21 | `test_v21_exact_salt_width_and_independent_codec_partition_oracle` |
| V22 | `test_v22_authority_floor_requires_an_existing_batch_partition` |
| V23 | `test_v23_two_origin_shared_runtime_head_aggregate_max_and_max_plus_one` |
| V24 | `test_v24_origin_ledger_total_decimal_cardinality_max_and_max_plus_one` |
| V25 | `test_v25_public_commit_enforces_2248_member_codec_cardinality` |

## 変異登録と単一理由性

`old` 一意性は、固定 HEAD の source に対する逐語 `.count()` で確認しました。表の `1` は exactly one を表します。

| ID | 壊す防壁 | `old` | 期待 node | 単一理由性 |
|---|---|---:|---|---|
| M-1 | member preimage から wire を除外 | 1 | V01/V02/V08/V14/V16a/V16b/V17/V18/V19/V20 | 成立。連鎖赤はすべて wire 束縛欠落による commitment 不一致 |
| M-2 | query ordinal 束縛を除外 | 1 | M-1 と同じ | 成立。同じ ordinal 束縛欠落が原因 |
| M-3 | replicate ordinal 束縛を除外 | 1 | M-1 と同じ | 成立。同じ replicate 束縛欠落が原因 |
| M-4 | origin-wide replicate ordinal 検査を削除 | 1 | V17 | 成立 |
| M-5 | query ordinal の origin-contiguous 検査を削除 | 1 | V17 | 成立 |
| M-6 | duplicate candidate commitment 拒否のみ削除 | 1 | V07/V17 | 成立。両 node とも同じ重複拒否の欠落 |
| M-7 | seal 時の candidate wire 正準性検査を削除 | 1 | V17 | 成立 |
| M-8 | prepared/committed member identity 比較を削除 | 1 | V16a | 成立 |
| M-9-double-prime ※ | cardinality、`zip(strict=True)`、query partition の三層を同時除去 | 累積 `[1,1,1]` | V18 | 厳密な単一編集理由ではない。三層全体を外したときの partial-opening 感度 pin |
| M-10-prime | codec/reducer 共有 outcome closure を削除 | 1 | V18 | 成立。共有 helper の一つの閉包検査が原因 |
| M-11 | accepted/rejected の evidence 必須を削除 | 1 | V18 | 成立 |
| M-12 | tombstoned の evidence-null 要求を削除 | 1 | V18 | 成立 |
| M-13 | result/evidence commitment 比較だけを削除 | 1 | V18 | 成立。outcome tamper は対象外、evidence tamper のみ |
| M-14-prime | floor を `sealed+tombstoned` へ弱化 | 1 | V14 | 成立 |
| M-15 | pre-seal semantic hash に実行依存 counter を戻す | 1 | V16b/V20 | 成立。同じ counter 漏洩を frame/hash の二つの oracle が観測 |
| M-16-prime ※ | seal 用 durable projection に opening の実 replicate ordinal を混入 | 1 | V16b/V20 | 未確立。漏洩は観測するが、現行 node は replay 受理を最後まで証明しない |
| M-17 | `_salt` の上限を外し、32文字以上を許す | 1 | V21 | 成立 |
| M-18a | Qmax feasibility を単一 batch 上限へ退行 | 1 | V14/V21/V22/V23/V24/V25 | 成立。連鎖赤はすべて同じ過剰拒否。`category=positive` |
| M-18b | public commit の per-batch cardinality guard を削除 | 1 | V25 | 成立 |
| M-18c | origin-total byte guard だけを削除 | 1 | V24 | 成立 |
| M-19 | floor を満たす batch partition の存在検査を削除 | 1 | V22 | 成立 |
| M-20 | authority 全体の shared runtime-head 上限を削除 | 1 | V23 | 成立 |
| M-21 | cardinality 十進桁 reserve を旧 affine 式へ戻す | 1 | V24 | 成立 |
| M-22 ※ | unknown event の parser 終端を `None` 返却へ変更 | 1 | V02 | replay 耐性としては不成立。direct parser は赤になるが後段 reducer が mask する |
| M-23-prime | accepted+constraint のみ許可し、digest を `_sha()` で保持 | 1 | V18 | 成立。他 outcome セルは不変 |
| M-24-prime | evidence 必須を accepted のみに限定し、rejected-no-evidence を許可 | 1 | V18 | 成立。accepted の必須条件は維持 |
| M-25-prime | tombstoned+constraint のみ許可し、digest を `_sha()` で保持 | 1 | V18 | 成立。accepted 側は不変 |

M-23-prime/M-24-prime/M-25-prime は単純削除ではなく、対象セルだけを変える exact replacement です。M-23/M-25 は与えられた constraint digest を `None` に正規化しません。

## Diagnostic pin

- M-9-double-prime: 三つの冗長 gate を同時に外す複合感度検査であり、個々の防壁の KILLED 実績には数えられません。
- M-22: direct parser は赤になりますが、実 replay は後段の `"unsupported origin event"` に mask されるため数えられません。
- M-16-prime: shape/hash 漏洩は検出しますが、node が replay-capable mutant の受理を最後まで証明しないため数えられません。

専用 diagnostic category は現行 schema にないため、M-9 は `both-layers`、M-16/M-22 は `negative` に写像しました。実態上はいずれも `expected_status: KILLED` です。

## 静的検証

- harness の `_load_spec()` 成功
- mutation ID 27件、重複なし、指定集合と一致
- 全 expected nodeid をテスト AST 上で確認
- 全 `old` が固定 HEAD に逐語で1件
- M-9 の累積置換後 count は順に `[1, 1, 1]`
- JSON parse、`git diff --check` 成功
- repo 内の変更なし

SHA-256:

```text
6bbcc67661ac11cf88a72dd5d4aa2b7bd7832cd2a869950edb0d2095db1dec54  /work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/mutation-spec.json
```

## 総括

指定された24件の KILLED 対象と3件の diagnostic sensitivity pinを、commit `61fc520` 固定の spec として登録しました。exact anchor、累積一意性、nodeid、schema、SHA-256 は静的確認済みです。コード・テスト・repo 文書・commit には触れず、変異およびテストの実走は親へ残しています。