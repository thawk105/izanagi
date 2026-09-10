## 総括

- F1〜F8 はすべて実装と kill node の追加まで完了しました。
- F3 は安全側の選択肢 (b) とし、rollback 成功後も lease を保持します。
- provenance は checker が違反を返す rc=1 だけを決定的拒否としました。
- receipt と Git の一時 I/O 失敗は retryable、構造的不正は非 retryable に分離しました。
- docs は編集せず、commit も作成していません。差分は許可された 4 file だけです。
- pytest は dispatch infrastructure failure のため未実走です。緑とは報告しません。

### F1〜F8 対応表

| 項目 | 状態 | 対応 |
|---|---|---|
| F1 | closed | rc=1 のみ決定的拒否。rc=16、負値、その他非 0 は retryable |
| F2 | closed | 内部 `KeyboardInterrupt` を retryable として保持。rollback、finalize、provenance の中断経路も解放不可 |
| F3 | closed | 選択肢 (b)。rollback 成功後を `(False, False)` に固定 |
| F4 | closed | receipt I/O と Git 実行失敗を retryable。JSON/schema/path shape など構造不正は非 retryable |
| F5 | closed | post-provenance で active plan を再確認してから rc=21 を分類 |
| F6 | closed | JSON を compact separators で出力し、64 KiB 上限は不変 |
| F7 | closed | 両 bool を `compare=False` とし、既存 equality 意味論を維持 |
| F8 | closed | M3、M6 完全集合、M12 両分岐、F1/F3/F4 の kill node を追加 |
| 回帰実走 | partial | wrapper の rc=16 により pytest 本体は未起動 |
| regressed | なし | 静的検査で既知の退行なし。動的確認は未完 |

### 修正箇所

- F1: [`tools/dev_wave_land.py:66`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:66)、[`tools/dev_wave_land.py:2060`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2060)
  - checker 自身は rc=2 を実行不能として返し、rc=1 だけを違反、rc=0 を違反なしとしています。[`tools/check_ai_provenance.py:2562`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/check_ai_provenance.py:2562)、[`tools/check_ai_provenance.py:2579`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/check_ai_provenance.py:2579)、[`tools/check_ai_provenance.py:2623`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/check_ai_provenance.py:2623)
  - rc=16 は dispatch failure の予約値です。[`tools/check_ai_provenance.py:38`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/check_ai_provenance.py:38)
  - 負値は checker の通常 return ではなく signal 終了なので保持します。
  - node: [`test_dev_wave_land.py:5984`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/orchestrator/tests/test_dev_wave_land.py:5984)、[`test_dev_wave_land.py:6034`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/orchestrator/tests/test_dev_wave_land.py:6034)、[`test_dev_wave_land.py:6040`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/orchestrator/tests/test_dev_wave_land.py:6040)

- F2: [`tools/dev_wave_land.py:2551`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2551)、[`tools/dev_wave_land.py:2593`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2593)、[`tools/dev_wave_land.py:3036`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:3036)、[`tools/dev_wave_land.py:3105`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:3105)、[`tools/dev_wave_land.py:3150`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:3150)
  - `KeyboardInterrupt` を内部 catch した結果は `release_safe=False, retryable=True`。
  - `SystemExit` と未捕捉の `BaseException` は `LandResult` 化されず伝播するため release 処理へ到達しません。
  - node: [`test_dev_wave_land.py:6074`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/orchestrator/tests/test_dev_wave_land.py:6074)

- F3: [`tools/dev_wave_land.py:2577`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2577)
  - 選択肢 (b) を採用しました。現在の安価な検査では ref 以外の index、worktree、journal、symbolic HEAD を完全に証明できないためです。
  - node: [`test_dev_wave_land.py:6107`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/orchestrator/tests/test_dev_wave_land.py:6107)

- F4: [`tools/dev_wave_land.py:393`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:393)、[`tools/dev_wave_land.py:423`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:423)、[`tools/dev_wave_land.py:462`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:462)、[`tools/dev_wave_land.py:523`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:523)、[`tools/dev_wave_land.py:720`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:720)、[`tools/dev_wave_land.py:1807`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:1807)
  - `OSError` と Git command 非 0 は一律保持側です。Git stderr から恒久的不正と一時障害を確実に区別できないため、安全側へ倒しました。
  - JSON、schema、重複 key、path shape、symlink/non-regular などの構造的不正は非 retryable のままです。
  - node: [`test_dev_wave_land.py:6165`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/orchestrator/tests/test_dev_wave_land.py:6165)、[`test_dev_wave_land.py:6202`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/orchestrator/tests/test_dev_wave_land.py:6202)

- F5: [`tools/dev_wave_land.py:2861`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2861)
  - 再取得後に `_locked_preflight()` を完了し、active plan が無い場合だけ control replacement を `release_safe=True` にします。
  - active plan が存在する場合は保持します。
  - node: [`test_dev_wave_land.py:2362`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/orchestrator/tests/test_dev_wave_land.py:2362)

- F6: [`tools/dev_wave_land.py:3253`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:3253)
  - `separators=(",", ":")` を使用。
  - 回帰 fixture は旧 JSON 65,491 bytes、新 field を通常出力した場合 65,547 bytes、compact 後 65,526 bytesを固定しています。
  - 64 KiB 上限と `message()` の意味論は変更していません。
  - node: [`test_dev_wave_land.py:6361`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/orchestrator/tests/test_dev_wave_land.py:6361)

- F7: [`tools/dev_wave_land.py:142`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:142)
  - `release_safe` と `retryable_same_request` を `field(default=False, compare=False)` に変更。
  - equality 固定 node: [`test_dev_wave_land.py:5874`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/orchestrator/tests/test_dev_wave_land.py:5874)

- F8:
  - M3: [`test_dev_wave_land.py:6074`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/orchestrator/tests/test_dev_wave_land.py:6074)
  - M6 完全集合: [`test_dev_wave_land.py:1351`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/orchestrator/tests/test_dev_wave_land.py:1351)、[`test_dev_wave_land.py:2362`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/orchestrator/tests/test_dev_wave_land.py:2362)
  - M12 両分岐: [`test_dev_wave_land.py:6284`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/orchestrator/tests/test_dev_wave_land.py:6284)、[`test_dev_wave_land.py:6323`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/orchestrator/tests/test_dev_wave_land.py:6323)

### M0〜M15 対応

| 変異 | kill node |
|---|---|
| M0 | `test_main_releases_owned_lease_after_success_and_preserves_core_result` |
| M1 | `test_land_result_release_contract_defaults_fail_closed_and_is_in_json` |
| M2 | `test_main_requires_release_safe_and_not_retryable_same_request` |
| M3 | `test_internal_fold_planning_interrupt_is_never_release_safe`、外側伝播は `test_main_unexpected_exception_or_interrupt_never_releases` |
| M4 | `test_fold_rollback_failure_reason_reports_preserved_state` |
| M5 | `test_finalize_failure_keeps_verified_fold_commit_and_never_rolls_back` |
| M6 | `test_foreign_handoff_of_any_shape_is_protected_from_target_collision`、`test_post_provenance_reacquire_rejects_control_directory_replacement` |
| M7 | `test_provenance_checker_timeout_is_retryable_and_retains`、rc=16 node、signal node |
| M8 | `test_provenance_checker_violation_rc_is_release_safe_and_releases` |
| M9 | `test_main_binds_release_to_wave_main_and_flushed_core_json` |
| M10 | 既存 `test_non_owner_release_never_removes_lease` |
| M11 | `test_release_expected_main_sha_does_not_delete_reclaimed_same_slug` |
| M12 | `test_main_receipt_digest_change_blocks_release`、`test_main_verified_receipt_digest_mismatch_blocks_release` |
| M13 | `test_main_binds_release_to_wave_main_and_flushed_core_json` |
| M14 | `test_release_failure_never_overwrites_land_result` |
| M15 | `test_land_result_release_contract_defaults_fail_closed_and_is_in_json`、`test_main_binds_release_to_wave_main_and_flushed_core_json` |

追加の分類変異は、F3 rollback 成功の誤解放を `test_successful_fold_rollback_remains_held_fail_closed`、F4 retryable 除去を receipt/status の 2 node、F6 境界退行を compact JSON node が殺します。

### 新規 node

`test_dev_wave_land.py` に次の 17 node を追加しました。

- release contract: `test_land_result_release_contract_defaults_fail_closed_and_is_in_json`、`test_main_releases_owned_lease_after_success_and_preserves_core_result`、`test_main_requires_release_safe_and_not_retryable_same_request`、`test_main_unexpected_exception_or_interrupt_never_releases`
- provenance: `test_provenance_checker_violation_rc_is_release_safe_and_releases`、`test_provenance_checker_infrastructure_rc_is_retryable_and_retains`、`test_provenance_checker_signal_returncode_is_retryable_and_retains`、`test_provenance_checker_timeout_is_retryable_and_retains`
- fold/I/O: `test_internal_fold_planning_interrupt_is_never_release_safe`、`test_successful_fold_rollback_remains_held_fail_closed`、`test_receipt_read_io_failure_is_retryable_and_retains`、`test_locked_status_git_io_failure_is_retryable_and_retains`
- authority/output: `test_main_binds_release_to_wave_main_and_flushed_core_json`、`test_main_receipt_digest_change_blocks_release`、`test_main_verified_receipt_digest_mismatch_blocks_release`、`test_compact_core_json_preserves_legacy_64k_message_boundary`、`test_release_failure_never_overwrites_land_result`

`test_wave_land_window.py` には [`test_release_expected_main_sha_does_not_delete_reclaimed_same_slug`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/orchestrator/tests/test_wave_land_window.py:1250) を追加しました。

### 既存 node への変更

既存 node への変更は次の 4 件だけです。

| node | 変更 | 許可根拠 |
|---|---|---|
| `test_foreign_handoff_of_any_shape_is_protected_from_target_collision` | `(True, False)` assertion を追加 | M6 kill node として明示許可 |
| `test_post_provenance_reacquire_rejects_control_directory_replacement` | 段5の期待を正しい `(True, False)` に変更 | F5 の明示許可、M6 完全集合 |
| `test_finalize_failure_keeps_verified_fold_commit_and_never_rolls_back` | `(False, True)` assertion を追加 | M5 kill node として明示許可 |
| `test_fold_rollback_failure_reason_reports_preserved_state` | `(False, False)` assertion を追加 | M4 kill node として明示許可 |

既存 assertion の削除、反転、緩和、skip、xfail 化はありません。equality 対応のためだけに段5で加えられていた既存 node の変更は戻しました。

### 検査結果

- `git diff --check`: rc=0
- 4 file の Python compile: `syntax-ok`
- U+0300〜U+036F 検査: 問題なし
- pytest: **未実走**
  - `python3 tools/run_tests.py -q` 経由で追加・変更対象 22 node の実行を要求
  - wrapper 終了値: rc=16
  - 理由: `Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1`
  - receipt: `output/pegasus-dispatch/b4c7442fb12e758e9493577d538c2436/receipt.json`
  - pytest 本体の実行 node 数: 0
- full suite、mutation 実走、provenance 監査: 未実施
- docs 編集: 0 file
- commit: 未作成