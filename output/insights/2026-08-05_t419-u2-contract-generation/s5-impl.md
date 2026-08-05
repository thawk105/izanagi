現行の受理・拒否挙動は変更していません。`lookup()` は従来どおり 2 環境のみ受理し、未知・非 `str` を `EnvContractError` で拒否します。`REGISTRY` の値型も `ExecutionEnvironmentContract` のままです。

実装内容:

- 権限を持たない frozen `GenerationEntry` と immutable `GENERATIONS` を追加。
- leaf-level JSON Pointer 差分による `is_valid_successor()` を追加。path/SHA の同時変更だけを許可。
- 純関数 `validate_generations()` と、活性化権限未実装時の g2 bootstrap fuse を追加。
- 全世代 index を使う `resolve_by_contract_sha256()` を追加。形式・未知・非一意・env 不一致を拒否。
- `REGISTRY` を `GENERATIONS` の末尾から導出。`lookup()` 本体は未変更。
- 独立 hash golden、synthetic 世代列、resolver、loader grandfather pin のテストを追加。

静的確認では既存 19 箇所の `ec.lookup()` は削除・変更されておらず、新規テストで 2 箇所追加されただけです。production 21 caller（T-419 probe、`t126_driver`、floor/oracle/freeze/silo/pipeline/loop/scoping/trigger 各 module）は未変更です。

共有 fixture・`conftest.py` は変更していません。既存の env-contract consumer test 17 files は module 初期化検証の波及候補ですが、`REGISTRY`/`lookup()` の公開挙動は維持しています。

pytest、import、py_compile は実行していません。`git diff --check` のみ静的確認済みで、状態は「実装済み・未実走」です。commit も作成していません。

## 総括

- 変更: [env_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-contract-generation/orchestrator/campaign/env_contract.py)
- 変更: [test_env_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-contract-generation/orchestrator/tests/test_env_contract.py)
- 追加 API: `GenerationEntry`, `GENERATIONS`, `is_valid_successor`, `validate_generations`, `resolve_by_contract_sha256`
- g1 literal・既存 hash golden・`lookup()`・consumer は静的に維持
- docs、凍結成果物、他 production module は未変更
- テストは実装済み・未実走、commit なし