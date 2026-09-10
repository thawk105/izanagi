## 総括
実装済み・未実走。認可された1 literalだけ修正しました。

## 変更
[orchestrator/tests/test_check_docs.py:2519](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2544-mutation-trigger/orchestrator/tests/test_check_docs.py:2519) の `9_517` → `9_507`。

現物pinを訂正済み入口に整合。上限 `9_520`、負例 `9_521` の拒否は維持し、correctnessの受理・拒否は不変です。

## 検証
- 入口の実体は9,507 bytes。HEADとの差は「fix 後に」の削除だけで、UTF-8で正確に10 bytes。
- 差分は1行・1 literal。`git diff --check` 成功。
- テスト再走は先のqstat失敗を踏まえ省略。親の訂正前結果（1 failed, 588 passed, 8 skipped）は訂正後の成功証拠には数えません。

| 所見 | closed / partial / regressed | 根拠 |
|---|---|---|
| byte-pin | partial | 修正・静的整合確認済み。訂正後テスト未実走 |

## 波及
所有外は以下です。今回の編集なし。

- caller：pytestによる対象nodeの収集・実行。
- 共有fixture/helper：`_build_min_repo`、`_read`、`_pad_to_bytes`、`_run_check`。
- consumer：`tools/check_docs.py` の予算検査・条件15契約、対象テスト。実行時間台帳にもnode参照あり。

docs編集、commit、git add、親全走、変異本走、新設・改名は行っていません。