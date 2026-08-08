production caller 閉包に禁止対象の oracle driver が含まれるため、指示どおり未編集で停止しました。

`pipeline.evaluate` は [s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/s8b_oracle_driver.py:1162) で production default として選ばれ、[同ファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/s8b_oracle_driver.py:1352) から直接呼ばれています。契約は `_prepare_v2_execution()` 内の `lookup()` で取得されますが、activation receipt は保持されていません。

したがって `pipeline.evaluate(..., *, activation_receipt=...)` を必須化するには oracle driver への配線が不可避です。しかし禁止事項は「oracle driver への receipt 配線を実装しない」と明記しています。省略時の自己発行や任意引数化は fail-open となるため採用できません。

受理・拒否挙動は変更前後で同一です。現状の自己発行・自己照合、g1 のみの receipt テスト、lock 非保持の fork テストがそのまま残っています。

## 総括

### 1. 所見対応表

| 所見 | 状態 | 理由 |
|---|---|---|
| R1: caller-held receipt | partial | 現実装の receipt 解決は残るが、guard 内の自己発行を解消できていない |
| R2: Pegasus g2 統合正例 | partial | production seam の g2 テストは未追加 |
| R3: held-lock fork | partial | at-fork callback は既存だが、競合形テストは未追加 |
| regressed | なし | 実装・テストを変更していない |

### 2. 変更ファイルと行数

- 変更ファイル: 0
- 差分: `+0/-0`
- docs 編集・commit: なし
- 既存の段 5 未 commit 差分には非接触

### 3. 走らせた検査と結果

- 必須正本 5 ファイル: 全文読了
- `git status --short --branch`: 既存段 5 差分を確認
- `require_certified_writer_authorization` / `pipeline.evaluate` / `run_campaign` の production caller 静的検索: 完了
- pytest・meta-test・`check_codex_agents.py`・`check_docs.py`: 未実走
- 緑の主張: なし

### 4. 未実走・未達

R1〜R3 はすべて未完了です。停止条件が実装前に成立したため、テストも開始していません。

### 5. 親への申し送り

最小の再裁定が必要です。推奨は、oracle の「最初の書込み境界」全体は scope 外のまま維持しつつ、`pipeline.evaluate` certified sink へ渡すための最小限の receipt 保持・引渡しだけを `s8b_oracle_driver.py` に許可することです。

追随対象となる production 閉包は次です。

- guard 直接 caller: `pipeline.py`、`loop.py`、`screening_driver.py`、`s1_direct_comparison.py`
- evaluate 直接 caller: `loop.py`、`screening_driver.py`、`s1_direct_comparison.py`、`s8b_oracle_driver.py`
- `run_campaign` 経由: `p2_2.py`、`sanity_silo.py`、`p3_s4_loop_sort.py`、`backoff_sweep.py`、`s6_sort_sweep.py`、`backoff_repro.py`、`p3_s4_red.py`、`s8a_trigger_sweep.py`、`p3_kickoff.py`、`demo.py`、`p3_s4_loop.py`、`p3_s4_loop_trigger_gating.py`
- 主な consumer test: `test_campaign.py`、`test_execution_guard.py`、`test_screening_driver.py`、`test_s1_direct_comparison.py`、`test_s8b_oracle_driver.py` と各 campaign driver test。