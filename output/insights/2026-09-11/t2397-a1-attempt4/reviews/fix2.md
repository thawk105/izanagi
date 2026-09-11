## 総括

[指定ファイル](tools/pegasus/paper_story_a1_paired.sh)の4条件だけ修正しました。先頭 case が選択した policy を再利用し、pilot の full study ID は先頭の1箇所に戻しました。

| 所見 | 状態 | 根拠 |
|---|---|---|
| 後段の study ID 再列挙 | partial | 実装済み・未実走 |
| 追補集合・staging・拒否条件の維持 | partial | 処理本体は変更なし。動的確認は親へ引継ぎ |

- `git diff --check` 成功。差分は所有ファイルの4行置換のみ。test/docs・fixture変更、add/commit/submitなし。
- 実走を試みた範囲：`orchestrator/tests/test_paper_story_a1_job_contract.py` 全体。runner が `qstat -Q` 失敗で rc=16、実走 node は0件。
- 親で必要な制約検査：`test_job_body_dispatches_legacy_pilot_and_future_sized_studies`、`test_non_certifying_source_closure_matches_shell_and_preserves_legacy_set`、`test_non_certifying_source_closure_rejects_each_file_drift`、`test_a1_amendment_binding_rejects_single_changed_input_M8`。
- 所有外の波及先：`paper_story_a1_paired.py` の submit・terminal consumer、job 契約の `_shell_fixture`／`_fixture_job_source`、paired・headline・hooks の関連テスト。

shell 構文確認の `bash -n` は PreToolUse hook がログインノード上の dispatch-required 実行体として拒否しました。迂回せず、構文確認も未実走です。