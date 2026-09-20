## 変更差分

指定2ファイルに実装済みです。署名済み受理式・固定診断を追加し、構造化正例、負例、文法同期検査、既存テストの parameterize を反映しました。

`git diff --stat`:

```text
 orchestrator/campaign/s8b_ratified_freeze.py   |  45 +++++-
 orchestrator/tests/test_s8b_ratified_freeze.py | 213 +++++++++++++++++++++++--
 2 files changed, 238 insertions(+), 20 deletions(-)
```

`git status --porcelain --untracked-files=all`:

```text
 M orchestrator/campaign/s8b_ratified_freeze.py
 M orchestrator/tests/test_s8b_ratified_freeze.py
```

## 実走結果

- 2ファイルの `python3 -m py_compile`: 成功。
- `git diff --check`: 成功。
- 指定の焦点選択を `tools/run_tests.py` 経由で試行: rc=16。`qstat -Q preflight rc=1` により、テスト子プロセスは未起動。実走 nodeid・件数はありません。

## 変異期待の確認

assert の静的読解による対応です。KILLED の実測ではありません。

| 変異 | 検出する検査 |
|---|---|
| m1 | 本文＋末尾同値の helper 直接診断比較 |
| m2 | 本文のみの parse 件数診断比較 |
| m3 | 構造化2行の直接診断比較 |
| m4・m5 | 末尾空白／小文字 key の canonical 診断比較 |
| m6〜m8 | 非構造化値／予約 product／model・reasoning=none の exact reason |
| m9 | none＋適合構造化行の exact reason |
| m10・m11 | merge／ancestry の exact reason |
| m12 | `generation-commit-none` の exact reason |
| m13〜m15 | approval diff／pointer diff／pointer parent の exact reason |

静的には検出不能な変異を認めませんでした。ただし、m2 のガード単純削除は `IndexError`、m6 の不適合ガード単純削除は `AttributeError` による失敗が想定され、受理成功への変化とは区別が必要です。

## 静的列挙 (所有外 caller・共有 fixture・consumer test への波及)

既存関数の本文比較で、変更は `_assert_user_commit` のみでした。

- approval／pointer／revocation／cancellation の4呼び手は逐語不変。
- `_is_none_commit`、`_assert_candidate_commit`、diff／親関係検査は逐語不変。
- `_add_generation` の `claude-opus`、共有 fixture は不変。
- runtime の `tools` import は追加していません。checker import は同期テスト内のみです。
- A/X record・所有外 consumer test・docs は変更していません。

## 未実走・限界

pytest、全走、変異実走は未実施です。親の dispatch で確認が必要です。文法同期テストも構文検査までで、判定一致の実測は未了です。

## 総括

**実装済み・未実走**です。構文検査と差分検査は成功しました。commit・add・push は行っていません。