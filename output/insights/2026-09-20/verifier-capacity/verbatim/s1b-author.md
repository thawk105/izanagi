## 総括

[probe/verifier_profile_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/vcap-s1probe/probe/verifier_profile_probe.py) のみ編集しました。`compare`・`_verify_child`・`summarize-compare` を追加し、前提検査・復元・edge wrapper・sampler・`timed_process` を共用しています。差分は未 commit で残しています。

- 行数: **1205**
- SHA256: `17ad243e45baef589306f50f016915b5ba83a3f3baf14f915589b68b54ed830a`

指定 selftest は **9 PASS / 0 FAIL / 0 SKIP、rc=0**。

```text
PASS (a) run rc=0
PASS (b) phase start/end pairs
PASS (c) samples required keys
PASS (d) completed, peaks, estimates
PASS (e) summarize Markdown
PASS (f) serializable=True
PASS (g) restore mismatch rc=4
PASS (h) compare workers 1/2, identical wire/full, serializable, commit witnesses
PASS (i) integrity.notes diff path and unequal wire/full
```

`ast.parse`、3 subcommand の `--help`、`git diff --check` も成功しました。失敗経路 7 種は模擬呼出しで確認し、usage エラーでは実際に rc=2・`compare.json`・両側 samples の生成を確認しました。

`full_fields_json` に含める非 wire field は `Integrity.expected_commits`、`Integrity.observed_commits`、`Integrity.proof_surfaces`。後者の `protocol`・`lock_coverage`・`permutation`・`write_intent` も保持します。

未実走は計算ノード経路、旧新の実 tree、大規模保全 trace。pytest・build・compute 投入は行っていません。

判断点は、旧側未完走時には新側を起動せず停止すること、SCC wall に既存同様 `n_edges` 走査を含めること、node used peak は既存 `run` 同様の開始時差分とすることです。usage の専用 stop_reason が仕様にないため、rc=2 と `error` に詳細を残し、`stop_reason="old-failed"` としています。