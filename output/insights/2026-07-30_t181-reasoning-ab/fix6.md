## 総括

F3-1〜F3-4 を実装上クローズしました。変更は [codex_reasoning_ab.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2050) と [test_codex_reasoning_ab.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1381) の2ファイルだけです。docs・commit・対象外 limitation には触れていません。

F3-1 は各 verdict row に append 時点の `packet_sha256_at_read` を機械付与し、freeze、reveal、最終 adjudication で output SHA と照合します。F3-2 は primary の final-attempt 規則を維持しつつ、reliability を全 attempt の post-treatment occurrence から集計します。F3-3 は正規化後の第一 decision 文を有限 grammar で完全一致させ、句読点後の最終判断否認も拒否します。F3-4 は prelaunch 例外をゼロ資源の `technical-invalid` completion として記録し、未起動 mate を `pair-invalidated` と明示して、次 generation の両側 retry と manifest replayを許可しました。

追加した独立 node は次の4件です。

- `test_f3_1_packet_swap_restore_is_rejected`
- `test_f3_2_pair_invalidated_post_treatment_occurrence_is_reliable`
- `test_f3_3_scorer_rejects_decision_disclaimed_after_punctuation`
- `test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation`

既存テストの削除・改名はなく、M1〜M12、500-byte 境界、歴史 control、pair timing、POS四分岐×NEG除外の node は静的に残っています。`python3 -m py_compile` は成功しました。一方、指示どおり pytest、`tools/run_tests.py`、snapshot build、`git submodule update`、外部 clone は一切実行していません。したがって緑や pass 件数は主張しません。

波及可能性は、verdict log と freeze artifact に新しい digest field が加わるため旧形式の未凍結 fixture は再生成が必要なこと、post-treatment reliability が final attempt 数ではなく実際の全 occurrence 数へ増える場合があること、prelaunch ledger row が launch receiptを持たない構造化 completionを許すこと、曖昧 decision の受理集合が意図どおり縮小することです。最終受理と件数確認は、親による計算ノード上の targeted/full 実測に委ねます。