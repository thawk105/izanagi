実装完了です。編集は指定された 2 ファイルのみで、docs・単位 A・commit には触れていません。

| 所見 | 状態 | 対応 |
|---|---|---|
| A-6 | closed | manifest entry に一致する rollout が複数あれば、`--strict` なしでも rc=2 |
| A-1 ledger 側 | closed | 累積 token counters または派生 `cli_reported` の巻き戻りを `usage_cumulative_rollback` として検出。strict 時 rc=2 |
| 受入固定 | closed | 合成 manifest 10 entry で 10 session / 434 calls / 2,757,982 tokens と stage 別 6 値を固定 |
| 回帰 | regressed なし | 既存 103 test を含む全 106 test が通過 |

変更箇所は [codex_worker_ledger.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t180-author-b/tools/codex_worker_ledger.py:384) と [test_codex_worker_ledger.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t180-author-b/orchestrator/tests/test_codex_worker_ledger.py:526) です。

受理集合の変更は以下です。

- 変更前: manifest 1 entry に三者一致 rollout が複数あっても、issue を出すだけで非 strict は rc=0。
- 変更後: 同入力は strict の有無にかかわらず rc=2。
- 変更前: `total_tokens` が増加していれば、`cli_reported` が 1000→2 に巻き戻っても strict で受理。
- 変更後: `usage_cumulative_rollback` を出し、strict では rc=2。非 strict は既存 issue 規約どおり rc=0。
- 健全な legacy invocation の出力 schema・集計値、および健全な manifest 集計値は不変です。

検査結果:

- 焦点 5 node: `5 passed`
  - `test_cli_reported_cumulative_rollback_fails_strict`
  - `test_manifest_duplicate_rollout_fails_without_strict`
  - `test_manifest_t179_frozen_synthetic_stage_aggregates`
  - `test_non_monotonic_cumulative_and_event_counters_are_exposed`
  - `test_legacy_selector_t179_frozen_golden_without_manifest_p2`
- 指定全走: `python3 -m pytest orchestrator/tests/test_codex_worker_ledger.py -q -rf` → `106 passed in 0.47s`
- `git diff --check` → rc=0
- `check_codex_agents.py` → rc=0
- `check_docs.py` → rc=0

静的な波及可能性:

- 単位 A の launcher が生成する manifest に重複 rollout があれば、ledger consumer は新たに rc=2 を受けます。これは意図した fail-closed 変更です。
- `issues` の category を列挙する外部 consumer は、新しい `usage_cumulative_rollback` を扱う必要があります。リポジトリ内に直接 caller は見つかりませんでした。
- 共有 fixture は変更せず、追加テストは既存の合成 helper のみを利用しています。
- `tools/codex_worker_launch.py` とその consumer test はこの worktreeに存在せず、変更していません。
- 既存の段 5 差分は staged、今回の fix は unstaged の状態です。commit は作成していません。

## 総括

- closed 3件 / partial 0件 / regressed 0件。
- 焦点 5 node: 5 passed。
- 指定全範囲: 106 passed。
- 補助検査 3種: すべて rc=0。
- 未了なし。