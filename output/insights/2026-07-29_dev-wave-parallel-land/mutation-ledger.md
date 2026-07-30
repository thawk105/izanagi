# dev-wave parallel land — mutation ledger

- 対象 commit: `43c4ec4c7ff658582f0584f104ce59f388552cc5`
- harness: 一時 harness（実走後に削除。spec と結果は本台帳へ凍結）
- 方式: 単一 process lock、old anchor exact 1 件、1 file diff、`pytest -q -rf`、
  failure node 照合、各回 `git checkout -- <対象>`、source bytes 比較、tracked diff 0
- 結果: 13/13 KILLED、SURVIVED 0、復元失敗 0

| ID | 注入した fail-open / over-reject | kill node |
|---|---|---|
| M1 | tested-main / audited ancestry を常時許可 | `test_same_base_two_wave_winner_stale_resync_loser_land_e2e` |
| M2 | cooperative flock を省略 | `test_nonblocking_common_lock_reports_lock_busy` |
| M3 | main tracked/index dirt record を除外 | `test_tracked_and_staged_main_dirt_are_rejected` |
| M4 | unknown untracked を許可 | `test_unknown_untracked_rejected_without_main_or_foreign_artifact_change` |
| M5 | handoff type/schema validation を省略 | `test_malformed_symlink_and_nonregular_handoff_are_rejected` |
| M6 | worktree admin/backpointer binding を省略 | `test_unregistered_alias_child_is_rejected` |
| M7 | shallow/graft/replace rejection を省略 | `test_shallow_graft_replace_filter_and_promisor_are_rejected` |
| M8 | wave HEAD == tested tip を省略 | `test_audited_sequence_and_moved_wave_tip_are_exact` |
| M9 | post-merge HEAD result split を無効化 | `test_not_landed_is_distinct_from_postcondition_failure` |
| M10 | valid handoff を一律拒否 | `test_handoff_all_states_and_stale_are_accepted` |
| M11 | registered Claude/Codex worktree を一律拒否 | `test_basic_land_accepts_registered_claude_and_codex_children` |
| M12 | S09 の唯一 helper route を除去 | `test_real_repo_clean` |
| M13 | S09 の再受入→evidence→O23 順序を helper 単発へ縮退 | `test_real_repo_clean` |

## M13 erratum

事前登録では E2E node を直接の kill oracle としたが、helper は裁定どおり acceptance receipt を認証せず、
manager の再受入工程は executable Python でなく共通 dispatcher が正本である。そこで fix 後 anchor を
S09 acceptance-order literal へ再照準した。二 wave E2E は winner→stale→new-main merge→subprocess
acceptance receipt→new A..T evidence→loser land の正例を独立に固定し、dispatcher 縮退は
`test_real_repo_clean` が kill する。初回案を消さず、この役割分担を erratum とする。

## 復元後

- `git diff --exit-code`: rc=0
- related pytest: 180 passed
- `python3 tools/check_docs.py`: 違反なし
