**GO（今回の焦点レビュー範囲）。closed 13／partial 0／regressed 0。**

| 所見 | 判定 | 確認根拠 |
|---|---|---|
| A-M1 | closed維持 | 稿の同一bytesを確認、WAL説明に変更なし |
| A-M2 | closed維持 | 所要時間の出所・限定に変更なし |
| A-M3 | closed維持 | publish保証の限定に変更なし |
| A-M4 | closed維持 | 認可根拠の参照に変更なし |
| A-S1 | closed維持 | READMEの個別扱いはanchorと一致 |
| A-S2 | closed維持 | 旧値との区別に変更なし |
| A-N1 | closed維持 | hash用途の記述に変更なし |
| B-MF1 | closed維持 | 生成器は旧implから不変 |
| B-MF2 | closed維持 | path完全一致検査はanchorと一致 |
| B-S1 | closed維持 | 図3成果物のhashは前回確認値と一致 |
| B-S2 | closed維持 | 区間両端検査はanchorと一致 |
| F-MF1 | **closed** | 単独終端・M13の実注入と失敗nodeを確認 |
| R-M1 | **closed** | insight実在、原資料・限定・検証記録へ到達可能 |

証拠：

- **同一性**：稿・PNG・PDF・provenanceのSHA-256は前回focus記載値と一致。生成器・test・両README・稿は指定anchor `fd7506c746c406543ce144a9455cef0fed19070e` と一致。anchor以後のtracked差分はinsightの検証記録追記のみ。
- **単独実走**：[focus-tests-1.log](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2775-a1-sized-results-recovery/focus-tests-1.log) の終端は **28 passed、skip 0、child rc=0**。
- **変異**：[ledger](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2775-a1-sized-results-recovery/mutation-results-v3.json) はbaseline PASSED、M0 SURVIVED、M1〜M13 KILLED。stdoutから失敗node集合を照合し、期待と**14/14完全一致**。全行のanchor・spec束縛とstdout hashも一致。spec実物のSHA-256は `f7a03a67706a91b169a257cec3069c36fd08c014d06403d45130f3fd9ffbc94f`。
- **新旧差**：M13は旧「全欠落ならskip」を実際に復活。traceで`pytest.skip`到達を確認し、`test_landed_fig9_rejects_all_missing_outputs` **だけ**が失敗（1 failed／27 passed）。修正版は全欠落を存在assertで拒否し、この負例を含む28件が通過。診断文字列だけの変異ではない。
- **復元・終端**：固定HEAD復元＋読戻し一致の方針、非終端履歴なし。[wrapper receipt](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2775-a1-sized-results-recovery/mutation-results-v3.json.wrapper-receipt.json) はrc=0、`terminal_ledger`・`shared_snapshot_matches`・`teardown_completed`すべてtrue。共有照合の射程は独立clone内。
- **参照**：[insight README](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2775-a1-sized-results-recovery/output/insights/2026-09-18/t2775-a1-sized-results-draft/README.md) から稿・公開leaf・限定・検算逐語・変異証拠へ辿れる。保存されたv3 ledger／receipt／specはjob側と同一bytes。最終受入は未完了として記録され、先書きなし。

## 総括

**F-MF1とR-M1は解消、今回の残件はありません。** GOは焦点レビューの判定であり、最終受入・land完了を意味しません。今回は読み取りと証拠照合のみで、pytest実走・変更・子の起動は行っていません。