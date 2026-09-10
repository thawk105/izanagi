## 実装結果

親裁定のプラン v2 を指定された 2 ファイルへ実装しました。

変更前は、正常 job が output 公開後の audit／receipt staging 中に wall 予算を超えても `accepted / rc=0` になりました。既存の not-accepted／launcher-error job は各理由で拒否されていました。

変更後は、publication I/O が成功した論理 job について、audit／staging 後の超過だけが `not_accepted / max_wall_clock_s / rc=1` へ移ります。既存の拒否分類や正常な accepted 集合は拡大していません。

## Production 変更

[tools/codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/tools/codex_worker_launch.py:30) で次を変更しました。

- launcher 局所の `_monotonic_ns()` seam を追加し、module 内の直接呼出しを集約。
- `_stage_receipt_write()` が fsync 済み temp `Path` を返すよう変更。
- `_atomic_create_json_reserved()` が staged temp を受け取り、成功・例外とも cleanup する所有契約を docstring に固定。
- accepted 経路を output 公開→hash 照合→published audit→staging→late latch→同一 temp 公開の順序へ変更。
- flip 時は staged temp と output を削除し、output 親 directory を fsync 後に flag を戻して receipt を再構築。
- launcher-error fallback の output 削除にも親 directory fsync を追加。
- `actuals.wall_clock_s` と late gate の観測時刻が異なることを docstring に明記。

schema v2、receipt field 集合、`wall_clock_scope` literal、writer/checker truth table は変更していません。

## 追加テスト

[orchestrator/tests/test_codex_worker_launch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t678-publication-wall-gate/orchestrator/tests/test_codex_worker_launch.py:2077) に以下を追加しました。

- N1: staging 後の論理時刻超過、output・temp 残骸の撤去。
- N2: published output audit 後の論理時刻超過。
- N3: staged `Path` と inode がそのまま publication helper に渡ること。
- N4 `test_positive_p1_normal_job_is_accepted` は変更していません。

時間予算の既定値と外側 timeout 10 秒も変更していません。専用 meta-test は静的検索上ありませんでした。

## 検査

焦点 node は `tools/run_tests.py` で 2 回投入しましたが、いずれも `qstat -Q preflight rc=1`、runner rc=16 で dispatch 前に停止しました。テスト本体は未実走です。

対象 nodeid:

- `test_receipt_staging_wall_overrun_flips_to_not_accepted_and_removes_output`
- `test_receipt_audit_wall_overrun_flips_to_not_accepted`
- `test_accepted_publication_reuses_the_staged_receipt_temp`
- `test_positive_p1_normal_job_is_accepted`

直接 pytest には迂回していません。したがって状態は「実装済み・未実走」です。

非テスト検査は以下が rc=0 でした。

- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- `git diff --check`

## 静的な波及可能性

- repo 内に production executable caller はなく、現在の直接影響は dogfood receipt と将来の `DW-O01` 結線です。
- private helper の signature 変更は `_publish_complete_receipt`、launcher-error fallback、既存 publication-failure monkeypatch、create-only race test に波及します。
- 共有 fixture の `max_wall="3"`、evidence `1.0`、termination `0.05`、timeout `10` は不変です。
- create-only publication syscall 以降の未計測区間と、親裁定が scope 外とした S-A〜S-G は未修正です。

## 総括

- 変更: `tools/codex_worker_launch.py` の clock、staging、atomic create、supervised/fallback publication。
- 変更: `orchestrator/tests/test_codex_worker_launch.py` に N1–N3 を追加。
- N4・schema・literal・truth table・時間予算は不変。
- 編集は指定 2 ファイルのみで、docs・新規ファイル・commit・git add はありません。
- 焦点 4 node は dispatch 障害により実装済み・未実走です。
- 残存リスクは未実走と、create-only publication 後の不可逆な残余区間です。