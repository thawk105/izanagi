## 変更点

[orchestrator/tests/test_s8c_preregistration_core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-c02-receipt-v2/orchestrator/tests/test_s8c_preregistration_core.py:644) の契約由来 pin 5 値だけを更新しました。

- path 件数: `39` → `40`
- 現行 contract hash: `c626566e…997c`
- 非 path 制御文字 variant: NUL・CR・LF の3 hash

assert、parametrize、検査対象、受理条件は変更していません。docs 編集・commit・所有外編集はありません。

## 導出

path 件数は、HEAD 版と作業木版の JSON を再帰走査し、値が文字列である exact key `path` を数えました。

- HEAD: 39
- 作業木: 40
- 増加箇所: C02 の `/conditions/1/required_evidence/1/path`
- 追加された evidence: `proposal_namespace_producer`
- path: `orchestrator/campaign/p3_autonomous_workload_trial.py`
- 条件別では C02 のみ `2 → 3`、ほか11条件は不変

現行 hash は指定どおり次から導出しました。

```python
M.evidence_contract_sha256(EVIDENCE_CONTRACT_FILE.read_bytes())
```

結果は `c626566ea79eaaf6f5a958b3f418d5995b044d06edaac33fe012c29e8218997c`。標準ライブラリによる canonical JSON と domain prefix からの独立計算も一致しました。

制御文字 variant は各回、現行契約を parse し、テストと同じく `conditions[0]["static_only_note"]` へ `f"{control}data"` を追加して `json.dumps(..., ensure_ascii=False).encode("utf-8")` しました。

- NUL: `e72b5b12d12c570bb13a7407024e921959023371f08b3671f58c32de83c911cc`
- CR: `e1b6e7f5b33ce38d201c86efd548f07e57e7e59198ec1406913c43d1f8aec436`
- LF: `83eb67e76235cc292aab2f854b54bfcc8d1b461dc2d96febf4c81d55c5eace55`

いずれも production helper と独立計算が一致し、working-tree hash 等の揮発値は含みません。

関連する制約 meta-test も洗い出しました。

- `test_current_markdown_extracts_nine_fields_and_conditions_1_to_12`: 条件番号1〜12の完全一致
- `test_predicate_registry_is_exactly_c01_through_c12`: C01〜C12の順序・件数
- `test_contract_declares_exact_terminal_definition_path_universe`: unique evidence path 14件
- `test_satisfiable_predicate_requires_negative_control`: machine ID集合、7 negative-control IDの完全一致
- `test_machine_checkable_contract_and_evaluator_registry_are_bijective`: 契約ID・evaluator IDの全単射
- `test_machine_contract_function_names_exist_and_checked_set_is_exact`: 21 tupleの完全一致。静的再導出は missing 0
- `test_candidate_is_not_effective_and_has_zero_satisfied_predicates`: 12 predicate・ID順序・SATISFIED 0件
- `test_wave_files_do_not_contaminate_production_holdout_scan`: required path 8件の包含
- `test_contract_path_inventory_has_expected_count`: 今回更新した全40 `path` 位置の pin

静的再計数では既存の `12 / 14 / 7 / 21` pin は現契約と一致し、追加更新は不要でした。

## 実走

次の nodeid を `python3 tools/run_tests.py` 経由で投入しました。

- `test_contract_path_inventory_has_expected_count`
- `test_current_evidence_contract_hash_is_frozen`
- `test_evidence_contract_hash_accepts_non_path_controls[nul]`
- `test_evidence_contract_hash_accepts_non_path_controls[cr]`
- `test_evidence_contract_hash_accepts_non_path_controls[lf]`

実行器が Pegasus dispatch を選択しましたが、`qstat -Q preflight rc=1`、child rc=16 で終了し、pytest は開始されませんでした。したがって実装済み・未実走です。

静的検査結果:

- `git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 成功
- 旧 hash 4値の残存検索: 0件

## 未解決

親による上記5 instanceの実走が必要です。指定されたU3由来の期待赤3件には触れていません。

- `test_candidate_freeze_matches_contract_and_generation_chain`
- `test_repository_tip_binds_current_decider_version_without_activation`
- `test_current_repository_snapshot_exactly_matches_head`

## 総括

契約改訂で変化した path 件数、現行 contract hash、制御文字 variant hashを契約から再導出し、drift検知の意味を保ったまま逐語値だけ更新しました。docs・所有外ファイル・commitには触れていません。実装済み・未実走です。