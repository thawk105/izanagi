A〜E を実装しました。docs・既存テスト期待値・git index・commit には触れていません。

変更箇所:

- [site_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/campaign/site_policy.py:66)
- [collect_wave_usage.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:150)
- [test_collect_wave_usage.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:90)

### 現行と変更後の挙動

| 対象 | 現行 | 変更後 |
|---|---|---|
| site 判定 | `PEGASUS_LOGIN` のみ `blocked` | `LOGIN`、`SUSPECT`、hostname 不明、Pegasus 名で NQSV 証拠欠落を `blocked`。既知の非 Pegasus と compute のみ収集 |
| `--out` | 現 worktree root 配下だけ拒否。本体 checkout・別 worktreeを受理 | 解決後 path の全祖先を走査し、`.git` file/dir があれば拒否 |
| CLI 非 gate | 公開関数の rc=0 のみ中心 | 実 process で必須引数欠落、project 0 件、repo 内出力、collector exit code 2 を固定 |
| M8 | collector の例外が捕捉され、誤呼出しを見逃し得る | 呼出しカウンタを直接 `0` と検査 |
| status 順位 | 実装は `missing` 優先だが組合せ未固定 | 0 call + limit、0 call + issues の両方で `missing` と理由を固定 |

### 静的な波及確認

- `current_site()` の既存 caller は無引数のため従来動作を維持します。`require_evidence=True` は新 helper のみ使用します。
- `_validated_out()` の consumer は `collect_wave_usage.py` 内部だけです。
- `test_site_policy.py` の既存期待値は変更していません。
- 共有 fixture `_patch_other_site` は新しい keyword 引数に対応しただけで、期待値の緩和はありません。
- subprocess の site 制御は `tmp_path` 内の `sitecustomize.py` に隔離し、機体固有 path を fixture に保存していません。
- repo 内の既存 docs、ledger 実装・テスト差分は変更していません。

## 総括

### (a) 対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| A. site fail-closed | **partial** | 実装・静的テスト済み。`reasons` と collector 0 回を固定。pytest 未実走 |
| B. repo 外検査 | **partial** | 全祖先の `.git` file/dir 検査と synthetic tmp fixture を追加。pytest 未実走 |
| C. 実 process 非 gate | **partial** | 指定4経路と `collector_exit_code == 2` の subprocess test を追加。pytest 未実走 |
| D. M8 呼出しカウンタ | **partial** | project 未指定・blocked の双方で `calls == 0` を追加。pytest 未実走 |
| E. status 優先順位 | **partial** | limit/issues 各組合せで `missing` 優先を追加。pytest 未実走 |

### (b) 走らせた検査と結果

- `git diff --check`: 成功
- 対象3ファイルの `ast.parse`: 成功
- staged 差分: なし
- `tools/run_tests.py` による対象 test、collect-only、site-policy 併走を計4回試行: すべて `qstat -Q preflight rc=1`、runner rc=16
- 実行された pytest nodeid: なし

したがって、A〜E はすべて「実装済み・未実走」であり、緑は主張しません。

### (c) 残した穴

- pytest の実走確認が dispatch infrastructure failure により残っています。
- 裁定どおり dangling symlink、repo-local import error、cwd 正規化、SIGKILL 時の temp、privacy lint 等には手を出していません。
- docs の既存未コミット差分はそのまま残しています。