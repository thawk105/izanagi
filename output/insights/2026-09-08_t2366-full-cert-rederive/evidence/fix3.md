## 実行した command と stdout

```bash
cd /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive && python3 tools/update_acceptance_duration_ledger.py --add-only /home/SFC/tanab/.claude/jobs/b4871f75/tmp/dev-wave-t2366-full-cert-rederive/junit-a2-1.xml
```

rc=0。stdout は逐語で以下です。

```text
excluded_failure_or_error=0
mode=add-only
added=69
skipped_existing=106
excluded_frozen_removed=0
excluded_writer_base_key=0
excluded_frozen_suite=0
excluded_total=0
```

## 追加された node

[acceptance_duration_ledger.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/acceptance_duration_ledger.json) の `git diff` で、69 nodeid の追加を確認しました。`nodeid_count` は 19761 から 19830 へ更新されています。

うち `test_full_materializer_*` は次の 5 件です。

- `test_full_materializer_rejects_forged_effects_from_positive_evidence`
- `test_full_materializer_rejects_forged_status_from_positive_evidence`
- `test_full_materializer_rejects_indeterminate_report_from_full_success_acquisition`
- `test_full_materializer_rejects_reread_partial_receipt_chain_behind_forged_full_fields`
- `test_full_materializer_writes_reread_receipt_bytes_not_supplied_bytes`

差分上、既存 entry の変更はありません。

## 実走した検査

自走 harness:

```bash
cd /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive && PYTHONPATH=. python3 orchestrator/tests/test_update_acceptance_duration_ledger.py
```

rc=0、24 件収集、24 passed。

再検査:

```bash
python3 tools/update_acceptance_duration_ledger.py --check --add-only /home/SFC/tanab/.claude/jobs/b4871f75/tmp/dev-wave-t2366-full-cert-rederive/junit-a2-1.xml
```

rc=0。`added=0`、`skipped_existing=175` を確認しました。

## 未了・判断を仰ぐ点

なし。commit、stage、stash、branch 操作は行っていません。

## 総括

正本 producer の add-only 出力だけで台帳へ 69 nodeid を登録しました。  
`test_full_materializer_*` は指定どおり 5 件含まれています。  
自走 harness は 24/24 passed、再検査も rc=0 です。  
編集対象は指定された台帳 1 ファイルだけです。