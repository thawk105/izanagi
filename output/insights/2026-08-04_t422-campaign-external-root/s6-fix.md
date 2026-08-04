指定された F-1〜F-10 を所有範囲内で修正しました。pytest は未実走のため、テストの緑は主張しません。

### 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| F-1 | closed | `..` component を拒否。resolve 前後で固定 suffix を lstat walkし、既存 resolved base の directory 型も検査 |
| F-2 | closed | `exploration/campaigns` と `exploration/autonomous-trials` の双方を resolve 前後で検査 |
| F-3 | closed | pin と lock を `sys` 上の単一 process singleton に統合。二重 alias の drift 負例を追加 |
| F-4 | closed | singleton lock 内で env 読取、admission、比較、pin を原子的に実施。lock 利用を thread で固定 |
| F-5 | closed | WAL の `append/log`、`write_lock`、`acquire_lock_atomic` の mkdir 直前に worktree gate を追加 |
| F-6 | closed | 8c の env 未設定時は従来の `ROOT/output/...`、設定時だけ resolver を使用 |
| F-7 | closed | F98 fake evaluator を有効な pre-build abort に変更し、policy 付き `wal.replay` 成功を期待値化 |
| F-8 | closed | `_effective_uid()` seam を追加し、共有 `os.geteuid` の monkeypatch を廃止 |
| F-9 | closed | 拒否文へ env 名、絶対 path、job 専用、base 形式の復旧策を追加 |
| F-10 | closed | campaign import scope が `finally` で `sys.path[:]` 全体を復元 |
| 回帰 | 未実測 | 静的検査では regressed 所見なし。pytest 未実走のため動的回帰は未判定 |

### 差分要約

現在の段5＋fix累積差分は、所有6ファイルで717行追加・7行削除です。

- [layout.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/layout.py:222): resolver hardening、process singleton、UID seam、診断改善
- [wal.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/wal.py:310): 3 materializer の worktree gate
- [p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/campaign/p3_autonomous_workload_trial.py:1757): 8c legacy default 復元
- [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_campaign.py:3610): resolver、alias、lock、8c、WAL gate の回帰テスト
- [test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/test_dev_wave_land.py:2698): replay-valid F98 正例と `sys.path` 隔離
- [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t422-campaign-external-root/orchestrator/tests/conftest.py:124): singleton reset を1回に単純化

docs、hooks、`tools/dev_wave_land.py`、`durable_root.py`、禁止された layout body、indexには触れていません。親の既存 docs 4ファイルの差分も保持しています。`git diff --cached` は空です。

### 受理・拒否挙動

- 明示 `output_root` / `--run-root` の優先順位と文字列は維持。
- env 未設定の exploration layout は従来の `repo_output_root()`、8c は従来の `ROOT/output` を使用。
- env root は、新たに `..`、両固定 suffix の symlink/non-directory、resolved base の非directoryを拒否。
- module alias や並行 thread を跨ぐ env drift を process singletonで拒否。
- worktree container 内では、`ensure()` 未呼出でも WAL lock・log作成を拒否。これは official layoutにも適用。
- 診断に `IZANAGI_EXPLORATION_OUTPUT_ROOT=<絶対 path の job 専用 base>` と、baseが`exploration/`自体ではない旨を表示。

### 所有外への波及可能性

- exploration resolver caller: `p3_kickoff.py`、`p3_s4_loop*.py`、`p3_s4_red.py`、`s8b_oracle_exploration.py`
- WAL materializer caller: `loop.py`、`pipeline.py`、`ident.py`、`guided.py`、`screening_driver.py`、`s8b_oracle_driver.py`等
- consumer test: exploration namespace、各P3 loop、autonomous trial、oracle、guided、screening、direct comparison系
- autouse fixtureは全orchestrator pytestへ波及しますが、削除するenvとreset対象は exploration root stateだけです。

### 静的検査

実行して rc=0:

- `python3 -m py_compile`（所有6ファイル、Python 3.10.12）
- `git diff --check`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- 新設テスト名を固定するF42 meta-testの静的検索：該当なし

pytest、`run_tests.py`、変異、受入全走は指示どおり実行していません。

触れなかった採用済み所見はありません。scope外の official/sweep 外部化、process跨ぎresume manifest、capability化・promotion receipt、親docsは変更していません。

## 総括

F-1〜F-10はコードと純増・強化テスト上でclosedです。所有・禁止境界を維持し、必須静的検査は通過しました。動的な合否は未判定であり、親による計算ノード上の関連pytest・変異・受入再走が必要です。