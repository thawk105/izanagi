段 6 fix を実装しました。docs、Git index、commit、禁止ファイルには触れていません。pytest と変異 harness 本走は未実施です。

### 所見対応

| 所見 | 状態 | 対応 |
|---|---|---|
| C1 / D1 | closed | 従量 5 key を値によらず存在検査し、`metered-transport-env-present` で拒否。M16/P3 を追加 |
| C2 | closed | source-env型、PBS、TLS、未受理proxy、従量keyをpolicy read前のpure preflightへ移動。reader 0回を固定 |
| C3 | closed | valid receiptで `_invoke()` 成功、provider 1回、valid event、journal/report同値を検査 |
| C4 | closed | production providerの既定 `subprocess.run` を実shimで通過。resolver seamは裁定どおり新設せず |
| C5 | closed | M5をleaf/provider、M10をrun-level counter、M12をpre/post-openへ分離 |
| C6 | partial | 診断OSError、supervisor-error、両wall-budget、run-finishは閉鎖。cleanup failureのterminal反映は採用範囲外のまま |
| C7 | closed | M11、M12、M13を層別nodeidへ分割し、code・回数・sentinel不在を固定 |
| D2 | partial | 従量envは閉鎖。PATH/HOME・実行体digestはT-242残余 |
| D3 | partial | PBS_JOBIDをexact syntax/64文字以内へ制限。scheduler receipt/cgroup照合は不採用残余 |
| D4 | partial | URI path禁止とPBS syntaxを実装。生PBS_JOBID保持とhash化不採用は親裁定どおり |
| D5 | closed | opt-out provenanceのforged receiptをinvalid化 |
| D6 | closed | artifact診断失敗が元のrole failureを置換せず、invalid attemptを保持 |
| D7 | partial | 正常opt-outのtransport非露出を実subprocessで固定。object shape・異常分類の完全byte parityは主張していない |

regressed と判定した所見はありません。

### 差分

- [claude_transport.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_transport.py): pure preflight、従量key deny、PBS syntax、URI path禁止。
- [p3_autonomous_workload_trial.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py): opt-out receipt拒否、診断best-effort、terminal receipt閉包、consumer側PBS syntax。
- [test_claude_transport.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py): 40 testへ拡張。成功consumer、real shim、M5/M10/M11/M12/M13、M16/P1/P3等を追加。
- [mutate.py](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/mutate.py)・[mutations.json](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/mutations.json): flock、timeout、diff-stat記録、失敗node抽出、内容比較復元を備えたspec駆動harness。
- 段5のprovider/policy/registry bytesには段6追加変更なし。

所有外への静的波及として、`site_policy.py`、s8b両ファイル、`p3_s4_loop_trigger_gating.py`、docsは無変更です。`CLAUDE_ENV_ALLOWLIST`も従来の5 keyのままです。

### 変異対応

以下では `T::` を `orchestrator/tests/test_claude_transport.py::` と略記します。

| 変異 | kill／緑維持node |
|---|---|
| M1 | `T::test_rejects_non_compute_sites_and_wrapper_orders_io` |
| M2 | `T::test_rejects_each_tls_override_without_secret_disclosure` |
| M3 | `T::test_rejects_each_unadmitted_proxy_name_without_disclosure` |
| M4 | `T::test_rejects_missing_non_string_and_drifted_required_pair` |
| M5-leaf | `T::test_m5_leaf_preserves_distinct_http_and_https_values` |
| M5-provider | `T::test_m5_provider_real_subprocess_preserves_distinct_admitted_pair` |
| M6 | `T::test_reverse_endpoint_key_order_uses_literal_canonical_digest` |
| M7 | `T::test_rejects_pbs_job_witness_failures_without_disclosure` |
| M8 / M9 | `T::test_cli_flag_default_and_all_four_wiring_links_are_explicit` |
| M10 | `T::test_m10_run_resolves_site_and_policy_once_for_all_four_roles` |
| M11-invalid | `T::test_m11_invalid_attempt_keeps_same_receipt` |
| M11-init | `T::test_m11_provider_init_error_keeps_same_receipt` |
| M12-pre-open | `T::test_m12_pre_open_rejects_policy_symlink_before_open` |
| M12-post-open | `T::test_m12_post_open_rejects_controlled_regular_file_swap` |
| M13-leaf | `T::test_m13_leaf_error_never_discloses_proxy_value` |
| M13-trial | `T::test_m13_trial_error_redacts_endpoint_and_jobid` |
| M14-exact | `T::test_invoke_consumer_rejects_missing_extra_and_hash_receipts` |
| M14-success-reject/drop | `T::test_success_consumer_keeps_valid_receipt_in_journal_and_report` |
| M14-opt-out | `T::test_opt_out_rejects_forged_provider_transport_receipt` |
| M15 | `T::test_committed_policy_matches_independent_literal_hash_and_registry` |
| M16 | `T::test_m16_rejects_each_metered_transport_key_by_presence` |
| P1 | `T::test_p1_default_provider_real_subprocess_has_no_transport_fields` |
| P2 | `T::test_accepts_committed_literal_with_exact_receipt` |
| P3 | `T::test_p3_accepts_when_metered_transport_keys_are_absent` |

全negative anchorは最終ソース上1件、全nodeidはAST上実在します。ただし変異本走前なので、KILLEDや「SURVIVEDなし」はまだ主張できません。

### 静的検査

- `py_compile`: production 3 file、test、`mutate.py` 成功
- JSON構文: policy、registry、`mutations.json` 成功
- `git diff --check`／`--cached --check`: 成功
- `check_codex_agents.py`: 成功
- `check_docs.py`: 違反なし
- anchor一意性: negative 23 entryすべて `count=1`
- pytest、plain runner、mutation harness: 未実施。緑は主張しません
- commit／stage／branch操作: 未実施

## 総括

採用されたmust-fixは実装済みです。裁定で残したT-242、scheduler attestation、receipt値のhash化、cleanup outcome、campaign proof-chain束縛は実装していません。次工程は親による統合commit後の変異harness本走とPegasus計算ノード受入です。