## 所見ごとの対応表 (closed / partial / regressed)

| 所見 | 状態 | 対応 |
|---|---|---|
| F-5：`record` の変数衝突 | closed（修正済み、実走未確認） | resolver の戻り値を `protocol_record` に改名し、path を `protocol_rel` に保持。末尾 return も置換 |
| F-1〜F-4 | 維持 | 今回変更なし |

## 変更点 (file:line)

`orchestrator/campaign/s8b_holdout_freeze.py` のみ今回編集しました。

- 1393：resolver の戻り値を `protocol_record` に改名。
- 1398〜1405：`protocol_rel` を保持し、HEAD 比較・読み取りに使用。
- 1674：返却値を `protocol_rel` に変更。

既存 journal loop、テスト期待値、docs は変更していません。commit していません。

## 実走した検査と結果

- AST parse：成功、rc=0。
- `git diff --check`：成功、rc=0。
- `FLOOR_PROTOCOL_REL` 代入：1 件。
- `_run_git` / `_run_git_bytes` / `_run_git_z`：定義・subprocess 起動各 1 件。
- 必須 `use_perf_from_receipt` / `result_keys_for_mode` / `validate_manifest_v3`：呼出し各 1 件。

焦点走は Pegasus の規律に従い runner 経由で試行しました。

```sh
PYTHONPATH=. python3 tools/run_tests.py -q orchestrator/tests/test_s8b_holdout_freeze.py -p no:cacheprovider
```

結果は **rc=16、`qstat -Q preflight rc=1`、`child_started=false`**。pytest は開始されず、実走 nodeid・件数はありません。runner が `output/pegasus-dispatch/47ea5f58aec57c4e3088bb6861b78b52/receipt.json` を自動生成した旨を出力しました。

指定の `grep -n "record\." orchestrator/campaign/s8b_holdout_freeze.py` 結果：

```text
961:    if record.get("path") != rel:
962:        raise FreezeError(f"{field}.path 不一致: {record.get('path')!r}")
964:    if record.get("sha256") != actual:
966:            f"{field} sha256 不一致: recorded={record.get('sha256')} actual={actual}"
1241:            or known_record.get("path") != migration.KNOWN_AXES_REL
1242:            or known_record.get("sha256") != migration.KNOWN_AXES_RAW_SHA256):
1398:    protocol_rel = protocol_record.path
1399:    if protocol_record.commit_oid != head:
1609:        record for record in journal_records if record.get("event") == "session"
1618:        if record.get("event") in {"session-start", "session"}
1915:        if record.get("event") in {"session-start", "session"}
2032:    rel = _canonical_relative_path(record.get("path"), label=f"v1 {field}.path")
```

段 5 で追加した protocol 参照は新名へ移行済みです。裸の `record.path` / `record.commit_oid` / `record.raw_bytes` が残っていないことも AST で確認しました。

## 総括

F-5 は **実装済み・未実走**です。静的検査は成功しました。親側で修正後 bytes の焦点走をお願いします。