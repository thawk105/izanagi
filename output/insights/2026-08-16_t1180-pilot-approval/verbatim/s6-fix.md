実装はテスト 1 ファイルだけで完了しました。production bytes、driver gate、既存期待値は変更していません。

| 所見 | 状態 | 対応 |
|---|---|---|
| レビュー A 所見 1 | closed | 承認変数の全 3 出現、代入・`unset`・`export`・`declare`・`local` 禁止、冒頭 `unset` 対象集合を固定 |
| レビュー A 所見 2 | closed | 不一致値へ `*`、`?`、`-n`、改行を追加 |
| レビュー B 所見 1 | closed | static admission → exact 照合 → receipt 検査 → dependency build → driver 実行の source index 順序を固定 |
| レビュー B 所見 2 | closed | テスト名・docstring を submitter-generated qsub argv の保証に限定。実 scheduler seam は T-1180-b のまま scope 外 |
| 回帰 | regressed なし | 既存期待値の変更、緩和、skip、削除なし |

### 追加・変更したテスト

- 新設:
  `test_floor_job_confirmation_dataflow_and_admission_order_are_fixed`
- 8 ケースへ拡張:
  `test_floor_job_rejects_confirmation_not_bound_to_submission_nonce`
  - `empty`
  - `literal-one`
  - `different-nonce`
  - `literal-true`
  - `asterisk`
  - `question-mark`
  - `leading-hyphen`
  - `newline`
- 改名:
  `test_submit_floor_qsub_argv_does_not_inherit_ambient_confirmation`

### 実走結果

- `python3 orchestrator/tests/test_pegasus_floor_tools.py`
  - 最終結果: **85 nodeids、85 passed**
  - `IZANAGI_EFFECTIVE_SCHEDULER_V1`: `serial`
- 制約 meta-test:
  - `test_every_test_file_is_self_runnable_or_allowlisted`
  - `test_allowlist_has_no_stale_or_self_runnable_entries`
  - `test_this_metatest_is_itself_self_runnable`
  - **3 passed**

### S1 / S2 手動変異

- S1: gate 後、`PROTOCOL_PATH` 直前へ承認変数代入を注入
  - **2 failed / 83 passed**
  - 新設 dataflow node が出現集合違反で赤
  - 既存 dependency fragment node も未束縛変数で赤
- S2: 冒頭 `unset` に承認変数を追加
  - **1 failed / 84 passed**
  - 新設 dataflow node が赤

復元後の `tools/pegasus/` 差分 SHA-256 は変異前後とも
`a3f975789c3e647219ae8fb418fa2ba4c46711cc7c9ec3cec4eaf0bb6ce9a31b`
で一致しました。

手順上の例外は `partial` です。指定された `git checkout --` は両回とも sandbox が `.git/worktrees/.../index.lock` を read-only として拒否しました。外部 backup は使わず、保持済み Git index から `git checkout-index` で復元し、最終的に index も元の未 stage 状態へ戻しました。

### 最終差分

- `git diff --check`: 成功
- staged 差分: なし
- `orchestrator/campaign/`: 差分なし
- `git diff HEAD --stat`:

  `orchestrator/tests/test_pegasus_floor_tools.py | 324 +++++++++++++++++++++++--`  
  `tools/pegasus/floor_campaign.sh                |  19 +-`  
  `tools/pegasus/submit_floor.sh                  |  11 +-`  
  `3 files changed, 328 insertions(+), 26 deletions(-)`

docs 編集、commit、push、scheduler 投入は行っていません。

## 総括

レビュー A/B の実装所見はすべてテスト側で閉じました。新設した単一 node が S1 と S2 の双方を実際に kill し、最終 self-runner は 85 件すべて緑です。production 差分は変異前の bytes と一致しています。