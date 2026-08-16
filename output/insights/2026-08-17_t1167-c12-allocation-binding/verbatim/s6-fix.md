段 6 fix を実装しました。commit、stage、docs/output/契約 JSON の編集はしていません。pytest は指定どおり未実走です。

| レビュー所見 | 状態 | 対応 |
|---|---|---|
| A1 M1 生存 | closed（実装済み・未実走） | `check_reservation` のみ到達する負例が、`read_binding` 要求の欠落を `UNSATISFIED / allocation-enforcement-consumer-absent` として検出します。 |
| A2 M6 欠落 | closed（実装済み・未実走） | 実 HEAD supervisor への一意注入 overlay が、両 call を追加した場合に helper の通過側 `None` を検出します。 |
| B1 T-1202 との版衝突 | partial | 本 worktree の g4/v2 一致は pin しましたが、先着 wave 後の v3 再導出は親の統合時作業です。 |
| B2 T-1250 世代競合 | partial | 現候補 g4 の整合は検査対象ですが、先着 g4 を残した g5 合成は親の統合時作業です。 |
| B3 T-1202 合成時の C12 退行 | partial | module-local helper の M1/M6 closure は追加済みです。cross-module explorer との合成は親の統合時作業です。 |
| B4 M1 生存 | closed（実装済み・未実走） | A1 と同じ独立負例により、`read_binding` だけを要求集合から落とす変異を検出します。 |
| B5 M6 欠落 | closed（実装済み・未実走） | A2 と同じ実 HEAD overlay 正例により、正しく両 call を追加した木への過剰拒否を検出します。 |
| B6 g4 版 pin 欠落 | closed（実装済み・未実走） | candidate tip の最新 record が schema v2、実行中の版と一致、理由コードが `decider-version-match` であることを検出します。 |

変更・追加した nodeid は次のとおりです。

- `orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_accepts_non_path_controls[nul]`
- `orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_accepts_non_path_controls[cr]`
- `orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_accepts_non_path_controls[lf]`
- `orchestrator/tests/test_s8c_preregistration_predicates.py::test_c12_allocation_binding_helper_rejects_check_without_read_binding`
- `orchestrator/tests/test_s8c_preregistration_predicates.py::test_current_repository_c12_allocation_binding_helper_accepts_both_calls_overlay`
- `orchestrator/tests/test_s8c_preregistration_invariant.py::test_repository_candidate_tip_binds_current_decider_version_without_activation`

受理集合は広がっていません。正例が pin するのは allocation helper の戻り値 `None`、つまり後段へ進むことだけです。C12 が `SATISFIED` を返す経路は追加されず、後段の終端も `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` のままです。

静的な波及可能性は次のとおりです。

- production caller は `_evaluate_c12` のみで、その上流は predicate registry と activation report です。
- `TOKEN_ONLY_C12` は既存 negative-control fixture と新規 M1 負例で共有されます。
- `repository_candidate_commit` は複数 invariant test の session fixture です。新規版 pin は同じ candidate bytesを読み取るだけです。
- activation report を構築する `test_trial_registry.py`、`test_p3_autonomous_workload_trial.py`、`test_reflux_origin_binding.py` は間接 consumer です。
- 親所有の g4、docs、凍結契約 JSON は今回触れていません。

確認結果:

- 独立 semantic hash 再計算: 現契約と指定 3 literal が一致
- M1/M6 静的 helper probe: 期待一致
- g4 schema/decider 静的 pin: v2/v2 一致
- `git diff --check`: 通過
- `tools/check_codex_agents.py`: OK
- `tools/check_docs.py`: 違反なし
- pytest: 未実走

## 総括

M1、M6、g4 版 pin のレビュー所見は実装で閉じました。残る partial 3 件は並行 wave の着地順に依存する親の合成・世代再発行作業です。