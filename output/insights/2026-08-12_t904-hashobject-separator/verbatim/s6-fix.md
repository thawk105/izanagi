[対象テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t904-hashobject-sep/orchestrator/tests/test_codex_reasoning_ab.py:1418)だけを修正しました。production、docs は変更せず、commit も作成していません。Web 検索は未使用です。

### 修正内容

- fixture で `root.txt` が `root\n` として commit 済みであることを確認。
- `-answer`:
  - 新規内容では `reasons == []`。
  - その後 `root.txt.read_bytes()` で上書きし、reason リストを完全一致で検査。
- `--stdin`:
  - `root.txt` と同じ reachable bytes を使用。
  - reason リストを完全一致で検査。
  - 修正前の empty stdin による fail-open を説明する docstring を追加。
- `hash-object -w` は両テストから削除。

### 受理集合の変化

- `test_leading_dash_untracked_path_is_hashed_as_path`: production の `"--"` を削除すると、相 (a) の本来受理される snapshot が rc=129 `ValidationError` で拒否され、受理→拒否となる。
- `test_option_named_untracked_path_is_hashed_not_stdin`: `"--"` を削除すると `/dev/null` の空 stdin を hash して `reasons == []` となり、本来拒否される混入 snapshot が受理される fail-open になる。

### 検査

実装済み・未実走です。次の nodeid を `tools/run_tests.py` へ投入しましたが、pytest 起動前に `qstat -Q preflight rc=1`、rc=16 で拒否されました。迂回していません。

- `orchestrator/tests/test_codex_reasoning_ab.py::test_leading_dash_untracked_path_is_hashed_as_path`
- `orchestrator/tests/test_codex_reasoning_ab.py::test_option_named_untracked_path_is_hashed_not_stdin`

静的検査は成功しました。

- `git diff --check`
- Python AST parse
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

### 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| BLOCKER: unreachable blob により受理集合差を証明しない | partial | reachable blob に変更済み。実走できていないため closed とはしない |
| MAJOR: replay consumer 未検証 | partial | 親の受入全走対象。今回の所有範囲外 |
| MAJOR: symlink の durable 記録 | partial | 段7の親担当。docs 編集禁止に従い未変更 |
| MINOR: mutation collection の実 node 未確認 | partial | dispatch 防壁により未実走 |
| NIT: 新設 node の時間未測定 | partial | 実走不能のため未測定 |
| 回帰 | regressed なし | 編集対象は指定テストファイルのみ |

## 総括

- dangling blob を廃止し、HEAD reachable な `root.txt` blob で受理集合差を固定した。
- 2 テストとも reason リストを完全一致で検査する。
- pytest は dispatch infrastructure failure のため実装済み・未実走。
- production・docs・既存期待値は変更せず、commit と Web 検索も行っていない。