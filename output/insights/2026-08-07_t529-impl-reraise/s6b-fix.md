敵対レビュー4所見への修正と回帰試験追加は完了しました。ただし実行基盤の `rc=16` により pytest は未実走のため、全所見を `partial` とします。

## 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| F-1 | partial | 共有 private core に `contract_sha256` の exact `str` 検査を1か所だけ追加。両 lane の派生型拒否試験も追加。未実走 |
| F-2 | partial | g1/current-g2 状態で `main` が historical resolver を使う CLI 配線試験を追加。未実走 |
| E-1 | partial | ambiguous resolver が current lookup へ fallback しない試験を追加。未実走 |
| E-2 | partial | fresh 成功系で lookup 1回と、calibration・receipt・build・command receipt への sentinel 同一性を固定。未実走 |

## 編集ファイル

- [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_floor_campaign.py:340)
  - 共有 `_validate_protocol_with_resolver` 内で `type(recorded_hash) is not str` を拒否。
  - 例外境界は既存どおり `FloorContractError` から `FloorCampaignError` へ変換。

- [test_s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_s8b_floor_campaign.py:4451)
  - F-1、F-2、E-1、E-2 の4試験を純増。
  - tracked 既存期待値の反転・緩和・skip・削除なし。

`docs/`、`output/`、`s8b_floor_contract.py`、`env_contract.py`、凍結 manifest は編集していません。既に staged だった `s4b-addendum.md` にも触れておらず、`git add`・commit は行っていません。

## テスト結果

`python3 tools/run_tests.py` 経由で、次の9 nodeid selector（parameter 展開予定11 cases）を実行要求しました。

- `test_protocol_lanes_both_reject_str_subclass_contract_sha256`
- `test_public_validate_protocol_ambiguous_generation_never_falls_back_to_current`
- `test_main_validates_recorded_g1_with_historical_lane_when_current_is_g2`
- `test_current_admission_reuses_exact_contract_across_successful_run`
- `test_public_validate_protocol_resolves_recorded_historical_generation_once`
- `test_public_validate_protocol_historical_failures_never_fallback_to_current`
- `test_fresh_run_rejects_recorded_g1_when_current_contract_is_g2_before_io`
- `test_resume_under_unchanged_current_contract_generation_completes`
- `test_resume_rejects_recorded_g1_when_current_contract_is_g2_before_calibration`

結果は pytest collection 前に `rc=16`：

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
```

sandbox 外の admission 台帳も更新不能だったため、ローカル実行への迂回はしていません。したがって緑は主張しません。

静的検査結果：

- Python `compile()`：`syntax-ok`
- `git diff --check`：成功
- 凍結 protocol SHA-256：`261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac`
- `floor_protocol.json` と `FROZEN_MANIFEST`：差分なし

## 所有外への波及可能性

- 公開 `validate_protocol` の production caller は `main`。テスト consumer は floor contract、protocol builder、ratified freeze／verify 系。
- current private lane は protocol builder、freeze 発行後 read-back、fresh/resume admission が使用。
- `s8b_prediction_runner` は builder 経由で current lane の影響を受ける。
- 共有 fixture は `_protocol`、`_valid_protocol_dict`、合成 g2 registry、fake build／prepare／receipt。追加試験の monkeypatch は各試験終了時に復元される。
- production shell `tools/pegasus/floor_campaign.sh` は `main` の間接 consumer。ただし現行 official 経路は protocol 読込み前に拒否される。
- 共有 leaf `s8b_floor_contract.validate_protocol` は変更していないため、他 consumer の受理集合へ直接の変更はない。

## 総括

4所見のコード修正と回帰試験は実装済みです。凍結 bytes・禁止対象・既存期待値は不変です。ただし pytest が実行基盤で停止したため、現状は全件 `partial（実装済み・未実走）` であり、`closed` ではありません。