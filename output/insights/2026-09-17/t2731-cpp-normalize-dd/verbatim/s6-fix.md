## 所見ごとの対応表 (A6-1 / A6-2)

| 所見 | 状態 | 対応 |
|---|---|---|
| A6-1 | partial | 例外の `match` と `getattr` による cleanup を指定どおり修正。実走待ち。 |
| A6-2 | closed | 比較式は不変だが、未使用指令も差分素材となり受理集合が狭まる旨を追記。 |

## 変更した file と差分の要約

- `orchestrator/campaign/source_digest.py`: docstring に 2 行追記。
- `orchestrator/tests/test_campaign.py`: 拒否理由の署名固定と cleanup 修正。

`git diff --stat`: 指定の 2 file のみ、4 行追加・2 行削除。`git diff --check`: 成功。

## 実走した nodeid と結果 (緑 / 赤 / 未実走)

`orchestrator/tests/test_campaign.py::test_source_digest_cpp_environment_prefix_mismatch_fails_closed`

**実装済み・未実走**。pytest 起動を試みましたが、PreToolUse hook が Pegasus ログインノードでの直接実行を拒否しました。親の計算ノードでの実走が必要です。

## 総括

製品の挙動・受理集合を変えず、指定の 2 点を修正しました。commit・push・stash は行っていません。