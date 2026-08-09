実装済みですが、pytest は実行基盤障害により未実走です。commit は作成していません。

## 総括

- (a) 実装内容

  - [tools/dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/tools/dev_wave_land.py:52) に `RC_PROVENANCE = 29` を追加。
  - lock 外で full-history checker を実行し、tip SHA・checker blob SHA・return code を receipt に束縛。
  - checker の wave root・`tools/`・leaf を `O_NOFOLLOW` 相当の FD で監査中まで束縛。
  - argv、環境、標準入出力、`shell=False`、`close_fds=True`、`timeout=3900` を固定し、起動失敗・timeout・想定外例外を rc=29 に変換。
  - lock 内で receipt の3条件を照合。active fold recovery は新規 commit を admit しないため照合対象外とするコメントを追加。
  - [test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-provenance-known-violation/orchestrator/tests/test_dev_wave_land.py:122) の共有 fixture に tracked checker stub を追加。
  - M1〜M9、通常 land 正例、provenance 赤での active recovery 正例、clean commit の checker 欠落・leaf/ancestor symlink 負例を追加。
  - docs、`tools/check_ai_provenance.py`、既存テスト期待値は変更していない。commit も未作成。

- (b) 検査結果

  - 新設8 nodeid、`test_dev_wave_land.py` 全体、plain-runner meta-test 3 nodeidを `tools/run_tests.py` へ投入したが、すべてテスト開始前に `qstat -Q preflight rc=1`、runner rc=16 で停止。
  - 対象 nodeid:
    - `test_provenance_gate_accepts_tip_zero_and_lands`
    - `test_provenance_gate_rejects_tip_nonzero_before_ff`
    - `test_provenance_audit_runs_before_global_lock`
    - `test_provenance_receipt_rejects_each_bound_field`
    - `test_provenance_receipt_rejects_tip_that_moves_during_audit`
    - `test_provenance_subprocess_contract_and_exception_mapping`
    - `test_provenance_checker_missing_and_symlink_components_are_rejected_clean`
    - `test_active_transaction_recovery_completes_with_provenance_red`
  - meta-test:
    - `test_every_test_file_is_self_runnable_or_allowlisted`
    - `test_allowlist_has_no_stale_or_self_runnable_entries`
    - `test_this_metatest_is_itself_self_runnable`
  - したがって結果は「実装済み・pytest未実走」。テスト緑や要件 closed は主張しない。テスト赤は未観測で、内訳は実行基盤 rc=16 のみ。
  - AST 構文検査、`git diff --check`、`tools/check_codex_agents.py`、`tools/check_docs.py` は成功。
  - 親 docs 未 land に由来する expected finding は事前想定なし。

- (c) 残る risk・波及可能性

  - 親側で新設 nodeid、同テストファイル全体、meta-test、受入全走を再実走する必要がある。
  - 全通常 land caller は、lock 取得前に最大3900秒の監査と新しい rc=29を受ける。runbook、CLI利用者、supervisor の rc consumer に波及し得る。
  - 共有 `_Repo` fixture を使う既存 land、CLI E2E、Git wrapper、FD継承、race、resync、fold consumer test は追加 subprocess／blob照合の影響対象。
  - tip 側 helper/checker が可変である cooperative trust root、直接 main 更新など land helper 外の経路は、段4裁定どおり scope 外の残余 risk。