## 変更

- [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pi-impl/orchestrator/tests/conftest.py:2501): `pytest_configure_node` で、早期 memo の直後に session 一回の写し job を起動します。終了処理は thread を join し、写しを削除して例外を伝播します。終了処理は `pytest_unconfigure` から呼ばれ、`pytest_sessionfinish` には呼出しがないため、worker 終了後の位置です。
- [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pi-impl/orchestrator/tests/test_s8b_oracle_driver.py:996): builder の複製を写し経由に変更し、T1 を一件追加しました。T2 には helper と builder の呼出し回数が等しいことを追加しました。
- [test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pi-impl/orchestrator/tests/test_real_repo_serialization.py:6453): 既存の模擬 hook fixture だけで新 job を no-op にしました。T1 は既存の conftest 読込み方式を使える位置に置き、consumer AST の対象を増やしていません。

## 実走

`python3 -m py_compile`（上記 3 ファイル）と `git diff --check` は成功しました。

`PYTHONPATH=. python3 tools/run_tests.py -q -rf -p no:cacheprovider orchestrator/tests/test_s8b_oracle_driver.py::test_t080_visible_output_snapshot_starts_once_and_preserves_copy` は `qstat -Q` の dispatch 事前確認で `rc=16` となり、**テスト本体は未実走**です。T1・T2 と受入全走に緑の判定はありません。

## 変異の帰属

| 変異 | 期待する検出 | 単一理由・mask |
|---|---|---|
| M1 | T2 の helper 回数＝builder 回数 | 単一理由 |
| M2 | T1 の変更後 bytes と変更前の直接複製の不一致 | 単一理由 |
| M3 | T1 の mtime 不一致 | 単一理由。元 file の mtime を固定済み |
| M4 | T1 の二回目の hook 呼出し | **登録された spy 2 回の理由は mask あり**。`mkdir(exist_ok=False)` の衝突が先に起きるため、二回目が正常に戻ることを明示する assert へ再照準が必要 |
| M5 | T1 の実関数 spy が 0 回 | 単一理由 |
| M6 | T1 の helper 呼出し前に `result.json` が現れない | 単一理由 |
| M7 | T1 の finish 後も dir が残る | 単一理由 |

## 波及

所有外で本物の hook を直接呼ぶ [test_acceptance_schedule_order.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pi-impl/orchestrator/tests/test_acceptance_schedule_order.py:1084) の G2a test は shard spec を持たず、新 job の発火対象外です。所有内では nonce 配線の二 test と `_early_memo_cache_probe` を使う test 群が直接 caller で、発火する模擬 fixture には局所 no-op を入れました。

関連する meta-test は `test_t080_stub_free_e2e_exact_consumers_and_nodeids_b5`、`test_real_repo_group_collection_exactly_matches_canonical_nodes`、受入 duration ledger と hold の collection 検査です。T1 は既存 consumer helper を呼ばず、real-repo access 登録、ledger、hold 台帳の編集は生じていません。

## 総括

v2 の写し生成、builder 経由、終了時削除を所有 3 ファイルに実装しました。
T1 は小さい git repo で本物の hook と複製関数を通す形です。
実走は dispatch 障害で未完了です。M4 は登録された spy 理由が dir 衝突に mask されるため、親の変異検査前に再照準が必要です。