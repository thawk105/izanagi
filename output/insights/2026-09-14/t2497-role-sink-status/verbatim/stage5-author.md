## 変更の要約

段4「プランv2」を対象1ファイルへ実装しました。**実装済み・未実走**です。commit・pushはしていません。

## 実装した内容 (file:line)

対象: [test_p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2497-role-sink-status/orchestrator/tests/test_p3_autonomous_workload_trial.py:1846)

- **1846行:** statusだけを判定し、wire・実statusをメッセージに含め、先頭cellを返すhelper。
- **1922行:** `run_trial`直後に無条件で呼び、既存2箇所を戻り値へ接続。
- **2006行:** 実producerのpartial二形を検査する負例1 node。成立条件は`pytest.raises`の外、捕捉対象はhelper呼出しだけ。D387の限界をdocstringに記載。

## 現行の受理・拒否挙動と変更後の差

変更前は収集数・payload・横断assert等で拒否しますが、reportのstatus自体は検査しません。指定の負例二形が旧nodeで受理されたとは主張しません。

変更後は既存条件に加え、各reportに`status == "complete"`を要求します。既存assertはAST一致を確認し、32反復・並行度・admission経路は維持しています。

## 実走した nodeid と結果

**実走0件。** 以下を`tools/run_tests.py`へ渡しましたが、両起動とも`qstat -Q preflight rc=1`、runner終了値16、`child_started=false`でした。

| file（`orchestrator/tests/`配下） | 指定node |
|---|---|
| `test_p3_autonomous_workload_trial.py` | `test_role_sink_bytes_vary_only_at_declared_declassifications` |
| 同上 | `test_role_sink_report_complete_rejects_partial_reports` |
| `test_pytest_collection_config.py` | `test_repo_pytest_ini_has_no_addopts_and_pins_testpaths` |
| 同上 | `test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests` |
| `test_acceptance_schedule_order.py` | `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` |
| `test_real_repo_serialization.py` | `test_real_repo_group_collection_exactly_matches_canonical_nodes` |

静的検査は、構文解析・既存assert一致・新規node数1・重複名なし・`git diff --check`が成功しました。

## 波及可能性の静的列挙

- helperのcallerは本テストと新規負例のみ。
- 既存provider・`_InvalidPlanner`・`_fake_drive`・`_fake_preview`は再利用のみで変更なし。
- production・所有外caller・共有fixture・consumer testへのコード変更なし。
- 新規nodeにより収集集合と所要台帳の未登録集合が1件増加。関連meta-testは検索して上記へ選定しました。

## 未実施・未確認

- 焦点走、meta-test、負例の所要実測、変異M1〜M5／M5′、受入全走。
- 旧版との受理集合差の実測。
- runnerが対象外の`output/pegasus-dispatch/`へ失敗receiptを2件自動生成しました。ソース編集は指定1ファイルのみです。

## 総括

実装と静的検査は完了しました。実走検証はdispatch基盤エラーで未完了のため、**closedとは申告しません**。