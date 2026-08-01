実装を完了しました。指定された 6 ファイルだけを変更し、docs・禁止対象・`CLAUDE_ENV_ALLOWLIST`・Git index/commit には触れていません。

### 変更差分

| ファイル | 行範囲 | 内容 |
|---|---:|---|
| [claude_transport.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_transport.py:1) | L1–328 | pure evaluator、frozen admission/receipt、site/PBS/policy/env/URI gate、symlink・regular-file・size・read-once 検査、redacted error code |
| [claude_projected_provider.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:96) | L96–200, L327–351 | opt-in flag、run-level admission の受領、exact proxy env 追加、成功 provenance への receipt 追加 |
| [p3_autonomous_workload_trial.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:568) | L568–741 | receipt exact-schema/hash gate、エラー redaction、invalid/init event への receipt |
| 同上 | L771–942 | 4 provider への同一 admission 配布、report への opt-in receipt、全 role attempt への配線 |
| 同上 | L1179–1403 | run 単位 1 回の admission、先頭 `transport-admission` event、CLI flag の `main → run_trial → _provider_set` 配線 |
| [transport_v1.json](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/tools/pegasus/policies/transport_v1.json:1) | L1–9 | 観測済み lowercase 2 endpoint の固定 policy |
| [registry_v1.json](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/tools/pegasus/policies/registry_v1.json:3) | L3–8 | transport policy を閉集合 registry に追加 |
| [test_claude_transport.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:1) | L1–1138 | 独立 literal/SHA、異値・逆順 vector、21 rejection code、CLI/4-role/receipt/report/redaction 境界、plain-runner harness |

### 受理・拒否挙動

現行は proxy を常に child env から落とし、compute node では role transport が成立しません。transport admission、flag、receipt はありません。

変更後も flag 省略時は leaf、site 判定、policy read を呼びません。child argv/env、既存 17-key provenance、journal/report へ transport field を追加しない条件分岐です。

明示 opt-in 時だけ、次の全条件を満たす場合に受理します。

- `PEGASUS_COMPUTE`
- 非空 `PBS_JOBID`
- lowercase `http_proxy` / `https_proxy` の exact 2 値
- 固定 policy との文字列完全一致
- TLS override 7 key と未受理 proxy 8 key が不在
- policy path が symlink なしの regular fileで、size/read/schema/URI が正当

それ以外は fail-closed です。固定 proxy 自体の侵害、T-242、valid-schema 意味注入、T-236/T-277/T-278 は解決・受理対象に広げていません。

### 静的波及

- production caller は `_provider_set()` のみ。既存 constructor test 4 箇所は新引数省略で opt-out を維持します。
- 既存 `_provider_set` monkeypatch fixture は factory の遅延解決を保持しました。
- `p3_autonomous_workload_trial` の journal/report consumer は opt-in 時だけ receipt を扱います。
- `p3_s4_loop_trigger_gating.py` の campaign WAL/proof chain は裁定どおり scope 外です。
- `s8b_prediction_runner.py`、`s8b_selector_freeze.py` の 5-key env／exact 8-key provenance には到達しません。
- `site_policy.py` の hostname classifier は変更せず、transport 専用 PBS witness だけを追加しました。
- `test_pegasus_policy_registry.py` は新 policy が未追跡の現在の worker 状態では trackedness gate が期待どおり赤になります。親の stage/commit 後に解消すべきものです。
- 親 docs 未 land のため期待して赤くなる finding 集合はありません。D96 の docs 同一変更単位化は親の統合責務です。上記未追跡 gate 以外の赤は回帰として扱ってください。

### M1〜M15 対応

| 変異 | kill する nodeid |
|---|---|
| M1 | `orchestrator/tests/test_claude_transport.py::test_rejects_non_compute_sites_and_wrapper_orders_io` |
| M2 | `...::test_rejects_each_tls_override_without_secret_disclosure` |
| M3 | `...::test_rejects_each_unadmitted_proxy_name_without_disclosure` |
| M4 | `...::test_rejects_missing_non_string_and_drifted_required_pair` |
| M5 | `...::test_accepts_distinct_http_https_synthetic_vector` |
| M6 | `...::test_reverse_endpoint_key_order_uses_literal_canonical_digest` |
| M7 | `...::test_rejects_pbs_job_witness_failures_without_disclosure` |
| M8 | `...::test_cli_flag_default_and_all_four_wiring_links_are_explicit` |
| M9 | `...::test_cli_flag_default_and_all_four_wiring_links_are_explicit` |
| M10 | `...::test_provider_set_passes_one_immutable_receipt_object_to_four_roles` |
| M11 | `...::test_invalid_attempt_and_provider_init_event_keep_same_redacted_receipt` |
| M12 | `...::test_policy_surface_rejects_missing_symlink_nonregular_and_oversize` |
| M13 | `...::test_rejects_missing_non_string_and_drifted_required_pair` および `...::test_invalid_attempt_and_provider_init_event_keep_same_redacted_receipt` |
| M14 | `...::test_invoke_consumer_rejects_missing_extra_and_hash_receipts` |
| M15 | `...::test_committed_policy_matches_independent_literal_hash_and_registry` |

## 総括

- `git diff --check`、`py_compile`、JSON 構文、AST による24 test/self-runner構造、21 rejection code の test 対応、`check_codex_agents.py`、`check_docs.py` は通過しました。
- pytest・plain test runner・ビルド・実走は指示どおり一切実行していません。したがってテストの緑は主張しません。
- commit、stage、docs 編集、禁止ファイル編集は行っていません。