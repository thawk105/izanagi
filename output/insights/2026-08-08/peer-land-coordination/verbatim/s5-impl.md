実装済みです。実装前の現行挙動は、新規 tool のため「無」でした。受理集合は段 4 裁定で指定された範囲だけです。

- [wave_land_window.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/tools/wave_land_window.py:157)
  - `declare`：`O_NOFOLLOW`、regular file・所有者検査、4 行ヘッダ直後への byte 保存更新
  - `peers`：self 除外、TTL、件数・byte 上限、partial/unavailable、閉じた射影値
  - `message`：固定 2 行、land JSON の成功 status と `main_after` 検証、生成拒否 rc=3
  - roster・git・外部 process・機体固有 path は不使用
- [test_wave_land_window.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/orchestrator/tests/test_wave_land_window.py:76)
  - 必須正例と MW1〜MW7 を収録
  - 既存テスト・fixture・期待値は変更していません

検査結果：

- Python 構文検査：成功
- `python3 tools/check_codex_agents.py`：成功
- `python3 tools/check_docs.py`：成功
- 対象範囲 `orchestrator/tests/test_wave_land_window.py`：未実走
  - `tools/run_tests.py` 経由で2回試行
  - いずれも pytest 起動前に rc=16
  - 理由：`Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1`
  - したがってテスト緑は主張しません

所有外への静的波及候補は、親 caller の `.claude/commands/dev-wave.md`、handoff 生成側、`dev_wave_land.py` の保存 JSON consumer です。共有 fixture への変更はなく、親による変異 matrix・関連 consumer test・受入全走が残っています。既存の親所有 `.claude/commands/dev-wave.md` 差分には触れず、commit も作成していません。

## 総括

- 実装範囲：新規 tool と専用テストのみ。
- 必須正例および MW1〜MW7 のテストを実装。
- 対象テストは dispatch 基盤障害により未実走。
- 静的構文・Codex 構成・docs 整合検査は成功。
- リスク：親 caller 統合、変異実走、consumer test、受入全走は未確認。