## 総括

- `ruling.md` の v2-1〜v2-6を、指定された4ファイルだけに実装しました。
- release 条件は `release_safe and not retryable_same_request` のみに限定しています。
- provenance rc=29は checker 非0と timeout・例外・binding失敗を区別しました。
- receipt digest、wave slug、`main_sha` の3段階で release 権限を束縛しました。
- stdout JSONを flushした後に releaseし、結果はstderrの1行だけへ出します。`lease_release` はJSONに含めません。
- docsは未編集、commitも未作成です。HEADは `e44aa4f96429e59ee30dbe0b8691f612905f4759` のままです。
- テストは実装済みですが、Pegasus dispatch障害により未実走です。

### return site の宣言

既定値は `(release_safe, retryable_same_request) = (False, False)` です。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:140)

| 到達点 | 宣言 | merge / fold / receipt の確認根拠 |
|---|---:|---|
| fold state読取失敗 | `(False, True)` | merge前、active state不明、receipt完全検証前。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:1722) |
| dirt・identity・audit等のlocked preflight拒否 | active planなしなら `(True, False)`、ありなら `(False, False)` | merge前。active planを読んだ後の検査だけを明示分類。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:1731) |
| stale-main | `(True, False)` | lock内照合のみ、active planなし、merge前。receiptはrelease権限snapshotのみ。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:1759) |
| provenance checker完走・非0 | `(True, False)` | merge前、checker returncodeを直接確認。receipt完全検証前だがdigest snapshot済み。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:1998) |
| provenance timeout・例外・binding・中断 | `(False, True)` | 実行結果またはbindingが確定しない。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:1905) |
| successful landに`main_after`なし | `(False, False)` | main状態を確認できないためfail-closed。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2395) |
| fold成功 | `(True, False)` | fold postcondition後に構築され、finalize成功後だけ返る。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2472) |
| fold失敗・rollback成功 | `(True, False)` | ref・index・worktree復元、journal削除、`main_after == rollback_ref`を確認。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2508) |
| rollback不完了 rc=28 | `(False, False)` | journalまたは中間状態が残る。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2508) |
| fold finalize失敗 rc=30 | `(False, True)` | verified commit後だがjournal未finalize。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2526) |
| active recovery失敗 rc=27 | `(False, True)` | active transactionが残る各検査・復元経路。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2578) |
| active recovery成功 | `(True, False)` | postcondition検証とjournal finalize後。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2600) |
| merge postcondition失敗 rc=25 | `(False, False)` | mainが動いた可能性を除外できない。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2624) |
| not-landed rc=24 | `(False, False)` | merge操作後であり、release-safe権限には採用しない。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2655) |
|通常land成功 | `(True, False)` | ff-only後のHEAD・ref・clean・wave postcondition完了。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2695) |
| lock-busy | `(False, True)` | lock未取得、同一requestで再試行可能。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2714) |
| active transaction各preflight失敗 | `(False, True)` | journalがopen。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2864) |
| fold計画・no-fold検証・snapshot失敗 | `(True, False)` | receipt完全検証後、active planなし、merge前のread-only処理。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2992) |
| already-landed no-op | `(True, False)` | receipt完全検証後、mainはtested tip、active planなし。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:3043) |
|一般 `_Reject` | phaseに応じて上記3組 | rcから導出せず、明示フラグとactive planなしのquiescent phaseだけを使用。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:3145) |

Falseへ落としたのは、active state読取不能、active recovery/finalize失敗、rollback不完了または復元HEAD不一致、rc=25、rc=24、`main_after`不明、active planを読む前のhistory/config/target検査失敗です。予期しない例外は従来どおり伝播し、JSONもreleaseも実行しません。

### M0〜M15 / P1 のテスト対応

- M0・P1: `test_main_releases_owned_lease_after_success_and_preserves_core_result`
- M1・M15: `test_land_result_release_contract_defaults_fail_closed_and_is_in_json`
- M2: `test_main_requires_release_safe_and_not_retryable_same_request`
- M3: `test_main_unexpected_exception_or_interrupt_never_releases`
- M4: `test_fold_rollback_failure_reason_reports_preserved_state`
- M5: `test_finalize_failure_keeps_verified_fold_commit_and_never_rolls_back`
- M6: `test_foreign_handoff_of_any_shape_is_protected_from_target_collision`
- M7: `test_provenance_checker_timeout_is_retryable_and_retains`
- M8: `test_provenance_checker_nonzero_is_release_safe_and_releases`
- M9・M13・M15: `test_main_binds_release_to_wave_main_and_flushed_core_json`
- M10: `test_non_owner_release_never_removes_lease`
- M11: `test_release_expected_main_sha_does_not_delete_reclaimed_same_slug`
- M12: `test_main_receipt_digest_change_blocks_release`
- M14: `test_release_failure_never_overwrites_land_result`

新設nodeは上記のうち `test_land_result_release_contract_defaults_fail_closed_and_is_in_json` から `test_release_failure_never_overwrites_land_result` までの9件と、`test_release_expected_main_sha_does_not_delete_reclaimed_same_slug` の計10件です。既存nodeにも stale、lock busy、rc=21、rc=24〜30、rollback、active recovery、fold preflightのbool固定を追加しました。

### 検査結果

実装済み・未実走です。

`python3 tools/run_tests.py` で重点16 nodeを指定しましたが、子pytest起動前に終了しました。

- dispatch rc: `16`
- 理由: `qstat -Q preflight rc=1`
- stderr: `Unknown user-id`
- 実際に走ったnodeid: 0件

静的検査は次を通過しています。

- `git diff --check`
- 対象4ファイルのAST parse
- plain runner対象の新規9 testが全て引数なしであること
- 変更ファイルが指定4ファイルだけであること

### caller・fixture・consumerへの波及

`release()` の既存callerは次のとおりです。

- CLI wrapper: optional引数を省略したままなので旧挙動と同一。[wave_land_window.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/wave_land_window.py:969)
- `tools/dev_wave_wait.py::_release_once`: 上記CLIを呼ぶため旧挙動のまま。[dev_wave_wait.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_wait.py:2333)
- test helper `_release`: 上記CLIを引数追加なしで使用。[test_wave_land_window.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/orchestrator/tests/test_wave_land_window.py:94)
- 新caller `dev_wave_land.main()` だけが `expected_main_sha=tested_main_sha` を指定します。[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:3243)

共有fixtureは `_Repo`、`_Repo._acceptance_receipt()`、`_land_cli_argv()`、`_FakeFoldModule` を再利用し、既存hashや揮発payloadを期待値へ焼き込んでいません。

production consumerの `wave_land_window.message()` は従来どおり `status` と `main_after` だけを読み、新しい2 boolを無視します。[wave_land_window.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/wave_land_window.py:891) repo外の既知5 scriptもstatus-only、t1142のloopはrc-onlyなのでschema追加では壊れません。ただし、それらがrelease失敗や新boolを認識しない残余は静的に残ります。

### 受理・拒否集合

現行の受理は、厳密なacceptance receipt、完全なaudit closure、full-history provenance、clean/identity/control検査、ff-only、fold postcondition/finalizeを全て通る経路と、既存のalready-landed no-opです。

現行の拒否は、receipt不成立、dirt/collision、identity/config/history不成立、audit/provenance拒否、stale-main、lock競合、fold/recovery/finalize失敗、land postcondition失敗です。

これらの判定関数、rc、status、ff-only、fold、lock、TTL、FIFO、待ち札、通知の意味論は変更していません。追加したのは結果の2 boolと、結果確定後の条件付きlease releaseだけです。