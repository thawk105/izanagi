1. **変更前の受理・拒否挙動**

静的確認では、既知 driver の top-level `trial` を持つ v1 は受理され、v2 は `unknown trial: None` → `campaign_input_unreadable` で停止していました。

変更後に受理が広がるのは有効な v2 です。旧 `json.loads` が許した不正 v1（duplicate key・非有限値・codec の reserved field 等）は拒否へ移ります。これは裁定の範囲内です。それ以外の候補選別・受理条件は変更していません。

2. **変更したファイルと箇所**

- [p3_b4_prerun_caller.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-b/orchestrator/campaign/p3_b4_prerun_caller.py:50)：`collect_scheduled_batch` の L68 を byte decoder、L76 を `decoded.identity.get("trial")` に変更。L85 の catch は維持。module／関数 docstring と L95 のコメントを caller が読む checkpoint・lock の範囲に限定。`_MISSING_SOURCES` は変更なし。
- [test_p3_b4_prerun_caller.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-b/orchestrator/tests/test_p3_b4_prerun_caller.py:24)：`_lock_binding` で module 内一度だけ HEAD binding を生成し、`_campaign` を v2 化。L114 に v1 三 driver 回帰、L137 に v1 trial 欠落を追加。L274 の既存 parametrization に 5 ケースを追加し、unknown trial は v2 再 encode に変更。

既存 assertion は削除・緩和していません。issuer は既存の実物を通す fixture を維持しています。

3. **静的検査**

以下はともに **rc=0**。生成ファイルを残さない構文コンパイルを使用しました。

```sh
python3 -B -c 'import ast; from pathlib import Path; paths = (Path("orchestrator/campaign/p3_b4_prerun_caller.py"), Path("orchestrator/tests/test_p3_b4_prerun_caller.py")); [(compile(ast.parse(p.read_bytes(), filename=str(p)), str(p), "exec"), print(str(p) + ": syntax OK")) for p in paths]'
git diff --check
```

`git status --short` も rc=0。変更は所有 2 ファイルだけです。

4. **meta-test の静的確認**

`rg` で nodeid・台帳・ファイル列挙・production census を検索し、該当実装を確認しました。

| meta-test | 今回の影響 |
|---|---|
| `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` | 新規 7 node が未登録となり被覆率の分母が増える。90% 閾値の成否は未実走 |
| `test_update_acceptance_duration_ledger.py::test_g7e_checked_in_ledger_has_valid_schema_and_finite_durations` | 台帳不変のため今回の影響なし |
| 同 `test_t1574_changed_suite_ledger_node_delta_is_exact` | 固定対象 suite に caller は含まれず、影響なし |
| `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`／`test_allowlist_has_no_stale_or_self_runnable_entries` | ファイル集合・既存 `pytest.main` harness 不変 |
| `test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests` | ファイル集合・除外設定不変 |
| `test_t1286_commit_receipt.py` の commit producer／capability issuer census | 対象呼出し追加なし |
| `test_p3_b4_analysis_path.py` の analysis caller census、`test_ccbench_spawn_sites.py` の process census、`test_s8b_floor_campaign.py` の `use_perf` census | 対象呼出し追加なし |

台帳へ推測の実行時間は登録していません。

5. **所有外への波及**

- Python 内の caller 参照検索では、所有テスト以外の直接 consumer は見つかりませんでした。`collect_scheduled_batch` の production 呼出しは同 module の `main` です。
- 共有 lock helper は既存 API を利用するだけで変更なし。他 consumer fixture への変更要求はありません。
- issuer・base／sort／trigger driver・side channel consumer は変更なし。赤候補ごとに不足 12 件、候補なしで空 batch を issuer に渡す分岐を維持します。
- caller は contract-loader closure 外です。今回の編集による closure path／blob の変更はありません。
- 過去 insight の mutation-spec に caller 参照があります。過去の記録は変更していません。

6. **実装済み・未実走**

親が計算ノードで走らせる候補は以下です。新設・fixture 変更の影響を受ける完全な nodeid を静的に列挙しています。collection 自体も未実行です。

```text
orchestrator/tests/test_p3_b4_prerun_caller.py::test_success_only_campaigns_reach_issuer_once_with_empty_batch_and_no_root
orchestrator/tests/test_p3_b4_prerun_caller.py::test_v1_campaigns_remain_readable
orchestrator/tests/test_p3_b4_prerun_caller.py::test_missing_v1_trial_is_campaign_input_unreadable
orchestrator/tests/test_p3_b4_prerun_caller.py::test_mixed_campaigns_report_all_missing_sources_and_never_call_issuer
orchestrator/tests/test_p3_b4_prerun_caller.py::test_minimal_rejected_row_is_a_candidate
orchestrator/tests/test_p3_b4_prerun_caller.py::test_fail_row_is_not_a_candidate
orchestrator/tests/test_p3_b4_prerun_caller.py::test_publication_root_is_not_an_argument
orchestrator/tests/test_p3_b4_prerun_caller.py::test_all_candidates_have_all_missing_fields
orchestrator/tests/test_p3_b4_prerun_caller.py::test_unreadable_campaign_never_calls_issuer[checkpoint_absent]
orchestrator/tests/test_p3_b4_prerun_caller.py::test_unreadable_campaign_never_calls_issuer[lock_absent]
orchestrator/tests/test_p3_b4_prerun_caller.py::test_unreadable_campaign_never_calls_issuer[json]
orchestrator/tests/test_p3_b4_prerun_caller.py::test_unreadable_campaign_never_calls_issuer[whiteboard]
orchestrator/tests/test_p3_b4_prerun_caller.py::test_unreadable_campaign_never_calls_issuer[trial]
orchestrator/tests/test_p3_b4_prerun_caller.py::test_unreadable_campaign_never_calls_issuer[row]
orchestrator/tests/test_p3_b4_prerun_caller.py::test_unreadable_campaign_never_calls_issuer[result_absent]
orchestrator/tests/test_p3_b4_prerun_caller.py::test_unreadable_campaign_never_calls_issuer[deep_json]
orchestrator/tests/test_p3_b4_prerun_caller.py::test_unreadable_campaign_never_calls_issuer[non_certifying]
orchestrator/tests/test_p3_b4_prerun_caller.py::test_unreadable_campaign_never_calls_issuer[noncanonical_inner]
orchestrator/tests/test_p3_b4_prerun_caller.py::test_unreadable_campaign_never_calls_issuer[noncanonical_outer]
orchestrator/tests/test_p3_b4_prerun_caller.py::test_unreadable_campaign_never_calls_issuer[authority]
orchestrator/tests/test_p3_b4_prerun_caller.py::test_unreadable_campaign_never_calls_issuer[invalid_utf8]
```

加えて、変更していない発行回帰の候補：

```text
orchestrator/tests/test_p3_b4_prerun_caller.py::test_issue_half_serializes_real_receipt_for_a_complete_batch
```

7. **C1〜C5 の位置と単一理由性**

位置はすべて `p3_b4_prerun_caller.py` です。KILL は未実測です。

| 変異 | 実装後の位置・一行変異 | 自己点検 |
|---|---|---|
| C1 | L76：trial を raw outer の `.get("trial")` へ戻す | 有効 v2 は codec を通過。その後の unknown-trial 分岐で停止し、success-only の issuer 到達期待が落ちる |
| C2 | L68：decoder 呼出しを raw JSON＋inner 手読みに置換 | authority・非 canonical inner／outer ケースは既知 trial・正常 checkpoint。codec を迂回すると同じ不正を拒否する別層はない |
| C3 | L70 直後：`if decoded.is_v1: raise ValueError("v1 rejected")` | v1 回帰入力は codec と driver 判定で受理可能。追加した過剰拒否だけが停止理由 |
| C4 | L85：catch tuple から `ValueError` を削除 | authority 等の codec 例外を捕捉する別 catch はない。`main` は `CampaignInputUnreadable` のみ捕捉するため例外が漏れる |
| C5 | L76：`.get("trial")` を `["trial"]` へ変更 | v1 codec は trial 欠落を許す。添字で `KeyError` が発生し、後段判定へ届かず既存 catch でも捕捉されない |

C2 は正常 lock を作った後に不正化するため、fixture encoder が対象入力を先に拒否する構成にはしていません。non-certifying ケースも専用 encoder で有効な形式を生成しています。

## 総括

**実装済み・未実走。** 所有 2 ファイルだけを変更し、構文検査と差分検査は rc=0。テスト実行・commit・docs 編集は行っていません。