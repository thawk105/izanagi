## 総括

所有2ファイルの最小修復を実装しました。検証は実行基盤で停止したため、未実走です。

| 状態 | 結果 |
|---|---|
| closed | なし |
| partial | 回帰3件を修復済み。テスト実走待ち |
| regressed | 未判定（テスト未起動） |

変更行：

- `orchestrator/campaign/paper_story_a1_source.py`：旧8行の不要importを削除。現61–65行で既存 `patchharness._git` を再利用し、非0終了を `RuntimeError` に変換。root・pin・HEAD・期待tree検査を維持。
- `orchestrator/tests/test_ccbench_spawn_sites.py`：903行・2671行だけを `7268 → 7374` に更新。同じlegacy `run_campaign` 呼出しへの行番号整合です。

`git diff --check` は成功。`python3 tools/run_tests.py orchestrator/tests/test_ccbench_spawn_sites.py` は **orphan-hold により rc=16、child_started=false**。回帰3件、未知process・別deferred sinkの既存負例、sourceの正例・負例は未実走です。

所有外への波及候補はA1の `materialized()` 利用箇所と `pipeline.py:1100` のbuild境界検証です。共有fixture・consumer testは変更していません。add・commit・docs編集・submitは行っていません。