## 総括

**実装前に停止しました。ファイル変更・commit はありません。** 次の矛盾と所有外 caller を検出しました。

- [既存テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t548-a-procure/orchestrator/tests/test_pegasus_thirdparty_fetch.py:814) が `verify-deps` の成功と shallow の受理を要求しています。命令廃止にはこの期待値の変更が必要ですが、依頼は期待値の反転・削除を禁止しています。
- 裁定の対象一覧にない [b4_binary_record.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t548-a-procure/orchestrator/campaign/b4_binary_record.py:75) が `verify-deps` を実際に呼びます。対応テストも同命令を要求しています。裁定 §2.3 の「一覧外の読み手を見つけたら報告して止める」に従いました。

実走結果（すべて**変更前**）：

| nodeid／範囲 | 結果 |
|---|---|
| `orchestrator/tests/test_pegasus_thirdparty_fetch.py::*`（自走 harness 全57ケース） | 57 passed、rc=0 |
| `orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted` | PASS |
| 同 `::test_allowlist_has_no_stale_or_self_runnable_entries` | PASS |
| 同 `::test_this_metatest_is_itself_self_runnable` | PASS、harness rc=0 |
| `orchestrator/tests/test_t126_pegasus_tools.py::test_shared_pegasus_policy_owns_no_t126_qualification_keys`（関数直接実行） | PASS、rc=0 |

直接実行の準備コマンドは入力ミスで2回 rc=1、その後修正して上記 node を実走しました。top-level key 検査は `t126_` 接頭辞の禁止と bytes golden で、旧 key 名の許可リストではありません。

policy の実測 SHA256：

```text
a8806c4a4da81f2cbadcb5cbeee54ce7c1106bd0d291c1a2725f86b8b8a8032a
```

指定の `3a3c7d607de77e23368f9ce382b41e6e524de3ee1e2809e7c6d890ada95a6c90` とは**不一致**です。未編集なので変更前の値です。

受理・拒否挙動は**変わりません**。現行 `verify-deps` は origin を照合せず shallow を許容します。予定の新経路ではこの受理集合を縮小し、origin 不一致・shallow を拒否しますが、未実装です。

静的な波及先は、裁定記載の shell／PBS 15本、Python consumer 4本、`mocc_trace_v1_policy.json`、README、指定の期待赤5ファイルに加え、**`b4_binary_record.py`、`test_b4_binary_record.py`、`test_hooks.py`** です。調達テスト内の共有 `git_fixture` も旧 locator を生成しています。

指定の期待赤5ファイル全体は未実走で、赤の突き合わせは未完了です。実走テストの赤はありません。ネットワーク clone、新経路の検証・実装も未実施であり、完了・closed とは申告しません。