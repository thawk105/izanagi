## 総括

- F1: `partial` — v1 の同一レンズを `AuthorityError` で拒否し、historical 正常系テストを追加。未実走。
- F2: `partial` — 指定 3 箇所の caller 値を `max` 化。CLI の受理集合は未変更。未実走。
- 変更ファイル:
  - [`launch_authority.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/tools/dev_waves/launch_authority.py:102)
  - [`test_dev_wave_launch_authority.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/orchestrator/tests/test_dev_wave_launch_authority.py:378)
  - [`test_dev_wave_codex.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1132-stage2-luna/orchestrator/tests/test_dev_wave_codex.py:101)
- 回帰テスト nodeid: `orchestrator/tests/test_dev_wave_launch_authority.py::test_historical_v1_rejects_same_lens_model_and_reconstructs_valid_v1`（pytest 未実走）。
- 期待赤: なし。
- 波及先: `tools/codex_worker_launch.py` の live/historical authority 読み込み、`test_codex_worker_launch.py` の v2 consumer、authority test の共有 fixture、`test_check_docs.py` の parser fixture、`test_spool_fold.py` の import isolation。bound stage の `high` 拒否テストは変更なし。
- 実装できなかった点: pytest 実走は指示どおり未実施。`git diff --check` は通過。docs 編集・commit はしていません。