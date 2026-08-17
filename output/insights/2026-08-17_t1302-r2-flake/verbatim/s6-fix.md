## 直した内容

- F-1: [_real_red_checker_repo](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1302-r2-nonattrib/orchestrator/tests/test_dev_wave_wait.py:2955) に独立 literal の `tools/run_tests.py` を初回 commitへ追加し、main/tip の blob SHA 等値を明示検査。
- F-2: [_runner_tree_entry](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1302-r2-nonattrib/tools/dev_wave_land.py:619) を追加。`ls-tree -z --full-tree` の rc 非 0 は retryable、空 entry は恒久拒否、存在時は type と SHA を構造化解析。
- F-3: [outer receipt 専用検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1302-r2-nonattrib/orchestrator/tests/test_dev_wave_wait.py:3879) を追加。重複集合を持つ `_RedCheckResult` を outer producerへ直接入力。
- F-4: [実 producer mixed 検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1302-r2-nonattrib/orchestrator/tests/test_check_acceptance_reds.py:705) を追加。実 receipt bytesを実 consumerへ渡して red/flake 分離を固定。
- F-5: [64 KiB 境界検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1302-r2-nonattrib/orchestrator/tests/test_dev_wave_land.py:6802) を裁定どおり変更。旧 payload は上限超過、新最大は改行込み 65536 bytes、縮小幅 21 bytes、追加 field 30 bytesを独立 literalで固定。

## 追加・変更したテスト

- `test_land_runner_path_absence_is_permanent_rejection`
  - path 不在で `retryable_same_request=False`、`release_safe=True`、main 不変を主張。
  - 全 Git 失敗を retryable にする変異を殺す。
- `test_land_runner_lookup_process_failure_is_retryable`
  - runner lookup の process failureで `retryable_same_request=True`、`release_safe=False`を主張。
  - Git障害まで恒久拒否にする変異を殺す。
- `test_acceptance_receipt_rejects_overlapping_red_check_sets_directly`
  - inner consumerを経由せず outer disjoint 述語だけを検査し、M4 outer変異を殺す。
- `test_mixed_non_attributable_and_flake_receipt_round_trips_to_waiter`
  - 実 producerが red 1件と flake 1件を書き、実 consumerが独立 literalの2集合を返すことを検査。
  - mixed時に片方を落とす変異を殺す。
- `test_compact_core_json_preserves_legacy_64k_message_boundary`
  - fixture短縮による隠蔽を除き、旧最大超過と新最大の完全境界を固定。

## 波及の静的列挙

- `_runner_tree_entry` は child-green の tip runner存在確認と、non-attributable-only のmain/tip blob等値確認に影響する。child-greenで異なるblobを許す契約は維持。
- `_real_red_checker_repo` の共有 caller 4件にrunner blobが追加される。既存PATH shim、PYTHONPATH shadow、snapshot差替えは未変更。
- `tools/wave_land_window.py` は新最大JSONのconsumerだが所有外のため未変更。
- checker mixed検査は `dev_wave_wait.py` のimport-time回帰に波及しうる。
- 新規検査は固定commit数、固定node数で、履歴や台帳規模に比例しない。

## 未了・懸念

- 指示どおりpytestは未実走。緑は主張しない。
- AST構文解析、test名重複検査、`git diff --check`、変更file範囲、結合文字不在は静的確認済み。
- 親は指定3 test file、焦点3件、F-2分類2件、mixed相互pin、M4 outer変異、64 KiB境界を実測する必要がある。
- docs、spool、commitには触れていない。

## 総括

F-1からF-5まで指定5 file内で修正した。  
runner path不在とGit障害のretryable分類を構造化結果で分離した。  
outer disjoint、実producer mixed、64 KiB縮小を独立検出力で固定した。  
状態は「実装済み・未実走」。