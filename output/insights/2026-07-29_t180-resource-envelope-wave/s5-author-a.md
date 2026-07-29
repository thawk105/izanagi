実装を完了しました。commit・docs 編集・単位 B のファイル変更はありません。

### 現行の受理・拒否挙動

- Codex rc=0、validator rc=0、rollout/stdout metering 一致、manifest membership、hash、終了確認、全上限内をすべて満たす場合だけ受理します。
- metering 欠落・不一致、`cached_input_tokens > input_tokens`、process group 残存、validator 失敗は非採用です。
- `limit_trigger` がある attempt は、SIGTERM handler が正常成果物を書いても受理しません。
- retry は read-only 限定です。workspace-write の複数 attempt は argparse 相当 rc=2 です。
- receipt と manifest は temp・fsync・atomic replace、checker は hash・validator・metering・membership を再計算します。

### 変更範囲

- [tools/codex_worker_launch.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t180-author-a/tools/codex_worker_launch.py:1)
- [test_codex_worker_launch.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/t180-author-a/orchestrator/tests/test_codex_worker_launch.py:1)

fake Codex は正常、metering 欠落、ID 遅延・変化・複数 session、rollout 欠損、SIGTERM 無視、`setsid()` 脱出、TERM 後正常出力、late writer を再現します。実 Codex は呼びません。

### 検査結果

- `python3 -m pytest orchestrator/tests/test_codex_worker_launch.py -q -rf`
  - ファイル全体、30 passed
  - M1〜M11、M16: 指定名の各 node
  - P1: `test_positive_p1_normal_job_is_accepted`
  - P3: `test_positive_p3_exact_limit_natural_exit_is_accepted`
- `python3 -m pytest orchestrator/tests/test_check_docs.py -q -rf`
  - ファイル全体、134 passed
- `python3 -m py_compile ...`: rc=0
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0

### 未了 finding

R5 の「同一 attempt で観測した全 session を manifest に記録」と、凍結 schema の「`(job_id, attempt_index)` 一意」は同時に満たせません。現在は全 `session_ids` を launcher-error receipt に保存し、manifest の部分追記を拒否します。

完全解消には、manifest を `(job_id, attempt_index, session_id)` 一意へ変更するか `session_index` を追加し、単位 B の独立 parser と同時に再凍結する裁定が必要です。

波及可能性は、単位 B の manifest parser、将来の DW-O01 caller、T-184 の policy 結線、親が追加する consumer test です。共有 fixture への変更はありません。

## 総括

- 実装: R1–R3、R6–R9、R12–R15、R19、R20、launcher 側 R4 相当検査、凍結 manifest schema。
- R5: receipt lineage は実装済み、複数 session の manifest 表現だけ仕様矛盾により fail-closed。
- 検査: launcher 30/30、meta-test 134/134、静的 gate すべて rc=0。
- 未了: manifest 一意制約の親裁定と単位 B との同期。
- 変更は指定 2 ファイルのみ。docs・ledger・commit は未実施。