## 受理・拒否挙動

**実装済み・未実走です。** テストは runner の dispatch 認証エラーで、pytest 起動前に停止しました。

v2 の変更前後は次のとおりです。v1 の扱いは変更していません。

| 経路 | 変更前 | 実装後 |
|---|---|---|
| 通常 decoder／encode／resume | exact-63 | 不変 |
| certified admission | 現行 grammar と既存 gate | 不変 |
| 歴史 decoder | exact-63／exact-24 | exact-62 を追加 |
| 未知 grammar | 拒否 | 拒否を維持 |

受理拡張は grammar 単位です。個体 hash allowlist は追加していません。

## 変更ファイル

- [campaign_lock.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2483-impl/orchestrator/campaign/campaign_lock.py:146)：独立 exact-62 literal、兄弟 validator、歴史型 whitelist、decoder 分岐を追加。
- [artifact_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2483-impl/orchestrator/campaign/artifact_admission.py:94)：独立 scope、scope 組と map 順序の対応検査、全62 blob 検証、歴史 epoch 分岐を追加。
- [test_campaign_lock_codec.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2483-impl/orchestrator/tests/test_campaign_lock_codec.py:575)：専用型、通常経路拒否、未知 grammar、authority 直接構築の検査を追加。
- [test_artifact_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2483-impl/orchestrator/tests/test_artifact_admission.py:2994)：固定 known-answer 正例、certified 拒否、未知 grammar、62件の blob 不一致、scope 混成拒否を追加。

Git 差分は指定4ファイルのみです。既存テスト関数はすべて変更前のソースと一致しています。commit・git add・branch 操作はしていません。

## 検査結果

**実走したテスト nodeid：なし。全新設 node は実装済み・未実走です。**

次の3試行はいずれも rc=16、`child_started=false` でした。

1. codec 全件と admission の `t733` 該当テスト。
2. `t733` 該当テストの `--collect-only`。
3. 後述の meta-test。

共通の停止理由：

```text
qstat -Q preflight rc=1
NQSconnect: [API EACCTAUTH] Unknown user-id. (uid: 31609, errno: 1)
```

`queue_state` も観測不能でした。runner の安全判定を迂回して直接 pytest を実行していません。runner が生成した補助12ファイルは除去しました。

静的検査では以下を確認しました。

- 4ファイルの AST parse 成功、`git diff --check` 成功。
- 通常 decoder、encoder、通常 authority validator、certified gate のソース不変。
- exact-24 validator のソース不変。
- 現行 tuple、現行 scope 定数、epoch domain／hash 式の不変。
- Git 由来 exact-62 と production／独立期待 tuple の完全一致。
- 固定 known-answer と合成 fixture の対応一致。

実3本の受入 A／B、測定 C、実ファイルの前後 hash 確認は未実施です。

## contract-loader-drift の帰属

事前登録した期待赤は、実 checkout の HEAD 束縛を通るテストで本文に `contract-loader-drift` が出る場合だけです。

**観測件数は0件です。** pytest 自体が起動していないため、drift が解消した証拠ではありません。今後この赤が出た場合の非帰属根拠は、変更した production 2ファイルが HEAD blob 束縛対象であり、親による commit 前は disk bytes と一致しないという指定の運用事実です。

## 固定 known-answer

[固定値の定義](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2483-impl/orchestrator/tests/test_artifact_admission.py:375)は以下です。

```text
E1:78920efc47f4eb280b956a8fb92abed16b888495db544b62b1a15bf1f61004e9
```

宣言順 path hash：

```text
b274387d0be033a98e86d54e5225667221bde79776832e73fb3d07cebfc6067a
```

算出手順：

1. production 実装後、`git show 2a9ba783f^:orchestrator/campaign/campaign_lock.py` を再取得し、AST から当時の tuple を抽出。
2. 宣言順1始まりの各 `i` に対し、合成 fixture bytes を ASCII の `epoch closure fixture {i}\n` とする。
3. epoch は `SHA256(b"campaign-verifier-epoch/v1" || Σ(path UTF-8 || NUL || SHA256(fixture bytes)))`。
4. path hash は `SHA256(Σ(path UTF-8 || NUL))`。

期待値は固定文字列です。テスト実行時に production 定数や期待列から期待値を再計算しません。production と期待 tuple を同時に並べ替えても固定 hash が検出します。

## 制約 meta-test

直接参照・AST inventory・runner 契約を探索しました。

| meta-test の完全 nodeid | 対象／結果 |
|---|---|
| `orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted` | 自走 harness。試行したが child 未起動 |
| `orchestrator/tests/test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries` | allowlist 整合。試行したが child 未起動 |
| `orchestrator/tests/test_plain_runner_coverage.py::test_this_metatest_is_itself_self_runnable` | 自己適用。試行したが child 未起動 |
| `orchestrator/tests/test_p3_build_authority_cli.py::test_tracked_python_coder_authority_ast_closure_is_exact` | `_new_schema_campaign` の exact callsite／cardinality。試行したが child 未起動 |
| `orchestrator/tests/test_real_repo_serialization.py::test_receipt_memo_consumer_inventory_and_optouts_are_complete` | 試行したが child 未起動。静的には別2ファイルの inventory で、本変更の直接対象外 |
| `orchestrator/tests/test_real_repo_serialization.py::test_real_repo_group_collection_exactly_matches_canonical_nodes` | 共有 fixture／group 集合。未実走 |

既存関数の改名・削除はありません。両ファイルの既存 `_run()` は新設 node も pytest に委譲します。

追加探索で `tests/` および `orchestrator/tests/test_*meta*`、`test_test*`、`test_enforcement*`、`test_sentinel*` に該当するパスは読めませんでした。必読対象8ファイルはすべて読み取り成功しています。

## 所有外への波及

- `layer3_report._read_campaign_lock`：歴史 admission 後も通常 decoder で exact-62 を再拒否します。材料レポート対応は未完了です。
- `b10_backoff_shape_sweep._assert_report_lock_binding`：decode 後の exact-24 専用条件で拒否を維持します。拒否段階は変わり得ます。
- `b10_backoff_static_tail_formal.load_explore_correctness_mode`：中央 admission を通れば、既存の `run_kind`／workload 条件まで進みます。
- `replay.py`、`critic/digest.py`、`critic/online_digest.py`、`tools/plotting/plot_backoff.py`、`plot_s1_9pair.py`：歴史 API 利用箇所の到達範囲が変わる可能性があります。consumer 全経路の成功は未検証です。
- その他の直接参照元：`t1998_stock_inline_pair.py`、`s6_sort_sweep.py`、`s8a_trigger_sweep.py`、`p3_b4_closed_critic.py`、`p3_b4_wiring_probe.py`、`p3_s4_loop.py`、`p3_s4_loop_sort.py`、`p3_s4_loop_trigger_gating.py`、`p3_s4_red.py`、`p3_autonomous_workload_trial.py`、`autonomous_trial_completeness.py`。certified 側の gate は変更していません。
- 共有 fixture：`campaign_lock_test_support.py`、`commit_receipt_support.py`、既存 `_committed_closure_repo`／`_new_schema_campaign` は変更していません。
- admission receipt の `validator_sha256` は自身の実装 bytes に依存するため、変更後に生成する receipt 全体の旧 bytes との一致は主張しません。

既存 consumer 回帰確認として、以下は未実走です。

```text
orchestrator/tests/test_b10_backoff_shape_sweep.py::test_report_lock_identity_accepts_exact_pre_t733_real_snapshots
orchestrator/tests/test_b10_backoff_shape_sweep.py::test_run_formal_report_reaches_locked_collection_and_writer_without_live_inputs
orchestrator/tests/test_b10_backoff_static_tail_formal.py::test_probe_5_explore_mode_and_formal_report_comparison
```

## 新設 nodeid 全覧

9関数・76 node。以下はソースの parameter 宣言から静的に展開した一覧で、pytest collect 成功の証拠ではありません。

```text
orchestrator/tests/test_campaign_lock_codec.py::test_t733_exact62_uses_dedicated_historical_decoder_type
orchestrator/tests/test_campaign_lock_codec.py::test_t733_exact62_remains_rejected_by_normal_decoder
orchestrator/tests/test_campaign_lock_codec.py::test_t733_exact62_rejects_unknown_grammars[subset]
orchestrator/tests/test_campaign_lock_codec.py::test_t733_exact62_rejects_unknown_grammars[superset]
orchestrator/tests/test_campaign_lock_codec.py::test_t733_exact62_rejects_unknown_grammars[same-count-replacement]
orchestrator/tests/test_campaign_lock_codec.py::test_t733_exact62_rejects_unknown_grammars[order]
orchestrator/tests/test_campaign_lock_codec.py::test_t733_exact62_authority_requires_exact_declared_order
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_is_readable_only_as_recorded_historical_epoch
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_is_rejected_for_certified_use
orchestrator/tests/test_artifact_admission.py::test_unknown_t733_exact62_grammar_is_rejected_for_both_read_purposes[subset]
orchestrator/tests/test_artifact_admission.py::test_unknown_t733_exact62_grammar_is_rejected_for_both_read_purposes[superset]
orchestrator/tests/test_artifact_admission.py::test_unknown_t733_exact62_grammar_is_rejected_for_both_read_purposes[same-count-replacement]
orchestrator/tests/test_artifact_admission.py::test_unknown_t733_exact62_grammar_is_rejected_for_both_read_purposes[order]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/env_contract.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/env_contract_activation.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/execution_guard.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/loop.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/pipeline.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/wal.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/ident.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/artifact_admission.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/verifier/core.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/verifier/dsg.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/verifier/model.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/verifier/parse.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/verifier/__init__.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/verifier/report.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/s8c_preregistration.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/s8c_preregistration_evidence.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/s8c_generation_projection.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/campaign_lock.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/contract_loader_binding.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/guided.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/replay.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/qualification/artifacts.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/qualification/t126_driver.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/verifier/commit_receipt.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/calibrator/__init__.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/calibrator/effective_clock_policy.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/calibrator/perf_preflight.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/calibrator/runner.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/calibrator/schema_v2.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/calibrator/stability.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/__init__.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/axis_trigger_gating.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/build_admission.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/buildcache.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/calibration_verify.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/campaign_claim.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/diff_quarantine.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/env_attestation.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/genome.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/layout.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/lock.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/model.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/p2_2.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/p3_b4_launcher.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/p3_b4_protocol.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/reflux_ir.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/reservation.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/search_baselines.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/site_policy.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/source_digest.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/campaign/trigger_gate_binding.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/critic/__init__.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/critic/online_digest.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/holdout_observation.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/qualification/__init__.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/qualification/attempt_ledger.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/qualification/collector.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/qualification/contract.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/qualification/identity.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/qualification/qsub_binding.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/qualification/retry_index.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_rejects_each_recorded_commit_blob_mismatch[orchestrator/qualification/series.py]
orchestrator/tests/test_artifact_admission.py::test_t733_exact62_epoch_requires_matching_scope_and_paths
```

## 裁定との相違

実装上の相違は見つかっていません。authority 側の順序検査は、validator が宣言順に再構成した map の検査であり、元 wire 順序の独立再検査とは説明していません。追加の個体 gate、scope の hash preimage への追加、所有外コードの変更はありません。

## 総括

指定4ファイルへの実装と静的照合は完了しました。  
新設9関数・76 node は実装済み・未実走です。  
dispatch 認証障害により、テスト・meta-test・実3本の受入確認が残っています。  
`layer3_report` の exact-62 再拒否は裁定どおり未修正です。