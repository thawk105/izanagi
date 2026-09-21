## 総括

**実装済み・未実走です。** 変更は次の 2 ファイルだけです。git add / commit、docs 編集は行っていません。

- [loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2795r-unit-a1/orchestrator/campaign/loop.py): 発行個体・PID の台帳、不可逆 close、コピー／pickle 拒否、認可直後の束縛、再利用時の全束縛照合を追加。receipt は台帳内で JSON 文字列として保存します。
- [test_campaign.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2795r-unit-a1/orchestrator/tests/test_campaign.py:14189): 17 test 関数、パラメータ展開後 28 node を追加しました。

変更前は S 無しで毎回認可・claim 取得を行い、single_process 契約の同 identity・同 root への 2 回目は `ClaimError` でした。変更後も S 無しの挙動は維持し、受理が増えるのは「同 process・同 sink が発行し束縛した未 close の S を、全束縛が一致する再利用で渡した場合」だけです。

**検査結果:** `py_compile`、`git diff --check`、NFC 確認は成功しました。既存 test 関数・class の AST は不変で、S 無しの認可本体も取得結果の保持を除いて AST が一致しています。`campaign_claim.py`・`reservation.py`・`execution_guard.py`・`ident.py` は HEAD と bytes 一致です。pytest・変異検査の成功は主張しません。

以下は変異を検出する**設計上の対応**であり、KILLED の実測結果ではありません。表中の `S_` は `test_authorization_session_` の略です。

| 新設 test 名 | 対応する変異 ID |
|---|---|
| `S_reuses_one_real_claim` | M10、M0 の等価対照対象 |
| `test_no_session_second_authorization_keeps_claim_error` | M11 |
| `S_rejects_unissued_and_copy` | M4 |
| `S_rejects_closed` | M5 |
| `S_rejects_pid_mismatch` | M6 |
| `S_rejects_claim_change` | M1、M2（created_utc case） |
| `S_rechecks_expired_reservation` | M1、M3 |
| `S_rejects_changed_reservation` | M1 |
| `S_rechecks_receipt` | M1、M7 |
| `S_receipt_is_detached` | receipt 不変性の補助検査、独立 ID なし |
| `S_rechecks_prewrite_validator` | M1、M8 |
| `S_rejects_changed_binding` | M1。冗長な比較を独立 ID として数えない |
| `S_failed_authorization_does_not_bind` | 束縛時点の補助検査、独立 ID なし |
| `S_new_session_cannot_inherit_claim` | 移植拒否の補助検査、独立 ID なし |
| `S_binds_before_perf_failure` | M9 |
| `S_two_campaigns_one_claim` | C2 の補助検査。H 群から除外 |
| `S_non_single_process_binding` | M1 と claim 非生成の補助検査 |

静的に確認した波及は次のとおりです。

- production caller inventory は **17 file・22 call のまま**です。対象は `b10_backoff_static_tail_formal`、`b10_backoff_shape_sweep`、`backoff_extended_sweep`、`backoff_repro`、`backoff_sweep`、`demo`、`p2_2`、`p3_kickoff`、`p3_s4_loop`、`p3_s4_loop_sort`、`p3_s4_loop_trigger_gating`、`p3_s4_red`、`paper_story_a1_paired`、`paper_story_a2_certification`、`s6_sort_sweep`、`s8a_trigger_sweep`、`sanity_silo`。自動 session 化はしていません。
- 既存 single_process test の順序・receipt object 同一性の期待値、共有 fixture、conftest は変更していません。新設 test は pytest fixture に依存し、末尾の単独実行用 `_run()` は fixture を注入しません。
- `test_p3_s4_loop.py` と driver の配線は未変更で、A2 の担当範囲です。
- `loop.py` の closure bytes が変わるため、lock を作る結合 test は親の統合 commit 後に実走が必要です。closure／resumability の stub は追加していません。

**親の判断・後続作業:** 統合 commit、H 群の exact node 集合の確定、commit 後の結合検査と変異検査が必要です。追加の設計裁定を要する点は見つかっていません。