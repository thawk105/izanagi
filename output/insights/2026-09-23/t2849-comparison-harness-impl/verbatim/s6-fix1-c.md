[tools/t2849_llm_round.py:142](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2849-fix1-c/tools/t2849_llm_round.py:142) を修正しました。

| 所見 | 状態 | 修正 |
|---|---|---|
| T6 | partial（実装済み・未実走） | `RoundTool.cmd_proposal` で preflight を既存の `validate_backoff_implementation` に置換 |

変更前は型・サイズだけを確認し、`double now_backoff = 1 + 2;` を受理していました。変更後は strict literal 文法に違反する実装を公開前に拒否します。正常な literal は引き続き受理する設計です。

- 差分：production 追加1行・削除1行、test変更0行。期待値変更なし。
- `git diff --check`：成功。
- 所有外への波及：handshake consumer に届く proposal が文法検査済みになる。共有fixture・consumer test・interfaceの変更不要。
- commit・branch操作なし。

試行したコマンド：

```bash
PYTHONPATH=. timeout 300 python3 -m pytest -q -p no:cacheprovider -rf orchestrator/tests/test_t2849_llm_round.py
```

実走した nodeid はありません。確認対象は同ファイルの全件、特に `test_normal_schema_and_grammar_rejection[implementation-double now_backoff = 1 + 2;]` です。

## 総括

T6 の実装修正は完了、closed 判定は親の焦点走待ちです。所有外の必要変更はありません。U-C の登録変異対応は以下のとおりで、今回の kill 実測はありません。

| 変異 | 位置 | 検出予定 nodeid（ファイル内） |
|---|---|---|
| M23 | job body harness 分岐の lock 設定 | `test_t2849_job_contract.py::test_harness_bench_lock` |
| M24 | 同分岐の終了処理 | `test_t2849_job_contract.py::test_harness_single_driver` |
| M25 | `RoundTool.cmd_inputs` | `test_t2849_llm_round.py::test_prior_observations_both_roles` |

実行制御の PreToolUse `guard_bash` が、上記pytestを「Pegasusログインノードでの重量処理」として拒否しました。共通指示に従い、未実走として報告します。